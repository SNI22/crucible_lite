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
Board:    Custom STM32F103 PVDF Signal Conditioning PCB (revision 2023-02-20)
          Schematic: ~/Documents/piezo_circuit/PVDF压电采集资料/PVDF压电采集系统资料/
                     Schematic_PVDF压电信号调理系统_2023-02-20.pdf
MCU:      STM32F103C8T6, ARM Cortex-M3, 72 MHz, 64 KB flash / 20 KB SRAM, LQFP-48
Sensors:  PVDF + proof-mass cantilever (off-board, via H1 1×2 header).
          Mounting per ~/Documents/piezo_circuit/SENSOR_MOUNTING.md —
          full-area epoxy to ceramic tile floor; ≤ 3 m max range.
External: Raspberry Pi 5 (Linux host running detection algorithm and CSV capture);
          ST-Link V2 or J-Link SWD probe;
          USB-UART adapter (CH340 on Alientek "Warship" board if used, or external).
Notes:    Scope-reduced pass — only P1 (floor acceleration) implemented.
          P2 (microphone) and P3 (WiFi sensing) deferred to a future stage gate.
          Two known Article I violations carried forward from prior firmware:
            (1) `accur = 0.015295` (18× analog gain) baked in — needs Bill for
                boot-time self-calibration
            (2) `ADC offset = 1890` (DC zero-code) baked in — same fix
          HCNR200-500E linear optocoupler in BOM but not in current build.

          Alternative signal path (contingency, not current build):
          Tap the analog output of the OP07 final gain stage (test header H3/H4)
          directly into a Raspberry Pi ADC hat (e.g., ADS1263 high-precision hat).
          The STM32 MCU then becomes inactive — the Pi 5 does sampling and analysis.
          Useful escape valve if the STM32 onboard ADC's ~47.6 kS/s + 12-bit
          resolution proves inadequate (noise floor, dynamic range, or aliasing on
          tile floors). Prior repo's ~/Documents/piezo_circuit/raspberry_pi/ folder
          attempted ADS1263 at 7200 SPS → decimated to 5000 SPS but was abandoned
          due to DOA hat hardware; a replacement hat would resurrect this path.
          Switching to this path is a Bill-level change (Amendment 3) — not allowed
          mid-stage.
```

---

## Pin Map

| Signal | STM32 pin | Port/pin | Function | Caution |
|--------|-----------|----------|----------|---------|
| Piezo_ADC | PA6 | ADC1_IN6 | Analog input from OP07 U9 output (post-conditioning) | Sampled at 47.6 kS/s, 239.5-cycle sample time, DMA1 Ch1 |
| Dout_Trigger | PB15 | EXTI15 | LM311 comparator output (event trigger) | Threshold set by RP5 trim — record current setting in calibration log |
| UART1_TX | PA9 | USART1 TX | UART to host @ 115200 baud | Wired to H15 header and CH340 if Warship board used |
| UART1_RX | PA10 | USART1 RX | UART from host @ 115200 baud | Currently unused in main loop |
| OLED_SCL | PB6 | I2C1 SCL | OLED SSD1306 clock | 5.1 kΩ pull-up to 3.3 V (R58) |
| OLED_SDA | PB7 | I2C1 SDA | OLED SSD1306 data | 5.1 kΩ pull-up to 3.3 V (R59) |
| XTAL_IN | OSC_IN | — | 8 MHz HSE crystal X2 | 22 pF load caps C11/C12 |
| XTAL_OUT | OSC_OUT | — | 8 MHz HSE crystal X2 | — |
| RESET | NRST | — | Reset button | Pull-up R12 10 kΩ |
| BOOT0 | BOOT0 | — | Bootloader select on H15 header | Tied LOW for normal boot |
| Debug_GPIO | PA11, PA2, PA3, PA4 | GPIO | Header H6 (general I/O) | Currently unused |

---

## Active Firmware Toolchain

```
Build:          Keil MDK-ARM (free size-limited edition; image < 32 KB)
                Project: ~/Documents/piezo_circuit/PVDF压电采集资料/采集代码/USER/Template.uvprojx
                Library: ST Standard Peripheral Library (SPL, vendored — not HAL/CubeMX)
                Build host: Windows laptop (Keil is Windows-only; no Linux/CLI build path)
                Status: firmware frozen for this stage gate — no active development
                Known Article I violations: `accur = 0.015295` and `ADC offset = 1890`
                  baked into main.c — see Hardware Notes for fix plan
Flash:          ST-Link V2 SWD (primary) via Keil µVision built-in flasher
                Alternative: UART bootloader via BOOT0 = HIGH on H15 header +
                             `stm32flash` on Pi 5 host
Serial monitor: ~/Documents/piezo_circuit/receiver/receiver.py
                  PC-side capture (CSV write + key-tag events) on Pi 5 host
                  Formats supported: FireWater (ASCII), JustFloat (binary), RawData
                  Baud: 115200 (firmware USART1 default)
                  CSV schema: sample_index,value,event
                  Transport: Bluetooth-serial bridge (HC-05/06 SPP module on USART1)
                             OR direct USB-UART (CH340)
                Alternative for quick checks: minicom -b 115200 -o -D /dev/ttyUSB0
Wireless recv:  N/A — STM32F103 has no onboard wireless
                Alerts: routed via Pi 5 host (network/SMS/etc., implementation TBD)
                WiFi sensing module (P3): deferred to a future stage gate
Simulation:     ~/Documents/piezo_circuit/analysis/floor_sim.py
                  OpenSeesPy Kirchhoff plate model with `bathroom` preset
                  Emits CSV in same sample_index,value,event format as receiver.py
                  Enables signal-only Stage 1 simulation path (no firmware-in-loop required)
                Signal-only path is the primary Stage 1 simulator.
                Renode-based firmware-in-loop simulation: not configured (STM32F103
                  is Renode-supported but not wired up here; defer unless needed).
```

---

## Blocked Toolchains

None.

**Project cost constraint** (not a block, a guideline for advisors and Bill drafters):
This pass operates on the existing PVDF + STM32F103 PCB hardware. Any proposed
hardware addition that requires a new component purchase, a new PCB spin, or a
new MCU (e.g., MLX thermal camera, dedicated audio codec board, dual-MCU architecture)
is "too costly" for this stage and must be raised as a Bill with explicit cost
justification before procurement. The hw-advisor and bill-drafter must flag any
suggestion that would breach this constraint.

This is not a formal `/toolchain block` — it is a budget gate. A future Bill may
relax it for a specific component without requiring a Judicial Hearing.

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

> Use `/toolchain add lib` to add entries. Host-side Python versions pinned at
> `/toolchain scaffold` (when `src/` modules are generated).

### Firmware-side (Keil MDK, vendored — no package manager)

| Library | Version | Source | Purpose | Known issues |
|---------|---------|--------|---------|--------------|
| STM32F10x_StdPeriph_Lib | V3.5.0 (ST Standard Peripheral Library) | Vendored at `~/Documents/piezo_circuit/PVDF压电采集资料/采集代码/STM32F10x_FWLib/` | Low-level peripheral access (ADC, DMA, USART, GPIO, RCC) — predates HAL/Cube | Deprecated by ST since 2014; long-term Bill candidate to migrate to HAL/LL |
| CMSIS Core (Cortex-M3) | per Alientek Warship template (to verify) | Vendored at `~/Documents/piezo_circuit/PVDF压电采集资料/采集代码/CORE/` | ARM Cortex-M3 core abstraction, startup, `system_stm32f10x.c` | — |
| OLED SSD1306 driver | local (author-written) | `~/Documents/piezo_circuit/PVDF压电采集资料/采集代码/HARDWARE/OLED/` | I2C OLED waveform / voltage display | Two drivers coexist (`OLED_I2C` + `OLED0561`); `main.c` calls both Init paths |

### Host-side (Pi 5, Python — versions TBD, pin at `/toolchain scaffold`)

| Library | Version | Source | Purpose | Known issues |
|---------|---------|--------|---------|--------------|
| numpy | TBD | PyPI | Numerical arrays for analysis and simulation | — |
| scipy | TBD | PyPI | Signal processing (filters, FFT, envelope) | — |
| matplotlib | TBD | PyPI | Plotting (plotter agent uses `Agg` backend) | — |
| pyserial | TBD | PyPI | `receiver.py` serial bridge | — |
| GUI framework | TBD — confirm by reading `receiver.py` (PyQt5 or tkinter) | PyPI / system | `receiver.py` interactive GUI | — |
| openseespy | TBD | PyPI | Kirchhoff plate floor simulator (`floor_sim.py`) | — |

---

## Repository Registry

> One entry per git repository in use. Use `/toolchain add repo` to add entries.

| Repo | Path | Remote | Branch | Purpose | Access |
|------|------|--------|--------|---------|--------|
| piezo_fall | /home/sni22/crucible/piezo_fall | (TBD — no remote configured yet) | master | This project — Crucible-governed fall detection | read+write |
| piezo_circuit | /home/sni22/Documents/piezo_circuit | git@github.com:SNI22/piezo-circuit.git | main | Prior fall-detection work — reference for STM32 firmware (Keil), custom PCB schematics, `receiver.py`, `analysis/floor_sim.py`, sensor-mounting protocol, feature dictionary, prior test data | **read-only** — agents in this project may not commit to this repo |
| crucible-core | /home/sni22/crucible/core | (no remote) | master | Crucible governance framework template — source of CONSTITUTION.md / amendments.md / agent definitions for this project | **read-only** |

---

## Stage Status

```
Spec Gate  — Device Specification:  CLOSED 2026-05-15 (Amendment 1 ratified, commit e06398e)
Stage 0    — HIL Toolchain Lock:    OPEN — adapted protocol (see below)
Stage 1    — Simulation:            NOT STARTED
Stage 2    — Firmware Integration:  NOT STARTED
Stage 3    — Field Test:            NOT STARTED
Stage 4    — Host Integration:      NOT STARTED
```

---

## Stage 0 — Adapted HIL Toolchain Lock Protocol

The framework default Stage 0 assumes four sequential flashable test programs
(counter → sensor readout → algorithm-on-MCU over USB → algorithm-on-MCU over
wireless). This project's architecture does not fit that model: the MCU
performs sampling + UART streaming only, and the algorithm runs on the Pi 5
host. The protocol below is the adapted Stage 0 for piezo_fall; it preserves
the intent of the framework's gates (prove the entire pipeline works before
algorithm development) while matching the actual hardware.

| Gate | Test | Pass criterion |
|------|------|----------------|
| **0.1** | **MCU alive.** Power the STM32 (custom PCB or Alientek Warship dev board), connect transport (USB-UART or HC-05/06 BT-serial bridge) to the Pi 5 / laptop receiver, run `receiver.py`. | Continuous UART data stream visible in receiver.py at 115200 baud; no resets across a 60-second observation window. |
| **0.2a** | **ADC plausibility.** With piezo sensor connected, observe the live receiver.py trace at rest, then tap the floor 30 cm from the sensor. | Quiet baseline near ADC count 1890 (DC zero-code, may vary per board ±100) ; clear transient spike clearly above baseline on tap. |
| **0.2b** | **Streaming rate verification.** Capture a 10-second receiver.py session at rest. Count sample rows in the resulting CSV. | ≥ 10,000 sample rows (≥ 1 kHz × 10 s) — matches Amendment 1's "≥ 1 kHz piezo" clause. Significantly fewer rows is a HARD FAIL — either flash modified firmware that streams at ≥ 1 kHz, or open an Amendment 3 Bill for an alternative signal path. Record the actual measured rate in `device_context.md` Test Results table. |
| **0.3** | **Receiver capture end-to-end.** Capture a 30-second receiver.py session; key-tag one "step" event with SPACE while tapping near the sensor. | Valid CSV with `sample_index,value,event` schema; the tagged event row exists at a sample index close to the actual tap (within receiver.py's documented tag latency). |
| **0.4** | **Wireless / transport check.** If the deployment uses an HC-05/06 BT-serial bridge, repeat gate 0.1 over BT instead of USB and confirm receiver.py captures equivalently. If deployment is USB-only, explicitly record that and skip this gate. | BT capture matches USB capture in format and continuity for ≥ 60 s, OR explicit "BT not in deployment scope — USB-only" record in Test Results table. |

**Procedure for each gate:** human executes the hardware action; the result
is recorded in `docs/device_context.md` Test Results table by the human; the
session orchestrator confirms recorded pass/fail and gates the next test.

**[JUSTICE GATE S0]** All four gates pass + records committed → invoke
`stage-compactor` to close Stage 0 → run `/toolchain lock` to stamp the
config as Stage 0 validated.

---

## Constitutional References

- **Amendment 3 (Toolchain Alignment):** This file is the live implementation of the active toolchain record. Any change to the active toolchain requires updating this file and ratifying or amending Amendment 3.
- **Amendment 4 (Three-Strike Rule):** Blocked toolchain entries in this file are the formal record of strikes. Three strikes → block mandatory.
- **Amendment 2 (Stage Gate Order):** Stage status table above is the authoritative gate record. Stage N cannot open until Stage N-1 is CLOSED here.
