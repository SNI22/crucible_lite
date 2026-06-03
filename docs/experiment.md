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
| G4 | Finray, 18 mm | fixed gap, TBD |

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
| T1b | 0 | 0 | 0 | `d_safe` |
| T2b | 2.5 | 0 | 0 | `d_safe` |
| T3b | 5 | 0 | 0 | `d_safe` |
| T4b | 0 | 2.5 | 0 | `d_safe` |
| T5b | 0 | 5 | 0 | `d_safe` |
| T6b | 0 | 0 | 2.5 | `d_safe` |
| T7b | 0 | 0 | 5 | `d_safe` |

14 conditions × 3 reps × 4 grippers = **168 trials**.

---

## Total budget

| Block | Trials |
|---|---|
| Pilot (P1–P3) | ~35 |
| Study 1 (depth × tilt 0) | 78 |
| Study 2 (tilt × depth) | 168 |
| **Total** | **≈ 280 trials** |

Estimated runtime: 3–4 sessions.

---

## Open items (to confirm with supervisor)

1. **Gripping direction** in EEF frame (x or y) — determines which tilt axis is
   *asymmetric* under gripper mirror symmetry. Once confirmed, that axis extends
   to ±5° (adds ~24 trials).
2. `GRASP_WIDTH_M` for the **finray 18 mm**.
3. Whether to **empirically validate** the gripper mirror symmetry on the two
   "supposed-to-be-symmetric" axes for G1 (full ±5° on those axes — adds 12
   trials, provides a "verified" line for the report).

---

## Recorded per trial (auto-saved)

- pose + F_ext CSV at 30 Hz
- `run_config.json` (gripper, depth, tilt, positions, controller settings)
- `config.yaml` snapshot
- Grasp success / failure (manual visual annotation)

---

## Symmetry argument (rationale for tilt-level choice)

Each gripper is mirror-symmetric across the plane perpendicular to the gripping
direction (the two fingers / blades are identical). Combined with the cloth
edge being approximately straight (mirror-symmetric about its perpendicular),
two of three tilt axes have +θ ⇔ −θ outcomes — the rotations whose axes lie
*in* the mirror plane. Only the rotation about the gripping direction itself
breaks this symmetry (both fingers tilt together → not mirror-equivalent).

Levels {0, 2.5°, 5°} therefore cover the symmetric range. The asymmetric axis
(to be identified in item 1 above) will be extended to negative angles in a
later patch.

---

## Constitutional / governance notes

- **Article II** (human in the loop): all force-driven descents and grasps run
  with operator present and e-stop in hand; each session is manually authorized.
- **Article I** (signal first): contact force = Franka `F_ext_z` (Amendment 1
  Signal Inventory row 7), bias-corrected per run. A301 FlexiForce calibration
  is currently blocked by a non-repeatable raw response (suspected TPU 90 A
  foot spreading load off the active area); F_ext serves as the first-pass
  primitive until that is resolved.
