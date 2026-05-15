"""
Layer B — log-log OLS fit for F = a * raw^b.

Implements Bill 0002 Part 1 (curve form) and Part 4 (acceptance criteria).
Pure numpy; no I/O. Acceptance criteria are parametrized by full-scale N so
both A301-1 (FS = 4.4 N) and A301-25 (FS = 110 N) channels use the same code.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class FitResult:
    a: float
    b: float
    rms_residual_N: float
    max_residual_N: float
    adj_r_squared_loglog: float
    n_points: int


@dataclass(frozen=True)
class Acceptance:
    passed: bool
    rms_residual_N: float
    rms_criterion_N: float
    max_residual_N: float
    max_criterion_N: float
    adj_r_squared_loglog: float
    r_squared_criterion: float
    failures: tuple[str, ...]


def fit_power_law(points: list[tuple[float, float]]) -> FitResult:
    """
    Fit F = a * raw^b in log-log space by ordinary least squares.

    Args:
        points: list of (raw_mean, applied_N) pairs. Both must be > 0
            because log(0) is undefined.

    Returns:
        FitResult with fitted (a, b), residual statistics in N, and
        log-log adjusted R-squared.

    Raises:
        ValueError on < 3 points or any non-positive value.
    """
    if len(points) < 3:
        raise ValueError(f"Need >=3 points for power-law fit; got {len(points)}")
    raws = np.array([p[0] for p in points], dtype=float)
    Fs = np.array([p[1] for p in points], dtype=float)
    if np.any(raws <= 0) or np.any(Fs <= 0):
        raise ValueError("All raw and F values must be > 0 for log-log fit")

    log_raws = np.log(raws)
    log_Fs = np.log(Fs)
    b, log_a = np.polyfit(log_raws, log_Fs, 1)
    a = math.exp(log_a)

    F_fit = a * raws ** b
    residuals_N = F_fit - Fs
    rms_N = float(np.sqrt(np.mean(residuals_N ** 2)))
    max_N = float(np.max(np.abs(residuals_N)))

    log_F_fit = np.log(F_fit)
    ss_res = float(np.sum((log_Fs - log_F_fit) ** 2))
    ss_tot = float(np.sum((log_Fs - np.mean(log_Fs)) ** 2))
    n = len(points)
    p = 2
    if ss_tot == 0:
        adj_r_squared = 1.0
    else:
        r_squared = 1.0 - ss_res / ss_tot
        adj_r_squared = 1.0 - (1.0 - r_squared) * (n - 1) / (n - p)

    return FitResult(
        a=float(a),
        b=float(b),
        rms_residual_N=rms_N,
        max_residual_N=max_N,
        adj_r_squared_loglog=float(adj_r_squared),
        n_points=n,
    )


def check_acceptance(fit: FitResult, full_scale_N: float) -> Acceptance:
    """
    Bill 0002 Part 4 acceptance: RMS <= 2% FS, max <= 4% FS, log-log adj-R^2 >= 0.998.
    """
    rms_criterion = 0.02 * full_scale_N
    max_criterion = 0.04 * full_scale_N
    r_squared_criterion = 0.998

    failures: list[str] = []
    if fit.rms_residual_N > rms_criterion:
        failures.append(
            f"RMS {fit.rms_residual_N:.4f} N > criterion {rms_criterion:.4f} N"
        )
    if fit.max_residual_N > max_criterion:
        failures.append(
            f"max |residual| {fit.max_residual_N:.4f} N > criterion {max_criterion:.4f} N"
        )
    if fit.adj_r_squared_loglog < r_squared_criterion:
        failures.append(
            f"adj-R^2 {fit.adj_r_squared_loglog:.5f} < criterion {r_squared_criterion}"
        )

    return Acceptance(
        passed=len(failures) == 0,
        rms_residual_N=fit.rms_residual_N,
        rms_criterion_N=rms_criterion,
        max_residual_N=fit.max_residual_N,
        max_criterion_N=max_criterion,
        adj_r_squared_loglog=fit.adj_r_squared_loglog,
        r_squared_criterion=r_squared_criterion,
        failures=tuple(failures),
    )
