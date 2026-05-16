"""
Stage 1 Path A fall-detection algorithm for piezo_fall.

Hybrid architecture (per user direction):
  - Rules for signal cleaning and event detection
  - ML (RandomForest) for per-event classification
  - Rules for post-event temporal gating (stillness check)

Article I (Signal First) traceability:
  Every threshold, filter cutoff, and feature definition below traces to
  domain primitive P1 (floor acceleration, m/s², measured via piezo at
  ≥ 1 kHz — Amendment 1) and to physical models documented in
  FALL_DETECTION_DESIGN.md Appendix A.

  The RandomForest classifier is a fitted function over primitive-grounded
  features. Its decision boundaries are learned from data rather than
  hand-coded, but every INPUT to the classifier traces to a primitive.
  Crucible posture: features are constitutional; learned weights are
  data-derived parameters of the same kind as a regression coefficient
  fitted to measurements.

  Training data comes from src/signals.py — synthetic profiles whose
  labels trace to physical class definitions in device_context.md
  Simulation Profile Catalog.

──────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from scipy import signal as scipy_signal

# Lazy sklearn import — only when training/inferring
_sklearn_imported = False


def _import_sklearn():
    global _sklearn_imported, RandomForestClassifier, StandardScaler
    if not _sklearn_imported:
        from sklearn.ensemble import RandomForestClassifier as _RFC
        from sklearn.preprocessing import StandardScaler as _SS
        RandomForestClassifier = _RFC
        StandardScaler = _SS
        _sklearn_imported = True


# ─── Constants (each traces to a primitive or a documented reference) ──

FS_HZ = 1000  # P1 sample rate per Amendment 1 (≥ 1 kHz)

# Signal preprocessing (rules — noise rejection by filtering)
BANDPASS_LOW_HZ = 2.0    # P1: reject DC + slow drift (sub-1-Hz baseline wander)
BANDPASS_HIGH_HZ = 300.0 # P1: keep impact spectrum (50-200 Hz primary band)
NOTCH_HZ = 60.0          # P1: reject mains hum + vent fundamental (60 Hz motor)
NOTCH_Q = 30.0           # narrow notch, doesn't kill nearby bands

# Impulsive event gate (FALL_DETECTION_DESIGN.md §Case 2 stage-1 event gate)
RMS_ENVELOPE_WINDOW_MS = 20   # short window for impact detection
IMPULSIVE_THRESHOLD_SIGMA = 4.0  # RMS env > 4σ of noise baseline = candidate
IMPULSIVE_MIN_DURATION_MS = 15   # below this is too short to be a real impact
EVENT_WINDOW_MS = 500            # window extracted around each event peak

# Slump event gate (audit's identified blind spot — sustained low-amplitude)
SLUMP_WINDOW_S = 1.0     # 1 s long-window RMS for sustained rumble
SLUMP_THRESHOLD_SIGMA = 1.8   # lower threshold, sustained — looking for elevated baseline
SLUMP_MIN_DURATION_S = 1.5    # must persist ≥ 1.5 s to count

# Feature window
FFT_NPERSEG = 256        # for spectral features (gives ~4 Hz freq resolution)

# Temporal context (Q4 — ML learns cadence from these aggregate features)
TEMPORAL_LOOKBACK_S = 5.0  # range over which to count prior events

# Post-event stillness gate (FALL_DETECTION_DESIGN.md §Case 2 stage-3 gate)
STILLNESS_DURATION_S = 5.0  # confirmed fall = no step-like events in next 5 s


# ─── Data structures ───────────────────────────────────────────────────

@dataclass
class CandidateEvent:
    """One detected event from a signal trace."""
    onset_s: float
    peak_s: float
    end_s: float
    kind: str           # 'impulsive' | 'slump'
    peak_value: float
    features: dict = field(default_factory=dict)
    predicted_class: Optional[str] = None  # set by classifier


@dataclass
class DetectionResult:
    """Output of run() — per Amendment 1 P1 primitive output."""
    classified_as: str       # 'fall' | 'not-fall'
    event_time_s: Optional[float]   # for latency measurement
    candidate_events: list[CandidateEvent]
    gate_outcome: str        # diagnostic: 'no_event', 'rejected_by_classifier',
                             # 'rejected_by_stillness', 'fall_confirmed'


# ─── 1. Signal preprocessing (rules) ───────────────────────────────────

def preprocess(samples: np.ndarray, fs: int = FS_HZ) -> np.ndarray:
    """Bandpass 2–300 Hz + 60 Hz notch.

    BANDPASS rationale (P1):
      - 2 Hz HP cuts DC, thermal drift, slow body sway
      - 300 Hz LP keeps the full impact-frequency band (footsteps to 200 Hz,
        object impacts to 300 Hz) without aliasing into Nyquist (= 500 Hz)
    NOTCH rationale (P1):
      - 60 Hz = mains hum AND the bathroom-vent motor fundamental
        (per device_context.md operating envelope, vent_humming is the
        always-on background source — removing its narrow-band carrier
        cleans every recording)
    """
    nyq = fs / 2
    # Bandpass (4th-order Butterworth, zero-phase)
    sos_bp = scipy_signal.butter(
        4, [BANDPASS_LOW_HZ / nyq, BANDPASS_HIGH_HZ / nyq],
        btype='band', output='sos'
    )
    filtered = scipy_signal.sosfiltfilt(sos_bp, samples)
    # 60 Hz notch (IIR notch)
    b_n, a_n = scipy_signal.iirnotch(NOTCH_HZ / nyq, NOTCH_Q)
    filtered = scipy_signal.filtfilt(b_n, a_n, filtered)
    return filtered


# ─── 2. Event detection (rules) ────────────────────────────────────────

def _rms_envelope(samples: np.ndarray, window_samples: int) -> np.ndarray:
    """Rolling RMS over window."""
    sq = samples ** 2
    kernel = np.ones(window_samples) / window_samples
    return np.sqrt(np.convolve(sq, kernel, mode='same'))


def detect_impulsive_events(samples: np.ndarray,
                             fs: int = FS_HZ) -> list[CandidateEvent]:
    """RMS-envelope threshold detector for impulsive events (footsteps,
    drops, fast falls). Returns one CandidateEvent per region where the
    envelope exceeds noise-baseline × IMPULSIVE_THRESHOLD_SIGMA.
    """
    win_samples = int(RMS_ENVELOPE_WINDOW_MS / 1000 * fs)
    env = _rms_envelope(samples, win_samples)
    # Noise baseline = median of envelope (robust to outliers from events)
    baseline = np.median(env)
    mad = np.median(np.abs(env - baseline)) + 1e-12
    # Convert MAD to sigma-equivalent (Gaussian: σ ≈ 1.4826 × MAD)
    sigma = 1.4826 * mad
    thresh = baseline + IMPULSIVE_THRESHOLD_SIGMA * sigma

    above = env > thresh
    events: list[CandidateEvent] = []
    in_event = False
    start_idx = 0
    for i, hi in enumerate(above):
        if hi and not in_event:
            in_event = True
            start_idx = i
        elif not hi and in_event:
            in_event = False
            end_idx = i
            dur_ms = (end_idx - start_idx) / fs * 1000
            if dur_ms >= IMPULSIVE_MIN_DURATION_MS:
                peak_local = np.argmax(np.abs(samples[start_idx:end_idx]))
                peak_idx = start_idx + peak_local
                events.append(CandidateEvent(
                    onset_s=start_idx / fs,
                    peak_s=peak_idx / fs,
                    end_s=end_idx / fs,
                    kind='impulsive',
                    peak_value=float(np.abs(samples[peak_idx])),
                ))
    return events


def detect_slump_events(samples: np.ndarray,
                         fs: int = FS_HZ) -> list[CandidateEvent]:
    """Sustained-rumble detector for slow descents (the audit's blind spot).

    Long-window RMS (1 s) elevated above baseline for ≥ 1.5 s = slump
    candidate. Lower sigma threshold than impulsive because slump is
    intentionally low-amplitude.
    """
    win_samples = int(SLUMP_WINDOW_S * fs)
    env = _rms_envelope(samples, win_samples)
    baseline = np.median(env)
    mad = np.median(np.abs(env - baseline)) + 1e-12
    sigma = 1.4826 * mad
    thresh = baseline + SLUMP_THRESHOLD_SIGMA * sigma

    above = env > thresh
    events: list[CandidateEvent] = []
    in_event = False
    start_idx = 0
    for i, hi in enumerate(above):
        if hi and not in_event:
            in_event = True
            start_idx = i
        elif not hi and in_event:
            in_event = False
            end_idx = i
            dur_s = (end_idx - start_idx) / fs
            if dur_s >= SLUMP_MIN_DURATION_S:
                peak_local = np.argmax(np.abs(samples[start_idx:end_idx]))
                peak_idx = start_idx + peak_local
                events.append(CandidateEvent(
                    onset_s=start_idx / fs,
                    peak_s=peak_idx / fs,
                    end_s=end_idx / fs,
                    kind='slump',
                    peak_value=float(np.abs(samples[peak_idx])),
                ))
    return events


def detect_events(samples: np.ndarray,
                   fs: int = FS_HZ) -> list[CandidateEvent]:
    """Run both impulsive and slump detectors, return merged list sorted
    by onset time."""
    events = detect_impulsive_events(samples, fs) + detect_slump_events(samples, fs)
    events.sort(key=lambda e: e.onset_s)
    return events


# ─── 3. Per-event feature extraction (Appendix A) ──────────────────────

def extract_features(samples: np.ndarray, event: CandidateEvent,
                      fs: int = FS_HZ) -> dict:
    """Compute 6 per-event features for the ML classifier.

    All features trace to FALL_DETECTION_DESIGN.md Appendix A and to P1.
    """
    win_samples = int(EVENT_WINDOW_MS / 1000 * fs)
    peak_idx = int(event.peak_s * fs)
    half = win_samples // 2
    start = max(0, peak_idx - half)
    end = min(len(samples), peak_idx + half)
    window = samples[start:end]
    if len(window) < FFT_NPERSEG:
        # Pad short windows for FFT
        window = np.pad(window, (0, FFT_NPERSEG - len(window)))

    # Feature 1: peak amplitude (Appendix A §1)
    peak_amp = float(np.max(np.abs(window)))

    # Feature 2: total energy (Appendix A §2) — area under |x|²
    total_energy = float(np.sum(window ** 2))

    # Feature 3: duration above noise (Appendix A §3)
    win_ms = int(RMS_ENVELOPE_WINDOW_MS / 1000 * fs)
    env = _rms_envelope(window, win_ms)
    noise_floor = np.median(env)
    duration_above_noise_ms = float(np.sum(env > 3 * noise_floor) / fs * 1000)

    # Feature 4: spectral centroid (Appendix A §5)
    # Falls have low centroid (10-40 Hz), object drops have high (100-300 Hz)
    freqs, psd = scipy_signal.welch(window, fs=fs, nperseg=FFT_NPERSEG)
    total_psd = np.sum(psd) + 1e-12
    spectral_centroid_hz = float(np.sum(freqs * psd) / total_psd)

    # Feature 5: decay time constant (Appendix A §7)
    # Fit envelope of post-peak signal to exp(-t/τ); use simple log-linear fit
    post_peak = env[len(env)//2:]  # second half of envelope
    if len(post_peak) > 5 and np.max(post_peak) > 0:
        # log-linear fit y = log(A) - t/τ
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            log_env = np.log(post_peak + 1e-12)
            t_axis = np.arange(len(post_peak)) / fs
            if np.std(log_env) > 0:
                slope, _ = np.polyfit(t_axis, log_env, 1)
                tau_s = float(-1.0 / slope) if slope < 0 else 1.0
            else:
                tau_s = 1.0
    else:
        tau_s = 1.0
    decay_tau_ms = float(tau_s * 1000)

    # Feature 6: multi-peak count (Appendix A §8)
    # Number of separate peaks ≥ 0.3 × global max, separated by ≥ 20 ms
    threshold = 0.3 * peak_amp
    peak_distance = int(0.020 * fs)  # 20 ms
    peaks, _ = scipy_signal.find_peaks(np.abs(window),
                                        height=threshold,
                                        distance=peak_distance)
    multi_peak_count = int(len(peaks))

    # NEW FEATURES (all scale-invariant or ratio-based for cross-bathroom generalization).
    # Article I: each traces to P1 (floor acceleration) via energy / RMS / band integrals.

    # Pre-event RMS (1 s before event onset). Baseline activity level.
    fs_val = fs  # alias
    pre_start = max(0, int(event.onset_s * fs_val) - fs_val)
    pre_end = max(0, int(event.onset_s * fs_val))
    if pre_end > pre_start + 10:
        pre_event_rms = float(np.sqrt(np.mean(samples[pre_start:pre_end] ** 2)))
    else:
        pre_event_rms = 0.0

    # Post-event RMS (1 s after event end). Stillness measure.
    post_start = min(len(samples), int(event.end_s * fs_val))
    post_end = min(len(samples), post_start + fs_val)
    if post_end > post_start + 10:
        post_event_rms = float(np.sqrt(np.mean(samples[post_start:post_end] ** 2)))
    else:
        post_event_rms = 0.0

    # Pre/post ratio: <1 indicates stillness (fall-like); ~1 or >1 indicates continued activity.
    post_pre_rms_ratio = post_event_rms / (pre_event_rms + 1e-12)

    # Energy band fractions. Falls live 5-30 Hz (soft tissue contact),
    # drops live 100-300 Hz (rigid impact). Per FALL_DETECTION_DESIGN.md Appendix A §6.
    low_band_mask = (freqs >= 5) & (freqs <= 30)
    mid_band_mask = (freqs > 30) & (freqs <= 100)
    high_band_mask = (freqs > 100) & (freqs <= 300)
    total_psd_safe = total_psd  # already computed above
    low_band_energy_frac = float(np.sum(psd[low_band_mask]) / total_psd_safe)
    high_band_energy_frac = float(np.sum(psd[high_band_mask]) / total_psd_safe)

    return {
        'peak_amp': peak_amp,
        'total_energy': total_energy,
        'duration_above_noise_ms': duration_above_noise_ms,
        'spectral_centroid_hz': spectral_centroid_hz,
        'decay_tau_ms': min(decay_tau_ms, 5000.0),  # cap pathological fits
        'multi_peak_count': multi_peak_count,
        # Scale-invariant additions for cross-bathroom generalization
        'pre_event_rms': pre_event_rms,
        'post_event_rms': post_event_rms,
        'post_pre_rms_ratio': min(post_pre_rms_ratio, 100.0),  # cap pathological ratios
        'low_band_energy_frac': low_band_energy_frac,
        'high_band_energy_frac': high_band_energy_frac,
    }


# ─── 4. Temporal context features (Q4: let ML learn cadence) ───────────

def extract_temporal_context(events: list[CandidateEvent],
                              current_idx: int) -> dict:
    """For the event at events[current_idx], summarise temporal context
    over ±TEMPORAL_LOOKBACK_S. Lets the ML classifier discover the
    'walked → BANG → silence' fall pattern without hand-coded rules.
    """
    if current_idx < 0 or current_idx >= len(events):
        return {'events_in_last_5s': 0, 'time_since_last_event_s': 999.0}
    cur_t = events[current_idx].onset_s
    prior = [e for e in events[:current_idx]
             if cur_t - e.onset_s <= TEMPORAL_LOOKBACK_S]
    n_prior = len(prior)
    if prior:
        time_since_last = cur_t - prior[-1].onset_s
    else:
        time_since_last = 999.0  # "no prior event in window"
    return {
        'events_in_last_5s': n_prior,
        'time_since_last_event_s': float(time_since_last),
    }


# Feature column order — must be consistent across train and inference
FEATURE_COLS = [
    'peak_amp', 'total_energy', 'duration_above_noise_ms',
    'spectral_centroid_hz', 'decay_tau_ms', 'multi_peak_count',
    'pre_event_rms', 'post_event_rms', 'post_pre_rms_ratio',
    'low_band_energy_frac', 'high_band_energy_frac',
    'events_in_last_5s', 'time_since_last_event_s',
]


def feature_dict_to_vec(d: dict) -> np.ndarray:
    return np.array([d[k] for k in FEATURE_COLS], dtype=np.float64)


# ─── 5. ML classifier (training and inference) ─────────────────────────

@dataclass
class TrainedModel:
    rf: object  # RandomForestClassifier (lazy-typed)
    scaler: object  # StandardScaler
    feature_cols: list[str]


def train_classifier(seeds_per_profile: int = 30,
                      seed_base: int = 1000,
                      n_estimators: int = 200,
                      max_depth: int = 8,
                      model_type: str = 'rf',
                      ) -> TrainedModel:
    """Generate synthetic data from src/signals.py, extract features per
    detected event, fit RandomForest. Returns trained model bundle.

    Labels: each event's predicted class is the profile's class label
    ('noise', 'confuser', 'fall'). For inference we'll collapse to
    binary 'fall' / 'not-fall' at the gate-outcome stage.
    """
    _import_sklearn()
    from .signals import generate, list_profiles

    X_list: list[np.ndarray] = []
    y_list: list[str] = []

    for profile in list_profiles():
        for seed_offset in range(seeds_per_profile):
            seed = seed_base + seed_offset
            samples, gt = generate(profile, seed=seed)
            samples = preprocess(samples)
            events = detect_events(samples)
            for i, ev in enumerate(events):
                feats = extract_features(samples, ev)
                feats.update(extract_temporal_context(events, i))
                X_list.append(feature_dict_to_vec(feats))
                y_list.append(gt.cls)

    if not X_list:
        raise RuntimeError("No events detected across all training profiles — "
                            "tune detector thresholds")

    X = np.vstack(X_list)
    y = np.array(y_list)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    if model_type == 'rf':
        clf = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            class_weight='balanced',
            random_state=42,
        )
    elif model_type == 'svm':
        # SVM with RBF kernel — alternative decision boundary geometry
        from sklearn.svm import SVC
        clf = SVC(
            kernel='rbf',
            class_weight='balanced',
            probability=False,
            random_state=42,
        )
    else:
        raise ValueError(f"Unknown model_type: {model_type}")
    clf.fit(X_scaled, y)
    return TrainedModel(rf=clf, scaler=scaler, feature_cols=FEATURE_COLS)


# Lazy module-level model cache
_default_model: Optional[TrainedModel] = None


def _get_default_model() -> TrainedModel:
    global _default_model
    if _default_model is None:
        _default_model = train_classifier()
    return _default_model


# ─── 6. Stillness gate (post-event temporal rule) ──────────────────────

def stillness_confirmed(events: list[CandidateEvent],
                         candidate_idx: int,
                         total_duration_s: float) -> bool:
    """A fall candidate is confirmed only if NO additional impulsive event
    occurs within STILLNESS_DURATION_S after it. Rationale: a real fall
    is followed by silence; a person who dropped something keeps walking.
    """
    cand = events[candidate_idx]
    cutoff = cand.end_s + STILLNESS_DURATION_S
    for ev in events[candidate_idx + 1:]:
        if ev.onset_s > cutoff:
            break
        if ev.kind == 'impulsive':
            # Step-like activity after the candidate → reject
            return False
    return True


# ─── 7. Main inference entry point ─────────────────────────────────────

def run(samples: np.ndarray,
         fs: int = FS_HZ,
         model: Optional[TrainedModel] = None,
         ) -> DetectionResult:
    """Full pipeline: preprocess → detect → classify → stillness gate.

    Returns DetectionResult with class label (binary 'fall' / 'not-fall'),
    event time (for latency measurement), all candidate events with features,
    and a diagnostic gate-outcome label.
    """
    if model is None:
        model = _get_default_model()

    filtered = preprocess(samples, fs)
    events = detect_events(filtered, fs)
    duration_s = len(samples) / fs

    if not events:
        return DetectionResult(
            classified_as='not-fall',
            event_time_s=None,
            candidate_events=[],
            gate_outcome='no_event',
        )

    # Classify each event — use the MODEL's feature_cols (not global)
    # so RF-8/RF-13/SVM-13 etc. all work with their respective feature subsets.
    feature_rows = []
    cols = getattr(model, 'feature_cols', FEATURE_COLS)
    for i, ev in enumerate(events):
        feats = extract_features(filtered, ev, fs)
        feats.update(extract_temporal_context(events, i))
        ev.features = feats
        # Select only the feature columns the model was trained on
        feature_rows.append(np.array([feats[c] for c in cols], dtype=np.float64))

    X = np.vstack(feature_rows)
    X_scaled = model.scaler.transform(X)
    preds = model.rf.predict(X_scaled)

    for ev, pred in zip(events, preds):
        ev.predicted_class = str(pred)

    # Find first 'fall' candidate
    fall_candidates = [i for i, ev in enumerate(events) if ev.predicted_class == 'fall']
    if not fall_candidates:
        return DetectionResult(
            classified_as='not-fall',
            event_time_s=None,
            candidate_events=events,
            gate_outcome='rejected_by_classifier',
        )

    # Apply stillness gate
    for cand_idx in fall_candidates:
        if stillness_confirmed(events, cand_idx, duration_s):
            return DetectionResult(
                classified_as='fall',
                event_time_s=events[cand_idx].onset_s,
                candidate_events=events,
                gate_outcome='fall_confirmed',
            )

    return DetectionResult(
        classified_as='not-fall',
        event_time_s=None,
        candidate_events=events,
        gate_outcome='rejected_by_stillness',
    )
