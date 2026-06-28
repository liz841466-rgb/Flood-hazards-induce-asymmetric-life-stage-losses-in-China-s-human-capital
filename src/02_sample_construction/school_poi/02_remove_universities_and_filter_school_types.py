#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 02_remove_universities_and_filter_school_types.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 3
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 02_remove_universities_and_filter_school_types.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
import os
from pathlib import Path
import geopandas as gpd

in_dir  = Path(r"D:\GISdata\CHINA_SCHOOL")
out_dir = Path(r"D:\GISdata\CHINA_SCHOOL\filter")
out_dir.mkdir(parents=True, exist_ok=True)

# Original notebook comment normalized for the public code archive.
bad_values_str = {"2090101"}  # Original notebook comment normalized for the public code archive.

def normalize_type_series(s):
    """Archived notebook note for 02_remove_universities_and_filter_school_types.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    # Original notebook comment normalized for the public code archive.
    s = s.astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    s = s.str.replace(r"[^0-9]", "", regex=True)
    return s

shps = sorted(in_dir.glob("*.shp"))
if not shps:
    print("[INFO] Notebook progress message.")
else:
    print("[INFO] Notebook progress message.")

for shp in shps:
    try:
        gdf = gpd.read_file(shp)
        total = len(gdf)

        if "type" not in gdf.columns:
            # Original notebook comment normalized for the public code archive.
            dst = out_dir / shp.name
            gdf.to_file(dst, driver="ESRI Shapefile")  # Original notebook comment normalized for the public code archive.
            print("[INFO] Notebook progress message.")
            continue

        t_norm = normalize_type_series(gdf["type"])
        mask_keep = ~t_norm.isin(bad_values_str)
        kept = int(mask_keep.sum())
        removed = total - kept

        gdf_filtered = gdf.loc[mask_keep].copy()

        dst = out_dir / shp.name
        gdf_filtered.to_file(dst, driver="ESRI Shapefile")  # Original notebook comment normalized for the public code archive.
        print("[INFO] Notebook progress message.")

    except Exception as e:
        print("[INFO] Notebook progress message.")

print("[INFO] Notebook progress message.")


# ------------------------------------------------------------------------------
# Notebook cell 8
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
import re
from pathlib import Path
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import font_manager

# =============================================================================
def setup_zh_font():
    preferred = [
        "Microsoft YaHei", "Microsoft YaHei UI", "SimHei",
        "Microsoft JhengHei", "PingFang SC", "Heiti SC", "STHeiti",
        "Noto Sans CJK SC", "Source Han Sans SC"
    ]
    have = {f.name for f in font_manager.fontManager.ttflist}
    for name in preferred:
        if name in have:
            mpl.rcParams["font.sans-serif"] = [name]
            mpl.rcParams["axes.unicode_minus"] = False
            print("[INFO] Notebook progress message.")
            return
    print("[INFO] Notebook progress message.")
setup_zh_font()

# =============================================================================
in_dir = Path(r"D:\GISdata\CHINA_SCHOOL\filter")

# =============================================================================
pinyin2cn = {
    "anhui":"安徽","aomen":"澳门","beijing":"北京","chongqing":"重庆","fujian":"福建",
    "gansu":"甘肃","guangxi":"广西","guizhou":"贵州","hainan":"海南","hebei":"河北",
    "heilongjiang":"黑龙江","henan":"河南","hubei":"湖北","hunan":"湖南","jiangsu":"江苏",
    "jiangxi":"江西","jilin":"吉林","liaoning":"辽宁","neimenggu":"内蒙古","ningxia":"宁夏",
    "qinghai":"青海","shanxi":"山西","shaanxi":"陕西","sichuan":"四川","tianjin":"天津",
    "yunnan":"云南","zhejiang":"浙江","shanghai":"上海","guangdong":"广东","guandong":"广东",
    "shandong":"山东","shangdong":"山东","xinjiang":"新疆","xizang":"西藏","xianggang":"香港"
}

TYPE_MAP = {"2090102":"中学", "2090103":"小学", "2090104":"幼儿园"}

def normalize_type_series(s):
    s = s.astype(str).str.strip()
    s = s.str.replace(r"\.0$", "", regex=True)
    s = s.str.replace(r"[^0-9]", "", regex=True)
    return s

def base_to_cn(base):
    return pinyin2cn.get(base.lower(), base)

# =============================================================================
shps = sorted(in_dir.glob("*.shp"))
if not shps:
    raise SystemExit(f"未在 {in_dir} 找到 .shp。")

records = []
for shp in shps:
    try:
        prov_cn = base_to_cn(shp.stem)
        gdf = gpd.read_file(shp)

        if "type" not in gdf.columns:
            c2 = c3 = c4 = 0
        else:
            t = normalize_type_series(gdf["type"])
            vc = t.value_counts()
            c2 = int(vc.get("2090102", 0))   # Original notebook comment normalized for the public code archive.
            c3 = int(vc.get("2090103", 0))   # Original notebook comment normalized for the public code archive.
            c4 = int(vc.get("2090104", 0))   # Original notebook comment normalized for the public code archive.

        total = c2 + c3 + c4
        records.append({"省份":prov_cn, "中学(2090102)":c2, "小学(2090103)":c3, "幼儿园(2090104)":c4, "总计":total})
        print("[INFO] Notebook progress message.")
    except Exception as e:
        print("[INFO] Notebook progress message.")

df = pd.DataFrame(records).sort_values("总计", ascending=False, ignore_index=True)

print("[INFO] Notebook progress message.")
print(df.to_string(index=False))

nation = df[["中学(2090102)", "小学(2090103)", "幼儿园(2090104)"]].sum()
print("[INFO] Notebook progress message.")
print("[INFO] Notebook progress message.")
print("[INFO] Notebook progress message.")
print("[INFO] Notebook progress message.")

# =============================================================================
# Original notebook comment normalized for the public code archive.
plt.figure(figsize=(max(12, len(df)*0.6), 6))
x = range(len(df))
w = 0.28
plt.bar([i - w for i in x], df["幼儿园(2090104)"], w, label="幼儿园")
plt.bar(x,                         df["小学(2090103)"], w, label="小学")
plt.bar([i + w for i in x],       df["中学(2090102)"], w, label="中学")
plt.xticks(list(x), df["省份"], rotation=60, ha="right")
plt.ylabel("数量")
plt.title("各省（自治区/直辖市/港澳）幼儿园 / 小学 / 中学 数量（仅显示）")
plt.legend()
plt.tight_layout()
plt.show()

# Original notebook comment normalized for the public code archive.
plt.figure(figsize=(6, 4))
plt.bar(["幼儿园","小学","中学"],
        [nation["幼儿园(2090104)"], nation["小学(2090103)"], nation["中学(2090102)"]])
plt.ylabel("数量")
plt.title("全国幼儿园 / 小学 / 中学 总计（仅显示）")
plt.tight_layout()
plt.show()


# ------------------------------------------------------------------------------
# Notebook cell 9
# ------------------------------------------------------------------------------
# =============================================================================
# Original notebook comment normalized for the public code archive.
plt.figure(figsize=(max(12, len(df)*0.6), 6))
x = range(len(df))
w = 0.28
plt.bar([i - w for i in x], df["幼儿园(2090104)"], w, label="幼儿园")
plt.bar(x,                         df["小学(2090103)"], w, label="小学")
plt.bar([i + w for i in x],       df["中学(2090102)"], w, label="中学")
plt.xticks(list(x), df["省份"], rotation=60, ha="right")
plt.ylabel("数量")
plt.title("各省（自治区/直辖市/港澳）幼儿园 / 小学 / 中学 数量")
plt.legend()
plt.tight_layout()
plt.show()

# Original notebook comment normalized for the public code archive.
plt.figure(figsize=(6, 4))
plt.bar(["幼儿园","小学","中学"],
        [nation["幼儿园(2090104)"], nation["小学(2090103)"], nation["中学(2090102)"]])
plt.ylabel("数量")
plt.title("全国幼儿园 / 小学 / 中学 总计")
plt.tight_layout()
plt.show()


# ------------------------------------------------------------------------------
# Notebook cell 12
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 02_remove_universities_and_filter_school_types.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
from pathlib import Path
import geopandas as gpd

in_dir  = Path(r"D:\GISdata\CHINA_SCHOOL\filter")
out_dir = Path(r"D:\GISdata\CHINA_SCHOOL\filter_WGS84")
out_dir.mkdir(parents=True, exist_ok=True)

def assume_web_mercator(crs_obj):
    """Archived notebook note for 02_remove_universities_and_filter_school_types.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if crs_obj is None:
        return True
    s = str(crs_obj).lower()
    # Original notebook comment normalized for the public code archive.
    return ("web_mercator" in s) or ("mercator_auxiliary_sphere" in s) or ("3857" in s)

shps = sorted(in_dir.glob("*.shp"))
if not shps:
    raise SystemExit(f"未在 {in_dir} 找到 .shp 文件。")

for shp in shps:
    try:
        gdf = gpd.read_file(shp)
        # Original notebook comment normalized for the public code archive.
        if assume_web_mercator(gdf.crs):
            gdf = gdf.set_crs(epsg=3857, allow_override=True)
            src = "EPSG:3857 (Web Mercator)"
        else:
            src = str(gdf.crs)

        # Original notebook comment normalized for the public code archive.
        gdf4326 = gdf.to_crs(epsg=4326)

        # Original notebook comment normalized for the public code archive.
        dst = out_dir / shp.name
        gdf4326.to_file(dst, driver="ESRI Shapefile")

        # Original notebook comment normalized for the public code archive.
        minx, miny, maxx, maxy = gdf4326.total_bounds
        print("[INFO] Notebook progress message.")
    except Exception as e:
        print("[INFO] Notebook progress message.")

print("[INFO] Notebook progress message.")
