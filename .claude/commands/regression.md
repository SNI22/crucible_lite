Invoke the regression-runner agent to run the full simulation profile matrix against stage-gate criteria.

Usage: /regression [profile]

Arguments:
  profile  — run a single named profile only (optional)
  (none)   — run all profiles registered in docs/device_context.md Signal Inventory

What regression-runner does:
  1. Reads profile list from docs/device_context.md Operating Envelope
  2. Reads pass/fail threshold from Device Purpose section
  3. Dispatches simulator-operator for each profile
  4. Compares results against threshold
  5. Prints a pass/fail matrix and stage-gate verdict

Output:
  Per-profile: primary metric vs threshold, PASS/FAIL/ERROR
  Summary: N pass, N fail, N error
  Stage gate verdict: MET / BLOCKED / PIPELINE-ERROR

Constitutional grounding:
  Amendment 5 — simulation is the hardware proxy; regression validates every profile
  Amendment 6 — signal plots are dispatched per profile when requested

Run:
  After any firmware or algorithm change (before stage gate)
  Before any /session stage advance
  After any /hear ruling that changes algorithm or firmware

Three-strike rule (Amendment 4):
  If simulator-operator fails 3 consecutive times on the same profile, regression-runner
  stops and escalates — does not continue to other profiles.

Now invoke the regression-runner agent.
If a profile name is given in "$ARGUMENTS", run that profile only.
If no argument, run the full matrix.
If no profiles are registered in device_context.md, print:
  "No profiles registered. Run /spec collect to populate the Signal Inventory
   with operating conditions before running regression."
