"""
Central config for the thesis cloth-manipulation experiments (FR3 + arm_client).

Single source of truth for positions, fixed EEF orientation, the multi-stage
descent geometry, speeds, gripper, and logging. Edit values here; the experiment
scripts import this module and use these as defaults (CLI flags still override).

All positions are in the FR3 base frame, metres. All angles are degrees.
"""
from __future__ import annotations

import numpy as np
from scipy.spatial.transform import Rotation

# --------------------------------------------------------------------------
# Robot / namespace
# --------------------------------------------------------------------------
NAMESPACE = "fr3"

# --------------------------------------------------------------------------
# Fixed end-effector orientation (held constant for the whole task)
# --------------------------------------------------------------------------
# RPY in degrees, extrinsic 'xyz'. Operator-specified gripper-down orientation.
# NOTE: docs/device_context.md records the commanded constant as (90, 0, 0);
# this differs (mount/convention). Verify with --teach (it prints the achieved
# RPY) before trusting these numbers on hardware.
EEF_RPY_DEG: tuple[float, float, float] = (180.0, 0.0, 0.0)


def eef_orientation() -> Rotation:
    """The fixed task orientation as a scipy Rotation."""
    return Rotation.from_euler("xyz", EEF_RPY_DEG, degrees=True)


# --------------------------------------------------------------------------
# Task positions (base frame, metres). z is the TABLE SURFACE height — the
# contact threshold where the gripper just touches the table/cloth. The press
# below this surface is controlled by GRASP_DEPTH (below), not by z.
# Set these from a --teach capture (it prints ready-to-paste lines).
# --------------------------------------------------------------------------
POSITION_A: tuple[float, float, float] = (0.45, 0.20, 0.05)   # grasp the cloth edge here
POSITION_B: tuple[float, float, float] = (0.45, -0.20, 0.05)  # release here


def position_a() -> np.ndarray:
    return np.array(POSITION_A, dtype=float)


def position_b() -> np.ndarray:
    return np.array(POSITION_B, dtype=float)


# --------------------------------------------------------------------------
# Multi-stage descent geometry (m), relative to the TABLE SURFACE z of each
# position. APPROACH/FINE/LIFT are heights ABOVE the surface (positive up).
# --------------------------------------------------------------------------
APPROACH_DZ = 0.030   # clearance above surface before fine descent
FINE_DZ = 0.005       # 6Q +5 mm fine approach (above surface)
LIFT_DZ = 0.080       # lift height above surface

# GRASP_DEPTH: how far BELOW the table surface to press the EEF, to build
# contact force on the cloth for the grasp (positive = deeper below surface).
# This is the key grasp-tuning knob. The finray deforms over this depth;
# set 0 for a rigid parallel jaw (6Q note: it does not need the over-travel).
# Press target z = surface_z - GRASP_DEPTH.
GRASP_DEPTH = 0.003

# --------------------------------------------------------------------------
# Speeds (m/s)
# --------------------------------------------------------------------------
TRAVEL_SPEED = 0.10    # clearance moves / traverse A->B
DESCENT_SPEED = 0.03   # fine approach / contact / lower / retreat
PRESS_SPEED = 0.01     # very slow into the press

# --------------------------------------------------------------------------
# Gripper
# --------------------------------------------------------------------------
GRASP_FORCE_N = 20.0   # thin cloth -> keep modest
GRASP_SPEED = 0.05

# --------------------------------------------------------------------------
# F_ext / pose logging
# --------------------------------------------------------------------------
WRENCH_HZ = 30.0
