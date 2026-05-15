"""
Layer C scaffolding — MTS bar-lowering control + Case 1 Condition C1 check.

**Scope: the Python-API control path.** Most lab MTS frames ship with
proprietary GUI software (MTS TestSuite, Instron Bluehill, Zwick testXpert,
Bose WinTest, etc.) and do not expose a Python API out of the box. If your
MTS is in that category, the practical C1 path is:
  (a) author a test method in the vendor software,
  (b) run it manually with the sensor,
  (c) export a force-time CSV,
  (d) analyse the CSV in Python (TBD module — to be added once the lab path
      is confirmed).
The control-side code in this module is the alternate path, useful only if
your MTS exposes an SDK, Modbus TCP, OPC-UA, or similar that lets external
Python drive the crosshead. It is committed as a reference contract +
working Mock + unit-tested control flow, ready to be wired up if API access
becomes available. See Task #5 (Verify MTS feasibility) for status.

Lower-until-force is the primitive operation under the API path: drive the
MTS crosshead downward at constant velocity, polling force, and stop the
moment the reading reaches target. Used for:
  - Case 1 Condition C1 feasibility check (can the MTS reach 4.4 N AND
    110 N in ≤ 0.5 s per Bill 0002 Part 3.2?).
  - Each per-level acquisition in the actual calibration session (paired
    with `CalibrationCapture` from Layer A).

The lab-specific concrete driver is the user's responsibility — implement
the `MTSDriver` Protocol against your hardware and pass the instance into
`lower_until_force()` or `c1_feasibility_check()`.

**ARTICLE II:** Running these functions against real hardware causes
physical motion of the MTS crosshead. Human-present approval is required
before execution. Nothing in this module auto-runs on import.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Protocol, runtime_checkable


@dataclass(frozen=True)
class MTSState:
    """A single (timestamp, position, force) snapshot from the MTS."""
    t_s: float
    position_mm: float
    force_N: float


@runtime_checkable
class MTSDriver(Protocol):
    """
    Contract for the lab MTS hardware driver.

    All methods are synchronous. `lower_at()` is non-blocking: it commands the
    crosshead to move and returns immediately; motion continues until `stop()`.
    """

    def home(self) -> None:
        """Return the bar to a known safe position with zero applied force."""
        ...

    def lower_at(self, velocity_mm_per_s: float) -> None:
        """Begin lowering the bar at the given velocity. Non-blocking."""
        ...

    def stop(self) -> None:
        """Halt motion immediately. Idempotent."""
        ...

    def read_state(self) -> MTSState:
        """Return the current (t, position, force) snapshot."""
        ...


@dataclass(frozen=True)
class LowerResult:
    target_N: float
    velocity_mm_per_s: float
    target_reached: bool
    time_to_target_s: float | None
    peak_force_N: float
    final_force_N: float
    final_position_mm: float
    n_samples: int
    samples: list[MTSState] = field(default_factory=list, repr=False)


def lower_until_force(
    driver: MTSDriver,
    target_N: float,
    *,
    velocity_mm_per_s: float = 10.0,
    max_displacement_mm: float = 5.0,
    poll_period_s: float = 0.001,
    timeout_s: float = 10.0,
) -> LowerResult:
    """
    Lower the MTS bar at constant velocity until force ≥ `target_N`.

    Always calls `driver.stop()` on exit (success, safety abort, or exception).
    Records the full state stream so the caller can inspect the force profile
    (overshoot, settling time, velocity actually achieved, etc.).

    Stops on the first of:
      - Force reads ≥ target_N → target_reached = True
      - |displacement| ≥ max_displacement_mm (safety limit)
      - elapsed ≥ timeout_s (deadlock guard)

    Args:
        driver: any object satisfying `MTSDriver`.
        target_N: force threshold to stop at.
        velocity_mm_per_s: positive downward velocity.
        max_displacement_mm: safety limit on bar travel from start.
        poll_period_s: how often to read force during descent.
        timeout_s: hard time limit.

    Returns:
        LowerResult with target_reached, time_to_target_s, peak_force_N,
        and the full sample stream.
    """
    start_state = driver.read_state()
    start_time = start_state.t_s
    start_position = start_state.position_mm

    samples: list[MTSState] = [start_state]
    peak_force = start_state.force_N
    target_reached = False
    time_to_target: float | None = None

    driver.lower_at(velocity_mm_per_s)
    try:
        while True:
            time.sleep(poll_period_s)
            state = driver.read_state()
            samples.append(state)
            if state.force_N > peak_force:
                peak_force = state.force_N

            elapsed = state.t_s - start_time
            displacement = abs(state.position_mm - start_position)

            if state.force_N >= target_N:
                target_reached = True
                time_to_target = elapsed
                break
            if displacement >= max_displacement_mm:
                break
            if elapsed >= timeout_s:
                break
    finally:
        driver.stop()

    final_state = driver.read_state()
    return LowerResult(
        target_N=target_N,
        velocity_mm_per_s=velocity_mm_per_s,
        target_reached=target_reached,
        time_to_target_s=time_to_target,
        peak_force_N=peak_force,
        final_force_N=final_state.force_N,
        final_position_mm=final_state.position_mm,
        n_samples=len(samples),
        samples=samples,
    )


@dataclass(frozen=True)
class C1LevelResult:
    target_N: float
    velocity_mm_per_s: float
    target_reached: bool
    time_to_target_s: float | None
    peak_force_N: float
    passed_C1: bool


@dataclass(frozen=True)
class C1Report:
    threshold_s: float
    levels: list[C1LevelResult]
    overall_passed: bool


def c1_feasibility_check(
    driver: MTSDriver,
    *,
    levels_N: list[float] | None = None,
    velocity_mm_per_s: float = 10.0,
    threshold_s: float = 0.5,
    settle_between_levels_s: float = 5.0,
    max_displacement_mm: float = 5.0,
    poll_period_s: float = 0.001,
) -> C1Report:
    """
    Case 1 Condition C1: time-to-target on A301-1 FS (4.4 N) and A301-25 FS (110 N).

    For each level, home the bar, lower at constant velocity until force ≥ level
    or a safety limit triggers, and record time-to-target. C1 passes iff every
    level reaches target within `threshold_s` (default 0.5 s per Bill 0002 Part 3.2).

    Default levels: [4.4, 110.0] N — the A301-1 and A301-25 full-scale values
    used in Bill 0002. Adjust `velocity_mm_per_s` per your MTS to find the
    minimum time-to-target your hardware can achieve.
    """
    if levels_N is None:
        levels_N = [4.4, 110.0]

    results: list[C1LevelResult] = []
    for target in levels_N:
        driver.home()
        time.sleep(1.0)
        result = lower_until_force(
            driver,
            target_N=target,
            velocity_mm_per_s=velocity_mm_per_s,
            max_displacement_mm=max_displacement_mm,
            poll_period_s=poll_period_s,
        )
        passed = (
            result.target_reached
            and result.time_to_target_s is not None
            and result.time_to_target_s <= threshold_s
        )
        results.append(
            C1LevelResult(
                target_N=target,
                velocity_mm_per_s=velocity_mm_per_s,
                target_reached=result.target_reached,
                time_to_target_s=result.time_to_target_s,
                peak_force_N=result.peak_force_N,
                passed_C1=passed,
            )
        )
        if target != levels_N[-1]:
            time.sleep(settle_between_levels_s)

    return C1Report(
        threshold_s=threshold_s,
        levels=results,
        overall_passed=all(r.passed_C1 for r in results),
    )


def write_c1_report(
    report: C1Report,
    date: str,
    operator: str,
    output_dir: Path | str = "docs/c1_check",
) -> Path:
    """
    Write the C1 report to `<output_dir>/c1_check_<YYYYMMDD>.json` for the case_law
    follow-up record on Condition C1 (Case 1, 2026-05-15).

    `date` is YYYY-MM-DD; the filename uses YYYYMMDD.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "case_law_reference": "Case 1, Condition C1",
        "bill_reference": "Bill 0002 Part 3.2",
        "check_date": date,
        "operator": operator,
        "threshold_s": report.threshold_s,
        "overall_passed": report.overall_passed,
        "levels": [asdict(r) for r in report.levels],
    }
    path = output_dir / f"c1_check_{date.replace('-', '')}.json"
    path.write_text(json.dumps(record, indent=2))
    return path


# ----------------------------------------------------------------------
# Mock driver for unit tests.
#
# Simulates an MTS following Hooke's law: F = position × stiffness.
# Real MTS frames are more complex (controller dynamics, friction,
# overshoot) — this Mock is sufficient for testing the control-flow
# logic of lower_until_force() and c1_feasibility_check() but is NOT
# a substitute for testing against the real hardware.
# ----------------------------------------------------------------------


class MockMTSDriver:
    """
    Deterministic MTS simulator. Force follows a linear Hooke's-law model:
    `force_N = max(0, position_mm × stiffness_N_per_mm)`.
    Position advances linearly while moving.
    """

    def __init__(
        self,
        stiffness_N_per_mm: float = 50.0,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.stiffness = stiffness_N_per_mm
        self.clock = clock or time.monotonic
        self._velocity = 0.0
        self._position_mm = 0.0
        self._position_at_lower_start_mm = 0.0
        self._t_at_lower_start: float | None = None

    def home(self) -> None:
        self._velocity = 0.0
        self._position_mm = 0.0
        self._t_at_lower_start = None

    def lower_at(self, velocity_mm_per_s: float) -> None:
        # Freeze current position before changing motion state.
        self._position_mm = self._current_position()
        self._velocity = velocity_mm_per_s
        self._t_at_lower_start = self.clock()
        self._position_at_lower_start_mm = self._position_mm

    def stop(self) -> None:
        self._position_mm = self._current_position()
        self._velocity = 0.0
        self._t_at_lower_start = None

    def read_state(self) -> MTSState:
        t = self.clock()
        pos = self._current_position()
        force = max(0.0, pos * self.stiffness)
        return MTSState(t_s=t, position_mm=pos, force_N=force)

    def _current_position(self) -> float:
        if self._velocity == 0.0 or self._t_at_lower_start is None:
            return self._position_mm
        elapsed = self.clock() - self._t_at_lower_start
        return self._position_at_lower_start_mm + self._velocity * elapsed
