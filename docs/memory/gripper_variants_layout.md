---
name: gripper-variants-layout
description: "Four gripper variants and the cloth-grasp folder layout (library code at family root, experiment1 per variant with config_<variant>.py)"
metadata: 
  node_type: memory
  type: project
  originSessionId: 923b8ca9-f1ab-4cb2-a5b8-034e144d327e
---

The cloth-grasp benchmark has **four gripper variants**, paired into two
**families** (which share library code):

| Variant (folder name)   | Family        | Notes |
|-------------------------|---------------|---|
| `parallel_jaw_stock`    | `parallel_jaw`| Rigid baseline |
| `parallel_jaw_TPU`      | `parallel_jaw`| + TPU 90A pad on the jaws |
| `finray_33`             | `finray`      | 33 mm finray blades, flat-seat fixture (Study 3 0° reference) |
| `finray_18`             | `finray`      | 18 mm finray blades |
| `finray_33_5deg`        | `finray`      | 33 mm finray blades + 5° inclined-seat fixture (Study 3) |

(Mapping is hard-coded in `_VARIANT_TO_FAMILY` at the top of every
experiment1 script.)

### Folder layout (`experiments/cloth_grasp/` in sim2real_adlros)

```
cloth_grasp/
  parallel_jaw/                   # FAMILY library — shared by both pj variants
    cloth_pick_place_AtoB.py
    config.py                     # family default (used by standalone calls)
    monitor_gui.py
    probe_surface.py
    status_bus.py
  finray/                         # FAMILY library — shared by both finray variants
    (same files)
  pilot/                          # pilot test data (2026-05-22) — data only
    parallel_jaw/results/
    finray/results/
    plots/
  experiment1/                    # Study 1 (and follow-ons) per variant
    parallel_jaw_stock/
      config_parallel_jaw_stock.py # variant-specific config
      ground_truth_finder.py       # per-variant entry point
      run_trial.py
      depth_<±X.X>mm_<ts>/         # generated data
        ground_truth_used.json
        depth_summary.json
        trial_NNN/{pose_wrench.csv, run_config.json, config.yaml}
    parallel_jaw_TPU/
      config_parallel_jaw_TPU.py
      …
    finray_33/
      config_finray_33.py
      …
    finray_18/
      config_finray_18.py
      …
```

### Why each variant has its own `config_<variant>.py`

Same physical robot config (positions, orientations, speeds, grasp
settings) needs to differ subtly across variants (e.g. tip offset for
`finray_18` vs `finray_33`, gripper-mode for TPU vs stock jaws). A
single shared `config.py` is dangerous — too easy to misuse the wrong
variant's values. The per-variant file makes the active config visible
in the import line.

### How the scripts import the right config

Each experiment1 script:
1. Reads its directory name → `GRIPPER_VARIANT`.
2. Resolves family via `_VARIANT_TO_FAMILY`.
3. Loads `config_<variant>.py` from its own folder via `importlib.util`.
4. Injects it as `sys.modules["config"] = <module>` BEFORE importing
   the family library helpers (`cloth_pick_place_AtoB.py`,
   `probe_surface.py`) — so the helpers' `import config` resolves to
   the variant's module, not the family default.

### How to apply

When asked about gripper variants or where to put new experimental
code:
- Library / state machine / motion helpers → `cloth_grasp/<family>/`
- Per-variant orchestration (depth sweep, tilt sweep, etc.) →
  `cloth_grasp/experiment1/<variant>/`
- Pilot data (already captured) → leave under `pilot/`
- New experiments (experiment2, etc.) → follow the experiment1 pattern
- Configs are ALWAYS per-variant (`config_<variant>.py`); the family
  `config.py` is the seed, not the authoritative source for experiments.

See also [[experiment-matrix-locked]], [[gripper-frame-convention]],
[[per-gripper-tcp-via-touchoff]].
