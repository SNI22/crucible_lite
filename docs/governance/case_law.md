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

## Frozen Precedents

*(Populated by stage-compactor at each stage gate.)*
