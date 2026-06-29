#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 07_wave_healthcare_access_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""



from __future__ import annotations
# =============================================================================
# Source notebook
# =============================================================================
# record_type : wave_step
# year        : 2011
# step        : 7
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 07_wave_healthcare_access_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 8
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 07_wave_healthcare_access_time.

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
OUT_DIR = Path(r"E:\impact_assessment_child_order\older\hospital\2011")
OUT_DTA  = OUT_DIR / "2011_Access_TimeCost.dta"
OUT_XLSX = OUT_DIR / "2011_Access_TimeCost.xlsx"

HEALTH_NAME = "health_care_and_insurance.dta"

# =============================================================================
def find_data_file(fname: str) -> Path | None:
    for d in DATA_DIRS:
        p = Path(d) / fname
        if p.exists():
            return p
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
    """Archived notebook note for 07_wave_healthcare_access_time.

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
    df2 = sanitize_for_stata(df.copy())
    try:
        import pyreadstat
        pyreadstat.write_dta(df2, str(path_dta), version=118)
    except Exception:
        df2.to_stata(str(path_dta), write_index=False, version=118)
    df.to_excel(path_xlsx, index=False, na_rep="NA")
    print("[INFO] Notebook progress message.")

# =============================================================================
def flag_has_outpt(df: pd.DataFrame) -> pd.Series:
    """Archived notebook note for 07_wave_healthcare_access_time.

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
    """Archived notebook note for 07_wave_healthcare_access_time.

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

# =============================================================================
def main():
    # Original notebook comment normalized for the public code archive.
    health_path = find_data_file(HEALTH_NAME)
    if health_path is None:
        raise FileNotFoundError(f"找不到 {HEALTH_NAME}；请检查 DATA_DIRS。")
    print("health_file:", health_path)

    med = read_dta(health_path)
    med = normalize_keys(med)

    # Original notebook comment normalized for the public code archive.
    to_num = lambda s: pd.to_numeric(med.get(s), errors="coerce")
    has_outpt = flag_has_outpt(med)  # 1/0/NA
    inp_any   = flag_inp_any(med)    # 1/0/NA

    ed012     = to_num("ed012")      # Original notebook comment normalized for the public code archive.
    ed014_2   = to_num("ed014_2")    # Original notebook comment normalized for the public code archive.
    ed013_raw = to_num("ed013")      # Original notebook comment normalized for the public code archive.
    ed0141_raw= to_num("ed014_1")    # Original notebook comment normalized for the public code archive.
    ed015_raw = to_num("ed015")      # Original notebook comment normalized for the public code archive.
    ed005_visits = sum_by_prefix(med, "ed005")  # Original notebook comment normalized for the public code archive.

    ee014_2   = to_num("ee014_2")    # Original notebook comment normalized for the public code archive.
    ee013_raw = to_num("ee013")      # Original notebook comment normalized for the public code archive.
    ee0141_raw= to_num("ee014_1")    # Original notebook comment normalized for the public code archive.
    ee015_raw = to_num("ee015")      # Original notebook comment normalized for the public code archive.

    # Original notebook comment normalized for the public code archive.
    U_out_ask      = (has_outpt == 1) & (ed012 != 1)       # Original notebook comment normalized for the public code archive.
    U_out_walk     = U_out_ask & (ed014_2 == 1)
    U_out_nonwalk  = U_out_ask & (ed014_2 != 1)
    U_out_cost_asked = (~ed015_raw.isna()) | U_out_nonwalk # Original notebook comment normalized for the public code archive.

    no_out_or_home = (has_outpt == 0) | (ed012 == 1)       # Original notebook comment normalized for the public code archive.
    U_inp_ask      = (inp_any == 1)                        # Original notebook comment normalized for the public code archive.
    U_inp_walk     = U_inp_ask & (ee014_2 == 1)
    U_inp_nonwalk  = U_inp_ask & (ee014_2 != 1)
    U_inp_cost_asked = (~ee015_raw.isna()) | U_inp_nonwalk

    # Original notebook comment normalized for the public code archive.
    outpt_dist_single_anl = np.where(U_out_ask, ed013_raw,  np.nan)
    outpt_time_single_anl = np.where(U_out_ask, ed0141_raw, np.nan)
    outpt_cost_single_anl = np.where(U_out_cost_asked, np.where(U_out_walk, 0, ed015_raw), np.nan)

    inp_dist_single_anl   = np.where(U_inp_ask, ee013_raw,  np.nan)
    inp_time_single_anl   = np.where(U_inp_ask, ee0141_raw, np.nan)
    inp_cost_single_anl   = np.where(U_inp_cost_asked, np.where(U_inp_walk, 0, ee015_raw), np.nan)

    # Original notebook comment normalized for the public code archive.
    def prefer_then_struct0(amount: pd.Series | np.ndarray, no_event_mask: pd.Series | np.ndarray):
        a = pd.to_numeric(amount, errors="coerce")
        out = a.copy()
        out.loc[pd.isna(a) & (no_event_mask.astype("float64") == 1)] = 0.0
        return out

    outpt_dist_single_unc = np.where(no_out_or_home, 0, ed013_raw)
    outpt_time_single_unc = prefer_then_struct0(ed0141_raw, no_out_or_home)
    outpt_cost_single_unc = np.where(has_outpt == 0, 0,
                                np.where(ed012 == 1, 0,
                                  np.where(ed014_2 == 1, 0, ed015_raw)))

    # Original notebook comment normalized for the public code archive.
    outpt_dist_month_unc  = (ed005_visits * 2) * pd.to_numeric(outpt_dist_single_unc, errors="coerce")
    outpt_time_month_unc  = (ed005_visits * 2) * pd.to_numeric(outpt_time_single_unc, errors="coerce")
    outpt_cost_month_unc  = (ed005_visits * 2) * pd.to_numeric(pd.Series(outpt_cost_single_unc).fillna(0), errors="coerce")

    inp_dist_single_unc   = np.where(inp_any == 0, 0, ee013_raw)
    inp_time_single_unc   = prefer_then_struct0(ee0141_raw, (inp_any == 0))
    inp_cost_single_unc   = np.where(inp_any == 0, 0, np.where(ee014_2 == 1, 0, ee015_raw))

    # Original notebook comment normalized for the public code archive.
    keys = [c for c in ["ID","householdID","communityID","householdID10","ID12"] if c in med.columns]
    res = med[keys].copy()

    # Original notebook comment normalized for the public code archive.
    res["ed012_homevisit"]   = ed012
    res["ed013_raw"]         = ed013_raw
    res["ed014_1_raw"]       = ed0141_raw
    res["ed014_2_mode_raw"]  = ed014_2
    res["ed015_raw"]         = ed015_raw
    res["ed005_visits"]      = ed005_visits

    res["ee013_raw"]         = ee013_raw
    res["ee014_1_raw"]       = ee0141_raw
    res["ee014_2_mode_raw"]  = ee014_2
    res["ee015_raw"]         = ee015_raw

    res["has_outpt"] = has_outpt.astype("float64")
    res["inp_any"]   = inp_any.astype("float64")

    # Original notebook comment normalized for the public code archive.
    res["outpt_dist_single_anl"] = outpt_dist_single_anl
    res["outpt_time_single_anl"] = outpt_time_single_anl
    res["outpt_cost_single_anl"] = outpt_cost_single_anl

    res["outpt_dist_single_unc"] = outpt_dist_single_unc
    res["outpt_time_single_unc"] = outpt_time_single_unc
    res["outpt_cost_single_unc"] = outpt_cost_single_unc

    res["outpt_dist_month_unc"]  = outpt_dist_month_unc
    res["outpt_time_month_unc"]  = outpt_time_month_unc
    res["outpt_cost_month_unc"]  = outpt_cost_month_unc

    res["outpt_walk"]      = (U_out_walk).astype("float64")       # Original notebook comment normalized for the public code archive.
    res["outpt_homevisit"] = (ed012 == 1).astype("float64")       # Original notebook comment normalized for the public code archive.

    # Original notebook comment normalized for the public code archive.
    res["inp_dist_single_anl"] = inp_dist_single_anl
    res["inp_time_single_anl"] = inp_time_single_anl
    res["inp_cost_single_anl"] = inp_cost_single_anl

    res["inp_dist_single_unc"] = inp_dist_single_unc
    res["inp_time_single_unc"] = inp_time_single_unc
    res["inp_cost_single_unc"] = inp_cost_single_unc

    res["inp_walk"] = (U_inp_walk).astype("float64")

    # Original notebook comment normalized for the public code archive.
    addr_cols = [c for c in med.columns if re.match(r"^(ed016|ee012)", str(c), flags=re.I)]
    if addr_cols:
        res = pd.concat([res, med[addr_cols]], axis=1)

    # Original notebook comment normalized for the public code archive.
    write_out(res, OUT_DTA, OUT_XLSX)
    print("[INFO] Notebook progress message.")

if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 10
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 07_wave_healthcare_access_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import re, inspect
import numpy as np
import pandas as pd
from pathlib import Path

# =============================================================================
ROOT = Path(r"E:\impact_assessment_child_order\older\hospital\2011")
ACC_XLSX = ROOT / "2011_Access_TimeCost.xlsx"
ACC_DTA  = ROOT / "2011_Access_TimeCost.dta"

HEALTH_DIRS = [
    r"E:\project_flood_impact_assessment\老年人健康\CHARLS\charls原版数据\原始数据+问卷2011~2020\2011\household_and_community_questionnaire_data",
    r"E:\impact_assessment_child_order\older\health\2011",
]
HEALTH_NAME = "health_care_and_insurance.dta"

OUT_XLSX = ROOT / "2011_Access_result.xlsx"
OUT_DTA  = ROOT / "2011_Access_result.dta"

# =============================================================================
W_DIM_SUBJ = 0.5
W_DIM_REAL = 0.5
ED003_BARRIER_CODES = {2, 3, 4, 5}
EE002_BARRIER_CODES = {2, 3, 4, 5}

# =============================================================================
def try_read_access_table() -> pd.DataFrame:
    if ACC_XLSX.exists():
        return pd.read_excel(ACC_XLSX)
    if ACC_DTA.exists():
        try:
            import pyreadstat
            df, _ = pyreadstat.read_dta(str(ACC_DTA), apply_value_formats=False)
            return df
        except Exception:
            return pd.read_stata(ACC_DTA, convert_categoricals=False)
    raise FileNotFoundError("未找到 2011_Access_TimeCost.(xlsx/dta)，请先运行第一段脚本。")

def find_health_file() -> Path | None:
    for d in HEALTH_DIRS:
        p = Path(d) / HEALTH_NAME
        if p.exists(): return p
    for d in HEALTH_DIRS:
        dd = Path(d)
        if not dd.exists(): continue
        for pp in dd.glob("*.dta"):
            if pp.name.lower() == HEALTH_NAME.lower():
                return pp
    return None

def read_health(path: Path | None) -> pd.DataFrame:
    if path is None or not path.exists():
        print("[INFO] Notebook progress message.")
        return pd.DataFrame()
    try:
        import pyreadstat
        df, _ = pyreadstat.read_dta(str(path), apply_value_formats=False)
        return df
    except Exception:
        return pd.read_stata(path, convert_categoricals=False)

def _clean_to_str(s: pd.Series) -> pd.Series:
    s = pd.Series(s, dtype="object"); m = s.isna()
    t = s[~m].astype(str).str.strip().str.replace(r"\.0$","",regex=True).str.replace(r"\s+","",regex=True)
    s.loc[~m] = t; s.loc[m] = np.nan; return s

def ew_score(df: pd.DataFrame, pos_cols: list[str], to_100=True, minmax_eps=1e-9):
    if len(pos_cols) == 0:
        return pd.Series(np.nan, index=df.index), pd.Series(dtype="float64"), {}
    X = df[pos_cols].copy()
    # Original notebook comment normalized for the public code archive.
    shift = (-X.min(skipna=True)).clip(lower=0)
    X = X + shift
    # Original notebook comment normalized for the public code archive.
    X = X.loc[:, X.notna().any(axis=0)]
    nunique = X.nunique(dropna=True)
    X = X.loc[:, nunique > 1]
    if X.shape[1] == 0:
        return pd.Series(0.0, index=df.index), pd.Series(dtype="float64"), {}
    # [0,1]
    Xn = (X - X.min()) / (X.max() - X.min() + minmax_eps)
    keep = Xn.sum(axis=0) > 0
    Xn = Xn.loc[:, keep]
    if Xn.shape[1] == 0:
        return pd.Series(0.0, index=df.index), pd.Series(dtype="float64"), {}
    # Original notebook comment normalized for the public code archive.
    P = Xn / (Xn.sum(axis=0) + 1e-12)
    n = (P.notna().any(axis=1)).sum()
    k = 1.0 / np.log(n if n>1 else 2)
    E = -k * (P.replace(0,np.nan) * np.log(P.replace(0,np.nan))).sum(axis=0).fillna(0)
    D = 1 - E
    w = (D / D.sum()) if D.sum() > 0 else pd.Series(1.0/len(D), index=D.index)
    S = (Xn * w).sum(axis=1)
    if to_100: S = 100 * S / (w.sum() if w.sum()!=0 else 1.0)
    return S.reindex(df.index), w, {"norm": Xn, "w": w}

def write_dta_smart(df: pd.DataFrame, out_path: Path, var_labels=None):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Original notebook comment normalized for the public code archive.
    import re as _re
    cols = list(df.columns); new, used=set(),[]
    new=[]; used=set()
    for c in cols:
        base=_re.sub(r"[^0-9A-Za-z_]","_",str(c))[:32]
        name, i = base, 1
        while name in used:
            suf=f"_{i}"; name=base[:32-len(suf)]+suf; i+=1
        new.append(name); used.add(name)
    if new!=cols: df=df.rename(columns=dict(zip(cols,new)))
    # Original notebook comment normalized for the public code archive.
    def _obj_str(s):
        m=s.isna(); t=s.astype(object).astype(str); t[m]=None; return t
    for c in [x for x in ["ID12","householdID10","ID","householdID","communityID"] if x in df.columns]:
        df[c]=_obj_str(df[c])
    for c in df.select_dtypes(include=["object"]).columns:
        if df[c].notna().sum()==0: df[c]=df[c].astype("float64")
        else: df[c]=_obj_str(df[c])
    for c in df.select_dtypes(include=["bool"]).columns:
        df[c]=df[c].astype("float64")
    # Original notebook comment normalized for the public code archive.
    try:
        import pyreadstat
        try:
            if "variable_labels" in inspect.signature(pyreadstat.write_dta).parameters:
                pyreadstat.write_dta(df.copy(), str(out_path), version=118,
                                     variable_labels={c: (var_labels.get(c,"") if var_labels else "") for c in df.columns})
            else:
                pyreadstat.write_dta(df.copy(), str(out_path), version=118)
            print("Saved DTA via pyreadstat ->", out_path)
            return
        except Exception as e:
            print("[INFO] Notebook progress message.", e)
            raise
    except Exception:
        pass
    try:
        df.copy().to_stata(out_path, write_index=False, version=118,
                           variable_labels=(var_labels or {}))
        print("Saved DTA via pandas ->", out_path)
    except Exception as e2:
        print("[INFO] Notebook progress message.", e2)
        df.copy().to_stata(out_path, write_index=False, version=118)
        print("Saved DTA via pandas (no labels) ->", out_path)

# Original notebook comment normalized for the public code archive.
def build_join_id12_for_health(hp: pd.DataFrame, acc: pd.DataFrame) -> pd.Series:
    """Archived notebook note for 07_wave_healthcare_access_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if hp.empty: return pd.Series(np.nan, index=hp.index, dtype="object")
    # Original notebook comment normalized for the public code archive.
    acc_id_digits = _clean_to_str(acc.get("ID")).str.replace(r"\D","",regex=True) if "ID" in acc.columns else pd.Series(index=acc.index, dtype="object")
    acc_map = pd.DataFrame({"_acc_id": acc_id_digits, "_acc_id12": _clean_to_str(acc.get("ID12")) if "ID12" in acc.columns else pd.Series(dtype="object")})
    acc_map = acc_map.dropna().drop_duplicates(subset=["_acc_id"])

    # Original notebook comment normalized for the public code archive.
    j1 = None
    if "ID12" in hp.columns:
        j1 = _clean_to_str(hp["ID12"]).str.replace(r"\D","",regex=True)
        j1 = j1.where(j1.str.len()==12, np.nan)

    # 2) hh10 + ID[-2:]
    j2 = None
    def mk_hh10(hh):
        hh = _clean_to_str(hh).str.replace(r"\D","",regex=True)
        hh9  = hh.where(hh.str.len()==9, np.nan)
        hh10 = hh.where(hh.str.len()==10, np.nan)
        return np.where(hh10.notna(), hh10.str.zfill(10),
                 np.where(hh9.notna(), hh9.str.zfill(9)+"0", np.nan))
    if "householdID" in hp.columns and "ID" in hp.columns:
        hh10 = pd.Series(mk_hh10(hp["householdID"]), index=hp.index, dtype="object")
        idd  = _clean_to_str(hp["ID"]).str.replace(r"\D","",regex=True)
        pn2  = idd.where(idd.str.len()>=2, np.nan).str[-2:]
        j2   = pd.Series(np.where(pd.Series(hh10).notna() & pn2.notna(), hh10 + pn2, np.nan), index=hp.index, dtype="object")

    # Original notebook comment normalized for the public code archive.
    j3 = None
    if "ID" in hp.columns and not acc_map.empty:
        idd = _clean_to_str(hp["ID"]).str.replace(r"\D","",regex=True)
        j3  = pd.Series(np.nan, index=hp.index, dtype="object")
        tmp = pd.DataFrame({"_hid": idd}).reset_index()
        tmp = tmp.merge(acc_map.rename(columns={"_acc_id":"_hid"}), on="_hid", how="left")
        j3.loc[tmp["index"]] = tmp["_acc_id12"].values

    # Original notebook comment normalized for the public code archive.
    out = pd.Series(np.nan, index=hp.index, dtype="object")
    for cand in (j1, j2, j3):
        if cand is not None:
            out = out.where(out.notna(), cand)
    return out

# Original notebook comment normalized for the public code archive.
def any_reason(df: pd.DataFrame, prefix: str, code_set: set[int]) -> pd.Series:
    pat = rf"^{prefix}(?:s|_)?\d+_?$"
    cand = [c for c in df.columns if re.match(pat, str(c), flags=re.I)]
    if cand:
        mask_cols=[]
        for c in cand:
            m=re.findall(r"(\d+)", str(c))
            if m and int(m[-1]) in code_set: mask_cols.append(c)
        if mask_cols:
            arr=(df[mask_cols].apply(pd.to_numeric, errors="coerce")==1)
            return arr.any(axis=1).astype("float64")
        return pd.Series(np.nan, index=df.index)
    base = next((c for c in df.columns if c.lower()==prefix.lower()), None)
    if base is not None:
        v=pd.to_numeric(df[base], errors="coerce")
        return v.isin(list(code_set)).astype("float64")
    return pd.Series(np.nan, index=df.index)

# Original notebook comment normalized for the public code archive.
def ensure_inp_any(acc: pd.DataFrame, hp: pd.DataFrame, join_id12: pd.Series) -> pd.Series:
    if "inp_any" in acc.columns and not pd.isna(acc["inp_any"]).all():
        return pd.to_numeric(acc["inp_any"], errors="coerce")
    if hp.empty or join_id12.isna().all():
        return pd.Series(np.nan, index=acc.index)
    ee003_col = next((c for c in hp.columns if c.lower()=="ee003"), None)
    if ee003_col is None:
        return pd.Series(np.nan, index=acc.index)
    ee = (pd.to_numeric(hp[ee003_col], errors="coerce")==1).astype("float64")
    t = pd.DataFrame({"join_ID12": join_id12, "ee": ee}).dropna(subset=["join_ID12"])
    g = t.groupby("join_ID12", as_index=False)["ee"].max()
    return acc.merge(g, left_on="ID12", right_on="join_ID12", how="left")["ee"]

# =============================================================================
def main():
    # Original notebook comment normalized for the public code archive.
    acc = try_read_access_table()
    if "ID12" not in acc.columns:
        raise ValueError("2011_Access_TimeCost 中缺少 ID12。")
    acc["ID12"] = _clean_to_str(acc["ID12"]).str.replace(r"\D","",regex=True)
    acc = acc.sort_index().drop_duplicates(subset=["ID12"], keep="first")
    print("[INFO] Notebook progress message.", acc.shape)

    # Original notebook comment normalized for the public code archive.
    hp_path = find_health_file()
    hp = read_health(hp_path)
    if not hp.empty:
        join_id12 = build_join_id12_for_health(hp, acc)  # Series
        cov = int(join_id12.notna().sum()); tot = len(join_id12)
        print("[INFO] Notebook progress message.")
    else:
        join_id12 = pd.Series(np.nan, index=pd.RangeIndex(0))

    # Original notebook comment normalized for the public code archive.
    subj_cols = []

    # Original notebook comment normalized for the public code archive.
    if not hp.empty and {"ed001","ed002"} <= {c.lower() for c in hp.columns} and join_id12.notna().any():
        ed001 = pd.to_numeric(hp[[c for c in hp.columns if c.lower()=="ed001"][0]], errors="coerce")
        ed002 = pd.to_numeric(hp[[c for c in hp.columns if c.lower()=="ed002"][0]], errors="coerce")
        unmet = ((ed002==1) & (ed001==2)).astype("float64")
        t = pd.DataFrame({"join_ID12": join_id12, "bar_unmet_outpt": unmet})
        g = (t.dropna(subset=["join_ID12"])
               .groupby("join_ID12", as_index=False)["bar_unmet_outpt"].max())
        acc = acc.merge(g, left_on="ID12", right_on="join_ID12", how="left")
        acc.drop(columns=["join_ID12"], inplace=True)
    else:
        # Original notebook comment normalized for the public code archive.
        acc["bar_unmet_outpt"] = (acc.get("has_outpt", pd.Series(0,index=acc.index)).fillna(0)==0).astype("float64")
    subj_cols.append("bar_unmet_outpt")

    # Original notebook comment normalized for the public code archive.
    if not hp.empty and any(c.lower()=="ee001" for c in hp.columns) and join_id12.notna().any():
        ee001 = (pd.to_numeric(hp[[c for c in hp.columns if c.lower()=="ee001"][0]], errors="coerce")==1).astype("float64")
        t = pd.DataFrame({"join_ID12": join_id12, "EE001_any": ee001}).dropna(subset=["join_ID12"])
        g = t.groupby("join_ID12", as_index=False)["EE001_any"].max()
        acc = acc.merge(g, left_on="ID12", right_on="join_ID12", how="left")
        acc.drop(columns=["join_ID12"], inplace=True)
    else:
        acc["EE001_any"] = np.nan

    # Original notebook comment normalized for the public code archive.
    acc["inp_any"] = ensure_inp_any(acc, hp, join_id12)
    acc["bar_advised_no_hosp"] = ((acc["EE001_any"]==1) & (acc["inp_any"]!=1)).astype("float64")
    acc.drop(columns=[c for c in ["EE001_any"] if c in acc.columns], inplace=True)
    subj_cols.append("bar_advised_no_hosp")

    # Original notebook comment normalized for the public code archive.
    if not hp.empty and join_id12.notna().any():
        ed_mask = any_reason(hp, "ed003", ED003_BARRIER_CODES)
        ee_mask = any_reason(hp, "ee002", EE002_BARRIER_CODES)
        t1 = pd.DataFrame({"join_ID12": join_id12, "bar_ed003": ed_mask}).dropna(subset=["join_ID12"])
        t2 = pd.DataFrame({"join_ID12": join_id12, "bar_ee002": ee_mask}).dropna(subset=["join_ID12"])
        g1 = t1.groupby("join_ID12", as_index=False)["bar_ed003"].max()
        g2 = t2.groupby("join_ID12", as_index=False)["bar_ee002"].max()
        acc = acc.merge(g1, left_on="ID12", right_on="join_ID12", how="left").drop(columns=["join_ID12"])
        acc = acc.merge(g2, left_on="ID12", right_on="join_ID12", how="left").drop(columns=["join_ID12"])
    else:
        acc["bar_ed003"] = np.nan
        acc["bar_ee002"] = np.nan
    subj_cols += ["bar_ed003","bar_ee002"]

    subj_use = [c for c in subj_cols if c in acc.columns]

    # Original notebook comment normalized for the public code archive.
    real_use = [c for c in [
        "outpt_time_month_unc","outpt_dist_month_unc","outpt_cost_month_unc",
        "inp_time_single_unc","inp_dist_single_unc","inp_cost_single_unc",
    ] if c in acc.columns]

    # Original notebook comment normalized for the public code archive.
    subj_score, subj_w, _ = ew_score(acc, subj_use, to_100=True)
    real_score, real_w, _ = ew_score(acc, real_use, to_100=True)

    # Original notebook comment normalized for the public code archive.
    comp_score = (W_DIM_SUBJ*subj_score.fillna(0) + W_DIM_REAL*real_score.fillna(0)) / (W_DIM_SUBJ+W_DIM_REAL)

    # Original notebook comment normalized for the public code archive.
    keep_ids = [c for c in ["ID12","householdID10","ID","householdID","communityID"] if c in acc.columns]
    cols_out = keep_ids + subj_use + real_use + ["has_outpt","inp_any","outpt_walk","outpt_homevisit"]
    cols_out = [c for c in cols_out if c in acc.columns]
    out = acc[cols_out].copy()
    out["主观障碍指数(0-100)"] = subj_score
    out["已实现成本时间指数(0-100)"] = real_score
    out["就医可达性综合指数(0-100)"] = comp_score

    # Excel
    for c in [x for x in ["ID12","householdID10","ID","householdID","communityID"] if x in out.columns]:
        out[c] = out[c].astype(object).astype(str).where(~out[c].isna(), None)
    out.to_excel(OUT_XLSX, index=False)
    print("Excel ->", OUT_XLSX)

    # DTA
    var_labels = {
        "ID12":"个人ID(12位)","householdID10":"householdID(10位)","ID":"ID(2011-11位)","householdID":"householdID(2011-9位)",
        "communityID":"社区(7位)",
        "bar_unmet_outpt":"主观障碍-生病未门诊(1/0)",
        "bar_advised_no_hosp":"主观障碍-建议住院未住(1/0)",
        "bar_ed003":"主观障碍-门诊理由含交通/距离/时间/费用(1/0)",
        "bar_ee002":"主观障碍-住院理由含交通/距离/时间/费用(1/0)",
        "outpt_time_month_unc":"门诊-月单程时间合计(分钟)",
        "outpt_dist_month_unc":"门诊-月单程距离合计(同单位)",
        "outpt_cost_month_unc":"门诊-月单程交通费合计(元)",
        "inp_time_single_unc":"住院-单程时间(分钟)",
        "inp_dist_single_unc":"住院-单程距离(同单位)",
        "inp_cost_single_unc":"住院-单程交通费(元)",
        "has_outpt":"过去月是否门诊(1/0/NA)",
        "inp_any":"过去年是否住院(1/0/NA)",
        "outpt_walk":"门诊-步行(1/0/NA)",
        "outpt_homevisit":"门诊-上门服务(1/0/NA)",
        "主观障碍指数(0-100)":"熵权-主观障碍(越大越差)",
        "已实现成本时间指数(0-100)":"熵权-已实现成本/时间(越大越差)",
        "就医可达性综合指数(0-100)":"0.5*主观 + 0.5*已实现（可调）",
    }
    write_dta_smart(out.copy(), OUT_DTA, var_labels=var_labels)
    print("DTA  ->", OUT_DTA)

    # Original notebook comment normalized for the public code archive.
    def pretty(tag, w):
        if w.empty: print("[INFO] Notebook progress message."); return
        print("[INFO] Notebook progress message.")
        ww=(w/w.sum()).sort_values(ascending=False)
        for k,v in ww.items(): print(f"  - {k}: {v:.3f}")
    pretty("主观障碍", subj_w)
    pretty("已实现成本/时间", real_w)
    print("[INFO] Notebook progress message.")

if __name__ == "__main__":
    main()




# =============================================================================
# Source notebook
# =============================================================================
# record_type : wave_step
# year        : 2013
# step        : 7
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 07_wave_healthcare_access_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 3
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 07_wave_healthcare_access_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import re
from pathlib import Path
import numpy as np
import pandas as pd

# =============================================================================
DATA_DIRS = [
    r"E:\project_flood_impact_assessment\老年人健康\CHARLS\charls原版数据\原始数据+问卷2011~2020\2013\CHARLS2013_Dataset",
    r"E:\impact_assessment_child_order\older\health\2013",
]
OUT_DIR = Path(r"E:\impact_assessment_child_order\older\hospital\2013")
OUT_DTA  = OUT_DIR / "2013_Access_TimeCost.dta"
OUT_XLSX = OUT_DIR / "2013_Access_TimeCost.xlsx"

# Original notebook comment normalized for the public code archive.
LIKELY_FILENAMES = [
    "health_care_and_insurance.dta",
    "Health_Care_and_Insurance.dta",
    "HealthCareAndInsurance.dta",
    "Health care and insurance.dta",
]

# =============================================================================
def read_dta(path: Path) -> pd.DataFrame:
    if not path or not path.exists():
        raise FileNotFoundError(f"未找到文件：{path}")
    try:
        import pyreadstat
        df, _ = pyreadstat.read_dta(str(path), apply_value_formats=False)
        return df
    except Exception:
        return pd.read_stata(path, convert_categoricals=False)


def list_columns_quick(path: Path):
    """Archived notebook note for 07_wave_healthcare_access_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    try:
        import pyreadstat
        df, meta = pyreadstat.read_dta(str(path), apply_value_formats=False, row_limit=1)
        return list(df.columns)
    except Exception:
        # Original notebook comment normalized for the public code archive.
        df = pd.read_stata(path, convert_categoricals=False)
        return list(df.columns)


def find_health_table() -> Path:
    # Original notebook comment normalized for the public code archive.
    for d in DATA_DIRS:
        for name in LIKELY_FILENAMES:
            p = Path(d) / name
            if p.exists():
                return p
    # Original notebook comment normalized for the public code archive.
    need_any = {"ed013", "ed014_1", "ed014_2", "ed015", "ed005_", "ed012",
                "ee013", "ee014_1", "ee014_2", "ee015", "ee003"}
    for d in DATA_DIRS:
        dd = Path(d)
        if not dd.exists():
            continue
        for pp in dd.glob("*.dta"):
            cols = {c.lower() for c in list_columns_quick(pp)}
            # Original notebook comment normalized for the public code archive.
            hit = 0
            for k in need_any:
                base = k.split("_")[0]
                if any(c.startswith(base) for c in cols):
                    hit += 1
            if hit >= 7:
                return pp
    raise FileNotFoundError("未在 2013 目录中定位到含 ED/EE 核心变量的 health/insurance 表。请检查目录或补充 LIKELY_FILENAMES。")


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


def normalize_keys(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 07_wave_healthcare_access_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()
    low = {c.lower(): c for c in df.columns}

    def pick(*names):
        for n in names:
            if n.lower() in low:
                return low[n.lower()]
        return None

    c_hh  = pick("householdid", "householdID", "hhid")
    c_pid = pick("id", "pid", "PID")
    c_com = pick("communityid", "communityID", "commid")

    if c_hh and c_hh != "householdID":
        df.rename(columns={c_hh: "householdID"}, inplace=True)
    if c_pid and c_pid != "ID":
        df.rename(columns={c_pid: "ID"}, inplace=True)
    if c_com and c_com != "communityID":
        df.rename(columns={c_com: "communityID"}, inplace=True)

    # Original notebook comment normalized for the public code archive.
    if "householdID" in df.columns:
        hh_digits = _clean_to_str(df["householdID"]).str.replace(r"\D", "", regex=True)
        hh9  = hh_digits.where(hh_digits.str.len() == 9, np.nan)
        hh10 = hh_digits.where(hh_digits.str.len() == 10, np.nan)
        df["householdID10"] = np.where(
            hh10.notna(), hh10.str.zfill(10),
            np.where(hh9.notna(), hh9.str.zfill(9) + "0", np.nan)
        ).astype("object")
        df["householdID"] = hh_digits.where(hh_digits.str.len() > 0, np.nan).astype("object")
    else:
        df["householdID10"] = np.nan

    if "communityID" in df.columns:
        df["communityID"] = digits_width(df["communityID"], 7)

    # Original notebook comment normalized for the public code archive.
    if "ID" in df.columns:
        id_digits = _clean_to_str(df["ID"]).str.replace(r"\D", "", regex=True)
        direct12 = id_digits.where(id_digits.str.len() == 12, np.nan).astype("object")
        pn2 = id_digits.where(id_digits.str.len() >= 2, np.nan).str[-2:]
    else:
        direct12 = pd.Series(np.nan, index=df.index, dtype="object")
        pn2 = pd.Series(np.nan, index=df.index, dtype="object")

    made = np.where(pd.Series(pn2).notna() & df["householdID10"].notna(),
                    df["householdID10"] + pn2.astype("object"), np.nan)
    df["ID12"] = pd.Series(direct12, index=df.index).fillna(pd.Series(made, index=df.index)).astype("object")
    return df


def sum_by_prefix(df: pd.DataFrame, prefix: str) -> pd.Series:
    cols = [c for c in df.columns if str(c).lower().startswith(prefix.lower())]
    if not cols:
        return pd.Series(np.nan, index=df.index, dtype="float64")
    arr = df[cols].apply(pd.to_numeric, errors="coerce")
    s = arr.sum(axis=1, skipna=True)
    all_na = arr.isna().all(axis=1)
    return s.where(~all_na, np.nan)


def sanitize_for_stata(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    for c in d.select_dtypes(include=["Int8", "Int16", "Int32", "Int64", "UInt8", "UInt16", "UInt32", "UInt64", "boolean"]).columns:
        d[c] = d[c].astype("float64")
    for c in d.select_dtypes(include=["object", "string"]).columns:
        s = d[c].astype(object)
        m = pd.isna(s)
        s = s.astype(str)
        s[m] = None
        d[c] = s.map(lambda x: x if (x is None or len(x) <= 2000) else x[:2000])
    return d


def write_out(df: pd.DataFrame, path_dta: Path, path_xlsx: Path):
    path_dta.parent.mkdir(parents=True, exist_ok=True)
    df2 = sanitize_for_stata(df.copy())
    try:
        import pyreadstat
        pyreadstat.write_dta(df2, str(path_dta), version=118)
    except Exception:
        df2.to_stata(str(path_dta), write_index=False, version=118)
    df.to_excel(path_xlsx, index=False, na_rep="NA")
    print("[INFO] Notebook progress message.")


# =============================================================================
def flag_has_outpt(df: pd.DataFrame) -> pd.Series:
    """Archived notebook note for 07_wave_healthcare_access_time.

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
    """Archived notebook note for 07_wave_healthcare_access_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if "ee003" in {c.lower() for c in df.columns}:
        col = [c for c in df.columns if c.lower() == "ee003"][0]
        ee003 = pd.to_numeric(df[col], errors="coerce")
        return (ee003 == 1).astype("int8", copy=False)
    evid = [c for c in df.columns if re.match(r"^ee00(4|5|6|7|8|9|24|25|26|27)(_1)?$", str(c), flags=re.I)]
    if evid:
        A = df[evid].apply(pd.to_numeric, errors="coerce")
        has = A.notna() & (A != 0)
        return has.any(axis=1).astype("int8", copy=False)
    return pd.Series(np.nan, index=df.index)


def to_num_col(df: pd.DataFrame, name: str) -> pd.Series:
    """Archived notebook note for 07_wave_healthcare_access_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if name in df.columns:
        return pd.to_numeric(df[name], errors="coerce")
    return pd.Series(np.nan, index=df.index, dtype="float64")


# =============================================================================
def main():
    # Original notebook comment normalized for the public code archive.
    health_path = find_health_table()
    print("health_file:", health_path)

    med = read_dta(health_path)
    med = normalize_keys(med)

    # Original notebook comment normalized for the public code archive.
    has_outpt = flag_has_outpt(med)  # 1/0/NA
    inp_any   = flag_inp_any(med)    # 1/0/NA

    ed012      = to_num_col(med, "ed012")      # Original notebook comment normalized for the public code archive.
    ed014_2    = to_num_col(med, "ed014_2")    # Original notebook comment normalized for the public code archive.
    ed013_raw  = to_num_col(med, "ed013")      # Original notebook comment normalized for the public code archive.
    ed0141_raw = to_num_col(med, "ed014_1")    # Original notebook comment normalized for the public code archive.
    ed015_raw  = to_num_col(med, "ed015")      # Original notebook comment normalized for the public code archive.
    ed005_visits = sum_by_prefix(med, "ed005")  # Original notebook comment normalized for the public code archive.

    ee014_2    = to_num_col(med, "ee014_2")    # Original notebook comment normalized for the public code archive.
    ee013_raw  = to_num_col(med, "ee013")      # Original notebook comment normalized for the public code archive.
    ee0141_raw = to_num_col(med, "ee014_1")    # Original notebook comment normalized for the public code archive.
    ee015_raw  = to_num_col(med, "ee015")      # Original notebook comment normalized for the public code archive.

    # Original notebook comment normalized for the public code archive.
    U_out_ask        = (has_outpt == 1) & ed012.notna() & (ed012 != 1)
    U_out_walk       = U_out_ask & (ed014_2 == 1)
    U_out_nonwalk    = U_out_ask & ed014_2.notna() & (ed014_2 != 1)
    U_out_cost_asked = U_out_ask & (ed015_raw.notna() | U_out_nonwalk)

    no_out_or_home   = (has_outpt == 0) | (ed012 == 1)  # Original notebook comment normalized for the public code archive.

    U_inp_ask        = (inp_any == 1)
    U_inp_walk       = U_inp_ask & (ee014_2 == 1)
    U_inp_nonwalk    = U_inp_ask & ee014_2.notna() & (ee014_2 != 1)
    U_inp_cost_asked = U_inp_ask & (ee015_raw.notna() | U_inp_nonwalk)

    # Original notebook comment normalized for the public code archive.
    outpt_dist_single_anl = np.where(U_out_ask, ed013_raw,  np.nan)
    outpt_time_single_anl = np.where(U_out_ask, ed0141_raw, np.nan)
    outpt_cost_single_anl = np.where(U_out_cost_asked, np.where(U_out_walk, 0, ed015_raw), np.nan)

    inp_dist_single_anl   = np.where(U_inp_ask, ee013_raw,  np.nan)
    inp_time_single_anl   = np.where(U_inp_ask, ee0141_raw, np.nan)
    inp_cost_single_anl   = np.where(U_inp_cost_asked, np.where(U_inp_walk, 0, ee015_raw), np.nan)

    # Original notebook comment normalized for the public code archive.
    def prefer_then_struct0(amount, no_event_mask):
        a = pd.to_numeric(pd.Series(amount), errors="coerce")
        nem = pd.Series(no_event_mask).astype("float64") == 1
        out = a.copy()
        out.loc[a.isna() & nem] = 0.0
        return out

    outpt_dist_single_unc = np.where(no_out_or_home, 0, ed013_raw)
    outpt_time_single_unc = prefer_then_struct0(ed0141_raw, no_out_or_home)
    outpt_cost_single_unc = np.where(
        has_outpt == 0, 0,
        np.where(ed012 == 1, 0, np.where(ed014_2 == 1, 0, ed015_raw))
    )

    # Original notebook comment normalized for the public code archive.
    outpt_dist_month_unc  = (ed005_visits * 2) * pd.to_numeric(outpt_dist_single_unc, errors="coerce")
    outpt_time_month_unc  = (ed005_visits * 2) * pd.to_numeric(outpt_time_single_unc, errors="coerce")
    outpt_cost_month_unc  = (ed005_visits * 2) * pd.to_numeric(pd.Series(outpt_cost_single_unc).fillna(0), errors="coerce")

    inp_dist_single_unc   = np.where(inp_any == 0, 0, ee013_raw)
    inp_time_single_unc   = prefer_then_struct0(ee0141_raw, (inp_any == 0))
    inp_cost_single_unc   = np.where(inp_any == 0, 0, np.where(ee014_2 == 1, 0, ee015_raw))

    # Original notebook comment normalized for the public code archive.
    keys = [c for c in ["ID", "householdID", "communityID", "householdID10", "ID12"] if c in med.columns]
    res = med[keys].copy() if keys else pd.DataFrame(index=med.index)

    # Original notebook comment normalized for the public code archive.
    res["ed012_homevisit"]   = ed012
    res["ed013_raw"]         = ed013_raw
    res["ed014_1_raw"]       = ed0141_raw
    res["ed014_2_mode_raw"]  = ed014_2
    res["ed015_raw"]         = ed015_raw
    res["ed005_visits"]      = ed005_visits

    res["ee013_raw"]         = ee013_raw
    res["ee014_1_raw"]       = ee0141_raw
    res["ee014_2_mode_raw"]  = ee014_2
    res["ee015_raw"]         = ee015_raw

    res["has_outpt"] = has_outpt.astype("float64")
    res["inp_any"]   = inp_any.astype("float64")

    # Original notebook comment normalized for the public code archive.
    res["outpt_dist_single_anl"] = outpt_dist_single_anl
    res["outpt_time_single_anl"] = outpt_time_single_anl
    res["outpt_cost_single_anl"] = outpt_cost_single_anl

    res["outpt_dist_single_unc"] = outpt_dist_single_unc
    res["outpt_time_single_unc"] = outpt_time_single_unc
    res["outpt_cost_single_unc"] = outpt_cost_single_unc

    res["outpt_dist_month_unc"]  = outpt_dist_month_unc
    res["outpt_time_month_unc"]  = outpt_time_month_unc
    res["outpt_cost_month_unc"]  = outpt_cost_month_unc

    res["outpt_walk"]      = (U_out_walk).astype("float64")       # Original notebook comment normalized for the public code archive.
    res["outpt_homevisit"] = (ed012 == 1).astype("float64")       # Original notebook comment normalized for the public code archive.

    # Original notebook comment normalized for the public code archive.
    res["inp_dist_single_anl"] = inp_dist_single_anl
    res["inp_time_single_anl"] = inp_time_single_anl
    res["inp_cost_single_anl"] = inp_cost_single_anl

    res["inp_dist_single_unc"] = inp_dist_single_unc
    res["inp_time_single_unc"] = inp_time_single_unc
    res["inp_cost_single_unc"] = inp_cost_single_unc

    res["inp_walk"] = (U_inp_walk).astype("float64")

    # Original notebook comment normalized for the public code archive.
    addr_cols = [c for c in med.columns if re.match(r"^(ed016|ee012)", str(c), flags=re.I)]
    if addr_cols:
        res = pd.concat([res, med[addr_cols]], axis=1)

    # Original notebook comment normalized for the public code archive.
    write_out(res, OUT_DTA, OUT_XLSX)
    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 5
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 07_wave_healthcare_access_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import re, inspect
import numpy as np
import pandas as pd
from pathlib import Path

# =============================================================================
ROOT = Path(r"E:\impact_assessment_child_order\older\hospital\2013")
ACC_XLSX = ROOT / "2013_Access_TimeCost.xlsx"
ACC_DTA  = ROOT / "2013_Access_TimeCost.dta"

HEALTH_DIRS = [
    r"E:\project_flood_impact_assessment\老年人健康\CHARLS\charls原版数据\原始数据+问卷2011~2020\2013\CHARLS2013_Dataset",
    r"E:\impact_assessment_child_order\older\health\2013",
]
LIKELY_HEALTH = [
    "health_care_and_insurance.dta", "Health_Care_and_Insurance.dta",
    "HealthCareAndInsurance.dta", "Health care and insurance.dta"
]

OUT_XLSX = ROOT / "2013_Access_result.xlsx"
OUT_DTA  = ROOT / "2013_Access_result.dta"

# =============================================================================
W_DIM_SUBJ = 0.5
W_DIM_REAL = 0.5
ED003_BARRIER_CODES = {2, 3, 4, 5}
EE002_BARRIER_CODES = {2, 3, 4, 5}

# =============================================================================
def _clean_to_str(s: pd.Series) -> pd.Series:
    s = pd.Series(s, dtype="object"); m = s.isna()
    t = s[~m].astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = t; s.loc[m] = np.nan; return s


def try_read_access_table() -> pd.DataFrame:
    if ACC_XLSX.exists():
        return pd.read_excel(ACC_XLSX)
    if ACC_DTA.exists():
        try:
            import pyreadstat
            df, _ = pyreadstat.read_dta(str(ACC_DTA), apply_value_formats=False)
            return df
        except Exception:
            return pd.read_stata(ACC_DTA, convert_categoricals=False)
    raise FileNotFoundError("未找到 2013_Access_TimeCost.(xlsx/dta)，请先运行脚本1。")


def find_health_file() -> Path | None:
    for d in HEALTH_DIRS:
        for name in LIKELY_HEALTH:
            p = Path(d) / name
            if p.exists():
                return p
    for d in HEALTH_DIRS:
        dd = Path(d)
        if not dd.exists():
            continue
        for pp in dd.glob("*.dta"):
            cols = set()
            try:
                import pyreadstat
                df, _ = pyreadstat.read_dta(str(pp), apply_value_formats=False, row_limit=1)
                cols = {c.lower() for c in df.columns}
            except Exception:
                try:
                    df = pd.read_stata(pp, convert_categoricals=False)
                    cols = {c.lower() for c in df.columns}
                except Exception:
                    continue
            if {"ed001", "ed002", "ee001", "ee002", "ee003"} & cols:
                return pp
    return None


def read_health(path: Path | None) -> pd.DataFrame:
    if path is None or not path.exists():
        print("[INFO] Notebook progress message.")
        return pd.DataFrame()
    try:
        import pyreadstat
        df, _ = pyreadstat.read_dta(str(path), apply_value_formats=False)
        return df
    except Exception:
        return pd.read_stata(path, convert_categoricals=False)


def any_reason(df: pd.DataFrame, prefix: str, code_set: set[int]) -> pd.Series:
    pat = rf"^{prefix}(?:s|_)?\d+_?$"
    cand = [c for c in df.columns if re.match(pat, str(c), flags=re.I)]
    if cand:
        mask_cols = []
        for c in cand:
            m = re.findall(r"(\d+)", str(c))
            if m and int(m[-1]) in code_set:
                mask_cols.append(c)
        if mask_cols:
            arr = (df[mask_cols].apply(pd.to_numeric, errors="coerce") == 1)
            return arr.any(axis=1).astype("float64")
        return pd.Series(np.nan, index=df.index)
    base = next((c for c in df.columns if c.lower() == prefix.lower()), None)
    if base is not None:
        v = pd.to_numeric(df[base], errors="coerce")
        return v.isin(list(code_set)).astype("float64")
    return pd.Series(np.nan, index=df.index)


def build_join_id12_for_health(hp: pd.DataFrame, acc: pd.DataFrame) -> pd.Series:
    """Archived notebook note for 07_wave_healthcare_access_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if hp.empty:
        return pd.Series(np.nan, index=hp.index, dtype="object")
    # Original notebook comment normalized for the public code archive.
    acc_id_digits = _clean_to_str(acc.get("ID")).str.replace(r"\D", "", regex=True) if "ID" in acc.columns else pd.Series(index=acc.index, dtype="object")
    acc_map = pd.DataFrame({"_acc_id": acc_id_digits, "_acc_id12": _clean_to_str(acc.get("ID12")) if "ID12" in acc.columns else pd.Series(dtype="object")})
    acc_map = acc_map.dropna().drop_duplicates(subset=["_acc_id"])

    # Original notebook comment normalized for the public code archive.
    j1 = None
    if "ID12" in hp.columns:
        j1 = _clean_to_str(hp["ID12"]).str.replace(r"\D", "", regex=True)
        j1 = j1.where(j1.str.len() == 12, np.nan)

    # 2) hh10 + ID[-2:]
    j2 = None
    if "householdID" in hp.columns and "ID" in hp.columns:
        hh = _clean_to_str(hp["householdID"]).str.replace(r"\D", "", regex=True)
        hh10 = np.where(
            hh.where(hh.str.len() == 10, np.nan).notna(), hh.str.zfill(10),
            np.where(hh.where(hh.str.len() == 9, np.nan).notna(), hh.str.zfill(9) + "0", np.nan)
        )
        idd = _clean_to_str(hp["ID"]).str.replace(r"\D", "", regex=True)
        pn2 = idd.where(idd.str.len() >= 2, np.nan).str[-2:]
        j2 = pd.Series(np.where(pd.Series(hh10).notna() & pn2.notna(), pd.Series(hh10) + pn2, np.nan), index=hp.index, dtype="object")

    # Original notebook comment normalized for the public code archive.
    j3 = None
    if "ID" in hp.columns and not acc_map.empty:
        idd = _clean_to_str(hp["ID"]).str.replace(r"\D", "", regex=True)
        tmp = pd.DataFrame({"_hid": idd}).reset_index().merge(acc_map.rename(columns={"_acc_id": "_hid"}), on="_hid", how="left")
        j3 = pd.Series(np.nan, index=hp.index, dtype="object")
        j3.loc[tmp["index"]] = tmp["_acc_id12"].values

    out = pd.Series(np.nan, index=hp.index, dtype="object")
    for cand in (j1, j2, j3):
        if cand is not None:
            out = out.where(out.notna(), cand)
    return out


def ensure_inp_any(acc: pd.DataFrame, hp: pd.DataFrame, join_id12: pd.Series) -> pd.Series:
    """Archived notebook note for 07_wave_healthcare_access_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if "inp_any" in acc.columns and not pd.isna(acc["inp_any"]).all():
        return pd.to_numeric(acc["inp_any"], errors="coerce")
    if hp.empty or join_id12.isna().all():
        return pd.Series(np.nan, index=acc.index)
    ee003_col = next((c for c in hp.columns if c.lower() == "ee003"), None)
    if ee003_col is None:
        return pd.Series(np.nan, index=acc.index)
    ee = (pd.to_numeric(hp[ee003_col], errors="coerce") == 1).astype("float64")
    t = pd.DataFrame({"join_ID12": join_id12, "ee": ee}).dropna(subset=["join_ID12"])
    g = t.groupby("join_ID12", as_index=False)["ee"].max()
    return acc.merge(g, left_on="ID12", right_on="join_ID12", how="left")["ee"]


def ew_score(df: pd.DataFrame, pos_cols: list[str], to_100=True, minmax_eps=1e-9):
    if len(pos_cols) == 0:
        return pd.Series(np.nan, index=df.index), pd.Series(dtype="float64"), {}
    X = df[pos_cols].copy()
    # Original notebook comment normalized for the public code archive.
    shift = (-X.min(skipna=True)).clip(lower=0)
    X = X + shift
    # Original notebook comment normalized for the public code archive.
    X = X.loc[:, X.notna().any(axis=0)]
    nunique = X.nunique(dropna=True)
    X = X.loc[:, nunique > 1]
    if X.shape[1] == 0:
        return pd.Series(0.0, index=df.index), pd.Series(dtype="float64"), {}
    # Original notebook comment normalized for the public code archive.
    Xn = (X - X.min()) / (X.max() - X.min() + minmax_eps)
    keep = Xn.sum(axis=0) > 0
    Xn = Xn.loc[:, keep]
    if Xn.shape[1] == 0:
        return pd.Series(0.0, index=df.index), pd.Series(dtype="float64"), {}
    # Original notebook comment normalized for the public code archive.
    P = Xn / (Xn.sum(axis=0) + 1e-12)
    n = (P.notna().any(axis=1)).sum()
    k = 1.0 / np.log(n if n > 1 else 2)
    E = -k * (P.replace(0, np.nan) * np.log(P.replace(0, np.nan))).sum(axis=0).fillna(0)
    D = 1 - E
    w = (D / D.sum()) if D.sum() > 0 else pd.Series(1.0 / len(D), index=D.index)
    S = (Xn * w).sum(axis=1)
    if to_100:
        S = 100 * S / (w.sum() if w.sum() != 0 else 1.0)
    return S.reindex(df.index), w, {}


def write_dta_smart(df: pd.DataFrame, out_path: Path, var_labels=None):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    import re as _re
    cols = list(df.columns)
    new = []
    used = set()
    for c in cols:
        base = _re.sub(r"[^0-9A-Za-z_]", "_", str(c))[:32]
        name, i = base, 1
        while name in used:
            suf = f"_{i}"
            name = base[:32 - len(suf)] + suf
            i += 1
        new.append(name)
        used.add(name)
    if new != cols:
        df = df.rename(columns=dict(zip(cols, new)))

    def _obj_str(s):
        s = s.astype(object)
        m = s.isna()
        t = s.astype(str)
        t[m] = None
        return t

    for c in [x for x in ["ID12", "householdID10", "ID", "householdID", "communityID"] if x in df.columns]:
        df[c] = _obj_str(df[c])
    for c in df.select_dtypes(include=["object"]).columns:
        if df[c].notna().sum() == 0:
            df[c] = df[c].astype("float64")
        else:
            df[c] = _obj_str(df[c])
    for c in df.select_dtypes(include=["bool"]).columns:
        df[c] = df[c].astype("float64")

    try:
        import pyreadstat
        try:
            if "variable_labels" in inspect.signature(pyreadstat.write_dta).parameters:
                pyreadstat.write_dta(
                    df.copy(), str(out_path), version=118,
                    variable_labels={c: (var_labels.get(c, "") if var_labels else "") for c in df.columns}
                )
            else:
                pyreadstat.write_dta(df.copy(), str(out_path), version=118)
            print("Saved DTA via pyreadstat ->", out_path)
            return
        except Exception as e:
            print("[INFO] Notebook progress message.", e)
            raise
    except Exception:
        pass

    try:
        df.copy().to_stata(out_path, write_index=False, version=118, variable_labels=(var_labels or {}))
        print("Saved DTA via pandas ->", out_path)
    except Exception as e2:
        print("[INFO] Notebook progress message.", e2)
        df.copy().to_stata(out_path, write_index=False, version=118)
        print("Saved DTA via pandas (no labels) ->", out_path)


# =============================================================================
def main():
    # Access_TimeCost
    acc = try_read_access_table()
    if "ID12" not in acc.columns:
        raise ValueError("2013_Access_TimeCost 中缺少 ID12。")
    acc["ID12"] = _clean_to_str(acc["ID12"]).str.replace(r"\D", "", regex=True)
    acc = acc.sort_index().drop_duplicates(subset=["ID12"], keep="first")
    print("[INFO] Notebook progress message.", acc.shape)

    # Original notebook comment normalized for the public code archive.
    hp = read_health(find_health_file())
    if not hp.empty:
        join_id12 = build_join_id12_for_health(hp, acc)
        tot = len(join_id12)
        cov = int(join_id12.notna().sum())
        if tot > 0:
            print("[INFO] Notebook progress message.")
        else:
            print("[INFO] Notebook progress message.")
    else:
        join_id12 = pd.Series(np.nan, index=pd.RangeIndex(0))

    # Original notebook comment normalized for the public code archive.
    subj_cols = []

    # Original notebook comment normalized for the public code archive.
    if not hp.empty and {"ed001", "ed002"} <= {c.lower() for c in hp.columns} and join_id12.notna().any():
        ed001 = pd.to_numeric(hp[[c for c in hp.columns if c.lower() == "ed001"][0]], errors="coerce")
        ed002 = pd.to_numeric(hp[[c for c in hp.columns if c.lower() == "ed002"][0]], errors="coerce")
        unmet = ((ed002 == 1) & (ed001 == 2)).astype("float64")
        t = pd.DataFrame({"join_ID12": join_id12, "bar_unmet_outpt": unmet})
        g = (t.dropna(subset=["join_ID12"]).groupby("join_ID12", as_index=False)["bar_unmet_outpt"].max())
        acc = acc.merge(g, left_on="ID12", right_on="join_ID12", how="left").drop(columns=["join_ID12"])
    else:
        acc["bar_unmet_outpt"] = (acc.get("has_outpt", pd.Series(0, index=acc.index)).fillna(0) == 0).astype("float64")
    subj_cols.append("bar_unmet_outpt")

    # Original notebook comment normalized for the public code archive.
    if not hp.empty and any(c.lower() == "ee001" for c in hp.columns) and join_id12.notna().any():
        ee001 = (pd.to_numeric(hp[[c for c in hp.columns if c.lower() == "ee001"][0]], errors="coerce") == 1).astype("float64")
        t = pd.DataFrame({"join_ID12": join_id12, "EE001_any": ee001}).dropna(subset=["join_ID12"])
        g = t.groupby("join_ID12", as_index=False)["EE001_any"].max()
        acc = acc.merge(g, left_on="ID12", right_on="join_ID12", how="left").drop(columns=["join_ID12"])
    else:
        acc["EE001_any"] = np.nan

    acc["inp_any"] = ensure_inp_any(acc, hp, join_id12)
    acc["bar_advised_no_hosp"] = ((acc["EE001_any"] == 1) & (acc["inp_any"] != 1)).astype("float64")
    if "EE001_any" in acc.columns:
        acc.drop(columns=["EE001_any"], inplace=True)
    subj_cols.append("bar_advised_no_hosp")

    # Original notebook comment normalized for the public code archive.
    if not hp.empty and join_id12.notna().any():
        ed_mask = any_reason(hp, "ed003", ED003_BARRIER_CODES)
        ee_mask = any_reason(hp, "ee002", EE002_BARRIER_CODES)
        t1 = pd.DataFrame({"join_ID12": join_id12, "bar_ed003": ed_mask}).dropna(subset=["join_ID12"])
        t2 = pd.DataFrame({"join_ID12": join_id12, "bar_ee002": ee_mask}).dropna(subset=["join_ID12"])
        g1 = t1.groupby("join_ID12", as_index=False)["bar_ed003"].max()
        g2 = t2.groupby("join_ID12", as_index=False)["bar_ee002"].max()
        acc = acc.merge(g1, left_on="ID12", right_on="join_ID12", how="left").drop(columns=["join_ID12"])
        acc = acc.merge(g2, left_on="ID12", right_on="join_ID12", how="left").drop(columns=["join_ID12"])
    else:
        acc["bar_ed003"] = np.nan
        acc["bar_ee002"] = np.nan
    subj_cols += ["bar_ed003", "bar_ee002"]

    subj_use = [c for c in subj_cols if c in acc.columns]

    # Original notebook comment normalized for the public code archive.
    real_use = [c for c in [
        "outpt_time_month_unc", "outpt_dist_month_unc", "outpt_cost_month_unc",
        "inp_time_single_unc", "inp_dist_single_unc", "inp_cost_single_unc",
    ] if c in acc.columns]

    # Original notebook comment normalized for the public code archive.
    subj_score, subj_w, _ = ew_score(acc, subj_use, to_100=True)
    real_score, real_w, _ = ew_score(acc, real_use, to_100=True)

    # Original notebook comment normalized for the public code archive.
    comp_score = (W_DIM_SUBJ * subj_score.fillna(0) + W_DIM_REAL * real_score.fillna(0)) / (W_DIM_SUBJ + W_DIM_REAL)

    # Original notebook comment normalized for the public code archive.
    keep_ids = [c for c in ["ID12", "householdID10", "ID", "householdID", "communityID"] if c in acc.columns]
    cols_out  = keep_ids + subj_use + real_use + ["has_outpt", "inp_any", "outpt_walk", "outpt_homevisit"]
    cols_out  = [c for c in cols_out if c in acc.columns]
    out = acc[cols_out].copy()
    out["主观障碍指数(0-100)"] = subj_score
    out["已实现成本时间指数(0-100)"] = real_score
    out["就医可达性综合指数(0-100)"] = comp_score

    # Excel output note.
    for c in [x for x in ["ID12", "householdID10", "ID", "householdID", "communityID"] if x in out.columns]:
        out[c] = out[c].astype(object).astype(str).where(~out[c].isna(), None)
    out.to_excel(OUT_XLSX, index=False)
    print("Excel ->", OUT_XLSX)

    # Original notebook comment normalized for the public code archive.
    var_labels = {
        "ID12": "个人ID(12位)", "householdID10": "householdID(10位)", "ID": "ID(原始)", "householdID": "householdID(原始)",
        "communityID": "社区(7位)",
        "bar_unmet_outpt": "主观障碍-生病未门诊(1/0)",
        "bar_advised_no_hosp": "主观障碍-建议住院未住(1/0)",
        "bar_ed003": "主观障碍-门诊理由含交通/距离/时间/费用(1/0)",
        "bar_ee002": "主观障碍-住院理由含交通/距离/时间/费用(1/0)",
        "outpt_time_month_unc": "门诊-月单程时间合计(分钟)",
        "outpt_dist_month_unc": "门诊-月单程距离合计(同单位)",
        "outpt_cost_month_unc": "门诊-月单程交通费合计(元)",
        "inp_time_single_unc": "住院-单程时间(分钟)",
        "inp_dist_single_unc": "住院-单程距离(同单位)",
        "inp_cost_single_unc": "住院-单程交通费(元)",
        "has_outpt": "过去月是否门诊(1/0/NA)",
        "inp_any": "过去年是否住院(1/0/NA)",
        "outpt_walk": "门诊-步行(1/0/NA)",
        "outpt_homevisit": "门诊-上门服务(1/0/NA)",
        "主观障碍指数(0-100)": "熵权-主观障碍(越大越差)",
        "已实现成本时间指数(0-100)": "熵权-已实现成本/时间(越大越差)",
        "就医可达性综合指数(0-100)": "0.5*主观 + 0.5*已实现（可调）",
    }
    write_dta_smart(out.copy(), OUT_DTA, var_labels=var_labels)
    print("DTA  ->", OUT_DTA)

    # Original notebook comment normalized for the public code archive.
    def pretty(tag, w):
        if w.empty:
            print("[INFO] Notebook progress message."); return
        print("[INFO] Notebook progress message.")
        ww = (w / w.sum()).sort_values(ascending=False)
        for k, v in ww.items():
            print(f"  - {k}: {v:.3f}")

    pretty("主观障碍", subj_w)
    pretty("已实现成本/时间", real_w)
    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()




# =============================================================================
# Source notebook
# =============================================================================
# record_type : wave_step
# year        : 2015
# step        : 7
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 07_wave_healthcare_access_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 3
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 07_wave_healthcare_access_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import re
from pathlib import Path
import numpy as np
import pandas as pd

# =============================================================================
DATA_DIRS = [
    r"E:\project_flood_impact_assessment\老年人健康\CHARLS\charls原版数据\原始数据+问卷2011~2020\2015\CHARLS2015r",
    r"E:\\impact_assessment_child_order\\older\\health\\2015"
]
OUT_DIR = Path(r"E:\\impact_assessment_child_order\\older\\hospital\\2015")
OUT_DTA  = OUT_DIR / "2015_Access_TimeCost.dta"
OUT_XLSX = OUT_DIR / "2015_Access_TimeCost.xlsx"

# Original notebook comment normalized for the public code archive.
LIKELY_FILENAMES = [
    "health_care_and_insurance.dta",
    "Health_Care_and_Insurance.dta",
    "HealthCareAndInsurance.dta",
    "Health care and insurance.dta",
]

# =============================================================================
def read_dta(path: Path) -> pd.DataFrame:
    if not path or not path.exists():
        raise FileNotFoundError(f"未找到文件：{path}")
    try:
        import pyreadstat
        df, _ = pyreadstat.read_dta(str(path), apply_value_formats=False)
        return df
    except Exception:
        return pd.read_stata(path, convert_categoricals=False)


def list_columns_quick(path: Path):
    """Archived notebook note for 07_wave_healthcare_access_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    try:
        import pyreadstat
        df, meta = pyreadstat.read_dta(str(path), apply_value_formats=False, row_limit=1)
        return list(df.columns)
    except Exception:
        # Original notebook comment normalized for the public code archive.
        df = pd.read_stata(path, convert_categoricals=False)
        return list(df.columns)


def find_health_table() -> Path:
    # Original notebook comment normalized for the public code archive.
    for d in DATA_DIRS:
        for name in LIKELY_FILENAMES:
            p = Path(d) / name
            if p.exists():
                return p
    # Original notebook comment normalized for the public code archive.
    need_any = {"ed013", "ed014_1", "ed014_2", "ed015", "ed005_", "ed012",
                "ee013", "ee014_1", "ee014_2", "ee015", "ee003"}
    for d in DATA_DIRS:
        dd = Path(d)
        if not dd.exists():
            continue
        for pp in dd.glob("*.dta"):
            try:
                cols = {c.lower() for c in list_columns_quick(pp)}
            except Exception:
                continue
            # Original notebook comment normalized for the public code archive.
            hit = 0
            for k in need_any:
                base = k.split("_")[0]
                if any(c.startswith(base) for c in cols):
                    hit += 1
            if hit >= 7:
                return pp
    raise FileNotFoundError("未在 2015 目录中定位到含 ED/EE 核心变量的 health/insurance 表。请检查目录或补充 LIKELY_FILENAMES。")


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


def normalize_keys(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 07_wave_healthcare_access_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()
    low = {c.lower(): c for c in df.columns}

    def pick(*names):
        for n in names:
            if n.lower() in low:
                return low[n.lower()]
        return None

    c_hh  = pick("householdid", "householdID", "hhid")
    c_pid = pick("id", "pid", "PID")
    c_com = pick("communityid", "communityID", "commid")

    if c_hh and c_hh != "householdID":
        df.rename(columns={c_hh: "householdID"}, inplace=True)
    if c_pid and c_pid != "ID":
        df.rename(columns={c_pid: "ID"}, inplace=True)
    if c_com and c_com != "communityID":
        df.rename(columns={c_com: "communityID"}, inplace=True)

    if "householdID" in df.columns:
        hh_digits = _clean_to_str(df["householdID"]).str.replace(r"\D", "", regex=True)
        hh9  = hh_digits.where(hh_digits.str.len() == 9,  np.nan)
        hh10 = hh_digits.where(hh_digits.str.len() == 10, np.nan)
        df["householdID10"] = np.where(
            hh10.notna(), hh10.str.zfill(10),
            np.where(hh9.notna(), hh9.str.zfill(9) + "0", np.nan)
        ).astype("object")
        df["householdID"] = hh_digits.where(hh_digits.str.len() > 0, np.nan).astype("object")
    else:
        df["householdID10"] = np.nan

    if "communityID" in df.columns:
        df["communityID"] = digits_width(df["communityID"], 7)

    # Original notebook comment normalized for the public code archive.
    if "ID" in df.columns:
        id_digits = _clean_to_str(df["ID"]).str.replace(r"\D", "", regex=True)
        direct12 = id_digits.where(id_digits.str.len() == 12, np.nan).astype("object")
        pn2 = id_digits.where(id_digits.str.len() >= 2, np.nan).str[-2:]
    else:
        direct12 = pd.Series(np.nan, index=df.index, dtype="object")
        pn2 = pd.Series(np.nan, index=df.index, dtype="object")

    made = np.where(pd.Series(pn2).notna() & df["householdID10"].notna(),
                    df["householdID10"] + pn2.astype("object"), np.nan)
    df["ID12"] = pd.Series(direct12, index=df.index).fillna(pd.Series(made, index=df.index)).astype("object")
    return df


def sum_by_prefix(df: pd.DataFrame, prefix: str) -> pd.Series:
    cols = [c for c in df.columns if str(c).lower().startswith(prefix.lower())]
    if not cols:
        return pd.Series(np.nan, index=df.index, dtype="float64")
    arr = df[cols].apply(pd.to_numeric, errors="coerce")
    s = arr.sum(axis=1, skipna=True)
    all_na = arr.isna().all(axis=1)
    return s.where(~all_na, np.nan)


def sanitize_for_stata(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    for c in d.select_dtypes(include=["Int8", "Int16", "Int32", "Int64", "UInt8", "UInt16", "UInt32", "UInt64", "boolean"]).columns:
        d[c] = d[c].astype("float64")
    for c in d.select_dtypes(include=["object", "string"]).columns:
        s = d[c].astype(object)
        m = pd.isna(s)
        s = s.astype(str)
        s[m] = None
        d[c] = s.map(lambda x: x if (x is None or len(x) <= 2000) else x[:2000])
    return d


def write_out(df: pd.DataFrame, path_dta: Path, path_xlsx: Path):
    path_dta.parent.mkdir(parents=True, exist_ok=True)
    df2 = sanitize_for_stata(df.copy())
    try:
        import pyreadstat
        pyreadstat.write_dta(df2, str(path_dta), version=118)
    except Exception:
        df2.to_stata(str(path_dta), write_index=False, version=118)
    df.to_excel(path_xlsx, index=False, na_rep="NA")
    print("[INFO] Notebook progress message.")


# =============================================================================
def flag_has_outpt(df: pd.DataFrame) -> pd.Series:
    """Archived notebook note for 07_wave_healthcare_access_time.

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
    """Archived notebook note for 07_wave_healthcare_access_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if "ee003" in {c.lower() for c in df.columns}:
        col = [c for c in df.columns if c.lower() == "ee003"][0]
        ee003 = pd.to_numeric(df[col], errors="coerce")
        return (ee003 == 1).astype("int8", copy=False)
    evid = [c for c in df.columns if re.match(r"^ee00(4|5|6|7|8|9|24|25|26|27)(_1)?$", str(c), flags=re.I)]
    if evid:
        A = df[evid].apply(pd.to_numeric, errors="coerce")
        has = A.notna() & (A != 0)
        return has.any(axis=1).astype("int8", copy=False)
    return pd.Series(np.nan, index=df.index)


def to_num_col(df: pd.DataFrame, name: str) -> pd.Series:
    """Archived notebook note for 07_wave_healthcare_access_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if name in df.columns:
        return pd.to_numeric(df[name], errors="coerce")
    return pd.Series(np.nan, index=df.index, dtype="float64")


# =============================================================================
def main():
    # Original notebook comment normalized for the public code archive.
    health_path = find_health_table()
    print("health_file:", health_path)

    med = read_dta(health_path)
    med = normalize_keys(med)

    # Original notebook comment normalized for the public code archive.
    has_outpt = flag_has_outpt(med)  # 1/0/NA
    inp_any   = flag_inp_any(med)    # 1/0/NA

    ed012      = to_num_col(med, "ed012")      # Original notebook comment normalized for the public code archive.
    ed014_2    = to_num_col(med, "ed014_2")    # Original notebook comment normalized for the public code archive.
    ed013_raw  = to_num_col(med, "ed013")      # Original notebook comment normalized for the public code archive.
    ed0141_raw = to_num_col(med, "ed014_1")    # Original notebook comment normalized for the public code archive.
    ed015_raw  = to_num_col(med, "ed015")      # Original notebook comment normalized for the public code archive.
    ed005_visits = sum_by_prefix(med, "ed005")  # Original notebook comment normalized for the public code archive.

    ee014_2    = to_num_col(med, "ee014_2")    # Original notebook comment normalized for the public code archive.
    ee013_raw  = to_num_col(med, "ee013")      # Original notebook comment normalized for the public code archive.
    ee0141_raw = to_num_col(med, "ee014_1")    # Original notebook comment normalized for the public code archive.
    ee015_raw  = to_num_col(med, "ee015")      # Original notebook comment normalized for the public code archive.

    # Original notebook comment normalized for the public code archive.
    U_out_ask        = (has_outpt == 1) & ed012.notna() & (ed012 != 1)
    U_out_walk       = U_out_ask & (ed014_2 == 1)
    U_out_nonwalk    = U_out_ask & ed014_2.notna() & (ed014_2 != 1)
    U_out_cost_asked = U_out_ask & (ed015_raw.notna() | U_out_nonwalk)

    no_out_or_home   = (has_outpt == 0) | (ed012 == 1)  # Original notebook comment normalized for the public code archive.

    U_inp_ask        = (inp_any == 1)
    U_inp_walk       = U_inp_ask & (ee014_2 == 1)
    U_inp_nonwalk    = U_inp_ask & ee014_2.notna() & (ee014_2 != 1)
    U_inp_cost_asked = U_inp_ask & (ee015_raw.notna() | U_inp_nonwalk)

    # Original notebook comment normalized for the public code archive.
    outpt_dist_single_anl = np.where(U_out_ask, ed013_raw,  np.nan)
    outpt_time_single_anl = np.where(U_out_ask, ed0141_raw, np.nan)
    outpt_cost_single_anl = np.where(U_out_cost_asked, np.where(U_out_walk, 0, ed015_raw), np.nan)

    inp_dist_single_anl   = np.where(U_inp_ask, ee013_raw,  np.nan)
    inp_time_single_anl   = np.where(U_inp_ask, ee0141_raw, np.nan)
    inp_cost_single_anl   = np.where(U_inp_cost_asked, np.where(U_inp_walk, 0, ee015_raw), np.nan)

    # Original notebook comment normalized for the public code archive.
    def prefer_then_struct0(amount, no_event_mask):
        a = pd.to_numeric(pd.Series(amount), errors="coerce")
        nem = pd.Series(no_event_mask).astype("float64") == 1
        out = a.copy()
        out.loc[a.isna() & nem] = 0.0
        return out

    outpt_dist_single_unc = np.where(no_out_or_home, 0, ed013_raw)
    outpt_time_single_unc = prefer_then_struct0(ed0141_raw, no_out_or_home)
    outpt_cost_single_unc = np.where(
        has_outpt == 0, 0,
        np.where(ed012 == 1, 0, np.where(ed014_2 == 1, 0, ed015_raw))
    )

    # Original notebook comment normalized for the public code archive.
    outpt_dist_month_unc  = (ed005_visits * 2) * pd.to_numeric(outpt_dist_single_unc, errors="coerce")
    outpt_time_month_unc  = (ed005_visits * 2) * pd.to_numeric(outpt_time_single_unc, errors="coerce")
    outpt_cost_month_unc  = (ed005_visits * 2) * pd.to_numeric(pd.Series(outpt_cost_single_unc).fillna(0), errors="coerce")

    inp_dist_single_unc   = np.where(inp_any == 0, 0, ee013_raw)
    inp_time_single_unc   = prefer_then_struct0(ee0141_raw, (inp_any == 0))
    inp_cost_single_unc   = np.where(inp_any == 0, 0, np.where(ee014_2 == 1, 0, ee015_raw))

    # Original notebook comment normalized for the public code archive.
    keys = [c for c in ["ID", "householdID", "communityID", "householdID10", "ID12"] if c in med.columns]
    res = med[keys].copy() if keys else pd.DataFrame(index=med.index)

    # Original notebook comment normalized for the public code archive.
    res["ed012_homevisit"]   = ed012
    res["ed013_raw"]         = ed013_raw
    res["ed014_1_raw"]       = ed0141_raw
    res["ed014_2_mode_raw"]  = ed014_2
    res["ed015_raw"]         = ed015_raw
    res["ed005_visits"]      = ed005_visits

    res["ee013_raw"]         = ee013_raw
    res["ee014_1_raw"]       = ee0141_raw
    res["ee014_2_mode_raw"]  = ee014_2
    res["ee015_raw"]         = ee015_raw

    res["has_outpt"] = has_outpt.astype("float64")
    res["inp_any"]   = inp_any.astype("float64")

    # Original notebook comment normalized for the public code archive.
    res["outpt_dist_single_anl"] = outpt_dist_single_anl
    res["outpt_time_single_anl"] = outpt_time_single_anl
    res["outpt_cost_single_anl"] = outpt_cost_single_anl

    res["outpt_dist_single_unc"] = outpt_dist_single_unc
    res["outpt_time_single_unc"] = outpt_time_single_unc
    res["outpt_cost_single_unc"] = outpt_cost_single_unc

    res["outpt_dist_month_unc"]  = outpt_dist_month_unc
    res["outpt_time_month_unc"]  = outpt_time_month_unc
    res["outpt_cost_month_unc"]  = outpt_cost_month_unc

    res["outpt_walk"]      = (U_out_walk).astype("float64")       # Original notebook comment normalized for the public code archive.
    res["outpt_homevisit"] = (ed012 == 1).astype("float64")       # Original notebook comment normalized for the public code archive.

    # Original notebook comment normalized for the public code archive.
    res["inp_dist_single_anl"] = inp_dist_single_anl
    res["inp_time_single_anl"] = inp_time_single_anl
    res["inp_cost_single_anl"] = inp_cost_single_anl

    res["inp_dist_single_unc"] = inp_dist_single_unc
    res["inp_time_single_unc"] = inp_time_single_unc
    res["inp_cost_single_unc"] = inp_cost_single_unc

    res["inp_walk"] = (U_inp_walk).astype("float64")

    # Original notebook comment normalized for the public code archive.
    addr_cols = [c for c in med.columns if re.match(r"^(ed016|ee012)", str(c), flags=re.I)]
    if addr_cols:
        res = pd.concat([res, med[addr_cols]], axis=1)

    # Original notebook comment normalized for the public code archive.
    write_out(res, OUT_DTA, OUT_XLSX)
    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 5
# ------------------------------------------------------------------------------
# =============================================================================
# =============================================================================

# -*- coding: utf-8 -*-
"""Archived notebook note for 07_wave_healthcare_access_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import re, inspect
import numpy as np
import pandas as pd
from pathlib import Path

# =============================================================================
ROOT = Path(r"E:\\impact_assessment_child_order\\older\\hospital\\2015")
ACC_XLSX = ROOT / "2015_Access_TimeCost.xlsx"
ACC_DTA  = ROOT / "2015_Access_TimeCost.dta"

HEALTH_DIRS = [
    r"E:\project_flood_impact_assessment\老年人健康\CHARLS\charls原版数据\原始数据+问卷2011~2020\2015\CHARLS2015r",
    r"E:\\impact_assessment_child_order\\older\\health\\2015",
    r"/mnt/data",
]
LIKELY_HEALTH = [
    "Health_Care_and_Insurance.dta", "Health_Care_and_Insurance.dta",
    "HealthCareAndInsurance.dta", "Health care and insurance.dta"
]

OUT_XLSX = ROOT / "2015_Access_result.xlsx"
OUT_DTA  = ROOT / "2015_Access_result.dta"

# =============================================================================
W_DIM_SUBJ = 0.5
W_DIM_REAL = 0.5
ED003_BARRIER_CODES = {2, 3, 4, 5}
EE002_BARRIER_CODES = {2, 3, 4, 5}

# =============================================================================
def _clean_to_str(s: pd.Series) -> pd.Series:
    s = pd.Series(s, dtype="object"); m = s.isna()
    t = s[~m].astype(str).str.strip().str.replace(r"\.0$","",regex=True).str.replace(r"\s+","",regex=True)
    s.loc[~m]=t; s.loc[m]=np.nan; return s


def try_read_access_table() -> pd.DataFrame:
    if ACC_XLSX.exists(): return pd.read_excel(ACC_XLSX)
    if ACC_DTA.exists():
        try:
            import pyreadstat; df,_=pyreadstat.read_dta(str(ACC_DTA), apply_value_formats=False); return df
        except Exception: return pd.read_stata(ACC_DTA, convert_categoricals=False)
    raise FileNotFoundError("未找到 2015_Access_TimeCost.(xlsx/dta)，请先运行脚本1。")


def find_health_file() -> Path | None:
    for d in HEALTH_DIRS:
        for name in LIKELY_HEALTH:
            p = Path(d)/name
            if p.exists(): return p
    for d in HEALTH_DIRS:
        dd=Path(d);
        if not dd.exists(): continue
        for pp in dd.glob("*.dta"):
            cols=set()
            try:
                import pyreadstat; df,_=pyreadstat.read_dta(str(pp),apply_value_formats=False,row_limit=1); cols={c.lower() for c in df.columns}
            except Exception:
                try:
                    df=pd.read_stata(pp, convert_categoricals=False); cols={c.lower() for c in df.columns}
                except Exception:
                    continue
            if {"ed001","ed002","ee001","ee002","ee003"} & cols:
                return pp
    return None


def read_health(path: Path | None) -> pd.DataFrame:
    if path is None or not path.exists():
        print("[INFO] Notebook progress message.")
        return pd.DataFrame()
    try:
        import pyreadstat; df,_=pyreadstat.read_dta(str(path), apply_value_formats=False); return df
    except Exception: return pd.read_stata(path, convert_categoricals=False)


def any_reason(df: pd.DataFrame, prefix: str, code_set: set[int]) -> pd.Series:
    pat = rf"^{prefix}(?:s|_)?\d+_?$"
    cand=[c for c in df.columns if re.match(pat,str(c),flags=re.I)]
    if cand:
        mask=[];
        for c in cand:
            m=re.findall(r"(\d+)",str(c));
            if m and int(m[-1]) in code_set: mask.append(c)
        if mask:
            arr=(df[mask].apply(pd.to_numeric, errors="coerce")==1)
            return arr.any(axis=1).astype("float64")
        return pd.Series(np.nan, index=df.index)
    base=next((c for c in df.columns if c.lower()==prefix.lower()), None)
    if base is not None:
        v=pd.to_numeric(df[base], errors="coerce")
        return v.isin(list(code_set)).astype("float64")
    return pd.Series(np.nan, index=df.index)


def build_join_id12_for_health(hp: pd.DataFrame, acc: pd.DataFrame) -> pd.Series:
    if hp.empty: return pd.Series(np.nan, index=hp.index, dtype="object")
    acc_id_digits = _clean_to_str(acc.get("ID")).str.replace(r"\D","",regex=True) if "ID" in acc.columns else pd.Series(index=acc.index, dtype="object")
    acc_map = pd.DataFrame({"_acc_id": acc_id_digits, "_acc_id12": _clean_to_str(acc.get("ID12")) if "ID12" in acc.columns else pd.Series(dtype="object")})
    acc_map = acc_map.dropna().drop_duplicates(subset=["_acc_id"])
    j1=None
    if "ID12" in hp.columns:
        j1=_clean_to_str(hp["ID12"]).str.replace(r"\D","",regex=True); j1=j1.where(j1.str.len()==12, np.nan)
    j2=None
    if "householdID" in hp.columns and "ID" in hp.columns:
        hh=_clean_to_str(hp["householdID"]).str.replace(r"\D","",regex=True)
        hh10=np.where(hh.where(hh.str.len()==10,np.nan).notna(), hh.str.zfill(10),
                      np.where(hh.where(hh.str.len()==9,np.nan).notna(), hh.str.zfill(9)+"0", np.nan))
        idd=_clean_to_str(hp["ID"]).str.replace(r"\D","",regex=True)
        pn2=idd.where(idd.str.len()>=2, np.nan).str[-2:]
        j2=pd.Series(np.where(pd.Series(hh10).notna() & pn2.notna(), pd.Series(hh10)+pn2, np.nan), index=hp.index, dtype="object")
    j3=None
    if "ID" in hp.columns and not acc_map.empty:
        idd=_clean_to_str(hp["ID"]).str.replace(r"\D","",regex=True)
        tmp=pd.DataFrame({"_hid": idd}).reset_index().merge(acc_map.rename(columns={"_acc_id":"_hid"}), on="_hid", how="left")
        j3=pd.Series(np.nan, index=hp.index, dtype="object"); j3.loc[tmp["index"]]=tmp["_acc_id12"].values
    out=pd.Series(np.nan, index=hp.index, dtype="object")
    for cand in (j1,j2,j3):
        if cand is not None: out=out.where(out.notna(), cand)
    return out


def ensure_inp_any(acc: pd.DataFrame, hp: pd.DataFrame, join_id12: pd.Series) -> pd.Series:
    if "inp_any" in acc.columns and not pd.isna(acc["inp_any"]).all():
        return pd.to_numeric(acc["inp_any"], errors="coerce")
    if hp.empty or join_id12.isna().all():
        return pd.Series(np.nan, index=acc.index)
    ee003_col = next((c for c in hp.columns if c.lower()=="ee003"), None)
    if ee003_col is None:
        return pd.Series(np.nan, index=acc.index)
    ee = (pd.to_numeric(hp[ee003_col], errors="coerce")==1).astype("float64")
    t = pd.DataFrame({"join_ID12": join_id12, "ee": ee}).dropna(subset=["join_ID12"])
    g = t.groupby("join_ID12", as_index=False)["ee"].max()
    return acc.merge(g, left_on="ID12", right_on="join_ID12", how="left")["ee"]


def ew_score(df: pd.DataFrame, pos_cols: list[str], to_100=True, minmax_eps=1e-9):
    if len(pos_cols)==0: return pd.Series(np.nan,index=df.index), pd.Series(dtype="float64"), {}
    X=df[pos_cols].copy(); shift=(-X.min(skipna=True)).clip(lower=0); X=X+shift
    X=X.loc[:, X.notna().any(axis=0)]; nunique=X.nunique(dropna=True); X=X.loc[:, nunique>1]
    if X.shape[1]==0: return pd.Series(0.0,index=df.index), pd.Series(dtype="float64"), {}
    Xn=(X - X.min())/(X.max()-X.min()+minmax_eps)
    keep=Xn.sum(axis=0)>0; Xn=Xn.loc[:, keep]
    if Xn.shape[1]==0: return pd.Series(0.0,index=df.index), pd.Series(dtype="float64"), {}
    P=Xn/(Xn.sum(axis=0)+1e-12); n=(P.notna().any(axis=1)).sum(); k=1.0/np.log(n if n>1 else 2)
    E=-k*(P.replace(0,np.nan)*np.log(P.replace(0,np.nan))).sum(axis=0).fillna(0); D=1-E
    w=(D/D.sum()) if D.sum()>0 else pd.Series(1.0/len(D), index=D.index)
    S=(Xn*w).sum(axis=1);
    if to_100: S=100*S/(w.sum() if w.sum()!=0 else 1.0)
    return S.reindex(df.index), w, {}


def write_dta_smart(df: pd.DataFrame, out_path: Path, var_labels=None):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    import re as _re
    cols=list(df.columns)
    new=[]; used=set()
    for c in cols:
        base=_re.sub(r"[^0-9A-Za-z_]","_",str(c))[:32]
        name,i=base,1
        while name in used:
            suf=f"_{i}"; name=base[:32-len(suf)]+suf; i+=1
        new.append(name); used.add(name)
    if new!=cols: df=df.rename(columns=dict(zip(cols,new)))
    def _obj_str(s): m=s.isna(); t=s.astype(object).astype(str); t[m]=None; return t
    for c in [x for x in ["ID12","householdID10","ID","householdID","communityID"] if x in df.columns]:
        df[c]=_obj_str(df[c])
    for c in df.select_dtypes(include=["object"]).columns:
        if df[c].notna().sum()==0: df[c]=df[c].astype("float64")
        else: df[c]=_obj_str(df[c])
    for c in df.select_dtypes(include=["bool"]).columns: df[c]=df[c].astype("float64")
    try:
        import pyreadstat
        try:
            if "variable_labels" in inspect.signature(pyreadstat.write_dta).parameters:
                pyreadstat.write_dta(df.copy(), str(out_path), version=118,
                                     variable_labels={c:(var_labels.get(c,"") if var_labels else "") for c in df.columns})
            else:
                pyreadstat.write_dta(df.copy(), str(out_path), version=118)
            print("Saved DTA via pyreadstat ->", out_path); return
        except Exception as e: print("[INFO] Notebook progress message.", e); raise
    except Exception: pass
    try:
        df.copy().to_stata(out_path, write_index=False, version=118, variable_labels=(var_labels or {}))
        print("Saved DTA via pandas ->", out_path)
    except Exception as e2:
        print("[INFO] Notebook progress message.", e2)
        df.copy().to_stata(out_path, write_index=False, version=118)
        print("Saved DTA via pandas (no labels) ->", out_path)


# =============================================================================
def main():
    # Access_TimeCost
    acc=try_read_access_table()
    if "ID12" not in acc.columns: raise ValueError("2015_Access_TimeCost 中缺少 ID12。")
    acc["ID12"]=_clean_to_str(acc["ID12"]).str.replace(r"\D","",regex=True)
    acc=acc.sort_index().drop_duplicates(subset=["ID12"], keep="first")
    print("[INFO] Notebook progress message.", acc.shape)

    # Original notebook comment normalized for the public code archive.
    hp=read_health(find_health_file())
    if not hp.empty:
        join_id12=build_join_id12_for_health(hp, acc)
        tot=len(join_id12); cov=int(join_id12.notna().sum())
        if tot>0: print("[INFO] Notebook progress message.")
        else: print("[INFO] Notebook progress message.")
    else:
        join_id12=pd.Series(np.nan, index=pd.RangeIndex(0))

    # Original notebook comment normalized for the public code archive.
    subj_cols=[]
    if not hp.empty and {"ed001","ed002"} <= {c.lower() for c in hp.columns} and join_id12.notna().any():
        ed001=pd.to_numeric(hp[[c for c in hp.columns if c.lower()=="ed001"][0]], errors="coerce")
        ed002=pd.to_numeric(hp[[c for c in hp.columns if c.lower()=="ed002"][0]], errors="coerce")
        unmet=((ed002==1)&(ed001==2)).astype("float64")
        t=pd.DataFrame({"join_ID12":join_id12,"bar_unmet_outpt":unmet})
        g=(t.dropna(subset=["join_ID12"]).groupby("join_ID12", as_index=False)["bar_unmet_outpt"].max())
        acc=acc.merge(g, left_on="ID12", right_on="join_ID12", how="left").drop(columns=["join_ID12"])
    else:
        acc["bar_unmet_outpt"]=(acc.get("has_outpt", pd.Series(0,index=acc.index)).fillna(0)==0).astype("float64")
    subj_cols.append("bar_unmet_outpt")

    if not hp.empty and any(c.lower()=="ee001" for c in hp.columns) and join_id12.notna().any():
        ee001=(pd.to_numeric(hp[[c for c in hp.columns if c.lower()=="ee001"][0]],errors="coerce")==1).astype("float64")
        t=pd.DataFrame({"join_ID12":join_id12,"EE001_any":ee001}).dropna(subset=["join_ID12"])
        g=t.groupby("join_ID12", as_index=False)["EE001_any"].max()
        acc=acc.merge(g, left_on="ID12", right_on="join_ID12", how="left").drop(columns=["join_ID12"])
    else:
        acc["EE001_any"]=np.nan

    acc["inp_any"]=ensure_inp_any(acc, hp, join_id12)
    acc["bar_advised_no_hosp"]=((acc["EE001_any"]==1)&(acc["inp_any"]!=1)).astype("float64")
    if "EE001_any" in acc.columns: acc.drop(columns=["EE001_any"], inplace=True)
    subj_cols.append("bar_advised_no_hosp")

    if not hp.empty and join_id12.notna().any():
        ed_mask=any_reason(hp,"ed003",ED003_BARRIER_CODES)
        ee_mask=any_reason(hp,"ee002",EE002_BARRIER_CODES)
        t1=pd.DataFrame({"join_ID12":join_id12,"bar_ed003":ed_mask}).dropna(subset=["join_ID12"])
        t2=pd.DataFrame({"join_ID12":join_id12,"bar_ee002":ee_mask}).dropna(subset=["join_ID12"])
        g1=t1.groupby("join_ID12", as_index=False)["bar_ed003"].max()
        g2=t2.groupby("join_ID12", as_index=False)["bar_ee002"].max()
        acc=acc.merge(g1, left_on="ID12", right_on="join_ID12", how="left").drop(columns=["join_ID12"])
        acc=acc.merge(g2, left_on="ID12", right_on="join_ID12", how="left").drop(columns=["join_ID12"])
    else:
        acc["bar_ed003"]=np.nan; acc["bar_ee002"]=np.nan
    subj_cols+=["bar_ed003","bar_ee002"]

    subj_use=[c for c in subj_cols if c in acc.columns]

    # Original notebook comment normalized for the public code archive.
    real_use=[c for c in ["outpt_time_month_unc","outpt_dist_month_unc","outpt_cost_month_unc",
                          "inp_time_single_unc","inp_dist_single_unc","inp_cost_single_unc"] if c in acc.columns]

    # Original notebook comment normalized for the public code archive.
    subj_score, subj_w, _=ew_score(acc, subj_use, to_100=True)
    real_score, real_w, _=ew_score(acc, real_use, to_100=True)
    comp_score=(W_DIM_SUBJ*subj_score.fillna(0)+W_DIM_REAL*real_score.fillna(0))/(W_DIM_SUBJ+W_DIM_REAL)

    # Original notebook comment normalized for the public code archive.
    keep_ids=[c for c in ["ID12","householdID10","ID","householdID","communityID"] if c in acc.columns]
    cols_out=keep_ids+subj_use+real_use+["has_outpt","inp_any","outpt_walk","outpt_homevisit"]
    cols_out=[c for c in cols_out if c in acc.columns]
    out=acc[cols_out].copy()
    out["主观障碍指数(0-100)"]=subj_score
    out["已实现成本时间指数(0-100)"]=real_score
    out["就医可达性综合指数(0-100)"]=comp_score

    for c in [x for x in ["ID12","householdID10","ID","householdID","communityID"] if x in out.columns]:
        out[c]=out[c].astype(object).astype(str).where(~out[c].isna(), None)
    out.to_excel(OUT_XLSX, index=False)
    print("Excel ->", OUT_XLSX)

    var_labels = {
        "ID12":"个人ID(12位)","householdID10":"householdID(10位)","ID":"ID(原始)","householdID":"householdID(原始)",
        "communityID":"社区(7位)",
        "bar_unmet_outpt":"主观障碍-生病未门诊(1/0)",
        "bar_advised_no_hosp":"主观障碍-建议住院未住(1/0)",
        "bar_ed003":"主观障碍-门诊理由含交通/距离/时间/费用(1/0)",
        "bar_ee002":"主观障碍-住院理由含交通/距离/时间/费用(1/0)",
        "outpt_time_month_unc":"门诊-月单程时间合计(分钟)",
        "outpt_dist_month_unc":"门诊-月单程距离合计(同单位)",
        "outpt_cost_month_unc":"门诊-月单程交通费合计(元)",
        "inp_time_single_unc":"住院-单程时间(分钟)",
        "inp_dist_single_unc":"住院-单程距离(同单位)",
        "inp_cost_single_unc":"住院-单程交通费(元)",
        "has_outpt":"过去月是否门诊(1/0/NA)",
        "inp_any":"过去年是否住院(1/0/NA)",
        "outpt_walk":"门诊-步行(1/0/NA)",
        "outpt_homevisit":"门诊-上门服务(1/0/NA)",
        "主观障碍指数(0-100)":"熵权-主观障碍(越大越差)",
        "已实现成本时间指数(0-100)":"熵权-已实现成本/时间(越大越差)",
        "就医可达性综合指数(0-100)":"0.5*主观 + 0.5*已实现（可调）",
    }
    write_dta_smart(out.copy(), OUT_DTA, var_labels=var_labels)
    print("DTA  ->", OUT_DTA)

    def pretty(tag, w):
        if w.empty: print("[INFO] Notebook progress message."); return
        print("[INFO] Notebook progress message.")
        ww=(w/w.sum()).sort_values(ascending=False)
        for k,v in ww.items(): print(f"  - {k}: {v:.3f}")
    pretty("主观障碍", subj_w)
    pretty("已实现成本/时间", real_w)
    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()




# =============================================================================
# Source notebook
# =============================================================================
# record_type : wave_step
# year        : 2018
# step        : 7
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 07_wave_healthcare_access_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 3
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 07_wave_healthcare_access_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import re
from pathlib import Path
import numpy as np
import pandas as pd

# =============================================================================
DATA_DIRS = [
    r"E:\project_flood_impact_assessment\老年人健康\CHARLS\charls原版数据\原始数据+问卷2011~2020\2018\CHARLS2018r",
    r"E:\impact_assessment_child_order\older\health\2018",
    r"/mnt/data",
]
OUT_DIR = Path(r"E:\impact_assessment_child_order\older\hospital\2018")
OUT_DTA  = OUT_DIR / "2018_Access_TimeCost.dta"
OUT_XLSX = OUT_DIR / "2018_Access_TimeCost.xlsx"

# Original notebook comment normalized for the public code archive.
LIKELY_FILENAMES = [
    "Health_Care_and_Insurance.dta",
    "health_care_and_insurance.dta",
    "HealthCareAndInsurance.dta",
    "Health care and insurance.dta",
]

# =============================================================================
def read_dta(path: Path) -> pd.DataFrame:
    if not path or not path.exists():
        raise FileNotFoundError(f"未找到文件：{path}")
    try:
        import pyreadstat
        df, _ = pyreadstat.read_dta(str(path), apply_value_formats=False)
        return df
    except Exception:
        return pd.read_stata(path, convert_categoricals=False)


def list_columns_quick(path: Path):
    """Archived notebook note for 07_wave_healthcare_access_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    try:
        import pyreadstat
        df, _ = pyreadstat.read_dta(str(path), apply_value_formats=False, row_limit=1)
        return list(df.columns)
    except Exception:
        df = pd.read_stata(path, convert_categoricals=False)
        return list(df.columns)


def find_health_table() -> Path:
    # Original notebook comment normalized for the public code archive.
    for d in DATA_DIRS:
        for name in LIKELY_FILENAMES:
            p = Path(d) / name
            if p.exists():
                return p
    # Original notebook comment normalized for the public code archive.
    need_any = {"ed013", "ed014_1", "ed014_2", "ed015", "ed005_", "ed012",
                "ee013", "ee014_1", "ee014_2", "ee015", "ee003"}
    for d in DATA_DIRS:
        dd = Path(d)
        if not dd.exists():
            continue
        for pp in dd.glob("*.dta"):
            try:
                cols = {c.lower() for c in list_columns_quick(pp)}
            except Exception:
                continue
            hit = 0
            for k in need_any:
                base = k.split("_")[0]
                if any(c.startswith(base) for c in cols):
                    hit += 1
            if hit >= 7:
                return pp
    raise FileNotFoundError("未在 2018 目录中定位到含 ED/EE 核心变量的 health/insurance 表。请检查目录或补充 LIKELY_FILENAMES。")


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


def normalize_keys(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 07_wave_healthcare_access_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()
    low = {c.lower(): c for c in df.columns}

    def pick(*names):
        for n in names:
            if n.lower() in low:
                return low[n.lower()]
        return None

    c_hh  = pick("householdid", "householdID", "hhid")
    c_pid = pick("id", "pid", "PID")
    c_com = pick("communityid", "communityID", "commid")

    if c_hh and c_hh != "householdID":
        df.rename(columns={c_hh: "householdID"}, inplace=True)
    if c_pid and c_pid != "ID":
        df.rename(columns={c_pid: "ID"}, inplace=True)
    if c_com and c_com != "communityID":
        df.rename(columns={c_com: "communityID"}, inplace=True)

    if "householdID" in df.columns:
        hh_digits = _clean_to_str(df["householdID"]).str.replace(r"\D", "", regex=True)
        hh9  = hh_digits.where(hh_digits.str.len() == 9,  np.nan)
        hh10 = hh_digits.where(hh_digits.str.len() == 10, np.nan)
        df["householdID10"] = np.where(
            hh10.notna(), hh10.str.zfill(10),
            np.where(hh9.notna(), hh9.str.zfill(9) + "0", np.nan)
        ).astype("object")
        df["householdID"] = hh_digits.where(hh_digits.str.len() > 0, np.nan).astype("object")
    else:
        df["householdID10"] = np.nan

    if "communityID" in df.columns:
        df["communityID"] = digits_width(df["communityID"], 7)

    # Original notebook comment normalized for the public code archive.
    if "ID" in df.columns:
        id_digits = _clean_to_str(df["ID"]).str.replace(r"\D", "", regex=True)
        direct12 = id_digits.where(id_digits.str.len() == 12, np.nan).astype("object")
        pn2 = id_digits.where(id_digits.str.len() >= 2, np.nan).str[-2:]
    else:
        direct12 = pd.Series(np.nan, index=df.index, dtype="object")
        pn2 = pd.Series(np.nan, index=df.index, dtype="object")

    made = np.where(pd.Series(pn2).notna() & df["householdID10"].notna(),
                    df["householdID10"] + pn2.astype("object"), np.nan)
    df["ID12"] = pd.Series(direct12, index=df.index).fillna(pd.Series(made, index=df.index)).astype("object")
    return df


def sum_by_prefix(df: pd.DataFrame, prefix: str) -> pd.Series:
    cols = [c for c in df.columns if str(c).lower().startswith(prefix.lower())]
    if not cols:
        return pd.Series(np.nan, index=df.index, dtype="float64")
    arr = df[cols].apply(pd.to_numeric, errors="coerce")
    s = arr.sum(axis=1, skipna=True)
    all_na = arr.isna().all(axis=1)
    return s.where(~all_na, np.nan)


def sanitize_for_stata(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    for c in d.select_dtypes(include=["Int8", "Int16", "Int32", "Int64", "UInt8", "UInt16", "UInt32", "UInt64", "boolean"]).columns:
        d[c] = d[c].astype("float64")
    for c in d.select_dtypes(include=["object", "string"]).columns:
        s = d[c].astype(object)
        m = pd.isna(s)
        s = s.astype(str)
        s[m] = None
        d[c] = s.map(lambda x: x if (x is None or len(x) <= 2000) else x[:2000])
    return d


def write_out(df: pd.DataFrame, path_dta: Path, path_xlsx: Path):
    path_dta.parent.mkdir(parents=True, exist_ok=True)
    df2 = sanitize_for_stata(df.copy())
    try:
        import pyreadstat
        pyreadstat.write_dta(df2, str(path_dta), version=118)
    except Exception:
        df2.to_stata(str(path_dta), write_index=False, version=118)
    df.to_excel(path_xlsx, index=False, na_rep="NA")
    print("[INFO] Notebook progress message.")


# =============================================================================
def flag_has_outpt(df: pd.DataFrame) -> pd.Series:
    """Archived notebook note for 07_wave_healthcare_access_time.

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
    """Archived notebook note for 07_wave_healthcare_access_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if "ee003" in {c.lower() for c in df.columns}:
        col = [c for c in df.columns if c.lower() == "ee003"][0]
        ee003 = pd.to_numeric(df[col], errors="coerce")
        return (ee003 == 1).astype("int8", copy=False)
    evid = [c for c in df.columns if re.match(r"^ee00(4|5|6|7|8|9|24|25|26|27)(_1)?$", str(c), flags=re.I)]
    if evid:
        A = df[evid].apply(pd.to_numeric, errors="coerce")
        has = A.notna() & (A != 0)
        return has.any(axis=1).astype("int8", copy=False)
    return pd.Series(np.nan, index=df.index)


def to_num_col(df: pd.DataFrame, name: str) -> pd.Series:
    """Archived notebook note for 07_wave_healthcare_access_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if name in df.columns:
        return pd.to_numeric(df[name], errors="coerce")
    return pd.Series(np.nan, index=df.index, dtype="float64")


# =============================================================================
def main():
    # Original notebook comment normalized for the public code archive.
    health_path = find_health_table()
    print("health_file:", health_path)

    med = read_dta(health_path)
    med = normalize_keys(med)

    # Original notebook comment normalized for the public code archive.
    has_outpt = flag_has_outpt(med)  # 1/0/NA
    inp_any   = flag_inp_any(med)    # 1/0/NA

    ed012      = to_num_col(med, "ed012")      # Original notebook comment normalized for the public code archive.
    ed014_2    = to_num_col(med, "ed014_2")    # Original notebook comment normalized for the public code archive.
    ed013_raw  = to_num_col(med, "ed013")      # Original notebook comment normalized for the public code archive.
    ed0141_raw = to_num_col(med, "ed014_1")    # Original notebook comment normalized for the public code archive.
    ed015_raw  = to_num_col(med, "ed015")      # Original notebook comment normalized for the public code archive.
    ed005_visits = sum_by_prefix(med, "ed005")  # Original notebook comment normalized for the public code archive.

    ee014_2    = to_num_col(med, "ee014_2")    # Original notebook comment normalized for the public code archive.
    ee013_raw  = to_num_col(med, "ee013")      # Original notebook comment normalized for the public code archive.
    ee0141_raw = to_num_col(med, "ee014_1")    # Original notebook comment normalized for the public code archive.
    ee015_raw  = to_num_col(med, "ee015")      # Original notebook comment normalized for the public code archive.

    # Original notebook comment normalized for the public code archive.
    U_out_ask        = (has_outpt == 1) & ed012.notna() & (ed012 != 1)
    U_out_walk       = U_out_ask & (ed014_2 == 1)
    U_out_nonwalk    = U_out_ask & ed014_2.notna() & (ed014_2 != 1)
    U_out_cost_asked = U_out_ask & (ed015_raw.notna() | U_out_nonwalk)

    no_out_or_home   = (has_outpt == 0) | (ed012 == 1)  # Original notebook comment normalized for the public code archive.

    U_inp_ask        = (inp_any == 1)
    U_inp_walk       = U_inp_ask & (ee014_2 == 1)
    U_inp_nonwalk    = U_inp_ask & ee014_2.notna() & (ee014_2 != 1)
    U_inp_cost_asked = U_inp_ask & (ee015_raw.notna() | U_inp_nonwalk)

    # Original notebook comment normalized for the public code archive.
    outpt_dist_single_anl = np.where(U_out_ask, ed013_raw,  np.nan)
    outpt_time_single_anl = np.where(U_out_ask, ed0141_raw, np.nan)
    outpt_cost_single_anl = np.where(U_out_cost_asked, np.where(U_out_walk, 0, ed015_raw), np.nan)

    inp_dist_single_anl   = np.where(U_inp_ask, ee013_raw,  np.nan)
    inp_time_single_anl   = np.where(U_inp_ask, ee0141_raw, np.nan)
    inp_cost_single_anl   = np.where(U_inp_cost_asked, np.where(U_inp_walk, 0, ee015_raw), np.nan)

    # Original notebook comment normalized for the public code archive.
    def prefer_then_struct0(amount, no_event_mask):
        a = pd.to_numeric(pd.Series(amount), errors="coerce")
        nem = pd.Series(no_event_mask).astype("float64") == 1
        out = a.copy()
        out.loc[a.isna() & nem] = 0.0
        return out

    outpt_dist_single_unc = np.where(no_out_or_home, 0, ed013_raw)
    outpt_time_single_unc = prefer_then_struct0(ed0141_raw, no_out_or_home)
    outpt_cost_single_unc = np.where(
        has_outpt == 0, 0,
        np.where(ed012 == 1, 0, np.where(ed014_2 == 1, 0, ed015_raw))
    )

    # Original notebook comment normalized for the public code archive.
    outpt_dist_month_unc  = (ed005_visits * 2) * pd.to_numeric(outpt_dist_single_unc, errors="coerce")
    outpt_time_month_unc  = (ed005_visits * 2) * pd.to_numeric(outpt_time_single_unc, errors="coerce")
    outpt_cost_month_unc  = (ed005_visits * 2) * pd.to_numeric(pd.Series(outpt_cost_single_unc).fillna(0), errors="coerce")

    inp_dist_single_unc   = np.where(inp_any == 0, 0, ee013_raw)
    inp_time_single_unc   = prefer_then_struct0(ee0141_raw, (inp_any == 0))
    inp_cost_single_unc   = np.where(inp_any == 0, 0, np.where(ee014_2 == 1, 0, ee015_raw))

    # Original notebook comment normalized for the public code archive.
    keys = [c for c in ["ID", "householdID", "communityID", "householdID10", "ID12"] if c in med.columns]
    res = med[keys].copy() if keys else pd.DataFrame(index=med.index)

    # Original notebook comment normalized for the public code archive.
    res["ed012_homevisit"]   = ed012
    res["ed013_raw"]         = ed013_raw
    res["ed014_1_raw"]       = ed0141_raw
    res["ed014_2_mode_raw"]  = ed014_2
    res["ed015_raw"]         = ed015_raw
    res["ed005_visits"]      = ed005_visits

    res["ee013_raw"]         = ee013_raw
    res["ee014_1_raw"]       = ee0141_raw
    res["ee014_2_mode_raw"]  = ee014_2
    res["ee015_raw"]         = ee015_raw

    res["has_outpt"] = has_outpt.astype("float64")
    res["inp_any"]   = inp_any.astype("float64")

    # Original notebook comment normalized for the public code archive.
    res["outpt_dist_single_anl"] = outpt_dist_single_anl
    res["outpt_time_single_anl"] = outpt_time_single_anl
    res["outpt_cost_single_anl"] = outpt_cost_single_anl

    res["outpt_dist_single_unc"] = outpt_dist_single_unc
    res["outpt_time_single_unc"] = outpt_time_single_unc
    res["outpt_cost_single_unc"] = outpt_cost_single_unc

    res["outpt_dist_month_unc"]  = outpt_dist_month_unc
    res["outpt_time_month_unc"]  = outpt_time_month_unc
    res["outpt_cost_month_unc"]  = outpt_cost_month_unc

    res["outpt_walk"]      = (U_out_walk).astype("float64")       # Original notebook comment normalized for the public code archive.
    res["outpt_homevisit"] = (ed012 == 1).astype("float64")       # Original notebook comment normalized for the public code archive.

    # Original notebook comment normalized for the public code archive.
    res["inp_dist_single_anl"] = inp_dist_single_anl
    res["inp_time_single_anl"] = inp_time_single_anl
    res["inp_cost_single_anl"] = inp_cost_single_anl

    res["inp_dist_single_unc"] = inp_dist_single_unc
    res["inp_time_single_unc"] = inp_time_single_unc
    res["inp_cost_single_unc"] = inp_cost_single_unc

    res["inp_walk"] = (U_inp_walk).astype("float64")

    # Original notebook comment normalized for the public code archive.
    addr_cols = [c for c in med.columns if re.match(r"^(ed016|ee012)", str(c), flags=re.I)]
    if addr_cols:
        res = pd.concat([res, med[addr_cols]], axis=1)

    # Original notebook comment normalized for the public code archive.
    write_out(res, OUT_DTA, OUT_XLSX)
    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 5
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 07_wave_healthcare_access_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import re, inspect
import numpy as np
import pandas as pd
from pathlib import Path

# =============================================================================
ROOT = Path(r"E:\impact_assessment_child_order\older\hospital\2018")
ACC_XLSX = ROOT / "2018_Access_TimeCost.xlsx"
ACC_DTA  = ROOT / "2018_Access_TimeCost.dta"

HEALTH_DIRS = [
    r"E:\project_flood_impact_assessment\老年人健康\CHARLS\charls原版数据\原始数据+问卷2011~2020\2018\CHARLS2018r",
    r"E:\impact_assessment_child_order\older\health\2018",
    r"/mnt/data",
]
LIKELY_HEALTH = [
    "Health_Care_and_Insurance.dta",
    "health_care_and_insurance.dta",
    "HealthCareAndInsurance.dta",
    "Health care and insurance.dta",
]

OUT_XLSX = ROOT / "2018_Access_result.xlsx"
OUT_DTA  = ROOT / "2018_Access_result.dta"

# =============================================================================
W_DIM_SUBJ = 0.5
W_DIM_REAL = 0.5
ED003_BARRIER_CODES = {2, 3, 4, 5}
EE002_BARRIER_CODES = {2, 3, 4, 5}

# =============================================================================
def _clean_to_str(s: pd.Series) -> pd.Series:
    s = pd.Series(s, dtype="object"); m = s.isna()
    t = s[~m].astype(str).str.strip().str.replace(r"\.0$","",regex=True).str.replace(r"\s+","",regex=True)
    s.loc[~m]=t; s.loc[m]=np.nan; return s


def try_read_access_table() -> pd.DataFrame:
    if ACC_XLSX.exists(): return pd.read_excel(ACC_XLSX)
    if ACC_DTA.exists():
        try:
            import pyreadstat; df,_=pyreadstat.read_dta(str(ACC_DTA), apply_value_formats=False); return df
        except Exception: return pd.read_stata(ACC_DTA, convert_categoricals=False)
    raise FileNotFoundError("未找到 2018_Access_TimeCost.(xlsx/dta)，请先运行脚本1。")


def find_health_file() -> Path | None:
    for d in HEALTH_DIRS:
        for name in LIKELY_HEALTH:
            p = Path(d)/name
            if p.exists(): return p
    for d in HEALTH_DIRS:
        dd=Path(d)
        if not dd.exists(): continue
        for pp in dd.glob("*.dta"):
            cols=set()
            try:
                import pyreadstat
                df,_=pyreadstat.read_dta(str(pp),apply_value_formats=False,row_limit=1)
                cols={c.lower() for c in df.columns}
            except Exception:
                try:
                    df=pd.read_stata(pp, convert_categoricals=False)
                    cols={c.lower() for c in df.columns}
                except Exception:
                    continue
            if {"ed001","ed002","ee001","ee002","ee003"} & cols:
                return pp
    return None


def read_health(path: Path | None) -> pd.DataFrame:
    if path is None or not path.exists():
        print("[INFO] Notebook progress message.")
        return pd.DataFrame()
    try:
        import pyreadstat; df,_=pyreadstat.read_dta(str(path), apply_value_formats=False); return df
    except Exception: return pd.read_stata(path, convert_categoricals=False)


def any_reason(df: pd.DataFrame, prefix: str, code_set: set[int]) -> pd.Series:
    """Archived notebook note for 07_wave_healthcare_access_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    pat = rf"^{prefix}(?:s|_)?\d+_?$"
    cand=[c for c in df.columns if re.match(pat,str(c),flags=re.I)]
    if cand:
        mask=[]
        for c in cand:
            m=re.findall(r"(\d+)",str(c))
            if m and int(m[-1]) in code_set: mask.append(c)
        if mask:
            arr=(df[mask].apply(pd.to_numeric, errors="coerce")==1)
            return arr.any(axis=1).astype("float64")
        return pd.Series(np.nan, index=df.index)
    base=next((c for c in df.columns if c.lower()==prefix.lower()), None)
    if base is not None:
        v=pd.to_numeric(df[base], errors="coerce")
        return v.isin(list(code_set)).astype("float64")
    return pd.Series(np.nan, index=df.index)


def build_join_id12_for_health(hp: pd.DataFrame, acc: pd.DataFrame) -> pd.Series:
    """Archived notebook note for 07_wave_healthcare_access_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if hp.empty: return pd.Series(np.nan, index=hp.index, dtype="object")
    acc_id_digits = _clean_to_str(acc.get("ID")).str.replace(r"\D","",regex=True) if "ID" in acc.columns else pd.Series(index=acc.index, dtype="object")
    acc_map = pd.DataFrame({"_acc_id": acc_id_digits, "_acc_id12": _clean_to_str(acc.get("ID12")) if "ID12" in acc.columns else pd.Series(dtype="object")})
    acc_map = acc_map.dropna().drop_duplicates(subset=["_acc_id"])
    j1=None
    if "ID12" in hp.columns:
        j1=_clean_to_str(hp["ID12"]).str.replace(r"\D","",regex=True); j1=j1.where(j1.str.len()==12, np.nan)
    j2=None
    if "householdID" in hp.columns and "ID" in hp.columns:
        hh=_clean_to_str(hp["householdID"]).str.replace(r"\D","",regex=True)
        hh10=np.where(hh.where(hh.str.len()==10,np.nan).notna(), hh.str.zfill(10),
                      np.where(hh.where(hh.str.len()==9,np.nan).notna(), hh.str.zfill(9)+"0", np.nan))
        idd=_clean_to_str(hp["ID"]).str.replace(r"\D","",regex=True)
        pn2=idd.where(idd.str.len()>=2, np.nan).str[-2:]
        j2=pd.Series(np.where(pd.Series(hh10).notna() & pn2.notna(), pd.Series(hh10)+pn2, np.nan), index=hp.index, dtype="object")
    j3=None
    if "ID" in hp.columns and not acc_map.empty:
        idd=_clean_to_str(hp["ID"]).str.replace(r"\D","",regex=True)
        tmp=pd.DataFrame({"_hid": idd}).reset_index().merge(acc_map.rename(columns={"_acc_id":"_hid"}), on="_hid", how="left")
        j3=pd.Series(np.nan, index=hp.index, dtype="object"); j3.loc[tmp["index"]]=tmp["_acc_id12"].values
    out=pd.Series(np.nan, index=hp.index, dtype="object")
    for cand in (j1,j2,j3):
        if cand is not None: out=out.where(out.notna(), cand)
    return out


def ensure_inp_any(acc: pd.DataFrame, hp: pd.DataFrame, join_id12: pd.Series) -> pd.Series:
    """Archived notebook note for 07_wave_healthcare_access_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if "inp_any" in acc.columns and not pd.isna(acc["inp_any"]).all():
        return pd.to_numeric(acc["inp_any"], errors="coerce")
    if hp.empty or join_id12.isna().all():
        return pd.Series(np.nan, index=acc.index)
    ee003_col = next((c for c in hp.columns if c.lower()=="ee003"), None)
    if ee003_col is None:
        return pd.Series(np.nan, index=acc.index)
    ee = (pd.to_numeric(hp[ee003_col], errors="coerce")==1).astype("float64")
    t = pd.DataFrame({"join_ID12": join_id12, "ee": ee}).dropna(subset=["join_ID12"])
    g = t.groupby("join_ID12", as_index=False)["ee"].max()
    return acc.merge(g, left_on="ID12", right_on="join_ID12", how="left")["ee"]


def ew_score(df: pd.DataFrame, pos_cols: list[str], to_100=True, minmax_eps=1e-9):
    if len(pos_cols)==0: return pd.Series(np.nan,index=df.index), pd.Series(dtype="float64"), {}
    X=df[pos_cols].copy()
    shift=(-X.min(skipna=True)).clip(lower=0); X=X+shift
    X=X.loc[:, X.notna().any(axis=0)]
    nunique=X.nunique(dropna=True); X=X.loc[:, nunique>1]
    if X.shape[1]==0: return pd.Series(0.0,index=df.index), pd.Series(dtype="float64"), {}
    Xn=(X - X.min())/(X.max()-X.min()+minmax_eps)
    keep=Xn.sum(axis=0)>0; Xn=Xn.loc[:, keep]
    if Xn.shape[1]==0: return pd.Series(0.0,index=df.index), pd.Series(dtype="float64"), {}
    P=Xn/(Xn.sum(axis=0)+1e-12)
    n=(P.notna().any(axis=1)).sum(); k=1.0/np.log(n if n>1 else 2)
    E=-k*(P.replace(0,np.nan)*np.log(P.replace(0,np.nan))).sum(axis=0).fillna(0)
    D=1-E
    w=(D/D.sum()) if D.sum()>0 else pd.Series(1.0/len(D), index=D.index)
    S=(Xn*w).sum(axis=1)
    if to_100: S=100*S/(w.sum() if w.sum()!=0 else 1.0)
    return S.reindex(df.index), w, {}


def write_dta_smart(df: pd.DataFrame, out_path: Path, var_labels=None):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    import re as _re
    cols=list(df.columns)
    new=[]; used=set()
    for c in cols:
        base=_re.sub(r"[^0-9A-Za-z_]","_",str(c))[:32]
        name,i=base,1
        while name in used:
            suf=f"_{i}"; name=base[:32-len(suf)]+suf; i+=1
        new.append(name); used.add(name)
    if new!=cols: df=df.rename(columns=dict(zip(cols,new)))

    def _obj_str(s):
        s = s.astype(object)
        m = s.isna()
        t = s.astype(str)
        t[m] = None
        return t

    for c in [x for x in ["ID12","householdID10","ID","householdID","communityID"] if x in df.columns]:
        df[c]=_obj_str(df[c])
    for c in df.select_dtypes(include=["object"]).columns:
        if df[c].notna().sum()==0: df[c]=df[c].astype("float64")
        else: df[c]=_obj_str(df[c])
    for c in df.select_dtypes(include=["bool"]).columns: df[c]=df[c].astype("float64")

    try:
        import pyreadstat
        try:
            if "variable_labels" in inspect.signature(pyreadstat.write_dta).parameters:
                pyreadstat.write_dta(
                    df.copy(), str(out_path), version=118,
                    variable_labels={c:(var_labels.get(c,"") if var_labels else "") for c in df.columns}
                )
            else:
                pyreadstat.write_dta(df.copy(), str(out_path), version=118)
            print("Saved DTA via pyreadstat ->", out_path); return
        except Exception as e:
            print("[INFO] Notebook progress message.", e)
            raise
    except Exception:
        pass
    try:
        df.copy().to_stata(out_path, write_index=False, version=118, variable_labels=(var_labels or {}))
        print("Saved DTA via pandas ->", out_path)
    except Exception as e2:
        print("[INFO] Notebook progress message.", e2)
        df.copy().to_stata(out_path, write_index=False, version=118)
        print("Saved DTA via pandas (no labels) ->", out_path)


# =============================================================================
def main():
    # Access_TimeCost
    acc=try_read_access_table()
    if "ID12" not in acc.columns: raise ValueError("2018_Access_TimeCost 中缺少 ID12。")
    acc["ID12"]=_clean_to_str(acc["ID12"]).str.replace(r"\D","",regex=True)
    acc=acc.sort_index().drop_duplicates(subset=["ID12"], keep="first")
    print("[INFO] Notebook progress message.", acc.shape)

    # Original notebook comment normalized for the public code archive.
    hp=read_health(find_health_file())
    if not hp.empty:
        join_id12=build_join_id12_for_health(hp, acc)
        tot=len(join_id12); cov=int(join_id12.notna().sum())
        if tot>0: print("[INFO] Notebook progress message.")
        else: print("[INFO] Notebook progress message.")
    else:
        join_id12=pd.Series(np.nan, index=pd.RangeIndex(0))

    # Original notebook comment normalized for the public code archive.
    subj_cols=[]
    # Original notebook comment normalized for the public code archive.
    if not hp.empty and {"ed001","ed002"} <= {c.lower() for c in hp.columns} and join_id12.notna().any():
        ed001=pd.to_numeric(hp[[c for c in hp.columns if c.lower()=="ed001"][0]], errors="coerce")
        ed002=pd.to_numeric(hp[[c for c in hp.columns if c.lower()=="ed002"][0]], errors="coerce")
        unmet=((ed002==1)&(ed001==2)).astype("float64")
        t=pd.DataFrame({"join_ID12":join_id12,"bar_unmet_outpt":unmet})
        g=(t.dropna(subset=["join_ID12"]).groupby("join_ID12", as_index=False)["bar_unmet_outpt"].max())
        acc=acc.merge(g, left_on="ID12", right_on="join_ID12", how="left").drop(columns=["join_ID12"])
    else:
        acc["bar_unmet_outpt"]=(acc.get("has_outpt", pd.Series(0,index=acc.index)).fillna(0)==0).astype("float64")
    subj_cols.append("bar_unmet_outpt")

    # Original notebook comment normalized for the public code archive.
    if not hp.empty and any(c.lower()=="ee001" for c in hp.columns) and join_id12.notna().any():
        ee001=(pd.to_numeric(hp[[c for c in hp.columns if c.lower()=="ee001"][0]],errors="coerce")==1).astype("float64")
        t=pd.DataFrame({"join_ID12":join_id12,"EE001_any":ee001}).dropna(subset=["join_ID12"])
        g=t.groupby("join_ID12", as_index=False)["EE001_any"].max()
        acc=acc.merge(g, left_on="ID12", right_on="join_ID12", how="left").drop(columns=["join_ID12"])
    else:
        acc["EE001_any"]=np.nan

    acc["inp_any"]=ensure_inp_any(acc, hp, join_id12)
    acc["bar_advised_no_hosp"]=((acc["EE001_any"]==1)&(acc["inp_any"]!=1)).astype("float64")
    if "EE001_any" in acc.columns: acc.drop(columns=["EE001_any"], inplace=True)
    subj_cols.append("bar_advised_no_hosp")

    # Original notebook comment normalized for the public code archive.
    if not hp.empty and join_id12.notna().any():
        ed_mask=any_reason(hp,"ed003",ED003_BARRIER_CODES)
        ee_mask=any_reason(hp,"ee002",EE002_BARRIER_CODES)
        t1=pd.DataFrame({"join_ID12":join_id12,"bar_ed003":ed_mask}).dropna(subset=["join_ID12"])
        t2=pd.DataFrame({"join_ID12":join_id12,"bar_ee002":ee_mask}).dropna(subset=["join_ID12"])
        g1=t1.groupby("join_ID12", as_index=False)["bar_ed003"].max()
        g2=t2.groupby("join_ID12", as_index=False)["bar_ee002"].max()
        acc=acc.merge(g1, left_on="ID12", right_on="join_ID12", how="left").drop(columns=["join_ID12"])
        acc=acc.merge(g2, left_on="ID12", right_on="join_ID12", how="left").drop(columns=["join_ID12"])
    else:
        acc["bar_ed003"]=np.nan; acc["bar_ee002"]=np.nan
    subj_cols+=["bar_ed003","bar_ee002"]

    subj_use=[c for c in subj_cols if c in acc.columns]

    # Original notebook comment normalized for the public code archive.
    real_use=[c for c in [
        "outpt_time_month_unc","outpt_dist_month_unc","outpt_cost_month_unc",
        "inp_time_single_unc","inp_dist_single_unc","inp_cost_single_unc"
    ] if c in acc.columns]

    # Original notebook comment normalized for the public code archive.
    subj_score, subj_w, _=ew_score(acc, subj_use, to_100=True)
    real_score, real_w, _=ew_score(acc, real_use, to_100=True)
    comp_score=(W_DIM_SUBJ*subj_score.fillna(0)+W_DIM_REAL*real_score.fillna(0))/(W_DIM_SUBJ+W_DIM_REAL)

    # Original notebook comment normalized for the public code archive.
    keep_ids=[c for c in ["ID12","householdID10","ID","householdID","communityID"] if c in acc.columns]
    cols_out=keep_ids+subj_use+real_use+["has_outpt","inp_any","outpt_walk","outpt_homevisit"]
    cols_out=[c for c in cols_out if c in acc.columns]
    out=acc[cols_out].copy()
    out["主观障碍指数(0-100)"]=subj_score
    out["已实现成本时间指数(0-100)"]=real_score
    out["就医可达性综合指数(0-100)"]=comp_score

    # Excel output note.
    for c in [x for x in ["ID12","householdID10","ID","householdID","communityID"] if x in out.columns]:
        out[c]=out[c].astype(object).astype(str).where(~out[c].isna(), None)
    out.to_excel(OUT_XLSX, index=False)
    print("Excel ->", OUT_XLSX)

    # Original notebook comment normalized for the public code archive.
    var_labels = {
        "ID12":"个人ID(12位)","householdID10":"householdID(10位)","ID":"ID(原始)","householdID":"householdID(原始)",
        "communityID":"社区(7位)",
        "bar_unmet_outpt":"主观障碍-生病未门诊(1/0)",
        "bar_advised_no_hosp":"主观障碍-建议住院未住(1/0)",
        "bar_ed003":"主观障碍-门诊理由含交通/距离/时间/费用(1/0)",
        "bar_ee002":"主观障碍-住院理由含交通/距离/时间/费用(1/0)",
        "outpt_time_month_unc":"门诊-月单程时间合计(分钟)",
        "outpt_dist_month_unc":"门诊-月单程距离合计(同单位)",
        "outpt_cost_month_unc":"门诊-月单程交通费合计(元)",
        "inp_time_single_unc":"住院-单程时间(分钟)",
        "inp_dist_single_unc":"住院-单程距离(同单位)",
        "inp_cost_single_unc":"住院-单程交通费(元)",
        "has_outpt":"过去月是否门诊(1/0/NA)",
        "inp_any":"过去年是否住院(1/0/NA)",
        "outpt_walk":"门诊-步行(1/0/NA)",
        "outpt_homevisit":"门诊-上门服务(1/0/NA)",
        "主观障碍指数(0-100)":"熵权-主观障碍(越大越差)",
        "已实现成本时间指数(0-100)":"熵权-已实现成本/时间(越大越差)",
        "就医可达性综合指数(0-100)":"0.5*主观 + 0.5*已实现（可调）",
    }
    write_dta_smart(out.copy(), OUT_DTA, var_labels=var_labels)
    print("DTA  ->", OUT_DTA)

    # Original notebook comment normalized for the public code archive.
    def pretty(tag, w):
        if w.empty: print("[INFO] Notebook progress message."); return
        print("[INFO] Notebook progress message.")
        ww=(w/w.sum()).sort_values(ascending=False)
        for k,v in ww.items(): print(f"  - {k}: {v:.3f}")
    pretty("主观障碍", subj_w)
    pretty("已实现成本/时间", real_w)
    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()




# =============================================================================
# Source notebook
# =============================================================================
# record_type : wave_step
# year        : 2020
# step        : 7
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 07_wave_healthcare_access_time.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
