### BILL 0008: Canonical color scheme for gripper variants across all diagrams
Proposed by: Shiyao Ni (drafted by Claude session)
Date drafted: 2026-08-09
Change type: software (analysis/figure pipeline — presentation standard)
Status: ENACTED 2026-08-09 (requested and approved by Shiyao Ni in-session)

---

**Problem statement:**
Figures generated across sessions risk drifting color assignments, making
cross-figure comparison error-prone (a variant that is green in one plot
and blue in another invites misreading). A fixed variant→color map is a
presentation-integrity requirement for the thesis and seminar.

---

**Canonical palette (binding for every figure from 2026-08-09 onward):**

| Variant              | Hex       | Family        |
|----------------------|-----------|---------------|
| parallel_jaw_stock   | `#c44e52` | rigid (red)   |
| parallel_jaw_TPU     | `#dd8452` | rigid (orange)|
| finray_18            | `#55a868` | finray (green)|
| finray_18_model2     | `#4c72b0` | finray (blue) |
| finray_26            | `#8172b3` | finray (purple)|
| finray_26_5deg       | `#937860` | finray (brown)|

Supporting encodings (non-variant):
- measured failure / zero-in-window marker: dark red `#8b0000`, marker "x"
- assumed-by-symmetry entries: variant color at alpha 0.3, dashed edge
- analysis-window end line: grey `0.4`, dashed
- tilt conditions are encoded by alpha/hatch, never by changing the
  variant's hue: 0° solid; x ±2.5° alpha 0.8 hatch «//»/«\\\\»; y ±2.5°
  alpha 0.55 (plain / «..»)

Machine-readable copy: `docs/variant_palette.json` — plotting scripts must
load colors from it (or reproduce it exactly), not hard-code ad-hoc hues.

---

**Article grounding:**
Presentation standard; no Article I constants involved. Recorded as a Bill
so figure-generating agents in future sessions are bound by it.

---

**Evidence:**
All figures regenerated 2026-08-09 (working_range_hist, success_rate_hist,
working_range_tilt, finray_tilt_dcal, pj_tilt_dcal, finray_shape_dcal,
fr18_m1_vs_m2_aligned0) already conform to this palette.
