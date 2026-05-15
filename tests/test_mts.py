"""Tests for src.calibration.mts using MockMTSDriver."""
from __future__ import annotations

from src.calibration.mts import (
    MockMTSDriver,
    MTSDriver,
    c1_feasibility_check,
    lower_until_force,
)


def test_mock_driver_satisfies_protocol():
    """The Mock implements the Protocol (runtime_checkable)."""
    driver = MockMTSDriver()
    assert isinstance(driver, MTSDriver)


def test_lower_until_force_reaches_target_fast_mts():
    """High-stiffness, high-velocity MTS reaches 4.4 N quickly."""
    driver = MockMTSDriver(stiffness_N_per_mm=1000.0)
    result = lower_until_force(
        driver, target_N=4.4, velocity_mm_per_s=100.0, poll_period_s=0.001
    )
    assert result.target_reached
    assert result.time_to_target_s is not None
    assert result.time_to_target_s < 0.5
    assert result.peak_force_N >= 4.4


def test_lower_until_force_safety_stops_on_displacement():
    """Tight max_displacement halts the bar before target is reached."""
    driver = MockMTSDriver(stiffness_N_per_mm=0.1)  # too soft to reach 110 N in 2 mm
    result = lower_until_force(
        driver,
        target_N=110.0,
        velocity_mm_per_s=10.0,
        max_displacement_mm=2.0,
        poll_period_s=0.001,
        timeout_s=2.0,
    )
    assert not result.target_reached
    assert abs(result.final_position_mm) <= 2.0 + 0.05  # tolerate one extra poll
    # At pos=2 mm with stiffness=0.1, force=0.2 N — well below 110.
    assert result.peak_force_N < 1.0


def test_lower_until_force_calls_stop_even_on_completion():
    """After target reached, the driver must be stopped (no runaway)."""
    driver = MockMTSDriver(stiffness_N_per_mm=1000.0)
    lower_until_force(
        driver, target_N=4.4, velocity_mm_per_s=100.0, poll_period_s=0.001
    )
    # After return, driver._velocity should be zero — internal state, but
    # behaviour-visible via read_state: position should not change anymore.
    s1 = driver.read_state()
    import time as _t

    _t.sleep(0.01)
    s2 = driver.read_state()
    assert abs(s1.position_mm - s2.position_mm) < 1e-9


def test_c1_feasibility_check_passes_capable_mts():
    """Very stiff, very fast MTS passes both 4.4 N and 110 N levels."""
    driver = MockMTSDriver(stiffness_N_per_mm=10000.0)
    report = c1_feasibility_check(
        driver,
        velocity_mm_per_s=100.0,
        threshold_s=0.5,
        settle_between_levels_s=0.01,
        max_displacement_mm=2.0,
        poll_period_s=0.001,
    )
    assert report.overall_passed
    assert len(report.levels) == 2
    for level in report.levels:
        assert level.passed_C1
        assert level.time_to_target_s is not None
        assert level.time_to_target_s < 0.5


def test_c1_feasibility_check_fails_slow_mts():
    """Soft, slow MTS misses both targets within the 0.5 s threshold."""
    driver = MockMTSDriver(stiffness_N_per_mm=1.0)
    report = c1_feasibility_check(
        driver,
        velocity_mm_per_s=1.0,
        threshold_s=0.5,
        settle_between_levels_s=0.01,
        max_displacement_mm=2.0,
        poll_period_s=0.001,
    )
    assert not report.overall_passed
    # At least the 110 N level must fail (stiffness 1, max disp 2 mm → 2 N peak).
    assert not report.levels[1].passed_C1
