Collect the device specification: purpose, project target, signal inventory, and operating envelope. Writes the Device Purpose section of docs/device_context.md and drafts Amendment 1 (Domain Primitives) for human ratification.

Run this before /toolchain init and before /session 0. It is the first act of every new Crucible project.

Usage: /spec [subcommand]

Subcommands:
  collect   — full interactive interview (default if no subcommand)
  review    — read current docs/device_context.md and flag any gaps
  signals   — add or update signal inventory only (no full interview)
  target    — update the project target only

---

## Why this command exists

The GaitSense reference implementation worked because the project target was precise:
*"Detect gait asymmetry in people who walk stairs unevenly due to neurological impairment."*
Not "measure gait." Not "help people walk." A specific failure mode in a specific population
in a specific terrain condition.

That precision is what made every attorney argument admissible and every hardware decision
traceable. Without it, Article I has nothing to enforce against — "traces to a domain
primitive" means nothing if the primitive was never named.

This command exists to generate that precision before a single line of firmware is written.

---

## Step 1 — Project target interview

Ask the following questions in order. Wait for a full answer before asking the next.
Do not ask more than one question at a time.

**Q1 — What does this device do in one sentence?**
(Not what it measures — what it *does*. For the user, what changes because this device exists?)

Example answers:
- "It tells a physiotherapist whether a patient's gait is symmetric after hip replacement."
- "It shuts off an HVAC zone when no one has been in the room for 20 minutes."
- "It alerts a maintenance team before a bearing fails on a conveyor motor."

**Q2 — Who or what depends on the device's output being correct?**
(A person? A system? A decision? Name the dependency chain from output to consequence.)

Example: "The physiotherapist sees a symmetry score → decides whether to continue rehab.
If the score is wrong, the patient either over-trains or under-trains."

**Q3 — What is the hardest operating scenario this device must handle?**
(The case the device is most likely to fail at. This is the project target.)

Example: "Stair walking. The algorithm was tuned on flat ground and misses every second step
on stairs, making the symmetry score meaningless for the population that needs it most."

**Q4 — What does failure look like?**
Ask for both directions:
- False positive (device says X when X is not true): consequence?
- False negative (device misses X when X is true): consequence?

Example:
- "False positive: device reports symmetric gait in an asymmetric patient → therapist
  discharges patient early → patient reinjures."
- "False negative: device reports asymmetric gait in a symmetric patient → patient
  continues unnecessary rehab → wasted time and cost."

**Q5 — What is the pass/fail threshold for the project target?**
(Expressed as a measurement, not a subjective judgement.)

Example: "The device must detect ≥ 98 out of 100 steps on stairs, with SI error < 3%
compared to the gold standard (force plate measurement)."

---

## Step 2 — Signal inventory

For each sensor or signal source on the device, collect:

Ask: "List your sensors or signal sources. For each, I'll ask a few questions."

For each signal source, ask:
1. **Name** — what is this signal? (e.g., "IMU accelerometer Z-axis", "thermistor on motor housing")
2. **Physical quantity** — what does it measure in the world? (e.g., "vertical acceleration", "motor bearing temperature")
3. **Unit** — (e.g., m/s², °C, Pa, Hz, counts)
4. **Expected range** — min and max in normal operation (e.g., "−2g to +6g during walking")
5. **Hard limits** — values that indicate sensor failure or out-of-range condition
6. **Sample rate** — Hz or trigger condition
7. **Domain primitive link** — which of the device's domain primitives does this signal serve?

---

## Step 3 — Domain primitive extraction

After the signal inventory, derive the domain primitives.

Rules for primitive extraction:
- A domain primitive is a physically measurable quantity the device ultimately reports or controls
- It is NOT a sensor reading — it is what the sensor reading is *evidence of*
- There are usually 2–3 primitives; more than 4 is a sign the scope is too broad
- Every signal collected in Step 2 must trace to at least one primitive
- Flag any signal whose derivation from a domain primitive passes through more than one intermediate physical quantity. The one-intermediate-step limit enforces three properties simultaneously: (1) **Article I traceability** — the primitive citation remains verifiable; (2) **causation over correlation** — each additional intermediate is a potential confound that may correlate with the primitive in the training population but not causally link to it across conditions; (3) **hallucination prevention** — longer chains give an agent room to insert plausible-sounding intermediates that are not actually measured, anchoring decisions in fiction rather than physics. Recommend the human engineer identify a more direct sensor or redefine the primitive.

Present the extracted primitives to the human and ask for confirmation:

```
Based on your answers, the domain primitives for [Device Name] are:

  1. [Primitive name] ([unit]) — [one-line physical description]
     Measured via: [signal(s) from Step 2]

  2. [Primitive name] ([unit]) — [one-line physical description]
     Measured via: [signal(s)]

  3. [Primitive name] ([unit]) — [one-line physical description, if applicable]
     Measured via: [signal(s)]

Do these correctly name what the device ultimately measures or controls?
If no, tell me what to change.
```

Do not proceed to Step 4 until the human confirms the primitives.

---

## Step 4 — Operating envelope

Ask:

**Q6 — Normal operating conditions**
(Temperature range, humidity, vibration, mounting position, use duration, duty cycle)

**Q7 — Worst-case operating conditions**
(The environment the device will encounter at the extremes of its intended use)

**Q8 — Out-of-scope conditions**
(Conditions the device is explicitly NOT designed to handle — what would void the warranty)

---

## Step 5 — Write to docs/device_context.md

Once all answers are collected, write the Device Purpose section of `docs/device_context.md`.

Write the following blocks:

### Device Purpose block
```markdown
## Device Purpose

[One paragraph composed from Q1–Q4 answers. Must name: what the device does,
who depends on it, the hardest scenario (project target), and both failure modes
with their consequences.]

**Project target:** [Q3 answer in one sentence — the specific hard case]

**Pass/fail threshold:** [Q5 answer]

**Domain primitives** (traces to Article I):
1. [Primitive 1] ([unit]) — [description]
   Measured via: [signal(s)]
2. [Primitive 2] ([unit]) — [description]
   Measured via: [signal(s)]
3. [Primitive 3] ([unit]) — [description, if applicable]
   Measured via: [signal(s)]

**Operating envelope:**
- Normal: [Q6 answer]
- Worst-case: [Q7 answer]
- Out-of-scope: [Q8 answer]
```

### Signal Inventory block
Write a Signal Inventory section to `docs/device_context.md`:

```markdown
## Signal Inventory

| Signal | Physical quantity | Unit | Normal range | Hard limits | Sample rate | Primitive |
|--------|-----------------|------|--------------|-------------|-------------|-----------|
| [name] | [quantity]       | [u]  | [min – max]  | [limits]    | [Hz]        | [P1/P2/P3] |
```

---

## Step 6 — Draft Amendment 1

After writing to device_context.md, draft Amendment 1 for the human to ratify.

Print the draft — do NOT write it to amendments.md yet. The human ratifies it explicitly.

```
### PROPOSED AMENDMENT 1: Domain Primitives — [Device Name]
Proposed by: spec-collector
Date: [today]
Traces to: Article I

Governing rule (one sentence):
Every threshold, filter cutoff, FSM transition, and algorithm parameter in this
project must trace to one of the following domain primitives. A parameter that
cannot be so traced is a guess and is not permitted.

Domain primitives:
  1. [Primitive 1] ([unit]) — [description]
  2. [Primitive 2] ([unit]) — [description]
  3. [Primitive 3] ([unit]) — [description, if applicable]

Physical or process justification:
[One paragraph: why these primitives and not others. Cite the project target
and the hardest operating scenario as the justification.]

Amendment it complements or constrains:
  Precedes all other Amendments — all subsequent Amendments must be consistent
  with these primitives.

What happens without it:
  Parameters are set by intuition or by fitting to data, with no traceable
  physical basis. Article I cannot be enforced.
```

Ask the human: "Do you ratify Amendment 1? (yes / no / revise)"
- If yes: write the amendment to `docs/governance/amendments.md` and print a confirmation.
- If revise: ask what to change, revise, and ask again.
- If no: discard and note that Amendment 1 must be ratified before /session 0 can run.

---

## Step 7 — Print readiness summary

```
══════════════════════════════════════════════════════════════
SPEC COLLECTION COMPLETE
══════════════════════════════════════════════════════════════
Device Purpose    : written to docs/device_context.md ✓
Signal Inventory  : [N] signals recorded ✓
Domain Primitives : [N] primitives extracted ✓
Amendment 1       : [RATIFIED / PENDING RATIFICATION]
══════════════════════════════════════════════════════════════
Next steps:
  1. Run /toolchain init  — register hardware, pins, and libraries
  2. Ratify Amendments 2–4 (Stage Gate, Toolchain Alignment, Three-Strike)
  3. Run /session 0       — HIL Toolchain Lock
══════════════════════════════════════════════════════════════
```

---

## Subcommand: /spec review

Read `docs/device_context.md` and check for gaps. Flag:

- **MISSING** — section is a placeholder, not filled in
- **VAGUE** — Device Purpose has no specific project target or failure mode consequences
- **NO THRESHOLD** — pass/fail threshold is missing or stated qualitatively ("works well")
- **SIGNAL GAP** — a signal is listed in toolchain_config.md (Pin Map) but not in Signal Inventory
- **PRIMITIVE MISMATCH** — a signal's Primitive column does not match any named primitive
- **STALE** — Operating Envelope references conditions that conflict with current toolchain_config.md

Print a gap table, then state which gaps block /session 0 (hard blockers) vs which are warnings.

---

## Subcommand: /spec signals

Skip the full interview. Ask for additional signals to add to the Signal Inventory table in
`docs/device_context.md`. Use the same per-signal questions from Step 2.
Write to the table and confirm what was added.

---

## Subcommand: /spec target

Read the current Device Purpose section. Ask:
"What has changed about the project target since this was written?"
Update only the Project Target and Pass/Fail Threshold lines.
Do not re-interview on primitives or signals unless the human says the target change
requires primitive changes (which would require Amendment revision).

Now parse "$ARGUMENTS" and run the matching subcommand, defaulting to `collect` if empty.
