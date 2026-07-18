# Bill 0005 — Cloth-Grasp Benchmark Sweep Scripts

**Status:** PROPOSED 2026-06-04
**Branch:** `bill/cloth-grasp-sweep-scripts`
**Change type:** software (orchestration scripts that operate the FR3
for the Pilot, Study 1, Study 2, and Study 3 sweeps specified in
`docs/experiment.md`)
**Proposed by:** sni22
**Traces to:** Article I (Signal First), Article II (Human in the
Loop), Amendment 1 (Domain Primitives — Contact Force, End-Effector
Pose), [[experiment-matrix-locked]].

---

## Problem

`docs/experiment.md` (commit `b074018`) locks the cloth-grasp
benchmark matrix: Pilot (P1 touch-off, P2 max-depth escalation,
P3 success threshold), Study 1 (depth × tilt=0), Study 2
(tilt × depth), Study 3 (inclined-seat sub-study). Only the Study 1
depth-sweep orchestration exists today
(`sim2real_adlros/experiments/cloth_grasp/{parallel_jaw,finray}/sweep_runner.py`,
single-purpose). P2 and P3 reuse Study 1 by accident of similar shape;
Study 2 has no tilt implementation at all; Study 3 has no fixture-swap
workflow.

This Bill enacts the script work needed to operate the FR3 for the
full matrix, without changing the protocol (Study definitions,
metrics, BOM, etc. remain governed by `docs/experiment.md`).

---

## Proposed change

### Change 1 — Generalise `sweep_runner.py` (both gripper folders)

Extend the existing per-gripper `sweep_runner.py` with a `--study`
selector. Each value drives a different matrix iterator that calls
`run_pick_place` (Study 1/2/3) or `probe_surface.touchoff_once`
(Pilot P1).

```
--study pilot1   # touch-off, single (x, y), 5 reps, writes table_ground_truth.json
--study pilot2   # depth escalation, --repeats 1, abort-on-reflex
--study pilot3   # success-threshold scan, --repeats 3
--study 1        # current depth sweep (existing default)
--study 2        # tilt × depth sweep (requires Change 2)
--study 3        # Study 3 Option B: Study 1 sweep + asymmetric-axis tilt slice
```

The runner reads its per-trial matrix from gripper-default tables
inside the script:

```python
STUDY1_DEPTHS_MM = (-1, 0, 1, 2, 3, 4, 5) if config.GRASP_WIDTH_M is None else (-1, 0, 2, 4, 6, 8)
STUDY2_TILT_LEVELS_DEG = (0.0, 2.5, 5.0)  # all three axes, single-sided (operator directive 2026-06-04)
STUDY2_DEPTH_LABELS   = ("d_min", "d_safe")     # values resolved per-gripper from pilot JSON
STUDY3_FIXTURE_LABELS = ("S2.5", "S5")          # finray-only; operator confirms swap between blocks
```

All values overridable via CLI (`--depths`, `--tilts`, etc.). Default
selection by `config.GRASP_WIDTH_M` (None ⇒ parallel jaw).

### Change 2 — Add tilt-about-contact to `cloth_pick_place_AtoB.py`

Four new CLI arguments (with defaults equal to the current behaviour
so existing invocations are unchanged):

```
--rx <deg>                # tilt about base-frame x at the contact point (default 0)
--ry <deg>                # tilt about base-frame y at the contact point (default 0)
--rz <deg>                # tilt about base-frame z at the contact point (default 0)
--pivot-offset-z <m>      # contact-point offset BELOW fr3_hand_tcp (default 0)
```

In `run_pick_place`, before computing waypoints:

```python
import scipy.spatial.transform as st
R_tilt = st.Rotation.from_euler("xyz", [args.rx, args.ry, args.rz], degrees=True)
if (args.rx, args.ry, args.rz) != (0.0, 0.0, 0.0):
    # Orientation: pre-multiply (compose tilt with the base orientation).
    orient = R_tilt * orient
    # Position correction so the contact point stays at (A_xy.x, A_xy.y, surf_a):
    # TCP_target = contact_point + R_tilt @ [0, 0, pivot_offset_z]
    offset = R_tilt.apply(np.array([0.0, 0.0, args.pivot_offset_z]))
    A_xy = A_xy + np.array([offset[0], offset[1], 0.0])
    B_xy = B_xy + np.array([offset[0], offset[1], 0.0])
    # Vertical descent in base frame is preserved (acceptable for |tilt| ≤ 5°).
```

When all three tilt args are zero, the code path is identical to today
(no behavioural change). `pivot_offset_z` is read by the runner from
the Pilot P1 touch-off JSON per gripper.

### Change 3 — Per-trial metadata fields

`sweep_runner.py` writes the following additional fields into each
trial's `run_config.json`:

```json
{
  "tilt_deg": {"rx": 0.0, "ry": 0.0, "rz": 0.0},
  "pivot_offset_z_m": 0.0,
  "fixture_label": null,                 // "S2.5" | "S5" for Study 3
  "depth_label": null,                   // "d_min" | "d_safe" for Study 2/3
  "study": "1"                           // "pilot1" | "pilot2" | "pilot3" | "1" | "2" | "3"
}
```

All fields appear with `null` / zero defaults for backward compatibility
with already-captured trial directories.

### Change 4 — Operator interaction for fixture swaps (Study 3)

For `--study 3`, the runner pauses between fixture blocks with an
explicit prompt:

```
=== FIXTURE SWAP ===
Mount fixture: S5 (finray 33 mm on 5° inclined seat)
Type READY when the swap is complete and the gripper is re-homed.
```

After READY is typed, the runner re-runs `probe_surface.touchoff_once`
at the canonical (x, y) to refresh the touch-off z for the new
fixture; the refreshed Δz is used as `pivot_offset_z` for the
subsequent block.

### Change 5 — Consolidated results.json schema

A consolidated `results.json` is written at sweep end and after every
trial (resumable record). One entry per attempted trial; new fields
absent from Phase A:

```json
{
  "trial": <int>,
  "study": "<string>",
  "depth_mm": <float>,
  "rep": <int>,
  "rx_deg": <float>, "ry_deg": <float>, "rz_deg": <float>,
  "pivot_offset_z_m": <float>,
  "fixture_label": "<string or null>",
  "depth_label": "<string or null>",
  "status": "completed" | "aborted" | "error" | "skipped",
  "success": true | false | null,
  "error": "<string or null>",
  "data_dir": "<relative path>"
}
```

---

## Article / Amendment grounding

- **Article I (Signal First):** Every trial logs Contact Force (F_ext,
  Amendment 1 row 7) and End-Effector Pose (Amendment 1 row 2) at
  30 Hz to the trial's `pose_wrench.csv`. No threshold or tilt level
  in the runner is set without a citation in `docs/experiment.md`.
- **Article II (Human in the Loop):** Every trial confirms with the
  operator before motion (unless `--yes`); every trial's grasp outcome
  is operator-rated; Study 3 fixture swap is human-gated by the READY
  prompt (Change 4). e-stop in hand throughout.
- **Amendment 1 (Domain Primitives, RATIFIED 2026-05-14):** Contact
  Force (Primitive 1) and End-Effector Pose (Primitive 2) are the only
  signals consumed by these scripts; both are logged and exported.

This Bill is required because Change 2 adds new motion-shaping logic
(tilt-about-contact-point) and Change 1 adds new measurement stages
(P2 escalation, Study 2, Study 3) — both fall under "Software pipeline
(new stage, new metric)" per CLAUDE.md, requiring a Bill.

---

## Physical evidence

| Artefact | Path / link | What it shows |
|---|---|---|
| Locked experiment matrix | `docs/experiment.md` | The conditions these scripts must iterate. |
| Existing Phase A runner | `sim2real_adlros/experiments/cloth_grasp/{parallel_jaw,finray}/sweep_runner.py` | Working Study 1 orchestration this Bill generalises. |
| Existing pick-place state machine | `sim2real_adlros/experiments/cloth_grasp/{parallel_jaw,finray}/cloth_pick_place_AtoB.py` | The `run_pick_place` entry point Change 2 extends. |
| Existing touch-off implementation | `…/{parallel_jaw,finray}/probe_surface.py` | `touchoff_once` reused by `--study pilot1`. |
| F_ext as Contact Force source | session_log 2026-05-22, [[fext-contact-force-pivot]] | Establishes the primitive these scripts log. |

---

## Expected outcome

Measurable in primitive terms, not code metrics:

1. `--study pilot1` produces one
   `docs/calibration/per_gripper_tcp/<gripper>_<date>.json` per
   gripper, with `z_ground_truth_m` (mean) and `z_std_m` (≤ 0.3 mm
   per the 2026-05-22 touch-off baseline).
2. `--study pilot2` produces a `max_depth_safe` per gripper recorded
   in the per-gripper pilot JSON, defined as `max(depth_completed) − 1 mm`.
3. `--study pilot3` produces a `d_min_success` per gripper —
   shallowest depth with ≥ 2/3 reps passing.
4. `--study 1` produces a per-gripper `F(d)` table with ≥ 3 reps per
   depth (n ≥ 3 enables a Student-t SE bar — superior to the n = 1
   2026-05-22 preliminary).
5. `--study 2` produces a per-gripper × per-axis × per-depth grid of
   (success, F-at-grasp) values with ≥ 3 reps per condition; the
   commanded tilt at the contact point matches the achieved tilt
   within 0.5° (verifiable from the per-trial CSV's quaternion).
6. `--study 3` produces seat-shift `Δθ` data: tilt-tolerance
   curves for G3-S2.5 and G3-S5 (and G3 flat as the free 0°
   reference), enabling the seat-as-passive-correction hypothesis to
   be tested.

All outcome JSON / CSV files conform to the Change 3 / Change 5 schema.

---

## Rollback plan

| Component | Rollback |
|---|---|
| `sweep_runner.py` (both folders, in sim2real_adlros) | `git revert` on that workspace. The Phase A invocation (no `--study` flag) remains the default behaviour, so already-collected sweeps are unaffected. |
| `cloth_pick_place_AtoB.py` tilt args (Change 2) | `git revert` on that workspace. With tilt args defaulting to 0, the pre-Bill code path is preserved — existing invocations work unchanged. |
| `docs/governance/bills/0005-cloth-grasp-benchmark-protocol.md` | `git revert` on this repo's `cloth_grasp` branch. |
| Acquired data | Stays on disk. Each trial's `run_config.json` records the script revision (commit hash, Change 3) so admissibility is traceable. |

No firmware, no toolchain, no hardware modification in this Bill (the
inclined-seat fixtures of Study 3 are governed by a separate BOM
process — see `docs/experiment.md` Open Item 4).

---

## Implementation surface

**Modified:** `sim2real_adlros/experiments/cloth_grasp/parallel_jaw/sweep_runner.py`
**Modified:** `sim2real_adlros/experiments/cloth_grasp/finray/sweep_runner.py`
(byte-identical between the two folders, mirroring the existing pattern)

**Modified:** `sim2real_adlros/experiments/cloth_grasp/parallel_jaw/cloth_pick_place_AtoB.py`
**Modified:** `sim2real_adlros/experiments/cloth_grasp/finray/cloth_pick_place_AtoB.py`
(byte-identical; Change 2 adds 4 CLI args + a `R_tilt` block in `run_pick_place`)

**New:** `docs/calibration/per_gripper_tcp/` (directory created on
first `--study pilot1` invocation; one JSON per gripper)

**New:** `docs/calibration/per_gripper_pilot/` (directory created on
first `--study pilot2`/`pilot3` invocation; one JSON per gripper)

**No changes to:**

- `probe_surface.py` (consumed as a library by `--study pilot1`)
- `config.py` (per-gripper; values stay; new defaults live in the
  runner)
- `monitor_gui.py`, `status_bus.py`
- Any file in `src/calibration/` (Bills 0002/0003/0004 surface —
  untouched)
- `docs/toolchain_config.md` Channel & Topic Map
- `arm_client` (read-only API consumer)

Implementation begins on branch `bill/cloth-grasp-sweep-scripts` after
this Bill is committed. Order of work:

1. Change 2 (tilt args + math in `cloth_pick_place_AtoB.py`) — small,
   verifiable in isolation against a teach-mode capture.
2. Change 1 (runner `--study` selector) layered on Change 2.
3. Change 4 (fixture-swap UX) folded into the runner.
4. Changes 3 / 5 (schema fields) — pure metadata, last.

Each step lands as its own commit on the branch; the branch merges to
`cloth_grasp` only after `--study 1` (the unchanged default behaviour)
has been re-run end-to-end and the resulting `results.json` validates
against the Change 5 schema.
