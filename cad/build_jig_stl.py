"""Build STL files for the impulse jig from the same parameters as impulse_jig.scad.

This is a stopgap until OpenSCAD is installed. The SCAD file is the canonical
parametric source — this Python script generates the same geometry numerically
so we can preview / print without a SCAD installation.

Run:
    /tmp/stl_env/bin/python3 cad/build_jig_stl.py

Outputs:
    cad/jig_tube.stl
    cad/jig_puck.stl
    cad/jig_cap.stl
    cad/jig_preview.png  (rendered preview)
"""
import math
import os
import trimesh
import numpy as np
import matplotlib.pyplot as plt

OUT = os.path.dirname(os.path.abspath(__file__))

# ---- parameters (mirror impulse_jig.scad) ----
weight_count          = 8
weight_unit_mass_g    = 15
weight_density_g_cc   = 11.3

drop_height_mm        = 230
tube_extra_top_mm     = 16   # tuned for Bambu X1C Z=256mm (total height 250mm)
tube_wall_mm          = 3
puck_clearance_mm     = 1
pin_dia_mm            = 1.2
base_dia_mm           = 70
base_thickness_mm     = 4
funnel_extra_dia_mm   = 5    # loading-funnel widening at tube top
funnel_depth_mm       = 5

# derived
total_mass_g          = weight_count * weight_unit_mass_g
weight_volume_cc      = total_mass_g / weight_density_g_cc

puck_inner_dia_mm     = 21
puck_inner_radius     = puck_inner_dia_mm / 2
puck_wall_mm          = 2
puck_bottom_mm        = 3
puck_outer_dia_mm     = puck_inner_dia_mm + 2 * puck_wall_mm
puck_required_cavity_cc = weight_volume_cc * 1.15
puck_inner_height_mm  = puck_required_cavity_cc * 1000 / (math.pi * puck_inner_radius ** 2)
puck_total_height_mm  = puck_inner_height_mm + puck_bottom_mm

cap_lip_height_mm     = 4
cap_clearance_mm      = 0.15
cap_top_thickness_mm  = 1.5

tube_id_mm            = puck_outer_dia_mm + 2 * puck_clearance_mm
tube_od_mm            = tube_id_mm + 2 * tube_wall_mm
tube_total_height_mm  = drop_height_mm + tube_extra_top_mm

# ---- print summary ----
v_impact_ms = math.sqrt(2 * 9.81 * drop_height_mm / 1000)
ke_J = 0.5 * (total_mass_g / 1000) * v_impact_ms ** 2
total_print_height_mm = tube_total_height_mm + base_thickness_mm
print("=== IMPULSE JIG — derived dimensions ===")
print(f"  total mass: {total_mass_g} g ({weight_count}x {weight_unit_mass_g} g)")
print(f"  puck OD x H: {puck_outer_dia_mm} x {puck_total_height_mm:.1f} mm")
print(f"  tube ID x OD x H: {tube_id_mm} x {tube_od_mm} x {tube_total_height_mm} mm")
print(f"  TOTAL PRINT HEIGHT (tube+base): {total_print_height_mm} mm  "
      f"[X1C Z=256mm -> margin: {256 - total_print_height_mm} mm]")
print(f"  drop height: {drop_height_mm} mm")
print(f"  impact velocity: {v_impact_ms:.2f} m/s")
print(f"  kinetic energy: {ke_J:.3f} J")

# ---- helpers ----
def cyl(d, h, z=0, sections=64):
    m = trimesh.creation.cylinder(radius=d/2, height=h, sections=sections)
    m.apply_translation([0, 0, h/2 + z])
    return m

def cyl_at_y(d, h, sections=24):
    # cylinder along Y-axis, centered on origin
    m = trimesh.creation.cylinder(radius=d/2, height=h, sections=sections)
    # default cylinder is along Z; rotate to align with Y
    m.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2, [1, 0, 0]))
    return m

# ---- tube assembly ----
print("\nBuilding tube...")
# base plate
base_solid = cyl(base_dia_mm, base_thickness_mm)
base_hole  = cyl(tube_id_mm, base_thickness_mm + 0.2, z=-0.1)
base       = base_solid.difference(base_hole)

# tube
tube_outer = cyl(tube_od_mm, tube_total_height_mm, z=base_thickness_mm)
tube_bore  = cyl(tube_id_mm, tube_total_height_mm + 0.2, z=base_thickness_mm - 0.1)
# loading funnel at top (truncated cone widening the bore)
funnel = trimesh.creation.cone(radius=(tube_id_mm + funnel_extra_dia_mm) / 2,
                                height=funnel_depth_mm + 0.1, sections=64)
# cone() makes a cone with apex up. We want a frustum widening upward.
# Construct as a cylinder difference for simplicity:
funnel_box   = cyl(tube_id_mm + funnel_extra_dia_mm, funnel_depth_mm + 0.1,
                   z=base_thickness_mm + tube_total_height_mm - funnel_depth_mm)
# Use a tapered approach: subtract a cone-shaped solid
# Easier: just use a slight outward chamfer via a wider cylinder at top
pin_hole = cyl_at_y(pin_dia_mm + 0.3, tube_od_mm + 2)
pin_hole.apply_translation([0, 0, base_thickness_mm + drop_height_mm])
tube = tube_outer.difference([tube_bore, funnel_box, pin_hole])

# small witness ring at pin height
ring_outer = cyl(tube_od_mm + 0.8, 0.4, z=base_thickness_mm + drop_height_mm)
ring_hole  = cyl(tube_od_mm,       0.6, z=base_thickness_mm + drop_height_mm - 0.1)
ring = ring_outer.difference(ring_hole)

tube_assembly = trimesh.util.concatenate([base, tube, ring])
tube_assembly.export(os.path.join(OUT, 'jig_tube.stl'))
print(f"  saved jig_tube.stl ({len(tube_assembly.faces)} faces)")

# ---- puck ----
print("\nBuilding puck...")
puck_outer = cyl(puck_outer_dia_mm, puck_total_height_mm)
puck_inner = cyl(puck_inner_dia_mm, puck_total_height_mm - puck_bottom_mm + 0.1, z=puck_bottom_mm)
puck = puck_outer.difference(puck_inner)
puck.export(os.path.join(OUT, 'jig_puck.stl'))
print(f"  saved jig_puck.stl ({len(puck.faces)} faces)")

# ---- cap ----
print("\nBuilding cap...")
fit_dia = puck_inner_dia_mm - 2 * cap_clearance_mm
cap_flange = cyl(puck_outer_dia_mm, cap_top_thickness_mm)
cap_lip    = cyl(fit_dia, cap_lip_height_mm, z=-cap_lip_height_mm + 0.01)
cap = trimesh.util.concatenate([cap_flange, cap_lip])
cap.export(os.path.join(OUT, 'jig_cap.stl'))
print(f"  saved jig_cap.stl ({len(cap.faces)} faces)")

# ---- preview render ----
print("\nRendering preview...")

# layout: tube on left, puck in middle, cap on right
def shift(mesh, dx):
    m = mesh.copy()
    m.apply_translation([dx, 0, 0])
    return m

x_tube = 0
x_puck = tube_od_mm/2 + 25 + puck_outer_dia_mm/2
x_cap  = x_puck + puck_outer_dia_mm/2 + 15 + puck_outer_dia_mm/2

scene_meshes = [
    ('tube',  tube_assembly,                       'tab:blue'),
    ('puck',  shift(puck, x_puck),                 'tab:orange'),
    ('cap',   shift(cap,  x_cap),                  'tab:green'),
]

fig = plt.figure(figsize=(18, 10))

# 3D view
ax = fig.add_subplot(2, 2, 1, projection='3d')
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
for name, m, color in scene_meshes:
    tris = m.triangles
    poly = Poly3DCollection(tris, alpha=0.7, edgecolor='k', linewidth=0.05, facecolor=color)
    ax.add_collection3d(poly)
ax.set_xlim(-base_dia_mm/2 - 5, x_cap + puck_outer_dia_mm/2 + 5)
ax.set_ylim(-base_dia_mm/2, base_dia_mm/2)
ax.set_zlim(0, tube_total_height_mm + base_thickness_mm + 5)
try:
    ax.set_box_aspect((x_cap + puck_outer_dia_mm + 10, base_dia_mm, tube_total_height_mm + 10))
except Exception:
    pass
ax.set_xlabel('X (mm)'); ax.set_ylabel('Y (mm)'); ax.set_zlabel('Z (mm)')
ax.set_title('3D view — tube + puck + cap')
ax.view_init(elev=18, azim=-60)

# Front view (X-Z) — slice all parts
ax = fig.add_subplot(2, 2, 2)
for name, m, color in scene_meshes:
    # cut a slice along Y=0 to expose the bore
    try:
        sliced = m.section(plane_origin=[0, 0, 0], plane_normal=[0, 1, 0])
        if sliced is not None:
            # convert to 2D
            slice_2d, _ = sliced.to_2D()
            for poly in slice_2d.polygons_full:
                ax.fill(*poly.exterior.xy, facecolor=color, edgecolor='k', linewidth=0.5, alpha=0.5)
                for interior in poly.interiors:
                    ax.fill(*interior.xy, facecolor='white', edgecolor='k', linewidth=0.5)
    except Exception:
        # fallback: silhouette
        v = m.vertices
        ax.fill(v[:, 0], v[:, 2], facecolor=color, edgecolor='k', linewidth=0.1, alpha=0.2)
ax.set_xlabel('X (mm)'); ax.set_ylabel('Z (mm)'); ax.set_title('Section through Y=0 (inside view)')
ax.set_aspect('equal'); ax.grid(alpha=0.3)

# Top view (X-Y, looking down)
ax = fig.add_subplot(2, 2, 3)
for name, m, color in scene_meshes:
    # project to X-Y by drawing outlines at multiple Z slices
    # simpler: just outline the vertices in X-Y
    v = m.vertices
    # convex hull in xy as a footprint approximation
    try:
        from scipy.spatial import ConvexHull
        pts = v[:, :2]
        hull = ConvexHull(pts)
        ax.fill(pts[hull.vertices, 0], pts[hull.vertices, 1],
                facecolor=color, edgecolor='k', alpha=0.3, label=name)
    except Exception:
        pass
ax.set_xlabel('X (mm)'); ax.set_ylabel('Y (mm)'); ax.set_title('Top view (footprints)')
ax.set_aspect('equal'); ax.grid(alpha=0.3); ax.legend(loc='upper right')

# Dimensions text panel
ax = fig.add_subplot(2, 2, 4)
ax.axis('off')
info = f"""IMPULSE JIG — design summary
Target printer: BAMBU X1C (256 x 256 x 256 mm)

Mass:          {total_mass_g} g  ({weight_count}× {weight_unit_mass_g} g fishing weights)
Drop height:   {drop_height_mm} mm
Impact vel:    {v_impact_ms:.2f} m/s
Energy:        {ke_J:.3f} J

TUBE
  ID:          {tube_id_mm} mm  (puck OD + {2*puck_clearance_mm} mm clearance)
  OD:          {tube_od_mm} mm
  Tube only:   {tube_total_height_mm} mm  (drop + {tube_extra_top_mm} mm above pin)
  Base plate:  {base_dia_mm} mm dia × {base_thickness_mm} mm thick
  PRINT TOTAL: {total_print_height_mm} mm  [X1C Z=256 -> {256 - total_print_height_mm} mm margin]

PUCK
  OD:          {puck_outer_dia_mm} mm
  ID:          {puck_inner_dia_mm} mm
  Height:      {puck_total_height_mm:.1f} mm
  Bottom:      {puck_bottom_mm} mm SOLID (striking face)

CAP
  OD:          {puck_outer_dia_mm} mm
  Lip dia:     {puck_inner_dia_mm - 2*cap_clearance_mm:.2f} mm (friction fit)
  Lip depth:   {cap_lip_height_mm} mm

PIN
  Dia:         {pin_dia_mm} mm (hole {pin_dia_mm+0.3} mm for paperclip)
  Z position:  {drop_height_mm} mm above tube interior bottom

LOADING NOTE
  When loaded, the puck's lower {tube_extra_top_mm} mm is guided by
  the tube. The remaining {puck_total_height_mm - tube_extra_top_mm:.0f} mm
  sticks above the tube top — that's fine, puck only needs guidance
  until it accelerates downward.

PRINT SETTINGS (Bambu Studio)
  Material:    PLA (Bambu Basic PLA fine)
  Tube:        vertical, 4 walls, 30% gyroid, 0.2 mm layer, brim 5mm
  Puck:        open-face up, 4 walls, 100% infill, 0.16 mm layer
  Cap:         flange-down, 4 walls, 100% infill
  All on one plate: ~3.5 hr total (mostly tube)
"""
ax.text(0.02, 0.98, info, family='monospace', fontsize=10, va='top', ha='left')

plt.tight_layout()
plt.savefig(os.path.join(OUT, 'jig_preview.png'), dpi=110, bbox_inches='tight')
print(f"  saved jig_preview.png")
print("\nDone.")
