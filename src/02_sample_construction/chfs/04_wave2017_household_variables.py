#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 04_wave2017_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 2
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 04_wave2017_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import numpy as np
import pandas as pd

# =============================================================================
BASE = r"E:\project_flood_impact_assessment\教育数据\CHFS_center\2017"
FN_HH     = "chfs2017_hh_202206.dta"
FN_IND    = "chfs2017_ind_202206.dta"
FN_MASTER = "chfs2017_master_202206.dta"
FN_GEO    = "区县码2017.dta"

OUT_XLSX  = "CHFS2017_教育与收入_户级.xlsx"
SURVEY_YEAR = 2017
INCOME_YEAR = 2016

# =============================================================================
def read_stata_safe(path):
    try:
        return pd.read_stata(path, convert_categoricals=False)
    except Exception:
        return pd.read_stata(path, convert_categoricals=True)

def drop_duplicate_columns(df, keep="first"):
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated(keep=keep)]
    return df

def to_int(x): return pd.to_numeric(x, errors="coerce").astype("Int64")

def strip_str_or_na(s):
    if pd.isna(s): return pd.NA
    s2 = str(s).strip()
    return s2 if s2 else pd.NA

def make_hh_key(df):
    alias = {
        "hhid_2017": ["hhid_2017"],
        "hhid_2015": ["hhid_2015"],
        "hhid_2013": ["hhid_2013"],
        "hhid_2011": ["hhid_2011", "dhhid_2011"],
        "hhid":      ["hhid"],
    }
    vals = {}
    for std, cands in alias.items():
        for c in cands:
            if c in df.columns:
                vals[std] = df[c].astype(str)
                break
        else:
            vals[std] = pd.Series(pd.NA, index=df.index)
    key = vals["hhid_2017"]
    for lvl in ["hhid_2015","hhid_2013","hhid_2011","hhid"]:
        key = key.fillna(vals[lvl])
    return key.where(~key.astype(str).str.lower().isin({"nan"}), pd.NA)

def add_priority_flags(df):
    df = df.copy()
    for col in ["hhid_2017","hhid_2015","hhid_2013","hhid_2011","dhhid_2011"]:
        if col not in df.columns: df[col] = pd.NA
    df["_p2017"] = df["hhid_2017"].notna().astype(int)
    df["_p2015"] = df["hhid_2015"].notna().astype(int)
    df["_p2013"] = df["hhid_2013"].notna().astype(int)
    df["_p2011"] = df["hhid_2011"].fillna(df["dhhid_2011"]).notna().astype(int)
    return df

def dedupe_right_by_priority(df, key, value_cols=None):
    if value_cols is None: value_cols = []
    df = add_priority_flags(df)
    df["_nonnull"] = df[value_cols].notna().sum(axis=1) if value_cols else 0
    df = df.sort_values(["_p2017","_p2015","_p2013","_p2011","_nonnull"], ascending=False)
    df = df.drop_duplicates(subset=[key], keep="first")
    return df.drop(columns=[c for c in df.columns if c.startswith("_p") or c=="_nonnull"])

def first_nonnull(s):
    s = s.dropna()
    return s.iloc[0] if len(s) else np.nan

def clean_missing_codes(df):
    miss_maps = {
        "g1016":  [-9, -7],
        "e1022":  [-9, -7],
        "e1021":  [-9, -7],  # Original notebook comment normalized for the public code archive.
    }
    for col, bads in miss_maps.items():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").replace(bads, np.nan)
    return df

# =============================================================================
hh     = read_stata_safe(os.path.join(BASE, FN_HH))
ind    = read_stata_safe(os.path.join(BASE, FN_IND))
master = read_stata_safe(os.path.join(BASE, FN_MASTER))
geo    = read_stata_safe(os.path.join(BASE, FN_GEO))

hh, ind, master, geo = map(drop_duplicate_columns, [hh, ind, master, geo])

# =============================================================================
for d in (hh, ind, master, geo):
    d["hh_key"] = make_hh_key(d)

# Original notebook comment normalized for the public code archive.
hh = dedupe_right_by_priority(hh, "hh_key", value_cols=[c for c in ["e1001","e1020","g1016","e1022","e1021"] if c in hh.columns])

# =============================================================================
birth = None
if "a2005" in ind.columns: birth = to_int(ind["a2005"])
if "a1114" in ind.columns:
    b2 = to_int(ind["a1114"])
    birth = birth.fillna(b2) if birth is not None else b2
if birth is None: raise KeyError("IND 缺少出生年变量（未找到 a2005 或 a1114）")
ind["age"] = SURVEY_YEAR - birth
ind.loc[(ind["age"] < 0) | (ind["age"] > 120), "age"] = pd.NA
child = (ind.assign(child_u15=(ind["age"]<=15).astype("Int64"))
           .groupby("hh_key", as_index=False)["child_u15"].sum()
           .rename(columns={"child_u15":"child_u15_num"}))
child["any_child_u15"] = (child["child_u15_num"]>0).astype("Int64")

# =============================================================================
censor_cols = [c for c in master.columns if c.startswith("censor_total_income")]
keep_cols = ["hh_key","total_income","weight_hh"] + (censor_cols[:1] if censor_cols else [])
master_slim = master[[c for c in keep_cols if c in master.columns]].copy()

# Original notebook comment normalized for the public code archive.
if master_slim.duplicated("hh_key").any():
    agg = {"total_income": first_nonnull}
    if "weight_hh" in master_slim.columns: agg["weight_hh"] = first_nonnull
    if censor_cols: agg[censor_cols[0]] = first_nonnull
    master_slim = (master_slim.sort_values(["total_income"], ascending=False)
                   .groupby("hh_key", as_index=False).agg(agg))

# =============================================================================
geo_keep = ["hh_key","hhid","hhid_2011","hhid_2013","hhid_2015","hhid_2017",
            "prov_CHN","city","county","rural","swgt"]
geo = geo[[c for c in geo_keep if c in geo.columns]].copy()
geo = dedupe_right_by_priority(geo, "hh_key", value_cols=["prov_CHN","city","county","rural","swgt"] if "swgt" in geo.columns else ["prov_CHN","city","county","rural"])
if "rural" in geo.columns: geo["rural"] = to_int(geo["rural"])
for col in ["prov_CHN","city","county"]:
    if col in geo.columns: geo[col] = geo[col].apply(strip_str_or_na)

# =============================================================================
hh = clean_missing_codes(hh)

# =============================================================================
df = hh.merge(child,       on="hh_key", how="left", validate="one_to_one")
df = df.merge(master_slim, on="hh_key", how="left", validate="one_to_one")
df = df.merge(geo,         on="hh_key", how="left", validate="one_to_one")

# Original notebook comment normalized for the public code archive.
df["child_u15_num"] = df["child_u15_num"].fillna(0).astype("Int64")
df["any_child_u15"] = df["any_child_u15"].fillna(0).astype("Int64")

# =============================================================================
if "swgt" in df.columns:
    df["weight_out"] = pd.to_numeric(df["swgt"], errors="coerce")
elif "weight_hh" in df.columns:
    df["weight_out"] = pd.to_numeric(df["weight_hh"], errors="coerce")
else:
    df["weight_out"] = pd.NA  # Original notebook comment normalized for the public code archive.

# =============================================================================
# Original notebook comment normalized for the public code archive.
if "hhid" in df.columns: df["hhid_out"] = df["hhid"].astype(str)
elif "hhid" in hh.columns: df["hhid_out"] = hh["hhid"].astype(str)
else: df["hhid_out"] = df["hh_key"].astype(str)

# Original notebook comment normalized for the public code archive.
censor_col = None
for c in ["censor_total_income_imp"] + [c for c in df.columns if c.startswith("censor_total_income")]:
    if c in df.columns:
        censor_col = c
        break

select_cols = [
    "hhid_out",
    "prov_CHN","city","county","rural",
    "weight_out",
    "total_income",
    *( [censor_col] if censor_col else [] ),
    "e1001","e1020","e1022","e1021",  # Original notebook comment normalized for the public code archive.
    "g1016",
    "any_child_u15","child_u15_num",
]
select_cols = [c for c in select_cols if c in df.columns]

out = df[select_cols].rename(columns={
    "hhid_out": "家庭ID",
    "prov_CHN": "省",
    "city": "市",
    "county": "县",
    "rural": "是否农村",
    "weight_out": "抽样权重",
    "total_income": f"家庭可支配收入（{INCOME_YEAR}年，元）",
    (censor_col or ""): "收入截尾标记（imp）",
    "e1001": "是否有教育银行贷款（原始码1/2）",
    "e1020": "是否有教育民间借款（原始码1/2）",
    "e1022": "教育民间借款尚欠金额（元）",
    "e1021": "教育民间借款总额（旧口径，元）",
    "g1016": f"去年教育培训支出（{INCOME_YEAR}年，元）",
    "any_child_u15": "是否有15岁及以下儿童",
    "child_u15_num": "15岁及以下儿童数量",
})
if "" in out.columns:  # Original notebook comment normalized for the public code archive.
    out = out.drop(columns=[""])

# =============================================================================
out_path = os.path.join(BASE, OUT_XLSX)
out.to_excel(out_path, index=False)
print("[INFO] Notebook progress message.")
print("[INFO] Notebook progress message.", len(out))
print(out.head(5))


# ------------------------------------------------------------------------------
# Notebook cell 5
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 04_wave2017_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import numpy as np
import pandas as pd

# =============================================================================
BASE = r"E:\project_flood_impact_assessment\教育数据\CHFS_center\2017"
FN_HH     = "chfs2017_hh_202206.dta"
FN_IND    = "chfs2017_ind_202206.dta"
FN_MASTER = "chfs2017_master_202206.dta"
FN_GEO    = "区县码2017.dta"

OUT_XLSX  = "CHFS2017_教育与收入_户级.xlsx"
SURVEY_YEAR = 2017
INCOME_YEAR = 2016

# =============================================================================
def read_stata_safe(path):
    try:
        return pd.read_stata(path, convert_categoricals=False)
    except Exception:
        return pd.read_stata(path, convert_categoricals=True)

def drop_duplicate_columns(df, keep="first"):
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated(keep=keep)]
    return df

def to_int(x):
    return pd.to_numeric(x, errors="coerce").astype("Int64")

def strip_str_or_na(s):
    if pd.isna(s):
        return pd.NA
    s2 = str(s).strip()
    return s2 if s2 else pd.NA

def make_hh_key(df):
    alias = {
        "hhid_2017": ["hhid_2017"],
        "hhid_2015": ["hhid_2015"],
        "hhid_2013": ["hhid_2013"],
        "hhid_2011": ["hhid_2011", "dhhid_2011"],
        "hhid":      ["hhid"],
    }
    vals = {}
    for std, cands in alias.items():
        for c in cands:
            if c in df.columns:
                vals[std] = df[c].astype(str)
                break
        else:
            vals[std] = pd.Series(pd.NA, index=df.index)
    key = vals["hhid_2017"]
    for lvl in ["hhid_2015", "hhid_2013", "hhid_2011", "hhid"]:
        key = key.fillna(vals[lvl])
    return key.where(~key.astype(str).str.lower().isin({"nan"}), pd.NA)

def add_priority_flags(df):
    df = df.copy()
    for col in ["hhid_2017", "hhid_2015", "hhid_2013", "hhid_2011", "dhhid_2011"]:
        if col not in df.columns:
            df[col] = pd.NA
    df["_p2017"] = df["hhid_2017"].notna().astype(int)
    df["_p2015"] = df["hhid_2015"].notna().astype(int)
    df["_p2013"] = df["hhid_2013"].notna().astype(int)
    df["_p2011"] = df["hhid_2011"].fillna(df["dhhid_2011"]).notna().astype(int)
    return df

def dedupe_right_by_priority(df, key, value_cols=None):
    if value_cols is None:
        value_cols = []
    df = add_priority_flags(df)
    df["_nonnull"] = df[value_cols].notna().sum(axis=1) if value_cols else 0
    df = df.sort_values(
        ["_p2017", "_p2015", "_p2013", "_p2011", "_nonnull"],
        ascending=False
    )
    df = df.drop_duplicates(subset=[key], keep="first")
    return df.drop(columns=[c for c in df.columns if c.startswith("_p") or c == "_nonnull"])

def first_nonnull(s):
    s = s.dropna()
    return s.iloc[0] if len(s) else np.nan

def clean_missing_codes(df):
    """Archived notebook note for 04_wave2017_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    miss_maps = {
        "g1016":  [-9, -7],
        "g1016b": [-9, -7],   # Original notebook comment normalized for the public code archive.
        "e1022":  [-9, -7],
        "e1021":  [-9, -7],   # Original notebook comment normalized for the public code archive.
    }
    for col, bads in miss_maps.items():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").replace(bads, np.nan)
    return df

# =============================================================================
hh     = read_stata_safe(os.path.join(BASE, FN_HH))
ind    = read_stata_safe(os.path.join(BASE, FN_IND))
master = read_stata_safe(os.path.join(BASE, FN_MASTER))
geo    = read_stata_safe(os.path.join(BASE, FN_GEO))

hh, ind, master, geo = map(drop_duplicate_columns, [hh, ind, master, geo])

# =============================================================================
for d in (hh, ind, master, geo):
    d["hh_key"] = make_hh_key(d)

# Original notebook comment normalized for the public code archive.
hh = dedupe_right_by_priority(
    hh,
    "hh_key",
    value_cols=[c for c in ["e1001", "e1020", "g1016", "g1016b", "e1022", "e1021"] if c in hh.columns]
)

# =============================================================================
birth = None
if "a2005" in ind.columns:
    birth = to_int(ind["a2005"])
if "a1114" in ind.columns:
    b2 = to_int(ind["a1114"])
    birth = birth.fillna(b2) if birth is not None else b2
if birth is None:
    raise KeyError("IND 缺少出生年变量（未找到 a2005 或 a1114）")

ind["age"] = SURVEY_YEAR - birth
ind.loc[(ind["age"] < 0) | (ind["age"] > 120), "age"] = pd.NA

child = (
    ind.assign(child_u15=(ind["age"] <= 15).astype("Int64"))
       .groupby("hh_key", as_index=False)["child_u15"].sum()
       .rename(columns={"child_u15": "child_u15_num"})
)
child["any_child_u15"] = (child["child_u15_num"] > 0).astype("Int64")

# =============================================================================
censor_cols = [c for c in master.columns if c.startswith("censor_total_income")]
keep_cols = ["hh_key", "total_income", "weight_hh"] + (censor_cols[:1] if censor_cols else [])
master_slim = master[[c for c in keep_cols if c in master.columns]].copy()

# Original notebook comment normalized for the public code archive.
if master_slim.duplicated("hh_key").any():
    agg = {"total_income": first_nonnull}
    if "weight_hh" in master_slim.columns:
        agg["weight_hh"] = first_nonnull
    if censor_cols:
        agg[censor_cols[0]] = first_nonnull
    master_slim = (
        master_slim
        .sort_values(["total_income"], ascending=False)
        .groupby("hh_key", as_index=False)
        .agg(agg)
    )

# =============================================================================
geo_keep = [
    "hh_key", "hhid", "hhid_2011", "hhid_2013", "hhid_2015", "hhid_2017",
    "prov_CHN", "city", "county", "rural", "swgt"
]
geo = geo[[c for c in geo_keep if c in geo.columns]].copy()
geo = dedupe_right_by_priority(
    geo,
    "hh_key",
    value_cols=["prov_CHN", "city", "county", "rural", "swgt"] if "swgt" in geo.columns
               else ["prov_CHN", "city", "county", "rural"]
)
if "rural" in geo.columns:
    geo["rural"] = to_int(geo["rural"])
for col in ["prov_CHN", "city", "county"]:
    if col in geo.columns:
        geo[col] = geo[col].apply(strip_str_or_na)

# =============================================================================
hh = clean_missing_codes(hh)

# =============================================================================
df = hh.merge(child,       on="hh_key", how="left", validate="one_to_one")
df = df.merge(master_slim, on="hh_key", how="left", validate="one_to_one")
df = df.merge(geo,         on="hh_key", how="left", validate="one_to_one")

# Original notebook comment normalized for the public code archive.
df["child_u15_num"] = df["child_u15_num"].fillna(0).astype("Int64")
df["any_child_u15"] = df["any_child_u15"].fillna(0).astype("Int64")

# =============================================================================
if "swgt" in df.columns:
    df["weight_out"] = pd.to_numeric(df["swgt"], errors="coerce")
elif "weight_hh" in df.columns:
    df["weight_out"] = pd.to_numeric(df["weight_hh"], errors="coerce")
else:
    df["weight_out"] = pd.NA  # Original notebook comment normalized for the public code archive.

# =============================================================================
# Original notebook comment normalized for the public code archive.
if "hhid" in df.columns:
    df["hhid_out"] = df["hhid"].astype(str)
elif "hhid" in hh.columns:
    df["hhid_out"] = hh["hhid"].astype(str)
else:
    df["hhid_out"] = df["hh_key"].astype(str)

# Original notebook comment normalized for the public code archive.
censor_col = None
for c in ["censor_total_income_imp"] + [c for c in df.columns if c.startswith("censor_total_income")]:
    if c in df.columns:
        censor_col = c
        break

select_cols = [
    "hhid_out",
    "prov_CHN", "city", "county", "rural",
    "weight_out",
    "total_income",
    *( [censor_col] if censor_col else [] ),
    "e1001", "e1020", "e1022", "e1021",  # Original notebook comment normalized for the public code archive.
    "g1016", "g1016b",
    "any_child_u15", "child_u15_num",
]
select_cols = [c for c in select_cols if c in df.columns]

out = df[select_cols].rename(columns={
    "hhid_out": "家庭ID",
    "prov_CHN": "省",
    "city": "市",
    "county": "县",
    "rural": "是否农村",
    "weight_out": "抽样权重",
    "total_income": f"家庭可支配收入（{INCOME_YEAR}年，元）",
    (censor_col or ""): "收入截尾标记（imp）",
    "e1001": "是否有教育银行贷款（原始码1/2）",
    "e1020": "是否有教育民间借款（原始码1/2）",
    "e1022": "教育民间借款尚欠金额（元）",
    "e1021": "教育民间借款总额（旧口径，元）",
    "g1016":  f"去年教育培训支出（{INCOME_YEAR}年，元）",
    "g1016b": f"去年子女教育培训支出（{INCOME_YEAR}年，元）",
    "any_child_u15": "是否有15岁及以下儿童",
    "child_u15_num": "15岁及以下儿童数量",
})
if "" in out.columns:  # Original notebook comment normalized for the public code archive.
    out = out.drop(columns=[""])

# =============================================================================
out_path = os.path.join(BASE, OUT_XLSX)
out.to_excel(out_path, index=False)
print("[INFO] Notebook progress message.")
print("[INFO] Notebook progress message.", len(out))
print(out.head(5))


# ------------------------------------------------------------------------------
# Notebook cell 9
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 04_wave2017_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import numpy as np
import pandas as pd

# =============================================================================
BASE = r"E:\project_flood_impact_assessment\教育数据\CHFS_center\2017"
FN_HH     = "chfs2017_hh_202206.dta"
FN_IND    = "chfs2017_ind_202206.dta"
FN_MASTER = "chfs2017_master_202206.dta"
FN_GEO    = "区县码2017.dta"

OUT_XLSX  = "CHFS2017_教育与收入_户级.xlsx"
SURVEY_YEAR = 2017
INCOME_YEAR = 2016

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
def read_stata_safe(path):
    try:
        return pd.read_stata(path, convert_categoricals=False)
    except Exception:
        return pd.read_stata(path, convert_categoricals=True)

def drop_duplicate_columns(df, keep="first"):
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated(keep=keep)]
    return df

def to_int(x):
    return pd.to_numeric(x, errors="coerce").astype("Int64")

def strip_str_or_na(s):
    if pd.isna(s):
        return pd.NA
    s2 = str(s).strip()
    return s2 if s2 else pd.NA

def make_hh_key(df):
    alias = {
        "hhid_2017": ["hhid_2017"],
        "hhid_2015": ["hhid_2015"],
        "hhid_2013": ["hhid_2013"],
        "hhid_2011": ["hhid_2011", "dhhid_2011"],
        "hhid":      ["hhid"],
    }
    vals = {}
    for std, cands in alias.items():
        for c in cands:
            if c in df.columns:
                vals[std] = df[c].astype(str)
                break
        else:
            vals[std] = pd.Series(pd.NA, index=df.index)
    key = vals["hhid_2017"]
    for lvl in ["hhid_2015", "hhid_2013", "hhid_2011", "hhid"]:
        key = key.fillna(vals[lvl])
    return key.where(~key.astype(str).str.lower().isin({"nan"}), pd.NA)

def add_priority_flags(df):
    df = df.copy()
    for col in ["hhid_2017", "hhid_2015", "hhid_2013", "hhid_2011", "dhhid_2011"]:
        if col not in df.columns:
            df[col] = pd.NA
    df["_p2017"] = df["hhid_2017"].notna().astype(int)
    df["_p2015"] = df["hhid_2015"].notna().astype(int)
    df["_p2013"] = df["hhid_2013"].notna().astype(int)
    df["_p2011"] = df["hhid_2011"].fillna(df["dhhid_2011"]).notna().astype(int)
    return df

def dedupe_right_by_priority(df, key, value_cols=None):
    if value_cols is None:
        value_cols = []
    df = add_priority_flags(df)
    df["_nonnull"] = df[value_cols].notna().sum(axis=1) if value_cols else 0
    df = df.sort_values(
        ["_p2017", "_p2015", "_p2013", "_p2011", "_nonnull"],
        ascending=False
    )
    df = df.drop_duplicates(subset=[key], keep="first")
    return df.drop(columns=[c for c in df.columns if c.startswith("_p") or c == "_nonnull"])

def first_nonnull(s):
    s = s.dropna()
    return s.iloc[0] if len(s) else np.nan

def clean_missing_codes(df):
    """Archived notebook note for 04_wave2017_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    miss_maps = {
        "g1016":  [-9, -7],
        "g1016b": [-9, -7],
        "e1022":  [-9, -7],
        "e1021":  [-9, -7],
    }
    for col, bads in miss_maps.items():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").replace(bads, np.nan)
    return df

# =============================================================================
hh     = read_stata_safe(os.path.join(BASE, FN_HH))
ind    = read_stata_safe(os.path.join(BASE, FN_IND))
master = read_stata_safe(os.path.join(BASE, FN_MASTER))
geo    = read_stata_safe(os.path.join(BASE, FN_GEO))

hh, ind, master, geo = map(drop_duplicate_columns, [hh, ind, master, geo])

# =============================================================================
for d in (hh, ind, master, geo):
    d["hh_key"] = make_hh_key(d)

# Original notebook comment normalized for the public code archive.
hh = dedupe_right_by_priority(
    hh,
    "hh_key",
    value_cols=[c for c in ["e1001", "e1020", "g1016", "g1016b", "e1022", "e1021"] if c in hh.columns]
)

# =============================================================================
# Original notebook comment normalized for the public code archive.
birth = None
if "a2005" in ind.columns:
    birth = to_int(ind["a2005"])
if "a1114" in ind.columns:
    b2 = to_int(ind["a1114"])
    birth = birth.fillna(b2) if birth is not None else b2
if birth is None:
    raise KeyError("IND 缺少出生年变量（未找到 a2005 或 a1114）")

ind["birth"] = birth
ind["age"] = SURVEY_YEAR - ind["birth"]
# Original notebook comment normalized for the public code archive.
ind.loc[(ind["age"] < 0) | (ind["age"] > 120), ["age", "birth"]] = pd.NA

# Original notebook comment normalized for the public code archive.
child = (
    ind.assign(child_u15=(ind["age"] <= 15).astype("Int64"))
       .groupby("hh_key", as_index=False)["child_u15"].sum()
       .rename(columns={"child_u15": "child_u15_num"})
)
child["any_child_u15"] = (child["child_u15_num"] > 0).astype("Int64")

# Original notebook comment normalized for the public code archive.
birth_agg = (
    ind.groupby("hh_key")["birth"]
       .agg(hh_birth_min="min",
            hh_birth_max="max",
            hh_birth_mean="mean")
       .reset_index()
)

# Original notebook comment normalized for the public code archive.
if "a2012" in ind.columns:
    ind["edu_code"] = to_int(ind["a2012"])
    ind.loc[~ind["edu_code"].between(1, 9), "edu_code"] = pd.NA
else:
    ind["edu_code"] = pd.Series(pd.NA, index=ind.index, dtype="Int64")

edu_agg = (
    ind.groupby("hh_key")["edu_code"]
       .max()
       .rename("hh_max_edu_code")
       .reset_index()
)

# =============================================================================
censor_cols = [c for c in master.columns if c.startswith("censor_total_income")]
keep_cols = ["hh_key", "total_income", "weight_hh"] + (censor_cols[:1] if censor_cols else [])
master_slim = master[[c for c in keep_cols if c in master.columns]].copy()

# Original notebook comment normalized for the public code archive.
if master_slim.duplicated("hh_key").any():
    agg = {"total_income": first_nonnull}
    if "weight_hh" in master_slim.columns:
        agg["weight_hh"] = first_nonnull
    if censor_cols:
        agg[censor_cols[0]] = first_nonnull
    master_slim = (
        master_slim
        .sort_values(["total_income"], ascending=False)
        .groupby("hh_key", as_index=False)
        .agg(agg)
    )

# =============================================================================
geo_keep = [
    "hh_key", "hhid", "hhid_2011", "hhid_2013", "hhid_2015", "hhid_2017",
    "prov_CHN", "city", "county", "rural", "swgt"
]
geo = geo[[c for c in geo_keep if c in geo.columns]].copy()
geo = dedupe_right_by_priority(
    geo,
    "hh_key",
    value_cols=["prov_CHN", "city", "county", "rural", "swgt"] if "swgt" in geo.columns
               else ["prov_CHN", "city", "county", "rural"]
)
if "rural" in geo.columns:
    geo["rural"] = to_int(geo["rural"])
for col in ["prov_CHN", "city", "county"]:
    if col in geo.columns:
        geo[col] = geo[col].apply(strip_str_or_na)

# =============================================================================
hh = clean_missing_codes(hh)

# =============================================================================
df = hh.merge(child,       on="hh_key", how="left", validate="one_to_one")
df = df.merge(birth_agg,   on="hh_key", how="left")
df = df.merge(edu_agg,     on="hh_key", how="left")
df = df.merge(master_slim, on="hh_key", how="left", validate="one_to_one")
df = df.merge(geo,         on="hh_key", how="left", validate="one_to_one")

# Original notebook comment normalized for the public code archive.
df["hh_max_edu_label"] = df["hh_max_edu_code"].map(EDU_LABEL_MAP)

# Original notebook comment normalized for the public code archive.
df["child_u15_num"] = df["child_u15_num"].fillna(0).astype("Int64")
df["any_child_u15"] = df["any_child_u15"].fillna(0).astype("Int64")

# =============================================================================
if "swgt" in df.columns:
    df["weight_out"] = pd.to_numeric(df["swgt"], errors="coerce")
elif "weight_hh" in df.columns:
    df["weight_out"] = pd.to_numeric(df["weight_hh"], errors="coerce")
else:
    df["weight_out"] = pd.NA  # Original notebook comment normalized for the public code archive.

# =============================================================================
# Original notebook comment normalized for the public code archive.
if "hhid" in df.columns:
    df["hhid_out"] = df["hhid"].astype(str)
elif "hhid" in hh.columns:
    df["hhid_out"] = hh["hhid"].astype(str)
else:
    df["hhid_out"] = df["hh_key"].astype(str)

# Original notebook comment normalized for the public code archive.
censor_col = None
for c in ["censor_total_income_imp"] + [c for c in df.columns if c.startswith("censor_total_income")]:
    if c in df.columns:
        censor_col = c
        break

select_cols = [
    "hhid_out",
    "prov_CHN", "city", "county", "rural",
    "weight_out",
    "total_income",
    *( [censor_col] if censor_col else [] ),
    "e1001", "e1020", "e1022", "e1021",
    "g1016", "g1016b",
    "any_child_u15", "child_u15_num",
    "hh_birth_min", "hh_birth_max", "hh_birth_mean",
    "hh_max_edu_code", "hh_max_edu_label",
]
select_cols = [c for c in select_cols if c in df.columns]

out = df[select_cols].rename(columns={
    "hhid_out": "家庭ID",
    "prov_CHN": "省",
    "city": "市",
    "county": "县",
    "rural": "是否农村",
    "weight_out": "抽样权重",
    "total_income": f"家庭可支配收入（{INCOME_YEAR}年，元）",
    (censor_col or ""): "收入截尾标记（imp）",
    "e1001": "是否有教育银行贷款（原始码1/2）",
    "e1020": "是否有教育民间借款（原始码1/2）",
    "e1022": "教育民间借款尚欠金额（元）",
    "e1021": "教育民间借款总额（旧口径，元）",
    "g1016":  f"去年教育培训支出（{INCOME_YEAR}年，元）",
    "g1016b": f"去年子女教育培训支出（{INCOME_YEAR}年，元）",
    "any_child_u15": "是否有15岁及以下儿童",
    "child_u15_num": "15岁及以下儿童数量",
    "hh_birth_min":  "最年长成员出生年",
    "hh_birth_max":  "最年轻成员出生年",
    "hh_birth_mean": "家庭成员平均出生年",
    "hh_max_edu_code":  "家庭最高文化程度（代码）",
    "hh_max_edu_label": "家庭最高文化程度",
})
if "" in out.columns:  # Original notebook comment normalized for the public code archive.
    out = out.drop(columns=[""])

# =============================================================================
out_path = os.path.join(BASE, OUT_XLSX)
out.to_excel(out_path, index=False)
print("[INFO] Notebook progress message.")
print("[INFO] Notebook progress message.", len(out))
print(out.head(5))
