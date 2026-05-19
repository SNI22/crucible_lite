"""
FlexiForce DAQ per-channel calibration — Bill 0002, extended by Bill 0003.

Layer A (capture):       `CalibrationCapture` — baseline → onset → window.
Layer B (fit):           `fit_power_law` + `check_acceptance` — log-log OLS.
Layer B (json):          `build_calibration_record` + `write_calibration_json`.
Layer C (MTS):           `MTSDriver` Protocol + `lower_until_force` +
                         `c1_feasibility_check` + `MockMTSDriver`.
                         Hardware driver implementation is the lab's responsibility.
Layer D (dead-weight):   `DeadWeightRecord` + `deadweight_force_N` +
                         `acquire_level` + `build_deadweight_calibration_record`
                         (Bill 0003, A301-1 channels Ch0–Ch4 only).
"""
from src.calibration.capture import CalibrationCapture, CalibrationPoint, CaptureError
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
from src.calibration.fit import Acceptance, FitResult, check_acceptance, fit_power_law
from src.calibration.json_writer import (
    CalibrationPointRecord,
    build_calibration_record,
    write_calibration_json,
)
from src.calibration.mts import (
    C1LevelResult,
    C1Report,
    LowerResult,
    MockMTSDriver,
    MTSDriver,
    MTSState,
    c1_feasibility_check,
    lower_until_force,
    write_c1_report,
)

__all__ = [
    "CalibrationCapture",
    "CalibrationPoint",
    "CaptureError",
    "FitResult",
    "Acceptance",
    "fit_power_law",
    "check_acceptance",
    "CalibrationPointRecord",
    "build_calibration_record",
    "write_calibration_json",
    "MTSDriver",
    "MTSState",
    "MockMTSDriver",
    "LowerResult",
    "C1LevelResult",
    "C1Report",
    "lower_until_force",
    "c1_feasibility_check",
    "write_c1_report",
    "A301_1_CHANNELS",
    "CGPM_GRAVITY_M_PER_S2",
    "DeadWeightRecord",
    "ScopeError",
    "acquire_level",
    "build_deadweight_calibration_record",
    "check_scope",
    "deadweight_force_N",
]
