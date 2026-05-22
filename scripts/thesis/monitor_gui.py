#!/usr/bin/env python3
"""
Live monitor GUI for the FR3 cloth pick-and-place.

Read-only dashboard — it NEVER commands motion. Run it alongside
cloth_pick_place_AtoB.py to watch the run live:

  - 2D top-down map (base-frame x-y) with positions A and B, the actual EEF
    (dot + trail) and the commanded EEF (ghost marker).
  - A vertical z gauge (the descent axis) marking the table surface and the
    press depth.
  - A readout panel: actual and commanded pose (xyz + RPY), F_ext force, and
    gripper width.
  - A status bar: current stage (from status_bus), grasper state, |F_ext|,
    and a freshness indicator.

=== HOW TO RUN (in the sim2real_adlros pixi env, with a display) ===
  cd ~/Documents/sim2real_adlros
  pixi run -e humble python ~/crucible/cloth-grasp/scripts/thesis/monitor_gui.py
  # then, in another terminal, run the controller as usual.
"""
from __future__ import annotations

import sys
import time
from collections import deque
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

from arm_client.robot import Robot
from arm_client.gripper.franka_hand import Gripper

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402
import status_bus  # noqa: E402


def _safe(getter, default=None):
    """Read a Robot/Gripper property that may raise before data arrives."""
    try:
        return getter()
    except Exception:
        return default


def _rpy_deg(pose) -> np.ndarray:
    return pose.orientation.as_euler("xyz", degrees=True)


class Dashboard:
    def __init__(self, robot: Robot, gripper: Gripper, trail: int = 250):
        self.robot = robot
        self.gripper = gripper
        self.tx: deque[float] = deque(maxlen=trail)
        self.ty: deque[float] = deque(maxlen=trail)

        a, b = config.position_a(), config.position_b()
        self.surf = float(a[2])
        self.depth = float(config.GRASP_DEPTH)
        self.lift = float(config.LIFT_DZ)

        self.fig = plt.figure(figsize=(12, 7))
        self.fig.canvas.manager.set_window_title("FR3 cloth pick-place monitor")
        gs = self.fig.add_gridspec(2, 3, width_ratios=[3, 0.5, 2], height_ratios=[6, 1])

        # --- 2D top-down map (x horizontal, y vertical) ---
        self.ax_map = self.fig.add_subplot(gs[0, 0])
        self.ax_map.set_title("Top-down map (base frame)")
        self.ax_map.set_xlabel("x [m]")
        self.ax_map.set_ylabel("y [m]")
        self.ax_map.set_aspect("equal", adjustable="box")
        m = 0.15
        xs = [a[0], b[0]]
        ys = [a[1], b[1]]
        self.ax_map.set_xlim(min(xs) - m, max(xs) + m)
        self.ax_map.set_ylim(min(ys) - m, max(ys) + m)
        self.ax_map.grid(True, alpha=0.3)
        self.ax_map.plot(a[0], a[1], "s", color="green", ms=12, label="A (grasp)")
        self.ax_map.plot(b[0], b[1], "s", color="red", ms=12, label="B (release)")
        (self.trail_line,) = self.ax_map.plot([], [], "-", color="tab:blue", alpha=0.4, lw=1)
        (self.actual_pt,) = self.ax_map.plot([], [], "o", color="tab:blue", ms=12, label="EEF actual")
        (self.cmd_pt,) = self.ax_map.plot([], [], "x", color="tab:orange", ms=12, mew=3, label="EEF commanded")
        self.ax_map.legend(loc="upper right", fontsize=8)

        # --- vertical z gauge ---
        self.ax_z = self.fig.add_subplot(gs[0, 1])
        self.ax_z.set_title("z [m]")
        self.ax_z.set_xticks([])
        z_lo = self.surf - self.depth - 0.02
        z_hi = self.surf + self.lift + 0.03
        self.ax_z.set_ylim(z_lo, z_hi)
        self.ax_z.axhline(self.surf, color="black", lw=1.5)
        self.ax_z.text(0.5, self.surf, " surface", va="bottom", ha="center", fontsize=7)
        self.ax_z.axhline(self.surf - self.depth, color="red", ls="--", lw=1)
        self.ax_z.text(0.5, self.surf - self.depth, " press depth", va="top", ha="center", fontsize=7, color="red")
        (self.z_marker,) = self.ax_z.plot([0.5], [self.surf], "o", color="tab:blue", ms=14)
        self.ax_z.set_xlim(0, 1)

        # --- text readout ---
        self.ax_txt = self.fig.add_subplot(gs[0, 2])
        self.ax_txt.axis("off")
        self.txt = self.ax_txt.text(
            0.0, 1.0, "", va="top", ha="left", family="monospace", fontsize=9,
            transform=self.ax_txt.transAxes,
        )

        # --- status bar ---
        self.ax_status = self.fig.add_subplot(gs[1, :])
        self.ax_status.axis("off")
        self.status = self.ax_status.text(
            0.01, 0.5, "", va="center", ha="left", family="monospace", fontsize=12,
            transform=self.ax_status.transAxes,
            bbox=dict(boxstyle="round", fc="#eee", ec="gray"),
        )

    def update(self, _frame):
        pose = _safe(lambda: self.robot.end_effector_pose)
        cmd = _safe(lambda: self.robot.target_pose)
        wrench = _safe(lambda: self.robot.end_effector_wrench, {})
        gw = _safe(lambda: self.gripper.value)
        st = status_bus.read()

        force = np.asarray(wrench.get("force", [np.nan] * 3), dtype=float) if wrench else np.array([np.nan] * 3)
        fmag = float(np.linalg.norm(force)) if np.all(np.isfinite(force)) else float("nan")

        if pose is not None:
            x, y, z = (float(v) for v in pose.position)
            self.tx.append(x)
            self.ty.append(y)
            self.trail_line.set_data(self.tx, self.ty)
            self.actual_pt.set_data([x], [y])
            # red when pressing below the surface, blue otherwise
            self.actual_pt.set_color("red" if z < self.surf - 1e-4 else "tab:blue")
            self.z_marker.set_data([0.5], [z])
            self.z_marker.set_color("red" if z < self.surf - 1e-4 else "tab:blue")

        if cmd is not None:
            self.cmd_pt.set_data([float(cmd.position[0])], [float(cmd.position[1])])

        # gripper state
        if gw is None:
            grip = "?"
        elif gw > 0.01:
            grip = f"OPEN ({gw*1000:.0f} mm)"
        else:
            grip = f"CLOSED/GRASP ({gw*1000:.0f} mm)"

        # text readout
        def fmt_pose(p):
            if p is None:
                return "   (none)"
            rpy = _rpy_deg(p)
            return (f"  xyz [m]: {p.position[0]:+.3f} {p.position[1]:+.3f} {p.position[2]:+.3f}\n"
                    f"  RPY [d]: {rpy[0]:+6.1f} {rpy[1]:+6.1f} {rpy[2]:+6.1f}")

        self.txt.set_text(
            "ACTUAL EEF\n" + fmt_pose(pose) + "\n\n"
            "COMMANDED EEF\n" + fmt_pose(cmd) + "\n\n"
            "F_ext [N] (base)\n"
            f"  Fx {force[0]:+7.2f}  Fy {force[1]:+7.2f}\n"
            f"  Fz {force[2]:+7.2f}  |F| {fmag:6.2f}\n\n"
            f"GRIPPER\n  {grip}\n"
        )

        # status bar
        stage = st.get("stage", "—")
        age = (time.time() - st["t"]) if "t" in st else None
        fresh = "live" if (age is not None and age < 2.0) else "no controller"
        self.status.set_text(
            f" STAGE: {stage:<22}  GRIPPER: {grip:<20}  |F_ext|: {fmag:5.2f} N   [{fresh}]"
        )

        return (self.trail_line, self.actual_pt, self.cmd_pt, self.z_marker, self.txt, self.status)


def main() -> int:
    robot = Robot(namespace=config.NAMESPACE)
    robot.wait_until_ready(timeout=10.0)
    gripper = Gripper(namespace=config.NAMESPACE)
    gripper.wait_until_ready(timeout=10.0)

    dash = Dashboard(robot, gripper)
    _ani = FuncAnimation(dash.fig, dash.update, interval=66, blit=False, cache_frame_data=False)
    try:
        plt.show()
    finally:
        gripper.shutdown()
        robot.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
