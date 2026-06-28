#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 02_multi_return_period_exposure_count_regressions.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 4
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Distributed-lag (age 0..15) flood exposure regressions with RESUME,
ONLY rural/urban, memory-friendly.

For each (T, sample):
  - build 16 age-specific exposure cols on the fly
  - run FE regression
  - append results to a master CSV
  - save a plot
  - mark done in done.txt

This avoids holding 6*16=96 exposure columns in memory at once.

Author: you + ChatGPT
"""

from pathlib import Path
import warnings
import re

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pyfixest.estimation import feols

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)

# ================================
# 0. CONFIG
# ================================

FLOOD_CSV = Path(
    "/home/ll/jupyter_notebook/result/county_storage_return_events/"
    "county_flood_events_T10_20_50_100_1980_2015.csv"
)

EDU_PARQUET = Path(
    "/home/ll/jupyter_notebook/gis_data/census/edu_micro_2015.parquet"
)

OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "statistics/distributed_lag_age015_storage_BM_resume"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

DONE_TXT = OUT_DIR / "done.txt"
MASTER_CSV = OUT_DIR / "dl_age015_byT_rural_urban_results.csv"

# Original notebook comment normalized for the public code archive.
AGE0, AGE1 = 0, 15

# Original notebook comment normalized for the public code archive.
BIRTH_MIN, BIRTH_MAX = 1980, 2000
AGE_2015_MIN, AGE_2015_MAX = 15, 35
ONLY_NON_MIGRANT = True

# Original notebook comment normalized for the public code archive.
SAMPLES = ["rural", "urban"]

# Original notebook comment normalized for the public code archive.
T_LIST = [2, 5, 10, 20, 50, 100]
REQUIRE_ALL_T = True  # Original notebook comment normalized for the public code archive.

# Original notebook comment normalized for the public code archive.
CONTROL_FML = "C(M34) + C(M37) + C(M15) + C(M16)"

# Original notebook comment normalized for the public code archive.
SIG_LEVEL = 0.10


# ================================
# 1. HELPERS
# ================================

def read_done_set(path: Path) -> set:
    if not path.exists():
        return set()
    s = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            s.add(line)
    return s

def mark_done(path: Path, key: str):
    with path.open("a", encoding="utf-8") as f:
        f.write(key + "\n")

def normalize_tidy(res: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 02_multi_return_period_exposure_count_regressions.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    res = res.reset_index()
    if res.columns[0] != "Term":
        res = res.rename(columns={res.columns[0]: "Term"})
    rename_map = {}
    for c in res.columns:
        lc = c.lower().replace(" ", "").replace(".", "")
        if lc in ["stderr", "stderror", "std_error", "std"]:
            rename_map[c] = "StdError"
        if lc in ["pvalue", "p>|t|", "pr(>|t|)", "p"]:
            rename_map[c] = "PValue"
        if lc in ["estimate", "coef", "coefficient"]:
            rename_map[c] = "Estimate"
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

def stars_for_p(p: float) -> str:
    try:
        p = float(p)
    except Exception:
        return ""
    if p < 0.001:
        return "****"
    elif p < 0.05:
        return "**"
    elif p < 0.10:
        return "*"
    else:
        return ""

def build_is_urban_is_migrant(df: pd.DataFrame) -> pd.DataFrame:
    # Original notebook comment normalized for the public code archive.
    if "is_urban" not in df.columns and "M2" in df.columns:
        suffix = df["M2"] % 100
        df["is_urban"] = np.where((suffix >= 1) & (suffix <= 20), 1, 0)
    # Original notebook comment normalized for the public code archive.
    if "is_migrant" not in df.columns and "M38" in df.columns:
        df["is_migrant"] = np.where(df["M38"] == 1, 0, 1)
    return df

def safe_append_csv(df: pd.DataFrame, path: Path):
    if df.empty:
        return
    if not path.exists():
        df.to_csv(path, index=False, encoding="utf-8-sig")
    else:
        df.to_csv(path, index=False, header=False, mode="a", encoding="utf-8-sig")

def load_flood_index():
    df = pd.read_csv(FLOOD_CSV)

    if "county_code" in df.columns:
        county_col = "county_code"
    elif "county_id" in df.columns:
        county_col = "county_id"
    else:
        raise ValueError("洪水文件中找不到 county_code 或 county_id")

    df[county_col] = pd.to_numeric(df[county_col], errors="coerce").astype("Int64")
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    needed = [f"flood_ge_T{t}" for t in T_LIST]
    missing = [c for c in needed if c not in df.columns]

    if missing and REQUIRE_ALL_T:
        raise ValueError(
            "洪水事件面板缺少以下列（建议先生成/补齐，别补0）：\n"
            + "\n".join(missing)
            + f"\n当前文件: {FLOOD_CSV}"
        )

    keep = [county_col, "year"] + [c for c in needed if c in df.columns]
    df = df[keep].dropna(subset=[county_col, "year"])

    for c in keep:
        if c.startswith("flood_ge_T"):
            df[c] = df[c].fillna(0).astype(np.int8)

    if county_col != "county_code":
        df = df.rename(columns={county_col: "county_code"})
    df["county_code"] = df["county_code"].astype("Int64")

    df = df.set_index(["county_code", "year"]).sort_index()

    have_cols = [c for c in needed if c in df.columns]
    print(f"[INFO] Flood panel indexed: shape={df.shape}, have={have_cols}")
    return df, have_cols

def load_micro_base():
    df = pd.read_parquet(EDU_PARQUET)
    print(f"[INFO] Micro raw shape={df.shape}")

    must = ["M2", "birth_year", "edu_years", "M34", "M37", "M15", "M16", "M38"]
    miss = [c for c in must if c not in df.columns]
    if miss:
        raise ValueError("微观数据缺少必要列: " + ", ".join(miss))

    df["M2"] = pd.to_numeric(df["M2"], errors="coerce").astype("Int64")
    df["birth_year"] = pd.to_numeric(df["birth_year"], errors="coerce").astype("Int64")
    df["edu_years"] = pd.to_numeric(df["edu_years"], errors="coerce")

    df = build_is_urban_is_migrant(df)

    mask = pd.Series(True, index=df.index)
    mask &= df["birth_year"].between(BIRTH_MIN, BIRTH_MAX)

    if "age_2015" in df.columns:
        df["age_2015"] = pd.to_numeric(df["age_2015"], errors="coerce")
        mask &= df["age_2015"].between(AGE_2015_MIN, AGE_2015_MAX)

    if ONLY_NON_MIGRANT:
        mask &= (df["is_migrant"] == 0)

    df = df[mask].copy()

    # Fixed-effects regression helper.
    df["prov_code"] = (df["M2"] // 10000).astype("Int64")
    df["prov_birth_fe"] = df["prov_code"].astype(str) + "_" + df["birth_year"].astype(int).astype(str)
    df["birth_year_c"] = df["birth_year"].astype(int) - 1995

    # controls -> category
    for c in ["M34", "M37", "M15", "M16"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
        df = df.dropna(subset=[c])
        df[c] = df[c].astype(int).astype("category")
        df[c] = df[c].cat.remove_unused_categories()

    df = df.dropna(subset=["M2", "birth_year", "edu_years", "prov_birth_fe", "birth_year_c"])
    print(f"[INFO] Micro base shape={df.shape}")

    # Original notebook comment normalized for the public code archive.
    keep_cols = ["edu_years", "M2", "birth_year", "birth_year_c", "prov_birth_fe",
                 "is_urban", "is_migrant", "M34", "M37", "M15", "M16"]
    if "age_2015" in df.columns:
        keep_cols.append("age_2015")
    df = df[keep_cols].copy()

    return df

def build_age_exposure_matrix(dfm: pd.DataFrame, flood_idx: pd.DataFrame, flood_col: str) -> pd.DataFrame:
    """Archived notebook note for 02_multi_return_period_exposure_count_regressions.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    county = dfm["M2"].astype("Int64").to_numpy()
    byear = dfm["birth_year"].astype(int).to_numpy()

    exp = {}
    s = flood_idx[flood_col]  # Series with MultiIndex

    for a in range(AGE0, AGE1 + 1):
        year = byear + a
        idx = pd.MultiIndex.from_arrays([county, year], names=["county_code", "year"])
        x = s.reindex(idx).fillna(0).to_numpy(dtype=np.int8)
        exp[f"E_a{a:02d}"] = x

    return pd.DataFrame(exp, index=dfm.index)

def run_one(df_base: pd.DataFrame, flood_idx: pd.DataFrame, T: int, sample: str) -> pd.DataFrame:
    """Archived notebook note for 02_multi_return_period_exposure_count_regressions.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    # sample filter
    if sample == "rural":
        dfm = df_base[df_base["is_urban"] == 0].copy()
    elif sample == "urban":
        dfm = df_base[df_base["is_urban"] == 1].copy()
    else:
        raise ValueError("sample must be rural/urban")

    if dfm.empty:
        return pd.DataFrame()

    flood_col = f"flood_ge_T{T}"
    if flood_col not in flood_idx.columns:
        raise ValueError(f"Flood panel missing {flood_col}")

    # Original notebook comment normalized for the public code archive.
    Xexp = build_age_exposure_matrix(dfm, flood_idx, flood_col=flood_col)

    # Original notebook comment normalized for the public code archive.
    dfm = pd.concat([dfm, Xexp], axis=1)

    x_terms = [f"E_a{a:02d}" for a in range(AGE0, AGE1 + 1)]
    dfm = dfm.dropna(subset=["edu_years", "M2", "prov_birth_fe", "birth_year_c"] + x_terms)

    if dfm.empty:
        return pd.DataFrame()

    X = " + ".join(x_terms)
    fml = f"edu_years ~ {X} + {CONTROL_FML} + i(M2, birth_year_c) | M2 + prov_birth_fe"

    fit = feols(fml, data=dfm, vcov={"CRV1": "M2"})
    td = normalize_tidy(fit.tidy())

    out = td[td["Term"].isin(x_terms)].copy()
    if out.empty:
        return pd.DataFrame()

    out["T"] = int(T)
    out["sample"] = sample
    out["age"] = out["Term"].str.extract(r"E_a(\d{2})").astype(int)
    out["Estimate"] = pd.to_numeric(out["Estimate"], errors="coerce")
    out["StdError"] = pd.to_numeric(out.get("StdError", np.nan), errors="coerce")
    out["PValue"] = pd.to_numeric(out.get("PValue", np.nan), errors="coerce")
    out["CI_low"] = out["Estimate"] - 1.96 * out["StdError"]
    out["CI_high"] = out["Estimate"] + 1.96 * out["StdError"]
    out["nobs"] = int(len(dfm))
    out = out.sort_values("age")

    return out

def plot_age_curve(out: pd.DataFrame, save_path: Path):
    if out.empty:
        return

    ages = out["age"].to_numpy()
    est = out["Estimate"].to_numpy(float)
    lo = out["CI_low"].to_numpy(float)
    hi = out["CI_high"].to_numpy(float)
    pv = out["PValue"].to_numpy(float)

    yerr = np.vstack([est - lo, hi - est])

    T = int(out["T"].iloc[0])
    sample = out["sample"].iloc[0]

    fig, ax = plt.subplots(figsize=(8.2, 5.0))
    ax.axhline(0, linestyle="--", linewidth=1)

    ax.errorbar(ages, est, yerr=yerr, fmt="o", capsize=3)

    # Original notebook comment normalized for the public code archive.
    y0, y1 = ax.get_ylim()
    offset = 0.03 * (y1 - y0 if y1 > y0 else 1.0)
    for a, b, p in zip(ages, est, pv):
        s = stars_for_p(p)
        if s:
            ax.text(a, b + offset, s, ha="center", va="bottom", fontsize=10)

    ax.set_xticks(np.arange(AGE0, AGE1 + 1, 1))
    ax.set_xlabel("儿童年龄 a（0–15）")
    ax.set_ylabel("系数：该年龄暴露对 edu_years 的边际影响")
    ax.set_title(f"Distributed-lag 逐岁暴露 | T={T} | sample={sample}")

    plt.tight_layout()
    plt.savefig(save_path, dpi=200)
    plt.close(fig)

# ================================
# 2. MAIN
# ================================

def main():
    done = read_done_set(DONE_TXT)
    print(f"[INFO] done items: {len(done)}")

    flood_idx, have_cols = load_flood_index()

    # Original notebook comment normalized for the public code archive.
    # Original notebook comment normalized for the public code archive.
    # Original notebook comment normalized for the public code archive.
    # make sure all needed cols exist
    need_cols = [f"flood_ge_T{t}" for t in T_LIST]
    miss = [c for c in need_cols if c not in flood_idx.columns]
    if miss and REQUIRE_ALL_T:
        raise ValueError("缺少列: " + ", ".join(miss))

    df_base = load_micro_base()

    for T in T_LIST:
        for sample in SAMPLES:
            key = f"T{T}_{sample}"
            if key in done:
                print(f"[SKIP] {key} already done.")
                continue

            print("\n==============================")
            print(f"[RUN] {key}")
            print("==============================")

            try:
                out = run_one(df_base, flood_idx, T=T, sample=sample)
            except Exception as e:
                # Original notebook comment normalized for the public code archive.
                print(f"[ERROR] {key} failed: {repr(e)}")
                continue

            if out.empty:
                print(f"[WARN] {key} produced empty output (terms dropped or empty sample).")
                # Original notebook comment normalized for the public code archive.
                mark_done(DONE_TXT, key)
                done.add(key)
                continue

            # 1) append results
            safe_append_csv(out, MASTER_CSV)
            print(f"[DONE] appended to master csv: {MASTER_CSV}")

            # 2) plot
            fig_path = OUT_DIR / f"coef_age_curve_T{T}_{sample}.png"
            plot_age_curve(out, fig_path)
            print(f"[DONE] saved plot: {fig_path}")

            # 3) mark done
            mark_done(DONE_TXT, key)
            done.add(key)
            print(f"[DONE] marked done: {key}")

    print("\n[ALL DONE]")

if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 5
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Visualize distributed-lag results (age 0-15) for T={2,5,10,20,50,100} and sample={rural,urban}

Input:
  dl_age015_byT_rural_urban_results.csv  (columns: T, sample, age, Estimate, StdError, PValue, CI_low, CI_high)

Outputs:
  1) heatmap_beta_TxAge_rural.png
  2) heatmap_beta_TxAge_urban.png
  3) overlay_age_curves_rural.png
  4) overlay_age_curves_urban.png
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ======================
# 0. PATHS
# ======================
IN_CSV = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/statistics/"
    "distributed_lag_age015_storage_BM_resume/dl_age015_byT_rural_urban_results.csv"
)

OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/statistics/"
    "distributed_lag_age015_storage_BM_resume/visual"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Original notebook comment normalized for the public code archive.
T_ORDER = [2, 5, 10, 20, 50, 100]
AGE0, AGE1 = 0, 15

# Original notebook comment normalized for the public code archive.
SIG_LEVEL = 0.10


# ======================
# 1. LOAD
# ======================
def load_results(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Original notebook comment normalized for the public code archive.
    df["T"] = pd.to_numeric(df["T"], errors="coerce").astype(int)
    df["age"] = pd.to_numeric(df["age"], errors="coerce").astype(int)
    for c in ["Estimate", "StdError", "PValue", "CI_low", "CI_high"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["T", "age", "sample", "Estimate"])
    # Original notebook comment normalized for the public code archive.
    df = df[df["age"].between(AGE0, AGE1)]
    return df


# ======================
# 2. HEATMAP: T × AGE
# ======================
def plot_heatmap(df: pd.DataFrame, sample: str, save_path: Path):
    sub = df[df["sample"] == sample].copy()
    if sub.empty:
        print(f"[WARN] heatmap: no data for sample={sample}")
        return

    # Original notebook comment normalized for the public code archive.
    mat = (
        sub.pivot_table(index="T", columns="age", values="Estimate", aggfunc="mean")
        .reindex(index=T_ORDER, columns=list(range(AGE0, AGE1 + 1)))
    )

    # Original notebook comment normalized for the public code archive.
    sig = (
        sub.pivot_table(index="T", columns="age", values="PValue", aggfunc="min")
        .reindex(index=T_ORDER, columns=list(range(AGE0, AGE1 + 1)))
    )
    sig_mask = (sig < SIG_LEVEL)

    fig, ax = plt.subplots(figsize=(10.5, 4.8))

    # Original notebook comment normalized for the public code archive.
    data = mat.to_numpy(dtype=float)
    im = ax.imshow(data, aspect="auto")

    # ticks
    ax.set_xticks(np.arange(AGE0, AGE1 + 1))
    ax.set_xticklabels(list(range(AGE0, AGE1 + 1)))
    ax.set_yticks(np.arange(len(T_ORDER)))
    ax.set_yticklabels(T_ORDER)

    ax.set_xlabel("儿童年龄 a（0–15）")
    ax.set_ylabel("洪水返回期阈值 T（年）")
    ax.set_title(f"Distributed-lag：系数热力图（Estimate）| sample={sample}\n(显著性：p < {SIG_LEVEL})")

    # colorbar
    cbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cbar.set_label("Estimate")

    # Original notebook comment normalized for the public code archive.
    for i, T in enumerate(T_ORDER):
        for j, a in enumerate(range(AGE0, AGE1 + 1)):
            try:
                if bool(sig_mask.loc[T, a]) and np.isfinite(data[i, j]):
                    ax.text(j, i, "*", ha="center", va="center", fontsize=10, color="black")
            except Exception:
                pass

    plt.tight_layout()
    plt.savefig(save_path, dpi=220)
    plt.close(fig)
    print(f"[DONE] saved heatmap: {save_path}")


# ======================
# 3. OVERLAY CURVES: by T
# ======================
def plot_overlay_curves(df: pd.DataFrame, sample: str, save_path: Path):
    sub = df[df["sample"] == sample].copy()
    if sub.empty:
        print(f"[WARN] overlay: no data for sample={sample}")
        return

    fig, ax = plt.subplots(figsize=(10.5, 5.0))
    ax.axhline(0, linestyle="--", linewidth=1)

    ages = np.arange(AGE0, AGE1 + 1)

    for T in T_ORDER:
        sT = sub[sub["T"] == T].sort_values("age")
        if sT.empty:
            continue

        # Original notebook comment normalized for the public code archive.
        sT = sT.set_index("age").reindex(ages)

        y = sT["Estimate"].to_numpy(float)
        lo = sT["CI_low"].to_numpy(float) if "CI_low" in sT else np.full_like(y, np.nan)
        hi = sT["CI_high"].to_numpy(float) if "CI_high" in sT else np.full_like(y, np.nan)

        ax.plot(ages, y, marker="o", linewidth=1.4, label=f"T={T}")
        # Original notebook comment normalized for the public code archive.
        if np.all(np.isfinite(lo)) and np.all(np.isfinite(hi)):
            ax.fill_between(ages, lo, hi, alpha=0.12)

    ax.set_xticks(ages)
    ax.set_xlabel("儿童年龄 a（0–15）")
    ax.set_ylabel("系数：该年龄暴露对 edu_years 的边际影响")
    ax.set_title(f"Distributed-lag：不同返回期 T 的年龄效应曲线（含 95% CI）| sample={sample}")

    ax.legend(ncol=3, frameon=True)
    plt.tight_layout()
    plt.savefig(save_path, dpi=220)
    plt.close(fig)
    print(f"[DONE] saved overlay curves: {save_path}")


# ======================
# 4. MAIN
# ======================
def main():
    print(f"[READ] {IN_CSV}")
    df = load_results(IN_CSV)
    print(f"[INFO] loaded shape={df.shape}, samples={df['sample'].unique()}, T={sorted(df['T'].unique())}")

    for sample in ["rural", "urban"]:
        plot_heatmap(df, sample=sample, save_path=OUT_DIR / f"heatmap_beta_TxAge_{sample}.png")
        plot_overlay_curves(df, sample=sample, save_path=OUT_DIR / f"overlay_age_curves_{sample}.png")

    print(f"[DONE] all figures saved to: {OUT_DIR}")

if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 7
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Distributed-lag (age 0..15) regressions with RESUME,
ONLY rural/urban, using "ALL FLOODS" (no return-period split).

ALL_FLOOD definition:
  flood_all = max(flood_ge_T2, flood_ge_T5, ..., flood_ge_T100)
  (you can switch to using only flood_ge_T2 if desired)

Outputs:
  master csv + plots + done.txt under OUT_DIR
"""

from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pyfixest.estimation import feols

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)

# ================================
# 0. CONFIG
# ================================

FLOOD_CSV = Path(
    "/home/ll/jupyter_notebook/result/county_storage_return_events/"
    "county_flood_events_T10_20_50_100_1980_2015.csv"
)
EDU_PARQUET = Path(
    "/home/ll/jupyter_notebook/gis_data/census/edu_micro_2015.parquet"
)

OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "statistics/distributed_lag_age015_ALLFLOOD_storage_BM_resume"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

DONE_TXT = OUT_DIR / "done.txt"
MASTER_CSV = OUT_DIR / "dl_age015_ALLFLOOD_rural_urban_results.csv"

AGE0, AGE1 = 0, 15

BIRTH_MIN, BIRTH_MAX = 1980, 2000
AGE_2015_MIN, AGE_2015_MAX = 15, 35
ONLY_NON_MIGRANT = True

SAMPLES = ["rural", "urban"]

# Original notebook comment normalized for the public code archive.
T_LIST_FOR_ALL = [2, 5, 10, 20, 50, 100]
REQUIRE_ALL_T = True

CONTROL_FML = "C(M34) + C(M37) + C(M15) + C(M16)"
SIG_LEVEL = 0.10


# ================================
# 1. HELPERS
# ================================

def read_done_set(path: Path) -> set:
    if not path.exists():
        return set()
    return set([x.strip() for x in path.read_text(encoding="utf-8").splitlines() if x.strip()])

def mark_done(path: Path, key: str):
    with path.open("a", encoding="utf-8") as f:
        f.write(key + "\n")

def safe_append_csv(df: pd.DataFrame, path: Path):
    if df.empty:
        return
    if not path.exists():
        df.to_csv(path, index=False, encoding="utf-8-sig")
    else:
        df.to_csv(path, index=False, header=False, mode="a", encoding="utf-8-sig")

def normalize_tidy(res: pd.DataFrame) -> pd.DataFrame:
    res = res.reset_index()
    if res.columns[0] != "Term":
        res = res.rename(columns={res.columns[0]: "Term"})
    rename_map = {}
    for c in res.columns:
        lc = c.lower().replace(" ", "").replace(".", "")
        if lc in ["stderr", "stderror", "std_error", "std"]:
            rename_map[c] = "StdError"
        if lc in ["pvalue", "p>|t|", "pr(>|t|)", "p"]:
            rename_map[c] = "PValue"
        if lc in ["estimate", "coef", "coefficient"]:
            rename_map[c] = "Estimate"
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

def stars_for_p(p: float) -> str:
    try:
        p = float(p)
    except Exception:
        return ""
    if p < 0.001: return "****"
    if p < 0.05:  return "**"
    if p < 0.10:  return "*"
    return ""

def build_is_urban_is_migrant(df: pd.DataFrame) -> pd.DataFrame:
    if "is_urban" not in df.columns and "M2" in df.columns:
        suffix = df["M2"] % 100
        df["is_urban"] = np.where((suffix >= 1) & (suffix <= 20), 1, 0)
    if "is_migrant" not in df.columns and "M38" in df.columns:
        df["is_migrant"] = np.where(df["M38"] == 1, 0, 1)
    return df


# ================================
# 2. LOAD FLOOD -> build flood_all
# ================================

def load_flood_index_all():
    df = pd.read_csv(FLOOD_CSV)

    if "county_code" in df.columns:
        county_col = "county_code"
    elif "county_id" in df.columns:
        county_col = "county_id"
    else:
        raise ValueError("洪水文件中找不到 county_code 或 county_id")

    df[county_col] = pd.to_numeric(df[county_col], errors="coerce").astype("Int64")
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    needed = [f"flood_ge_T{t}" for t in T_LIST_FOR_ALL]
    missing = [c for c in needed if c not in df.columns]
    if missing and REQUIRE_ALL_T:
        raise ValueError("洪水面板缺少列（无法合成 ALL_FLOOD）:\n" + "\n".join(missing))

    keep = [county_col, "year"] + [c for c in needed if c in df.columns]
    df = df[keep].dropna(subset=[county_col, "year"])

    for c in needed:
        if c in df.columns:
            df[c] = df[c].fillna(0).astype(np.int8)

    # =============================================================================
    have = [c for c in needed if c in df.columns]
    df["flood_all"] = df[have].max(axis=1).astype(np.int8)

    # Original notebook comment normalized for the public code archive.
    # df["flood_all"] = df["flood_ge_T2"].astype(np.int8)

    if county_col != "county_code":
        df = df.rename(columns={county_col: "county_code"})
    df["county_code"] = df["county_code"].astype("Int64")

    flood_idx = df.set_index(["county_code", "year"]).sort_index()[["flood_all"]]
    print(f"[INFO] Flood indexed: shape={flood_idx.shape}, col=flood_all")
    return flood_idx


# ================================
# 3. LOAD MICRO BASE (memory saving)
# ================================

def load_micro_base():
    df = pd.read_parquet(EDU_PARQUET)
    print(f"[INFO] Micro raw shape={df.shape}")

    must = ["M2", "birth_year", "edu_years", "M34", "M37", "M15", "M16", "M38"]
    miss = [c for c in must if c not in df.columns]
    if miss:
        raise ValueError("微观数据缺少必要列: " + ", ".join(miss))

    df["M2"] = pd.to_numeric(df["M2"], errors="coerce").astype("Int64")
    df["birth_year"] = pd.to_numeric(df["birth_year"], errors="coerce").astype("Int64")
    df["edu_years"] = pd.to_numeric(df["edu_years"], errors="coerce")

    df = build_is_urban_is_migrant(df)

    m = pd.Series(True, index=df.index)
    m &= df["birth_year"].between(BIRTH_MIN, BIRTH_MAX)

    if "age_2015" in df.columns:
        df["age_2015"] = pd.to_numeric(df["age_2015"], errors="coerce")
        m &= df["age_2015"].between(AGE_2015_MIN, AGE_2015_MAX)

    if ONLY_NON_MIGRANT:
        m &= (df["is_migrant"] == 0)

    df = df[m].copy()

    df["prov_code"] = (df["M2"] // 10000).astype("Int64")
    df["prov_birth_fe"] = df["prov_code"].astype(str) + "_" + df["birth_year"].astype(int).astype(str)
    df["birth_year_c"] = df["birth_year"].astype(int) - 1995

    for c in ["M34", "M37", "M15", "M16"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
        df = df.dropna(subset=[c])
        df[c] = df[c].astype(int).astype("category")
        df[c] = df[c].cat.remove_unused_categories()

    df = df.dropna(subset=["M2", "birth_year", "edu_years", "prov_birth_fe", "birth_year_c"])
    print(f"[INFO] Micro base shape={df.shape}")

    keep = ["edu_years", "M2", "birth_year", "birth_year_c", "prov_birth_fe",
            "is_urban", "is_migrant", "M34", "M37", "M15", "M16"]
    if "age_2015" in df.columns:
        keep.append("age_2015")
    return df[keep].copy()


# ================================
# 4. BUILD age exposures for flood_all
# ================================

def build_age_exposure_matrix(dfm: pd.DataFrame, flood_idx: pd.DataFrame) -> pd.DataFrame:
    county = dfm["M2"].astype("Int64").to_numpy()
    byear = dfm["birth_year"].astype(int).to_numpy()

    s = flood_idx["flood_all"]  # Series indexed by (county_code, year)
    exp = {}
    for a in range(AGE0, AGE1 + 1):
        year = byear + a
        idx = pd.MultiIndex.from_arrays([county, year], names=["county_code", "year"])
        exp[f"E_a{a:02d}"] = s.reindex(idx).fillna(0).to_numpy(dtype=np.int8)

    return pd.DataFrame(exp, index=dfm.index)


def run_one(df_base: pd.DataFrame, flood_idx: pd.DataFrame, sample: str) -> pd.DataFrame:
    if sample == "rural":
        dfm = df_base[df_base["is_urban"] == 0].copy()
    elif sample == "urban":
        dfm = df_base[df_base["is_urban"] == 1].copy()
    else:
        raise ValueError("sample must be rural/urban")

    if dfm.empty:
        return pd.DataFrame()

    Xexp = build_age_exposure_matrix(dfm, flood_idx)
    dfm = pd.concat([dfm, Xexp], axis=1)

    x_terms = [f"E_a{a:02d}" for a in range(AGE0, AGE1 + 1)]
    dfm = dfm.dropna(subset=["edu_years", "M2", "prov_birth_fe", "birth_year_c"] + x_terms)
    if dfm.empty:
        return pd.DataFrame()

    X = " + ".join(x_terms)
    fml = f"edu_years ~ {X} + {CONTROL_FML} + i(M2, birth_year_c) | M2 + prov_birth_fe"

    fit = feols(fml, data=dfm, vcov={"CRV1": "M2"})
    td = normalize_tidy(fit.tidy())

    out = td[td["Term"].isin(x_terms)].copy()
    if out.empty:
        return pd.DataFrame()

    out["flood_def"] = "all_flood"     # Original notebook comment normalized for the public code archive.
    out["sample"] = sample
    out["age"] = out["Term"].str.extract(r"E_a(\d{2})").astype(int)

    out["Estimate"] = pd.to_numeric(out["Estimate"], errors="coerce")
    out["StdError"] = pd.to_numeric(out.get("StdError", np.nan), errors="coerce")
    out["PValue"] = pd.to_numeric(out.get("PValue", np.nan), errors="coerce")
    out["CI_low"] = out["Estimate"] - 1.96 * out["StdError"]
    out["CI_high"] = out["Estimate"] + 1.96 * out["StdError"]
    out["nobs"] = int(len(dfm))

    return out.sort_values("age")


def plot_age_curve(out: pd.DataFrame, save_path: Path):
    if out.empty:
        return
    ages = out["age"].to_numpy(int)
    est = out["Estimate"].to_numpy(float)
    lo = out["CI_low"].to_numpy(float)
    hi = out["CI_high"].to_numpy(float)
    pv = out["PValue"].to_numpy(float)

    yerr = np.vstack([est - lo, hi - est])

    sample = out["sample"].iloc[0]

    fig, ax = plt.subplots(figsize=(8.2, 5.0))
    ax.axhline(0, linestyle="--", linewidth=1)
    ax.errorbar(ages, est, yerr=yerr, fmt="o", capsize=3)

    y0, y1 = ax.get_ylim()
    offset = 0.03 * (y1 - y0 if y1 > y0 else 1.0)
    for a, b, p in zip(ages, est, pv):
        s = stars_for_p(p)
        if s:
            ax.text(a, b + offset, s, ha="center", va="bottom", fontsize=10)

    ax.set_xticks(np.arange(AGE0, AGE1 + 1, 1))
    ax.set_xlabel("儿童年龄 a（0–15）")
    ax.set_ylabel("系数：该年龄暴露对 edu_years 的边际影响")
    ax.set_title(f"Distributed-lag 逐岁暴露 | ALL FLOODS | sample={sample}")

    plt.tight_layout()
    plt.savefig(save_path, dpi=200)
    plt.close(fig)


# ================================
# 5. MAIN (resume)
# ================================

def main():
    done = read_done_set(DONE_TXT)
    print(f"[INFO] done items: {len(done)}")

    flood_idx = load_flood_index_all()
    df_base = load_micro_base()

    for sample in SAMPLES:
        key = f"ALLFLOOD_{sample}"
        if key in done:
            print(f"[SKIP] {key} already done.")
            continue

        print("\n==============================")
        print(f"[RUN] {key}")
        print("==============================")

        try:
            out = run_one(df_base, flood_idx, sample=sample)
        except Exception as e:
            print(f"[ERROR] {key} failed: {repr(e)}")
            continue

        if out.empty:
            print(f"[WARN] {key} empty output.")
            mark_done(DONE_TXT, key)
            done.add(key)
            continue

        safe_append_csv(out, MASTER_CSV)
        print(f"[DONE] appended to: {MASTER_CSV}")

        fig_path = OUT_DIR / f"coef_age_curve_ALLFLOOD_{sample}.png"
        plot_age_curve(out, fig_path)
        print(f"[DONE] saved plot: {fig_path}")

        mark_done(DONE_TXT, key)
        done.add(key)
        print(f"[DONE] marked done: {key}")

    print("\n[ALL DONE]")

if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 13
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 02_multi_return_period_exposure_count_regressions.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pyfixest.estimation import feols

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)

# =========================================================
# 0. CONFIG
# =========================================================

# --- choose method: "bin" / "almon2" / "spline"
METHOD = "bin"

# B1: age bins (inclusive)
# Original notebook comment normalized for the public code archive.
AGE_BINS = [(0, 3), (4, 6), (7, 9), (10, 12), (13, 15)]  # Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.

# Original notebook comment normalized for the public code archive.
ALMON_DEGREE = 2

# B3: spline knots (age)
SPLINE_KNOTS = [4, 8, 12]  # Original notebook comment normalized for the public code archive.

# --- data paths
FLOOD_CSV = Path(
    "/home/ll/jupyter_notebook/result/county_storage_return_events/"
    "county_flood_events_T10_20_50_100_1980_2015.csv"
)
EDU_PARQUET = Path(
    "/home/ll/jupyter_notebook/gis_data/census/edu_micro_2015.parquet"
)

OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/statistics/"
    f"planB_{METHOD}_age015_storage_BM_resume"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

DONE_TXT = OUT_DIR / "done.txt"
MASTER_CSV = OUT_DIR / "planB_results.csv"

# --- sample restrictions
AGE0, AGE1 = 0, 15
BIRTH_MIN, BIRTH_MAX = 1980, 2000
AGE_2015_MIN, AGE_2015_MAX = 15, 35
ONLY_NON_MIGRANT = True

SAMPLES = ["rural", "urban"]
T_LIST = [2, 5, 10, 20, 50, 100]
REQUIRE_ALL_T = True

CONTROL_FML = "C(M34) + C(M37) + C(M15) + C(M16)"
SIG_LEVEL = 0.10


# =========================================================
# 1. Small helpers
# =========================================================

def read_done_set(path: Path) -> set:
    if not path.exists():
        return set()
    return set([x.strip() for x in path.read_text(encoding="utf-8").splitlines() if x.strip()])

def mark_done(path: Path, key: str):
    with path.open("a", encoding="utf-8") as f:
        f.write(key + "\n")

def safe_append_csv(df: pd.DataFrame, path: Path):
    if df.empty:
        return
    if not path.exists():
        df.to_csv(path, index=False, encoding="utf-8-sig")
    else:
        df.to_csv(path, index=False, header=False, mode="a", encoding="utf-8-sig")

def normalize_tidy(res: pd.DataFrame) -> pd.DataFrame:
    res = res.reset_index()
    if res.columns[0] != "Term":
        res = res.rename(columns={res.columns[0]: "Term"})
    rename_map = {}
    for c in res.columns:
        lc = c.lower().replace(" ", "").replace(".", "")
        if lc in ["stderr", "stderror", "std_error", "std"]:
            rename_map[c] = "StdError"
        if lc in ["pvalue", "p>|t|", "pr(>|t|)", "p"]:
            rename_map[c] = "PValue"
        if lc in ["estimate", "coef", "coefficient"]:
            rename_map[c] = "Estimate"
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

def stars_for_p(p: float) -> str:
    try:
        p = float(p)
    except Exception:
        return ""
    if p < 0.001: return "****"
    if p < 0.05:  return "**"
    if p < 0.10:  return "*"
    return ""

def build_is_urban_is_migrant(df: pd.DataFrame) -> pd.DataFrame:
    if "is_urban" not in df.columns and "M2" in df.columns:
        suffix = df["M2"] % 100
        df["is_urban"] = np.where((suffix >= 1) & (suffix <= 20), 1, 0)
    if "is_migrant" not in df.columns and "M38" in df.columns:
        df["is_migrant"] = np.where(df["M38"] == 1, 0, 1)
    return df


# =========================================================
# 2. Load flood panel -> MultiIndex
# =========================================================

def load_flood_index():
    df = pd.read_csv(FLOOD_CSV)
    if "county_code" in df.columns:
        county_col = "county_code"
    elif "county_id" in df.columns:
        county_col = "county_id"
    else:
        raise ValueError("洪水文件中找不到 county_code 或 county_id")

    df[county_col] = pd.to_numeric(df[county_col], errors="coerce").astype("Int64")
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    need = [f"flood_ge_T{t}" for t in T_LIST]
    miss = [c for c in need if c not in df.columns]
    if miss and REQUIRE_ALL_T:
        raise ValueError("洪水面板缺少列: " + ", ".join(miss))

    keep = [county_col, "year"] + [c for c in need if c in df.columns]
    df = df[keep].dropna(subset=[county_col, "year"])
    for c in keep:
        if c.startswith("flood_ge_T"):
            df[c] = df[c].fillna(0).astype(np.int8)

    if county_col != "county_code":
        df = df.rename(columns={county_col: "county_code"})
    df["county_code"] = df["county_code"].astype("Int64")

    df = df.set_index(["county_code", "year"]).sort_index()
    print(f"[INFO] Flood indexed: shape={df.shape}, cols={[c for c in df.columns if c.startswith('flood_ge_T')]}")
    return df


# =========================================================
# 3. Load micro base (memory-saving)
# =========================================================

def load_micro_base():
    df = pd.read_parquet(EDU_PARQUET)
    print(f"[INFO] Micro raw shape={df.shape}")

    must = ["M2", "birth_year", "edu_years", "M34", "M37", "M15", "M16", "M38"]
    miss = [c for c in must if c not in df.columns]
    if miss:
        raise ValueError("微观数据缺少列: " + ", ".join(miss))

    df["M2"] = pd.to_numeric(df["M2"], errors="coerce").astype("Int64")
    df["birth_year"] = pd.to_numeric(df["birth_year"], errors="coerce").astype("Int64")
    df["edu_years"] = pd.to_numeric(df["edu_years"], errors="coerce")

    df = build_is_urban_is_migrant(df)

    m = pd.Series(True, index=df.index)
    m &= df["birth_year"].between(BIRTH_MIN, BIRTH_MAX)
    if "age_2015" in df.columns:
        df["age_2015"] = pd.to_numeric(df["age_2015"], errors="coerce")
        m &= df["age_2015"].between(AGE_2015_MIN, AGE_2015_MAX)
    if ONLY_NON_MIGRANT:
        m &= (df["is_migrant"] == 0)

    df = df[m].copy()

    df["prov_code"] = (df["M2"] // 10000).astype("Int64")
    df["prov_birth_fe"] = df["prov_code"].astype(str) + "_" + df["birth_year"].astype(int).astype(str)
    df["birth_year_c"] = df["birth_year"].astype(int) - 1995

    for c in ["M34", "M37", "M15", "M16"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
        df = df.dropna(subset=[c])
        df[c] = df[c].astype(int).astype("category")
        df[c] = df[c].cat.remove_unused_categories()

    df = df.dropna(subset=["M2", "birth_year", "edu_years", "prov_birth_fe", "birth_year_c"])
    print(f"[INFO] Micro base shape={df.shape}")

    keep = ["edu_years", "M2", "birth_year", "birth_year_c", "prov_birth_fe",
            "is_urban", "is_migrant", "M34", "M37", "M15", "M16"]
    if "age_2015" in df.columns:
        keep.append("age_2015")
    return df[keep].copy()


# =========================================================
# 4. Build age exposures E_a00..E_a15 on the fly
# =========================================================

def build_E_age(dfm: pd.DataFrame, flood_idx: pd.DataFrame, flood_col: str) -> pd.DataFrame:
    county = dfm["M2"].astype("Int64").to_numpy()
    byear = dfm["birth_year"].astype(int).to_numpy()
    s = flood_idx[flood_col]  # Series indexed by (county_code, year)

    out = {}
    for a in range(AGE0, AGE1 + 1):
        year = byear + a
        idx = pd.MultiIndex.from_arrays([county, year], names=["county_code", "year"])
        out[f"E_a{a:02d}"] = s.reindex(idx).fillna(0).to_numpy(dtype=np.int8)

    return pd.DataFrame(out, index=dfm.index)


# =========================================================
# 5. Plan B: compress exposures
# =========================================================

def make_regressors(E: pd.DataFrame):
    """
    Return:
      X_df: columns used in regression
      meta: dict for plotting (method-specific)
    """
    ages = np.arange(AGE0, AGE1 + 1)

    if METHOD == "bin":
        cols = []
        X = {}
        for (l, r) in AGE_BINS:
            name = f"X_bin_{l:02d}_{r:02d}"  # sum of exposures in that band
            band_cols = [f"E_a{a:02d}" for a in range(l, r + 1)]
            #X[name] = E[band_cols].sum(axis=1).astype(np.int16)
            X[name] = E[band_cols].mean(axis=1).astype(np.float32)

            cols.append(name)
        X_df = pd.DataFrame(X, index=E.index)
        meta = {"bins": AGE_BINS, "x_cols": cols}

    elif METHOD == "almon2":
        # Z0 = ΣE_a; Z1 = ΣaE_a; Z2 = Σa^2 E_a
        a = ages.astype(float)
        X_df = pd.DataFrame(index=E.index)
        X_df["Z0"] = E.sum(axis=1).astype(np.int16)
        X_df["Z1"] = (E.values * a[None, :]).sum(axis=1)
        X_df["Z2"] = (E.values * (a**2)[None, :]).sum(axis=1)
        meta = {"degree": 2, "ages": ages, "x_cols": ["Z0", "Z1", "Z2"]}

    elif METHOD == "spline":
        # Linear spline basis: beta(a)=g0 + g1*a + Σ_k gk * (a-knot)_+
        a = ages.astype(float)
        X_df = pd.DataFrame(index=E.index)
        X_df["S0"] = E.sum(axis=1).astype(np.int16)
        X_df["S1"] = (E.values * a[None, :]).sum(axis=1)
        x_cols = ["S0", "S1"]
        for k in SPLINE_KNOTS:
            h = np.maximum(a - float(k), 0.0)
            name = f"H{k}"
            X_df[name] = (E.values * h[None, :]).sum(axis=1)
            x_cols.append(name)
        meta = {"knots": SPLINE_KNOTS, "ages": ages, "x_cols": x_cols}

    else:
        raise ValueError("METHOD must be bin/almon2/spline")

    return X_df, meta


# =========================================================
# 6. Regression
# =========================================================

def run_one(df_base: pd.DataFrame, flood_idx: pd.DataFrame, T: int, sample: str) -> pd.DataFrame:
    if sample == "rural":
        dfm = df_base[df_base["is_urban"] == 0].copy()
    elif sample == "urban":
        dfm = df_base[df_base["is_urban"] == 1].copy()
    else:
        raise ValueError("sample must be rural/urban")

    if dfm.empty:
        return pd.DataFrame()

    flood_col = f"flood_ge_T{T}"
    if flood_col not in flood_idx.columns:
        raise ValueError(f"Flood panel missing {flood_col}")

    # build E and compressed X
    E = build_E_age(dfm, flood_idx, flood_col=flood_col)
    X_df, meta = make_regressors(E)

    dfm = pd.concat([dfm, X_df], axis=1)

    x_cols = meta["x_cols"]
    dfm = dfm.dropna(subset=["edu_years", "M2", "prov_birth_fe", "birth_year_c"] + x_cols)
    if dfm.empty:
        return pd.DataFrame()

    X = " + ".join(x_cols)
    fml = f"edu_years ~ {X} + {CONTROL_FML} + i(M2, birth_year_c) | M2 + prov_birth_fe"

    fit = feols(fml, data=dfm, vcov={"CRV1": "M2"})
    td = normalize_tidy(fit.tidy())

    out = td[td["Term"].isin(x_cols)].copy()
    if out.empty:
        return pd.DataFrame()

    out["T"] = int(T)
    out["sample"] = sample
    out["method"] = METHOD
    out["nobs"] = int(len(dfm))
    out["Estimate"] = pd.to_numeric(out["Estimate"], errors="coerce")
    out["StdError"] = pd.to_numeric(out.get("StdError", np.nan), errors="coerce")
    out["PValue"] = pd.to_numeric(out.get("PValue", np.nan), errors="coerce")
    out["CI_low"] = out["Estimate"] - 1.96 * out["StdError"]
    out["CI_high"] = out["Estimate"] + 1.96 * out["StdError"]

    # method-specific labels for plotting
    if METHOD == "bin":
        # map Term -> (l,r)
        bins = meta["bins"]
        term2bin = {f"X_bin_{l:02d}_{r:02d}": (l, r) for (l, r) in bins}
        out["bin_l"] = out["Term"].map(lambda t: term2bin.get(t, (np.nan, np.nan))[0])
        out["bin_r"] = out["Term"].map(lambda t: term2bin.get(t, (np.nan, np.nan))[1])
        out = out.sort_values(["bin_l", "bin_r"])

    else:
        out = out.sort_values("Term")

    return out


# =========================================================
# 7. Visualization (method-specific)
# =========================================================

def plot_bin_effect(out: pd.DataFrame, save_path: Path):
    """Bins: plot segments for each age band with CI"""
    if out.empty:
        return
    sub = out.copy().reset_index(drop=True)
    T = int(sub["T"].iloc[0]); sample = sub["sample"].iloc[0]

    fig, ax = plt.subplots(figsize=(8.8, 4.8))
    ax.axhline(0, linestyle="--", linewidth=1)

    for _, r in sub.iterrows():
        l, rr = int(r["bin_l"]), int(r["bin_r"])
        est, lo, hi, pv = r["Estimate"], r["CI_low"], r["CI_high"], r["PValue"]
        # segment across [l, r]
        ax.plot([l, rr], [est, est], linewidth=2)
        ax.plot([l, rr], [lo, lo], linewidth=1, alpha=0.6)
        ax.plot([l, rr], [hi, hi], linewidth=1, alpha=0.6)
        s = stars_for_p(pv)
        if s:
            ax.text((l+rr)/2, est, s, ha="center", va="bottom", fontsize=11)

    ax.set_xticks(np.arange(AGE0, AGE1 + 1))
    ax.set_xlabel("儿童年龄 a（0–15）")
    ax.set_ylabel("系数：该年龄段暴露（暴露年数求和）对 edu_years 的影响")
    ax.set_title(f"Plan B1 年龄分箱 | T={T} | sample={sample}")
    plt.tight_layout()
    plt.savefig(save_path, dpi=220)
    plt.close(fig)

def plot_param_table(out: pd.DataFrame, save_path: Path):
    """Archived notebook note for 02_multi_return_period_exposure_count_regressions.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if out.empty:
        return
    sub = out.copy().reset_index(drop=True)
    T = int(sub["T"].iloc[0]); sample = sub["sample"].iloc[0]

    xs = np.arange(len(sub))
    fig, ax = plt.subplots(figsize=(8.8, 4.8))
    ax.axhline(0, linestyle="--", linewidth=1)

    y = sub["Estimate"].to_numpy(float)
    lo = sub["CI_low"].to_numpy(float)
    hi = sub["CI_high"].to_numpy(float)
    yerr = np.vstack([y - lo, hi - y])

    ax.errorbar(xs, y, yerr=yerr, fmt="o", capsize=4)
    ax.set_xticks(xs)
    ax.set_xticklabels(sub["Term"].tolist(), rotation=0)
    ax.set_xlabel("约束基函数参数")
    ax.set_ylabel("系数（含 95% CI）")
    ax.set_title(f"Plan B 参数估计 | method={METHOD} | T={T} | sample={sample}")

    for i, pv in enumerate(sub["PValue"].to_numpy(float)):
        s = stars_for_p(pv)
        if s:
            ax.text(i, y[i], s, ha="center", va="bottom", fontsize=11)

    plt.tight_layout()
    plt.savefig(save_path, dpi=220)
    plt.close(fig)


# =========================================================
# 8. MAIN (resume)
# =========================================================

def main():
    done = read_done_set(DONE_TXT)
    print(f"[INFO] done items: {len(done)}")

    flood_idx = load_flood_index()

    need_cols = [f"flood_ge_T{t}" for t in T_LIST]
    miss = [c for c in need_cols if c not in flood_idx.columns]
    if miss and REQUIRE_ALL_T:
        raise ValueError("缺少列: " + ", ".join(miss))

    df_base = load_micro_base()

    for T in T_LIST:
        for sample in SAMPLES:
            key = f"{METHOD}_T{T}_{sample}"
            if key in done:
                print(f"[SKIP] {key} already done.")
                continue

            print("\n==============================")
            print(f"[RUN] {key}")
            print("==============================")

            try:
                out = run_one(df_base, flood_idx, T=T, sample=sample)
            except Exception as e:
                print(f"[ERROR] {key} failed: {repr(e)}")
                continue

            if out.empty:
                print(f"[WARN] {key} empty output (terms dropped or empty sample).")
                mark_done(DONE_TXT, key)
                done.add(key)
                continue

            safe_append_csv(out, MASTER_CSV)
            print(f"[DONE] appended: {MASTER_CSV}")

            # plot
            if METHOD == "bin":
                fig_path = OUT_DIR / f"bin_effect_T{T}_{sample}.png"
                plot_bin_effect(out, fig_path)
            else:
                fig_path = OUT_DIR / f"param_plot_{METHOD}_T{T}_{sample}.png"
                plot_param_table(out, fig_path)

            print(f"[DONE] saved plot: {fig_path}")

            mark_done(DONE_TXT, key)
            done.add(key)
            print(f"[DONE] marked done: {key}")

    print("\n[ALL DONE]")

if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 15
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 02_multi_return_period_exposure_count_regressions.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pyfixest.estimation import feols

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)

# =========================================================
# 0. CONFIG
# =========================================================

# --- choose method: "bin" / "almon2" / "spline"
METHOD = "bin"

# B1: age bins (inclusive)
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
AGE_BINS = [(0,1),(2,3),(4,5),(6,7),(8,9),(10,11),(12,13),(14,15)]
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.

# Original notebook comment normalized for the public code archive.
ALMON_DEGREE = 2

# B3: spline knots (age)
SPLINE_KNOTS = [4, 8, 12]  # Original notebook comment normalized for the public code archive.

# --- data paths
FLOOD_CSV = Path(
    "/home/ll/jupyter_notebook/result/county_storage_return_events/"
    "county_flood_events_T10_20_50_100_1980_2015.csv"
)
EDU_PARQUET = Path(
    "/home/ll/jupyter_notebook/gis_data/census/edu_micro_2015.parquet"
)

OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/statistics/"
    f"planB_{METHOD}_age015_storage_BM_resume"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

DONE_TXT = OUT_DIR / "done.txt"
MASTER_CSV = OUT_DIR / "planB_results.csv"

# --- sample restrictions
AGE0, AGE1 = 0, 15
BIRTH_MIN, BIRTH_MAX = 1980, 2000
AGE_2015_MIN, AGE_2015_MAX = 15, 35
ONLY_NON_MIGRANT = True

SAMPLES = ["rural", "urban"]
T_LIST = [2, 5, 10, 20, 50, 100]
REQUIRE_ALL_T = True

CONTROL_FML = "C(M34) + C(M37) + C(M15) + C(M16)"
SIG_LEVEL = 0.10


# =========================================================
# 1. Small helpers
# =========================================================

def read_done_set(path: Path) -> set:
    if not path.exists():
        return set()
    return set([x.strip() for x in path.read_text(encoding="utf-8").splitlines() if x.strip()])

def mark_done(path: Path, key: str):
    with path.open("a", encoding="utf-8") as f:
        f.write(key + "\n")

def safe_append_csv(df: pd.DataFrame, path: Path):
    if df.empty:
        return
    if not path.exists():
        df.to_csv(path, index=False, encoding="utf-8-sig")
    else:
        df.to_csv(path, index=False, header=False, mode="a", encoding="utf-8-sig")

def normalize_tidy(res: pd.DataFrame) -> pd.DataFrame:
    res = res.reset_index()
    if res.columns[0] != "Term":
        res = res.rename(columns={res.columns[0]: "Term"})
    rename_map = {}
    for c in res.columns:
        lc = c.lower().replace(" ", "").replace(".", "")
        if lc in ["stderr", "stderror", "std_error", "std"]:
            rename_map[c] = "StdError"
        if lc in ["pvalue", "p>|t|", "pr(>|t|)", "p"]:
            rename_map[c] = "PValue"
        if lc in ["estimate", "coef", "coefficient"]:
            rename_map[c] = "Estimate"
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

def stars_for_p(p: float) -> str:
    try:
        p = float(p)
    except Exception:
        return ""
    if p < 0.001: return "****"
    if p < 0.05:  return "**"
    if p < 0.10:  return "*"
    return ""

def build_is_urban_is_migrant(df: pd.DataFrame) -> pd.DataFrame:
    if "is_urban" not in df.columns and "M2" in df.columns:
        suffix = df["M2"] % 100
        df["is_urban"] = np.where((suffix >= 1) & (suffix <= 20), 1, 0)
    if "is_migrant" not in df.columns and "M38" in df.columns:
        df["is_migrant"] = np.where(df["M38"] == 1, 0, 1)
    return df


# =========================================================
# 2. Load flood panel -> MultiIndex
# =========================================================

def load_flood_index():
    df = pd.read_csv(FLOOD_CSV)
    if "county_code" in df.columns:
        county_col = "county_code"
    elif "county_id" in df.columns:
        county_col = "county_id"
    else:
        raise ValueError("洪水文件中找不到 county_code 或 county_id")

    df[county_col] = pd.to_numeric(df[county_col], errors="coerce").astype("Int64")
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    need = [f"flood_ge_T{t}" for t in T_LIST]
    miss = [c for c in need if c not in df.columns]
    if miss and REQUIRE_ALL_T:
        raise ValueError("洪水面板缺少列: " + ", ".join(miss))

    keep = [county_col, "year"] + [c for c in need if c in df.columns]
    df = df[keep].dropna(subset=[county_col, "year"])
    for c in keep:
        if c.startswith("flood_ge_T"):
            df[c] = df[c].fillna(0).astype(np.int8)

    if county_col != "county_code":
        df = df.rename(columns={county_col: "county_code"})
    df["county_code"] = df["county_code"].astype("Int64")

    df = df.set_index(["county_code", "year"]).sort_index()
    print(f"[INFO] Flood indexed: shape={df.shape}, cols={[c for c in df.columns if c.startswith('flood_ge_T')]}")
    return df


# =========================================================
# 3. Load micro base (memory-saving)
# =========================================================

def load_micro_base():
    df = pd.read_parquet(EDU_PARQUET)
    print(f"[INFO] Micro raw shape={df.shape}")

    must = ["M2", "birth_year", "edu_years", "M34", "M37", "M15", "M16", "M38"]
    miss = [c for c in must if c not in df.columns]
    if miss:
        raise ValueError("微观数据缺少列: " + ", ".join(miss))

    df["M2"] = pd.to_numeric(df["M2"], errors="coerce").astype("Int64")
    df["birth_year"] = pd.to_numeric(df["birth_year"], errors="coerce").astype("Int64")
    df["edu_years"] = pd.to_numeric(df["edu_years"], errors="coerce")

    df = build_is_urban_is_migrant(df)

    m = pd.Series(True, index=df.index)
    m &= df["birth_year"].between(BIRTH_MIN, BIRTH_MAX)
    if "age_2015" in df.columns:
        df["age_2015"] = pd.to_numeric(df["age_2015"], errors="coerce")
        m &= df["age_2015"].between(AGE_2015_MIN, AGE_2015_MAX)
    if ONLY_NON_MIGRANT:
        m &= (df["is_migrant"] == 0)

    df = df[m].copy()

    df["prov_code"] = (df["M2"] // 10000).astype("Int64")
    df["prov_birth_fe"] = df["prov_code"].astype(str) + "_" + df["birth_year"].astype(int).astype(str)
    df["birth_year_c"] = df["birth_year"].astype(int) - 1995

    for c in ["M34", "M37", "M15", "M16"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
        df = df.dropna(subset=[c])
        df[c] = df[c].astype(int).astype("category")
        df[c] = df[c].cat.remove_unused_categories()

    df = df.dropna(subset=["M2", "birth_year", "edu_years", "prov_birth_fe", "birth_year_c"])
    print(f"[INFO] Micro base shape={df.shape}")

    keep = ["edu_years", "M2", "birth_year", "birth_year_c", "prov_birth_fe",
            "is_urban", "is_migrant", "M34", "M37", "M15", "M16"]
    if "age_2015" in df.columns:
        keep.append("age_2015")
    return df[keep].copy()


# =========================================================
# 4. Build age exposures E_a00..E_a15 on the fly
# =========================================================

def build_E_age(dfm: pd.DataFrame, flood_idx: pd.DataFrame, flood_col: str) -> pd.DataFrame:
    county = dfm["M2"].astype("Int64").to_numpy()
    byear = dfm["birth_year"].astype(int).to_numpy()
    s = flood_idx[flood_col]  # Series indexed by (county_code, year)

    out = {}
    for a in range(AGE0, AGE1 + 1):
        year = byear + a
        idx = pd.MultiIndex.from_arrays([county, year], names=["county_code", "year"])
        out[f"E_a{a:02d}"] = s.reindex(idx).fillna(0).to_numpy(dtype=np.int8)

    return pd.DataFrame(out, index=dfm.index)


# =========================================================
# 5. Plan B: compress exposures
# =========================================================

def make_regressors(E: pd.DataFrame):
    """
    Return:
      X_df: columns used in regression
      meta: dict for plotting (method-specific)
    """
    ages = np.arange(AGE0, AGE1 + 1)

    if METHOD == "bin":
        cols = []
        X = {}
        for (l, r) in AGE_BINS:
            name = f"X_bin_{l:02d}_{r:02d}"  # sum of exposures in that band
            band_cols = [f"E_a{a:02d}" for a in range(l, r + 1)]
            #X[name] = E[band_cols].sum(axis=1).astype(np.int16)
            X[name] = E[band_cols].mean(axis=1).astype(np.float32)

            cols.append(name)
        X_df = pd.DataFrame(X, index=E.index)
        meta = {"bins": AGE_BINS, "x_cols": cols}

    elif METHOD == "almon2":
        # Z0 = ΣE_a; Z1 = ΣaE_a; Z2 = Σa^2 E_a
        a = ages.astype(float)
        X_df = pd.DataFrame(index=E.index)
        X_df["Z0"] = E.sum(axis=1).astype(np.int16)
        X_df["Z1"] = (E.values * a[None, :]).sum(axis=1)
        X_df["Z2"] = (E.values * (a**2)[None, :]).sum(axis=1)
        meta = {"degree": 2, "ages": ages, "x_cols": ["Z0", "Z1", "Z2"]}

    elif METHOD == "spline":
        # Linear spline basis: beta(a)=g0 + g1*a + Σ_k gk * (a-knot)_+
        a = ages.astype(float)
        X_df = pd.DataFrame(index=E.index)
        X_df["S0"] = E.sum(axis=1).astype(np.int16)
        X_df["S1"] = (E.values * a[None, :]).sum(axis=1)
        x_cols = ["S0", "S1"]
        for k in SPLINE_KNOTS:
            h = np.maximum(a - float(k), 0.0)
            name = f"H{k}"
            X_df[name] = (E.values * h[None, :]).sum(axis=1)
            x_cols.append(name)
        meta = {"knots": SPLINE_KNOTS, "ages": ages, "x_cols": x_cols}

    else:
        raise ValueError("METHOD must be bin/almon2/spline")

    return X_df, meta


# =========================================================
# 6. Regression
# =========================================================

def run_one(df_base: pd.DataFrame, flood_idx: pd.DataFrame, T: int, sample: str) -> pd.DataFrame:
    if sample == "rural":
        dfm = df_base[df_base["is_urban"] == 0].copy()
    elif sample == "urban":
        dfm = df_base[df_base["is_urban"] == 1].copy()
    else:
        raise ValueError("sample must be rural/urban")

    if dfm.empty:
        return pd.DataFrame()

    flood_col = f"flood_ge_T{T}"
    if flood_col not in flood_idx.columns:
        raise ValueError(f"Flood panel missing {flood_col}")

    # build E and compressed X
    E = build_E_age(dfm, flood_idx, flood_col=flood_col)
    X_df, meta = make_regressors(E)

    dfm = pd.concat([dfm, X_df], axis=1)

    x_cols = meta["x_cols"]
    dfm = dfm.dropna(subset=["edu_years", "M2", "prov_birth_fe", "birth_year_c"] + x_cols)
    if dfm.empty:
        return pd.DataFrame()

    X = " + ".join(x_cols)
    fml = f"edu_years ~ {X} + {CONTROL_FML} + i(M2, birth_year_c) | M2 + prov_birth_fe"

    fit = feols(fml, data=dfm, vcov={"CRV1": "M2"})
    td = normalize_tidy(fit.tidy())

    out = td[td["Term"].isin(x_cols)].copy()
    if out.empty:
        return pd.DataFrame()

    out["T"] = int(T)
    out["sample"] = sample
    out["method"] = METHOD
    out["nobs"] = int(len(dfm))
    out["Estimate"] = pd.to_numeric(out["Estimate"], errors="coerce")
    out["StdError"] = pd.to_numeric(out.get("StdError", np.nan), errors="coerce")
    out["PValue"] = pd.to_numeric(out.get("PValue", np.nan), errors="coerce")
    out["CI_low"] = out["Estimate"] - 1.96 * out["StdError"]
    out["CI_high"] = out["Estimate"] + 1.96 * out["StdError"]

    # method-specific labels for plotting
    if METHOD == "bin":
        # map Term -> (l,r)
        bins = meta["bins"]
        term2bin = {f"X_bin_{l:02d}_{r:02d}": (l, r) for (l, r) in bins}
        out["bin_l"] = out["Term"].map(lambda t: term2bin.get(t, (np.nan, np.nan))[0])
        out["bin_r"] = out["Term"].map(lambda t: term2bin.get(t, (np.nan, np.nan))[1])
        out = out.sort_values(["bin_l", "bin_r"])

    else:
        out = out.sort_values("Term")

    return out


# =========================================================
# 7. Visualization (method-specific)
# =========================================================

def plot_bin_effect(out: pd.DataFrame, save_path: Path):
    """Bins: plot segments for each age band with CI"""
    if out.empty:
        return
    sub = out.copy().reset_index(drop=True)
    T = int(sub["T"].iloc[0]); sample = sub["sample"].iloc[0]

    fig, ax = plt.subplots(figsize=(8.8, 4.8))
    ax.axhline(0, linestyle="--", linewidth=1)

    for _, r in sub.iterrows():
        l, rr = int(r["bin_l"]), int(r["bin_r"])
        est, lo, hi, pv = r["Estimate"], r["CI_low"], r["CI_high"], r["PValue"]
        # segment across [l, r]
        ax.plot([l, rr], [est, est], linewidth=2)
        ax.plot([l, rr], [lo, lo], linewidth=1, alpha=0.6)
        ax.plot([l, rr], [hi, hi], linewidth=1, alpha=0.6)
        s = stars_for_p(pv)
        if s:
            ax.text((l+rr)/2, est, s, ha="center", va="bottom", fontsize=11)

    ax.set_xticks(np.arange(AGE0, AGE1 + 1))
    ax.set_xlabel("儿童年龄 a（0–15）")
    ax.set_ylabel("系数：该年龄段暴露（暴露年数求和）对 edu_years 的影响")
    ax.set_title(f"Plan B1 年龄分箱 | T={T} | sample={sample}")
    plt.tight_layout()
    plt.savefig(save_path, dpi=220)
    plt.close(fig)

def plot_param_table(out: pd.DataFrame, save_path: Path):
    """Archived notebook note for 02_multi_return_period_exposure_count_regressions.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if out.empty:
        return
    sub = out.copy().reset_index(drop=True)
    T = int(sub["T"].iloc[0]); sample = sub["sample"].iloc[0]

    xs = np.arange(len(sub))
    fig, ax = plt.subplots(figsize=(8.8, 4.8))
    ax.axhline(0, linestyle="--", linewidth=1)

    y = sub["Estimate"].to_numpy(float)
    lo = sub["CI_low"].to_numpy(float)
    hi = sub["CI_high"].to_numpy(float)
    yerr = np.vstack([y - lo, hi - y])

    ax.errorbar(xs, y, yerr=yerr, fmt="o", capsize=4)
    ax.set_xticks(xs)
    ax.set_xticklabels(sub["Term"].tolist(), rotation=0)
    ax.set_xlabel("约束基函数参数")
    ax.set_ylabel("系数（含 95% CI）")
    ax.set_title(f"Plan B 参数估计 | method={METHOD} | T={T} | sample={sample}")

    for i, pv in enumerate(sub["PValue"].to_numpy(float)):
        s = stars_for_p(pv)
        if s:
            ax.text(i, y[i], s, ha="center", va="bottom", fontsize=11)

    plt.tight_layout()
    plt.savefig(save_path, dpi=220)
    plt.close(fig)


# =========================================================
# 8. MAIN (resume)
# =========================================================

def main():
    done = read_done_set(DONE_TXT)
    print(f"[INFO] done items: {len(done)}")

    flood_idx = load_flood_index()

    need_cols = [f"flood_ge_T{t}" for t in T_LIST]
    miss = [c for c in need_cols if c not in flood_idx.columns]
    if miss and REQUIRE_ALL_T:
        raise ValueError("缺少列: " + ", ".join(miss))

    df_base = load_micro_base()

    for T in T_LIST:
        for sample in SAMPLES:
            key = f"{METHOD}_T{T}_{sample}"
            if key in done:
                print(f"[SKIP] {key} already done.")
                continue

            print("\n==============================")
            print(f"[RUN] {key}")
            print("==============================")

            try:
                out = run_one(df_base, flood_idx, T=T, sample=sample)
            except Exception as e:
                print(f"[ERROR] {key} failed: {repr(e)}")
                continue

            if out.empty:
                print(f"[WARN] {key} empty output (terms dropped or empty sample).")
                mark_done(DONE_TXT, key)
                done.add(key)
                continue

            safe_append_csv(out, MASTER_CSV)
            print(f"[DONE] appended: {MASTER_CSV}")

            # plot
            if METHOD == "bin":
                fig_path = OUT_DIR / f"bin_effect_T{T}_{sample}.png"
                plot_bin_effect(out, fig_path)
            else:
                fig_path = OUT_DIR / f"param_plot_{METHOD}_T{T}_{sample}.png"
                plot_param_table(out, fig_path)

            print(f"[DONE] saved plot: {fig_path}")

            mark_done(DONE_TXT, key)
            done.add(key)
            print(f"[DONE] marked done: {key}")

    print("\n[ALL DONE]")

if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 18
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =======================
# CONFIG
# =======================
RESULT_CSV = Path("/home/ll/jupyter_notebook/result/impact_assessment/flood/statistics/planB_bin_age015_storage_BM_resume/planB_results.csv")
OUT_DIR    = Path("/home/ll/jupyter_notebook/result/impact_assessment/flood/statistics/planB_bin_age015_storage_BM_resume")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Original notebook comment normalized for the public code archive.
SELECT_T = None

# Original notebook comment normalized for the public code archive.
EXPOSURE_AGG = "mean"   # "mean" or "sum"

# Original notebook comment normalized for the public code archive.
def stars(p):
    try:
        p = float(p)
    except Exception:
        return ""
    if p < 0.001: return "****"
    if p < 0.05:  return "**"
    if p < 0.10:  return "*"
    return ""

# =======================
# Helpers
# =======================
def parse_bin(term: str):
    """Archived notebook note for 02_multi_return_period_exposure_count_regressions.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    m = re.search(r"X_bin_(\d{2})_(\d{2})", str(term))
    if not m:
        return None
    l = int(m.group(1)); r = int(m.group(2))
    return l, r, f"{l}\u2013{r}"  # en-dash

def plot_one_T(dfT: pd.DataFrame, T: int, out_png: Path):
    """
    dfT: already filtered to method==bin & T==T
    """
    if dfT.empty:
        print(f"[WARN] T={T} empty; skip.")
        return

    # Original notebook comment normalized for the public code archive.
    bins = dfT["Term"].apply(parse_bin)
    dfT = dfT.copy()
    dfT["bin_l"] = bins.apply(lambda x: x[0] if x else np.nan)
    dfT["bin_r"] = bins.apply(lambda x: x[1] if x else np.nan)
    dfT["bin_lab"] = bins.apply(lambda x: x[2] if x else None)
    dfT = dfT.dropna(subset=["bin_l","bin_r","bin_lab"])
    dfT = dfT.sort_values(["bin_l","bin_r","sample"]).reset_index(drop=True)

    # Original notebook comment normalized for the public code archive.
    sample_order = ["rural", "urban"]
    dfT["sample"] = pd.Categorical(dfT["sample"], categories=sample_order, ordered=True)

    # Original notebook comment normalized for the public code archive.
    est = dfT.pivot(index="bin_lab", columns="sample", values="Estimate").reindex(columns=sample_order)
    lo  = dfT.pivot(index="bin_lab", columns="sample", values="CI_low").reindex(columns=sample_order)
    hi  = dfT.pivot(index="bin_lab", columns="sample", values="CI_high").reindex(columns=sample_order)
    pv  = dfT.pivot(index="bin_lab", columns="sample", values="PValue").reindex(columns=sample_order)

    # Original notebook comment normalized for the public code archive.
    bin_labels = est.index.tolist()
    x = np.arange(len(bin_labels))
    width = 0.36

    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    ax.axhline(0, linestyle="--", linewidth=1)

    # Original notebook comment normalized for the public code archive.
    for j, s in enumerate(sample_order):
        y = est[s].to_numpy(dtype=float)
        ylo = lo[s].to_numpy(dtype=float)
        yhi = hi[s].to_numpy(dtype=float)

        # Original notebook comment normalized for the public code archive.
        yerr = np.vstack([y - ylo, yhi - y])

        # Original notebook comment normalized for the public code archive.
        xpos = x + (j - 0.5) * width
        ax.bar(xpos, y, width=width, label=s)
        ax.errorbar(xpos, y, yerr=yerr, fmt="none", capsize=4, linewidth=1)

        # Original notebook comment normalized for the public code archive.
        pvals = pv[s].to_numpy(dtype=float)
        # Original notebook comment normalized for the public code archive.
        y0, y1 = ax.get_ylim()
        off = 0.03 * (y1 - y0 if y1 > y0 else 1.0)
        for xi, yi, pi in zip(xpos, y, pvals):
            st = stars(pi)
            if st and np.isfinite(yi):
                ax.text(xi, yi + (off if yi >= 0 else -off), st,
                        ha="center", va=("bottom" if yi >= 0 else "top"), fontsize=11)

    ax.set_xticks(x)
    ax.set_xticklabels(bin_labels, rotation=0)
    ax.set_xlabel("年龄段（岁）")

    if EXPOSURE_AGG == "mean":
        ax.set_ylabel("系数：该年龄段洪水暴露占比(均值) 对 edu_years 的边际影响")
    else:
        ax.set_ylabel("系数：该年龄段洪水暴露年数(求和) 对 edu_years 的边际影响")

    ax.set_title(f"Plan B1 年龄分箱（城乡对比） | T={T}")
    ax.legend(title="sample")

    plt.tight_layout()
    plt.savefig(out_png, dpi=220)
    plt.close(fig)
    print(f"[DONE] saved: {out_png}")

# =======================
# Main
# =======================
def main():
    df = pd.read_csv(RESULT_CSV)
    # Original notebook comment normalized for the public code archive.
    if "method" in df.columns:
        df = df[df["method"].astype(str) == "bin"].copy()

    # Original notebook comment normalized for the public code archive.
    df = df[df["sample"].isin(["rural","urban"])].copy()

    # Original notebook comment normalized for the public code archive.
    Ts = sorted(df["T"].dropna().astype(int).unique().tolist())
    if SELECT_T is not None:
        Ts = [int(SELECT_T)] if int(SELECT_T) in Ts else []
    if not Ts:
        raise ValueError("没有可用的 T（或 SELECT_T 不在结果中）")

    for T in Ts:
        dfT = df[df["T"].astype(int) == int(T)].copy()
        out_png = OUT_DIR / f"bar_bin_rural_urban_T{T}.png"
        plot_one_T(dfT, T=int(T), out_png=out_png)

if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 23
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ALL floods (ignore return periods & severity) + age bins (0-15) distributed lag,
ONE final plot only: side-by-side bars (rural vs urban) with 95% CI error bars.

Steps:
1) Flood panel: collapse ALL flood-related columns -> flood_any (county-year)
2) For each sample (rural/urban):
   - build E_a00..E_a15 on the fly from flood_any
   - compress into age-bin regressors (mean or sum)
   - run FE regression
3) Combine rural+urban coefficients -> ONE bar+errorbar plot

Memory-friendly: only build 16 exposure cols per sample, then drop.
"""

from pathlib import Path
import re
import gc
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pyfixest.estimation import feols

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)

# =========================================================
# 0. CONFIG
# =========================================================

FLOOD_CSV = Path(
    "/home/ll/jupyter_notebook/result/county_storage_return_events/"
    "county_flood_events_T10_20_50_100_1980_2015.csv"
)
EDU_PARQUET = Path(
    "/home/ll/jupyter_notebook/gis_data/census/edu_micro_2015.parquet"
)

OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/statistics/"
    "ALLfloods_agebins_oneplot"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

MASTER_CSV = OUT_DIR / "allfloods_agebins_rural_urban_results.csv"
FIG_PATH   = OUT_DIR / "ALLfloods_agebins_bar_rural_urban.png"

# Original notebook comment normalized for the public code archive.
AGE0, AGE1 = 0, 15

# Original notebook comment normalized for the public code archive.
AGE_BINS = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9), (10, 11), (12, 13), (14, 15)]
# Original notebook comment normalized for the public code archive.
# AGE_BINS = [(0,11),(12,13),(14,15)]

# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
BIN_AGG = "mean"   # "mean" or "sum"

# Original notebook comment normalized for the public code archive.
BIRTH_MIN, BIRTH_MAX = 1980, 2000
AGE_2015_MIN, AGE_2015_MAX = 15, 35
ONLY_NON_MIGRANT = True

SAMPLES = ["rural", "urban"]

# Original notebook comment normalized for the public code archive.
CONTROL_FML = "C(M34) + C(M37) + C(M15) + C(M16)"
VCOV_SPEC = {"CRV1": "M2"}  # county-cluster

# =========================================================
# 1. Helpers
# =========================================================

def normalize_tidy(res: pd.DataFrame) -> pd.DataFrame:
    res = res.reset_index()
    if res.columns[0] != "Term":
        res = res.rename(columns={res.columns[0]: "Term"})
    rename_map = {}
    for c in res.columns:
        lc = c.lower().replace(" ", "").replace(".", "")
        if lc in ["stderr", "stderror", "std_error", "std"]:
            rename_map[c] = "StdError"
        if lc in ["pvalue", "p>|t|", "pr(>|t|)", "p"]:
            rename_map[c] = "PValue"
        if lc in ["estimate", "coef", "coefficient"]:
            rename_map[c] = "Estimate"
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

def stars_for_p(p):
    try:
        p = float(p)
    except Exception:
        return ""
    if p < 0.001: return "****"
    if p < 0.05:  return "**"
    if p < 0.10:  return "*"
    return ""

def build_is_urban_is_migrant(df: pd.DataFrame) -> pd.DataFrame:
    # Original notebook comment normalized for the public code archive.
    if "is_urban" not in df.columns and "M2" in df.columns:
        suffix = df["M2"] % 100
        df["is_urban"] = np.where((suffix >= 1) & (suffix <= 20), 1, 0)
    # Original notebook comment normalized for the public code archive.
    if "is_migrant" not in df.columns and "M38" in df.columns:
        df["is_migrant"] = np.where(df["M38"] == 1, 0, 1)
    return df

# =========================================================
# 2. Flood: collapse ALL flood cols -> flood_any (county-year)
# =========================================================

def load_flood_any_index():
    df = pd.read_csv(FLOOD_CSV)

    if "county_code" in df.columns:
        county_col = "county_code"
    elif "county_id" in df.columns:
        county_col = "county_id"
    else:
        raise ValueError("洪水文件中找不到 county_code 或 county_id")

    df[county_col] = pd.to_numeric(df[county_col], errors="coerce").astype("Int64")
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df = df.dropna(subset=[county_col, "year"]).copy()

    # Original notebook comment normalized for the public code archive.
    flood_cols = [c for c in df.columns if c.startswith("flood_ge_")]
    if len(flood_cols) == 0:
        flood_cols = [c for c in df.columns
                      if ("flood" in c.lower()) and (c not in [county_col, "year"])]

    if len(flood_cols) == 0:
        raise ValueError("未在洪水面板中识别到任何洪水列（例如 flood_ge_T10 等）。请检查列名。")

    # Original notebook comment normalized for the public code archive.
    for c in flood_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(np.int8)

    # Original notebook comment normalized for the public code archive.
    df["flood_any"] = df[flood_cols].max(axis=1).astype(np.int8)

    if county_col != "county_code":
        df = df.rename(columns={county_col: "county_code"})
    df["county_code"] = df["county_code"].astype("Int64")

    out = df[["county_code", "year", "flood_any"]].set_index(["county_code", "year"]).sort_index()

    print(f"[INFO] Flood cols used ({len(flood_cols)}): {flood_cols[:10]}{' ...' if len(flood_cols)>10 else ''}")
    print(f"[INFO] Flood_any indexed: shape={out.shape}, share_any={out['flood_any'].mean():.4f}")
    return out

# =========================================================
# 3. Micro base
# =========================================================

def load_micro_base():
    df = pd.read_parquet(EDU_PARQUET)
    print(f"[INFO] Micro raw shape={df.shape}")

    must = ["M2", "birth_year", "edu_years", "M34", "M37", "M15", "M16", "M38"]
    miss = [c for c in must if c not in df.columns]
    if miss:
        raise ValueError("微观数据缺少列: " + ", ".join(miss))

    df["M2"] = pd.to_numeric(df["M2"], errors="coerce").astype("Int64")
    df["birth_year"] = pd.to_numeric(df["birth_year"], errors="coerce").astype("Int64")
    df["edu_years"] = pd.to_numeric(df["edu_years"], errors="coerce")

    df = build_is_urban_is_migrant(df)

    m = pd.Series(True, index=df.index)
    m &= df["birth_year"].between(BIRTH_MIN, BIRTH_MAX)

    if "age_2015" in df.columns:
        df["age_2015"] = pd.to_numeric(df["age_2015"], errors="coerce")
        m &= df["age_2015"].between(AGE_2015_MIN, AGE_2015_MAX)

    if ONLY_NON_MIGRANT:
        m &= (df["is_migrant"] == 0)

    df = df[m].copy()

    df["prov_code"] = (df["M2"] // 10000).astype("Int64")
    df["prov_birth_fe"] = df["prov_code"].astype(str) + "_" + df["birth_year"].astype(int).astype(str)
    df["birth_year_c"] = df["birth_year"].astype(int) - 1995

    for c in ["M34", "M37", "M15", "M16"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
        df = df.dropna(subset=[c])
        df[c] = df[c].astype(int).astype("category")
        df[c] = df[c].cat.remove_unused_categories()

    df = df.dropna(subset=["M2", "birth_year", "edu_years", "prov_birth_fe", "birth_year_c"])
    print(f"[INFO] Micro base shape={df.shape}")

    keep = ["edu_years", "M2", "birth_year", "birth_year_c", "prov_birth_fe",
            "is_urban", "is_migrant", "M34", "M37", "M15", "M16"]
    if "age_2015" in df.columns:
        keep.append("age_2015")

    return df[keep].copy()

# =========================================================
# 4. Build E_a00..E_a15 from flood_any
# =========================================================

def build_E_age(dfm: pd.DataFrame, flood_any_idx: pd.DataFrame) -> pd.DataFrame:
    county = dfm["M2"].astype("Int64").to_numpy()
    byear = dfm["birth_year"].astype(int).to_numpy()
    s = flood_any_idx["flood_any"]  # Series indexed by (county_code, year)

    out = {}
    for a in range(AGE0, AGE1 + 1):
        year = byear + a
        idx = pd.MultiIndex.from_arrays([county, year], names=["county_code", "year"])
        out[f"E_a{a:02d}"] = s.reindex(idx).fillna(0).to_numpy(dtype=np.int8)

    return pd.DataFrame(out, index=dfm.index)

def make_bin_regressors(E: pd.DataFrame):
    X = {}
    x_cols = []
    for (l, r) in AGE_BINS:
        name = f"X_bin_{l:02d}_{r:02d}"
        band_cols = [f"E_a{a:02d}" for a in range(l, r + 1)]
        if BIN_AGG == "mean":
            X[name] = E[band_cols].mean(axis=1).astype(np.float32)
        elif BIN_AGG == "sum":
            X[name] = E[band_cols].sum(axis=1).astype(np.int16)
        else:
            raise ValueError("BIN_AGG must be 'mean' or 'sum'")
        x_cols.append(name)
    return pd.DataFrame(X, index=E.index), x_cols

# =========================================================
# 5. Regression (one time per sample)
# =========================================================

def run_one_sample(df_base: pd.DataFrame, flood_any_idx: pd.DataFrame, sample: str) -> pd.DataFrame:
    if sample == "rural":
        dfm = df_base[df_base["is_urban"] == 0].copy()
    elif sample == "urban":
        dfm = df_base[df_base["is_urban"] == 1].copy()
    else:
        raise ValueError("sample must be rural/urban")

    if dfm.empty:
        return pd.DataFrame()

    E = build_E_age(dfm, flood_any_idx)
    X_df, x_cols = make_bin_regressors(E)
    dfm = pd.concat([dfm, X_df], axis=1)

    dfm = dfm.dropna(subset=["edu_years", "M2", "prov_birth_fe", "birth_year_c"] + x_cols)
    if dfm.empty:
        return pd.DataFrame()

    X = " + ".join(x_cols)
    fml = f"edu_years ~ {X} + {CONTROL_FML} + i(M2, birth_year_c) | M2 + prov_birth_fe"

    fit = feols(fml, data=dfm, vcov=VCOV_SPEC)
    td = normalize_tidy(fit.tidy())

    out = td[td["Term"].isin(x_cols)].copy()
    if out.empty:
        return pd.DataFrame()

    out["sample"] = sample
    out["method"] = "bin_allfloods"
    out["bin_agg"] = BIN_AGG
    out["nobs"] = int(len(dfm))

    out["Estimate"] = pd.to_numeric(out["Estimate"], errors="coerce")
    out["StdError"] = pd.to_numeric(out.get("StdError", np.nan), errors="coerce")
    out["PValue"] = pd.to_numeric(out.get("PValue", np.nan), errors="coerce")
    out["CI_low"] = out["Estimate"] - 1.96 * out["StdError"]
    out["CI_high"] = out["Estimate"] + 1.96 * out["StdError"]

    term2bin = {f"X_bin_{l:02d}_{r:02d}": (l, r) for (l, r) in AGE_BINS}
    out["bin_l"] = out["Term"].map(lambda t: term2bin.get(t, (np.nan, np.nan))[0])
    out["bin_r"] = out["Term"].map(lambda t: term2bin.get(t, (np.nan, np.nan))[1])
    out = out.sort_values(["bin_l", "bin_r"]).reset_index(drop=True)

    # free memory
    del E, X_df, dfm, fit, td
    gc.collect()
    return out

# =========================================================
# 6. ONE plot: bars + error bars (rural vs urban)
# =========================================================

def plot_one_bar_rural_urban(res: pd.DataFrame, save_path: Path):
    if res.empty:
        return

    df = res.copy()
    df["bin_label"] = df.apply(lambda r: f"{int(r['bin_l'])}\u2013{int(r['bin_r'])}", axis=1)
    bin_order = [f"{l}\u2013{r}" for (l, r) in AGE_BINS]

    df["bin_label"] = pd.Categorical(df["bin_label"], categories=bin_order, ordered=True)
    df["sample"] = pd.Categorical(df["sample"], categories=["rural", "urban"], ordered=True)

    est = df.pivot(index="bin_label", columns="sample", values="Estimate").reindex(bin_order)
    lo  = df.pivot(index="bin_label", columns="sample", values="CI_low").reindex(bin_order)
    hi  = df.pivot(index="bin_label", columns="sample", values="CI_high").reindex(bin_order)
    pv  = df.pivot(index="bin_label", columns="sample", values="PValue").reindex(bin_order)

    x = np.arange(len(bin_order))
    width = 0.36

    fig, ax = plt.subplots(figsize=(11.2, 5.4))
    ax.axhline(0, linestyle="--", linewidth=1)

    for j, s in enumerate(["rural", "urban"]):
        y = est[s].to_numpy(dtype=float)
        ylo = lo[s].to_numpy(dtype=float)
        yhi = hi[s].to_numpy(dtype=float)
        yerr = np.vstack([y - ylo, yhi - y])

        xpos = x + (j - 0.5) * width
        ax.bar(xpos, y, width=width, label=s)
        ax.errorbar(xpos, y, yerr=yerr, fmt="none", capsize=4, linewidth=1)

        # stars
        y0, y1 = ax.get_ylim()
        off = 0.03 * (y1 - y0 if y1 > y0 else 1.0)
        pvals = pv[s].to_numpy(dtype=float)
        for xi, yi, pi in zip(xpos, y, pvals):
            st = stars_for_p(pi)
            if st and np.isfinite(yi):
                ax.text(xi, yi + (off if yi >= 0 else -off),
                        st, ha="center",
                        va=("bottom" if yi >= 0 else "top"),
                        fontsize=11)

    ax.set_xticks(x)
    ax.set_xticklabels(bin_order, rotation=0)
    ax.set_xlabel("年龄段（岁）")

    if BIN_AGG == "mean":
        ax.set_ylabel("系数：年龄段内洪水暴露均值 对 edu_years 的边际影响")
        agg_note = "mean"
    else:
        ax.set_ylabel("系数：年龄段内洪水暴露年数(求和) 对 edu_years 的边际影响")
        agg_note = "sum"

    ax.set_title(f"所有洪水（不分重现期/不分严重度）| 年龄分段 | 城乡并排 | agg={agg_note}")
    ax.legend(title="sample")

    plt.tight_layout()
    plt.savefig(save_path, dpi=240)
    plt.close(fig)

# =========================================================
# 7. MAIN
# =========================================================

def main():
    flood_any_idx = load_flood_any_index()
    df_base = load_micro_base()

    outs = []
    for sample in SAMPLES:
        print("\n==============================")
        print(f"[RUN] sample={sample}")
        print("==============================")
        out = run_one_sample(df_base, flood_any_idx, sample=sample)
        if out.empty:
            print(f"[WARN] sample={sample}: empty output")
        else:
            outs.append(out)

    if len(outs) == 0:
        raise RuntimeError("rural/urban 都没有跑出结果，请检查样本筛选条件/数据列名。")

    res = pd.concat(outs, axis=0, ignore_index=True)

    # save result table
    res.to_csv(MASTER_CSV, index=False, encoding="utf-8-sig")
    print(f"[DONE] saved csv: {MASTER_CSV}")

    # ONE plot
    plot_one_bar_rural_urban(res, FIG_PATH)
    print(f"[DONE] saved ONE plot: {FIG_PATH}")

if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 27
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 02_multi_return_period_exposure_count_regressions.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings
from math import erf, sqrt

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pyfixest.estimation import feols

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)

# =========================================================
# 0. CONFIG
# =========================================================

# --- choose exposure scale:
# True  -> mean within group (0-1), easier to compare across groups with different lengths
# False -> sum within group (0..#years), interpretable as "per extra exposed year"
USE_MEAN = False

# --- two groups (non-contiguous "other")
BIN_SETS = {
    "X_mid_12_13": list(range(12, 14)),                    # 12, 13
    "X_other":     list(range(0, 12)) + list(range(14, 16)) # 0-11, 14-15
}
BIN_LABELS = {
    "X_mid_12_13": "12–13",
    "X_other": "0–11 & 14–15"
}

# --- data paths
FLOOD_CSV = Path(
    "/home/ll/jupyter_notebook/result/county_storage_return_events/"
    "county_flood_events_T10_20_50_100_1980_2015.csv"
)
EDU_PARQUET = Path(
    "/home/ll/jupyter_notebook/gis_data/census/edu_micro_2015.parquet"
)

OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/statistics/"
    f"planB_two_groups_{'mean' if USE_MEAN else 'sum'}_age015_storage_BM_resume"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

DONE_TXT   = OUT_DIR / "done.txt"
MASTER_CSV = OUT_DIR / "planB_two_groups_results.csv"

# --- sample restrictions
BIRTH_MIN, BIRTH_MAX = 1980, 2000
AGE_2015_MIN, AGE_2015_MAX = 15, 35
ONLY_NON_MIGRANT = True

SAMPLES = ["rural", "urban"]
T_LIST = [2, 5, 10, 20, 50, 100]
REQUIRE_ALL_T = True

CONTROL_FML = "C(M34) + C(M37) + C(M15) + C(M16)"
SIG_LEVEL = 0.10


# =========================================================
# 1. Small helpers
# =========================================================

def read_done_set(path: Path) -> set:
    if not path.exists():
        return set()
    return set([x.strip() for x in path.read_text(encoding="utf-8").splitlines() if x.strip()])

def mark_done(path: Path, key: str):
    with path.open("a", encoding="utf-8") as f:
        f.write(key + "\n")

def safe_append_csv(df: pd.DataFrame, path: Path):
    if df.empty:
        return
    if not path.exists():
        df.to_csv(path, index=False, encoding="utf-8-sig")
    else:
        df.to_csv(path, index=False, header=False, mode="a", encoding="utf-8-sig")

def normalize_tidy(res: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 02_multi_return_period_exposure_count_regressions.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    res = res.reset_index()
    if res.columns[0] != "Term":
        res = res.rename(columns={res.columns[0]: "Term"})
    rename_map = {}
    for c in res.columns:
        lc = c.lower().replace(" ", "").replace(".", "")
        if lc in ["stderr", "stderror", "std_error", "std"]:
            rename_map[c] = "StdError"
        if lc in ["pvalue", "p>|t|", "pr(>|t|)", "p"]:
            rename_map[c] = "PValue"
        if lc in ["estimate", "coef", "coefficient"]:
            rename_map[c] = "Estimate"
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

def stars_for_p(p: float) -> str:
    try:
        p = float(p)
    except Exception:
        return ""
    if p < 0.001: return "****"
    if p < 0.05:  return "**"
    if p < 0.10:  return "*"
    return ""

def norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))

def build_is_urban_is_migrant(df: pd.DataFrame) -> pd.DataFrame:
    # Original notebook comment normalized for the public code archive.
    if "is_urban" not in df.columns and "M2" in df.columns:
        suffix = df["M2"] % 100
        df["is_urban"] = np.where((suffix >= 1) & (suffix <= 20), 1, 0)
    # Original notebook comment normalized for the public code archive.
    if "is_migrant" not in df.columns and "M38" in df.columns:
        df["is_migrant"] = np.where(df["M38"] == 1, 0, 1)
    return df


# =========================================================
# 2. Load flood panel -> MultiIndex
# =========================================================

def load_flood_index() -> pd.DataFrame:
    df = pd.read_csv(FLOOD_CSV)
    if "county_code" in df.columns:
        county_col = "county_code"
    elif "county_id" in df.columns:
        county_col = "county_id"
    else:
        raise ValueError("洪水文件中找不到 county_code 或 county_id")

    df[county_col] = pd.to_numeric(df[county_col], errors="coerce").astype("Int64")
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    need = [f"flood_ge_T{t}" for t in T_LIST]
    miss = [c for c in need if c not in df.columns]
    if miss and REQUIRE_ALL_T:
        raise ValueError("洪水面板缺少列: " + ", ".join(miss))

    keep = [county_col, "year"] + [c for c in need if c in df.columns]
    df = df[keep].dropna(subset=[county_col, "year"])

    for c in keep:
        if c.startswith("flood_ge_T"):
            df[c] = df[c].fillna(0).astype(np.int8)

    if county_col != "county_code":
        df = df.rename(columns={county_col: "county_code"})
    df["county_code"] = df["county_code"].astype("Int64")

    df = df.set_index(["county_code", "year"]).sort_index()
    print(f"[INFO] Flood indexed: shape={df.shape}, cols={list(df.columns)}")
    return df


# =========================================================
# 3. Load micro base (memory-saving)
# =========================================================

def load_micro_base() -> pd.DataFrame:
    df = pd.read_parquet(EDU_PARQUET)
    print(f"[INFO] Micro raw shape={df.shape}")

    must = ["M2", "birth_year", "edu_years", "M34", "M37", "M15", "M16", "M38"]
    miss = [c for c in must if c not in df.columns]
    if miss:
        raise ValueError("微观数据缺少列: " + ", ".join(miss))

    df["M2"] = pd.to_numeric(df["M2"], errors="coerce").astype("Int64")
    df["birth_year"] = pd.to_numeric(df["birth_year"], errors="coerce").astype("Int64")
    df["edu_years"] = pd.to_numeric(df["edu_years"], errors="coerce")

    df = build_is_urban_is_migrant(df)

    m = pd.Series(True, index=df.index)
    m &= df["birth_year"].between(BIRTH_MIN, BIRTH_MAX)

    if "age_2015" in df.columns:
        df["age_2015"] = pd.to_numeric(df["age_2015"], errors="coerce")
        m &= df["age_2015"].between(AGE_2015_MIN, AGE_2015_MAX)

    if ONLY_NON_MIGRANT:
        m &= (df["is_migrant"] == 0)

    df = df[m].copy()

    # FE variables
    df["prov_code"] = (df["M2"] // 10000).astype("Int64")
    df["prov_birth_fe"] = df["prov_code"].astype(str) + "_" + df["birth_year"].astype(int).astype(str)
    df["birth_year_c"] = df["birth_year"].astype(int) - 1995

    # controls -> category
    for c in ["M34", "M37", "M15", "M16"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
        df = df.dropna(subset=[c])
        df[c] = df[c].astype(int).astype("category")
        df[c] = df[c].cat.remove_unused_categories()

    df = df.dropna(subset=["M2", "birth_year", "edu_years", "prov_birth_fe", "birth_year_c"])
    print(f"[INFO] Micro base shape={df.shape}")

    keep = ["edu_years", "M2", "birth_year", "birth_year_c", "prov_birth_fe",
            "is_urban", "is_migrant", "M34", "M37", "M15", "M16"]
    if "age_2015" in df.columns:
        keep.append("age_2015")
    return df[keep].copy()


# =========================================================
# 4. Build two-group exposures directly (NO 16 cols)
# =========================================================

def build_two_group_exposures(dfm: pd.DataFrame, flood_idx: pd.DataFrame, flood_col: str) -> pd.DataFrame:
    """
    Build:
      X_mid_12_13 : mean/sum of exposures at ages {12,13}
      X_other     : mean/sum of exposures at ages {0..11,14,15}
    Using reindex on MultiIndex (county_code, year) repeatedly but only accumulates 2 arrays.
    """
    county = dfm["M2"].astype("Int64").to_numpy()
    byear  = dfm["birth_year"].astype(int).to_numpy()
    s = flood_idx[flood_col]  # Series indexed by (county_code, year)

    out = {}
    for name, ages in BIN_SETS.items():
        acc = np.zeros(len(dfm), dtype=np.int16)
        for a in ages:
            year = byear + int(a)
            idx = pd.MultiIndex.from_arrays([county, year], names=["county_code", "year"])
            acc += s.reindex(idx).fillna(0).to_numpy(dtype=np.int16)

        if USE_MEAN:
            out[name] = (acc / float(len(ages))).astype(np.float32)
        else:
            out[name] = acc.astype(np.int16)

    return pd.DataFrame(out, index=dfm.index)


# =========================================================
# 5. Regression + (optional) diff test using covariance
# =========================================================

def try_get_vcov_matrix(fit):
    """
    Try to obtain coefficient covariance matrix as pandas.DataFrame.
    pyfixest versions differ; attempt multiple fallbacks.
    """
    # 1) common: fit.vcov() or fit.vcov
    for attr in ["vcov", "vcov_"]:
        if hasattr(fit, attr):
            obj = getattr(fit, attr)
            try:
                if callable(obj):
                    V = obj()
                else:
                    V = obj
                if V is not None:
                    # could be np.ndarray or pd.DataFrame
                    if isinstance(V, pd.DataFrame):
                        return V
                    if isinstance(V, np.ndarray):
                        # need coefficient names
                        try:
                            names = list(fit.coef().index)
                        except Exception:
                            names = None
                        if names and len(names) == V.shape[0]:
                            return pd.DataFrame(V, index=names, columns=names)
            except Exception:
                pass

    # 2) try fit.get_vcov()
    if hasattr(fit, "get_vcov"):
        try:
            V = fit.get_vcov()
            if isinstance(V, pd.DataFrame):
                return V
            if isinstance(V, np.ndarray):
                try:
                    names = list(fit.coef().index)
                except Exception:
                    names = None
                if names and len(names) == V.shape[0]:
                    return pd.DataFrame(V, index=names, columns=names)
        except Exception:
            pass

    return None

def run_one(df_base: pd.DataFrame, flood_idx: pd.DataFrame, T: int, sample: str) -> pd.DataFrame:
    # sample filter
    if sample == "rural":
        dfm = df_base[df_base["is_urban"] == 0].copy()
    elif sample == "urban":
        dfm = df_base[df_base["is_urban"] == 1].copy()
    else:
        raise ValueError("sample must be rural/urban")

    if dfm.empty:
        return pd.DataFrame()

    flood_col = f"flood_ge_T{T}"
    if flood_col not in flood_idx.columns:
        raise ValueError(f"Flood panel missing {flood_col}")

    # build two-group X
    X_df = build_two_group_exposures(dfm, flood_idx, flood_col=flood_col)
    dfm = pd.concat([dfm, X_df], axis=1)

    x_cols = list(BIN_SETS.keys())
    dfm = dfm.dropna(subset=["edu_years", "M2", "prov_birth_fe", "birth_year_c"] + x_cols)
    if dfm.empty:
        return pd.DataFrame()

    X = " + ".join(x_cols)
    fml = f"edu_years ~ {X} + {CONTROL_FML} + i(M2, birth_year_c) | M2 + prov_birth_fe"

    fit = feols(fml, data=dfm, vcov={"CRV1": "M2"})
    td = normalize_tidy(fit.tidy())

    out = td[td["Term"].isin(x_cols)].copy()
    if out.empty:
        return pd.DataFrame()

    out["T"] = int(T)
    out["sample"] = sample
    out["method"] = "two_groups_mean" if USE_MEAN else "two_groups_sum"
    out["group_label"] = out["Term"].map(BIN_LABELS).fillna(out["Term"])
    out["nobs"] = int(len(dfm))

    out["Estimate"] = pd.to_numeric(out["Estimate"], errors="coerce")
    out["StdError"] = pd.to_numeric(out.get("StdError", np.nan), errors="coerce")
    out["PValue"] = pd.to_numeric(out.get("PValue", np.nan), errors="coerce")
    out["CI_low"] = out["Estimate"] - 1.96 * out["StdError"]
    out["CI_high"] = out["Estimate"] + 1.96 * out["StdError"]

    # ---- optional: diff test (mid - other) using covariance
    # add one extra row: Term="diff_mid_minus_other"
    if set(x_cols).issubset(set(out["Term"].tolist())):
        V = try_get_vcov_matrix(fit)
        if V is not None:
            t1, t2 = "X_mid_12_13", "X_other"
            if (t1 in V.index) and (t2 in V.index):
                b = {r["Term"]: float(r["Estimate"]) for _, r in out.iterrows()}
                diff = b[t1] - b[t2]
                var = float(V.loc[t1, t1] + V.loc[t2, t2] - 2.0 * V.loc[t1, t2])
                var = max(var, 0.0)
                se = float(np.sqrt(var))
                z = diff / se if se > 0 else np.nan
                p = 2.0 * (1.0 - norm_cdf(abs(z))) if np.isfinite(z) else np.nan

                diff_row = {
                    "Term": "diff_mid_minus_other",
                    "Estimate": diff,
                    "StdError": se,
                    "PValue": p,
                    "CI_low": diff - 1.96 * se if np.isfinite(se) else np.nan,
                    "CI_high": diff + 1.96 * se if np.isfinite(se) else np.nan,
                    "T": int(T),
                    "sample": sample,
                    "method": out["method"].iloc[0],
                    "group_label": "diff(12–13) - other",
                    "nobs": int(len(dfm)),
                }
                out = pd.concat([out, pd.DataFrame([diff_row])], ignore_index=True)

    # order rows
    order = ["X_mid_12_13", "X_other", "diff_mid_minus_other"]
    out["__ord"] = out["Term"].map({k:i for i,k in enumerate(order)}).fillna(99)
    out = out.sort_values("__ord").drop(columns="__ord").reset_index(drop=True)
    return out


# =========================================================
# 6. Visualization
# =========================================================

def plot_two_groups(out: pd.DataFrame, save_path: Path):
    if out.empty:
        return

    # only plot the two coefficients (exclude diff row if exists)
    sub = out[out["Term"].isin(["X_mid_12_13", "X_other"])].copy()
    if sub.empty:
        return

    T = int(sub["T"].iloc[0])
    sample = sub["sample"].iloc[0]

    labels = sub["group_label"].tolist()
    est = sub["Estimate"].to_numpy(float)
    lo  = sub["CI_low"].to_numpy(float)
    hi  = sub["CI_high"].to_numpy(float)
    pv  = sub["PValue"].to_numpy(float)

    yerr = np.vstack([est - lo, hi - est])
    xs = np.arange(len(labels))

    fig, ax = plt.subplots(figsize=(6.8, 4.8))
    ax.axhline(0, linestyle="--", linewidth=1)

    ax.errorbar(xs, est, yerr=yerr, fmt="o", capsize=4)

    # stars
    y0, y1 = ax.get_ylim()
    offset = 0.06 * (y1 - y0 if y1 > y0 else 1.0)
    for x, b, p in zip(xs, est, pv):
        s = stars_for_p(p)
        if s:
            ax.text(x, b + offset, s, ha="center", va="bottom", fontsize=12)

    # diff p-value in title if available
    diff_row = out[out["Term"] == "diff_mid_minus_other"]
    diff_note = ""
    if not diff_row.empty:
        p_diff = float(diff_row["PValue"].iloc[0])
        diff_note = f" | diff p={p_diff:.3g}"

    ax.set_xticks(xs)
    ax.set_xticklabels(labels)
    ax.set_xlabel("年龄组")
    ax.set_ylabel("系数：该年龄组暴露对 edu_years 的边际影响")
    ax.set_title(
        f"Two-group exposure ({'mean' if USE_MEAN else 'sum'}) | T={T} | {sample}{diff_note}"
    )

    plt.tight_layout()
    plt.savefig(save_path, dpi=220)
    plt.close(fig)


# =========================================================
# 7. MAIN (resume)
# =========================================================

def main():
    done = read_done_set(DONE_TXT)
    print(f"[INFO] done items: {len(done)}")

    flood_idx = load_flood_index()
    need_cols = [f"flood_ge_T{t}" for t in T_LIST]
    miss = [c for c in need_cols if c not in flood_idx.columns]
    if miss and REQUIRE_ALL_T:
        raise ValueError("缺少列: " + ", ".join(miss))

    df_base = load_micro_base()

    for T in T_LIST:
        for sample in SAMPLES:
            key = f"two_groups_{'mean' if USE_MEAN else 'sum'}_T{T}_{sample}"
            if key in done:
                print(f"[SKIP] {key} already done.")
                continue

            print("\n==============================")
            print(f"[RUN] {key}")
            print("==============================")

            try:
                out = run_one(df_base, flood_idx, T=T, sample=sample)
            except Exception as e:
                print(f"[ERROR] {key} failed: {repr(e)}")
                continue

            if out.empty:
                print(f"[WARN] {key} empty output (terms dropped or empty sample).")
                mark_done(DONE_TXT, key)
                done.add(key)
                continue

            safe_append_csv(out, MASTER_CSV)
            print(f"[DONE] appended: {MASTER_CSV}")

            fig_path = OUT_DIR / f"two_groups_T{T}_{sample}.png"
            plot_two_groups(out, fig_path)
            print(f"[DONE] saved plot: {fig_path}")

            mark_done(DONE_TXT, key)
            done.add(key)
            print(f"[DONE] marked done: {key}")

    print("\n[ALL DONE]")

if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 29
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 02_multi_return_period_exposure_count_regressions.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings
from math import erf, sqrt

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pyfixest.estimation import feols

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)

# =========================================================
# 0. CONFIG
# =========================================================

# --- choose exposure scale:
# True  -> mean within group (0-1), easier to compare across groups with different lengths (RECOMMENDED)
# False -> sum within group (0..#years), interpretable as "per extra exposed year" but scale differs by group length
USE_MEAN = True

# Original notebook comment normalized for the public code archive.
BIN_SETS = {
    "X_mid_10_13": list(range(10, 14)),                     # 10,11,12,13 (4 years)
    "X_other":     list(range(0, 10)) + list(range(14, 16))  # 0-9 (10y) + 14-15 (2y) = 12 years
}
BIN_LABELS = {
    "X_mid_10_13": "10–13",
    "X_other": "0–9 & 14–15"
}

# --- data paths
FLOOD_CSV = Path(
    "/home/ll/jupyter_notebook/result/county_storage_return_events/"
    "county_flood_events_T10_20_50_100_1980_2015.csv"
)
EDU_PARQUET = Path(
    "/home/ll/jupyter_notebook/gis_data/census/edu_micro_2015.parquet"
)

OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/statistics/"
    f"planB_two_groups_10_13_{'mean' if USE_MEAN else 'sum'}_age015_storage_BM_resume"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

DONE_TXT   = OUT_DIR / "done.txt"
MASTER_CSV = OUT_DIR / "planB_two_groups_results.csv"

# --- sample restrictions
BIRTH_MIN, BIRTH_MAX = 1980, 2000
AGE_2015_MIN, AGE_2015_MAX = 15, 35
ONLY_NON_MIGRANT = True

SAMPLES = ["rural", "urban"]
T_LIST = [2, 5, 10, 20, 50, 100]
REQUIRE_ALL_T = True

CONTROL_FML = "C(M34) + C(M37) + C(M15) + C(M16)"


# =========================================================
# 1. Small helpers
# =========================================================

def read_done_set(path: Path) -> set:
    if not path.exists():
        return set()
    return set([x.strip() for x in path.read_text(encoding="utf-8").splitlines() if x.strip()])

def mark_done(path: Path, key: str):
    with path.open("a", encoding="utf-8") as f:
        f.write(key + "\n")

def safe_append_csv(df: pd.DataFrame, path: Path):
    if df.empty:
        return
    if not path.exists():
        df.to_csv(path, index=False, encoding="utf-8-sig")
    else:
        df.to_csv(path, index=False, header=False, mode="a", encoding="utf-8-sig")

def normalize_tidy(res: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 02_multi_return_period_exposure_count_regressions.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    res = res.reset_index()
    if res.columns[0] != "Term":
        res = res.rename(columns={res.columns[0]: "Term"})
    rename_map = {}
    for c in res.columns:
        lc = c.lower().replace(" ", "").replace(".", "")
        if lc in ["stderr", "stderror", "std_error", "std"]:
            rename_map[c] = "StdError"
        if lc in ["pvalue", "p>|t|", "pr(>|t|)", "p"]:
            rename_map[c] = "PValue"
        if lc in ["estimate", "coef", "coefficient"]:
            rename_map[c] = "Estimate"
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

def stars_for_p(p: float) -> str:
    try:
        p = float(p)
    except Exception:
        return ""
    if p < 0.001: return "****"
    if p < 0.05:  return "**"
    if p < 0.10:  return "*"
    return ""

def norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))

def build_is_urban_is_migrant(df: pd.DataFrame) -> pd.DataFrame:
    # Original notebook comment normalized for the public code archive.
    if "is_urban" not in df.columns and "M2" in df.columns:
        suffix = df["M2"] % 100
        df["is_urban"] = np.where((suffix >= 1) & (suffix <= 20), 1, 0)
    # Original notebook comment normalized for the public code archive.
    if "is_migrant" not in df.columns and "M38" in df.columns:
        df["is_migrant"] = np.where(df["M38"] == 1, 0, 1)
    return df


# =========================================================
# 2. Load flood panel -> MultiIndex
# =========================================================

def load_flood_index() -> pd.DataFrame:
    df = pd.read_csv(FLOOD_CSV)

    if "county_code" in df.columns:
        county_col = "county_code"
    elif "county_id" in df.columns:
        county_col = "county_id"
    else:
        raise ValueError("洪水文件中找不到 county_code 或 county_id")

    df[county_col] = pd.to_numeric(df[county_col], errors="coerce").astype("Int64")
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    need = [f"flood_ge_T{t}" for t in T_LIST]
    miss = [c for c in need if c not in df.columns]
    if miss and REQUIRE_ALL_T:
        raise ValueError("洪水面板缺少列: " + ", ".join(miss))

    keep = [county_col, "year"] + [c for c in need if c in df.columns]
    df = df[keep].dropna(subset=[county_col, "year"])

    for c in keep:
        if c.startswith("flood_ge_T"):
            df[c] = df[c].fillna(0).astype(np.int8)

    if county_col != "county_code":
        df = df.rename(columns={county_col: "county_code"})
    df["county_code"] = df["county_code"].astype("Int64")

    df = df.set_index(["county_code", "year"]).sort_index()
    print(f"[INFO] Flood indexed: shape={df.shape}, cols={list(df.columns)}")
    return df


# =========================================================
# 3. Load micro base (memory-saving)
# =========================================================

def load_micro_base() -> pd.DataFrame:
    df = pd.read_parquet(EDU_PARQUET)
    print(f"[INFO] Micro raw shape={df.shape}")

    must = ["M2", "birth_year", "edu_years", "M34", "M37", "M15", "M16", "M38"]
    miss = [c for c in must if c not in df.columns]
    if miss:
        raise ValueError("微观数据缺少列: " + ", ".join(miss))

    df["M2"] = pd.to_numeric(df["M2"], errors="coerce").astype("Int64")
    df["birth_year"] = pd.to_numeric(df["birth_year"], errors="coerce").astype("Int64")
    df["edu_years"] = pd.to_numeric(df["edu_years"], errors="coerce")

    df = build_is_urban_is_migrant(df)

    m = pd.Series(True, index=df.index)
    m &= df["birth_year"].between(BIRTH_MIN, BIRTH_MAX)

    if "age_2015" in df.columns:
        df["age_2015"] = pd.to_numeric(df["age_2015"], errors="coerce")
        m &= df["age_2015"].between(AGE_2015_MIN, AGE_2015_MAX)

    if ONLY_NON_MIGRANT:
        m &= (df["is_migrant"] == 0)

    df = df[m].copy()

    # FE variables
    df["prov_code"] = (df["M2"] // 10000).astype("Int64")
    df["prov_birth_fe"] = df["prov_code"].astype(str) + "_" + df["birth_year"].astype(int).astype(str)
    df["birth_year_c"] = df["birth_year"].astype(int) - 1995

    # controls -> category
    for c in ["M34", "M37", "M15", "M16"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
        df = df.dropna(subset=[c])
        df[c] = df[c].astype(int).astype("category")
        df[c] = df[c].cat.remove_unused_categories()

    df = df.dropna(subset=["M2", "birth_year", "edu_years", "prov_birth_fe", "birth_year_c"])
    print(f"[INFO] Micro base shape={df.shape}")

    keep = ["edu_years", "M2", "birth_year", "birth_year_c", "prov_birth_fe",
            "is_urban", "is_migrant", "M34", "M37", "M15", "M16"]
    if "age_2015" in df.columns:
        keep.append("age_2015")
    return df[keep].copy()


# =========================================================
# 4. Build two-group exposures directly (NO 16 cols)
# =========================================================

def build_two_group_exposures(dfm: pd.DataFrame, flood_idx: pd.DataFrame, flood_col: str) -> pd.DataFrame:
    """
    Build:
      X_mid_10_13 : mean/sum of exposures at ages {10,11,12,13}
      X_other     : mean/sum of exposures at ages {0..9,14,15}
    Only accumulates 2 arrays -> memory-friendly.
    """
    county = dfm["M2"].astype("Int64").to_numpy()
    byear  = dfm["birth_year"].astype(int).to_numpy()
    s = flood_idx[flood_col]  # Series indexed by (county_code, year)

    out = {}
    for name, ages in BIN_SETS.items():
        acc = np.zeros(len(dfm), dtype=np.int16)
        for a in ages:
            year = byear + int(a)
            idx = pd.MultiIndex.from_arrays([county, year], names=["county_code", "year"])
            acc += s.reindex(idx).fillna(0).to_numpy(dtype=np.int16)

        if USE_MEAN:
            out[name] = (acc / float(len(ages))).astype(np.float32)
        else:
            out[name] = acc.astype(np.int16)

    return pd.DataFrame(out, index=dfm.index)


# =========================================================
# 5. Diff test: need covariance matrix
# =========================================================

def try_get_vcov_matrix(fit):
    """
    Try to obtain coefficient covariance matrix as pandas.DataFrame.
    pyfixest versions differ; attempt multiple fallbacks.
    """
    for attr in ["vcov", "vcov_"]:
        if hasattr(fit, attr):
            obj = getattr(fit, attr)
            try:
                V = obj() if callable(obj) else obj
                if V is None:
                    continue
                if isinstance(V, pd.DataFrame):
                    return V
                if isinstance(V, np.ndarray):
                    try:
                        names = list(fit.coef().index)
                    except Exception:
                        names = None
                    if names and len(names) == V.shape[0]:
                        return pd.DataFrame(V, index=names, columns=names)
            except Exception:
                pass

    if hasattr(fit, "get_vcov"):
        try:
            V = fit.get_vcov()
            if isinstance(V, pd.DataFrame):
                return V
            if isinstance(V, np.ndarray):
                try:
                    names = list(fit.coef().index)
                except Exception:
                    names = None
                if names and len(names) == V.shape[0]:
                    return pd.DataFrame(V, index=names, columns=names)
        except Exception:
            pass

    return None


# =========================================================
# 6. Regression
# =========================================================

def run_one(df_base: pd.DataFrame, flood_idx: pd.DataFrame, T: int, sample: str) -> pd.DataFrame:
    # sample filter
    if sample == "rural":
        dfm = df_base[df_base["is_urban"] == 0].copy()
    elif sample == "urban":
        dfm = df_base[df_base["is_urban"] == 1].copy()
    else:
        raise ValueError("sample must be rural/urban")

    if dfm.empty:
        return pd.DataFrame()

    flood_col = f"flood_ge_T{T}"
    if flood_col not in flood_idx.columns:
        raise ValueError(f"Flood panel missing {flood_col}")

    # build two-group X
    X_df = build_two_group_exposures(dfm, flood_idx, flood_col=flood_col)
    dfm = pd.concat([dfm, X_df], axis=1)

    x_cols = list(BIN_SETS.keys())
    dfm = dfm.dropna(subset=["edu_years", "M2", "prov_birth_fe", "birth_year_c"] + x_cols)
    if dfm.empty:
        return pd.DataFrame()

    X = " + ".join(x_cols)
    fml = f"edu_years ~ {X} + {CONTROL_FML} + i(M2, birth_year_c) | M2 + prov_birth_fe"

    fit = feols(fml, data=dfm, vcov={"CRV1": "M2"})
    td = normalize_tidy(fit.tidy())

    out = td[td["Term"].isin(x_cols)].copy()
    if out.empty:
        return pd.DataFrame()

    out["T"] = int(T)
    out["sample"] = sample
    out["method"] = "two_groups_mean" if USE_MEAN else "two_groups_sum"
    out["group_label"] = out["Term"].map(BIN_LABELS).fillna(out["Term"])
    out["nobs"] = int(len(dfm))

    out["Estimate"] = pd.to_numeric(out["Estimate"], errors="coerce")
    out["StdError"] = pd.to_numeric(out.get("StdError", np.nan), errors="coerce")
    out["PValue"] = pd.to_numeric(out.get("PValue", np.nan), errors="coerce")
    out["CI_low"] = out["Estimate"] - 1.96 * out["StdError"]
    out["CI_high"] = out["Estimate"] + 1.96 * out["StdError"]

    # ---- optional: diff test (mid - other) using covariance
    if set(x_cols).issubset(set(out["Term"].tolist())):
        V = try_get_vcov_matrix(fit)
        if V is not None:
            t1, t2 = "X_mid_10_13", "X_other"
            if (t1 in V.index) and (t2 in V.index):
                b = {r["Term"]: float(r["Estimate"]) for _, r in out.iterrows()}
                diff = b[t1] - b[t2]
                var = float(V.loc[t1, t1] + V.loc[t2, t2] - 2.0 * V.loc[t1, t2])
                var = max(var, 0.0)
                se = float(np.sqrt(var))
                z = diff / se if se > 0 else np.nan
                p = 2.0 * (1.0 - norm_cdf(abs(z))) if np.isfinite(z) else np.nan

                diff_row = {
                    "Term": "diff_mid_minus_other",
                    "Estimate": diff,
                    "StdError": se,
                    "PValue": p,
                    "CI_low": diff - 1.96 * se if np.isfinite(se) else np.nan,
                    "CI_high": diff + 1.96 * se if np.isfinite(se) else np.nan,
                    "T": int(T),
                    "sample": sample,
                    "method": out["method"].iloc[0],
                    "group_label": "diff(10–13) - other",
                    "nobs": int(len(dfm)),
                }
                out = pd.concat([out, pd.DataFrame([diff_row])], ignore_index=True)

    # order rows
    order = ["X_mid_10_13", "X_other", "diff_mid_minus_other"]
    out["__ord"] = out["Term"].map({k: i for i, k in enumerate(order)}).fillna(99)
    out = out.sort_values("__ord").drop(columns="__ord").reset_index(drop=True)
    return out


# =========================================================
# 7. Visualization
# =========================================================

def plot_two_groups(out: pd.DataFrame, save_path: Path):
    if out.empty:
        return

    sub = out[out["Term"].isin(["X_mid_10_13", "X_other"])].copy()
    if sub.empty:
        return

    T = int(sub["T"].iloc[0])
    sample = sub["sample"].iloc[0]

    labels = sub["group_label"].tolist()
    est = sub["Estimate"].to_numpy(float)
    lo  = sub["CI_low"].to_numpy(float)
    hi  = sub["CI_high"].to_numpy(float)
    pv  = sub["PValue"].to_numpy(float)

    yerr = np.vstack([est - lo, hi - est])
    xs = np.arange(len(labels))

    fig, ax = plt.subplots(figsize=(6.8, 4.8))
    ax.axhline(0, linestyle="--", linewidth=1)

    ax.errorbar(xs, est, yerr=yerr, fmt="o", capsize=4)

    y0, y1 = ax.get_ylim()
    offset = 0.06 * (y1 - y0 if y1 > y0 else 1.0)
    for x, b, p in zip(xs, est, pv):
        s = stars_for_p(p)
        if s:
            ax.text(x, b + offset, s, ha="center", va="bottom", fontsize=12)

    # diff p-value in title if available
    diff_row = out[out["Term"] == "diff_mid_minus_other"]
    diff_note = ""
    if not diff_row.empty:
        p_diff = float(diff_row["PValue"].iloc[0])
        diff_note = f" | diff p={p_diff:.3g}"

    ax.set_xticks(xs)
    ax.set_xticklabels(labels)
    ax.set_xlabel("年龄组")
    ax.set_ylabel("系数：该年龄组暴露对 edu_years 的边际影响")
    ax.set_title(
        f"Two-group exposure ({'mean' if USE_MEAN else 'sum'}) | mid=10–13 | T={T} | {sample}{diff_note}"
    )

    plt.tight_layout()
    plt.savefig(save_path, dpi=220)
    plt.close(fig)


# =========================================================
# 8. MAIN (resume)
# =========================================================

def main():
    done = read_done_set(DONE_TXT)
    print(f"[INFO] done items: {len(done)}")

    flood_idx = load_flood_index()
    need_cols = [f"flood_ge_T{t}" for t in T_LIST]
    miss = [c for c in need_cols if c not in flood_idx.columns]
    if miss and REQUIRE_ALL_T:
        raise ValueError("缺少列: " + ", ".join(miss))

    df_base = load_micro_base()

    for T in T_LIST:
        for sample in SAMPLES:
            key = f"two_groups_10_13_{'mean' if USE_MEAN else 'sum'}_T{T}_{sample}"
            if key in done:
                print(f"[SKIP] {key} already done.")
                continue

            print("\n==============================")
            print(f"[RUN] {key}")
            print("==============================")

            try:
                out = run_one(df_base, flood_idx, T=T, sample=sample)
            except Exception as e:
                print(f"[ERROR] {key} failed: {repr(e)}")
                continue

            if out.empty:
                print(f"[WARN] {key} empty output (terms dropped or empty sample).")
                mark_done(DONE_TXT, key)
                done.add(key)
                continue

            safe_append_csv(out, MASTER_CSV)
            print(f"[DONE] appended: {MASTER_CSV}")

            fig_path = OUT_DIR / f"two_groups_10_13_T{T}_{sample}.png"
            plot_two_groups(out, fig_path)
            print(f"[DONE] saved plot: {fig_path}")

            mark_done(DONE_TXT, key)
            done.add(key)
            print(f"[DONE] marked done: {key}")

    print("\n[ALL DONE]")

if __name__ == "__main__":
    main()
