#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 07_build_unbalanced_household_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 2
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 07_build_unbalanced_household_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import re
import numpy as np
import pandas as pd

# =============================================================================
ROOT = r"E:\project_flood_impact_assessment\教育数据\CHFS_center"
WAVES = [2011, 2013, 2015, 2017, 2019]

FILES = {
    2011: os.path.join(ROOT, "2011", "CHFS2011_教育与收入_户级.xlsx"),
    2013: os.path.join(ROOT, "2013", "CHFS2013_教育与收入_户级.xlsx"),
    2015: os.path.join(ROOT, "2015", "CHFS2015_教育与收入_户级.xlsx"),
    2017: os.path.join(ROOT, "2017", "CHFS2017_教育与收入_户级.xlsx"),
    # Original notebook comment normalized for the public code archive.
    # CHFS/CFHS processing note.
    2019: os.path.join(ROOT, "2019", "CHFS2019_教育与收入_户级.xlsx"),
}

# Original notebook comment normalized for the public code archive.
INCOME_YEAR_MAP = {
    2011: 2010,
    2013: 2012,
    2015: 2014,
    2017: 2016,
    2019: 2018,
}

OUTDIR = os.path.join(ROOT, "output")
os.makedirs(OUTDIR, exist_ok=True)

# =============================================================================
def normalize_id_val(x):
    """Archived notebook note for 07_build_unbalanced_household_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if pd.isna(x):
        return pd.NA
    s = str(x).strip()
    if s.lower() in {"nan", "nat", ""}:
        return pd.NA
    # Original notebook comment normalized for the public code archive.
    s = re.sub(r"\.0+$", "", s)
    s = s.replace(" ", "")
    return s if s else pd.NA

def to_int_series(s):
    return pd.to_numeric(s, errors="coerce").astype("Int64")

def to_float_series(s):
    return pd.to_numeric(s, errors="coerce")

def compute_edu_debt_indicator(df, year):
    """Archived notebook note for 07_build_unbalanced_household_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    idx = df.index
    out = pd.Series(pd.NA, index=idx, dtype="Int64")

    def combine_by_cols(col_list):
        if not col_list:
            return out
        sub = df[col_list].apply(pd.to_numeric, errors="coerce")
        any1 = (sub == 1).any(axis=1)
        any_nonmiss = sub.notna().any(axis=1)
        all2 = (sub == 2).all(axis=1) & any_nonmiss

        res = pd.Series(pd.NA, index=idx, dtype="Int64")
        res.loc[any1] = 1
        res.loc[~any1 & all2] = 2
        return res

    if year in (2011, 2013, 2015):
        cols = []
        c1 = "是否有教育银行贷款（原始码1/2）"
        c2 = "是否为子女教育向他人/机构借款（原始码1/2）"
        if c1 in df.columns: cols.append(c1)
        if c2 in df.columns: cols.append(c2)
        if cols:
            out = combine_by_cols(cols)

    elif year == 2017:
        cols = []
        c1 = "是否有教育银行贷款（原始码1/2）"
        c2 = "是否有教育民间借款（原始码1/2）"
        if c1 in df.columns: cols.append(c1)
        if c2 in df.columns: cols.append(c2)
        if cols:
            out = combine_by_cols(cols)

    elif year == 2019:
        c = "是否有教育负债（原始码1/2）"
        if c in df.columns:
            out = to_int_series(df[c])

    return out

def compute_edu_debt_balance(df, year):
    """Archived notebook note for 07_build_unbalanced_household_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    idx = df.index
    out = pd.Series(np.nan, index=idx)

    if year in (2011, 2013, 2015):
        cols = []
        c1 = "教育贷款总额（元）"
        c2 = "子女教育借款总额（元）"
        if c1 in df.columns: cols.append(c1)
        if c2 in df.columns: cols.append(c2)
        if cols:
            sub = df[cols].apply(to_float_series)
            # Original notebook comment normalized for the public code archive.
            out = sub.sum(axis=1, min_count=1)

    elif year == 2017:
        c = "教育民间借款尚欠金额（元）"
        if c in df.columns:
            out = to_float_series(df[c])

    elif year == 2019:
        c = "教育负债余额（元）"
        if c in df.columns:
            out = to_float_series(df[c])

    return out

def read_wave_to_panel(year, path):
    """Archived notebook note for 07_build_unbalanced_household_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print("[INFO] Notebook progress message.")
    df = pd.read_excel(path)

    if "家庭ID" not in df.columns:
        raise KeyError(f"{year} 波 Excel 缺少列：家庭ID")

    # =============================================================================
    famid = df["家庭ID"].map(normalize_id_val)

    # =============================================================================
    prov = df["省"] if "省" in df.columns else pd.Series(pd.NA, index=df.index)
    city = df["市"] if "市" in df.columns else pd.Series(pd.NA, index=df.index)
    county = df["县"] if "县" in df.columns else pd.Series(pd.NA, index=df.index)

    # =============================================================================
    if "是否农村" in df.columns:
        rural_t = to_int_series(df["是否农村"])
    else:
        rural_t = pd.Series(pd.NA, index=df.index, dtype="Int64")

    # =============================================================================
    if "抽样权重" in df.columns:
        weight = to_float_series(df["抽样权重"])
    else:
        weight = pd.Series(np.nan, index=df.index)

    # =============================================================================
    inc_cols = [c for c in df.columns if "家庭可支配收入" in str(c)]
    if inc_cols:
        inc_col = inc_cols[0]
        income = to_float_series(df[inc_col])
    else:
        inc_col = None
        income = pd.Series(np.nan, index=df.index)

    income_year = INCOME_YEAR_MAP.get(year, year - 1)

    # =============================================================================
    # Original notebook comment normalized for the public code archive.
    edu_cols = [
        c for c in df.columns
        if ("去年" in str(c) and "教育" in str(c)
            and "培训" in str(c) and "支出" in str(c)
            and "子女" not in str(c))
    ]
    if edu_cols:
        edu_col = edu_cols[0]
        edu_training = to_float_series(df[edu_col])
    else:
        edu_col = None
        edu_training = pd.Series(np.nan, index=df.index)

    # =============================================================================
    child_train_cols = [
        c for c in df.columns
        if ("去年" in str(c) and "子女" in str(c)
            and "教育" in str(c) and "培训" in str(c) and "支出" in str(c))
    ]
    if child_train_cols:
        child_train_col = child_train_cols[0]
        edu_child_training = to_float_series(df[child_train_col])
    else:
        edu_child_training = pd.Series(np.nan, index=df.index)

    edu_year = INCOME_YEAR_MAP.get(year, year - 1)

    # =============================================================================
    # Original notebook comment normalized for the public code archive.
    all_stu_cols = [c for c in df.columns if "在校成员教育支出总额" in str(c)]
    if all_stu_cols:
        stu_all = to_float_series(df[all_stu_cols[0]])
    else:
        stu_all = pd.Series(np.nan, index=df.index)

    # Original notebook comment normalized for the public code archive.
    u15_stu_cols = [c for c in df.columns if "15岁及以下子女教育支出总额" in str(c)]
    if u15_stu_cols:
        stu_u15 = to_float_series(df[u15_stu_cols[0]])
    else:
        stu_u15 = pd.Series(np.nan, index=df.index)

    # =============================================================================
    child_any_col = "是否有15岁及以下儿童"
    child_num_col = "15岁及以下儿童数量"

    if child_any_col in df.columns:
        has_child = to_int_series(df[child_any_col])
    else:
        has_child = pd.Series(pd.NA, index=df.index, dtype="Int64")

    if child_num_col in df.columns:
        n_child = to_int_series(df[child_num_col])
    else:
        n_child = pd.Series(pd.NA, index=df.index, dtype="Int64")

    # =============================================================================
    has_edu_debt = compute_edu_debt_indicator(df, year)
    edu_debt_bal = compute_edu_debt_balance(df, year)

    # =============================================================================
    panel_y = pd.DataFrame({
        "家庭ID": famid,
        "来源年份": year,
        "省": prov,
        "市": city,
        "县": county,
        "是否农村_当年": rural_t,
        "家庭可支配收入（元）": income,
        "收入口径年份": income_year,
        "是否有教育负债（原始码1/2）": has_edu_debt,
        "教育负债余额（元）": edu_debt_bal,
        "去年教育培训支出（元）": edu_training,
        "去年子女教育培训支出（元）": edu_child_training,
        "教育培训支出口径年份": edu_year,
        "在校成员教育支出总额（元）": stu_all,
        "15岁及以下子女教育支出总额（元）": stu_u15,
        "是否有15岁及以下儿童": has_child,
        "15岁及以下儿童数量": n_child,
    })

    # Original notebook comment normalized for the public code archive.
    panel_y = panel_y.dropna(subset=["家庭ID"]).reset_index(drop=True)

    # =============================================================================
    weights_y = pd.DataFrame({
        "家庭ID": panel_y["家庭ID"],
        "来源年份": year,
        "抽样权重": weight.loc[panel_y.index].values,
    })

    return panel_y, weights_y


def derive_rural_panel(panel_df):
    """Archived notebook note for 07_build_unbalanced_household_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    def decide(s):
        s = s.dropna()
        if s.empty:
            return pd.NA
        n_rural = (s == 1).sum()
        n_urban = (s == 0).sum()
        if n_rural > n_urban:
            return 1
        elif n_urban > n_rural:
            return 0
        else:
            return pd.NA

    rural_panel = (panel_df
                   .groupby("家庭ID")["是否农村_当年"]
                   .apply(decide)
                   .astype("Int64"))
    return rural_panel


# =============================================================================
panel_list = []
weight_list = []

for y in WAVES:
    p_y, w_y = read_wave_to_panel(y, FILES[y])
    panel_list.append(p_y)
    weight_list.append(w_y)

# Original notebook comment normalized for the public code archive.
panel = pd.concat(panel_list, axis=0, ignore_index=True)

# Original notebook comment normalized for the public code archive.
panel = panel.sort_values(["家庭ID", "来源年份"]).reset_index(drop=True)

# Original notebook comment normalized for the public code archive.
dup_cnt = panel.duplicated(subset=["家庭ID", "来源年份"]).sum()
print("[INFO] Notebook progress message.")

# =============================================================================
rural_panel = derive_rural_panel(panel)
rural_panel_df = rural_panel.reset_index().rename(columns={"是否农村_当年": "是否农村"})

panel = panel.merge(rural_panel_df, on="家庭ID", how="left")

# Original notebook comment normalized for the public code archive.
col_order = [
    "家庭ID", "来源年份",
    "省", "市", "县",
    "是否农村",          # Original notebook comment normalized for the public code archive.
    "是否农村_当年",     # Original notebook comment normalized for the public code archive.
    "家庭可支配收入（元）", "收入口径年份",
    "是否有教育负债（原始码1/2）", "教育负债余额（元）",
    "去年教育培训支出（元）",
    "去年子女教育培训支出（元）",
    "教育培训支出口径年份",
    "在校成员教育支出总额（元）",
    "15岁及以下子女教育支出总额（元）",
    "是否有15岁及以下儿童", "15岁及以下儿童数量",
]
# Original notebook comment normalized for the public code archive.
col_order = [c for c in col_order if c in panel.columns]
panel = panel[col_order].copy()

# =============================================================================
out_panel = os.path.join(OUTDIR, "CHFS_家庭不平衡面板_2011_2019.xlsx")
panel.to_excel(out_panel, index=False)
print("[INFO] Notebook progress message.")

# =============================================================================
weights_all = pd.concat(weight_list, axis=0, ignore_index=True)
weights_all = weights_all.dropna(subset=["家庭ID"]).copy()
weights_all = weights_all.sort_values(["家庭ID", "来源年份"]).reset_index(drop=True)

out_w = os.path.join(OUTDIR, "CHFS_家庭不平衡面板_抽样权重.xlsx")
weights_all.to_excel(out_w, index=False)
print("[INFO] Notebook progress message.")


# ------------------------------------------------------------------------------
# Notebook cell 4
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 07_build_unbalanced_household_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import pandas as pd
import geopandas as gpd
from pathlib import Path

# =============================================================================
ROOT = Path(r"E:\project_flood_impact_assessment\教育数据\CHFS_center")
PANEL_IN   = ROOT / "output" / "CHFS_家庭不平衡面板_2011_2019.xlsx"
SHAPEFILE  = Path(r"D:\GISdata\GS（2024）0650号\1\country.shp")

# Original notebook comment normalized for the public code archive.
MAPPING_XLSX = ROOT / "output" / "CHFS_县名人工对照表.xlsx"

# Original notebook comment normalized for the public code archive.
OUT_FIRST  = ROOT / "output" / "CHFS_家庭不平衡面板_2011_2019_带县代码_第一轮.xlsx"
OUT_FINAL  = ROOT / "output" / "CHFS_家庭不平衡面板_2011_2019_带县代码_二次回填.xlsx"


def norm_str(s):
    """Archived notebook note for 07_build_unbalanced_household_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if pd.isna(s):
        return None
    s2 = str(s).strip()
    return s2 if s2 and s2.lower() not in {"nan", "nat"} else None


# =============================================================================
print("[INFO] Notebook progress message.")
df = pd.read_excel(PANEL_IN)

for col in ["省", "市", "县"]:
    if col in df.columns:
        df[col] = df[col].map(norm_str)

print("[INFO] Notebook progress message.")
gdf = gpd.read_file(SHAPEFILE)

# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
geo = gdf[["省", "市", "县", "县代码"]].copy()

for col in ["省", "市", "县"]:
    if col in geo.columns:
        geo[col] = geo[col].map(norm_str)

# Original notebook comment normalized for the public code archive.
geo["县代码"] = pd.to_numeric(geo["县代码"], errors="coerce").astype("Int64")

# Shapefile output note.
geo = geo.drop_duplicates(subset=["省", "市", "县"], keep="first")

# =============================================================================
df1 = df.merge(
    geo,
    on=["省", "市", "县"],
    how="left",
    suffixes=("", "_geo")
)

df1 = df1.rename(columns={"县代码": "county_code"})

n_total   = len(df1)
n_missing = df1["county_code"].isna().sum()
print("[INFO] Notebook progress message.")

# Original notebook comment normalized for the public code archive.
df1.to_excel(OUT_FIRST, index=False)
print("[INFO] Notebook progress message.")

# Original notebook comment normalized for the public code archive.
unmatched = (
    df1.loc[df1["county_code"].isna(), ["省", "市", "县"]]
       .drop_duplicates()
       .sort_values(["省", "市", "县"])
)

print("[INFO] Notebook progress message.")

# =============================================================================
if not MAPPING_XLSX.exists():
    mapping_tpl = unmatched.rename(columns={"省": "旧省", "市": "旧市", "县": "旧县"})
    # Shapefile output note.
    mapping_tpl["新省"] = ""
    mapping_tpl["新市"] = ""
    mapping_tpl["新县"] = ""

    mapping_tpl.to_excel(MAPPING_XLSX, index=False)
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    raise SystemExit()

# =============================================================================
print("[INFO] Notebook progress message.")
mapping = pd.read_excel(MAPPING_XLSX)

# Original notebook comment normalized for the public code archive.
for col in ["旧省", "旧市", "旧县", "新省", "新市", "新县"]:
    if col in mapping.columns:
        mapping[col] = mapping[col].map(norm_str)

# Original notebook comment normalized for the public code archive.
mapping = mapping.dropna(subset=["旧省", "旧市", "旧县", "新县"])

# Original notebook comment normalized for the public code archive.
df2 = df1.merge(
    mapping[["旧省", "旧市", "旧县", "新省", "新市", "新县"]],
    left_on=["省", "市", "县"],
    right_on=["旧省", "旧市", "旧县"],
    how="left"
)

# Shapefile output note.
df2["省_final"] = df2["新省"].combine_first(df2["省"])
df2["市_final"] = df2["新市"].combine_first(df2["市"])
df2["县_final"] = df2["新县"].combine_first(df2["县"])

# Shapefile output note.
df2 = df2.drop(columns=["county_code"])  # Original notebook comment normalized for the public code archive.
geo_final = geo.rename(columns={"省": "省_final", "市": "市_final", "县": "县_final"})

df2 = df2.merge(
    geo_final,
    on=["省_final", "市_final", "县_final"],
    how="left"
)

df2 = df2.rename(columns={"县代码": "county_code"})

n_missing2 = df2["county_code"].isna().sum()
print("[INFO] Notebook progress message.")

# Original notebook comment normalized for the public code archive.
df2["省"] = df2["省_final"]
df2["市"] = df2["市_final"]
df2["县"] = df2["县_final"]

# Original notebook comment normalized for the public code archive.
drop_cols = [c for c in ["旧省", "旧市", "旧县", "新省", "新市", "新县",
                         "省_final","市_final","县_final"] if c in df2.columns]
df2 = df2.drop(columns=drop_cols)

# =============================================================================
df2.to_excel(OUT_FINAL, index=False)
print("[INFO] Notebook progress message.")


# ------------------------------------------------------------------------------
# Notebook cell 6
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 07_build_unbalanced_household_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import pandas as pd
import geopandas as gpd
import numpy as np
from pathlib import Path

# =============================================================================
ROOT = Path(r"E:\project_flood_impact_assessment\教育数据\CHFS_center")

PANEL_XLSX = ROOT / "output" / "CHFS_家庭不平衡面板_2011_2019.xlsx"
SHAPEFILE  = Path(r"D:\GISdata\GS（2024）0650号\1\country.shp")

OUT_FIRST  = ROOT / "output" / "CHFS_家庭不平衡面板_2011_2019_带县代码_第一轮.xlsx"
OUT_FINAL  = ROOT / "output" / "CHFS_家庭不平衡面板_2011_2019_带县代码_最终版.xlsx"

CROSSWALK_XLSX = ROOT / "output" / "CHFS_县名人工对照表.xlsx"
UNMATCHED_XLSX = ROOT / "output" / "CHFS_县名人工对照表_仍未匹配.xlsx"

# =============================================================================
def clean_str_col(s: pd.Series) -> pd.Series:
    """Archived notebook note for 07_build_unbalanced_household_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    return (
        s.astype(str)
         .str.strip()
         .replace({"nan": None, "NaN": None, "": None})
    )

def load_panel():
    print("[INFO] Notebook progress message.")
    df = pd.read_excel(PANEL_XLSX)

    for col in ["省", "市", "县"]:
        if col in df.columns:
            df[col] = clean_str_col(df[col])
        else:
            raise KeyError(f"面板缺少列: {col}")
    return df

def load_geo():
    print("[INFO] Notebook progress message.")
    gdf = gpd.read_file(SHAPEFILE)

    # Original notebook comment normalized for the public code archive.
    need_cols = ["省", "市", "县", "县代码"]
    for c in need_cols:
        if c not in gdf.columns:
            raise KeyError(f"行政区划 shapefile 缺少字段: {c}")

    geo = gdf[need_cols].copy()
    for col in ["省", "市", "县"]:
        geo[col] = clean_str_col(geo[col])

    # Original notebook comment normalized for the public code archive.
    geo = geo.drop_duplicates(subset=["省", "市", "县"], keep="first")
    return geo

# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
MANUAL_NAME_MAP = {
    # Original notebook comment normalized for the public code archive.
    ("四川省",   "宜宾市",   "宜宾县"):   ("四川省",   "宜宾市",   "叙州区"),
    ("广东省",   "广州市",   "增城市"):   ("广东省",   "广州市",   "增城区"),
    ("湖北省",   "荆州市",   "监利县"):   ("湖北省",   "荆州市",   "监利市"),
    ("广西壮族自治区", "南宁市", "新城区"): ("广西壮族自治区", "南宁市", "青秀区"),
    ("甘肃省",   "天水市",   "北道区"):   ("甘肃省",   "天水市",   "麦积区"),
    ("安徽省",   "合肥市",   "西市区"):   ("安徽省",   "合肥市",   "庐阳区"),
    ("湖南省",   "永州市",   "芝山区"):   ("湖南省",   "永州市",   "零陵区"),
    ("云南省",   "曲靖市",   "沾益县"):   ("云南省",   "曲靖市",   "沾益区"),
    ("辽宁省",   "沈阳市",   "辽中县"):   ("辽宁省",   "沈阳市",   "辽中区"),
    ("山东省",   "青岛市",   "即墨市"):   ("山东省",   "青岛市",   "即墨区"),
    ("吉林省",   "长春市",   "九台市"):   ("吉林省",   "长春市",   "九台区"),
    ("河北省",   "保定市",   "清苑县"):   ("河北省",   "保定市",   "清苑区"),
    ("重庆市",   "重庆市",   "潼南县"):   ("重庆市",   "重庆市",   "潼南区"),
    ("重庆市",   "重庆市",   "铜梁县"):   ("重庆市",   "重庆市",   "铜梁区"),
    ("重庆市",   "重庆市",   "武隆县"):   ("重庆市",   "重庆市",   "武隆区"),
    ("重庆市",   "重庆市",   "双桥区"):   ("重庆市",   "重庆市",   "大足区"),
    # Original notebook comment normalized for the public code archive.
    ("浙江省",   "杭州市",   "下城区"):   ("浙江省",   "杭州市",   "拱墅区"),
    ("浙江省",   "杭州市",   "江干区"):   ("浙江省",   "杭州市",   "上城区"),
    # CHFS/CFHS processing note.
}

MUNICIPALITIES = {"北京市", "天津市", "上海市", "重庆市"}

def build_first_round():
    """Archived notebook note for 07_build_unbalanced_household_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = load_panel()
    geo = load_geo()

    df1 = df.merge(geo, on=["省", "市", "县"], how="left")
    df1 = df1.rename(columns={"县代码": "county_code"})

    n_total = len(df1)
    n_missing = df1["county_code"].isna().sum()
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    df1.to_excel(OUT_FIRST, index=False)
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    unmatched = (
        df1.loc[df1["county_code"].isna(), ["省", "市", "县"]]
           .drop_duplicates()
           .rename(columns={"省": "旧省", "市": "旧市", "县": "旧县"})
           .sort_values(["旧省", "旧市", "旧县"])
           .reset_index(drop=True)
    )
    unmatched["新省"] = np.nan
    unmatched["新市"] = np.nan
    unmatched["新县"] = np.nan

    unmatched.to_excel(CROSSWALK_XLSX, index=False)
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")

def auto_fill_crosswalk(map_df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 07_build_unbalanced_household_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    map_df = map_df.copy()

    # Original notebook comment normalized for the public code archive.
    for col in ["旧省", "旧市", "旧县", "新省", "新市", "新县"]:
        if col in map_df.columns:
            map_df[col] = clean_str_col(map_df[col])

    # Original notebook comment normalized for the public code archive.
    mask_empty_new = map_df["新县"].isna()

    auto_filled = 0

    for idx, row in map_df.loc[mask_empty_new].iterrows():
        old_prov = row["旧省"]
        old_city = row["旧市"]
        old_county = row["旧县"]

        new_prov = None
        new_city = None
        new_county = None

        # Original notebook comment normalized for the public code archive.
        if (old_prov in MUNICIPALITIES) and (old_city == "市辖区"):
            new_prov = old_prov
            new_city = old_prov
            new_county = old_county

        # Original notebook comment normalized for the public code archive.
        key = (old_prov, old_city, old_county)
        if key in MANUAL_NAME_MAP:
            new_prov, new_city, new_county = MANUAL_NAME_MAP[key]

        if new_prov is not None and new_city is not None and new_county is not None:
            map_df.at[idx, "新省"] = new_prov
            map_df.at[idx, "新市"] = new_city
            map_df.at[idx, "新县"] = new_county
            auto_filled += 1

    print("[INFO] Notebook progress message.")
    return map_df

def second_round_with_crosswalk():
    """Archived notebook note for 07_build_unbalanced_household_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = load_panel()
    geo = load_geo()

    if not CROSSWALK_XLSX.exists():
        print("[INFO] Notebook progress message.")
        build_first_round()
        return

    # Original notebook comment normalized for the public code archive.
    print("[INFO] Notebook progress message.")
    map_df = pd.read_excel(CROSSWALK_XLSX)
    expected_cols = {"旧省", "旧市", "旧县", "新省", "新市", "新县"}
    if not expected_cols.issubset(set(map_df.columns)):
        raise KeyError(f"县名对照表缺少列：{expected_cols - set(map_df.columns)}")

    map_df = auto_fill_crosswalk(map_df)

    # Original notebook comment normalized for the public code archive.
    map_df.to_excel(CROSSWALK_XLSX, index=False)
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    # Original notebook comment normalized for the public code archive.
    df = df.rename(columns={"省": "省_old", "市": "市_old", "县": "县_old"})

    df = df.merge(
        map_df,
        left_on=["省_old", "市_old", "县_old"],
        right_on=["旧省", "旧市", "旧县"],
        how="left"
    )

    # Original notebook comment normalized for the public code archive.
    # Original notebook comment normalized for the public code archive.
    df["省"] = df["新省"].where(df["新省"].notna(), df["省_old"])
    df["市"] = df["新市"].where(df["新市"].notna(), df["市_old"])
    df["县"] = df["新县"].where(df["新县"].notna(), df["县_old"])

    # Shapefile output note.
    df2 = df.merge(
        geo,
        on=["省", "市", "县"],
        how="left",
        validate="m:1"  # Original notebook comment normalized for the public code archive.
    )
    df2 = df2.rename(columns={"县代码": "county_code"})

    n_total = len(df2)
    n_missing = df2["county_code"].isna().sum()
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    df_out = df2.copy()

    # Original notebook comment normalized for the public code archive.
    drop_cols = ["省_old", "市_old", "县_old", "旧省", "旧市", "旧县", "新省", "新市", "新县"]
    drop_cols = [c for c in drop_cols if c in df_out.columns]
    df_out = df_out.drop(columns=drop_cols)

    df_out.to_excel(OUT_FINAL, index=False)
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    unmatched2 = (
        df2.loc[df2["county_code"].isna(), ["省", "市", "县"]]
           .drop_duplicates()
           .sort_values(["省", "市", "县"])
           .reset_index(drop=True)
    )
    unmatched2.to_excel(UNMATCHED_XLSX, index=False)
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")

# =============================================================================
if __name__ == "__main__":
    # Original notebook comment normalized for the public code archive.
    if not CROSSWALK_XLSX.exists():
        build_first_round()
    else:
        second_round_with_crosswalk()


# ------------------------------------------------------------------------------
# Notebook cell 13
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 07_build_unbalanced_household_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import re
import numpy as np
import pandas as pd

# =============================================================================
ROOT = r"E:\project_flood_impact_assessment\教育数据\CHFS_center"
WAVES = [2011, 2013, 2015, 2017, 2019]

FILES = {
    2011: os.path.join(ROOT, "2011", "CHFS2011_教育与收入_户级.xlsx"),
    2013: os.path.join(ROOT, "2013", "CHFS2013_教育与收入_户级.xlsx"),
    2015: os.path.join(ROOT, "2015", "CHFS2015_教育与收入_户级.xlsx"),
    2017: os.path.join(ROOT, "2017", "CHFS2017_教育与收入_户级.xlsx"),
    # Original notebook comment normalized for the public code archive.
    # CHFS/CFHS processing note.
    2019: os.path.join(ROOT, "2019", "CHFS2019_教育与收入_户级.xlsx"),
}

# Original notebook comment normalized for the public code archive.
INCOME_YEAR_MAP = {
    2011: 2010,
    2013: 2012,
    2015: 2014,
    2017: 2016,
    2019: 2018,
}

# Original notebook comment normalized for the public code archive.
SURVEY_YEAR_MAP = {
    2011: 2011,
    2013: 2013,
    2015: 2015,
    2017: 2017,
    2019: 2019,
}

OUTDIR = os.path.join(ROOT, "output")
os.makedirs(OUTDIR, exist_ok=True)

# =============================================================================
def normalize_id_val(x):
    """Archived notebook note for 07_build_unbalanced_household_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if pd.isna(x):
        return pd.NA
    s = str(x).strip()
    if s.lower() in {"nan", "nat", ""}:
        return pd.NA
    # Original notebook comment normalized for the public code archive.
    s = re.sub(r"\.0+$", "", s)
    s = s.replace(" ", "")
    return s if s else pd.NA

def to_int_series(s):
    return pd.to_numeric(s, errors="coerce").astype("Int64")

def to_float_series(s):
    return pd.to_numeric(s, errors="coerce")

def compute_edu_debt_indicator(df, year):
    """Archived notebook note for 07_build_unbalanced_household_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    idx = df.index
    out = pd.Series(pd.NA, index=idx, dtype="Int64")

    def combine_by_cols(col_list):
        if not col_list:
            return out
        sub = df[col_list].apply(pd.to_numeric, errors="coerce")
        any1 = (sub == 1).any(axis=1)
        any_nonmiss = sub.notna().any(axis=1)
        all2 = (sub == 2).all(axis=1) & any_nonmiss

        res = pd.Series(pd.NA, index=idx, dtype="Int64")
        res.loc[any1] = 1
        res.loc[~any1 & all2] = 2
        return res

    if year in (2011, 2013, 2015):
        cols = []
        c1 = "是否有教育银行贷款（原始码1/2）"
        c2 = "是否为子女教育向他人/机构借款（原始码1/2）"
        if c1 in df.columns: cols.append(c1)
        if c2 in df.columns: cols.append(c2)
        if cols:
            out = combine_by_cols(cols)

    elif year == 2017:
        cols = []
        c1 = "是否有教育银行贷款（原始码1/2）"
        c2 = "是否有教育民间借款（原始码1/2）"
        if c1 in df.columns: cols.append(c1)
        if c2 in df.columns: cols.append(c2)
        if cols:
            out = combine_by_cols(cols)

    elif year == 2019:
        c = "是否有教育负债（原始码1/2）"
        if c in df.columns:
            out = to_int_series(df[c])

    return out

def compute_edu_debt_balance(df, year):
    """Archived notebook note for 07_build_unbalanced_household_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    idx = df.index
    out = pd.Series(np.nan, index=idx)

    if year in (2011, 2013, 2015):
        cols = []
        c1 = "教育贷款总额（元）"
        c2 = "子女教育借款总额（元）"
        if c1 in df.columns: cols.append(c1)
        if c2 in df.columns: cols.append(c2)
        if cols:
            sub = df[cols].apply(to_float_series)
            # Original notebook comment normalized for the public code archive.
            out = sub.sum(axis=1, min_count=1)

    elif year == 2017:
        c = "教育民间借款尚欠金额（元）"
        if c in df.columns:
            out = to_float_series(df[c])

    elif year == 2019:
        c = "教育负债余额（元）"
        if c in df.columns:
            out = to_float_series(df[c])

    return out

def read_wave_to_panel(year, path):
    """Archived notebook note for 07_build_unbalanced_household_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print("[INFO] Notebook progress message.")
    df = pd.read_excel(path)

    if "家庭ID" not in df.columns:
        raise KeyError(f"{year} 波 Excel 缺少列：家庭ID")

    # =============================================================================
    famid = df["家庭ID"].map(normalize_id_val)

    # =============================================================================
    prov = df["省"] if "省" in df.columns else pd.Series(pd.NA, index=df.index)
    city = df["市"] if "市" in df.columns else pd.Series(pd.NA, index=df.index)
    county = df["县"] if "县" in df.columns else pd.Series(pd.NA, index=df.index)

    # =============================================================================
    if "是否农村" in df.columns:
        rural_t = to_int_series(df["是否农村"])
    else:
        rural_t = pd.Series(pd.NA, index=df.index, dtype="Int64")

    # =============================================================================
    if "抽样权重" in df.columns:
        weight = to_float_series(df["抽样权重"])
    else:
        weight = pd.Series(np.nan, index=df.index)

    # =============================================================================
    inc_cols = [c for c in df.columns if "家庭可支配收入" in str(c)]
    if inc_cols:
        inc_col = inc_cols[0]
        income = to_float_series(df[inc_col])
    else:
        inc_col = None
        income = pd.Series(np.nan, index=df.index)

    income_year = INCOME_YEAR_MAP.get(year, year - 1)

    # =============================================================================
    # Original notebook comment normalized for the public code archive.
    edu_cols = [
        c for c in df.columns
        if ("去年" in str(c) and "教育" in str(c)
            and "培训" in str(c) and "支出" in str(c)
            and "子女" not in str(c))
    ]
    if edu_cols:
        edu_col = edu_cols[0]
        edu_training = to_float_series(df[edu_col])
    else:
        edu_col = None
        edu_training = pd.Series(np.nan, index=df.index)

    # =============================================================================
    child_train_cols = [
        c for c in df.columns
        if ("去年" in str(c) and "子女" in str(c)
            and "教育" in str(c) and "培训" in str(c) and "支出" in str(c))
    ]
    if child_train_cols:
        child_train_col = child_train_cols[0]
        edu_child_training = to_float_series(df[child_train_col])
    else:
        edu_child_training = pd.Series(np.nan, index=df.index)

    edu_year = INCOME_YEAR_MAP.get(year, year - 1)

    # =============================================================================
    # Original notebook comment normalized for the public code archive.
    all_stu_cols = [c for c in df.columns if "在校成员教育支出总额" in str(c)]
    if all_stu_cols:
        stu_all = to_float_series(df[all_stu_cols[0]])
    else:
        stu_all = pd.Series(np.nan, index=df.index)

    # Original notebook comment normalized for the public code archive.
    u15_stu_cols = [c for c in df.columns if "15岁及以下子女教育支出总额" in str(c)]
    if u15_stu_cols:
        stu_u15 = to_float_series(df[u15_stu_cols[0]])
    else:
        stu_u15 = pd.Series(np.nan, index=df.index)

    # =============================================================================
    child_any_col = "是否有15岁及以下儿童"
    child_num_col = "15岁及以下儿童数量"

    if child_any_col in df.columns:
        has_child = to_int_series(df[child_any_col])
    else:
        has_child = pd.Series(pd.NA, index=df.index, dtype="Int64")

    if child_num_col in df.columns:
        n_child = to_int_series(df[child_num_col])
    else:
        n_child = pd.Series(pd.NA, index=df.index, dtype="Int64")

    # =============================================================================
    has_edu_debt = compute_edu_debt_indicator(df, year)
    edu_debt_bal = compute_edu_debt_balance(df, year)

    # =============================================================================
    # Excel output note.
    birth_min = to_float_series(df["最年长成员出生年"]) if "最年长成员出生年" in df.columns else pd.Series(np.nan, index=df.index)
    birth_max = to_float_series(df["最年轻成员出生年"]) if "最年轻成员出生年" in df.columns else pd.Series(np.nan, index=df.index)
    birth_mean = to_float_series(df["家庭成员平均出生年"]) if "家庭成员平均出生年" in df.columns else pd.Series(np.nan, index=df.index)

    # Original notebook comment normalized for the public code archive.
    survey_year = SURVEY_YEAR_MAP.get(year, year)
    if "家庭成员平均出生年" in df.columns:
        age_mean = survey_year - birth_mean
    else:
        age_mean = pd.Series(np.nan, index=df.index)

    edu_code = to_int_series(df["家庭最高文化程度（代码）"]) if "家庭最高文化程度（代码）" in df.columns else pd.Series(pd.NA, index=df.index, dtype="Int64")
    edu_label = df["家庭最高文化程度"] if "家庭最高文化程度" in df.columns else pd.Series(pd.NA, index=df.index)

    # =============================================================================
    panel_y = pd.DataFrame({
        "家庭ID": famid,
        "来源年份": year,
        "省": prov,
        "市": city,
        "县": county,
        "是否农村_当年": rural_t,
        "家庭可支配收入（元）": income,
        "收入口径年份": income_year,
        "是否有教育负债（原始码1/2）": has_edu_debt,
        "教育负债余额（元）": edu_debt_bal,
        "去年教育培训支出（元）": edu_training,
        "去年子女教育培训支出（元）": edu_child_training,
        "教育培训支出口径年份": edu_year,
        "在校成员教育支出总额（元）": stu_all,
        "15岁及以下子女教育支出总额（元）": stu_u15,
        "是否有15岁及以下儿童": has_child,
        "15岁及以下儿童数量": n_child,
        # Original notebook comment normalized for the public code archive.
        "最年长成员出生年": birth_min,
        "最年轻成员出生年": birth_max,
        "家庭成员平均出生年": birth_mean,
        "家庭成员平均年龄": age_mean,
        "家庭最高文化程度（代码）": edu_code,
        "家庭最高文化程度": edu_label,
    })

    # Original notebook comment normalized for the public code archive.
    panel_y = panel_y.dropna(subset=["家庭ID"]).reset_index(drop=True)

    # =============================================================================
    weights_y = pd.DataFrame({
        "家庭ID": panel_y["家庭ID"],
        "来源年份": year,
        "抽样权重": weight.loc[panel_y.index].values,
    })

    return panel_y, weights_y


def derive_rural_panel(panel_df):
    """Archived notebook note for 07_build_unbalanced_household_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    def decide(s):
        s = s.dropna()
        if s.empty:
            return pd.NA
        n_rural = (s == 1).sum()
        n_urban = (s == 0).sum()
        if n_rural > n_urban:
            return 1
        elif n_urban > n_rural:
            return 0
        else:
            return pd.NA

    rural_panel = (panel_df
                   .groupby("家庭ID")["是否农村_当年"]
                   .apply(decide)
                   .astype("Int64"))
    return rural_panel


# =============================================================================
panel_list = []
weight_list = []

for y in WAVES:
    p_y, w_y = read_wave_to_panel(y, FILES[y])
    panel_list.append(p_y)
    weight_list.append(w_y)

# Original notebook comment normalized for the public code archive.
panel = pd.concat(panel_list, axis=0, ignore_index=True)

# Original notebook comment normalized for the public code archive.
panel = panel.sort_values(["家庭ID", "来源年份"]).reset_index(drop=True)

# Original notebook comment normalized for the public code archive.
dup_cnt = panel.duplicated(subset=["家庭ID", "来源年份"]).sum()
print("[INFO] Notebook progress message.")

# =============================================================================
rural_panel = derive_rural_panel(panel)
rural_panel_df = rural_panel.reset_index().rename(columns={"是否农村_当年": "是否农村"})

panel = panel.merge(rural_panel_df, on="家庭ID", how="left")

# Original notebook comment normalized for the public code archive.
col_order = [
    "家庭ID", "来源年份",
    "省", "市", "县",
    "是否农村",          # Original notebook comment normalized for the public code archive.
    "是否农村_当年",     # Original notebook comment normalized for the public code archive.
    "家庭可支配收入（元）", "收入口径年份",
    "是否有教育负债（原始码1/2）", "教育负债余额（元）",
    "去年教育培训支出（元）",
    "去年子女教育培训支出（元）",
    "教育培训支出口径年份",
    "在校成员教育支出总额（元）",
    "15岁及以下子女教育支出总额（元）",
    "是否有15岁及以下儿童", "15岁及以下儿童数量",
    # Original notebook comment normalized for the public code archive.
    "最年长成员出生年",
    "最年轻成员出生年",
    "家庭成员平均出生年",
    "家庭成员平均年龄",
    "家庭最高文化程度（代码）",
    "家庭最高文化程度",
]
# Original notebook comment normalized for the public code archive.
col_order = [c for c in col_order if c in panel.columns]
panel = panel[col_order].copy()

# =============================================================================
out_panel = os.path.join(OUTDIR, "CHFS_家庭不平衡面板_2011_2019.xlsx")
panel.to_excel(out_panel, index=False)
print("[INFO] Notebook progress message.")

# =============================================================================
weights_all = pd.concat(weight_list, axis=0, ignore_index=True)
weights_all = weights_all.dropna(subset=["家庭ID"]).copy()
weights_all = weights_all.sort_values(["家庭ID", "来源年份"]).reset_index(drop=True)

out_w = os.path.join(OUTDIR, "CHFS_家庭不平衡面板_抽样权重.xlsx")
weights_all.to_excel(out_w, index=False)
print("[INFO] Notebook progress message.")


# ------------------------------------------------------------------------------
# Notebook cell 15
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 07_build_unbalanced_household_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import pandas as pd
import geopandas as gpd
from pathlib import Path

# =============================================================================
ROOT = Path(r"E:\project_flood_impact_assessment\教育数据\CHFS_center")
PANEL_IN   = ROOT / "output" / "CHFS_家庭不平衡面板_2011_2019.xlsx"
SHAPEFILE  = Path(r"D:\GISdata\GS（2024）0650号\1\country.shp")

# Original notebook comment normalized for the public code archive.
MAPPING_XLSX = ROOT / "output" / "CHFS_县名人工对照表.xlsx"

# Original notebook comment normalized for the public code archive.
OUT_FIRST  = ROOT / "output" / "CHFS_家庭不平衡面板_2011_2019_带县代码_第一轮.xlsx"
OUT_FINAL  = ROOT / "output" / "CHFS_家庭不平衡面板_2011_2019_带县代码_二次回填.xlsx"


def norm_str(s):
    """Archived notebook note for 07_build_unbalanced_household_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if pd.isna(s):
        return None
    s2 = str(s).strip()
    return s2 if s2 and s2.lower() not in {"nan", "nat"} else None


# =============================================================================
print("[INFO] Notebook progress message.")
df = pd.read_excel(PANEL_IN)

for col in ["省", "市", "县"]:
    if col in df.columns:
        df[col] = df[col].map(norm_str)

print("[INFO] Notebook progress message.")
gdf = gpd.read_file(SHAPEFILE)

# Original notebook comment normalized for the public code archive.
geo = gdf[["省", "市", "县", "县代码"]].copy()

for col in ["省", "市", "县"]:
    if col in geo.columns:
        geo[col] = geo[col].map(norm_str)

# Original notebook comment normalized for the public code archive.
geo["县代码"] = pd.to_numeric(geo["县代码"], errors="coerce").astype("Int64")

# Shapefile output note.
geo = geo.drop_duplicates(subset=["省", "市", "县"], keep="first")

# =============================================================================
df1 = df.merge(
    geo,
    on=["省", "市", "县"],
    how="left",
    suffixes=("", "_geo")
)

df1 = df1.rename(columns={"县代码": "county_code"})

n_total   = len(df1)
n_missing = df1["county_code"].isna().sum()
print("[INFO] Notebook progress message.")

# Original notebook comment normalized for the public code archive.
df1.to_excel(OUT_FIRST, index=False)
print("[INFO] Notebook progress message.")

# Original notebook comment normalized for the public code archive.
unmatched = (
    df1.loc[df1["county_code"].isna(), ["省", "市", "县"]]
       .drop_duplicates()
       .sort_values(["省", "市", "县"])
)

print("[INFO] Notebook progress message.")

# =============================================================================
if not MAPPING_XLSX.exists():
    mapping_tpl = unmatched.rename(columns={"省": "旧省", "市": "旧市", "县": "旧县"})
    mapping_tpl["新省"] = ""
    mapping_tpl["新市"] = ""
    mapping_tpl["新县"] = ""

    mapping_tpl.to_excel(MAPPING_XLSX, index=False)
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    raise SystemExit()

# =============================================================================
print("[INFO] Notebook progress message.")
mapping = pd.read_excel(MAPPING_XLSX)

for col in ["旧省", "旧市", "旧县", "新省", "新市", "新县"]:
    if col in mapping.columns:
        mapping[col] = mapping[col].map(norm_str)

mapping = mapping.dropna(subset=["旧省", "旧市", "旧县", "新县"])

df2 = df1.merge(
    mapping[["旧省", "旧市", "旧县", "新省", "新市", "新县"]],
    left_on=["省", "市", "县"],
    right_on=["旧省", "旧市", "旧县"],
    how="left"
)

df2["省_final"] = df2["新省"].combine_first(df2["省"])
df2["市_final"] = df2["新市"].combine_first(df2["市"])
df2["县_final"] = df2["新县"].combine_first(df2["县"])

df2 = df2.drop(columns=["county_code"])
geo_final = geo.rename(columns={"省": "省_final", "市": "市_final", "县": "县_final"})

df2 = df2.merge(
    geo_final,
    on=["省_final", "市_final", "县_final"],
    how="left"
)

df2 = df2.rename(columns={"县代码": "county_code"})

n_missing2 = df2["county_code"].isna().sum()
print("[INFO] Notebook progress message.")

df2["省"] = df2["省_final"]
df2["市"] = df2["市_final"]
df2["县"] = df2["县_final"]

drop_cols = [c for c in ["旧省", "旧市", "旧县", "新省", "新市", "新县",
                         "省_final","市_final","县_final"] if c in df2.columns]
df2 = df2.drop(columns=drop_cols)

df2.to_excel(OUT_FINAL, index=False)
print("[INFO] Notebook progress message.")


# ------------------------------------------------------------------------------
# Notebook cell 17
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 07_build_unbalanced_household_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import pandas as pd
import geopandas as gpd
import numpy as np
from pathlib import Path

# =============================================================================
ROOT = Path(r"E:\project_flood_impact_assessment\教育数据\CHFS_center")

PANEL_XLSX = ROOT / "output" / "CHFS_家庭不平衡面板_2011_2019.xlsx"
SHAPEFILE  = Path(r"D:\GISdata\GS（2024）0650号\1\country.shp")

OUT_FIRST  = ROOT / "output" / "CHFS_家庭不平衡面板_2011_2019_带县代码_第一轮.xlsx"
OUT_FINAL  = ROOT / "output" / "CHFS_家庭不平衡面板_2011_2019_带县代码_最终版.xlsx"

CROSSWALK_XLSX = ROOT / "output" / "CHFS_县名人工对照表.xlsx"
UNMATCHED_XLSX = ROOT / "output" / "CHFS_县名人工对照表_仍未匹配.xlsx"

def clean_str_col(s: pd.Series) -> pd.Series:
    """Archived notebook note for 07_build_unbalanced_household_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    return (
        s.astype(str)
         .str.strip()
         .replace({"nan": None, "NaN": None, "": None})
    )

def load_panel():
    print("[INFO] Notebook progress message.")
    df = pd.read_excel(PANEL_XLSX)

    for col in ["省", "市", "县"]:
        if col in df.columns:
            df[col] = clean_str_col(df[col])
        else:
            raise KeyError(f"面板缺少列: {col}")
    return df

def load_geo():
    print("[INFO] Notebook progress message.")
    gdf = gpd.read_file(SHAPEFILE)

    need_cols = ["省", "市", "县", "县代码"]
    for c in need_cols:
        if c not in gdf.columns:
            raise KeyError(f"行政区划 shapefile 缺少字段: {c}")

    geo = gdf[need_cols].copy()
    for col in ["省", "市", "县"]:
        geo[col] = clean_str_col(geo[col])

    geo = geo.drop_duplicates(subset=["省", "市", "县"], keep="first")
    return geo

# Original notebook comment normalized for the public code archive.
MANUAL_NAME_MAP = {
    ("四川省",   "宜宾市",   "宜宾县"):   ("四川省",   "宜宾市",   "叙州区"),
    ("广东省",   "广州市",   "增城市"):   ("广东省",   "广州市",   "增城区"),
    ("湖北省",   "荆州市",   "监利县"):   ("湖北省",   "荆州市",   "监利市"),
    ("广西壮族自治区", "南宁市", "新城区"): ("广西壮族自治区", "南宁市", "青秀区"),
    ("甘肃省",   "天水市",   "北道区"):   ("甘肃省",   "天水市",   "麦积区"),
    ("安徽省",   "合肥市",   "西市区"):   ("安徽省",   "合肥市",   "庐阳区"),
    ("湖南省",   "永州市",   "芝山区"):   ("湖南省",   "永州市",   "零陵区"),
    ("云南省",   "曲靖市",   "沾益县"):   ("云南省",   "曲靖市",   "沾益区"),
    ("辽宁省",   "沈阳市",   "辽中县"):   ("辽宁省",   "沈阳市",   "辽中区"),
    ("山东省",   "青岛市",   "即墨市"):   ("山东省",   "青岛市",   "即墨区"),
    ("吉林省",   "长春市",   "九台市"):   ("吉林省",   "长春市",   "九台区"),
    ("河北省",   "保定市",   "清苑县"):   ("河北省",   "保定市",   "清苑区"),
    ("重庆市",   "重庆市",   "潼南县"):   ("重庆市",   "重庆市",   "潼南区"),
    ("重庆市",   "重庆市",   "铜梁县"):   ("重庆市",   "重庆市",   "铜梁区"),
    ("重庆市",   "重庆市",   "武隆县"):   ("重庆市",   "重庆市",   "武隆区"),
    ("重庆市",   "重庆市",   "双桥区"):   ("重庆市",   "重庆市",   "大足区"),
    ("浙江省",   "杭州市",   "下城区"):   ("浙江省",   "杭州市",   "拱墅区"),
    ("浙江省",   "杭州市",   "江干区"):   ("浙江省",   "杭州市",   "上城区"),
}

MUNICIPALITIES = {"北京市", "天津市", "上海市", "重庆市"}

def build_first_round():
    df = load_panel()
    geo = load_geo()

    df1 = df.merge(geo, on=["省", "市", "县"], how="left")
    df1 = df1.rename(columns={"县代码": "county_code"})

    n_total = len(df1)
    n_missing = df1["county_code"].isna().sum()
    print("[INFO] Notebook progress message.")

    df1.to_excel(OUT_FIRST, index=False)
    print("[INFO] Notebook progress message.")

    unmatched = (
        df1.loc[df1["county_code"].isna(), ["省", "市", "县"]]
           .drop_duplicates()
           .rename(columns={"省": "旧省", "市": "旧市", "县": "旧县"})
           .sort_values(["旧省", "旧市", "旧县"])
           .reset_index(drop=True)
    )
    unmatched["新省"] = np.nan
    unmatched["新市"] = np.nan
    unmatched["新县"] = np.nan

    unmatched.to_excel(CROSSWALK_XLSX, index=False)
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")

def auto_fill_crosswalk(map_df: pd.DataFrame) -> pd.DataFrame:
    map_df = map_df.copy()

    for col in ["旧省", "旧市", "旧县", "新省", "新市", "新县"]:
        if col in map_df.columns:
            map_df[col] = clean_str_col(map_df[col])

    mask_empty_new = map_df["新县"].isna()
    auto_filled = 0

    for idx, row in map_df.loc[mask_empty_new].iterrows():
        old_prov = row["旧省"]
        old_city = row["旧市"]
        old_county = row["旧县"]

        new_prov = None
        new_city = None
        new_county = None

        # Original notebook comment normalized for the public code archive.
        if (old_prov in MUNICIPALITIES) and (old_city == "市辖区"):
            new_prov = old_prov
            new_city = old_prov
            new_county = old_county

        # Original notebook comment normalized for the public code archive.
        key = (old_prov, old_city, old_county)
        if key in MANUAL_NAME_MAP:
            new_prov, new_city, new_county = MANUAL_NAME_MAP[key]

        if new_prov is not None and new_city is not None and new_county is not None:
            map_df.at[idx, "新省"] = new_prov
            map_df.at[idx, "新市"] = new_city
            map_df.at[idx, "新县"] = new_county
            auto_filled += 1

    print("[INFO] Notebook progress message.")
    return map_df

def second_round_with_crosswalk():
    df = load_panel()
    geo = load_geo()

    if not CROSSWALK_XLSX.exists():
        print("[INFO] Notebook progress message.")
        build_first_round()
        return

    print("[INFO] Notebook progress message.")
    map_df = pd.read_excel(CROSSWALK_XLSX)
    expected_cols = {"旧省", "旧市", "旧县", "新省", "新市", "新县"}
    if not expected_cols.issubset(set(map_df.columns)):
        raise KeyError(f"县名对照表缺少列：{expected_cols - set(map_df.columns)}")

    map_df = auto_fill_crosswalk(map_df)

    map_df.to_excel(CROSSWALK_XLSX, index=False)
    print("[INFO] Notebook progress message.")

    df = df.rename(columns={"省": "省_old", "市": "市_old", "县": "县_old"})

    df = df.merge(
        map_df,
        left_on=["省_old", "市_old", "县_old"],
        right_on=["旧省", "旧市", "旧县"],
        how="left"
    )

    df["省"] = df["新省"].where(df["新省"].notna(), df["省_old"])
    df["市"] = df["新市"].where(df["新市"].notna(), df["市_old"])
    df["县"] = df["新县"].where(df["新县"].notna(), df["县_old"])

    df2 = df.merge(
        geo,
        on=["省", "市", "县"],
        how="left",
        validate="m:1"
    )
    df2 = df2.rename(columns={"县代码": "county_code"})

    n_total = len(df2)
    n_missing = df2["county_code"].isna().sum()
    print("[INFO] Notebook progress message.")

    df_out = df2.copy()

    drop_cols = ["省_old", "市_old", "县_old", "旧省", "旧市", "旧县", "新省", "新市", "新县"]
    drop_cols = [c for c in drop_cols if c in df_out.columns]
    df_out = df_out.drop(columns=drop_cols)

    df_out.to_excel(OUT_FINAL, index=False)
    print("[INFO] Notebook progress message.")

    unmatched2 = (
        df2.loc[df2["county_code"].isna(), ["省", "市", "县"]]
           .drop_duplicates()
           .sort_values(["省", "市", "县"])
           .reset_index(drop=True)
    )
    unmatched2.to_excel(UNMATCHED_XLSX, index=False)
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")

if __name__ == "__main__":
    if not CROSSWALK_XLSX.exists():
        build_first_round()
    else:
        second_round_with_crosswalk()
