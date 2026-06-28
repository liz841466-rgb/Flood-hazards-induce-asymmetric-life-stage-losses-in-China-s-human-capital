#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 1
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pyfixest.estimation import feols

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)

# =============================================================================

# CHFS/CFHS processing note.
CHFS_PANEL_XLSX = Path(
    "/home/ll/jupyter_notebook/gis_data/Child/"
    "CHFS_家庭不平衡面板_2011_2019_带县代码_最终版.xlsx"
)

# CaMa-Flood processing note.
FLOOD_CSV = Path(
    "/home/ll/jupyter_notebook/result/county_storage_return_events/"
    "county_flood_events_T10_20_50_100_1980_2015.csv"
)

# Original notebook comment normalized for the public code archive.
OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/statistics/"
    "CHFS_mechanism_margins_k1"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

# CHFS/CFHS processing note.
OUT_PANEL_PARQUET = OUT_DIR / "CHFS_panel_with_flood_BM_k1_margins.parquet"

# Original notebook comment normalized for the public code archive.
OUT_RES_CSV = OUT_DIR / "CHFS_mechanism_margins_k1_results.csv"

# Original notebook comment normalized for the public code archive.
K_WINDOW = 1

# Original notebook comment normalized for the public code archive.
T_LIST = [2, 5, 10, 20, 50, 100]

# Original notebook comment normalized for the public code archive.
SAMPLES = ["all", "rural", "urban"]

# Original notebook comment normalized for the public code archive.
CONTROL_FML = "log_income + log_childnum + C(is_rural) + C(wave)"

# Original notebook comment normalized for the public code archive.
ONLY_HAS_CHILD_U15 = True

# Original notebook comment normalized for the public code archive.
BINARY_COLS = [f"flood_ge_T{t}" for t in T_LIST]

# Original notebook comment normalized for the public code archive.
CLUSTER_VAR = "county_code"

# Original notebook comment normalized for the public code archive.
MECH_SPECS = [
    dict(
        dep_var="has_edu_spend",
        pos_col=None,  # Original notebook comment normalized for the public code archive.
        label="教育培训参与率（是否有支出）",
        tag="train_extensive",
    ),
    dict(
        dep_var="edu_train_total",
        pos_col="edu_train_total",  # Original notebook comment normalized for the public code archive.
        label="教育培训支出（有支出家庭，元）",
        tag="train_intensive",
    ),
    dict(
        dep_var="has_edu_debt",
        pos_col=None,
        label="是否有教育负债",
        tag="debt_extensive",
    ),
    dict(
        dep_var="edu_debt_balance",
        pos_col="edu_debt_balance",  # Original notebook comment normalized for the public code archive.
        label="教育负债余额（有负债家庭，元）",
        tag="debt_intensive",
    ),
]


# =============================================================================

def normalize_tidy(res: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 01_household_education_investment_mechanism.

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
    return res


def get_nobs(fit, fallback_df: pd.DataFrame) -> int:
    """Archived notebook note for 01_household_education_investment_mechanism.

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


def stars_for_p(p: float) -> str:
    """Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    try:
        p = float(p)
    except (TypeError, ValueError):
        return ""
    if p < 0.01:
        return "***"
    elif p < 0.05:
        return "**"
    elif p < 0.10:
        return "*"
    else:
        return ""


# =============================================================================

def load_flood_panel():
    """Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print("[INFO] Notebook progress message.")
    df = pd.read_csv(FLOOD_CSV)

    if "county_code" in df.columns:
        county_col = "county_code"
    elif "county_id" in df.columns:
        county_col = "county_id"
    else:
        raise ValueError("洪水文件中没有 county_code 或 county_id 列。")

    df[county_col] = pd.to_numeric(df[county_col], errors="coerce").astype("Int64")
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    # Original notebook comment normalized for the public code archive.
    for c in BINARY_COLS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
        else:
            print("[INFO] Notebook progress message.")
            df[c] = 0

    df = df.dropna(subset=[county_col, "year"])
    print(
        f"[INFO] 洪水面板形状: {df.shape}, 年份: "
        f"{df['year'].min()}–{df['year'].max()}"
    )
    return df, county_col


def build_flood_window_k1(df_flood: pd.DataFrame,
                          county_col: str,
                          k: int = 1) -> pd.DataFrame:
    """Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df_flood.copy().sort_values([county_col, "year"])
    for c in BINARY_COLS:
        new_col = f"share_{c}_{k}y"
        df[new_col] = (
            df.groupby(county_col)[c]
              .rolling(window=k, min_periods=1)
              .mean()
              .reset_index(level=0, drop=True)
        )
    return df


# =============================================================================

def load_chfs_base() -> pd.DataFrame:
    """Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print("[INFO] Notebook progress message.")
    df = pd.read_excel(CHFS_PANEL_XLSX)
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    if "教育培训支出口径年份" in df.columns:
        df["edu_year"] = pd.to_numeric(df["教育培训支出口径年份"],
                                       errors="coerce").astype("Int64")
    elif "收入口径年份" in df.columns:
        df["edu_year"] = pd.to_numeric(df["收入口径年份"],
                                       errors="coerce").astype("Int64")
    else:
        raise KeyError("CHFS 中找不到『教育培训支出口径年份』或『收入口径年份』。")

    # Original notebook comment normalized for the public code archive.
    if "来源年份" in df.columns:
        df["wave"] = pd.to_numeric(df["来源年份"],
                                   errors="coerce").astype("Int64")
    else:
        raise KeyError("CHFS 中缺少列：来源年份")

    # Original notebook comment normalized for the public code archive.
    if "省" in df.columns:
        df["prov"] = df["省"].astype(str)
    else:
        df["prov"] = ""

    # is_rural
    if "是否农村" in df.columns:
        tmp = pd.to_numeric(df["是否农村"], errors="coerce")
        df["is_rural"] = np.where(tmp == 1, 1,
                                  np.where(tmp == 0, 0, np.nan))
    else:
        df["is_rural"] = np.nan

    # has_child_u15
    if "是否有15岁及以下儿童" in df.columns:
        tmp = pd.to_numeric(df["是否有15岁及以下儿童"], errors="coerce")
        df["has_child_u15"] = np.where(tmp == 1, 1,
                                       np.where(tmp == 0, 0, np.nan))
    else:
        df["has_child_u15"] = np.nan

    # n_child_u15
    if "15岁及以下儿童数量" in df.columns:
        df["n_child_u15"] = pd.to_numeric(df["15岁及以下儿童数量"],
                                          errors="coerce")
    else:
        df["n_child_u15"] = np.nan

    # income & log_income
    if "家庭可支配收入（元）" in df.columns:
        df["income"] = pd.to_numeric(df["家庭可支配收入（元）"],
                                     errors="coerce")
    else:
        df["income"] = np.nan
    df["income"] = df["income"].fillna(0)
    df["log_income"] = np.log(df["income"].clip(lower=0) + 1.0)

    # log_childnum
    df["n_child_u15"] = df["n_child_u15"].fillna(0)
    df["log_childnum"] = np.log(df["n_child_u15"].clip(lower=0) + 1.0)

    # Original notebook comment normalized for the public code archive.
    if "去年教育培训支出（元）" in df.columns:
        df["edu_train_total"] = pd.to_numeric(
            df["去年教育培训支出（元）"], errors="coerce"
        ).fillna(0)
    else:
        df["edu_train_total"] = 0.0
    df["edu_train_total"] = df["edu_train_total"].clip(lower=0)

    # Original notebook comment normalized for the public code archive.
    df["ln_edu_train_total"] = np.log(df["edu_train_total"] + 1.0)

    # Original notebook comment normalized for the public code archive.
    df["has_edu_spend"] = (df["edu_train_total"] > 0).astype(int)

    # Original notebook comment normalized for the public code archive.
    if "教育负债余额（元）" in df.columns:
        df["edu_debt_balance"] = pd.to_numeric(
            df["教育负债余额（元）"], errors="coerce"
        ).fillna(0)
    else:
        df["edu_debt_balance"] = 0.0
    df["edu_debt_balance"] = df["edu_debt_balance"].clip(lower=0)

    # Original notebook comment normalized for the public code archive.
    df["ln_edu_debt_balance"] = np.log(df["edu_debt_balance"] + 1.0)

    # Original notebook comment normalized for the public code archive.
    if "是否有教育负债（原始码1/2）" in df.columns:
        tmp = pd.to_numeric(df["是否有教育负债（原始码1/2）"],
                            errors="coerce")
        df["has_edu_debt"] = np.where(tmp == 1, 1,
                                      np.where(tmp == 2, 0, np.nan))
    else:
        # Original notebook comment normalized for the public code archive.
        df["has_edu_debt"] = (df["edu_debt_balance"] > 0).astype(int)

    # county_code
    if "county_code" not in df.columns:
        raise KeyError("CHFS 面板中缺少 county_code 列。")
    df["county_code"] = pd.to_numeric(df["county_code"],
                                      errors="coerce").astype("Int64")

    # County-level processing note.
    df = df.dropna(subset=["edu_year", "county_code"]).copy()
    print("[INFO] Notebook progress message.")

    return df


def prepare_sample(df: pd.DataFrame,
                   dep_var: str,
                   exp_var: str,
                   sample: str,
                   pos_col: "str | None" = None) -> pd.DataFrame:
    """Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    dfm = df.copy()

    if ONLY_HAS_CHILD_U15:
        dfm = dfm[dfm["has_child_u15"] == 1]

    if sample == "rural":
        dfm = dfm[dfm["is_rural"] == 1]
    elif sample == "urban":
        dfm = dfm[dfm["is_rural"] == 0]

    if pos_col is not None:
        dfm = dfm[dfm[pos_col] > 0]

    keep_cols = [
        dep_var, exp_var, "log_income", "log_childnum",
        "is_rural", "wave", "prov", "county_code"
    ]
    dfm = dfm.dropna(subset=keep_cols)

    dfm["county_code"] = pd.to_numeric(
        dfm["county_code"], errors="coerce"
    )
    dfm = dfm.dropna(subset=["county_code"])
    dfm["county_code"] = dfm["county_code"].astype("Int64")

    return dfm.reset_index(drop=True)


# =============================================================================

def merge_chfs_with_flood_k1(df_chfs_base: pd.DataFrame,
                             df_flood_k1: pd.DataFrame,
                             county_col: str,
                             flood_year_min: int,
                             flood_year_max: int) -> pd.DataFrame:
    """Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    suffix = f"_{K_WINDOW}y"  # "_1y"

    # Original notebook comment normalized for the public code archive.
    share_cols_k = [
        c for c in df_flood_k1.columns
        if c.startswith("share_flood_ge_T") and c.endswith(suffix)
    ]
    if not share_cols_k:
        raise ValueError(f"在洪水面板中找不到 k={K_WINDOW} 的 share 列。")

    cols_keep = [county_col, "year"] + share_cols_k
    flood_sub = df_flood_k1[cols_keep].copy()
    if county_col != "county_code":
        flood_sub = flood_sub.rename(columns={county_col: "county_code"})
    flood_sub = flood_sub.rename(columns={"year": "edu_year"})

    # CHFS/CFHS processing note.
    df_ch = df_chfs_base[
        df_chfs_base["edu_year"].between(flood_year_min, flood_year_max)
    ].copy()

    df_merged = df_ch.merge(
        flood_sub,
        how="left",
        on=["county_code", "edu_year"],
        validate="m:1",
    )
    print(
        f"[INFO] k={K_WINDOW}: 合并后 CHFS 行数 {df_merged.shape[0]}, "
        f"share 列数 {len(share_cols_k)}"
    )
    return df_merged


# =============================================================================

def run_mech_reg_for_k1(df_k: pd.DataFrame,
                        dep_var: str,
                        dep_label: str,
                        pos_col: "str | None",
                        sample: str) -> pd.DataFrame:
    """Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    records = []
    suffix = f"_{K_WINDOW}y"  # "_1y"

    for T in T_LIST:
        T_str = str(int(T))
        exp_var = f"share_flood_ge_T{T_str}{suffix}"

        if exp_var not in df_k.columns:
            print("[INFO] Notebook progress message.")
            continue

        dfm = prepare_sample(df_k, dep_var, exp_var, sample, pos_col=pos_col)
        print(
            f"[REG] dep={dep_var} ({dep_label}), sample={sample}, "
            f"k={K_WINDOW}, T={T_str}, N={len(dfm)}"
        )

        if len(dfm) < 200:
            print("[INFO] Notebook progress message.")
            continue

        fml = f"{dep_var} ~ {exp_var} + {CONTROL_FML}"
        try:
            fit = feols(fml, data=dfm, vcov={"CRV1": CLUSTER_VAR})
        except Exception as e:
            print("[INFO] Notebook progress message.")
            continue

        tidy = normalize_tidy(fit.tidy())
        sub = tidy[tidy["Term"].str.contains(exp_var, na=False)]
        if sub.empty:
            print("[INFO] Notebook progress message.")
            continue

        row = sub.iloc[0]
        est = float(row["Estimate"])
        se = float(row.get("StdError", np.nan))
        pv = float(row.get("PValue", np.nan))

        rec = {
            "dep_var": dep_var,
            "dep_label": dep_label,
            "sample": sample,
            "k_window": int(K_WINDOW),
            "T": float(T),
            "Term": exp_var,
            "Estimate": est,
            "StdError": se,
            "PValue": pv,
            "CI_low": est - 1.96 * se if np.isfinite(se) else np.nan,
            "CI_high": est + 1.96 * se if np.isfinite(se) else np.nan,
            "nobs": get_nobs(fit, dfm),
        }
        records.append(rec)

    return pd.DataFrame(records)


# =============================================================================

def plot_mech(df: pd.DataFrame,
              dep_var: str,
              dep_label: str,
              sample: str,
              title: str,
              ylabel: str,
              file_tag: str):
    """Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sub = df[
        (df["dep_var"] == dep_var)
        & (df["sample"] == sample)
        & (df["k_window"] == K_WINDOW)
    ].copy()
    if sub.empty:
        print("[INFO] Notebook progress message.")
        return

    sub["T"] = pd.to_numeric(sub["T"], errors="coerce")
    sub = sub.dropna(subset=["T", "Estimate"])
    if sub.empty:
        print("[INFO] Notebook progress message.")
        return

    sub = sub.sort_values("T")

    # Original notebook comment normalized for the public code archive.
    if {"CI_low", "CI_high"}.issubset(sub.columns):
        y_min = np.nanmin(sub["CI_low"].values)
        y_max = np.nanmax(sub["CI_high"].values)
    else:
        y_min = np.nanmin(sub["Estimate"].values)
        y_max = np.nanmax(sub["Estimate"].values)

    if (not np.isfinite(y_min)) or (not np.isfinite(y_max)) or (y_max <= y_min):
        y_min, y_max = -0.5, 0.5

    y_range = y_max - y_min
    pad = 0.08 * y_range if y_range > 0 else 0.1
    offset_y = 0.04 * y_range if y_range > 0 else 0.05

    T_vals = sub["T"].to_numpy(float)
    est = sub["Estimate"].to_numpy(float)

    # Original notebook comment normalized for the public code archive.
    if {"CI_low", "CI_high"}.issubset(sub.columns):
        ci_low = sub["CI_low"].to_numpy(float)
        ci_high = sub["CI_high"].to_numpy(float)
        yerr = np.vstack([est - ci_low, ci_high - est])
    else:
        se = sub["StdError"].to_numpy(float)
        yerr = 1.96 * se

    fig, ax = plt.subplots(figsize=(6.5, 4.5))

    ax.errorbar(
        T_vals,
        est,
        yerr=yerr,
        fmt="o",
        linestyle="none",
        capsize=4,
    )

    # Original notebook comment normalized for the public code archive.
    for xi, yi, (_, row) in zip(T_vals, est, sub.iterrows()):
        star = stars_for_p(row.get("PValue"))
        if star:
            ax.text(
                xi,
                yi + offset_y,
                star,
                ha="center",
                va="bottom",
                fontsize=9,
            )

    ax.axhline(0, linestyle="--", linewidth=1)

    ax.set_xlabel("洪水返回期 T（年）")
    ax.set_ylabel(ylabel)
    ax.set_title(f"{title}\n(sample = {sample})")

    ax.set_xticks(T_vals)
    ax.set_xticklabels([str(int(t)) for t in T_vals])

    ax.set_ylim(y_min - pad, y_max + pad)

    plt.tight_layout()

    out_path = OUT_DIR / f"{file_tag}_{sample}.png"
    plt.savefig(out_path, dpi=200)
    plt.show()
    print("[INFO] Notebook progress message.")


# =============================================================================

def main():
    # Original notebook comment normalized for the public code archive.
    df_flood, county_col = load_flood_panel()
    df_flood_k1 = build_flood_window_k1(df_flood, county_col, k=K_WINDOW)
    flood_year_min = int(df_flood_k1["year"].min())
    flood_year_max = int(df_flood_k1["year"].max())
    print("[INFO] Notebook progress message.")

    # CHFS/CFHS processing note.
    df_chfs_base = load_chfs_base()

    # Original notebook comment normalized for the public code archive.
    df_k1 = merge_chfs_with_flood_k1(
        df_chfs_base, df_flood_k1,
        county_col,
        flood_year_min, flood_year_max
    )
    df_k1["k_window"] = K_WINDOW

    # Original notebook comment normalized for the public code archive.
    df_k1.to_parquet(OUT_PANEL_PARQUET, index=False)
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    res_all_list = []
    for spec in MECH_SPECS:
        dep_var = spec["dep_var"]
        dep_label = spec["label"]
        pos_col = spec["pos_col"]
        for s in SAMPLES:
            res = run_mech_reg_for_k1(df_k1, dep_var, dep_label, pos_col, s)
            if not res.empty:
                res_all_list.append(res)

    if not res_all_list:
        print("[INFO] Notebook progress message.")
        return

    df_res_all = pd.concat(res_all_list, axis=0, ignore_index=True)
    df_res_all.to_csv(OUT_RES_CSV, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print(df_res_all.head())

    # Original notebook comment normalized for the public code archive.
    plot_cfgs = {
        "has_edu_spend": dict(
            title="洪水对教育培训参与率的影响（广延边际）",
            ylabel="系数：share_flood_ge_T_1y 对 是否有教育培训支出 的影响 (百分点)",
            file_base="mech_train_extensive",
        ),
        "edu_train_total": dict(
            title="洪水对教育培训支出金额的影响（有支出家庭，元）",
            ylabel="系数：share_flood_ge_T_1y 对 教育培训支出（元） 的影响",
            file_base="mech_train_intensive",
        ),
        "has_edu_debt": dict(
            title="洪水对教育负债发生的影响（广延边际）",
            ylabel="系数：share_flood_ge_T_1y 对 是否有教育负债 的影响 (百分点)",
            file_base="mech_debt_extensive",
        ),
        "edu_debt_balance": dict(
            title="洪水对教育负债余额的影响（有负债家庭，元）",
            ylabel="系数：share_flood_ge_T_1y 对 教育负债余额（元） 的影响",
            file_base="mech_debt_intensive",
        ),
    }

    for spec in MECH_SPECS:
        dep_var = spec["dep_var"]
        cfg = plot_cfgs.get(dep_var, None)
        if cfg is None:
            continue
        for s in SAMPLES:
            plot_mech(
                df=df_res_all,
                dep_var=dep_var,
                dep_label=spec["label"],
                sample=s,
                title=cfg["title"],
                ylabel=cfg["ylabel"],
                file_tag=cfg["file_base"],
            )

    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 6
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =============================================================================

RES_CSV = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/statistics/"
    "CHFS_mechanism_margins_k1/CHFS_mechanism_margins_k1_results.csv"
)

# Original notebook comment normalized for the public code archive.
DEP_ORDER = [
    "教育培训参与率（是否有支出）",
    "是否有教育负债",
    "教育培训支出（有支出家庭，元）",
    "教育负债余额（有负债家庭，元）",
]
DEP_ORDER_MAP = {lab: i for i, lab in enumerate(DEP_ORDER)}

SAMPLE_ORDER = ["all", "rural", "urban"]


# =============================================================================

def classify_dep_type(row) -> str:
    """Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    dep_var = str(row.get("dep_var", ""))
    dep_label = str(row.get("dep_label", ""))

    # Original notebook comment normalized for the public code archive.
    if dep_var.startswith("has_"):
        return "binary"
    if ("参与率" in dep_label) or ("是否" in dep_label):
        return "binary"

    # Original notebook comment normalized for the public code archive.
    if ("元" in dep_label) or ("amt" in dep_var) or ("amount" in dep_var):
        return "amount"

    return "amount"  # Original notebook comment normalized for the public code archive.


def load_results() -> pd.DataFrame:
    df = pd.read_csv(RES_CSV)

    # Original notebook comment normalized for the public code archive.
    for col in ["T", "Estimate", "StdError", "CI_low", "CI_high",
                "PValue", "k_window"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Original notebook comment normalized for the public code archive.
    df = df[df["k_window"] == 1].copy()

    # dep_type / dep_order
    df["dep_type"] = df.apply(classify_dep_type, axis=1)
    df["dep_order"] = df["dep_label"].map(DEP_ORDER_MAP)

    return df


# =============================================================================

def plot_heatmap_by_type(df: pd.DataFrame, dep_type: str = "binary"):
    """Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sub = df[df["dep_type"] == dep_type].copy()
    if sub.empty:
        print("[INFO] Notebook progress message.")
        return

    sub = sub.dropna(subset=["dep_label", "T", "Estimate"])
    sub["T_int"] = sub["T"].astype(int)

    # Original notebook comment normalized for the public code archive.
    def row_rank(r):
        d = DEP_ORDER_MAP.get(r["dep_label"], 999)
        s = SAMPLE_ORDER.index(r["sample"]) if r["sample"] in SAMPLE_ORDER else 999
        return d * 10 + s

    sub["row_rank"] = sub.apply(row_rank, axis=1)

    # Original notebook comment normalized for the public code archive.
    sub["row_label"] = (
        sub["dep_label"].astype(str)
        + " [" + sub["sample"].astype(str) + "]"
    )

    sub = sub.sort_values(["row_rank", "row_label", "T_int"])

    mat = sub.pivot_table(
        index="row_label",
        columns="T_int",
        values="Estimate",
        aggfunc="mean",
    )

    mat = mat.reindex(sorted(mat.columns), axis=1)

    fig, ax = plt.subplots(figsize=(7, max(4, 0.35 * mat.shape[0])))

    im = ax.imshow(mat.values, aspect="auto", cmap="bwr")

    ax.set_yticks(np.arange(mat.shape[0]))
    ax.set_yticklabels(mat.index.tolist(), fontsize=9)
    ax.set_xticks(np.arange(mat.shape[1]))
    ax.set_xticklabels(mat.columns.tolist())

    ax.set_xlabel("返回期 T（年）")
    if dep_type == "binary":
        ax.set_ylabel("机制 × 样本（概率类）")
        title_type = "有无类（概率）"
    else:
        ax.set_ylabel("机制 × 样本（金额类）")
        title_type = "金额类（元）"

    ax.set_title(f"Flood 系数热图：{title_type}")

    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("Estimate")

    plt.tight_layout()
    plt.show()


# ============== 3. main ==============

if __name__ == "__main__":
    df_all = load_results()

    # Original notebook comment normalized for the public code archive.
    plot_heatmap_by_type(df_all, dep_type="binary")

    # Original notebook comment normalized for the public code archive.
    plot_heatmap_by_type(df_all, dep_type="amount")


# ------------------------------------------------------------------------------
# Notebook cell 9
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =============================================================================

RES_CSV = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/statistics/"
    "CHFS_mechanism_margins_k1/CHFS_mechanism_margins_k1_results.csv"
)

T_LIST = [2, 5, 10, 20, 50, 100]

# Original notebook comment normalized for the public code archive.
DEP_ORDER = [
    "教育培训参与率（是否有支出）",
    "是否有教育负债",
]
DEP_ORDER_MAP = {lab: i for i, lab in enumerate(DEP_ORDER)}


# =============================================================================

def classify_dep_type(row) -> str:
    dep_var = str(row.get("dep_var", ""))
    dep_label = str(row.get("dep_label", ""))
    if dep_var.startswith("has_"):
        return "binary"
    if ("参与率" in dep_label) or ("是否" in dep_label):
        return "binary"
    if ("元" in dep_label) or ("amt" in dep_var) or ("amount" in dep_var):
        return "amount"
    return "amount"


def load_binary_results() -> pd.DataFrame:
    df = pd.read_csv(RES_CSV)

    for col in ["T", "Estimate", "StdError", "CI_low", "CI_high",
                "PValue", "k_window"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df[df["k_window"] == 1].copy()

    df["dep_type"] = df.apply(classify_dep_type, axis=1)
    df["dep_order"] = df["dep_label"].map(DEP_ORDER_MAP)

    # Original notebook comment normalized for the public code archive.
    df = df[df["dep_type"] == "binary"].copy()

    return df


# =============================================================================

def stars_for_p(p: float) -> str:
    try:
        p = float(p)
    except (TypeError, ValueError):
        return ""
    if p < 0.01:
        return "***"
    elif p < 0.05:
        return "**"
    elif p < 0.10:
        return "*"
    else:
        return ""


# =============================================================================

def plot_binary_dot_whisker_allT(df: pd.DataFrame, sample: str = "rural"):
    """Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sub = df[df["sample"] == sample].copy()
    if sub.empty:
        print("[INFO] Notebook progress message.")
        return

    sub["T_int"] = sub["T"].astype(int)
    sub = sub.dropna(subset=["dep_label", "Estimate"])

    # Original notebook comment normalized for the public code archive.
    sub = sub.sort_values(["dep_order", "dep_label", "T_int"])

    # Original notebook comment normalized for the public code archive.
    sub["y_label"] = sub.apply(
        lambda r: f"{r['dep_label']}，T={int(r['T_int'])}", axis=1
    )

    y_labels = sub["y_label"].tolist()
    y_pos = np.arange(len(y_labels))

    est = sub["Estimate"].to_numpy(float)

    # CI / SE
    if {"CI_low", "CI_high"}.issubset(sub.columns) and sub["CI_low"].notna().any():
        ci_low = sub["CI_low"].to_numpy(float)
        ci_high = sub["CI_high"].to_numpy(float)
        xerr = np.vstack([est - ci_low, ci_high - est])
    else:
        se = sub["StdError"].to_numpy(float)
        xerr = 1.96 * se

    # Original notebook comment normalized for the public code archive.
    x_min = np.nanmin(est - (xerr[0] if xerr.ndim == 2 else xerr))
    x_max = np.nanmax(est + (xerr[1] if xerr.ndim == 2 else xerr))
    if not np.isfinite(x_min) or not np.isfinite(x_max) or x_max <= x_min:
        x_min, x_max = -0.5, 0.5
    x_range = x_max - x_min
    star_offset = 0.03 * x_range if x_range > 0 else 0.05

    fig, ax = plt.subplots(figsize=(7, max(4, 0.35 * len(y_labels))))

    ax.errorbar(
        est,
        y_pos,
        xerr=xerr,
        fmt="o",
        linestyle="none",
        capsize=4,
        color="tab:blue",
    )

    # Original notebook comment normalized for the public code archive.
    for xi, yi, (_, row) in zip(est, y_pos, sub.iterrows()):
        star = stars_for_p(row["PValue"])
        if star:
            ax.text(
                xi + star_offset,
                yi,
                star,
                va="center",
                ha="left",
                fontsize=9,
            )

    ax.axvline(0, linestyle="--", linewidth=1, color="gray")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(y_labels, fontsize=9)

    ax.set_xlabel("Flood 系数（概率/参与率变化）")
    ax.set_title(f"Dot-and-whisker：所有 T 的有无类机制（sample = {sample}）")

    plt.tight_layout()
    plt.show()


# =============================================================================

def plot_binary_bar_allT(df: pd.DataFrame, sample: str = "rural"):
    """Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sub = df[df["sample"] == sample].copy()
    if sub.empty:
        print("[INFO] Notebook progress message.")
        return

    sub["T_int"] = sub["T"].astype(int)

    mechanisms = [m for m in DEP_ORDER if m in sub["dep_label"].unique()]
    if not mechanisms:
        print("[INFO] Notebook progress message.")
        return

    n_mech = len(mechanisms)
    mech_colors = plt.cm.Set1(np.linspace(0, 1, n_mech))

    T_vals = [t for t in T_LIST if t in sub["T_int"].unique()]
    x_base = np.arange(len(T_vals))
    width = 0.8 / n_mech

    fig, ax = plt.subplots(figsize=(7, 4))

    for j, m in enumerate(mechanisms):
        tmp = sub[sub["dep_label"] == m].set_index("T_int")

        est_list = []
        yerr_low_list = []
        yerr_high_list = []

        for t in T_vals:
            if t in tmp.index:
                row = tmp.loc[t]
                est = float(row["Estimate"])
                if {"CI_low", "CI_high"}.issubset(tmp.columns) and pd.notna(row["CI_low"]):
                    yerr_low = est - float(row["CI_low"])
                    yerr_high = float(row["CI_high"]) - est
                else:
                    se = float(row["StdError"])
                    yerr_low = 1.96 * se
                    yerr_high = 1.96 * se
                star = stars_for_p(row["PValue"])
            else:
                est = 0.0
                yerr_low = 0.0
                yerr_high = 0.0
                star = ""

            est_list.append(est)
            yerr_low_list.append(yerr_low)
            yerr_high_list.append(yerr_high)

        est_arr = np.array(est_list)
        yerr = np.vstack([yerr_low_list, yerr_high_list])

        x_pos = x_base + (j - (n_mech - 1) / 2) * width

        ax.bar(
            x_pos,
            est_arr,
            width,
            yerr=yerr,
            capsize=4,
            label=m,
            color=mech_colors[j],
            alpha=0.9,
        )

        # Original notebook comment normalized for the public code archive.
        for xi, yi, yl, yh in zip(x_pos, est_arr, yerr_low_list, yerr_high_list):
            # Original notebook comment normalized for the public code archive.
            if yl == yh == 0:
                continue
            # Original notebook comment normalized for the public code archive.
            t_idx = T_vals[list(x_pos).index(xi)]
            row = tmp.loc[t_idx] if t_idx in tmp.index else None
            if row is not None:
                star = stars_for_p(row["PValue"])
                if star:
                    ax.text(
                        xi,
                        yi + (yh if yi >= 0 else -yl),
                        star,
                        ha="center",
                        va="bottom" if yi >= 0 else "top",
                        fontsize=9,
                    )

    ax.axhline(0, linestyle="--", linewidth=1, color="gray")

    ax.set_xticks(x_base)
    ax.set_xticklabels([str(int(t)) for t in T_vals])

    ax.set_xlabel("返回期 T（年）")
    ax.set_ylabel("Flood 系数（概率/参与率变化）")
    ax.set_title(f"条形图：所有 T 的有无类机制（sample = {sample}）")
    ax.legend(title="机制")

    plt.tight_layout()
    plt.show()


# ============== 5. main ==============

if __name__ == "__main__":
    df_bin = load_binary_results()

    # rural：Dot-and-whisker + Bar
    plot_binary_dot_whisker_allT(df_bin, sample="rural")
    plot_binary_bar_allT(df_bin, sample="rural")

    # urban：Dot-and-whisker + Bar
    plot_binary_dot_whisker_allT(df_bin, sample="urban")
    plot_binary_bar_allT(df_bin, sample="urban")


# ------------------------------------------------------------------------------
# Notebook cell 12
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =============================================================================

RES_CSV = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/statistics/"
    "CHFS_mechanism_margins_k1/CHFS_mechanism_margins_k1_results.csv"
)


# =============================================================================

def stars_for_p(p: float) -> str:
    """Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    try:
        p = float(p)
    except (TypeError, ValueError):
        return ""
    if p < 0.01:
        return "***"
    elif p < 0.05:
        return "**"
    elif p < 0.10:
        return "*"
    else:
        return ""


def load_results() -> pd.DataFrame:
    """Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print("[INFO] Notebook progress message.")
    df = pd.read_csv(RES_CSV)

    # Original notebook comment normalized for the public code archive.
    for col in ["T", "Estimate", "StdError", "PValue", "CI_low", "CI_high", "k_window"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    print("[INFO] Notebook progress message.")
    return df


# =============================================================================

def plot_binary_bar_one_dep(df: pd.DataFrame,
                            dep_var: str,
                            k_window: int = 1) -> None:
    """Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    # Original notebook comment normalized for the public code archive.
    sub = df[
        (df["dep_var"] == dep_var)
        & (df["k_window"] == k_window)
        & (df["sample"].isin(["rural", "urban"]))
    ].copy()

    if sub.empty:
        print("[INFO] Notebook progress message.")
        return

    # Original notebook comment normalized for the public code archive.
    T_vals = sorted(sub["T"].dropna().unique())
    if not T_vals:
        print("[INFO] Notebook progress message.")
        return

    # Original notebook comment normalized for the public code archive.
    x_base = np.arange(len(T_vals))
    width = 0.35  # Original notebook comment normalized for the public code archive.

    # Original notebook comment normalized for the public code archive.
    if "dep_label" in sub.columns:
        dep_label = sub["dep_label"].dropna().unique()
        dep_label = dep_label[0] if len(dep_label) > 0 else dep_var
    else:
        dep_label = dep_var

    fig, ax = plt.subplots(figsize=(7, 4.5))

    # Original notebook comment normalized for the public code archive.
    # Original notebook comment normalized for the public code archive.
    data_by_sample = {}
    for s in ["rural", "urban"]:
        tmp = sub[sub["sample"] == s].copy()
        if tmp.empty:
            data_by_sample[s] = None
            continue
        tmp = tmp.set_index("T").reindex(T_vals)  # Original notebook comment normalized for the public code archive.
        data_by_sample[s] = tmp

    # Original notebook comment normalized for the public code archive.
    for i, s in enumerate(["rural", "urban"]):
        tmp = data_by_sample[s]
        if tmp is None:
            print("[INFO] Notebook progress message.")
            continue

        est = tmp["Estimate"].to_numpy(float)

        # Original notebook comment normalized for the public code archive.
        if {"CI_low", "CI_high"}.issubset(tmp.columns):
            ci_low = tmp["CI_low"].to_numpy(float)
            ci_high = tmp["CI_high"].to_numpy(float)
            yerr = np.vstack([est - ci_low, ci_high - est])
        else:
            se = tmp["StdError"].to_numpy(float)
            yerr = 1.96 * se

        x_pos = x_base + (i - 0.5) * width  # Original notebook comment normalized for the public code archive.

        # Original notebook comment normalized for the public code archive.
        bars = ax.bar(
            x_pos,
            est,
            width=width,
            yerr=yerr,
            capsize=4,
            label=f"{s}",
        )

        # Original notebook comment normalized for the public code archive.
        if "PValue" in tmp.columns:
            pvals = tmp["PValue"].to_numpy(float)
        else:
            pvals = np.full_like(est, np.nan)

        # Original notebook comment normalized for the public code archive.
        # Original notebook comment normalized for the public code archive.
        for xi, yi, pv in zip(x_pos, est, pvals):
            if not np.isfinite(yi):
                continue
            star = stars_for_p(pv)
            if star:
                ax.text(
                    xi,
                    yi + np.sign(yi) * 0.02 * max(1.0, abs(yi)),  # Original notebook comment normalized for the public code archive.
                    star,
                    ha="center",
                    va="bottom" if yi >= 0 else "top",
                    fontsize=9,
                )

    # Original notebook comment normalized for the public code archive.
    ax.axhline(0, linestyle="--", linewidth=1, color="gray")

    # Original notebook comment normalized for the public code archive.
    ax.set_xticks(x_base)
    ax.set_xticklabels([str(int(t)) for t in T_vals])

    ax.set_xlabel("洪水返回期 T（年）")
    ax.set_ylabel(f"Flood 系数（{dep_label}）")
    ax.set_title(f"{dep_label} × 洪水暴露系数（k = {k_window} 年窗口，rural vs urban）")

    ax.legend(title="样本类型")
    plt.tight_layout()
    plt.show()


# =============================================================================

def main():
    df = load_results()

    # Original notebook comment normalized for the public code archive.
    df_k1 = df[df["k_window"] == 1].copy()
    if df_k1.empty:
        print("[INFO] Notebook progress message.")
        return

    # Original notebook comment normalized for the public code archive.
    binary_dep_vars = (
        df_k1.loc[df_k1["dep_var"].astype(str).str.startswith("has_"), "dep_var"]
        .dropna()
        .unique()
    )

    print("[INFO] Notebook progress message.")

    for dep in binary_dep_vars:
        print("[INFO] Notebook progress message.")
        plot_binary_bar_one_dep(df_k1, dep_var=dep, k_window=1)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 15
# ------------------------------------------------------------------------------


#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf

# =============================================================================

# CHFS/CFHS processing note.
CHFS_PANEL_XLSX = Path(
    "/home/ll/jupyter_notebook/gis_data/Child/"
    "CHFS_家庭不平衡面板_2011_2019_带县代码_最终版.xlsx"
)

# CaMa-Flood processing note.
FLOOD_CSV = Path(
    "/home/ll/jupyter_notebook/result/county_storage_return_events/"
    "county_flood_events_T10_20_50_100_1980_2015.csv"
)

# Original notebook comment normalized for the public code archive.
T_LIST = [2, 5, 10, 20, 50, 100]

# Original notebook comment normalized for the public code archive.
BINARY_COLS = [f"flood_ge_T{t}" for t in T_LIST]

# Original notebook comment normalized for the public code archive.
K_WINDOW = 1

# Original notebook comment normalized for the public code archive.
ONLY_HAS_CHILD_U15 = True


# =============================================================================

def load_flood_panel():
    """Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print("[INFO] Notebook progress message.")
    df = pd.read_csv(FLOOD_CSV)

    if "county_code" in df.columns:
        county_col = "county_code"
    elif "county_id" in df.columns:
        county_col = "county_id"
    else:
        raise ValueError("洪水文件中没有 county_code 或 county_id 列。")

    df[county_col] = pd.to_numeric(df[county_col], errors="coerce").astype("Int64")
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    # Original notebook comment normalized for the public code archive.
    for c in BINARY_COLS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
        else:
            print("[INFO] Notebook progress message.")
            df[c] = 0

    df = df.dropna(subset=[county_col, "year"])
    print(
        f"[INFO] 洪水面板形状: {df.shape}, 年份范围: "
        f"{df['year'].min()}–{df['year'].max()}"
    )
    return df, county_col


def build_flood_window_k1(df_flood: pd.DataFrame,
                          county_col: str) -> pd.DataFrame:
    """Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df_flood.copy().sort_values([county_col, "year"])

    for c in BINARY_COLS:
        new_col = f"share_{c}_1y"
        df[new_col] = df.groupby(county_col)[c].rolling(
            window=K_WINDOW, min_periods=1
        ).mean().reset_index(level=0, drop=True)

    return df


def load_chfs_base() -> pd.DataFrame:
    """Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print("[INFO] Notebook progress message.")
    df = pd.read_excel(CHFS_PANEL_XLSX)
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    if "教育培训支出口径年份" in df.columns:
        df["edu_year"] = pd.to_numeric(df["教育培训支出口径年份"],
                                       errors="coerce").astype("Int64")
    elif "收入口径年份" in df.columns:
        df["edu_year"] = pd.to_numeric(df["收入口径年份"],
                                       errors="coerce").astype("Int64")
    else:
        raise KeyError("CHFS 中找不到『教育培训支出口径年份』或『收入口径年份』。")

    # Original notebook comment normalized for the public code archive.
    if "来源年份" in df.columns:
        df["wave"] = pd.to_numeric(df["来源年份"],
                                   errors="coerce").astype("Int64")
    else:
        raise KeyError("CHFS 中缺少列：来源年份")

    # Original notebook comment normalized for the public code archive.
    if "省" in df.columns:
        df["prov"] = df["省"].astype(str)
    else:
        df["prov"] = ""

    # is_rural
    if "是否农村" in df.columns:
        tmp = pd.to_numeric(df["是否农村"], errors="coerce")
        df["is_rural"] = np.where(tmp == 1, 1,
                                  np.where(tmp == 0, 0, np.nan))
    else:
        df["is_rural"] = np.nan

    # has_child_u15
    if "是否有15岁及以下儿童" in df.columns:
        tmp = pd.to_numeric(df["是否有15岁及以下儿童"], errors="coerce")
        df["has_child_u15"] = np.where(tmp == 1, 1,
                                       np.where(tmp == 0, 0, np.nan))
    else:
        df["has_child_u15"] = np.nan

    # n_child_u15
    if "15岁及以下儿童数量" in df.columns:
        df["n_child_u15"] = pd.to_numeric(df["15岁及以下儿童数量"],
                                          errors="coerce")
    else:
        df["n_child_u15"] = np.nan

    # income & log_income
    if "家庭可支配收入（元）" in df.columns:
        df["income"] = pd.to_numeric(df["家庭可支配收入（元）"],
                                     errors="coerce")
    else:
        df["income"] = np.nan
    df["income"] = df["income"].fillna(0)
    df["log_income"] = np.log(df["income"].clip(lower=0) + 1.0)

    # log_childnum
    df["n_child_u15"] = df["n_child_u15"].fillna(0)
    df["log_childnum"] = np.log(df["n_child_u15"].clip(lower=0) + 1.0)

    # Original notebook comment normalized for the public code archive.
    if "去年教育培训支出（元）" in df.columns:
        edu_amount = pd.to_numeric(df["去年教育培训支出（元）"],
                                   errors="coerce").fillna(0)
    else:
        edu_amount = pd.Series(0.0, index=df.index)
    df["edu_amount"] = edu_amount.clip(lower=0)

    # Original notebook comment normalized for the public code archive.
    if "教育负债余额（元）" in df.columns:
        debt_bal = pd.to_numeric(df["教育负债余额（元）"],
                                 errors="coerce").fillna(0)
    else:
        debt_bal = pd.Series(0.0, index=df.index)
    df["edu_debt_balance"] = debt_bal.clip(lower=0)

    # county_code
    if "county_code" not in df.columns:
        raise KeyError("CHFS 面板中缺少 county_code 列。")
    df["county_code"] = pd.to_numeric(df["county_code"],
                                      errors="coerce").astype("Int64")

    # County-level processing note.
    df = df.dropna(subset=["edu_year", "county_code"]).copy()
    print("[INFO] Notebook progress message.")

    return df


def merge_chfs_flood_k1() -> pd.DataFrame:
    """Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    # Original notebook comment normalized for the public code archive.
    df_flood, county_col = load_flood_panel()
    df_flood_k1 = build_flood_window_k1(df_flood, county_col)

    flood_year_min = int(df_flood_k1["year"].min())
    flood_year_max = int(df_flood_k1["year"].max())
    print("[INFO] Notebook progress message.")

    # County-level processing note.
    share_cols = [
        c for c in df_flood_k1.columns
        if c.startswith("share_flood_ge_T") and c.endswith("_1y")
    ]
    keep_cols = [county_col, "year"] + share_cols
    flood_sub = df_flood_k1[keep_cols].copy()

    # County-level processing note.
    if county_col != "county_code":
        flood_sub = flood_sub.rename(columns={county_col: "county_code"})
    flood_sub = flood_sub.rename(columns={"year": "edu_year"})

    # CHFS
    df_chfs = load_chfs_base()
    df_chfs = df_chfs[
        df_chfs["edu_year"].between(flood_year_min, flood_year_max)
    ].copy()

    df_merged = df_chfs.merge(
        flood_sub,
        how="left",
        on=["county_code", "edu_year"],
        validate="m:1",
    )
    print("[INFO] Notebook progress message.")
    return df_merged


# =============================================================================

def prepare_sample_for_plot(df_all: pd.DataFrame,
                            dep_var: str,
                            T: int,
                            sample: str = "all") -> tuple[pd.DataFrame, str]:
    """Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    T_str = str(int(T))
    exp_var = f"share_flood_ge_T{T_str}_1y"

    if exp_var not in df_all.columns:
        raise KeyError(f"找不到暴露列: {exp_var}")

    # Original notebook comment normalized for the public code archive.
    df = df_all.copy()

    # Original notebook comment normalized for the public code archive.
    if ONLY_HAS_CHILD_U15:
        df = df[df["has_child_u15"] == 1]

    # Original notebook comment normalized for the public code archive.
    if sample == "rural":
        df = df[df["is_rural"] == 1]
    elif sample == "urban":
        df = df[df["is_rural"] == 0]
    # Original notebook comment normalized for the public code archive.

    # Original notebook comment normalized for the public code archive.
    keep_cols = [
        dep_var, exp_var,
        "log_income", "log_childnum", "is_rural", "wave"
    ]
    df = df.dropna(subset=keep_cols).copy()

    if df.empty:
        raise ValueError(f"dep_var={dep_var}, T={T}, sample={sample} 有效样本为空。")

    # Original notebook comment normalized for the public code archive.
    # Original notebook comment normalized for the public code archive.
    df["wave"] = df["wave"].astype(int)
    df["is_rural"] = df["is_rural"].astype(int)

    print(
        f"[INFO] 绘图子样本: dep_var={dep_var}, T={T}, sample={sample}, "
        f"N={len(df)}"
    )
    return df, exp_var



def plot_amount_scatter(df_all: pd.DataFrame,
                        dep_var: str,
                        dep_label: str,
                        T: int,
                        sample: str = "all",
                        partial: bool = True):
    """Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df, exp_var = prepare_sample_for_plot(df_all, dep_var, T, sample)

    if partial:
        # =============================================================================
        ctl = "log_income + log_childnum + C(is_rural) + C(wave)"

        # y ~ controls
        fml_y = f"{dep_var} ~ {ctl}"
        res_y = smf.ols(fml_y, data=df).fit()
        y_res = res_y.resid

        # x ~ controls
        fml_x = f"{exp_var} ~ {ctl}"
        res_x = smf.ols(fml_x, data=df).fit()
        x_res = res_x.resid

        x = x_res.to_numpy()
        y = y_res.to_numpy()
        x_label = f"{exp_var}（控制后残差）"
        y_label = f"{dep_label}（控制后残差）"

        title_suffix = "（部分残差图：已控制收入、儿童数、城乡、波次）"

    else:
        # =============================================================================
        x = df[exp_var].to_numpy(float)
        y = df[dep_var].to_numpy(float)
        x_label = exp_var
        y_label = dep_label
        title_suffix = "（原始值：未控制协变量）"

    # Original notebook comment normalized for the public code archive.
    mask = np.isfinite(x) & np.isfinite(y)
    x = x[mask]
    y = y[mask]

    if len(x) < 50:
        print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    beta1, beta0 = np.polyfit(x, y, 1)

    # Original notebook comment normalized for the public code archive.
    x_min, x_max = np.quantile(x, [0.01, 0.99])
    xs = np.linspace(x_min, x_max, 100)
    ys = beta0 + beta1 * xs

    # =============================================================================
    plt.figure(figsize=(6.5, 4.5))

    # Original notebook comment normalized for the public code archive.
    plt.scatter(x, y, alpha=0.2, s=10, label="家庭观测值")

    # Original notebook comment normalized for the public code archive.
    plt.plot(xs, ys, linewidth=2, label=f"线性拟合：y = {beta0:.2f} + {beta1:.2f} x")

    plt.axhline(0, linestyle="--", linewidth=1, color="gray")

    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(
        f"{dep_label} × 洪水暴露散点 + 回归线\n"
        f"T = {T} 年, sample = {sample} {title_suffix}"
    )

    plt.legend()
    plt.tight_layout()
    plt.show()


# =============================================================================

def main():
    # Original notebook comment normalized for the public code archive.
    df_panel = merge_chfs_flood_k1()

    # Original notebook comment normalized for the public code archive.
    print("[INFO] Notebook progress message.")
    plot_amount_scatter(
        df_panel,
        dep_var="edu_amount",
        dep_label="教育培训支出（元）",
        T=20,
        sample="rural",
        partial=True,
    )

    print("[INFO] Notebook progress message.")
    plot_amount_scatter(
        df_panel,
        dep_var="edu_amount",
        dep_label="教育培训支出（元）",
        T=20,
        sample="urban",
        partial=True,
    )

    # Original notebook comment normalized for the public code archive.
    print("[INFO] Notebook progress message.")
    plot_amount_scatter(
        df_panel,
        dep_var="edu_debt_balance",
        dep_label="教育负债余额（元）",
        T=20,
        sample="all",
        partial=False,
    )


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 17
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf

# =============================================================================

PANEL_PARQUET = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/statistics/"
    "CHFS_mechanism_windows_1to5/CHFS_panel_with_flood_BM_1to5y.parquet"
)

# Original notebook comment normalized for the public code archive.
T_LIST = [2, 5, 10, 20, 50, 100]
K_WINDOW = 1   # Original notebook comment normalized for the public code archive.

# Original notebook comment normalized for the public code archive.
CONTROL_FML_RHS = "log_income + log_childnum + C(is_rural) + C(wave)"


# =============================================================================

def add_amount_vars(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()

    # Original notebook comment normalized for the public code archive.
    if "edu_amount" not in df.columns:
        if "去年教育培训支出（元）" in df.columns:
            df["edu_amount"] = pd.to_numeric(
                df["去年教育培训支出（元）"], errors="coerce"
            ).fillna(0)
        elif "edu_train_total" in df.columns:
            df["edu_amount"] = pd.to_numeric(
                df["edu_train_total"], errors="coerce"
            ).fillna(0)
        else:
            raise KeyError(
                "找不到『去年教育培训支出（元）』或 'edu_train_total'，无法生成 edu_amount。"
            )

    # Original notebook comment normalized for the public code archive.
    if "edu_debt_balance" not in df.columns:
        if "教育负债余额（元）" in df.columns:
            df["edu_debt_balance"] = pd.to_numeric(
                df["教育负债余额（元）"], errors="coerce"
            ).fillna(0)
        else:
            # Original notebook comment normalized for the public code archive.
            df["edu_debt_balance"] = np.nan

    return df


# =============================================================================

def filter_sample(df: pd.DataFrame, sample: str) -> pd.DataFrame:
    """Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()

    # Original notebook comment normalized for the public code archive.
    if "has_child_u15" in df.columns:
        df = df[df["has_child_u15"] == 1]

    # Original notebook comment normalized for the public code archive.
    if sample == "rural":
        df = df[df["is_rural"] == 1]
    elif sample == "urban":
        df = df[df["is_rural"] == 0]
    # Original notebook comment normalized for the public code archive.

    return df


def partial_residuals(df: pd.DataFrame,
                      dep_var: str,
                      exp_var: str) -> tuple[np.ndarray, np.ndarray]:
    """Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()

    cols_for_reg = [
        dep_var, exp_var,
        "log_income", "log_childnum", "is_rural", "wave"
    ]
    for c in cols_for_reg:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")

    # Original notebook comment normalized for the public code archive.
    df = df.dropna(subset=[dep_var, exp_var, "log_income", "log_childnum", "is_rural", "wave"])

    if df.empty:
        return np.array([]), np.array([])

    fml_y = f"{dep_var} ~ {CONTROL_FML_RHS}"
    fml_x = f"{exp_var} ~ {CONTROL_FML_RHS}"

    res_y = smf.ols(fml_y, data=df).fit()
    res_x = smf.ols(fml_x, data=df).fit()

    y_res = res_y.resid.to_numpy(float)
    x_res = res_x.resid.to_numpy(float)
    return x_res, y_res


# =============================================================================

def plot_amount_scatter_allT(df_all: pd.DataFrame,
                             dep_var: str = "edu_amount",
                             dep_label: str = "教育金额（元）",
                             sample: str = "rural",
                             partial: bool = True):
    """Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = filter_sample(df_all, sample)

    # Original notebook comment normalized for the public code archive.
    for c in ["log_income", "log_childnum", "is_rural", "wave"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")

    colors = plt.cm.tab10(np.linspace(0, 1, len(T_LIST)))

    fig, ax = plt.subplots(figsize=(7, 5))

    any_plotted = False

    for idx, T in enumerate(T_LIST):
        exp_col = f"share_flood_ge_T{int(T)}_{K_WINDOW}y"
        if exp_col not in df.columns:
            print("[INFO] Notebook progress message.")
            continue

        # Original notebook comment normalized for the public code archive.
        cols_needed = [dep_var, exp_col, "log_income", "log_childnum",
                       "is_rural", "wave"]
        cols_existing = [c for c in cols_needed if c in df.columns]

        sub = df.dropna(subset=cols_existing).copy()
        if sub.empty:
            print("[INFO] Notebook progress message.")
            continue

        if partial:
            x, y = partial_residuals(sub, dep_var=dep_var, exp_var=exp_col)
            if x.size == 0:
                print("[INFO] Notebook progress message.")
                continue
            xlabel = f"{exp_col}（控制后残差）"
            ylabel = f"{dep_label}（控制后残差）"
            title_suffix = "（部分残差图：已控制收入、儿童数、城乡、波次）"
        else:
            x = sub[exp_col].to_numpy(float)
            y = sub[dep_var].to_numpy(float)
            xlabel = exp_col
            ylabel = dep_label
            title_suffix = "（原始值散点图）"

        ax.scatter(
            x,
            y,
            s=8,
            alpha=0.3,
            color=colors[idx],
            label=f"T = {int(T)} 年",
        )
        any_plotted = True

    if not any_plotted:
        print("[INFO] Notebook progress message.")
        return

    # Original notebook comment normalized for the public code archive.
    if partial:
        ax.axvline(0, color="grey", linestyle="--", linewidth=1)
    ax.axhline(0, color="grey", linestyle="--", linewidth=1)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(
        f"{dep_label} × 洪水暴露散点图\n"
        f"sample = {sample}{title_suffix}"
    )
    ax.legend(markerscale=2, fontsize=9)
    plt.tight_layout()
    plt.show()


# =============================================================================

def main():
    print("[INFO] Notebook progress message.")
    df_panel = pd.read_parquet(PANEL_PARQUET)

    # Original notebook comment normalized for the public code archive.
    df_panel = add_amount_vars(df_panel)

    # Original notebook comment normalized for the public code archive.
    print("[INFO] Notebook progress message.")
    plot_amount_scatter_allT(
        df_panel,
        dep_var="edu_amount",
        dep_label="教育培训支出（元）",
        sample="rural",
        partial=True,   # Original notebook comment normalized for the public code archive.
    )

    # Original notebook comment normalized for the public code archive.
    print("[INFO] Notebook progress message.")
    plot_amount_scatter_allT(
        df_panel,
        dep_var="edu_amount",
        dep_label="教育培训支出（元）",
        sample="urban",
        partial=True,
    )

    # Original notebook comment normalized for the public code archive.
    # plot_amount_scatter_allT(
    #     df_panel,
    #     dep_var="edu_debt_balance",
    # Original notebook comment normalized for the public code archive.
    #     sample="rural",
    #     partial=True,
    # )


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 19
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf

# =============================================================================

PANEL_PARQUET = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/statistics/"
    "CHFS_mechanism_windows_1to5/CHFS_panel_with_flood_BM_1to5y.parquet"
)

# Original notebook comment normalized for the public code archive.
T_LIST = [2, 5, 10, 20, 50, 100]
K_WINDOW = 1   # Original notebook comment normalized for the public code archive.

# Original notebook comment normalized for the public code archive.
CONTROL_FML_RHS = "log_income + log_childnum + C(is_rural) + C(wave)"


# =============================================================================

def stars_for_p(p: float) -> str:
    """Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    try:
        p = float(p)
    except (TypeError, ValueError):
        return ""
    if p < 0.01:
        return "***"
    elif p < 0.05:
        return "**"
    elif p < 0.10:
        return "*"
    else:
        return ""


# =============================================================================

def add_amount_vars(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()

    # Original notebook comment normalized for the public code archive.
    if "edu_amount" not in df.columns:
        if "去年教育培训支出（元）" in df.columns:
            df["edu_amount"] = pd.to_numeric(
                df["去年教育培训支出（元）"], errors="coerce"
            ).fillna(0)
        elif "edu_train_total" in df.columns:
            df["edu_amount"] = pd.to_numeric(
                df["edu_train_total"], errors="coerce"
            ).fillna(0)
        else:
            raise KeyError(
                "找不到『去年教育培训支出（元）』或 'edu_train_total'，无法生成 edu_amount。"
            )

    # Original notebook comment normalized for the public code archive.
    if "edu_debt_balance" not in df.columns:
        if "教育负债余额（元）" in df.columns:
            df["edu_debt_balance"] = pd.to_numeric(
                df["教育负债余额（元）"], errors="coerce"
            ).fillna(0)
        else:
            # Original notebook comment normalized for the public code archive.
            df["edu_debt_balance"] = np.nan

    return df


# =============================================================================

def filter_sample(df: pd.DataFrame, sample: str) -> pd.DataFrame:
    """Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()

    if "has_child_u15" in df.columns:
        df = df[df["has_child_u15"] == 1]

    if sample == "rural":
        df = df[df["is_rural"] == 1]
    elif sample == "urban":
        df = df[df["is_rural"] == 0]

    return df


def partial_residuals(df: pd.DataFrame,
                      dep_var: str,
                      exp_var: str) -> tuple[np.ndarray, np.ndarray]:
    """Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()

    cols_for_reg = [
        dep_var, exp_var,
        "log_income", "log_childnum", "is_rural", "wave"
    ]
    for c in cols_for_reg:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")

    df = df.dropna(subset=[
        dep_var, exp_var,
        "log_income", "log_childnum", "is_rural", "wave"
    ])
    if df.empty:
        return np.array([]), np.array([])

    # dep_var ~ controls
    fml_y = f"{dep_var} ~ {CONTROL_FML_RHS}"
    # exp_var ~ controls
    fml_x = f"{exp_var} ~ {CONTROL_FML_RHS}"

    res_y = smf.ols(fml_y, data=df).fit()
    res_x = smf.ols(fml_x, data=df).fit()

    y_res = res_y.resid.to_numpy(float)
    x_res = res_x.resid.to_numpy(float)
    return x_res, y_res


# =============================================================================

def get_line_for_T(df: pd.DataFrame,
                   dep_var: str,
                   exp_var: str) -> tuple[np.ndarray, np.ndarray, float] | tuple[None, None, float]:
    """Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()

    # Original notebook comment normalized for the public code archive.
    cols_for_reg = [
        dep_var, exp_var,
        "log_income", "log_childnum", "is_rural", "wave"
    ]
    for c in cols_for_reg:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")

    df = df.dropna(subset=cols_for_reg)
    if df.shape[0] < 200:
        print("[INFO] Notebook progress message.")
        return None, None, np.nan

    # Original notebook comment normalized for the public code archive.
    fml = f"{dep_var} ~ {exp_var} + {CONTROL_FML_RHS}"
    try:
        fit = smf.ols(fml, data=df).fit()
    except Exception as e:
        print("[INFO] Notebook progress message.")
        return None, None, np.nan

    if exp_var not in fit.params.index:
        print("[INFO] Notebook progress message.")
        return None, None, np.nan

    beta = float(fit.params[exp_var])
    pval = float(fit.pvalues.get(exp_var, np.nan))

    # Original notebook comment normalized for the public code archive.
    x_res, y_res = partial_residuals(df, dep_var=dep_var, exp_var=exp_var)
    if x_res.size == 0:
        print("[INFO] Notebook progress message.")
        return None, None, pval

    # Original notebook comment normalized for the public code archive.
    x_min = np.quantile(x_res, 0.05)
    x_max = np.quantile(x_res, 0.95)
    if not np.isfinite(x_min) or not np.isfinite(x_max) or x_min == x_max:
        print("[INFO] Notebook progress message.")
        return None, None, pval

    x_grid = np.linspace(x_min, x_max, 50)
    # Original notebook comment normalized for the public code archive.
    y_grid = beta * x_grid

    return x_grid, y_grid, pval


# =============================================================================

def plot_amount_lines_allT(df_all: pd.DataFrame,
                           dep_var: str = "edu_amount",
                           dep_label: str = "教育金额（元）",
                           sample: str = "rural"):
    """Archived notebook note for 01_household_education_investment_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = filter_sample(df_all, sample)

    # Original notebook comment normalized for the public code archive.
    for c in ["log_income", "log_childnum", "is_rural", "wave"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")

    colors = plt.cm.tab10(np.linspace(0, 1, len(T_LIST)))

    fig, ax = plt.subplots(figsize=(7, 5))

    x_all = []
    y_all = []
    any_line = False

    for idx, T in enumerate(T_LIST):
        exp_var = f"share_flood_ge_T{int(T)}_{K_WINDOW}y"
        if exp_var not in df.columns:
            print("[INFO] Notebook progress message.")
            continue

        x_grid, y_grid, pval = get_line_for_T(df, dep_var=dep_var, exp_var=exp_var)
        if x_grid is None:
            continue

        # Original notebook comment normalized for the public code archive.
        star = stars_for_p(pval)
        if pval < 0.05:
            linestyle = "-"
            alpha = 1.0
        elif pval < 0.10:
            linestyle = "--"
            alpha = 0.9
        else:
            linestyle = ":"
            alpha = 0.6

        label = f"T = {int(T)} 年{(' ' + star) if star else ''}"

        ax.plot(
            x_grid,
            y_grid,
            color=colors[idx],
            linewidth=2,
            linestyle=linestyle,
            alpha=alpha,
            label=label,
        )

        x_all.append(x_grid)
        y_all.append(y_grid)
        any_line = True

        print(f"[INFO] sample={sample}, dep={dep_var}, T={T}: "
              f"beta={y_grid[-1]/x_grid[-1]:.3f}, p={pval:.4f}, stars='{star}'")

    if not any_line:
        print("[INFO] Notebook progress message.")
        return

    x_all = np.concatenate(x_all)
    y_all = np.concatenate(y_all)

    # Original notebook comment normalized for the public code archive.
    x_min, x_max = np.nanmin(x_all), np.nanmax(x_all)
    y_min, y_max = np.nanmin(y_all), np.nanmax(y_all)

    if not np.isfinite(x_min) or not np.isfinite(x_max) or x_min == x_max:
        x_min, x_max = -0.1, 0.1
    if not np.isfinite(y_min) or not np.isfinite(y_max) or y_min == y_max:
        y_min, y_max = -1.0, 1.0

    x_pad = 0.05 * (x_max - x_min if x_max > x_min else 0.1)
    y_pad = 0.08 * (y_max - y_min if y_max > y_min else 0.2)

    ax.axhline(0, color="grey", linestyle="--", linewidth=1)
    ax.axvline(0, color="grey", linestyle="--", linewidth=1)

    ax.set_xlim(x_min - x_pad, x_max + x_pad)
    ax.set_ylim(y_min - y_pad, y_max + y_pad)

    ax.set_xlabel("share_flood_ge_T_1y（控制后残差）")
    ax.set_ylabel(f"{dep_label}（控制后残差）")
    ax.set_title(
        f"{dep_label} × 洪水暴露：多返回期 T 回归线\n"
        f"sample = {sample}（已控制收入、儿童数、城乡、波次；线型反映显著性）"
    )
    ax.legend(fontsize=9)
    plt.tight_layout()
    plt.show()


# =============================================================================

def main():
    print("[INFO] Notebook progress message.")
    df_panel = pd.read_parquet(PANEL_PARQUET)

    # Original notebook comment normalized for the public code archive.
    df_panel = add_amount_vars(df_panel)

    # Original notebook comment normalized for the public code archive.
    print("[INFO] Notebook progress message.")
    plot_amount_lines_allT(
        df_panel,
        dep_var="edu_amount",
        dep_label="教育培训支出（元）",
        sample="rural",
    )

    # Original notebook comment normalized for the public code archive.
    print("[INFO] Notebook progress message.")
    plot_amount_lines_allT(
        df_panel,
        dep_var="edu_amount",
        dep_label="教育培训支出（元）",
        sample="urban",
    )

    # Original notebook comment normalized for the public code archive.
    # plot_amount_lines_allT(
    #     df_panel,
    #     dep_var="edu_debt_balance",
    # Original notebook comment normalized for the public code archive.
    #     sample="rural",
    # )


if __name__ == "__main__":
    main()
