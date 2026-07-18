---
name: trial-outcome-taxonomy
description: "Distinguish 'failed trial' (invalid data — controller error, anomaly) from 'no-grasp' (valid data, cloth slipped at lift). A trial with success=False but valid Fz measurements is a no-grasp, NOT a failure — its force data counts."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 923b8ca9-f1ab-4cb2-a5b8-034e144d327e
---

**Rule:** A trial's `success=False` flag means the GRASP outcome failed (cloth
slipped after lift), NOT that the trial itself failed. As long as the trial
executed correctly and produced stationary-stage Fz samples, the force data
is valid and counts toward n.

**Why:** The benchmark measures force across the contact window — that
measurement is valid regardless of whether the cloth was later held at lift.
A "no-grasp" trial tells you "this was the force present when the cloth
was being engaged at this depth/tilt", which is its own scientifically
meaningful answer. Marking it as "failed" implies the data is invalid; it's
not.

**How to apply:**

| outcome    | meaning                                          | counts as data? |
|------------|--------------------------------------------------|-----------------|
| success    | Cloth held after lift; success=True              | YES              |
| no-grasp   | Trial executed cleanly; cloth slipped at lift    | YES — valid Fz   |
| failed     | Controller error, no stationary samples, anomaly | NO — invalid     |

**Examples:**
- fr18 −1.0 mm x+2.5° (today, 2026-06-26): 3/3 trials all `success=False`,
  Fz = −14.07 ± 0.21 N. NOT a failed cell. It's a no-grasp cell with valid
  force data. Should be included in force-curve analysis and counted as n=3.
- +2.0 mm trial 2 outlier (−38.57 N vs neighbors −36.5): true failed/anomalous
  trial — excluded by user request.

**Counting convention:** When tabulating "trials per cell" for coverage tables,
count ALL trials with stationary Fz samples regardless of success flag. The
success flag is a separate dimension for grasp-rate analysis, not a data
validity flag.

Linked: [[no-hide-without-explicit-ask]] — both memories address the broader
theme of preserving valid data and the user's explicit-instruction protocol.
