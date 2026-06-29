#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 03_wave2015_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 4
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 03_wave2015_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
import os, numpy as np, pandas as pd

BASE = r"E:\project_flood_impact_assessment\教育数据\CHFS_center\2015"
FN_HH  = "chfs2015_hh_20191120_version14.dta"
FN_IND = "chfs2015_ind_20191120_version14.dta"
FN_GEO = "区县码2015.dta"
OUT_XLSX = "CHFS2015_教育与收入_户级.xlsx"

SURVEY_YEAR = 2015
INCOME_YEAR = 2014

def read_stata_safe(p):
    try: return pd.read_stata(p, convert_categoricals=False)
    except Exception: return pd.read_stata(p, convert_categoricals=True)

def drop_dup(df):
    return df.loc[:, ~df.columns.duplicated(keep="first")]

def to_int(x): return pd.to_numeric(x, errors="coerce").astype("Int64")
def strip_na(s):
    if pd.isna(s): return pd.NA
    s=str(s).strip(); return s if s else pd.NA
def normalize_id(x):
    if pd.isna(x): return pd.NA
    s=str(x).strip()
    if s.endswith(".0"): s=s[:-2]
    return s if s else pd.NA
def map_bin(s):
    if pd.isna(s): return pd.NA
    return {1:1,2:0,"1":1,"2":0,"是":1,"否":0,True:1,False:0}.get(s,pd.NA)
def clean_miss(df):
    for c,b in {"g1016":[-9,-7],"e1021":[-9],"e1007c":[-9,-7]}.items():
        if c in df.columns: df[c]=pd.to_numeric(df[c],errors="coerce").replace(b,np.nan)
    return df

hh, ind, geo = [drop_dup(read_stata_safe(os.path.join(BASE,f))) for f in [FN_HH,FN_IND,FN_GEO]]

# Original notebook comment normalized for the public code archive.
need_hh={"hhid","hhid_2011","hhid_2013","hhid_2015",
         "total_income","censor_total_income_imp",
         "e1001","e1008","e1007c","e1020","e1021","g1016"}
miss=[c for c in need_hh if c not in hh.columns]
if miss: raise KeyError(f"2015 HH 缺少字段：{miss}")

# Original notebook comment normalized for the public code archive.
for d in (hh, ind, geo):
    for c in [c for c in ["hhid","hhid_2011","hhid_2013","hhid_2015"] if c in d.columns]:
        d[c]=d[c].map(normalize_id)

# Original notebook comment normalized for the public code archive.
by=None
if "a2005" in ind.columns: by=to_int(ind["a2005"])
if "a1114" in ind.columns:
    b2=to_int(ind["a1114"]); by = by.fillna(b2) if by is not None else b2
if by is None: raise KeyError("2015 IND 缺少 a2005/a1114")
ind["age"]=SURVEY_YEAR - by
ind.loc[(ind["age"]<0)|(ind["age"]>120),"age"]=pd.NA
child=(ind.assign(child_u15=(ind["age"]<=15).astype("Int64"))
         .groupby("hhid",as_index=False)["child_u15"].sum()
         .rename(columns={"child_u15":"child_u15_num"}))
child["any_child_u15"]=(child["child_u15_num"]>0).astype("Int64")
child = drop_dup(child)

# Original notebook comment normalized for the public code archive.
geo=geo[[c for c in ["hhid","prov_CHN","city","county","rural","swgt"] if c in geo.columns]].copy()
geo=geo.drop_duplicates(subset="hhid", keep="first")
geo["rural"]=to_int(geo.get("rural"))
geo["swgt"]=pd.to_numeric(geo.get("swgt"),errors="coerce")
for c in ["prov_CHN","city","county"]:
    if c in geo.columns: geo[c]=geo[c].apply(strip_na)

# Original notebook comment normalized for the public code archive.
df = hh.merge(child,on="hhid",how="left",validate="one_to_one")
df = df.merge(geo,on="hhid",how="left",validate="one_to_one")
df["child_u15_num"]=df["child_u15_num"].fillna(0).astype("Int64")
df["any_child_u15"]=df["any_child_u15"].fillna(0).astype("Int64")

# Original notebook comment normalized for the public code archive.
df=clean_miss(df)
df["是否有教育银行贷款_二元"]=df.get("e1001").apply(map_bin).astype("Int64")
df["是否为子女教育借款_二元"]=df.get("e1020").apply(map_bin).astype("Int64")

# Original notebook comment normalized for the public code archive.
df["panel_id"]=df["hhid_2011"].fillna(df["hhid_2013"]).fillna(df["hhid_2015"]).fillna(df["hhid"])

select = [
    "panel_id","hhid_2011","hhid_2013","hhid_2015","hhid",
    "prov_CHN","city","county","rural","swgt",
    "total_income","censor_total_income_imp",
    "e1001","e1008","e1007c","e1020","e1021","g1016",
    "any_child_u15","child_u15_num",
    "是否有教育银行贷款_二元","是否为子女教育借款_二元"
]
select=[c for c in select if c in df.columns]
out=df[select].rename(columns={
    "panel_id":"家庭ID","hhid_2011":"家庭ID2011","hhid_2013":"上一波家庭ID（2013）",
    "hhid_2015":"当波家庭ID（2015）","hhid":"备用ID",
    "prov_CHN":"省","city":"市","county":"县","rural":"是否农村","swgt":"抽样权重",
    "total_income":f"家庭可支配收入（{INCOME_YEAR}年，元）",
    "censor_total_income_imp":"收入截尾标记（imp）",
    "e1001":"是否有教育银行贷款（原始码1/2）","e1008":"教育贷款年份",
    "e1007c":"教育贷款总额（元）","e1020":"是否为子女教育向他人/机构借款（原始码1/2）",
    "e1021":"子女教育借款总额（元）","g1016":f"去年教育培训支出（{INCOME_YEAR}年，元）",
    "any_child_u15":"是否有15岁及以下儿童","child_u15_num":"15岁及以下儿童数量",
})
for c in ["省","市","县"]:
    if c in out.columns: out[c]=out[c].apply(strip_na)
out.to_excel(os.path.join(BASE, OUT_XLSX), index=False)
print("[INFO] Notebook progress message.", os.path.join(BASE, OUT_XLSX))


# ------------------------------------------------------------------------------
# Notebook cell 7
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 03_wave2015_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
import os, numpy as np, pandas as pd

BASE = r"E:\project_flood_impact_assessment\教育数据\CHFS_center\2015"
FN_HH  = "chfs2015_hh_20191120_version14.dta"
FN_IND = "chfs2015_ind_20191120_version14.dta"
FN_GEO = "区县码2015.dta"
OUT_XLSX = "CHFS2015_教育与收入_户级.xlsx"

SURVEY_YEAR = 2015
INCOME_YEAR = 2014

def read_stata_safe(p):
    try:
        return pd.read_stata(p, convert_categoricals=False)
    except Exception:
        return pd.read_stata(p, convert_categoricals=True)

def drop_dup(df):
    return df.loc[:, ~df.columns.duplicated(keep="first")]

def to_int(x):
    return pd.to_numeric(x, errors="coerce").astype("Int64")

def strip_na(s):
    if pd.isna(s): return pd.NA
    s = str(s).strip()
    return s if s else pd.NA

def normalize_id(x):
    if pd.isna(x): return pd.NA
    s = str(x).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s if s else pd.NA

def map_bin(s):
    if pd.isna(s): return pd.NA
    return {1:1,2:0,"1":1,"2":0,"是":1,"否":0,True:1,False:0}.get(s,pd.NA)

def clean_miss(df):
    """Archived notebook note for 03_wave2015_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    miss_dict = {
        "g1016":  [-9, -7],
        "g1016b": [-9, -7],  # Original notebook comment normalized for the public code archive.
        "e1021":  [-9],
        "e1007c": [-9, -7],
    }
    for c, bads in miss_dict.items():
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").replace(bads, np.nan)
    return df

# =============================================================================
hh, ind, geo = [drop_dup(read_stata_safe(os.path.join(BASE,f)))
                for f in [FN_HH, FN_IND, FN_GEO]]

# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
need_hh = {
    "hhid","hhid_2011","hhid_2013","hhid_2015",
    "total_income","censor_total_income_imp",
    "e1001","e1008","e1007c","e1020","e1021","g1016"
}
miss = [c for c in need_hh if c not in hh.columns]
if miss:
    raise KeyError(f"2015 HH 缺少字段：{miss}")

# =============================================================================
for d in (hh, ind, geo):
    for c in [c for c in ["hhid","hhid_2011","hhid_2013","hhid_2015"] if c in d.columns]:
        d[c] = d[c].map(normalize_id)

# =============================================================================
by = None
if "a2005" in ind.columns:
    by = to_int(ind["a2005"])
if "a1114" in ind.columns:
    b2 = to_int(ind["a1114"])
    by = by.fillna(b2) if by is not None else b2
if by is None:
    raise KeyError("2015 IND 缺少 a2005/a1114")

ind["age"] = SURVEY_YEAR - by
ind.loc[(ind["age"] < 0) | (ind["age"] > 120), "age"] = pd.NA

child = (
    ind.assign(child_u15=(ind["age"] <= 15).astype("Int64"))
       .groupby("hhid", as_index=False)["child_u15"].sum()
       .rename(columns={"child_u15":"child_u15_num"})
)
child["any_child_u15"] = (child["child_u15_num"] > 0).astype("Int64")
child = drop_dup(child)

# =============================================================================
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
#     edu_ij      = i + j
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.

col_map = {c.lower(): c for c in ind.columns}
col_i = col_map.get("a2013i")
col_j = col_map.get("a2013j")

if col_i or col_j:
    for c in [col_i, col_j]:
        if c:
            ind[c] = pd.to_numeric(ind[c], errors="coerce").replace({-9: np.nan, -7: np.nan})
    use_cols = [c for c in [col_i, col_j] if c]

    if use_cols:
        ind["edu_ij"] = ind[use_cols].sum(axis=1, skipna=True)
    else:
        ind["edu_ij"] = np.nan

    # Original notebook comment normalized for the public code archive.
    edu_all = (
        ind.groupby("hhid", as_index=False)["edu_ij"]
           .sum()
           .rename(columns={"edu_ij": "child_edu_all"})
    )

    # Original notebook comment normalized for the public code archive.
    edu_u15 = (
        ind.loc[ind["age"] <= 15]
           .groupby("hhid", as_index=False)["edu_ij"]
           .sum()
           .rename(columns={"edu_ij": "child_edu_u15"})
    )
else:
    edu_all = pd.DataFrame({"hhid": [], "child_edu_all": []})
    edu_u15 = pd.DataFrame({"hhid": [], "child_edu_u15": []})

# =============================================================================
geo = geo[[c for c in ["hhid","prov_CHN","city","county","rural","swgt"] if c in geo.columns]].copy()
geo = geo.drop_duplicates(subset="hhid", keep="first")
geo["rural"] = to_int(geo.get("rural"))
geo["swgt"]  = pd.to_numeric(geo.get("swgt"), errors="coerce")
for c in ["prov_CHN","city","county"]:
    if c in geo.columns:
        geo[c] = geo[c].apply(strip_na)

# =============================================================================
df = hh.merge(child,   on="hhid", how="left", validate="one_to_one")
df = df.merge(edu_all, on="hhid", how="left")   # Original notebook comment normalized for the public code archive.
df = df.merge(edu_u15, on="hhid", how="left")   # Original notebook comment normalized for the public code archive.
df = df.merge(geo,     on="hhid", how="left", validate="one_to_one")

# Original notebook comment normalized for the public code archive.
df["child_u15_num"]  = df["child_u15_num"].fillna(0).astype("Int64")
df["any_child_u15"]  = df["any_child_u15"].fillna(0).astype("Int64")
if "child_edu_all" in df.columns:
    df["child_edu_all"] = df["child_edu_all"].fillna(0.0)
if "child_edu_u15" in df.columns:
    df["child_edu_u15"] = df["child_edu_u15"].fillna(0.0)

# =============================================================================
df = clean_miss(df)
df["是否有教育银行贷款_二元"] = df.get("e1001").apply(map_bin).astype("Int64")
df["是否为子女教育借款_二元"] = df.get("e1020").apply(map_bin).astype("Int64")

# =============================================================================
df["panel_id"] = (
    df["hhid_2011"].fillna(df["hhid_2013"])
                   .fillna(df["hhid_2015"])
                   .fillna(df["hhid"])
)

# =============================================================================
select = [
    "panel_id","hhid_2011","hhid_2013","hhid_2015","hhid",
    "prov_CHN","city","county","rural","swgt",
    "total_income","censor_total_income_imp",
    "e1001","e1008","e1007c","e1020","e1021",
    "g1016","g1016b",          # Original notebook comment normalized for the public code archive.
    "any_child_u15","child_u15_num",
    "child_edu_all","child_edu_u15",  # Original notebook comment normalized for the public code archive.
    "是否有教育银行贷款_二元","是否为子女教育借款_二元"
]
select = [c for c in select if c in df.columns]

out = df[select].rename(columns={
    "panel_id":    "家庭ID",
    "hhid_2011":   "家庭ID2011",
    "hhid_2013":   "上一波家庭ID（2013）",
    "hhid_2015":   "当波家庭ID（2015）",
    "hhid":        "备用ID",
    "prov_CHN":    "省",
    "city":        "市",
    "county":      "县",
    "rural":       "是否农村",
    "swgt":        "抽样权重",
    "total_income":              f"家庭可支配收入（{INCOME_YEAR}年，元）",
    "censor_total_income_imp":   "收入截尾标记（imp）",
    "e1001":       "是否有教育银行贷款（原始码1/2）",
    "e1008":       "教育贷款年份",
    "e1007c":      "教育贷款总额（元）",
    "e1020":       "是否为子女教育向他人/机构借款（原始码1/2）",
    "e1021":       "子女教育借款总额（元）",
    "g1016":       f"去年教育培训支出（{INCOME_YEAR}年，元）",
    "g1016b":      f"去年子女教育培训支出（{INCOME_YEAR}年，元）",  # Original notebook comment normalized for the public code archive.
    "any_child_u15": "是否有15岁及以下儿童",
    "child_u15_num": "15岁及以下儿童数量",
    "child_edu_all": "在校成员教育支出总额（A2013i+j汇总，元）",
    "child_edu_u15": "15岁及以下子女教育支出总额（A2013i+j汇总，元）",
})

for c in ["省","市","县"]:
    if c in out.columns:
        out[c] = out[c].apply(strip_na)

out_path = os.path.join(BASE, OUT_XLSX)
out.to_excel(out_path, index=False)
print("[INFO] Notebook progress message.", out_path)


# ------------------------------------------------------------------------------
# Notebook cell 10
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 03_wave2015_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os, numpy as np, pandas as pd

BASE = r"E:\project_flood_impact_assessment\教育数据\CHFS_center\2015"
FN_HH  = "chfs2015_hh_20191120_version14.dta"
FN_IND = "chfs2015_ind_20191120_version14.dta"
FN_GEO = "区县码2015.dta"
OUT_XLSX = "CHFS2015_教育与收入_户级.xlsx"

SURVEY_YEAR = 2015
INCOME_YEAR = 2014

def read_stata_safe(p):
    try:
        return pd.read_stata(p, convert_categoricals=False)
    except Exception:
        return pd.read_stata(p, convert_categoricals=True)

def drop_dup(df):
    return df.loc[:, ~df.columns.duplicated(keep="first")]

def to_int(x):
    return pd.to_numeric(x, errors="coerce").astype("Int64")

def strip_na(s):
    if pd.isna(s): return pd.NA
    s = str(s).strip()
    return s if s else pd.NA

def normalize_id(x):
    if pd.isna(x): return pd.NA
    s = str(x).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s if s else pd.NA

def map_bin(s):
    if pd.isna(s): return pd.NA
    return {1:1,2:0,"1":1,"2":0,"是":1,"否":0,True:1,False:0}.get(s,pd.NA)

def clean_miss(df):
    """Archived notebook note for 03_wave2015_household_variables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    miss_dict = {
        "g1016":  [-9, -7],
        "g1016b": [-9, -7],
        "e1021":  [-9],
        "e1007c": [-9, -7],
    }
    for c, bads in miss_dict.items():
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").replace(bads, np.nan)
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
hh, ind, geo = [drop_dup(read_stata_safe(os.path.join(BASE,f)))
                for f in [FN_HH, FN_IND, FN_GEO]]

# Original notebook comment normalized for the public code archive.
need_hh = {
    "hhid","hhid_2011","hhid_2013","hhid_2015",
    "total_income","censor_total_income_imp",
    "e1001","e1008","e1007c","e1020","e1021","g1016"
}
miss = [c for c in need_hh if c not in hh.columns]
if miss:
    raise KeyError(f"2015 HH 缺少字段：{miss}")

# =============================================================================
for d in (hh, ind, geo):
    for c in [c for c in ["hhid","hhid_2011","hhid_2013","hhid_2015"] if c in d.columns]:
        d[c] = d[c].map(normalize_id)

# =============================================================================
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
birth = None
if "a2005" in ind.columns:
    birth = to_int(ind["a2005"])
if "a1114" in ind.columns:
    b2 = to_int(ind["a1114"])
    birth = birth.fillna(b2) if birth is not None else b2
if birth is None:
    raise KeyError("2015 IND 缺少 a2005/a1114（出生年）")

ind["birth"] = birth
ind["age"] = SURVEY_YEAR - ind["birth"]
# Original notebook comment normalized for the public code archive.
ind.loc[(ind["age"] < 0) | (ind["age"] > 120), ["age","birth"]] = pd.NA

# =============================================================================
child = (
    ind.assign(child_u15=(ind["age"] <= 15).astype("Int64"))
       .groupby("hhid", as_index=False)["child_u15"].sum()
       .rename(columns={"child_u15":"child_u15_num"})
)
child["any_child_u15"] = (child["child_u15_num"] > 0).astype("Int64")
child = drop_dup(child)

# =============================================================================
birth_agg = (
    ind.groupby("hhid")["birth"]
       .agg(hh_birth_min="min",
            hh_birth_max="max",
            hh_birth_mean="mean")
       .reset_index()
)

# =============================================================================
if "a2012" in ind.columns:
    ind["edu_code"] = to_int(ind["a2012"])
    ind.loc[~ind["edu_code"].between(1, 9), "edu_code"] = pd.NA
else:
    ind["edu_code"] = pd.Series(pd.NA, index=ind.index, dtype="Int64")

edu_agg = (
    ind.groupby("hhid")["edu_code"]
       .max()
       .rename("hh_max_edu_code")
       .reset_index()
)

# =============================================================================
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
col_map = {c.lower(): c for c in ind.columns}
col_i = col_map.get("a2013i")
col_j = col_map.get("a2013j")

if col_i or col_j:
    for c in [col_i, col_j]:
        if c:
            ind[c] = pd.to_numeric(ind[c], errors="coerce").replace({-9: np.nan, -7: np.nan})
    use_cols = [c for c in [col_i, col_j] if c]

    if use_cols:
        ind["edu_ij"] = ind[use_cols].sum(axis=1, skipna=True)
    else:
        ind["edu_ij"] = np.nan

    # Original notebook comment normalized for the public code archive.
    edu_all = (
        ind.groupby("hhid", as_index=False)["edu_ij"]
           .sum()
           .rename(columns={"edu_ij": "child_edu_all"})
    )

    # Original notebook comment normalized for the public code archive.
    edu_u15 = (
        ind.loc[ind["age"] <= 15]
           .groupby("hhid", as_index=False)["edu_ij"]
           .sum()
           .rename(columns={"edu_ij": "child_edu_u15"})
    )
else:
    edu_all = pd.DataFrame({"hhid": [], "child_edu_all": []})
    edu_u15 = pd.DataFrame({"hhid": [], "child_edu_u15": []})

# =============================================================================
geo = geo[[c for c in ["hhid","prov_CHN","city","county","rural","swgt"] if c in geo.columns]].copy()
geo = geo.drop_duplicates(subset="hhid", keep="first")
geo["rural"] = to_int(geo.get("rural"))
geo["swgt"]  = pd.to_numeric(geo.get("swgt"), errors="coerce")
for c in ["prov_CHN","city","county"]:
    if c in geo.columns:
        geo[c] = geo[c].apply(strip_na)

# =============================================================================
df = hh.merge(child,    on="hhid", how="left", validate="one_to_one")
df = df.merge(edu_all,  on="hhid", how="left")
df = df.merge(edu_u15,  on="hhid", how="left")
df = df.merge(birth_agg,on="hhid", how="left")
df = df.merge(edu_agg,  on="hhid", how="left")
df = df.merge(geo,      on="hhid", how="left", validate="one_to_one")

# Original notebook comment normalized for the public code archive.
df["hh_max_edu_label"] = df["hh_max_edu_code"].map(EDU_LABEL_MAP)

# Original notebook comment normalized for the public code archive.
df["child_u15_num"]  = df["child_u15_num"].fillna(0).astype("Int64")
df["any_child_u15"]  = df["any_child_u15"].fillna(0).astype("Int64")
if "child_edu_all" in df.columns:
    df["child_edu_all"] = df["child_edu_all"].fillna(0.0)
if "child_edu_u15" in df.columns:
    df["child_edu_u15"] = df["child_edu_u15"].fillna(0.0)

# =============================================================================
df = clean_miss(df)
df["是否有教育银行贷款_二元"] = df.get("e1001").apply(map_bin).astype("Int64")
df["是否为子女教育借款_二元"] = df.get("e1020").apply(map_bin).astype("Int64")

# =============================================================================
df["panel_id"] = (
    df["hhid_2011"].fillna(df["hhid_2013"])
                   .fillna(df["hhid_2015"])
                   .fillna(df["hhid"])
)

# =============================================================================
select = [
    "panel_id","hhid_2011","hhid_2013","hhid_2015","hhid",
    "prov_CHN","city","county","rural","swgt",
    "total_income","censor_total_income_imp",
    "e1001","e1008","e1007c","e1020","e1021",
    "g1016","g1016b",
    "any_child_u15","child_u15_num",
    "child_edu_all","child_edu_u15",
    "hh_birth_min","hh_birth_max","hh_birth_mean",
    "hh_max_edu_code","hh_max_edu_label",
    "是否有教育银行贷款_二元","是否为子女教育借款_二元"
]
select = [c for c in select if c in df.columns]

out = df[select].rename(columns={
    "panel_id":    "家庭ID",
    "hhid_2011":   "家庭ID2011",
    "hhid_2013":   "上一波家庭ID（2013）",
    "hhid_2015":   "当波家庭ID（2015）",
    "hhid":        "备用ID",
    "prov_CHN":    "省",
    "city":        "市",
    "county":      "县",
    "rural":       "是否农村",
    "swgt":        "抽样权重",
    "total_income":              f"家庭可支配收入（{INCOME_YEAR}年，元）",
    "censor_total_income_imp":   "收入截尾标记（imp）",
    "e1001":       "是否有教育银行贷款（原始码1/2）",
    "e1008":       "教育贷款年份",
    "e1007c":      "教育贷款总额（元）",
    "e1020":       "是否为子女教育向他人/机构借款（原始码1/2）",
    "e1021":       "子女教育借款总额（元）",
    "g1016":       f"去年教育培训支出（{INCOME_YEAR}年，元）",
    "g1016b":      f"去年子女教育培训支出（{INCOME_YEAR}年，元）",
    "any_child_u15": "是否有15岁及以下儿童",
    "child_u15_num": "15岁及以下儿童数量",
    "child_edu_all": "在校成员教育支出总额（A2013i+j汇总，元）",
    "child_edu_u15": "15岁及以下子女教育支出总额（A2013i+j汇总，元）",
    "hh_birth_min":  "最年长成员出生年",
    "hh_birth_max":  "最年轻成员出生年",
    "hh_birth_mean": "家庭成员平均出生年",
    "hh_max_edu_code":  "家庭最高文化程度（代码）",
    "hh_max_edu_label": "家庭最高文化程度",
})

for c in ["省","市","县"]:
    if c in out.columns:
        out[c] = out[c].apply(strip_na)

out_path = os.path.join(BASE, OUT_XLSX)
out.to_excel(out_path, index=False)
print("[INFO] Notebook progress message.", out_path)
