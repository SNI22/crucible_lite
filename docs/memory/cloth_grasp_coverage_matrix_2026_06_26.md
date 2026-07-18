---
name: cloth-grasp-coverage-matrix-2026-06-26
description: "CRUCIAL — full coverage matrix for cloth_grasp benchmark across all 4 finray variants (fr18, fr18_model2, fr26, fr26_5deg) × all depths × 5 tilt conditions (0°, x±2.5°, y±2.5°). Authoritative snapshot as of 2026-06-26 night. Always re-derive fresh from filesystem before recommending fills — entries become stale within hours during active sweeps."
metadata: 
  node_type: memory
  type: project
  originSessionId: 923b8ca9-f1ab-4cb2-a5b8-034e144d327e
---

**Use:** Single-glance reference for what depth × tilt × variant cells have been
run vs blank. Critical for planning next runs and for spotting cross-session
contamination during bias computation.

**Why this matters:** Knee-region cells (+1.5 to +4 mm) are highly sensitive to
session drift (1–5 N inter-session). Whenever a new x+TILT cell is added on a
fresh day, the matching x−TILT cell from a prior day must be re-run or staged.
The matrix below is the truth source for which pairs are same-session.

**How to apply:** Before regenerating bias bars or recommending runs, re-scan
the filesystem (cells get added/staged hourly). Use this table only as a
starting reference; never quote n-counts without re-verifying.

---

## Variants in scope

- **fr18** — finray standard 18 mm finger thickness
- **fr18_model2** — fr18 SECOND PRINT, added 2026-06-26 to demonstrate
  manufacturing variability / defects (no cells run yet, scaffold ready in
  `experiment2/finray_18_model2/`, ground_truth from 2026-06-05)
- **fr26** — finray standard 26 mm finger thickness (flat mount)
- **fr26_5deg** — fr26 finger on 5° pre-tilted mount

## Coverage snapshot (2026-06-26, post-staging older x−2.5° cells on fr26_5deg)

Columns within each variant block: **`0°  x+2.5°  x−2.5°  y+2.5°  y−2.5°`**.
`n` = trial count after dedup; `·` = no data.

```
                fr18                  fr26                fr26_5deg
depth   |  0   x+  x-  y+  y-  |  0   x+  x-  y+  y-  |  0   x+  x-  y+  y-
─────────┼──────────────────────┼──────────────────────┼──────────────────────
-2.0    |  ·   ·   ·   ·   ·   |  ·   ·   ·   ·   ·   |  ·   ·   ·   3   3
-1.5    |  ·   ·   ·   3   3   |  ·   ·   ·   3   3   |  ·   3   3   3   3
-1.0    |  4   3   ·   3   3   |  3   ·   ·   3   3   |  3   3   3   3   3
-0.5    |  4   3   ·   3   3   |  4   1   4   3   3   |  3   3   3   3   3
-0.15   |  ·   ·   ·   ·   ·   |  ·   ·   ·   3   ·   |  ·   ·   ·   ·   ·
 0.0    |  3   ·   ·   ·   ·   |  3   3   3   ·   ·   |  3   ·   ·   ·   ·
+0.5    |  ·   ·   ·   ·   ·   |  ·   2   3   ·   ·   |  ·   ·   ·   ·   ·
+1.5    |  ·   3   ·   3   3   |  ·   ·   ·   ·   ·   |  ·   3   3   3   3
+2.0    |  3   3   ·   3   3   |  3   3   3   2   3   |  3   3   3   3   3
+2.3    |  ·   ·   ·   ·   3   |  ·   ·   ·   ·   ·   |  ·   ·   ·   ·   ·
+2.5    |  ·   3   ·   3   ·   |  ·   3   3   ·   ·   |  ·   3   3   3   3
+3.0    |  ·   3   ·   ·   ·   |  ·   3   3   ·   ·   |  ·   3   4   3   3
+3.5    |  ·   ·   ·   ·   ·   |  ·   3   3   ·   ·   |  ·   3   4   ·   ·
+4.0    |  3   ·   ·   3   3   |  3   3   3   3   3   |  3   3   3   3   3
+5.0    |  ·   ·   ·   ·   ·   |  ·   3   3   ·   ·   |  ·   ·   ·   ·   ·
+6.0    |  3   3   ·   3   3   |  3   3   3   3   3   |  3   3   3   3   3
+8.0    |  4   3   ·   3   3   |  3   3   3   3   3   |  3   3   1   3   3
+10.0   |  3   2   ·   ·   ·   |  3   3   3   3   3   |  3   3   3   3   3
+12.0   |  3   3   ·   3   2   |  ·   3   3   3   3   |  3   3   3   3   3
+14.0   |  1   ·   ·   ·   ·   |  ·   ·   ·   ·   ·   |  ·   ·   ·   ·   ·
+16.0   |  ·   ·   ·   ·   ·   |  3   3   3   3   3   |  ·   3   3   3   3
+18.0   |  ·   ·   ·   ·   ·   |  5   ·   ·   ·   ·   |  ·   ·   ·   ·   ·
+18.5   |  ·   ·   ·   ·   ·   |  3   ·   ·   ·   ·   |  ·   ·   ·   ·   ·
+19.0   |  ·   ·   ·   ·   ·   |  3   ·   ·   ·   ·   |  ·   ·   ·   ·   ·
+20.0   |  ·   ·   ·   ·   ·   |  6   ·   ·   ·   ·   |  3   ·   ·   ·   ·
+22.0   |  ·   ·   ·   ·   ·   |  5   ·   ·   ·   ·   |  ·   ·   ·   ·   ·
```

(fr18_model2 row not shown — no cells run yet as of memory creation.)

## Major gaps to fill (in priority order)

1. **fr18 x −2.5° column entirely empty** — biggest hole; blocks fr18 x-bias
   computation and completes the 3-variant × 2-axis bipolar story.
2. **fr18_model2 — everything blank** — manufacturing-defect comparison cohort
   added 2026-06-26, scaffold ready, awaiting runs.
3. **fr26 +1.5 mm row entirely empty** — only knee-region depth with NO data
   on fr26; blocks dense knee comparison with fr26_5deg (which has it on all 4
   tilts).
4. **fr26_5deg +3.5 mm y-axis** — one missing knee point.
5. **Incomplete cells (n=1)**: fr26 −0.5 mm x+2.5° (n=1), fr26_5deg +8 mm
   x−2.5° (n=1). Either run more or stage.

## Filesystem layout reminder

```
experiments/cloth_grasp/
├── experiment1/<variant>/depth_+NN.Nmm_<timestamp>/   ← 0° baseline
└── experiment2/<variant>/depth_+NN.Nmm_tx±DD.D_ty±DD.D_<timestamp>/  ← tilt sweeps
```

Variant directories: `finray_18`, `finray_18_model2`, `finray_26`,
`finray_26_5deg`, `parallel_jaw_stock`, `parallel_jaw_TPU` (the last two are
rigid baselines, not in this matrix).

Linked: [[no-hide-without-explicit-ask]] — session drift on knee cells is the
main reason older cells need staging when newer arrive, but never auto-stage.
