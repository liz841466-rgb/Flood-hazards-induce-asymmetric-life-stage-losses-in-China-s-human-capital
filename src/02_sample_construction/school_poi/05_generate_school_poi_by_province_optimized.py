#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 05_generate_school_poi_by_province_optimized.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 5
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 05_generate_school_poi_by_province_optimized.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import geopandas as gpd
import pandas as pd

# Original notebook comment normalized for the public code archive.
SCHOOL_ALL_SHP = r"D:\GISdata\2024school\小学_中学.shp"
OUT_DIR        = r"D:\GISdata\CHINA_SCHOOL"
os.makedirs(OUT_DIR, exist_ok=True)

# Original notebook comment normalized for the public code archive.
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
VALID_PROV_NAMES = set(PROV_SLUG.keys())

# Original notebook comment normalized for the public code archive.
try:
    from pyogrio import write_dataframe as _write_df
    HAS_PYOGRIO = True
except ImportError:
    HAS_PYOGRIO = False

def write_shp(df, out_path):
    drop_cols = [c for c in df.columns if c.startswith("index_")]
    if drop_cols:
        df = df.drop(columns=drop_cols)

    if HAS_PYOGRIO:
        _write_df(
            df,
            out_path,
            driver="ESRI Shapefile",
            encoding="GBK",
            layer_options={"ENCODING": "GBK"},
        )
    else:
        df.to_file(
            out_path,
            driver="ESRI Shapefile",
            encoding="GBK",
        )

# Original notebook comment normalized for the public code archive.
def looks_reasonable(g):
    cols_text = "".join([str(c) for c in g.columns])
    # Original notebook comment normalized for the public code archive.
    sample_vals = []
    for c in g.columns:
        if g[c].dtype == object:
            sample_vals.extend(g[c].dropna().astype(str).head(200).tolist())
            if len(sample_vals) > 1000:
                break
    vals_text = "".join(sample_vals)

    text = cols_text + vals_text
    # Original notebook comment normalized for the public code archive.
    keywords = ["小学", "中学", "学校", "省", "市", "区"]
    return any(k in text for k in keywords)

def read_school():
    if not os.path.exists(SCHOOL_ALL_SHP):
        raise FileNotFoundError(f"找不到 {SCHOOL_ALL_SHP}")

    # Original notebook comment normalized for the public code archive.
    encodings = ["gbk", "cp936", "gb18030", None]  # Original notebook comment normalized for the public code archive.
    last_err = None
    for enc in encodings:
        try:
            if enc is None:
                g = gpd.read_file(SCHOOL_ALL_SHP)
                used = "默认"
            else:
                g = gpd.read_file(SCHOOL_ALL_SHP, encoding=enc)
                used = enc
        except Exception as e:
            last_err = e
            continue

        if looks_reasonable(g):
            print("[INFO] Notebook progress message.")
            print("[INFO] Notebook progress message.", list(g.columns))
            return g
        else:
            print("[INFO] Notebook progress message.")

    raise RuntimeError(
        # Notebook-export prose note omitted from the public code archive.
        f"请在 ArcGIS/QGIS 中把原始数据另存为 UTF-8 或 GBK 后再跑本脚本。最后错误: {last_err}"
    )

def detect_province_col(gdf):
    cols = list(gdf.columns)

    # Original notebook comment normalized for the public code archive.
    for name in ["省份", "省", "省名", "PROV", "prov", "Province"]:
        if name in cols:
            print("[INFO] Notebook progress message.")
            return name

    # Original notebook comment normalized for the public code archive.
    for c in cols:
        s = gdf[c]
        if s.dtype != object:
            continue
        vals = s.dropna().astype(str).str.strip()
        if vals.empty:
            continue
        uniq = vals.unique()
        if len(uniq) < 5 or len(uniq) > 100:
            continue

        match = 0
        for v in uniq:
            if v in VALID_PROV_NAMES:
                match += 1
                continue
            # Original notebook comment normalized for the public code archive.
            v2 = v.replace("省", "").replace("市", "").replace("自治区", "") \
                  .replace("回族自治区", "").replace("壮族自治区", "") \
                  .replace("维吾尔自治区", "").replace("特别行政区", "")
            for full in VALID_PROV_NAMES:
                fb = full.replace("省", "").replace("市", "").replace("自治区", "") \
                         .replace("回族自治区", "").replace("壮族自治区", "") \
                         .replace("维吾尔自治区", "").replace("特别行政区", "")
                if v2 == fb:
                    match += 1
                    break

        if match / len(uniq) >= 0.7:
            print("[INFO] Notebook progress message.")
            return c

    raise ValueError(
        "自动识别省份列失败：源数据字段名或编码本身就有问题。"
        "在 Python 里打印 gdf.head()，看清真实字段，再手动指定。"
    )

def main():
    gdf = read_school()

    if gdf.crs is None:
        raise ValueError("源数据缺少坐标系，请在 GIS 中设为 GCS_WGS_1984 (EPSG:4326)")

    prov_col = detect_province_col(gdf)

    # Original notebook comment normalized for the public code archive.
    gdf[prov_col] = gdf[prov_col].astype(str).str.strip()

    print("[INFO] Notebook progress message.")
    for prov_name, sub in gdf.groupby(prov_col):
        if pd.isna(prov_name):
            continue
        pname = str(prov_name).strip()
        if not pname:
            continue

        # Original notebook comment normalized for the public code archive.
        slug = PROV_SLUG.get(pname)

        # Original notebook comment normalized for the public code archive.
        if not slug:
            base = pname.replace("省", "").replace("市", "") \
                        .replace("自治区", "").replace("回族自治区", "") \
                        .replace("壮族自治区", "").replace("维吾尔自治区", "") \
                        .replace("特别行政区", "")
            for full, s in PROV_SLUG.items():
                fb = full.replace("省", "").replace("市", "") \
                         .replace("自治区", "").replace("回族自治区", "") \
                         .replace("壮族自治区", "").replace("维吾尔自治区", "") \
                         .replace("特别行政区", "")
                if base == fb:
                    slug = s
                    break

        if not slug:
            print("[INFO] Notebook progress message.")
            continue

        out_path = os.path.join(OUT_DIR, f"{slug}_小学_中学.shp")
        write_shp(sub, out_path)
        print("[INFO] Notebook progress message.")

    print("[INFO] Notebook progress message.")

if __name__ == "__main__":
    main()
