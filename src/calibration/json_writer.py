"""
Layer B — calibration JSON record writer.

Implements Bill 0002 Part 6.2 schema, extended by Bill 0003 Clause (e) to
include `force_source` and `dead_weight_records` fields for the dead-weight
calibration path (Case 2, 2026-05-19; A301-1 channels Ch0–Ch4 only).

The `CURVE_FIT — derived from ...` field is the project-specific implementation
of Amendment 7's documentation format (Case 1, 2026-05-15).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.calibration.fit import Acceptance, FitResult


@dataclass(frozen=True)
class CalibrationPointRecord:
    level_index: int
    applied_N: float
    raw_mean: float
    raw_std: float
    repeats: int


def build_calibration_record(
    *,
    channel: int,
    sensor_model: str,
    physical_location: str,
    calibration_date: str,
    operator: str,
    full_scale_N: float,
    quiescent_load_N: float,
    fit: FitResult,
    acceptance: Acceptance,
    points: list[CalibrationPointRecord],
    acquisition_window_s: tuple[float, float] = (0.5, 2.5),
    force_source: str = "mts",
    dead_weight_records: list[dict] | None = None,
    fixture_stack: dict | None = None,
) -> dict:
    """
    Assemble the per-channel calibration record per Bill 0002 Part 6.2,
    extended by Bill 0003 Clause (e).

    `calibration_date` is YYYY-MM-DD. The Amendment 7 traceability field is
    inlined here; do not rename its key — the police agent and code-reviewer
    both look it up by name.

    `force_source` is "mts" (Bill 0002 path) or "dead_weight" (Bill 0003 path).
    For "dead_weight", `dead_weight_records` is the top-level traceability list
    (one entry per weight used in the session); the per-point dead_weight_record
    is attached by build_deadweight_calibration_record after this function returns.
    """
    if force_source not in ("mts", "dead_weight"):
        raise ValueError(
            f"force_source must be 'mts' or 'dead_weight'; got {force_source!r}"
        )
    if force_source == "mts" and dead_weight_records is not None:
        raise ValueError(
            "dead_weight_records must be None when force_source='mts'"
        )
    if force_source == "dead_weight" and not dead_weight_records:
        raise ValueError(
            "dead_weight_records required when force_source='dead_weight'"
        )

    if force_source == "mts":
        curve_fit_key = "CURVE_FIT — derived from Contact Force primitive (Amendment 1)"
        curve_fit_value = (
            "Physical derivation: piezoresistive conductance F = a * raw^b; "
            "fit in log-log space via OLS. "
            f"Value: a = {fit.a:.6g} N*ADC^-b, b = {fit.b:.6g} dimensionless. "
            "Traces to: Amendment 1 primitive 1 (Contact Force)."
        )
        amendment_grounding = "Amendment 1, Amendment 7"
    elif fixture_stack is not None:
        curve_fit_key = (
            "CURVE_FIT — derived from Contact Force primitive (Amendment 1), "
            "dead-weight + TPU pad path (Bills 0003 + 0004)"
        )
        curve_fit_value = (
            "Physical derivation: F = m * g, g = 9.80665 m/s^2 (CGPM 1901). "
            "Fixturing stack: weight -> backing disc -> TPU 95A 1 mm pad -> "
            "A301-1 sensor surface. Pad installed identically at calibration "
            "and trial. Curve fit: F(raw) = a * raw^b; fit in log-log space "
            f"via OLS. Value: a = {fit.a:.6g} N*ADC^-b, b = {fit.b:.6g} "
            "dimensionless. Traces to: Amendment 1 primitive 1 (Contact "
            "Force), Amendment 7 (Calibration Discipline), Case 3."
        )
        amendment_grounding = (
            "Amendment 1, Amendment 7, Bill 0003 (Case 2), Bill 0004 (Case 3)"
        )
    else:
        curve_fit_key = (
            "CURVE_FIT — derived from Contact Force primitive (Amendment 1), "
            "dead-weight path (Bill 0003)"
        )
        curve_fit_value = (
            "Physical derivation: F = m * g, g = 9.80665 m/s^2 (CGPM 1901). "
            "Mass uncertainty for OIML M1 at 0.5 kg is <= 0.025 g -> force "
            "uncertainty <= 0.00025 N. Curve fit: F(raw) = a * raw^b; fit in "
            f"log-log space via OLS. Value: a = {fit.a:.6g} N*ADC^-b, "
            f"b = {fit.b:.6g} dimensionless. Traces to: Amendment 1 primitive "
            "1 (Contact Force), Amendment 7 (Calibration Discipline)."
        )
        amendment_grounding = "Amendment 1, Amendment 7, Bill 0003 (Case 2)"

    record: dict = {
        "channel": channel,
        "sensor_model": sensor_model,
        "physical_location": physical_location,
        "calibration_date": calibration_date,
        "operator": operator,
        "mts_used": force_source == "mts",
        "force_source": force_source,
        "primitive": "Contact Force",
        "amendment_grounding": amendment_grounding,
        curve_fit_key: curve_fit_value,
        "a": fit.a,
        "b": fit.b,
        "full_scale_N": full_scale_N,
        "quiescent_load_N": quiescent_load_N,
        "acquisition_window_s": list(acquisition_window_s),
        "acceptance": {
            "rms_residual_N": acceptance.rms_residual_N,
            "max_residual_N": acceptance.max_residual_N,
            "adj_r_squared_loglog": acceptance.adj_r_squared_loglog,
            "rms_criterion_N": acceptance.rms_criterion_N,
            "max_criterion_N": acceptance.max_criterion_N,
            "r_squared_criterion": acceptance.r_squared_criterion,
            "passed": acceptance.passed,
            "failures": list(acceptance.failures),
        },
        "calibration_points": [
            {
                "level_index": p.level_index,
                "applied_N": p.applied_N,
                "raw_mean": p.raw_mean,
                "raw_std": p.raw_std,
                "repeats": p.repeats,
            }
            for p in points
        ],
    }

    if force_source == "dead_weight":
        record["dead_weight_records"] = list(dead_weight_records or [])

    if fixture_stack is not None:
        if force_source != "dead_weight":
            raise ValueError(
                "fixture_stack is only valid for force_source='dead_weight' "
                "(Bill 0004 builds on Bill 0003)"
            )
        record["fixture_stack"] = fixture_stack

    return record


def write_calibration_json(
    record: dict,
    output_dir: Path | str = "docs/calibration",
) -> Path:
    """
    Write record to `<output_dir>/ch<N>_<YYYYMMDD>.json`.
    Filename derived from `record["channel"]` and `record["calibration_date"]`.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    channel = record["channel"]
    cal_date = record["calibration_date"].replace("-", "")
    path = output_dir / f"ch{channel}_{cal_date}.json"
    path.write_text(json.dumps(record, indent=2))
    return path
