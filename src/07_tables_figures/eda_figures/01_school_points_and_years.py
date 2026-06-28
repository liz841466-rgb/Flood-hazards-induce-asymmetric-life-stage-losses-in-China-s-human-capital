#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 01_school_points_and_years.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from __future__ import annotations
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 3
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 01_school_points_and_years.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import warnings
warnings.filterwarnings("ignore")

import json
import math
import ast
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

import rasterio
from rasterio.transform import from_origin
from rasterio.features import rasterize
from shapely.prepared import prep


# =========================
# Source path: internal local path omitted from the public archive.
# =========================
SCHOOL_SHP = Path(r"E:\impact_assessment_child_order\data\supplement\school_points_EDA_county\china_school_L3\china_school_L3.shp")
COUNTY_SHP = Path(r"E:\impact_assessment_child_order\data\supplement\school_points_EDA_county\country\country.shp")

OUT_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\school_points_EDA_county\EDA_L1L2_AB_county")
OUT_FIG = OUT_DIR / "figs"
OUT_TAB = OUT_DIR / "tables"
OUT_RAS = OUT_DIR / "rasters"
for p in [OUT_FIG, OUT_TAB, OUT_RAS]:
    p.mkdir(parents=True, exist_ok=True)


# =========================
# Options
# =========================
CI_KEEP = {"L1", "L2"}
RULE_KEEP = {"A", "B"}         # Original notebook comment normalized for the public code archive.
YEAR_CEIL = 2020               # Original notebook comment normalized for the public code archive.
DENSITY_PER_KM2 = 100.0        # Original notebook comment normalized for the public code archive.
MORAN_PERMUTATIONS = 199
TOPK_COUNTIES = 50

# Original notebook comment normalized for the public code archive.
RASTER_RES_DEG = 0.05


# =========================
# Column candidates (robust)
# =========================
COUNTY_CODE_CANDIDATES = [
    "county_code", "县代码", "ADCODE", "adcode", "COUNTYCODE", "countyid", "county_id", "CODE", "code",
]
PROV_COL_CANDIDATES = ["prov", "PROV", "province", "PROVINCE", "省", "省份", "prov_name", "省名"]

# Original notebook comment normalized for the public code archive.
CASE_TYPE_COL_CANDIDATES = ["case_type", "CASE_TYPE", "case", "CASE"]
FUSE_NOTE_COL_CANDIDATES = ["fuse_note", "FUSE_NOTE", "fuse", "FUSE"]
EVI_FLAGS_COL_CANDIDATES = ["evi_flags", "EVI_FLAGS", "evi", "EVI"]


# =========================================================
# IO helpers
# =========================================================
def read_shp_safe(shp_path: Path) -> gpd.GeoDataFrame:
    encodings = [None, "gbk", "gb18030", "utf-8", "latin1"]
    last_err = None
    for enc in encodings:
        try:
            if enc is None:
                gdf = gpd.read_file(shp_path)
                print("[INFO] Notebook progress message.")
            else:
                gdf = gpd.read_file(shp_path, encoding=enc)
                print("[INFO] Notebook progress message.")
            return gdf
        except Exception as e:
            last_err = e
    raise RuntimeError(f"无法读取 {shp_path}") from last_err


def pick_first_existing_col(df: pd.DataFrame, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None


def ensure_wgs84(gdf: gpd.GeoDataFrame, name: str) -> gpd.GeoDataFrame:
    if gdf.crs is None:
        raise ValueError(f"{name} 缺少 CRS。请先写入正确 CRS（通常 EPSG:4326 或投影坐标系）。")
    return gdf.to_crs(epsg=4326)


# =========================================================
# Parse rule_group from case_type
# =========================================================
def rule_from_case_type(case_type: str) -> str:
    """Archived notebook note for 01_school_points_and_years.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if case_type is None:
        return "UNK"
    s = str(case_type).strip()
    if s == "" or s.lower() in {"nan", "none"}:
        return "UNK"
    # Original notebook comment normalized for the public code archive.
    prefix = s.split("_", 1)[0]
    prefix = prefix.strip()
    if prefix in {"A", "B", "C", "D"}:
        return prefix
    # Original notebook comment normalized for the public code archive.
    ch = prefix[:1].upper()
    if ch in {"A", "B", "C", "D"}:
        return ch
    return "UNK"


# =========================================================
# Parse evi_flags robustly
# =========================================================
def parse_evi_flags(val):
    """Archived notebook note for 01_school_points_and_years.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return {}
    if isinstance(val, dict):
        return val

    s = str(val).strip()
    if s == "" or s.lower() in {"nan", "none"}:
        return {}

    # Original notebook comment normalized for the public code archive.
    s_json = s.replace("'", '"')
    try:
        d = json.loads(s_json)
        if isinstance(d, dict):
            return d
    except Exception:
        pass

    # Original notebook comment normalized for the public code archive.
    s_py = (
        s.replace(": false", ": False")
         .replace(": true", ": True")
         .replace(": null", ": None")
    )
    try:
        d = ast.literal_eval(s_py)
        if isinstance(d, dict):
            return d
    except Exception:
        return {}

    return {}


def flag_get(d: dict, k: str) -> int:
    v = d.get(k, False)
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, (int, np.integer)):
        return int(v != 0)
    if isinstance(v, str):
        vv = v.strip().lower()
        if vv in {"true", "t", "1", "yes", "y"}:
            return 1
        if vv in {"false", "f", "0", "no", "n"}:
            return 0
    return 0


# =========================================================
# Load schools (L1/L2) + rule AB + build_year non-missing
# =========================================================
def load_schools_l1l2_ab() -> gpd.GeoDataFrame:
    print("[INFO] Notebook progress message.")
    gdf = read_shp_safe(SCHOOL_SHP)

    if "CI" not in gdf.columns:
        raise KeyError("学校 shapefile 缺少 CI 字段（用于筛选 L1/L2）")
    if "build_year" not in gdf.columns:
        raise KeyError("学校 shapefile 缺少 build_year 字段")

    case_col = pick_first_existing_col(gdf, CASE_TYPE_COL_CANDIDATES)
    fuse_col = pick_first_existing_col(gdf, FUSE_NOTE_COL_CANDIDATES)
    evi_col  = pick_first_existing_col(gdf, EVI_FLAGS_COL_CANDIDATES)

    if case_col is None:
        raise KeyError(f"找不到 case_type 列（你截图里有）。请检查列名。现有列：{list(gdf.columns)}")
    if fuse_col is None:
        print("[INFO] Notebook progress message.")
    if evi_col is None:
        print("[INFO] Notebook progress message.")

    n0 = len(gdf)

    # CI filter
    gdf = gdf[gdf["CI"].isin(list(CI_KEEP))].copy()

    # build_year non-missing
    gdf["build_year"] = pd.to_numeric(gdf["build_year"], errors="coerce")
    gdf = gdf.dropna(subset=["build_year"]).copy()
    gdf["build_year"] = gdf["build_year"].astype(int)

    # rule_group from case_type, keep AB
    gdf["_case_type"] = gdf[case_col].astype(str)
    gdf["rule_group"] = gdf["_case_type"].apply(rule_from_case_type)
    gdf = gdf[gdf["rule_group"].isin(list(RULE_KEEP))].copy()

    # fuse_note
    if fuse_col is not None:
        gdf["_fuse_note"] = gdf[fuse_col].astype(str)
    else:
        gdf["_fuse_note"] = "<NA>"

    # evi_flags -> columns
    if evi_col is not None:
        evi_dicts = gdf[evi_col].apply(parse_evi_flags)
        gdf["evi_clcd_pix"] = evi_dicts.apply(lambda d: flag_get(d, "clcd_pix")).astype(int)
        gdf["evi_clcd_env"] = evi_dicts.apply(lambda d: flag_get(d, "clcd_env")).astype(int)
        gdf["evi_ntl"]      = evi_dicts.apply(lambda d: flag_get(d, "ntl")).astype(int)
        gdf["evi_pop"]      = evi_dicts.apply(lambda d: flag_get(d, "pop")).astype(int)
        gdf["evi_edu"]      = evi_dicts.apply(lambda d: flag_get(d, "edu")).astype(int)
        gdf["evi_urban"]    = evi_dicts.apply(lambda d: flag_get(d, "urban")).astype(int)
        # Original notebook comment normalized for the public code archive.
        gdf["urban_proxy"]  = ((gdf["evi_urban"] == 1) | (gdf["evi_ntl"] == 1) | (gdf["evi_pop"] == 1)).astype(int)
        print("[INFO] Notebook progress message.")
    else:
        for c in ["evi_clcd_pix","evi_clcd_env","evi_ntl","evi_pop","evi_edu","evi_urban","urban_proxy"]:
            gdf[c] = 0

    # geometry / WGS84
    gdf = ensure_wgs84(gdf, "school points")
    gdf["lon"] = gdf.geometry.x
    gdf["lat"] = gdf.geometry.y

    # school_id
    if "prov" in gdf.columns and "sid" in gdf.columns:
        gdf["school_id"] = gdf["prov"].astype(str) + "_" + gdf["sid"].astype(str)
    else:
        gdf["school_id"] = gdf.index.astype(str)

    print("[INFO] Notebook progress message.")
    return gdf


def load_counties() -> gpd.GeoDataFrame:
    print("[INFO] Notebook progress message.")
    gdf = read_shp_safe(COUNTY_SHP)
    gdf = ensure_wgs84(gdf, "county polygons")

    code_col = pick_first_existing_col(gdf, COUNTY_CODE_CANDIDATES)
    if code_col is None:
        raise KeyError(f"县界找不到县代码字段。现有列：{list(gdf.columns)}")
    gdf["county_code"] = pd.to_numeric(gdf[code_col], errors="coerce").astype("Int64")
    gdf = gdf.dropna(subset=["county_code"]).copy()

    prov_col = pick_first_existing_col(gdf, PROV_COL_CANDIDATES)
    if prov_col is not None:
        gdf["_prov"] = gdf[prov_col].astype(str)
        print("[INFO] Notebook progress message.")
    else:
        gdf["_prov"] = "<NA>"

    return gdf[["county_code", "_prov", "geometry"]].copy()


def sjoin_school_county(sch: gpd.GeoDataFrame, cnty: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    print("[INFO] Notebook progress message.")
    j = gpd.sjoin(
        sch,
        cnty[["county_code", "_prov", "geometry"]],
        how="left",
        predicate="within",
    )
    n0 = len(j)
    j = j.dropna(subset=["county_code"]).copy()
    j["county_code"] = pd.to_numeric(j["county_code"], errors="coerce").astype("Int64")
    print("[INFO] Notebook progress message.")
    return j


# =========================================================
# County metrics + maps + outputs (vector + raster)
# =========================================================
def compute_county_area_km2(cnty_wgs84: gpd.GeoDataFrame) -> pd.Series:
    cnty_ea = cnty_wgs84.to_crs(epsg=6933)  # Original notebook comment normalized for the public code archive.
    return (cnty_ea.geometry.area / 1e6)


def county_basic_metrics(joined: gpd.GeoDataFrame, cnty: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    print("[INFO] Notebook progress message.")
    area_km2 = compute_county_area_km2(cnty)

    j = joined.copy()
    j = j[j["build_year"] <= YEAR_CEIL].copy()

    agg = (
        j.groupby(["county_code"], as_index=False)
        .agg(
            n_school=("school_id", "nunique"),
            n_L1=("CI", lambda x: int((x == "L1").sum())),
            n_L2=("CI", lambda x: int((x == "L2").sum())),
            share_L1=("CI", lambda x: float((x == "L1").mean()) if len(x) else np.nan),
            n_A=("rule_group", lambda x: int((x == "A").sum())),
            n_B=("rule_group", lambda x: int((x == "B").sum())),
            share_B=("rule_group", lambda x: float((x == "B").mean()) if len(x) else np.nan),
            share_evi_urban=("evi_urban", "mean"),
            share_urban_proxy=("urban_proxy", "mean"),
            share_evi_ntl=("evi_ntl", "mean"),
            share_evi_pop=("evi_pop", "mean"),
        )
    )

    out = cnty.copy()
    out["area_km2"] = area_km2.values
    out = out.merge(agg, on="county_code", how="left")

    for c in ["n_school","n_L1","n_L2","n_A","n_B"]:
        out[c] = out[c].fillna(0).astype(int)

    out["has_school"] = (out["n_school"] > 0).astype(int)
    out["density"] = out["n_school"] / out["area_km2"].replace({0: np.nan}) * DENSITY_PER_KM2
    out["density_unit"] = f"schools_per_{int(DENSITY_PER_KM2)}km2"

    coverage_rate = out["has_school"].mean()
    share_with_L2 = (out["n_L2"] > 0).mean()
    out_txt = OUT_TAB / "summary_key_stats_AB.txt"
    out_txt.write_text(
        f"YEAR_CEIL={YEAR_CEIL}\n"
        f"counties_total={len(out)}\n"
        f"coverage_rate_has_school={coverage_rate:.4f}\n"
        f"share_counties_with_L2={share_with_L2:.4f}\n",
        encoding="utf-8"
    )
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")

    # save table
    out_path = OUT_TAB / "county_school_basic_AB.parquet"
    out.to_parquet(out_path, index=False)
    print("[INFO] Notebook progress message.")

    # vector output (GPKG recommended)
    gpkg_path = OUT_TAB / "county_school_basic_AB.gpkg"
    out.to_file(gpkg_path, layer="county_school_basic_AB", driver="GPKG")
    print("[INFO] Notebook progress message.")

    # Shapefile output note.
    shp_path = OUT_TAB / "county_school_basic_AB.shp"
    try:
        out.to_file(shp_path, driver="ESRI Shapefile")
        print("[INFO] Notebook progress message.")
    except Exception as e:
        print("[INFO] Notebook progress message.")

    return out


def plot_choropleth(gdf: gpd.GeoDataFrame, col: str, title: str, out_png: Path, cmap="viridis"):
    fig, ax = plt.subplots(1, 1, figsize=(9.5, 8.5), dpi=220)
    gdf.plot(column=col, ax=ax, legend=True, cmap=cmap, linewidth=0.05, edgecolor="black")
    ax.set_title(title)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(out_png, bbox_inches="tight")
    plt.close(fig)
    print(f"[FIG] {out_png}")


def rasterize_county_values(county_gdf: gpd.GeoDataFrame, value_col: str, out_tif: Path, res_deg: float):
    """Archived notebook note for 01_school_points_and_years.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    g = county_gdf.copy()
    g = g[g.geometry.notna()].copy()

    minx, miny, maxx, maxy = g.total_bounds
    width = int(math.ceil((maxx - minx) / res_deg))
    height = int(math.ceil((maxy - miny) / res_deg))
    transform = from_origin(minx, maxy, res_deg, res_deg)

    shapes = [(geom, float(val) if pd.notna(val) else np.nan)
              for geom, val in zip(g.geometry.values, g[value_col].values)]

    arr = rasterize(
        shapes=shapes,
        out_shape=(height, width),
        transform=transform,
        fill=np.nan,
        all_touched=True,
        dtype="float32",
    )

    with rasterio.open(
        out_tif,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=transform,
        nodata=np.nan,
        compress="deflate",
    ) as dst:
        dst.write(arr, 1)

    print(f"[RASTER] {out_tif}  (res={res_deg} deg, shape={arr.shape})")


# =========================================================
# Moran's I (Queen adjacency)
# =========================================================
def queen_neighbors(gdf: gpd.GeoDataFrame):
    geoms = gdf.geometry.values
    sindex = gdf.sindex
    prepared = [prep(geom) for geom in geoms]
    neighbors = [[] for _ in range(len(gdf))]

    for i, geom in enumerate(geoms):
        cand_idx = list(sindex.intersection(geom.bounds))
        for j in cand_idx:
            if j == i:
                continue
            if prepared[i].intersects(geoms[j]):
                neighbors[i].append(j)

    return [sorted(list(set(nbs))) for nbs in neighbors]


def moran_I(x: np.ndarray, neighbors, permutations: int = 199, seed: int = 42):
    rng = np.random.default_rng(seed)
    x = np.asarray(x, dtype=float)
    mask = np.isfinite(x)

    idx = np.where(mask)[0]
    x = x[idx]

    old_to_new = {old: new for new, old in enumerate(idx)}
    nb2 = []
    for old in idx:
        nb2.append([old_to_new[n] for n in neighbors[old] if n in old_to_new])

    n = len(x)
    if n < 10:
        return dict(I=np.nan, p=np.nan, z=np.nan, n=n)

    z = x - x.mean()
    denom = np.sum(z * z)
    if denom == 0:
        return dict(I=np.nan, p=np.nan, z=np.nan, n=n)

    num = 0.0
    wsum = 0.0
    for i in range(n):
        nbs = nb2[i]
        if len(nbs) == 0:
            continue
        w = 1.0 / len(nbs)
        wsum += 1.0
        for j in nbs:
            num += w * z[i] * z[j]

    if wsum == 0:
        return dict(I=np.nan, p=np.nan, z=np.nan, n=n)

    I_obs = (n / wsum) * (num / denom)

    I_perm = []
    for _ in range(permutations):
        z_perm = rng.permutation(z)
        nump = 0.0
        wsum_p = 0.0
        for i in range(n):
            nbs = nb2[i]
            if len(nbs) == 0:
                continue
            w = 1.0 / len(nbs)
            wsum_p += 1.0
            for j in nbs:
                nump += w * z_perm[i] * z_perm[j]
        I_perm.append((n / wsum_p) * (nump / denom))

    I_perm = np.array(I_perm)
    p = (np.sum(np.abs(I_perm) >= abs(I_obs)) + 1) / (permutations + 1)
    zscore = (I_obs - I_perm.mean()) / (I_perm.std(ddof=1) + 1e-12)

    return dict(I=float(I_obs), p=float(p), z=float(zscore), n=int(n))


def run_moran(county_gdf: gpd.GeoDataFrame):
    print("[INFO] Notebook progress message.")
    g = county_gdf.copy()
    g = g[g.geometry.notna()].copy()
    g = g[g["area_km2"] > 0].copy()

    neighbors = queen_neighbors(g)
    res = moran_I(g["density"].to_numpy(), neighbors, permutations=MORAN_PERMUTATIONS)

    txt = (
        f"Moran's I on county density ({g['density_unit'].iloc[0]}), "
        f"n={res['n']}, I={res['I']:.4f}, z={res['z']:.3f}, p={res['p']:.4f}, perms={MORAN_PERMUTATIONS}\n"
    )
    print("[INFO] " + txt.strip())

    out_txt = OUT_TAB / "moran_density_AB.txt"
    out_txt.write_text(txt, encoding="utf-8")
    print("[INFO] Notebook progress message.")


# =========================================================
# Plots: box + jitter (avoid degenerate boxplot confusion)
# =========================================================
def box_with_jitter(values: np.ndarray, title: str, ylab: str, out_png: Path, ylim=None):
    v = values[np.isfinite(values)]
    fig, ax = plt.subplots(1, 1, figsize=(6.2, 5.2), dpi=220)
    ax.boxplot(v, vert=True, showfliers=True)

    # jitter
    if len(v) > 0:
        x = 1 + (np.random.default_rng(0).random(len(v)) - 0.5) * 0.10
        ax.scatter(x, v, s=6, alpha=0.25)

    ax.set_title(title)
    ax.set_ylabel(ylab)
    ax.set_xticks([])
    if ylim is not None:
        ax.set_ylim(*ylim)
    fig.tight_layout()
    fig.savefig(out_png, bbox_inches="tight")
    plt.close(fig)
    print(f"[FIG] {out_png}")


def run_boxplots(county_gdf: gpd.GeoDataFrame):
    # Original notebook comment normalized for the public code archive.
    sub = county_gdf[county_gdf["has_school"] == 1].copy()

    # 1) share_L1
    box_with_jitter(
        values=sub["share_L1"].to_numpy(dtype=float),
        title=f"County share_L1 among (L1+L2) schools (rule A/B, build_year <= {YEAR_CEIL})",
        ylab="share_L1",
        out_png=OUT_FIG / "box_share_L1_by_county_AB.png",
        ylim=(0, 1)
    )

    # Original notebook comment normalized for the public code archive.
    vals = sub["n_L2"].to_numpy()
    fig, ax = plt.subplots(1, 1, figsize=(7.8, 4.6), dpi=220)
    ax.hist(vals, bins=np.arange(vals.min(), vals.max() + 2), density=False)
    ax.set_title(f"n_L2 by county (rule A/B, build_year <= {YEAR_CEIL})")
    ax.set_xlabel("n_L2")
    ax.set_ylabel("count of counties")
    fig.tight_layout()
    fig.savefig(OUT_FIG / "hist_n_L2_by_county_AB.png", bbox_inches="tight")
    plt.close(fig)
    print(f"[FIG] {OUT_FIG / 'hist_n_L2_by_county_AB.png'}")

    # Original notebook comment normalized for the public code archive.
    box_with_jitter(
        values=sub["share_urban_proxy"].to_numpy(dtype=float),
        title=f"County urban-proxy share (mean(urban OR ntl OR pop), rule A/B, build_year <= {YEAR_CEIL})",
        ylab="share_urban_proxy",
        out_png=OUT_FIG / "box_share_urbanproxy_by_county_AB.png",
        ylim=(0, 1)
    )


# =========================================================
# Rule contribution (A/B) + evidence flags
# =========================================================
def run_rule_and_evidence_summaries(joined: gpd.GeoDataFrame):
    j = joined.copy()
    j = j[j["build_year"] <= YEAR_CEIL].copy()

    # overall A/B share
    overall = (
        j.groupby("rule_group", as_index=False)
        .agg(n=("school_id", "nunique"))
        .sort_values("n", ascending=False)
    )
    total = overall["n"].sum()
    overall["share"] = overall["n"] / (total if total > 0 else 1)
    overall.to_csv(OUT_TAB / "rule_AB_overall.csv", index=False)
    print("[INFO] Notebook progress message.")

    fig, ax = plt.subplots(1, 1, figsize=(6.0, 4.2), dpi=220)
    ax.bar(overall["rule_group"].astype(str), overall["share"].to_numpy())
    ax.set_title(f"Overall share by rule_group (A/B, build_year <= {YEAR_CEIL})")
    ax.set_ylabel("share of schools")
    fig.tight_layout()
    fig.savefig(OUT_FIG / "rule_AB_bar.png", bbox_inches="tight")
    plt.close(fig)
    print(f"[FIG] {OUT_FIG / 'rule_AB_bar.png'}")

    # by county topK
    tot = j.groupby("county_code")["school_id"].nunique().rename("n_total").sort_values(ascending=False)
    top = tot.head(TOPK_COUNTIES).index

    byc = (
        j.groupby(["county_code", "rule_group"], as_index=False)
        .agg(n=("school_id", "nunique"))
    )
    byc = byc.merge(tot.rename("n_total"), on="county_code", how="left")
    byc["share"] = byc["n"] / byc["n_total"].replace({0: np.nan})
    byc_top = byc[byc["county_code"].isin(top)].copy()
    byc_top.to_csv(OUT_TAB / "rule_AB_by_county_top.csv", index=False)
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    evi_cols = ["evi_clcd_pix","evi_clcd_env","evi_ntl","evi_pop","evi_edu","evi_urban"]
    evi_overall = pd.DataFrame({
        "flag": evi_cols,
        "mean": [float(j[c].mean()) for c in evi_cols],
        "sum":  [int(j[c].sum()) for c in evi_cols],
        "n":    [int(j[c].shape[0]) for c in evi_cols],
    }).sort_values("mean", ascending=False)
    evi_overall.to_csv(OUT_TAB / "evidence_flags_overall.csv", index=False)
    print("[INFO] Notebook progress message.")

    # evidence flags by county topK
    evi_byc = (
        j[j["county_code"].isin(top)]
        .groupby("county_code", as_index=False)
        .agg(**{f"share_{c}": (c, "mean") for c in evi_cols})
    )
    evi_byc.to_csv(OUT_TAB / "evidence_flags_by_county_top.csv", index=False)
    print("[INFO] Notebook progress message.")


# =========================================================
# Original notebook comment normalized for the public code archive.
# =========================================================
def run_build_year_eda(sch: gpd.GeoDataFrame):
    print("[INFO] Notebook progress message.")
    by_all = sch["build_year"].astype(int).to_numpy()

    fig, ax = plt.subplots(1, 1, figsize=(9.2, 4.8), dpi=220)
    bins = np.arange(by_all.min(), by_all.max() + 2, 1)
    ax.hist(by_all, bins=bins, density=False)
    ax.set_title("build_year distribution (CI in {L1,L2}, rule A/B)")
    ax.set_xlabel("build_year")
    ax.set_ylabel("count of schools")
    fig.tight_layout()
    fig.savefig(OUT_FIG / "buildyear_hist_AB.png", bbox_inches="tight")
    plt.close(fig)
    print(f"[FIG] {OUT_FIG / 'buildyear_hist_AB.png'}")

    # Original notebook comment normalized for the public code archive.
    year_counts = pd.Series(by_all).value_counts().sort_index()
    years = year_counts.index.to_numpy()
    counts = year_counts.values.astype(float)
    pd.DataFrame({"build_year": years, "n_new_schools": counts}).to_csv(
        OUT_TAB / "build_year_counts_AB.csv", index=False
    )
    print("[INFO] Notebook progress message.")

    fig, ax = plt.subplots(1, 1, figsize=(10.2, 4.2), dpi=220)
    ax.plot(years, counts, linewidth=1.2)
    ax.set_title("New schools by build_year (counts, rule A/B)")
    ax.set_xlabel("build_year")
    ax.set_ylabel("n_new_schools")
    fig.tight_layout()
    fig.savefig(OUT_FIG / "buildyear_new_schools_ts_AB.png", bbox_inches="tight")
    plt.close(fig)
    print(f"[FIG] {OUT_FIG / 'buildyear_new_schools_ts_AB.png'}")


# =========================================================
# Main
# =========================================================
def main():
    # 0) load
    sch = load_schools_l1l2_ab()
    cnty = load_counties()

    # 1) join
    joined = sjoin_school_county(sch, cnty)

    # 2) county metrics
    county_gdf = county_basic_metrics(joined, cnty)

    # 3) maps (vector choropleth)
    plot_choropleth(
        county_gdf,
        col="n_school",
        title=f"County n_school (CI in {{L1,L2}}, rule A/B, build_year <= {YEAR_CEIL})",
        out_png=OUT_FIG / "map_n_school_AB.png",
        cmap="viridis",
    )
    plot_choropleth(
        county_gdf,
        col="density",
        title=f"County density ({county_gdf['density_unit'].iloc[0]}), rule A/B, build_year <= {YEAR_CEIL}",
        out_png=OUT_FIG / "map_density_AB.png",
        cmap="viridis",
    )
    plot_choropleth(
        county_gdf,
        col="has_school",
        title=f"County coverage (has >=1 school, rule A/B, build_year <= {YEAR_CEIL})",
        out_png=OUT_FIG / "map_has_school_AB.png",
        cmap="Greys",
    )

    # 4) raster outputs
    rasterize_county_values(
        county_gdf, "n_school",
        OUT_RAS / f"county_n_school_AB_{str(RASTER_RES_DEG).replace('.','p')}deg.tif",
        res_deg=RASTER_RES_DEG
    )
    rasterize_county_values(
        county_gdf, "density",
        OUT_RAS / f"county_density_AB_{str(RASTER_RES_DEG).replace('.','p')}deg.tif",
        res_deg=RASTER_RES_DEG
    )

    # 5) spatial clustering
    run_moran(county_gdf)

    # 6) boxplots (share_L1 / n_L2 / urban proxy)
    run_boxplots(county_gdf)

    # 7) rule & evidence summaries
    run_rule_and_evidence_summaries(joined)

    # 8) build_year EDA
    run_build_year_eda(sch)

    print("[INFO] Notebook progress message.")
    print(f"  figs:    {OUT_FIG}")
    print(f"  tables:  {OUT_TAB}")
    print(f"  rasters: {OUT_RAS}")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 5
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Only 2 plots (vertical layout, 2x1), publication-style:

  (A) Build year distribution (annual counts; bar)
  (B) New schools by build year (annual counts; line)

Layout + style targets (match your reference screenshot):
  - Vertical 2x1, shared x-axis
  - All English, Times New Roman
  - Horizontal year tick labels (e.g., 1985, 1990...) for readability
  - Bar color: #a7b7aa
  - Export: PNG + SVG

Input (latest Windows path):
  SCHOOL_SHP:
    E:\impact_assessment_child_order\data\supplement\school_points_EDA_county\china_school_L3\china_school_L3.shp

Output:
  E:\impact_assessment_child_order\data\supplement\school_points_EDA_county\EDA_L1L2_AB_county\figs\
    buildyear_hist_and_ts_AB_vertical.png
    buildyear_hist_and_ts_AB_vertical.svg

Filters:
  - CI in {L1, L2}
  - build_year not null
  - rule_group in {A, B} inferred from case_type
  - (default) build_year <= YEAR_CEIL (2020); set YEAR_CEIL=None to disable
"""

import warnings
warnings.filterwarnings("ignore")

from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt

# =========================
# Paths (latest)
# =========================
SCHOOL_SHP = Path(r"E:\impact_assessment_child_order\data\supplement\school_points_EDA_county\china_school_L3\china_school_L3.shp")

OUT_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\school_points_EDA_county\EDA_L1L2_AB_county")
OUT_FIG = OUT_DIR / "figs"
OUT_FIG.mkdir(parents=True, exist_ok=True)

OUT_PNG = OUT_FIG / "buildyear_hist_and_ts_AB_vertical.png"
OUT_SVG = OUT_FIG / "buildyear_hist_and_ts_AB_vertical.svg"

# =========================
# Options
# =========================
CI_KEEP = {"L1", "L2"}
RULE_KEEP = {"A", "B"}
YEAR_CEIL = 2020  # set None to disable ceiling

CASE_TYPE_COL_CANDIDATES = ["case_type", "CASE_TYPE", "case", "CASE"]

# =========================
# Figure style config
# =========================
BAR_COLOR = "#a7b7aa"

FIGSIZE = (9.6, 9.6)  # tweak to match your layout
DPI = 300

TITLE_FS = 16
LABEL_FS = 15
TICK_FS = 12
LINE_LW = 1.6
BAR_EDGE_LW = 0.0

GRID_LS = "--"
GRID_LW = 0.8
GRID_ALPHA = 0.35

# X ticks step
XTICK_STEP_LONG = 5
XTICK_STEP_SHORT = 2
LONG_SPAN_THRESHOLD = 30

# =========================
# Global plotting style
# =========================
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams["figure.dpi"] = DPI
mpl.rcParams["savefig.dpi"] = DPI
mpl.rcParams["pdf.fonttype"] = 42
mpl.rcParams["ps.fonttype"] = 42
mpl.rcParams["svg.fonttype"] = "none"  # keep text as text in SVG


# =========================
# Helpers
# =========================
def read_shp_safe(shp_path: Path) -> gpd.GeoDataFrame:
    encodings = [None, "gbk", "gb18030", "utf-8", "latin1"]
    last_err = None
    for enc in encodings:
        try:
            if enc is None:
                gdf = gpd.read_file(shp_path)
                print(f"[INFO] Read {shp_path.name} success (encoding=auto)")
            else:
                gdf = gpd.read_file(shp_path, encoding=enc)
                print(f"[INFO] Read {shp_path.name} success (encoding={enc})")
            return gdf
        except Exception as e:
            last_err = e
    raise RuntimeError(f"Failed to read: {shp_path}") from last_err


def pick_first_existing_col(df: pd.DataFrame, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None


def rule_from_case_type(case_type: str) -> str:
    """
    case_type examples: A_CLCD_direct, B_xxx, C_urban_xxx, D_NoDate
    """
    if case_type is None:
        return "UNK"
    s = str(case_type).strip()
    if s == "" or s.lower() in {"nan", "none"}:
        return "UNK"
    prefix = s.split("_", 1)[0].strip()
    if prefix in {"A", "B", "C", "D"}:
        return prefix
    ch = prefix[:1].upper()
    return ch if ch in {"A", "B", "C", "D"} else "UNK"


def load_schools_l1l2_ab_buildyear() -> pd.Series:
    print(f"[STEP] Load school shp: {SCHOOL_SHP}")
    gdf = read_shp_safe(SCHOOL_SHP)

    if "CI" not in gdf.columns:
        raise KeyError("School shp missing column: CI")
    if "build_year" not in gdf.columns:
        raise KeyError("School shp missing column: build_year")

    case_col = pick_first_existing_col(gdf, CASE_TYPE_COL_CANDIDATES)
    if case_col is None:
        raise KeyError(
            f"School shp missing case_type-like column. Existing cols={list(gdf.columns)}"
        )

    n0 = len(gdf)

    # CI filter
    gdf = gdf[gdf["CI"].isin(list(CI_KEEP))].copy()

    # build_year filter
    gdf["build_year"] = pd.to_numeric(gdf["build_year"], errors="coerce")
    gdf = gdf.dropna(subset=["build_year"]).copy()
    gdf["build_year"] = gdf["build_year"].astype(int)

    # rule_group filter
    gdf["rule_group"] = gdf[case_col].apply(rule_from_case_type)
    gdf = gdf[gdf["rule_group"].isin(list(RULE_KEEP))].copy()

    # optional YEAR_CEIL
    if YEAR_CEIL is not None:
        gdf = gdf[gdf["build_year"] <= int(YEAR_CEIL)].copy()

    print(
        f"[INFO] Schools: raw={n0} -> filtered={len(gdf)} "
        f"(CI=L1/L2, rule=A/B, year_ceiling={YEAR_CEIL})"
    )

    if len(gdf) == 0:
        raise RuntimeError(
            "No schools left after filtering. Check CI/case_type/build_year/year_ceiling."
        )

    return gdf["build_year"].astype(int)


def style_axes(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.grid(True, linestyle=GRID_LS, linewidth=GRID_LW, alpha=GRID_ALPHA)
    ax.set_axisbelow(True)


def save_fig(fig, png_path: Path, svg_path: Path, dpi: int = 300) -> None:
    png_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(png_path, dpi=dpi, bbox_inches="tight")
    fig.savefig(svg_path, bbox_inches="tight")
    print(f"[SAVE] {png_path}")
    print(f"[SAVE] {svg_path}")


# =========================
# Main
# =========================
def main():
    by = load_schools_l1l2_ab_buildyear().to_numpy(dtype=int)

    # annual counts
    year_counts = pd.Series(by).value_counts().sort_index()
    years = year_counts.index.to_numpy(dtype=int)
    counts = year_counts.values.astype(float)

    ymin = int(years.min())
    ymax = int(years.max())

    # x ticks step
    step = XTICK_STEP_LONG if (ymax - ymin) > LONG_SPAN_THRESHOLD else XTICK_STEP_SHORT
    xticks = np.arange((ymin // step) * step, ymax + 1, step)

    # ---- Figure (vertical 2x1) ----
    fig, (ax1, ax2) = plt.subplots(
        2, 1,
        figsize=FIGSIZE,
        dpi=DPI,
        sharex=True,
        gridspec_kw={"height_ratios": [1.05, 1.0], "hspace": 0.12},
    )

    # Panel A: annual bar distribution
    ax1.bar(
        years,
        counts,
        width=0.90,
        color=BAR_COLOR,
        edgecolor=BAR_COLOR,
        linewidth=BAR_EDGE_LW,
    )
    ax1.set_ylabel("Count of schools", fontsize=LABEL_FS)
    ax1.set_title(
        "Build year distribution (CI in {L1, L2}, rule group {A, B})",
        fontsize=TITLE_FS,
        pad=8,
    )
    ax1.tick_params(axis="y", labelsize=TICK_FS)
    style_axes(ax1)

    # Panel B: annual new schools time series
    ax2.plot(years, counts, linewidth=LINE_LW)
    ax2.set_xlabel("Build year", fontsize=LABEL_FS)
    ax2.set_ylabel("New schools (count)", fontsize=LABEL_FS)
    ax2.tick_params(axis="y", labelsize=TICK_FS)
    style_axes(ax2)

    # Shared x axis formatting (horizontal labels)
    ax2.set_xticks(xticks)
    ax2.tick_params(axis="x", labelsize=TICK_FS, rotation=0)

    # xlim padding
    ax2.set_xlim(ymin - 0.8, ymax + 0.8)

    # Tight layout
    plt.tight_layout()

    save_fig(fig, OUT_PNG, OUT_SVG, dpi=DPI)
    plt.close(fig)

    print("[DONE] Vertical build_year distribution + time series (PNG+SVG).")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 9
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Print total number of schools (overall / rural-county / urban-county)
====================================================================

Urban/rural county definition (same as your micro regression):
  suffix = county_code % 100
  urban-county = 1(suffix in [1,20]) else 0

Inputs (latest Windows paths):
  1) School points shp:
     E:\impact_assessment_child_order\data\supplement\school_points_EDA_county\china_school_L3\china_school_L3.shp
  2) County polygons shp (for spatial join to county_code):
     E:\impact_assessment_child_order\data\supplement\school_points_EDA_county\country\country.shp
  3) Micro parquet (for the set of counties used to define county groups; optional but recommended):
     E:\impact_assessment_child_order\data\supplement\school_points_EDA_county\edu_micro_2015_BM_school_exposure.parquet

What it prints:
  - total schools after filters (CI in {L1,L2}, build_year not null, build_year<=YEAR_MAX)
  - total schools in counties appearing in micro data (recommended for EDA consistency)
  - rural-county schools count
  - urban-county schools count

Notes:
  - By default we count unique schools using "school_id" if possible, else fall back to row count.
  - If your school shp has duplicated points/rows, ensure school_id is truly unique.
"""

import warnings
warnings.filterwarnings("ignore")

from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd


# =========================
# Paths
# =========================
SCHOOL_SHP = Path(r"E:\impact_assessment_child_order\data\supplement\school_points_EDA_county\china_school_L3\china_school_L3.shp")
COUNTY_SHP = Path(r"E:\impact_assessment_child_order\data\supplement\school_points_EDA_county\country\country.shp")
MICRO_PARQUET = Path(r"E:\impact_assessment_child_order\data\supplement\school_points_EDA_county\edu_micro_2015_BM_school_exposure.parquet")

# =========================
# Options
# =========================
CI_KEEP = {"L1", "L2"}
YEAR_MAX = 2020  # set None to disable year ceiling

COUNTY_CODE_CANDIDATES = [
    "county_code", "县代码", "ADCODE", "adcode", "COUNTYCODE", "countyid", "county_id", "CODE", "code",
]


# =========================
# Helpers
# =========================
def read_shp_safe(shp_path: Path) -> gpd.GeoDataFrame:
    encodings = [None, "gbk", "gb18030", "utf-8", "latin1"]
    last_err = None
    for enc in encodings:
        try:
            if enc is None:
                gdf = gpd.read_file(shp_path)
                print(f"[INFO] Read {shp_path.name} success (encoding=auto)")
            else:
                gdf = gpd.read_file(shp_path, encoding=enc)
                print(f"[INFO] Read {shp_path.name} success (encoding={enc})")
            return gdf
        except Exception as e:
            last_err = e
    raise RuntimeError(f"Failed to read: {shp_path}") from last_err


def ensure_wgs84(gdf: gpd.GeoDataFrame, name: str) -> gpd.GeoDataFrame:
    if gdf.crs is None:
        raise ValueError(f"{name} missing CRS. Please set CRS before running.")
    return gdf.to_crs(epsg=4326)


def pick_first_existing_col(df: pd.DataFrame, candidates) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def county_is_urban_from_code(county_code: pd.Series) -> pd.Series:
    cc = pd.to_numeric(county_code, errors="coerce")
    suffix = (cc % 100).astype("Int64")
    return ((suffix >= 1) & (suffix <= 20)).astype(int)


def get_school_id(gdf: gpd.GeoDataFrame) -> pd.Series:
    """
    Prefer stable unique id if available; otherwise fall back to index.
    """
    if "school_id" in gdf.columns:
        return gdf["school_id"].astype(str)
    if ("prov" in gdf.columns) and ("sid" in gdf.columns):
        return (gdf["prov"].astype(str) + "_" + gdf["sid"].astype(str))
    return gdf.index.astype(str)


def load_micro_county_set() -> set[int]:
    """
    Use micro data to define the county universe for grouping (recommended).
    """
    df = pd.read_parquet(MICRO_PARQUET)
    if "county_code" in df.columns:
        cc = pd.to_numeric(df["county_code"], errors="coerce")
    elif "M2" in df.columns:
        cc = pd.to_numeric(df["M2"], errors="coerce")
    else:
        raise KeyError("Micro parquet must contain county_code or M2.")
    cc = cc.dropna().astype("Int64").astype(int)
    return set(cc.unique().tolist())


def load_schools_filtered() -> gpd.GeoDataFrame:
    gdf = read_shp_safe(SCHOOL_SHP)

    if "CI" not in gdf.columns:
        raise KeyError("School shp missing field: CI")
    if "build_year" not in gdf.columns:
        raise KeyError("School shp missing field: build_year")

    # filter CI
    gdf = gdf[gdf["CI"].isin(list(CI_KEEP))].copy()

    # filter build_year
    gdf["build_year"] = pd.to_numeric(gdf["build_year"], errors="coerce")
    gdf = gdf.dropna(subset=["build_year"]).copy()
    gdf["build_year"] = gdf["build_year"].astype(int)

    # optional year ceiling
    if YEAR_MAX is not None:
        gdf = gdf[gdf["build_year"] <= int(YEAR_MAX)].copy()

    gdf = ensure_wgs84(gdf, "schools")
    gdf["school_id"] = get_school_id(gdf)

    return gdf[["school_id", "CI", "build_year", "geometry"]].copy()


def load_counties() -> gpd.GeoDataFrame:
    cnty = read_shp_safe(COUNTY_SHP)
    cnty = ensure_wgs84(cnty, "counties")

    code_col = pick_first_existing_col(cnty, COUNTY_CODE_CANDIDATES)
    if code_col is None:
        raise KeyError(f"County shp missing county code field. Existing cols={list(cnty.columns)}")

    cnty["county_code"] = pd.to_numeric(cnty[code_col], errors="coerce").astype("Int64")
    cnty = cnty.dropna(subset=["county_code"]).copy()

    return cnty[["county_code", "geometry"]].copy()


def sjoin_school_to_county(sch: gpd.GeoDataFrame, cnty: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    j = gpd.sjoin(
        sch,
        cnty[["county_code", "geometry"]],
        how="left",
        predicate="within",
    )
    j = j.dropna(subset=["county_code"]).copy()
    j["county_code"] = pd.to_numeric(j["county_code"], errors="coerce").astype("Int64")
    return j


def main():
    # Load
    sch = load_schools_filtered()
    cnty = load_counties()
    j = sjoin_school_to_county(sch, cnty)

    # County group (urban/rural) from county_code suffix
    j["county_is_urban"] = county_is_urban_from_code(j["county_code"])

    # (Recommended) restrict counties to those appearing in micro data
    micro_counties = load_micro_county_set()
    j_micro = j[j["county_code"].astype(int).isin(micro_counties)].copy()

    # Counts (unique schools)
    total_all = j["school_id"].nunique()
    total_micro = j_micro["school_id"].nunique()

    rural_micro = j_micro.loc[j_micro["county_is_urban"] == 0, "school_id"].nunique()
    urban_micro = j_micro.loc[j_micro["county_is_urban"] == 1, "school_id"].nunique()

    print("============================================================")
    print("[FILTERS]")
    print(f"  CI in {sorted(list(CI_KEEP))}")
    print(f"  build_year not null")
    print(f"  build_year <= {YEAR_MAX}" if YEAR_MAX is not None else "  build_year ceiling: None")
    print("============================================================")
    print("[TOTAL SCHOOLS] (after filters)")
    print(f"  All matched-to-county schools: {int(total_all)}")
    print("------------------------------------------------------------")
    print("[TOTAL SCHOOLS IN MICRO COUNTY UNIVERSE] (recommended for EDA)")
    print(f"  All (micro counties only): {int(total_micro)}")
    print(f"  Rural-county schools:      {int(rural_micro)}")
    print(f"  Urban-county schools:      {int(urban_micro)}")
    print("============================================================")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 14
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 01_school_points_and_years.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import warnings
warnings.filterwarnings("ignore")

from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt


# =========================
# Paths
# =========================
SCHOOL_SHP = Path(r"E:\impact_assessment_child_order\data\supplement\school_points_EDA_county\china_school_L3\china_school_L3.shp")
COUNTY_SHP = Path(r"E:\impact_assessment_child_order\data\supplement\school_points_EDA_county\country\country.shp")

MICRO_PARQUET = Path(r"E:\impact_assessment_child_order\data\supplement\school_points_EDA_county\edu_micro_2015_BM_school_exposure.parquet")

OUT_DIR = Path("E:\impact_assessment_child_order\data\supplement\school_points_EDA_county\EDA_L1L2_AB_county\EDA_county_urbanRural_fromMicro_only2fig")
OUT_FIG = OUT_DIR / "figs"
OUT_TAB = OUT_DIR / "tables"
OUT_FIG.mkdir(parents=True, exist_ok=True)
OUT_TAB.mkdir(parents=True, exist_ok=True)

# =========================
# Options
# =========================
CI_KEEP = {"L1", "L2"}
YEAR_MAX = 2020  # Original notebook comment normalized for the public code archive.

COUNTY_CODE_CANDIDATES = [
    "county_code", "县代码", "ADCODE", "adcode", "COUNTYCODE", "countyid", "county_id", "CODE", "code",
]


# =========================================================
# Helpers
# =========================================================
def read_shp_safe(shp_path: Path) -> gpd.GeoDataFrame:
    encodings = [None, "gbk", "gb18030", "utf-8", "latin1"]
    last_err = None
    for enc in encodings:
        try:
            if enc is None:
                gdf = gpd.read_file(shp_path)
                print(f"[INFO] Read {shp_path.name} success (encoding=auto)")
            else:
                gdf = gpd.read_file(shp_path, encoding=enc)
                print(f"[INFO] Read {shp_path.name} success (encoding={enc})")
            return gdf
        except Exception as e:
            last_err = e
    raise RuntimeError(f"Failed to read: {shp_path}") from last_err


def ensure_wgs84(gdf: gpd.GeoDataFrame, name: str) -> gpd.GeoDataFrame:
    if gdf.crs is None:
        raise ValueError(f"{name} missing CRS. Please set CRS before running.")
    return gdf.to_crs(epsg=4326)


def pick_first_existing_col(df: pd.DataFrame, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None


def county_is_urban_from_code(county_code: pd.Series) -> pd.Series:
    cc = pd.to_numeric(county_code, errors="coerce")
    suffix = (cc % 100).astype("Int64")
    return ((suffix >= 1) & (suffix <= 20)).astype(int)


# =========================================================
# 0) urban/rural county set from micro data
# =========================================================
def load_micro_county_groups():
    """Archived notebook note for 01_school_points_and_years.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print(f"[STEP] Load micro data for county group definition: {MICRO_PARQUET}")
    df = pd.read_parquet(MICRO_PARQUET)

    if "M2" not in df.columns and "county_code" not in df.columns:
        raise KeyError("Micro parquet must contain M2 or county_code.")

    if "county_code" in df.columns:
        cc = pd.to_numeric(df["county_code"], errors="coerce")
    else:
        cc = pd.to_numeric(df["M2"], errors="coerce")

    cc = cc.dropna().astype("Int64")
    cnty = pd.DataFrame({"county_code": cc.unique()})
    cnty["county_is_urban"] = county_is_urban_from_code(cnty["county_code"])

    print(f"[INFO] Micro counties: {len(cnty)} (urban={int((cnty['county_is_urban']==1).sum())}, rural={int((cnty['county_is_urban']==0).sum())})")
    return cnty


# =========================================================
# 1) load schools + counties + spatial join
# =========================================================
def load_schools_l1l2() -> gpd.GeoDataFrame:
    print(f"[STEP] Load school points: {SCHOOL_SHP}")
    sch = read_shp_safe(SCHOOL_SHP)

    if "CI" not in sch.columns:
        raise KeyError("School shp missing field: CI")
    if "build_year" not in sch.columns:
        raise KeyError("School shp missing field: build_year")

    n0 = len(sch)
    sch = sch[sch["CI"].isin(list(CI_KEEP))].copy()
    n1 = len(sch)

    sch["build_year"] = pd.to_numeric(sch["build_year"], errors="coerce")
    sch = sch.dropna(subset=["build_year"]).copy()
    sch["build_year"] = sch["build_year"].astype(int)

    # Original notebook comment normalized for the public code archive.
    sch = sch[sch["build_year"] <= YEAR_MAX].copy()

    print(f"[INFO] Schools: raw={n0}, keep CI(L1/L2)={n1}, keep build_year notna & <= {YEAR_MAX} => {len(sch)}")

    sch = ensure_wgs84(sch, "schools")
    sch["lon"] = sch.geometry.x
    sch["lat"] = sch.geometry.y

    if "prov" in sch.columns and "sid" in sch.columns:
        sch["school_id"] = sch["prov"].astype(str) + "_" + sch["sid"].astype(str)
    else:
        sch["school_id"] = sch.index.astype(str)

    return sch[["school_id", "CI", "build_year", "lon", "lat", "geometry"]].copy()


def load_counties() -> gpd.GeoDataFrame:
    print(f"[STEP] Load county polygons: {COUNTY_SHP}")
    cnty = read_shp_safe(COUNTY_SHP)
    cnty = ensure_wgs84(cnty, "counties")

    code_col = pick_first_existing_col(cnty, COUNTY_CODE_CANDIDATES)
    if code_col is None:
        raise KeyError(f"County shp missing county code field. Existing cols={list(cnty.columns)}")

    cnty["county_code"] = pd.to_numeric(cnty[code_col], errors="coerce").astype("Int64")
    cnty = cnty.dropna(subset=["county_code"]).copy()

    return cnty[["county_code", "geometry"]].copy()


def sjoin_school_to_county(sch: gpd.GeoDataFrame, cnty: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    print("[STEP] Spatial join (schools within county)")
    j = gpd.sjoin(
        sch,
        cnty[["county_code", "geometry"]],
        how="left",
        predicate="within",
    )
    n0 = len(j)
    j = j.dropna(subset=["county_code"]).copy()
    j["county_code"] = pd.to_numeric(j["county_code"], errors="coerce").astype("Int64")
    print(f"[INFO] sjoin: total={n0}, matched={len(j)}")
    return j


# =========================================================
# 2) only two figures
# =========================================================
def plot_box_n_school_by_group(j: gpd.GeoDataFrame, df_cnty_group: pd.DataFrame):
    """Archived notebook note for 01_school_points_and_years.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print("[STEP] Plot box_n_school_by_group")

    county_n = (
        j.groupby("county_code", as_index=False)
        .agg(n_school=("school_id", "nunique"))
    )

    # Original notebook comment normalized for the public code archive.
    out = county_n.merge(df_cnty_group, on="county_code", how="inner")
    out_path = OUT_TAB / "county_n_school.parquet"
    out.to_parquet(out_path, index=False)
    print(f"[DONE] county_n_school saved: {out_path} (n_counties={len(out)})")

    rural = out.loc[out["county_is_urban"] == 0, "n_school"].to_numpy()
    urban = out.loc[out["county_is_urban"] == 1, "n_school"].to_numpy()

    fig, ax = plt.subplots(1, 1, figsize=(7.2, 5.2), dpi=220)
    ax.boxplot([rural, urban], labels=["rural-county", "urban-county"], showfliers=True)
    ax.set_title(f"n_school (CI in {{L1,L2}}, build_year<={YEAR_MAX}) by county group (from micro M2)")
    ax.set_ylabel("n_school")
    fig.tight_layout()
    fig.savefig(OUT_FIG / "box_n_school_by_group.png", bbox_inches="tight")
    plt.close(fig)
    print(f"[FIG] {OUT_FIG / 'box_n_school_by_group.png'}")


def plot_buildyear_hist_by_group(j: gpd.GeoDataFrame, df_cnty_group: pd.DataFrame):
    """Archived notebook note for 01_school_points_and_years.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print("[STEP] Plot build_year hist (schools) by county group (from micro M2)")

    jj = j.merge(df_cnty_group, on="county_code", how="inner")

    rural_year = jj.loc[jj["county_is_urban"] == 0, "build_year"].to_numpy()
    urban_year = jj.loc[jj["county_is_urban"] == 1, "build_year"].to_numpy()

    # export counts table (optional but useful)
    tab = (
        jj.groupby(["county_is_urban", "build_year"], as_index=False)
        .agg(n_new_schools=("school_id", "nunique"))
        .sort_values(["county_is_urban", "build_year"])
    )
    tab.to_csv(OUT_TAB / "buildyear_by_group_counts.csv", index=False, encoding="utf-8-sig")
    print(f"[DONE] buildyear_by_group_counts saved: {OUT_TAB / 'buildyear_by_group_counts.csv'}")

    if len(rural_year) == 0 or len(urban_year) == 0:
        print("[WARN] One group has zero schools after merging with micro counties; skip hist.")
        return

    ymin = int(min(rural_year.min(), urban_year.min()))
    ymax = int(max(rural_year.max(), urban_year.max()))
    bins = np.arange(ymin, ymax + 2, 1)

    fig, ax = plt.subplots(1, 1, figsize=(10.0, 4.8), dpi=220)
    ax.hist(rural_year, bins=bins, density=True, alpha=0.35, label="rural-county schools")
    ax.hist(urban_year, bins=bins, density=True, alpha=0.35, label="urban-county schools")
    ax.set_title(f"build_year distribution (CI in {{L1,L2}}, build_year<={YEAR_MAX}) by county group (from micro M2)")
    ax.set_xlabel("build_year")
    ax.set_ylabel("density")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT_FIG / "buildyear_hist_urban_vs_rural.png", bbox_inches="tight")
    plt.close(fig)
    print(f"[FIG] {OUT_FIG / 'buildyear_hist_urban_vs_rural.png'}")


# =========================================================
# Main
# =========================================================
def main():
    # A) county group definition from micro data
    df_cnty_group = load_micro_county_groups()

    # B) school points and spatial join to county_code
    sch = load_schools_l1l2()
    cnty = load_counties()
    j = sjoin_school_to_county(sch, cnty)

    # C) two figs
    plot_box_n_school_by_group(j, df_cnty_group)
    plot_buildyear_hist_by_group(j, df_cnty_group)

    print("[ALL DONE]")
    print(f"  figs:   {OUT_FIG}")
    print(f"  tables: {OUT_TAB}")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 19
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Export data for box_n_school_by_group (county-level n_school + county urban/rural group)
======================================================================================

County urban/rural definition (from MICRO data, consistent with your regression):
  suffix = county_code % 100
  county_is_urban = 1 if suffix in [1,20] else 0

School filters:
  - CI in {L1, L2}
  - build_year <= 2020
  - rule_group in {A, B}  (inferred from school attributes, e.g., case_type starts with 'A'/'B')

Inputs (latest paths):
  SCHOOL_SHP:
    E:\impact_assessment_child_order\data\supplement\school_points_EDA_county\china_school_L3\china_school_L3.shp
  COUNTY_SHP:
    E:\impact_assessment_child_order\data\supplement\school_points_EDA_county\country\country.shp
  MICRO_PARQUET:
    E:\impact_assessment_child_order\data\supplement\school_points_EDA_county\edu_micro_2015_BM_school_exposure.parquet

Outputs:
  OUT_DIR\tables\
    county_n_school_for_box.parquet
    county_n_school_for_box.csv
"""

import warnings
warnings.filterwarnings("ignore")

from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd

# =========================
# Paths (LATEST)
# =========================
SCHOOL_SHP = Path(r"E:\impact_assessment_child_order\data\supplement\school_points_EDA_county\china_school_L3\china_school_L3.shp")
COUNTY_SHP = Path(r"E:\impact_assessment_child_order\data\supplement\school_points_EDA_county\country\country.shp")
MICRO_PARQUET = Path(r"E:\impact_assessment_child_order\data\supplement\school_points_EDA_county\edu_micro_2015_BM_school_exposure.parquet")

OUT_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\school_points_EDA_county\EDA_L1L2_AB_county\EDA_county_urbanRural_fromMicro_only2fig")
OUT_TAB = OUT_DIR / "tables"
OUT_TAB.mkdir(parents=True, exist_ok=True)

# =========================
# Options
# =========================
CI_KEEP = {"L1", "L2"}
RULE_KEEP = {"A", "B"}
YEAR_MAX = 2020

COUNTY_CODE_CANDIDATES = [
    "county_code", "县代码", "ADCODE", "adcode", "COUNTYCODE",
    "countyid", "county_id", "CODE", "code",
]

# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------
def read_shp_safe(shp_path: Path) -> gpd.GeoDataFrame:
    encodings = [None, "gbk", "gb18030", "utf-8", "latin1"]
    last_err = None
    for enc in encodings:
        try:
            if enc is None:
                gdf = gpd.read_file(shp_path)
                print(f"[INFO] Read {shp_path.name} success (encoding=auto)")
            else:
                gdf = gpd.read_file(shp_path, encoding=enc)
                print(f"[INFO] Read {shp_path.name} success (encoding={enc})")
            return gdf
        except Exception as e:
            last_err = e
    raise RuntimeError(f"Failed to read: {shp_path}") from last_err


def ensure_wgs84(gdf: gpd.GeoDataFrame, name: str) -> gpd.GeoDataFrame:
    if gdf.crs is None:
        raise ValueError(f"{name} missing CRS. Please set CRS before running.")
    return gdf.to_crs(epsg=4326)


def pick_first_existing_col(df: pd.DataFrame, candidates) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def county_is_urban_from_code(county_code: pd.Series) -> pd.Series:
    cc = pd.to_numeric(county_code, errors="coerce")
    suffix = (cc % 100).astype("Int64")
    return ((suffix >= 1) & (suffix <= 20)).astype(int)


def infer_rule_group_from_school(sch: gpd.GeoDataFrame) -> pd.Series:
    """
    Try infer A/B/C/D rule group from school attributes.
    Typical fields you showed: case_type like 'A_CLCD_direct', 'D_NoDate', 'C_urban_N', etc.
    We take the FIRST CHAR (upper) if it is in {A,B,C,D}.
    """
    cand_cols = ["rule_group", "rule", "RULE", "case_type", "CASE_TYPE", "case", "CASE"]
    col = pick_first_existing_col(sch, cand_cols)
    if col is None:
        return pd.Series(pd.array([pd.NA] * len(sch), dtype="string"))

    s = sch[col].astype(str).str.strip()
    first = s.str[0].str.upper()
    first = first.where(first.isin(list("ABCD")), pd.NA)
    return first.astype("string")


# ---------------------------------------------------------
# Step 1: county groups from MICRO
# ---------------------------------------------------------
def load_micro_county_groups() -> pd.DataFrame:
    """
    Read micro parquet and deduplicate counties.
    Use 'county_code' if exists else use 'M2'.
    """
    print(f"[STEP] Load micro data: {MICRO_PARQUET}")
    df = pd.read_parquet(MICRO_PARQUET)

    if ("county_code" not in df.columns) and ("M2" not in df.columns):
        raise KeyError("Micro parquet must contain 'county_code' or 'M2'.")

    cc = pd.to_numeric(df["county_code"] if "county_code" in df.columns else df["M2"], errors="coerce")
    cc = cc.dropna().astype("Int64")

    out = pd.DataFrame({"county_code": pd.array(pd.unique(cc), dtype="Int64")})
    out = out.dropna(subset=["county_code"]).copy()
    out["county_is_urban"] = county_is_urban_from_code(out["county_code"])

    print(
        f"[INFO] Micro counties: {len(out)} | "
        f"urban={int((out['county_is_urban']==1).sum())}, "
        f"rural={int((out['county_is_urban']==0).sum())}"
    )
    return out


# ---------------------------------------------------------
# Step 2: schools -> county_code via sjoin, then aggregate n_school
# ---------------------------------------------------------
def load_counties() -> gpd.GeoDataFrame:
    print(f"[STEP] Load county polygons: {COUNTY_SHP}")
    cnty = read_shp_safe(COUNTY_SHP)
    cnty = ensure_wgs84(cnty, "counties")

    code_col = pick_first_existing_col(cnty, COUNTY_CODE_CANDIDATES)
    if code_col is None:
        raise KeyError(f"County shp missing county-code field. Existing cols={list(cnty.columns)}")

    cnty["county_code"] = pd.to_numeric(cnty[code_col], errors="coerce").astype("Int64")
    cnty = cnty.dropna(subset=["county_code"]).copy()
    return cnty[["county_code", "geometry"]].copy()


def load_schools_filtered() -> gpd.GeoDataFrame:
    print(f"[STEP] Load school points: {SCHOOL_SHP}")
    sch = read_shp_safe(SCHOOL_SHP)

    for req in ["CI", "build_year"]:
        if req not in sch.columns:
            raise KeyError(f"School shp missing field: {req}")

    n0 = len(sch)

    # CI filter
    sch = sch[sch["CI"].isin(list(CI_KEEP))].copy()

    # build_year filter
    sch["build_year"] = pd.to_numeric(sch["build_year"], errors="coerce")
    sch = sch.dropna(subset=["build_year"]).copy()
    sch["build_year"] = sch["build_year"].astype(int)
    sch = sch[sch["build_year"] <= YEAR_MAX].copy()

    # infer rule group and enforce A/B
    sch["_rule_group"] = infer_rule_group_from_school(sch)
    if not sch["_rule_group"].notna().any():
        raise KeyError(
            "Cannot infer rule group from school attributes. "
            "Please ensure school shp has 'case_type' (e.g., 'A_CLCD_direct') or 'rule_group'."
        )

    before = len(sch)
    sch = sch[sch["_rule_group"].isin(list(RULE_KEEP))].copy()
    print(f"[INFO] Schools: raw={n0}, after CI/build_year={before}, keep rule A/B => {len(sch)}")

    sch = ensure_wgs84(sch, "schools")

    # school_id (robust)
    if "prov" in sch.columns and "sid" in sch.columns:
        sch["school_id"] = sch["prov"].astype(str) + "_" + sch["sid"].astype(str)
    else:
        sch["school_id"] = sch.index.astype(str)

    return sch[["school_id", "CI", "build_year", "_rule_group", "geometry"]].copy()


def sjoin_school_to_county(sch: gpd.GeoDataFrame, cnty: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    print("[STEP] Spatial join: schools within county")
    j = gpd.sjoin(sch, cnty, how="left", predicate="within")
    n0 = len(j)
    j = j.dropna(subset=["county_code"]).copy()
    j["county_code"] = pd.to_numeric(j["county_code"], errors="coerce").astype("Int64")
    print(f"[INFO] sjoin: total={n0}, matched={len(j)}")
    return j


def build_county_n_school(j: gpd.GeoDataFrame, micro_groups: pd.DataFrame) -> pd.DataFrame:
    """
    County-level n_school, then merge micro-based county_is_urban.
    Inner-join: only counties that appear in micro data (as requested).
    """
    county_n = (
        j.groupby("county_code", as_index=False)
        .agg(n_school=("school_id", "nunique"))
    )

    out = county_n.merge(micro_groups, on="county_code", how="inner")
    out["county_group"] = np.where(out["county_is_urban"] == 1, "urban-county", "rural-county")

    print(f"[INFO] Counties in output: {len(out)}")
    print(out.head())
    return out


def main():
    micro_groups = load_micro_county_groups()
    cnty = load_counties()
    sch = load_schools_filtered()
    j = sjoin_school_to_county(sch, cnty)

    out = build_county_n_school(j, micro_groups)

    out_parquet = OUT_TAB / "county_n_school_for_box.parquet"
    out_csv = OUT_TAB / "county_n_school_for_box.csv"
    out.to_parquet(out_parquet, index=False)
    out.to_csv(out_csv, index=False, encoding="utf-8-sig")

    print(f"[SAVE] {out_parquet}")
    print(f"[SAVE] {out_csv}")
    print("[DONE] Export finished.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 21
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Plot box_n_school_by_group (visualization only)
===============================================

Input:
  tables/county_n_school_for_box.parquet  (exported by the companion script)

Output:
  figs/box_n_school_by_group.png

Design (borrowed from your reference):
  - 2 groups: Rural county / Urban county
  - NO points, NO outlier dots (showfliers=False)
  - Box face colors + group-specific line colors
  - Dashed whiskers
  - Optional winsorize + log1p transform (off by default)
  - Whiskers default percentile-style (5,95) to mimic sampling plots
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# =========================
# Paths
# =========================
BASE_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\school_points_EDA_county\EDA_L1L2_AB_county\EDA_county_urbanRural_fromMicro_only2fig")
IN_DATA  = BASE_DIR / "tables" / "county_n_school_for_box.parquet"
OUT_FIG  = BASE_DIR / "figs"
OUT_FIG.mkdir(parents=True, exist_ok=True)

OUT_PNG = OUT_FIG / "box_n_school_by_group.png"

# =========================
# Options
# =========================
# Robust transform (OFF by default; set True if you want)
BOX_WINSOR_Q = None     # e.g., 0.99 ; set None to disable
BOX_LOG1P = False       # set True to plot log(1+n_school)

# Whiskers: percentile-style (recommended for your style)
BOX_WHIS = (5, 95)
# If you prefer Tukey:
# BOX_WHIS = 1.5

# =========================
# Style (match your reference)
# =========================
BOX_FACE = {"rural": "#de77ae", "urban": "#35978f"}
LINE_COL = {"rural": "#c51b7d", "urban": "#01665e"}

BOX_ALPHA = 0.55
BOX_LW = 1.0
MED_LW = 1.0
WHISK_LW = 1.0
CAP_LW = 1.0
WHISK_LS = "--"  # dashed whiskers

mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams["figure.dpi"] = 300
mpl.rcParams["pdf.fonttype"] = 42
mpl.rcParams["ps.fonttype"] = 42


def save_fig(fig, out_path: Path, dpi: int = 300) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    print(f"[SAVE] {out_path}")


def winsorize_upper_np(x: np.ndarray, q: float) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if x.size == 0:
        return x
    cap = float(np.quantile(x, q))
    return np.minimum(x, cap)


def transform_arr(x: np.ndarray) -> np.ndarray:
    z = np.asarray(x, dtype=float)
    z = z[~np.isnan(z)]
    if (BOX_WINSOR_Q is not None) and (z.size > 0):
        z = winsorize_upper_np(z, BOX_WINSOR_Q)
    if BOX_LOG1P:
        z = np.log1p(z)
    return z


def style_boxplot_artists(bp, labels: list[str]) -> None:
    """
    Apply:
      - face color with alpha
      - edges/whiskers/caps/median in group color
      - dashed whiskers
    """
    n = len(labels)

    for i in range(n):
        g = labels[i]
        box = bp["boxes"][i]
        box.set_facecolor(BOX_FACE[g])
        box.set_alpha(BOX_ALPHA)
        box.set_edgecolor(LINE_COL[g])
        box.set_linewidth(BOX_LW)

        med = bp["medians"][i]
        med.set_color(LINE_COL[g])
        med.set_linewidth(MED_LW)

    for i in range(n):
        g = labels[i]
        for w in (bp["whiskers"][2 * i], bp["whiskers"][2 * i + 1]):
            w.set_color(LINE_COL[g])
            w.set_linewidth(WHISK_LW)
            w.set_linestyle(WHISK_LS)

        for c in (bp["caps"][2 * i], bp["caps"][2 * i + 1]):
            c.set_color(LINE_COL[g])
            c.set_linewidth(CAP_LW)


def main():
    print(f"[READ] {IN_DATA}")
    df = pd.read_parquet(IN_DATA)

    if "county_is_urban" not in df.columns or "n_school" not in df.columns:
        raise KeyError("Input must contain columns: county_is_urban, n_school")

    rural = df.loc[df["county_is_urban"] == 0, "n_school"].to_numpy()
    urban = df.loc[df["county_is_urban"] == 1, "n_school"].to_numpy()

    rural_t = transform_arr(rural)
    urban_t = transform_arr(urban)

    labels = ["rural", "urban"]
    data_for_box = [rural_t, urban_t]
    xlabels = ["Rural", "Urban"]

    ylabel = "Number of schools per county"
    if BOX_WINSOR_Q is not None:
        ylabel += f" (winsorized at {BOX_WINSOR_Q:.2f})"
    if BOX_LOG1P:
        ylabel = "log(1 + Number of schools) (per county)"

    fig, ax = plt.subplots(figsize=(6.6, 3.9), dpi=300)

    bp = ax.boxplot(
        data_for_box,
        positions=[1, 2],
        widths=0.15,
        patch_artist=True,
        showfliers=False,      # IMPORTANT: no outlier dots
        whis=BOX_WHIS,
        boxprops=dict(linewidth=BOX_LW),
        medianprops=dict(linewidth=MED_LW),
        whiskerprops=dict(linewidth=WHISK_LW),
        capprops=dict(linewidth=CAP_LW),
    )

    style_boxplot_artists(bp, labels)

    ax.set_xticks([1, 2])
    ax.set_xticklabels(xlabels, fontsize=14)
    ax.set_ylabel(ylabel, fontsize=14)
    ax.set_title("County-level school counts", fontsize=14, pad=8)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.grid(True, linestyle="--", linewidth=0.8, alpha=0.35)
    ax.set_axisbelow(True)

    plt.tight_layout()
    save_fig(fig, OUT_PNG, dpi=300)
    plt.close(fig)

    print("[DONE] box_n_school_by_group plotted.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 24
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EXPORT: Urban-county vs Rural-county new schools by build_year
=============================================================

County urban/rural definition (coarse, consistent with your micro regressions):
  suffix = county_code % 100
  county_is_urban = 1 if suffix in [1,20] else 0

School filters:
  - CI in {L1, L2}
  - build_year non-missing
  - build_year <= YEAR_MAX (default 2020)

Outputs (tables only):
  OUT_TAB/
    - new_schools_by_year_urban_rural.csv
        build_year, n_new_rural, n_new_urban   (one year, two columns)
    - new_schools_by_5yr_urban_rural.csv
        bin_start, bin_label, n_new_rural, n_new_urban   (5-year bins)
"""

import warnings
warnings.filterwarnings("ignore")

from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd

# =========================
# Paths (latest Windows)
# =========================
SCHOOL_SHP = Path(r"E:\impact_assessment_child_order\data\supplement\school_points_EDA_county\china_school_L3\china_school_L3.shp")
COUNTY_SHP = Path(r"E:\impact_assessment_child_order\data\supplement\school_points_EDA_county\country\country.shp")
MICRO_PARQUET = Path(r"E:\impact_assessment_child_order\data\supplement\school_points_EDA_county\edu_micro_2015_BM_school_exposure.parquet")

OUT_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\school_points_EDA_county\EDA_L1L2_AB_county\EDA_county_urbanRural_fromMicro_only2fig")
OUT_TAB = OUT_DIR / "tables"
OUT_TAB.mkdir(parents=True, exist_ok=True)

# =========================
# Options
# =========================
CI_KEEP = {"L1", "L2"}
YEAR_MAX = 2020

COUNTY_CODE_CANDIDATES = [
    "county_code", "县代码", "ADCODE", "adcode", "COUNTYCODE",
    "countyid", "county_id", "CODE", "code",
]

# =========================
# Helpers
# =========================
def read_shp_safe(shp_path: Path) -> gpd.GeoDataFrame:
    encodings = [None, "gbk", "gb18030", "utf-8", "latin1"]
    last_err = None
    for enc in encodings:
        try:
            if enc is None:
                gdf = gpd.read_file(shp_path)
            else:
                gdf = gpd.read_file(shp_path, encoding=enc)
            print(f"[INFO] Read {shp_path.name} success (encoding={'auto' if enc is None else enc})")
            return gdf
        except Exception as e:
            last_err = e
    raise RuntimeError(f"Failed to read: {shp_path}") from last_err

def ensure_wgs84(gdf: gpd.GeoDataFrame, name: str) -> gpd.GeoDataFrame:
    if gdf.crs is None:
        raise ValueError(f"{name} missing CRS. Please set CRS before running.")
    return gdf.to_crs(epsg=4326)

def pick_first_existing_col(df: pd.DataFrame, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None

def county_is_urban_from_code(county_code: pd.Series) -> pd.Series:
    cc = pd.to_numeric(county_code, errors="coerce")
    suffix = (cc % 100).astype("Int64")
    return ((suffix >= 1) & (suffix <= 20)).astype(int)

# =========================
# 0) county groups from micro
# =========================
def load_micro_county_groups() -> pd.DataFrame:
    print(f"[STEP] Load micro data: {MICRO_PARQUET}")
    df = pd.read_parquet(MICRO_PARQUET)

    if "M2" not in df.columns and "county_code" not in df.columns:
        raise KeyError("Micro parquet must contain M2 or county_code.")

    cc = pd.to_numeric(df["county_code"], errors="coerce") if "county_code" in df.columns else pd.to_numeric(df["M2"], errors="coerce")
    cc = cc.dropna().astype("Int64")

    out = pd.DataFrame({"county_code": pd.Series(cc.unique(), dtype="Int64")})
    out["county_is_urban"] = county_is_urban_from_code(out["county_code"])

    print(f"[INFO] Micro counties: {len(out)} (urban={(out['county_is_urban']==1).sum()}, rural={(out['county_is_urban']==0).sum()})")
    return out

# =========================
# 1) schools + counties + sjoin
# =========================
def load_schools_l1l2() -> gpd.GeoDataFrame:
    print(f"[STEP] Load school points: {SCHOOL_SHP}")
    sch = read_shp_safe(SCHOOL_SHP)

    if "CI" not in sch.columns:
        raise KeyError("School shp missing field: CI")
    if "build_year" not in sch.columns:
        raise KeyError("School shp missing field: build_year")

    sch = sch[sch["CI"].isin(list(CI_KEEP))].copy()
    sch["build_year"] = pd.to_numeric(sch["build_year"], errors="coerce")
    sch = sch.dropna(subset=["build_year"]).copy()
    sch["build_year"] = sch["build_year"].astype(int)
    sch = sch[sch["build_year"] <= YEAR_MAX].copy()

    sch = ensure_wgs84(sch, "schools")

    if "prov" in sch.columns and "sid" in sch.columns:
        sch["school_id"] = sch["prov"].astype(str) + "_" + sch["sid"].astype(str)
    else:
        sch["school_id"] = sch.index.astype(str)

    print(f"[INFO] Schools kept: {len(sch)} (CI=L1/L2, build_year<= {YEAR_MAX})")
    return sch[["school_id", "build_year", "geometry"]].copy()

def load_counties() -> gpd.GeoDataFrame:
    print(f"[STEP] Load county polygons: {COUNTY_SHP}")
    cnty = read_shp_safe(COUNTY_SHP)
    cnty = ensure_wgs84(cnty, "counties")

    code_col = pick_first_existing_col(cnty, COUNTY_CODE_CANDIDATES)
    if code_col is None:
        raise KeyError(f"County shp missing county code field. Existing cols={list(cnty.columns)}")

    cnty["county_code"] = pd.to_numeric(cnty[code_col], errors="coerce").astype("Int64")
    cnty = cnty.dropna(subset=["county_code"]).copy()
    return cnty[["county_code", "geometry"]].copy()

def sjoin_school_to_county(sch: gpd.GeoDataFrame, cnty: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    print("[STEP] Spatial join (schools within county)")
    j = gpd.sjoin(sch, cnty[["county_code", "geometry"]], how="left", predicate="within")
    j = j.dropna(subset=["county_code"]).copy()
    j["county_code"] = pd.to_numeric(j["county_code"], errors="coerce").astype("Int64")
    print(f"[INFO] Matched schools: {len(j)}")
    return j

# =========================
# 2) build tables
# =========================
def make_annual_and_5yr_tables(j: gpd.GeoDataFrame, df_cnty_group: pd.DataFrame):
    # keep only schools whose counties appear in micro (group definition source)
    jj = j.merge(df_cnty_group, on="county_code", how="inner").copy()

    # annual new schools (by build_year)
    annual = (
        jj.groupby(["county_is_urban", "build_year"], as_index=False)
          .agg(n_new=("school_id", "nunique"))
    )

    # pivot to 2 columns
    wide = annual.pivot(index="build_year", columns="county_is_urban", values="n_new").fillna(0).astype(int)
    # 0=rural, 1=urban
    wide = wide.rename(columns={0: "n_new_rural", 1: "n_new_urban"}).reset_index()

    # ensure continuous years
    y_min = int(wide["build_year"].min())
    y_max = int(wide["build_year"].max())
    full_years = pd.DataFrame({"build_year": np.arange(y_min, y_max + 1, 1)})
    wide = full_years.merge(wide, on="build_year", how="left").fillna(0)
    wide[["n_new_rural", "n_new_urban"]] = wide[["n_new_rural", "n_new_urban"]].astype(int)

    out1 = OUT_TAB / "new_schools_by_year_urban_rural.csv"
    wide.to_csv(out1, index=False, encoding="utf-8-sig")
    print(f"[SAVE] {out1}")

    # 5-year bins
    def bin_start(y: int) -> int:
        return int((y // 5) * 5)

    jj["bin_start"] = jj["build_year"].apply(bin_start).astype(int)
    five = (
        jj.groupby(["county_is_urban", "bin_start"], as_index=False)
          .agg(n_new=("school_id", "nunique"))
    )
    five_wide = five.pivot(index="bin_start", columns="county_is_urban", values="n_new").fillna(0).astype(int)
    five_wide = five_wide.rename(columns={0: "n_new_rural", 1: "n_new_urban"}).reset_index()
    five_wide["bin_label"] = five_wide["bin_start"].astype(str) + "-" + (five_wide["bin_start"] + 4).astype(str)
    five_wide = five_wide.sort_values("bin_start").reset_index(drop=True)

    out2 = OUT_TAB / "new_schools_by_5yr_urban_rural.csv"
    five_wide.to_csv(out2, index=False, encoding="utf-8-sig")
    print(f"[SAVE] {out2}")

def main():
    df_cnty_group = load_micro_county_groups()
    sch = load_schools_l1l2()
    cnty = load_counties()
    j = sjoin_school_to_county(sch, cnty)
    make_annual_and_5yr_tables(j, df_cnty_group)
    print("[DONE] Tables exported.")

if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 27
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PLOT:
  1) Annual new schools: 1 year, 2 bars (NOT stacked)
  2) 5-year new schools: 2 lines

Inputs:
  OUT_TAB/
    - new_schools_by_year_urban_rural.csv
    - new_schools_by_5yr_urban_rural.csv
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# =========================
# Paths
# =========================
OUT_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\school_points_EDA_county\EDA_L1L2_AB_county\EDA_county_urbanRural_fromMicro_only2fig")
OUT_TAB = OUT_DIR / "tables"
OUT_FIG = OUT_DIR / "figs"
OUT_FIG.mkdir(parents=True, exist_ok=True)

IN_ANNUAL = OUT_TAB / "new_schools_by_year_urban_rural.csv"
IN_FIVE   = OUT_TAB / "new_schools_by_5yr_urban_rural.csv"

# =========================
# Global style
# =========================
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams["figure.dpi"] = 300
mpl.rcParams["pdf.fonttype"] = 42
mpl.rcParams["ps.fonttype"] = 42

def save_fig(fig, out_path: Path, dpi: int = 300) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    print(f"[SAVE] {out_path}")

# =========================
# Fig 1: annual (2 bars per year, not stacked)
# =========================
def plot_annual_two_bars(df: pd.DataFrame):
    years = df["build_year"].astype(int).to_numpy()
    rural = df["n_new_rural"].astype(float).to_numpy()
    urban = df["n_new_urban"].astype(float).to_numpy()

    x = np.arange(len(years))
    w = 0.42

    fig, ax = plt.subplots(figsize=(12.8, 4.6), dpi=300)

    ax.bar(x - w/2, rural, width=w, label="Rural-county")
    ax.bar(x + w/2, urban, width=w, label="Urban-county")

    # tick density control (avoid overcrowding)
    step = 5 if len(years) > 60 else 2
    tick_idx = np.arange(0, len(years), step)
    ax.set_xticks(tick_idx)
    ax.set_xticklabels(years[tick_idx], rotation=0)

    ax.set_xlabel("Build year", fontsize=14)
    ax.set_ylabel("Number of newly built schools", fontsize=14)
    ax.set_title("Annual new schools (CI=L1/L2, build_year<=2020)", fontsize=13, pad=8)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.grid(True, linestyle="--", linewidth=0.8, alpha=0.35)
    ax.set_axisbelow(True)

    ax.legend(frameon=False, fontsize=12)
    plt.tight_layout()
    save_fig(fig, OUT_FIG / "annual_new_schools_urban_vs_rural_bars.png", dpi=300)
    plt.close(fig)

# =========================
# Fig 2: 5-year lines
# =========================
def plot_5yr_lines(df: pd.DataFrame):
    x = df["bin_start"].astype(int).to_numpy()
    rural = df["n_new_rural"].astype(float).to_numpy()
    urban = df["n_new_urban"].astype(float).to_numpy()

    fig, ax = plt.subplots(figsize=(10.8, 4.6), dpi=300)
    ax.plot(x, rural, marker="o", linewidth=1.6, label="Rural-county")
    ax.plot(x, urban, marker="o", linewidth=1.6, label="Urban-county")

    ax.set_xlabel("5-year bin (start year)", fontsize=14)
    ax.set_ylabel("Number of newly built schools", fontsize=14)
    ax.set_title("New schools by 5-year bins (CI=L1/L2, build_year<=2020)", fontsize=13, pad=8)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.grid(True, linestyle="--", linewidth=0.8, alpha=0.35)
    ax.set_axisbelow(True)

    ax.legend(frameon=False, fontsize=12)
    plt.tight_layout()
    save_fig(fig, OUT_FIG / "new_schools_5yr_urban_vs_rural_lines.png", dpi=300)
    plt.close(fig)

def main():
    df_a = pd.read_csv(IN_ANNUAL)
    df_5 = pd.read_csv(IN_FIVE)

    # basic validation
    need_a = {"build_year", "n_new_rural", "n_new_urban"}
    need_5 = {"bin_start", "n_new_rural", "n_new_urban"}
    if not need_a.issubset(df_a.columns):
        raise KeyError(f"Annual file missing columns: {need_a - set(df_a.columns)}")
    if not need_5.issubset(df_5.columns):
        raise KeyError(f"5yr file missing columns: {need_5 - set(df_5.columns)}")

    plot_annual_two_bars(df_a)
    plot_5yr_lines(df_5)

    print("[DONE] 2 figures generated.")

if __name__ == "__main__":
    main()
