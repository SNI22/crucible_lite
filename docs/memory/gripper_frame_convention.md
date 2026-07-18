---
name: gripper-frame-convention
description: Franka Hand EEF frame — gripping (jaw-closing) direction is y; mirror plane is xz; asymmetric tilt axis is rotation about y
metadata: 
  node_type: memory
  type: project
  originSessionId: 923b8ca9-f1ab-4cb2-a5b8-034e144d327e
---

EEF frame convention for the FR3 + Franka Hand + finray setup, locked
2026-06-04:

- **z** = approach axis (gripper-down direction; toward the cloth/table).
- **y** = jaw-closing direction. The two fingers / finray blades move
  along ±y. (Matches the Franka Hand URDF's `fr3_finger_joint1/2`
  prismatic axis in the `fr3_hand` frame.)
- **x** = the third axis (perpendicular to gripping and approach;
  along the gripping line at the tip).

The gripper is **mirror-symmetric across the xz plane** (the plane
perpendicular to y), because reflecting across xz swaps the +y and
−y fingers, which are identical.

### Tilt-axis consequences (resolves [[experiment-matrix-locked]] Open Item 1)

- **Rotation about x**: symmetric (mirror-equivalent to its negative).
  Levels {0, 2.5, 5°}.
- **Rotation about z**: symmetric. Levels {0, 2.5, 5°}.
- **Rotation about y** (the gripping direction): **physically
  asymmetric** — both fingers tilt together fore/aft about the
  gripping line; one direction noses into the cloth body, the other
  off the edge. **By operator directive 2026-06-04**, the experiment
  matrix tests y single-sided at {0, 2.5, 5°} (into the cloth body
  direction). The −y side is a follow-up question if motivated by data.

### Inclined-seat sub-study (Study 3)

The finray inclined-seat fixtures geometrically bias the y-axis tilt.
The Option-B asymmetric-axis slice in Study 3 is therefore the y-axis
sweep, with the seat angle as a between-fixture offset that should
shift the tilt-tolerance curve along the same axis.

### How to apply

Whenever code or docs reference "the asymmetric tilt axis," "the
gripping direction," or "the gripper mirror plane," resolve to:
y / y / xz respectively. The `STUDY2_TILT_LEVELS_DEG_SYM` (for x and
z) and `STUDY2_TILT_LEVELS_DEG_ASYM` (for y) defaults in
`sweep_runner.py` (Bill 0005, Change 1) follow this convention.
