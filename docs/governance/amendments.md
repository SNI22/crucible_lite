# Crucible Amendments

All amendments derive from Article I (Signal First) and/or Article II (Human in the Loop)
in CONSTITUTION.md. The governing Articles are unconditional and cannot be amended.

Amendment 1 is always the Domain Primitives amendment — written by `/spec collect` for
each specific project. Amendments 2–4 are mandatory framework amendments ratified here.
Amendments 5 onwards are domain-agnostic operational amendments included as defaults;
ratify them by removing the PROPOSED prefix. Project-specific amendments (signal plot
mandate, statistical derivation rules, etc.) are added after Amendment 1 is ratified.

---

## Amendment 1 — Domain Primitives (piezo_fall)
*Traces to: Article I*
*Status: RATIFIED — 2026-05-15*

**Governing rule:** Every threshold, filter cutoff, FSM transition, and
algorithm parameter in this project must trace to one of the following
three domain primitives. A parameter that cannot be so traced is a guess
and is not permitted.

**Domain primitives:**

1. **Floor acceleration** (m/s²) — inertial response of the bathroom floor
   to mechanical events on it. Measured via piezo (PVDF + proof-mass
   cantilever) at **≥ 1 kHz**. Every recorded CSV from this project
   MUST include three metadata fields: `int_mark` (firmware streaming
   delay-selector value), `transport` ("usb-uart" or "bt-spp" or
   equivalent), and `measured_rate_hz` (samples ÷ wall-clock recording
   duration). CSVs missing any of these three fields are NOT admissible
   as Article I evidence in any future Judicial Hearing.
   [Revised 2026-05-16 by Case 1 (Bill 001) — set to ≥1.5 kHz.
    Re-revised 2026-05-16 by Case 2 (Bill 002) — back to ≥1 kHz after
    empirical evidence (catfood_bedroom_2.txt) showed BT-SPP sustains
    only ~1.38 kHz, contradicting Case 1's 1.7-1.9 kHz assumption.]

2. **Acoustic pressure** (Pa, or normalized PCM count) — sound pressure in
   the bathroom air; broadband channel for environment classification
   (shower / flush / drain false-alarm suppression) and speech-band
   channel for verbal-response detection ("yes / no / help" after the
   post-detection prompt). Measured via microphone.

3. **Human room occupancy** (boolean, with optional confidence) —
   presence of a human body in the monitored room. Measured via WiFi
   sensing module.

**Physical justification:** The device's purpose is to detect an elderly
person's fall in a bathroom and prompt for confirmation before escalating.
The hardest case is a slow controlled descent ("slump") at up to 3 m range
on tile floor, in the presence of plumbing-induced floor vibration. No
single sensor can disambiguate these scenarios:

- Floor acceleration alone cannot reject a shower-running false positive
  whose vibration spectrum may overlap a slow fall.
- Acoustic pressure alone cannot detect a silent slow slump.
- Occupancy alone cannot distinguish a fall from someone standing still.

Each primitive captures a physically distinct quantity; the fall-detection
decision derives from their joint state. Removing any of the three creates
an ambiguity class the device cannot resolve. The microphone's broadband
and speech-band channels are both derived from the same primitive
(acoustic pressure) and therefore count as one primitive, not two.

**Constraint on future amendments:** All future project amendments must
cite at least one of P1 / P2 / P3 as the physical basis for any threshold,
gain, cutoff, or transition condition they introduce.

**Failure mode without it:** Parameters set by intuition or by fitting
to data with no traceable physical basis. Article I unenforceable. The
repeated failure mode of the prior non-Crucible iteration of this project
— magic constants like `accur = 0.015295` and `ADC offset = 1890` baked
into firmware with no per-unit calibration and no primitive trace —
would recur in this project.

---

## Mandatory Framework Amendments

These three must be ratified before /session 0 on any Crucible project.
They are pre-written here — read, confirm they are correct for your project,
then remove the PROPOSED prefix to ratify.

---

### Amendment 2 — Stage Gate Order
*Traces to: Article I + II*
*Status: RATIFIED — 2026-05-15*

Development proceeds through exactly these stages in order, and no stage begins
until the previous stage's exit criteria are explicitly confirmed by the human:

  Spec Gate → Stage 0 (HIL Toolchain Lock) → Stage 1 (Simulation) →
  Stage 2 (Firmware Integration) → Stage 3 (Field Test) → Stage 4 (Host Integration)

An agent must not begin Stage N+1 work while Stage N has any open failure, even one
that appears unrelated to the next stage's work. Each stage's errors become
exponentially more expensive to fix in later stages. Hardware is a validation tool,
not a debugging tool.

**Exit criteria for each stage are defined in `/session`.**
**Stage closeout is executed by `stage-compactor`.**

---

### Amendment 3 — Toolchain Alignment
*Traces to: Article II*
*Status: RATIFIED — 2026-05-15*

Every agent working on this project must operate within the toolchain that is currently
active and recorded in `docs/toolchain_config.md`. No agent may introduce a new
toolchain, framework, or build system without a Bill enacted through the Legislative
Process. Switching toolchains mid-stage is not permitted — it requires a new stage gate.

The active toolchain record in `docs/toolchain_config.md` is the single source of truth
for all build, flash, and test operations. An agent that silently switches from the active
toolchain to a different one violates Article II regardless of whether the output compiles.

A blocked toolchain may only be re-activated by explicit human decision at a stage gate,
recorded in toolchain_config.md with a date and reason.

---

### Amendment 4 — Three-Strike Escalation Rule
*Traces to: Article II*
*Status: RATIFIED — 2026-05-15*

If a simulation, unit test, hardware smoke test, or iterative fix process fails to meet
exit criteria within three attempts, the agent must stop, report the full status to the
human, and wait for a human determination before any further action.

The three-strike report must include:
  1. What was attempted on each of the three tries
  2. What was observed on each attempt (exact output, not a summary)
  3. What the agent does not know — the open question that a human must answer

The agent must not propose a fourth approach without explicit human direction.

**Rationale:** Continuing past three failures compounds work debt and masks the root
cause. Three-strike reports also function as input to Judicial Hearings when the
failure pattern suggests a design conflict rather than a bug.

---

## Domain-Agnostic Operational Amendments

Ratify these as they become relevant to your project. Remove the PROPOSED prefix
after explicit human ratification.

---

### Amendment 5 — Simulation is the Hardware Proxy
*Traces to: Article I + II*
*Status: PROPOSED — ratify when Stage 1 begins*

If something cannot be tested in simulation, a simulation test must be written first.
Hardware results that deviate from simulation predictions are evidence of a hardware or
mounting problem — not a firmware problem — unless the corresponding simulation test
was never written.

The handoff document (`docs/governance/handoff.md`) is the binding prediction set
against which hardware results are compared at each stage gate.

---

### Amendment 6 — Signal Plot Mandate
*Traces to: Article I + II*
*Status: PROPOSED — ratify when Stage 1 begins*

After any change to the project's signal model or any filter coefficient in firmware
source, an agent must generate a signal plot, save it to `docs/plots/`, and wait for
human visual confirmation before proceeding.

Signal plots are the primary mechanism for catching silent model errors that pass
numerical tests. Human visual review of physical plausibility cannot be substituted
by a numerical test. A metric value that looks correct can be produced by a physically
implausible signal.

**Invoked by:** `/plot-profile` and `/plot-evidence signal`

---

### Amendment 7 — Calibration Discipline
*Traces to: Article I*
*Status: PROPOSED — ratify before any threshold is introduced in firmware*

One new calibration constant may be introduced per algorithmic iteration. Every
calibration constant must be documented with its physical derivation before the
session ends.

A constant derived from a physical measurement predicts its own correct value when
the operating conditions change. A tuned constant (fitted to observed data without
physical derivation) requires re-tuning at every hardware or population change.

Documentation format (inline in firmware source):
```
/* CONSTANT_NAME — derived from [domain primitive].
 * Physical derivation: [formula or measurement].
 * Value: [N] [unit].
 * Traces to: Amendment 1 primitive [N]. */
```

---

### Amendment 8 — Algorithm Search Honesty
*Traces to: Article I + II*
*Status: PROPOSED — ratify when algorithm work begins*

When an algorithm fix domain has been exhausted without resolution, the agent must
explicitly state:
  - Which domain was searched
  - Why it yielded no result
  - No more than three alternative domains

The human selects exactly one alternative. The hardware iteration option (sensor
repositioning, BOM change, enclosure change) must always remain on the list —
it is never automatically eliminated.

**Rationale:** An agent that continues searching within an exhausted domain without
disclosure violates Article II. Switching domains unilaterally violates the same
Article. The cost of an algorithm fix may exceed the cost of a hardware change —
the human must be in the decision.

---

### Amendment 9 — Hardware Optimization Transparency
*Traces to: Article II*
*Status: PROPOSED — ratify when algorithm work begins*

When an agent identifies that an algorithm change enables lower-cost hardware
(fewer sensors, lower-spec component, simpler enclosure), it must explicitly state
this and the physical reasoning before proceeding. The human decides whether to
optimize.

BOM changes have supply chain, procurement, and schedule consequences an agent
does not possess. All BOM or hardware specification changes require explicit human
authorization and must be recorded in `docs/device_context.md` BOM section.

---

### Amendment 10 — Interim Results and Decision Logging
*Traces to: Article II*
*Status: PROPOSED — ratify before any multi-step iterative session*

During any iterative build-debug process, intermediate results must be printed to
the terminal for human review. The agent waits for a human determination before
proposing the next action.

The specific human decision must be recorded in `docs/governance/case_law.md` or
the relevant stage record before the session ends.

**Rationale:** Prevents the most common failure mode in agentic development — an
agent runs five sub-steps autonomously, encounters an anomaly in step 2, compensates
in step 3, and delivers a result in step 5 that looks correct but carries a hidden
assumption no human ever approved.

---

### Amendment 11 — Scaffold Immutability
*Traces to: Article I + II*
*Status: PROPOSED — ratify before Stage 1 begins*

Project analysis modules (`src/events.py`, `src/analysis.py`, `src/plot.py`) are
generated exactly once — at the first execution of the stage that requires them
(Stage 1: Simulation) — by `/toolchain scaffold`.

After the human engineer and code-reviewer have confirmed the scaffolded modules
are correct (Article I compliant: all parsed fields trace to a domain primitive
declared in Amendment 1), those files are frozen. They must not be regenerated,
overwritten, or modified for the remainder of the project unless the human
explicitly authorizes a re-scaffold.

**What this means in practice:**

- `/toolchain scaffold` is blocked from running a second time without explicit human
  instruction. An agent must not invoke it silently during any session.
- Any change to `docs/device_context.md` Signal Inventory or
  `docs/toolchain_config.md` Firmware UART Format that would alter the scaffolded
  modules constitutes a change to the analysis pipeline and requires a **Bill**
  enacted through the Legislative Process before re-scaffolding is permitted.
- The code-reviewer must audit the scaffolded `src/` files at the Stage 1 Justice Gate
  as part of its Article I compliance check. Findings are resolved before the gate closes —
  not by silent re-generation.

**Rationale:** Regenerating scaffolded modules mid-project without governance is
identical in effect to changing firmware analysis logic without a Bill. It redefines
what the device measures, which violates Article I if the new definition has not been
traced to a domain primitive. It removes the human from a decision that changes
physical interpretation, which violates Article II.

**What happens without it:** An agent re-runs scaffold to "fix" a minor label,
silently changing a field name. The UART parser breaks on existing log files.
No one knows why Stage 3 field data no longer replays correctly.

**Amendment it complements:** Amendment 3 (Toolchain Alignment — the generated
modules are part of the analysis toolchain and are subject to the same alignment
discipline as firmware build tools).

---

## Project-Specific Amendments

Amendment 1 (Domain Primitives) is written here by `/spec collect` after human
ratification. Subsequent project-specific amendments are added below Amendment 1
as the project evolves.

> [Amendment 1 will appear here after /spec collect is run and ratified.]

---

## Amendment Index

| # | Title | Status | Traces to |
|---|-------|--------|-----------|
| 1 | Domain Primitives | RATIFIED 2026-05-15 | Article I |
| 2 | Stage Gate Order | RATIFIED 2026-05-15 | Article I + II |
| 3 | Toolchain Alignment | RATIFIED 2026-05-15 | Article II |
| 4 | Three-Strike Escalation Rule | RATIFIED 2026-05-15 | Article II |
| 5 | Simulation is the Hardware Proxy | PROPOSED | Article I + II |
| 6 | Signal Plot Mandate | PROPOSED | Article I + II |
| 7 | Calibration Discipline | PROPOSED | Article I |
| 8 | Algorithm Search Honesty | PROPOSED | Article I + II |
| 9 | Hardware Optimization Transparency | PROPOSED | Article II |
| 10 | Interim Results and Decision Logging | PROPOSED | Article II |
| 11 | Scaffold Immutability | PROPOSED | Article I + II |
