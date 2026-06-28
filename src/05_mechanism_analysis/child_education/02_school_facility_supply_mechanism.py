#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 02_school_facility_supply_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 2
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 02_school_facility_supply_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd

# =============================================================================
# Original notebook comment normalized for the public code archive.
SCHOOL_PANEL_PARQUET = Path(
    "/home/ll/jupyter_notebook/result/ensemble_school/"
    "school_flood_exposure_ge1m_panel.parquet"
)

# Original notebook comment normalized for the public code archive.
COUNTY_SHP = Path(
    "/home/ll/jupyter_notebook/gis_data/China/country/country.shp"
)

# Original notebook comment normalized for the public code archive.
EDU_BM_PARQUET = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "edu_micro_2015_with_storage_BM_T2_5_10_20_50_100.parquet"
)

# Original notebook comment normalized for the public code archive.
OUT_COUNTY_YEAR = Path(
    "/home/ll/jupyter_notebook/result/ensemble_school/"
    "school_flood_exposure_ge1m_county_year.parquet"
)
OUT_SCHOOL_COHORT = Path(
    "/home/ll/jupyter_notebook/result/ensemble_school/"
    "school_flood_exposure_ge1m_county_birthyear.parquet"
)
OUT_EDU_SCHOOL_PARQUET = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "edu_micro_2015_BM_school_exposure.parquet"
)
OUT_EDU_SCHOOL_SAMPLE = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "edu_micro_2015_BM_school_exposure_sample.xlsx"
)

# Original notebook comment normalized for the public code archive.
SCHOOL_AGE_MIN = 6
SCHOOL_AGE_MAX = 15


# =============================================================================
def load_county_shp():
    """Archived notebook note for 02_school_facility_supply_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print("[INFO] Notebook progress message.")
    gdf = gpd.read_file(COUNTY_SHP)

    if gdf.crs is None:
        raise ValueError("county shapefile 缺少 CRS，请先写入 EPSG:4326。")
    gdf = gdf.to_crs(epsg=4326)

    # Original notebook comment normalized for the public code archive.
    if "county_code" in gdf.columns:
        code_col = "county_code"
    elif "县代码" in gdf.columns:
        code_col = "县代码"
    else:
        raise KeyError("县级矢量中找不到 county_code 或 县代码 字段。")

    gdf["county_code"] = pd.to_numeric(gdf[code_col], errors="coerce").astype("Int64")
    gdf = gdf.dropna(subset=["county_code"]).copy()
    return gdf[["county_code", "geometry"]]


def build_county_year_from_school():
    """Archived notebook note for 02_school_facility_supply_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print("[INFO] Notebook progress message.")
    df = pd.read_parquet(SCHOOL_PANEL_PARQUET)
    print("[INFO] Notebook progress message.")
    # School POI processing note.

    # Original notebook comment normalized for the public code archive.
    gdf_county = load_county_shp()

    gdf_school = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["lon"], df["lat"]),
        crs="EPSG:4326",
    )

    print("[INFO] Notebook progress message.")
    gdf_join = gpd.sjoin(
        gdf_school,
        gdf_county,
        how="left",
        predicate="within",
    )

    # Original notebook comment normalized for the public code archive.
    gdf_join = gdf_join.dropna(subset=["county_code"]).copy()
    gdf_join["county_code"] = (
        pd.to_numeric(gdf_join["county_code"], errors="coerce").astype("Int64")
    )

    keep_cols = [
        "school_id",
        "county_code",
        "year",
        "build_year",
        "exposed_ge1m",
        "days_ge1m",
    ]
    df_j = gdf_join[keep_cols].copy()

    # Original notebook comment normalized for the public code archive.
    df_j = df_j[df_j["build_year"] <= df_j["year"]].copy()

    # County-level processing note.
    print("[INFO] Notebook progress message.")
    grouped = (
        df_j.groupby(["county_code", "year"], as_index=False)
        .agg(
            n_school=("school_id", "nunique"),
            n_school_exposed_ge1m=("exposed_ge1m", lambda x: int((x > 0).sum())),
            share_exposed_ge1m=("exposed_ge1m", "mean"),  # Original notebook comment normalized for the public code archive.
            mean_days_ge1m=("days_ge1m", "mean"),
        )
    )

    print("[INFO] Notebook progress message.")
    print(grouped.head())

    OUT_COUNTY_YEAR.parent.mkdir(parents=True, exist_ok=True)
    grouped.to_parquet(OUT_COUNTY_YEAR, index=False)
    print("[INFO] Notebook progress message.")

    return grouped


def build_school_cohort_exposure(df_cy: pd.DataFrame, birth_min: int, birth_max: int):
    """Archived notebook note for 02_school_facility_supply_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print(
        f"[STEP] 按在学年龄段 {SCHOOL_AGE_MIN}–{SCHOOL_AGE_MAX} 岁展开 county×year → county×birth_year"
    )

    pieces = []
    for age in range(SCHOOL_AGE_MIN, SCHOOL_AGE_MAX + 1):
        tmp = df_cy.copy()
        tmp["age"] = age
        tmp["birth_year"] = tmp["year"] - age
        pieces.append(tmp)

    df_expanded = pd.concat(pieces, ignore_index=True)

    # Original notebook comment normalized for the public code archive.
    df_expanded = df_expanded[
        (df_expanded["birth_year"] >= birth_min)
        & (df_expanded["birth_year"] <= birth_max)
    ].copy()

    print("[INFO] Notebook progress message.")

    # County-level processing note.
    agg = (
        df_expanded.groupby(["county_code", "birth_year"], as_index=False)
        .agg(
            # Original notebook comment normalized for the public code archive.
            F_school_n_years=("year", "nunique"),
            # Original notebook comment normalized for the public code archive.
            F_school_any_exposed_ge1m=(
                "share_exposed_ge1m",
                lambda x: int((x > 0).any()),
            ),
            # Original notebook comment normalized for the public code archive.
            F_school_mean_share_ge1m=("share_exposed_ge1m", "mean"),
            # Original notebook comment normalized for the public code archive.
            F_school_mean_days_ge1m=("mean_days_ge1m", "mean"),
            # Original notebook comment normalized for the public code archive.
            F_school_n_flood_years=(
                "share_exposed_ge1m",
                lambda x: int((x > 0).sum()),
            ),
        )
    )

    # School POI processing note.
    agg["F_school_mean_share"] = agg["F_school_mean_share_ge1m"]

    print("[INFO] Notebook progress message.")
    print(agg.head())

    OUT_SCHOOL_COHORT.parent.mkdir(parents=True, exist_ok=True)
    agg.to_parquet(OUT_SCHOOL_COHORT, index=False)
    print("[INFO] Notebook progress message.")

    return agg


def merge_school_exposure_to_micro(df_school_cohort: pd.DataFrame):
    """Archived notebook note for 02_school_facility_supply_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print("[INFO] Notebook progress message.")
    edu = pd.read_parquet(EDU_BM_PARQUET)
    print("[INFO] Notebook progress message.")

    # birth_year
    if "birth_year" not in edu.columns:
        raise KeyError("教育微观数据中缺少 birth_year 列。")
    edu["birth_year"] = pd.to_numeric(edu["birth_year"], errors="coerce").astype(
        "Int64"
    )

    # County-level processing note.
    if "county_code" in edu.columns:
        edu["county_code"] = pd.to_numeric(edu["county_code"], errors="coerce").astype(
            "Int64"
        )
    elif "M2" in edu.columns:
        edu["county_code"] = pd.to_numeric(edu["M2"], errors="coerce").astype("Int64")
    else:
        raise KeyError("教育微观数据中缺少 county_code 或 M2 列。")

    df_school_cohort = df_school_cohort.copy()
    df_school_cohort["county_code"] = pd.to_numeric(
        df_school_cohort["county_code"], errors="coerce"
    ).astype("Int64")
    df_school_cohort["birth_year"] = pd.to_numeric(
        df_school_cohort["birth_year"], errors="coerce"
    ).astype("Int64")

    # County-level processing note.
    merged = edu.merge(
        df_school_cohort,
        how="left",
        on=["county_code", "birth_year"],
        validate="m:1",
    )

    # Original notebook comment normalized for the public code archive.
    exp_cols = [c for c in merged.columns if c.startswith("F_school_")]
    for c in exp_cols:
        merged[c] = merged[c].fillna(0)

    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print(merged[["county_code", "birth_year"] + exp_cols].head())

    OUT_EDU_SCHOOL_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    merged.to_parquet(OUT_EDU_SCHOOL_PARQUET, index=False)
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    n_sample = min(100_000, len(merged))
    if n_sample > 0:
        sample = merged.sample(n=n_sample, random_state=42)
        OUT_EDU_SCHOOL_SAMPLE.parent.mkdir(parents=True, exist_ok=True)
        sample.to_excel(
            OUT_EDU_SCHOOL_SAMPLE, index=False, sheet_name="sample"
        )
        print("[INFO] Notebook progress message.")

    return merged


def main():
    # County-level processing note.
    df_cy = build_county_year_from_school()

    # Original notebook comment normalized for the public code archive.
    edu = pd.read_parquet(EDU_BM_PARQUET)
    birth_min = int(pd.to_numeric(edu["birth_year"], errors="coerce").min())
    birth_max = int(pd.to_numeric(edu["birth_year"], errors="coerce").max())
    print("[INFO] Notebook progress message.")

    # School POI processing note.
    df_school_cohort = build_school_cohort_exposure(df_cy, birth_min, birth_max)

    # Original notebook comment normalized for the public code archive.
    merge_school_exposure_to_micro(df_school_cohort)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 5
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 02_school_facility_supply_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings
import numpy as np
import pandas as pd
from pyfixest.estimation import feols

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)

# =============================================================================
IN_PARQUET = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "edu_micro_2015_BM_school_exposure.parquet"
)

OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "statistics/school_mechanism_FE"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_CSV = OUT_DIR / "school_mechanism_FE_n_floodyears.csv"

Y_VAR = "edu_years"

# Original notebook comment normalized for the public code archive.
BIRTH_MIN, BIRTH_MAX = 1980, 2000
AGE_MIN, AGE_MAX = 15, 35
ONLY_NON_MIGRANT = True
SAMPLES_URBAN = ["rural", "urban"]  # Original notebook comment normalized for the public code archive.

# Original notebook comment normalized for the public code archive.
CONTROL_VARS = ["M34", "M37", "M15", "M16"]
CONTROL_FML = " + ".join([f"C({c})" for c in CONTROL_VARS])

# Original notebook comment normalized for the public code archive.
D_PREFIX = "D_flood_"
K_MAX = 9  # Original notebook comment normalized for the public code archive.


# =============================================================================
def ensure_numeric(df: pd.DataFrame, cols):
    """Archived notebook note for 02_school_facility_supply_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def build_is_urban_is_migrant(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 02_school_facility_supply_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if "is_urban" not in df.columns and "M2" in df.columns:
        suffix = df["M2"].astype("Int64") % 100
        df["is_urban"] = np.where((suffix >= 1) & (suffix <= 20), 1, 0)

    if "is_migrant" not in df.columns and "M38" in df.columns:
        df["is_migrant"] = np.where(df["M38"] == 1, 0, 1)

    return df


def add_flood_count_dummies(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 02_school_facility_supply_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if "F_school_n_flood_years" not in df.columns:
        raise KeyError(
            "数据中缺少 F_school_n_flood_years，请先运行 Route A 数据准备脚本。"
        )

    df = df.copy()
    df["F_school_n_flood_years"] = pd.to_numeric(
        df["F_school_n_flood_years"], errors="coerce"
    ).fillna(0)

    # Original notebook comment normalized for the public code archive.
    df["n_flood_cap"] = df["F_school_n_flood_years"].clip(lower=0, upper=K_MAX).astype(
        int
    )

    for k in range(1, K_MAX + 1):
        col = f"{D_PREFIX}{k}"
        df[col] = (df["n_flood_cap"] == k).astype(int)

    return df


def normalize_tidy(res) -> pd.DataFrame:
    """Archived notebook note for 02_school_facility_supply_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = res.tidy().reset_index()
    if df.columns[0] != "Term":
        df = df.rename(columns={df.columns[0]: "Term"})

    rename = {}
    for c in df.columns:
        lc = c.lower().replace(" ", "").replace(".", "")
        if lc in ["estimate", "coef", "coefficient"]:
            rename[c] = "Estimate"
        elif lc in ["stderr", "stderror", "std_error", "std"]:
            rename[c] = "StdError"
        elif lc in ["pvalue", "p>|t|", "pr(>|t|)", "p"]:
            rename[c] = "PValue"
    df = df.rename(columns=rename)

    if "StdError" not in df.columns:
        for c in df.columns:
            if "std" in c.lower():
                df = df.rename(columns={c: "StdError"})
                break
    if "PValue" not in df.columns:
        for c in df.columns:
            if c.lower().startswith("p"):
                df = df.rename(columns={c: "PValue"})
                break
    return df


def get_nobs(fit, fallback_df: pd.DataFrame) -> int:
    """Archived notebook note for 02_school_facility_supply_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    for attr in ["nobs", "_N", "N"]:
        if hasattr(fit, attr):
            try:
                return int(getattr(fit, attr))
            except Exception:
                pass
    return int(len(fallback_df))


def prepare_sample(df_all: pd.DataFrame, sample_tag: str) -> pd.DataFrame:
    """Archived notebook note for 02_school_facility_supply_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df_all.copy()

    num_cols = ["M2", "M38", "birth_year", "age_2015"] + CONTROL_VARS
    df = ensure_numeric(df, num_cols)
    df = build_is_urban_is_migrant(df)
    df = add_flood_count_dummies(df)

    mask = pd.Series(True, index=df.index)

    # Original notebook comment normalized for the public code archive.
    if ONLY_NON_MIGRANT and "is_migrant" in df.columns:
        mask &= (df["is_migrant"] == 0)

    # Original notebook comment normalized for the public code archive.
    if "age_2015" in df.columns:
        mask &= df["age_2015"].between(AGE_MIN, AGE_MAX)
    mask &= df["birth_year"].between(BIRTH_MIN, BIRTH_MAX)

    # Original notebook comment normalized for the public code archive.
    if sample_tag == "rural":
        mask &= (df["is_urban"] == 0)
    elif sample_tag == "urban":
        mask &= (df["is_urban"] == 1)

    dfm = df[mask].copy()

    # Original notebook comment normalized for the public code archive.
    dfm = dfm.dropna(subset=[Y_VAR, "M2", "birth_year"])

    # Original notebook comment normalized for the public code archive.
    dfm["prov_code"] = (dfm["M2"].astype("Int64") // 10000)

    # Original notebook comment normalized for the public code archive.
    dfm["prov_birth_fe"] = (
        dfm["prov_code"].astype("Int64").astype(str) + "_" +
        dfm["birth_year"].astype("Int64").astype(str)
    )

    # Original notebook comment normalized for the public code archive.
    dfm["birth_year_c"] = dfm["birth_year"] - 1995

    # Original notebook comment normalized for the public code archive.
    for c in CONTROL_VARS:
        if c in dfm.columns:
            dfm[c] = pd.to_numeric(dfm[c], errors="coerce")
            dfm = dfm.dropna(subset=[c])
            dfm[c] = dfm[c].astype(int).astype("category")
            dfm[c] = dfm[c].cat.remove_unused_categories()

    dfm = dfm.reset_index(drop=True)
    return dfm


def run_regressions(df_all: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 02_school_facility_supply_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    records = []

    # Original notebook comment normalized for the public code archive.
    d_cols = [f"{D_PREFIX}{k}" for k in range(1, K_MAX + 1)]

    for sample_tag in SAMPLES_URBAN:
        dfm = prepare_sample(df_all, sample_tag)
        n = len(dfm)
        print(f"[FEOLS] sample={sample_tag}, N={n}")
        if n < 200:
            print("[INFO] Notebook progress message.")
            continue

        # Original notebook comment normalized for the public code archive.
        missing = [c for c in d_cols if c not in dfm.columns]
        if missing:
            raise KeyError(f"样本 {sample_tag} 缺少虚拟变量列: {missing}")

        # Original notebook comment normalized for the public code archive.
        d_part = " + ".join(d_cols)
        fml = (
            f"{Y_VAR} ~ {d_part} + {CONTROL_FML} + "
            f"i(M2, birth_year_c) | M2 + prov_birth_fe"
        )

        try:
            fit = feols(fml, dfm, vcov={"CRV1": "M2"})
        except Exception as e:
            print("[INFO] Notebook progress message.")
            continue

        tidy = normalize_tidy(fit)
        nobs = get_nobs(fit, dfm)

        # Original notebook comment normalized for the public code archive.
        for k in range(1, K_MAX + 1):
            term_name = f"{D_PREFIX}{k}"
            row = tidy[tidy["Term"] == term_name]
            if row.empty:
                continue
            row = row.iloc[0]
            est = row.get("Estimate", np.nan)
            se = row.get("StdError", np.nan)
            pv = row.get("PValue", np.nan)

            records.append({
                "sample": sample_tag,
                "k_flood": k,  # Original notebook comment normalized for the public code archive.
                "Term": term_name,
                "Estimate": float(est) if pd.notna(est) else np.nan,
                "StdError": float(se) if pd.notna(se) else np.nan,
                "PValue": float(pv) if pd.notna(pv) else np.nan,
                "nobs": nobs,
            })

    return pd.DataFrame(records)


# =============================================================================
def main():
    print("[INFO] Notebook progress message.")
    df = pd.read_parquet(IN_PARQUET)
    print("[INFO] Notebook progress message.")

    res_df = run_regressions(df)

    if not res_df.empty:
        res_df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
        print("[INFO] Notebook progress message.")
        print(res_df.head())
    else:
        print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 7
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 02_school_facility_supply_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =============================================================================
RES_CSV = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/statistics/"
    "school_mechanism_FE/school_mechanism_FE_n_floodyears.csv"
)

OUT_LINE = RES_CSV.parent / "school_mechanism_FE_n_floodyears_line.png"
OUT_DOT  = RES_CSV.parent / "school_mechanism_FE_n_floodyears_dotwhisker.png"


def sig_label(p: float) -> str:
    """Archived notebook note for 02_school_facility_supply_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if p <= 0.001:
        return "***"
    elif p <= 0.01:
        return "**"
    elif p <= 0.05:
        return "*"
    elif p <= 0.1:
        return "."
    else:
        return ""


def prepare_data() -> pd.DataFrame:
    """Archived notebook note for 02_school_facility_supply_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print("[INFO] Notebook progress message.")
    df = pd.read_csv(RES_CSV)
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    df = df[df["sample"].isin(["rural", "urban"])].copy()

    if df.empty:
        raise RuntimeError("结果表中没有 rural / urban 的回归结果。")

    # Original notebook comment normalized for the public code archive.
    df["k_flood"] = pd.to_numeric(df["k_flood"], errors="coerce").astype(int)

    # Original notebook comment normalized for the public code archive.
    z = 1.96
    df["CI_low"] = df["Estimate"] - z * df["StdError"]
    df["CI_high"] = df["Estimate"] + z * df["StdError"]

    # Original notebook comment normalized for the public code archive.
    df["sig"] = df["PValue"].apply(sig_label)

    print("[INFO] Notebook progress message.")
    print(df.head())

    return df


def plot_line(df: pd.DataFrame):
    """Archived notebook note for 02_school_facility_supply_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    fig, ax = plt.subplots(figsize=(7, 4.5))

    # Original notebook comment normalized for the public code archive.
    style_cfg = {
        "rural": dict(color="tab:green", marker="o", label="农村"),
        "urban": dict(color="tab:red", marker="s", label="城镇"),
    }

    z = 1.96
    ks = sorted(df["k_flood"].unique())

    for sample in ["rural", "urban"]:
        sub = df[df["sample"] == sample].copy()
        if sub.empty:
            continue

        sub = sub.sort_values("k_flood")
        x = sub["k_flood"].values
        y = sub["Estimate"].values
        yerr = z * sub["StdError"].values

        ax.errorbar(
            x,
            y,
            yerr=yerr,
            **style_cfg[sample],
            linestyle="-",
            capsize=4,
            linewidth=1.5,
        )

    # Original notebook comment normalized for the public code archive.
    ax.axhline(0.0, linestyle="--", color="gray", linewidth=1)

    # Original notebook comment normalized for the public code archive.
    xticks = ks
    xticklabels = [str(k) if k < 9 else "9+" for k in ks]
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels)

    ax.set_xlabel("在学期间内被淹年份数（年）")
    ax.set_ylabel("对受教育年限的边际影响（年）")
    ax.set_title("学校淹没机制（次数）：rural / urban 对比（折线+误差棒）")

    ax.legend(loc="best", frameon=False)

    plt.tight_layout()
    plt.savefig(OUT_LINE, dpi=300)
    plt.show()
    print("[INFO] Notebook progress message.")


def plot_dot_whisker(df: pd.DataFrame):
    """Archived notebook note for 02_school_facility_supply_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    fig, ax = plt.subplots(figsize=(7, 4.5))

    style_cfg = {
        "rural": dict(color="tab:green", marker="o", label="农村"),
        "urban": dict(color="tab:red", marker="s", label="城镇"),
    }

    z = 1.96
    ks = sorted(df["k_flood"].unique())

    # Original notebook comment normalized for the public code archive.
    offset = 0.15
    sample_pos_shift = {"rural": -offset, "urban": offset}

    for sample in ["rural", "urban"]:
        sub = df[df["sample"] == sample].copy()
        if sub.empty:
            continue
        sub = sub.sort_values("k_flood")

        y = sub["k_flood"].values.astype(float) + sample_pos_shift[sample]
        x = sub["Estimate"].values
        xerr = z * sub["StdError"].values

        ax.errorbar(
            x,
            y,
            xerr=xerr,
            **style_cfg[sample],
            linestyle="none",
            capsize=4,
            linewidth=1.5,
        )

    # Original notebook comment normalized for the public code archive.
    ax.axvline(0.0, linestyle="--", color="gray", linewidth=1)

    # Original notebook comment normalized for the public code archive.
    yticks = ks
    yticklabels = [str(k) if k < 9 else "9+" for k in ks]
    ax.set_yticks(yticks)
    ax.set_yticklabels(yticklabels)

    ax.set_xlabel("对受教育年限的边际影响（年）")
    ax.set_ylabel("在学期间内被淹年份数（年）")
    ax.set_title("学校淹没机制（次数）：rural / urban 对比（Dot-and-whisker）")
    ax.legend(loc="best", frameon=False)

    plt.tight_layout()
    plt.savefig(OUT_DOT, dpi=300)
    plt.show()
    print("[INFO] Notebook progress message.")


def main():
    df = prepare_data()
    plot_line(df)
    plot_dot_whisker(df)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 9
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 02_school_facility_supply_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

import numpy as np
import pandas as pd
from pyfixest.estimation import feols

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)

# =============================================================================

IN_PARQUET = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "edu_micro_2015_BM_school_exposure.parquet"
)

OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "statistics/school_mechanism_FE"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_CSV = OUT_DIR / "school_mechanism_trend_FE_results.csv"

Y_VAR = "edu_years"
TREND_VAR = "F_school_n_flood_years"  # Original notebook comment normalized for the public code archive.

# Original notebook comment normalized for the public code archive.
BIRTH_MIN, BIRTH_MAX = 1980, 2000
AGE_MIN, AGE_MAX = 15, 35
ONLY_NON_MIGRANT = True

# Original notebook comment normalized for the public code archive.
SAMPLES_URBAN = ["rural", "urban"]

# Original notebook comment normalized for the public code archive.
CONTROL_VARS = ["M34", "M37", "M15", "M16"]
CONTROL_FML = " + ".join([f"C({c})" for c in CONTROL_VARS])


# =============================================================================

def ensure_numeric(df: pd.DataFrame, cols):
    """Archived notebook note for 02_school_facility_supply_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def build_is_urban_is_migrant(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 02_school_facility_supply_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if "is_urban" not in df.columns and "M2" in df.columns:
        suffix = df["M2"].astype("Int64") % 100
        df["is_urban"] = np.where((suffix >= 1) & (suffix <= 20), 1, 0)

    if "is_migrant" not in df.columns and "M38" in df.columns:
        df["is_migrant"] = np.where(df["M38"] == 1, 0, 1)

    return df


def get_nobs(fit, fallback_df: pd.DataFrame) -> int:
    """Archived notebook note for 02_school_facility_supply_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    for attr in ["nobs", "_N", "N"]:
        if hasattr(fit, attr):
            try:
                return int(getattr(fit, attr))
            except Exception:
                pass
    return int(len(fallback_df))


def normalize_tidy(res) -> pd.DataFrame:
    """Archived notebook note for 02_school_facility_supply_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = res.tidy().reset_index()
    # Original notebook comment normalized for the public code archive.
    if df.columns[0] != "Term":
        df = df.rename(columns={df.columns[0]: "Term"})

    rename = {}
    for c in df.columns:
        lc = c.lower().replace(" ", "").replace(".", "")
        if lc in ["estimate", "coef", "coefficient"]:
            rename[c] = "Estimate"
        elif lc in ["stderr", "stderror", "std_error", "std"]:
            rename[c] = "StdError"
        elif lc in ["pvalue", "p>|t|", "pr(>|t|)", "p"]:
            rename[c] = "PValue"
    df = df.rename(columns=rename)

    # Original notebook comment normalized for the public code archive.
    if "StdError" not in df.columns:
        for c in df.columns:
            if "std" in c.lower():
                df = df.rename(columns={c: "StdError"})
                break
    if "PValue" not in df.columns:
        for c in df.columns:
            if c.lower().startswith("p"):
                df = df.rename(columns={c: "PValue"})
                break

    return df


# =============================================================================

def prepare_sample(df_all: pd.DataFrame, sample_tag: str) -> pd.DataFrame:
    """Archived notebook note for 02_school_facility_supply_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df_all.copy()

    # Original notebook comment normalized for the public code archive.
    num_cols = ["M2", "M38", "birth_year", "age_2015", TREND_VAR] + CONTROL_VARS
    df = ensure_numeric(df, num_cols)

    # is_urban / is_migrant
    df = build_is_urban_is_migrant(df)

    mask = pd.Series(True, index=df.index)

    # Original notebook comment normalized for the public code archive.
    if ONLY_NON_MIGRANT and "is_migrant" in df.columns:
        mask &= (df["is_migrant"] == 0)

    # Original notebook comment normalized for the public code archive.
    if "age_2015" in df.columns:
        mask &= df["age_2015"].between(AGE_MIN, AGE_MAX)
    mask &= df["birth_year"].between(BIRTH_MIN, BIRTH_MAX)

    # Original notebook comment normalized for the public code archive.
    if sample_tag == "rural":
        mask &= (df["is_urban"] == 0)
    elif sample_tag == "urban":
        mask &= (df["is_urban"] == 1)

    dfm = df[mask].copy()

    # Original notebook comment normalized for the public code archive.
    dfm[TREND_VAR] = pd.to_numeric(dfm[TREND_VAR], errors="coerce")

    # Original notebook comment normalized for the public code archive.
    dfm = dfm.dropna(subset=[Y_VAR, TREND_VAR, "M2", "birth_year"])

    # Original notebook comment normalized for the public code archive.
    dfm["prov_code"] = (dfm["M2"].astype("Int64") // 10000)

    # Original notebook comment normalized for the public code archive.
    dfm["prov_birth_fe"] = (
        dfm["prov_code"].astype("Int64").astype(str)
        + "_"
        + dfm["birth_year"].astype("Int64").astype(str)
    )

    # Original notebook comment normalized for the public code archive.
    dfm["birth_year_c"] = dfm["birth_year"] - 1995

    # Original notebook comment normalized for the public code archive.
    for c in CONTROL_VARS:
        if c in dfm.columns:
            dfm[c] = pd.to_numeric(dfm[c], errors="coerce")
            dfm = dfm.dropna(subset=[c])
            dfm[c] = dfm[c].astype(int).astype("category")
            dfm[c] = dfm[c].cat.remove_unused_categories()

    dfm = dfm.reset_index(drop=True)
    return dfm


# =============================================================================

def run_trend_regressions(df_all: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 02_school_facility_supply_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    records = []

    for sample_tag in SAMPLES_URBAN:
        dfm = prepare_sample(df_all, sample_tag)
        n = len(dfm)
        print(f"[FEOLS] sample={sample_tag}, N={n}")
        if n < 200:
            print("[INFO] Notebook progress message.")
            continue

        # Original notebook comment normalized for the public code archive.
        fml = (
            f"{Y_VAR} ~ {TREND_VAR} + {CONTROL_FML} + "
            f"i(M2, birth_year_c) | M2 + prov_birth_fe"
        )
        print(f"  [FML] {fml}")

        try:
            fit = feols(fml, dfm, vcov={"CRV1": "M2"})
        except Exception as e:
            print("[INFO] Notebook progress message.")
            continue

        tidy = normalize_tidy(fit)
        nobs = get_nobs(fit, dfm)

        # Original notebook comment normalized for the public code archive.
        row = tidy[tidy["Term"] == TREND_VAR]
        if row.empty:
            print("[INFO] Notebook progress message.")
            continue

        r = row.iloc[0]
        est = r.get("Estimate", np.nan)
        se = r.get("StdError", np.nan)
        pv = r.get("PValue", np.nan)

        records.append(
            {
                "sample": sample_tag,
                "Term": TREND_VAR,
                "Estimate": float(est) if pd.notna(est) else np.nan,
                "StdError": float(se) if pd.notna(se) else np.nan,
                "PValue": float(pv) if pd.notna(pv) else np.nan,
                "nobs": nobs,
            }
        )

    return pd.DataFrame.from_records(records)


# =============================================================================

def main():
    print("[INFO] Notebook progress message.")
    df = pd.read_parquet(IN_PARQUET)
    print("[INFO] Notebook progress message.")

    if TREND_VAR not in df.columns:
        raise KeyError(
            f"数据中缺少 {TREND_VAR}。请在 county×birth_year 聚合时构造 "
            # Notebook-export prose note omitted from the public code archive.
        )

    res_df = run_trend_regressions(df)

    if not res_df.empty:
        res_df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
        print("[INFO] Notebook progress message.")
        print(res_df)
    else:
        print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 11
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 02_school_facility_supply_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =============================================================================
RES_CSV = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/statistics/"
    "school_mechanism_FE/school_mechanism_trend_FE_results.csv"
)

OUT_PNG = RES_CSV.parent / "school_mechanism_trend_FE_rural_urban.png"


def sig_label(p: float) -> str:
    """Archived notebook note for 02_school_facility_supply_mechanism.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if p <= 0.001:
        return "***"
    elif p <= 0.01:
        return "**"
    elif p <= 0.05:
        return "*"
    elif p <= 0.1:
        return "."
    else:
        return ""


def main():
    print("[INFO] Notebook progress message.")
    df = pd.read_csv(RES_CSV)
    print("[INFO] Notebook progress message.")

    # School POI processing note.
    sub = df[df["Term"] == "F_school_n_flood_years"].copy()

    if sub.empty:
        print("[INFO] Notebook progress message.")
        return

    # Original notebook comment normalized for the public code archive.
    sample_order = ["rural", "urban"]
    sub["sample"] = pd.Categorical(sub["sample"], categories=sample_order, ordered=True)
    sub = sub.sort_values("sample")

    # Original notebook comment normalized for the public code archive.
    z = 1.96
    sub["CI_low"] = sub["Estimate"] - z * sub["StdError"]
    sub["CI_high"] = sub["Estimate"] + z * sub["StdError"]

    # Original notebook comment normalized for the public code archive.
    sub["sig"] = sub["PValue"].apply(sig_label)

    print("[INFO] Notebook progress message.")
    print(sub[["sample", "Estimate", "StdError", "PValue", "CI_low", "CI_high", "sig"]])

    # =============================================================================
    fig, ax = plt.subplots(figsize=(6, 4))

    x = np.arange(len(sub))  # [0,1]
    y = sub["Estimate"].values
    yerr = z * sub["StdError"].values

    # Original notebook comment normalized for the public code archive.
    ax.errorbar(
        x,
        y,
        yerr=yerr,
        fmt="o",
        capsize=5,
        linewidth=1.5,
    )

    # Original notebook comment normalized for the public code archive.
    ax.axhline(0.0, linestyle="--", linewidth=1, color="gray")

    # Original notebook comment normalized for the public code archive.
    xticklabels = []
    for s in sub["sample"]:
        if s == "rural":
            xticklabels.append("农村")
        elif s == "urban":
            xticklabels.append("城镇")
        else:
            xticklabels.append(str(s))

    ax.set_xticks(x)
    ax.set_xticklabels(xticklabels)

    ax.set_ylabel("被淹年份次数的线性效应（年/次）")
    ax.set_title("学校淹没机制（次数：线性趋势）rural / urban 系数对比")

    # Original notebook comment normalized for the public code archive.
    ymax = np.nanmax(sub["CI_high"])
    ymin = np.nanmin(sub["CI_low"])
    y_span = ymax - ymin if ymax > ymin else 1.0

    # Original notebook comment normalized for the public code archive.
    for i, row in sub.reset_index(drop=True).iterrows():
        xi = x[i]
        ci_high = row["CI_high"]
        est = row["Estimate"]
        sig = row["sig"]
        p = row["PValue"]

        # Original notebook comment normalized for the public code archive.
        if sig != "":
            ax.text(
                xi,
                ci_high + 0.03 * y_span,
                sig,
                ha="center",
                va="bottom",
                fontsize=12,
            )

        # Original notebook comment normalized for the public code archive.
        ax.text(
            xi,
            ci_high + 0.13 * y_span,
            f"{est:.3f}\n(p={p:.3f})",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    plt.tight_layout()
    plt.savefig(OUT_PNG, dpi=300)
    plt.show()
    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()
