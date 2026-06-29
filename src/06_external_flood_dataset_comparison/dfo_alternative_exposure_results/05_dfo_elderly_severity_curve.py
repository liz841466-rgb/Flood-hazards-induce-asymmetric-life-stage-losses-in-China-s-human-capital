#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 05_dfo_elderly_severity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 1
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 05_dfo_elderly_severity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
from math import erf, sqrt

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt

# =============================================================================

OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/DFO_city"
)
MERGED_PANEL = OUT_DIR / "charls_health_panel_60plus_with_index_DFO_5_10_20_30y.parquet"

ID_COL = "pid12"
Y_VAR = "health_index_z"
YEAR_COL = "year"
PROV_COL = "province"
CLUSTER_COL = "city_code"

# Original notebook comment normalized for the public code archive.
PREFIX = "centroid"
WINDOW = 10

SAMPLES = ["all", "urban", "rural"]


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

def demean_two_fe(df: pd.DataFrame, cols, fe1, fe2) -> pd.DataFrame:
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
    cols_needed = [y_col] + list(x_cols) + [fe1, fe2, cluster_col]
    df = df.dropna(subset=cols_needed).copy()
    df = df[df[cluster_col].notna()].copy()
    if df.empty:
        raise ValueError("cluster_col 全缺失，无法回归。")

    df = demean_two_fe(df, [y_col] + list(x_cols), fe1=fe1, fe2=fe2)

    y = df[f"{y_col}_dm"].to_numpy(dtype="float64")
    X = df[[f"{c}_dm" for c in x_cols]].to_numpy(dtype="float64")

    df["cluster_group"] = pd.Categorical(df[cluster_col]).codes
    groups = df["cluster_group"].to_numpy()

    model = sm.OLS(y, X)
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": groups})
    return fit


# =============================================================================

def run_and_plot_severity_curve():
    print(f"[READ] merged panel: {MERGED_PANEL}")
    df = pd.read_parquet(MERGED_PANEL)

    # Original notebook comment normalized for the public code archive.
    df[Y_VAR] = pd.to_numeric(df[Y_VAR], errors="coerce")
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df[YEAR_COL] = pd.to_numeric(df[YEAR_COL], errors="coerce")

    base_cols = [Y_VAR, "age", ID_COL, PROV_COL, CLUSTER_COL, YEAR_COL]
    df = df.dropna(subset=base_cols).copy()

    df["age2"] = df["age"] ** 2
    df["prov_str"] = df[PROV_COL].astype(str).str.strip()
    df["prov_year"] = df["prov_str"] + "_" + df[YEAR_COL].astype(int).astype(str)

    # Original notebook comment normalized for the public code archive.
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

    print(
        f"[INFO] IDs with >=2 waves: {df[ID_COL].nunique()}, "
        f"N={len(df)}, years={sorted(df[YEAR_COL].unique())}"
    )

    # Original notebook comment normalized for the public code archive.
    any_col = f"share_DFO_any_{PREFIX}_{WINDOW}y"
    sev15_col = f"share_DFO_sev1_5_{PREFIX}_{WINDOW}y"
    sev2_col = f"share_DFO_sev2_{PREFIX}_{WINDOW}y"

    for col in [any_col, sev15_col, sev2_col]:
        if col not in df.columns:
            raise KeyError(f"缺少列 {col}，请确认前面的 DFO 面板是否包含该规格。")

    df[any_col] = pd.to_numeric(df[any_col], errors="coerce")
    df[sev15_col] = pd.to_numeric(df[sev15_col], errors="coerce").fillna(0.0)
    df[sev2_col] = pd.to_numeric(df[sev2_col], errors="coerce").fillna(0.0)

    df["sev_total"] = df[sev15_col] + df[sev2_col]

    # Original notebook comment normalized for the public code archive.
    df["ratio"] = np.where(
        df[any_col] > 0,
        df["sev_total"] / df[any_col],
        0.0,
    )
    df["ratio2"] = df["ratio"] ** 2

    # Original notebook comment normalized for the public code archive.
    sample_specs = {"all": None, "urban": 1, "rural": 0}

    # Original notebook comment normalized for the public code archive.
    lambda_grid = np.linspace(0.0, 1.0, 101)

    for sample_name, gval in sample_specs.items():
        if gval is None:
            sub = df.copy()
        else:
            sub = df[df["urban_group"] == gval].copy()

        # Original notebook comment normalized for the public code archive.
        waves_sub = sub.groupby(ID_COL)[YEAR_COL].nunique()
        keep_ids_sub = waves_sub[waves_sub >= 2].index
        sub = sub[sub[ID_COL].isin(keep_ids_sub)].copy()

        if len(sub) < 100 or sub[CLUSTER_COL].nunique() < 10:
            print(
                f"[WARN] sample={sample_name} N 或 城市数过小 "
                f"(N={len(sub)}, N_city={sub[CLUSTER_COL].nunique()}), 跳过。"
            )
            continue

        # Original notebook comment normalized for the public code archive.
        any0 = float(sub[any_col].mean())
        print(f"[INFO] sample={sample_name}, any0 (mean {any_col}) = {any0:.4f}")

        x_cols = [
            any_col,
            "any_ratio",      # any * ratio
            "any_ratio2",     # any * ratio^2
            "age",
            "age2",
        ]

        # Original notebook comment normalized for the public code archive.
        sub["any_ratio"] = sub[any_col] * sub["ratio"]
        sub["any_ratio2"] = sub[any_col] * sub["ratio2"]

        fit = fe_reg_twoFE_city_cluster_fit(
            sub,
            y_col=Y_VAR,
            x_cols=x_cols,
            fe1=ID_COL,
            fe2="prov_year",
            cluster_col=CLUSTER_COL,
        )

        # =============================================================================
        beta = np.asarray(fit.params, dtype="float64")          # Original notebook comment normalized for the public code archive.
        cov = np.asarray(fit.cov_params(), dtype="float64")     # Original notebook comment normalized for the public code archive.

        idx = [0, 1, 2]  # Original notebook comment normalized for the public code archive.
        gamma = beta[idx]                          # (3,)
        Sigma = cov[np.ix_(idx, idx)]              # (3,3)

        # Original notebook comment normalized for the public code archive.
        beta_lambda = []
        se_lambda = []
        for lam in lambda_grid:
            v = np.array([any0, any0 * lam, any0 * lam**2], dtype="float64")
            b = float(v @ gamma)
            var_b = float(v @ Sigma @ v)
            var_b = max(var_b, 0.0)
            s = float(np.sqrt(var_b))
            beta_lambda.append(b)
            se_lambda.append(s)

        beta_lambda = np.array(beta_lambda)
        se_lambda = np.array(se_lambda)
        ci_low = beta_lambda - 1.96 * se_lambda
        ci_high = beta_lambda + 1.96 * se_lambda

        # Original notebook comment normalized for the public code archive.
        for lam in [0.0, 1.0]:
            v = np.array([any0, any0 * lam, any0 * lam**2], dtype="float64")
            b = float(v @ gamma)
            var_b = float(v @ Sigma @ v)
            var_b = max(var_b, 0.0)
            s = float(np.sqrt(var_b))
            if s > 0:
                t = b / s
                p = 2.0 * (1.0 - norm_cdf(abs(t)))
            else:
                p = np.nan
            print(f"[INFO] sample={sample_name}, λ={lam:.1f}: β={b:.4f}, p={p:.4g}")

        # Original notebook comment normalized for the public code archive.
        fig, ax = plt.subplots(figsize=(6, 4))

        ax.plot(lambda_grid, beta_lambda, label="β(λ) 估计")
        ax.fill_between(lambda_grid, ci_low, ci_high, alpha=0.25, label="95% CI")

        ax.axhline(0, linestyle="--", linewidth=1)
        ax.set_xlabel("严重洪水占比 λ（在总 DFO 暴露中的比例）")
        ax.set_ylabel("DFO 暴露对 health_index_z 的效应 β(λ)")
        ax.set_title(
            f"DFO 严重程度占比 λ 的非线性效应曲线\n"
            f"(prefix={PREFIX}, window={WINDOW}y, sample={sample_name})"
        )
        ax.set_xlim(0, 1)
        ax.legend()
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    run_and_plot_severity_curve()


# ------------------------------------------------------------------------------
# Notebook cell 4
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 05_dfo_elderly_severity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
from math import erf, sqrt

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt

# =============================================================================

OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/DFO_city"
)
MERGED_PANEL = OUT_DIR / "charls_health_panel_60plus_with_index_DFO_5_10_20_30y.parquet"

ID_COL = "pid12"
Y_VAR = "health_index_z"
YEAR_COL = "year"
PROV_COL = "province"
CLUSTER_COL = "city_code"

# Original notebook comment normalized for the public code archive.
PREFIXES = ["centroid", "area50", "full"]
WINDOWS = [5, 10, 20, 30]

SAMPLES = ["all", "urban", "rural"]


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

def demean_two_fe(df: pd.DataFrame, cols, fe1, fe2) -> pd.DataFrame:
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
    cols_needed = [y_col] + list(x_cols) + [fe1, fe2, cluster_col]
    df = df.dropna(subset=cols_needed).copy()
    df = df[df[cluster_col].notna()].copy()
    if df.empty:
        raise ValueError("cluster_col 全缺失，无法回归。")

    df = demean_two_fe(df, [y_col] + list(x_cols), fe1=fe1, fe2=fe2)

    y = df[f"{y_col}_dm"].to_numpy(dtype="float64")
    X = df[[f"{c}_dm" for c in x_cols]].to_numpy(dtype="float64")

    df["cluster_group"] = pd.Categorical(df[cluster_col]).codes
    groups = df["cluster_group"].to_numpy()

    model = sm.OLS(y, X)
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": groups})
    return fit


# =============================================================================

def run_and_plot_severity_curve_all_specs():
    print(f"[READ] merged panel: {MERGED_PANEL}")
    df = pd.read_parquet(MERGED_PANEL)

    # =============================================================================

    any_series_list = []
    sev_series_list = []

    for prefix in PREFIXES:
        for w in WINDOWS:
            any_col = f"share_DFO_any_{prefix}_{w}y"
            sev15_col = f"share_DFO_sev1_5_{prefix}_{w}y"
            sev2_col = f"share_DFO_sev2_{prefix}_{w}y"

            if any_col not in df.columns:
                print("[INFO] Notebook progress message.")
                continue

            # Original notebook comment normalized for the public code archive.
            if (sev15_col not in df.columns) and (sev2_col not in df.columns):
                print("[INFO] Notebook progress message.")
                continue

            s_any = pd.to_numeric(df[any_col], errors="coerce")

            s_sev = pd.Series(0.0, index=df.index, dtype="float64")
            if sev15_col in df.columns:
                s_sev = s_sev + pd.to_numeric(df[sev15_col], errors="coerce").fillna(0.0)
            if sev2_col in df.columns:
                s_sev = s_sev + pd.to_numeric(df[sev2_col], errors="coerce").fillna(0.0)

            any_series_list.append(s_any)
            sev_series_list.append(s_sev)

            print("[INFO] Notebook progress message.")

    if not any_series_list:
        raise RuntimeError("没有任何可用的 DFO 暴露规格用于聚合，请检查列名。")

    # Original notebook comment normalized for the public code archive.
    any_mat = pd.concat(any_series_list, axis=1)
    sev_mat = pd.concat(sev_series_list, axis=1)

    df["any_agg"] = any_mat.mean(axis=1)
    df["sev_total_agg"] = sev_mat.mean(axis=1)

    # Original notebook comment normalized for the public code archive.
    df["ratio"] = np.where(
        df["any_agg"] > 0,
        df["sev_total_agg"] / df["any_agg"],
        0.0,
    )
    df["ratio2"] = df["ratio"] ** 2

    print("[INFO] Notebook progress message.")
    print(df[["any_agg", "sev_total_agg", "ratio"]].describe())

    # =============================================================================

    df[Y_VAR] = pd.to_numeric(df[Y_VAR], errors="coerce")
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

    print(
        f"[INFO] IDs with >=2 waves: {df[ID_COL].nunique()}, "
        f"N={len(df)}, years={sorted(df[YEAR_COL].unique())}"
    )

    # City-level processing note.
    df[CLUSTER_COL] = pd.to_numeric(df[CLUSTER_COL], errors="coerce")

    # Original notebook comment normalized for the public code archive.
    df["any_ratio"] = df["any_agg"] * df["ratio"]
    df["any_ratio2"] = df["any_agg"] * df["ratio2"]

    # Original notebook comment normalized for the public code archive.
    lambda_grid = np.linspace(0.0, 1.0, 101)

    sample_specs = {"all": None, "urban": 1, "rural": 0}

    for sample_name, gval in sample_specs.items():
        if gval is None:
            sub = df.copy()
        else:
            sub = df[df["urban_group"] == gval].copy()

        # Original notebook comment normalized for the public code archive.
        waves_sub = sub.groupby(ID_COL)[YEAR_COL].nunique()
        keep_ids_sub = waves_sub[waves_sub >= 2].index
        sub = sub[sub[ID_COL].isin(keep_ids_sub)].copy()

        if len(sub) < 100 or sub[CLUSTER_COL].nunique() < 10:
            print(
                f"[WARN] sample={sample_name} N 或 城市数过小 "
                f"(N={len(sub)}, N_city={sub[CLUSTER_COL].nunique()}), 跳过。"
            )
            continue

        # Original notebook comment normalized for the public code archive.
        any0 = float(sub["any_agg"].mean())
        print(f"[INFO] sample={sample_name}, any0 (mean any_agg) = {any0:.4f}")

        x_cols = [
            "any_agg",
            "any_ratio",   # any_agg * ratio
            "any_ratio2",  # any_agg * ratio^2
            "age",
            "age2",
        ]

        fit = fe_reg_twoFE_city_cluster_fit(
            sub,
            y_col=Y_VAR,
            x_cols=x_cols,
            fe1=ID_COL,
            fe2="prov_year",
            cluster_col=CLUSTER_COL,
        )

        # Original notebook comment normalized for the public code archive.
        beta = np.asarray(fit.params, dtype="float64")
        cov = np.asarray(fit.cov_params(), dtype="float64")

        # Original notebook comment normalized for the public code archive.
        idx = [0, 1, 2]
        gamma = beta[idx]
        Sigma = cov[np.ix_(idx, idx)]

        # Original notebook comment normalized for the public code archive.
        beta_lambda = []
        se_lambda = []
        for lam in lambda_grid:
            v = np.array([any0, any0 * lam, any0 * lam**2], dtype="float64")
            b = float(v @ gamma)
            var_b = float(v @ Sigma @ v)
            var_b = max(var_b, 0.0)
            s = float(np.sqrt(var_b))
            beta_lambda.append(b)
            se_lambda.append(s)

        beta_lambda = np.array(beta_lambda)
        se_lambda = np.array(se_lambda)
        ci_low = beta_lambda - 1.96 * se_lambda
        ci_high = beta_lambda + 1.96 * se_lambda

        # Original notebook comment normalized for the public code archive.
        for lam in [0.0, 1.0]:
            v = np.array([any0, any0 * lam, any0 * lam**2], dtype="float64")
            b = float(v @ gamma)
            var_b = float(v @ Sigma @ v)
            var_b = max(var_b, 0.0)
            s = float(np.sqrt(var_b))
            if s > 0:
                t = b / s
                p = 2.0 * (1.0 - norm_cdf(abs(t)))
            else:
                p = np.nan
            print(f"[INFO] sample={sample_name}, λ={lam:.1f}: β={b:.4f}, p={p:.4g}")

        # =============================================================================
        fig, ax = plt.subplots(figsize=(6, 4))

        ax.plot(lambda_grid, beta_lambda, label="β(λ) 估计")
        ax.fill_between(lambda_grid, ci_low, ci_high, alpha=0.25, label="95% CI")

        ax.axhline(0, linestyle="--", linewidth=1)
        ax.set_xlabel("严重洪水占比 λ（在综合 DFO 暴露中的比例）")
        ax.set_ylabel("综合 DFO 暴露对 health_index_z 的效应 β(λ)")
        ax.set_title(
            "DFO 严重程度占比 λ 的非线性效应曲线\n"
            f"(已跨 prefix & window 聚合，sample={sample_name})"
        )
        ax.set_xlim(0, 1)
        ax.legend()
        plt.tight_layout()
        plt.show()



if __name__ == "__main__":
    run_and_plot_severity_curve_all_specs()


# ------------------------------------------------------------------------------
# Notebook cell 6
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 05_dfo_elderly_severity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
from math import erf, sqrt

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt

# =============================================================================

OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/DFO_city"
)
MERGED_PANEL = OUT_DIR / "charls_health_panel_60plus_with_index_DFO_5_10_20_30y.parquet"

ID_COL = "pid12"
Y_VAR = "health_index_z"
YEAR_COL = "year"
PROV_COL = "province"
CLUSTER_COL = "city_code"

# Original notebook comment normalized for the public code archive.
PREFIXES = ["centroid", "area50", "full"]
WINDOWS = [5, 10, 20, 30]

SAMPLES = ["all", "urban", "rural"]


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

def demean_two_fe(df: pd.DataFrame, cols, fe1, fe2) -> pd.DataFrame:
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
    cols_needed = [y_col] + list(x_cols) + [fe1, fe2, cluster_col]
    df = df.dropna(subset=cols_needed).copy()
    df = df[df[cluster_col].notna()].copy()
    if df.empty:
        raise ValueError("cluster_col 全缺失，无法回归。")

    df = demean_two_fe(df, [y_col] + list(x_cols), fe1=fe1, fe2=fe2)

    y = df[f"{y_col}_dm"].to_numpy(dtype="float64")
    X = df[[f"{c}_dm" for c in x_cols]].to_numpy(dtype="float64")

    df["cluster_group"] = pd.Categorical(df[cluster_col]).codes
    groups = df["cluster_group"].to_numpy()

    model = sm.OLS(y, X)
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": groups})
    return fit


# =============================================================================

def run_and_plot_severity_curve_weight_sev2():
    print(f"[READ] merged panel: {MERGED_PANEL}")
    df = pd.read_parquet(MERGED_PANEL)

    # =============================================================================

    any_series_list = []
    sev_series_list = []

    for prefix in PREFIXES:
        for w in WINDOWS:
            any_col = f"share_DFO_any_{prefix}_{w}y"
            sev15_col = f"share_DFO_sev1_5_{prefix}_{w}y"
            sev2_col = f"share_DFO_sev2_{prefix}_{w}y"

            if any_col not in df.columns:
                print("[INFO] Notebook progress message.")
                continue

            if (sev15_col not in df.columns) and (sev2_col not in df.columns):
                print("[INFO] Notebook progress message.")
                continue

            s_any = pd.to_numeric(df[any_col], errors="coerce")

            # Original notebook comment normalized for the public code archive.
            s_sev = pd.Series(0.0, index=df.index, dtype="float64")
            if sev15_col in df.columns:
                s_sev = s_sev + pd.to_numeric(df[sev15_col], errors="coerce").fillna(0.0)
            if sev2_col in df.columns:
                s_sev = s_sev + 2.0 * pd.to_numeric(df[sev2_col], errors="coerce").fillna(0.0)

            any_series_list.append(s_any)
            sev_series_list.append(s_sev)

            print("[INFO] Notebook progress message.")

    if not any_series_list:
        raise RuntimeError("没有任何可用的 DFO 暴露规格用于聚合，请检查列名。")

    any_mat = pd.concat(any_series_list, axis=1)
    sev_mat = pd.concat(sev_series_list, axis=1)

    df["any_agg"] = any_mat.mean(axis=1)
    df["sev_total_agg"] = sev_mat.mean(axis=1)

    # Original notebook comment normalized for the public code archive.
    df["ratio"] = np.where(
        df["any_agg"] > 0,
        df["sev_total_agg"] / df["any_agg"],
        0.0,
    )
    df["ratio2"] = df["ratio"] ** 2

    print("[INFO] Notebook progress message.")
    print(df[["any_agg", "sev_total_agg", "ratio"]].describe())

    # =============================================================================

    df[Y_VAR] = pd.to_numeric(df[Y_VAR], errors="coerce")
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

    waves_per_id = df.groupby(ID_COL)[YEAR_COL].nunique()
    keep_ids = waves_per_id[waves_per_id >= 2].index
    df = df[df[ID_COL].isin(keep_ids)].copy()

    print(
        f"[INFO] IDs with >=2 waves: {df[ID_COL].nunique()}, "
        f"N={len(df)}, years={sorted(df[YEAR_COL].unique())}"
    )

    df[CLUSTER_COL] = pd.to_numeric(df[CLUSTER_COL], errors="coerce")

    df["any_ratio"] = df["any_agg"] * df["ratio"]
    df["any_ratio2"] = df["any_agg"] * df["ratio2"]

    sample_specs = {"all": None, "urban": 1, "rural": 0}

    for sample_name, gval in sample_specs.items():
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
            continue

        # =============================================================================
        ratio_vals = sub["ratio"].to_numpy(dtype="float64")
        ratio_vals = ratio_vals[np.isfinite(ratio_vals)]
        if len(ratio_vals) >= 20:
            q01, q99 = np.quantile(ratio_vals, [0.01, 0.99])
        else:
            q01, q99 = 0.0, 1.0

        lambda_max = float(q99)
        if not np.isfinite(lambda_max) or lambda_max <= 0:
            lambda_max = 1.0  # Original notebook comment normalized for the public code archive.

        print(
            f"[INFO] sample={sample_name}, ratio 分布: "
            f"q1%={q01:.3f}, q99%={q99:.3f} => λ_max={lambda_max:.3f}"
        )

        lambda_grid = np.linspace(0.0, lambda_max, 101)

        any0 = float(sub["any_agg"].mean())
        print(f"[INFO] sample={sample_name}, any0 (mean any_agg) = {any0:.4f}")

        x_cols = ["any_agg", "any_ratio", "any_ratio2", "age", "age2"]

        fit = fe_reg_twoFE_city_cluster_fit(
            sub,
            y_col=Y_VAR,
            x_cols=x_cols,
            fe1=ID_COL,
            fe2="prov_year",
            cluster_col=CLUSTER_COL,
        )

        beta = np.asarray(fit.params, dtype="float64")
        cov = np.asarray(fit.cov_params(), dtype="float64")

        idx = [0, 1, 2]  # any_agg, any_ratio, any_ratio2
        gamma = beta[idx]
        Sigma = cov[np.ix_(idx, idx)]

        # Original notebook comment normalized for the public code archive.
        beta_lambda = []
        se_lambda = []
        for lam in lambda_grid:
            v = np.array([any0, any0 * lam, any0 * lam**2], dtype="float64")
            b = float(v @ gamma)
            var_b = float(v @ Sigma @ v)
            var_b = max(var_b, 0.0)
            s = float(np.sqrt(var_b))
            beta_lambda.append(b)
            se_lambda.append(s)

        beta_lambda = np.array(beta_lambda)
        se_lambda = np.array(se_lambda)
        ci_low = beta_lambda - 1.96 * se_lambda
        ci_high = beta_lambda + 1.96 * se_lambda

        # Original notebook comment normalized for the public code archive.
        for lam, label in [(0.0, "0%"), (lambda_max, "99% 分位")]:
            v = np.array([any0, any0 * lam, any0 * lam**2], dtype="float64")
            b = float(v @ gamma)
            var_b = float(v @ Sigma @ v)
            var_b = max(var_b, 0.0)
            s = float(np.sqrt(var_b))
            if s > 0:
                t = b / s
                p = 2.0 * (1.0 - norm_cdf(abs(t)))
            else:
                p = np.nan
            print(f"[INFO] sample={sample_name}, λ={label}: β={b:.4f}, p={p:.4g}")

        # =============================================================================
        fig, ax = plt.subplots(figsize=(6, 4))

        ax.plot(lambda_grid, beta_lambda, label="β(λ) 估计")
        ax.fill_between(lambda_grid, ci_low, ci_high, alpha=0.25, label="95% CI")

        ax.axhline(0, linestyle="--", linewidth=1)
        ax.set_xlabel("严重洪水强度指数 λ（sev2 权重=2）")
        ax.set_ylabel("综合 DFO 暴露对 health_index_z 的效应 β(λ)")
        ax.set_title(
            "DFO 严重洪水强度 λ 的非线性效应曲线\n"
            f"(跨 prefix & window 聚合，sev2 加倍权重，sample={sample_name})"
        )
        ax.set_xlim(0, lambda_max)
        ax.legend()

        # Original notebook comment normalized for the public code archive.
        ax.text(
            0.99, 0.02,
            f"λ_max ≈ ratio 99% 分位 ≈ {lambda_max:.2f}",
            transform=ax.transAxes,
            ha="right",
            va="bottom",
            fontsize=8
        )

        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    run_and_plot_severity_curve_weight_sev2()


# ------------------------------------------------------------------------------
# Notebook cell 10
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 05_dfo_elderly_severity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
from math import erf, sqrt

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt

# =============================================================================

OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/DFO_city"
)
MERGED_PANEL = OUT_DIR / "charls_health_panel_60plus_with_index_DFO_5_10_20_30y.parquet"

ID_COL = "pid12"
Y_VAR = "health_index_z"
YEAR_COL = "year"
PROV_COL = "province"
CLUSTER_COL = "city_code"

# Original notebook comment normalized for the public code archive.
PREFIXES = [ "area50", "full"]
WINDOWS = [5, 10, 20, 30]

SAMPLES = ["all", "urban", "rural"]


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

def demean_two_fe(df: pd.DataFrame, cols, fe1, fe2) -> pd.DataFrame:
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
    cols_needed = [y_col] + list(x_cols) + [fe1, fe2, cluster_col]
    df = df.dropna(subset=cols_needed).copy()
    df = df[df[cluster_col].notna()].copy()
    if df.empty:
        raise ValueError("cluster_col 全缺失，无法回归。")

    df = demean_two_fe(df, [y_col] + list(x_cols), fe1=fe1, fe2=fe2)

    y = df[f"{y_col}_dm"].to_numpy(dtype="float64")
    X = df[[f"{c}_dm" for c in x_cols]].to_numpy(dtype="float64")

    df["cluster_group"] = pd.Categorical(df[cluster_col]).codes
    groups = df["cluster_group"].to_numpy()

    model = sm.OLS(y, X)
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": groups})
    return fit


# =============================================================================

def run_and_plot_severity_curve_up_to_q99():
    print(f"[READ] merged panel: {MERGED_PANEL}")
    df = pd.read_parquet(MERGED_PANEL)

    # =============================================================================

    any_series_list = []
    sev_series_list = []

    for prefix in PREFIXES:
        for w in WINDOWS:
            any_col = f"share_DFO_any_{prefix}_{w}y"
            sev15_col = f"share_DFO_sev1_5_{prefix}_{w}y"
            sev2_col = f"share_DFO_sev2_{prefix}_{w}y"

            if any_col not in df.columns:
                print("[INFO] Notebook progress message.")
                continue

            if (sev15_col not in df.columns) and (sev2_col not in df.columns):
                print("[INFO] Notebook progress message.")
                continue

            s_any = pd.to_numeric(df[any_col], errors="coerce")

            s_sev = pd.Series(0.0, index=df.index, dtype="float64")
            if sev15_col in df.columns:
                s_sev = s_sev + pd.to_numeric(df[sev15_col], errors="coerce").fillna(0.0)
            if sev2_col in df.columns:
                s_sev = s_sev + pd.to_numeric(df[sev2_col], errors="coerce").fillna(0.0)

            any_series_list.append(s_any)
            sev_series_list.append(s_sev)

            print("[INFO] Notebook progress message.")

    if not any_series_list:
        raise RuntimeError("没有任何可用的 DFO 暴露规格用于聚合，请检查列名。")

    any_mat = pd.concat(any_series_list, axis=1)
    sev_mat = pd.concat(sev_series_list, axis=1)

    df["any_agg"] = any_mat.mean(axis=1)
    df["sev_total_agg"] = sev_mat.mean(axis=1)

    df["ratio"] = np.where(
        df["any_agg"] > 0,
        df["sev_total_agg"] / df["any_agg"],
        0.0,
    )
    df["ratio2"] = df["ratio"] ** 2

    print("[INFO] Notebook progress message.")
    print(df[["any_agg", "sev_total_agg", "ratio"]].describe())

    # =============================================================================

    df[Y_VAR] = pd.to_numeric(df[Y_VAR], errors="coerce")
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

    waves_per_id = df.groupby(ID_COL)[YEAR_COL].nunique()
    keep_ids = waves_per_id[waves_per_id >= 2].index
    df = df[df[ID_COL].isin(keep_ids)].copy()

    print(
        f"[INFO] IDs with >=2 waves: {df[ID_COL].nunique()}, "
        f"N={len(df)}, years={sorted(df[YEAR_COL].unique())}"
    )

    df[CLUSTER_COL] = pd.to_numeric(df[CLUSTER_COL], errors="coerce")

    df["any_ratio"] = df["any_agg"] * df["ratio"]
    df["any_ratio2"] = df["any_agg"] * df["ratio2"]

    sample_specs = {"all": None, "urban": 1, "rural": 0}

    for sample_name, gval in sample_specs.items():
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
            continue

        # =============================================================================
        ratio_vals = sub["ratio"].to_numpy(dtype="float64")
        ratio_vals = ratio_vals[np.isfinite(ratio_vals)]
        if len(ratio_vals) >= 20:
            q01, q99 = np.quantile(ratio_vals, [0.01, 0.99])
        else:
            q01, q99 = 0.0, 1.0

        lambda_max = float(q99)
        if not np.isfinite(lambda_max) or lambda_max <= 0:
            lambda_max = 1.0
        lambda_max = min(lambda_max, 1.0)   # Original notebook comment normalized for the public code archive.

        print(
            f"[INFO] sample={sample_name}, ratio 分布: "
            f"q1%={q01:.3f}, q99%={q99:.3f} => λ_max={lambda_max:.3f}"
        )

        # Original notebook comment normalized for the public code archive.
        lambda_grid = np.linspace(0.0, lambda_max, 101)

        # Original notebook comment normalized for the public code archive.
        any0 = float(sub["any_agg"].mean())
        print(f"[INFO] sample={sample_name}, any0 (mean any_agg) = {any0:.4f}")

        x_cols = ["any_agg", "any_ratio", "any_ratio2", "age", "age2"]

        fit = fe_reg_twoFE_city_cluster_fit(
            sub,
            y_col=Y_VAR,
            x_cols=x_cols,
            fe1=ID_COL,
            fe2="prov_year",
            cluster_col=CLUSTER_COL,
        )

        beta = np.asarray(fit.params, dtype="float64")
        cov = np.asarray(fit.cov_params(), dtype="float64")

        idx = [0, 1, 2]  # any_agg, any_ratio, any_ratio2
        gamma = beta[idx]
        Sigma = cov[np.ix_(idx, idx)]

        # Original notebook comment normalized for the public code archive.
        beta_lambda = []
        se_lambda = []
        for lam in lambda_grid:
            v = np.array([any0, any0 * lam, any0 * lam**2], dtype="float64")
            b = float(v @ gamma)
            var_b = float(v @ Sigma @ v)
            var_b = max(var_b, 0.0)
            s = float(np.sqrt(var_b))
            beta_lambda.append(b)
            se_lambda.append(s)

        beta_lambda = np.array(beta_lambda)
        se_lambda = np.array(se_lambda)
        ci_low = beta_lambda - 1.96 * se_lambda
        ci_high = beta_lambda + 1.96 * se_lambda

        # Original notebook comment normalized for the public code archive.
        for lam, label in [(0.0, "0%"), (lambda_max, "99% 分位")]:
            v = np.array([any0, any0 * lam, any0 * lam**2], dtype="float64")
            b = float(v @ gamma)
            var_b = float(v @ Sigma @ v)
            var_b = max(var_b, 0.0)
            s = float(np.sqrt(var_b))
            if s > 0:
                t = b / s
                p = 2.0 * (1.0 - norm_cdf(abs(t)))
            else:
                p = np.nan
            print(f"[INFO] sample={sample_name}, λ={label}: β={b:.4f}, p={p:.4g}")

        # =============================================================================
        fig, ax = plt.subplots(figsize=(6, 4))

        ax.plot(lambda_grid, beta_lambda, label="β(λ) 估计")
        ax.fill_between(lambda_grid, ci_low, ci_high, alpha=0.25, label="95% CI")

        ax.axhline(0, linestyle="--", linewidth=1)
        ax.set_xlabel("严重洪水占比 λ（在综合 DFO 暴露中的比例）")
        ax.set_ylabel("综合 DFO 暴露对 health_index_z 的效应 β(λ)")
        ax.set_title(
            "DFO 严重程度占比 λ 的非线性效应曲线\n"
            f"(已跨 prefix & window 聚合，只画到 ratio 的 99% 分位，sample={sample_name})"
        )
        ax.set_xlim(0, lambda_max)
        ax.legend()

        # Original notebook comment normalized for the public code archive.
        ax.text(
            0.99, 0.02,
            f"λ_max = ratio 99% 分位 ≈ {lambda_max:.2f}",
            transform=ax.transAxes,
            ha="right",
            va="bottom",
            fontsize=8
        )

        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    run_and_plot_severity_curve_up_to_q99()


# ------------------------------------------------------------------------------
# Notebook cell 13
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 05_dfo_elderly_severity_curve.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
from math import erf, sqrt

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt


# =============================================================================

# Original notebook comment normalized for the public code archive.
OUT_DIR = Path("/home/ll/jupyter_notebook/result/impact_assessment/older/DFO_city")
MERGED_PANEL = OUT_DIR / "charls_health_panel_60plus_with_index_DFO_5_10_20_30y.parquet"

# Original notebook comment normalized for the public code archive.
EXPORT_DIR = Path("/home/ll/jupyter_notebook/result/windows/DF0/1216DFO_EDU_HEALTH")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

# Original notebook comment normalized for the public code archive.
MERGED_PANEL_COPIED = EXPORT_DIR / "charls_health_panel_60plus_with_index_DFO_5_10_20_30y.parquet"
if MERGED_PANEL_COPIED.exists():
    MERGED_PANEL = MERGED_PANEL_COPIED

ID_COL = "pid12"
Y_VAR = "health_index_z"
YEAR_COL = "year"
PROV_COL = "province"
CLUSTER_COL = "city_code"

# Original notebook comment normalized for the public code archive.
PREFIXES = ["centroid", "area50", "full"]
WINDOWS = [5, 10, 20, 30]

SAMPLES = ["all", "urban", "rural"]


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


def demean_two_fe(df: pd.DataFrame, cols, fe1, fe2) -> pd.DataFrame:
    """Archived notebook note for 05_dfo_elderly_severity_curve.

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


def fe_reg_twoFE_city_cluster_fit(
    df: pd.DataFrame,
    y_col: str,
    x_cols,
    fe1: str,
    fe2: str,
    cluster_col: str
):
    """Archived notebook note for 05_dfo_elderly_severity_curve.

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


# =============================================================================

def run_and_plot_severity_poly_curve():
    print(f"[READ] merged panel: {MERGED_PANEL}")
    if not MERGED_PANEL.exists():
        raise FileNotFoundError(f"找不到 parquet：{MERGED_PANEL}")

    df = pd.read_parquet(MERGED_PANEL)

    # =============================================================================
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

    # =============================================================================
    df[Y_VAR] = pd.to_numeric(df[Y_VAR], errors="coerce")
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df[YEAR_COL] = pd.to_numeric(df[YEAR_COL], errors="coerce")

    df["age2"] = df["age"] ** 2
    df["prov_str"] = df[PROV_COL].astype(str).str.strip()
    # prov_year FE
    df["prov_year"] = df["prov_str"] + "_" + df[YEAR_COL].astype("Int64").astype(str)

    # urban_group
    if "urban_nbs" in df.columns:
        df["urban_nbs"] = pd.to_numeric(df["urban_nbs"], errors="coerce").fillna(0).astype(int)
        grp_urban = df.groupby(ID_COL)["urban_nbs"].mean()
        df = df.merge(
            (grp_urban > 0.5).astype(int).rename("urban_group"),
            on=ID_COL, how="left",
        )
    else:
        df["urban_group"] = 1  # Original notebook comment normalized for the public code archive.

    # Original notebook comment normalized for the public code archive.
    waves_per_id = df.groupby(ID_COL)[YEAR_COL].nunique()
    keep_ids = waves_per_id[waves_per_id >= 2].index
    df = df[df[ID_COL].isin(keep_ids)].copy()

    # cluster
    df[CLUSTER_COL] = pd.to_numeric(df[CLUSTER_COL], errors="coerce")

    print(
        f"[INFO] IDs with >=2 waves: {df[ID_COL].nunique()}, "
        f"N={len(df)}, years={sorted(df[YEAR_COL].dropna().unique())}"
    )

    sample_specs = {"all": None, "urban": 1, "rural": 0}

    # =============================================================================
    curve_rows = []
    point_rows = []

    # =============================================================================
    for sample_name, gval in sample_specs.items():
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
            continue

        # Original notebook comment normalized for the public code archive.
        sev_ge = sub["E15_agg"] + sub["E2_agg"]
        mask_ge = sev_ge > 0
        if mask_ge.any():
            s_mix_vals = (
                (1.5 * sub.loc[mask_ge, "E15_agg"] + 2.0 * sub.loc[mask_ge, "E2_agg"])
                / sev_ge[mask_ge]
            )
            s_mix = float(s_mix_vals.mean())
        else:
            s_mix = 1.75
        s_mix = min(max(s_mix, 1.5), 2.0)
        print("[INFO] Notebook progress message.")

        x_cols = ["X0", "X1", "X2", "age", "age2"]
        fit = fe_reg_twoFE_city_cluster_fit(
            sub,
            y_col=Y_VAR,
            x_cols=x_cols,
            fe1=ID_COL,
            fe2="prov_year",
            cluster_col=CLUSTER_COL,
        )

        gamma_idx = [f"{c}_dm" for c in ["X0", "X1", "X2"]]
        missing_gamma = [g for g in gamma_idx if g not in fit.params.index]
        if missing_gamma:
            raise KeyError(f"回归结果中缺少参数列: {missing_gamma}")

        gamma = fit.params[gamma_idx].to_numpy(dtype="float64")
        Sigma = fit.cov_params().loc[gamma_idx, gamma_idx].to_numpy(dtype="float64")

        print(f"[INFO] sample={sample_name}, γ estimates (X0,X1,X2):")
        print(fit.params[gamma_idx])

        # Original notebook comment normalized for the public code archive.
        s_points = np.array([1.0, 1.5, s_mix], dtype="float64")
        labels = ["sev1", "sev1.5", "sev1.5+2"]

        # Original notebook comment normalized for the public code archive.
        s_max = float(s_points.max())
        s_grid = np.linspace(1.0, s_max, 201)

        # Original notebook comment normalized for the public code archive.
        beta_s = np.empty_like(s_grid)
        se_s = np.empty_like(s_grid)
        for i, s in enumerate(s_grid):
            v = np.array([1.0, s, s**2], dtype="float64")
            b = float(v @ gamma)
            var_b = float(v @ Sigma @ v)
            var_b = max(var_b, 0.0)
            beta_s[i] = b
            se_s[i] = float(np.sqrt(var_b))

        ci_low = beta_s - 1.96 * se_s
        ci_high = beta_s + 1.96 * se_s

        # Original notebook comment normalized for the public code archive.
        beta_pts, se_pts, p_pts = [], [], []
        for s in s_points:
            v = np.array([1.0, s, s**2], dtype="float64")
            b = float(v @ gamma)
            var_b = float(v @ Sigma @ v)
            var_b = max(var_b, 0.0)
            se_b = float(np.sqrt(var_b))
            if se_b > 0:
                t_b = b / se_b
                p_b = 2.0 * (1.0 - norm_cdf(abs(t_b)))
            else:
                p_b = np.nan
            beta_pts.append(b)
            se_pts.append(se_b)
            p_pts.append(p_b)

        beta_pts = np.array(beta_pts, dtype="float64")
        se_pts = np.array(se_pts, dtype="float64")
        p_pts = np.array(p_pts, dtype="float64")
        ci_pts_low = beta_pts - 1.96 * se_pts
        ci_pts_high = beta_pts + 1.96 * se_pts

        # =============================================================================
        curve_rows.append(pd.DataFrame({
            "sample": sample_name,
            "s": s_grid,
            "beta": beta_s,
            "ci_low": ci_low,
            "ci_high": ci_high,
        }))

        point_rows.append(pd.DataFrame({
            "sample": sample_name,
            "sev_label": labels,
            "s": s_points,
            "beta": beta_pts,
            "ci_low": ci_pts_low,
            "ci_high": ci_pts_high,
            "pvalue": p_pts,
            "se": se_pts,
        }))

        # =============================================================================
        fig, ax = plt.subplots(figsize=(6, 4))

        ax.plot(s_grid, beta_s, label="β(s) 估计")
        ax.fill_between(s_grid, ci_low, ci_high, alpha=0.25, label="95% CI")

        ax.errorbar(
            s_points,
            beta_pts,
            yerr=[beta_pts - ci_pts_low, ci_pts_high - beta_pts],
            fmt="o",
            capsize=4,
            linestyle="none",
            color="black",
            label="sev1 / sev1.5 / sev1.5+2 代表点",
        )

        y_range = (np.nanmax(ci_high) - np.nanmin(ci_low))
        y_range = y_range if np.isfinite(y_range) and y_range > 0 else 1.0
        offset = 0.03 * y_range

        for sx, by, pp in zip(s_points, beta_pts, p_pts):
            star = stars_for_p(pp)
            if star:
                ax.text(sx, by + offset, star, ha="center", va="bottom", fontsize=10)

        ax.axhline(0, linestyle="--", linewidth=1)
        ax.set_xlim(1.0, s_max)
        ax.set_xlabel("DFO 严重程度 s（1=sev1, 1.5=sev1.5, 2=sev2）")
        ax.set_ylabel("边际效应 β(s)：对 health_index_z 的影响")

        ax.set_title(
            "DFO 严重程度 s 的非线性效应曲线 β(s)\n"
            f"(跨 prefix & window 聚合，sample={sample_name})"
        )

        ax.set_xticks(s_points)
        ax.set_xticklabels(
            [
                "sev1\n(中等洪水)",
                "sev1.5\n(较严重洪水)",
                f"sev1.5+2\n(平均 s≈{s_mix:.2f})",
            ]
        )

        ax.legend()
        plt.tight_layout()

        # =============================================================================
        out_png = EXPORT_DIR / f"severity_poly_health_sample_{sample_name}.png"
        plt.savefig(out_png, dpi=300)
        print(f"[OK] saved figure: {out_png}")

        plt.show()

    # =============================================================================
    if curve_rows:
        df_curve = pd.concat(curve_rows, ignore_index=True)
        out_curve = EXPORT_DIR / "severity_poly_health_curve.csv"
        df_curve.to_csv(out_curve, index=False)
        print(f"[OK] saved: {out_curve}")
    else:
        print("[INFO] Notebook progress message.")

    if point_rows:
        df_points = pd.concat(point_rows, ignore_index=True)
        out_points = EXPORT_DIR / "severity_poly_health_points.csv"
        df_points.to_csv(out_points, index=False)
        print(f"[OK] saved: {out_points}")
    else:
        print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    run_and_plot_severity_poly_curve()
