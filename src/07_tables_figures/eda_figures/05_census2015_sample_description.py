#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 05_census2015_sample_description.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 5
# ------------------------------------------------------------------------------
import pandas as pd
import numpy as np
from pathlib import Path

# =============================================================================
DATA = Path(r"E:/impact_assessment_child_order/data/supplement/EDA/"
            r"edu_micro_2015_with_storage_BM_T2_5_10_20_50_100.parquet")

# =============================================================================
BIRTH_MIN, BIRTH_MAX = 1980, 2000
AGE_MIN, AGE_MAX     = 15, 35
ONLY_NON_MIGRANT     = True

# Original notebook comment normalized for the public code archive.
NEEDED_BASE = ["M2", "birth_year", "age_2015", "M38", "edu_years", "M34", "M37", "M15", "M16"]

def build_is_urban_is_migrant(df: pd.DataFrame) -> pd.DataFrame:
    # Original notebook comment normalized for the public code archive.
    df["M2"]  = pd.to_numeric(df["M2"], errors="coerce").astype("Int64")
    df["M38"] = pd.to_numeric(df["M38"], errors="coerce").astype("Int64")

    # Original notebook comment normalized for the public code archive.
    suffix = df["M2"] % 100
    df["is_urban"] = suffix.between(1, 20).astype("Int64")  # True/False/<NA> -> 1/0/<NA>

    # Original notebook comment normalized for the public code archive.
    df["is_migrant"] = (df["M38"] != 1).astype("Int64")     # True/False/<NA> -> 1/0/<NA>

    return df

def add_fe_keys(df: pd.DataFrame) -> pd.DataFrame:
    # Original notebook comment normalized for the public code archive.
    df["prov_code"] = (df["M2"] // 10000).astype("Int64")

    # Fixed-effects regression helper.
    df["prov_birth_fe"] = df["prov_code"].astype(str) + "_" + df["birth_year"].astype(str)
    df["county_birth_cell"] = df["M2"].astype(str) + "_" + df["birth_year"].astype(str)
    return df

def sample_mask(df: pd.DataFrame, sample: str) -> pd.Series:
    m = pd.Series(True, index=df.index)

    # Original notebook comment normalized for the public code archive.
    m &= df["age_2015"].between(AGE_MIN, AGE_MAX)
    m &= df["birth_year"].between(BIRTH_MIN, BIRTH_MAX)

    # Original notebook comment normalized for the public code archive.
    if ONLY_NON_MIGRANT:
        m &= (df["is_migrant"] == 0)

    # Original notebook comment normalized for the public code archive.
    if sample == "rural":
        m &= (df["is_urban"] == 0)
    elif sample == "urban":
        m &= (df["is_urban"] == 1)
    elif sample == "all":
        pass
    else:
        raise ValueError("sample must be one of: all/rural/urban")

    return m

def quantiles(s: pd.Series) -> pd.Series:
    qs = [0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99]
    out = s.quantile(qs)
    out.index = [f"p{int(q*100):02d}" for q in qs]
    return out

# =============================================================================
df = pd.read_parquet(DATA)

missing_cols = [c for c in NEEDED_BASE if c not in df.columns]
if missing_cols:
    raise ValueError(f"DATA 缺少必要列：{missing_cols}")

df = df[NEEDED_BASE].copy()

# Original notebook comment normalized for the public code archive.
df["birth_year"] = pd.to_numeric(df["birth_year"], errors="coerce").astype("Int64")
df["age_2015"]   = pd.to_numeric(df["age_2015"], errors="coerce")
df["edu_years"]  = pd.to_numeric(df["edu_years"], errors="coerce")

for c in ["M34", "M37", "M15", "M16"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

# Fixed-effects regression helper.
df = build_is_urban_is_migrant(df)
df = add_fe_keys(df)

# =============================================================================
steps = [
    ("Raw loaded",                        lambda d: pd.Series(True, index=d.index)),
    ("Non-missing identifiers/outcome",   lambda d: d[["M2","birth_year","age_2015","M38","edu_years"]].notna().all(axis=1)),
    (f"Age in [{AGE_MIN},{AGE_MAX}]",     lambda d: d["age_2015"].between(AGE_MIN, AGE_MAX)),
    (f"Birth in [{BIRTH_MIN},{BIRTH_MAX}]", lambda d: d["birth_year"].between(BIRTH_MIN, BIRTH_MAX)),
    ("Non-migrant (M38==1)",              lambda d: (d["is_migrant"] == 0) if ONLY_NON_MIGRANT else pd.Series(True, index=d.index)),
    ("Non-missing controls (M34/M37/M15/M16)", lambda d: d[["M34","M37","M15","M16"]].notna().all(axis=1)),
]

flow_rows = []
for sample in ["all", "rural", "urban"]:
    m_sample = sample_mask(df, sample)
    cum = pd.Series(True, index=df.index)

    for name, f in steps:
        cum &= f(df)

        cur = cum.copy()
        if name == steps[-1][0]:  # Original notebook comment normalized for the public code archive.
            cur &= m_sample

        flow_rows.append({"sample": sample, "step": name, "N": int(cur.sum())})

flow_table = pd.DataFrame(flow_rows)

# =============================================================================
final_mask_all = (
    df["age_2015"].between(AGE_MIN, AGE_MAX)
    & df["birth_year"].between(BIRTH_MIN, BIRTH_MAX)
    & ((df["is_migrant"] == 0) if ONLY_NON_MIGRANT else True)
    & df[["M2","birth_year","edu_years","M34","M37","M15","M16"]].notna().all(axis=1)
)
df_final = df[final_mask_all].copy()

# =============================================================================
desc_rows = []
for sample in ["all","rural","urban"]:
    m = sample_mask(df_final, sample)
    x = df_final.loc[m, "edu_years"].dropna()
    if len(x) == 0:
        continue
    q = quantiles(x)
    row = {
        "sample": sample,
        "N": int(len(x)),
        "mean": float(x.mean()),
        "sd": float(x.std(ddof=1)),
        **{k: float(v) for k, v in q.items()}
    }
    desc_rows.append(row)

edu_desc = pd.DataFrame(desc_rows)

# =============================================================================
def size_summaries(g: pd.Series) -> dict:
    return {
        "n_groups": int(g.size),
        "min": int(g.min()),
        "p10": float(g.quantile(0.10)),
        "p50": float(g.quantile(0.50)),
        "p90": float(g.quantile(0.90)),
        "max": int(g.max()),
        "mean": float(g.mean()),
    }

support_rows = []
for sample in ["all","rural","urban"]:
    m = sample_mask(df_final, sample)
    d = df_final.loc[m].copy()
    if len(d) == 0:
        continue

    county_sizes = d.groupby("M2").size()
    prov_birth_sizes = d.groupby("prov_birth_fe").size()
    county_birth_sizes = d.groupby("county_birth_cell").size()

    support_rows.append({
        "sample": sample,
        "N": int(len(d)),
        **{f"county_{k}": v for k, v in size_summaries(county_sizes).items()},
        **{f"provbirth_{k}": v for k, v in size_summaries(prov_birth_sizes).items()},
        **{f"county_birth_{k}": v for k, v in size_summaries(county_birth_sizes).items()},
    })

fe_support = pd.DataFrame(support_rows)

# =============================================================================
out_dir = Path(r"E:\impact_assessment_child_order\data\supplement\EDA\1%sample_2015")
out_dir.mkdir(parents=True, exist_ok=True)

flow_table.to_csv(out_dir / "A_flow_table.csv", index=False, encoding="utf-8-sig")
edu_desc.to_csv(out_dir / "B_edu_years_desc.csv", index=False, encoding="utf-8-sig")
fe_support.to_csv(out_dir / "C_fe_cluster_support.csv", index=False, encoding="utf-8-sig")

print("Saved:", out_dir)
print("Dtypes check:", df[["M2","M38","is_urban","is_migrant"]].dtypes)


# ------------------------------------------------------------------------------
# Notebook cell 9
# ------------------------------------------------------------------------------
import pandas as pd
import numpy as np
from pathlib import Path

# =============================================================================
DATA = Path(r"E:/impact_assessment_child_order/data/supplement/EDA/"
            r"edu_micro_2015_with_storage_BM_T2_5_10_20_50_100.parquet")

# =============================================================================
BIRTH_MIN, BIRTH_MAX = 1980, 2000
AGE_MIN, AGE_MAX     = 15, 35
ONLY_NON_MIGRANT     = True

NEEDED_BASE = ["M2", "birth_year", "age_2015", "M38", "edu_years", "M34", "M37", "M15", "M16"]

# =============================================================================
OUT_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\EDA\1%sample_2015")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ----------------
# Helpers
# ----------------
def build_is_urban_is_migrant(df: pd.DataFrame) -> pd.DataFrame:
    df["M2"]  = pd.to_numeric(df["M2"], errors="coerce").astype("Int64")
    df["M38"] = pd.to_numeric(df["M38"], errors="coerce").astype("Int64")

    suffix = df["M2"] % 100
    df["is_urban"] = suffix.between(1, 20).astype("Int64")      # 1/0/<NA>
    df["is_migrant"] = (df["M38"] != 1).astype("Int64")         # 1/0/<NA>
    return df

def add_fe_keys(df: pd.DataFrame) -> pd.DataFrame:
    df["prov_code"] = (df["M2"] // 10000).astype("Int64")
    df["prov_birth_fe"] = df["prov_code"].astype(str) + "_" + df["birth_year"].astype(str)
    df["county_birth_cell"] = df["M2"].astype(str) + "_" + df["birth_year"].astype(str)
    return df

def base_sample_mask(df: pd.DataFrame, sample: str) -> pd.Series:
    """Archived notebook note for 05_census2015_sample_description.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if sample == "all":
        return pd.Series(True, index=df.index)
    if sample == "rural":
        return (df["is_urban"] == 0)
    if sample == "urban":
        return (df["is_urban"] == 1)
    raise ValueError("sample must be one of: all/rural/urban")

def step_masks(df: pd.DataFrame):
    """Archived notebook note for 05_census2015_sample_description.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    masks = [
        ("Raw loaded", lambda d: pd.Series(True, index=d.index)),
        ("Non-missing identifiers/outcome",
         lambda d: d[["M2","birth_year","age_2015","M38","edu_years"]].notna().all(axis=1)),
        (f"Age in [{AGE_MIN},{AGE_MAX}]",
         lambda d: d["age_2015"].between(AGE_MIN, AGE_MAX)),
        (f"Birth in [{BIRTH_MIN},{BIRTH_MAX}]",
         lambda d: d["birth_year"].between(BIRTH_MIN, BIRTH_MAX)),
        ("Non-migrant (M38==1)",
         lambda d: (d["is_migrant"] == 0) if ONLY_NON_MIGRANT else pd.Series(True, index=d.index)),
        ("Non-missing controls (M34/M37/M15/M16)",
         lambda d: d[["M34","M37","M15","M16"]].notna().all(axis=1)),
    ]
    return masks

def edu_summary(x: pd.Series) -> dict:
    x = x.dropna()
    if len(x) == 0:
        return {"edu_mean": np.nan, "edu_sd": np.nan, "edu_p25": np.nan, "edu_p50": np.nan, "edu_p75": np.nan, "edu_max": np.nan}
    qs = x.quantile([0.25, 0.50, 0.75])
    return {
        "edu_mean": float(x.mean()),
        "edu_sd": float(x.std(ddof=1)),
        "edu_p25": float(qs.loc[0.25]),
        "edu_p50": float(qs.loc[0.50]),
        "edu_p75": float(qs.loc[0.75]),
        "edu_max": float(x.max()),
    }

def group_size_quartiles(gsize: pd.Series, prefix: str) -> dict:
    """Archived notebook note for 05_census2015_sample_description.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if gsize.empty:
        return {
            f"{prefix}_n_groups": 0,
            f"{prefix}_mean": np.nan,
            f"{prefix}_p25": np.nan,
            f"{prefix}_p50": np.nan,
            f"{prefix}_p75": np.nan,
            f"{prefix}_max": np.nan,
        }
    qs = gsize.quantile([0.25, 0.50, 0.75])
    return {
        f"{prefix}_n_groups": int(gsize.size),
        f"{prefix}_mean": float(gsize.mean()),
        f"{prefix}_p25": float(qs.loc[0.25]),
        f"{prefix}_p50": float(qs.loc[0.50]),
        f"{prefix}_p75": float(qs.loc[0.75]),
        f"{prefix}_max": int(gsize.max()),
    }

# ----------------
# 1) Read & clean
# ----------------
df = pd.read_parquet(DATA)

missing = [c for c in NEEDED_BASE if c not in df.columns]
if missing:
    raise ValueError(f"DATA 缺少必要列：{missing}")

df = df[NEEDED_BASE].copy()

# Original notebook comment normalized for the public code archive.
df["birth_year"] = pd.to_numeric(df["birth_year"], errors="coerce").astype("Int64")
df["age_2015"]   = pd.to_numeric(df["age_2015"], errors="coerce")
df["edu_years"]  = pd.to_numeric(df["edu_years"], errors="coerce")
for c in ["M34", "M37", "M15", "M16"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

df = build_is_urban_is_migrant(df)
df = add_fe_keys(df)

# ----------------
# Original notebook comment normalized for the public code archive.
# ----------------
steps = step_masks(df)

flow_rows = []
flow_wide_rows = []

for sample in ["all", "rural", "urban"]:
    base = base_sample_mask(df, sample)
    cum = base.copy()

    row_wide = {"sample": sample}
    for step_name, f in steps:
        cum = cum & f(df)
        n = int(cum.sum())
        flow_rows.append({"sample": sample, "step": step_name, "N": n})
        row_wide[step_name] = n

    flow_wide_rows.append(row_wide)

flow_long = pd.DataFrame(flow_rows)
flow_wide = pd.DataFrame(flow_wide_rows)

# ----------------
# Original notebook comment normalized for the public code archive.
# ----------------
abc_rows = []
final_step_name = steps[-1][0]  # "Non-missing controls..."

for sample in ["all", "rural", "urban"]:
    # Original notebook comment normalized for the public code archive.
    base = base_sample_mask(df, sample)
    cum = base.copy()
    counts = {}

    for step_name, f in steps:
        cum = cum & f(df)
        counts[step_name] = int(cum.sum())

    d = df.loc[cum].copy()

    # Original notebook comment normalized for the public code archive.
    out = {"sample": sample}
    out.update({
        "N_raw": counts["Raw loaded"],
        "N_nonmiss_id_outcome": counts["Non-missing identifiers/outcome"],
        "N_age": counts[f"Age in [{AGE_MIN},{AGE_MAX}]"],
        "N_birth": counts[f"Birth in [{BIRTH_MIN},{BIRTH_MAX}]"],
        "N_nonmigrant": counts["Non-migrant (M38==1)"],
        "N_final": counts[final_step_name],
    })

    # Original notebook comment normalized for the public code archive.
    out.update(edu_summary(d["edu_years"]))

    # Fixed-effects regression helper.
    out.update(group_size_quartiles(d.groupby("M2").size(), "county_size"))
    out.update(group_size_quartiles(d.groupby("prov_birth_fe").size(), "provbirth_size"))
    out.update(group_size_quartiles(d.groupby("county_birth_cell").size(), "county_birth_size"))

    abc_rows.append(out)

abc_one_table = pd.DataFrame(abc_rows)

# ----------------
# 4) Save
# ----------------
flow_long.to_csv(OUT_DIR / "A_flow_table_corrected_long.csv", index=False, encoding="utf-8-sig")
flow_wide.to_csv(OUT_DIR / "A_flow_table_corrected_wide.csv", index=False, encoding="utf-8-sig")
abc_one_table.to_csv(OUT_DIR / "ABC_one_table.csv", index=False, encoding="utf-8-sig")

# Excel output note.
with pd.ExcelWriter(OUT_DIR / "ABC_summary.xlsx", engine="openpyxl") as w:
    flow_long.to_excel(w, index=False, sheet_name="A_flow_long")
    flow_wide.to_excel(w, index=False, sheet_name="A_flow_wide")
    abc_one_table.to_excel(w, index=False, sheet_name="ABC_one_table")

print("Saved to:", OUT_DIR)
print("Files:",
      "A_flow_table_corrected_long.csv",
      "A_flow_table_corrected_wide.csv",
      "ABC_one_table.csv",
      "ABC_summary.xlsx")


# ------------------------------------------------------------------------------
# Notebook cell 12
# ------------------------------------------------------------------------------
import pandas as pd
import numpy as np
from pathlib import Path

# =============================================================================
DATA = Path(
    r"E:/impact_assessment_child_order/data/supplement/EDA/"
    r"edu_micro_2015_with_storage_BM_T2_5_10_20_50_100.parquet"
)

# =============================================================================
OUT_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\EDA\1%sample_2015")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
BIRTH_MIN, BIRTH_MAX = 1980, 2000
AGE_MIN, AGE_MAX     = 15, 35
ONLY_NON_MIGRANT     = True

NEEDED_BASE = ["M2", "birth_year", "age_2015", "M38", "edu_years", "M34", "M37", "M15", "M16"]

# ----------------
# Helpers
# ----------------
def build_is_urban_is_migrant(df: pd.DataFrame) -> pd.DataFrame:
    df["M2"]  = pd.to_numeric(df["M2"], errors="coerce").astype("Int64")
    df["M38"] = pd.to_numeric(df["M38"], errors="coerce").astype("Int64")

    suffix = df["M2"] % 100
    df["is_urban"] = suffix.between(1, 20).astype("Int64")   # 1/0/<NA>
    df["is_migrant"] = (df["M38"] != 1).astype("Int64")      # 1/0/<NA>
    return df

def add_fe_keys(df: pd.DataFrame) -> pd.DataFrame:
    df["prov_code"] = (df["M2"] // 10000).astype("Int64")
    df["prov_birth_fe"] = df["prov_code"].astype(str) + "_" + df["birth_year"].astype(str)
    df["county_birth_cell"] = df["M2"].astype(str) + "_" + df["birth_year"].astype(str)
    return df

def base_sample_mask(df: pd.DataFrame, sample: str) -> pd.Series:
    if sample == "all":
        return pd.Series(True, index=df.index)
    if sample == "rural":
        return (df["is_urban"] == 0)
    if sample == "urban":
        return (df["is_urban"] == 1)
    raise ValueError("sample must be one of: all/rural/urban")

def mean_or_nan(x: pd.Series) -> float:
    x = x.dropna()
    return float(x.mean()) if len(x) else np.nan

# ----------------
# 1) Read & clean
# ----------------
df = pd.read_parquet(DATA)

missing = [c for c in NEEDED_BASE if c not in df.columns]
if missing:
    raise ValueError(f"DATA 缺少必要列：{missing}")

df = df[NEEDED_BASE].copy()

df["birth_year"] = pd.to_numeric(df["birth_year"], errors="coerce").astype("Int64")
df["age_2015"]   = pd.to_numeric(df["age_2015"], errors="coerce")
df["edu_years"]  = pd.to_numeric(df["edu_years"], errors="coerce")
for c in ["M34", "M37", "M15", "M16"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

df = build_is_urban_is_migrant(df)
df = add_fe_keys(df)

# ----------------
# 2) Build table: rows=metrics, cols=all/rural/urban
# ----------------
samples = ["all", "rural", "urban"]

row_names = [
    f"Age in [{AGE_MIN},{AGE_MAX}]",
    "Non-migrant (M38==1)",
    "Non-missing controls",
    "N_final",
    "edu_mean",
    "county_size_n_groups",
    "county_size_mean",
    "provbirth_size_n_groups",
    "provbirth_size_mean",
    "county_birth_size_n_groups",
    "county_birth_size_mean",
]

out = pd.DataFrame(index=row_names, columns=samples, dtype=float)

for s in samples:
    base = base_sample_mask(df, s)

    # Original notebook comment normalized for the public code archive.
    m_id_outcome = df[["M2","birth_year","age_2015","M38","edu_years"]].notna().all(axis=1)
    m_age   = df["age_2015"].between(AGE_MIN, AGE_MAX)
    m_birth = df["birth_year"].between(BIRTH_MIN, BIRTH_MAX)
    m_migr  = (df["is_migrant"] == 0) if ONLY_NON_MIGRANT else pd.Series(True, index=df.index)
    m_ctrl  = df[["M34","M37","M15","M16"]].notna().all(axis=1)

    # Original notebook comment normalized for the public code archive.
    m_step_age   = base & m_id_outcome & m_age
    m_step_migr  = m_step_age & m_birth & m_migr
    m_step_ctrl  = m_step_migr & m_ctrl
    m_final      = m_step_ctrl  # Original notebook comment normalized for the public code archive.

    # Original notebook comment normalized for the public code archive.
    out.loc[f"Age in [{AGE_MIN},{AGE_MAX}]", s] = int(m_step_age.sum())
    out.loc["Non-migrant (M38==1)", s]          = int(m_step_migr.sum())
    out.loc["Non-missing controls", s]          = int(m_step_ctrl.sum())
    out.loc["N_final", s]                       = int(m_final.sum())

    # Original notebook comment normalized for the public code archive.
    d = df.loc[m_final].copy()

    out.loc["edu_mean", s] = mean_or_nan(d["edu_years"])

    county_sizes = d.groupby("M2").size()
    provbirth_sizes = d.groupby("prov_birth_fe").size()
    county_birth_sizes = d.groupby("county_birth_cell").size()

    out.loc["county_size_n_groups", s] = int(county_sizes.size)
    out.loc["county_size_mean", s]     = float(county_sizes.mean()) if county_sizes.size else np.nan

    out.loc["provbirth_size_n_groups", s] = int(provbirth_sizes.size)
    out.loc["provbirth_size_mean", s]     = float(provbirth_sizes.mean()) if provbirth_sizes.size else np.nan

    out.loc["county_birth_size_n_groups", s] = int(county_birth_sizes.size)
    out.loc["county_birth_size_mean", s]     = float(county_birth_sizes.mean()) if county_birth_sizes.size else np.nan

# =============================================================================
count_rows = [
    f"Age in [{AGE_MIN},{AGE_MAX}]",
    "Non-migrant (M38==1)",
    "Non-missing controls",
    "N_final",
    "county_size_n_groups",
    "provbirth_size_n_groups",
    "county_birth_size_n_groups",
]

out_fmt = out.copy()

# Original notebook comment normalized for the public code archive.
out_fmt.loc[count_rows] = out_fmt.loc[count_rows].round(0).astype("Int64")

# Original notebook comment normalized for the public code archive.
mean_rows = [r for r in out_fmt.index if r not in count_rows]
out_fmt.loc[mean_rows] = out_fmt.loc[mean_rows].astype(float).round(2)

# Original notebook comment normalized for the public code archive.
save_path = OUT_DIR / "ABC_one_table_wide.csv"
out_fmt.to_csv(save_path, encoding="utf-8-sig")

print("Saved:", save_path)
print(out_fmt)


# ------------------------------------------------------------------------------
# Notebook cell 15
# ------------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""
Boxplots (NO points, NO outlier dots) for 3 groups: All / Rural / Urban
- Box face colors:
    all   #cde7f0
    rural #dae5cf
    urban #fb9a99
- Box border + whiskers + median use the corresponding "point" colors:
    all   #3d7da9
    rural #b9d89a
    urban #e31a1c
- Whiskers are dashed
- Box face transparency (alpha) adjustable via BOX_ALPHA
- Produce 4 figures:
    1) edu_years
    2) county cluster size
    3) prov×birth FE cell size
    4) county×birth cell size
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


# =========================
# 0) GLOBAL PLOT STYLE (Times New Roman)
# =========================
plt.rcParams.update({
    "font.family": "Times New Roman",   # Original notebook comment normalized for the public code archive.
    "axes.unicode_minus": False,        # Original notebook comment normalized for the public code archive.
    "pdf.fonttype": 42,                 # Original notebook comment normalized for the public code archive.
    "ps.fonttype": 42,
})


# =========================
# 0) PATHS & CONFIG
# =========================
DATA = Path(
    r"E:\impact_assessment_child_order\data\supplement\EDA"
    r"\edu_micro_2015_with_storage_BM_T2_5_10_20_50_100.parquet"
)

OUT_DIR = Path(r"E:\impact_assessment_child_order\data\supplement\EDA\1%sample_2015")
OUT_DIR.mkdir(parents=True, exist_ok=True)

BIRTH_MIN, BIRTH_MAX = 1980, 2000
AGE_MIN, AGE_MAX     = 15, 35
ONLY_NON_MIGRANT     = True

NEEDED = ["M2", "birth_year", "age_2015", "M38", "edu_years", "M34", "M37", "M15", "M16"]
GROUPS = ["all", "rural", "urban"]

# Box face colors (theme)
BOX_FACE = {"all": "#cde7f0", "rural": "#fdbf6f", "urban": "#cab2d6"}

# Line colors (match your previous point colors)
LINE_COL = {"all": "#3d7da9", "rural": "#ff7f00", "urban": "#6a3d9a"}

# Transparency for box fills
BOX_ALPHA = 0.55   # <-- adjust this (0=transparent, 1=opaque)

# Line widths
BOX_LW = 1.0
MED_LW = 1.0
WHISK_LW = 1.0
CAP_LW = 1.0

# Whisker style
WHISK_LS = "--"    # dashed whiskers


# =========================
# 1) HELPERS
# =========================
def build_is_urban_is_migrant(df: pd.DataFrame) -> pd.DataFrame:
    df["M2"]  = pd.to_numeric(df["M2"], errors="coerce").astype("Int64")
    df["M38"] = pd.to_numeric(df["M38"], errors="coerce").astype("Int64")

    suffix = df["M2"] % 100
    df["is_urban"] = suffix.between(1, 20).astype("Int64")     # 1/0/<NA>
    df["is_migrant"] = (df["M38"] != 1).astype("Int64")        # 1/0/<NA>
    return df

def final_reg_sample_mask(df: pd.DataFrame) -> pd.Series:
    m = pd.Series(True, index=df.index)

    m &= df[["M2", "birth_year", "age_2015", "M38", "edu_years"]].notna().all(axis=1)
    m &= df["age_2015"].between(AGE_MIN, AGE_MAX)
    m &= df["birth_year"].between(BIRTH_MIN, BIRTH_MAX)

    if ONLY_NON_MIGRANT:
        m &= (df["is_migrant"] == 0)

    m &= df[["M34", "M37", "M15", "M16"]].notna().all(axis=1)
    return m

def mask_by_group(df: pd.DataFrame, group: str) -> pd.Series:
    if group == "all":
        return pd.Series(True, index=df.index)
    if group == "rural":
        return df["is_urban"] == 0
    if group == "urban":
        return df["is_urban"] == 1
    raise ValueError("group must be one of: all / rural / urban")

def style_boxplot_artists(bp, labels):
    n = len(labels)

    # Boxes + medians
    for i in range(n):
        g = labels[i]

        box = bp["boxes"][i]
        box.set_facecolor(BOX_FACE[g])
        box.set_alpha(BOX_ALPHA)
        box.set_edgecolor(LINE_COL[g])
        box.set_linewidth(BOX_LW)

        med = bp["medians"][i]
        med.set_color(LINE_COL[g])
        med.set_linewidth(MED_LW)

    # Whiskers and caps
    for i in range(n):
        g = labels[i]

        w1 = bp["whiskers"][2*i]
        w2 = bp["whiskers"][2*i + 1]
        for w in (w1, w2):
            w.set_color(LINE_COL[g])
            w.set_linewidth(WHISK_LW)
            w.set_linestyle(WHISK_LS)

        c1 = bp["caps"][2*i]
        c2 = bp["caps"][2*i + 1]
        for c in (c1, c2):
            c.set_color(LINE_COL[g])
            c.set_linewidth(CAP_LW)

def boxplot_3groups(
    data_dict: dict,
    title: str,
    ylabel: str,
    out_path: Path,
    order=("all", "rural", "urban"),
    figsize=(6.6, 3.9),
    dpi=300,
):
    labels = list(order)
    positions = np.arange(1, len(labels) + 1)

    data_for_box = []
    for g in labels:
        x = np.asarray(data_dict.get(g, []), dtype=float)
        x = x[~np.isnan(x)]
        data_for_box.append(x)

    fig, ax = plt.subplots(figsize=figsize)

    bp = ax.boxplot(
        data_for_box,
        positions=positions,
        widths=0.22,
        patch_artist=True,
        showfliers=False,
        whis=1.5,
        boxprops=dict(linewidth=BOX_LW),
        medianprops=dict(linewidth=MED_LW),
        whiskerprops=dict(linewidth=WHISK_LW),
        capprops=dict(linewidth=CAP_LW),
    )

    style_boxplot_artists(bp, labels)

    # Original notebook comment normalized for the public code archive.
    pretty_labels = {"all": "All", "rural": "Rural", "urban": "Urban"}
    ax.set_xticks(positions)
    ax.set_xticklabels([pretty_labels[g] for g in labels], fontsize=16)

    ax.set_ylabel(ylabel, fontsize=16)
    ax.tick_params(axis="y", labelsize=16)   # Original notebook comment normalized for the public code archive.
    ax.set_title(title, fontsize=17, pad=8)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.grid(True, linestyle="--", linewidth=0.8, alpha=0.35)
    ax.set_axisbelow(True)

    plt.tight_layout()
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.show()
    print("[DONE] Saved:", out_path)


# =========================
# 2) LOAD + FILTER
# =========================
df = pd.read_parquet(DATA)

missing = [c for c in NEEDED if c not in df.columns]
if missing:
    raise ValueError(f"DATA missing required columns: {missing}")

df = df[NEEDED].copy()

df["birth_year"] = pd.to_numeric(df["birth_year"], errors="coerce").astype("Int64")
df["age_2015"]   = pd.to_numeric(df["age_2015"], errors="coerce")
df["edu_years"]  = pd.to_numeric(df["edu_years"], errors="coerce")
for c in ["M34", "M37", "M15", "M16"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

df = build_is_urban_is_migrant(df)
m_final = final_reg_sample_mask(df)
df_final = df.loc[m_final].copy()

print("[INFO] Final N all  :", len(df_final))
print("[INFO] Final N rural:", int(mask_by_group(df_final, "rural").sum()))
print("[INFO] Final N urban:", int(mask_by_group(df_final, "urban").sum()))


# =========================
# 3) BUILD 4 DISTRIBUTIONS
# =========================
edu_data = {}
for g in GROUPS:
    mg = mask_by_group(df_final, g)
    edu_data[g] = df_final.loc[mg, "edu_years"].astype(float).to_numpy()

county_size_data = {}
for g in GROUPS:
    mg = mask_by_group(df_final, g)
    d = df_final.loc[mg]
    county_size_data[g] = d.groupby("M2").size().astype(float).to_numpy()

provbirth_size_data = {}
for g in GROUPS:
    mg = mask_by_group(df_final, g)
    d = df_final.loc[mg].copy()
    prov_code = (pd.to_numeric(d["M2"], errors="coerce").astype("Int64") // 10000).astype("Int64")
    prov_birth_fe = prov_code.astype(str) + "_" + d["birth_year"].astype(str)
    provbirth_size_data[g] = prov_birth_fe.value_counts().astype(float).to_numpy()

county_birth_size_data = {}
for g in GROUPS:
    mg = mask_by_group(df_final, g)
    d = df_final.loc[mg].copy()
    county_birth_cell = d["M2"].astype(str) + "_" + d["birth_year"].astype(str)
    county_birth_size_data[g] = county_birth_cell.value_counts().astype(float).to_numpy()


# =========================
# 4) PLOT & SAVE (Optimized titles)
# =========================
boxplot_3groups(
    data_dict=edu_data,
    title="Years of Schooling in the Regression Sample",
    ylabel="Years of schooling",
    out_path=OUT_DIR / "box_edu_years.png",
)

boxplot_3groups(
    data_dict=county_size_data,
    title="Sample Size per County",
    ylabel="Observations per county",
    out_path=OUT_DIR / "box_county_cluster_size.png",
)

boxplot_3groups(
    data_dict=provbirth_size_data,
    title="Sample Size per Province × Birth-Year Cell",
    ylabel="Observations per province × birth-year",
    out_path=OUT_DIR / "box_prov_birth_fe_size.png",
)

boxplot_3groups(
    data_dict=county_birth_size_data,
    title="Sample Size per County × Birth-Year Cell",
    ylabel="Observations per county × birth-year",
    out_path=OUT_DIR / "box_county_birth_cell_size.png",
)

print("[ALL DONE] Figures saved to:", OUT_DIR)


# ------------------------------------------------------------------------------
# Notebook cell 16
# ------------------------------------------------------------------------------
# =========================
# ONLY PRINT (no raw arrays)
# =========================
import numpy as np

def print_dist_summary(data_dict: dict, name: str, order=("all", "rural", "urban")):
    """
    Print distribution summaries WITHOUT printing raw data.
    """
    pretty = {"all": "All", "rural": "Rural", "urban": "Urban"}

    print(f"\n[SUMMARY] {name}")
    for g in order:
        x = np.asarray(data_dict.get(g, []), dtype=float)
        x = x[~np.isnan(x)]

        if x.size == 0:
            print(f"  {pretty.get(g, g):5s}: N=0")
            continue

        # If values are effectively integers, print as ints; otherwise 2 decimals
        is_int_like = np.allclose(x, np.round(x), equal_nan=True)

        q1, med, q3 = np.quantile(x, [0.25, 0.50, 0.75])
        sd = float(np.std(x, ddof=1)) if x.size > 1 else 0.0

        def fmt(v):
            return f"{int(round(v)):,}" if is_int_like else f"{v:.2f}"

        print(
            f"  {pretty.get(g, g):5s}: "
            f"N={x.size:,}, mean={fmt(np.mean(x))}, sd={fmt(sd)}, "
            f"min={fmt(np.min(x))}, p25={fmt(q1)}, median={fmt(med)}, p75={fmt(q3)}, max={fmt(np.max(x))}"
        )

# ---- call examples (replace xxx_data with your dicts) ----
print_dist_summary(edu_data, "edu_years (individual-level)")
print_dist_summary(county_size_data, "county cluster size (N per county)")
print_dist_summary(provbirth_size_data, "province × birth-year FE cell size")
print_dist_summary(county_birth_size_data, "county × birth-year cell size")
