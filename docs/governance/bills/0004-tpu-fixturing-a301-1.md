# Bill 0004 — TPU 95A Fixturing Pad for A301-1 Channels (Ch0–Ch4)

**Status:** CONDITIONALLY ENACTED 2026-05-19 (Case 3, see `case_law.md`) —
four binding conditions must be satisfied before calibration data is admitted.
**Branch:** `bill/tpu-fixturing-a301-1`
**Change type:** hardware procedure + software schema (fixturing standard for
A301-1 dead-weight calibration path)
**Traces to:** Article I (Signal First), Article II (Human in the Loop),
Amendments 1, 7; Amendment 9 (PROPOSED — BOM change authorised by Case 3
Justice ruling pending ratification); Case 2 (Bill 0003 dead-weight path, scope
inherited); Case 3 (this Bill's hearing).

---

## Problem

Bill 0003 (Case 2) enacted the dead-weight calibration path for A301-1 channels
Ch0–Ch4. Under that path the OIML M1 mass is placed on the A301-1 sensor
surface to generate the calibration force points. During trial runs, however,
force is not applied directly to the bare sensor — it is applied through a
3D-printed bench-foot geometry that contacts the sensor surface. If the
bench-foot geometry is present at trial time but absent at calibration time, the
transfer function measured at calibration does not describe the sensor's response
at trial.

Amendment 7 (Calibration Discipline) states: "A constant derived from a physical
measurement predicts its own correct value when the operating conditions change.
A tuned constant (fitted to observed data without physical derivation) requires
re-tuning at every hardware or population change." A calibration performed with
one contact geometry applied to a sensor that operates through a different contact
geometry is a tuned constant in the Amendment 7 sense — it does not predict its
own correct value when fixturing changes between calibration and trial.

A TPU 95A 1.0 mm pad placed at the A301-1 contact interface at both calibration
time and trial time establishes fixturing identity: the calibration and trial
stacks are physically identical, making the fitted coefficients (a, b) traceable
to the specific contact geometry deployed in the field.

**Scope:** A301-1 channels Ch0–Ch4 ONLY. Inherits the scope of Bill 0003 / Case 2.

A301-25 channels Ch5–Ch6 (finger-pad sensors) are NOT affected by this Bill.
Their calibration path (MTS, Bill 0002) and fixturing conditions are governed
by separate Bills.

---

## Force-source compatibility

This Bill is additive on top of the Bill 0003 dead-weight path. It does not
alter:
- The force-generation mechanism (OIML M1 dead-weight, F = m · g,
  g = 9.80665 m/s²)
- The acquisition timing (0.5–2.5 s window, 200 samples at 100 Hz)
- The discard threshold (σ > 21 ADC counts)
- The repeats-per-level protocol (3 repeats, full unload between)
- The sensor conditioning protocol (3 full load-unload cycles before data)
- The fit acceptance criteria (RMS ≤ 0.088 N, max ≤ 0.176 N, adj-R² ≥ 0.998)
- The Bill 0002 Part 5 re-fit cadence (30 days, triggers (a)–(e); Case 3 C4
  adds trigger (f) — see below)
- The admissibility binding (Bill 0002 Part 7, all five conditions)

The only physical addition is the TPU 95A 1.0 mm pad in the load path, present
identically at calibration time and trial time.

---

## Enacted clauses

### Clause (a) — Fixturing identity mandate

At both calibration time and trial time, every A301-1 channel (Ch0–Ch4) must
have the TPU 95A 1.0 mm fixturing pad in place at the sensor contact interface.
The pad is interposed between the 3D-printed bench-foot geometry and the A301-1
sensor surface. The calibration stack (weight → rigid backing disc → TPU 95A
1 mm pad → A301-1 sensor) must be physically identical to the trial stack
(bench-foot → TPU 95A 1 mm pad → A301-1 sensor).

### Clause (b) — Pad specification

Each pad must conform to the following specification:

| Parameter | Value |
|---|---|
| Durometer | TPU 95A |
| Nominal thickness | 1.0 mm |
| Acceptable thickness range | 0.8 mm – 1.2 mm (verified with calipers before install) |
| Material / brand | OUVERTURE TPU 95A filament |
| Print infill | 100% |
| Layer-line orientation | Identical across all 5 pads (same print session) |
| Filament lot | Same lot number for all 5 pads |
| Print session | Same session for all 5 pads |
| Bonding / adhesive | None (dry-seated; see TPUPadRecord.bonding_adhesive = "none") |
| Install date | Recorded in TPUPadRecord.install_date |

### Clause (c) — Pre-acquisition sanity check (superseded by Case 3 C1)

See Case 3 Condition C1 (mandatory; described in full in the Conditions section
below). Clause (c) as originally drafted is superseded by C1, which imposes a
stricter protocol: the full deployed stack (A301-1 + TPU 95A 1 mm pad + 200 g
weight) is tested, not just the bare placement transient.

### Clause (d) — TPUPadRecord dataclass

A `TPUPadRecord` dataclass is added to `src/calibration/deadweight.py`
(existing file, created by Bill 0003). No new files are created by this clause.

```python
@dataclass
class TPUPadRecord:
    channel: int               # Ch0–Ch4
    durometer: str             # "95A"
    thickness_mm: float        # measured pre-install (calipers); must be in [0.8, 1.2]
    manufacturer: str          # "OUVERTURE"
    lot_number: str            # filament lot id
    print_session_id: str      # print session identifier (date + operator)
    infill_pct: int            # 100
    layer_orientation: str     # e.g. "0/90" or "45/135" — identical across all 5 pads
    bonding_adhesive: str      # "none"
    install_date: str          # ISO 8601 date (YYYY-MM-DD)
```

The `build_deadweight_calibration_record` function in `deadweight.py` is
extended with a `tpu_pad: TPUPadRecord | None = None` parameter. When
`tpu_pad` is not None, the fixture_stack field is populated in the JSON record.

### Clause (e) — JSON schema additions: fixture_stack field

The Bill 0002 Part 6.2 / Bill 0003 Clause (e) JSON schema is extended with a
new `fixture_stack` object for any channel calibrated under this Bill. No
existing field is removed or modified.

**New field added alongside `dead_weight_record`:**

```json
{
  "fixture_stack": {
    "description": "Physical load path from weight to sensor surface at calibration time",
    "layers_top_to_bottom": [
      "OIML M1 mass (Bill 0003 dead_weight_record)",
      "rigid backing disc — ~2 mm acrylic or aluminium, diameter matching sensor active area",
      "TPU 95A 1.0 mm pad (OUVERTURE, 100% infill)",
      "A301-1 sensor surface"
    ],
    "tpu_pad": {
      "channel": <int>,
      "durometer": "95A",
      "thickness_mm": <float>,
      "manufacturer": "OUVERTURE",
      "lot_number": "<string>",
      "print_session_id": "<string>",
      "infill_pct": 100,
      "layer_orientation": "<string>",
      "bonding_adhesive": "none",
      "install_date": "<YYYY-MM-DD>"
    },
    "backing_disc": {
      "material": "acrylic or aluminium",
      "thickness_mm": "<float>",
      "diameter_mm": "<float>"
    }
  },
  "CURVE_FIT — derived from Contact Force primitive (Amendment 1), dead-weight + TPU pad path (Bills 0003 + 0004)":
    "Physical derivation: F = m · g, g = 9.80665 m/s² (CGPM 1901). Fixturing stack: weight → backing disc → TPU 95A 1 mm OUVERTURE pad → A301-1 sensor surface. Pad installed identically at calibration and trial. Traces to: Amendment 1 primitive 1 (Contact Force), Amendment 7 (Calibration Discipline), Case 3."
}
```

For channels calibrated under Bill 0003 alone (bare-sensor, before Bill 0004
conditions are satisfied), `fixture_stack` is omitted.

### Clause (f) — BOM additions (authorised by Case 3 Justice ruling under Article II)

The following items are added to `docs/device_context.md` BOM. Amendment 9
(Hardware Optimization Transparency) is PROPOSED at this ruling date; the BOM
change is authorised by direct Justice ruling under Article II pending Amendment
9 ratification.

| Item | Qty | Spec | Notes |
|---|---|---|---|
| TPU 95A fixturing pad, 1.0 mm | 5 | OUVERTURE filament, 100% infill, same lot + session | One per A301-1 channel (Ch0–Ch4) |
| Rigid backing disc | 5 | ~2 mm acrylic or aluminium, diameter to match A301-1 active area | Seated between weight and pad |
| Calipers (session tool) | 1 | Resolution ≤ 0.02 mm | For pre-install thickness check and C4 trigger measurement |

---

## Conditions binding on implementation (Case 3, Justice ruling 2026-05-19)

All four conditions must be satisfied and results recorded in
`docs/device_context.md` Signal Measurements before any TPU pad calibration
data is admitted.

### C1 — Pre-acquisition sanity check with TPU pad in place

Before the first calibration point is acquired on any A301-1 channel under this
Bill, run a one-shot placement-transient capture on a single channel with the
full deployed stack:

**Stack:** A301-1 sensor + TPU 95A 1.0 mm pad (seated, no weight) → place
200 g OIML M1 mass on top of backing disc on top of pad.

**Protocol:**
1. 200 frames baseline (no weight; pad seated on sensor, backing disc in place).
2. Place 200 g OIML mass on backing disc.
3. Capture 500 frames post-placement at 100 Hz via `capture.py`.
4. Confirm placement transient decays to within `capture.py` `is_stationary`
   5% creep allowance (line 52) before t = 0.5 s.
5. Record result (frames captured, stationarity verdict, timestamp) in
   `docs/device_context.md` Signal Measurements.

**Pass criterion:** Transient decays within stationarity criterion before
t = 0.5 s.

**Failure action:** Bill 0004 is suspended. A follow-up Bill must be filed
before any TPU-pad calibration data is acquired.

### C2 — Bare-sensor baseline offset measurement

Before any TPU pad calibration data is admitted, the operator runs a
comparative offset measurement on one A301-1 channel to confirm the projected
0.22 N systematic offset actually exists on this hardware.

**Protocol:**
1. Apply a 200 g OIML M1 mass directly to the bare A301-1 sensor surface
   (no pad, no backing disc). Record 200 sample mean raw ADC reading using
   the Bill 0003 acquisition window (0.5–2.5 s, 100 Hz). Call this
   `raw_bare`.
2. Apply the same 200 g mass via the deployed 3D-printed bench-foot geometry
   seated on the bare sensor (no pad; bench-foot directly on sensor). Record
   200 sample mean raw ADC reading. Call this `raw_benchfoot`.
3. Compute delta in ADC counts: `delta_raw = raw_benchfoot - raw_bare`.
4. Convert to Newtons using a preliminary linear approximation:
   `delta_F ≈ delta_raw * applied_N / mean_raw`
   where `applied_N = 1.9613 N` (200 g × 9.80665 m/s²) and
   `mean_raw = (raw_bare + raw_benchfoot) / 2`.
5. Record `raw_bare`, `raw_benchfoot`, `delta_raw`, and `delta_F` in
   `docs/device_context.md` Signal Measurements as:
   "bench-foot vs OIML-mass offset, bare A301-1, Ch<N>"

**Decision threshold:**

| |delta_F| | Action |
|---|---|
| < 0.05 N | Bill 0004 SUSPENDED. The projected fixturing offset does not hold on this hardware. Operator continues with bare-sensor Bill 0003 protocol. |
| >= 0.05 N | Bill 0004 PROCEEDS. The measured delta_F is the empirical justification for fixturing identity. |

The 0.05 N threshold is half the Bill 0002 Part 5.2 zero-load tolerance (0.1 N).

### C3 — Per-pad modulus consistency check

Before any pad is deployed on a channel, all 5 pads must pass a 3-point
loading consistency test to bound 3D-printed TPU anisotropy.

**Requirements:**
- All 5 pads must be printed from the same OUVERTURE filament lot.
- All 5 pads must be printed in the same session, with identical layer-line
  orientation and identical slicer settings (100% infill).

**Protocol:**
1. Select one A301-1 channel as the reference channel for this test.
2. For each of the 5 pads in turn:
   a. Seat the pad on the reference channel sensor surface.
   b. Place the backing disc, then the 200 g OIML mass on the pad.
   c. Record the raw ADC mean over the 0.5–2.5 s window (200 samples at 100 Hz).
   d. Remove weight and pad.
3. Compute:
   - `mean_across_pads = mean of the 5 raw ADC readings`
   - `spread = max(raw_means) - min(raw_means)`
   - `spread_pct = spread / mean_across_pads * 100`

**Pass criterion:** `spread_pct < 5%`.

**Failure action:** Any pad whose reading contributes to a spread exceeding 5%
must be re-printed in a fresh session (same lot, same settings). Alternatively,
the per-pad raw ADC reading is recorded as a known systematic in the JSON
`fixture_stack.tpu_pad.print_session_id` field and a channel-specific offset
correction is documented. Re-printing is preferred.

**Record:** All 5 pad raw ADC readings, computed spread, spread_pct, filament
lot number, and print session ID are recorded in `docs/device_context.md`
Signal Measurements as:
"TPU 95A inter-pad consistency, lot <id>, print session <id>"

### C4 — Polymer compression-set re-calibration trigger

A new trigger is added to the Bill 0002 Part 5.1 mandatory re-calibration
trigger list. This addition is authorised by Case 3 ruling and does NOT violate
Case 1 Condition C2 (which froze Part 5 cadence, not the trigger list). Case 3
explicitly extends Part 5 for the dead-weight + pad path.

**New trigger (f):**

> "(f) Visible deformation or thickness change of any TPU fixturing pad > 0.05 mm
> (5% of nominal 1.0 mm), measured with calipers at session start. Reason:
> polymer compression set under sustained load can exceed 5% in 30 days at room
> temperature, shifting the calibrated artifact's response."

**Implementation:** At the start of each calibration or trial session, the
operator measures each pad's thickness with calipers (resolution ≤ 0.02 mm)
and records the measurement. If any pad shows thickness change > 0.05 mm
relative to its install measurement (recorded in TPUPadRecord.thickness_mm),
that channel's calibration must be re-acquired with the new pad before trial
data is admitted.

---

## TPUPadRecord schema (complete reference)

```python
@dataclass
class TPUPadRecord:
    channel: int               # Ch0–Ch4 (A301-1 only)
    durometer: str             # "95A"
    thickness_mm: float        # measured with calipers before install; in [0.8, 1.2]
    manufacturer: str          # "OUVERTURE"
    lot_number: str            # filament lot identifier (from spool label)
    print_session_id: str      # date + operator, e.g. "20260519_sni22"
    infill_pct: int            # 100 (mandatory)
    layer_orientation: str     # e.g. "0/90" — must be identical for all 5 pads
    bonding_adhesive: str      # "none" (dry-seated)
    install_date: str          # ISO 8601, e.g. "2026-05-19"
```

Validation rules (enforced in `deadweight.py`):
- `durometer` must equal `"95A"`
- `thickness_mm` must be in `[0.8, 1.2]`
- `infill_pct` must equal `100`
- `bonding_adhesive` must equal `"none"`
- `channel` must be in `[0, 1, 2, 3, 4]`

---

## Implementation surface

**Modified file:** `src/calibration/deadweight.py` (created by Bill 0003)
  - Add `TPUPadRecord` dataclass (with validation)
  - Extend `build_deadweight_calibration_record` with
    `tpu_pad: TPUPadRecord | None = None` parameter
  - When `tpu_pad` is not None, populate `fixture_stack` in the JSON record

**Modified file:** `src/calibration/json_writer.py` (or equivalent JSON
serialisation module)
  - Add `fixture_stack` field schema as specified in Clause (e)
  - Ensure `fixture_stack` is omitted (not null) for Bill 0003 bare-sensor
    records

**BOM additions in:** `docs/device_context.md` BOM section (5 TPU pads, 5
backing discs, 1 calipers reference) — recorded under Article II authorisation
by Case 3 Justice ruling.

**No changes to:**
  - `src/calibration/mts.py`
  - `src/calibration/capture.py`
  - `src/calibration/fit.py`
  - `docs/governance/bills/0002-flexiforce-calibration.md`
  - `docs/governance/bills/0003-deadweight-a301-1.md`
  - `docs/toolchain_config.md` Channel & Topic Map (updated post-implementation
    when JSON files with `fixture_stack` field are produced, not during this
    governance recording turn)

Implementation begins on branch `bill/tpu-fixturing-a301-1` after this
governance record is committed.

---

## Constitutional grounding

- **Article I (Signal First):** Every calibration coefficient must trace to a
  first-order physically measurable quantity. Fixturing identity (calibration
  stack = trial stack) is required for the fitted transfer function to remain
  predictive at trial time. The TPU 95A pad establishes this identity.
- **Article II (Human in the Loop):** The 6-row BOM change (5 pads + 5 backing
  discs + calipers reference) is authorised by direct Justice ruling under
  Article II, pending Amendment 9 ratification.
- **Amendment 1 (Domain Primitives, RATIFIED 2026-05-14):** Contact Force is
  Primitive 1. The A301-1 table-foot array is a named evidence source. This Bill
  ensures that the calibration stack at calibration time is identical to the
  contact geometry at trial time, preserving the traceability of Contact Force
  evidence from Ch0–Ch4.
- **Amendment 7 (Calibration Discipline, RATIFIED 2026-05-15 by Case 1):** The
  fixturing identity principle is an application of Amendment 7's core rule —
  calibration constants must predict their own correct value when operating
  conditions change. A constant fitted with one contact geometry does not predict
  its value under a different geometry. The `CURVE_FIT — derived from ...` header
  in the JSON (Clause (e)) records the fixturing stack as part of the physical
  derivation.
- **Amendment 9 (Hardware Optimization Transparency, PROPOSED):** The BOM change
  introduced by this Bill would require Amendment 9 process once ratified. The
  Justice's ruling under Article II authorises the change ahead of ratification
  and designates it as a precedent example for Amendment 9's scope once ratified.
- **Case 1 (2026-05-15):** Established acquisition window (0.5–2.5 s) and
  discard threshold (σ > 21 ADC counts). Both preserved unchanged.
- **Case 2 / Bill 0003 (2026-05-19):** Established the dead-weight force path for
  A301-1 Ch0–Ch4. This Bill is additive on top of that path.
- **Case 3 (2026-05-19):** This Bill's hearing. Conditionally enacted with four
  binding conditions (C1–C4).

---

## Expected outcome

After all four conditions (C1–C4) pass and Ch0–Ch4 are calibrated with the TPU
pad stack:

- A301-1 (Ch0–Ch4): RMS residual target ≤ 0.088 N (2% of 4.4 N FS), as per
  Bill 0002 / Bill 0003.
- Each channel's JSON calibration record contains a `fixture_stack` field with
  full TPU pad metadata (TPUPadRecord), providing traceability from the fitted
  coefficients to the specific physical contact geometry deployed in the
  benchmark.
- Bill 0002 Part 5.2 session-start zero-load check and the C4 caliper check
  together detect polymer compression set before it contaminates trial data.
- A301-25 channels Ch5–Ch6 remain on the MTS path under Bill 0002, unaffected
  by this Bill.
