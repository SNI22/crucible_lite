---
name: fext-contact-force-pivot
description: Franka built-in F_ext is the first-pass Contact Force source while the A301 arrays are blocked
metadata: 
  node_type: memory
  type: project
  originSessionId: 923b8ca9-f1ab-4cb2-a5b8-034e144d327e
---

Since 2026-05-22, the cloth-grasp experiments use the Franka built-in **F_ext**
(`external_wrench_in_base_frame`, flange) as the first-pass Contact Force
estimate, because the A301 calibration is blocked ([[calibration_blocked_repeatability]]).
F_ext is Amendment-1-sanctioned (Signal Inventory row 7).

Key facts:
- It is a model-based flange wrench, NOT per-contact force, and lumps
  table-contact + grip + dynamics into one resultant.
- It has a **pose-dependent bias** (~1.6 N near home, up to ~5 N at far-out
  poses) — subtract the `init` free-air mean per run before comparing.
- The **Franka Hand gripper reports NO force** (libfranka GripperState has no
  force field; driver hard-codes joint_states effort to 0; Grasp action returns
  only success). The only gripper force is the commanded value (20 N),
  unmeasured. A measured pinch force needs the A301-25 pads (blocked).

Control/experiment code lives in sim2real_adlros/experiments/cloth_grasp/
(imports arm_client; runs on the FR3), NOT in this repo.
