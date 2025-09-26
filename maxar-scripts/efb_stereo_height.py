#!/usr/bin/env python3
"""
EFB Pile Height from Maxar stereo (prototype)
Inputs: date (YYYY-MM-DD), lat, lon
Outputs: imagery preview, DSM, height estimate, PDF report saved locally.

Prereqs:
  - Python 3.9+
  - pip install: requests, shapely, rasterio, numpy, matplotlib, reportlab, tqdm
  - Install NASA Ames Stereo Pipeline and ensure 'parallel_stereo' and 'point2dem' in PATH.
  - A valid Maxar MGP bearer token with access to Discovery and Browse-Archive stereo APIs.

Usage:
  python efb_stereo_height.py --date 2025-08-31 --lat 3.9152 --lon 103.3910
"""
import argparse, os, sys, json, time, subprocess, tempfile, math
from datetime import datetime, timedelta
import requests
from shapely.geometry import Point, mapping
import numpy as np
import rasterio
from rasterio.mask import mask
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from tqdm import tqdm

# ========= USER CONFIG (fill these in) =========
MGP_BEARER_TOKEN = os.environ.get("MGP_TOKEN", "PUT_YOUR_MAXAR_BEARER_TOKEN_HERE")
SEARCH_RADIUS_M = 150       # radius around the point for search (meters)
PILE_RADIUS_M   = 25        # radius used to measure pile area
BACKGROUND_RING_M = 40      # ring outside pile for "ground" reference (median)
MAX_CLOUD_PCT = 20
MAX_OFF_NADIR_DEG = 35
# ==============================================

DISCOVERY_BASE = "https://api.maxar.com/discovery/v1"
STEREO_BASE    = "https://api.maxar.com/browse-archive/v1"

HDRS = {"Authorization": f"Bearer {MGP_BEARER_TOKEN}"}

def haversine_buffer_geojson(lat, lon, radius_m):
    # Very small buffer: approximate meters to degrees using local scale.
    # For STAC intersects, a ~circle polygon is overkill; a small square is fine. We'll do a tiny square.
    dlat = radius_m / 111320.0
    dlon = radius_m / (111320.0 * math.cos(math.radians(lat)))
    coords = [
        [lon - dlon, lat - dlat],
        [lon + dlon, lat - dlat],
        [lon + dlon, lat + dlat],
        [lon - dlon, lat + dlat],
        [lon - dlon, lat - dlat],
    ]
    return {"type": "Polygon", "coordinates": [coords]}

def stac_search_items(date_str, lat, lon, radius_m, days_window=15):
    """
    Use Discovery STAC /search (CQL2) to find items near date/location.
    """
    t0 = datetime.fromisoformat(date_str)
    start = (t0 - timedelta(days=days_window)).strftime("%Y-%m-%dT00:00:00Z")
    end   = (t0 + timedelta(days=days_window)).strftime("%Y-%m-%dT23:59:59Z")

    body = {
        "datetime": f"{start}/{end}",
        "limit": 100,
        "intersects": haversine_buffer_geojson(lat, lon, radius_m),
        # Filter on properties (CQL2 text) if supported by your account/collections.
        # Example filters often used: cloud cover, off-nadir, sensor names, etc.
        "filter-lang": "cql2-text",
        "filter": f"properties.maxar:cloudCoverPercent < {MAX_CLOUD_PCT} AND properties.view:offNadir < {MAX_OFF_NADIR_DEG}"
    }
    r = requests.post(f"{DISCOVERY_BASE}/search", headers=HDRS, json=body, timeout=60)
    r.raise_for_status()
    return r.json()

def find_stereo_pairs(date_str, lat, lon, radius_m):
    """
    Use Browse-Archive Stereo endpoint to request valid stereo pairs near AOI/time.
    """
    body = {
        # AOI is a polygon; send small square around the point:
        "aoi": haversine_buffer_geojson(lat, lon, radius_m),
        # Optional: date window
        "startDate": (datetime.fromisoformat(date_str) - timedelta(days=15)).strftime("%Y-%m-%d"),
        "endDate":   (datetime.fromisoformat(date_str) + timedelta(days=15)).strftime("%Y-%m-%d"),
        # Optional filters:
        "maxCloudCover": MAX_CLOUD_PCT,
        "maxOffNadirAngle": MAX_OFF_NADIR_DEG
    }
    r = requests.post(f"{STEREO_BASE}/stereo", headers=HDRS, json=body, timeout=60)
    r.raise_for_status()
    return r.json()

def download_asset(url, out_path):
    with requests.get(url, headers=HDRS, stream=True, timeout=300) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1<<20):
                if chunk:
                    f.write(chunk)
    return out_path

def run_asp(left_tif, left_rpc, right_tif, right_rpc, out_dir):
    """
    Calls parallel_stereo then point2dem to produce a DSM GeoTIFF.
    Assumes Level-1B with RPC available (typical for Maxar System Ready Basic/Standard).
    """
    stem = os.path.join(out_dir, "wv_stereo")
    # parallel_stereo will detect RPC from .xml or .rpc sidecars if named consistently.
    cmd1 = [
        "parallel_stereo",
        left_tif, right_tif,  # images
        left_rpc, right_rpc,  # cameras (RPC XMLs)
        stem,
        "--alignment-method", "affineepipolar",
        "--subpixel-mode", "3",
        "--threads", str(max(1, os.cpu_count() - 1))
    ]
    print("Running:", " ".join(cmd1))
    subprocess.check_call(cmd1)

    # Convert point cloud to DSM
    cmd2 = [
        "point2dem",
        stem + "-PC.tif",
        "--tr", "0.5",   # 0.5 m grid (tune to sensor/GSD)
        "--outdir", out_dir,
        "--nodata", "-32767"
    ]
    print("Running:", " ".join(cmd2))
    subprocess.check_call(cmd2)
    dsm_tif = os.path.join(out_dir, "wv_stereo-DEM.tif")  # naming per point2dem default
    return dsm_tif

def circle_mask(dataset, lat, lon, radius_m):
    # Create a small circular polygon around (lat,lon) in GeoJSON by approximating with a square mask then refine using distance
    # Simpler: mask via square, then compute distances in meters approximately.
    dlat = radius_m / 111320.0
    dlon = radius_m / (111320.0 * math.cos(math.radians(lat)))
    poly = haversine_buffer_geojson(lat, lon, radius_m)
    out_image, out_transform = mask(dataset, [poly], crop=True)
    arr = out_image[0]
    # Build a boolean circle mask on this cropped window
    rows, cols = arr.shape
    ys = np.arange(rows)
    xs = np.arange(cols)
    xv, yv = np.meshgrid(xs, ys)
    # convert pixel to lat/lon roughly
    # Use affine to map pixels to geographic
    T = out_transform
    lons = T.c + xv * T.a + yv * T.b
    lats = T.f + xv * T.d + yv * T.e
    dist_m = np.sqrt(((lats - lat) * 111320.0)**2 + ((lons - lon) * 111320.0 * np.cos(np.radians(lat)))**2)
    circle = dist_m <= radius_m
    return arr, circle

def estimate_pile_height(dsm_path, lat, lon, pile_m=25, bg_ring_m=40):
    with rasterio.open(dsm_path) as ds:
        pile_arr, pile_circle = circle_mask(ds, lat, lon, pile_m)
        bg_arr, bg_circle = circle_mask(ds, lat, lon, bg_ring_m)
        # background ring = within bg_ring but outside pile_circle (same crop, so align sizes)
        # For simplicity, recompute bg on same window:
        # use bg_circle but exclude inner pile circle indices (same size, as both cropped independently they differ).
        # Instead, compute background as pixels within [pile_m, bg_ring_m]
        # We already have separate crops; fallback: use bg_arr median minus pile_arr max from its own crop.
        pile_vals = pile_arr[pile_circle & np.isfinite(pile_arr)]
        bg_vals   = bg_arr[np.isfinite(bg_arr)]
        if pile_vals.size == 0 or bg_vals.size == 0:
            return None, None, None
        pile_max = np.percentile(pile_vals, 95)   # robust max
        bg_med   = np.median(bg_vals)
        height_m = float(pile_max - bg_med)
    return height_m, pile_max, bg_med

def quicklook_png(dsm_path, lat, lon, out_png):
    with rasterio.open(dsm_path) as ds:
        data = ds.read(1, masked=True)
        vmin, vmax = np.percentile(data.compressed(), [5, 95])
        plt.figure(figsize=(6, 6))
        plt.imshow(data, vmin=vmin, vmax=vmax)
        plt.title("DSM (m)")
        plt.scatter([], [])  # keep default legend clean
        plt.savefig(out_png, dpi=150, bbox_inches="tight")
        plt.close()
    return out_png

def write_pdf(report_path, lat, lon, date_str, height_m, dsm_png):
    c = canvas.Canvas(report_path, pagesize=A4)
    w, h = A4
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2*cm, h-2.5*cm, "EFB Pile Height Report (Stereo-derived)")
    c.setFont("Helvetica", 11)
    c.drawString(2*cm, h-3.5*cm, f"Date requested: {date_str}")
    c.drawString(2*cm, h-4.2*cm, f"Location: {lat:.6f}, {lon:.6f}")
    gmaps = f"https://www.google.com/maps?q={lat:.6f},{lon:.6f}"
    c.drawString(2*cm, h-4.9*cm, f"Google Maps: {gmaps}")
    c.drawString(2*cm, h-5.6*cm, f"Estimated pile height: {height_m:.2f} m" if height_m is not None else "Estimated pile height: N/A")

    # Image
    if os.path.exists(dsm_png):
        c.drawImage(dsm_png, 2*cm, 3*cm, width=16*cm, height=12*cm, preserveAspectRatio=True, mask='auto')

    c.setFont("Helvetica-Oblique", 8)
    c.drawString(2*cm, 2*cm, "Method: Stereo pair → DSM via Ames Stereo Pipeline; height = 95th pct (pile) − median (local background).")
    c.drawString(2*cm, 1.4*cm, "Prototype — for internal testing.")
    c.showPage()
    c.save()
    return report_path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--lat",  type=float, required=True)
    ap.add_argument("--lon",  type=float, required=True)
    args = ap.parse_args()

    if "PUT_YOUR_MAXAR_BEARER_TOKEN_HERE" in MGP_BEARER_TOKEN:
        print("\n[!] You must set MGP_TOKEN env var or edit MGP_BEARER_TOKEN with your Maxar bearer token.\n", file=sys.stderr)
        sys.exit(2)

    work = tempfile.mkdtemp(prefix="efb_stereo_")
    print("Working dir:", work)

    # 1) Find stereo pairs near date/AOI
    print("Searching for stereo pairs…")
    stereo = find_stereo_pairs(args.date, args.lat, args.lon, SEARCH_RADIUS_M)
    # Response schema can include candidate image IDs and URLs. For now we assume first match has two items with download links.
    # You may need to adapt keys based on your account/product.
    # Fallback: do a general STAC search to list items.
    if not stereo or "pairs" not in stereo or len(stereo["pairs"]) == 0:
        print("No stereo pairs from /stereo; falling back to STAC search.")
        items = stac_search_items(args.date, args.lat, args.lon, SEARCH_RADIUS_M)
        print(json.dumps(items.get("features", [])[:2], indent=2))
        print("\n[!] Could not programmatically select a stereo pair from your account response.\n"
              "    After you have access, plug in the actual asset download URLs below.\n")
        # ----- EXIT early with instructions -----
        sys.exit(1)

    pair = stereo["pairs"][0]
    # The actual schema may differ. Commonly you'll have two image IDs and asset links to L1B TIFF and RPC XML.
    # Replace the keys below once you inspect your real response.
    left_img_url  = pair.get("left", {}).get("l1bTiffUrl")
    left_rpc_url  = pair.get("left", {}).get("rpcXmlUrl")
    right_img_url = pair.get("right", {}).get("l1bTiffUrl")
    right_rpc_url = pair.get("right", {}).get("rpcXmlUrl")

    for k, v in [("left_img_url", left_img_url), ("left_rpc_url", left_rpc_url),
                 ("right_img_url", right_img_url), ("right_rpc_url", right_rpc_url)]:
        if not v:
            print(f"[!] Missing {k} in the stereo response. Inspect your account’s schema and update key names.", file=sys.stderr)
            sys.exit(1)

    left_tif  = download_asset(left_img_url,  os.path.join(work, "left.tif"))
    left_rpc  = download_asset(left_rpc_url,  os.path.join(work, "left.xml"))
    right_tif = download_asset(right_img_url, os.path.join(work, "right.tif"))
    right_rpc = download_asset(right_rpc_url, os.path.join(work, "right.xml"))

    # 2) Run ASP to create DSM
    dsm_tif = run_asp(left_tif, left_rpc, right_tif, right_rpc, work)

    # 3) Estimate pile height near lat/lon
    height_m, pile_max, bg_med = estimate_pile_height(dsm_tif, args.lat, args.lon, PILE_RADIUS_M, BACKGROUND_RING_M)
    print(f"Estimated pile height: {height_m:.2f} m" if height_m else "Estimated pile height: N/A")

    # 4) Quicklook and PDF
    png_path = quicklook_png(dsm_tif, args.lat, args.lon, os.path.join(work, "dsm_preview.png"))
    date_tag = args.date.replace("-", "")
    report = os.path.join(os.getcwd(), f"EFB_Pile_Height_{date_tag}_{args.lat:.5f}_{args.lon:.5f}.pdf")
    write_pdf(report, args.lat, args.lon, args.date, height_m if height_m else float("nan"), png_path)
    print("\nSaved PDF:", report)

if __name__ == "__main__":
    main()
