# Crucible Case Law

This file records all Judicial Hearing rulings. Entries are written by the prevailing
attorney immediately after the Justice's ruling, before any implementation begins.

Live entries accumulate full argument text. Frozen entries (after stage closeout via
`stage-compactor`) contain only the compact operational record.

---

## Active Precedents

### Case 1: Stage 0 Closure Package — Host-Driven Smoke Tests + FlexiForce Calibration

**Date:** 2026-05-15
**Positions:**
  - A — Enact both Bills (0001 Stage 0 host-driven, 0002 FlexiForce calibration)
    as drafted, with bundled ratification of Amendment 7.
  - B — Calibration Bill's per-level acquisition timing (5 s settle + 1 s sample)
    is the wrong timescale for A301's logarithmic creep. Replace only Part 3.2
    and 3.3: rapid MTS ramp to target (<0.5 s), then 2 s average over the
    0.5–2.5 s post-load window (200 samples). All other Bill elements retained.

**Prevailing position:** B (uncontested — Justice declined to argue Position A
and conceded Position B on the merits).

**Justice's ruling:**
1. Bill 0001 (Stage 0 Host-Driven Smoke Test Suite) is **ENACTED as drafted**.
   No element of Bill 0001 was disputed by Position B.
2. Bill 0002 (FlexiForce DAQ Per-Channel Calibration Protocol) is **ENACTED
   with Part 3.2 and 3.3 modified per Position B**:
   - 3.2 (timing): MTS ramps rapidly to target (≤ 0.5 s); no dedicated settle
     wait; DAQ sampling begins at t = 0.5 s post-load.
   - 3.3 (window): 200 samples (2 s at 100 Hz, window 0.5–2.5 s post-load);
     mean is the raw value for the calibration point; discard threshold
     σ > 21 ADC counts (= 15 × √2).
   - All other Bill 0002 elements (curve form, force levels, repeats, warm-up,
     acceptance criteria, re-fit cadence, JSON schema, admissibility binding)
     retained as drafted.
3. **Amendment 7 (Calibration Discipline) is RATIFIED.** Bill 0002 Part 6.2
   JSON record header (`"CURVE_FIT — derived from ..."`) is the project-specific
   implementation of Amendment 7's documentation format.

**Physical/empirical basis (Benjamin Franklin Principle):**
A301 FlexiForce creep is monotonic and logarithmic in time (~5% per decade of
log time per published characterization of piezoresistive polymer force sensors
of this class). A calibration sampled at t = 5 s of static dwell is ~5%
further from the true applied force than a sample at the geometric centre of
the 0.5–2.5 s window (~t = 1.4 s). Trial force application occurs over ~1–3 s;
matching the calibration timescale to the trial timescale eliminates a
systematic 2.5–5% Contact Force bias that would otherwise propagate
uncharacterized through benchmark metrics 3, 4, and 5. The 200-sample window
also provides a noise floor better by √2 than the original 100-sample
protocol.

**Device outcome protected (Thomas Jefferson Principle):**
The published soft-vs-rigid grasper comparison envelope reflects the physical
Contact Force tolerance of each grasper at the timescale of actual contact,
not a systematic offset from a bench-testing convention. The FlexiForce DAQ
stack — established project context as the dominant uncertainty source — is
calibrated against its operating regime, not against an irrelevant
static-dwell regime.

**Conditions:**
- **C1 — MTS feasibility precondition:** Bill 0002 Part 3.2 requires MTS ramp
  rate ≥ ~10 N/s for A301-1 and ≥ ~220 N/s for A301-25. The calibration
  session may not proceed until this capability is confirmed on the specific
  lab MTS unit. If unmet, Part 3 is suspended pending a follow-up Bill
  proposing either a step-release fixture, an MTS upgrade, or an extension of
  trial pre-pinch dwell to 5 s (each carries different costs).
- **C2 — Part 5 cadence unchanged:** The 30-day re-fit cadence and
  session-start zero-load check remain as drafted. The ~3–4× reduction in
  per-channel acquisition time does not alter any cadence or admissibility
  rule.
- **C3 — H1 FIRST-PASS thresholds remain first-pass:** Bill 0001 H1.3
  (σ ≤ 20 ADC counts) and H1.5 (drift ≤ 10 ADC counts) are first-pass and
  to be re-tightened by a separate Bill once empirical per-channel noise
  data exists from the first MTS calibration session.

**Enacted bills:**
  - `docs/governance/bills/0001-stage0-host-driven.md`
  - `docs/governance/bills/0002-flexiforce-calibration.md`

**Amendment ratified by this case:** Amendment 7 (Calibration Discipline).

**Implementation branches:**
  - `bill/stage0-host-driven` (smoke tests first)
  - `bill/flexiforce-calibration-protocol` (after C1 verified)

**Follow-up action items recorded for the next agent-updater run:** Amendment 7
ratification should propagate to agents whose standing scope cites calibration
(code-reviewer, bill-drafter, hw-advisor, sw-advisor, police).

---

#### Arguments — Position A (not filed)

The Justice declined to argue Position A and conceded Position B on the merits.
No Position A filing exists in the record. The hearing was therefore decided
on Position B's unrebutted physical case.

#### Arguments — Position B (filed by Attorney-B, 2026-05-15)

> Position B accepts the Calibration Bill's curve form, force-level sweep,
> acceptance criteria, JSON storage schema, admissibility binding, re-fit
> cadence, and the bundled ratification of Amendment 7 in full. The single
> contested element is the per-level sampling timing in Part 3: specifically,
> the 5 s post-load settle wait followed by a 1 s sample window. Position B
> replaces only those two timing parameters with a rapid MTS ramp to target
> (under 0.5 s), then a DAQ sample window spanning 0.5–2.5 s post-load
> (200 samples at 100 Hz). The Stage 0 Smoke Test Bill is not disputed at
> all. The rationale is that A301 creep is monotonically logarithmic in
> time, the calibration reading at t = 5 s is therefore further from the
> true applied force than a reading taken in the 0.5–2.5 s window, and the
> trial force-application duration is 1–3 s — the calibration timescale
> must match the measurement timescale or the fitted curve absorbs a
> systematic offset that re-emerges as a bias in every subsequent trial.

**Amendment invoked.** Amendment 1 — Domain Primitives (RATIFIED 2026-05-14,
traces to Article I). Amendment 1 declares Contact Force as the primary
domain primitive for this benchmark. Its "What happens without it" clause
warns: *"Parameters are set by intuition or by fitting to data... the
published benchmark comparison loses physical traceability."* The
calibration timescale is a parameter. It must trace to the physics of the
Contact Force primitive as it is actually measured during trials — not to a
convenience window selected for signal stability.

Amendment 7 (then PROPOSED, ratified by this case) is also invoked: *"A
constant derived from a physical measurement predicts its own correct value
when the operating conditions change. A tuned constant (fitted to observed
data without physical derivation) requires re-tuning at every hardware or
population change."* A calibration curve whose coefficients were fitted at
t = 5 s of static dwell, when applied to readings taken at t = 1–3 s of
dynamic contact, is a tuned constant in the Amendment 7 sense — it does not
predict its own correct value when operating conditions (specifically,
elapsed contact time) change.

Article I directly: every threshold and algorithm decision must trace to a
first-order physically measurable quantity. The sampling window is an
algorithm decision. Its grounding must be the physical behavior of the
Contact Force signal under the A301 sensor during the actual trial timescale
— not a generic "wait for stability" convention from bench-testing practice.

**Precedent.** None. Case law was empty at hearing time.

**Physical outcome protected.** The A301 FlexiForce sensor exhibits
logarithmic creep: under a static applied load, the reported raw ADC count
continues to rise after the load is mechanically settled. Characterization
of piezoresistive polymer sensors of this class shows roughly 5% per decade
of log time in creep magnitude. Applied to the Bill's timing:

- Load reaches target at t = 0 s.
- At t = 0.5 s (lower bound of the Position B window): one half-decade of
  log time has elapsed; creep contribution is approximately 2.5% relative
  to the t = 1 s reference reading.
- At t = 2.5 s (upper bound of the Position B window): the window is
  centered near t = 1.5 s; approximately 3–4% creep accumulated relative
  to t = 0.
- At t = 5 s (Position A settle-end / sample start): a full additional
  half-decade of log time beyond t = 1.5 s has passed; creep is
  approximately 5–6% above the t = 1.5 s value, or approximately 8–9%
  above the t = 0 reading.

The sample window at t = 5–6 s (Position A) therefore captures a raw count
that is approximately 5% higher than the raw count at the geometric center
of Position B's window (t ~ 1.4 s). For a power-law fit `F = a · raw^b`,
this raw offset is absorbed into the coefficient `a`. The fitted curve then
systematically overestimates raw at any given true force — which, when
inverted at trial time, causes the reported trial Contact Force to read
*low* relative to the true applied force at t = 1–3 s of contact.

Position B protects: the fitted curve coefficients represent the sensor's
transfer function at the timescale of actual trial contact (1–3 s),
eliminating a monotonic systematic low-bias in reported Contact Force
values. This directly protects the accuracy of benchmark metrics 3, 4, and
5 (from `docs/device_context.md` Pass/fail threshold: maximum admissible
surface force, peak grasp force, minimum grasp force), all of which trace
to Contact Force under Amendment 1.

On the noise floor: Position A uses a 1 s window at 100 Hz = 100 samples.
Position B uses a 2 s window at 100 Hz = 200 samples. Noise-floor standard
error on each calibration point is lower under Position B by √2 ≈ 1.41.
The "std > 15 ADC counts — discard" criterion in the Bill was written for
100 samples. With 200 samples, the equivalent precision condition is met
at std > 21 ADC counts (15 × √2). The Bill 0002 enacted text uses 21 ADC
counts.

**Consequences of Position A in physical terms.** If Position A prevails,
the per-channel power-law coefficients are fitted to raw values recorded at
t = 5–6 s of static dwell. During trials, A301 sensors experience contact
durations of approximately 1–3 s. The mismatch means every trial force
reading is passed through a curve that was not fitted to the sensor's state
at that timescale.

At trial time t = 1.5 s, the raw count is approximately 5% lower than the
raw count at t = 5.5 s (the calibration point). When `F = a · raw^b` is
applied to the lower trial raw, it returns a force reading systematically
below the true applied force. The magnitude of this bias, ~5% on the raw
input to a power-law with b typically in the range 0.5–1.0 for
piezoresistive sensors, propagates as a 2.5–5% absolute error in reported
Contact Force — before any other source of uncertainty is added.

Directly consequential for:
- Metric 3 (maximum admissible surface force): the controller-quit event is
  a fixed physical threshold; if reported Contact Force reads low by
  2.5–5%, the measured "maximum admissible" force is systematically
  underestimated. The soft grasper, which operates at higher surface forces
  than the rigid grasper, is more exposed to this bias.
- Metrics 4 and 5 (peak and minimum grasp force): both biased low by the
  same systematic.
- The benchmark's core output is the parameter-space comparison envelope
  between soft and rigid graspers. A 5% systematic on the dominant
  uncertainty source, uncharacterized and unrecorded, violates Amendment 1
  and Article I — the very failure mode Amendment 1's "What happens without
  it" clause warns against.

**On MTS capability.** Position B requires ramp completion in under 0.5 s.
If the available MTS cannot achieve this rate, the correct response under
the Thomas Jefferson Principle is not to accept the calibration bias of
Position A — it is to redesign either the fixture (step-release mechanism
at target force) or the trial protocol (extend trial contact dwell to 5+ s
to match calibration timescale). Position A's 5 s settle is not a physics
fact derived from the Contact Force primitive; it is a procedural
convention that may be appropriate for a static bench characterization
context but is mismatched to this benchmark's trial timescale.

**Concessions.** Position B does not dispute: the Stage 0 Host-Driven Smoke
Test Suite (H0–H3, all sub-checks); the Calibration Bill's curve form
`F = a · raw^b`; the 8-level log-spaced force sweep and specific force
levels; the 3 repeats per level with full unload between; the sensor
warm-up protocol; the acceptance criteria (RMS ≤ 2% FS, max ≤ 4% FS,
log-log adj-R² ≥ 0.998 per channel); the JSON storage schema, admissibility
binding, and re-fit cadence; the bundled ratification of Amendment 7.

**Open question for the Justice.** Part 5 of the Calibration Bill (re-fit
cadence, "30 days" interval) was drafted assuming the per-level timing
from Part 3 as context. The timing change reduces total per-channel
acquisition time by ~3–4×, which may make a shorter re-fit cadence
practical. Position B takes no position on whether the cadence number
should change — that is a separate question. The Part 5 language does not
reference the specific timing window, so no textual edit is strictly
required for consistency. *(Justice ruled C2: cadence unchanged.)*

---

### Case 2: Bill 0003 — Dead-Weight Alternative Force Source for A301-1 Calibration

**Date:** 2026-05-19
**Positions:**
  - A — Enact Bill 0003 as drafted — dead-weight first-pass calibration
    unblocks Stage 0 close while MTS access remains unresolved.
  - B — Reject Bill 0003 — wait for MTS access before any per-channel
    calibration; do not admit a lower-precision force source even as
    first-pass.

**Prevailing position:** A (amended at ruling — substantially narrower than
as-drafted). Justice ruled on 2026-05-19.

**Scope of enactment:**
- Bill 0003 applies to A301-1 channels Ch0–Ch4 ONLY.
- A301-25 channels Ch5–Ch6 remain on the MTS path under Bill 0002 unchanged;
  calibration deferred until MTS access is resolved.
- Bill 0002 Part 3's clause "No alternative force-generation rig is admissible"
  is REVERSED for A301-1 only, by this ruling. The reversal was the subject
  of this named hearing.

**Justice's ruling:**

1. **Clause (a) — ENACTED, scoped:** Dead-weight loading is admissible as
   an alternative force source for first-pass A301-1 calibration (Ch0–Ch4).
   MTS path under Bill 0002 remains primary; if MTS access becomes available,
   MTS recalibration of A301-1 channels is recommended but not mandatory within
   any fixed window. A301-25 (Ch5–Ch6) calibration must use the MTS path per
   Bill 0002 unchanged.

2. **Clause (b) — REMOVED:** No Part 3.2b. Existing Bill 0002 Part 3.2 timing
   (0.5–2.5 s window, 200 samples) stands unchanged. The capture.py DAQ-stream
   onset detector resolves t=0 from the signal, not from operator placement
   timing.

3. **Clause (c) — REMOVED:** No σ-discard threshold change. Existing 21 ADC
   count threshold stands.

4. **Clause (d) — ENACTED:** New `src/calibration/deadweight.py` shall contain:
   - `DeadWeightRecord` dataclass (`mass_kg`, `oiml_class`, `certificate_id`,
     `traceable_to`)
   - `deadweight_force_N(mass_kg) -> float` using g = 9.80665 m/s² (CGPM
     standard gravity)
   - Coordination wrapper around existing `capture.py` / `fit.py`
   - No modification to `mts.py`

5. **Clause (e) — ENACTED:** JSON schema additions in Bill 0002 Part 6.2:
   - `force_source: "dead_weight" | "mts"`
   - `dead_weight_record: { mass_kg, oiml_class, certificate_id, traceable_to,
     g_m_per_s2 }`
   - Amendment 7 derivation header records the mass-to-force derivation
     explicitly

6. **Clause (f) — REMOVED:** No 30-day MTS-access recalibration trigger.
   Resolves Case 1 C2 conflict — Part 5 cadence remains as drafted per Case 1.

**Force levels for A301-1** (FS 4.4 N, calibration range 0.25–4.18 N):
Use 50/100/200/500 g weights (OIML M1 or better, mass certificate recorded),
singly and stacked, yielding: 0.49, 0.98, 1.47, 1.96, 2.45, 2.94, 3.43,
4.90 N (eight log-spaced points; the 4.90 N point slightly exceeds the 4.18 N
upper end — clip to 4.4 N FS or omit at operator discretion).

**Conditions on application:**

- **C1 — Pre-acquisition placement-transient sanity check (Attorney-B residual
  condition):** Before the first calibration point is acquired on any channel
  under this Bill, run a one-shot placement-transient capture on a single
  A301-1 channel: 200 frames baseline + 500 frames post-placement at one
  mid-range weight (e.g., 200 g). Record the result to
  `docs/device_context.md` Signal Measurements. Confirm the placement
  transient decays to within the within-window stationarity criterion (5%
  creep allowance per `capture.py` `is_stationary`) before t = 0.5 s. If it
  does not, this Bill is suspended pending a follow-up Bill that either
  (i) extends the acquisition window or (ii) modifies the placement procedure.

- **C2 — Case 1 Condition C1 (MTS feasibility check) status:**
  - For A301-1 channels Ch0–Ch4: DEFERRED. Does not block Stage 0 close.
  - For A301-25 channels Ch5–Ch6: REMAINS BLOCKING. Channels Ch5–Ch6 stay TBD
    in `docs/toolchain_config.md` until MTS access is confirmed.

- **C3 — OIML mass traceability:** Each weight used must carry OIML M1 or
  better classification with a current certificate number and a traceability
  statement (national standard authority). Metadata recorded in the
  `dead_weight_record` block of the JSON calibration header per Bill 0002
  Part 6.2 as amended by Clause (e) of this Bill.

- **C4 — Case 1 Conditions C2 and C3 stand unchanged.** Part 5 cadence is
  unmodified.

**Physical/empirical basis (Benjamin Franklin Principle):**
F = m · g where g = 9.80665 m/s² (CGPM standard gravity, 1901). OIML M1
mass-uncertainty at 0.5 kg is ≤ 0.025 g, giving force uncertainty ≤ 0.00025 N
— four orders of magnitude below the A301-1 Part 4 acceptance criterion of
RMS residual ≤ 0.088 N (2% of 4.4 N FS). The 50/100/200/500 g weight set,
singly and stacked, covers the A301-1 calibration force range with appropriate
log-spacing. Dead-weight force generation introduces no measurable uncertainty
into the calibration point at this sensor's FS. The `capture.py` module is
force-source-agnostic by design (frame_source iterator, DAQ-stream onset
detection); the existing 0.5–2.5 s window and σ ≤ 21 ADC count threshold
remain physically traceable under dead-weight loading provided C1 sanity check
passes.

**Device outcome protected (Thomas Jefferson Principle):**
A301-1 channels Ch0–Ch4 (table-foot contact-force array) transition from
INADMISSIBLE to ADMISSIBLE under Bill 0002 Part 7. Contact Force evidence
becomes available for benchmark metrics 3, 4, and 5 on the table-foot array.
The finger-pad A301-25 channels (Ch5–Ch6) remain inadmissible until MTS access
is resolved — acknowledged as a partial Stage 0 progress condition. The MTS
calibration path (`src/calibration/mts.py`) is preserved intact for both
sensor families.

**Enacted bill:** Bill 0003 — Dead-Weight Calibration for A301-1 Channels
(amended at ruling)
**Implementation branch:** `bill/deadweight-calibration-a301-1`

---

#### Arguments — Position A (filed by Attorney-A, 2026-05-19)

Attorney-A argued that:

**Amendment invoked:** Amendment 1 (Domain Primitives, RATIFIED 2026-05-14)
and Amendment 7 (Calibration Discipline, RATIFIED 2026-05-15 by Case 1). The
Contact Force primitive requires admissible evidence from Ch0–Ch4. With MTS
access unresolved, the Bill 0002 Part 3 prohibition on alternative force sources
leaves Ch0–Ch4 permanently inadmissible under the current record — which itself
violates Amendment 2 (Stage Gate Order) by blocking Stage 0 close
indefinitely. Dead-weight generation is traceable to CGPM standard gravity
(g = 9.80665 m/s²), a physical first-order measurement, satisfying Article I.

**Precedent:** Case 1 (2026-05-15). Case 1 established that the Bill 0002 MTS
feasibility precondition (C1) could be deferred — it does not block Stage 0
close until MTS access is confirmed. This ruling created the gap that Bill 0003
fills: if MTS is unavailable, a physically traceable alternative force source
is needed or Stage 0 remains permanently open. Case 1 did not address this
gap because MTS access was assumed resolvable in the short term.

**Physical outcome protected:** OIML M1 force uncertainty at 0.5 kg is
≤ 0.00025 N — four orders of magnitude below the A301-1 acceptance criterion
of 0.088 N RMS residual. Dead-weight loading introduces no measurable force
uncertainty at A301-1 FS of 4.4 N. The `capture.py` onset-detection mechanism
is force-source-agnostic. The 0.5–2.5 s window and 21 ADC count threshold from
Case 1 remain unchanged and their physical derivation is unaffected by whether
the load arrives via MTS ramp or manual weight placement (provided the
placement transient has decayed before t = 0.5 s — confirmed by C1 sanity
check).

**Consequences of Position B in physical terms:** If Position B prevails,
Ch0–Ch4 remain tagged INADMISSIBLE indefinitely. Benchmark metrics 3, 4, and 5
— all tracing to Contact Force under Amendment 1 — are blocked. Stage 0 cannot
close under Amendment 2. The project is halted by an equipment-access constraint
that has a physically traceable, metrologically adequate substitute.

#### Arguments — Position B (filed by Attorney-B, 2026-05-19)

Attorney-B argued that:

**Amendment invoked:** Amendment 1 (Domain Primitives) and Amendment 7
(Calibration Discipline). The MTS path was ratified in Case 1 specifically
because it provides a controlled, repeatable ramp rate — the controlled ramp
rate (≤ 0.5 s to target) is what ensures the calibration acquisition window
(0.5–2.5 s) begins after the load is mechanically settled but before
logarithmic creep advances significantly. Manual weight placement cannot
guarantee ramp completion before t = 0.5 s; placement transient dynamics
are operator-dependent and uncharacterized.

**Precedent:** Case 1 (2026-05-15). Case 1's entire physical argument for
the 0.5–2.5 s window rested on the MTS's ability to deliver load in ≤ 0.5 s.
Substituting a manual placement procedure without first characterizing the
placement transient risks the window beginning before the signal has settled,
which would absorb a transient artifact into the calibration point — the
precise failure mode Case 1 was constructed to prevent.

**Physical outcome protected:** A calibration produced with an uncharacterized
placement transient could have RMS residuals that pass the 0.088 N criterion
at calibration time but carry a systematic bias that emerges as force readings
drift during trials. The MTS path's mechanical reproducibility is the physical
guarantor of the window's validity.

**Consequences of Position A in physical terms:** An inadequately characterized
placement transient that contaminates calibration points would produce fitted
coefficients (a, b) that absorb the transient artifact. Trial force readings
would exhibit a systematic offset whose sign and magnitude cannot be determined
without the characterization Position B requires first.

**Residual conditions (adopted as Case 2 C1):**
1. Run a one-shot placement-transient capture before the first calibration
   point is acquired (200 frames baseline + 500 frames post-placement at one
   mid-range weight). Confirm transient decays within the is_stationary
   criterion before t = 0.5 s.
2. Physical justification required for any window shift — moot; window remains
   0.5–2.5 s unchanged.
3. Revert to 0.5–2.5 s if transient decays before 0.5 s — moot; C1 sanity
   check confirms this assumption holds before calibration begins.

---

### Case 3: Bill 0004 — TPU 95A Fixturing Pad for A301-1 Channels (Ch0–Ch4)

**Date:** 2026-05-19
**Positions:**
  - A — Enact Bill 0004 as drafted — TPU 95A 1.0 mm pad (OUVERTURE, 3D-printed
    100% infill) at the A301-1 contact interface at both calibration time and
    trial time.
  - B — Reject Bill 0004 — bare-sensor calibration is sufficient; do not
    introduce TPU viscoelastic compliance into the load path.

**Prevailing position:** A (CONDITIONALLY ENACTED — substantially amended at
ruling with four binding conditions). Justice ruled on 2026-05-19.

**Scope of enactment:**
- Bill 0004 applies to A301-1 channels Ch0–Ch4 ONLY (inherits the Bill 0003 /
  Case 2 scope).
- A301-25 channels Ch5–Ch6 are NOT affected.

Position B's evidentiary point about the empty Signal Measurements table
prevailed in part: the 0.22 N systematic offset was a class-level projection,
not a measurement on this hardware. The four conditions below convert Position
A's projections into a measurement-first protocol.

**Justice's ruling:**

Bill 0004 is enacted with the four conditions below. Original Bill 0004
clauses (a), (b), (d), (e), (f) stand as drafted, subject to the four
conditions. Clause (c) is superseded by Case 3 C1 (which strengthens the
original wording).

**CONDITIONS BINDING ON IMPLEMENTATION:**

**C1 — Pre-acquisition sanity check with TPU pad in place (modifies Bill 0004
Clause (c)):**
Before the first calibration point is acquired on any A301-1 channel under
Bill 0004, run a one-shot placement-transient capture on a single channel with
the full A301-1 + TPU 95A 1.0 mm pad + 200 g weight stack as deployed. 200
frames baseline + 500 frames post-placement at 100 Hz. Record the result to
`docs/device_context.md` Signal Measurements. Confirm the placement transient
decays to within the within-window stationarity criterion (5% creep allowance
per `capture.py` `is_stationary`, line 52) before t = 0.5 s. If the check
fails, Bill 0004 is suspended pending a follow-up Bill.

**C2 — Bare-sensor baseline offset measurement (new — protects against Position
B's evidentiary objection):**
Before any TPU pad calibration data is admitted, the operator runs a
comparative offset measurement on one A301-1 channel:
  (a) Apply a 200 g OIML M1 mass directly to the bare A301-1 sensor surface.
      Record 200 sample mean raw ADC reading.
  (b) Apply the same 200 g mass via the deployed 3D-printed bench-foot geometry
      seated on the bare sensor. Record 200 sample mean raw ADC reading.
  (c) Compute the bare-sensor vs bench-foot delta in ADC counts. Convert to
      Newtons using a preliminary linear approximation
      (delta_F ≈ delta_raw * applied_N / mean_raw).
  (d) Record both measurements and the computed delta_F in
      `docs/device_context.md` Signal Measurements as
      "bench-foot vs OIML-mass offset, bare A301-1, Ch<N>".
If |delta_F| < 0.05 N (half the Bill 0002 Part 5.2 zero-load tolerance), the
TPU pad is NOT necessary for Article I compliance, and Bill 0004 is suspended
(the projected 0.22 N motivation does not hold on this hardware). If
|delta_F| >= 0.05 N, Bill 0004 proceeds — the measured offset is the empirical
justification for fixturing identity.

**C3 — Per-pad modulus consistency check (new — protects against 3D-printed
TPU anisotropy):**
Each of the 5 TPU 95A pads must be produced from the same OUVERTURE filament
lot, printed in the same session at 100% infill with identical layer-line
orientation. Before deployment, run a simple 3-point loading consistency test:
place each pad in turn between the same bare A301-1 channel and the same 200 g
OIML mass; record the raw ADC reading at the 0.5–2.5 s window. The inter-pad
spread (max - min raw mean) must be < 5% of the mean reading across the 5
pads. If the spread exceeds 5%, the affected pad(s) must be re-printed or the
inter-channel variance must be recorded as a known systematic in the JSON
`dead_weight_record.print_session_id` field. Measurement results recorded in
`docs/device_context.md` Signal Measurements as
"TPU 95A inter-pad consistency, lot <id>, print session <id>".

**C4 — Polymer compression-set re-calibration trigger (modifies Bill 0002
Part 5.1):**
The 30-day re-fit cadence under Bill 0002 Part 5 was designed for sensor
drift. Under Bill 0004, the calibrated artifact (A301-1 + TPU 95A 1 mm stack)
has an additional drift mode: polymer compression set. A new trigger is added
to the Bill 0002 Part 5.1 mandatory re-calibration trigger list (NOTE: this
addition is authorised by Case 3 ruling, NOT a violation of Case 1 Condition
C2 which froze Part 5 — Case 3 explicitly extends Part 5 for the dead-weight +
pad path):

  "(f) Visible deformation or thickness change of any TPU fixturing pad > 0.05
  mm (5% of nominal 1.0 mm), measured with calipers at session start. Reason:
  polymer compression set under sustained load can exceed 5% in 30 days at
  room temperature, shifting the calibrated artifact's response."

**Amendment 9 status acknowledgement:**
Amendment 9 (Hardware Optimization Transparency) is PROPOSED, not RATIFIED, as
of this ruling. The 6-row BOM change (5 TPU pads + 1 backing disc reference,
applied per A301-1 channel) is authorised by this Justice's ruling under
Article II directly, pending Amendment 9 ratification. Once Amendment 9 is
ratified, this BOM change shall be cited as a precedent example of
pre-Amendment-9 BOM change ratified by Judicial Hearing.

**Physical/empirical basis (Benjamin Franklin Principle):**
Position B's evidentiary objection was correct: Bill 0004 as drafted relied on
a class-level projection (0.22 N offset) without per-hardware measurement.
Position A's Article I / Amendment 7 argument is sound in principle
(calibration ≡ trial fixturing identity) but requires empirical grounding on
this specific hardware. The four conditions resolve the dispute by requiring
measurement before enactment is fully operative:
  - C2 measures whether the projected offset actually exists.
  - C1 measures whether the pad-in-place stack settles within the 0.5 s window.
  - C3 measures inter-pad consistency to bound the 3D-printed anisotropy
    concern.
  - C4 acknowledges polymer drift mode in the re-cal cadence.
If all four checks pass, the fixturing-identity argument is empirically
grounded and Bill 0004 is fully operative. If any check fails, the operator
suspends and files a follow-up Bill.

**Device outcome protected (Thomas Jefferson Principle):**
A301-1 channels Ch0–Ch4 (table-foot contact-force array) gain a defined,
traceable, measurement-grounded fixturing standard (A301-1 + TPU 95A 1 mm
stack, with all per-pad metadata in the JSON). The dead-weight calibration
coefficients (a, b) become traceable not only to the OIML M1 mass standard
(Bill 0003) but also to the specific fixturing stack used at both calibration
and trial. Bill 0002 Part 5.2 session-start zero-load check operates on the
same fixturing as calibration, eliminating the spurious-abort risk. A301-25
channels Ch5–Ch6 remain on the MTS path under Bill 0002 unchanged.

**Enacted bill:** Bill 0004 — TPU 95A Fixturing Pad for A301-1 Channels
(conditionally enacted, four conditions binding).
**Implementation branch:** `bill/tpu-fixturing-a301-1`

---

#### Arguments — Position A (filed by Attorney-A, 2026-05-19)

Position A argued that:

**Amendment invoked:** Amendment 1 (Domain Primitives, RATIFIED 2026-05-14),
Amendment 7 (Calibration Discipline, RATIFIED 2026-05-15 by Case 1). The
fixturing identity principle — calibration and trial must use the identical
contact geometry — is an Article I requirement: if the bench-foot geometry
differs between calibration and trial, the transfer function measured at
calibration does not predict the sensor output at trial. This is precisely
the Amendment 7 failure mode ("a tuned constant... requires re-tuning at
every hardware or population change"). The TPU 95A 1 mm pad is the physical
artifact that establishes fixturing identity for the A301-1 array.

**Precedent:** Case 1 (2026-05-15) and Case 2 (2026-05-19). Case 1
established that the calibration timescale must match the trial timescale —
the same principle of measurement-condition identity that governs fixturing.
Case 2 established the dead-weight path for A301-1, creating the context in
which fixturing standardisation becomes necessary: the bench-foot geometry
through which dead-weight force is delivered at calibration time must be
identical to the geometry present at trial time.

**Physical outcome protected:** A 3D-printed bench-foot geometry channels the
applied dead-weight force through a defined contact patch on the A301-1
sensor surface. Without a TPU pad, the effective contact area and stress
distribution at calibration differ from those at trial (where the bench foot
sits on the loaded sensor surface without an intervening pad). A class-level
projection of the resulting systematic offset is approximately 0.22 N at
2 N applied force — ~10% of the Contact Force primitive range relevant to
benchmark metric 3.

**Consequences of Position B in physical terms:** If Position B prevails, the
A301-1 calibration is performed bare-sensor (no bench-foot pad), but trial
measurements pass through the bench-foot geometry. The transfer function
mismatch introduces a systematic force error whose magnitude is uncharacterized
and unrecorded, violating Article I and Amendment 7.

---

#### Arguments — Position B (filed by Attorney-B, 2026-05-19)

Position B argued that:

**Amendment invoked:** Amendment 1 (Domain Primitives) and the Benjamin
Franklin Principle. The Signal Measurements table in `docs/device_context.md`
is empty. No per-hardware measurement of the bench-foot vs bare-sensor offset
exists for this project's specific A301-1 units, bench-foot geometry, and
surface finish. The 0.22 N figure cited by Position A is a class-level
projection from sensor characterization literature, not a measurement on this
hardware.

**Precedent:** Case 1 (2026-05-15). Case 1 ruled that calibration parameters
must trace to physical measurements — not to "generic bench-testing
conventions." Position A's 0.22 N figure is a convention drawn from a
different measurement context.

**Physical outcome protected:** A TPU 95A viscoelastic pad introduces its
own compliance and creep into the force path between the applied dead-weight
and the sensor surface. TPU compression creep over 30 days at room temperature
can exceed 5% — comparable in magnitude to the offset it is intended to
correct. A bare-sensor calibration with the bench-foot geometry measured
directly (no pad) avoids adding a new viscoelastic variable with an
uncharacterized drift mode.

**Consequences of Position A in physical terms:** If Position A prevails
without empirical grounding, the calibration stack includes a TPU pad whose
compliance and long-term creep are uncharacterized on this hardware. The
improvement in fixturing identity may be smaller than the variance introduced
by inter-pad 3D-printing anisotropy and polymer compression set.

**Residual conditions (adopted as Case 3 C1–C4):**
C2 — Measure the actual bench-foot vs bare-sensor offset before admitting TPU
pad calibration. C1 — Confirm pad-in-place stack settles within 0.5 s. C3 —
Confirm inter-pad consistency < 5% spread. C4 — Add polymer compression set
as a re-calibration trigger.

---

## Frozen Precedents

*(Populated by stage-compactor at each stage gate.)*
