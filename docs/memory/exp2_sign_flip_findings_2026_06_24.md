---
name: exp2-sign-flip-findings-2026-06-24
description: Session 2026-06-23/24 result — y-tilt ±2.5° on stock + TPU + finray_26 shows universal force bias toward +2.5° that decomposes into sign-invariant gripper slope + constant cloth/setup offset
metadata: 
  node_type: memory
  type: project
  originSessionId: 923b8ca9-f1ab-4cb2-a5b8-034e144d327e
---

Session of 2026-06-23 → 2026-06-24 produced the cleanest cross-variant
finding of the campaign: the y-tilt ±2.5° asymmetry on rigid-jaw variants
(stock + TPU) decomposes into a **sign-invariant force-depth slope**
(<1% deviation) plus a **constant additive offset** of 1–3 N.

**Numbers (y-tilt sign-flip, 3 depth points each):**
- stock: slope +2.5° = 23.62 N/mm, slope −2.5° = 23.77 N/mm (0.7% diff), offset = +2.7 N
- TPU: slope +2.5° = 15.97 N/mm, slope −2.5° = 16.02 N/mm (0.3% diff), offset = +1.1 N
- finray_26: only 2 depth points per sign — slope diff = 12% (unreliable, add 1 more point)

**Universal observations from 8 sign-flip pairs across 3 grippers:**
- +2.5° y-tilt produces MORE |Fz| than −2.5° in every cell (8/8)
- Magnitude of bias attenuates with depth (53% at boundary → <1% at safe)
- Slope is sign-invariant (depth-response is a gripper property)
- Offset is sign-asymmetric (additive cloth/setup bias in series)

**Success-rate finding (boundary cells):**
- finray boundary: +2.5° succeeds, −2.5° fails (undergrip with less force)
- stock boundary: +2.5° fails, −2.5° succeeds (asymmetric overpress slip)
- TPU boundary: both signs succeed (compliant pad bridges both failure modes)
- safe depth: both signs succeed for all grippers

**Why:** the gripper-cloth-fixture system has a persistent ~10–50% force
bias toward +y rotation (likely cloth weave anisotropy or sub-mm cloth
mis-alignment, not gripper geometry — three structurally different
grippers show the same bias direction). Failure mode depends on gripper
class. TPU's 2 mm pad makes it the most tilt-tolerant at boundary.

**How to apply:** when discussing y-tilt asymmetry in the thesis,
write the slope-vs-offset decomposition rather than the raw +2.5° vs
−2.5° comparison. Discussion chapter `docs/thesis/base/discussion/discussion.tex`
section "Cross-Variant Sign-Flip Analysis" was drafted today and is the
load-bearing version. Three more cells would tighten the story:
finray_26 at one more depth at −2.5° y (3-pt slope confirmation),
finray_18 at any boundary tilt cell (variant currently empty in exp2),
and the cloth-rotation control to nail down whether the bias is weave
or fixture.

Related: [[franka-dds-vpn-conflict]] for the DDS setup that made this
session possible; [[finray-naming-convention]] for variant numbering.
