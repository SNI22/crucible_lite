# Cloth-Grasp Tilt & Depth Experiment Plan

**Date**: 2026-06-03
**Engineer**: Shiyao Ni
**Hardware**: Franka FR3 + arm_client, `fr3_pose_controller`
**Contact-force source**: Franka `F_ext` (flange, base frame), bias-corrected per run.
A301 FlexiForce calibration currently blocked; F_ext is the first-pass estimate.

---

## Objective

Characterize cloth-grasp contact force and tilt tolerance across four gripper
variants (rigid vs soft) to quantify the soft-grasper advantage for thin cloth.

## Research questions

1. **Force vs depth** — How does contact force scale with press depth across rigid
   and soft grippers? (Study 1)
2. **Tilt × depth tolerance** — How does tilt about the contact point affect
   grasp success and contact force, and does this depend on press depth? (Study 2)

## Variables

**Independent**
- Gripper variant (4 levels)
- Press depth (gripper-specific levels)
- Tilt axis ∈ {x, y, z}, angle ∈ {0, 2.5°, 5°}

**Dependent**
- Contact force `F_ext_z` (Franka external wrench, base frame, bias-corrected)
- Grasp success (visual: cloth held through lift A → B)
- Settle (steady-hold) force
- Peak press force

**Controlled**
- Cloth specimen (single, characterized)
- Position A / B in robot base frame
- Per-gripper contact-point TCP offset (from touch-off pilot)
- Approach / descent / press speeds, settle times
- Baseline EEF orientation = (180°, 0°, 0°) RPY

---

## Gripper roster

| ID | Gripper | Grasp mode |
|---|---|---|
| G1 | Parallel jaw, standard (rigid) | force-close, 20 N command |
| G2 | Parallel jaw + TPU 90 A pad | force-close, 20 N command |
| G3 | Finray, 33 mm | fixed gap, 60 mm |
| G4 | Finray, 18 mm | fixed gap, 60 mm |

---

## Pilot phase (per gripper, one-off)

| # | Task | Method | Output |
|---|---|---|---|
| P1 | Touch-off at common (x, y) | `probe_surface.py`, 5 taps @ 2 N | `z_table` (mean ± std), TCP offset Δz |
| P2 | Max-depth escalation, tilt = 0 | step 1 mm until controller reflex (force-safety / accel-discontinuity) | `max_depth_safe` |
| P3 | Success threshold scan, tilt = 0 | step 1 mm from −1 mm upward; ≥ 2/3 trials grasp | `d_min_success` |

≈ 30–40 trials total across grippers.

---

## Study 1 — depth sweep, tilt = 0

Headline force-vs-depth curve per gripper.

| Gripper | Depths (mm) | Repeats | Trials |
|---|---|---|---|
| G1 | −1, 0, 1, 2, 3, 4, 5 (capped by `max_depth_safe`) | 3 | 21 |
| G2 | −1, 0, 1, 2, 3, 4, 5 (capped) | 3 | 21 |
| G3 | −1, 0, 2, 4, 6, 8 (capped) | 3 | 18 |
| G4 | −1, 0, 2, 4, 6, 8 (capped) | 3 | 18 |

**Study 1 total: 78 trials.**

---

## Study 2 — tilt × depth

Tilt about the **per-gripper contact point** (TCP offset from P1).
Two depth levels per gripper:

- `d_min` = `d_min_success` — marginal-grasp fragility under tilt
- `d_safe` = (`d_min_success` + `max_depth_safe`) / 2 — comfortable-grasp margin under tilt

**Axis convention (confirmed 2026-06-04):** the gripper-closing
direction is **y**; the gripper is mirror-symmetric across **xz**. By
choice (operator directive 2026-06-04), all three axes are tested
**single-sided at {0, 2.5, 5°}** — x and z by mirror symmetry, y by
electing to characterise one tilt direction only (into the cloth body,
not off the edge). If the −y side turns out to differ materially, a
follow-up bill can extend it.

Per-gripper tilt conditions (one axis at a time):

| # | rx (°) | ry (°) | rz (°) | Depth |
|---|---|---|---|---|
| T1a | 0 | 0 | 0 | `d_min` |
| T2a | 2.5 | 0 | 0 | `d_min` |
| T3a | 5 | 0 | 0 | `d_min` |
| T4a | 0 | 2.5 | 0 | `d_min` |
| T5a | 0 | 5 | 0 | `d_min` |
| T6a | 0 | 0 | 2.5 | `d_min` |
| T7a | 0 | 0 | 5 | `d_min` |
| T1b–T7b | (same tilts) |  |  | `d_safe` |

7 conditions × 2 depths × 3 reps × 4 grippers = **168 trials**.

---

## Study 3 — inclined-seat finray sub-study

The mounting fixture between the Franka Hand carriage and the finray blades
is a CAD design parameter. Two fixture variants under comparison (finray
33 mm only):

| Variant | Seat angle | Notes |
|---|---|---|
| G3-S2.5 | 2.5° | finray 33 mm on inclined seat |
| G3-S5 | 5° | finray 33 mm on inclined seat |

The standard (flat-seat) **G3** from the main study provides a third
0°-seat reference at no extra cost (data is already collected by Study 1
and Study 2).

### Protocol (Option B — targeted)

Per fixture variant: a depth sweep at tilt = 0 plus a tilt sweep on
the **y axis only** (the gripping direction; the inclined seat
geometrically biases this exact axis, which is why this slice is the
publishable test). Single-sided per the Study 2 axis convention.

| Block | Levels | Trials per variant |
|---|---|---|
| Depth sweep (tilt = 0) | −1, 0, 2, 4, 6, 8 mm × 3 reps | 18 |
| y-axis tilt × depth | 3 angles (ry = 0, 2.5, 5°) × 2 depths (`d_min`, `d_safe`) × 3 reps | 18 |

**36 trials × 2 variants = 72 trials.**

*Detection note:* with one-sided sweeps, the seat-shift hypothesis is
detectable only if the bias goes in the +y direction. If the data is
consistent with a negative shift, a follow-up bill can extend the
sweep to ±5° on the inclined-seat variants.

### Hypothesis

The seat tilt is a built-in geometric offset on the asymmetric tilt axis.
If it acts as a **passive alignment correction**, the tilt-tolerance
curve should shift along that axis by approximately the seat-angle
difference (G3-S5 vs G3-S2.5 ⇒ ~2.5° shift). If the curves change
shape without shifting, the seat is changing blade compliance, not
alignment — a different (also useful) story.

Adding the flat G3 as a 0° reference gives three points (0°, 2.5°, 5°
seat) for a linear or saturating fit on tilt-tolerance shift vs seat
angle.

---

## Total budget

| Block | Trials |
|---|---|
| Pilot (P1–P3) | ~35 |
| Study 1 (depth × tilt 0) | 78 |
| Study 2 (tilt × depth, all axes single-sided) | 168 |
| Study 3 (inclined-seat sub-study, single-sided) | 72 |
| **Total** | **≈ 353 trials** |

Estimated runtime: 4–6 sessions.

---

## Open items (to confirm with supervisor)

1. ~~**Gripping direction** in EEF frame.~~ **RESOLVED 2026-06-04:**
   gripping direction = **y**; mirror plane = **xz**; asymmetric tilt
   axis = rotation about **y**. By operator directive 2026-06-04, all
   three axes (including y) are tested single-sided at {0, 2.5, 5°};
   the −y side is deferred to a follow-up bill if motivated by data.
2. ~~`GRASP_WIDTH_M` for the **finray 18 mm**.~~ **RESOLVED 2026-06-04:**
   `GRASP_WIDTH_M = 0.060` (same as G3, finray 33 mm).
3. ~~Whether to **empirically validate** the gripper mirror symmetry on the two
   symmetric axes (x and z) for G1 (full ±5° on those axes — adds 12
   trials, provides a "verified" line for the report).~~ **DECLINED 2026-06-04:**
   x and z sweep at {0, 2.5, 5°} only, on the theoretical symmetry
   argument; the y-axis already covers both signs in the main matrix.
   If a reviewer pushes back, the validation can be added as a
   targeted 12-trial follow-up at that point.

All open items resolved or declined. Matrix locked at **≈ 425 trials**.

---

## Recorded per trial (auto-saved)

- pose + F_ext CSV at 30 Hz
- `run_config.json` (gripper, depth, tilt, positions, controller settings)
- `config.yaml` snapshot
- Grasp success / failure (manual visual annotation)

---

## Symmetry argument (rationale for tilt-level choice)

Each gripper is mirror-symmetric across the **xz** plane (perpendicular
to the y-axis gripping direction; the two fingers / blades are
identical). Combined with the cloth edge being approximately straight
(mirror-symmetric about its perpendicular), the two rotations whose
axes lie *in* the xz plane — rotation about **x** and rotation about
**z** — have +θ ⇔ −θ outcomes under the combined reflection. Only
rotation about **y** (the gripping direction itself, perpendicular to
the xz plane) breaks this symmetry: both fingers tilt together
(fore/aft about the gripping line), and the +y / −y directions
correspond to physically different conditions (one tilts the contact
toward the cloth body, the other off the edge).

x and z are swept at {0, 2.5°, 5°} (3 levels) by symmetry. y is
**physically** asymmetric (the +y and −y tilts are different
conditions), but by operator directive (2026-06-04) is swept
single-sided at {0, 2.5°, 5°} as well — characterising one tilt
direction (into the cloth body) without the −y side. The −y side
becomes a follow-up question if the +y data motivates it.

---

## Constitutional / governance notes

- **Article II** (human in the loop): all force-driven descents and grasps run
  with operator present and e-stop in hand; each session is manually authorized.
- **Article I** (signal first): contact force = Franka `F_ext_z` (Amendment 1
  Signal Inventory row 7), bias-corrected per run. A301 FlexiForce calibration
  is currently blocked by a non-repeatable raw response (suspected TPU 90 A
  foot spreading load off the active area); F_ext serves as the first-pass
  primitive until that is resolved.
