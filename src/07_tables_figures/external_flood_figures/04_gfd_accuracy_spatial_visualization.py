#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 04_gfd_accuracy_spatial_visualization.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 3
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
from pathlib import Path
import rasterio
from rasterio.warp import reproject, Resampling

# ===================== User Config =====================
CAMA_ROOT = Path(r"E:\洪水影响评估数据\CAMA\cama_cama_meanDepth_raw")
GFD_ROOT  = Path(r"E:\洪水影响评估数据\GFD")

OUT_ROOT  = Path(r"E:\洪水影响评估数据\CAMA_GFD_onefile_products")  # Original notebook comment normalized for the public code archive.
DEPTH_THR_M = 0.3

# External flood dataset comparison note.
# External flood dataset comparison note.
MASK_OUT_WHERE_GFD_INVALID = True
# =======================================================


def is_year_dir(p: Path) -> bool:
    return p.is_dir() and p.name.isdigit()


def cama_to_gfd_path(cama_fp: Path, year: str) -> Path:
    name = cama_fp.name
    if not name.endswith("_CAMA_meanDepth.tif"):
        raise ValueError(f"Unexpected CAMA filename: {name}")
    gfd_name = name.replace("_CAMA_meanDepth.tif", "_DFO_b1_flood.tif")
    return GFD_ROOT / year / gfd_name


def read_cama(cama_fp: Path):
    with rasterio.open(cama_fp) as src:
        depth = src.read(1).astype(np.float32)
        meta = src.meta.copy()
        crs = src.crs
        transform = src.transform
        nodata = src.nodata
    if nodata is None:
        nodata = -9999.0
    return depth, meta, crs, transform, float(nodata)


def warp_gfd_to_cama(gfd_fp: Path, dst_shape, dst_crs, dst_transform):
    with rasterio.open(gfd_fp) as src:
        gfd = src.read(1).astype(np.uint8)
        src_crs = src.crs
        src_transform = src.transform
        src_nodata = src.nodata
        if src_nodata is None:
            src_nodata = 255

    dst = np.full(dst_shape, 255, dtype=np.uint8)
    reproject(
        source=gfd,
        destination=dst,
        src_transform=src_transform,
        src_crs=src_crs,
        src_nodata=src_nodata,
        dst_transform=dst_transform,
        dst_crs=dst_crs,
        dst_nodata=255,
        resampling=Resampling.nearest
    )
    return dst


def write_class_tif(out_fp: Path, arr: np.ndarray, ref_meta: dict, crs, transform):
    meta = ref_meta.copy()
    meta.update({
        "driver": "GTiff",
        "dtype": "uint8",
        "count": 1,
        "nodata": 255,          # Original notebook comment normalized for the public code archive.
        "crs": crs,
        "transform": transform,
        "compress": "LZW"
    })
    out_fp.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(out_fp, "w", **meta) as dst:
        dst.write(arr.astype(np.uint8), 1)


def main():
    OUT_ROOT.mkdir(parents=True, exist_ok=True)

    years = sorted([p.name for p in CAMA_ROOT.iterdir() if is_year_dir(p)])
    if not years:
        raise FileNotFoundError(f"No year folders found under: {CAMA_ROOT}")

    for year in years:
        cama_year = CAMA_ROOT / year
        out_year = OUT_ROOT / year
        out_year.mkdir(parents=True, exist_ok=True)

        cama_files = sorted(cama_year.glob("DFO_*_CAMA_meanDepth.tif"))
        if not cama_files:
            print(f"[WARN] No CAMA tif in {cama_year}")
            continue

        print(f"[INFO] Year {year}: {len(cama_files)} events")

        for cama_fp in cama_files:
            gfd_fp = cama_to_gfd_path(cama_fp, year)
            if not gfd_fp.exists():
                print(f"[WARN] Missing GFD for {cama_fp.name}")
                continue

            depth, ref_meta, dst_crs, dst_transform, cama_nodata = read_cama(cama_fp)
            H, W = depth.shape

            cama_valid = np.isfinite(depth) & (depth != cama_nodata)
            cama_flood = cama_valid & (depth > 0)

            gfd_on_cama = warp_gfd_to_cama(gfd_fp, (H, W), dst_crs, dst_transform)
            gfd_valid = (gfd_on_cama != 255)
            gfd_flood = (gfd_on_cama == 1)
            gfd_nonflood = (gfd_on_cama == 0)

            # Original notebook comment normalized for the public code archive.
            out = np.zeros((H, W), dtype=np.uint8)

            # Original notebook comment normalized for the public code archive.
            # External flood dataset comparison note.
            out[~cama_valid] = 255
            if MASK_OUT_WHERE_GFD_INVALID:
                out[(cama_valid) & (~gfd_valid)] = 255

            # 1 = overlap
            overlap = cama_flood & gfd_flood
            if MASK_OUT_WHERE_GFD_INVALID:
                overlap = overlap & gfd_valid
            out[overlap] = 1

            # 2 = CAMA-only (GFD==0) AND depth>=thr
            nonoverlap_strong = cama_flood & gfd_nonflood & (depth >= DEPTH_THR_M)
            if MASK_OUT_WHERE_GFD_INVALID:
                nonoverlap_strong = nonoverlap_strong & gfd_valid
            out[nonoverlap_strong] = 2

            stem = cama_fp.name.replace("_CAMA_meanDepth.tif", "")
            out_fp = out_year / f"{stem}_class_overlap_or_camaOnly_ge{DEPTH_THR_M:.1f}m_onCAMA.tif"
            write_class_tif(out_fp, out, ref_meta, dst_crs, dst_transform)

            print(f"  [OK] {stem} -> {out_fp.name}")

    print("[DONE]")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 6
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


XLSX_PATH = r"E:\洪水影响评估数据\CSI_compare_raw_vs_proc_thr0p3.xlsx"
OUT_PNG_OVERLAY = r"E:\洪水影响评估数据\CSI_hist_overlay.png"
OUT_PNG_SIDE_BY_SIDE = r"E:\洪水影响评估数据\CSI_hist_side_by_side.png"

BINS = 30
XRANGE = (0.0, 1.0)   # Original notebook comment normalized for the public code archive.
DENSITY = False       # Original notebook comment normalized for the public code archive.


def _get_series(df, col):
    if col not in df.columns:
        raise KeyError(f"找不到列：{col}。现有列：{list(df.columns)}")
    s = pd.to_numeric(df[col], errors="coerce")
    s = s[np.isfinite(s)]
    # Original notebook comment normalized for the public code archive.
    s = s[(s >= XRANGE[0]) & (s <= XRANGE[1])]
    return s.to_numpy()


def plot_overlay_hist(csi_raw, csi_proc, out_png=None):
    # Original notebook comment normalized for the public code archive.
    edges = np.linspace(XRANGE[0], XRANGE[1], BINS + 1)

    plt.figure(figsize=(7, 4.5))
    plt.hist(csi_raw,  bins=edges, alpha=0.55, label="CSI_raw",  density=DENSITY)
    plt.hist(csi_proc, bins=edges, alpha=0.55, label="CSI_proc", density=DENSITY)

    plt.xlabel("CSI")
    plt.ylabel("Density" if DENSITY else "Count")
    plt.title("Histogram of CSI: raw vs processed")
    plt.xlim(XRANGE)
    plt.legend()
    plt.tight_layout()

    if out_png:
        plt.savefig(out_png, dpi=300)
    plt.show()


def plot_side_by_side_hist(csi_raw, csi_proc, out_png=None):
    edges = np.linspace(XRANGE[0], XRANGE[1], BINS + 1)

    plt.figure(figsize=(7, 4.5))
    # Original notebook comment normalized for the public code archive.
    raw_counts, _ = np.histogram(csi_raw, bins=edges, density=DENSITY)
    pro_counts, _ = np.histogram(csi_proc, bins=edges, density=DENSITY)

    centers = (edges[:-1] + edges[1:]) / 2
    width = (edges[1] - edges[0]) * 0.42

    plt.bar(centers - width/2, raw_counts, width=width, label="CSI_raw")
    plt.bar(centers + width/2, pro_counts, width=width, label="CSI_proc")

    plt.xlabel("CSI")
    plt.ylabel("Density" if DENSITY else "Count")
    plt.title("Histogram of CSI: raw vs processed (side-by-side)")
    plt.xlim(XRANGE)
    plt.legend()
    plt.tight_layout()

    if out_png:
        plt.savefig(out_png, dpi=300)
    plt.show()


def main():
    df = pd.read_excel(XLSX_PATH)

    csi_raw  = _get_series(df, "CSI_raw")
    csi_proc = _get_series(df, "CSI_proc")

    print(f"[INFO] N(CSI_raw)  = {csi_raw.size}")
    print(f"[INFO] N(CSI_proc) = {csi_proc.size}")
    print(f"[INFO] mean raw={np.nanmean(csi_raw):.4f}, mean proc={np.nanmean(csi_proc):.4f}")
    print(f"[INFO] median raw={np.nanmedian(csi_raw):.4f}, median proc={np.nanmedian(csi_proc):.4f}")

    # Original notebook comment normalized for the public code archive.
    plot_overlay_hist(csi_raw, csi_proc, out_png=OUT_PNG_OVERLAY)

    # Original notebook comment normalized for the public code archive.
    plot_side_by_side_hist(csi_raw, csi_proc, out_png=OUT_PNG_SIDE_BY_SIDE)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 9
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
from pathlib import Path
import rasterio
from rasterio.enums import Resampling
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import matplotlib.patches as mpatches

# ===================== User Config =====================
CLASS_ROOT = Path(r"E:\洪水影响评估数据\CAMA_GFD_onefile_products")

# Original notebook comment normalized for the public code archive.
PNG_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\accuracy\GFD_Flooded\png")

# Original notebook comment normalized for the public code archive.
MAX_SIDE = 2000

# Original notebook comment normalized for the public code archive.
PREFIX_YEAR_IN_FILENAME = True

# Original notebook comment normalized for the public code archive.
ADD_TITLE = True
ADD_LEGEND = True

# Original notebook comment normalized for the public code archive.
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
# =======================================================


def is_year_dir(p: Path) -> bool:
    return p.is_dir() and p.name.isdigit()


def read_uint8_with_downsample(tif_fp: Path, max_side: int = 2000) -> np.ndarray:
    """Read single-band uint8 raster; optionally downsample so max(H,W)<=max_side."""
    with rasterio.open(tif_fp) as src:
        h, w = src.height, src.width
        scale = max(h, w) / float(max_side)
        if scale <= 1.0:
            return src.read(1).astype(np.uint8)

        new_h = max(1, int(round(h / scale)))
        new_w = max(1, int(round(w / scale)))
        return src.read(
            1,
            out_shape=(new_h, new_w),
            resampling=Resampling.nearest
        ).astype(np.uint8)


def build_cmap_and_norm():
    """
    Display mapping:
      0 -> white
      1 -> red     (overlap)
      2 -> blue    (CAMA-only & depth>=thr)
      255 -> lightgray (NoData)  [we remap 255 -> 3 for display]
    """
    colors = ["white", "red", "blue", "lightgray"]
    cmap = ListedColormap(colors)

    bounds = [-0.5, 0.5, 1.5, 2.5, 3.5]
    norm = BoundaryNorm(bounds, cmap.N)

    legend = [
        mpatches.Patch(color="red", label="1: Overlap"),
        mpatches.Patch(color="blue", label="2: CAMA-only & depth>=thr"),
        mpatches.Patch(color="white", label="0: Other"),
        mpatches.Patch(color="lightgray", label="255: NoData/Invalid"),
    ]
    return cmap, norm, legend


def unique_path(out_dir: Path, base_name: str) -> Path:
    """
    Avoid overwrite if the same name already exists: add _v2/_v3...
    """
    fp = out_dir / base_name
    if not fp.exists():
        return fp
    stem = fp.stem
    suf = fp.suffix
    k = 2
    while True:
        cand = out_dir / f"{stem}_v{k}{suf}"
        if not cand.exists():
            return cand
        k += 1


def main():
    PNG_DIR.mkdir(parents=True, exist_ok=True)
    cmap, norm, legend_patches = build_cmap_and_norm()

    years = sorted([p for p in CLASS_ROOT.iterdir() if is_year_dir(p)])
    if not years:
        raise FileNotFoundError(f"No year folders found under: {CLASS_ROOT}")

    total = 0

    for ydir in years:
        year = ydir.name
        tif_files = sorted([p for p in ydir.glob("*.tif") if p.is_file()])
        if not tif_files:
            print(f"[WARN] {year}: no tif files.")
            continue

        print(f"[INFO] {year}: {len(tif_files)} tif files")

        for tif_fp in tif_files:
            arr = read_uint8_with_downsample(tif_fp, MAX_SIDE)

            # Remap nodata 255 -> 3 for display
            disp = arr.astype(np.int16)
            disp[disp == 255] = 3

            plt.figure(figsize=(7.5, 6.0), dpi=150)
            plt.imshow(disp, cmap=cmap, norm=norm, interpolation="nearest")
            plt.axis("off")

            if ADD_TITLE:
                title = tif_fp.stem
                if PREFIX_YEAR_IN_FILENAME:
                    title = f"{year} | {title}"
                plt.title(title, fontsize=10)

            if ADD_LEGEND:
                plt.legend(
                    handles=legend_patches,
                    loc="lower center",
                    ncol=2,
                    frameon=True,
                    fontsize=9
                )

            # Output filename
            if PREFIX_YEAR_IN_FILENAME:
                base = f"{year}__{tif_fp.stem}.png"
            else:
                base = f"{tif_fp.stem}.png"

            out_png = unique_path(PNG_DIR, base)

            plt.tight_layout(pad=0.2)
            plt.savefig(out_png, dpi=200)
            plt.close()

            total += 1
            if total % 50 == 0:
                print(f"  [INFO] exported {total} pngs ...")

    print(f"[DONE] Total PNG exported: {total}")
    print(f"[OUT] {PNG_DIR}")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 13
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_gfd_accuracy_spatial_visualization.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import rasterio
from rasterio.warp import reproject, Resampling


# =============================================================================
CAMA_ROOT = Path(r"E:\洪水影响评估数据\CAMA\cama_cama_meanDepth_raw")
GFD_ROOT  = Path(r"E:\洪水影响评估数据\GFD")

DEPTH_THR_M = 0.3

# External flood dataset comparison note.
STRICT_VALID_DOMAIN = True

# Original notebook comment normalized for the public code archive.
OUT_XLSX = Path(r"E:\洪水影响评估数据\CSI_compare_raw_vs_proc_thr0p3.xlsx")

# Original notebook comment normalized for the public code archive.
SAVE_DIAG_RASTER = True
DIAG_OUT_ROOT = Path(r"E:\洪水影响评估数据\CSI_diag_rasters_thr0p3")
# ===================================================


NODATA_GFD_DEFAULT = 255
NODATA_DIAG = 255


def is_year_dir(p: Path) -> bool:
    return p.is_dir() and p.name.isdigit()


def cama_to_gfd_path(cama_fp: Path, year: str) -> Path:
    """
    CAMA: DFO_1627_From_20000830_to_20000910_CAMA_meanDepth.tif
    GFD : DFO_1627_From_20000830_to_20000910_DFO_b1_flood.tif
    """
    name = cama_fp.name
    if not name.endswith("_CAMA_meanDepth.tif"):
        raise ValueError(f"Unexpected CAMA filename: {name}")
    prefix = name.replace("_CAMA_meanDepth.tif", "")
    gfd_name = f"{prefix}_DFO_b1_flood.tif"
    return GFD_ROOT / year / gfd_name, prefix


def safe_div(num: float, den: float) -> float:
    if den <= 0:
        return float("nan")
    return float(num) / float(den)


def warp_gfd_to_cama_grid(gfd_fp: Path, dst_shape, dst_crs, dst_transform) -> np.ndarray:
    with rasterio.open(gfd_fp) as src:
        gfd = src.read(1).astype(np.uint8)
        src_crs = src.crs
        src_transform = src.transform
        src_nodata = src.nodata
        if src_nodata is None:
            src_nodata = NODATA_GFD_DEFAULT

    dst = np.full(dst_shape, NODATA_GFD_DEFAULT, dtype=np.uint8)
    reproject(
        source=gfd,
        destination=dst,
        src_transform=src_transform,
        src_crs=src_crs,
        src_nodata=src_nodata,
        dst_transform=dst_transform,
        dst_crs=dst_crs,
        dst_nodata=NODATA_GFD_DEFAULT,
        resampling=Resampling.nearest
    )
    return dst


def write_uint8_geotiff(out_fp: Path, arr: np.ndarray, ref_meta: dict, crs, transform):
    meta = ref_meta.copy()
    meta.update({
        "driver": "GTiff",
        "dtype": "uint8",
        "count": 1,
        "nodata": NODATA_DIAG,
        "crs": crs,
        "transform": transform,
        "compress": "LZW",
    })
    out_fp.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(out_fp, "w", **meta) as dst:
        dst.write(arr.astype(np.uint8), 1)


def main():
    years = sorted([p.name for p in CAMA_ROOT.iterdir() if is_year_dir(p)])
    if not years:
        raise FileNotFoundError(f"在 CAMA_ROOT 下未找到年份文件夹：{CAMA_ROOT}")

    rows = []

    print("year,event,CSI_raw,CSI_proc")

    for year in years:
        cama_year_dir = CAMA_ROOT / year
        cama_files = sorted([p for p in cama_year_dir.glob("DFO_*_CAMA_meanDepth.tif") if p.is_file()])
        if not cama_files:
            continue

        for cama_fp in cama_files:
            gfd_fp, prefix = cama_to_gfd_path(cama_fp, year)
            if not gfd_fp.exists():
                # Original notebook comment normalized for the public code archive.
                rows.append({
                    "year": int(year),
                    "event": prefix,
                    "CSI_raw": np.nan,
                    "CSI_proc": np.nan,
                    "note": "missing_gfd",
                })
                print(f"{year},{prefix},nan,nan")
                continue

            # ---- read CAMA depth ----
            with rasterio.open(cama_fp) as cama_src:
                depth = cama_src.read(1).astype(np.float32)
                ref_meta = cama_src.meta.copy()
                dst_crs = cama_src.crs
                dst_transform = cama_src.transform
                cama_nodata = cama_src.nodata

            if cama_nodata is None:
                cama_nodata = -9999.0

            H, W = depth.shape

            cama_valid = np.isfinite(depth) & (depth != float(cama_nodata))
            pred_raw = cama_valid & (depth > 0)

            # ---- warp GFD ----
            gfd = warp_gfd_to_cama_grid(gfd_fp, (H, W), dst_crs, dst_transform)
            gfd_valid = (gfd != NODATA_GFD_DEFAULT)
            obs = (gfd == 1)

            # ---- valid domain ----
            if STRICT_VALID_DOMAIN:
                valid = cama_valid & gfd_valid
            else:
                valid = cama_valid

            # ---- CSI_raw (standard confusion) ----
            TP_raw = int(np.count_nonzero(valid & pred_raw & obs))
            FP_raw = int(np.count_nonzero(valid & pred_raw & (~obs)))
            FN_raw = int(np.count_nonzero(valid & (~pred_raw) & obs))
            CSI_raw = safe_div(TP_raw, TP_raw + FP_raw + FN_raw)

            # ---- CSI_proc (your post-processed/diagnostic definition) ----
            # overlap = TP area (uses obs)
            overlap = valid & pred_raw & obs
            # strong non-overlap FP (depth>=thr, obs=0)
            strong_fp = valid & pred_raw & (~obs) & (depth >= DEPTH_THR_M)
            pred_proc = overlap | strong_fp

            TP_proc = int(np.count_nonzero(valid & pred_proc & obs))
            FP_proc = int(np.count_nonzero(valid & pred_proc & (~obs)))
            FN_proc = int(np.count_nonzero(valid & (~pred_proc) & obs))
            CSI_proc = safe_div(TP_proc, TP_proc + FP_proc + FN_proc)

            # ---- print only two CSI ----
            print(f"{year},{prefix},{CSI_raw:.6f},{CSI_proc:.6f}")

            # ---- record ----
            rows.append({
                "year": int(year),
                "event": prefix,
                "CSI_raw": CSI_raw,
                "CSI_proc": CSI_proc,
                # Original notebook comment normalized for the public code archive.
                "TP_raw": TP_raw, "FP_raw": FP_raw, "FN_raw": FN_raw,
                "TP_proc": TP_proc, "FP_proc": FP_proc, "FN_proc": FN_proc,
                "valid_pixels": int(np.count_nonzero(valid)),
                "FP_removed_by_thr": int(max(0, FP_raw - FP_proc)),
                "note": "",
            })

            # ---- optional: diagnostic raster for visualization ----
            if SAVE_DIAG_RASTER:
                diag = np.zeros((H, W), dtype=np.uint8)

                # nodata / invalid
                diag[~cama_valid] = NODATA_DIAG
                if STRICT_VALID_DOMAIN:
                    diag[cama_valid & (~gfd_valid)] = NODATA_DIAG

                # TP / FP weak / FP strong / FN
                tp_mask = valid & pred_raw & obs
                fp_weak = valid & pred_raw & (~obs) & (depth > 0) & (depth < DEPTH_THR_M)
                fp_strg = valid & pred_raw & (~obs) & (depth >= DEPTH_THR_M)
                fn_mask = valid & (~pred_raw) & obs

                diag[tp_mask] = 10
                diag[fp_weak] = 20
                diag[fp_strg] = 21
                diag[fn_mask] = 30

                out_fp = (DIAG_OUT_ROOT / year / f"{prefix}_diag_TP_FPweak_FPstrong_FN_thr{DEPTH_THR_M:.1f}.tif")
                write_uint8_geotiff(out_fp, diag, ref_meta, dst_crs, dst_transform)

    # ---- save xlsx ----
    df = pd.DataFrame(rows)
    OUT_XLSX.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(OUT_XLSX, index=False)
    print(f"\n[XLSX] saved -> {OUT_XLSX}")


if __name__ == "__main__":
    main()
