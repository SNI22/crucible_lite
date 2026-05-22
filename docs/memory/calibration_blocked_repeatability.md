---
name: calibration-blocked-repeatability
description: "A301-1 calibration is blocked by a non-monotonic, non-repeatable raw sensor response; suspected TPU 90A foot spreading load off the active area"
metadata: 
  node_type: memory
  type: project
  originSessionId: 923b8ca9-f1ab-4cb2-a5b8-034e144d327e
---

As of 2026-05-21, A301-1 dead-weight calibration is **blocked** by a hardware
fault, not a software/fit issue. First attempt on ch0 gave physically
impossible data: force rose 10× (0.52→4.97 N) but raw barely moved (518→825),
2 N read lower than 1 N (non-monotonic), and the 53 g level varied ±301 counts
across 5 repeats (non-repeatable). Fit adj-R² 0.24.

**Leading hypothesis:** the bench **TPU 90A calibration foot is too soft** — it
spreads the point load around the ~9.5 mm A301-1 active area instead of onto
it, so the element sees a small inconsistent fraction of the applied weight.
Likely fix: a rigid load concentrator (matched-diameter puck on the sensor),
which would change the Bill 0004 fixturing decision (TPU 95A pad → rigid) and
need a Bill amendment.

Diagnostic tool: `scripts/calibrate_a301_1.py --channel N --monitor` (live raw
readout). Decisive test: press directly on the sensor element vs through the
90A foot — if direct swings clean and through-foot doesn't, the foot is
confirmed.

Also: operator states A301-1 reads to 15 N per foot, contradicting
`device_context.md:127` (4.4 N) — correct that doc once the front-end works.
See [[dominant_error_source_flexiforce]] and [[a301_calibration_mts]].
