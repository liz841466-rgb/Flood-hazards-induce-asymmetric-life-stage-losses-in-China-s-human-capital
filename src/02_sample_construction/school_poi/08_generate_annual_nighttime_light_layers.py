#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 08_generate_annual_nighttime_light_layers.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 2
# ------------------------------------------------------------------------------
import os
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from tqdm import tqdm

# =============================================================================
NATL_NTL_DIR = r"D:\GISdata\Night_Light\1992-2024年经过矫正的夜间灯光数据\【立方数据学社】全国范围的数据"
PROV_SHP     = r"D:\GISdata\GS（2024）0650号\1\province.shp"
OUT_ROOT     = r"D:\GISdata\Night_Light"   # Original notebook comment normalized for the public code archive.

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

def list_natl_rasters():
    files = []
    for fname in os.listdir(NATL_NTL_DIR):
        if fname.lower().endswith(".tif"):
            files.append(os.path.join(NATL_NTL_DIR, fname))
    if not files:
        raise RuntimeError("全国夜光目录下未找到 .tif 文件")
    return sorted(files)

def load_provinces(target_crs):
    gdf = gpd.read_file(PROV_SHP)
    # Original notebook comment normalized for the public code archive.
    if "省" in gdf.columns:
        name_col = "省"
    elif "NAME" in gdf.columns:
        name_col = "NAME"
    else:
        raise KeyError("province.shp 中找不到省名字段，请手动修改脚本中的 name_col。")

    gdf = gdf[[name_col, "geometry"]].rename(columns={name_col: "prov_name"})

    # Original notebook comment normalized for the public code archive.
    gdf = gdf.to_crs(target_crs)

    # Original notebook comment normalized for the public code archive.
    slugs = []
    for n in gdf["prov_name"]:
        n = str(n).strip()
        if n not in PROV_SLUG:
            raise KeyError(f"省名 '{n}' 未在 PROV_SLUG 字典中定义，请补充映射。")
        slugs.append(PROV_SLUG[n])
    gdf["slug"] = slugs

    return gdf

def clip_and_save(natl_path, prov_geom, out_path):
    # Original notebook comment normalized for the public code archive.
    if os.path.exists(out_path):
        return

    with rasterio.open(natl_path) as src:
        out_image, out_transform = mask(
            src,
            [prov_geom],
            crop=True,
            nodata=src.nodata
        )
        # Original notebook comment normalized for the public code archive.
        if (out_image == src.nodata).all():
            return

        meta = src.meta.copy()
        meta.update({
            "height": out_image.shape[1],
            "width":  out_image.shape[2],
            "transform": out_transform
        })

        # Original notebook comment normalized for the public code archive.
        os.makedirs(os.path.dirname(out_path), exist_ok=True)

        with rasterio.open(out_path, "w", **meta) as dst:
            dst.write(out_image)

def main():
    natl_files = list_natl_rasters()
    # Original notebook comment normalized for the public code archive.
    with rasterio.open(natl_files[0]) as tmp:
        ntl_crs = tmp.crs

    prov_gdf = load_provinces(ntl_crs)

    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    for _, row in prov_gdf.iterrows():
        slug = row["slug"]
        geom = row.geometry

        print("[INFO] Notebook progress message.")
        out_dir = os.path.join(OUT_ROOT, slug)
        os.makedirs(out_dir, exist_ok=True)

        for natl_path in tqdm(natl_files, ncols=80, desc=f"{slug}", leave=False):
            fname = os.path.basename(natl_path)
            # Original notebook comment normalized for the public code archive.
            out_path = os.path.join(out_dir, fname)
            clip_and_save(natl_path, geom, out_path)

    print("[INFO] Notebook progress message.", OUT_ROOT)

if __name__ == "__main__":
    main()
