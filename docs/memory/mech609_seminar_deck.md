---
name: mech609-seminar-deck
description: "MECH 609 seminar (Aug 12 2026) — deck location, artifact URL, style constraints, and grading-driven structure"
metadata: 
  node_type: memory
  type: project
  originSessionId: 923b8ca9-f1ab-4cb2-a5b8-034e144d327e
  modified: 2026-08-06T05:13:19.105Z
---

MECH 609 Masters Seminar: **August 12, 2026, 16h30, ENGMD-267**. 15–17 min talk + 5 min Q&A, graded on presentation quality only (not research quality).

Deck lives at `docs/seminar/MECH609_seminar.html` (self-contained HTML, keyboard nav, press P → print to PDF). Rebuilt from `deck_template.html` + a Python base64-inline step (template in session scratchpad — regenerate images if scratchpad is cleaned). Artifact URL (same URL across republshes): https://claude.ai/code/artifact/9b886ab4-3624-42f1-b155-f83d8eda5769

**Why:** repeated deck-revision requests each encoded a durable preference.

**How to apply:** any future edits to the seminar deck must respect:
- LaTeX look: Latin Modern fonts embedded from `/usr/share/texmf/fonts/opentype/public/lm/` as data-URI @font-face; McGill Red #ED1B2F rules; formal academic register (user rejected a "designed" version as unprofessional)
- Title slide: date only — NO time, NO room, NO email anywhere
- ALL thanks/credits (ADL-ros2 controller, MACRObotics, supervisor) go ONLY on the final acknowledgements slide; slide-9 tools box stays neutral/factual
- Low word density: fragments on slides, spoken sentences carry detail; sparse slides filled with card grids / big-numeral rows, not more text
- Structure per MECH 609 evaluation criteria: ~50% background / 40% results / 10% conclusions; general mech-eng audience (no unexplained acronyms); explicit tools acknowledgement is a graded item
- MACRObotics logo on title + final slide is a RECREATION (URW Gothic Demi + drawn purple blobs) — swap for the official file when user provides it
