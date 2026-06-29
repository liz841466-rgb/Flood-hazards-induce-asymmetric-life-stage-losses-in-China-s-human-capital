#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 02_wave2013_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 4
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 02_wave2013_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import numpy as np
import pandas as pd

# =============================================================================
BASE = r"E:\project_flood_impact_assessment\教育数据\CHFS_center\2013"
FN_HH  = "chfs2013_hh_20191120_version14.dta"
FN_IND = "chfs2013_ind_20191120_version14.dta"
FN_GEO = "区县码2013.dta"
OUT_XLSX = "CHFS2013_教育与收入_户级.xlsx"

SURVEY_YEAR = 2013
INCOME_YEAR = 2012

# =============================================================================
def read_stata_safe(p):
    try: return pd.read_stata(p, convert_categoricals=False)
    except Exception: return pd.read_stata(p, convert_categoricals=True)

def drop_dup_cols(df, keep="first"):
    return df.loc[:, ~df.columns.duplicated(keep=keep)]

def to_int(x):
    return pd.to_numeric(x, errors="coerce").astype("Int64")

def strip_na(s):
    if pd.isna(s): return pd.NA
    s = str(s).strip()
    return s if s else pd.NA

def normalize_id(x):
    if pd.isna(x): return pd.NA
    s = str(x).strip()
    if s.endswith(".0"): s = s[:-2]
    return s if s else pd.NA

def map_bin(s):
    if pd.isna(s): return pd.NA
    return {1:1, 2:0, "1":1, "2":0, "是":1, "否":0, True:1, False:0}.get(s, pd.NA)

def clean_miss(df):
    for c, bads in {"g1016":[-9,-7], "e1012":[-9999], "e1021":[-9]}.items():
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").replace(bads, np.nan)
    return df

def make_panel_id_2013(d):
    """Archived notebook note for 02_wave2013_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    key = pd.Series(pd.NA, index=d.index, dtype="object")
    for c in ["hhid_2011", "hhid_2013", "hhid"]:
        if c in d.columns:
            key = key.fillna(d[c].map(normalize_id))
    return key

# =============================================================================
hh  = drop_dup_cols(read_stata_safe(os.path.join(BASE, FN_HH)))
ind = drop_dup_cols(read_stata_safe(os.path.join(BASE, FN_IND)))
geo = drop_dup_cols(read_stata_safe(os.path.join(BASE, FN_GEO)))

# =============================================================================
for d in (hh, ind, geo):
    for c in [c for c in ["hhid","hhid_2011","hhid_2013"] if c in d.columns]:
        d[c] = d[c].map(normalize_id)

hh  = hh.copy();  hh["hh_key"]  = make_panel_id_2013(hh)
ind = ind.copy(); ind["hh_key"] = make_panel_id_2013(ind)
geo = geo.copy(); geo["hh_key"] = make_panel_id_2013(geo)

# =============================================================================
if "a2005" not in ind.columns:
    raise KeyError("2013 IND 缺少 a2005（出生年）")
ind["a2005"] = to_int(ind["a2005"])
# Original notebook comment normalized for the public code archive.
ind = pd.concat([ind, pd.DataFrame({
    "age": (SURVEY_YEAR - ind["a2005"]).astype("float")
})], axis=1)
ind.loc[(ind["age"] < 0) | (ind["age"] > 120), "age"] = pd.NA

child = (ind.assign(child_u15=(ind["age"] <= 15).astype("Int64"))
           .groupby("hh_key", as_index=False)["child_u15"].sum()
           .rename(columns={"child_u15": "child_u15_num"}))
child["any_child_u15"] = (child["child_u15_num"] > 0).astype("Int64")
child = drop_dup_cols(child)

# =============================================================================
keep_geo = ["hh_key","hhid","hhid_2011","hhid_2013","prov_CHN","city","county","rural","swgt"]
geo = geo[[c for c in keep_geo if c in geo.columns]].copy()
geo = geo.drop_duplicates(subset="hh_key", keep="first")
geo["rural"] = to_int(geo.get("rural"))
geo["swgt"]  = pd.to_numeric(geo.get("swgt"), errors="coerce")
for c in ["prov_CHN","city","county"]:
    if c in geo.columns: geo[c] = geo[c].apply(strip_na)

# =============================================================================
df = hh.merge(child, on="hh_key", how="left", validate="one_to_one")
df = df.merge(geo,   on="hh_key", how="left", validate="one_to_one")

df["child_u15_num"] = df["child_u15_num"].fillna(0).astype("Int64")
df["any_child_u15"] = df["any_child_u15"].fillna(0).astype("Int64")

# =============================================================================
df = clean_miss(df)
df["是否有教育银行贷款_二元"] = df.get("e1001").apply(map_bin).astype("Int64")
df["是否为子女教育借款_二元"] = df.get("e1020").apply(map_bin).astype("Int64")

# =============================================================================
df["panel_id"] = df["hh_key"]

select = [
    "panel_id","hhid_2011","hhid_2013","hhid",
    "prov_CHN","city","county","rural","swgt",
    "total_income","censor_total_income_imp",
    "e1001","e1008","e1012","e1020","e1021","g1016",
    "any_child_u15","child_u15_num",
    "是否有教育银行贷款_二元","是否为子女教育借款_二元",
]
select = [c for c in select if c in df.columns]

out = df[select].rename(columns={
    "panel_id":"家庭ID",
    "hhid_2011":"家庭ID2011",
    "hhid_2013":"当波家庭ID（2013）",
    "hhid":"备用ID",
    "prov_CHN":"省","city":"市","county":"县",
    "rural":"是否农村","swgt":"抽样权重",
    "total_income":f"家庭可支配收入（{INCOME_YEAR}年，元）",
    "censor_total_income_imp":"收入截尾标记（imp）",
    "e1001":"是否有教育银行贷款（原始码1/2）",
    "e1008":"教育贷款年份",
    "e1012":"教育贷款总额（元）",
    "e1020":"是否为子女教育向他人/机构借款（原始码1/2）",
    "e1021":"子女教育借款总额（元）",
    "g1016":f"去年教育培训支出（{INCOME_YEAR}年，元）",
    "any_child_u15":"是否有15岁及以下儿童",
    "child_u15_num":"15岁及以下儿童数量",
})

for c in ["省","市","县"]:
    if c in out.columns: out[c] = out[c].apply(strip_na)

out.to_excel(os.path.join(BASE, OUT_XLSX), index=False)
print("[INFO] Notebook progress message.", os.path.join(BASE, OUT_XLSX))


# ------------------------------------------------------------------------------
# Notebook cell 7
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 02_wave2013_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import numpy as np
import pandas as pd

# =============================================================================
BASE = r"E:\project_flood_impact_assessment\教育数据\CHFS_center\2013"
FN_HH  = "chfs2013_hh_20191120_version14.dta"
FN_IND = "chfs2013_ind_20191120_version14.dta"
FN_GEO = "区县码2013.dta"
OUT_XLSX = "CHFS2013_教育与收入_户级.xlsx"

SURVEY_YEAR = 2013
INCOME_YEAR = 2012

# =============================================================================
def read_stata_safe(p):
    try:
        return pd.read_stata(p, convert_categoricals=False)
    except Exception:
        return pd.read_stata(p, convert_categoricals=True)

def drop_dup_cols(df, keep="first"):
    return df.loc[:, ~df.columns.duplicated(keep=keep)]

def to_int(x):
    return pd.to_numeric(x, errors="coerce").astype("Int64")

def strip_na(s):
    if pd.isna(s):
        return pd.NA
    s = str(s).strip()
    return s if s else pd.NA

def normalize_id(x):
    if pd.isna(x):
        return pd.NA
    s = str(x).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s if s else pd.NA

def map_bin(s):
    if pd.isna(s):
        return pd.NA
    return {1: 1, 2: 0,
            "1": 1, "2": 0,
            "是": 1, "否": 0,
            True: 1, False: 0}.get(s, pd.NA)

def clean_miss(df):
    """Archived notebook note for 02_wave2013_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    miss_maps = {
        "g1016":  [-9, -7],
        "g1016b": [-9, -7],   # Original notebook comment normalized for the public code archive.
        "e1012":  [-9999],
        "e1021":  [-9],
    }
    for c, bads in miss_maps.items():
        if c in df.columns:
            df[c] = (
                pd.to_numeric(df[c], errors="coerce")
                  .replace(bads, np.nan)
            )
    return df

def make_panel_id_2013(d):
    """Archived notebook note for 02_wave2013_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    key = pd.Series(pd.NA, index=d.index, dtype="object")
    for c in ["hhid_2011", "hhid_2013", "hhid"]:
        if c in d.columns:
            key = key.fillna(d[c].map(normalize_id))
    return key

# =============================================================================
hh  = drop_dup_cols(read_stata_safe(os.path.join(BASE, FN_HH)))
ind = drop_dup_cols(read_stata_safe(os.path.join(BASE, FN_IND)))
geo = drop_dup_cols(read_stata_safe(os.path.join(BASE, FN_GEO)))

# =============================================================================
for d in (hh, ind, geo):
    for c in [c for c in ["hhid", "hhid_2011", "hhid_2013"] if c in d.columns]:
        d[c] = d[c].map(normalize_id)

hh  = hh.copy();  hh["hh_key"]  = make_panel_id_2013(hh)
ind = ind.copy(); ind["hh_key"] = make_panel_id_2013(ind)
geo = geo.copy(); geo["hh_key"] = make_panel_id_2013(geo)

# =============================================================================
if "a2005" not in ind.columns:
    raise KeyError("2013 IND 缺少 a2005（出生年）")
ind["a2005"] = to_int(ind["a2005"])

ind = pd.concat(
    [ind,
     pd.DataFrame({"age": (SURVEY_YEAR - ind["a2005"]).astype("float")},
                  index=ind.index)],
    axis=1
)
ind.loc[(ind["age"] < 0) | (ind["age"] > 120), "age"] = pd.NA

child = (
    ind.assign(child_u15=(ind["age"] <= 15).astype("Int64"))
       .groupby("hh_key", as_index=False)["child_u15"].sum()
       .rename(columns={"child_u15": "child_u15_num"})
)
child["any_child_u15"] = (child["child_u15_num"] > 0).astype("Int64")
child = drop_dup_cols(child)

# =============================================================================
keep_geo = [
    "hh_key", "hhid", "hhid_2011", "hhid_2013",
    "prov_CHN", "city", "county", "rural", "swgt"
]
geo = geo[[c for c in keep_geo if c in geo.columns]].copy()
geo = geo.drop_duplicates(subset="hh_key", keep="first")
geo["rural"] = to_int(geo.get("rural"))
geo["swgt"]  = pd.to_numeric(geo.get("swgt"), errors="coerce")
for c in ["prov_CHN", "city", "county"]:
    if c in geo.columns:
        geo[c] = geo[c].apply(strip_na)

# =============================================================================
df = hh.merge(child, on="hh_key", how="left", validate="one_to_one")
df = df.merge(geo,   on="hh_key", how="left", validate="one_to_one")

df["child_u15_num"] = df["child_u15_num"].fillna(0).astype("Int64")
df["any_child_u15"] = df["any_child_u15"].fillna(0).astype("Int64")

# =============================================================================
df = clean_miss(df)
df["是否有教育银行贷款_二元"] = df.get("e1001").apply(map_bin).astype("Int64")
df["是否为子女教育借款_二元"] = df.get("e1020").apply(map_bin).astype("Int64")

# =============================================================================
df["panel_id"] = df["hh_key"]

select = [
    "panel_id", "hhid_2011", "hhid_2013", "hhid",
    "prov_CHN", "city", "county", "rural", "swgt",
    "total_income", "censor_total_income_imp",
    "e1001", "e1008", "e1012", "e1020", "e1021",
    "g1016", "g1016b",      # Original notebook comment normalized for the public code archive.
    "any_child_u15", "child_u15_num",
    "是否有教育银行贷款_二元", "是否为子女教育借款_二元",
]
select = [c for c in select if c in df.columns]

out = df[select].rename(columns={
    "panel_id":    "家庭ID",
    "hhid_2011":   "家庭ID2011",
    "hhid_2013":   "当波家庭ID（2013）",
    "hhid":        "备用ID",
    "prov_CHN":    "省",
    "city":        "市",
    "county":      "县",
    "rural":       "是否农村",
    "swgt":        "抽样权重",
    "total_income":              f"家庭可支配收入（{INCOME_YEAR}年，元）",
    "censor_total_income_imp":   "收入截尾标记（imp）",
    "e1001": "是否有教育银行贷款（原始码1/2）",
    "e1008": "教育贷款年份",
    "e1012": "教育贷款总额（元）",
    "e1020": "是否为子女教育向他人/机构借款（原始码1/2）",
    "e1021": "子女教育借款总额（元）",
    "g1016":  f"去年教育培训支出（{INCOME_YEAR}年，元）",
    "g1016b": f"去年子女教育培训支出（{INCOME_YEAR}年，元）",  # Original notebook comment normalized for the public code archive.
    "any_child_u15":  "是否有15岁及以下儿童",
    "child_u15_num":  "15岁及以下儿童数量",
})

for c in ["省", "市", "县"]:
    if c in out.columns:
        out[c] = out[c].apply(strip_na)

out.to_excel(os.path.join(BASE, OUT_XLSX), index=False)
print("[INFO] Notebook progress message.", os.path.join(BASE, OUT_XLSX))


# ------------------------------------------------------------------------------
# Notebook cell 10
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 02_wave2013_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import numpy as np
import pandas as pd

# =============================================================================
BASE = r"E:\project_flood_impact_assessment\教育数据\CHFS_center\2013"
FN_HH  = "chfs2013_hh_20191120_version14.dta"
FN_IND = "chfs2013_ind_20191120_version14.dta"
FN_GEO = "区县码2013.dta"
OUT_XLSX = "CHFS2013_教育与收入_户级.xlsx"

SURVEY_YEAR = 2013
INCOME_YEAR = 2012

# =============================================================================
def read_stata_safe(p):
    try:
        return pd.read_stata(p, convert_categoricals=False)
    except Exception:
        return pd.read_stata(p, convert_categoricals=True)

def drop_dup_cols(df, keep="first"):
    return df.loc[:, ~df.columns.duplicated(keep=keep)]

def to_int(x):
    return pd.to_numeric(x, errors="coerce").astype("Int64")

def strip_na(s):
    if pd.isna(s):
        return pd.NA
    s = str(s).strip()
    return s if s else pd.NA

def normalize_id(x):
    if pd.isna(x):
        return pd.NA
    s = str(x).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s if s else pd.NA

def map_bin(s):
    if pd.isna(s):
        return pd.NA
    return {1: 1, 2: 0,
            "1": 1, "2": 0,
            "是": 1, "否": 0,
            True: 1, False: 0}.get(s, pd.NA)

def clean_miss(df):
    """Archived notebook note for 02_wave2013_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    miss_maps = {
        "g1016":  [-9, -7],
        "g1016b": [-9, -7],
        "e1012":  [-9999],
        "e1021":  [-9],
    }
    for c, bads in miss_maps.items():
        if c in df.columns:
            df[c] = (
                pd.to_numeric(df[c], errors="coerce")
                  .replace(bads, np.nan)
            )
    return df

def make_panel_id_2013(d):
    """Archived notebook note for 02_wave2013_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    key = pd.Series(pd.NA, index=d.index, dtype="object")
    for c in ["hhid_2011", "hhid_2013", "hhid"]:
        if c in d.columns:
            key = key.fillna(d[c].map(normalize_id))
    return key

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
hh  = drop_dup_cols(read_stata_safe(os.path.join(BASE, FN_HH)))
ind = drop_dup_cols(read_stata_safe(os.path.join(BASE, FN_IND)))
geo = drop_dup_cols(read_stata_safe(os.path.join(BASE, FN_GEO)))

# =============================================================================
for d in (hh, ind, geo):
    for c in [c for c in ["hhid", "hhid_2011", "hhid_2013"] if c in d.columns]:
        d[c] = d[c].map(normalize_id)

hh  = hh.copy();  hh["hh_key"]  = make_panel_id_2013(hh)
ind = ind.copy(); ind["hh_key"] = make_panel_id_2013(ind)
geo = geo.copy(); geo["hh_key"] = make_panel_id_2013(geo)

# =============================================================================
if "a2005" not in ind.columns:
    raise KeyError("2013 IND 缺少 a2005（出生年）")

ind["a2005"] = to_int(ind["a2005"])

ind = pd.concat(
    [ind,
     pd.DataFrame({"age": (SURVEY_YEAR - ind["a2005"]).astype("float")},
                  index=ind.index)],
    axis=1
)
ind.loc[(ind["age"] < 0) | (ind["age"] > 120), ["age", "a2005"]] = pd.NA

# =============================================================================
child = (
    ind.assign(child_u15=(ind["age"] <= 15).astype("Int64"))
       .groupby("hh_key", as_index=False)["child_u15"].sum()
       .rename(columns={"child_u15": "child_u15_num"})
)
child["any_child_u15"] = (child["child_u15_num"] > 0).astype("Int64")
child = drop_dup_cols(child)

# =============================================================================
# Original notebook comment normalized for the public code archive.
if "a2012" in ind.columns:
    ind["edu_code"] = to_int(ind["a2012"])
    ind.loc[~ind["edu_code"].between(1, 9), "edu_code"] = pd.NA
else:
    ind["edu_code"] = pd.Series(pd.NA, index=ind.index, dtype="Int64")

# Original notebook comment normalized for the public code archive.
birth_agg = (
    ind.groupby("hh_key")["a2005"]
       .agg(hh_birth_min="min",
            hh_birth_max="max",
            hh_birth_mean="mean")
       .reset_index()
)

# Original notebook comment normalized for the public code archive.
edu_agg = (
    ind.groupby("hh_key")["edu_code"]
       .max()
       .rename("hh_max_edu_code")
       .reset_index()
)

# =============================================================================
keep_geo = [
    "hh_key", "hhid", "hhid_2011", "hhid_2013",
    "prov_CHN", "city", "county", "rural", "swgt"
]
geo = geo[[c for c in keep_geo if c in geo.columns]].copy()
geo = geo.drop_duplicates(subset="hh_key", keep="first")
geo["rural"] = to_int(geo.get("rural"))
geo["swgt"]  = pd.to_numeric(geo.get("swgt"), errors="coerce")
for c in ["prov_CHN", "city", "county"]:
    if c in geo.columns:
        geo[c] = geo[c].apply(strip_na)

# =============================================================================
df = hh.merge(child,     on="hh_key", how="left", validate="one_to_one")
df = df.merge(birth_agg, on="hh_key", how="left")
df = df.merge(edu_agg,   on="hh_key", how="left")
df = df.merge(geo,       on="hh_key", how="left", validate="one_to_one")

df["child_u15_num"] = df["child_u15_num"].fillna(0).astype("Int64")
df["any_child_u15"] = df["any_child_u15"].fillna(0).astype("Int64")

# Original notebook comment normalized for the public code archive.
df["hh_max_edu_label"] = df["hh_max_edu_code"].map(EDU_LABEL_MAP)

# =============================================================================
df = clean_miss(df)
df["是否有教育银行贷款_二元"] = df.get("e1001").apply(map_bin).astype("Int64")
df["是否为子女教育借款_二元"] = df.get("e1020").apply(map_bin).astype("Int64")

# =============================================================================
df["panel_id"] = df["hh_key"]

select = [
    "panel_id", "hhid_2011", "hhid_2013", "hhid",
    "prov_CHN", "city", "county", "rural", "swgt",
    "total_income", "censor_total_income_imp",
    "e1001", "e1008", "e1012", "e1020", "e1021",
    "g1016", "g1016b",
    "any_child_u15", "child_u15_num",
    "是否有教育银行贷款_二元", "是否为子女教育借款_二元",
    # Original notebook comment normalized for the public code archive.
    "hh_birth_min", "hh_birth_max", "hh_birth_mean",
    "hh_max_edu_code", "hh_max_edu_label",
]
select = [c for c in select if c in df.columns]

out = df[select].rename(columns={
    "panel_id":    "家庭ID",
    "hhid_2011":   "家庭ID2011",
    "hhid_2013":   "当波家庭ID（2013）",
    "hhid":        "备用ID",
    "prov_CHN":    "省",
    "city":        "市",
    "county":      "县",
    "rural":       "是否农村",
    "swgt":        "抽样权重",
    "total_income":            f"家庭可支配收入（{INCOME_YEAR}年，元）",
    "censor_total_income_imp":"收入截尾标记（imp）",
    "e1001": "是否有教育银行贷款（原始码1/2）",
    "e1008": "教育贷款年份",
    "e1012": "教育贷款总额（元）",
    "e1020": "是否为子女教育向他人/机构借款（原始码1/2）",
    "e1021": "子女教育借款总额（元）",
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

for c in ["省", "市", "县"]:
    if c in out.columns:
        out[c] = out[c].apply(strip_na)

out_path = os.path.join(BASE, OUT_XLSX)
out.to_excel(out_path, index=False)
print("[INFO] Notebook progress message.", out_path)
