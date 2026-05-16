"""Compare RF-8, RF-13, SVM-13 on the same synthetic validation set."""

import sys
sys.path.insert(0, '/home/sni22/crucible/piezo_fall')
import time
from collections import defaultdict
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler

from src.signals import generate, list_profiles
from src.algorithm import (
    preprocess, detect_events, extract_features,
    extract_temporal_context, feature_dict_to_vec, FEATURE_COLS,
    run, TrainedModel,
)

# Two feature sets to compare
FEATURE_SET_8 = [
    'peak_amp', 'total_energy', 'duration_above_noise_ms',
    'spectral_centroid_hz', 'decay_tau_ms', 'multi_peak_count',
    'events_in_last_5s', 'time_since_last_event_s',
]
FEATURE_SET_13 = FEATURE_COLS  # all 13 from current algorithm.py


def build_training_set(seeds_per_profile=20, seed_base=1000):
    """Generate synthetic traces, extract features per detected event, return X, y."""
    X_list = []
    y_list = []
    print(f'Generating training data ({seeds_per_profile} seeds × {len(list_profiles())} profiles)...', flush=True)
    t0 = time.time()
    for profile in list_profiles():
        for seed_off in range(seeds_per_profile):
            seed = seed_base + seed_off
            samples, gt = generate(profile, seed=seed, geometry=['small','medium'][seed_off % 2])
            filtered = preprocess(samples)
            events = detect_events(filtered)
            for i, ev in enumerate(events):
                feats = extract_features(filtered, ev)
                feats.update(extract_temporal_context(events, i))
                X_list.append(feats)
                y_list.append(gt.cls)
    print(f'  collected {len(X_list)} events in {time.time()-t0:.1f}s', flush=True)
    return X_list, np.array(y_list)


def fit_model(X_list, y, feature_cols, model_type):
    """Fit a model on the given feature subset."""
    X = np.array([[feats[c] for c in feature_cols] for feats in X_list], dtype=np.float64)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    if model_type == 'rf':
        clf = RandomForestClassifier(
            n_estimators=200, max_depth=8,
            class_weight='balanced', random_state=42,
        )
    else:  # svm
        clf = SVC(kernel='rbf', class_weight='balanced', random_state=42)
    clf.fit(X_scaled, y)
    return TrainedModel(rf=clf, scaler=scaler, feature_cols=feature_cols)


def build_test_set(test_seeds=40, seed_base=6000):
    """Generate test traces ONCE so all models can share them."""
    test_traces = []  # list of (profile, seed, geom, samples, gt)
    truths = {}
    print(f'    building test set ({test_seeds} seeds × {len(list_profiles())} profiles × 2 geoms)...', flush=True)
    t0 = time.time()
    for profile in list_profiles():
        for seed_off in range(test_seeds):
            seed = seed_base + seed_off
            for geom in ['small', 'medium']:
                samples, gt = generate(profile, seed=seed, geometry=geom)
                test_traces.append((profile, seed, geom, samples, gt))
                truths[profile] = gt.cls
    print(f'    built {len(test_traces)} test traces in {time.time()-t0:.1f}s', flush=True)
    return test_traces, truths


def validate_with_test_set(model, test_traces):
    """Run model against pre-generated test traces."""
    results = defaultdict(lambda: defaultdict(list))
    for profile, seed, geom, samples, gt in test_traces:
        r = run(samples, model=model)
        results[profile][geom].append(r.classified_as)
    return results


def summarize(name, results, truths):
    """Compute summary stats."""
    fc = 0; ft = 0; fps = 0; fpt = 0
    for prof in results:
        for geom in ['small', 'medium']:
            preds = results[prof][geom]
            n_fall = sum(1 for p in preds if p == 'fall')
            n_total = len(preds)
            if truths[prof] == 'fall':
                fc += n_fall
                ft += n_total
            else:
                fps += n_fall
                fpt += n_total
    sens = 100 * fc / ft if ft > 0 else 0
    fp_rate = 100 * fps / fpt if fpt > 0 else 0
    return {'name': name, 'sens': sens, 'fp_rate': fp_rate, 'fc': fc, 'ft': ft, 'fps': fps, 'fpt': fpt}


# ─── Main comparison ───────────────────────────────────────────────
print('=== Classifier Comparison: RF-8 vs RF-13 vs SVM-13 ===', flush=True)
print()

X_list, y = build_training_set(seeds_per_profile=20)

print()
print('Fitting RF-8...', flush=True)
t = time.time()
model_rf8 = fit_model(X_list, y, FEATURE_SET_8, 'rf')
print(f'  fit in {time.time()-t:.1f}s', flush=True)
print('Fitting RF-13...', flush=True)
t = time.time()
model_rf13 = fit_model(X_list, y, FEATURE_SET_13, 'rf')
print(f'  fit in {time.time()-t:.1f}s', flush=True)
print('Fitting SVM-13...', flush=True)
t = time.time()
model_svm13 = fit_model(X_list, y, FEATURE_SET_13, 'svm')
print(f'  fit in {time.time()-t:.1f}s', flush=True)
print()

# Build test set ONCE (shared across all models)
N = 40
print(f'Validating ({N} seeds × {len(list_profiles())} profiles × 2 geoms)...', flush=True)
test_traces, truths = build_test_set(test_seeds=N)
all_results = {}
for name, model in [('RF-8', model_rf8), ('RF-13', model_rf13), ('SVM-13', model_svm13)]:
    print(f'  {name}...', flush=True)
    t = time.time()
    results = validate_with_test_set(model, test_traces)
    print(f'    done in {time.time()-t:.1f}s', flush=True)
    all_results[name] = (results, truths, summarize(name, results, truths))

print()
print('═════════════════════════════════════════════════════════════════')
print('SUMMARY')
print('═════════════════════════════════════════════════════════════════')
print(f'{"model":<10} {"sensitivity":<14} {"FP rate":<14} {"FP/week (est)":<14}')
print('-' * 65)
for name in ['RF-8', 'RF-13', 'SVM-13']:
    s = all_results[name][2]
    sim_h = 10 * N * 30 / 3600  # 10 non-fall profiles × N seeds × 30s × 2 geoms
    fpw = (s['fps'] / sim_h) * 168 if sim_h > 0 else 0
    print(f'{name:<10} {s["fc"]}/{s["ft"]} ({s["sens"]:>5.1f}%)  '
          f'{s["fps"]}/{s["fpt"]} ({s["fp_rate"]:>5.2f}%) {fpw:>10.0f}')

print()
print('Per-profile FP breakdown:')
print(f'{"profile":<24} {"truth":<10} {"RF-8":<8} {"RF-13":<8} {"SVM-13":<8}')
print('-' * 60)
profiles = list_profiles()
for profile in profiles:
    line = f'{profile:<24} '
    truth = all_results['RF-8'][1][profile]
    line += f'{truth:<10} '
    for name in ['RF-8', 'RF-13', 'SVM-13']:
        results, truths, _ = all_results[name]
        all_preds = results[profile]['small'] + results[profile]['medium']
        n_fall = sum(1 for p in all_preds if p == 'fall')
        n_total = len(all_preds)
        if truth == 'fall':
            line += f'{n_fall}/{n_total:<5} '
        else:
            line += f'{n_fall}/{n_total:<5} '
    print(line)
