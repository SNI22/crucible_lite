"""
Stage 1 Path A signal generator for piezo_fall.

Each profile is a composite of one always-on background (ventilator humming)
plus optional plumbing/noise sources plus an optional event pulse.

Event pulses can be either SYNTHETIC (analytical model below) or REAL
(loaded from a pre-cropped CSV in the receiver.py sample_index,value,event
schema). The simulator framework treats them uniformly — same composition
pipeline, same output shape.

────────────────────────────────────────────────────────────────────────
Article I (Signal First) — what this file traces to:

  Domain primitive P1 (per Amendment 1): floor acceleration (m/s²),
  measured via piezo (PVDF + proof-mass cantilever) at ≥ 1 kHz.

  Every event pulse and background source below derives from a stated
  physical model of how that source couples into the bathroom floor.
  Parameters are NOT calibrated to absolute m/s² in this Stage 1
  iteration — they are in *arbitrary amplitude units* internally
  consistent across profiles. Absolute calibration is a deferred Stage 2
  task that requires:
    1. The firmware's `accur = 0.015295` constant (currently in the
       FW-IDENTITY-UNRESOLVED firmware — see toolchain_config.md
       Stage 0 Ruling), giving ADC count → voltage.
    2. The piezo+amplifier sensitivity in mV per m/s² — currently
       unmeasured (deferred to Stage 2 / 3 calibration test).
  When those two values become known, set ADC_TO_MS2 below to the
  product, and all output rescales automatically.

  Stage 1 algorithm development uses scale-invariant features (band
  ratios, multi-peak count, spectral centroid in Hz, decay time
  constants), so arbitrary-unit operation is acceptable for now.

────────────────────────────────────────────────────────────────────────
Sample rate: fixed at 1 kHz. Amendment 1's piezo clause is "≥ 1 kHz";
1 kHz is the floor (stretch path to 2 kHz exists per toolchain_config.md
Hardware contingency note).

────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

# ─── Constants ──────────────────────────────────────────────────────────

FS_HZ = 1000  # primitive P1 sample rate — Amendment 1 ≥ 1 kHz floor
DEFAULT_DURATION_S = 30.0  # matches the 30 s detection-latency target
DEFAULT_EVENT_ONSET_S = 10.0  # event at T=10 s → 20 s of post-event window

# Deferred-calibration constant. Multiply internal arbitrary units by this
# to convert to m/s². Stage 2 must set this from firmware `accur` × piezo
# sensitivity (mV/(m/s²)). Until then we operate in arbitrary units.
ADC_TO_MS2 = 1.0  # TODO: Stage 2 — derive from accur (0.015295) + piezo sensitivity


# ─── Ground-truth structure ─────────────────────────────────────────────

@dataclass
class GroundTruth:
    """Returned alongside the signal so the evaluator knows the right answer."""
    profile: str
    cls: str  # 'noise' | 'confuser' | 'fall'
    event_onset_s: float | None  # None for noise profiles
    fs: int
    source: str  # 'synthetic' | 'real_csv:<path>'
    caveats: list[str] = field(default_factory=list)


# ─── Synthetic event-pulse generators ───────────────────────────────────
#
# Each function returns a 1D ndarray of length n samples at FS_HZ.
# Pulses are amplitude-normalized so a "typical" event peaks around 1.0;
# the composer scales these to match the chosen event amplitude.
# Physical basis is cited in the docstring of each.

def _damped_oscillator(fs: int, duration_s: float, freq_hz: float,
                        tau_s: float, rng: np.random.Generator,
                        phase_jitter: bool = True) -> np.ndarray:
    """sin(2πf t) · exp(-t/τ).  The Appendix-A "decay envelope" model.

    Used as the building block for all rigid-contact impacts: a brief
    contact rings the floor's local mode at frequency f, decaying with
    time constant τ. Different (f, τ) → different impact signatures.
    """
    n = int(fs * duration_s)
    t = np.arange(n) / fs
    phase = rng.uniform(0, 2 * np.pi) if phase_jitter else 0.0
    return np.sin(2 * np.pi * freq_hz * t + phase) * np.exp(-t / tau_s)


def pulse_footstep(rng: np.random.Generator) -> np.ndarray:
    """Single heel-strike. ~30-50 ms duration. High-band (50-200 Hz)
    because small rigid contact area (heel) couples stiffly.

    Reference: FALL_DETECTION_DESIGN.md §Case 2, "footsteps: ~30–80 ms,
    50–150 Hz, quick single-mode ringdown".
    """
    freq = rng.uniform(80, 150)  # heel-strike fundamental
    tau = rng.uniform(0.008, 0.015)  # fast single-mode decay
    pulse = _damped_oscillator(FS_HZ, 0.06, freq, tau, rng)
    return pulse / np.max(np.abs(pulse))


def pulse_drop_phone(rng: np.random.Generator) -> np.ndarray:
    """Light rigid drop (~150-250 g). Brief sharp impact, ~5-15 ms.
    Frequency band 100-300 Hz (small contact area, low compliance).
    Single peak. Reference: FALL_DETECTION_DESIGN.md §Case 3 rigid
    impact column.
    """
    freq = rng.uniform(150, 280)
    tau = rng.uniform(0.004, 0.010)
    pulse = _damped_oscillator(FS_HZ, 0.04, freq, tau, rng)
    return pulse / np.max(np.abs(pulse))


def pulse_drop_heavy(rng: np.random.Generator) -> np.ndarray:
    """Heavy rigid drop (~500-700 g, e.g. hair dryer + plug). Longer
    contact, more low-band energy than phone. Plug-bounce may add a
    secondary low-amplitude tail (modeled as a soft after-impact).
    """
    freq = rng.uniform(80, 180)
    tau = rng.uniform(0.010, 0.020)
    main = _damped_oscillator(FS_HZ, 0.06, freq, tau, rng)
    # Plug bounce: small after-impact 20-40 ms later
    after = np.zeros_like(main)
    delay = int(rng.uniform(0.020, 0.040) * FS_HZ)
    bounce = _damped_oscillator(FS_HZ, 0.04 - delay / FS_HZ, freq * 1.2,
                                tau * 0.6, rng) * 0.3
    after[delay:delay + len(bounce)] = bounce
    pulse = main + after
    return pulse / np.max(np.abs(pulse))


def pulse_drop_glass(rng: np.random.Generator) -> np.ndarray:
    """Brittle multi-impact drop (~200 g cosmetic glass). 2-4 closely
    spaced impacts as the object lands + fragments scatter. High band
    (200-500 Hz) because fragments are small and rigid. THIS PROFILE
    SPECIFICALLY TESTS whether the naive "multi-peak ≥ 2 → fall"
    feature breaks — a glass drop is multi-peak but NOT a fall.
    """
    n = int(0.10 * FS_HZ)
    pulse = np.zeros(n)
    n_impacts = rng.integers(2, 5)
    for _ in range(n_impacts):
        freq = rng.uniform(200, 500)
        tau = rng.uniform(0.003, 0.008)
        sub = _damped_oscillator(FS_HZ, 0.03, freq, tau, rng) * rng.uniform(0.3, 1.0)
        onset = rng.integers(0, n - len(sub))
        pulse[onset:onset + len(sub)] += sub
    return pulse / np.max(np.abs(pulse))


def pulse_fall_fast(rng: np.random.Generator) -> np.ndarray:
    """Fast human fall — multi-impact body sequence (hip → limb → head
    over ~100-300 ms), low-band (10-40 Hz) from soft tissue contact.
    Reference: FALL_DETECTION_DESIGN.md §Case 2 fall column and
    §Multi-impact count feature.
    """
    n = int(0.50 * FS_HZ)
    pulse = np.zeros(n)
    n_impacts = rng.integers(2, 4)
    amps = sorted(rng.uniform(0.4, 1.0, n_impacts), reverse=True)
    inter_impact_ms = rng.uniform(0.060, 0.200, n_impacts - 1)
    onset_ms = 0.0
    for i in range(n_impacts):
        freq = rng.uniform(15, 40)  # soft-tissue contact, low band
        tau = rng.uniform(0.020, 0.060)
        sub = _damped_oscillator(FS_HZ, 0.20, freq, tau, rng) * amps[i]
        onset = int(onset_ms / 1000.0 * FS_HZ)
        if onset + len(sub) > n:
            sub = sub[:n - onset]
        pulse[onset:onset + len(sub)] += sub
        if i < n_impacts - 1:
            onset_ms += inter_impact_ms[i] * 1000.0
    return pulse / np.max(np.abs(pulse))


def pulse_fall_slump(rng: np.random.Generator) -> np.ndarray:
    """Slow controlled descent — the audit's identified blind spot.

    Physical model: sustained low-amplitude friction rumble for 2-4 s
    as the body slides down a wall / tub, followed by a SOFT final
    impact when the body comes to rest. Frequency very low (5-20 Hz)
    for friction; the final impact slightly higher (10-30 Hz, lower
    amplitude than a fast-fall impact because most KE was dissipated
    in friction).

    NOTE: This is a hand-built physical model — slump signature was
    NEVER recorded in the prior project, so there is no ground-truth
    reference to validate against. Parameters are reasonable physical
    estimates; revisit when real slump data exists (Stage 3 field
    test, if feasible to surrogate with a heavy sandbag lowered by
    rope).
    """
    slide_dur = rng.uniform(2.0, 4.0)
    n_slide = int(slide_dur * FS_HZ)
    # Pink-ish narrow-band noise as friction rumble
    raw = rng.standard_normal(n_slide)
    # Lowpass to 5-20 Hz region via simple moving average + decimate-equivalent
    kernel_len = int(FS_HZ * 0.05)  # 50 ms boxcar → ~10 Hz lowpass
    kernel = np.ones(kernel_len) / kernel_len
    friction = np.convolve(raw, kernel, mode='same')
    # Envelope: friction increases as body accelerates downward, then dies
    env = np.linspace(0.3, 1.0, n_slide) * np.exp(
        -((np.arange(n_slide) - n_slide * 0.7) ** 2) / (n_slide * 0.3) ** 2
    )
    friction *= env
    friction /= np.max(np.abs(friction)) + 1e-12
    friction *= 0.3  # slump amplitude is intentionally LOW — the whole point

    # Soft final impact
    impact_freq = rng.uniform(10, 30)
    impact_tau = rng.uniform(0.030, 0.080)
    final_impact = _damped_oscillator(FS_HZ, 0.20, impact_freq,
                                       impact_tau, rng) * 0.6
    n_pad = int(0.05 * FS_HZ)  # 50 ms gap between slide-end and impact
    pulse = np.concatenate([friction, np.zeros(n_pad), final_impact])
    return pulse / np.max(np.abs(pulse))


# Dispatch table: synthetic-pulse name → generator fn
SYNTH_PULSES = {
    'footstep': pulse_footstep,
    'drop_phone': pulse_drop_phone,
    'drop_heavy': pulse_drop_heavy,
    'drop_glass': pulse_drop_glass,
    'fall_fast': pulse_fall_fast,
    'fall_slump': pulse_fall_slump,
}


# ─── Synthetic background generators ────────────────────────────────────

def bg_vent(rng: np.random.Generator, duration_s: float) -> np.ndarray:
    """Bathroom exhaust fan: narrow-band hum at 60 Hz motor frequency
    + 2nd and 3rd harmonics, very small amplitude (always-on baseline).
    """
    n = int(duration_s * FS_HZ)
    t = np.arange(n) / FS_HZ
    sig = (np.sin(2 * np.pi * 60.0 * t + rng.uniform(0, 2*np.pi)) * 0.04
           + np.sin(2 * np.pi * 120.0 * t + rng.uniform(0, 2*np.pi)) * 0.02
           + np.sin(2 * np.pi * 180.0 * t + rng.uniform(0, 2*np.pi)) * 0.01)
    # Add a touch of broadband noise — sensor + electronics floor
    sig += rng.standard_normal(n) * 0.005
    return sig


def bg_shower(rng: np.random.Generator, duration_s: float) -> np.ndarray:
    """Shower running: broadband water-on-tile, dominant 100-800 Hz band.
    Modeled as bandpass-shaped white noise.
    """
    n = int(duration_s * FS_HZ)
    raw = rng.standard_normal(n)
    # Crude bandpass: subtract running mean (~highpass) and lowpass with MA
    raw -= np.convolve(raw, np.ones(int(FS_HZ / 100)) / int(FS_HZ / 100),
                       mode='same')  # rough highpass ~100 Hz
    sig = np.convolve(raw, np.ones(int(FS_HZ / 800)) / int(FS_HZ / 800),
                      mode='same')  # rough lowpass ~800 Hz
    return sig * 0.15


def bg_flush(rng: np.random.Generator, duration_s: float) -> np.ndarray:
    """Toilet flush transient: ~30 s. Tank-fill (broadband 100-500 Hz)
    for first ~10 s, then drain swirl + tank refill. Returns to silence
    after ~30 s.
    """
    n = int(duration_s * FS_HZ)
    sig = np.zeros(n)
    flush_start = int(FS_HZ * rng.uniform(2.0, 5.0))
    flush_dur = int(FS_HZ * 30.0)
    flush_end = min(flush_start + flush_dur, n)
    raw = rng.standard_normal(flush_end - flush_start)
    raw -= np.convolve(raw, np.ones(int(FS_HZ / 100)) / int(FS_HZ / 100),
                       mode='same')
    flush_sig = np.convolve(raw, np.ones(int(FS_HZ / 500)) / int(FS_HZ / 500),
                            mode='same')
    # Envelope: ramp up, sustain, ramp down
    env = np.ones(flush_end - flush_start)
    ramp = int(FS_HZ * 2.0)
    env[:ramp] = np.linspace(0, 1, ramp)
    env[-ramp:] = np.linspace(1, 0, ramp)
    sig[flush_start:flush_end] = flush_sig * env * 0.20
    return sig


def bg_washer(rng: np.random.Generator, duration_s: float,
              attenuation: float = 1.0) -> np.ndarray:
    """Washing machine on spin cycle: narrow-band ~20-30 Hz motor +
    sidebands. attenuation = 1.0 for local, ~0.25 for through-wall
    neighbor (lowpass attenuation through structure).
    """
    n = int(duration_s * FS_HZ)
    t = np.arange(n) / FS_HZ
    spin_hz = rng.uniform(22.0, 28.0)
    sig = np.sin(2 * np.pi * spin_hz * t + rng.uniform(0, 2*np.pi)) * 0.25
    # Sidebands from mechanical imbalance
    sig += np.sin(2 * np.pi * (spin_hz * 2) * t) * 0.10
    sig += np.sin(2 * np.pi * (spin_hz * 0.5) * t) * 0.05
    sig += rng.standard_normal(n) * 0.01
    if attenuation < 1.0:
        # Lowpass for through-wall attenuation: structure damps high freqs
        kernel = np.ones(int(FS_HZ / 30)) / int(FS_HZ / 30)
        sig = np.convolve(sig, kernel, mode='same')
    return sig * attenuation


# ─── Real-pulse loader ──────────────────────────────────────────────────

def load_pulse_csv(path: str | Path) -> np.ndarray:
    """Load a pre-cropped pulse CSV in receiver.py format
    (sample_index, value, event). Returns the 'value' column as ndarray.

    Caller is responsible for pre-cropping the CSV to just the pulse
    window (e.g., 50-500 ms around the tagged event) using a GUI tool.
    Sample rate is assumed to match FS_HZ (the firmware's ≥ 1 kHz spec);
    this is an OPEN FINDING (SAMPLE-RATE-UNMEASURED, Stage 0 ruling)
    that may require future rescaling.
    """
    values = []
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            values.append(float(row['value']))
    arr = np.array(values, dtype=np.float64)
    # Normalize to peak = 1 in arbitrary units (matches synthetic convention)
    peak = np.max(np.abs(arr))
    return arr / peak if peak > 0 else arr


# ─── Profile recipes ────────────────────────────────────────────────────
# Each entry: (class, background_sources, event_type, event_amp)

@dataclass
class Recipe:
    cls: str
    bg_sources: list[str]  # names of bg_* functions ('vent', 'shower', etc.)
    event_type: str | None  # name in SYNTH_PULSES, or None for noise profiles
    event_amp: float = 1.0  # peak amplitude of injected pulse (arbitrary units)


PROFILES: dict[str, Recipe] = {
    'noise_vent':          Recipe('noise', ['vent'], None),
    'noise_shower':        Recipe('noise', ['vent', 'shower'], None),
    'noise_flush':         Recipe('noise', ['vent', 'flush'], None),
    'noise_washer_local':  Recipe('noise', ['vent', 'washer_local'], None),
    'noise_washer_neighbor': Recipe('noise', ['vent', 'washer_neighbor'], None),
    # Confusers: discrete events that look fall-like but aren't.
    # Event amplitudes calibrated so the 3 m far-step is ≈ a 3 m far-fall
    # amplitude (the Case 2 hard discrimination point).
    'confuser_step':       Recipe('confuser', ['vent'], 'footstep', event_amp=0.6),
    'confuser_drop_phone': Recipe('confuser', ['vent'], 'drop_phone', event_amp=0.5),
    'confuser_drop_heavy': Recipe('confuser', ['vent'], 'drop_heavy', event_amp=0.9),
    'confuser_drop_glass': Recipe('confuser', ['vent'], 'drop_glass', event_amp=0.6),
    # Falls: the positive class.
    'fall_fast':           Recipe('fall', ['vent'], 'fall_fast', event_amp=0.7),
    'fall_slump':          Recipe('fall', ['vent', 'shower'], 'fall_slump', event_amp=0.4),
}


# ─── Main entry point ───────────────────────────────────────────────────

def generate(profile: str,
             duration_s: float = DEFAULT_DURATION_S,
             seed: int = 0,
             event_onset_s: float = DEFAULT_EVENT_ONSET_S,
             event_override: str | Path | None = None,
             ) -> tuple[np.ndarray, GroundTruth]:
    """Generate one signal trace for the named profile.

    Args:
        profile: one of the 11 keys in PROFILES.
        duration_s: total window length (default 30 s — matches latency target).
        seed: RNG seed for reproducibility.
        event_onset_s: when in the window the event pulse is injected
            (default 10 s → 20 s of post-event time for stillness gating).
            Ignored for pure-noise profiles.
        event_override: path to a pre-cropped pulse CSV. If given, REPLACES
            the synthetic event pulse with the real recording. Background
            sources are still synthetic. Useful for testing the algorithm
            against real recorded events (e.g., a real footstep recording
            substituted into the confuser_step composite).

    Returns:
        (samples, ground_truth):
            samples: shape (duration_s * FS_HZ,) in arbitrary amplitude units.
            ground_truth: GroundTruth dataclass with class label, event
                onset (None for noise profiles), source, and caveats list.
    """
    if profile not in PROFILES:
        raise KeyError(f"Unknown profile {profile!r}. "
                       f"Available: {sorted(PROFILES.keys())}")

    recipe = PROFILES[profile]
    rng = np.random.default_rng(seed)
    n = int(duration_s * FS_HZ)
    samples = np.zeros(n)

    # 1. Generate background(s)
    for bg_name in recipe.bg_sources:
        if bg_name == 'vent':
            samples += bg_vent(rng, duration_s)
        elif bg_name == 'shower':
            samples += bg_shower(rng, duration_s)
        elif bg_name == 'flush':
            samples += bg_flush(rng, duration_s)
        elif bg_name == 'washer_local':
            samples += bg_washer(rng, duration_s, attenuation=1.0)
        elif bg_name == 'washer_neighbor':
            samples += bg_washer(rng, duration_s, attenuation=0.25)
        else:
            raise ValueError(f"Unknown bg source {bg_name!r}")

    # 2. Generate or load event pulse (if any)
    caveats: list[str] = []
    source = 'synthetic'
    if recipe.event_type is not None:
        if event_override is not None:
            pulse = load_pulse_csv(event_override)
            source = f'real_csv:{event_override}'
            caveats.append(
                'Real-data pulse: sample rate assumed 1 kHz (SAMPLE-RATE-UNMEASURED)'
            )
        else:
            pulse_fn = SYNTH_PULSES[recipe.event_type]
            pulse = pulse_fn(rng)
        pulse *= recipe.event_amp

        # Inject at event_onset_s (center-aligned)
        onset_sample = int(event_onset_s * FS_HZ)
        end_sample = min(onset_sample + len(pulse), n)
        samples[onset_sample:end_sample] += pulse[:end_sample - onset_sample]
        gt_onset = event_onset_s
    else:
        gt_onset = None

    gt = GroundTruth(
        profile=profile,
        cls=recipe.cls,
        event_onset_s=gt_onset,
        fs=FS_HZ,
        source=source,
        caveats=caveats,
    )
    return samples, gt


def list_profiles() -> list[str]:
    """Return the canonical list of profile names."""
    return list(PROFILES.keys())
