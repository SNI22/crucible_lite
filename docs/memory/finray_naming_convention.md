---
name: finray-naming-convention
description: "The number suffix on finray variants (18, 33) refers to finger thickness, NOT Shore-A hardness / stiffness"
metadata: 
  node_type: memory
  type: project
  originSessionId: 923b8ca9-f1ab-4cb2-a5b8-034e144d327e
---

The `_18`, `_33` suffix on finray variant names (`finray_18`, `finray_33`, `finray_33_5deg`) refers to **finger thickness**, NOT material durometer / Shore hardness.

**Why:** I incorrectly labeled finray_18 as "Shore 18A" in a 2026-06-05 force-vs-depth analysis plot; user corrected.

**How to apply:** When labeling plots or discussing finray variants, describe the number as a thickness/geometry parameter, not as a stiffness/hardness parameter. Don't write "Shore 18A" / "Shore 33A" / similar in titles, axis labels, or analysis text. Confirm with the user what UNITS (mm? other?) before publishing if it matters for the thesis.
