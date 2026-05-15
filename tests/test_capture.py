"""Synthetic-frame tests for src.calibration.capture (Bill 0002 Part 3.2 + 3.3)."""
from __future__ import annotations

from typing import Iterator, Iterable

import pytest

from src.calibration.capture import CalibrationCapture, CaptureError


def make_frames(ch5_pattern: Iterable[int]) -> Iterator[tuple[int, ...]]:
    """
    Build (ts_ns, ch0..ch7) frames where channel 5 follows the given pattern;
    all other channels are zero. 100 Hz (10 ms per frame).
    """
    for i, v in enumerate(ch5_pattern):
        ts_ns = i * 10_000_000
        channels = [0] * 8
        channels[5] = v
        yield (ts_ns, *channels)


def test_capture_basic_step_load():
    """Quiescent baseline at 50, then step to 1000. Window must average to 1000."""
    baseline = [50, 52, 48, 51, 49] * 20      # 100 frames; sample std ~ 1.6
    loaded = [1000] * 300                      # plenty for 50-frame settle + 200-frame window
    cap = CalibrationCapture(make_frames(baseline + loaded), channel=5)
    cap.arm()
    point = cap.acquire()
    assert 49 <= point.baseline_mean <= 51
    assert point.raw_mean == 1000.0
    assert point.raw_std == 0.0
    assert point.n_samples == 200


def test_capture_onset_at_first_frame_above_threshold():
    """
    Baseline = 50 (std = 0). Threshold = 50 + max(5*0, 30) = 80.
    Ramp = [60, 80, 200, ...]: 60 below, 80 equal (not strictly greater),
    200 first to trigger → onset at scan frame index 3.
    """
    baseline = [50] * 100
    ramp_and_rest = [60, 80, 200] + [1000] * 300
    cap = CalibrationCapture(make_frames(baseline + ramp_and_rest), channel=5)
    cap.arm()
    point = cap.acquire()
    assert point.t_onset_frame_index == 3


def test_capture_aborts_when_no_onset():
    baseline = [50] * 100
    quiescent_after = ([50, 52, 48] * 300)     # never crosses threshold
    cap = CalibrationCapture(
        make_frames(baseline + quiescent_after), channel=5, max_wait_s=2.0
    )
    cap.arm()
    with pytest.raises(CaptureError, match="No onset detected"):
        cap.acquire()


def test_capture_aborts_when_stream_exhausted_during_window():
    baseline = [50] * 100
    loaded = [1000] * 60                       # < 50 settle + 200 window
    cap = CalibrationCapture(make_frames(baseline + loaded), channel=5)
    cap.arm()
    with pytest.raises(CaptureError, match="exhausted"):
        cap.acquire()


def test_capture_arm_twice_raises():
    cap = CalibrationCapture(make_frames([50] * 200), channel=5)
    cap.arm()
    with pytest.raises(CaptureError, match="already armed"):
        cap.arm()


def test_capture_acquire_before_arm_raises():
    cap = CalibrationCapture(make_frames([50] * 200), channel=5)
    with pytest.raises(CaptureError, match=r"arm\(\) before acquire"):
        cap.acquire()


def test_capture_baseline_exhausted_raises():
    cap = CalibrationCapture(make_frames([50] * 50), channel=5, baseline_s=1.0)
    with pytest.raises(CaptureError, match="exhausted during baseline"):
        cap.arm()


def test_capture_rejects_bad_window():
    with pytest.raises(ValueError, match="window_s"):
        CalibrationCapture(make_frames([50] * 200), channel=5, window_s=(2.5, 0.5))


def test_capture_threshold_uses_sigma_when_larger_than_min_counts():
    """
    Baseline 100 ± 50 (std ≈ 50). Threshold = 100 + max(5*50, 30) = 100 + 250 = 350.
    First frame to exceed 350 should trigger onset.
    """
    # 100 frames with ~50 std around mean 100
    baseline = [100 + (-50 if i % 2 else 50) for i in range(100)]
    # After baseline: 200 (below 350), 400 (above 350)
    after = [200, 400] + [1000] * 300
    cap = CalibrationCapture(make_frames(baseline + after), channel=5)
    cap.arm()
    assert cap._baseline_std > 40  # sanity
    point = cap.acquire()
    # frame 1 = 200 (below 350); frame 2 = 400 (above 350) → onset at 2
    assert point.t_onset_frame_index == 2


def test_capture_detects_non_stationary_window():
    """
    MTS still ramping during the window — second-half mean clearly higher
    than first-half. is_stationary() returns False at default 5% threshold.
    """
    baseline = [50] * 100
    # First post-baseline frame above threshold → onset at scan frame 1.
    # Settle skip consumes 49 more. Capture window = scan frames 51–250.
    # Construct a ramp that continues rising sharply across the capture window:
    onset_and_settle = [1000] * 50                  # scan frames 1–50
    # Step by 2 ADC counts per frame → 200-sample window covers 1000..1398
    capture_ramp = [1000 + 2 * i for i in range(200)]
    cap = CalibrationCapture(
        make_frames(baseline + onset_and_settle + capture_ramp), channel=5
    )
    cap.arm()
    point = cap.acquire()
    # First half (100 samples) values 1000..1198, mean = 1099
    # Second half (100 samples) values 1200..1398, mean = 1299
    # drift = 200, drift_fraction = 200 / 1199 ≈ 16.7% — fails both 5% and 10%
    assert point.within_window_drift_fraction > 0.15
    assert not point.is_stationary()                       # default 5% threshold
    assert not point.is_stationary(0.10)                   # also fails 10%
    assert point.is_stationary(0.20)                       # passes a generous 20%
    # And the raw_std would also flag this as noisy:
    assert point.raw_std > 100


def test_capture_stationary_under_realistic_creep_passes():
    """
    A301 logarithmic creep produces ~1.5% rise across the 0.5–2.5 s window
    even when MTS is perfectly stationary. Default is_stationary(0.05) must pass.
    """
    baseline = [50] * 100
    onset_and_settle = [1000] * 50
    # Linear approximation of creep across the window: 1000 → 1015 (1.5%)
    capture = [1000 + round(i * 15 / 199) for i in range(200)]
    cap = CalibrationCapture(
        make_frames(baseline + onset_and_settle + capture), channel=5
    )
    cap.arm()
    point = cap.acquire()
    # First half mean ≈ 1003.7, second half mean ≈ 1011.3, drift_fraction ≈ 0.75%
    assert 0.005 < point.within_window_drift_fraction < 0.015
    assert point.is_stationary()                           # 5% default passes
    assert not point.is_stationary(0.005)                  # tighter 0.5% would fail


def test_capture_stationary_constant_signal():
    """Perfectly constant signal → drift = 0, stationary at any threshold."""
    cap = CalibrationCapture(
        make_frames([50] * 100 + [1000] * 300), channel=5
    )
    cap.arm()
    point = cap.acquire()
    assert point.within_window_drift_fraction == 0.0
    assert point.is_stationary(0.0)
