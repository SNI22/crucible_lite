"""Visualize a profile: floor plan (2D top-down) + signal trace.

Helps confirm the simulator does what we think — sensor placement,
event locations, signal time-domain shape — primitive P1 visualization.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle, Circle

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.signals import (
    generate, list_profiles, GEOMETRIES, piezo_xy_for, FS_HZ,
)


def classify_impact(force_N, duration_s):
    """Map (force, duration) to event-type label for color coding.
    Primitive P1 event taxonomy derived from physics ranges in signals.py.
    """
    if duration_s < 0.010:
        return 'drop' if force_N < 1500 else 'drop_heavy'
    elif duration_s < 0.040:
        return 'footstep'
    elif duration_s < 0.060:
        return 'fall_impact'
    else:
        return 'slump_final'


TYPE_COLOR = {
    'drop':         '#ff8c00',  # orange — rigid object
    'drop_heavy':   '#d2691e',  # darker orange
    'footstep':     '#1f77b4',  # blue — walking
    'fall_impact':  '#dc143c',  # crimson — fall body impacts
    'slump_final':  '#8b0000',  # dark red — slump final soft impact
}


def render_profile(profile, seed=42, geometry='medium', output_path=None):
    """Render one profile as a 2-panel figure."""
    samples, gt = generate(profile, seed=seed, geometry=geometry)
    geom = GEOMETRIES[geometry]
    sensor_xy = piezo_xy_for(geom)

    fig, (ax_plan, ax_sig) = plt.subplots(1, 2, figsize=(14, 6),
                                          gridspec_kw={'width_ratios': [1, 2]})

    # ── Left: floor plan ──
    ax_plan.add_patch(Rectangle((0, 0), geom.Lx, geom.Ly,
                                 fill=False, edgecolor='gray', linewidth=2))
    # Sensor (triangle marker)
    ax_plan.plot(sensor_xy[0], sensor_xy[1],
                  '^', color='royalblue', markersize=18, markeredgecolor='navy',
                  label=f'Piezo sensor ({sensor_xy[0]:.2f}, {sensor_xy[1]:.2f})',
                  zorder=10)
    # Impact locations
    for i, impact in enumerate(gt.impacts):
        kind = classify_impact(impact.force_N, impact.duration_s)
        ax_plan.plot(impact.xy[0], impact.xy[1], 'o',
                      color=TYPE_COLOR[kind], markersize=10,
                      markeredgecolor='black', zorder=5)
        ax_plan.annotate(f't={impact.time_s:.1f}s\n{int(impact.force_N)}N',
                          (impact.xy[0], impact.xy[1]),
                          textcoords="offset points", xytext=(8, 5),
                          fontsize=7, alpha=0.8)
    # Walking trajectory: connect consecutive footsteps with line
    footsteps = [(imp.xy, imp.time_s) for imp in gt.impacts
                  if classify_impact(imp.force_N, imp.duration_s) == 'footstep']
    if len(footsteps) >= 2:
        # Group consecutive footsteps (gap < 2 s = same walk segment)
        segments = [[footsteps[0]]]
        for fs in footsteps[1:]:
            if fs[1] - segments[-1][-1][1] < 2.0:
                segments[-1].append(fs)
            else:
                segments.append([fs])
        for seg in segments:
            xs = [s[0][0] for s in seg]
            ys = [s[0][1] for s in seg]
            ax_plan.plot(xs, ys, '--', color='royalblue',
                          alpha=0.4, linewidth=1.5, zorder=3)
    # Legend with one entry per impact kind present
    present_kinds = set(classify_impact(imp.force_N, imp.duration_s)
                        for imp in gt.impacts)
    for kind in present_kinds:
        ax_plan.plot([], [], 'o', color=TYPE_COLOR[kind], markersize=10,
                      markeredgecolor='black', label=kind)
    ax_plan.set_xlim(-0.15, geom.Lx + 0.15)
    ax_plan.set_ylim(-0.15, geom.Ly + 0.15)
    ax_plan.set_aspect('equal')
    ax_plan.set_xlabel('X (m)')
    ax_plan.set_ylabel('Y (m)')
    ax_plan.set_title(f'Floor plan — {geometry} ({geom.Lx}×{geom.Ly} m)')
    ax_plan.legend(loc='upper left', fontsize=8, framealpha=0.9)
    ax_plan.grid(True, alpha=0.3)

    # ── Right: signal trace ──
    t = np.arange(len(samples)) / FS_HZ
    ax_sig.plot(t, samples, linewidth=0.4, color='black')
    # Vertical lines at each event onset
    for impact in gt.impacts:
        kind = classify_impact(impact.force_N, impact.duration_s)
        ax_sig.axvline(impact.time_s, color=TYPE_COLOR[kind],
                        alpha=0.6, linewidth=1)
    if gt.event_onset_s is not None:
        ax_sig.axvline(gt.event_onset_s, color='green', linestyle=':',
                        alpha=0.5, linewidth=2, label=f'event_onset_s = {gt.event_onset_s:.1f}')
        ax_sig.legend(loc='upper right', fontsize=8)
    peak = np.max(np.abs(samples))
    ax_sig.set_xlabel('Time (s)')
    ax_sig.set_ylabel('Floor accel (m/s²)')
    ax_sig.set_title(f'{profile} — class={gt.cls} — peak={peak:.3f} m/s² — '
                      f'{len(gt.impacts)} impacts')
    ax_sig.set_xlim(0, t[-1])
    ax_sig.grid(True, alpha=0.3)

    fig.suptitle(f'piezo_fall simulation render — profile={profile}, '
                  f'geometry={geometry}, seed={seed}',
                  fontsize=11, y=1.02)
    fig.tight_layout()

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=120, bbox_inches='tight')
        print(f'  saved: {output_path}')
    plt.close(fig)
    return output_path


def render_all_profiles(output_dir='docs/plots/sim_render', seed=42):
    """Render every profile in the catalog × every geometry."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for geometry in ['small', 'medium']:
        for profile in list_profiles():
            path = out_dir / f'{profile}__{geometry}__seed{seed}.png'
            render_profile(profile, seed=seed, geometry=geometry,
                            output_path=str(path))
            paths.append(path)
    return paths


if __name__ == '__main__':
    paths = render_all_profiles()
    print(f'\nGenerated {len(paths)} PNG files in docs/plots/sim_render/')
