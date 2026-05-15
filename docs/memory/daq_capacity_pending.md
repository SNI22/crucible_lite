---
name: daq-capacity-pending
description: "Custom 8-channel DAQ is currently full (Ch 0-6 used, Ch 7 spare); 5 incoming A301-25 sensors will require a capacity decision before wiring."
metadata:
  type: project
---

The 8-channel custom CH340T DAQ has Ch 0–4 = A301-1 bench feet (1–5), Ch 5–6 = A301-25 finger-pads (L, R), Ch 7 = spare. An additional 5× A301-25 sensors are incoming with location TBD — they cannot all be wired without changing the DAQ topology.

**Why:** Recorded during /toolchain init on 2026-05-15. The user has 6× A301-1 (5 wired, 1 unwired spare) and 2× A301-25 (both wired), with 5× A301-25 inbound. Total A301-25 once received = 7, but only 1 free DAQ channel — surfaced as a flag in `docs/toolchain_config.md` Channel & Topic Map but not yet decided.

**How to apply:** Before wiring any of the 5 incoming A301-25 sensors, a decision must be made: (a) add a second 8-ch DAQ, (b) multiplex channels, or (c) restrict which sensors are live per trial. This is a Bill-level change (touches the Contact Force evidence source for Amendment 1). Related: [[project-comparison-framing]].
