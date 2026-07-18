# Bill 0006 — Franka FCI Launch Procedure (Session Pre-flight)

**Status:** PROPOSED 2026-06-04
**Branch:** `bill/fci-launch-procedure`
**Change type:** governance / toolchain (Standing Order amendment —
session pre-flight checklist for the FR3)
**Proposed by:** sni22
**Traces to:** Article II (Human in the Loop — operator action required
before any robot motion), [[franka-fci-launch]].

---

## Problem

Every cloth-grasp session starts with the dev machine running scripts
in the `sim2real_adlros` pixi env that consume the `arm_client` API
(`Robot`, `Gripper`). These scripts depend on the Franka Control
Interface (FCI) being active on the realtime PC `franka-pc`. If the
FCI is not active, every motion script hangs silently at
`wait_until_ready` — there is no signal in the script output that
explains why. Newcomers (or returning operators after a context gap)
have wasted time chasing a software bug that was actually a missing
toolchain step.

This Bill formalises the pre-flight as a documented Standing Order, so
it appears in the toolchain config and is loaded into agent memory
([[franka-fci-launch]]) for future sessions.

---

## Proposed change

### Clause (a) — Add Standing Order: "FCI Activation"

A new Bureaucracy Standing Order is added to the cloth-grasp project
governance. Procedure, performed **once at the start of every session**
before any arm_client-using script is launched:

1. **SSH to the realtime PC:**
   ```
   ssh franka-pc
   ```
2. **Launch FCI on the realtime PC:**
   ```
   fr3-launch
   ```
3. Leave the `fr3-launch` process running for the duration of the
   session. Re-launch if the connection drops or the process exits.

The procedure is operator-executed and human-gated (Article II).
No agent or script may invoke `ssh franka-pc` or `fr3-launch`
autonomously.

### Clause (b) — `docs/toolchain_config.md` addition

A new section is added to `docs/toolchain_config.md`:

```
## Session pre-flight — FCI activation

Before any arm_client script (Robot, Gripper) runs on the dev machine,
the FCI must be active on the realtime PC `franka-pc`:

  ssh franka-pc
  fr3-launch

A hung wait_until_ready in any motion script is almost always this
step missing or the fr3-launch process having exited. Re-SSH and
re-launch.

Scripts that depend on this:
  experiments/cloth_grasp/experiment1/<variant>/ground_truth_finder.py
  experiments/cloth_grasp/experiment1/<variant>/run_trial.py
    (variants: parallel_jaw_stock, parallel_jaw_TPU, finray_33, finray_18)
  experiments/cloth_grasp/<family>/probe_surface.py
  experiments/cloth_grasp/<family>/cloth_pick_place_AtoB.py
  experiments/cloth_grasp/<family>/monitor_gui.py
    (families: parallel_jaw, finray)
```

### Clause (c) — Diagnostic note in `run_trial.py` / `ground_truth_finder.py`

The two operational scripts gain a one-line tip in their startup
banner: if `wait_until_ready` doesn't return promptly, suggest the
FCI launch procedure.

(Implementation is a small `try ... except TimeoutError` around
`wait_until_ready` printing a hint. Optional; the Standing Order +
toolchain_config text are the substantive deliverables of this Bill.)

---

## Article / Amendment grounding

- **Article II (Human in the Loop):** The FCI launch is an
  operator-executed action whose effect is to enable real-robot
  motion. Encoding it as a Standing Order (operator pre-flight)
  matches Article II's intent — humans gate the path from script to
  motion.
- **No Amendment violated:** This Bill is additive (a new Standing
  Order + a toolchain_config section + a one-line diagnostic). No
  existing Amendment scope is altered.

---

## Physical evidence

| Observation | Source |
|---|---|
| `wait_until_ready` hangs indefinitely when FCI is not activated | Operator-reported, 2026-06-04 |
| `ssh franka-pc` + `fr3-launch` is the locked recovery procedure | Operator confirmation, 2026-06-04 |
| The hang is silent — script output gives no diagnostic | Source review of `arm_client.robot.Robot.wait_until_ready` (consumes ROS service availability; no FCI-status hook) |

This is operator-level operational knowledge, not a measurement
deficit. The evidence is the observed failure mode and the operator's
confirmation of the recovery.

---

## Expected outcome

After enactment:

1. `docs/toolchain_config.md` carries the FCI launch procedure under
   a "Session pre-flight" section — discoverable by anyone reading the
   toolchain docs.
2. Agent memory ([[franka-fci-launch]]) carries the same procedure as
   a reference-type memory loaded into every future session — so when
   an operator returns after a break and asks "how do I start the
   robot," the agent answers correctly without having to re-derive
   from session logs.
3. (Optional Clause (c) implementation) New `run_trial.py` /
   `ground_truth_finder.py` invocations show a hint line if their
   `wait_until_ready` takes longer than a short threshold.

Measurable in operational terms: **time-to-first-trial after a session
gap decreases** from "minutes of debugging silently-hung scripts" to
"30 seconds of two-command pre-flight."

---

## Rollback plan

| Component | Rollback |
|---|---|
| Standing Order text | `git revert` on this repo's `cloth_grasp` branch. |
| `docs/toolchain_config.md` section | `git revert`. The FCI procedure itself is a property of the FR3 + libfranka, not of this repo — removing the documentation doesn't change the underlying requirement. |
| `franka_fci_launch.md` memory entry | Delete the file + remove the line from `MEMORY.md`. |
| Clause (c) script hint | `git revert` on the sim2real_adlros workspace if implemented. |

No physical / hardware rollback. The procedure is governance and
documentation.

---

## Implementation surface

| Path | Status |
|---|---|
| `docs/governance/bills/0006-fci-launch-procedure.md` | NEW (this file) |
| `docs/toolchain_config.md` "Session pre-flight" section | EXTENDED at enactment |
| `~/.claude/projects/.../memory/franka_fci_launch.md` | NEW (saved 2026-06-04) |
| `~/.claude/projects/.../memory/MEMORY.md` index | EXTENDED (saved 2026-06-04) |
| `experiment1/<gripper>/run_trial.py` startup banner | EXTENDED if Clause (c) is implemented |
| `experiment1/<gripper>/ground_truth_finder.py` startup banner | EXTENDED if Clause (c) is implemented |

**No changes to:**

- `arm_client` (we add a startup hint AROUND it, not a change to it)
- Any motion script's behaviour mid-trial
- Any other Bill or governance record
