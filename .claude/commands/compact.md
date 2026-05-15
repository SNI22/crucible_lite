Compact spiralling documentation into tight operational references without losing constitutional binding.

Usage: /compact [target]

Targets:
  stage <N>       — close Stage N and freeze its case law (requires human confirmation that gate is met)
  case-law        — triage live case_law.md: summarise sprawl, flag candidates for stage-compactor
  amendments      — triage amendments.md: identify redundant, superseded, or over-specified amendments
  docs            — scan all docs/ for files that have grown beyond their purpose; recommend pruning
  all             — run all four in sequence

If no target given, run docs triage first and print a compaction menu.

---

## When to use this command

Documentation spirals when:
- case_law.md accumulates argument threads that were resolved but never frozen
- amendments.md has grown amendments that now contradict each other or overlap
- docs/ contains drafts, superseded handoff notes, or stale plot evidence
- A stage gate was confirmed verbally but never formally closed
- The same decision appears in three places with slightly different wording

The Justice calls /compact when re-reading the constitutional record before a hearing
takes longer than it should, or when an agent cites a stale precedent that was de facto
resolved but not recorded as frozen.

Compaction is not deletion. It is distillation. The full record is preserved in
`docs/governance/case_law.md`; the closeout document is what agents read daily.

---

## Stage compaction  (`/compact stage <N>`)

Precondition: the human engineer must explicitly confirm the stage gate is met
before this runs. Do not infer confirmation from context.

Print:
```
STAGE <N> COMPACTION
Precondition: Justice must confirm Stage <N> gate is met before I proceed.
Is Stage <N> complete? (yes / no)
```

If confirmed, invoke the **stage-compactor** agent with: "Stage <N> is closed."
It will:
1. Read `docs/governance/case_law.md` — identify entries tagged to Stage N
2. Read `docs/governance/handoff.md` — confirm exit criteria
3. Produce Settled Precedent Cards for each ruling
4. Write to `docs/governance/stage_<N>_closeout.md`
5. Mark compacted entries as `[FROZEN — Stage N closed YYYY-MM-DD]`
6. Commit both files

Print a summary after the agent completes:
```
──────────────────────────────────────
STAGE <N> COMPACTION COMPLETE
Precedents frozen   : N
Closeout written    : docs/governance/stage_<N>_closeout.md
Case law updated    : docs/governance/case_law.md
──────────────────────────────────────
```

---

## Case law triage  (`/compact case-law`)

Read `docs/governance/case_law.md` in full. For each entry, classify it:

| Status | Meaning |
|--------|---------|
| `FROZEN` | Already compacted — skip |
| `LIVE — ready to freeze` | Ruling was issued, implementation complete, no open questions |
| `LIVE — active` | Hearing is recent or implementation is ongoing — do not freeze |
| `ORPHANED` | No stage tag, no implementation reference — flag for human review |
| `DUPLICATE` | Substantially the same ruling appears under another case — flag for merge |

Print a triage table:
```
──────────────────────────────────────────────────────
CASE LAW TRIAGE  (docs/governance/case_law.md)
──────────────────────────────────────────────────────
Case                   Stage   Status
<Case Name>            N       LIVE — ready to freeze
<Case Name>            N       FROZEN
<Case Name>            ?       ORPHANED — no stage tag
──────────────────────────────────────────────────────
Recommended: run /compact stage <N> to freeze LIVE-ready entries.
──────────────────────────────────────────────────────
```

Do not freeze anything automatically. Print the recommendation and stop.
The Justice decides which stage to close.

---

## Amendment triage  (`/compact amendments`)

Read `docs/governance/amendments.md` in full. Flag:

- **Superseded** — a later amendment makes this one redundant (cite both by number)
- **Conflicting** — two amendments mandate incompatible actions (requires a Judicial Hearing, not compaction)
- **Over-specified** — an amendment references a specific file path, function name, or magic number that has since changed
- **Healthy** — in force, unambiguous, and consistent with current source

Print a triage table. Do not modify amendments.md. If conflicts are found, print:
```
CONFLICT DETECTED: Amendment N vs Amendment M
This requires a Judicial Hearing — use /hear to resolve before compacting.
```

---

## Docs triage  (`/compact docs`)

Scan `docs/` recursively. For each file, report:

- **Size** (lines)
- **Last-modified hint** — infer from git log if available
- **Purpose** — one-line summary of what the file is supposed to be
- **Spiral risk** — HIGH / MEDIUM / LOW based on size, staleness, and whether its content is referenced anywhere

Print a triage table:
```
──────────────────────────────────────────────────────────────────
DOCS TRIAGE
──────────────────────────────────────────────────────────────────
File                                    Lines   Spiral Risk   Note
docs/governance/case_law.md             412     HIGH          14 live entries, 3 orphaned
docs/governance/amendments.md           180     MEDIUM        2 over-specified paths
docs/plots/si_comparison.png            —       LOW           evidence file, fine
docs/governance/handoff.md              38      LOW           current, in use
──────────────────────────────────────────────────────────────────
Recommendation: /compact case-law to triage the 3 orphaned entries.
──────────────────────────────────────────────────────────────────
```

Do not delete or modify any files. Print the triage and stop.

---

## Conduct Rules

1. Never compact without explicit human confirmation of stage gate completion.
2. Never delete case law entries — only freeze (mark immutable) or flag.
3. Never modify amendments.md — only report findings.
4. Never merge duplicate cases unilaterally — flag for human decision.
5. If `docs/governance/handoff.md` is missing or incomplete when stage compaction
   is requested, print a hard stop:
   ```
   STOP: docs/governance/handoff.md is missing or incomplete.
   Stage compaction requires a confirmed exit criteria record.
   Create or complete handoff.md before closing this stage.
   ```
6. If stage-compactor encounters a conflict between a case law entry and the
   confirmed exit criteria, escalate to human — do not proceed.
