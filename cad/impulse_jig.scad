// =============================================================
// piezo_fall — Impulse Jig (parametric, Bambu X1C friendly)
// =============================================================
// Drops a stack of fishing weights from a fixed height through a
// guide tube to deliver a repeatable mechanical impulse to the
// floor for IR characterization.
//
// Tested fit: Bambu X1C (256 x 256 x 256 mm). Tube prints in one
// piece at 250 mm tall — 6 mm under the Z limit.
//
// Open in OpenSCAD (free, https://openscad.org). Pick a part via
// the `part` variable below, Render (F6), Export STL, slice in
// Bambu Studio.
//
// Three parts to print separately (suggested all on one plate):
//   "tube"  — vertical guide tube + integrated base plate
//   "puck"  — small shell that holds the fishing weights
//   "cap"   — friction-fit lid for the puck (optional; tape works)
//
// Default config:
//   8x 15 g fishing weights inside the puck = ~120 g total
//   230 mm drop height
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
weight_density_g_cc = 11.3;  // lead density (use 7.85 for steel)

// --- drop height & tube ---
drop_height_mm      = 230;   // distance from pin to inner tube bottom
tube_extra_top_mm   = 16;    // length above the pin. Puck sits ON
                              // the pin with its lower 16 mm guided
                              // by the tube and the rest exposed
                              // above. Don't need to enclose the
                              // whole puck — it only needs guidance
                              // until it accelerates down.
tube_wall_mm        = 3;     // tube wall thickness
puck_clearance_mm   = 1;     // radial gap between puck OD and tube ID
                              // (1 mm = 2 mm diameter clearance,
                              // smooth slide without binding)

// --- pin ---
pin_dia_mm          = 1.2;   // hole diameter (paperclip ≈ 1 mm)
pin_height_above_bot = 230;  // pin Z position above interior bottom

// --- base plate ---
base_dia_mm         = 70;    // base plate diameter (stability on tile)
base_thickness_mm   = 4;     // base thickness

// --- loading funnel at top of tube ---
funnel_extra_dia_mm = 5;     // how much wider the tube mouth gets at top
funnel_depth_mm     = 5;     // length of the funnel chamfer

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
puck_outer_dia_mm   = puck_inner_dia_mm + 2 * puck_wall_mm;  // 25 mm
puck_outer_radius   = puck_outer_dia_mm / 2;

// internal cavity volume must hold all the weights
puck_required_cavity_cc = weight_volume_cc * 1.15;  // 15% air gap
puck_inner_height_mm    = puck_required_cavity_cc * 1000 /
                          (3.14159 * puck_inner_radius * puck_inner_radius);
puck_total_height_mm    = puck_inner_height_mm + puck_bottom_mm;

// cap — friction-fit on top of puck
cap_lip_height_mm    = 4;
cap_clearance_mm     = 0.15;  // tight fit
cap_top_thickness_mm = 1.5;

// tube
tube_id_mm            = puck_outer_dia_mm + 2 * puck_clearance_mm;
tube_od_mm            = tube_id_mm + 2 * tube_wall_mm;
tube_total_height_mm  = drop_height_mm + tube_extra_top_mm;
total_print_height_mm = tube_total_height_mm + base_thickness_mm;

// echo at render-time
echo("=== IMPULSE JIG — derived dimensions ===");
echo(str("  total mass: ", total_mass_g, " g (", weight_count, "x ", weight_unit_mass_g, " g)"));
echo(str("  puck OD x H: ", puck_outer_dia_mm, " x ", puck_total_height_mm, " mm"));
echo(str("  tube ID x OD x H: ", tube_id_mm, " x ", tube_od_mm, " x ", tube_total_height_mm, " mm"));
echo(str("  TOTAL PRINT HEIGHT (tube+base): ", total_print_height_mm, " mm   [X1C Z=256 -> margin: ", 256 - total_print_height_mm, " mm]"));
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
    // base plate with central exit hole + edge chamfer
    difference() {
        // base solid with a small top chamfer (for nicer print finish at the
        // tube-base junction)
        union() {
            cylinder(d = base_dia_mm, h = base_thickness_mm);
        }
        // exit hole
        translate([0, 0, -0.1])
            cylinder(d = tube_id_mm, h = base_thickness_mm + 0.2);
    }

    // guide tube — open top and bottom
    translate([0, 0, base_thickness_mm]) {
        difference() {
            // outer wall
            cylinder(d = tube_od_mm, h = tube_total_height_mm);

            // inner bore (uniform across full height)
            translate([0, 0, -0.1])
                cylinder(d = tube_id_mm, h = tube_total_height_mm + 0.2);

            // loading funnel at the top — chamfer widening the ID
            translate([0, 0, tube_total_height_mm - funnel_depth_mm])
                cylinder(d1 = tube_id_mm,
                         d2 = tube_id_mm + funnel_extra_dia_mm,
                         h = funnel_depth_mm + 0.1);

            // pin holes — both sides, at pin_height_above_bot
            translate([0, 0, pin_height_above_bot])
                rotate([90, 0, 0])
                    cylinder(d = pin_dia_mm + 0.3, h = tube_od_mm + 2,
                             center = true);
        }
    }

    // small witness ring at pin line — visual indicator
    translate([0, 0, base_thickness_mm + pin_height_above_bot])
        difference() {
            cylinder(d = tube_od_mm + 0.8, h = 0.4);
            translate([0, 0, -0.1])
                cylinder(d = tube_od_mm, h = 0.6);
        }
}

module puck() {
    difference() {
        cylinder(d = puck_outer_dia_mm, h = puck_total_height_mm);
        translate([0, 0, puck_bottom_mm])
            cylinder(d = puck_inner_dia_mm, h = puck_total_height_mm);
    }
}

module cap() {
    fit_dia = puck_inner_dia_mm - 2 * cap_clearance_mm;
    union() {
        cylinder(d = puck_outer_dia_mm, h = cap_top_thickness_mm);
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
    tube_assembly();
    translate([tube_od_mm + 20, 0, 0]) puck();
    translate([tube_od_mm + 20 + puck_outer_dia_mm + 15, 0, 0]) cap();
}

// =============================================================
// BAMBU X1C PRINT NOTES
// =============================================================
// Bambu Studio import:
//   1. Export STL for each part (set `part` variable, F6, Export)
//   2. Drag all three STLs into a new Bambu Studio project
//   3. Use the "Auto-Arrange" button to lay them out on the plate
//   4. Material: PLA (Bambu Basic PLA is fine)
//   5. Profile: 0.20 mm Standard for tube; 0.16 mm Fine for puck
//      (the puck's striking face is more sensitive to layer height
//      than the tube's bore)
//
// Per-part settings:
//   TUBE
//     - Orientation: vertical (long axis = Z). DO NOT lay it on
//       its side — bore would need supports and surface would suffer.
//     - Walls: 4 (default)
//     - Infill: 30% gyroid (default is fine)
//     - Top/bottom layers: 5
//     - Build plate: textured PEI for adhesion on tall part
//     - Brim: 5 mm recommended for the tall thin print
//     - Print time: ~3 hours
//
//   PUCK
//     - Orientation: open face UP (bottom is the striking face,
//       print it as solid bottom layers on the build plate)
//     - Walls: 4
//     - Infill: doesn't matter — print 100% to keep the bottom 5 mm
//       fully solid, or set bottom-layers count high enough to make
//       the entire 3 mm bottom solid (recommended)
//     - Print time: ~30 min
//
//   CAP
//     - Orientation: flange-side DOWN on plate
//     - Walls: 4
//     - Infill: 100%
//     - Print time: ~10 min
//
//   All three on one plate: ~3.5 hours total (mostly the tube).
//   Bambu Studio's chamber + AMS not required; single-material PLA.
