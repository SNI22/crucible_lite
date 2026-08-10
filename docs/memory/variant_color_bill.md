---
name: variant-color-bill
description: Bill 0008 — binding variant→color map for ALL cloth-grasp figures; load from docs/variant_palette.json
metadata: 
  node_type: memory
  type: project
  originSessionId: 923b8ca9-f1ab-4cb2-a5b8-034e144d327e
  modified: 2026-08-10T02:04:10.251Z
---

Bill 0008 (ENACTED 2026-08-09) fixes the color of every gripper variant in every figure:
pj_stock `#c44e52` · pj_TPU `#dd8452` · finray_18 `#55a868` · finray_18_model2 `#4c72b0` · finray_26 `#8172b3` · finray_26_5deg `#937860`.
Failure/zero marker dark-red `#8b0000` ×; tilt conditions encoded by alpha/hatch (never hue); symmetry-assumed entries alpha 0.3 dashed.

**Why:** user mandated a constant color scheme so diagrams stay cross-comparable.

**How to apply:** any new plot must use these exact hexes — machine-readable at `docs/variant_palette.json`; changing them requires a new Bill. Related: [[thesis-state-2026-08-06]] (Bill 0007 calibrated axis).
