Invoke the plotter agent to generate signal diagnostic plots or simulation evidence.

Usage: /plot <subcommand> [args]

Subcommands:
  profile <name> [mode]          — signal diagnostic plot for a single profile
  evidence signal <profile> [mode]   — signal diagnostic plot (evidence mode)
  evidence uart <log_path>           — UART session output from a Renode log file
  evidence sim <profile> [mode]      — full simulation evidence: UART + signal plot combined

Arguments:
  profile:  a profile name defined in the project's signal model
            (read from docs/device_context.md Signal Inventory or docs/toolchain_config.md)
  mode:     optional variant (e.g. nominal, worst-case, pathological — project-specific)
  log_path: path to UART log file (e.g. simulator/logs/renode_<profile>.log)

Examples:
  /plot profile nominal
  /plot profile worst-case pathological
  /plot evidence signal nominal
  /plot evidence signal worst-case pathological
  /plot evidence uart simulator/logs/renode_nominal.log
  /plot evidence sim nominal

Constitutional grounding:
  Signal Plot Amendment (check docs/governance/amendments.md for current number):
    signal plots mandatory after any signal model or algorithm parameter change
  Bureaucracy Signal Plotting Standing Order: no Bill or hearing required

The plotter agent does NOT:
- Modify source code or algorithm parameters
- Interpret whether the signal is correct (that is the Justice's role)
- Run simulations or build firmware
- Propose fixes based on what it observes

If no subcommand given, print this usage and stop.

Now parse "$ARGUMENTS":
  First word is the subcommand: "profile" or "evidence"
  For "profile": second word is the profile name, third (if present) is the mode
  For "evidence": second word is the type (signal/uart/sim), remaining words are the target

Before invoking the plotter:
  Read docs/device_context.md Signal Inventory to confirm the requested profile name exists.
  If it does not, stop and print:
    "Profile '<name>' not found in Signal Inventory. Valid profiles are: [list from device_context.md]
     Add it via /spec signals if this is a new operating condition."

For "profile" subcommand, the plotter agent must:
1. Read docs/toolchain_config.md to locate the firmware repo and signal model path
2. Read docs/device_context.md Signal Inventory to confirm the profile name is valid
3. Call the project's signal model to generate the signal sequence for the named profile
4. Apply the filter chain defined in the project's algorithm source
5. Save plot to docs/plots/<profile>_signal_check.png
6. Print data table to stdout (peak values, key timestamps, threshold crossings)
7. Plot using crucible.signal.plot — do NOT write inline plot code
