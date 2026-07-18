---
name: move-to-noop-in-fr3-pose
description: "Under fr3_pose_controller, BOTH Robot.move_to() AND Robot.set_target() are observed to be no-ops — execute_cartesian_traj is the only motion primitive that actually drives the robot"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 923b8ca9-f1ab-4cb2-a5b8-034e144d327e
---

Under `fr3_pose_controller`, both `Robot.move_to(pose, speed)` AND
`Robot.set_target(pose=...)` from the `arm_client` API are observed
to be no-ops — they print debug lines like
`[debug] Moving to target pose Pos: [...] with time_to_move: 2 sec`
but the robot does not move.

Symptom observed 2026-06-04: a 10 cm pre-lift in
`ground_truth_finder.py` issued first via `move_to` and then via
`set_target` printed the debug lines, but the EE z stayed at the
original 40 mm in both cases. Same in
`probe_surface.touchoff_once` per-tap retract and the per-step
descent loop.

**The proven motion primitive under `fr3_pose_controller`** is
`execute_cartesian_traj` + `wait_for_trajectory_completion` — the
exact pattern `cloth_pick_place_AtoB._smooth_through` uses
successfully across every prior session.

```python
from arm_client.robot import Pose, Twist
waypoints = [
    (Pose(start_xyz, orient), Twist(np.zeros(3), np.zeros(3))),
    (Pose(end_xyz,   orient), Twist(np.zeros(3), np.zeros(3))),
]
times = [0.0, max(distance / speed_m_per_s, 1.0)]
robot.execute_cartesian_traj(waypoints, times)
while robot.wait_for_trajectory_completion(times[-1], timeout_margin=1.5):
    time.sleep(0.05)
time.sleep(0.3)  # final settle
```

### Force-watching descent under fr3_pose_controller

Pattern: send the full descent as ONE long trajectory, poll F_ext
during execution, preempt on contact by issuing a "hold at current
pose" trajectory (two identical waypoints at the current z, ~0.5 s
duration) — the new trajectory replaces the in-flight descent and
stops the robot at the detected z. Capture the achieved z BEFORE
issuing the stop trajectory so the recorded value reflects the
exact moment the threshold was crossed.

See `experiments/cloth_grasp/{parallel_jaw,finray}/probe_surface.py::touchoff_once`
for the full implementation.

### How to apply

Whenever you write code that needs to drive the FR3 under
`fr3_pose_controller`:
- **Do NOT** use `robot.move_to(...)` — silently no-ops.
- **Do NOT** use `robot.set_target(...)` — also silently no-ops in
  the cloth-grasp setup.
- Use `robot.execute_cartesian_traj(...) +
  wait_for_trajectory_completion(...)` for every motion (single
  move, multi-waypoint trajectory, or even a "stop" command that's
  two waypoints at the same pose).

If you see "time_to_move: ..." in the debug output but the robot
isn't actually moving, this is the diagnosis.
