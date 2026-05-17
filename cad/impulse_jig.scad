// =============================================================
// piezo_fall — Impulse Jig (parametric)
// =============================================================
// Drops a stack of fishing weights from a fixed height through a
// guide tube to deliver a repeatable mechanical impulse to the
// floor for IR characterization.
//
// Open in OpenSCAD (free, https://openscad.org). Pick a part via
// the `part` variable below, then Render (F6) and Export STL.
//
// Three parts to print separately:
//   "tube"  — vertical guide tube + integrated base plate
//   "puck"  — small shell that holds the fishing weights
//   "cap"   — friction-fit lid for the puck (optional; tape works)
//
// Print all three on a single build plate if you orient the tube
// vertically. Puck + cap orient with their open faces upward.
//
// Default config:
//   8x 15g fishing weights inside the puck = ~120 g total
//   230 mm drop height (user's max ceiling/reach)
//   ~0.27 J impact energy
//
// =============================================================
// PICK ONE PART TO RENDER
// =============================================================
part = "tube";  // "tube", "puck", "cap", or "all" for preview

// =============================================================
// USER PARAMETERS — edit these to suit your build
// =============================================================

// --- impulse mass (the puck) ---
weight_count        = 8;     // number of 15 g fishing weights
weight_unit_mass_g  = 15;    // mass per weight (g)
weight_density_g_cc = 11.3;  // lead density (use 7.85 for steel, 11.3 for lead)

// --- drop height & tube ---
drop_height_mm      = 230;   // distance from pin to inner tube bottom
tube_extra_top_mm   = 30;    // length above the pin (for loading + finger clearance)
tube_wall_mm        = 3;     // tube wall thickness
puck_clearance_mm   = 1;     // radial gap between puck OD and tube ID
                              // (1 mm = ~2 mm diameter clearance, smooth slide)

// --- pin ---
pin_dia_mm          = 1.2;   // pin diameter (paperclip is ~1 mm; print hole slightly larger)
pin_height_above_bot = 230;  // pin location measured from inside tube bottom

// --- base plate ---
base_dia_mm         = 70;    // base plate diameter (stability on tile)
base_thickness_mm   = 4;     // base thickness

// --- rendering precision ---
$fn = 96;

// =============================================================
// DERIVED DIMENSIONS — auto-computed, don't edit
// =============================================================

// total mass and inferred puck size
total_mass_g     = weight_count * weight_unit_mass_g;
weight_volume_cc = total_mass_g / weight_density_g_cc;

// puck shell — sized to hold all the weights with a little air gap
puck_inner_dia_mm   = 21;
puck_inner_radius   = puck_inner_dia_mm / 2;
puck_wall_mm        = 2;
puck_bottom_mm      = 3;     // SOLID striking face
puck_outer_dia_mm   = puck_inner_dia_mm + 2 * puck_wall_mm;  // = 25 mm
puck_outer_radius   = puck_outer_dia_mm / 2;

// internal cavity volume must hold all the weights
puck_required_cavity_cc = weight_volume_cc * 1.15;  // 15% air gap for packing
puck_inner_height_mm    = puck_required_cavity_cc * 1000 /
                          (3.14159 * puck_inner_radius * puck_inner_radius);
puck_total_height_mm    = puck_inner_height_mm + puck_bottom_mm;

// cap — friction-fit on top of puck
cap_lip_height_mm   = 4;
cap_clearance_mm    = 0.15;   // tight fit
cap_top_thickness_mm = 1.5;

// tube
tube_id_mm          = puck_outer_dia_mm + 2 * puck_clearance_mm;  // = 27 mm
tube_od_mm          = tube_id_mm + 2 * tube_wall_mm;              // = 33 mm
tube_total_height_mm = drop_height_mm + tube_extra_top_mm;        // = 260 mm

// echo summary at render-time so user sees the numbers
echo("=== IMPULSE JIG — derived dimensions ===");
echo(str("  total mass: ", total_mass_g, " g (", weight_count, "x ", weight_unit_mass_g, " g)"));
echo(str("  puck OD x H: ", puck_outer_dia_mm, " x ", puck_total_height_mm, " mm"));
echo(str("  tube ID x OD x H: ", tube_id_mm, " x ", tube_od_mm, " x ", tube_total_height_mm, " mm"));
echo(str("  drop height: ", drop_height_mm, " mm"));
echo(str("  impact velocity: ",
        sqrt(2 * 9810 * drop_height_mm) / 1000, " m/s"));
echo(str("  kinetic energy: ",
        0.5 * total_mass_g / 1000 * pow(sqrt(2*9.81*drop_height_mm/1000), 2),
        " J"));

// =============================================================
// MODULES
// =============================================================

module tube_assembly() {
    // base plate with central exit hole
    difference() {
        cylinder(d = base_dia_mm, h = base_thickness_mm);
        translate([0, 0, -0.1])
            cylinder(d = tube_id_mm, h = base_thickness_mm + 0.2);
    }

    // guide tube — open top and bottom
    translate([0, 0, base_thickness_mm]) {
        difference() {
            // outer wall
            cylinder(d = tube_od_mm, h = tube_total_height_mm);
            // inner bore
            translate([0, 0, -0.1])
                cylinder(d = tube_id_mm, h = tube_total_height_mm + 0.2);
            // pin holes — both sides, at drop_height_mm above tube interior bottom
            // (which is at z = 0 from the start of the tube cylinder)
            translate([0, 0, drop_height_mm])
                rotate([90, 0, 0])
                    cylinder(d = pin_dia_mm + 0.3, h = tube_od_mm + 2,
                             center = true);
        }
    }

    // small witness mark at drop_height_mm so the user can see the pin line
    // (this is a 0.4 mm protrusion ring — visible but doesn't affect function)
    translate([0, 0, base_thickness_mm + drop_height_mm])
        difference() {
            cylinder(d = tube_od_mm + 0.8, h = 0.4);
            translate([0, 0, -0.1])
                cylinder(d = tube_od_mm, h = 0.6);
        }
}

module puck() {
    // bottom solid striking face + thin-wall cup
    difference() {
        cylinder(d = puck_outer_dia_mm, h = puck_total_height_mm);
        translate([0, 0, puck_bottom_mm])
            cylinder(d = puck_inner_dia_mm, h = puck_total_height_mm);
    }
}

module cap() {
    // a small disc that friction-fits into the top of the puck
    fit_dia = puck_inner_dia_mm - 2 * cap_clearance_mm;
    union() {
        // grip flange (sits on top of puck rim)
        cylinder(d = puck_outer_dia_mm, h = cap_top_thickness_mm);
        // lip that fits inside the puck mouth
        translate([0, 0, -cap_lip_height_mm + 0.01])
            cylinder(d = fit_dia, h = cap_lip_height_mm);
    }
}

// =============================================================
// RENDER
// =============================================================

if (part == "tube") {
    tube_assembly();
} else if (part == "puck") {
    puck();
} else if (part == "cap") {
    cap();
} else if (part == "all") {
    // preview layout — all three parts shown side by side
    tube_assembly();
    translate([tube_od_mm + 20, 0, 0]) puck();
    translate([tube_od_mm + 20 + puck_outer_dia_mm + 15, 0, 0]) cap();
}
