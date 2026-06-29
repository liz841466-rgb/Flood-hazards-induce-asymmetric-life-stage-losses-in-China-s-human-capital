#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""



# =============================================================================
# Source notebook
# =============================================================================
# record_type : wave_step
# year        : 2011
# step        : 2
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 7
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
import re
from pathlib import Path
import numpy as np
import pandas as pd

# =============================================================================
in_path  = r"E:\impact_assessment_child_order\older\health\2011\health.dta"
out_dir  = r"E:\impact_assessment_child_order\older\health\2011"
out_dta  = fr"{out_dir}\2011_health_result.dta"
out_xlsx = fr"{out_dir}\2011_health_result.xlsx"
out_elim = fr"{out_dir}\eliminate.xlsx"

# =================================================
# Original notebook comment normalized for the public code archive.
# =================================================
def read_dta(path):
    df = pd.read_stata(path, convert_categoricals=False)
    print("[INFO] Notebook progress message.")
    return df

def ensure_dir(p):
    Path(p).mkdir(parents=True, exist_ok=True)

def find_cols(df, pattern):
    """Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if isinstance(pattern, str):
        pattern = re.compile(pattern, flags=re.IGNORECASE)
    return [c for c in df.columns if pattern.match(c)]

def sort_cols_by_suffix(cols, prefix_regex=r"^(.+?)_?(\d+)_?$"):
    """Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    def key(c):
        m = re.match(prefix_regex, c, flags=re.IGNORECASE)
        return (int(m.group(2)) if m else 10**9)
    return sorted(cols, key=key)

def first_nonnull(*series):
    """Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    out = None
    for s in series:
        if s is None:
            continue
        s = pd.to_numeric(s, errors="coerce")
        out = s if out is None else out.combine_first(s)
    return out

def row_any_eq(df, cols, val):
    if not cols:
        return pd.Series(False, index=df.index)
    arr = df[cols].apply(pd.to_numeric, errors="coerce")
    return (arr == val).any(axis=1)

def row_all_eq(df, cols, val):
    if not cols:
        return pd.Series(False, index=df.index)
    arr = df[cols].apply(pd.to_numeric, errors="coerce")
    any_notna = arr.notna().any(axis=1)
    all_val = (arr.replace(np.nan, val) == val).all(axis=1)
    return any_notna & all_val

def row_min(df, cols):
    if not cols:
        return pd.Series(np.nan, index=df.index)
    arr = df[cols].apply(pd.to_numeric, errors="coerce")
    return arr.min(axis=1)

def ensure_varname_len32(df):
    """Archived notebook note for 02_wave_health_recode.

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
        new.append(name); used.add(name)
    if new != cols:
        df = df.rename(columns=dict(zip(cols,new)))
        print("[INFO] Notebook progress message.")
    return df

def write_stata_safely(df, out_path, var_labels=None):
    df = ensure_varname_len32(df)
    ensure_dir(Path(out_path).parent)
    try:
        import pyreadstat
        vlabels = {k: var_labels.get(k, "") for k in df.columns} if var_labels else None
        last_err = None
        for ver in (118, 117, 114):
            try:
                pyreadstat.write_dta(df, out_path, version=ver, variable_labels=vlabels)
                print("[INFO] Notebook progress message.")
                return
            except Exception as e:
                last_err = e
        print("[INFO] Notebook progress message.")
    except Exception as e:
        print("[INFO] Notebook progress message.", e)

    # Original notebook comment normalized for the public code archive.
    def to_latin1(d):
        d = d.copy()
        for c in d.select_dtypes(include=["object","string"]).columns:
            s = d[c].astype(object)
            mask = pd.isna(s)
            s = s.astype(str).str.encode("latin-1", errors="ignore").str.decode("latin-1")
            s[mask] = None
            d[c] = s
        return d
    df2 = to_latin1(df)
    df2.to_stata(out_path, write_index=False, version=117)
    print("[INFO] Notebook progress message.")

def _clean_to_str(s: pd.Series) -> pd.Series:
    """Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = pd.Series(s, dtype="object")
    m = s.isna()
    sc = s[~m].astype(str).str.strip()
    sc = sc.str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = sc
    s.loc[m]  = np.nan
    return s

def canon_id_fixed(s: pd.Series, width: int) -> pd.Series:
    """Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = _clean_to_str(s)
    m = s.notna()
    s.loc[m] = s.loc[m].astype(str).str.zfill(width)
    return s

def _digits_width(s: pd.Series, width: int) -> pd.Series:
    """Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    t = _clean_to_str(s).str.replace(r"\D", "", regex=True)
    t = t.where(t.str.len() > 0, np.nan)
    return t.where(t.isna(), t.str[-width:].str.zfill(width)).astype("object")

def add_id12_hhid10_2011(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()
    hh9  = _digits_width(df["householdID"], 9) if "householdID" in df.columns else pd.Series(np.nan, index=df.index)
    id11 = _digits_width(df["ID"],          11) if "ID"          in df.columns else pd.Series(np.nan, index=df.index)

    df["householdID10"] = hh9.where(hh9.isna(), hh9 + "0")
    pn2 = id11.str[-2:]
    df["ID12"] = np.where(hh9.notna() & pn2.notna(), df["householdID10"] + pn2, np.nan).astype("object")
    return df

def suffix_map(cols):
    """Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    m = {}
    for c in cols:
        mt = re.search(r"_(\d+)_?$", c, flags=re.I)
        if mt:
            m[mt.group(1)] = c
    return m

# =================================================
# Original notebook comment normalized for the public code archive.
# =================================================
df = read_dta(in_path)

# Original notebook comment normalized for the public code archive.
for key in ("householdID","communityID","ID"):
    if key not in df.columns and key.lower() in df.columns.str.lower():
        real = df.columns[df.columns.str.lower()==key.lower()][0]
        df = df.rename(columns={real:key})

# Original notebook comment normalized for the public code archive.
if "householdID" in df.columns:
    df["householdID"] = canon_id_fixed(df["householdID"], 9)
if "communityID" in df.columns:
    df["communityID"] = canon_id_fixed(df["communityID"], 7)
if "ID" in df.columns:
    df["ID"] = canon_id_fixed(df["ID"], 11)

# Original notebook comment normalized for the public code archive.
df = add_id12_hhid10_2011(df)

# =================================================
# Original notebook comment normalized for the public code archive.
# =================================================
# Original notebook comment normalized for the public code archive.
col_da001 = find_cols(df, r"^da001_?$")
col_da002 = find_cols(df, r"^da002_?$")
col_da079 = find_cols(df, r"^da079_?$")
col_da080 = find_cols(df, r"^da080_?$")
srh = first_nonnull(
    df[col_da001[0]] if col_da001 else None,
    df[col_da002[0]] if col_da002 else None,
    df[col_da079[0]] if col_da079 else None,
    df[col_da080[0]] if col_da080 else None,
)

# Original notebook comment normalized for the public code archive.
d7_cols = find_cols(df, r"^da007_\d+_?$")
d7_cols = sort_cols_by_suffix(d7_cols, r"^(da007)_?(\d+)_?$")
disease = pd.Series(np.nan, index=df.index, dtype="float64")
if d7_cols:
    disease = pd.Series(
        np.where(row_any_eq(df, d7_cols, 1), 1,
                 np.where(row_all_eq(df, d7_cols, 2), 2, np.nan)),
        index=df.index, dtype="float64"
    )

# Original notebook comment normalized for the public code archive.
d711_cols = find_cols(df, r"^da007_11_?$")
mental_neuro_psych = pd.Series(np.nan, index=df.index, dtype="float64")
if d711_cols:
    s = pd.to_numeric(df[d711_cols[0]], errors="coerce")
    mental_neuro_psych = s.where(s.isin([1,2]), np.nan)

d712_cols = find_cols(df, r"^da007_12_?$")
memory_disease = pd.Series(np.nan, index=df.index, dtype="float64")
if d712_cols:
    s = pd.to_numeric(df[d712_cols[0]], errors="coerce")
    memory_disease = s.where(s.isin([1,2]), np.nan)

# Original notebook comment normalized for the public code archive.
s_cols_1_11 = sort_cols_by_suffix(find_cols(df, r"^da056s([1-9]|1[0-1])_?$"), r"^(da056s)_?(\d+)_?$")
s_col_12    = find_cols(df, r"^da056s12_?$")
social_activity = pd.Series(np.nan, index=df.index, dtype="float64")
if s_cols_1_11 or s_col_12:
    any_1_11 = df[s_cols_1_11].notna().any(axis=1) if s_cols_1_11 else False
    eq12_12  = row_any_eq(df, s_col_12, 12) if s_col_12 else False
    social_activity = pd.Series(
        np.where(eq12_12, 2, np.where(any_1_11, 1, np.nan)),
        index=df.index, dtype="float64"
    )

# Original notebook comment normalized for the public code archive.
f_cols = sort_cols_by_suffix(find_cols(df, r"^da057_(?:[1-9]|10|11)_?$"))
social_freq = pd.Series(np.nan, index=df.index, dtype="float64")
if f_cols:
    social_freq = row_min(df, f_cols)
if isinstance(social_activity, pd.Series):
    social_freq = pd.to_numeric(social_freq, errors="coerce")
    social_freq.loc[social_activity == 2] = 0

# Original notebook comment normalized for the public code archive.
db_map = {
    "db001": ("run1km", "慢跑1km"),
    "db002": ("walk1km", "步行1km"),
    "db003": ("walk100m", "步行100m"),
    "db004": ("sit_to_stand", "座位起立"),
    "db005": ("stairs", "爬楼"),
    "db006": ("bend_kneel_squat", "弯腰/跪/蹲"),
    "db007": ("arm_raise", "上肢伸展"),
    "db008": ("lift5kg", "提举5kg"),
    "db009": ("pick_coin", "桌上拾硬币"),
    "db010": ("dress", "穿衣"),
    "db011": ("bathe", "洗澡"),
    "db012": ("eat", "进食"),
    "db013": ("bed_chair_transfer", "床椅转移"),
    "db014": ("toilet", "如厕"),
    "db015": ("incontinence", "大小便控制"),
    "db016": ("housework", "做家务"),
}
# Original notebook comment normalized for the public code archive.
db_cols_present = {old: find_cols(df, rf"^{old}_?$")[0] for old in db_map if find_cols(df, rf"^{old}_?$")}
db_new = {}
for old,(new,label) in db_map.items():
    if old in db_cols_present:
        db_new[new] = pd.to_numeric(df[db_cols_present[old]], errors="coerce")

# Original notebook comment normalized for the public code archive.
if "db001" in db_cols_present:
    mask_db001_eq1 = pd.to_numeric(df[db_cols_present["db001"]], errors="coerce") == 1
    for target in ("db002","db003"):
        tgt_new = db_map[target][0]
        if tgt_new not in db_new:
            db_new[tgt_new] = pd.Series(np.nan, index=df.index, dtype="float64")
        db_new[tgt_new].loc[mask_db001_eq1] = 1

# =============================================================================
if "db002" in db_cols_present:
    mask_db002_eq1 = pd.to_numeric(df[db_cols_present["db002"]], errors="coerce") == 1
    tgt_new = db_map["db003"][0]
    if tgt_new not in db_new:
        db_new[tgt_new] = pd.Series(np.nan, index=df.index, dtype="float64")
    db_new[tgt_new].loc[mask_db002_eq1] = 1

# Original notebook comment normalized for the public code archive.
needed_for_skip = ["db001"] + [f"db00{i}" for i in range(3,10)]
present_needed = [k for k in needed_for_skip if k in db_cols_present]
if present_needed:
    arr = pd.DataFrame({k: pd.to_numeric(df[db_cols_present[k]], errors="coerce") for k in present_needed})
    mask_all1 = (arr == 1).all(axis=1)
    for k in [f"db01{i}" for i in range(0,6)]:  # db010..db015
        newname = db_map[k][0]
        if newname not in db_new:
            db_new[newname] = pd.Series(np.nan, index=df.index, dtype="float64")
        fill_mask = mask_all1 & db_new[newname].isna()
        db_new[newname].loc[fill_mask] = 1

# Original notebook comment normalized for the public code archive.
dc_map = {
    "dc011": ("depress", "抑郁"),
    "dc012": ("effort", "做事很费力"),
    "dc013": ("hope", "对未来有希望"),
    "dc014": ("fear", "害怕"),
    "dc015": ("sleep", "睡眠差"),
    "dc016": ("happy", "快乐"),
    "dc018": ("hopeless", "活不下去"),
    "dc028": ("life_satisfaction", "生活满意度"),
}
dc_new = {}
for old,(new,label) in dc_map.items():
    real = find_cols(df, rf"^{old}_?$")
    if real:
        dc_new[new] = pd.to_numeric(df[real[0]], errors="coerce")

# Original notebook comment normalized for the public code archive.
cd003_cols = sort_cols_by_suffix(find_cols(df, r"^cd003_(?:[1-9]|1[0-4])_?$"))
if cd003_cols:
    all_na_cd003 = df[cd003_cols].isna().all(axis=1)
    if all_na_cd003.any():
        df.loc[all_na_cd003, cd003_cols] = 9
    meet_child = row_min(df, cd003_cols)
else:
    meet_child = pd.Series(np.nan, index=df.index)
meet_child = pd.to_numeric(meet_child, errors="coerce").fillna(9)  # Original notebook comment normalized for the public code archive.

# Original notebook comment normalized for the public code archive.
cd004_cols = sort_cols_by_suffix(find_cols(df, r"^cd004_(?:[1-9]|1[0-4])_?$"))
# Original notebook comment normalized for the public code archive.
if cd003_cols and cd004_cols:
    m3 = suffix_map(cd003_cols); m4 = suffix_map(cd004_cols)
    for k in (set(m3) & set(m4)):
        c3, c4 = m3[k], m4[k]
        v3 = pd.to_numeric(df[c3], errors="coerce")
        mask_fill = df[c4].isna() & v3.isin([1,2,3])
        df.loc[mask_fill, c4] = v3.loc[mask_fill]
if cd004_cols:
    all_na_cd004 = df[cd004_cols].isna().all(axis=1)
    if all_na_cd004.any():
        df.loc[all_na_cd004, cd004_cols] = 9
    call_child = row_min(df, cd004_cols)
else:
    call_child = pd.Series(np.nan, index=df.index)
call_child = pd.to_numeric(call_child, errors="coerce").fillna(9)  # Original notebook comment normalized for the public code archive.

# Original notebook comment normalized for the public code archive.
ce_cols = [c for c in (find_cols(df, r"^ce027_?$") + find_cols(df, r"^ce031_?$"))]
annual_transfer = pd.Series(2, index=df.index, dtype="float64")
if ce_cols:
    any1 = row_any_eq(df, ce_cols, 1)
    annual_transfer.loc[any1] = 1

# =================================================
# Original notebook comment normalized for the public code archive.
# =================================================
prefix_pat = re.compile(r"^(da|db|dc|cd|ce)", flags=re.IGNORECASE)
measure_raw_cols = [c for c in df.columns if prefix_pat.match(c)]
id_cols_keys = [c for c in ["ID","householdID","communityID","householdID10","ID12"] if c in df.columns]  # Original notebook comment normalized for the public code archive.

if measure_raw_cols:
    mask_elim = df[measure_raw_cols].isna().all(axis=1)
else:
    mask_elim = pd.Series(False, index=df.index)

eliminated = df.loc[mask_elim, id_cols_keys].copy()
kept_mask = ~mask_elim

print("[INFO] Notebook progress message.")
ensure_dir(out_dir)
# Original notebook comment normalized for the public code archive.
if not eliminated.empty:
    eliminated.to_excel(out_elim, index=False)
    print("[INFO] Notebook progress message.")

# =================================================
# Original notebook comment normalized for the public code archive.
# =================================================
# Excel output note.
cols_keys = {
    "ID": df["ID"] if "ID" in df.columns else np.nan,
    "householdID": df["householdID"] if "householdID" in df.columns else np.nan,
    "communityID": df["communityID"] if "communityID" in df.columns else np.nan,
    "householdID10": df["householdID10"] if "householdID10" in df.columns else np.nan,  # ★
    "ID12": df["ID12"] if "ID12" in df.columns else np.nan,                              # ★
}

res = pd.DataFrame({
    **cols_keys,
    "srh": srh,                          # Original notebook comment normalized for the public code archive.
    "disease": disease,                  # Original notebook comment normalized for the public code archive.
    "mental_neuro_psych": mental_neuro_psych,  # Original notebook comment normalized for the public code archive.
    "memory_disease": memory_disease,          # Original notebook comment normalized for the public code archive.
    "social_activity": social_activity,  # Original notebook comment normalized for the public code archive.
    "social_freq": social_freq,          # Original notebook comment normalized for the public code archive.
    "meet_child_freq": meet_child,       # Original notebook comment normalized for the public code archive.
    "call_child_freq": call_child,       # Original notebook comment normalized for the public code archive.
    "annual_transfer": annual_transfer,  # Original notebook comment normalized for the public code archive.
}, index=df.index)

# Original notebook comment normalized for the public code archive.
for k, v in db_new.items():
    res[k] = v
for k, v in dc_new.items():
    res[k] = v

# Original notebook comment normalized for the public code archive.
res = res.loc[kept_mask].reset_index(drop=True)

# Original notebook comment normalized for the public code archive.
var_labels = {
    "ID": "ID(2011原11位)",
    "householdID": "householdID(9位，2011原始)",
    "communityID": "communityID(7位)",
    "householdID10": "householdID(10位，2013+兼容)",  # ★
    "ID12": "个人ID(12位，2013+兼容)",                 # ★
    "srh": "自评健康",
    "disease": "疾病",
    "mental_neuro_psych": "情绪/神经/精神问题",
    "memory_disease": "记忆相关疾病",
    "social_activity": "社交活动",
    "social_freq": "社交频率",
    "meet_child_freq": "与子女见面频率",
    "call_child_freq": "与子女通讯频率",
    "annual_transfer": "年度转移",
}
for old,(new,label) in db_map.items():
    if new in res.columns:
        var_labels[new] = label
for old,(new,label) in dc_map.items():
    if new in res.columns:
        var_labels[new] = label

# Original notebook comment normalized for the public code archive.
ensure_dir(out_dir)

# Original notebook comment normalized for the public code archive.
write_stata_safely(res, out_dta, var_labels=var_labels)

# Excel output note.
cn_cols = {c: var_labels.get(c, c) for c in res.columns}
for k in ("ID","householdID","communityID","householdID10","ID12"):  # Original notebook comment normalized for the public code archive.
    if k in cn_cols:
        cn_cols[k] = k
res_excel = res.rename(columns=cn_cols)
res_excel.to_excel(out_xlsx, index=False)
print("[INFO] Notebook progress message.")
print("[INFO] Notebook progress message.")




# =============================================================================
# Source notebook
# =============================================================================
# record_type : wave_step
# year        : 2013
# step        : 2
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 16
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
import re
from pathlib import Path
import numpy as np
import pandas as pd

# =============================================================================
in_path  = r"E:\impact_assessment_child_order\older\health\2013\health.dta"
out_dir  = r"E:\impact_assessment_child_order\older\health\2013"
out_dta  = fr"{out_dir}\2013_health_result.dta"
out_xlsx = fr"{out_dir}\2013_health_result.xlsx"
out_elim = fr"{out_dir}\eliminate.xlsx"

# =================================================
# Original notebook comment normalized for the public code archive.
# =================================================
def read_dta(path):
    df = pd.read_stata(path, convert_categoricals=False)
    print("[INFO] Notebook progress message.")
    return df

def ensure_dir(p):
    Path(p).mkdir(parents=True, exist_ok=True)

def find_cols(df, pattern):
    """Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if isinstance(pattern, str):
        pattern = re.compile(pattern, flags=re.IGNORECASE)
    return [c for c in df.columns if pattern.match(c)]

def sort_cols_by_suffix(cols, prefix_regex=r"^(.+?)_?(\d+)_?$"):
    """Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    def key(c):
        m = re.match(prefix_regex, c, flags=re.IGNORECASE)
        return (int(m.group(2)) if m else 10**9)
    return sorted(cols, key=key)

def suffix_map(cols):
    """Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    m = {}
    for c in cols:
        mt = re.search(r"_(\d+)_?$", c, flags=re.I)
        if mt:
            m[mt.group(1)] = c
    return m

def first_nonnull(*series):
    """Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    out = None
    for s in series:
        if s is None:
            continue
        s = pd.to_numeric(s, errors="coerce")
        out = s if out is None else out.combine_first(s)
    return out

def row_min(df, cols):
    if not cols:
        return pd.Series(np.nan, index=df.index)
    arr = df[cols].apply(pd.to_numeric, errors="coerce")
    return arr.min(axis=1)

def ensure_varname_len32(df):
    """Archived notebook note for 02_wave_health_recode.

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
        new.append(name); used.add(name)
    if new != cols:
        df = df.rename(columns=dict(zip(cols,new)))
        print("[INFO] Notebook progress message.")
    return df

def write_stata_safely(df, out_path, var_labels=None):
    df = ensure_varname_len32(df)
    ensure_dir(Path(out_path).parent)
    try:
        import pyreadstat
        vlabels = {k: var_labels.get(k, "") for k in df.columns} if var_labels else None
        last_err = None
        for ver in (118, 117, 114):
            try:
                pyreadstat.write_dta(df, out_path, version=ver, variable_labels=vlabels)
                print("[INFO] Notebook progress message.")
                return
            except Exception as e:
                last_err = e
        print("[INFO] Notebook progress message.")
    except Exception as e:
        print("[INFO] Notebook progress message.", e)

    # Original notebook comment normalized for the public code archive.
    def to_latin1(d):
        d = d.copy()
        for c in d.select_dtypes(include=["object","string"]).columns:
            s = d[c].astype(object)
            mask = pd.isna(s)
            s = s.astype(str).str.encode("latin-1", errors="ignore").str.decode("latin-1")
            s[mask] = None
            d[c] = s
        return d
    df2 = to_latin1(df)
    df2.to_stata(out_path, write_index=False, version=117)
    print("[INFO] Notebook progress message.")

def _clean_to_str(s: pd.Series) -> pd.Series:
    """Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = pd.Series(s, dtype="object")
    m = s.isna()
    sc = s[~m].astype(str).str.strip()
    sc = sc.str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = sc
    s.loc[m]  = np.nan
    return s

def canon_id_fixed(s: pd.Series, width: int) -> pd.Series:
    """Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = _clean_to_str(s)
    m = s.notna()
    s.loc[m] = s.loc[m].astype(str).str.zfill(width)
    return s

# =================================================
# Original notebook comment normalized for the public code archive.
# =================================================
def pick_scalar(df, families):
    """Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    series_list = []
    for fam in families:
        cols = find_cols(df, rf"^{fam}_?$")
        if cols:
            series_list.append(pd.to_numeric(df[cols[0]], errors="coerce"))
    return first_nonnull(*series_list) if series_list else pd.Series(np.nan, index=df.index)

def pick_group(df, families):
    """Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    suf_set = set()
    for fam in families:
        cols = find_cols(df, rf"^{fam}_?(\d+)_?$")  # Original notebook comment normalized for the public code archive.
        for c in cols:
            m = re.search(r"(\d+)_?$", c, flags=re.I)  # Original notebook comment normalized for the public code archive.
            if m: suf_set.add(m.group(1))

    merged = {}
    for s in sorted(suf_set, key=lambda x: int(x)):
        series_list = []
        for fam in families:
            cand = find_cols(df, rf"^{fam}_?{s}_?$")  # Original notebook comment normalized for the public code archive.
            if cand:
                series_list.append(pd.to_numeric(df[cand[0]], errors="coerce"))
        merged[s] = first_nonnull(*series_list) if series_list else pd.Series(np.nan, index=df.index)
    return merged

# ================================
# Original notebook comment normalized for the public code archive.
# ================================
df = read_dta(in_path)

# Original notebook comment normalized for the public code archive.
for key in ("householdID","communityID","ID"):
    if key not in df.columns and key.lower() in df.columns.str.lower():
        real = df.columns[df.columns.str.lower()==key.lower()][0]
        df = df.rename(columns={real:key})

# Original notebook comment normalized for the public code archive.
if "householdID" in df.columns:
    df["householdID"] = canon_id_fixed(df["householdID"], 9)
if "communityID" in df.columns:
    df["communityID"] = canon_id_fixed(df["communityID"], 7)
if "ID" in df.columns:
    df["ID"] = canon_id_fixed(df["ID"], 11)

# ================================
# Original notebook comment normalized for the public code archive.
# ================================
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
da001_any = pick_scalar(df, ["ZDA001","DA001"])
da002_any = pick_scalar(df, ["ZDA002","DA002"])
da079_any = pick_scalar(df, ["ZDA079","DA079"])
da080_any = pick_scalar(df, ["ZDA080","DA080"])
srh = first_nonnull(da001_any, da002_any, da079_any, da080_any)

# Original notebook comment normalized for the public code archive.
d7 = pick_group(df, ["DA007_W2FILLED", "ZDA007", "DA007"])
disease = pd.Series(np.nan, index=df.index, dtype="float64")
if d7:
    arr = pd.DataFrame({f"da007_{k}": v for k, v in d7.items()})
    any1 = (arr == 1).any(axis=1)
    any_notna = arr.notna().any(axis=1)
    all2 = (arr.fillna(2) == 2).all(axis=1) & any_notna
    disease = pd.Series(np.where(any1, 1, np.where(all2, 2, np.nan)),
                        index=df.index, dtype="float64")
# Original notebook comment normalized for the public code archive.
da007_11 = d7.get("11", pd.Series(np.nan, index=df.index))
da007_12 = d7.get("12", pd.Series(np.nan, index=df.index))
mental_neuro_psych = pd.to_numeric(da007_11, errors="coerce").where(lambda s: s.isin([1,2]))
memory_disease     = pd.to_numeric(da007_12, errors="coerce").where(lambda s: s.isin([1,2]))

# Original notebook comment normalized for the public code archive.
s56 = pick_group(df, ["ZDA056s", "DA056s"])
s56_1_11 = [s56[k] for k in sorted([x for x in s56.keys() if x.isdigit() and 1<=int(x)<=11], key=int)]
any_1_11 = (pd.concat(s56_1_11, axis=1).notna().any(axis=1) if s56_1_11 else pd.Series(False, index=df.index))
# Original notebook comment normalized for the public code archive.
s12_candidates = []
for fam in ["ZDA056s12","DA056s12"]:
    s12_candidates += [df[c] for c in find_cols(df, rf"^{fam}(_\d+)?_?$")]
any_12_is_12 = pd.Series(False, index=df.index)
if s12_candidates:
    s12_mat = pd.concat([pd.to_numeric(s, errors="coerce") for s in s12_candidates], axis=1)
    any_12_is_12 = (s12_mat == 12).any(axis=1)
social_activity = pd.Series(np.where(any_12_is_12, 2,
                                     np.where(any_1_11, 1, np.nan)),
                            index=df.index, dtype="float64")

# Original notebook comment normalized for the public code archive.
s57 = pick_group(df, ["ZDA057", "DA057"])
s57_series = [s57[k] for k in sorted(s57.keys(), key=int)] if s57 else []
if s57_series:
    freq_df = pd.concat([pd.to_numeric(s, errors="coerce") for s in s57_series], axis=1)
    social_freq = freq_df.min(axis=1)
else:
    social_freq = pd.Series(np.nan, index=df.index, dtype="float64")
social_freq.loc[social_activity == 2] = 0

# Original notebook comment normalized for the public code archive.
db_map = {
    "DB001": ("run1km", "慢跑1km"),
    "DB002": ("walk1km", "步行1km"),
    "DB003": ("walk100m", "步行100m"),
    "DB004": ("sit_to_stand", "座位起立"),
    "DB005": ("stairs", "爬楼"),
    "DB006": ("bend_kneel_squat", "弯腰/跪/蹲"),
    "DB007": ("arm_raise", "上肢伸展"),
    "DB008": ("lift5kg", "提举5kg"),
    "DB009": ("pick_coin", "桌上拾硬币"),
    "DB010": ("dress", "穿衣"),
    "DB011": ("bathe", "洗澡"),
    "DB012": ("eat", "进食"),
    "DB013": ("bed_chair_transfer", "床椅转移"),
    "DB014": ("toilet", "如厕"),
    "DB015": ("incontinence", "大小便控制"),
    "DB016": ("housework", "做家务"),
}
db_new = {}
for old,(new,label) in db_map.items():
    db_new[new] = pick_scalar(df, [f"Z{old}", old])  # Original notebook comment normalized for the public code archive.

# =============================================================================
if "run1km" in db_new:
    m1 = (pd.to_numeric(db_new["run1km"], errors="coerce") == 1)
    for tgt in ("walk1km","walk100m"):
        if tgt in db_new:
            db_new[tgt] = db_new[tgt].copy()
            db_new[tgt].loc[m1] = 1
if "walk1km" in db_new and "walk100m" in db_new:
    m2 = (pd.to_numeric(db_new["walk1km"], errors="coerce") == 1)
    db_new["walk100m"] = db_new["walk100m"].copy()
    db_new["walk100m"].loc[m2] = 1

# Original notebook comment normalized for the public code archive.
needed = ["run1km","walk100m","pick_coin","lift5kg","arm_raise","bend_kneel_squat","stairs"]
present_needed = [k for k in needed if k in db_new]
if present_needed:
    arr = pd.DataFrame({k: pd.to_numeric(db_new[k], errors="coerce") for k in present_needed})
    mask_all1 = (arr == 1).all(axis=1)
    for tgt in ["dress","bathe","eat","bed_chair_transfer","toilet","incontinence"]:
        if tgt in db_new:
            db_new[tgt] = db_new[tgt].copy()
            fill_mask = mask_all1 & db_new[tgt].isna()
            db_new[tgt].loc[fill_mask] = 1

# =============================================================================
APPLY_UNDER50_SKIP_IMPUTE = True
if APPLY_UNDER50_SKIP_IMPUTE:
    # Original notebook comment normalized for the public code archive.
    birth_year = pick_scalar(df, ["ZBA002_1","BA002_1","ZBA002","BA002"])
    under50 = pd.to_numeric(birth_year, errors="coerce") > 1963  # 2013-50=1963
    good_srh = pd.to_numeric(srh, errors="coerce").isin([1,2])

    def da_eq2(code):
        # Original notebook comment normalized for the public code archive.
        s = pick_scalar(df, [f"Z{code}", code])
        return (pd.to_numeric(s, errors="coerce") == 2)

    cond_list = [da_eq2(x) for x in ["DA003","DA004","DA005","DA008"]]
    # Original notebook comment normalized for the public code archive.
    if not disease.isna().all():
        cond_list.append(pd.to_numeric(disease, errors="coerce") == 2)

    if all(c is not None for c in cond_list):
        cond_all = cond_list[0]
        for c in cond_list[1:]:
            cond_all = cond_all & c
        mask_skip = under50 & good_srh & cond_all
        if mask_skip.any():
            for k in db_new:
                db_new[k] = db_new[k].copy()
                db_new[k].loc[mask_skip] = 1

# Original notebook comment normalized for the public code archive.
dc_map = {
    "DC011": ("depress", "抑郁"),
    "DC012": ("effort", "做事很费力"),
    "DC013": ("hope", "对未来有希望"),
    "DC014": ("fear", "害怕"),
    "DC015": ("sleep", "睡眠差"),
    "DC016": ("happy", "快乐"),
    "DC018": ("hopeless", "活不下去"),
    "DC028": ("life_satisfaction", "生活满意度"),
}
dc_new = {}
for old,(new,label) in dc_map.items():
    dc_new[new] = pick_scalar(df, [f"Z{old}", old])  # Original notebook comment normalized for the public code archive.

# Original notebook comment normalized for the public code archive.
cd3 = pick_group(df, ["ZCD003","CD003"])
cd4 = pick_group(df, ["ZCD004","CD004"])
shared_keys = sorted(set(cd3.keys()) & set(cd4.keys()), key=int)
for k in shared_keys:
    v3 = pd.to_numeric(cd3[k], errors="coerce")
    s4 = cd4[k].copy()
    mask_fill = s4.isna() & v3.isin([1,2,3])
    s4.loc[mask_fill] = v3.loc[mask_fill]
    cd4[k] = s4

def _rowwise_min_or9(series_list):
    if not series_list:
        return pd.Series(9, index=df.index)
    mat = pd.concat([pd.to_numeric(s, errors="coerce") for s in series_list], axis=1)
    all_na = mat.isna().all(axis=1)
    mat.loc[all_na, :] = 9
    return mat.min(axis=1)

meet_child = _rowwise_min_or9([cd3[k] for k in sorted(cd3.keys(), key=int)]) if cd3 else pd.Series(9, index=df.index)
call_child = _rowwise_min_or9([cd4[k] for k in sorted(cd4.keys(), key=int)]) if cd4 else pd.Series(9, index=df.index)
meet_child = pd.to_numeric(meet_child, errors="coerce").fillna(9)
call_child = pd.to_numeric(call_child, errors="coerce").fillna(9)

# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
def collect_ce009_amount_cols(df):
    """Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    pat_amt = re.compile(r'^Z?CE009_(?:1|2|3|4)(?:_(?:\d+))*_?$', re.IGNORECASE)
    pat_minmax_tail = re.compile(r'(?:__?(?:min|max))$', re.IGNORECASE)
    keep = []
    for c in df.columns:
        cl = str(c)
        if pat_amt.match(cl) and not pat_minmax_tail.search(cl):
            keep.append(c)
    # Original notebook comment normalized for the public code archive.
    return list(dict.fromkeys(keep))

ce009_cols = collect_ce009_amount_cols(df)

annual_transfer = pd.Series(np.nan, index=df.index, dtype="float64")  # Original notebook comment normalized for the public code archive.
if ce009_cols:
    A = df[ce009_cols].apply(pd.to_numeric, errors="coerce")
    A = A.mask(A < 0)  # Original notebook comment normalized for the public code archive.
    any_observed = A.notna().any(axis=1)
    any_nonzero  = (A.fillna(0) > 0).any(axis=1)
    all_zero     = (A.fillna(0) == 0).all(axis=1) & any_observed

    annual_transfer.loc[any_nonzero] = 1.0
    annual_transfer.loc[all_zero]    = 2.0

# ================================
# Original notebook comment normalized for the public code archive.
# ================================
prefix_pat = re.compile(r"^(da|db|dc|cd|ce)", flags=re.IGNORECASE)
measure_raw_cols = [c for c in df.columns if prefix_pat.match(c)]
id_cols_triplet = [c for c in ["ID","householdID","communityID"] if c in df.columns]
mask_elim = df[measure_raw_cols].isna().all(axis=1) if measure_raw_cols else pd.Series(False, index=df.index)
eliminated = df.loc[mask_elim, id_cols_triplet].copy()
kept_mask = ~mask_elim
print("[INFO] Notebook progress message.")
ensure_dir(out_dir)
if not eliminated.empty:
    eliminated.to_excel(out_elim, index=False)
    print("[INFO] Notebook progress message.")

# ================================
# Original notebook comment normalized for the public code archive.
# ================================
cols_keys = {
    "ID": df["ID"] if "ID" in df.columns else np.nan,
    "householdID": df["householdID"] if "householdID" in df.columns else np.nan,
    "communityID": df["communityID"] if "communityID" in df.columns else np.nan,
}
res = pd.DataFrame({
    **cols_keys,
    "srh": srh,
    "disease": disease,
    "mental_neuro_psych": mental_neuro_psych,
    "memory_disease": memory_disease,
    "social_activity": social_activity,
    "social_freq": social_freq,
    "meet_child_freq": meet_child,
    "call_child_freq": call_child,
    "annual_transfer": annual_transfer,
}, index=df.index)

# Original notebook comment normalized for the public code archive.
for k,v in db_new.items(): res[k] = v
for k,v in dc_new.items(): res[k] = v

# Original notebook comment normalized for the public code archive.
res = res.loc[kept_mask].reset_index(drop=True)

# Original notebook comment normalized for the public code archive.
var_labels = {
    "ID": "ID",
    "householdID": "householdID",
    "communityID": "communityID",
    "srh": "自评健康",
    "disease": "疾病（合并 Z/基线）",
    "mental_neuro_psych": "情绪/神经/精神问题",
    "memory_disease": "记忆相关疾病",
    "social_activity": "社交活动",
    "social_freq": "社交频率",
    "meet_child_freq": "与子女见面频率",
    "call_child_freq": "与子女通讯频率",
    "annual_transfer": "年度转移",
}
for old,(new,label) in db_map.items():
    if new in res.columns: var_labels[new] = label
for old,(new,label) in dc_map.items():
    if new in res.columns: var_labels[new] = label

# Original notebook comment normalized for the public code archive.
ensure_dir(out_dir)
write_stata_safely(res, out_dta, var_labels=var_labels)

# Excel output note.
cn_cols = {c: var_labels.get(c, c) for c in res.columns}
for k in ("ID","householdID","communityID"): cn_cols[k] = k
res.rename(columns=cn_cols).to_excel(out_xlsx, index=False)
print("[INFO] Notebook progress message.")
print("[INFO] Notebook progress message.")


# ------------------------------------------------------------------------------
# Notebook cell 19
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from pathlib import Path

# =============================================================================
# Excel output note.
path = r"E:\impact_assessment_child_order\older\health\2013\2013_health_result.xlsx"
df = pd.read_excel(path, dtype=object)   # Original notebook comment normalized for the public code archive.

# Original notebook comment normalized for the public code archive.
# path = r"E:\impact_assessment_child_order\older\health\2013\2013_health_result.dta"
# df = pd.read_stata(path, convert_categoricals=False)

# =============================================================================
df = df.replace(r"^\s*$", np.nan, regex=True)

# =============================================================================
n = len(df)
na_count = df.isna().sum()
na_pct = (na_count / n * 100).round(2)

summary = (
    pd.DataFrame({"n_missing": na_count, "missing_pct": na_pct})
      .sort_values("n_missing", ascending=False)
)

# Original notebook comment normalized for the public code archive.
print(summary.head(20))

# Original notebook comment normalized for the public code archive.
out = Path(path).with_name(Path(path).stem + "_missing_summary.xlsx")
summary.to_excel(out, index=True)
print("[INFO] Notebook progress message.")




# =============================================================================
# Source notebook
# =============================================================================
# record_type : wave_step
# year        : 2015
# step        : 2
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 4
# ------------------------------------------------------------------------------
# Notebook-export prose note omitted from the public code archive.


# ------------------------------------------------------------------------------
# Notebook cell 10
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
import re
from pathlib import Path
import numpy as np
import pandas as pd

# =============================================================================
in_path  = r"E:\impact_assessment_child_order\older\health\2015\health.dta"
out_dir  = r"E:\impact_assessment_child_order\older\health\2015"
out_dta  = fr"{out_dir}\2015_health_result.dta"
out_xlsx = fr"{out_dir}\2015_health_result.xlsx"
out_elim = fr"{out_dir}\eliminate.xlsx"

# =============================================================================

def read_dta(path):
    df = pd.read_stata(path, convert_categoricals=False)
    print("[INFO] Notebook progress message.")
    return df

def ensure_dir(p):
    Path(p).mkdir(parents=True, exist_ok=True)

def find_cols(df, pattern):
    """Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if isinstance(pattern, str):
        pattern = re.compile(pattern, flags=re.IGNORECASE)
    return [c for c in df.columns if pattern.match(c)]

def sort_cols_by_suffix(cols, prefix_regex=r"^(.+?)_?(\d+)_?$"):
    def key(c):
        m = re.match(prefix_regex, c, flags=re.IGNORECASE)
        return (int(m.group(2)) if m else 10**9)
    return sorted(cols, key=key)

def suffix_map(cols):
    m = {}
    for c in cols:
        mt = re.search(r"_(\d+)_?$", c, flags=re.I)
        if mt:
            m[mt.group(1)] = c
    return m

def first_nonnull(*series):
    """Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    out = None
    for s in series:
        if s is None:
            continue
        s = pd.to_numeric(s, errors="coerce")
        out = s if out is None else out.combine_first(s)
    return out if out is not None else pd.Series(np.nan, index=series[0].index if series and series[0] is not None else None)

def row_min(df, cols):
    if not cols:
        return pd.Series(np.nan, index=df.index)
    arr = df[cols].apply(pd.to_numeric, errors="coerce")
    return arr.min(axis=1)

def ensure_varname_len32(df):
    cols = list(df.columns)
    new, used = [], set()
    for c in cols:
        base = str(c)[:32]
        name = base
        i = 1
        while name in used:
            suffix = f"_{i}"
            name = (base[:32-len(suffix)] + suffix)
            i += 1
        new.append(name); used.add(name)
    if new != cols:
        df = df.rename(columns=dict(zip(cols, new)))
        print("[INFO] Notebook progress message.")
    return df

def write_stata_safely(df, out_path, var_labels=None):
    df = ensure_varname_len32(df)
    ensure_dir(Path(out_path).parent)
    try:
        import pyreadstat
        vlabels = {k: var_labels.get(k, "") for k in df.columns} if var_labels else None
        last_err = None
        for ver in (118, 117, 114):
            try:
                pyreadstat.write_dta(df, out_path, version=ver, variable_labels=vlabels)
                print("[INFO] Notebook progress message.")
                return
            except Exception as e:
                last_err = e
        print("[INFO] Notebook progress message.")
    except Exception as e:
        print("[INFO] Notebook progress message.", e)
    # Original notebook comment normalized for the public code archive.
    def to_latin1(d):
        d = d.copy()
        for c in d.select_dtypes(include=["object","string"]).columns:
            s = d[c].astype(object)
            mask = pd.isna(s)
            s = s.astype(str).str.encode("latin-1", errors="ignore").str.decode("latin-1")
            s[mask] = None
            d[c] = s
        return d
    df2 = to_latin1(df)
    df2.to_stata(out_path, write_index=False, version=117)
    print("[INFO] Notebook progress message.")

def _clean_to_str(s: pd.Series) -> pd.Series:
    s = pd.Series(s, dtype="object")
    m = s.isna()
    sc = s[~m].astype(str).str.strip()
    sc = sc.str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = sc; s.loc[m] = np.nan
    return s

def canon_id_fixed(s: pd.Series, width: int) -> pd.Series:
    s = _clean_to_str(s)
    m = s.notna()
    s.loc[m] = s.loc[m].astype(str).str.zfill(width)
    return s

# Original notebook comment normalized for the public code archive.

def pick_scalar(df, families):
    """Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    series_list = []
    for fam in families:
        cols = [c for c in df.columns if re.match(rf"^{fam}_?$", c, flags=re.I)]
        if cols:
            series_list.append(pd.to_numeric(df[cols[0]], errors="coerce"))
    if not series_list:
        return pd.Series(np.nan, index=df.index)
    out = series_list[0]
    for s in series_list[1:]:
        out = out.combine_first(s)
    return out

def pick_group(df, families):
    """Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    suf_set = set()
    for fam in families:
        for c in df.columns:
            m = re.match(rf"^{fam}_?(\d+)_?$", c, flags=re.I)
            if m:
                suf_set.add(m.group(1))
    out = {}
    for s in sorted(suf_set, key=lambda x: int(x)):
        series_list = []
        for fam in families:
            cand = [c for c in df.columns if re.match(rf"^{fam}_?{s}_?$", c, flags=re.I)]
            if cand:
                series_list.append(pd.to_numeric(df[cand[0]], errors="coerce"))
        if not series_list:
            out[s] = pd.Series(np.nan, index=df.index)
        else:
            cur = series_list[0]
            for ss in series_list[1:]:
                cur = cur.combine_first(ss)
            out[s] = cur
    return out

# =============================================================================

def _grab_numeric(df, pat):
    """Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if isinstance(pat, str):
        pat = re.compile(pat, flags=re.IGNORECASE)
    cols = [c for c in df.columns if pat.match(c)]
    if not cols:
        return pd.Series(np.nan, index=df.index, dtype="float64")
    return pd.to_numeric(df[cols[0]], errors="coerce")

def synthesize_da007_filled_2015(df):
    """Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    out = {}
    for i in range(1, 15):
        da   = _grab_numeric(df, rf"^DA007_?{i}_?$")
        w21  = _grab_numeric(df, rf"^DA007_W2_1_?{i}_?$")
        w22  = _grab_numeric(df, rf"^DA007_W2_2_?{i}_?$")
        zda7 = _grab_numeric(df, rf"^ZDA007_?{i}_?$")
        zda8 = _grab_numeric(df, rf"^ZDA008_?{i}_?$")
        da8  = _grab_numeric(df, rf"^DA008_?{i}_?$") if i in {1,5,11} else pd.Series(np.nan, index=df.index, dtype="float64")

        pre_have = (zda7 == 1) | (zda8 == 1)

        cur = pd.Series(np.nan, index=df.index, dtype="float64")

        # Original notebook comment normalized for the public code archive.
        m = da.isin([1, 2])
        cur.loc[m] = da[m]

        # Original notebook comment normalized for the public code archive.
        m = cur.isna() & w22.isin([1, 2])
        cur.loc[m] = w22[m]

        # Original notebook comment normalized for the public code archive.
        m = cur.isna() & pre_have & (w21 == 1)
        cur.loc[m] = 1

        # Original notebook comment normalized for the public code archive.
        if i in {1, 5, 11}:
            m = cur.isna() & (da8 == 1)
            cur.loc[m] = 1

        out[str(i)] = cur.where(cur.isin([1,2]), np.nan)
    return out

# =============================================================================

df = read_dta(in_path)

# Original notebook comment normalized for the public code archive.
for key in ("householdID","communityID","ID"):
    if key not in df.columns and key.lower() in df.columns.str.lower():
        real = df.columns[df.columns.str.lower()==key.lower()][0]
        df = df.rename(columns={real:key})

# Original notebook comment normalized for the public code archive.
if "householdID" in df.columns:
    df["householdID"] = canon_id_fixed(df["householdID"], 9)
if "communityID" in df.columns:
    df["communityID"] = canon_id_fixed(df["communityID"], 7)
if "ID" in df.columns:
    df["ID"] = canon_id_fixed(df["ID"], 11)

# =============================================================================

# Original notebook comment normalized for the public code archive.
srh = first_nonnull(
    pick_scalar(df, ["ZDA001","DA001"]),
    pick_scalar(df, ["ZDA002","DA002"]),
    pick_scalar(df, ["ZDA079","DA079"]),
    pick_scalar(df, ["ZDA080","DA080"]),
)

# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
filled = synthesize_da007_filled_2015(df)          # dict: {"1":Series,...,"14":Series}
# Original notebook comment normalized for the public code archive.
zda = pick_group(df, ["ZDA007"])
da  = pick_group(df, ["DA007"])

all_keys = sorted(set(filled) | set(zda) | set(da), key=int)
d7_all = {}
for k in all_keys:
    s = first_nonnull(
        filled.get(k, pd.Series(np.nan, index=df.index)),
        zda.get(k,    pd.Series(np.nan, index=df.index)),
        da.get(k,     pd.Series(np.nan, index=df.index)),
    )
    d7_all[k] = s.where(s.isin([1,2]), np.nan)

arr = pd.DataFrame({f"d7_{k}": v for k,v in d7_all.items()})

# Original notebook comment normalized for the public code archive.
disease = pd.Series(np.nan, index=df.index, dtype="float64")
if not arr.empty:
    any1 = (arr == 1).any(axis=1)
    any_notna = arr.notna().any(axis=1)
    all2 = (arr.fillna(2) == 2).all(axis=1) & any_notna
    disease = pd.Series(np.where(any1, 1, np.where(all2, 2, np.nan)), index=df.index, dtype="float64")

# Original notebook comment normalized for the public code archive.
mental_neuro_psych = d7_all.get("11", pd.Series(np.nan, index=df.index)).astype("float64")
memory_disease     = d7_all.get("12", pd.Series(np.nan, index=df.index)).astype("float64")

# Original notebook comment normalized for the public code archive.
s56 = pick_group(df, ["ZDA056s","DA056s"])  # Original notebook comment normalized for the public code archive.
s57 = pick_group(df, ["ZDA057","DA057"])    # Original notebook comment normalized for the public code archive.
# =============================================================================
s56_1_11 = [s56[k] for k in sorted([x for x in s56.keys() if x.isdigit() and 1 <= int(x) <= 11], key=int)] if s56 else []
any_1_11 = (pd.concat(s56_1_11, axis=1).notna().any(axis=1) if s56_1_11 else pd.Series(False, index=df.index))
s12_candidates = []
for fam in ["ZDA056s12","DA056s12"]:
    s12_candidates += [df[c] for c in find_cols(df, rf"^{fam}(_\d+)?_?$")]
any_12_is_12 = (pd.concat([pd.to_numeric(s, errors="coerce") for s in s12_candidates], axis=1) == 12).any(axis=1) if s12_candidates else pd.Series(False, index=df.index)
social_activity = pd.Series(np.where(any_12_is_12, 2, np.where(any_1_11, 1, np.nan)), index=df.index, dtype="float64")
# Original notebook comment normalized for the public code archive.
s57_series = [s57[k] for k in sorted(s57.keys(), key=int)] if s57 else []
social_freq = (pd.concat([pd.to_numeric(s, errors="coerce") for s in s57_series], axis=1).min(axis=1) if s57_series else pd.Series(np.nan, index=df.index, dtype="float64"))
social_freq.loc[social_activity == 2] = 0

# Original notebook comment normalized for the public code archive.
db_map = {
    "DB001": ("run1km", "慢跑1km"),
    "DB002": ("walk1km", "步行1km"),
    "DB003": ("walk100m", "步行100m"),
    "DB004": ("sit_to_stand", "座位起立"),
    "DB005": ("stairs", "爬楼"),
    "DB006": ("bend_kneel_squat", "弯腰/跪/蹲"),
    "DB007": ("arm_raise", "上肢伸展"),
    "DB008": ("lift5kg", "提举5kg"),
    "DB009": ("pick_coin", "桌上拾硬币"),
    "DB010": ("dress", "穿衣"),
    "DB011": ("bathe", "洗澡"),
    "DB012": ("eat", "进食"),
    "DB013": ("bed_chair_transfer", "床椅转移"),
    "DB014": ("toilet", "如厕"),
    "DB015": ("incontinence", "大小便控制"),
    "DB016": ("housework", "做家务"),
}
db_new = {new: pick_scalar(df, [f"Z{old}", old]) for old,(new,_) in db_map.items()}

# =============================================================================
if "run1km" in db_new:
    m1 = (pd.to_numeric(db_new["run1km"], errors="coerce") == 1)
    for tgt in ("walk1km","walk100m"):
        db_new[tgt] = (db_new.get(tgt, pd.Series(np.nan, index=df.index))).copy()
        db_new[tgt].loc[m1] = 1
if "walk1km" in db_new and "walk100m" in db_new:
    m2 = (pd.to_numeric(db_new["walk1km"], errors="coerce") == 1)
    db_new["walk100m"] = db_new["walk100m"].copy(); db_new["walk100m"].loc[m2] = 1

# Original notebook comment normalized for the public code archive.
needed = ["run1km","walk100m","pick_coin","lift5kg","arm_raise","bend_kneel_squat","stairs"]
present_needed = [k for k in needed if k in db_new]
if present_needed:
    arr_db = pd.DataFrame({k: pd.to_numeric(db_new[k], errors="coerce") for k in present_needed})
    mask_all1 = (arr_db == 1).all(axis=1)
    for tgt in ["dress","bathe","eat","bed_chair_transfer","toilet","incontinence"]:
        if tgt in db_new:
            fill_mask = mask_all1 & db_new[tgt].isna()
            db_new[tgt] = db_new[tgt].copy(); db_new[tgt].loc[fill_mask] = 1

# Original notebook comment normalized for the public code archive.
APPLY_UNDER50_SKIP_IMPUTE_2015 = True
if APPLY_UNDER50_SKIP_IMPUTE_2015:
    birth_year = pick_scalar(df, ["ZBA002_1","BA002_1","ZBA002","BA002"])  # Original notebook comment normalized for the public code archive.
    under50 = pd.to_numeric(birth_year, errors="coerce") > 1965
    srh_good = pd.to_numeric(srh, errors="coerce").isin([1,2])
    def da_eq2(code):
        return (pd.to_numeric(pick_scalar(df, [f"Z{code}", code]), errors="coerce") == 2)
    conds = [da_eq2(x) for x in ["DA003","DA004","DA005","DA008"]]
    if not disease.isna().all():
        conds.append(pd.to_numeric(disease, errors="coerce") == 2)
    cond_all = conds[0]
    for c in conds[1:]:
        cond_all = cond_all & c
    mask_skip = under50 & srh_good & cond_all
    for k in db_new:
        db_new[k] = db_new[k].copy(); db_new[k].loc[mask_skip] = 1

# Original notebook comment normalized for the public code archive.
dc_map = {
    "DC011": ("depress", "抑郁"),
    "DC012": ("effort", "做事很费力"),
    "DC013": ("hope", "对未来有希望"),
    "DC014": ("fear", "害怕"),
    "DC015": ("sleep", "睡眠差"),
    "DC016": ("happy", "快乐"),
    "DC018": ("hopeless", "活不下去"),
    "DC028": ("life_satisfaction", "生活满意度"),
}
dc_new = {new: pick_scalar(df, [f"Z{old}", old]) for old,(new,_) in dc_map.items()}

# Original notebook comment normalized for the public code archive.
cd003_cols = sort_cols_by_suffix(find_cols(df, r"^cd003_(?:[1-9]|1[0-6])_?$"))
cd004_cols = sort_cols_by_suffix(find_cols(df, r"^cd004_(?:[1-9]|1[0-6])_?$"))
# Original notebook comment normalized for the public code archive.
if cd003_cols and cd004_cols:
    m3, m4 = suffix_map(cd003_cols), suffix_map(cd004_cols)
    for k in (set(m3) & set(m4)):
        c3, c4 = m3[k], m4[k]
        v3 = pd.to_numeric(df[c3], errors="coerce")
        mask_fill = df[c4].isna() & v3.isin([1,2,3])
        df.loc[mask_fill, c4] = v3.loc[mask_fill]
# Original notebook comment normalized for the public code archive.
meet_child = pd.Series(np.nan, index=df.index)
call_child = pd.Series(np.nan, index=df.index)
if cd003_cols:
    all_na_cd003 = df[cd003_cols].isna().all(axis=1)
    df.loc[all_na_cd003, cd003_cols] = 9
    meet_child = row_min(df, cd003_cols)
if cd004_cols:
    all_na_cd004 = df[cd004_cols].isna().all(axis=1)
    df.loc[all_na_cd004, cd004_cols] = 9
    call_child = row_min(df, cd004_cols)
meet_child = pd.to_numeric(meet_child, errors="coerce").fillna(9)
call_child = pd.to_numeric(call_child, errors="coerce").fillna(9)

# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
def collect_ce009_amount_cols(df):
    """Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    pat_amt = re.compile(r'^CE009_(?:1|2|3|4)(?:_(?:\d+))*_?$', re.IGNORECASE)
    pat_minmax_tail = re.compile(r'(?:__?(?:min|max))$', re.IGNORECASE)
    keep = []
    for c in df.columns:
        cl = str(c)
        if pat_amt.match(cl) and not pat_minmax_tail.search(cl):
            keep.append(c)
    return list(dict.fromkeys(keep))

ce009_cols = collect_ce009_amount_cols(df)

annual_transfer = pd.Series(np.nan, index=df.index, dtype="float64")
if ce009_cols:
    A = df[ce009_cols].apply(pd.to_numeric, errors="coerce")
    A = A.mask(A < 0)  # Original notebook comment normalized for the public code archive.
    any_observed = A.notna().any(axis=1)
    any_nonzero  = (A.fillna(0) > 0).any(axis=1)
    all_zero     = (A.fillna(0) == 0).all(axis=1) & any_observed

    annual_transfer.loc[any_nonzero] = 1.0
    annual_transfer.loc[all_zero]    = 2.0

# =============================================================================

prefix_pat = re.compile(r"^(da|db|dc|cd|ce)", flags=re.IGNORECASE)
measure_raw_cols = [c for c in df.columns if prefix_pat.match(c)]
id_cols_triplet = [c for c in ["ID","householdID","communityID"] if c in df.columns]
mask_elim = df[measure_raw_cols].isna().all(axis=1) if measure_raw_cols else pd.Series(False, index=df.index)
eliminated = df.loc[mask_elim, id_cols_triplet].copy()
kept_mask = ~mask_elim
print("[INFO] Notebook progress message.")
ensure_dir(out_dir)
if not eliminated.empty:
    eliminated.to_excel(out_elim, index=False)
    print("[INFO] Notebook progress message.")

# =============================================================================

cols_keys = {
    "ID": df["ID"] if "ID" in df.columns else np.nan,
    "householdID": df["householdID"] if "householdID" in df.columns else np.nan,
    "communityID": df["communityID"] if "communityID" in df.columns else np.nan,
}

res = pd.DataFrame({
    **cols_keys,
    "srh": srh,
    "disease": disease,
    "mental_neuro_psych": mental_neuro_psych,
    "memory_disease": memory_disease,
    "social_activity": social_activity,
    "social_freq": social_freq,
    "meet_child_freq": meet_child,
    "call_child_freq": call_child,
    "annual_transfer": annual_transfer,
}, index=df.index)

# Original notebook comment normalized for the public code archive.
for k,v in db_new.items():
    res[k] = v
for k,v in dc_new.items():
    res[k] = v

# Original notebook comment normalized for the public code archive.
res = res.loc[kept_mask].reset_index(drop=True)

# Original notebook comment normalized for the public code archive.
var_labels = {
    "ID": "ID",
    "householdID": "householdID",
    "communityID": "communityID",
    "srh": "自评健康",
    "disease": "疾病（当期口径优先，含W2/DA008）",
    "mental_neuro_psych": "情绪/神经/精神问题",
    "memory_disease": "记忆相关疾病",
    "social_activity": "社交活动",
    "social_freq": "社交频率",
    "meet_child_freq": "与子女见面频率",
    "call_child_freq": "与子女通讯频率",
    "annual_transfer": "年度转移（金额>0；全缺失=NA）",
}
for old,(new,label) in db_map.items():
    var_labels[new] = label
for old,(new,label) in dc_map.items():
    var_labels[new] = label

# Original notebook comment normalized for the public code archive.
ensure_dir(out_dir)
write_stata_safely(res, out_dta, var_labels=var_labels)
cn_cols = {c: var_labels.get(c, c) for c in res.columns}
for k in ("ID","householdID","communityID"):
    cn_cols[k] = k
res.rename(columns=cn_cols).to_excel(out_xlsx, index=False)
print("[INFO] Notebook progress message.")
print("[INFO] Notebook progress message.")

# =============================================================================
def miss_rate(s):
    return f"{int(s.isna().sum()):,}（{100*s.isna().mean():.2f}%）"
print("[INFO] Notebook progress message.")
print("[INFO] Notebook progress message.", miss_rate(res["disease"]))
print("[INFO] Notebook progress message.", miss_rate(res["mental_neuro_psych"]))
print("[INFO] Notebook progress message.", miss_rate(res["memory_disease"]))


# ------------------------------------------------------------------------------
# Notebook cell 11
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from pathlib import Path

# =============================================================================
# Excel output note.
path = r"E:\impact_assessment_child_order\older\health\2015\2015_health_result.xlsx"
df = pd.read_excel(path, dtype=object)   # Original notebook comment normalized for the public code archive.



# =============================================================================
df = df.replace(r"^\s*$", np.nan, regex=True)

# =============================================================================
n = len(df)
na_count = df.isna().sum()
na_pct = (na_count / n * 100).round(2)

summary = (
    pd.DataFrame({"n_missing": na_count, "missing_pct": na_pct})
      .sort_values("n_missing", ascending=False)
)

# Original notebook comment normalized for the public code archive.
print(summary.head(20))

# Original notebook comment normalized for the public code archive.
out = Path(path).with_name(Path(path).stem + "_missing_summary.xlsx")
summary.to_excel(out, index=True)
print("[INFO] Notebook progress message.")




# =============================================================================
# Source notebook
# =============================================================================
# record_type : wave_step
# year        : 2018
# step        : 2
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 10
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import re
from pathlib import Path
import numpy as np
import pandas as pd

# =============================================================================
in_path  = r"E:\impact_assessment_child_order\older\health\2018\health.dta"
out_dir  = r"E:\impact_assessment_child_order\older\health\2018"
out_dta  = fr"{out_dir}\2018_health_result.dta"
out_xlsx = fr"{out_dir}\2018_health_result.xlsx"
out_elim = fr"{out_dir}\eliminate.xlsx"

# =============================================================================

def read_dta(path):
    df = pd.read_stata(path, convert_categoricals=False)
    print("[INFO] Notebook progress message.")
    return df

def ensure_dir(p):
    Path(p).mkdir(parents=True, exist_ok=True)

def find_cols(df, pattern):
    """Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if isinstance(pattern, str):
        pattern = re.compile(pattern, flags=re.IGNORECASE)
    return [c for c in df.columns if pattern.match(c)]

def sort_cols_by_suffix(cols, prefix_regex=r"^(.+?)_?(\d+)_?$"):
    """Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    def key(c):
        m = re.match(prefix_regex, c, flags=re.IGNORECASE)
        return (int(m.group(2)) if m else 10**9)
    return sorted(cols, key=key)

def suffix_map(cols):
    """Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    m = {}
    for c in cols:
        mt = re.search(r"_(\d+)_?$", c, flags=re.I)
        if mt:
            m[mt.group(1)] = c
    return m

def first_nonnull(*series):
    """Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    out = None
    for s in series:
        if s is None:
            continue
        s = pd.to_numeric(s, errors="coerce")
        out = s if out is None else out.combine_first(s)
    if out is None:
        n = None
        for s in series:
            if isinstance(s, pd.Series):
                n = s.index
                break
        out = pd.Series(np.nan, index=(n if n is not None else []))
    return out

def row_min(df, cols):
    if not cols:
        return pd.Series(np.nan, index=df.index)
    arr = df[cols].apply(pd.to_numeric, errors="coerce")
    return arr.min(axis=1)

def ensure_varname_len32(df):
    cols = list(df.columns); new, used = [], set()
    for c in cols:
        base = str(c)[:32]
        name = base; i = 1
        while name in used:
            suf = f"_{i}"
            name = base[:32-len(suf)] + suf
            i += 1
        new.append(name); used.add(name)
    if new != cols:
        df = df.rename(columns=dict(zip(cols, new)))
        print("[INFO] Notebook progress message.")
    return df

def write_stata_safely(df, out_path, var_labels=None):
    df = ensure_varname_len32(df)
    ensure_dir(Path(out_path).parent)
    try:
        import pyreadstat
        vlabels = {k: var_labels.get(k, "") for k in df.columns} if var_labels else None
        last_err = None
        for ver in (118, 117, 114):
            try:
                pyreadstat.write_dta(df, out_path, version=ver, variable_labels=vlabels)
                print("[INFO] Notebook progress message.")
                return
            except Exception as e:
                last_err = e
        print("[INFO] Notebook progress message.")
    except Exception as e:
        print("[INFO] Notebook progress message.", e)
    # Original notebook comment normalized for the public code archive.
    def to_latin1(d):
        d = d.copy()
        for c in d.select_dtypes(include=["object","string"]).columns:
            s = d[c].astype(object)
            mask = pd.isna(s)
            s = s.astype(str).str.encode("latin-1", errors="ignore").str.decode("latin-1")
            s[mask] = None
            d[c] = s
        return d
    df2 = to_latin1(df)
    df2.to_stata(out_path, write_index=False, version=117)
    print("[INFO] Notebook progress message.")

def _clean_to_str(s: pd.Series) -> pd.Series:
    s = pd.Series(s, dtype="object")
    m = s.isna()
    sc = s[~m].astype(str).str.strip()
    sc = sc.str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = sc; s.loc[m] = np.nan
    return s

def canon_id_fixed(s: pd.Series, width: int) -> pd.Series:
    s = _clean_to_str(s)
    m = s.notna()
    s.loc[m] = s.loc[m].astype(str).str.zfill(width)
    return s

# Original notebook comment normalized for the public code archive.

def pick_scalar(df, families):
    """Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    series_list = []
    for fam in families:
        cols = [c for c in df.columns if re.match(rf"^{fam}_?$", c, flags=re.I)]
        if cols:
            series_list.append(pd.to_numeric(df[cols[0]], errors="coerce"))
    if not series_list:
        return pd.Series(np.nan, index=df.index)
    out = series_list[0]
    for s in series_list[1:]:
        out = out.combine_first(s)
    return out

def pick_group(df, families):
    """Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    suf_set = set()
    for fam in families:
        for c in df.columns:
            m = re.match(rf"^{fam}_?(\d+)_?$", c, flags=re.I)
            if m:
                suf_set.add(m.group(1))
    out = {}
    for s in sorted(suf_set, key=lambda x: int(x)):
        series_list = []
        for fam in families:
            cand = [c for c in df.columns if re.match(rf"^{fam}_?{s}_?$", c, flags=re.I)]
            if cand:
                series_list.append(pd.to_numeric(df[cand[0]], errors="coerce"))
        if not series_list:
            out[s] = pd.Series(np.nan, index=df.index)
        else:
            cur = series_list[0]
            for ss in series_list[1:]:
                cur = cur.combine_first(ss)
            out[s] = cur
    return out

# =============================================================================

df = read_dta(in_path)

# Original notebook comment normalized for the public code archive.
for key in ("householdID","communityID","ID"):
    if key not in df.columns and key.lower() in df.columns.str.lower():
        real = df.columns[df.columns.str.lower()==key.lower()][0]
        df = df.rename(columns={real:key})

# Original notebook comment normalized for the public code archive.
if "householdID" in df.columns:
    df["householdID"] = canon_id_fixed(df["householdID"], 9)
if "communityID" in df.columns:
    df["communityID"] = canon_id_fixed(df["communityID"], 7)
if "ID" in df.columns:
    df["ID"] = canon_id_fixed(df["ID"], 11)

# =============================================================================

# Original notebook comment normalized for the public code archive.
srh = first_nonnull(
    pick_scalar(df, ["ZDA001","DA001"]),
    pick_scalar(df, ["ZDA002","DA002"]),
    pick_scalar(df, ["ZDA079","DA079"]),
    pick_scalar(df, ["ZDA080","DA080"]),
)

# Original notebook comment normalized for the public code archive.
filled = pick_group(df, ["DA007_FILLED","da007_filled"])  # Original notebook comment normalized for the public code archive.
if filled:
    arr = pd.concat([v.rename(f"f_{k}") for k,v in filled.items()], axis=1)
else:
    d7 = pick_group(df, ["ZDA007","DA007"])
    arr = pd.concat([v.rename(f"d7_{k}") for k,v in d7.items()], axis=1) if d7 else pd.DataFrame(index=df.index)

disease = pd.Series(np.nan, index=df.index, dtype="float64")
if not arr.empty:
    any1 = (arr == 1).any(axis=1)
    any_notna = arr.notna().any(axis=1)
    all2 = (arr.fillna(2) == 2).all(axis=1) & any_notna
    disease = pd.Series(np.where(any1, 1, np.where(all2, 2, np.nan)), index=df.index, dtype="float64")

# Original notebook comment normalized for the public code archive.
d7_for_pick = filled if filled else (pick_group(df, ["ZDA007","DA007"]) if 'd7' not in locals() else d7)

def _only_12_from_group(d7_dict, k):
    s = pd.to_numeric(d7_dict.get(str(k), pd.Series(np.nan, index=df.index)), errors="coerce") if d7_dict else pd.Series(np.nan, index=df.index)
    return s.where(s.isin([1,2]), np.nan)

mental_neuro_psych = _only_12_from_group(d7_for_pick, 11)
memory_disease     = _only_12_from_group(d7_for_pick, 12)

# =============================================================================
# Original notebook comment normalized for the public code archive.
act_cols = []
for pat in [r"^da056s(?:[1-9]|1[0-1])_?$", r"^da056_s(?:[1-9]|1[0-1])_?$"]:
    act_cols += find_cols(df, pat)
act_cols = sort_cols_by_suffix(list(dict.fromkeys(act_cols)), r"^(da056(?:_s|s))_?(\d+)_?$")

none_cols = []
for pat in [r"^da056s12_?$", r"^da056_s12_?$"]:
    none_cols += find_cols(df, pat)
none_cols = list(dict.fromkeys(none_cols))

freq_cols = []
for pat in [r"^da057_(?:[1-9]|10|11)_?$", r"^da057_s(?:[1-9]|1[0-1])_?$"]:
    freq_cols += find_cols(df, pat)
freq_cols = sort_cols_by_suffix(list(dict.fromkeys(freq_cols)), r"^(da057(?:_s|))_?(\d+)_?$")

def picked_matrix(df, cols):
    if not cols: return None
    M = df[cols].apply(pd.to_numeric, errors="coerce")
    return (M > 0) | (M == 1)    # Original notebook comment normalized for the public code archive.

picked_any  = picked_matrix(df, act_cols)
picked_none = picked_matrix(df, none_cols)

social_activity = pd.Series(np.nan, index=df.index, dtype="float64")
if picked_none is not None:
    social_activity[picked_none.any(axis=1)] = 2.0
if picked_any is not None:
    mask_yes = picked_any.any(axis=1) & ~(picked_none.any(axis=1) if picked_none is not None else False)
    social_activity[mask_yes] = 1.0

social_freq = pd.Series(np.nan, index=df.index, dtype="float64")
if freq_cols:
    F = df[freq_cols].apply(pd.to_numeric, errors="coerce")
    social_freq = F.min(axis=1)     # Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
social_freq.loc[social_activity == 2] = 0

# Original notebook comment normalized for the public code archive.
db_map = {
    "DB001": ("run1km", "慢跑1km"),
    "DB002": ("walk1km", "步行1km"),
    "DB003": ("walk100m", "步行100m"),
    "DB004": ("sit_to_stand", "座位起立"),
    "DB005": ("stairs", "爬楼"),
    "DB006": ("bend_kneel_squat", "弯腰/跪/蹲"),
    "DB007": ("arm_raise", "上肢伸展"),
    "DB008": ("lift5kg", "提举5kg"),
    "DB009": ("pick_coin", "桌上拾硬币"),
    "DB010": ("dress", "穿衣"),
    "DB011": ("bathe", "洗澡"),
    "DB012": ("eat", "进食"),
    "DB013": ("bed_chair_transfer", "床椅转移"),
    "DB014": ("toilet", "如厕"),
    "DB015": ("incontinence", "大小便控制"),
    "DB016": ("housework", "做家务"),
}
db_new = {new: pick_scalar(df, [f"Z{old}", old]) for old,(new,_) in db_map.items()}

# =============================================================================
if "run1km" in db_new:
    m1 = (pd.to_numeric(db_new["run1km"], errors="coerce") == 1)
    for tgt in ("walk1km","walk100m"):
        db_new[tgt] = db_new.get(tgt, pd.Series(np.nan, index=df.index)).copy()
        db_new[tgt].loc[m1] = 1
if "walk1km" in db_new and "walk100m" in db_new:
    m2 = (pd.to_numeric(db_new["walk1km"], errors="coerce") == 1)
    db_new["walk100m"] = db_new["walk100m"].copy(); db_new["walk100m"].loc[m2] = 1

# Original notebook comment normalized for the public code archive.
needed = ["run1km","walk100m","pick_coin","lift5kg","arm_raise","bend_kneel_squat","stairs"]
present_needed = [k for k in needed if k in db_new]
if present_needed:
    arr = pd.DataFrame({k: pd.to_numeric(db_new[k], errors="coerce") for k in present_needed})
    mask_all1 = (arr == 1).all(axis=1)
    for tgt in ["dress","bathe","eat","bed_chair_transfer","toilet","incontinence"]:
        if tgt in db_new:
            fill_mask = mask_all1 & db_new[tgt].isna()
            db_new[tgt] = db_new[tgt].copy(); db_new[tgt].loc[fill_mask] = 1

# Original notebook comment normalized for the public code archive.
dc_map = {
    "DC011": ("depress", "抑郁"),
    "DC012": ("effort", "做事很费力"),
    "DC013": ("hope", "对未来有希望"),
    "DC014": ("fear", "害怕"),
    "DC015": ("sleep", "睡眠差"),
    "DC016": ("happy", "快乐"),
    "DC018": ("hopeless", "活不下去"),
    "DC028": ("life_satisfaction", "生活满意度"),
}
dc_new = {new: pick_scalar(df, [f"Z{old}", old]) for old,(new,_) in dc_map.items()}

# Original notebook comment normalized for the public code archive.
cd003_cols = sort_cols_by_suffix(find_cols(df, r"^cd003_(?:[1-9]|1[0-5])_?$"))
cd004_cols = sort_cols_by_suffix(find_cols(df, r"^cd004_(?:[1-9]|1[0-5])_?$"))

# Original notebook comment normalized for the public code archive.
if cd003_cols and cd004_cols:
    m3, m4 = suffix_map(cd003_cols), suffix_map(cd004_cols)
    for k in (set(m3) & set(m4)):
        c3, c4 = m3[k], m4[k]
        v3 = pd.to_numeric(df[c3], errors="coerce")
        mask_fill = df[c4].isna() & v3.isin([1,2,3])
        df.loc[mask_fill, c4] = v3.loc[mask_fill]

# Original notebook comment normalized for the public code archive.
meet_child = pd.Series(np.nan, index=df.index)
call_child = pd.Series(np.nan, index=df.index)
if cd003_cols:
    all_na_cd003 = df[cd003_cols].isna().all(axis=1)
    df.loc[all_na_cd003, cd003_cols] = 9
    meet_child = row_min(df, cd003_cols)
if cd004_cols:
    all_na_cd004 = df[cd004_cols].isna().all(axis=1)
    df.loc[all_na_cd004, cd004_cols] = 9
    call_child = row_min(df, cd004_cols)
meet_child = pd.to_numeric(meet_child, errors="coerce").fillna(9)
call_child = pd.to_numeric(call_child, errors="coerce").fillna(9)

# Original notebook comment normalized for the public code archive.
def collect_ce009_amount_cols(df):
    """Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    pat_amt = re.compile(r'^ce009_(?:1|2|3|4)(?:_(?:\d+))*_?$', re.IGNORECASE)
    keep = []
    for c in df.columns:
        cl = c.lower()
        if ('__min' in cl) or ('__max' in cl) or cl.endswith('_min') or cl.endswith('_max'):
            continue
        if pat_amt.match(cl):
            keep.append(c)
    return list(dict.fromkeys(keep))

def collect_ce009_bracket_cols(df):
    """Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    pat_br = re.compile(r'^ce009_(?:1|2|3|4)(?:_(?:\d+))+__(?:min|max)$', re.IGNORECASE)
    alt_br = re.compile(r'^ce009_(?:1|2|3|4)(?:_(?:\d+))*_(?:min|max)$', re.IGNORECASE)
    keep = []
    for c in df.columns:
        cl = c.lower()
        if pat_br.match(cl) or alt_br.match(cl):
            keep.append(c)
    return list(dict.fromkeys(keep))

def has_child_to_parent_transfer(df, use_bracket_as_evidence=True):
    """Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    amt_cols = collect_ce009_amount_cols(df)
    A = df[amt_cols].apply(pd.to_numeric, errors="coerce") if amt_cols else pd.DataFrame(index=df.index)
    A = A.mask(A < 0)  # Original notebook comment normalized for the public code archive.

    any_nonzero = (A > 0).any(axis=1) if not A.empty else pd.Series(False, index=df.index)
    any_observed = A.notna().any(axis=1) if not A.empty else pd.Series(False, index=df.index)

    if use_bracket_as_evidence:
        br_cols = collect_ce009_bracket_cols(df)
        if br_cols:
            B = df[br_cols].apply(pd.to_numeric, errors="coerce").mask(lambda x: x < 0)
            any_nonzero = any_nonzero | (B > 0).any(axis=1)
            any_observed = any_observed | B.notna().any(axis=1)

    out = pd.Series(np.nan, index=df.index, dtype="float64")
    out.loc[any_nonzero] = 1.0
    out.loc[~any_nonzero & any_observed] = 2.0
    return out

child_to_parent_transfer = has_child_to_parent_transfer(df, use_bracket_as_evidence=True)

# =============================================================================
prefix_pat = re.compile(r"^(da|db|dc|cd|ce)", flags=re.IGNORECASE)
measure_raw_cols = [c for c in df.columns if prefix_pat.match(c)]
id_cols_triplet = [c for c in ["ID","householdID","communityID"] if c in df.columns]
mask_elim = df[measure_raw_cols].isna().all(axis=1) if measure_raw_cols else pd.Series(False, index=df.index)
eliminated = df.loc[mask_elim, id_cols_triplet].copy()
kept_mask = ~mask_elim
print("[INFO] Notebook progress message.")
ensure_dir(out_dir)
if not eliminated.empty:
    eliminated.to_excel(out_elim, index=False)
    print("[INFO] Notebook progress message.")

# =============================================================================

cols_keys = {
    "ID": df["ID"] if "ID" in df.columns else np.nan,
    "householdID": df["householdID"] if "householdID" in df.columns else np.nan,
    "communityID": df["communityID"] if "communityID" in df.columns else np.nan,
}

res = pd.DataFrame({
    **cols_keys,
    "srh": srh,
    "disease": disease,
    "mental_neuro_psych": mental_neuro_psych,
    "memory_disease": memory_disease,
    "social_activity": social_activity,
    "social_freq": social_freq,
    "meet_child_freq": meet_child,
    "call_child_freq": call_child,
    "child_to_parent_transfer": child_to_parent_transfer,  # Original notebook comment normalized for the public code archive.
}, index=df.index)

# Original notebook comment normalized for the public code archive.
for k, v in db_new.items():
    res[k] = v
for k, v in dc_new.items():
    res[k] = v

# Original notebook comment normalized for the public code archive.
res = res.loc[kept_mask].reset_index(drop=True)

# Original notebook comment normalized for the public code archive.
var_labels = {
    "ID": "ID",
    "householdID": "householdID",
    "communityID": "communityID",
    "srh": "自评健康",
    "disease": "疾病（当期口径优先）",
    "mental_neuro_psych": "情绪/神经/精神问题",
    "memory_disease": "记忆相关疾病",
    "social_activity": "社交活动",
    "social_freq": "社交频率",
    "meet_child_freq": "与子女见面频率（1高-10低，9=缺失兜底）",
    "call_child_freq": "与子女通讯频率（1高-10低，9=缺失兜底）",
    "child_to_parent_transfer": "子女→父母年度转移（CE009；金额>0；全缺失=NA）",
}
# Original notebook comment normalized for the public code archive.
for old,(new,label) in db_map.items():
    var_labels[new] = label
for old,(new,label) in dc_map.items():
    var_labels[new] = label

# Original notebook comment normalized for the public code archive.
ensure_dir(out_dir)
write_stata_safely(res, out_dta, var_labels=var_labels)

# Excel output note.
cn_cols = {c: var_labels.get(c, c) for c in res.columns}
for k in ("ID","householdID","communityID"):
    cn_cols[k] = k
res.rename(columns=cn_cols).to_excel(out_xlsx, index=False)
print("[INFO] Notebook progress message.")
print("[INFO] Notebook progress message.")


# ------------------------------------------------------------------------------
# Notebook cell 11
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from pathlib import Path

# =============================================================================
# Excel output note.
path = r"E:\impact_assessment_child_order\older\health\2018\2018_health_result.xlsx"
df = pd.read_excel(path, dtype=object)   # Original notebook comment normalized for the public code archive.



# =============================================================================
df = df.replace(r"^\s*$", np.nan, regex=True)

# =============================================================================
n = len(df)
na_count = df.isna().sum()
na_pct = (na_count / n * 100).round(2)

summary = (
    pd.DataFrame({"n_missing": na_count, "missing_pct": na_pct})
      .sort_values("n_missing", ascending=False)
)

# Original notebook comment normalized for the public code archive.
print(summary.head(20))

# Original notebook comment normalized for the public code archive.
out = Path(path).with_name(Path(path).stem + "_missing_summary.xlsx")
summary.to_excel(out, index=True)
print("[INFO] Notebook progress message.")




# =============================================================================
# Source notebook
# =============================================================================
# record_type : wave_step
# year        : 2020
# step        : 2
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 4
# ------------------------------------------------------------------------------
# Notebook-export prose note omitted from the public code archive.


# ------------------------------------------------------------------------------
# Notebook cell 11
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import re
from pathlib import Path
import numpy as np
import pandas as pd

# =============================================================================
base_in = r"E:\project_flood_impact_assessment\老年人健康\CHARLS\charls原版数据\原始数据+问卷2011~2020\2020\CHARLS2020r"
f_d  = fr"{base_in}\Health_Status_and_Functioning.dta"
f_ci = fr"{base_in}\Family_Information.dta"   # CA015/CA016/CA017

base_out = r"E:\impact_assessment_child_order\older\health\2020"
out_dta  = fr"{base_out}\2020_health_result.dta"
out_xlsx = fr"{base_out}\2020_health_result.xlsx"
out_elim = fr"{base_out}\eliminate.xlsx"  # Original notebook comment normalized for the public code archive.

# =============================================================================
def read_dta(path):
    df = pd.read_stata(path, convert_categoricals=False)
    print("[INFO] Notebook progress message.")
    return df

def ensure_dir(p): Path(p).mkdir(parents=True, exist_ok=True)

def find_cols(df, pattern):
    if isinstance(pattern, str):
        pattern = re.compile(pattern, flags=re.IGNORECASE)
    return [c for c in df.columns if pattern.match(c)]

def sort_cols_by_suffix(cols, prefix_regex=r"^(.+?)_?(\d+)_?$"):
    def key(c):
        m = re.match(prefix_regex, c, flags=re.IGNORECASE)
        return (int(m.group(2)) if m else 10**9)
    return sorted(cols, key=key)

def suffix_map(cols):
    m = {}
    for c in cols:
        mt = re.search(r"_(\d+)_?$", c, flags=re.I)
        if mt: m[mt.group(1)] = c
    return m

def first_nonnull(*series):
    out = None
    for s in series:
        if s is None: continue
        s = pd.to_numeric(s, errors="coerce")
        out = s if out is None else out.combine_first(s)
    return out

def row_any_eq(df, cols, val):
    if not cols: return pd.Series(False, index=df.index)
    arr = df[cols].apply(pd.to_numeric, errors="coerce")
    return (arr == val).any(axis=1)

def row_all_eq(df, cols, val):
    if not cols: return pd.Series(False, index=df.index)
    arr = df[cols].apply(pd.to_numeric, errors="coerce")
    any_notna = arr.notna().any(axis=1)
    all_val   = (arr.replace(np.nan, val) == val).all(axis=1)
    return any_notna & all_val

def row_min(df, cols):
    if not cols:
        return pd.Series(np.nan, index=df.index, dtype="float64")
    arr = df[cols].apply(pd.to_numeric, errors="coerce")
    return arr.min(axis=1)

def ensure_varname_len32(df):
    cols = list(df.columns); new, used = [], set()
    for c in cols:
        base = str(c)[:32]; name = base; i = 1
        while name in used:
            suf = f"_{i}"; name = base[:32-len(suf)] + suf; i += 1
        new.append(name); used.add(name)
    if new != cols:
        df = df.rename(columns=dict(zip(cols,new)))
        print("[INFO] Notebook progress message.")
    return df

def coerce_to_latin1(df, how="ignore"):
    d = df.copy()
    for c in d.select_dtypes(include=["object","string"]).columns:
        s = d[c].astype(object); m = pd.isna(s)
        s = s.astype(str).str.encode("latin-1", errors=how).str.decode("latin-1")
        s[m] = None; d[c] = s
    return d

def sanitize_for_stata(d):
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

def write_stata_safely(df, out_path, var_labels=None):
    df = ensure_varname_len32(df)
    ensure_dir(Path(out_path).parent)
    try:
        import pyreadstat
        vlabels = {k: var_labels.get(k, "") for k in df.columns} if var_labels else None
        last_err = None
        for ver in (118, 117, 114):
            try:
                pyreadstat.write_dta(df, out_path, version=ver, variable_labels=vlabels)
                print("[INFO] Notebook progress message.")
                return
            except Exception as e:
                last_err = e
        print("[INFO] Notebook progress message.")
    except Exception as e:
        print("[INFO] Notebook progress message.", e)
    df2 = coerce_to_latin1(df, how="ignore")
    df2.to_stata(out_path, write_index=False, version=117)
    print("[INFO] Notebook progress message.")

def _clean_to_str(s: pd.Series) -> pd.Series:
    s = pd.Series(s, dtype="object"); m = s.isna()
    sc = s[~m].astype(str).str.strip()
    sc = sc.str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = sc; s.loc[m] = np.nan
    return s

def canon_id_fixed(s: pd.Series, width: int) -> pd.Series:
    s = _clean_to_str(s); m = s.notna()
    s.loc[m] = s.loc[m].astype(str).str.zfill(width); return s

def standardize_keys(df, keys=("ID","householdID","communityID")):
    lower_map = {c.lower(): c for c in df.columns}
    if "id" not in lower_map and "pid" in lower_map:
        df = df.rename(columns={lower_map["pid"]: "ID"}); lower_map["id"] = "ID"
    ren = {}
    for k in keys:
        if k.lower() in lower_map and lower_map[k.lower()] != k:
            ren[lower_map[k.lower()]] = k
    if ren: df = df.rename(columns=ren)
    if "ID" in df.columns: df["ID"] = canon_id_fixed(df["ID"], 11)
    if "householdID" in df.columns: df["householdID"] = canon_id_fixed(df["householdID"], 9)
    if "communityID" in df.columns: df["communityID"] = canon_id_fixed(df["communityID"], 7)
    return df

# =============================================================================
d_df  = standardize_keys(read_dta(f_d))
ci_df = standardize_keys(read_dta(f_ci))

# =============================================================================
df = d_df

# Original notebook comment normalized for the public code archive.
srh_cols = find_cols(df, r"^da001(?:_\d+)?_?$")
srh = row_min(df, srh_cols) if srh_cols else pd.Series(np.nan, index=df.index, dtype="float64")
srh = pd.to_numeric(srh, errors="coerce")

# Original notebook comment normalized for the public code archive.
d3_cols = sort_cols_by_suffix(find_cols(df, r"^da003_(?:\d+)_?$"), r"^(da003)_?(\d+)_?$")
if d3_cols:
    disease = pd.Series(
        np.where(row_any_eq(df, d3_cols, 1), 1,
                 np.where(row_all_eq(df, d3_cols, 2), 2, np.nan)),
        index=df.index, dtype="float64"
    )
else:
    disease = pd.Series(np.nan, index=df.index, dtype="float64")

# Original notebook comment normalized for the public code archive.
act_cols = sort_cols_by_suffix(find_cols(df, r"^da038(?:_s)?(?:[1-9])_?$"),
                               r"^(da038(?:_s)?)?(\d+)_?$")
A = df[act_cols].apply(pd.to_numeric, errors="coerce") if act_cols else pd.DataFrame(index=df.index)
has_none = (A.filter(regex=r"^da038(?:_s)?9_?$") == 9).any(axis=1) if not A.empty else pd.Series(False, index=df.index)
has_any  = (A.filter(regex=r"^da038(?:_s)?[1-8]_?$") > 0).any(axis=1) if not A.empty else pd.Series(False, index=df.index)
social_activity = pd.Series(np.where(has_none, 2, np.where(has_any, 1, np.nan)),
                            index=df.index, dtype="float64")

freq_cols = sort_cols_by_suffix(find_cols(df, r"^da039_(?:[1-8])_?$"))
social_freq = row_min(df, freq_cols) if freq_cols else pd.Series(np.nan, index=df.index, dtype="float64")
social_freq = pd.to_numeric(social_freq, errors="coerce")
social_freq.loc[social_activity == 2] = 0

# Original notebook comment normalized for the public code archive.
db_new = {}
def _take(var):  # Original notebook comment normalized for the public code archive.
    cols = find_cols(df, rf"^{var}_?$")
    return (pd.to_numeric(df[cols[0]], errors="coerce") if cols else None)

# Original notebook comment normalized for the public code archive.
m_2020 = {
    "db001": ("dress",              "穿衣"),
    "db003": ("bathe",              "洗澡"),            # Original notebook comment normalized for the public code archive.
    "db005": ("eat",                "进食"),
    "db007": ("bed_chair_transfer", "床椅转移"),
    # Original notebook comment normalized for the public code archive.
    "db009": ("bend_kneel_squat",   "如厕（替代弯腰/跪/蹲）"),
    "db011": ("incontinence",       "大小便控制"),
}
for old,(new,_) in m_2020.items():
    s = _take(old)
    if s is not None: db_new[new] = s

# Original notebook comment normalized for the public code archive.
if "bathe" not in db_new:
    s_bathe_help = _take("db004")
    if s_bathe_help is not None: db_new["bathe"] = s_bathe_help

# Original notebook comment normalized for the public code archive.
for cand in ("db016","db012"):
    s_hw = _take(cand)
    if s_hw is not None:
        db_new["housework"] = s_hw
        break

# Original notebook comment normalized for the public code archive.
dc_map = {
    "dc018": ("depress", "抑郁"),
    "dc019": ("effort", "做事很费力"),
    "dc020": ("hope", "对未来有希望"),
    "dc021": ("fear", "害怕"),
    "dc022": ("sleep", "睡眠差"),
    "dc023": ("happy", "快乐"),
    "dc025": ("hopeless", "活不下去"),
    "dc026": ("life_satisfaction", "生活满意度"),
}
dc_new = {}
for old,(new,_) in dc_map.items():
    cols = find_cols(df, rf"^{old}_?$")
    if cols: dc_new[new] = pd.to_numeric(df[cols[0]], errors="coerce")

# =============================================================================
ci = ci_df.copy()

meet_cols = sort_cols_by_suffix(find_cols(ci, r"^ca015_(?:\d+)_?$"))
if meet_cols:
    all_na_meet = ci[meet_cols].isna().all(axis=1)
    if all_na_meet.any(): ci.loc[all_na_meet, meet_cols] = 9
    meet_child = row_min(ci, meet_cols)
else:
    meet_child = pd.Series(np.nan, index=ci.index, dtype="float64")
meet_child = pd.to_numeric(meet_child, errors="coerce").fillna(9)

call_cols = sort_cols_by_suffix(find_cols(ci, r"^ca016_(?:\d+)_?$"))
if meet_cols and call_cols:
    m3, m4 = suffix_map(meet_cols), suffix_map(call_cols)
    for k in (set(m3) & set(m4)):
        c3, c4 = m3[k], m4[k]
        v3 = pd.to_numeric(ci[c3], errors="coerce")
        mask_fill = ci[c4].isna() & v3.isin([1,2,3])
        ci.loc[mask_fill, c4] = v3.loc[mask_fill]
if call_cols:
    all_na_call = ci[call_cols].isna().all(axis=1)
    if all_na_call.any(): ci.loc[all_na_call, call_cols] = 9
    call_child = row_min(ci, call_cols)
else:
    call_child = pd.Series(np.nan, index=ci.index, dtype="float64")
call_child = pd.to_numeric(call_child, errors="coerce").fillna(9)

trans_cols = [c for c in ci.columns if re.match(r"^ca017_", c, flags=re.IGNORECASE)]
if trans_cols:
    A = ci[trans_cols].apply(pd.to_numeric, errors="coerce").mask(lambda x: x < 0)
    any_observed = A.notna().any(axis=1)
    any_pos      = (A.fillna(0) > 0).any(axis=1)
    all_zero     = (A.fillna(0) == 0).all(axis=1) & any_observed
    annual_transfer = pd.Series(np.nan, index=ci.index, dtype="float64")
    annual_transfer.loc[any_pos]  = 1.0
    annual_transfer.loc[all_zero] = 2.0
else:
    annual_transfer = pd.Series(np.nan, index=ci.index, dtype="float64")

# =============================================================================
res_d = pd.DataFrame({
    "ID": d_df["ID"] if "ID" in d_df.columns else np.nan,
    "householdID": d_df["householdID"] if "householdID" in d_df.columns else np.nan,
    "communityID": d_df["communityID"] if "communityID" in d_df.columns else np.nan,
    "srh": srh,
    "disease": disease,
    "social_activity": social_activity,
    "social_freq": social_freq,
}, index=d_df.index)
for k,v in db_new.items(): res_d[k] = v
for k,v in dc_new.items(): res_d[k] = v

res_ci = pd.DataFrame({
    "householdID": ci_df["householdID"] if "householdID" in ci_df.columns else np.nan,
    "communityID": ci_df["communityID"] if "communityID" in ci_df.columns else np.nan,
    "meet_child_freq": meet_child,
    "call_child_freq": call_child,
    "annual_transfer": annual_transfer,
}, index=ci_df.index)

def dedup_on_keys(df, keys):
    before = len(df)
    df2 = df.drop_duplicates(subset=[k for k in keys if k in df.columns], keep="first")
    if len(df2) < before:
        print("[INFO] Notebook progress message.")
    return df2

keys_hh = ["householdID","communityID"]
res_d  = dedup_on_keys(res_d,  ["householdID","communityID","ID"])
res_ci = dedup_on_keys(res_ci, keys_hh)

health = res_d.merge(res_ci, on=keys_hh, how="left", suffixes=("", "_ci"))

# =============================================================================
key_cols = [c for c in ("ID","householdID","communityID") if c in health.columns]
measure_cols = [c for c in health.columns if c not in key_cols]
mask_elim = health[measure_cols].isna().all(axis=1)
eliminated = health.loc[mask_elim, key_cols].copy()
kept = health.loc[~mask_elim].reset_index(drop=True)
print("[INFO] Notebook progress message.")
if not eliminated.empty:
    ensure_dir(base_out)
    eliminated.to_excel(out_elim, index=False)
    print("[INFO] Notebook progress message.")

# =============================================================================
var_labels = {
    "ID": "ID",
    "householdID": "householdID",
    "communityID": "communityID",
    "srh": "自评健康",
    "disease": "疾病（DA003 阵列）",
    "social_activity": "社交活动",
    "social_freq": "社交频率",
    "meet_child_freq": "与子女见面频率",
    "call_child_freq": "与子女通讯频率",
    "annual_transfer": "年度转移（CA017）",
    # ADL
    "dress": "穿衣",
    "bathe": "洗澡（困难题；少量可能来自“是否有人帮助”兜底）",
    "eat": "进食",
    "bed_chair_transfer": "床椅转移",
    "bend_kneel_squat": "如厕（按你的要求，作为“弯腰/跪/蹲”的替代）",
    "incontinence": "大小便控制",
    "housework": "做家务",
    # DC
    "depress": "抑郁", "effort": "做事很费力", "hope": "对未来有希望",
    "fear": "害怕", "sleep": "睡眠差", "happy": "快乐",
    "hopeless": "活不下去", "life_satisfaction": "生活满意度",
}

# =============================================================================
ensure_dir(base_out)
health_clean = sanitize_for_stata(kept)
write_stata_safely(health_clean, out_dta, var_labels=var_labels)

cn_cols = {c: var_labels.get(c, c) for c in kept.columns}
for k in ("ID","householdID","communityID"): cn_cols[k] = k
kept.rename(columns=cn_cols).to_excel(out_xlsx, index=False)
print("[INFO] Notebook progress message.")
print("[INFO] Notebook progress message.")


# ------------------------------------------------------------------------------
# Notebook cell 13
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 02_wave_health_recode.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import re
from pathlib import Path
import numpy as np
import pandas as pd

# =============================================================================
base_in = r"E:\project_flood_impact_assessment\老年人健康\CHARLS\charls原版数据\原始数据+问卷2011~2020\2020\CHARLS2020r"
f_d  = fr"{base_in}\Health_Status_and_Functioning.dta"
f_ci = fr"{base_in}\Family_Information.dta"   # CA015/CA016/CA017

base_out = r"E:\impact_assessment_child_order\older\health\2020"
out_dta  = fr"{base_out}\2020_health_result.dta"
out_xlsx = fr"{base_out}\2020_health_result.xlsx"
out_elim = fr"{base_out}\eliminate.xlsx"  # Original notebook comment normalized for the public code archive.

# =============================================================================
def read_dta(path):
    df = pd.read_stata(path, convert_categoricals=False)
    print("[INFO] Notebook progress message.")
    return df

def ensure_dir(p): Path(p).mkdir(parents=True, exist_ok=True)

def find_cols(df, pattern):
    if isinstance(pattern, str):
        pattern = re.compile(pattern, flags=re.IGNORECASE)
    return [c for c in df.columns if pattern.match(c)]

def sort_cols_by_suffix(cols, prefix_regex=r"^(.+?)_?(\d+)_?$"):
    def key(c):
        m = re.match(prefix_regex, c, flags=re.IGNORECASE)
        return (int(m.group(2)) if m else 10**9)
    return sorted(cols, key=key)

def suffix_map(cols):
    m = {}
    for c in cols:
        mt = re.search(r"_(\d+)_?$", c, flags=re.I)
        if mt: m[mt.group(1)] = c
    return m

def first_nonnull(*series):
    out = None
    for s in series:
        if s is None: continue
        s = pd.to_numeric(s, errors="coerce")
        out = s if out is None else out.combine_first(s)
    return out

def row_any_eq(df, cols, val):
    if not cols: return pd.Series(False, index=df.index)
    arr = df[cols].apply(pd.to_numeric, errors="coerce")
    return (arr == val).any(axis=1)

def row_all_eq(df, cols, val):
    if not cols: return pd.Series(False, index=df.index)
    arr = df[cols].apply(pd.to_numeric, errors="coerce")
    any_notna = arr.notna().any(axis=1)
    all_val   = (arr.replace(np.nan, val) == val).all(axis=1)
    return any_notna & all_val

def row_min(df, cols):
    if not cols:
        return pd.Series(np.nan, index=df.index, dtype="float64")
    arr = df[cols].apply(pd.to_numeric, errors="coerce")
    return arr.min(axis=1)

def ensure_varname_len32(df):
    cols = list(df.columns); new, used = [], set()
    for c in cols:
        base = str(c)[:32]; name = base; i = 1
        while name in used:
            suf = f"_{i}"; name = base[:32-len(suf)] + suf; i += 1
        new.append(name); used.add(name)
    if new != cols:
        df = df.rename(columns=dict(zip(cols,new)))
        print("[INFO] Notebook progress message.")
    return df

def coerce_to_latin1(df, how="ignore"):
    d = df.copy()
    for c in d.select_dtypes(include=["object","string"]).columns:
        s = d[c].astype(object); m = pd.isna(s)
        s = s.astype(str).str.encode("latin-1", errors=how).str.decode("latin-1")
        s[m] = None; d[c] = s
    return d

def sanitize_for_stata(d):
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

def write_stata_safely(df, out_path, var_labels=None):
    df = ensure_varname_len32(df)
    ensure_dir(Path(out_path).parent)
    try:
        import pyreadstat
        vlabels = {k: var_labels.get(k, "") for k in df.columns} if var_labels else None
        last_err = None
        for ver in (118, 117, 114):
            try:
                pyreadstat.write_dta(df, out_path, version=ver, variable_labels=vlabels)
                print("[INFO] Notebook progress message.")
                return
            except Exception as e:
                last_err = e
        print("[INFO] Notebook progress message.")
    except Exception as e:
        print("[INFO] Notebook progress message.", e)
    df2 = coerce_to_latin1(df, how="ignore")
    df2.to_stata(out_path, write_index=False, version=117)
    print("[INFO] Notebook progress message.")

def _clean_to_str(s: pd.Series) -> pd.Series:
    s = pd.Series(s, dtype="object"); m = s.isna()
    sc = s[~m].astype(str).str.strip()
    sc = sc.str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = sc; s.loc[m] = np.nan
    return s

def canon_id_fixed(s: pd.Series, width: int) -> pd.Series:
    s = _clean_to_str(s); m = s.notna()
    s.loc[m] = s.loc[m].astype(str).str.zfill(width); return s

def standardize_keys(df, keys=("ID","householdID","communityID")):
    lower_map = {c.lower(): c for c in df.columns}
    if "id" not in lower_map and "pid" in lower_map:
        df = df.rename(columns={lower_map["pid"]: "ID"}); lower_map["id"] = "ID"
    ren = {}
    for k in keys:
        if k.lower() in lower_map and lower_map[k.lower()] != k:
            ren[lower_map[k.lower()]] = k
    if ren: df = df.rename(columns=ren)
    if "ID" in df.columns: df["ID"] = canon_id_fixed(df["ID"], 11)
    if "householdID" in df.columns: df["householdID"] = canon_id_fixed(df["householdID"], 9)
    if "communityID" in df.columns: df["communityID"] = canon_id_fixed(df["communityID"], 7)
    return df

# =============================================================================
d_df  = standardize_keys(read_dta(f_d))
ci_df = standardize_keys(read_dta(f_ci))

# =============================================================================
df = d_df

# Original notebook comment normalized for the public code archive.
srh_cols = find_cols(df, r"^da001(?:_\d+)?_?$")
srh = row_min(df, srh_cols) if srh_cols else pd.Series(np.nan, index=df.index, dtype="float64")
srh = pd.to_numeric(srh, errors="coerce")

# Original notebook comment normalized for the public code archive.
d3_cols = sort_cols_by_suffix(find_cols(df, r"^da003_(?:\d+)_?$"), r"^(da003)_?(\d+)_?$")
if d3_cols:
    disease = pd.Series(
        np.where(row_any_eq(df, d3_cols, 1), 1,
                 np.where(row_all_eq(df, d3_cols, 2), 2, np.nan)),
        index=df.index, dtype="float64"
    )
else:
    disease = pd.Series(np.nan, index=df.index, dtype="float64")

# Original notebook comment normalized for the public code archive.
act_cols = sort_cols_by_suffix(find_cols(df, r"^da038(?:_s)?(?:[1-9])_?$"),
                               r"^(da038(?:_s)?)?(\d+)_?$")
A = df[act_cols].apply(pd.to_numeric, errors="coerce") if act_cols else pd.DataFrame(index=df.index)
has_none = (A.filter(regex=r"^da038(?:_s)?9_?$") == 9).any(axis=1) if not A.empty else pd.Series(False, index=df.index)
has_any  = (A.filter(regex=r"^da038(?:_s)?[1-8]_?$") > 0).any(axis=1) if not A.empty else pd.Series(False, index=df.index)
social_activity = pd.Series(np.where(has_none, 2, np.where(has_any, 1, np.nan)),
                            index=df.index, dtype="float64")

freq_cols = sort_cols_by_suffix(find_cols(df, r"^da039_(?:[1-8])_?$"))
social_freq = row_min(df, freq_cols) if freq_cols else pd.Series(np.nan, index=df.index, dtype="float64")
social_freq = pd.to_numeric(social_freq, errors="coerce")
social_freq.loc[social_activity == 2] = 0

# Original notebook comment normalized for the public code archive.
db_new = {}
def _take(var):  # Original notebook comment normalized for the public code archive.
    cols = find_cols(df, rf"^{var}_?$")
    return (pd.to_numeric(df[cols[0]], errors="coerce") if cols else None)

# Original notebook comment normalized for the public code archive.
m_2020 = {
    "db001": ("dress",              "穿衣"),
    "db003": ("bathe",              "洗澡"),            # Original notebook comment normalized for the public code archive.
    "db005": ("eat",                "进食"),
    "db007": ("bed_chair_transfer", "床椅转移"),
    "db009": ("bend_kneel_squat",   "如厕（替代弯腰/跪/蹲）"),
    "db011": ("incontinence",       "大小便控制"),
}
for old,(new,_) in m_2020.items():
    s = _take(old)
    if s is not None: db_new[new] = s

# Original notebook comment normalized for the public code archive.
if "bathe" not in db_new:
    s_bathe_help = _take("db004")
    if s_bathe_help is not None: db_new["bathe"] = s_bathe_help

# Original notebook comment normalized for the public code archive.
for cand in ("db016","db012"):
    s_hw = _take(cand)
    if s_hw is not None:
        db_new["housework"] = s_hw
        break

# Original notebook comment normalized for the public code archive.
dc_map = {
    # Original notebook comment normalized for the public code archive.
    "dc014": ("immediate_recall", "即时回忆（DC014）"),
    "dc028": ("delayed_recall",   "延迟回忆（DC028）"),

    # Original notebook comment normalized for the public code archive.
    "dc018": ("depress", "抑郁"),
    "dc019": ("effort", "做事很费力"),
    "dc020": ("hope", "对未来有希望"),
    "dc021": ("fear", "害怕"),
    "dc022": ("sleep", "睡眠差"),
    "dc023": ("happy", "快乐"),
    "dc025": ("hopeless", "活不下去"),
    "dc026": ("life_satisfaction", "生活满意度"),
}
dc_new = {}
for old,(new,_) in dc_map.items():
    cols = find_cols(df, rf"^{old}_?$")
    if cols: dc_new[new] = pd.to_numeric(df[cols[0]], errors="coerce")

# Original notebook comment normalized for the public code archive.
cesd_cols = {}
for i in range(16, 26):  # 16..25
    nm = f"dc{str(i).zfill(3)}"
    cols = find_cols(df, rf"^{nm}_?$")
    if cols:
        cesd_cols[nm] = pd.to_numeric(df[cols[0]], errors="coerce")

if cesd_cols:
    cesd_df = pd.DataFrame(cesd_cols, index=df.index)

    # Original notebook comment normalized for the public code archive.
    map_ = {1:0, 2:1, 3:2, 4:3}
    cesd_rec = cesd_df.apply(lambda s: s.map(map_))

    # Original notebook comment normalized for the public code archive.
    for pos in ("dc020", "dc023"):
        if pos in cesd_rec:
            cesd_rec[pos] = 3 - cesd_rec[pos]

    # Original notebook comment normalized for the public code archive.
    cesd10_sum = cesd_rec.sum(axis=1, min_count=8)
else:
    cesd10_sum = pd.Series(np.nan, index=df.index, dtype="float64")

# =============================================================================
ci = ci_df.copy()

meet_cols = sort_cols_by_suffix(find_cols(ci, r"^ca015_(?:\d+)_?$"))
if meet_cols:
    all_na_meet = ci[meet_cols].isna().all(axis=1)
    if all_na_meet.any(): ci.loc[all_na_meet, meet_cols] = 9
    meet_child = row_min(ci, meet_cols)
else:
    meet_child = pd.Series(np.nan, index=ci.index, dtype="float64")
meet_child = pd.to_numeric(meet_child, errors="coerce").fillna(9)

call_cols = sort_cols_by_suffix(find_cols(ci, r"^ca016_(?:\d+)_?$"))
if meet_cols and call_cols:
    m3, m4 = suffix_map(meet_cols), suffix_map(call_cols)
    for k in (set(m3) & set(m4)):
        c3, c4 = m3[k], m4[k]
        v3 = pd.to_numeric(ci[c3], errors="coerce")
        mask_fill = ci[c4].isna() & v3.isin([1,2,3])
        ci.loc[mask_fill, c4] = v3.loc[mask_fill]
if call_cols:
    all_na_call = ci[call_cols].isna().all(axis=1)
    if all_na_call.any(): ci.loc[all_na_call, call_cols] = 9
    call_child = row_min(ci, call_cols)
else:
    call_child = pd.Series(np.nan, index=ci.index, dtype="float64")
call_child = pd.to_numeric(call_child, errors="coerce").fillna(9)

trans_cols = [c for c in ci.columns if re.match(r"^ca017_", c, flags=re.IGNORECASE)]
if trans_cols:
    A = ci[trans_cols].apply(pd.to_numeric, errors="coerce").mask(lambda x: x < 0)
    any_observed = A.notna().any(axis=1)
    any_pos      = (A.fillna(0) > 0).any(axis=1)
    all_zero     = (A.fillna(0) == 0).all(axis=1) & any_observed
    annual_transfer = pd.Series(np.nan, index=ci.index, dtype="float64")
    annual_transfer.loc[any_pos]  = 1.0
    annual_transfer.loc[all_zero] = 2.0
else:
    annual_transfer = pd.Series(np.nan, index=ci.index, dtype="float64")

# =============================================================================
res_d = pd.DataFrame({
    "ID": d_df["ID"] if "ID" in d_df.columns else np.nan,
    "householdID": d_df["householdID"] if "householdID" in d_df.columns else np.nan,
    "communityID": d_df["communityID"] if "communityID" in d_df.columns else np.nan,
    "srh": srh,
    "disease": disease,
    "social_activity": social_activity,
    "social_freq": social_freq,
}, index=d_df.index)

for k,v in db_new.items(): res_d[k] = v
for k,v in dc_new.items(): res_d[k] = v
# Original notebook comment normalized for the public code archive.
res_d["cesd10_sum"] = cesd10_sum

res_ci = pd.DataFrame({
    "householdID": ci_df["householdID"] if "householdID" in ci_df.columns else np.nan,
    "communityID": ci_df["communityID"] if "communityID" in ci_df.columns else np.nan,
    "meet_child_freq": meet_child,
    "call_child_freq": call_child,
    "annual_transfer": annual_transfer,
}, index=ci_df.index)

def dedup_on_keys(df, keys):
    before = len(df)
    df2 = df.drop_duplicates(subset=[k for k in keys if k in df.columns], keep="first")
    if len(df2) < before:
        print("[INFO] Notebook progress message.")
    return df2

keys_hh = ["householdID","communityID"]
res_d  = dedup_on_keys(res_d,  ["householdID","communityID","ID"])
res_ci = dedup_on_keys(res_ci, keys_hh)

health = res_d.merge(res_ci, on=keys_hh, how="left", suffixes=("", "_ci"))

# =============================================================================
key_cols = [c for c in ("ID","householdID","communityID") if c in health.columns]
measure_cols = [c for c in health.columns if c not in key_cols]
mask_elim = health[measure_cols].isna().all(axis=1)
eliminated = health.loc[mask_elim, key_cols].copy()
kept = health.loc[~mask_elim].reset_index(drop=True)
print("[INFO] Notebook progress message.")
if not eliminated.empty:
    ensure_dir(base_out)
    eliminated.to_excel(out_elim, index=False)
    print("[INFO] Notebook progress message.")

# =============================================================================
var_labels = {
    "ID": "ID",
    "householdID": "householdID",
    "communityID": "communityID",
    "srh": "自评健康",
    "disease": "疾病（DA003 阵列）",
    "social_activity": "社交活动",
    "social_freq": "社交频率",
    "meet_child_freq": "与子女见面频率",
    "call_child_freq": "与子女通讯频率",
    "annual_transfer": "年度转移（CA017）",
    # ADL
    "dress": "穿衣",
    "bathe": "洗澡（困难题；少量来自“是否有人帮助”兜底）",
    "eat": "进食",
    "bed_chair_transfer": "床椅转移",
    "bend_kneel_squat": "如厕（作为“弯腰/跪/蹲”的替代）",
    "incontinence": "大小便控制",
    "housework": "做家务",
    # Original notebook comment normalized for the public code archive.
    "depress": "抑郁", "effort": "做事很费力", "hope": "对未来有希望",
    "fear": "害怕", "sleep": "睡眠差", "happy": "快乐",
    "hopeless": "活不下去", "life_satisfaction": "生活满意度",
    # Original notebook comment normalized for the public code archive.
    "immediate_recall": "即时回忆（DC014）",
    "delayed_recall":   "延迟回忆（DC028）",
    "cesd10_sum":       "CES-D10 总分（DC016–DC025；0–30；正向题反向；≥8题有效）",
}

# =============================================================================
ensure_dir(base_out)
health_clean = sanitize_for_stata(kept)
write_stata_safely(health_clean, out_dta, var_labels=var_labels)

# Original notebook comment normalized for the public code archive.
cn_cols = {c: var_labels.get(c, c) for c in kept.columns}
for k in ("ID","householdID","communityID"): cn_cols[k] = k
kept.rename(columns=cn_cols).to_excel(out_xlsx, index=False)
print("[INFO] Notebook progress message.")
print("[INFO] Notebook progress message.")


# ------------------------------------------------------------------------------
# Notebook cell 14
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from pathlib import Path

# =============================================================================
# Excel output note.
path = r"E:\impact_assessment_child_order\older\health\2020\2020_health_result.xlsx"
df = pd.read_excel(path, dtype=object)   # Original notebook comment normalized for the public code archive.



# =============================================================================
df = df.replace(r"^\s*$", np.nan, regex=True)

# =============================================================================
n = len(df)
na_count = df.isna().sum()
na_pct = (na_count / n * 100).round(2)

summary = (
    pd.DataFrame({"n_missing": na_count, "missing_pct": na_pct})
      .sort_values("n_missing", ascending=False)
)

# Original notebook comment normalized for the public code archive.
print(summary.head(20))

# Original notebook comment normalized for the public code archive.
out = Path(path).with_name(Path(path).stem + "_missing_summary.xlsx")
summary.to_excel(out, index=True)
print("[INFO] Notebook progress message.")
