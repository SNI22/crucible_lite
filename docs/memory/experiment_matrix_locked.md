---
name: experiment-matrix-locked
description: Locked tilt × depth experiment matrix for the 4-gripper soft-vs-rigid cloth-grasp benchmark (≈ 280 trials)
metadata: 
  node_type: memory
  type: project
  originSessionId: 923b8ca9-f1ab-4cb2-a5b8-034e144d327e
---

Experiment plan locked 2026-06-03 in `docs/experiment.md`
(commit `b074018` on branch `cloth_grasp`). Three blocks across four
grippers: G1 parallel jaw (rigid), G2 parallel jaw + TPU 90 A pad,
G3 finray 33 mm, G4 finray 18 mm.

- **Pilot** (per gripper, ~35 total): P1 touch-off → per-gripper TCP
  offset (see [[per_gripper_tcp_via_touchoff]]); P2 max-depth escalation
  → `max_depth_safe`; P3 success-threshold scan → `d_min_success`.
- **Study 1** (depth × tilt = 0, 78 trials): force-vs-depth curve.
  G1/G2 depths −1..5 mm × 3 reps; G3/G4 depths −1..8 mm × 3 reps.
  Sweep runner: `sim2real_adlros/experiments/cloth_grasp/{parallel_jaw,finray}/sweep_runner.py`.
- **Study 2** (tilt × depth, 168 trials): tilt about the
  per-gripper contact point. Levels 0, 2.5, 5° on each axis (one axis
  at a time). Two depths per gripper: `d_min` and `d_safe`.

**Why:** publishable-quality soft-vs-rigid comparison needs depth and
tilt characterization, not just the preliminary single-depth result
from 2026-05-22 ([[soft-vs-rigid-preliminary]]).

**How to apply:** when running experiments, follow the matrix; when
asked about progress, frame it as pilot / Study 1 / Study 2 blocks.

Open items (in `docs/experiment.md`): confirm which EEF axis is the
gripping direction (drives which tilt axis is asymmetric → ±5°
instead of +0/+2.5/+5°); `GRASP_WIDTH_M` for finray 18 mm; whether
to empirically validate gripper mirror symmetry on G1.
