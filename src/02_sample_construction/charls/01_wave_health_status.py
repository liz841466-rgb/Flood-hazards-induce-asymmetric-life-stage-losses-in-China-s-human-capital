#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""



# =============================================================================
# Source notebook
# =============================================================================
# record_type : wave_step
# year        : 2011
# step        : 1
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 7
# ------------------------------------------------------------------------------
# =============================================================================
exists_queries = set(sum_codes.loc[sum_codes["exists"], "query"])
matched_vars = (res_codes
                .loc[(res_codes["match_type"] != "NOT_FOUND") &
                     (res_codes["query"].isin(exists_queries)), "variable"]
                .dropna().tolist())

# Original notebook comment normalized for the public code archive.
seen = set()
matched_vars = [x for x in matched_vars if not (x in seen or seen.add(x))]

id_cols = ["householdID", "communityID"]
keep_cols = [c for c in id_cols if c in df.columns] + [c for c in matched_vars if c in df.columns]
keep_cols = keep_cols or [c for c in id_cols if c in df.columns]
sub = df[keep_cols].copy()

# =============================================================================
import numpy as np
import pandas as pd

def sanitize_for_stata(d):
    d = d.copy()

    # Original notebook comment normalized for the public code archive.
    ext_ints = list(d.select_dtypes(include=["Int8","Int16","Int32","Int64",
                                            "UInt8","UInt16","UInt32","UInt64",
                                            "boolean"]).columns)
    for c in ext_ints:
        d[c] = d[c].astype("float64")

    # Original notebook comment normalized for the public code archive.
    for c in d.select_dtypes(include=["datetime","datetimetz"]).columns:
        d[c] = d[c].view("int64") / 1e9  # Original notebook comment normalized for the public code archive.

    # Original notebook comment normalized for the public code archive.
    obj_cols = list(d.select_dtypes(include=["object","string"]).columns)
    for c in obj_cols:
        s = d[c].astype(object)
        # Original notebook comment normalized for the public code archive.
        mask = pd.isna(s)
        s = s.astype(str)
        s[mask] = None
        # Original notebook comment normalized for the public code archive.
        s = s.map(lambda x: x if (x is None or len(x) <= 2000) else x[:2000])
        d[c] = s

    return d

sub_clean = sanitize_for_stata(sub)

# =============================================================================
from pathlib import Path
out_path = r"E:\impact_assessment_child_order\older\health\2011\physical_mental.dta"
Path(Path(out_path).parent).mkdir(parents=True, exist_ok=True)

# Original notebook comment normalized for the public code archive.
try:
    import pyreadstat
    pyreadstat.write_dta(sub_clean, out_path, version=118)
    print("[INFO] Notebook progress message.")
except Exception as e:
    print("[INFO] Notebook progress message.", e)
    sub_clean.to_stata(out_path, write_index=False, version=117)
    print("[INFO] Notebook progress message.")


# ------------------------------------------------------------------------------
# Notebook cell 23
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
import re
from pathlib import Path
import numpy as np
import pandas as pd

# =============================================================================
base_in_d = r"E:\project_flood_impact_assessment\老年人健康\CHARLS\charls原版数据\原始数据+问卷2011~2020\2011\household_and_community_questionnaire_data"
f_d      = fr"{base_in_d}\health_status_and_functioning.dta"

base_in_cdce = r"E:\project_flood_impact_assessment\老年人健康\CHARLS\charls原版数据\原始数据+问卷2011~2020\2011\household_and_community_questionnaire_data"
f_cd    = fr"{base_in_cdce}\family_information.dta"
f_ce    = fr"{base_in_cdce}\family_transfer.dta"

base_out = r"E:\impact_assessment_child_order\older\health\2011"
pm_out   = fr"{base_out}\physical_mental.dta"
s1_out   = fr"{base_out}\social_1.dta"
s2_out   = fr"{base_out}\social_2.dta"
health_dta  = fr"{base_out}\health.dta"
health_xls  = fr"{base_out}\health.xls"
health_xlsx = fr"{base_out}\health.xlsx"

# =================================================
# Original notebook comment normalized for the public code archive.
# =================================================
def read_dta_basic(path):
    df = pd.read_stata(path, convert_categoricals=False)
    print("[INFO] Notebook progress message.")
    return df

def read_dta_with_labels(path):
    var_labels = {}
    try:
        import pyreadstat
        df, meta = pyreadstat.read_dta(path, apply_value_formats=False, formats_as_category=False)
        var_labels = meta.column_names_to_labels or {}
    except Exception as e:
        print("[INFO] Notebook progress message.")
        df = pd.read_stata(path, convert_categoricals=False)
        var_labels = {c: "" for c in df.columns}
    print("[INFO] Notebook progress message.")
    return df, var_labels

def _clean_to_str(s: pd.Series) -> pd.Series:
    """Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = pd.Series(s, dtype="object")
    m = s.isna()
    sc = s[~m].astype(str).str.strip()
    sc = sc.str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = sc
    s.loc[m] = np.nan
    return s

def _canon_fixed(s: pd.Series, width: int) -> pd.Series:
    """Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = _clean_to_str(s)
    m = s.notna()
    s.loc[m] = s.loc[m].astype(str).str.zfill(width)
    return s

def _digits_width(s: pd.Series, width: int) -> pd.Series:
    """Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    t = _clean_to_str(s).str.replace(r"\D", "", regex=True)
    t = t.where(t.str.len() > 0, np.nan)
    return t.where(t.isna(), t.str[-width:].str.zfill(width)).astype("object")

def add_id12_hhid10_2011(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()
    hh9  = _digits_width(df["householdID"], 9) if "householdID" in df.columns else pd.Series(np.nan, index=df.index)
    id11 = _digits_width(df["ID"],          11) if "ID"          in df.columns else pd.Series(np.nan, index=df.index)
    if "householdID" in df.columns:
        df["householdID"] = _canon_fixed(df["householdID"], 9)
    if "communityID" in df.columns:
        df["communityID"] = _canon_fixed(df["communityID"], 7)
    if "ID" in df.columns:
        df["ID"] = _canon_fixed(df["ID"], 11)

    df["householdID10"] = hh9.where(hh9.isna(), hh9 + "0")
    pn2 = id11.str[-2:]
    df["ID12"] = np.where(hh9.notna() & pn2.notna(), df["householdID10"] + pn2, np.nan).astype("object")
    return df

def standardize_keys(df, keys=("householdID","communityID","ID")):
    """Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    lower_map = {c.lower(): c for c in df.columns}
    rename = {}
    for k in keys:
        lk = k.lower()
        if lk in lower_map and lower_map[lk] != k:
            rename[lower_map[lk]] = k
    if rename:
        df = df.rename(columns=rename)

    if "householdID" in df.columns:
        df["householdID"] = _canon_fixed(df["householdID"], 9)
    if "communityID" in df.columns:
        df["communityID"] = _canon_fixed(df["communityID"], 7)
    if "ID" in df.columns:
        df["ID"] = _canon_fixed(df["ID"], 11)
    return df

def sanitize_for_stata(d):
    d = d.copy()
    for c in d.select_dtypes(include=["Int8","Int16","Int32","Int64",
                                      "UInt8","UInt16","UInt32","UInt64",
                                      "boolean"]).columns:
        d[c] = d[c].astype("float64")
    for c in d.select_dtypes(include=["datetime64[ns]","datetimetz"]).columns:
        d[c] = d[c].view("int64") / 1e9
    for c in d.select_dtypes(include=["object","string"]).columns:
        s = d[c].astype(object)
        m = pd.isna(s)
        s = s.astype(str); s[m] = None
        d[c] = s.map(lambda x: x if (x is None or len(x)<=2000) else x[:2000])
    return d

def write_dta(df, path, var_labels=None):
    Path(Path(path).parent).mkdir(parents=True, exist_ok=True)
    df2 = sanitize_for_stata(df)
    try:
        import pyreadstat
        vlabels = {k: (var_labels.get(k, "") if var_labels else "") for k in df2.columns}
        pyreadstat.write_dta(df2, path, version=118, variable_labels=vlabels if var_labels else None)
        print("[INFO] Notebook progress message.")
    except Exception as e:
        print("[INFO] Notebook progress message.")
        df2.to_stata(path, write_index=False, version=117)
        print("[INFO] Notebook progress message.")

def dedup_on_keys(df, keys=("householdID","communityID")):
    before = len(df)
    df2 = df.drop_duplicates(subset=list(keys), keep="first")
    if len(df2) < before:
        print("[INFO] Notebook progress message.")
    return df2

def merge_no_suffix(left, right, keys=("householdID","communityID"), suffix="_dup", how="outer"):
    """Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    overlap = [c for c in right.columns if c in left.columns and c not in keys]
    merged = left.merge(right, on=list(keys), how=how, suffixes=("", suffix))
    for c in overlap:
        c2 = c + suffix
        merged[c] = merged[c].combine_first(merged[c2])
        merged = merged.drop(columns=[c2])
    return merged

# =================================================
# Original notebook comment normalized for the public code archive.
# =================================================
def pick_pm_vars(df, sum_codes=None, res_codes=None):
    if sum_codes is not None and res_codes is not None:
        exists_queries = set(sum_codes.loc[sum_codes["exists"], "query"])
        matched_vars = (res_codes
                        .loc[(res_codes["match_type"] != "NOT_FOUND") &
                             (res_codes["query"].isin(exists_queries)), "variable"]
                        .dropna().tolist())
        seen = set()
        matched_vars = [x for x in matched_vars if not (x in seen or seen.add(x))]
        return matched_vars
    prefixes = ["da","db","dc"]
    return [c for c in df.columns if any(c.lower().startswith(p) for p in prefixes)]

D_raw = standardize_keys(read_dta_basic(f_d))
D_raw = add_id12_hhid10_2011(D_raw)  # Original notebook comment normalized for the public code archive.

try:
    matched = pick_pm_vars(D_raw,
                           sum_codes=globals().get("sum_codes"),
                           res_codes=globals().get("res_codes"))
except Exception:
    matched = pick_pm_vars(D_raw, None, None)

id_cols = [c for c in ["householdID","communityID","ID","householdID10","ID12"] if c in D_raw.columns]  # ★
keep_cols_pm = id_cols + [c for c in matched if c in D_raw.columns]
keep_cols_pm = keep_cols_pm or id_cols
PM = D_raw[keep_cols_pm].copy()
write_dta(PM, pm_out)

# =================================================
# Original notebook comment normalized for the public code archive.
# =================================================
def resolve_columns(df, var_labels, code_list, id_names=("householdID","communityID","ID","householdID10","ID12")):
    cols = list(df.columns); cols_lower = [c.lower() for c in cols]
    want_ids = []
    for nm in id_names:
        if nm in cols: want_ids.append(nm)
        else:
            nm_low = nm.lower()
            if nm_low in cols_lower: want_ids.append(cols[cols_lower.index(nm_low)])

    found = []
    for code in code_list:
        code_low = code.lower()
        cands = []
        if code in cols: cands.append(code)
        if code_low in cols_lower: cands.append(cols[cols_lower.index(code_low)])
        cands += [c for c in cols if c.lower().startswith(code_low)]
        if not cands:
            for c, lab in var_labels.items():
                if lab and re.search(code, lab, flags=re.IGNORECASE):
                    cands.append(c)
        seen = set()
        cands = [c for c in cols if c in cands and not (c in seen or seen.add(c))]
        found.extend(cands)

    keep, seen = [], set()
    for c in cols:
        if (c in want_ids or c in found) and c not in seen:
            keep.append(c); seen.add(c)
    return keep

CD_raw, CD_labels = read_dta_with_labels(f_cd)
CE_raw, CE_labels = read_dta_with_labels(f_ce)

# Original notebook comment normalized for the public code archive.
CD_raw = standardize_keys(CD_raw); CE_raw = standardize_keys(CE_raw)
CD_raw = add_id12_hhid10_2011(CD_raw)  # Original notebook comment normalized for the public code archive.
CE_raw = add_id12_hhid10_2011(CE_raw)  # ★

codes_cd003 = [f"CD003_{i}" for i in range(1, 15)]
codes_cd004 = [f"CD004_{i}" for i in range(1, 15)]
cd_keep = resolve_columns(CD_raw, CD_labels, [*codes_cd003, *codes_cd004])
ce_keep = resolve_columns(CE_raw, CE_labels, ["CE027", "CE031"])

# Original notebook comment normalized for the public code archive.
if "householdID10" in CD_raw.columns and "householdID10" not in cd_keep:
    cd_keep = ["householdID10"] + cd_keep
if "householdID10" in CE_raw.columns and "householdID10" not in ce_keep:
    ce_keep = ["householdID10"] + ce_keep

write_dta(CD_raw[cd_keep], s1_out, CD_labels)
write_dta(CE_raw[ce_keep], s2_out, CE_labels)

# =================================================
# Original notebook comment normalized for the public code archive.
# =================================================
pm = standardize_keys(read_dta_basic(pm_out))
s1 = standardize_keys(read_dta_basic(s1_out))
s2 = standardize_keys(read_dta_basic(s2_out))

keys_hh = ("householdID","communityID")

# Original notebook comment normalized for the public code archive.
if "ID12" in pm.columns and pm["ID12"].notna().any():
    pm = dedup_on_keys(pm, keys=("ID12",))  # Original notebook comment normalized for the public code archive.
else:
    pm = dedup_on_keys(pm, keys=("householdID","communityID","ID"))

s1 = dedup_on_keys(s1, keys=keys_hh)
s2 = dedup_on_keys(s2, keys=keys_hh)

# Original notebook comment normalized for the public code archive.
health = merge_no_suffix(pm, s1, keys=keys_hh, suffix="_s1", how="left")
health = merge_no_suffix(health, s2, keys=keys_hh, suffix="_s2", how="left")

print("[INFO] Notebook progress message.")

Path(base_out).mkdir(parents=True, exist_ok=True)
write_dta(health, health_dta)

try:
    with pd.ExcelWriter(health_xls, engine="xlwt") as writer:
        health.to_excel(writer, sheet_name="health", index=False)
    print("[INFO] Notebook progress message.")
except Exception as e:
    print("[INFO] Notebook progress message.")
    health.to_excel(health_xlsx, index=False)
    print("[INFO] Notebook progress message.")




# =============================================================================
# Source notebook
# =============================================================================
# record_type : wave_step
# year        : 2013
# step        : 1
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 6
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
import re
from pathlib import Path
import numpy as np
import pandas as pd

# =============================================================================
base_in = r"E:\project_flood_impact_assessment\老年人健康\CHARLS\charls原版数据\原始数据+问卷2011~2020\2013\CHARLS2013_Dataset"
f_d   = fr"{base_in}\Health_Status_and_Functioning.dta"
f_cd  = fr"{base_in}\Family_Information.dta"
f_ce  = fr"{base_in}\Family_Transfer.dta"

base_out = r"E:\impact_assessment_child_order\older\health\2013"
out_dta  = fr"{base_out}\health.dta"
out_xlsx = fr"{base_out}\health.xlsx"

# =============================================================================
def read_dta(path):
    df = pd.read_stata(path, convert_categoricals=False)
    print("[INFO] Notebook progress message.")
    return df

def standardize_keys(df, keys=("householdID","communityID")):
    # Original notebook comment normalized for the public code archive.
    lower_map = {c.lower(): c for c in df.columns}
    rename = {}
    for k in keys:
        lk = k.lower()
        if lk in lower_map and lower_map[lk] != k:
            rename[lower_map[lk]] = k
    if rename:
        df = df.rename(columns=rename)
    # Original notebook comment normalized for the public code archive.
    for k in keys:
        if k in df.columns:
            def norm(x):
                if pd.isna(x): return None
                try:
                    fx = float(x)
                    if fx.is_integer(): return str(int(fx))
                except Exception:
                    pass
                return str(x).strip()
            df[k] = df[k].map(norm)
    return df

def select_by_codes(df, code_list):
    """Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    cols = list(df.columns)
    want = []
    for code in code_list:
        pat = re.compile(r'^' + re.escape(code.lower()) + r'(?=$|[_a-z0-9])')
        picks = [c for c in cols if pat.search(c.lower())]
        want.extend(picks)
    # Original notebook comment normalized for the public code archive.
    seen = set(); want = [c for c in cols if c in want and not (c in seen or seen.add(c))]
    return want

def select_cd(df):
    cols = list(df.columns); cols_l = [c.lower() for c in cols]
    want = []
    for i in range(1, 12):
        for t in (f"cd003_{i}", f"cd003_{i}_"):
            if t in cols_l: want.append(cols[cols_l.index(t)])
    for i in range(1, 12):
        for t in (f"cd004_{i}", f"cd004_{i}_"):
            if t in cols_l: want.append(cols[cols_l.index(t)])
    seen=set(); want=[c for c in cols if c in want and not (c in seen or seen.add(c))]
    return want

def select_ce(df):
    cols = list(df.columns)
    keep, seen = [], set()
    pat_ce009 = re.compile(r'^ce009_(?:1|3)(?:_(?:\d+))*_?$', re.IGNORECASE)
    for c in cols:
        if pat_ce009.match(c.lower()) and c not in seen:
            keep.append(c); seen.add(c)
    for name in ["ce013_1", "ce013_3", "ce013_1_", "ce013_3_"]:
        for c in cols:
            if c.lower() == name and c not in seen:
                keep.append(c); seen.add(c)
    return keep

def dedup_on_keys(df, keys):
    before = len(df)
    df2 = df.drop_duplicates(subset=list(keys), keep="first")
    if len(df2) < before:
        print("[INFO] Notebook progress message.")
    return df2

def merge_no_suffix(left, right, keys, suffix="_dup", how="left"):
    """Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    overlap = [c for c in right.columns if c in left.columns and c not in keys]
    merged = left.merge(right, on=list(keys), how=how, suffixes=("", suffix))
    for c in overlap:
        c2 = c + suffix
        merged[c] = merged[c].combine_first(merged[c2])
        merged = merged.drop(columns=[c2])
    return merged

def sanitize_for_stata(d):
    """Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    d = d.copy()
    for c in d.select_dtypes(include=["Int8","Int16","Int32","Int64",
                                      "UInt8","UInt16","UInt32","UInt64",
                                      "boolean"]).columns:
        d[c] = d[c].astype("float64")
    for c in d.select_dtypes(include=["datetime64[ns]","datetimetz"]).columns:
        d[c] = d[c].view("int64")/1e9
    for c in d.select_dtypes(include=["object","string"]).columns:
        s = d[c].astype(object); m = pd.isna(s); s = s.astype(str); s[m] = None
        d[c] = s.map(lambda x: x if (x is None or len(x)<=2000) else x[:2000])
    return d

# =============================================================================
def harmonize_da007_2013(df):
    """Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    import re
    # Original notebook comment normalized for the public code archive.
    items = set()
    for c in df.columns:
        for pat in (rf'(?i)^da007_(\d+)_?$',        # DA007_1 / DA007_1_
                    rf'(?i)^zda007_(\d+)_?$',       # ZDA007_1 / ZDA007_1_
                    rf'(?i)^da007_w2_1_(\d+)_?$',   # W2_1_1 / _1_
                    rf'(?i)^da007_w2_2_(\d+)_?$'):  # W2_2_1 / _1_
            m = re.match(pat, c)
            if m: items.add(int(m.group(1)))
    items = sorted(items)

    def col(regex):
        hits = [c for c in df.columns if re.match(regex, c, flags=re.IGNORECASE)]
        return pd.to_numeric(df[hits[0]], errors="coerce") if hits else None

    # Original notebook comment normalized for the public code archive.
    def rec01(s):
        out = pd.Series(np.nan, index=df.index, dtype="float64")
        if s is not None:
            out = out.copy()
            out[s == 1] = 1.0
            out[s == 2] = 0.0
        return out

    # 1/0 → 1/2
    def to12(s01):
        out = pd.Series(np.nan, index=s01.index, dtype="float64")
        out[s01 == 1] = 1.0
        out[s01 == 0] = 2.0
        return out

    for i in items:
        da  = rec01(col(rf'(?i)^da007_{i}_?$'))
        zda = rec01(col(rf'(?i)^zda007_{i}_?$'))
        ok  = rec01(col(rf'(?i)^da007_w2_1_{i}_?$'))  # Original notebook comment normalized for the public code archive.
        new = rec01(col(rf'(?i)^da007_w2_2_{i}_?$'))  # Original notebook comment normalized for the public code archive.

        # Original notebook comment normalized for the public code archive.
        carried_prev = zda.copy()
        if ok is not None:
            carried_prev = carried_prev.copy()
            carried_prev[ok == 0] = 0.0

        # Original notebook comment normalized for the public code archive.
        cur01 = pd.Series(np.nan, index=df.index, dtype="float64")
        has_da = da.notna()
        cur01[has_da] = da[has_da]

        # Original notebook comment normalized for the public code archive.
        remain = ~has_da
        yes_mask = ((carried_prev == 1) | (new == 1))
        no_mask  = ((carried_prev == 0) & (new == 0))
        # Original notebook comment normalized for the public code archive.
        yes_mask = yes_mask.fillna(False)
        no_mask  = no_mask.fillna(False)

        cur01[remain & yes_mask] = 1.0
        cur01[remain & (~yes_mask) & no_mask] = 0.0

        df[f'da007_w2filled_{i}'] = to12(cur01)
    return df

# =============================================================================
# Original notebook comment normalized for the public code archive.
d_df  = standardize_keys(read_dta(f_d),  keys=("householdID","communityID","ID"))
cd_df = standardize_keys(read_dta(f_cd), keys=("householdID","communityID"))
ce_df = standardize_keys(read_dta(f_ce), keys=("householdID","communityID"))

keys_hh = ("householdID","communityID")
keys_person = ("householdID","communityID","ID")

for nm, df_, must in [("D", d_df, keys_person), ("CD", cd_df, keys_hh), ("CE", ce_df, keys_hh)]:
    missing = [k for k in must if k not in df_.columns]
    if missing:
        raise KeyError(f"{nm} 表缺少键列：{missing}")

# Original notebook comment normalized for the public code archive.
D_CODES = (
    ["DA001","DA002","DA007","DA056","DA057","DA079","DA080",
     "ZDA007", "DA007_W2_1", "DA007_W2_2"] +
    [f"DB{str(i).zfill(3)}" for i in range(1,17)] +
    ["DC009","DC011","DC012","DC013","DC014","DC015","DC016","DC018","DC028"]
)

d_cols  = [*keys_person, *select_by_codes(d_df, [c.lower() for c in D_CODES])]
cd_cols = [*keys_hh, *select_cd(cd_df)]
ce_cols = [*keys_hh, *select_ce(ce_df)]
print("[INFO] Notebook progress message.")

# Original notebook comment normalized for the public code archive.
d_df  = d_df[d_cols].drop_duplicates(subset=list(keys_person))
cd_df = dedup_on_keys(cd_df[cd_cols], keys_hh)
ce_df = dedup_on_keys(ce_df[ce_cols], keys_hh)

# =============================================================================
d_df = harmonize_da007_2013(d_df)

# =============================================================================
health = merge_no_suffix(d_df,  cd_df, keys_hh, suffix="_cd", how="left")
health = merge_no_suffix(health, ce_df, keys_hh, suffix="_ce", how="left")
print("[INFO] Notebook progress message.")

# =============================================================================
Path(base_out).mkdir(parents=True, exist_ok=True)

# .dta
health_clean = sanitize_for_stata(health)
try:
    import pyreadstat
    pyreadstat.write_dta(health_clean, out_dta, version=118)
    print("[INFO] Notebook progress message.")
except Exception as e:
    print("[INFO] Notebook progress message.", e)
    health_clean.to_stata(out_dta, write_index=False, version=117)
    print("[INFO] Notebook progress message.")

# .xlsx
try:
    health.to_excel(out_xlsx, index=False)
    print("[INFO] Notebook progress message.")
except Exception as e:
    print("[INFO] Notebook progress message.")


# ------------------------------------------------------------------------------
# Notebook cell 9
# ------------------------------------------------------------------------------
import re, pandas as pd
p = r"E:\impact_assessment_child_order\older\health\2013\health.dta"
df = pd.read_stata(p, convert_categoricals=False)
[w for w in df.columns if re.match(r'(?i)^da007_w2filled_\d+$', w)], df.filter(regex='(?i)^da007_w2filled_').shape




# =============================================================================
# Source notebook
# =============================================================================
# record_type : wave_step
# year        : 2015
# step        : 1
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 6
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import re
from pathlib import Path
import numpy as np
import pandas as pd

# =============================================================================
base_in = r"E:\project_flood_impact_assessment\老年人健康\CHARLS\charls原版数据\原始数据+问卷2011~2020\2015\CHARLS2015r"
f_d  = fr"{base_in}\Health_Status_and_Functioning.dta"
f_cd = fr"{base_in}\Family_Information.dta"
f_ce = fr"{base_in}\Family_Transfer.dta"

base_out = r"E:\impact_assessment_child_order\older\health\2015"
out_dta  = fr"{base_out}\health.dta"
out_xlsx = fr"{base_out}\health.xlsx"

# =============================================================================

def read_dta_basic(path):
    df = pd.read_stata(path, convert_categoricals=False)
    print("[INFO] Notebook progress message.")
    return df


def read_dta_with_labels(path):
    """Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    var_labels = {}
    try:
        import pyreadstat
        df, meta = pyreadstat.read_dta(path, apply_value_formats=False, formats_as_category=False)
        var_labels = meta.column_names_to_labels or {}
    except Exception as e:
        print("[INFO] Notebook progress message.")
        df = pd.read_stata(path, convert_categoricals=False)
        var_labels = {c: "" for c in df.columns}
    print("[INFO] Notebook progress message.")
    return df, var_labels


def _clean_to_str(s: pd.Series) -> pd.Series:
    s = pd.Series(s, dtype="object")
    m = s.isna()
    sc = s[~m].astype(str).str.strip()
    sc = sc.str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = sc
    s.loc[m] = np.nan
    return s


def _canon_fixed(s: pd.Series, width: int) -> pd.Series:
    s = _clean_to_str(s)
    m = s.notna()
    s.loc[m] = s.loc[m].astype(str).str.zfill(width)
    return s


def standardize_keys(df, need_id: bool = False):
    """Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()
    lower_map = {c.lower(): c for c in df.columns}

    def pick_and_rename(target: str, alts):
        for nm in [target.lower(), *[a.lower() for a in alts]]:
            if nm in lower_map:
                real = lower_map[nm]
                if real != target:
                    df.rename(columns={real: target}, inplace=True)
                return True
        return False

    ok_hh = pick_and_rename("householdID", alts=["householdid"])  # Original notebook comment normalized for the public code archive.
    ok_cc = pick_and_rename("communityID", alts=["communityid"])  # Original notebook comment normalized for the public code archive.
    ok_id = True
    if need_id:
        ok_id = pick_and_rename("ID", alts=["pid", "individualid", "personid", "charlsid", "indid", "person_id"])  # Original notebook comment normalized for the public code archive.

    if not (ok_hh and ok_cc and (ok_id if need_id else True)):
        missing = [nm for nm, ok in [("householdID", ok_hh), ("communityID", ok_cc), ("ID", ok_id if need_id else True)] if not ok]
        raise KeyError(f"表缺少必需键列：{missing}")

    if "householdID" in df.columns:
        df["householdID"] = _canon_fixed(df["householdID"], 9)
    if "communityID" in df.columns:
        df["communityID"] = _canon_fixed(df["communityID"], 7)
    if need_id and ("ID" in df.columns):
        df["ID"] = _canon_fixed(df["ID"], 11)
    return df


def sanitize_for_stata(d):
    d = d.copy()

    # Original notebook comment normalized for the public code archive.
    for c in d.select_dtypes(include=["Int8","Int16","Int32","Int64",
                                      "UInt8","UInt16","UInt32","UInt64",
                                      "boolean"]).columns:
        d[c] = d[c].astype("float64")

    # Original notebook comment normalized for the public code archive.
    for c in d.select_dtypes(include=["datetime64[ns]","datetimetz"]).columns:
        d[c] = d[c].view("int64") / 1e9

    # Original notebook comment normalized for the public code archive.
    obj_cols = list(d.select_dtypes(include=["object","string"]).columns)
    drop_all_null = []  # Original notebook comment normalized for the public code archive.
    for c in obj_cols:
        s = pd.Series(d[c], dtype="object")
        if s.isna().all():
            drop_all_null.append(c)
            continue
        m = s.isna()
        s = s.astype(str)
        s[m] = None
        # Original notebook comment normalized for the public code archive.
        s = s.map(lambda x: x if (x is None or len(x) <= 2000) else x[:2000])
        d[c] = s

    if drop_all_null:
        print("[INFO] Notebook progress message.")
        d = d.drop(columns=drop_all_null)

    return d


def write_dta(df, path, var_labels=None):
    from pathlib import Path
    Path(Path(path).parent).mkdir(parents=True, exist_ok=True)

    df2 = sanitize_for_stata(df)

    # Original notebook comment normalized for the public code archive.
    vlabels = None
    if var_labels:
        vlabels = {k: var_labels.get(k, "") for k in df2.columns}

    # Original notebook comment normalized for the public code archive.
    try:
        import pyreadstat, inspect
        kwargs = {"version": 118}
        if vlabels:
            # Original notebook comment normalized for the public code archive.
            if "variable_labels" in inspect.signature(pyreadstat.write_dta).parameters:
                kwargs["variable_labels"] = vlabels
        pyreadstat.write_dta(df2, path, **kwargs)
        print("[INFO] Notebook progress message.")
        return
    except Exception as e:
        print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    df2.to_stata(path, write_index=False, version=118, variable_labels=vlabels)
    print("[INFO] Notebook progress message.")



def dedup_on_keys(df, keys):
    before = len(df)
    df2 = df.drop_duplicates(subset=list(keys), keep="first")
    if len(df2) < before:
        print("[INFO] Notebook progress message.")
    return df2


def merge_no_suffix(left, right, keys, suffix="_dup", how="left"):
    """Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    overlap = [c for c in right.columns if c in left.columns and c not in keys]
    merged = left.merge(right, on=list(keys), how=how, suffixes=("", suffix))
    for c in overlap:
        c2 = c + suffix
        merged[c] = merged[c].combine_first(merged[c2])
        merged = merged.drop(columns=[c2])
    return merged


def select_by_codes(df, code_list):
    """Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    cols = list(df.columns)
    want = []
    for code in code_list:
        pat = re.compile(r'^' + re.escape(code.lower()) + r'(?=$|[_a-z0-9])')
        picks = [c for c in cols if pat.search(c.lower())]
        want.extend(picks)
    seen = set()
    want = [c for c in cols if c in want and not (c in seen or seen.add(c))]
    return want


def select_cd_2015(df):
    cols = list(df.columns); cols_l = [c.lower() for c in cols]
    want = []
    for i in range(1, 17):
        for name in (f"cd003_{i}", f"cd003_{i}_", f"cd004_{i}", f"cd004_{i}_"):
            if name in cols_l:
                want.append(cols[cols_l.index(name)])
    seen = set()
    want = [c for c in cols if c in want and not (c in seen or seen.add(c))]
    return want


def select_ce_full(df):
    """Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    cols = list(df.columns)
    keep = []
    # Original notebook comment normalized for the public code archive.
    pat_main = re.compile(r'^ce(002|009|016|022|029|036)(?:_(?:[1-4]))(?:_(?:\d+))*_?$', re.IGNORECASE)
    # Original notebook comment normalized for the public code archive.
    pat_sib  = re.compile(r'^ce07[2-5].*', re.IGNORECASE)
    seen = set()
    for c in cols:
        cl = c.lower()
        if pat_main.match(cl) or pat_sib.match(cl):
            if c not in seen:
                keep.append(c); seen.add(c)
    # Original notebook comment normalized for the public code archive.
    for name in ["ce013_1", "ce013_3", "ce013_1_", "ce013_3_"]:
        for c in cols:
            if c.lower() == name and c not in seen:
                keep.append(c); seen.add(c)
    return keep


# =============================================================================

def harmonize_da007_currentwave(df):
    """Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    items = set()
    for c in df.columns:
        for pat in (r'(?i)^da007_(\d+)_?$', r'(?i)^zda007_(\d+)_?$', r'(?i)^da007_w2_1_(\d+)_?$', r'(?i)^da007_w2_2_(\d+)_?$'):
            m = re.match(pat, c)
            if m:
                try:
                    items.add(int(m.group(1)))
                except Exception:
                    pass
    items = sorted(items)
    if not items:
        print("[INFO] Notebook progress message.")
        return df

    def col(regex):
        hits = [c for c in df.columns if re.match(regex, c, flags=re.IGNORECASE)]
        return pd.to_numeric(df[hits[0]], errors="coerce") if hits else None

    def rec01(s):  # 1/2 -> 1/0
        out = pd.Series(np.nan, index=df.index, dtype="float64")
        if s is not None:
            out[s == 1] = 1.0
            out[s == 2] = 0.0
        return out

    def to12(s01):  # 1/0 -> 1/2
        out = pd.Series(np.nan, index=s01.index, dtype="float64")
        out[s01 == 1] = 1.0
        out[s01 == 0] = 2.0
        return out

    for i in items:
        da  = rec01(col(rf'(?i)^da007_{i}_?$'))
        zda = rec01(col(rf'(?i)^zda007_{i}_?$'))
        ok  = rec01(col(rf'(?i)^da007_w2_1_{i}_?$'))  # Original notebook comment normalized for the public code archive.
        new = rec01(col(rf'(?i)^da007_w2_2_{i}_?$'))  # Original notebook comment normalized for the public code archive.

        # Original notebook comment normalized for the public code archive.
        carried_prev = zda.copy() if zda is not None else pd.Series(np.nan, index=df.index, dtype="float64")
        if ok is not None:
            carried_prev[ok == 0] = 0.0

        cur01 = pd.Series(np.nan, index=df.index, dtype="float64")
        if da is not None:
            has_da = da.notna()
            cur01[has_da] = da[has_da]
            remain = ~has_da
        else:
            remain = pd.Series(True, index=df.index)

        yes_mask = pd.Series(False, index=df.index)
        no_mask  = pd.Series(False, index=df.index)
        if carried_prev is not None:
            yes_mask |= (carried_prev == 1)
            no_mask  |= (carried_prev == 0)
        if new is not None:
            yes_mask |= (new == 1)
            no_mask  &= ~(new == 1)  # Original notebook comment normalized for the public code archive.

        cur01[remain & yes_mask.fillna(False)] = 1.0
        cur01[remain & (~yes_mask.fillna(False)) & no_mask.fillna(False)] = 0.0

        df[f'da007_filled_{i}'] = to12(cur01)

    return df


# =============================================================================
if __name__ == "__main__":
    # Original notebook comment normalized for the public code archive.
    D_raw, D_labels   = read_dta_with_labels(f_d)
    CD_raw, CD_labels = read_dta_with_labels(f_cd)
    CE_raw, CE_labels = read_dta_with_labels(f_ce)

    # Original notebook comment normalized for the public code archive.
    D  = standardize_keys(D_raw,  need_id=True)
    CD = standardize_keys(CD_raw, need_id=False)
    CE = standardize_keys(CE_raw, need_id=False)

    keys_hh     = ("householdID","communityID")
    keys_person = ("householdID","communityID","ID")

    # Original notebook comment normalized for the public code archive.
    D_CODES = (
        ["DA001","DA002","DA007","DA056","DA057","DA079","DA080"] +
        [f"DB{str(i).zfill(3)}" for i in range(1, 17)] +
        ["DC011","DC012","DC013","DC014","DC015","DC016","DC018","DC028",
         "DA007_W2_1","DA007_W2_2","ZDA007"]  # Original notebook comment normalized for the public code archive.
    )

    # Original notebook comment normalized for the public code archive.
    D  = dedup_on_keys(D[[*keys_person, *select_by_codes(D,  [c.lower() for c in D_CODES])]], keys_person)
    CD = dedup_on_keys(CD[[*keys_hh,     *select_cd_2015(CD)]],                           keys_hh)
    CE = dedup_on_keys(CE[[*keys_hh,     *select_ce_full(CE)]],                           keys_hh)

    # Original notebook comment normalized for the public code archive.
    D = harmonize_da007_currentwave(D)

    # Original notebook comment normalized for the public code archive.
    health = merge_no_suffix(D,  CD, keys=keys_hh, suffix="_cd", how="left")
    health = merge_no_suffix(health, CE, keys=keys_hh, suffix="_ce", how="left")

    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    Path(base_out).mkdir(parents=True, exist_ok=True)
    write_dta(health, out_dta, var_labels={**D_labels, **CD_labels, **CE_labels})
    try:
        health.to_excel(out_xlsx, index=False)
        print("[INFO] Notebook progress message.")
    except Exception as e:
        print("[INFO] Notebook progress message.")




# =============================================================================
# Source notebook
# =============================================================================
# record_type : wave_step
# year        : 2018
# step        : 1
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 6
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import re
from pathlib import Path
import numpy as np
import pandas as pd


# =============================================================================
base_in = r"E:\project_flood_impact_assessment\老年人健康\CHARLS\charls原版数据\原始数据+问卷2011~2020\2018\CHARLS2018r"
f_d  = fr"{base_in}\Health_Status_and_Functioning.dta"
f_cd = fr"{base_in}\Family_Information.dta"   # Original notebook comment normalized for the public code archive.
f_ce = fr"{base_in}\Family_Transfer.dta"
f_cg = fr"{base_in}\Cognition.dta"            # Original notebook comment normalized for the public code archive.

base_out = r"E:\impact_assessment_child_order\older\health\2018"
out_dta  = fr"{base_out}\health.dta"
out_xlsx = fr"{base_out}\health.xlsx"


# =============================================================================
def read_dta_with_labels(path):
    """Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    var_labels = {}
    try:
        import pyreadstat
        df, meta = pyreadstat.read_dta(path, apply_value_formats=False, formats_as_category=False)
        var_labels = meta.column_names_to_labels or {}
    except Exception as e:
        print("[INFO] Notebook progress message.")
        df = pd.read_stata(path, convert_categoricals=False)
        var_labels = {c: "" for c in df.columns}
    print("[INFO] Notebook progress message.")
    return df, var_labels


def _clean_to_str(s: pd.Series) -> pd.Series:
    s = pd.Series(s, dtype="object")
    m = s.isna()
    sc = s[~m].astype(str).str.strip()
    sc = sc.str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = sc
    s.loc[m] = np.nan
    return s


def _canon_fixed(s: pd.Series, width: int) -> pd.Series:
    s = _clean_to_str(s)
    m = s.notna()
    s.loc[m] = s.loc[m].astype(str).str.zfill(width)
    return s


def standardize_keys(df, need_id: bool):
    """Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()
    lower_map = {c.lower(): c for c in df.columns}

    def pick(target: str, alts):
        for nm in [target.lower(), *[a.lower() for a in alts]]:
            if nm in lower_map:
                real = lower_map[nm]
                if real != target:
                    df.rename(columns={real: target}, inplace=True)
                return True
        return False

    ok_hh = pick("householdID", alts=["householdid"])
    ok_cc = pick("communityID", alts=["communityid"])
    ok_id = True
    if need_id:
        ok_id = pick("ID", alts=["pid","individualid","personid","charlsid","indid","person_id"])

    missing = [nm for nm, ok in [("householdID", ok_hh), ("communityID", ok_cc), ("ID", ok_id if need_id else True)] if not ok]
    if missing:
        raise KeyError(f"表缺少必需键列：{missing}")

    if "householdID" in df.columns:
        df["householdID"] = _canon_fixed(df["householdID"], 9)
    if "communityID" in df.columns:
        df["communityID"] = _canon_fixed(df["communityID"], 7)
    if need_id and ("ID" in df.columns):
        df["ID"] = _canon_fixed(df["ID"], 11)
    return df


def sanitize_for_stata(d):
    """Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    d = d.copy()
    # Original notebook comment normalized for the public code archive.
    for c in d.select_dtypes(include=["Int8","Int16","Int32","Int64",
                                      "UInt8","UInt16","UInt32","UInt64","boolean"]).columns:
        d[c] = d[c].astype("float64")
    # Original notebook comment normalized for the public code archive.
    for c in d.select_dtypes(include=["datetime64[ns]","datetimetz"]).columns:
        d[c] = d[c].view("int64")/1e9
    # Original notebook comment normalized for the public code archive.
    obj_cols = list(d.select_dtypes(include=["object","string"]).columns)
    drop_all_null = []
    for c in obj_cols:
        s = pd.Series(d[c], dtype="object")
        if s.isna().all():
            drop_all_null.append(c)
            continue
        m = s.isna(); s = s.astype(str); s[m] = None
        d[c] = s.map(lambda x: x if (x is None or len(x) <= 2000) else x[:2000])
    if drop_all_null:
        print("[INFO] Notebook progress message.")
        d = d.drop(columns=drop_all_null)
    return d


def write_dta(df, path, var_labels=None):
    Path(Path(path).parent).mkdir(parents=True, exist_ok=True)
    df2 = sanitize_for_stata(df)
    vlabels = {k: var_labels.get(k, "") for k in df2.columns} if var_labels else None
    try:
        import pyreadstat, inspect
        kwargs = {"version": 118}
        if vlabels and "variable_labels" in inspect.signature(pyreadstat.write_dta).parameters:
            kwargs["variable_labels"] = vlabels
        pyreadstat.write_dta(df2, path, **kwargs)
        print("[INFO] Notebook progress message.")
    except Exception as e:
        print("[INFO] Notebook progress message.")
        df2.to_stata(path, write_index=False, version=118, variable_labels=vlabels)
        print("[INFO] Notebook progress message.")


def dedup_on_keys(df, keys):
    before = len(df)
    df2 = df.drop_duplicates(subset=list(keys), keep="first")
    if len(df2) < before:
        print("[INFO] Notebook progress message.")
    return df2


def merge_no_suffix(left, right, keys, suffix="_dup", how="left"):
    """Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    overlap = [c for c in right.columns if c in left.columns and c not in keys]
    merged = left.merge(right, on=list(keys), how=how, suffixes=("", suffix))
    for c in overlap:
        c2 = c + suffix
        merged[c] = merged[c].combine_first(merged[c2])
        merged = merged.drop(columns=[c2])
    return merged


def select_by_codes(df, code_list):
    """Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    cols = list(df.columns)
    want = []
    for code in code_list:
        pat = re.compile(r'^' + re.escape(code.lower()) + r'(?=$|[_a-z0-9])')
        picks = [c for c in cols if pat.search(c.lower())]
        want.extend(picks)
    seen = set()
    want = [c for c in cols if c in want and not (c in seen or seen.add(c))]
    return want


def select_cd_2018(df):
    """Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    cols = list(df.columns); L = [c.lower() for c in cols]
    want = []
    for base, hi in [("cd003", 20), ("cd004", 20)]:  # Original notebook comment normalized for the public code archive.
        for i in range(1, hi+1):
            for n in (f"{base}_{i}", f"{base}_{i}_"):
                if n in L:
                    want.append(cols[L.index(n)])
    seen=set(); want=[c for c in cols if c in want and not (c in seen or seen.add(c))]
    return want


def select_ce_full_2018(df):
    """Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    cols = list(df.columns); keep=[]; seen=set()
    # Original notebook comment normalized for the public code archive.
    pat_main = re.compile(r'^ce(002|009|016|022|029|036)_(?:[1-4])(?:_(?:\d+))*_?$', re.IGNORECASE)
    # Original notebook comment normalized for the public code archive.
    pat_sib  = re.compile(r'^ce07[2-5].*', re.IGNORECASE)
    for c in cols:
        cl=c.lower()
        if (pat_main.match(cl) or pat_sib.match(cl)) and c not in seen:
            keep.append(c); seen.add(c)
    # Original notebook comment normalized for the public code archive.
    for name in ["ce013_1","ce013_3","ce013_1_","ce013_3_"]:
        for c in cols:
            if c.lower()==name and c not in seen:
                keep.append(c); seen.add(c)
    return keep


# =============================================================================
def harmonize_da007_w4(df):
    """Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    items = set()
    for c in df.columns:
        for pat in (
            r'(?i)^da007_(\d+)_?$',          # Original notebook comment normalized for the public code archive.
            r'(?i)^zda007_(\d+)_?$',         # Original notebook comment normalized for the public code archive.
            r'(?i)^da007_w[234]_1_(\d+)_?$', # Original notebook comment normalized for the public code archive.
            r'(?i)^da007_w[234]_2_(\d+)_?$'  # Original notebook comment normalized for the public code archive.
        ):
            m = re.match(pat, c)
            if m:
                try:
                    items.add(int(m.group(1)))
                except Exception:
                    pass
    items = sorted(items)
    if not items:
        print("[INFO] Notebook progress message.")
        return df

    def col(regex):
        hits = [c for c in df.columns if re.match(regex, c, flags=re.IGNORECASE)]
        return pd.to_numeric(df[hits[0]], errors="coerce") if hits else None

    def rec01(s):  # 1/2 -> 1/0/NA
        out = pd.Series(np.nan, index=df.index, dtype="float64")
        if s is not None:
            out[s == 1] = 1.0
            out[s == 2] = 0.0
        return out

    def to12(s01):  # 1/0 -> 1/2/NA
        out = pd.Series(np.nan, index=s01.index, dtype="float64")
        out[s01 == 1] = 1.0
        out[s01 == 0] = 2.0
        return out

    for i in items:
        da  = rec01(col(rf'(?i)^da007_{i}_?$'))
        zda = rec01(col(rf'(?i)^zda007_{i}_?$'))
        ok  = rec01(col(rf'(?i)^da007_w[234]_1_{i}_?$'))  # Original notebook comment normalized for the public code archive.
        new = rec01(col(rf'(?i)^da007_w[234]_2_{i}_?$'))  # Original notebook comment normalized for the public code archive.

        # Original notebook comment normalized for the public code archive.
        carried_prev = zda.copy() if zda is not None else pd.Series(np.nan, index=df.index, dtype="float64")
        if ok is not None:
            carried_prev[ok == 0] = 0.0

        cur01 = pd.Series(np.nan, index=df.index, dtype="float64")
        if da is not None:
            has_da = da.notna()
            cur01[has_da] = da[has_da]
            remain = ~has_da
        else:
            remain = pd.Series(True, index=df.index)

        yes_mask = pd.Series(False, index=df.index)
        no_mask  = pd.Series(False,  index=df.index)
        if carried_prev is not None:
            yes_mask |= (carried_prev == 1)
            no_mask  |= (carried_prev == 0)
        if new is not None:
            yes_mask |= (new == 1)
            # Original notebook comment normalized for the public code archive.

        cur01[remain & yes_mask.fillna(False)] = 1.0
        cur01[remain & (~yes_mask.fillna(False)) & no_mask.fillna(False)] = 0.0

        df[f'da007_filled_{i}'] = to12(cur01)
    return df


# =============================================================================
if __name__ == "__main__":
    # Original notebook comment normalized for the public code archive.
    D_raw,  D_labels  = read_dta_with_labels(f_d)
    CD_raw, CD_labels = read_dta_with_labels(f_cd)
    CE_raw, CE_labels = read_dta_with_labels(f_ce)
    CG_raw, CG_labels = read_dta_with_labels(f_cg)

    # Original notebook comment normalized for the public code archive.
    D  = standardize_keys(D_raw,  need_id=True)
    CD = standardize_keys(CD_raw, need_id=False)
    CE = standardize_keys(CE_raw, need_id=False)
    CG = standardize_keys(CG_raw, need_id=False)

    keys_hh     = ("householdID","communityID")
    keys_person = ("householdID","communityID","ID")

    # Original notebook comment normalized for the public code archive.
    # Original notebook comment normalized for the public code archive.
    D_CODES = (
        ["DA001","DA002","DA007","DA056","DA057","DA079","DA080"] +
        [f"DB{str(i).zfill(3)}" for i in range(1,17)] +
        ["ZDA007", "DA007_W2_1","DA007_W2_2","DA007_W3_1","DA007_W3_2","DA007_W4_1","DA007_W4_2"]
    )
    # Original notebook comment normalized for the public code archive.
    DC_CODES = ["DC011","DC012","DC013","DC014","DC015","DC016","DC018","DC028"]

    D  = D[[*keys_person, *select_by_codes(D,  [c.lower() for c in D_CODES])]]
    CD = CD[[*keys_hh,     *select_cd_2018(CD)]]
    CE = CE[[*keys_hh,     *select_ce_full_2018(CE)]]
    CG = CG[[*keys_hh,     *select_by_codes(CG, [c.lower() for c in DC_CODES])]]

    # Original notebook comment normalized for the public code archive.
    D  = dedup_on_keys(D,  keys_person)
    CD = dedup_on_keys(CD, keys_hh)
    CE = dedup_on_keys(CE, keys_hh)
    CG = dedup_on_keys(CG, keys_hh)

    # Original notebook comment normalized for the public code archive.
    D = harmonize_da007_w4(D)

    # Original notebook comment normalized for the public code archive.
    health = merge_no_suffix(D,  CD, keys=keys_hh, suffix="_cd", how="left")
    health = merge_no_suffix(health, CE, keys=keys_hh, suffix="_ce", how="left")
    health = merge_no_suffix(health, CG, keys=keys_hh, suffix="_cg", how="left")

    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    Path(base_out).mkdir(parents=True, exist_ok=True)
    labels_all = {**D_labels, **CD_labels, **CE_labels, **CG_labels}
    write_dta(health, out_dta, var_labels=labels_all)
    try:
        health.to_excel(out_xlsx, index=False)
        print("[INFO] Notebook progress message.")
    except Exception as e:
        print("[INFO] Notebook progress message.")




# =============================================================================
# Source notebook
# =============================================================================
# record_type : wave_step
# year        : 2020
# step        : 1
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 7
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import re
from pathlib import Path
import numpy as np
import pandas as pd

# =============================================================================
base_in = r"E:\project_flood_impact_assessment\老年人健康\CHARLS\charls原版数据\原始数据+问卷2011~2020\2020\CHARLS2020r"
f_d  = fr"{base_in}\Health_Status_and_Functioning.dta"
f_ci = fr"{base_in}\Family_Information.dta"   # Original notebook comment normalized for the public code archive.

base_out = r"E:\impact_assessment_child_order\older\health\2020"
out_dta  = fr"{base_out}\health.dta"
out_xlsx = fr"{base_out}\health.xlsx"

# =============================================================================
def read_dta_with_labels(path):
    """Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    var_labels = {}
    try:
        import pyreadstat
        df, meta = pyreadstat.read_dta(path, apply_value_formats=False, formats_as_category=False)
        var_labels = meta.column_names_to_labels or {}
    except Exception as e:
        print("[INFO] Notebook progress message.")
        df = pd.read_stata(path, convert_categoricals=False)
        var_labels = {c: "" for c in df.columns}
    print("[INFO] Notebook progress message.")
    return df, var_labels

def _clean_to_str(s: pd.Series) -> pd.Series:
    s = pd.Series(s, dtype="object")
    m = s.isna()
    sc = s[~m].astype(str).str.strip()
    sc = sc.str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = sc
    s.loc[m] = np.nan
    return s

def _canon_fixed(s: pd.Series, width: int) -> pd.Series:
    s = _clean_to_str(s)
    m = s.notna()
    s.loc[m] = s.loc[m].astype(str).str.zfill(width)
    return s

def standardize_keys(df, need_id: bool):
    """Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()
    lower_map = {c.lower(): c for c in df.columns}

    def pick(target: str, alts):
        for nm in [target.lower(), *[a.lower() for a in alts]]:
            if nm in lower_map:
                real = lower_map[nm]
                if real != target:
                    df.rename(columns={real: target}, inplace=True)
                return True
        return False

    ok_hh = pick("householdID", alts=["householdid"])
    ok_cc = pick("communityID", alts=["communityid"])
    ok_id = True
    if need_id:
        ok_id = pick("ID", alts=["pid","individualid","personid","charlsid","indid","person_id"])

    missing = [nm for nm, ok in [("householdID", ok_hh), ("communityID", ok_cc), ("ID", ok_id if need_id else True)] if not ok]
    if missing:
        raise KeyError(f"表缺少必需键列：{missing}")

    if "householdID" in df.columns:
        df["householdID"] = _canon_fixed(df["householdID"], 9)
    if "communityID" in df.columns:
        df["communityID"] = _canon_fixed(df["communityID"], 7)
    if need_id and ("ID" in df.columns):
        df["ID"] = _canon_fixed(df["ID"], 11)
    return df

def sanitize_for_stata(d):
    """Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    d = d.copy()
    # Original notebook comment normalized for the public code archive.
    for c in d.select_dtypes(include=["Int8","Int16","Int32","Int64","UInt8","UInt16","UInt32","UInt64","boolean"]).columns:
        d[c] = d[c].astype("float64")
    # Original notebook comment normalized for the public code archive.
    for c in d.select_dtypes(include=["datetime64[ns]","datetimetz"]).columns:
        d[c] = d[c].view("int64")/1e9
    # Original notebook comment normalized for the public code archive.
    obj_cols = list(d.select_dtypes(include=["object","string"]).columns)
    drop_all_null = []
    for c in obj_cols:
        s = pd.Series(d[c], dtype="object")
        if s.isna().all():
            drop_all_null.append(c)
            continue
        m = s.isna(); s = s.astype(str); s[m] = None
        d[c] = s.map(lambda x: x if (x is None or len(x) <= 2000) else x[:2000])
    if drop_all_null:
        print("[INFO] Notebook progress message.")
        d = d.drop(columns=drop_all_null)
    return d

def write_dta(df, path, var_labels=None):
    Path(Path(path).parent).mkdir(parents=True, exist_ok=True)
    df2 = sanitize_for_stata(df)
    vlabels = {k: var_labels.get(k, "") for k in df2.columns} if var_labels else None
    try:
        import pyreadstat, inspect
        kwargs = {"version": 118}
        if vlabels and "variable_labels" in inspect.signature(pyreadstat.write_dta).parameters:
            kwargs["variable_labels"] = vlabels
        pyreadstat.write_dta(df2, path, **kwargs)
        print("[INFO] Notebook progress message.")
    except Exception as e:
        print("[INFO] Notebook progress message.")
        # Original notebook comment normalized for the public code archive.
        df2.to_stata(path, write_index=False, version=118, variable_labels=vlabels)
        print("[INFO] Notebook progress message.")

def ensure_varname_len32(df):
    """Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    cols = list(df.columns)
    new = []
    used = set()
    for c in cols:
        base = str(c)[:32]
        name = base
        i = 1
        while name in used:
            suffix = f"_{i}"
            name = (base[:32-len(suffix)] + suffix)
            i += 1
        new.append(name)
        used.add(name)
    if new != cols:
        df = df.rename(columns=dict(zip(cols, new)))
        print("[INFO] Notebook progress message.")
    return df

def write_stata_safely(df, out_path, var_labels=None):
    df = ensure_varname_len32(df)
    write_dta(df, out_path, var_labels=var_labels)

def dedup_on_keys(df, keys):
    before = len(df)
    df2 = df.drop_duplicates(subset=list(keys), keep="first")
    if len(df2) < before:
        print("[INFO] Notebook progress message.")
    return df2

def merge_no_suffix(left, right, keys, suffix="_dup", how="left"):
    """Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    overlap = [c for c in right.columns if c in left.columns and c not in keys]
    merged = left.merge(right, on=list(keys), how=how, suffixes=("", suffix))
    for c in overlap:
        c2 = c + suffix
        merged[c] = merged[c].combine_first(merged[c2])
        merged = merged.drop(columns=[c2])
    return merged

# =============================================================================
def select_by_codes(df, code_list):
    """Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    cols = list(df.columns)
    want = []
    for code in code_list:
        pat = re.compile(r'^' + re.escape(code.lower()) + r'(?=$|[_a-z0-9])')
        picks = [c for c in cols if pat.search(c.lower())]
        want.extend(picks)
    seen = set()
    want = [c for c in cols if c in want and not (c in seen or seen.add(c))]
    return want

def select_D_2020(df):
    """Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    da_core = ["DA001","DA002","DA002_1","DA003",
               "DA005","DA006","DA007","DA008","DA009","DA010","DA011","DA012","DA013","DA014",
               "DA019","DA020","DA021","DA022","DA023","DA024","DA025","DA026",
               "DA038","DA039"]
    db_adl = [f"DB{str(i).zfill(3)}" for i in range(1,24)]  # 001..023
    dc_cesd = [f"DC{str(i).zfill(3)}" for i in range(9,19)] + ["DC023","DC024","DC025"]

    keep = [*select_by_codes(df, [c.lower() for c in da_core]),
            *select_by_codes(df, [c.lower() for c in db_adl]),
            *select_by_codes(df, [c.lower() for c in dc_cesd])]
    # Original notebook comment normalized for the public code archive.
    seen=set(); keep=[c for c in df.columns if c in keep and not (c in seen or seen.add(c))]
    return keep

def select_CA015_016(df):
    cols, L = list(df.columns), [c.lower() for c in df.columns]
    keep=[]
    for base in ("ca015","ca016"):
        # Original notebook comment normalized for the public code archive.
        for i in range(1,21):
            for nm in (f"{base}_{i}", f"{base}_{i}_"):
                if nm in L: keep.append(cols[L.index(nm)])
    seen=set(); return [c for c in cols if c in keep and not (c in seen or seen.add(c))]

def select_CA017(df):
    """Archived notebook note for 01_wave_health_status.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    cols = list(df.columns)
    want = []
    pat = re.compile(r'^ca017_1_(?:[1-9]|1[0-9]|20)_?$', re.IGNORECASE)
    for c in cols:
        if pat.match(c.lower()):
            want.append(c)
    return want

# =============================================================================
D_raw,  D_labels  = read_dta_with_labels(f_d)
CI_raw, CI_labels = read_dta_with_labels(f_ci)

# Original notebook comment normalized for the public code archive.
D  = standardize_keys(D_raw,  need_id=True)
CI = standardize_keys(CI_raw, need_id=False)

keys_hh     = ("householdID","communityID")
keys_person = ("householdID","communityID","ID")

# Original notebook comment normalized for the public code archive.
D_cols  = [*keys_person, *select_D_2020(D)]
CI_cols = [*keys_hh,     *select_CA015_016(CI), *select_CA017(CI)]

print("[INFO] Notebook progress message.")

# Original notebook comment normalized for the public code archive.
D  = dedup_on_keys(D[D_cols],  keys_person)
CI = dedup_on_keys(CI[CI_cols], keys_hh)

# =============================================================================
health = merge_no_suffix(D, CI, keys=keys_hh, suffix="_ci", how="left")
print("[INFO] Notebook progress message.")

# =============================================================================
Path(base_out).mkdir(parents=True, exist_ok=True)
labels_all = {**D_labels, **CI_labels}

write_stata_safely(health, out_dta, var_labels=labels_all)
try:
    health.to_excel(out_xlsx, index=False)
    print("[INFO] Notebook progress message.")
except Exception as e:
    print("[INFO] Notebook progress message.")
