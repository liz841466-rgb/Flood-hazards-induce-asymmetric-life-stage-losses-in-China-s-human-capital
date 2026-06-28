#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 01_city_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 3
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 01_city_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import numpy as np
import pandas as pd

# =============================================================================

BASE_DIR = "/home/ll/jupyter_notebook"

# CaMa-Flood processing note.
CAMA_DIR = os.path.join(BASE_DIR, "result/impact_assessment/older")
CAMA_CSV = os.path.join(
    CAMA_DIR,
    "city_flood_events_T2_5_10_20_50_100_1980_2020.csv"
)

# External flood dataset comparison note.
DFO_DIR = os.path.join(BASE_DIR, "result/impact_assessment/older/DFO_city")
DFO_PARQ = os.path.join(
    DFO_DIR,
    "dfo_city_year_1980_2020_all_sev.parquet"
)

# Original notebook comment normalized for the public code archive.
OUT_DIR = os.path.join(BASE_DIR, "result/impact_assessment/older/compare_DFO_all_events")
os.makedirs(OUT_DIR, exist_ok=True)


# =============================================================================

def load_cama_events(path: str) -> pd.DataFrame:
    """Archived notebook note for 01_city_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = pd.read_csv(path, dtype={"city_code": str})

    # Original notebook comment normalized for the public code archive.
    cama_cols = [c for c in df.columns if c.startswith("flood_ge_T")]
    if not cama_cols:
        raise RuntimeError("未在 CaMa CSV 中找到 flood_ge_T* 列，请检查输入文件。")

    # Original notebook comment normalized for the public code archive.
    for c in cama_cols:
        df[c] = df[c].astype(int)

    # CaMa-Flood processing note.
    df["cama_any_event"] = (df[cama_cols].max(axis=1) > 0).astype(int)

    # Original notebook comment normalized for the public code archive.
    keep = ["year", "city_code", "cama_any_event"] + cama_cols
    df = df[keep]

    return df


def load_dfo_panel(path: str) -> pd.DataFrame:
    """Archived notebook note for 01_city_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = pd.read_parquet(path)
    df["city_code"] = df["city_code"].astype(str)

    # Original notebook comment normalized for the public code archive.
    needed = ["flooded_any_centroid", "flooded_any_area50", "flooded_any_full"]
    for c in needed:
        if c not in df.columns:
            raise RuntimeError(f"DFO 表中缺少列: {c}")
        df[c] = df[c].astype(int)

    keep = ["year", "city_code"] + needed
    return df[keep]


# =============================================================================

def compute_contingency_and_skill(
    cama_flag: pd.Series,
    dfo_flag: pd.Series,
) -> dict:
    """Archived notebook note for 01_city_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    cama = cama_flag.astype(int).values
    dfo = dfo_flag.astype(int).values

    hits         = int(((cama == 1) & (dfo == 1)).sum())
    misses       = int(((cama == 0) & (dfo == 1)).sum())
    false_alarms = int(((cama == 1) & (dfo == 0)).sum())
    correct_neg  = int(((cama == 0) & (dfo == 0)).sum())

    H, M, F, C = hits, misses, false_alarms, correct_neg
    TOT = H + M + F + C

    pod = H / (H + M) if (H + M) > 0 else np.nan          # Probability of Detection
    far = F / (H + F) if (H + F) > 0 else np.nan          # False Alarm Ratio
    pofd = F / (F + C) if (F + C) > 0 else np.nan         # Probability of False Detection
    csi = H / (H + M + F) if (H + M + F) > 0 else np.nan  # Critical Success Index

    # External flood dataset comparison note.
    freq_cama = (H + F) / TOT if TOT > 0 else np.nan
    freq_dfo  = (H + M) / TOT if TOT > 0 else np.nan
    bias = freq_cama / freq_dfo if (freq_cama >= 0 and freq_dfo > 0) else np.nan

    # Heidke Skill Score (HSS)
    denom_hss = (H + M) * (M + C) + (H + F) * (F + C)
    hss = (2 * (H * C - F * M) / denom_hss) if denom_hss > 0 else np.nan

    # Equitable Threat Score (ETS)
    if TOT > 0:
        h_random = (H + M) * (H + F) / TOT
        denom_ets = (H + M + F - h_random)
        ets = (H - h_random) / denom_ets if denom_ets > 0 else np.nan
    else:
        ets = np.nan

    return {
        "H": H,
        "M": M,
        "F": F,
        "C": C,
        "POD": pod,
        "FAR": far,
        "POFD": pofd,
        "CSI": csi,
        "Bias": bias,
        "HSS": hss,
        "ETS": ets,
        "freq_cama": freq_cama,
        "freq_dfo": freq_dfo,
    }


def print_skill_report(label: str, metrics: dict):
    """Archived notebook note for 01_city_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print("\n" + "=" * 72)
    print("[INFO] Notebook progress message.")
    print("-" * 72)
    print(f"Hits         (1,1): {metrics['H']}")
    print(f"Misses       (0,1): {metrics['M']}")
    print(f"False alarms (1,0): {metrics['F']}")
    print(f"Correct neg  (0,0): {metrics['C']}")
    print("-" * 72)
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print(f"HSS  (Heidke Skill Score)     = {metrics['HSS']:.3f}")
    print(f"ETS  (Equitable Threat Score) = {metrics['ETS']:.3f}")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")


# =============================================================================

def main():
    print("[INFO] Notebook progress message.")
    df_cama = load_cama_events(CAMA_CSV)

    print("[INFO] Notebook progress message.")
    df_dfo = load_dfo_panel(DFO_PARQ)

    print("[INFO] Notebook progress message.")
    df = df_cama.merge(
        df_dfo,
        on=["city_code", "year"],
        how="inner",
        suffixes=("_cama", "_dfo")
    )
    print("[INFO] Notebook progress message.", df.shape)

    # =============================================================================
    dfo_centroid = df["flooded_any_centroid"].astype(int)
    cama_any = df["cama_any_event"].astype(int)

    metrics_cent = compute_contingency_and_skill(cama_any, dfo_centroid)
    print_skill_report("[INFO] Notebook progress message.", metrics_cent)

    # Original notebook comment normalized for the public code archive.
    grp_cent = df.groupby("city_code", as_index=False).agg(
        cama_any_freq=("cama_any_event", "mean"),
        dfo_any_freq_centroid=("flooded_any_centroid", "mean"),
    )
    corr_cent = grp_cent["cama_any_freq"].corr(grp_cent["dfo_any_freq_centroid"])
    print("[INFO] Notebook progress message.")

    out_cent = os.path.join(
        OUT_DIR, "city_freq_CaMaAny_vs_DFOAny_centroid.csv"
    )
    grp_cent.to_csv(out_cent, index=False)
    print("[INFO] Notebook progress message.")

    # =============================================================================
    dfo_area50 = df["flooded_any_area50"].astype(int)
    metrics_a50 = compute_contingency_and_skill(cama_any, dfo_area50)
    print_skill_report("[INFO] Notebook progress message.", metrics_a50)

    grp_a50 = df.groupby("city_code", as_index=False).agg(
        cama_any_freq=("cama_any_event", "mean"),
        dfo_any_freq_area50=("flooded_any_area50", "mean"),
    )
    corr_a50 = grp_a50["cama_any_freq"].corr(grp_a50["dfo_any_freq_area50"])
    print("[INFO] Notebook progress message.")

    out_a50 = os.path.join(
        OUT_DIR, "city_freq_CaMaAny_vs_DFOAny_area50.csv"
    )
    grp_a50.to_csv(out_a50, index=False)
    print("[INFO] Notebook progress message.")

    # =============================================================================
    dfo_full = df["flooded_any_full"].astype(int)
    metrics_full = compute_contingency_and_skill(cama_any, dfo_full)
    print_skill_report("[INFO] Notebook progress message.", metrics_full)

    grp_full = df.groupby("city_code", as_index=False).agg(
        cama_any_freq=("cama_any_event", "mean"),
        dfo_any_freq_full=("flooded_any_full", "mean"),
    )
    corr_full = grp_full["cama_any_freq"].corr(grp_full["dfo_any_freq_full"])
    print("[INFO] Notebook progress message.")

    out_full = os.path.join(
        OUT_DIR, "city_freq_CaMaAny_vs_DFOAny_full.csv"
    )
    grp_full.to_csv(out_full, index=False)
    print("[INFO] Notebook progress message.")

    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 8
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 01_city_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import numpy as np
import pandas as pd

# =============================================================================

BASE_DIR = "/home/ll/jupyter_notebook"

# CaMa-Flood processing note.
CAMA_DIR = os.path.join(BASE_DIR, "result/impact_assessment/older")
CAMA_CSV = os.path.join(
    CAMA_DIR,
    "city_flood_events_T2_5_10_20_50_100_1980_2020.csv"
)

# External flood dataset comparison note.
DFO_DIR = os.path.join(BASE_DIR, "result/impact_assessment/older/DFO_city")
DFO_PARQ = os.path.join(
    DFO_DIR,
    "dfo_city_year_1980_2020_all_sev.parquet"
)

# Original notebook comment normalized for the public code archive.
YEAR_MIN = 1985
YEAR_MAX = 2020

# Original notebook comment normalized for the public code archive.
OUT_DIR = os.path.join(
    BASE_DIR,
    f"result/impact_assessment/older/compare_DFO_all_events_{YEAR_MIN}_{YEAR_MAX}"
)
os.makedirs(OUT_DIR, exist_ok=True)


# =============================================================================

def load_cama_events(path: str) -> pd.DataFrame:
    """Archived notebook note for 01_city_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = pd.read_csv(path, dtype={"city_code": str})

    # Original notebook comment normalized for the public code archive.
    cama_cols = [c for c in df.columns if c.startswith("flood_ge_T")]
    if not cama_cols:
        raise RuntimeError("未在 CaMa CSV 中找到 flood_ge_T* 列，请检查输入文件。")

    # Original notebook comment normalized for the public code archive.
    for c in cama_cols:
        df[c] = df[c].astype(int)

    # CaMa-Flood processing note.
    df["cama_any_event"] = (df[cama_cols].max(axis=1) > 0).astype(int)

    # Original notebook comment normalized for the public code archive.
    keep = ["year", "city_code", "cama_any_event"] + cama_cols
    df = df[keep]

    return df


def load_dfo_panel(path: str) -> pd.DataFrame:
    """Archived notebook note for 01_city_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = pd.read_parquet(path)
    df["city_code"] = df["city_code"].astype(str)

    # Original notebook comment normalized for the public code archive.
    needed = ["flooded_any_centroid", "flooded_any_area50", "flooded_any_full"]
    for c in needed:
        if c not in df.columns:
            raise RuntimeError(f"DFO 表中缺少列: {c}")
        df[c] = df[c].astype(int)

    keep = ["year", "city_code"] + needed
    return df[keep]


# =============================================================================

def compute_contingency_and_skill(
    cama_flag: pd.Series,
    dfo_flag: pd.Series,
) -> dict:
    """Archived notebook note for 01_city_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    cama = cama_flag.astype(int).values
    dfo = dfo_flag.astype(int).values

    hits         = int(((cama == 1) & (dfo == 1)).sum())
    misses       = int(((cama == 0) & (dfo == 1)).sum())
    false_alarms = int(((cama == 1) & (dfo == 0)).sum())
    correct_neg  = int(((cama == 0) & (dfo == 0)).sum())

    H, M, F, C = hits, misses, false_alarms, correct_neg
    TOT = H + M + F + C

    pod = H / (H + M) if (H + M) > 0 else np.nan          # Probability of Detection
    far = F / (H + F) if (H + F) > 0 else np.nan          # False Alarm Ratio
    pofd = F / (F + C) if (F + C) > 0 else np.nan         # Probability of False Detection
    csi = H / (H + M + F) if (H + M + F) > 0 else np.nan  # Critical Success Index

    # External flood dataset comparison note.
    freq_cama = (H + F) / TOT if TOT > 0 else np.nan
    freq_dfo  = (H + M) / TOT if TOT > 0 else np.nan
    bias = freq_cama / freq_dfo if (freq_cama >= 0 and freq_dfo > 0) else np.nan

    # Heidke Skill Score (HSS)
    denom_hss = (H + M) * (M + C) + (H + F) * (F + C)
    hss = (2 * (H * C - F * M) / denom_hss) if denom_hss > 0 else np.nan

    # Equitable Threat Score (ETS)
    if TOT > 0:
        h_random = (H + M) * (H + F) / TOT
        denom_ets = (H + M + F - h_random)
        ets = (H - h_random) / denom_ets if denom_ets > 0 else np.nan
    else:
        ets = np.nan

    return {
        "H": H,
        "M": M,
        "F": F,
        "C": C,
        "POD": pod,
        "FAR": far,
        "POFD": pofd,
        "CSI": csi,
        "Bias": bias,
        "HSS": hss,
        "ETS": ets,
        "freq_cama": freq_cama,
        "freq_dfo": freq_dfo,
        "TOT": TOT,
    }


def print_skill_report(label: str, metrics: dict):
    """Archived notebook note for 01_city_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print("\n" + "=" * 72)
    print("[INFO] Notebook progress message.")
    print("-" * 72)
    print("[INFO] Notebook progress message.")
    print(f"Hits         (1,1): {metrics['H']}")
    print(f"Misses       (0,1): {metrics['M']}")
    print(f"False alarms (1,0): {metrics['F']}")
    print(f"Correct neg  (0,0): {metrics['C']}")
    print("-" * 72)
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print(f"HSS  (Heidke Skill Score)     = {metrics['HSS']:.3f}")
    print(f"ETS  (Equitable Threat Score) = {metrics['ETS']:.3f}")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")


# =============================================================================

def main():
    print("[INFO] Notebook progress message.")
    df_cama = load_cama_events(CAMA_CSV)

    print("[INFO] Notebook progress message.")
    df_dfo = load_dfo_panel(DFO_PARQ)

    print("[INFO] Notebook progress message.")
    df = df_cama.merge(
        df_dfo,
        on=["city_code", "year"],
        how="inner",
        suffixes=("_cama", "_dfo")
    )
    print("[INFO] Notebook progress message.", df.shape)

    # =============================================================================
    df = df[(df["year"] >= YEAR_MIN) & (df["year"] <= YEAR_MAX)].copy()
    print("[INFO] Notebook progress message.", df.shape)

    cama_any = df["cama_any_event"].astype(int)

    # =============================================================================
    dfo_centroid = df["flooded_any_centroid"].astype(int)

    metrics_cent = compute_contingency_and_skill(cama_any, dfo_centroid)
    print_skill_report("[INFO] Notebook progress message.", metrics_cent)

    # Original notebook comment normalized for the public code archive.
    grp_cent = df.groupby("city_code", as_index=False).agg(
        cama_any_freq=("cama_any_event", "mean"),
        dfo_any_freq_centroid=("flooded_any_centroid", "mean"),
    )
    corr_cent = grp_cent["cama_any_freq"].corr(grp_cent["dfo_any_freq_centroid"])
    print("[INFO] Notebook progress message.")

    out_cent = os.path.join(
        OUT_DIR,
        f"city_freq_CaMaAny_vs_DFOAny_centroid_{YEAR_MIN}_{YEAR_MAX}.csv"
    )
    grp_cent.to_csv(out_cent, index=False)
    print("[INFO] Notebook progress message.")

    # =============================================================================
    dfo_area50 = df["flooded_any_area50"].astype(int)
    metrics_a50 = compute_contingency_and_skill(cama_any, dfo_area50)
    print_skill_report("[INFO] Notebook progress message.", metrics_a50)

    grp_a50 = df.groupby("city_code", as_index=False).agg(
        cama_any_freq=("cama_any_event", "mean"),
        dfo_any_freq_area50=("flooded_any_area50", "mean"),
    )
    corr_a50 = grp_a50["cama_any_freq"].corr(grp_a50["dfo_any_freq_area50"])
    print("[INFO] Notebook progress message.")

    out_a50 = os.path.join(
        OUT_DIR,
        f"city_freq_CaMaAny_vs_DFOAny_area50_{YEAR_MIN}_{YEAR_MAX}.csv"
    )
    grp_a50.to_csv(out_a50, index=False)
    print("[INFO] Notebook progress message.")

    # =============================================================================
    dfo_full = df["flooded_any_full"].astype(int)
    metrics_full = compute_contingency_and_skill(cama_any, dfo_full)
    print_skill_report("[INFO] Notebook progress message.", metrics_full)

    grp_full = df.groupby("city_code", as_index=False).agg(
        cama_any_freq=("cama_any_event", "mean"),
        dfo_any_freq_full=("flooded_any_full", "mean"),
    )
    corr_full = grp_full["cama_any_freq"].corr(grp_full["dfo_any_freq_full"])
    print("[INFO] Notebook progress message.")

    out_full = os.path.join(
        OUT_DIR,
        f"city_freq_CaMaAny_vs_DFOAny_full_{YEAR_MIN}_{YEAR_MAX}.csv"
    )
    grp_full.to_csv(out_full, index=False)
    print("[INFO] Notebook progress message.")

    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 11
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 01_city_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import numpy as np
import pandas as pd

# =============================================================================

BASE_DIR = "/home/ll/jupyter_notebook"

# CaMa-Flood processing note.
CAMA_DIR = os.path.join(BASE_DIR, "result/impact_assessment/older")
CAMA_CSV = os.path.join(
    CAMA_DIR,
    "city_flood_events_T2_5_10_20_50_100_1980_2020.csv"
)

# External flood dataset comparison note.
DFO_DIR = os.path.join(BASE_DIR, "result/impact_assessment/older/DFO_city")
DFO_PARQ = os.path.join(
    DFO_DIR,
    "dfo_city_year_1980_2020_all_sev.parquet"
)

# Original notebook comment normalized for the public code archive.
YEAR_MIN = 1985
YEAR_MAX = 2020

# Original notebook comment normalized for the public code archive.
OUT_DIR = os.path.join(
    BASE_DIR,
    f"result/impact_assessment/older/compare_DFO_all_events_{YEAR_MIN}_{YEAR_MAX}"
)
os.makedirs(OUT_DIR, exist_ok=True)


# =============================================================================

def load_cama_events(path: str) -> pd.DataFrame:
    """Archived notebook note for 01_city_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = pd.read_csv(path, dtype={"city_code": str})

    # Original notebook comment normalized for the public code archive.
    cama_cols = [c for c in df.columns if c.startswith("flood_ge_T")]
    if not cama_cols:
        raise RuntimeError("未在 CaMa CSV 中找到 flood_ge_T* 列，请检查输入文件。")

    # Original notebook comment normalized for the public code archive.
    for c in cama_cols:
        df[c] = df[c].astype(int)

    # CaMa-Flood processing note.
    df["cama_any_event"] = (df[cama_cols].max(axis=1) > 0).astype(int)

    # Original notebook comment normalized for the public code archive.
    keep = ["year", "city_code", "cama_any_event"] + cama_cols
    df = df[keep]

    return df


def load_dfo_panel(path: str) -> pd.DataFrame:
    """Archived notebook note for 01_city_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = pd.read_parquet(path)
    df["city_code"] = df["city_code"].astype(str)

    # Original notebook comment normalized for the public code archive.
    needed = ["flooded_any_centroid", "flooded_any_area50", "flooded_any_full"]
    for c in needed:
        if c not in df.columns:
            raise RuntimeError(f"DFO 表中缺少列: {c}")
        df[c] = df[c].astype(int)

    keep = ["year", "city_code"] + needed
    return df[keep]


# =============================================================================

def compute_contingency_and_skill(
    cama_flag: pd.Series,
    dfo_flag: pd.Series,
) -> dict:
    """Archived notebook note for 01_city_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    cama = cama_flag.astype(int).values
    dfo = dfo_flag.astype(int).values

    hits         = int(((cama == 1) & (dfo == 1)).sum())
    misses       = int(((cama == 0) & (dfo == 1)).sum())
    false_alarms = int(((cama == 1) & (dfo == 0)).sum())
    correct_neg  = int(((cama == 0) & (dfo == 0)).sum())

    H, M, F, C = hits, misses, false_alarms, correct_neg
    TOT = H + M + F + C

    pod = H / (H + M) if (H + M) > 0 else np.nan          # Probability of Detection
    far = F / (H + F) if (H + F) > 0 else np.nan          # False Alarm Ratio
    pofd = F / (F + C) if (F + C) > 0 else np.nan         # Probability of False Detection
    csi = H / (H + M + F) if (H + M + F) > 0 else np.nan  # Critical Success Index

    # External flood dataset comparison note.
    freq_cama = (H + F) / TOT if TOT > 0 else np.nan
    freq_dfo  = (H + M) / TOT if TOT > 0 else np.nan
    bias = freq_cama / freq_dfo if (freq_cama >= 0 and freq_dfo > 0) else np.nan

    # Heidke Skill Score (HSS)
    denom_hss = (H + M) * (M + C) + (H + F) * (F + C)
    hss = (2 * (H * C - F * M) / denom_hss) if denom_hss > 0 else np.nan

    # Equitable Threat Score (ETS)
    if TOT > 0:
        h_random = (H + M) * (H + F) / TOT
        denom_ets = (H + M + F - h_random)
        ets = (H - h_random) / denom_ets if denom_ets > 0 else np.nan
    else:
        ets = np.nan

    return {
        "H": H,
        "M": M,
        "F": F,
        "C": C,
        "POD": pod,
        "FAR": far,
        "POFD": pofd,
        "CSI": csi,
        "Bias": bias,
        "HSS": hss,
        "ETS": ets,
        "freq_cama": freq_cama,
        "freq_dfo": freq_dfo,
        "TOT": TOT,
    }


def print_skill_report(label: str, metrics: dict):
    """Archived notebook note for 01_city_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print("\n" + "=" * 72)
    print("[INFO] Notebook progress message.")
    print("-" * 72)
    print("[INFO] Notebook progress message.")
    print(f"Hits         (1,1): {metrics['H']}")
    print(f"Misses       (0,1): {metrics['M']}")
    print(f"False alarms (1,0): {metrics['F']}")
    print(f"Correct neg  (0,0): {metrics['C']}")
    print("-" * 72)
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print(f"HSS  (Heidke Skill Score)     = {metrics['HSS']:.3f}")
    print(f"ETS  (Equitable Threat Score) = {metrics['ETS']:.3f}")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")


# =============================================================================

def main():
    print("[INFO] Notebook progress message.")
    df_cama = load_cama_events(CAMA_CSV)

    print("[INFO] Notebook progress message.")
    df_dfo = load_dfo_panel(DFO_PARQ)

    print("[INFO] Notebook progress message.")
    df = df_cama.merge(
        df_dfo,
        on=["city_code", "year"],
        how="inner",
        suffixes=("_cama", "_dfo")
    )
    print("[INFO] Notebook progress message.", df.shape)

    # =============================================================================
    df = df[(df["year"] >= YEAR_MIN) & (df["year"] <= YEAR_MAX)].copy()
    print("[INFO] Notebook progress message.", df.shape)

    # CaMa-Flood processing note.
    cama_any = df["cama_any_event"].astype(int)

    # =============================================================================
    dfo_centroid = df["flooded_any_centroid"].astype(int)

    # Original notebook comment normalized for the public code archive.
    metrics_cent = compute_contingency_and_skill(cama_any, dfo_centroid)
    print_skill_report("[INFO] Notebook progress message.", metrics_cent)

    # Original notebook comment normalized for the public code archive.
    grp_cent = df.groupby("city_code", as_index=False).agg(
        cama_any_freq=("cama_any_event", "mean"),
        dfo_any_freq_centroid=("flooded_any_centroid", "mean"),
    )
    corr_cent = grp_cent["cama_any_freq"].corr(grp_cent["dfo_any_freq_centroid"])
    print("[INFO] Notebook progress message.")

    out_cent = os.path.join(
        OUT_DIR,
        f"city_freq_CaMaAny_vs_DFOAny_centroid_{YEAR_MIN}_{YEAR_MAX}.csv"
    )
    grp_cent.to_csv(out_cent, index=False)
    print("[INFO] Notebook progress message.")

    # =============================================================================
    # External flood dataset comparison note.
    missed = df[(df["cama_any_event"] == 0) & (df["flooded_any_centroid"] == 1)].copy()
    print("[INFO] Notebook progress message.")

    if not missed.empty:
        # Original notebook comment normalized for the public code archive.
        miss_by_year = (
            missed.groupby("year")
            .size()
            .reset_index(name="n_miss")
            .sort_values("year")
        )

        print("\n[Missed events by year] DFO=1 & CaMa=0（centroid）")
        for _, row in miss_by_year.iterrows():
            print(f"  Year {int(row['year'])}: {int(row['n_miss'])} city-year(s)")

        # Original notebook comment normalized for the public code archive.
        missed_list = (
            missed[["city_code", "year"]]
            .drop_duplicates()
            .sort_values(["year", "city_code"])
        )

        print("[INFO] Notebook progress message.")
        print(missed_list.head(20).to_string(index=False))  # Original notebook comment normalized for the public code archive.

        # City-level processing note.
        missed_csv = os.path.join(
            OUT_DIR,
            f"missed_events_city_year_centroid_{YEAR_MIN}_{YEAR_MAX}.csv"
        )
        missed_list.to_csv(missed_csv, index=False)
        print("[INFO] Notebook progress message.")
    else:
        print("[INFO] Notebook progress message.")

    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 20
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 01_city_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

# =============================================================================

BASE_DIR = "/home/ll/jupyter_notebook"

CAMA_CSV = os.path.join(
    BASE_DIR,
    "result/impact_assessment/older/city_flood_events_T2_5_10_20_50_100_1980_2020.csv"
)
DFO_PARQ = os.path.join(
    BASE_DIR,
    "result/impact_assessment/older/DFO_city/dfo_city_year_1980_2020_all_sev.parquet"
)
CITY_SHP = os.path.join(
    BASE_DIR,
    "gis_data/China/city/city.shp"
)
CITY_ID_FIELD = "市代码"

OUT_DIR = os.path.join(
    BASE_DIR,
    "result/impact_assessment/older/fig_CaMa_DFO_hits_DFOactive"
)
os.makedirs(OUT_DIR, exist_ok=True)

# Original notebook comment normalized for the public code archive.
YEAR_MIN = 1985
YEAR_MAX = 2020
SPATIAL_DEF = "centroid"   # Original notebook comment normalized for the public code archive.
DFO_COL = f"flooded_any_{SPATIAL_DEF}"

# External flood dataset comparison note.
ONLY_DFO_ACTIVE = True


# =============================================================================

def load_cama_events(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, dtype={"city_code": str})
    cama_cols = [c for c in df.columns if c.startswith("flood_ge_T")]
    for c in cama_cols:
        df[c] = df[c].astype(int)
    df["cama_any_event"] = (df[cama_cols].max(axis=1) > 0).astype(int)
    return df[["year", "city_code", "cama_any_event"] + cama_cols]


def load_dfo_panel(path: str) -> pd.DataFrame:
    df = pd.read_parquet(path)
    df["city_code"] = df["city_code"].astype(str)
    if DFO_COL not in df.columns:
        raise RuntimeError(f"DFO 表中缺少列: {DFO_COL}")
    df[DFO_COL] = df[DFO_COL].astype(int)
    return df[["year", "city_code", DFO_COL]]


def merge_cama_dfo():
    df_cama = load_cama_events(CAMA_CSV)
    df_dfo = load_dfo_panel(DFO_PARQ)

    df = df_cama.merge(df_dfo, on=["city_code", "year"], how="inner")

    # Original notebook comment normalized for the public code archive.
    df = df[(df["year"] >= YEAR_MIN) & (df["year"] <= YEAR_MAX)].copy()
    print("[INFO] Notebook progress message.")

    # External flood dataset comparison note.
    if ONLY_DFO_ACTIVE:
        s = df.groupby("city_code")[DFO_COL].sum()
        active_cities = s[s > 0].index
        df = df[df["city_code"].isin(active_cities)].copy()
        print("[INFO] Notebook progress message.")
        print("[INFO] Notebook progress message.")

    return df


# =============================================================================

def classify_cases(df: pd.DataFrame) -> pd.DataFrame:
    cama = df["cama_any_event"].astype(int)
    dfo = df[DFO_COL].astype(int)

    conditions = [
        (cama == 1) & (dfo == 1),
        (cama == 0) & (dfo == 1),
        (cama == 1) & (dfo == 0),
        (cama == 0) & (dfo == 0),
    ]
    choices = ["hit", "miss", "false_alarm", "correct_neg"]
    df["case_type"] = np.select(conditions, choices, default="unknown")
    return df


# =============================================================================

def load_city_gdf(active_city_codes: pd.Index) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(CITY_SHP)
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)
    gdf["city_code"] = gdf[CITY_ID_FIELD].astype(str)

    # External flood dataset comparison note.
    gdf = gdf[gdf["city_code"].isin(active_city_codes)].copy()
    print("[INFO] Notebook progress message.")
    return gdf


# =============================================================================

def plot_case_map_for_year(df_all: pd.DataFrame, gdf_city: gpd.GeoDataFrame,
                           year_sel: int):
    df_y = df_all[df_all["year"] == year_sel].copy()
    if df_y.empty:
        print("[INFO] Notebook progress message.")
        return

    gdf = gdf_city.merge(
        df_y[["city_code", "case_type"]],
        on="city_code",
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
        f"CaMa vs DFO ({SPATIAL_DEF}), {year_sel}\n"
        "仅 DFO-active 市：hit=CaMa&DFO; miss=DFO only; false_alarm=CaMa only",
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
        OUT_DIR, f"map_case_{SPATIAL_DEF}_{year_sel}_DFOactive.png"
    )
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    print("[INFO] Notebook progress message.")


# =============================================================================

def compute_city_hit_false_rates(df_all: pd.DataFrame) -> pd.DataFrame:
    df = df_all.copy()
    df["H"] = (df["case_type"] == "hit").astype(int)
    df["M"] = (df["case_type"] == "miss").astype(int)
    df["F"] = (df["case_type"] == "false_alarm").astype(int)
    df["C"] = (df["case_type"] == "correct_neg").astype(int)

    grp = df.groupby("city_code", as_index=False).agg(
        H=("H", "sum"),
        M=("M", "sum"),
        F=("F", "sum"),
        C=("C", "sum"),
    )

    grp["hit_rate_DFOyears"] = grp["H"] / (grp["H"] + grp["M"])
    grp.loc[(grp["H"] + grp["M"]) == 0, "hit_rate_DFOyears"] = np.nan  # External flood dataset comparison note.

    grp["false_alarm_rate_CAMAYears"] = grp["F"] / (grp["H"] + grp["F"])
    grp.loc[(grp["H"] + grp["F"]) == 0, "false_alarm_rate_CAMAYears"] = np.nan  # CaMa-Flood processing note.

    return grp


def plot_rate_map(gdf_city: gpd.GeoDataFrame, df_rates: pd.DataFrame,
                  col: str, vmin=0.0, vmax=1.0, title="", fname=""):
    gdf = gdf_city.merge(df_rates[["city_code", col]], on="city_code", how="left")

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


# =============================================================================

def plot_rate_histogram(df_rates: pd.DataFrame, col: str,
                        bins: int = 20, title: str = "", fname: str = ""):
    """Archived notebook note for 01_city_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    data = df_rates[col].dropna().values
    if data.size == 0:
        print("[INFO] Notebook progress message.")
        return

    fig, ax = plt.subplots(1, 1, figsize=(6, 4))
    ax.hist(data, bins=bins, edgecolor="black")

    ax.set_xlabel(col)
    ax.set_ylabel("Number of cities")
    ax.set_title(title, fontsize=11)

    fig.tight_layout()
    out_png = os.path.join(OUT_DIR, fname)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    print("[INFO] Notebook progress message.")


# =============================================================================

def main():
    print("[INFO] Notebook progress message.")
    df = merge_cama_dfo()
    df = classify_cases(df)

    # External flood dataset comparison note.
    active_city_codes = df["city_code"].unique()

    print("[INFO] Notebook progress message.")
    gdf_city = load_city_gdf(active_city_codes)

    # =============================================================================
    year_example = 1998  # Original notebook comment normalized for the public code archive.
    print("[INFO] Notebook progress message.")
    plot_case_map_for_year(df, gdf_city, year_example)

    # =============================================================================
    print("[INFO] Notebook progress message.")
    df_rates = compute_city_hit_false_rates(df)

    # Original notebook comment normalized for the public code archive.
    plot_rate_map(
        gdf_city,
        df_rates,
        col="hit_rate_DFOyears",
        vmin=0.0,
        vmax=1.0,
        title=f"CaMa 对 DFO 事件命中率 H/(H+M)\n"
              f"{YEAR_MIN}-{YEAR_MAX}, {SPATIAL_DEF}, 仅 DFO-active 市",
        fname=f"map_hit_rate_{SPATIAL_DEF}_{YEAR_MIN}_{YEAR_MAX}_DFOactive.png"
    )

    plot_rate_map(
        gdf_city,
        df_rates,
        col="false_alarm_rate_CAMAYears",
        vmin=0.0,
        vmax=1.0,
        title=f"CaMa 空报率 F/(H+F)\n"
              f"{YEAR_MIN}-{YEAR_MAX}, {SPATIAL_DEF}, 仅 DFO-active 市",
        fname=f"map_false_alarm_rate_{SPATIAL_DEF}_{YEAR_MIN}_{YEAR_MAX}_DFOactive.png"
    )

    # Original notebook comment normalized for the public code archive.
    plot_rate_histogram(
        df_rates,
        col="hit_rate_DFOyears",
        bins=20,
        title=f"CaMa 命中率分布 H/(H+M)\n{YEAR_MIN}-{YEAR_MAX}, {SPATIAL_DEF}, 仅 DFO-active 市",
        fname=f"hist_hit_rate_{SPATIAL_DEF}_{YEAR_MIN}_{YEAR_MAX}_DFOactive.png"
    )

    plot_rate_histogram(
        df_rates,
        col="false_alarm_rate_CAMAYears",
        bins=20,
        title=f"CaMa 空报率分布 F/(H+F)\n{YEAR_MIN}-{YEAR_MAX}, {SPATIAL_DEF}, 仅 DFO-active 市",
        fname=f"hist_false_alarm_rate_{SPATIAL_DEF}_{YEAR_MIN}_{YEAR_MAX}_DFOactive.png"
    )

    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 22
# ------------------------------------------------------------------------------
# Notebook-export prose note omitted from the public code archive.
# Notebook-export prose note omitted from the public code archive.


# ------------------------------------------------------------------------------
# Notebook cell 23
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 01_city_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

# =============================================================================

BASE_DIR = "/home/ll/jupyter_notebook"

CAMA_CSV = os.path.join(
    BASE_DIR,
    "result/impact_assessment/older/city_flood_events_T2_5_10_20_50_100_1980_2020.csv"
)
DFO_PARQ = os.path.join(
    BASE_DIR,
    "result/impact_assessment/older/DFO_city/dfo_city_year_1980_2020_all_sev.parquet"
)
CITY_SHP = os.path.join(
    BASE_DIR,
    "gis_data/China/city/city.shp"
)
CITY_ID_FIELD = "市代码"

OUT_DIR = os.path.join(
    BASE_DIR,
    "result/impact_assessment/older/fig_CaMa_DFO_hits_DFOactive"
)
os.makedirs(OUT_DIR, exist_ok=True)

# Original notebook comment normalized for the public code archive.
YEAR_MIN = 1985
YEAR_MAX = 2020
SPATIAL_DEF = "centroid"   # Original notebook comment normalized for the public code archive.
DFO_COL = f"flooded_any_{SPATIAL_DEF}"

# External flood dataset comparison note.
ONLY_DFO_ACTIVE = True


# =============================================================================

def load_cama_events(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, dtype={"city_code": str})
    cama_cols = [c for c in df.columns if c.startswith("flood_ge_T")]
    for c in cama_cols:
        df[c] = df[c].astype(int)
    df["cama_any_event"] = (df[cama_cols].max(axis=1) > 0).astype(int)
    return df[["year", "city_code", "cama_any_event"] + cama_cols]


def load_dfo_panel(path: str) -> pd.DataFrame:
    df = pd.read_parquet(path)
    df["city_code"] = df["city_code"].astype(str)
    if DFO_COL not in df.columns:
        raise RuntimeError(f"DFO 表中缺少列: {DFO_COL}")
    df[DFO_COL] = df[DFO_COL].astype(int)
    return df[["year", "city_code", DFO_COL]]


def merge_cama_dfo():
    df_cama = load_cama_events(CAMA_CSV)
    df_dfo = load_dfo_panel(DFO_PARQ)

    df = df_cama.merge(df_dfo, on=["city_code", "year"], how="inner")

    # Original notebook comment normalized for the public code archive.
    df = df[(df["year"] >= YEAR_MIN) & (df["year"] <= YEAR_MAX)].copy()
    print("[INFO] Notebook progress message.")

    # External flood dataset comparison note.
    if ONLY_DFO_ACTIVE:
        s = df.groupby("city_code")[DFO_COL].sum()
        active_cities = s[s > 0].index
        df = df[df["city_code"].isin(active_cities)].copy()
        print("[INFO] Notebook progress message.")
        print("[INFO] Notebook progress message.")

    return df


# =============================================================================

def classify_cases(df: pd.DataFrame) -> pd.DataFrame:
    cama = df["cama_any_event"].astype(int)
    dfo = df[DFO_COL].astype(int)

    conditions = [
        (cama == 1) & (dfo == 1),
        (cama == 0) & (dfo == 1),
        (cama == 1) & (dfo == 0),
        (cama == 0) & (dfo == 0),
    ]
    choices = ["hit", "miss", "false_alarm", "correct_neg"]
    df["case_type"] = np.select(conditions, choices, default="unknown")
    return df


# =============================================================================

def load_city_gdf(active_city_codes: pd.Index) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(CITY_SHP)
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)
    gdf["city_code"] = gdf[CITY_ID_FIELD].astype(str)

    # External flood dataset comparison note.
    gdf = gdf[gdf["city_code"].isin(active_city_codes)].copy()
    print("[INFO] Notebook progress message.")
    return gdf


# =============================================================================

def plot_case_map_for_year(df_all: pd.DataFrame, gdf_city: gpd.GeoDataFrame,
                           year_sel: int):
    df_y = df_all[df_all["year"] == year_sel].copy()
    if df_y.empty:
        print("[INFO] Notebook progress message.")
        return

    gdf = gdf_city.merge(
        df_y[["city_code", "case_type"]],
        on="city_code",
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
        f"CaMa vs DFO ({SPATIAL_DEF}), {year_sel}\n"
        "仅 DFO-active 市：hit=CaMa&DFO; miss=DFO only; false_alarm=CaMa only",
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
        OUT_DIR, f"map_case_{SPATIAL_DEF}_{year_sel}_DFOactive.png"
    )
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    print("[INFO] Notebook progress message.")


# =============================================================================

def compute_city_hit_false_rates(df_all: pd.DataFrame) -> pd.DataFrame:
    df = df_all.copy()
    df["H"] = (df["case_type"] == "hit").astype(int)
    df["M"] = (df["case_type"] == "miss").astype(int)
    df["F"] = (df["case_type"] == "false_alarm").astype(int)
    df["C"] = (df["case_type"] == "correct_neg").astype(int)

    grp = df.groupby("city_code", as_index=False).agg(
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


# =============================================================================

def plot_two_rates_centroid_map(gdf_city: gpd.GeoDataFrame,
                                df_rates: pd.DataFrame,
                                col1: str,
                                col2: str,
                                title: str = "",
                                fname: str = "",
                                size_min: float = 10,
                                size_max: float = 80,
                                offset_deg: float = 0.25):
    """Archived notebook note for 01_city_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    gdf = gdf_city.merge(df_rates[["city_code", col1, col2]], on="city_code", how="left")

    # Original notebook comment normalized for the public code archive.
    centroids = gdf.geometry.centroid
    x = centroids.x.values
    y = centroids.y.values
    v1 = gdf[col1].values.astype(float)
    v2 = gdf[col2].values.astype(float)

    def scale_size(v):
        v = np.array(v, dtype=float)
        v[np.isnan(v)] = np.nan
        v_min = np.nanmin(v)
        v_max = np.nanmax(v)
        if not np.isfinite(v_min) or v_max == v_min:
            return np.full_like(v, (size_min + size_max) / 2.0)
        v_norm = (v - v_min) / (v_max - v_min)
        return size_min + v_norm * (size_max - size_min)

    s1 = scale_size(v1)
    s2 = scale_size(v2)

    fig, ax = plt.subplots(1, 1, figsize=(8, 7))

    # Original notebook comment normalized for the public code archive.
    gdf_city.boundary.plot(ax=ax, linewidth=0.5, edgecolor="lightgrey")

    # Original notebook comment normalized for the public code archive.
    mask1 = ~np.isnan(v1)
    mask2 = ~np.isnan(v2)

    sc1 = ax.scatter(
        x[mask1] - offset_deg,
        y[mask1],
        s=s1[mask1],
        color="red",
        alpha=0.7,
        edgecolors="black",
        linewidths=0.2,
        label="Hit rate"
    )

    sc2 = ax.scatter(
        x[mask2] + offset_deg,
        y[mask2],
        s=s2[mask2],
        color="blue",
        alpha=0.7,
        edgecolors="black",
        linewidths=0.2,
        label="False alarm rate"
    )

    ax.set_title(title, fontsize=11)
    ax.set_axis_off()

    # Original notebook comment normalized for the public code archive.
    ax.legend(loc="lower left", fontsize=9, frameon=True)

    fig.tight_layout()
    out_png = os.path.join(OUT_DIR, fname)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    print("[INFO] Notebook progress message.")


# =============================================================================

def plot_rate_hist_stacked(df_rates: pd.DataFrame,
                           col1: str,
                           col2: str,
                           bins: int = 20,
                           title: str = "",
                           fname: str = ""):
    """Archived notebook note for 01_city_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    data1 = df_rates[col1].dropna().values
    data2 = df_rates[col2].dropna().values

    if (data1.size == 0) or (data2.size == 0):
        print("[INFO] Notebook progress message.")
        return

    mean1 = data1.mean()
    mean2 = data2.mean()

    # Original notebook comment normalized for the public code archive.
    bins_edges = np.linspace(0.0, 1.0, bins + 1)
    counts1, edges = np.histogram(data1, bins=bins_edges)
    counts2, _ = np.histogram(data2, bins=bins_edges)

    centers = (edges[:-1] + edges[1:]) / 2.0
    width = edges[1] - edges[0]

    fig, ax = plt.subplots(1, 1, figsize=(7, 4))

    # Original notebook comment normalized for the public code archive.
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

    # Original notebook comment normalized for the public code archive.
    ax.axvline(mean1, linestyle="--", linewidth=1.5, color="red",
               label=f"Hit mean = {mean1:.2f}")
    ax.axvline(mean2, linestyle="--", linewidth=1.5, color="blue",
               label=f"False mean = {mean2:.2f}")

    ax.set_xlim(0.0, 1.0)
    ax.set_xlabel("Rate")
    ax.set_ylabel("Number of cities")
    ax.set_title(title, fontsize=11)

    # Original notebook comment normalized for the public code archive.
    handles, labels = ax.get_legend_handles_labels()
    # Original notebook comment normalized for the public code archive.
    unique = dict(zip(labels, handles))
    ax.legend(unique.values(), unique.keys(), fontsize=8, frameon=True, loc="upper right")

    fig.tight_layout()
    out_png = os.path.join(OUT_DIR, fname)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    print("[INFO] Notebook progress message.")


# =============================================================================

def main():
    print("[INFO] Notebook progress message.")
    df = merge_cama_dfo()
    df = classify_cases(df)

    # External flood dataset comparison note.
    active_city_codes = df["city_code"].unique()

    print("[INFO] Notebook progress message.")
    gdf_city = load_city_gdf(active_city_codes)

    # =============================================================================
    year_example = 1998
    print("[INFO] Notebook progress message.")
    plot_case_map_for_year(df, gdf_city, year_example)

    # =============================================================================
    print("[INFO] Notebook progress message.")
    df_rates = compute_city_hit_false_rates(df)

    # Original notebook comment normalized for the public code archive.
    plot_two_rates_centroid_map(
        gdf_city,
        df_rates,
        col1="hit_rate_DFOyears",
        col2="false_alarm_rate_CAMAYears",
        title=f"CaMa 命中率与空报率（市质心点，红: 命中率；蓝: 空报率）\n"
              f"{YEAR_MIN}-{YEAR_MAX}, {SPATIAL_DEF}, 仅 DFO-active 市",
        fname=f"map_two_rates_centroid_{SPATIAL_DEF}_{YEAR_MIN}_{YEAR_MAX}_DFOactive.png"
    )

    # Original notebook comment normalized for the public code archive.
    plot_rate_hist_stacked(
        df_rates,
        col1="hit_rate_DFOyears",
        col2="false_alarm_rate_CAMAYears",
        bins=20,
        title=f"CaMa 命中率与空报率分布（堆叠直方图）\n"
              f"{YEAR_MIN}-{YEAR_MAX}, {SPATIAL_DEF}, 仅 DFO-active 市",
        fname=f"hist_stacked_hit_false_{SPATIAL_DEF}_{YEAR_MIN}_{YEAR_MAX}_DFOactive.png"
    )

    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 25
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 01_city_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point

# =============================================================================

BASE_DIR = "/home/ll/jupyter_notebook"

CAMA_CSV = os.path.join(
    BASE_DIR,
    "result/impact_assessment/older/city_flood_events_T2_5_10_20_50_100_1980_2020.csv"
)
DFO_PARQ = os.path.join(
    BASE_DIR,
    "result/impact_assessment/older/DFO_city/dfo_city_year_1980_2020_all_sev.parquet"
)
CITY_SHP = os.path.join(
    BASE_DIR,
    "gis_data/China/city/city.shp"
)
CITY_ID_FIELD = "市代码"

# Original notebook comment normalized for the public code archive.
OUT_DIR = os.path.join(
    BASE_DIR,
    "result/impact_assessment/older/fig_CaMa_DFO_hits_DFOactive"
)
os.makedirs(OUT_DIR, exist_ok=True)

# Original notebook comment normalized for the public code archive.
EXPORT_DIR = os.path.join(
    BASE_DIR,
    "result/windows/验证/市"
)
os.makedirs(EXPORT_DIR, exist_ok=True)

# Original notebook comment normalized for the public code archive.
YEAR_MIN = 1985
YEAR_MAX = 2020
SPATIAL_DEF = "centroid"   # Original notebook comment normalized for the public code archive.
DFO_COL = f"flooded_any_{SPATIAL_DEF}"

# External flood dataset comparison note.
ONLY_DFO_ACTIVE = True


# =============================================================================

def load_cama_events(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, dtype={"city_code": str})
    cama_cols = [c for c in df.columns if c.startswith("flood_ge_T")]
    for c in cama_cols:
        df[c] = df[c].astype(int)
    df["cama_any_event"] = (df[cama_cols].max(axis=1) > 0).astype(int)
    return df[["year", "city_code", "cama_any_event"] + cama_cols]


def load_dfo_panel(path: str) -> pd.DataFrame:
    df = pd.read_parquet(path)
    df["city_code"] = df["city_code"].astype(str)
    if DFO_COL not in df.columns:
        raise RuntimeError(f"DFO 表中缺少列: {DFO_COL}")
    df[DFO_COL] = df[DFO_COL].astype(int)
    return df[["year", "city_code", DFO_COL]]


def merge_cama_dfo() -> pd.DataFrame:
    df_cama = load_cama_events(CAMA_CSV)
    df_dfo = load_dfo_panel(DFO_PARQ)

    df = df_cama.merge(df_dfo, on=["city_code", "year"], how="inner")

    # Original notebook comment normalized for the public code archive.
    df = df[(df["year"] >= YEAR_MIN) & (df["year"] <= YEAR_MAX)].copy()
    print("[INFO] Notebook progress message.")

    # External flood dataset comparison note.
    if ONLY_DFO_ACTIVE:
        s = df.groupby("city_code")[DFO_COL].sum()
        active_cities = s[s > 0].index
        df = df[df["city_code"].isin(active_cities)].copy()
        print("[INFO] Notebook progress message.")
        print("[INFO] Notebook progress message.")

    return df


# =============================================================================

def classify_cases(df: pd.DataFrame) -> pd.DataFrame:
    cama = df["cama_any_event"].astype(int)
    dfo = df[DFO_COL].astype(int)

    conditions = [
        (cama == 1) & (dfo == 1),
        (cama == 0) & (dfo == 1),
        (cama == 1) & (dfo == 0),
        (cama == 0) & (dfo == 0),
    ]
    choices = ["hit", "miss", "false_alarm", "correct_neg"]
    df["case_type"] = np.select(conditions, choices, default="unknown")
    return df


# =============================================================================

def load_city_gdf(active_city_codes: pd.Index) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(CITY_SHP)
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)
    gdf["city_code"] = gdf[CITY_ID_FIELD].astype(str)

    # External flood dataset comparison note.
    gdf = gdf[gdf["city_code"].isin(active_city_codes)].copy()
    print("[INFO] Notebook progress message.")
    return gdf


# =============================================================================

def plot_case_map_for_year(df_all: pd.DataFrame, gdf_city: gpd.GeoDataFrame,
                           year_sel: int):
    df_y = df_all[df_all["year"] == year_sel].copy()
    if df_y.empty:
        print("[INFO] Notebook progress message.")
        return

    gdf = gdf_city.merge(
        df_y[["city_code", "case_type"]],
        on="city_code",
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
        f"CaMa vs DFO ({SPATIAL_DEF}), {year_sel}\n"
        "仅 DFO-active 市：hit=CaMa&DFO; miss=DFO only; false_alarm=CaMa only",
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
        OUT_DIR, f"map_case_{SPATIAL_DEF}_{year_sel}_DFOactive.png"
    )
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    print("[INFO] Notebook progress message.")


# =============================================================================

def compute_city_hit_false_rates(df_all: pd.DataFrame) -> pd.DataFrame:
    df = df_all.copy()
    df["H"] = (df["case_type"] == "hit").astype(int)
    df["M"] = (df["case_type"] == "miss").astype(int)
    df["F"] = (df["case_type"] == "false_alarm").astype(int)
    df["C"] = (df["case_type"] == "correct_neg").astype(int)

    grp = df.groupby("city_code", as_index=False).agg(
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


# =============================================================================

def plot_two_rates_centroid_map(gdf_city: gpd.GeoDataFrame,
                                df_rates: pd.DataFrame,
                                col1: str,
                                col2: str,
                                title: str = "",
                                fname: str = "",
                                size_min: float = 10,
                                size_max: float = 80,
                                offset_deg: float = 0.25):
    """Archived notebook note for 01_city_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    gdf = gdf_city.merge(df_rates[["city_code", col1, col2]], on="city_code", how="left")

    # Original notebook comment normalized for the public code archive.
    centroids = gdf.geometry.centroid
    x = centroids.x.values
    y = centroids.y.values
    v1 = gdf[col1].values.astype(float)
    v2 = gdf[col2].values.astype(float)

    def scale_size(v):
        v = np.array(v, dtype=float)
        v[np.isnan(v)] = np.nan
        v_min = np.nanmin(v)
        v_max = np.nanmax(v)
        if not np.isfinite(v_min) or v_max == v_min:
            return np.full_like(v, (size_min + size_max) / 2.0)
        v_norm = (v - v_min) / (v_max - v_min)
        return size_min + v_norm * (size_max - size_min)

    s1 = scale_size(v1)
    s2 = scale_size(v2)

    fig, ax = plt.subplots(1, 1, figsize=(8, 7))

    # Original notebook comment normalized for the public code archive.
    gdf_city.boundary.plot(ax=ax, linewidth=0.5, edgecolor="lightgrey")

    mask1 = ~np.isnan(v1)
    mask2 = ~np.isnan(v2)

    ax.scatter(
        x[mask1] - offset_deg,
        y[mask1],
        s=s1[mask1],
        color="red",
        alpha=0.7,
        edgecolors="black",
        linewidths=0.2,
        label="Hit rate"
    )

    ax.scatter(
        x[mask2] + offset_deg,
        y[mask2],
        s=s2[mask2],
        color="blue",
        alpha=0.7,
        edgecolors="black",
        linewidths=0.2,
        label="False alarm rate"
    )

    ax.set_title(title, fontsize=11)
    ax.set_axis_off()
    ax.legend(loc="lower left", fontsize=9, frameon=True)

    fig.tight_layout()
    out_png = os.path.join(OUT_DIR, fname)
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    print("[INFO] Notebook progress message.")


# =============================================================================

def plot_rate_hist_stacked(df_rates: pd.DataFrame,
                           col1: str,
                           col2: str,
                           bins: int = 20,
                           title: str = "",
                           fname: str = ""):
    """Archived notebook note for 01_city_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    data1 = df_rates[col1].dropna().values
    data2 = df_rates[col2].dropna().values

    if (data1.size == 0) or (data2.size == 0):
        print("[INFO] Notebook progress message.")
        return

    mean1 = data1.mean()
    mean2 = data2.mean()

    # Original notebook comment normalized for the public code archive.
    bins_edges = np.linspace(0.0, 1.0, bins + 1)
    counts1, edges = np.histogram(data1, bins=bins_edges)
    counts2, _ = np.histogram(data2, bins=bins_edges)

    centers = (edges[:-1] + edges[1:]) / 2.0
    width = edges[1] - edges[0]

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
    ax.set_ylabel("Number of cities")
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

from shapely.geometry import Point  # Original notebook comment normalized for the public code archive.

def export_points_and_hist_data(gdf_city: gpd.GeoDataFrame,
                                df_rates: pd.DataFrame):
    """Archived notebook note for 01_city_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

    # Original notebook comment normalized for the public code archive.
    gdf_poly = gdf_city[["city_code", "geometry"]].merge(
        df_rates[["city_code", "H", "M", "F", "C",
                  "hit_rate_DFOyears", "false_alarm_rate_CAMAYears"]],
        on="city_code",
        how="left"
    )

    def jitter_geoms(geoms, seed: int = 42, scale: float = 0.3):
        """Archived notebook note for 01_city_gumbel_events_vs_dfo.

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

            # Original notebook comment normalized for the public code archive.
            dx = (rng.random() - 0.5) * scale * width
            dy = (rng.random() - 0.5) * scale * height

            c = geom.centroid
            pts.append(Point(c.x + dx, c.y + dy))
        return pts

    # =============================================================================
    hit_attr = gdf_poly[["city_code", "hit_rate_DFOyears"]].copy()
    hit_attr = hit_attr.rename(columns={"hit_rate_DFOyears": "hit_rate"})
    hit_geom = jitter_geoms(gdf_poly.geometry, seed=42, scale=0.3)

    gdf_hit = gpd.GeoDataFrame(
        hit_attr,
        geometry=hit_geom,
        crs=gdf_poly.crs       # Original notebook comment normalized for the public code archive.
    )

    hit_shp = os.path.join(EXPORT_DIR, "city_hit_rate_points.shp")
    gdf_hit.to_file(hit_shp)
    print("[INFO] Notebook progress message.")

    # =============================================================================
    false_attr = gdf_poly[["city_code", "false_alarm_rate_CAMAYears"]].copy()
    false_attr = false_attr.rename(columns={"false_alarm_rate_CAMAYears": "false_rate"})
    false_geom = jitter_geoms(gdf_poly.geometry, seed=123, scale=0.3)

    gdf_false = gpd.GeoDataFrame(
        false_attr,
        geometry=false_geom,
        crs=gdf_poly.crs
    )

    false_shp = os.path.join(EXPORT_DIR, "city_false_rate_points.shp")
    gdf_false.to_file(false_shp)
    print("[INFO] Notebook progress message.")

    # =============================================================================
    hist_df = df_rates[[
        "city_code", "H", "M", "F", "C",
        "hit_rate_DFOyears", "false_alarm_rate_CAMAYears"
    ]].copy()
    hist_csv = os.path.join(EXPORT_DIR, "city_hit_false_rates_for_hist.csv")
    hist_df.to_csv(hist_csv, index=False)
    print("[INFO] Notebook progress message.")


# =============================================================================

def main():
    print("[INFO] Notebook progress message.")
    df = merge_cama_dfo()
    df = classify_cases(df)

    # External flood dataset comparison note.
    active_city_codes = df["city_code"].unique()

    print("[INFO] Notebook progress message.")
    gdf_city = load_city_gdf(active_city_codes)

    # =============================================================================
    year_example = 1998
    print("[INFO] Notebook progress message.")
    plot_case_map_for_year(df, gdf_city, year_example)

    # =============================================================================
    print("[INFO] Notebook progress message.")
    df_rates = compute_city_hit_false_rates(df)

    # Original notebook comment normalized for the public code archive.
    print("[INFO] Notebook progress message.")
    export_points_and_hist_data(gdf_city, df_rates)

    # Original notebook comment normalized for the public code archive.
    plot_two_rates_centroid_map(
        gdf_city,
        df_rates,
        col1="hit_rate_DFOyears",
        col2="false_alarm_rate_CAMAYears",
        title=f"CaMa 命中率与空报率（市质心点，红: 命中率；蓝: 空报率）\n"
              f"{YEAR_MIN}-{YEAR_MAX}, {SPATIAL_DEF}, 仅 DFO-active 市",
        fname=f"map_two_rates_centroid_{SPATIAL_DEF}_{YEAR_MIN}_{YEAR_MAX}_DFOactive.png"
    )

    # Original notebook comment normalized for the public code archive.
    plot_rate_hist_stacked(
        df_rates,
        col1="hit_rate_DFOyears",
        col2="false_alarm_rate_CAMAYears",
        bins=20,
        title=f"CaMa 命中率与空报率分布（堆叠直方图）\n"
              f"{YEAR_MIN}-{YEAR_MAX}, {SPATIAL_DEF}, 仅 DFO-active 市",
        fname=f"hist_stacked_hit_false_{SPATIAL_DEF}_{YEAR_MIN}_{YEAR_MAX}_DFOactive.png"
    )

    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 28
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 01_city_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =============================================================================

BASE_DIR = "/home/ll/jupyter_notebook"

CAMA_CSV = os.path.join(
    BASE_DIR,
    "result/impact_assessment/older/city_flood_events_T2_5_10_20_50_100_1980_2020.csv"
)
DFO_PARQ = os.path.join(
    BASE_DIR,
    "result/impact_assessment/older/DFO_city/dfo_city_year_1980_2020_all_sev.parquet"
)

YEAR_MIN = 1985
YEAR_MAX = 2020

SPATIAL_DEF = "centroid"   # Original notebook comment normalized for the public code archive.
DFO_COL = f"flooded_any_{SPATIAL_DEF}"

# External flood dataset comparison note.
MIN_DFO_YEARS = 3

OUT_DIR = os.path.join(
    BASE_DIR,
    f"result/impact_assessment/older/fig_scatter_POD_{SPATIAL_DEF}_{YEAR_MIN}_{YEAR_MAX}"
)
os.makedirs(OUT_DIR, exist_ok=True)


# =============================================================================

def load_cama_events(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, dtype={"city_code": str})
    cama_cols = [c for c in df.columns if c.startswith("flood_ge_T")]
    if not cama_cols:
        raise RuntimeError("未在 CaMa CSV 中找到 flood_ge_T* 列。")

    for c in cama_cols:
        df[c] = df[c].astype(int)

    df["cama_any_event"] = (df[cama_cols].max(axis=1) > 0).astype(int)
    return df[["year", "city_code", "cama_any_event"]]


def load_dfo_panel(path: str) -> pd.DataFrame:
    df = pd.read_parquet(path)
    df["city_code"] = df["city_code"].astype(str)
    if DFO_COL not in df.columns:
        raise RuntimeError(f"DFO 表中缺少列: {DFO_COL}")
    df[DFO_COL] = df[DFO_COL].astype(int)
    return df[["year", "city_code", DFO_COL]]


def merge_cama_dfo() -> pd.DataFrame:
    df_cama = load_cama_events(CAMA_CSV)
    df_dfo = load_dfo_panel(DFO_PARQ)

    df = df_cama.merge(df_dfo, on=["city_code", "year"], how="inner")
    df = df[(df["year"] >= YEAR_MIN) & (df["year"] <= YEAR_MAX)].copy()
    print("[INFO] Notebook progress message.")

    # External flood dataset comparison note.
    s = df.groupby("city_code")[DFO_COL].sum()
    active_cities = s[s > 0].index
    df = df[df["city_code"].isin(active_cities)].copy()
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")

    return df


# =============================================================================

def compute_city_POD(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    cama = df["cama_any_event"].astype(int)
    dfo = df[DFO_COL].astype(int)

    df["H"] = ((cama == 1) & (dfo == 1)).astype(int)
    df["M"] = ((cama == 0) & (dfo == 1)).astype(int)
    df["F"] = ((cama == 1) & (dfo == 0)).astype(int)
    df["C"] = ((cama == 0) & (dfo == 0)).astype(int)

    grp = df.groupby("city_code", as_index=False).agg(
        H=("H", "sum"),
        M=("M", "sum"),
        F=("F", "sum"),
        C=("C", "sum"),
        N_year=("year", "nunique"),
    )

    grp["DFO_years"] = grp["H"] + grp["M"]      # External flood dataset comparison note.
    grp["CaMa_years"] = grp["H"] + grp["F"]     # CaMa-Flood processing note.

    grp["POD"] = grp["H"] / (grp["H"] + grp["M"])
    grp.loc[grp["DFO_years"] == 0, "POD"] = np.nan  # External flood dataset comparison note.

    grp["freq_DFO"] = grp["DFO_years"] / grp["N_year"]
    grp["freq_CaMa"] = grp["CaMa_years"] / grp["N_year"]

    # External flood dataset comparison note.
    before = grp.shape[0]
    grp = grp[grp["DFO_years"] >= MIN_DFO_YEARS].copy()
    after = grp.shape[0]
    print("[INFO] Notebook progress message.")

    return grp


# =============================================================================

def plot_scatter_POD_vs_freq(grp: pd.DataFrame):
    """Archived notebook note for 01_city_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    # Original notebook comment normalized for the public code archive.
    overall_H = grp["H"].sum()
    overall_M = grp["M"].sum()
    overall_POD = overall_H / (overall_H + overall_M)
    print("[INFO] Notebook progress message.")

    # External flood dataset comparison note.
    fig, ax = plt.subplots(1, 1, figsize=(6, 5))
    ax.scatter(grp["freq_DFO"], grp["POD"], s=20, alpha=0.7)
    ax.axhline(overall_POD, color="red", linestyle="--", linewidth=1.0,
               label=f"overall POD = {overall_POD:.2f}")
    ax.set_xlabel("DFO 事件频率 (年内 DFO=1 年数 / 年数)")
    ax.set_ylabel("POD = H/(H+M)")
    ax.set_title(f"POD vs DFO 事件频率\n{YEAR_MIN}-{YEAR_MAX}, {SPATIAL_DEF}, DFO-active 市")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.legend(loc="lower right", fontsize=8)

    out_png1 = os.path.join(
        OUT_DIR, f"scatter_POD_vs_freqDFO_{SPATIAL_DEF}_{YEAR_MIN}_{YEAR_MAX}.png"
    )
    fig.tight_layout()
    fig.savefig(out_png1, dpi=300)
    plt.close(fig)
    print("[INFO] Notebook progress message.")

    # CaMa-Flood processing note.
    fig, ax = plt.subplots(1, 1, figsize=(6, 5))
    ax.scatter(grp["freq_CaMa"], grp["POD"], s=20, alpha=0.7)
    ax.axhline(overall_POD, color="red", linestyle="--", linewidth=1.0,
               label=f"overall POD = {overall_POD:.2f}")
    ax.set_xlabel("CaMa 事件频率 (年内 CaMa=1 年数 / 年数)")
    ax.set_ylabel("POD = H/(H+M)")
    ax.set_title(f"POD vs CaMa 事件频率\n{YEAR_MIN}-{YEAR_MAX}, {SPATIAL_DEF}, DFO-active 市")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.legend(loc="lower right", fontsize=8)

    out_png2 = os.path.join(
        OUT_DIR, f"scatter_POD_vs_freqCaMa_{SPATIAL_DEF}_{YEAR_MIN}_{YEAR_MAX}.png"
    )
    fig.tight_layout()
    fig.savefig(out_png2, dpi=300)
    plt.close(fig)
    print("[INFO] Notebook progress message.")


# =============================================================================

def main():
    print("[INFO] Notebook progress message.")
    df = merge_cama_dfo()

    print("[INFO] Notebook progress message.")
    grp = compute_city_POD(df)

    # Original notebook comment normalized for the public code archive.
    out_csv = os.path.join(
        OUT_DIR, f"city_POD_stats_{SPATIAL_DEF}_{YEAR_MIN}_{YEAR_MAX}.csv"
    )
    grp.to_csv(out_csv, index=False)
    print("[INFO] Notebook progress message.")

    print("[INFO] Notebook progress message.")
    plot_scatter_POD_vs_freq(grp)

    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 32
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 01_city_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import numpy as np
import pandas as pd

# =============================================================================

BASE_DIR = "/home/ll/jupyter_notebook"

# CaMa-Flood processing note.
CAMA_DIR = os.path.join(BASE_DIR, "result/impact_assessment/older")
CAMA_CSV = os.path.join(
    CAMA_DIR,
    "city_flood_events_T2_5_10_20_50_100_1980_2020.csv"
)

# External flood dataset comparison note.
DFO_DIR = os.path.join(BASE_DIR, "result/impact_assessment/older/DFO_city")
DFO_PARQ = os.path.join(
    DFO_DIR,
    "dfo_city_year_1980_2020_all_sev.parquet"
)

# Original notebook comment normalized for the public code archive.
OUT_DIR = os.path.join(BASE_DIR, "result/impact_assessment/older/compare_DFO_all_events_DFOactive")
os.makedirs(OUT_DIR, exist_ok=True)


# =============================================================================

def load_cama_events(path: str) -> pd.DataFrame:
    """Archived notebook note for 01_city_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = pd.read_csv(path, dtype={"city_code": str})

    cama_cols = [c for c in df.columns if c.startswith("flood_ge_T")]
    if not cama_cols:
        raise RuntimeError("未在 CaMa CSV 中找到 flood_ge_T* 列，请检查输入文件。")

    for c in cama_cols:
        df[c] = df[c].astype(int)

    df["cama_any_event"] = (df[cama_cols].max(axis=1) > 0).astype(int)

    keep = ["year", "city_code", "cama_any_event"] + cama_cols
    return df[keep]


def load_dfo_panel(path: str) -> pd.DataFrame:
    """Archived notebook note for 01_city_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = pd.read_parquet(path)
    df["city_code"] = df["city_code"].astype(str)

    needed = ["flooded_any_centroid", "flooded_any_area50", "flooded_any_full"]
    for c in needed:
        if c not in df.columns:
            raise RuntimeError(f"DFO 表中缺少列: {c}")
        df[c] = df[c].astype(int)

    keep = ["year", "city_code"] + needed
    return df[keep]


# =============================================================================

def compute_contingency_and_skill(
    cama_flag: pd.Series,
    dfo_flag: pd.Series,
) -> dict:
    """Archived notebook note for 01_city_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    cama = cama_flag.astype(int).values
    dfo = dfo_flag.astype(int).values

    hits         = int(((cama == 1) & (dfo == 1)).sum())
    misses       = int(((cama == 0) & (dfo == 1)).sum())
    false_alarms = int(((cama == 1) & (dfo == 0)).sum())
    correct_neg  = int(((cama == 0) & (dfo == 0)).sum())

    H, M, F, C = hits, misses, false_alarms, correct_neg
    TOT = H + M + F + C

    pod = H / (H + M) if (H + M) > 0 else np.nan          # Probability of Detection
    far = F / (H + F) if (H + F) > 0 else np.nan          # False Alarm Ratio
    pofd = F / (F + C) if (F + C) > 0 else np.nan         # Probability of False Detection
    csi = H / (H + M + F) if (H + M + F) > 0 else np.nan  # Critical Success Index

    freq_cama = (H + F) / TOT if TOT > 0 else np.nan
    freq_dfo  = (H + M) / TOT if TOT > 0 else np.nan
    bias = freq_cama / freq_dfo if (freq_cama >= 0 and freq_dfo > 0) else np.nan

    denom_hss = (H + M) * (M + C) + (H + F) * (F + C)
    hss = (2 * (H * C - F * M) / denom_hss) if denom_hss > 0 else np.nan

    if TOT > 0:
        h_random = (H + M) * (H + F) / TOT
        denom_ets = (H + M + F - h_random)
        ets = (H - h_random) / denom_ets if denom_ets > 0 else np.nan
    else:
        ets = np.nan

    return {
        "H": H,
        "M": M,
        "F": F,
        "C": C,
        "POD": pod,
        "FAR": far,
        "POFD": pofd,
        "CSI": csi,
        "Bias": bias,
        "HSS": hss,
        "ETS": ets,
        "freq_cama": freq_cama,
        "freq_dfo": freq_dfo,
        "TOT": TOT,
    }


def print_skill_report(label: str, metrics: dict):
    """Archived notebook note for 01_city_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print("\n" + "=" * 72)
    print("[INFO] Notebook progress message.")
    print("-" * 72)
    print("[INFO] Notebook progress message.")
    print(f"Hits         (1,1)        : {metrics['H']}")
    print(f"Misses       (0,1)        : {metrics['M']}")
    print(f"False alarms (1,0)        : {metrics['F']}")
    print(f"Correct neg  (0,0)        : {metrics['C']}")
    print("-" * 72)
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print(f"HSS  (Heidke Skill Score)  = {metrics['HSS']:.3f}")
    print(f"ETS  (Equitable Threat Score) = {metrics['ETS']:.3f}")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")


# =============================================================================

def get_dfo_active_cities(df: pd.DataFrame, dfo_col: str) -> pd.Index:
    """Archived notebook note for 01_city_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = df.groupby("city_code")[dfo_col].sum()
    active = s[s > 0].index
    return active


# =============================================================================

def main():
    print("[INFO] Notebook progress message.")
    df_cama = load_cama_events(CAMA_CSV)

    print("[INFO] Notebook progress message.")
    df_dfo = load_dfo_panel(DFO_PARQ)

    print("[INFO] Notebook progress message.")
    df = df_cama.merge(
        df_dfo,
        on=["city_code", "year"],
        how="inner",
        suffixes=("_cama", "_dfo")
    )
    print("[INFO] Notebook progress message.", df.shape)

    cama_any = df["cama_any_event"].astype(int)

    # =============================================================================

    # 1) centroid
    dfo_centroid = df["flooded_any_centroid"].astype(int)
    metrics_cent_all = compute_contingency_and_skill(cama_any, dfo_centroid)
    print_skill_report("[INFO] Notebook progress message.", metrics_cent_all)

    grp_cent = df.groupby("city_code", as_index=False).agg(
        cama_any_freq=("cama_any_event", "mean"),
        dfo_any_freq_centroid=("flooded_any_centroid", "mean"),
    )
    corr_cent = grp_cent["cama_any_freq"].corr(grp_cent["dfo_any_freq_centroid"])
    print("[INFO] Notebook progress message.")
    grp_cent.to_csv(
        os.path.join(OUT_DIR, "city_freq_CaMaAny_vs_DFOAny_centroid_allCities.csv"),
        index=False
    )

    # 2) area50
    dfo_area50 = df["flooded_any_area50"].astype(int)
    metrics_a50_all = compute_contingency_and_skill(cama_any, dfo_area50)
    print_skill_report("[INFO] Notebook progress message.", metrics_a50_all)

    grp_a50 = df.groupby("city_code", as_index=False).agg(
        cama_any_freq=("cama_any_event", "mean"),
        dfo_any_freq_area50=("flooded_any_area50", "mean"),
    )
    corr_a50 = grp_a50["cama_any_freq"].corr(grp_a50["dfo_any_freq_area50"])
    print("[INFO] Notebook progress message.")
    grp_a50.to_csv(
        os.path.join(OUT_DIR, "city_freq_CaMaAny_vs_DFOAny_area50_allCities.csv"),
        index=False
    )

    # 3) full
    dfo_full = df["flooded_any_full"].astype(int)
    metrics_full_all = compute_contingency_and_skill(cama_any, dfo_full)
    print_skill_report("[INFO] Notebook progress message.", metrics_full_all)

    grp_full = df.groupby("city_code", as_index=False).agg(
        cama_any_freq=("cama_any_event", "mean"),
        dfo_any_freq_full=("flooded_any_full", "mean"),
    )
    corr_full = grp_full["cama_any_freq"].corr(grp_full["dfo_any_freq_full"])
    print("[INFO] Notebook progress message.")
    grp_full.to_csv(
        os.path.join(OUT_DIR, "city_freq_CaMaAny_vs_DFOAny_full_allCities.csv"),
        index=False
    )

    # =============================================================================

    # External flood dataset comparison note.
    # Original notebook comment normalized for the public code archive.

    # Original notebook comment normalized for the public code archive.
    active_cent = get_dfo_active_cities(df, "flooded_any_centroid")
    df_cent_active = df[df["city_code"].isin(active_cent)].copy()
    print("[INFO] Notebook progress message.", len(active_cent))
    print("[INFO] Notebook progress message.", df_cent_active.shape)

    cama_any_cent = df_cent_active["cama_any_event"].astype(int)
    dfo_cent_active = df_cent_active["flooded_any_centroid"].astype(int)
    metrics_cent_active = compute_contingency_and_skill(cama_any_cent, dfo_cent_active)
    print_skill_report("[INFO] Notebook progress message.", metrics_cent_active)

    grp_cent_act = df_cent_active.groupby("city_code", as_index=False).agg(
        cama_any_freq=("cama_any_event", "mean"),
        dfo_any_freq_centroid=("flooded_any_centroid", "mean"),
    )
    corr_cent_act = grp_cent_act["cama_any_freq"].corr(grp_cent_act["dfo_any_freq_centroid"])
    print("[INFO] Notebook progress message.")
    grp_cent_act.to_csv(
        os.path.join(OUT_DIR, "city_freq_CaMaAny_vs_DFOAny_centroid_DFOactiveCities.csv"),
        index=False
    )

    # Original notebook comment normalized for the public code archive.
    active_a50 = get_dfo_active_cities(df, "flooded_any_area50")
    df_a50_active = df[df["city_code"].isin(active_a50)].copy()
    print("[INFO] Notebook progress message.", len(active_a50))
    print("[INFO] Notebook progress message.", df_a50_active.shape)

    cama_any_a50 = df_a50_active["cama_any_event"].astype(int)
    dfo_a50_active = df_a50_active["flooded_any_area50"].astype(int)
    metrics_a50_active = compute_contingency_and_skill(cama_any_a50, dfo_a50_active)
    print_skill_report("[INFO] Notebook progress message.", metrics_a50_active)

    grp_a50_act = df_a50_active.groupby("city_code", as_index=False).agg(
        cama_any_freq=("cama_any_event", "mean"),
        dfo_any_freq_area50=("flooded_any_area50", "mean"),
    )
    corr_a50_act = grp_a50_act["cama_any_freq"].corr(grp_a50_act["dfo_any_freq_area50"])
    print("[INFO] Notebook progress message.")
    grp_a50_act.to_csv(
        os.path.join(OUT_DIR, "city_freq_CaMaAny_vs_DFOAny_area50_DFOactiveCities.csv"),
        index=False
    )

    # Original notebook comment normalized for the public code archive.
    active_full = get_dfo_active_cities(df, "flooded_any_full")
    df_full_active = df[df["city_code"].isin(active_full)].copy()
    print("[INFO] Notebook progress message.", len(active_full))
    print("[INFO] Notebook progress message.", df_full_active.shape)

    cama_any_full = df_full_active["cama_any_event"].astype(int)
    dfo_full_active = df_full_active["flooded_any_full"].astype(int)
    metrics_full_active = compute_contingency_and_skill(cama_any_full, dfo_full_active)
    print_skill_report("[INFO] Notebook progress message.", metrics_full_active)

    grp_full_act = df_full_active.groupby("city_code", as_index=False).agg(
        cama_any_freq=("cama_any_event", "mean"),
        dfo_any_freq_full=("flooded_any_full", "mean"),
    )
    corr_full_act = grp_full_act["cama_any_freq"].corr(grp_full_act["dfo_any_freq_full"])
    print("[INFO] Notebook progress message.")
    grp_full_act.to_csv(
        os.path.join(OUT_DIR, "city_freq_CaMaAny_vs_DFOAny_full_DFOactiveCities.csv"),
        index=False
    )

    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 36
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 01_city_gumbel_events_vs_dfo.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import re
from glob import glob

import numpy as np
import pandas as pd
import geopandas as gpd
from rasterio.transform import Affine
from rasterio import features
from pyproj import Geod

# =============================================================================

BASE_DIR = "/home/ll/jupyter_notebook"

# CaMa-Flood processing note.
STOR_P50_ROOT = os.path.join(
    BASE_DIR,
    "result/ensemble_storge_daily_bin_p50"
)

# Original notebook comment normalized for the public code archive.
CITY_SHP = os.path.join(BASE_DIR, "gis_data/China/city/city.shp")
CITY_ID_FIELD = "市代码"
CITY_NAME_FIELD = "市"

# External flood dataset comparison note.
DFO_PARQ = os.path.join(
    BASE_DIR,
    "result/impact_assessment/older/DFO_city/dfo_city_year_1980_2020_all_sev.parquet"
)

# Original notebook comment normalized for the public code archive.
START_YEAR = 1980
END_YEAR   = 2020

# Original notebook comment normalized for the public code archive.
APPLY_DRY_FILTER = True    # Original notebook comment normalized for the public code archive.
DRY_FRAC_MIN     = 0.30    # Original notebook comment normalized for the public code archive.
DRY_COUNTY_MIN   = 0.05    # Original notebook comment normalized for the public code archive.

OUT_DIR = os.path.join(
    BASE_DIR,
    "result/impact_assessment/older/compare_raw_products"
)
os.makedirs(OUT_DIR, exist_ok=True)


# =============================================================================

def find_sample_json(p50_root: str) -> str:
    pattern = os.path.join(p50_root, "**", "*.bin.json")
    cands = glob(pattern, recursive=True)
    if not cands:
        raise RuntimeError(f"在 {p50_root} 下未找到任何 .bin.json 文件。")
    cands = sorted(cands)
    print("[INFO] Notebook progress message.")
    return cands[0]


def prepare_storge_meta(sample_json: str):
    import json
    with open(sample_json, "r", encoding="utf-8") as jf:
        meta = json.load(jf)

    rows, cols = int(meta["rows"]), int(meta["cols"])
    compact = meta.get("compact_mode", "float32")

    if compact == "float32":
        dtype = np.dtype("<f4")
        scale = 1.0
        nan_code = None
    elif compact == "float16":
        dtype = np.dtype("<f2")
        scale = 1.0
        nan_code = None
    elif compact == "u16_q01m":
        dtype = np.dtype("<u2")
        bands = meta["bands"][0]
        scale = float(bands.get("scale", 0.01))
        nan_code = np.uint16(bands.get("nan", 65535))
    else:
        raise ValueError(f"未知 compact_mode: {compact}")

    x0, y0, dx, dy = meta["transform"]
    transform = Affine(dx, 0, x0, 0, dy, y0)
    crs = meta.get("crs", "EPSG:4326")
    return rows, cols, dtype, scale, nan_code, transform, crs


def pixel_area_raster(transform: Affine, shape):
    ny, nx = shape
    geod = Geod(ellps="WGS84")

    xs = transform.c + (np.arange(nx) + 0.5) * transform.a
    ys = transform.f + (np.arange(ny) + 0.5) * transform.e

    x_left  = xs[0]  - 0.5 * transform.a
    x_right = xs[-1] + 0.5 * transform.a

    area = np.zeros((ny, nx), dtype=np.float64)
    for j in range(ny):
        dlon_row = geod.line_length([x_left, x_right], [ys[j], ys[j]]) / nx
        y_top = ys[j] - 0.5 * transform.e
        y_bot = ys[j] + 0.5 * transform.e
        dlat = geod.line_length([xs[0], xs[0]], [y_top, y_bot])
        area[j, :] = dlon_row * dlat
    return area


def rasterize_cities(transform, shape, city_shp, id_field, name_field):
    ny, nx = shape
    gdf = gpd.read_file(city_shp)
    if gdf.crs is None:
        gdf = gdf.set_crs(4326)
    else:
        gdf = gdf.to_crs(4326)

    # Original notebook comment normalized for the public code archive.
    if id_field not in gdf.columns:
        raise ValueError(f"市界文件中找不到 ID 字段 {id_field}。")

    ids_raw = gdf[id_field]
    ids_as_key = ids_raw.astype(str)
    codes, uniques = pd.factorize(ids_as_key, sort=False)
    cid_per_row = (codes + 1).astype(np.int32)  # internal id from 1

    # Original notebook comment normalized for the public code archive.
    if name_field and name_field in gdf.columns:
        name_map = gdf[[id_field, name_field]].drop_duplicates(subset=[id_field]).copy()
        name_map[id_field] = name_map[id_field].astype(str)
        name_map.columns = ["city_code", "city_name"]
    else:
        name_map = pd.DataFrame(columns=["city_code", "city_name"])

    map_df = pd.DataFrame({
        "city_id": np.arange(1, len(uniques) + 1, dtype=np.int32),
        "city_code": uniques
    })
    if not name_map.empty:
        map_df = map_df.merge(name_map, on="city_code", how="left")

    shapes_iter = ((geom, int(cid)) for geom, cid in zip(gdf.geometry, cid_per_row))
    city_id_full = features.rasterize(
        shapes=shapes_iter,
        out_shape=(ny, nx),
        transform=transform,
        fill=0,
        dtype="int32"
    )

    return city_id_full, map_df


def compute_city_area(city_id_full, pix_area_full, map_df):
    mask = city_id_full > 0
    cids = city_id_full[mask].astype(np.int32)
    weights = pix_area_full[mask]
    max_cid = int(city_id_full.max())

    bc = np.bincount(cids, weights=weights, minlength=max_cid + 1)
    area_m2 = {int(i): float(w) for i, w in enumerate(bc) if i != 0}

    df_area = map_df.copy()
    df_area["area_m2"]  = df_area["city_id"].map(area_m2).fillna(0.0)
    df_area["area_km2"] = df_area["area_m2"] / 1e6
    return df_area


def list_storge_bin_files(p50_root, start_year=None, end_year=None):
    pattern = os.path.join(p50_root, "**", "*.bin")
    paths = sorted(glob(pattern, recursive=True))
    out = []
    for p in paths:
        fname = os.path.basename(p)
        m = re.search(r"(\d{8})", fname)
        if not m:
            continue
        datestr = m.group(1)
        year = int(datestr[:4])
        if start_year is not None and year < start_year:
            continue
        if end_year is not None and year > end_year:
            continue
        date = pd.to_datetime(datestr, format="%Y%m%d")
        out.append((p, date))
    print("[INFO] Notebook progress message.")
    return out


def load_cama_storage(bin_path, rows, cols, dtype, scale, nan_code):
    n = rows * cols
    with open(bin_path, "rb") as f:
        buf = f.read()
    arr = np.frombuffer(buf, dtype=dtype, count=n)
    if arr.size != n:
        raise RuntimeError(f"{bin_path} 数据长度不匹配。期望 {n}，实际 {arr.size}")
    arr = arr.reshape((rows, cols)).astype(np.float32)

    if nan_code is not None:
        arr[arr == nan_code] = np.nan
    arr = arr * scale

    # Original notebook comment normalized for the public code archive.
    arr = np.where(np.isfinite(arr) & (arr > 0), arr, np.nan)
    return arr


def compute_annual_max_storage(bin_list, rows, cols, dtype, scale, nan_code):
    if not bin_list:
        raise RuntimeError("bin_list 为空。")

    years = sorted({date.year for _, date in bin_list})
    year_to_idx = {y: i for i, y in enumerate(years)}
    Ny = len(years)

    S_annual_max = np.full((Ny, rows, cols), np.nan, dtype=np.float32)

    print("[INFO] Notebook progress message.")
    bin_list_sorted = sorted(bin_list, key=lambda x: x[1])

    prev_year = None
    for bin_path, date in bin_list_sorted:
        y = date.year
        idx = year_to_idx[y]
        if prev_year is None or y != prev_year:
            print("[INFO] Notebook progress message.")
            prev_year = y

        arr = load_cama_storage(bin_path, rows, cols, dtype, scale, nan_code)

        current_max = S_annual_max[idx]
        mask_curr_nan = ~np.isfinite(current_max)
        mask_arr_nan  = ~np.isfinite(arr)

        replace_mask = mask_curr_nan & (~mask_arr_nan)
        current_max[replace_mask] = arr[replace_mask]

        both_valid = (~mask_curr_nan) & (~mask_arr_nan)
        current_max[both_valid] = np.maximum(current_max[both_valid], arr[both_valid])

        S_annual_max[idx] = current_max

    return np.array(years, dtype=int), S_annual_max


def compute_city_annual_series(S_annual_max, city_id_full, pix_area_full):
    Ny, rows, cols = S_annual_max.shape
    max_cid = int(city_id_full.max())
    city_series = np.full((Ny, max_cid + 1), np.nan, dtype=np.float32)

    valid_city_mask = city_id_full > 0

    for t in range(Ny):
        S_year = S_annual_max[t]
        mask = valid_city_mask & np.isfinite(S_year)
        if not mask.any():
            continue

        cids = city_id_full[mask].astype(np.int32)
        areas = pix_area_full[mask].astype(np.float64)
        vals  = S_year[mask].astype(np.float64)

        num = np.bincount(cids, weights=areas * vals, minlength=max_cid + 1)
        den = np.bincount(cids, weights=areas, minlength=max_cid + 1)

        with np.errstate(divide="ignore", invalid="ignore"):
            mean_vals = num / den
        mean_vals[den == 0] = np.nan

        city_series[t, :] = mean_vals.astype(np.float32)

    return city_series


# =============================================================================

def apply_dry_filters(S_annual_max, city_id_full, pix_area_full,
                      dry_frac_min, dry_county_min, out_dir):
    Ny, rows, cols = S_annual_max.shape
    max_cid = int(city_id_full.max())

    # Original notebook comment normalized for the public code archive.
    valid_frac = np.isfinite(S_annual_max).sum(axis=0) / float(Ny)
    dry_mask = valid_frac < dry_frac_min

    n_dry_pix = int(dry_mask.sum())
    n_all_pix = int(rows * cols)
    print(f"[D1] dry pixels: {n_dry_pix}/{n_all_pix} "
          f"({n_dry_pix/n_all_pix:.3f}), DRY_FRAC_MIN={dry_frac_min}")

    S_annual_max[:, dry_mask] = np.nan

    np.save(os.path.join(out_dir, "dry_mask_pixels_D1.npy"),
            dry_mask.astype(np.uint8))
    pd.DataFrame({
        "DRY_FRAC_MIN": [dry_frac_min],
        "n_dry_pixels": [n_dry_pix],
        "n_all_pixels": [n_all_pix],
        "dry_pixel_share": [n_dry_pix/n_all_pix]
    }).to_csv(os.path.join(out_dir, "dry_mask_pixels_D1_report.csv"), index=False)

    # Original notebook comment normalized for the public code archive.
    valid_pixel_any = np.isfinite(S_annual_max).any(axis=0) & (city_id_full > 0)

    cids_valid = city_id_full[valid_pixel_any].astype(np.int32)
    areas_valid = pix_area_full[valid_pixel_any].astype(np.float64)

    cids_total = city_id_full[city_id_full > 0].astype(np.int32)
    areas_total = pix_area_full[city_id_full > 0].astype(np.float64)

    valid_area = np.bincount(cids_valid, weights=areas_valid, minlength=max_cid + 1)
    total_area = np.bincount(cids_total, weights=areas_total, minlength=max_cid + 1)

    with np.errstate(divide="ignore", invalid="ignore"):
        g_frac = valid_area / total_area
    g_frac[total_area == 0] = np.nan

    dry_cities = np.where(g_frac < dry_county_min)[0]
    dry_cities = dry_cities[dry_cities > 0]

    print(f"[D2] dry cities: {len(dry_cities)}/{max_cid} "
          f"({len(dry_cities)/max_cid:.3f}), DRY_COUNTY_MIN={dry_county_min}")

    return S_annual_max, dry_cities, g_frac


# =============================================================================

def main():
    # =============================================================================
    print("[INFO] Notebook progress message.")
    sample_json = find_sample_json(STOR_P50_ROOT)
    rows, cols, dtp, scl, nan_code, transform, crs = prepare_storge_meta(sample_json)
    ny, nx = rows, cols
    print(f"[INFO] storge P50 grid: {nx} x {ny}, crs={crs}")

    # =============================================================================
    print("[INFO] Notebook progress message.")
    pix_area_full = pixel_area_raster(transform, (ny, nx))

    print("[INFO] Notebook progress message.")
    city_id_full, map_df = rasterize_cities(
        transform, (ny, nx), CITY_SHP, CITY_ID_FIELD, CITY_NAME_FIELD
    )
    df_area = compute_city_area(city_id_full, pix_area_full, map_df)
    df_area.to_csv(os.path.join(OUT_DIR, "city_total_area_storage.csv"), index=False)
    print("[INFO] Notebook progress message.")

    # =============================================================================
    print("[INFO] Notebook progress message.")
    bin_list = list_storge_bin_files(STOR_P50_ROOT, START_YEAR, END_YEAR)
    if not bin_list:
        raise RuntimeError("未找到任何 P50 bin 文件，请检查 STOR_P50_ROOT 和年份设置。")

    print("[INFO] Notebook progress message.")
    years_all, S_annual_max = compute_annual_max_storage(
        bin_list, rows, cols, dtp, scl, nan_code
    )

    # =============================================================================
    if APPLY_DRY_FILTER:
        print("[INFO] Notebook progress message.")
        S_annual_max, dry_cities, g_frac = apply_dry_filters(
            S_annual_max, city_id_full, pix_area_full,
            DRY_FRAC_MIN, DRY_COUNTY_MIN, OUT_DIR
        )
    else:
        dry_cities = np.array([], dtype=int)
        g_frac = None

    # =============================================================================
    print("[INFO] Notebook progress message.")
    city_series = compute_city_annual_series(
        S_annual_max, city_id_full, pix_area_full
    )  # (Ny, n_cities+1)

    # Original notebook comment normalized for the public code archive.
    if APPLY_DRY_FILTER and len(dry_cities) > 0:
        city_series[:, dry_cities] = np.nan

    # =============================================================================
    print("[INFO] Notebook progress message.")
    years_all = np.asarray(years_all, dtype=int)
    Ny, nC1 = city_series.shape

    recs = []
    for iy, y in enumerate(years_all):
        vals = city_series[iy, :]
        for _, row in map_df.iterrows():
            cid = int(row["city_id"])
            code = row["city_code"]
            name = row.get("city_name", None)
            v = vals[cid]
            recs.append({
                "year": int(y),
                "city_id_cama": cid,
                "city_code": code,
                "city_name": name,
                "S_city_annual_max_m3": float(v) if np.isfinite(v) else np.nan,
            })
    df_cama_city_year = pd.DataFrame.from_records(recs)
    df_cama_city_year.to_parquet(
        os.path.join(OUT_DIR, "city_year_cama_annualmax.parquet"),
        index=False
    )
    print("[INFO] Notebook progress message.")

    # =============================================================================
    print("[INFO] Notebook progress message.")
    df_dfo = pd.read_parquet(DFO_PARQ)
    df_dfo["city_code"] = df_dfo["city_code"].astype(str)

    print("[INFO] Notebook progress message.")
    df_all = df_cama_city_year.merge(
        df_dfo,
        on=["city_code", "year"],
        how="inner"
    )
    out_parq = os.path.join(OUT_DIR, "city_year_cama_dfo_raw_compare.parquet")
    out_csv  = os.path.join(OUT_DIR, "city_year_cama_dfo_raw_compare.csv")
    df_all.to_parquet(out_parq, index=False)
    df_all.to_csv(out_csv, index=False)
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.", df_all.shape)

    # =============================================================================
    # External flood dataset comparison note.
    print("[INFO] Notebook progress message.")

    mask_valid = np.isfinite(df_all["S_city_annual_max_m3"])
    dfv = df_all[mask_valid].copy()

    # External flood dataset comparison note.
    for flag_col in ["flooded_any_centroid",
                     "flooded_any_area50",
                     "flooded_any_full"]:
        if flag_col not in dfv.columns:
            continue
        mu1 = dfv.loc[dfv[flag_col] == 1, "S_city_annual_max_m3"].mean()
        mu0 = dfv.loc[dfv[flag_col] == 0, "S_city_annual_max_m3"].mean()
        print("[INFO] Notebook progress message.")
        print("[INFO] Notebook progress message.")

    # External flood dataset comparison note.
    # Original notebook comment normalized for the public code archive.
    dfv["log10_S_city_annual_max"] = np.log10(dfv["S_city_annual_max_m3"].clip(lower=1.0))

    # Original notebook comment normalized for the public code archive.
    for flag_col in ["flooded_any_centroid",
                     "flooded_any_area50",
                     "flooded_any_full"]:
        if flag_col not in dfv.columns:
            continue
        r = dfv["log10_S_city_annual_max"].corr(dfv[flag_col].astype(float))
        print(f"  Corr(log10 S_annual_max, {flag_col}) = {r:.3f}")

    # External flood dataset comparison note.
    for col in ["flooded_times_centroid",
                "duration_days_centroid",
                "severe_times_centroid_sev1",
                "severe_times_centroid_sev1_5",
                "severe_times_centroid_sev2"]:
        if col in dfv.columns:
            r = dfv["log10_S_city_annual_max"].corr(dfv[col].astype(float))
            print(f"  Corr(log10 S_annual_max, {col}) = {r:.3f}")

    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()
