# BILL 002 — Revise Amendment 1 P1 rate floor from ≥1.5 kHz to ≥1 kHz

**Proposed by:** human engineer
**Date:** 2026-05-16
**Status:** ENACTED by Case 2 (same date) — by-consent ruling, empirical evidence uncontested
**Traces to:** Article I (correcting an empirically-falsified amendment clause)

---

## The Change

Revise Amendment 1 P1 clause: rate floor `≥ 1.5 kHz` → `≥ 1 kHz`.
All other Case 1 changes (CSV metadata requirements, admissibility rule)
stay in place.

## Evidence

Empirical timestamped recording at
`~/Documents/piezo_circuit/bedroom_pilot_testing/catfood_bedroom_2.txt`:
  - First sample: 04:07:53.795
  - Last sample (line 47): 04:07:53.829
  - 47 samples in 34 ms → effective rate ~1.38 kHz
  - BT-bursting visible: 4-6 samples per millisecond cluster

Case 1's premise that BT-SPP sustains ~1.7–1.9 kHz over a HC-05/06 +
external USB BT dongle is contradicted by this measurement. Real
deployment achieves ~1.38 kHz, which fails Case 1's 1.5 kHz floor.

## Mechanical enforcement after this Bill

With ≥ 1 kHz floor + INT_MARK rate table:
  INT_MARK=0: ~1.38 kHz observed (passes ≥ 1 kHz) ✓
  INT_MARK=1: 500 Hz (fails) ✗ — still forbidden
  INT_MARK=2: 200 Hz (fails) ✗
  INT_MARK=3: 100 Hz (fails) ✗
  INT_MARK=4: 50 Hz (fails) ✗

The mechanical-enforcement property is preserved (only INT_MARK=0 can
satisfy the floor), at the realistic rather than aspirational threshold.

## What stays from Case 1

  - Mandatory CSV metadata (int_mark, transport, measured_rate_hz)
  - Inadmissibility rule for CSVs missing these fields
  - INT_MARK=0 deployment constraint in toolchain_config.md

Only the rate number changes.
