### BILL 0007: Calibrated depth reference — first successful grasp defines d = 0; analysis window restricted to calibrated 0–10 mm
Proposed by: Shiyao Ni (drafted by Claude session)
Date drafted: 2026-08-09
Change type: software (analysis pipeline — reference frame and analysis window)
Status: PROPOSED — awaiting human enactment

---

**Problem statement:**
All benchmark analyses currently use raw command depth, whose zero is the
force-touch-off ground truth. This zero is contaminated by every calibration
artifact in the chain: cross-session F_ext bias drift (several N; sign flip
observed on finray_18_model2 between 2026-06-27 and 2026-07-21), ground-truth
z shift on recalibration (+0.39 mm on finray_18_model2), per-variant TCP
offsets, and print-to-print geometry differences. Consequently, cross-variant
and cross-print comparisons at the same raw depth partly compare calibration
states, not gripper behaviour. Additionally, sweep end depths differ per
variant (+14 to +22 mm), making range statistics non-uniform.

---

**Proposed change:**
1. Define per (variant, calibration epoch) the calibrated depth
   d_cal = d_command − d_first_success, where d_first_success is the
   shallowest zero-tilt cell in the analysed record whose completed trials
   are all successful (Amendment 1 outcome taxonomy: success; no-grasp and
   safety-abort cells do not qualify).
2. Tilt-condition cells inherit d_first_success from their variant's
   zero-tilt sweep in the same calibration epoch (no per-tilt re-zeroing).
3. All aggregate analyses, figures, and reported statistics use only
   d_cal ∈ [0, 10] mm. Cells outside the window remain in the record but are
   excluded from aggregates.
4. Affected artifacts: R1 working-range figure, R2 tilt figures, R3 curve-
   shape figure, R4 print-comparison figure (already uses this convention),
   thesis Methods (definition), Results (all numbers), seminar deck slides
   13–16.

---

**Article / Amendment grounding:**
Article I (Signal First): d_first_success is a first-order physically
measurable event — the shallowest depth at which the gripper reliably holds
the cloth — whereas the raw zero is a derived calibration construct. Using
the physical event as reference makes every reported number trace to a
measured grasp outcome rather than to the state of the calibration chain.
Not making this change leaves cross-print comparisons confounded by
calibration drift, which Article I exists to prevent.

---

**Physical evidence:**
- images/fr18_m1_vs_m2_aligned0.png — aligning the two fr18 prints at first
  success collapses their curves to +4.1 N mean difference (RMSE 5.0 N over
  13.5 mm); unaligned, the same data shows a ~1 mm depth offset consistent
  with print/calibration geometry, not behaviour.
- finray_18_model2 recalibration record (ground_truth_20260721_130614.json
  vs ground_truth_20260627_004540.json): z_ground_truth +0.393 mm,
  fext_bias_z sign flip (−1.2 N → +4.3 N) across sessions with unchanged
  hardware — direct measurement of the raw-zero drift this Bill removes.
- Working-range recount (2026-08-09): rigid variants' entire success spans
  (1.0 mm, 2.5 mm) and all finray spans exceed 10 mm, so a calibrated
  0–10 mm window retains every variant's full comparable region.

---

**Consequences and known costs:**
- Finray working ranges become right-censored at 10 mm: reported claim
  changes from "15.5–22.5 mm" to "≥ 10 mm (window end) vs 1.0–2.5 mm rigid".
  Weaker headline, stronger comparability.
- Deep-region data (d_cal > 10 mm: the second force rise, fr26 cells to
  +22 mm) is excluded from aggregates; retained in the record and available
  to a future Bill.
- R3's peak–valley shape is fully contained in the window (peak ≈ 2–4 mm,
  valley ≈ 6–8 mm); the late rise is truncated.
- Rigid variants: d_first_success is defined (both have all-success cells);
  their windows sit entirely inside [0, 10] — no change to their numbers.

---

**Enactment:**
Requires human approval (Article II). On enactment: recompute all affected
figures and statistics, update thesis Methods/Results and seminar deck, and
record the enacted Bill in case_law.md.
