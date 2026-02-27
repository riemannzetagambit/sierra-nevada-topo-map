# Sierra Nevada Topographic Wall Map

A large-format custom topographic wall map of the Sierra Nevada from Leavitt Meadows to the Golden Trout Wilderness — roughly 170 miles north–south by 70 miles east–west — built entirely in QGIS using publicly available data sources.

**Print dimensions:** 24"×60" (1:220,000) or 36"×86" (1:150,000)
**Map rotation:** 30° from North (aligns the range axis vertically)
**Coordinate system:** EPSG:4326 (WGS 84)
**Bounding box:** 36.05°N – 38.80°N, 120.25°W – 117.50°W

---

## Table of Contents

1. [Data Sources](#data-sources)
2. [Layer Organization](#layer-organization)
3. [Basemap Generation Script](#basemap-generation-script)
4. [Aesthetics and Styling](#aesthetics-and-styling)

---

## Data Sources

### 1. Sierra Crests (GNIS)

**Source:** [USGS Geographic Names Information System (GNIS)](https://www.usgs.gov/tools/geographic-names-information-system-gnis)
**File:** `DomesticNames_CA_Text.zip`
**Import:** Layer → Add Delimited Text Layer, pipe `|` delimiter, `prim_long_dec` as X, `prim_lat_dec` as Y, EPSG:4326
**Filter:** Custom subset of the GNIS dataset filtered by feature name to include named crests along the Sierra Nevada crest line.

---

### 2. National Park Names (Custom Layer)

Hand-digitized point or polygon layer created within QGIS. Labels placed manually. No external download — covers Yosemite, Sequoia, Kings Canyon, and Devils Postpile.

---

### 3. Wilderness Names (Custom Layer)

Major and minor wilderness areas labeled as a custom layer. Includes (among others): Yosemite, Emigrant, Ansel Adams, Hoover, Mokelumne, Muir, Dinkey Lakes, Sequoia–Kings Canyon, Golden Trout, South Sierra, and Jenny Lakes. Hand-placed labels; no external download.

---

### 4. Valleys, Meadows, Canyons, and Basins (GNIS)

**Source:** USGS GNIS — `DomesticNames_CA_Text.zip` (same file as above)
**Filter:** Filtered by `feature_class` for Basin, Valley, Flat (meadow), Canyon, and similar classes. Split into two layers (major and minor) for label size differentiation. Key named features include Tuolumne Meadows, Kings Canyon, Yosemite Valley, Kern Canyon, Evolution Valley, Evolution Basin, Humphreys Basin, Dusy Basin, Palisade Basin, and others.

---

### 5. Sierra Subranges and Divides (Custom Shapefile)

**Created manually:** Layer → Create Layer → New Shapefile Layer (LineString, EPSG:4326), field `name` (Text, 100 chars).
Named features include: Cathedral Range, Clark Range, Ritter Range, Sawtooth Ridge, Silver Divide, Mono Divide, Le Conte Divide, Goddard Divide, White Divide, Black Divide, The Palisades, Monarch Divide, Great Western Divide, Kings-Kaweah Divide, Kings-Kern Divide.
**Label note:** Wrap-on-character `|` used as a delimiter for multi-line labels (set under "Wrap on character" in QGIS label settings).

---

### 6. Passes — Major / Minor / East Side (GNIS)

**Source:** USGS GNIS — `DomesticNames_CA_Text.zip`
**Filter:** `feature_class = 'Gap'`
Split into three tiers for visual hierarchy:

- **Tier 1 — Trans-Sierra highway passes** (very large labels): Sonora, Tioga, Ebbetts, Carson, Monitor
- **Tier 2 — JMT/PCT passes** (large labels): Donohue, Island, Silver, Selden, Muir, Mather, Pinchot, Glen, Forester, Cottonwood
- **Tier 3 — East-side access passes** (medium labels): Kearsarge, Bishop, Piute, Mono, McGee, Shepherd, Army, Taboose, Sawmill, Baxter

---

### 7. Sierra Summits — Major / Notable / All (GNIS)

**Source:** USGS GNIS — `DomesticNames_CA_Text.zip`
**Filter:** `feature_class = 'Summit'`, bounding box `prim_lat_dec BETWEEN 36.05 AND 38.80`, `prim_long_dec BETWEEN -120.25 AND -117.90`
Split into three layers:

- **Major peaks (~60 peaks):** Most significant summits; large black triangle symbols and large Palatino labels. Elevations shown.
- **Notable peaks:** Secondary tier; medium styling.
- **All peaks:** Remaining summits within the bounding box, with a name-based and `feature_id`-based exclusion list to prevent clutter and remove duplicate/misplaced entries (e.g., `feature_id NOT IN (268341, 267671)` removes a duplicate Mt Tom and Mt Stanford).

Peaks are each assigned to exactly one layer via exclusion filters, so no peak appears twice.

---

### 8. Custom Peak Names (Custom CSV Layer)

Peaks not well-represented in GNIS — chiefly technical climbing objectives.
**File:** `custom_peaks_list.csv` (included in this repo)
**Import:** Layer → Add Delimited Text Layer, comma delimiter, `longitude` as X, `latitude` as Y, EPSG:4326

| Name | Longitude | Latitude |
|---|---|---|
| Venacher Needle | -118.4755 | 36.9997 |
| Mt Bandaloop | -119.4292 | 37.9917 |
| Adair Buttress | -119.4068 | 37.6918 |
| The Bowmaiden | -119.4875 | 37.8626 |
| Saber Ridge | -118.5703 | 36.5958 |
| The Obelisk | -118.8521 | 36.9073 |
| Kettle Dome | -118.7861 | 36.9493 |
| Silver Turret | -118.7570 | 36.8841 |
| Cobra Turret | -118.7544 | 36.8993 |
| Oyster Peak | -118.7356 | 37.0543 |
| Whaleback | -118.5311 | 36.6310 |
| The Minarets | -119.1682 | 37.6569 |

"The Minarets" replaces the GNIS 'Minarets' entry for better label placement.

---

### 9. Major State and Federal Roads (TIGER)

**Source:** [US Census Bureau TIGER/Line Shapefiles — Roads](https://www.census.gov/cgi-bin/geo/shapefiles/index.php)
Select "All Roads" by county. Counties used: Fresno, Inyo, Madera, Mono, Tulare, Tuolumne.
**Filter:** `"RTTYP" IN ('S', 'U')` — state routes and US routes only.
**Label expression:** `'CA-' || replace("FULLNAME", 'State Rte ', '')` and equivalent for US routes.

---

### 10. County Roads — Trailhead Access Roads (TIGER)

**Source:** Same TIGER county road files as above (Fresno, Inyo, Madera, Mono, Tulare, Tuolumne).
**Filter:** Extended filter matching named forest and trailhead access roads by `FULLNAME` pattern — Tioga Road, Kaiser Pass Road, Mineral King Road, Whitney Portal Road, Onion Valley Road, Reds Meadow Road, and others — plus specific `fid` inclusions/exclusions to handle road-segment quirks.
**Critical NULL-handling note:** TIGER's `FULLNAME` field contains NULL values. Exclusion filters must use the pattern `("FULLNAME" IS NULL OR "FULLNAME" NOT LIKE '%Mineral King Rd Trl%')` — a plain `NOT LIKE` without the NULL guard will silently drop NULL-named roads.
Label visibility filtered separately to avoid labeling every connector segment.

---

### 11. Rivers and Water Bodies (NHD)

**Source:** [USGS National Hydrography Dataset (NHD) — Full Resolution Geodatabases](https://www.usgs.gov/national-hydrography/access-national-hydrography-products)
HUC regions used:

| HUC | Name |
|---|---|
| 1803 | Tulare-Kern |
| 1804 | San Joaquin |
| 1809 | Eastern Sierra / Owens |
| 1605 | Walker River / Upper Great Basin |

Layers extracted from each geodatabase: `NHDFlowLine` (rivers and streams) and `NHDWaterbody` (lakes, reservoirs, glaciers).

**Rivers (NHDFlowLine):**
Filter: `"visibilityfilter" >= 250000 OR ("gnis_name" IS NOT NULL AND "gnis_name" != '')`
Label size data-defined by `visibilityfilter` value (9–14pt).

Each HUC's flowline data is loaded as **two separate layers**:
1. **Display layer** (original `NHDFlowLine`): renders river symbology; labels turned OFF.
2. **Label layer** (NHDFlowLine dissolved by `gnis_name`): renders labels only; symbology turned OFF.

Dissolving by name eliminates duplicate labels on rivers whose geometry is split across many segments (e.g., Fish Creek, Mono Creek). Exception: HUC 1809 (Owens River) uses unrestricted label repeats given the river's length along the map axis.

**Lakes (NHDWaterbody):**
Filter: `"gnis_name" IS NOT NULL AND "gnis_name" != '' AND "areasqkm" > 0.2 AND "ftype" NOT IN (378, 466)` — excludes glaciers (`ftype = 378`) and swamp/marsh (`ftype = 466`).
Fill: `#2b5a8a`, no stroke. Labels visible only for `areasqkm > 0.5`.
Lake polygons set as label **obstacles** to prevent river labels from rendering inside lake boundaries.

**Glaciers (NHDWaterbody):**
Filter: `"ftype" = 378`. White fill (`#FFFFFF`), no border — rendered as a separate layer above lakes.

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
8. Sierra subranges and divides (custom shapefile)
9. National Park names (custom)
10. Wilderness names — major (custom)
11. Wilderness names — minor (custom)
12. Valleys/Meadows/Canyons/Basins — major (GNIS)
13. Valleys/Meadows/Canyons/Basins — minor (GNIS)
14. Roads — state and federal (TIGER)
15. Roads — county trailhead access (TIGER)
16. Glaciers (NHDWaterbody, white fill)
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

**Blend mode rendering caveat.** The hillshade layer uses Multiply blend mode at ~45–70% opacity over hypsometric tints. Blend modes may not render correctly in PDF export from QGIS. Export as raster (TIFF or PNG at 300 DPI) or pre-render the blended base as a GeoTIFF using the included Python script.

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

**DEM Source:** [USGS 3DEP 1/3 arc-second (approximately 10m resolution)](https://www.usgs.gov/3d-elevation-program)
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

Output: `sierra_basemap_output/sierra_hillshade.tif`

### Step 3 — Hypsometric Tints

Elevation-to-color ramp (EPSG:4326 DEM in meters):

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
| 3500 | ~11,500 | (255, 255, 255) | White |
| 4420 | ~14,500 | (255, 255, 255) | White |

The ramp aims for a muted, cool USGS-adjacent look — not the warm browns of traditional hypsometric maps. Forest belt elevations get a subtle sage-green; high alpine terrain fades to white.

Output: `sierra_basemap_output/sierra_hypsometric.tif`

### Step 4 — Hillshade Blend

Hillshade is blended with the hypsometric ramp using a multiply blend at 45% opacity:

```
result = hypsometric × (1 - 0.45 + 0.45 × hillshade)
```

Output: `sierra_basemap_output/sierra_basemap.tif`

### Step 5 — Contour Lines

Generated from the merged DEM (converted to feet). Uses `gdal_contour` if available on PATH, otherwise falls back to matplotlib. Output is GeoPackage (`.gpkg`) or GeoJSON.

| Layer | Interval |
|---|---|
| Regular contours | 500 ft |
| Bold index contours | 2000 ft |

Outputs: `sierra_basemap_output/sierra_contours_500ft.gpkg`, `sierra_contours_2000ft.gpkg`

### Step 6 — NLCD Vegetation Tinting (Optional)

**Source:** [Multi-Resolution Land Characteristics Consortium (MRLC) — Annual NLCD Land Cover](https://www.mrlc.gov/data)
**Dataset:** Annual NLCD Land Cover 2024 (EPSG:5070 Albers Equal Area). Reprojected on the fly to match the basemap extent.

NLCD land cover classes and blending treatment:

| NLCD Class(es) | Description | Tinting Treatment |
|---|---|---|
| 41, 42, 43 | Deciduous / Evergreen / Mixed Forest | Tiny green enhancement: R×0.97, G×1.01, B×0.97 |
| 52 | Shrub/Scrub | Push toward cool beige (235, 232, 222) at up to 55% blend |
| 71 | Grassland/Herbaceous (meadows) | Subtle green: R×0.96, G×1.02, B×0.96 |
| 31 | Barren (rock, sand, scree) | Push toward cool beige at up to 65% blend |
| 21–24 | Developed areas | Push toward warm gray (238, 232, 222) at up to 50% blend |
| 11, 12 | Open water / Ice | No tinting applied |

Tinting is graduated by elevation: full strength below ~7,000 ft (2,130m), linearly fading to zero above ~9,500 ft (2,900m) — allowing the high-alpine white ramp to dominate above treeline regardless of NLCD class.

Output: `sierra_basemap_output/sierra_basemap_nlcd.tif`

---

## Aesthetics and Styling

### Typography

- **Primary font:** Palatino (peaks, passes, rivers, lakes, meadows, basins)
- **Subranges and divides:** Cinzel or Palatino Small Caps, curved label placement following the line geometry
- **River labels:** Palatino Italic, blue, curved along flowline geometry, "Merge connected lines" enabled in QGIS label settings
- **Peak labels:** Black triangle marker (major peaks), Palatino, with white buffer/halo for legibility over terrain

### Print Configuration

| Setting | Value |
|---|---|
| Page size | 24"×60" or 36"×86" |
| Scale | 1:220,000 (2'×5') or 1:150,000 (3'×7') |
| Map rotation | 30° from North |
| Print resolution | 300 DPI |
| DPI for proofing | 150 DPI |

### Color Palette

*(Notes to fill in — add your label color choices, road color choices, contour color and weight choices, lake fill, glacier fill, and any other per-layer styling decisions here.)*

### Blend Mode Notes

- Hillshade layer: Multiply blend mode at 45% opacity over hypsometric tints
- NLCD layer: Applied as a pre-rendered GeoTIFF (see script Step 6 above) rather than a live QGIS blend, to avoid export artifacts

---

## Reproducing This Map

1. Download DEM tiles (bash script in [Step 1](#step-1--dem-merge-and-clip) above)
2. Download NLCD 2024 land cover from [mrlc.gov](https://www.mrlc.gov/data) and update `NLCD_PATH` in the script
3. Run `scripts/sierra_basemap_generation.py` to produce the base raster layers and contours
4. Download GNIS `DomesticNames_CA_Text.zip` from [USGS GNIS](https://www.usgs.gov/tools/geographic-names-information-system-gnis) and import as a delimited text layer
5. Download NHD Full Resolution Geodatabases for HUC 1803, 1804, 1809, and 1605 from [USGS NHD](https://www.usgs.gov/national-hydrography/access-national-hydrography-products)
6. Download TIGER/Line road shapefiles for Fresno, Inyo, Madera, Mono, Tulare, and Tuolumne counties from [Census TIGER](https://www.census.gov/cgi-bin/geo/shapefiles/index.php)
7. Build layers in QGIS following the [Layer Organization](#layer-organization) section above
8. Add `custom_peaks_list.csv` as a delimited text layer for climbing objectives not in GNIS
