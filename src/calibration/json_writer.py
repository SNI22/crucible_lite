"""
Layer B — calibration JSON record writer.

Implements Bill 0002 Part 6.2 schema. The `CURVE_FIT — derived from ...`
field is the project-specific implementation of Amendment 7's documentation
format (Case 1, 2026-05-15).
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
) -> dict:
    """
    Assemble the per-channel calibration record per Bill 0002 Part 6.2.

    `calibration_date` is YYYY-MM-DD. The Amendment 7 traceability field is
    inlined here; do not rename its key — the police agent and code-reviewer
    both look it up by name.
    """
    return {
        "channel": channel,
        "sensor_model": sensor_model,
        "physical_location": physical_location,
        "calibration_date": calibration_date,
        "operator": operator,
        "mts_used": True,
        "primitive": "Contact Force",
        "amendment_grounding": "Amendment 1, Amendment 7",
        "CURVE_FIT — derived from Contact Force primitive (Amendment 1)": (
            "Physical derivation: piezoresistive conductance F = a * raw^b; "
            "fit in log-log space via OLS. "
            f"Value: a = {fit.a:.6g} N*ADC^-b, b = {fit.b:.6g} dimensionless. "
            "Traces to: Amendment 1 primitive 1 (Contact Force)."
        ),
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
