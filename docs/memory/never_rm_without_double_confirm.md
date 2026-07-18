---
name: never-rm-without-double-confirm
description: "When user says 'remove' or 'delete' multiple cells/trials in a batch, ALWAYS confirm hard-delete vs stage before running rm -rf. Even if a precedent exists for hard-delete on a SINGLE explicitly-named cell, do not extrapolate to bulk deletes. The experiments/cloth_grasp/ tree is NOT git-tracked, no trash, no recovery."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 923b8ca9-f1ab-4cb2-a5b8-034e144d327e
---

**Rule:** For any bulk delete operation across multiple cells/trials, ASK the
user "hard-delete with rm -rf (irreversible) or stage with underscore prefix?"
before executing. Even if the user has previously authorized hard-delete on
one specific named cell, don't extrapolate that to a batch operation.

**Why:** `experiments/cloth_grasp/` is untracked by git, files removed with
`shutil.rmtree()` or `rm -rf` are NOT recoverable — they don't go to the trash.
There is no undo. The user lost 13 staged failed cells + 6 outlier trial dirs
on 2026-06-28 because I interpreted "remove all failed attempts" as hard-delete
based on a single prior precedent ("remove!!! not stage").

**How to apply:**
- Single named cell explicitly tagged with "remove" or "delete" + emphasis
  ("!!!"): hard-delete is OK per user precedent
- Batch of more than one cell: ALWAYS ask "stage or delete?" even if user
  said "remove" — the word ambiguity matters too much for irreversible action
- When in doubt, default to staging (underscore prefix). Easier to delete later
  than to undelete.
- Before any rm -rf, print the full list of paths to delete and require explicit
  user confirmation if more than one item.

Linked: [[no-hide-without-explicit-ask]] — both about being conservative with
filesystem mutations even when the user gives an imperative.
