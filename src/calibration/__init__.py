"""
FlexiForce DAQ per-channel calibration — Bill 0002.

Layer A (capture):    `CalibrationCapture` — baseline → onset → window.
Layer B (fit):        `fit_power_law` + `check_acceptance` — log-log OLS.
Layer B (json):       `build_calibration_record` + `write_calibration_json`.

Layer C (MTS control) is deferred until Case 1 Condition C1 is verified.
"""
from src.calibration.capture import CalibrationCapture, CalibrationPoint, CaptureError
from src.calibration.fit import Acceptance, FitResult, check_acceptance, fit_power_law
from src.calibration.json_writer import (
    CalibrationPointRecord,
    build_calibration_record,
    write_calibration_json,
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
]
