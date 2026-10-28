# ApartGEMSDOE1 — H-APART-5 (`PLKC-DualOOF-CELF E3`) Concealed Piedmont, Fluvial Knickzone & Hydrothermal Fault Discovery

> **AUTOMATED VALIDATION & 950-RASTER UNIQUENESS GATE VERDICT: `PASS — UNIQUE & OK TO DOWNLOAD AND SUBMIT`**
> - **Promoted Unique GeoTIFF**: [`docs/downloads/apartgems1-plkc-dualoof-e3-20261028-4499e12f-zeros.tif`](docs/downloads/apartgems1-plkc-dualoof-e3-20261028-4499e12f-zeros.tif) (`137,227` bytes) · Single-TIFF Archive: [`docs/downloads/apartgems1-plkc-dualoof-e3-20261028-4499e12f-zeros.zip`](docs/downloads/apartgems1-plkc-dualoof-e3-20261028-4499e12f-zeros.zip)
> - **Archived Prior Submission (Do Not Resubmit)**: [`docs/downloads/archive/apartgems1-udth-submod-e3-20261027-50e7b334-zeros.tif`](docs/downloads/archive/apartgems1-udth-submod-e3-20261027-50e7b334-zeros.tif) (`0.0525` `ORGANIZER-CONFIRMED`, `10.81%` 3-px overlap with promoted Session 2)
> - **SHA-256**: `9a2d5d67f65979d2054f8babd8dea3c5f516dc871ab01e3434adc74ea1838d73` | **Decoded Footprint SHA-256**: `4499e12f937d632f1d97de90bab80d8a297c8a159ecb8f1f583bb1627a4d0111`
> - **Submission Name**: `apartgems1-plkc-dualoof-e3-4499e12f`
> - **Short Submission Comment (`109/140` chars)**: `H-APART-5 PLKC-DualOOF (E3): Dual-OOF 1m/10m chi+updip+GDR1391+piedmont; CELF d>=2.8, [0,1] zeros (37654 px).`
> - **Format & Portal `[0, 1]` Safety**: Single-band `float32`, `EPSG:32611`, `3730×3292`, `Affine(100, 0, 243350, 0, -100, 4508550)`, `nodata=None`, **`min=0.0`, `max=1.0`, `0` NaNs and `0` Infs across all `12,279,160` grid cells** (permanently prevents `"Predicted values must be in range [0, 1]"`).
> - **Spacing & Collar Hygiene**: **`37,654` binary `1.0` pixels**, `min NN = 2.8284 px` (`0.0% < 2.8 px`, **`1.28%` >=3 neighbors in 300 m** vs Session 1's `97.30%`), `0` on catalogue, `0` inside `<=200 m` collar, `15,546` (`41.29%`) in far-field basins `>1.5 km`.
> - **Primary Holdout Score (`HOLDOUT-DTI`)**: **`0.0795`** (`95% CI [0.0594, 0.1027]` on `gems57-pooled-hide-v2`, `seed=2026`, `11,360` withheld positive pixels; **`seed=20` stability = `0.0908`**; detached `>800 m` blind `HOLDOUT-DTI` = **`0.0706`**; **`+51.9%`** over Session 1 `0.0523` and **`+215%`** over matched-collar `distance_only` `0.0252`).
> - **Zero-SGMC Concealed Piedmont Benchmark (`HOLDOUT-DTI`)**: **`0.1094`** (`95% CI [0.0908, 0.1288]` on `sgmc-piedmont-basin-v1`, `10,579` withheld concealed piedmont pixels; **zero SGMC used in features or training**; **`5.12×` Session 1 `0.0214`**, beating `GEMSDOE70 P8` `0.0854` [`0.2478` live] and `GEMSDOE32 B2` `0.0954` [`0.2778` live]).
> - **53-Repo / 950-Raster Fleet Uniqueness Gate**: Pre-placement surface `|ρ| = 0.5492 <= 0.90` (`PASS`); Final raster `|ρ| = 0.0818 <= 0.90` (`PASS`); Max 3-px dot overlap across `881` competing sparse detectors = **`62.64% <= 70.00%`** (`PASS`; **`43.17%`** vs `GEMSDOE32` `0.2778`; **`34.95%`** vs `GEMSDOE70` `0.2478`; **`10.81%`** vs Session 1 `0.0525`).
> - **GitHub Pages UI**: [`docs/index.html`](docs/index.html) (Main Dashboard & One-Click Download) · [`docs/executive-summary.html`](docs/executive-summary.html) (Executive Summary & Step-by-Step DrivenData Submission Guide).

![PLKC-DualOOF E3 Submission Map](docs/assets/plkc_submission_map.png)

---

## 1. Executive Summary & Auditable Focus-9 GEMSDOE Table

Per Parallel-Run Protocol Rule 3, every number is strictly labeled as either local **`HOLDOUT-DTI`** (with evaluator version, withheld positive pixel count, and 20 km spatial block bootstrap 95% CI) or **`ORGANIZER-CONFIRMED`** (copied from the competition prompt ledger / portal receipt; never a projection).

| Site | Downloadable `.tif` & SHA-256 | Strictly Labeled Score | Emitted Dots & Spacing | NaN / Range Status | Cross-Fleet Uniqueness | Gate Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ApartGEMSDOE1 (Session 2 — Promoted)** | [`apartgems1-plkc-dualoof-e3-20261028-4499e12f-zeros.tif`](docs/downloads/apartgems1-plkc-dualoof-e3-20261028-4499e12f-zeros.tif) (`9a2d5d67f659…`) | `HOLDOUT-DTI`: **`0.0795`** (`[0.0594, 0.1027]`, `gems57-pooled-hide-v2`, `11,360` px; `seed=20`: **`0.0908`**); Detached `>800m`: **`0.0706`**; Concealed Piedmont `HOLDOUT-DTI` (`sgmc-piedmont-basin-v1`, `10,579` px): **`0.1094`** (`[0.0908, 0.1288]`) | `37,654` (`min NN=2.83 px`, `1.28%` >=3 nbrs, `0` <=200m, `41.3%` >1.5km) | All-finite `[0,1]` (`0` NaN) | **UNIQUE** (max `62.64%` across 881 sparse / 950 total; **`43.17%`** vs `GEMSDOE32`; **`10.81%`** vs Sess 1) | **PASS — OK TO DOWNLOAD & SUBMIT** |
| **ApartGEMSDOE1 (Session 1 — Archived)** | [`apartgems1-udth-submod-e3-20261027-50e7b334-zeros.tif`](docs/downloads/archive/apartgems1-udth-submod-e3-20261027-50e7b334-zeros.tif) | `ORGANIZER-CONFIRMED`: `0.0525` · `HOLDOUT-DTI`: `0.0523` (`[0.0375, 0.0687]`) · Concealed Piedmont `HOLDOUT-DTI`: `0.0214` | `38,500` (`97.3%` >=3 nbrs crowded) | All-finite `[0,1]` | Already submitted (`0.0525` live) | **ARCHIVED — DO NOT RESUBMIT** |
| [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) | [`gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif) (`c55bafc47005…`) | `ORGANIZER-CONFIRMED` (ledger): `0.2778` · Static `HOLDOUT-DTI`: `0.0042` (`[0.0035, 0.0050]`) · Concealed Piedmont `HOLDOUT-DTI`: `0.0954` | `37,654` (`0` <=200m) | All-finite `[0,1]` | **DUPLICATE** (`100.00%` w/ `GEMSDOE36`; `43.17%` w/ Ours) | **DO NOT RESUBMIT** (H19-5 derivative) |
| [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/) | [`gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif`](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif) (`e15891020b9c…`) | `ORGANIZER-CONFIRMED` (ledger): `0.2750` · Static `HOLDOUT-DTI`: `0.0042` (`[0.0035, 0.0050]`) · Concealed Piedmont `HOLDOUT-DTI`: `0.0970` | `38,854` (`0` <=200m) | All-finite `[0,1]` | **DUPLICATE** (`97.58%` w/ `GEMSDOE27`; `43.71%` w/ Ours) | **DO NOT RESUBMIT** (H19-5 derivative) |
| [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) | [`gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif`](https://buffedlizard55-lab.github.io/GEMSDOE28/docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif) (`5556aa1438fd…`) | `ORGANIZER-CONFIRMED` (ledger): `0.2710` · Static `HOLDOUT-DTI`: `0.0294` (`[0.0247, 0.0344]`) | `37,660` (`2,353` <=200m) | `7,111,787` exterior NaNs | **DUPLICATE** (`100.00%` w/ `GEMSDOE25`; `44.05%` w/ Ours) | **DO NOT RESUBMIT** (H19-5 derivative) |
| [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/) | [`gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif`](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif) (`07b6db440535…`) | `ORGANIZER-CONFIRMED` (ledger): `0.2708` · Static `HOLDOUT-DTI`: `0.0310` (`[0.0260, 0.0363]`) | `40,199` (`2,545` <=200m) | `7,111,787` exterior NaNs | **DUPLICATE** (`100.00%` w/ `GEMSDOE25`; `44.55%` w/ Ours) | **DO NOT RESUBMIT** (H19-5 derivative) |
| [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) | [`GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif`](https://buffedlizard55-lab.github.io/GEMSDOE33/docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif) (`87f857d505e2…`) | `ORGANIZER-CONFIRMED` (ledger): `0.2632` · Static `HOLDOUT-DTI`: `0.0534` (`[0.0465, 0.0608]`) | `41,865` (`3,894` <=200m) | All-finite `[0,1]` | **DUPLICATE** (`99.71%` w/ `GEMSDOE27`; `45.27%` w/ Ours) | **DO NOT RESUBMIT** (H19-5 derivative) |
| [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/) | [`gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif`](https://buffedlizard55-lab.github.io/GEMSDOE25/docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif) (`91eae1ca42ec…`) | `ORGANIZER-CONFIRMED` (ledger): `0.2600` · Static `HOLDOUT-DTI`: `0.0930` (`[0.0793, 0.1076]`) · Concealed Piedmont `HOLDOUT-DTI`: `0.0910` | `44,090` (`6,436` <=200m) | `7,111,787` exterior NaNs | **DUPLICATE** (`100.00%` w/ `GEMSDOE30`; `45.47%` w/ Ours) | **DO NOT RESUBMIT** (H19-5 derivative) |
| [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/) | [`gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif`](https://buffedlizard55-lab.github.io/GEMSDOE30/docs/downloads/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif) (`91eae1ca42ec…`) | `ORGANIZER-CONFIRMED` (ledger): `0.2600` · Static `HOLDOUT-DTI`: `0.0930` (`[0.0793, 0.1076]`) · Concealed Piedmont `HOLDOUT-DTI`: `0.0910` | `44,090` (`6,436` <=200m) | `7,111,787` exterior NaNs | **DUPLICATE** (`100.00%` w/ `GEMSDOE25`; `45.47%` w/ Ours) | **DO NOT RESUBMIT** (H19-5 derivative) |
| [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) | [`gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif`](https://buffedlizard55-lab.github.io/GEMSDOE24/docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif) (`68d0e2e4fcc5…`) | `ORGANIZER-CONFIRMED` (ledger): `0.2477` · Static `HOLDOUT-DTI`: `0.0893` (`[0.0760, 0.1033]`) · Concealed Piedmont `HOLDOUT-DTI`: `0.0865` | `60,069` (`8,769` <=200m) | `7,111,787` exterior NaNs | **DUPLICATE** (`100.00%` w/ `GEMSDOE25`; `47.19%` w/ Ours) | **DO NOT RESUBMIT** (H19-5 derivative) |
| [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) | [`gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif`](https://buffedlizard55-lab.github.io/GEMSDOE27/docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif) (`33003374335d…`) | `ORGANIZER-CONFIRMED` (ledger): `0.2449` · Static `HOLDOUT-DTI`: `0.0888` (`[0.0756, 0.1026]`) | `61,328` (`8,875` <=200m) | `7,111,787` exterior NaNs | **DUPLICATE** (`98.02%` w/ `GEMSDOE24`; `47.93%` w/ Ours) | **DO NOT RESUBMIT** (H19-5 derivative) |

![Focus-9 Uniqueness & GEMSDOE32 Ladder](docs/assets/focus9_audit_and_uniqueness.png)

---

## 2. Deep PhD Analysis: Why `GEMSDOE32` Scored `0.2778`, Why Session 1 Scored `0.0525`, and How `H-APART-5` Advances Beyond Both

### 2.1 Exact Zero-XOR Forensic Proof of `GEMSDOE32` (`h33-h33-2-b2-zeros`: `0.2778` `ORGANIZER-CONFIRMED`)
Byte-level comparison across all `5,167,373` active footprint pixels (`evidence/focus_sites_forensic_audit.json`) proves with **zero differing pixels (`XOR = 0`)**:
1. **`GEMSDOE32_B2 (37,654 dots) == GEMSDOE25_D28 (44,090 dots) & (EDT(~existing_faults) > 2.0 px)`** (`0` XOR differing pixels).
2. **`GEMSDOE25_D28 (44,090 dots) == GEMSDOE30_D28 (44,090 dots)`** (`0` XOR differing pixels).
3. **`100.00%` of `GEMSDOE32_B2`'s `37,654` dots are an exact subset of `19GEMSDOE` `H19-5` (`121,131` solid ridge pixels, `0.1922` `ORGANIZER-CONFIRMED`)**.

Why each post-processing operation lifted the live score from `0.1922` to `0.2778`:
- **Kernel-Matched Poisson Spacing (`0.1922 -> 0.2477 -> 0.2600`)**: Under Distance-Tolerant IoU (`alpha = 0.2, beta = 0.8, R = 300 m` triangular kernel), `TP_w` evaluates a **max** over 300 m disks while `FP_w` sums **additively** (`0.2 * sum (1 - q(x))`). Thinning solid `121,131`-pixel ridges at `d = 2.8 px` (`280 m`, `44,090` dots) eliminated triple-counted false positives inside each 300 m kernel disk (`+0.0678`).
- **200 m Known-Catalogue Collar Amputation (`0.2600 -> 0.2778`)**: Because organizer evaluation masks `existing_faults.tif` (Forum Thread 11516), deleting all `6,436` `D2.8` dots within `<=200 m` of mapped faults stripped near-catalogue false positives (`+0.0178`).
- **Why Pruning `H19-5` Plateaus at `~0.278` (vs `0.3195` Benchmark / `0.4413+` Top Leaderboard)**: At `S = 0.2778`, an additional dot increases DTI iff its expected truth kernel credit exceeds `p* = 0.2 * 0.2778 / (1 - 0.8 * 0.2778) = 0.0714`. Further pruning `H19-5` cannot recover hidden faults where `H19-5`'s uncalibrated hand-crafted composites missed **concealed piedmont fronts** (downdip gravity shift `z_b cot 60°` under `>250 m` alluvium), fired on **Pleistocene Lake Lahontan (`1,330 m`) / Bonneville (`1,463/1,558 m`) shoreline benches**, or suffered **25.8% 1 m LiDAR tile-gap discontinuities**.

### 2.2 Forensic Root-Cause Post-Mortem of Session 1 (`50e7b334`: `0.0525` `ORGANIZER-CONFIRMED`) & Session 2 Repairs
Byte-level inspection of Session 1's `apartgems1-udth-submod-e3-20261027-50e7b334-zeros.tif` uncovered three compounding defects — all eliminated in Session 2:
1. **`97.30%` Kernel Blob Crowding in `src/gems57/emit.py` (Fixed -> `1.28%` Crowding, `76×` Reduction)**: Session 1's shared `greedy_allocate` iterated in static initial order without CELF max-heap re-sorting and clipped `k_self = min(E[k], 1.0) = 1.0`, collapsing the marginal bar `c * (1 - k_self) -> 0` and packing `99.37%` of dots at `NN <= 1.5 px` (`13.52` mean neighbors in `300 m`). Repairing `noisy_or_self_credit` + CELF max-heap + `min_sep_px = 2.8` enforces `min NN = 2.8284 px` across all `37,654` dots.
2. **`75%` In-Sample PU Memorization on Live Export (Fixed -> `0%` In-Sample Weight via Dual-Partition 100%-OOF)**: Unmapped faults are labeled `y = 0` in Positive-Unlabeled training. Session 1 averaged all 4 LOQO trees across the full map (`75%` in-sample `y = 0` suppression). Session 2 stitches 16 spatially buffered (`1.2 km`) models across two `45°`-offset 4-sector partitions so every live pixel is predicted `100%` out-of-fold.
3. **Zero-SGMC Concealed Piedmont Specialist + Orthometric Pluvial-Shoreline Deconfounding + Fluvial `chi/ksn` (`H-APART-5`)**: Session 2 unlocks orthometric 3DEP elevation (`zmean_m`) to suppress horizontal Lahontan/Bonneville benches, adds across-fault fluvial `Delta-chi` & `ksn` knickzones, preserves exact `NaN` semantics on 12-band 1 m LiDAR (`74.2%` interior coverage) via quantile-calibrated Dual-Regime (`M_Full` + `M_Sub`) HGBs, and adds a dedicated **Zero-SGMC Concealed Piedmont Specialist** (`b15_depth_base >= 180 m`), raising read-only Concealed Piedmont `HOLDOUT-DTI` **5.12-fold** (`0.0214 -> 0.1094`).

---

## 3. Ranked Pre-Registered Untried Geological Hypotheses (`evidence/preregistration_hypotheses.json`)

1. **`H-APART-5` (Implemented & Promoted) — Pluvial-Shoreline-Deconfounded Fluvial Chi-Ksn Tectonic Geomorphology + Dual-Regime (1m LiDAR / 10m 3DEP) Frangi Axial Vesselness + Hydrothermal/Volcanic Updip Conduit Coupling with Kernel-Spaced CELF Submodular Allocation (PLKC-DualOOF-CELF)**:
   - *Physical Transform*: Couples drainage-area-normalized channel steepness jumps (ksn) and cross-divide chi disequilibrium with de-quantized 1m LiDAR crest-toe Laplacian dipoles and 10m profile-curvature breaklines while subtracting horizontal equipotential Pleistocene Lake Lahontan (~1,330 m Sehoo) & Bonneville (~1,558 m) wave-cut shoreline benches via orthometric zmean_m along-strike elevation constancy; calibrates M_Sub across the 24.7% 1m LiDAR gap onto M_Full+M_Sub; sharpens 100-200 m fault/conduit crests via Stage-2 multi-scale Hessian Frangi tubular vesselness minus 800 m halo background; fuses survey-seam-clean updip-projected gravity/RTP contacts with hydrothermal K/Th adularia + U/Th redox + MT clay-cap edges + 2m thermal probes + volcanic vents; allocates 37,654 binary {0,1} off-collar dots via repaired CELF max-heap with noisy-OR self-credit and min_sep_px=2.8.
   - *Why Missing from USGS/INGENIOUS*: Sub-1.5 m Holocene intrabasin scarps outside 1m LiDAR strips, wave-cut pluvial shoreline mimics that obscure true oblique piedmont faults in Carson Sink/Dixie Valley/Winnemucca Lake, and hydrothermally altered / volcanic-hosted blind accommodation zones lack continuous aerial-photo scarps in existing_faults.tif.
   - *Named Non-Fault Mimics*: Pleistocene Lake Lahontan (~1,330 m) & Lake Bonneville (~1,558 m) equipotential wave-cut shoreline benches, high-drainage-area radial alluvial-fan incised washes, TIGER highway/rail embankments, and USGS GeoDAWN aeromagnetic contractor block-stitch boundaries.
   - *Expected Gain & Cost*: +0.055 to +0.080 HOLDOUT-DTI over Session 1 (0.0523 -> 0.110-0.135+) and +0.020+ on blind C_pied over GEMSDOE32 (0.0937) (Low-Medium (~8 min CPU compute on 2 cores, <1.2 GB RAM; all official public layers SHA-verified in .cache/external/)).
2. **`H-APART-6` (Pre-Registered Backlog) — 3D Multi-Altitude Potential-Field Euler Deconvolution (Structural Index N=0.5) & Upward-Continued (150 m) Magnetic Depth-Persistence Clustering**:
   - *Physical Transform*: Sliding-window 3D Euler homogeneity inversion for dipping basement contacts (N=0.5) combined with TMI_up150-to-RTP horizontal gradient survival ratio to separate deep (>300 m) basement-cutting faults from surficial volcanic float.
   - *Why Missing from USGS/INGENIOUS*: Detects buried horst/graben bounding faults beneath 300-1,500 m of undisturbed playa sediments.
   - *Named Non-Fault Mimics*: Miocene basaltic lava-flow paleochannel margins and GeoDAWN contractor flight-block boundaries.
   - *Expected Gain & Cost*: +0.004 to +0.012 HOLDOUT-DTI (Medium).
3. **`H-APART-7` (Pre-Registered Backlog) — Radiometric Uranium-Thorium Redox-Front Mobilization (U/Th, U/K) & Epithermal Adularia (K/Th) Dual-Halo Conduit Detector**:
   - *Physical Transform*: Redox-front U6+ -> U4+ precipitation (elevated U/Th) paired with Th-immobile potassium adularia enrichment (depressed Th/K) and lateral MT conductivity boundaries along fluid-mixing geothermal faults.
   - *Why Missing from USGS/INGENIOUS*: Argillic/phyllic hydrothermal clay alteration softens fault zones so topographic scarps degrade rapidly into smooth low-relief mounds.
   - *Named Non-Fault Mimics*: Unfaulted felsic rhyolite ash-flow tuffs with uniformly elevated magmatic K, U, and Th (rejected via immobile-Th ratio normalization).
   - *Expected Gain & Cost*: +0.003 to +0.008 HOLDOUT-DTI (folded into H-APART-5 E2/E3) (Low).
4. **`H-APART-8` (Pre-Registered Backlog) — NASA OPERA Sentinel-1 InSAR Vertical Subsidence & Seasonal Hydrologic Phase-Step Playa Aquifer-Baffle Detection**:
   - *Physical Transform*: Sharp transverse horizontal gradient in multi-year vertical InSAR velocity and seasonal poroelastic phase lag across clay-sealed fault gouge acting as groundwater flow barriers beneath flat playas.
   - *Why Missing from USGS/INGENIOUS*: Active evaporite playas have <0.2 m relief where annual sheetflooding erases surface fault scarps.
   - *Named Non-Fault Mimics*: Circular agricultural groundwater pumping cones of depression.
   - *Expected Gain & Cost*: +0.008 to +0.020 blind-playa DTI (external workstation next step) (High (blocked in allowlisted sandbox; official public source verified at https://asf.alaska.edu/datasets/daac/opera/)).
5. **`H-APART-9` (Pre-Registered Backlog) — NASA LP DAAC ASTER TIR Quartz/Opaline Sinter Reststrahlen (Bands 10-14) & SWIR Al-OH Argillic Alteration Mapping**:
   - *Physical Transform*: 8.6 um silica reststrahlen emissivity trough + 2.17-2.20 um kaolinite/illite/alunite SWIR absorption along silicified cryptic fault breccias and unmapped sinter aprons.
   - *Why Missing from USGS/INGENIOUS*: Cryptic silicified fault zones without Quaternary vertical scarp throw.
   - *Named Non-Fault Mimics*: Eolian quartz sand sheets and playa salt crusts.
   - *Expected Gain & Cost*: +0.005 to +0.015 DTI (external workstation next step) (Medium-High (blocked in allowlisted sandbox; official public source verified at https://lpdaac.usgs.gov/products/ast_07xtv003/)).

---

## 4. Holdout Experiments (`Budget = 3/3`), Concealed Piedmont Diagnostic & 47-Channel Leakage Canary

![Holdout Progression, Concealed Piedmont Diagnostic & Leakage Canary](docs/assets/holdout_experiments_and_canary.png)

### 4.1 Primary Spatially-Blocked Hide-and-Recover Holdout (`gems57-pooled-hide-v2`, `alpha=0.2, beta=0.8, 300 m`)

| Arm / Experiment | `HOLDOUT-DTI` (`seed=2026`, `11,360` px) | 95% Block Bootstrap CI | Detached Blind (`>800 m`) DTI | `seed=20` Stability (`11,321` px) | Key Mechanism Tested |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `zero_control` | `0.0000` | `[0.0000, 0.0000]` | `0.0000` | `0.0000` | All-zero baseline |
| `distance_only_collar2_control` | `0.0252` | `[0.0213, 0.0297]` | **`0.0000`** | `0.0260` | Proves halo rings fail completely on blind (`>800 m`) faults |
| `Session 1 Archived` (`50e7b334`, `0.0525` live) | `0.0523` | `[0.0375, 0.0687]` | `0.0332` | `0.0478` | Prior PR #12 baseline (`97.3%` kernel crowding) |
| **`E1`: `PLKC Dual-Regime Blind` (`38` ch)** | **`0.0687`** | `[0.0506, 0.0908]` | **`0.0718`** | `0.0771` | Preserved-NaN 1m LiDAR + 10m 3DEP + `chi/ksn` + 60° updip + pluvial/road deconfounders + CELF `d>=2.8` |
| **`E2`: `+ Hydro-Conduit & Anisotropy` (`44` ch)** | **`0.0725`** | `[0.0520, 0.0945]` | **`0.0729`** | `0.0787` | Adds GeoDAWN `K/Th` & `U/Th`, MT clay-cap edges, GDR #1391 springs/2m-probes/sinter/vents & 8-azimuth anisotropy |
| **`E3`: `PLKC-DualOOF-CELF Full` (Promoted)** | **`0.0795`** | **`[0.0594, 0.1027]`** | **`0.0706`** | **`0.0908`** | Adds Zero-SGMC Concealed Piedmont Specialist (`b15 >= 180 m`) + physical-gated directional tip/relay continuation (`Δ vs DistOnly = +0.0543`, 95% CI `[+0.0331, +0.0787]`) |

### 4.2 Strictly Read-Only Zero-SGMC Concealed Piedmont Benchmark (`sgmc-piedmont-basin-v1`, `10,579` px)
Across `18` live-scored peer submissions (`evidence/concealed_piedmont_benchmarks.json`), `sgmc-piedmont-basin-v1` correlates significantly with `ORGANIZER-CONFIRMED` live leaderboard DTI (`Spearman ρ = +0.5455, p = 0.0192`). Using **zero SGMC data anywhere in features, training, or calibration**, our promoted raster achieves:

| Submission | Emitted Dots | `>=3` Nbrs in `300 m` | `HOLDOUT-DTI` (`sgmc-piedmont-basin-v1`, `10,579` px) | `ORGANIZER-CONFIRMED` Live Score |
| :--- | :---: | :---: | :---: | :---: |
| `ApartGEMSDOE1` Session 1 (`50e7b334`, archived) | `38,500` | `97.30%` | `0.0214` (`[0.0156, 0.0277]`) | `0.0525` |
| `GEMSDOE27` `H31-1` (`cf8e1bbef244`) | `37,654` | `0.21%` | `0.0833` (`[0.0677, 0.1003]`) | `0.2250` |
| `GEMSDOE70` `P8-OOF38k` (`20261020`, top non-H19-5) | `37,654` | `15.10%` | `0.0854` (`[0.0706, 0.1011]`) | `0.2478` |
| `GEMSDOE32` `H33-2-B2` (`e5eb6e7e`, Focus-9 high) | `37,654` | `0.69%` | `0.0954` (`[0.0788, 0.1130]`) | `0.2778` |
| `GEMSDOE76` `PTCF-39200` (`fe5fc7dd`) | `39,200` | `3.39%` | `0.0962` (`[0.0793, 0.1137]`) | `0.2343` |
| **`ApartGEMSDOE1` Session 2 (`4499e12f`, Promoted)** | **`37,654`** | **`1.28%`** | **`0.1094` (`[0.0908, 0.1288]`)** | *Ready to submit (`PASS`)* |

---

## 5. Reproducible Autonomous CLI Commands

```bash
# 1. Autonomously download/restore & SHA-256 verify competition rasters, 10m 3DEP, chi/ksn, LiDAR & GDR #1391
bash scripts/download_competition_data.sh

# 2. Run pixel-exact Focus-9 forensic audit, Concealed Piedmont benchmark & 53-repo / 950-raster Registry Index
.venv/bin/python scripts/audit_focus_sites_and_registry.py

# 3. Execute H-APART-5 47-channel leakage canaries, <=3 LOQO experiments, 950-raster uniqueness gate & GeoTIFF build
.venv/bin/python scripts/run_apartgems_pipeline.py

# 4. Run standalone zero-human-input GeoTIFF + Uniqueness validator, regenerate figures/pages & run pytest suite
.venv/bin/python scripts/validate_submission.py docs/downloads/apartgems1-plkc-dualoof-e3-20261028-4499e12f-zeros.tif --json-out evidence/cli_validator_check.json
.venv/bin/python scripts/generate_figures.py
.venv/bin/python scripts/build_pages_and_readme.py
.venv/bin/pytest -v
```

---

## 6. Machine-Readable Parallel-Run Protocol Run Card (`evidence/run_card.json`)

```json
{
  "protocol": "GEMS Parallel-Run Protocol v1",
  "branch": "arena/eceaf9f6-apartgemsdoe1",
  "generated_utc": "2026-10-28T08:54:38.693782+00:00",
  "hypothesis": "H-APART-5 (PLKC-DualOOF-CELF): Pluvial-Shoreline-Deconfounded 1m/10m Scarp + Fluvial Chi/Ksn Knickzone + 60-deg Updip Gravity/Magnetic & Hydrothermal Conduit Dual-Regime Nested-OOF + Zero-SGMC Concealed Piedmont Specialist + CELF Noisy-OR d>=2.8 Allocation",
  "mechanism": "Combines preserved-NaN 1m LiDAR scarps (74.2% interior coverage) with quantile-calibrated 10m 3DEP slope/curvature, across-fault fluvial chi/ksn knickzones, 60-deg updip-migrated gravity/RTP-magnetic contacts, GeoDAWN K/Th & U/Th alteration, GDR #1391 thermal springs/2m-probes/sinter/vents, Stage-2 8-azimuth directional line-integrals, a dedicated zero-SGMC basin-cover specialist head (b15_depth_base >= 180 m), and fold-visible tip/relay continuation across two 45-deg-offset 4-sector 100%-OOF partitions, emitted via CELF max-heap submodular allocation at min_sep_px=2.8 (>200 m catalogue collar).",
  "named_non_fault_mimic_process": "Pleistocene Lake Lahontan (1,330 m) and Lake Bonneville/Provo (1,463 m / 1,558 m) wave-cut paleoshoreline benches, radial alluvial-fan incised washes, US Census TIGER highway/rail embankments, GeoDAWN aeromagnetic/radiometric flight-block stitching seams, and circular volcanic/erosional knobs (suppressed via orthometric pluvial-bench x zero-basement-gradient deconfounder, drainage-orthogonal alignment, TIGER road distance, acquisition_block_id seam weighting, and Stage-2 1.5 km directional anisotropy).",
  "holdout_dti": {
    "label": "HOLDOUT-DTI",
    "evaluator_version": "gems57-pooled-hide-v2",
    "split": "gems57-pooled-hide-v2 (seed=2026, buffer_px=3, 20 km spatial block bootstrap)",
    "withheld_positive_pixels": 11360,
    "dti": 0.079473,
    "ci95": [
      0.059426,
      0.10265
    ],
    "session_1_archived_holdout_dti": 0.052328,
    "detached_gt_800m_blind_dti": 0.07056,
    "seed_20_stability_dti": 0.090829,
    "experiments_progression": {
      "E1_plkc_dual_regime_blind": 0.068729,
      "E2_plkc_hydro_stage2_vessel": 0.072549,
      "E3_plkc_dualoof_celf_full": 0.079473
    }
  },
  "concealed_piedmont_holdout_dti": {
    "label": "HOLDOUT-DTI",
    "evaluator_version": "sgmc-piedmont-basin-v1",
    "note": "Strictly read-only diagnostic on concealed USGS SGMC piedmont/basin faults (>250m from catalogue, depth_to_base >= 250m); zero SGMC used in features or training.",
    "withheld_positive_pixels": 10579,
    "dti": 0.109439,
    "ci95": [
      0.090838,
      0.128807
    ],
    "vs_session_1_00525": 0.021384,
    "vs_gemsdoe70_p8_02478": 0.085443,
    "vs_gemsdoe32_b2_02778": 0.095385
  },
  "leakage_canary": {
    "features_tested": 47,
    "max_symmetric_auc": 0.76655,
    "cap": 0.9,
    "all_passed": true
  },
  "registry_uniqueness": {
    "repositories_checked": 53,
    "unique_rasters_checked": 950,
    "competing_sparse_detectors_checked": 881,
    "pre_placement_surface_max_abs_spearman": 0.54916,
    "pre_placement_nearest_peer": "GEMSDOE82::surface_h82.tif",
    "post_placement_final_max_abs_spearman": 0.08181,
    "post_placement_max_3px_overlap_all_950": 0.62644,
    "post_placement_max_3px_overlap_vs_competing": 0.62644,
    "post_placement_max_3px_symmetric_f1_all_950": 0.49029,
    "vs_gemsdoe32_02778_3px_overlap": 0.43169,
    "vs_session_1_50e7b334_3px_overlap": 0.10806,
    "vs_gemsdoe70_02478_3px_overlap": 0.3495,
    "nearest_3px_overlap_peer": "GEMSDOE91::gems91-spac-e3-20261024T183000Z-a2740c89-zeros.tif",
    "spearman_cap": 0.9,
    "overlap_3px_cap": 0.7,
    "passed": true
  },
  "raster_sha256": "9a2d5d67f65979d2054f8babd8dea3c5f516dc871ab01e3434adc74ea1838d73",
  "decoded_footprint_sha256": "4499e12f937d632f1d97de90bab80d8a297c8a159ecb8f1f583bb1627a4d0111",
  "validator_output": {
    "file": "docs/downloads/apartgems1-plkc-dualoof-e3-20261028-4499e12f-zeros.tif",
    "zip_file": "docs/downloads/apartgems1-plkc-dualoof-e3-20261028-4499e12f-zeros.zip",
    "bytes": 137227,
    "crs": "EPSG:32611",
    "shape": [
      3730,
      3292
    ],
    "transform": [
      100.0,
      0.0,
      243350.0,
      0.0,
      -100.0,
      4508550.0
    ],
    "dtype": "float32",
    "nodata": null,
    "min": 0.0,
    "max": 1.0,
    "n_nan": 0,
    "n_infinite": 0,
    "emitted_positive_pixels": 37654,
    "on_catalogue_positive_pixels": 0,
    "within_200m_collar_pixels": 0,
    "farfield_gt_1500m_pixels": 15546,
    "farfield_gt_1500m_fraction": 0.412865,
    "min_nearest_neighbor_px": 2.8284,
    "frac_ge3_neighbors_in_3px": 0.012774,
    "all_checks_passed": true
  },
  "submission_name": "apartgems1-plkc-dualoof-e3-4499e12f",
  "submission_note": "H-APART-5 PLKC-DualOOF (E3): Dual-OOF 1m/10m chi+updip+GDR1391+piedmont; CELF d>=2.8, [0,1] zeros (37654 px).",
  "submission_note_chars": 109,
  "verdict": "promote"
}
```

---

## 7. Remaining Limitations & Next-Steps Roadmap

1. **25.8% Exterior 1 m LiDAR Coverage Gap**: Although our quantile-calibrated Dual-Regime (`M_Full` + `M_Sub`) architecture eliminates sharp step-discontinuities across the `74.2% / 25.8%` 1 m LiDAR boundary, sub-meter Holocene scarps outside USGS 3DEP 1 m swaths remain limited by 10 m 3DEP vertical resolution (`~0.5–1.0 m`). Incorporating Sentinel-1 InSAR phase-gradient coherence or commercial stereo-optical DSMs outside 1 m LiDAR strips is the highest-leverage sensor addition.
2. **2D Azimuthal Dip Prior vs. Full 3D Joint Gravity-Magnetic-MT Inversion**: `udpc_*` migrates basement gradients updip using a `60°` Great Basin normal-fault dip prior scaled by `Band 15 depth_to_base_surf`. Replacing this analytic migration with 3D Euler deconvolution (`H-APART-6`, `N=0.5`) coupled to 3D magnetotelluric resistivity gradients (`H-APART-8`) can further sharpen sub-basin fault-plane geometry in asymmetric half-grabens.
3. **Subaerial Bias of Catalogue Hide-and-Recover Holdout**: Withheld segments in `gems57-pooled-hide-v2` come from `existing_faults.tif` (predominantly subaerial range-front scarps), whereas hidden INGENIOUS faults include a higher fraction of concealed basinward piedmont structures. Tracking both `gems57-pooled-hide-v2` (`0.0795` / `0.0908`) and strictly read-only `sgmc-piedmont-basin-v1` (`0.1094`) provides complementary guardrails without touching SGMC in training.

---

## 8. Standing Reference: Original Competition Task & Protocol Specification

<details>
<summary>Click to expand full standing user instructions & Parallel-Run Protocol reference</summary>

- **Competition**: DOE GEMS DrivenData Prize Challenge (`https://www.drivendata.org/competitions/306/competition-doe-gems/`, leaderboard high `0.4413`, benchmark `0.3195`, best listed GEMSDOE site `0.2778` on `GEMSDOE32`; archived Session 1 `ApartGEMSDOE1` `udth-submod-e3-20261027-50e7b334`: `0.0525`).
- **Core Deliverables**:
  1. Store prompt instructions in `README.md`, complete pending work autonomously, and download/prepare official competition data automatically (`scripts/download_competition_data.sh`, `scripts/prepare_data.py`).
  2. Deep PhD-level analysis of `GEMSDOE32` (`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`: `0.2778`) — why/how it scored `0.2778` and how to beat `0.2778` (and `0.3195`) — plus an executive summary and auditable table across `GEMSDOE24`, `GEMSDOE25`, `GEMSDOE27`, `GEMSDOE28`, `GEMSDOE30`, `GEMSDOE31`, `GEMSDOE32`, `GEMSDOE33`, and `GEMSDOE36`.
  3. Propose 3–5 untried geological hypotheses for hidden faults and geothermal vents/conduits before implementing, ranked by expected DTI gain and cost; generate a **unique** single-band `.tif` submission strictly in `[0, 1]` (preventing `"Predicted values must be in range [0, 1]"`), no footprint NaNs, matching `example_submission.tif` CRS/shape/geotransform, validated 100% automatically in code without human-inspection gates.
  4. Build a clean GitHub Pages UI (`docs/index.html`) with obvious one-click `.tif` download & automated validation status right at the top, plus an executive summary subpage (`docs/executive-summary.html`) explaining step-by-step how to submit on DrivenData, backed by verified official links.
  5. Enforce Parallel-Run Protocol: (1) Uniqueness gate (`|ρ| <= 0.90` on pre-placement surface & final raster, `<= 70%` 3-px dot overlap across fleet registry); (2) Reuse shared `evaluate_holdout.py` & `submission_writer.py` (`alpha=0.2, beta=0.8, 300 m` triangular kernel); (3) Strict score labeling (`HOLDOUT-DTI` vs `ORGANIZER-CONFIRMED`, never writing a projection as a score); (4) Single-feature leakage canary (`AUC <= 0.90`); (5) End with JSON Run Card; (6) Cap at `<= 3` experiments or `2` hours.
  6. Execute in 3 complete verification passes, open & merge PR onto `main`, and document remaining work & limitations.

</details>
