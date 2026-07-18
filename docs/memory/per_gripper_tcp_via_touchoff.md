---
name: per-gripper-tcp-via-touchoff
description: "Per-gripper TCP / contact-point z-offset comes from differential touch-off, not CAD measurement"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 923b8ca9-f1ab-4cb2-a5b8-034e144d327e
---

For the tilt test the rotation must pivot about the **contact point**,
which sits at a gripper-specific z-offset below the standard
`fr3_hand_tcp` (45 mm fingertip plane). The locked method for that
offset is **differential touch-off**, not a CAD measurement.

Probe the same (x, y) point with each gripper using
`probe_surface.py` (5 taps, 2 N threshold). The reported
`fr3_hand_tcp` z at contact differs across grippers by exactly the
tip-extension offset: `Δz = z_finray − z_jaw` is the finray's tip
length below the TCP, ready to use as the tilt-pivot / TCP offset.

**Why:** datum-free. CAD ("measure mount-to-tip from the screw-hole
center") suffers ambiguity over what plane the URDF's 58.4 mm
reference corresponds to AND the screw-hole geometry (the Franka
finger bolts onto a vertical mating face, so screws are perpendicular
to z, complicating "measure along the screw"). The touch-off
sidesteps both: it gives the effective offset directly in hardware,
no reference plane assumed.

**How to apply:**
- Before any tilt experiment, run `probe_surface.py` once per gripper
  at one common (x, y) and record each `table_ground_truth.json`.
- Compute `Δz_per_gripper = z_at_contact − z_reference` (pick any
  one gripper as reference; the relative offsets are what matter for
  the per-gripper TCP).
- Cross-check against any CAD estimate as a sanity number, not as
  the source of truth.

See [[experiment-matrix-locked]] (Pilot P1).
