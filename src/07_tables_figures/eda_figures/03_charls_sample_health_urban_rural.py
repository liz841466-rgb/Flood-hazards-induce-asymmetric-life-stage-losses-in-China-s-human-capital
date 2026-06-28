#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 03_charls_sample_health_urban_rural.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 1
# ------------------------------------------------------------------------------

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EDA: Urban/rural wave sample size (stacked) + cumulative unique sample (dual y-axis).

Data:
    charls_health_panel_60plus_with_index_Tall_5_10_20_30y.parquet
"""

from pathlib import Path
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt


# =========================
# Global plotting style
# =========================

mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams["figure.dpi"] = 300

# ---------------- basic global style (no font forced) ----------------
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams["figure.dpi"] = 300
# Original notebook comment normalized for the public code archive.
mpl.rcParams.update({
     "font.family": "Times New Roman",
#     "axes.labelsize": 18,
     "xtick.labelsize": 12,
     "ytick.labelsize": 12,
 })
# =========================
# Paths and basic config
# =========================

PANEL_MERGED = (
    Path(r"E:\impact_assessment_child_order\data\supplement\EDA")
    / "charls_health_panel_60plus_with_index_Tall_5_10_20_30y.parquet"
)

ID_COL = "pid12"
YEAR_COL = "year"
URBAN_NBS_COL = "urban_nbs"

URBAN_THRESHOLD = 0.5  # consistent with main regression specification

SAVE_FIG = True
OUT_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\EDA\figure")
FIG_NAME = "wave_stacked_with_cum_urban_rural.png"


# =========================
# Urban/rural grouping
# =========================

def add_urban_group(
    df: pd.DataFrame,
    id_col: str = ID_COL,
    urban_nbs_col: str = URBAN_NBS_COL,
    threshold: float = URBAN_THRESHOLD,
) -> pd.DataFrame:
    """
    Define an urban group indicator at the individual level:

        urban_group = 1 if mean(urban_nbs) > threshold, else 0.
    """
    if urban_nbs_col not in df.columns:
        raise KeyError(f"Column '{urban_nbs_col}' not found.")

    out = df.copy()
    out[urban_nbs_col] = pd.to_numeric(
        out[urban_nbs_col], errors="coerce"
    ).fillna(0)

    grp_urban = out.groupby(id_col)[urban_nbs_col].mean()
    urban_group = (grp_urban > threshold).astype(int).rename("urban_group")

    out = out.merge(urban_group, on=id_col, how="left")
    return out


# =========================
# Summary construction
# =========================

def build_stacked_wave_and_cum_summary(
    df: pd.DataFrame,
    id_col: str = ID_COL,
    year_col: str = YEAR_COL,
    urban_group_col: str = "urban_group",
) -> pd.DataFrame:
    """
    Build a summary table for plotting:

        columns:
            year
            wave_rural_unique
            wave_urban_unique
            wave_total_unique
            cum_rural_unique
            cum_urban_unique
            cum_total_unique
    """
    needed = [id_col, year_col, urban_group_col]
    tmp = df[needed].dropna().copy()

    tmp[year_col] = pd.to_numeric(tmp[year_col], errors="coerce")
    tmp = tmp.dropna(subset=[year_col])
    tmp[year_col] = tmp[year_col].astype(int)

    years = sorted(tmp[year_col].unique())

    # Wave unique counts by year and group
    wave_counts = (
        tmp.groupby([year_col, urban_group_col])[id_col]
        .nunique()
        .unstack(urban_group_col)
        .reindex(years)
        .fillna(0)
        .astype(int)
    )

    # Ensure both 0 (rural) and 1 (urban) columns exist
    if 0 not in wave_counts.columns:
        wave_counts[0] = 0
    if 1 not in wave_counts.columns:
        wave_counts[1] = 0

    # Order as rural(0), urban(1)
    wave_counts = wave_counts[[0, 1]]

    wave_rural = wave_counts[0].values
    wave_urban = wave_counts[1].values

    # Cumulative unique counts: use first year per pid and fixed group
    pid_first = (
        tmp.groupby(id_col)
        .agg(first_year=(year_col, "min"), group=(urban_group_col, "first"))
    )

    first_urban = pid_first[pid_first["group"] == 1]["first_year"]
    first_rural = pid_first[pid_first["group"] == 0]["first_year"]

    cum_urban = [int((first_urban <= y).sum()) for y in years]
    cum_rural = [int((first_rural <= y).sum()) for y in years]
    cum_total = [int((pid_first["first_year"] <= y).sum()) for y in years]

    out = pd.DataFrame(
        {
            "year": years,
            "wave_rural_unique": wave_rural,
            "wave_urban_unique": wave_urban,
            "wave_total_unique": wave_rural + wave_urban,
            "cum_rural_unique": cum_rural,
            "cum_urban_unique": cum_urban,
            "cum_total_unique": cum_total,
        }
    )

    return out


# =========================
# Plotting: stacked bars + dual cumulative lines
# =========================

def plot_stacked_wave_with_cum_lines(
    summary_df: pd.DataFrame,
    title: str = "Urban vs rural: wave sample size (stacked) and cumulative unique sample",
    save_fig: bool = SAVE_FIG,
    out_dir: Path = OUT_DIR,
    fig_name: str = FIG_NAME,
):
    years = summary_df["year"].tolist()  # [2011, 2013, 2015, 2018, 2020]
    x_pos = list(range(len(years)))      # equal spacing

    wave_rural = summary_df["wave_rural_unique"].tolist()
    wave_urban = summary_df["wave_urban_unique"].tolist()
    cum_rural = summary_df["cum_rural_unique"].tolist()
    cum_urban = summary_df["cum_urban_unique"].tolist()
    total_wave = summary_df["wave_total_unique"].tolist()

    fig, ax1 = plt.subplots(figsize=(7.5, 4.2))

    bar_width = 0.45  # narrower bars

    # Stacked bars with specified colors
    ax1.bar(
        x_pos,
        wave_rural,
        width=bar_width,
        label="Rural wave unique",
        color="#80cdc1",
    )
    ax1.bar(
        x_pos,
        wave_urban,
        width=bar_width,
        bottom=wave_rural,
        label="Urban wave unique",
        color="#dfc27d",
    )

    ax1.set_xlabel("Year")
    ax1.set_ylabel("Wave unique individuals", fontsize=12, fontfamily="Times New Roman")

    # X ticks
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels([str(y) for y in years])

    # Right axis for cumulative unique counts
    ax2 = ax1.twinx()
    ax2.plot(
        x_pos,
        cum_rural,
        marker="o",
        label="Rural cumulative unique",
        color="#018571",
    )
    ax2.plot(
        x_pos,
        cum_urban,
        marker="o",
        label="Urban cumulative unique",
        color="#a6611a",
    )
    ax2.set_ylabel("Cumulative unique individuals", fontsize=12, fontfamily="Times New Roman")

    # ----- y-axis limit + label offset -----
    max_wave = max(total_wave) if total_wave else 0
    ax1.set_ylim(0, 13300)                    # Original notebook comment normalized for the public code archive.
    label_offset = 0.02 * max_wave if max_wave > 0 else 0  # Original notebook comment normalized for the public code archive.

    # Label total wave unique counts on top of bars (higher)
    for x, total in zip(x_pos, total_wave):
        ax1.text(
            x,
            total + label_offset,              # Original notebook comment normalized for the public code archive.
            f"{total:,}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    # Merge legends from both axes; keep inside the axes (no frame)
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(
        h1 + h2,
        l1 + l2,
        loc="upper left",
        #bbox_to_anchor=(0.02, 0.98),
        bbox_to_anchor=(0.02, 0.99),# Original notebook comment normalized for the public code archive.
        frameon=False,
    )

    #ax1.set_title(title)

    plt.tight_layout()

    if save_fig:
        out_dir.mkdir(parents=True, exist_ok=True)
        save_path = out_dir / fig_name
        plt.savefig(save_path, dpi=300)
        print(f"[SAVE] Figure saved: {save_path}")

    plt.show()
    plt.close(fig)


# =========================
# main
# =========================

def main():
    print(f"[READ] {PANEL_MERGED}")
    df = pd.read_parquet(PANEL_MERGED)

    df = add_urban_group(df)
    summary = build_stacked_wave_and_cum_summary(df)

    print("\n[SUMMARY TABLE] Urban/rural wave and cumulative unique samples:")
    print(summary)

    plot_stacked_wave_with_cum_lines(
        summary,
        title="Urban vs rural: wave sample size (stacked) and cumulative unique sample",
        save_fig=SAVE_FIG,
    )


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 5
# ------------------------------------------------------------------------------
# Notebook-export prose note omitted from the public code archive.


# ------------------------------------------------------------------------------
# Notebook cell 6
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EDA: Wave distribution of health_index_raw by year and urban/rural group
(grouped boxplots: All / Rural / Urban for each year).

Data:
  charls_health_panel_60plus_with_index_Tall_5_10_20_30y.parquet

Groups:
  - All sample
  - Rural (urban_group = 0)
  - Urban (urban_group = 1)
"""

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


# =========================
# Config
# =========================

PANEL_MERGED = (
    Path(r"E:\impact_assessment_child_order\data\supplement\EDA")
    / "charls_health_panel_60plus_with_index_Tall_5_10_20_30y.parquet"
)

ID_COL = "pid12"
YEAR_COL = "year"
URBAN_NBS_COL = "urban_nbs"
Y_VAR = "health_index_raw"
URBAN_THRESHOLD = 0.5


# =========================
# Urban / rural grouping
# =========================

def add_urban_group(
    df: pd.DataFrame,
    id_col: str = ID_COL,
    urban_nbs_col: str = URBAN_NBS_COL,
    threshold: float = URBAN_THRESHOLD,
) -> pd.DataFrame:
    """Define urban_group at the individual level."""
    if urban_nbs_col not in df.columns:
        raise KeyError(f"Column '{urban_nbs_col}' not found.")

    out = df.copy()
    out[urban_nbs_col] = pd.to_numeric(out[urban_nbs_col], errors="coerce").fillna(0)

    grp = out.groupby(id_col)[urban_nbs_col].mean()
    urban_group = (grp > threshold).astype(int).rename("urban_group")

    out = out.merge(urban_group, on=id_col, how="left")
    return out


# =========================
# Grouped boxplots: all / rural / urban
# =========================

def plot_all_rural_urban_by_year_box(
    df: pd.DataFrame,
    y_col: str = Y_VAR,
    year_col: str = YEAR_COL,
    group_col: str = "urban_group",
):
    tmp = df[[y_col, year_col, group_col]].copy()
    tmp[y_col] = pd.to_numeric(tmp[y_col], errors="coerce")
    tmp[year_col] = pd.to_numeric(tmp[year_col], errors="coerce")
    tmp = tmp.dropna(subset=[y_col, year_col, group_col]).copy()
    tmp[year_col] = tmp[year_col].astype(int)

    years = sorted(tmp[year_col].unique())
    x = np.arange(len(years))

    # data for each group
    data_all = [tmp.loc[tmp[year_col] == y, y_col].values for y in years]
    data_rural = [
        tmp.loc[(tmp[year_col] == y) & (tmp[group_col] == 0), y_col].values
        for y in years
    ]
    data_urban = [
        tmp.loc[(tmp[year_col] == y) & (tmp[group_col] == 1), y_col].values
        for y in years
    ]

    fig, ax = plt.subplots(figsize=(9, 4.6))

    # narrow boxes
    width = 0.18

    # positions: All (left), Rural (center), Urban (right)
    pos_all = x - width
    pos_rural = x
    pos_urban = x + width

    # colors
    color_all = "#bdbdbd"
    color_rural = "#80cdc1"
    color_urban = "#dfc27d"

    # All
    bp_all = ax.boxplot(
        data_all,
        positions=pos_all,
        widths=width,
        patch_artist=True,
        showfliers=True,
    )
    for patch in bp_all["boxes"]:
        patch.set_facecolor(color_all)

    # Rural
    bp_rural = ax.boxplot(
        data_rural,
        positions=pos_rural,
        widths=width,
        patch_artist=True,
        showfliers=True,
    )
    for patch in bp_rural["boxes"]:
        patch.set_facecolor(color_rural)

    # Urban
    bp_urban = ax.boxplot(
        data_urban,
        positions=pos_urban,
        widths=width,
        patch_artist=True,
        showfliers=True,
    )
    for patch in bp_urban["boxes"]:
        patch.set_facecolor(color_urban)

    ax.set_xticks(x)
    ax.set_xticklabels(years)
    ax.set_xlabel("Year")
    ax.set_ylabel(y_col)

    # legend using dummy handles
    handles = [
        Line2D([0], [0], color=color_all, lw=6, label="All"),
        Line2D([0], [0], color=color_rural, lw=6, label="Rural"),
        Line2D([0], [0], color=color_urban, lw=6, label="Urban"),
    ]
    ax.legend(handles=handles, loc="upper left", frameon=False)

    plt.tight_layout()
    plt.show()

    # optional: print sample sizes for reference
    n_table = (
        tmp.groupby([year_col, group_col])[y_col]
        .count()
        .unstack(group_col)
        .rename(columns={0: "rural_n", 1: "urban_n"})
        .reindex(years)
        .fillna(0)
        .astype(int)
    )
    n_table["all_n"] = n_table["rural_n"] + n_table["urban_n"]
    print("\n[INFO] N by year and group (all / rural / urban):")
    print(n_table[["all_n", "rural_n", "urban_n"]])


# =========================
# main
# =========================

def main():
    print(f"[READ] {PANEL_MERGED}")
    df = pd.read_parquet(PANEL_MERGED)

    if Y_VAR not in df.columns:
        raise KeyError(f"{Y_VAR} not found in the data.")

    df = add_urban_group(df)

    # single figure: All + Rural + Urban
    plot_all_rural_urban_by_year_box(df)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 8
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 03_charls_sample_health_urban_rural.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# ---------------- basic global style (no font forced) ----------------
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams["figure.dpi"] = 300
# Original notebook comment normalized for the public code archive.
mpl.rcParams.update({
     "font.family": "Times New Roman",
#     "axes.labelsize": 18,
     "xtick.labelsize": 12,
     "ytick.labelsize": 12,
 })

# ---------------- paths & config ----------------
BASE_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\EDA")
PANEL_MERGED = BASE_DIR / "charls_health_panel_60plus_with_index_Tall_5_10_20_30y.parquet"

OUT_DIR = BASE_DIR / "figure"
OUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_NAME = "health_index_raw_mirror_hist_rural_urban.png"

ID_COL = "pid12"
YEAR_COL = "year"
URBAN_NBS_COL = "urban_nbs"
Y_VAR = "health_index_raw"
URBAN_THRESHOLD = 0.5

N_BINS = 20  # number of bins for health_index_raw


# --------------- helper: add urban_group ---------------

def add_urban_group(
    df: pd.DataFrame,
    id_col: str = ID_COL,
    urban_nbs_col: str = URBAN_NBS_COL,
    threshold: float = URBAN_THRESHOLD,
) -> pd.DataFrame:
    """Define urban_group = 1 (urban) or 0 (rural) by mean urban_nbs per pid."""
    if urban_nbs_col not in df.columns:
        raise KeyError(f"Column '{urban_nbs_col}' not found.")

    out = df.copy()
    out[urban_nbs_col] = pd.to_numeric(out[urban_nbs_col], errors="coerce").fillna(0)

    grp = out.groupby(id_col)[urban_nbs_col].mean()
    urban_group = (grp > threshold).astype(int).rename("urban_group")

    out = out.merge(urban_group, on=id_col, how="left")
    return out


# --------------- plotting function ---------------

def plot_mirror_histogram(
    df: pd.DataFrame,
    save_dir: Path = OUT_DIR,
    fig_name: str = FIG_NAME,
):
    """
    Mirror histogram:
      left side: rural (urban_group = 0)
      right side: urban (urban_group = 1)
    """
    tmp = df[[Y_VAR, "urban_group"]].copy()
    tmp[Y_VAR] = pd.to_numeric(tmp[Y_VAR], errors="coerce")
    tmp = tmp.dropna(subset=[Y_VAR, "urban_group"])

    # health values
    rural_vals = tmp.loc[tmp["urban_group"] == 0, Y_VAR].values
    urban_vals = tmp.loc[tmp["urban_group"] == 1, Y_VAR].values

    # restrict to [0,1]
    rural_vals = rural_vals[(rural_vals >= 0) & (rural_vals <= 1)]
    urban_vals = urban_vals[(urban_vals >= 0) & (urban_vals <= 1)]

    # common bins on [0,1]
    bins = np.linspace(0.0, 1.0, N_BINS + 1)
    centers = 0.5 * (bins[:-1] + bins[1:])
    bin_width = bins[1] - bins[0]

    counts_rural, _ = np.histogram(rural_vals, bins=bins)
    counts_urban, _ = np.histogram(urban_vals, bins=bins)

    fig, ax = plt.subplots(figsize=(7.5, 4.2))

    # colors
    color_rural = "#80cdc1"
    color_urban = "#dfc27d"

    # rural bars on the left (x negative), urban on the right (x positive)
    for c, h in zip(counts_rural, centers):
        if c == 0:
            continue
        x_center = -h
        ax.bar(
            x_center,
            c,
            width=bin_width,
            color=color_rural,
            align="center",
            edgecolor="none",
        )

    for c, h in zip(counts_urban, centers):
        if c == 0:
            continue
        x_center = h
        ax.bar(
            x_center,
            c,
            width=bin_width,
            color=color_urban,
            align="center",
            edgecolor="none",
        )

    # symmetric x-limits around 0
    ax.set_xlim(-1.05, 1.05)

    # Original notebook comment normalized for the public code archive.
    ticks_val = np.linspace(0.0, 1.0, 6)  # 0, 0.2, ..., 1.0
    ticks = [-t for t in ticks_val[::-1] if t > 0] + [0.0] + list(ticks_val[1:])
    labels = [f"{t:.1f}" for t in ticks_val[::-1] if t > 0] + ["0.0"] + [
        f"{t:.1f}" for t in ticks_val[1:]
    ]
    ax.set_xticks(ticks)
    ax.set_xticklabels(labels)

    # Original notebook comment normalized for the public code archive.
    ax.set_ylabel("Count", fontsize=12, fontfamily="Times New Roman")              # e.g. fontsize=18, fontfamily="Times New Roman"
    ax.set_xlabel("General health",  fontsize=12, fontfamily="Times New Roman")     # e.g. fontsize=18, fontfamily="Times New Roman"

    # dashed center line
    ax.axvline(0, color="gray", linestyle="--", linewidth=1)

    plt.tight_layout()

    # save
    save_path = save_dir / fig_name
    fig.savefig(save_path, dpi=300)
    print(f"[SAVE] Figure saved: {save_path}")

    plt.close(fig)


# --------------- main ---------------

def main():
    print(f"[READ] {PANEL_MERGED}")
    df = pd.read_parquet(PANEL_MERGED)

    if Y_VAR not in df.columns:
        raise KeyError(f"{Y_VAR} not found in the data.")

    df = add_urban_group(df)

    plot_mirror_histogram(df)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 9
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Boxplots of health_index_raw by wave for Rural and Urban separately
(no outliers shown).

Data:
    E:\impact_assessment_child_order\data\supplement\EDA\
        charls_health_panel_60plus_with_index_Tall_5_10_20_30y.parquet
"""

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt


# ---------------- global style ----------------
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams["figure.dpi"] = 300


# ---------------- paths & config ----------------
PANEL_MERGED = (
    Path(r"E:\impact_assessment_child_order\data\supplement\EDA")
    / "charls_health_panel_60plus_with_index_Tall_5_10_20_30y.parquet"
)

OUT_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\EDA\figure")
OUT_DIR.mkdir(parents=True, exist_ok=True)

ID_COL = "pid12"
YEAR_COL = "year"
URBAN_NBS_COL = "urban_nbs"
Y_VAR = "health_index_raw"
URBAN_THRESHOLD = 0.5

COLOR_RURAL = "#80cdc1"
COLOR_URBAN = "#dfc27d"


# --------------- helper: add urban_group ---------------

def add_urban_group(
    df: pd.DataFrame,
    id_col: str = ID_COL,
    urban_nbs_col: str = URBAN_NBS_COL,
    threshold: float = URBAN_THRESHOLD,
) -> pd.DataFrame:
    """Define urban_group=1 (urban) or 0 (rural) by mean urban_nbs per pid."""
    if urban_nbs_col not in df.columns:
        raise KeyError(f"Column '{urban_nbs_col}' not found.")

    out = df.copy()
    out[urban_nbs_col] = pd.to_numeric(out[urban_nbs_col], errors="coerce").fillna(0)

    grp = out.groupby(id_col)[urban_nbs_col].mean()
    urban_group = (grp > threshold).astype(int).rename("urban_group")

    out = out.merge(urban_group, on=id_col, how="left")
    return out


# --------------- plotting function ---------------

def plot_group_boxplots(
    df: pd.DataFrame,
    group_value: int,
    color: str,
    title_suffix: str,
    save_path: Path,
):
    """
    Draw one boxplot figure for a given group (0 = rural, 1 = urban),
    with health_index_raw on y-axis and waves (years) on x-axis.
    Outliers are not shown.
    """
    sub = df[df["urban_group"] == group_value].copy()
    sub[Y_VAR] = pd.to_numeric(sub[Y_VAR], errors="coerce")
    sub[Y_VAR] = sub[Y_VAR].clip(lower=0, upper=1)
    sub[YEAR_COL] = pd.to_numeric(sub[YEAR_COL], errors="coerce")
    sub = sub.dropna(subset=[Y_VAR, YEAR_COL])
    sub[YEAR_COL] = sub[YEAR_COL].astype(int)

    years = sorted(sub[YEAR_COL].unique())
    data = [sub.loc[sub[YEAR_COL] == y, Y_VAR].values for y in years]

    # slightly narrower figure width so waves look closer
    fig, ax = plt.subplots(figsize=(6.5, 4.0))

    bp = ax.boxplot(
        data,
        labels=[str(y) for y in years],
        showfliers=False,          # no outliers
        patch_artist=True,
        widths=0.5,                # thinner-ish boxes
    )

    for box in bp["boxes"]:
        box.set_facecolor(color)
        box.set_edgecolor("black")
    for element in ["whiskers", "caps", "medians"]:
        plt.setp(bp[element], color="black")

    ax.set_xlabel("Year")
    ax.set_ylabel("General health")
    ax.set_ylim(0.0, 1.0)

    # no title
    # ax.set_title(f"health_index_raw by wave ({title_suffix})")

    plt.tight_layout()

    fig.savefig(save_path, dpi=300)
    print(f"[SAVE] Figure saved: {save_path}")

    plt.close(fig)


# --------------- main ---------------

def main():
    print(f"[READ] {PANEL_MERGED}")
    df = pd.read_parquet(PANEL_MERGED)

    if Y_VAR not in df.columns:
        raise KeyError(f"{Y_VAR} not found in the data.")

    df = add_urban_group(df)

    # Rural (urban_group = 0)
    plot_group_boxplots(
        df,
        group_value=0,
        color=COLOR_RURAL,
        title_suffix="Rural",
        save_path=OUT_DIR / "health_index_raw_box_rural.png",
    )

    # Urban (urban_group = 1)
    plot_group_boxplots(
        df,
        group_value=1,
        color=COLOR_URBAN,
        title_suffix="Urban",
        save_path=OUT_DIR / "health_index_raw_box_urban.png",
    )


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 10
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Boxplots of health_index_raw by wave for Rural and Urban
in a single figure (2 rows × 1 column, no outliers).

Data:
    E:\impact_assessment_child_order\data\supplement\EDA\
        charls_health_panel_60plus_with_index_Tall_5_10_20_30y.parquet
"""

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

# ---------------- global style ----------------
mpl.rcParams.update({
    "font.family": "Times New Roman",
    "axes.unicode_minus": False,
    "figure.dpi": 300,
    "axes.labelsize": 20,   # axis labels
    "axes.titlesize": 0,   # (we do not use titles here, but keep for consistency)
    "xtick.labelsize": 24,  # x tick labels
    "ytick.labelsize": 24,  # y tick labels
    "legend.fontsize": 21,  # legend font
})

# ---------------- paths & config ----------------
PANEL_MERGED = (
    Path(r"E:\impact_assessment_child_order\data\supplement\EDA")
    / "charls_health_panel_60plus_with_index_Tall_5_10_20_30y.parquet"
)

OUT_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\EDA\figure")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FIG = "health_index_raw_box_rural_urban_2x1.png"

ID_COL = "pid12"
YEAR_COL = "year"
URBAN_NBS_COL = "urban_nbs"
Y_VAR = "health_index_raw"
URBAN_THRESHOLD = 0.5

COLOR_RURAL = "#80cdc1"
COLOR_URBAN = "#dfc27d"


# --------------- helper: add urban_group ---------------

def add_urban_group(
    df: pd.DataFrame,
    id_col: str = ID_COL,
    urban_nbs_col: str = URBAN_NBS_COL,
    threshold: float = URBAN_THRESHOLD,
) -> pd.DataFrame:
    """Define urban_group = 1 (urban) or 0 (rural) by mean urban_nbs per pid."""
    if urban_nbs_col not in df.columns:
        raise KeyError(f"Column '{urban_nbs_col}' not found.")

    out = df.copy()
    out[urban_nbs_col] = pd.to_numeric(out[urban_nbs_col], errors="coerce").fillna(0)

    grp = out.groupby(id_col)[urban_nbs_col].mean()
    urban_group = (grp > threshold).astype(int).rename("urban_group")

    out = out.merge(urban_group, on=id_col, how="left")
    return out


# --------------- combined plotting function ---------------

def plot_combined_boxplots(df: pd.DataFrame, save_path: Path):
    """Archived notebook note for 03_charls_sample_health_urban_rural.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df[Y_VAR] = pd.to_numeric(df[Y_VAR], errors="coerce")
    df[Y_VAR] = df[Y_VAR].clip(lower=0, upper=1)
    df[YEAR_COL] = pd.to_numeric(df[YEAR_COL], errors="coerce")
    df = df.dropna(subset=[Y_VAR, YEAR_COL])
    df[YEAR_COL] = df[YEAR_COL].astype(int)

    years = sorted(df[YEAR_COL].unique())

    rural = df[df["urban_group"] == 0].copy()
    urban = df[df["urban_group"] == 1].copy()

    data_rural = [rural.loc[rural[YEAR_COL] == y, Y_VAR].values for y in years]
    data_urban = [urban.loc[urban[YEAR_COL] == y, Y_VAR].values for y in years]

    # match KDE figure size and layout: 2 rows × 1 column, (7, 8)
    fig, axes = plt.subplots(
        2, 1,
        figsize=(7, 8),
        sharex=True,
        sharey=True,
    )

    # ----- top: rural -----
    bp_r = axes[0].boxplot(
        data_rural,
        labels=[str(y) for y in years],
        showfliers=False,
        patch_artist=True,
        widths=0.5,
    )
    for box in bp_r["boxes"]:
        box.set_facecolor(COLOR_RURAL)
        box.set_edgecolor("black")
    for element in ["whiskers", "caps", "medians"]:
        plt.setp(bp_r[element], color="black")

    #axes[0].set_ylabel("General health")
    axes[0].set_ylim(0.0, 1.0)
    # no title

    # ----- bottom: urban -----
    bp_u = axes[1].boxplot(
        data_urban,
        labels=[str(y) for y in years],
        showfliers=False,
        patch_artist=True,
        widths=0.5,
    )
    for box in bp_u["boxes"]:
        box.set_facecolor(COLOR_URBAN)
        box.set_edgecolor("black")
    for element in ["whiskers", "caps", "medians"]:
        plt.setp(bp_u[element], color="black")

    #axes[1].set_xlabel("Year")
    #axes[1].set_ylabel("General health")
    # no title

    # ----- move y-axis labels and ticks to the right, keep left spine -----
    for ax in axes:
        ax.yaxis.set_label_position("right")
        ax.yaxis.tick_right()
        ax.tick_params(axis="y", left=False, right=True)
        ax.spines["left"].set_visible(True)
        ax.spines["right"].set_visible(True)

    plt.tight_layout()
    fig.savefig(save_path, dpi=300)
    print(f"[SAVE] Figure saved: {save_path}")
    plt.close(fig)


# --------------- main ---------------

def main():
    print(f"[READ] {PANEL_MERGED}")
    df = pd.read_parquet(PANEL_MERGED)

    if Y_VAR not in df.columns:
        raise KeyError(f"{Y_VAR} not found in the data.")

    df = add_urban_group(df)

    plot_combined_boxplots(df, save_path=OUT_DIR / OUT_FIG)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 14
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Rural vs Urban: KDE of 3 health dimensions (all waves pooled),
clipped to [0,1] for display.

Variables:
    - health_phys
    - health_mental
    - health_social
"""

from pathlib import Path
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# ---------------- global style ----------------
mpl.rcParams.update({
    "font.family": "Times New Roman",
    "axes.unicode_minus": False,
    "figure.dpi": 300,
    "axes.labelsize": 20,   # axis labels
    "axes.titlesize": 0,   # (we do not use titles here, but keep for consistency)
    "xtick.labelsize": 24,  # x tick labels
    "ytick.labelsize": 24,  # y tick labels
    "legend.fontsize": 21,  # legend font
})

# ---------------- paths ----------------
PANEL_MERGED = (
    Path(r"E:\impact_assessment_child_order\data\supplement\EDA")
    / "charls_health_panel_60plus_with_index_Tall_5_10_20_30y.parquet"
)

OUT_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\EDA\figure")
OUT_FIG = "health_kde_rural_urban.png"

ID_COL = "pid12"
URBAN_NBS_COL = "urban_nbs"
YEAR_COL = "year"

vars_3 = ["health_phys", "health_mental", "health_social"]
URBAN_THRESHOLD = 0.5

# fixed colors for the three dimensions
COLOR_MAP = {
    "health_phys": "#1b9e77",
    "health_mental": "#d95f02",
    "health_social": "#7570b3",
}

# legend label mapping (variable name -> display name)
LABEL_MAP = {
    "health_phys": "Physical health",
    "health_mental": "Mental health",
    "health_social": "Social health",
}


def add_urban_group(df, id_col=ID_COL, urban_nbs_col=URBAN_NBS_COL, threshold=URBAN_THRESHOLD):
    """
    Define urban_group: mean(urban_nbs) > threshold -> 1 (urban), else 0 (rural).
    """
    if urban_nbs_col not in df.columns:
        raise KeyError(f"Column '{urban_nbs_col}' not found.")

    out = df.copy()
    out[urban_nbs_col] = (
        pd.to_numeric(out[urban_nbs_col], errors="coerce")
        .fillna(0)
        .astype(int)
    )

    grp_urban = out.groupby(id_col)[urban_nbs_col].mean()
    out = out.merge(
        (grp_urban > threshold).astype(int).rename("urban_group"),
        on=id_col,
        how="left",
    )
    return out


def main():
    print(f"[READ] {PANEL_MERGED}")
    df = pd.read_parquet(PANEL_MERGED)

    # urban/rural grouping
    df = add_urban_group(df)

    # convert to numeric
    for v in vars_3:
        df[v] = pd.to_numeric(df.get(v), errors="coerce")

    # split by group
    rural = df[df["urban_group"] == 0].dropna(subset=vars_3, how="all").copy()
    urban = df[df["urban_group"] == 1].dropna(subset=vars_3, how="all").copy()

    # clip to [0,1] for display
    for v in vars_3:
        rural[v] = rural[v].clip(0, 1)
        urban[v] = urban[v].clip(0, 1)

    # ===== plot: 2 rows, 1 column =====
    fig, axes = plt.subplots(2, 1, figsize=(7, 8), sharex=True, sharey=True)

    # --- top: Rural ---
    for v in vars_3:
        s = rural[v].dropna()
        if len(s) > 0:
            s.plot(
                kind="density",
                ax=axes[0],
                label=LABEL_MAP.get(v, v),   # <- changed legend label
                color=COLOR_MAP.get(v, None),
            )

    #axes[0].set_ylabel("Density")
    axes[0].legend()

    # --- bottom: Urban ---
    for v in vars_3:
        s = urban[v].dropna()
        if len(s) > 0:
            s.plot(
                kind="density",
                ax=axes[1],
                label=LABEL_MAP.get(v, v),   # <- changed legend label
                color=COLOR_MAP.get(v, None),
            )

    axes[1].set_xlabel("General health")
    #axes[1].set_ylabel("Density")
    axes[1].legend()

    # move y-axis labeling to the right, keep left frame line
    for ax in axes:
        ax.set_ylabel("")                      # Original notebook comment normalized for the public code archive.
        ax.yaxis.set_label_position("right")   # Original notebook comment normalized for the public code archive.
        ax.yaxis.tick_right()                  # ticks on the right
        ax.tick_params(axis="y", left=False, right=True)
        ax.spines["left"].set_visible(True)
        ax.spines["right"].set_visible(True)

    # common x range
    axes[1].set_xlim(0, 1)

    plt.tight_layout()

    # save figure
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    save_path = OUT_DIR / OUT_FIG
    plt.savefig(save_path, dpi=300)
    print(f"[SAVE] Figure saved: {save_path}")

    plt.show()

    # optional: descriptive stats (after clipping)
    print("[INFO] Notebook progress message.")
    print(rural[vars_3].describe())

    print("[INFO] Notebook progress message.")
    print(urban[vars_3].describe())


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 18
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 03_charls_sample_health_urban_rural.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd


# =========================
# Original notebook comment normalized for the public code archive.
# =========================

BASE_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\EDA")
PANEL_MERGED = BASE_DIR / "charls_health_panel_60plus_with_index_Tall_5_10_20_30y.parquet"

OUT_DIR = BASE_DIR / "table"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_XLSX = OUT_DIR / "health_summary_by_wave_rural_urban.xlsx"

ID_COL = "pid12"
YEAR_COL = "year"
URBAN_NBS_COL = "urban_nbs"
URBAN_THRESHOLD = 0.5

# CHARLS processing note.
WAVES = [2011, 2013, 2015, 2018, 2020]

# Original notebook comment normalized for the public code archive.
HEALTH_VARS = {
    "health_phys": "Physical health",
    "health_mental": "Mental health",
    "health_social": "Social adaptation",
    "health_index_raw": "General health index",
}


# =========================
# Original notebook comment normalized for the public code archive.
# =========================

def add_urban_group(
    df: pd.DataFrame,
    id_col: str = ID_COL,
    urban_nbs_col: str = URBAN_NBS_COL,
    threshold: float = URBAN_THRESHOLD,
) -> pd.DataFrame:
    """Archived notebook note for 03_charls_sample_health_urban_rural.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if urban_nbs_col not in df.columns:
        raise KeyError(f"Column '{urban_nbs_col}' not found in data.")

    out = df.copy()
    out[urban_nbs_col] = pd.to_numeric(out[urban_nbs_col], errors="coerce").fillna(0)

    grp_mean = out.groupby(id_col)[urban_nbs_col].mean()
    urban_group = (grp_mean > threshold).astype(int).rename("urban_group")

    out = out.merge(urban_group, on=id_col, how="left")
    return out


def mean_se_ci(series: pd.Series) -> dict:
    """Archived notebook note for 03_charls_sample_health_urban_rural.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = pd.to_numeric(series, errors="coerce")
    s = s[np.isfinite(s)]
    n = int(s.size)

    if n == 0:
        return dict(n=0, mean=np.nan, sd=np.nan, se=np.nan,
                    ci_l=np.nan, ci_u=np.nan)

    mean = float(s.mean())
    if n > 1:
        sd = float(s.std(ddof=1))
        se = sd / np.sqrt(n)
    else:
        sd = 0.0
        se = 0.0

    ci_l = mean - 1.96 * se
    ci_u = mean + 1.96 * se

    return dict(n=n, mean=mean, sd=sd, se=se, ci_l=ci_l, ci_u=ci_u)


def fmt_num(x, decimals: int = 3) -> str:
    """Archived notebook note for 03_charls_sample_health_urban_rural.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if pd.isna(x):
        return ""
    return f"{x:.{decimals}f}"


def fmt_ci(l, u, decimals: int = 3) -> str:
    """Archived notebook note for 03_charls_sample_health_urban_rural.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if pd.isna(l) or pd.isna(u):
        return ""
    return f"[{fmt_num(l, decimals)}, {fmt_num(u, decimals)}]"


# =========================
# Original notebook comment normalized for the public code archive.
# =========================

def build_health_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 03_charls_sample_health_urban_rural.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    rows = []

    # Original notebook comment normalized for the public code archive.
    df = df.copy()
    df[YEAR_COL] = pd.to_numeric(df[YEAR_COL], errors="coerce")
    df = df[np.isfinite(df[YEAR_COL])]
    df[YEAR_COL] = df[YEAR_COL].astype(int)
    df = df[df[YEAR_COL].isin(WAVES)]

    # Original notebook comment normalized for the public code archive.
    for var in HEALTH_VARS.keys():
        if var not in df.columns:
            raise KeyError(f"Health variable '{var}' not found in data.")
        df[var] = pd.to_numeric(df[var], errors="coerce")
        df[var] = df[var].clip(lower=0.0, upper=1.0)

    # Original notebook comment normalized for the public code archive.
    time_levels = [("All waves", None)] + [(str(y), y) for y in WAVES]

    for time_label, year in time_levels:
        if year is None:
            sub = df
        else:
            sub = df[df[YEAR_COL] == year]

        if sub.empty:
            continue

        # Original notebook comment normalized for the public code archive.
        all_unique_id = sub[ID_COL].nunique()

        for var, label in HEALTH_VARS.items():
            # All / Rural / Urban stats
            stats_all = mean_se_ci(sub[var])
            stats_r = mean_se_ci(sub.loc[sub["urban_group"] == 0, var])
            stats_u = mean_se_ci(sub.loc[sub["urban_group"] == 1, var])

            # Original notebook comment normalized for the public code archive.
            sd_all = stats_all["sd"]
            if (
                (not pd.isna(sd_all))
                and (sd_all > 0)
                and (stats_r["n"] > 0)
                and (stats_u["n"] > 0)
            ):
                diff_raw = stats_u["mean"] - stats_r["mean"]
                se_diff_raw = np.sqrt(stats_r["se"] ** 2 + stats_u["se"] ** 2)
                diff_std = diff_raw / sd_all
                se_diff_std = se_diff_raw / sd_all
                ci_std_l = diff_std - 1.96 * se_diff_std
                ci_std_u = diff_std + 1.96 * se_diff_std
            else:
                diff_std = np.nan
                ci_std_l = np.nan
                ci_std_u = np.nan

            row = dict(
                Time=time_label,
                Variable_code=var,
                Variable_label=label,

                All_N=stats_all["n"],            # Original notebook comment normalized for the public code archive.
                All_unique_id=all_unique_id,     # Original notebook comment normalized for the public code archive.

                All_mean=stats_all["mean"],
                All_ci_l=stats_all["ci_l"],
                All_ci_u=stats_all["ci_u"],

                Rural_N=stats_r["n"],
                Rural_mean=stats_r["mean"],
                Rural_ci_l=stats_r["ci_l"],
                Rural_ci_u=stats_r["ci_u"],

                Urban_N=stats_u["n"],
                Urban_mean=stats_u["mean"],
                Urban_ci_l=stats_u["ci_l"],
                Urban_ci_u=stats_u["ci_u"],

                Std_diff=diff_std,
                Std_diff_ci_l=ci_std_l,
                Std_diff_ci_u=ci_std_u,
            )
            rows.append(row)

    summ = pd.DataFrame(rows)

    # =============================================================================
    summ["All_mean_str"] = summ["All_mean"].apply(fmt_num)
    summ["All_CI"] = summ.apply(
        lambda r: fmt_ci(r["All_ci_l"], r["All_ci_u"]), axis=1
    )

    summ["Rural_mean_str"] = summ["Rural_mean"].apply(fmt_num)
    summ["Rural_CI"] = summ.apply(
        lambda r: fmt_ci(r["Rural_ci_l"], r["Rural_ci_u"]), axis=1
    )

    summ["Urban_mean_str"] = summ["Urban_mean"].apply(fmt_num)
    summ["Urban_CI"] = summ.apply(
        lambda r: fmt_ci(r["Urban_ci_l"], r["Urban_ci_u"]), axis=1
    )

    summ["Std_diff_str"] = summ["Std_diff"].apply(fmt_num)
    summ["Std_diff_CI"] = summ.apply(
        lambda r: fmt_ci(r["Std_diff_ci_l"], r["Std_diff_ci_u"]), axis=1
    )

    # Original notebook comment normalized for the public code archive.
    time_order = ["All waves"] + [str(y) for y in WAVES]
    var_order = list(HEALTH_VARS.keys())

    summ["Time"] = pd.Categorical(summ["Time"], categories=time_order, ordered=True)
    summ["Variable_code"] = pd.Categorical(
        summ["Variable_code"], categories=var_order, ordered=True
    )
    summ = summ.sort_values(["Variable_code", "Time"]).reset_index(drop=True)

    return summ


# =========================
# main
# =========================

def main():
    print(f"[READ] {PANEL_MERGED}")
    df = pd.read_parquet(PANEL_MERGED)

    # Original notebook comment normalized for the public code archive.
    df = add_urban_group(df)

    # Original notebook comment normalized for the public code archive.
    summary = build_health_summary(df)

    # Original notebook comment normalized for the public code archive.
    export_cols = [
        "Time",
        "Variable_label",
        "All_N", "All_unique_id", "All_mean_str", "All_CI",
        "Rural_N", "Rural_mean_str", "Rural_CI",
        "Urban_N", "Urban_mean_str", "Urban_CI",
        "Std_diff_str", "Std_diff_CI",
    ]
    export_df = summary[export_cols].copy()

    print("\n[PREVIEW] first few rows:")
    print(export_df.head(12))

    with pd.ExcelWriter(OUT_XLSX) as writer:
        export_df.to_excel(writer, sheet_name="summary", index=False)

    print(f"\n[SAVE] Summary table written to:\n  {OUT_XLSX}")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 20
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Rural vs Urban: forest plot of standardized mean differences (health indices)

- Variables (columns in data):
    health_phys        -> Physical health
    health_mental      -> Mental health
    health_social      -> Social adaptation
    health_index_raw   -> Overall health index

- Time levels:
    All waves (2011, 2013, 2015, 2018, 2020 pooled)
    2011, 2013, 2015, 2018, 2020

Standardized difference = (mean_U - mean_R) / sd_all,
95% CI transformed accordingly.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt


# =========================
# Original notebook comment normalized for the public code archive.
# =========================

mpl.rcParams.update({
    "font.family": "Times New Roman",
    "axes.unicode_minus": False,
    "figure.dpi": 300,
    "xtick.labelsize": 10,
    "ytick.labelsize": 9,
})


# =========================
# Original notebook comment normalized for the public code archive.
# =========================

BASE_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\EDA")
PANEL_MERGED = BASE_DIR / "charls_health_panel_60plus_with_index_Tall_5_10_20_30y.parquet"

OUT_DIR = BASE_DIR / "figure"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PNG = OUT_DIR / "health_std_diff_forest_rural_urban.png"
OUT_SVG = OUT_DIR / "health_std_diff_forest_rural_urban.svg"

ID_COL = "pid12"
YEAR_COL = "year"
URBAN_NBS_COL = "urban_nbs"
URBAN_THRESHOLD = 0.5

WAVES = [2011, 2013, 2015, 2018, 2020]

HEALTH_VARS = {
    "health_phys": "Physical health",
    "health_mental": "Mental health",
    "health_social": "Social adaptation",
    "health_index_raw": "General health index",
}

# Original notebook comment normalized for the public code archive.
FIG_WIDTH_INCH = 33.556 / 25.4   # ≈ 1.3211 inch
FIG_HEIGHT_INCH = 155.867 / 25.4 # ≈ 6.1365 inch


# =========================
# Original notebook comment normalized for the public code archive.
# =========================

def add_urban_group(
    df: pd.DataFrame,
    id_col: str = ID_COL,
    urban_nbs_col: str = URBAN_NBS_COL,
    threshold: float = URBAN_THRESHOLD,
) -> pd.DataFrame:
    """Archived notebook note for 03_charls_sample_health_urban_rural.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if urban_nbs_col not in df.columns:
        raise KeyError(f"Column '{urban_nbs_col}' not found in data.")

    out = df.copy()
    out[urban_nbs_col] = pd.to_numeric(out[urban_nbs_col], errors="coerce").fillna(0)

    grp_mean = out.groupby(id_col)[urban_nbs_col].mean()
    urban_group = (grp_mean > threshold).astype(int).rename("urban_group")

    out = out.merge(urban_group, on=id_col, how="left")
    return out


def mean_se_ci(series: pd.Series) -> dict:
    """Archived notebook note for 03_charls_sample_health_urban_rural.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = pd.to_numeric(series, errors="coerce")
    s = s[np.isfinite(s)]
    n = int(s.size)

    if n == 0:
        return dict(n=0, mean=np.nan, sd=np.nan, se=np.nan,
                    ci_l=np.nan, ci_u=np.nan)

    mean = float(s.mean())
    if n > 1:
        sd = float(s.std(ddof=1))
        se = sd / np.sqrt(n)
    else:
        sd = 0.0
        se = 0.0

    ci_l = mean - 1.96 * se
    ci_u = mean + 1.96 * se

    return dict(n=n, mean=mean, sd=sd, se=se, ci_l=ci_l, ci_u=ci_u)


# =========================
# Original notebook comment normalized for the public code archive.
# =========================

def build_health_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 03_charls_sample_health_urban_rural.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    rows = []

    df = df.copy()
    df[YEAR_COL] = pd.to_numeric(df[YEAR_COL], errors="coerce")
    df = df[np.isfinite(df[YEAR_COL])]
    df[YEAR_COL] = df[YEAR_COL].astype(int)
    df = df[df[YEAR_COL].isin(WAVES)]

    # Original notebook comment normalized for the public code archive.
    for var in HEALTH_VARS.keys():
        if var not in df.columns:
            raise KeyError(f"Health variable '{var}' not found in data.")
        df[var] = pd.to_numeric(df[var], errors="coerce")
        df[var] = df[var].clip(lower=0.0, upper=1.0)

    # Original notebook comment normalized for the public code archive.
    time_levels = [("All waves", None)] + [(str(y), y) for y in WAVES]

    for time_label, year in time_levels:
        if year is None:
            sub = df
        else:
            sub = df[df[YEAR_COL] == year]

        if sub.empty:
            continue

        for var, label in HEALTH_VARS.items():
            stats_all = mean_se_ci(sub[var])
            stats_r = mean_se_ci(sub.loc[sub["urban_group"] == 0, var])
            stats_u = mean_se_ci(sub.loc[sub["urban_group"] == 1, var])

            sd_all = stats_all["sd"]
            if (
                (not pd.isna(sd_all))
                and (sd_all > 0)
                and (stats_r["n"] > 0)
                and (stats_u["n"] > 0)
            ):
                diff_raw = stats_u["mean"] - stats_r["mean"]
                se_diff_raw = np.sqrt(stats_r["se"] ** 2 + stats_u["se"] ** 2)

                diff_std = diff_raw / sd_all
                se_diff_std = se_diff_raw / sd_all
                ci_std_l = diff_std - 1.96 * se_diff_std
                ci_std_u = diff_std + 1.96 * se_diff_std
            else:
                diff_std = np.nan
                ci_std_l = np.nan
                ci_std_u = np.nan

            rows.append(
                dict(
                    Time=time_label,
                    Variable_code=var,
                    Variable_label=label,
                    Std_diff=diff_std,
                    Std_diff_ci_l=ci_std_l,
                    Std_diff_ci_u=ci_std_u,
                )
            )

    summ = pd.DataFrame(rows)

    # Original notebook comment normalized for the public code archive.
    time_order = ["All waves"] + [str(y) for y in WAVES]
    var_order = list(HEALTH_VARS.keys())

    summ["Time"] = pd.Categorical(summ["Time"], categories=time_order, ordered=True)
    summ["Variable_code"] = pd.Categorical(
        summ["Variable_code"], categories=var_order, ordered=True
    )
    summ = summ.sort_values(["Variable_code", "Time"]).reset_index(drop=True)

    return summ


# =========================
# Original notebook comment normalized for the public code archive.
# =========================

def plot_forest(summary: pd.DataFrame,
                out_png: Path = OUT_PNG,
                out_svg: Path = OUT_SVG):
    """Archived notebook note for 03_charls_sample_health_urban_rural.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

    df = summary.copy()
    df = df[df["Std_diff"].notna()].reset_index(drop=True)

    if df.empty:
        print("[WARN] No non-missing Std_diff; skip forest plot.")
        return

    # Original notebook comment normalized for the public code archive.
    df["Label"] = df["Variable_label"].astype(str) + " (" + df["Time"].astype(str) + ")"

    # Original notebook comment normalized for the public code archive.
    df = df.iloc[::-1].reset_index(drop=True)

    y_pos = np.arange(len(df))  # 0,1,...,n-1

    x = df["Std_diff"].to_numpy(dtype=float)
    x_l = df["Std_diff_ci_l"].to_numpy(dtype=float)
    x_u = df["Std_diff_ci_u"].to_numpy(dtype=float)

    # Original notebook comment normalized for the public code archive.
    x_min = np.nanmin(x_l)
    x_max = np.nanmax(x_u)
    if not np.isfinite(x_min) or not np.isfinite(x_max):
        x_min, x_max = -0.2, 0.4
    pad = 0.05 * (x_max - x_min) if x_max > x_min else 0.05

    # Original notebook comment normalized for the public code archive.
    fig, ax = plt.subplots(figsize=(FIG_WIDTH_INCH, FIG_HEIGHT_INCH))

    # Original notebook comment normalized for the public code archive.
    ax.hlines(y=y_pos, xmin=x_l, xmax=x_u, color="black", linewidth=1)
    ax.plot(x, y_pos, "o", color="red", markersize=4)

    # Original notebook comment normalized for the public code archive.
    ax.axvline(0, color="grey", linestyle="--", linewidth=1)

    # Original notebook comment normalized for the public code archive.
    ax.set_yticks(y_pos)
    ax.set_yticklabels(df["Label"])

    ax.set_xlabel("Urban − Rural (standardized mean difference, SD units)")

    ax.set_xlim(x_min - pad, x_max + pad)

    plt.tight_layout()

    # Original notebook comment normalized for the public code archive.
    fig.savefig(out_png, dpi=300)
    fig.savefig(out_svg, dpi=300, transparent=True)
    print(f"[SAVE] Forest plot saved:\n  {out_png}\n  {out_svg}")

    plt.close(fig)


# =========================
# main
# =========================

def main():
    print(f"[READ] {PANEL_MERGED}")
    df = pd.read_parquet(PANEL_MERGED)

    # Original notebook comment normalized for the public code archive.
    df = add_urban_group(df)

    # Original notebook comment normalized for the public code archive.
    summary = build_health_summary(df)

    print("\n[CHECK] first few rows of summary:")
    print(summary.head())

    # Original notebook comment normalized for the public code archive.
    plot_forest(summary)


if __name__ == "__main__":
    main()
