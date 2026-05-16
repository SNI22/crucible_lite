# BILL 001 — Amendment 1 Sample-Rate Clause Revision

**Proposed by:** human engineer + spec-collector (drafted with assistance)
**Date:** 2026-05-16
**Status:** DRAFT — awaiting Judicial Hearing
**Traces to:** Article I

---

## The Change

Revise Amendment 1's clause for primitive P1 (Floor acceleration) sample rate
to accurately reflect the active firmware's variable-rate behavior, AND mandate
a binding rule that links Amendment 1 compliance to a specific firmware
configuration setting.

---

## Evidence

The active firmware was identified on 2026-05-16 at:
```
~/Documents/piezo_circuit/代码 - 调节发送频率/USER/main.c
```

Its main loop (verbatim):
```c
while(1) {
    if(INT_MARK==1)t=2;
    if(INT_MARK==2)t=5;
    if(INT_MARK==3)t=10;
    if(INT_MARK==4)t=20;
    if(INT_MARK!=0)delay_ms(t);
    USART2_printf("%.3f\n",(ADC_DMA_IN*3.3/4069)-1.65);
    IWDG_Feed();
}
```

Streaming rate behavior (cited in toolchain_config.md Stage 0 Ruling):

| INT_MARK | Delay | Streaming rate |
|---|---|---|
| 0 (default) | 0 ms | ~1.9 kHz (UART-throughput-bound at 115200 baud × 6 char/sample) |
| 1 | 2 ms | 500 Hz |
| 2 | 5 ms | 200 Hz |
| 3 | 10 ms | 100 Hz |
| 4 | 20 ms | 50 Hz |

**Article I problem:** Amendment 1 currently mandates "P1 measured via piezo at
≥ 1 kHz." Of these five INT_MARK settings, only INT_MARK=0 satisfies this
clause. INT_MARK=1–4 violate Amendment 1.

The firmware ships with INT_MARK=0 default, BUT an external EXTI key can change
it at runtime. If the device is deployed with the key accidentally pressed, the
device runs at 50–500 Hz and silently violates Amendment 1 with no warning.

The bathroom_testing CSV recordings (used in Stage 1 sim-to-real verification)
were captured at some INT_MARK setting that was never logged — empirical
event-spacing analysis suggests INT_MARK=0 (~1.9 kHz) but this is unconfirmed,
which itself is a SAMPLE-RATE-PARTIALLY-RESOLVED Stage 0 finding.

---

## Proposed Amendment 1 Revision

Replace the current P1 clause:
```
P1 — Floor acceleration (m/s²) — inertial response of the bathroom floor
to mechanical events on it. Measured via piezo (PVDF + proof-mass cantilever)
at ≥ 1 kHz.
```

With:
```
P1 — Floor acceleration (m/s²) — inertial response of the bathroom floor
to mechanical events on it. Measured via piezo (PVDF + proof-mass cantilever)
at a sample rate ≥ 1 kHz. Compliance with this clause requires the active
firmware (USER/main.c) to run with INT_MARK=0 in deployment, which yields
the maximum UART-throughput-bound streaming rate (~1.9 kHz at 115200 baud
× 6-char "%.3f\n" output). Lower INT_MARK settings (1–4) violate Amendment
1 and are forbidden in deployment unless this amendment is revised. Every
recorded CSV from this project MUST include the INT_MARK value and an
empirically-measured sample-rate field; CSVs without this metadata are
not admissible as Article I evidence in any hearing.
```

---

## Expected Outcome (measurable in primitive P1 units)

- **Before**: Amendment 1 nominally requires ≥1 kHz but firmware can silently
  run at 50–500 Hz without violation detection. Every Stage-1 simulation
  built on assumed 1 kHz is implicitly conditional on an unverified rate.
- **After**: Amendment 1 compliance is binary and inspectable — INT_MARK=0
  in deployment + sample-rate field in every CSV. The
  SAMPLE-RATE-PARTIALLY-RESOLVED Stage 0 finding becomes resolvable.

Specific metric: 100 % of recorded CSVs after this amendment ratification
have an INT_MARK + measured-rate metadata field; 0 % do today.

---

## Amendment it complements/constrains

- **Amendment 1 (Domain Primitives)**: this Bill REVISES Amendment 1's P1 clause
- **Amendment 3 (Toolchain Alignment)**: this Bill adds a binding tie between
  Amendment 1 and a specific toolchain config (INT_MARK firmware setting),
  which is a use of Amendment 3 — recording it as part of the active
  toolchain. The firmware-INT_MARK-must-be-0 rule should also be added to
  `docs/toolchain_config.md` Active Firmware Toolchain section as a
  hard configuration constraint.

---

## Physical / Process Justification

1. **Nyquist for fall signals.** Real fall floor acceleration concentrates
   5–40 Hz (soft-tissue contact) with secondary content up to ~200 Hz
   (multi-impact + plate modes). Nyquist for 200 Hz content requires
   ≥ 400 Hz sample rate; for safety margin against aliasing, ≥ 1 kHz is
   appropriate. INT_MARK=1 (500 Hz) is technically Nyquist-OK for the
   main fall band but risks aliasing on higher-frequency content; lower
   rates definitely alias.

2. **Sim-to-real fidelity.** The Stage 1 simulator's bathroom-plate FEA
   model excites plate modes up to ~600 Hz (first 25 modes). Capturing
   these modes requires ≥ 1.2 kHz Nyquist-compliant rate, which only
   INT_MARK=0 (1.9 kHz) reliably provides.

3. **Forensic admissibility.** The 100 % sim-to-real disagreement found
   on 2026-05-15 may have been partially caused by an undisclosed
   rate mismatch (CSV recorded at ~1.9 kHz, simulator running at 1 kHz).
   Without sample-rate metadata in every recording, no future
   sim-to-real test is reproducible.

4. **Cost-free enforcement.** Setting INT_MARK=0 is the firmware
   default; this Bill primarily mandates that the deployment NOT
   change it accidentally. The metadata requirement adds a few bytes
   per recording session — negligible cost.

---

## What Happens Without This Bill

- Amendment 1 remains technically violable: any future operator can
  press the EXTI key and silently reduce sample rate, then claim
  Amendment 1 compliance because the firmware is "in spec."
- Future sim-to-real tests will be unreproducible because the rate
  parameter of the real-data recordings is undocumented.
- The SAMPLE-RATE-PARTIALLY-RESOLVED Stage 0 finding remains stuck.
- Each future debate about "is this data admissible" will re-litigate
  whether the implicit rate assumption was correct.

---

## Position B (alternative, for debate)

An alternative reading: Amendment 1's "≥ 1 kHz" already implicitly
restricts to INT_MARK=0; making it explicit is redundant. Position B
would amend ONLY the metadata-logging requirement, leaving the
INT_MARK-binding rule implicit. Risk: silent rate violations remain
detectable only by post-hoc analysis.

---

## Specific Files Affected by Enactment

- `docs/governance/amendments.md` — Amendment 1 text revision
- `docs/toolchain_config.md` — add INT_MARK=0 as a configuration
  constraint under Active Firmware Toolchain, and a metadata
  requirement under the recording protocol
- `docs/device_context.md` — Test Results table column for INT_MARK
  + measured rate per recording

---

## Recommended Hearing Path

`/judicial hear "Amendment 1 sample-rate revision (Bill 001)" "revise per Bill" vs "Position B: metadata-only revision"`
