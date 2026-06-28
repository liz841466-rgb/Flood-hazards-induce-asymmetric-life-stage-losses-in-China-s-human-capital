#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Plot county-level additional add-rate histogram.

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
    "legend.fontsize": 12,
})


# =======================
# Paths
# =======================
BASE_DIR = r"E:\impact_assessment_child_order\data\supplement\accuracy\DFO"
CSV_PATH = os.path.join(BASE_DIR, "tri_county_summary.csv")
OUT_PNG = os.path.join(BASE_DIR, "hist_add_rate.png")


# =======================
# Parameters
# =======================
COL_RATE = "add_rate"
MIN_DENOM = 5
BINS = 20
XRANGE = (0.0, 1.0)

BAR_COLOR = "#fdb863"
EDGE_COLOR = "black"
EDGE_LW = 0.8


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

    df["N_add"] = _to_num(df["N_add"]).fillna(0).astype(int)
    df["N_neither"] = _to_num(df["N_neither"]).fillna(0).astype(int)
    df[COL_RATE] = _to_num(df[COL_RATE])

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
        linewidth=EDGE_LW,
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

