# Crucible Case Law

This file records all Judicial Hearing rulings. Entries are written by the prevailing
attorney immediately after the Justice's ruling, before any implementation begins.

Live entries accumulate full argument text. Frozen entries (after stage closeout via
`stage-compactor`) contain only the compact operational record.

---

## Active Precedents

### Case 1: Amendment 1 sample-rate revision (Bill 001)
**Date:** 2026-05-16
**Positions:**
  A — revise per Bill (mandate INT_MARK=0 in Amendment text + sample-rate metadata)
  B — metadata-only revision (drop the INT_MARK binding from Amendment text)
**Prevailing position:** B (with modification — see ruling text)

**Justice's ruling:**
Position B prevails on the textual question (no firmware-config strings in
Amendment 1 text — Amendment 3 owns the toolchain layer). However, the rate
floor in Amendment 1 P1 is RAISED from ≥ 1 kHz to **≥ 1.5 kHz** to mechanically
enforce INT_MARK=0 without embedding firmware identifiers in Amendment text:
no INT_MARK setting other than 0 satisfies the new 1.5 kHz floor, achieving
Position A's safety goal through the rate specification itself.

In addition, every recorded CSV MUST include three metadata fields:
`int_mark`, `transport`, `measured_rate_hz`. CSVs without these are not
admissible as Article I evidence.

**Physical/empirical basis (Benjamin Franklin Principle):**
  - INT_MARK rate table (toolchain_config.md Active Firmware Toolchain):
    INT_MARK=0 → ~1.9 kHz (USB-UART or BT-SPP); 1 → 500 Hz; 2 → 200 Hz;
    3 → 100 Hz; 4 → 50 Hz. Only 0 meets ≥ 1.5 kHz.
  - Nyquist: bathroom-slab FEA model excites plate modes to ~600 Hz.
    1.5 kHz Nyquist (750 Hz) covers this with margin; lower rates alias
    plate-mode content into the 5–40 Hz fall-signal band.
  - BT-SPP throughput evidence (this hearing's clarifying analysis):
    HC-05/06 sustains ~1.7-1.9 kHz at 115200 baud with ASCII output.
    1.5 kHz is the conservative deliverable rate on both transports.
  - Active firmware confirmed at
    ~/Documents/piezo_circuit/代码 - 调节发送频率/USER/main.c (FW-IDENTITY
    resolved 2026-05-16). Source main loop reads ADC_DMA_IN and
    `USART2_printf("%.3f\n", ...)` once per iteration.

**Device outcome protected (Thomas Jefferson Principle):**
  - Real falls (5–40 Hz floor accel) are captured without aliasing artifacts
    from plate-mode content above 750 Hz.
  - Silent runtime rate reductions (EXTI press → INT_MARK > 0) become
    immediately inadmissible as evidence, because the resulting CSV
    cannot pass the metadata-admissibility gate at ≥ 1.5 kHz.
  - Sim-to-real verification reproducibility: future tests will have
    the three metadata fields needed to interpret each recording.
  - Avoids embedding firmware paths or baud arithmetic in Amendment 1
    text — preserves Amendment 1's independence from firmware revisions
    (e.g., the known 4069→4095 typo fix doesn't trigger an Amendment cycle).

**Conditions on application:**
  1. Amendment 1 P1 text revised in this commit; effective immediately.
  2. toolchain_config.md remains the single source of truth for the
    INT_MARK=0 deployment constraint (Amendment 3 jurisdiction).
  3. receiver.py + future data-collection tooling must capture
    `int_mark`, `transport`, `measured_rate_hz` per session as the
    minimum mandatory metadata. Implementation deferred to next
    data-collection sprint, but no NEW CSVs admissible without it.
  4. Existing bathroom_testing CSVs remain admissible as legacy
    evidence (pre-ruling), but a documented best-estimate of each
    CSV's INT_MARK + measured rate should be appended to
    device_context.md Test Results table when next consulted.

**Enacted bill:** Bill 001 (with modification — rate raised to 1.5 kHz)
**Implementation branch:** piezo_fall (this branch, commit forthcoming)

---

---

## Frozen Precedents

*(Populated by stage-compactor at each stage gate.)*
