---
name: franka-fci-launch
description: "Before any FR3 motion script can run, the FCI must be activated on the realtime PC via ssh franka-pc + fr3-launch"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 923b8ca9-f1ab-4cb2-a5b8-034e144d327e
---

To control the Franka FR3 from the dev machine (where the
`sim2real_adlros` pixi env runs the cloth-grasp scripts), the **FCI
must first be activated on the realtime PC**.

Procedure (verified by user 2026-06-04):

1. **SSH to the realtime PC:**
   ```
   ssh franka-pc
   ```
2. **Launch FCI on the realtime PC:**
   ```
   fr3-launch
   ```

Only after `fr3-launch` is running on `franka-pc` will any `arm_client`
client (Robot / Gripper) on the dev machine succeed in
`wait_until_ready`. Without it, every motion script (`ground_truth_finder.py`,
`run_trial.py`, `cloth_pick_place_AtoB.py`, `probe_surface.py`,
`monitor_gui.py`, …) hangs at startup.

### When to apply

At the START of every cloth-grasp session, before running any of:
- `experiments/cloth_grasp/experiment1/<variant>/ground_truth_finder.py`
  (variants: `parallel_jaw_stock`, `parallel_jaw_TPU`, `finray_33`, `finray_18`)
- `experiments/cloth_grasp/experiment1/<variant>/run_trial.py`
- `experiments/cloth_grasp/<family>/probe_surface.py` (families: `parallel_jaw`, `finray`)
- `experiments/cloth_grasp/<family>/cloth_pick_place_AtoB.py`
- any other arm_client-using script

If a script appears to hang at `wait_until_ready`, the most likely
cause is that FCI was never activated this session (or the connection
to `franka-pc` dropped). Re-SSH and re-launch.

See also: Bill 0006 (formal toolchain procedure record).
