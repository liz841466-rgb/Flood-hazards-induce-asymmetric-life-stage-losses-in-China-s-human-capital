#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 03_health_dimension_and_disease_outcomes.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 9
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 03_health_dimension_and_disease_outcomes.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
from math import erf, sqrt
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


# =============================================================================
OUT_DIR = Path("/home/ll/jupyter_notebook/result/impact_assessment/older/flood_health_result")

# Original notebook comment normalized for the public code archive.
Y_VARS = ["health_phys", "health_mental", "health_social"]

# Fixed-effects regression helper.
RES_CSV_TEMPLATE = OUT_DIR / "fe_{yvar}_Tall_5_10_20_30y_pid12_provYearFE_cityCluster.csv"

SAMPLES = ["all", "rural", "urban"]
T_LIST = [2, 5, 10, 20, 50, 100]


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
def read_fe_result(yvar: str) -> pd.DataFrame:
    res_csv = Path(str(RES_CSV_TEMPLATE).format(yvar=yvar))
    print("[INFO] Notebook progress message.")
    if not res_csv.exists():
        raise FileNotFoundError(f"找不到结果文件：{res_csv}。请先用 code5/code4 跑出该 Y 的 FE 结果。")

    df = pd.read_csv(res_csv)

    needed = ["Y_var", "window", "T", "sample", "Estimate", "Std. Error", "N"]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise KeyError(f"结果文件缺少必要列: {missing}")

    # Original notebook comment normalized for the public code archive.
    df["window"] = pd.to_numeric(df["window"], errors="coerce")
    df["T"] = pd.to_numeric(df["T"], errors="coerce")
    df["Estimate"] = pd.to_numeric(df["Estimate"], errors="coerce")
    df["Std. Error"] = pd.to_numeric(df["Std. Error"], errors="coerce")
    df["N"] = pd.to_numeric(df["N"], errors="coerce")

    df = df.dropna(subset=["window", "T", "Estimate", "Std. Error", "sample"])
    df["window"] = df["window"].astype(int)
    df["T"] = df["T"].astype(int)

    # Original notebook comment normalized for the public code archive.
    df = df[df["Y_var"].astype(str) == str(yvar)].copy()
    if df.empty:
        # Original notebook comment normalized for the public code archive.
        print("[INFO] Notebook progress message.")
        df = pd.read_csv(res_csv)
        df["window"] = pd.to_numeric(df["window"], errors="coerce").astype("Int64")
        df["T"] = pd.to_numeric(df["T"], errors="coerce").astype("Int64")
        for col in ["Estimate", "Std. Error", "N"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.dropna(subset=["window", "T", "Estimate", "Std. Error", "sample"]).copy()
        df["window"] = df["window"].astype(int)
        df["T"] = df["T"].astype(int)
        df["Y_var"] = yvar  # Original notebook comment normalized for the public code archive.

    return df


def aggregate_across_window(df: pd.DataFrame, yvar: str) -> pd.DataFrame:
    """Archived notebook note for 03_health_dimension_and_disease_outcomes.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    group_cols = ["Y_var", "sample", "T"]

    def agg_one(g: pd.DataFrame) -> pd.Series:
        est = g["Estimate"].to_numpy(float)
        se = g["Std. Error"].to_numpy(float)

        var = se ** 2
        var[var <= 0] = 1e-12
        w = 1.0 / var

        beta_w = float(np.sum(w * est) / np.sum(w))
        var_w = float(1.0 / np.sum(w))
        se_w = float(np.sqrt(var_w))

        if se_w > 0:
            t_val = beta_w / se_w
            p_val = 2.0 * (1.0 - norm_cdf(abs(t_val)))
        else:
            t_val = np.nan
            p_val = np.nan

        ci_low = beta_w - 1.96 * se_w
        ci_high = beta_w + 1.96 * se_w

        win_list = sorted(g["window"].astype(int).unique().tolist())

        return pd.Series(
            {
                "Estimate": beta_w,
                "Std. Error": se_w,
                "t value": t_val,
                "Pr(>|t|)": p_val,
                "2.5%": ci_low,
                "97.5%": ci_high,
                "n_window": len(win_list),
                "window_list": ",".join(str(w) for w in win_list),
                "N_min": g["N"].min(),
                "N_max": g["N"].max(),
            }
        )

    df_T = (
        df.groupby(group_cols, as_index=False)
          .apply(agg_one)
          .reset_index(drop=True)
          .sort_values(["sample", "T"])
    )

    out_path = OUT_DIR / f"fe_{yvar}_Tall_windowAgg_over_T.csv"
    df_T.to_csv(out_path, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")
    return df_T


# =============================================================================
def plot_beta_T_curve(df_T: pd.DataFrame, yvar: str, sample: str):
    sub = df_T[(df_T["Y_var"] == yvar) & (df_T["sample"] == sample)].copy()
    sub = sub[sub["T"].isin(T_LIST)].copy()
    if sub.empty:
        print("[INFO] Notebook progress message.")
        return

    sub = sub.sort_values("T")
    T_vals = sub["T"].to_numpy(float)
    est = sub["Estimate"].to_numpy(float)
    se = sub["Std. Error"].to_numpy(float)

    var = se ** 2
    var[var <= 0] = 1e-12
    w = 1.0 / var

    # Original notebook comment normalized for the public code archive.
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

    print("[INFO] Notebook progress message.")
    print(fit.summary())

    # Original notebook comment normalized for the public code archive.
    T_min, T_max = float(T_vals.min()), float(T_vals.max())
    logT_grid = np.linspace(np.log(T_min), np.log(T_max), 200)
    T_grid = np.exp(logT_grid)

    def design_vec(lt: float) -> np.ndarray:
        if degree == 2:
            return np.array([1.0, lt, lt**2], dtype="float64")
        elif degree == 1:
            return np.array([1.0, lt], dtype="float64")
        else:
            return np.array([1.0], dtype="float64")

    beta_grid = []
    se_grid = []
    for lt in logT_grid:
        v = design_vec(lt)
        b = float(v @ gamma)
        var_b = float(v @ Sigma @ v)
        var_b = max(var_b, 0.0)
        beta_grid.append(b)
        se_grid.append(np.sqrt(var_b))

    beta_grid = np.array(beta_grid)
    se_grid = np.array(se_grid)
    ci_low = beta_grid - 1.96 * se_grid
    ci_high = beta_grid + 1.96 * se_grid

    # Original notebook comment normalized for the public code archive.
    ci_pts_low = est - 1.96 * se
    ci_pts_high = est + 1.96 * se
    p_vals = np.array([2.0 * (1.0 - norm_cdf(abs(b/s))) if s > 0 else np.nan for b, s in zip(est, se)])

    # =============================================================================
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(T_grid, beta_grid, label="β(T) 估计")
    ax.fill_between(T_grid, ci_low, ci_high, alpha=0.25, label="95% CI")

    ax.errorbar(
        T_vals, est,
        yerr=[est - ci_pts_low, ci_pts_high - est],
        fmt="o", linestyle="none", capsize=4, color="black",
        label="各返回期点（跨 window 聚合）"
    )

    y_min = min(ci_low.min(), ci_pts_low.min())
    y_max = max(ci_high.max(), ci_pts_high.max())
    pad = 0.05 * (y_max - y_min if y_max > y_min else 1.0)
    offset = 0.03 * (y_max - y_min if y_max > y_min else 1.0)

    for T, b, p in zip(T_vals, est, p_vals):
        star = stars_for_p(p)
        if star:
            ax.text(T, b + offset, star, ha="center", va="bottom", fontsize=10)

    ax.set_xscale("log")
    ax.set_xlim(T_min * 0.9, T_max * 1.1)
    ax.set_xticks(T_LIST)
    ax.get_xaxis().set_major_formatter(mticker.ScalarFormatter())
    ax.get_xaxis().set_minor_formatter(mticker.NullFormatter())

    ax.axhline(0, linestyle="--", linewidth=1)
    ax.set_ylim(y_min - pad, y_max + pad)

    ax.set_xlabel("洪水返回期 T（年）")
    ax.set_ylabel(f"β(T) 对 {yvar} 的影响")
    ax.set_title(f"洪水返回期 T 的非线性强度效应 β(T)\nY={yvar}, sample={sample}")

    ax.legend()
    plt.tight_layout()
    plt.show()


def main():
    for yvar in Y_VARS:
        df_fe = read_fe_result(yvar)
        # Original notebook comment normalized for the public code archive.
        df_fe = df_fe[df_fe["T"].isin(T_LIST)].copy()

        df_Tagg = aggregate_across_window(df_fe, yvar=yvar)
        # Original notebook comment normalized for the public code archive.
        df_Tagg["Y_var"] = yvar

        for sample in SAMPLES:
            plot_beta_T_curve(df_Tagg, yvar=yvar, sample=sample)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 11
# ------------------------------------------------------------------------------
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

OUT_DIR = Path("/home/ll/jupyter_notebook/result/impact_assessment/older/flood_health_result")
Y_VAR = "health_phys"  # Original notebook comment normalized for the public code archive.
SAMPLE = "all"         # all / rural / urban
RES_CSV = OUT_DIR / f"fe_{Y_VAR}_Tall_5_10_20_30y_pid12_provYearFE_cityCluster.csv"

T_LIST = [2, 5, 10, 20, 50, 100]
WINDOW_LIST = [5, 10, 20, 30]

def stars(p):
    if pd.isna(p): return ""
    if p < 0.001: return "****"
    if p < 0.05:  return "**"
    if p < 0.10:  return "*"
    return ""

df = pd.read_csv(RES_CSV)
df = df[(df["Y_var"] == Y_VAR) & (df["sample"] == SAMPLE)].copy()
df["T"] = pd.to_numeric(df["T"], errors="coerce").astype(int)
df["window"] = pd.to_numeric(df["window"], errors="coerce").astype(int)
for c in ["Estimate", "Std. Error", "Pr(>|t|)"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

df = df[df["T"].isin(T_LIST) & df["window"].isin(WINDOW_LIST)].copy()

# =============================================================================
plt.figure(figsize=(6,4))
for w in sorted(df["window"].unique()):
    sub = df[df["window"] == w].sort_values("T")
    T = sub["T"].values
    b = sub["Estimate"].values
    se = sub["Std. Error"].values
    plt.errorbar(T, b, yerr=1.96*se, fmt="o-", capsize=3, label=f"window={w}")

plt.axhline(0, linestyle="--", linewidth=1)
plt.xscale("log")
plt.xticks(T_LIST, [str(t) for t in T_LIST])
plt.gca().xaxis.set_minor_formatter(mticker.NullFormatter())
plt.xlabel("重现期 T（年）")
plt.ylabel(f"β 对 {Y_VAR} 的影响")
plt.title(f"{Y_VAR}: 不同时间窗口下 β(T)（sample={SAMPLE}）")
plt.legend()
plt.tight_layout()
plt.show()

# =============================================================================
mat = df.pivot_table(index="window", columns="T", values="Estimate", aggfunc="mean").reindex(WINDOW_LIST)
pmat = df.pivot_table(index="window", columns="T", values="Pr(>|t|)", aggfunc="mean").reindex(WINDOW_LIST)

plt.figure(figsize=(6,4))
im = plt.imshow(mat.values, aspect="auto")  # Original notebook comment normalized for the public code archive.
plt.colorbar(im, label="Estimate")

plt.xticks(range(len(mat.columns)), [str(t) for t in mat.columns])
plt.yticks(range(len(mat.index)), [str(w) for w in mat.index])
plt.xlabel("T（年）")
plt.ylabel("window（年）")
plt.title(f"{Y_VAR}: window×T 系数热力图（sample={SAMPLE}）")

# Original notebook comment normalized for the public code archive.
for i, w in enumerate(mat.index):
    for j, t in enumerate(mat.columns):
        st = stars(pmat.loc[w, t]) if (w in pmat.index and t in pmat.columns) else ""
        if st:
            plt.text(j, i, st, ha="center", va="center", fontsize=10)

plt.tight_layout()
plt.show()


# ------------------------------------------------------------------------------
# Notebook cell 14
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import shutil

# Fixed-effects regression helper.
OLD_OUT_DIR = Path("/home/ll/jupyter_notebook/result/impact_assessment/older/flood_health_result")

# Original notebook comment normalized for the public code archive.
NEW_OUT_DIR = Path("/home/ll/jupyter_notebook/result/windows/Gumbel/1218三维健康_disease")
NEW_OUT_DIR.mkdir(parents=True, exist_ok=True)

# Original notebook comment normalized for the public code archive.
Y_VARS = ["health_phys", "health_mental", "health_social"]

# Fixed-effects regression helper.
FE_NAME = "fe_{yvar}_Tall_5_10_20_30y_pid12_provYearFE_cityCluster.csv"

# Original notebook comment normalized for the public code archive.
AGG_NAME = "fe_{yvar}_Tall_windowAgg_over_T.csv"

for yvar in Y_VARS:
    src_fe = OLD_OUT_DIR / FE_NAME.format(yvar=yvar)
    dst_fe = NEW_OUT_DIR / src_fe.name

    if src_fe.exists():
        shutil.copy2(src_fe, dst_fe)
        print(f"[OK] copied: {src_fe} -> {dst_fe}")
    else:
        print(f"[MISS] not found: {src_fe}")

    # Original notebook comment normalized for the public code archive.
    src_agg = OLD_OUT_DIR / AGG_NAME.format(yvar=yvar)
    dst_agg = NEW_OUT_DIR / src_agg.name
    if src_agg.exists():
        shutil.copy2(src_agg, dst_agg)
        print(f"[OK] copied: {src_agg} -> {dst_agg}")

print("[INFO] Notebook progress message.")

# =========================
# Original notebook comment normalized for the public code archive.
# =========================
OUT_DIR = NEW_OUT_DIR
Y_VAR = "health_phys"  # Original notebook comment normalized for the public code archive.
SAMPLE = "all"         # all / rural / urban
RES_CSV = OUT_DIR / f"fe_{Y_VAR}_Tall_5_10_20_30y_pid12_provYearFE_cityCluster.csv"
print("[CHECK] RES_CSV =", RES_CSV)


# ------------------------------------------------------------------------------
# Notebook cell 16
# ------------------------------------------------------------------------------
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# =============================================================================
OUT_DIR = Path("/home/ll/jupyter_notebook/result/windows/Gumbel/1218三维健康_disease")

# Original notebook comment normalized for the public code archive.
Y_VARS = ["health_phys", "health_mental", "health_social"]
Y_LABEL = {
    "health_phys": "身体健康",
    "health_mental": "心理健康",
    "health_social": "社会适应",
}

SAMPLE = "all"  # all / rural / urban

T_LIST = [2, 5, 10, 20, 50, 100]
WINDOW_LIST = [5, 10, 20, 30]


def stars(p):
    if pd.isna(p):
        return ""
    if p < 0.001:
        return "****"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""


def load_fe_csv(y_var: str) -> pd.DataFrame:
    res_csv = OUT_DIR / f"fe_{y_var}_Tall_5_10_20_30y_pid12_provYearFE_cityCluster.csv"
    if not res_csv.exists():
        raise FileNotFoundError(f"找不到文件：{res_csv}")

    df = pd.read_csv(res_csv)

    # Original notebook comment normalized for the public code archive.
    df = df[(df["Y_var"] == y_var) & (df["sample"] == SAMPLE)].copy()

    # Original notebook comment normalized for the public code archive.
    df["T"] = pd.to_numeric(df["T"], errors="coerce")
    df["window"] = pd.to_numeric(df["window"], errors="coerce")
    for c in ["Estimate", "Std. Error", "Pr(>|t|)"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=["T", "window", "Estimate", "Std. Error"]).copy()
    df["T"] = df["T"].astype(int)
    df["window"] = df["window"].astype(int)

    # Original notebook comment normalized for the public code archive.
    df = df[df["T"].isin(T_LIST) & df["window"].isin(WINDOW_LIST)].copy()
    return df


def plot_line_and_heatmap(df: pd.DataFrame, y_var: str):
    yname = Y_LABEL.get(y_var, y_var)

    # =============================================================================
    plt.figure(figsize=(6, 4))

    for w in WINDOW_LIST:
        sub = df[df["window"] == w].sort_values("T")
        if sub.empty:
            continue
        T = sub["T"].values
        b = sub["Estimate"].values
        se = sub["Std. Error"].values

        plt.errorbar(T, b, yerr=1.96 * se, fmt="o-", capsize=3, label=f"window={w}")

    plt.axhline(0, linestyle="--", linewidth=1)
    plt.xscale("log")
    plt.xticks(T_LIST, [str(t) for t in T_LIST])
    plt.gca().xaxis.set_minor_formatter(mticker.NullFormatter())

    plt.xlabel("重现期 T（年）")
    plt.ylabel(f"β 对 {y_var} 的影响")
    plt.title(f"{yname}（{y_var}）：不同时间窗口下 β(T)（sample={SAMPLE}）")

    plt.legend()
    plt.tight_layout()
    plt.show()

    # =============================================================================
    mat = (
        df.pivot_table(index="window", columns="T", values="Estimate", aggfunc="mean")
          .reindex(index=WINDOW_LIST, columns=T_LIST)
    )
    pmat = (
        df.pivot_table(index="window", columns="T", values="Pr(>|t|)", aggfunc="mean")
          .reindex(index=WINDOW_LIST, columns=T_LIST)
    )

    plt.figure(figsize=(6, 4))
    im = plt.imshow(mat.values, aspect="auto")
    plt.colorbar(im, label="Estimate")

    plt.xticks(range(len(mat.columns)), [str(t) for t in mat.columns])
    plt.yticks(range(len(mat.index)), [str(w) for w in mat.index])

    plt.xlabel("T（年）")
    plt.ylabel("window（年）")
    plt.title(f"{yname}（{y_var}）：window×T 系数热力图（sample={SAMPLE}）")

    # Original notebook comment normalized for the public code archive.
    for i, w in enumerate(mat.index):
        for j, t in enumerate(mat.columns):
            p = pmat.loc[w, t]
            st = stars(p)
            if st:
                plt.text(j, i, st, ha="center", va="center", fontsize=10)

    plt.tight_layout()
    plt.show()


def main():
    for y_var in Y_VARS:
        try:
            df = load_fe_csv(y_var)
            if df.empty:
                print("[INFO] Notebook progress message.")
                continue
            plot_line_and_heatmap(df, y_var)
        except Exception as e:
            print(f"[ERROR] {y_var}: {e}")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 19
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm

# ======================
# Original notebook comment normalized for the public code archive.
# ======================
PANEL_MERGED = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/flood_health_result/"
    "charls_health_panel_60plus_with_index_Tall_5_10_20_30y.parquet"
)

OUT_DIR = Path("/home/ll/jupyter_notebook/result/windows/Gumbel/1218三维健康_disease")
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_CSV = OUT_DIR / "fe_components_Tall_5_10_20_30y_pid12_provYearFE_cityCluster_cityCluster.csv"

T_LIST = [2, 5, 10, 20, 50, 100]
WINDOW_LIST = [5, 10, 20, 30]

ID_COL = "pid12"
YEAR_COL = "year"
PROV_COL = "province"
CLUSTER_COL = "city_code"

SAMPLES = ["all", "urban", "rural"]   # Original notebook comment normalized for the public code archive.
MIN_N = 200
MIN_CITY = 10

# ======================
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# ======================

PHYS_VARS_HIGH_BAD = [
    "dress", "bathe", "eat",
    "bed_chair_transfer", "toilet",
    "walk100m", "walk1km", "stairs",
    "run1km", "lift5kg", "bend_kneel_squat",
    "pick_coin", "incontinence", "housework",
    "arm_raise", "sit_to_stand",
]
PHYS_VARS_HIGH_GOOD = [
    "disease",  # Original notebook comment normalized for the public code archive.
]

MENTAL_VARS_HIGH_BAD = [
    "cesd10_sum",
    "depress", "effort", "fear", "sleep", "hopeless",
    "life_satisfaction", "srh",
]
MENTAL_VARS_HIGH_GOOD = [
    "happy", "hope",
    # Original notebook comment normalized for the public code archive.
    "memory_disease",
    "mental_neuro_psych",
]

SOCIAL_VARS_HIGH_BAD = [
    "call_child_freq",
    "meet_child_freq",
    "social_freq",
    "social_activity",   # Original notebook comment normalized for the public code archive.
]
SOCIAL_VARS_HIGH_GOOD = [
    # Original notebook comment normalized for the public code archive.
    "annual_transfer",
]

# Original notebook comment normalized for the public code archive.
LOG1P_VARS = {"annual_transfer"}

# Original notebook comment normalized for the public code archive.
MISSING_CODES = {88, 89, 90, 96, 97, 98, 99, 888, 999, 9999}

def clean_numeric(series: pd.Series) -> pd.Series:
    x = pd.to_numeric(series, errors="coerce").astype("float64")
    x = x.where(~x.isin(MISSING_CODES), np.nan)
    return x

def scale_to_01(series: pd.Series, higher_better: bool) -> pd.Series:
    x = clean_numeric(series)
    vmin = x.min()
    vmax = x.max()
    if pd.isna(vmin) or pd.isna(vmax) or vmin == vmax:
        return pd.Series(np.nan, index=x.index, dtype="float64")
    if higher_better:
        z = (x - vmin) / (vmax - vmin)
    else:
        z = (vmax - x) / (vmax - vmin)
    return z.clip(0.0, 1.0)

def make_component_spec(df: pd.DataFrame):
    """Archived notebook note for 03_health_dimension_and_disease_outcomes.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    comps = []

    def add_list(var_list, higher_better, domain):
        for v in var_list:
            if v in df.columns:
                comps.append((v, f"{v}_norm2", higher_better, domain))

    add_list(PHYS_VARS_HIGH_BAD,   False, "phys")
    add_list(PHYS_VARS_HIGH_GOOD,  True,  "phys")
    add_list(MENTAL_VARS_HIGH_BAD, False, "mental")
    add_list(MENTAL_VARS_HIGH_GOOD,True,  "mental")
    add_list(SOCIAL_VARS_HIGH_BAD, False, "social")
    add_list(SOCIAL_VARS_HIGH_GOOD,True,  "social")

    # Original notebook comment normalized for the public code archive.
    seen = set()
    uniq = []
    for raw, norm, hb, dom in comps:
        if raw not in seen:
            uniq.append((raw, norm, hb, dom))
            seen.add(raw)
    return uniq

# ======================
# Fixed-effects regression helper.
# ======================

def demean_two_fe(df, cols, fe1, fe2):
    df = df.copy()
    g1 = df.groupby(fe1)
    g2 = df.groupby(fe2)
    mu = df[cols].mean()
    for col in cols:
        df[f"{col}_dm"] = (
            df[col]
            - g1[col].transform("mean")
            - g2[col].transform("mean")
            + mu[col]
        )
    return df

def fe_reg_twoFE_city_cluster(df, y_col, x_cols, fe1, fe2, cluster_col):
    need = [y_col] + x_cols + [fe1, fe2, cluster_col]
    df = df.dropna(subset=need).copy()
    df = df[df[cluster_col].notna()].copy()
    if df.empty:
        raise ValueError("有效样本为空。")

    df = demean_two_fe(df, [y_col] + x_cols, fe1=fe1, fe2=fe2)

    y = df[f"{y_col}_dm"].to_numpy()
    X = df[[f"{c}_dm" for c in x_cols]].to_numpy()

    df["_cluster_group"] = pd.Categorical(df[cluster_col]).codes
    groups = df["_cluster_group"].to_numpy()

    fit = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": groups})
    ci_low, ci_high = fit.conf_int().T

    res = pd.DataFrame(
        {
            "Estimate": fit.params,
            "Std. Error": fit.bse,
            "t value": fit.tvalues,
            "Pr(>|t|)": fit.pvalues,
            "2.5%": ci_low,
            "97.5%": ci_high,
        },
        index=x_cols,
    )
    return res

# ======================
# Original notebook comment normalized for the public code archive.
# ======================

def main():
    print(f"[READ] {PANEL_MERGED}")
    df = pd.read_parquet(PANEL_MERGED)

    # Original notebook comment normalized for the public code archive.
    for col in [ID_COL, PROV_COL, CLUSTER_COL, YEAR_COL, "age", "urban_nbs"]:
        if col not in df.columns:
            raise KeyError(f"面板缺少必要列：{col}")

    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df[YEAR_COL] = pd.to_numeric(df[YEAR_COL], errors="coerce")
    df = df.dropna(subset=[ID_COL, PROV_COL, CLUSTER_COL, YEAR_COL, "age", "urban_nbs"]).copy()

    df[ID_COL] = df[ID_COL].astype(str)
    df["age2"] = df["age"] ** 2

    # Fixed-effects regression helper.
    df["prov_str"] = df[PROV_COL].astype(str).str.strip()
    df["prov_year"] = df["prov_str"] + "_" + df[YEAR_COL].astype(int).astype(str)

    # Original notebook comment normalized for the public code archive.
    df["urban_nbs"] = pd.to_numeric(df["urban_nbs"], errors="coerce").fillna(0).astype(int)
    grp_urban = df.groupby(ID_COL)["urban_nbs"].mean()
    df = df.merge((grp_urban > 0.5).astype(int).rename("urban_group"),
                  on=ID_COL, how="left")

    # Original notebook comment normalized for the public code archive.
    waves_per_id = df.groupby(ID_COL)[YEAR_COL].nunique()
    keep_ids = waves_per_id[waves_per_id >= 2].index
    df = df[df[ID_COL].isin(keep_ids)].copy()
    print(f"[INFO] keep pid (>=2 waves): N_id={df[ID_COL].nunique()}, N={len(df)}")

    # Original notebook comment normalized for the public code archive.
    comps = make_component_spec(df)
    print(f"[INFO] component count (existing in df): {len(comps)}")
    if not comps:
        raise ValueError("没有任何组件变量在面板中匹配到。")

    # Original notebook comment normalized for the public code archive.
    for raw, norm, hb, dom in comps:
        x = df[raw]
        if raw in LOG1P_VARS:
            x = np.log1p(clean_numeric(x))
        df[norm] = scale_to_01(x, higher_better=hb)

    # Original notebook comment normalized for the public code archive.
    sample_specs = {
        "all": None,
        "urban": 1,
        "rural": 0,
    }
    sample_specs = {k: sample_specs[k] for k in SAMPLES}

    all_rows = []

    # Original notebook comment normalized for the public code archive.
    for raw, y_col, hb, dom in comps:
        # Original notebook comment normalized for the public code archive.
        if df[y_col].notna().sum() < MIN_N:
            print(f"[SKIP] {y_col}: too few non-missing")
            continue

        for window in WINDOW_LIST:
            exp_cols = {T: f"share_flood_T{T}_{window}y" for T in T_LIST}

            for T, exp_col in exp_cols.items():
                if exp_col not in df.columns:
                    continue

                for sample_name, gval in sample_specs.items():
                    sub = df.copy() if gval is None else df[df["urban_group"] == gval].copy()

                    # Original notebook comment normalized for the public code archive.
                    waves_sub = sub.groupby(ID_COL)[YEAR_COL].nunique()
                    keep_sub = waves_sub[waves_sub >= 2].index
                    sub = sub[sub[ID_COL].isin(keep_sub)].copy()

                    if len(sub) < MIN_N or sub[CLUSTER_COL].nunique() < MIN_CITY:
                        continue

                    x_cols = [exp_col, "age", "age2"]
                    try:
                        res = fe_reg_twoFE_city_cluster(
                            sub,
                            y_col=y_col,
                            x_cols=x_cols,
                            fe1=ID_COL,
                            fe2="prov_year",
                            cluster_col=CLUSTER_COL,
                        )
                    except Exception:
                        continue

                    r = res.loc[exp_col].copy()
                    r["outcome_raw"] = raw
                    r["outcome"] = y_col
                    r["domain"] = dom
                    r["higher_better"] = int(hb)
                    r["window"] = window
                    r["T"] = T
                    r["exposure"] = exp_col
                    r["sample"] = sample_name
                    r["N"] = len(sub)
                    r["N_id"] = sub[ID_COL].nunique()
                    r["N_city"] = sub[CLUSTER_COL].nunique()
                    r["N_year"] = sub[YEAR_COL].nunique()

                    all_rows.append(r)

        print(f"[DONE outcome] {y_col}")

    if not all_rows:
        raise ValueError("没有任何回归成功产出结果，请检查暴露列名、样本量、缺失情况。")

    out = pd.DataFrame(all_rows)
    out = out[
        [
            "domain", "outcome_raw", "outcome", "higher_better",
            "sample", "window", "T", "exposure",
            "Estimate", "Std. Error", "t value", "Pr(>|t|)", "2.5%", "97.5%",
            "N", "N_id", "N_city", "N_year",
        ]
    ].sort_values(["domain", "outcome", "sample", "window", "T"])

    out.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    print(f"[SAVE] {OUT_CSV}")
    print(out.head(10))

if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 20
# ------------------------------------------------------------------------------
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# =============================================================================
OUT_DIR = Path("/home/ll/jupyter_notebook/result/windows/Gumbel/1218三维健康_disease")
RES_CSV = OUT_DIR / "fe_components_Tall_5_10_20_30y_pid12_provYearFE_cityCluster_cityCluster.csv"

FIG_DIR = OUT_DIR / "fig_components"
FIG_DIR.mkdir(parents=True, exist_ok=True)

T_LIST = [2, 5, 10, 20, 50, 100]
WINDOW_LIST = [5, 10, 20, 30]
SAMPLES = ["all", "rural", "urban"]


def stars(p):
    if pd.isna(p): return ""
    if p < 0.001: return "****"
    if p < 0.05:  return "**"
    if p < 0.10:  return "*"
    return ""

def pretty_name(outcome: str) -> str:
    # Original notebook comment normalized for the public code archive.
    if isinstance(outcome, str) and outcome.endswith("_norm2"):
        return outcome[:-6]
    return str(outcome)

df = pd.read_csv(RES_CSV)
# Original notebook comment normalized for the public code archive.
for c in ["Estimate", "Std. Error", "Pr(>|t|)", "2.5%", "97.5%"]:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")
df["T"] = pd.to_numeric(df["T"], errors="coerce")
df["window"] = pd.to_numeric(df["window"], errors="coerce")

df = df.dropna(subset=["outcome", "sample", "window", "T", "Estimate", "Std. Error"]).copy()
df["T"] = df["T"].astype(int)
df["window"] = df["window"].astype(int)

# Original notebook comment normalized for the public code archive.
df = df[df["T"].isin(T_LIST) & df["window"].isin(WINDOW_LIST)].copy()

print("[INFO] loaded:", df.shape)
print("[INFO] outcomes:", df["outcome"].nunique(), "samples:", df["sample"].unique())


# =============================================================================
def plot_one_outcome(outcome: str, sample: str = "all", save: bool = True):
    sub = df[(df["outcome"] == outcome) & (df["sample"] == sample)].copy()
    if sub.empty:
        print(f"[WARN] empty: outcome={outcome}, sample={sample}")
        return

    title_name = pretty_name(outcome)

    # =============================================================================
    plt.figure(figsize=(6,4))
    for w in WINDOW_LIST:
        tmp = sub[sub["window"] == w].sort_values("T")
        if tmp.empty:
            continue
        T = tmp["T"].values
        b = tmp["Estimate"].values
        se = tmp["Std. Error"].values
        plt.errorbar(T, b, yerr=1.96*se, fmt="o-", capsize=3, label=f"window={w}")

    plt.axhline(0, linestyle="--", linewidth=1)
    plt.xscale("log")
    plt.xticks(T_LIST, [str(t) for t in T_LIST])
    plt.gca().xaxis.set_minor_formatter(mticker.NullFormatter())
    plt.xlabel("重现期 T（年）")
    plt.ylabel(f"β 对 {title_name} 的影响（0-1 方向统一后）")
    plt.title(f"{title_name}: 不同时间窗口下 β(T)（sample={sample}）")
    plt.legend()
    plt.tight_layout()

    if save:
        p = FIG_DIR / f"line_{outcome}_{sample}.png"
        plt.savefig(p, dpi=200)
        plt.close()
        print("[SAVE]", p)
    else:
        plt.show()

    # =============================================================================
    mat = (sub.pivot_table(index="window", columns="T", values="Estimate", aggfunc="mean")
              .reindex(index=WINDOW_LIST, columns=T_LIST))
    pmat = (sub.pivot_table(index="window", columns="T", values="Pr(>|t|)", aggfunc="mean")
               .reindex(index=WINDOW_LIST, columns=T_LIST))

    plt.figure(figsize=(6,4))
    im = plt.imshow(mat.values, aspect="auto")
    plt.colorbar(im, label="Estimate")
    plt.xticks(range(len(mat.columns)), [str(t) for t in mat.columns])
    plt.yticks(range(len(mat.index)), [str(w) for w in mat.index])
    plt.xlabel("T（年）")
    plt.ylabel("window（年）")
    plt.title(f"{title_name}: window×T 系数热力图（sample={sample}）")

    for i, w in enumerate(mat.index):
        for j, t in enumerate(mat.columns):
            p = pmat.loc[w, t] if (w in pmat.index and t in pmat.columns) else np.nan
            st = stars(p)
            if st:
                plt.text(j, i, st, ha="center", va="center", fontsize=10)

    plt.tight_layout()
    if save:
        p = FIG_DIR / f"heat_{outcome}_{sample}.png"
        plt.savefig(p, dpi=200)
        plt.close()
        print("[SAVE]", p)
    else:
        plt.show()


# =============================================================================
def plot_forest_topN(sample: str, window: int, T: int,
                     domain: str | None = None, topN: int = 20, save: bool = True):
    sub = df[(df["sample"] == sample) & (df["window"] == window) & (df["T"] == T)].copy()
    if domain is not None and "domain" in sub.columns:
        sub = sub[sub["domain"] == domain].copy()

    if sub.empty:
        print(f"[WARN] empty: sample={sample}, window={window}, T={T}, domain={domain}")
        return

    # Original notebook comment normalized for the public code archive.
    sub["abs_est"] = sub["Estimate"].abs()
    sub = sub.sort_values("abs_est", ascending=False).head(topN).copy()
    sub = sub.sort_values("Estimate", ascending=True)  # Original notebook comment normalized for the public code archive.

    y = np.arange(len(sub))
    est = sub["Estimate"].values
    se = sub["Std. Error"].values
    ci_low = est - 1.96*se
    ci_high = est + 1.96*se
    labels = [pretty_name(x) for x in sub["outcome"].tolist()]

    plt.figure(figsize=(7, max(4, 0.25*len(sub) + 1)))
    plt.hlines(y, ci_low, ci_high)
    plt.plot(est, y, marker="o", linestyle="none")
    plt.axvline(0, linestyle="--", linewidth=1)

    plt.yticks(y, labels)
    title_dom = domain if domain is not None else "all-domain"
    plt.xlabel("Estimate（95% CI）")
    plt.title(f"Top {topN} | sample={sample}, window={window}, T={T}, {title_dom}")
    plt.tight_layout()

    if save:
        p = FIG_DIR / f"forest_top{topN}_{title_dom}_{sample}_w{window}_T{T}.png"
        plt.savefig(p, dpi=200)
        plt.close()
        print("[SAVE]", p)
    else:
        plt.show()


# =============================================================================
def plot_heatmap_outcome_by_T(sample: str, window: int,
                             domain: str | None = None, topK: int = 40, save: bool = True):
    sub = df[(df["sample"] == sample) & (df["window"] == window)].copy()
    if domain is not None and "domain" in sub.columns:
        sub = sub[sub["domain"] == domain].copy()

    if sub.empty:
        print(f"[WARN] empty: sample={sample}, window={window}, domain={domain}")
        return

    mat = sub.pivot_table(index="outcome", columns="T", values="Estimate", aggfunc="mean")
    mat = mat.reindex(columns=T_LIST)

    # Original notebook comment normalized for the public code archive.
    score = mat.abs().mean(axis=1).sort_values(ascending=False)
    keep = score.head(topK).index
    mat = mat.loc[keep].copy()

    # Original notebook comment normalized for the public code archive.
    mat["__sort__"] = mat.abs().mean(axis=1)
    mat = mat.sort_values("__sort__", ascending=True).drop(columns="__sort__")

    plt.figure(figsize=(7, max(4, 0.25*len(mat) + 1)))
    im = plt.imshow(mat.values, aspect="auto")
    plt.colorbar(im, label="Estimate")

    plt.xticks(range(len(mat.columns)), [str(t) for t in mat.columns])
    plt.yticks(range(len(mat.index)), [pretty_name(o) for o in mat.index])

    title_dom = domain if domain is not None else "all-domain"
    plt.xlabel("T（年）")
    plt.ylabel("组件（TopK by mean |β|）")
    plt.title(f"组件×T 热力图 | sample={sample}, window={window}, {title_dom}")
    plt.tight_layout()

    if save:
        p = FIG_DIR / f"heat_outcome_byT_top{topK}_{title_dom}_{sample}_w{window}.png"
        plt.savefig(p, dpi=200)
        plt.close()
        print("[SAVE]", p)
    else:
        plt.show()


# =============================================================================
if __name__ == "__main__":
    # Original notebook comment normalized for the public code archive.
    plot_one_outcome("dress_norm2", sample="all", save=True)

    # Original notebook comment normalized for the public code archive.
    plot_forest_topN(sample="all", window=30, T=100, domain=None, topN=25, save=True)

    # Original notebook comment normalized for the public code archive.
    plot_heatmap_outcome_by_T(sample="all", window=30, domain=None, topK=40, save=True)

    # Original notebook comment normalized for the public code archive.
    # plot_forest_topN("all", 30, 100, domain="phys", topN=20, save=True)
    # plot_heatmap_outcome_by_T("all", 30, domain="mental", topK=30, save=True)


# ------------------------------------------------------------------------------
# Notebook cell 23
# ------------------------------------------------------------------------------
from pathlib import Path
import numpy as np
import pandas as pd

# =============================================================================
OUT_DIR = Path("/home/ll/jupyter_notebook/result/windows/Gumbel/1218三维健康_disease")
Y_VARS = ["health_phys", "health_mental", "health_social"]   # Original notebook comment normalized for the public code archive.
SAMPLES = ["all", "rural", "urban"]                          # Original notebook comment normalized for the public code archive.
T_LIST = [2, 5, 10, 20, 50, 100]
WINDOW_LIST = [5, 10, 20, 30]

# Original notebook comment normalized for the public code archive.
TOL = 1e-12


def monotonic_check(est_by_T: pd.Series, tol=TOL):
    """Archived notebook note for 03_health_dimension_and_disease_outcomes.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    Ts = est_by_T.index.to_list()
    ys = est_by_T.values.astype(float)

    diffs = np.diff(ys)

    nondec = np.all(diffs >= -tol)
    noninc = np.all(diffs <=  tol)

    if nondec and noninc:
        direction = "flat"
    elif nondec:
        direction = "nondecreasing"
    elif noninc:
        direction = "nonincreasing"
    else:
        direction = "nonmonotonic"

    violations = []
    if direction == "nonmonotonic":
        # Original notebook comment normalized for the public code archive.
        for i in range(len(diffs)):
            Ti, Tj = Ts[i], Ts[i+1]
            d = diffs[i]
            violations.append((Ti, Tj, float(d)))

    return direction, violations


def print_block(y_var: str, sample: str, window: int, sub: pd.DataFrame):
    # Original notebook comment normalized for the public code archive.
    sub = sub[sub["T"].isin(T_LIST)].copy()

    # Original notebook comment normalized for the public code archive.
    g = sub.groupby("T", as_index=True)["Estimate"].mean().reindex(T_LIST)

    # Original notebook comment normalized for the public code archive.
    n_avail = g.notna().sum()
    if n_avail < 3:
        print(f"  [SKIP] window={window}, sample={sample}: available T points={n_avail} < 3")
        return

    # Original notebook comment normalized for the public code archive.
    g2 = g.dropna()
    direction, violations = monotonic_check(g2)

    # Original notebook comment normalized for the public code archive.
    print(f"  window={window:>2} | sample={sample:<5} | monotonic={direction:<13} | nT={len(g2)}")

    # Original notebook comment normalized for the public code archive.
    if direction == "nonmonotonic":
        # Original notebook comment normalized for the public code archive.
        # Original notebook comment normalized for the public code archive.
        print("    Adjacent diffs (est[T_next]-est[T_prev]):")
        for Ti, Tj, d in violations:
            sign = "+" if d > 0 else ("-" if d < 0 else "0")
            print(f"      {Ti:>3}→{Tj:<3}: {d:+.6f} ({sign})")
        return

    # Original notebook comment normalized for the public code archive.
    def pick_row(Tv):
        r = sub[sub["T"] == Tv].copy()
        if r.empty:
            return None
        # Original notebook comment normalized for the public code archive.
        out = {
            "Estimate": float(r["Estimate"].mean()),
            "Std. Error": float(r["Std. Error"].mean()) if "Std. Error" in r.columns else np.nan,
            "CI_low": float(r["2.5%"].mean()) if "2.5%" in r.columns else np.nan,
            "CI_high": float(r["97.5%"].mean()) if "97.5%" in r.columns else np.nan,
            "p": float(r["Pr(>|t|)"].mean()) if "Pr(>|t|)" in r.columns else np.nan,
        }
        return out

    r2 = pick_row(2)
    r100 = pick_row(100)

    if (r2 is None) or (r100 is None):
        print("    [INFO] Monotonic, but T=2 or T=100 missing -> cannot print dumbbell endpoints.")
        return

    print("    Dumbbell endpoints (T=2 vs T=100):")
    print(f"      T=  2 : beta={r2['Estimate']:+.6f},  CI=[{r2['CI_low']:+.6f}, {r2['CI_high']:+.6f}],  p={r2['p']}")
    print(f"      T=100: beta={r100['Estimate']:+.6f}, CI=[{r100['CI_low']:+.6f}, {r100['CI_high']:+.6f}], p={r100['p']}")


def main():
    for y_var in Y_VARS:
        res_csv = OUT_DIR / f"fe_{y_var}_Tall_5_10_20_30y_pid12_provYearFE_cityCluster.csv"
        if not res_csv.exists():
            print(f"[MISS] {res_csv}")
            continue

        df = pd.read_csv(res_csv)

        # Original notebook comment normalized for the public code archive.
        df["T"] = pd.to_numeric(df["T"], errors="coerce")
        df["window"] = pd.to_numeric(df["window"], errors="coerce")
        for c in ["Estimate", "Std. Error", "Pr(>|t|)", "2.5%", "97.5%"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")

        df = df.dropna(subset=["T", "window", "Estimate", "sample"]).copy()
        df["T"] = df["T"].astype(int)
        df["window"] = df["window"].astype(int)

        # Original notebook comment normalized for the public code archive.
        if "Y_var" in df.columns:
            df = df[df["Y_var"].astype(str) == y_var].copy()

        print("\n" + "=" * 80)
        print(f"[CHECK] y_var={y_var} | file={res_csv.name}")

        for sample in SAMPLES:
            print(f"\n  --- sample={sample} ---")
            d1 = df[df["sample"] == sample].copy()
            if d1.empty:
                print("  [SKIP] no rows")
                continue

            for window in WINDOW_LIST:
                sub = d1[d1["window"] == window].copy()
                if sub.empty:
                    print(f"  [SKIP] window={window}, sample={sample}: no rows")
                    continue
                print_block(y_var, sample, window, sub)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 24
# ------------------------------------------------------------------------------
from pathlib import Path
import numpy as np
import pandas as pd

OUT_DIR = Path("/home/ll/jupyter_notebook/result/windows/Gumbel/1218三维健康_disease")

Y_VARS = ["health_phys", "health_mental", "health_social"]
SAMPLES = ["all", "rural", "urban"]
T_LIST = [2, 5, 10, 20, 50, 100]
WINDOW_LIST = [5, 10, 20, 30]

# Original notebook comment normalized for the public code archive.
Z_CUT = 1.96   # Original notebook comment normalized for the public code archive.
TOL = 1e-12    # Original notebook comment normalized for the public code archive.

def classify_point_monotone(betas, tol=TOL):
    """Archived notebook note for 03_health_dimension_and_disease_outcomes.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    y = np.asarray(betas, float)
    diffs = np.diff(y)
    nondec = np.all(diffs >= -tol)
    noninc = np.all(diffs <=  tol)
    if nondec and noninc: return "flat"
    if nondec: return "nondecreasing"
    if noninc: return "nonincreasing"
    return "nonmonotonic"

def check_monotone_significant(Ts, betas, ses, direction="nonincreasing", z_cut=Z_CUT, tol=TOL):
    """Archived notebook note for 03_health_dimension_and_disease_outcomes.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    Ts = list(Ts)
    b = np.asarray(betas, float)
    se = np.asarray(ses, float)

    viol = []
    for i in range(len(Ts)-1):
        d = b[i+1] - b[i]
        se_diff = np.sqrt(se[i]**2 + se[i+1]**2)
        if not np.isfinite(se_diff) or se_diff <= 0:
            z = np.nan
        else:
            z = d / se_diff

        if direction == "nonincreasing":
            # Original notebook comment normalized for the public code archive.
            if (d > tol) and np.isfinite(z) and (z > z_cut):
                viol.append((Ts[i], Ts[i+1], float(d), float(z)))
        else:
            # Original notebook comment normalized for the public code archive.
            if (d < -tol) and np.isfinite(z) and (abs(z) > z_cut):
                viol.append((Ts[i], Ts[i+1], float(d), float(z)))

    return (len(viol) == 0), viol

def print_endpoints(Ts, betas, ses):
    # Original notebook comment normalized for the public code archive.
    mp = {int(T): (float(b), float(s)) for T, b, s in zip(Ts, betas, ses)}
    if 2 in mp and 100 in mp:
        b2, s2 = mp[2]
        b100, s100 = mp[100]
        print(f"      endpoints: T=2  beta={b2:+.6f},  CI=[{b2-1.96*s2:+.6f},{b2+1.96*s2:+.6f}]")
        print(f"                 T=100 beta={b100:+.6f}, CI=[{b100-1.96*s100:+.6f},{b100+1.96*s100:+.6f}]")
    else:
        print("      endpoints: missing T=2 or T=100")

def main():
    for y_var in Y_VARS:
        f = OUT_DIR / f"fe_{y_var}_Tall_5_10_20_30y_pid12_provYearFE_cityCluster.csv"
        if not f.exists():
            print(f"[MISS] {f}")
            continue

        df = pd.read_csv(f)
        if "Y_var" in df.columns:
            df = df[df["Y_var"].astype(str) == y_var].copy()

        df["T"] = pd.to_numeric(df["T"], errors="coerce")
        df["window"] = pd.to_numeric(df["window"], errors="coerce")
        for c in ["Estimate", "Std. Error"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")

        df = df.dropna(subset=["sample", "window", "T", "Estimate", "Std. Error"]).copy()
        df["T"] = df["T"].astype(int)
        df["window"] = df["window"].astype(int)
        df = df[df["T"].isin(T_LIST) & df["window"].isin(WINDOW_LIST)].copy()

        print("\n" + "="*90)
        print(f"[CHECK-SIG] y_var={y_var} | Z_CUT={Z_CUT} | file={f.name}")

        for sample in SAMPLES:
            print(f"\n  --- sample={sample} ---")
            d1 = df[df["sample"] == sample].copy()
            if d1.empty:
                print("  [SKIP] no rows")
                continue

            for window in WINDOW_LIST:
                sub = d1[d1["window"] == window].copy()
                if sub.empty:
                    print(f"  window={window:>2}: [SKIP] no rows")
                    continue

                sub = sub.groupby("T", as_index=False)[["Estimate","Std. Error"]].mean()
                sub = sub[sub["T"].isin(T_LIST)].copy()
                sub = sub.sort_values("T")
                if len(sub) < 3:
                    print(f"  window={window:>2}: [SKIP] nT={len(sub)} < 3")
                    continue

                Ts = sub["T"].tolist()
                betas = sub["Estimate"].to_numpy(float)
                ses = sub["Std. Error"].to_numpy(float)

                # Original notebook comment normalized for the public code archive.
                point_cls = classify_point_monotone(betas)

                # Original notebook comment normalized for the public code archive.
                ok_sig, viol = check_monotone_significant(Ts, betas, ses, direction="nonincreasing", z_cut=Z_CUT)

                sig_cls = "nonincreasing (sig)" if ok_sig else "NOT nonincreasing (sig)"

                print(f"  window={window:>2} | point={point_cls:<13} | sig={sig_cls}")

                if ok_sig:
                    print_endpoints(Ts, betas, ses)
                else:
                    print("      significant violations (upward jumps):")
                    for Ti, Tj, d, z in viol:
                        print(f"        {Ti:>3}→{Tj:<3}: diff={d:+.6f}, z={z:+.3f}")

if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 27
# ------------------------------------------------------------------------------
from pathlib import Path
from math import erf, sqrt
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =============================================================================
OUT_DIR = Path("/home/ll/jupyter_notebook/result/windows/Gumbel/1218三维健康_disease")
RES_CSV = OUT_DIR / "fe_components_Tall_5_10_20_30y_pid12_provYearFE_cityCluster_cityCluster.csv"

# =============================================================================
SAMPLE = "all"                 # all / rural / urban
WINDOW_LIST = [5, 10, 20, 30]
T_SMALL, T_LARGE = 2, 100
ALPHA = 0.05                   # Original notebook comment normalized for the public code archive.
SIZE_SMALL, SIZE_LARGE = 25, 90

DOMAIN_FILTER = None           # Original notebook comment normalized for the public code archive.
SORT_BY = "domain"             # "domain" / "diff" / "beta100"


# =============================================================================
def norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))

def p_two_sided_from_z(z: float) -> float:
    if not np.isfinite(z):
        return np.nan
    return 2.0 * (1.0 - norm_cdf(abs(z)))


def load_window_data(sample: str, window: int, domain_filter=None) -> pd.DataFrame:
    df = pd.read_csv(RES_CSV)

    # Original notebook comment normalized for the public code archive.
    for c in ["Unnamed: 0", "index"]:
        if c in df.columns:
            df = df.drop(columns=[c])

    need = ["sample", "window", "T", "outcome", "Estimate", "Std. Error"]
    miss = [c for c in need if c not in df.columns]
    if miss:
        raise KeyError(f"结果文件缺少列: {miss}\n请检查：{RES_CSV}")

    # Original notebook comment normalized for the public code archive.
    df["window"] = pd.to_numeric(df["window"], errors="coerce")
    df["T"] = pd.to_numeric(df["T"], errors="coerce")
    for c in ["Estimate", "Std. Error"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=["sample", "window", "T", "outcome", "Estimate", "Std. Error"]).copy()
    df["window"] = df["window"].astype(int)
    df["T"] = df["T"].astype(int)
    df["sample"] = df["sample"].astype(str)
    df["outcome"] = df["outcome"].astype(str)

    df = df[(df["sample"] == sample) & (df["window"] == window) & (df["T"].isin([T_SMALL, T_LARGE]))].copy()

    if domain_filter is not None:
        if "domain" not in df.columns:
            raise KeyError("设置了 DOMAIN_FILTER，但文件中没有 domain 列。")
        df = df[df["domain"].astype(str) == str(domain_filter)].copy()

    if df.empty:
        return pd.DataFrame()

    # Original notebook comment normalized for the public code archive.
    g = df.groupby(["outcome", "T"], as_index=False)[["Estimate", "Std. Error"]].mean()

    # Original notebook comment normalized for the public code archive.
    beta = g.pivot(index="outcome", columns="T", values="Estimate")
    se   = g.pivot(index="outcome", columns="T", values="Std. Error")
    keep = beta.dropna(subset=[T_SMALL, T_LARGE]).copy()
    keep_se = se.loc[keep.index].copy()

    out = pd.DataFrame({
        "outcome": keep.index,
        "beta2": keep[T_SMALL].values,
        "beta100": keep[T_LARGE].values,
        "se2": keep_se[T_SMALL].values,
        "se100": keep_se[T_LARGE].values,
    }).reset_index(drop=True)

    # Original notebook comment normalized for the public code archive.
    if "domain" in df.columns:
        dom = df.groupby("outcome", as_index=False)["domain"].agg(lambda x: x.dropna().astype(str).iloc[0] if len(x.dropna()) else "")
        out = out.merge(dom, on="outcome", how="left")
    else:
        out["domain"] = ""

    # Original notebook comment normalized for the public code archive.
    out["diff_100_minus_2"] = out["beta100"] - out["beta2"]
    out["se_diff"] = np.sqrt(out["se2"]**2 + out["se100"]**2)
    out["z_diff"] = out["diff_100_minus_2"] / out["se_diff"]
    out["p_diff"] = out["z_diff"].apply(p_two_sided_from_z)
    out["sig_trend"] = out["p_diff"] < ALPHA

    return out


def plot_dumbbell_with_sig_line(sample: str, window: int, domain_filter=None, sort_by="domain"):
    dat = load_window_data(sample, window, domain_filter=domain_filter)
    if dat.empty:
        print(f"[SKIP] sample={sample}, window={window}: no endpoints (T=2 & 100).")
        return

    # Original notebook comment normalized for the public code archive.
    if sort_by == "diff":
        dat = dat.sort_values(["diff_100_minus_2", "outcome"])
    elif sort_by == "beta100":
        dat = dat.sort_values(["beta100", "outcome"])
    else:
        dat = dat.sort_values(["domain", "outcome"])

    y = np.arange(len(dat))
    b2 = dat["beta2"].to_numpy(float)
    b100 = dat["beta100"].to_numpy(float)

    xmin = float(min(b2.min(), b100.min()))
    xmax = float(max(b2.max(), b100.max()))
    pad = 0.08 * (xmax - xmin if xmax > xmin else 1.0)
    xmin, xmax = xmin - pad, xmax + pad

    fig_h = max(4.5, 0.32 * len(dat))
    plt.figure(figsize=(9, fig_h))

    # Original notebook comment normalized for the public code archive.
    for i in range(len(dat)):
        ls = "-" if bool(dat.iloc[i]["sig_trend"]) else "--"
        plt.hlines(y=i, xmin=b2[i], xmax=b100[i], linewidth=2, linestyle=ls)

    # Original notebook comment normalized for the public code archive.
    plt.scatter(b2, y, s=SIZE_SMALL, label=f"T={T_SMALL}")
    plt.scatter(b100, y, s=SIZE_LARGE, label=f"T={T_LARGE}")

    plt.axvline(0, linestyle="--", linewidth=1)
    plt.xlim(xmin, xmax)

    plt.yticks(y, dat["outcome"].tolist())
    title_dom = f", domain={domain_filter}" if domain_filter is not None else ""
    plt.title(f"指标端点哑铃图（sample={sample}, window={window}{title_dom}）：p<0.05 实线，否则虚线")
    plt.xlabel("回归系数 β（Estimate）")
    plt.legend()
    plt.tight_layout()
    plt.show()

    # Original notebook comment normalized for the public code archive.
    n_sig = int(dat["sig_trend"].sum())
    print(f"[INFO] sample={sample}, window={window}: significant trend (p<{ALPHA}) = {n_sig}/{len(dat)}")


if __name__ == "__main__":
    for w in WINDOW_LIST:
        plot_dumbbell_with_sig_line(
            sample=SAMPLE,
            window=w,
            domain_filter=DOMAIN_FILTER,  # Original notebook comment normalized for the public code archive.
            sort_by=SORT_BY
        )


# ------------------------------------------------------------------------------
# Notebook cell 29
# ------------------------------------------------------------------------------
from pathlib import Path
from math import erf, sqrt
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =============================================================================
OUT_DIR = Path("/home/ll/jupyter_notebook/result/windows/Gumbel/1218三维健康_disease")
RES_CSV = OUT_DIR / "fe_components_Tall_5_10_20_30y_pid12_provYearFE_cityCluster_cityCluster.csv"

# =============================================================================
SAMPLE = "all"                 # all / rural / urban
WINDOW_LIST = [5, 10, 20, 30]   # Original notebook comment normalized for the public code archive.
T_SMALL, T_LARGE = 2, 100
ALPHA = 0.05
SIZE_SMALL, SIZE_LARGE = 25, 90

DOMAIN_FILTER = None           # Original notebook comment normalized for the public code archive.
SORT_BY = "domain"             # "domain" / "diff" / "beta100"


# =============================================================================
def norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))

def p_two_sided_from_z(z: float) -> float:
    if not np.isfinite(z):
        return np.nan
    return 2.0 * (1.0 - norm_cdf(abs(z)))


def load_merged_windows(sample: str, domain_filter=None) -> pd.DataFrame:
    df = pd.read_csv(RES_CSV)

    # Original notebook comment normalized for the public code archive.
    for c in ["Unnamed: 0", "index"]:
        if c in df.columns:
            df = df.drop(columns=[c])

    need = ["sample", "window", "T", "outcome", "Estimate", "Std. Error"]
    miss = [c for c in need if c not in df.columns]
    if miss:
        raise KeyError(f"结果文件缺少列: {miss}\n请检查：{RES_CSV}")

    # Original notebook comment normalized for the public code archive.
    df["window"] = pd.to_numeric(df["window"], errors="coerce")
    df["T"] = pd.to_numeric(df["T"], errors="coerce")
    df["Estimate"] = pd.to_numeric(df["Estimate"], errors="coerce")
    df["Std. Error"] = pd.to_numeric(df["Std. Error"], errors="coerce")

    df = df.dropna(subset=["sample", "window", "T", "outcome", "Estimate", "Std. Error"]).copy()
    df["window"] = df["window"].astype(int)
    df["T"] = df["T"].astype(int)
    df["sample"] = df["sample"].astype(str)
    df["outcome"] = df["outcome"].astype(str)

    # Original notebook comment normalized for the public code archive.
    df = df[(df["sample"] == sample) &
            (df["window"].isin(WINDOW_LIST)) &
            (df["T"].isin([T_SMALL, T_LARGE]))].copy()

    # Original notebook comment normalized for the public code archive.
    if domain_filter is not None:
        if "domain" not in df.columns:
            raise KeyError("设置了 DOMAIN_FILTER，但文件中没有 domain 列。")
        df = df[df["domain"].astype(str) == str(domain_filter)].copy()

    if df.empty:
        return pd.DataFrame()

    # Original notebook comment normalized for the public code archive.
    df["var"] = df["Std. Error"] ** 2
    df.loc[df["var"] <= 0, "var"] = np.nan
    df = df.dropna(subset=["var"]).copy()
    df["w"] = 1.0 / df["var"]

    def agg_one(g: pd.DataFrame) -> pd.Series:
        w = g["w"].to_numpy(float)
        est = g["Estimate"].to_numpy(float)
        beta_w = float(np.sum(w * est) / np.sum(w))
        se_w = float(np.sqrt(1.0 / np.sum(w)))
        win_list = sorted(g["window"].astype(int).unique().tolist())
        return pd.Series({
            "beta_agg": beta_w,
            "se_agg": se_w,
            "n_win": len(win_list),
            "win_list": ",".join(map(str, win_list)),
        })

    agg = df.groupby(["outcome", "T"], as_index=False).apply(agg_one)

    # Original notebook comment normalized for the public code archive.
    beta = agg.pivot(index="outcome", columns="T", values="beta_agg")
    se   = agg.pivot(index="outcome", columns="T", values="se_agg")
    nwin = agg.pivot(index="outcome", columns="T", values="n_win")

    keep = beta.dropna(subset=[T_SMALL, T_LARGE]).copy()
    if keep.empty:
        return pd.DataFrame()

    out = pd.DataFrame({
        "outcome": keep.index,
        "beta2": keep[T_SMALL].values,
        "beta100": keep[T_LARGE].values,
        "se2": se.loc[keep.index, T_SMALL].values,
        "se100": se.loc[keep.index, T_LARGE].values,
        "nwin2": nwin.loc[keep.index, T_SMALL].values,
        "nwin100": nwin.loc[keep.index, T_LARGE].values,
    }).reset_index(drop=True)

    # Original notebook comment normalized for the public code archive.
    if "domain" in df.columns:
        dom = df.groupby("outcome", as_index=False)["domain"].agg(
            lambda x: x.dropna().astype(str).iloc[0] if len(x.dropna()) else ""
        )
        out = out.merge(dom, on="outcome", how="left")
    else:
        out["domain"] = ""

    # Original notebook comment normalized for the public code archive.
    out["diff_100_minus_2"] = out["beta100"] - out["beta2"]
    out["se_diff"] = np.sqrt(out["se2"]**2 + out["se100"]**2)
    out["z_diff"] = out["diff_100_minus_2"] / out["se_diff"]
    out["p_diff"] = out["z_diff"].apply(p_two_sided_from_z)
    out["sig_trend"] = out["p_diff"] < ALPHA

    return out


def plot_dumbbell_merged(sample: str, domain_filter=None, sort_by="domain"):
    dat = load_merged_windows(sample, domain_filter=domain_filter)
    if dat.empty:
        print(f"[SKIP] sample={sample}: no merged endpoints (T=2 & 100) found.")
        return

    # Original notebook comment normalized for the public code archive.
    if sort_by == "diff":
        dat = dat.sort_values(["diff_100_minus_2", "outcome"])
    elif sort_by == "beta100":
        dat = dat.sort_values(["beta100", "outcome"])
    else:
        dat = dat.sort_values(["domain", "outcome"])

    y = np.arange(len(dat))
    b2 = dat["beta2"].to_numpy(float)
    b100 = dat["beta100"].to_numpy(float)

    xmin = float(min(b2.min(), b100.min()))
    xmax = float(max(b2.max(), b100.max()))
    pad = 0.08 * (xmax - xmin if xmax > xmin else 1.0)
    xmin, xmax = xmin - pad, xmax + pad

    fig_h = max(4.5, 0.32 * len(dat))
    plt.figure(figsize=(9, fig_h))

    # Original notebook comment normalized for the public code archive.
    for i in range(len(dat)):
        ls = "-" if bool(dat.iloc[i]["sig_trend"]) else "--"
        plt.hlines(y=i, xmin=b2[i], xmax=b100[i], linewidth=2, linestyle=ls)

    # Original notebook comment normalized for the public code archive.
    plt.scatter(b2, y, s=SIZE_SMALL, label=f"T={T_SMALL}")
    plt.scatter(b100, y, s=SIZE_LARGE, label=f"T={T_LARGE}")

    plt.axvline(0, linestyle="--", linewidth=1)
    plt.xlim(xmin, xmax)

    plt.yticks(y, dat["outcome"].tolist())
    title_dom = f", domain={domain_filter}" if domain_filter is not None else ""
    plt.title(f"融合窗口(5/10/20/30)后的端点哑铃图（sample={sample}{title_dom}）：p<0.05 实线，否则虚线")
    plt.xlabel("回归系数 β（Estimate，跨窗口逆方差加权）")
    plt.legend()
    plt.tight_layout()
    plt.show()

    # Original notebook comment normalized for the public code archive.
    n_sig = int(dat["sig_trend"].sum())
    print(f"[INFO] merged windows: sample={sample}: significant Δ(100-2) (p<{ALPHA}) = {n_sig}/{len(dat)}")
    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    plot_dumbbell_merged(
        sample=SAMPLE,
        domain_filter=DOMAIN_FILTER,  # Original notebook comment normalized for the public code archive.
        sort_by=SORT_BY
    )


# ------------------------------------------------------------------------------
# Notebook cell 33
# ------------------------------------------------------------------------------
# Notebook-export prose note omitted from the public code archive.
