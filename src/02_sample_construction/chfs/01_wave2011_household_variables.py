#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 01_wave2011_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 7
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 01_wave2011_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import pandas as pd
import numpy as np

# =============================================================================
BASE = r"E:\project_flood_impact_assessment\教育数据\CHFS_center\2011"
FN_HH  = "chfs2011_hh_20191120_version14.dta"
FN_IND = "chfs2011_ind_20191120_version14.dta"
FN_GEO = "区县码2011.dta"
OUT_XLSX = "CHFS2011_教育与收入_户级.xlsx"

SURVEY_YEAR  = 2011
INCOME_YEAR  = 2010

# =============================================================================
def read_stata_safe(path):
    try:
        return pd.read_stata(path, convert_categoricals=False)
    except Exception:
        return pd.read_stata(path, convert_categoricals=True)

def drop_duplicate_columns(df, keep="first"):
    # Original notebook comment normalized for the public code archive.
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated(keep=keep)]
    return df

def to_int(series):
    return pd.to_numeric(series, errors="coerce").astype("Int64")

def strip_str(s):
    if pd.isna(s): return pd.NA
    s2 = str(s).strip()
    return s2 if s2 else pd.NA

def normalize_id(x):
    if pd.isna(x): return pd.NA
    s = str(x).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s if s else pd.NA

def map_yes_no_to_binary(s):
    if pd.isna(s): return pd.NA
    m = {1:1, 2:0, "1":1, "2":0, "是":1, "否":0, True:1, False:0, "yes":1, "no":0, "Y":1, "N":0}
    return m.get(s, pd.NA)

def clean_missing_codes(df):
    miss_maps = {"g1016":[-9,-7], "e1012":[-9999], "e1021":[-9]}
    for col, bads in miss_maps.items():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").replace(bads, np.nan)
    return df

# =============================================================================
hh  = drop_duplicate_columns(read_stata_safe(os.path.join(BASE, FN_HH)))
ind = drop_duplicate_columns(read_stata_safe(os.path.join(BASE, FN_IND)))
geo = drop_duplicate_columns(read_stata_safe(os.path.join(BASE, FN_GEO)))

# =============================================================================
if "hhid" not in hh.columns or "hhid" not in ind.columns:
    raise KeyError("2011 HH/IND 必须包含 hhid 列")

hh["hhid"]  = hh["hhid"].map(normalize_id)
ind["hhid"] = ind["hhid"].map(normalize_id)

# Original notebook comment normalized for the public code archive.
if "hhid_2011" in geo.columns and "hhid" in geo.columns:
    geo = geo.drop(columns=["hhid"])
    key_col = "hhid_2011"
elif "hhid_2011" in geo.columns:
    key_col = "hhid_2011"
elif "hhid" in geo.columns:
    key_col = "hhid"
else:
    raise KeyError("2011 GEO 缺少 hhid_2011 / hhid")

geo = geo.rename(columns={key_col: "hhid"})
geo["hhid"] = geo["hhid"].map(normalize_id)

# =============================================================================
if "a2005" not in ind.columns:
    raise KeyError("2011 IND 缺少 a2005（出生年）")
ind["a2005"] = to_int(ind["a2005"])
ind["age"]   = SURVEY_YEAR - ind["a2005"]
ind.loc[(ind["age"] < 0) | (ind["age"] > 120), "age"] = pd.NA

child = (ind.assign(child_u15=(ind["age"] <= 15).astype("Int64"))
           .groupby("hhid", as_index=False)["child_u15"].sum()
           .rename(columns={"child_u15":"child_u15_num"}))
child["any_child_u15"] = (child["child_u15_num"] > 0).astype("Int64")
child = drop_duplicate_columns(child)   # Original notebook comment normalized for the public code archive.

# =============================================================================
keep_geo = ["hhid"] + [c for c in ["prov_CHN","city","county","rural","swgt"] if c in geo.columns]
geo = geo.loc[:, keep_geo].copy()
geo = drop_duplicate_columns(geo)
geo = geo.drop_duplicates(subset="hhid", keep="first")
if "rural" in geo.columns: geo["rural"] = to_int(geo["rural"])
if "swgt"  in geo.columns: geo["swgt"]  = pd.to_numeric(geo["swgt"], errors="coerce")

# =============================================================================
hh = drop_duplicate_columns(hh)      # Original notebook comment normalized for the public code archive.
df = hh.merge(child, on="hhid", how="left", validate="one_to_one")
df = df.merge(geo,   on="hhid", how="left", validate="one_to_one")

for c in ["child_u15_num","any_child_u15"]:
    if c in df.columns:
        df[c] = df[c].fillna(0).astype("Int64")

# =============================================================================
df = clean_missing_codes(df)
df["是否有教育银行贷款_二元"] = df.get("e1001").apply(map_yes_no_to_binary).astype("Int64")
df["是否为子女教育借款_二元"]   = df.get("e1020").apply(map_yes_no_to_binary).astype("Int64")

# =============================================================================
df["panel_id"] = df["hhid"]  # Original notebook comment normalized for the public code archive.
select_cols = [
    "panel_id","hhid","prov_CHN","city","county","rural","swgt",
    "hh_income","censor_hh_income","e1001","e1008","e1012","e1020","e1021","g1016",
    "any_child_u15","child_u15_num","是否有教育银行贷款_二元","是否为子女教育借款_二元"
]
select_cols = [c for c in select_cols if c in df.columns]
out = df[select_cols].rename(columns={
    "panel_id":"家庭ID","hhid":"当波家庭ID","prov_CHN":"省","city":"市","county":"县",
    "rural":"是否农村","swgt":"抽样权重",
    "hh_income":f"家庭可支配收入（{INCOME_YEAR}年，元）","censor_hh_income":"收入截尾标记",
    "e1001":"是否有教育银行贷款（原始码1/2）","e1008":"教育贷款年份","e1012":"教育贷款总额（元）",
    "e1020":"是否为子女教育向他人/机构借款（原始码1/2）","e1021":"子女教育借款总额（元）",
    "g1016":f"去年教育培训支出（{INCOME_YEAR}年，元）",
    "any_child_u15":"是否有15岁及以下儿童","child_u15_num":"15岁及以下儿童数量",
})
for col in ["省","市","县"]:
    if col in out.columns: out[col] = out[col].apply(strip_str)
out.to_excel(os.path.join(BASE, OUT_XLSX), index=False)
print("[INFO] Notebook progress message.", os.path.join(BASE, OUT_XLSX))


# ------------------------------------------------------------------------------
# Notebook cell 10
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 01_wave2011_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import pandas as pd
import numpy as np

# =============================================================================
BASE = r"E:\project_flood_impact_assessment\教育数据\CHFS_center\2011"
FN_HH  = "chfs2011_hh_20191120_version14.dta"
FN_IND = "chfs2011_ind_20191120_version14.dta"
FN_GEO = "区县码2011.dta"
OUT_XLSX = "CHFS2011_教育与收入_户级.xlsx"

SURVEY_YEAR  = 2011
INCOME_YEAR  = 2010

# =============================================================================
def read_stata_safe(path):
    try:
        return pd.read_stata(path, convert_categoricals=False)
    except Exception:
        return pd.read_stata(path, convert_categoricals=True)

def drop_duplicate_columns(df, keep="first"):
    # Original notebook comment normalized for the public code archive.
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated(keep=keep)]
    return df

def to_int(series):
    return pd.to_numeric(series, errors="coerce").astype("Int64")

def strip_str(s):
    if pd.isna(s): return pd.NA
    s2 = str(s).strip()
    return s2 if s2 else pd.NA

def normalize_id(x):
    if pd.isna(x): return pd.NA
    s = str(x).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s if s else pd.NA

def map_yes_no_to_binary(s):
    if pd.isna(s): return pd.NA
    m = {
        1:1, 2:0,
        "1":1, "2":0,
        "是":1, "否":0,
        True:1, False:0,
        "yes":1, "no":0, "Y":1, "N":0
    }
    return m.get(s, pd.NA)

def clean_missing_codes(df):
    # Original notebook comment normalized for the public code archive.
    miss_maps = {
        "g1016":[-9,-7],
        "e1012":[-9999],
        "e1021":[-9],
    }
    for col, bads in miss_maps.items():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").replace(bads, np.nan)
    return df

# Original notebook comment normalized for the public code archive.
EDU_LABEL_MAP = {
    1: "没上过学",
    2: "小学",
    3: "初中",
    4: "高中",
    5: "中专/职高",
    6: "大专/高职",
    7: "大学本科",
    8: "硕士研究生",
    9: "博士研究生",
}

# =============================================================================
hh  = drop_duplicate_columns(read_stata_safe(os.path.join(BASE, FN_HH)))
ind = drop_duplicate_columns(read_stata_safe(os.path.join(BASE, FN_IND)))
geo = drop_duplicate_columns(read_stata_safe(os.path.join(BASE, FN_GEO)))

# =============================================================================
if "hhid" not in hh.columns or "hhid" not in ind.columns:
    raise KeyError("2011 HH/IND 必须包含 hhid 列")

hh["hhid"]  = hh["hhid"].map(normalize_id)
ind["hhid"] = ind["hhid"].map(normalize_id)

# Original notebook comment normalized for the public code archive.
if "hhid_2011" in geo.columns and "hhid" in geo.columns:
    geo = geo.drop(columns=["hhid"])
    key_col = "hhid_2011"
elif "hhid_2011" in geo.columns:
    key_col = "hhid_2011"
elif "hhid" in geo.columns:
    key_col = "hhid"
else:
    raise KeyError("2011 GEO 缺少 hhid_2011 / hhid")

geo = geo.rename(columns={key_col: "hhid"})
geo["hhid"] = geo["hhid"].map(normalize_id)

# =============================================================================
if "a2005" not in ind.columns:
    raise KeyError("2011 IND 缺少 a2005（出生年）")

ind["a2005"] = to_int(ind["a2005"])
ind["age"]   = SURVEY_YEAR - ind["a2005"]

# Original notebook comment normalized for the public code archive.
mask_bad_age = (ind["age"] < 0) | (ind["age"] > 120)
ind.loc[mask_bad_age, ["age", "a2005"]] = pd.NA

# =============================================================================
child = (
    ind.assign(child_u15=(ind["age"] <= 15).astype("Int64"))
       .groupby("hhid", as_index=False)["child_u15"].sum()
       .rename(columns={"child_u15":"child_u15_num"})
)
child["any_child_u15"] = (child["child_u15_num"] > 0).astype("Int64")
child = drop_duplicate_columns(child)   # Original notebook comment normalized for the public code archive.

# =============================================================================
# Original notebook comment normalized for the public code archive.
if "a2012" in ind.columns:
    ind["edu_code"] = to_int(ind["a2012"])
    # Original notebook comment normalized for the public code archive.
    ind.loc[~ind["edu_code"].between(1, 9), "edu_code"] = pd.NA
else:
    ind["edu_code"] = pd.Series(pd.NA, index=ind.index, dtype="Int64")

# Original notebook comment normalized for the public code archive.
birth_agg = (
    ind.groupby("hhid")["a2005"]
       .agg(hh_birth_min="min",
            hh_birth_max="max",
            hh_birth_mean="mean")
       .reset_index()
)

# Original notebook comment normalized for the public code archive.
edu_agg = (
    ind.groupby("hhid")["edu_code"]
       .max()   # Original notebook comment normalized for the public code archive.
       .rename("hh_max_edu_code")
       .reset_index()
)

# =============================================================================
keep_geo = ["hhid"] + [c for c in ["prov_CHN","city","county","rural","swgt"] if c in geo.columns]
geo = geo.loc[:, keep_geo].copy()
geo = drop_duplicate_columns(geo)
geo = geo.drop_duplicates(subset="hhid", keep="first")
if "rural" in geo.columns:
    geo["rural"] = to_int(geo["rural"])
if "swgt"  in geo.columns:
    geo["swgt"]  = pd.to_numeric(geo["swgt"], errors="coerce")

# =============================================================================
hh = drop_duplicate_columns(hh)      # Original notebook comment normalized for the public code archive.
df = hh.merge(child,    on="hhid", how="left", validate="one_to_one")
df = df.merge(birth_agg, on="hhid", how="left")   # Original notebook comment normalized for the public code archive.
df = df.merge(edu_agg,  on="hhid", how="left")   # Original notebook comment normalized for the public code archive.
df = df.merge(geo,      on="hhid", how="left", validate="one_to_one")

for c in ["child_u15_num","any_child_u15"]:
    if c in df.columns:
        df[c] = df[c].fillna(0).astype("Int64")

# Original notebook comment normalized for the public code archive.
df["hh_max_edu_label"] = df["hh_max_edu_code"].map(EDU_LABEL_MAP)

# =============================================================================
df = clean_missing_codes(df)
df["是否有教育银行贷款_二元"] = df.get("e1001").apply(map_yes_no_to_binary).astype("Int64")
df["是否为子女教育借款_二元"]   = df.get("e1020").apply(map_yes_no_to_binary).astype("Int64")

# =============================================================================
df["panel_id"] = df["hhid"]  # Original notebook comment normalized for the public code archive.

select_cols = [
    "panel_id","hhid","prov_CHN","city","county","rural","swgt",
    "hh_income","censor_hh_income",
    "e1001","e1008","e1012","e1020","e1021","g1016",
    "any_child_u15","child_u15_num",
    "是否有教育银行贷款_二元","是否为子女教育借款_二元",
    # Original notebook comment normalized for the public code archive.
    "hh_birth_min","hh_birth_max","hh_birth_mean",
    "hh_max_edu_code","hh_max_edu_label",
]
select_cols = [c for c in select_cols if c in df.columns]

out = df[select_cols].rename(columns={
    "panel_id":"家庭ID",
    "hhid":"当波家庭ID",
    "prov_CHN":"省",
    "city":"市",
    "county":"县",
    "rural":"是否农村",
    "swgt":"抽样权重",
    "hh_income":f"家庭可支配收入（{INCOME_YEAR}年，元）",
    "censor_hh_income":"收入截尾标记",
    "e1001":"是否有教育银行贷款（原始码1/2）",
    "e1008":"教育贷款年份",
    "e1012":"教育贷款总额（元）",
    "e1020":"是否为子女教育向他人/机构借款（原始码1/2）",
    "e1021":"子女教育借款总额（元）",
    "g1016":f"去年教育培训支出（{INCOME_YEAR}年，元）",
    "any_child_u15":"是否有15岁及以下儿童",
    "child_u15_num":"15岁及以下儿童数量",
    # Original notebook comment normalized for the public code archive.
    "hh_birth_min":"最年长成员出生年",
    "hh_birth_max":"最年轻成员出生年",
    "hh_birth_mean":"家庭成员平均出生年",
    "hh_max_edu_code":"家庭最高文化程度（代码）",
    "hh_max_edu_label":"家庭最高文化程度",
})

for col in ["省","市","县"]:
    if col in out.columns:
        out[col] = out[col].apply(strip_str)

out_path = os.path.join(BASE, OUT_XLSX)
out.to_excel(out_path, index=False)
print("[INFO] Notebook progress message.", out_path)
