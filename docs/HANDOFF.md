# Thesis Handoff — Soft vs Rigid Gripper Benchmark for Cloth Grasping

**Snapshot date:** 2026-06-29
**Author:** Shiyao Ni (shiyao.ni@mail.mcgill.ca)
**McGill Master's thesis** — Department of Mechanical Engineering

This document lets you resume work on this thesis from a fresh machine.
Read it end-to-end before touching anything.

---

## 1. Repository layout

### 1.1 Thesis repo (this repo, tracked by git)

```
crucible/cloth-grasp/
├── CONSTITUTION.md                # Crucible governance framework (Articles I & II)
├── docs/
│   ├── HANDOFF.md                 # THIS FILE
│   ├── experiment.md              # Original tilt × depth experiment plan
│   ├── device_context.md          # Device purpose, BOM, signal inventory
│   ├── toolchain_config.md        # Active board, pins, libs, blocked tools
│   ├── governance/
│   │   ├── amendments.md          # Ratified rules (Amend. 1 = domain primitives)
│   │   ├── case_law.md            # All Judicial Hearing rulings
│   │   └── bills/                 # Six enacted Bills (0001–0006)
│   ├── memory/                    # Long-lived memory notes
│   │   └── MEMORY.md              # Index of memory entries
│   └── thesis/
│       ├── Thesis.tex             # Main LaTeX entrypoint (McGill_PhD_Thesis_Template-based, since 2026-07-30)
│       ├── Thesis.pdf             # Built output (stale — last built under the old template)
│       ├── Thesis_methods_only.tex # Standalone Methods+Experiments excerpt for supervisor review
│       ├── content/               # ALL chapters + frontmatter now live flat here (one file each):
│       │   ├── TitlePage.tex, AbstractEnglish.tex, AbstractFrench.tex,
│       │   │   Contributions.tex, Acknowledgements.tex
│       │   ├── Introduction.tex, RelevantLiterature.tex, Methods.tex,
│       │   │   Experiments.tex, Results.tex, Discussion.tex, Conclusions.tex
│       │   └── Publications.tex, Acronyms.tex
│       ├── latex-pkg/             # Margin/style .sty files — still used by Thesis_methods_only.tex
│       └── images/                # All figures (56 PNG files, `final_*.png` are canonical, + McGill logo PDF)
│
│       NOTE: the old `base/<chapter>/` directory structure, lowercase-named
│       content files, and `img/`/`figures/` dirs were retired on 2026-07-30
│       when the thesis was migrated onto the McGill_PhD_Thesis_Template
│       (~/Documents/thesis_template/McGill_PhD_Thesis_Template). All real
│       content was ported verbatim; only leftover generic-template cruft
│       (unrelated placeholder acronyms/publications/appendix/bib entries,
│       an orphaned French abstract about an unrelated metamodelling thesis,
│       a stale .bak draft) was dropped. See git history around that date
│       for the full diff if anything seems missing.
```

### 1.2 Experimental data repo (NOT tracked by git — separate location)

```
~/Documents/sim2real_adlros/experiments/cloth_grasp/
├── experiment1/                   # 0° depth sweep per variant
│   ├── finray_18/
│   ├── finray_18_model2/
│   ├── finray_26/
│   ├── finray_26_5deg/
│   ├── parallel_jaw_stock/
│   └── parallel_jaw_TPU/
└── experiment2/                   # ±2.5° tilt sweep per variant
    ├── finray_18/
    ├── finray_18_model2/
    ├── finray_26/
    ├── finray_26_5deg/
    ├── parallel_jaw_stock/
    └── parallel_jaw_TPU/
```

Each variant folder contains `depth_+NN.Nmm_tx±DD.D_ty±DD.D_YYYYMMDD_HHMMSS/`
cell directories with `depth_summary.json`, `ground_truth_used.json`, and
per-trial `trial_NNN/pose_wrench.csv`. See
`.claude/projects/-home-sni22-crucible-cloth-grasp/memory/cloth_grasp_coverage_matrix_2026_06_26.md`
for the coverage matrix at last snapshot.

**IMPORTANT**: `experiments/cloth_grasp/` is **not git-tracked** and is
too large to email. Move it to the new laptop via rsync, USB drive, or
cloud sync. If you commit only the thesis repo, you lose the ability to
regenerate any figure from raw data on the new laptop.

---

## 2. Thesis current state (2026-06-29)

### 2.1 Title

**"Soft vs Rigid Gripper Benchmark for Cloth Grasping"**
Subtitle: *A Force-Depth-Tilt Characterization of Parallel-Jaw and Finray
Geometries*

Set in `docs/thesis/content/FirstPage.tex`. Author name and copyright
year still contain `\TODO{...}` placeholders — fill in before submission.

### 2.2 Chapter structure (Traditional McGill format)

| Ch | Title | File | Status |
|----|---|---|---|
| 1 | Introduction | `content/Introduction.tex` | Existed before this session, not modified |
| 2 | Background | `content/RelevantLiterature.tex` | Existed before, not modified |
| 3 | Methods | `content/Methods.tex` | Existed before, `ch:exp2` refs updated to `ch:experiments` |
| 4 | Experimental Design and Procedure | `content/Experiments.tex` | Combines old exp1 + exp2 |
| 5 | Results | `content/Results.tex` | Number-heavy, tables only |
| 6 | Discussion | `content/Discussion.tex` | Interpretation/mechanisms |
| 7 | Conclusion and Future Work | `content/Conclusions.tex` | Existed before, `ch:exp2` refs updated |

(Paths updated 2026-07-30 — see the note in §1.1. Content is unchanged from the
prior `base/<chapter>/<chapter>.tex` layout, just relocated. The old orphaned
`base/exp1/exp1.tex` and `base/exp2/exp2.tex` — superseded by `Experiments.tex`
above — were deleted in that same migration, not just left on disk.)

### 2.3 Building the PDF

```bash
cd docs/thesis
latexmk -pdf -interaction=nonstopmode -halt-on-error Thesis.tex
```

Output: `Thesis.pdf`. Requires `pdflatex` and `latexmk`. On a fresh
Ubuntu machine: `sudo apt install texlive-full`.

Current build: **44 pages, 393 KB**. No fatal errors. Only warnings are
`\TODO{...}` placeholders (author name, GitHub URL, commit hash).

---

## 3. Experimental data current state

### 3.1 Gripper roster (6 variants)

| Variant | Family | Description |
|---|---|---|
| `finray_18` | Finray | 18 mm blade thickness (original print) |
| `finray_18_model2` | Finray | Second print of same 18 mm CAD (manufacturing variability) |
| `finray_26` | Finray | 26 mm blade thickness, flat mount |
| `finray_26_5deg` | Finray | 26 mm blade on 5° inclined seat |
| `parallel_jaw_stock` | Rigid | Bare Franka default parallel-jaw fingers |
| `parallel_jaw_TPU` | Rigid | Parallel jaw with 2 mm TPU 90A compliant pad |

### 3.2 Coverage (approximate cell counts as of 2026-06-29)

| Variant | 0° | x +2.5° | x −2.5° | y +2.5° | y −2.5° |
|---|---|---|---|---|---|
| fr18 | 17 | 12 | 12 | 9 | 9 |
| fr18_model2 | 14 | 12 | 12 | 11 | 10 |
| fr26 | ~10 | 12 | 12 | 10 | 10 |
| fr26_5deg | ~10 | 13 | 13 | 14 | 14 |
| pj_stock | 9 | 4 | 0 | 4 | 3 |
| pj_TPU | 4 | 8 | 0 | 4 | 3 |

**Major open coverage gaps**:
- `pj_stock` x −2.5° column entirely empty (would unlock rigid-jaw x-bias bars)
- `pj_TPU` x −2.5° column entirely empty
- `pj_TPU` boundary depths (+0.5, +1.0, +2.0 mm) thin on y axis

For the exact per-cell breakdown at snapshot time, see the auto-memory
entry `cloth_grasp_coverage_matrix_2026_06_26.md`. Re-derive fresh from
filesystem before making run decisions — the matrix drifts fast.

### 3.3 Trial outcome classification

Three-way taxonomy used throughout the analysis (Section~\ref{sec:trial-protocol}
in the thesis):
- **success** — trial completed, Fz measured, cloth held after lift
- **no-grasp** — trial completed, Fz measured, cloth slipped at lift (VALID Fz data)
- **failed trial** — controller error or aborted (Fz INVALID, excluded)

Never treat no-grasp trials as failed trials; their force data is
scientifically valid and essential for characterising boundary depths.

---

## 4. Key findings (thesis-ready)

### 4.1 Canonical force-depth curve shape (all finrays)

All four finray variants exhibit a stereotyped **bell + valley + recovery**
shape:
1. Boundary rise (linear engagement)
2. Knee peak at +2 to +3 mm
3. Valley trough at +6 to +8 mm (rib buckling)
4. Recovery rise past +10 mm (structural compression)

Depth locations of the four features are within ±1 mm across all four
finray variants; force magnitudes scale with finger frontal area.

### 4.2 Mount-tilt equivalence: 5° mount ≡ −1.13 mm depth shift

Cleanest quantitative finding of the campaign. `finray_26_5deg` aligned
to `finray_26` requires:

| Axis | Depth shift | Force offset | RMSE |
|---|---|---|---|
| x | −1.14 mm | +2.7 N | 1.75 N |
| y | −1.12 mm | +3.1 N | 1.58 N |

**Axis-independent within 0.03 mm.** Geometric interpretation: the load
concentrates on the proximal ~25% of the finger length
(L_eff ≈ 13 mm out of 50 mm total finger length; 1.13 = 13·sin(5°)).

### 4.3 Cross-axis bias sign reversal at the boundary

On `fr26_5deg` and on `fr18` (independently), the x-axis and y-axis
biases have **opposite signs** at boundary depths. Consistent with a
cloth-fixture direction preference (not gripper geometry) breaking the
mirror-plane symmetry of the x-axis measurement.

### 4.4 Manufacturing variability vs cross-session drift

- **Same-day print-to-print variability** (`fr18` vs `fr18_model2`):
  ~5.5 N (~15% of peak force) after best-fit alignment
- **Same-print cross-session drift** (`fr18` June-4 vs June-28):
  7–10 N at knee-adjacent depths

**Cross-session drift is LARGER than manufacturing variability.** All
same-session comparisons are internally valid; cross-day claims are
qualified throughout the thesis.

### 4.5 Bipolar tilt-bias structure

The bias trajectory itself follows a bipolar shape in depth: signed peak
at boundary → zero-crossing near knee → sign-reversed plateau through
valley → depth-gated attenuation. Best characterised on `fr26_5deg`
y-axis with 14 sign-flip pairs from −2 to +16 mm.

### 4.6 Deployment envelope

- Finray successful-grasp window: 8–12 mm on all variants
- Parallel jaw successful-grasp window: 1–2 mm
- Parallel jaws hit Franka excess-force safety within 1–1.5 mm past
  their successful window; finrays never triggered safety in tested
  range

---

## 5. Open items (priority-ordered)

### 5.1 HIGH — needed for thesis completion

1. **Fill `\TODO` placeholders** in `content/FirstPage.tex`
   (author name, copyright year) and in
   `base/discussion/discussion.tex` (public GitHub URL, commit hash).
2. **Add figures to Results/Discussion chapters.** The narrative
   references phenomena but doesn't yet `\includegraphics` the
   `docs/thesis/img/final_*.png` plots. Recommended figure integration:
   - Sec `sec:zero-tilt-results` → `final_fr26_all.png` or
     `final_fr18_model2_all.png` as an exemplar canonical curve
   - Sec `sec:bipolar-bias-results` → `fr26_5deg_y_axis_sweep.png`
   - Sec `sec:cross-axis-results` → `fr26_5deg_xy_axes.png`
   - Sec `sec:mount-tilt-results` → `fr26_vs_fr26_5deg_aligned.png` +
     `fr26_vs_fr26_5deg_y_aligned.png`
   - Sec `sec:manufacturing-results` → `final_fr18_vs_model2.png`
   - Sec `sec:pj-vs-finray-results` → `final_pj_stock_vs_tpu.png` and
     one finray comparison
3. **Complete `pj_stock` and `pj_TPU` x −2.5° sweeps** to enable
   rigid-jaw x-bias comparison with finray family.

### 5.2 MEDIUM — nice to have

4. Rotate the cloth specimen 90° and re-measure a small subset of
   fr26_5deg boundary cells. Would isolate the cloth-weave direction
   from the fixture contribution in the cross-axis sign-reversal
   finding.
5. Re-run 3–4 depths on `fr18_model2` to widen its dataset with the
   +1.0 and +12 mm boundary points that fr18 has but model2 doesn't
   yet.

### 5.3 LOW — future work / thesis discussion

6. Third finray print (`finray_18_model3` if manufactured) would
   strengthen the manufacturing-variability claim from N=2 to N=3.
7. CT-scan post-hoc analysis of `fr18` vs `fr18_model2` fingers to
   verify the rib-wall-thickness hypothesis for the qualitative x-bias
   sign flip between prints.

---

## 6. How to resume on the new laptop

### 6.1 Bootstrap sequence

```bash
# 1. Clone or pull the thesis repo
git clone <this-repo-url> crucible-cloth-grasp
cd crucible-cloth-grasp

# 2. Copy experimental data (NOT in git)
rsync -av <source>:~/Documents/sim2real_adlros/experiments/cloth_grasp/ \
          ~/Documents/sim2real_adlros/experiments/cloth_grasp/

# 3. Install LaTeX
sudo apt install texlive-full latexmk

# 4. Build the thesis PDF to confirm setup
cd docs/thesis
latexmk -pdf -interaction=nonstopmode Thesis.tex

# 5. If running new experiments — set up pixi/ROS 2 stack per
#    the Franka launch memory in .claude/projects/.../memory/franka_fci_launch.md
#    and DDS memory in franka_dds_vpn_conflict.md
```

### 6.2 Files to read on arrival

1. **`docs/HANDOFF.md`** (this file) — you are here
2. **`docs/thesis/Thesis.pdf`** — current thesis state
3. **`CONSTITUTION.md`** and **`docs/governance/amendments.md`** — the
   Crucible governance framework (Articles I & II, ratified amendments)
4. **`.claude/projects/-home-sni22-crucible-cloth-grasp/memory/MEMORY.md`** —
   auto-memory index (session-to-session notes, especially
   franka_fci_launch, franka_dds_vpn_conflict, and
   cloth_grasp_coverage_matrix)

### 6.3 Regenerating plots from raw data

The current `docs/thesis/img/final_*.png` plots are generated by ad-hoc
Python scripts embedded in the conversation history. There is **no
persistent plotting script** in the repo. Two options:

- **Option A (fast)**: git-commit the current PNG files with the thesis
  and rely on them until re-plotting is needed.
- **Option B (reproducible)**: consolidate the Python plotting logic
  into a script under `docs/thesis/scripts/plot_final.py` before
  committing. This is the recommended path for thesis reproducibility.

Option B is not yet done. If you're going to re-run plots often on the
new laptop, do Option B first.

---

## 7. Repositories and permissions

- **Thesis repo**: this repo (private McGill GitLab or personal GitHub —
  populate the URL in `discussion.tex` when submitting).
- **`sim2real_adlros`**: private ADLROS lab repo containing the
  `arm_client` Python package. The `experiments/cloth_grasp/` subtree
  is untracked; do not add it to that repo (too large, high churn).

---

## 8. Housekeeping notes

- The `experiments/cloth_grasp/` tree has 65+ underscore-prefixed
  "staged" cells (older data superseded by newer runs, and 4 old
  duplicate cells that were hard-deleted). Staged cells are retained
  as historical record but are NOT read by any analysis script (all
  pool functions filter out `_depth_*` directories).
- Two `\TODO` placeholders in `Discussion.tex` (public GitHub URL,
  commit hash) — fill in before final submission.
- (2026-07-30) `exp1.tex`/`exp2.tex` and the rest of the old `base/`
  layout were deleted as part of the McGill_PhD_Thesis_Template migration
  — see the note in §1.1. No longer just "safe to delete"; already done.
- **No LaTeX toolchain is available on the Windows machine this migration
  was done on** — the new `Thesis.tex` has not been build-verified.
  Package/macro usage was audited manually (every `\usepackage` the active
  chapters actually need — amsmath, booktabs, url, fontenc/lmodern for
  `\textmu`, vmargin for GPS margins — was cross-checked against actual
  command usage in the chapter files), but run
  `latexmk -pdf -interaction=nonstopmode -halt-on-error Thesis.tex` on the
  Linux box at the first opportunity and fix anything that surfaces.
