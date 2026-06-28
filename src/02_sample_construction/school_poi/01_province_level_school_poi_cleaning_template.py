#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Archived school POI / education-facility workflow stage.

Workflow label : Province-level school POI cleaning template
Category       : province_template
Source         : representative province notebooks
Generated for  : GitHub code archive

Important
---------
This file preserves code cells exported from the user's original Jupyter
notebooks. It is intended for auditability. It does not include raw POI data,
geospatial rasters, or processed school-level outputs.
"""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ==============================================================================
# Province-level processing note.
# Source notebook: internal original notebook (non-public source filename omitted).
# ==============================================================================

# ------------------------------------------------------------------------------
# Notebook cell 1
# ------------------------------------------------------------------------------
import os
import re
import math
import json

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.transform import rowcol
from rasterio.windows import Window
from tqdm import tqdm
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

# =============================================================================

SCHOOL_SHP = r"D:\GISdata\CHINA_SCHOOL\anhui_小学_中学.shp"
EULUC_SHP  = r"D:\GISdata\EULUC\24anhui.shp"

CLCD_ROOT     = r"D:\GISdata\landcover"
CLCD_PROVINCE = "anhui"   # CLCD_v01_YYYY_albert_anhui.tif

NTL_ROOT = r"D:\GISdata\Night_Light\anhui"
POP_ROOT = r"D:\GISdata\PopulationDensity\worldpop安徽省"

RESULT_ROOT = r"D:\GISdata\school_result"
L1L2_DIR    = os.path.join(RESULT_ROOT, "L1L2")
L3_DIR      = os.path.join(RESULT_ROOT, "L3")

os.makedirs(L1L2_DIR, exist_ok=True)
os.makedirs(L3_DIR, exist_ok=True)

# School POI processing note.
L1L2_SHP  = os.path.join(L1L2_DIR, "anhui_school.shp")
L1L2_XLSX = os.path.join(L1L2_DIR, "anhui_school.xlsx")
L3_SHP    = os.path.join(L3_DIR, "anhui_school.shp")
L3_XLSX   = os.path.join(L3_DIR, "anhui_school.xlsx")

BUFFER_RADIUS_M = 1800.0
STABLE_YEARS_K  = 1
SIM_THRESHOLD   = 0.9

IMP_CLASS   = 8
ALL_CLASSES = np.arange(0, 11, dtype=int)

EULUC_EDU_CLASS     = 7
EULUC_URBAN_CLASSES = {0, 1, 2, 3, 6, 8, 9, 10}

RF_N_ESTIMATORS = 300
RF_MAX_DEPTH    = 10
RF_RANDOM_STATE = 42

# =============================================================================

def index_clcd_files():
    year_files = {}
    ref_crs = ref_transform = None
    ref_w = ref_h = None
    ref_nodata = None

    pattern = re.compile(
        rf"CLCD_v01_(\d{{4}})_albert_{CLCD_PROVINCE}",
        re.IGNORECASE
    )

    for root, _, files in os.walk(CLCD_ROOT):
        for fname in files:
            if not fname.lower().endswith(".tif"):
                continue
            m = pattern.search(fname)
            if not m:
                continue
            year = int(m.group(1))
            path = os.path.join(root, fname)
            with rasterio.open(path) as src:
                if ref_crs is None:
                    ref_crs = src.crs
                    ref_transform = src.transform
                    ref_w, ref_h = src.width, src.height
                    ref_nodata = src.nodata
                else:
                    if src.crs != ref_crs:
                        raise ValueError(f"CLCD {year} CRS 不一致")
                    if src.transform != ref_transform or src.width != ref_w or src.height != ref_h:
                        raise ValueError(f"CLCD {year} 网格参数不一致")
            year_files[year] = path

    if not year_files:
        raise RuntimeError("未找到 CLCD_v01_YYYY_albert_anhui.tif")

    years = sorted(year_files.keys())
    if 2024 not in years:
        raise RuntimeError("缺少 2024 年 CLCD")

    print("[INFO] Notebook progress message.", years)
    return years, year_files, ref_crs, ref_transform, ref_w, ref_h, ref_nodata


def index_ntl_files(expected_crs):
    year_files = {}
    for fname in os.listdir(NTL_ROOT):
        if not fname.lower().endswith(".tif"):
            continue
        m = re.search(r'(19|20)\d{2}', fname)
        if not m:
            continue
        year = int(m.group(0))
        path = os.path.join(NTL_ROOT, fname)
        with rasterio.open(path) as src:
            if src.crs != expected_crs:
                raise ValueError(f"夜光 {fname} CRS 与 CLCD 不一致")
        year_files[year] = path

    if not year_files:
        raise RuntimeError("夜光目录无有效 tif")

    years = sorted(year_files.keys())
    print("[INFO] Notebook progress message.", years)
    return years, year_files


def index_pop_files():
    year_files = {}
    ref_crs = None
    ref_transform = None

    for fname in os.listdir(POP_ROOT):
        if not fname.lower().endswith(".tif"):
            continue
        m = re.search(r'(19|20)\d{2}', fname)
        if not m:
            continue
        year = int(m.group(0))
        path = os.path.join(POP_ROOT, fname)
        with rasterio.open(path) as src:
            if ref_crs is None:
                ref_crs = src.crs
                ref_transform = src.transform
            else:
                if src.crs != ref_crs or src.transform != ref_transform:
                    raise ValueError(f"人口 {fname} CRS/transform 不一致")
        year_files[year] = path

    if not year_files:
        raise RuntimeError("人口密度目录无有效 tif")

    years = sorted(year_files.keys())
    print("[INFO] Notebook progress message.", years)
    return years, year_files, ref_crs, ref_transform

# =============================================================================

def precompute_buffer_mask_m(radius_m, transform):
    res_x = abs(transform.a)
    res_y = abs(transform.e)
    res = (res_x + res_y) / 2.0
    r_px = int(math.ceil(radius_m / res))
    ys, xs = np.ogrid[-r_px:r_px+1, -r_px:r_px+1]
    dist2 = (xs * res)**2 + (ys * res)**2
    mask = dist2 <= radius_m**2
    return mask, r_px


def precompute_buffer_mask_pop(radius_m, transform, lat0=25.0):
    cell_deg_x = abs(transform.a)
    cell_deg_y = abs(transform.e)

    cell_m_x = 111320.0 * math.cos(math.radians(lat0)) * cell_deg_x
    cell_m_y = 111320.0 * cell_deg_y
    cell_m   = (cell_m_x + cell_m_y) / 2.0

    r_px = int(math.ceil(radius_m / cell_m))
    r_px = max(r_px, 1)

    ys, xs = np.ogrid[-r_px:r_px+1, -r_px:r_px+1]
    dist_x_m = xs * cell_m_x
    dist_y_m = ys * cell_m_y
    dist2 = dist_x_m**2 + dist_y_m**2
    mask = dist2 <= radius_m**2
    return mask, r_px

# =============================================================================

def buffer_stats_from_src(src, row, col, mask, r_px, all_classes, imp_class, nodata):
    h, w = src.height, src.width
    if not (0 <= row < h and 0 <= col < w):
        return np.nan, np.zeros(len(all_classes)), 0.0

    r0 = max(0, row - r_px)
    r1 = min(h, row + r_px + 1)
    c0 = max(0, col - r_px)
    c1 = min(w, col + r_px + 1)
    win = Window(c0, r0, c1 - c0, r1 - r0)

    sub = src.read(1, window=win)

    mr0 = r_px - (row - r0)
    mr1 = mr0 + (r1 - r0)
    mc0 = r_px - (col - c0)
    mc1 = mc0 + (c1 - c0)
    sub_mask = mask[mr0:mr1, mc0:mc1]

    if nodata is not None:
        valid = sub_mask & (sub != nodata)
    else:
        valid = sub_mask

    if not np.any(valid):
        return np.nan, np.zeros(len(all_classes)), 0.0

    vals = sub[valid]
    uniq, cnt = np.unique(vals, return_counts=True)

    probs = np.zeros(len(all_classes), float)
    total = cnt.sum()
    if total > 0:
        idx_map = {int(v): i for i, v in enumerate(all_classes)}
        for u, c in zip(uniq, cnt):
            j = idx_map.get(int(u))
            if j is not None:
                probs[j] = c / total

    central = float(sub[row - r0, col - c0])
    if nodata is not None and central == nodata:
        central = np.nan

    imp_ratio = 0.0
    if imp_class in all_classes:
        imp_idx = int(np.where(all_classes == imp_class)[0][0])
        imp_ratio = probs[imp_idx]

    return central, probs, float(imp_ratio)


def buffer_mean_from_src(src, row, col, mask, r_px, nodata, treat_zero_as_nan=False):
    h, w = src.height, src.width
    if not (0 <= row < h and 0 <= col < w):
        return np.nan

    r0 = max(0, row - r_px)
    r1 = min(h, row + r_px + 1)
    c0 = max(0, col - r_px)
    c1 = min(w, col + r_px + 1)
    win = Window(c0, r0, c1 - c0, r1 - r0)

    sub = src.read(1, window=win)

    mr0 = r_px - (row - r0)
    mr1 = mr0 + (r1 - r0)
    mc0 = r_px - (col - c0)
    mc1 = mc0 + (c1 - c0)
    sub_mask = mask[mr0:mr1, mc0:mc1]

    if nodata is not None:
        valid = sub_mask & (sub != nodata)
    else:
        valid = sub_mask

    if not np.any(valid):
        return np.nan

    vals = sub[valid].astype(float)
    if treat_zero_as_nan:
        vals[vals == 0.0] = np.nan
    if np.all(np.isnan(vals)):
        return np.nan

    return float(np.nanmean(vals))

# =============================================================================

def compute_similarity(p_t, p_ref):
    return 1.0 - 0.5 * np.abs(p_t - p_ref).sum()


def detect_jump_year(series, years, low_q=0.2, high_q=0.6, k=3):
    arr = np.array(series, float)
    mask = ~np.isnan(arr)
    if mask.sum() < k + 2:
        return None

    vals = arr[mask]
    vmin, vmax = np.min(vals), np.max(vals)
    if vmax - vmin <= 1e-6:
        return None

    low_thr  = vmin + (vmax - vmin) * low_q
    high_thr = vmin + (vmax - vmin) * high_q

    n = len(arr)
    for i in range(n - k + 1):
        block = arr[i:i+k]
        if np.any(np.isnan(block)):
            continue
        if np.all(block >= high_thr):
            before = arr[:i]
            before = before[~np.isnan(before)]
            if before.size == 0 or np.max(before) <= low_thr:
                if np.all(arr[i:][~np.isnan(arr[i:])] >= high_thr):
                    return years[i]
    return None


def reverse_stable_run(stable, end_idx, k):
    i = end_idx
    while i >= 0 and stable[i]:
        i -= 1
    start = i + 1
    if end_idx - start + 1 >= k:
        return start
    return None

# =============================================================================

def compute_all_features():
    years_clcd, clcd_files, clcd_crs, clcd_transform, _, _, _ = index_clcd_files()
    years_ntl, ntl_files = index_ntl_files(clcd_crs)
    years_pop, pop_files, pop_crs, pop_transform = index_pop_files()

    # Original notebook comment normalized for the public code archive.
    euluc = gpd.read_file(EULUC_SHP)
    if euluc.crs is None:
        raise ValueError("EULUC 无 CRS")
    if "Class" not in euluc.columns:
        raise ValueError("EULUC 缺 Class 字段")
    euluc = euluc.to_crs(clcd_crs)
    euluc = euluc[["Class", "geometry"]].rename(columns={"Class": "euluc_cls"})

    # Original notebook comment normalized for the public code archive.
    schools = gpd.read_file(SCHOOL_SHP)
    if schools.crs is None:
        raise ValueError("学校点 无 CRS")
    schools = schools.to_crs(clcd_crs)
    schools["sid"] = np.arange(len(schools), dtype=int)

    # Original notebook comment normalized for the public code archive.
    schools = gpd.sjoin(schools, euluc, how="left", predicate="within").drop(columns=["index_right"])
    euluc_class = schools["euluc_cls"].to_numpy()
    is_urban = np.isin(euluc_class, list(EULUC_URBAN_CLASSES) + [EULUC_EDU_CLASS])

    # Original notebook comment normalized for the public code archive.
    xs = schools.geometry.x.to_numpy()
    ys = schools.geometry.y.to_numpy()

    # CLCD index
    rows_clcd, cols_clcd = rowcol(clcd_transform, xs, ys, op=np.floor)
    rows_clcd = rows_clcd.astype(int)
    cols_clcd = cols_clcd.astype(int)

    # Original notebook comment normalized for the public code archive.
    with rasterio.open(ntl_files[years_ntl[0]]) as src:
        ntl_transform = src.transform
        ntl_nodata    = src.nodata
    rows_ntl, cols_ntl = rowcol(ntl_transform, xs, ys, op=np.floor)
    rows_ntl = rows_ntl.astype(int)
    cols_ntl = cols_ntl.astype(int)

    # Original notebook comment normalized for the public code archive.
    schools_pop = schools.to_crs(pop_crs)
    xs_pop = schools_pop.geometry.x.to_numpy()
    ys_pop = schools_pop.geometry.y.to_numpy()
    rows_pop, cols_pop = rowcol(pop_transform, xs_pop, ys_pop, op=np.floor)
    rows_pop = rows_pop.astype(int)
    cols_pop = cols_pop.astype(int)

    n_pts  = len(schools)
    n_clcd = len(years_clcd)
    n_ntl  = len(years_ntl)
    n_pop  = len(years_pop)
    n_cls  = len(ALL_CLASSES)

    print("[INFO] Notebook progress message.", n_pts)

    # buffer mask
    mask_clcd, rpx_clcd = precompute_buffer_mask_m(BUFFER_RADIUS_M, clcd_transform)
    mask_ntl,  rpx_ntl  = precompute_buffer_mask_m(BUFFER_RADIUS_M, ntl_transform)
    mask_pop,  rpx_pop  = precompute_buffer_mask_pop(BUFFER_RADIUS_M, pop_transform, lat0=25.0)

    # allocate
    clcd_ts = np.full((n_pts, n_clcd), np.nan, float)
    lc_probs = np.zeros((n_pts, n_clcd, n_cls), float)
    imp_ts = np.zeros((n_pts, n_clcd), float)

    ntl_ts = np.full((n_pts, n_ntl), np.nan, float)
    pop_ts = np.full((n_pts, n_pop), np.nan, float)

    # CLCD
    for j, y in enumerate(tqdm(years_clcd, desc="Processing", ncols=80)):
        path = clcd_files[y]
        with rasterio.open(path) as src:
            nodata = src.nodata
            for i in range(n_pts):
                val, probs, imp = buffer_stats_from_src(
                    src,
                    rows_clcd[i], cols_clcd[i],
                    mask_clcd, rpx_clcd,
                    ALL_CLASSES, IMP_CLASS, nodata
                )
                clcd_ts[i, j] = val
                lc_probs[i, j, :] = probs
                imp_ts[i, j] = imp

    # Original notebook comment normalized for the public code archive.
    for j, y in enumerate(tqdm(years_ntl, desc="Processing", ncols=80)):
        path = ntl_files[y]
        with rasterio.open(path) as src:
            nodata = src.nodata if src.nodata is not None else ntl_nodata
            for i in range(n_pts):
                ntl_ts[i, j] = buffer_mean_from_src(
                    src,
                    rows_ntl[i], cols_ntl[i],
                    mask_ntl, rpx_ntl,
                    nodata,
                    treat_zero_as_nan=False
                )

    # Original notebook comment normalized for the public code archive.
    for j, y in enumerate(tqdm(years_pop, desc="Processing", ncols=80)):
        path = pop_files[y]
        with rasterio.open(path) as src:
            nodata = src.nodata
            for i in range(n_pts):
                v = buffer_mean_from_src(
                    src,
                    rows_pop[i], cols_pop[i],
                    mask_pop, rpx_pop,
                    nodata,
                    treat_zero_as_nan=True
                )
                pop_ts[i, j] = v

    return (years_clcd, years_ntl, years_pop,
            clcd_ts, lc_probs, imp_ts, ntl_ts, pop_ts,
            euluc_class, is_urban, schools)

# =============================================================================

def rule_based_inference(years_clcd, years_ntl, years_pop,
                         clcd_ts, lc_probs, imp_ts, ntl_ts, pop_ts,
                         euluc_class, is_urban):

    n_pts = clcd_ts.shape[0]
    idx_2024 = years_clcd.index(2024)
    idx_2022 = years_clcd.index(2022) if 2022 in years_clcd else None

    case_type = []
    r_min = []
    r_max = []
    flags_json = []
    notes = []

    for i in tqdm(range(n_pts), desc="Processing", ncols=80):
        lc = clcd_ts[i, :]
        probs = lc_probs[i, :, :]
        imp = imp_ts[i, :]
        ntl = ntl_ts[i, :]
        pop = pop_ts[i, :]
        eu = euluc_class[i]
        urban = bool(is_urban[i])

        flags = {
            "clcd_pix": False,
            "clcd_env": False,
            "ntl": False,
            "pop": False,
            "edu": False,
            "urban": False
        }
        note = ""
        ctype = "D_NoDate"
        ymin = None
        ymax = None

        # Original notebook comment normalized for the public code archive.
        val_2024 = lc[idx_2024]
        if not np.isnan(val_2024) and int(val_2024) == IMP_CLASS:
            stable = np.array(
                [(not np.isnan(v) and int(v) == IMP_CLASS) for v in lc],
                dtype=bool
            )
            start_idx = reverse_stable_run(stable, idx_2024, STABLE_YEARS_K)
            if start_idx is not None:
                if start_idx == 0 and np.all(stable):
                    ctype = "A_CLCD_left"
                    ymin = None
                    ymax = years_clcd[0]
                    flags["clcd_pix"] = True
                    note = "impervious_since_first_year"
                else:
                    ctype = "A_CLCD_direct"
                    ymin = years_clcd[start_idx]
                    ymax = 2024
                    flags["clcd_pix"] = True

        # Original notebook comment normalized for the public code archive.
        if (not ctype.startswith("A_")) and (not np.isnan(eu)) and int(eu) == EULUC_EDU_CLASS and idx_2022 is not None:
            flags["edu"] = True
            pref = probs[idx_2024, :]
            sim = np.array([
                compute_similarity(probs[j, :], pref)
                for j in range(len(years_clcd))
            ])
            stable = sim >= SIM_THRESHOLD

            if np.all(stable[idx_2022:idx_2024+1]):
                start_idx = reverse_stable_run(stable, idx_2022, STABLE_YEARS_K)
                if start_idx is not None:
                    ymin = years_clcd[start_idx]
                    ymax = 2022
                    flags["clcd_env"] = True

                    t_ntl = detect_jump_year(ntl, years_ntl) if not np.all(np.isnan(ntl)) else None
                    t_pop = detect_jump_year(pop, years_pop) if not np.all(np.isnan(pop)) else None
                    ok_ntl = (t_ntl is None) or (t_ntl <= ymax)
                    ok_pop = (t_pop is None) or (t_pop <= ymax)

                    if ok_ntl and ok_pop:
                        ctype = "B_EU_edu_s"
                    else:
                        ctype = "B_EU_edu_w"
                        note = "ntl_or_pop_late"
                        if t_ntl is not None:
                            flags["ntl"] = True
                        if t_pop is not None:
                            flags["pop"] = True
                else:
                    ctype = "B_EU_edu_u"
                    note = "no_long_stable_before_2022"
            else:
                ctype = "B_EU_edu_u"
                note = "env_changed_after_2022"

        # Original notebook comment normalized for the public code archive.
        if (not ctype.startswith("A_")) and (not ctype.startswith("B_")) \
           and (not np.isnan(eu)) and int(eu) in EULUC_URBAN_CLASSES:
            flags["urban"] = True

            t_imp = detect_jump_year(imp, years_clcd)
            t_ntl = detect_jump_year(ntl, years_ntl) if not np.all(np.isnan(ntl)) else None
            t_pop = detect_jump_year(pop, years_pop) if not np.all(np.isnan(pop)) else None

            cand = []
            if t_imp is not None:
                cand.append(t_imp)
                flags["clcd_pix"] = True
            if t_ntl is not None:
                cand.append(t_ntl)
                flags["ntl"] = True
            if t_pop is not None:
                cand.append(t_pop)
                flags["pop"] = True

            if cand:
                t_urban = max(cand)
                ymin = t_urban
                ymax = 2024
                ctype = "C_urban"
            else:
                ctype = "C_urban_N"
                note = "no_jump"

        if ctype == "D_NoDate" and urban:
            flags["urban"] = True

        case_type.append(ctype)
        r_min.append(ymin)
        r_max.append(ymax)
        flags_json.append(json.dumps(flags, ensure_ascii=False))
        notes.append(note)

    return case_type, r_min, r_max, flags_json, notes

# =============================================================================

def build_ml_dataset(years_clcd, years_ntl, years_pop,
                     imp_ts, ntl_ts, pop_ts,
                     is_urban,
                     case_type, r_min, r_max):

    n = imp_ts.shape[0]
    idx_2024 = years_clcd.index(2024)

    def safe_jump(arr2d, years):
        res = []
        for i in range(n):
            arr = arr2d[i, :]
            if np.all(np.isnan(arr)):
                res.append(np.nan)
            else:
                res.append(detect_jump_year(arr, years))
        return np.array(res, float)

    imp_jump = safe_jump(imp_ts, years_clcd)
    ntl_jump = safe_jump(ntl_ts, years_ntl)
    pop_jump = safe_jump(pop_ts, years_pop)

    imp_2024 = imp_ts[:, idx_2024]
    ntl_latest = np.nan_to_num(ntl_ts[:, -1], nan=0.0)
    pop_latest = np.nan_to_num(pop_ts[:, -1], nan=0.0)

    def encode_year(arr, ref=2024):
        arr = arr.astype(float)
        miss = np.isnan(arr)
        val = np.where(miss, 0, ref - arr)
        return val, miss.astype(int)

    f_impjmp, m_impjmp = encode_year(imp_jump)
    f_ntljmp, m_ntljmp = encode_year(ntl_jump)
    f_popjmp, m_popjmp = encode_year(pop_jump)

    X = np.column_stack([
        f_impjmp, m_impjmp,
        f_ntljmp, m_ntljmp,
        f_popjmp, m_popjmp,
        imp_2024,
        ntl_latest,
        pop_latest,
        is_urban.astype(int)
    ])

    # Original notebook comment normalized for the public code archive.
    level1_mask = np.array([
        (ct == "A_CLCD_direct") or (ct == "B_EU_edu_s")
        for ct in case_type
    ])

    y = np.array([
        r_min[i] if level1_mask[i] and r_min[i] is not None else np.nan
        for i in range(n)
    ], dtype=float)

    meta = {
        "imp_jump_year": imp_jump,
        "ntl_jump_year": ntl_jump,
        "pop_jump_year": pop_jump,
        "imp_2024": imp_2024,
        "ntl_latest": ntl_latest,
        "pop_latest": pop_latest,
        "level1_mask": level1_mask,
        "y_level1": y
    }

    return X, meta

# =============================================================================

def train_rf_model(X, meta):
    level1 = meta["level1_mask"]
    y = meta["y_level1"]
    idx = np.where(~np.isnan(y) & level1)[0]

    if idx.size < 50:
        print("[INFO] Notebook progress message.")
        return None

    X_train = X[idx, :]
    y_train = y[idx]

    X_tr, X_te, y_tr, y_te = train_test_split(
        X_train, y_train, test_size=0.2, random_state=RF_RANDOM_STATE
    )

    rf = RandomForestRegressor(
        n_estimators=RF_N_ESTIMATORS,
        max_depth=RF_MAX_DEPTH,
        random_state=RF_RANDOM_STATE,
        n_jobs=-1
    )
    rf.fit(X_tr, y_tr)

    if X_te.shape[0] > 0:
        pred = rf.predict(X_te)
        mae = float(np.mean(np.abs(pred - y_te)))
        print("[INFO] Notebook progress message.")

    return rf

# =============================================================================

def fuse_rule_and_model(X, meta, case_type, r_min, r_max, rf):
    n = X.shape[0]
    level1 = meta["level1_mask"]

    if rf is not None:
        model_pred = rf.predict(X)
        model_pred = np.clip(model_pred, 1950, 2025)
    else:
        model_pred = np.full(n, np.nan)

    build_year = []
    out_min = []
    out_max = []
    CI = []
    fuse_note = []

    for i in range(n):
        ct   = case_type[i]
        rmin = r_min[i]
        rmax = r_max[i]
        mp   = None if np.isnan(model_pred[i]) else float(model_pred[i])

        est = None
        cmin = rmin
        cmax = rmax
        ci = "NoDate"
        note = ""

        if level1[i] and rmin is not None:
            est  = float(rmin)
            cmin = float(rmin)
            cmax = float(rmax) if rmax is not None else float(rmin)
            ci   = "L1"
            note = "rule_strong"
        else:
            if rmin is not None or rmax is not None:
                if rmin is not None and rmax is not None:
                    if mp is not None and rmin <= mp <= rmax:
                        est = mp
                        width = rmax - rmin
                        if width <= 5:
                            ci = "L1"
                        elif width <= 10:
                            ci = "L2"
                        else:
                            ci = "L3"
                        note = "model_in_rule"
                    else:
                        est = (rmin + rmax) / 2.0
                        width = rmax - rmin
                        if width <= 5:
                            ci = "L2"
                        else:
                            ci = "L3"
                        note = "rule_mid"
                elif rmin is not None:
                    if mp is not None and mp >= rmin:
                        est = mp
                        ci = "L2"
                        note = "model_low"
                    else:
                        est = float(rmin)
                        ci = "L3"
                        note = "lb_only"
                else:  # only rmax
                    if mp is not None and mp <= rmax:
                        est = mp
                        ci = "L2"
                        note = "model_up"
                    else:
                        est = float(rmax)
                        ci = "L3"
                        note = "ub_only"
            else:
                if mp is not None:
                    est = mp
                    ci = "L3"
                    note = "model_only"

        build_year.append(est if est is not None else np.nan)
        out_min.append(cmin if cmin is not None else np.nan)
        out_max.append(cmax if cmax is not None else np.nan)
        CI.append(ci)
        fuse_note.append(note)

    return (np.array(build_year),
            np.array(out_min),
            np.array(out_max),
            CI,
            fuse_note)

# =============================================================================

def main():
    # Original notebook comment normalized for the public code archive.
    (years_clcd, years_ntl, years_pop,
     clcd_ts, lc_probs, imp_ts, ntl_ts, pop_ts,
     euluc_class, is_urban, schools) = compute_all_features()

    # Original notebook comment normalized for the public code archive.
    (case_type,
     r_min,
     r_max,
     flags_json,
     rule_notes) = rule_based_inference(
        years_clcd, years_ntl, years_pop,
        clcd_ts, lc_probs, imp_ts, ntl_ts, pop_ts,
        euluc_class, is_urban
    )

    # Original notebook comment normalized for the public code archive.
    X, meta = build_ml_dataset(
        years_clcd, years_ntl, years_pop,
        imp_ts, ntl_ts, pop_ts,
        is_urban,
        case_type, r_min, r_max
    )

    # Original notebook comment normalized for the public code archive.
    rf = train_rf_model(X, meta)

    # Original notebook comment normalized for the public code archive.
    (build_year,
     out_min,
     out_max,
     CI,
     fuse_note) = fuse_rule_and_model(
        X, meta,
        case_type, r_min, r_max,
        rf
    )

    # Original notebook comment normalized for the public code archive.
    out = schools.copy()
    out["case_type"] = case_type
    out["min"]       = out_min
    out["max"]       = out_max
    out["evi_flags"] = flags_json
    out["rule_note"] = rule_notes
    out["build_year"] = build_year
    out["CI"]         = CI
    out["fuse_note"]  = fuse_note

    # Original notebook comment normalized for the public code archive.
    out["CI"] = out["CI"].astype(str)

    out_L1L2 = out[out["CI"].isin(["L1", "L2"])].copy()
    out_all  = out.copy()

    # Shapefile output note.
    if len(out_L1L2) > 0:
        out_L1L2.to_file(L1L2_SHP, encoding="utf-8")
    else:
        print("[INFO] Notebook progress message.")

    out_all.to_file(L3_SHP, encoding="utf-8")

    # Excel output note.
    if len(out_L1L2) > 0:
        out_L1L2.drop(columns="geometry").to_excel(L1L2_XLSX, index=False)
    out_all.drop(columns="geometry").to_excel(L3_XLSX, index=False)

    print("[INFO] Notebook progress message.")
    print("  L1L2 ->", L1L2_SHP, "[INFO] Notebook progress message.", L1L2_XLSX)
    print("  L3   ->", L3_SHP,   "[INFO] Notebook progress message.", L3_XLSX)


if __name__ == "__main__":
    main()


# ==============================================================================
# Province-level processing note.
# Source notebook: internal original notebook (non-public source filename omitted).
# ==============================================================================

# ------------------------------------------------------------------------------
# Notebook cell 1
# ------------------------------------------------------------------------------
import os
import re
import math
import json

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.transform import rowcol
from rasterio.windows import Window
from tqdm import tqdm
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

# =============================================================================

SCHOOL_SHP = r"D:\GISdata\CHINA_SCHOOL\beijing_小学_中学.shp"
EULUC_SHP  = r"D:\GISdata\EULUC\24beijing.shp"

CLCD_ROOT     = r"D:\GISdata\landcover"
CLCD_PROVINCE = "beijing"   # CLCD_v01_YYYY_albert_beijing.tif

NTL_ROOT = r"D:\GISdata\Night_Light\beijing"
POP_ROOT = r"D:\GISdata\PopulationDensity\worldpop北京市"

RESULT_ROOT = r"D:\GISdata\school_result"
L1L2_DIR    = os.path.join(RESULT_ROOT, "L1L2")
L3_DIR      = os.path.join(RESULT_ROOT, "L3")

os.makedirs(L1L2_DIR, exist_ok=True)
os.makedirs(L3_DIR, exist_ok=True)

# School POI processing note.
L1L2_SHP  = os.path.join(L1L2_DIR, "beijing_school.shp")
L1L2_XLSX = os.path.join(L1L2_DIR, "beijing_school.xlsx")
L3_SHP    = os.path.join(L3_DIR, "beijing_school.shp")
L3_XLSX   = os.path.join(L3_DIR, "beijing_school.xlsx")

BUFFER_RADIUS_M = 1800.0
STABLE_YEARS_K  = 1
SIM_THRESHOLD   = 0.9

IMP_CLASS   = 8
ALL_CLASSES = np.arange(0, 11, dtype=int)

EULUC_EDU_CLASS     = 7
EULUC_URBAN_CLASSES = {0, 1, 2, 3, 6, 8, 9, 10}

RF_N_ESTIMATORS = 300
RF_MAX_DEPTH    = 10
RF_RANDOM_STATE = 42

# =============================================================================

def index_clcd_files():
    year_files = {}
    ref_crs = ref_transform = None
    ref_w = ref_h = None
    ref_nodata = None

    pattern = re.compile(
        rf"CLCD_v01_(\d{{4}})_albert_{CLCD_PROVINCE}",
        re.IGNORECASE
    )

    for root, _, files in os.walk(CLCD_ROOT):
        for fname in files:
            if not fname.lower().endswith(".tif"):
                continue
            m = pattern.search(fname)
            if not m:
                continue
            year = int(m.group(1))
            path = os.path.join(root, fname)
            with rasterio.open(path) as src:
                if ref_crs is None:
                    ref_crs = src.crs
                    ref_transform = src.transform
                    ref_w, ref_h = src.width, src.height
                    ref_nodata = src.nodata
                else:
                    if src.crs != ref_crs:
                        raise ValueError(f"CLCD {year} CRS 不一致")
                    if src.transform != ref_transform or src.width != ref_w or src.height != ref_h:
                        raise ValueError(f"CLCD {year} 网格参数不一致")
            year_files[year] = path

    if not year_files:
        raise RuntimeError("未找到 CLCD_v01_YYYY_albert_beijing.tif")

    years = sorted(year_files.keys())
    if 2024 not in years:
        raise RuntimeError("缺少 2024 年 CLCD")

    print("[INFO] Notebook progress message.", years)
    return years, year_files, ref_crs, ref_transform, ref_w, ref_h, ref_nodata


def index_ntl_files(expected_crs):
    year_files = {}
    for fname in os.listdir(NTL_ROOT):
        if not fname.lower().endswith(".tif"):
            continue
        m = re.search(r'(19|20)\d{2}', fname)
        if not m:
            continue
        year = int(m.group(0))
        path = os.path.join(NTL_ROOT, fname)
        with rasterio.open(path) as src:
            if src.crs != expected_crs:
                raise ValueError(f"夜光 {fname} CRS 与 CLCD 不一致")
        year_files[year] = path

    if not year_files:
        raise RuntimeError("夜光目录无有效 tif")

    years = sorted(year_files.keys())
    print("[INFO] Notebook progress message.", years)
    return years, year_files


def index_pop_files():
    year_files = {}
    ref_crs = None
    ref_transform = None

    for fname in os.listdir(POP_ROOT):
        if not fname.lower().endswith(".tif"):
            continue
        m = re.search(r'(19|20)\d{2}', fname)
        if not m:
            continue
        year = int(m.group(0))
        path = os.path.join(POP_ROOT, fname)
        with rasterio.open(path) as src:
            if ref_crs is None:
                ref_crs = src.crs
                ref_transform = src.transform
            else:
                if src.crs != ref_crs or src.transform != ref_transform:
                    raise ValueError(f"人口 {fname} CRS/transform 不一致")
        year_files[year] = path

    if not year_files:
        raise RuntimeError("人口密度目录无有效 tif")

    years = sorted(year_files.keys())
    print("[INFO] Notebook progress message.", years)
    return years, year_files, ref_crs, ref_transform

# =============================================================================

def precompute_buffer_mask_m(radius_m, transform):
    res_x = abs(transform.a)
    res_y = abs(transform.e)
    res = (res_x + res_y) / 2.0
    r_px = int(math.ceil(radius_m / res))
    ys, xs = np.ogrid[-r_px:r_px+1, -r_px:r_px+1]
    dist2 = (xs * res)**2 + (ys * res)**2
    mask = dist2 <= radius_m**2
    return mask, r_px


def precompute_buffer_mask_pop(radius_m, transform, lat0=25.0):
    cell_deg_x = abs(transform.a)
    cell_deg_y = abs(transform.e)

    cell_m_x = 111320.0 * math.cos(math.radians(lat0)) * cell_deg_x
    cell_m_y = 111320.0 * cell_deg_y
    cell_m   = (cell_m_x + cell_m_y) / 2.0

    r_px = int(math.ceil(radius_m / cell_m))
    r_px = max(r_px, 1)

    ys, xs = np.ogrid[-r_px:r_px+1, -r_px:r_px+1]
    dist_x_m = xs * cell_m_x
    dist_y_m = ys * cell_m_y
    dist2 = dist_x_m**2 + dist_y_m**2
    mask = dist2 <= radius_m**2
    return mask, r_px

# =============================================================================

def buffer_stats_from_src(src, row, col, mask, r_px, all_classes, imp_class, nodata):
    h, w = src.height, src.width
    if not (0 <= row < h and 0 <= col < w):
        return np.nan, np.zeros(len(all_classes)), 0.0

    r0 = max(0, row - r_px)
    r1 = min(h, row + r_px + 1)
    c0 = max(0, col - r_px)
    c1 = min(w, col + r_px + 1)
    win = Window(c0, r0, c1 - c0, r1 - r0)

    sub = src.read(1, window=win)

    mr0 = r_px - (row - r0)
    mr1 = mr0 + (r1 - r0)
    mc0 = r_px - (col - c0)
    mc1 = mc0 + (c1 - c0)
    sub_mask = mask[mr0:mr1, mc0:mc1]

    if nodata is not None:
        valid = sub_mask & (sub != nodata)
    else:
        valid = sub_mask

    if not np.any(valid):
        return np.nan, np.zeros(len(all_classes)), 0.0

    vals = sub[valid]
    uniq, cnt = np.unique(vals, return_counts=True)

    probs = np.zeros(len(all_classes), float)
    total = cnt.sum()
    if total > 0:
        idx_map = {int(v): i for i, v in enumerate(all_classes)}
        for u, c in zip(uniq, cnt):
            j = idx_map.get(int(u))
            if j is not None:
                probs[j] = c / total

    central = float(sub[row - r0, col - c0])
    if nodata is not None and central == nodata:
        central = np.nan

    imp_ratio = 0.0
    if imp_class in all_classes:
        imp_idx = int(np.where(all_classes == imp_class)[0][0])
        imp_ratio = probs[imp_idx]

    return central, probs, float(imp_ratio)


def buffer_mean_from_src(src, row, col, mask, r_px, nodata, treat_zero_as_nan=False):
    h, w = src.height, src.width
    if not (0 <= row < h and 0 <= col < w):
        return np.nan

    r0 = max(0, row - r_px)
    r1 = min(h, row + r_px + 1)
    c0 = max(0, col - r_px)
    c1 = min(w, col + r_px + 1)
    win = Window(c0, r0, c1 - c0, r1 - r0)

    sub = src.read(1, window=win)

    mr0 = r_px - (row - r0)
    mr1 = mr0 + (r1 - r0)
    mc0 = r_px - (col - c0)
    mc1 = mc0 + (c1 - c0)
    sub_mask = mask[mr0:mr1, mc0:mc1]

    if nodata is not None:
        valid = sub_mask & (sub != nodata)
    else:
        valid = sub_mask

    if not np.any(valid):
        return np.nan

    vals = sub[valid].astype(float)
    if treat_zero_as_nan:
        vals[vals == 0.0] = np.nan
    if np.all(np.isnan(vals)):
        return np.nan

    return float(np.nanmean(vals))

# =============================================================================

def compute_similarity(p_t, p_ref):
    return 1.0 - 0.5 * np.abs(p_t - p_ref).sum()


def detect_jump_year(series, years, low_q=0.2, high_q=0.6, k=3):
    arr = np.array(series, float)
    mask = ~np.isnan(arr)
    if mask.sum() < k + 2:
        return None

    vals = arr[mask]
    vmin, vmax = np.min(vals), np.max(vals)
    if vmax - vmin <= 1e-6:
        return None

    low_thr  = vmin + (vmax - vmin) * low_q
    high_thr = vmin + (vmax - vmin) * high_q

    n = len(arr)
    for i in range(n - k + 1):
        block = arr[i:i+k]
        if np.any(np.isnan(block)):
            continue
        if np.all(block >= high_thr):
            before = arr[:i]
            before = before[~np.isnan(before)]
            if before.size == 0 or np.max(before) <= low_thr:
                if np.all(arr[i:][~np.isnan(arr[i:])] >= high_thr):
                    return years[i]
    return None


def reverse_stable_run(stable, end_idx, k):
    i = end_idx
    while i >= 0 and stable[i]:
        i -= 1
    start = i + 1
    if end_idx - start + 1 >= k:
        return start
    return None

# =============================================================================

def compute_all_features():
    years_clcd, clcd_files, clcd_crs, clcd_transform, _, _, _ = index_clcd_files()
    years_ntl, ntl_files = index_ntl_files(clcd_crs)
    years_pop, pop_files, pop_crs, pop_transform = index_pop_files()

    # Original notebook comment normalized for the public code archive.
    euluc = gpd.read_file(EULUC_SHP)
    if euluc.crs is None:
        raise ValueError("EULUC 无 CRS")
    if "Class" not in euluc.columns:
        raise ValueError("EULUC 缺 Class 字段")
    euluc = euluc.to_crs(clcd_crs)
    euluc = euluc[["Class", "geometry"]].rename(columns={"Class": "euluc_cls"})

    # Original notebook comment normalized for the public code archive.
    schools = gpd.read_file(SCHOOL_SHP)
    if schools.crs is None:
        raise ValueError("学校点 无 CRS")
    schools = schools.to_crs(clcd_crs)
    schools["sid"] = np.arange(len(schools), dtype=int)

    # Original notebook comment normalized for the public code archive.
    schools = gpd.sjoin(schools, euluc, how="left", predicate="within").drop(columns=["index_right"])
    euluc_class = schools["euluc_cls"].to_numpy()
    is_urban = np.isin(euluc_class, list(EULUC_URBAN_CLASSES) + [EULUC_EDU_CLASS])

    # Original notebook comment normalized for the public code archive.
    xs = schools.geometry.x.to_numpy()
    ys = schools.geometry.y.to_numpy()

    # CLCD index
    rows_clcd, cols_clcd = rowcol(clcd_transform, xs, ys, op=np.floor)
    rows_clcd = rows_clcd.astype(int)
    cols_clcd = cols_clcd.astype(int)

    # Original notebook comment normalized for the public code archive.
    with rasterio.open(ntl_files[years_ntl[0]]) as src:
        ntl_transform = src.transform
        ntl_nodata    = src.nodata
    rows_ntl, cols_ntl = rowcol(ntl_transform, xs, ys, op=np.floor)
    rows_ntl = rows_ntl.astype(int)
    cols_ntl = cols_ntl.astype(int)

    # Original notebook comment normalized for the public code archive.
    schools_pop = schools.to_crs(pop_crs)
    xs_pop = schools_pop.geometry.x.to_numpy()
    ys_pop = schools_pop.geometry.y.to_numpy()
    rows_pop, cols_pop = rowcol(pop_transform, xs_pop, ys_pop, op=np.floor)
    rows_pop = rows_pop.astype(int)
    cols_pop = cols_pop.astype(int)

    n_pts  = len(schools)
    n_clcd = len(years_clcd)
    n_ntl  = len(years_ntl)
    n_pop  = len(years_pop)
    n_cls  = len(ALL_CLASSES)

    print("[INFO] Notebook progress message.", n_pts)

    # buffer mask
    mask_clcd, rpx_clcd = precompute_buffer_mask_m(BUFFER_RADIUS_M, clcd_transform)
    mask_ntl,  rpx_ntl  = precompute_buffer_mask_m(BUFFER_RADIUS_M, ntl_transform)
    mask_pop,  rpx_pop  = precompute_buffer_mask_pop(BUFFER_RADIUS_M, pop_transform, lat0=25.0)

    # allocate
    clcd_ts = np.full((n_pts, n_clcd), np.nan, float)
    lc_probs = np.zeros((n_pts, n_clcd, n_cls), float)
    imp_ts = np.zeros((n_pts, n_clcd), float)

    ntl_ts = np.full((n_pts, n_ntl), np.nan, float)
    pop_ts = np.full((n_pts, n_pop), np.nan, float)

    # CLCD
    for j, y in enumerate(tqdm(years_clcd, desc="Processing", ncols=80)):
        path = clcd_files[y]
        with rasterio.open(path) as src:
            nodata = src.nodata
            for i in range(n_pts):
                val, probs, imp = buffer_stats_from_src(
                    src,
                    rows_clcd[i], cols_clcd[i],
                    mask_clcd, rpx_clcd,
                    ALL_CLASSES, IMP_CLASS, nodata
                )
                clcd_ts[i, j] = val
                lc_probs[i, j, :] = probs
                imp_ts[i, j] = imp

    # Original notebook comment normalized for the public code archive.
    for j, y in enumerate(tqdm(years_ntl, desc="Processing", ncols=80)):
        path = ntl_files[y]
        with rasterio.open(path) as src:
            nodata = src.nodata if src.nodata is not None else ntl_nodata
            for i in range(n_pts):
                ntl_ts[i, j] = buffer_mean_from_src(
                    src,
                    rows_ntl[i], cols_ntl[i],
                    mask_ntl, rpx_ntl,
                    nodata,
                    treat_zero_as_nan=False
                )

    # Original notebook comment normalized for the public code archive.
    for j, y in enumerate(tqdm(years_pop, desc="Processing", ncols=80)):
        path = pop_files[y]
        with rasterio.open(path) as src:
            nodata = src.nodata
            for i in range(n_pts):
                v = buffer_mean_from_src(
                    src,
                    rows_pop[i], cols_pop[i],
                    mask_pop, rpx_pop,
                    nodata,
                    treat_zero_as_nan=True
                )
                pop_ts[i, j] = v

    return (years_clcd, years_ntl, years_pop,
            clcd_ts, lc_probs, imp_ts, ntl_ts, pop_ts,
            euluc_class, is_urban, schools)

# =============================================================================

def rule_based_inference(years_clcd, years_ntl, years_pop,
                         clcd_ts, lc_probs, imp_ts, ntl_ts, pop_ts,
                         euluc_class, is_urban):

    n_pts = clcd_ts.shape[0]
    idx_2024 = years_clcd.index(2024)
    idx_2022 = years_clcd.index(2022) if 2022 in years_clcd else None

    case_type = []
    r_min = []
    r_max = []
    flags_json = []
    notes = []

    for i in tqdm(range(n_pts), desc="Processing", ncols=80):
        lc = clcd_ts[i, :]
        probs = lc_probs[i, :, :]
        imp = imp_ts[i, :]
        ntl = ntl_ts[i, :]
        pop = pop_ts[i, :]
        eu = euluc_class[i]
        urban = bool(is_urban[i])

        flags = {
            "clcd_pix": False,
            "clcd_env": False,
            "ntl": False,
            "pop": False,
            "edu": False,
            "urban": False
        }
        note = ""
        ctype = "D_NoDate"
        ymin = None
        ymax = None

        # Original notebook comment normalized for the public code archive.
        val_2024 = lc[idx_2024]
        if not np.isnan(val_2024) and int(val_2024) == IMP_CLASS:
            stable = np.array(
                [(not np.isnan(v) and int(v) == IMP_CLASS) for v in lc],
                dtype=bool
            )
            start_idx = reverse_stable_run(stable, idx_2024, STABLE_YEARS_K)
            if start_idx is not None:
                if start_idx == 0 and np.all(stable):
                    ctype = "A_CLCD_left"
                    ymin = None
                    ymax = years_clcd[0]
                    flags["clcd_pix"] = True
                    note = "impervious_since_first_year"
                else:
                    ctype = "A_CLCD_direct"
                    ymin = years_clcd[start_idx]
                    ymax = 2024
                    flags["clcd_pix"] = True

        # Original notebook comment normalized for the public code archive.
        if (not ctype.startswith("A_")) and (not np.isnan(eu)) and int(eu) == EULUC_EDU_CLASS and idx_2022 is not None:
            flags["edu"] = True
            pref = probs[idx_2024, :]
            sim = np.array([
                compute_similarity(probs[j, :], pref)
                for j in range(len(years_clcd))
            ])
            stable = sim >= SIM_THRESHOLD

            if np.all(stable[idx_2022:idx_2024+1]):
                start_idx = reverse_stable_run(stable, idx_2022, STABLE_YEARS_K)
                if start_idx is not None:
                    ymin = years_clcd[start_idx]
                    ymax = 2022
                    flags["clcd_env"] = True

                    t_ntl = detect_jump_year(ntl, years_ntl) if not np.all(np.isnan(ntl)) else None
                    t_pop = detect_jump_year(pop, years_pop) if not np.all(np.isnan(pop)) else None
                    ok_ntl = (t_ntl is None) or (t_ntl <= ymax)
                    ok_pop = (t_pop is None) or (t_pop <= ymax)

                    if ok_ntl and ok_pop:
                        ctype = "B_EU_edu_s"
                    else:
                        ctype = "B_EU_edu_w"
                        note = "ntl_or_pop_late"
                        if t_ntl is not None:
                            flags["ntl"] = True
                        if t_pop is not None:
                            flags["pop"] = True
                else:
                    ctype = "B_EU_edu_u"
                    note = "no_long_stable_before_2022"
            else:
                ctype = "B_EU_edu_u"
                note = "env_changed_after_2022"

        # Original notebook comment normalized for the public code archive.
        if (not ctype.startswith("A_")) and (not ctype.startswith("B_")) \
           and (not np.isnan(eu)) and int(eu) in EULUC_URBAN_CLASSES:
            flags["urban"] = True

            t_imp = detect_jump_year(imp, years_clcd)
            t_ntl = detect_jump_year(ntl, years_ntl) if not np.all(np.isnan(ntl)) else None
            t_pop = detect_jump_year(pop, years_pop) if not np.all(np.isnan(pop)) else None

            cand = []
            if t_imp is not None:
                cand.append(t_imp)
                flags["clcd_pix"] = True
            if t_ntl is not None:
                cand.append(t_ntl)
                flags["ntl"] = True
            if t_pop is not None:
                cand.append(t_pop)
                flags["pop"] = True

            if cand:
                t_urban = max(cand)
                ymin = t_urban
                ymax = 2024
                ctype = "C_urban"
            else:
                ctype = "C_urban_N"
                note = "no_jump"

        if ctype == "D_NoDate" and urban:
            flags["urban"] = True

        case_type.append(ctype)
        r_min.append(ymin)
        r_max.append(ymax)
        flags_json.append(json.dumps(flags, ensure_ascii=False))
        notes.append(note)

    return case_type, r_min, r_max, flags_json, notes

# =============================================================================

def build_ml_dataset(years_clcd, years_ntl, years_pop,
                     imp_ts, ntl_ts, pop_ts,
                     is_urban,
                     case_type, r_min, r_max):

    n = imp_ts.shape[0]
    idx_2024 = years_clcd.index(2024)

    def safe_jump(arr2d, years):
        res = []
        for i in range(n):
            arr = arr2d[i, :]
            if np.all(np.isnan(arr)):
                res.append(np.nan)
            else:
                res.append(detect_jump_year(arr, years))
        return np.array(res, float)

    imp_jump = safe_jump(imp_ts, years_clcd)
    ntl_jump = safe_jump(ntl_ts, years_ntl)
    pop_jump = safe_jump(pop_ts, years_pop)

    imp_2024 = imp_ts[:, idx_2024]
    ntl_latest = np.nan_to_num(ntl_ts[:, -1], nan=0.0)
    pop_latest = np.nan_to_num(pop_ts[:, -1], nan=0.0)

    def encode_year(arr, ref=2024):
        arr = arr.astype(float)
        miss = np.isnan(arr)
        val = np.where(miss, 0, ref - arr)
        return val, miss.astype(int)

    f_impjmp, m_impjmp = encode_year(imp_jump)
    f_ntljmp, m_ntljmp = encode_year(ntl_jump)
    f_popjmp, m_popjmp = encode_year(pop_jump)

    X = np.column_stack([
        f_impjmp, m_impjmp,
        f_ntljmp, m_ntljmp,
        f_popjmp, m_popjmp,
        imp_2024,
        ntl_latest,
        pop_latest,
        is_urban.astype(int)
    ])

    # Original notebook comment normalized for the public code archive.
    level1_mask = np.array([
        (ct == "A_CLCD_direct") or (ct == "B_EU_edu_s")
        for ct in case_type
    ])

    y = np.array([
        r_min[i] if level1_mask[i] and r_min[i] is not None else np.nan
        for i in range(n)
    ], dtype=float)

    meta = {
        "imp_jump_year": imp_jump,
        "ntl_jump_year": ntl_jump,
        "pop_jump_year": pop_jump,
        "imp_2024": imp_2024,
        "ntl_latest": ntl_latest,
        "pop_latest": pop_latest,
        "level1_mask": level1_mask,
        "y_level1": y
    }

    return X, meta

# =============================================================================

def train_rf_model(X, meta):
    level1 = meta["level1_mask"]
    y = meta["y_level1"]
    idx = np.where(~np.isnan(y) & level1)[0]

    if idx.size < 50:
        print("[INFO] Notebook progress message.")
        return None

    X_train = X[idx, :]
    y_train = y[idx]

    X_tr, X_te, y_tr, y_te = train_test_split(
        X_train, y_train, test_size=0.2, random_state=RF_RANDOM_STATE
    )

    rf = RandomForestRegressor(
        n_estimators=RF_N_ESTIMATORS,
        max_depth=RF_MAX_DEPTH,
        random_state=RF_RANDOM_STATE,
        n_jobs=-1
    )
    rf.fit(X_tr, y_tr)

    if X_te.shape[0] > 0:
        pred = rf.predict(X_te)
        mae = float(np.mean(np.abs(pred - y_te)))
        print("[INFO] Notebook progress message.")

    return rf

# =============================================================================

def fuse_rule_and_model(X, meta, case_type, r_min, r_max, rf):
    n = X.shape[0]
    level1 = meta["level1_mask"]

    if rf is not None:
        model_pred = rf.predict(X)
        model_pred = np.clip(model_pred, 1950, 2025)
    else:
        model_pred = np.full(n, np.nan)

    build_year = []
    out_min = []
    out_max = []
    CI = []
    fuse_note = []

    for i in range(n):
        ct   = case_type[i]
        rmin = r_min[i]
        rmax = r_max[i]
        mp   = None if np.isnan(model_pred[i]) else float(model_pred[i])

        est = None
        cmin = rmin
        cmax = rmax
        ci = "NoDate"
        note = ""

        if level1[i] and rmin is not None:
            est  = float(rmin)
            cmin = float(rmin)
            cmax = float(rmax) if rmax is not None else float(rmin)
            ci   = "L1"
            note = "rule_strong"
        else:
            if rmin is not None or rmax is not None:
                if rmin is not None and rmax is not None:
                    if mp is not None and rmin <= mp <= rmax:
                        est = mp
                        width = rmax - rmin
                        if width <= 5:
                            ci = "L1"
                        elif width <= 10:
                            ci = "L2"
                        else:
                            ci = "L3"
                        note = "model_in_rule"
                    else:
                        est = (rmin + rmax) / 2.0
                        width = rmax - rmin
                        if width <= 5:
                            ci = "L2"
                        else:
                            ci = "L3"
                        note = "rule_mid"
                elif rmin is not None:
                    if mp is not None and mp >= rmin:
                        est = mp
                        ci = "L2"
                        note = "model_low"
                    else:
                        est = float(rmin)
                        ci = "L3"
                        note = "lb_only"
                else:  # only rmax
                    if mp is not None and mp <= rmax:
                        est = mp
                        ci = "L2"
                        note = "model_up"
                    else:
                        est = float(rmax)
                        ci = "L3"
                        note = "ub_only"
            else:
                if mp is not None:
                    est = mp
                    ci = "L3"
                    note = "model_only"

        build_year.append(est if est is not None else np.nan)
        out_min.append(cmin if cmin is not None else np.nan)
        out_max.append(cmax if cmax is not None else np.nan)
        CI.append(ci)
        fuse_note.append(note)

    return (np.array(build_year),
            np.array(out_min),
            np.array(out_max),
            CI,
            fuse_note)

# =============================================================================

def main():
    # Original notebook comment normalized for the public code archive.
    (years_clcd, years_ntl, years_pop,
     clcd_ts, lc_probs, imp_ts, ntl_ts, pop_ts,
     euluc_class, is_urban, schools) = compute_all_features()

    # Original notebook comment normalized for the public code archive.
    (case_type,
     r_min,
     r_max,
     flags_json,
     rule_notes) = rule_based_inference(
        years_clcd, years_ntl, years_pop,
        clcd_ts, lc_probs, imp_ts, ntl_ts, pop_ts,
        euluc_class, is_urban
    )

    # Original notebook comment normalized for the public code archive.
    X, meta = build_ml_dataset(
        years_clcd, years_ntl, years_pop,
        imp_ts, ntl_ts, pop_ts,
        is_urban,
        case_type, r_min, r_max
    )

    # Original notebook comment normalized for the public code archive.
    rf = train_rf_model(X, meta)

    # Original notebook comment normalized for the public code archive.
    (build_year,
     out_min,
     out_max,
     CI,
     fuse_note) = fuse_rule_and_model(
        X, meta,
        case_type, r_min, r_max,
        rf
    )

    # Original notebook comment normalized for the public code archive.
    out = schools.copy()
    out["case_type"] = case_type
    out["min"]       = out_min
    out["max"]       = out_max
    out["evi_flags"] = flags_json
    out["rule_note"] = rule_notes
    out["build_year"] = build_year
    out["CI"]         = CI
    out["fuse_note"]  = fuse_note

    # Original notebook comment normalized for the public code archive.
    out["CI"] = out["CI"].astype(str)

    out_L1L2 = out[out["CI"].isin(["L1", "L2"])].copy()
    out_all  = out.copy()

    # Shapefile output note.
    if len(out_L1L2) > 0:
        out_L1L2.to_file(L1L2_SHP, encoding="utf-8")
    else:
        print("[INFO] Notebook progress message.")

    out_all.to_file(L3_SHP, encoding="utf-8")

    # Excel output note.
    if len(out_L1L2) > 0:
        out_L1L2.drop(columns="geometry").to_excel(L1L2_XLSX, index=False)
    out_all.drop(columns="geometry").to_excel(L3_XLSX, index=False)

    print("[INFO] Notebook progress message.")
    print("  L1L2 ->", L1L2_SHP, "[INFO] Notebook progress message.", L1L2_XLSX)
    print("  L3   ->", L3_SHP,   "[INFO] Notebook progress message.", L3_XLSX)


if __name__ == "__main__":
    main()


# ==============================================================================
# Province-level processing note.
# Source notebook: internal original notebook (non-public source filename omitted).
# ==============================================================================

# ------------------------------------------------------------------------------
# Notebook cell 1
# ------------------------------------------------------------------------------
import os
import re
import math
import json

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.transform import rowcol
from rasterio.windows import Window
from tqdm import tqdm
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

# =============================================================================

SCHOOL_SHP = r"D:\GISdata\CHINA_SCHOOL\fujian_小学_中学.shp"
EULUC_SHP  = r"D:\GISdata\EULUC\24fujian.shp"

CLCD_ROOT     = r"D:\GISdata\landcover"
CLCD_PROVINCE = "fujian"   # CLCD_v01_YYYY_albert_fujian.tif

NTL_ROOT = r"D:\GISdata\Night_Light\fujian"
POP_ROOT = r"D:\GISdata\PopulationDensity\worldpop福建省"

RESULT_ROOT = r"D:\GISdata\school_result"
L1L2_DIR    = os.path.join(RESULT_ROOT, "L1L2")
L3_DIR      = os.path.join(RESULT_ROOT, "L3")

os.makedirs(L1L2_DIR, exist_ok=True)
os.makedirs(L3_DIR, exist_ok=True)

# School POI processing note.
L1L2_SHP  = os.path.join(L1L2_DIR, "fujian_school.shp")
L1L2_XLSX = os.path.join(L1L2_DIR, "fujian_school.xlsx")
L3_SHP    = os.path.join(L3_DIR, "fujian_school.shp")
L3_XLSX   = os.path.join(L3_DIR, "fujian_school.xlsx")

BUFFER_RADIUS_M = 1800.0
STABLE_YEARS_K  = 1
SIM_THRESHOLD   = 0.9

IMP_CLASS   = 8
ALL_CLASSES = np.arange(0, 11, dtype=int)

EULUC_EDU_CLASS     = 7
EULUC_URBAN_CLASSES = {0, 1, 2, 3, 6, 8, 9, 10}

RF_N_ESTIMATORS = 300
RF_MAX_DEPTH    = 10
RF_RANDOM_STATE = 42

# =============================================================================

def index_clcd_files():
    year_files = {}
    ref_crs = ref_transform = None
    ref_w = ref_h = None
    ref_nodata = None

    pattern = re.compile(
        rf"CLCD_v01_(\d{{4}})_albert_{CLCD_PROVINCE}",
        re.IGNORECASE
    )

    for root, _, files in os.walk(CLCD_ROOT):
        for fname in files:
            if not fname.lower().endswith(".tif"):
                continue
            m = pattern.search(fname)
            if not m:
                continue
            year = int(m.group(1))
            path = os.path.join(root, fname)
            with rasterio.open(path) as src:
                if ref_crs is None:
                    ref_crs = src.crs
                    ref_transform = src.transform
                    ref_w, ref_h = src.width, src.height
                    ref_nodata = src.nodata
                else:
                    if src.crs != ref_crs:
                        raise ValueError(f"CLCD {year} CRS 不一致")
                    if src.transform != ref_transform or src.width != ref_w or src.height != ref_h:
                        raise ValueError(f"CLCD {year} 网格参数不一致")
            year_files[year] = path

    if not year_files:
        raise RuntimeError("未找到 CLCD_v01_YYYY_albert_fujian.tif")

    years = sorted(year_files.keys())
    if 2024 not in years:
        raise RuntimeError("缺少 2024 年 CLCD")

    print("[INFO] Notebook progress message.", years)
    return years, year_files, ref_crs, ref_transform, ref_w, ref_h, ref_nodata


def index_ntl_files(expected_crs):
    year_files = {}
    for fname in os.listdir(NTL_ROOT):
        if not fname.lower().endswith(".tif"):
            continue
        m = re.search(r'(19|20)\d{2}', fname)
        if not m:
            continue
        year = int(m.group(0))
        path = os.path.join(NTL_ROOT, fname)
        with rasterio.open(path) as src:
            if src.crs != expected_crs:
                raise ValueError(f"夜光 {fname} CRS 与 CLCD 不一致")
        year_files[year] = path

    if not year_files:
        raise RuntimeError("夜光目录无有效 tif")

    years = sorted(year_files.keys())
    print("[INFO] Notebook progress message.", years)
    return years, year_files


def index_pop_files():
    year_files = {}
    ref_crs = None
    ref_transform = None

    for fname in os.listdir(POP_ROOT):
        if not fname.lower().endswith(".tif"):
            continue
        m = re.search(r'(19|20)\d{2}', fname)
        if not m:
            continue
        year = int(m.group(0))
        path = os.path.join(POP_ROOT, fname)
        with rasterio.open(path) as src:
            if ref_crs is None:
                ref_crs = src.crs
                ref_transform = src.transform
            else:
                if src.crs != ref_crs or src.transform != ref_transform:
                    raise ValueError(f"人口 {fname} CRS/transform 不一致")
        year_files[year] = path

    if not year_files:
        raise RuntimeError("人口密度目录无有效 tif")

    years = sorted(year_files.keys())
    print("[INFO] Notebook progress message.", years)
    return years, year_files, ref_crs, ref_transform

# =============================================================================

def precompute_buffer_mask_m(radius_m, transform):
    res_x = abs(transform.a)
    res_y = abs(transform.e)
    res = (res_x + res_y) / 2.0
    r_px = int(math.ceil(radius_m / res))
    ys, xs = np.ogrid[-r_px:r_px+1, -r_px:r_px+1]
    dist2 = (xs * res)**2 + (ys * res)**2
    mask = dist2 <= radius_m**2
    return mask, r_px


def precompute_buffer_mask_pop(radius_m, transform, lat0=25.0):
    cell_deg_x = abs(transform.a)
    cell_deg_y = abs(transform.e)

    cell_m_x = 111320.0 * math.cos(math.radians(lat0)) * cell_deg_x
    cell_m_y = 111320.0 * cell_deg_y
    cell_m   = (cell_m_x + cell_m_y) / 2.0

    r_px = int(math.ceil(radius_m / cell_m))
    r_px = max(r_px, 1)

    ys, xs = np.ogrid[-r_px:r_px+1, -r_px:r_px+1]
    dist_x_m = xs * cell_m_x
    dist_y_m = ys * cell_m_y
    dist2 = dist_x_m**2 + dist_y_m**2
    mask = dist2 <= radius_m**2
    return mask, r_px

# =============================================================================

def buffer_stats_from_src(src, row, col, mask, r_px, all_classes, imp_class, nodata):
    h, w = src.height, src.width
    if not (0 <= row < h and 0 <= col < w):
        return np.nan, np.zeros(len(all_classes)), 0.0

    r0 = max(0, row - r_px)
    r1 = min(h, row + r_px + 1)
    c0 = max(0, col - r_px)
    c1 = min(w, col + r_px + 1)
    win = Window(c0, r0, c1 - c0, r1 - r0)

    sub = src.read(1, window=win)

    mr0 = r_px - (row - r0)
    mr1 = mr0 + (r1 - r0)
    mc0 = r_px - (col - c0)
    mc1 = mc0 + (c1 - c0)
    sub_mask = mask[mr0:mr1, mc0:mc1]

    if nodata is not None:
        valid = sub_mask & (sub != nodata)
    else:
        valid = sub_mask

    if not np.any(valid):
        return np.nan, np.zeros(len(all_classes)), 0.0

    vals = sub[valid]
    uniq, cnt = np.unique(vals, return_counts=True)

    probs = np.zeros(len(all_classes), float)
    total = cnt.sum()
    if total > 0:
        idx_map = {int(v): i for i, v in enumerate(all_classes)}
        for u, c in zip(uniq, cnt):
            j = idx_map.get(int(u))
            if j is not None:
                probs[j] = c / total

    central = float(sub[row - r0, col - c0])
    if nodata is not None and central == nodata:
        central = np.nan

    imp_ratio = 0.0
    if imp_class in all_classes:
        imp_idx = int(np.where(all_classes == imp_class)[0][0])
        imp_ratio = probs[imp_idx]

    return central, probs, float(imp_ratio)


def buffer_mean_from_src(src, row, col, mask, r_px, nodata, treat_zero_as_nan=False):
    h, w = src.height, src.width
    if not (0 <= row < h and 0 <= col < w):
        return np.nan

    r0 = max(0, row - r_px)
    r1 = min(h, row + r_px + 1)
    c0 = max(0, col - r_px)
    c1 = min(w, col + r_px + 1)
    win = Window(c0, r0, c1 - c0, r1 - r0)

    sub = src.read(1, window=win)

    mr0 = r_px - (row - r0)
    mr1 = mr0 + (r1 - r0)
    mc0 = r_px - (col - c0)
    mc1 = mc0 + (c1 - c0)
    sub_mask = mask[mr0:mr1, mc0:mc1]

    if nodata is not None:
        valid = sub_mask & (sub != nodata)
    else:
        valid = sub_mask

    if not np.any(valid):
        return np.nan

    vals = sub[valid].astype(float)
    if treat_zero_as_nan:
        vals[vals == 0.0] = np.nan
    if np.all(np.isnan(vals)):
        return np.nan

    return float(np.nanmean(vals))

# =============================================================================

def compute_similarity(p_t, p_ref):
    return 1.0 - 0.5 * np.abs(p_t - p_ref).sum()


def detect_jump_year(series, years, low_q=0.2, high_q=0.6, k=3):
    arr = np.array(series, float)
    mask = ~np.isnan(arr)
    if mask.sum() < k + 2:
        return None

    vals = arr[mask]
    vmin, vmax = np.min(vals), np.max(vals)
    if vmax - vmin <= 1e-6:
        return None

    low_thr  = vmin + (vmax - vmin) * low_q
    high_thr = vmin + (vmax - vmin) * high_q

    n = len(arr)
    for i in range(n - k + 1):
        block = arr[i:i+k]
        if np.any(np.isnan(block)):
            continue
        if np.all(block >= high_thr):
            before = arr[:i]
            before = before[~np.isnan(before)]
            if before.size == 0 or np.max(before) <= low_thr:
                if np.all(arr[i:][~np.isnan(arr[i:])] >= high_thr):
                    return years[i]
    return None


def reverse_stable_run(stable, end_idx, k):
    i = end_idx
    while i >= 0 and stable[i]:
        i -= 1
    start = i + 1
    if end_idx - start + 1 >= k:
        return start
    return None

# =============================================================================

def compute_all_features():
    years_clcd, clcd_files, clcd_crs, clcd_transform, _, _, _ = index_clcd_files()
    years_ntl, ntl_files = index_ntl_files(clcd_crs)
    years_pop, pop_files, pop_crs, pop_transform = index_pop_files()

    # Original notebook comment normalized for the public code archive.
    euluc = gpd.read_file(EULUC_SHP)
    if euluc.crs is None:
        raise ValueError("EULUC 无 CRS")
    if "Class" not in euluc.columns:
        raise ValueError("EULUC 缺 Class 字段")
    euluc = euluc.to_crs(clcd_crs)
    euluc = euluc[["Class", "geometry"]].rename(columns={"Class": "euluc_cls"})

    # Original notebook comment normalized for the public code archive.
    schools = gpd.read_file(SCHOOL_SHP)
    if schools.crs is None:
        raise ValueError("学校点 无 CRS")
    schools = schools.to_crs(clcd_crs)
    schools["sid"] = np.arange(len(schools), dtype=int)

    # Original notebook comment normalized for the public code archive.
    schools = gpd.sjoin(schools, euluc, how="left", predicate="within").drop(columns=["index_right"])
    euluc_class = schools["euluc_cls"].to_numpy()
    is_urban = np.isin(euluc_class, list(EULUC_URBAN_CLASSES) + [EULUC_EDU_CLASS])

    # Original notebook comment normalized for the public code archive.
    xs = schools.geometry.x.to_numpy()
    ys = schools.geometry.y.to_numpy()

    # CLCD index
    rows_clcd, cols_clcd = rowcol(clcd_transform, xs, ys, op=np.floor)
    rows_clcd = rows_clcd.astype(int)
    cols_clcd = cols_clcd.astype(int)

    # Original notebook comment normalized for the public code archive.
    with rasterio.open(ntl_files[years_ntl[0]]) as src:
        ntl_transform = src.transform
        ntl_nodata    = src.nodata
    rows_ntl, cols_ntl = rowcol(ntl_transform, xs, ys, op=np.floor)
    rows_ntl = rows_ntl.astype(int)
    cols_ntl = cols_ntl.astype(int)

    # Original notebook comment normalized for the public code archive.
    schools_pop = schools.to_crs(pop_crs)
    xs_pop = schools_pop.geometry.x.to_numpy()
    ys_pop = schools_pop.geometry.y.to_numpy()
    rows_pop, cols_pop = rowcol(pop_transform, xs_pop, ys_pop, op=np.floor)
    rows_pop = rows_pop.astype(int)
    cols_pop = cols_pop.astype(int)

    n_pts  = len(schools)
    n_clcd = len(years_clcd)
    n_ntl  = len(years_ntl)
    n_pop  = len(years_pop)
    n_cls  = len(ALL_CLASSES)

    print("[INFO] Notebook progress message.", n_pts)

    # buffer mask
    mask_clcd, rpx_clcd = precompute_buffer_mask_m(BUFFER_RADIUS_M, clcd_transform)
    mask_ntl,  rpx_ntl  = precompute_buffer_mask_m(BUFFER_RADIUS_M, ntl_transform)
    mask_pop,  rpx_pop  = precompute_buffer_mask_pop(BUFFER_RADIUS_M, pop_transform, lat0=25.0)

    # allocate
    clcd_ts = np.full((n_pts, n_clcd), np.nan, float)
    lc_probs = np.zeros((n_pts, n_clcd, n_cls), float)
    imp_ts = np.zeros((n_pts, n_clcd), float)

    ntl_ts = np.full((n_pts, n_ntl), np.nan, float)
    pop_ts = np.full((n_pts, n_pop), np.nan, float)

    # CLCD
    for j, y in enumerate(tqdm(years_clcd, desc="Processing", ncols=80)):
        path = clcd_files[y]
        with rasterio.open(path) as src:
            nodata = src.nodata
            for i in range(n_pts):
                val, probs, imp = buffer_stats_from_src(
                    src,
                    rows_clcd[i], cols_clcd[i],
                    mask_clcd, rpx_clcd,
                    ALL_CLASSES, IMP_CLASS, nodata
                )
                clcd_ts[i, j] = val
                lc_probs[i, j, :] = probs
                imp_ts[i, j] = imp

    # Original notebook comment normalized for the public code archive.
    for j, y in enumerate(tqdm(years_ntl, desc="Processing", ncols=80)):
        path = ntl_files[y]
        with rasterio.open(path) as src:
            nodata = src.nodata if src.nodata is not None else ntl_nodata
            for i in range(n_pts):
                ntl_ts[i, j] = buffer_mean_from_src(
                    src,
                    rows_ntl[i], cols_ntl[i],
                    mask_ntl, rpx_ntl,
                    nodata,
                    treat_zero_as_nan=False
                )

    # Original notebook comment normalized for the public code archive.
    for j, y in enumerate(tqdm(years_pop, desc="Processing", ncols=80)):
        path = pop_files[y]
        with rasterio.open(path) as src:
            nodata = src.nodata
            for i in range(n_pts):
                v = buffer_mean_from_src(
                    src,
                    rows_pop[i], cols_pop[i],
                    mask_pop, rpx_pop,
                    nodata,
                    treat_zero_as_nan=True
                )
                pop_ts[i, j] = v

    return (years_clcd, years_ntl, years_pop,
            clcd_ts, lc_probs, imp_ts, ntl_ts, pop_ts,
            euluc_class, is_urban, schools)

# =============================================================================

def rule_based_inference(years_clcd, years_ntl, years_pop,
                         clcd_ts, lc_probs, imp_ts, ntl_ts, pop_ts,
                         euluc_class, is_urban):

    n_pts = clcd_ts.shape[0]
    idx_2024 = years_clcd.index(2024)
    idx_2022 = years_clcd.index(2022) if 2022 in years_clcd else None

    case_type = []
    r_min = []
    r_max = []
    flags_json = []
    notes = []

    for i in tqdm(range(n_pts), desc="Processing", ncols=80):
        lc = clcd_ts[i, :]
        probs = lc_probs[i, :, :]
        imp = imp_ts[i, :]
        ntl = ntl_ts[i, :]
        pop = pop_ts[i, :]
        eu = euluc_class[i]
        urban = bool(is_urban[i])

        flags = {
            "clcd_pix": False,
            "clcd_env": False,
            "ntl": False,
            "pop": False,
            "edu": False,
            "urban": False
        }
        note = ""
        ctype = "D_NoDate"
        ymin = None
        ymax = None

        # Original notebook comment normalized for the public code archive.
        val_2024 = lc[idx_2024]
        if not np.isnan(val_2024) and int(val_2024) == IMP_CLASS:
            stable = np.array(
                [(not np.isnan(v) and int(v) == IMP_CLASS) for v in lc],
                dtype=bool
            )
            start_idx = reverse_stable_run(stable, idx_2024, STABLE_YEARS_K)
            if start_idx is not None:
                if start_idx == 0 and np.all(stable):
                    ctype = "A_CLCD_left"
                    ymin = None
                    ymax = years_clcd[0]
                    flags["clcd_pix"] = True
                    note = "impervious_since_first_year"
                else:
                    ctype = "A_CLCD_direct"
                    ymin = years_clcd[start_idx]
                    ymax = 2024
                    flags["clcd_pix"] = True

        # Original notebook comment normalized for the public code archive.
        if (not ctype.startswith("A_")) and (not np.isnan(eu)) and int(eu) == EULUC_EDU_CLASS and idx_2022 is not None:
            flags["edu"] = True
            pref = probs[idx_2024, :]
            sim = np.array([
                compute_similarity(probs[j, :], pref)
                for j in range(len(years_clcd))
            ])
            stable = sim >= SIM_THRESHOLD

            if np.all(stable[idx_2022:idx_2024+1]):
                start_idx = reverse_stable_run(stable, idx_2022, STABLE_YEARS_K)
                if start_idx is not None:
                    ymin = years_clcd[start_idx]
                    ymax = 2022
                    flags["clcd_env"] = True

                    t_ntl = detect_jump_year(ntl, years_ntl) if not np.all(np.isnan(ntl)) else None
                    t_pop = detect_jump_year(pop, years_pop) if not np.all(np.isnan(pop)) else None
                    ok_ntl = (t_ntl is None) or (t_ntl <= ymax)
                    ok_pop = (t_pop is None) or (t_pop <= ymax)

                    if ok_ntl and ok_pop:
                        ctype = "B_EU_edu_s"
                    else:
                        ctype = "B_EU_edu_w"
                        note = "ntl_or_pop_late"
                        if t_ntl is not None:
                            flags["ntl"] = True
                        if t_pop is not None:
                            flags["pop"] = True
                else:
                    ctype = "B_EU_edu_u"
                    note = "no_long_stable_before_2022"
            else:
                ctype = "B_EU_edu_u"
                note = "env_changed_after_2022"

        # Original notebook comment normalized for the public code archive.
        if (not ctype.startswith("A_")) and (not ctype.startswith("B_")) \
           and (not np.isnan(eu)) and int(eu) in EULUC_URBAN_CLASSES:
            flags["urban"] = True

            t_imp = detect_jump_year(imp, years_clcd)
            t_ntl = detect_jump_year(ntl, years_ntl) if not np.all(np.isnan(ntl)) else None
            t_pop = detect_jump_year(pop, years_pop) if not np.all(np.isnan(pop)) else None

            cand = []
            if t_imp is not None:
                cand.append(t_imp)
                flags["clcd_pix"] = True
            if t_ntl is not None:
                cand.append(t_ntl)
                flags["ntl"] = True
            if t_pop is not None:
                cand.append(t_pop)
                flags["pop"] = True

            if cand:
                t_urban = max(cand)
                ymin = t_urban
                ymax = 2024
                ctype = "C_urban"
            else:
                ctype = "C_urban_N"
                note = "no_jump"

        if ctype == "D_NoDate" and urban:
            flags["urban"] = True

        case_type.append(ctype)
        r_min.append(ymin)
        r_max.append(ymax)
        flags_json.append(json.dumps(flags, ensure_ascii=False))
        notes.append(note)

    return case_type, r_min, r_max, flags_json, notes

# =============================================================================

def build_ml_dataset(years_clcd, years_ntl, years_pop,
                     imp_ts, ntl_ts, pop_ts,
                     is_urban,
                     case_type, r_min, r_max):

    n = imp_ts.shape[0]
    idx_2024 = years_clcd.index(2024)

    def safe_jump(arr2d, years):
        res = []
        for i in range(n):
            arr = arr2d[i, :]
            if np.all(np.isnan(arr)):
                res.append(np.nan)
            else:
                res.append(detect_jump_year(arr, years))
        return np.array(res, float)

    imp_jump = safe_jump(imp_ts, years_clcd)
    ntl_jump = safe_jump(ntl_ts, years_ntl)
    pop_jump = safe_jump(pop_ts, years_pop)

    imp_2024 = imp_ts[:, idx_2024]
    ntl_latest = np.nan_to_num(ntl_ts[:, -1], nan=0.0)
    pop_latest = np.nan_to_num(pop_ts[:, -1], nan=0.0)

    def encode_year(arr, ref=2024):
        arr = arr.astype(float)
        miss = np.isnan(arr)
        val = np.where(miss, 0, ref - arr)
        return val, miss.astype(int)

    f_impjmp, m_impjmp = encode_year(imp_jump)
    f_ntljmp, m_ntljmp = encode_year(ntl_jump)
    f_popjmp, m_popjmp = encode_year(pop_jump)

    X = np.column_stack([
        f_impjmp, m_impjmp,
        f_ntljmp, m_ntljmp,
        f_popjmp, m_popjmp,
        imp_2024,
        ntl_latest,
        pop_latest,
        is_urban.astype(int)
    ])

    # Original notebook comment normalized for the public code archive.
    level1_mask = np.array([
        (ct == "A_CLCD_direct") or (ct == "B_EU_edu_s")
        for ct in case_type
    ])

    y = np.array([
        r_min[i] if level1_mask[i] and r_min[i] is not None else np.nan
        for i in range(n)
    ], dtype=float)

    meta = {
        "imp_jump_year": imp_jump,
        "ntl_jump_year": ntl_jump,
        "pop_jump_year": pop_jump,
        "imp_2024": imp_2024,
        "ntl_latest": ntl_latest,
        "pop_latest": pop_latest,
        "level1_mask": level1_mask,
        "y_level1": y
    }

    return X, meta

# =============================================================================

def train_rf_model(X, meta):
    level1 = meta["level1_mask"]
    y = meta["y_level1"]
    idx = np.where(~np.isnan(y) & level1)[0]

    if idx.size < 50:
        print("[INFO] Notebook progress message.")
        return None

    X_train = X[idx, :]
    y_train = y[idx]

    X_tr, X_te, y_tr, y_te = train_test_split(
        X_train, y_train, test_size=0.2, random_state=RF_RANDOM_STATE
    )

    rf = RandomForestRegressor(
        n_estimators=RF_N_ESTIMATORS,
        max_depth=RF_MAX_DEPTH,
        random_state=RF_RANDOM_STATE,
        n_jobs=-1
    )
    rf.fit(X_tr, y_tr)

    if X_te.shape[0] > 0:
        pred = rf.predict(X_te)
        mae = float(np.mean(np.abs(pred - y_te)))
        print("[INFO] Notebook progress message.")

    return rf

# =============================================================================

def fuse_rule_and_model(X, meta, case_type, r_min, r_max, rf):
    n = X.shape[0]
    level1 = meta["level1_mask"]

    if rf is not None:
        model_pred = rf.predict(X)
        model_pred = np.clip(model_pred, 1950, 2025)
    else:
        model_pred = np.full(n, np.nan)

    build_year = []
    out_min = []
    out_max = []
    CI = []
    fuse_note = []

    for i in range(n):
        ct   = case_type[i]
        rmin = r_min[i]
        rmax = r_max[i]
        mp   = None if np.isnan(model_pred[i]) else float(model_pred[i])

        est = None
        cmin = rmin
        cmax = rmax
        ci = "NoDate"
        note = ""

        if level1[i] and rmin is not None:
            est  = float(rmin)
            cmin = float(rmin)
            cmax = float(rmax) if rmax is not None else float(rmin)
            ci   = "L1"
            note = "rule_strong"
        else:
            if rmin is not None or rmax is not None:
                if rmin is not None and rmax is not None:
                    if mp is not None and rmin <= mp <= rmax:
                        est = mp
                        width = rmax - rmin
                        if width <= 5:
                            ci = "L1"
                        elif width <= 10:
                            ci = "L2"
                        else:
                            ci = "L3"
                        note = "model_in_rule"
                    else:
                        est = (rmin + rmax) / 2.0
                        width = rmax - rmin
                        if width <= 5:
                            ci = "L2"
                        else:
                            ci = "L3"
                        note = "rule_mid"
                elif rmin is not None:
                    if mp is not None and mp >= rmin:
                        est = mp
                        ci = "L2"
                        note = "model_low"
                    else:
                        est = float(rmin)
                        ci = "L3"
                        note = "lb_only"
                else:  # only rmax
                    if mp is not None and mp <= rmax:
                        est = mp
                        ci = "L2"
                        note = "model_up"
                    else:
                        est = float(rmax)
                        ci = "L3"
                        note = "ub_only"
            else:
                if mp is not None:
                    est = mp
                    ci = "L3"
                    note = "model_only"

        build_year.append(est if est is not None else np.nan)
        out_min.append(cmin if cmin is not None else np.nan)
        out_max.append(cmax if cmax is not None else np.nan)
        CI.append(ci)
        fuse_note.append(note)

    return (np.array(build_year),
            np.array(out_min),
            np.array(out_max),
            CI,
            fuse_note)

# =============================================================================

def main():
    # Original notebook comment normalized for the public code archive.
    (years_clcd, years_ntl, years_pop,
     clcd_ts, lc_probs, imp_ts, ntl_ts, pop_ts,
     euluc_class, is_urban, schools) = compute_all_features()

    # Original notebook comment normalized for the public code archive.
    (case_type,
     r_min,
     r_max,
     flags_json,
     rule_notes) = rule_based_inference(
        years_clcd, years_ntl, years_pop,
        clcd_ts, lc_probs, imp_ts, ntl_ts, pop_ts,
        euluc_class, is_urban
    )

    # Original notebook comment normalized for the public code archive.
    X, meta = build_ml_dataset(
        years_clcd, years_ntl, years_pop,
        imp_ts, ntl_ts, pop_ts,
        is_urban,
        case_type, r_min, r_max
    )

    # Original notebook comment normalized for the public code archive.
    rf = train_rf_model(X, meta)

    # Original notebook comment normalized for the public code archive.
    (build_year,
     out_min,
     out_max,
     CI,
     fuse_note) = fuse_rule_and_model(
        X, meta,
        case_type, r_min, r_max,
        rf
    )

    # Original notebook comment normalized for the public code archive.
    out = schools.copy()
    out["case_type"] = case_type
    out["min"]       = out_min
    out["max"]       = out_max
    out["evi_flags"] = flags_json
    out["rule_note"] = rule_notes
    out["build_year"] = build_year
    out["CI"]         = CI
    out["fuse_note"]  = fuse_note

    # Original notebook comment normalized for the public code archive.
    out["CI"] = out["CI"].astype(str)

    out_L1L2 = out[out["CI"].isin(["L1", "L2"])].copy()
    out_all  = out.copy()

    # Shapefile output note.
    if len(out_L1L2) > 0:
        out_L1L2.to_file(L1L2_SHP, encoding="utf-8")
    else:
        print("[INFO] Notebook progress message.")

    out_all.to_file(L3_SHP, encoding="utf-8")

    # Excel output note.
    if len(out_L1L2) > 0:
        out_L1L2.drop(columns="geometry").to_excel(L1L2_XLSX, index=False)
    out_all.drop(columns="geometry").to_excel(L3_XLSX, index=False)

    print("[INFO] Notebook progress message.")
    print("  L1L2 ->", L1L2_SHP, "[INFO] Notebook progress message.", L1L2_XLSX)
    print("  L3   ->", L3_SHP,   "[INFO] Notebook progress message.", L3_XLSX)


if __name__ == "__main__":
    main()
