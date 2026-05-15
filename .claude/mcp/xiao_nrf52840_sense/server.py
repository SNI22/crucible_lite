#!/usr/bin/env python3
"""
MCP server — Seeed XIAO nRF52840 Sense hardware reference.

Serves verified hardware specifications for the XIAO nRF52840 Sense board
and its onboard LSM6DS3TR-C IMU. Every response includes a source citation
so any value extracted here that enters a firmware threshold satisfies
Article I (Signal First) — the citation travels with the number.

Usage (Claude Code):
  Register in .claude/settings.json under "mcpServers" (see README in this dir).
  Then hw-advisor and attorneys can call these tools directly during sessions.

Transport: stdio (JSON-RPC 2.0)
Protocol:  Model Context Protocol (MCP) 1.0

Sources:
  [S1] Seeed Studio XIAO nRF52840 Sense Wiki
       https://wiki.seeedstudio.com/XIAO_BLE/
  [S2] STMicroelectronics LSM6DS3TR-C datasheet DS12232 Rev 5
       https://www.st.com/resource/en/datasheet/lsm6ds3tr-c.pdf
  [S3] Nordic Semiconductor nRF52840 Product Specification v1.7
       https://infocenter.nordicsemi.com/pdf/nRF52840_PS_v1.7.pdf
"""

import json
import sys
from typing import Any

# ── MCP wire protocol helpers ─────────────────────────────────────────────────

def send(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def respond(id: Any, result: Any) -> None:
    send({"jsonrpc": "2.0", "id": id, "result": result})


def error(id: Any, code: int, message: str) -> None:
    send({"jsonrpc": "2.0", "id": id, "error": {"code": code, "message": message}})


# ── Tool definitions ──────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "board_summary",
        "description": (
            "Returns the XIAO nRF52840 Sense board overview: MCU, memory, "
            "connectivity, onboard sensors, and key variant notes. "
            "Use before /toolchain init to verify board model and MCU spec."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "imu_spec",
        "description": (
            "Returns LSM6DS3TR-C IMU specification for a requested parameter. "
            "Each value includes the datasheet section and page so it can be "
            "cited as Amendment 1 primitive evidence. "
            "Parameters: noise_density, odr_options, full_scale, i2c_address, "
            "who_am_i, power_on_time, all."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "param": {
                    "type": "string",
                    "description": "noise_density | odr_options | full_scale | i2c_address | who_am_i | power_on_time | all"
                }
            },
            "required": ["param"]
        }
    },
    {
        "name": "pinout",
        "description": (
            "Returns the XIAO nRF52840 Sense pin map. "
            "Includes Arduino pin number, nRF52840 port/pin, function, and "
            "any cautions. Use before /toolchain add pins."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "signal": {
                    "type": "string",
                    "description": "Optional: filter by signal name (e.g. IMU_SDA, LED_RED). Omit for full map."
                }
            },
            "required": []
        }
    },
    {
        "name": "known_issues",
        "description": (
            "Returns documented hardware bring-up issues for the XIAO nRF52840 Sense. "
            "Covers NFC/GPIO conflict, IMU power sequencing, and USB-C enumeration. "
            "Attorneys may cite these as evidence in hardware hearings."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]

# ── Tool implementations ──────────────────────────────────────────────────────

def tool_board_summary() -> str:
    return """XIAO nRF52840 Sense — Board Summary
Source: [S1] Seeed Studio XIAO nRF52840 Sense Wiki

MCU:         Nordic nRF52840, ARM Cortex-M4F @ 64 MHz
Flash:       1 MB internal + 2 MB QSPI external
RAM:         256 KB
BLE:         Bluetooth 5.0, -95 dBm sensitivity, 8 dBm TX power
USB:         USB-C, USB 2.0 full-speed (12 Mbit/s)
Onboard IMU: STMicroelectronics LSM6DS3TR-C (6-axis accel + gyro)
Onboard MIC: MSM261D3526H1CPM PDM microphone
Supply:      3.3 V (onboard LDO from USB 5 V or Li-Po)
Dimensions:  21 × 17.5 mm

CRITICAL VARIANT NOTE [S1]:
  Must be the *Sense* variant (SKU 102010448).
  The standard XIAO nRF52840 (SKU 102010448) has NO onboard IMU.
  The two boards are physically identical — verify SKU before ordering.

Arduino core: Seeed nRF52 mbed (mbed_nano FQBN group)
FQBN:         Seeed XIAO nRF52840 Sense — use during /toolchain init
"""


def tool_imu_spec(param: str) -> str:
    specs = {
        "noise_density": """LSM6DS3TR-C — Noise Density
Source: [S2] DS12232 Rev 5, Table 3 (Electrical Characteristics)

Accelerometer noise density:  80 μg/√Hz  (@ FS = ±2g, ODR = 1.66 kHz)
Gyroscope noise density:       4 mdps/√Hz (@ FS = ±250 dps, ODR = 1.66 kHz)

Article I use: these values set the minimum detectable signal floor.
Any threshold below 3× noise floor (240 μg for accel, 12 mdps for gyro)
cannot be reliably distinguished from noise — cite this when justifying
detection thresholds in firmware.""",

        "odr_options": """LSM6DS3TR-C — Output Data Rate Options
Source: [S2] DS12232 Rev 5, Table 4 (ODR and Power Mode)

Accelerometer ODR (Hz): 12.5, 26, 52, 104, 208, 416, 833, 1666, 3333, 6666
Gyroscope ODR (Hz):     12.5, 26, 52, 104, 208, 416, 833, 1666

High-performance mode active above 12.5 Hz for both axes.
Power-down: ODR = 0 (register CTRL1_XL / CTRL2_G bits ODR_XL / ODR_G = 0000)

Article I use: ODR must be ≥ 2× the highest signal frequency of interest
(Nyquist). For walking gait (fundamental ~2 Hz, heel-strike transient ~50 Hz):
ODR = 104 Hz is the minimum; 208 Hz recommended. Cite this in CTRL1_XL.""",

        "full_scale": """LSM6DS3TR-C — Full-Scale Options
Source: [S2] DS12232 Rev 5, Table 4

Accelerometer FS: ±2g, ±4g, ±8g, ±16g
  Sensitivity:    0.061, 0.122, 0.244, 0.488  mg/LSB respectively

Gyroscope FS:     ±125, ±250, ±500, ±1000, ±2000  dps
  Sensitivity:    4.375, 8.75, 17.5, 35, 70  mdps/LSB respectively

Article I use: FS must contain the peak domain primitive value plus margin.
For walking gait: accel peak ~6g (heel-strike) → use ±8g minimum.
Push-off gyro peak ~300 dps → use ±500 dps minimum. Cite domain primitive
measurement when setting CTRL1_XL FS_XL and CTRL2_G FS_G bits.""",

        "i2c_address": """LSM6DS3TR-C — I2C Address
Source: [S2] DS12232 Rev 5, Section 6.1.1

Primary address (SDO/SA0 = GND):  0x6A
Alternate address (SDO/SA0 = VCC): 0x6B

On XIAO nRF52840 Sense: SDO pin is tied to GND → address is always 0x6A.
WHO_AM_I register (0x0F) returns 0x6A as device identifier.

I2C bus: SDA = P0.07 (Arduino pin 4), SCL = P0.27 (Arduino pin 5)
Max I2C speed: 400 kHz (Fast Mode) [S2 Section 6.1]""",

        "who_am_i": """LSM6DS3TR-C — WHO_AM_I Register
Source: [S2] DS12232 Rev 5, Section 9.11

Register address: 0x0F
Expected value:   0x6A

Use in firmware bring-up to confirm IMU is alive and responding on I2C.
If WHO_AM_I ≠ 0x6A: check power pin (P1.08 must be HIGH ≥ 5 ms before
first I2C transaction), check I2C address (SA0 pin state), check pull-ups.""",

        "power_on_time": """LSM6DS3TR-C — Power-On and Boot Time
Source: [S2] DS12232 Rev 5, Table 3 (Electrical Characteristics)

Boot time (power-on to first valid data): 35 ms (typical), 45 ms (max)

On XIAO nRF52840 Sense: IMU is powered via P1.08 (software-switched).
P1.08 must be driven HIGH, then firmware must wait ≥ 45 ms before the
first I2C transaction. Omitting this delay causes WHO_AM_I read failure
or all-zero sensor output on first read.

Article I use: cite [S2] Table 3 in the firmware delay constant:
  /* IMU_BOOT_DELAY_MS = 45 — LSM6DS3TR-C max boot time [S2 Table 3] */""",
    }

    if param == "all":
        return "\n\n---\n\n".join(specs.values())

    if param not in specs:
        valid = ", ".join(specs.keys()) + ", all"
        return f"Unknown parameter '{param}'. Valid options: {valid}"

    return specs[param]


def tool_pinout(signal: str = "") -> str:
    pins = [
        ("D0",        "0",   "P0.02", "GPIO / ADC",         "—"),
        ("D1",        "1",   "P0.03", "GPIO / ADC",         "—"),
        ("D2",        "2",   "P0.28", "GPIO / ADC",         "—"),
        ("D3",        "3",   "P0.29", "GPIO / ADC",         "—"),
        ("IMU_SDA",   "4",   "P0.07", "I2C SDA (IMU)",      "—"),
        ("IMU_SCL",   "5",   "P0.27", "I2C SCL (IMU)",      "P0.27 = NFC2 by default — configure as GPIO before use [S1]"),
        ("D6",        "6",   "P1.11", "UART TX / GPIO",     "—"),
        ("D7",        "7",   "P1.12", "UART RX / GPIO",     "—"),
        ("D8",        "8",   "P1.13", "SPI SCK / GPIO",     "—"),
        ("D9",        "9",   "P1.14", "SPI MISO / GPIO",    "—"),
        ("D10",       "10",  "P1.15", "SPI MOSI / GPIO",    "—"),
        ("IMU_POWER", "—",   "P1.08", "IMU VCC switch",     "Drive HIGH ≥ 45 ms before first I2C read [S2 Table 3]"),
        ("LED_RED",   "—",   "P0.26", "RGB LED red",        "Active LOW"),
        ("LED_GREEN", "—",   "P0.30", "RGB LED green",      "Active LOW"),
        ("LED_BLUE",  "—",   "P0.06", "RGB LED blue",       "Active LOW"),
        ("LED_PWR",   "—",   "P0.13", "Charge indicator",   "Active LOW, do not drive"),
        ("IMU_INT1",  "—",   "P0.11", "IMU interrupt 1",    "Optional — wire if using DRDY or threshold interrupt"),
    ]

    header = (
        "XIAO nRF52840 Sense — Pin Map\n"
        "Source: [S1] Seeed Studio XIAO nRF52840 Sense Wiki\n\n"
        f"{'Signal':<14} {'Arduino':>7}  {'nRF port/pin':<14} {'Function':<24} Caution\n"
        + "─" * 90
    )

    rows = []
    for name, ard, port, func, caution in pins:
        if signal and signal.upper() not in name.upper():
            continue
        rows.append(f"{name:<14} {ard:>7}  {port:<14} {func:<24} {caution}")

    if not rows:
        return f"No pin found matching '{signal}'."

    return header + "\n" + "\n".join(rows)


def tool_known_issues() -> str:
    return """XIAO nRF52840 Sense — Known Hardware Issues
Source: [S1] Seeed Studio XIAO nRF52840 Sense Wiki, community reports

ISSUE 1 — NFC pins as GPIO (P0.27 / P0.09)
  P0.27 (IMU_SCL) and P0.09 are NFC antenna pins by default.
  Must be reconfigured as GPIO in firmware before use as I2C or digital IO.
  Arduino mbed core handles this automatically for SDA/SCL.
  Raw nRF SDK / Zephyr: call nfc_t2t_setup() or set NFCT_TASKS_DISABLE
  before accessing these pins.

ISSUE 2 — IMU power sequencing
  The LSM6DS3TR-C is powered via P1.08 (software-controlled VCC switch).
  If P1.08 is not driven HIGH before I2C init, WHO_AM_I returns 0xFF or 0x00.
  Firmware must: (1) set P1.08 HIGH, (2) delay ≥ 45 ms, (3) init I2C.
  Arduino library digitalWrite(PIN_LSM6DS3TR_C_POWER, HIGH) handles step 1.
  The delay must be explicit — do not rely on I2C init time.

ISSUE 3 — 3.3 V rail brownout during BLE advertising
  BLE TX draws ~15 mA peak. If the Li-Po is near depleted (<3.5 V),
  the 3.3 V LDO may momentarily drop, resetting the IMU.
  Symptom: WHO_AM_I reads correctly at startup but returns error mid-session.
  Mitigation: monitor battery voltage; alert before LDO drops below spec.

ISSUE 4 — USB-C enumeration after soft reset
  On some hosts, a soft reset (not power cycle) leaves the USB-C port in a
  state where the CDC serial port does not re-enumerate for 2–5 seconds.
  Not a hardware defect — host USB driver behaviour. Use a 3-second reconnect
  delay in firmware test scripts that rely on serial output after reset.
"""


# ── Request dispatcher ────────────────────────────────────────────────────────

def dispatch(method: str, params: dict, id: Any) -> None:
    if method == "initialize":
        respond(id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {
                "name": "xiao-nrf52840-sense",
                "version": "1.0.0"
            }
        })

    elif method == "tools/list":
        respond(id, {"tools": TOOLS})

    elif method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments", {})

        if name == "board_summary":
            respond(id, {"content": [{"type": "text", "text": tool_board_summary()}]})

        elif name == "imu_spec":
            respond(id, {"content": [{"type": "text", "text": tool_imu_spec(args.get("param", "all"))}]})

        elif name == "pinout":
            respond(id, {"content": [{"type": "text", "text": tool_pinout(args.get("signal", ""))}]})

        elif name == "known_issues":
            respond(id, {"content": [{"type": "text", "text": tool_known_issues()}]})

        else:
            error(id, -32601, f"Unknown tool: {name}")

    elif method == "notifications/initialized":
        pass  # no response needed for notifications

    else:
        error(id, -32601, f"Method not found: {method}")


# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue

        method = req.get("method", "")
        params = req.get("params", {})
        id = req.get("id")  # None for notifications

        dispatch(method, params, id)


if __name__ == "__main__":
    main()
