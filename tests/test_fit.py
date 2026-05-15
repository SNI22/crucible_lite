"""Synthetic-data tests for src.calibration.fit (Bill 0002 Parts 1 + 4)."""
from __future__ import annotations

import math

import numpy as np
import pytest

from src.calibration.fit import FitResult, check_acceptance, fit_power_law


def synthesize_points(
    a: float, b: float, raws: list[float], noise_std: float = 0.0, rng_seed: int = 42
) -> list[tuple[float, float]]:
    """(raw, F) pairs from a power law with optional Gaussian noise added in F."""
    rng = np.random.default_rng(rng_seed)
    return [
        (float(r), float(a * r ** b + rng.normal(0.0, noise_std))) for r in raws
    ]


def test_fit_recovers_clean_power_law():
    a_true, b_true = 1e-4, 1.5
    raws = [100, 200, 400, 800, 1600, 3200]
    points = synthesize_points(a_true, b_true, raws, noise_std=0.0)
    fit = fit_power_law(points)
    assert math.isclose(fit.a, a_true, rel_tol=1e-6)
    assert math.isclose(fit.b, b_true, rel_tol=1e-6)
    assert fit.rms_residual_N < 1e-8
    assert fit.adj_r_squared_loglog > 0.9999


def test_fit_with_small_noise_passes_a301_1_acceptance():
    """A301-1 FS = 4.4 N. Noise std 0.02 N is well below the 0.088 N RMS criterion."""
    # F = 0.0025 * raw — linear, spans 0.5–6.25 N across the chosen raws.
    a_true, b_true = 0.0025, 1.0
    raws = [200, 400, 800, 1200, 1600, 2000, 2500]
    points = synthesize_points(a_true, b_true, raws, noise_std=0.02, rng_seed=42)
    fit = fit_power_law(points)
    acc = check_acceptance(fit, full_scale_N=4.4)
    assert acc.passed, f"Failures: {acc.failures}"


def test_fit_with_large_noise_fails_acceptance():
    """Noise std 0.15 N gives RMS residual > 0.088 N (A301-1 criterion)."""
    a_true, b_true = 0.0025, 1.0
    raws = [200, 400, 800, 1200, 1600, 2000, 2500]
    points = synthesize_points(a_true, b_true, raws, noise_std=0.15, rng_seed=42)
    fit = fit_power_law(points)
    acc = check_acceptance(fit, full_scale_N=4.4)
    assert not acc.passed


def test_fit_requires_three_points():
    with pytest.raises(ValueError, match=">=3 points"):
        fit_power_law([(100, 0.5), (200, 1.0)])


def test_fit_rejects_non_positive():
    with pytest.raises(ValueError, match="must be > 0"):
        fit_power_law([(100, 0.5), (200, 1.0), (0, 1.5)])
    with pytest.raises(ValueError, match="must be > 0"):
        fit_power_law([(100, 0.5), (200, -1.0), (300, 1.5)])


def test_acceptance_criteria_a301_1():
    """Bill 0002 Part 4: RMS <= 0.088 N (2% FS), max <= 0.176 N (4% FS), adj-R^2 >= 0.998."""
    fit = FitResult(
        a=1.0,
        b=1.0,
        rms_residual_N=0.087,
        max_residual_N=0.175,
        adj_r_squared_loglog=0.999,
        n_points=8,
    )
    acc = check_acceptance(fit, full_scale_N=4.4)
    assert acc.passed
    assert math.isclose(acc.rms_criterion_N, 0.088)
    assert math.isclose(acc.max_criterion_N, 0.176)


def test_acceptance_criteria_a301_25():
    """Bill 0002 Part 4: A301-25 FS = 110 N → RMS <= 2.2, max <= 4.4."""
    fit = FitResult(
        a=1.0,
        b=1.0,
        rms_residual_N=2.1,
        max_residual_N=4.3,
        adj_r_squared_loglog=0.999,
        n_points=8,
    )
    acc = check_acceptance(fit, full_scale_N=110.0)
    assert acc.passed
    assert math.isclose(acc.rms_criterion_N, 2.2)
    assert math.isclose(acc.max_criterion_N, 4.4)


def test_acceptance_reports_each_failure_separately():
    fit = FitResult(
        a=1.0,
        b=1.0,
        rms_residual_N=0.5,         # fails RMS criterion 0.088
        max_residual_N=1.0,         # fails max criterion 0.176
        adj_r_squared_loglog=0.95,  # fails R^2 criterion 0.998
        n_points=8,
    )
    acc = check_acceptance(fit, full_scale_N=4.4)
    assert not acc.passed
    assert len(acc.failures) == 3
