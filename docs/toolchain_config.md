# Toolchain Configuration

> **Written and maintained by `/toolchain` commands only.**  
> All agents read this file before taking any toolchain-dependent action.  
> Human edits are permitted but must be followed by `/toolchain validate`.

---

## Lock Status

```
Status:  UNLOCKED
Locked:  —
Evidence: —
```

---

## Hardware

```
Board:    Franka Research 3 (FR3) robotic arm — 7-DOF, torque-controlled.
          Controlled via ROS2 Humble + franka_ros2 stack on a host PC
          (see Repository Registry → sim2real_adlros).
MCU:      None on the Crucible side — compute is the host PC.
          Host OS / RT kernel: TBD (record at /toolchain lock once lab
          machine is finalized).
Sensors:  - 6× Tekscan FlexiForce A301-1 (low-range, ~0–4.4 N) — 5 wired
            under the test bench (feet 1–4 at corners, clockwise from the
            foot at lowest x, y; foot 5 at centre) for per-foot reading +
            summed contact force + centroid (Contact Force primitive,
            Amendment 1); 1 held as unwired spare.
          - 2× Tekscan FlexiForce A301-25 (~0–110 N) currently wired —
            finger-pad pair (left + right) at the grasper pinch line
            (Contact Force primitive). An additional 5× A301-25 are
            incoming; location TBD and a DAQ-capacity decision is
            required before wiring (the current 8-channel DAQ has only
            1 free channel after the 5 feet + 2 pads).
          - Franka FCI external-wrench estimate (F_ext) at the end-effector
            flange, surfaced via franka_ros2 (Contact Force primitive,
            admissibility gate).
          - Franka FCI Cartesian pose stream (achieved end-effector pose,
            mm + deg), surfaced via franka_ros2 (End-Effector Pose primitive).
          All FlexiForce sensors are read via the custom 8-channel pressure
          DAQ described below.
External: - Custom 8-channel pressure DAQ — CH340T USB-serial
            (/dev/ttyUSB0), 50–100 Hz, per-channel sensor-range assignment.
            Read via the `flexiforce_reader` Python package (see Repository
            Registry). The vendor single-K formula
            (F[N] = K / (4095·51/raw − 51)) is NOT used in this project.
          - Calibration weight set — multiple known masses spanning each
            sensor's operating range. Calibration is performed by fitting a
            per-channel custom curve (form TBD; to be locked via Bill before
            Stage 0 close) to the (raw, applied_force) point set. Per-channel
            curve coefficients are the admissible source for Contact Force
            values; no Contact Force reading is admissible until its channel
            has a recorded fit.
Notes:    Compute platform is the ROS2 Humble + franka_ros2 stack — NOT raw
          libfranka. End-Effector Pose evidence therefore comes from a ROS2
          topic, not direct libfranka. The "quit on error" admissibility gate
          referenced in Amendment 1 is the franka_ros2 controller's error
          state, not a libfranka exception.
```

---

## Channel & Topic Map

This project is host-driven (no MCU), so the traditional pin map is replaced
by two tables: the **DAQ channel map** (which custom-DAQ channel reads which
physical sensor location) and the **ROS2 topic map** (which franka_ros2 topic
carries which Amendment 1 primitive evidence).

### DAQ channel map (8-ch CH340T DAQ)

Each row maps one physical channel of the custom DAQ to a sensor and its
calibration record. A channel is admissible only when the calibration curve
column points to a recorded fit (see Hardware → calibration note).

Foot numbering convention: feet 1–4 are at the corners, numbered **clockwise
starting from the foot with the lowest (x, y) coordinates in the table-zero
frame**; foot 5 is the **centre foot** under the middle of the bench. This
numbering must be reproduced physically (label each foot) so that channel ↔
location mapping is unambiguous across calibration sessions.

| Ch | Sensor model | Physical location | Primitive | Range preset | Calibration curve | Caution |
|----|--------------|-------------------|-----------|--------------|-------------------|---------|
| 0 | A301-1 | bench foot 1 (lowest x, y) | Contact Force | 1 lb (~4.4 N) | TBD — Stage 0 fit | — |
| 1 | A301-1 | bench foot 2 (clockwise) | Contact Force | 1 lb (~4.4 N) | TBD — Stage 0 fit | — |
| 2 | A301-1 | bench foot 3 (clockwise) | Contact Force | 1 lb (~4.4 N) | TBD — Stage 0 fit | — |
| 3 | A301-1 | bench foot 4 (clockwise) | Contact Force | 1 lb (~4.4 N) | TBD — Stage 0 fit | — |
| 4 | A301-1 | bench foot 5 (centre) | Contact Force | 1 lb (~4.4 N) | TBD — Stage 0 fit | — |
| 5 | A301-25 | finger-pad — left | Contact Force | 25 lb (~110 N) | TBD — Stage 0 fit | — |
| 6 | A301-25 | finger-pad — right | Contact Force | 25 lb (~110 N) | TBD — Stage 0 fit | — |
| 7 | — | (spare) | — | — | — | unused |

**Sensor inventory not currently wired** (recorded for traceability):

| Qty | Model | Status | Intended use |
|-----|-------|--------|--------------|
| 1 | A301-1 | unwired spare | hot-swap reserve for any of Ch 0–4 |
| 5 | A301-25 | incoming | location TBD; will exceed current 8-channel DAQ capacity (5 + 2 already wired = 7 × A301-25, but only 1 free channel) — capacity decision required before wiring |

### ROS2 topic map (franka_ros2)

Each row maps a ROS2 topic to the Amendment 1 primitive whose evidence it
carries. A reading from a topic not listed here is not admissible.

| Topic | Message type | Primitive | Field used | Sample rate | Notes |
|-------|--------------|-----------|------------|-------------|-------|
| /franka_robot_state_broadcaster/current_pose | geometry_msgs/PoseStamped | End-Effector Pose | pose.position (m → mm), pose.orientation (quat → deg) | 100 Hz (franka_ros2 default) | Achieved pose; calibrated table-zero frame applied downstream. |
| /franka_robot_state_broadcaster/external_wrench_in_base_frame | geometry_msgs/WrenchStamped | Contact Force | wrench.force (N) | 100 Hz | Franka F_ext estimate at flange, base-frame. |
| /franka_robot_state_broadcaster/robot_state | franka_msgs/FrankaRobotState | End-Effector Pose + admissibility gate | o_t_ee (pose), current_errors / last_motion_errors (admissibility) | 100 Hz | Full robot state. The error fields are the "controller quit" admissibility gate referenced in Amendment 1 — a non-empty error set on a trial invalidates that trial's Contact Force / Pose readings. |

---

## Active Firmware Toolchain

This project has no on-device firmware — the "toolchain" here describes the
host-side stack that controls the arm, reads the DAQ, and runs simulation.

```
Build:          Pixi + colcon (ROS2 Humble workspace).
                Workspace: ~/Documents/sim2real_adlros (see Repository Registry).
                Build: `pixi run colcon build --symlink-install` (or
                `pixi run -e humble ...` per sim2real_adlros INSTRUCTION.md).
Flash:          N/A — no firmware on a microcontroller.
                The "deploy" equivalent is `colcon build` + sourcing the
                local workspace; the Franka arm itself runs vendor firmware
                that this project does not modify.
Serial monitor: flexiforce_reader (Python; reads /dev/ttyUSB0 CH340T at
                50–100 Hz). Run: `python -m flexiforce_reader` from
                ~/Documents/flexiforce/flexiforce_reader (see Repository
                Registry).
Wireless recv:  N/A — all data paths are wired (Ethernet to FR3, USB to DAQ).
Simulation:     SKIP — to be recorded later via `/toolchain add lib` when
                a sim framework is committed to. Stage 1 entry will block
                until this field is filled.
```

---

## Blocked Toolchains

> [Record blocked toolchain layers here as they are blocked by `/toolchain block`.]
> Format: `- [date] BLOCKED [layer]: [tool] — [reason citing failure mode]`
>
> Example:
> - 2026-01-15 BLOCKED build: Zephyr/PlatformIO — Three-strike failure on IMU I2C init.
>   IMU read returns all zeros on UARTE0. Evidence: smoke_test_2_imu_fail.log.
>   Blocked by Amendment 4 (Three-Strike Rule). Unblock requires Judicial Hearing.

---

## Data Stream Format

> **Required for `/toolchain scaffold`** — fill in before running Stage 1.
> This project has no firmware UART. The data-stream-of-record is two
> sources combined: (a) the custom 8-channel DAQ binary serial stream and
> (b) the franka_ros2 topic stream registered in the Channel & Topic Map
> above. Scaffold generates `src/events.py` (dataclasses), `src/analysis.py`
> (DAQ frame parser + ROS2 message wrappers), and `src/plot.py` (plot
> wrappers keyed on Amendment 1 primitive names).

```
session_end_marker: SESSION_END
  # Emitted by the trial-runner (host-side, not firmware) into the session
  # log file when a trial terminates — either by visual-success label or by
  # controller-quit. The marker is host-written; the parser only needs to
  # recognise it as the end-of-session sentinel.
```

### DAQ Serial Frame (binary, primary force-data stream)

The 8-channel custom DAQ (CH340T, /dev/ttyUSB0, 115200 8N1) emits a fixed
18-byte frame for every sample. Frame structure is defined by the vendor
and confirmed against `flexiforce_reader/protocol.py`:

```
[[stream]]
name:        daq_sample
transport:   serial /dev/ttyUSB0 @ 115200 8N1
start_byte:  0xAA
end_byte:    0x55
frame_size:  18 bytes
struct:      <8H            # 8 channels, uint16 little-endian, low byte first
fields:      ch0_raw, ch1_raw, ch2_raw, ch3_raw, ch4_raw, ch5_raw, ch6_raw, ch7_raw
types:       int, int, int, int, int, int, int, int   # 12-bit ADC codes (0..4095)
primitive:   Contact Force (post-calibration)
rate:        50–100 Hz (host-commanded; default 100 Hz)
host_cmds:   0xFF start streaming, 0xFE stop streaming, 50..100 set sample rate
```

**Conversion to Contact Force (N) is NOT vendor-formula.** Each `chN_raw`
must be converted to newtons via the per-channel custom curve fit recorded
in the Channel & Topic Map → Calibration curve column. A `daq_sample` is
not admissible Article-I evidence until its channels' fits are recorded.

### ROS2 Topic Streams (Franka primitives)

Each topic in the ROS2 topic map above is consumed as a stream by
`src/analysis.py`. The scaffold generates one dataclass per topic, named
after the topic's last path segment, with the field paths listed below.

```
[[stream]]
name:       current_pose
transport:  ros2 topic /franka_robot_state_broadcaster/current_pose
msg_type:   geometry_msgs/PoseStamped
fields:     ts_ns, px_m, py_m, pz_m, qw, qx, qy, qz
field_src:  header.stamp, pose.position.x, pose.position.y, pose.position.z,
            pose.orientation.w, pose.orientation.x, pose.orientation.y, pose.orientation.z
types:      int, float, float, float, float, float, float, float
primitive:  End-Effector Pose
units:      ns, m, m, m, quat (downstream conversion: m → mm, quat → deg in src/analysis.py)
rate:       100 Hz (franka_ros2 default)
```

```
[[stream]]
name:       external_wrench
transport:  ros2 topic /franka_robot_state_broadcaster/external_wrench_in_base_frame
msg_type:   geometry_msgs/WrenchStamped
fields:     ts_ns, fx_N, fy_N, fz_N, tx_Nm, ty_Nm, tz_Nm
field_src:  header.stamp, wrench.force.x, wrench.force.y, wrench.force.z,
            wrench.torque.x, wrench.torque.y, wrench.torque.z
types:      int, float, float, float, float, float, float
primitive:  Contact Force (Franka F_ext branch)
rate:       100 Hz
```

```
[[stream]]
name:       robot_state
transport:  ros2 topic /franka_robot_state_broadcaster/robot_state
msg_type:   franka_msgs/FrankaRobotState
fields:     ts_ns, o_t_ee_pose, current_errors, last_motion_errors
field_src:  header.stamp, o_t_ee.pose, current_errors, last_motion_errors
types:      int, Pose, ErrorSet, ErrorSet
primitive:  End-Effector Pose + admissibility gate
notes:      A non-empty current_errors or last_motion_errors set on a trial
            invalidates that trial's Contact Force and Pose readings
            (Amendment 1 admissibility gate).
rate:       100 Hz
```

### Binary Export Format (optional)

Not used in this project. Trials are recorded as ROS2 bag files (`ros2 bag
record`) plus a parallel DAQ CSV from `flexiforce_reader`. Bag + CSV are
the on-disk session record; no separate binary export is produced.

---

## Library Manifest

This project has three library tiers: Crucible Python deps (this repo),
DAQ-side Python deps (flexiforce_reader), and ROS2 / Franka deps (Pixi-managed
in sim2real_adlros). Versions are recorded as the constraint in the
authoritative manifest file, not re-pinned here.

### Crucible Python (`requirements.txt` in this repo)

| Library | Version | Source | Purpose | Known issues |
|---------|---------|--------|---------|--------------|
| numpy | >=1.24.0 | PyPI | Signal generation, sample arrays, sensor data math | — |
| matplotlib | >=3.7.0 | PyPI | Diagnostic plots (Agg backend, headless) | — |
| bleak | >=0.21.0 | PyPI | (Inherited from upstream Crucible template; not used in this host-driven project — candidate for removal) | Unused dependency — flag at Stage 0 review |
| pytest | >=7.4.0 | PyPI | Test runner for crucible/ infrastructure | — |

### DAQ-side Python (`flexiforce_reader`, branch `main`)

| Library | Version | Source | Purpose | Known issues |
|---------|---------|--------|---------|--------------|
| flexiforce-reader | 0.1.0 | git@github.com:SNI22/flexiforce_reader.git (branch `main`) | 8-channel DAQ readout + live GUI + CSV recording; defines wire protocol in `flexiforce_reader/protocol.py` | Vendor single-K formula is wrong for this project — use per-channel custom curve fit (see Channel & Topic Map) |
| pyserial | >=3.5 | PyPI | CH340T USB-serial transport | — |
| PyQt5 | >=5.15 | PyPI | flexiforce_reader GUI | Not needed for headless capture; CLI-only mode TBD |
| pyqtgraph | >=0.13 | PyPI | Live channel plotting in flexiforce_reader GUI | — |

### ROS2 + Franka (Pixi-managed in `sim2real_adlros/pixi.toml`, env `humble`)

| Library | Version | Source | Purpose | Known issues |
|---------|---------|--------|---------|--------------|
| ros-humble-desktop | latest (via conda-forge) | Pixi / conda-forge | ROS2 Humble core | — |
| ros-humble-franka-ros2 | latest (via conda-forge) | Pixi / conda-forge | franka_ros2 binary distribution | `franka_msgs` not provided by conda — built from source under `sim2real_adlros/src/franka_ros2/` per INSTRUCTION.md |
| franka_msgs | source build | `sim2real_adlros/src/franka_ros2/franka_msgs/` | Message types for FrankaRobotState, error reporting | Must be `colcon build`'d before any node importing it can run |
| ros-humble-ament-cmake | <4.0 | Pixi / conda-forge | Build system pin (sim2real_adlros INSTRUCTION.md) | Version pin is constitutional — do not relax without a Bill |
| numpy | <=2.4.3 | Pixi / conda-forge | ROS2-side numerics (separate env from Crucible side) | Version ceiling per sim2real_adlros pixi.toml |

### Simulation framework

| Library | Version | Source | Purpose | Known issues |
|---------|---------|--------|---------|--------------|
| (Isaac Sim / Isaac Lab) | TBD | TBD | Controller-behaviour validation (deferred) | Slot reserved — sim choice deferred per Active Firmware Toolchain. Fill in via `/toolchain add lib` when committed. |

---

## Repository Registry

| Repo | Branch | Purpose | Notes |
|------|--------|---------|-------|
| ~/Documents/crucible-lite (this repo) | `main` | Constitutional governance + analysis / scaffold infrastructure. Owns Amendment 1, Channel & Topic Map, Data Stream Format, and the per-trial post-processing once it lands in `src/`. | Commit policy here: any change to constitutional records (`docs/governance/`, `docs/device_context.md`, `docs/toolchain_config.md`) must reference a ratified Amendment or an enacted Bill in the commit message. |
| ~/Documents/sim2real_adlros | `updated_sim2real` | ROS2 Humble + franka_ros2 control workspace. Owns the live topic stream (`/franka_robot_state_broadcaster/*`), controller configs (`configs/controllers/`), and the trial-runner scripts (`experiments/`, `scripts/`). Remote: `git@github.com:McGill-Applied-Dynamics-Lab/adl-ros2.git`. | Read + invoke only from this Crucible project. Do not commit Crucible artefacts here. franka_msgs builds from `src/franka_ros2/franka_msgs/` — see INSTRUCTION.md before first build. |
| ~/Documents/flexiforce/flexiforce_reader | `main` | DAQ-side Python — wire protocol (`protocol.py`), serial reader, GUI, calibration store. Remote: `git@github.com:SNI22/flexiforce_reader.git`. | Vendor protocol is canonical here. If the DAQ frame format changes, this repo updates first, then `docs/toolchain_config.md` Data Stream Format updates to match. |
| ~/Documents/flexiforce | n/a (directory, not a git repo) | Holds the vendor PDF `8路测量系统二次开发指南.pdf`, vendor CVI distribution kit `cvidistkit.flexiforce_1lbs`, and the `flexiforce_reader` submodule directory. | Vendor reference material only — read-only. The PDF is the authoritative source for the 18-byte frame format and the vendor K-formula (which this project does not use). |

---

## Stage Status

```
Spec Gate  — Device Specification:  NOT STARTED
Stage 0    — HIL Toolchain Lock:    NOT STARTED
Stage 1    — Simulation:            NOT STARTED
Stage 2    — Firmware Integration:  NOT STARTED
Stage 3    — Field Test:            NOT STARTED
Stage 4    — Host Integration:      NOT STARTED
```

---

## Constitutional References

- **Amendment 3 (Toolchain Alignment):** This file is the live implementation of the active toolchain record. Any change to the active toolchain requires updating this file and ratifying or amending Amendment 3.
- **Amendment 4 (Three-Strike Rule):** Blocked toolchain entries in this file are the formal record of strikes. Three strikes → block mandatory.
- **Amendment 2 (Stage Gate Order):** Stage status table above is the authoritative gate record. Stage N cannot open until Stage N-1 is CLOSED here.
