"""
Layer A — DAQ capture with baseline → onset → window.

Per Bill 0002 Part 3.2 + 3.3 (Case 1 Position B):
  - Baseline: collect `baseline_s` of quiescent frames before force is applied.
  - Onset: first frame where `chN_raw > baseline_mean + max(onset_sigma * baseline_std,
    onset_min_counts)`.
  - Settle skip: `window_s[0]` seconds after onset are discarded.
  - Capture: `window_s[1] - window_s[0]` seconds of frames are averaged.

The capture is two-phase by design (arm + acquire) so the caller can trigger
the MTS ramp between the two phases. Onset is detected from the DAQ stream
itself — no wall-clock synchronisation between MTS and DAQ is required.

Frame source contract: an iterator yielding sequences indexable as
`frame[0]` (ts_ns, unused by this module) and `frame[channel + 1]` (raw ADC
code for the given channel). This matches `flexiforce_reader`'s 8-channel
frame layout (Bill 0001 H1.1 / `toolchain_config.md` DAQ Serial Frame).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterator, Sequence


@dataclass(frozen=True)
class CalibrationPoint:
    """
    One per-level calibration measurement.

    `mean_first_half` / `mean_second_half` / `within_window_drift_fraction`
    expose the within-window stationarity of the captured signal.
    Per A301 spec, logarithmic creep produces a small monotonic rise across
    the 0.5–2.5 s window (~1.5% under nominal load) — `is_stationary()`
    accepts up to 5% by default, matching the sensor's creep allowance.
    Drift beyond that indicates the MTS did not settle on the commanded
    force within the window — the point should be discarded and re-acquired
    after diagnosing the MTS behaviour (Case 1 Condition C1).
    """
    channel: int
    raw_mean: float
    raw_std: float
    n_samples: int
    baseline_mean: float
    baseline_std: float
    t_onset_frame_index: int
    mean_first_half: float
    mean_second_half: float
    within_window_drift_fraction: float

    def is_stationary(self, creep_allowance_fraction: float = 0.05) -> bool:
        """True if |within_window_drift_fraction| <= creep_allowance_fraction."""
        return abs(self.within_window_drift_fraction) <= creep_allowance_fraction


class CaptureError(Exception):
    """Raised when capture cannot complete (no onset, exhausted stream, etc.)."""


class CalibrationCapture:
    """
    Two-phase calibration-point capture for one channel.

    Usage:
        cap = CalibrationCapture(reader_frames, channel=5)
        cap.arm()             # blocks for baseline_s; sensor must be unloaded
        mts.ramp_to(10.0)     # caller triggers MTS here
        point = cap.acquire() # blocks until window captured
    """

    def __init__(
        self,
        frame_source: Iterator[Sequence[int]],
        channel: int,
        *,
        sample_rate_hz: float = 100.0,
        baseline_s: float = 1.0,
        onset_sigma: float = 5.0,
        onset_min_counts: int = 30,
        max_wait_s: float = 5.0,
        window_s: tuple[float, float] = (0.5, 2.5),
    ) -> None:
        if channel < 0:
            raise ValueError("channel must be >= 0")
        if window_s[0] >= window_s[1]:
            raise ValueError("window_s must be (start, end) with end > start")

        self.frames = frame_source
        self.channel = channel
        self.sample_rate_hz = sample_rate_hz
        self.baseline_frames_n = int(round(baseline_s * sample_rate_hz))
        self.onset_sigma = onset_sigma
        self.onset_min_counts = onset_min_counts
        self.max_wait_frames_n = int(round(max_wait_s * sample_rate_hz))
        self.settle_frames_n = int(round(window_s[0] * sample_rate_hz))
        self.window_frames_n = int(
            round((window_s[1] - window_s[0]) * sample_rate_hz)
        )

        self._baseline_mean: float | None = None
        self._baseline_std: float | None = None
        self._armed = False

    def _channel_value(self, frame: Sequence[int]) -> int:
        return int(frame[self.channel + 1])

    def arm(self) -> None:
        """Capture baseline. Sensor must be quiescent throughout this call."""
        if self._armed:
            raise CaptureError("Capture already armed")
        baseline: list[int] = []
        for _ in range(self.baseline_frames_n):
            try:
                frame = next(self.frames)
            except StopIteration:
                raise CaptureError(
                    "Frame source exhausted during baseline capture"
                )
            baseline.append(self._channel_value(frame))
        n = len(baseline)
        mean = sum(baseline) / n
        var = sum((x - mean) ** 2 for x in baseline) / max(n - 1, 1)
        self._baseline_mean = mean
        self._baseline_std = math.sqrt(var)
        self._armed = True

    def acquire(self) -> CalibrationPoint:
        """
        Scan for load onset, skip the settle window, capture the acquisition window.

        Must be called after `arm()`. The caller is expected to apply force
        (e.g., trigger the MTS ramp) between arm and acquire — onset is detected
        from the DAQ stream itself, so exact timing of the trigger is not
        critical as long as the load arrives within `max_wait_s`.
        """
        if not self._armed:
            raise CaptureError("Call arm() before acquire()")
        assert self._baseline_mean is not None
        assert self._baseline_std is not None

        threshold = self._baseline_mean + max(
            self.onset_sigma * self._baseline_std,
            self.onset_min_counts,
        )

        onset_idx = -1
        scanned = 0
        for frame in self.frames:
            scanned += 1
            if self._channel_value(frame) > threshold:
                onset_idx = scanned
                break
            if scanned >= self.max_wait_frames_n:
                raise CaptureError(
                    f"No onset detected within {self.max_wait_frames_n} frames "
                    f"(threshold={threshold:.1f} ADC counts on ch{self.channel}); "
                    "did the MTS apply the load?"
                )
        if onset_idx < 0:
            raise CaptureError(
                "Frame source exhausted during onset scan with no load detected"
            )

        for _ in range(self.settle_frames_n - 1):
            try:
                next(self.frames)
            except StopIteration:
                raise CaptureError("Frame source exhausted during settle")

        samples: list[int] = []
        for _ in range(self.window_frames_n):
            try:
                frame = next(self.frames)
            except StopIteration:
                raise CaptureError(
                    "Frame source exhausted during window capture"
                )
            samples.append(self._channel_value(frame))

        n = len(samples)
        mean = sum(samples) / n
        var = sum((x - mean) ** 2 for x in samples) / max(n - 1, 1)
        std = math.sqrt(var)

        half = n // 2
        mean_first = sum(samples[:half]) / max(half, 1)
        mean_second = sum(samples[half:]) / max(n - half, 1)
        if mean != 0:
            drift_fraction = (mean_second - mean_first) / mean
        else:
            drift_fraction = 0.0

        return CalibrationPoint(
            channel=self.channel,
            raw_mean=mean,
            raw_std=std,
            n_samples=n,
            baseline_mean=self._baseline_mean,
            baseline_std=self._baseline_std,
            t_onset_frame_index=onset_idx,
            mean_first_half=mean_first,
            mean_second_half=mean_second,
            within_window_drift_fraction=drift_fraction,
        )
