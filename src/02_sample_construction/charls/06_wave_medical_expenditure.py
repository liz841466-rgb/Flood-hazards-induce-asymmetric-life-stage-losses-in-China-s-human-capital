#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""



from __future__ import annotations
# =============================================================================
# Source notebook
# =============================================================================
# record_type : wave_step
# year        : 2011
# step        : 6
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 7
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import re
from pathlib import Path
import numpy as np
import pandas as pd

# =============================================================================
DATA_DIRS = [
    r"E:\project_flood_impact_assessment\老年人健康\CHARLS\charls原版数据\原始数据+问卷2011~2020\2011\household_and_community_questionnaire_data",
    r"E:\impact_assessment_child_order\older\health\2011",
]
OUT_DIR = Path(r"E:\impact_assessment_child_order\older\expenditure")
OUT_DTA  = OUT_DIR / "2011_Medical_investment.dta"
OUT_XLSX = OUT_DIR / "2011_Medical_investment.xlsx"

HEALTH_NAME    = "health_care_and_insurance.dta"
HOUSEHOLD_NAME = "household_income.dta"   # Original notebook comment normalized for the public code archive.

# =============================================================================
def find_data_file(fname: str) -> Path | None:
    # Original notebook comment normalized for the public code archive.
    for d in DATA_DIRS:
        p = Path(d) / fname
        if p.exists():
            return p
    # Original notebook comment normalized for the public code archive.
    for d in DATA_DIRS:
        dd = Path(d)
        if not dd.exists():
            continue
        for pp in dd.glob("*.dta"):
            if pp.name.lower() == fname.lower():
                return pp
    return None

def read_dta(path: Path) -> pd.DataFrame:
    if not path or not path.exists():
        raise FileNotFoundError(f"未找到文件：{path}")
    try:
        import pyreadstat
        df, _ = pyreadstat.read_dta(str(path), apply_value_formats=False)
        return df
    except Exception:
        return pd.read_stata(path, convert_categoricals=False)

def _clean_to_str(s: pd.Series) -> pd.Series:
    s = pd.Series(s, dtype="object")
    m = s.isna()
    t = s[~m].astype(str).str.strip()
    t = t.str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = t; s.loc[m] = np.nan
    return s

def digits_width(s: pd.Series, width: int) -> pd.Series:
    t = _clean_to_str(s).str.replace(r"\D","",regex=True)
    t = t.where(t.str.len() > 0, np.nan)
    return t.where(t.isna(), t.str[-width:].str.zfill(width)).astype("object")

def normalize_keys(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()
    low = {c.lower(): c for c in df.columns}
    def pick(*names):
        for n in names:
            if n.lower() in low: return low[n.lower()]
        return None

    c_hh  = pick("householdid","householdID","hhid")
    c_pid = pick("id","pid","PID")
    c_com = pick("communityid","communityID","commid")

    if c_hh  and c_hh  != "householdID":  df.rename(columns={c_hh :"householdID"},  inplace=True)
    if c_pid and c_pid != "ID":           df.rename(columns={c_pid:"ID"},           inplace=True)
    if c_com and c_com != "communityID":  df.rename(columns={c_com:"communityID"},  inplace=True)

    # Original notebook comment normalized for the public code archive.
    if "householdID" in df.columns:
        hh_digits = _clean_to_str(df["householdID"]).str.replace(r"\D","",regex=True)
        hh9  = hh_digits.where(hh_digits.str.len()==9,  np.nan)
        hh10 = hh_digits.where(hh_digits.str.len()==10, np.nan)
        df["householdID10"] = np.where(hh10.notna(), hh10.str.zfill(10),
                                 np.where(hh9.notna(), hh9.str.zfill(9)+"0", np.nan)).astype("object")
        df["householdID"] = hh_digits.where(hh_digits.str.len()>0, np.nan).astype("object")
    else:
        df["householdID10"] = np.nan

    # Original notebook comment normalized for the public code archive.
    if "communityID" in df.columns:
        df["communityID"] = digits_width(df["communityID"], 7)

    # Original notebook comment normalized for the public code archive.
    if "ID" in df.columns:
        id_digits = _clean_to_str(df["ID"]).str.replace(r"\D","",regex=True)
        id11 = id_digits.where(id_digits.str.len()==11, np.nan).astype("object")
        id12 = id_digits.where(id_digits.str.len()==12, np.nan).astype("object")
        pn2  = id11.str[-2:]
    else:
        id12 = pd.Series(np.nan, index=df.index, dtype="object")
        pn2  = pd.Series(np.nan, index=df.index, dtype="object")

    made = np.where(pd.Series(pn2).notna() & df["householdID10"].notna(),
                    df["householdID10"] + pn2.astype("object"), np.nan)
    df["ID12"] = pd.Series(id12, index=df.index).fillna(pd.Series(made, index=df.index)).astype("object")
    return df

def sum_by_prefix(df: pd.DataFrame, prefix: str) -> pd.Series:
    cols = [c for c in df.columns if str(c).lower().startswith(prefix.lower())]
    if not cols:
        return pd.Series(np.nan, index=df.index, dtype="float64")
    arr = df[cols].apply(pd.to_numeric, errors="coerce")
    s = arr.sum(axis=1, skipna=True)
    all_na = arr.isna().all(axis=1)
    return s.where(~all_na, np.nan)

def amount_from_switch(df: pd.DataFrame, sw_col: str, amt_col: str) -> pd.Series:
    """Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sw = pd.to_numeric(df.get(sw_col), errors="coerce")
    amt = pd.to_numeric(df.get(amt_col), errors="coerce")
    out = pd.Series(np.nan, index=df.index, dtype="float64")
    out.loc[sw == 1] = amt.loc[sw == 1]
    out.loc[sw == 2] = 0.0
    return out

# =============================================================================
def flag_has_outpt(df: pd.DataFrame) -> pd.Series:
    """Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    ed004_cols = [c for c in df.columns if re.match(r"^ed004(_\d+_?)?$", str(c), flags=re.I)
                  or re.match(r"^ed004s?\d+_?$", str(c), flags=re.I)]
    if ed004_cols:
        arr = df[ed004_cols].apply(pd.to_numeric, errors="coerce")
        has = (arr == 1).any(axis=1)
        return has.astype("int8", copy=False)
    evid = []
    evid += [c for c in df.columns if re.match(r"^ed005", str(c), flags=re.I)]
    evid += [c for c in df.columns if re.match(r"^ed006", str(c), flags=re.I)]
    evid += [c for c in df.columns if re.match(r"^ed023(_1)?$", str(c), flags=re.I)]
    if evid:
        A = df[evid].apply(pd.to_numeric, errors="coerce")
        has = A.notna() & (A != 0)
        return has.any(axis=1).astype("int8", copy=False)
    return pd.Series(np.nan, index=df.index)

def flag_inp_any(df: pd.DataFrame) -> pd.Series:
    """Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if "ee003" in df.columns:
        ee003 = pd.to_numeric(df["ee003"], errors="coerce")
        return (ee003 == 1).astype("int8", copy=False)
    evid = [c for c in df.columns if re.match(r"^ee00(4|5|6|7|8|9|24|25|26|27)(_1)?$", str(c), flags=re.I)]
    if evid:
        A = df[evid].apply(pd.to_numeric, errors="coerce")
        has = A.notna() & (A != 0)
        return has.any(axis=1).astype("int8", copy=False)
    return pd.Series(np.nan, index=df.index)

def flag_self_none(df: pd.DataFrame) -> pd.Series:
    """Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s7 = [c for c in df.columns if re.match(r"^ef001s?7_?$", str(c), flags=re.I)]
    if s7:
        v = pd.to_numeric(df[s7[0]], errors="coerce")
        return (v == 1).astype("int8", copy=False)
    ef001_cols = [c for c in df.columns if re.match(r"^ef001s?\d+_?$", str(c), flags=re.I)]
    if ef001_cols:
        any1 = (df[ef001_cols].apply(pd.to_numeric, errors="coerce") == 1).any(axis=1)
        ef2_cols = [c for c in df.columns if re.match(r"^ef002", str(c), flags=re.I)]
        ef3_cols = [c for c in df.columns if re.match(r"^ef003", str(c), flags=re.I)]
        if ef2_cols or ef3_cols:
            arr = pd.DataFrame()
            if ef2_cols: arr = pd.concat([arr, df[ef2_cols]], axis=1)
            if ef3_cols: arr = pd.concat([arr, df[ef3_cols]], axis=1)
            all_na = arr.apply(pd.to_numeric, errors="coerce").isna().all(axis=1)
            out = pd.Series(np.nan, index=df.index)
            out.loc[any1] = 0
            out.loc[~any1 & all_na] = 1
            return out.astype("float64")
    return pd.Series(np.nan, index=df.index)

def sanitize_for_stata(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    for c in d.select_dtypes(include=["Int8","Int16","Int32","Int64","UInt8","UInt16","UInt32","UInt64","boolean"]).columns:
        d[c] = d[c].astype("float64")
    for c in d.select_dtypes(include=["object","string"]).columns:
        s = d[c].astype(object)
        m = pd.isna(s); s = s.astype(str); s[m] = None
        d[c] = s.map(lambda x: x if (x is None or len(x)<=2000) else x[:2000])
    return d

def write_out(df: pd.DataFrame, path_dta: Path, path_xlsx: Path):
    path_dta.parent.mkdir(parents=True, exist_ok=True)
    df2 = sanitize_for_stata(df)
    try:
        import pyreadstat
        pyreadstat.write_dta(df2, str(path_dta), version=118)
    except Exception:
        df2.to_stata(str(path_dta), write_index=False, version=118)
    df.to_excel(path_xlsx, index=False, na_rep="NA")  # Excel output note.
    print("[INFO] Notebook progress message.")

# =============================================================================
# Original notebook comment normalized for the public code archive.
health_path = find_data_file(HEALTH_NAME)
if health_path is None:
    raise FileNotFoundError(f"找不到 {HEALTH_NAME}；请检查 DATA_DIRS。")
household_path = find_data_file(HOUSEHOLD_NAME) or find_data_file("individual_income.dta")

print("health_file   :", health_path)
print("household_file:", household_path if household_path else "[INFO] Notebook progress message.")

med = read_dta(health_path)
med = normalize_keys(med)

# Original notebook comment normalized for the public code archive.
ed023_amt_raw = amount_from_switch(med, "ed023", "ed023_1")
ed024_amt_raw = amount_from_switch(med, "ed024", "ed024_1")
ee005_amt_raw = amount_from_switch(med, "ee005", "ee005_1")
ee006_amt_raw = amount_from_switch(med, "ee006", "ee006_1")

ee024_amt_raw = pd.to_numeric(med.get("ee024_1"), errors="coerce")
if ee024_amt_raw.isna().all():
    ee024_amt_raw = pd.to_numeric(med.get("ee024"), errors="coerce")
ee027_amt_raw = pd.to_numeric(med.get("ee027_1"), errors="coerce")
if ee027_amt_raw.isna().all():
    ee027_amt_raw = pd.to_numeric(med.get("ee027"), errors="coerce")

ed006_sum_raw = sum_by_prefix(med, "ed006")  # Original notebook comment normalized for the public code archive.
ed007_sum_raw = sum_by_prefix(med, "ed007")  # Original notebook comment normalized for the public code archive.
ef002_sum_raw = sum_by_prefix(med, "ef002")  # Original notebook comment normalized for the public code archive.
ef003_sum_raw = sum_by_prefix(med, "ef003")  # Original notebook comment normalized for the public code archive.

ef001_cols = [c for c in med.columns if re.match(r"^ef001s?\d+_?$", str(c), flags=re.I)]
ef001_any = (med[ef001_cols].apply(pd.to_numeric, errors="coerce") == 1).any(axis=1).astype("float64") \
            if ef001_cols else pd.Series(np.nan, index=med.index, dtype="float64")

# Original notebook comment normalized for the public code archive.
has_outpt = flag_has_outpt(med)  # 1/0/NA
inp_any   = flag_inp_any(med)    # 1/0/NA
self_none = flag_self_none(med)  # Original notebook comment normalized for the public code archive.

no_outpt = (has_outpt == 0)    # Original notebook comment normalized for the public code archive.
no_inp   = (inp_any  == 0)     # Original notebook comment normalized for the public code archive.
no_self  = (self_none == 1)    # Original notebook comment normalized for the public code archive.

# Original notebook comment normalized for the public code archive.
def prefer_then_struct0(amount, no_event_mask):
    a = pd.to_numeric(amount, errors="coerce")
    out = a.copy()
    out.loc[a.isna() & (no_event_mask.astype("float64") == 1)] = 0.0
    return out

outpt_last_total  = prefer_then_struct0(ed023_amt_raw, no_outpt)
outpt_last_oop    = prefer_then_struct0(ed024_amt_raw, no_outpt)
outpt_month_total = prefer_then_struct0(ed006_sum_raw, no_outpt)
outpt_month_oop   = prefer_then_struct0(ed007_sum_raw, no_outpt)

inp_year_total = prefer_then_struct0(ee005_amt_raw, no_inp)
inp_year_oop   = prefer_then_struct0(ee006_amt_raw, no_inp)
inp_last_total = prefer_then_struct0(ee024_amt_raw, no_inp)
inp_last_oop   = prefer_then_struct0(ee027_amt_raw, no_inp)

self_treat_total = prefer_then_struct0(ef002_sum_raw, no_self)
self_treat_oop   = prefer_then_struct0(ef003_sum_raw, no_self)

# Original notebook comment normalized for the public code archive.
keys = [c for c in ["ID","householdID","communityID","householdID10","ID12"] if c in med.columns]
res = med[keys].copy()

res["ed023_amt_raw"] = ed023_amt_raw
res["ed024_amt_raw"] = ed024_amt_raw
res["ee005_amt_raw"] = ee005_amt_raw
res["ee006_amt_raw"] = ee006_amt_raw
res["ee024_amt_raw"] = ee024_amt_raw
res["ee027_amt_raw"] = ee027_amt_raw
res["ed006_sum_raw"] = ed006_sum_raw
res["ed007_sum_raw"] = ed007_sum_raw
res["ef002_sum_raw"] = ef002_sum_raw
res["ef003_sum_raw"] = ef003_sum_raw

res["has_outpt"] = has_outpt
res["inp_any"]   = inp_any
res["self_none"] = self_none
res["ef001_any"] = ef001_any

# Original notebook comment normalized for the public code archive.
res["outpt_month_total"] = outpt_month_total
res["outpt_month_oop"]   = outpt_month_oop
res["outpt_last_total"]  = outpt_last_total
res["outpt_last_oop"]    = outpt_last_oop
res["inp_year_total"]    = inp_year_total
res["inp_year_oop"]      = inp_year_oop
res["inp_last_total"]    = inp_last_total
res["inp_last_oop"]      = inp_last_oop
res["self_treat_total"]  = self_treat_total
res["self_treat_oop"]    = self_treat_oop

# Original notebook comment normalized for the public code archive.
if household_path is not None:
    hh = read_dta(household_path)
    hh = normalize_keys(hh)
    cols = [c for c in ["ge010_10","ge010_5"] if c in hh.columns]
    if cols:
        for c in cols:
            hh[c] = pd.to_numeric(hh[c], errors="coerce").replace(-9999, np.nan)
        take_first = (hh.groupby("householdID10")[cols]
                      .apply(lambda g: g.apply(lambda s: s.dropna().iloc[0] if s.notna().any() else np.nan))
                      .reset_index())
        res = res.merge(take_first, on="householdID10", how="left")
    else:
        res["ge010_10"] = np.nan
        res["ge010_5"]  = np.nan
else:
    res["ge010_10"] = np.nan
    res["ge010_5"]  = np.nan

# Original notebook comment normalized for the public code archive.
write_out(res, OUT_DTA, OUT_XLSX)
print("[INFO] Notebook progress message.")




# =============================================================================
# Source notebook
# =============================================================================
# record_type : wave_step
# year        : 2013
# step        : 6
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 3
# ------------------------------------------------------------------------------
# Notebook-export prose note omitted from the public code archive.


# ------------------------------------------------------------------------------
# Notebook cell 4
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import re
from pathlib import Path
import numpy as np
import pandas as pd

# =============================================================================
BASE = Path(r"E:\project_flood_impact_assessment\老年人健康\CHARLS\charls原版数据\原始数据+问卷2011~2020\2013\CHARLS2013_Dataset")
HEALTH_FILE    = BASE / "health_care_and_insurance.dta"
HOUSEHOLD_FILE = BASE / "household_income.dta"
OUT_DIR  = BASE
OUT_DTA  = OUT_DIR / "2013_Medical_investment.dta"
OUT_XLSX = OUT_DIR / "2013_Medical_investment.xlsx"

# =============================================================================
def read_dta(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"未找到：{path}")
    try:
        import pyreadstat
        df, _ = pyreadstat.read_dta(str(path), apply_value_formats=False)
        return df
    except Exception:
        return pd.read_stata(path, convert_categoricals=False)

def sanitize_for_stata(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    for c in d.select_dtypes(include=["Int8","Int16","Int32","Int64","UInt8","UInt16","UInt32","UInt64","boolean"]).columns:
        d[c] = d[c].astype("float64")
    for c in d.select_dtypes(include=["object","string"]).columns:
        s = d[c].astype(object)
        m = pd.isna(s); s = s.astype(str); s[m] = None
        d[c] = s.map(lambda x: x if (x is None or len(x)<=2000) else x[:2000])
    return d

def write_out(df: pd.DataFrame, out_dta: Path, out_xlsx: Path):
    out_dta.parent.mkdir(parents=True, exist_ok=True)
    df2 = sanitize_for_stata(df)
    try:
        import pyreadstat
        pyreadstat.write_dta(df2, str(out_dta), version=118)
        print("[INFO] Notebook progress message.")
    except Exception as e:
        print("[INFO] Notebook progress message.", e)
        df2.to_stata(str(out_dta), write_index=False, version=118)
        print("[INFO] Notebook progress message.")
    df.to_excel(out_xlsx, index=False, na_rep="NA")
    print("[INFO] Notebook progress message.")

# =============================================================================
def _clean_to_str(s: pd.Series) -> pd.Series:
    s = pd.Series(s, dtype="object")
    m = s.isna()
    t = s[~m].astype(str).str.strip()
    t = t.str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = t; s.loc[m] = np.nan
    return s

def digits_width(s: pd.Series, width: int) -> pd.Series:
    t = _clean_to_str(s).str.replace(r"\D", "", regex=True)
    t = t.where(t.str.len()>0, np.nan)
    return t.where(t.isna(), t.str[-width:].str.zfill(width)).astype("object")

def normalize_keys_2013(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()
    low = {c.lower(): c for c in df.columns}
    def pick(*names):
        for n in names:
            if n.lower() in low: return low[n.lower()]
        return None
    c_hh  = pick("householdid10","householdid","householdID10","householdID","hhid")
    c_pid = pick("id12","id","pid","PID","ID12")
    c_com = pick("communityid","communityID","commid")

    if c_hh and c_hh != "householdID": df.rename(columns={c_hh:"householdID"}, inplace=True)
    if c_pid and c_pid != "ID":        df.rename(columns={c_pid:"ID"}, inplace=True)
    if c_com and c_com != "communityID": df.rename(columns={c_com:"communityID"}, inplace=True)

    if "householdID" in df.columns:
        hh = _clean_to_str(df["householdID"]).str.replace(r"\D","",regex=True)
        df["householdID10"] = digits_width(hh, 10)
        df["householdID"] = hh.where(hh.str.len()>0, np.nan).astype("object")
    else:
        df["householdID10"] = np.nan

    if "communityID" in df.columns:
        df["communityID"] = digits_width(df["communityID"], 7)

    if "ID" in df.columns:
        idd  = _clean_to_str(df["ID"]).str.replace(r"\D","",regex=True)
        id12 = idd.where(idd.str.len()==12, np.nan)
        id11 = idd.where(idd.str.len()==11, np.nan)
    else:
        id12 = pd.Series(np.nan, index=df.index)
        id11 = pd.Series(np.nan, index=df.index)
    pn2 = id11.str[-2:]
    made = np.where((df["householdID10"].notna()) & (pn2.notna()),
                    df["householdID10"] + pn2, np.nan)
    df["ID12"] = pd.Series(id12, index=df.index).fillna(pd.Series(made, index=df.index)).astype("object")
    return df

# =============================================================================
def amount_from_switch(df: pd.DataFrame, sw_col: str, amt_col: str) -> pd.Series:
    """Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sw  = pd.to_numeric(df.get(sw_col), errors="coerce")
    amt = pd.to_numeric(df.get(amt_col), errors="coerce")
    out = pd.Series(np.nan, index=df.index, dtype="float64")
    out.loc[sw == 1] = amt.loc[sw == 1]
    out.loc[sw == 2] = 0.0
    return out

def sum_amount_blocks(df: pd.DataFrame, prefix: str) -> pd.Series:
    """Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    pat = re.compile(rf"^{re.escape(prefix)}.*_1$", flags=re.IGNORECASE)
    cols = [c for c in df.columns if pat.match(str(c))]
    if not cols:
        return pd.Series(np.nan, index=df.index, dtype="float64")
    arr = df[cols].apply(pd.to_numeric, errors="coerce")
    s = arr.sum(axis=1, skipna=True)
    all_na = arr.isna().all(axis=1)
    return s.where(~all_na, np.nan)

def flag_has_outpt(df: pd.DataFrame) -> pd.Series:
    """Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    ed004_cols = [c for c in df.columns if re.match(r"^ed004(_\d+_?)?$", str(c), flags=re.I)
                  or re.match(r"^ed004s?\d+_?$", str(c), flags=re.I)]
    if ed004_cols:
        arr = df[ed004_cols].apply(pd.to_numeric, errors="coerce")
        return ((arr == 1).any(axis=1)).astype("int8")
    evid = []
    evid += [c for c in df.columns if re.match(r"^ed005", str(c), flags=re.I)]
    evid += [c for c in df.columns if re.match(r"^ed006", str(c), flags=re.I)]
    evid += [c for c in df.columns if re.match(r"^ed023(_1)?$", str(c), flags=re.I)]
    if evid:
        A = df[evid].apply(pd.to_numeric, errors="coerce")
        return (A.notna() & (A != 0)).any(axis=1).astype("int8")
    return pd.Series(np.nan, index=df.index)

def flag_inp_any(df: pd.DataFrame) -> pd.Series:
    """Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    c = [cc for cc in df.columns if cc.lower() == "ee003"]
    if c:
        v = pd.to_numeric(df[c[0]], errors="coerce")
        return (v == 1).astype("int8")
    evid = [c for c in df.columns if re.match(r"^ee00(4|5|6|7|8|9|24|25|26|27)(_1)?$", str(c), flags=re.I)]
    if evid:
        A = df[evid].apply(pd.to_numeric, errors="coerce")
        return (A.notna() & (A != 0)).any(axis=1).astype("int8")
    return pd.Series(np.nan, index=df.index)

def flag_self_none(df: pd.DataFrame) -> pd.Series:
    """Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s7 = [c for c in df.columns if re.match(r"^ef001s?7_?$", str(c), flags=re.I)]
    if s7:
        v = pd.to_numeric(df[s7[0]], errors="coerce")
        return (v == 1).astype("int8")
    ef001_cols = [c for c in df.columns if re.match(r"^ef001s?\d+_?$", str(c), flags=re.I)]
    if ef001_cols:
        any1 = (df[ef001_cols].apply(pd.to_numeric, errors="coerce") == 1).any(axis=1)
        ef2_cols = [c for c in df.columns if re.match(r"^ef002", str(c), flags=re.I)]
        ef3_cols = [c for c in df.columns if re.match(r"^ef003", str(c), flags=re.I)]
        arr = pd.DataFrame()
        if ef2_cols: arr = pd.concat([arr, df[ef2_cols]], axis=1)
        if ef3_cols: arr = pd.concat([arr, df[ef3_cols]], axis=1)
        all_na = arr.apply(pd.to_numeric, errors="coerce").isna().all(axis=1) if not arr.empty else pd.Series(False, index=df.index)
        out = pd.Series(np.nan, index=df.index)
        out.loc[any1] = 0
        out.loc[~any1 & all_na] = 1
        return out.astype("float64")
    return pd.Series(np.nan, index=df.index)

def prefer_then_struct0(amount: pd.Series, no_event_mask: pd.Series) -> pd.Series:
    """Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    a = pd.to_numeric(amount, errors="coerce")
    out = a.copy()
    out.loc[a.isna() & (no_event_mask.astype("float64") == 1)] = 0.0
    return out

# =============================================================================
def main():
    # Original notebook comment normalized for the public code archive.
    med = read_dta(HEALTH_FILE)
    med = normalize_keys_2013(med)

    # Original notebook comment normalized for the public code archive.
    ed023_amt_raw = amount_from_switch(med, "ed023", "ed023_1")  # Original notebook comment normalized for the public code archive.
    ed024_amt_raw = amount_from_switch(med, "ed024", "ed024_1")  # Original notebook comment normalized for the public code archive.

    ee005_amt_raw = amount_from_switch(med, "ee005", "ee005_1")  # Original notebook comment normalized for the public code archive.
    ee006_amt_raw = amount_from_switch(med, "ee006", "ee006_1")  # Original notebook comment normalized for the public code archive.

    # Original notebook comment normalized for the public code archive.
    ee024_amt_raw = pd.to_numeric(med.get("ee024_1"), errors="coerce")
    if ee024_amt_raw.isna().all():
        ee024_amt_raw = pd.to_numeric(med.get("ee024"), errors="coerce")
    ee027_amt_raw = pd.to_numeric(med.get("ee027_1"), errors="coerce")
    if ee027_amt_raw.isna().all():
        ee027_amt_raw = pd.to_numeric(med.get("ee027"), errors="coerce")

    # Original notebook comment normalized for the public code archive.
    ed006_sum_raw = sum_amount_blocks(med, "ed006")  # Original notebook comment normalized for the public code archive.
    ed007_sum_raw = sum_amount_blocks(med, "ed007")  # Original notebook comment normalized for the public code archive.
    ef002_sum_raw = sum_amount_blocks(med, "ef002")  # Original notebook comment normalized for the public code archive.
    ef003_sum_raw = sum_amount_blocks(med, "ef003")  # Original notebook comment normalized for the public code archive.

    # Original notebook comment normalized for the public code archive.
    ef001_cols = [c for c in med.columns if re.match(r"^ef001s?\d+_?$", str(c), flags=re.I)]
    ef001_any = (med[ef001_cols].apply(pd.to_numeric, errors="coerce") == 1).any(axis=1).astype("float64") \
                if ef001_cols else pd.Series(np.nan, index=med.index, dtype="float64")

    # Original notebook comment normalized for the public code archive.
    has_outpt = flag_has_outpt(med)   # Original notebook comment normalized for the public code archive.
    inp_any   = flag_inp_any(med)     # Original notebook comment normalized for the public code archive.
    self_none = flag_self_none(med)   # Original notebook comment normalized for the public code archive.

    no_outpt = (has_outpt == 0)
    no_inp   = (inp_any  == 0)
    no_self  = (self_none == 1)

    # Original notebook comment normalized for the public code archive.
    outpt_last_total  = prefer_then_struct0(ed023_amt_raw, no_outpt)
    outpt_last_oop    = prefer_then_struct0(ed024_amt_raw, no_outpt)
    outpt_month_total = prefer_then_struct0(ed006_sum_raw, no_outpt)
    outpt_month_oop   = prefer_then_struct0(ed007_sum_raw, no_outpt)

    inp_year_total = prefer_then_struct0(ee005_amt_raw, no_inp)
    inp_year_oop   = prefer_then_struct0(ee006_amt_raw, no_inp)
    inp_last_total = prefer_then_struct0(ee024_amt_raw, no_inp)
    inp_last_oop   = prefer_then_struct0(ee027_amt_raw, no_inp)

    self_treat_total = prefer_then_struct0(ef002_sum_raw, no_self)
    self_treat_oop   = prefer_then_struct0(ef003_sum_raw, no_self)

    # Original notebook comment normalized for the public code archive.
    keys = [c for c in ["ID","householdID","communityID","householdID10","ID12"] if c in med.columns]
    res = med[keys].copy()

    res["ed023_amt_raw"] = ed023_amt_raw
    res["ed024_amt_raw"] = ed024_amt_raw
    res["ee005_amt_raw"] = ee005_amt_raw
    res["ee006_amt_raw"] = ee006_amt_raw
    res["ee024_amt_raw"] = ee024_amt_raw
    res["ee027_amt_raw"] = ee027_amt_raw
    res["ed006_sum_raw"] = ed006_sum_raw
    res["ed007_sum_raw"] = ed007_sum_raw
    res["ef002_sum_raw"] = ef002_sum_raw
    res["ef003_sum_raw"] = ef003_sum_raw

    res["has_outpt"] = has_outpt
    res["inp_any"]   = inp_any
    res["self_none"] = self_none
    res["ef001_any"] = ef001_any

    # Original notebook comment normalized for the public code archive.
    res["outpt_month_total"] = outpt_month_total
    res["outpt_month_oop"]   = outpt_month_oop
    res["outpt_last_total"]  = outpt_last_total
    res["outpt_last_oop"]    = outpt_last_oop

    res["inp_year_total"]    = inp_year_total
    res["inp_year_oop"]      = inp_year_oop
    res["inp_last_total"]    = inp_last_total
    res["inp_last_oop"]      = inp_last_oop

    res["self_treat_total"]  = self_treat_total
    res["self_treat_oop"]    = self_treat_oop

    # Original notebook comment normalized for the public code archive.
    hh = read_dta(HOUSEHOLD_FILE)
    hh = normalize_keys_2013(hh)
    cols = [c for c in ["ge010_6","ge010_7"] if c in hh.columns]
    if cols:
        for c in cols:
            hh[c] = pd.to_numeric(hh[c], errors="coerce").replace(-9999, np.nan)
        take_first = (hh.groupby("householdID10")[cols]
                      .apply(lambda g: g.apply(lambda s: s.dropna().iloc[0] if s.notna().any() else np.nan))
                      .reset_index())
        res = res.merge(take_first, on="householdID10", how="left")
    else:
        res["ge010_6"] = np.nan
        res["ge010_7"] = np.nan

    # Original notebook comment normalized for the public code archive.
    write_out(res, OUT_DTA, OUT_XLSX)

if __name__ == "__main__":
    main()




# =============================================================================
# Source notebook
# =============================================================================
# record_type : wave_step
# year        : 2015
# step        : 6
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 4
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import re
from pathlib import Path
import numpy as np
import pandas as pd

# =============================================================================
BASE_2015 = Path(r"E:\project_flood_impact_assessment\老年人健康\CHARLS\charls原版数据\原始数据+问卷2011~2020\2015\CHARLS2015r")  # Original notebook comment normalized for the public code archive.
HEALTH_2015    = BASE_2015 / "health_care_and_insurance.dta"
HOUSEHOLD_2015 = BASE_2015 / "household_income.dta"  # Original notebook comment normalized for the public code archive.
OUT_DIR  = Path(r"E:\impact_assessment_child_order\older\expenditure\2015")
OUT_DTA  = OUT_DIR / "Medical_investment_2015.dta"
OUT_XLSX = OUT_DIR / "Medical_investment_2015.xlsx"

# =============================================================================
def read_dta(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"未找到：{path}")
    try:
        import pyreadstat
        df, _ = pyreadstat.read_dta(str(path), apply_value_formats=False)
        return df
    except Exception:
        return pd.read_stata(path, convert_categoricals=False)

def sanitize_for_stata(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    # Original notebook comment normalized for the public code archive.
    for c in d.select_dtypes(include=["Int8","Int16","Int32","Int64",
                                      "UInt8","UInt16","UInt32","UInt64",
                                      "boolean"]).columns:
        d[c] = d[c].astype("float64")
    # Original notebook comment normalized for the public code archive.
    for c in d.select_dtypes(include=["object","string"]).columns:
        s = d[c].astype(object)
        m = pd.isna(s); s = s.astype(str); s[m] = None
        d[c] = s.map(lambda x: x if (x is None or len(x) <= 2000) else x[:2000])
    return d

def write_out(df: pd.DataFrame, dta_path: Path, xlsx_path: Path):
    dta_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import pyreadstat
        pyreadstat.write_dta(sanitize_for_stata(df), str(dta_path), version=118)
        print("[INFO] Notebook progress message.", dta_path)
    except Exception as e:
        print("[INFO] Notebook progress message.", e)
        sanitize_for_stata(df).to_stata(str(dta_path), write_index=False, version=118)
        print("[INFO] Notebook progress message.", dta_path)
    df.to_excel(xlsx_path, index=False, na_rep="NA")
    print("[INFO] Notebook progress message.", xlsx_path)

# =============================================================================
def _clean_to_str(s: pd.Series) -> pd.Series:
    s = pd.Series(s, dtype="object")
    m = s.isna()
    t = s[~m].astype(str).str.strip()
    t = t.str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = t; s.loc[m] = np.nan
    return s

def digits_width(s: pd.Series, width: int) -> pd.Series:
    t = _clean_to_str(s).str.replace(r"\D", "", regex=True)
    t = t.where(t.str.len() > 0, np.nan)
    return t.where(t.isna(), t.str[-width:].str.zfill(width)).astype("object")

def normalize_keys_2013plus(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()
    low = {c.lower(): c for c in df.columns}
    def pick(*names):
        for n in names:
            if n.lower() in low: return low[n.lower()]
        return None

    c_hh  = pick("householdid10","householdid","householdID10","householdID","hhid")
    c_pid = pick("id12","id","pid","PID","ID12")
    c_com = pick("communityid","communityID","commid")

    if c_hh  and c_hh  != "householdID":  df.rename(columns={c_hh :"householdID"},  inplace=True)
    if c_pid and c_pid != "ID":           df.rename(columns={c_pid:"ID"},           inplace=True)
    if c_com and c_com != "communityID":  df.rename(columns={c_com:"communityID"},  inplace=True)

    # Original notebook comment normalized for the public code archive.
    if "householdID" in df.columns:
        hh = _clean_to_str(df["householdID"]).str.replace(r"\D","",regex=True)
        df["householdID10"] = digits_width(hh, 10)
        df["householdID"] = hh.where(hh.str.len() > 0, np.nan).astype("object")
    else:
        df["householdID10"] = np.nan

    # Original notebook comment normalized for the public code archive.
    if "communityID" in df.columns:
        df["communityID"] = digits_width(df["communityID"], 7)

    # Original notebook comment normalized for the public code archive.
    if "ID" in df.columns:
        idd  = _clean_to_str(df["ID"]).str.replace(r"\D","",regex=True)
        id12 = idd.where(idd.str.len()==12, np.nan)
        id11 = idd.where(idd.str.len()==11, np.nan)
    else:
        id12 = pd.Series(np.nan, index=df.index)
        id11 = pd.Series(np.nan, index=df.index)

    pn2  = id11.str[-2:]
    made = np.where((df["householdID10"].notna()) & (pn2.notna()),
                    df["householdID10"] + pn2, np.nan)
    df["ID12"] = pd.Series(id12, index=df.index).fillna(pd.Series(made, index=df.index)).astype("object")
    return df

# =============================================================================
def amount_from_switch(df: pd.DataFrame, sw_col: str, amt_col: str) -> pd.Series:
    """Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sw  = pd.to_numeric(df.get(sw_col), errors="coerce")
    amt = pd.to_numeric(df.get(amt_col), errors="coerce")
    out = pd.Series(np.nan, index=df.index, dtype="float64")
    out.loc[sw == 1] = amt.loc[sw == 1]
    out.loc[sw == 2] = 0.0
    return out

def sum_amount_blocks(df: pd.DataFrame, prefix: str) -> pd.Series:
    """Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    pat = re.compile(rf"^{re.escape(prefix)}.*_1$", flags=re.IGNORECASE)
    cols = [c for c in df.columns if pat.match(str(c))]
    if not cols:
        return pd.Series(np.nan, index=df.index, dtype="float64")
    arr = df[cols].apply(pd.to_numeric, errors="coerce")
    s = arr.sum(axis=1, skipna=True)
    all_na = arr.isna().all(axis=1)
    return s.where(~all_na, np.nan)

def flag_has_outpt(df: pd.DataFrame) -> pd.Series:
    """Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    ed004_cols = [c for c in df.columns if re.match(r"^ed004(_\d+_?)?$", str(c), flags=re.I)
                  or re.match(r"^ed004s?\d+_?$", str(c), flags=re.I)]
    if ed004_cols:
        arr = df[ed004_cols].apply(pd.to_numeric, errors="coerce")
        return ((arr == 1).any(axis=1)).astype("int8")
    evid = []
    evid += [c for c in df.columns if re.match(r"^ed005", str(c), flags=re.I)]
    evid += [c for c in df.columns if re.match(r"^ed006", str(c), flags=re.I)]
    evid += [c for c in df.columns if re.match(r"^ed023(_1)?$", str(c), flags=re.I)]
    if evid:
        A = df[evid].apply(pd.to_numeric, errors="coerce")
        return (A.notna() & (A != 0)).any(axis=1).astype("int8")
    return pd.Series(np.nan, index=df.index)

def flag_inp_any(df: pd.DataFrame) -> pd.Series:
    """Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if "ee003" in {c.lower(): c for c in df.columns}:
        v = pd.to_numeric(df[[c for c in df.columns if c.lower()=="ee003"][0]], errors="coerce")
        return (v == 1).astype("int8")
    evid = [c for c in df.columns if re.match(r"^ee00(4|5|6|7|8|9|24|25|26|27)(_1)?$", str(c), flags=re.I)]
    if evid:
        A = df[evid].apply(pd.to_numeric, errors="coerce")
        return (A.notna() & (A != 0)).any(axis=1).astype("int8")
    return pd.Series(np.nan, index=df.index)

def flag_self_none(df: pd.DataFrame) -> pd.Series:
    """Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s7 = [c for c in df.columns if re.match(r"^ef001s?7_?$", str(c), flags=re.I)]
    if s7:
        v = pd.to_numeric(df[s7[0]], errors="coerce")
        return (v == 1).astype("int8")
    ef001_cols = [c for c in df.columns if re.match(r"^ef001s?\d+_?$", str(c), flags=re.I)]
    if ef001_cols:
        any1 = (df[ef001_cols].apply(pd.to_numeric, errors="coerce") == 1).any(axis=1)
        ef2_cols = [c for c in df.columns if re.match(r"^ef002", str(c), flags=re.I)]
        ef3_cols = [c for c in df.columns if re.match(r"^ef003", str(c), flags=re.I)]
        arr = pd.DataFrame()
        if ef2_cols: arr = pd.concat([arr, df[ef2_cols]], axis=1)
        if ef3_cols: arr = pd.concat([arr, df[ef3_cols]], axis=1)
        all_na = arr.apply(pd.to_numeric, errors="coerce").isna().all(axis=1) if not arr.empty else pd.Series(False, index=df.index)
        out = pd.Series(np.nan, index=df.index)
        out.loc[any1] = 0
        out.loc[~any1 & all_na] = 1
        return out.astype("float64")
    return pd.Series(np.nan, index=df.index)

def prefer_then_struct0(amount: pd.Series, no_event_mask: pd.Series) -> pd.Series:
    """Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    a = pd.to_numeric(amount, errors="coerce")
    out = a.copy()
    out.loc[a.isna() & (no_event_mask.astype("float64") == 1)] = 0.0
    return out

# =============================================================================
def main():
    # Original notebook comment normalized for the public code archive.
    med = read_dta(HEALTH_2015)
    med = normalize_keys_2013plus(med)

    # Original notebook comment normalized for the public code archive.
    ed023_amt_raw = amount_from_switch(med, "ed023", "ed023_1")  # Original notebook comment normalized for the public code archive.
    ed024_amt_raw = amount_from_switch(med, "ed024", "ed024_1")  # Original notebook comment normalized for the public code archive.

    ee005_amt_raw = amount_from_switch(med, "ee005", "ee005_1")  # Original notebook comment normalized for the public code archive.
    ee006_amt_raw = amount_from_switch(med, "ee006", "ee006_1")  # Original notebook comment normalized for the public code archive.

    # Original notebook comment normalized for the public code archive.
    ee024_amt_raw = pd.to_numeric(med.get("ee024_1"), errors="coerce")
    if ee024_amt_raw.isna().all():
        ee024_amt_raw = pd.to_numeric(med.get("ee024"), errors="coerce")
    ee027_amt_raw = pd.to_numeric(med.get("ee027_1"), errors="coerce")
    if ee027_amt_raw.isna().all():
        ee027_amt_raw = pd.to_numeric(med.get("ee027"), errors="coerce")

    # Original notebook comment normalized for the public code archive.
    ed006_sum_raw = sum_amount_blocks(med, "ed006")  # Original notebook comment normalized for the public code archive.
    ed007_sum_raw = sum_amount_blocks(med, "ed007")  # Original notebook comment normalized for the public code archive.
    ef002_sum_raw = sum_amount_blocks(med, "ef002")  # Original notebook comment normalized for the public code archive.
    ef003_sum_raw = sum_amount_blocks(med, "ef003")  # Original notebook comment normalized for the public code archive.

    # Original notebook comment normalized for the public code archive.
    ef001_cols = [c for c in med.columns if re.match(r"^ef001s?\d+_?$", str(c), flags=re.I)]
    ef001_any = (med[ef001_cols].apply(pd.to_numeric, errors="coerce") == 1).any(axis=1).astype("float64") \
                if ef001_cols else pd.Series(np.nan, index=med.index, dtype="float64")

    # Original notebook comment normalized for the public code archive.
    has_outpt = flag_has_outpt(med)   # 1/0/NA
    inp_any   = flag_inp_any(med)     # 1/0/NA
    self_none = flag_self_none(med)   # Original notebook comment normalized for the public code archive.

    no_outpt = (has_outpt == 0)
    no_inp   = (inp_any  == 0)
    no_self  = (self_none == 1)

    # Original notebook comment normalized for the public code archive.
    outpt_last_total  = prefer_then_struct0(ed023_amt_raw, no_outpt)
    outpt_last_oop    = prefer_then_struct0(ed024_amt_raw, no_outpt)
    outpt_month_total = prefer_then_struct0(ed006_sum_raw, no_outpt)
    outpt_month_oop   = prefer_then_struct0(ed007_sum_raw, no_outpt)

    inp_year_total = prefer_then_struct0(ee005_amt_raw, no_inp)
    inp_year_oop   = prefer_then_struct0(ee006_amt_raw, no_inp)
    inp_last_total = prefer_then_struct0(ee024_amt_raw, no_inp)
    inp_last_oop   = prefer_then_struct0(ee027_amt_raw, no_inp)

    self_treat_total = prefer_then_struct0(ef002_sum_raw, no_self)
    self_treat_oop   = prefer_then_struct0(ef003_sum_raw, no_self)

    # Original notebook comment normalized for the public code archive.
    keys = [c for c in ["ID","householdID","communityID","householdID10","ID12"] if c in med.columns]
    res = med[keys].copy()

    # Original notebook comment normalized for the public code archive.
    res["ed023_amt_raw"] = ed023_amt_raw
    res["ed024_amt_raw"] = ed024_amt_raw
    res["ee005_amt_raw"] = ee005_amt_raw
    res["ee006_amt_raw"] = ee006_amt_raw
    res["ee024_amt_raw"] = ee024_amt_raw
    res["ee027_amt_raw"] = ee027_amt_raw
    res["ed006_sum_raw"] = ed006_sum_raw
    res["ed007_sum_raw"] = ed007_sum_raw
    res["ef002_sum_raw"] = ef002_sum_raw
    res["ef003_sum_raw"] = ef003_sum_raw

    # Original notebook comment normalized for the public code archive.
    res["has_outpt"] = has_outpt
    res["inp_any"]   = inp_any
    res["self_none"] = self_none
    res["ef001_any"] = ef001_any

    # Original notebook comment normalized for the public code archive.
    res["outpt_month_total"] = outpt_month_total
    res["outpt_month_oop"]   = outpt_month_oop
    res["outpt_last_total"]  = outpt_last_total
    res["outpt_last_oop"]    = outpt_last_oop

    res["inp_year_total"]    = inp_year_total
    res["inp_year_oop"]      = inp_year_oop
    res["inp_last_total"]    = inp_last_total
    res["inp_last_oop"]      = inp_last_oop

    res["self_treat_total"]  = self_treat_total
    res["self_treat_oop"]    = self_treat_oop

    # Original notebook comment normalized for the public code archive.
    if HOUSEHOLD_2015.exists():
        hh = read_dta(HOUSEHOLD_2015)
        hh = normalize_keys_2013plus(hh)
        cols = [c for c in ["ge010_6","ge010_7"] if c in hh.columns]
        if cols:
            for c in cols:
                hh[c] = pd.to_numeric(hh[c], errors="coerce").replace(-9999, np.nan)
            take_first = (hh.groupby("householdID10")[cols]
                          .apply(lambda g: g.apply(lambda s: s.dropna().iloc[0] if s.notna().any() else np.nan))
                          .reset_index())
            res = res.merge(take_first, on="householdID10", how="left")
        else:
            res["ge010_6"] = np.nan
            res["ge010_7"] = np.nan
    else:
        res["ge010_6"] = np.nan
        res["ge010_7"] = np.nan

    # Original notebook comment normalized for the public code archive.
    write_out(res, OUT_DTA, OUT_XLSX)
    print("[INFO] Notebook progress message.")

if __name__ == "__main__":
    main()




# =============================================================================
# Source notebook
# =============================================================================
# record_type : wave_step
# year        : 2018
# step        : 6
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 4
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import re
from pathlib import Path
import numpy as np
import pandas as pd

# =============================================================================
BASE = Path(r"E:\project_flood_impact_assessment\老年人健康\CHARLS\charls原版数据\原始数据+问卷2011~2020\2018\CHARLS2018r")
HEALTH_FILE_CAND = ["health_care_and_insurance.dta", "Health_Care_and_Insurance.dta"]
HOUSEHOLD_FILE_CAND = ["household_income.dta", "Household_Income.dta"]

OUT_DIR  = Path(r"E:\impact_assessment_child_order\older\expenditure\2018")
OUT_DTA  = OUT_DIR / "Medical_investment_2018.dta"
OUT_XLSX = OUT_DIR / "Medical_investment_2018.xlsx"

# =============================================================================
def read_dta(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    try:
        import pyreadstat
        df, _ = pyreadstat.read_dta(str(path), apply_value_formats=False)
        return df
    except Exception:
        return pd.read_stata(path, convert_categoricals=False)

def find_first_existing(base: Path, names: list[str]) -> Path | None:
    for n in names:
        p = base / n
        if p.exists(): return p
    return None

def _clean_to_str(s: pd.Series) -> pd.Series:
    s = pd.Series(s, copy=True).astype("string")
    m = s.notna()
    s.loc[m] = (s.loc[m]
                  .str.strip()
                  .str.replace(r"\.0$", "", regex=True)
                  .str.replace(r"\s+", "", regex=True))
    return s

def _empty_string_series(index) -> pd.Series:
    return pd.Series(pd.array([pd.NA]*len(index), dtype="string"), index=index)

def digits_width(s: pd.Series, width: int) -> pd.Series:
    t = _clean_to_str(s)
    if t.isna().all():
        return pd.Series(np.nan, index=t.index, dtype="object")
    t = t.str.replace(r"\D", "", regex=True)
    t = t.mask(t.str.len() == 0, pd.NA)
    t = t.where(t.isna(), t.str[-width:].str.zfill(width))
    return t.astype("object")

def normalize_keys(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()
    low = {c.lower(): c for c in df.columns}
    def pick(*names):
        for n in names:
            c = low.get(n.lower())
            if c is not None: return c
        return None
    c_hh  = pick("householdid10","householdid","hhid")
    c_id  = pick("id12","id","pid")
    c_com = pick("communityid","commid")

    if c_hh  and c_hh  != "householdID":  df.rename(columns={c_hh :"householdID"},  inplace=True)
    if c_id  and c_id  != "ID":           df.rename(columns={c_id :"ID"},           inplace=True)
    if c_com and c_com != "communityID":  df.rename(columns={c_com:"communityID"},  inplace=True)

    hh_raw  = _clean_to_str(df["householdID"]) if "householdID" in df.columns else _empty_string_series(df.index)
    pid_raw = _clean_to_str(df["ID"])          if "ID"          in df.columns else _empty_string_series(df.index)

    hh  = hh_raw.str.replace(r"\D","",regex=True)
    pid = pid_raw.str.replace(r"\D","",regex=True)

    df["householdID10"] = digits_width(hh, 10)
    df["ID12"]          = digits_width(pid, 12)
    if "communityID" in df.columns:
        df["communityID"] = digits_width(df["communityID"], 7)

    df["householdID"] = hh.where(hh.str.len()>0, np.nan).astype("object")
    df["ID"]          = pid.where(pid.str.len()>0, np.nan).astype("object")
    return df

def sum_amount_cols(df: pd.DataFrame, prefix: str) -> pd.Series:
    cols_1 = [c for c in df.columns if str(c).lower().startswith(prefix.lower()) and str(c).lower().endswith("_1")]
    if cols_1:
        arr = df[cols_1].apply(pd.to_numeric, errors="coerce")
        s = arr.sum(axis=1, skipna=True)
        return s.where(~arr.isna().all(axis=1), np.nan)
    cols_any = [c for c in df.columns if str(c).lower().startswith(prefix.lower())]
    if not cols_any:
        return pd.Series(np.nan, index=df.index, dtype="float64")
    arr = df[cols_any].apply(pd.to_numeric, errors="coerce")
    s = arr.sum(axis=1, skipna=True)
    return s.where(~arr.isna().all(axis=1), np.nan)

def decode_amount(df: pd.DataFrame, stem: str) -> pd.Series:
    steml = stem.lower()
    for c in df.columns:
        if str(c).lower() == f"{steml}_1":
            return pd.to_numeric(df[c], errors="coerce")
    for c in df.columns:
        if str(c).lower() == steml:
            return pd.to_numeric(df[c], errors="coerce")
    return pd.Series(np.nan, index=df.index, dtype="float64")

def amount_from_switch(df: pd.DataFrame, base: str) -> pd.Series:
    low = {c.lower(): c for c in df.columns}
    code_col = low.get(base.lower())
    amt_col  = next((c for c in df.columns if str(c).lower() == f"{base.lower()}_1"), None)
    s = pd.Series(np.nan, index=df.index, dtype="float64")
    if amt_col is not None and code_col is None:
        return pd.to_numeric(df[amt_col], errors="coerce")
    if amt_col is None and code_col is None:
        return s
    code = pd.to_numeric(df[code_col], errors="coerce") if code_col is not None else None
    amt  = pd.to_numeric(df[amt_col],  errors="coerce") if amt_col  is not None else None
    if code is not None:
        s.loc[code == 2] = 0.0
        if amt is not None:
            s.loc[code == 1] = amt.loc[code == 1]
    return s if amt_col is None else s.combine_first(amt)

def struct0_by_flag(amount: pd.Series, flag: pd.Series | None, yes=1, no=2) -> pd.Series:
    if flag is None: return amount.copy()
    out = amount.copy()
    out = out.where(~(flag==no), 0.0)
    return out

def sanitize_for_stata(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    for c in d.select_dtypes(include=["Int8","Int16","Int32","Int64","UInt8","UInt16","UInt32","UInt64","boolean"]).columns:
        d[c] = d[c].astype("float64")
    for c in d.select_dtypes(include=["object","string"]).columns:
        s = d[c].astype(object)
        m = pd.isna(s); s = s.astype(str); s[m] = None
        d[c] = s.map(lambda x: x if (x is None or len(x)<=2000) else x[:2000])
    return d

def write_out(df: pd.DataFrame, out_dta: Path, out_xlsx: Path):
    out_dta.parent.mkdir(parents=True, exist_ok=True)
    d2 = sanitize_for_stata(df)
    try:
        import pyreadstat
        pyreadstat.write_dta(d2, str(out_dta), version=118)
        print("[INFO] Notebook progress message.", out_dta)
    except Exception as e:
        print("[INFO] Notebook progress message.", e)
        d2.to_stata(str(out_dta), write_index=False, version=118)
        print("[INFO] Notebook progress message.", out_dta)
    df.to_excel(out_xlsx, index=False, na_rep="NA")
    print("[INFO] Notebook progress message.", out_xlsx)

# =============================================================================
hp = find_first_existing(BASE, HEALTH_FILE_CAND)
if hp is None:
    for p in BASE.glob("*.dta"):
        try: tmp = read_dta(p)
        except Exception: continue
        low = {c.lower() for c in tmp.columns}
        if {"ed006_w4_1","ed023_w4_1","ee005_w4_1","ef001_w4"} & low:
            hp = p; break
if hp is None:
    raise FileNotFoundError("未找到 2018 医疗保健与保险 .dta")

med = read_dta(hp)
med = normalize_keys(med)

hhp = find_first_existing(BASE, HOUSEHOLD_FILE_CAND)
hh = None
if hhp is None:
    for p in BASE.glob("*.dta"):
        try: tmp = read_dta(p)
        except Exception: continue
        low = {c.lower() for c in tmp.columns}
        if "ge010_6" in low or "ge010_7" in low:
            hhp = p; break
if hhp is not None:
    hh = read_dta(hhp)
    hh = normalize_keys(hh)

# =============================================================================
keys = [c for c in ["ID","householdID","communityID","householdID10","ID12"] if c in med.columns]
res = med[keys].copy()

# Original notebook comment normalized for the public code archive.
res["ed006_w4_sum_raw"] = sum_amount_cols(med, "ed006_w4")
ed007_sum_raw = sum_amount_cols(med, "ed007")
res["ed007_sum_raw"] = ed007_sum_raw if not ed007_sum_raw.isna().all() else np.nan

# Original notebook comment normalized for the public code archive.
ed001 = pd.to_numeric(med.get("ED001") if "ED001" in med.columns else med.get("ed001"), errors="coerce") \
        if ("ED001" in med.columns or "ed001" in med.columns) else None

# Original notebook comment normalized for the public code archive.
res["ed023_w4_amt_raw"] = decode_amount(med, "ed023_w4")
res["ed024_amt_raw"]    = amount_from_switch(med, "ed024")

# Original notebook comment normalized for the public code archive.
res["ee005_w4_amt_raw"] = decode_amount(med, "ee005_w4")
res["ee006_amt_raw"]    = amount_from_switch(med, "ee006")
res["ee024_w4_amt_raw"] = decode_amount(med, "ee024_w4")
res["ee027_amt_raw"]    = amount_from_switch(med, "ee027")
ee003 = pd.to_numeric(med.get("EE003") if "EE003" in med.columns else med.get("ee003"), errors="coerce") \
        if ("EE003" in med.columns or "ee003" in med.columns) else None

# Original notebook comment normalized for the public code archive.
ef001 = pd.to_numeric(med.get("EF001_W4") if "EF001_W4" in med.columns else med.get("ef001_w4"), errors="coerce") \
        if ("EF001_W4" in med.columns or "ef001_w4" in med.columns) else None
res["ef002_w4_sum_raw"] = sum_amount_cols(med, "ef002_w4")
res["ef003_sum_raw"]    = amount_from_switch(med, "ef003")

# Original notebook comment normalized for the public code archive.
if hh is not None:
    keep = ["householdID10"]
    for want in ["ge010_6","ge010_7"]:
        rc = next((c for c in hh.columns if c.lower()==want), None)
        if rc: keep.append(rc)
    if len(keep) > 1:
        tmp = hh[keep].copy()
        agg = (tmp.groupby("householdID10")[keep[1:]]
                 .apply(lambda g: g.apply(lambda s: pd.to_numeric(s, errors="coerce").dropna().iloc[0]
                                          if pd.to_numeric(s, errors="coerce").notna().any() else np.nan))
                 .reset_index())
        rename_map = {c: c.lower() for c in agg.columns if c.lower() in ["ge010_6","ge010_7"]}
        agg.rename(columns=rename_map, inplace=True)
        res = res.merge(agg, on="householdID10", how="left")
    else:
        res["ge010_6"] = np.nan; res["ge010_7"] = np.nan
else:
    res["ge010_6"] = np.nan; res["ge010_7"] = np.nan

# =============================================================================
# Original notebook comment normalized for the public code archive.
outpt_month_total  = struct0_by_flag(res["ed006_w4_sum_raw"], ed001, yes=1, no=2)
outpt_month_oop_pref = res["ed007_sum_raw"]
if (isinstance(outpt_month_oop_pref, pd.Series) and outpt_month_oop_pref.isna().all()) and (ed001 is not None):
    outpt_month_oop_pref = res["ed024_amt_raw"].where(ed001==1, np.nan)
outpt_month_oop    = struct0_by_flag(outpt_month_oop_pref, ed001, yes=1, no=2)

# Original notebook comment normalized for the public code archive.
outpt_last_total   = struct0_by_flag(res["ed023_w4_amt_raw"], ed001, yes=1, no=2)
outpt_last_oop     = struct0_by_flag(res["ed024_amt_raw"],    ed001, yes=1, no=2)

# Original notebook comment normalized for the public code archive.
inp_year_total     = struct0_by_flag(res["ee005_w4_amt_raw"], ee003, yes=1, no=2)
inp_year_oop       = struct0_by_flag(res["ee006_amt_raw"],     ee003, yes=1, no=2)
inp_last_total     = struct0_by_flag(res["ee024_w4_amt_raw"],  ee003, yes=1, no=2)
inp_last_oop       = struct0_by_flag(res["ee027_amt_raw"],     ee003, yes=1, no=2)

# Original notebook comment normalized for the public code archive.
self_treat_total   = struct0_by_flag(res["ef002_w4_sum_raw"], ef001, yes=1, no=2)
self_treat_oop     = struct0_by_flag(res["ef003_sum_raw"],    ef001, yes=1, no=2)

# Original notebook comment normalized for the public code archive.
res["outpt_month_total"] = outpt_month_total
res["outpt_month_oop"]   = outpt_month_oop
res["outpt_last_total"]  = outpt_last_total
res["outpt_last_oop"]    = outpt_last_oop

res["inp_year_total"]    = inp_year_total
res["inp_year_oop"]      = inp_year_oop
res["inp_last_total"]    = inp_last_total
res["inp_last_oop"]      = inp_last_oop

res["self_treat_total"]  = self_treat_total
res["self_treat_oop"]    = self_treat_oop

# =============================================================================
raws = [c for c in res.columns if c.endswith("_amt_raw") or c.endswith("_sum_raw")]
finals = ["outpt_month_total","outpt_month_oop","outpt_last_total","outpt_last_oop",
          "inp_year_total","inp_year_oop","inp_last_total","inp_last_oop",
          "self_treat_total","self_treat_oop"]
hh2 = [c for c in ["ge010_6","ge010_7"] if c in res.columns]
order = [*keys, *raws, *finals, *hh2]
res = res[[c for c in order if c in res.columns]]

# =============================================================================
OUT_DIR.mkdir(parents=True, exist_ok=True)
def sanitize_for_stata(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    for c in d.select_dtypes(include=["Int8","Int16","Int32","Int64","UInt8","UInt16","UInt32","UInt64","boolean"]).columns:
        d[c] = d[c].astype("float64")
    for c in d.select_dtypes(include=["object","string"]).columns:
        s = d[c].astype(object); m = pd.isna(s); s = s.astype(str); s[m] = None
        d[c] = s.map(lambda x: x if (x is None or len(x)<=2000) else x[:2000])
    return d
try:
    import pyreadstat
    pyreadstat.write_dta(sanitize_for_stata(res), str(OUT_DTA), version=118)
    print("[INFO] Notebook progress message.", OUT_DTA)
except Exception as e:
    print("[INFO] Notebook progress message.", e)
    sanitize_for_stata(res).to_stata(str(OUT_DTA), write_index=False, version=118)
    print("[INFO] Notebook progress message.", OUT_DTA)
res.to_excel(OUT_XLSX, index=False, na_rep="NA")
print("[INFO] Notebook progress message.", OUT_XLSX)




# =============================================================================
# Source notebook
# =============================================================================
# record_type : wave_step
# year        : 2020
# step        : 6
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 2
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import re
from pathlib import Path
import numpy as np
import pandas as pd

# =============================================================================
# CHARLS processing note.
DATA_DIRS = [
    r"E:\CHARLS\2020",
    r"E:\project_flood_impact_assessment\老年人健康\CHARLS\charls原版数据\原始数据+问卷2011~2020\2020\CHARLS2020r",
]
# Original notebook comment normalized for the public code archive.
OUT_DIR = Path(r"E:\impact_assessment_child_order\older\expenditure\2020")

# Original notebook comment normalized for the public code archive.
HOUSEHOLD_HINTS = ["household_income", "Household_Income"]
EXIT_HINTS      = ["exit", "deceased", "EX", "Exit"]
INDIVIDUAL_HINTS = ["health_status", "health_status_and_functioning"]


# =============================================================================

def read_dta(path: Path) -> pd.DataFrame:
    """Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    try:
        import pyreadstat
        df, _ = pyreadstat.read_dta(str(path), apply_value_formats=False)
        return df
    except Exception:
        return pd.read_stata(path, convert_categoricals=False)

def find_file_by_cols(dirpath: Path, need_any: list[str]) -> Path | None:
    """Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    for p in dirpath.glob("*.dta"):
        try:
            df = read_dta(p)
            low_cols = {c.lower() for c in df.columns}
            if any(n.lower() in low_cols for n in need_any):
                print("[INFO] Notebook progress message.")
                return p
        except Exception:
            continue
    return None

def find_candidates() -> tuple[Path|None, Path|None, Path|None]:
    """Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print("[INFO] Notebook progress message.")
    hh_path, ex_path, indiv_path = None, None, None
    for d in DATA_DIRS:
        base = Path(d)
        if not base.exists():
            continue

        print("[INFO] Notebook progress message.")
        # Original notebook comment normalized for the public code archive.
        if not hh_path:
            for hint in HOUSEHOLD_HINTS:
                for p in base.glob(f"*{hint}*.dta"):
                    if p.exists(): hh_path = p; break
                if hh_path: break
            if not hh_path:
                hh_path = find_file_by_cols(base, ["gf013_6", "gf013_7"])

        # Original notebook comment normalized for the public code archive.
        if not ex_path:
            for hint in EXIT_HINTS:
                for p in base.glob(f"*{hint}*.dta"):
                    if p.exists(): ex_path = p; break
                if ex_path: break
            if not ex_path:
                ex_path = find_file_by_cols(base, ["exed031", "exeg010", "exef001"])

        # Original notebook comment normalized for the public code archive.
        if not indiv_path:
            for hint in INDIVIDUAL_HINTS:
                for p in base.glob(f"*{hint}*.dta"):
                    if p.exists(): indiv_path = p; break
                if indiv_path: break
            if not indiv_path:
                indiv_path = find_file_by_cols(base, ["da001"])

        # Original notebook comment normalized for the public code archive.
        if hh_path and indiv_path:
            break

    return hh_path, ex_path, indiv_path

def _clean_to_str(s: pd.Series) -> pd.Series:
    """Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = pd.Series(s, dtype="object")
    m = s.isna()
    t = s[~m].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    s.loc[~m] = t
    s.loc[m] = np.nan
    return s

def digits_width(s: pd.Series, width: int) -> pd.Series:
    """Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    t = _clean_to_str(s).str.replace(r"\D", "", regex=True).str.strip()
    t = t.where(t.str.len() > 0, np.nan)
    return t.where(t.isna(), t.str.zfill(width)).astype("object")

def normalize_keys_2013plus(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()
    low = {c.lower(): c for c in df.columns}
    def pick(*names):
        return next((low[n.lower()] for n in names if n.lower() in low), None)

    ch = pick("householdid10", "householdid", "householdID")
    ci = pick("id12", "id", "pid")
    cc = pick("communityid", "communityID")

    if ch and ch != "householdID": df.rename(columns={ch: "householdID"}, inplace=True)
    if ci and ci != "ID": df.rename(columns={ci: "ID"}, inplace=True)
    if cc and cc != "communityID": df.rename(columns={cc: "communityID"}, inplace=True)

    df["householdID10"] = digits_width(df.get("householdID"), 10)
    df["ID12"] = digits_width(df.get("ID"), 12)
    if "communityID" in df.columns:
        df["communityID"] = digits_width(df["communityID"], 7)

    return df

def sanitize_for_stata(d: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    d = d.copy()
    int_cols = d.select_dtypes(include=["number"]).columns
    d[int_cols] = d[int_cols].astype("float64")

    for c in d.select_dtypes(include=["object", "string"]).columns:
        s = d[c].astype(str).map(lambda x: x if len(x) <= 2000 else x[:2000])
        s = s.replace('nan', '')
        d[c] = s
    return d

def write_out(df: pd.DataFrame, base_name: str, out_dir: Path):
    """Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path_dta = out_dir / f"{base_name}.dta"
    path_xlsx = out_dir / f"{base_name}.xlsx"

    df_stata = sanitize_for_stata(df)
    try:
        import pyreadstat
        pyreadstat.write_dta(df_stata, str(path_dta), version=118)
    except Exception:
        df_stata.to_stata(str(path_dta), write_index=False, version=118)

    df.to_excel(path_xlsx, index=False, na_rep="NA")
    print("[INFO] Notebook progress message.")

def get_real_colname(df: pd.DataFrame, name: str) -> str | None:
    """Archived notebook note for 06_wave_medical_expenditure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    return next((c for c in df.columns if c.lower() == name.lower()), None)

# =============================================================================
def main():
    hh_path, ex_path, indiv_path = find_candidates()

    if hh_path is None or indiv_path is None:
        raise FileNotFoundError("错误：未能找到必要的户级文件和个人文件。请检查 `DATA_DIRS` 路径设置。")

    # =============================================================================
    print("[INFO] Notebook progress message.")
    hh = read_dta(hh_path)
    print("[INFO] Notebook progress message.")
    hh = normalize_keys_2013plus(hh)

    c_med = get_real_colname(hh, "gf013_6")
    c_hlt = get_real_colname(hh, "gf013_7")
    if not c_med and not c_hlt:
        raise KeyError("户级文件中未找到 gf013_6 或 gf013_7。")

    key_cols = [c for c in ["householdID10", "communityID", "householdID"] if get_real_colname(hh, c)]
    use_cols = key_cols + [c for c in [c_med, c_hlt] if c]
    use = hh[use_cols].copy()

    missing_codes = [-9999, -9, 99999999]
    for c in [c_med, c_hlt]:
        if c:
            use[c] = pd.to_numeric(use[c], errors="coerce").replace(missing_codes, np.nan)

    agg = (use.groupby("householdID10")
              .first() # Original notebook comment normalized for the public code archive.
              .reset_index())

    if c_med: agg.rename(columns={c_med: "hh_med_year"}, inplace=True)
    if c_hlt: agg.rename(columns={c_hlt: "hh_health_year"}, inplace=True)

    write_out(agg, "2020_M_household", OUT_DIR)

    # =============================================================================
    if ex_path:
        print("[INFO] Notebook progress message.")
        ex = read_dta(ex_path)
        print("[INFO] Notebook progress message.")
        ex = normalize_keys_2013plus(ex)

        cols_map = {
            "outpt_last_month_total": "exed031",
            "outpt_last_month_oop": "exed032",
            "inp_last_year_total": "exeg010",
            "inp_last_year_oop": "exeg011",
            "selftreat_flag": "exef001",
            "selftreat_last_month_total": "exef002",
            "selftreat_last_month_oop": "exef003",
        }

        ex_keys = [c for c in ["ID12", "householdID10", "communityID", "ID", "householdID"] if c in ex.columns]
        ex_res = ex[ex_keys].copy()

        for new_name, old_name in cols_map.items():
            col_real = get_real_colname(ex, old_name)
            if col_real:
                ex_res[new_name] = pd.to_numeric(ex[col_real], errors="coerce").replace(missing_codes, np.nan)
            else:
                ex_res[new_name] = np.nan

        if "selftreat_flag" in ex_res:
            is_no = ex_res["selftreat_flag"] == 2
            ex_res.loc[is_no, "selftreat_last_month_total"] = 0.0
            ex_res.loc[is_no, "selftreat_last_month_oop"] = 0.0

        ex_res = ex_res.merge(agg[["householdID10", "hh_med_year", "hh_health_year"]],
                              on="householdID10", how="left")

        write_out(ex_res, "2020_M_exit", OUT_DIR)
    else:
        print("[INFO] Notebook progress message.")

    # =============================================================================
    print("[INFO] Notebook progress message.")
    indiv = read_dta(indiv_path)
    print("[INFO] Notebook progress message.")
    indiv = normalize_keys_2013plus(indiv)

    # Original notebook comment normalized for the public code archive.
    indiv_keys = [c for c in ["ID12", "householdID10", "communityID", "ID", "householdID"] if c in indiv.columns]
    indiv_base = indiv[indiv_keys].copy()

    indiv_all = indiv_base.merge(agg[["householdID10", "hh_med_year", "hh_health_year"]],
                                 on="householdID10",
                                 how="left")

    write_out(indiv_all, "2020_M_individual_all", OUT_DIR)

    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()
