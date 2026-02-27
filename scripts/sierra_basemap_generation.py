#!/usr/bin/env python3
"""
Sierra Nevada Topographic Basemap Generator
============================================
Produces a label-free topo basemap from USGS 3DEP DEM tiles.

Outputs:
  1. sierra_merged_dem.tif      — Merged + clipped DEM (meters)
  2. sierra_hillshade.tif       — Hillshade layer
  3. sierra_hypsometric.tif     — Elevation color ramp (RGB GeoTIFF)
  4. sierra_basemap.tif         — Final blended basemap (hillshade × tints)
  5. sierra_contours_500ft.gpkg — 500-foot contour lines (GeoPackage)
  6. sierra_contours_2000ft.gpkg— 2000-foot bold contour lines (GeoPackage)
  7. sierra_basemap_nlcd.tif    — (Optional) Basemap with vegetation tinting

Usage:
  Run all steps:
    python3 sierra_basemap_generation.py

  Run specific steps only (much faster for color tweaking):
    python3 sierra_basemap_generation.py hypsometric blend nlcd
    python3 sierra_basemap_generation.py nlcd

  Available steps:
    dem         — Merge and clip DEM tiles (slow, only needed once)
    hillshade   — Generate hillshade from DEM (only needed once)
    hypsometric — Generate elevation color ramp (re-run when tweaking colors)
    blend       — Blend hillshade × hypsometric (re-run after hypsometric)
    contours    — Generate contour lines (slow, only needed once)
    nlcd        — Apply NLCD vegetation tinting (re-run when tweaking NLCD)

Requires: rasterio, numpy, scipy, matplotlib, shapely
  pip install rasterio numpy scipy matplotlib shapely

Optional (for GeoPackage contour output instead of GeoJSON):
  pip install fiona

Optional (much faster contours — install GDAL CLI tools):
  brew install gdal          # macOS
  sudo apt install gdal-bin  # Linux
"""

import os
import sys
import glob
import time
import numpy as np
from pathlib import Path

# ============================================================================
# CONFIG — Edit these paths to match your setup
# ============================================================================

PROJECT_DIR = Path.home() / "projects" / "Sierra Nevada Entire Range Map"

# Directory containing your 9 USGS_13_*.tif DEM files
DEM_DIR = PROJECT_DIR / "geotiffs" / "USGS DEM"

# NLCD GeoTIFF (set to None to skip vegetation tinting)
NLCD_PATH = PROJECT_DIR / "geotiffs" / "NLCD_e9ce33df-24f9-454e-98e9-9c8223f2ecd7" / \
    "Annual_NLCD_LndCov_2024_CU_C1V1_e9ce33df-24f9-454e-98e9-9c8223f2ecd7.tiff"

# Output directory (will be created if needed)
OUTPUT_DIR = PROJECT_DIR / "sierra_basemap_output"

# Bounding box: Leavitt Meadows to Golden Trout Wilderness
# (lon_min, lat_min, lon_max, lat_max) in EPSG:4326
BBOX = (-120.25, 36.05, -117.5, 38.8)

# Hillshade parameters
AZIMUTH = 315      # Light direction (degrees from north)
ALTITUDE = 45      # Light angle above horizon (degrees)
Z_FACTOR = 1.0     # Vertical exaggeration (1.0 = none)

# Blend opacity for hillshade (0.0–1.0). 0.6 = 60% hillshade influence
HILLSHADE_OPACITY = 0.45

# Contour intervals (in feet)
CONTOUR_MINOR = 500    # Regular contour lines
CONTOUR_MAJOR = 2000   # Bold contour lines

# ============================================================================
# Hypsometric color ramp (elevation in meters → RGB)
# Tries to match the USGS Topo color scheme, which is lighter
# ============================================================================
HYPSOMETRIC_RAMP = [
    # Low elevations: cool light gray (not warm beige!)
    (300,  228, 232, 224),    # ~1,000 ft — Cool pale gray-green
    (900,  225, 230, 222),    # ~3,000 ft — Cool pale gray
    (1220, 222, 228, 218),    # ~4,000 ft — Barely green
    (1520, 218, 226, 214),    # ~5,000 ft — Hint of sage
    # Mid-elevation forest belt: the most green it gets (still very muted)
    (1830, 210, 222, 206),    # ~6,000 ft — Muted sage (peak green)
    (2130, 208, 220, 204),    # ~7,000 ft — Muted sage
    (2440, 216, 224, 212),    # ~8,000 ft — Fading sage
    # High elevation: cool cream to white
    (2745, 225, 226, 220),    # ~9,000 ft — Pale cool cream
    (3050, 251, 251, 249),    # ~10,000 ft — Near white
    (3200, 254, 254, 253),    # ~10,500 ft — Essentially white
    (3350, 255, 255, 245),    # ~11,000 ft — White
    (3500, 255, 255, 255),    # ~11,500 ft — White
    (3660, 255, 255, 255),    # ~12,000 ft — White
    (3960, 255, 255, 255),    # ~13,000 ft — White
    (4420, 255, 255, 255),    # ~14,500 ft — White
]

# ============================================================================
# END CONFIG
# ============================================================================

import rasterio
from rasterio.merge import merge
from rasterio.mask import mask
from rasterio.transform import from_bounds
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.features import shapes as rio_shapes
from scipy.ndimage import uniform_filter
import json


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
    return path


def log(msg):
    print(f"  → {msg}", flush=True)


def fmt_elapsed(seconds):
    """Format elapsed seconds as a human-readable string."""
    m, s = divmod(int(seconds), 60)
    if m > 0:
        return f"{m}m {s}s"
    return f"{s}s"


# ============================================================================
# Step 1: Merge DEM tiles and clip to bounding box
# ============================================================================
def merge_and_clip_dem():
    print("\n" + "="*60)
    print("STEP 1: Merging DEM tiles and clipping to bounding box")
    print("="*60)

    output_path = os.path.join(OUTPUT_DIR, "sierra_merged_dem.tif")

    # Find all DEM tiles
    tiles = sorted(glob.glob(os.path.join(DEM_DIR, "USGS_13_*.tif")))
    if not tiles:
        print(f"  ERROR: No DEM tiles found in {DEM_DIR}")
        print(f"  Expected files like: USGS_13_n38w120.tif")
        sys.exit(1)

    log(f"Found {len(tiles)} DEM tiles")
    for t in tiles:
        log(f"  {os.path.basename(t)}")

    # Open all tiles
    src_files = [rasterio.open(t) for t in tiles]

    # Merge
    log("Merging tiles (this may take a minute)...")
    mosaic, out_transform = merge(src_files)
    out_meta = src_files[0].meta.copy()
    out_meta.update({
        "driver": "GTiff",
        "height": mosaic.shape[1],
        "width": mosaic.shape[2],
        "transform": out_transform,
        "compress": "lzw",
    })

    # Close source files
    for s in src_files:
        s.close()

    # Write merged (full extent first, then clip)
    merged_full = os.path.join(OUTPUT_DIR, "_temp_merged_full.tif")
    log("Writing merged raster...")
    out_meta["BIGTIFF"] = "YES"
    with rasterio.open(merged_full, "w", **out_meta) as dest:
        dest.write(mosaic)

    # Clip to bounding box
    log(f"Clipping to bbox: {BBOX}")
    from shapely.geometry import box
    clip_geom = [box(BBOX[0], BBOX[1], BBOX[2], BBOX[3]).__geo_interface__]

    with rasterio.open(merged_full) as src:
        clipped, clipped_transform = mask(src, clip_geom, crop=True)
        clip_meta = src.meta.copy()
        clip_meta.update({
            "height": clipped.shape[1],
            "width": clipped.shape[2],
            "transform": clipped_transform,
            "compress": "lzw",
        })

    with rasterio.open(output_path, "w", **clip_meta) as dest:
        dest.write(clipped)

    # Clean up temp
    os.remove(merged_full)

    log(f"Output: {output_path}")
    log(f"Shape: {clipped.shape[1]} × {clipped.shape[2]} pixels")
    return output_path


# ============================================================================
# Step 2: Generate hillshade
# ============================================================================
def generate_hillshade(dem_path):
    print("\n" + "="*60)
    print("STEP 2: Generating hillshade")
    print("="*60)

    output_path = os.path.join(OUTPUT_DIR, "sierra_hillshade.tif")

    with rasterio.open(dem_path) as src:
        dem = src.read(1).astype(np.float32)
        meta = src.meta.copy()
        res_x = abs(src.transform[0])  # cell size in degrees
        res_y = abs(src.transform[4])

    # For geographic CRS (degrees), we need to convert cell size to meters
    # at the latitude of the center of the dataset
    center_lat = (BBOX[1] + BBOX[3]) / 2.0
    lat_rad = np.radians(center_lat)
    meters_per_deg_x = 111320 * np.cos(lat_rad)
    meters_per_deg_y = 111320

    cellsize_x = res_x * meters_per_deg_x
    cellsize_y = res_y * meters_per_deg_y

    log(f"Cell size: ~{cellsize_x:.1f} × {cellsize_y:.1f} meters")
    log(f"Azimuth: {AZIMUTH}°, Altitude: {ALTITUDE}°, Z-factor: {Z_FACTOR}")

    # Replace nodata with nan
    nodata = meta.get("nodata")
    if nodata is not None:
        dem[dem == nodata] = np.nan

    # Compute gradient (Horn's method approximation using numpy)
    # dz/dx and dz/dy
    pad = np.pad(dem, 1, mode='edge')
    dzdx = (
        (pad[:-2, 2:] + 2*pad[1:-1, 2:] + pad[2:, 2:]) -
        (pad[:-2, :-2] + 2*pad[1:-1, :-2] + pad[2:, :-2])
    ) / (8.0 * cellsize_x)
    dzdy = (
        (pad[:-2, :-2] + 2*pad[:-2, 1:-1] + pad[:-2, 2:]) -
        (pad[2:, :-2] + 2*pad[2:, 1:-1] + pad[2:, 2:])
    ) / (8.0 * cellsize_y)

    # Apply z-factor
    dzdx *= Z_FACTOR
    dzdy *= Z_FACTOR

    # Convert azimuth and altitude to radians
    azimuth_rad = np.radians(360 - AZIMUTH + 90)  # convert to math angle
    altitude_rad = np.radians(ALTITUDE)

    # Hillshade formula
    slope = np.arctan(np.sqrt(dzdx**2 + dzdy**2))
    aspect = np.arctan2(-dzdy, dzdx)  # Note: -dzdy for geographic convention

    hillshade = (
        np.sin(altitude_rad) * np.cos(slope) +
        np.cos(altitude_rad) * np.sin(slope) * np.cos(azimuth_rad - aspect)
    )

    # Scale to 0-255
    hillshade = np.clip(hillshade * 255, 0, 255).astype(np.uint8)

    # Handle nodata areas
    hillshade[np.isnan(dem)] = 0

    # Write output
    hs_meta = meta.copy()
    hs_meta.update({
        "dtype": "uint8",
        "nodata": 0,
        "compress": "lzw",
    })

    with rasterio.open(output_path, "w", **hs_meta) as dest:
        dest.write(hillshade, 1)

    log(f"Output: {output_path}")
    return output_path


# ============================================================================
# Step 3: Generate hypsometric tints (elevation → color)
# ============================================================================
def generate_hypsometric(dem_path):
    print("\n" + "="*60)
    print("STEP 3: Generating hypsometric tints")
    print("="*60)

    output_path = os.path.join(OUTPUT_DIR, "sierra_hypsometric.tif")

    with rasterio.open(dem_path) as src:
        dem = src.read(1).astype(np.float32)
        meta = src.meta.copy()

    nodata = meta.get("nodata")
    if nodata is not None:
        dem[np.isclose(dem, nodata)] = np.nan

    log(f"Elevation range: {np.nanmin(dem):.0f}m – {np.nanmax(dem):.0f}m")

    # Build lookup arrays for interpolation
    elevs = np.array([e for e, r, g, b in HYPSOMETRIC_RAMP], dtype=np.float32)
    reds  = np.array([r for e, r, g, b in HYPSOMETRIC_RAMP], dtype=np.float32)
    greens = np.array([g for e, r, g, b in HYPSOMETRIC_RAMP], dtype=np.float32)
    blues = np.array([b for e, r, g, b in HYPSOMETRIC_RAMP], dtype=np.float32)

    # Interpolate each channel
    log("Interpolating elevation colors...")
    r = np.interp(dem, elevs, reds).astype(np.uint8)
    g = np.interp(dem, elevs, greens).astype(np.uint8)
    b = np.interp(dem, elevs, blues).astype(np.uint8)

    # Set nodata areas to a neutral gray
    nan_mask = np.isnan(dem)
    r[nan_mask] = 200
    g[nan_mask] = 200
    b[nan_mask] = 200

    # Below-ramp areas (e.g. low valleys): clamp to darkest green
    below = dem < elevs[0]
    r[below & ~nan_mask] = HYPSOMETRIC_RAMP[0][1]
    g[below & ~nan_mask] = HYPSOMETRIC_RAMP[0][2]
    b[below & ~nan_mask] = HYPSOMETRIC_RAMP[0][3]

    # Write RGB GeoTIFF
    rgb_meta = meta.copy()
    rgb_meta.update({
        "dtype": "uint8",
        "count": 3,
        "nodata": None,
        "compress": "lzw",
    })

    with rasterio.open(output_path, "w", **rgb_meta) as dest:
        dest.write(r, 1)
        dest.write(g, 2)
        dest.write(b, 3)

    log(f"Output: {output_path}")
    return output_path


# ============================================================================
# Step 4: Blend hillshade + hypsometric tints (Multiply blend mode)
# ============================================================================
def blend_basemap(hillshade_path, hypsometric_path):
    print("\n" + "="*60)
    print("STEP 4: Blending hillshade × hypsometric tints")
    print("="*60)

    output_path = os.path.join(OUTPUT_DIR, "sierra_basemap.tif")

    with rasterio.open(hillshade_path) as hs_src:
        hillshade = hs_src.read(1).astype(np.float32) / 255.0

    with rasterio.open(hypsometric_path) as hyp_src:
        r = hyp_src.read(1).astype(np.float32)
        g = hyp_src.read(2).astype(np.float32)
        b = hyp_src.read(3).astype(np.float32)
        meta = hyp_src.meta.copy()

    log(f"Hillshade opacity: {HILLSHADE_OPACITY}")

    # Multiply blend: result = hypsometric × hillshade
    # With opacity control: result = lerp(hypsometric, hypsometric × hillshade, opacity)
    #   = hypsometric × (1 - opacity + opacity × hillshade)
    blend_factor = (1.0 - HILLSHADE_OPACITY) + HILLSHADE_OPACITY * hillshade

    r_out = np.clip(r * blend_factor, 0, 255).astype(np.uint8)
    g_out = np.clip(g * blend_factor, 0, 255).astype(np.uint8)
    b_out = np.clip(b * blend_factor, 0, 255).astype(np.uint8)

    with rasterio.open(output_path, "w", **meta) as dest:
        dest.write(r_out, 1)
        dest.write(g_out, 2)
        dest.write(b_out, 3)

    log(f"Output: {output_path}")
    return output_path


# ============================================================================
# Step 5: Generate contour lines
# ============================================================================
def generate_contours(dem_path):
    print("\n" + "="*60)
    print("STEP 5: Generating contour lines")
    print("="*60)

    try:
        import subprocess
        # Check if gdal_contour is available (much faster than pure Python)
        result = subprocess.run(["gdal_contour", "--version"],
                                capture_output=True, text=True)
        has_gdal = result.returncode == 0
    except FileNotFoundError:
        has_gdal = False

    if has_gdal:
        return _contours_gdal(dem_path)
    else:
        return _contours_python(dem_path)


def _contours_gdal(dem_path):
    """Use gdal_contour (fast, robust)."""
    import subprocess

    # Convert DEM to feet first for clean contour values
    dem_ft_path = os.path.join(OUTPUT_DIR, "_temp_dem_feet.tif")

    log("Converting DEM to feet...")
    with rasterio.open(dem_path) as src:
        dem = src.read(1).astype(np.float32)
        meta = src.meta.copy()
        nodata = meta.get("nodata")
        if nodata is not None:
            valid = dem != nodata
            dem[valid] = dem[valid] * 3.28084
        else:
            dem = dem * 3.28084
        meta["dtype"] = "float32"

    with rasterio.open(dem_ft_path, "w", **meta) as dest:
        dest.write(dem, 1)

    # Generate 500' contours
    out_500 = os.path.join(OUTPUT_DIR, "sierra_contours_500ft.gpkg")
    log(f"Generating {CONTOUR_MINOR}' contours...")
    subprocess.run([
        "gdal_contour",
        "-a", "elevation_ft",
        "-i", str(CONTOUR_MINOR),
        "-f", "GPKG",
        dem_ft_path, out_500
    ], check=True)
    log(f"Output: {out_500}")

    # Generate 2000' contours
    out_2000 = os.path.join(OUTPUT_DIR, "sierra_contours_2000ft.gpkg")
    log(f"Generating {CONTOUR_MAJOR}' contours...")
    subprocess.run([
        "gdal_contour",
        "-a", "elevation_ft",
        "-i", str(CONTOUR_MAJOR),
        "-f", "GPKG",
        dem_ft_path, out_2000
    ], check=True)
    log(f"Output: {out_2000}")

    os.remove(dem_ft_path)
    return out_500, out_2000


def _contours_python(dem_path):
    """Pure Python/matplotlib contour generation (slower but no GDAL needed)."""
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection

    log("Using matplotlib for contour generation (gdal_contour not found)")
    log("This will be slower but works without GDAL CLI tools")

    with rasterio.open(dem_path) as src:
        dem = src.read(1).astype(np.float32)
        transform = src.transform
        crs = src.crs
        nodata = src.nodata

    if nodata is not None:
        dem[dem == nodata] = np.nan

    # Convert to feet
    dem_ft = dem * 3.28084

    # Build coordinate arrays
    rows, cols = dem_ft.shape
    x = np.array([transform[2] + (c + 0.5) * transform[0] for c in range(cols)])
    y = np.array([transform[5] + (r + 0.5) * transform[4] for r in range(rows)])

    for interval, label in [(CONTOUR_MINOR, "500ft"), (CONTOUR_MAJOR, "2000ft")]:
        output_path = os.path.join(OUTPUT_DIR, f"sierra_contours_{label}.gpkg")
        log(f"Generating {label} contours...")

        # Compute contour levels
        vmin = np.nanmin(dem_ft)
        vmax = np.nanmax(dem_ft)
        levels = np.arange(
            np.ceil(vmin / interval) * interval,
            vmax + 1,
            interval
        )

        # Generate contours using matplotlib (not rendering, just computing)
        fig, ax = plt.subplots()
        cs = ax.contour(x, y, dem_ft, levels=levels)
        plt.close(fig)

        # Convert to GeoPackage via manual GeoJSON → rasterio/fiona
        try:
            import fiona
            from fiona.crs import from_epsg
            has_fiona = True
        except ImportError:
            has_fiona = False

        if has_fiona:
            schema = {
                "geometry": "LineString",
                "properties": {"elevation_ft": "float"},
            }
            with fiona.open(output_path, "w", driver="GPKG",
                            schema=schema, crs=crs.to_dict()) as dst:
                for level_idx, level in enumerate(cs.levels):
                    for seg in cs.allsegs[level_idx]:
                        if len(seg) < 2:
                            continue
                        coords = seg.tolist()
                        dst.write({
                            "geometry": {
                                "type": "LineString",
                                "coordinates": coords,
                            },
                            "properties": {"elevation_ft": float(level)},
                        })
        else:
            # Fallback: write GeoJSON
            output_path = output_path.replace(".gpkg", ".geojson")
            features = []
            for level_idx, level in enumerate(cs.levels):
                for seg in cs.allsegs[level_idx]:
                    if len(seg) < 2:
                        continue
                    features.append({
                        "type": "Feature",
                        "geometry": {
                            "type": "LineString",
                            "coordinates": seg.tolist(),
                        },
                        "properties": {"elevation_ft": float(level)},
                    })

            geojson = {
                "type": "FeatureCollection",
                "crs": {"type": "name",
                         "properties": {"name": f"urn:ogc:def:crs:EPSG::{crs.to_epsg()}"}},
                "features": features,
            }
            with open(output_path, "w") as f:
                json.dump(geojson, f)

        log(f"Output: {output_path} ({len(levels)} contour levels)")

    return (
        os.path.join(OUTPUT_DIR, f"sierra_contours_{CONTOUR_MINOR}ft.*"),
        os.path.join(OUTPUT_DIR, f"sierra_contours_{CONTOUR_MAJOR}ft.*"),
    )


# ============================================================================
# Step 6 (Optional): NLCD vegetation tinting
# ============================================================================
def apply_nlcd_tinting(basemap_path, dem_path):
    print("\n" + "="*60)
    print("STEP 6: Applying NLCD vegetation tinting")
    print("="*60)

    if NLCD_PATH is None or not os.path.exists(NLCD_PATH):
        log("NLCD path not set or file not found — skipping")
        return basemap_path

    output_path = os.path.join(OUTPUT_DIR, "sierra_basemap_nlcd.tif")

    # Read basemap
    with rasterio.open(basemap_path) as src:
        basemap_r = src.read(1).astype(np.float32)
        basemap_g = src.read(2).astype(np.float32)
        basemap_b = src.read(3).astype(np.float32)
        bm_meta = src.meta.copy()
        bm_transform = src.transform
        bm_crs = src.crs
        bm_shape = basemap_r.shape

    # We need to reproject NLCD to match the basemap's extent/resolution
    # NLCD is typically in Albers Equal Area (EPSG:5070)
    log("Reprojecting NLCD to match basemap extent...")

    with rasterio.open(NLCD_PATH) as nlcd_src:
        # Calculate transform for target
        dst_transform, dst_width, dst_height = calculate_default_transform(
            nlcd_src.crs, bm_crs,
            nlcd_src.width, nlcd_src.height,
            *nlcd_src.bounds,
            dst_width=bm_shape[1], dst_height=bm_shape[0]
        )

        # We actually want to match exactly
        nlcd_reprojected = np.zeros(bm_shape, dtype=np.uint8)
        reproject(
            source=rasterio.band(nlcd_src, 1),
            destination=nlcd_reprojected,
            src_transform=nlcd_src.transform,
            src_crs=nlcd_src.crs,
            dst_transform=bm_transform,
            dst_crs=bm_crs,
            resampling=Resampling.nearest,
        )

    log("Applying vegetation color adjustments...")

    # NLCD classes and their tinting
    # Forest (41=Deciduous, 42=Evergreen, 43=Mixed) → green boost
    # Shrub (52) → slight warm/tan tint
    # Grassland/Herbaceous (71) → light green (meadows)
    # Barren (31) → no change (rock)

    # Target beige for non-vegetated areas: rgb(245, 240, 230)
    # Strategy: push NON-forest areas toward warm beige,
    # rather than pushing forest areas toward green
    
    forest_mask = np.isin(nlcd_reprojected, [41, 42, 43])
    shrub_mask = nlcd_reprojected == 52
    grass_mask = nlcd_reprojected == 71
    water_mask = np.isin(nlcd_reprojected, [11, 12])
    barren_mask = np.isin(nlcd_reprojected, [31])  # Rock/sand/clay
    developed_mask = np.isin(nlcd_reprojected, [21, 22, 23, 24])

    # Read DEM to mask high elevations from NLCD tinting
    with rasterio.open(dem_path) as dem_src:
        dem_elev = np.zeros(bm_shape, dtype=np.float32)
        reproject(
            source=rasterio.band(dem_src, 1),
            destination=dem_elev,
            src_transform=dem_src.transform,
            src_crs=dem_src.crs,
            dst_transform=bm_transform,
            dst_crs=bm_crs,
            resampling=Resampling.bilinear,
        )

    # Don't apply NLCD tinting above ~9500ft (2900m) — let the ramp's white shine
    high_elev_mask = dem_elev > 2900
    shrub_mask = shrub_mask & ~high_elev_mask
    barren_mask = barren_mask & ~high_elev_mask
    developed_mask = developed_mask & ~high_elev_mask

    # Elevation-graduated blend: stronger NLCD influence at lower elevations
    # Below 2130m (~7000ft): full strength. 2130-2900m: fade out linearly.
    nlcd_strength = np.clip((2900 - dem_elev) / (2900 - 2130), 0.0, 1.0)
    nlcd_strength[high_elev_mask] = 0.0

    # Cooler, lighter beige — closer to warm gray than golden tan
    beige_r, beige_g, beige_b = 235, 232, 222

    # Shrub: strong push toward cool beige, graduated by elevation
    shrub_blend = 0.55 * nlcd_strength  # up to 55% beige at low elevations
    basemap_r[shrub_mask] = basemap_r[shrub_mask] * (1 - shrub_blend[shrub_mask]) + beige_r * shrub_blend[shrub_mask]
    basemap_g[shrub_mask] = basemap_g[shrub_mask] * (1 - shrub_blend[shrub_mask]) + beige_g * shrub_blend[shrub_mask]
    basemap_b[shrub_mask] = basemap_b[shrub_mask] * (1 - shrub_blend[shrub_mask]) + beige_b * shrub_blend[shrub_mask]

    # Barren: even stronger beige
    barren_blend = 0.65 * nlcd_strength
    basemap_r[barren_mask] = basemap_r[barren_mask] * (1 - barren_blend[barren_mask]) + beige_r * barren_blend[barren_mask]
    basemap_g[barren_mask] = basemap_g[barren_mask] * (1 - barren_blend[barren_mask]) + beige_g * barren_blend[barren_mask]
    basemap_b[barren_mask] = basemap_b[barren_mask] * (1 - barren_blend[barren_mask]) + beige_b * barren_blend[barren_mask]

    # Developed areas: neutral warm gray
    dev_blend = 0.50 * nlcd_strength
    basemap_r[developed_mask] = basemap_r[developed_mask] * (1 - dev_blend[developed_mask]) + 238 * dev_blend[developed_mask]
    basemap_g[developed_mask] = basemap_g[developed_mask] * (1 - dev_blend[developed_mask]) + 232 * dev_blend[developed_mask]
    basemap_b[developed_mask] = basemap_b[developed_mask] * (1 - dev_blend[developed_mask]) + 222 * dev_blend[developed_mask]

    # Forest: preserve the sage-green from the ramp, tiny enhancement only
    basemap_r[forest_mask] *= 0.97
    basemap_g[forest_mask] *= 1.01
    basemap_b[forest_mask] *= 0.97

    # Grassland/meadow: very subtle brighter green
    basemap_r[grass_mask] *= 0.96
    basemap_g[grass_mask] *= 1.02
    basemap_b[grass_mask] *= 0.96

    r_out = np.clip(basemap_r, 0, 255).astype(np.uint8)
    g_out = np.clip(basemap_g, 0, 255).astype(np.uint8)
    b_out = np.clip(basemap_b, 0, 255).astype(np.uint8)

    with rasterio.open(output_path, "w", **bm_meta) as dest:
        dest.write(r_out, 1)
        dest.write(g_out, 2)
        dest.write(b_out, 3)

    log(f"Output: {output_path}")
    log(f"Forest pixels: {forest_mask.sum():,}")
    log(f"Shrub pixels:  {shrub_mask.sum():,}")
    log(f"Meadow pixels: {grass_mask.sum():,}")
    return output_path


# ============================================================================
# Step registry and CLI
# ============================================================================
STEP_NAMES = ["dem", "hillshade", "hypsometric", "blend", "contours", "nlcd"]


def resolve_paths():
    """Return expected paths for intermediate files."""
    return {
        "dem": os.path.join(OUTPUT_DIR, "sierra_merged_dem.tif"),
        "hillshade": os.path.join(OUTPUT_DIR, "sierra_hillshade.tif"),
        "hypsometric": os.path.join(OUTPUT_DIR, "sierra_hypsometric.tif"),
        "basemap": os.path.join(OUTPUT_DIR, "sierra_basemap.tif"),
        "nlcd": os.path.join(OUTPUT_DIR, "sierra_basemap_nlcd.tif"),
    }


def main():
    # Parse CLI args for step selection
    requested_steps = [s.lower() for s in sys.argv[1:] if not s.startswith("-")]

    # Validate step names
    for s in requested_steps:
        if s not in STEP_NAMES:
            print(f"ERROR: Unknown step '{s}'")
            print(f"Available steps: {', '.join(STEP_NAMES)}")
            sys.exit(1)

    run_all = len(requested_steps) == 0
    steps_to_run = set(requested_steps) if not run_all else set(STEP_NAMES)

    print("=" * 60)
    print("  Sierra Nevada Topographic Basemap Generator")
    print("=" * 60)
    print(f"  DEM directory:  {DEM_DIR}")
    print(f"  NLCD file:      {NLCD_PATH}")
    print(f"  Output dir:     {OUTPUT_DIR}")
    print(f"  Bounding box:   {BBOX}")
    if not run_all:
        print(f"  Steps:          {', '.join(requested_steps)}")
    else:
        print(f"  Steps:          ALL")
    print()

    # Validate inputs
    if "dem" in steps_to_run and not os.path.isdir(DEM_DIR):
        print(f"ERROR: DEM directory not found: {DEM_DIR}")
        sys.exit(1)

    ensure_dir(OUTPUT_DIR)

    paths = resolve_paths()
    pipeline_start = time.time()

    # Step 1: DEM merge
    if "dem" in steps_to_run:
        t0 = time.time()
        merge_and_clip_dem()
        log(f"Step 'dem' completed in {fmt_elapsed(time.time() - t0)}")
    elif not os.path.exists(paths["dem"]):
        print(f"ERROR: {paths['dem']} not found. Run 'dem' step first.")
        sys.exit(1)

    dem_path = paths["dem"]

    # Step 2: Hillshade
    if "hillshade" in steps_to_run:
        t0 = time.time()
        generate_hillshade(dem_path)
        log(f"Step 'hillshade' completed in {fmt_elapsed(time.time() - t0)}")
    elif "blend" in steps_to_run and not os.path.exists(paths["hillshade"]):
        print(f"ERROR: {paths['hillshade']} not found. Run 'hillshade' step first.")
        sys.exit(1)

    # Step 3: Hypsometric
    if "hypsometric" in steps_to_run:
        t0 = time.time()
        generate_hypsometric(dem_path)
        log(f"Step 'hypsometric' completed in {fmt_elapsed(time.time() - t0)}")
    elif "blend" in steps_to_run and not os.path.exists(paths["hypsometric"]):
        print(f"ERROR: {paths['hypsometric']} not found. Run 'hypsometric' step first.")
        sys.exit(1)

    # Step 4: Blend
    if "blend" in steps_to_run:
        t0 = time.time()
        blend_basemap(paths["hillshade"], paths["hypsometric"])
        log(f"Step 'blend' completed in {fmt_elapsed(time.time() - t0)}")
    elif "nlcd" in steps_to_run and not os.path.exists(paths["basemap"]):
        print(f"ERROR: {paths['basemap']} not found. Run 'blend' step first.")
        sys.exit(1)

    # Step 5: Contours
    if "contours" in steps_to_run:
        t0 = time.time()
        generate_contours(dem_path)
        log(f"Step 'contours' completed in {fmt_elapsed(time.time() - t0)}")

    # Step 6: NLCD
    if "nlcd" in steps_to_run:
        t0 = time.time()
        if NLCD_PATH and os.path.exists(NLCD_PATH):
            apply_nlcd_tinting(paths["basemap"], dem_path)
            log(f"Step 'nlcd' completed in {fmt_elapsed(time.time() - t0)}")
        else:
            log("Skipping NLCD vegetation tinting (file not found or not configured)")

    total_elapsed = time.time() - pipeline_start

    print("\n" + "=" * 60)
    print(f"  DONE! Total time: {fmt_elapsed(total_elapsed)}")
    print(f"  Output dir: {OUTPUT_DIR}")
    print("=" * 60)

    if run_all:
        print()
        print("  Quick re-runs for color tweaking:")
        print("    python3 sierra_basemap_generation.py hypsometric blend nlcd")
        print("    python3 sierra_basemap_generation.py nlcd")
        print()


if __name__ == "__main__":
    main()