#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Plot county-level hit-rate and false-rate histograms.

This script supports the Chinese news-based flood inventory validation. It uses
local summary CSV files and does not redistribute raw inventory records.
"""

import os

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# =======================
# Global style
# =======================
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams.update({
    "figure.dpi": 300,
    "font.size": 12,
    "axes.labelsize": 16,
    "axes.titlesize": 16,
    "xtick.labelsize": 14,
    "ytick.labelsize": 14,
    "legend.fontsize": 14,
})


# =======================
# Paths
# =======================
BASE_DIR = r"E:\impact_assessment_child_order\data\supplement\accuracy\DFO"
CSV_PATH = os.path.join(BASE_DIR, "county_hit_false_rates_for_hist_fromPAC.csv")
OUT_PNG = os.path.join(BASE_DIR, "county_hist_sideby_hit_false_2000_2020_fromPAC.png")


# =======================
# Parameters
# =======================
COL_HIT = "hit_rate_DFOyears"
COL_FALSE = "false_alarm_rate_CAMAYears"

BINS = 20
XRANGE = (0.0, 1.0)

HIT_COLOR = "#e66101"
FALSE_COLOR = "#2b83ba"


def _clean_rate(arr, x0=0.0, x1=1.0):
    arr = pd.to_numeric(arr, errors="coerce").to_numpy(dtype=float)
    arr = arr[np.isfinite(arr)]
    arr = arr[(arr >= x0) & (arr <= x1)]
    return arr


def main():
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

    os.makedirs(os.path.dirname(OUT_PNG), exist_ok=True)

    df = pd.read_csv(CSV_PATH)

    for c in [COL_HIT, COL_FALSE]:
        if c not in df.columns:
            raise RuntimeError(f"Missing column: {c}. Available: {list(df.columns)}")

    data_hit = _clean_rate(df[COL_HIT], *XRANGE)
    data_false = _clean_rate(df[COL_FALSE], *XRANGE)

    if (data_hit.size == 0) or (data_false.size == 0):
        raise RuntimeError("No valid hit/false data after cleaning.")

    mean_hit = float(np.mean(data_hit))
    mean_false = float(np.mean(data_false))

    print(f"[INFO] CSV           : {CSV_PATH}")
    print(f"[INFO] OUT_PNG       : {OUT_PNG}")
    print(f"[INFO] Hit mean      : {mean_hit:.4f} (N={data_hit.size})")
    print(f"[INFO] False mean    : {mean_false:.4f} (N={data_false.size})")

    edges = np.linspace(XRANGE[0], XRANGE[1], BINS + 1)
    counts_hit, _ = np.histogram(data_hit, bins=edges)
    counts_false, _ = np.histogram(data_false, bins=edges)

    centers = (edges[:-1] + edges[1:]) / 2.0
    width = edges[1] - edges[0]
    bar_width = width * 0.35

    fig, ax = plt.subplots(figsize=(7, 4))

    ax.bar(
        centers - bar_width / 2,
        counts_hit,
        width=bar_width,
        color=HIT_COLOR,
        label="Hit rate",
    )
    ax.bar(
        centers + bar_width / 2,
        counts_false,
        width=bar_width,
        color=FALSE_COLOR,
        label="False rate",
    )

    ax.axvline(
        mean_hit,
        linestyle="--",
        linewidth=1.5,
        color=HIT_COLOR,
        label=f"Hit mean = {mean_hit:.2f}",
    )
    ax.axvline(
        mean_false,
        linestyle="--",
        linewidth=1.5,
        color=FALSE_COLOR,
        label=f"False mean = {mean_false:.2f}",
    )

    ax.set_xlim(*XRANGE)
    ax.set_xlabel("Rate")
    ax.set_ylabel("Number of counties")

    handles, labels = ax.get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    ax.legend(unique.values(), unique.keys(), fontsize=12, frameon=False, loc="upper left")

    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=300, transparent=True)
    plt.show()

    print(f"[SAVE] {OUT_PNG}")


if __name__ == "__main__":
    main()

