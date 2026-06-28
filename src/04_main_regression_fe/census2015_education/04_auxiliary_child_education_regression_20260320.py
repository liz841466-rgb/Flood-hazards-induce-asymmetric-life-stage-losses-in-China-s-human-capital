#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 04_auxiliary_child_education_regression_20260320.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 3
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_auxiliary_child_education_regression_20260320.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings
from math import erf, sqrt

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import statsmodels.api as sm
from pyfixest.estimation import feols

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)

# =========================================================
# 0. CONFIG
# =========================================================

DATA_PARQUET = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "edu_micro_2015_with_storage_BM_T2_5_10_20_50_100.parquet"
)

OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "statistics/storage_allT_betaT_BM_hs_any"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Original notebook comment normalized for the public code archive.
DEPVAR = "hs_any"

# Original notebook comment normalized for the public code archive.
T_LIST_DEFAULT = [2, 5, 10, 20, 50, 100]

# Original notebook comment normalized for the public code archive.
BIRTH_MIN, BIRTH_MAX = 1980, 2000
AGE_MIN, AGE_MAX     = 15, 35

ONLY_NON_MIGRANT = True
SAMPLES_URBAN = ["all", "rural", "urban"]

# Original notebook comment normalized for the public code archive.
CONTROL_FML = "C(M34) + C(M37) + C(M15) + C(M16)"

# Original notebook comment normalized for the public code archive.
SIG_LEVEL = 0.10

# Original notebook comment normalized for the public code archive.
OUT_LINEAR_CSV = OUT_DIR / f"storage_BM_{DEPVAR}_linear_allT.csv"
OUT_META_CSV   = OUT_DIR / f"storage_BM_{DEPVAR}_meta_params.csv"
OUT_GRID_CSV   = OUT_DIR / f"storage_BM_{DEPVAR}_betaT_grid_all_samples.csv"


# =========================================================
# 1. HELPERS
# =========================================================

def ensure_numeric(df: pd.DataFrame, cols):
    """Archived notebook note for 04_auxiliary_child_education_regression_20260320.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def build_is_urban_is_migrant(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 04_auxiliary_child_education_regression_20260320.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    # Original notebook comment normalized for the public code archive.
    if "is_urban" not in df.columns and "M2" in df.columns:
        suffix = pd.to_numeric(df["M2"], errors="coerce") % 100
        df["is_urban"] = np.where((suffix >= 1) & (suffix <= 20), 1, 0)
        df.loc[pd.isna(df["M2"]), "is_urban"] = np.nan

    # Original notebook comment normalized for the public code archive.
    if "is_migrant" not in df.columns and "M38" in df.columns:
        M38 = pd.to_numeric(df["M38"], errors="coerce")
        df["is_migrant"] = np.where(M38 == 1, 0, 1)
        df.loc[pd.isna(M38), "is_migrant"] = np.nan

    return df


def build_hs_any_if_needed(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 04_auxiliary_child_education_regression_20260320.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if DEPVAR not in df.columns:
        if "M51" not in df.columns:
            raise ValueError(
                f"数据中既没有 {DEPVAR}，也没有 M51，无法构造高中及以上教育程度变量。"
            )
        df["M51"] = pd.to_numeric(df["M51"], errors="coerce")
        df[DEPVAR] = np.where(df["M51"].ge(4), 1, 0)
        df.loc[df["M51"].isna(), DEPVAR] = np.nan

    # Original notebook comment normalized for the public code archive.
    df[DEPVAR] = pd.to_numeric(df[DEPVAR], errors="coerce")
    return df


def validate_depvar_binary(df: pd.DataFrame, depvar: str):
    """Archived notebook note for 04_auxiliary_child_education_regression_20260320.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    vals = pd.Series(df[depvar]).dropna().unique()
    bad = sorted(v for v in vals if v not in [0, 1, 0.0, 1.0])
    if bad:
        raise ValueError(
            f"{depvar} 检测到非 0/1 取值：{bad[:10]}。"
            # Notebook-export prose note omitted from the public code archive.
        )


def detect_T_list(df: pd.DataFrame):
    """Archived notebook note for 04_auxiliary_child_education_regression_20260320.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    ts = set()
    for c in df.columns:
        if c.startswith("share_flood_ge_T"):
            try:
                t = float(c.replace("share_flood_ge_T", ""))
                ts.add(t)
            except Exception:
                continue
    return sorted(ts) if ts else T_LIST_DEFAULT


def normalize_tidy(res: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 04_auxiliary_child_education_regression_20260320.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    res = res.reset_index()

    if res.columns[0] != "Term":
        res = res.rename(columns={res.columns[0]: "Term"})

    rename_map = {}
    for c in res.columns:
        lc = c.lower().replace(" ", "").replace(".", "")
        if lc in ["estimate", "coef", "coefficient"]:
            rename_map[c] = "Estimate"
        elif lc in ["stderr", "stderror", "std_error", "std"]:
            rename_map[c] = "StdError"
        elif lc in ["pvalue", "p>|t|", "pr(>|t|)", "p"]:
            rename_map[c] = "PValue"

    res = res.rename(columns=rename_map)

    # Original notebook comment normalized for the public code archive.
    if "StdError" not in res.columns:
        for c in res.columns:
            if "std" in c.lower():
                res = res.rename(columns={c: "StdError"})
                break

    if "PValue" not in res.columns:
        for c in res.columns:
            if c.lower().startswith("p"):
                res = res.rename(columns={c: "PValue"})
                break

    if "Estimate" not in res.columns:
        raise ValueError("tidy() 结果中未找到 Estimate 列。")

    return res


def get_nobs(fit, fallback_df: pd.DataFrame) -> int:
    """Archived notebook note for 04_auxiliary_child_education_regression_20260320.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    for attr in ["nobs", "_N", "N"]:
        if hasattr(fit, attr):
            try:
                v = getattr(fit, attr)
                if isinstance(v, (int, float)):
                    return int(v)
            except Exception:
                pass
    return int(len(fallback_df))


def norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))


def stars_for_p(p: float) -> str:
    """Archived notebook note for 04_auxiliary_child_education_regression_20260320.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
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


# =========================================================
# 2. SAMPLE PREPARATION
# =========================================================

def prepare_sample(df: pd.DataFrame, main_share: str, main_years: str, sample_urban: str):
    """Archived notebook note for 04_auxiliary_child_education_regression_20260320.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()

    # Original notebook comment normalized for the public code archive.
    num_cols = [
        "M2", "M38", "M52",
        "birth_year", "age_2015",
        "M34", "M37", "M15", "M16", "M3", "M51",
        main_share, main_years, DEPVAR
    ]
    df = ensure_numeric(df, num_cols)
    df = build_is_urban_is_migrant(df)
    df = build_hs_any_if_needed(df)

    # Original notebook comment normalized for the public code archive.
    mask = pd.Series(True, index=df.index)

    if ONLY_NON_MIGRANT:
        mask &= (df["is_migrant"] == 0)

    if sample_urban == "rural":
        mask &= (df["is_urban"] == 0)
    elif sample_urban == "urban":
        mask &= (df["is_urban"] == 1)
    elif sample_urban == "all":
        pass
    else:
        raise ValueError(f"未知 sample_urban: {sample_urban}")

    if "age_2015" in df.columns:
        mask &= df["age_2015"].between(AGE_MIN, AGE_MAX)

    mask &= df["birth_year"].between(BIRTH_MIN, BIRTH_MAX)

    dfm = df.loc[mask].copy()

    # Original notebook comment normalized for the public code archive.
    need_cols = ["M2", "birth_year", DEPVAR, main_share, main_years]
    dfm = dfm.dropna(subset=need_cols)

    # Original notebook comment normalized for the public code archive.
    validate_depvar_binary(dfm, DEPVAR)

    # Original notebook comment normalized for the public code archive.
    dfm["M2"] = pd.to_numeric(dfm["M2"], errors="coerce")
    dfm = dfm.dropna(subset=["M2"])
    dfm["M2"] = dfm["M2"].astype(np.int64)

    dfm["birth_year"] = pd.to_numeric(dfm["birth_year"], errors="coerce")
    dfm = dfm.dropna(subset=["birth_year"])
    dfm["birth_year"] = dfm["birth_year"].astype(np.int64)

    dfm["prov_code"] = (dfm["M2"] // 10000).astype(np.int64)
    dfm["prov_birth_fe"] = (
        dfm["prov_code"].astype(str) + "_" +
        dfm["birth_year"].astype(str)
    )
    dfm["birth_year_c"] = dfm["birth_year"] - 1995

    # Original notebook comment normalized for the public code archive.
    for c in ["M34", "M37", "M15", "M16"]:
        if c not in dfm.columns:
            raise ValueError(f"缺少控制变量列 {c}。")
        dfm[c] = pd.to_numeric(dfm[c], errors="coerce")
        dfm = dfm.dropna(subset=[c])
        dfm[c] = dfm[c].astype(int).astype("category")
        dfm[c] = dfm[c].cat.remove_unused_categories()

    # Original notebook comment normalized for the public code archive.
    dfm[DEPVAR] = pd.to_numeric(dfm[DEPVAR], errors="coerce")
    dfm = dfm.dropna(subset=[DEPVAR])
    dfm[DEPVAR] = dfm[DEPVAR].astype(float)

    # Original notebook comment normalized for the public code archive.
    dfm["years_main"] = pd.to_numeric(dfm[main_years], errors="coerce").fillna(0).astype(int)
    dfm["T_1"]   = (dfm["years_main"] == 1).astype(int)
    dfm["T_2_3"] = dfm["years_main"].between(2, 3).astype(int)
    dfm["T_ge4"] = (dfm["years_main"] >= 4).astype(int)

    return dfm.reset_index(drop=True)


# =========================================================
# 3. LINEAR REGRESSION FOR EACH T
# =========================================================

def run_linear(dfm: pd.DataFrame, main_share: str):
    """Archived notebook note for 04_auxiliary_child_education_regression_20260320.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    fml = (
        f"{DEPVAR} ~ {main_share} + {CONTROL_FML} + i(M2, birth_year_c) "
        f"| M2 + prov_birth_fe"
    )

    fit = feols(fml, data=dfm, vcov={"CRV1": "M2"})
    res = normalize_tidy(fit.tidy())

    key = res[res["Term"].astype(str).str.contains(main_share, na=False)].copy()
    if key.empty:
        return None

    row = key.iloc[0]
    est = float(row["Estimate"])
    se  = float(row.get("StdError", np.nan))
    pv  = float(row.get("PValue", np.nan))

    return {
        "Estimate": est,
        "StdError": se,
        "PValue": pv,
        "CI_low": est - 1.96 * se if np.isfinite(se) else np.nan,
        "CI_high": est + 1.96 * se if np.isfinite(se) else np.nan,
        "nobs": get_nobs(fit, dfm),
        "mean_depvar": float(dfm[DEPVAR].mean()),
    }


def run_storage_linear_allT():
    """Archived notebook note for 04_auxiliary_child_education_regression_20260320.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print(f"[STEP] Load data: {DATA_PARQUET}")
    df_all = pd.read_parquet(DATA_PARQUET)
    print(f"[INFO] Raw shape = {df_all.shape}")

    df_all = build_is_urban_is_migrant(df_all)
    df_all = build_hs_any_if_needed(df_all)

    T_list = detect_T_list(df_all)
    print(f"[INFO] Detected T list: {T_list}")

    all_rows = []

    for T in T_list:
        T_str = str(int(T)) if float(T).is_integer() else str(T)
        main_ret   = f"flood_ge_T{T_str}"
        main_share = f"share_{main_ret}"
        main_years = f"years_{main_ret}"

        if main_share not in df_all.columns or main_years not in df_all.columns:
            print(f"[SKIP] T={T_str}: missing {main_share} or {main_years}")
            continue

        print("\n====================================================")
        print(f"[PANEL] T = {T_str}")
        print("====================================================")

        for sample in SAMPLES_URBAN:
            dfm = prepare_sample(df_all, main_share, main_years, sample)
            print(f"[SAMPLE] {sample:>5s} | N = {len(dfm):,}")

            if len(dfm) == 0:
                continue

            lin = run_linear(dfm, main_share)
            if lin is None:
                continue

            all_rows.append({
                "T": float(T),
                "T_str": T_str,
                "sample": sample,
                "depvar": DEPVAR,
                "Term": main_share,
                "main_share": main_share,
                "main_years": main_years,
                "age_min": AGE_MIN,
                "age_max": AGE_MAX,
                "birth_min": BIRTH_MIN,
                "birth_max": BIRTH_MAX,
                "only_non_migrant": ONLY_NON_MIGRANT,
                **lin
            })

    df_lin = pd.DataFrame(all_rows)
    if df_lin.empty:
        print("[WARN] No regression results were produced.")
        return df_lin

    df_lin = df_lin.sort_values(["sample", "T"]).reset_index(drop=True)
    df_lin.to_csv(OUT_LINEAR_CSV, index=False, encoding="utf-8-sig")
    print(f"\n[DONE] Linear results saved: {OUT_LINEAR_CSV}")
    print(df_lin.head())

    return df_lin


# =========================================================
# 4. META-REGRESSION OF β(T)
# =========================================================

def fit_betaT_meta(sub: pd.DataFrame):
    """Archived notebook note for 04_auxiliary_child_education_regression_20260320.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sub = sub.sort_values("T").copy()

    T_vals = sub["T"].to_numpy(float)
    est = sub["Estimate"].to_numpy(float)
    se = sub["StdError"].to_numpy(float)

    # Original notebook comment normalized for the public code archive.
    var = se ** 2
    var[var <= 0] = 1e-12
    w = 1.0 / var

    logT = np.log(T_vals)

    # Original notebook comment normalized for the public code archive.
    if len(T_vals) >= 3:
        X = np.column_stack([np.ones_like(logT), logT, logT**2])
        degree = 2
    elif len(T_vals) == 2:
        X = np.column_stack([np.ones_like(logT), logT])
        degree = 1
    else:
        X = np.ones((len(logT), 1))
        degree = 0

    model = sm.WLS(est, X, weights=w)
    fit = model.fit()

    gamma = np.asarray(fit.params, dtype="float64")
    Sigma = np.asarray(fit.cov_params(), dtype="float64")

    return fit, degree, gamma, Sigma


def design_vec(log_t: float, degree: int) -> np.ndarray:
    """Archived notebook note for 04_auxiliary_child_education_regression_20260320.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if degree == 2:
        return np.array([1.0, log_t, log_t**2], dtype="float64")
    elif degree == 1:
        return np.array([1.0, log_t], dtype="float64")
    else:
        return np.array([1.0], dtype="float64")


def make_betaT_grid(sub: pd.DataFrame, degree: int, gamma: np.ndarray, Sigma: np.ndarray, n_grid=200):
    """Archived notebook note for 04_auxiliary_child_education_regression_20260320.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    T_vals = sub["T"].to_numpy(float)
    T_min, T_max = float(T_vals.min()), float(T_vals.max())

    logT_grid = np.linspace(np.log(T_min), np.log(T_max), n_grid)
    T_grid = np.exp(logT_grid)

    beta_grid = []
    se_grid = []

    for lt in logT_grid:
        v = design_vec(lt, degree)
        b = float(v @ gamma)
        var_b = float(v @ Sigma @ v)
        var_b = max(var_b, 0.0)

        beta_grid.append(b)
        se_grid.append(np.sqrt(var_b))

    beta_grid = np.asarray(beta_grid, dtype=float)
    se_grid = np.asarray(se_grid, dtype=float)

    out = pd.DataFrame({
        "T_grid": T_grid,
        "beta_grid": beta_grid,
        "se_grid": se_grid,
        "ci_low": beta_grid - 1.96 * se_grid,
        "ci_high": beta_grid + 1.96 * se_grid,
    })
    return out


def save_meta_and_grid(df_lin: pd.DataFrame):
    """Archived notebook note for 04_auxiliary_child_education_regression_20260320.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    meta_rows = []
    grid_all = []

    for sample in SAMPLES_URBAN:
        sub = df_lin[df_lin["sample"] == sample].copy()
        if sub.empty:
            continue

        fit, degree, gamma, Sigma = fit_betaT_meta(sub)

        # Original notebook comment normalized for the public code archive.
        row = {
            "sample": sample,
            "depvar": DEPVAR,
            "degree": degree,
            "n_points": len(sub),
            "rsquared": float(getattr(fit, "rsquared", np.nan)),
            "aic": float(getattr(fit, "aic", np.nan)),
            "bic": float(getattr(fit, "bic", np.nan)),
        }

        for i, val in enumerate(np.asarray(gamma).ravel()):
            row[f"gamma_{i}"] = float(val)

        se_params = np.sqrt(np.diag(np.asarray(Sigma, dtype=float)))
        for i, val in enumerate(np.asarray(se_params).ravel()):
            row[f"gamma_{i}_se"] = float(val)

        meta_rows.append(row)

        # Original notebook comment normalized for the public code archive.
        grid = make_betaT_grid(sub, degree, gamma, Sigma, n_grid=200)
        grid["sample"] = sample
        grid["depvar"] = DEPVAR
        grid_all.append(grid)

        print(f"\n[INFO] sample={sample} meta-regression summary:")
        print(fit.summary())

    df_meta = pd.DataFrame(meta_rows)
    df_grid = pd.concat(grid_all, ignore_index=True) if grid_all else pd.DataFrame()

    if not df_meta.empty:
        df_meta.to_csv(OUT_META_CSV, index=False, encoding="utf-8-sig")
        print(f"[DONE] Meta parameter table saved: {OUT_META_CSV}")

    if not df_grid.empty:
        df_grid.to_csv(OUT_GRID_CSV, index=False, encoding="utf-8-sig")
        print(f"[DONE] Smoothed beta(T) grid saved: {OUT_GRID_CSV}")

    return df_meta, df_grid


# =========================================================
# 5. PLOTTING
# =========================================================

def plot_beta_T_curve(df_lin: pd.DataFrame, sample: str):
    """Archived notebook note for 04_auxiliary_child_education_regression_20260320.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sub = df_lin[df_lin["sample"] == sample].copy()
    if sub.empty:
        print(f"[WARN] sample={sample} has no results; skip plotting.")
        return

    sub = sub.sort_values("T")

    fit, degree, gamma, Sigma = fit_betaT_meta(sub)
    grid = make_betaT_grid(sub, degree, gamma, Sigma, n_grid=200)

    T_vals = sub["T"].to_numpy(float)
    est = sub["Estimate"].to_numpy(float)
    ci_pts_low = sub["CI_low"].to_numpy(float)
    ci_pts_high = sub["CI_high"].to_numpy(float)
    p_vals = sub["PValue"].to_numpy(float)

    T_grid = grid["T_grid"].to_numpy(float)
    beta_grid = grid["beta_grid"].to_numpy(float)
    ci_low = grid["ci_low"].to_numpy(float)
    ci_high = grid["ci_high"].to_numpy(float)

    # =============================================================================
    fig, ax = plt.subplots(figsize=(6.8, 4.8))

    # Original notebook comment normalized for the public code archive.
    ax.plot(
        T_grid, beta_grid,
        color="black", linewidth=1.8,
        label="β(T) estimate"
    )

    # 95% CI
    ax.fill_between(
        T_grid, ci_low, ci_high,
        color="red", alpha=0.18,
        label="95% CI"
    )

    # Original notebook comment normalized for the public code archive.
    yerr = np.vstack([est - ci_pts_low, ci_pts_high - est])
    ax.errorbar(
        T_vals, est, yerr=yerr,
        fmt="o", capsize=4,
        color="black", linestyle="none",
        label="Point estimates"
    )

    # Original notebook comment normalized for the public code archive.
    y_min = np.nanmin([ci_low.min(), ci_pts_low.min()])
    y_max = np.nanmax([ci_high.max(), ci_pts_high.max()])

    if (not np.isfinite(y_min)) or (not np.isfinite(y_max)) or (y_max <= y_min):
        y_min, y_max = -0.10, 0.10

    pad = 0.06 * (y_max - y_min)
    offset = 0.04 * (y_max - y_min)

    for T, b, pv in zip(T_vals, est, p_vals):
        s = stars_for_p(pv)
        if s and np.isfinite(b):
            ax.text(
                T, b + offset, s,
                ha="center", va="bottom",
                fontsize=11
            )

    # Original notebook comment normalized for the public code archive.
    ax.set_xscale("log")
    ax.set_xlim(float(T_vals.min()) * 0.9, float(T_vals.max()) * 1.1)

    ticks = sorted(set(int(t) for t in T_vals))
    ax.set_xticks(ticks)
    ax.get_xaxis().set_major_formatter(mticker.ScalarFormatter())
    ax.get_xaxis().set_minor_formatter(mticker.NullFormatter())

    # Original notebook comment normalized for the public code archive.
    ax.axhline(0, linestyle="--", linewidth=1, color="gray")

    # Original notebook comment normalized for the public code archive.
    ax.set_ylim(y_min - pad, y_max + pad)

    # Original notebook comment normalized for the public code archive.
    ax.set_xlabel("Flood return period T (years, log scale)")
    ax.set_ylabel("β(T): effect of share_flood_ge_T on hs_any (percentage-point scale)")
    ax.set_title(
        "CaMa storage BM: severity-profile β(T) for high-school-or-above attainment\n"
        f"(sample = {sample})"
    )

    ax.legend(frameon=False)
    plt.tight_layout()

    fig_path = OUT_DIR / f"betaT_storage_BM_{DEPVAR}_sample_{sample}.png"
    plt.savefig(fig_path, dpi=250, bbox_inches="tight")
    plt.show()

    print(f"[DONE] Figure saved: {fig_path}")


# =========================================================
# 6. MAIN
# =========================================================

def main():
    # Original notebook comment normalized for the public code archive.
    df_lin = run_storage_linear_allT()
    if df_lin.empty:
        print("[WARN] No linear results; abort.")
        return

    # Original notebook comment normalized for the public code archive.
    save_meta_and_grid(df_lin)

    # Original notebook comment normalized for the public code archive.
    for sample in SAMPLES_URBAN:
        plot_beta_T_curve(df_lin, sample=sample)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 5
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_auxiliary_child_education_regression_20260320.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import statsmodels.api as sm

# =========================================================
# 0. PATHS
# =========================================================

OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "statistics/storage_allT_betaT_BM_hs_any"
)

LIN_CSV = OUT_DIR / "storage_BM_hs_any_linear_allT.csv"
SAMPLES = ["all", "rural", "urban"]


# =========================================================
# 1. HELPERS
# =========================================================

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


def fit_betaT_meta(sub: pd.DataFrame):
    sub = sub.sort_values("T").copy()

    T_vals = sub["T"].to_numpy(float)
    est = sub["Estimate"].to_numpy(float)
    se = sub["StdError"].to_numpy(float)

    var = se ** 2
    var[var <= 0] = 1e-12
    w = 1.0 / var

    logT = np.log(T_vals)

    if len(T_vals) >= 3:
        X = np.column_stack([np.ones_like(logT), logT, logT**2])
        degree = 2
    elif len(T_vals) == 2:
        X = np.column_stack([np.ones_like(logT), logT])
        degree = 1
    else:
        X = np.ones((len(logT), 1))
        degree = 0

    fit = sm.WLS(est, X, weights=w).fit()
    gamma = np.asarray(fit.params, dtype="float64")
    Sigma = np.asarray(fit.cov_params(), dtype="float64")

    return fit, degree, gamma, Sigma


def design_vec(log_t: float, degree: int) -> np.ndarray:
    if degree == 2:
        return np.array([1.0, log_t, log_t**2], dtype="float64")
    elif degree == 1:
        return np.array([1.0, log_t], dtype="float64")
    else:
        return np.array([1.0], dtype="float64")


def make_betaT_grid(sub: pd.DataFrame, degree: int, gamma: np.ndarray, Sigma: np.ndarray, n_grid=200):
    T_vals = sub["T"].to_numpy(float)
    T_min, T_max = float(T_vals.min()), float(T_vals.max())

    logT_grid = np.linspace(np.log(T_min), np.log(T_max), n_grid)
    T_grid = np.exp(logT_grid)

    beta_grid = []
    se_grid = []

    for lt in logT_grid:
        v = design_vec(lt, degree)
        b = float(v @ gamma)
        var_b = float(v @ Sigma @ v)
        var_b = max(var_b, 0.0)

        beta_grid.append(b)
        se_grid.append(np.sqrt(var_b))

    beta_grid = np.asarray(beta_grid, dtype=float)
    se_grid = np.asarray(se_grid, dtype=float)

    return pd.DataFrame({
        "T_grid": T_grid,
        "beta_grid": beta_grid,
        "ci_low": beta_grid - 1.96 * se_grid,
        "ci_high": beta_grid + 1.96 * se_grid,
    })


# =========================================================
# 2. PLOT
# =========================================================

def plot_beta_T_curve(df_lin: pd.DataFrame, sample: str):
    sub = df_lin[df_lin["sample"] == sample].copy()
    if sub.empty:
        print(f"[WARN] sample={sample} has no rows; skip.")
        return

    sub = sub.sort_values("T")

    fit, degree, gamma, Sigma = fit_betaT_meta(sub)
    grid = make_betaT_grid(sub, degree, gamma, Sigma, n_grid=200)

    print(f"\n[INFO] sample={sample} meta-regression summary:")
    print(fit.summary())

    T_vals = sub["T"].to_numpy(float)
    est = sub["Estimate"].to_numpy(float)
    ci_pts_low = sub["CI_low"].to_numpy(float)
    ci_pts_high = sub["CI_high"].to_numpy(float)
    p_vals = sub["PValue"].to_numpy(float)

    T_grid = grid["T_grid"].to_numpy(float)
    beta_grid = grid["beta_grid"].to_numpy(float)
    ci_low = grid["ci_low"].to_numpy(float)
    ci_high = grid["ci_high"].to_numpy(float)

    fig, ax = plt.subplots(figsize=(6.8, 4.8))

    ax.plot(T_grid, beta_grid, color="black", linewidth=1.8, label="β(T) estimate")
    ax.fill_between(T_grid, ci_low, ci_high, color="red", alpha=0.18, label="95% CI")

    yerr = np.vstack([est - ci_pts_low, ci_pts_high - est])
    ax.errorbar(
        T_vals, est, yerr=yerr,
        fmt="o", capsize=4,
        color="black", linestyle="none",
        label="Point estimates"
    )

    y_min = np.nanmin([ci_low.min(), ci_pts_low.min()])
    y_max = np.nanmax([ci_high.max(), ci_pts_high.max()])

    if (not np.isfinite(y_min)) or (not np.isfinite(y_max)) or (y_max <= y_min):
        y_min, y_max = -0.10, 0.10

    pad = 0.06 * (y_max - y_min)
    offset = 0.04 * (y_max - y_min)

    for T, b, pv in zip(T_vals, est, p_vals):
        s = stars_for_p(pv)
        if s and np.isfinite(b):
            ax.text(T, b + offset, s, ha="center", va="bottom", fontsize=11)

    ax.set_xscale("log")
    ax.set_xlim(float(T_vals.min()) * 0.9, float(T_vals.max()) * 1.1)

    ticks = sorted(set(int(t) for t in T_vals))
    ax.set_xticks(ticks)
    ax.get_xaxis().set_major_formatter(mticker.ScalarFormatter())
    ax.get_xaxis().set_minor_formatter(mticker.NullFormatter())

    ax.axhline(0, linestyle="--", linewidth=1, color="gray")
    ax.set_ylim(y_min - pad, y_max + pad)

    ax.set_xlabel("Flood return period T (years, log scale)")
    ax.set_ylabel("β(T): effect of share_flood_ge_T on hs_any (percentage-point scale)")
    ax.set_title(
        "CaMa storage BM: severity-profile β(T) for high-school-or-above attainment\n"
        f"(sample = {sample})"
    )

    ax.legend(frameon=False)
    plt.tight_layout()

    fig_path = OUT_DIR / f"betaT_storage_BM_hs_any_sample_{sample}_fromCSV.png"
    plt.savefig(fig_path, dpi=250, bbox_inches="tight")
    plt.show()

    print(f"[DONE] Saved figure: {fig_path}")


# =========================================================
# 3. MAIN
# =========================================================

if __name__ == "__main__":
    print(f"[READ] {LIN_CSV}")
    df_lin = pd.read_csv(LIN_CSV)

    # Original notebook comment normalized for the public code archive.
    for c in ["T", "Estimate", "StdError", "CI_low", "CI_high", "PValue", "sample"]:
        if c not in df_lin.columns:
            raise ValueError(f"线性结果表缺少列：{c}")

    df_lin["T"] = pd.to_numeric(df_lin["T"], errors="coerce")
    df_lin["Estimate"] = pd.to_numeric(df_lin["Estimate"], errors="coerce")
    df_lin["StdError"] = pd.to_numeric(df_lin["StdError"], errors="coerce")
    df_lin["CI_low"] = pd.to_numeric(df_lin["CI_low"], errors="coerce")
    df_lin["CI_high"] = pd.to_numeric(df_lin["CI_high"], errors="coerce")
    df_lin["PValue"] = pd.to_numeric(df_lin["PValue"], errors="coerce")

    df_lin = df_lin.dropna(subset=["T", "Estimate", "StdError"])

    for sample in SAMPLES:
        plot_beta_T_curve(df_lin, sample=sample)
