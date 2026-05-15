# Device Context — RAG Evidence Base

This file is the primary evidence document for all agents operating under the
Crucible Constitutional Governance system. It is read by attorneys before
constructing hearing arguments, by the hw-advisor before making suggestions,
and by the simulator-operator when validating simulation parameters against
known hardware behaviour.

**Agents: read this file before any hearing argument or advisory session.**  
**Humans: keep this file current. A stale BOM or outdated test result here is
a constitutional violation under Article I (Signal First).**

Maintained by: human engineer (primary) + `/toolchain` command (hardware/pin sections).  
Updated after: every field test session, every BOM revision, every schematic change.

---

## Device Purpose

This device is a hardware-comparison benchmark that maps and compares the
**control-parameter success region** of a soft, passively-adaptive grasper
(UMI finray, TPU 90A) against a rigid factory parallel-jaw grasper, on the
task of grasping thin flat cloth from a hard surface with a Franka Research 3
arm. For each grasper, the benchmark sweeps gripper-control parameters
(approach z-offset, head rotation, applied force, finger gap, closing speed)
and records the boundary of the region in which a researcher-verified grasp
succeeds without the Franka controller quitting due to error. The output is
two parameter-space envelopes whose size and shape constitute the comparison.

The direct dependent is the researcher running the experiment, who labels
each trial pass/fail by visual inspection (eliminating false positives at the
trial level) and reads off the per-grasper tolerance envelopes. Downstream,
the published comparison is read by robotics researchers selecting hardware
for cloth-manipulation work — an incorrect tolerance envelope biases the
soft-vs-rigid selection decision in their projects.

The remaining failure mode is **false-negative trials caused by premature
controller termination** (force-safety abort firing before the grasp
completes). Because this systematically penalises graspers operating near
the Franka force-safety threshold — likely the soft grasper, which needs
higher contact deformation to pinch — it biases the comparison toward the
rigid grasper unless explicitly tracked via the controller-status admissibility
signal.

**Project target:** Map the per-grasper success region for grasping thin flat
cloth lying on a hard, instrumented 3D-printed surface, with the grasper
operating in moderate-force contact with the surface during pre-pinch descent.

**Pass/fail threshold:** Conclusive comparison requires, per grasper, the
following five tolerance metrics to be mapped across the control-parameter
space, plus three functional task evaluations under a shared human-defined
policy:

Benchmark metrics (per grasper):
1. z-axis tolerance — range of approach-height offset over which grasp succeeds
2. Angular tolerance — orientation spread of the Franka **achieved** end-effector
   pose observed across the set of successful trials, when commanded orientation
   is held constant at (90°, 0°, 0°). This is a **passive observation**, not an
   active parameter sweep — it captures how much controller-introduced orientation
   error the grasper can absorb without grasp failure.
3. Maximum surface-contact force at which the controller still agrees (does not quit)
4. Peak contact force during successful grasps (table or cloth)
5. Minimum contact force required for a successful grasp (table or cloth)

Functional tasks (both graspers, same policy):
- Diagonal fold (flat cloth corner grasp)
- Middle pick → drop onto adjacent sphere (flat cloth middle grasp)
- Drag from A to B (flat cloth edge grasp)

Per-trial admissibility: controller did not quit + visual verification that the
cloth was grasped and lifted.

**Domain primitives** (traces to Article I):
1. **Contact Force** (N) — force at any physical contact interface between
   the grasper and the environment (cloth–grasper, grasper–table, finger-pad
   pinch line).
   Measured via: table-foot A301-1 array, Franka built-in F_ext at the
   end-effector flange, finger-pad A301-25 pair.
2. **End-Effector Pose** (mm, deg) — Cartesian position and orientation of
   the grasper relative to the calibrated table-zero frame. Orientation is
   commanded constant at (90°, 0°, 0°) for every trial — it is NOT a swept
   parameter. The achieved orientation deviates from the command by residual
   controller / mechanical error; this deviation is the physical basis of
   benchmark metric #2 (angular tolerance), recorded as a passive observation
   across the successful trials.
   Measured via: Franka achieved pose + per-session table z-zero calibration;
   Franka commanded pose logged alongside for command-vs-achieved error.

**Operating envelope:**
- **Normal:** Single fixed lab cell. Testing bench fixed to the table on
  which the Franka R3 is mounted. Standard lab ambient. No environmental
  perturbations beyond HVAC. Single DAQ at 100 Hz aggregates the 5 table-foot
  A301-1s and the 2 finger-pad A301-25s; Franka FCI streams at 1 kHz; all
  signals share a ROS time base.
- **Worst-case:** Tekscan A301 sensor drift during long sessions or after
  prolonged static load — requires per-session calibration against a
  reference load and may require re-zero between trials.
- **Out-of-scope** (the comparison data does NOT support claims about):
  - Cloth types other than the two tested specimens (1 thin + 1 thick)
  - Surfaces other than the instrumented 3D-printed test bench (a rougher
    surface may be added in a future scope expansion)
  - Graspers other than the tested set: 22 mm UMI finray (TPU 90A),
    17 mm UMI finray (TPU 90A), factory Franka Hand parallel jaw. Additional
    finray variants may be added; other materials, geometries, and durometers
    are out of scope without explicit re-test.
  - Robots other than the lab Franka Research 3 (the "controller agrees"
    admissibility criterion is Franka-controller-specific)
  - Cluttered workspaces (other objects present in the cell)
  - Actively-controlled compliant graspers (the soft grasper here is fully
    passive)

---

## Signal Inventory

All streaming signals carry ROS message-header timestamps and share a common
ROS time base. The 5 table-foot A301-1 channels and the 2 finger-pad A301-25
channels are read by a single 8-channel DAQ; one channel is spare.

| # | Signal | Physical quantity | Unit | Normal range | Hard limit | Sample rate | Primitive |
|---|--------|-------------------|------|--------------|------------|-------------|-----------|
| 1 | Franka joint torques (×7) | Per-joint actuator torque | N·m | Per-joint, per Franka R3 spec | Franka safety cutoff | 1 kHz | Contact Force (indirect via Jacobian) |
| 2 | Franka EE achieved pose | Cartesian position + orientation | mm, rad | Workspace envelope above table | Franka workspace bound | 1 kHz | End-Effector Pose |
| 3 | Franka EE commanded pose | Cartesian position + orientation | mm, rad | Same as #2 | Same as #2 | 1 kHz | End-Effector Pose |
| 4 | Franka finger displacement | Gripper opening (Franka Hand) | mm | 0–80 mm (factory parallel jaw) | Mechanical stop | event-driven (~30 Hz) | (control input; not a primitive) |
| 5 | Franka controller status | Error / quit flag | enum | OK | "Quit due to error" flag → trial inadmissible | event-driven | Admissibility gate (derived from Contact Force) |
| 6 | Table-foot array (5× A301-1) | Per-foot vertical force | N | 0–3 N per foot (target), array sum 0–15 N | 4.4 N per foot (saturation) | 100 Hz | Contact Force (table side; sum = total Fz, centroid = contact location) |
| 7 | Franka F_ext (built-in) | Estimated end-effector wrench | N, N·m | 0–20 N per axis | Franka collision threshold | 1 kHz | Contact Force (at flange) |
| 8 | Finger-pad pair (2× A301-25) | Force at pinch line | N | 0–10 N (transient 0–30 N) | 111 N (saturation) | 100 Hz | Contact Force (at pinch line) |

**Per-session metadata** (recorded once per session, before the first trial):
- Table z-zero calibration value (Franka world-frame mm)
- A301 per-sensor calibration coefficient (against reference load)
- ROS time-sync confirmation
- DAQ channel-to-sensor mapping

**Per-trial metadata** (HIL-entered by the tester, every trial):
- Cloth ID, thickness, material, dryness, prior-trial wear count
- Grasper under test (22 mm UMI finray TPU 90A / 17 mm UMI finray TPU 90A / Franka factory parallel jaw)
- Control parameters: approach z-offset, head rotation, applied-force setpoint, finger gap, closing speed
- Visual outcome (pass / fail)
- Failure mode if fail: cloth-not-grasped / cloth-dropped-during-lift / controller-quit / other

**Deferred verification (to be closed at `/toolchain init`):**
- Weigh the 3D-printed test bench once printed; measure baseline per-foot loading on the A301-1 array; confirm each foot retains ≥ 1.5 N of headroom above static. If not, substitute one or more A301-25 sensors at the high-load feet.
- Bench-test each A301 against a precision reference load (e.g., calibrated scale) and record the per-sensor coefficient.

---

## Bill of Materials (BOM)

> Component-level record. Every component that touches a domain primitive must be here.
> Include part number, value/spec, supplier, and any substitution notes.
> Delete this instruction block and replace with your actual BOM.

| Ref | Component | Part Number | Value / Spec | Supplier | Notes |
|-----|-----------|-------------|--------------|----------|-------|
| U1  | [MCU board] | — | — | — | [e.g., must be Sense variant] |
| U2  | [Sensor] | — | [I2C addr, ODR, range] | — | — |
| R1  | [Resistor] | — | [Ω, tolerance, power] | — | — |
| C1  | [Capacitor] | — | [μF, voltage] | — | — |
| J1  | [Connector] | — | — | — | — |

**BOM revision:** [vX.Y — YYYY-MM-DD]  
**Known substitution constraints:**  
- [e.g., "U2: LSM6DS3TR-C only — LSM6DSO has different WHO_AM_I and I2C timing"]

---

## Circuit Notes

> Key connections, power rail topology, and any physical issues found during bring-up.
> Include anything an attorney might need to argue a signal-path or power-budget hearing.

### Power topology
- [e.g., "3.3V from on-board LDO via P1.08 software-switched power pin"]
- [e.g., "Battery: 3.7V Li-Po → USB-C charging via onboard PMIC"]

### Key signal paths
- [e.g., "IMU: I2C on SDA=P0.07 / SCL=P0.27, address 0x6A, INT1=P0.11"]
- [e.g., "LED RGB: P0.26 (red), P0.30 (green), P0.06 (blue) — active LOW"]

### Known circuit issues
- [e.g., "P0.27 is also the NFC antenna pin — configure as GPIO before use"]
- [e.g., "IMU power pin must be asserted HIGH ≥ 5ms before first I2C transaction"]

**Schematic revision:** [vX.Y — YYYY-MM-DD]  
**Schematic file:** [path or URL, or "not yet committed"]

---

## Test Results

> Structured record of every validation run. Agents cite entries here by date and type
> when making empirical arguments. An argument citing a test result not in this record
> is inadmissible under the Benjamin Franklin Principle.

### Field / HIL test log

| Date | Stage | Test type | Profile / scenario | Key measurement | Pass/Fail | Notes |
|------|-------|-----------|-------------------|-----------------|-----------|-------|
| YYYY-MM-DD | 0 | HIL smoke | USB serial | [e.g., counter=100 ✓] | PASS | — |
| YYYY-MM-DD | 0 | HIL smoke | IMU I2C | [e.g., WHO_AM_I=0x6A ✓] | PASS | — |
| YYYY-MM-DD | 1 | Simulation | [profile] | [e.g., steps=100, SI=2.1%] | PASS | — |
| YYYY-MM-DD | 2 | Firmware | [scenario] | [e.g., SESSION_END in 18s] | PASS | — |

### Signal measurements (evidence pool)

> Discrete measurements cited in case law or Bills. Each entry must name the file
> and the physical quantity it supports.

| Date | Signal | Value | File / log | Physical quantity |
|------|--------|-------|------------|-------------------|
| YYYY-MM-DD | [e.g., gyr_y peak] | [e.g., 38.4 dps] | [log path] | [e.g., push-off angular velocity] |
| YYYY-MM-DD | [e.g., SI_interval] | [e.g., 2.3%] | [log path] | [e.g., bilateral symmetry] |

### Open anomalies

> Issues observed but not yet explained or resolved. An attorney may cite an open
> anomaly as evidence that a position is unsafe — it has the same weight as a
> confirmed measurement.

| Date observed | Description | Stage | Status |
|---------------|-------------|-------|--------|
| YYYY-MM-DD | [what was seen] | [N] | [open / investigating / resolved YYYY-MM-DD] |

---

## Hardware Bring-up History

> Chronological record of significant hardware events: new revisions, failures,
> component swaps, and the reason for each. Attorneys use this to establish whether
> a current anomaly has a hardware precedent.

| Date | Event | Impact | Action taken |
|------|-------|--------|--------------|
| YYYY-MM-DD | [e.g., Rev A board received] | — | [toolchain init run] |
| YYYY-MM-DD | [e.g., I2C pullup too weak — 10kΩ → 4.7kΩ] | [IMU lost comms at 400kHz] | [BOM updated] |

---

## Agent Reading Guide

| Agent | Sections to read | Why |
|-------|-----------------|-----|
| Attorney-A / B | All | Full evidence base before constructing any argument |
| hw-advisor | Device Purpose, BOM, Circuit Notes, Open Anomalies | Grounds suggestions in actual hardware |
| simulator-operator | Signal Measurements, Test Results | Validates simulation output against known hardware |
| uart-reader | Test Results, Signal Measurements | Contextualises printed UART output |
| plotter | Domain Primitives, Signal Measurements | Ensures plot annotations use correct physical units and thresholds |
| stage-compactor | Test Results, Hardware Bring-up History | Verifies stage exit criteria before freezing precedents |
