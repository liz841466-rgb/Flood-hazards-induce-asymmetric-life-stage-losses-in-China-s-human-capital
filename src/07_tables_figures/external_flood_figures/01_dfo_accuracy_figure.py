#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 01_dfo_accuracy_figure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 2
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Draw side-by-side histograms of CaMa hit rate and false alarm rate
from an exported CSV file.

Input:
  E:\impact_assessment_child_order\data\supplement\accuracy\
    city_hit_false_rates_for_hist.csv

Output:
  Same directory:
    hist_stacked_hit_false_from_export.png
"""

import os
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# ===== Global style: Times New Roman, no Chinese on figure =====
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False

BASE_DIR = r"E:\impact_assessment_child_order\data\supplement\accuracy"
CSV_PATH = os.path.join(BASE_DIR, "city_hit_false_rates_for_hist.csv")
OUT_PNG = os.path.join(BASE_DIR, "hist_stacked_hit_false_from_export.png")
# =============================================================================
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False

# Original notebook comment normalized for the public code archive.
mpl.rcParams["axes.labelsize"] = 18      # Original notebook comment normalized for the public code archive.
mpl.rcParams["xtick.labelsize"] = 16     # Original notebook comment normalized for the public code archive.
mpl.rcParams["ytick.labelsize"] = 16     # Original notebook comment normalized for the public code archive.
mpl.rcParams["legend.fontsize"] = 16     # Original notebook comment normalized for the public code archive.

def main():
    df = pd.read_csv(CSV_PATH)

    col1 = "hit_rate_DFOyears"
    col2 = "false_alarm_rate_CAMAYears"

    data1 = df[col1].dropna().values
    data2 = df[col2].dropna().values

    if (data1.size == 0) or (data2.size == 0):
        print("[WARN] Hit rate or false alarm rate is empty. No figure generated.")
        return

    mean1 = data1.mean()
    mean2 = data2.mean()

    # histogram bins
    bins = 20
    bins_edges = np.linspace(0.0, 1.0, bins + 1)
    counts1, edges = np.histogram(data1, bins=bins_edges)
    counts2, _ = np.histogram(data2, bins=bins_edges)

    centers = (edges[:-1] + edges[1:]) / 2.0
    width = edges[1] - edges[0]

    fig, ax = plt.subplots(1, 1, figsize=(7, 4))

    # side-by-side bars (not stacked)
    bar_width = width * 0.35

    ax.bar(
        centers - bar_width / 2,
        counts1,
        width=bar_width,
        color="#8c510a",       # HIT color
        label="Hit rate",
    )
    ax.bar(
        centers + bar_width / 2,
        counts2,
        width=bar_width,
        color="#01665e",       # False color
        label="False rate",
    )

    # mean vertical lines
    ax.axvline(
        mean1,
        linestyle="--",
        linewidth=1.5,
        color="#8c510a",
        label=f"Hit mean = {mean1:.2f}",
    )
    ax.axvline(
        mean2,
        linestyle="--",
        linewidth=1.5,
        color="#01665e",
        label=f"False mean = {mean2:.2f}",
    )

    ax.set_xlim(0.0, 1.0)
    ax.set_xlabel("Rate")
    ax.set_ylabel("Number of cities")

    # no title, all text is English only
    handles, labels = ax.get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    ax.legend(unique.values(), unique.keys(), fontsize=16, frameon=False, loc="upper left")

    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=300, transparent=True)
    plt.show()
    print(f"[SAVE] Figure saved: {OUT_PNG}")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 4
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 01_dfo_accuracy_figure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# =============================================================================
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False

# =============================================================================
BASE_DIR = r"E:\impact_assessment_child_order\data\supplement\accuracy\country"
CSV_PATH = os.path.join(BASE_DIR, "county_hit_false_rates_for_hist.csv")
OUT_PNG = os.path.join(BASE_DIR, "county_hist_stacked_hit_false_from_export.png")

# =============================================================================
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False

# Original notebook comment normalized for the public code archive.
mpl.rcParams["axes.labelsize"] = 18      # Original notebook comment normalized for the public code archive.
mpl.rcParams["xtick.labelsize"] = 16     # Original notebook comment normalized for the public code archive.
mpl.rcParams["ytick.labelsize"] = 16     # Original notebook comment normalized for the public code archive.
mpl.rcParams["legend.fontsize"] = 20     # Original notebook comment normalized for the public code archive.


def main():
    print("[INFO] Notebook progress message.")
    df = pd.read_csv(CSV_PATH)

    col_hit = "hit_rate_DFOyears"
    col_false = "false_alarm_rate_CAMAYears"

    if col_hit not in df.columns or col_false not in df.columns:
        raise RuntimeError(
            f"Required columns not found in CSV: {col_hit}, {col_false}. "
            f"Please check county_hit_false_rates_for_hist.csv."
        )

    data_hit = df[col_hit].dropna().values
    data_false = df[col_false].dropna().values

    if (data_hit.size == 0) or (data_false.size == 0):
        print("[WARN] Hit rate or false alarm rate is empty. No figure generated.")
        return

    mean_hit = data_hit.mean()
    mean_false = data_false.mean()
    print(f"[INFO] Mean hit rate   : {mean_hit:.3f}")
    print(f"[INFO] Mean false alarm: {mean_false:.3f}")

    # =============================================================================
    bins = 20
    bins_edges = np.linspace(0.0, 1.0, bins + 1)
    counts_hit, edges = np.histogram(data_hit, bins=bins_edges)
    counts_false, _ = np.histogram(data_false, bins=bins_edges)

    centers = (edges[:-1] + edges[1:]) / 2.0
    width = edges[1] - edges[0]

    # =============================================================================
    fig, ax = plt.subplots(1, 1, figsize=(7, 4))

    bar_width = width * 0.35

    # HIT: #8c510a
    ax.bar(
        centers - bar_width / 2,
        counts_hit,
        width=bar_width,
        color="#762a83",
        label="Hit rate",
    )
    # False alarm: #01665e
    ax.bar(
        centers + bar_width / 2,
        counts_false,
        width=bar_width,
        color="#1b7837",
        label="False rate",
    )

    # mean lines
    ax.axvline(
        mean_hit,
        linestyle="--",
        linewidth=1.5,
        color="#762a83",
        label=f"Hit mean = {mean_hit:.2f}",
    )
    ax.axvline(
        mean_false,
        linestyle="--",
        linewidth=1.5,
        color="#1b7837",
        label=f"False mean = {mean_false:.2f}",
    )

    ax.set_xlim(0.0, 1.0)
    ax.set_xlabel("Rate")
    ax.set_ylabel("Number of counties")
    # no title; all labels are English

    # Original notebook comment normalized for the public code archive.
    handles, labels = ax.get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    ax.legend(unique.values(), unique.keys(), fontsize=16, frameon=False, loc="upper left" )

    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=300, transparent=True)
    plt.show()
    print(f"[SAVE] Figure saved: {OUT_PNG}")


if __name__ == "__main__":
    main()
