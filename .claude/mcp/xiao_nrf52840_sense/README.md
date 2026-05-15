# MCP Server — Seeed XIAO nRF52840 Sense

Reference example of a Crucible hardware documentation MCP server.

Serves verified specs for the XIAO nRF52840 Sense board and its onboard
LSM6DS3TR-C IMU. Every value includes a datasheet citation so it satisfies
Article I (Signal First) when used as the basis for a firmware threshold.

---

## What it provides

| Tool | When to use |
|---|---|
| `board_summary` | Before `/toolchain init` — confirms MCU, variant, FQBN |
| `imu_spec` | When setting ODR, full-scale, or detection thresholds — cites DS12232 |
| `pinout` | Before `/toolchain add pins` — complete pin map with cautions |
| `known_issues` | Before Stage 0 bring-up — documents NFC/GPIO, power sequencing issues |

---

## Registration

MCP servers are registered in `.mcp.json` at the project root (separate from `.claude/settings.json`):

```json
{
  "mcpServers": {
    "xiao-nrf52840-sense": {
      "command": "python3",
      "args": [".claude/mcp/xiao_nrf52840_sense/server.py"]
    }
  }
}
```

This file is already present in the repo. No extra steps needed — Claude Code picks it up automatically on session start.

No extra dependencies — stdlib only (json, sys).

---

## How it fits Crucible

This server is **read-only evidence infrastructure**. It does not make decisions.

- `hw-advisor` calls `imu_spec` to ground suggestions in datasheet values
  rather than relying on whatever the engineer typed into `device_context.md`
- Attorneys can call `known_issues` during a `/judicial hear` as admissible evidence
- The citation in every response (`[S2] DS12232 Rev 5, Table 3`) travels with
  the number into any document or comment that uses it — Article I is satisfied
  at the source, not retroactively

**What it is not:** this server does not fetch live web content. The specs are
pinned to a specific datasheet revision. If you update the hardware, update the
server and bump the revision tag — then amendment record reflects the change.

---

## Pattern for other boards / MCPs

Copy this directory, replace the spec data, keep the structure:

1. Each tool returns a string with a `Source: [SN]` citation on the first data line
2. "Article I use:" paragraphs explain how the value connects to a domain primitive
3. Server is stdlib-only, stdio transport, no external dependencies
4. Register in `.claude/settings.json` `mcpServers` block

Safe online document MCPs (datasheets, standards, regulatory docs) follow the
same pattern but fetch from a pinned URL or cached PDF instead of hardcoded strings.
The citation discipline is identical — source and revision must travel with the value.
