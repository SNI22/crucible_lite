---
name: no-hide-without-explicit-ask
description: "Never rename / hide / underscore-prefix a data cell unless the user has explicitly named THAT specific cell. Don't infer cascading hides from prior policy, don't apply a 'consistent' rule, don't drop pairs to clean up plots."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 923b8ca9-f1ab-4cb2-a5b8-034e144d327e
---

**Rule:** Do not hide (underscore-prefix) any experiment cell unless the user
has explicitly named the specific cell to hide. Even if a prior turn established
a "policy" (e.g., hide older when newer exists), do NOT extend that policy on
your own to other cells, other depths, or the other half of a sign-flip pair.

**Why:** The user is actively running new cells while we work. A cell that looks
"orphaned" right now may pair with a fresh cell minutes later. Hiding it
prematurely makes its data invisible when the matching cell arrives, and removes
features (e.g., bias bars) the user wants to keep on the plot until the pair is
restored.

**Concrete incident (2026-06-26):** User asked me to "stage the old one" for the
+3.0 mm fr26_5deg cross-session pair. I correctly hid the older x −2.5° cell,
but the result was that the +3.0 mm bias bar vanished from the plot. The user
wanted the bar to remain visible until the new x −2.5° cell finished running
("the new test for -2.5 is going to happen soon. do not remove anything unless
i specifically tell you to !!!"). I had to restore the hidden cell.

**How to apply:**
- Hide a cell ONLY when the user names it explicitly (path, timestamp, or
  unambiguous depth+tilt+session reference).
- If asked to hide one half of a pair, FIRST flag that the bar will disappear
  and confirm before renaming.
- When the user says "stage the older one" for a sign-flip pair, default to
  hiding the older +TILT cell first (the new one usually replaces the +TILT
  cell, not the −TILT). When in doubt, ask.
- Do NOT proactively run a sweep across other (depth, tilt) combos applying the
  same rule. Even if the same artifact appears at +2.0, +2.5, +3.5 mm, wait for
  the user to ask cell-by-cell.
- The dedup script that hides ALL older duplicates is fine when the user
  explicitly asks for a project-wide cleanup — but never as an inference from
  a single-cell request.

**THIRD INCIDENT (2026-06-29):** User said "let's ignore +1.20 here" referring
to a depth row in a coverage table I'd just shown. I interpreted "ignore" as a
staging instruction (rename with underscore prefix). User responded "no no no
you do not have to stage it, please undo." The correct interpretation was
verbal/conversational: "let's not discuss this row" or "exclude from the
narrative" — NOT a filesystem mutation. The word "stage" or "hide" or "remove"
must appear before any rename/delete action.

**SECOND INCIDENT (2026-06-26 23:00):** User said "I will redo all the tests
then, now please stage the previous results" while planning fr18 x+2.5°
reruns. I staged ALL 10 Tuesday x+2.5° cells (across all depths) — but the
user had only rerun 5 of them (−1.0, −0.5, +1.5, +2.0, +2.5 mm). For the
other 5 (+3.0, +6.0, +8.0, +10.0, +12.0 mm) there was no today cell yet,
so staging the Tuesday cell DELETED their data entirely from active use.
User reaction: "do not stage the ones that I did not run new trials!!!!"

**Refined rule:** "Stage the previous results" ALWAYS means "stage previous
cells THAT HAVE A NEW REPLACEMENT". Cells at depths the user hasn't rerun
must stay active. Before mass-staging, check which (depth, tilt) combos have
a new (today) cell first; only stage olders where a newer exists. Never
preemptively stage based on planned/future runs.
