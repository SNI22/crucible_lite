"""Tests for src.calibration.deadweight (Bill 0003, Case 2)."""
from __future__ import annotations

import math

import pytest

from src.calibration.capture import CalibrationCapture
from src.calibration.deadweight import (
    A301_1_CHANNELS,
    CGPM_GRAVITY_M_PER_S2,
    DeadWeightRecord,
    ScopeError,
    acquire_level,
    build_deadweight_calibration_record,
    check_scope,
    deadweight_force_N,
)
from src.calibration.fit import check_acceptance, fit_power_law
from src.calibration.json_writer import CalibrationPointRecord


# ----------------------------------------------------------------------
# CGPM gravity and mass-to-force conversion
# ----------------------------------------------------------------------


def test_cgpm_gravity_is_invariant():
    """CGPM 1901 standard gravity = 9.80665 m/s^2 exactly."""
    assert CGPM_GRAVITY_M_PER_S2 == 9.80665


def test_deadweight_force_500g():
    """500 g -> 4.903 N (Bill 0003 weight set, top of A301-1 range)."""
    assert math.isclose(deadweight_force_N(0.500), 4.903325, rel_tol=1e-9)


def test_deadweight_force_50g():
    """50 g -> 0.490 N (Bill 0003 weight set, bottom of A301-1 range)."""
    assert math.isclose(deadweight_force_N(0.050), 0.4903325, rel_tol=1e-9)


def test_deadweight_force_zero_mass():
    """Zero mass is permitted (e.g., quiescent baseline) and yields 0 N."""
    assert deadweight_force_N(0.0) == 0.0


def test_deadweight_force_rejects_negative_mass():
    with pytest.raises(ValueError, match="mass_kg must be >= 0"):
        deadweight_force_N(-0.1)


# ----------------------------------------------------------------------
# DeadWeightRecord validation
# ----------------------------------------------------------------------


def _good_record(mass_kg: float = 0.200) -> DeadWeightRecord:
    return DeadWeightRecord(
        mass_kg=mass_kg,
        oiml_class="M1",
        certificate_id="MASSCAL-2026-0042",
        traceable_to="NRC Canada mass standard",
    )


def test_dead_weight_record_serialises_g_m_per_s2():
    """as_json_block must include the CGPM gravity for Amendment 7 traceability."""
    block = _good_record().as_json_block()
    assert block["g_m_per_s2"] == CGPM_GRAVITY_M_PER_S2
    assert block["mass_kg"] == 0.200
    assert block["oiml_class"] == "M1"
    assert block["certificate_id"] == "MASSCAL-2026-0042"
    assert block["traceable_to"] == "NRC Canada mass standard"


def test_dead_weight_record_rejects_zero_mass():
    with pytest.raises(ValueError, match="mass_kg must be > 0"):
        DeadWeightRecord(
            mass_kg=0.0,
            oiml_class="M1",
            certificate_id="x",
            traceable_to="x",
        )


def test_dead_weight_record_requires_oiml_class():
    with pytest.raises(ValueError, match="oiml_class is required"):
        DeadWeightRecord(
            mass_kg=0.1, oiml_class="", certificate_id="x", traceable_to="x"
        )


def test_dead_weight_record_requires_certificate_id():
    with pytest.raises(ValueError, match="certificate_id is required"):
        DeadWeightRecord(
            mass_kg=0.1, oiml_class="M1", certificate_id="", traceable_to="x"
        )


def test_dead_weight_record_requires_traceable_to():
    with pytest.raises(ValueError, match="traceable_to is required"):
        DeadWeightRecord(
            mass_kg=0.1, oiml_class="M1", certificate_id="x", traceable_to=""
        )


# ----------------------------------------------------------------------
# Channel scope (Bill 0003 Clause (a))
# ----------------------------------------------------------------------


def test_a301_1_channels_is_0_through_4():
    assert A301_1_CHANNELS == frozenset({0, 1, 2, 3, 4})


@pytest.mark.parametrize("ch", [0, 1, 2, 3, 4])
def test_check_scope_accepts_a301_1(ch):
    check_scope(ch)  # no raise


@pytest.mark.parametrize("ch", [5, 6, 7, -1, 99])
def test_check_scope_rejects_a301_25_and_invalid(ch):
    with pytest.raises(ScopeError, match="A301-1 only"):
        check_scope(ch)


# ----------------------------------------------------------------------
# acquire_level — coordination wrapper
# ----------------------------------------------------------------------


def _synthetic_frames(
    channel: int,
    baseline_counts: int,
    loaded_counts: int,
    n_baseline: int,
    n_loaded: int,
):
    """Build a frame iterator: baseline frames then step to loaded value."""
    for i in range(n_baseline):
        frame = [i] + [baseline_counts] * 8
        yield frame
    for i in range(n_loaded):
        frame = [n_baseline + i] + [loaded_counts] * 8
        yield frame


def test_acquire_level_pairs_capture_with_mass_to_force():
    """acquire_level returns (point, applied_N) on an A301-1 channel."""
    frames = _synthetic_frames(
        channel=2, baseline_counts=100, loaded_counts=800,
        n_baseline=120, n_loaded=400,
    )
    capture = CalibrationCapture(
        frames, channel=2,
        sample_rate_hz=100.0, baseline_s=1.0,
        onset_sigma=5.0, onset_min_counts=30,
        max_wait_s=2.0, window_s=(0.5, 2.5),
    )
    capture.arm()
    weight = _good_record(mass_kg=0.200)
    point, applied_N = acquire_level(capture, weight)
    assert point.channel == 2
    assert math.isclose(applied_N, 0.200 * CGPM_GRAVITY_M_PER_S2, rel_tol=1e-9)
    assert point.raw_mean > 700  # captured the loaded step


def test_acquire_level_rejects_a301_25_channel():
    """Calling acquire_level on Ch5 is a ScopeError before any DAQ I/O."""
    frames = _synthetic_frames(
        channel=5, baseline_counts=100, loaded_counts=800,
        n_baseline=120, n_loaded=400,
    )
    capture = CalibrationCapture(frames, channel=5)
    capture.arm()
    with pytest.raises(ScopeError):
        acquire_level(capture, _good_record())


# ----------------------------------------------------------------------
# JSON record builder
# ----------------------------------------------------------------------


def _eight_synthetic_points() -> tuple[list[CalibrationPointRecord], list[DeadWeightRecord]]:
    """Eight points on a clean F = 0.005 * raw^1.0 curve, raw in 100–1000."""
    weights = [
        DeadWeightRecord(mass_kg=m, oiml_class="M1",
                         certificate_id=f"C{i:02d}",
                         traceable_to="NRC Canada")
        for i, m in enumerate(
            [0.050, 0.100, 0.150, 0.200, 0.250, 0.300, 0.350, 0.500]
        )
    ]
    points = []
    for i, w in enumerate(weights):
        applied = deadweight_force_N(w.mass_kg)
        raw = applied / 0.005  # invert F = 0.005 * raw -> raw = F / 0.005
        points.append(CalibrationPointRecord(
            level_index=i, applied_N=applied,
            raw_mean=raw, raw_std=2.0, repeats=3,
        ))
    return points, weights


def test_build_deadweight_record_shape_and_fields():
    points, weights = _eight_synthetic_points()
    fit = fit_power_law([(p.raw_mean, p.applied_N) for p in points])
    acc = check_acceptance(fit, full_scale_N=4.4)

    record = build_deadweight_calibration_record(
        channel=2,
        sensor_model="A301-1",
        physical_location="table-foot, position TL",
        calibration_date="2026-05-20",
        operator="shiyao",
        full_scale_N=4.4,
        quiescent_load_N=0.0,
        fit=fit,
        acceptance=acc,
        points=points,
        weights_used=weights,
    )

    # Bill 0003 Clause (e) required fields
    assert record["force_source"] == "dead_weight"
    assert record["mts_used"] is False
    assert record["channel"] == 2
    assert "dead_weight_records" in record
    assert len(record["dead_weight_records"]) == 8
    # Amendment 7 header swapped to dead-weight variant
    dw_header = (
        "CURVE_FIT — derived from Contact Force primitive (Amendment 1), "
        "dead-weight path (Bill 0003)"
    )
    assert dw_header in record
    # MTS-variant header MUST be absent for a dead-weight record
    mts_header = "CURVE_FIT — derived from Contact Force primitive (Amendment 1)"
    assert mts_header not in record
    # Per-point dead_weight_record attached
    for pt, w in zip(record["calibration_points"], weights):
        assert pt["dead_weight_record"]["mass_kg"] == w.mass_kg
        assert pt["dead_weight_record"]["oiml_class"] == "M1"
        assert pt["dead_weight_record"]["g_m_per_s2"] == CGPM_GRAVITY_M_PER_S2
    # Bill 0003 grounding cited
    assert "Bill 0003" in record["amendment_grounding"]


def test_build_deadweight_record_rejects_out_of_scope_channel():
    points, weights = _eight_synthetic_points()
    fit = fit_power_law([(p.raw_mean, p.applied_N) for p in points])
    acc = check_acceptance(fit, full_scale_N=4.4)
    with pytest.raises(ScopeError):
        build_deadweight_calibration_record(
            channel=5,
            sensor_model="A301-25",
            physical_location="finger-pad, right",
            calibration_date="2026-05-20",
            operator="shiyao",
            full_scale_N=110.0,
            quiescent_load_N=0.0,
            fit=fit, acceptance=acc,
            points=points, weights_used=weights,
        )


def test_build_deadweight_record_rejects_mismatched_lengths():
    points, weights = _eight_synthetic_points()
    fit = fit_power_law([(p.raw_mean, p.applied_N) for p in points])
    acc = check_acceptance(fit, full_scale_N=4.4)
    with pytest.raises(ValueError, match="each calibration point must cite"):
        build_deadweight_calibration_record(
            channel=0,
            sensor_model="A301-1",
            physical_location="table-foot",
            calibration_date="2026-05-20",
            operator="shiyao",
            full_scale_N=4.4,
            quiescent_load_N=0.0,
            fit=fit, acceptance=acc,
            points=points, weights_used=weights[:7],  # off by one
        )


def test_build_deadweight_record_rejects_empty_weights_list():
    points, _ = _eight_synthetic_points()
    fit = fit_power_law([(p.raw_mean, p.applied_N) for p in points])
    acc = check_acceptance(fit, full_scale_N=4.4)
    with pytest.raises(ValueError, match="at least one DeadWeightRecord"):
        build_deadweight_calibration_record(
            channel=0,
            sensor_model="A301-1",
            physical_location="table-foot",
            calibration_date="2026-05-20",
            operator="shiyao",
            full_scale_N=4.4,
            quiescent_load_N=0.0,
            fit=fit, acceptance=acc,
            points=points, weights_used=[],
        )


# ----------------------------------------------------------------------
# json_writer.build_calibration_record — force_source param validation
# ----------------------------------------------------------------------


def test_build_calibration_record_mts_default_still_works():
    """Backward-compat: default force_source='mts' yields the Bill 0002 schema."""
    from src.calibration.json_writer import build_calibration_record
    points, _ = _eight_synthetic_points()
    fit = fit_power_law([(p.raw_mean, p.applied_N) for p in points])
    acc = check_acceptance(fit, full_scale_N=4.4)

    record = build_calibration_record(
        channel=0,
        sensor_model="A301-1",
        physical_location="table-foot",
        calibration_date="2026-05-20",
        operator="shiyao",
        full_scale_N=4.4,
        quiescent_load_N=0.0,
        fit=fit, acceptance=acc, points=points,
    )
    assert record["force_source"] == "mts"
    assert record["mts_used"] is True
    assert "dead_weight_records" not in record
    assert (
        "CURVE_FIT — derived from Contact Force primitive (Amendment 1)"
        in record
    )


def test_build_calibration_record_rejects_dead_weight_without_records():
    from src.calibration.json_writer import build_calibration_record
    points, _ = _eight_synthetic_points()
    fit = fit_power_law([(p.raw_mean, p.applied_N) for p in points])
    acc = check_acceptance(fit, full_scale_N=4.4)
    with pytest.raises(ValueError, match="dead_weight_records required"):
        build_calibration_record(
            channel=0,
            sensor_model="A301-1",
            physical_location="table-foot",
            calibration_date="2026-05-20",
            operator="shiyao",
            full_scale_N=4.4,
            quiescent_load_N=0.0,
            fit=fit, acceptance=acc, points=points,
            force_source="dead_weight",
        )


def test_build_calibration_record_rejects_mts_with_records():
    from src.calibration.json_writer import build_calibration_record
    points, weights = _eight_synthetic_points()
    fit = fit_power_law([(p.raw_mean, p.applied_N) for p in points])
    acc = check_acceptance(fit, full_scale_N=4.4)
    with pytest.raises(ValueError, match="must be None when force_source='mts'"):
        build_calibration_record(
            channel=0,
            sensor_model="A301-1",
            physical_location="table-foot",
            calibration_date="2026-05-20",
            operator="shiyao",
            full_scale_N=4.4,
            quiescent_load_N=0.0,
            fit=fit, acceptance=acc, points=points,
            force_source="mts",
            dead_weight_records=[w.as_json_block() for w in weights],
        )


def test_build_calibration_record_rejects_unknown_force_source():
    from src.calibration.json_writer import build_calibration_record
    points, _ = _eight_synthetic_points()
    fit = fit_power_law([(p.raw_mean, p.applied_N) for p in points])
    acc = check_acceptance(fit, full_scale_N=4.4)
    with pytest.raises(ValueError, match="must be 'mts' or 'dead_weight'"):
        build_calibration_record(
            channel=0,
            sensor_model="A301-1",
            physical_location="table-foot",
            calibration_date="2026-05-20",
            operator="shiyao",
            full_scale_N=4.4,
            quiescent_load_N=0.0,
            fit=fit, acceptance=acc, points=points,
            force_source="balloon",
        )
