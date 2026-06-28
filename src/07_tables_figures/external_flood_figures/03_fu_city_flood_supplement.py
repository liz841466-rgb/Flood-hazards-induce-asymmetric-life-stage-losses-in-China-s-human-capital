#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 03_fu_city_flood_supplement.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 2
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

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
    "legend.fontsize": 14,   # Original notebook comment normalized for the public code archive.
})

# =======================
# Paths (Windows)
# =======================
BASE_DIR = r"E:\impact_assessment_child_order\data\supplement\accuracy\DFO"
CSV_PATH = os.path.join(BASE_DIR, "county_hit_false_rates_for_hist_fromPAC.csv")
OUT_PNG  = os.path.join(BASE_DIR, "county_hist_sideby_hit_false_2000_2020_fromPAC.png")

# =======================
# Params
# =======================
COL_HIT   = "hit_rate_DFOyears"
COL_FALSE = "false_alarm_rate_CAMAYears"

BINS   = 20
XRANGE = (0.0, 1.0)

HIT_COLOR   = "#e66101"
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

    # ===== fixed bins on [0,1] =====
    edges = np.linspace(XRANGE[0], XRANGE[1], BINS + 1)
    counts_hit, _ = np.histogram(data_hit, bins=edges)
    counts_false, _ = np.histogram(data_false, bins=edges)

    centers = (edges[:-1] + edges[1:]) / 2.0
    width = edges[1] - edges[0]
    bar_width = width * 0.35

    # ===== side-by-side histogram bars =====
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

    # mean lines
    ax.axvline(mean_hit, linestyle="--", linewidth=1.5, color=HIT_COLOR,
               label=f"Hit mean = {mean_hit:.2f}")
    ax.axvline(mean_false, linestyle="--", linewidth=1.5, color=FALSE_COLOR,
               label=f"False mean = {mean_false:.2f}")

    ax.set_xlim(*XRANGE)
    ax.set_xlabel("Rate")
    ax.set_ylabel("Number of counties")
    # no title; all labels are English

    # legend (deduplicate)
    handles, labels = ax.get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    ax.legend(unique.values(), unique.keys(), fontsize=12, frameon=False, loc="upper left")

    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=300, transparent=True)
    plt.show()

    print(f"[SAVE] {OUT_PNG}")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 5
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

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
    "legend.fontsize": 12,
})

# =======================
# Paths (Windows)
# =======================
BASE_DIR = r"E:\impact_assessment_child_order\data\supplement\accuracy\DFO"
CSV_PATH = os.path.join(BASE_DIR, "tri_county_summary.csv")
OUT_PNG  = os.path.join(BASE_DIR, "hist_add_rate.png")

# =======================
# Params
# =======================
COL_RATE  = "add_rate"
MIN_DENOM = 5
BINS      = 20
XRANGE    = (0.0, 1.0)

BAR_COLOR  = "#fdb863"
EDGE_COLOR = "black"
EDGE_LW    = 0.8


def _to_num(s):
    return pd.to_numeric(s, errors="coerce")


def main():
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

    os.makedirs(os.path.dirname(OUT_PNG), exist_ok=True)

    df = pd.read_csv(CSV_PATH)

    need = ["N_add", "N_neither", COL_RATE]
    miss = [c for c in need if c not in df.columns]
    if miss:
        raise RuntimeError(f"Missing columns {miss}. Available: {list(df.columns)}")

    df["N_add"]     = _to_num(df["N_add"]).fillna(0).astype(int)
    df["N_neither"] = _to_num(df["N_neither"]).fillna(0).astype(int)
    df[COL_RATE]    = _to_num(df[COL_RATE])

    df["denom"] = df["N_add"] + df["N_neither"]

    if MIN_DENOM > 0:
        df = df[df["denom"] >= MIN_DENOM].copy()

    data = df[COL_RATE].to_numpy(dtype=float)
    data = data[np.isfinite(data)]
    data = data[(data >= XRANGE[0]) & (data <= XRANGE[1])]

    if data.size == 0:
        raise RuntimeError("No valid add_rate values after filtering/cleaning.")

    mean_v = float(np.mean(data))
    min_v = float(np.min(data))
    max_v = float(np.max(data))

    print(f"[INFO] CSV      : {CSV_PATH}")
    print(f"[INFO] OUT_PNG  : {OUT_PNG}")
    print(f"[INFO] counties : {data.size} (denom >= {MIN_DENOM})")
    print(f"[INFO] add_rate : mean={mean_v:.4f}, min={min_v:.4f}, max={max_v:.4f}")

    edges = np.linspace(XRANGE[0], XRANGE[1], BINS + 1)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(
        data,
        bins=edges,
        color=BAR_COLOR,
        edgecolor=EDGE_COLOR,
        linewidth=EDGE_LW
    )

    ax.axvline(mean_v, linestyle="--", linewidth=1.5, color="black", label=f"Mean = {mean_v:.2f}")

    ax.set_xlim(*XRANGE)
    ax.set_xlabel("Add rate")
    ax.set_ylabel("Number of counties")
    ax.legend(frameon=False, loc="upper left")

    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=300)
    plt.show()

    print(f"[SAVE] {OUT_PNG}")


if __name__ == "__main__":
    main()
