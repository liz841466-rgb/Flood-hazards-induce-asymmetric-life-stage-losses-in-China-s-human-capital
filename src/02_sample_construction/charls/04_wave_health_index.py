#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 04_wave_health_index.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""



# =============================================================================
# Source notebook
# =============================================================================
# record_type : wave_step
# year        : 2011
# step        : 4
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 04_wave_health_index.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 7
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 04_wave_health_index.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Tuple
import math

# ---------------- Paths ----------------
DATA_DIR = Path(r"E:\impact_assessment_child_order\older\health\2011")
INPUT_DTA  = DATA_DIR / "2011_health_result.dta"
INPUT_XLSX = DATA_DIR / "2011_health_result.xlsx"
OUT_XLSX   = DATA_DIR / "health_index_entropy.xlsx"
OUT_DTA    = DATA_DIR / "health_index_entropy.dta"
OUT_CHI    = DATA_DIR / "2011_综合健康指数.xlsx"
OUT_ELIM   = DATA_DIR / "eliminate_entropy_missing_half.xlsx"

DATA_DIR.mkdir(parents=True, exist_ok=True)

# -------------- Helpers --------------
def _clean_to_str(s: pd.Series) -> pd.Series:
    s = pd.Series(s, dtype="object"); m = s.isna()
    sc = s[~m].astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = sc; s.loc[m] = np.nan; return s

def canon_id_fixed(s: pd.Series, width: int) -> pd.Series:
    s = _clean_to_str(s); m = s.notna(); s.loc[m] = s.loc[m].astype(str).str.zfill(width); return s

def _digits_width(s: pd.Series, width: int) -> pd.Series:
    t = _clean_to_str(s).str.replace(r"\D", "", regex=True)
    t = t.where(t.str.len() > 0, np.nan)
    return t.where(t.isna(), t.str[-width:].str.zfill(width)).astype("object")

def ensure_ids_2011(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 04_wave_health_index.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    d = df.copy()
    if "householdID" in d.columns: d["householdID"] = canon_id_fixed(d["householdID"], 9)
    if "communityID" in d.columns: d["communityID"] = canon_id_fixed(d["communityID"], 7)
    if "ID" in d.columns:          d["ID"]          = canon_id_fixed(d["ID"], 11)

    if "householdID10" not in d.columns or d["householdID10"].isna().all():
        hh9  = _digits_width(d["householdID"], 9) if "householdID" in d.columns else pd.Series(np.nan, index=d.index)
        d["householdID10"] = hh9.where(hh9.isna(), hh9 + "0")
    else:
        d["householdID10"] = _digits_width(d["householdID10"], 10)

    if "ID12" not in d.columns or d["ID12"].isna().all():
        id11 = _digits_width(d["ID"], 11) if "ID" in d.columns else pd.Series(np.nan, index=d.index)
        pn2  = id11.str[-2:]
        d["ID12"] = np.where(d["householdID10"].notna() & pn2.notna(), d["householdID10"] + pn2, np.nan).astype("object")
    else:
        d["ID12"] = _digits_width(d["ID12"], 12)
    return d

def minmax01(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce"); vmin, vmax = s.min(), s.max()
    if pd.isna(vmin) or pd.isna(vmax) or vmax == vmin: return pd.Series(np.nan, index=s.index)
    return (s - vmin) / (vmax - vmin)

def entropy_weights(X: pd.DataFrame):
    X = X.apply(lambda s: s.fillna(s.median()), axis=0)
    var = X.var(skipna=True); keep = var[var > 0].index.tolist(); X = X[keep]
    if X.shape[1] == 0: return pd.Series(dtype=float), X
    P = X / X.sum(axis=0); P = P.replace([0, np.inf, -np.inf], 1e-12)
    n = X.shape[0]; k = 1.0 / np.log(n)
    E = -k * (P * np.log(P)).sum(axis=0); D = 1 - E
    W = (pd.Series(np.ones(len(D)) / len(D), index=D.index) if np.isclose(D.sum(), 0) else D / D.sum())
    return W, X

def prepare_series(col: str, s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce").replace({88: np.nan, 99: np.nan})
    if col in {"disease","mental_neuro_psych","memory_disease","social_activity"}:
        return s.where(s.isin([1,2]), np.nan)
    if col in {"depress","effort","hope","fear","sleep","happy","hopeless"}:
        return s.where(s.isin([1,2,3,4]), np.nan)
    if col == "life_satisfaction": return s.where(s.isin([1,2,3,4,5]), np.nan)
    if col == "srh":               return s.where(s.isin([1,2,3,4,5]), np.nan)
    if col in {"meet_child_freq","call_child_freq"}:
        return s.where(s.isin(list(range(1,11))), np.nan)
    if col == "social_freq":
        s = s.where(s.isin([0,1,2,3]), np.nan)
        return s.map({0:4, 1:1, 2:2, 3:3})  # Original notebook comment normalized for the public code archive.
    return s

def build_index(df: pd.DataFrame, indicators: Dict[str, bool], label: str):
    X = pd.DataFrame(index=df.index); used, dropped = [], []
    for col, higher_is_better in indicators.items():
        if col not in df.columns: dropped.append(col); continue
        s = prepare_series(col, df[col])
        oriented = s if higher_is_better else ((s.max(skipna=True) - s) if pd.notna(s.max(skipna=True)) else s*np.nan)
        X[col] = minmax01(oriented); used.append(col)
    if X.shape[1] == 0:
        return (pd.Series(np.nan, index=df.index, name=label), pd.Series(dtype=float), used, dropped)
    w, Xn = entropy_weights(X)
    if len(w) == 0:
        return (pd.Series(np.nan, index=df.index, name=label), w, used, dropped)
    score = (Xn[w.index] * w).sum(axis=1); score.name = label; return score, w, used, dropped

def block_index(df, blocks: Dict[str, Dict[str,bool]], label: str):
    sub_scores, ind_weights, diag = {}, {}, []
    for sub_name, sub_ind in blocks.items():
        s, w, used, dropped = build_index(df, sub_ind, f"{label}-{sub_name}")
        sub_scores[sub_name] = s; ind_weights[sub_name] = w
        diag.append([label, sub_name, "; ".join(used) if used else "(none)", "; ".join(dropped) if dropped else ""])
    X = pd.DataFrame(sub_scores)
    if X.dropna(how="all").empty:
        return (pd.Series(np.nan, index=df.index, name=label), ind_weights, pd.Series(dtype=float),
                pd.DataFrame(diag, columns=["维度","子维度","使用了哪些列","缺失/未匹配"]))
    X = X.apply(lambda s: s.fillna(s.median()), axis=0)
    w_block, Xn = entropy_weights(X)
    total = (Xn[w_block.index] * w_block).sum(axis=1); total.name = label
    return total, ind_weights, w_block, pd.DataFrame(diag, columns=["维度","子维度","使用了哪些列","缺失/未匹配"])

def to_0_100(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce"); vmin, vmax = s.min(), s.max()
    if pd.isna(vmin) or pd.isna(vmax) or vmax == vmin: return pd.Series(np.nan, index=s.index)
    return (s - vmin) / (vmax - vmin) * 100.0

def weights_table(w_detail: Dict[str, pd.Series]) -> pd.DataFrame:
    rows = []
    for sub, w in w_detail.items():
        if w is None or len(w) == 0: rows.append((sub, "(no-use-or-constant)", np.nan))
        else:
            for k,v in w.items(): rows.append((sub, k, v))
    return pd.DataFrame(rows, columns=["子维度","指标","熵权权重"])

# -------------- Read data --------------
try:
    df0 = pd.read_stata(INPUT_DTA, convert_categoricals=False); print("Read:", INPUT_DTA)
except Exception as e:
    print("Read .dta failed, fallback to .xlsx:", e)
    df0 = pd.read_excel(INPUT_XLSX); print("Read:", INPUT_XLSX)

# Original notebook comment normalized for the public code archive.
df0 = ensure_ids_2011(df0)

# =============================================================================
ALL_33 = [
    "srh","disease","mental_neuro_psych","memory_disease","social_activity","social_freq",
    "meet_child_freq","call_child_freq","annual_transfer",
    "run1km","walk1km","walk100m","sit_to_stand","stairs","bend_kneel_squat","arm_raise","lift5kg","pick_coin",
    "dress","bathe","eat","bed_chair_transfer","toilet","incontinence","housework",
    "depress","effort","hope","fear","sleep","happy","hopeless","life_satisfaction"
]

# Original notebook comment normalized for the public code archive.
avail_cols = [c for c in ALL_33 if c in df0.columns]
clean_mat = pd.DataFrame({c: prepare_series(c, df0[c]) for c in avail_cols})
miss_cnt  = clean_mat.isna().sum(axis=1)
threshold = math.ceil(len(avail_cols) / 2)  # 33 -> 17
drop_mask = miss_cnt >= threshold
n_drop    = int(drop_mask.sum())
print("[INFO] Notebook progress message.")

# Original notebook comment normalized for the public code archive.
if n_drop > 0:
    id_cols = [c for c in ["ID12","householdID10","ID","householdID","communityID"] if c in df0.columns]  # Original notebook comment normalized for the public code archive.
    elim = df0.loc[drop_mask, id_cols].copy()
    elim["missing_count_33"] = miss_cnt[drop_mask].values
    elim["missing_rate"] = elim["missing_count_33"] / float(len(avail_cols))
    elim.to_excel(OUT_ELIM, index=False)
    print("Eliminate list ->", OUT_ELIM)

# Original notebook comment normalized for the public code archive.
df = df0.loc[~drop_mask].reset_index(drop=True).copy()

# =============================================================================
ADL   = {c: False for c in ["dress","bathe","eat","bed_chair_transfer","toilet","incontinence","housework"]}
FUNC  = {c: False for c in ["run1km","walk1km","walk100m","sit_to_stand","stairs","bend_kneel_squat","arm_raise","lift5kg","pick_coin"]}
DIS   = {"disease": True}

PSY_SYM   = {"depress": False, "effort": False, "hope": True, "fear": False, "sleep": False, "happy": True, "hopeless": False}
SUBJ      = {"life_satisfaction": False, "srh": False}
PSY_CHRON = {"mental_neuro_psych": True, "memory_disease": True}

SOC_PART = {"social_activity": False, "social_freq": False}
INTERGEN = {"meet_child_freq": False, "call_child_freq": False}
SOC_LIFE = {"life_satisfaction": False, "depress": False}

# =============================================================================
def entropy_layer(df, blocks, label):
    return block_index(df, blocks, label)

body_idx,  body_w_detail,  body_w_block,  diag_body  = entropy_layer(df, {"日常活动": ADL, "身体功能": FUNC, "疾病": DIS}, label="身体健康")
mental_idx, mental_w_detail, mental_w_block, diag_mental = entropy_layer(df, {"心理症状": PSY_SYM, "主观评估": SUBJ, "慢病": PSY_CHRON}, label="心理健康")
social_idx, social_w_detail, social_w_block, diag_social = entropy_layer(df, {"社会参与": SOC_PART, "代际联系": INTERGEN, "生活满意度与抑郁": SOC_LIFE}, label="社会适应")

diag_all = pd.concat([diag_body, diag_mental, diag_social], ignore_index=True)

# Original notebook comment normalized for the public code archive.
topX = pd.DataFrame({"身体健康": body_idx, "心理健康": mental_idx, "社会适应": social_idx})
if topX.dropna(how="all").empty:
    top_w = pd.Series(dtype=float)
    overall = pd.Series(np.nan, index=df.index, name="综合健康指数(熵权)")
else:
    topX = topX.apply(lambda s: s.fillna(s.median()), axis=0)
    top_w, topXn = entropy_weights(topX)
    overall = (topXn[top_w.index] * top_w).sum(axis=1)
    overall.name = "综合健康指数(熵权)"

# =============================================================================
out = df.copy()
out["身体健康"] = body_idx
out["心理健康"] = mental_idx
out["社会适应"] = social_idx
out["综合健康指数(熵权)"] = overall
out["身体健康(0-100)"]     = to_0_100(out["身体健康"])
out["心理健康(0-100)"]     = to_0_100(out["心理健康"])
out["社会适应(0-100)"]     = to_0_100(out["社会适应"])
out["综合健康指数(0-100)"] = to_0_100(out["综合健康指数(熵权)"])

tab_body   = weights_table(body_w_detail)
tab_mental = weights_table(mental_w_detail)
tab_social = weights_table(social_w_detail)

with pd.ExcelWriter(OUT_XLSX, engine="xlsxwriter") as writer:
    out.to_excel(writer, index=False, sheet_name="indices")
    pd.DataFrame({"维度": top_w.index, "熵权权重": top_w.values}).to_excel(writer, index=False, sheet_name="weights_top3")
    tab_body.to_excel(writer, index=False, sheet_name="weights_body")
    pd.DataFrame({"子维度": body_w_block.index, "权重": body_w_block.values}).to_excel(writer, index=False, sheet_name="weights_body_blocks")
    tab_mental.to_excel(writer, index=False, sheet_name="weights_mental")
    pd.DataFrame({"子维度": mental_w_block.index, "权重": mental_w_block.values}).to_excel(writer, index=False, sheet_name="weights_mental_blocks")
    tab_social.to_excel(writer, index=False, sheet_name="weights_social")
    pd.DataFrame({"子维度": social_w_block.index, "权重": social_w_block.values}).to_excel(writer, index=False, sheet_name="weights_social_blocks")
    diag_all.to_excel(writer, index=False, sheet_name="diagnostics")
print("Excel ->", OUT_XLSX)

# Original notebook comment normalized for the public code archive.
id_cols = [c for c in ["ID12","householdID10","ID","householdID","communityID"] if c in out.columns]
dta_map = {
    "身体健康": "body_index",
    "心理健康": "mental_index",
    "社会适应": "social_index",
    "综合健康指数(熵权)": "overall_index_ewm",
    "身体健康(0-100)": "body_index_0_100",
    "心理健康(0-100)": "mental_index_0_100",
    "社会适应(0-100)": "social_index_0_100",
    "综合健康指数(0-100)": "overall_index_0_100",
}
dta_cols = id_cols + [k for k in dta_map if k in out.columns]
out_dta = out[dta_cols].rename(columns=dta_map)
out_dta.to_stata(OUT_DTA, write_index=False)
print("Stata  ->", OUT_DTA)

# Excel output note.
chi_cols = [c for c in ["ID12","householdID10","ID","householdID","communityID"] if c in out.columns] + \
           ["身体健康(0-100)","心理健康(0-100)","社会适应(0-100)","综合健康指数(0-100)"]
missing = [c for c in ["身体健康(0-100)","心理健康(0-100)","社会适应(0-100)","综合健康指数(0-100)"] if c not in out.columns]
if missing: raise KeyError(f"缺少导出所需列：{missing}")
out[chi_cols].to_excel(OUT_CHI, index=False)
print("CHI   ->", OUT_CHI)

print("\nTop-level weights:"); print(top_w)


# ------------------------------------------------------------------------------
# Notebook cell 12
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 04_wave_health_index.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import math
import numpy as np
import pandas as pd

# =============================================================================
YEAR = 2011  # Original notebook comment normalized for the public code archive.

BASE = Path(r"E:\impact_assessment_child_order\older\health") / str(YEAR)
INPUT_DTA  = BASE / f"{YEAR}_health_result.dta"
INPUT_XLSX = BASE / f"{YEAR}_health_result.xlsx"
OUT_XLSX   = BASE / f"{YEAR}_health_index_panel_fixed.xlsx"
OUT_DTA    = BASE / f"{YEAR}_health_index_panel_fixed.dta"
OUT_ELIM   = BASE / f"{YEAR}_health_index_panel_drop_missing_half.xlsx"

# Original notebook comment normalized for the public code archive.
STRICT_CHECK = False

# Original notebook comment normalized for the public code archive.
USE_COMMON_ITEMS_ONLY = True

# =============================================================================
def _clean_to_str(s: pd.Series) -> pd.Series:
    s = pd.Series(s, dtype="object")
    m = s.isna()
    sc = s[~m].astype(str).str.strip()
    sc = sc.str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    sc = sc.str.replace(r"\s+", "", regex=True)
    s.loc[~m] = sc
    s.loc[m] = np.nan
    return s

def canon_id_fixed(s: pd.Series, width: int) -> pd.Series:
    s = _clean_to_str(s)
    m = s.notna()
    s.loc[m] = s.loc[m].astype(str).str.zfill(width)
    return s

# =============================================================================
# Original notebook comment normalized for the public code archive.
PANEL_ITEMS = [
    "srh","disease","mental_neuro_psych","memory_disease","social_activity","social_freq",
    "meet_child_freq","call_child_freq",
    # Fixed-effects regression helper.
    "run1km","walk1km","walk100m","sit_to_stand","stairs","bend_kneel_squat","arm_raise","lift5kg","pick_coin",
    "dress","bathe","eat","bed_chair_transfer","toilet","incontinence","housework",
    "depress","effort","hope","fear","sleep","happy","hopeless","life_satisfaction",
]

BODY_VARS = [
    "run1km","walk1km","walk100m","sit_to_stand","stairs",
    "bend_kneel_squat","arm_raise","lift5kg","pick_coin",
    "dress","bathe","eat","bed_chair_transfer","toilet","incontinence","housework",
    "disease",
]

MENTAL_VARS = [
    "mental_neuro_psych","memory_disease",
    "depress","effort","hope","fear","sleep","happy","hopeless",
    "life_satisfaction","srh",
]

SOCIAL_VARS = [
    "social_activity","social_freq","meet_child_freq","call_child_freq",
]

MENTAL_4LV = ["depress","effort","hope","fear","sleep","happy","hopeless"]

# Original notebook comment normalized for the public code archive.
HIGHER_IS_BETTER = {
    # Original notebook comment normalized for the public code archive.
    "run1km": False, "walk1km": False, "walk100m": False,
    "sit_to_stand": False, "stairs": False, "bend_kneel_squat": False,
    "arm_raise": False, "lift5kg": False, "pick_coin": False,
    "dress": False, "bathe": False, "eat": False, "bed_chair_transfer": False,
    "toilet": False, "incontinence": False, "housework": False,
    # Original notebook comment normalized for the public code archive.
    "disease": True,
    "mental_neuro_psych": True,
    "memory_disease": True,
    # Original notebook comment normalized for the public code archive.
    "social_activity": False,
    # Original notebook comment normalized for the public code archive.
    "social_freq": False,
    # Original notebook comment normalized for the public code archive.
    "meet_child_freq": False,
    "call_child_freq": False,
    # Original notebook comment normalized for the public code archive.
    "depress": False,
    "effort": False,
    "hope": True,
    "fear": False,
    "sleep": False,
    "happy": True,
    "hopeless": False,
    # Original notebook comment normalized for the public code archive.
    "life_satisfaction": False,
    "srh": False,
}

def theoretical_range(col: str, year: int):
    """Archived notebook note for 04_wave_health_index.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if col in BODY_VARS:
        return 1, 4
    if col in {"disease","mental_neuro_psych","memory_disease","social_activity"}:
        return 1, 2
    if col in MENTAL_4LV:
        return 1, 4
    if col in {"life_satisfaction","srh"}:
        return 1, 5
    if col == "social_freq":
        # Original notebook comment normalized for the public code archive.
        return 1, 4
    if col in {"meet_child_freq","call_child_freq"}:
        # Original notebook comment normalized for the public code archive.
        if year >= 2015:
            return 1, 16
        else:
            return 1, 10
    # Original notebook comment normalized for the public code archive.
    return None, None

def clean_item(col: str, s: pd.Series, year: int) -> pd.Series:
    """Archived notebook note for 04_wave_health_index.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    # Original notebook comment normalized for the public code archive.
    if col in {"meet_child_freq","call_child_freq"}:
        x = pd.to_numeric(s, errors="coerce").replace({88: np.nan, 99: np.nan})
        if year >= 2015:
            # Original notebook comment normalized for the public code archive.
            x = x.where(x.isin(range(1,17)), np.nan)
            x = x.where(x != 9, np.nan)
        else:
            # 1..10
            x = x.where(x.isin(range(1,11)), np.nan)
        return x

    x = pd.to_numeric(s, errors="coerce").replace({88: np.nan, 99: np.nan})

    if col in {"disease","mental_neuro_psych","memory_disease","social_activity"}:
        return x.where(x.isin([1,2]), np.nan)

    if col in MENTAL_4LV:
        return x.where(x.isin([1,2,3,4]), np.nan)

    if col in {"life_satisfaction","srh"}:
        return x.where(x.isin([1,2,3,4,5]), np.nan)

    if col == "social_freq":
        # Original notebook comment normalized for the public code archive.
        x = x.where(x.isin([0,1,2,3]), np.nan)
        x = x.map({0:4, 1:1, 2:2, 3:3})
        return x

    if col in BODY_VARS:
        # Original notebook comment normalized for the public code archive.
        return x.where(x.isin([1,2,3,4]), np.nan)

    # Original notebook comment normalized for the public code archive.
    return x

def to_01(col: str, s: pd.Series, year: int) -> pd.Series:
    """Archived notebook note for 04_wave_health_index.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    vmin, vmax = theoretical_range(col, year)
    if vmin is None or vmax is None:
        return pd.Series(np.nan, index=s.index)

    x = clean_item(col, s, year)
    hi = HIGHER_IS_BETTER.get(col, True)

    if hi:
        score = (x - vmin) / (vmax - vmin)
    else:
        score = (vmax - x) / (vmax - vmin)

    score = score.clip(lower=0.0, upper=1.0)
    return score

# =============================================================================
try:
    df0 = pd.read_stata(INPUT_DTA, convert_categoricals=False)
    print("Read:", INPUT_DTA)
except Exception as e:
    print("Read .dta failed, fallback to .xlsx:", e)
    df0 = pd.read_excel(INPUT_XLSX)
    print("Read:", INPUT_XLSX)

# Original notebook comment normalized for the public code archive.
for key, width in (("householdID",9), ("communityID",7), ("ID",11)):
    if key in df0.columns:
        df0[key] = canon_id_fixed(df0[key], width)

# Original notebook comment normalized for the public code archive.
avail_items = [c for c in PANEL_ITEMS if c in df0.columns]

if USE_COMMON_ITEMS_ONLY:
    # Original notebook comment normalized for the public code archive.
    COMMON_11_18 = [
        "srh","disease","social_activity","social_freq",
        "meet_child_freq","call_child_freq",
        "run1km","walk1km","walk100m","sit_to_stand","stairs",
        "bend_kneel_squat","arm_raise","lift5kg","pick_coin",
        "dress","bathe","eat","bed_chair_transfer","toilet","incontinence","housework",
        "depress","effort","hope","fear","sleep","happy","hopeless","life_satisfaction",
        "mental_neuro_psych","memory_disease",
    ]
    avail_items = [c for c in avail_items if c in COMMON_11_18]

if STRICT_CHECK:
    miss = [c for c in PANEL_ITEMS if c not in df0.columns]
    if miss:
        raise KeyError(f"{YEAR} 缺少以下健康指标列（健康结果文件可能不是最新版）：{miss}")
else:
    miss_panel = [c for c in PANEL_ITEMS if c not in df0.columns]
    if miss_panel:
        print("[INFO] Notebook progress message.")

print("[INFO] Notebook progress message.")

# =============================================================================
if len(avail_items) == 0:
    raise RuntimeError(f"{YEAR} 年在当前设定下没有任何可用健康指标，请检查 PANEL_ITEMS / COMMON_11_18。")

clean_mat = pd.DataFrame({c: clean_item(c, df0[c], YEAR) for c in avail_items})
miss_cnt  = clean_mat.isna().sum(axis=1)
threshold = math.ceil(len(avail_items) / 2)
drop_mask = miss_cnt >= threshold
n_drop    = int(drop_mask.sum())
print("[INFO] Notebook progress message.")

if n_drop > 0:
    id_cols = [c for c in ["ID","householdID","communityID"] if c in df0.columns]
    elim = df0.loc[drop_mask, id_cols].copy()
    elim["missing_count"] = miss_cnt[drop_mask].values
    elim["missing_rate"]  = elim["missing_count"] / float(len(avail_items))
    elim.to_excel(OUT_ELIM, index=False)
    print("Eliminate list ->", OUT_ELIM)

df = df0.loc[~drop_mask].reset_index(drop=True).copy()

# =============================================================================
score_cols = {}
for col in avail_items:
    score_cols[col] = to_01(col, df[col], YEAR)

scores = pd.DataFrame(score_cols, index=df.index)

# Original notebook comment normalized for the public code archive.
def dim_mean(dim_vars):
    cols = [c for c in dim_vars if c in scores.columns]
    if not cols:
        return pd.Series(np.nan, index=scores.index)
    return scores[cols].mean(axis=1, skipna=True)

body_score   = dim_mean(BODY_VARS);   body_score.name   = "body_index_fixed01"
mental_score = dim_mean(MENTAL_VARS); mental_score.name = "mental_index_fixed01"
social_score = dim_mean(SOCIAL_VARS); social_score.name = "social_index_fixed01"

# Original notebook comment normalized for the public code archive.
top_mat = pd.concat([body_score, mental_score, social_score], axis=1)
overall_score = top_mat.mean(axis=1, skipna=True)
overall_score.name = "overall_index_fixed01"

# =============================================================================
def to_0_100(s: pd.Series) -> pd.Series:
    return s * 100.0

def z_within_year(s: pd.Series) -> pd.Series:
    m = s.mean(skipna=True)
    sd = s.std(skipna=True)
    if pd.isna(sd) or sd == 0:
        return pd.Series(np.nan, index=s.index)
    return (s - m) / sd


body_0_100    = to_0_100(body_score);   body_0_100.name   = "body_index_0_100"
mental_0_100  = to_0_100(mental_score); mental_0_100.name = "mental_index_0_100"
social_0_100  = to_0_100(social_score); social_0_100.name = "social_index_0_100"
overall_0_100 = to_0_100(overall_score);overall_0_100.name= "overall_index_0_100"

body_z    = z_within_year(body_score);   body_z.name   = "body_index_z"
mental_z  = z_within_year(mental_score); mental_z.name = "mental_index_z"
social_z  = z_within_year(social_score); social_z.name = "social_index_z"
overall_z = z_within_year(overall_score);overall_z.name= "overall_index_z"

# =============================================================================
out = df.copy()
out["身体健康(0_1)"]     = body_score
out["心理健康(0_1)"]     = mental_score
out["社会适应(0_1)"]     = social_score
out["综合健康指数(0_1)"] = overall_score

out["身体健康(0_100)"]     = body_0_100
out["心理健康(0_100)"]     = mental_0_100
out["社会适应(0_100)"]     = social_0_100
out["综合健康指数(0_100)"] = overall_0_100

out["身体健康(z)"]     = body_z
out["心理健康(z)"]     = mental_z
out["社会适应(z)"]     = social_z
out["综合健康指数(z)"] = overall_z

# Original notebook comment normalized for the public code archive.
id_cols = [c for c in ["ID","householdID","communityID"] if c in out.columns]
dta_map = {
    "身体健康(0_1)": "body_index_fixed01",
    "心理健康(0_1)": "mental_index_fixed01",
    "社会适应(0_1)": "social_index_fixed01",
    "综合健康指数(0_1)": "overall_index_fixed01",
    "身体健康(0_100)": "body_index_0_100",
    "心理健康(0_100)": "mental_index_0_100",
    "社会适应(0_100)": "social_index_0_100",
    "综合健康指数(0_100)": "overall_index_0_100",
    "身体健康(z)": "body_index_z",
    "心理健康(z)": "mental_index_z",
    "社会适应(z)": "social_index_z",
    "综合健康指数(z)": "overall_index_z",
}
dta_cols = id_cols + [k for k in dta_map if k in out.columns]
out_dta = out[dta_cols].rename(columns=dta_map)

# Original notebook comment normalized for the public code archive.
out.to_excel(OUT_XLSX, index=False)
print("Excel ->", OUT_XLSX)

out_dta.to_stata(OUT_DTA, write_index=False)
print("Stata ->", OUT_DTA)

print("[INFO] Notebook progress message.")




# =============================================================================
# Source notebook
# =============================================================================
# record_type : wave_step
# year        : 2013
# step        : 4
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 04_wave_health_index.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 1
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 04_wave_health_index.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import math
import numpy as np
import pandas as pd

# =============================================================================
YEAR = 2013

# Original notebook comment normalized for the public code archive.
STRICT_CHECK = True

# =============================================================================
BASE = Path(r"E:\impact_assessment_child_order\older\health") / str(YEAR)
INPUT_DTA  = BASE / f"{YEAR}_health_result.dta"
INPUT_XLSX = BASE / f"{YEAR}_health_result.xlsx"
OUT_XLSX   = BASE / "health_index_entropy.xlsx"
OUT_DTA    = BASE / "health_index_entropy.dta"
OUT_CHI    = BASE / f"{YEAR}_综合健康指数.xlsx"
OUT_ELIM   = BASE / f"{YEAR}_eliminate_entropy_missing_half.xlsx"
BASE.mkdir(parents=True, exist_ok=True)

# =============================================================================
def _clean_to_str(s: pd.Series) -> pd.Series:
    s = pd.Series(s, dtype="object"); m = s.isna()
    sc = s[~m].astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = sc; s.loc[m] = np.nan; return s

def canon_id_fixed(s: pd.Series, width: int) -> pd.Series:
    s = _clean_to_str(s); m = s.notna(); s.loc[m] = s.loc[m].astype(str).str.zfill(width); return s

def minmax01(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce"); vmin, vmax = s.min(), s.max()
    if pd.isna(vmin) or pd.isna(vmax) or vmax == vmin: return pd.Series(np.nan, index=s.index)
    return (s - vmin) / (vmax - vmin)

def entropy_weights(X: pd.DataFrame):
    # Original notebook comment normalized for the public code archive.
    X = X.apply(lambda s: s.fillna(s.median()), axis=0)
    var = X.var(skipna=True); keep = var[var > 0].index.tolist(); X = X[keep]
    if X.shape[1] == 0: return pd.Series(dtype=float), X
    P = X / X.sum(axis=0)
    P = P.replace([0, np.inf, -np.inf], 1e-12)
    n = X.shape[0]; k = 1.0 / np.log(n)
    E = -k * (P * np.log(P)).sum(axis=0)   # Original notebook comment normalized for the public code archive.
    D = 1 - E                              # Original notebook comment normalized for the public code archive.
    W = (pd.Series(np.ones(len(D)) / len(D), index=D.index) if np.isclose(D.sum(), 0) else D / D.sum())
    return W, X

def prepare_series(col: str, s: pd.Series) -> pd.Series:
    """Archived notebook note for 04_wave_health_index.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = pd.to_numeric(s, errors="coerce").replace({88: np.nan, 99: np.nan})
    if col in {"disease","mental_neuro_psych","memory_disease","social_activity"}:
        return s.where(s.isin([1,2]), np.nan)
    if col in {"depress","effort","hope","fear","sleep","happy","hopeless"}:
        return s.where(s.isin([1,2,3,4]), np.nan)
    if col == "life_satisfaction": return s.where(s.isin([1,2,3,4,5]), np.nan)
    if col == "srh":               return s.where(s.isin([1,2,3,4,5]), np.nan)
    if col in {"meet_child_freq","call_child_freq"}:
        return s.where(s.isin(list(range(1,11))), np.nan)
    if col == "social_freq":
        s = s.where(s.isin([0,1,2,3]), np.nan)   # Original notebook comment normalized for the public code archive.
        return s.map({0:4, 1:1, 2:2, 3:3})       # Original notebook comment normalized for the public code archive.
    return s

def build_index(df: pd.DataFrame, indicators: dict, label: str):
    X = pd.DataFrame(index=df.index); used, dropped = [], []
    for col, higher_is_better in indicators.items():
        if col not in df.columns: dropped.append(col); continue
        s = prepare_series(col, df[col])
        # Original notebook comment normalized for the public code archive.
        if higher_is_better:
            oriented = s
        else:
            vmax = s.max(skipna=True)
            oriented = (vmax - s) if pd.notna(vmax) else s * np.nan
        X[col] = minmax01(oriented)
        used.append(col)
    if X.shape[1] == 0:
        return (pd.Series(np.nan, index=df.index, name=label), pd.Series(dtype=float), used, dropped)
    w, Xn = entropy_weights(X)
    if len(w) == 0:
        return (pd.Series(np.nan, index=df.index, name=label), w, used, dropped)
    score = (Xn[w.index] * w).sum(axis=1); score.name = label
    return score, w, used, dropped

def block_index(df, blocks: dict, label: str):
    sub_scores, ind_weights, diag = {}, {}, []
    for sub_name, sub_ind in blocks.items():
        s, w, used, dropped = build_index(df, sub_ind, f"{label}-{sub_name}")
        sub_scores[sub_name] = s; ind_weights[sub_name] = w
        diag.append([label, sub_name, "; ".join(used) if used else "(none)", "; ".join(dropped) if dropped else ""])
    X = pd.DataFrame(sub_scores)
    if X.dropna(how="all").empty:
        return (pd.Series(np.nan, index=df.index, name=label), ind_weights, pd.Series(dtype=float),
                pd.DataFrame(diag, columns=["维度","子维度","使用了哪些列","缺失/未匹配"]))
    X = X.apply(lambda s: s.fillna(s.median()), axis=0)
    w_block, Xn = entropy_weights(X)
    total = (Xn[w_block.index] * w_block).sum(axis=1); total.name = label
    return total, ind_weights, w_block, pd.DataFrame(diag, columns=["维度","子维度","使用了哪些列","缺失/未匹配"])

def to_0_100(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce"); vmin, vmax = s.min(), s.max()
    if pd.isna(vmin) or pd.isna(vmax) or vmax == vmin: return pd.Series(np.nan, index=s.index)
    return (s - vmin) / (vmax - vmin) * 100.0

def weights_table(w_detail: dict) -> pd.DataFrame:
    rows = []
    for sub, w in w_detail.items():
        if w is None or len(w) == 0: rows.append((sub, "(no-use-or-constant)", np.nan))
        else:
            for k,v in w.items(): rows.append((sub, k, v))
    return pd.DataFrame(rows, columns=["子维度","指标","熵权权重"])

# =============================================================================
try:
    df0 = pd.read_stata(INPUT_DTA, convert_categoricals=False); print("Read:", INPUT_DTA)
except Exception as e:
    print("Read .dta failed, fallback to .xlsx:", e)
    df0 = pd.read_excel(INPUT_XLSX); print("Read:", INPUT_XLSX)

# =============================================================================
for key, width in (("householdID",9), ("communityID",7), ("ID",11)):
    if key in df0.columns: df0[key] = canon_id_fixed(df0[key], width)

# =============================================================================
ALL_33 = [
    "srh","disease","mental_neuro_psych","memory_disease","social_activity","social_freq",
    "meet_child_freq","call_child_freq","annual_transfer",
    "run1km","walk1km","walk100m","sit_to_stand","stairs","bend_kneel_squat","arm_raise","lift5kg","pick_coin",
    "dress","bathe","eat","bed_chair_transfer","toilet","incontinence","housework",
    "depress","effort","hope","fear","sleep","happy","hopeless","life_satisfaction"
]
avail_cols = [c for c in ALL_33 if c in df0.columns]
if STRICT_CHECK:
    miss = [c for c in ALL_33 if c not in df0.columns]
    if miss:
        raise KeyError(f"{YEAR} 数据缺少以下指标列（请确认已用最新 {YEAR}_health_result）：{miss}")
else:
    miss = [c for c in ALL_33 if c not in df0.columns]
    if miss: print("[INFO] Notebook progress message.")

# =============================================================================
clean_mat = pd.DataFrame({c: prepare_series(c, df0[c]) for c in avail_cols})
miss_cnt  = clean_mat.isna().sum(axis=1)
threshold = math.ceil(len(avail_cols) / 2)          # Original notebook comment normalized for the public code archive.
drop_mask = miss_cnt >= threshold
n_drop    = int(drop_mask.sum())
print("[INFO] Notebook progress message.")

if n_drop > 0:
    id_cols = [c for c in ["ID","householdID","communityID"] if c in df0.columns]
    elim = df0.loc[drop_mask, id_cols].copy()
    elim["missing_count_33"] = miss_cnt[drop_mask].values
    elim["missing_rate"]     = elim["missing_count_33"] / float(len(avail_cols))
    elim.to_excel(OUT_ELIM, index=False)
    print("Eliminate list ->", OUT_ELIM)

df = df0.loc[~drop_mask].reset_index(drop=True).copy()

# =============================================================================
ADL   = {c: False for c in ["dress","bathe","eat","bed_chair_transfer","toilet","incontinence","housework"]}
FUNC  = {c: False for c in ["run1km","walk1km","walk100m","sit_to_stand","stairs","bend_kneel_squat","arm_raise","lift5kg","pick_coin"]}
DIS   = {"disease": True}

PSY_SYM   = {"depress": False, "effort": False, "hope": True, "fear": False, "sleep": False, "happy": True, "hopeless": False}
SUBJ      = {"life_satisfaction": False, "srh": False}
PSY_CHRON = {"mental_neuro_psych": True, "memory_disease": True}

SOC_PART  = {"social_activity": False, "social_freq": False}
INTERGEN  = {"meet_child_freq": False, "call_child_freq": False}
SOC_LIFE  = {"life_satisfaction": False, "depress": False}

body_idx,  body_w_detail,  body_w_block,  diag_body  = block_index(df, {"日常活动": ADL, "身体功能": FUNC, "疾病": DIS}, label="身体健康")
mental_idx, mental_w_detail, mental_w_block, diag_mental = block_index(df, {"心理症状": PSY_SYM, "主观评估": SUBJ, "慢病": PSY_CHRON}, label="心理健康")
social_idx, social_w_detail, social_w_block, diag_social = block_index(df, {"社会参与": SOC_PART, "代际联系": INTERGEN, "生活满意度与抑郁": SOC_LIFE}, label="社会适应")

diag_all = pd.concat([diag_body, diag_mental, diag_social], ignore_index=True)

topX = pd.DataFrame({"身体健康": body_idx, "心理健康": mental_idx, "社会适应": social_idx})
if topX.dropna(how="all").empty:
    top_w = pd.Series(dtype=float)
    overall = pd.Series(np.nan, index=df.index, name="综合健康指数(熵权)")
else:
    topX = topX.apply(lambda s: s.fillna(s.median()), axis=0)
    top_w, topXn = entropy_weights(topX)
    overall = (topXn[top_w.index] * top_w).sum(axis=1); overall.name = "综合健康指数(熵权)"

# =============================================================================
out = df.copy()
out["身体健康"] = body_idx
out["心理健康"] = mental_idx
out["社会适应"] = social_idx
out["综合健康指数(熵权)"] = overall
out["身体健康(0-100)"]     = to_0_100(out["身体健康"])
out["心理健康(0-100)"]     = to_0_100(out["心理健康"])
out["社会适应(0-100)"]     = to_0_100(out["社会适应"])
out["综合健康指数(0-100)"] = to_0_100(out["综合健康指数(熵权)"])

tab_body   = weights_table(body_w_detail)
tab_mental = weights_table(mental_w_detail)
tab_social = weights_table(social_w_detail)

with pd.ExcelWriter(OUT_XLSX, engine="xlsxwriter") as writer:
    out.to_excel(writer, index=False, sheet_name="indices")
    pd.DataFrame({"维度": top_w.index, "熵权权重": top_w.values}).to_excel(writer, index=False, sheet_name="weights_top3")
    tab_body.to_excel(writer, index=False, sheet_name="weights_body")
    pd.DataFrame({"子维度": body_w_block.index, "权重": body_w_block.values}).to_excel(writer, index=False, sheet_name="weights_body_blocks")
    tab_mental.to_excel(writer, index=False, sheet_name="weights_mental")
    pd.DataFrame({"子维度": mental_w_block.index, "权重": mental_w_block.values}).to_excel(writer, index=False, sheet_name="weights_mental_blocks")
    tab_social.to_excel(writer, index=False, sheet_name="weights_social")
    pd.DataFrame({"子维度": social_w_block.index, "权重": social_w_block.values}).to_excel(writer, index=False, sheet_name="weights_social_blocks")
    diag_all.to_excel(writer, index=False, sheet_name="diagnostics")
print("Excel ->", OUT_XLSX)

id_cols = [c for c in ["ID","householdID","communityID"] if c in out.columns]
dta_map = {
    "身体健康": "body_index",
    "心理健康": "mental_index",
    "社会适应": "social_index",
    "综合健康指数(熵权)": "overall_index_ewm",
    "身体健康(0-100)": "body_index_0_100",
    "心理健康(0-100)": "mental_index_0_100",
    "社会适应(0-100)": "social_index_0_100",
    "综合健康指数(0-100)": "overall_index_0_100",
}
dta_cols = id_cols + [k for k in dta_map if k in out.columns]
out_dta = out[dta_cols].rename(columns=dta_map)
out_dta.to_stata(OUT_DTA, write_index=False)
print("Stata  ->", OUT_DTA)

chi_cols = ["ID","householdID","communityID","身体健康(0-100)","心理健康(0-100)","社会适应(0-100)","综合健康指数(0-100)"]
missing = [c for c in chi_cols if c not in out.columns]
if missing: raise KeyError(f"缺少导出所需列：{missing}")
out[chi_cols].to_excel(OUT_CHI, index=False)
print("CHI   ->", OUT_CHI)

print("\nTop-level weights:"); print(top_w)
print("[INFO] Notebook progress message.")




# =============================================================================
# Source notebook
# =============================================================================
# record_type : wave_step
# year        : 2015
# step        : 4
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 04_wave_health_index.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 1
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 04_wave_health_index.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import math
import numpy as np
import pandas as pd

# =============================================================================
BASE = Path(r"E:\impact_assessment_child_order\older\health\2015")
INPUT_DTA  = BASE / "2015_health_result.dta"
INPUT_XLSX = BASE / "2015_health_result.xlsx"
OUT_XLSX   = BASE / "health_index_entropy.xlsx"
OUT_DTA    = BASE / "health_index_entropy.dta"
OUT_CHI    = BASE / "2015_综合健康指数.xlsx"
OUT_ELIM   = BASE / "2015_eliminate_entropy_missing_half.xlsx"
BASE.mkdir(parents=True, exist_ok=True)

# =============================================================================
def _clean_to_str(s: pd.Series) -> pd.Series:
    s = pd.Series(s, dtype="object"); m = s.isna()
    sc = s[~m].astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = sc; s.loc[m] = np.nan; return s

def canon_id_fixed(s: pd.Series, width: int) -> pd.Series:
    s = _clean_to_str(s); m = s.notna(); s.loc[m] = s.loc[m].astype(str).str.zfill(width); return s

def minmax01(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce"); vmin, vmax = s.min(), s.max()
    if pd.isna(vmin) or pd.isna(vmax) or vmax == vmin: return pd.Series(np.nan, index=s.index)
    return (s - vmin) / (vmax - vmin)

def entropy_weights(X: pd.DataFrame):
    # Original notebook comment normalized for the public code archive.
    X = X.apply(lambda s: s.fillna(s.median()), axis=0)
    var = X.var(skipna=True); keep = var[var > 0].index.tolist(); X = X[keep]
    if X.shape[1] == 0: return pd.Series(dtype=float), X
    P = X / X.sum(axis=0); P = P.replace([0, np.inf, -np.inf], 1e-12)
    n = X.shape[0]; k = 1.0 / np.log(n)
    E = -k * (P * np.log(P)).sum(axis=0); D = 1 - E
    W = (pd.Series(np.ones(len(D)) / len(D), index=D.index) if np.isclose(D.sum(), 0) else D / D.sum())
    return W, X

def prepare_series(col: str, s: pd.Series) -> pd.Series:
    """Archived notebook note for 04_wave_health_index.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = pd.to_numeric(s, errors="coerce").replace({88: np.nan, 99: np.nan})
    if col in {"disease","mental_neuro_psych","memory_disease","social_activity"}:
        return s.where(s.isin([1,2]), np.nan)
    if col in {"depress","effort","hope","fear","sleep","happy","hopeless"}:
        return s.where(s.isin([1,2,3,4]), np.nan)
    if col == "life_satisfaction": return s.where(s.isin([1,2,3,4,5]), np.nan)
    if col == "srh":               return s.where(s.isin([1,2,3,4,5]), np.nan)
    # Original notebook comment normalized for the public code archive.
    if col in {"meet_child_freq","call_child_freq"}:
        s = s.where(s.isin(list(range(1,17))), np.nan)
        s = s.where(s != 9, np.nan)
        return s
    # Original notebook comment normalized for the public code archive.
    if col == "social_freq":
        s = s.where(s.isin([0,1,2,3]), np.nan)
        return s.map({0:4, 1:1, 2:2, 3:3})
    return s

def build_index(df: pd.DataFrame, indicators: dict, label: str):
    X = pd.DataFrame(index=df.index); used, dropped = [], []
    for col, higher_is_better in indicators.items():
        if col not in df.columns:
            dropped.append(col); continue
        s = prepare_series(col, df[col])
        vmax = s.max(skipna=True)
        oriented = s if higher_is_better else ((vmax - s) if pd.notna(vmax) else s*np.nan)
        X[col] = minmax01(oriented); used.append(col)
    if X.shape[1] == 0:
        return (pd.Series(np.nan, index=df.index, name=label), pd.Series(dtype=float), used, dropped)
    w, Xn = entropy_weights(X)
    if len(w) == 0:
        return (pd.Series(np.nan, index=df.index, name=label), w, used, dropped)
    score = (Xn[w.index] * w).sum(axis=1); score.name = label
    return score, w, used, dropped

def block_index(df, blocks: dict, label: str):
    sub_scores, ind_weights, diag = {}, {}, []
    for sub_name, sub_ind in blocks.items():
        s, w, used, dropped = build_index(df, sub_ind, f"{label}-{sub_name}")
        sub_scores[sub_name] = s; ind_weights[sub_name] = w
        diag.append([label, sub_name, "; ".join(used) if used else "(none)", "; ".join(dropped) if dropped else ""])
    X = pd.DataFrame(sub_scores)
    if X.dropna(how="all").empty:
        return (pd.Series(np.nan, index=df.index, name=label), ind_weights, pd.Series(dtype=float),
                pd.DataFrame(diag, columns=["维度","子维度","使用了哪些列","缺失/未匹配"]))
    X = X.apply(lambda s: s.fillna(s.median()), axis=0)
    w_block, Xn = entropy_weights(X)
    total = (Xn[w_block.index] * w_block).sum(axis=1); total.name = label
    return total, ind_weights, w_block, pd.DataFrame(diag, columns=["维度","子维度","使用了哪些列","缺失/未匹配"])

def to_0_100(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce"); vmin, vmax = s.min(), s.max()
    if pd.isna(vmin) or pd.isna(vmax) or vmax == vmin: return pd.Series(np.nan, index=s.index)
    return (s - vmin) / (vmax - vmin) * 100.0

def weights_table(w_detail: dict) -> pd.DataFrame:
    rows = []
    for sub, w in w_detail.items():
        if w is None or len(w) == 0: rows.append((sub, "(no-use-or-constant)", np.nan))
        else:
            for k,v in w.items(): rows.append((sub, k, v))
    return pd.DataFrame(rows, columns=["子维度","指标","熵权权重"])

# =============================================================================
try:
    df0 = pd.read_stata(INPUT_DTA, convert_categoricals=False); print("Read:", INPUT_DTA)
except Exception as e:
    print("Read .dta failed, fallback to .xlsx:", e)
    df0 = pd.read_excel(INPUT_XLSX); print("Read:", INPUT_XLSX)

# =============================================================================
for key, width in (("householdID",9), ("communityID",7), ("ID",11)):
    if key in df0.columns: df0[key] = canon_id_fixed(df0[key], width)

# =============================================================================
ALL_33 = [
    "srh","disease","mental_neuro_psych","memory_disease","social_activity","social_freq",
    "meet_child_freq","call_child_freq","annual_transfer",
    "run1km","walk1km","walk100m","sit_to_stand","stairs","bend_kneel_squat","arm_raise","lift5kg","pick_coin",
    "dress","bathe","eat","bed_chair_transfer","toilet","incontinence","housework",
    "depress","effort","hope","fear","sleep","happy","hopeless","life_satisfaction"
]
avail_cols = [c for c in ALL_33 if c in df0.columns]
miss = [c for c in ALL_33 if c not in df0.columns]
if miss:
    print("[INFO] Notebook progress message.")

# =============================================================================
clean_mat = pd.DataFrame({c: prepare_series(c, df0[c]) for c in avail_cols})
miss_cnt  = clean_mat.isna().sum(axis=1)
threshold = math.ceil(len(avail_cols) / 2)      # Original notebook comment normalized for the public code archive.
drop_mask = miss_cnt >= threshold
n_drop    = int(drop_mask.sum())
print("[INFO] Notebook progress message.")

if n_drop > 0:
    id_cols = [c for c in ["ID","householdID","communityID"] if c in df0.columns]
    elim = df0.loc[drop_mask, id_cols].copy()
    elim["missing_count"] = miss_cnt[drop_mask].values
    elim["missing_rate"]  = elim["missing_count"] / float(len(avail_cols))
    elim.to_excel(OUT_ELIM, index=False)
    print("Eliminate list ->", OUT_ELIM)

df = df0.loc[~drop_mask].reset_index(drop=True).copy()

# =============================================================================
ADL   = {c: False for c in ["dress","bathe","eat","bed_chair_transfer","toilet","incontinence","housework"]}
FUNC  = {c: False for c in ["run1km","walk1km","walk100m","sit_to_stand","stairs","bend_kneel_squat","arm_raise","lift5kg","pick_coin"]}
DIS   = {"disease": True}

PSY_SYM   = {"depress": False, "effort": False, "hope": True, "fear": False, "sleep": False, "happy": True, "hopeless": False}
SUBJ      = {"life_satisfaction": False, "srh": False}
PSY_CHRON = {"mental_neuro_psych": True, "memory_disease": True}

SOC_PART  = {"social_activity": False, "social_freq": False}
INTERGEN  = {"meet_child_freq": False, "call_child_freq": False}
SOC_LIFE  = {"life_satisfaction": False, "depress": False}

body_idx,  body_w_detail,  body_w_block,  diag_body  = block_index(df, {"日常活动": ADL, "身体功能": FUNC, "疾病": DIS}, label="身体健康")
mental_idx, mental_w_detail, mental_w_block, diag_mental = block_index(df, {"心理症状": PSY_SYM, "主观评估": SUBJ, "慢病": PSY_CHRON}, label="心理健康")
social_idx, social_w_detail, social_w_block, diag_social = block_index(df, {"社会参与": SOC_PART, "代际联系": INTERGEN, "生活满意度与抑郁": SOC_LIFE}, label="社会适应")
diag_all = pd.concat([diag_body, diag_mental, diag_social], ignore_index=True)

topX = pd.DataFrame({"身体健康": body_idx, "心理健康": mental_idx, "社会适应": social_idx})
if topX.dropna(how="all").empty:
    top_w = pd.Series(dtype=float)
    overall = pd.Series(np.nan, index=df.index, name="综合健康指数(熵权)")
else:
    topX = topX.apply(lambda s: s.fillna(s.median()), axis=0)
    top_w, topXn = entropy_weights(topX)
    overall = (topXn[top_w.index] * top_w).sum(axis=1); overall.name = "综合健康指数(熵权)"

# =============================================================================
out = df.copy()
out["身体健康"] = body_idx
out["心理健康"] = mental_idx
out["社会适应"] = social_idx
out["综合健康指数(熵权)"] = overall
out["身体健康(0-100)"]     = to_0_100(out["身体健康"])
out["心理健康(0-100)"]     = to_0_100(out["心理健康"])
out["社会适应(0-100)"]     = to_0_100(out["社会适应"])
out["综合健康指数(0-100)"] = to_0_100(out["综合健康指数(熵权)"])

with pd.ExcelWriter(OUT_XLSX, engine="xlsxwriter") as writer:
    out.to_excel(writer, index=False, sheet_name="indices")
    # Original notebook comment normalized for the public code archive.
    def _weights_sheet(w, sheet, writer):
        if w is None or len(w)==0: pd.DataFrame(columns=["名称","权重"]).to_excel(writer, index=False, sheet_name=sheet)
        else: pd.DataFrame({"名称": w.index, "权重": w.values}).to_excel(writer, index=False, sheet_name=sheet)
    _weights_sheet(top_w,             "weights_top3", writer)
    pd.DataFrame([(k,i,v) for k,wd in body_w_detail.items()  for i,v in wd.items()],  columns=["子维度","指标","熵权权重"]).to_excel(writer, index=False, sheet_name="weights_body")
    pd.DataFrame([(k,i,v) for k,wd in mental_w_detail.items() for i,v in wd.items()], columns=["子维度","指标","熵权权重"]).to_excel(writer, index=False, sheet_name="weights_mental")
    pd.DataFrame([(k,i,v) for k,wd in social_w_detail.items() for i,v in wd.items()], columns=["子维度","指标","熵权权重"]).to_excel(writer, index=False, sheet_name="weights_social")
    diag_all.to_excel(writer, index=False, sheet_name="diagnostics")
print("Excel ->", OUT_XLSX)

id_cols = [c for c in ["ID","householdID","communityID"] if c in out.columns]
dta_map = {
    "身体健康": "body_index",
    "心理健康": "mental_index",
    "社会适应": "social_index",
    "综合健康指数(熵权)": "overall_index_ewm",
    "身体健康(0-100)": "body_index_0_100",
    "心理健康(0-100)": "mental_index_0_100",
    "社会适应(0-100)": "social_index_0_100",
    "综合健康指数(0-100)": "overall_index_0_100",
}
dta_cols = id_cols + [k for k in dta_map if k in out.columns]
out_dta = out[dta_cols].rename(columns=dta_map)
out_dta.to_stata(OUT_DTA, write_index=False)
print("Stata ->", OUT_DTA)

chi_cols = ["ID","householdID","communityID","身体健康(0-100)","心理健康(0-100)","社会适应(0-100)","综合健康指数(0-100)"]
out[chi_cols].to_excel(OUT_CHI, index=False)
print("CHI ->", OUT_CHI)

print("\nTop-level weights:"); print(top_w)
print("[INFO] Notebook progress message.")




# =============================================================================
# Source notebook
# =============================================================================
# record_type : wave_step
# year        : 2018
# step        : 4
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 04_wave_health_index.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 1
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 04_wave_health_index.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import math
import numpy as np
import pandas as pd

# =============================================================================
YEAR = 2018
BASE = Path(r"E:\impact_assessment_child_order\older\health") / str(YEAR)
INPUT_DTA  = BASE / f"{YEAR}_health_result.dta"
INPUT_XLSX = BASE / f"{YEAR}_health_result.xlsx"
OUT_XLSX   = BASE / "health_index_entropy.xlsx"
OUT_DTA    = BASE / "health_index_entropy.dta"
OUT_CHI    = BASE / f"{YEAR}_综合健康指数.xlsx"
OUT_ELIM   = BASE / f"{YEAR}_eliminate_entropy_missing_half.xlsx"
BASE.mkdir(parents=True, exist_ok=True)

# =============================================================================
def _clean_to_str(s: pd.Series) -> pd.Series:
    s = pd.Series(s, dtype="object"); m = s.isna()
    sc = s[~m].astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = sc; s.loc[m] = np.nan; return s

def canon_id_fixed(s: pd.Series, width: int) -> pd.Series:
    s = _clean_to_str(s); m = s.notna(); s.loc[m] = s.loc[m].astype(str).str.zfill(width); return s

def minmax01(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce"); vmin, vmax = s.min(), s.max()
    if pd.isna(vmin) or pd.isna(vmax) or vmax == vmin: return pd.Series(np.nan, index=s.index)
    return (s - vmin) / (vmax - vmin)

def entropy_weights(X: pd.DataFrame):
    # Original notebook comment normalized for the public code archive.
    X = X.apply(lambda s: s.fillna(s.median()), axis=0)
    var = X.var(skipna=True); keep = var[var > 0].index.tolist(); X = X[keep]
    if X.shape[1] == 0: return pd.Series(dtype=float), X
    P = X / X.sum(axis=0); P = P.replace([0, np.inf, -np.inf], 1e-12)
    n = X.shape[0]; k = 1.0 / np.log(n)
    E = -k * (P * np.log(P)).sum(axis=0); D = 1 - E
    W = (pd.Series(np.ones(len(D)) / len(D), index=D.index) if np.isclose(D.sum(), 0) else D / D.sum())
    return W, X

def _meet_call_auto(series: pd.Series) -> pd.Series:
    """Archived notebook note for 04_wave_health_index.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    s = pd.to_numeric(series, errors="coerce").replace({88: np.nan, 99: np.nan})
    vmax = s.max(skipna=True)
    if pd.notna(vmax) and vmax > 10:
        s = s.where(s.isin(list(range(1,17))), np.nan)
        s = s.where(s != 9, np.nan)  # Original notebook comment normalized for the public code archive.
    else:
        s = s.where(s.isin(list(range(1,11))), np.nan)
    return s

def prepare_series(col: str, s: pd.Series) -> pd.Series:
    """Archived notebook note for 04_wave_health_index.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if col in {"meet_child_freq","call_child_freq"}:
        return _meet_call_auto(s)
    s = pd.to_numeric(s, errors="coerce").replace({88: np.nan, 99: np.nan})
    if col in {"disease","mental_neuro_psych","memory_disease","social_activity"}:
        return s.where(s.isin([1,2]), np.nan)
    if col in {"depress","effort","hope","fear","sleep","happy","hopeless"}:
        return s.where(s.isin([1,2,3,4]), np.nan)
    if col == "life_satisfaction": return s.where(s.isin([1,2,3,4,5]), np.nan)
    if col == "srh":               return s.where(s.isin([1,2,3,4,5]), np.nan)
    if col == "social_freq":
        s = s.where(s.isin([0,1,2,3]), np.nan)      # Original notebook comment normalized for the public code archive.
        return s.map({0:4, 1:1, 2:2, 3:3})          # Original notebook comment normalized for the public code archive.
    return s

def build_index(df: pd.DataFrame, indicators: dict, label: str):
    X = pd.DataFrame(index=df.index); used, dropped = [], []
    for col, higher_is_better in indicators.items():
        if col not in df.columns: dropped.append(col); continue
        s = prepare_series(col, df[col])
        vmax = s.max(skipna=True)
        oriented = s if higher_is_better else ((vmax - s) if pd.notna(vmax) else s*np.nan)
        X[col] = minmax01(oriented); used.append(col)
    if X.shape[1] == 0:
        return (pd.Series(np.nan, index=df.index, name=label), pd.Series(dtype=float), used, dropped)
    w, Xn = entropy_weights(X)
    if len(w) == 0:
        return (pd.Series(np.nan, index=df.index, name=label), w, used, dropped)
    score = (Xn[w.index] * w).sum(axis=1); score.name = label
    return score, w, used, dropped

def block_index(df, blocks: dict, label: str):
    sub_scores, ind_weights, diag = {}, {}, []
    for sub_name, sub_ind in blocks.items():
        s, w, used, dropped = build_index(df, sub_ind, f"{label}-{sub_name}")
        sub_scores[sub_name] = s; ind_weights[sub_name] = w
        diag.append([label, sub_name, "; ".join(used) if used else "(none)", "; ".join(dropped) if dropped else ""])
    X = pd.DataFrame(sub_scores)
    if X.dropna(how="all").empty:
        return (pd.Series(np.nan, index=df.index, name=label), ind_weights, pd.Series(dtype=float),
                pd.DataFrame(diag, columns=["维度","子维度","使用了哪些列","缺失/未匹配"]))
    X = X.apply(lambda s: s.fillna(s.median()), axis=0)
    w_block, Xn = entropy_weights(X)
    total = (Xn[w_block.index] * w_block).sum(axis=1); total.name = label
    return total, ind_weights, w_block, pd.DataFrame(diag, columns=["维度","子维度","使用了哪些列","缺失/未匹配"])

def to_0_100(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce"); vmin, vmax = s.min(), s.max()
    if pd.isna(vmin) or pd.isna(vmax) or vmax == vmin: return pd.Series(np.nan, index=s.index)
    return (s - vmin) / (vmax - vmin) * 100.0

def weights_table(w_detail: dict) -> pd.DataFrame:
    rows = []
    for sub, w in w_detail.items():
        if w is None or len(w) == 0: rows.append((sub, "(no-use-or-constant)", np.nan))
        else:
            for k,v in w.items(): rows.append((sub, k, v))
    return pd.DataFrame(rows, columns=["子维度","指标","熵权权重"])

# =============================================================================
try:
    df0 = pd.read_stata(INPUT_DTA, convert_categoricals=False); print("Read:", INPUT_DTA)
except Exception as e:
    print("Read .dta failed, fallback to .xlsx:", e)
    df0 = pd.read_excel(INPUT_XLSX); print("Read:", INPUT_XLSX)

# =============================================================================
for key, width in (("householdID",9), ("communityID",7), ("ID",11)):
    if key in df0.columns: df0[key] = canon_id_fixed(df0[key], width)

# =============================================================================
ALL_33 = [
    "srh","disease","mental_neuro_psych","memory_disease","social_activity","social_freq",
    "meet_child_freq","call_child_freq","annual_transfer",
    "run1km","walk1km","walk100m","sit_to_stand","stairs","bend_kneel_squat","arm_raise","lift5kg","pick_coin",
    "dress","bathe","eat","bed_chair_transfer","toilet","incontinence","housework",
    "depress","effort","hope","fear","sleep","happy","hopeless","life_satisfaction"
]
avail_cols = [c for c in ALL_33 if c in df0.columns]
miss = [c for c in ALL_33 if c not in df0.columns]
if miss:
    print("[INFO] Notebook progress message.")

# =============================================================================
clean_mat = pd.DataFrame({c: prepare_series(c, df0[c]) for c in avail_cols})
miss_cnt  = clean_mat.isna().sum(axis=1)
threshold = math.ceil(len(avail_cols) / 2)      # Original notebook comment normalized for the public code archive.
drop_mask = miss_cnt >= threshold
n_drop    = int(drop_mask.sum())
print("[INFO] Notebook progress message.")

if n_drop > 0:
    id_cols = [c for c in ["ID","householdID","communityID"] if c in df0.columns]
    elim = df0.loc[drop_mask, id_cols].copy()
    elim["missing_count"] = miss_cnt[drop_mask].values
    elim["missing_rate"]  = elim["missing_count"] / float(len(avail_cols))
    elim.to_excel(OUT_ELIM, index=False)
    print("Eliminate list ->", OUT_ELIM)

df = df0.loc[~drop_mask].reset_index(drop=True).copy()

# =============================================================================
ADL   = {c: False for c in ["dress","bathe","eat","bed_chair_transfer","toilet","incontinence","housework"]}
FUNC  = {c: False for c in ["run1km","walk1km","walk100m","sit_to_stand","stairs","bend_kneel_squat","arm_raise","lift5kg","pick_coin"]}
DIS   = {"disease": True}

PSY_SYM   = {"depress": False, "effort": False, "hope": True, "fear": False, "sleep": False, "happy": True, "hopeless": False}
SUBJ      = {"life_satisfaction": False, "srh": False}
PSY_CHRON = {"mental_neuro_psych": True, "memory_disease": True}

SOC_PART  = {"social_activity": False, "social_freq": False}
INTERGEN  = {"meet_child_freq": False, "call_child_freq": False}
SOC_LIFE  = {"life_satisfaction": False, "depress": False}

body_idx,  body_w_detail,  body_w_block,  diag_body  = block_index(df, {"日常活动": ADL, "身体功能": FUNC, "疾病": DIS}, label="身体健康")
mental_idx, mental_w_detail, mental_w_block, diag_mental = block_index(df, {"心理症状": PSY_SYM, "主观评估": SUBJ, "慢病": PSY_CHRON}, label="心理健康")
social_idx, social_w_detail, social_w_block, diag_social = block_index(df, {"社会参与": SOC_PART, "代际联系": INTERGEN, "生活满意度与抑郁": SOC_LIFE}, label="社会适应")
diag_all = pd.concat([diag_body, diag_mental, diag_social], ignore_index=True)

topX = pd.DataFrame({"身体健康": body_idx, "心理健康": mental_idx, "社会适应": social_idx})
if topX.dropna(how="all").empty:
    top_w = pd.Series(dtype=float)
    overall = pd.Series(np.nan, index=df.index, name="综合健康指数(熵权)")
else:
    topX = topX.apply(lambda s: s.fillna(s.median()), axis=0)
    top_w, topXn = entropy_weights(topX)
    overall = (topXn[top_w.index] * top_w).sum(axis=1); overall.name = "综合健康指数(熵权)"

# =============================================================================
out = df.copy()
out["身体健康"] = body_idx
out["心理健康"] = mental_idx
out["社会适应"] = social_idx
out["综合健康指数(熵权)"] = overall
out["身体健康(0-100)"]     = to_0_100(out["身体健康"])
out["心理健康(0-100)"]     = to_0_100(out["心理健康"])
out["社会适应(0-100)"]     = to_0_100(out["社会适应"])
out["综合健康指数(0-100)"] = to_0_100(out["综合健康指数(熵权)"])

tab_body   = weights_table(body_w_detail)
tab_mental = weights_table(mental_w_detail)
tab_social = weights_table(social_w_detail)

with pd.ExcelWriter(OUT_XLSX, engine="xlsxwriter") as writer:
    out.to_excel(writer, index=False, sheet_name="indices")
    pd.DataFrame({"维度": top_w.index, "熵权权重": top_w.values}).to_excel(writer, index=False, sheet_name="weights_top3")
    tab_body.to_excel(writer, index=False, sheet_name="weights_body")
    pd.DataFrame({"子维度": body_w_block.index, "权重": body_w_block.values}).to_excel(writer, index=False, sheet_name="weights_body_blocks")
    tab_mental.to_excel(writer, index=False, sheet_name="weights_mental")
    pd.DataFrame({"子维度": mental_w_block.index, "权重": mental_w_block.values}).to_excel(writer, index=False, sheet_name="weights_mental_blocks")
    tab_social.to_excel(writer, index=False, sheet_name="weights_social")
    pd.DataFrame({"子维度": social_w_block.index, "权重": social_w_block.values}).to_excel(writer, index=False, sheet_name="weights_social_blocks")
    diag_all.to_excel(writer, index=False, sheet_name="diagnostics")
print("Excel ->", OUT_XLSX)

id_cols = [c for c in ["ID","householdID","communityID"] if c in out.columns]
dta_map = {
    "身体健康": "body_index",
    "心理健康": "mental_index",
    "社会适应": "social_index",
    "综合健康指数(熵权)": "overall_index_ewm",
    "身体健康(0-100)": "body_index_0_100",
    "心理健康(0-100)": "mental_index_0_100",
    "社会适应(0-100)": "social_index_0_100",
    "综合健康指数(0-100)": "overall_index_0_100",
}
dta_cols = id_cols + [k for k in dta_map if k in out.columns]
out_dta = out[dta_cols].rename(columns=dta_map)
out_dta.to_stata(OUT_DTA, write_index=False)
print("Stata ->", OUT_DTA)

chi_cols = ["ID","householdID","communityID","身体健康(0-100)","心理健康(0-100)","社会适应(0-100)","综合健康指数(0-100)"]
out[chi_cols].to_excel(OUT_CHI, index=False)
print("CHI ->", OUT_CHI)

print("\nTop-level weights:"); print(top_w)
print("[INFO] Notebook progress message.")




# =============================================================================
# Source notebook
# =============================================================================
# record_type : wave_step
# year        : 2020
# step        : 4
# step_name: archived processing step.
# Source notebook: internal original notebook (non-public source filename omitted).
# Source path: internal local path omitted from the public archive.
# =============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 04_wave_health_index.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

# ------------------------------------------------------------------------------
# Notebook cell 5
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Archived notebook note for 04_wave_health_index.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import math
import numpy as np
import pandas as pd

# =============================================================================
YEAR = 2020
BASE      = Path(r"E:\impact_assessment_child_order\older\health") / str(YEAR)
INPUT_DTA = BASE / f"{YEAR}_health_result.dta"
INPUT_XLSX= BASE / f"{YEAR}_health_result.xlsx"
OUT_XLSX  = BASE / "health_index_entropy.xlsx"
OUT_DTA   = BASE / "health_index_entropy.dta"
OUT_CHI   = BASE / f"{YEAR}_综合健康指数.xlsx"
OUT_ELIM  = BASE / f"{YEAR}_eliminate_entropy_missing_half.xlsx"
BASE.mkdir(parents=True, exist_ok=True)

# =============================================================================
def _clean_to_str(s: pd.Series) -> pd.Series:
    s = pd.Series(s, dtype="object"); m = s.isna()
    sc = s[~m].astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.replace(r"\s+", "", regex=True)
    s.loc[~m] = sc; s.loc[m] = np.nan; return s

def canon_id_fixed(s: pd.Series, width: int) -> pd.Series:
    s = _clean_to_str(s); m = s.notna(); s.loc[m] = s.loc[m].astype(str).str.zfill(width); return s

def minmax01(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce"); vmin, vmax = s.min(), s.max()
    if pd.isna(vmin) or pd.isna(vmax) or vmax == vmin: return pd.Series(np.nan, index=s.index)
    return (s - vmin) / (vmax - vmin)

def entropy_weights(X: pd.DataFrame):
    # Original notebook comment normalized for the public code archive.
    X = X.apply(lambda s: s.fillna(s.median()), axis=0)
    var = X.var(skipna=True); keep = var[var > 0].index.tolist(); X = X[keep]
    if X.shape[1] == 0: return pd.Series(dtype=float), X
    P = X / X.sum(axis=0); P = P.replace([0, np.inf, -np.inf], 1e-12)
    n = X.shape[0]; k = 1.0 / np.log(n)
    E = -k * (P * np.log(P)).sum(axis=0); D = 1 - E
    W = (pd.Series(np.ones(len(D)) / len(D), index=D.index) if np.isclose(D.sum(), 0) else D / D.sum())
    return W, X

# Original notebook comment normalized for the public code archive.
def _meet_call_auto(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce").replace({88: np.nan, 99: np.nan})
    vmax = s.max(skipna=True)
    if pd.notna(vmax) and vmax > 10:
        s = s.where(s.isin(list(range(1,17))), np.nan)
        s = s.where(s != 9, np.nan)  # Original notebook comment normalized for the public code archive.
    else:
        s = s.where(s.isin(list(range(1,11))), np.nan)
    return s

def prepare_series(col: str, s: pd.Series) -> pd.Series:
    """Archived notebook note for 04_wave_health_index.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if col in {"meet_child_freq","call_child_freq"}:
        return _meet_call_auto(s)

    s = pd.to_numeric(s, errors="coerce").replace({88: np.nan, 99: np.nan})

    # Original notebook comment normalized for the public code archive.
    if col in {"immediate_recall","delayed_recall"}:
        # Original notebook comment normalized for the public code archive.
        s = s.where(s.isin(range(0,11)) | s.isna(), np.nan)
        s = s.replace({11: 0})  # Original notebook comment normalized for the public code archive.
        return s
    if col == "cesd10_sum":
        return s.where((s >= 0) & (s <= 30), np.nan)

    # Original notebook comment normalized for the public code archive.
    if col in {"disease","social_activity"}:
        return s.where(s.isin([1,2]), np.nan)
    if col in {"depress","effort","hope","fear","sleep","happy","hopeless"}:
        return s.where(s.isin([1,2,3,4]), np.nan)
    if col == "life_satisfaction":
        return s.where(s.isin([1,2,3,4,5]), np.nan)
    if col == "srh":
        return s.where(s.isin([1,2,3,4,5]), np.nan)
    if col == "social_freq":
        # Original notebook comment normalized for the public code archive.
        s = s.where(s.isin([0,1,2,3]), np.nan)
        return s.map({0:4, 1:1, 2:2, 3:3})
    # Original notebook comment normalized for the public code archive.
    return s

def build_index(df: pd.DataFrame, indicators: dict, label: str):
    """
    indicators: {column: higher_is_better(bool)}
    """
    X = pd.DataFrame(index=df.index); used, dropped = [], []
    for col, higher_is_better in indicators.items():
        if col not in df.columns:
            dropped.append(col); continue
        s = prepare_series(col, df[col])
        vmax = s.max(skipna=True)
        oriented = s if higher_is_better else ((vmax - s) if pd.notna(vmax) else s*np.nan)
        X[col] = minmax01(oriented); used.append(col)
    if X.shape[1] == 0:
        return (pd.Series(np.nan, index=df.index, name=label), pd.Series(dtype=float), used, dropped)
    w, Xn = entropy_weights(X)
    if len(w) == 0:
        return (pd.Series(np.nan, index=df.index, name=label), w, used, dropped)
    score = (Xn[w.index] * w).sum(axis=1); score.name = label
    return score, w, used, dropped

def block_index(df, blocks: dict, label: str):
    sub_scores, ind_weights, diag = {}, {}, []
    for sub_name, sub_ind in blocks.items():
        s, w, used, dropped = build_index(df, sub_ind, f"{label}-{sub_name}")
        sub_scores[sub_name] = s; ind_weights[sub_name] = w
        diag.append([label, sub_name, "; ".join(used) if used else "(none)", "; ".join(dropped) if dropped else ""])
    X = pd.DataFrame(sub_scores)
    if X.dropna(how="all").empty:
        return (pd.Series(np.nan, index=df.index, name=label), ind_weights, pd.Series(dtype=float),
                pd.DataFrame(diag, columns=["维度","子维度","使用了哪些列","缺失/未匹配"]))
    X = X.apply(lambda s: s.fillna(s.median()), axis=0)
    w_block, Xn = entropy_weights(X)
    total = (Xn[w_block.index] * w_block).sum(axis=1); total.name = label
    return total, ind_weights, w_block, pd.DataFrame(diag, columns=["维度","子维度","使用了哪些列","缺失/未匹配"])

def to_0_100(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce"); vmin, vmax = s.min(), s.max()
    if pd.isna(vmin) or pd.isna(vmax) or vmax == vmin: return pd.Series(np.nan, index=s.index)
    return (s - vmin) / (vmax - vmin) * 100.0

def weights_table(w_detail: dict) -> pd.DataFrame:
    rows = []
    for sub, w in w_detail.items():
        if w is None or len(w) == 0: rows.append((sub, "(no-use-or-constant)", np.nan))
        else:
            for k,v in w.items(): rows.append((sub, k, v))
    return pd.DataFrame(rows, columns=["子维度","指标","熵权权重"])

# =============================================================================
try:
    df0 = pd.read_stata(INPUT_DTA, convert_categoricals=False); print("Read:", INPUT_DTA)
except Exception as e:
    print("Read .dta failed, fallback to .xlsx:", e)
    df0 = pd.read_excel(INPUT_XLSX); print("Read:", INPUT_XLSX)

# =============================================================================
for key, width in (("householdID",9), ("communityID",7), ("ID",11)):
    if key in df0.columns: df0[key] = canon_id_fixed(df0[key], width)

# =============================================================================
ALL_2020 = [
    # Original notebook comment normalized for the public code archive.
    "srh","disease","social_activity","social_freq","meet_child_freq","call_child_freq","annual_transfer",
    # Original notebook comment normalized for the public code archive.
    "dress","bathe","eat","bed_chair_transfer","bend_kneel_squat","incontinence","housework",
    # Original notebook comment normalized for the public code archive.
    "life_satisfaction",
    # Original notebook comment normalized for the public code archive.
    "immediate_recall","delayed_recall","cesd10_sum",
]
avail_cols = [c for c in ALL_2020 if c in df0.columns]
miss = [c for c in ALL_2020 if c not in df0.columns]
if miss:
    print("[INFO] Notebook progress message.")

# =============================================================================
clean_mat = pd.DataFrame({c: prepare_series(c, df0[c]) for c in avail_cols})
miss_cnt  = clean_mat.isna().sum(axis=1)
threshold = math.ceil(len(avail_cols) / 2)
drop_mask = miss_cnt >= threshold
n_drop    = int(drop_mask.sum())
print("[INFO] Notebook progress message.")

if n_drop > 0:
    id_cols = [c for c in ["ID","householdID","communityID"] if c in df0.columns]
    elim = df0.loc[drop_mask, id_cols].copy()
    elim["missing_count"] = miss_cnt[drop_mask].values
    elim["missing_rate"]  = elim["missing_count"] / float(len(avail_cols))
    elim.to_excel(OUT_ELIM, index=False)
    print("Eliminate list ->", OUT_ELIM)

df = df0.loc[~drop_mask].reset_index(drop=True).copy()

# =============================================================================
# Original notebook comment normalized for the public code archive.
ADL = {c: False for c in ["dress","bathe","eat","bed_chair_transfer","bend_kneel_squat","incontinence","housework"]}
DIS = {"disease": True}  # Original notebook comment normalized for the public code archive.

# Original notebook comment normalized for the public code archive.
COGNITIVE = {"immediate_recall": True, "delayed_recall": True}   # Original notebook comment normalized for the public code archive.
DEPRESS   = {"cesd10_sum": False}                                 # Original notebook comment normalized for the public code archive.
SUBJ      = {"life_satisfaction": False, "srh": False}            # Original notebook comment normalized for the public code archive.

# Fixed-effects regression helper.
SOC_PART  = {"social_activity": False, "social_freq": False}
INTERGEN  = {"meet_child_freq": False, "call_child_freq": False}
TRANSFER  = {"annual_transfer": True}  # Original notebook comment normalized for the public code archive.

body_idx,  body_w_detail,  body_w_block,  diag_body   = block_index(df, {"日常活动": ADL, "疾病": DIS}, label="身体健康")
mental_idx, mental_w_detail, mental_w_block, diag_mental = block_index(df, {"认知记忆": COGNITIVE, "抑郁症状": DEPRESS, "主观评估": SUBJ}, label="心理健康")
social_idx, social_w_detail, social_w_block, diag_social = block_index(df, {"社会参与": SOC_PART, "代际联系": INTERGEN, "年度转移": TRANSFER}, label="社会适应")
diag_all = pd.concat([diag_body, diag_mental, diag_social], ignore_index=True)

# Original notebook comment normalized for the public code archive.
topX = pd.DataFrame({"身体健康": body_idx, "心理健康": mental_idx, "社会适应": social_idx})
if topX.dropna(how="all").empty:
    top_w = pd.Series(dtype=float)
    overall = pd.Series(np.nan, index=df.index, name="综合健康指数(熵权)")
else:
    topX = topX.apply(lambda s: s.fillna(s.median()), axis=0)
    top_w, topXn = entropy_weights(topX)
    overall = (topXn[top_w.index] * top_w).sum(axis=1); overall.name = "综合健康指数(熵权)"

# =============================================================================
out = df.copy()
out["身体健康"] = body_idx
out["心理健康"] = mental_idx
out["社会适应"] = social_idx
out["综合健康指数(熵权)"] = overall
out["身体健康(0-100)"]     = to_0_100(out["身体健康"])
out["心理健康(0-100)"]     = to_0_100(out["心理健康"])
out["社会适应(0-100)"]     = to_0_100(out["社会适应"])
out["综合健康指数(0-100)"] = to_0_100(out["综合健康指数(熵权)"])

tab_body   = weights_table(body_w_detail)
tab_mental = weights_table(mental_w_detail)
tab_social = weights_table(social_w_detail)

with pd.ExcelWriter(OUT_XLSX, engine="xlsxwriter") as writer:
    out.to_excel(writer, index=False, sheet_name="indices")
    pd.DataFrame({"维度": top_w.index, "熵权权重": top_w.values}).to_excel(writer, index=False, sheet_name="weights_top3")
    tab_body.to_excel(writer, index=False, sheet_name="weights_body")
    pd.DataFrame({"子维度": body_w_block.index, "权重": body_w_block.values}).to_excel(writer, index=False, sheet_name="weights_body_blocks")
    tab_mental.to_excel(writer, index=False, sheet_name="weights_mental")
    pd.DataFrame({"子维度": mental_w_block.index, "权重": mental_w_block.values}).to_excel(writer, index=False, sheet_name="weights_mental_blocks")
    tab_social.to_excel(writer, index=False, sheet_name="weights_social")
    pd.DataFrame({"子维度": social_w_block.index, "权重": social_w_block.values}).to_excel(writer, index=False, sheet_name="weights_social_blocks")
    diag_all.to_excel(writer, index=False, sheet_name="diagnostics")
print("Excel ->", OUT_XLSX)

id_cols = [c for c in ["ID","householdID","communityID"] if c in out.columns]
dta_map = {
    "身体健康": "body_index",
    "心理健康": "mental_index",
    "社会适应": "social_index",
    "综合健康指数(熵权)": "overall_index_ewm",
    "身体健康(0-100)": "body_index_0_100",
    "心理健康(0-100)": "mental_index_0_100",
    "社会适应(0-100)": "social_index_0_100",
    "综合健康指数(0-100)": "overall_index_0_100",
}
dta_cols = id_cols + [k for k in dta_map if k in out.columns]
out_dta = out[dta_cols].rename(columns=dta_map)
out_dta.to_stata(OUT_DTA, write_index=False)
print("Stata ->", OUT_DTA)

chi_cols = ["ID","householdID","communityID","身体健康(0-100)","心理健康(0-100)","社会适应(0-100)","综合健康指数(0-100)"]
missing = [c for c in chi_cols if c not in out.columns]
if missing: raise KeyError(f"缺少导出所需列：{missing}")
out[chi_cols].to_excel(OUT_CHI, index=False)
print("CHI ->", OUT_CHI)

print("\nTop-level weights:"); print(top_w)
print("[INFO] Notebook progress message.")
