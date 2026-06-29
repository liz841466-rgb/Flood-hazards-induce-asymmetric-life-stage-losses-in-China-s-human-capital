#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 04_health_status_index_figure.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 1
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
# Notebook cell 4
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from math import erf, sqrt
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# =========================
# Global style (Times New Roman)
# =========================
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams.update({
    "figure.dpi": 300,
    "font.size": 12,
    "axes.labelsize": 14,
    "axes.titlesize": 14,
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
    "legend.fontsize": 11,
})

# =========================
# Paths (Windows)
# =========================
OUT_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\statues_index")
RES_CSV = OUT_DIR / "fe_components_Tall_5_10_20_30y_pid12_provYearFE_cityCluster_cityCluster.csv"

# =========================
# Parameters
# =========================
SAMPLE = "rural"                 # all / rural / urban
WINDOW_LIST = [5, 10, 20, 30]
T_SMALL, T_LARGE = 2, 100
ALPHA = 0.05                   # p < 0.05 -> solid line, else dashed
SIZE_SMALL, SIZE_LARGE = 25, 90

DOMAIN_FILTER = None           # None=all; or "phys"/"mental"/"social" (match your 'domain' values)
SORT_BY = "domain"             # "domain" / "diff" / "beta100"

# Optional: save figures
SAVE_PNG = False
PNG_DPI = 300


# =========================
# Normal CDF (for p-values)
# =========================
def norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))

def p_two_sided_from_z(z: float) -> float:
    if not np.isfinite(z):
        return np.nan
    return 2.0 * (1.0 - norm_cdf(abs(z)))


def read_results(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    # Drop possible index columns
    for c in ["Unnamed: 0", "index"]:
        if c in df.columns:
            df = df.drop(columns=[c])

    required = ["sample", "window", "T", "outcome", "Estimate", "Std. Error"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(
            f"Missing required columns in CSV: {missing}\n"
            f"Please check: {csv_path}"
        )

    # Numeric conversion
    df["window"] = pd.to_numeric(df["window"], errors="coerce")
    df["T"] = pd.to_numeric(df["T"], errors="coerce")
    for c in ["Estimate", "Std. Error"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=["sample", "window", "T", "outcome", "Estimate", "Std. Error"]).copy()
    df["window"] = df["window"].astype(int)
    df["T"] = df["T"].astype(int)
    df["sample"] = df["sample"].astype(str)
    df["outcome"] = df["outcome"].astype(str)

    if "domain" in df.columns:
        df["domain"] = df["domain"].astype(str)

    return df


def build_endpoints_table(df_all: pd.DataFrame, sample: str, window: int, domain_filter=None) -> pd.DataFrame:
    df = df_all.copy()

    df = df[(df["sample"] == sample) &
            (df["window"] == int(window)) &
            (df["T"].isin([T_SMALL, T_LARGE]))].copy()

    if domain_filter is not None:
        if "domain" not in df.columns:
            raise KeyError("DOMAIN_FILTER is set, but the CSV has no 'domain' column.")
        df = df[df["domain"].astype(str) == str(domain_filter)].copy()

    if df.empty:
        return pd.DataFrame()

    # If duplicates exist (should not), take mean by (outcome, T)
    g = df.groupby(["outcome", "T"], as_index=False)[["Estimate", "Std. Error"]].mean()

    # Pivot to wide
    beta = g.pivot(index="outcome", columns="T", values="Estimate")
    se = g.pivot(index="outcome", columns="T", values="Std. Error")

    keep = beta.dropna(subset=[T_SMALL, T_LARGE]).copy()
    keep_se = se.loc[keep.index].copy()

    out = pd.DataFrame({
        "outcome": keep.index,
        "beta2": keep[T_SMALL].values,
        "beta100": keep[T_LARGE].values,
        "se2": keep_se[T_SMALL].values,
        "se100": keep_se[T_LARGE].values,
    }).reset_index(drop=True)

    # Bring domain (if exists)
    if "domain" in df.columns:
        dom = (df.groupby("outcome", as_index=False)["domain"]
                 .agg(lambda x: x.dropna().astype(str).iloc[0] if len(x.dropna()) else ""))
        out = out.merge(dom, on="outcome", how="left")
    else:
        out["domain"] = ""

    # Trend significance (conservative: ignore covariance)
    out["diff_100_minus_2"] = out["beta100"] - out["beta2"]
    out["se_diff"] = np.sqrt(out["se2"] ** 2 + out["se100"] ** 2)
    out["z_diff"] = out["diff_100_minus_2"] / out["se_diff"]
    out["p_diff"] = out["z_diff"].apply(p_two_sided_from_z)
    out["sig_trend"] = out["p_diff"] < ALPHA

    return out


def plot_dumbbell_with_sig_line(df_all: pd.DataFrame, sample: str, window: int, domain_filter=None, sort_by="domain"):
    dat = build_endpoints_table(df_all, sample, window, domain_filter=domain_filter)
    if dat.empty:
        print(f"[SKIP] sample={sample}, window={window}: no endpoints for T={T_SMALL} and T={T_LARGE}.")
        return

    # Sorting
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
    fig, ax = plt.subplots(figsize=(9, fig_h))

    # Connecting lines: solid if p<alpha, else dashed
    for i in range(len(dat)):
        ls = "-" if bool(dat.iloc[i]["sig_trend"]) else "--"
        ax.hlines(y=i, xmin=b2[i], xmax=b100[i], linewidth=2, linestyle=ls)

    # Endpoints
    ax.scatter(b2, y, s=SIZE_SMALL, label=f"T={T_SMALL}")
    ax.scatter(b100, y, s=SIZE_LARGE, label=f"T={T_LARGE}")

    ax.axvline(0, linestyle="--", linewidth=1)
    ax.set_xlim(xmin, xmax)

    ax.set_yticks(y)
    ax.set_yticklabels(dat["outcome"].tolist(), color="black")

    dom_txt = f", domain={domain_filter}" if domain_filter is not None else ""
    ax.set_title(
        f"Endpoint Dumbbell Plot (sample={sample}, window={window}{dom_txt}): "
        f"solid if p<{ALPHA}, otherwise dashed"
    )
    ax.set_xlabel("Regression Coefficient β (Estimate)")
    ax.legend()

    plt.tight_layout()

    if SAVE_PNG:
        tag_dom = f"_domain-{domain_filter}" if domain_filter is not None else ""
        out_png = OUT_DIR / f"dumbbell_endpoints_sample-{sample}_window-{window}{tag_dom}.png"
        fig.savefig(out_png, dpi=PNG_DPI, bbox_inches="tight")
        print(f"[SAVE] {out_png}")

    plt.show()

    n_sig = int(dat["sig_trend"].sum())
    print(f"[INFO] sample={sample}, window={window}: significant trend (p<{ALPHA}) = {n_sig}/{len(dat)}")


if __name__ == "__main__":
    print(f"[INFO] Reading results: {RES_CSV}")
    df_all = read_results(RES_CSV)

    for w in WINDOW_LIST:
        plot_dumbbell_with_sig_line(
            df_all=df_all,
            sample=SAMPLE,
            window=w,
            domain_filter=DOMAIN_FILTER,  # None or "phys"/"mental"/"social"
            sort_by=SORT_BY
        )


# ------------------------------------------------------------------------------
# Notebook cell 6
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from math import erf, sqrt
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# =========================
# Global style (Times New Roman)
# =========================
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams["svg.fonttype"] = "none"   # keep text editable in SVG
mpl.rcParams.update({
    "figure.dpi": 300,
    "font.size": 12,
    "axes.labelsize": 13,
    "axes.titlesize": 13,
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
})

# =========================
# Paths (Windows)
# =========================
BASE_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\statues_index")
RES_CSV  = BASE_DIR / "fe_components_Tall_5_10_20_30y_pid12_provYearFE_cityCluster_cityCluster.csv"

OUT_DIR = BASE_DIR / "dumbbell"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# =========================
# Parameters
# =========================
SAMPLES = ["rural", "urban"]
WINDOW_GROUPS = [(5, 10), (20, 30)]   # each group makes ONE figure

T_SMALL, T_LARGE = 2, 100
ALPHA = 0.05

SIZE_SMALL, SIZE_LARGE = 22, 70
DOMAIN_FILTER = None                  # None or "phys"/"mental"/"social"
SORT_BY = "domain"                    # "domain" / "diff" / "beta100"

# === Color for points & connecting lines ===
MAIN_COLOR = "#8cbedd"

# Save SVG
SAVE_SVG = True
SVG_DPI = 300          # not very meaningful for pure vector, but harmless
SHOW_FIG = True

# gridlines at x ticks: solid gray
GRID_ON = True
GRID_COLOR = "0.85"
GRID_LW = 0.8


# =========================
# Normal CDF (for p-values)
# =========================
def norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))

def p_two_sided_from_z(z: float) -> float:
    if not np.isfinite(z):
        return np.nan
    return 2.0 * (1.0 - norm_cdf(abs(z)))


# =========================
# IO + data shaping
# =========================
def read_results(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    for c in ["Unnamed: 0", "index"]:
        if c in df.columns:
            df = df.drop(columns=[c])

    required = ["sample", "window", "T", "outcome", "Estimate", "Std. Error"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}\nCheck: {csv_path}")

    df["window"] = pd.to_numeric(df["window"], errors="coerce")
    df["T"] = pd.to_numeric(df["T"], errors="coerce")
    df["Estimate"] = pd.to_numeric(df["Estimate"], errors="coerce")
    df["Std. Error"] = pd.to_numeric(df["Std. Error"], errors="coerce")

    df = df.dropna(subset=["sample", "window", "T", "outcome", "Estimate", "Std. Error"]).copy()
    df["sample"] = df["sample"].astype(str)
    df["window"] = df["window"].astype(int)
    df["T"] = df["T"].astype(int)
    df["outcome"] = df["outcome"].astype(str)

    if "domain" in df.columns:
        df["domain"] = df["domain"].astype(str)
    else:
        df["domain"] = ""

    return df


def endpoints_table(df_all: pd.DataFrame, sample: str, window: int, domain_filter=None) -> pd.DataFrame:
    df = df_all[(df_all["sample"] == sample) &
                (df_all["window"] == int(window)) &
                (df_all["T"].isin([T_SMALL, T_LARGE]))].copy()

    if domain_filter is not None:
        if "domain" not in df.columns:
            raise KeyError("DOMAIN_FILTER is set but CSV has no 'domain' column.")
        df = df[df["domain"].astype(str) == str(domain_filter)].copy()

    if df.empty:
        return pd.DataFrame()

    g = df.groupby(["outcome", "T"], as_index=False)[["Estimate", "Std. Error"]].mean()
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

    # domain
    if "domain" in df.columns and df["domain"].notna().any():
        dom = df.groupby("outcome", as_index=False)["domain"].agg(
            lambda x: x.dropna().astype(str).iloc[0] if len(x.dropna()) else ""
        )
        out = out.merge(dom, on="outcome", how="left")
    else:
        out["domain"] = ""

    # trend significance (conservative: ignore covariance)
    out["diff_100_minus_2"] = out["beta100"] - out["beta2"]
    out["se_diff"] = np.sqrt(out["se2"]**2 + out["se100"]**2)
    out["z_diff"] = out["diff_100_minus_2"] / out["se_diff"]
    out["p_diff"] = out["z_diff"].apply(p_two_sided_from_z)
    out["sig_trend"] = out["p_diff"] < ALPHA

    return out


def master_order(df_all: pd.DataFrame, sample: str, windows: list[int], domain_filter=None, sort_by="domain") -> list[str]:
    tables = []
    for w in windows:
        t = endpoints_table(df_all, sample, w, domain_filter=domain_filter)
        if t.empty:
            return []
        tables.append(t)

    common = set(tables[0]["outcome"])
    for t in tables[1:]:
        common &= set(t["outcome"])
    if not common:
        return []

    common = sorted(common)

    pieces = []
    for w, t in zip(windows, tables):
        tmp = t[t["outcome"].isin(common)][["outcome", "domain", "diff_100_minus_2", "beta100"]].copy()
        tmp["window"] = int(w)
        pieces.append(tmp)

    long_df = pd.concat(pieces, ignore_index=True)

    agg = (long_df.groupby("outcome", as_index=False)
           .agg(
               domain=("domain", lambda x: x.dropna().astype(str).iloc[0] if len(x.dropna()) else ""),
               diff_mean=("diff_100_minus_2", "mean"),
               b100_mean=("beta100", "mean"),
           ))

    if sort_by == "diff":
        agg = agg.sort_values(["diff_mean", "outcome"], ascending=[True, True])
    elif sort_by == "beta100":
        agg = agg.sort_values(["b100_mean", "outcome"], ascending=[True, True])
    else:
        agg = agg.sort_values(["domain", "outcome"], ascending=[True, True])

    return agg["outcome"].tolist()


# =========================
# Plot helpers
# =========================
def strip_axes(ax, show_bottom: bool):
    for side in ["top", "right", "left", "bottom"]:
        ax.spines[side].set_visible(False)

    if show_bottom:
        ax.spines["bottom"].set_visible(True)
        ax.tick_params(axis="x", bottom=True, labelbottom=True, length=3)
    else:
        ax.tick_params(axis="x", bottom=False, labelbottom=False)

    ax.tick_params(axis="y", left=False, labelleft=False)

    if GRID_ON:
        ax.grid(axis="x", which="major", linestyle="-", linewidth=GRID_LW, color=GRID_COLOR)


def plot_one_panel(ax, dat: pd.DataFrame, outcomes_order: list[str], show_bottom_x: bool):
    dat = dat.set_index("outcome").reindex(outcomes_order).reset_index()
    y = np.arange(len(outcomes_order))

    b2 = dat["beta2"].to_numpy(float)
    b100 = dat["beta100"].to_numpy(float)

    finite = np.isfinite(b2) & np.isfinite(b100)
    xmin = float(min(np.nanmin(b2[finite]), np.nanmin(b100[finite])))
    xmax = float(max(np.nanmax(b2[finite]), np.nanmax(b100[finite])))
    pad = 0.08 * (xmax - xmin if xmax > xmin else 1.0)
    xmin, xmax = xmin - pad, xmax + pad

    # connecting lines (color set to MAIN_COLOR)
    for i in range(len(outcomes_order)):
        if not np.isfinite(b2[i]) or not np.isfinite(b100[i]):
            continue
        ls = "-" if bool(dat.loc[i, "sig_trend"]) else "--"
        ax.hlines(y=i, xmin=b2[i], xmax=b100[i],
                  linewidth=1.8, linestyle=ls, colors=MAIN_COLOR)

    # endpoints (both sizes in MAIN_COLOR)
    ax.scatter(b2, y, s=SIZE_SMALL, c=MAIN_COLOR, edgecolors=MAIN_COLOR, linewidths=0.0, zorder=3)
    ax.scatter(b100, y, s=SIZE_LARGE, c=MAIN_COLOR, edgecolors=MAIN_COLOR, linewidths=0.0, zorder=3)

    # zero line keep neutral
    ax.axvline(0, linestyle="--", linewidth=1, color="0.35")

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(-0.5, len(outcomes_order) - 0.5)
    ax.invert_yaxis()

    strip_axes(ax, show_bottom=show_bottom_x)


def clean_outcome_label(name: str) -> str:
    return str(name).replace("_norm2", "")


def plot_label_axis(ax_mid, outcomes_order: list[str]):
    ax_mid.set_xlim(0, 1)
    ax_mid.set_ylim(-0.5, len(outcomes_order) - 0.5)
    ax_mid.invert_yaxis()
    ax_mid.axis("off")

    trans = ax_mid.get_yaxis_transform()
    for i, name in enumerate(outcomes_order):
        ax_mid.text(0.02, i, clean_outcome_label(name), transform=trans, ha="left", va="center")


def plot_pair_1row(df_all: pd.DataFrame, sample: str, w_left: int, w_right: int):
    windows = [w_left, w_right]
    order = master_order(df_all, sample, windows, domain_filter=DOMAIN_FILTER, sort_by=SORT_BY)
    if not order:
        print(f"[SKIP] sample={sample}, windows={windows}: no common outcomes.")
        return

    dL = endpoints_table(df_all, sample, w_left, domain_filter=DOMAIN_FILTER)
    dR = endpoints_table(df_all, sample, w_right, domain_filter=DOMAIN_FILTER)

    n = len(order)
    fig_h = max(6.0, 0.26 * n)
    fig_w = 13.0

    fig = plt.figure(figsize=(fig_w, fig_h))
    gs = fig.add_gridspec(
        nrows=1, ncols=3,
        width_ratios=[1.25, 1.60, 1.25],
        wspace=0.02
    )

    axL = fig.add_subplot(gs[0, 0])
    axM = fig.add_subplot(gs[0, 1])
    axR = fig.add_subplot(gs[0, 2])

    plot_one_panel(axL, dL, order, show_bottom_x=True)
    plot_one_panel(axR, dR, order, show_bottom_x=True)
    plot_label_axis(axM, order)

    fig.supxlabel("Coefficient")
    plt.tight_layout()

    if SAVE_SVG:
        tag_dom = f"_domain-{DOMAIN_FILTER}" if DOMAIN_FILTER is not None else ""
        out_svg = OUT_DIR / f"dumbbell_pair_{w_left}-{w_right}_sample-{sample}{tag_dom}.svg"
        fig.savefig(out_svg, format="svg", dpi=SVG_DPI, bbox_inches="tight")
        print(f"[SAVE] {out_svg}")

    if SHOW_FIG:
        plt.show()
    else:
        plt.close(fig)


if __name__ == "__main__":
    print(f"[INFO] Reading results: {RES_CSV}")
    df_all = read_results(RES_CSV)

    for s in SAMPLES:
        for (w1, w2) in WINDOW_GROUPS:
            plot_pair_1row(df_all, sample=s, w_left=w1, w_right=w2)


# ------------------------------------------------------------------------------
# Notebook cell 9
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from math import erf, sqrt
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# =========================
# Global style
# =========================
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams["svg.fonttype"] = "none"  # keep text editable in SVG
mpl.rcParams.update({
    "figure.dpi": 300,
    "font.size": 15,
    "axes.labelsize": 14,
    "xtick.labelsize": 14,
    "ytick.labelsize": 14,
})

# =========================
# Paths (Windows)
# =========================
BASE_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\statues_index")
RES_CSV  = BASE_DIR / "fe_components_Tall_5_10_20_30y_pid12_provYearFE_cityCluster_cityCluster.csv"
OUT_DIR  = BASE_DIR / "dumbbell"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# =========================
# Parameters
# =========================
WINDOW_LIST = [5, 10, 20, 30]   # merged windows
T_SMALL, T_LARGE = 2, 100
ALPHA = 0.05

SIZE_SMALL, SIZE_LARGE = 40, 70
DOMAIN_FILTER = None            # None or "phys"/"mental"/"social" (only used for filtering, not ordering)

COLOR_RURAL = "#8cbedd"
COLOR_URBAN = "#f2604f"

GRID_ON = True
GRID_COLOR = "0.85"
GRID_LW = 0.8

SAVE_SVG = True
SHOW_FIG = True

# Layout: bring panels closer but avoid label clipping
WIDTH_RATIOS = [1.35, 0.60, 1.35]
WSPACE = 0.002

# vertical spacing between variables
Y_GAP = 1.30  # 1.0 default; >1 looser; e.g. 1.15

# =========================
# Custom variable order (your lists)
# =========================
PHYS_VARS_HIGH_BAD = [
    "dress", "bathe", "eat",
    "bed_chair_transfer", "toilet",
    "walk100m", "walk1km", "stairs",
    "run1km", "lift5kg", "bend_kneel_squat",
    "pick_coin", "incontinence", "housework",
    "arm_raise", "sit_to_stand",
]
PHYS_VARS_HIGH_GOOD = [
    "disease",  # may not exist -> auto skip
]

MENTAL_VARS_HIGH_BAD = [
    "cesd10_sum",
    "depress", "effort", "fear", "sleep", "hopeless",
    "life_satisfaction", "srh",
]
MENTAL_VARS_HIGH_GOOD = [
    "happy", "hope",
    "memory_disease",
    "mental_neuro_psych",
]

SOCIAL_VARS_HIGH_BAD = [
    "call_child_freq",
    "meet_child_freq",
    "social_freq",
    "social_activity",
]
SOCIAL_VARS_HIGH_GOOD = [
    "annual_transfer",
]

CUSTOM_ORDER_CLEAN = (
    PHYS_VARS_HIGH_BAD + PHYS_VARS_HIGH_GOOD
    + MENTAL_VARS_HIGH_BAD + MENTAL_VARS_HIGH_GOOD
    + SOCIAL_VARS_HIGH_BAD + SOCIAL_VARS_HIGH_GOOD
)

USE_CUSTOM_ORDER = True
APPEND_OTHERS = False   # True: append any remaining variables after custom list


# =========================
# Stats helpers
# =========================
def norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))

def p_two_sided_from_z(z: float) -> float:
    if not np.isfinite(z):
        return np.nan
    return 2.0 * (1.0 - norm_cdf(abs(z)))

def clean_outcome_label(name: str) -> str:
    # display label
    return str(name).replace("_norm2", "")

def normalize_key(name: str) -> str:
    # matching key
    return clean_outcome_label(name).strip()


# =========================
# IO
# =========================
def read_results(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    for c in ["Unnamed: 0", "index"]:
        if c in df.columns:
            df = df.drop(columns=[c])

    required = ["sample", "window", "T", "outcome", "Estimate", "Std. Error"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}\nCheck: {csv_path}")

    df["window"] = pd.to_numeric(df["window"], errors="coerce")
    df["T"] = pd.to_numeric(df["T"], errors="coerce")
    df["Estimate"] = pd.to_numeric(df["Estimate"], errors="coerce")
    df["Std. Error"] = pd.to_numeric(df["Std. Error"], errors="coerce")

    df = df.dropna(subset=["sample", "window", "T", "outcome", "Estimate", "Std. Error"]).copy()
    df["sample"] = df["sample"].astype(str)
    df["window"] = df["window"].astype(int)
    df["T"] = df["T"].astype(int)
    df["outcome"] = df["outcome"].astype(str)

    if "domain" in df.columns:
        df["domain"] = df["domain"].astype(str)
    else:
        df["domain"] = ""

    return df


# =========================
# Merge windows by IVW for endpoints (T=2 and T=100)
# =========================
def merged_endpoints(df_all: pd.DataFrame, sample: str, domain_filter=None) -> pd.DataFrame:
    df = df_all[(df_all["sample"] == sample) &
                (df_all["window"].isin(WINDOW_LIST)) &
                (df_all["T"].isin([T_SMALL, T_LARGE]))].copy()

    if domain_filter is not None:
        if "domain" not in df.columns:
            raise KeyError("DOMAIN_FILTER is set but CSV has no 'domain' column.")
        df = df[df["domain"].astype(str) == str(domain_filter)].copy()

    if df.empty:
        return pd.DataFrame()

    df["var"] = df["Std. Error"] ** 2
    df.loc[df["var"] <= 0, "var"] = np.nan
    df = df.dropna(subset=["var"]).copy()
    df["w"] = 1.0 / df["var"]

    def agg_one(g: pd.DataFrame) -> pd.Series:
        w = g["w"].to_numpy(float)
        est = g["Estimate"].to_numpy(float)
        beta_w = float(np.sum(w * est) / np.sum(w))
        se_w = float(np.sqrt(1.0 / np.sum(w)))
        return pd.Series({"beta_agg": beta_w, "se_agg": se_w})

    agg = (df.groupby(["outcome", "T"], as_index=False)
             .apply(agg_one)
             .reset_index(drop=True))

    beta = agg.pivot(index="outcome", columns="T", values="beta_agg")
    se   = agg.pivot(index="outcome", columns="T", values="se_agg")

    keep = beta.dropna(subset=[T_SMALL, T_LARGE]).copy()
    if keep.empty:
        return pd.DataFrame()

    out = pd.DataFrame({
        "outcome": keep.index,
        "beta2": keep[T_SMALL].values,
        "beta100": keep[T_LARGE].values,
        "se2": se.loc[keep.index, T_SMALL].values,
        "se100": se.loc[keep.index, T_LARGE].values,
    }).reset_index(drop=True)

    # domain (optional)
    if "domain" in df.columns and df["domain"].notna().any():
        dom = df.groupby("outcome", as_index=False)["domain"].agg(
            lambda x: x.dropna().astype(str).iloc[0] if len(x.dropna()) else ""
        )
        out = out.merge(dom, on="outcome", how="left")
    else:
        out["domain"] = ""

    # significance of endpoint difference
    out["diff_100_minus_2"] = out["beta100"] - out["beta2"]
    out["se_diff"] = np.sqrt(out["se2"]**2 + out["se100"]**2)
    out["z_diff"] = out["diff_100_minus_2"] / out["se_diff"]
    out["p_diff"] = out["z_diff"].apply(p_two_sided_from_z)
    out["sig_trend"] = out["p_diff"] < ALPHA

    return out


# =========================
# Ordering
# =========================
def build_order_custom(dat_r: pd.DataFrame, dat_u: pd.DataFrame) -> list[str]:
    # only keep outcomes present in both rural and urban
    common_full = sorted(set(dat_r["outcome"]) & set(dat_u["outcome"]))
    if not common_full:
        return []

    # map clean -> full (handle _norm2)
    clean_to_full = {}
    for full in common_full:
        key = normalize_key(full)
        # if collision, keep the first; usually no collision
        if key not in clean_to_full:
            clean_to_full[key] = full

    order_full = []
    for nm in CUSTOM_ORDER_CLEAN:
        k = normalize_key(nm)
        if k in clean_to_full:
            order_full.append(clean_to_full[k])

    if APPEND_OTHERS:
        rest = [x for x in common_full if x not in order_full]
        # stable append by clean label
        rest = sorted(rest, key=lambda s: normalize_key(s))
        order_full.extend(rest)

    return order_full


def build_order_default(dat_r: pd.DataFrame, dat_u: pd.DataFrame) -> list[str]:
    # fallback: domain then outcome
    common = sorted(set(dat_r["outcome"]) & set(dat_u["outcome"]))
    if not common:
        return []
    tmp = dat_r[dat_r["outcome"].isin(common)][["outcome", "domain"]].copy()
    tmp["domain"] = tmp["domain"].fillna("")
    tmp["clean"] = tmp["outcome"].map(normalize_key)
    tmp = tmp.sort_values(["domain", "clean", "outcome"])
    return tmp["outcome"].tolist()


# =========================
# Plot
# =========================
def style_axis(ax):
    for side in ["top", "right", "left", "bottom"]:
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_visible(True)

    ax.tick_params(axis="y", left=False, labelleft=False)
    ax.tick_params(axis="x", bottom=True, labelbottom=True, length=3)

    ax.set_axisbelow(True)
    if GRID_ON:
        ax.grid(axis="x", which="major", linestyle="-", linewidth=GRID_LW, color=GRID_COLOR)


def plot_panel(ax, dat: pd.DataFrame, order: list[str], color: str, xlim, y_pos):
    dat = dat.set_index("outcome").reindex(order).reset_index()
    b2 = dat["beta2"].to_numpy(float)
    b100 = dat["beta100"].to_numpy(float)

    for i in range(len(order)):
        if not np.isfinite(b2[i]) or not np.isfinite(b100[i]):
            continue
        ls = "-" if bool(dat.loc[i, "sig_trend"]) else "--"
        ax.hlines(y=y_pos[i], xmin=b2[i], xmax=b100[i], linewidth=2.0, linestyle=ls, colors=color)

    ax.scatter(b2, y_pos, s=SIZE_SMALL, c=color, edgecolors=color, linewidths=0.0, zorder=3)
    ax.scatter(b100, y_pos, s=SIZE_LARGE, c=color, edgecolors=color, linewidths=0.0, zorder=3)

    ax.axvline(0, linestyle="--", linewidth=1.0, color="0.35")

    ax.set_xlim(*xlim)
    ax.set_ylim(y_pos[-1] + 0.5 * Y_GAP, y_pos[0] - 0.5 * Y_GAP)  # inverted
    style_axis(ax)


def plot_labels(ax_mid, order: list[str], y_pos):
    ax_mid.set_xlim(0, 1)
    ax_mid.set_ylim(y_pos[-1] + 0.5 * Y_GAP, y_pos[0] - 0.5 * Y_GAP)
    ax_mid.axis("off")

    trans = ax_mid.get_yaxis_transform()
    for i, full_name in enumerate(order):
        ax_mid.text(
            0.5, y_pos[i], clean_outcome_label(full_name),
            transform=trans, ha="center", va="center",
            zorder=10, clip_on=False
        )


def plot_rural_urban_one_figure(df_all: pd.DataFrame):
    dat_r = merged_endpoints(df_all, "rural", domain_filter=DOMAIN_FILTER)
    dat_u = merged_endpoints(df_all, "urban", domain_filter=DOMAIN_FILTER)

    if dat_r.empty or dat_u.empty:
        print("[SKIP] rural or urban has no merged endpoints.")
        return

    if USE_CUSTOM_ORDER:
        order = build_order_custom(dat_r, dat_u)
    else:
        order = build_order_default(dat_r, dat_u)

    if not order:
        print("[SKIP] No common outcomes between rural and urban (after ordering).")
        return

    # unified xlim
    r_vals = dat_r.set_index("outcome").reindex(order)[["beta2", "beta100"]].to_numpy().ravel()
    u_vals = dat_u.set_index("outcome").reindex(order)[["beta2", "beta100"]].to_numpy().ravel()
    all_vals = np.concatenate([r_vals, u_vals]).astype(float)
    all_vals = all_vals[np.isfinite(all_vals)]
    xmin, xmax = float(all_vals.min()), float(all_vals.max())
    pad = 0.08 * (xmax - xmin if xmax > xmin else 1.0)
    xlim = (xmin - pad, xmax + pad)

    # y positions with adjustable spacing
    y_pos = np.arange(len(order), dtype=float) * Y_GAP

    fig_h = max(6.0, 0.26 * len(order) * Y_GAP)
    fig_w = 13.0

    fig = plt.figure(figsize=(fig_w, fig_h))
    gs = fig.add_gridspec(
        nrows=1, ncols=3,
        width_ratios=WIDTH_RATIOS,
        wspace=WSPACE
    )

    axL = fig.add_subplot(gs[0, 0])
    axM = fig.add_subplot(gs[0, 1])
    axR = fig.add_subplot(gs[0, 2])

    # ensure middle labels are not covered by side axes
    axL.set_zorder(1)
    axR.set_zorder(1)
    axM.set_zorder(3)
    axM.patch.set_alpha(0.0)

    plot_panel(axL, dat_r, order, COLOR_RURAL, xlim=xlim, y_pos=y_pos)
    plot_labels(axM, order, y_pos=y_pos)
    plot_panel(axR, dat_u, order, COLOR_URBAN, xlim=xlim, y_pos=y_pos)

    fig.supxlabel("Coefficient")
    plt.tight_layout()

    if SAVE_SVG:
        tag_dom = f"_domain-{DOMAIN_FILTER}" if DOMAIN_FILTER is not None else ""
        win_tag = "-".join(map(str, WINDOW_LIST))
        tag_custom = "_customOrder" if USE_CUSTOM_ORDER else "_defaultOrder"
        out_svg = OUT_DIR / f"dumbbell_mergedWin{win_tag}_rural-left_urban-right{tag_custom}{tag_dom}.svg"
        fig.savefig(out_svg, format="svg", bbox_inches="tight", pad_inches=0.02)
        print(f"[SAVE] {out_svg}")

    if SHOW_FIG:
        plt.show()
    else:
        plt.close(fig)


if __name__ == "__main__":
    print(f"[INFO] Reading results: {RES_CSV}")
    df_all = read_results(RES_CSV)
    plot_rural_urban_one_figure(df_all)


# ------------------------------------------------------------------------------
# Notebook cell 10
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# =========================
# Global style
# =========================
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams["svg.fonttype"] = "none"  # keep text editable in SVG
mpl.rcParams.update({
    "figure.dpi": 300,
    "font.size": 14,
})

# =========================
# Paths
# =========================
BASE_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\statues_index")
OUT_DIR  = BASE_DIR / "dumbbell"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# =========================
# Your plotting conventions
# =========================
COLOR_RURAL = "#8cbedd"
COLOR_URBAN = "#f2604f"
ALPHA = 0.05

# scatter sizes used in your main figure (area in pt^2)
SIZE_SMALL = 40   # T=2
SIZE_LARGE = 70   # T=100

# convert scatter area to legend markersize (approx.)
MS_SMALL = float(np.sqrt(SIZE_SMALL))
MS_LARGE = float(np.sqrt(SIZE_LARGE))

# =========================
# Build legend handles
# =========================
handles = [
    # Sample color
    Line2D([0], [0], linestyle="None", marker="o",
           markerfacecolor=COLOR_RURAL, markeredgecolor=COLOR_RURAL,
           markersize=8, label="Rural"),
    Line2D([0], [0], linestyle="None", marker="o",
           markerfacecolor=COLOR_URBAN, markeredgecolor=COLOR_URBAN,
           markersize=8, label="Urban"),

    # Significance (line style)
    Line2D([0, 1], [0, 0], color="0.35", lw=2.2, linestyle="-",
           label=rf"Significant trend ($p<{ALPHA}$)"),
    Line2D([0, 1], [0, 0], color="0.35", lw=2.2, linestyle="--",
           label=rf"Not significant ($p\geq{ALPHA}$)"),

    # Endpoint meaning (dot size)
    Line2D([0], [0], linestyle="None", marker="o",
           markerfacecolor="0.35", markeredgecolor="0.35",
           markersize=MS_SMALL, label="Endpoint: T=2 (small dot)"),
    Line2D([0], [0], linestyle="None", marker="o",
           markerfacecolor="0.35", markeredgecolor="0.35",
           markersize=MS_LARGE, label="Endpoint: T=100 (large dot)"),
]

# =========================
# Draw legend-only figure
# =========================
fig = plt.figure(figsize=(10.5, 1.8))
ax = fig.add_subplot(111)
ax.axis("off")

leg = fig.legend(
    handles=handles,
    loc="center",
    ncol=3,               # 6 items -> 2 rows
    frameon=False,
    handlelength=2.6,
    columnspacing=1.6,
    handletextpad=0.6,
    borderaxespad=0.0,
)

# =========================
# Save
# =========================
out_svg = OUT_DIR / "legend_dumbbell_encoding.svg"
fig.savefig(out_svg, format="svg", bbox_inches="tight", pad_inches=0.02)
print(f"[SAVE] {out_svg}")

plt.show()


# ------------------------------------------------------------------------------
# Notebook cell 12
# ------------------------------------------------------------------------------
#8cbedd


# ------------------------------------------------------------------------------
# Notebook cell 13
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from math import erf, sqrt
import numpy as np
import pandas as pd

# =========================
# Paths
# =========================
BASE_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\statues_index")
IN_CSV   = BASE_DIR / "fe_components_Tall_5_10_20_30y_pid12_provYearFE_cityCluster_cityCluster.csv"

OUT_RAW  = BASE_DIR / "T_2_100_raw_rows.csv"
OUT_WIDE = BASE_DIR / "T_2_100_endpoints_wide.csv"

T_SMALL, T_LARGE = 2, 100
ALPHA = 0.05

# =========================
# p-value helpers (normal approx)
# =========================
def norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))

def p_two_sided_from_z(z: float) -> float:
    if not np.isfinite(z):
        return np.nan
    return 2.0 * (1.0 - norm_cdf(abs(z)))

# =========================
# Read & clean
# =========================
def read_results(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    for c in ["Unnamed: 0", "index"]:
        if c in df.columns:
            df = df.drop(columns=[c])

    required = ["sample", "window", "T", "outcome", "Estimate", "Std. Error"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}\nCheck: {csv_path}")

    df["window"] = pd.to_numeric(df["window"], errors="coerce")
    df["T"] = pd.to_numeric(df["T"], errors="coerce")
    df["Estimate"] = pd.to_numeric(df["Estimate"], errors="coerce")
    df["Std. Error"] = pd.to_numeric(df["Std. Error"], errors="coerce")

    df = df.dropna(subset=["sample", "window", "T", "outcome", "Estimate", "Std. Error"]).copy()
    df["sample"] = df["sample"].astype(str)
    df["window"] = df["window"].astype(int)
    df["T"] = df["T"].astype(int)
    df["outcome"] = df["outcome"].astype(str)

    if "domain" in df.columns:
        df["domain"] = df["domain"].astype(str)
    else:
        df["domain"] = ""

    return df

# =========================
# Export: raw rows (T=2,100 only)
# =========================
def export_raw_T_2_100(df_all: pd.DataFrame):
    df_sub = df_all[df_all["T"].isin([T_SMALL, T_LARGE])].copy()
    df_sub.to_csv(OUT_RAW, index=False, encoding="utf-8-sig")
    print(f"[SAVE] raw rows (T=2,100): {OUT_RAW}")

# =========================
# Export: wide endpoints table (one row per sample-window-outcome)
# Original notebook comment normalized for the public code archive.
# =========================
def export_endpoints_wide(df_all: pd.DataFrame):
    df = df_all[df_all["T"].isin([T_SMALL, T_LARGE])].copy()
    if df.empty:
        print("[WARN] No rows with T=2 or T=100.")
        return

    # School POI processing note.
    g = (df.groupby(["sample", "window", "outcome", "T"], as_index=False)
           .agg(Estimate=("Estimate", "mean"),
                StdError=("Std. Error", "mean")))

    # Original notebook comment normalized for the public code archive.
    beta = g.pivot(index=["sample", "window", "outcome"], columns="T", values="Estimate")
    se   = g.pivot(index=["sample", "window", "outcome"], columns="T", values="StdError")

    # Original notebook comment normalized for the public code archive.
    keep_idx = beta.dropna(subset=[T_SMALL, T_LARGE]).index
    beta = beta.loc[keep_idx]
    se   = se.loc[keep_idx]

    out = pd.DataFrame({
        "sample": [i[0] for i in keep_idx],
        "window": [i[1] for i in keep_idx],
        "outcome": [i[2] for i in keep_idx],
        "beta2": beta[T_SMALL].values,
        "beta100": beta[T_LARGE].values,
        "se2": se[T_SMALL].values,
        "se100": se[T_LARGE].values,
    })

    # Original notebook comment normalized for the public code archive.
    if "domain" in df_all.columns:
        dom = (df_all.groupby(["sample", "window", "outcome"], as_index=False)["domain"]
                     .agg(lambda x: x.dropna().astype(str).iloc[0] if len(x.dropna()) else ""))
        out = out.merge(dom, on=["sample", "window", "outcome"], how="left")
    else:
        out["domain"] = ""

    # Original notebook comment normalized for the public code archive.
    out["diff_100_minus_2"] = out["beta100"] - out["beta2"]
    out["se_diff"] = np.sqrt(out["se2"]**2 + out["se100"]**2)
    out["z_diff"] = out["diff_100_minus_2"] / out["se_diff"]
    out["p_diff"] = out["z_diff"].apply(p_two_sided_from_z)
    out["sig_trend"] = out["p_diff"] < ALPHA

    # Original notebook comment normalized for the public code archive.
    out = out.sort_values(["sample", "window", "domain", "outcome"], kind="mergesort")

    out.to_csv(OUT_WIDE, index=False, encoding="utf-8-sig")
    print(f"[SAVE] endpoints wide (T=2,100): {OUT_WIDE}")

# =========================
# Main
# =========================
if __name__ == "__main__":
    print(f"[INFO] Reading: {IN_CSV}")
    df_all = read_results(IN_CSV)

    export_raw_T_2_100(df_all)
    export_endpoints_wide(df_all)


# ------------------------------------------------------------------------------
# Notebook cell 17
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from math import erf, sqrt
import numpy as np
import pandas as pd

# =========================
# Paths
# =========================
BASE_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\statues_index")
IN_CSV   = BASE_DIR / "fe_components_Tall_5_10_20_30y_pid12_provYearFE_cityCluster_cityCluster.csv"
OUT_DIR  = BASE_DIR / "dumbbell_values"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Original notebook comment normalized for the public code archive.
OUT_CSV  = OUT_DIR / "figure_values_T2_T100_mergedWin5-10-20-30_rural_urban.csv"
OUT_XLSX = OUT_DIR / "figure_values_T2_T100_mergedWin5-10-20-30_rural_urban.xlsx"

# =========================
# Parameters (match your plotting script)
# =========================
WINDOW_LIST = [5, 10, 20, 30]
T_SMALL, T_LARGE = 2, 100
ALPHA = 0.05

# Original notebook comment normalized for the public code archive.
USE_CUSTOM_ORDER = True
APPEND_OTHERS = False

# =========================
# Custom order (same as your figure)
# =========================
PHYS_VARS_HIGH_BAD = [
    "dress", "bathe", "eat",
    "bed_chair_transfer", "toilet",
    "walk100m", "walk1km", "stairs",
    "run1km", "lift5kg", "bend_kneel_squat",
    "pick_coin", "incontinence", "housework",
    "arm_raise", "sit_to_stand",
]
PHYS_VARS_HIGH_GOOD = [
    "disease",
]
MENTAL_VARS_HIGH_BAD = [
    "cesd10_sum",
    "depress", "effort", "fear", "sleep", "hopeless",
    "life_satisfaction", "srh",
]
MENTAL_VARS_HIGH_GOOD = [
    "happy", "hope",
    "memory_disease",
    "mental_neuro_psych",
]
SOCIAL_VARS_HIGH_BAD = [
    "call_child_freq",
    "meet_child_freq",
    "social_freq",
    "social_activity",
]
SOCIAL_VARS_HIGH_GOOD = [
    "annual_transfer",
]

CUSTOM_ORDER_CLEAN = (
    PHYS_VARS_HIGH_BAD + PHYS_VARS_HIGH_GOOD
    + MENTAL_VARS_HIGH_BAD + MENTAL_VARS_HIGH_GOOD
    + SOCIAL_VARS_HIGH_BAD + SOCIAL_VARS_HIGH_GOOD
)

# =========================
# Stats helpers
# =========================
def norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))

def p_two_sided_from_z(z: float) -> float:
    if not np.isfinite(z):
        return np.nan
    return 2.0 * (1.0 - norm_cdf(abs(z)))

def clean_outcome_label(name: str) -> str:
    return str(name).replace("_norm2", "")

def normalize_key(name: str) -> str:
    return clean_outcome_label(name).strip()

# =========================
# IO
# =========================
def read_results(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    for c in ["Unnamed: 0", "index"]:
        if c in df.columns:
            df = df.drop(columns=[c])

    required = ["sample", "window", "T", "outcome", "Estimate", "Std. Error"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}\nCheck: {csv_path}")

    df["window"] = pd.to_numeric(df["window"], errors="coerce")
    df["T"] = pd.to_numeric(df["T"], errors="coerce")
    df["Estimate"] = pd.to_numeric(df["Estimate"], errors="coerce")
    df["Std. Error"] = pd.to_numeric(df["Std. Error"], errors="coerce")

    df = df.dropna(subset=["sample", "window", "T", "outcome", "Estimate", "Std. Error"]).copy()
    df["sample"] = df["sample"].astype(str)
    df["window"] = df["window"].astype(int)
    df["T"] = df["T"].astype(int)
    df["outcome"] = df["outcome"].astype(str)

    if "domain" in df.columns:
        df["domain"] = df["domain"].astype(str)
    else:
        df["domain"] = ""

    return df

# =========================
# IVW merge endpoints across windows (same as your figure script)
# =========================
def merged_endpoints(df_all: pd.DataFrame, sample: str) -> pd.DataFrame:
    df = df_all[(df_all["sample"] == sample) &
                (df_all["window"].isin(WINDOW_LIST)) &
                (df_all["T"].isin([T_SMALL, T_LARGE]))].copy()
    if df.empty:
        return pd.DataFrame()

    df["var"] = df["Std. Error"] ** 2
    df.loc[df["var"] <= 0, "var"] = np.nan
    df = df.dropna(subset=["var"]).copy()
    df["w"] = 1.0 / df["var"]

    def agg_one(g: pd.DataFrame) -> pd.Series:
        w = g["w"].to_numpy(float)
        est = g["Estimate"].to_numpy(float)
        beta_w = float(np.sum(w * est) / np.sum(w))
        se_w = float(np.sqrt(1.0 / np.sum(w)))
        return pd.Series({"beta_agg": beta_w, "se_agg": se_w})

    agg = (df.groupby(["outcome", "T"], as_index=False)
             .apply(agg_one)
             .reset_index(drop=True))

    beta = agg.pivot(index="outcome", columns="T", values="beta_agg")
    se   = agg.pivot(index="outcome", columns="T", values="se_agg")

    keep = beta.dropna(subset=[T_SMALL, T_LARGE]).copy()
    if keep.empty:
        return pd.DataFrame()

    out = pd.DataFrame({
        "outcome": keep.index,
        "beta2": keep[T_SMALL].values,
        "beta100": keep[T_LARGE].values,
        "se2": se.loc[keep.index, T_SMALL].values,
        "se100": se.loc[keep.index, T_LARGE].values,
    }).reset_index(drop=True)

    # Original notebook comment normalized for the public code archive.
    if "domain" in df_all.columns and df_all["domain"].notna().any():
        dom = (df_all[df_all["sample"] == sample]
               .groupby("outcome", as_index=False)["domain"]
               .agg(lambda x: x.dropna().astype(str).iloc[0] if len(x.dropna()) else ""))
        out = out.merge(dom, on="outcome", how="left")
    else:
        out["domain"] = ""

    # diff significance (same conservative approach)
    out["diff_100_minus_2"] = out["beta100"] - out["beta2"]
    out["se_diff"] = np.sqrt(out["se2"]**2 + out["se100"]**2)
    out["z_diff"] = out["diff_100_minus_2"] / out["se_diff"]
    out["p_diff"] = out["z_diff"].apply(p_two_sided_from_z)
    out["sig_trend"] = out["p_diff"] < ALPHA

    return out

# =========================
# Build order (same as your figure script)
# =========================
def build_order_custom(dat_r: pd.DataFrame, dat_u: pd.DataFrame) -> list[str]:
    common_full = sorted(set(dat_r["outcome"]) & set(dat_u["outcome"]))
    if not common_full:
        return []

    clean_to_full = {}
    for full in common_full:
        k = normalize_key(full)
        if k not in clean_to_full:
            clean_to_full[k] = full

    order_full = []
    for nm in CUSTOM_ORDER_CLEAN:
        k = normalize_key(nm)
        if k in clean_to_full:
            order_full.append(clean_to_full[k])

    if APPEND_OTHERS:
        rest = [x for x in common_full if x not in order_full]
        rest = sorted(rest, key=lambda s: normalize_key(s))
        order_full.extend(rest)

    return order_full

# =========================
# Export numeric file used by the figure
# =========================
def export_figure_values(df_all: pd.DataFrame):
    dat_r = merged_endpoints(df_all, "rural")
    dat_u = merged_endpoints(df_all, "urban")

    if dat_r.empty or dat_u.empty:
        raise RuntimeError("rural 或 urban 的合并端点为空；请检查 sample/window/T 是否匹配。")

    # order (match figure)
    if USE_CUSTOM_ORDER:
        order = build_order_custom(dat_r, dat_u)
    else:
        order = sorted(set(dat_r["outcome"]) & set(dat_u["outcome"]))

    if not order:
        raise RuntimeError("rural 与 urban 没有共同 outcome（或自定义列表一个也没匹配到）。")

    # restrict & order
    dat_r = dat_r.set_index("outcome").reindex(order).reset_index()
    dat_u = dat_u.set_index("outcome").reindex(order).reset_index()

    # merge into one table (one row per outcome) -> easiest “figure values file”
    out = pd.DataFrame({
        "outcome_full": order,
        "outcome_label": [clean_outcome_label(x) for x in order],
        "domain": dat_r["domain"].fillna(""),

        "rural_beta2": dat_r["beta2"],
        "rural_se2": dat_r["se2"],
        "rural_beta100": dat_r["beta100"],
        "rural_se100": dat_r["se100"],
        "rural_diff_100_minus_2": dat_r["diff_100_minus_2"],
        "rural_p_diff": dat_r["p_diff"],
        "rural_sig_trend": dat_r["sig_trend"],

        "urban_beta2": dat_u["beta2"],
        "urban_se2": dat_u["se2"],
        "urban_beta100": dat_u["beta100"],
        "urban_se100": dat_u["se100"],
        "urban_diff_100_minus_2": dat_u["diff_100_minus_2"],
        "urban_p_diff": dat_u["p_diff"],
        "urban_sig_trend": dat_u["sig_trend"],
    })

    # Original notebook comment normalized for the public code archive.
    out.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    out.to_excel(OUT_XLSX, index=False)
    print(f"[SAVE] {OUT_CSV}")
    print(f"[SAVE] {OUT_XLSX}")

if __name__ == "__main__":
    print(f"[INFO] Reading: {IN_CSV}")
    df_all = read_results(IN_CSV)
    export_figure_values(df_all)
