#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 01_dfo_child_elderly_intensity_curves.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 1
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 01_dfo_child_elderly_intensity_curves.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
from math import erf, sqrt

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


# =============================================================================

# External flood dataset comparison note.
EDU_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood_dfo_rep/severity_curve_edu_beta"
)
EDU_PTS_CSV = EDU_DIR / "severity_curve_edu_beta_points.csv"

# External flood dataset comparison note.
HEALTH_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/DFO_city"
)
MERGED_PANEL = HEALTH_DIR / "charls_health_panel_60plus_with_index_DFO_5_10_20_30y.parquet"

# Original notebook comment normalized for the public code archive.
OUT_DIR_COMBINED = HEALTH_DIR / "severity_edu_health_twinx"
OUT_DIR_COMBINED.mkdir(parents=True, exist_ok=True)

# Original notebook comment normalized for the public code archive.
ID_COL = "pid12"
Y_VAR_HEALTH = "health_index_z"
YEAR_COL = "year"
PROV_COL = "province"
CLUSTER_COL = "city_code"

PREFIXES = ["centroid", "area50", "full"]
WINDOWS = [5, 10, 20, 30]

SAMPLES = ["all", "rural", "urban"]   # Original notebook comment normalized for the public code archive.
SAVE_FIG = True


# =============================================================================

def norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))


def stars_for_p(p: float) -> str:
    try:
        p = float(p)
    except (TypeError, ValueError):
        return ""
    if p < 0.001:
        return "****"
    elif p < 0.05:
        return "**"
    elif p < 0.10:
        return "*"
    else:
        return ""


# =============================================================================

def build_continuous_beta_from_points(sub: pd.DataFrame):
    """Archived notebook note for 01_dfo_child_elderly_intensity_curves.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sub = sub.sort_values("s").copy()
    s_vals = sub["s"].to_numpy(dtype="float64")
    beta_vals = sub["Estimate"].to_numpy(dtype="float64")
    se_vals = sub["StdError"].to_numpy(dtype="float64")

    n = len(s_vals)
    if n < 2:
        raise ValueError("至少需要 2 个严重程度点才能构造连续 β(s)。")

    deg = n - 1
    # Original notebook comment normalized for the public code archive.
    M = np.vstack([s_vals**k for k in range(deg + 1)]).T

    var_vals = se_vals ** 2
    var_vals[var_vals <= 0] = 1e-12
    Cov_B = np.diag(var_vals)

    M_inv = np.linalg.inv(M)
    gamma = M_inv @ beta_vals
    Cov_gamma = M_inv @ Cov_B @ M_inv.T

    return s_vals, beta_vals, se_vals, gamma, Cov_gamma


def load_edu_points() -> pd.DataFrame:
    print(f"[READ] EDU severity points: {EDU_PTS_CSV}")
    df_pts = pd.read_csv(EDU_PTS_CSV)
    print("[INFO] Notebook progress message.")
    print(df_pts.head())
    return df_pts


def get_edu_curve_for_sample(df_pts: pd.DataFrame, sample_type: str):
    """Archived notebook note for 01_dfo_child_elderly_intensity_curves.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sub = df_pts[df_pts["sample_type"] == sample_type].copy()
    if sub.empty:
        print("[INFO] Notebook progress message.")
        return None

    s_vals, beta_vals, se_vals, gamma, Cov_gamma = build_continuous_beta_from_points(sub)
    labels = sub["sev_label"].tolist()
    p_vals = sub["PValue"].to_numpy(dtype="float64")

    print("[INFO] Notebook progress message.")
    return {
        "s_vals": s_vals,
        "labels": labels,
        "p_vals": p_vals,
        "gamma": gamma,
        "Cov_gamma": Cov_gamma,
    }


def eval_poly_curve(gamma, Sigma, s_array):
    """Archived notebook note for 01_dfo_child_elderly_intensity_curves.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s_array = np.asarray(s_array, dtype="float64")
    deg = len(gamma) - 1
    Phi = np.vstack([s_array**k for k in range(deg + 1)]).T

    beta = Phi @ gamma
    var = np.einsum("ij,jk,ik->i", Phi, Sigma, Phi)
    var = np.maximum(var, 0.0)
    se = np.sqrt(var)

    ci_low = beta - 1.96 * se
    ci_high = beta + 1.96 * se
    return beta, se, ci_low, ci_high


# =============================================================================

def demean_two_fe(df: pd.DataFrame, cols, fe1, fe2) -> pd.DataFrame:
    """Archived notebook note for 01_dfo_child_elderly_intensity_curves.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()
    X = df[cols].astype("float64")

    g1_means = X.groupby(df[fe1]).transform("mean")
    g2_means = X.groupby(df[fe2]).transform("mean")
    mu = X.mean()

    X_dm = X - g1_means - g2_means + mu
    X_dm.columns = [f"{c}_dm" for c in cols]

    df = pd.concat([df, X_dm], axis=1)
    return df


def fe_reg_twoFE_city_cluster_fit(df: pd.DataFrame,
                                  y_col: str,
                                  x_cols,
                                  fe1: str,
                                  fe2: str,
                                  cluster_col: str):
    """Archived notebook note for 01_dfo_child_elderly_intensity_curves.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    cols_needed = [y_col] + list(x_cols) + [fe1, fe2, cluster_col]
    df = df.dropna(subset=cols_needed).copy()

    df = df[df[cluster_col].notna()].copy()
    if df.empty:
        raise ValueError("cluster_col 全缺失，无法回归。")

    df = demean_two_fe(df, [y_col] + list(x_cols), fe1=fe1, fe2=fe2)

    y = df[f"{y_col}_dm"].astype("float64")
    X_dm_cols = [f"{c}_dm" for c in x_cols]
    X = df[X_dm_cols].astype("float64")

    df["cluster_group"] = pd.Categorical(df[cluster_col]).codes
    groups = df["cluster_group"].to_numpy()

    model = sm.OLS(y, X)
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": groups})
    return fit


def prepare_health_panel() -> pd.DataFrame:
    """Archived notebook note for 01_dfo_child_elderly_intensity_curves.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print(f"[READ] merged panel: {MERGED_PANEL}")
    df = pd.read_parquet(MERGED_PANEL)

    # Original notebook comment normalized for the public code archive.
    sev1_list, sev15_list, sev2_list = [], [], []
    for prefix in PREFIXES:
        for w in WINDOWS:
            c1 = f"share_DFO_sev1_{prefix}_{w}y"
            c15 = f"share_DFO_sev1_5_{prefix}_{w}y"
            c2 = f"share_DFO_sev2_{prefix}_{w}y"

            has_any = False
            if c1 in df.columns:
                sev1_list.append(pd.to_numeric(df[c1], errors="coerce"))
                has_any = True
            if c15 in df.columns:
                sev15_list.append(pd.to_numeric(df[c15], errors="coerce"))
                has_any = True
            if c2 in df.columns:
                sev2_list.append(pd.to_numeric(df[c2], errors="coerce"))
                has_any = True

            if has_any:
                print("[INFO] Notebook progress message.")
            else:
                print("[INFO] Notebook progress message.")

    if sev1_list:
        sev1_mat = pd.concat(sev1_list, axis=1)
        df["E1_agg"] = sev1_mat.mean(axis=1, skipna=True)
    else:
        df["E1_agg"] = 0.0

    if sev15_list:
        sev15_mat = pd.concat(sev15_list, axis=1)
        df["E15_agg"] = sev15_mat.mean(axis=1, skipna=True)
    else:
        df["E15_agg"] = 0.0

    if sev2_list:
        sev2_mat = pd.concat(sev2_list, axis=1)
        df["E2_agg"] = sev2_mat.mean(axis=1, skipna=True)
    else:
        df["E2_agg"] = 0.0

    df[["E1_agg", "E15_agg", "E2_agg"]] = (
        df[["E1_agg", "E15_agg", "E2_agg"]].fillna(0.0).astype("float64")
    )

    print("[INFO] Notebook progress message.")
    print(df[["E1_agg", "E15_agg", "E2_agg"]].describe())

    # Original notebook comment normalized for the public code archive.
    df["X0"] = df["E1_agg"] + df["E15_agg"] + df["E2_agg"]
    df["X1"] = 1.0 * df["E1_agg"] + 1.5 * df["E15_agg"] + 2.0 * df["E2_agg"]
    df["X2"] = 1.0**2 * df["E1_agg"] + 1.5**2 * df["E15_agg"] + 2.0**2 * df["E2_agg"]

    # Fixed-effects regression helper.
    df[Y_VAR_HEALTH] = pd.to_numeric(df[Y_VAR_HEALTH], errors="coerce")
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df[YEAR_COL] = pd.to_numeric(df[YEAR_COL], errors="coerce")

    df["age2"] = df["age"] ** 2
    df["prov_str"] = df[PROV_COL].astype(str).str.strip()
    df["prov_year"] = df["prov_str"] + "_" + df[YEAR_COL].astype(int).astype(str)

    if "urban_nbs" in df.columns:
        df["urban_nbs"] = pd.to_numeric(df["urban_nbs"], errors="coerce").fillna(0).astype(int)
        grp_urban = df.groupby(ID_COL)["urban_nbs"].mean()
        df = df.merge(
            (grp_urban > 0.5).astype(int).rename("urban_group"),
            on=ID_COL, how="left",
        )
    else:
        df["urban_group"] = 1

    # Original notebook comment normalized for the public code archive.
    waves_per_id = df.groupby(ID_COL)[YEAR_COL].nunique()
    keep_ids = waves_per_id[waves_per_id >= 2].index
    df = df[df[ID_COL].isin(keep_ids)].copy()

    df[CLUSTER_COL] = pd.to_numeric(df[CLUSTER_COL], errors="coerce")

    print(
        f"[INFO] health panel: IDs with >=2 waves: {df[ID_COL].nunique()}, "
        f"N={len(df)}, years={sorted(df[YEAR_COL].unique())}"
    )
    return df


def estimate_health_poly(df: pd.DataFrame, sample_name: str):
    """Archived notebook note for 01_dfo_child_elderly_intensity_curves.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    # Original notebook comment normalized for the public code archive.
    sample_specs = {"all": None, "urban": 1, "rural": 0}
    if sample_name not in sample_specs:
        raise KeyError(f"未知 sample_name: {sample_name}")

    gval = sample_specs[sample_name]
    if gval is None:
        sub = df.copy()
    else:
        sub = df[df["urban_group"] == gval].copy()

    waves_sub = sub.groupby(ID_COL)[YEAR_COL].nunique()
    keep_ids_sub = waves_sub[waves_sub >= 2].index
    sub = sub[sub[ID_COL].isin(keep_ids_sub)].copy()

    if len(sub) < 100 or sub[CLUSTER_COL].nunique() < 10:
        print(
            f"[WARN] sample={sample_name} N 或 城市数过小 "
            f"(N={len(sub)}, N_city={sub[CLUSTER_COL].nunique()}), 跳过。"
        )
        return None

    x_cols = ["X0", "X1", "X2", "age", "age2"]
    fit = fe_reg_twoFE_city_cluster_fit(
        sub,
        y_col=Y_VAR_HEALTH,
        x_cols=x_cols,
        fe1=ID_COL,
        fe2="prov_year",
        cluster_col=CLUSTER_COL,
    )

    gamma_idx = [f"{c}_dm" for c in ["X0", "X1", "X2"]]
    missing_gamma = [g for g in gamma_idx if g not in fit.params.index]
    if missing_gamma:
        raise KeyError(f"回归结果中缺少参数列: {missing_gamma}")

    gamma_raw = fit.params[gamma_idx].to_numpy(dtype="float64")
    Sigma_raw = fit.cov_params().loc[gamma_idx, gamma_idx].to_numpy(dtype="float64")

    print(f"[INFO] HEALTH sample={sample_name}, γ(X0,X1,X2) = {gamma_raw}")

    # Original notebook comment normalized for the public code archive.
    # Original notebook comment normalized for the public code archive.
    #   X0 = sum E_i
    #   X1 = sum s_i * E_i
    #   X2 = sum s_i^2 * E_i
    # Original notebook comment normalized for the public code archive.
    # Original notebook comment normalized for the public code archive.
    gamma = gamma_raw
    Sigma = Sigma_raw

    return {
        "gamma": gamma,
        "Cov_gamma": Sigma,
        "fit": fit,
    }


# =============================================================================

def plot_severity_twinx(sample: str, edu_info: dict, health_info: dict):
    """Archived notebook note for 01_dfo_child_elderly_intensity_curves.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

    s_vals_edu = edu_info["s_vals"]
    labels_edu = edu_info["labels"]
    p_vals_edu = edu_info["p_vals"]
    gamma_edu = edu_info["gamma"]
    Sigma_edu = edu_info["Cov_gamma"]

    gamma_h = health_info["gamma"]
    Sigma_h = health_info["Cov_gamma"]

    # Original notebook comment normalized for the public code archive.
    s_min, s_max = float(s_vals_edu.min()), float(s_vals_edu.max())
    s_grid = np.linspace(s_min, s_max, 201)

    # Original notebook comment normalized for the public code archive.
    beta_edu_grid, se_edu_grid, ci_edu_low, ci_edu_high = eval_poly_curve(
        gamma_edu, Sigma_edu, s_grid
    )

    # Original notebook comment normalized for the public code archive.
    beta_h_grid, se_h_grid, ci_h_low, ci_h_high = eval_poly_curve(
        gamma_h, Sigma_h, s_grid
    )

    # Original notebook comment normalized for the public code archive.
    beta_edu_pts, se_edu_pts, ci_edu_pts_low, ci_edu_pts_high = eval_poly_curve(
        gamma_edu, Sigma_edu, s_vals_edu
    )

    # Original notebook comment normalized for the public code archive.
    p_edu_calc = []
    for b, se in zip(beta_edu_pts, se_edu_pts):
        if se > 0:
            t_val = b / se
            p_val = 2.0 * (1.0 - norm_cdf(abs(t_val)))
        else:
            p_val = np.nan
        p_edu_calc.append(p_val)
    p_edu_calc = np.array(p_edu_calc)

    # Original notebook comment normalized for the public code archive.
    beta_h_pts, se_h_pts, ci_h_pts_low, ci_h_pts_high = eval_poly_curve(
        gamma_h, Sigma_h, s_vals_edu
    )
    p_h_calc = []
    for b, se in zip(beta_h_pts, se_h_pts):
        if se > 0:
            t_val = b / se
            p_val = 2.0 * (1.0 - norm_cdf(abs(t_val)))
        else:
            p_val = np.nan
        p_h_calc.append(p_val)
    p_h_calc = np.array(p_h_calc)

    # =============================================================================
    fig, ax1 = plt.subplots(figsize=(6.5, 4.5))
    ax2 = ax1.twinx()  # Original notebook comment normalized for the public code archive.

    # =============================================================================
    ax1.plot(
        s_grid,
        beta_edu_grid,
        label="教育 β(s)",
    )
    ax1.fill_between(
        s_grid,
        ci_edu_low,
        ci_edu_high,
        alpha=0.18,
    )
    ax1.errorbar(
        s_vals_edu,
        beta_edu_pts,
        yerr=[
            beta_edu_pts - ci_edu_pts_low,
            ci_edu_pts_high - beta_edu_pts,
        ],
        fmt="o",
        linestyle="none",
        capsize=4,
        label="教育代表点",
    )

    # Original notebook comment normalized for the public code archive.
    vals1 = np.concatenate([
        ci_edu_low,
        ci_edu_high,
        ci_edu_pts_low,
        ci_edu_pts_high,
        np.array([0.0]),
    ])
    y1_min_raw = np.nanmin(vals1)
    y1_max_raw = np.nanmax(vals1)
    max_abs1 = float(max(abs(y1_min_raw), abs(y1_max_raw), 1e-6))
    pad_factor1 = 1.05
    y1_min = -max_abs1 * pad_factor1
    y1_max = max_abs1 * pad_factor1
    ax1.set_ylim(y1_min, y1_max)

    # =============================================================================
    ax2.plot(
        s_grid,
        beta_h_grid,
        linestyle="--",
        label="健康 β(s)",
    )
    ax2.fill_between(
        s_grid,
        ci_h_low,
        ci_h_high,
        alpha=0.18,
    )
    ax2.errorbar(
        s_vals_edu,
        beta_h_pts,
        yerr=[
            beta_h_pts - ci_h_pts_low,
            ci_h_pts_high - beta_h_pts,
        ],
        fmt="s",
        linestyle="none",
        capsize=4,
        label="健康代表点",
    )

    vals2 = np.concatenate([
        ci_h_low,
        ci_h_high,
        ci_h_pts_low,
        ci_h_pts_high,
        np.array([0.0]),
    ])
    y2_min_raw = np.nanmin(vals2)
    y2_max_raw = np.nanmax(vals2)
    max_abs2 = float(max(abs(y2_min_raw), abs(y2_max_raw), 1e-6))
    pad_factor2 = 1.05
    y2_min = -max_abs2 * pad_factor2
    y2_max = max_abs2 * pad_factor2
    ax2.set_ylim(y2_min, y2_max)

    # Original notebook comment normalized for the public code archive.
    y1_range = y1_max - y1_min
    offset1 = 0.04 * y1_range
    for sx, b, p in zip(s_vals_edu, beta_edu_pts, p_edu_calc):
        star = stars_for_p(p)
        if star and np.isfinite(b):
            ax1.text(sx, b + offset1, star, ha="center", va="bottom", fontsize=10)

    # Original notebook comment normalized for the public code archive.
    y2_range = y2_max - y2_min
    offset2 = 0.04 * y2_range
    for sx, b, p in zip(s_vals_edu, beta_h_pts, p_h_calc):
        star = stars_for_p(p)
        if star and np.isfinite(b):
            ax2.text(sx, b + offset2, star, ha="center", va="bottom", fontsize=10)

    # Original notebook comment normalized for the public code archive.
    ax1.set_xlim(s_min - 0.05, s_max + 0.05)
    ax1.set_xticks(s_vals_edu)
    # Original notebook comment normalized for the public code archive.
    xticklabels = []
    for lab, s in zip(labels_edu, s_vals_edu):
        if lab == "sev1":
            xticklabels.append("sev1\n(s=1)")
        elif lab == "sev1.5":
            xticklabels.append("sev1.5\n(s=1.5)")
        elif lab == "sev1.5+2":
            xticklabels.append(f"sev1.5+2\n(s≈{s:.2f})")
        else:
            xticklabels.append(f"{lab}\n(s≈{s:.2f})")
    ax1.set_xticklabels(xticklabels)

    # Original notebook comment normalized for the public code archive.
    ax1.axhline(0, linestyle="--", linewidth=1)

    ax1.set_xlabel("DFO 严重程度 s")
    ax1.set_ylabel("β(s) – 教育结果")
    ax2.set_ylabel("β(s) – 健康结果")

    ax1.set_title(
        "DFO 严重程度 s 的非线性效应曲线 β(s)\n"
        f"教育 vs 健康（sample={sample}，双 y 轴，0 对齐）"
    )

    # Original notebook comment normalized for the public code archive.
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="best")

    plt.tight_layout()

    if SAVE_FIG:
        fig_path = OUT_DIR_COMBINED / f"severity_edu_health_twinx_sample_{sample}.png"
        fig.savefig(fig_path, dpi=200)
        print("[INFO] Notebook progress message.")

    plt.show()
    plt.close(fig)


# ========= main =========

def main():
    # Original notebook comment normalized for the public code archive.
    df_edu_pts = load_edu_points()
    # Original notebook comment normalized for the public code archive.
    df_health = prepare_health_panel()

    for sample in SAMPLES:
        print(f"\n================ sample={sample} ================")
        edu_info = get_edu_curve_for_sample(df_edu_pts, sample_type=sample)
        if edu_info is None:
            print("[INFO] Notebook progress message.")
            continue

        health_info = estimate_health_poly(df_health, sample_name=sample)
        if health_info is None:
            print("[INFO] Notebook progress message.")
            continue

        plot_severity_twinx(sample, edu_info, health_info)

    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 3
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 01_dfo_child_elderly_intensity_curves.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import shutil

# =============================================================================

# Original notebook comment normalized for the public code archive.
EDU_SRC_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood_dfo_rep/severity_curve_edu_beta"
)

# Original notebook comment normalized for the public code archive.
EDU_PTS_SRC = EDU_SRC_DIR / "severity_curve_edu_beta_points.csv"

# Original notebook comment normalized for the public code archive.
EDU_REG_SRC = EDU_SRC_DIR / "severity_curve_edu_beta_reg_results.csv"

# External flood dataset comparison note.
HEALTH_PANEL_SRC = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/DFO_city/"
    "charls_health_panel_60plus_with_index_DFO_5_10_20_30y.parquet"
)

# =============================================================================

TARGET_DIR = Path(
    "/home/ll/jupyter_notebook/result/windows/DF0/1129联合绘图_教育_健康_曲线"
)


def copy_if_exists(src: Path, dst_dir: Path):
    """Archived notebook note for 01_dfo_child_elderly_intensity_curves.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if not src.exists():
        print("[INFO] Notebook progress message.")
        return
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name
    shutil.copy2(src, dst)
    print(f"[COPY] {src} -> {dst}")


def main():
    print("[INFO] Notebook progress message.")
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    # Original notebook comment normalized for the public code archive.
    copy_if_exists(EDU_PTS_SRC, TARGET_DIR)

    # Original notebook comment normalized for the public code archive.
    copy_if_exists(EDU_REG_SRC, TARGET_DIR)

    # External flood dataset comparison note.
    copy_if_exists(HEALTH_PANEL_SRC, TARGET_DIR)

    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 5
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 01_dfo_child_elderly_intensity_curves.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
from math import erf, sqrt

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt


# =============================================================================

BASE_DIR = Path(
    "/home/ll/jupyter_notebook/result/windows/DF0/1129联合绘图_教育_健康_曲线"
)

# Original notebook comment normalized for the public code archive.
EDU_PTS_CSV = BASE_DIR / "severity_curve_edu_beta_points.csv"

# External flood dataset comparison note.
MERGED_PANEL = BASE_DIR / "charls_health_panel_60plus_with_index_DFO_5_10_20_30y.parquet"

# Original notebook comment normalized for the public code archive.
OUT_DIR_PLOTS = BASE_DIR / "plots_twinx"
OUT_DIR_PLOTS.mkdir(parents=True, exist_ok=True)

# Original notebook comment normalized for the public code archive.
ID_COL = "pid12"
Y_VAR_HEALTH = "health_index_z"
YEAR_COL = "year"
PROV_COL = "province"
CLUSTER_COL = "city_code"

# Original notebook comment normalized for the public code archive.
PREFIXES = ["centroid", "area50", "full"]
WINDOWS = [5, 10, 20, 30]

SAMPLES = ["all", "rural", "urban"]
SAVE_FIG = True


# =============================================================================

def norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))


def stars_for_p(p: float) -> str:
    try:
        p = float(p)
    except (TypeError, ValueError):
        return ""
    if p < 0.001:
        return "****"
    elif p < 0.05:
        return "**"
    elif p < 0.10:
        return "*"
    else:
        return ""


# =============================================================================

def build_continuous_beta_from_points(sub: pd.DataFrame):
    """Archived notebook note for 01_dfo_child_elderly_intensity_curves.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sub = sub.sort_values("s").copy()
    s_vals = sub["s"].to_numpy(dtype="float64")
    beta_vals = sub["Estimate"].to_numpy(dtype="float64")
    se_vals = sub["StdError"].to_numpy(dtype="float64")

    n = len(s_vals)
    if n < 2:
        raise ValueError("至少需要 2 个严重程度点才能构造连续 β(s)。")

    deg = n - 1
    # Original notebook comment normalized for the public code archive.
    M = np.vstack([s_vals**k for k in range(deg + 1)]).T

    var_vals = se_vals ** 2
    var_vals[var_vals <= 0] = 1e-12
    Cov_B = np.diag(var_vals)

    M_inv = np.linalg.inv(M)
    gamma = M_inv @ beta_vals
    Cov_gamma = M_inv @ Cov_B @ M_inv.T

    return s_vals, beta_vals, se_vals, gamma, Cov_gamma


def load_edu_points() -> pd.DataFrame:
    print(f"[READ] EDU severity points: {EDU_PTS_CSV}")
    if not EDU_PTS_CSV.exists():
        raise FileNotFoundError(f"教育严重度点文件不存在: {EDU_PTS_CSV}")
    df_pts = pd.read_csv(EDU_PTS_CSV)
    print("[INFO] Notebook progress message.")
    print(df_pts.head())
    return df_pts


def get_edu_curve_for_sample(df_pts: pd.DataFrame, sample_type: str):
    """Archived notebook note for 01_dfo_child_elderly_intensity_curves.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sub = df_pts[df_pts["sample_type"] == sample_type].copy()
    if sub.empty:
        print("[INFO] Notebook progress message.")
        return None

    s_vals, beta_vals, se_vals, gamma, Cov_gamma = build_continuous_beta_from_points(sub)
    labels = sub["sev_label"].tolist()
    p_vals = sub["PValue"].to_numpy(dtype="float64")

    print("[INFO] Notebook progress message.")
    return {
        "s_vals": s_vals,
        "labels": labels,
        "p_vals": p_vals,
        "gamma": gamma,
        "Cov_gamma": Cov_gamma,
    }


def eval_poly_curve(gamma, Sigma, s_array):
    """Archived notebook note for 01_dfo_child_elderly_intensity_curves.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s_array = np.asarray(s_array, dtype="float64")
    deg = len(gamma) - 1
    Phi = np.vstack([s_array**k for k in range(deg + 1)]).T

    beta = Phi @ gamma
    var = np.einsum("ij,jk,ik->i", Phi, Sigma, Phi)
    var = np.maximum(var, 0.0)
    se = np.sqrt(var)

    ci_low = beta - 1.96 * se
    ci_high = beta + 1.96 * se
    return beta, se, ci_low, ci_high


# =============================================================================

def demean_two_fe(df: pd.DataFrame, cols, fe1, fe2) -> pd.DataFrame:
    """Archived notebook note for 01_dfo_child_elderly_intensity_curves.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()
    X = df[cols].astype("float64")

    g1_means = X.groupby(df[fe1]).transform("mean")
    g2_means = X.groupby(df[fe2]).transform("mean")
    mu = X.mean()

    X_dm = X - g1_means - g2_means + mu
    X_dm.columns = [f"{c}_dm" for c in cols]

    df = pd.concat([df, X_dm], axis=1)
    return df


def fe_reg_twoFE_city_cluster_fit(df: pd.DataFrame,
                                  y_col: str,
                                  x_cols,
                                  fe1: str,
                                  fe2: str,
                                  cluster_col: str):
    """Archived notebook note for 01_dfo_child_elderly_intensity_curves.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    cols_needed = [y_col] + list(x_cols) + [fe1, fe2, cluster_col]
    df = df.dropna(subset=cols_needed).copy()

    df = df[df[cluster_col].notna()].copy()
    if df.empty:
        raise ValueError("cluster_col 全缺失，无法回归。")

    df = demean_two_fe(df, [y_col] + list(x_cols), fe1=fe1, fe2=fe2)

    y = df[f"{y_col}_dm"].astype("float64")
    X_dm_cols = [f"{c}_dm" for c in x_cols]
    X = df[X_dm_cols].astype("float64")

    df["cluster_group"] = pd.Categorical(df[cluster_col]).codes
    groups = df["cluster_group"].to_numpy()

    model = sm.OLS(y, X)
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": groups})
    return fit


def prepare_health_panel() -> pd.DataFrame:
    """Archived notebook note for 01_dfo_child_elderly_intensity_curves.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print(f"[READ] HEALTH panel: {MERGED_PANEL}")
    if not MERGED_PANEL.exists():
        raise FileNotFoundError(f"健康 panel 文件不存在: {MERGED_PANEL}")
    df = pd.read_parquet(MERGED_PANEL)

    # Original notebook comment normalized for the public code archive.
    sev1_list, sev15_list, sev2_list = [], [], []
    for prefix in PREFIXES:
        for w in WINDOWS:
            c1 = f"share_DFO_sev1_{prefix}_{w}y"
            c15 = f"share_DFO_sev1_5_{prefix}_{w}y"
            c2 = f"share_DFO_sev2_{prefix}_{w}y"

            has_any = False
            if c1 in df.columns:
                sev1_list.append(pd.to_numeric(df[c1], errors="coerce"))
                has_any = True
            if c15 in df.columns:
                sev15_list.append(pd.to_numeric(df[c15], errors="coerce"))
                has_any = True
            if c2 in df.columns:
                sev2_list.append(pd.to_numeric(df[c2], errors="coerce"))
                has_any = True

            if has_any:
                print("[INFO] Notebook progress message.")
            else:
                print("[INFO] Notebook progress message.")

    if sev1_list:
        sev1_mat = pd.concat(sev1_list, axis=1)
        df["E1_agg"] = sev1_mat.mean(axis=1, skipna=True)
    else:
        df["E1_agg"] = 0.0

    if sev15_list:
        sev15_mat = pd.concat(sev15_list, axis=1)
        df["E15_agg"] = sev15_mat.mean(axis=1, skipna=True)
    else:
        df["E15_agg"] = 0.0

    if sev2_list:
        sev2_mat = pd.concat(sev2_list, axis=1)
        df["E2_agg"] = sev2_mat.mean(axis=1, skipna=True)
    else:
        df["E2_agg"] = 0.0

    df[["E1_agg", "E15_agg", "E2_agg"]] = (
        df[["E1_agg", "E15_agg", "E2_agg"]].fillna(0.0).astype("float64")
    )

    print("[INFO] Notebook progress message.")
    print(df[["E1_agg", "E15_agg", "E2_agg"]].describe())

    # Original notebook comment normalized for the public code archive.
    df["X0"] = df["E1_agg"] + df["E15_agg"] + df["E2_agg"]
    df["X1"] = 1.0 * df["E1_agg"] + 1.5 * df["E15_agg"] + 2.0 * df["E2_agg"]
    df["X2"] = 1.0**2 * df["E1_agg"] + 1.5**2 * df["E15_agg"] + 2.0**2 * df["E2_agg"]

    # Fixed-effects regression helper.
    df[Y_VAR_HEALTH] = pd.to_numeric(df[Y_VAR_HEALTH], errors="coerce")
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df[YEAR_COL] = pd.to_numeric(df[YEAR_COL], errors="coerce")

    df["age2"] = df["age"] ** 2
    df["prov_str"] = df[PROV_COL].astype(str).str.strip()
    df["prov_year"] = df["prov_str"] + "_" + df[YEAR_COL].astype(int).astype(str)

    if "urban_nbs" in df.columns:
        df["urban_nbs"] = pd.to_numeric(df["urban_nbs"], errors="coerce").fillna(0).astype(int)
        grp_urban = df.groupby(ID_COL)["urban_nbs"].mean()
        df = df.merge(
            (grp_urban > 0.5).astype(int).rename("urban_group"),
            on=ID_COL, how="left",
        )
    else:
        df["urban_group"] = 1

    # Original notebook comment normalized for the public code archive.
    waves_per_id = df.groupby(ID_COL)[YEAR_COL].nunique()
    keep_ids = waves_per_id[waves_per_id >= 2].index
    df = df[df[ID_COL].isin(keep_ids)].copy()

    df[CLUSTER_COL] = pd.to_numeric(df[CLUSTER_COL], errors="coerce")

    print(
        f"[INFO] health panel: IDs with >=2 waves: {df[ID_COL].nunique()}, "
        f"N={len(df)}, years={sorted(df[YEAR_COL].unique())}"
    )
    return df


def estimate_health_poly(df: pd.DataFrame, sample_name: str):
    """Archived notebook note for 01_dfo_child_elderly_intensity_curves.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sample_specs = {"all": None, "urban": 1, "rural": 0}
    if sample_name not in sample_specs:
        raise KeyError(f"未知 sample_name: {sample_name}")

    gval = sample_specs[sample_name]
    if gval is None:
        sub = df.copy()
    else:
        sub = df[df["urban_group"] == gval].copy()

    waves_sub = sub.groupby(ID_COL)[YEAR_COL].nunique()
    keep_ids_sub = waves_sub[waves_sub >= 2].index
    sub = sub[sub[ID_COL].isin(keep_ids_sub)].copy()

    if len(sub) < 100 or sub[CLUSTER_COL].nunique() < 10:
        print(
            f"[WARN] sample={sample_name} N 或 城市数过小 "
            f"(N={len(sub)}, N_city={sub[CLUSTER_COL].nunique()}), 跳过。"
        )
        return None

    x_cols = ["X0", "X1", "X2", "age", "age2"]
    fit = fe_reg_twoFE_city_cluster_fit(
        sub,
        y_col=Y_VAR_HEALTH,
        x_cols=x_cols,
        fe1=ID_COL,
        fe2="prov_year",
        cluster_col=CLUSTER_COL,
    )

    gamma_idx = [f"{c}_dm" for c in ["X0", "X1", "X2"]]
    missing_gamma = [g for g in gamma_idx if g not in fit.params.index]
    if missing_gamma:
        raise KeyError(f"回归结果中缺少参数列: {missing_gamma}")

    gamma_raw = fit.params[gamma_idx].to_numpy(dtype="float64")
    Sigma_raw = fit.cov_params().loc[gamma_idx, gamma_idx].to_numpy(dtype="float64")

    print(f"[INFO] HEALTH sample={sample_name}, γ(X0,X1,X2) = {gamma_raw}")

    # Original notebook comment normalized for the public code archive.
    gamma = gamma_raw
    Sigma = Sigma_raw

    return {
        "gamma": gamma,
        "Cov_gamma": Sigma,
        "fit": fit,
    }


# =============================================================================

def plot_severity_twinx(sample: str, edu_info: dict, health_info: dict):
    """Archived notebook note for 01_dfo_child_elderly_intensity_curves.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

    s_vals_edu = edu_info["s_vals"]
    labels_edu = edu_info["labels"]
    gamma_edu = edu_info["gamma"]
    Sigma_edu = edu_info["Cov_gamma"]

    gamma_h = health_info["gamma"]
    Sigma_h = health_info["Cov_gamma"]

    # Original notebook comment normalized for the public code archive.
    s_min, s_max = float(s_vals_edu.min()), float(s_vals_edu.max())
    s_grid = np.linspace(s_min, s_max, 201)

    # Original notebook comment normalized for the public code archive.
    beta_edu_grid, se_edu_grid, ci_edu_low, ci_edu_high = eval_poly_curve(
        gamma_edu, Sigma_edu, s_grid
    )
    # Original notebook comment normalized for the public code archive.
    beta_h_grid, se_h_grid, ci_h_low, ci_h_high = eval_poly_curve(
        gamma_h, Sigma_h, s_grid
    )

    # Original notebook comment normalized for the public code archive.
    beta_edu_pts, se_edu_pts, ci_edu_pts_low, ci_edu_pts_high = eval_poly_curve(
        gamma_edu, Sigma_edu, s_vals_edu
    )
    beta_h_pts, se_h_pts, ci_h_pts_low, ci_h_pts_high = eval_poly_curve(
        gamma_h, Sigma_h, s_vals_edu
    )

    # Original notebook comment normalized for the public code archive.
    p_edu = []
    for b, se in zip(beta_edu_pts, se_edu_pts):
        if se > 0:
            t_val = b / se
            p_val = 2.0 * (1.0 - norm_cdf(abs(t_val)))
        else:
            p_val = np.nan
        p_edu.append(p_val)
    p_edu = np.array(p_edu)

    p_h = []
    for b, se in zip(beta_h_pts, se_h_pts):
        if se > 0:
            t_val = b / se
            p_val = 2.0 * (1.0 - norm_cdf(abs(t_val)))
        else:
            p_val = np.nan
        p_h.append(p_val)
    p_h = np.array(p_h)

    # =============================================================================
    fig, ax1 = plt.subplots(figsize=(6.5, 4.5))
    ax2 = ax1.twinx()

    # Original notebook comment normalized for the public code archive.
    ax1.plot(
        s_grid,
        beta_edu_grid,
        label="教育 β(s)",
    )
    ax1.fill_between(
        s_grid,
        ci_edu_low,
        ci_edu_high,
        alpha=0.18,
    )
    ax1.errorbar(
        s_vals_edu,
        beta_edu_pts,
        yerr=[
            beta_edu_pts - ci_edu_pts_low,
            ci_edu_pts_high - beta_edu_pts,
        ],
        fmt="o",
        capsize=4,
        linestyle="none",
        label="教育代表点",
    )

    # Original notebook comment normalized for the public code archive.
    ax2.plot(
        s_grid,
        beta_h_grid,
        linestyle="--",
        label="健康 β(s)",
    )
    ax2.fill_between(
        s_grid,
        ci_h_low,
        ci_h_high,
        alpha=0.18,
    )
    ax2.errorbar(
        s_vals_edu,
        beta_h_pts,
        yerr=[
            beta_h_pts - ci_h_pts_low,
            ci_h_pts_high - beta_h_pts,
        ],
        fmt="s",
        capsize=4,
        linestyle="none",
        label="健康代表点",
    )

    # Original notebook comment normalized for the public code archive.
    vals1 = np.concatenate([
        ci_edu_low,
        ci_edu_high,
        ci_edu_pts_low,
        ci_edu_pts_high,
        np.array([0.0]),
    ])
    y1_min_raw = np.nanmin(vals1)
    y1_max_raw = np.nanmax(vals1)
    max_abs1 = float(max(abs(y1_min_raw), abs(y1_max_raw), 1e-6))
    pad_factor1 = 1.05
    y1_min = -max_abs1 * pad_factor1
    y1_max = max_abs1 * pad_factor1
    ax1.set_ylim(y1_min, y1_max)

    # Original notebook comment normalized for the public code archive.
    vals2 = np.concatenate([
        ci_h_low,
        ci_h_high,
        ci_h_pts_low,
        ci_h_pts_high,
        np.array([0.0]),
    ])
    y2_min_raw = np.nanmin(vals2)
    y2_max_raw = np.nanmax(vals2)
    max_abs2 = float(max(abs(y2_min_raw), abs(y2_max_raw), 1e-6))
    pad_factor2 = 1.05
    y2_min = -max_abs2 * pad_factor2
    y2_max = max_abs2 * pad_factor2
    ax2.set_ylim(y2_min, y2_max)

    # Original notebook comment normalized for the public code archive.
    y1_range = y1_max - y1_min
    offset1 = 0.04 * y1_range
    for sx, b, p in zip(s_vals_edu, beta_edu_pts, p_edu):
        star = stars_for_p(p)
        if star and np.isfinite(b):
            ax1.text(sx, b + offset1, star, ha="center", va="bottom", fontsize=10)

    # Original notebook comment normalized for the public code archive.
    y2_range = y2_max - y2_min
    offset2 = 0.04 * y2_range
    for sx, b, p in zip(s_vals_edu, beta_h_pts, p_h):
        star = stars_for_p(p)
        if star and np.isfinite(b):
            ax2.text(sx, b + offset2, star, ha="center", va="bottom", fontsize=10)

    # Original notebook comment normalized for the public code archive.
    ax1.set_xlim(s_min - 0.05, s_max + 0.05)
    ax1.set_xticks(s_vals_edu)
    xticklabels = []
    for lab, s in zip(labels_edu, s_vals_edu):
        if lab == "sev1":
            xticklabels.append("sev1\n(s=1)")
        elif lab == "sev1.5":
            xticklabels.append("sev1.5\n(s=1.5)")
        elif lab == "sev1.5+2":
            xticklabels.append(f"sev1.5+2\n(s≈{s:.2f})")
        else:
            xticklabels.append(f"{lab}\n(s≈{s:.2f})")
    ax1.set_xticklabels(xticklabels)

    # Original notebook comment normalized for the public code archive.
    ax1.axhline(0, linestyle="--", linewidth=1)

    ax1.set_xlabel("DFO 严重程度 s")
    ax1.set_ylabel("β(s) – 教育结果")
    ax2.set_ylabel("β(s) – 健康结果")

    ax1.set_title(
        "DFO 严重程度 s 的非线性效应曲线 β(s)\n"
        f"教育 vs 健康（sample={sample}，双 y 轴，0 对齐）"
    )

    # Original notebook comment normalized for the public code archive.
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="best")

    plt.tight_layout()

    if SAVE_FIG:
        fig_path = OUT_DIR_PLOTS / f"severity_edu_health_twinx_sample_{sample}.png"
        fig.savefig(fig_path, dpi=200)
        print("[INFO] Notebook progress message.")

    plt.show()
    plt.close(fig)


# ========= main =========

def main():
    # Original notebook comment normalized for the public code archive.
    df_edu_pts = load_edu_points()
    # Original notebook comment normalized for the public code archive.
    df_health = prepare_health_panel()

    for sample in SAMPLES:
        print(f"\n================ sample={sample} ================")
        edu_info = get_edu_curve_for_sample(df_edu_pts, sample_type=sample)
        if edu_info is None:
            print("[INFO] Notebook progress message.")
            continue

        health_info = estimate_health_poly(df_health, sample_name=sample)
        if health_info is None:
            print("[INFO] Notebook progress message.")
            continue

        plot_severity_twinx(sample, edu_info, health_info)

    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()
