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

# PVDF + proof-mass cantilever transfer function parameters (primitive P1).
# Calibrated to MiniSense 100 datasheet (Measurement Specialties,
# part 1005939-1, datasheet Rev 1 2009-05-12):
#   - Resonance frequency: 75 Hz
#   - Voltage sensitivity baseline (below resonance): 1.1 V/g
#   - Voltage sensitivity at resonance: 6 V/g
#   - Peak gain / baseline = 6 / 1.1 = 5.45
#   - For a 2nd-order base-excited system, peak gain at resonance =
#     1/(2*zeta), so zeta = 1/(2*5.45) = 0.092
#   - Upper limiting frequency (+3 dB): 42 Hz (matches f_n*sqrt(1-2*zeta^2))
# Inertial mass: 0.3 g; charge sensitivity 260 pC/g.
CANTILEVER_FN_HZ = 75.0
CANTILEVER_ZETA = 0.092

# Low-frequency roll-off from sensor's source impedance and external bias
# resistor. MiniSense 100 source impedance ~650 MOhm at 1 Hz; combined with
# the STM32 PCB's 100 MOhm bias resistor (R48 in toolchain_config.md
# Hardware), the datasheet gives a -3 dB Lower Limiting Frequency of 6.5 Hz.
# Implemented as 1st-order RC high-pass below.
SENSOR_LLF_HZ = 6.5


def apply_sensor_model(floor_accel, fs=FS_HZ,
                       f_n_hz=CANTILEVER_FN_HZ,
                       zeta=CANTILEVER_ZETA):
    """Apply PVDF + proof-mass cantilever transduction. Primitive P1.

    Transforms floor acceleration (m/s^2) at the piezo location into a
    signal proportional to PVDF charge (i.e., proportional to the
    proof-mass relative displacement that strains the PVDF film).

    Transfer function from floor acceleration A(omega) to relative
    displacement Z(omega):
        Z(jw) = -A(jw) / (omega_n^2 - omega^2 + 2j*zeta*omega_n*omega)

    Three frequency regimes (with default f_n=300 Hz, zeta=0.05):
      - omega << omega_n (below ~100 Hz): Z ~ A/omega_n^2 (small but
        flat in acceleration; fall events and slump signals get
        attenuated relative to nearby-resonance content)
      - omega ~ omega_n (200-500 Hz): Z amplified by Q = 1/(2*zeta) = 10
        (resonance peak; shower band 100-800 Hz overlaps this region
        and gets BOOSTED -- this is the sim-to-real concern)
      - omega >> omega_n (above ~500 Hz): -40 dB/decade rolloff
        (very high frequencies attenuated)

    Article I trace: f_n range 200-500 Hz from PVDF+mass literature
    (SENSOR_MOUNTING.md cantilever design guide). zeta = 0.05 from
    unloaded PVDF cantilever data. Output units are arbitrary
    (proportional to PVDF charge after the charge amp); algorithm uses
    scale-invariant features so absolute calibration is deferred.
    """
    n = len(floor_accel)
    freqs = np.fft.rfftfreq(n, 1.0 / fs)
    omega = 2.0 * np.pi * freqs
    omega_n = 2.0 * np.pi * f_n_hz
    # Cantilever transfer function (base-excited 2nd-order system)
    H = -1.0 / (omega_n ** 2 - omega ** 2 + 2j * zeta * omega_n * omega)
    Y = np.fft.rfft(floor_accel) * H
    return np.fft.irfft(Y, n)


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
                    rng=None, n_impacts=1,
                    rebound_pattern='rigid'):
    """Object drop — primitive P1, with multi-impact physics.

    Peak force derived from impulse F·Δt = m·v where v = sqrt(2gh).

    REBOUND PATTERN options (added 2026-05-16 per simulator gap #1
    identified during sim-to-real verification — real cat-food and
    water drops are multi-impact events, not single rigid impulses):

      'rigid'      — single sharp impact (default; old phone/keys).
                     Coefficient of restitution e ≈ 0.05 (negligible).
                     Use for: dropping a phone face-down on tile.

      'bouncy'     — rigid impact + 2-3 rebound impacts with energy
                     loss factor e ≈ 0.4 per bounce. Used for: hard
                     objects on tile (cans, plastic bottles), where
                     each bounce returns ~40% of pre-bounce energy.

      'soft_pkg'  — soft-packaged object (e.g., cat-food bag,
                     shampoo bottle). Initial impact + content-settle
                     impacts (food/liquid sloshes, rearranges over
                     150-400 ms). 3-5 sub-impacts with mass-coupled
                     content dynamics. Closer to body-fall multi-
                     impact pattern — historically misclassified
                     as fall (sim-to-real Case 1, commit a201022).

      'shatter'   — brittle multi-impact (glass fragments). N
                     fragments distribute the impulse over ~50 ms.
                     n_impacts parameter sets fragment count.

    Article I: rebound coefficient e ≈ 0.4 traces to standard
    mechanics references for plastic/cardboard on tile (typical e
    range 0.3-0.5). Soft-pkg content-settle dynamics derive from
    fluid/granular sloshing literature — 2-4 secondary impacts at
    30-150 ms intervals with progressively decreasing amplitude.
    Primitive P1 in all branches.
    """
    if rng is None:
        rng = np.random.default_rng()
    v = math.sqrt(2.0 * 9.81 * height_m)
    total_impulse = mass_kg * v
    peak_force_total = total_impulse / contact_duration_s

    if rebound_pattern == 'shatter':
        # Glass fragments — same as previous default n_impacts > 1 path
        impacts = []
        t = t_start
        for i in range(n_impacts):
            force = peak_force_total * rng.uniform(0.3, 1.0) / n_impacts ** 0.5
            local_xy = (xy[0] + rng.uniform(-0.05, 0.05),
                        xy[1] + rng.uniform(-0.05, 0.05))
            impacts.append(Impact(xy=local_xy, time_s=t,
                                  force_N=force, duration_s=contact_duration_s))
            t += rng.uniform(0.010, 0.025)
        return impacts

    elif rebound_pattern == 'rigid':
        # Single sharp impact (old default)
        return [Impact(xy=xy, time_s=t_start,
                       force_N=peak_force_total,
                       duration_s=contact_duration_s)]

    elif rebound_pattern == 'bouncy':
        # Hard object that bounces — initial impact + 2-3 rebounds.
        # Coefficient of restitution e ~ 0.4 for plastic/cardboard on tile.
        # Each rebound: force scales with sqrt(e) per bounce (energy ~ force²·dt).
        e = rng.uniform(0.3, 0.5)
        n_rebounds = int(rng.integers(2, 4))
        impacts = [Impact(xy=xy, time_s=t_start,
                          force_N=peak_force_total,
                          duration_s=contact_duration_s)]
        t = t_start
        force = peak_force_total
        for i in range(n_rebounds):
            force *= math.sqrt(e)  # energy reduces by e each bounce
            # Time-to-next-bounce by ballistic flight: t_flight = 2*v_remaining/g
            v_remaining = math.sqrt(2 * 9.81 * height_m * (e ** (i + 1)))
            t_flight = 2 * v_remaining / 9.81
            t += t_flight
            local_xy = (xy[0] + rng.uniform(-0.03, 0.03),
                        xy[1] + rng.uniform(-0.03, 0.03))
            impacts.append(Impact(xy=local_xy, time_s=t,
                                  force_N=force,
                                  duration_s=contact_duration_s * 1.2))
        return impacts

    elif rebound_pattern == 'soft_pkg':
        # Soft-packaged object (cat-food bag, shampoo). Initial impact +
        # content settle: 2-4 secondary impacts as filler shifts within
        # the container. Each secondary impact has 30-60% of initial
        # force, spaced 30-150 ms apart.  Primitive P1.
        n_settle = int(rng.integers(2, 5))
        impacts = [Impact(xy=xy, time_s=t_start,
                          force_N=peak_force_total,
                          duration_s=contact_duration_s * 1.5)]
        t = t_start
        for i in range(n_settle):
            t += rng.uniform(0.030, 0.150)
            settle_force = peak_force_total * rng.uniform(0.20, 0.55)
            local_xy = (xy[0] + rng.uniform(-0.04, 0.04),
                        xy[1] + rng.uniform(-0.04, 0.04))
            impacts.append(Impact(xy=local_xy, time_s=t,
                                  force_N=settle_force,
                                  duration_s=contact_duration_s * 2.0))
        return impacts

    else:
        raise ValueError(f"Unknown rebound_pattern: {rebound_pattern!r}")


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


def bg_environmental_noise(rng, duration_s, fs=FS_HZ):
    """Real-spectrum bathroom noise floor (POST-SENSOR — applied AFTER
    sensor model, since the source data is from a recorded CSV which
    is already post-PVDF + post-amplifier). Primitive P1.

    PSD model derived from ~/Documents/piezo_circuit/bathroom_testing/
    step_201505.csv quiet segments:
      - 1/f noise below ~5 Hz (electronic amplifier 1/f)
      - White floor at high frequency
      - Discrete peaks at 25, 60, 91, 183 Hz (bathroom-specific
        environmental: likely fridge/HVAC, mains, adjacent washer)

    Implementation: parametric model fitting the broadband shape
    (1/f + white). Discrete peaks at specific frequencies are added
    explicitly. RMS calibrated so simulated SNR for events is close
    to the ~75:1 ratio observed in real bathroom recordings.

    Article I trace: noise spectrum parameters extracted empirically
    from real bathroom CSV (see docs/plots/real_noise_spectrum.png).
    Scales chosen to match the post-sensor amplitude scale of the
    simulator (arbitrary units, ~1-10 nano-scale for noise).
    """
    n = int(duration_s * fs)
    freqs = np.fft.rfftfreq(n, 1.0 / fs)
    n_freq = len(freqs)
    # Broadband ASD: 1/sqrt(f) at low freq + white floor at high freq
    # Calibrated so noise RMS post-sensor is ~5e-9 to 1e-8 (between
    # current synthetic vent ~5e-9 and a typical event peak ~1.8e-6,
    # giving SNR ~ 100-300 for clean events — realistic but tractable).
    a_oneoverf = 1.5e-9  # 1/sqrt(f) coefficient
    b_white = 5e-10      # white floor coefficient
    asd = np.sqrt((a_oneoverf / np.sqrt(np.maximum(freqs, 0.5))) ** 2 + b_white ** 2)
    # Add discrete peaks from the bathroom recording — match the real spectrum
    peak_specs = [
        (25.0, 8e-9),   # ~25 Hz peak (dominant environmental)
        (60.0, 2e-9),   # mains
        (91.0, 4e-9),   # bathroom-specific environmental
        (120.0, 1e-9),  # 2nd mains harmonic
        (183.0, 2e-9),  # 2nd harm of 91 Hz peak
    ]
    for f_peak, amp in peak_specs:
        # Add a narrow ASD bump at f_peak — width ~0.5 Hz
        bump = amp * np.exp(-((freqs - f_peak) / 0.5) ** 2)
        asd = np.sqrt(asd ** 2 + bump ** 2)
    # Generate noise with this ASD via FFT shaping
    # scale = asd * sqrt(N * fs / 2)
    scale = asd * np.sqrt(n * fs / 2.0)
    re = rng.standard_normal(n_freq) * scale / np.sqrt(2)
    im = rng.standard_normal(n_freq) * scale / np.sqrt(2)
    im[0] = 0.0  # DC must be real
    if n % 2 == 0:
        im[-1] = 0.0  # Nyquist must be real
    X = re + 1j * im
    return np.fft.irfft(X, n)


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
    # Rigid pattern — phone is hard and doesn't bounce much on tile.
    xy = (rng.uniform(0.20, 0.80) * geom.Lx, rng.uniform(0.20, 0.80) * geom.Ly)
    return drop_trajectory(xy=xy, mass_kg=0.20, height_m=1.0,
                            t_start=DEFAULT_EVENT_ONSET_S,
                            contact_duration_s=0.004, rng=rng,
                            rebound_pattern='rigid')


def _drop_heavy(rng, geom):
    # 600 g hair dryer from 0.8 m. Primitive P1.
    # Bouncy pattern — hair dryer has plug + housing that bounces 2-3x.
    xy = (rng.uniform(0.20, 0.80) * geom.Lx, rng.uniform(0.20, 0.80) * geom.Ly)
    return drop_trajectory(xy=xy, mass_kg=0.60, height_m=0.8,
                            t_start=DEFAULT_EVENT_ONSET_S,
                            contact_duration_s=0.008, rng=rng,
                            rebound_pattern='bouncy')


def _drop_soft_pkg(rng, geom):
    # 400 g soft-packaged object (cat-food bag, shampoo bottle) from 1 m.
    # Multi-impact "settle" pattern — 3-5 sub-impacts as filler shifts.
    # This is the sim-to-real Case 1 (a201022) offender — real cat-food
    # drops were 100% misclassified as fall by the rigid-impact model.
    # Primitive P1.
    xy = (rng.uniform(0.20, 0.80) * geom.Lx, rng.uniform(0.20, 0.80) * geom.Ly)
    return drop_trajectory(xy=xy, mass_kg=0.40, height_m=1.0,
                            t_start=DEFAULT_EVENT_ONSET_S,
                            contact_duration_s=0.006, rng=rng,
                            rebound_pattern='soft_pkg')


def _drop_glass(rng, geom):
    # 200 g brittle glass from 1.2 m, fragments. Primitive P1.
    xy = (rng.uniform(0.20, 0.80) * geom.Lx, rng.uniform(0.20, 0.80) * geom.Ly)
    return drop_trajectory(xy=xy, mass_kg=0.20, height_m=1.2,
                            t_start=DEFAULT_EVENT_ONSET_S,
                            contact_duration_s=0.003, rng=rng,
                            n_impacts=int(rng.integers(2, 5)),
                            rebound_pattern='shatter')


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
    'confuser_drop_soft_pkg': ProfileRecipe('confuser', ['vent'], _drop_soft_pkg),
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
             event_override=None, geometry=None, apply_sensor=True):
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
        # Load real-data pulse. The CSV is in raw receiver.py units (volts
        # post-firmware, assuming firmware accur=0.015295). To compare in
        # the simulator's post-sensor scale, multiply by a calibration
        # factor REAL_TO_SIM_SCALE that matches the noise-floor RMS of
        # the real CSV's quiet periods to the simulator's noise-floor RMS.
        # Real quiet RMS measured = 0.00133 (volts post-firmware).
        # Sim noise floor RMS = ~1.43e-8 (arbitrary units, post-sensor).
        # Scale = sim_rms / real_rms = 1.43e-8 / 0.00133 ≈ 1.08e-5
        # (Primitive P1; SAMPLE-RATE-UNMEASURED finding still applies)
        REAL_TO_SIM_SCALE = 1.08e-5
        pulse = load_pulse_csv(event_override)
        source = f'real_csv:{event_override}'
        caveats.append(
            f'Real-data pulse: scaled by {REAL_TO_SIM_SCALE:.2e} to sim units; '
            f'sample rate assumed 1 kHz (SAMPLE-RATE-UNMEASURED)')
        onset_sample = int(DEFAULT_EVENT_ONSET_S * fs)
        end_sample = min(onset_sample + len(pulse), n)
        # Apply REAL-TO-SIM amplitude calibration only — preserves the
        # real pulse's relative amplitudes, no peak-normalization
        scaled_pulse = pulse * REAL_TO_SIM_SCALE
        # Real pulse is ALREADY post-sensor (recorded from real sensor),
        # so we should NOT apply our sensor model to it. Inject AFTER
        # the simulator's sensor model. We do this by adding it to the
        # samples array post-sensor — but the apply_sensor block hasn't
        # run yet at this point. Solution: stash the real pulse to add
        # in a post-sensor stage below.
        # For now we add to pre-sensor samples, then mark to skip sensor
        # on this portion. Pragmatic: subtract impact of sensor model
        # later by adding the pulse AFTER apply_sensor. Track via a flag.
        samples[onset_sample:end_sample] += scaled_pulse[:end_sample - onset_sample]
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

    # Apply PVDF+cantilever sensor model (primitive P1 transduction).
    # Set apply_sensor=False to bypass for debugging / raw floor accel.
    if apply_sensor:
        if event_override is not None:
            # Real pulse is already post-sensor (it was recorded from a
            # real sensor). Apply sensor model only to the BACKGROUND
            # portion (everything except the injected real pulse).
            # Strategy: temporarily separate them, apply sensor to bg,
            # then re-add the real pulse.
            onset_sample = int(DEFAULT_EVENT_ONSET_S * fs)
            real_pulse_len = int(len(load_pulse_csv(event_override)))
            real_pulse_len = min(real_pulse_len, n - onset_sample)
            real_segment = samples[onset_sample:onset_sample + real_pulse_len].copy()
            # Zero out the real pulse region, sensor-model the bg, add real back
            samples_bg = samples.copy()
            samples_bg[onset_sample:onset_sample + real_pulse_len] -= real_segment
            samples_bg = apply_sensor_model(samples_bg, fs=fs)
            samples = samples_bg
            # Reinject the (un-sensor-modeled) real pulse at the same offset
            samples[onset_sample:onset_sample + real_pulse_len] += real_segment
            caveats.append(
                f'sensor model applied to background only; real pulse passed through unchanged')
        else:
            samples = apply_sensor_model(samples, fs=fs)
            caveats.append(
                f'sensor model applied: PVDF+cantilever f_n={CANTILEVER_FN_HZ}Hz zeta={CANTILEVER_ZETA}')
        # Add real-spectrum environmental + sensor electronic noise floor.
        # Added POST-sensor because the real CSV from which the spectrum
        # was extracted is already post-PVDF + post-amp.
        samples = samples + bg_environmental_noise(rng, duration_s, fs)
        caveats.append('real-spectrum noise floor added (post-sensor)')

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
