---
name: descent-reflex-fix-2026-08-11
description: Franka acceleration-discontinuity reflex on descent — per-leg _safe_traj fix ported from experiment2 to all experiment1 run_trial.py on 2026-08-11
metadata: 
  node_type: memory
  type: project
  originSessionId: 923b8ca9-f1ab-4cb2-a5b8-034e144d327e
  modified: 2026-08-11T21:10:45.686Z
---

2026-08-11: finray_18 E1 zero-tilt session crashed with libfranka reflex
`cartesian_motion_generator_joint_acceleration_discontinuity` during the final
sine descent. Root cause: experiment1 run_trial.py still used multi-waypoint
`_smooth_through` for bulk descent (acceleration mismatch at interior
waypoints leaves EE ~0.7 mm off-target → controller inserts a ramp-up segment
whose junction reflexes). The fix (per-leg 2-waypoint `_safe_traj` cosine
S-curves, zero vel+accel at endpoints) went into experiment2 scripts on
2026-06-26 23:00 but was never back-ported. On 2026-08-11 the Phase A block
was ported into all six experiment1 variant scripts; originals kept as
`run_trial.py.bak_20260811`. experiments/ is NOT git-tracked ([[never-rm-without-double-confirm]]).

**Why:** any future edit to descent/trajectory logic must go into BOTH
experiment1 and experiment2 script sets — they are parallel copies, not shared.

**How to apply:** after a reflex crash, ros2_control_node dies and the launch
tears down franka_gripper_node — subsequent "grasp action not available"
errors are a consequence, not a separate bug. Restart via [[franka-fci-launch]].
