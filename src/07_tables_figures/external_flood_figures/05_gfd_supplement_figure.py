#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 05_gfd_supplement_figure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 3
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
# =======================
# Global style
# =======================
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False

mpl.rcParams.update({
    "font.size": 12,         # Original notebook comment normalized for the public code archive.
    "axes.labelsize": 16,    # Original notebook comment normalized for the public code archive.
    "axes.titlesize": 16,    # Original notebook comment normalized for the public code archive.
    "xtick.labelsize": 16,   # Original notebook comment normalized for the public code archive.
    "ytick.labelsize": 16,   # Original notebook comment normalized for the public code archive.
    "legend.fontsize": 12,   # Original notebook comment normalized for the public code archive.
})

# =======================
# Paths (Windows)
# =======================
IN_DIR   = r"E:\impact_assessment_child_order\data\supplement\accuracy"
OUT_DIR  = r"E:\impact_assessment_child_order\data\supplement\accuracy\GFD"

CACHE_NPZ = os.path.join(IN_DIR, "event_POD_cache_2000_2018.npz")
OUT_PNG   = os.path.join(OUT_DIR, "event_POD_hist_from_cache_2000_2018.png")

# =======================
# Global style: Times New Roman
# =======================
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False  # avoid minus sign issues

def main():
    if not os.path.exists(CACHE_NPZ):
        raise FileNotFoundError(
            f"Cache not found: {CACHE_NPZ}\n"
            f"Please run make_pod_cache_2000_2018.py first."
        )

    os.makedirs(OUT_DIR, exist_ok=True)

    data = np.load(CACHE_NPZ, allow_pickle=False)
    if "pod" not in data.files:
        raise KeyError(f"'pod' not found in cache npz. Keys: {data.files}")

    pod = data["pod"].astype(float)
    pod = pod[np.isfinite(pod)]

    if pod.size == 0:
        print("[WARN] No valid POD values in cache. Histogram not generated.")
        return

    plt.figure(figsize=(12, 4))
    plt.hist(
        pod,
        bins=20,
        range=(0.0, 1.0),
        color="#8dd3c7",
        edgecolor="black",
        linewidth=0.8
    )
    plt.xlabel("Event-level POD")
    plt.ylabel("Number of events")
    plt.tight_layout()
    plt.savefig(OUT_PNG, dpi=300)
    plt.close()

    print(f"[SAVE] {OUT_PNG}")
    print(f"[INFO] N={pod.size}, min={pod.min():.4f}, max={pod.max():.4f}, mean={pod.mean():.4f}, median={np.median(pod):.4f}")

if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 6
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# =======================
# Paths (Windows)
# =======================
IN_DIR   = r"E:\impact_assessment_child_order\data\supplement\accuracy"
OUT_DIR  = r"E:\impact_assessment_child_order\data\supplement\accuracy\GFD"

CSV_PATH = os.path.join(IN_DIR, "event_POD_cache_2000_2018.csv")
OUT_PNG  = os.path.join(OUT_DIR, "event_FAR_hist_from_csv_2000_2018.png")

# =======================
# Global style: Times New Roman
# =======================
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False

def main():
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

    os.makedirs(OUT_DIR, exist_ok=True)

    df = pd.read_csv(CSV_PATH)

    # Required columns: TP, FP
    for col in ["TP", "FP"]:
        if col not in df.columns:
            raise KeyError(f"Column '{col}' not found in CSV. Available: {list(df.columns)}")

    tp = pd.to_numeric(df["TP"], errors="coerce").to_numpy(dtype=float)
    fp = pd.to_numeric(df["FP"], errors="coerce").to_numpy(dtype=float)

    denom = tp + fp
    far = np.where(denom > 0, fp / denom, np.nan)
    far = far[np.isfinite(far)]
    far = far[(far >= 0.0) & (far <= 1.0)]

    if far.size == 0:
        print("[WARN] No valid FAR values. Histogram not generated.")
        return

    plt.figure(figsize=(6, 4))
    plt.hist(far, bins=20, range=(0.0, 1.0), edgecolor="black", linewidth=0.8)
    plt.xlabel("Event-level FAR (False Alarm Ratio)")
    plt.ylabel("Number of events")
    plt.tight_layout()
    plt.savefig(OUT_PNG, dpi=300)
    plt.close()

    print(f"[SAVE] {OUT_PNG}")
    print(f"[INFO] N={far.size}, min={far.min():.4f}, max={far.max():.4f}, mean={far.mean():.4f}")

if __name__ == "__main__":
    main()
