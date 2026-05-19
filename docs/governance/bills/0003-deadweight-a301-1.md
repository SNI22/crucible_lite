# Bill 0003 — Dead-Weight Calibration for A301-1 Channels (Ch0–Ch4)

**Status:** ENACTED 2026-05-19 (Case 2, see `case_law.md`) — amended at ruling,
substantially narrower than as-drafted.
**Branch:** `bill/deadweight-calibration-a301-1`
**Change type:** software + hardware procedure (alternative force-source path)
**Traces to:** Article I (Signal First), Amendments 1, 2, 7; Case 1 (partial
reversal of Bill 0002 Part 3 prohibition on alternative force rigs, scoped to
A301-1 only); Case 2 (this Bill's hearing).

---

## Problem

Bill 0002 Part 3 states: *"No alternative force-generation rig is admissible."*
Case 1 Condition C1 deferred confirmation of MTS ramp-rate capability as a
pre-condition for calibration but did not address the scenario where MTS access
remains unresolved indefinitely. With MTS access unconfirmed, Ch0–Ch4 (A301-1,
table-foot contact-force array) remain tagged INADMISSIBLE under Bill 0002 Part 7.

This blocks benchmark metrics 3, 4, and 5 — all tracing to Contact Force under
Amendment 1 — and prevents Stage 0 close under Amendment 2. OIML-traceable
dead-weight loading produces force uncertainty four orders of magnitude below the
A301-1 acceptance criterion and is therefore a metrologically adequate substitute
for the A301-1 force range (FS 4.4 N). This Bill creates the alternative path.

**Scope:** A301-1 channels Ch0–Ch4 ONLY.

A301-25 channels Ch5–Ch6 (FS 110 N, finger-pad sensors) are NOT covered by this
Bill. Their calibration requires MTS ramp rates ≥ 220 N/s, which dead-weight
loading cannot physically replicate at the required timescale. Ch5–Ch6 calibration
remains deferred under Bill 0002 unchanged until MTS access is confirmed.

---

## Constitutional reversal

Case 2 (2026-05-19) reversed Bill 0002 Part 3's prohibition on alternative
force-generation rigs **for A301-1 scope only**. The MTS path under Bill 0002
remains primary; dead-weight is an alternative first-pass path for Ch0–Ch4
exclusively. Bill 0002 itself is not modified.

---

## Enacted protocol (4 active clauses)

### Clause (a) — Force Source: Dead-Weight Loading (A301-1, Ch0–Ch4)

Dead-weight loading is admissible as an alternative force source for first-pass
calibration of A301-1 channels Ch0–Ch4.

- **Primary path:** MTS calibration per Bill 0002 Part 3 remains the preferred
  path. If MTS access becomes available, MTS recalibration of A301-1 channels
  is recommended but not mandatory within any fixed recalibration window.
- **Alternative path (this Bill):** OIML M1 or better calibrated masses placed
  directly on the A301-1 sensor surface generate the calibration force points.
  Force is computed from `deadweight_force_N(mass_kg)` using CGPM standard
  gravity (g = 9.80665 m/s²).
- **A301-25 channels Ch5–Ch6:** NOT covered. MTS path per Bill 0002 unchanged.

### Clause (d) — New Module: `src/calibration/deadweight.py`

A new source file `src/calibration/deadweight.py` shall be created on branch
`bill/deadweight-calibration-a301-1`. It contains:

```python
@dataclass
class DeadWeightRecord:
    mass_kg: float
    oiml_class: str          # e.g. "M1"
    certificate_id: str
    traceable_to: str        # e.g. "NRC Canada mass standard"

CGPM_GRAVITY_M_PER_S2 = 9.80665  # CGPM standard gravity, 1901

def deadweight_force_N(mass_kg: float) -> float:
    """
    FORCE — derived from Contact Force primitive (Amendment 1).
    Physical derivation: F = m · g, g = 9.80665 m/s² (CGPM 1901 standard gravity).
    Value: mass_kg · 9.80665 [N].
    Traces to: Amendment 1 primitive 1 (Contact Force), Amendment 7 (Calibration
    Discipline).
    """
    return mass_kg * CGPM_GRAVITY_M_PER_S2
```

The module also provides a coordination wrapper that calls the existing
`capture.py` / `fit.py` modules. No changes to `mts.py` are made or permitted
by this Bill. Implementation is on branch `bill/deadweight-calibration-a301-1`
after this governance record is committed.

### Clause (e) — JSON Schema Additions

The Bill 0002 Part 6.2 JSON schema is extended with the following fields for
any channel calibrated under this Bill. These fields are added to the existing
schema; no existing field is removed or modified.

**New fields:**

```json
{
  "force_source": "dead_weight",
  "dead_weight_record": {
    "mass_kg": <float>,
    "oiml_class": "M1",
    "certificate_id": "<string>",
    "traceable_to": "<national standard authority>",
    "g_m_per_s2": 9.80665
  },
  "CURVE_FIT — derived from Contact Force primitive (Amendment 1), dead-weight path (Bill 0003)":
    "Physical derivation: F = m · g, g = 9.80665 m/s² (CGPM 1901). Mass uncertainty for OIML M1 at 0.5 kg is ≤ 0.025 g → force uncertainty ≤ 0.00025 N. Curve fit: F(raw) = a · raw^b; fit in log-log space via OLS. Value: a = <float> N·ADC^-b, b = <float> dimensionless. Traces to: Amendment 1 primitive 1 (Contact Force), Amendment 7 (Calibration Discipline)."
}
```

For channels calibrated via MTS (Bill 0002 original path), `force_source` is
`"mts"` and `dead_weight_record` is omitted. For channels calibrated under this
Bill, `force_source` is `"dead_weight"` and `mts_used` (from Bill 0002 schema)
is `false`.

---

## Force source specification

### Physical basis

F = m · g where g = 9.80665 m/s² (CGPM standard gravity, adopted 1901).

OIML M1 mass uncertainty at 0.5 kg is ≤ 0.025 g, giving a force uncertainty
of ≤ 0.00025 N. The A301-1 Part 4 acceptance criterion is RMS residual
≤ 0.088 N (2% of 4.4 N FS). The dead-weight force uncertainty is therefore
four orders of magnitude below the acceptance criterion. Dead-weight loading
introduces no measurable force uncertainty at this sensor's full scale.

### Weight set

Use OIML M1 or better calibrated masses in the following nominal values,
singly and stacked:

| Nominal mass | OIML M1 max error | Derived force |
|---|---|---|
| 50 g | ≤ 3 mg | 0.490 N |
| 100 g | ≤ 5 mg | 0.981 N |
| 150 g (50+100) | ≤ 8 mg | 1.471 N |
| 200 g (2×100) | ≤ 10 mg | 1.961 N |
| 250 g (50+200) | ≤ 13 mg | 2.452 N |
| 300 g (100+200) | ≤ 15 mg | 2.942 N |
| 350 g (50+100+200) | ≤ 18 mg | 3.432 N |
| 500 g | ≤ 25 mg | 4.903 N |

The 500 g point (4.903 N) slightly exceeds the Bill 0002 calibration upper
bound of 4.18 N but is below FS (4.4 N). The operator may clip to 4.4 N FS or
omit this point at discretion; the decision is recorded in the JSON
`calibration_notes` field.

Eight calibration points are the target, matching Bill 0002 Part 3.1's
log-spaced sweep count.

### OIML traceability requirement (Case 2 C3)

Each weight must carry:
- OIML M1 or better classification
- Current certificate number
- Traceability statement citing the national standard authority (e.g., NRC
  Canada, NIST USA)

This metadata is recorded in the `dead_weight_record` block of the JSON
calibration header per Clause (e) above.

---

## Acquisition protocol

The acquisition protocol is **unchanged from Bill 0002 Part 3.2–3.7** in its
entirety. The only change is the force-generation mechanism (dead-weight instead
of MTS). All timing, window, and threshold parameters are retained.

### Timing (Bill 0002 Part 3.2, unchanged)

- Place weight on sensor surface before t = 0.
- DAQ sampling begins at **t = 0.5 s post-placement**.
- t = 0 is resolved from the DAQ-stream onset detector in `capture.py`
  (not from operator placement timing).

### Sample window and discard rule (Bill 0002 Part 3.3, unchanged)

- **200 samples (2 s at 100 Hz, window 0.5–2.5 s post-load)**.
- Mean of 200 samples is the raw value for the calibration point.
- Standard deviation recorded in JSON.
- Discard threshold: **σ > 21 ADC counts** (= 15 × √2). Discarded levels
  re-acquired.

### Repeats per level (Bill 0002 Part 3.4, unchanged)

3 independent acquisitions per level, with full unload between (weight removed,
5 s settle, weight replaced). Three repeat means averaged → one (raw, F) point.

### Sensor conditioning (Bill 0002 Part 3.6, unchanged)

Before any calibration data, 3 full load-unload cycles to FS (use 500 g weight),
30 s hold at FS, unload. Reduces first-cycle creep hysteresis.

---

## Fit acceptance criteria (Bill 0002 Part 4, unchanged)

A301-1 (FS = 4.4 N):
- RMS residual ≤ 0.088 N (2% of FS)
- max |residual| ≤ 0.176 N (4% of FS)
- log-log adjusted R² ≥ 0.998

Fits failing any criterion are re-acquired, not re-fit with looser bounds.

---

## Pre-acquisition sanity check (Case 2 C1 — mandatory before first calibration point)

Before the first calibration point is acquired on any channel under this Bill,
the operator runs a one-shot placement-transient capture:

1. 200 frames baseline (no weight on sensor).
2. Place a mid-range weight (e.g., 200 g) on the sensor surface.
3. 500 frames post-placement captured by `capture.py`.
4. Confirm that the placement transient decays to within the within-window
   stationarity criterion — `capture.py` `is_stationary` with 5% creep
   allowance — before t = 0.5 s.
5. Record the result (frames captured, stationarity verdict, timestamp) to
   `docs/device_context.md` Signal Measurements table.

**If the sanity check fails** (transient has not decayed by t = 0.5 s):
This Bill is suspended. A follow-up Bill must be filed proposing either:
(i) extension of the acquisition window start beyond 0.5 s, or
(ii) a modified weight-placement procedure that achieves faster settling.
No calibration data may be acquired until the follow-up Bill is enacted.

---

## Re-fit cadence and drift detection (Bill 0002 Part 5, unchanged)

Case 2 Condition C4 explicitly preserves Bill 0002 Part 5 without modification.
The 30-day re-calibration cadence, mandatory re-calibration triggers, session-start
zero-load check, and intra-session re-zero warning apply identically to channels
calibrated under this Bill.

---

## Storage and traceability (Bill 0002 Part 6, extended)

**6.1 Record location:** `docs/calibration/ch<N>_<YYYYMMDD>.json` (same as
Bill 0002).

**6.2 JSON schema:** Bill 0002 Part 6.2 schema, plus the `force_source` and
`dead_weight_record` fields defined in Clause (e) above.

**6.3 Channel & Topic Map update:** On admittance of a channel's fit, update the
Calibration curve column in `docs/toolchain_config.md` to:
`docs/calibration/ch<N>_<YYYYMMDD>.json (admitted YYYY-MM-DD)`
(same procedure as Bill 0002 Part 6.3).

**6.4 Raw CSVs:** Same location as Bill 0002 Part 6.4 (`calibration_raw/` in
the flexiforce_reader repo). JSON cites the raw CSV filename.

---

## Admissibility binding (Bill 0002 Part 7, unchanged)

A `daq_sample` reading on channel N is admissible Article-I evidence for the
Contact Force primitive if and only if all five conditions from Bill 0002 Part 7
hold. This Bill does not add or relax any admissibility condition — it
provides an alternative route to satisfying condition (i) (the JSON calibration
file exists and is committed) by using dead-weight instead of MTS for the
force levels.

---

## Constitutional grounding

- **Article I (Signal First):** Dead-weight force generation derives from
  F = m · g — a first-order physically measurable quantity (mass, standard
  gravity). The mass is OIML M1 certified; g = 9.80665 m/s² is the CGPM
  international standard. The derivation is traceable to physical measurement,
  not to convention or intuition.
- **Amendment 1 (Domain Primitives):** Contact Force is Primitive 1. The
  A301-1 table-foot array is a named evidence source. This Bill makes Ch0–Ch4
  evidence admissible by providing a traceable calibration force path.
- **Amendment 2 (Stage Gate Order):** Stage 0 close requires admissible Contact
  Force evidence. With MTS access unresolved, this Bill is the path to partial
  Stage 0 progress on Ch0–Ch4 without violating Amendment 2's gate sequencing.
- **Amendment 7 (Calibration Discipline, RATIFIED 2026-05-15 by Case 1):** The
  mass-to-force derivation (F = m · g, g = 9.80665 m/s²) is documented in the
  Amendment 7 format in the JSON record header `CURVE_FIT — derived from ...`
  key (Clause (e) of this Bill). The derivation predicts its own correct value
  under any operating condition — it is a physically derived constant, not a
  tuned one.
- **Case 1 (2026-05-15):** Established the 0.5–2.5 s acquisition window and
  21 ADC count discard threshold as physically derived from A301 logarithmic
  creep physics. Both are preserved unchanged by this Bill. Case 1 C1 (MTS
  feasibility) is DEFERRED for A301-1 by Case 2; it REMAINS BLOCKING for
  A301-25.
- **Case 2 (2026-05-19):** This Bill's hearing. Reversed Bill 0002 Part 3's
  prohibition on alternative force rigs for A301-1 scope only. The reversal is
  recorded in Case 2 and in this Bill; Bill 0002 itself is not modified.

---

## Implementation surface

**New file:** `src/calibration/deadweight.py`
  - `DeadWeightRecord` dataclass
  - `deadweight_force_N(mass_kg: float) -> float` (CGPM gravity)
  - Coordination wrapper calling existing `capture.py` and `fit.py`

**No changes to:**
  - `src/calibration/mts.py`
  - `src/calibration/capture.py`
  - `src/calibration/fit.py`
  - `docs/governance/bills/0002-flexiforce-calibration.md`
  - `docs/toolchain_config.md` Channel & Topic Map (updated post-calibration
    when JSON files are produced, not during this governance recording turn)

Implementation begins on branch `bill/deadweight-calibration-a301-1` after
this governance record is committed to `cloth_grasp`.

---

## Expected outcome

After enactment and C1 sanity check passing, and Ch0–Ch4 calibrated:

A301-1 (Ch0–Ch4): RMS residual target ≤ 0.088 N (2% of 4.4 N FS).

Ch0–Ch4 `daq_sample` readings become admissible Article-I evidence for Contact
Force, enabling benchmark metrics 3, 4, and 5 on the table-foot array and
supporting partial Stage 0 close under Amendment 2.

A301-25 (Ch5–Ch6) remain inadmissible pending MTS access confirmation per
Bill 0002. Stage 0 close is partial until Ch5–Ch6 are calibrated.
