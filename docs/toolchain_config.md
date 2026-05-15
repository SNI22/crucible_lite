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
Board:    > [board model — e.g., "Seeed XIAO nRF52840 Sense 102010448"]
MCU:      > [MCU — e.g., "nRF52840, ARM Cortex-M4F, 64 MHz"]
Sensors:  > [sensors — e.g., "LSM6DS3TR-C IMU, I2C 0x6A"]
External: > [debug probes, PPK2, oscilloscope, etc. — or "none"]
Notes:    > [variant notes — e.g., "Must be Sense variant — on-board IMU only on Sense"]
```

---

## Pin Map

| Signal | Arduino pin | nRF52840 port/pin | Function | Caution |
|--------|-------------|-------------------|----------|---------|
| > [signal] | > [pin] | > [port/pin] | > [function] | > [caution or "—"] |

---

## Active Firmware Toolchain

```
Build:          > [FQBN or build system — e.g., "arduino:mbed_nano:nano33ble" or "Zephyr / PlatformIO"]
Flash:          > [flash method — e.g., "UF2 drag-drop" or "J-Link SWD"]
Serial monitor: > [serial monitor — e.g., "minicom 115200 8N1" or "python -m serial.tools.miniterm"]
Wireless recv:  > [BLE receiver script — e.g., "python crucible/transport/ble.py --device MyDevice"]
Simulation:     > [sim framework — e.g., "Renode 1.16 via crucible.sim.renode.RenoneBridge"]
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

## Firmware UART Format

> **Required for `/toolchain scaffold`** — fill in before running Stage 1.  
> This section defines what the firmware emits over UART. It is used to  
> generate `src/analysis.py` (UART parser) and `src/events.py` (event types).

```
session_end_marker: SESSION_END
```

### Event Definitions

> One block per UART event type the firmware emits. Add blocks as needed.

```
[[event]]
name:     > [logical name — e.g., "primary_event", "snapshot", "reading"]
marker:   > [text prefix that identifies this line — e.g., "STEP", "READING", "SNAPSHOT"]
pattern:  > [full regex — e.g., r"STEP\s+#(\d+)\s+ts=(\d+)\s+value=([\d.]+)"]
fields:   > [comma-separated field names matching capture groups — e.g., "index, ts_ms, value"]
types:    > [comma-separated Python types — e.g., "int, float, float"]
```

### Binary Export Format (optional)

> Fill in only if firmware supports a binary bulk export over BLE or UART.

```
magic:  > [4-byte magic — e.g., "PROJ" or leave blank]
struct: > [Python struct format string — e.g., "<IIHHBb"]
fields: > [comma-separated field names matching struct groups]
scale:  > [comma-separated scale factors — e.g., "1, 1, 0.1, 0.1, 1, 1"]
```

---

## Library Manifest

> One entry per firmware library. Use `/toolchain add lib` to add entries.

| Library | Version | Source | Purpose | Known issues |
|---------|---------|--------|---------|--------------|
| > [name] | > [version — pin exactly] | > [source] | > [purpose] | > [issues or "—"] |

---

## Repository Registry

> One entry per git repository in use. Use `/toolchain add repo` to add entries.

| Repo | Branch | Purpose | Notes |
|------|--------|---------|-------|
| > [path or URL] | > [branch] | > [purpose] | > [access notes or "—"] |

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
