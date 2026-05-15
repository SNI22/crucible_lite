# Bill 0001 — Stage 0 Host-Driven Smoke Test Suite

**Status:** ENACTED 2026-05-15 (Case 1, see `case_law.md`)
**Branch:** `bill/stage0-host-driven`
**Change type:** software (Stage 0 exit-criteria definition)
**Traces to:** Article I (Signal First), Article II (Human in the Loop),
Amendments 1, 2, 3; Amendment 8 (PROPOSED) by reference.

---

## Problem

The canonical Stage 0 (HIL Toolchain Lock) smoke test set in `/session` is written
for an MCU target — counter firmware build→flash→USB serial, sensor readout
firmware, algorithm over USB, algorithm over wireless. This project has
**no MCU and no firmware**:

- `docs/toolchain_config.md` Active Firmware Toolchain: `Flash: N/A — no firmware
  on a microcontroller.` `Wireless recv: N/A — all data paths are wired.`
- Compute is the host PC running ROS2 Humble + franka_ros2.
- Data paths of record: (a) DAQ binary serial frame on `/dev/ttyUSB0`
  (CH340T, 115200 8N1, 18-byte frame, 8× uint16 LE, 50–100 Hz), (b) franka_ros2
  ROS2 topic streams (`/franka_robot_state_broadcaster/{current_pose,
  external_wrench_in_base_frame, robot_state}`).

Stage 0 must prove build → run → observe end-to-end for both data paths before
Stage 1 begins. Without this Bill, Stage 0 has no project-specific exit criteria.

---

## Enacted text — Stage 0 exit criteria

Implement a host-side Python test script at `src/stage0_smoke_test.py` invoked
as a standing-order check (no firmware flash; no human approval gate beyond
Stage 0 close, except where noted in H3). The script runs four test groups
sequentially. The ROS2 topic check (H0) and DAQ check (H1) may be run
independently; H2 and H3 require both signal sources live. All tests operate
against live hardware; no mocking.

### H0 — ROS2 Build and Topic-Rate Check

H0.1 — Build sanity:
  ```python
  from franka_msgs.msg import FrankaRobotState
  ```
  Pass: import succeeds. Fail: ImportError → print colcon build instruction
  from sim2real_adlros INSTRUCTION.md.

H0.2 — Topic-rate check: subscribe for 10 s and record mean message rate on
each of the three topics. Pass: each topic ≥ 90 Hz (90% of 100 Hz nominal).
Fail: name the topic and observed rate.

### H1 — DAQ Frame Integrity and Contact Force Primitive Health (load-bearing)

H1.1 — Frame sync and delivery rate. Stream for 10 s. Pass: zero malformed
  frames (start_byte ≠ 0xAA, end_byte ≠ 0x55, frame_size ≠ 18 bytes);
  mean rate ≥ 45 Hz (90% of 50 Hz minimum).

H1.2 — No-load non-zero. Over any 1 s sub-window of quiescent operation
  (sensors under bench static pre-load only, no human contact): for each
  Ch0–Ch6, `mean(chN_raw) > 0`. Fail: name dead channel(s).

H1.3 — No-load noise band per channel. Over a 5 s quiescent window: for each
  Ch0–Ch6, `σ_chN ≤ 20 ADC counts`. FIRST-PASS threshold derived from the
  12-bit ADC range (4095 codes): 20 counts = 0.49% of full-scale, an
  achievable target for a functioning channel. To be re-tightened by a
  follow-up Bill once empirical per-channel σ data exists from the first
  MTS calibration session (Bill 0002).

H1.4 — Stimulus tracking ≥ 10 frames. With operator pressing each wired
  channel deliberately one at a time: pressed channel's `chN_raw` rises
  monotonically for ≥ 10 consecutive frames relative to a 5-frame pre-press
  mean. At 100 Hz, 10 frames = 100 ms — within a deliberate human press
  (typical 300–800 ms), long enough to exclude single-sample noise.

H1.5 — Cross-channel zero-load drift coherence. Over the same 5 s window as
  H1.3, compute per channel `mean_early = mean over [0 s, 2 s]` and
  `mean_late = mean over [3 s, 5 s]`. Pass: `|mean_late − mean_early| ≤
  10 ADC counts` on every wired channel. FIRST-PASS, to be re-tightened.

### H2 — End-Effector Pose Plausibility

H2.1 — Position within Franka R3 workspace: `pz_m > 0`, `sqrt(px² + py² + pz²)
  ≤ 0.855 m`. Over 10 s arm-stationary window.

H2.2 — Orientation deviation from command (90°, 0°, 0°) ≤ 15° per axis
  (sanity gate, not benchmark tolerance).

H2.3 — Position stability: `σ_px, σ_py, σ_pz ≤ 0.5 mm` over 10 s.

### H3 — Controller-Error Admissibility Gate

H3.1 — Clean error state at rest. Subscribe to `robot_state` for 10 s arm-
  stationary. Pass: `current_errors` and `last_motion_errors` both empty.

H3.2 — Admissibility gate exercised. Commanded motion (move to safe waypoint
  and return to home). Pass: `last_motion_errors` empty after motion.

H3 is an **Article II action** — live arm motion requires explicit human
authorization and presence before execution. Not run autonomously by an agent.

---

## Stage 0 exit criteria (all four must pass)

- H0: `colcon build` exits 0; all three topics ≥ 90 Hz.
- H1: malformed-frame count 0, frame rate ≥ 45 Hz, Ch0–Ch6 non-zero,
  σ ≤ 20 ADC counts, ≥10 monotone frames on stimulus, drift ≤ 10 ADC counts.
- H2: pose in workspace, orientation within 15°, σ ≤ 0.5 mm.
- H3: clean error state at rest, clean motion errors after a commanded motion.

Stage 0 close has additional non-test blockers (see `case_law.md` Case 1
conditions and existing `toolchain_config.md` notes): per-channel A301
calibration via Bill 0002, DAQ wiring decision for incoming A301-25 sensors,
police WARNING acknowledgement for commit `c07a0d9`, removal of unused
`bleak` dependency.

---

## Constitutional grounding

- **Amendment 1 (Domain Primitives):** H1 tests the Contact Force primitive
  evidence chain (A301 → DAQ → host). H2 tests the End-Effector Pose primitive
  evidence chain. H3 tests the Contact Force admissibility gate (derived from
  Amendment 1).
- **Amendment 2 (Stage Gate Order):** This Bill defines Stage 0 exit criteria.
- **Amendment 3 (Toolchain Alignment):** All tests use the active toolchain
  (Pixi/colcon, flexiforce_reader, ros2 CLI). No new tooling.
- **Amendment 8 (Algorithm Search Honesty, PROPOSED):** Cited by reference —
  H1.3 and H1.5 noise discipline is the constitutional substitute for letting
  downstream algorithms paper over a noisy DAQ path.
