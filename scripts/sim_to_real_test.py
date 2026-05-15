"""Sim-to-real verification: substitute real cropped events into synthetic
profiles and report detector predictions."""

import sys, csv
sys.path.insert(0, '/home/sni22/crucible/piezo_fall')
from pathlib import Path
from collections import defaultdict
import numpy as np
import tempfile

from src.signals import generate, list_profiles, FS_HZ
from src.algorithm import run, train_classifier


def load_csv_with_events(path):
    values = []
    events = []
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            values.append(float(row['value']))
            events.append(row['event'].strip())
    return np.array(values), np.array(events)


def extract_event_window(values, event_idx, window_samples=500):
    """Extract ±window_samples/2 around the tagged sample."""
    half = window_samples // 2
    start = max(0, event_idx - half)
    end = min(len(values), event_idx + half)
    return values[start:end]


def write_pulse_csv(pulse, path):
    """Write a cropped pulse as a receiver.py-format CSV (sample_index, value, event)."""
    with open(path, 'w') as f:
        f.write('sample_index,value,event\n')
        for i, v in enumerate(pulse):
            f.write(f'{i},{v:.6f},\n')


# Real-data sources to test
TESTS = [
    {
        'csv_path': '/home/sni22/Documents/piezo_circuit/bathroom_testing/step_201505.csv',
        'event_label_in_csv': 'step',
        'real_event_type': 'real_step',
        'substitute_into_profile': 'confuser_step',
        'expected_class': 'confuser',  # walking should NOT be classified as fall
    },
    {
        'csv_path': '/home/sni22/Documents/piezo_circuit/bathroom_testing/catfood_201505.csv',
        'event_label_in_csv': 'fall',  # note: tagged 'fall' but is actually cat-food drop = object
        'real_event_type': 'real_catfood_drop',
        'substitute_into_profile': 'confuser_drop_phone',
        'expected_class': 'confuser',  # object drop should NOT be classified as fall
    },
    {
        'csv_path': '/home/sni22/Documents/piezo_circuit/bathroom_testing/water_201505.csv',
        'event_label_in_csv': 'other',
        'real_event_type': 'real_water_drop',
        'substitute_into_profile': 'noise_flush',  # closest match — water-related transient
        'expected_class': 'noise',
    },
]

print('Sim-to-real verification — training detector first...', flush=True)
model = train_classifier(seeds_per_profile=20, seed_base=1000)
print(f'  trained', flush=True)
print()

results = []
tmp_dir = Path(tempfile.mkdtemp(prefix='piezo_real_pulses_'))
print(f'Cropped pulses saved to: {tmp_dir}')
print()

for test in TESTS:
    print(f'=== {test["real_event_type"]} ===', flush=True)
    print(f'  source: {Path(test["csv_path"]).name}', flush=True)
    print(f'  substituting into: {test["substitute_into_profile"]}', flush=True)
    print(f'  expected class: NOT fall', flush=True)

    values, events = load_csv_with_events(test['csv_path'])
    event_indices = np.where(events == test['event_label_in_csv'])[0]
    print(f'  found {len(event_indices)} tagged events', flush=True)

    n_classified_fall = 0
    for i, idx in enumerate(event_indices):
        pulse = extract_event_window(values, idx, window_samples=500)
        pulse_path = tmp_dir / f"{test['real_event_type']}_{i:02d}.csv"
        write_pulse_csv(pulse, pulse_path)

        # Generate trace with real pulse substituted
        samples, gt = generate(
            test['substitute_into_profile'],
            seed=1234 + i,  # different seed per substitution
            geometry='medium',
            event_override=str(pulse_path),
        )
        result = run(samples, model=model)
        was_fall = (result.classified_as == 'fall')
        if was_fall:
            n_classified_fall += 1
        gate = result.gate_outcome
        # print(f'    event {i}: classified={result.classified_as} ({gate})')

    fp_rate = n_classified_fall / len(event_indices) if event_indices.size > 0 else 0
    print(f'  → {n_classified_fall}/{len(event_indices)} classified as fall ({100*fp_rate:.1f}%)', flush=True)
    print()
    results.append({
        'test': test['real_event_type'],
        'n_events': len(event_indices),
        'n_fall_class': n_classified_fall,
        'fp_rate': fp_rate,
    })

print()
print('=' * 60)
print('SIM-TO-REAL FP SUMMARY')
print('=' * 60)
print(f'{"real event type":<25} {"n events":<10} {"fall-classified":<16} {"FP %":<10}')
print('-' * 60)
for r in results:
    print(f'{r["test"]:<25} {r["n_events"]:<10} {r["n_fall_class"]:<16} {100*r["fp_rate"]:<10.1f}')
