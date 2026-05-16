"""Corrected sim-to-real test (v2, 2026-05-16).

Tag mapping per user clarification:
  step  → confuser (NOT-fall)              → substitute into confuser_step
  other → confuser (NOT-fall, water bottle) → substitute into confuser_drop_phone
  fall  → fall (catfood = body fall)       → substitute into fall_fast

Per-distance grouping via peak-sorted amplitude (matches design intent).
Catfood 1.5m group split into "unblocked" (top 3) and "blocked" (bottom 3)
to test body-absorption hypothesis.
"""

import sys, csv, tempfile
sys.path.insert(0, '/home/sni22/crucible/piezo_fall')
from pathlib import Path
from collections import defaultdict
import numpy as np

from src.signals import generate, list_profiles, FS_HZ
from src.algorithm import run, train_classifier


def load_csv_with_events(path):
    values, events = [], []
    with open(path) as f:
        for row in csv.DictReader(f):
            values.append(float(row['value']))
            events.append(row['event'].strip())
    return np.array(values), np.array(events)


def extract_event_window(values, event_idx, window=500):
    """Snap to local max within ±300 of tag, then crop ±window/2."""
    s0, s1 = max(0, event_idx - 300), min(len(values), event_idx + 300)
    local_peak_offset = np.argmax(np.abs(values[s0:s1]))
    actual_idx = s0 + local_peak_offset
    w0 = max(0, actual_idx - window // 2)
    w1 = min(len(values), actual_idx + window // 2)
    return values[w0:w1], np.max(np.abs(values[w0:w1]))


def write_pulse_csv(pulse, path):
    with open(path, 'w') as f:
        f.write('sample_index,value,event\n')
        for i, v in enumerate(pulse):
            f.write(f'{i},{v:.6f},\n')


CSVS = [
    {
        'path': '/home/sni22/Documents/piezo_circuit/bathroom_testing/step_201505.csv',
        'tag': 'step',
        'expected_class': 'confuser',  # NOT-fall
        'substitute_into': 'confuser_step',
        'layout': [(0.5, 3), (1.5, 3), (2.0, 3)],  # (distance, n_events) — peak-sorted
    },
    {
        'path': '/home/sni22/Documents/piezo_circuit/bathroom_testing/catfood_201505.csv',
        'tag': 'fall',
        'expected_class': 'fall',  # FALL (catfood = body fall surrogate)
        'substitute_into': 'fall_fast',
        'layout': [(0.5, 3), (1.5, 6), (2.0, 3)],  # 6 at 1.5m = unblocked+blocked
        'split_1_5m': True,  # split 1.5m group into unblocked (top 3) / blocked (bottom 3)
    },
    {
        'path': '/home/sni22/Documents/piezo_circuit/bathroom_testing/water_201505.csv',
        'tag': 'other',
        'expected_class': 'confuser',  # NOT-fall (water = rigid object drop)
        'substitute_into': 'confuser_drop_phone',
        'layout': [(0.5, 3), (1.5, 3), (2.0, 3)],
    },
]

print('=== Sim-to-Real v2 — corrected tag mapping ===', flush=True)
print('Training classifier...', flush=True)
import time
t0 = time.time()
model = train_classifier(seeds_per_profile=20, seed_base=1000)
print(f'  trained in {time.time()-t0:.1f}s', flush=True)
print()

tmp_dir = Path(tempfile.mkdtemp(prefix='piezo_real_v2_'))

# Collect: per-event {distance, peak, classification}
results = []

for test in CSVS:
    print(f'--- {Path(test["path"]).name} (tag={test["tag"]}, expected={test["expected_class"]}, → {test["substitute_into"]}) ---', flush=True)
    values, events = load_csv_with_events(test['path'])
    event_indices = np.where(events == test['tag'])[0]

    # Extract event windows + peaks
    windows = []
    peaks = []
    for idx in event_indices:
        win, peak = extract_event_window(values, idx)
        windows.append(win)
        peaks.append(peak)
    peaks = np.array(peaks)

    # Sort by peak (large=close=0.5m, small=far=2m)
    order = np.argsort(peaks)[::-1]

    # Assign distance based on layout
    distance_labels = []
    cursor = 0
    for distance, n in test['layout']:
        for _ in range(n):
            distance_labels.append(distance)
        cursor += n
    # distance_labels has same length as event_indices, sorted by peak

    # If split_1_5m: re-label the 1.5m group's top 3 as "1.5m_unblocked", bottom 3 as "1.5m_blocked"
    if test.get('split_1_5m'):
        # Find indices in peak-sorted order that are at 1.5m
        idx_15m = [i for i, d in enumerate(distance_labels) if d == 1.5]
        # Top 3 (already at front of 1.5m group due to peak-sort) = unblocked
        for j, i in enumerate(idx_15m):
            if j < 3:
                distance_labels[i] = '1.5m_unblocked'
            else:
                distance_labels[i] = '1.5m_blocked'

    # Run each event through detector
    n_total = len(event_indices)
    for i, (win, peak, dist) in enumerate(zip([windows[k] for k in order],
                                               [peaks[k] for k in order],
                                               distance_labels)):
        pulse_path = tmp_dir / f"{test['tag']}_{i:02d}.csv"
        write_pulse_csv(win, pulse_path)
        # Substitute into the matching synthetic profile
        samples, gt = generate(
            test['substitute_into'],
            seed=2000 + i,
            geometry='medium',
            event_override=str(pulse_path),
        )
        result = run(samples, model=model)
        results.append({
            'csv': Path(test['path']).name,
            'tag': test['tag'],
            'expected_class': test['expected_class'],
            'substitute_into': test['substitute_into'],
            'distance': dist,
            'peak_v': peak,
            'classified_as': result.classified_as,
            'correct': (result.classified_as == 'fall') == (test['expected_class'] == 'fall'),
        })
    print(f'  processed {n_total} events', flush=True)

# Summary
print()
print('=' * 80)
print('SUMMARY — corrected sim-to-real test (v2)')
print('=' * 80)
print(f'{"CSV":<25} {"tag":<6} {"distance":<18} {"n":<4} {"sens/FP":<10} {"correct %":<10}')
print('-' * 80)

by_csv_dist = defaultdict(list)
for r in results:
    key = (r['csv'], r['tag'], str(r['distance']))
    by_csv_dist[key].append(r)

for (csv_name, tag, dist), events in sorted(by_csv_dist.items()):
    n = len(events)
    n_fall = sum(1 for e in events if e['classified_as'] == 'fall')
    if events[0]['expected_class'] == 'fall':
        sens = n_fall / n
        metric = f'{n_fall}/{n} sens'
        pct = sens
    else:
        fp = n_fall / n
        metric = f'{n_fall}/{n} FP'
        pct = 1 - fp  # correctness = 1 - FP
    print(f'{csv_name:<25} {tag:<6} {dist:<18} {n:<4} {metric:<10} {100*pct:<10.0f}')

# Aggregate
print()
print('AGGREGATE:')
fall_events = [r for r in results if r['expected_class'] == 'fall']
confuser_events = [r for r in results if r['expected_class'] == 'confuser']
fall_caught = sum(1 for r in fall_events if r['classified_as'] == 'fall')
fp_count = sum(1 for r in confuser_events if r['classified_as'] == 'fall')
print(f'  Sensitivity (fall surrogates → fall):   {fall_caught}/{len(fall_events)} = {100*fall_caught/len(fall_events):.1f}%')
print(f'  False-positive rate (confusers → fall): {fp_count}/{len(confuser_events)} = {100*fp_count/len(confuser_events):.1f}%')
