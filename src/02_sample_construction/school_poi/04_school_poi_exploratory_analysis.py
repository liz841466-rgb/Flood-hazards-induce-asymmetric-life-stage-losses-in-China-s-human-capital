#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 04_school_poi_exploratory_analysis.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 2
# ------------------------------------------------------------------------------
import os
import glob

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

# =============================================================================

L1L2_DIR   = r"D:\GISdata\school_result\L1L2"     # Original notebook comment normalized for the public code archive.
RESULT_DIR = r"D:\GISdata\school_result"          # Original notebook comment normalized for the public code archive.
REF_YEAR   = 2024                                 # Original notebook comment normalized for the public code archive.

os.makedirs(RESULT_DIR, exist_ok=True)


# =============================================================================

def safe_read_gdf(path: str) -> gpd.GeoDataFrame:
    """Archived notebook note for 04_school_poi_exploratory_analysis.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    for engine in ["pyogrio", "fiona"]:
        for enc in [None, "utf-8", "gbk", "gb18030"]:
            try:
                if enc is None:
                    print("[INFO] Notebook progress message.")
                    gdf = gpd.read_file(path, engine=engine)
                else:
                    print("[INFO] Notebook progress message.")
                    gdf = gpd.read_file(path, engine=engine, encoding=enc)
                print("[INFO] Notebook progress message.")
                return gdf
            except UnicodeDecodeError:
                continue

    raise RuntimeError(f"无法用 utf-8/gbk/gb18030 + pyogrio/fiona 读取 {path}")


# =============================================================================

def load_all_l1l2_schools(l1l2_dir: str) -> gpd.GeoDataFrame:
    """Archived notebook note for 04_school_poi_exploratory_analysis.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    pattern = os.path.join(l1l2_dir, "*_school.shp")
    shp_files = glob.glob(pattern)

    if not shp_files:
        raise RuntimeError(f"未在 {l1l2_dir} 找到 *_school.shp")

    gdf_list = []
    for path in shp_files:
        fname = os.path.basename(path)
        province_en = fname.replace("_school.shp", "")  # School POI processing note.

        print("[INFO] Notebook progress message.")
        gdf = safe_read_gdf(path)
        gdf["province_en"] = province_en
        gdf_list.append(gdf)

    all_gdf = pd.concat(gdf_list, ignore_index=True)
    print("[INFO] Notebook progress message.")
    return all_gdf


def preprocess_build_year(df: pd.DataFrame, ref_year: int = REF_YEAR) -> pd.DataFrame:
    """Archived notebook note for 04_school_poi_exploratory_analysis.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()

    if "CI" in df.columns:
        df = df[df["CI"].isin(["L1", "L2"])]

    df = df[df["build_year"].notna()].copy()

    # Original notebook comment normalized for the public code archive.
    df["build_year_round"] = df["build_year"].round().astype(int)
    df["age"] = ref_year - df["build_year_round"]

    return df


# =============================================================================

def plot_and_save_build_year_age_distribution(df: pd.DataFrame, out_dir: str):
    """Archived notebook note for 04_school_poi_exploratory_analysis.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    # Original notebook comment normalized for the public code archive.
    plt.figure()
    df["build_year_round"].hist(bins=40)
    plt.xlabel("Build Year (rounded)")
    plt.ylabel("Number of schools")
    plt.title("Distribution of school build years (national, L1/L2)")
    plt.grid(True, linestyle="--", alpha=0.3)
    plt.tight_layout()
    out_path_year = os.path.join(out_dir, "build_year_distribution_national_300dpi.png")
    plt.savefig(out_path_year, dpi=300)
    plt.close()
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    plt.figure()
    df["age"].hist(bins=40)
    plt.xlabel(f"School age (years, as of {REF_YEAR})")
    plt.ylabel("Number of schools")
    plt.title("Distribution of school ages (national, L1/L2)")
    plt.grid(True, linestyle="--", alpha=0.3)
    plt.tight_layout()
    out_path_age = os.path.join(out_dir, "school_age_distribution_national_300dpi.png")
    plt.savefig(out_path_age, dpi=300)
    plt.close()
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    summary = df[["build_year_round", "age"]].describe()
    summary_path = os.path.join(out_dir, "build_year_age_summary_national.xlsx")
    summary.to_excel(summary_path)
    print("[INFO] Notebook progress message.")


# =============================================================================

def build_and_save_national_timeseries(df: pd.DataFrame, out_dir: str) -> pd.DataFrame:
    """Archived notebook note for 04_school_poi_exploratory_analysis.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    ts = (
        df.groupby("build_year_round")
          .size()
          .rename("n_schools")
          .reset_index()
          .sort_values("build_year_round")
    )

    print("[INFO] Notebook progress message.")
    print(ts.head())
    print("...")
    print(ts.tail())

    # Original notebook comment normalized for the public code archive.
    ts_path = os.path.join(out_dir, "national_timeseries_new_schools.xlsx")
    ts.to_excel(ts_path, index=False)
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    plt.figure()
    plt.plot(ts["build_year_round"], ts["n_schools"], marker="o")
    plt.xlabel("Year")
    plt.ylabel("Number of newly built schools (L1/L2)")
    plt.title("National time series of school construction")
    plt.grid(True, linestyle="--", alpha=0.3)
    plt.tight_layout()
    ts_fig_path = os.path.join(out_dir, "national_timeseries_new_schools_300dpi.png")
    plt.savefig(ts_fig_path, dpi=300)
    plt.close()
    print("[INFO] Notebook progress message.")

    return ts


# =============================================================================

def main():
    # Original notebook comment normalized for the public code archive.
    gdf_all = load_all_l1l2_schools(L1L2_DIR)

    # Original notebook comment normalized for the public code archive.
    df = preprocess_build_year(gdf_all, ref_year=REF_YEAR)
    print("[INFO] Notebook progress message.")

    # =============================================================================
    plot_and_save_build_year_age_distribution(df, RESULT_DIR)

    # =============================================================================
    build_and_save_national_timeseries(df, RESULT_DIR)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 4
# ------------------------------------------------------------------------------
import os
import glob

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

# =============================================================================

# Original notebook comment normalized for the public code archive.
DATA_SUBDIR = "L3"   # Original notebook comment normalized for the public code archive.

BASE_DIR   = r"D:\GISdata\school_result"
DATA_DIR   = os.path.join(BASE_DIR, DATA_SUBDIR)
RESULT_DIR = BASE_DIR
REF_YEAR   = 2024   # Original notebook comment normalized for the public code archive.

# Original notebook comment normalized for the public code archive.
USE_ONLY_L1L2 = False   # Original notebook comment normalized for the public code archive.

os.makedirs(RESULT_DIR, exist_ok=True)


# =============================================================================

def safe_read_gdf(path: str) -> gpd.GeoDataFrame:
    """Archived notebook note for 04_school_poi_exploratory_analysis.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    for engine in ["pyogrio", "fiona"]:
        for enc in [None, "utf-8", "gbk", "gb18030"]:
            try:
                if enc is None:
                    print("[INFO] Notebook progress message.")
                    gdf = gpd.read_file(path, engine=engine)
                else:
                    print("[INFO] Notebook progress message.")
                    gdf = gpd.read_file(path, engine=engine, encoding=enc)
                print("[INFO] Notebook progress message.")
                return gdf
            except UnicodeDecodeError:
                continue

    raise RuntimeError(f"无法用 utf-8/gbk/gb18030 + pyogrio/fiona 读取 {path}")


# =============================================================================

def load_all_schools(data_dir: str) -> gpd.GeoDataFrame:
    """Archived notebook note for 04_school_poi_exploratory_analysis.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    pattern = os.path.join(data_dir, "*_school.shp")
    shp_files = glob.glob(pattern)

    if not shp_files:
        raise RuntimeError(f"未在 {data_dir} 找到 *_school.shp")

    gdf_list = []
    for path in shp_files:
        fname = os.path.basename(path)
        province_en = fname.replace("_school.shp", "")  # School POI processing note.

        print("[INFO] Notebook progress message.")
        gdf = safe_read_gdf(path)
        gdf["province_en"] = province_en
        gdf_list.append(gdf)

    all_gdf = pd.concat(gdf_list, ignore_index=True)
    print("[INFO] Notebook progress message.")
    return all_gdf


def preprocess_build_year(df: pd.DataFrame,
                          ref_year: int = REF_YEAR,
                          only_l1l2: bool = True) -> pd.DataFrame:
    """Archived notebook note for 04_school_poi_exploratory_analysis.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()

    if only_l1l2 and "CI" in df.columns:
        df = df[df["CI"].isin(["L1", "L2"])]

    df = df[df["build_year"].notna()].copy()

    df["build_year_round"] = df["build_year"].round().astype(int)
    df["age"] = ref_year - df["build_year_round"]

    return df


# =============================================================================

def plot_and_save_build_year_age_distribution(df: pd.DataFrame, out_dir: str, tag: str):
    """Archived notebook note for 04_school_poi_exploratory_analysis.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    # Original notebook comment normalized for the public code archive.
    plt.figure()
    df["build_year_round"].hist(bins=40)
    plt.xlabel("Build Year (rounded)")
    plt.ylabel("Number of schools")
    plt.title(f"Distribution of school build years (national, {tag})")
    plt.grid(True, linestyle="--", alpha=0.3)
    plt.tight_layout()
    out_path_year = os.path.join(out_dir, f"build_year_distribution_{tag}_300dpi.png")
    plt.savefig(out_path_year, dpi=300)
    plt.close()
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    plt.figure()
    df["age"].hist(bins=40)
    plt.xlabel(f"School age (years, as of {REF_YEAR})")
    plt.ylabel("Number of schools")
    plt.title(f"Distribution of school ages (national, {tag})")
    plt.grid(True, linestyle="--", alpha=0.3)
    plt.tight_layout()
    out_path_age = os.path.join(out_dir, f"school_age_distribution_{tag}_300dpi.png")
    plt.savefig(out_path_age, dpi=300)
    plt.close()
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    summary = df[["build_year_round", "age"]].describe()
    summary_path = os.path.join(out_dir, f"build_year_age_summary_{tag}.xlsx")
    summary.to_excel(summary_path)
    print("[INFO] Notebook progress message.")


# =============================================================================

def build_and_save_national_timeseries(df: pd.DataFrame, out_dir: str, tag: str) -> pd.DataFrame:
    """Archived notebook note for 04_school_poi_exploratory_analysis.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    ts = (
        df.groupby("build_year_round")
          .size()
          .rename("n_schools")
          .reset_index()
          .sort_values("build_year_round")
    )

    print("[INFO] Notebook progress message.")
    print(ts.head())
    print("...")
    print(ts.tail())

    # Original notebook comment normalized for the public code archive.
    ts_path = os.path.join(out_dir, f"national_timeseries_new_schools_{tag}.xlsx")
    ts.to_excel(ts_path, index=False)
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    plt.figure()
    plt.plot(ts["build_year_round"], ts["n_schools"], marker="o")
    plt.xlabel("Year")
    plt.ylabel("Number of newly built schools")
    plt.title(f"National time series of school construction ({tag})")
    plt.grid(True, linestyle="--", alpha=0.3)
    plt.tight_layout()
    ts_fig_path = os.path.join(out_dir, f"national_timeseries_new_schools_{tag}_300dpi.png")
    plt.savefig(ts_fig_path, dpi=300)
    plt.close()
    print("[INFO] Notebook progress message.")

    return ts


# =============================================================================

def main():
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    gdf_all = load_all_schools(DATA_DIR)

    # Original notebook comment normalized for the public code archive.
    df = preprocess_build_year(gdf_all,
                               ref_year=REF_YEAR,
                               only_l1l2=USE_ONLY_L1L2)
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    if DATA_SUBDIR == "L1L2":
        tag = "L1L2"
    else:
        tag = "L3_L1L2" if USE_ONLY_L1L2 else "L3_all"

    # =============================================================================
    plot_and_save_build_year_age_distribution(df, RESULT_DIR, tag)

    # =============================================================================
    build_and_save_national_timeseries(df, RESULT_DIR, tag)


if __name__ == "__main__":
    main()
