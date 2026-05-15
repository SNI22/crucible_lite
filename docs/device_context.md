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

This device detects falls of an elderly person in a bathroom by sensing floor
vibration, then prompts the user to confirm whether help is needed. If no
"no" response is received within a fixed timeout, the device escalates to an
external channel (caregiver / family / emergency services — escalation
transport is out of scope for this project). The dependency chain is:
floor-vibration event → on-device fall classification → user prompt →
verbal/manual acknowledgment or escalation. A false positive prompts the
elderly user unnecessarily (recoverable annoyance, budgeted at ≤ 1 per
7 days). A false negative leaves an injured or unconscious person on the
bathroom floor with no alarm — the catastrophic failure the device exists
to prevent.

**Project target:** Detect a fall of an elderly person on a bathroom-tile
floor at up to 3 m range, including the slow-controlled-descent (slump)
case, while rejecting heavy footsteps, dropped objects, and bathroom
plumbing vibration (shower / flush / drain).

**Pass/fail threshold:**
- Sensitivity ≥ 95 % of real falls detected within 30 s of fall onset,
  covering fast falls, slow slumps, and falls at the 3 m far-range case.
- False positive rate ≤ 1 alarm per 7 days of typical bathroom use.
- Detection latency: alarm prompt fires within 30 s of fall onset.

**Domain primitives** (traces to Article I — ratified by Amendment 1):
1. **Floor acceleration** (m/s²) — inertial response of the bathroom floor
   to mechanical events on it.
   Measured via: piezo (PVDF + proof-mass cantilever) at ≥ 1 kHz.
2. **Acoustic pressure** (Pa, or normalized) — sound pressure in the
   bathroom air, both broadband (environment classification) and
   speech-band (verbal-response detection).
   Measured via: microphone (digital I2S MEMS recommended; pinned at
   `/toolchain init`).
3. **Human room occupancy** (boolean, with optional confidence) — whether
   a human body is present in the monitored room.
   Measured via: WiFi sensing module (output interface pinned at
   `/toolchain init`).

**Operating envelope:**
- **Normal:** ceramic / porcelain tile floor, PVDF+mass cantilever
  epoxied across full base footprint, ≤ 3 m max fall range, 15–30 °C,
  30–95 %RH, mains-powered, always-on 24/7.
- **Worst-case (still in-scope):** active shower running, toilet flush +
  tap running, neighbor footsteps through shared wall/floor, door slammed,
  brief second-person presence (helper / delivery), bath mat partially
  covering the floor, splash on enclosure (splash-rated, not submerged).
- **Out-of-scope:** outdoor / submerged deployment; multi-person
  bathrooms; floors over springy subfloor (joist over basement);
  carpet / soft flooring; rugs covering the device; detection of falls
  outside the monitored room; whole-house single-device monitoring.

---

## Signal Inventory

| Signal | Physical quantity | Unit | Normal range | Hard limits | Sample rate | Primitive |
|--------|------------------|------|--------------|-------------|-------------|-----------|
| Piezo (PVDF+mass) | Floor acceleration | m/s² (derived from V via charge-amp transfer function) | ±0.5 g typical bathroom activity | clip at front-end rail (≈ ±5 V at ADC input) | 1 kHz baseline; ≥ 2 kHz stretch via external ADC | P1 |
| Microphone — broadband channel | Acoustic pressure | Pa (or 16-bit PCM count) | 30–80 dB SPL room ambient | clip at digital full-scale | 8–16 kHz (TBD at /toolchain init) | P2 |
| Microphone — speech-band channel | Acoustic pressure (300–3400 Hz) | Pa (or 16-bit PCM count) | response-time speech bursts | clip at digital full-scale | derived from broadband channel | P2 |
| WiFi sensing | Human room occupancy | boolean (+ optional confidence 0–1) | 0 or 1 with confidence ≥ 0.7 stable | sensor-not-responding watchdog | event-driven or 1 Hz poll (TBD) | P3 |

**Stretch / cost-gated sensors (deferred to /toolchain init decision):**
- PIR — only if WiFi-sensing presence proves unreliable in bathroom RF environment
- IMU on device housing — only if device housing itself gets bumped causing piezo false positives
- MLX thermal — likely too expensive; skip

**Pre-existing assets carried in from `~/Documents/piezo_circuit/`:**
- Charge-amplifier front-end (CA3140 or MAX44248, 100 MΩ ∥ 10 nF feedback)
- Sensor-mounting protocol (`SENSOR_MOUNTING.md` — PVDF+mass cantilever, full-area epoxy)
- Walk-vs-fall characterization protocol (`WALK_VS_FALL_PROTOCOL.md`)
- Feature dictionary (peak, energy, duration, spectral centroid, band ratios, decay shape, multi-peak count, footstep cadence) — pending augmentation with a slump-rumble feature
- ESP32-S3 host-streaming firmware (5 kHz reference; will be adapted to project firmware)
- Bedroom + livingroom test data; **bathroom fall data does not yet exist** and is a Stage 1 data-collection requirement

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
