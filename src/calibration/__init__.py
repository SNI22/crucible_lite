"""
FlexiForce DAQ per-channel calibration — Bill 0002.

Layer A (capture):    `CalibrationCapture` — baseline → onset → window.
Layer B (fit):        `fit_power_law` + `check_acceptance` — log-log OLS.
Layer B (json):       `build_calibration_record` + `write_calibration_json`.
Layer C (MTS):        `MTSDriver` Protocol + `lower_until_force` +
                      `c1_feasibility_check` + `MockMTSDriver`.
                      Hardware driver implementation is the lab's responsibility.
"""
from src.calibration.capture import CalibrationCapture, CalibrationPoint, CaptureError
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
]
