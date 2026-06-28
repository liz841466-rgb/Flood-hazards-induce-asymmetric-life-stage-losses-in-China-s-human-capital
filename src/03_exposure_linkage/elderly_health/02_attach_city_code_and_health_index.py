#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 02_attach_city_code_and_health_index.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 2
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 02_attach_city_code_and_health_index.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import re


# ======================
# Original notebook comment normalized for the public code archive.
# ======================
def _clean_to_str(s: pd.Series) -> pd.Series:
    """Archived notebook note for 02_attach_city_code_and_health_index.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = pd.Series(s, dtype="object")
    m = s.isna()
    sc = (
        s[~m]
        .astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.replace(r"\s+", "", regex=True)
    )
    s.loc[~m] = sc
    s.loc[m] = np.nan
    return s


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
    "襄樊": "襄阳",
    "襄樊市": "襄阳",
    "海东地区": "海东",
    "海东市": "海东",
    "阿克苏地区": "阿克苏",
    "巢湖市": "巢湖",
}

# Original notebook comment normalized for the public code archive.
DELEGATED_TO = {
    ("安徽", "巢湖"): ("安徽", "合肥"),
    # Original notebook comment normalized for the public code archive.
}


def norm_province(x: pd.Series) -> pd.Series:
    """Archived notebook note for 02_attach_city_code_and_health_index.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = _clean_to_str(x).fillna("")
    s = s.replace(PROV_ALIAS)
    s = s.str.replace(r"(省|市|特别行政区|自治区)$", "", regex=True)
    return s.str.strip()


def norm_city(x: pd.Series) -> pd.Series:
    """Archived notebook note for 02_attach_city_code_and_health_index.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = _clean_to_str(x).fillna("")
    s = s.replace(CITY_ALIAS)
    s = s.str.replace(
        r"(市|地区|盟|自治州|林区|矿区|新区)$", "", regex=True
    ).str.replace(r"市辖区$", "", regex=True)
    return s.str.strip()


def pick_col(df: pd.DataFrame, candidates):
    """Archived notebook note for 02_attach_city_code_and_health_index.

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


# ======================
# Original notebook comment normalized for the public code archive.
# ======================
def read_city_codes(path: Path) -> pd.DataFrame:
    """Archived notebook note for 02_attach_city_code_and_health_index.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if not path.exists():
        print("[INFO] Notebook progress message.")
        return pd.DataFrame(columns=["prov_norm", "city_norm", "city_code"])

    code_raw = pd.read_excel(path)

    prov_col = pick_col(code_raw, ["province", "省", "省份"])
    city_col = pick_col(code_raw, ["city", "市", "地市", "地级市", "prefecture"])
    code_col = pick_col(
        code_raw,
        ["code", "编码", "代码", "citycode", "行政区划代码", "adcode", "ad_code"],
    )

    if city_col is None or code_col is None:
        print("[INFO] Notebook progress message.")
        return pd.DataFrame(columns=["prov_norm", "city_norm", "city_code"])

    codes = pd.DataFrame(
        {
            "province": _clean_to_str(code_raw[prov_col])
            if prov_col
            else pd.Series(np.nan, index=code_raw.index, dtype="object"),
            "city": _clean_to_str(code_raw[city_col]),
            "city_code": _clean_to_str(code_raw[code_col]),
        }
    )

    # Original notebook comment normalized for the public code archive.
    codes = codes[codes["city"].notna()].copy()
    codes["city_code"] = codes["city_code"].str.extract(r"(\d+)", expand=False)
    m = codes["city_code"].notna()
    codes.loc[m, "city_code"] = (
        codes.loc[m, "city_code"].astype(str).str.zfill(6)
    )

    codes["prov_norm"] = norm_province(codes["province"])
    codes["city_norm"] = norm_city(codes["city"])
    codes = codes.drop_duplicates(subset=["prov_norm", "city_norm"])

    print(
        f"[INFO] 编码表读取完成: {codes.shape[0]} 行, 列: {list(codes.columns)}"
    )
    return codes[["prov_norm", "city_norm", "city_code"]]


# ======================
# City-level processing note.
# ======================
def add_city_code_to_df(
    df: pd.DataFrame, codes: pd.DataFrame, df_name: str = ""
) -> pd.DataFrame:
    """Archived notebook note for 02_attach_city_code_and_health_index.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()

    prov_col = pick_col(df, ["province", "省", "省份"])
    city_col = pick_col(df, ["city", "市", "地市", "地级市", "prefecture"])

    print(
        f"[INFO] {df_name} 识别出的省/市列: province={prov_col}, city={city_col}"
    )

    if city_col is None:
        print("[INFO] Notebook progress message.")
        df["city_code"] = np.nan
        return df

    # Original notebook comment normalized for the public code archive.
    if prov_col is not None:
        df["prov_norm"] = norm_province(df[prov_col])
    else:
        df["prov_norm"] = ""

    df["city_norm"] = norm_city(df[city_col])

    # Archived notebook metadata.
    merged = df.merge(
        codes, how="left", on=["prov_norm", "city_norm"], suffixes=("", "_code")
    )
    matched_pc = merged["city_code"].notna().sum()
    print(
        f"[INFO] {df_name} 第一步 (省+市) 精确匹配: {matched_pc} 条 city_code。"
    )

    # Archived notebook metadata.
    need = merged["city_code"].isna()
    if need.any():
        uniq_city = (
            codes.groupby("city_norm")["city_code"]
            .nunique()
            .reset_index()
        )
        uniq_city = uniq_city[uniq_city["city_code"] == 1]["city_norm"]
        codes_city_only = (
            codes[codes["city_norm"].isin(uniq_city)][
                ["city_norm", "city_code"]
            ]
            .drop_duplicates("city_norm")
        )

        fill = (
            merged.loc[need, ["city_norm"]]
            .merge(codes_city_only, on="city_norm", how="left")["city_code"]
        )
        merged.loc[need, "city_code"] = fill.values
        matched_city_only = merged["city_code"].notna().sum() - matched_pc
        print(
            f"[INFO] {df_name} 第二步 (仅市名唯一) 匹配新增: {matched_city_only} 条。"
        )

    # Archived notebook metadata.
    if "prov_norm" in merged.columns and "city_norm" in merged.columns:
        code_map = codes.set_index(["prov_norm", "city_norm"])[
            "city_code"
        ].to_dict()
        filled = 0
        for (prov_from, city_from), (prov_to, city_to) in DELEGATED_TO.items():
            mask = (
                merged["city_code"].isna()
                & (merged["prov_norm"] == prov_from)
                & (merged["city_norm"] == city_from)
            )
            if mask.any():
                code_to = code_map.get((prov_to, city_to))
                if pd.notna(code_to):
                    merged.loc[mask, "city_code"] = str(code_to).zfill(6)
                    filled += int(mask.sum())
        if filled:
            print(
                f"[INFO] {df_name} 第三步 代管/撤地兜底填充: {filled} 条（例如 巢湖→合肥）。"
            )

    total_matched = merged["city_code"].notna().sum()
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    merged.drop(columns=["prov_norm", "city_norm"], inplace=True)

    return merged


# ======================
# CHARLS processing note.
# ======================
def process_charls_long():
    # Original notebook comment normalized for the public code archive.
    CHARLS_CSV = Path(
        "/home/ll/jupyter_notebook/gis_data/OLDER/CHARLS/health/charls_health_panel_long.csv"
    )
    CODE_XLS_LINUX = Path(
        "/home/ll/jupyter_notebook/gis_data/OLDER/CHARLS/health/编码.xls"
    )  # Original notebook comment normalized for the public code archive.

    if not CHARLS_CSV.exists():
        print("[INFO] Notebook progress message.")
        return

    print("[INFO] Notebook progress message.")
    df = pd.read_csv(CHARLS_CSV)

    codes = read_city_codes(CODE_XLS_LINUX)
    if codes.empty:
        print("[INFO] Notebook progress message.")
        return

    df2 = add_city_code_to_df(df, codes, df_name="CHARLS_long")

    # City-level processing note.
    out_csv = CHARLS_CSV.with_name("charls_health_panel_long_citycode.csv")
    out_parq = CHARLS_CSV.with_name(
        "charls_health_panel_long_citycode.parquet"
    )

    df2.to_csv(out_csv, index=False, encoding="utf-8-sig")
    df2.to_parquet(out_parq, index=False)

    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")


# ======================
# Original notebook comment normalized for the public code archive.
# ======================
def process_health_investment():
    # Original notebook comment normalized for the public code archive.
    PANEL_XLSX = Path(
        r"/home/ll/jupyter_notebook/gis_data/OLDER/CHARLS/health/Health_investment_with_Access_panel_2011_2020.xlsx"
    )
    CODE_XLS_WIN = Path(r"/home/ll/jupyter_notebook/gis_data/OLDER/CHARLS/health/编码.xls")

    if not PANEL_XLSX.exists():
        print("[INFO] Notebook progress message.")
        return

    print("[INFO] Notebook progress message.")
    df = pd.read_excel(PANEL_XLSX)

    codes = read_city_codes(CODE_XLS_WIN)
    if codes.empty:
        print("[INFO] Notebook progress message.")
        return

    df2 = add_city_code_to_df(df, codes, df_name="Health_investment")

    out_xlsx = PANEL_XLSX.with_name(
        "Health_investment_with_Access_panel_2011_2020_citycode.xlsx"
    )
    out_csv = PANEL_XLSX.with_name(
        "Health_investment_with_Access_panel_2011_2020_citycode.csv"
    )

    df2.to_excel(out_xlsx, index=False)
    df2.to_csv(out_csv, index=False, encoding="utf-8-sig")

    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")


# ======================
# main
# ======================
if __name__ == "__main__":
    # Original notebook comment normalized for the public code archive.
    process_charls_long()

    # Original notebook comment normalized for the public code archive.
    process_health_investment()


# ------------------------------------------------------------------------------
# Notebook cell 3
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 02_attach_city_code_and_health_index.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd


# =============================================================================
PANEL_CHARLS_CITYCODE = Path(
    "/home/ll/jupyter_notebook/gis_data/OLDER/CHARLS/health/"
    "charls_health_panel_long_citycode.parquet"
)

PANEL_HEALTH_INV = Path(
    "/home/ll/jupyter_notebook/gis_data/OLDER/CHARLS/health/"
    "Health_investment_with_Access_panel_2011_2020.xlsx"
)


# =============================================================================
def _to_int_id(s: pd.Series) -> pd.Series:
    """Archived notebook note for 02_attach_city_code_and_health_index.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    return pd.to_numeric(s, errors="coerce").astype("Int64")


def _mode_safe(series: pd.Series):
    """Archived notebook note for 02_attach_city_code_and_health_index.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = series.dropna()
    if s.empty:
        return np.nan
    return s.value_counts().index[0]


# =============================================================================
def build_community_mapping() -> pd.DataFrame:
    if not PANEL_CHARLS_CITYCODE.exists():
        raise FileNotFoundError(f"未找到 CHARLS 长面板（带 city_code）: {PANEL_CHARLS_CITYCODE}")

    print("[INFO] Notebook progress message.")
    panel = pd.read_parquet(PANEL_CHARLS_CITYCODE)

    if "communityID" not in panel.columns:
        raise KeyError("CHARLS 长面板中不存在 communityID 列，无法构造映射。")

    # Original notebook comment normalized for the public code archive.
    panel["communityID"] = _to_int_id(panel["communityID"])

    # Original notebook comment normalized for the public code archive.
    keep_cols = ["communityID"]
    for col in ["province", "city", "city_code"]:
        if col in panel.columns:
            keep_cols.append(col)

    df = panel[keep_cols].copy()

    # City-level processing note.
    if "city_code" not in df.columns:
        raise KeyError("CHARLS 长面板中找不到 city_code 列，请确认前一步 city_code 生成成功。")

    df = df[df["communityID"].notna() & df["city_code"].notna()].copy()

    # City-level processing note.
    nunique_city = df.groupby("communityID")["city_code"].nunique()
    conflict = nunique_city[nunique_city > 1]
    if len(conflict) > 0:
        print("[INFO] Notebook progress message."
              f"将使用众数作为代表。")

    # City-level processing note.
    agg_dict = {"city_code": _mode_safe}
    if "province" in df.columns:
        agg_dict["province"] = _mode_safe
    if "city" in df.columns:
        agg_dict["city"] = _mode_safe

    mapping = (
        df.groupby("communityID", as_index=False)
        .agg(agg_dict)
        .copy()
    )

    # City-level processing note.
    mapping["city_code"] = (
        mapping["city_code"]
        .astype(str)
        .str.extract(r"(\d+)", expand=False)
        .str.zfill(6)
    )

    print("[INFO] Notebook progress message.")
    return mapping


# =============================================================================
def attach_citycode_to_health_investment(mapping: pd.DataFrame):
    if not PANEL_HEALTH_INV.exists():
        print("[INFO] Notebook progress message.")
        return

    print("[INFO] Notebook progress message.")
    hi = pd.read_excel(PANEL_HEALTH_INV)
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    if "communityID" not in hi.columns:
        raise KeyError("Health_investment 面板中不存在 communityID 列，无法按社区合并。")

    # City-level processing note.
    if "city_code" in hi.columns:
        print("[INFO] Notebook progress message.")
        hi = hi.drop(columns=["city_code"])

    # Original notebook comment normalized for the public code archive.
    hi["communityID"] = _to_int_id(hi["communityID"])

    # Original notebook comment normalized for the public code archive.
    merged = hi.merge(
        mapping,
        on="communityID",
        how="left",
        validate="m:1",  # City-level processing note.
    )

    total_rows = len(merged)
    matched_rows = merged["city_code"].notna().sum()
    n_comm_hi = merged["communityID"].nunique()
    n_comm_matched = merged.loc[merged["city_code"].notna(), "communityID"].nunique()

    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")

    # City-level processing note.
    out_xlsx = PANEL_HEALTH_INV.with_name(
        "Health_investment_with_Access_panel_2011_2020_citycode.xlsx"
    )
    out_csv = PANEL_HEALTH_INV.with_name(
        "Health_investment_with_Access_panel_2011_2020_citycode.csv"
    )

    merged.to_excel(out_xlsx, index=False)
    merged.to_csv(out_csv, index=False, encoding="utf-8-sig")

    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")


# ============== main ==============
def main():
    mapping = build_community_mapping()
    attach_citycode_to_health_investment(mapping)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 7
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 02_attach_city_code_and_health_index.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd

# =============================================================================
IN_CSV = Path("/home/ll/jupyter_notebook/gis_data/OLDER/CHARLS/health/charls_health_panel_long_citycode.csv")
OUT_PARQUET = Path("/home/ll/jupyter_notebook/gis_data/OLDER/CHARLS/health/charls_health_panel_long_with_index.parquet")
OUT_CSV     = Path("/home/ll/jupyter_notebook/gis_data/OLDER/CHARLS/health/charls_health_panel_long_with_index.csv")


# =============================================================================

# Original notebook comment normalized for the public code archive.
PHYS_VARS_HIGH_BAD = [
    "dress", "bathe", "eat",
    "bed_chair_transfer", "toilet",
    "walk100m", "walk1km", "stairs",
    "run1km", "lift5kg", "bend_kneel_squat",
    "pick_coin", "incontinence", "housework",
    "arm_raise", "sit_to_stand",
]

PHYS_VARS_HIGH_GOOD = [
    # Original notebook comment normalized for the public code archive.
    "disease" # Original notebook comment normalized for the public code archive.
]

# Original notebook comment normalized for the public code archive.
# Fixed-effects regression helper.
# MENTAL_VARS_HIGH_BAD = [
# Original notebook comment normalized for the public code archive.
# Fixed-effects regression helper.
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# ]

# MENTAL_VARS_HIGH_GOOD = [
# Original notebook comment normalized for the public code archive.
#     # "happy", "hope",
# ]

MENTAL_VARS_HIGH_BAD = [
    "cesd10_sum",          # Original notebook comment normalized for the public code archive.
    # Original notebook comment normalized for the public code archive.
    "depress",        # Original notebook comment normalized for the public code archive.
    "effort",         # Original notebook comment normalized for the public code archive.
    "fear",           # Original notebook comment normalized for the public code archive.
    "sleep",          # Original notebook comment normalized for the public code archive.
    "hopeless",       # Original notebook comment normalized for the public code archive.

    # Original notebook comment normalized for the public code archive.
    "life_satisfaction",  # Original notebook comment normalized for the public code archive.
    "srh",                # Original notebook comment normalized for the public code archive.

    # Original notebook comment normalized for the public code archive.
    # Original notebook comment normalized for the public code archive.
    # Original notebook comment normalized for the public code archive.
]

# Original notebook comment normalized for the public code archive.
MENTAL_VARS_HIGH_GOOD = [
    "happy",  # Original notebook comment normalized for the public code archive.
    "hope",   # Original notebook comment normalized for the public code archive.
    "memory_disease",     # Original notebook comment normalized for the public code archive.
    "mental_neuro_psych", # Original notebook comment normalized for the public code archive.
]





# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
SOCIAL_VARS_HIGH_BAD = [
    "call_child_freq",   # Original notebook comment normalized for the public code archive.
    "meet_child_freq",   # Original notebook comment normalized for the public code archive.
    "social_freq",       # Original notebook comment normalized for the public code archive.
    # Original notebook comment normalized for the public code archive.
    "social_activity",
    "annual_transfer",  
]

SOCIAL_VARS_HIGH_GOOD = [
    # Fixed-effects regression helper.
    # Fixed-effects regression helper.
]


# =============================================================================

MISSING_CODES = {88, 89, 90, 96, 97, 98, 99, 888, 999, 9999}

def clean_numeric(series: pd.Series) -> pd.Series:
    """Archived notebook note for 02_attach_city_code_and_health_index.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    x = pd.to_numeric(series, errors="coerce")
    x = x.astype("float64")
    x = x.where(~x.isin(MISSING_CODES), np.nan)
    return x


def scale_to_01(series: pd.Series, higher_better: bool) -> pd.Series:
    """Archived notebook note for 02_attach_city_code_and_health_index.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    x = clean_numeric(series)
    vmin = x.min()
    vmax = x.max()

    if pd.isna(vmin) or pd.isna(vmax) or vmin == vmax:
        # Original notebook comment normalized for the public code archive.
        return pd.Series(np.nan, index=x.index, dtype="float64")

    if higher_better:
        z = (x - vmin) / (vmax - vmin)
    else:
        z = (vmax - x) / (vmax - vmin)

    # Original notebook comment normalized for the public code archive.
    z = z.clip(lower=0.0, upper=1.0)
    return z


def row_mean_with_min_nonmissing(df: pd.DataFrame, cols, min_nonmissing: int = 1) -> pd.Series:
    """Archived notebook note for 02_attach_city_code_and_health_index.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if not cols:
        return pd.Series(np.nan, index=df.index, dtype="float64")
    sub = df[cols]
    valid_counts = sub.notna().sum(axis=1)
    m = sub.mean(axis=1, skipna=True)
    return m.where(valid_counts >= min_nonmissing, np.nan)


# =============================================================================

def main():
    # Original notebook comment normalized for the public code archive.
    print(f"[READ] {IN_CSV}")
    df = pd.read_csv(
        IN_CSV,
        low_memory=False,
        dtype={
            "ID12": "string",
            "pid12": "string",
            "householdID": "string",
            "householdID10": "string",
            "communityID": "string",
        },
    )
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    df["year"] = pd.to_numeric(df["year"], errors="coerce")

    # Original notebook comment normalized for the public code archive.
    def existing(cols):
        return [c for c in cols if c in df.columns]

    phys_bad = existing(PHYS_VARS_HIGH_BAD)
    phys_good = existing(PHYS_VARS_HIGH_GOOD)
    ment_bad = existing(MENTAL_VARS_HIGH_BAD)
    ment_good = existing(MENTAL_VARS_HIGH_GOOD)
    soc_bad  = existing(SOCIAL_VARS_HIGH_BAD)
    soc_good = existing(SOCIAL_VARS_HIGH_GOOD)

    print("[INFO] Notebook progress message.", phys_bad)
    print("[INFO] Notebook progress message.", phys_good)
    print("[INFO] Notebook progress message.", ment_bad)
    print("[INFO] Notebook progress message.", ment_good)
    print("[INFO] Notebook progress message.", soc_bad)
    print("[INFO] Notebook progress message.", soc_good)

    # Original notebook comment normalized for the public code archive.
    norm_cols_phys = []
    norm_cols_ment = []
    norm_cols_soc  = []

    # Original notebook comment normalized for the public code archive.
    for col in phys_bad:
        norm_name = f"{col}_norm"
        df[norm_name] = scale_to_01(df[col], higher_better=False)
        norm_cols_phys.append(norm_name)

    for col in phys_good:
        norm_name = f"{col}_norm"
        df[norm_name] = scale_to_01(df[col], higher_better=True)
        norm_cols_phys.append(norm_name)

    # Original notebook comment normalized for the public code archive.
    for col in ment_bad:
        norm_name = f"{col}_norm"
        df[norm_name] = scale_to_01(df[col], higher_better=False)
        norm_cols_ment.append(norm_name)

    for col in ment_good:
        norm_name = f"{col}_norm"
        df[norm_name] = scale_to_01(df[col], higher_better=True)
        norm_cols_ment.append(norm_name)

    # Original notebook comment normalized for the public code archive.
    for col in soc_bad:
        norm_name = f"{col}_norm"
        df[norm_name] = scale_to_01(df[col], higher_better=False)
        norm_cols_soc.append(norm_name)

    for col in soc_good:
        norm_name = f"{col}_norm"
        df[norm_name] = scale_to_01(df[col], higher_better=True)
        norm_cols_soc.append(norm_name)

    print("[INFO] Notebook progress message.", norm_cols_phys)
    print("[INFO] Notebook progress message.", norm_cols_ment)
    print("[INFO] Notebook progress message.", norm_cols_soc)

    # Original notebook comment normalized for the public code archive.
    # Original notebook comment normalized for the public code archive.
    df["health_phys"] = row_mean_with_min_nonmissing(df, norm_cols_phys, min_nonmissing=3)

    # Original notebook comment normalized for the public code archive.
    df["health_mental"] = row_mean_with_min_nonmissing(df, norm_cols_ment, min_nonmissing=1)

    # Original notebook comment normalized for the public code archive.
    df["health_social"] = row_mean_with_min_nonmissing(df, norm_cols_soc, min_nonmissing=1)

    # Original notebook comment normalized for the public code archive.
    dim_cols = ["health_phys", "health_mental", "health_social"]
    valid_dim_counts = df[dim_cols].notna().sum(axis=1)
    df["health_index_raw"] = df[dim_cols].mean(axis=1, skipna=True)
    df.loc[valid_dim_counts < 2, "health_index_raw"] = np.nan

    # Original notebook comment normalized for the public code archive.
    mask = df["health_index_raw"].notna()
    mu = df.loc[mask, "health_index_raw"].mean()
    sigma = df.loc[mask, "health_index_raw"].std(ddof=0)

    if sigma and not np.isclose(sigma, 0.0):
        df["health_index_z"] = (df["health_index_raw"] - mu) / sigma
    else:
        # Original notebook comment normalized for the public code archive.
        df["health_index_z"] = np.nan

    print("[INFO] Notebook progress message.", df["health_index_raw"].notna().sum())
    print("[INFO] Notebook progress message.", df["health_index_z"].notna().sum())

    # Original notebook comment normalized for the public code archive.
    if "age" in df.columns:
        age60 = df["age"] >= 60
        print("[INFO] Notebook progress message.", age60.sum())
        print(df.loc[age60, "health_index_z"].describe())

    # Original notebook comment normalized for the public code archive.
    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT_PARQUET, index=False)
    df.to_csv(OUT_CSV, index=False)
    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()
