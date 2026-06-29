#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 09_joint_unbalanced_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""



from __future__ import annotations
# =============================================================================
# Source notebook
# =============================================================================
# record_type : joint_panel
# year        :
# step        : 1
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 09_joint_unbalanced_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 3
# ------------------------------------------------------------------------------
from pathlib import Path
import pandas as pd
import numpy as np

# ================================
# Original notebook comment normalized for the public code archive.
# ================================
BASE = Path(r"E:\impact_assessment_child_order\older\health")
YEARS = [2011, 2013, 2015, 2018, 2020]

# ================================
# Excel output note.
# Original notebook comment normalized for the public code archive.
# ================================
COMMON_RENAME = {
    # Original notebook comment normalized for the public code archive.
    "出生年": "birth_year",
    "年龄": "age",

    # Original notebook comment normalized for the public code archive.
    "age_2011": "age",
    "age_2013": "age",
    "age_2015": "age",
    "age_2018": "age",
    "age_2020": "age",

    # Original notebook comment normalized for the public code archive.
    "身体健康(0_1)": "phys_0_1",
    "身体健康(0_100)": "phys_0_100",
    "身体健康(z)": "phys_z",

    "心理健康(0_1)": "mental_0_1",
    "心理健康(0_100)": "mental_0_100",
    "心理健康(z)": "mental_z",

    "社会适应(0_1)": "social_0_1",
    "社会适应(0_100)": "social_0_100",
    "社会适应(z)": "social_z",

    "综合健康指数(0_1)": "health_0_1",
    "综合健康指数(0_100)": "health_0_100",
    "综合健康指数(z)": "health_z",
}

# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def load_one_wave(year: int) -> pd.DataFrame:
    fp = BASE / str(year) / f"{year}_chi_result.xlsx"
    print(f"[READ] YEAR={year} -> {fp}")

    df = pd.read_excel(fp)

    # Original notebook comment normalized for the public code archive.
    rename_dict = {k: v for k, v in COMMON_RENAME.items() if k in df.columns}
    df = df.rename(columns=rename_dict)

    # Original notebook comment normalized for the public code archive.
    df["year"] = year

    # Excel output note.
    if "ID" in df.columns:
        df["ID"] = df["ID"].astype("string").str.strip()
    else:
        raise ValueError(f"YEAR={year}: 未找到 ID 列，请检查 Excel 列名。")

    # Original notebook comment normalized for the public code archive.
    if "birth_year" in df.columns:
        df["birth_year"] = pd.to_numeric(df["birth_year"], errors="coerce").astype("Int64")

    if "age" in df.columns:
        df["age"] = pd.to_numeric(df["age"], errors="coerce").astype("Int64")

    # Original notebook comment normalized for the public code archive.
    for col in ["householdID", "communityID", "province", "city", "city_code"]:
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip()

    print("[INFO] Notebook progress message.")
    return df

# ================================
# Original notebook comment normalized for the public code archive.
# ================================
dfs = []
for y in YEARS:
    df_y = load_one_wave(y)
    dfs.append(df_y)

panel = pd.concat(dfs, ignore_index=True)
print("[INFO] Notebook progress message.", panel.shape)

# ================================
# Original notebook comment normalized for the public code archive.
# ================================
dup_mask = panel.duplicated(subset=["ID", "year"], keep=False)
n_dup = dup_mask.sum()
print("[INFO] Notebook progress message.")

if n_dup > 0:
    # Original notebook comment normalized for the public code archive.
    dup_examples = panel.loc[dup_mask, ["ID", "year"]].drop_duplicates().head(20)
    print("[INFO] Notebook progress message.")
    print(dup_examples)
    # Original notebook comment normalized for the public code archive.
    # Original notebook comment normalized for the public code archive.
    panel = panel.drop_duplicates(subset=["ID", "year"], keep="first").copy()
    print("[INFO] Notebook progress message.", panel.shape)

# ================================
# Original notebook comment normalized for the public code archive.
# ================================
if "birth_year" in panel.columns:
    n_unique_birth = panel.groupby("ID")["birth_year"].nunique(dropna=True)
    bad_ids = n_unique_birth[n_unique_birth > 1].index
    print("[INFO] Notebook progress message.")

    if len(bad_ids) > 0:
        print("[INFO] Notebook progress message.")
        print(list(bad_ids)[:10])
        # Original notebook comment normalized for the public code archive.
        # print(panel.loc[panel["ID"].isin(bad_ids)].sort_values(["ID", "year"]).head(50))

# ================================
# Original notebook comment normalized for the public code archive.
# ================================
waves_per_id = panel.groupby("ID")["year"].nunique()
print("[INFO] Notebook progress message.")
print(waves_per_id.value_counts().sort_index())

# ================================
# Original notebook comment normalized for the public code archive.
# ================================
panel = panel.sort_values(["ID", "year"]).reset_index(drop=True)

OUT_FP = BASE / "chi_panel_2011_2020_unbalanced.xlsx"
panel.to_excel(OUT_FP, index=False)
print("[INFO] Notebook progress message.")
print("       ", OUT_FP)


# ------------------------------------------------------------------------------
# Notebook cell 5
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 09_joint_unbalanced_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd

# =============================================================================

ROOT = Path(r"E:\impact_assessment_child_order\older\health")

WAVE_CONFIG = {
    2011: dict(
        health = ROOT / "2011" / "2011_health_result.dta",
        demo   = ROOT / "2011" / "2011_age_region.dta",
        age_var = "age_2011",
    ),
    2013: dict(
        health = ROOT / "2013" / "2013_health_result.dta",
        demo   = ROOT / "2013" / "2013_age_region.dta",
        age_var = "age_2013",
    ),
    2015: dict(
        health = ROOT / "2015" / "2015_health_result.dta",
        demo   = ROOT / "2015" / "2015_age_region.dta",
        age_var = "age_2015",   # Original notebook comment normalized for the public code archive.
    ),
    2018: dict(
        health = ROOT / "2018" / "2018_health_result.dta",
        demo   = ROOT / "2018" / "2018_age_region.dta",
        age_var = "age_2018",
    ),
    2020: dict(
        health = ROOT / "2020" / "2020_health_result.dta",
        demo   = ROOT / "2020" / "2020_age_region.dta",
        age_var = "age_2020",
    ),
}

OUT_DTA  = ROOT / "charls_panel_unbalanced_2011_2020.dta"
OUT_XLSX = ROOT / "charls_panel_unbalanced_2011_2020.xlsx"

# =============================================================================

def read_dta(path: Path) -> pd.DataFrame:
    df = pd.read_stata(path, convert_categoricals=False)
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

def digits_width(s: pd.Series, width: int) -> pd.Series:
    """Archived notebook note for 09_joint_unbalanced_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    t = _clean_to_str(s).str.replace(r"\D", "", regex=True)
    t = t.where(t.str.len() > 0, np.nan)
    # Original notebook comment normalized for the public code archive.
    t = t.where(t.isna(), t.str[-width:].str.zfill(width))
    return t.astype("object")

def ensure_pid12(df: pd.DataFrame, year: int, from_2011=False) -> pd.DataFrame:
    """Archived notebook note for 09_joint_unbalanced_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()

    if year == 2011:
        if "ID12" in df.columns:
            df["pid12"] = digits_width(df["ID12"], 12)
        else:
            # Original notebook comment normalized for the public code archive.
            hh9  = digits_width(df.get("householdID", np.nan), 9)
            id11 = digits_width(df.get("ID", np.nan),          11)
            hh10 = hh9.where(hh9.isna(), hh9 + "0")
            pn2  = id11.str[-2:]
            df["pid12"] = np.where(
                hh10.notna() & pn2.notna(),
                (hh10 + pn2).astype("object"),
                np.nan
            )
    else:
        # Original notebook comment normalized for the public code archive.
        if "ID" not in df.columns:
            raise KeyError(f"{year} 波缺少 ID 列，无法构造 pid12")
        df["pid12"] = digits_width(df["ID"], 12)

    # Original notebook comment normalized for the public code archive.
    n_pid = df["pid12"].notna().sum()
    print("[INFO] Notebook progress message.")
    return df

def sanitize_for_stata(d: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 09_joint_unbalanced_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
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
    for c in d.select_dtypes(include=["object","string"]).columns:
        s = pd.Series(d[c], dtype="object")
        m = s.isna()
        s = s.astype(str)
        s[m] = None
        s = s.map(lambda x: x if (x is None or len(x) <= 2000) else x[:2000])
        d[c] = s

    return d

def write_dta(df: pd.DataFrame, path: Path):
    """Archived notebook note for 09_joint_unbalanced_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df2 = sanitize_for_stata(df)

    # Original notebook comment normalized for the public code archive.
    cols = list(df2.columns)
    new, used = [], set()
    for c in cols:
        base = str(c)[:32]
        name, i = base, 1
        while name in used:
            suf = f"_{i}"
            name = base[:32-len(suf)] + suf
            i += 1
        new.append(name); used.add(name)
    if new != cols:
        df2 = df2.rename(columns=dict(zip(cols, new)))

    try:
        import pyreadstat, inspect
        kwargs = {"version": 118}
        # Original notebook comment normalized for the public code archive.
        pyreadstat.write_dta(df2, str(path), **kwargs)
        print(f"[WRITE] DTA(pyreadstat) -> {path}")
    except Exception as e:
        print("[INFO] Notebook progress message.")
        df2.to_stata(path, write_index=False, version=118)
        print(f"[WRITE] DTA(pandas) -> {path}")

# =============================================================================

def load_wave(year: int, cfg: dict) -> pd.DataFrame:
    """Archived notebook note for 09_joint_unbalanced_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print("[INFO] Notebook progress message.")
    f_health = cfg["health"]
    f_demo   = cfg["demo"]
    age_var  = cfg["age_var"]

    # Original notebook comment normalized for the public code archive.
    h = read_dta(f_health)
    d = read_dta(f_demo)

    # Original notebook comment normalized for the public code archive.
    h = ensure_pid12(h, year)
    d = ensure_pid12(d, year)

    # Original notebook comment normalized for the public code archive.
    demo_keep_cols = ["pid12"]
    for c in ["ID", "householdID", "communityID", "birth_year", age_var,
              "province", "city", "urban_nbs", "areatype"]:
        if c in d.columns:
            demo_keep_cols.append(c)
    demo = d[demo_keep_cols].drop_duplicates(subset=["pid12"])

    # Original notebook comment normalized for the public code archive.
    merged = h.copy()
    merged = merged.merge(demo, on="pid12", how="left", suffixes=("", "_demo"))
    merged["year"] = year

    # Original notebook comment normalized for the public code archive.
    dup_mask = merged.duplicated(subset=["pid12", "year"])
    n_dup = int(dup_mask.sum())
    if n_dup > 0:
        print("[INFO] Notebook progress message.")
        merged = merged[~dup_mask].copy()

    print("[INFO] Notebook progress message.")
    return merged

# =============================================================================

def main():
    wave_dfs = []
    for year, cfg in WAVE_CONFIG.items():
        for k in ("health", "demo"):
            if not Path(cfg[k]).exists():
                raise FileNotFoundError(f"{year} 波缺少 {k} 文件: {cfg[k]}")
        wave_dfs.append(load_wave(year, cfg))

    # Original notebook comment normalized for the public code archive.
    panel = pd.concat(wave_dfs, ignore_index=True, sort=False)
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    print("[INFO] Notebook progress message.")
    print(panel["year"].value_counts().sort_index())

    # Original notebook comment normalized for the public code archive.
    waves_per_pid = panel.groupby("pid12")["year"].nunique()
    print("[INFO] Notebook progress message.")
    print(waves_per_pid.value_counts().sort_index())

    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    panel_sorted = panel.sort_values(["pid12", "year"]).reset_index(drop=True)

    write_dta(panel_sorted, OUT_DTA)
    try:
        panel_sorted.to_excel(OUT_XLSX, index=False)
        print(f"[WRITE] Excel -> {OUT_XLSX}")
    except Exception as e:
        print("[INFO] Notebook progress message.")

    print("[INFO] Notebook progress message.")

if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 6
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 09_joint_unbalanced_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd


# =========================
# Original notebook comment normalized for the public code archive.
# =========================

BASE_DIR = Path(r"E:\impact_assessment_child_order\older\health")

# Archived notebook metadata.
WAVES = {
    2011: {"wave": 1},
    2013: {"wave": 2},
    2015: {"wave": 3},
    2018: {"wave": 4},
    2020: {"wave": 5},
}


# =========================
# Original notebook comment normalized for the public code archive.
# =========================

def _clean_to_str(s: pd.Series) -> pd.Series:
    """Archived notebook note for 09_joint_unbalanced_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = pd.Series(s, dtype="object")
    m = s.isna()
    sc = s[~m].astype(str).str.strip()
    sc = sc.str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = sc
    s.loc[m] = np.nan
    return s


def canon_fixed(s: pd.Series, width: int) -> pd.Series:
    """Archived notebook note for 09_joint_unbalanced_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = _clean_to_str(s)
    m = s.notna()
    s.loc[m] = s.loc[m].astype(str).str.zfill(width)
    return s.astype("object")


def load_one_wave(year: int, wave_meta: dict) -> pd.DataFrame | None:
    """Archived notebook note for 09_joint_unbalanced_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    wave_dir = BASE_DIR / str(year)
    health_path = wave_dir / f"{year}_health_result.dta"
    age_path    = wave_dir / f"{year}_age_region.dta"

    if not health_path.exists():
        print("[INFO] Notebook progress message.")
        return None

    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    health = pd.read_stata(health_path, convert_categoricals=False)
    print("[INFO] Notebook progress message.")

    # =============================================================================
    if year == 2011:
        # Original notebook comment normalized for the public code archive.
        if "ID12" not in health.columns:
            raise KeyError(f"{year} health_result 中找不到 ID12 列，请检查 2011 提取脚本。")
        health["ID12"] = canon_fixed(health["ID12"], 12)
        health["pid12"] = health["ID12"]
    else:
        # Original notebook comment normalized for the public code archive.
        if "ID" not in health.columns:
            raise KeyError(f"{year} health_result 中找不到 ID 列，请检查 {year} 提取脚本。")
        health["ID"] = canon_fixed(health["ID"], 12)
        health["pid12"] = health["ID"]

    # Original notebook comment normalized for the public code archive.
    before = len(health)
    health = health.dropna(subset=["pid12"])
    health = health.drop_duplicates(subset=["pid12"])
    print("[INFO] Notebook progress message.")

    # =============================================================================
    if age_path.exists():
        print("[INFO] Notebook progress message.")
        age = pd.read_stata(age_path, convert_categoricals=False)
        print("[INFO] Notebook progress message.")

        # Original notebook comment normalized for the public code archive.
        if year == 2011:
            if "ID12" not in age.columns:
                # Original notebook comment normalized for the public code archive.
                raise KeyError(f"{year} age_region 中找不到 ID12 列，请检查 2011_age_region 脚本。")
            age["ID12"] = canon_fixed(age["ID12"], 12)
            age["pid12"] = age["ID12"]
        else:
            if "ID" not in age.columns:
                raise KeyError(f"{year} age_region 中找不到 ID 列，请检查 {year}_age_region 脚本。")
            age["ID"] = canon_fixed(age["ID"], 12)
            age["pid12"] = age["ID"]

        # Original notebook comment normalized for the public code archive.
        # Original notebook comment normalized for the public code archive.
        if "birth_year" not in age.columns and "出生年" in age.columns:
            age = age.rename(columns={"出生年": "birth_year"})

        # Original notebook comment normalized for the public code archive.
        age_col = None
        age_candidates = [c for c in age.columns if c.lower().startswith("age_")]
        if age_candidates:
            age_col = age_candidates[0]
        elif "年龄" in age.columns:
            age_col = "年龄"

        if age_col is not None and age_col != "age":
            age = age.rename(columns={age_col: "age"})

        # Original notebook comment normalized for the public code archive.
        keep_age_cols = ["pid12"]
        for c in ["birth_year", "age", "province", "city", "urban_nbs", "areatype"]:
            if c in age.columns:
                keep_age_cols.append(c)

        age_slim = age[keep_age_cols].drop_duplicates(subset=["pid12"])
        print("[INFO] Notebook progress message.")
        print("[INFO] Notebook progress message.")

        # =============================================================================
        wave_df = health.merge(age_slim, on="pid12", how="left")
        print("[INFO] Notebook progress message.")
    else:
        print("[INFO] Notebook progress message.")
        wave_df = health

    # =============================================================================
    wave_df["year"] = year
    wave_df["wave"] = wave_meta["wave"]

    return wave_df


# =========================
# Original notebook comment normalized for the public code archive.
# =========================

if __name__ == "__main__":
    all_waves = []

    for year, meta in sorted(WAVES.items()):
        df_wave = load_one_wave(year, meta)
        if df_wave is not None:
            all_waves.append(df_wave)

    if not all_waves:
        raise RuntimeError("未成功读取任何波次数据，请检查路径与文件是否存在。")

    # Original notebook comment normalized for the public code archive.
    panel = pd.concat(all_waves, axis=0, ignore_index=True, sort=True)
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    n_ids = panel["pid12"].nunique()
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    preferred_first = [
        "pid12", "year", "wave",
        "ID", "ID12", "householdID", "householdID10", "communityID",
        "birth_year", "age",
        "province", "city", "urban_nbs", "areatype",
    ]
    # Original notebook comment normalized for the public code archive.
    first_cols = [c for c in preferred_first if c in panel.columns]
    other_cols = [c for c in panel.columns if c not in first_cols]
    panel = panel[first_cols + other_cols]

    # Original notebook comment normalized for the public code archive.
    out_dir = BASE_DIR / "panel"
    out_dir.mkdir(parents=True, exist_ok=True)

    dta_path  = out_dir / "charls_health_panel_long.dta"
    csv_path  = out_dir / "charls_health_panel_long.csv"

    # Original notebook comment normalized for the public code archive.
    panel.to_stata(dta_path, write_index=False, version=118)
    print("[INFO] Notebook progress message.")

    panel.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    print("[INFO] Notebook progress message.")
    waves_per_id = panel.groupby("pid12")["year"].nunique()
    tab = waves_per_id.value_counts().sort_index()
    print(tab)
    print("[INFO] Notebook progress message.")




# =============================================================================
# Source notebook
# =============================================================================
# record_type : joint_panel
# year        :
# step        : 2
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 09_joint_unbalanced_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 2
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 09_joint_unbalanced_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd

# =============================================================================
ACCESS_FILES = {
    2011: Path(r"E:\impact_assessment_child_order\older\hospital\2011\2011_Access_TimeCost.dta"),
    2013: Path(r"E:\impact_assessment_child_order\older\hospital\2013\2013_Access_TimeCost.dta"),
    2015: Path(r"E:\impact_assessment_child_order\older\hospital\2015\2015_Access_TimeCost.dta"),
    2018: Path(r"E:\impact_assessment_child_order\older\hospital\2018\2018_Access_TimeCost.dta"),
}

OUT_DIR  = Path(r"E:\impact_assessment_child_order\older\health\panel")
OUT_DTA  = OUT_DIR / "Access_TimeCost_panel_2011_2018.dta"
OUT_XLSX = OUT_DIR / "Access_TimeCost_panel_2011_2018.xlsx"


# =============================================================================
def read_dta(path: Path) -> pd.DataFrame:
    """Archived notebook note for 09_joint_unbalanced_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if not path or not path.exists():
        raise FileNotFoundError(f"未找到文件: {path}")
    try:
        import pyreadstat
        df, _ = pyreadstat.read_dta(str(path), apply_value_formats=False)
        return df
    except Exception:
        return pd.read_stata(path, convert_categoricals=False)


def _clean_to_str(s: pd.Series) -> pd.Series:
    """Archived notebook note for 09_joint_unbalanced_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = pd.Series(s, dtype="object")
    m = s.isna()
    t = s[~m].astype(str).str.strip()
    t = t.str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = t
    s.loc[m] = np.nan
    return s


def sanitize_for_stata(d: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 09_joint_unbalanced_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    d = d.copy()
    # int/bool -> float
    for c in d.select_dtypes(
        include=[
            "Int8", "Int16", "Int32", "Int64",
            "UInt8", "UInt16", "UInt32", "UInt64",
            "boolean",
        ]
    ).columns:
        d[c] = d[c].astype("float64")

    # Original notebook comment normalized for the public code archive.
    for c in d.select_dtypes(include=["object", "string"]).columns:
        s = d[c].astype(object)
        m = pd.isna(s)
        s = s.astype(str)
        s[m] = None
        d[c] = s.map(lambda x: x if (x is None or len(x) <= 2000) else x[:2000])
    return d


def write_out_panel(df: pd.DataFrame, dta_path: Path, xlsx_path: Path):
    dta_path.parent.mkdir(parents=True, exist_ok=True)
    df2 = sanitize_for_stata(df)

    # Original notebook comment normalized for the public code archive.
    try:
        import pyreadstat
        pyreadstat.write_dta(df2, str(dta_path), version=118)
        print("[INFO] Notebook progress message.", dta_path)
    except Exception as e:
        print("[INFO] Notebook progress message.", e)
        df2.to_stata(str(dta_path), write_index=False, version=118)
        print("[INFO] Notebook progress message.", dta_path)

    # Excel output note.
    df.to_excel(xlsx_path, index=False, na_rep="NA")
    print("[INFO] Notebook progress message.", xlsx_path)


# =============================================================================
def load_wave_access(year: int, path: Path) -> pd.DataFrame:
    """Archived notebook note for 09_joint_unbalanced_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print("[INFO] Notebook progress message.")
    df = read_dta(path)

    # Original notebook comment normalized for the public code archive.
    if "ID12" not in df.columns:
        raise KeyError(f"{path} 中找不到 ID12 列，请确认 Access_TimeCost 脚本已正确输出 ID12。")

    # Original notebook comment normalized for the public code archive.
    id12 = _clean_to_str(df["ID12"]).str.replace(r"\D", "", regex=True)
    id12 = id12.where(id12.str.len() == 12, np.nan)
    df["ID12"] = id12.astype("object")

    n_before = df.shape[0]
    df = df[df["ID12"].notna()].copy()
    n_after = df.shape[0]
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    df = df.sort_index()
    df = df.drop_duplicates(subset=["ID12"], keep="first")
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    df["year"] = int(year)
    df["wave"] = int(year)

    return df


# =============================================================================
def main():
    panel_list = []

    for year, fp in ACCESS_FILES.items():
        if not fp.exists():
            print("[INFO] Notebook progress message.")
            continue
        panel_list.append(load_wave_access(year, fp))

    if not panel_list:
        raise RuntimeError("没有任何 Access_TimeCost 波次成功读入，请检查路径。")

    # Original notebook comment normalized for the public code archive.
    panel = pd.concat(panel_list, axis=0, ignore_index=True, sort=False)

    # Original notebook comment normalized for the public code archive.
    n_before = panel.shape[0]
    panel = panel.sort_values(["ID12", "year"]).drop_duplicates(subset=["ID12", "year"], keep="first")
    n_after = panel.shape[0]
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    write_out_panel(panel, OUT_DTA, OUT_XLSX)
    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()




# =============================================================================
# Source notebook
# =============================================================================
# record_type : joint_panel
# year        :
# step        : 3
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 09_joint_unbalanced_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 1
# ------------------------------------------------------------------------------
from pathlib import Path
import pandas as pd
import pyreadstat
import numpy as np

# =============================================================================
BASE = Path(r"E:\impact_assessment_child_order\older\health\2013")
XLSX_FP = BASE / "2013_chi_result.xlsx"
DTA_FP  = BASE / "2013_chi_result.dta"

print("[PATH] Excel:", XLSX_FP)
print("[PATH] Stata:", DTA_FP)

# =============================================================================
df_xlsx = pd.read_excel(XLSX_FP)
print("[INFO] Notebook progress message.", df_xlsx.shape)

# =============================================================================
df_dta, meta = pyreadstat.read_dta(DTA_FP)
print("[INFO] Notebook progress message.", df_dta.shape)

# =============================================================================
cols_xlsx = list(map(str, df_xlsx.columns))
cols_dta  = list(map(str, df_dta.columns))

print("[INFO] Notebook progress message.", len(cols_xlsx))
print("[INFO] Notebook progress message.", len(cols_dta))

set_xlsx = set(cols_xlsx)
set_dta  = set(cols_dta)

print("[INFO] Notebook progress message.", set_xlsx == set_dta)

if set_xlsx != set_dta:
    only_in_xlsx = sorted(set_xlsx - set_dta)
    only_in_dta  = sorted(set_dta  - set_xlsx)
    if only_in_xlsx:
        print("[INFO] Notebook progress message.")
        for c in only_in_xlsx:
            print("   ", c)
    if only_in_dta:
        print("[INFO] Notebook progress message.")
        for c in only_in_dta:
            print("   ", c)

# Original notebook comment normalized for the public code archive.
print("[INFO] Notebook progress message.", cols_xlsx[:20])
print("[INFO] Notebook progress message.", cols_dta[:20])

# Original notebook comment normalized for the public code archive.
# print("\n[DTA meta] column_names:", meta.column_names[:20])
# print("[DTA meta] column_labels:", meta.column_labels[:20])


# ------------------------------------------------------------------------------
# Notebook cell 2
# ------------------------------------------------------------------------------
from pathlib import Path
import pandas as pd
import pyreadstat
import numpy as np

BASE = Path(r"E:\impact_assessment_child_order\older\health\2015")
XLSX_FP = BASE / "2015_chi_result.xlsx"
DTA_FP  = BASE / "2015_chi_result.dta"

df_xlsx = pd.read_excel(XLSX_FP)
df_dta, meta = pyreadstat.read_dta(DTA_FP)

print("[INFO] Notebook progress message.", df_xlsx.shape)
print("[INFO] Notebook progress message.", df_dta.shape)

assert df_xlsx.shape == df_dta.shape, "行列数不一致, 无法逐格比较"

# Original notebook comment normalized for the public code archive.
df_dta_pos = df_dta.copy()
df_dta_pos.columns = df_xlsx.columns

# Original notebook comment normalized for the public code archive.
dfx = df_xlsx.copy()
dfd = df_dta_pos.copy()

for c in dfx.columns:
    dfx[c] = dfx[c].astype("string").fillna("__NA__")
    dfd[c] = dfd[c].astype("string").fillna("__NA__")

cmp = (dfx.values == dfd.values)
total_cells = cmp.size
same_cells = cmp.sum()
diff_cells = total_cells - same_cells

print("[INFO] Notebook progress message.", total_cells)
print("[INFO] Notebook progress message.", same_cells)
print("[INFO] Notebook progress message.", diff_cells)

if diff_cells == 0:
    print("[INFO] Notebook progress message.")
else:
    print("[INFO] Notebook progress message.")
    # Original notebook comment normalized for the public code archive.
    idx_flat = np.where(~cmp.ravel())[0][:10]
    nrow, ncol = dfx.shape
    for k in idx_flat:
        i = k // ncol
        j = k %  ncol
        col = dfx.columns[j]
        print("[INFO] Notebook progress message.")




# =============================================================================
# Source notebook
# =============================================================================
# record_type : joint_panel
# year        :
# step        : 4
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 09_joint_unbalanced_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 1
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 09_joint_unbalanced_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd

# =============================================================================
INV_PATH = Path(r"E:\impact_assessment_child_order\older\health\panel\Medical_investment_panel_2011_2020.dta")
ACC_PATH = Path(r"E:\impact_assessment_child_order\older\health\panel\Access_TimeCost_panel_2011_2018.dta")

OUT_DIR  = Path(r"E:\impact_assessment_child_order\older\health\panel")
OUT_DTA  = OUT_DIR / "Health_investment_with_Access_panel_2011_2020.dta"
OUT_XLSX = OUT_DIR / "Health_investment_with_Access_panel_2011_2020.xlsx"


# =============================================================================
def read_dta(path: Path) -> pd.DataFrame:
    """Archived notebook note for 09_joint_unbalanced_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if not path.exists():
        raise FileNotFoundError(f"未找到文件：{path}")
    try:
        import pyreadstat
        df, _ = pyreadstat.read_dta(str(path), apply_value_formats=False)
        return df
    except Exception:
        return pd.read_stata(path, convert_categoricals=False)


def _clean_to_str(s: pd.Series) -> pd.Series:
    """Archived notebook note for 09_joint_unbalanced_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = pd.Series(s, dtype="object")
    m = s.isna()
    t = s[~m].astype(str).str.strip()
    t = t.str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = t
    s.loc[m] = np.nan
    return s


def sanitize_for_stata(d: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 09_joint_unbalanced_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    d = d.copy()
    # int/bool -> float
    for c in d.select_dtypes(
        include=[
            "Int8", "Int16", "Int32", "Int64",
            "UInt8", "UInt16", "UInt32", "UInt64",
            "boolean",
        ]
    ).columns:
        d[c] = d[c].astype("float64")

    # Original notebook comment normalized for the public code archive.
    for c in d.select_dtypes(include=["object", "string"]).columns:
        s = d[c].astype(object)
        m = pd.isna(s)
        s = s.astype(str)
        s[m] = None
        d[c] = s.map(lambda x: x if (x is None or len(x) <= 2000) else x[:2000])
    return d


def write_out(df: pd.DataFrame, dta_path: Path, xlsx_path: Path):
    dta_path.parent.mkdir(parents=True, exist_ok=True)
    df2 = sanitize_for_stata(df)

    # Original notebook comment normalized for the public code archive.
    try:
        import pyreadstat
        pyreadstat.write_dta(df2, str(dta_path), version=118)
        print("[INFO] Notebook progress message.", dta_path)
    except Exception as e:
        print("[INFO] Notebook progress message.", e)
        df2.to_stata(str(dta_path), write_index=False, version=118)
        print("[INFO] Notebook progress message.", dta_path)

    # Excel output note.
    df.to_excel(xlsx_path, index=False, na_rep="NA")
    print("[INFO] Notebook progress message.", xlsx_path)


# =============================================================================
def main():
    # Original notebook comment normalized for the public code archive.
    print("[INFO] Notebook progress message.", INV_PATH)
    inv = read_dta(INV_PATH)
    print("[INFO] Notebook progress message.", ACC_PATH)
    acc = read_dta(ACC_PATH)

    # Original notebook comment normalized for the public code archive.
    if "ID12" not in inv.columns or "year" not in inv.columns:
        raise KeyError("医疗投入面板中缺少 ID12 或 year，请检查上游脚本。")
    if "ID12" not in acc.columns or "year" not in acc.columns:
        raise KeyError("就诊时间成本面板中缺少 ID12 或 year，请检查上游脚本。")

    # Original notebook comment normalized for the public code archive.
    for df_name, df in [("INV", inv), ("ACC", acc)]:
        id12 = _clean_to_str(df["ID12"]).str.replace(r"\D", "", regex=True)
        id12 = id12.where(id12.str.len() == 12, np.nan)
        df["ID12"] = id12.astype("object")
        # Archived notebook metadata.
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
        print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    inv = inv.sort_values(["ID12", "year"])
    inv = inv.drop_duplicates(subset=["ID12", "year"], keep="first")
    acc = acc.sort_values(["ID12", "year"])
    acc = acc.drop_duplicates(subset=["ID12", "year"], keep="first")

    print("[INFO] Notebook progress message.", inv.shape[0])
    print("[INFO] Notebook progress message.", acc.shape[0])

    # Original notebook comment normalized for the public code archive.
    common_cols = set(inv.columns) & set(acc.columns)
    key_cols = {"ID12", "year"}
    drop_from_acc = [c for c in common_cols if c not in key_cols]

    if drop_from_acc:
        print("[INFO] Notebook progress message.")
        print("       ", drop_from_acc)
        acc = acc.drop(columns=drop_from_acc)

    # Original notebook comment normalized for the public code archive.
    panel = inv.merge(acc, on=["ID12", "year"], how="outer", indicator="merge_src")

    # Original notebook comment normalized for the public code archive.
    panel = panel.sort_values(["ID12", "year"]).reset_index(drop=True)

    # Original notebook comment normalized for the public code archive.
    print("[INFO] Notebook progress message.", panel.shape[0])
    print("[INFO] Notebook progress message.")
    print(panel["year"].value_counts(dropna=False).sort_index())

    # Original notebook comment normalized for the public code archive.
    write_out(panel, OUT_DTA, OUT_XLSX)
    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 5
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 09_joint_unbalanced_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(r"E:\impact_assessment_child_order\older\health\panel")

FILE_HEALTH = BASE_DIR / "charls_health_panel_long.csv"
FILE_INVACC = BASE_DIR / "Health_investment_with_Access_panel_2011_2020.xlsx"


def read_csv_safe(path: Path) -> pd.DataFrame:
    """Archived notebook note for 09_joint_unbalanced_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    try:
        return pd.read_csv(path)
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="gbk")


# CHARLS processing note.
df_health = read_csv_safe(FILE_HEALTH)

print("========== 1) charls_health_panel_long.csv ==========")
print("[INFO] Notebook progress message.")
print("[INFO] Notebook progress message.")          # (n_rows, n_cols)

print("[INFO] Notebook progress message.")
print(list(df_health.columns))

print("[INFO] Notebook progress message.")
print(df_health.head(10))

# Original notebook comment normalized for the public code archive.
for col in ["year", "wave", "ID12", "householdID10"]:
    if col in df_health.columns:
        print("[INFO] Notebook progress message.", df_health[col].notna().sum())
        if col in ["year", "wave"]:
            print("[INFO] Notebook progress message.")
            print(df_health[col].value_counts(dropna=False).sort_index())


# Original notebook comment normalized for the public code archive.
df_invacc = pd.read_excel(FILE_INVACC, sheet_name=0)

print("\n\n========== 2) Health_investment_with_Access_panel_2011_2020.xlsx ==========")
print("[INFO] Notebook progress message.")
print("[INFO] Notebook progress message.")

print("[INFO] Notebook progress message.")
print(list(df_invacc.columns))

print("[INFO] Notebook progress message.")
print(df_invacc.head(10))

# Original notebook comment normalized for the public code archive.
for col in ["year", "wave", "ID12", "householdID10"]:
    if col in df_invacc.columns:
        print("[INFO] Notebook progress message.", df_invacc[col].notna().sum())
        if col in ["year", "wave"]:
            print("[INFO] Notebook progress message.")
            print(df_invacc[col].value_counts(dropna=False).sort_index())




# =============================================================================
# Source notebook
# =============================================================================
# record_type : joint_panel
# year        :
# step        : 5
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 09_joint_unbalanced_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 2
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 09_joint_unbalanced_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd


# =============================================================================
BASE_EXP = Path(r"E:\impact_assessment_child_order\older\expenditure")
OUT_DIR  = Path(r"E:\impact_assessment_child_order\older\health\panel")

# Original notebook comment normalized for the public code archive.
WAVES_PERSONAL = {
    2011: BASE_EXP / "2011" / "Medical_investment_2011.dta",
    2013: BASE_EXP / "2013" / "Medical_investment_2013.dta",
    2015: BASE_EXP / "2015" / "Medical_investment_2015.dta",
    2018: BASE_EXP / "2018" / "Medical_investment_2018.dta",
}
# 2020
FP_2020_HH   = BASE_EXP / "2020" / "2020_M_household.dta"
FP_2020_EXIT = BASE_EXP / "2020" / "2020_M_exit.dta"
FP_2020_IND  = BASE_EXP / "2020" / "2020_M_individual_all.dta"

OUT_DTA  = OUT_DIR / "Medical_investment_panel_2011_2020.dta"
OUT_XLSX = OUT_DIR / "Medical_investment_panel_2011_2020.xlsx"


# =============================================================================
def read_dta(path: Path) -> pd.DataFrame:
    """Archived notebook note for 09_joint_unbalanced_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if not path.exists():
        raise FileNotFoundError(f"未找到文件: {path}")
    try:
        import pyreadstat
        df, _ = pyreadstat.read_dta(str(path), apply_value_formats=False)
        return df
    except Exception:
        return pd.read_stata(path, convert_categoricals=False)


def _clean_to_str(s: pd.Series) -> pd.Series:
    """Archived notebook note for 09_joint_unbalanced_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = pd.Series(s, dtype="object")
    m = s.isna()
    t = s[~m].astype(str).str.strip()
    t = t.str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = t
    s.loc[m] = np.nan
    return s


def sanitize_id12(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 09_joint_unbalanced_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()
    if "ID12" in df.columns:
        id12 = _clean_to_str(df["ID12"]).str.replace(r"\D", "", regex=True)
        id12 = id12.where(id12.str.len() == 12, np.nan)
        df["ID12"] = id12.astype("object")
    elif "ID" in df.columns:
        # Original notebook comment normalized for the public code archive.
        idd = _clean_to_str(df["ID"]).str.replace(r"\D", "", regex=True)
        id12 = idd.where(idd.str.len() == 12, np.nan)
        df["ID12"] = id12.astype("object")
    else:
        df["ID12"] = np.nan
    return df


def sanitize_for_stata(d: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 09_joint_unbalanced_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    d = d.copy()
    for c in d.select_dtypes(
        include=["Int8", "Int16", "Int32", "Int64", "UInt8", "UInt16", "UInt32", "UInt64", "boolean"]
    ).columns:
        d[c] = d[c].astype("float64")
    for c in d.select_dtypes(include=["object", "string"]).columns:
        s = d[c].astype(object)
        m = pd.isna(s)
        s = s.astype(str)
        s[m] = None
        d[c] = s.map(lambda x: x if (x is None or len(x) <= 2000) else x[:2000])
    return d


def write_out_panel(df: pd.DataFrame, dta_path: Path, xlsx_path: Path):
    dta_path.parent.mkdir(parents=True, exist_ok=True)
    df2 = sanitize_for_stata(df)
    try:
        import pyreadstat
        pyreadstat.write_dta(df2, str(dta_path), version=118)
        print("[INFO] Notebook progress message.", dta_path)
    except Exception as e:
        print("[INFO] Notebook progress message.", e)
        df2.to_stata(str(dta_path), write_index=False, version=118)
        print("[INFO] Notebook progress message.", dta_path)
    df.to_excel(xlsx_path, index=False, na_rep="NA")
    print("[INFO] Notebook progress message.", xlsx_path)


# =============================================================================
COMMON_ID_COLS = ["ID12", "householdID10", "ID", "householdID", "communityID"]

M_PERSONAL_COLS = [
    "outpt_month_total", "outpt_month_oop",
    "outpt_last_total",  "outpt_last_oop",
    "inp_year_total",    "inp_year_oop",
    "inp_last_total",    "inp_last_oop",
    "self_treat_total",  "self_treat_oop",
]

# Original notebook comment normalized for the public code archive.
GE_COLS = ["ge010_6", "ge010_7"]


def load_wave_personal_M(year: int, path: Path) -> pd.DataFrame:
    """Archived notebook note for 09_joint_unbalanced_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print("[INFO] Notebook progress message.")
    df = read_dta(path)
    df = sanitize_id12(df)

    # Original notebook comment normalized for the public code archive.
    keep_cols = [c for c in COMMON_ID_COLS if c in df.columns]
    keep_cols += [c for c in M_PERSONAL_COLS if c in df.columns]
    keep_cols += [c for c in GE_COLS if c in df.columns]

    sub = df[keep_cols].copy()

    # Original notebook comment normalized for the public code archive.
    if "ge010_6" in sub.columns:
        sub.rename(columns={"ge010_6": "hh_med_year"}, inplace=True)
    if "ge010_7" in sub.columns:
        sub.rename(columns={"ge010_7": "hh_health_year"}, inplace=True)

    sub["year"] = year
    sub["wave"] = year
    sub["is_exit2020"] = 0.0  # Original notebook comment normalized for the public code archive.

    # Original notebook comment normalized for the public code archive.
    n_before = sub.shape[0]
    sub = sub[sub["ID12"].notna()].copy()
    n_after = sub.shape[0]
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    sub = sub.sort_index()
    sub = sub.drop_duplicates(subset=["ID12", "year"], keep="first")
    print("[INFO] Notebook progress message.")

    return sub


def load_2020_panel(
    fp_hh: Path,
    fp_exit: Path,
    fp_ind: Path,
) -> pd.DataFrame:
    """Archived notebook note for 09_joint_unbalanced_panel.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    # Original notebook comment normalized for the public code archive.
    print("[INFO] Notebook progress message.")
    hh = read_dta(fp_hh)
    hh = sanitize_id12(hh)  # Original notebook comment normalized for the public code archive.

    # Original notebook comment normalized for the public code archive.
    print("[INFO] Notebook progress message.")
    ind = read_dta(fp_ind)
    ind = sanitize_id12(ind)
    keep_cols = [c for c in COMMON_ID_COLS if c in ind.columns]
    # Original notebook comment normalized for the public code archive.
    for c in ["hh_med_year", "hh_health_year"]:
        if c in ind.columns:
            keep_cols.append(c)

    ind_sub = ind[keep_cols].copy()
    ind_sub["year"] = 2020
    ind_sub["wave"] = 2020
    ind_sub["is_exit2020"] = 0.0

    # Original notebook comment normalized for the public code archive.
    print("[INFO] Notebook progress message.")
    ex = read_dta(fp_exit)
    ex = sanitize_id12(ex)

    # Original notebook comment normalized for the public code archive.
    rename_map = {}
    if "outpt_last_month_total" in ex.columns:
        rename_map["outpt_last_month_total"] = "outpt_month_total"
    if "outpt_last_month_oop" in ex.columns:
        rename_map["outpt_last_month_oop"] = "outpt_month_oop"
    if "inp_last_year_total" in ex.columns:
        rename_map["inp_last_year_total"] = "inp_year_total"
    if "inp_last_year_oop" in ex.columns:
        rename_map["inp_last_year_oop"] = "inp_year_oop"
    if "selftreat_last_month_total" in ex.columns:
        rename_map["selftreat_last_month_total"] = "self_treat_total"
    if "selftreat_last_month_oop" in ex.columns:
        rename_map["selftreat_last_month_oop"] = "self_treat_oop"

    ex = ex.rename(columns=rename_map)

    keep_cols_ex = [c for c in COMMON_ID_COLS if c in ex.columns]
    # Original notebook comment normalized for the public code archive.
    for c in M_PERSONAL_COLS:
        if c in ex.columns:
            keep_cols_ex.append(c)
    # Original notebook comment normalized for the public code archive.
    for c in ["hh_med_year", "hh_health_year"]:
        if c in ex.columns:
            keep_cols_ex.append(c)

    ex_sub = ex[keep_cols_ex].copy()
    ex_sub["year"] = 2020
    ex_sub["wave"] = 2020
    ex_sub["is_exit2020"] = 1.0

    # Original notebook comment normalized for the public code archive.
    # Original notebook comment normalized for the public code archive.
    # Original notebook comment normalized for the public code archive.
    panel_2020 = pd.concat([ex_sub, ind_sub], axis=0, ignore_index=True)
    # Original notebook comment normalized for the public code archive.
    panel_2020 = panel_2020[panel_2020["ID12"].notna()].copy()
    # Original notebook comment normalized for the public code archive.
    panel_2020 = panel_2020.sort_values(by=["is_exit2020"], ascending=False)
    panel_2020 = panel_2020.drop_duplicates(subset=["ID12", "year"], keep="first")
    panel_2020 = panel_2020.sort_index()

    print("[INFO] Notebook progress message.")
    return panel_2020


# =============================================================================
def main():
    # Original notebook comment normalized for the public code archive.
    panel_list = []
    for yr, fp in WAVES_PERSONAL.items():
        if not fp.exists():
            print("[INFO] Notebook progress message.")
            continue
        panel_list.append(load_wave_personal_M(yr, fp))

    # 2) 2020：regular + exit
    if FP_2020_IND.exists() and FP_2020_EXIT.exists():
        panel_2020 = load_2020_panel(FP_2020_HH, FP_2020_EXIT, FP_2020_IND)
        panel_list.append(panel_2020)
    else:
        print("[INFO] Notebook progress message.")
        # Original notebook comment normalized for the public code archive.

    if not panel_list:
        raise RuntimeError("没有任何波次成功读入，检查路径配置是否正确。")

    # Original notebook comment normalized for the public code archive.
    panel = pd.concat(panel_list, axis=0, ignore_index=True)

    # Original notebook comment normalized for the public code archive.
    panel["ID12"] = _clean_to_str(panel["ID12"]).str.replace(r"\D", "", regex=True)
    panel.loc[panel["ID12"].str.len() == 0, "ID12"] = np.nan

    # Original notebook comment normalized for the public code archive.
    n_before = panel.shape[0]
    panel = panel[panel["ID12"].notna()].copy()
    n_after = panel.shape[0]
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    panel = panel.sort_values(by=["ID12", "year"]).reset_index(drop=True)

    # Original notebook comment normalized for the public code archive.
    write_out_panel(panel, OUT_DTA, OUT_XLSX)
    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()
