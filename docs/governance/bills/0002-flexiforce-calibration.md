# Bill 0002 — FlexiForce DAQ Per-Channel Calibration Protocol

**Status:** ENACTED 2026-05-15 (Case 1, see `case_law.md`) — with Part 3.2 and
3.3 modified per the ruling on Position B.
**Branch:** `bill/flexiforce-calibration-protocol`
**Change type:** software + hardware procedure
**Traces to:** Article I (Signal First), Amendments 1, 2; ratifies Amendment 7.

---

## Problem

`docs/toolchain_config.md` records the Calibration curve column for Ch0–Ch6
as "TBD — Stage 0 fit" and states explicitly: *"A `daq_sample` is not
admissible Article-I evidence until its channels' fits are recorded."* The
vendor single-K formula is documented as NOT used. No alternative conversion
is in force. Every `daq_sample` on Ch0–Ch6 is therefore currently
inadmissible as Contact Force evidence under Article I, blocking Stage 0
close under Amendment 2.

The FlexiForce DAQ stack is the dominant uncertainty source in this benchmark
(saved project context: all other error sources are constrained). The
calibration protocol carries first-order weight on benchmark conclusions.

---

## Enacted protocol (7 parts)

### Part 1 — Curve Form

Per-channel power law, no offset:
```
F(raw) = a · raw^b
```
Fitted in log-log space by OLS: `log F = log a + b · log raw`. Form chosen
because (a) piezoresistive conductance physics predicts sub-linear response
with `F(0) = 0`, (b) two parameters are identifiable from 8 well-distributed
points with 3 degrees of freedom remaining, (c) numerically stable in log-log.

### Part 2 — Per-Channel vs Pooled

Fits are **per-channel**. A301 production units vary by up to ±30% in
conductance within a family. Pooling within a family is permitted only if,
after individual fits, the maximum pairwise residual difference across
same-family channels is < 2% of family full-scale (< 0.088 N for A301-1,
< 2.2 N for A301-25). This pre-condition is not expected to be met; it
documents the criterion by which pooling could be reconsidered.

### Part 3 — Calibration Data Acquisition Protocol

Force-generation source: laboratory **MTS (Mechanical Testing System)**. No
alternative force-generation rig is admissible.

**3.1 Force levels per channel** (log-spaced):
  - A301-1 (Ch0–Ch4, FS 4.4 N): 0.25, 0.44, 0.77, 1.35, 1.76, 2.64, 3.52, 4.18 N
  - A301-25 (Ch5–Ch6, FS 110 N): 6.6, 11, 19, 33, 55, 77, 99, 110 N

**3.2 Per-level acquisition timing** *(modified per Case 1 ruling — Position B prevailed):*
  - MTS ramps rapidly to target force; ramp completion in **≤ 0.5 s**.
  - No dedicated settle wait; DAQ sampling begins at **t = 0.5 s post-load**.
  - Rationale: A301 creep is monotonic and logarithmic in time. The "settled"
    reading at t = 5 s is further from the true applied force than an
    early-window reading. The trial measurement timescale (~1–3 s of applied
    force per trial) is the timescale the calibration must match.

**3.3 Sample window and discard rule** *(modified per Case 1 ruling):*
  - **200 samples (2 s at 100 Hz, window 0.5–2.5 s post-load)**.
  - Mean of these 200 samples is the raw value for that calibration point.
  - Standard deviation recorded in the JSON.
  - Discard threshold: **σ > 21 ADC counts** (= 15 × √2, scaled for the larger
    sample window). Discarded levels are re-acquired.

**3.4 Repeats per level:** 3 independent acquisitions per level, with full
unload between (MTS returns to 0 N, 5 s settle, then re-ramps). Three repeat
means averaged → one (raw, F) point.

**3.5 Inter-level transition:** MTS ramps between levels at 0.5 N/s (slow,
for fixture safety — only the per-level *sampling* ramp is fast per 3.2).
5 s dwell after each inter-level transition before the next acquisition.

**3.6 Sensor conditioning (warm-up):** Before any calibration data, each
sensor receives 3 full load-unload cycles to FS, 30 s hold at FS, unload at
0.5 N/s. Reduces first-cycle creep hysteresis.

**3.7 DAQ state:** Streaming at 100 Hz (host command 0x64). Raw CSV written
to `~/Documents/flexiforce/flexiforce_reader/calibration_raw/ch<N>_<YYYYMMDD>_raw.csv`.
Post-processing computes the fit.

**MTS feasibility precondition (Case 1 Condition C1):** Part 3.2 requires
MTS ramp rate ≥ ~10 N/s for A301-1, ≥ ~220 N/s for A301-25. The calibration
session may not proceed until this capability is confirmed on the specific
lab MTS unit. If unmet, Part 3 is suspended pending a follow-up Bill.

### Part 4 — Fit Acceptance Criteria (in Newtons)

A301-1 (FS = 4.4 N):
  - RMS residual ≤ 0.088 N (2% of FS)
  - max |residual| ≤ 0.176 N (4% of FS)
  - log-log adjusted R² ≥ 0.998

A301-25 (FS = 110 N):
  - RMS residual ≤ 2.2 N (2% of FS)
  - max |residual| ≤ 4.4 N (4% of FS)
  - log-log adjusted R² ≥ 0.998

Fits failing any criterion are re-acquired (not re-fit with looser bounds).

### Part 5 — Re-Fit Cadence and Drift Detection

**5.1 Mandatory re-calibration triggers** (any one):
  (a) Channel re-wiring or sensor swap.
  (b) Lab ambient leaves 18–28 °C for any session.
  (c) 30 days since last admitted fit on the channel.
  (d) Session-start zero-load check fails (see 5.2).
  (e) Researcher discretion on observed anomaly.

**5.2 Session-start zero-load check:** Before every trial session, with the
bench carrying only its dead weight, 10 s sample → mean raw → converted to
N via fit → compared to `quiescent_load_N` recorded in JSON. Drift tolerance:
≤ 0.10 N (A301-1) or ≤ 2.5 N (A301-25). Failure suspends the session and
logs an anomaly.

**5.3 Intra-session re-zero (warning, not block):** Between trials, 3 s
no-contact window checked against fit's quiescent prediction. Failure flags
the next trial as a re-zero warning for review.

### Part 6 — Storage and Traceability

**6.1 Calibration record location:** `docs/calibration/ch<N>_<YYYYMMDD>.json`
in this repo. One JSON per channel per calibration date.

**6.2 JSON schema (required fields):**
```json
{
  "channel": 0,
  "sensor_model": "A301-1",
  "physical_location": "bench foot 1 (lowest x,y)",
  "calibration_date": "2026-05-15",
  "operator": "<name>",
  "mts_used": true,
  "primitive": "Contact Force",
  "amendment_grounding": "Amendment 1, Amendment 7",
  "CURVE_FIT — derived from Contact Force primitive (Amendment 1)":
    "Physical derivation: piezoresistive conductance F = a · raw^b; fit in log-log space via OLS. Value: a = <float> N·ADC^-b, b = <float> dimensionless. Traces to: Amendment 1 primitive 1 (Contact Force).",
  "a": <float>,
  "b": <float>,
  "full_scale_N": 4.4,
  "quiescent_load_N": <float>,
  "acquisition_window_s": [0.5, 2.5],
  "acceptance": {
    "rms_residual_N": <float>,
    "max_residual_N": <float>,
    "adj_r_squared_loglog": <float>,
    "rms_criterion_N": 0.088,
    "max_criterion_N": 0.176,
    "r_squared_criterion": 0.998,
    "passed": true
  },
  "calibration_points": [
    {"level_index": 0, "applied_N": 0.25, "raw_mean": <int>, "raw_std": <float>, "repeats": 3},
    ...
  ]
}
```

The `CURVE_FIT — derived from ...` key is the project-specific implementation
of Amendment 7's documentation format (adapted from "firmware inline comment"
to "JSON record header field" because this project has no firmware source).

**6.3 Channel & Topic Map update:** On admittance of a channel's fit, update
the Calibration curve column in `docs/toolchain_config.md` to:
  `docs/calibration/ch<N>_<YYYYMMDD>.json (admitted YYYY-MM-DD)`

**6.4 Raw CSVs** live in the `flexiforce_reader` repo (SNI22/flexiforce_reader,
branch `main`) at `calibration_raw/`. JSON in this repo cites the raw CSV
filename for full traceability.

### Part 7 — Admissibility Binding

A `daq_sample` reading on channel N is admissible Article-I evidence for the
Contact Force primitive **iff all five hold**:
  (i)   `docs/calibration/ch<N>_<YYYYMMDD>.json` exists and is committed on
        the `cloth_grasp` branch.
  (ii)  `acceptance.passed` is `true`.
  (iii) `calibration_date` within 30 days of session date, or a re-cal has
        been performed within 30 days.
  (iv)  Session-start zero-load check for channel N passed on session date.
  (v)   `docs/toolchain_config.md` Channel & Topic Map entry for channel N
        points to the specific JSON file (not "TBD").

A `daq_sample` failing any of these is tagged INADMISSIBLE and excluded from
benchmark metric computations.

---

## Constitutional grounding

- **Article I (Signal First):** This protocol is the mechanism by which raw
  ADC codes are traced to Contact Force (N).
- **Amendment 1 (Domain Primitives):** Contact Force is Primitive 1; the A301
  array is the named evidence source. This Bill makes that evidence admissible.
- **Amendment 2 (Stage Gate Order):** Stage 0 close requires admissible
  Contact Force evidence; this Bill unblocks it.
- **Amendment 7 (Calibration Discipline):** Ratified by Case 1 (see
  `case_law.md`). Part 6.2 JSON schema is the project-specific implementation
  of Amendment 7's documentation format.

---

## Expected outcome

After enactment and all 7 channels calibrated:

A301-1 (Ch0–Ch4): RMS residual target ≤ 0.088 N (2% of 4.4 N FS).
A301-25 (Ch5–Ch6): RMS residual target ≤ 2.2 N (2% of 110 N FS).

Every `daq_sample` on Ch0–Ch6 becomes admissible Article-I evidence for
Contact Force, unblocking benchmark metrics 3, 4, 5 and enabling Stage 0
close under Amendment 2.
