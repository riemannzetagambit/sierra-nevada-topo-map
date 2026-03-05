# Sierra Nevada Topographic Wall Map

A large-format custom topographic wall map of the Sierra Nevada from Leavitt Meadows to the Golden Trout Wilderness — roughly 170 miles north–south by 70 miles east–west — built entirely in QGIS using publicly available data sources.

**Print dimensions:** 24"×60" (1:220,000) or 36"×86" (1:150,000)
**Map rotation:** 30° from North (aligns the range axis vertically)
**Coordinate system:** EPSG:4326 (WGS 84)
**Bounding box:** 36.05°N – 38.80°N, 120.25°W – 117.50°W

> This README was written with the assistance of [Claude](https://claude.ai) (Anthropic).

---

## Table of Contents

1. [Data Sources](#data-sources)
2. [Layer Organization](#layer-organization)
3. [Basemap Generation Script](#basemap-generation-script)
4. [Aesthetics and Styling](#aesthetics-and-styling)
5. [Reproducing This Map](#reproducing-this-map)

---

## Data Sources

### Downloaded Data

These are external datasets downloaded from public sources. They are not included in this repo due to size.

| Layer | Source | Download Link | What to Download | QGIS Import Notes | Filters Used | Layer Properties / Notes |
|---|---|---|---|---|---|---|
| **Sierra Crests** | USGS GNIS | [GNIS Download](https://www.usgs.gov/tools/geographic-names-information-system-gnis) | `DomesticNames_CA_Text.zip` (California) | Add Delimited Text Layer; pipe `\|` delimiter; `prim_long_dec` as X, `prim_lat_dec` as Y; EPSG:4326 | Custom name-based filter for named crests along the Sierra crest line | Adobe Caslon Pro Bold, 1000 map units, `#4e4e4e`; wrap char `\|` |
| **Valleys, Meadows, Canyons, Basins — Major** | USGS GNIS | (same file as above) | (same file) | (same import as above) | Filtered by `feature_class` (Basin, Valley, Flat, etc.) for major named features: Tuolumne Meadows, Kings Canyon, Yosemite Valley, Kern Canyon, Evolution Valley/Basin, Humphreys Basin, Dusy Basin, Palisade Basin, etc. | Palatino Bold, 14pt, `#442314`; wrap char `\|` |
| **Valleys, Meadows, Canyons, Basins — Minor** | USGS GNIS | (same file) | (same file) | (same import) | Same feature classes, filtered for secondary named features | Palatino Bold, 3.5mm, `#442314`; wrap char `\|` |
| **Passes — Tier 1 (Highway)** | USGS GNIS | (same file) | (same file) | (same import) | `feature_class = 'Gap'`; manually split: Sonora, Tioga, Ebbetts, Carson, Monitor | Palatino Bold, 1500 map units, `#395734` (dark green); cross marker size 10 |
| **Passes — Tier 2 (JMT/PCT)** | USGS GNIS | (same file) | (same file) | (same import) | `feature_class = 'Gap'`; Donohue, Island, Silver, Selden, Muir, Mather, Pinchot, Glen, Forester, Cottonwood | Palatino Bold, 750 map units, `#395734`; cross marker size 3 |
| **Passes — Tier 3 (East Side)** | USGS GNIS | (same file) | (same file) | (same import) | `feature_class = 'Gap'`; Kearsarge, Bishop, Piute, Mono, McGee, Shepherd, Army, Taboose, Sawmill, Baxter | Palatino Bold, 750 map units, `#395734`; cross marker size 3 |
| **Summits — Major (~60 peaks)** | USGS GNIS | (same file) | (same file) | (same import) | `feature_class = 'Summit'`; bounding box `prim_lat_dec BETWEEN 36.05 AND 38.80`, `prim_long_dec BETWEEN -120.25 AND -117.90`; hand-curated list of ~60 most significant summits | Palatino Regular, 20pt, `#000000`; black triangle size 7; elevations shown |
| **Summits — Notable** | USGS GNIS | (same file) | (same file) | (same import) | Same bounding box; secondary tier peaks excluded from Major layer | Palatino Regular, 14pt, `#2d2d2d`; dark gray triangle size 4 |
| **Summits — All** | USGS GNIS | (same file) | (same file) | (same import) | Same bounding box; remaining summits with name + `feature_id` exclusion list to remove clutter and duplicates (e.g. `feature_id NOT IN (268341, 267671)` for duplicate Mt Tom / Mt Stanford) | Palatino Regular, 2.75mm, `#4a4a4a`; gray triangle size 2; one tier per peak via exclusion filters |
| **State & Federal Roads** | US Census TIGER/Line | [TIGER Roads Download](https://www.census.gov/cgi-bin/geo/shapefiles/index.php) | Select "All Roads" by county: **Fresno, Inyo, Madera, Mono, Tulare, Tuolumne** | Add Vector Layer | `"RTTYP" IN ('S', 'U')` for state and US routes | Open Sans Bold, 4mm, `#a47158`; line `#a47158` width 0.75mm; buffer 0.5 near-white; label expression: `'CA-' \|\| replace("FULLNAME", 'State Rte ', '')` |
| **County Roads (Trailhead Access)** | US Census TIGER/Line | (same source) | (same counties) | Add Vector Layer | Extended `FULLNAME` pattern filter for named trailhead access roads (Tioga, Kaiser Pass, Mineral King, Whitney Portal, Onion Valley, Reds Meadow, etc.) plus `fid` inclusions/exclusions | Open Sans Bold, 4mm, `#a47158`; line `#a47158` width 0.75mm; buffer 0.5 near-white. **NULL handling:** `("FULLNAME" IS NULL OR "FULLNAME" NOT LIKE '...')` required. |
| **Rivers — HUC 1803 (Tulare-Kern)** | USGS NHD | [NHD S3 Download](https://prd-tnm.s3.amazonaws.com/index.html?prefix=StagedProducts/Hydrography/NHD/HU4/GDB/) | `NHD_H_1803_HU4_GDB.zip` | Extract `.gdb`; add `NHDFlowLine` and `NHDWaterbody` layers | FlowLine: `"visibilityfilter" >= 250000 OR ("gnis_name" IS NOT NULL AND "gnis_name" != '')` | **Two layers per HUC:** (1) Display: line `#4a7fb0` width 0.46mm, labels off; (2) Label: Palatino Italic, `#2b5a8a`, curved, buffer 0.5 `#fafafa`, dissolved by `gnis_name`. |
| **Rivers — HUC 1804 (San Joaquin)** | USGS NHD | (same S3 link) | `NHD_H_1804_HU4_GDB.zip` | (same) | (same filter) | (same dual-layer approach and styling) |
| **Rivers — HUC 1809 (Eastern Sierra)** | USGS NHD | (same S3 link) | `NHD_H_1809_HU4_GDB.zip` | (same) | (same filter) | Same styling; **label repeats allowed** for Owens River due to length along map axis |
| **Rivers — HUC 1605 (Walker River)** | USGS NHD | (same S3 link) | `NHD_H_1605_HU4_GDB.zip` | (same) | (same filter) | (same dual-layer approach and styling) |
| **Lakes** | USGS NHD | (same S3 link) | (from same `.gdb` files — `NHDWaterbody` layer) | (same) | `"gnis_name" IS NOT NULL AND "gnis_name" != '' AND "areasqkm" > 0.2 AND "ftype" NOT IN (378, 466)` — excludes glaciers and swamp/marsh | Palatino Regular, 5mm, `#2b5a8a`; fill `#c3e8ff` (light blue), no stroke. Labels only for `areasqkm > 0.5`. Set as label **obstacles**. |
| **DEM Tiles** | USGS 3DEP 1/3 arc-second | [3DEP via S3](https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/current/) | 13 tiles: n36w118, n37w118–w121, n38w118–w121, n39w118–w121. See [download script](#step-1--dem-merge-and-clip). | Processed via Python script (not loaded directly in QGIS) | N/A | Merged and clipped to bounding box by `scripts/sierra_basemap_generation.py` |
| **NLCD Land Cover** | MRLC | [MRLC Data Download](https://www.mrlc.gov/data) | Annual NLCD Land Cover 2024 | Processed via Python script (not loaded directly in QGIS) | N/A | Used for vegetation tinting in basemap blend. See [NLCD Vegetation Tinting](#step-6--nlcd-vegetation-tinting-optional). |

### Custom Layers (Included in This Repo)

These are hand-created layers included in `shapefiles_geopackages/topographic_features/`. They have no external download source.

| Layer | Files | Description | Layer Properties / Notes |
|---|---|---|---|
| **National Park Names** | `national_park_names.*` | Hand-digitized point/polygon layer for Yosemite, Sequoia, Kings Canyon, Devils Postpile | Palatino Bold, 20pt, `#264224` (dark forest green); wrap char `\|` |
| **Wilderness Names — Major** | `major_wilderness_names.*` | Major wilderness areas: Yosemite, Emigrant, Ansel Adams, Hoover, Mokelumne, Muir, Sequoia–Kings Canyon, Golden Trout, South Sierra, etc. | Palatino Bold, 14pt, `#7f2b0a` (rusty brown); wrap char `\|` |
| **Wilderness Names — Minor** | `minor_wilderness_names.*` | Smaller or less prominent wilderness areas including Dinkey Lakes, Jenny Lakes, Monarch, etc. | Palatino Bold, 8pt, `#7f2b0a`; wrap char `\|` |
| **Valleys/Meadows/Canyons/Basins — Major** | `major_basins_valleys_meadows_canyons.*` | Major named features custom-placed for better positioning than GNIS coordinates | Palatino Bold, 14pt, `#442314` (dark brown); wrap char `\|` |
| **Valleys/Meadows/Canyons/Basins — Minor** | `minor_basins_valleys_meadows_canyons.*` | Secondary named features | Palatino Bold, 3.5mm, `#442314`; wrap char `\|` |
| **Sierra Subranges and Divides** | `sierra_ranges_and_divides.*` | LineString layer (EPSG:4326) with named ranges and divides: Cathedral Range, Clark Range, Ritter Range, Sawtooth Ridge, Silver Divide, Mono Divide, Le Conte Divide, Goddard Divide, White Divide, Black Divide, The Palisades, Monarch Divide, Great Western Divide, Kings-Kaweah Divide, Kings-Kern Divide | Adobe Caslon Pro Bold, 16pt, `#462e0c` (dark chocolate); curved placement along line; red guide line `#ff0010` 0.26mm |
| **Sierra Crests** | `crests.*` | Custom point or line layer for named crests | Adobe Caslon Pro Bold, 1000 map units, `#4e4e4e`; wrap char `\|` |
| **The Lake of Power** | `the_lake_of_power.*` | Custom feature | Palatino Regular, 2mm, `#2b5a8a`; wrap char `\|` |
| **Custom Peak Names** | `custom_peaks_list.csv` | Climbing objectives not in GNIS: Venacher Needle, Mt Bandaloop, Adair Buttress, The Bowmaiden, Saber Ridge, The Obelisk, Kettle Dome, Silver Turret, Cobra Turret, Oyster Peak, Whaleback, The Minarets | Palatino Regular, 2.75mm, `#4a4a4a`; gray triangle size 2. CSV import: comma delimiter, `longitude` as X, `latitude` as Y, EPSG:4326. "The Minarets" replaces the GNIS entry for better label placement. |

---

## Layer Organization

### Layer Stack Order (top to bottom in QGIS)

1. Custom peak names (CSV)
2. Major summits (GNIS)
3. Notable summits (GNIS)
4. All summits (GNIS)
5. Passes — Tier 1 (highway passes)
6. Passes — Tier 2 (JMT/PCT passes)
7. Passes — Tier 3 (east-side passes)
8. Sierra crests (custom shapefile)
9. Sierra subranges and divides (custom shapefile)
10. National Park names (custom)
11. Wilderness names — major (custom)
12. Wilderness names — minor (custom)
13. Valleys/Meadows/Canyons/Basins — major (custom)
14. Valleys/Meadows/Canyons/Basins — minor (custom)
15. Roads — state and federal (TIGER)
16. Roads — county trailhead access (TIGER)
17. Lakes (NHDWaterbody)
18. River label layers — one per HUC (dissolved NHDFlowLine, labels only, no symbology)
19. River display layers — one per HUC (original NHDFlowLine, symbology only, no labels)
20. Contour lines — 2000' bold
21. Contour lines — 500' regular
22. Base map raster (hillshade blended with hypsometric tints + NLCD vegetation layer)

### Key Organizational Decisions

**River label/display split.** NHDFlowLine data is duplicated per HUC. The original layer handles symbology only (labels off). A copy dissolved on `gnis_name` handles labels only (symbology off). Without dissolving, rivers whose geometry is split into dozens of segments (common in NHD) produce duplicate floating labels. The dissolved copy gives QGIS a single geometry per named river to anchor one label to.

**Three-tier peak layers.** Separate layers for major, notable, and all peaks allow different symbol sizes, triangle styles, and label styling without complex data-defined overrides across hundreds of features. Features are assigned to exactly one layer via filter exclusion lists.

**Three-tier pass layers.** Same rationale as peaks: Tier 1 highway passes get very large labels; Tier 2 JMT/PCT passes get large labels; Tier 3 east-side passes get medium labels.

**Label sizes in mm, not map units.** All label sizes are specified in mm so they render correctly in both the map canvas and Print Layout, regardless of zoom level.

**Label rotation for tilted layout.** The map is rotated ~30° from north. Labels use a data-defined rotation of `@map_rotation * -1` to stay horizontal in the printed layout.

**Lake obstacle setting.** Lake polygons are flagged as label obstacles, preventing river and stream labels from being placed inside lake boundaries (e.g., prevents a label from floating inside Simpson Meadow reservoir).

**Blend mode rendering caveat.** The hillshade layer uses Multiply blend mode at ~45% opacity over hypsometric tints. Blend modes may not render correctly in PDF export from QGIS. Export as raster (TIFF or PNG at 300 DPI) or pre-render the blended base as a GeoTIFF using the included Python script.

**QGIS auxiliary storage for label pinning.** Individual labels can be manually dragged to a better position using QGIS's label pin tool. This writes position offsets to the layer's auxiliary storage. If labels stop responding to drag, check that `auxiliary_storage_labeling_positionx` and `_positiony` are not set in the label placement data-defined properties — clear those fields to re-enable interactive pinning.

---

## Basemap Generation Script

**Script:** `scripts/sierra_basemap_generation.py`
**Dependencies:** `rasterio`, `numpy`, `scipy`, `matplotlib`, `shapely` (and optionally `fiona` for GeoPackage output, `gdal-bin` for faster contours)

```bash
pip install rasterio numpy scipy matplotlib shapely fiona
```

The script runs a six-step pipeline. Steps can be run individually to avoid re-processing slow steps during color iteration:

```bash
# Run full pipeline
python3 scripts/sierra_basemap_generation.py

# Re-run only color steps (fast, useful while tuning)
python3 scripts/sierra_basemap_generation.py hypsometric blend nlcd

# Re-run only NLCD tinting
python3 scripts/sierra_basemap_generation.py nlcd
```

### Step 1 — DEM Merge and Clip

**DEM Source:** [USGS 3DEP 1/3 arc-second (~10m resolution)](https://www.usgs.gov/3d-elevation-program)
**Download URL pattern:**
```
https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/current/{tile}/USGS_13_{tile}.tif
```

**Tiles used** (covering the bounding box 36.05–38.80°N, 120.25–117.50°W):

```bash
for tile in n36w118 n37w118 n37w119 n37w120 n38w118 n38w119 n38w120 n39w118 n39w119 n39w120 n37w121 n38w121 n39w121; do
  if [ ! -f ./geotiffs/USGS_13_${tile}.tif ]; then
    curl -o ./geotiffs/USGS_13_${tile}.tif \
      "https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/current/${tile}/USGS_13_${tile}.tif"
  fi
done
```

Tiles are merged and clipped to the project bounding box using `rasterio.merge` and `rasterio.mask`. Output: `sierra_basemap_output/sierra_merged_dem.tif`.

### Step 2 — Hillshade

Computed using Horn's method (numpy gradient approximation). Parameters:

| Parameter | Value |
|---|---|
| Azimuth | 315° (northwest light) |
| Altitude | 45° |
| Z-factor | 1.0 (no vertical exaggeration) |
| Hillshade blend opacity | 0.45 |

### Step 3 — Hypsometric Tints

Elevation-to-color ramp (DEM in meters, interpolated):

| Elevation (m) | ~Elevation (ft) | RGB | Description |
|---|---|---|---|
| 300 | ~1,000 | (228, 232, 224) | Cool pale gray-green |
| 900 | ~3,000 | (225, 230, 222) | Cool pale gray |
| 1220 | ~4,000 | (222, 228, 218) | Barely green |
| 1520 | ~5,000 | (218, 226, 214) | Hint of sage |
| 1830 | ~6,000 | (210, 222, 206) | Muted sage (peak green) |
| 2130 | ~7,000 | (208, 220, 204) | Muted sage |
| 2440 | ~8,000 | (216, 224, 212) | Fading sage |
| 2745 | ~9,000 | (225, 226, 220) | Pale cool cream |
| 3050 | ~10,000 | (251, 251, 249) | Near white |
| 3200 | ~10,500 | (254, 254, 253) | Essentially white |
| 3500+ | ~11,500+ | (255, 255, 255) | White |

The ramp aims for a muted, cool USGS-adjacent look — not the warm browns of traditional hypsometric maps. Forest belt elevations get a subtle sage-green; high alpine terrain fades to white.

### Step 4 — Hillshade Blend

Hillshade is blended with the hypsometric ramp using a multiply blend at 45% opacity:

```
result = hypsometric × (1 - 0.45 + 0.45 × hillshade)
```

### Step 5 — Contour Lines

Generated from the merged DEM (converted to feet). Uses `gdal_contour` if available, otherwise falls back to matplotlib.

| Layer | Interval |
|---|---|
| Regular contours | 500 ft |
| Bold index contours | 2000 ft |

### Step 6 — NLCD Vegetation Tinting (Optional)

**Source:** [MRLC — Annual NLCD Land Cover 2024](https://www.mrlc.gov/data) (EPSG:5070 Albers Equal Area, reprojected on the fly)

| NLCD Class(es) | Description | Tinting Treatment |
|---|---|---|
| 41, 42, 43 | Forest (Deciduous/Evergreen/Mixed) | Tiny green enhancement: R×0.97, G×1.01, B×0.97 |
| 52 | Shrub/Scrub | Push toward cool beige (235, 232, 222) at up to 55% blend |
| 71 | Grassland/Herbaceous (meadows) | Subtle green: R×0.96, G×1.02, B×0.96 |
| 31 | Barren (rock, sand, scree) | Push toward cool beige at up to 65% blend |
| 21–24 | Developed areas | Push toward warm gray (238, 232, 222) at up to 50% blend |
| 11, 12 | Open water / Ice | No tinting |

Tinting is graduated by elevation: full strength below ~7,000 ft (2,130m), linearly fading to zero above ~9,500 ft (2,900m).

---

## Aesthetics and Styling

*Extracted from the QGIS project file.*

### Per-Layer Typography and Symbology

| Layer | Font | Size | Label Color | Symbol | Notes |
|---|---|---|---|---|---|
| **Major Summits** | Palatino Regular | 20 pt | `#000000` (black) | Black triangle, size 7 | Elevations shown |
| **Notable Summits** | Palatino Regular | 14 pt | `#2d2d2d` (dark gray) | Dark gray triangle, size 4 | — |
| **All Summits** | Palatino Regular | 2.75 mm | `#4a4a4a` (gray) | Gray triangle, size 2 | — |
| **Custom Peaks** | Palatino Regular | 2.75 mm | `#4a4a4a` (gray) | Gray triangle, size 2 | Same styling as All Summits |
| **Passes — Tier 1 (Highway)** | Palatino Bold | 1500 map units | `#395734` (dark green) | Cross marker, size 10 | — |
| **Passes — Tier 2 (JMT/PCT)** | Palatino Bold | 750 map units | `#395734` (dark green) | Cross marker, size 3 | — |
| **Passes — Tier 3 (East Side)** | Palatino Bold | 750 map units | `#395734` (dark green) | Cross marker, size 3 | — |
| **Sierra Crests** | Adobe Caslon Pro Bold | 1000 map units | `#4e4e4e` (gray) | — | Wrap character: `\|` |
| **Sierra Ranges/Divides** | Adobe Caslon Pro Bold | 16 pt | `#462e0c` (dark chocolate) | Red line `#ff0010`, 0.26mm | Curved placement along line geometry |
| **National Park Names** | Palatino Bold | 20 pt | `#264224` (dark forest green) | — | Wrap character: `\|` |
| **Wilderness — Major** | Palatino Bold | 14 pt | `#7f2b0a` (rusty brown) | — | Wrap character: `\|` |
| **Wilderness — Minor** | Palatino Bold | 8 pt | `#7f2b0a` (rusty brown) | — | Wrap character: `\|` |
| **Basins/Valleys — Major** | Palatino Bold | 14 pt | `#442314` (dark brown) | — | Wrap character: `\|` |
| **Basins/Valleys — Minor** | Palatino Bold | 3.5 mm | `#442314` (dark brown) | — | Wrap character: `\|` |
| **State & Federal Roads** | Open Sans Bold | 4 mm | `#a47158` (warm brown) | Line `#a47158`, width 0.75mm | Buffer: 0.5 near-white |
| **County Roads** | Open Sans Bold | 4 mm | `#a47158` (warm brown) | Line `#a47158`, width 0.75mm | Buffer: 0.5 near-white |
| **Rivers (display)** | — | — | — | Line `#4a7fb0` (blue), width 0.46mm | Labels off; symbology only |
| **Rivers (label layers)** | Palatino Italic | data-defined | `#2b5a8a` (dark blue) | — | Labels only; symbology off; buffer 0.5 near-white; curved placement |
| **Lakes** | Palatino Regular | 5 mm | `#2b5a8a` (dark blue) | Fill `#c3e8ff` (light blue) | Labels only for `areasqkm > 0.5`; set as obstacles |
| **The Lake of Power** | Palatino Regular | 2 mm | `#2b5a8a` (dark blue) | — | Wrap character: `\|` |
| **Contours — 2000'** | Palatino Regular | 7 pt | `#6b5a48` (brown) | Line `#6b5a48`, width 0.2mm | Buffer: 0.35 near-white |
| **Contours — 500'** | (no labels) | — | — | Line `#8a7560`, width 0.1mm | — |

### Print Configuration

| Setting | Value |
|---|---|
| Page size | 24"×60" or 36"×86" |
| Scale | 1:220,000 (2'×5') or 1:150,000 (3'×7') |
| Map rotation | 30° from North |
| Print resolution | 300 DPI |
| Proofing resolution | 150 DPI |

### Blend Mode Notes

- Hillshade: Multiply blend mode at 45% opacity over hypsometric tints
- NLCD: Applied as a pre-rendered GeoTIFF (script Step 6) rather than a live QGIS blend, to avoid export artifacts

### Color Palette Summary

| Element | Color | Hex |
|---|---|---|
| Peak labels (major) | Black | `#000000` |
| Peak labels (notable/all) | Dark gray | `#2d2d2d` / `#4a4a4a` |
| Pass labels | Dark green | `#395734` |
| National Park labels | Dark forest green | `#264224` |
| Wilderness labels | Rusty brown | `#7f2b0a` |
| Basin/Valley/Meadow labels | Dark brown | `#442314` |
| Range/Divide labels | Dark chocolate | `#462e0c` |
| Crest labels | Gray | `#4e4e4e` |
| Road labels + lines | Warm brown | `#a47158` |
| River labels | Dark blue | `#2b5a8a` |
| River lines | Blue | `#4a7fb0` |
| Lake fill | Light blue | `#c3e8ff` |
| Lake labels | Dark blue | `#2b5a8a` |
| Contour lines (2000') | Brown | `#6b5a48` |
| Contour lines (500') | Light brown | `#8a7560` |
| Label buffers (roads, rivers, contours) | Near-white | `#fafafa` |

---

## Reproducing This Map

1. Download DEM tiles (bash script in [Step 1](#step-1--dem-merge-and-clip))
2. Download NLCD 2024 land cover from [mrlc.gov](https://www.mrlc.gov/data) and update `NLCD_PATH` in the script
3. Run `scripts/sierra_basemap_generation.py` to produce the base raster layers and contours
4. Download GNIS `DomesticNames_CA_Text.zip` from [USGS GNIS](https://www.usgs.gov/tools/geographic-names-information-system-gnis) and import as a delimited text layer
5. Download NHD Full Resolution Geodatabases for [HUC 1803, 1804, 1809, and 1605](https://prd-tnm.s3.amazonaws.com/index.html?prefix=StagedProducts/Hydrography/NHD/HU4/GDB/)
6. Download TIGER/Line road shapefiles for Fresno, Inyo, Madera, Mono, Tulare, and Tuolumne counties from [Census TIGER](https://www.census.gov/cgi-bin/geo/shapefiles/index.php)
7. Build layers in QGIS following the [Layer Organization](#layer-organization) section
8. Add `custom_peaks_list.csv` as a delimited text layer for climbing objectives not in GNIS
9. Copy custom shapefiles from `shapefiles_geopackages/topographic_features/` into your QGIS project
