#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 05_diagnostics_city_county_crosswalk.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 1
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 05_diagnostics_city_county_crosswalk.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import re
import numpy as np
import pandas as pd
import geopandas as gpd

# =========================
# Original notebook comment normalized for the public code archive.
# =========================
COUNTY_SHP = Path("/home/ll/jupyter_notebook/gis_data/China/country/country.shp")
CITY_SHP   = Path("/home/ll/jupyter_notebook/gis_data/China/city/city.shp")

OUT_DIR = Path("/home/ll/jupyter_notebook/result/check_county_city_link")
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_COUNTY_COLUMNS = OUT_DIR / "county_columns.txt"
OUT_CITY_COLUMNS   = OUT_DIR / "city_columns.txt"
OUT_ATTR_CHECK     = OUT_DIR / "county_city_attribute_check.csv"
OUT_SPATIAL_CHECK  = OUT_DIR / "county_city_spatial_check.csv"
OUT_SUMMARY        = OUT_DIR / "county_city_link_summary.txt"

# Original notebook comment normalized for the public code archive.
COUNTY_CITY_CODE_CANDIDATES = ["市代码", "city_code", "CITY_CODE", "地市代码", "市级代码"]
COUNTY_CITY_NAME_CANDIDATES = ["市", "city_name", "CITY_NAME", "地市", "地级市"]

CITY_CODE_CANDIDATES = ["市代码", "city_code", "CITY_CODE", "adcode", "ADCODE", "code", "CODE"]
CITY_NAME_CANDIDATES = ["市", "city_name", "CITY_NAME", "name", "NAME"]


# =========================
# Original notebook comment normalized for the public code archive.
# =========================
def normalize_code(s: pd.Series) -> pd.Series:
    """Archived notebook note for 05_diagnostics_city_county_crosswalk.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    x = s.astype(str).str.strip()
    x = x.replace({"nan": pd.NA, "None": pd.NA, "": pd.NA})
    x = x.str.replace(r"\.0$", "", regex=True)
    return x


def normalize_name(s: pd.Series) -> pd.Series:
    """Archived notebook note for 05_diagnostics_city_county_crosswalk.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    x = s.astype(str).str.strip()
    x = x.replace({"nan": pd.NA, "None": pd.NA, "": pd.NA})
    return x


def normalize_name_loose(s: pd.Series) -> pd.Series:
    """Archived notebook note for 05_diagnostics_city_county_crosswalk.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    x = normalize_name(s)
    x = x.fillna("")
    x = x.str.replace(r"\s+", "", regex=True)
    x = x.str.replace(r"(市|地区|自治州|盟)$", "", regex=True)
    x = x.replace({"": pd.NA})
    return x


def pick_existing_field(columns, candidates):
    for c in candidates:
        if c in columns:
            return c
    return None


def write_columns_txt(path: Path, cols):
    with open(path, "w", encoding="utf-8") as f:
        for c in cols:
            f.write(str(c) + "\n")


def print_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


# =========================
# Original notebook comment normalized for the public code archive.
# =========================
def load_shps():
    if not COUNTY_SHP.exists():
        raise FileNotFoundError(f"找不到 county shapefile: {COUNTY_SHP}")
    if not CITY_SHP.exists():
        raise FileNotFoundError(f"找不到 city shapefile: {CITY_SHP}")

    gdf_county = gpd.read_file(COUNTY_SHP)
    gdf_city = gpd.read_file(CITY_SHP)

    return gdf_county, gdf_city


# =========================
# Original notebook comment normalized for the public code archive.
# =========================
def attribute_check(gdf_county: gpd.GeoDataFrame, gdf_city: gpd.GeoDataFrame):
    print_section("[INFO] Notebook progress message.")

    county_cols = list(gdf_county.columns)
    city_cols = list(gdf_city.columns)

    write_columns_txt(OUT_COUNTY_COLUMNS, county_cols)
    write_columns_txt(OUT_CITY_COLUMNS, city_cols)

    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print(f"[INFO] county.shp CRS: {gdf_county.crs}")
    print(f"[INFO] city.shp   CRS: {gdf_city.crs}")

    print("[INFO] Notebook progress message.")
    print(county_cols)
    print("[INFO] Notebook progress message.")
    print(city_cols)

    county_city_code_col = pick_existing_field(county_cols, COUNTY_CITY_CODE_CANDIDATES)
    county_city_name_col = pick_existing_field(county_cols, COUNTY_CITY_NAME_CANDIDATES)
    city_code_col = pick_existing_field(city_cols, CITY_CODE_CANDIDATES)
    city_name_col = pick_existing_field(city_cols, CITY_NAME_CANDIDATES)

    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")

    result = {
        "county_city_code_col": county_city_code_col,
        "county_city_name_col": county_city_name_col,
        "city_code_col": city_code_col,
        "city_name_col": city_name_col,
    }

    if county_city_code_col is None and county_city_name_col is None:
        print("[INFO] Notebook progress message.")
        print("[INFO] Notebook progress message.")
        return result, None

    # Original notebook comment normalized for the public code archive.
    df_county = gdf_county.copy()
    df_city = gdf_city.copy()

    # Original notebook comment normalized for the public code archive.
    if county_city_code_col is not None:
        df_county["county_city_code_attr"] = normalize_code(df_county[county_city_code_col])
    else:
        df_county["county_city_code_attr"] = pd.NA

    if county_city_name_col is not None:
        df_county["county_city_name_attr"] = normalize_name(df_county[county_city_name_col])
        df_county["county_city_name_attr_loose"] = normalize_name_loose(df_county[county_city_name_col])
    else:
        df_county["county_city_name_attr"] = pd.NA
        df_county["county_city_name_attr_loose"] = pd.NA

    # Original notebook comment normalized for the public code archive.
    if city_code_col is not None:
        df_city["city_code_std"] = normalize_code(df_city[city_code_col])
    else:
        df_city["city_code_std"] = pd.NA

    if city_name_col is not None:
        df_city["city_name_std"] = normalize_name(df_city[city_name_col])
        df_city["city_name_std_loose"] = normalize_name_loose(df_city[city_name_col])
    else:
        df_city["city_name_std"] = pd.NA
        df_city["city_name_std_loose"] = pd.NA

    # City-level processing note.
    if city_code_col is not None:
        dup_city_code = df_city["city_code_std"].dropna().duplicated().sum()
        print("[INFO] Notebook progress message.")
    else:
        dup_city_code = np.nan

    # Original notebook comment normalized for the public code archive.
    attr_check_df = df_county.copy()

    if city_code_col is not None:
        city_ref = df_city[["city_code_std", "city_name_std", "city_name_std_loose"]].drop_duplicates(subset=["city_code_std"])
        attr_check_df = attr_check_df.merge(
            city_ref,
            how="left",
            left_on="county_city_code_attr",
            right_on="city_code_std"
        )

        attr_check_df["code_match_found"] = attr_check_df["city_code_std"].notna().astype(int)

        if county_city_name_col is not None:
            attr_check_df["name_match_strict_by_code"] = (
                attr_check_df["county_city_name_attr"] == attr_check_df["city_name_std"]
            ).astype("Int64")
            attr_check_df["name_match_loose_by_code"] = (
                attr_check_df["county_city_name_attr_loose"] == attr_check_df["city_name_std_loose"]
            ).astype("Int64")
        else:
            attr_check_df["name_match_strict_by_code"] = pd.NA
            attr_check_df["name_match_loose_by_code"] = pd.NA
    else:
        attr_check_df["code_match_found"] = pd.NA
        attr_check_df["name_match_strict_by_code"] = pd.NA
        attr_check_df["name_match_loose_by_code"] = pd.NA

    # Original notebook comment normalized for the public code archive.
    if county_city_name_col is not None and city_name_col is not None:
        city_name_ref = df_city[["city_name_std", "city_name_std_loose"]].drop_duplicates()
        strict_name_set = set(city_name_ref["city_name_std"].dropna())
        loose_name_set = set(city_name_ref["city_name_std_loose"].dropna())

        attr_check_df["name_exists_in_city_strict"] = attr_check_df["county_city_name_attr"].isin(strict_name_set).astype(int)
        attr_check_df["name_exists_in_city_loose"] = attr_check_df["county_city_name_attr_loose"].isin(loose_name_set).astype(int)
    else:
        attr_check_df["name_exists_in_city_strict"] = pd.NA
        attr_check_df["name_exists_in_city_loose"] = pd.NA

    # Original notebook comment normalized for the public code archive.
    keep_cols = [
        c for c in [
            county_city_code_col,
            county_city_name_col,
            "county_city_code_attr",
            "county_city_name_attr",
            "county_city_name_attr_loose",
            "city_code_std",
            "city_name_std",
            "city_name_std_loose",
            "code_match_found",
            "name_match_strict_by_code",
            "name_match_loose_by_code",
            "name_exists_in_city_strict",
            "name_exists_in_city_loose",
        ] if c in attr_check_df.columns
    ]
    attr_check_df[keep_cols].to_csv(OUT_ATTR_CHECK, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    print_section("[INFO] Notebook progress message.")

    n_county = len(attr_check_df)

    if city_code_col is not None and county_city_code_col is not None:
        code_match_rate = attr_check_df["code_match_found"].mean()
        print("[INFO] Notebook progress message.")

        if county_city_name_col is not None:
            strict_rate = attr_check_df["name_match_strict_by_code"].dropna().mean()
            loose_rate = attr_check_df["name_match_loose_by_code"].dropna().mean()
            print("[INFO] Notebook progress message.")
            print("[INFO] Notebook progress message.")
    else:
        code_match_rate = np.nan

    if county_city_name_col is not None and city_name_col is not None:
        strict_exist_rate = attr_check_df["name_exists_in_city_strict"].mean()
        loose_exist_rate = attr_check_df["name_exists_in_city_loose"].mean()
        print("[INFO] Notebook progress message.")
        print("[INFO] Notebook progress message.")

    result.update({
        "n_county": n_county,
        "dup_city_code": dup_city_code,
        "code_match_rate": code_match_rate,
    })

    return result, attr_check_df


# =========================
# Original notebook comment normalized for the public code archive.
# =========================
def spatial_check(gdf_county: gpd.GeoDataFrame, gdf_city: gpd.GeoDataFrame, attr_info: dict, attr_check_df: pd.DataFrame):
    print_section("[INFO] Notebook progress message.")

    county_city_code_col = attr_info["county_city_code_col"]
    county_city_name_col = attr_info["county_city_name_col"]
    city_code_col = attr_info["city_code_col"]
    city_name_col = attr_info["city_name_col"]

    if gdf_county.crs is None or gdf_city.crs is None:
        print("[INFO] Notebook progress message.")
        return None

    gdf_county2 = gdf_county.to_crs(gdf_city.crs).copy()

    # Original notebook comment normalized for the public code archive.
    if gdf_city.crs.is_geographic:
        gdf_county_metric = gdf_county2.to_crs(3857)
        centroid = gdf_county_metric.geometry.centroid.to_crs(gdf_city.crs)
    else:
        centroid = gdf_county2.geometry.centroid

    gdf_cent = gdf_county2.copy()
    gdf_cent["geometry"] = centroid

    # City-level processing note.
    gdf_city2 = gdf_city.copy()
    if city_code_col is not None:
        gdf_city2["city_code_std"] = normalize_code(gdf_city2[city_code_col])
    else:
        gdf_city2["city_code_std"] = pd.NA

    if city_name_col is not None:
        gdf_city2["city_name_std"] = normalize_name(gdf_city2[city_name_col])
        gdf_city2["city_name_std_loose"] = normalize_name_loose(gdf_city2[city_name_col])
    else:
        gdf_city2["city_name_std"] = pd.NA
        gdf_city2["city_name_std_loose"] = pd.NA

    city_keep = ["geometry", "city_code_std", "city_name_std", "city_name_std_loose"]
    gdf_city2 = gdf_city2[city_keep].copy()

    # Original notebook comment normalized for the public code archive.
    gdf_join = gpd.sjoin(
        gdf_cent,
        gdf_city2,
        how="left",
        predicate="within"
    )

    # Original notebook comment normalized for the public code archive.
    if county_city_code_col is not None:
        gdf_join["county_city_code_attr"] = normalize_code(gdf_join[county_city_code_col])
    else:
        gdf_join["county_city_code_attr"] = pd.NA

    if county_city_name_col is not None:
        gdf_join["county_city_name_attr"] = normalize_name(gdf_join[county_city_name_col])
        gdf_join["county_city_name_attr_loose"] = normalize_name_loose(gdf_join[county_city_name_col])
    else:
        gdf_join["county_city_name_attr"] = pd.NA
        gdf_join["county_city_name_attr_loose"] = pd.NA

    # Original notebook comment normalized for the public code archive.
    gdf_join["spatial_match_found"] = gdf_join["city_code_std"].notna().astype(int)

    if county_city_code_col is not None:
        gdf_join["code_match_spatial"] = (
            gdf_join["county_city_code_attr"] == gdf_join["city_code_std"]
        ).astype("Int64")
    else:
        gdf_join["code_match_spatial"] = pd.NA

    if county_city_name_col is not None:
        gdf_join["name_match_spatial_strict"] = (
            gdf_join["county_city_name_attr"] == gdf_join["city_name_std"]
        ).astype("Int64")
        gdf_join["name_match_spatial_loose"] = (
            gdf_join["county_city_name_attr_loose"] == gdf_join["city_name_std_loose"]
        ).astype("Int64")
    else:
        gdf_join["name_match_spatial_strict"] = pd.NA
        gdf_join["name_match_spatial_loose"] = pd.NA

    keep_cols = [
        c for c in [
            county_city_code_col,
            county_city_name_col,
            "county_city_code_attr",
            "county_city_name_attr",
            "county_city_name_attr_loose",
            "city_code_std",
            "city_name_std",
            "city_name_std_loose",
            "spatial_match_found",
            "code_match_spatial",
            "name_match_spatial_strict",
            "name_match_spatial_loose",
        ] if c in gdf_join.columns
    ]
    gdf_join[keep_cols].to_csv(OUT_SPATIAL_CHECK, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")

    print_section("[INFO] Notebook progress message.")

    spatial_found_rate = gdf_join["spatial_match_found"].mean()
    print("[INFO] Notebook progress message.")

    if county_city_code_col is not None:
        code_match_spatial_rate = gdf_join["code_match_spatial"].dropna().mean()
        print("[INFO] Notebook progress message.")
    else:
        code_match_spatial_rate = np.nan

    if county_city_name_col is not None:
        strict_name_spatial_rate = gdf_join["name_match_spatial_strict"].dropna().mean()
        loose_name_spatial_rate = gdf_join["name_match_spatial_loose"].dropna().mean()
        print("[INFO] Notebook progress message.")
        print("[INFO] Notebook progress message.")

    return {
        "spatial_found_rate": spatial_found_rate,
        "code_match_spatial_rate": code_match_spatial_rate,
    }


# =========================
# Original notebook comment normalized for the public code archive.
# =========================
def final_judgement(attr_info: dict, spatial_info: dict):
    print_section("[INFO] Notebook progress message.")

    lines = []

    county_city_code_col = attr_info["county_city_code_col"]
    county_city_name_col = attr_info["county_city_name_col"]

    if county_city_code_col is None and county_city_name_col is None:
        msg = "结论：county.shp 内部缺少可用的市字段，不能直接依赖属性字段判断县属于哪个市，应使用空间连接。"
        print(msg)
        lines.append(msg)
        return lines

    code_match_rate = attr_info.get("code_match_rate", np.nan)
    code_match_spatial_rate = np.nan if spatial_info is None else spatial_info.get("code_match_spatial_rate", np.nan)
    spatial_found_rate = np.nan if spatial_info is None else spatial_info.get("spatial_found_rate", np.nan)

    # Original notebook comment normalized for the public code archive.
    if (
        county_city_code_col is not None
        and np.isfinite(code_match_rate)
        and code_match_rate >= 0.98
        and np.isfinite(code_match_spatial_rate)
        and code_match_spatial_rate >= 0.95
    ):
        msg = (
            "结论：county.shp 中的市代码字段质量很高。"
            "可以较放心地直接用 county.shp 内部的市代码将县归属到市。"
        )
    elif (
        county_city_code_col is not None
        and np.isfinite(code_match_rate)
        and code_match_rate >= 0.90
        and (not np.isfinite(code_match_spatial_rate) or code_match_spatial_rate >= 0.85)
    ):
        msg = (
            "结论：county.shp 中的市代码字段总体可用，但仍存在一定不一致记录。"
            "建议在正式分析前，对不匹配记录做人工核查，或在主流程中优先使用空间连接结果。"
        )
    else:
        msg = (
            "结论：county.shp 内部市字段与 city.shp 的对应关系不够稳。"
            "不建议直接依赖 county.shp 内部的市代码/市名称字段，建议改用空间连接作为市归属主口径。"
        )

    print(msg)
    lines.append(msg)

    if np.isfinite(spatial_found_rate):
        lines.append(f"县质心落入市 polygon 的比例: {spatial_found_rate:.4f}")
    if np.isfinite(code_match_rate):
        lines.append(f"县内市代码能在 city.shp 中找到的比例: {code_match_rate:.4f}")
    if np.isfinite(code_match_spatial_rate):
        lines.append(f"县内市代码与空间匹配市代码一致比例: {code_match_spatial_rate:.4f}")

    with open(OUT_SUMMARY, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")

    print("[INFO] Notebook progress message.")
    return lines


# =========================
# 6. MAIN
# =========================
def main():
    gdf_county, gdf_city = load_shps()
    attr_info, attr_check_df = attribute_check(gdf_county, gdf_city)
    spatial_info = spatial_check(gdf_county, gdf_city, attr_info, attr_check_df)
    final_judgement(attr_info, spatial_info)


if __name__ == "__main__":
    main()
