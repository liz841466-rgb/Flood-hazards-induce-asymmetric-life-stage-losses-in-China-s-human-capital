#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 06_five_wave_exploratory_analysis.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 1
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 06_five_wave_exploratory_analysis.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

# =============================================================================
def set_cn_font():
    # Original notebook comment normalized for the public code archive.
    candidates = [
        "Microsoft YaHei", "SimHei", "SimSun", "NSimSun",
        "KaiTi", "FangSong", "Source Han Sans CN", "Noto Sans CJK SC",
        "Arial Unicode MS"
    ]
    installed = {f.name for f in fm.fontManager.ttflist}
    use = [f for f in candidates if f in installed] or ["DejaVu Sans"]
    plt.rcParams["font.sans-serif"] = use
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["axes.unicode_minus"] = False

set_cn_font()

# Original notebook comment normalized for the public code archive.
def safe_sheet(name: str) -> str:
    return re.sub(r'[\[\]\:\*\?\/\\]', '_', str(name))[:31]

def normalize_id_val(x):
    """Archived notebook note for 06_five_wave_exploratory_analysis.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if pd.isna(x):
        return pd.NA
    s = str(x).strip()
    if s.lower() in {"nan", "nat", ""}:
        return pd.NA
    # Original notebook comment normalized for the public code archive.
    s = re.sub(r"\.0+$", "", s)
    # Original notebook comment normalized for the public code archive.
    s = s.replace(" ", "")
    return s if s else pd.NA

# =============================================================================
ROOT = r"E:\project_flood_impact_assessment\教育数据\CHFS_center"
WAVES = [2011, 2013, 2015, 2017, 2019]
FILES = {
    2011: os.path.join(ROOT, "2011", "CHFS2011_教育与收入_户级.xlsx"),
    2013: os.path.join(ROOT, "2013", "CHFS2013_教育与收入_户级.xlsx"),
    2015: os.path.join(ROOT, "2015", "CHFS2015_教育与收入_户级.xlsx"),
    2017: os.path.join(ROOT, "2017", "CHFS2017_教育与收入_户级.xlsx"),
    2019: os.path.join(ROOT, "2019", "CHFS2019_教育与收入_户级.xlsx"),
}
OUTDIR = os.path.join(ROOT, "output")
os.makedirs(OUTDIR, exist_ok=True)

# =============================================================================
def first_nonnull(*vals):
    for v in vals:
        if v is not None and not (isinstance(v, float) and np.isnan(v)):
            if pd.isna(v):
                continue
            return v
    return pd.NA

def standardize_family_id(df, year):
    """Archived notebook note for 06_five_wave_exploratory_analysis.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    cand_cols = [
        "家庭ID", "家庭ID2011", "上一波家庭ID（2013）", "当波家庭ID（2013）",
        "当波家庭ID（2015）", "当波家庭ID（2017）", "当波家庭ID（2019）",
        "备用ID",
        # Original notebook comment normalized for the public code archive.
        "hhid_2011","hhid_2013","hhid_2015","hhid_2017","hhid_2019","hhid"
    ]
    have = [c for c in cand_cols if c in df.columns]
    if not have:
        raise KeyError(f"{year} 无法找到任何ID列，请检查原表。")
    # Original notebook comment normalized for the public code archive.
    fid = pd.Series(pd.NA, index=df.index, dtype="object")
    for c in ["家庭ID","家庭ID2011","hhid_2011","上一波家庭ID（2013）","当波家庭ID（2013）","hhid_2013",
              "当波家庭ID（2015）","hhid_2015","当波家庭ID（2017）","hhid_2017",
              "当波家庭ID（2019）","hhid_2019","备用ID","hhid"]:
        if c in df.columns:
            fid = fid.fillna(df[c].map(normalize_id_val))
    return fid.astype("string")

def find_child_col(df):
    for c in df.columns:
        if "是否有15岁及以下儿童" in str(c):
            return c
    return None

def find_edu_col(df):
    # Original notebook comment normalized for the public code archive.
    for c in df.columns:
        if re.search(r"去年.*教育.*培训.*支出", str(c)):
            return c
    return None

def read_wave(year, path):
    """Archived notebook note for 06_five_wave_exploratory_analysis.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = pd.read_excel(path)

    # Original notebook comment normalized for the public code archive.
    famid = standardize_family_id(df, year)
    df["家庭ID_std"] = famid.map(normalize_id_val)

    # Original notebook comment normalized for the public code archive.
    child_col = find_child_col(df)
    if child_col is not None:
        child = pd.to_numeric(df[child_col], errors="coerce").astype("Int64")
    else:
        child = pd.Series(pd.NA, index=df.index, dtype="Int64")

    # Original notebook comment normalized for the public code archive.
    edu_col = find_edu_col(df)
    edu = pd.to_numeric(df[edu_col], errors="coerce") if edu_col else pd.Series(np.nan, index=df.index)

    out = pd.DataFrame({
        "家庭ID": df["家庭ID_std"],
        "有儿童": child,
        "edu_exp": edu,
        "year": year
    })
    # Original notebook comment normalized for the public code archive.
    out = out.dropna(subset=["家庭ID"]).drop_duplicates(subset=["家庭ID"], keep="first")
    return out

def build_sets(dfs, subset=None):
    """Archived notebook note for 06_five_wave_exploratory_analysis.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    id_sets = {}
    for y, d in dfs.items():
        if subset == 'child':
            s = set(d.loc[d["有儿童"] == 1, "家庭ID"])
        else:
            s = set(d["家庭ID"])
        id_sets[y] = s
    return id_sets

def coverage_metrics(id_sets):
    """Archived notebook note for 06_five_wave_exploratory_analysis.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    years = sorted(id_sets.keys())
    rows, cumulative = [], set()
    for i, y in enumerate(years):
        curr = id_sets[y]
        n = len(curr)
        cumulative |= curr
        cum_n = len(cumulative)
        if i == 0:
            new = n
            lost = np.nan
            retain_rate = np.nan
        else:
            prev = id_sets[years[i-1]]
            new = len(curr - prev)
            lost = len(prev - curr)
            retain_rate = (len(curr & prev) / len(prev)) if len(prev) > 0 else np.nan
        rows.append({
            "year": y,
            "样本量": n,
            "新增(相对上一波)": new,
            "流失(相对上一波)": lost,
            "上一波→本波留存率": retain_rate,
            "累计唯一样本": cum_n
        })
    return pd.DataFrame(rows).set_index("year")

def participation_distribution(id_sets):
    """Archived notebook note for 06_five_wave_exploratory_analysis.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    years = sorted(id_sets.keys())
    all_ids = set().union(*[id_sets[y] for y in years])
    counts = {hid: sum(hid in id_sets[y] for y in years) for hid in all_ids}
    s = pd.Series(counts).value_counts().sort_index()
    # Original notebook comment normalized for the public code archive.
    for k in range(1, len(years)+1):
        if k not in s.index:
            s.loc[k] = 0
    return s.sort_index()

def plot_panels(metrics, part_dist, title, out_png):
    """Archived notebook note for 06_five_wave_exploratory_analysis.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    years = metrics.index.tolist()
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))

    # Original notebook comment normalized for the public code archive.
    ax = axes[0,0]
    ax.bar(years, metrics["样本量"])
    ax.set_title("每波样本量（户）")
    ax.set_xlabel("年份"); ax.set_ylabel("户数")
    ax2 = ax.twinx()
    ax2.plot(years, metrics["累计唯一样本"], marker="o")
    ax2.set_ylabel("累计唯一样本")

    # Original notebook comment normalized for the public code archive.
    ax = axes[0,1]
    x = np.arange(1, len(years))
    width = 0.35
    add_vals = metrics["新增(相对上一波)"].iloc[1:].values
    drop_vals = metrics["流失(相对上一波)"].iloc[1:].values
    ticks = [f"{years[i-1]}→{years[i]}" for i in range(1, len(years))]
    ax.bar(x - width/2, add_vals, width, label="新增")
    ax.bar(x + width/2, drop_vals, width, label="流失")
    ax.set_xticks(x); ax.set_xticklabels(ticks)
    ax.set_title("相邻波 新增/流失（户）"); ax.legend()

    # Original notebook comment normalized for the public code archive.
    ax = axes[1,0]
    ax.plot(years[1:], metrics["上一波→本波留存率"].iloc[1:], marker="o")
    ax.set_ylim(0, 1)
    ax.set_title("上一波→本波留存率"); ax.set_xlabel("年份"); ax.set_ylabel("比例")

    # Original notebook comment normalized for the public code archive.
    ax = axes[1,1]
    k = part_dist.index.tolist()
    ax.bar(k, part_dist.values)
    ax.set_xticks(k); ax.set_xlabel("参与波次数（次）"); ax.set_ylabel("户数")
    five = int(part_dist.get(5, 0))
    ax.set_title(f"参与波次数分布（5波都在：{five} 户）")

    fig.suptitle(title, y=1.02, fontsize=12)
    fig.tight_layout()
    fig.savefig(out_png, dpi=150)
    plt.close(fig)

def build_common_trend(dfs):
    """Archived notebook note for 06_five_wave_exploratory_analysis.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    inter = set(dfs[WAVES[0]]["家庭ID"])
    for y in WAVES[1:]:
        inter &= set(dfs[y]["家庭ID"])
    common_ids = sorted(list(inter))

    wide = pd.DataFrame({"家庭ID": common_ids})
    for y in WAVES:
        col = f"edu_exp_{y}"
        tmp = (dfs[y][["家庭ID","edu_exp"]]
                   .drop_duplicates("家庭ID", keep="first")
                   .set_index("家庭ID")["edu_exp"]
                   .rename(col))
        wide = wide.merge(tmp, left_on="家庭ID", right_index=True, how="left")

    stats = []
    for y in WAVES:
        col = f"edu_exp_{y}"
        vals = pd.to_numeric(wide[col], errors="coerce")
        n = int(vals.notna().sum())
        mean_v   = float(np.nanmean(vals))   if n > 0 else np.nan
        median_v = float(np.nanmedian(vals)) if n > 0 else np.nan
        stats.append({"year": y, "均值": mean_v, "中位数": median_v, "N": n})
    stat_df = pd.DataFrame(stats).set_index("year")
    return wide, stat_df

# =============================================================================
dfs = {y: read_wave(y, FILES[y]) for y in WAVES}

# =============================================================================
id_sets_all = build_sets(dfs, subset=None)
metrics_all = coverage_metrics(id_sets_all)
part_all = participation_distribution(id_sets_all)

# Original notebook comment normalized for the public code archive.
out_matrix_all = os.path.join(OUTDIR, "CHFS_覆盖度留存_家庭.xlsx")
with pd.ExcelWriter(out_matrix_all, engine="xlsxwriter") as w:
    metrics_all.to_excel(w, sheet_name=safe_sheet("指标矩阵"))
    part_all.rename("户数").to_excel(w, sheet_name=safe_sheet("参与次数分布"))
print("[INFO] Notebook progress message.")

# Original notebook comment normalized for the public code archive.
png_all = os.path.join(OUTDIR, "CHFS_覆盖度留存_家庭.png")
plot_panels(metrics_all, part_all, "CHFS（家庭）覆盖度/留存概览（全体样本）", png_all)
print("[INFO] Notebook progress message.")

# =============================================================================
id_sets_child = build_sets(dfs, subset='child')
metrics_child = coverage_metrics(id_sets_child)
part_child = participation_distribution(id_sets_child)

out_matrix_child = os.path.join(OUTDIR, "CHFS_覆盖度留存_家庭_有儿童.xlsx")
with pd.ExcelWriter(out_matrix_child, engine="xlsxwriter") as w:
    metrics_child.to_excel(w, sheet_name=safe_sheet("指标矩阵"))
    part_child.rename("户数").to_excel(w, sheet_name=safe_sheet("参与次数分布"))
print("[INFO] Notebook progress message.")

png_child = os.path.join(OUTDIR, "CHFS_覆盖度留存_家庭_有儿童.png")
plot_panels(metrics_child, part_child, "CHFS（家庭）覆盖度/留存概览（仅有≤15岁儿童的家庭）", png_child)
print("[INFO] Notebook progress message.")

# =============================================================================
wide_common, trend_stats = build_common_trend(dfs)

# Original notebook comment normalized for the public code archive.
fig = plt.figure(figsize=(6,4))
plt.plot(trend_stats.index, trend_stats["均值"], marker="o", label="均值")
plt.plot(trend_stats.index, trend_stats["中位数"], marker="o", label="中位数")
plt.xlabel("年份"); plt.ylabel("去年教育培训支出（元）")
plt.title(f"五波共同样本 教育培训支出趋势（N={int(trend_stats['N'].min())}）")
plt.legend()
png_trend = os.path.join(OUTDIR, "CHFS_共同样本_教育培训支出趋势.png")
plt.tight_layout()
plt.savefig(png_trend, dpi=150); plt.close()
print("[INFO] Notebook progress message.")

# Original notebook comment normalized for the public code archive.
wide_path = os.path.join(OUTDIR, "CHFS_共同样本_教育培训支出宽表.xlsx")
with pd.ExcelWriter(wide_path, engine="xlsxwriter") as w:
    wide_common.to_excel(w, index=False, sheet_name=safe_sheet("宽表（户x年份）"))
    trend_stats.to_excel(w, sheet_name=safe_sheet("统计_均值_中位数"))
print("[INFO] Notebook progress message.")


# ------------------------------------------------------------------------------
# Notebook cell 3
# ------------------------------------------------------------------------------
# =============================================================================
import os, re, numpy as np, pandas as pd
import matplotlib.pyplot as plt

def safe_sheet(name: str) -> str:
    return re.sub(r'[\[\]\:\*\?\/\\]', '_', str(name))[:31]

# =============================================================================
present_sets = {y: set(dfs[y]["家庭ID"]) for y in WAVES}
all_ids = set().union(*present_sets.values())
eligible_ids = sorted([hid for hid in all_ids
                       if sum(hid in present_sets[y] for y in WAVES) >= 4])

# =============================================================================
wide4 = pd.DataFrame({"家庭ID": eligible_ids})
for y in WAVES:
    tmp = (dfs[y][["家庭ID", "edu_exp"]]
             .drop_duplicates("家庭ID", keep="first")
             .rename(columns={"edu_exp": f"edu_exp_{y}"}))
    wide4 = wide4.merge(tmp, on="家庭ID", how="left")

# Original notebook comment normalized for the public code archive.
stats4 = []
for y in WAVES:
    col = f"edu_exp_{y}"
    vals = pd.to_numeric(wide4[col], errors="coerce")
    n = int(vals.notna().sum())
    mean_v   = float(np.nanmean(vals))   if n > 0 else np.nan
    median_v = float(np.nanmedian(vals)) if n > 0 else np.nan
    stats4.append({"year": y, "均值": mean_v, "中位数": median_v, "N": n})
trend_stats4 = pd.DataFrame(stats4).set_index("year")

# Original notebook comment normalized for the public code archive.
wide_path = os.path.join(OUTDIR, "CHFS_共同样本_教育培训支出宽表.xlsx")
with pd.ExcelWriter(wide_path, engine="xlsxwriter") as w:
    wide4.to_excel(w, index=False, sheet_name=safe_sheet("宽表（≥4波）"))
    trend_stats4.to_excel(w, sheet_name=safe_sheet("统计_均值_中位数"))
print("[INFO] Notebook progress message.")

# Original notebook comment normalized for the public code archive.
plt.figure(figsize=(6,4))
plt.plot(trend_stats4.index, trend_stats4["均值"], marker="o", label="均值")
plt.plot(trend_stats4.index, trend_stats4["中位数"], marker="o", label="中位数")
plt.xlabel("年份"); plt.ylabel("去年教育培训支出（元）")
plt.title("≥4波共同样本 教育培训支出趋势")
plt.legend()
png_trend = os.path.join(OUTDIR, "CHFS_共同样本_教育培训支出趋势.png")
plt.tight_layout(); plt.savefig(png_trend, dpi=150); plt.close()
print("[INFO] Notebook progress message.")

# =============================================================================
# Original notebook comment normalized for the public code archive.
stats4_child = []
for y in WAVES:
    # Original notebook comment normalized for the public code archive.
    ids_child_y = set(dfs[y].loc[dfs[y]["有儿童"] == 1, "家庭ID"])
    use_ids = set(eligible_ids) & ids_child_y
    # Original notebook comment normalized for the public code archive.
    tmp = dfs[y].loc[dfs[y]["家庭ID"].isin(use_ids), ["家庭ID", "edu_exp"]]
    vals = pd.to_numeric(tmp["edu_exp"], errors="coerce")
    n = int(vals.notna().sum())
    mean_v   = float(np.nanmean(vals))   if n > 0 else np.nan
    median_v = float(np.nanmedian(vals)) if n > 0 else np.nan
    stats4_child.append({"year": y, "均值": mean_v, "中位数": median_v, "N": n})

trend_child = pd.DataFrame(stats4_child).set_index("year")

# Original notebook comment normalized for the public code archive.
plt.figure(figsize=(6,4))
plt.plot(trend_child.index, trend_child["均值"], marker="o", label="均值")
plt.plot(trend_child.index, trend_child["中位数"], marker="o", label="中位数")
plt.xlabel("年份"); plt.ylabel("去年教育培训支出（元）")
plt.title("（有≤15岁儿童）≥4波共同样本 教育培训支出趋势")
plt.legend()
png_trend_child = os.path.join(OUTDIR, "CHFS_共同样本_教育培训支出趋势_有儿童.png")
plt.tight_layout(); plt.savefig(png_trend_child, dpi=150); plt.close()
print("[INFO] Notebook progress message.")


# ------------------------------------------------------------------------------
# Notebook cell 5
# ------------------------------------------------------------------------------
# =============================================================================
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
def set_cn_font():
    candidates = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "NSimSun"]
    installed = {f.name for f in fm.fontManager.ttflist}
    use = [f for f in candidates if f in installed] or ["DejaVu Sans"]
    plt.rcParams["font.sans-serif"] = use
    plt.rcParams["axes.unicode_minus"] = False
set_cn_font()

# =============================================================================
# CHFS/CFHS processing note.
# WAVES = [2011, 2013, 2015, 2017, 2019]
# FILES = {
# CHFS/CFHS processing note.
# CHFS/CFHS processing note.
# CHFS/CFHS processing note.
# CHFS/CFHS processing note.
# CHFS/CFHS processing note.
# }
# OUTDIR = os.path.join(ROOT, "output"); os.makedirs(OUTDIR, exist_ok=True)

import re, os, numpy as np, pandas as pd

def safe_sheet(name: str) -> str:
    return re.sub(r'[\[\]\:\*\?\/\\]', '_', str(name))[:31]

def _find_col(cols, keywords):
    """Archived notebook note for 06_five_wave_exploratory_analysis.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    cols_str = [str(c) for c in cols]
    for kw in keywords:
        for c in cols_str:
            if kw in c:
                return c
    return None

def read_income_wave(year, path):
    """Archived notebook note for 06_five_wave_exploratory_analysis.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = pd.read_excel(path)
    if "家庭ID" not in df.columns:
        raise KeyError(f"{year} 缺少列：家庭ID")
    df["家庭ID"] = df["家庭ID"].astype(str).str.strip()

    # Original notebook comment normalized for the public code archive.
    child_col = _find_col(df.columns, ["是否有15岁及以下儿童"])
    if child_col is not None:
        child = pd.to_numeric(df[child_col], errors="coerce").astype("Int64")
    else:
        child = pd.Series(pd.NA, index=df.index, dtype="Int64")

    # Original notebook comment normalized for the public code archive.
    inc_col = _find_col(df.columns, ["可支配收入", "总收入", "total_income", "hh_income"])
    if inc_col is None:
        # Original notebook comment normalized for the public code archive.
        inc_col = next((c for c in df.columns if re.search(r"家庭.*(可支配|总).*收入", str(c))), None)
    inc = pd.to_numeric(df[inc_col], errors="coerce") if inc_col else pd.Series(np.nan, index=df.index)

    out = pd.DataFrame({
        "家庭ID": df["家庭ID"],
        "有儿童": child,
        "income": inc
    })
    out["year"] = year
    return out

# Original notebook comment normalized for the public code archive.
inc_dfs = {y: read_income_wave(y, FILES[y]) for y in WAVES}

# Original notebook comment normalized for the public code archive.
present_sets = {y: set(inc_dfs[y]["家庭ID"]) for y in WAVES}
all_ids = set().union(*present_sets.values())
eligible_ids_4_inc = sorted([hid for hid in all_ids
                             if sum(hid in present_sets[y] for y in WAVES) >= 4])

# Original notebook comment normalized for the public code archive.
wide4_inc = pd.DataFrame({"家庭ID": eligible_ids_4_inc})
for y in WAVES:
    tmp = (inc_dfs[y][["家庭ID", "income"]]
             .drop_duplicates(subset="家庭ID", keep="first")
             .rename(columns={"income": f"inc_{y}"}))
    wide4_inc = wide4_inc.merge(tmp, on="家庭ID", how="left")

# Original notebook comment normalized for the public code archive.
stats_inc_all = []
for y in WAVES:
    col = f"inc_{y}"
    vals = pd.to_numeric(wide4_inc[col], errors="coerce")
    n = int(vals.notna().sum())
    mean_v   = float(np.nanmean(vals))   if n > 0 else np.nan
    median_v = float(np.nanmedian(vals)) if n > 0 else np.nan
    stats_inc_all.append({"year": y, "均值": mean_v, "中位数": median_v, "N": n})
trend_inc_all = pd.DataFrame(stats_inc_all).set_index("year")

# Original notebook comment normalized for the public code archive.
stats_inc_child = []
for y in WAVES:
    ids_child_y = set(inc_dfs[y].loc[inc_dfs[y]["有儿童"] == 1, "家庭ID"])
    use_ids = set(eligible_ids_4_inc) & ids_child_y
    vals = pd.to_numeric(
        inc_dfs[y].loc[inc_dfs[y]["家庭ID"].isin(use_ids), "income"],
        errors="coerce"
    )
    n = int(vals.notna().sum())
    mean_v   = float(np.nanmean(vals))   if n > 0 else np.nan
    median_v = float(np.nanmedian(vals)) if n > 0 else np.nan
    stats_inc_child.append({"year": y, "均值": mean_v, "中位数": median_v, "N": n})
trend_inc_child = pd.DataFrame(stats_inc_child).set_index("year")

# Original notebook comment normalized for the public code archive.
xlsx_inc = os.path.join(OUTDIR, "CHFS_共同样本_可支配收入宽表.xlsx")
with pd.ExcelWriter(xlsx_inc, engine="xlsxwriter") as w:
    wide4_inc.to_excel(w, index=False, sheet_name=safe_sheet("宽表（≥4波）"))
    trend_inc_all.to_excel(w, sheet_name=safe_sheet("统计_全体"))
    trend_inc_child.to_excel(w, sheet_name=safe_sheet("统计_有儿童"))
print("[INFO] Notebook progress message.")

# Original notebook comment normalized for the public code archive.
plt.figure(figsize=(6,4))
plt.plot(trend_inc_all.index, trend_inc_all["均值"], marker="o", label="均值")
plt.plot(trend_inc_all.index, trend_inc_all["中位数"], marker="o", label="中位数")
plt.xlabel("年份"); plt.ylabel("家庭可支配收入（元）")
plt.title(f"≥4波共同样本 家庭可支配收入趋势（全体；最小N={int(trend_inc_all['N'].min())}）")
plt.legend()
png_inc_all = os.path.join(OUTDIR, "CHFS_共同样本_可支配收入趋势.png")
plt.tight_layout(); plt.savefig(png_inc_all, dpi=150); plt.close()
print("[INFO] Notebook progress message.")

# Original notebook comment normalized for the public code archive.
plt.figure(figsize=(6,4))
plt.plot(trend_inc_child.index, trend_inc_child["均值"], marker="o", label="均值")
plt.plot(trend_inc_child.index, trend_inc_child["中位数"], marker="o", label="中位数")
plt.xlabel("年份"); plt.ylabel("家庭可支配收入（元）")
plt.title(f"（有≤15岁儿童）≥4波共同样本 家庭可支配收入趋势（最小N={int(trend_inc_child['N'].min())}）")
plt.legend()
png_inc_child = os.path.join(OUTDIR, "CHFS_共同样本_可支配收入趋势_有儿童.png")
plt.tight_layout(); plt.savefig(png_inc_child, dpi=150); plt.close()
print("[INFO] Notebook progress message.")
