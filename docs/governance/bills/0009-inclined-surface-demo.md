### BILL 0009: Experiment 3 — inclined-surface grasp demonstration (success-only, blind flat calibration, single +0.5 mm press)
Proposed by: Shiyao Ni (drafted by Claude session)
Date drafted: 2026-08-12
Change type: experimental protocol (new experiment) + hardware fixture (wedge)
Status: DRAFT — awaiting Justice approval (Article II)

---

**Problem statement:**
Experiments 1 and 2 characterised the contact phase on a flat, levelled
surface with per-variant calibration, and established the headline claim:
finray fingers hold a ≥ 10 mm calibrated depth window under every tested
orientation, versus 0.5–2.5 mm (closed) for the rigid jaws, with two
stock-jaw tilt conditions producing no success at all. That claim
predicts a concrete deployable consequence that no experiment yet
demonstrates end-to-end: when the surface deviates from the calibration
assumption, the finrays should keep grasping under the same naive policy
while the rigid jaws fail. The thesis currently argues this implication
(Conclusions, "Implications") by inference from flat-surface windows; a
direct demonstration would ground it.

---

**Proposed change:**
Add Experiment 3 (E3): a success-only grasp demonstration on an inclined
surface, calibrated blind as if the surface were flat, with a single
minimal-press grasp attempt — no depth or position sweep.

1. **Fixture.** The acrylic test surface is mounted on a wedge at incline
   angle β = 4.15° per the SURFACE_RISER CAD model (grounding below); the as-built fixture is verified against this nominal before the session. Same cloth specimen, same robot,
   same controller and trial policy as E1/E2. The slope direction is
   aligned with the gripping direction (gripper local y), the axis with
   the strongest measured rigid-jaw tilt degradation; the orientation is
   recorded in cell metadata.
2. **Blind calibration.** Each variant is calibrated with the standard
   `ground_truth_finder` force touch-off (3 N threshold) at the grasp
   position, exactly as on a flat surface — the incline is treated as
   unknown. No tilt compensation.
3. **Single grasp attempt protocol.** Each trial presses to the
   calibrated touch-off depth **+ 0.5 mm** — the minimal press at which
   every variant demonstrated successful flat-surface grasping — closes
   the gripper, lifts, and records held / not held. No force metrics are
   reported (force stays logged for the record only).
4. **Outcome metric.** Binary per the Amendment 1 outcome taxonomy:
   success / no-grasp; safety aborts recorded as aborts.
5. **Pilot scope (this Bill).** All six variants — `finray_18`,
   `finray_18_model2`, `finray_26`, `finray_26_5deg`,
   `parallel_jaw_stock`, `parallel_jaw_TPU` — at 3 attempts each
   (18 trials). Extension to other incline angles or larger n requires
   a revision of this Bill after the pilot is reviewed.
6. **Registered prediction (falsifiable).** The incline presents each
   gripper with a 4.15° surface-relative tilt it was not calibrated for.
   From the flat-surface record: all four finray variants succeed (their
   windows held at every tested orientation, including the 5° seat
   evidence on `finray_26_5deg`, which brackets this incline); both rigid
   variants fail or are marginal (at only ±2.5° their windows shrank to
   0.5–2.5 mm, with two `parallel_jaw_stock` tilt conditions producing no
   success at all; 4.15° exceeds the largest tested rigid tilt while the
   +0.5 mm press sits at the very bottom edge of the flat-surface
   window).
7. **Data layout.** New tree
   `experiments/cloth_grasp/experiment3/<variant>/incl+4.15deg_<YYYYMMDD_HHMMSS>/`
   with the standard depth_summary.json + session_log npz per cell;
   incline angle and slope orientation in cell metadata.

---

**Article / Amendment grounding:**
Every parameter traces to a measured primitive:
- β = 4.15°: read directly from the SURFACE_RISER STEP model (top-face
  normal 4.1467° from vertical, cross-checked via the independent
  ref_axis direction to machine precision). This is below the largest
  surface-relative tilt with existing compliant-grasp evidence (the
  finray_26_5deg seat, Experiments 1–2) and still exceeds the largest
  runtime tilt tested on the rigid jaws (2.5°) — a deployment-realistic
  misalignment, not an extrapolated extreme for the compliant finger.
- +0.5 mm press: the shallowest calibrated depth at which every variant
  recorded successful flat-surface grasps (the pj_stock y −2.5° window
  is exactly 0.5 mm, Bill 0007 record) — i.e., the most conservative
  press a flat-surface-calibrated policy could justify.
- 3 N touch-off, 3 repeats, −60 N abort, outcome taxonomy: unchanged
  E1/E2 primitives.
- Slope aligned with gripping direction y: the axis of the documented
  rigid-jaw y± tilt evidence (2026-06-24 sign-flip findings).
Not making this change leaves the thesis's central implication
demonstrated only by inference from flat-surface data.

---

**Physical evidence:**
- images/working_range_hist.png, images/working_range_tilt.png — the
  measured windows (≥ 10 mm vs 1.5/2.5 mm closed; stock-jaw no-success
  tilt conditions) from which the prediction derives.
- Bill 0007 record — calibrated-axis zeros and the 0.5 mm minimal
  window ruling (R3 note 2).
- 2026-08-11 descent-reflex fix (ported to all experiment1 variant
  scripts) — prerequisite for reliable descents; E3 scripts must derive
  from the fixed versions.

---

**Consequences and known costs:**
- Pilot data only: 3 attempts per variant (18 trials across all six
  variants) supports a demonstration figure/table and a short thesis
  section explicitly marked as pilot, not a statistical claim.
  Full-matrix statistics require a Bill revision.
- New fixture: a wedge (BOM addition) whose angle must be measured and
  recorded (level / print-angle verification) — the incline is a
  controlled input even though calibration is blind to it.
- The rigid jaw may trigger a −60 N safety abort on the downslope jaw;
  each abort costs an fr3-launch restart — budget session time.
- Cloth placement on an incline may shift between trials; the flatten
  step must be repeated per attempt and slippage noted.
- Scripts: E3 needs a minimal variant of run_trial.py (fixed +0.5 mm
  press, no sweep) for each of the six variants; all six must inherit
  the 2026-08-11 per-leg descent fix.
- Interpretive limit: a single press depth cannot separate depth-error
  from tilt-error contributions to a rigid-jaw failure; the demo shows
  THAT the naive policy fails on rigid jaws, not which error component
  dominates. E1/E2 carry that decomposition.

---

**Enactment:**
Requires human approval (Article II) before any hardware session.
On enactment: build/measure the wedge, scaffold
`experiments/cloth_grasp/experiment3/`, derive the E3 trial script from
the fixed E1 scripts, run the 6-trial pilot, and record the outcome
grid. Thesis integration (pilot section + demo figure) and any deck
material follow as separate steps under the Standing Orders.
