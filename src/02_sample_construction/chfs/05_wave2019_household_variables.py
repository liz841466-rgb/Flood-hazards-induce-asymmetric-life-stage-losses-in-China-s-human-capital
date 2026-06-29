#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 05_wave2019_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 2
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 05_wave2019_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import numpy as np
import pandas as pd

# =============================================================================
BASE = r"E:\project_flood_impact_assessment\教育数据\CHFS_center\2019"
FN_HH     = "chfs2019_hh_202112.dta"
FN_IND    = "chfs2019_ind_202112.dta"
FN_MASTER = "chfs2019_master_202112.dta"
FN_GEO    = "区县码2019.dta"

OUT_XLSX  = "CHFS2019_教育与收入_户级.xlsx"
SURVEY_YEAR = 2019
INCOME_YEAR = 2018  # CHFS/CFHS processing note.

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

def to_int(series):
    return pd.to_numeric(series, errors="coerce").astype("Int64")

def strip_str_or_na(s):
    if pd.isna(s): return pd.NA
    s2 = str(s).strip()
    return s2 if s2 else pd.NA

def make_hh_key(df):
    """Archived notebook note for 05_wave2019_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    alias = {
        "hhid_2019": ["hhid_2019"],
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

    key = vals["hhid_2019"]
    for lvl in ["hhid_2017","hhid_2015","hhid_2013","hhid_2011","hhid"]:
        key = key.fillna(vals[lvl])
    key = key.where(~key.astype(str).str.lower().isin({"nan"}), other=pd.NA)
    return key

def add_priority_flags(df):
    """Archived notebook note for 05_wave2019_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()
    for col in ["hhid_2019","hhid_2017","hhid_2015","hhid_2013","hhid_2011","dhhid_2011"]:
        if col not in df.columns: df[col] = pd.NA
    df["_p2019"] = df["hhid_2019"].notna().astype(int)
    df["_p2017"] = df["hhid_2017"].notna().astype(int)
    df["_p2015"] = df["hhid_2015"].notna().astype(int)
    df["_p2013"] = df["hhid_2013"].notna().astype(int)
    df["_p2011"] = df["hhid_2011"].fillna(df["dhhid_2011"]).notna().astype(int)
    return df

def dedupe_right_by_priority(df, key, value_cols=None):
    """Archived notebook note for 05_wave2019_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if value_cols is None: value_cols = []
    df = add_priority_flags(df)
    df["_nonnull"] = df[value_cols].notna().sum(axis=1) if value_cols else 0
    df = df.sort_values(["_p2019","_p2017","_p2015","_p2013","_p2011","_nonnull"], ascending=False)
    df = df.drop_duplicates(subset=[key], keep="first")
    return df.drop(columns=[c for c in df.columns if c.startswith("_p") or c=="_nonnull"])

def first_nonnull(s):
    s = s.dropna()
    return s.iloc[0] if len(s) else np.nan

def clean_missing_codes(df):
    """Archived notebook note for 05_wave2019_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    miss_maps = {
        "g1016":  [-9, -7],
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
hh = dedupe_right_by_priority(hh, "hh_key", value_cols=[c for c in ["e1001a","g1016"] if c in hh.columns])

# =============================================================================
birth = None
if "a2005" in ind.columns: birth = to_int(ind["a2005"])
if "a1114" in ind.columns:
    b2 = to_int(ind["a1114"])
    birth = birth.fillna(b2) if birth is not None else b2
if birth is None: raise KeyError("IND 缺少出生年变量（未找到 a2005 或 a1114）")

ind["age"] = SURVEY_YEAR - birth
ind.loc[(ind["age"] < 0) | (ind["age"] > 120), "age"] = pd.NA
child = (ind.assign(child_u15=(ind["age"] <= 15).astype("Int64"))
           .groupby("hh_key", as_index=False)["child_u15"].sum()
           .rename(columns={"child_u15":"child_u15_num"}))
child["any_child_u15"] = (child["child_u15_num"] > 0).astype("Int64")

# =============================================================================
# Original notebook comment normalized for the public code archive.
censor_cols = [c for c in master.columns if c.startswith("censor_total_income")]
keep_cols = ["hh_key","hhid","total_income","weight_hh","rural","educ_debt"] + (censor_cols[:1] if censor_cols else [])
master_slim = master[[c for c in keep_cols if c in master.columns]].copy()

if master_slim.duplicated("hh_key").any():
    agg = {
        "hhid": first_nonnull,
        "total_income": first_nonnull,
        "weight_hh": first_nonnull,
        "rural": first_nonnull,
        "educ_debt": first_nonnull,
    }
    if censor_cols: agg[censor_cols[0]] = first_nonnull
    master_slim = (master_slim
                   .sort_values(["total_income"], ascending=False)
                   .groupby("hh_key", as_index=False).agg(agg))

# =============================================================================
# County-level processing note.
if "country" in geo.columns and "county" not in geo.columns:
    geo = geo.rename(columns={"country": "county"})
# Original notebook comment normalized for the public code archive.
if "prov_CHN" not in geo.columns and "prov" in geo.columns:
    geo = geo.rename(columns={"prov": "prov_CHN"})

geo_keep = ["hh_key","hhid","hhid_2019","hhid_2017","hhid_2015","hhid_2013","hhid_2011","dhhid_2011",
            "prov_CHN","city","county"]
geo = geo[[c for c in geo_keep if c in geo.columns]].copy()
geo = dedupe_right_by_priority(geo, "hh_key", value_cols=["prov_CHN","city","county"])

for col in ["prov_CHN","city","county"]:
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
# =============================================================================
if "hhid" in df.columns and df["hhid"].notna().any():
    df["hhid_out"] = df["hhid"].astype(str)
elif "hhid" in geo.columns and geo["hhid"].notna().any():
    df["hhid_out"] = df["hhid"].astype(str)
elif "hhid_2019" in df.columns and df["hhid_2019"].notna().any():
    df["hhid_out"] = df["hhid_2019"].astype(str)
elif "hhid" in hh.columns:
    df["hhid_out"] = hh["hhid"].astype(str)
else:
    df["hhid_out"] = df["hh_key"].astype(str)

# Original notebook comment normalized for the public code archive.
df["weight_out"] = pd.to_numeric(df.get("weight_hh"), errors="coerce")
df["rural_out"]  = to_int(df.get("rural")) if "rural" in df.columns else pd.NA

# Original notebook comment normalized for the public code archive.
censor_col = None
for c in ["censor_total_income_imp"] + [c for c in df.columns if c.startswith("censor_total_income")]:
    if c in df.columns:
        censor_col = c
        break

# =============================================================================
select_cols = [
    "hhid_out",
    "prov_CHN","city","county",
    "rural_out",
    "weight_out",
    "total_income",
    *( [censor_col] if censor_col else [] ),
    "e1001a","educ_debt","g1016",
    "any_child_u15","child_u15_num",
]
select_cols = [c for c in select_cols if c in df.columns]

out = df[select_cols].rename(columns={
    "hhid_out": "家庭ID",
    "prov_CHN": "省",
    "city": "市",
    "county": "县",
    "rural_out": "是否农村",                         # Original notebook comment normalized for the public code archive.
    "weight_out": "抽样权重",
    "total_income": f"家庭可支配收入（{INCOME_YEAR}年，元）",
    (censor_col or ""): "收入截尾标记（imp）",
    "e1001a": "是否有教育负债（原始码1/2）",
    "educ_debt": "教育负债余额（元）",
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
"""Archived notebook note for 05_wave2019_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import numpy as np
import pandas as pd

# =============================================================================
ROOT = r"E:\project_flood_impact_assessment\教育数据\CHFS_center"
IN_XLSX  = os.path.join(ROOT, "2019", "CHFS2019_教育与收入_户级.xlsx")   # Original notebook comment normalized for the public code archive.
OUT_XLSX = os.path.join(ROOT, "2019", "CHFS2019_教育与收入_户级_补齐省市县.xlsx")

GEO_FILES = {
    2019: os.path.join(ROOT, "2019", "区县码2019.dta"),
    2017: os.path.join(ROOT, "2017", "区县码2017.dta"),
    2015: os.path.join(ROOT, "2015", "区县码2015.dta"),
    2013: os.path.join(ROOT, "2013", "区县码2013.dta"),
    2011: os.path.join(ROOT, "2011", "区县码2011.dta"),
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

def strip_str_or_na(s):
    if pd.isna(s): return pd.NA
    s2 = str(s).strip()
    return s2 if s2 else pd.NA

def build_geo_map(path, year):
    """Archived notebook note for 05_wave2019_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    g = read_stata_safe(path)
    g = drop_duplicate_columns(g)

    # County-level processing note.
    if "country" in g.columns and "county" not in g.columns:
        g = g.rename(columns={"country": "county"})
    prov_col = "prov_CHN" if "prov_CHN" in g.columns else ("prov" if "prov" in g.columns else None)

    # Excel output note.
    id_cols = [c for c in ["hhid","hhid_2019","hhid_2017","hhid_2015","hhid_2013","hhid_2011","dhhid_2011"] if c in g.columns]
    if not id_cols:
        return pd.DataFrame(columns=["家庭ID","省","市","县","来源年份"])

    cols_geo = [c for c in [prov_col,"city","county"] if c and c in g.columns]
    frames = []
    for ic in id_cols:
        tmp = g[[ic] + cols_geo].copy()
        rename_map = {ic:"家庭ID"}
        if prov_col in tmp.columns: rename_map[prov_col] = "省"
        if "city" in tmp.columns:   rename_map["city"]   = "市"
        if "county" in tmp.columns: rename_map["county"] = "县"
        tmp = tmp.rename(columns=rename_map)
        # Original notebook comment normalized for the public code archive.
        tmp["家庭ID"] = tmp["家庭ID"].astype(str).str.strip().replace({"nan": np.nan, "NaN": np.nan})
        # Original notebook comment normalized for the public code archive.
        for c in ["省","市","县"]:
            if c in tmp.columns:
                tmp[c] = tmp[c].apply(strip_str_or_na)
        tmp["来源年份"] = int(year)
        frames.append(tmp)

    out = pd.concat(frames, ignore_index=True).dropna(subset=["家庭ID"])
    # Original notebook comment normalized for the public code archive.
    out = out.drop_duplicates(subset=["家庭ID"], keep="first")
    # Original notebook comment normalized for the public code archive.
    for c in ["省","市","县"]:
        if c not in out.columns: out[c] = pd.NA
    return out[["家庭ID","省","市","县","来源年份"]]

# =============================================================================
df = pd.read_excel(IN_XLSX)
if "家庭ID" not in df.columns:
    raise KeyError("输入Excel缺少列：家庭ID")

# Original notebook comment normalized for the public code archive.
df["家庭ID"] = df["家庭ID"].astype(str).str.strip()
for c in ["省","市","县"]:
    if c not in df.columns:
        df[c] = pd.NA

print("[INFO] Notebook progress message.", {c: int(df[c].isna().sum()) for c in ["[INFO] Notebook progress message.","[INFO] Notebook progress message.","[INFO] Notebook progress message."]})

# =============================================================================
maps = []
for y in [2019, 2017, 2015, 2013, 2011]:   # Original notebook comment normalized for the public code archive.
    mp = build_geo_map(GEO_FILES[y], y)
    maps.append(mp)

geo_union = pd.concat(maps, ignore_index=True)
# Original notebook comment normalized for the public code archive.
geo_union = geo_union.sort_values(["来源年份"], ascending=False)\
                     .drop_duplicates(subset=["家庭ID"], keep="first")

# =============================================================================
df = df.merge(geo_union.rename(columns={"省":"省_补","市":"市_补","县":"县_补"}),
              on="家庭ID", how="left")

for c in ["省","市","县"]:
    fillc = f"{c}_补"
    if fillc in df.columns:
        df[c] = df[c].where(df[c].notna(), df[fillc])
        df = df.drop(columns=[fillc])

print("[INFO] Notebook progress message.", {c: int(df[c].isna().sum()) for c in ["[INFO] Notebook progress message.","[INFO] Notebook progress message.","[INFO] Notebook progress message."]})

# =============================================================================
df.to_excel(OUT_XLSX, index=False)
print("[INFO] Notebook progress message.")


# ------------------------------------------------------------------------------
# Notebook cell 9
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 05_wave2019_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import numpy as np
import pandas as pd

# =============================================================================
BASE = r"E:\project_flood_impact_assessment\教育数据\CHFS_center\2019"
FN_HH     = "chfs2019_hh_202112.dta"
FN_IND    = "chfs2019_ind_202112.dta"
FN_MASTER = "chfs2019_master_202112.dta"
FN_GEO    = "区县码2019.dta"

OUT_XLSX  = "CHFS2019_教育与收入_户级.xlsx"
SURVEY_YEAR = 2019
INCOME_YEAR = 2018  # CHFS/CFHS processing note.

# =============================================================================
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

def to_int(series):
    return pd.to_numeric(series, errors="coerce").astype("Int64")

def strip_str_or_na(s):
    if pd.isna(s): return pd.NA
    s2 = str(s).strip()
    return s2 if s2 else pd.NA

def make_hh_key(df):
    """Archived notebook note for 05_wave2019_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    alias = {
        "hhid_2019": ["hhid_2019"],
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

    key = vals["hhid_2019"]
    for lvl in ["hhid_2017","hhid_2015","hhid_2013","hhid_2011","hhid"]:
        key = key.fillna(vals[lvl])
    key = key.where(~key.astype(str).str.lower().isin({"nan"}), other=pd.NA)
    return key

def add_priority_flags(df):
    """Archived notebook note for 05_wave2019_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()
    for col in ["hhid_2019","hhid_2017","hhid_2015","hhid_2013","hhid_2011","dhhid_2011"]:
        if col not in df.columns: df[col] = pd.NA
    df["_p2019"] = df["hhid_2019"].notna().astype(int)
    df["_p2017"] = df["hhid_2017"].notna().astype(int)
    df["_p2015"] = df["hhid_2015"].notna().astype(int)
    df["_p2013"] = df["hhid_2013"].notna().astype(int)
    df["_p2011"] = df["hhid_2011"].fillna(df["dhhid_2011"]).notna().astype(int)
    return df

def dedupe_right_by_priority(df, key, value_cols=None):
    """Archived notebook note for 05_wave2019_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if value_cols is None: value_cols = []
    df = add_priority_flags(df)
    df["_nonnull"] = df[value_cols].notna().sum(axis=1) if value_cols else 0
    df = df.sort_values(["_p2019","_p2017","_p2015","_p2013","_p2011","_nonnull"], ascending=False)
    df = df.drop_duplicates(subset=[key], keep="first")
    return df.drop(columns=[c for c in df.columns if c.startswith("_p") or c=="_nonnull"])

def first_nonnull(s):
    s = s.dropna()
    return s.iloc[0] if len(s) else np.nan

def clean_missing_codes(df):
    """Archived notebook note for 05_wave2019_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    miss_maps = {
        "g1016":  [-9, -7],
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
hh = dedupe_right_by_priority(hh, "hh_key", value_cols=[c for c in ["e1001a","g1016"] if c in hh.columns])

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
ind["age"]   = SURVEY_YEAR - ind["birth"]
# Original notebook comment normalized for the public code archive.
ind.loc[(ind["age"] < 0) | (ind["age"] > 120), ["age", "birth"]] = pd.NA

# Original notebook comment normalized for the public code archive.
child = (
    ind.assign(child_u15=(ind["age"] <= 15).astype("Int64"))
       .groupby("hh_key", as_index=False)["child_u15"].sum()
       .rename(columns={"child_u15":"child_u15_num"})
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
# Original notebook comment normalized for the public code archive.
censor_cols = [c for c in master.columns if c.startswith("censor_total_income")]
keep_cols = ["hh_key","hhid","total_income","weight_hh","rural","educ_debt"] + (censor_cols[:1] if censor_cols else [])
master_slim = master[[c for c in keep_cols if c in master.columns]].copy()

if master_slim.duplicated("hh_key").any():
    agg = {
        "hhid": first_nonnull,
        "total_income": first_nonnull,
        "weight_hh": first_nonnull,
        "rural": first_nonnull,
        "educ_debt": first_nonnull,
    }
    if censor_cols: agg[censor_cols[0]] = first_nonnull
    master_slim = (master_slim
                   .sort_values(["total_income"], ascending=False)
                   .groupby("hh_key", as_index=False).agg(agg))

# =============================================================================
# County-level processing note.
if "country" in geo.columns and "county" not in geo.columns:
    geo = geo.rename(columns={"country": "county"})
# Original notebook comment normalized for the public code archive.
if "prov_CHN" not in geo.columns and "prov" in geo.columns:
    geo = geo.rename(columns={"prov": "prov_CHN"})

geo_keep = ["hh_key","hhid","hhid_2019","hhid_2017","hhid_2015","hhid_2013","hhid_2011","dhhid_2011",
            "prov_CHN","city","county"]
geo = geo[[c for c in geo_keep if c in geo.columns]].copy()
geo = dedupe_right_by_priority(geo, "hh_key", value_cols=["prov_CHN","city","county"])

for col in ["prov_CHN","city","county"]:
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
# =============================================================================
if "hhid" in df.columns and df["hhid"].notna().any():
    df["hhid_out"] = df["hhid"].astype(str)
elif "hhid" in geo.columns and geo["hhid"].notna().any():
    df["hhid_out"] = df["hhid"].astype(str)
elif "hhid_2019" in df.columns and df["hhid_2019"].notna().any():
    df["hhid_out"] = df["hhid_2019"].astype(str)
elif "hhid" in hh.columns:
    df["hhid_out"] = hh["hhid"].astype(str)
else:
    df["hhid_out"] = df["hh_key"].astype(str)

# Original notebook comment normalized for the public code archive.
df["weight_out"] = pd.to_numeric(df.get("weight_hh"), errors="coerce")
df["rural_out"]  = to_int(df.get("rural")) if "rural" in df.columns else pd.NA

# Original notebook comment normalized for the public code archive.
censor_col = None
for c in ["censor_total_income_imp"] + [c for c in df.columns if c.startswith("censor_total_income")]:
    if c in df.columns:
        censor_col = c
        break

# =============================================================================
select_cols = [
    "hhid_out",
    "prov_CHN","city","county",
    "rural_out",
    "weight_out",
    "total_income",
    *( [censor_col] if censor_col else [] ),
    "e1001a","educ_debt","g1016",
    "any_child_u15","child_u15_num",
    "hh_birth_min","hh_birth_max","hh_birth_mean",
    "hh_max_edu_code","hh_max_edu_label",
]
select_cols = [c for c in select_cols if c in df.columns]

out = df[select_cols].rename(columns={
    "hhid_out": "家庭ID",
    "prov_CHN": "省",
    "city": "市",
    "county": "县",
    "rural_out": "是否农村",                         # Original notebook comment normalized for the public code archive.
    "weight_out": "抽样权重",
    "total_income": f"家庭可支配收入（{INCOME_YEAR}年，元）",
    (censor_col or ""): "收入截尾标记（imp）",
    "e1001a": "是否有教育负债（原始码1/2）",
    "educ_debt": "教育负债余额（元）",
    "g1016": f"去年教育培训支出（{INCOME_YEAR}年，元）",
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


# ------------------------------------------------------------------------------
# Notebook cell 11
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 05_wave2019_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import numpy as np
import pandas as pd

# =============================================================================
ROOT = r"E:\project_flood_impact_assessment\教育数据\CHFS_center"
IN_XLSX  = os.path.join(ROOT, "2019", "CHFS2019_教育与收入_户级.xlsx")   # Original notebook comment normalized for the public code archive.
OUT_XLSX = os.path.join(ROOT, "2019", "CHFS2019_教育与收入_户级_补齐省市县.xlsx")

GEO_FILES = {
    2019: os.path.join(ROOT, "2019", "区县码2019.dta"),
    2017: os.path.join(ROOT, "2017", "区县码2017.dta"),
    2015: os.path.join(ROOT, "2015", "区县码2015.dta"),
    2013: os.path.join(ROOT, "2013", "区县码2013.dta"),
    2011: os.path.join(ROOT, "2011", "区县码2011.dta"),
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

def strip_str_or_na(s):
    if pd.isna(s): return pd.NA
    s2 = str(s).strip()
    return s2 if s2 else pd.NA

def build_geo_map(path, year):
    """Archived notebook note for 05_wave2019_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    g = read_stata_safe(path)
    g = drop_duplicate_columns(g)

    # County-level processing note.
    if "country" in g.columns and "county" not in g.columns:
        g = g.rename(columns={"country": "county"})
    prov_col = "prov_CHN" if "prov_CHN" in g.columns else ("prov" if "prov" in g.columns else None)

    # Excel output note.
    id_cols = [c for c in ["hhid","hhid_2019","hhid_2017","hhid_2015","hhid_2013","hhid_2011","dhhid_2011"]
               if c in g.columns]
    if not id_cols:
        return pd.DataFrame(columns=["家庭ID","省","市","县","来源年份"])

    cols_geo = [c for c in [prov_col,"city","county"] if c and c in g.columns]
    frames = []
    for ic in id_cols:
        tmp = g[[ic] + cols_geo].copy()
        rename_map = {ic:"家庭ID"}
        if prov_col in tmp.columns: rename_map[prov_col] = "省"
        if "city"   in tmp.columns: rename_map["city"]   = "市"
        if "county" in tmp.columns: rename_map["county"] = "县"
        tmp = tmp.rename(columns=rename_map)

        # Original notebook comment normalized for the public code archive.
        tmp["家庭ID"] = tmp["家庭ID"].astype(str).str.strip().replace({"nan": np.nan, "NaN": np.nan})

        # Original notebook comment normalized for the public code archive.
        for c in ["省","市","县"]:
            if c in tmp.columns:
                tmp[c] = tmp[c].apply(strip_str_or_na)

        tmp["来源年份"] = int(year)
        frames.append(tmp)

    out = pd.concat(frames, ignore_index=True).dropna(subset=["家庭ID"])
    # Original notebook comment normalized for the public code archive.
    out = out.drop_duplicates(subset=["家庭ID"], keep="first")

    # Original notebook comment normalized for the public code archive.
    for c in ["省","市","县"]:
        if c not in out.columns: out[c] = pd.NA

    return out[["家庭ID","省","市","县","来源年份"]]

# =============================================================================
df = pd.read_excel(IN_XLSX)
if "家庭ID" not in df.columns:
    raise KeyError("输入Excel缺少列：家庭ID")

# Original notebook comment normalized for the public code archive.
df["家庭ID"] = df["家庭ID"].astype(str).str.strip()
for c in ["省","市","县"]:
    if c not in df.columns:
        df[c] = pd.NA

print("[INFO] Notebook progress message.", {c: int(df[c].isna().sum()) for c in ["[INFO] Notebook progress message.","[INFO] Notebook progress message.","[INFO] Notebook progress message."]})

# =============================================================================
maps = []
for y in [2019, 2017, 2015, 2013, 2011]:   # Original notebook comment normalized for the public code archive.
    mp = build_geo_map(GEO_FILES[y], y)
    maps.append(mp)

geo_union = pd.concat(maps, ignore_index=True)
# Original notebook comment normalized for the public code archive.
geo_union = (geo_union
             .sort_values(["来源年份"], ascending=False)
             .drop_duplicates(subset=["家庭ID"], keep="first"))

# =============================================================================
df = df.merge(
    geo_union.rename(columns={"省":"省_补","市":"市_补","县":"县_补"}),
    on="家庭ID", how="left"
)

for c in ["省","市","县"]:
    fillc = f"{c}_补"
    if fillc in df.columns:
        df[c] = df[c].where(df[c].notna(), df[fillc])
        df = df.drop(columns=[fillc])

print("[INFO] Notebook progress message.", {c: int(df[c].isna().sum()) for c in ["[INFO] Notebook progress message.","[INFO] Notebook progress message.","[INFO] Notebook progress message."]})

# =============================================================================
df.to_excel(OUT_XLSX, index=False)
print("[INFO] Notebook progress message.")
