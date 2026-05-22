#!/usr/bin/env python3
"""
Cloth edge pick-and-place: grasp at A, lift, move to B, release.

Implements the project's "drag/move A->B (flat cloth edge grasp)" functional
task (docs/device_context.md) on the FR3 via the sim2real_adlros arm_client.

Grasp follows the 6Q multi-stage descent strategy:
  approach (clearance)  ->  fine +5 mm  ->  contact 0  ->  press -3 mm
  -> close gripper -> lift -> traverse to B at height -> lower -> open -> retreat

Contact force is logged from the Franka built-in F_ext estimate
(end_effector_wrench) — the first-pass Contact Force source while the A301
arrays are blocked. F_ext is an Amendment-1-sanctioned source (flange wrench,
base frame); it is a model-based estimate at the flange, not a per-contact
measurement.

All tunable values (positions A/B, fixed orientation, descent geometry, speeds,
grasp force, log rate) live in scripts/thesis/config.py. CLI flags override.

=== HOW TO RUN (inside the sim2real_adlros pixi env) ===
  cd ~/Documents/sim2real_adlros
  # 1. Teach: jog the robot to A and B, capture XYZ (orientation is fixed by config):
  pixi run -e humble python ~/crucible/cloth-grasp/scripts/thesis/cloth_pick_place_AtoB.py --teach
  #    -> paste the printed POSITION_A / POSITION_B lines into config.py
  # 2. Execute the pick-and-place:
  pixi run -e humble python ~/crucible/cloth-grasp/scripts/thesis/cloth_pick_place_AtoB.py --wrench-log run1.csv

ARTICLE II: this MOVES THE REAL ROBOT. A human must be present with the e-stop.
The script confirms before every motion stage unless --yes is given.
"""
from __future__ import annotations

import argparse
import csv
import sys
import threading
import time
from pathlib import Path

import numpy as np

from arm_client.robot import Pose, Robot
from arm_client.gripper.franka_hand import Gripper

# config.py + status_bus.py live next to this script.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402
import status_bus  # noqa: E402


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def banner(msg: str) -> None:
    print("\n" + "=" * 64 + f"\n{msg}\n" + "=" * 64)


def confirm(step: str, auto_yes: bool) -> None:
    """Pause for operator confirmation before a motion stage."""
    if auto_yes:
        print(f"  -> {step}")
        return
    ans = input(f"  -> {step}  [Enter = go / q = abort]: ").strip().lower()
    if ans == "q":
        raise KeyboardInterrupt


def flatten_wrench(w: dict) -> dict:
    """Flatten end_effector_wrench dict (force/torque arrays or scalars) for CSV."""
    out: dict[str, float] = {}
    for key, val in w.items():
        arr = np.atleast_1d(np.asarray(val, dtype=float)).ravel()
        if arr.size == 3:
            for axis, comp in zip("xyz", arr):
                out[f"{key}_{axis}"] = float(comp)
        elif arr.size == 1:
            out[key] = float(arr[0])
        else:
            for i, comp in enumerate(arr):
                out[f"{key}_{i}"] = float(comp)
    return out


def fz_estimate(robot: Robot) -> float:
    """Best-effort vertical contact-force estimate (N) from F_ext."""
    w = flatten_wrench(robot.end_effector_wrench)
    for k in ("force_z", "fz", "force_2"):
        if k in w:
            return w[k]
    return float("nan")


class WrenchLogger:
    """Background sampler: logs flattened F_ext + EE z to CSV at a fixed rate."""

    def __init__(self, robot: Robot, path: Path, hz: float, gripper: "Gripper | None" = None):
        self.robot = robot
        self.gripper = gripper
        self.path = path
        self.period = 1.0 / hz
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._stage = "init"
        # Active controller captured once (service call); cheap per-row reads
        # use is_ready. NOTE: a true franka "quit due to error" flag is not
        # surfaced by arm_client — it would require the robot_state broadcaster
        # (robot_mode / last_motion_errors). is_ready + active_controller are
        # health proxies only.
        try:
            self.active_controller = robot.controller_switcher_client.get_active_controller()
        except Exception:
            self.active_controller = "unknown"

    def stage(self, name: str) -> None:
        self._stage = name

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=2.0)

    def _run(self) -> None:
        with open(self.path, "w", newline="") as f:
            writer = None
            t0 = time.monotonic()
            while not self._stop.is_set():
                try:
                    row = {"t_s": time.monotonic() - t0, "stage": self._stage}
                    # End-effector pose: full position + orientation (achieved).
                    pose = self.robot.end_effector_pose
                    row["px_m"], row["py_m"], row["pz_m"] = (float(v) for v in pose.position)
                    qx, qy, qz, qw = pose.orientation.as_quat()
                    row["qx"], row["qy"], row["qz"], row["qw"] = (
                        float(qx), float(qy), float(qz), float(qw),
                    )
                    # Commanded (target) pose, if a target is set.
                    try:
                        cmd = self.robot.target_pose
                        row["cmd_px_m"], row["cmd_py_m"], row["cmd_pz_m"] = (
                            float(v) for v in cmd.position
                        )
                        cqx, cqy, cqz, cqw = cmd.orientation.as_quat()
                        row["cmd_qx"], row["cmd_qy"], row["cmd_qz"], row["cmd_qw"] = (
                            float(cqx), float(cqy), float(cqz), float(cqw),
                        )
                    except Exception:
                        for k in ("cmd_px_m", "cmd_py_m", "cmd_pz_m",
                                  "cmd_qx", "cmd_qy", "cmd_qz", "cmd_qw"):
                            row[k] = float("nan")
                    # F_ext at the flange (Contact Force estimate), base frame.
                    row.update(flatten_wrench(self.robot.end_effector_wrench))
                    # Gripper opening width, if available.
                    if self.gripper is not None:
                        gw = self.gripper.value
                        row["gripper_width_m"] = float(gw) if gw is not None else float("nan")
                    # Controller-health proxies (see __init__ note).
                    try:
                        row["is_ready"] = bool(self.robot.is_ready())
                    except Exception:
                        row["is_ready"] = False
                    row["active_controller"] = self.active_controller
                    if writer is None:
                        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
                        writer.writeheader()
                    writer.writerow(row)
                    f.flush()
                except Exception:
                    pass
                time.sleep(self.period)


# --------------------------------------------------------------------------
# Teach / load A and B
# --------------------------------------------------------------------------
def teach_poses(robot: Robot) -> None:
    """Capture XYZ for A and B; print config.py-ready lines + achieved RPY.

    Orientation is fixed by config.EEF_RPY_DEG, so teach only needs position.
    The achieved orientation is printed as RPY so you can verify/choose the
    fixed orientation value.
    """
    banner("TEACH MODE — capture positions A and B")
    print("Jog/hand-guide the gripper to the GRASP point (touching the cloth edge")
    print("on the table) for each position, then press Enter. Paste the printed")
    print("POSITION_A / POSITION_B lines into config.py.\n")
    captured = {}
    for label in ("A", "B"):
        input(f"  Move robot to position {label}, then press Enter to capture...")
        p = robot.end_effector_pose
        captured[label] = tuple(round(float(x), 4) for x in p.position)
        rpy = p.orientation.as_euler("xyz", degrees=True)
        print(f"    {label}: position={captured[label]}  achieved_RPY_deg="
              f"{np.round(rpy, 1).tolist()}")
    print("\n--- paste into scripts/thesis/config.py ---")
    print(f"POSITION_A = {captured['A']}")
    print(f"POSITION_B = {captured['B']}")
    print("(EEF_RPY_DEG is fixed in config; compare it to the achieved_RPY above.)")


def at_height(xy_source: np.ndarray, z_abs: float, orient) -> Pose:
    """Pose at xy_source's x,y with absolute z and the fixed orientation."""
    return Pose(
        position=np.array([xy_source[0], xy_source[1], z_abs]),
        orientation=orient,
    )


# --------------------------------------------------------------------------
# Pick and place
# --------------------------------------------------------------------------
def run_pick_place(robot: Robot, gripper: Gripper, A_xy: np.ndarray, B_xy: np.ndarray, args, logger) -> None:
    orient = config.eef_orientation()  # fixed orientation for the whole task
    surf_a, surf_b = A_xy[2], B_xy[2]  # table-surface z at A and B

    z_approach_A = surf_a + args.approach_dz
    z_fine_A = surf_a + args.fine_dz
    z_surface_A = surf_a
    z_press_A = surf_a - args.depth        # press BELOW the surface by `depth`
    z_lift = surf_a + args.lift_dz
    z_place_B = surf_b
    z_retreat_B = surf_b + args.approach_dz

    def set_stage(label):
        if logger:
            logger.stage(label)
        status_bus.publish(label)

    def go(label, target_pose, speed):
        set_stage(label)
        confirm(f"{label}: -> {np.round(target_pose.position, 4).tolist()} @ {speed} m/s", args.yes)
        robot.move_to(pose=target_pose, speed=speed)
        print(f"     Fz(F_ext) ~= {fz_estimate(robot):+.2f} N")

    banner("PICK @ A")
    confirm("open gripper", args.yes)
    gripper.open()

    go("approach_A", at_height(A_xy, z_approach_A, orient), args.travel_speed)
    go("fine_A", at_height(A_xy, z_fine_A, orient), args.descent_speed)
    go("surface_A", at_height(A_xy, z_surface_A, orient), args.descent_speed)
    go(f"press_A(depth={args.depth*1000:.0f}mm)", at_height(A_xy, z_press_A, orient), args.press_speed)

    set_stage("grasp")
    confirm(f"close gripper (grasp cloth, force={args.grasp_force} N)", args.yes)
    grasped = gripper.close(force=args.grasp_force, speed=args.grasp_speed)
    print(f"     grasp action returned: {grasped}  (visually verify the cloth is pinched)")
    print(f"     Fz(F_ext) ~= {fz_estimate(robot):+.2f} N")

    banner("LIFT + TRAVERSE -> PLACE @ B")
    go("lift_A", at_height(A_xy, z_lift, orient), args.descent_speed)
    go("traverse_B", at_height(B_xy, z_lift, orient), args.travel_speed)
    go("lower_B", at_height(B_xy, z_place_B, orient), args.descent_speed)

    set_stage("release")
    confirm("open gripper (release cloth)", args.yes)
    gripper.open()

    go("retreat_B", at_height(B_xy, z_retreat_B, orient), args.descent_speed)
    set_stage("done")
    banner("DONE")


def main() -> int:
    ap = argparse.ArgumentParser(description="Cloth edge pick-and-place A -> B (FR3)")
    ap.add_argument("--namespace", default=config.NAMESPACE)
    ap.add_argument("--teach", action="store_true", help="capture A and B XYZ, print config lines, exit")
    ap.add_argument("--grasp-force", type=float, default=config.GRASP_FORCE_N, help="grasp force (N)")
    ap.add_argument("--grasp-speed", type=float, default=config.GRASP_SPEED)
    # geometry (m), relative to the table surface z of each position
    ap.add_argument("--approach-dz", type=float, default=config.APPROACH_DZ, help="clearance above surface")
    ap.add_argument("--fine-dz", type=float, default=config.FINE_DZ, help="6Q +5 mm fine-approach above surface")
    ap.add_argument("--depth", type=float, default=config.GRASP_DEPTH,
                    help="press depth BELOW table surface (m, positive); builds grasp force. 0 for parallel jaw")
    ap.add_argument("--lift-dz", type=float, default=config.LIFT_DZ, help="lift height above surface")
    # speeds (m/s)
    ap.add_argument("--travel-speed", type=float, default=config.TRAVEL_SPEED)
    ap.add_argument("--descent-speed", type=float, default=config.DESCENT_SPEED)
    ap.add_argument("--press-speed", type=float, default=config.PRESS_SPEED, help="very slow into the press")
    # F_ext logging
    ap.add_argument("--wrench-log", type=Path, default=None, help="CSV path for continuous pose+F_ext log")
    ap.add_argument("--wrench-hz", type=float, default=config.WRENCH_HZ)
    ap.add_argument("--yes", action="store_true", help="skip per-stage confirmations (UNSAFE)")
    args = ap.parse_args()

    robot = Robot(namespace=args.namespace)
    robot.wait_until_ready(timeout=10.0)

    if args.teach:
        teach_poses(robot)
        robot.shutdown()
        return 0

    A_xy, B_xy = config.position_a(), config.position_b()

    banner("SAFETY — clear the workspace; keep the e-stop in hand")
    print(f"  A surface: {np.round(A_xy, 4).tolist()}  | press depth below surface: {args.depth*1000:.0f} mm")
    print(f"  B surface: {np.round(B_xy, 4).tolist()}")
    print(f"  EEF orientation (fixed): RPY{config.EEF_RPY_DEG} deg")
    print(f"  grasp force {args.grasp_force} N | F_ext as Contact Force estimate")
    if not args.yes:
        if input("\nType GO to arm and begin: ").strip() != "GO":
            print("Aborted.")
            robot.shutdown()
            return 130

    # Precision path: joint trajectory controller (IK-routed move_to).
    robot.controller_switcher_client.switch_controller("joint_trajectory_controller")

    gripper = Gripper(namespace=args.namespace)
    gripper.wait_until_ready(timeout=10.0)

    logger = None
    if args.wrench_log:
        logger = WrenchLogger(robot, args.wrench_log, args.wrench_hz, gripper=gripper)
        logger.start()
        print(f"Logging pose + F_ext + gripper to {args.wrench_log} at {args.wrench_hz} Hz")

    rc = 0
    try:
        run_pick_place(robot, gripper, A_xy, B_xy, args, logger)
    except KeyboardInterrupt:
        print("\nAborted by operator — robot stops at current pose.")
        rc = 130
    finally:
        if logger:
            logger.stop()
        gripper.shutdown()
        robot.shutdown()
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
