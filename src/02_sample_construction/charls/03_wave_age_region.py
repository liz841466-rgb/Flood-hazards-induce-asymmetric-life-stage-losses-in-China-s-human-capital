#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 03_wave_age_region.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""



# =============================================================================
# Source notebook
# =============================================================================
# record_type : wave_step
# year        : 2011
# step        : 3
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 03_wave_age_region.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 4
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 03_wave_age_region.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import re
import inspect
import numpy as np
import pandas as pd
from pathlib import Path

# =============================================================================
DEMOG = r"E:\project_flood_impact_assessment\老年人健康\CHARLS\charls原版数据\原始数据+问卷2011~2020\2011\household_and_community_questionnaire_data\demographic_background.dta"
PSU   = r"E:\project_flood_impact_assessment\老年人健康\CHARLS\charls原版数据\原始数据+问卷2011~2020\2011\household_and_community_questionnaire_data\psu.dta"
OUT_DIR = Path(r"E:\impact_assessment_child_order\older\health\2011")
OUT_DTA = OUT_DIR / "2011_age_region.dta"
OUT_XLSX= OUT_DIR / "2011_age_region.xlsx"
SURVEY_YEAR = 2011

# =============================================================================
def read_dta_smart(path, columns=None):
    """Archived notebook note for 03_wave_age_region.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    try:
        import pyreadstat
        df, meta = pyreadstat.read_dta(path, apply_value_formats=False, usecols=columns)
        print("[INFO] Notebook progress message.")
        return df
    except Exception as e:
        print("[INFO] Notebook progress message.")
        df = pd.read_stata(path, convert_categoricals=False, columns=columns)
        print("[INFO] Notebook progress message.")
        return df

def _clean_to_str(s: pd.Series) -> pd.Series:
    s = pd.Series(s, dtype="object")
    m = s.isna()
    sc = s[~m].astype(str).str.strip()
    sc = sc.str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = sc
    s.loc[m] = np.nan
    return s

def canon_id_fixed(s: pd.Series, width: int) -> pd.Series:
    s = _clean_to_str(s)
    m = s.notna()
    s.loc[m] = s.loc[m].astype(str).str.zfill(width)
    return s

def _digits_width(s: pd.Series, width: int) -> pd.Series:
    """Archived notebook note for 03_wave_age_region.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    t = _clean_to_str(s).str.replace(r"\D", "", regex=True)
    t = t.where(t.str.len() > 0, np.nan)
    return t.where(t.isna(), t.str[-width:].str.zfill(width)).astype("object")

def add_id12_hhid10_2011(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 03_wave_age_region.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()
    hh9  = _digits_width(df["householdID"], 9) if "householdID" in df.columns else pd.Series(np.nan, index=df.index)
    id11 = _digits_width(df["ID"],          11) if "ID"          in df.columns else pd.Series(np.nan, index=df.index)
    df["householdID10"] = hh9.where(hh9.isna(), hh9 + "0")
    pn2 = id11.str[-2:]
    df["ID12"] = np.where(hh9.notna() & pn2.notna(), df["householdID10"] + pn2, np.nan).astype("object")
    return df

def find_col(df: pd.DataFrame, *candidates):
    low = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand and not cand.startswith("^") and cand.lower() in low:
            return low[cand.lower()]
    for cand in candidates:
        if cand and cand.startswith("^"):
            pat = re.compile(cand, flags=re.I)
            for c in df.columns:
                if pat.match(c):
                    return c
    return None

# Original notebook comment normalized for the public code archive.
BAD_CHARS = "ÃÂÅÄÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞ±²³¼½¾"
def looks_mojibake(sample: str) -> bool:
    return any(ch in sample for ch in BAD_CHARS)
def has_chinese(sample: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", sample))
def fix_mojibake_series(s: pd.Series) -> pd.Series:
    """Archived notebook note for 03_wave_age_region.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = s.astype(object)
    m = s.notna()
    def _fix_one(val):
        if val is None: return val
        t = str(val)
        try:
            y = t.encode('latin1', errors='ignore').decode('gbk', errors='ignore')
            if has_chinese(y): return y
        except Exception:
            pass
        try:
            y = t.encode('latin1', errors='ignore').decode('gb18030', errors='ignore')
            if has_chinese(y): return y
        except Exception:
            pass
        return t
    s.loc[m] = [_fix_one(v) for v in s.loc[m]]
    return s

def write_dta_smart(df: pd.DataFrame, out_path: Path, var_labels=None):
    """Archived notebook note for 03_wave_age_region.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Original notebook comment normalized for the public code archive.
    cols = list(df.columns)
    new_cols, used = [], set()
    for c in cols:
        base = re.sub(r"[^0-9A-Za-z_]", "_", str(c))[:32]
        name, i = base, 1
        while name in used:
            suf = f"_{i}"
            name = base[:32-len(suf)] + suf
            i += 1
        new_cols.append(name); used.add(name)
    if new_cols != cols:
        df = df.rename(columns=dict(zip(cols, new_cols)))

    # 1) pyreadstat
    try:
        import pyreadstat
        for ver in (119, 118):
            kwargs = {"version": ver}
            if var_labels:
                try:
                    if "variable_labels" in inspect.signature(pyreadstat.write_dta).parameters:
                        kwargs["variable_labels"] = {k: var_labels.get(k, "") for k in df.columns}
                except Exception:
                    pass
            try:
                pyreadstat.write_dta(df, str(out_path), **kwargs)
                print("[INFO] Notebook progress message.")
                return
            except Exception as e:
                last = e
        print("[INFO] Notebook progress message.", last)
    except Exception as e:
        print("[INFO] Notebook progress message.", e)

    # 2) pandas UTF-8 (v118)
    try:
        df.to_stata(out_path, write_index=False, version=118)
        print("[INFO] Notebook progress message.", out_path)
        return
    except Exception as e:
        print("[INFO] Notebook progress message.", e)

    # Original notebook comment normalized for the public code archive.
    df2 = df.copy()
    for c in df2.select_dtypes(include=["object"]).columns:
        df2[c] = df2[c].astype(str).str.encode("latin-1", "ignore").str.decode("latin-1")
    df2.to_stata(out_path, write_index=False, version=117)
    print("[INFO] Notebook progress message.", out_path, "[INFO] Notebook progress message.")

# =============================================================================
demog = read_dta_smart(DEMOG)
psu   = read_dta_smart(PSU)

# =============================================================================
id_map = {
    "ID":          find_col(demog, "ID", "Pid", "PID", "pid", "personid"),
    "householdID": find_col(demog, "householdID", "HHID", "hhid", "HID", "hid", "houseid"),
    "communityID": find_col(demog, "communityID", "CID", "cid", "psu", "PSU"),
}
for std, real in list(id_map.items()):
    if real and real != std:
        demog = demog.rename(columns={real: std})

for key, width in (("householdID", 9), ("communityID", 7), ("ID", 11)):
    if key in demog.columns:
        demog[key] = canon_id_fixed(demog[key], width)
    else:
        demog[key] = pd.Series(np.nan, index=demog.index, dtype="object")

# Original notebook comment normalized for the public code archive.
demog = add_id12_hhid10_2011(demog)

# =============================================================================
def find_col_safe(name_or_regex):
    return find_col(demog, name_or_regex)  # Original notebook comment normalized for the public code archive.

col_ba002_1 = find_col_safe("ba002_1") or find_col_safe("^ba002_?1$")
col_BA004   = find_col_safe("BA004") or find_col_safe("ba004")

byr_report = pd.to_numeric(demog[col_ba002_1], errors="coerce") if col_ba002_1 else pd.Series(np.nan, index=demog.index)
age_self   = pd.to_numeric(demog[col_BA004],   errors="coerce") if col_BA004   else pd.Series(np.nan, index=demog.index)

# Original notebook comment normalized for the public code archive.
byr_report = byr_report.where((byr_report>=1900) & (byr_report<=SURVEY_YEAR), np.nan)
age_self   = age_self.where((age_self>=0) & (age_self<=120), np.nan)

# Original notebook comment normalized for the public code archive.
byr_from_age     = SURVEY_YEAR - age_self
byr_from_age_int = np.floor(byr_from_age).astype("float")

# Original notebook comment normalized for the public code archive.
birth_year = pd.Series(np.nan, index=demog.index, dtype="float")
equal_mask = (~byr_report.isna()) & (~byr_from_age_int.isna()) & (byr_report == byr_from_age_int)
only_report = (~byr_report.isna()) & (byr_from_age_int.isna())
only_age    = (byr_report.isna()) & (~byr_from_age_int.isna())
both_diff   = (~byr_report.isna()) & (~byr_from_age_int.isna()) & (byr_report != byr_from_age_int)

birth_year.loc[only_report] = byr_report.loc[only_report]
birth_year.loc[only_age]    = byr_from_age_int.loc[only_age]
birth_year.loc[equal_mask]  = byr_report.loc[equal_mask]
birth_year.loc[both_diff]   = np.minimum(byr_report.loc[both_diff], byr_from_age_int.loc[both_diff])
birth_year = birth_year.where((birth_year>=1900) & (birth_year<=SURVEY_YEAR), np.nan)
age_2011   = (SURVEY_YEAR - birth_year).where(~birth_year.isna(), np.nan)

# =============================================================================
col_comm_psu = find_col(psu, "communityID", "CID", "cid", "psu", "PSU")
if col_comm_psu and col_comm_psu != "communityID":
    psu = psu.rename(columns={col_comm_psu: "communityID"})
psu["communityID"] = canon_id_fixed(psu["communityID"], 7)

for col in ("province", "city"):
    if col in psu.columns and psu[col].dtype == object:
        sample = "".join(psu[col].dropna().astype(str).head(50).tolist())
        if looks_mojibake(sample) and not has_chinese(sample):
            print("[INFO] Notebook progress message.")
            psu[col] = fix_mojibake_series(psu[col])

keep_cols = [c for c in ["communityID","province","city","urban_nbs","areatype"] if c in psu.columns]
psu_slim = psu[keep_cols].drop_duplicates(subset=["communityID"]) if "communityID" in keep_cols else psu[keep_cols].copy()

# =============================================================================
out = demog[["ID","householdID","communityID","householdID10","ID12"]].copy()  # Original notebook comment normalized for the public code archive.
out["ba002_1"] = byr_report
out["BA004"]   = age_self
out["出生年"]    = birth_year
out["年龄"]     = age_2011

if "communityID" in psu_slim.columns:
    out = out.merge(psu_slim, on="communityID", how="left")

# =============================================================================
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Original notebook comment normalized for the public code archive.
cn2en = {"出生年": "birth_year", "年龄": "age_2011"}
out_dta = out.rename(columns=cn2en)
var_labels = {
    "ID":"ID(2011原11位)","householdID":"householdID(9位，2011原始)","communityID":"communityID(7位)",
    "householdID10":"householdID(10位，2013+兼容)","ID12":"个人ID(12位，2013+兼容)",
    "ba002_1":"报告出生年(ba002_1)","BA004":"自报年龄(BA004)",
    "birth_year":"出生年","age_2011":"年龄(2011-出生年)",
    "province":"省","city":"市","urban_nbs":"国家统计局城乡","areatype":"地区类型",
}
write_dta_smart(out_dta, OUT_DTA, var_labels=var_labels)

# Original notebook comment normalized for the public code archive.
out.to_excel(OUT_XLSX, index=False)
print("[INFO] Notebook progress message.", OUT_XLSX)

# =============================================================================
n_all = len(out); n_byr = out["出生年"].notna().sum(); n_age = out["年龄"].notna().sum()
print("[INFO] Notebook progress message.")
print(out[["province","city"]].dropna(how="all").head(5))




# =============================================================================
# Source notebook
# =============================================================================
# record_type : wave_step
# year        : 2013
# step        : 3
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 03_wave_age_region.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 3
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 03_wave_age_region.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import re
import inspect
import numpy as np
import pandas as pd
from pathlib import Path

# =============================================================================
DEMOG = r"E:\project_flood_impact_assessment\老年人健康\CHARLS\charls原版数据\原始数据+问卷2011~2020\2013\CHARLS2013_Dataset\demographic_background.dta"
PSU   = r"E:\project_flood_impact_assessment\老年人健康\CHARLS\charls原版数据\原始数据+问卷2011~2020\2013\CHARLS2013_Dataset\psu.dta"
OUT_DIR = Path(r"E:\impact_assessment_child_order\older\health\2013")
OUT_DTA = OUT_DIR / "2013_age_region.dta"
OUT_XLSX= OUT_DIR / "2013_age_region.xlsx"
SURVEY_YEAR = 2013

# =============================================================================
def read_dta_smart(path, columns=None):
    try:
        import pyreadstat
        df, meta = pyreadstat.read_dta(path, apply_value_formats=False, usecols=columns)
        print("[INFO] Notebook progress message.")
        return df
    except Exception as e:
        print("[INFO] Notebook progress message.")
        df = pd.read_stata(path, convert_categoricals=False, columns=columns)
        print("[INFO] Notebook progress message.")
        return df

def _clean_to_str(s: pd.Series) -> pd.Series:
    s = pd.Series(s, dtype="object")
    m = s.isna()
    sc = s[~m].astype(str).str.strip()
    sc = sc.str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = sc
    s.loc[m] = np.nan
    return s

def canon_id_fixed(s: pd.Series, width: int) -> pd.Series:
    s = _clean_to_str(s)
    m = s.notna()
    s.loc[m] = s.loc[m].astype(str).str.zfill(width)
    return s

def find_col(df: pd.DataFrame, *candidates):
    """Archived notebook note for 03_wave_age_region.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    low = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand and not cand.startswith("^") and cand.lower() in low:
            return low[cand.lower()]
    for cand in candidates:
        if cand and cand.startswith("^"):
            pat = re.compile(cand, flags=re.I)
            for c in df.columns:
                if pat.match(c): return c
    return None

# Original notebook comment normalized for the public code archive.
BAD_CHARS = "ÃÂÅÄÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞ±²³¼½¾"
def looks_mojibake(sample: str) -> bool:
    return any(ch in sample for ch in BAD_CHARS)
def has_chinese(sample: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", sample))
def fix_mojibake_series(s: pd.Series) -> pd.Series:
    s = s.astype(object); m = s.notna()
    def _fix_one(val):
        if val is None: return val
        t = str(val)
        try:
            y = t.encode('latin1', errors='ignore').decode('gbk', errors='ignore')
            if has_chinese(y): return y
        except Exception: pass
        try:
            y = t.encode('latin1', errors='ignore').decode('gb18030', errors='ignore')
            if has_chinese(y): return y
        except Exception: pass
        return t
    s.loc[m] = [_fix_one(v) for v in s.loc[m]]
    return s

def write_dta_smart(df: pd.DataFrame, out_path: Path, var_labels=None):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Original notebook comment normalized for the public code archive.
    cols = list(df.columns); new_cols, used = [], set()
    for c in cols:
        base = re.sub(r"[^0-9A-Za-z_]", "_", str(c))[:32]
        name, i = base, 1
        while name in used:
            suf = f"_{i}"; name = base[:32-len(suf)] + suf; i += 1
        new_cols.append(name); used.add(name)
    if new_cols != cols: df = df.rename(columns=dict(zip(cols, new_cols)))

    try:
        import pyreadstat
        for ver in (119, 118):
            kwargs = {"version": ver}
            if var_labels and "variable_labels" in inspect.signature(pyreadstat.write_dta).parameters:
                kwargs["variable_labels"] = {k: var_labels.get(k, "") for k in df.columns}
            try:
                pyreadstat.write_dta(df, str(out_path), **kwargs)
                print("[INFO] Notebook progress message.")
                return
            except Exception as e:
                last = e
        print("[INFO] Notebook progress message.", last)
    except Exception as e:
        print("[INFO] Notebook progress message.", e)

    df.to_stata(out_path, write_index=False, version=118)
    print("[INFO] Notebook progress message.", out_path)

# =============================================================================
demog = read_dta_smart(DEMOG)
psu   = read_dta_smart(PSU)

# =============================================================================
id_map = {
    "ID":          find_col(demog, "ID","Pid","PID","pid","personid"),
    "householdID": find_col(demog, "householdID","HHID","hhid","HID","hid","houseid"),
    "communityID": find_col(demog, "communityID","CID","cid","psu","PSU"),
}
for std, real in list(id_map.items()):
    if real and real != std:
        demog = demog.rename(columns={real: std})

for key, width in (("householdID",9), ("communityID",7), ("ID",11)):
    if key in demog.columns: demog[key] = canon_id_fixed(demog[key], width)
    else: demog[key] = pd.Series(np.nan, index=demog.index, dtype="object")

# =============================================================================
# Original notebook comment normalized for the public code archive.
col_zba002_1 = find_col(demog, "zba002_1", "ZBA002_1")
col_ba002_1  = find_col(demog, "ba002_1", "^ba002_?1$")
col_zba002   = find_col(demog, "zba002", "ZBA002")
col_ba002    = find_col(demog, "^ba002$")

byr_z1 = pd.to_numeric(demog[col_zba002_1], errors="coerce") if col_zba002_1 else pd.Series(np.nan, index=demog.index)
byr_b1 = pd.to_numeric(demog[col_ba002_1],  errors="coerce") if col_ba002_1  else pd.Series(np.nan, index=demog.index)
byr_z  = pd.to_numeric(demog[col_zba002],   errors="coerce") if col_zba002   else pd.Series(np.nan, index=demog.index)
byr_b  = pd.to_numeric(demog[col_ba002],    errors="coerce") if col_ba002    else pd.Series(np.nan, index=demog.index)

def clamp_year(s):
    return s.where((s>=1900) & (s<=SURVEY_YEAR), np.nan)

byr_candidates = [clamp_year(x) for x in (byr_z1, byr_b1, byr_z, byr_b)]
birth_year_report = None
for s in byr_candidates:
    birth_year_report = s if birth_year_report is None else birth_year_report.combine_first(s)

# Original notebook comment normalized for the public code archive.
col_age = find_col(demog, "ba004","BA004","zba004","ZBA004")
age_self = pd.to_numeric(demog[col_age], errors="coerce") if col_age else pd.Series(np.nan, index=demog.index)
age_self = age_self.where((age_self>=0) & (age_self<=120), np.nan)

# Original notebook comment normalized for the public code archive.
byr_from_age = np.floor(SURVEY_YEAR - age_self).astype("float")
byr_from_age = clamp_year(byr_from_age)

# Original notebook comment normalized for the public code archive.
birth_year = pd.Series(np.nan, index=demog.index, dtype="float")
both_ok   = birth_year_report.notna() & byr_from_age.notna()
only_rep  = birth_year_report.notna() & ~byr_from_age.notna()
only_age  = ~birth_year_report.notna() & byr_from_age.notna()

birth_year.loc[both_ok]  = np.minimum(birth_year_report.loc[both_ok], byr_from_age.loc[both_ok])
birth_year.loc[only_rep] = birth_year_report.loc[only_rep]
birth_year.loc[only_age] = byr_from_age.loc[only_age]

age_2013 = (SURVEY_YEAR - birth_year).where(birth_year.notna(), np.nan)

# =============================================================================
col_comm_psu = find_col(psu, "communityID","CID","cid","psu","PSU")
if col_comm_psu and col_comm_psu != "communityID":
    psu = psu.rename(columns={col_comm_psu: "communityID"})
psu["communityID"] = canon_id_fixed(psu["communityID"], 7)

for col in ("province","city"):
    if col in psu.columns and psu[col].dtype == object:
        sample = "".join(psu[col].dropna().astype(str).head(50).tolist())
        if looks_mojibake(sample) and not has_chinese(sample):
            print("[INFO] Notebook progress message.")
            psu[col] = fix_mojibake_series(psu[col])

keep_cols = [c for c in ["communityID","province","city","urban_nbs","areatype"] if c in psu.columns]
psu_slim = psu[keep_cols].drop_duplicates(subset=["communityID"]) if "communityID" in keep_cols else psu[keep_cols].copy()

# =============================================================================
out = demog[["ID","householdID","communityID"]].copy()
out["zba002_1"] = byr_z1
out["ba002_1"]  = byr_b1
out["zba002"]   = byr_z
out["ba002"]    = byr_b
out["ba004"]    = age_self
out["出生年"]     = birth_year
out["年龄"]      = age_2013

if "communityID" in psu_slim.columns:
    out = out.merge(psu_slim, on="communityID", how="left")

# =============================================================================
OUT_DIR.mkdir(parents=True, exist_ok=True)
# Original notebook comment normalized for the public code archive.
cn2en = {"出生年":"birth_year", "年龄":"age_2013"}
out_dta = out.rename(columns=cn2en)
var_labels = {
    "ID":"ID","householdID":"householdID","communityID":"communityID",
    "zba002_1":"上轮记录的出生年(zba002_1)","ba002_1":"本轮记录的出生年(ba002_1)",
    "zba002":"上轮出生年(zba002)","ba002":"本轮出生年(ba002)",
    "ba004":"自报年龄(ba004/BA004/zba004)","birth_year":"出生年","age_2013":"年龄(2013-出生年)",
    "province":"省","city":"市","urban_nbs":"国家统计局城乡","areatype":"地区类型",
}
write_dta_smart(out_dta, OUT_DTA, var_labels=var_labels)
out.to_excel(OUT_XLSX, index=False)
print("[INFO] Notebook progress message.", OUT_XLSX)

# =============================================================================
n_all = len(out); n_byr = out["出生年"].notna().sum(); n_age = out["年龄"].notna().sum()
print("[INFO] Notebook progress message.")
print(out[["province","city"]].dropna(how="all").head(5))




# =============================================================================
# Source notebook
# =============================================================================
# record_type : wave_step
# year        : 2015
# step        : 3
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 03_wave_age_region.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 3
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 03_wave_age_region.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import re
import inspect
import numpy as np
import pandas as pd
from pathlib import Path

# =============================================================================
BASE_2015 = Path(r"E:\project_flood_impact_assessment\老年人健康\CHARLS\charls原版数据\原始数据+问卷2011~2020\2015\CHARLS2015r")
OUT_DIR   = Path(r"E:\impact_assessment_child_order\older\health\2015")
OUT_DTA   = OUT_DIR / "2015_age_region.dta"
OUT_XLSX  = OUT_DIR / "2015_age_region.xlsx"
SURVEY_YEAR = 2015

# =============================================================================
def find_file(root: Path, filename: str) -> Path | None:
    """Archived notebook note for 03_wave_age_region.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    cand = []
    if not root.exists():
        return None
    low = filename.lower()
    for p in root.rglob("*"):
        if p.is_file() and p.name.lower() == low:
            cand.append(p)
    if not cand:
        return None
    # Original notebook comment normalized for the public code archive.
    def score(p: Path):
        s = 0
        key_parts = ["dataset", "household", "community", "questionnaire", "data"]
        s += sum(k in p.as_posix().lower() for k in key_parts) * 10
        s += len(p.as_posix())
        return s
    cand.sort(key=score, reverse=True)
    return cand[0]

def read_dta_smart(path, columns=None):
    """Archived notebook note for 03_wave_age_region.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    try:
        import pyreadstat
        df, meta = pyreadstat.read_dta(str(path), apply_value_formats=False, usecols=columns)
        print("[INFO] Notebook progress message.")
        return df
    except Exception as e:
        print("[INFO] Notebook progress message.")
        df = pd.read_stata(str(path), convert_categoricals=False, columns=columns)
        print("[INFO] Notebook progress message.")
        return df

def _clean_to_str(s: pd.Series) -> pd.Series:
    s = pd.Series(s, dtype="object")
    m = s.isna()
    sc = s[~m].astype(str).str.strip()
    sc = sc.str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = sc
    s.loc[m] = np.nan
    return s

def canon_id_fixed(s: pd.Series, width: int) -> pd.Series:
    s = _clean_to_str(s)
    m = s.notna()
    s.loc[m] = s.loc[m].astype(str).str.zfill(width)
    return s

def find_col(df: pd.DataFrame, *candidates):
    """Archived notebook note for 03_wave_age_region.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    low = {c.lower(): c for c in df.columns}
    # Original notebook comment normalized for the public code archive.
    for cand in candidates:
        if cand and not cand.startswith("^") and cand.lower() in low:
            return low[cand.lower()]
    # Original notebook comment normalized for the public code archive.
    for cand in candidates:
        if cand and cand.startswith("^"):
            pat = re.compile(cand, flags=re.I)
            for c in df.columns:
                if pat.match(c):
                    return c
    return None

# Original notebook comment normalized for the public code archive.
BAD_CHARS = "ÃÂÅÄÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞ±²³¼½¾"
def looks_mojibake(sample: str) -> bool:
    return any(ch in sample for ch in BAD_CHARS)
def has_chinese(sample: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", sample))
def fix_mojibake_series(s: pd.Series) -> pd.Series:
    s = s.astype(object)
    m = s.notna()
    def _fix_one(val):
        if val is None: return val
        t = str(val)
        try:
            y = t.encode('latin1', errors='ignore').decode('gbk', errors='ignore')
            if has_chinese(y): return y
        except Exception: pass
        try:
            y = t.encode('latin1', errors='ignore').decode('gb18030', errors='ignore')
            if has_chinese(y): return y
        except Exception: pass
        return t
    s.loc[m] = [_fix_one(v) for v in s.loc[m]]
    return s

def write_dta_smart(df: pd.DataFrame, out_path: Path, var_labels=None):
    """Archived notebook note for 03_wave_age_region.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Original notebook comment normalized for the public code archive.
    cols = list(df.columns)
    new_cols, used = [], set()
    for c in cols:
        base = re.sub(r"[^0-9A-Za-z_]", "_", str(c))[:32]
        name, i = base, 1
        while name in used:
            suf = f"_{i}"
            name = base[:32-len(suf)] + suf
            i += 1
        new_cols.append(name); used.add(name)
    if new_cols != cols:
        df = df.rename(columns=dict(zip(cols, new_cols)))

    try:
        import pyreadstat
        for ver in (119, 118):
            kwargs = {"version": ver}
            if var_labels and "variable_labels" in inspect.signature(pyreadstat.write_dta).parameters:
                kwargs["variable_labels"] = {k: var_labels.get(k, "") for k in df.columns}
            try:
                pyreadstat.write_dta(df, str(out_path), **kwargs)
                print("[INFO] Notebook progress message.")
                return
            except Exception as e:
                last = e
        print("[INFO] Notebook progress message.", last)
    except Exception as e:
        print("[INFO] Notebook progress message.", e)

    try:
        df.to_stata(out_path, write_index=False, version=118)
        print("[INFO] Notebook progress message.", out_path)
        return
    except Exception as e:
        print("[INFO] Notebook progress message.", e)
    # Original notebook comment normalized for the public code archive.
    df2 = df.copy()
    for c in df2.select_dtypes(include=["object"]).columns:
        df2[c] = df2[c].astype(str).str.encode("latin-1", "ignore").str.decode("latin-1")
    df2.to_stata(out_path, write_index=False, version=117)
    print("[INFO] Notebook progress message.", out_path, "[INFO] Notebook progress message.")

# =============================================================================
demog_path = find_file(BASE_2015, "demographic_background.dta")
psu_path   = find_file(BASE_2015, "psu.dta")

if demog_path is None:
    raise FileNotFoundError(f"未找到 demographic_background.dta（搜索根：{BASE_2015}）")
if psu_path is None:
    print("[INFO] Notebook progress message.")

demog = read_dta_smart(demog_path)
psu   = read_dta_smart(psu_path) if psu_path else None

# =============================================================================
id_map = {
    "ID":          find_col(demog, "ID","Pid","PID","pid","personid"),
    "householdID": find_col(demog, "householdID","HHID","hhid","HID","hid","houseid"),
    "communityID": find_col(demog, "communityID","CID","cid","psu","PSU"),
}
for std, real in list(id_map.items()):
    if real and real != std:
        demog = demog.rename(columns={real: std})

for key, width in (("householdID",9), ("communityID",7), ("ID",11)):
    if key in demog.columns:
        demog[key] = canon_id_fixed(demog[key], width)
    else:
        demog[key] = pd.Series(np.nan, index=demog.index, dtype="object")

# =============================================================================
# Original notebook comment normalized for the public code archive.
col_ba002     = find_col(demog, "BA002")               # Original notebook comment normalized for the public code archive.
col_ba002_1   = find_col(demog, "BA002_1", "^BA002_?1$")
col_ba004_y   = find_col(demog, "BA004_W3_1", "^BA004_?W3_?1$")

ba002_val     = pd.to_numeric(demog[col_ba002], errors="coerce") if col_ba002 else pd.Series(np.nan, index=demog.index)
byr_true      = pd.to_numeric(demog[col_ba002_1], errors="coerce") if col_ba002_1 else pd.Series(np.nan, index=demog.index)
byr_id        = pd.to_numeric(demog[col_ba004_y], errors="coerce") if col_ba004_y else pd.Series(np.nan, index=demog.index)

def clamp_year(s):
    return s.where((s>=1900) & (s<=SURVEY_YEAR), np.nan)

byr_true = clamp_year(byr_true)
byr_id   = clamp_year(byr_id)

# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
birth_year = pd.Series(np.nan, index=demog.index, dtype="float")

mask_ba002_is2 = (ba002_val == 2)
mask_ba002_is1 = (ba002_val == 1)

# Original notebook comment normalized for the public code archive.
birth_year.loc[mask_ba002_is2] = byr_true.loc[mask_ba002_is2]

# Original notebook comment normalized for the public code archive.
birth_year.loc[mask_ba002_is1] = byr_id.loc[mask_ba002_is1]

# Original notebook comment normalized for the public code archive.
mask_ba002_na = ba002_val.isna()
birth_year.loc[mask_ba002_na & byr_true.notna()] = byr_true.loc[mask_ba002_na & byr_true.notna()]
birth_year.loc[mask_ba002_na & birth_year.isna()] = byr_id.loc[mask_ba002_na & birth_year.isna()]

# Original notebook comment normalized for the public code archive.
birth_year = clamp_year(birth_year)
age_2015   = (SURVEY_YEAR - birth_year).where(birth_year.notna(), np.nan)

# =============================================================================
if psu is not None:
    col_comm_psu = find_col(psu, "communityID","CID","cid","psu","PSU")
    if col_comm_psu and col_comm_psu != "communityID":
        psu = psu.rename(columns={col_comm_psu: "communityID"})
    psu["communityID"] = canon_id_fixed(psu["communityID"], 7)

    for col in ("province","city"):
        if col in psu.columns and psu[col].dtype == object:
            sample = "".join(psu[col].dropna().astype(str).head(50).tolist())
            if looks_mojibake(sample) and not has_chinese(sample):
                print("[INFO] Notebook progress message.")
                psu[col] = fix_mojibake_series(psu[col])

    keep_cols = [c for c in ["communityID","province","city","urban_nbs","areatype"] if c in psu.columns]
    psu_slim = psu[keep_cols].drop_duplicates(subset=["communityID"]) if "communityID" in keep_cols else psu[keep_cols].copy()
else:
    psu_slim = None

# =============================================================================
out = demog[["ID","householdID","communityID"]].copy()
# Original notebook comment normalized for the public code archive.
out["BA002"]   = ba002_val
out["BA002_1"] = byr_true
out["BA004_W3_1"] = byr_id
out["出生年"]   = birth_year
out["年龄"]    = age_2015

if psu_slim is not None:
    out = out.merge(psu_slim, on="communityID", how="left")

# =============================================================================
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Original notebook comment normalized for the public code archive.
cn2en = {"出生年":"birth_year", "年龄":"age_2015"}
out_dta = out.rename(columns=cn2en)
var_labels = {
    "ID":"ID","householdID":"householdID","communityID":"communityID",
    "BA002":"真实生日选择(1=与证件一致/2=填写真实生日)",
    "BA002_1":"真实出生年(BA002_1)",
    "BA004_W3_1":"证件/户口本出生年(BA004_W3_1)",
    "birth_year":"出生年(综合 BA002/BA004_W3_1)",
    "age_2015":"年龄(2015-出生年)",
    "province":"省","city":"市","urban_nbs":"国家统计局城乡","areatype":"地区类型",
}
write_dta_smart(out_dta, OUT_DTA, var_labels=var_labels)

# Original notebook comment normalized for the public code archive.
out.to_excel(OUT_XLSX, index=False)
print("[INFO] Notebook progress message.", OUT_XLSX)

# =============================================================================
n_all = len(out); n_byr = out["出生年"].notna().sum(); n_age = out["年龄"].notna().sum()
print("[INFO] Notebook progress message.")
print(out[["province","city"]].dropna(how="all").head(5))




# =============================================================================
# Source notebook
# =============================================================================
# record_type : wave_step
# year        : 2018
# step        : 3
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 03_wave_age_region.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 1
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 03_wave_age_region.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import re
import inspect
import numpy as np
import pandas as pd
from pathlib import Path

# =============================================================================
BASE_2018 = Path(r"E:\project_flood_impact_assessment\老年人健康\CHARLS\charls原版数据\原始数据+问卷2011~2020\2018\CHARLS2018r")
OUT_DIR   = Path(r"E:\impact_assessment_child_order\older\health\2018")
OUT_DTA   = OUT_DIR / "2018_age_region.dta"
OUT_XLSX  = OUT_DIR / "2018_age_region.xlsx"
SURVEY_YEAR = 2018

# =============================================================================
def find_file(root: Path, filename: str) -> Path | None:
    """Archived notebook note for 03_wave_age_region.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    cand = []
    if not root.exists():
        return None
    low = filename.lower()
    for p in root.rglob("*"):
        if p.is_file() and p.name.lower() == low:
            cand.append(p)
    if not cand:
        return None
    # Original notebook comment normalized for the public code archive.
    def score(p: Path):
        s = 0
        key_parts = ["dataset", "household", "community", "questionnaire", "data"]
        s += sum(k in p.as_posix().lower() for k in key_parts) * 10
        s += len(p.as_posix())
        return s
    cand.sort(key=score, reverse=True)
    return cand[0]

def read_dta_smart(path, columns=None):
    """Archived notebook note for 03_wave_age_region.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    try:
        import pyreadstat
        df, meta = pyreadstat.read_dta(str(path), apply_value_formats=False, usecols=columns)
        print("[INFO] Notebook progress message.")
        return df
    except Exception as e:
        print("[INFO] Notebook progress message.")
        df = pd.read_stata(str(path), convert_categoricals=False, columns=columns)
        print("[INFO] Notebook progress message.")
        return df

def _clean_to_str(s: pd.Series) -> pd.Series:
    s = pd.Series(s, dtype="object")
    m = s.isna()
    sc = s[~m].astype(str).str.strip()
    sc = sc.str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = sc
    s.loc[m] = np.nan
    return s

def canon_id_fixed(s: pd.Series, width: int) -> pd.Series:
    s = _clean_to_str(s)
    m = s.notna()
    s.loc[m] = s.loc[m].astype(str).str.zfill(width)
    return s

def find_col(df: pd.DataFrame, *candidates):
    """Archived notebook note for 03_wave_age_region.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    low = {c.lower(): c for c in df.columns}
    # Original notebook comment normalized for the public code archive.
    for cand in candidates:
        if cand and not cand.startswith("^") and cand.lower() in low:
            return low[cand.lower()]
    # Original notebook comment normalized for the public code archive.
    for cand in candidates:
        if cand and cand.startswith("^"):
            pat = re.compile(cand, flags=re.I)
            for c in df.columns:
                if pat.match(c):
                    return c
    return None

# Original notebook comment normalized for the public code archive.
BAD_CHARS = "ÃÂÅÄÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞ±²³¼½¾"
def looks_mojibake(sample: str) -> bool:
    return any(ch in sample for ch in BAD_CHARS)
def has_chinese(sample: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", sample))
def fix_mojibake_series(s: pd.Series) -> pd.Series:
    s = s.astype(object)
    m = s.notna()
    def _fix_one(val):
        if val is None: return val
        t = str(val)
        try:
            y = t.encode('latin1', errors='ignore').decode('gbk', errors='ignore')
            if has_chinese(y): return y
        except Exception: pass
        try:
            y = t.encode('latin1', errors='ignore').decode('gb18030', errors='ignore')
            if has_chinese(y): return y
        except Exception: pass
        return t
    s.loc[m] = [_fix_one(v) for v in s.loc[m]]
    return s

def write_dta_smart(df: pd.DataFrame, out_path: Path, var_labels=None):
    """Archived notebook note for 03_wave_age_region.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Original notebook comment normalized for the public code archive.
    cols = list(df.columns)
    new_cols, used = [], set()
    for c in cols:
        base = re.sub(r"[^0-9A-Za-z_]", "_", str(c))[:32]
        name, i = base, 1
        while name in used:
            suf = f"_{i}"
            name = base[:32-len(suf)] + suf
            i += 1
        new_cols.append(name); used.add(name)
    if new_cols != cols:
        df = df.rename(columns=dict(zip(cols, new_cols)))

    try:
        import pyreadstat
        for ver in (119, 118):
            kwargs = {"version": ver}
            if var_labels and "variable_labels" in inspect.signature(pyreadstat.write_dta).parameters:
                kwargs["variable_labels"] = {k: var_labels.get(k, "") for k in df.columns}
            try:
                pyreadstat.write_dta(df, str(out_path), **kwargs)
                print("[INFO] Notebook progress message.")
                return
            except Exception as e:
                last = e
        print("[INFO] Notebook progress message.", last)
    except Exception as e:
        print("[INFO] Notebook progress message.", e)

    try:
        df.to_stata(out_path, write_index=False, version=118)
        print("[INFO] Notebook progress message.", out_path)
        return
    except Exception as e:
        print("[INFO] Notebook progress message.", e)
    # Original notebook comment normalized for the public code archive.
    df2 = df.copy()
    for c in df2.select_dtypes(include=["object"]).columns:
        df2[c] = df2[c].astype(str).str.encode("latin-1", "ignore").str.decode("latin-1")
    df2.to_stata(out_path, write_index=False, version=117)
    print("[INFO] Notebook progress message.", out_path, "[INFO] Notebook progress message.")

# =============================================================================
demog_path = find_file(BASE_2018, "demographic_background.dta")
psu_path   = find_file(BASE_2018, "psu.dta")

if demog_path is None:
    raise FileNotFoundError(f"未找到 demographic_background.dta（搜索根：{BASE_2018}）")
if psu_path is None:
    print("[INFO] Notebook progress message.")

demog = read_dta_smart(demog_path)
psu   = read_dta_smart(psu_path) if psu_path else None

# =============================================================================
id_map = {
    "ID":          find_col(demog, "ID","Pid","PID","pid","personid"),
    "householdID": find_col(demog, "householdID","HHID","hhid","HID","hid","houseid"),
    "communityID": find_col(demog, "communityID","CID","cid","psu","PSU"),
}
for std, real in list(id_map.items()):
    if real and real != std:
        demog = demog.rename(columns={real: std})

for key, width in (("householdID",9), ("communityID",7), ("ID",11)):
    if key in demog.columns:
        demog[key] = canon_id_fixed(demog[key], width)
    else:
        demog[key] = pd.Series(np.nan, index=demog.index, dtype="object")

# =============================================================================
# 2018（Wave 4）：
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
col_ba005_w4 = find_col(demog, "ba005_w4", "BA005_W4")
col_ba002_1  = find_col(demog, "ba002_1", "BA002_1", "^ba002_?1$")
col_ba004_y  = find_col(demog, "ba004_w3_1", "BA004_W3_1", "^ba004_?w3_?1$")

flag_same    = pd.to_numeric(demog[col_ba005_w4], errors="coerce") if col_ba005_w4 else pd.Series(np.nan, index=demog.index)
byr_true     = pd.to_numeric(demog[col_ba002_1],  errors="coerce") if col_ba002_1  else pd.Series(np.nan, index=demog.index)
byr_id       = pd.to_numeric(demog[col_ba004_y],  errors="coerce") if col_ba004_y  else pd.Series(np.nan, index=demog.index)

def clamp_year(s):
    return s.where((s>=1900) & (s<=SURVEY_YEAR), np.nan)

byr_true = clamp_year(byr_true)
byr_id   = clamp_year(byr_id)

birth_year = pd.Series(np.nan, index=demog.index, dtype="float")

# Original notebook comment normalized for the public code archive.
birth_year.loc[(flag_same == 2)] = byr_true.loc[(flag_same == 2)]

# Original notebook comment normalized for the public code archive.
birth_year.loc[(flag_same == 1)] = byr_id.loc[(flag_same == 1)]

# Original notebook comment normalized for the public code archive.
mask_na = flag_same.isna()
birth_year.loc[mask_na & byr_true.notna()] = byr_true.loc[mask_na & byr_true.notna()]
birth_year.loc[mask_na & birth_year.isna()] = byr_id.loc[mask_na & birth_year.isna()]

birth_year = clamp_year(birth_year)
age_2018   = (SURVEY_YEAR - birth_year).where(birth_year.notna(), np.nan)

# =============================================================================
if psu is not None:
    col_comm_psu = find_col(psu, "communityID","CID","cid","psu","PSU")
    if col_comm_psu and col_comm_psu != "communityID":
        psu = psu.rename(columns={col_comm_psu: "communityID"})
    psu["communityID"] = canon_id_fixed(psu["communityID"], 7)

    for col in ("province","city"):
        if col in psu.columns and psu[col].dtype == object:
            sample = "".join(psu[col].dropna().astype(str).head(50).tolist())
            if looks_mojibake(sample) and not has_chinese(sample):
                print("[INFO] Notebook progress message.")
                psu[col] = fix_mojibake_series(psu[col])

    keep_cols = [c for c in ["communityID","province","city","urban_nbs","areatype"] if c in psu.columns]
    psu_slim = psu[keep_cols].drop_duplicates(subset=["communityID"]) if "communityID" in keep_cols else psu[keep_cols].copy()
else:
    psu_slim = None

# =============================================================================
out = demog[["ID","householdID","communityID"]].copy()
# Original notebook comment normalized for the public code archive.
out["ba005_w4"]   = flag_same
out["ba002_1"]    = byr_true
out["ba004_w3_1"] = byr_id
out["出生年"]       = birth_year
out["年龄"]        = age_2018

if psu_slim is not None:
    out = out.merge(psu_slim, on="communityID", how="left")

# =============================================================================
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Original notebook comment normalized for the public code archive.
cn2en = {"出生年":"birth_year", "年龄":"age_2018"}
out_dta = out.rename(columns=cn2en)
var_labels = {
    "ID":"ID","householdID":"householdID","communityID":"communityID",
    "ba005_w4":"实际生日与证件是否一致(1=一致/2=不同)",
    "ba002_1":"实际出生年(ba002_1)",
    "ba004_w3_1":"证件/户口本出生年(ba004_w3_1)",
    "birth_year":"出生年(综合 ba005_w4/ba002_1/ba004_w3_1)",
    "age_2018":"年龄(2018-出生年)",
    "province":"省","city":"市","urban_nbs":"国家统计局城乡","areatype":"地区类型",
}
write_dta_smart(out_dta, OUT_DTA, var_labels=var_labels)

# Original notebook comment normalized for the public code archive.
out.to_excel(OUT_XLSX, index=False)
print("[INFO] Notebook progress message.", OUT_XLSX)

# =============================================================================
n_all = len(out); n_byr = out["出生年"].notna().sum(); n_age = out["年龄"].notna().sum()
print("[INFO] Notebook progress message.")
print(out[["province","city"]].dropna(how="all").head(5))




# =============================================================================
# Source notebook
# =============================================================================
# record_type : wave_step
# year        : 2020
# step        : 3
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 03_wave_age_region.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 1
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 03_wave_age_region.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import re, inspect
import numpy as np
import pandas as pd
from pathlib import Path

# =============================================================================
BASE_2020 = Path(r"E:\project_flood_impact_assessment\老年人健康\CHARLS\charls原版数据\原始数据+问卷2011~2020\2020\CHARLS2020r")
OUT_DIR   = Path(r"E:\impact_assessment_child_order\older\health\2020")
OUT_DTA   = OUT_DIR / "2020_age_region.dta"
OUT_XLSX  = OUT_DIR / "2020_age_region.xlsx"
SURVEY_YEAR = 2020

# =============================================================================
def find_file(root: Path, filename: str) -> Path | None:
    cand = []
    if not root.exists(): return None
    low = filename.lower()
    for p in root.rglob("*"):
        if p.is_file() and p.name.lower() == low:
            cand.append(p)
    if not cand: return None
    def score(p: Path):
        s = 0
        s += sum(k in p.as_posix().lower() for k in ["dataset","household","community","questionnaire","data"]) * 10
        s += len(p.as_posix())
        return s
    cand.sort(key=score, reverse=True)
    return cand[0]

def read_dta_smart(path, columns=None):
    try:
        import pyreadstat
        df, meta = pyreadstat.read_dta(str(path), apply_value_formats=False, usecols=columns)
        print("[INFO] Notebook progress message.")
        return df
    except Exception as e:
        print("[INFO] Notebook progress message.")
        df = pd.read_stata(str(path), convert_categoricals=False, columns=columns)
        print("[INFO] Notebook progress message.")
        return df

def _clean_to_str(s: pd.Series) -> pd.Series:
    s = pd.Series(s, dtype="object"); m = s.isna()
    sc = s[~m].astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = sc; s.loc[m] = np.nan
    return s

def canon_id_fixed(s: pd.Series, width: int) -> pd.Series:
    s = _clean_to_str(s); m = s.notna()
    s.loc[m] = s.loc[m].astype(str).str.zfill(width)
    return s

def find_col(df: pd.DataFrame, *candidates):
    low = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand and not cand.startswith("^") and cand.lower() in low:
            return low[cand.lower()]
    for cand in candidates:
        if cand and cand.startswith("^"):
            pat = re.compile(cand, flags=re.I)
            for c in df.columns:
                if pat.match(c): return c
    return None

# Original notebook comment normalized for the public code archive.
BAD_CHARS = "ÃÂÅÄÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞ±²³¼½¾"
def looks_mojibake(sample: str) -> bool: return any(ch in sample for ch in BAD_CHARS)
def has_chinese(sample: str) -> bool:    return bool(re.search(r"[\u4e00-\u9fff]", sample))
def fix_mojibake_series(s: pd.Series) -> pd.Series:
    s = s.astype(object); m = s.notna()
    def _fix_one(v):
        if v is None: return v
        t = str(v)
        try:
            y = t.encode("latin1","ignore").decode("gbk","ignore")
            if has_chinese(y): return y
        except Exception: pass
        try:
            y = t.encode("latin1","ignore").decode("gb18030","ignore")
            if has_chinese(y): return y
        except Exception: pass
        return t
    s.loc[m] = [_fix_one(v) for v in s.loc[m]]
    return s

def write_dta_smart(df: pd.DataFrame, out_path: Path, var_labels=None):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cols = list(df.columns); new_cols, used = [], set()
    for c in cols:
        base = re.sub(r"[^0-9A-Za-z_]", "_", str(c))[:32]
        name, i = base, 1
        while name in used:
            suf = f"_{i}"; name = base[:32-len(suf)] + suf; i += 1
        new_cols.append(name); used.add(name)
    if new_cols != cols: df = df.rename(columns=dict(zip(cols, new_cols)))

    try:
        import pyreadstat
        for ver in (119,118):
            kwargs = {"version": ver}
            if var_labels and "variable_labels" in inspect.signature(pyreadstat.write_dta).parameters:
                kwargs["variable_labels"] = {k: var_labels.get(k, "") for k in df.columns}
            try:
                pyreadstat.write_dta(df, str(out_path), **kwargs)
                print("[INFO] Notebook progress message.")
                return
            except Exception as e:
                last = e
        print("[INFO] Notebook progress message.", last)
    except Exception as e:
        print("[INFO] Notebook progress message.", e)

    try:
        df.to_stata(out_path, write_index=False, version=118)
        print("[INFO] Notebook progress message.", out_path)
        return
    except Exception as e:
        print("[INFO] Notebook progress message.", e)
    df2 = df.copy()
    for c in df2.select_dtypes(include=["object"]).columns:
        df2[c] = df2[c].astype(str).str.encode("latin-1","ignore").str.decode("latin-1")
    df2.to_stata(out_path, write_index=False, version=117)
    print("[INFO] Notebook progress message.", out_path, "[INFO] Notebook progress message.")

# =============================================================================
demog_path = find_file(BASE_2020, "demographic_background.dta")
psu_path   = find_file(BASE_2020, "psu.dta")
if demog_path is None:
    raise FileNotFoundError(f"未找到 demographic_background.dta（搜索根：{BASE_2020}）")
if psu_path is None:
    print("[INFO] Notebook progress message.")

demog = read_dta_smart(demog_path)
psu   = read_dta_smart(psu_path) if psu_path else None

# =============================================================================
id_map = {
    "ID":          find_col(demog, "ID","Pid","PID","pid","personid"),
    "householdID": find_col(demog, "householdID","HHID","hhid","HID","hid","houseid"),
    "communityID": find_col(demog, "communityID","CID","cid","psu","PSU"),
}
for std, real in list(id_map.items()):
    if real and real != std:
        demog = demog.rename(columns={real: std})

for key, width in (("householdID",9),("communityID",7),("ID",11)):
    if key in demog.columns: demog[key] = canon_id_fixed(demog[key], width)
    else: demog[key] = pd.Series(np.nan, index=demog.index, dtype="object")

# =============================================================================
# Original notebook comment normalized for the public code archive.
col_ba003_1 = find_col(demog, "BA003_1", "ba003_1", "^ba003_?1$")
byr_2020    = pd.to_numeric(demog[col_ba003_1], errors="coerce") if col_ba003_1 else pd.Series(np.nan, index=demog.index)
# Original notebook comment normalized for the public code archive.
byr_2020 = byr_2020.where((byr_2020>=1900) & (byr_2020<=2000), np.nan)

# Original notebook comment normalized for the public code archive.
col_zr = find_col(demog, "ZRBirthYear", "zrbirthyear", "^zr.*birth.*year$")
byr_prev = pd.to_numeric(demog[col_zr], errors="coerce") if col_zr else pd.Series(np.nan, index=demog.index)
byr_prev = byr_prev.where((byr_prev>=1900) & (byr_prev<=SURVEY_YEAR), np.nan)

birth_year = byr_2020.copy()
birth_year = birth_year.where(birth_year.notna(), byr_prev)

age_2020 = (SURVEY_YEAR - birth_year).where(birth_year.notna(), np.nan)

# Original notebook comment normalized for the public code archive.
col_ba004_1 = find_col(demog, "BA004_1", "ba004_1")
col_ba004_2 = find_col(demog, "BA004_2", "ba004_2")
col_ba004_3 = find_col(demog, "BA004_3", "ba004_3")
col_ba005   = find_col(demog, "BA005", "ba005")
col_ba005_1 = find_col(demog, "BA005_1", "ba005_1")

# =============================================================================
if psu is not None:
    col_comm_psu = find_col(psu, "communityID","CID","cid","psu","PSU")
    if col_comm_psu and col_comm_psu != "communityID":
        psu = psu.rename(columns={col_comm_psu: "communityID"})
    psu["communityID"] = canon_id_fixed(psu["communityID"], 7)

    for col in ("province","city"):
        if col in psu.columns and psu[col].dtype == object:
            sample = "".join(psu[col].dropna().astype(str).head(50).tolist())
            if looks_mojibake(sample) and not has_chinese(sample):
                print("[INFO] Notebook progress message.")
                psu[col] = fix_mojibake_series(psu[col])

    keep_cols = [c for c in ["communityID","province","city","urban_nbs","areatype"] if c in psu.columns]
    psu_slim = psu[keep_cols].drop_duplicates(subset=["communityID"]) if "communityID" in keep_cols else psu[keep_cols].copy()
else:
    psu_slim = None

# =============================================================================
out = demog[["ID","householdID","communityID"]].copy()
out["BA003_1"]  = birth_year   # Original notebook comment normalized for the public code archive.
out["出生年"]      = birth_year
out["年龄"]       = age_2020
# Original notebook comment normalized for the public code archive.
if col_ba004_1: out["BA004_1"] = demog[col_ba004_1]
if col_ba004_2: out["BA004_2"] = demog[col_ba004_2]
if col_ba004_3: out["BA004_3"] = demog[col_ba004_3]
if col_ba005:   out["BA005"]   = pd.to_numeric(demog[col_ba005], errors="coerce")
if col_ba005_1: out["BA005_1"] = demog[col_ba005_1]

if psu_slim is not None:
    out = out.merge(psu_slim, on="communityID", how="left")

# =============================================================================
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Original notebook comment normalized for the public code archive.
cn2en = {"出生年":"birth_year", "年龄":"age_2020"}
out_dta = out.rename(columns=cn2en)
var_labels = {
    "ID":"ID","householdID":"householdID","communityID":"communityID",
    "BA003_1":"真实出生年(BA003_1)",
    "birth_year":"出生年(优先 BA003_1；缺失回填上轮 ZRBirthYear)",
    "age_2020":"年龄(2020-出生年)",
    "BA004_1":"访问地址-省/市/区县(BA004_1)",
    "BA004_2":"访问地址-乡/镇/街道/村/社区(BA004_2)",
    "BA004_3":"访问地址-小区/楼号/单元/门牌号(BA004_3)",
    "BA005":"访问地类型(BA005:1家庭住宅/2工作场所/3其它)",
    "BA005_1":"访问地类型-其它说明(BA005_1)",
    "province":"省","city":"市","urban_nbs":"国家统计局城乡","areatype":"地区类型",
}
write_dta_smart(out_dta, OUT_DTA, var_labels=var_labels)

# Original notebook comment normalized for the public code archive.
out.to_excel(OUT_XLSX, index=False)
print("[INFO] Notebook progress message.", OUT_XLSX)

# =============================================================================
n_all = len(out); n_byr = out["出生年"].notna().sum(); n_age = out["年龄"].notna().sum()
print("[INFO] Notebook progress message.")
print(out[["province","city"]].dropna(how='all').head(5))
