#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""



# =============================================================================
# Source notebook
# =============================================================================
# record_type : wave_step
# year        : 2011
# step        : 5
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 4
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import re
import inspect
import numpy as np
import pandas as pd
from pathlib import Path

# =============================================================================
ROOT = Path(r"E:\impact_assessment_child_order\older\health\2011")
CHI_XLSX = ROOT / "2011_综合健康指数.xlsx"
AGE_DTA  = ROOT / "2011_age_region.dta"
AGE_XLSX = ROOT / "2011_age_region.xlsx"
OUT_DTA  = ROOT / "2011_chi_result.dta"
OUT_XLSX = ROOT / "2011_chi_result.xlsx"

# =============================================================================
def _clean_to_str(s: pd.Series) -> pd.Series:
    s = pd.Series(s, dtype="object"); m = s.isna()
    sc = s[~m].astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = sc; s.loc[m] = np.nan; return s

def canon_id_fixed(s: pd.Series, width: int) -> pd.Series:
    s = _clean_to_str(s); m = s.notna(); s.loc[m] = s.loc[m].astype(str).str.zfill(width); return s

def _digits_width(s: pd.Series, width: int) -> pd.Series:
    t = _clean_to_str(s).str.replace(r"\D", "", regex=True)
    t = t.where(t.str.len()>0, np.nan)
    return t.where(t.isna(), t.str[-width:].str.zfill(width)).astype("object")

def ensure_ids_2011(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    d = df.copy()
    if "householdID" in d.columns: d["householdID"] = canon_id_fixed(d["householdID"], 9)
    if "communityID" in d.columns: d["communityID"] = canon_id_fixed(d["communityID"], 7)
    if "ID" in d.columns:          d["ID"]          = canon_id_fixed(d["ID"], 11)

    # householdID10
    if "householdID10" not in d.columns or d["householdID10"].isna().all():
        hh9 = _digits_width(d["householdID"], 9) if "householdID" in d.columns else pd.Series(np.nan, index=d.index)
        d["householdID10"] = hh9.where(hh9.isna(), hh9 + "0")
    else:
        d["householdID10"] = _digits_width(d["householdID10"], 10)

    # ID12
    if "ID12" not in d.columns or d["ID12"].isna().all():
        id11 = _digits_width(d["ID"], 11) if "ID" in d.columns else pd.Series(np.nan, index=d.index)
        pn2  = id11.str[-2:]
        d["ID12"] = np.where(d["householdID10"].notna() & pn2.notna(), d["householdID10"] + pn2, np.nan).astype("object")
    else:
        d["ID12"] = _digits_width(d["ID12"], 12)
    return d

def read_age_table():
    if AGE_DTA.exists():
        try:
            import pyreadstat
            df, _ = pyreadstat.read_dta(str(AGE_DTA), apply_value_formats=False)
            print("Read age-region (pyreadstat):", AGE_DTA)
            return df
        except Exception as e:
            print("[INFO] Notebook progress message.", e)
            try:
                return pd.read_stata(AGE_DTA, convert_categoricals=False)
            except Exception as e2:
                print("[INFO] Notebook progress message.", e2)
    df = pd.read_excel(AGE_XLSX)
    print("Read age-region (xlsx):", AGE_XLSX)
    return df

def write_dta_smart(df: pd.DataFrame, out_path: Path, var_labels=None):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Original notebook comment normalized for the public code archive.
    cols = list(df.columns); new, used = [], set()
    for c in cols:
        base = re.sub(r"[^0-9A-Za-z_]", "_", str(c))[:32]
        name, i = base, 1
        while name in used:
            suf = f"_{i}"; name = base[:32-len(suf)] + suf; i += 1
        new.append(name); used.add(name)
    if new != cols: df = df.rename(columns=dict(zip(cols, new)))

    # Original notebook comment normalized for the public code archive.
    try:
        import pyreadstat
        last = None
        for ver in (119, 118):
            try:
                kwargs = {"version": ver}
                if var_labels:
                    try:
                        if "variable_labels" in inspect.signature(pyreadstat.write_dta).parameters:
                            kwargs["variable_labels"] = {k: var_labels.get(k, "") for k in df.columns}
                    except Exception:
                        pass
                pyreadstat.write_dta(df, str(out_path), **kwargs)
                print(f"Saved DTA via pyreadstat v{ver} ->", out_path)
                return
            except Exception as e:
                last = e
        print("[INFO] Notebook progress message.", last)
    except Exception as e:
        print("[INFO] Notebook progress message.", e)

    # pandas v118（UTF-8）
    try:
        df.to_stata(out_path, write_index=False, version=118)
        print("Saved DTA via pandas v118 (UTF-8) ->", out_path)
        return
    except Exception as e:
        print("[INFO] Notebook progress message.", e)

    df2 = df.copy()
    for c in df2.select_dtypes(include=["object"]).columns:
        df2[c] = df2[c].astype(str).str.encode("latin-1","ignore").str.decode("latin-1")
    df2.to_stata(out_path, write_index=False, version=117)
    print("Saved DTA via pandas v117 (latin-1) ->", out_path)

# =============================================================================
chi = pd.read_excel(CHI_XLSX)
print("Read chi xlsx:", CHI_XLSX)
age_all = read_age_table()

# =============================================================================
chi = ensure_ids_2011(chi)
age_all = ensure_ids_2011(age_all)

# =============================================================================
if "出生年" not in age_all.columns and "birth_year" in age_all.columns:
    age_all["出生年"] = age_all["birth_year"]
if "年龄" not in age_all.columns and "age_2011" in age_all.columns:
    age_all["年龄"] = age_all["age_2011"]

# =============================================================================
# Original notebook comment normalized for the public code archive.
if "ID12" in chi.columns and "ID12" in age_all.columns and chi["ID12"].notna().any():
    age_id = age_all[[c for c in ["ID12","出生年","年龄"] if c in age_all.columns]].drop_duplicates(subset=["ID12"])
    chi1 = chi.merge(age_id, on="ID12", how="left")
else:
    age_id = age_all[[c for c in ["ID","出生年","年龄"] if c in age_all.columns]].drop_duplicates(subset=["ID"])
    chi1 = chi.merge(age_id, on="ID", how="left")

# Original notebook comment normalized for the public code archive.
region_cols = [c for c in ["communityID","province","city","urban_nbs","areatype"] if c in age_all.columns]
age_region = age_all[region_cols].drop_duplicates(subset=["communityID"]) if "communityID" in region_cols else pd.DataFrame()
merged = chi1.merge(age_region, on="communityID", how="left") if not age_region.empty else chi1.copy()

# =============================================================================
order_front = [c for c in ["ID12","householdID10","ID","householdID","communityID"] if c in merged.columns]
four_idx = [c for c in ["身体健康(0-100)","心理健康(0-100)","社会适应(0-100)","综合健康指数(0-100)"] if c in merged.columns]
age_cols = [c for c in ["出生年","年龄"] if c in merged.columns]
region_cols_final = [c for c in ["province","city","urban_nbs","areatype"] if c in merged.columns]
other_cols = [c for c in merged.columns if c not in (order_front+four_idx+age_cols+region_cols_final)]
merged = merged[order_front + four_idx + age_cols + region_cols_final + other_cols]

# =============================================================================
# Excel
merged.to_excel(OUT_XLSX, index=False)
print("Excel ->", OUT_XLSX)

# Original notebook comment normalized for the public code archive.
dta_map = {
    "身体健康(0-100)":"body_index_0_100",
    "心理健康(0-100)":"mental_index_0_100",
    "社会适应(0-100)":"social_index_0_100",
    "综合健康指数(0-100)":"overall_index_0_100",
    "出生年":"birth_year",
    "年龄":"age_2011",
}
out_dta = merged.rename(columns=dta_map).copy()
var_labels = {
    "ID12":"个人ID(12位，2013+兼容)","householdID10":"householdID(10位，2013+兼容)",
    "ID":"ID(2011原11位)","householdID":"householdID(9位，2011原始)","communityID":"communityID(7位)",
    "body_index_0_100":"身体健康(0-100)","mental_index_0_100":"心理健康(0-100)",
    "social_index_0_100":"社会适应(0-100)","overall_index_0_100":"综合健康指数(0-100)",
    "birth_year":"出生年","age_2011":"年龄(2011-出生年)",
    "province":"省","city":"市","urban_nbs":"国家统计局城乡","areatype":"地区类型",
}
write_dta_smart(out_dta, OUT_DTA, var_labels=var_labels)
print("DTA  ->", OUT_DTA)

# =============================================================================
n_all = len(merged)
n_have_region = merged[["province","city"]].notna().any(axis=1).sum() if {"province","city"}.issubset(merged.columns) else 0
n_have_age = merged["年龄"].notna().sum() if "年龄" in merged.columns else 0
print("[INFO] Notebook progress message.")


# ------------------------------------------------------------------------------
# Notebook cell 10
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import re
import inspect
import numpy as np
import pandas as pd
from pathlib import Path

# =============================================================================
ROOT = Path(r"E:\impact_assessment_child_order\older\health\2011")
CHI_XLSX = ROOT / "2011_health_index_panel_fixed.xlsx"
AGE_DTA  = ROOT / "2011_age_region.dta"
AGE_XLSX = ROOT / "2011_age_region.xlsx"
OUT_DTA  = ROOT / "2011_chi_result.dta"
OUT_XLSX = ROOT / "2011_chi_result.xlsx"

# Original notebook comment normalized for the public code archive.
CODE_XLS = Path(r"E:\impact_assessment_child_order\older\编码.xls")

# =============================================================================
def _clean_to_str(s: pd.Series) -> pd.Series:
    s = pd.Series(s, dtype="object"); m = s.isna()
    sc = s[~m].astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = sc; s.loc[m] = np.nan; return s

def canon_id_fixed(s: pd.Series, width: int) -> pd.Series:
    s = _clean_to_str(s); m = s.notna(); s.loc[m] = s.loc[m].astype(str).str.zfill(width); return s

def _digits_width(s: pd.Series, width: int) -> pd.Series:
    t = _clean_to_str(s).str.replace(r"\D", "", regex=True)
    t = t.where(t.str.len()>0, np.nan)
    return t.where(t.isna(), t.str[-width:].str.zfill(width)).astype("object")

def ensure_ids_2011(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    d = df.copy()
    if "householdID" in d.columns: d["householdID"] = canon_id_fixed(d["householdID"], 9)
    if "communityID" in d.columns: d["communityID"] = canon_id_fixed(d["communityID"], 7)
    if "ID" in d.columns:          d["ID"]          = canon_id_fixed(d["ID"], 11)

    if "householdID10" not in d.columns or d["householdID10"].isna().all():
        hh9 = _digits_width(d["householdID"], 9) if "householdID" in d.columns else pd.Series(np.nan, index=d.index)
        d["householdID10"] = hh9.where(hh9.isna(), hh9 + "0")
    else:
        d["householdID10"] = _digits_width(d["householdID10"], 10)

    if "ID12" not in d.columns or d["ID12"].isna().all():
        id11 = _digits_width(d["ID"], 11) if "ID" in d.columns else pd.Series(np.nan, index=d.index)
        pn2  = id11.str[-2:]
        d["ID12"] = np.where(d["householdID10"].notna() & pn2.notna(), d["householdID10"] + pn2, np.nan).astype("object")
    else:
        d["ID12"] = _digits_width(d["ID12"], 12)
    return d

def read_age_table():
    if AGE_DTA.exists():
        try:
            import pyreadstat
            df, _ = pyreadstat.read_dta(str(AGE_DTA), apply_value_formats=False)
            print("Read age-region (pyreadstat):", AGE_DTA)
            return df
        except Exception as e:
            print("[INFO] Notebook progress message.", e)
            try:
                return pd.read_stata(AGE_DTA, convert_categoricals=False)
            except Exception as e2:
                print("[INFO] Notebook progress message.", e2)
    df = pd.read_excel(AGE_XLSX)
    print("Read age-region (xlsx):", AGE_XLSX)
    return df

def write_dta_smart(df: pd.DataFrame, out_path: Path, var_labels=None):
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cols = list(df.columns); new, used = [], set()
    for c in cols:
        base = re.sub(r"[^0-9A-Za-z_]", "_", str(c))[:32]
        name, i = base, 1
        while name in used:
            suf = f"_{i}"
            name = base[:32-len(suf)] + suf
            i += 1
        new.append(name); used.add(name)
    if new != cols: df = df.rename(columns=dict(zip(cols, new)))
    try:
        import pyreadstat
        last = None
        for ver in (119, 118):
            try:
                kwargs = {"version": ver}
                if var_labels:
                    try:
                        if "variable_labels" in inspect.signature(pyreadstat.write_dta).parameters:
                            kwargs["variable_labels"] = {k: var_labels.get(k, "") for k in df.columns}
                    except Exception:
                        pass
                pyreadstat.write_dta(df, str(out_path), **kwargs)
                print(f"Saved DTA via pyreadstat v{ver} ->", out_path)
                return
            except Exception as e:
                last = e
        print("[INFO] Notebook progress message.", last)
    except Exception as e:
        print("[INFO] Notebook progress message.", e)
    try:
        df.to_stata(out_path, write_index=False, version=118)
        print("Saved DTA via pandas v118 (UTF-8) ->", out_path)
        return
    except Exception as e:
        print("[INFO] Notebook progress message.", e)
    df2 = df.copy()
    for c in df2.select_dtypes(include=["object"]).columns:
        df2[c] = df2[c].astype(str).str.encode("latin-1","ignore").str.decode("latin-1")
    df2.to_stata(out_path, write_index=False, version=117)
    print("Saved DTA via pandas v117 (latin-1) ->", out_path)

def pick_col(df: pd.DataFrame, candidates):
    low = {c.lower(): c for c in df.columns}
    for n in candidates:
        if n and n.lower() in low: return low[n.lower()]
    for n in candidates:
        for c in df.columns:
            if n and n.lower() in c.lower(): return c
    return None

# Original notebook comment normalized for the public code archive.
PROV_ALIAS = {
    "内蒙古自治区":"内蒙古","广西壮族自治区":"广西","西藏自治区":"西藏",
    "宁夏回族自治区":"宁夏","新疆维吾尔自治区":"新疆",
    "香港特别行政区":"香港","澳门特别行政区":"澳门",
}
CITY_ALIAS = {
    "襄樊":"襄阳","襄樊市":"襄阳","海东地区":"海东","海东市":"海东","阿克苏地区":"阿克苏","巢湖市":"巢湖",
}
DELEGATED_TO = {("安徽","巢湖"): ("安徽","合肥")}

def norm_province(x: pd.Series) -> pd.Series:
    s = _clean_to_str(x).fillna("")
    s = s.replace(PROV_ALIAS).str.replace(r"(省|市|特别行政区|自治区)$","",regex=True)
    return s.str.strip()

def norm_city(x: pd.Series) -> pd.Series:
    s = _clean_to_str(x).fillna("").replace(CITY_ALIAS)
    s = s.str.replace(r"(市|地区|盟|自治州|林区|矿区|新区)$","",regex=True).str.replace(r"市辖区$","",regex=True)
    return s.str.strip()

def read_city_codes(path: Path) -> pd.DataFrame:
    if not path.exists():
        print("[INFO] Notebook progress message.")
        return pd.DataFrame(columns=["province","city","city_code","prov_norm","city_norm"])
    code_raw = pd.read_excel(path)
    prov_col = pick_col(code_raw, ["province","省","省份"])
    city_col = pick_col(code_raw, ["city","市","地市","地级市","prefecture"])
    code_col = pick_col(code_raw, ["code","编码","代码","citycode","行政区划代码","adcode","ad_code"])
    if city_col is None or code_col is None:
        print("[INFO] Notebook progress message.")
        return pd.DataFrame(columns=["province","city","city_code","prov_norm","city_norm"])
    codes = pd.DataFrame({
        "province": _clean_to_str(code_raw[prov_col]) if prov_col else pd.Series(np.nan, index=code_raw.index, dtype="object"),
        "city":     _clean_to_str(code_raw[city_col]),
        "city_code": _clean_to_str(code_raw[code_col]),
    })
    codes = codes[codes["city"].notna()].copy()
    codes["city_code"] = codes["city_code"].str.extract(r"(\d+)", expand=False)
    m = codes["city_code"].notna()
    codes.loc[m, "city_code"] = codes.loc[m, "city_code"].astype(str).str.zfill(6)
    codes["prov_norm"] = norm_province(codes["province"]) if "province" in codes.columns else ""
    codes["city_norm"] = norm_city(codes["city"])
    codes = codes.drop_duplicates(subset=["prov_norm","city_norm"])
    print("[INFO] Notebook progress message.")
    return codes

# =============================================================================
chi = pd.read_excel(CHI_XLSX); print("Read chi xlsx:", CHI_XLSX)
age_all = read_age_table()
codes   = read_city_codes(CODE_XLS)

# =============================================================================
chi = ensure_ids_2011(chi)
age_all = ensure_ids_2011(age_all)

# =============================================================================
if "出生年" not in age_all.columns and "birth_year" in age_all.columns:
    age_all["出生年"] = age_all["birth_year"]
if "年龄" not in age_all.columns and "age_2011" in age_all.columns:
    age_all["年龄"] = age_all["age_2011"]

# =============================================================================
# Original notebook comment normalized for the public code archive.
if "ID12" in chi.columns and "ID12" in age_all.columns and chi["ID12"].notna().any():
    age_id = age_all[[c for c in ["ID12","出生年","年龄"] if c in age_all.columns]].drop_duplicates(subset=["ID12"])
    chi1 = chi.merge(age_id, on="ID12", how="left")
else:
    age_id = age_all[[c for c in ["ID","出生年","年龄"] if c in age_all.columns]].drop_duplicates(subset=["ID"])
    chi1 = chi.merge(age_id, on="ID", how="left")

# Original notebook comment normalized for the public code archive.
region_cols = [c for c in ["communityID","province","city","urban_nbs","areatype"] if c in age_all.columns]
age_region = age_all[region_cols].drop_duplicates(subset=["communityID"]) if "communityID" in region_cols else pd.DataFrame()
merged = chi1.merge(age_region, on="communityID", how="left") if not age_region.empty else chi1.copy()

# =============================================================================
if not codes.empty and {"city"}.issubset(merged.columns):
    merged["prov_norm"] = norm_province(merged["province"]) if "province" in merged.columns else ""
    merged["city_norm"] = norm_city(merged["city"])
    # Step 1
    merged = merged.merge(codes[["prov_norm","city_norm","city_code"]], on=["prov_norm","city_norm"], how="left")
    matched_pc = merged["city_code"].notna().sum()
    # Step 2
    need = merged["city_code"].isna()
    if need.any():
        uniq_city = (codes.groupby("city_norm")["city_code"].nunique().reset_index())
        uniq_city = uniq_city[uniq_city["city_code"]==1]["city_norm"]
        codes_city_only = codes[codes["city_norm"].isin(uniq_city)][["city_norm","city_code"]].drop_duplicates("city_norm")
        fill = merged.loc[need, ["city_norm"]].merge(codes_city_only, on="city_norm", how="left")["city_code"]
        merged.loc[need, "city_code"] = fill.values
    # Step 3
    if "city_code" in merged.columns:
        code_map = codes.set_index(["prov_norm","city_norm"])["city_code"].to_dict()
        filled = 0
        for (prov_from, city_from), (prov_to, city_to) in DELEGATED_TO.items():
            mask = merged["city_code"].isna() & (merged["prov_norm"]==prov_from) & (merged["city_norm"]==city_from)
            if mask.any():
                code_to = code_map.get((prov_to, city_to))
                if pd.notna(code_to):
                    merged.loc[mask, "city_code"] = str(code_to).zfill(6)
                    filled += int(mask.sum())
        if filled:
            print("[INFO] Notebook progress message.")
    matched_total = merged["city_code"].notna().sum()
    print("[INFO] Notebook progress message.")

# =============================================================================
order_front = [c for c in ["ID12","householdID10","ID","householdID","communityID"] if c in merged.columns]
four_idx = [c for c in ["身体健康(0-100)","心理健康(0-100)","社会适应(0-100)","综合健康指数(0-100)"] if c in merged.columns]
age_cols = [c for c in ["出生年","年龄"] if c in merged.columns]
region_cols_final = [c for c in ["province","city","city_code","urban_nbs","areatype"] if c in merged.columns]
drop_helper = [c for c in ["prov_norm","city_norm"] if c in merged.columns]
other_cols = [c for c in merged.columns if c not in (order_front+four_idx+age_cols+region_cols_final+drop_helper)]
merged = merged[order_front + four_idx + age_cols + region_cols_final + other_cols]

# =============================================================================
# Excel
merged.to_excel(OUT_XLSX, index=False)
print("Excel ->", OUT_XLSX)

# Original notebook comment normalized for the public code archive.
dta_map = {
    "身体健康(0-100)":"body_index_0_100",
    "心理健康(0-100)":"mental_index_0_100",
    "社会适应(0-100)":"social_index_0_100",
    "综合健康指数(0-100)":"overall_index_0_100",
    "出生年":"birth_year",
    "年龄":"age_2011",
}
out_dta = merged.rename(columns=dta_map).copy()
var_labels = {
    "ID12":"个人ID(12位，2013+兼容)","householdID10":"householdID(10位，2013+兼容)",
    "ID":"ID(2011原11位)","householdID":"householdID(9位，2011原始)","communityID":"communityID(7位)",
    "body_index_0_100":"身体健康(0-100)","mental_index_0_100":"心理健康(0-100)",
    "social_index_0_100":"社会适应(0-100)","overall_index_0_100":"综合健康指数(0-100)",
    "birth_year":"出生年","age_2011":"年龄(2011-出生年)",
    "province":"省","city":"市","city_code":"市代码","urban_nbs":"国家统计局城乡","areatype":"地区类型",
}
def write_dta_smart_local(df, out_path, var_labels=None):  # Original notebook comment normalized for the public code archive.
    return write_dta_smart(df, out_path, var_labels=var_labels)
write_dta_smart_local(out_dta, OUT_DTA, var_labels=var_labels)
print("DTA  ->", OUT_DTA)

# =============================================================================
OUT_GIS_XLSX = ROOT / "2011_chi_result_forGIS.xlsx"
OUT_GIS_CSV  = ROOT / "2011_chi_result_forGIS.csv"

gis_map = {
    "身体健康(0-100)"    : "body100",
    "心理健康(0-100)"    : "mental100",
    "社会适应(0-100)"    : "social100",
    "综合健康指数(0-100)": "overall100",
    "出生年"             : "birthyr",
    "年龄"               : "age",
    "province"           : "prov",
    "city"               : "city",
    "city_code"          : "citycode",
    "urban_nbs"          : "urban_nbs",
    "areatype"           : "areatype",
}
gis = merged.rename(columns={k:v for k,v in gis_map.items() if k in merged.columns}).copy()

# City-level processing note.
if "citycode" in gis.columns:
    gis["citycode_txt"] = _clean_to_str(gis["citycode"])
    gis["citycode_int"] = pd.to_numeric(gis["citycode"], errors="coerce").astype("Int64")

# Original notebook comment normalized for the public code archive.
def arc_safe_cols(df):
    new = {}; used = set()
    for c in df.columns:
        name = re.sub(r"[^0-9A-Za-z_]", "_", str(c))
        if re.match(r"^\d", name): name = "_" + name
        name = name[:30]
        base = name; i = 1
        while name in used:
            suf = f"_{i}"; name = (base[:30-len(suf)] + suf); i += 1
        used.add(name); new[c] = name
    return df.rename(columns=new)

gis = arc_safe_cols(gis)

gis.to_excel(OUT_GIS_XLSX, index=False)
gis.to_csv(OUT_GIS_CSV, index=False, encoding="utf-8-sig")
print("GIS-friendly Excel ->", OUT_GIS_XLSX)
print("GIS-friendly CSV   ->", OUT_GIS_CSV)




# =============================================================================
# Source notebook
# =============================================================================
# record_type : wave_step
# year        : 2013
# step        : 5
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 2
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import re
import inspect
import numpy as np
import pandas as pd
from pathlib import Path

# =============================================================================
YEAR = 2013   # Original notebook comment normalized for the public code archive.

ROOT = Path(fr"E:\impact_assessment_child_order\older\health\{YEAR}")
CHI_XLSX = ROOT / f"{YEAR}_综合健康指数.xlsx"
AGE_DTA  = ROOT / f"{YEAR}_age_region.dta"
AGE_XLSX = ROOT / f"{YEAR}_age_region.xlsx"
OUT_DTA  = ROOT / f"{YEAR}_chi_result.dta"
OUT_XLSX = ROOT / f"{YEAR}_chi_result.xlsx"

# =============================================================================
def _clean_to_str(s: pd.Series) -> pd.Series:
    s = pd.Series(s, dtype="object")
    m = s.isna()
    t = s[~m].astype(str).str.strip()
    t = t.str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = t
    s.loc[m] = np.nan
    return s

def canon_id_fixed(s: pd.Series, width: int) -> pd.Series:
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = _clean_to_str(s)
    m = s.notna()
    s.loc[m] = s.loc[m].astype(str).str.zfill(width)
    return s

def canon_pid_11(s: pd.Series) -> pd.Series:
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = _clean_to_str(s)
    m = s.notna()
    t = s.copy()
    t.loc[m] = t.loc[m].str.replace(r"\D", "", regex=True)
    # Original notebook comment normalized for the public code archive.
    t = t.where(t.str.len() > 0, np.nan)
    # Original notebook comment normalized for the public code archive.
    t = t.where(t.isna(), t.str[-11:].str.zfill(11))
    return t.astype("object")

def find_col(df: pd.DataFrame, *candidates):
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
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

def read_age_table():
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if AGE_DTA.exists():
        try:
            import pyreadstat
            df, _ = pyreadstat.read_dta(str(AGE_DTA), apply_value_formats=False)
            print("Read age-region (pyreadstat):", AGE_DTA)
            return df
        except Exception as e:
            print("[INFO] Notebook progress message.", e)
            try:
                return pd.read_stata(AGE_DTA, convert_categoricals=False)
            except Exception as e2:
                print("[INFO] Notebook progress message.", e2)
    df = pd.read_excel(AGE_XLSX)
    print("Read age-region (xlsx):", AGE_XLSX)
    return df

def write_dta_smart(df: pd.DataFrame, out_path: Path, var_labels=None):
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Original notebook comment normalized for the public code archive.
    cols = list(df.columns); new, used = [], set()
    for c in cols:
        base = re.sub(r"[^0-9A-Za-z_]", "_", str(c))[:32]
        name, i = base, 1
        while name in used:
            suf = f"_{i}"; name = base[:32-len(suf)] + suf; i += 1
        new.append(name); used.add(name)
    if new != cols: df = df.rename(columns=dict(zip(cols, new)))
    # pyreadstat
    try:
        import pyreadstat
        last = None
        for ver in (119, 118):
            try:
                kwargs = {"version": ver}
                if var_labels:
                    try:
                        if "variable_labels" in inspect.signature(pyreadstat.write_dta).parameters:
                            kwargs["variable_labels"] = {k: var_labels.get(k, "") for k in df.columns}
                    except Exception:
                        pass
                pyreadstat.write_dta(df, str(out_path), **kwargs)
                print(f"Saved DTA via pyreadstat v{ver} ->", out_path)
                return
            except Exception as e:
                last = e
        print("[INFO] Notebook progress message.", last)
    except Exception as e:
        print("[INFO] Notebook progress message.", e)
    # pandas v118
    try:
        df.to_stata(out_path, write_index=False, version=118)
        print("Saved DTA via pandas v118 (UTF-8) ->", out_path)
        return
    except Exception as e:
        print("[INFO] Notebook progress message.", e)
    # Original notebook comment normalized for the public code archive.
    df2 = df.copy()
    for c in df2.select_dtypes(include=["object"]).columns:
        df2[c] = df2[c].astype(str).str.encode("latin-1","ignore").str.decode("latin-1")
    df2.to_stata(out_path, write_index=False, version=117)
    print("Saved DTA via pandas v117 (latin-1) ->", out_path)

# =============================================================================
chi = pd.read_excel(CHI_XLSX)
print("Read chi xlsx:", CHI_XLSX)

age_all = read_age_table()

# =============================================================================
for key, w in (("householdID",9), ("communityID",7)):
    if key in chi.columns:     chi[key]     = canon_id_fixed(chi[key], w)
    if key in age_all.columns: age_all[key] = canon_id_fixed(age_all[key], w)

# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
id_col_chi = find_col(chi, "ID", "Pid", "PID", "pid", "personid")
id_col_age = find_col(age_all, "ID", "Pid", "PID", "pid", "personid")
if id_col_chi and id_col_chi != "ID": chi = chi.rename(columns={id_col_chi: "ID"})
if id_col_age and id_col_age != "ID": age_all = age_all.rename(columns={id_col_age: "ID"})

if "ID" in chi.columns:
    chi["ID"] = canon_pid_11(chi["ID"])
if "ID" in age_all.columns:
    age_all["ID"] = canon_pid_11(age_all["ID"])

# =============================================================================
birth_en  = "birth_year"
age_en    = f"age_{YEAR}"
if "出生年" not in age_all.columns and birth_en in age_all.columns:
    age_all["出生年"] = age_all[birth_en]
if "年龄" not in age_all.columns and age_en in age_all.columns:
    age_all["年龄"] = age_all[age_en]

# =============================================================================
idx_ids = set(chi["ID"].dropna().astype(str)) if "ID" in chi.columns else set()
age_ids = set(age_all["ID"].dropna().astype(str)) if "ID" in age_all.columns else set()
inter   = idx_ids & age_ids
print("[INFO] Notebook progress message.")
print("[INFO] Notebook progress message.")
print("[INFO] Notebook progress message.")
print("[INFO] Notebook progress message.")
print("[INFO] Notebook progress message.")

# =============================================================================
# Original notebook comment normalized for the public code archive.
age_id_cols = [c for c in ["ID","出生年","年龄"] if c in age_all.columns]
age_id = age_all[age_id_cols].drop_duplicates(subset=["ID"]) if "ID" in age_all.columns else pd.DataFrame()
chi1 = chi.merge(age_id, on="ID", how="left") if not age_id.empty else chi.copy()

# Original notebook comment normalized for the public code archive.
region_cols = [c for c in ["communityID","province","city","urban_nbs","areatype"] if c in age_all.columns]
age_region = age_all[region_cols].drop_duplicates(subset=["communityID"]) if "communityID" in region_cols else pd.DataFrame()
merged = chi1.merge(age_region, on="communityID", how="left") if not age_region.empty else chi1.copy()

# =============================================================================
front = [c for c in ["ID","householdID","communityID"] if c in merged.columns]
four  = [c for c in ["身体健康(0-100)","心理健康(0-100)","社会适应(0-100)","综合健康指数(0-100)"] if c in merged.columns]
agecs = [c for c in ["出生年","年龄"] if c in merged.columns]
regs  = [c for c in ["province","city","urban_nbs","areatype"] if c in merged.columns]
others= [c for c in merged.columns if c not in (front+four+agecs+regs)]
merged = merged[front + four + agecs + regs + others]

# =============================================================================
# Excel
merged.to_excel(OUT_XLSX, index=False)
print("\nExcel ->", OUT_XLSX)

# Original notebook comment normalized for the public code archive.
dta_map = {
    "身体健康(0-100)":"body_index_0_100",
    "心理健康(0-100)":"mental_index_0_100",
    "社会适应(0-100)":"social_index_0_100",
    "综合健康指数(0-100)":"overall_index_0_100",
    "出生年":"birth_year",
    "年龄": f"age_{YEAR}",
}
out_dta = merged.rename(columns=dta_map).copy()
var_labels = {
    "ID":"ID","householdID":"householdID","communityID":"communityID",
    "body_index_0_100":"身体健康(0-100)","mental_index_0_100":"心理健康(0-100)",
    "social_index_0_100":"社会适应(0-100)","overall_index_0_100":"综合健康指数(0-100)",
    "birth_year":"出生年", f"age_{YEAR}":f"年龄({YEAR}-出生年)",
    "province":"省","city":"市","urban_nbs":"国家统计局城乡","areatype":"地区类型",
}
write_dta_smart(out_dta, OUT_DTA, var_labels=var_labels)
print("DTA  ->", OUT_DTA)

# =============================================================================
n_all = len(merged)
n_region = merged[["province","city"]].notna().any(axis=1).sum() if {"province","city"}.issubset(merged.columns) else 0
n_age = merged["年龄"].notna().sum() if "年龄" in merged.columns else 0
print("[INFO] Notebook progress message.")


# ------------------------------------------------------------------------------
# Notebook cell 4
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import re
import inspect
import numpy as np
import pandas as pd
from pathlib import Path

# =============================================================================
YEAR = 2013
ROOT = Path(fr"E:\impact_assessment_child_order\older\health\{YEAR}")
CHI_XLSX = ROOT / f"{YEAR}_综合健康指数.xlsx"
AGE_DTA  = ROOT / f"{YEAR}_age_region.dta"
AGE_XLSX = ROOT / f"{YEAR}_age_region.xlsx"
OUT_DTA  = ROOT / f"{YEAR}_chi_result.dta"
OUT_XLSX = ROOT / f"{YEAR}_chi_result.xlsx"

# Original notebook comment normalized for the public code archive.
CODE_XLS = Path(r"E:\impact_assessment_child_order\older\编码.xls")

# =============================================================================
def _clean_to_str(s: pd.Series) -> pd.Series:
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = pd.Series(s, dtype="object")
    m = s.isna()
    sc = s[~m].astype(str).str.strip()
    sc = sc.str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = sc
    s.loc[m] = np.nan
    return s

def canon_id_fixed(s: pd.Series, width: int) -> pd.Series:
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = _clean_to_str(s)
    m = s.notna()
    s.loc[m] = s.loc[m].astype(str).str.zfill(width)
    return s

def canon_pid_11(s: pd.Series) -> pd.Series:
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = _clean_to_str(s)
    m = s.notna()
    t = s.copy()
    t.loc[m] = t.loc[m].str.replace(r"\D", "", regex=True)
    t = t.where(t.str.len() > 0, np.nan)                        # Original notebook comment normalized for the public code archive.
    t = t.where(t.isna(), t.str[-11:].str.zfill(11))            # Original notebook comment normalized for the public code archive.
    return t.astype("object")

def pick_col(df: pd.DataFrame, candidates):
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    low = {c.lower(): c for c in df.columns}
    for n in candidates:
        if n and n.lower() in low:
            return low[n.lower()]
    for n in candidates:
        for c in df.columns:
            if n and n.lower() in c.lower():
                return c
    return None

def read_age_table():
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if AGE_DTA.exists():
        try:
            import pyreadstat
            df, _ = pyreadstat.read_dta(str(AGE_DTA), apply_value_formats=False)
            print("Read age-region (pyreadstat):", AGE_DTA)
            return df
        except Exception as e:
            print("[INFO] Notebook progress message.", e)
            try:
                return pd.read_stata(AGE_DTA, convert_categoricals=False)
            except Exception as e2:
                print("[INFO] Notebook progress message.", e2)
    df = pd.read_excel(AGE_XLSX)
    print("Read age-region (xlsx):", AGE_XLSX)
    return df

def write_dta_smart(df: pd.DataFrame, out_path: Path, var_labels=None):
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Original notebook comment normalized for the public code archive.
    cols = list(df.columns)
    new, used = [], set()
    for c in cols:
        base = re.sub(r"[^0-9A-Za-z_]", "_", str(c))[:32]
        name, i = base, 1
        while name in used:
            suf = f"_{i}"
            name = base[:32-len(suf)] + suf
            i += 1
        new.append(name); used.add(name)
    if new != cols:
        df = df.rename(columns=dict(zip(cols, new)))

    try:
        import pyreadstat
        last = None
        for ver in (119, 118):
            try:
                kwargs = {"version": ver}
                if var_labels:
                    try:
                        if "variable_labels" in inspect.signature(pyreadstat.write_dta).parameters:
                            kwargs["variable_labels"] = {k: var_labels.get(k, "") for k in df.columns}
                    except Exception:
                        pass
                pyreadstat.write_dta(df, str(out_path), **kwargs)
                print(f"Saved DTA via pyreadstat v{ver} ->", out_path)
                return
            except Exception as e:
                last = e
        print("[INFO] Notebook progress message.", last)
    except Exception as e:
        print("[INFO] Notebook progress message.", e)

    try:
        df.to_stata(out_path, write_index=False, version=118)
        print("Saved DTA via pandas v118 (UTF-8) ->", out_path)
        return
    except Exception as e:
        print("[INFO] Notebook progress message.", e)

    df2 = df.copy()
    for c in df2.select_dtypes(include=["object"]).columns:
        df2[c] = df2[c].astype(str).str.encode("latin-1","ignore").str.decode("latin-1")
    df2.to_stata(out_path, write_index=False, version=117)
    print("Saved DTA via pandas v117 (latin-1) ->", out_path)

# Original notebook comment normalized for the public code archive.
PROV_ALIAS = {
    "内蒙古自治区": "内蒙古",
    "广西壮族自治区": "广西",
    "西藏自治区": "西藏",
    "宁夏回族自治区": "宁夏",
    "新疆维吾尔自治区": "新疆",
    "香港特别行政区": "香港",
    "澳门特别行政区": "澳门",
}
CITY_ALIAS = {
    "襄樊": "襄阳", "襄樊市": "襄阳",
    "海东地区": "海东", "海东市": "海东",
    "阿克苏地区": "阿克苏",
    "巢湖市": "巢湖",
    # Original notebook comment normalized for the public code archive.
}
# City-level processing note.
DELEGATED_TO = {
    ("安徽", "巢湖"): ("安徽", "合肥"),   # Original notebook comment normalized for the public code archive.
}

def norm_province(x: pd.Series) -> pd.Series:
    s = _clean_to_str(x).fillna("")
    s = s.replace(PROV_ALIAS)
    s = s.str.replace(r"(省|市|特别行政区|自治区)$", "", regex=True)
    return s.str.strip()

def norm_city(x: pd.Series) -> pd.Series:
    s = _clean_to_str(x).fillna("")
    s = s.replace(CITY_ALIAS)
    s = s.str.replace(r"(市|地区|盟|自治州|林区|矿区|新区)$", "", regex=True)
    s = s.str.replace(r"市辖区$", "", regex=True)
    return s.str.strip()

def read_city_codes(path: Path) -> pd.DataFrame:
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if not path.exists():
        print("[INFO] Notebook progress message.")
        return pd.DataFrame(columns=["province","city","city_code","prov_norm","city_norm"])
    code_raw = pd.read_excel(path)
    prov_col = pick_col(code_raw, ["province","省","省份"])
    city_col = pick_col(code_raw, ["city","市","地市","地级市","prefecture"])
    code_col = pick_col(code_raw, ["code","编码","代码","citycode","行政区划代码","adcode","ad_code"])
    if city_col is None or code_col is None:
        print("[INFO] Notebook progress message.")
        return pd.DataFrame(columns=["province","city","city_code","prov_norm","city_norm"])

    codes = pd.DataFrame({
        "province": _clean_to_str(code_raw[prov_col]) if prov_col else pd.Series(np.nan, index=code_raw.index, dtype="object"),
        "city":     _clean_to_str(code_raw[city_col]),
        "city_code": _clean_to_str(code_raw[code_col]),
    })
    codes = codes[codes["city"].notna()].copy()
    codes["city_code"] = codes["city_code"].str.extract(r"(\d+)", expand=False)
    m = codes["city_code"].notna()
    codes.loc[m, "city_code"] = codes.loc[m, "city_code"].astype(str).str.zfill(6)
    codes["prov_norm"] = norm_province(codes["province"]) if "province" in codes.columns else ""
    codes["city_norm"] = norm_city(codes["city"])
    codes = codes.drop_duplicates(subset=["prov_norm","city_norm"])
    print("[INFO] Notebook progress message.")
    return codes

# =============================================================================
chi = pd.read_excel(CHI_XLSX)
print("Read chi xlsx:", CHI_XLSX)
age_all = read_age_table()
codes   = read_city_codes(CODE_XLS)

# =============================================================================
# Original notebook comment normalized for the public code archive.
for key, w in (("householdID",9), ("communityID",7)):
    if key in chi.columns:     chi[key]     = canon_id_fixed(chi[key], w)
    if key in age_all.columns: age_all[key] = canon_id_fixed(age_all[key], w)

# Original notebook comment normalized for the public code archive.
if "ID" in chi.columns:
    chi["ID"] = canon_pid_11(chi["ID"])
if "ID" in age_all.columns:
    age_all["ID"] = canon_pid_11(age_all["ID"])

# =============================================================================
if "出生年" not in age_all.columns and "birth_year" in age_all.columns:
    age_all["出生年"] = age_all["birth_year"]
age_col_en = f"age_{YEAR}"
if "年龄" not in age_all.columns and age_col_en in age_all.columns:
    age_all["年龄"] = age_all[age_col_en]

# =============================================================================
# Original notebook comment normalized for the public code archive.
age_id = age_all[[c for c in ["ID","出生年","年龄"] if c in age_all.columns]].drop_duplicates(subset=["ID"])
chi1 = chi.merge(age_id, on="ID", how="left")

# Original notebook comment normalized for the public code archive.
region_cols = [c for c in ["communityID","province","city","urban_nbs","areatype"] if c in age_all.columns]
age_region = age_all[region_cols].drop_duplicates(subset=["communityID"]) if "communityID" in region_cols else pd.DataFrame()
merged = chi1.merge(age_region, on="communityID", how="left") if not age_region.empty else chi1.copy()

# =============================================================================
if not codes.empty and {"city"}.issubset(merged.columns):
    merged["prov_norm"] = norm_province(merged["province"]) if "province" in merged.columns else ""
    merged["city_norm"] = norm_city(merged["city"])

    # Archived notebook metadata.
    merged = merged.merge(codes[["prov_norm","city_norm","city_code"]],
                          on=["prov_norm","city_norm"], how="left")
    matched_pc = merged["city_code"].notna().sum()

    # Archived notebook metadata.
    need = merged["city_code"].isna()
    if need.any():
        uniq_city = (codes.groupby("city_norm")["city_code"].nunique().reset_index())
        uniq_city = uniq_city[uniq_city["city_code"]==1]["city_norm"]
        codes_city_only = codes[codes["city_norm"].isin(uniq_city)][["city_norm","city_code"]].drop_duplicates("city_norm")
        fill = merged.loc[need, ["city_norm"]].merge(codes_city_only, on="city_norm", how="left")["city_code"]
        merged.loc[need, "city_code"] = fill.values

    # Archived notebook metadata.
    if "city_code" in merged.columns:
        code_map = codes.set_index(["prov_norm","city_norm"])["city_code"].to_dict()
        filled = 0
        for (prov_from, city_from), (prov_to, city_to) in DELEGATED_TO.items():
            mask = merged["city_code"].isna() & (merged["prov_norm"]==prov_from) & (merged["city_norm"]==city_from)
            if mask.any():
                code_to = code_map.get((prov_to, city_to))
                if pd.notna(code_to):
                    merged.loc[mask, "city_code"] = str(code_to).zfill(6)
                    filled += int(mask.sum())
        if filled:
            print("[INFO] Notebook progress message.")

    matched_total = merged["city_code"].notna().sum()
    print("[INFO] Notebook progress message.")

# =============================================================================
order_front = [c for c in ["ID","householdID","communityID"] if c in merged.columns]
four_idx = [c for c in ["身体健康(0-100)","心理健康(0-100)","社会适应(0-100)","综合健康指数(0-100)"] if c in merged.columns]
age_cols = [c for c in ["出生年","年龄"] if c in merged.columns]
region_cols_final = [c for c in ["province","city","city_code","urban_nbs","areatype"] if c in merged.columns]
drop_helper = [c for c in ["prov_norm","city_norm"] if c in merged.columns]
other_cols = [c for c in merged.columns if c not in (order_front+four_idx+age_cols+region_cols_final+drop_helper)]
merged = merged[order_front + four_idx + age_cols + region_cols_final + other_cols]

# =============================================================================
# Excel
merged.to_excel(OUT_XLSX, index=False)
print("Excel ->", OUT_XLSX)

# Original notebook comment normalized for the public code archive.
dta_map = {
    "身体健康(0-100)":"body_index_0_100",
    "心理健康(0-100)":"mental_index_0_100",
    "社会适应(0-100)":"social_index_0_100",
    "综合健康指数(0-100)":"overall_index_0_100",
    "出生年":"birth_year",
    "年龄": f"age_{YEAR}",
}
out_dta = merged.rename(columns=dta_map).copy()
var_labels = {
    "ID":"ID","householdID":"householdID","communityID":"communityID",
    "body_index_0_100":"身体健康(0-100)","mental_index_0_100":"心理健康(0-100)",
    "social_index_0_100":"社会适应(0-100)","overall_index_0_100":"综合健康指数(0-100)",
    "birth_year":"出生年", f"age_{YEAR}":f"年龄({YEAR}-出生年)",
    "province":"省","city":"市","city_code":"市代码",
    "urban_nbs":"国家统计局城乡","areatype":"地区类型",
}
write_dta_smart(out_dta, OUT_DTA, var_labels=var_labels)
print("DTA  ->", OUT_DTA)

# =============================================================================
OUT_GIS_XLSX = ROOT / f"{YEAR}_chi_result_forGIS.xlsx"
OUT_GIS_CSV  = ROOT / f"{YEAR}_chi_result_forGIS.csv"

gis_map = {
    "身体健康(0-100)"    : "body100",
    "心理健康(0-100)"    : "mental100",
    "社会适应(0-100)"    : "social100",
    "综合健康指数(0-100)": "overall100",
    "出生年"             : "birthyr",
    "年龄"               : "age",
    "province"           : "prov",
    "city"               : "city",
    "city_code"          : "citycode",
    "urban_nbs"          : "urban_nbs",
    "areatype"           : "areatype",
}
gis = merged.rename(columns={k:v for k,v in gis_map.items() if k in merged.columns}).copy()

if "citycode" in gis.columns:
    gis["citycode_txt"] = _clean_to_str(gis["citycode"])                               # Original notebook comment normalized for the public code archive.
    gis["citycode_int"] = pd.to_numeric(gis["citycode"], errors="coerce").astype("Int64")  # Original notebook comment normalized for the public code archive.

def arc_safe_cols(df):
    new = {}
    used = set()
    for c in df.columns:
        name = re.sub(r"[^0-9A-Za-z_]", "_", str(c))
        if re.match(r"^\d", name):
            name = "_" + name
        name = name[:30]
        base = name; i = 1
        while name in used:
            suf = f"_{i}"
            name = (base[:30-len(suf)] + suf)
            i += 1
        used.add(name); new[c] = name
    return df.rename(columns=new)

gis = arc_safe_cols(gis)
gis.to_excel(OUT_GIS_XLSX, index=False)
gis.to_csv(OUT_GIS_CSV, index=False, encoding="utf-8-sig")
print("GIS-friendly Excel ->", OUT_GIS_XLSX)
print("GIS-friendly CSV    ->", OUT_GIS_CSV)

# =============================================================================
n_all = len(merged)
n_region = merged[["province","city"]].notna().any(axis=1).sum() if {"province","city"}.issubset(merged.columns) else 0
n_age = merged["年龄"].notna().sum() if "年龄" in merged.columns else 0
print("[INFO] Notebook progress message.")




# =============================================================================
# Source notebook
# =============================================================================
# record_type : wave_step
# year        : 2015
# step        : 5
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 2
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import re
import inspect
import numpy as np
import pandas as pd
from pathlib import Path

# =============================================================================
ROOT = Path(r"E:\impact_assessment_child_order\older\health\2015")
CHI_XLSX = ROOT / "2015_综合健康指数.xlsx"
AGE_DTA  = ROOT / "2015_age_region.dta"
AGE_XLSX = ROOT / "2015_age_region.xlsx"
OUT_DTA  = ROOT / "2015_chi_result.dta"
OUT_XLSX = ROOT / "2015_chi_result.xlsx"

# =============================================================================
def _clean_to_str(s: pd.Series) -> pd.Series:
    s = pd.Series(s, dtype="object"); m = s.isna()
    sc = s[~m].astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = sc; s.loc[m] = np.nan; return s

def canon_id_fixed(s: pd.Series, width: int) -> pd.Series:
    s = _clean_to_str(s); m = s.notna(); s.loc[m] = s.loc[m].astype(str).str.zfill(width); return s

def canon_pid_11(s: pd.Series) -> pd.Series:
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = _clean_to_str(s); m = s.notna()
    t = s.copy(); t.loc[m] = t.loc[m].str.replace(r"\D", "", regex=True)
    t = t.where(t.str.len() > 0, np.nan)
    t = t.where(t.isna(), t.str[-11:].str.zfill(11))
    return t.astype("object")

def read_age_table():
    if AGE_DTA.exists():
        try:
            import pyreadstat
            df, _ = pyreadstat.read_dta(str(AGE_DTA), apply_value_formats=False)
            print("Read age-region (pyreadstat):", AGE_DTA)
            return df
        except Exception as e:
            print("[INFO] Notebook progress message.", e)
            try:
                return pd.read_stata(AGE_DTA, convert_categoricals=False)
            except Exception as e2:
                print("[INFO] Notebook progress message.", e2)
    df = pd.read_excel(AGE_XLSX)
    print("Read age-region (xlsx):", AGE_XLSX)
    return df

def write_dta_smart(df: pd.DataFrame, out_path: Path, var_labels=None):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Original notebook comment normalized for the public code archive.
    cols = list(df.columns); new, used = [], set()
    for c in cols:
        base = re.sub(r"[^0-9A-Za-z_]", "_", str(c))[:32]
        name, i = base, 1
        while name in used:
            suf = f"_{i}"; name = base[:32-len(suf)] + suf; i += 1
        new.append(name); used.add(name)
    if new != cols: df = df.rename(columns=dict(zip(cols, new)))

    # Original notebook comment normalized for the public code archive.
    try:
        import pyreadstat
        last = None
        for ver in (119, 118):
            try:
                kwargs = {"version": ver}
                if var_labels:
                    try:
                        if "variable_labels" in inspect.signature(pyreadstat.write_dta).parameters:
                            kwargs["variable_labels"] = {k: var_labels.get(k, "") for k in df.columns}
                    except Exception:
                        pass
                pyreadstat.write_dta(df, str(out_path), **kwargs)
                print(f"Saved DTA via pyreadstat v{ver} ->", out_path)
                return
            except Exception as e:
                last = e
        print("[INFO] Notebook progress message.", last)
    except Exception as e:
        print("[INFO] Notebook progress message.", e)

    # pandas v118（UTF-8）
    try:
        df.to_stata(out_path, write_index=False, version=118)
        print("Saved DTA via pandas v118 (UTF-8) ->", out_path)
        return
    except Exception as e:
        print("[INFO] Notebook progress message.", e)

    df2 = df.copy()
    for c in df2.select_dtypes(include=["object"]).columns:
        df2[c] = df2[c].astype(str).str.encode("latin-1","ignore").str.decode("latin-1")
    df2.to_stata(out_path, write_index=False, version=117)
    print("Saved DTA via pandas v117 (latin-1) ->", out_path)

# =============================================================================
chi = pd.read_excel(CHI_XLSX)
print("Read chi xlsx:", CHI_XLSX)

age_all = read_age_table()

# =============================================================================
for key, w in (("householdID",9), ("communityID",7)):
    if key in chi.columns:     chi[key]     = canon_id_fixed(chi[key], w)
    if key in age_all.columns: age_all[key] = canon_id_fixed(age_all[key], w)

# Original notebook comment normalized for the public code archive.
if "ID" in chi.columns:     chi["ID"]     = canon_pid_11(chi["ID"])
if "ID" in age_all.columns: age_all["ID"] = canon_pid_11(age_all["ID"])

# =============================================================================
if "出生年" not in age_all.columns and "birth_year" in age_all.columns:
    age_all["出生年"] = age_all["birth_year"]
if "年龄" not in age_all.columns and "age_2015" in age_all.columns:
    age_all["年龄"] = age_all["age_2015"]

# =============================================================================
# Original notebook comment normalized for the public code archive.
age_id = age_all[[c for c in ["ID","出生年","年龄"] if c in age_all.columns]].drop_duplicates(subset=["ID"])
chi1 = chi.merge(age_id, on="ID", how="left")

# Original notebook comment normalized for the public code archive.
region_cols = [c for c in ["communityID","province","city","urban_nbs","areatype"] if c in age_all.columns]
age_region = age_all[region_cols].drop_duplicates(subset=["communityID"]) if "communityID" in region_cols else pd.DataFrame()
merged = chi1.merge(age_region, on="communityID", how="left") if not age_region.empty else chi1.copy()

# =============================================================================
order_front = [c for c in ["ID","householdID","communityID"] if c in merged.columns]
four_idx = [c for c in ["身体健康(0-100)","心理健康(0-100)","社会适应(0-100)","综合健康指数(0-100)"] if c in merged.columns]
age_cols = [c for c in ["出生年","年龄"] if c in merged.columns]
region_cols_final = [c for c in ["province","city","urban_nbs","areatype"] if c in merged.columns]
other_cols = [c for c in merged.columns if c not in (order_front+four_idx+age_cols+region_cols_final)]
merged = merged[order_front + four_idx + age_cols + region_cols_final + other_cols]

# =============================================================================
# Excel
merged.to_excel(OUT_XLSX, index=False)
print("Excel ->", OUT_XLSX)

# Original notebook comment normalized for the public code archive.
dta_map = {
    "身体健康(0-100)":"body_index_0_100",
    "心理健康(0-100)":"mental_index_0_100",
    "社会适应(0-100)":"social_index_0_100",
    "综合健康指数(0-100)":"overall_index_0_100",
    "出生年":"birth_year",
    "年龄":"age_2015",
}
out_dta = merged.rename(columns=dta_map).copy()
var_labels = {
    "ID":"ID","householdID":"householdID","communityID":"communityID",
    "body_index_0_100":"身体健康(0-100)","mental_index_0_100":"心理健康(0-100)",
    "social_index_0_100":"社会适应(0-100)","overall_index_0_100":"综合健康指数(0-100)",
    "birth_year":"出生年","age_2015":"年龄(2015-出生年)",
    "province":"省","city":"市","urban_nbs":"国家统计局城乡","areatype":"地区类型",
}
write_dta_smart(out_dta, OUT_DTA, var_labels=var_labels)
print("DTA  ->", OUT_DTA)

# =============================================================================
n_all = len(merged)
n_have_region = merged[["province","city"]].notna().any(axis=1).sum() if {"province","city"}.issubset(merged.columns) else 0
n_have_age = merged["年龄"].notna().sum() if "年龄" in merged.columns else 0
print("[INFO] Notebook progress message.")


# ------------------------------------------------------------------------------
# Notebook cell 7
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import re
import inspect
import numpy as np
import pandas as pd
from pathlib import Path

# =============================================================================
YEAR = 2013
ROOT = Path(fr"E:\impact_assessment_child_order\older\health\{YEAR}")
CHI_XLSX = ROOT / f"{YEAR}_综合健康指数.xlsx"
AGE_DTA  = ROOT / f"{YEAR}_age_region.dta"
AGE_XLSX = ROOT / f"{YEAR}_age_region.xlsx"
OUT_DTA  = ROOT / f"{YEAR}_chi_result.dta"
OUT_XLSX = ROOT / f"{YEAR}_chi_result.xlsx"

# Original notebook comment normalized for the public code archive.
CODE_XLS = Path(r"E:\impact_assessment_child_order\older\编码.xls")

# =============================================================================
def _clean_to_str(s: pd.Series) -> pd.Series:
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = pd.Series(s, dtype="object")
    m = s.isna()
    sc = s[~m].astype(str).str.strip()
    sc = sc.str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = sc
    s.loc[m] = np.nan
    return s

def canon_id_fixed(s: pd.Series, width: int) -> pd.Series:
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = _clean_to_str(s)
    m = s.notna()
    s.loc[m] = s.loc[m].astype(str).str.zfill(width)
    return s

def canon_pid_11(s: pd.Series) -> pd.Series:
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = _clean_to_str(s)
    m = s.notna()
    t = s.copy()
    t.loc[m] = t.loc[m].str.replace(r"\D", "", regex=True)
    t = t.where(t.str.len() > 0, np.nan)                        # Original notebook comment normalized for the public code archive.
    t = t.where(t.isna(), t.str[-11:].str.zfill(11))            # Original notebook comment normalized for the public code archive.
    return t.astype("object")

def pick_col(df: pd.DataFrame, candidates):
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    low = {c.lower(): c for c in df.columns}
    for n in candidates:
        if n and n.lower() in low:
            return low[n.lower()]
    for n in candidates:
        for c in df.columns:
            if n and n.lower() in c.lower():
                return c
    return None

def read_age_table():
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if AGE_DTA.exists():
        try:
            import pyreadstat
            df, _ = pyreadstat.read_dta(str(AGE_DTA), apply_value_formats=False)
            print("Read age-region (pyreadstat):", AGE_DTA)
            return df
        except Exception as e:
            print("[INFO] Notebook progress message.", e)
            try:
                return pd.read_stata(AGE_DTA, convert_categoricals=False)
            except Exception as e2:
                print("[INFO] Notebook progress message.", e2)
    df = pd.read_excel(AGE_XLSX)
    print("Read age-region (xlsx):", AGE_XLSX)
    return df

def write_dta_smart(df: pd.DataFrame, out_path: Path, var_labels=None):
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Original notebook comment normalized for the public code archive.
    cols = list(df.columns)
    new, used = [], set()
    for c in cols:
        base = re.sub(r"[^0-9A-Za-z_]", "_", str(c))[:32]
        name, i = base, 1
        while name in used:
            suf = f"_{i}"
            name = base[:32-len(suf)] + suf
            i += 1
        new.append(name); used.add(name)
    if new != cols:
        df = df.rename(columns=dict(zip(cols, new)))

    try:
        import pyreadstat
        last = None
        for ver in (119, 118):
            try:
                kwargs = {"version": ver}
                if var_labels:
                    try:
                        if "variable_labels" in inspect.signature(pyreadstat.write_dta).parameters:
                            kwargs["variable_labels"] = {k: var_labels.get(k, "") for k in df.columns}
                    except Exception:
                        pass
                pyreadstat.write_dta(df, str(out_path), **kwargs)
                print(f"Saved DTA via pyreadstat v{ver} ->", out_path)
                return
            except Exception as e:
                last = e
        print("[INFO] Notebook progress message.", last)
    except Exception as e:
        print("[INFO] Notebook progress message.", e)

    try:
        df.to_stata(out_path, write_index=False, version=118)
        print("Saved DTA via pandas v118 (UTF-8) ->", out_path)
        return
    except Exception as e:
        print("[INFO] Notebook progress message.", e)

    df2 = df.copy()
    for c in df2.select_dtypes(include=["object"]).columns:
        df2[c] = df2[c].astype(str).str.encode("latin-1","ignore").str.decode("latin-1")
    df2.to_stata(out_path, write_index=False, version=117)
    print("Saved DTA via pandas v117 (latin-1) ->", out_path)

# Original notebook comment normalized for the public code archive.
PROV_ALIAS = {
    "内蒙古自治区": "内蒙古",
    "广西壮族自治区": "广西",
    "西藏自治区": "西藏",
    "宁夏回族自治区": "宁夏",
    "新疆维吾尔自治区": "新疆",
    "香港特别行政区": "香港",
    "澳门特别行政区": "澳门",
}
CITY_ALIAS = {
    "襄樊": "襄阳", "襄樊市": "襄阳",
    "海东地区": "海东", "海东市": "海东",
    "阿克苏地区": "阿克苏",
    "巢湖市": "巢湖",
    # Original notebook comment normalized for the public code archive.
}
# City-level processing note.
DELEGATED_TO = {
    ("安徽", "巢湖"): ("安徽", "合肥"),   # Original notebook comment normalized for the public code archive.
}

def norm_province(x: pd.Series) -> pd.Series:
    s = _clean_to_str(x).fillna("")
    s = s.replace(PROV_ALIAS)
    s = s.str.replace(r"(省|市|特别行政区|自治区)$", "", regex=True)
    return s.str.strip()

def norm_city(x: pd.Series) -> pd.Series:
    s = _clean_to_str(x).fillna("")
    s = s.replace(CITY_ALIAS)
    s = s.str.replace(r"(市|地区|盟|自治州|林区|矿区|新区)$", "", regex=True)
    s = s.str.replace(r"市辖区$", "", regex=True)
    return s.str.strip()

def read_city_codes(path: Path) -> pd.DataFrame:
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if not path.exists():
        print("[INFO] Notebook progress message.")
        return pd.DataFrame(columns=["province","city","city_code","prov_norm","city_norm"])
    code_raw = pd.read_excel(path)
    prov_col = pick_col(code_raw, ["province","省","省份"])
    city_col = pick_col(code_raw, ["city","市","地市","地级市","prefecture"])
    code_col = pick_col(code_raw, ["code","编码","代码","citycode","行政区划代码","adcode","ad_code"])
    if city_col is None or code_col is None:
        print("[INFO] Notebook progress message.")
        return pd.DataFrame(columns=["province","city","city_code","prov_norm","city_norm"])

    codes = pd.DataFrame({
        "province": _clean_to_str(code_raw[prov_col]) if prov_col else pd.Series(np.nan, index=code_raw.index, dtype="object"),
        "city":     _clean_to_str(code_raw[city_col]),
        "city_code": _clean_to_str(code_raw[code_col]),
    })
    codes = codes[codes["city"].notna()].copy()
    codes["city_code"] = codes["city_code"].str.extract(r"(\d+)", expand=False)
    m = codes["city_code"].notna()
    codes.loc[m, "city_code"] = codes.loc[m, "city_code"].astype(str).str.zfill(6)
    codes["prov_norm"] = norm_province(codes["province"]) if "province" in codes.columns else ""
    codes["city_norm"] = norm_city(codes["city"])
    codes = codes.drop_duplicates(subset=["prov_norm","city_norm"])
    print("[INFO] Notebook progress message.")
    return codes

# =============================================================================
chi = pd.read_excel(CHI_XLSX)
print("Read chi xlsx:", CHI_XLSX)
age_all = read_age_table()
codes   = read_city_codes(CODE_XLS)

# =============================================================================
# Original notebook comment normalized for the public code archive.
for key, w in (("householdID",9), ("communityID",7)):
    if key in chi.columns:     chi[key]     = canon_id_fixed(chi[key], w)
    if key in age_all.columns: age_all[key] = canon_id_fixed(age_all[key], w)

# Original notebook comment normalized for the public code archive.
if "ID" in chi.columns:
    chi["ID"] = canon_pid_11(chi["ID"])
if "ID" in age_all.columns:
    age_all["ID"] = canon_pid_11(age_all["ID"])

# =============================================================================
if "出生年" not in age_all.columns and "birth_year" in age_all.columns:
    age_all["出生年"] = age_all["birth_year"]
age_col_en = f"age_{YEAR}"
if "年龄" not in age_all.columns and age_col_en in age_all.columns:
    age_all["年龄"] = age_all[age_col_en]

# =============================================================================
# Original notebook comment normalized for the public code archive.
age_id = age_all[[c for c in ["ID","出生年","年龄"] if c in age_all.columns]].drop_duplicates(subset=["ID"])
chi1 = chi.merge(age_id, on="ID", how="left")

# Original notebook comment normalized for the public code archive.
region_cols = [c for c in ["communityID","province","city","urban_nbs","areatype"] if c in age_all.columns]
age_region = age_all[region_cols].drop_duplicates(subset=["communityID"]) if "communityID" in region_cols else pd.DataFrame()
merged = chi1.merge(age_region, on="communityID", how="left") if not age_region.empty else chi1.copy()

# =============================================================================
if not codes.empty and {"city"}.issubset(merged.columns):
    merged["prov_norm"] = norm_province(merged["province"]) if "province" in merged.columns else ""
    merged["city_norm"] = norm_city(merged["city"])

    # Archived notebook metadata.
    merged = merged.merge(codes[["prov_norm","city_norm","city_code"]],
                          on=["prov_norm","city_norm"], how="left")
    matched_pc = merged["city_code"].notna().sum()

    # Archived notebook metadata.
    need = merged["city_code"].isna()
    if need.any():
        uniq_city = (codes.groupby("city_norm")["city_code"].nunique().reset_index())
        uniq_city = uniq_city[uniq_city["city_code"]==1]["city_norm"]
        codes_city_only = codes[codes["city_norm"].isin(uniq_city)][["city_norm","city_code"]].drop_duplicates("city_norm")
        fill = merged.loc[need, ["city_norm"]].merge(codes_city_only, on="city_norm", how="left")["city_code"]
        merged.loc[need, "city_code"] = fill.values

    # Archived notebook metadata.
    if "city_code" in merged.columns:
        code_map = codes.set_index(["prov_norm","city_norm"])["city_code"].to_dict()
        filled = 0
        for (prov_from, city_from), (prov_to, city_to) in DELEGATED_TO.items():
            mask = merged["city_code"].isna() & (merged["prov_norm"]==prov_from) & (merged["city_norm"]==city_from)
            if mask.any():
                code_to = code_map.get((prov_to, city_to))
                if pd.notna(code_to):
                    merged.loc[mask, "city_code"] = str(code_to).zfill(6)
                    filled += int(mask.sum())
        if filled:
            print("[INFO] Notebook progress message.")

    matched_total = merged["city_code"].notna().sum()
    print("[INFO] Notebook progress message.")

# =============================================================================
order_front = [c for c in ["ID","householdID","communityID"] if c in merged.columns]
four_idx = [c for c in ["身体健康(0-100)","心理健康(0-100)","社会适应(0-100)","综合健康指数(0-100)"] if c in merged.columns]
age_cols = [c for c in ["出生年","年龄"] if c in merged.columns]
region_cols_final = [c for c in ["province","city","city_code","urban_nbs","areatype"] if c in merged.columns]
drop_helper = [c for c in ["prov_norm","city_norm"] if c in merged.columns]
other_cols = [c for c in merged.columns if c not in (order_front+four_idx+age_cols+region_cols_final+drop_helper)]
merged = merged[order_front + four_idx + age_cols + region_cols_final + other_cols]

# =============================================================================
# Excel
merged.to_excel(OUT_XLSX, index=False)
print("Excel ->", OUT_XLSX)

# Original notebook comment normalized for the public code archive.
dta_map = {
    "身体健康(0-100)":"body_index_0_100",
    "心理健康(0-100)":"mental_index_0_100",
    "社会适应(0-100)":"social_index_0_100",
    "综合健康指数(0-100)":"overall_index_0_100",
    "出生年":"birth_year",
    "年龄": f"age_{YEAR}",
}
out_dta = merged.rename(columns=dta_map).copy()
var_labels = {
    "ID":"ID","householdID":"householdID","communityID":"communityID",
    "body_index_0_100":"身体健康(0-100)","mental_index_0_100":"心理健康(0-100)",
    "social_index_0_100":"社会适应(0-100)","overall_index_0_100":"综合健康指数(0-100)",
    "birth_year":"出生年", f"age_{YEAR}":f"年龄({YEAR}-出生年)",
    "province":"省","city":"市","city_code":"市代码",
    "urban_nbs":"国家统计局城乡","areatype":"地区类型",
}
write_dta_smart(out_dta, OUT_DTA, var_labels=var_labels)
print("DTA  ->", OUT_DTA)

# =============================================================================
OUT_GIS_XLSX = ROOT / f"{YEAR}_chi_result_forGIS.xlsx"
OUT_GIS_CSV  = ROOT / f"{YEAR}_chi_result_forGIS.csv"

gis_map = {
    "身体健康(0-100)"    : "body100",
    "心理健康(0-100)"    : "mental100",
    "社会适应(0-100)"    : "social100",
    "综合健康指数(0-100)": "overall100",
    "出生年"             : "birthyr",
    "年龄"               : "age",
    "province"           : "prov",
    "city"               : "city",
    "city_code"          : "citycode",
    "urban_nbs"          : "urban_nbs",
    "areatype"           : "areatype",
}
gis = merged.rename(columns={k:v for k,v in gis_map.items() if k in merged.columns}).copy()

if "citycode" in gis.columns:
    gis["citycode_txt"] = _clean_to_str(gis["citycode"])                               # Original notebook comment normalized for the public code archive.
    gis["citycode_int"] = pd.to_numeric(gis["citycode"], errors="coerce").astype("Int64")  # Original notebook comment normalized for the public code archive.

def arc_safe_cols(df):
    new = {}
    used = set()
    for c in df.columns:
        name = re.sub(r"[^0-9A-Za-z_]", "_", str(c))
        if re.match(r"^\d", name):
            name = "_" + name
        name = name[:30]
        base = name; i = 1
        while name in used:
            suf = f"_{i}"
            name = (base[:30-len(suf)] + suf)
            i += 1
        used.add(name); new[c] = name
    return df.rename(columns=new)

gis = arc_safe_cols(gis)
gis.to_excel(OUT_GIS_XLSX, index=False)
gis.to_csv(OUT_GIS_CSV, index=False, encoding="utf-8-sig")
print("GIS-friendly Excel ->", OUT_GIS_XLSX)
print("GIS-friendly CSV    ->", OUT_GIS_CSV)

# =============================================================================
n_all = len(merged)
n_region = merged[["province","city"]].notna().any(axis=1).sum() if {"province","city"}.issubset(merged.columns) else 0
n_age = merged["年龄"].notna().sum() if "年龄" in merged.columns else 0
print("[INFO] Notebook progress message.")


# ------------------------------------------------------------------------------
# Notebook cell 8
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import re
import inspect
import numpy as np
import pandas as pd
from pathlib import Path

# =============================================================================
YEAR = 2015
ROOT = Path(fr"E:\impact_assessment_child_order\older\health\{YEAR}")
CHI_XLSX = ROOT / f"{YEAR}_综合健康指数.xlsx"
AGE_DTA  = ROOT / f"{YEAR}_age_region.dta"
AGE_XLSX = ROOT / f"{YEAR}_age_region.xlsx"
OUT_DTA  = ROOT / f"{YEAR}_chi_result.dta"
OUT_XLSX = ROOT / f"{YEAR}_chi_result.xlsx"

# Original notebook comment normalized for the public code archive.
CODE_XLS = Path(r"E:\impact_assessment_child_order\older\编码.xls")

# =============================================================================
def _clean_to_str(s: pd.Series) -> pd.Series:
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = pd.Series(s, dtype="object")
    m = s.isna()
    sc = s[~m].astype(str).str.strip()
    sc = sc.str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = sc
    s.loc[m] = np.nan
    return s

def canon_id_fixed(s: pd.Series, width: int) -> pd.Series:
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = _clean_to_str(s)
    m = s.notna()
    s.loc[m] = s.loc[m].astype(str).str.zfill(width)
    return s

def canon_pid_11(s: pd.Series) -> pd.Series:
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = _clean_to_str(s)
    m = s.notna()
    t = s.copy()
    t.loc[m] = t.loc[m].str.replace(r"\D", "", regex=True)
    t = t.where(t.str.len() > 0, np.nan)                        # Original notebook comment normalized for the public code archive.
    t = t.where(t.isna(), t.str[-11:].str.zfill(11))            # Original notebook comment normalized for the public code archive.
    return t.astype("object")

def pick_col(df: pd.DataFrame, candidates):
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    low = {c.lower(): c for c in df.columns}
    for n in candidates:
        if n and n.lower() in low:
            return low[n.lower()]
    for n in candidates:
        for c in df.columns:
            if n and n.lower() in c.lower():
                return c
    return None

def read_age_table():
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if AGE_DTA.exists():
        try:
            import pyreadstat
            df, _ = pyreadstat.read_dta(str(AGE_DTA), apply_value_formats=False)
            print("Read age-region (pyreadstat):", AGE_DTA)
            return df
        except Exception as e:
            print("[INFO] Notebook progress message.", e)
            try:
                return pd.read_stata(AGE_DTA, convert_categoricals=False)
            except Exception as e2:
                print("[INFO] Notebook progress message.", e2)
    df = pd.read_excel(AGE_XLSX)
    print("Read age-region (xlsx):", AGE_XLSX)
    return df

def write_dta_smart(df: pd.DataFrame, out_path: Path, var_labels=None):
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Original notebook comment normalized for the public code archive.
    cols = list(df.columns)
    new, used = [], set()
    for c in cols:
        base = re.sub(r"[^0-9A-Za-z_]", "_", str(c))[:32]
        name, i = base, 1
        while name in used:
            suf = f"_{i}"
            name = base[:32-len(suf)] + suf
            i += 1
        new.append(name); used.add(name)
    if new != cols:
        df = df.rename(columns=dict(zip(cols, new)))

    try:
        import pyreadstat
        last = None
        for ver in (119, 118):
            try:
                kwargs = {"version": ver}
                if var_labels:
                    try:
                        if "variable_labels" in inspect.signature(pyreadstat.write_dta).parameters:
                            kwargs["variable_labels"] = {k: var_labels.get(k, "") for k in df.columns}
                    except Exception:
                        pass
                pyreadstat.write_dta(df, str(out_path), **kwargs)
                print(f"Saved DTA via pyreadstat v{ver} ->", out_path)
                return
            except Exception as e:
                last = e
        print("[INFO] Notebook progress message.", last)
    except Exception as e:
        print("[INFO] Notebook progress message.", e)

    try:
        df.to_stata(out_path, write_index=False, version=118)
        print("Saved DTA via pandas v118 (UTF-8) ->", out_path)
        return
    except Exception as e:
        print("[INFO] Notebook progress message.", e)

    df2 = df.copy()
    for c in df2.select_dtypes(include=["object"]).columns:
        df2[c] = df2[c].astype(str).str.encode("latin-1","ignore").str.decode("latin-1")
    df2.to_stata(out_path, write_index=False, version=117)
    print("Saved DTA via pandas v117 (latin-1) ->", out_path)

# Original notebook comment normalized for the public code archive.
PROV_ALIAS = {
    "内蒙古自治区": "内蒙古",
    "广西壮族自治区": "广西",
    "西藏自治区": "西藏",
    "宁夏回族自治区": "宁夏",
    "新疆维吾尔自治区": "新疆",
    "香港特别行政区": "香港",
    "澳门特别行政区": "澳门",
}
CITY_ALIAS = {
    "襄樊": "襄阳", "襄樊市": "襄阳",
    "海东地区": "海东", "海东市": "海东",
    "阿克苏地区": "阿克苏",
    "巢湖市": "巢湖",
    # Original notebook comment normalized for the public code archive.
}
# City-level processing note.
DELEGATED_TO = {
    ("安徽", "巢湖"): ("安徽", "合肥"),   # Original notebook comment normalized for the public code archive.
}

def norm_province(x: pd.Series) -> pd.Series:
    s = _clean_to_str(x).fillna("")
    s = s.replace(PROV_ALIAS)
    s = s.str.replace(r"(省|市|特别行政区|自治区)$", "", regex=True)
    return s.str.strip()

def norm_city(x: pd.Series) -> pd.Series:
    s = _clean_to_str(x).fillna("")
    s = s.replace(CITY_ALIAS)
    s = s.str.replace(r"(市|地区|盟|自治州|林区|矿区|新区)$", "", regex=True)
    s = s.str.replace(r"市辖区$", "", regex=True)
    return s.str.strip()

def read_city_codes(path: Path) -> pd.DataFrame:
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if not path.exists():
        print("[INFO] Notebook progress message.")
        return pd.DataFrame(columns=["province","city","city_code","prov_norm","city_norm"])
    code_raw = pd.read_excel(path)
    prov_col = pick_col(code_raw, ["province","省","省份"])
    city_col = pick_col(code_raw, ["city","市","地市","地级市","prefecture"])
    code_col = pick_col(code_raw, ["code","编码","代码","citycode","行政区划代码","adcode","ad_code"])
    if city_col is None or code_col is None:
        print("[INFO] Notebook progress message.")
        return pd.DataFrame(columns=["province","city","city_code","prov_norm","city_norm"])

    codes = pd.DataFrame({
        "province": _clean_to_str(code_raw[prov_col]) if prov_col else pd.Series(np.nan, index=code_raw.index, dtype="object"),
        "city":     _clean_to_str(code_raw[city_col]),
        "city_code": _clean_to_str(code_raw[code_col]),
    })
    codes = codes[codes["city"].notna()].copy()
    codes["city_code"] = codes["city_code"].str.extract(r"(\d+)", expand=False)
    m = codes["city_code"].notna()
    codes.loc[m, "city_code"] = codes.loc[m, "city_code"].astype(str).str.zfill(6)
    codes["prov_norm"] = norm_province(codes["province"]) if "province" in codes.columns else ""
    codes["city_norm"] = norm_city(codes["city"])
    codes = codes.drop_duplicates(subset=["prov_norm","city_norm"])
    print("[INFO] Notebook progress message.")
    return codes

# =============================================================================
chi = pd.read_excel(CHI_XLSX)
print("Read chi xlsx:", CHI_XLSX)
age_all = read_age_table()
codes   = read_city_codes(CODE_XLS)

# =============================================================================
# Original notebook comment normalized for the public code archive.
for key, w in (("householdID",9), ("communityID",7)):
    if key in chi.columns:     chi[key]     = canon_id_fixed(chi[key], w)
    if key in age_all.columns: age_all[key] = canon_id_fixed(age_all[key], w)

# Original notebook comment normalized for the public code archive.
if "ID" in chi.columns:
    chi["ID"] = canon_pid_11(chi["ID"])
if "ID" in age_all.columns:
    age_all["ID"] = canon_pid_11(age_all["ID"])

# =============================================================================
if "出生年" not in age_all.columns and "birth_year" in age_all.columns:
    age_all["出生年"] = age_all["birth_year"]
age_col_en = f"age_{YEAR}"
if "年龄" not in age_all.columns and age_col_en in age_all.columns:
    age_all["年龄"] = age_all[age_col_en]

# =============================================================================
# Original notebook comment normalized for the public code archive.
age_id = age_all[[c for c in ["ID","出生年","年龄"] if c in age_all.columns]].drop_duplicates(subset=["ID"])
chi1 = chi.merge(age_id, on="ID", how="left")

# Original notebook comment normalized for the public code archive.
region_cols = [c for c in ["communityID","province","city","urban_nbs","areatype"] if c in age_all.columns]
age_region = age_all[region_cols].drop_duplicates(subset=["communityID"]) if "communityID" in region_cols else pd.DataFrame()
merged = chi1.merge(age_region, on="communityID", how="left") if not age_region.empty else chi1.copy()

# =============================================================================
if not codes.empty and {"city"}.issubset(merged.columns):
    merged["prov_norm"] = norm_province(merged["province"]) if "province" in merged.columns else ""
    merged["city_norm"] = norm_city(merged["city"])

    # Archived notebook metadata.
    merged = merged.merge(codes[["prov_norm","city_norm","city_code"]],
                          on=["prov_norm","city_norm"], how="left")
    matched_pc = merged["city_code"].notna().sum()

    # Archived notebook metadata.
    need = merged["city_code"].isna()
    if need.any():
        uniq_city = (codes.groupby("city_norm")["city_code"].nunique().reset_index())
        uniq_city = uniq_city[uniq_city["city_code"]==1]["city_norm"]
        codes_city_only = codes[codes["city_norm"].isin(uniq_city)][["city_norm","city_code"]].drop_duplicates("city_norm")
        fill = merged.loc[need, ["city_norm"]].merge(codes_city_only, on="city_norm", how="left")["city_code"]
        merged.loc[need, "city_code"] = fill.values

    # Archived notebook metadata.
    if "city_code" in merged.columns:
        code_map = codes.set_index(["prov_norm","city_norm"])["city_code"].to_dict()
        filled = 0
        for (prov_from, city_from), (prov_to, city_to) in DELEGATED_TO.items():
            mask = merged["city_code"].isna() & (merged["prov_norm"]==prov_from) & (merged["city_norm"]==city_from)
            if mask.any():
                code_to = code_map.get((prov_to, city_to))
                if pd.notna(code_to):
                    merged.loc[mask, "city_code"] = str(code_to).zfill(6)
                    filled += int(mask.sum())
        if filled:
            print("[INFO] Notebook progress message.")

    matched_total = merged["city_code"].notna().sum()
    print("[INFO] Notebook progress message.")

# =============================================================================
order_front = [c for c in ["ID","householdID","communityID"] if c in merged.columns]
four_idx = [c for c in ["身体健康(0-100)","心理健康(0-100)","社会适应(0-100)","综合健康指数(0-100)"] if c in merged.columns]
age_cols = [c for c in ["出生年","年龄"] if c in merged.columns]
region_cols_final = [c for c in ["province","city","city_code","urban_nbs","areatype"] if c in merged.columns]
drop_helper = [c for c in ["prov_norm","city_norm"] if c in merged.columns]
other_cols = [c for c in merged.columns if c not in (order_front+four_idx+age_cols+region_cols_final+drop_helper)]
merged = merged[order_front + four_idx + age_cols + region_cols_final + other_cols]

# =============================================================================
# Excel
merged.to_excel(OUT_XLSX, index=False)
print("Excel ->", OUT_XLSX)

# Original notebook comment normalized for the public code archive.
dta_map = {
    "身体健康(0-100)":"body_index_0_100",
    "心理健康(0-100)":"mental_index_0_100",
    "社会适应(0-100)":"social_index_0_100",
    "综合健康指数(0-100)":"overall_index_0_100",
    "出生年":"birth_year",
    "年龄": f"age_{YEAR}",
}
out_dta = merged.rename(columns=dta_map).copy()
var_labels = {
    "ID":"ID","householdID":"householdID","communityID":"communityID",
    "body_index_0_100":"身体健康(0-100)","mental_index_0_100":"心理健康(0-100)",
    "social_index_0_100":"社会适应(0-100)","overall_index_0_100":"综合健康指数(0-100)",
    "birth_year":"出生年", f"age_{YEAR}":f"年龄({YEAR}-出生年)",
    "province":"省","city":"市","city_code":"市代码",
    "urban_nbs":"国家统计局城乡","areatype":"地区类型",
}
write_dta_smart(out_dta, OUT_DTA, var_labels=var_labels)
print("DTA  ->", OUT_DTA)

# =============================================================================
OUT_GIS_XLSX = ROOT / f"{YEAR}_chi_result_forGIS.xlsx"
OUT_GIS_CSV  = ROOT / f"{YEAR}_chi_result_forGIS.csv"

gis_map = {
    "身体健康(0-100)"    : "body100",
    "心理健康(0-100)"    : "mental100",
    "社会适应(0-100)"    : "social100",
    "综合健康指数(0-100)": "overall100",
    "出生年"             : "birthyr",
    "年龄"               : "age",
    "province"           : "prov",
    "city"               : "city",
    "city_code"          : "citycode",
    "urban_nbs"          : "urban_nbs",
    "areatype"           : "areatype",
}
gis = merged.rename(columns={k:v for k,v in gis_map.items() if k in merged.columns}).copy()

if "citycode" in gis.columns:
    gis["citycode_txt"] = _clean_to_str(gis["citycode"])                               # Original notebook comment normalized for the public code archive.
    gis["citycode_int"] = pd.to_numeric(gis["citycode"], errors="coerce").astype("Int64")  # Original notebook comment normalized for the public code archive.

def arc_safe_cols(df):
    new = {}
    used = set()
    for c in df.columns:
        name = re.sub(r"[^0-9A-Za-z_]", "_", str(c))
        if re.match(r"^\d", name):
            name = "_" + name
        name = name[:30]
        base = name; i = 1
        while name in used:
            suf = f"_{i}"
            name = (base[:30-len(suf)] + suf)
            i += 1
        used.add(name); new[c] = name
    return df.rename(columns=new)

gis = arc_safe_cols(gis)
gis.to_excel(OUT_GIS_XLSX, index=False)
gis.to_csv(OUT_GIS_CSV, index=False, encoding="utf-8-sig")
print("GIS-friendly Excel ->", OUT_GIS_XLSX)
print("GIS-friendly CSV    ->", OUT_GIS_CSV)

# =============================================================================
n_all = len(merged)
n_region = merged[["province","city"]].notna().any(axis=1).sum() if {"province","city"}.issubset(merged.columns) else 0
n_age = merged["年龄"].notna().sum() if "年龄" in merged.columns else 0
print("[INFO] Notebook progress message.")




# =============================================================================
# Source notebook
# =============================================================================
# record_type : wave_step
# year        : 2018
# step        : 5
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 2
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import re
import inspect
import numpy as np
import pandas as pd
from pathlib import Path

# =============================================================================
YEAR = 2018

ROOT = Path(fr"E:\impact_assessment_child_order\older\health\{YEAR}")
CHI_XLSX = ROOT / f"{YEAR}_综合健康指数.xlsx"
AGE_DTA  = ROOT / f"{YEAR}_age_region.dta"
AGE_XLSX = ROOT / f"{YEAR}_age_region.xlsx"
OUT_DTA  = ROOT / f"{YEAR}_chi_result.dta"
OUT_XLSX = ROOT / f"{YEAR}_chi_result.xlsx"

# =============================================================================
def _clean_to_str(s: pd.Series) -> pd.Series:
    s = pd.Series(s, dtype="object")
    m = s.isna()
    t = s[~m].astype(str).str.strip()
    t = t.str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = t
    s.loc[m] = np.nan
    return s

def canon_id_fixed(s: pd.Series, width: int) -> pd.Series:
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = _clean_to_str(s)
    m = s.notna()
    s.loc[m] = s.loc[m].astype(str).str.zfill(width)
    return s

def canon_pid_11(s: pd.Series) -> pd.Series:
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = _clean_to_str(s)
    m = s.notna()
    t = s.copy()
    t.loc[m] = t.loc[m].str.replace(r"\D", "", regex=True)
    t = t.where(t.str.len() > 0, np.nan)
    t = t.where(t.isna(), t.str[-11:].str.zfill(11))
    return t.astype("object")

def find_col(df: pd.DataFrame, *candidates):
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
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

def read_age_table():
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if AGE_DTA.exists():
        try:
            import pyreadstat
            df, _ = pyreadstat.read_dta(str(AGE_DTA), apply_value_formats=False)
            print("Read age-region (pyreadstat):", AGE_DTA)
            return df
        except Exception as e:
            print("[INFO] Notebook progress message.", e)
            try:
                return pd.read_stata(AGE_DTA, convert_categoricals=False)
            except Exception as e2:
                print("[INFO] Notebook progress message.", e2)
    df = pd.read_excel(AGE_XLSX)
    print("Read age-region (xlsx):", AGE_XLSX)
    return df

def write_dta_smart(df: pd.DataFrame, out_path: Path, var_labels=None):
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Original notebook comment normalized for the public code archive.
    cols = list(df.columns); new, used = [], set()
    for c in cols:
        base = re.sub(r"[^0-9A-Za-z_]", "_", str(c))[:32]
        name, i = base, 1
        while name in used:
            suf = f"_{i}"; name = base[:32-len(suf)] + suf; i += 1
        new.append(name); used.add(name)
    if new != cols: df = df.rename(columns=dict(zip(cols, new)))
    # pyreadstat
    try:
        import pyreadstat
        last = None
        for ver in (119, 118):
            try:
                kwargs = {"version": ver}
                if var_labels:
                    try:
                        if "variable_labels" in inspect.signature(pyreadstat.write_dta).parameters:
                            kwargs["variable_labels"] = {k: var_labels.get(k, "") for k in df.columns}
                    except Exception:
                        pass
                pyreadstat.write_dta(df, str(out_path), **kwargs)
                print(f"Saved DTA via pyreadstat v{ver} ->", out_path)
                return
            except Exception as e:
                last = e
        print("[INFO] Notebook progress message.", last)
    except Exception as e:
        print("[INFO] Notebook progress message.", e)
    # pandas v118
    try:
        df.to_stata(out_path, write_index=False, version=118)
        print("Saved DTA via pandas v118 (UTF-8) ->", out_path)
        return
    except Exception as e:
        print("[INFO] Notebook progress message.", e)
    # Original notebook comment normalized for the public code archive.
    df2 = df.copy()
    for c in df2.select_dtypes(include=["object"]).columns:
        df2[c] = df2[c].astype(str).str.encode("latin-1","ignore").str.decode("latin-1")
    df2.to_stata(out_path, write_index=False, version=117)
    print("Saved DTA via pandas v117 (latin-1) ->", out_path)

# =============================================================================
chi = pd.read_excel(CHI_XLSX)
print("Read chi xlsx:", CHI_XLSX)
age_all = read_age_table()

# =============================================================================
for key, w in (("householdID",9), ("communityID",7)):
    if key in chi.columns:     chi[key]     = canon_id_fixed(chi[key], w)
    if key in age_all.columns: age_all[key] = canon_id_fixed(age_all[key], w)

# Original notebook comment normalized for the public code archive.
id_col_chi = find_col(chi, "ID", "Pid", "PID", "pid", "personid")
id_col_age = find_col(age_all, "ID", "Pid", "PID", "pid", "personid")
if id_col_chi and id_col_chi != "ID": chi = chi.rename(columns={id_col_chi: "ID"})
if id_col_age and id_col_age != "ID": age_all = age_all.rename(columns={id_col_age: "ID"})
if "ID" in chi.columns:     chi["ID"] = canon_pid_11(chi["ID"])
if "ID" in age_all.columns: age_all["ID"] = canon_pid_11(age_all["ID"])

# =============================================================================
if "出生年" not in age_all.columns and "birth_year" in age_all.columns:
    age_all["出生年"] = age_all["birth_year"]
age_en = f"age_{YEAR}"
if "年龄" not in age_all.columns and age_en in age_all.columns:
    age_all["年龄"] = age_all[age_en]

# =============================================================================
# Original notebook comment normalized for the public code archive.
age_id_cols = [c for c in ["ID","出生年","年龄"] if c in age_all.columns]
age_id = age_all[age_id_cols].drop_duplicates(subset=["ID"]) if "ID" in age_all.columns else pd.DataFrame()
chi1 = chi.merge(age_id, on="ID", how="left") if not age_id.empty else chi.copy()

# Original notebook comment normalized for the public code archive.
region_cols = [c for c in ["communityID","province","city","urban_nbs","areatype"] if c in age_all.columns]
age_region = age_all[region_cols].drop_duplicates(subset=["communityID"]) if "communityID" in region_cols else pd.DataFrame()
merged = chi1.merge(age_region, on="communityID", how="left") if not age_region.empty else chi1.copy()

# =============================================================================
front = [c for c in ["ID","householdID","communityID"] if c in merged.columns]
four  = [c for c in ["身体健康(0-100)","心理健康(0-100)","社会适应(0-100)","综合健康指数(0-100)"] if c in merged.columns]
agecs = [c for c in ["出生年","年龄"] if c in merged.columns]
regs  = [c for c in ["province","city","urban_nbs","areatype"] if c in merged.columns]
others= [c for c in merged.columns if c not in (front+four+agecs+regs)]
merged = merged[front + four + agecs + regs + others]

# =============================================================================
# Excel
merged.to_excel(OUT_XLSX, index=False)
print("\nExcel ->", OUT_XLSX)

# Original notebook comment normalized for the public code archive.
dta_map = {
    "身体健康(0-100)":"body_index_0_100",
    "心理健康(0-100)":"mental_index_0_100",
    "社会适应(0-100)":"social_index_0_100",
    "综合健康指数(0-100)":"overall_index_0_100",
    "出生年":"birth_year",
    "年龄": f"age_{YEAR}",
}
out_dta = merged.rename(columns=dta_map).copy()
var_labels = {
    "ID":"ID","householdID":"householdID","communityID":"communityID",
    "body_index_0_100":"身体健康(0-100)","mental_index_0_100":"心理健康(0-100)",
    "social_index_0_100":"社会适应(0-100)","overall_index_0_100":"综合健康指数(0-100)",
    "birth_year":"出生年", f"age_{YEAR}":f"年龄({YEAR}-出生年)",
    "province":"省","city":"市","urban_nbs":"国家统计局城乡","areatype":"地区类型",
}
write_dta_smart(out_dta, OUT_DTA, var_labels=var_labels)
print("DTA  ->", OUT_DTA)

# =============================================================================
n_all = len(merged)
n_region = merged[["province","city"]].notna().any(axis=1).sum() if {"province","city"}.issubset(merged.columns) else 0
n_age = merged["年龄"].notna().sum() if "年龄" in merged.columns else 0
print("[INFO] Notebook progress message.")


# ------------------------------------------------------------------------------
# Notebook cell 4
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import re
import inspect
import numpy as np
import pandas as pd
from pathlib import Path

# =============================================================================
YEAR = 2018
ROOT = Path(fr"E:\impact_assessment_child_order\older\health\{YEAR}")
CHI_XLSX = ROOT / f"{YEAR}_综合健康指数.xlsx"
AGE_DTA  = ROOT / f"{YEAR}_age_region.dta"
AGE_XLSX = ROOT / f"{YEAR}_age_region.xlsx"
OUT_DTA  = ROOT / f"{YEAR}_chi_result.dta"
OUT_XLSX = ROOT / f"{YEAR}_chi_result.xlsx"

# Original notebook comment normalized for the public code archive.
CODE_XLS = Path(r"E:\impact_assessment_child_order\older\编码.xls")

# =============================================================================
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

def canon_pid_11(s: pd.Series) -> pd.Series:
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = _clean_to_str(s)
    m = s.notna()
    t = s.copy()
    t.loc[m] = t.loc[m].str.replace(r"\D", "", regex=True)
    t = t.where(t.str.len() > 0, np.nan)
    t = t.where(t.isna(), t.str[-11:].str.zfill(11))
    return t.astype("object")

def pick_col(df: pd.DataFrame, candidates):
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    low = {c.lower(): c for c in df.columns}
    for n in candidates:
        if n and n.lower() in low:
            return low[n.lower()]
    for n in candidates:
        for c in df.columns:
            if n and n.lower() in c.lower():
                return c
    return None

def read_age_table():
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if AGE_DTA.exists():
        try:
            import pyreadstat
            df, _ = pyreadstat.read_dta(str(AGE_DTA), apply_value_formats=False)
            print("Read age-region (pyreadstat):", AGE_DTA)
            return df
        except Exception as e:
            print("[INFO] Notebook progress message.", e)
            try:
                return pd.read_stata(AGE_DTA, convert_categoricals=False)
            except Exception as e2:
                print("[INFO] Notebook progress message.", e2)
    df = pd.read_excel(AGE_XLSX)
    print("Read age-region (xlsx):", AGE_XLSX)
    return df

def write_dta_smart(df: pd.DataFrame, out_path: Path, var_labels=None):
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Original notebook comment normalized for the public code archive.
    cols = list(df.columns)
    new, used = [], set()
    for c in cols:
        base = re.sub(r"[^0-9A-Za-z_]", "_", str(c))[:32]
        name, i = base, 1
        while name in used:
            suf = f"_{i}"
            name = base[:32-len(suf)] + suf
            i += 1
        new.append(name); used.add(name)
    if new != cols:
        df = df.rename(columns=dict(zip(cols, new)))

    try:
        import pyreadstat
        last = None
        for ver in (119, 118):
            try:
                kwargs = {"version": ver}
                if var_labels:
                    try:
                        if "variable_labels" in inspect.signature(pyreadstat.write_dta).parameters:
                            kwargs["variable_labels"] = {k: var_labels.get(k, "") for k in df.columns}
                    except Exception:
                        pass
                pyreadstat.write_dta(df, str(out_path), **kwargs)
                print(f"Saved DTA via pyreadstat v{ver} ->", out_path)
                return
            except Exception as e:
                last = e
        print("[INFO] Notebook progress message.", last)
    except Exception as e:
        print("[INFO] Notebook progress message.", e)

    try:
        df.to_stata(out_path, write_index=False, version=118)
        print("Saved DTA via pandas v118 (UTF-8) ->", out_path)
        return
    except Exception as e:
        print("[INFO] Notebook progress message.", e)

    df2 = df.copy()
    for c in df2.select_dtypes(include=["object"]).columns:
        df2[c] = df2[c].astype(str).str.encode("latin-1","ignore").str.decode("latin-1")
    df2.to_stata(out_path, write_index=False, version=117)
    print("Saved DTA via pandas v117 (latin-1) ->", out_path)

# Original notebook comment normalized for the public code archive.
PROV_ALIAS = {
    "内蒙古自治区": "内蒙古",
    "广西壮族自治区": "广西",
    "西藏自治区": "西藏",
    "宁夏回族自治区": "宁夏",
    "新疆维吾尔自治区": "新疆",
    "香港特别行政区": "香港",
    "澳门特别行政区": "澳门",
}
CITY_ALIAS = {
    "襄樊": "襄阳", "襄樊市": "襄阳",
    "海东地区": "海东", "海东市": "海东",
    "阿克苏地区": "阿克苏",
    "巢湖市": "巢湖",
}
# City-level processing note.
DELEGATED_TO = {
    ("安徽", "巢湖"): ("安徽", "合肥"),   # Original notebook comment normalized for the public code archive.
}

def norm_province(x: pd.Series) -> pd.Series:
    s = _clean_to_str(x).fillna("")
    s = s.replace(PROV_ALIAS)
    s = s.str.replace(r"(省|市|特别行政区|自治区)$", "", regex=True)
    return s.str.strip()

def norm_city(x: pd.Series) -> pd.Series:
    s = _clean_to_str(x).fillna("")
    s = s.replace(CITY_ALIAS)
    s = s.str.replace(r"(市|地区|盟|自治州|林区|矿区|新区)$", "", regex=True)
    s = s.str.replace(r"市辖区$", "", regex=True)
    return s.str.strip()

def read_city_codes(path: Path) -> pd.DataFrame:
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if not path.exists():
        print("[INFO] Notebook progress message.")
        return pd.DataFrame(columns=["province","city","city_code","prov_norm","city_norm"])
    code_raw = pd.read_excel(path)
    prov_col = pick_col(code_raw, ["province","省","省份"])
    city_col = pick_col(code_raw, ["city","市","地市","地级市","prefecture"])
    code_col = pick_col(code_raw, ["code","编码","代码","citycode","行政区划代码","adcode","ad_code"])
    if city_col is None or code_col is None:
        print("[INFO] Notebook progress message.")
        return pd.DataFrame(columns=["province","city","city_code","prov_norm","city_norm"])

    codes = pd.DataFrame({
        "province": _clean_to_str(code_raw[prov_col]) if prov_col else pd.Series(np.nan, index=code_raw.index, dtype="object"),
        "city":     _clean_to_str(code_raw[city_col]),
        "city_code": _clean_to_str(code_raw[code_col]),
    })
    codes = codes[codes["city"].notna()].copy()
    codes["city_code"] = codes["city_code"].str.extract(r"(\d+)", expand=False)
    m = codes["city_code"].notna()
    codes.loc[m, "city_code"] = codes.loc[m, "city_code"].astype(str).str.zfill(6)
    codes["prov_norm"] = norm_province(codes["province"]) if "province" in codes.columns else ""
    codes["city_norm"] = norm_city(codes["city"])
    codes = codes.drop_duplicates(subset=["prov_norm","city_norm"])
    print("[INFO] Notebook progress message.")
    return codes

# =============================================================================
chi = pd.read_excel(CHI_XLSX)
print("Read chi xlsx:", CHI_XLSX)
age_all = read_age_table()
codes   = read_city_codes(CODE_XLS)

# =============================================================================
# Original notebook comment normalized for the public code archive.
for key, w in (("householdID",9), ("communityID",7)):
    if key in chi.columns:     chi[key]     = canon_id_fixed(chi[key], w)
    if key in age_all.columns: age_all[key] = canon_id_fixed(age_all[key], w)

# Original notebook comment normalized for the public code archive.
if "ID" in chi.columns:     chi["ID"] = canon_pid_11(chi["ID"])
if "ID" in age_all.columns: age_all["ID"] = canon_pid_11(age_all["ID"])

# =============================================================================
if "出生年" not in age_all.columns and "birth_year" in age_all.columns:
    age_all["出生年"] = age_all["birth_year"]
age_col_en = f"age_{YEAR}"
if "年龄" not in age_all.columns and age_col_en in age_all.columns:
    age_all["年龄"] = age_all[age_col_en]

# =============================================================================
# Original notebook comment normalized for the public code archive.
age_id = age_all[[c for c in ["ID","出生年","年龄"] if c in age_all.columns]].drop_duplicates(subset=["ID"])
chi1 = chi.merge(age_id, on="ID", how="left")

# Original notebook comment normalized for the public code archive.
region_cols = [c for c in ["communityID","province","city","urban_nbs","areatype"] if c in age_all.columns]
age_region = age_all[region_cols].drop_duplicates(subset=["communityID"]) if "communityID" in region_cols else pd.DataFrame()
merged = chi1.merge(age_region, on="communityID", how="left") if not age_region.empty else chi1.copy()

# =============================================================================
if not codes.empty and {"city"}.issubset(merged.columns):
    # Original notebook comment normalized for the public code archive.
    merged["prov_norm"] = norm_province(merged["province"]) if "province" in merged.columns else ""
    merged["city_norm"] = norm_city(merged["city"])

    # Archived notebook metadata.
    merged = merged.merge(codes[["prov_norm","city_norm","city_code"]],
                          on=["prov_norm","city_norm"], how="left")
    matched_pc = merged["city_code"].notna().sum()

    # Archived notebook metadata.
    need = merged["city_code"].isna()
    if need.any():
        uniq_city = (codes.groupby("city_norm")["city_code"].nunique().reset_index())
        uniq_city = uniq_city[uniq_city["city_code"]==1]["city_norm"]
        codes_city_only = codes[codes["city_norm"].isin(uniq_city)][["city_norm","city_code"]].drop_duplicates("city_norm")
        fill = merged.loc[need, ["city_norm"]].merge(codes_city_only, on="city_norm", how="left")["city_code"]
        merged.loc[need, "city_code"] = fill.values

    # Archived notebook metadata.
    if "city_code" in merged.columns:
        code_map = codes.set_index(["prov_norm","city_norm"])["city_code"].to_dict()
        filled = 0
        for (prov_from, city_from), (prov_to, city_to) in DELEGATED_TO.items():
            mask = merged["city_code"].isna() & (merged["prov_norm"]==prov_from) & (merged["city_norm"]==city_from)
            if mask.any():
                code_to = code_map.get((prov_to, city_to))
                if pd.notna(code_to):
                    merged.loc[mask, "city_code"] = str(code_to).zfill(6)
                    filled += int(mask.sum())
        if filled:
            print("[INFO] Notebook progress message.")

    matched_total = merged["city_code"].notna().sum()
    print("[INFO] Notebook progress message.")

# =============================================================================
order_front = [c for c in ["ID","householdID","communityID"] if c in merged.columns]
four_idx = [c for c in ["身体健康(0-100)","心理健康(0-100)","社会适应(0-100)","综合健康指数(0-100)"] if c in merged.columns]
age_cols = [c for c in ["出生年","年龄"] if c in merged.columns]
region_cols_final = [c for c in ["province","city","city_code","urban_nbs","areatype"] if c in merged.columns]
drop_helper = [c for c in ["prov_norm","city_norm"] if c in merged.columns]
other_cols = [c for c in merged.columns if c not in (order_front+four_idx+age_cols+region_cols_final+drop_helper)]
merged = merged[order_front + four_idx + age_cols + region_cols_final + other_cols]

# =============================================================================
#Excel
merged.to_excel(OUT_XLSX, index=False)
print("Excel ->", OUT_XLSX)

# Original notebook comment normalized for the public code archive.
dta_map = {
    "身体健康(0-100)":"body_index_0_100",
    "心理健康(0-100)":"mental_index_0_100",
    "社会适应(0-100)":"social_index_0_100",
    "综合健康指数(0-100)":"overall_index_0_100",
    "出生年":"birth_year",
    "年龄": f"age_{YEAR}",
}
out_dta = merged.rename(columns=dta_map).copy()
var_labels = {
    "ID":"ID","householdID":"householdID","communityID":"communityID",
    "body_index_0_100":"身体健康(0-100)","mental_index_0_100":"心理健康(0-100)",
    "social_index_0_100":"社会适应(0-100)","overall_index_0_100":"综合健康指数(0-100)",
    "birth_year":"出生年", f"age_{YEAR}":f"年龄({YEAR}-出生年)",
    "province":"省","city":"市","city_code":"市代码",
    "urban_nbs":"国家统计局城乡","areatype":"地区类型",
}
write_dta_smart(out_dta, OUT_DTA, var_labels=var_labels)
print("DTA  ->", OUT_DTA)

# =============================================================================
OUT_GIS_XLSX = ROOT / f"{YEAR}_chi_result_forGIS.xlsx"
OUT_GIS_CSV  = ROOT / f"{YEAR}_chi_result_forGIS.csv"

gis_map = {
    "身体健康(0-100)"    : "body100",
    "心理健康(0-100)"    : "mental100",
    "社会适应(0-100)"    : "social100",
    "综合健康指数(0-100)": "overall100",
    "出生年"             : "birthyr",
    "年龄"               : "age",
    "province"           : "prov",
    "city"               : "city",
    "city_code"          : "citycode",
    "urban_nbs"          : "urban_nbs",
    "areatype"           : "areatype",
}
gis = merged.rename(columns={k:v for k,v in gis_map.items() if k in merged.columns}).copy()

if "citycode" in gis.columns:
    gis["citycode_txt"] = _clean_to_str(gis["citycode"])                               # Original notebook comment normalized for the public code archive.
    gis["citycode_int"] = pd.to_numeric(gis["citycode"], errors="coerce").astype("Int64")  # Original notebook comment normalized for the public code archive.

def arc_safe_cols(df):
    new = {}
    used = set()
    for c in df.columns:
        name = re.sub(r"[^0-9A-Za-z_]", "_", str(c))
        if re.match(r"^\d", name):
            name = "_" + name
        name = name[:30]
        base = name; i = 1
        while name in used:
            suf = f"_{i}"
            name = (base[:30-len(suf)] + suf)
            i += 1
        used.add(name); new[c] = name
    return df.rename(columns=new)

gis = arc_safe_cols(gis)
gis.to_excel(OUT_GIS_XLSX, index=False)
gis.to_csv(OUT_GIS_CSV, index=False, encoding="utf-8-sig")
print("GIS-friendly Excel ->", OUT_GIS_XLSX)
print("GIS-friendly CSV    ->", OUT_GIS_CSV)

# =============================================================================
n_all = len(merged)
n_region = merged[["province","city"]].notna().any(axis=1).sum() if {"province","city"}.issubset(merged.columns) else 0
n_age = merged["年龄"].notna().sum() if "年龄" in merged.columns else 0
print("[INFO] Notebook progress message.")




# =============================================================================
# Source notebook
# =============================================================================
# record_type : wave_step
# year        : 2020
# step        : 5
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 2
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import re
import inspect
import numpy as np
import pandas as pd
from pathlib import Path

# =============================================================================
YEAR = 2020   # Original notebook comment normalized for the public code archive.
ROOT = Path(fr"E:\impact_assessment_child_order\older\health\{YEAR}")
CHI_XLSX = ROOT / f"{YEAR}_health_index_panel_fixed.xlsx"
AGE_DTA  = ROOT / f"{YEAR}_age_region.dta"
AGE_XLSX = ROOT / f"{YEAR}_age_region.xlsx"
OUT_DTA  = ROOT / f"{YEAR}_chi_result.dta"
OUT_XLSX = ROOT / f"{YEAR}_chi_result.xlsx"

# =============================================================================
def _clean_to_str(s: pd.Series) -> pd.Series:
    s = pd.Series(s, dtype="object"); m = s.isna()
    sc = s[~m].astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = sc; s.loc[m] = np.nan; return s

def canon_id_fixed(s: pd.Series, width: int) -> pd.Series:
    s = _clean_to_str(s); m = s.notna(); s.loc[m] = s.loc[m].astype(str).str.zfill(width); return s

def canon_pid_11(s: pd.Series) -> pd.Series:
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = _clean_to_str(s); m = s.notna(); t = s.copy()
    t.loc[m] = t.loc[m].str.replace(r"\D", "", regex=True)
    t = t.where(t.str.len() > 0, np.nan)
    t = t.where(t.isna(), t.str[-11:].str.zfill(11))
    return t.astype("object")

def read_age_table():
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if AGE_DTA.exists():
        try:
            import pyreadstat
            df, _ = pyreadstat.read_dta(str(AGE_DTA), apply_value_formats=False)
            print("Read age-region (pyreadstat):", AGE_DTA); return df
        except Exception as e:
            print("[INFO] Notebook progress message.", e)
            try:
                return pd.read_stata(AGE_DTA, convert_categoricals=False)
            except Exception as e2:
                print("[INFO] Notebook progress message.", e2)
    df = pd.read_excel(AGE_XLSX)
    print("Read age-region (xlsx):", AGE_XLSX); return df

def write_dta_smart(df: pd.DataFrame, out_path: Path, var_labels=None):
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Original notebook comment normalized for the public code archive.
    cols = list(df.columns); new, used = [], set()
    for c in cols:
        base = re.sub(r"[^0-9A-Za-z_]", "_", str(c))[:32]
        name, i = base, 1
        while name in used:
            suf = f"_{i}"; name = base[:32-len(suf)] + suf; i += 1
        new.append(name); used.add(name)
    if new != cols: df = df.rename(columns=dict(zip(cols, new)))

    try:
        import pyreadstat
        last = None
        for ver in (119, 118):
            try:
                kwargs = {"version": ver}
                if var_labels:
                    try:
                        if "variable_labels" in inspect.signature(pyreadstat.write_dta).parameters:
                            kwargs["variable_labels"] = {k: var_labels.get(k, "") for k in df.columns}
                    except Exception:
                        pass
                pyreadstat.write_dta(df, str(out_path), **kwargs)
                print(f"Saved DTA via pyreadstat v{ver} ->", out_path); return
            except Exception as e:
                last = e
        print("[INFO] Notebook progress message.", last)
    except Exception as e:
        print("[INFO] Notebook progress message.", e)

    try:
        df.to_stata(out_path, write_index=False, version=118)
        print("Saved DTA via pandas v118 (UTF-8) ->", out_path); return
    except Exception as e:
        print("[INFO] Notebook progress message.", e)

    df2 = df.copy()
    for c in df2.select_dtypes(include=["object"]).columns:
        df2[c] = df2[c].astype(str).str.encode("latin-1","ignore").str.decode("latin-1")
    df2.to_stata(out_path, write_index=False, version=117)
    print("Saved DTA via pandas v117 (latin-1) ->", out_path)

def find_col(df: pd.DataFrame, *candidates):
    """Archived notebook note for 05_wave_health_index_age_region_merge.

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

# =============================================================================
chi = pd.read_excel(CHI_XLSX)
print("Read chi xlsx:", CHI_XLSX)
age_all = read_age_table()

# =============================================================================
for key, w in (("householdID",9), ("communityID",7)):
    if key in chi.columns:     chi[key]     = canon_id_fixed(chi[key], w)
    if key in age_all.columns: age_all[key] = canon_id_fixed(age_all[key], w)

# Original notebook comment normalized for the public code archive.
id_col_chi = find_col(chi, "ID", "Pid", "PID", "pid", "personid", "individualid")
id_col_age = find_col(age_all, "ID", "Pid", "PID", "pid", "personid", "individualid")
if id_col_chi and id_col_chi != "ID": chi = chi.rename(columns={id_col_chi: "ID"})
if id_col_age and id_col_age != "ID": age_all = age_all.rename(columns={id_col_age: "ID"})
if "ID" in chi.columns:     chi["ID"] = canon_pid_11(chi["ID"])
if "ID" in age_all.columns: age_all["ID"] = canon_pid_11(age_all["ID"])

# =============================================================================
if "出生年" not in age_all.columns and "birth_year" in age_all.columns:
    age_all["出生年"] = age_all["birth_year"]
age_col_en = f"age_{YEAR}"
if "年龄" not in age_all.columns and age_col_en in age_all.columns:
    age_all["年龄"] = age_all[age_col_en]

# =============================================================================
# Original notebook comment normalized for the public code archive.
age_id = age_all[[c for c in ["ID","出生年","年龄"] if c in age_all.columns]].drop_duplicates(subset=["ID"])
chi1 = chi.merge(age_id, on="ID", how="left")

# Original notebook comment normalized for the public code archive.
region_cols = [c for c in ["communityID","province","city","urban_nbs","areatype"] if c in age_all.columns]
age_region = age_all[region_cols].drop_duplicates(subset=["communityID"]) if "communityID" in region_cols else pd.DataFrame()
merged = chi1.merge(age_region, on="communityID", how="left") if not age_region.empty else chi1.copy()

# =============================================================================
front = [c for c in ["ID","householdID","communityID"] if c in merged.columns]
four  = [c for c in ["身体健康(0-100)","心理健康(0-100)","社会适应(0-100)","综合健康指数(0-100)"] if c in merged.columns]
agecs = [c for c in ["出生年","年龄"] if c in merged.columns]
regs  = [c for c in ["province","city","urban_nbs","areatype"] if c in merged.columns]
others= [c for c in merged.columns if c not in (front+four+agecs+regs)]
merged = merged[front + four + agecs + regs + others]

# =============================================================================
# Excel
merged.to_excel(OUT_XLSX, index=False)
print("Excel ->", OUT_XLSX)

# Original notebook comment normalized for the public code archive.
dta_map = {
    "身体健康(0-100)":"body_index_0_100",
    "心理健康(0-100)":"mental_index_0_100",
    "社会适应(0-100)":"social_index_0_100",
    "综合健康指数(0-100)":"overall_index_0_100",
    "出生年":"birth_year",
    "年龄": f"age_{YEAR}",
}
out_dta = merged.rename(columns=dta_map).copy()
var_labels = {
    "ID":"ID","householdID":"householdID","communityID":"communityID",
    "body_index_0_100":"身体健康(0-100)","mental_index_0_100":"心理健康(0-100)",
    "social_index_0_100":"社会适应(0-100)","overall_index_0_100":"综合健康指数(0-100)",
    "birth_year":"出生年", f"age_{YEAR}":f"年龄({YEAR}-出生年)",
    "province":"省","city":"市","urban_nbs":"国家统计局城乡","areatype":"地区类型",
}
write_dta_smart(out_dta, OUT_DTA, var_labels=var_labels)
print("DTA  ->", OUT_DTA)

# =============================================================================
n_all = len(merged)
n_region = merged[["province","city"]].notna().any(axis=1).sum() if {"province","city"}.issubset(merged.columns) else 0
n_age = merged["年龄"].notna().sum() if "年龄" in merged.columns else 0
print("[INFO] Notebook progress message.")


# ------------------------------------------------------------------------------
# Notebook cell 4
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import re
import inspect
import numpy as np
import pandas as pd
from pathlib import Path

# =============================================================================
YEAR = 2020   # Original notebook comment normalized for the public code archive.
ROOT = Path(fr"E:\impact_assessment_child_order\older\health\{YEAR}")
CHI_XLSX = ROOT / f"{YEAR}_health_index_panel_fixed.xlsx"
AGE_DTA  = ROOT / f"{YEAR}_age_region.dta"
AGE_XLSX = ROOT / f"{YEAR}_age_region.xlsx"
OUT_DTA  = ROOT / f"{YEAR}_chi_result.dta"
OUT_XLSX = ROOT / f"{YEAR}_chi_result.xlsx"


# Original notebook comment normalized for the public code archive.
CODE_XLS = Path(r"E:\impact_assessment_child_order\older\编码.xls")

# =============================================================================
def _clean_to_str(s: pd.Series) -> pd.Series:
    s = pd.Series(s, dtype="object"); m = s.isna()
    sc = s[~m].astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = sc; s.loc[m] = np.nan; return s

def canon_id_fixed(s: pd.Series, width: int) -> pd.Series:
    s = _clean_to_str(s); m = s.notna(); s.loc[m] = s.loc[m].astype(str).str.zfill(width); return s

def canon_pid_11(s: pd.Series) -> pd.Series:
    s = _clean_to_str(s); m = s.notna(); t = s.copy()
    t.loc[m] = t.loc[m].str.replace(r"\D", "", regex=True)
    t = t.where(t.str.len() > 0, np.nan)
    t = t.where(t.isna(), t.str[-11:].str.zfill(11))
    return t.astype("object")

def read_age_table():
    if AGE_DTA.exists():
        try:
            import pyreadstat
            df, _ = pyreadstat.read_dta(str(AGE_DTA), apply_value_formats=False)
            print("Read age-region (pyreadstat):", AGE_DTA); return df
        except Exception as e:
            print("[INFO] Notebook progress message.", e)
            try:
                return pd.read_stata(AGE_DTA, convert_categoricals=False)
            except Exception as e2:
                print("[INFO] Notebook progress message.", e2)
    df = pd.read_excel(AGE_XLSX)
    print("Read age-region (xlsx):", AGE_XLSX); return df

def write_dta_smart(df: pd.DataFrame, out_path: Path, var_labels=None):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cols = list(df.columns); new, used = [], set()
    for c in cols:
        base = re.sub(r"[^0-9A-Za-z_]", "_", str(c))[:32]
        name, i = base, 1
        while name in used:
            suf = f"_{i}"; name = base[:32-len(suf)] + suf; i += 1
        new.append(name); used.add(name)
    if new != cols: df = df.rename(columns=dict(zip(cols, new)))
    try:
        import pyreadstat
        last = None
        for ver in (119, 118):
            try:
                kwargs = {"version": ver}
                if var_labels:
                    try:
                        if "variable_labels" in inspect.signature(pyreadstat.write_dta).parameters:
                            kwargs["variable_labels"] = {k: var_labels.get(k, "") for k in df.columns}
                    except Exception:
                        pass
                pyreadstat.write_dta(df, str(out_path), **kwargs)
                print(f"Saved DTA via pyreadstat v{ver} ->", out_path); return
            except Exception as e:
                last = e
        print("[INFO] Notebook progress message.", last)
    except Exception as e:
        print("[INFO] Notebook progress message.", e)
    try:
        df.to_stata(out_path, write_index=False, version=118)
        print("Saved DTA via pandas v118 (UTF-8) ->", out_path); return
    except Exception as e:
        print("[INFO] Notebook progress message.", e)
    df2 = df.copy()
    for c in df2.select_dtypes(include=["object"]).columns:
        df2[c] = df2[c].astype(str).str.encode("latin-1","ignore").str.decode("latin-1")
    df2.to_stata(out_path, write_index=False, version=117)
    print("Saved DTA via pandas v117 (latin-1) ->", out_path)

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
PROV_ALIAS = {
    "内蒙古自治区": "内蒙古",
    "广西壮族自治区": "广西",
    "西藏自治区": "西藏",
    "宁夏回族自治区": "宁夏",
    "新疆维吾尔自治区": "新疆",
    "香港特别行政区": "香港",
    "澳门特别行政区": "澳门",
}
CITY_ALIAS = {
    "襄樊": "襄阳", "襄樊市": "襄阳",
    "海东地区": "海东", "海东市": "海东",
    "阿克苏地区": "阿克苏",
    "巢湖市": "巢湖",
}
# Original notebook comment normalized for the public code archive.
DELEGATED_TO = {
    ("安徽", "巢湖"): ("安徽", "合肥"),
}

def norm_province(x: pd.Series) -> pd.Series:
    s = _clean_to_str(x).fillna("")
    s = s.replace(PROV_ALIAS)
    s = s.str.replace(r"(省|市|特别行政区|自治区)$", "", regex=True)
    return s.str.strip()

def norm_city(x: pd.Series) -> pd.Series:
    s = _clean_to_str(x).fillna("")
    s = s.replace(CITY_ALIAS)
    s = s.str.replace(r"(市|地区|盟|自治州|林区|矿区|新区)$", "", regex=True)
    s = s.str.replace(r"市辖区$", "", regex=True)
    return s.str.strip()

def pick_col(df: pd.DataFrame, candidates):
    low = {c.lower(): c for c in df.columns}
    for n in candidates:
        if n and n.lower() in low: return low[n.lower()]
    for n in candidates:
        for c in df.columns:
            if n and n.lower() in c.lower(): return c
    return None

def read_city_codes(path: Path) -> pd.DataFrame:
    """Archived notebook note for 05_wave_health_index_age_region_merge.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if not path.exists():
        print("[INFO] Notebook progress message.")
        return pd.DataFrame(columns=["province","city","city_code","prov_norm","city_norm"])
    code_raw = pd.read_excel(path)
    prov_col = pick_col(code_raw, ["province","省","省份"])
    city_col = pick_col(code_raw, ["city","市","地市","地级市","prefecture"])
    code_col = pick_col(code_raw, ["code","编码","代码","citycode","行政区划代码","adcode","ad_code"])
    if city_col is None or code_col is None:
        print("[INFO] Notebook progress message.")
        return pd.DataFrame(columns=["province","city","city_code","prov_norm","city_norm"])

    codes = pd.DataFrame({
        "province": _clean_to_str(code_raw[prov_col]) if prov_col else pd.Series(np.nan, index=code_raw.index, dtype="object"),
        "city":     _clean_to_str(code_raw[city_col]),
        "city_code": _clean_to_str(code_raw[code_col]),
    })
    codes = codes[codes["city"].notna()].copy()
    codes["city_code"] = codes["city_code"].str.extract(r"(\d+)", expand=False)
    m = codes["city_code"].notna()
    codes.loc[m, "city_code"] = codes.loc[m, "city_code"].astype(str).str.zfill(6)
    codes["prov_norm"] = norm_province(codes["province"]) if "province" in codes.columns else ""
    codes["city_norm"] = norm_city(codes["city"])
    codes = codes.drop_duplicates(subset=["prov_norm","city_norm"])
    print("[INFO] Notebook progress message.")
    return codes

# =============================================================================
chi = pd.read_excel(CHI_XLSX)
print("Read chi xlsx:", CHI_XLSX)
age_all = read_age_table()
codes   = read_city_codes(CODE_XLS)

# =============================================================================
for key, w in (("householdID",9), ("communityID",7)):
    if key in chi.columns:     chi[key]     = canon_id_fixed(chi[key], w)
    if key in age_all.columns: age_all[key] = canon_id_fixed(age_all[key], w)

# Original notebook comment normalized for the public code archive.
id_col_chi = find_col(chi, "ID", "Pid", "PID", "pid", "personid", "individualid")
id_col_age = find_col(age_all, "ID", "Pid", "PID", "pid", "personid", "individualid")
if id_col_chi and id_col_chi != "ID": chi = chi.rename(columns={id_col_chi: "ID"})
if id_col_age and id_col_age != "ID": age_all = age_all.rename(columns={id_col_age: "ID"})
if "ID" in chi.columns:     chi["ID"] = canon_pid_11(chi["ID"])
if "ID" in age_all.columns: age_all["ID"] = canon_pid_11(age_all["ID"])

# =============================================================================
if "出生年" not in age_all.columns and "birth_year" in age_all.columns:
    age_all["出生年"] = age_all["birth_year"]
age_col_en = f"age_{YEAR}"
if "年龄" not in age_all.columns and age_col_en in age_all.columns:
    age_all["年龄"] = age_all[age_col_en]

# =============================================================================
# Original notebook comment normalized for the public code archive.
age_id = age_all[[c for c in ["ID","出生年","年龄"] if c in age_all.columns]].drop_duplicates(subset=["ID"])
chi1 = chi.merge(age_id, on="ID", how="left")

# Original notebook comment normalized for the public code archive.
region_cols = [c for c in ["communityID","province","city","urban_nbs","areatype"] if c in age_all.columns]
age_region = age_all[region_cols].drop_duplicates(subset=["communityID"]) if "communityID" in region_cols else pd.DataFrame()
merged = chi1.merge(age_region, on="communityID", how="left") if not age_region.empty else chi1.copy()

# =============================================================================
if not codes.empty and {"city"}.issubset(merged.columns):
    merged["prov_norm"] = norm_province(merged["province"]) if "province" in merged.columns else ""
    merged["city_norm"] = norm_city(merged["city"])

    # Archived notebook metadata.
    merged = merged.merge(codes[["prov_norm","city_norm","city_code"]], on=["prov_norm","city_norm"], how="left")
    matched_pc = merged["city_code"].notna().sum()

    # Archived notebook metadata.
    need = merged["city_code"].isna()
    if need.any():
        uniq_city = (codes.groupby("city_norm")["city_code"].nunique().reset_index())
        uniq_city = uniq_city[uniq_city["city_code"]==1]["city_norm"]
        codes_city_only = codes[codes["city_norm"].isin(uniq_city)][["city_norm","city_code"]].drop_duplicates("city_norm")
        fill = merged.loc[need, ["city_norm"]].merge(codes_city_only, on="city_norm", how="left")["city_code"]
        merged.loc[need, "city_code"] = fill.values

    # Archived notebook metadata.
    if "city_code" in merged.columns:
        code_map = codes.set_index(["prov_norm","city_norm"])["city_code"].to_dict()
        filled = 0
        for (prov_from, city_from), (prov_to, city_to) in DELEGATED_TO.items():
            mask = merged["city_code"].isna() & (merged["prov_norm"]==prov_from) & (merged["city_norm"]==city_from)
            if mask.any():
                code_to = code_map.get((prov_to, city_to))
                if pd.notna(code_to):
                    merged.loc[mask, "city_code"] = str(code_to).zfill(6)
                    filled += int(mask.sum())
        if filled:
            print("[INFO] Notebook progress message.")

    matched_total = merged["city_code"].notna().sum()
    print("[INFO] Notebook progress message.")

# =============================================================================
order_front = [c for c in ["ID","householdID","communityID"] if c in merged.columns]
four_idx = [c for c in ["身体健康(0-100)","心理健康(0-100)","社会适应(0-100)","综合健康指数(0-100)"] if c in merged.columns]
age_cols = [c for c in ["出生年","年龄"] if c in merged.columns]
region_cols_final = [c for c in ["province","city","city_code","urban_nbs","areatype"] if c in merged.columns]
drop_helper = [c for c in ["prov_norm","city_norm"] if c in merged.columns]
other_cols = [c for c in merged.columns if c not in (order_front+four_idx+age_cols+region_cols_final+drop_helper)]
merged = merged[order_front + four_idx + age_cols + region_cols_final + other_cols]

# =============================================================================
# Excel
merged.to_excel(OUT_XLSX, index=False)
print("Excel ->", OUT_XLSX)

# Original notebook comment normalized for the public code archive.
dta_map = {
    "身体健康(0-100)":"body_index_0_100",
    "心理健康(0-100)":"mental_index_0_100",
    "社会适应(0-100)":"social_index_0_100",
    "综合健康指数(0-100)":"overall_index_0_100",
    "出生年":"birth_year",
    "年龄": f"age_{YEAR}",
}
out_dta = merged.rename(columns=dta_map).copy()
var_labels = {
    "ID":"ID","householdID":"householdID","communityID":"communityID",
    "body_index_0_100":"身体健康(0-100)","mental_index_0_100":"心理健康(0-100)",
    "social_index_0_100":"社会适应(0-100)","overall_index_0_100":"综合健康指数(0-100)",
    "birth_year":"出生年", f"age_{YEAR}":f"年龄({YEAR}-出生年)",
    "province":"省","city":"市","city_code":"市代码",
    "urban_nbs":"国家统计局城乡","areatype":"地区类型",
}
write_dta_smart(out_dta, OUT_DTA, var_labels=var_labels)
print("DTA  ->", OUT_DTA)

# =============================================================================
OUT_GIS_XLSX = ROOT / f"{YEAR}_chi_result_forGIS.xlsx"
OUT_GIS_CSV  = ROOT / f"{YEAR}_chi_result_forGIS.csv"

gis_map = {
    "身体健康(0-100)"    : "body100",
    "心理健康(0-100)"    : "mental100",
    "社会适应(0-100)"    : "social100",
    "综合健康指数(0-100)": "overall100",
    "出生年"             : "birthyr",
    "年龄"               : "age",
    "province"           : "prov",
    "city"               : "city",
    "city_code"          : "citycode",
    "urban_nbs"          : "urban_nbs",
    "areatype"           : "areatype",
}
gis = merged.rename(columns={k:v for k,v in gis_map.items() if k in merged.columns}).copy()

if "citycode" in gis.columns:
    gis["citycode_txt"] = _clean_to_str(gis["citycode"])                                   # Original notebook comment normalized for the public code archive.
    gis["citycode_int"] = pd.to_numeric(gis["citycode"], errors="coerce").astype("Int64")  # Original notebook comment normalized for the public code archive.

def arc_safe_cols(df):
    new = {}; used = set()
    for c in df.columns:
        name = re.sub(r"[^0-9A-Za-z_]", "_", str(c))
        if re.match(r"^\d", name): name = "_" + name
        name = name[:30]
        base = name; i = 1
        while name in used:
            suf = f"_{i}"; name = (base[:30-len(suf)] + suf); i += 1
        used.add(name); new[c] = name
    return df.rename(columns=new)

gis = arc_safe_cols(gis)
gis.to_excel(OUT_GIS_XLSX, index=False)
gis.to_csv(OUT_GIS_CSV, index=False, encoding="utf-8-sig")
print("GIS-friendly Excel ->", OUT_GIS_XLSX)
print("GIS-friendly CSV    ->", OUT_GIS_CSV)

# =============================================================================
n_all = len(merged)
n_region = merged[["province","city"]].notna().any(axis=1).sum() if {"province","city"}.issubset(merged.columns) else 0
n_age = merged["年龄"].notna().sum() if "年龄" in merged.columns else 0
print("[INFO] Notebook progress message.")
