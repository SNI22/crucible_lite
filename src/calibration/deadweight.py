"""
Layer D — Dead-weight calibration force source (Bill 0003 / Case 2).

Enacted: 2026-05-19. Scope: A301-1 channels Ch0–Ch4 ONLY.

Provides the mass-to-force conversion (F = m * g, CGPM 1901 standard gravity),
the OIML traceability record, a scope check that enforces the A301-1 channel
restriction, and a coordination wrapper that pairs a CalibrationCapture
acquisition with a calibrated mass to yield one (raw, applied_N) point ready
for fit.py.

The acquisition protocol itself (window, sigma-threshold, repeats, sensor
conditioning) is UNCHANGED from Bill 0002 Part 3 — only the force-generation
source is substituted. The DAQ-stream onset detector in capture.py resolves
t = 0 from the signal; the operator does not need to time the placement.

**Channel scope (Bill 0003 Clause (a)):** dead-weight is admissible for Ch0–Ch4
(A301-1) only. For Ch5–Ch6 (A301-25) the MTS path under Bill 0002 must be
used; invoking this module on a Ch5–Ch6 capture raises ScopeError.

**ARTICLE II:** Mass placement is a manual operator action. This module does
not move hardware autonomously. Onset detection from the DAQ stream means the
caller is responsible only for placing the weight; capture.py resolves the
timing.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from src.calibration.capture import CalibrationCapture, CalibrationPoint
from src.calibration.fit import Acceptance, FitResult
from src.calibration.json_writer import (
    CalibrationPointRecord,
    build_calibration_record,
)


# CGPM 1901 standard gravity. Physically derived constant — Amendment 7 prohibits
# tuning. Traces to Amendment 1 primitive 1 (Contact Force) via F = m * g.
CGPM_GRAVITY_M_PER_S2: float = 9.80665

# Bill 0003 Clause (a): dead-weight path is admissible for A301-1 only.
A301_1_CHANNELS: frozenset[int] = frozenset({0, 1, 2, 3, 4})


class ScopeError(ValueError):
    """Raised when the dead-weight path is invoked on a channel outside A301-1."""


@dataclass(frozen=True)
class DeadWeightRecord:
    """
    OIML traceability metadata for one calibrated mass (Bill 0003 Clause (e),
    Case 2 Condition C3).

    Every weight used during a Bill 0003 calibration session is associated with
    one record. The record is serialised into the JSON `dead_weight_record`
    block per Bill 0003 Clause (e).
    """
    mass_kg: float
    oiml_class: str           # "M1" or finer (e.g., "F2", "F1", "E2")
    certificate_id: str       # vendor or lab certificate number
    traceable_to: str         # e.g., "NRC Canada mass standard"

    def __post_init__(self) -> None:
        if self.mass_kg <= 0:
            raise ValueError(f"mass_kg must be > 0; got {self.mass_kg!r}")
        if not self.oiml_class:
            raise ValueError("oiml_class is required (e.g., 'M1')")
        if not self.certificate_id:
            raise ValueError("certificate_id is required (Case 2 C3)")
        if not self.traceable_to:
            raise ValueError("traceable_to is required (Case 2 C3)")

    def as_json_block(self) -> dict:
        """Return the JSON sub-record per Bill 0003 Clause (e)."""
        block = asdict(self)
        block["g_m_per_s2"] = CGPM_GRAVITY_M_PER_S2
        return block


def deadweight_force_N(mass_kg: float) -> float:
    """
    FORCE — derived from Contact Force primitive (Amendment 1).
    Physical derivation: F = m * g, g = 9.80665 m/s^2 (CGPM 1901 standard gravity).
    Traces to: Amendment 1 primitive 1 (Contact Force), Amendment 7 (Calibration
    Discipline), Bill 0003 Clause (d).
    """
    if mass_kg < 0:
        raise ValueError(f"mass_kg must be >= 0; got {mass_kg!r}")
    return mass_kg * CGPM_GRAVITY_M_PER_S2


def check_scope(channel: int) -> None:
    """Raise ScopeError if channel is outside A301-1 (Bill 0003 Clause (a))."""
    if channel not in A301_1_CHANNELS:
        raise ScopeError(
            f"Channel {channel} is out of Bill 0003 scope (A301-1 only, Ch0-Ch4). "
            "For A301-25 (Ch5-Ch6) use the MTS path under Bill 0002."
        )


def acquire_level(
    capture: CalibrationCapture,
    weight: DeadWeightRecord,
) -> tuple[CalibrationPoint, float]:
    """
    Coordination wrapper for one calibration level on the dead-weight path.

    The caller is expected to:
      1. Verify the sensor is unloaded.
      2. Call capture.arm() to record baseline.
      3. Place the calibrated mass on the sensor (operator action).
      4. Call this function: it invokes capture.acquire() (which detects onset
         from the DAQ stream), then computes F = m * g.

    Returns:
        (CalibrationPoint, applied_N) ready to be paired into fit_power_law.

    Raises:
        ScopeError if capture.channel is outside A301-1.
    """
    check_scope(capture.channel)
    point = capture.acquire()
    applied_N = deadweight_force_N(weight.mass_kg)
    return point, applied_N


def build_deadweight_calibration_record(
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
    weights_used: list[DeadWeightRecord],
    acquisition_window_s: tuple[float, float] = (0.5, 2.5),
) -> dict:
    """
    Assemble the calibration record for a dead-weight calibration session.

    Delegates the base record to json_writer.build_calibration_record with
    force_source='dead_weight', then attaches per-point weight metadata
    (Bill 0003 Clause (e)).

    Raises:
        ScopeError if channel is outside A301-1.
        ValueError if weights_used is empty or its length does not match points.
    """
    check_scope(channel)
    if not weights_used:
        raise ValueError("weights_used must contain at least one DeadWeightRecord")
    if len(weights_used) != len(points):
        raise ValueError(
            f"weights_used has {len(weights_used)} entries but points has "
            f"{len(points)}; each calibration point must cite its applied weight"
        )

    record = build_calibration_record(
        channel=channel,
        sensor_model=sensor_model,
        physical_location=physical_location,
        calibration_date=calibration_date,
        operator=operator,
        full_scale_N=full_scale_N,
        quiescent_load_N=quiescent_load_N,
        fit=fit,
        acceptance=acceptance,
        points=points,
        acquisition_window_s=acquisition_window_s,
        force_source="dead_weight",
        dead_weight_records=[w.as_json_block() for w in weights_used],
    )

    for point_record, weight in zip(record["calibration_points"], weights_used):
        point_record["dead_weight_record"] = weight.as_json_block()

    return record
