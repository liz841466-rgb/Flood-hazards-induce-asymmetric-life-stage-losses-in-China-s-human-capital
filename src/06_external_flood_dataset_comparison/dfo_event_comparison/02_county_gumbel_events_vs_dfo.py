#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 02_county_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 1
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 02_county_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

# =============================================================================

BASE_DIR = "/home/ll/jupyter_notebook"

# CaMa-Flood processing note.
CAMA_CSV = os.path.join(
    BASE_DIR,
    "result/county_storage_return_events/"
    "county_flood_events_T10_20_50_100_1980_2020.csv"
)

# External flood dataset comparison note.
DFO_CSV = os.path.join(
    BASE_DIR,
    "result/impact_assessment/flood/county_year_panel_DFO.csv"
)

# Original notebook comment normalized for the public code archive.
COUNTY_SHP = os.path.join(
    BASE_DIR,
    "gis_data/China/country/country.shp"
)
COUNTY_ID_FIELD = "县代码"

# Original notebook comment normalized for the public code archive.
OUT_DIR = os.path.join(
    BASE_DIR,
    "result/impact_assessment/older/fig_CaMa_DFO_hits_county_DFOactive"
)
os.makedirs(OUT_DIR, exist_ok=True)

# Original notebook comment normalized for the public code archive.
YEAR_MIN = 1985           # External flood dataset comparison note.
YEAR_MAX = 2020           # External flood dataset comparison note.

# External flood dataset comparison note.
DFO_COL = "flooded_any"

# External flood dataset comparison note.
ONLY_DFO_ACTIVE = True


# =============================================================================

def load_cama_events(path: str) -> pd.DataFrame:
    """Archived notebook note for 02_county_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = pd.read_csv(path, dtype={"county_code": str})

    # County-level processing note.
    if "county_code" not in df.columns:
        raise RuntimeError("CaMa 县级事件表中缺少 county_code 列，请检查输出。")

    cama_cols = [c for c in df.columns if c.startswith("flood_ge_T")]
    if not cama_cols:
        raise RuntimeError("CaMa 县级事件表中未找到 flood_ge_T* 列。")

    for c in cama_cols:
        df[c] = df[c].astype(int)

    df["cama_any_event"] = (df[cama_cols].max(axis=1) > 0).astype(int)

    # Original notebook comment normalized for the public code archive.
    out = df[["year", "county_code", "cama_any_event"] + cama_cols].copy()
    return out


def load_dfo_panel(path: str) -> pd.DataFrame:
    """Archived notebook note for 02_county_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = pd.read_csv(path, dtype={"county_code": str})
    if DFO_COL not in df.columns:
        raise RuntimeError(f"DFO 县面板中缺少列: {DFO_COL}")
    df[DFO_COL] = df[DFO_COL].astype(int)
    out = df[["year", "county_code", DFO_COL]].copy()
    return out


def merge_cama_dfo() -> pd.DataFrame:
    """Archived notebook note for 02_county_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df_cama = load_cama_events(CAMA_CSV)
    df_dfo  = load_dfo_panel(DFO_CSV)

    df = df_cama.merge(df_dfo, on=["county_code", "year"], how="inner")

    # Original notebook comment normalized for the public code archive.
    df = df[(df["year"] >= YEAR_MIN) & (df["year"] <= YEAR_MAX)].copy()
    print("[INFO] Notebook progress message.")

    # External flood dataset comparison note.
    if ONLY_DFO_ACTIVE:
        s = df.groupby("county_code")[DFO_COL].sum()
        active = s[s > 0].index
        df = df[df["county_code"].isin(active)].copy()
        print("[INFO] Notebook progress message.")
        print("[INFO] Notebook progress message.")

    return df


# =============================================================================

def classify_cases(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 02_county_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    cama = df["cama_any_event"].astype(int)
    dfo  = df[DFO_COL].astype(int)

    conditions = [
        (cama == 1) & (dfo == 1),
        (cama == 0) & (dfo == 1),
        (cama == 1) & (dfo == 0),
        (cama == 0) & (dfo == 0),
    ]
    choices = ["hit", "miss", "false_alarm", "correct_neg"]

    df = df.copy()
    df["case_type"] = np.select(conditions, choices, default="unknown")
    return df


# =============================================================================

def load_county_gdf(active_codes: pd.Index) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(COUNTY_SHP)
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)
    else:
        gdf = gdf.to_crs(epsg=4326)

    gdf["county_code"] = gdf[COUNTY_ID_FIELD].astype(str)
    gdf = gdf[gdf["county_code"].isin(active_codes)].copy()
    print("[INFO] Notebook progress message.")
    return gdf


# =============================================================================

def plot_case_map_for_year(df_all: pd.DataFrame,
                           gdf_county: gpd.GeoDataFrame,
                           year_sel: int):
    df_y = df_all[df_all["year"] == year_sel].copy()
    if df_y.empty:
        print("[INFO] Notebook progress message.")
        return

    gdf = gdf_county.merge(
        df_y[["county_code", "case_type"]],
        on="county_code",
        how="left"
    )

    color_map = {
        "hit": "tab:green",
        "miss": "tab:red",
        "false_alarm": "tab:orange",
        "correct_neg": "lightgrey",
        "unknown": "white",
    }
    gdf["case_color"] = gdf["case_type"].map(color_map).fillna("white")

    fig, ax = plt.subplots(1, 1, figsize=(8, 7))
    gdf.plot(color=gdf["case_color"], edgecolor="black", linewidth=0.2, ax=ax)

    ax.set_title(
        f"COUNTY: CaMa vs DFO, {year_sel}\n"
        "仅 DFO-active 县：hit=CaMa&DFO; miss=DFO only; false_alarm=CaMa only",
        fontsize=11
    )
    ax.set_axis_off()

    import matplotlib.patches as mpatches
    patches = [
        mpatches.Patch(color=color_map["hit"], label="Hit (CaMa=1, DFO=1)"),
        mpatches.Patch(color=color_map["miss"], label="Miss (CaMa=0, DFO=1)"),
        mpatches.Patch(color=color_map["false_alarm"], label="False alarm (CaMa=1, DFO=0)"),
        mpatches.Patch(color=color_map["correct_neg"], label="Correct neg (CaMa=0, DFO=0)"),
    ]
    ax.legend(handles=patches, loc="lower left", fontsize=8, frameon=True)

    fig.tight_layout()
    out_png = os.path.join(
        OUT_DIR, f"county_map_case_{year_sel}_DFOactive.png"
    )
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    print("[INFO] Notebook progress message.")


# =============================================================================

def compute_county_hit_false_rates(df_all: pd.DataFrame) -> pd.DataFrame:
    df = df_all.copy()
    df["H"] = (df["case_type"] == "hit").astype(int)
    df["M"] = (df["case_type"] == "miss").astype(int)
    df["F"] = (df["case_type"] == "false_alarm").astype(int)
    df["C"] = (df["case_type"] == "correct_neg").astype(int)

    grp = df.groupby("county_code", as_index=False).agg(
        H=("H", "sum"),
        M=("M", "sum"),
        F=("F", "sum"),
        C=("C", "sum"),
    )

    # External flood dataset comparison note.
    grp["hit_rate_DFOyears"] = grp["H"] / (grp["H"] + grp["M"])
    grp.loc[(grp["H"] + grp["M"]) == 0, "hit_rate_DFOyears"] = np.nan

    # CaMa-Flood processing note.
    grp["false_alarm_rate_CAMAYears"] = grp["F"] / (grp["H"] + grp["F"])
    grp.loc[(grp["H"] + grp["F"]) == 0, "false_alarm_rate_CAMAYears"] = np.nan

    return grp


def plot_rate_map(gdf_county: gpd.GeoDataFrame,
                  df_rates: pd.DataFrame,
                  col: str,
                  vmin=0.0,
                  vmax=1.0,
                  title: str = "",
                  fname: str = ""):
    gdf = gdf_county.merge(df_rates[["county_code", col]], on="county_code", how="left")

    fig, ax = plt.subplots(1, 1, figsize=(8, 7))
    gdf.plot(
        column=col,
        cmap="viridis",
        vmin=vmin,
        vmax=vmax,
        missing_kwds={"color": "lightgrey"},
        edgecolor="black",
        linewidth=0.2,
        ax=ax,
        legend=True
    )
    ax.set_title(title, fontsize=11)
    ax.set_axis_off()

    fig.tight_layout()
    out_png = os.path.join(OUT_DIR, fname)
    fig.savefig(out_png, dpi=300)
    plt.show()
    print("[INFO] Notebook progress message.")


def plot_rate_hist_stacked(df_rates: pd.DataFrame,
                           col1: str,
                           col2: str,
                           bins: int = 20,
                           title: str = "",
                           fname: str = ""):
    """Archived notebook note for 02_county_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    data1 = df_rates[col1].dropna().values
    data2 = df_rates[col2].dropna().values

    if (data1.size == 0) or (data2.size == 0):
        print("[INFO] Notebook progress message.")
        return

    mean1 = data1.mean()
    mean2 = data2.mean()

    bins_edges = np.linspace(0.0, 1.0, bins + 1)
    counts1, edges = np.histogram(data1, bins=bins_edges)
    counts2, _     = np.histogram(data2, bins=bins_edges)

    centers = (edges[:-1] + edges[1:]) / 2.0
    width   = edges[1] - edges[0]

    fig, ax = plt.subplots(1, 1, figsize=(7, 4))

    ax.bar(
        centers,
        counts1,
        width=width * 0.8,
        color="red",
        label="Hit rate"
    )
    ax.bar(
        centers,
        counts2,
        width=width * 0.8,
        bottom=counts1,
        color="blue",
        label="False alarm rate"
    )

    ax.axvline(mean1, linestyle="--", linewidth=1.5, color="red",
               label=f"Hit mean = {mean1:.2f}")
    ax.axvline(mean2, linestyle="--", linewidth=1.5, color="blue",
               label=f"False mean = {mean2:.2f}")

    ax.set_xlim(0.0, 1.0)
    ax.set_xlabel("Rate")
    ax.set_ylabel("Number of counties")
    ax.set_title(title, fontsize=11)

    handles, labels = ax.get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    ax.legend(unique.values(), unique.keys(), fontsize=8, frameon=True, loc="upper right")

    fig.tight_layout()
    out_png = os.path.join(OUT_DIR, fname)
    fig.savefig(out_png, dpi=300)
    plt.show()
    print("[INFO] Notebook progress message.")


# =============================================================================

def main():
    print("[INFO] Notebook progress message.")
    df = merge_cama_dfo()
    df = classify_cases(df)

    # External flood dataset comparison note.
    active_codes = df["county_code"].unique()

    print("[INFO] Notebook progress message.")
    gdf_county = load_county_gdf(active_codes)

    # =============================================================================
    year_example = 1998
    print("[INFO] Notebook progress message.")
    plot_case_map_for_year(df, gdf_county, year_example)

    # =============================================================================
    print("[INFO] Notebook progress message.")
    df_rates = compute_county_hit_false_rates(df)

    # Original notebook comment normalized for the public code archive.
    plot_rate_map(
        gdf_county,
        df_rates,
        col="hit_rate_DFOyears",
        vmin=0.0,
        vmax=1.0,
        title=f"县级 CaMa 对 DFO 事件命中率 H/(H+M)\n"
              f"{YEAR_MIN}-{YEAR_MAX}, 仅 DFO-active 县",
        fname=f"county_map_hit_rate_{YEAR_MIN}_{YEAR_MAX}_DFOactive.png"
    )

    plot_rate_map(
        gdf_county,
        df_rates,
        col="false_alarm_rate_CAMAYears",
        vmin=0.0,
        vmax=1.0,
        title=f"县级 CaMa 虚警率 F/(H+F)\n"
              f"{YEAR_MIN}-{YEAR_MAX}, 仅 DFO-active 县",
        fname=f"county_map_false_alarm_rate_{YEAR_MIN}_{YEAR_MAX}_DFOactive.png"
    )

    # Original notebook comment normalized for the public code archive.
    plot_rate_hist_stacked(
        df_rates,
        col1="hit_rate_DFOyears",
        col2="false_alarm_rate_CAMAYears",
        bins=20,
        title=f"县级 CaMa 命中率与虚警率分布（堆叠直方图）\n"
              f"{YEAR_MIN}-{YEAR_MAX}, 仅 DFO-active 县",
        fname=f"county_hist_stacked_hit_false_{YEAR_MIN}_{YEAR_MAX}_DFOactive.png"
    )

    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 5
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 02_county_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point

# =============================================================================

BASE_DIR = "/home/ll/jupyter_notebook"

# CaMa-Flood processing note.
CAMA_CSV = os.path.join(
    BASE_DIR,
    "result/county_storage_return_events/"
    "county_flood_events_T10_20_50_100_1980_2020.csv"
)

# External flood dataset comparison note.
DFO_CSV = os.path.join(
    BASE_DIR,
    "result/impact_assessment/flood/county_year_panel_DFO.csv"
)

# Original notebook comment normalized for the public code archive.
COUNTY_SHP = os.path.join(
    BASE_DIR,
    "gis_data/China/country/country.shp"
)
COUNTY_ID_FIELD = "县代码"

# Original notebook comment normalized for the public code archive.
OUT_DIR = os.path.join(
    BASE_DIR,
    "result/impact_assessment/older/fig_CaMa_DFO_hits_county_DFOactive"
)
os.makedirs(OUT_DIR, exist_ok=True)

# Original notebook comment normalized for the public code archive.
EXPORT_DIR = os.path.join(
    BASE_DIR,
    "result/windows/验证/县"
)
os.makedirs(EXPORT_DIR, exist_ok=True)

# Original notebook comment normalized for the public code archive.
YEAR_MIN = 1985           # External flood dataset comparison note.
YEAR_MAX = 2020           # External flood dataset comparison note.

# External flood dataset comparison note.
DFO_COL = "flooded_any"

# External flood dataset comparison note.
ONLY_DFO_ACTIVE = True


# =============================================================================

def load_cama_events(path: str) -> pd.DataFrame:
    """Archived notebook note for 02_county_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = pd.read_csv(path, dtype={"county_code": str})

    if "county_code" not in df.columns:
        raise RuntimeError("CaMa 县级事件表中缺少 county_code 列，请检查输出。")

    cama_cols = [c for c in df.columns if c.startswith("flood_ge_T")]
    if not cama_cols:
        raise RuntimeError("CaMa 县级事件表中未找到 flood_ge_T* 列。")

    for c in cama_cols:
        df[c] = df[c].astype(int)

    df["cama_any_event"] = (df[cama_cols].max(axis=1) > 0).astype(int)

    out = df[["year", "county_code", "cama_any_event"] + cama_cols].copy()
    return out


def load_dfo_panel(path: str) -> pd.DataFrame:
    """Archived notebook note for 02_county_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = pd.read_csv(path, dtype={"county_code": str})
    if DFO_COL not in df.columns:
        raise RuntimeError(f"DFO 县面板中缺少列: {DFO_COL}")
    df[DFO_COL] = df[DFO_COL].astype(int)
    out = df[["year", "county_code", DFO_COL]].copy()
    return out


def merge_cama_dfo() -> pd.DataFrame:
    """Archived notebook note for 02_county_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df_cama = load_cama_events(CAMA_CSV)
    df_dfo  = load_dfo_panel(DFO_CSV)

    df = df_cama.merge(df_dfo, on=["county_code", "year"], how="inner")

    df = df[(df["year"] >= YEAR_MIN) & (df["year"] <= YEAR_MAX)].copy()
    print("[INFO] Notebook progress message.")

    if ONLY_DFO_ACTIVE:
        s = df.groupby("county_code")[DFO_COL].sum()
        active = s[s > 0].index
        df = df[df["county_code"].isin(active)].copy()
        print("[INFO] Notebook progress message.")
        print("[INFO] Notebook progress message.")

    return df


# =============================================================================

def classify_cases(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 02_county_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    cama = df["cama_any_event"].astype(int)
    dfo  = df[DFO_COL].astype(int)

    conditions = [
        (cama == 1) & (dfo == 1),
        (cama == 0) & (dfo == 1),
        (cama == 1) & (dfo == 0),
        (cama == 0) & (dfo == 0),
    ]
    choices = ["hit", "miss", "false_alarm", "correct_neg"]

    df = df.copy()
    df["case_type"] = np.select(conditions, choices, default="unknown")
    return df


# =============================================================================

def load_county_gdf(active_codes: pd.Index) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(COUNTY_SHP)
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)
    else:
        gdf = gdf.to_crs(epsg=4326)

    gdf["county_code"] = gdf[COUNTY_ID_FIELD].astype(str)
    gdf = gdf[gdf["county_code"].isin(active_codes)].copy()
    print("[INFO] Notebook progress message.")
    return gdf


# =============================================================================

def plot_case_map_for_year(df_all: pd.DataFrame,
                           gdf_county: gpd.GeoDataFrame,
                           year_sel: int):
    df_y = df_all[df_all["year"] == year_sel].copy()
    if df_y.empty:
        print("[INFO] Notebook progress message.")
        return

    gdf = gdf_county.merge(
        df_y[["county_code", "case_type"]],
        on="county_code",
        how="left"
    )

    color_map = {
        "hit": "tab:green",
        "miss": "tab:red",
        "false_alarm": "tab:orange",
        "correct_neg": "lightgrey",
        "unknown": "white",
    }
    gdf["case_color"] = gdf["case_type"].map(color_map).fillna("white")

    fig, ax = plt.subplots(1, 1, figsize=(8, 7))
    gdf.plot(color=gdf["case_color"], edgecolor="black", linewidth=0.2, ax=ax)

    ax.set_title(
        f"COUNTY: CaMa vs DFO, {year_sel}\n"
        "仅 DFO-active 县：hit=CaMa&DFO; miss=DFO only; false_alarm=CaMa only",
        fontsize=11
    )
    ax.set_axis_off()

    import matplotlib.patches as mpatches
    patches = [
        mpatches.Patch(color=color_map["hit"], label="Hit (CaMa=1, DFO=1)"),
        mpatches.Patch(color=color_map["miss"], label="Miss (CaMa=0, DFO=1)"),
        mpatches.Patch(color=color_map["false_alarm"], label="False alarm (CaMa=1, DFO=0)"),
        mpatches.Patch(color=color_map["correct_neg"], label="Correct neg (CaMa=0, DFO=0)"),
    ]
    ax.legend(handles=patches, loc="lower left", fontsize=8, frameon=True)

    fig.tight_layout()
    out_png = os.path.join(
        OUT_DIR, f"county_map_case_{year_sel}_DFOactive.png"
    )
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    print("[INFO] Notebook progress message.")


# =============================================================================

def compute_county_hit_false_rates(df_all: pd.DataFrame) -> pd.DataFrame:
    df = df_all.copy()
    df["H"] = (df["case_type"] == "hit").astype(int)
    df["M"] = (df["case_type"] == "miss").astype(int)
    df["F"] = (df["case_type"] == "false_alarm").astype(int)
    df["C"] = (df["case_type"] == "correct_neg").astype(int)

    grp = df.groupby("county_code", as_index=False).agg(
        H=("H", "sum"),
        M=("M", "sum"),
        F=("F", "sum"),
        C=("C", "sum"),
    )

    grp["hit_rate_DFOyears"] = grp["H"] / (grp["H"] + grp["M"])
    grp.loc[(grp["H"] + grp["M"]) == 0, "hit_rate_DFOyears"] = np.nan

    grp["false_alarm_rate_CAMAYears"] = grp["F"] / (grp["H"] + grp["F"])
    grp.loc[(grp["H"] + grp["F"]) == 0, "false_alarm_rate_CAMAYears"] = np.nan

    return grp


def plot_rate_map(gdf_county: gpd.GeoDataFrame,
                  df_rates: pd.DataFrame,
                  col: str,
                  vmin=0.0,
                  vmax=1.0,
                  title: str = "",
                  fname: str = ""):
    gdf = gdf_county.merge(df_rates[["county_code", col]], on="county_code", how="left")

    fig, ax = plt.subplots(1, 1, figsize=(8, 7))
    gdf.plot(
        column=col,
        cmap="viridis",
        vmin=vmin,
        vmax=vmax,
        missing_kwds={"color": "lightgrey"},
        edgecolor="black",
        linewidth=0.2,
        ax=ax,
        legend=True
    )
    ax.set_title(title, fontsize=11)
    ax.set_axis_off()

    fig.tight_layout()
    out_png = os.path.join(OUT_DIR, fname)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    print("[INFO] Notebook progress message.")


def plot_rate_hist_stacked(df_rates: pd.DataFrame,
                           col1: str,
                           col2: str,
                           bins: int = 20,
                           title: str = "",
                           fname: str = ""):
    """Archived notebook note for 02_county_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    data1 = df_rates[col1].dropna().values
    data2 = df_rates[col2].dropna().values

    if (data1.size == 0) or (data2.size == 0):
        print("[INFO] Notebook progress message.")
        return

    mean1 = data1.mean()
    mean2 = data2.mean()

    bins_edges = np.linspace(0.0, 1.0, bins + 1)
    counts1, edges = np.histogram(data1, bins=bins_edges)
    counts2, _     = np.histogram(data2, bins=bins_edges)

    centers = (edges[:-1] + edges[1:]) / 2.0
    width   = edges[1] - edges[0]

    fig, ax = plt.subplots(1, 1, figsize=(7, 4))

    ax.bar(
        centers,
        counts1,
        width=width * 0.8,
        color="red",
        label="Hit rate"
    )
    ax.bar(
        centers,
        counts2,
        width=width * 0.8,
        bottom=counts1,
        color="blue",
        label="False alarm rate"
    )

    ax.axvline(mean1, linestyle="--", linewidth=1.5, color="red",
               label=f"Hit mean = {mean1:.2f}")
    ax.axvline(mean2, linestyle="--", linewidth=1.5, color="blue",
               label=f"False mean = {mean2:.2f}")

    ax.set_xlim(0.0, 1.0)
    ax.set_xlabel("Rate")
    ax.set_ylabel("Number of counties")
    ax.set_title(title, fontsize=11)

    handles, labels = ax.get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    ax.legend(unique.values(), unique.keys(), fontsize=8, frameon=True, loc="upper right")

    fig.tight_layout()
    out_png = os.path.join(OUT_DIR, fname)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    print("[INFO] Notebook progress message.")


# =============================================================================

def export_points_and_hist_data(gdf_county: gpd.GeoDataFrame,
                                df_rates: pd.DataFrame):
    """Archived notebook note for 02_county_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

    # Original notebook comment normalized for the public code archive.
    gdf_poly = gdf_county[["county_code", "geometry"]].merge(
        df_rates[["county_code", "H", "M", "F", "C",
                  "hit_rate_DFOyears", "false_alarm_rate_CAMAYears"]],
        on="county_code",
        how="left"
    )

    def jitter_geoms(geoms, seed: int = 42, scale: float = 0.3):
        """Archived notebook note for 02_county_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
        rng = np.random.default_rng(seed)
        pts = []
        for geom in geoms:
            if geom is None or geom.is_empty:
                pts.append(None)
                continue

            minx, miny, maxx, maxy = geom.bounds
            width = max(maxx - minx, 1e-4)
            height = max(maxy - miny, 1e-4)

            dx = (rng.random() - 0.5) * scale * width
            dy = (rng.random() - 0.5) * scale * height

            c = geom.centroid
            pts.append(Point(c.x + dx, c.y + dy))
        return pts

    # =============================================================================
    hit_attr = gdf_poly[["county_code", "hit_rate_DFOyears"]].copy()
    hit_attr = hit_attr.rename(columns={"hit_rate_DFOyears": "hit_rate"})
    hit_geom = jitter_geoms(gdf_poly.geometry, seed=42, scale=0.3)

    gdf_hit = gpd.GeoDataFrame(
        hit_attr,
        geometry=hit_geom,
        crs=gdf_poly.crs
    )

    hit_shp = os.path.join(EXPORT_DIR, "county_hit_rate_points.shp")
    gdf_hit.to_file(hit_shp)
    print("[INFO] Notebook progress message.")

    # =============================================================================
    false_attr = gdf_poly[["county_code", "false_alarm_rate_CAMAYears"]].copy()
    false_attr = false_attr.rename(columns={"false_alarm_rate_CAMAYears": "false_rate"})
    false_geom = jitter_geoms(gdf_poly.geometry, seed=123, scale=0.3)

    gdf_false = gpd.GeoDataFrame(
        false_attr,
        geometry=false_geom,
        crs=gdf_poly.crs
    )

    false_shp = os.path.join(EXPORT_DIR, "county_false_rate_points.shp")
    gdf_false.to_file(false_shp)
    print("[INFO] Notebook progress message.")

    # =============================================================================
    hist_df = df_rates[[
        "county_code", "H", "M", "F", "C",
        "hit_rate_DFOyears", "false_alarm_rate_CAMAYears"
    ]].copy()
    hist_csv = os.path.join(EXPORT_DIR, "county_hit_false_rates_for_hist.csv")
    hist_df.to_csv(hist_csv, index=False)
    print("[INFO] Notebook progress message.")


# =============================================================================

def main():
    print("[INFO] Notebook progress message.")
    df = merge_cama_dfo()
    df = classify_cases(df)

    # External flood dataset comparison note.
    active_codes = df["county_code"].unique()

    print("[INFO] Notebook progress message.")
    gdf_county = load_county_gdf(active_codes)

    # =============================================================================
    year_example = 1998
    print("[INFO] Notebook progress message.")
    plot_case_map_for_year(df, gdf_county, year_example)

    # =============================================================================
    print("[INFO] Notebook progress message.")
    df_rates = compute_county_hit_false_rates(df)

    # Original notebook comment normalized for the public code archive.
    print("[INFO] Notebook progress message.")
    export_points_and_hist_data(gdf_county, df_rates)

    # Original notebook comment normalized for the public code archive.
    plot_rate_map(
        gdf_county,
        df_rates,
        col="hit_rate_DFOyears",
        vmin=0.0,
        vmax=1.0,
        title=f"县级 CaMa 对 DFO 事件命中率 H/(H+M)\n"
              f"{YEAR_MIN}-{YEAR_MAX}, 仅 DFO-active 县",
        fname=f"county_map_hit_rate_{YEAR_MIN}_{YEAR_MAX}_DFOactive.png"
    )

    plot_rate_map(
        gdf_county,
        df_rates,
        col="false_alarm_rate_CAMAYears",
        vmin=0.0,
        vmax=1.0,
        title=f"县级 CaMa 虚警率 F/(H+F)\n"
              f"{YEAR_MIN}-{YEAR_MAX}, 仅 DFO-active 县",
        fname=f"county_map_false_alarm_rate_{YEAR_MIN}_{YEAR_MAX}_DFOactive.png"
    )

    # Original notebook comment normalized for the public code archive.
    plot_rate_hist_stacked(
        df_rates,
        col1="hit_rate_DFOyears",
        col2="false_alarm_rate_CAMAYears",
        bins=20,
        title=f"县级 CaMa 命中率与虚警率分布（堆叠直方图）\n"
              f"{YEAR_MIN}-{YEAR_MAX}, 仅 DFO-active 县",
        fname=f"county_hist_stacked_hit_false_{YEAR_MIN}_{YEAR_MAX}_DFOactive.png"
    )

    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 7
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 02_county_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =============================================================================

BASE_DIR = "/home/ll/jupyter_notebook"
DATA_DIR = os.path.join(BASE_DIR, "result/windows/验证/县")
CSV_PATH = os.path.join(DATA_DIR, "county_hit_false_rates_for_hist.csv")
OUT_PNG = os.path.join(DATA_DIR, "county_hist_stacked_hit_false_from_export.png")


def main():
    print("[INFO] Notebook progress message.")
    df = pd.read_csv(CSV_PATH)

    col_hit = "hit_rate_DFOyears"
    col_false = "false_alarm_rate_CAMAYears"

    if col_hit not in df.columns or col_false not in df.columns:
        raise RuntimeError(
            f"输入 CSV 中未找到所需列: {col_hit}, {col_false}，"
            f"请检查 county_hit_false_rates_for_hist.csv。"
        )

    data_hit = df[col_hit].dropna().values
    data_false = df[col_false].dropna().values

    if (data_hit.size == 0) or (data_false.size == 0):
        print("[INFO] Notebook progress message.")
        return

    mean_hit = data_hit.mean()
    mean_false = data_false.mean()
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")

    # =============================================================================
    bins = 20
    bins_edges = np.linspace(0.0, 1.0, bins + 1)
    counts_hit, edges = np.histogram(data_hit, bins=bins_edges)
    counts_false, _ = np.histogram(data_false, bins=bins_edges)

    centers = (edges[:-1] + edges[1:]) / 2.0
    width = edges[1] - edges[0]

    # =============================================================================
    fig, ax = plt.subplots(1, 1, figsize=(7, 4))

    # Original notebook comment normalized for the public code archive.
    ax.bar(
        centers,
        counts_hit,
        width=width * 0.8,
        color="red",
        label="Hit rate"
    )
    # Original notebook comment normalized for the public code archive.
    ax.bar(
        centers,
        counts_false,
        width=width * 0.8,
        bottom=counts_hit,
        color="blue",
        label="False alarm rate"
    )

    # Original notebook comment normalized for the public code archive.
    ax.axvline(mean_hit, linestyle="--", linewidth=1.5, color="red",
               label=f"Hit mean = {mean_hit:.2f}")
    ax.axvline(mean_false, linestyle="--", linewidth=1.5, color="blue",
               label=f"False mean = {mean_false:.2f}")

    ax.set_xlim(0.0, 1.0)
    ax.set_xlabel("Rate")
    ax.set_ylabel("Number of counties")
    ax.set_title("县级 CaMa 命中率与虚警率分布（基于导出 CSV）", fontsize=11)

    # Original notebook comment normalized for the public code archive.
    handles, labels = ax.get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    ax.legend(unique.values(), unique.keys(), fontsize=8, frameon=True, loc="upper right")

    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=300)
    plt.show()
    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 10
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 02_county_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point


# =========================
# Original notebook comment normalized for the public code archive.
# =========================
BASE_DIR = "/home/ll/jupyter_notebook"

# --- CaMa ---
CAMA_CSV = os.path.join(
    BASE_DIR,
    "result/county_storage_return_events/"
    "county_flood_events_T10_20_50_100_1980_2020.csv"
)

# =============================================================================
DFO_XLSX = os.path.join(
    BASE_DIR,
    "gis_data/DFO/PAC_yearly_occurrences_2000_2020_matched_to_country.xlsx"
)
SHEET_WIDE = "wide_counts_matched"
SHEET_WEIGHTS = "crosswalk_weights"

# =============================================================================
COUNTY_SHP = os.path.join(BASE_DIR, "gis_data/China/country/country.shp")
COUNTY_ID_FIELD = "县代码"

# =============================================================================
YEAR_MIN = 2000
YEAR_MAX = 2020

# =============================================================================
USE_WEIGHTS = True

# Original notebook comment normalized for the public code archive.
MIN_SHARE_ON_OLD = 0.0

# Original notebook comment normalized for the public code archive.
RENORMALIZE_WEIGHTS = True

# External flood dataset comparison note.
DFO_ANY_THRESH = 0.0

# External flood dataset comparison note.
ONLY_DFO_ACTIVE = True

# =============================================================================
RUN_TAG = "fromPAC"

OUT_DIR = os.path.join(
    BASE_DIR,
    f"result/impact_assessment/older/fig_CaMa_DFO_hits_county_{RUN_TAG}"
)
os.makedirs(OUT_DIR, exist_ok=True)

EXPORT_DIR = os.path.join(
    BASE_DIR,
    f"result/windows/验证/县_{RUN_TAG}"
)
os.makedirs(EXPORT_DIR, exist_ok=True)


# =========================
# Original notebook comment normalized for the public code archive.
# =========================
def norm_code(x, width=6) -> str:
    """Archived notebook note for 02_county_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if pd.isna(x):
        return None
    s = str(x).strip()
    if s.endswith(".0"):
        s = s[:-2]
    s = s.replace(" ", "")
    if width is not None and s.isdigit():
        s = s.zfill(width)
    return s


def clean_columns_for_years(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 02_county_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    new_cols = []
    for c in df.columns:
        s = str(c).strip()
        s2 = s.replace("年", "").strip()
        # Original notebook comment normalized for the public code archive.
        try:
            y = int(float(s2))
            if YEAR_MIN <= y <= YEAR_MAX:
                new_cols.append(str(y))
            else:
                new_cols.append(s)  # Original notebook comment normalized for the public code archive.
        except Exception:
            new_cols.append(s)
    df = df.copy()
    df.columns = new_cols
    return df


def detect_year_cols(df: pd.DataFrame, y0=2000, y1=2020):
    """Archived notebook note for 02_county_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    cols = []
    for c in df.columns:
        s = str(c).strip().replace("年", "")
        try:
            y = int(float(s))
            if y0 <= y <= y1:
                cols.append(str(y))
        except Exception:
            pass
    cols = sorted(set(cols), key=lambda z: int(z))
    return cols


# =========================
# CaMa-Flood processing note.
# =========================
def load_cama_events(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, dtype={"county_code": str})

    if "county_code" not in df.columns:
        raise RuntimeError("CaMa 县级事件表缺少 county_code 列。")

    cama_cols = [c for c in df.columns if c.startswith("flood_ge_T")]
    if not cama_cols:
        raise RuntimeError("CaMa 县级事件表未找到 flood_ge_T* 列。")

    for c in cama_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)

    df["cama_any_event"] = (df[cama_cols].max(axis=1) > 0).astype(int)

    df["county_code"] = df["county_code"].apply(norm_code)
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype(int)

    df = df[(df["year"] >= YEAR_MIN) & (df["year"] <= YEAR_MAX)].copy()
    return df[["county_code", "year", "cama_any_event"] + cama_cols].copy()


# =========================
# External flood dataset comparison note.
# =========================
def load_dfo_any_from_excel(xlsx_path: str) -> pd.DataFrame:
    # =============================================================================
    df_wide = pd.read_excel(xlsx_path, sheet_name=SHEET_WIDE)
    df_wide = clean_columns_for_years(df_wide)

    # Original notebook comment normalized for the public code archive.
    print("[DEBUG] wide_counts_matched columns head:", list(df_wide.columns)[:30])

    if "PAC" not in df_wide.columns:
        raise RuntimeError(f"{SHEET_WIDE} 缺少 PAC 列。")
    if "new_code" not in df_wide.columns:
        raise RuntimeError(f"{SHEET_WIDE} 缺少 new_code 列。")

    year_cols = detect_year_cols(df_wide, YEAR_MIN, YEAR_MAX)
    if not year_cols:
        raise RuntimeError(f"{SHEET_WIDE} 未检测到 {YEAR_MIN}-{YEAR_MAX} 的年份列。")

    # Original notebook comment normalized for the public code archive.
    df_wide["PAC"] = df_wide["PAC"].apply(lambda x: norm_code(x, width=None))  # Original notebook comment normalized for the public code archive.
    df_wide["new_code"] = df_wide["new_code"].apply(norm_code)

    # Original notebook comment normalized for the public code archive.
    for y in year_cols:
        if y not in df_wide.columns:
            raise RuntimeError(f"[ERROR] 年份列 {y} 不在 wide 表列名中。请检查列名清洗逻辑。")
        df_wide[y] = pd.to_numeric(df_wide[y], errors="coerce").fillna(0)

    # wide -> long：PAC×year -> count
    df_long = df_wide[["PAC", "new_code"] + year_cols].melt(
        id_vars=["PAC", "new_code"],
        value_vars=year_cols,
        var_name="year",
        value_name="dfo_count_raw"
    )
    df_long["year"] = df_long["year"].astype(int)

    # =============================================================================
    if USE_WEIGHTS:
        df_w = pd.read_excel(xlsx_path, sheet_name=SHEET_WEIGHTS)

        need_cols = {"PAC", "county_code", "share_on_old"}
        missing = need_cols - set(df_w.columns)
        if missing:
            raise RuntimeError(f"{SHEET_WEIGHTS} 缺少列: {missing}")

        df_w["PAC"] = df_w["PAC"].apply(lambda x: norm_code(x, width=None))
        df_w["county_code"] = df_w["county_code"].apply(norm_code)
        df_w["share_on_old"] = pd.to_numeric(df_w["share_on_old"], errors="coerce")

        df_w = df_w.dropna(subset=["PAC", "county_code", "share_on_old"]).copy()
        df_w = df_w[df_w["share_on_old"] >= MIN_SHARE_ON_OLD].copy()

        if df_w.empty:
            raise RuntimeError("weights 过滤后为空：请检查 MIN_SHARE_ON_OLD 或源表内容。")

        if RENORMALIZE_WEIGHTS:
            s = df_w.groupby("PAC")["share_on_old"].transform("sum")
            df_w = df_w[s > 0].copy()
            df_w["w"] = df_w["share_on_old"] / s
        else:
            df_w["w"] = df_w["share_on_old"]

        # County-level processing note.
        df_alloc = df_long.merge(df_w[["PAC", "county_code", "w"]], on="PAC", how="inner")
        df_alloc["dfo_count"] = df_alloc["dfo_count_raw"] * df_alloc["w"]

        df_county = df_alloc.groupby(["county_code", "year"], as_index=False).agg(
            dfo_count=("dfo_count", "sum")
        )
    else:
        # Original notebook comment normalized for the public code archive.
        df_county = df_long.dropna(subset=["new_code"]).copy()
        df_county = df_county.rename(columns={"new_code": "county_code"})
        df_county = df_county.groupby(["county_code", "year"], as_index=False).agg(
            dfo_count=("dfo_count_raw", "sum")
        )

    # Original notebook comment normalized for the public code archive.
    df_county["dfo_any"] = (df_county["dfo_count"] > DFO_ANY_THRESH).astype(int)

    out_csv = os.path.join(EXPORT_DIR, f"county_year_panel_DFO_any_{RUN_TAG}.csv")
    df_county.to_csv(out_csv, index=False)
    print("[INFO] Notebook progress message.")

    return df_county


# =========================
# Original notebook comment normalized for the public code archive.
# =========================
def classify_cases(df: pd.DataFrame) -> pd.DataFrame:
    cama = df["cama_any_event"].astype(int)
    dfo = df["dfo_any"].astype(int)

    conditions = [
        (cama == 1) & (dfo == 1),
        (cama == 0) & (dfo == 1),
        (cama == 1) & (dfo == 0),
        (cama == 0) & (dfo == 0),
    ]
    choices = ["hit", "miss", "false_alarm", "correct_neg"]

    df = df.copy()
    df["case_type"] = np.select(conditions, choices, default="unknown")
    return df


def compute_county_hit_false_rates(df_all: pd.DataFrame) -> pd.DataFrame:
    df = df_all.copy()
    df["H"] = (df["case_type"] == "hit").astype(int)
    df["M"] = (df["case_type"] == "miss").astype(int)
    df["F"] = (df["case_type"] == "false_alarm").astype(int)
    df["C"] = (df["case_type"] == "correct_neg").astype(int)

    grp = df.groupby("county_code", as_index=False).agg(
        H=("H", "sum"),
        M=("M", "sum"),
        F=("F", "sum"),
        C=("C", "sum"),
    )

    grp["hit_rate_DFOyears"] = grp["H"] / (grp["H"] + grp["M"])
    grp.loc[(grp["H"] + grp["M"]) == 0, "hit_rate_DFOyears"] = np.nan

    grp["false_alarm_rate_CAMAYears"] = grp["F"] / (grp["H"] + grp["F"])
    grp.loc[(grp["H"] + grp["F"]) == 0, "false_alarm_rate_CAMAYears"] = np.nan

    return grp


# =========================
# Original notebook comment normalized for the public code archive.
# =========================
def load_county_gdf(active_codes) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(COUNTY_SHP)
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)
    else:
        gdf = gdf.to_crs(epsg=4326)

    gdf["county_code"] = gdf[COUNTY_ID_FIELD].apply(norm_code)
    gdf = gdf[gdf["county_code"].isin(set(active_codes))].copy()
    print("[INFO] Notebook progress message.")
    return gdf


def plot_case_map_for_year(df_all, gdf_county, year_sel: int):
    df_y = df_all[df_all["year"] == year_sel].copy()
    if df_y.empty:
        print("[INFO] Notebook progress message.")
        return

    gdf = gdf_county.merge(df_y[["county_code", "case_type"]], on="county_code", how="left")

    color_map = {
        "hit": "tab:green",
        "miss": "tab:red",
        "false_alarm": "tab:orange",
        "correct_neg": "lightgrey",
        "unknown": "white",
    }
    gdf["case_color"] = gdf["case_type"].map(color_map).fillna("white")

    fig, ax = plt.subplots(1, 1, figsize=(8, 7))
    gdf.plot(color=gdf["case_color"], edgecolor="black", linewidth=0.2, ax=ax)

    ax.set_title(
        f"COUNTY: CaMa vs DFO(any from PAC), {year_sel}\n"
        f"hit=CaMa&DFO; miss=DFO only; false_alarm=CaMa only ({RUN_TAG})",
        fontsize=11
    )
    ax.set_axis_off()

    import matplotlib.patches as mpatches
    patches = [
        mpatches.Patch(color=color_map["hit"], label="Hit (CaMa=1, DFO=1)"),
        mpatches.Patch(color=color_map["miss"], label="Miss (CaMa=0, DFO=1)"),
        mpatches.Patch(color=color_map["false_alarm"], label="False alarm (CaMa=1, DFO=0)"),
        mpatches.Patch(color=color_map["correct_neg"], label="Correct neg (CaMa=0, DFO=0)"),
    ]
    ax.legend(handles=patches, loc="lower left", fontsize=8, frameon=True)

    fig.tight_layout()
    out_png = os.path.join(OUT_DIR, f"county_map_case_{year_sel}_{RUN_TAG}.png")
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    print("[INFO] Notebook progress message.")


def plot_rate_map(gdf_county, df_rates, col, title, fname, vmin=0.0, vmax=1.0):
    gdf = gdf_county.merge(df_rates[["county_code", col]], on="county_code", how="left")

    fig, ax = plt.subplots(1, 1, figsize=(8, 7))
    gdf.plot(
        column=col,
        cmap="viridis",
        vmin=vmin,
        vmax=vmax,
        missing_kwds={"color": "lightgrey"},
        edgecolor="black",
        linewidth=0.2,
        ax=ax,
        legend=True
    )
    ax.set_title(title, fontsize=11)
    ax.set_axis_off()

    fig.tight_layout()
    out_png = os.path.join(OUT_DIR, fname)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    print("[INFO] Notebook progress message.")


def plot_rate_hist_stacked(df_rates, col1, col2, bins=20, title="", fname=""):
    data1 = df_rates[col1].dropna().values
    data2 = df_rates[col2].dropna().values
    if (data1.size == 0) or (data2.size == 0):
        print("[INFO] Notebook progress message.")
        return

    mean1 = data1.mean()
    mean2 = data2.mean()

    bins_edges = np.linspace(0.0, 1.0, bins + 1)
    counts1, edges = np.histogram(data1, bins=bins_edges)
    counts2, _ = np.histogram(data2, bins=bins_edges)

    centers = (edges[:-1] + edges[1:]) / 2.0
    width = edges[1] - edges[0]

    fig, ax = plt.subplots(1, 1, figsize=(7, 4))
    ax.bar(centers, counts1, width=width * 0.8, color="red", label="Hit rate")
    ax.bar(centers, counts2, width=width * 0.8, bottom=counts1, color="blue", label="False alarm rate")

    ax.axvline(mean1, linestyle="--", linewidth=1.5, color="red", label=f"Hit mean = {mean1:.2f}")
    ax.axvline(mean2, linestyle="--", linewidth=1.5, color="blue", label=f"False mean = {mean2:.2f}")

    ax.set_xlim(0.0, 1.0)
    ax.set_xlabel("Rate")
    ax.set_ylabel("Number of counties")
    ax.set_title(title, fontsize=11)

    handles, labels = ax.get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    ax.legend(unique.values(), unique.keys(), fontsize=8, frameon=True, loc="upper right")

    fig.tight_layout()
    out_png = os.path.join(OUT_DIR, fname)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    print("[INFO] Notebook progress message.")


def export_points_and_hist_data(gdf_county, df_rates):
    gdf_poly = gdf_county[["county_code", "geometry"]].merge(
        df_rates[["county_code", "H", "M", "F", "C",
                  "hit_rate_DFOyears", "false_alarm_rate_CAMAYears"]],
        on="county_code",
        how="left"
    )

    def jitter_geoms(geoms, seed=42, scale=0.3):
        rng = np.random.default_rng(seed)
        pts = []
        for geom in geoms:
            if geom is None or geom.is_empty:
                pts.append(None)
                continue
            minx, miny, maxx, maxy = geom.bounds
            width = max(maxx - minx, 1e-4)
            height = max(maxy - miny, 1e-4)
            dx = (rng.random() - 0.5) * scale * width
            dy = (rng.random() - 0.5) * scale * height
            c = geom.centroid
            pts.append(Point(c.x + dx, c.y + dy))
        return pts

    hit_attr = gdf_poly[["county_code", "hit_rate_DFOyears"]].copy()
    hit_attr = hit_attr.rename(columns={"county_code": "code", "hit_rate_DFOyears": "hit_rate"})
    gdf_hit = gpd.GeoDataFrame(hit_attr, geometry=jitter_geoms(gdf_poly.geometry, seed=42, scale=0.3), crs=gdf_poly.crs)
    hit_shp = os.path.join(EXPORT_DIR, f"county_hit_rate_points_{RUN_TAG}.shp")
    gdf_hit.to_file(hit_shp)
    print("[INFO] Notebook progress message.")

    fa_attr = gdf_poly[["county_code", "false_alarm_rate_CAMAYears"]].copy()
    fa_attr = fa_attr.rename(columns={"county_code": "code", "false_alarm_rate_CAMAYears": "fa_rate"})
    gdf_fa = gpd.GeoDataFrame(fa_attr, geometry=jitter_geoms(gdf_poly.geometry, seed=123, scale=0.3), crs=gdf_poly.crs)
    fa_shp = os.path.join(EXPORT_DIR, f"county_false_rate_points_{RUN_TAG}.shp")
    gdf_fa.to_file(fa_shp)
    print("[INFO] Notebook progress message.")

    hist_df = df_rates[[
        "county_code", "H", "M", "F", "C",
        "hit_rate_DFOyears", "false_alarm_rate_CAMAYears"
    ]].copy()
    hist_csv = os.path.join(EXPORT_DIR, f"county_hit_false_rates_for_hist_{RUN_TAG}.csv")
    hist_df.to_csv(hist_csv, index=False)
    print("[INFO] Notebook progress message.")


# =========================
# Original notebook comment normalized for the public code archive.
# =========================
def main():
    print("[INFO] Notebook progress message.")
    df_cama = load_cama_events(CAMA_CSV)
    print("[INFO] Notebook progress message.")

    print("[INFO] Notebook progress message.")
    df_dfo = load_dfo_any_from_excel(DFO_XLSX)
    print("[INFO] Notebook progress message.")

    print("[INFO] Notebook progress message.")
    df = df_cama.merge(df_dfo, on=["county_code", "year"], how="inner")
    print("[INFO] Notebook progress message.")

    if ONLY_DFO_ACTIVE:
        s = df.groupby("county_code")["dfo_any"].sum()
        active = s[s > 0].index
        df = df[df["county_code"].isin(active)].copy()
        print("[INFO] Notebook progress message.")
    else:
        active = df["county_code"].unique()

    merged_csv = os.path.join(EXPORT_DIR, f"county_year_panel_CaMa_DFO_merged_{RUN_TAG}.csv")
    df.to_csv(merged_csv, index=False)
    print("[INFO] Notebook progress message.")

    print("[INFO] Notebook progress message.")
    df = classify_cases(df)

    print("[INFO] Notebook progress message.")
    gdf_county = load_county_gdf(active)

    year_example = 2010
    print("[INFO] Notebook progress message.")
    plot_case_map_for_year(df, gdf_county, year_example)

    print("[INFO] Notebook progress message.")
    df_rates = compute_county_hit_false_rates(df)

    print("[INFO] Notebook progress message.")
    export_points_and_hist_data(gdf_county, df_rates)

    print("[INFO] Notebook progress message.")
    plot_rate_map(
        gdf_county, df_rates,
        col="hit_rate_DFOyears",
        title=f"县级 CaMa 命中率 H/(H+M)\n{YEAR_MIN}-{YEAR_MAX}, {RUN_TAG}",
        fname=f"county_map_hit_rate_{YEAR_MIN}_{YEAR_MAX}_{RUN_TAG}.png"
    )
    plot_rate_map(
        gdf_county, df_rates,
        col="false_alarm_rate_CAMAYears",
        title=f"县级 CaMa 虚警率 F/(H+F)\n{YEAR_MIN}-{YEAR_MAX}, {RUN_TAG}",
        fname=f"county_map_false_alarm_rate_{YEAR_MIN}_{YEAR_MAX}_{RUN_TAG}.png"
    )

    print("[INFO] Notebook progress message.")
    plot_rate_hist_stacked(
        df_rates,
        col1="hit_rate_DFOyears",
        col2="false_alarm_rate_CAMAYears",
        bins=20,
        title=f"县级 CaMa 命中率与虚警率分布（堆叠直方图）\n{YEAR_MIN}-{YEAR_MAX}, {RUN_TAG}",
        fname=f"county_hist_stacked_hit_false_{YEAR_MIN}_{YEAR_MAX}_{RUN_TAG}.png"
    )

    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 12
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob
import shutil
import pandas as pd

# =============================================================================
OUT_DIR = "/home/ll/jupyter_notebook/result/impact_assessment/older/fig_CaMa_DFO_hits_county_fromPAC"
EXPORT_DIR = "/home/ll/jupyter_notebook/result/windows/验证/县_fromPAC"

# =============================================================================
DEST_DIR = "/home/ll/jupyter_notebook/result/windows/country_flood"
os.makedirs(DEST_DIR, exist_ok=True)

def copy_file(src, dst_dir):
    os.makedirs(dst_dir, exist_ok=True)
    dst = os.path.join(dst_dir, os.path.basename(src))
    shutil.copy2(src, dst)
    return dst

def copy_shapefile(shp_path, dst_dir):
    """Archived notebook note for 02_county_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    base, _ = os.path.splitext(shp_path)
    exts = [".shp", ".shx", ".dbf", ".prj", ".cpg", ".qpj", ".sbn", ".sbx", ".fix"]
    copied = []
    for ext in exts:
        f = base + ext
        if os.path.exists(f):
            copied.append(copy_file(f, dst_dir))
    if not copied:
        raise FileNotFoundError(f"未找到任何 shapefile 组成文件: {shp_path}")
    return copied

# =============================================================================
png_files = glob.glob(os.path.join(OUT_DIR, "*.png"))
for f in png_files:
    copy_file(f, DEST_DIR)

# =============================================================================
csv_files = glob.glob(os.path.join(EXPORT_DIR, "*.csv"))
for f in csv_files:
    copy_file(f, DEST_DIR)

# =============================================================================
hit_shp = os.path.join(EXPORT_DIR, "county_hit_rate_points_fromPAC.shp")
false_shp = os.path.join(EXPORT_DIR, "county_false_rate_points_fromPAC.shp")
copy_shapefile(hit_shp, DEST_DIR)
copy_shapefile(false_shp, DEST_DIR)

print("[INFO] Notebook progress message.")
print(f"[INFO] PNG copied: {len(png_files)}")
print(f"[INFO] CSV copied: {len(csv_files)}")
print("[INFO] SHP copied: hit/false (with sidecar files)")

# =============================================================================
hist_csv_new = os.path.join(DEST_DIR, "county_hit_false_rates_for_hist_fromPAC.csv")
if not os.path.exists(hist_csv_new):
    raise FileNotFoundError(f"新路径下未找到直方图 CSV: {hist_csv_new}")

df_hist = pd.read_csv(hist_csv_new)

col_hit = "hit_rate_DFOyears"
col_false = "false_alarm_rate_CAMAYears"

print("[INFO] Notebook progress message.")
print(hist_csv_new)

# Original notebook comment normalized for the public code archive.
print("[INFO] Notebook progress message.")
print(df_hist.head(10))

# Original notebook comment normalized for the public code archive.
hit_valid = df_hist[col_hit].dropna()
false_valid = df_hist[col_false].dropna()

print("\n[HIST SUMMARY]")
print(f"N counties (hit_rate not NA)   : {hit_valid.shape[0]}")
print(f"N counties (false_rate not NA) : {false_valid.shape[0]}")
print(f"Hit rate mean   : {hit_valid.mean():.4f}")
print(f"Hit rate median : {hit_valid.median():.4f}")
print(f"False rate mean : {false_valid.mean():.4f}")
print(f"False rate median: {false_valid.median():.4f}")


# ------------------------------------------------------------------------------
# Notebook cell 13
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 02_county_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =============================================================================
BASE_DIR = "/home/ll/jupyter_notebook"
DATA_DIR = os.path.join(BASE_DIR, "result/windows/country_flood")

CSV_PATH = os.path.join(DATA_DIR, "county_hit_false_rates_for_hist_fromPAC.csv")
OUT_PNG = os.path.join(DATA_DIR, "county_hist_stacked_hit_false_2000_2020_fromPAC_fromCountryFlood.png")

# =============================================================================
COL_HIT = "hit_rate_DFOyears"
COL_FALSE = "false_alarm_rate_CAMAYears"
BINS = 20
XRANGE = (0.0, 1.0)

TITLE = "县级 CaMa 命中率与虚警率分布（堆叠直方图）\n2000–2020（数据源：country_flood）"


def main():
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"未找到输入 CSV: {CSV_PATH}")

    print("[INFO] Notebook progress message.")
    df = pd.read_csv(CSV_PATH)

    # Original notebook comment normalized for the public code archive.
    for c in [COL_HIT, COL_FALSE]:
        if c not in df.columns:
            raise RuntimeError(f"输入 CSV 缺少列: {c}。现有列: {list(df.columns)}")

    data_hit = pd.to_numeric(df[COL_HIT], errors="coerce").dropna().values
    data_false = pd.to_numeric(df[COL_FALSE], errors="coerce").dropna().values

    if (data_hit.size == 0) or (data_false.size == 0):
        raise RuntimeError("命中率或虚警率为空，无法绘制直方图。")

    mean_hit = data_hit.mean()
    mean_false = data_false.mean()

    print(f"[INFO] Hit mean  : {mean_hit:.4f}")
    print(f"[INFO] False mean: {mean_false:.4f}")
    print(f"[INFO] N(hit valid)  : {data_hit.size}")
    print(f"[INFO] N(false valid): {data_false.size}")

    # =============================================================================
    bins_edges = np.linspace(XRANGE[0], XRANGE[1], BINS + 1)
    counts_hit, edges = np.histogram(data_hit, bins=bins_edges)
    counts_false, _ = np.histogram(data_false, bins=bins_edges)

    centers = (edges[:-1] + edges[1:]) / 2.0
    width = edges[1] - edges[0]

    # =============================================================================
    fig, ax = plt.subplots(1, 1, figsize=(7, 4))

    # Original notebook comment normalized for the public code archive.
    ax.bar(
        centers,
        counts_hit,
        width=width * 0.8,
        color="red",
        label="Hit rate"
    )

    # Original notebook comment normalized for the public code archive.
    ax.bar(
        centers,
        counts_false,
        width=width * 0.8,
        bottom=counts_hit,
        color="blue",
        label="False alarm rate"
    )

    # Original notebook comment normalized for the public code archive.
    ax.axvline(mean_hit, linestyle="--", linewidth=1.5, color="red",
               label=f"Hit mean = {mean_hit:.2f}")
    ax.axvline(mean_false, linestyle="--", linewidth=1.5, color="blue",
               label=f"False mean = {mean_false:.2f}")

    ax.set_xlim(*XRANGE)
    ax.set_xlabel("Rate")
    ax.set_ylabel("Number of counties")
    ax.set_title(TITLE, fontsize=11)

    # Original notebook comment normalized for the public code archive.
    handles, labels = ax.get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    ax.legend(unique.values(), unique.keys(), fontsize=8, frameon=True, loc="upper right")

    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=300)
    plt.close(fig)

    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 16
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 02_county_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt


# =========================
# Original notebook comment normalized for the public code archive.
# =========================
BASE_DIR = "/home/ll/jupyter_notebook"

CAMA_CSV = os.path.join(
    BASE_DIR,
    "result/county_storage_return_events/"
    "county_flood_events_T10_20_50_100_1980_2020.csv"
)

DFO_CSV = os.path.join(
    BASE_DIR,
    "result/impact_assessment/flood/"
    "county_year_panel_DFO.csv"
)
DFO_COL = "flooded_any"

COUNTRY_FLOOD_XLSX = os.path.join(
    BASE_DIR,
    "gis_data/DFO/PAC_yearly_occurrences_2000_2020_matched_to_country.xlsx"
)
SHEET_WIDE = "wide_counts_matched"
SHEET_WEIGHTS = "crosswalk_weights"

COUNTY_SHP = os.path.join(BASE_DIR, "gis_data/China/country/country.shp")
COUNTY_ID_FIELD = "县代码"

YEAR_MIN, YEAR_MAX = 2000, 2020

# Original notebook comment normalized for the public code archive.
USE_WEIGHTS = True
MIN_SHARE_ON_OLD = 0.0
RENORMALIZE_WEIGHTS = True

# Original notebook comment normalized for the public code archive.
ANY_THRESH = 0.0

# Original notebook comment normalized for the public code archive.
YEAR_EXAMPLE = 2010

# Original notebook comment normalized for the public code archive.
OUT_BASE = os.path.join(BASE_DIR, "result/windows/country_flood/tri_compare")
os.makedirs(OUT_BASE, exist_ok=True)


# =========================
# Original notebook comment normalized for the public code archive.
# =========================
def norm_code(x, width=6) -> str:
    if pd.isna(x):
        return None
    s = str(x).strip()
    if s.endswith(".0"):
        s = s[:-2]
    s = s.replace(" ", "")
    if width is not None and s.isdigit():
        s = s.zfill(width)
    return s


def clean_columns_for_years(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 02_county_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    new_cols = []
    for c in df.columns:
        s = str(c).strip()
        s2 = s.replace("年", "").strip()
        try:
            y = int(float(s2))
            if YEAR_MIN <= y <= YEAR_MAX:
                new_cols.append(str(y))
            else:
                new_cols.append(s)
        except Exception:
            new_cols.append(s)
    df = df.copy()
    df.columns = new_cols
    return df


def detect_year_cols(df: pd.DataFrame):
    cols = []
    for c in df.columns:
        s = str(c).strip().replace("年", "")
        try:
            y = int(float(s))
            if YEAR_MIN <= y <= YEAR_MAX:
                cols.append(str(y))
        except Exception:
            pass
    return sorted(set(cols), key=lambda z: int(z))


def consolidate_duplicate_year_cols(df: pd.DataFrame, year_cols):
    """Archived notebook note for 02_county_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()
    for y in year_cols:
        idx = np.where(df.columns == y)[0]
        if idx.size > 1:
            tmp = df.loc[:, df.columns == y].apply(pd.to_numeric, errors="coerce").fillna(0).sum(axis=1)
            # Original notebook comment normalized for the public code archive.
            df.iloc[:, idx[0]] = tmp
            # Original notebook comment normalized for the public code archive.
            drop_cols = [df.columns[i] for i in idx[1:]]
            # Original notebook comment normalized for the public code archive.
            keep_mask = np.ones(df.shape[1], dtype=bool)
            keep_mask[idx[1:]] = False
            df = df.loc[:, keep_mask]
    return df


# =========================
# CaMa-Flood processing note.
# =========================
def load_cama_any() -> pd.DataFrame:
    df = pd.read_csv(CAMA_CSV, dtype={"county_code": str})
    if "county_code" not in df.columns:
        raise RuntimeError("CaMa 表缺少 county_code 列。")

    cama_cols = [c for c in df.columns if c.startswith("flood_ge_T")]
    if not cama_cols:
        raise RuntimeError("CaMa 表未找到 flood_ge_T* 列。")

    for c in cama_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)

    df["cama_any"] = (df[cama_cols].max(axis=1) > 0).astype(int)
    df["county_code"] = df["county_code"].apply(norm_code)
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype(int)

    df = df[(df["year"] >= YEAR_MIN) & (df["year"] <= YEAR_MAX)].copy()
    return df[["county_code", "year", "cama_any"]].copy()


# =========================
# External flood dataset comparison note.
# =========================
def load_dfo_any() -> pd.DataFrame:
    df = pd.read_csv(DFO_CSV, dtype={"county_code": str})
    if DFO_COL not in df.columns:
        raise RuntimeError(f"DFO 面板缺少列：{DFO_COL}")
    df["county_code"] = df["county_code"].apply(norm_code)
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype(int)
    df["dfo_any"] = pd.to_numeric(df[DFO_COL], errors="coerce").fillna(0).astype(int)
    df = df[(df["year"] >= YEAR_MIN) & (df["year"] <= YEAR_MAX)].copy()
    return df[["county_code", "year", "dfo_any"]].copy()


# =========================
# Original notebook comment normalized for the public code archive.
# =========================
def load_country_flood_any() -> pd.DataFrame:
    df_wide = pd.read_excel(COUNTRY_FLOOD_XLSX, sheet_name=SHEET_WIDE)
    df_wide = clean_columns_for_years(df_wide)
    year_cols = detect_year_cols(df_wide)
    df_wide = consolidate_duplicate_year_cols(df_wide, year_cols)

    print("[DEBUG] wide_counts_matched columns head:", list(df_wide.columns)[:30])

    if "PAC" not in df_wide.columns:
        raise RuntimeError(f"{SHEET_WIDE} 缺少 PAC 列。")
    if "new_code" not in df_wide.columns:
        raise RuntimeError(f"{SHEET_WIDE} 缺少 new_code 列。")
    if not year_cols:
        raise RuntimeError(f"{SHEET_WIDE} 未检测到 {YEAR_MIN}-{YEAR_MAX} 年份列。")

    df_wide["PAC"] = df_wide["PAC"].apply(lambda x: norm_code(x, width=None))
    df_wide["new_code"] = df_wide["new_code"].apply(norm_code)

    for y in year_cols:
        df_wide[y] = pd.to_numeric(df_wide[y], errors="coerce").fillna(0)

    df_long = df_wide[["PAC", "new_code"] + year_cols].melt(
        id_vars=["PAC", "new_code"],
        value_vars=year_cols,
        var_name="year",
        value_name="cf_count_raw"
    )
    df_long["year"] = df_long["year"].astype(int)

    if USE_WEIGHTS:
        w = pd.read_excel(COUNTRY_FLOOD_XLSX, sheet_name=SHEET_WEIGHTS)
        need = {"PAC", "county_code", "share_on_old"}
        miss = need - set(w.columns)
        if miss:
            raise RuntimeError(f"{SHEET_WEIGHTS} 缺少列：{miss}")

        w["PAC"] = w["PAC"].apply(lambda x: norm_code(x, width=None))
        w["county_code"] = w["county_code"].apply(norm_code)
        w["share_on_old"] = pd.to_numeric(w["share_on_old"], errors="coerce")
        w = w.dropna(subset=["PAC", "county_code", "share_on_old"]).copy()
        w = w[w["share_on_old"] >= MIN_SHARE_ON_OLD].copy()
        if w.empty:
            raise RuntimeError("crosswalk_weights 过滤后为空，请检查 MIN_SHARE_ON_OLD 或源表。")

        if RENORMALIZE_WEIGHTS:
            s = w.groupby("PAC")["share_on_old"].transform("sum")
            w = w[s > 0].copy()
            w["w"] = w["share_on_old"] / s
        else:
            w["w"] = w["share_on_old"]

        alloc = df_long.merge(w[["PAC", "county_code", "w"]], on="PAC", how="inner")
        alloc["cf_count"] = alloc["cf_count_raw"] * alloc["w"]

        df_cf = alloc.groupby(["county_code", "year"], as_index=False).agg(
            cf_count=("cf_count", "sum")
        )
    else:
        df_cf = df_long.dropna(subset=["new_code"]).copy()
        df_cf = df_cf.rename(columns={"new_code": "county_code"})
        df_cf = df_cf.groupby(["county_code", "year"], as_index=False).agg(
            cf_count=("cf_count_raw", "sum")
        )

    df_cf["cf_any"] = (df_cf["cf_count"] > ANY_THRESH).astype(int)
    return df_cf[["county_code", "year", "cf_count", "cf_any"]].copy()


# =========================
# Original notebook comment normalized for the public code archive.
# =========================
def main():
    print("[INFO] Notebook progress message.")
    df_cama = load_cama_any()
    print(f"[INFO] CaMa rows={df_cama.shape}")

    print("[INFO] Notebook progress message.")
    df_dfo = load_dfo_any()
    print(f"[INFO] DFO rows={df_dfo.shape}")

    print("[INFO] Notebook progress message.")
    df_cf = load_country_flood_any()
    print(f"[INFO] country_flood rows={df_cf.shape}")

    # External flood dataset comparison note.
    df = df_cf.merge(df_cama, on=["county_code", "year"], how="left")
    df = df.merge(df_dfo, on=["county_code", "year"], how="left")

    # Original notebook comment normalized for the public code archive.
    n_miss_cama = df["cama_any"].isna().sum()
    n_miss_dfo = df["dfo_any"].isna().sum()
    print("[INFO] Notebook progress message.")

    # External flood dataset comparison note.
    df_cmp = df[(df["cf_any"] == 1) & df["cama_any"].notna() & df["dfo_any"].notna()].copy()
    df_cmp["cama_any"] = df_cmp["cama_any"].astype(int)
    df_cmp["dfo_any"] = df_cmp["dfo_any"].astype(int)

    # Original notebook comment normalized for the public code archive.
    # External flood dataset comparison note.
    df_cmp["only_cama_in_cf"] = ((df_cmp["dfo_any"] == 0) & (df_cmp["cama_any"] == 1)).astype(int)
    df_cmp["neither_in_cf"] = ((df_cmp["dfo_any"] == 0) & (df_cmp["cama_any"] == 0)).astype(int)
    df_cmp["dfo_hit_in_cf"] = (df_cmp["dfo_any"] == 1).astype(int)
    df_cmp["cama_hit_in_cf"] = (df_cmp["cama_any"] == 1).astype(int)
    df_cmp["both_hit_in_cf"] = ((df_cmp["dfo_any"] == 1) & (df_cmp["cama_any"] == 1)).astype(int)

    # Original notebook comment normalized for the public code archive.
    N_cf = df_cmp.shape[0]
    N_add = int(df_cmp["only_cama_in_cf"].sum())        # Original notebook comment normalized for the public code archive.
    N_neither = int(df_cmp["neither_in_cf"].sum())
    add_rate = N_add / (N_add + N_neither) if (N_add + N_neither) > 0 else np.nan

    dfo_recall = df_cmp["dfo_hit_in_cf"].mean()         # P(DFO=1 | CF=1)
    cama_recall = df_cmp["cama_hit_in_cf"].mean()       # P(CaMa=1 | CF=1)
    union_recall = ((df_cmp["dfo_any"] == 1) | (df_cmp["cama_any"] == 1)).mean()

    overall_txt = os.path.join(OUT_BASE, "tri_summary_overall.txt")
    with open(overall_txt, "w", encoding="utf-8") as f:
        f.write("=== 三方对照总体统计（以 country_flood=1 为基准）===\n")
        f.write(f"可比样本数（县×年，CF=1 且 CaMa/DFO 非缺失）: {N_cf}\n\n")
        f.write("[核心] CaMa 补上 DFO 漏检（CF=1, DFO=0, CaMa=1）\n")
        f.write(f"新增捕获数量 N_add: {N_add}\n")
        f.write(f"在 DFO=0 的 CF 洪水里，CaMa=1 的比例 add_rate = P(CaMa=1 | CF=1, DFO=0): {add_rate:.4f}\n\n")
        f.write("[参考] 在 CF=1 的全集上：\n")
        f.write(f"DFO 召回 P(DFO=1 | CF=1): {dfo_recall:.4f}\n")
        f.write(f"CaMa 召回 P(CaMa=1 | CF=1): {cama_recall:.4f}\n")
        f.write(f"并集召回 P(DFO=1 or CaMa=1 | CF=1): {union_recall:.4f}\n")
        f.write("\n")
        f.write(f"merge 缺失：cama_any NA={n_miss_cama}, dfo_any NA={n_miss_dfo}\n")
    print("[INFO] Notebook progress message.")

    # External flood dataset comparison note.
    panel_csv = os.path.join(OUT_BASE, "tri_panel_cf_dfo_cama_2000_2020.csv")
    df_out = df.copy()
    df_out.to_csv(panel_csv, index=False)
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    county = df_cmp.groupby("county_code", as_index=False).agg(
        N_cf=("cf_any", "size"),
        N_add=("only_cama_in_cf", "sum"),
        N_neither=("neither_in_cf", "sum"),
        N_dfo_hit=("dfo_hit_in_cf", "sum"),
        N_cama_hit=("cama_hit_in_cf", "sum"),
        N_both=("both_hit_in_cf", "sum"),
    )
    county["add_rate"] = county["N_add"] / (county["N_add"] + county["N_neither"])
    county.loc[(county["N_add"] + county["N_neither"]) == 0, "add_rate"] = np.nan

    county_csv = os.path.join(OUT_BASE, "tri_county_summary.csv")
    county.to_csv(county_csv, index=False)
    print("[INFO] Notebook progress message.")

    # =============================================================================
    gdf = gpd.read_file(COUNTY_SHP)
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)
    else:
        gdf = gdf.to_crs(epsg=4326)
    gdf["county_code"] = gdf[COUNTY_ID_FIELD].apply(norm_code)

    gdf2 = gdf.merge(county, on="county_code", how="inner")

    # External flood dataset comparison note.
    fig, ax = plt.subplots(1, 1, figsize=(8, 7))
    gdf2.plot(column="N_add", cmap="viridis", legend=True,
              missing_kwds={"color": "lightgrey"},
              edgecolor="black", linewidth=0.2, ax=ax)
    ax.set_title("县级：CaMa补上DFO漏检的次数\n(以 country_flood=1 为基准，统计 CF=1 & DFO=0 & CaMa=1)", fontsize=11)
    ax.set_axis_off()
    fig.tight_layout()
    out_png1 = os.path.join(OUT_BASE, "map_additional_hits_count.png")
    fig.savefig(out_png1, dpi=300)
    plt.close(fig)
    print("[INFO] Notebook progress message.")

    # 2) add_rate：P(CaMa=1 | CF=1, DFO=0)
    fig, ax = plt.subplots(1, 1, figsize=(8, 7))
    gdf2.plot(column="add_rate", cmap="viridis", legend=True, vmin=0, vmax=1,
              missing_kwds={"color": "lightgrey"},
              edgecolor="black", linewidth=0.2, ax=ax)
    ax.set_title("县级：CaMa补充命中率\nP(CaMa=1 | country_flood=1, DFO=0)", fontsize=11)
    ax.set_axis_off()
    fig.tight_layout()
    out_png2 = os.path.join(OUT_BASE, "map_additional_hit_rate.png")
    fig.savefig(out_png2, dpi=300)
    plt.close(fig)
    print("[INFO] Notebook progress message.")

    # =============================================================================
    df_y = df_cmp[df_cmp["year"] == YEAR_EXAMPLE][["county_code", "only_cama_in_cf"]].copy()
    if df_y.empty:
        print("[INFO] Notebook progress message.")
    else:
        gdfy = gdf.merge(df_y, on="county_code", how="left")
        # CaMa-Flood processing note.
        gdfy["plot_val"] = gdfy["only_cama_in_cf"].fillna(0).astype(int)

        fig, ax = plt.subplots(1, 1, figsize=(8, 7))
        gdfy.plot(column="plot_val", cmap="viridis", legend=True,
                  edgecolor="black", linewidth=0.2, ax=ax)
        ax.set_title(f"{YEAR_EXAMPLE} 年：仅 CaMa 抓到（CF=1, DFO=0, CaMa=1）\n(以 country_flood=1 为基准)", fontsize=11)
        ax.set_axis_off()
        fig.tight_layout()
        out_png3 = os.path.join(OUT_BASE, "map_year_example_only_cama.png")
        fig.savefig(out_png3, dpi=300)
        plt.close(fig)
        print("[INFO] Notebook progress message.")

    # External flood dataset comparison note.
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 17
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 02_county_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# =============================================================================
BASE_DIR = "/home/ll/jupyter_notebook/result/windows/country_flood/tri_compare"
PANEL_CSV = os.path.join(BASE_DIR, "tri_panel_cf_dfo_cama_2000_2020.csv")
COUNTY_CSV = os.path.join(BASE_DIR, "tri_county_summary.csv")

# =============================================================================
YEAR_MIN, YEAR_MAX = 2000, 2020

# Original notebook comment normalized for the public code archive.
MIN_DENOM_COUNTY = 5  # Original notebook comment normalized for the public code archive.

# =============================================================================
def read_panel():
    if not os.path.exists(PANEL_CSV):
        raise FileNotFoundError(PANEL_CSV)

    df = pd.read_csv(PANEL_CSV)

    # Original notebook comment normalized for the public code archive.
    need = ["county_code", "year", "cf_any", "cama_any", "dfo_any"]
    miss = [c for c in need if c not in df.columns]
    if miss:
        raise RuntimeError(f"tri_panel 缺少列: {miss}；现有列: {list(df.columns)}")

    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype(int)
    df["cf_any"] = pd.to_numeric(df["cf_any"], errors="coerce")
    df["cama_any"] = pd.to_numeric(df["cama_any"], errors="coerce")
    df["dfo_any"] = pd.to_numeric(df["dfo_any"], errors="coerce")

    df = df[(df["year"] >= YEAR_MIN) & (df["year"] <= YEAR_MAX)].copy()
    return df


def read_county():
    if not os.path.exists(COUNTY_CSV):
        raise FileNotFoundError(COUNTY_CSV)
    df = pd.read_csv(COUNTY_CSV)

    need = ["county_code", "N_add", "N_neither", "add_rate"]
    miss = [c for c in need if c not in df.columns]
    if miss:
        raise RuntimeError(f"tri_county_summary 缺少列: {miss}；现有列: {list(df.columns)}")

    for c in ["N_add", "N_neither"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
    df["add_rate"] = pd.to_numeric(df["add_rate"], errors="coerce")
    df["denom"] = df["N_add"] + df["N_neither"]
    return df


# =============================================================================
def build_metrics(df_panel: pd.DataFrame):
    # Original notebook comment normalized for the public code archive.
    df_cf = df_panel[df_panel["cf_any"] == 1].copy()

    # External flood dataset comparison note.
    cov = df_cf.groupby("year", as_index=False).agg(
        N_cf=("county_code", "size"),
        N_dfo_avail=("dfo_any", lambda x: x.notna().sum()),
        N_cama_avail=("cama_any", lambda x: x.notna().sum()),
    )
    cov["share_dfo_avail"] = cov["N_dfo_avail"] / cov["N_cf"]

    # External flood dataset comparison note.
    df_cmp = df_cf[df_cf["cama_any"].notna() & df_cf["dfo_any"].notna()].copy()
    df_cmp["cama_any"] = df_cmp["cama_any"].astype(int)
    df_cmp["dfo_any"] = df_cmp["dfo_any"].astype(int)

    # External flood dataset comparison note.
    df_cmp["dfo0"] = (df_cmp["dfo_any"] == 0).astype(int)
    df_cmp["add"] = ((df_cmp["dfo_any"] == 0) & (df_cmp["cama_any"] == 1)).astype(int)
    df_cmp["dfo_hit"] = (df_cmp["dfo_any"] == 1).astype(int)
    df_cmp["cama_hit"] = (df_cmp["cama_any"] == 1).astype(int)
    df_cmp["union_hit"] = ((df_cmp["dfo_any"] == 1) | (df_cmp["cama_any"] == 1)).astype(int)

    # Original notebook comment normalized for the public code archive.
    y = df_cmp.groupby("year", as_index=False).agg(
        N_cf=("county_code", "size"),         # Original notebook comment normalized for the public code archive.
        N_dfo0=("dfo0", "sum"),               # External flood dataset comparison note.
        N_add=("add", "sum"),                 # External flood dataset comparison note.
        dfo_recall=("dfo_hit", "mean"),       # P(DFO=1 | CF=1)
        cama_recall=("cama_hit", "mean"),     # P(CaMa=1 | CF=1)
        union_recall=("union_hit", "mean"),   # P(DFO=1 or CaMa=1 | CF=1)
    )
    y["add_rate"] = y["N_add"] / y["N_dfo0"]
    y.loc[y["N_dfo0"] == 0, "add_rate"] = np.nan

    # Original notebook comment normalized for the public code archive.
    N_cf_total = df_cmp.shape[0]
    N_dfo0_total = int(df_cmp["dfo0"].sum())
    N_add_total = int(df_cmp["add"].sum())
    add_rate_total = N_add_total / N_dfo0_total if N_dfo0_total > 0 else np.nan
    dfo_recall_total = df_cmp["dfo_hit"].mean()
    cama_recall_total = df_cmp["cama_hit"].mean()
    union_recall_total = df_cmp["union_hit"].mean()

    overall = {
        "N_cf_total": N_cf_total,
        "N_dfo0_total": N_dfo0_total,
        "N_add_total": N_add_total,
        "add_rate": add_rate_total,
        "dfo_recall": dfo_recall_total,
        "cama_recall": cama_recall_total,
        "union_recall": union_recall_total,
    }

    return cov, y, overall


# =============================================================================
def save_fig(fig, fname):
    out = os.path.join(BASE_DIR, fname)
    fig.savefig(out, dpi=300)
    plt.close(fig)
    print(f"[SAVE] {out}")


def plot_overall_rates(overall):
    labels = ["DFO recall", "CaMa recall", "Union recall", "Add rate\nP(CaMa=1|CF=1,DFO=0)"]
    values = [overall["dfo_recall"], overall["cama_recall"], overall["union_recall"], overall["add_rate"]]

    fig, ax = plt.subplots(1, 1, figsize=(7.5, 4))
    x = np.arange(len(labels))
    ax.bar(x, values)  # Original notebook comment normalized for the public code archive.
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=0)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Rate")
    ax.set_title("Overall metrics (base: country_flood=1)", fontsize=11)

    # Original notebook comment normalized for the public code archive.
    for i, v in enumerate(values):
        if pd.notna(v):
            ax.text(i, min(0.98, v + 0.02), f"{v:.3f}", ha="center", va="bottom", fontsize=9)

    fig.tight_layout()
    save_fig(fig, "viz_overall_rates.png")


def plot_yearly_coverage(cov):
    fig, ax1 = plt.subplots(1, 1, figsize=(8, 4))

    # Original notebook comment normalized for the public code archive.
    ax1.plot(cov["year"], cov["N_cf"], marker="o")
    ax1.set_xlabel("Year")
    ax1.set_ylabel("N (CF=1 county-year)")
    ax1.set_title("Yearly coverage: CF sample size and DFO availability", fontsize=11)

    # External flood dataset comparison note.
    ax2 = ax1.twinx()
    ax2.plot(cov["year"], cov["share_dfo_avail"], marker="o")
    ax2.set_ylabel("Share of CF with DFO available")
    ax2.set_ylim(0, 1.0)

    fig.tight_layout()
    save_fig(fig, "viz_yearly_coverage.png")


def plot_yearly_counts(y):
    fig, ax = plt.subplots(1, 1, figsize=(8, 4))
    ax.plot(y["year"], y["N_cf"], marker="o", label="N_cf (comparable)")
    ax.plot(y["year"], y["N_dfo0"], marker="o", label="N_dfo0 (CF=1 & DFO=0)")
    ax.plot(y["year"], y["N_add"], marker="o", label="N_add (CF=1 & DFO=0 & CaMa=1)")
    ax.set_xlabel("Year")
    ax.set_ylabel("Count")
    ax.set_title("Yearly counts (base: country_flood=1)", fontsize=11)
    ax.legend(fontsize=8, frameon=True, loc="best")
    fig.tight_layout()
    save_fig(fig, "viz_yearly_counts.png")


def plot_yearly_rates(y):
    fig, ax = plt.subplots(1, 1, figsize=(8, 4))
    ax.plot(y["year"], y["dfo_recall"], marker="o", label="DFO recall")
    ax.plot(y["year"], y["cama_recall"], marker="o", label="CaMa recall")
    ax.plot(y["year"], y["union_recall"], marker="o", label="Union recall")
    ax.plot(y["year"], y["add_rate"], marker="o", label="Add rate (CaMa|DFO=0)")
    ax.set_xlabel("Year")
    ax.set_ylabel("Rate")
    ax.set_ylim(0, 1.0)
    ax.set_title("Yearly rates (base: country_flood=1)", fontsize=11)
    ax.legend(fontsize=8, frameon=True, loc="best")
    fig.tight_layout()
    save_fig(fig, "viz_yearly_rates.png")


def plot_county_distributions(df_county):
    # Original notebook comment normalized for the public code archive.
    df_use = df_county[df_county["denom"] >= MIN_DENOM_COUNTY].copy()
    data_rate = df_use["add_rate"].dropna().values

    fig, ax = plt.subplots(1, 1, figsize=(7, 4))
    ax.hist(data_rate, bins=20)
    ax.set_xlim(0, 1.0)
    ax.set_xlabel("Add rate  P(CaMa=1 | CF=1, DFO=0)")
    ax.set_ylabel("Number of counties")
    ax.set_title(f"County distribution of add_rate (denom >= {MIN_DENOM_COUNTY})", fontsize=11)
    fig.tight_layout()
    save_fig(fig, "viz_county_add_rate_hist.png")

    # Original notebook comment normalized for the public code archive.
    data_add = pd.to_numeric(df_county["N_add"], errors="coerce").fillna(0).values
    fig, ax = plt.subplots(1, 1, figsize=(7, 4))
    ax.hist(data_add, bins=30)
    ax.set_xlabel("N_add (CF=1 & DFO=0 & CaMa=1) per county")
    ax.set_ylabel("Number of counties")
    ax.set_title("County distribution of N_add", fontsize=11)
    fig.tight_layout()
    save_fig(fig, "viz_county_add_count_hist.png")


def main():
    df_panel = read_panel()
    df_county = read_county()

    cov, y, overall = build_metrics(df_panel)

    # Original notebook comment normalized for the public code archive.
    out_year_csv = os.path.join(BASE_DIR, "yearly_metrics.csv")
    y.to_csv(out_year_csv, index=False)
    print(f"[SAVE] {out_year_csv}")

    # Original notebook comment normalized for the public code archive.
    plot_overall_rates(overall)
    plot_yearly_coverage(cov)
    plot_yearly_counts(y)
    plot_yearly_rates(y)
    plot_county_distributions(df_county)

    print("[INFO] Notebook progress message.", BASE_DIR)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 18
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =============================================================================
CSV_PATH = "/home/ll/jupyter_notebook/result/windows/country_flood/tri_compare/tri_county_summary.csv"
OUT_PNG  = "/home/ll/jupyter_notebook/result/windows/country_flood/tri_compare/hist_add_rate.png"

# =============================================================================
COL_RATE = "add_rate"
MIN_DENOM = 5       # Original notebook comment normalized for the public code archive.
BINS = 20
XRANGE = (0.0, 1.0)

def main():
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"未找到: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)

    need = ["N_add", "N_neither", COL_RATE]
    miss = [c for c in need if c not in df.columns]
    if miss:
        raise RuntimeError(f"缺少列 {miss}，现有列: {list(df.columns)}")

    df["N_add"] = pd.to_numeric(df["N_add"], errors="coerce").fillna(0).astype(int)
    df["N_neither"] = pd.to_numeric(df["N_neither"], errors="coerce").fillna(0).astype(int)
    df[COL_RATE] = pd.to_numeric(df[COL_RATE], errors="coerce")

    df["denom"] = df["N_add"] + df["N_neither"]
    df_use = df[df["denom"] >= MIN_DENOM].copy()

    data = df_use[COL_RATE].dropna().values
    if data.size == 0:
        raise RuntimeError("过滤后无有效 add_rate 数据，请降低 MIN_DENOM 或检查 CSV。")

    mean_v = float(np.mean(data))
    median_v = float(np.median(data))

    print(f"[INFO] counties used: {data.size} (denom >= {MIN_DENOM})")
    print(f"[INFO] add_rate mean: {mean_v:.4f}, median: {median_v:.4f}")

    # =============================================================================
    fig, ax = plt.subplots(1, 1, figsize=(7, 4))
    ax.hist(data, bins=BINS)

    ax.axvline(mean_v, linestyle="--", linewidth=1.5, label=f"Mean = {mean_v:.2f}")
    ax.axvline(median_v, linestyle="--", linewidth=1.5, label=f"Median = {median_v:.2f}")

    ax.set_xlim(*XRANGE)
    ax.set_xlabel("Add rate  P(CaMa=1 | country_flood=1, DFO=0)")
    ax.set_ylabel("Number of counties")
    ax.set_title(f"Supplementary hit rate distribution (denom >= {MIN_DENOM})", fontsize=11)
    ax.legend(fontsize=9, frameon=True, loc="upper right")

    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=300)
    plt.close(fig)

    print(f"[SAVE] {OUT_PNG}")

if __name__ == "__main__":
    main()
