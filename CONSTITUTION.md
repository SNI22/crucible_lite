# Crucible Constitutional Governance Document

> **This document must not be modified.** All project-specific rules are Amendments. All conflicts are resolved by Judicial Hearing. The Articles are unconditional.

## Preamble

This document governs all development decisions in any project that adopts the Crucible framework. It binds human engineers and AI agents equally. The two Articles below are unconditional — they cannot be amended, suspended, or reasoned around. All operational rules derive from them as Amendments. All conflicts between Amendments are resolved through the four-branch governance system defined herein.

The four branches are: the **Legislature** (proposes changes), the **Judiciary** (resolves conflicts and approves Bills), the **Amendment Ratification Process** (adds new governance rules), and the **Bureaucracy** (executes established procedures without approval). These four branches, together with the two Articles, constitute the complete governance system.

---

## Article I — Physics First

No parameter, threshold, gate, or algorithmic decision may be defined, proposed, or accepted unless it traces to a first-order physically measurable quantity in the device's domain and directly related to the purpose of the deployed devices, i.e., porosity of a filter as the ultimate criterion to change the filters. 

**Adapting this for your device:**

Before writing a single line of firmware, define your domain primitives — the two or three quantities that your device ultimately measures or responds to, and drives the decision making. Every threshold, every filter cutoff, every FSM transition must trace back to one of these.

Examples:
- Gait wearable → Cadence (steps/min), Step Length (m), Vertical Oscillation (cm)
- Thermostat → Thermal Mass (J/°C), Heat Transfer Coefficient (W/m²K), Occupancy Rate (persons/hr)
- Air quality monitor → Particulate mass concentration (μg/m³), Chemical concentration (ppb), Ventilation rate (ACH)
- Soil moisture sensor → Volumetric Water Content (m³/m³), Field Capacity (%), Wilting Point (%)

Sensor readings, ADC counts, filter outputs, and moving averages are measurements of these primitives — not the primitives themselves. An engineer who sets a threshold by fitting it to data without naming the underlying physical quantity has guessed. Guesses are not permitted.

**This Article is unconditional.** It cannot be suspended for schedule reasons, convenience, or "it worked in testing."

---

## Article II — Human in the Loop

No decision that changes the physical or algorithmic direction of the project may be made by an agent alone.

**An agent executes. A human decides.**

The boundary is defined as: any action whose consequence cannot be fully reversed by a single `git revert` requires human approval before execution. Flashing firmware to hardware is the limiting case — it is irreversible within a session.

Empirical evidence — signal plots, UART output, unit test results, field measurements — is the only valid input to a human decision. Argument from intuition, argument from prior success, and argument from expediency are not valid inputs.

**This Article is unconditional.**

---

## The Amendments

Amendments are the operational rules of your specific project. They derive from the Articles and govern day-to-day decisions.

**This repository ships with no pre-defined Amendments.** You write your own based on your device domain, your team, and your risk tolerance. The Amendment Ratification Process below governs how they are created.

The GaitSense reference implementation has 17 ratified Amendments. They are documented at `examples/gait_wearable/amendments.md` as a concrete example of what device-specific Amendments look like.

**Mandatory starting point:** Every Crucible project must ratify at minimum:
- An Amendment defining its domain primitives (Article I implementation) — written by `/spec collect`
- An Amendment defining its stage gate order — pre-drafted as Amendment 2
- An Amendment defining its toolchain alignment record — pre-drafted as Amendment 3
- An Amendment defining its three-strike escalation rule — pre-drafted as Amendment 4

These four are the minimum viable governance layer. Everything else grows from them.

Amendments 2–4 (and optional Amendments 5–10) are pre-drafted in `docs/governance/amendments.md`.
Read them, confirm they apply to your project, and ratify by removing the PROPOSED prefix.
Amendment 1 is written by `/spec collect` after domain primitive ratification.

---

## The Bureaucracy

The Bureaucracy executes established procedures autonomously — without a Bill, hearing, or Amendment vote. These are operations that must happen reliably every time, the same way every time.

### What the Bureaucracy governs

Any operation that:
- Executes an established procedure with a known-good outcome
- Does not alter firmware, simulation, or algorithm behaviour
- Is repeatable, deterministic, and fully reversible (or additive-only)

### Standing Order classes (pre-approved)

| Class | Operations |
|-------|-----------|
| **Firmware Build** | Compile from existing source using active toolchain |
| **Package Management** | Install, update, pin dependencies |
| **Simulation Execution** | Run established simulation scripts against existing profiles |
| **Signal Plotting** | Generate diagnostic plots per the project's signal plot mandate |
| **Data Export** | Export session data to established formats |
| **Version Control** | Commit, push, branch management for validated work |
| **Toolchain Validation** | Run `/toolchain validate` checks |

### Escalation triggers

| Trigger | Escalates to |
|---------|-------------|
| Output deviates from predicted result | Legislature — new Bill required |
| Two Standing Orders produce conflicting results | Judiciary — Hearing required |
| New instrument or API class needed | Legislature — Bill to establish new Standing Order |
| Any operation that would change source code or algorithm logic | Legislature — out of scope |
| Three consecutive failures of the same Standing Order | Three-Strike Amendment — escalate to human |

---

## The Legislative Process

### What requires a Bill

Any proposed change to: simulation (new profile, signal parameter), firmware (algorithm patch, threshold, FSM state), software (new pipeline stage), or hardware (BOM change, sensor repositioning). Bug fixes that restore a known-correct state do not require a Bill. Changes that introduce new behaviour do.

### Bill format

```
### BILL: [Descriptive name]
Proposed by: [engineer or agent]
Date drafted: [date]
Change type: simulation / firmware / software / hardware

Problem statement:
[What failure mode, gap, or improvement does this address?
Cite the specific test result, signal measurement, or field observation.]

Proposed change:
[Exactly what changes — file names, function names, parameter values]

Article/Amendment grounding:
[Which Article or Amendment authorizes this change?]

Physical evidence:
[Signal plots, UART output, unit test results, field measurements.
A Bill with no physical evidence is returned — it cannot be debated.]

Expected outcome:
[What measurable improvement does this produce?
State in terms of your domain primitives.]

Branch:
[The git branch on which this change will be implemented if enacted]
```

### Enactment

A Bill is debated before implementation. An agent is assigned as opposing attorney. The Justice (human) presides. Enacted Bills are implemented on a dedicated branch and validated against the expected outcome before merging.

---

## The Judicial Process

### Jurisdiction

Activates when: two Amendments mandate incompatible actions; a situation arises no Amendment addresses; or an agent is uncertain which Amendment governs.

### The Benjamin Franklin Principle

The Justice's ruling must be based on empirical evidence — a signal plot, a test result, a measurement, a field observation, a physical constraint — or on the governing Articles. A ruling that cannot cite its physical or empirical basis is not valid.

### The Thomas Jefferson Principle

The ultimate goal of every decision is the best possible hardware outcome: a device that is correct, robust, and honest in its output to the user or system that depends on it.

Where Amendments and precedents are silent or ambiguous, the Justice asks: *which decision gives the person or system relying on this device the most accurate measurement of what they care about?* That answer governs.

### Hearing procedure

1. **Declaration.** Justice identifies the conflict and the competing positions.
2. **Assignment.** Justice assigns an agent to each position.
3. **Argument — Position A.** Amendment invoked, precedent cited, physical outcome protected, consequences of opposing position.
4. **Argument — Position B.** Same four elements.
5. **Deliberation.** Justice may ask one clarifying question per attorney.
6. **Ruling.** Justice announces prevailing position, physical/empirical basis, patient/user outcome protected, any conditions.
7. **Recording.** Prevailing attorney records the ruling in `docs/governance/case_law.md` before any implementation begins.

### Binding effect

A ruling governs all future agents and humans until explicitly overruled by a new hearing. An agent that believes a precedent should not apply must declare a hearing — it may not deviate unilaterally.

---

## The Amendment Ratification Process

### What qualifies as a proposed Amendment

A new governance rule applicable to all future decisions — not a specific technical change (that is a Bill) and not a conflict ruling (that is a Judicial Hearing).

### Proposal format

```
### PROPOSED AMENDMENT [N]: [Title]
Proposed by: [engineer or agent]
Date: [date]
Traces to: Article I / Article II / both

Governing rule (one sentence):
[The rule]

Physical or process justification:
[Why this rule is needed. Cite a failure mode or empirical observation.]

Amendment it complements or constrains:
[Which existing Amendments does this interact with?]

What happens without it:
[The specific failure mode or ambiguity that persists if not ratified.]
```

### Ratification

Single-engineer project: the one human constitutes the full voting body. Explicit ratification required — silence is not ratification. Multi-team: > 60% of teams must vote Ratify. Quorum = at least 2 teams.

**Articles are immune.** No vote can amend Article I or Article II.

---

## The hw-advisor Role

The hw-advisor is a Crucible-specific agent that reads your existing circuit diagram, BOM, and test results, and provides grounded suggestions — not unsolicited redesigns.

**What hw-advisor does:**
- Reads your BOM and identifies component choices that conflict with test results
- Flags pin conflicts that match known failure patterns (from toolchain_config.md)
- Suggests component upgrades or substitutions when test data shows a specific gap (e.g., enclosure stiffness too low → heel-strike signal attenuated)
- Cross-references your field test results against your simulation predictions and identifies systematic deviations

**What hw-advisor does not do:**
- Redesign your circuit without a Bill
- Override your component choices without physical evidence
- Propose changes that cannot be traced to a domain primitive (Article I)
- Self-approve any change to the BOM or schematic (Article II)

Every hw-advisor suggestion is framed as a Bill proposal — it provides the problem statement and physical evidence; the human decides whether to enact it.

---

## Reference Implementation

The GaitSense ankle wearable project is the canonical reference implementation of this framework. It documents 5 stages, 17 ratified Amendments, 5 binding case law precedents, 13 bugs found and resolved before hardware deployment, and a complete toolchain evolution record (including a blocked toolchain and the three-strike rule that blocked it).

See `examples/gait_wearable/` for pointers into that codebase.
