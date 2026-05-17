# Real-to-Sim Correction Data Collection Protocol

**Status:** Draft 2026-05-16. Each recording session requires Article II
human approval to execute; this document is the plan, not authorization.

---

## Purpose

Stage 1 baseline (`docs/stage_1_baseline.md`) leaves the simulator-only
classifier at **50% sensitivity / 44% FP** on real bathroom CSVs.
Further simulator tweaking without real data hits diminishing returns
(also documented in the baseline). To close the gap, every simulator
component needs to be **fit against real ground truth**.

This protocol specifies what real measurements to collect, in what
order, and exactly which simulator parameter each measurement corrects.

The "tap test" is one piece of this (the IR-fitting piece); the full
plan covers tap + walk + drop + fall-surrogate + noise so a single
bathroom deployment captures everything needed.

---

## Real-to-sim correction map

This is the single most important table in this document. Each row is
a measurement type, what simulator component it fits, and the residual
that quantifies success.

| Measurement | Simulator component it fits | Fit method | Acceptance residual |
|---|---|---|---|
| **Tap IR at 3 distances** | `signals.py` floor-plate FEA (`floor_sim` damping ζ_plate, modal density, spatial decay coefficient `REAL_TO_SIM_SCALE`) + sensor-model end-to-end gain | Compare measured tap IR (envelope + spectrum) to simulated tap IR at same distance; minimize log-spectral distance + ringdown-tau residual | Per-tap envelope correlation ≥ 0.85; ringdown τ within ±30% |
| **Quiet baseline (60 s)** | `signals.py` `bg_environmental_noise` ASD (peaks + 1/f + white) — already done once, redo per bathroom | Compute Welch PSD of real baseline, overwrite per-peak amplitudes in noise model | Real PSD vs sim PSD within ±6 dB across 1–500 Hz |
| **Calibration walk (60 s)** | `signals.py` `_footstep_force_profile` (peak force range, contact time) | Match measured per-step peak amplitude distribution and footstep cadence distribution | Peak amplitude mean within ±20%; cadence distribution KS-test p > 0.05 |
| **Object drops × {phone, glass, water-bottle} × 3 distances** | `signals.py` `drop_trajectory` (`rebound_pattern` parameters: COR, multi-impact spacing) | Match measured multi-peak count, inter-peak interval, decay envelope | Multi-peak count match ±1; decay envelope correlation ≥ 0.80 |
| **Catfood-bag drops × 3 distances × {body-in-path, no-body}** | `signals.py` `fall_trajectory` `body_absorption_db` (currently 5 dB, weakly validated) | Compare amplitude ratio (body-in-path vs not) to current 5 dB assumption | Amplitude ratio within ±2 dB of measurement |
| **Slow-slump surrogate (heavy bag lowered onto floor)** | `signals.py` `fall_slump` profile (slow-rumble onset + final impact two-stage signature) | Match measured pre-impact slow build + impact decay shape | Two-stage signature visually matches in plot review (qualitative for now) |
| **Confuser noise (shower, vent, flush, washer if present)** | `signals.py` noise-profile amplitudes for `noise_shower`, `noise_vent`, etc. | Match per-source PSD against current noise-profile amplitudes | Per-source PSD within ±6 dB across 1–500 Hz |

After each fit, the **acceptance test for the corrected simulator** is
sim-to-real v3: rerun `scripts/sim_to_real_test_v2.py` on the held-out
events from the *same* bathroom and confirm:
- Sensitivity ≥ 80% (up from 50%)
- FP rate ≤ 10% (down from 44%)

Hitting these on the training bathroom is the **trigger for the 1-bathroom
→ 3-bathroom expand decision** (see Scope below).

---

## Scope: 1 bathroom now, explicit 3-bathroom trigger

Per 2026-05-16 user decision: collect the full protocol on **1 bathroom
first** before deciding whether to expand. This validates the protocol
itself before front-loading multi-bathroom logistics.

**Trigger to expand to 3 bathrooms:**

Expand if **any** of the following is true after corrected simulator
is tested on the 1-bathroom data:

1. **Sim-to-real v3 hits the 80%/10% target on the training bathroom**
   → the correction worked on this bathroom; need 2 more bathrooms to
   prove it generalizes (otherwise we may have just over-fit to one tile)
2. **Sim-to-real v3 fails by a *small* margin** (e.g., 70%/15%) → the
   simulator structure looks OK but more data is needed; collect 2 more
   bathrooms with the same protocol
3. **Tap-test repeatability is poor on a single bathroom** (per-tap
   envelope correlation < 0.7 across 5 repeats at the same distance) →
   sensor mount or tile-coupling is inconsistent; expand to characterize
   variance source before drawing conclusions

**Stay at 1 bathroom only if:**

- Sim-to-real v3 fails by a *large* margin (e.g., < 60%/> 25%) — extra
  data won't fix a structurally wrong simulator; instead, draft Bills to
  revise the simulator's structural assumptions (e.g., add multi-tile
  mosaic modeling, revisit FEA mode selection)

The trigger is recorded here so the decision is pre-committed and not
post-rationalized.

---

## Hardware setup

- **Device under test:** STM32F103C8T6 + MiniSense 100 in the
  ground_cantilever_housing (CAD: `~/Documents/piezo_circuit/`)
- **Preload:** ~200 g weight on top platform (loose, not bonded)
- **Firmware:** active build at `~/Documents/piezo_circuit/代码 - 调节发送频率/USER/main.c`
  with **INT_MARK = 0** (mandatory — satisfies Amendment 1 P1 ≥ 1 kHz
  rate floor per Case 1+2)
- **Transport:** USART2 (PA2/PA3, 115200 baud, FireWater ASCII `%.3f\n`),
  via USB-serial adapter
- **Logging host:** laptop / Pi recording USART2 stream → CSV

**Sample-rate check before any recording:** capture 10 s of USART2
output, compute measured_rate_hz = lines / wall-clock-elapsed. Must be
≥ 1000 Hz. If less, abort — INT_MARK is wrong, transport is buffering,
or the firmware build is the wrong one.

**Mandatory CSV metadata header** (per Case 1 ruling, missing →
not admissible as Article I evidence):

```
# int_mark: 0
# transport: USART2_USB
# measured_rate_hz: 1380
# bathroom_id: bathroom_A
# tile_size_mm: 200x200
# device_xy_in_room: "0.3m from west wall, 0.5m from south wall"
# preload_mass_g: 200
# operator: shiyao
# date: 2026-05-XX
# session_id: 001
# measurement_type: tap_0.5m  # or baseline / walk / drop_phone_1.5m / etc.
```

---

## Pre-session mount sanity check (~1 min, every session)

Catches a bad deploy before wasting 30+ minutes on data that's
contaminated by a compliant contact.

1. Place housing on tile. Confirm baseplate flush, no rocking when
   pushing the cap with a finger.
2. Place 200 g weight on top platform.
3. Start USART2 capture.
4. Tap the tile 30 cm from housing with a fingernail. 5 taps, ~2 s apart.
5. Stop capture. Plot or scope:
   - **Pass:** clean impulse, ringdown < 50 ms, no oscillation between taps
   - **Fail:** ringdown > 200 ms (compliant contact), delayed rise (foam
     in path), or large oscillation between taps (loose preload / rocking
     baseplate)

If fail: alcohol-wipe the tile, re-seat the housing, repeat. Don't
proceed to data collection until sanity check passes.

---

## Per-bathroom protocol

### Phase A — Install calibration (~5 min)

Same as `docs/device_context.md` Install-Time Calibration Design.
Produces the per-bathroom calibration reference that the algorithm
will use at deploy time.

| Step | Duration | File | Purpose |
|------|----------|------|---------|
| A1: Quiet baseline | 60 s, no one in room | `<bathroom_id>_baseline.csv` | Noise PSD reference; SNR denominator |
| A2: Tap at 0.5 m | 5 taps, ~2 s apart | `<bathroom_id>_tap_0.5m.csv` | IR at near distance |
| A3: Tap at 1.5 m | 5 taps | `<bathroom_id>_tap_1.5m.csv` | IR at mid distance |
| A4: Tap at 2.5 m | 5 taps | `<bathroom_id>_tap_2.5m.csv` | IR at far distance |
| A5: Calibration walk | 60 s normal walking | `<bathroom_id>_walk.csv` | Footstep amplitude reference |

Mark tap locations with tape so they're repeatable for re-installs.

### Phase B — Sim-correction data (15–30 min)

Each event in this phase is **labeled in a separate paper / phone log**
with timestamp, class, distance, and any anomaly (bounce off wall, wet
floor, etc.).

| Event class | Count target | Distances | Notes |
|-------------|--------------|-----------|-------|
| Object drop — water bottle | 15 | 0.5 / 1.5 / 2.5 m × 5 each | Rigid, single-impact-with-rebound class. Drops from waist height (~1 m). |
| Object drop — phone | 10 | 0.5 / 1.5 / 2.5 m × ~3 each | Lower-mass rigid object. Same drop height. |
| Object drop — glass | 10 | 0.5 / 1.5 / 2.5 m | Brittle / multi-impact class. Drops from waist height. Be careful. |
| Catfood-bag drop (body-fall surrogate) | 30 | 0.5 / 1.5 / 2.5 m × 10 each | At 1.5 m, split 5 with operator between drop and sensor ("body in path") and 5 without |
| Slow-slump surrogate | 10 | 0.5 / 1.5 / 2.5 m | Heavy bag (~10 kg) lowered slowly onto floor; controlled descent, not free fall |
| Step / walk (extra, beyond A5) | continuous 5 min | n/a | Operator walks varied paths; oversample for cadence statistics |
| Confuser — shower running | 60 s | n/a | Continuous, separately recorded |
| Confuser — vent on | 60 s | n/a | Continuous |
| Confuser — toilet flush | 5 flushes | n/a | One file with 5 distinct flushes |
| Confuser — washer (if present) | 60 s + a spin-up | n/a | Skip if not in/adjacent to bathroom |

Save Phase B events grouped by class:
```
<bathroom_id>_drop_water_<date>.csv      # all water drops in one file
<bathroom_id>_drop_phone_<date>.csv
<bathroom_id>_drop_glass_<date>.csv
<bathroom_id>_fall_catfood_<date>.csv
<bathroom_id>_fall_slump_<date>.csv
<bathroom_id>_walk_extra_<date>.csv
<bathroom_id>_noise_shower_<date>.csv
<bathroom_id>_noise_vent_<date>.csv
<bathroom_id>_noise_flush_<date>.csv
<bathroom_id>_noise_washer_<date>.csv
```

### Logging discipline

For every event in Phase B:
- Note timestamp (CSV records its own; phone log records wall clock for
  cross-reference)
- Event class label
- Distance from sensor (m)
- Body-in-path? (yes/no) — relevant for catfood-bag drops at 1.5 m
- Surface state (wet/dry)
- Any anomaly

A handwritten or phone-notes log with timestamps is sufficient. Goal:
ability to retro-label each event in the CSV during post-processing.

---

## Output layout

Per bathroom:
```
data/<bathroom_id>/
├── <bathroom_id>_baseline_<date>.csv      # Phase A1
├── <bathroom_id>_tap_0.5m_<date>.csv      # Phase A2
├── <bathroom_id>_tap_1.5m_<date>.csv      # Phase A3
├── <bathroom_id>_tap_2.5m_<date>.csv      # Phase A4
├── <bathroom_id>_walk_<date>.csv          # Phase A5
├── <bathroom_id>_drop_water_<date>.csv    # Phase B
├── <bathroom_id>_drop_phone_<date>.csv
├── <bathroom_id>_drop_glass_<date>.csv
├── <bathroom_id>_fall_catfood_<date>.csv
├── <bathroom_id>_fall_slump_<date>.csv
├── <bathroom_id>_walk_extra_<date>.csv
├── <bathroom_id>_noise_shower_<date>.csv
├── <bathroom_id>_noise_vent_<date>.csv
├── <bathroom_id>_noise_flush_<date>.csv
├── <bathroom_id>_noise_washer_<date>.csv  # if applicable
└── <bathroom_id>_log.md                    # human label log
```

Storage: the CSVs are likely large (kHz × minutes × float). Recommend
`data/` outside the repo with a symlink, and `data/` in `.gitignore`,
unless individual files stay under ~5 MB.

The existing CSVs in `~/Documents/piezo_circuit/bathroom_testing/`
(catfood_201505, water_201505, step_201505) should be migrated under
`data/bathroom_legacy/` with metadata headers retro-fitted (operator
best-effort: int_mark and measured_rate_hz are the load-bearing fields).

---

## How each measurement updates the simulator

This is the "what changes in `src/signals.py`" half of the loop. After
data is collected, draft a single **Bill** ("Sim-to-real v3 corrections
from bathroom_A data") covering all simulator parameter changes derived
from the data. The Bill goes through the standard Judicial Process — no
silent simulator parameter changes.

| Real measurement | Simulator parameter | Recommended fitting script |
|---|---|---|
| Tap IR per distance | `floor_sim` damping ζ, `REAL_TO_SIM_SCALE` | `scripts/fit_floor_ir.py` (to write) |
| Quiet baseline PSD | `bg_environmental_noise` peak amplitudes | `scripts/fit_noise_psd.py` (extend existing real_noise_spectrum work) |
| Calibration + extra walk | `_footstep_force_profile` peak range, contact time distribution | `scripts/fit_footstep.py` (to write) |
| Object drops (water/phone/glass) | `drop_trajectory` COR + multi-impact spacing per `rebound_pattern` | `scripts/fit_drop_rebound.py` (to write) |
| Catfood drops body-in vs out | `fall_trajectory` `body_absorption_db` (currently 5 dB guess) | `scripts/fit_body_absorption.py` (to write) |
| Confuser noise | `noise_shower` / `noise_vent` / `noise_flush` amplitudes | `scripts/fit_confuser_noise.py` (to write) |

These fit scripts don't exist yet — they get drafted as part of the
Bill execution, not preemptively. Listed here so the data-collection
plan and the analysis plan are visible together.

---

## Open questions before first execution

1. **Tap source standardization:** finger-nail tap is operator-dependent
   (amplitude varies ±50%). For better repeatability, recommend a
   **calibrated drop** — e.g., a 10 g steel ball dropped from a fixed
   100 mm height through a vertical guide. Build a simple jig before
   Phase A2–A4. (Optional refinement; finger taps are usable for an
   initial pass to validate the protocol.)
2. **Sample-rate measurement:** one-shot 10 s capture per session, or
   inline timestamp in CSV header? Recommend: inline, record session
   wall-clock start and CSV row count, derive rate post-hoc.
3. **Storage path:** `data/` symlinked outside repo with `.gitignore`,
   or in-repo if CSVs stay small? Recommend: symlinked, decide once we
   see actual file sizes.
4. **Legacy CSV admission:** retro-fitted metadata is operator-attested
   not measured. Acceptable for Phase B comparison but flag the
   asymmetry in any v3 report.
5. **Sample-event-segmentation tool:** Phase B produces hour-long CSVs
   with discrete events. Need a tool (script or simple GUI) to mark
   event windows from the log file. Build alongside Phase B execution.
