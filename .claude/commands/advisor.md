Invoke the hw-advisor or sw-advisor agent to review hardware or algorithm design decisions.

Usage: /advisor <hw|sw> [focus]

Subcommands:
  hw [focus]   — hardware design suggestions grounded in test results and BOM
  sw [focus]   — algorithm suggestions grounded in simulation profile evidence

hw focus options:
  bom          — component selection review against test results
  pins         — pin assignment conflicts or sub-optimal choices
  signal       — signal integrity issues (impedance, noise floor, filtering)
  power        — power budget and supply issues
  enclosure    — mechanical issues affecting signal quality
  (none)       — full review across all categories

sw focus options:
  detect    — trigger conditions and FSM transition logic
  filter    — LP/HP filter chain design (cutoff, order, chain)
  segment   — phase segmentation (stance/swing/push-off/heel-strike boundaries)
  metric    — derived metric computation (SI, cadence, symmetry indices)
  fsm       — state machine structure and state transition guards
  (none)    — full review across all categories

Examples:
  /advisor hw
  /advisor hw bom
  /advisor hw enclosure
  /advisor sw detect
  /advisor sw filter
  /advisor sw

If no subcommand given, print this usage and stop.

---

## hw subcommand

Reads before advising:
1. docs/device_context.md — Device Purpose, BOM, Circuit Notes, Test Results, Open Anomalies
2. docs/toolchain_config.md — hardware record, pin map, blocked toolchains
3. docs/governance/amendments.md — domain primitives and stage gate record

If docs/device_context.md is missing or its Test Results section contains no entries, print:
  "No test data available. Populate docs/device_context.md (Test Results section) after
   completing Stage 0 and at least one of Stage 1–3 before hw-advisor can produce
   evidence-based suggestions. Run /session 0 to start."

For each suggestion, produce:

### Suggestion [N]: [Title]

**Evidence base:**
[The specific test result, UART log line, or field measurement that prompted this suggestion.
No evidence = no suggestion. This line is mandatory.]

**Physical root cause:**
[What physical phenomenon is causing the observed result.
Must trace to a domain primitive per Article I.]

**Proposed change:**
[Specific component, value, pin assignment, or enclosure modification.
Stated precisely enough to act on without further clarification.]

**Expected improvement:**
[What measurable change in the domain primitive output is expected.
Stated in the same units as your domain primitives.]

**Bill required:** yes / no

**Risk if not addressed:**
[What happens if this suggestion is not implemented.]

hw-advisor never suggests a change it cannot trace to a specific test result (Article I).
hw-advisor never approves its own suggestions (Article II — every suggestion is a proposed Bill).

---

## sw subcommand

Reads before advising:
1. docs/device_context.md — Device Purpose, Domain Primitives, Signal Inventory, Test Results
2. docs/governance/amendments.md — domain primitive definitions and algorithm-relevant amendments
3. docs/toolchain_config.md — signal names, sample rates, pin assignments, active firmware repo
4. Any algorithm source files found under the registered firmware repo (from toolchain_config.md)

If docs/device_context.md is missing or its Test Results section contains no simulation profiles, print:
  "No simulation profiles available. Run /plot evidence sim <profile> after completing
   Stage 1 simulation before sw-advisor can produce evidence-based suggestions."

For each suggestion, produce:

### Suggestion [N]: [Title]

**Evidence base:**
[The specific signal measurement, profile comparison, or simulation run that prompted this.
Cite the profile name, signal name, and observed value. No evidence = no suggestion.]

**Signal-level root cause:**
[What the signal is doing in physical terms that causes the algorithm to fail.
Must trace to a domain primitive per Article I.]

**Proposed change:**
[Specific change to FSM condition, filter parameter, threshold, or phase boundary.
State the change precisely: old condition → new condition.]

**Expected improvement:**
[What measurable change in algorithm output is expected, in terms of the domain primitive.]

**Bill required:** yes / no

**Risk if not addressed:**
[What domain primitive degrades, and by how much, if this is not fixed.]

sw-advisor never proposes a threshold value without tracing it to a domain primitive (Article I).
sw-advisor never approves its own suggestions (Article II — every suggestion is a proposed Bill).

---

Now parse "$ARGUMENTS":
  First word is the subcommand: "hw" or "sw"
  Remaining words are the focus (optional)
  Invoke the hw-advisor agent for "hw", the sw-advisor agent for "sw"
  Pass the focus as the argument to the agent.
