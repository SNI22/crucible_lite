Declare a Judicial Hearing or draft a Bill under the Crucible Constitutional Governance system.

Usage: /judicial <hear|bill> [args]

Subcommands:
  hear "<name>" <position-A> vs <position-B>   — declare and run a Judicial Hearing
  bill <problem description>                    — produce a complete, debate-ready Bill

Examples:
  /judicial hear "step trigger" "acc-primary peak" vs "gyr-primary push-off crossing"
  /judicial hear "BLE MTU vs USB CDC" "BLE NUS primary — matches production path" vs "USB CDC primary — deterministic"
  /judicial hear "Arduino vs Zephyr re-evaluation" "unblock Zephyr — new overlay evidence" vs "keep Arduino — block stands"
  /judicial bill step detection fails on stairs — acc_filt peak delayed by 80ms under sigmoid loading
  /judicial bill replace soft TPU enclosure — heel-strike transient attenuated below detection threshold

If no subcommand given, print this usage and stop.

---

## hear subcommand

Declares and runs a full Judicial Hearing. Implements CONSTITUTION.md Judicial Process §1–5.

### Step 1 — Warm the courtroom

Invoke the judicial-clerk agent immediately. It will:
- Verify agent roster (attorney-A, attorney-B, simulator-operator, plotter, uart-reader)
- Print COURTROOM READY before any argument begins

Do not proceed past Step 1 until judicial-clerk prints COURTROOM READY.

### Step 2 — Print hearing declaration

```
══════════════════════════════════════════════════════════════
JUDICIAL HEARING DECLARED
Hearing: <hearing name>
Position A: <position-A-description>
Position B: <position-B-description>

Constitutional grounding to check before arguing:
  docs/governance/amendments.md          — all ratified amendments
  docs/governance/case_law.md            — all recorded precedents
  CONSTITUTION.md Judicial Process §3–4  — Benjamin Franklin + Thomas Jefferson principles

Evidence base to read before arguing:
  docs/device_context.md                 — BOM, circuit notes, test results, signal measurements
  docs/toolchain_config.md               — active hardware, pin map, blocked toolchains, repo registry

Evidence commands available during this hearing:
  /plot evidence signal <profile>         — IMU signal plot
  /plot evidence sim <profile>            — full simulation evidence (UART + signal)
  /plot evidence uart <log_path>          — UART session output from Renode log
══════════════════════════════════════════════════════════════
```

### Step 2b — Advisory pre-brief (optional but recommended)

If the hearing topic involves algorithm or firmware logic:
  Suggest: "Run `/advisor sw detect` (or relevant focus) before attorneys argue."

If the hearing topic involves hardware, BOM, or enclosure:
  Suggest: "Run `/advisor hw` before attorneys argue."

### Step 3 — Assign attorneys and launch arguments (parallel)

Assign Attorney-A to Position A and Attorney-B to Position B (or reverse).
Launch both attorney agents in parallel. Each must:
1. Read docs/governance/amendments.md
2. Read docs/governance/case_law.md
3. Read docs/device_context.md — BOM, circuit notes, test results, signal measurements
4. Read docs/toolchain_config.md — hardware record and blocked toolchains
5. Read any source files directly relevant to their position
6. Present all four required argument elements:
   - Amendment(s) invoked (exact number and title)
   - Precedent (case name and date, or explicit statement of none)
   - Physical/clinical outcome protected
   - Consequences of opposing position in physical terms

### Step 4 — Evidence collection (if Justice requests it)

Use /plot evidence to generate requested evidence. Evidence commands run as Bureaucracy
Standing Orders — no Bill or hearing required.

### Step 5 — Clarifying questions (Justice only)

The Justice may ask each attorney one clarifying question.
Print each Q&A clearly labelled:
  JUSTICE → ATTORNEY-A: <question>
  ATTORNEY-A: <answer>

### Step 6 — Ruling

The Justice announces:
- Which position prevails
- The governing physical/empirical basis (Benjamin Franklin Principle)
- The device/hardware outcome protected (Thomas Jefferson Principle)
- Any conditions or constraints on how the ruling is applied

### Step 7 — Record to case law

The prevailing attorney writes the ruling to docs/governance/case_law.md
using the standard case law template. This is a hard gate — implementation cannot
start until the ruling is recorded.

After the ruling is recorded:
- If the ruling enacts a Bill that changes agent scope: invoke agent-updater with the Bill name.
- The Justice reviews and applies any proposed agent edits before implementation begins.

Standard case law entry format:
```
### Case [N]: [Hearing Name]
**Date:** [date]
**Positions:** A — [description] | B — [description]
**Prevailing position:** [A or B]
**Justice's ruling:** [ruling text]
**Physical/empirical basis:** [evidence cited]
**Device outcome protected:** [Thomas Jefferson statement]
**Conditions:** [any constraints on application]
**Enacted bill (if any):** [bill name, or "none"]
**Implementation branch:** [branch name, or "none"]
```

### Nested Hearing Protocol

If a nested hearing must be declared during argument (Step 3–5):
1. Pause the current hearing — print PARENT HEARING PAUSED
2. Complete the nested hearing fully (Steps 1–7)
3. Resume parent hearing — print PARENT HEARING RESUMED
4. The child ruling is new evidence for the parent hearing; do not re-debate it

---

## bill subcommand

Invokes the bill-drafter agent to produce a complete, debate-ready Bill.

What bill-drafter does:
  1. Reads amendments, case law, device_context.md, and relevant source files
  2. Checks evidence gates (physical evidence must exist in the record)
  3. Identifies the correct amendment grounding
  4. Verifies the proposed change is specific and measurable
  5. Outputs a complete Bill or an INCOMPLETE report explaining what evidence is missing

Bill quality gates (all must pass before a Bill is output):
  Evidence gate    — physical evidence must exist in device_context.md or this session
  Amendment gate   — an Article or Amendment must authorise the change
  Outcome gate     — expected improvement must name a domain primitive and unit
  Scope gate       — proposed change must name specific files, functions, or values

After bill-drafter outputs the Bill:
  1. Review the Bill with the Justice
  2. Run /judicial hear "[Bill name]" to open debate
  3. After ruling, implement on the branch named in the Bill

Constitutional grounding:
  Article I  — Bill must trace to a domain primitive
  Article II — Bills are proposed; the Justice enacts
  Amendment 4 — three consecutive failures should trigger a Bill, not a fourth attempt

If no description given for bill subcommand, print usage and stop.

---

Now parse "$ARGUMENTS":
  First word is the subcommand: "hear" or "bill"
  For "hear": invoke the judicial-clerk agent, then run the 7-step hearing procedure.
    Parse remaining args as: first quoted string = hearing name,
    text after first "vs" = position B, text between name and "vs" = position A.
    If parsing fails, print usage and stop.
  For "bill": invoke the bill-drafter agent with the remaining text as the problem description.
    If no description given, print usage and stop.
