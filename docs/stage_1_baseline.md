# Stage 1 Baseline — Final Sim-to-Real Result (2026-05-16)

This document records the Stage 1 simulator + classifier performance baseline
at the end of the simulator-only iteration phase. Stage 1 is HELD HERE pending
real data collection (see `docs/data_collection_protocol.md` when written).

---

## TL;DR

The simulator + RandomForest classifier — trained ONLY on synthetic data — achieves
on real bathroom CSVs (30 events across step / catfood-fall / water-drop classes,
distance-resolved at 0.5 / 1.5 / 2.0 m):

| Metric | Value | Target | Status |
|---|---|---|---|
| Sensitivity (catfood fall surrogates → fall) | **6/12 = 50.0%** | ≥ 95% | FAILS |
| FP rate (steps + water bottle drops → fall) | **8/18 = 44.4%** | ≤ 1/week | FAILS |

This is the honest simulator-only ceiling. Any further improvement requires
real training data, not simulator tweaks.

---

## Per-distance per-class breakdown

| Source | Tag | Real meaning | Distance | n | Result | Correct % |
|---|---|---|---|---|---|---|
| step_201505 | step | walking (NOT-fall) | 0.5 m | 3 | 2/3 wrongly fall | 33% |
| step_201505 | step | walking | 1.5 m | 3 | 1/3 wrongly fall | 67% |
| step_201505 | step | walking | 2.0 m | 3 | 1/3 wrongly fall | 67% |
| water_201505 | other | water-bottle drop (NOT-fall, rigid object confuser) | 0.5 m | 3 | 2/3 wrongly fall | 33% |
| water_201505 | other | water-bottle drop | 1.5 m | 3 | 1/3 wrongly fall | 67% |
| water_201505 | other | water-bottle drop | 2.0 m | 3 | 1/3 wrongly fall | 67% |
| catfood_201505 | fall | body-fall surrogate (catfood bag) | 0.5 m | 3 | 2/3 caught | 67% |
| catfood_201505 | fall | body-fall surrogate | 1.5m_unblocked (human at far side) | 3 | 1/3 caught | 33% |
| catfood_201505 | fall | body-fall surrogate | 1.5m_blocked (human between) | 3 | 1/3 caught | 33% |
| catfood_201505 | fall | body-fall surrogate | 2.0 m | 3 | 2/3 caught | 67% |

## Key observation: amplitude bias

The detector is biased to call CLOSE/HIGH-AMPLITUDE signals "fall" regardless of
class. Close events of any class get flagged ~67% of the time; far events get
flagged ~33% of the time. The new scale-invariant features
(post_pre_rms_ratio, low/high band fractions) helped on synthetic data but
don't dominate on real data with realistic noise + amplitude variation.

## Body absorption test (5 dB body-in-path attenuation)

The catfood 1.5m group had 6 events split into two experimental conditions:
3 "unblocked" (human at the far side from sensor — clear propagation path)
and 3 "blocked" (human between drop point and sensor — body absorbs signal).

Both groups caught at the same rate (1/3 = 33%). With only 3 events per
condition, the noise on this number is too high to validate or reject the
5 dB body-absorption hypothesis (which is implemented in `fall_trajectory`
as `body_absorption_db=5.0` default). Needs ≥ 10 events per condition.

## What this baseline tells us about simulator iteration

The previous validation result was misinterpreted due to wrong tag-to-class
mapping (commit a201022, 2026-05-15). After user clarifications and a
corrected sim-to-real script (`scripts/sim_to_real_test_v2.py`):

- The simulator + sensor + noise pipeline produces reasonable signals
- The classifier trained on synthetic data has an **amplitude bias** that
  doesn't reflect what real falls look like
- Simulator improvements (multi-impact rebound, body absorption,
  cantilever sensor model) reduced the misinterpretation gap but did
  NOT close the actual classifier shortcoming
- The remaining gap requires real training data; further simulator
  tuning yields diminishing returns

---

## State of the simulator at this baseline

`src/signals.py` (v3, commit 893b865 + later) implements:

| Stage | Component | Evidence type |
|---|---|---|
| 1. Backgrounds | vent (60/120/180 Hz tones), shower (broadband), washer (narrow-band), flush (transient) | LITERATURE + HAND-TUNED amplitudes |
| 2. Events | floor_sim FEA plate model (Kirchhoff, 25 modes, 2 geometries) for impacts; analytical slump | PHYSICS + LITERATURE force ranges (Cavanagh & Lafortune, Robinovitch) |
| 2'. Drop rebound | rigid / bouncy / soft_pkg / shatter patterns | LITERATURE (coefficient of restitution) |
| 2''. Body absorption | 5 dB attenuation on fall_trajectory impacts | EMPIRICAL (catfood drop-human-sensor data, n=3, weak validation) |
| 3. Sensor model | MiniSense 100 cantilever (75 Hz, ζ=0.092) + bias HP (6.5 Hz) | DATASHEET-VERIFIED |
| 4. Noise floor | Real bathroom spectrum (1/f + white + peaks at 25/60/91/120/183 Hz) | EMPIRICAL from bathroom_testing/step_201505.csv |

## State of the classifier

`src/algorithm.py` (commit bda4652 + later) — RandomForest with 13 features:
- 6 per-event physical: peak_amp, total_energy, duration_above_noise_ms,
  spectral_centroid_hz, decay_tau_ms, multi_peak_count
- 5 scale-invariant (added 2026-05-16): pre_event_rms, post_event_rms,
  post_pre_rms_ratio, low_band_energy_frac, high_band_energy_frac
- 2 temporal context: events_in_last_5s, time_since_last_event_s

Trained on 20 seeds × 13 profiles × 2 geometries (small + medium bathroom) =
~1067 events. Tested in v1 on 100 synthetic seeds × 13 profiles × 2 geometries
(89.6% sens, 4.1% FP on synthetic). Tested in v2 on 30 real events across 3
CSVs (50% sens, 44% FP — this baseline).

## 14-profile catalog

| Class | Profile | Notes |
|---|---|---|
| noise (5) | noise_vent, noise_shower, noise_flush, noise_washer_local, noise_washer_neighbor | continuous backgrounds, no events |
| confuser (5) | confuser_step, confuser_drop_phone, confuser_drop_heavy, confuser_drop_glass, walk_in_out | events that aren't falls |
| fall (4) | fall_fast, fall_slump, fall_after_walk, fall_softbody_surrogate | fall events (with -5 dB body absorption) |

## Open simulator gaps (will only be closed with real data)

1. **Amplitude bias in classifier** — features need redesign or real data to overcome
2. **Body-absorption value (5 dB) is a guess** — needs ≥ 10 events per condition to validate
3. **Multi-tile mosaic floor not modeled** — defer to install-time calibration (per generalization strategy in `docs/device_context.md`)
4. **Sensor identity assumption unverified** — task #31 (user visual inspection)
5. **Plate damping / geometry** — defer to install-time calibration (tap test)
6. **Real fall human data unavailable** — surrogates only (catfood bag is closest)

## What needs to happen before Stage 2

Per `docs/device_context.md` Install-Time Calibration Design section:

1. Collect real bathroom recordings with metadata per Case 1 ruling (int_mark,
   transport, measured_rate_hz) from multiple bathrooms (≥ 3 recommended)
2. Add real events to training data alongside synthetic
3. Build install-time calibration scripts (tap test + baseline + walk)
4. Verify deployed sensor identity (task #31)
5. Verify firmware streaming rate (Bill 002 ratified ≥ 1 kHz; INT_MARK=0
   required in deployment)

---

## Files and commits at baseline

- `src/signals.py` — simulator (FEA + sensor + noise + 14 profiles)
- `src/algorithm.py` — RandomForest classifier (13 features)
- `scripts/sim_to_real_test_v2.py` — corrected sim-to-real test
- `docs/governance/amendments.md` — A1 P1 at ≥ 1 kHz (Case 1+2)
- `docs/governance/case_law.md` — Case 1 (Bill 001) + Case 2 (Bill 002)
- `docs/governance/bills/` — Bill 001 (enacted, modified) + Bill 002 (enacted)
- `docs/plots/sim_layout_diagram.png` — sensor + event-zone visualization
- `docs/plots/sensor_model_bode.png` — sensor TF vs datasheet verification
- `docs/plots/real_noise_spectrum.png` — empirical noise basis
- `docs/plots/sim_render/` — 26 per-profile signal renderings
- `docs/plots/real_vs_synth_footstep*.png` — earlier sim-vs-real comparisons

Stage 1 is HELD at this baseline. Resume at Stage 2 only after real data is
collected and added to the training corpus.

---

## Post-baseline finding (2026-05-16): deployed sensor identity confirmed

Task #31 (originally "verify deployed sensor visual inspection", reframed to
"confirm part = MiniSense 100 via BOM/marking") resolved:
**user confirms the deployed sensor is a MiniSense 100**.

Context for future agents who read the source repo and get confused:
the original `~/Documents/piezo_circuit/` repo contains a general-purpose
PVDF front-end designed to work with any PVDF sensor (custom cantilever or
commercial). Its `SENSOR_MOUNTING.md` covers all three configurations
(bare PVDF film, custom PVDF + proof mass cantilever, PZT disc). Its BOM
lists only the conditioning electronics (CA3140 / MAX44248 front-end,
100 MΩ bias resistor R48), not the sensor itself, because the sensor is
modular. None of this contradicts the MiniSense 100 deployment for
piezo_fall — the front-end happens to be compatible with the MiniSense's
output impedance and bias requirement.

### Implications

- Simulator's cantilever model (fn=75 Hz, ζ=0.092, 1.1 V/g baseline,
  6 V/g at resonance, 6.5 Hz HP via 100 MΩ × ~250 pF) remains
  **datasheet-correct** and is the right reference for sim work.
- Action item: add an explicit "Sensor: MiniSense 100 (Measurement
  Specialties)" line to the BOM in `docs/device_context.md` so this
  doesn't have to be re-derived next session.
