---
name: e3-inclined-demo-2026-08-12
description: "Experiment 3 (Bill 0009 DRAFT): inclined-surface success-only demo; scripts scaffolded in sim2real experiment3/ on 2026-08-12"
metadata: 
  node_type: memory
  type: project
  originSessionId: 923b8ca9-f1ab-4cb2-a5b8-034e144d327e
  modified: 2026-08-14T00:45:43.921Z
---

Bill 0009 (DRAFT, docs/governance/bills/0009-inclined-surface-demo.md, not
yet enacted): E3 inclined-surface grasp demo — wedge 4.15° (SURFACE_RISER STEP CAD, verified from top-face normal geometry, not the earlier 5.0° placeholder) with slope along
gripping direction y; BLIND flat-assumption touch-off calibration; single
press at touch-off +0.5 mm; success/no-grasp only (force logged, not
reported); pilot = ALL SIX variants × 3 attempts (18 trials, expanded 2026-08-14 from the original 2-variant scope). Registered
prediction: all 4 finray variants 3/3, both rigid variants fail/marginal. +0.5 mm traces to the
pj_stock y−2.5° window (Bill 0007 R3 note 2); 4.15° is read directly from the SURFACE_RISER.step CAD (top-face normal
4.1467° from vertical, cross-checked via ref_axis to machine precision) —
not a placeholder default; the fr26_5deg seat evidence (5°) brackets it.

Scripts live at sim2real_adlros/experiments/cloth_grasp/experiment3/
{finray_18,finray_18_model2,finray_26,finray_26_5deg,parallel_jaw_stock,parallel_jaw_TPU}/
(all six, NOT git-tracked, [[never-rm-without-double-confirm]]) —
copied from the [[descent-reflex-fix-2026-08-11]] fixed E1 scripts, patched:
--incline-deg (pass MEASURED wedge angle), --slope-orient, depth default
+0.5, dirs incl+4.15deg_depth_+00.5mm_<ts>/ with e3_meta.json (2-decimal angle
format, consistent across all six). README.md in
experiment3/ has the run protocol.

**Why:** the thesis Implications claim (naive flat policy works on finrays,
fails on rigid) was inference-only; E3 demonstrates it end-to-end.

**How to apply:** before the session — enact Bill 0009 (Article II gate),
update config A/B grasp XY for the wedge location, measure the wedge angle.
The 2026-08-11 fr18 session's +90.8 mm A.z override / −14 N in-air reading
may have been this raised setup being assembled — verify touch-off before
trusting forces there.
