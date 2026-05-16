---
name: dominant-error-source-flexiforce
description: FlexiForce DAQ stack (A301-1 array + A301-25 pair on custom 8-ch CH340T DAQ) is the dominant uncertainty source for this benchmark; Franka and fixture errors are fixed and out of scope
metadata: 
  node_type: memory
  type: project
  originSessionId: 2c5259c5-df91-4260-a9f9-c03165f5d475
---

In the cloth-grasping soft-vs-rigid benchmark, the FlexiForce sensor stack (A301-1 bench-foot array, A301-25 finger-pad pair, custom 8-channel CH340T DAQ, per-channel calibration-curve fit) is the **dominant error source**. All other error sources — Franka FCI pose/F_ext accuracy, controller behaviour, mechanical fixture, visual labelling — are constrained and cannot be changed.

**Why:** The user has explicitly identified this as the only remaining tunable contributor to comparison uncertainty. Because the benchmark output is a Contact Force tolerance envelope (metrics 3/4/5 in `docs/device_context.md` Pass/fail threshold), FlexiForce noise and calibration error propagate directly into the published soft-vs-rigid comparison. The Franka F_ext branch of the Contact Force primitive is a cross-check, not a substitute — the bench-foot and finger-pad evidence is what distinguishes pre-pinch table contact from at-pinch grasp force.

**How to apply:**
- Stage 0 H1 (DAQ frame sync + non-zero + stimulus-tracking) is the critical Stage 0 test, not a formality. Resist suggestions to loosen it.
- The per-channel calibration-curve fit Bill (next Stage 0 close blocker per [[a301-calibration-mts]]) carries first-order weight on benchmark conclusions; spend rigor on form selection, residual reporting, and per-channel re-fit cadence.
- When proposing engineering effort, default toward instrumentation/calibration improvements on the FlexiForce path before touching anything Franka- or fixture-side.
- When a Stage 1+ algorithm hides a DAQ pathology (e.g. low-pass smoothing over a noisy channel), flag it explicitly under Amendment 8 (Algorithm Search Honesty): hardware iteration must remain on the alternatives list.

Related: [[daq-capacity-pending]] (wiring decision for 5 incoming A301-25 affects which channels carry the comparison weight); [[a301-calibration-mts]] (the calibration source that determines the achievable FlexiForce accuracy floor).
