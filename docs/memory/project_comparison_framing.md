---
name: project-comparison-framing
description: "Crucible-lite project is a parameter-space comparison of soft vs rigid graspers on cloth manipulation, not a fixed-condition success-rate benchmark."
metadata:
  type: project
---

The device compares soft vs rigid graspers (Franka R3 arm, thin cloth flat on hard surface) by mapping the **success region in gripper-control parameter space** for each gripper, then comparing the size/shape of those regions. It is NOT a fixed-parameter success-rate trial.

**Why:** User explicitly corrected this framing during /spec collect Q5. The hardest-case fixture (thin flat cloth) is held constant; the swept variables are gripper-control parameters (force setpoint, approach height, finger gap, closing speed, etc.). The output is two parameter regions, and the comparison concerns how forgiving each gripper is.

**How to apply:** When reasoning about thresholds, the per-trial success is still binary (cloth grasped + lifted, visually verified by researcher → no false positives possible). The project-level threshold is about parameter-grid resolution, trials per grid point, success-region size metric, and premature-abort budget. Domain primitives must support measuring the boundary of the success region, not just per-trial pass/fail. Related: [[user-role]].
