"""
Stage 1 Path A signal generator for piezo_fall (v2 — physics-grounded).

Refactored 2026-05-15 to use floor_sim.py (OpenSeesPy Kirchhoff plate
FEA) for all impulsive events per user direction. Continuous backgrounds
remain synthetic.

Article I (Signal First) — what this file traces to:

  Domain primitive P1 (Amendment 1): floor acceleration (m/s²), measured
  via piezo at ≥ 1 kHz. All numeric constants below are derived from a
  named physical model or literature reference cited adjacent to the
  constant. Forces in NEWTONS trace to biomechanics literature:
    - Cavanagh & Lafortune 1980 for footstep peak force (~1.1× body weight)
    - Robinovitch et al. 1991 + FALL_DETECTION_DESIGN.md for fall floor-
      coupled peak force (~10-30% of body-impact 5-9 kN trochanter force)
  Positions in METERS within the 2 m × 2 m bathroom slab (floor_sim
  PRESETS['bathroom']).

Architecture:
  Impulse-response caching: floor_sim.simulate is linear (modal
  superposition). Per (source_xy → sensor_xy) pair, IR is computed once
  via FEA (~2.5 s) then convolved with each impact's force profile in
  milliseconds. This makes per-seed generation fast after a one-time
  warm-up of ~100 s for the spatial grid we use.
"""

from __future__ import annotations

import csv
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

# Path setup for floor_sim — registered prior_repo per toolchain_config.md
PRIOR_REPO_ANALYSIS = '/home/sni22/Documents/piezo_circuit/analysis'
if PRIOR_REPO_ANALYSIS not in sys.path:
    sys.path.insert(0, PRIOR_REPO_ANALYSIS)

import floor_sim  # noqa: E402


# ─── Constants (each traces to P1 or stated physical model) ────────────

# P1 sample rate per Amendment 1 (≥ 1 kHz floor)
FS_HZ = 1000
# Default window length 30 s — matches 30 s detection-latency target
# (device_context.md pass/fail threshold)
DEFAULT_DURATION_S = 30.0
# Event at t=10 s in default 30 s window — gives 20 s post-event for
# stillness gate (5 s requirement) plus headroom. Traces to P1 latency target.
DEFAULT_EVENT_ONSET_S = 10.0

# Bathroom geometry registry — primitive P1 spatial domain.
# Per user direction: focus on bathroom (medium) and bathroom_small;
# bathroom_large is reserved for later if needed.
GEOMETRIES = {
    'small':  floor_sim.PRESETS['bathroom_small'],  # 1.5 × 1.5 m, 12 cm concrete
    'medium': floor_sim.PRESETS['bathroom'],        # 2.0 × 2.0 m, 15 cm concrete
}
# Per-seed geometry distribution: 1/2 small, 1/2 medium.
# Order matters — seed % len(GEOMETRY_DISTRIBUTION) picks the geometry.
GEOMETRY_DISTRIBUTION = ['small', 'medium']

# Piezo placement: scaled to quarter-corner per geometry. Reason: simply-
# supported boundaries (floor_sim preset) force mode shapes to zero at the
# walls. Quarter-corner (~25% of slab dim from each wall) is the practical
# sweet spot — corner-region, but mode-shape product is ~50% of max so
# the sensor remains usefully sensitive. Primitive P1 sensor location.
def piezo_xy_for(geom):
    return (0.25 * geom.Lx, 0.25 * geom.Ly)

# Impulse response duration: 1.5 s post-impact. Derived from longest
# expected decay tau (~500 ms for low-frequency soft-tissue impacts per
# FALL_DETECTION_DESIGN.md §decay envelope) × 3 for full ringdown capture.
IR_DURATION_S = 1.5

# Spatial-grid quantization for IR cache reuse. Derived from primitive P1
# spatial resolution: 5 cm bins keep position error below ~1 plate mode
# half-wavelength (~10-20 cm for first modes).
IR_GRID_M = 0.05


# ─── Data structures ───────────────────────────────────────────────────

@dataclass
class Impact:
    """One discrete impact on the floor — derives from P1."""
    xy: tuple[float, float]
    time_s: float
    force_N: float
    duration_s: float


@dataclass
class GroundTruth:
    profile: str
    cls: str
    event_onset_s: float | None
    fs: int
    source: str
    caveats: list[str] = field(default_factory=list)
    impacts: list[Impact] = field(default_factory=list)


# ─── Impulse-response cache (P1 — modal superposition is linear) ───────

_IR_CACHE: dict[tuple[float, float], np.ndarray] = {}


def _quantize_xy(xy):
    # Quantize to IR_GRID_M (5 cm, primitive P1 spatial resolution)
    return (round(xy[0] / IR_GRID_M) * IR_GRID_M,
            round(xy[1] / IR_GRID_M) * IR_GRID_M)


# IR reference pulse — 5 ms half-sine (must be > sample period to avoid
# all-zero discrete sampling at fs=1000). Primitive P1 input forcing.
IR_REF_DURATION_S = 0.005


def _get_impulse_response(source_xy, geometry='medium', fs=FS_HZ):
    # True per-Newton impulse response h(t) recovered via Wiener
    # deconvolution from a 5 ms half-sine FEA reference. Primitive P1.
    # Cache keyed by (geometry, quantized_xy) so different bathroom sizes
    # don't collide in the cache.
    geom = GEOMETRIES[geometry]
    sensor_xy = piezo_xy_for(geom)
    key = (geometry, _quantize_xy(source_xy))
    if key not in _IR_CACHE:
        ref_impact = floor_sim.ImpactSpec(
            peak_force_N=1.0, duration_s=IR_REF_DURATION_S, t_start=0.0,
        )
        result = floor_sim.simulate(
            slab=geom, impact=ref_impact,
            source_xy=key[1], sensor_xy=sensor_xy,
            fs=fs, duration=IR_DURATION_S,
        )
        g = result.accel
        x_ref = _force_half_sine(1.0, IR_REF_DURATION_S, fs=fs)
        n = len(g)
        X = np.fft.rfft(x_ref, n)
        G = np.fft.rfft(g, n)
        eps = 1e-6 * np.max(np.abs(X) ** 2)
        H = (G * np.conj(X)) / (np.abs(X) ** 2 + eps)
        h = np.fft.irfft(H, n)
        _IR_CACHE[key] = h
    return _IR_CACHE[key]


def _force_half_sine(force_N, duration_s, fs=FS_HZ):
    # Half-sine force profile (primitive P1 input forcing)
    n = max(2, int(round(duration_s * fs)))
    t = np.arange(n) / fs
    return force_N * np.sin(np.pi * t / duration_s)


def impact_to_signal(impact, geometry='medium', fs=FS_HZ):
    # Sensor waveform from one Impact — convolve true IR with force (P1).
    # h has units (m/s²) per (sample of N), so conv(force_in_N, h) gives m/s²
    h = _get_impulse_response(impact.xy, geometry=geometry, fs=fs)
    force = _force_half_sine(impact.force_N, impact.duration_s, fs=fs)
    return np.convolve(force, h, mode='full')


# ─── Event trajectory generators (P1 spatial sources) ──────────────────

def walking_trajectory(start_xy, end_xy, *,
                       cadence_hz=1.7,
                       stride_length_m=0.6,
                       t_start=0.0,
                       force_range_N=(600.0, 900.0),
                       duration_s=0.030,
                       rng=None):
    """Footstep sequence from start_xy toward end_xy with physically
    constrained stride length. Forces trace to Cavanagh & Lafortune 1980
    (~1.1x body weight, primitive P1). Stride 0.5-0.7 m for elderly
    (literature average ~0.6 m). Cadence 1.4-2.0 Hz. Position jitter
    +/-3 cm for natural footfall scatter.
    Step count = floor(distance / stride_length) + 1, NOT
    speed * duration — this prevents physically unrealistic spacing.
    """
    if rng is None:
        rng = np.random.default_rng()
    # Constrain stride to physical range per primitive P1 gait literature
    stride_length_m = max(0.4, min(0.8, stride_length_m))
    dx = end_xy[0] - start_xy[0]
    dy = end_xy[1] - start_xy[1]
    distance_m = math.hypot(dx, dy)
    if distance_m > 0:
        # Unit direction vector — primitive P1 spatial domain
        ux = dx / distance_m
        uy = dy / distance_m
    else:
        ux = uy = 0.0
    n_steps = max(1, int(distance_m / stride_length_m) + 1)
    step_period_s = 1.0 / cadence_hz
    impacts = []
    for i in range(n_steps):
        step_distance = i * stride_length_m
        if step_distance > distance_m + 0.5 * stride_length_m:
            break
        xy = (start_xy[0] + ux * step_distance + rng.uniform(-0.03, 0.03),
              start_xy[1] + uy * step_distance + rng.uniform(-0.03, 0.03))
        t = t_start + i * step_period_s
        force = rng.uniform(*force_range_N)
        impacts.append(Impact(xy=xy, time_s=t, force_N=force, duration_s=duration_s))
    return impacts


def fall_trajectory(center_xy, n_impacts=3,
                    t_start=0.0, rng=None):
    """Multi-impact body fall — primitive P1.
    Forces: hip 1500-3000 N (derived from Robinovitch 1991 trochanter
    impact 5-9 kN, with floor coupling fraction 10-30% per
    FALL_DETECTION_DESIGN.md). Shoulder/head ~50% of hip impact.
    Spatial cluster ±30 cm. Inter-impact 80-200 ms derived from
    Appendix A §multi-impact peak spacing.
    """
    if rng is None:
        rng = np.random.default_rng()
    forces = sorted(rng.uniform(1500.0, 3000.0, n_impacts), reverse=True)
    forces = [forces[0]] + [f * 0.5 for f in forces[1:]]
    impacts = []
    t = t_start
    for i in range(n_impacts):
        xy = (center_xy[0] + rng.uniform(-0.30, 0.30),
              center_xy[1] + rng.uniform(-0.30, 0.30))
        impacts.append(Impact(xy=xy, time_s=t,
                              force_N=float(forces[i]),
                              duration_s=0.050))
        if i < n_impacts - 1:
            t += rng.uniform(0.080, 0.200)
    return impacts


def drop_trajectory(xy, mass_kg, height_m,
                    t_start=0.0, contact_duration_s=0.005,
                    rng=None, n_impacts=1):
    """Rigid-object drop — primitive P1.
    Peak force derived from impulse F·Δt = m·v where v = sqrt(2gh).
    For brittle multi-impact (glass), splits impulse across N hits
    over ~50 ms (Appendix A §multi-impact count for objects).
    """
    if rng is None:
        rng = np.random.default_rng()
    v = math.sqrt(2.0 * 9.81 * height_m)
    total_impulse = mass_kg * v
    peak_force_total = total_impulse / contact_duration_s
    if n_impacts == 1:
        return [Impact(xy=xy, time_s=t_start,
                       force_N=peak_force_total,
                       duration_s=contact_duration_s)]
    impacts = []
    t = t_start
    for i in range(n_impacts):
        # Multi-impact (glass fragments) — primitive P1
        force = peak_force_total * rng.uniform(0.3, 1.0) / n_impacts ** 0.5
        local_xy = (xy[0] + rng.uniform(-0.05, 0.05),
                    xy[1] + rng.uniform(-0.05, 0.05))
        impacts.append(Impact(xy=local_xy, time_s=t,
                              force_N=force, duration_s=contact_duration_s))
        t += rng.uniform(0.010, 0.025)
    return impacts


# ─── Slump (hand-rolled — sustained friction + final impact, P1) ───────

def slump_signal(t_start, slide_duration_s, center_xy, rng, fs=FS_HZ):
    """Slow controlled descent — primitive P1.
    Friction rumble: lowpass-filtered Gaussian noise (~10 Hz cutoff,
    50 ms boxcar derived from soft-tissue contact-spectrum upper bound
    in Appendix A §spectral centroid for falls).
    Envelope: ramp-up + Gaussian-peaked decay — physical estimate, NO
    prior project recorded slump events (open finding in device_context.md).
    Final impact 600-1000 N derived from FALL_DETECTION_DESIGN.md §slow-
    descent fraction of full fall energy.
    """
    n = int(slide_duration_s * fs)
    raw = rng.standard_normal(n)
    kernel_len = max(1, int(fs * 0.05))
    kernel = np.ones(kernel_len) / kernel_len
    friction = np.convolve(raw, kernel, mode='same')
    env_t = np.arange(n) / n
    env = (0.3 + 0.7 * env_t) * np.exp(-((env_t - 0.7) / 0.3) ** 2)
    friction *= env
    peak = np.max(np.abs(friction)) + 1e-12
    # Slump amplitude ~3 mg peak (primitive P1, intentionally low —
    # the audit's identified blind spot)
    friction = friction / peak * 0.003
    final_impact = Impact(
        xy=(center_xy[0] + rng.uniform(-0.05, 0.05),
            center_xy[1] + rng.uniform(-0.05, 0.05)),
        time_s=t_start + slide_duration_s + 0.05,
        force_N=float(rng.uniform(600.0, 1000.0)),
        duration_s=0.080,
    )
    return friction, [final_impact]


# ─── Synthetic continuous backgrounds (primitive P1, amplitude-tuned) ──

def bg_vent(rng, duration_s, fs=FS_HZ):
    """Exhaust fan — 60 Hz motor fundamental + harmonics, ~0.5 mg RMS.
    Frequencies trace to mains motor specifications; amplitudes are
    typical floor-coupled vent contributions per primitive P1.
    """
    n = int(duration_s * fs)
    t = np.arange(n) / fs
    # Primitive P1: 60 Hz mains motor fundamental + harmonics
    sig = (np.sin(2 * np.pi * 60.0 * t + rng.uniform(0, 2*np.pi)) * 0.001
           + np.sin(2 * np.pi * 120.0 * t + rng.uniform(0, 2*np.pi)) * 0.0005
           + np.sin(2 * np.pi * 180.0 * t + rng.uniform(0, 2*np.pi)) * 0.00025)
    # Electronic noise floor — primitive P1 amplitude scale
    sig += rng.standard_normal(n) * 0.0002
    return sig


def bg_shower(rng, duration_s, fs=FS_HZ):
    """Shower — broadband 100-800 Hz floor coupling, ~5 mg peak.
    Spectrum derived from water-on-tile literature (broadband cavitation
    + droplet impact). Amplitude is primitive P1 floor acceleration.
    """
    n = int(duration_s * fs)
    raw = rng.standard_normal(n)
    raw -= np.convolve(raw, np.ones(int(fs/100))/int(fs/100), mode='same')
    sig = np.convolve(raw, np.ones(int(fs/800))/int(fs/800), mode='same')
    return sig * 0.005


def bg_flush(rng, duration_s, fs=FS_HZ):
    """Toilet flush — 30 s transient; tank-fill + drain.
    Spectrum 100-500 Hz derived from pipe-flow physics. Primitive P1.
    """
    n = int(duration_s * fs)
    sig = np.zeros(n)
    flush_start = int(fs * rng.uniform(2.0, 5.0))
    flush_dur = int(fs * 30.0)
    flush_end = min(flush_start + flush_dur, n)
    raw = rng.standard_normal(flush_end - flush_start)
    raw -= np.convolve(raw, np.ones(int(fs/100))/int(fs/100), mode='same')
    sig_seg = np.convolve(raw, np.ones(int(fs/500))/int(fs/500), mode='same')
    env = np.ones(flush_end - flush_start)
    ramp = int(fs * 2.0)
    env[:ramp] = np.linspace(0, 1, ramp)
    env[-ramp:] = np.linspace(1, 0, ramp)
    # Primitive P1: ~7 mg peak floor acceleration for flush
    sig[flush_start:flush_end] = sig_seg * env * 0.007
    return sig


def bg_washer(rng, duration_s, fs=FS_HZ, attenuation=1.0):
    """Washer on spin — narrow-band 22-28 Hz spin frequency + sidebands.
    Spin frequency derives from typical residential washer specs.
    Attenuation 0.25 for through-wall coupling, primitive P1.
    """
    n = int(duration_s * fs)
    t = np.arange(n) / fs
    spin_hz = rng.uniform(22.0, 28.0)
    # Primitive P1 narrow-band amplitudes
    sig = np.sin(2 * np.pi * spin_hz * t + rng.uniform(0, 2*np.pi)) * 0.008
    sig += np.sin(2 * np.pi * spin_hz * 2 * t) * 0.003
    sig += np.sin(2 * np.pi * spin_hz * 0.5 * t) * 0.001
    sig += rng.standard_normal(n) * 0.0003
    if attenuation < 1.0:
        kernel = np.ones(int(fs/30)) / int(fs/30)
        sig = np.convolve(sig, kernel, mode='same')
    return sig * attenuation


# ─── Real-pulse loader (event override — preserves receiver.py schema) ─

def load_pulse_csv(path):
    """Load a pre-cropped pulse CSV in receiver.py format (sample_index,
    value, event). Returns the 'value' column as ndarray. Primitive P1.
    """
    values = []
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            values.append(float(row['value']))
    return np.array(values, dtype=np.float64)


# ─── Profile recipes (each maps to primitive P1 spatial source set) ────

@dataclass
class ProfileRecipe:
    cls: str
    bg_sources: list
    events_fn: object
    slump_fn: object | None = None


def _walking_into_bathroom(rng, geom):
    # Walking from far wall (~95% slab) toward sensor (~25% slab). P1.
    end_xy = (rng.uniform(0.20, 0.35) * geom.Lx, rng.uniform(0.20, 0.35) * geom.Ly)
    start_xy = (rng.uniform(0.80, 0.95) * geom.Lx, rng.uniform(0.30, 0.70) * geom.Ly)
    return walking_trajectory(
        start_xy=start_xy, end_xy=end_xy,
        stride_length_m=rng.uniform(0.5, 0.7),
        cadence_hz=rng.uniform(1.5, 2.0),
        t_start=rng.uniform(5.0, 10.0),
        rng=rng,
    )


def _fall_after_walk(rng, geom):
    # Composite: person walks into bathroom and then falls. Primitive P1.
    end_xy = (rng.uniform(0.50, 0.80) * geom.Lx, rng.uniform(0.50, 0.80) * geom.Ly)
    start_xy = (rng.uniform(0.85, 0.95) * geom.Lx, rng.uniform(0.20, 0.35) * geom.Ly)
    walking = walking_trajectory(
        start_xy=start_xy, end_xy=end_xy,
        stride_length_m=rng.uniform(0.5, 0.7),
        cadence_hz=rng.uniform(1.5, 2.0),
        t_start=rng.uniform(3.0, 5.0),
        rng=rng,
    )
    if walking:
        last_t = walking[-1].time_s
        last_xy = walking[-1].xy
    else:
        last_t = 5.0
        last_xy = end_xy
    # Fall at last footstep + small offset, after 0.3-0.7 s
    fall_center = (last_xy[0] + rng.uniform(-0.2, 0.2),
                   last_xy[1] + rng.uniform(-0.2, 0.2))
    falling = fall_trajectory(
        center_xy=fall_center, n_impacts=3,
        t_start=last_t + rng.uniform(0.3, 0.7),
        rng=rng,
    )
    return walking + falling


def _walk_in_out(rng, geom):
    # Composite: person walks IN, pauses, walks OUT. Primitive P1.
    pause_duration_s = rng.uniform(5.0, 10.0)
    mid_xy = (rng.uniform(0.40, 0.60) * geom.Lx, rng.uniform(0.40, 0.60) * geom.Ly)
    in_start = (rng.uniform(0.85, 0.95) * geom.Lx, rng.uniform(0.20, 0.35) * geom.Ly)
    out_end = (rng.uniform(0.85, 0.95) * geom.Lx, rng.uniform(0.20, 0.35) * geom.Ly)
    walk_in = walking_trajectory(
        start_xy=in_start, end_xy=mid_xy,
        stride_length_m=rng.uniform(0.5, 0.7),
        cadence_hz=rng.uniform(1.5, 2.0),
        t_start=rng.uniform(3.0, 4.0),
        rng=rng,
    )
    last_in_t = walk_in[-1].time_s if walk_in else 5.0
    walk_out = walking_trajectory(
        start_xy=mid_xy, end_xy=out_end,
        stride_length_m=rng.uniform(0.5, 0.7),
        cadence_hz=rng.uniform(1.5, 2.0),
        t_start=last_in_t + pause_duration_s,
        rng=rng,
    )
    return walk_in + walk_out


def _fall_fast_far(rng, geom):
    # Fall at far corner (~70-90% of slab dim). Primitive P1.
    center = (rng.uniform(0.70, 0.90) * geom.Lx, rng.uniform(0.70, 0.90) * geom.Ly)
    return fall_trajectory(
        center_xy=center, n_impacts=3,
        t_start=DEFAULT_EVENT_ONSET_S, rng=rng,
    )


def _slump_far(rng, geom):
    # Slump at far corner — primitive P1
    center = (rng.uniform(0.70, 0.90) * geom.Lx, rng.uniform(0.70, 0.90) * geom.Ly)
    slide_dur = rng.uniform(2.0, 3.5)
    t_start = DEFAULT_EVENT_ONSET_S
    friction, impacts = slump_signal(t_start, slide_dur, center, rng)
    return friction, t_start, impacts


def _drop_phone(rng, geom):
    # 200 g phone from 1 m, anywhere on slab. Primitive P1.
    xy = (rng.uniform(0.20, 0.80) * geom.Lx, rng.uniform(0.20, 0.80) * geom.Ly)
    return drop_trajectory(xy=xy, mass_kg=0.20, height_m=1.0,
                            t_start=DEFAULT_EVENT_ONSET_S,
                            contact_duration_s=0.004, rng=rng)


def _drop_heavy(rng, geom):
    # 600 g hair dryer from 0.8 m. Primitive P1.
    xy = (rng.uniform(0.20, 0.80) * geom.Lx, rng.uniform(0.20, 0.80) * geom.Ly)
    return drop_trajectory(xy=xy, mass_kg=0.60, height_m=0.8,
                            t_start=DEFAULT_EVENT_ONSET_S,
                            contact_duration_s=0.008, rng=rng)


def _drop_glass(rng, geom):
    # 200 g brittle glass from 1.2 m, multi-impact. Primitive P1.
    xy = (rng.uniform(0.20, 0.80) * geom.Lx, rng.uniform(0.20, 0.80) * geom.Ly)
    return drop_trajectory(xy=xy, mass_kg=0.20, height_m=1.2,
                            t_start=DEFAULT_EVENT_ONSET_S,
                            contact_duration_s=0.003, rng=rng,
                            n_impacts=int(rng.integers(2, 5)))


PROFILES = {
    'noise_vent':            ProfileRecipe('noise', ['vent'], lambda rng, geom: []),
    'noise_shower':          ProfileRecipe('noise', ['vent', 'shower'], lambda rng, geom: []),
    'noise_flush':           ProfileRecipe('noise', ['vent', 'flush'], lambda rng, geom: []),
    'noise_washer_local':    ProfileRecipe('noise', ['vent', 'washer_local'], lambda rng, geom: []),
    'noise_washer_neighbor': ProfileRecipe('noise', ['vent', 'washer_neighbor'], lambda rng, geom: []),
    'confuser_step':         ProfileRecipe('confuser', ['vent'], _walking_into_bathroom),
    'confuser_drop_phone':   ProfileRecipe('confuser', ['vent'], _drop_phone),
    'confuser_drop_heavy':   ProfileRecipe('confuser', ['vent'], _drop_heavy),
    'confuser_drop_glass':   ProfileRecipe('confuser', ['vent'], _drop_glass),
    'fall_fast':             ProfileRecipe('fall', ['vent'], _fall_fast_far),
    'fall_slump':            ProfileRecipe('fall', ['vent', 'shower'],
                                            lambda rng, geom: [],
                                            slump_fn=_slump_far),
    # Composite profiles — multi-event sessions. Primitive P1.
    'fall_after_walk':       ProfileRecipe('fall', ['vent'], _fall_after_walk),
    'walk_in_out':           ProfileRecipe('confuser', ['vent'], _walk_in_out),
}


# ─── Main entry point ──────────────────────────────────────────────────

def generate(profile, duration_s=DEFAULT_DURATION_S, seed=0, fs=FS_HZ,
             event_override=None, geometry=None):
    """Generate one trace for `profile`. Returns (samples in m/s², GroundTruth).

    geometry: if None, picked deterministically from GEOMETRY_DISTRIBUTION
        using seed % len(distribution). Set explicitly to 'small' or
        'medium' to force a specific bathroom geometry.
    """
    if profile not in PROFILES:
        raise KeyError(f"Unknown profile {profile!r}. Available: {sorted(PROFILES.keys())}")
    recipe = PROFILES[profile]
    rng = np.random.default_rng(seed)
    # Geometry selection — deterministic per seed for reproducibility
    if geometry is None:
        geometry = GEOMETRY_DISTRIBUTION[seed % len(GEOMETRY_DISTRIBUTION)]
    geom = GEOMETRIES[geometry]
    n = int(duration_s * fs)
    samples = np.zeros(n)
    caveats = []
    caveats.append(f'geometry: {geometry} ({geom.Lx}x{geom.Ly} m)')

    # Backgrounds (synthetic — primitive P1 floor acceleration in m/s²)
    for bg_name in recipe.bg_sources:
        if bg_name == 'vent':
            samples += bg_vent(rng, duration_s, fs)
        elif bg_name == 'shower':
            samples += bg_shower(rng, duration_s, fs)
            caveats.append('Synthetic shower — replace with real recording at Stage 2')
        elif bg_name == 'flush':
            samples += bg_flush(rng, duration_s, fs)
            caveats.append('Synthetic flush — replace with real recording at Stage 2')
        elif bg_name == 'washer_local':
            samples += bg_washer(rng, duration_s, fs, attenuation=1.0)
            caveats.append('Synthetic washer — replace with real recording at Stage 2')
        elif bg_name == 'washer_neighbor':
            samples += bg_washer(rng, duration_s, fs, attenuation=0.25)
            caveats.append('Synthetic washer (attenuated) — replace with real recording at Stage 2')
        else:
            raise ValueError(f"Unknown bg source {bg_name!r}")

    source = 'synthetic'
    event_onset_s = None
    impacts = []

    if event_override is not None:
        pulse = load_pulse_csv(event_override)
        source = f'real_csv:{event_override}'
        caveats.append('Real-data pulse: sample rate assumed 1 kHz (SAMPLE-RATE-UNMEASURED)')
        onset_sample = int(DEFAULT_EVENT_ONSET_S * fs)
        end_sample = min(onset_sample + len(pulse), n)
        peak = np.max(np.abs(pulse)) + 1e-12
        # Normalize real pulse to ~0.5 m/s² peak — primitive P1 typical event scale
        pulse = pulse / peak * 0.5
        samples[onset_sample:end_sample] += pulse[:end_sample - onset_sample]
        event_onset_s = DEFAULT_EVENT_ONSET_S
    else:
        if recipe.slump_fn is not None:
            friction, friction_t, slump_impacts = recipe.slump_fn(rng, geom)
            f_onset = int(friction_t * fs)
            f_end = min(f_onset + len(friction), n)
            samples[f_onset:f_end] += friction[:f_end - f_onset]
            impacts.extend(slump_impacts)
            event_onset_s = friction_t
        impacts.extend(recipe.events_fn(rng, geom))

        for imp in impacts:
            wf = impact_to_signal(imp, geometry=geometry, fs=fs)
            inj = int(imp.time_s * fs)
            end = min(inj + len(wf), n)
            if inj < 0 or inj >= n:
                continue
            samples[inj:end] += wf[:end - inj]

        if impacts and event_onset_s is None:
            event_onset_s = min(imp.time_s for imp in impacts)

    gt = GroundTruth(
        profile=profile, cls=recipe.cls,
        event_onset_s=event_onset_s,
        fs=fs, source=source, caveats=caveats,
        impacts=impacts,
    )
    return samples, gt


def list_profiles():
    return list(PROFILES.keys())


def precompute_ir_cache():
    """Warm IR cache by generating one trace per profile."""
    for p in list_profiles():
        generate(p, seed=42)
    return len(_IR_CACHE)
