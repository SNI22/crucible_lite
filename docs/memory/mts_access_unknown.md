---
name: mts-access-unknown
description: Lab MTS access mode (vendor GUI only vs Python API) is unconfirmed — blocks Case 1 Condition C1 feasibility check execution
metadata: 
  node_type: memory
  type: project
  originSessionId: 2c5259c5-df91-4260-a9f9-c03165f5d475
---

The lab MTS that will perform the FlexiForce calibration per Bill 0002 has not been characterised in terms of *how* it can be controlled. Most lab MTS frames ship with proprietary GUI software (MTS TestSuite TWE/Multipurpose, Instron Bluehill, Zwick testXpert, Bose WinTest, etc.) and **do not** expose a Python API out of the box. Some — MTS Series 793, modern Instron Bluehill 3+ with the right licence, or any system configured for Modbus TCP / OPC-UA — do.

**Why:** This determines the entire shape of Layer C. With Python API access, `c1_feasibility_check()` in `src/calibration/mts.py` runs end-to-end against a concrete driver implementing the `MTSDriver` Protocol. Without it, the practical path is: author a test method in the vendor software, run it manually for each target force, export a force-time CSV, and analyse offline — a separate CSV-analysis module that has not been written yet.

**How to apply:** Before reopening Task #5, get answers from the lab on (a) MTS model, (b) vendor software in use, (c) whether any SDK / Modbus / OPC-UA / Python scripting is configured or licensed. Then either implement a concrete driver against that API, or write the CSV-analysis module against an exported log from the vendor software. The control-side scaffolding already committed (`src/calibration/mts.py`, branch `bill/flexiforce-calibration-protocol`) covers the API path; only stub-driver replacement is needed if that path applies.

Related: [[a301-calibration-mts]] establishes MTS as the calibration force source; [[dominant-error-source-flexiforce]] confirms calibration carries first-order benchmark weight, so the C1 check is on the critical path.
