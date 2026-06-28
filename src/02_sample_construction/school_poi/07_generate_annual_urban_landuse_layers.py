#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 07_generate_annual_urban_landuse_layers.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 2
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 07_generate_annual_urban_landuse_layers.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import geopandas as gpd
import pandas as pd

# =============================================================================

EULUC_1 = r"D:\GISdata\EULUC\EULUC_China_20_1.shp"
EULUC_2 = r"D:\GISdata\EULUC\EULUC_China_20_2.shp"
PROVINCE_SHP = r"D:\GISdata\GS（2024）0650号\1\province.shp"

OUT_DIR = r"D:\GISdata\EULUC"
os.makedirs(OUT_DIR, exist_ok=True)

# =============================================================================

PROV_SLUG = {
    "北京市": "beijing",
    "天津市": "tianjin",
    "上海市": "shanghai",
    "重庆市": "chongqing",

    "河北省": "hebei",
    "山西省": "shanxi",
    "辽宁省": "liaoning",
    "吉林省": "jilin",
    "黑龙江省": "heilongjiang",
    "江苏省": "jiangsu",
    "浙江省": "zhejiang",
    "安徽省": "anhui",
    "福建省": "fujian",
    "江西省": "jiangxi",
    "山东省": "shandong",
    "河南省": "henan",
    "湖北省": "hubei",
    "湖南省": "hunan",
    "广东省": "guangdong",
    "海南省": "hainan",
    "四川省": "sichuan",
    "贵州省": "guizhou",
    "云南省": "yunnan",
    "陕西省": "shaanxi",
    "甘肃省": "gansu",
    "青海省": "qinghai",
    "台湾省": "taiwan",

    "内蒙古自治区": "neimenggu",
    "广西壮族自治区": "guangxi",
    "西藏自治区": "xizang",
    "宁夏回族自治区": "ningxia",
    "新疆维吾尔自治区": "xinjiang",

    "香港特别行政区": "hongkong",
    "澳门特别行政区": "macao",
}

# =============================================================================

def load_and_merge_euluc():
    if not os.path.exists(EULUC_1):
        raise FileNotFoundError(f"找不到 {EULUC_1}")
    if not os.path.exists(EULUC_2):
        raise FileNotFoundError(f"找不到 {EULUC_2}")

    print("[INFO] Notebook progress message.")
    e1 = gpd.read_file(EULUC_1)
    print("[INFO] Notebook progress message.")

    print("[INFO] Notebook progress message.")
    e2 = gpd.read_file(EULUC_2)
    print("[INFO] Notebook progress message.")

    if e1.crs is None or e2.crs is None:
        raise ValueError("EULUC 数据缺少 CRS，请先在 GIS 里设定为 GCS_WGS_1984 再跑。")

    if e1.crs != e2.crs:
        print("[INFO] Notebook progress message.")
        e2 = e2.to_crs(e1.crs)

    if "Class" not in e1.columns or "Class" not in e2.columns:
        raise ValueError("EULUC 数据缺少 Class 字段，请检查。")

    # Original notebook comment normalized for the public code archive.
    common_cols = list(set(e1.columns) | set(e2.columns))
    e1 = e1.reindex(columns=common_cols)
    e2 = e2.reindex(columns=common_cols)

    print("[INFO] Notebook progress message.")
    e_all = pd.concat([e1, e2], ignore_index=True)
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    # Original notebook comment normalized for the public code archive.
    print("[INFO] Notebook progress message.")
    e_all["__geom_wkb__"] = e_all.geometry.apply(lambda g: g.wkb if g is not None else None)
    # Original notebook comment normalized for the public code archive.
    e_all = e_all.drop_duplicates(subset=["Class", "__geom_wkb__"]).drop(columns="__geom_wkb__")
    e_all = gpd.GeoDataFrame(e_all, geometry="geometry", crs=e1.crs)
    print("[INFO] Notebook progress message.")

    return e_all

def load_provinces(target_crs):
    if not os.path.exists(PROVINCE_SHP):
        raise FileNotFoundError(f"找不到省界数据：{PROVINCE_SHP}")

    print("[INFO] Notebook progress message.")
    prov = gpd.read_file(PROVINCE_SHP)
    print("[INFO] Notebook progress message.")

    if "省" not in prov.columns:
        raise ValueError("省界数据缺少 '省' 字段。")

    if prov.crs is None:
        raise ValueError("省界数据 CRS 为空，请在 GIS 中设定为 GCS_WGS_1984 再跑。")

    if prov.crs != target_crs:
        print("[INFO] Notebook progress message.")
        prov = prov.to_crs(target_crs)

    return prov

def clip_by_province(euluc_all, prov_gdf):
    # Original notebook comment normalized for the public code archive.
    _ = euluc_all.sindex

    for idx, prow in prov_gdf.iterrows():
        prov_name = str(prow["省"]).strip()
        slug = PROV_SLUG.get(prov_name)

        if not slug:
            print("[INFO] Notebook progress message.")
            continue

        out_path = os.path.join(OUT_DIR, f"24{slug}.shp")
        if os.path.exists(out_path):
            print("[INFO] Notebook progress message.")
            continue

        geom = prow.geometry
        if geom is None or geom.is_empty:
            print("[INFO] Notebook progress message.")
            continue

        # Original notebook comment normalized for the public code archive.
        minx, miny, maxx, maxy = geom.bounds
        cand = euluc_all.cx[minx:maxx, miny:maxy]

        if cand.empty:
            print("[INFO] Notebook progress message.")
            continue

        # Original notebook comment normalized for the public code archive.
        prov_box = gpd.GeoDataFrame(
            {"_pid": [1]},
            geometry=[geom],
            crs=euluc_all.crs
        )

        # Original notebook comment normalized for the public code archive.
        clipped = gpd.overlay(
            cand,
            prov_box,
            how="intersection",
            keep_geom_type=False
        )

        if clipped.empty:
            print("[INFO] Notebook progress message.")
            continue

        # Original notebook comment normalized for the public code archive.
        drop_cols = [c for c in clipped.columns if c.startswith("index_") or c == "_pid"]
        if drop_cols:
            clipped = clipped.drop(columns=drop_cols)

        # Original notebook comment normalized for the public code archive.
        clipped = clipped[
            clipped.geometry.notnull()
            & ~clipped.geometry.is_empty
            & clipped.geometry.geom_type.isin(["Polygon", "MultiPolygon"])
        ]

        if clipped.empty:
            print("[INFO] Notebook progress message.")
            continue

        clipped.to_file(out_path, encoding="utf-8")
        print("[INFO] Notebook progress message.")

def main():
    euluc_all = load_and_merge_euluc()
    prov = load_provinces(euluc_all.crs)
    clip_by_province(euluc_all, prov)
    print("[INFO] Notebook progress message.")

if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 6
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 07_generate_annual_urban_landuse_layers.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import geopandas as gpd

# =============================================================================
EULUC_2018_SHP = r"D:\GISdata\EULUC\EULUC-China-1.0\euluc-latlonnw.shp"
PROVINCE_SHP   = r"D:\GISdata\GS（2024）0650号\1\province.shp"
OUT_DIR        = r"D:\GISdata\EULUC"

os.makedirs(OUT_DIR, exist_ok=True)

# =============================================================================
PROV_SLUG = {
    "北京市": "beijing",
    "天津市": "tianjin",
    "上海市": "shanghai",
    "重庆市": "chongqing",

    "河北省": "hebei",
    "山西省": "shanxi",
    "辽宁省": "liaoning",
    "吉林省": "jilin",
    "黑龙江省": "heilongjiang",
    "江苏省": "jiangsu",
    "浙江省": "zhejiang",
    "安徽省": "anhui",
    "福建省": "fujian",
    "江西省": "jiangxi",
    "山东省": "shandong",
    "河南省": "henan",
    "湖北省": "hubei",
    "湖南省": "hunan",
    "广东省": "guangdong",
    "海南省": "hainan",
    "四川省": "sichuan",
    "贵州省": "guizhou",
    "云南省": "yunnan",
    "陕西省": "shaanxi",
    "甘肃省": "gansu",
    "青海省": "qinghai",
    "台湾省": "taiwan",

    "内蒙古自治区": "neimenggu",
    "广西壮族自治区": "guangxi",
    "西藏自治区": "xizang",
    "宁夏回族自治区": "ningxia",
    "新疆维吾尔自治区": "xinjiang",

    "香港特别行政区": "hongkong",
    "澳门特别行政区": "macao",
}

# =============================================================================

def load_euluc_2018():
    if not os.path.exists(EULUC_2018_SHP):
        raise FileNotFoundError(f"找不到 EULUC 1.0 数据：{EULUC_2018_SHP}")
    print("[INFO] Notebook progress message.")
    g = gpd.read_file(EULUC_2018_SHP)
    print("[INFO] Notebook progress message.")

    if "Level2" not in g.columns:
        raise ValueError("EULUC 1.0 缺少 Level2 字段。")

    # Original notebook comment normalized for the public code archive.
    g = g[g["Level2"] == 502].copy()
    print("[INFO] Notebook progress message.")

    if g.crs is None:
        raise ValueError("EULUC 1.0 未定义 CRS，请在 GIS 中设为 GCS_WGS_1984 (EPSG:4326) 后再用。")

    return g

def load_provinces(target_crs):
    if not os.path.exists(PROVINCE_SHP):
        raise FileNotFoundError(f"找不到省界数据：{PROVINCE_SHP}")
    print("[INFO] Notebook progress message.")
    prov = gpd.read_file(PROVINCE_SHP)
    print("[INFO] Notebook progress message.")

    if "省" not in prov.columns:
        raise ValueError("省界数据缺少 '省' 字段。")

    if prov.crs is None:
        raise ValueError("省界未定义 CRS，请在 GIS 中设为 GCS_WGS_1984 (EPSG:4326) 后再用。")

    if prov.crs != target_crs:
        print("[INFO] Notebook progress message.")
        prov = prov.to_crs(target_crs)

    return prov

# =============================================================================

def clip_by_province_edu(euluc_edu, prov_gdf):
    # Original notebook comment normalized for the public code archive.
    _ = euluc_edu.sindex

    for idx, prow in prov_gdf.iterrows():
        prov_name = str(prow["省"]).strip()
        slug = PROV_SLUG.get(prov_name)

        if not slug:
            print("[INFO] Notebook progress message.")
            continue

        out_path = os.path.join(OUT_DIR, f"18{slug}.shp")
        if os.path.exists(out_path):
            print("[INFO] Notebook progress message.")
            continue

        geom = prow.geometry
        if geom is None or geom.is_empty:
            print("[INFO] Notebook progress message.")
            continue

        # Original notebook comment normalized for the public code archive.
        minx, miny, maxx, maxy = geom.bounds
        cand = euluc_edu.cx[minx:maxx, miny:maxy]

        if cand.empty:
            print("[INFO] Notebook progress message.")
            continue

        # Original notebook comment normalized for the public code archive.
        prov_box = gpd.GeoDataFrame({"_pid": [1]}, geometry=[geom], crs=euluc_edu.crs)

        clipped = gpd.overlay(
            cand,
            prov_box,
            how="intersection",
            keep_geom_type=False
        )

        if clipped.empty:
            print("[INFO] Notebook progress message.")
            continue

        # Original notebook comment normalized for the public code archive.
        drop_cols = [c for c in clipped.columns if c.startswith("index_") or c == "_pid"]
        if drop_cols:
            clipped = clipped.drop(columns=drop_cols)

        # Original notebook comment normalized for the public code archive.
        clipped = clipped[
            clipped.geometry.notnull()
            & ~clipped.geometry.is_empty
            & clipped.geometry.geom_type.isin(["Polygon", "MultiPolygon"])
        ]

        if clipped.empty:
            print("[INFO] Notebook progress message.")
            continue

        clipped.to_file(out_path, encoding="utf-8")
        print("[INFO] Notebook progress message.")

# =============================================================================

def main():
    euluc_edu = load_euluc_2018()
    prov = load_provinces(euluc_edu.crs)
    clip_by_province_edu(euluc_edu, prov)
    print("[INFO] Notebook progress message.")

if __name__ == "__main__":
    main()
