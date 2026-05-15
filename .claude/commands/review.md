Invoke audit agents to review code, documentation, or governance records.

Usage: /review <code|doc|gov> [focus]

Subcommands:
  code [focus]   — Article I traceability, FSM integrity, filter chain, unit checks
  doc  [focus]   — documentation completeness, staleness, cross-doc consistency
  gov  [focus]   — governance record consistency (amendments vs case law)

code focus options:
  article1   — Article I traceability only (every threshold traces to a domain primitive)
  filters    — filter chain coherence only (cutoffs, Nyquist, DC paths)
  fsm        — FSM structural integrity only (dead states, unreachable states, ambiguous transitions)
  units      — unit consistency only (caller/callee mismatches, undocumented conversions)
  amend7     — Amendment 7 calibration documentation only
  (none)     — full review across all categories

doc focus options:
  device     — docs/device_context.md only
  toolchain  — docs/toolchain_config.md only
  governance — amendments.md and case_law.md only
  cross      — cross-document consistency checks only
  (none)     — full review across all docs

gov focus options:
  amendments  — amendment health only (orphaned, superseded, stale, malformed)
  case-law    — case law health only (orphaned, frozen conflicts, missing fields, unimplemented)
  toolchain   — toolchain config vs Amendment 3 alignment only
  index       — amendment index accuracy only
  citations   — source code amendment citation checks only
  (none)      — full audit across all categories

Examples:
  /review code
  /review code article1
  /review code fsm
  /review doc governance
  /review doc cross
  /review gov
  /review gov amendments
  /review gov case-law

If no subcommand given, print this usage and stop.

---

## code subcommand

Constitutional grounding:
  Article I  — all thresholds must trace to domain primitives
  Amendment 1 — domain primitives are the evidence base for every finding
  Amendment 7 — calibration constants require derivation documentation
  Amendment 11 — src/ scaffold modules are frozen after Stage 1 gate

Reads before reviewing:
  docs/governance/amendments.md     — domain primitives and calibration amendments
  docs/device_context.md            — Signal Inventory (expected units and ranges)
  docs/toolchain_config.md          — active firmware repo and source file paths
  firmware source files             — from registered repo

Blocks stage gate if:
  Any ARTICLE-I-VIOLATION or FSM-DEAD-STATE is found.
  Each finding requires a Bill before /session can advance.

If Amendment 1 has not been ratified, print:
  "Amendment 1 not ratified — domain primitives undefined.
   Run /spec collect before code review."

---

## doc subcommand

Constitutional grounding:
  Amendment 2 — each closed stage must have test data recorded
  Amendment 3 — toolchain_config.md must be consistent with active toolchain record
  Amendment 6 — closed Stage 1 requires signal plots recorded in Test Results

Severity levels:
  BLOCKER  — blocks /session stage advance
  WARNING  — should fix before gate, does not hard-block
  INFO     — completeness gap, low urgency

Run before:
  Any stage gate (/session status)
  /compact (ensures compaction has complete source material)
  /hear (attorneys need a complete evidence base)

---

## gov subcommand

Constitutional grounding:
  All Articles and Amendments — this agent audits the entire governance record
  Amendment 3 — toolchain alignment is a hard check
  Amendment 4 — three-strike violations may appear as unrecorded case law entries

Highest-severity finding:
  CONFLICT — a frozen precedent contradicts a live amendment.
  All CONFLICT findings require a /hear before the next stage gate.

Run before:
  /compact all (ensures compaction operates on a consistent record)
  Any stage gate where governance questions exist
  After ratifying new amendments (to catch index gaps)

---

Now parse "$ARGUMENTS":
  First word is the subcommand: "code", "doc", or "gov"
  Remaining words are the focus (optional)
  Invoke the code-reviewer agent for "code"
  Invoke the doc-reviewer agent for "doc"
  Invoke the constitution-auditor agent for "gov"
  Pass the focus as the argument to the agent.
