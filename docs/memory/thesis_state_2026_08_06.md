---
name: thesis-state-2026-08-06
description: "Thesis manuscript state after the Aug 4-6 writing push — what is done, what only the user can fill"
metadata: 
  node_type: memory
  type: project
  originSessionId: 923b8ca9-f1ab-4cb2-a5b8-034e144d327e
  modified: 2026-08-10T01:34:15.684Z
---

As of 2026-08-06 the thesis (`docs/thesis/`, McGill_PhD_Thesis_Template, `content/` flat layout) builds clean at 63 pages, zero undefined refs/citations.

Done this push: supervisor's Methods feedback fixed (all symbols defined in Notation.tex + inline; past tense standardized; z_TCP/z_surf/σ naming unified); α (seat angle) and θx/θy (arm tilt) are **separate quantities, never summed** (user explicit); "0° = arm perpendicular to surface" simplification; hand-drawn figures wired in (fig 3.1 α/t from `docs/hand_drawing/FR3.pdf`, fig 3.2 θx/θy from cropped PNGs — crops via content-density because the Ground line spans full width); new Background §2.2 with 8 web-verified citations (Ramisa, Qian, FlingBot, Monkman, Guo, Ozcelik, Jiang, Li — all in references.bib, 43 entries); front matter all written (French abstract needs francophone proofread); Appendix coverage tables regenerated from filesystem (945 trials).

**Remaining TODOs only the user can fill:** cloth + test-surface photos; axis-triad labels on the two hand drawings ([[mech609-seminar-deck]] uses the same figures); funding sources in Acknowledgements; public GitHub URL + commit hash in Discussion; ADL-lab citation lead in RelevantLiterature.

**How to apply:** never invent citations — every bib entry must be web-verified before insertion (DOIs only when actually seen; use verified URLs otherwise). Standalone `Thesis_methods_only.tex` shares content/ sources and includes Notation.

**Bill 0007 ENACTED 2026-08-09** (docs/governance/bills/0007, Case 4): ALL aggregate analyses use calibrated depth d_cal = d − d_first_success (per variant/calibration epoch; shallowest all-success zero-tilt cell = 0; tilt cells inherit their variant's zero) and the window d_cal ∈ [0, 10] mm ONLY. d_first_success values: pj_stock +1.5, pj_TPU +1.0, fr18 −1.5, fr18_model2(Jul21) 0.0, fr26 −0.5, fr26_5deg 0.0. Finray ranges are right-censored → claim "≥10 mm vs 1–2.5 mm rigid", NOT the old "≥12/15–22mm". Deprecated data excluded from counts (845 analysed trials): m2 pre-recalibration June cells, fr26 tx+5° pilots, superseded same-config sessions. Any figure/statistic regenerated after this date must follow this convention.
