---
name: soft-vs-rigid-preliminary
description: Preliminary benchmark result — soft finray grips cloth at ~half the contact force of the rigid parallel jaw
metadata: 
  node_type: memory
  type: project
  originSessionId: 923b8ca9-f1ab-4cb2-a5b8-034e144d327e
---

First soft-vs-rigid result (2026-05-22, F_ext-based, preliminary):
**the soft UMI finray grasps thin cloth at ~17 N (succeeds from -1 mm press
depth); the rigid parallel jaw needs ~33 N (succeeds from 2.5 mm).** So the
finray grips at roughly **half the contact force** — the soft-grasper advantage
the benchmark exists to show (benchmark metric 5, min grasp force).

Caveats: F_ext (flange) estimate, bias-corrected per run, not per-contact;
compare by FORCE not raw depth (taught surfaces differ, finray's was ~1.5 mm
high); ~1 run/depth so no true repeatability bars yet (only finray -1 mm has a
clean pair). Finray force is noisy within a grasp (std ~5-7 N, compliance);
rigid is steady (~0.5 N). Lift-off force spikes (~45-49 N) are dynamic
transients, NOT table load.

Data + plots: sim2real_adlros/experiments/cloth_grasp/{parallel_jaw,finray}/
and docs/results/2026-05-22_finray_vs_parallel_jaw/. See [[fext_contact_force_pivot]].
