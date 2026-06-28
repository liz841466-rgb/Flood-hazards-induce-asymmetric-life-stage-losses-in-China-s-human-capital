#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 06_result_summary_tables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 1
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 06_result_summary_tables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm

# =============================================================================

PANEL_LONG_IDX = Path(
    "/home/ll/jupyter_notebook/gis_data/OLDER/CHARLS/health/"
    "charls_health_panel_long_with_index.parquet"
)

ROOT_FLOOD = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/flood_health_result"
)

# Excel output note.
FLOOD_TALL_PATHS = {
    5: ROOT_FLOOD / "city_flood_Tall_5y_1980_2020.xlsx",
    10: ROOT_FLOOD / "city_flood_Tall_10y_1980_2020.xlsx",
    20: ROOT_FLOOD / "city_flood_Tall_20y_1980_2020.xlsx",
    30: ROOT_FLOOD / "city_flood_Tall_30y_1980_2020.xlsx",
}

OUT_DIR = ROOT_FLOOD
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Original notebook comment normalized for the public code archive.
OUT_PANEL_MERGED_PARQUET = OUT_DIR / "charls_health_panel_60plus_with_index_Tall_5_10_20_30y.parquet"
OUT_PANEL_MERGED_XLSX    = OUT_DIR / "charls_health_panel_60plus_with_index_Tall_5_10_20_30y.xlsx"

# Original notebook comment normalized for the public code archive.
OUT_FE_SUMMARY = OUT_DIR / "fe_health_index_Tall_5_10_20_30y_urban_rural_results_pid12.csv"

# Original notebook comment normalized for the public code archive.
T_LIST = [2, 5, 10, 20, 50, 100]

# Original notebook comment normalized for the public code archive.
WINDOW_LIST = [5, 10, 20, 30]

# Original notebook comment normalized for the public code archive.
ID_COL = "pid12"


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def twoway_fe_reg(df, y_col, x_cols, id_col=ID_COL, t_col="year"):
    """Archived notebook note for 06_result_summary_tables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()

    cols = [y_col] + x_cols
    g_i = df.groupby(id_col)
    g_t = df.groupby(t_col)
    mu_all = df[cols].mean()

    for col in cols:
        df[f"{col}_dm"] = (
            df[col]
            - g_i[col].transform("mean")
            - g_t[col].transform("mean")
            + mu_all[col]
        )

    y = df[f"{y_col}_dm"].to_numpy()
    X = df[[f"{c}_dm" for c in x_cols]].to_numpy()

    model = sm.OLS(y, X)
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": df[id_col].to_numpy()})

    coefs = fit.params
    ses = fit.bse
    tvals = fit.tvalues
    pvals = fit.pvalues
    ci_low, ci_high = fit.conf_int().T

    res = pd.DataFrame(
        {
            "Estimate": coefs,
            "Std. Error": ses,
            "t value": tvals,
            "Pr(>|t|)": pvals,
            "2.5%": ci_low,
            "97.5%": ci_high,
        },
        index=x_cols,
    )
    return res


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def merge_panel_flood_allT_multiwindow():
    print(f"[READ] health panel (with index): {PANEL_LONG_IDX}")
    panel = pd.read_parquet(PANEL_LONG_IDX)

    # Original notebook comment normalized for the public code archive.
    panel["age"] = pd.to_numeric(panel["age"], errors="coerce")
    panel = panel[panel["age"] >= 60].copy()
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")

    # City-level processing note.
    if "city_code" not in panel.columns:
        raise KeyError("面板中不存在 city_code，请确认已经从 citycode 版本生成。")
    panel["city_code"] = pd.to_numeric(panel["city_code"], errors="coerce").astype("Int64")

    # Original notebook comment normalized for the public code archive.
    if ID_COL not in panel.columns:
        raise KeyError(f"面板中不存在列 {ID_COL}，请检查。")
    panel[ID_COL] = panel[ID_COL].astype(str)

    panel["year"] = pd.to_numeric(panel["year"], errors="coerce").astype("Int64")

    merged = panel.copy()
    all_exp_cols = []

    for window in WINDOW_LIST:
        flood_path = FLOOD_TALL_PATHS[window]
        print(f"[READ] flood {window}y (all T, xlsx): {flood_path}")
        fN = pd.read_excel(flood_path)

        fN["city_code"] = pd.to_numeric(fN["city_code"], errors="coerce").astype("Int64")
        fN["year"] = pd.to_numeric(fN["year"], errors="coerce").astype("Int64")

        # Original notebook comment normalized for the public code archive.
        exp_cols = [
            c
            for c in fN.columns
            if c.startswith("share_flood_T") and c.endswith(f"_{window}y")
        ]
        keep_cols = ["city_code", "year"] + exp_cols
        print("[INFO] Notebook progress message.")

        merged = merged.merge(
            fN[keep_cols],
            how="left",
            on=["city_code", "year"],
            validate="m:1",
        )

        # Original notebook comment normalized for the public code archive.
        if exp_cols:
            na_ratio = merged[exp_cols].isna().mean()
            print("[INFO] Notebook progress message.")

        # Original notebook comment normalized for the public code archive.
        for c in exp_cols:
            merged[c] = merged[c].fillna(0.0)

        all_exp_cols.extend(exp_cols)

    print("[INFO] Notebook progress message.")
    print(
        f"[INFO] 合并后 non-missing health_index_z 数量: "
        f"{merged['health_index_z'].notna().sum()}"
    )
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    merged.to_parquet(OUT_PANEL_MERGED_PARQUET, index=False)
    merged.to_excel(OUT_PANEL_MERGED_XLSX, index=False)
    print("[INFO] Notebook progress message.")

    return merged


# ================================
# Fixed-effects regression helper.
# ================================
def run_fe_multiT_urban_rural_multiwindow(df: pd.DataFrame):
    df = df.copy()

    # Original notebook comment normalized for the public code archive.
    df = df.dropna(subset=["health_index_z", "age", "urban_nbs", ID_COL, "year"]).copy()
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df = df.dropna(subset=["age"]).copy()
    df["age2"] = df["age"] ** 2

    df[ID_COL] = df[ID_COL].astype(str)
    df["year"] = pd.to_numeric(df["year"], errors="coerce")

    # Original notebook comment normalized for the public code archive.
    df["urban_nbs"] = pd.to_numeric(df["urban_nbs"], errors="coerce").fillna(0).astype(int)
    grp_urban = df.groupby(ID_COL)["urban_nbs"].mean()
    urban_group = (grp_urban > 0.5).astype(int).rename("urban_group")
    df = df.merge(urban_group, on=ID_COL, how="left")

    print("[INFO] Notebook progress message.")
    print(df[[ID_COL, "urban_group"]].drop_duplicates()["urban_group"].value_counts())

    # Fixed-effects regression helper.
    waves_per_id = df.groupby(ID_COL)["year"].nunique()
    keep_ids = waves_per_id[waves_per_id >= 2].index
    df = df[df[ID_COL].isin(keep_ids)].copy()
    print(
        f"[INFO] 至少有 2 个波次的 {ID_COL} 数: {df[ID_COL].nunique()}, "
        f"总行数: {len(df)}, 年份数: {df['year'].nunique()}"
    )

    sample_specs = {
        "all": None,
        "urban": 1,
        "rural": 0,
    }

    all_rows = []

    # Original notebook comment normalized for the public code archive.
    for window in WINDOW_LIST:
        exposure_cols = {T: f"share_flood_T{T}_{window}y" for T in T_LIST}

        for T, exp_col in exposure_cols.items():
            if exp_col not in df.columns:
                print("[INFO] Notebook progress message.")
                continue

            for sample_name, group_val in sample_specs.items():
                if group_val is None:
                    sub = df.copy()
                else:
                    sub = df[df["urban_group"] == group_val].copy()

                # Original notebook comment normalized for the public code archive.
                waves_sub = sub.groupby(ID_COL)["year"].nunique()
                keep_ids_sub = waves_sub[waves_sub >= 2].index
                sub = sub[sub[ID_COL].isin(keep_ids_sub)].copy()

                if len(sub) < 100:
                    print(
                        f"[WARN] window={window}, T={T}, {sample_name} 样本量过小 "
                        f"(N={len(sub)}), 跳过。"
                    )
                    continue

                x_cols = [exp_col, "age", "age2"]
                res = twoway_fe_reg(
                    sub,
                    y_col="health_index_z",
                    x_cols=x_cols,
                    id_col=ID_COL,
                    t_col="year",
                )

                # Original notebook comment normalized for the public code archive.
                row = res.loc[exp_col].copy()
                row["window"] = window
                row["T"] = T
                row["exposure"] = exp_col
                row["sample"] = sample_name
                row["N"] = len(sub)
                row["N_id"] = sub[ID_COL].nunique()
                row["N_year"] = sub["year"].nunique()

                # =============================================================================
                print("\n" + "=" * 40)
                print(f"[RESULT] window={window}y, T={T}, sample={sample_name}")
                print(res.loc[[exp_col]][["Estimate", "Pr(>|t|)"]])

                all_rows.append(row)

    if not all_rows:
        print("[INFO] Notebook progress message.")
        return

    out_df = pd.DataFrame(all_rows)
    out_df = out_df[
        [
            "window", "T", "exposure", "sample",
            "Estimate", "Std. Error", "t value", "Pr(>|t|)",
            "2.5%", "97.5%",
            "N", "N_id", "N_year",
        ]
    ]
    out_df.sort_values(["window", "T", "sample"], inplace=True)

    print("\n" + "=" * 60)
    print("[INFO] Notebook progress message.")
    print(out_df[["window", "T", "sample", "Estimate", "Pr(>|t|)"]])

    out_df.to_csv(OUT_FE_SUMMARY, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def main():
    merged = merge_panel_flood_allT_multiwindow()
    run_fe_multiT_urban_rural_multiwindow(merged)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 4
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 06_result_summary_tables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm

# =============================================================================

PANEL_MERGED = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/flood_health_result/"
    "charls_health_panel_60plus_with_index_Tall_5_10_20_30y.parquet"
)

OUT_DIR = PANEL_MERGED.parent

# Original notebook comment normalized for the public code archive.
#   "health_phys", "health_mental", "health_social", "health_index_z"
Y_VAR = "health_index_z"

# Original notebook comment normalized for the public code archive.
T_LIST = [2, 5, 10, 20, 50, 100]
WINDOW_LIST = [5, 10, 20, 30]

# Original notebook comment normalized for the public code archive.
ID_COL = "pid12"
CLUSTER_COL = "city_code"   # Original notebook comment normalized for the public code archive.
YEAR_COL = "year"
PROV_COL = "province"       # Original notebook comment normalized for the public code archive.


# =============================================================================

def demean_two_fe(df, cols, fe1, fe2):
    """Archived notebook note for 06_result_summary_tables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
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
    """Archived notebook note for 06_result_summary_tables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    cols_needed = [y_col] + x_cols + [fe1, fe2, cluster_col]
    df = df.dropna(subset=cols_needed).copy()

    # Original notebook comment normalized for the public code archive.
    df = df[df[cluster_col].notna()].copy()
    if df.empty:
        raise ValueError("所有观测在 cluster_col 上都缺失，无法回归。")

    # Fixed-effects regression helper.
    df = demean_two_fe(df, [y_col] + x_cols, fe1=fe1, fe2=fe2)

    y = df[f"{y_col}_dm"].to_numpy()
    X = df[[f"{c}_dm" for c in x_cols]].to_numpy()

    # Original notebook comment normalized for the public code archive.
    df["cluster_group"] = pd.Categorical(df[cluster_col]).codes
    groups = df["cluster_group"].to_numpy()

    model = sm.OLS(y, X)
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": groups})

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


# =============================================================================

def run_individual_fe_city_cluster():
    print(f"[READ] merged 60+ panel: {PANEL_MERGED}")
    df = pd.read_parquet(PANEL_MERGED)

    # Original notebook comment normalized for the public code archive.
    df[Y_VAR] = pd.to_numeric(df[Y_VAR], errors="coerce")
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df[YEAR_COL] = pd.to_numeric(df[YEAR_COL], errors="coerce")

    # Province-level processing note.
    # City-level processing note.

    # Original notebook comment normalized for the public code archive.
    df = df.dropna(subset=[Y_VAR, "age", ID_COL, PROV_COL, CLUSTER_COL, YEAR_COL]).copy()

    # Original notebook comment normalized for the public code archive.
    df["age2"] = df["age"] ** 2

    # Fixed-effects regression helper.
    df["prov_str"] = df[PROV_COL].astype(str).str.strip()
    df["prov_year"] = df["prov_str"] + "_" + df[YEAR_COL].astype(int).astype(str)

    # Original notebook comment normalized for the public code archive.
    df["urban_nbs"] = pd.to_numeric(df["urban_nbs"], errors="coerce").fillna(0).astype(int)
    grp_urban = df.groupby(ID_COL)["urban_nbs"].mean()
    df = df.merge(
        (grp_urban > 0.5).astype(int).rename("urban_group"),
        on=ID_COL,
        how="left",
    )

    print("[INFO] Notebook progress message.")
    print(df[[ID_COL, "urban_group"]].drop_duplicates()["urban_group"].value_counts())

    # Original notebook comment normalized for the public code archive.
    waves_per_id = df.groupby(ID_COL)[YEAR_COL].nunique()
    keep_ids = waves_per_id[waves_per_id >= 2].index
    df = df[df[ID_COL].isin(keep_ids)].copy()
    print(
        f"[INFO] 至少有 2 个波次的 {ID_COL} 数: {df[ID_COL].nunique()}, "
        f"总行数: {len(df)}, 年份数: {df[YEAR_COL].nunique()}"
    )

    # Original notebook comment normalized for the public code archive.
    sample_specs = {
        "all": None,
        "urban": 1,
        "rural": 0,
    }

    all_rows = []

    for window in WINDOW_LIST:
        exposure_cols = {T: f"share_flood_T{T}_{window}y" for T in T_LIST}

        for T, exp_col in exposure_cols.items():
            if exp_col not in df.columns:
                print("[INFO] Notebook progress message.")
                continue

            for sample_name, group_val in sample_specs.items():
                if group_val is None:
                    sub = df.copy()
                else:
                    sub = df[df["urban_group"] == group_val].copy()

                # Original notebook comment normalized for the public code archive.
                waves_sub = sub.groupby(ID_COL)[YEAR_COL].nunique()
                keep_ids_sub = waves_sub[waves_sub >= 2].index
                sub = sub[sub[ID_COL].isin(keep_ids_sub)].copy()

                if len(sub) < 100 or sub[CLUSTER_COL].nunique() < 10:
                    print(
                        f"[WARN] window={window}, T={T}, sample={sample_name} 样本量或城市数过小 "
                        f"(N={len(sub)}, N_city={sub[CLUSTER_COL].nunique()}), 跳过。"
                    )
                    continue

                x_cols = [exp_col, "age", "age2"]

                res = fe_reg_twoFE_city_cluster(
                    sub,
                    y_col=Y_VAR,
                    x_cols=x_cols,
                    fe1=ID_COL,
                    fe2="prov_year",
                    cluster_col=CLUSTER_COL,
                )

                row = res.loc[exp_col].copy()
                row["Y_var"] = Y_VAR
                row["window"] = window
                row["T"] = T
                row["exposure"] = exp_col
                row["sample"] = sample_name
                row["N"] = len(sub)
                row["N_id"] = sub[ID_COL].nunique()
                row["N_year"] = sub[YEAR_COL].nunique()
                row["N_city"] = sub[CLUSTER_COL].nunique()

                print("\n" + "=" * 40)
                print(
                    f"[RESULT] (prov×year FE, city cluster) Y={Y_VAR}, "
                    f"window={window}y, T={T}, sample={sample_name}"
                )
                print(res.loc[[exp_col]][["Estimate", "Pr(>|t|)"]])

                all_rows.append(row)

    if not all_rows:
        print("[INFO] Notebook progress message.")
        return

    out_df = pd.DataFrame(all_rows)
    out_df = out_df[
        [
            "Y_var", "window", "T", "exposure", "sample",
            "Estimate", "Std. Error", "t value", "Pr(>|t|)",
            "2.5%", "97.5%",
            "N", "N_id", "N_year", "N_city",
        ]
    ].sort_values(["Y_var", "window", "T", "sample"])

    print("\n" + "=" * 60)
    print("[INFO] Notebook progress message.")
    print(out_df[["Y_var", "window", "T", "sample", "Estimate", "Pr(>|t|)"]])

    out_path = OUT_DIR / f"fe_{Y_VAR}_Tall_5_10_20_30y_pid12_provYearFE_cityCluster.csv"
    out_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    run_individual_fe_city_cluster()


# ------------------------------------------------------------------------------
# Notebook cell 6
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 06_result_summary_tables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt  # Original notebook comment normalized for the public code archive.

# =============================================================================

PANEL_MERGED = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/flood_health_result/"
    "charls_health_panel_60plus_with_index_Tall_5_10_20_30y.parquet"
)

OUT_DIR = PANEL_MERGED.parent

# Original notebook comment normalized for the public code archive.
#   "health_phys", "health_mental", "health_social", "health_index_z"
Y_VAR = "health_index_z"

# Original notebook comment normalized for the public code archive.
T_LIST = [2, 5, 10, 20, 50, 100]
WINDOW_LIST = [5, 10, 20, 30]

# Original notebook comment normalized for the public code archive.
ID_COL = "pid12"
CLUSTER_COL = "city_code"   # Original notebook comment normalized for the public code archive.
YEAR_COL = "year"
PROV_COL = "province"       # Original notebook comment normalized for the public code archive.


# =============================================================================

def stars_for_p(p: float) -> str:
    """
    p<0.001 -> "****"
    p<0.05  -> "**"
    p<0.10  -> "*"
    else    -> ""
    """
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

def demean_two_fe(df, cols, fe1, fe2):
    """Archived notebook note for 06_result_summary_tables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
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
    """Archived notebook note for 06_result_summary_tables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    cols_needed = [y_col] + x_cols + [fe1, fe2, cluster_col]
    df = df.dropna(subset=cols_needed).copy()

    # Original notebook comment normalized for the public code archive.
    df = df[df[cluster_col].notna()].copy()
    if df.empty:
        raise ValueError("所有观测在 cluster_col 上都缺失，无法回归。")

    # Fixed-effects regression helper.
    df = demean_two_fe(df, [y_col] + x_cols, fe1=fe1, fe2=fe2)

    y = df[f"{y_col}_dm"].to_numpy()
    X = df[[f"{c}_dm" for c in x_cols]].to_numpy()

    # Original notebook comment normalized for the public code archive.
    df["cluster_group"] = pd.Categorical(df[cluster_col]).codes
    groups = df["cluster_group"].to_numpy()

    model = sm.OLS(y, X)
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": groups})

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


# =============================================================================

def run_individual_fe_city_cluster():
    print(f"[READ] merged 60+ panel: {PANEL_MERGED}")
    df = pd.read_parquet(PANEL_MERGED)

    # Original notebook comment normalized for the public code archive.
    df[Y_VAR] = pd.to_numeric(df[Y_VAR], errors="coerce")
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df[YEAR_COL] = pd.to_numeric(df[YEAR_COL], errors="coerce")

    # Original notebook comment normalized for the public code archive.
    df = df.dropna(subset=[Y_VAR, "age", ID_COL, PROV_COL, CLUSTER_COL, YEAR_COL]).copy()

    # Original notebook comment normalized for the public code archive.
    df["age2"] = df["age"] ** 2

    # Fixed-effects regression helper.
    df["prov_str"] = df[PROV_COL].astype(str).str.strip()
    df["prov_year"] = df["prov_str"] + "_" + df[YEAR_COL].astype(int).astype(str)

    # Original notebook comment normalized for the public code archive.
    df["urban_nbs"] = pd.to_numeric(df["urban_nbs"], errors="coerce").fillna(0).astype(int)
    grp_urban = df.groupby(ID_COL)["urban_nbs"].mean()
    df = df.merge(
        (grp_urban > 0.5).astype(int).rename("urban_group"),
        on=ID_COL,
        how="left",
    )

    print("[INFO] Notebook progress message.")
    print(df[[ID_COL, "urban_group"]].drop_duplicates()["urban_group"].value_counts())

    # Original notebook comment normalized for the public code archive.
    waves_per_id = df.groupby(ID_COL)[YEAR_COL].nunique()
    keep_ids = waves_per_id[waves_per_id >= 2].index
    df = df[df[ID_COL].isin(keep_ids)].copy()
    print(
        f"[INFO] 至少有 2 个波次的 {ID_COL} 数: {df[ID_COL].nunique()}, "
        f"总行数: {len(df)}, 年份数: {df[YEAR_COL].nunique()}"
    )

    # Original notebook comment normalized for the public code archive.
    sample_specs = {
        "all": None,
        "urban": 1,
        "rural": 0,
    }

    all_rows = []

    for window in WINDOW_LIST:
        exposure_cols = {T: f"share_flood_T{T}_{window}y" for T in T_LIST}

        for T, exp_col in exposure_cols.items():
            if exp_col not in df.columns:
                print("[INFO] Notebook progress message.")
                continue

            for sample_name, group_val in sample_specs.items():
                if group_val is None:
                    sub = df.copy()
                else:
                    sub = df[df["urban_group"] == group_val].copy()

                # Original notebook comment normalized for the public code archive.
                waves_sub = sub.groupby(ID_COL)[YEAR_COL].nunique()
                keep_ids_sub = waves_sub[waves_sub >= 2].index
                sub = sub[sub[ID_COL].isin(keep_ids_sub)].copy()

                if len(sub) < 100 or sub[CLUSTER_COL].nunique() < 10:
                    print(
                        f"[WARN] window={window}, T={T}, sample={sample_name} 样本量或城市数过小 "
                        f"(N={len(sub)}, N_city={sub[CLUSTER_COL].nunique()}), 跳过。"
                    )
                    continue

                x_cols = [exp_col, "age", "age2"]

                res = fe_reg_twoFE_city_cluster(
                    sub,
                    y_col=Y_VAR,
                    x_cols=x_cols,
                    fe1=ID_COL,
                    fe2="prov_year",
                    cluster_col=CLUSTER_COL,
                )

                row = res.loc[exp_col].copy()
                row["Y_var"] = Y_VAR
                row["window"] = window
                row["T"] = T
                row["exposure"] = exp_col
                row["sample"] = sample_name
                row["N"] = len(sub)
                row["N_id"] = sub[ID_COL].nunique()
                row["N_year"] = sub[YEAR_COL].nunique()
                row["N_city"] = sub[CLUSTER_COL].nunique()

                print("\n" + "=" * 40)
                print(
                    f"[RESULT] (prov×year FE, city cluster) Y={Y_VAR}, "
                    f"window={window}y, T={T}, sample={sample_name}"
                )
                print(res.loc[[exp_col]][["Estimate", "Pr(>|t|)"]])

                all_rows.append(row)

    if not all_rows:
        print("[INFO] Notebook progress message.")
        return None

    out_df = pd.DataFrame(all_rows)
    out_df = out_df[
        [
            "Y_var", "window", "T", "exposure", "sample",
            "Estimate", "Std. Error", "t value", "Pr(>|t|)",
            "2.5%", "97.5%",
            "N", "N_id", "N_year", "N_city",
        ]
    ].sort_values(["Y_var", "window", "T", "sample"])

    print("\n" + "=" * 60)
    print("[INFO] Notebook progress message.")
    print(out_df[["Y_var", "window", "T", "sample", "Estimate", "Pr(>|t|)"]])

    out_path = OUT_DIR / f"fe_{Y_VAR}_Tall_5_10_20_30y_pid12_provYearFE_cityCluster.csv"
    out_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    return out_df


# =============================================================================

def plot_intensity_by_sample(result_df: pd.DataFrame, sample: str = "all"):
    """Archived notebook note for 06_result_summary_tables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sub = result_df[
        (result_df["Y_var"] == Y_VAR) &
        (result_df["sample"] == sample)
    ].copy()

    if sub.empty:
        print("[INFO] Notebook progress message.")
        return

    # Original notebook comment normalized for the public code archive.
    y_min = sub["Estimate"].min()
    y_max = sub["Estimate"].max()
    if not np.isfinite(y_min) or not np.isfinite(y_max):
        y_min, y_max = -0.5, 0.5
    pad = 0.1 * (y_max - y_min if y_max > y_min else 1.0)
    y_lower, y_upper = y_min - pad, y_max + pad

    plt.figure(figsize=(6, 4))

    for T in sorted(sub["T"].unique()):
        tmp = sub[sub["T"] == T].sort_values("window")

        x_vals = tmp["window"].values
        y_vals = tmp["Estimate"].values
        p_vals = tmp["Pr(>|t|)"].values

        # Original notebook comment normalized for the public code archive.
        plt.plot(
            x_vals,
            y_vals,
            marker="o",
            label=f"T={T}"
        )

        # Original notebook comment normalized for the public code archive.
        y_range = y_upper - y_lower
        offset = 0.03 * y_range  # Original notebook comment normalized for the public code archive.
        for x, y, p in zip(x_vals, y_vals, p_vals):
            s = stars_for_p(p)
            if s:
                plt.text(
                    x,
                    y + offset,
                    s,
                    ha="center",
                    va="bottom",
                    fontsize=10
                )

    plt.axhline(0, linestyle="--", linewidth=1)
    plt.xlabel("滚动窗口长度（年）")
    plt.ylabel(f"{Y_VAR} 的强度效应系数 β")
    plt.title(f"强度型洪水暴露效应：sample={sample}")
    plt.legend(title="返回期 T")
    plt.ylim(y_lower, y_upper)
    plt.tight_layout()
    plt.show()  # Original notebook comment normalized for the public code archive.


# ========== main ==========

if __name__ == "__main__":
    # Original notebook comment normalized for the public code archive.
    result_df = run_individual_fe_city_cluster()

    # Original notebook comment normalized for the public code archive.
    if result_df is not None:
        plot_intensity_by_sample(result_df, sample="all")
        plot_intensity_by_sample(result_df, sample="rural")
        plot_intensity_by_sample(result_df, sample="urban")


# ------------------------------------------------------------------------------
# Notebook cell 9
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 06_result_summary_tables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm

# =============================================================================

PANEL_MERGED = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/flood_health_result/"
    "charls_health_panel_60plus_with_index_Tall_5_10_20_30y.parquet"
)

OUT_DIR = PANEL_MERGED.parent

# Original notebook comment normalized for the public code archive.
#   "health_phys", "health_mental", "health_social", "health_index_z"
Y_VAR = "health_phys"

# Original notebook comment normalized for the public code archive.
T_LIST = [2, 5, 10, 20, 50, 100]
WINDOW_LIST = [5, 10, 20, 30]

# Original notebook comment normalized for the public code archive.
ID_COL = "pid12"
CLUSTER_COL = "city_code"   # Original notebook comment normalized for the public code archive.
YEAR_COL = "year"
PROV_COL = "province"       # Original notebook comment normalized for the public code archive.


# =============================================================================

def demean_two_fe(df, cols, fe1, fe2):
    """Archived notebook note for 06_result_summary_tables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
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
    """Archived notebook note for 06_result_summary_tables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    cols_needed = [y_col] + x_cols + [fe1, fe2, cluster_col]
    df = df.dropna(subset=cols_needed).copy()

    # Original notebook comment normalized for the public code archive.
    df = df[df[cluster_col].notna()].copy()
    if df.empty:
        raise ValueError("所有观测在 cluster_col 上都缺失，无法回归。")

    # Fixed-effects regression helper.
    df = demean_two_fe(df, [y_col] + x_cols, fe1=fe1, fe2=fe2)

    y = df[f"{y_col}_dm"].to_numpy()
    X = df[[f"{c}_dm" for c in x_cols]].to_numpy()

    # Original notebook comment normalized for the public code archive.
    df["cluster_group"] = pd.Categorical(df[cluster_col]).codes
    groups = df["cluster_group"].to_numpy()

    model = sm.OLS(y, X)
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": groups})

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


# =============================================================================

def run_individual_fe_city_cluster():
    print(f"[READ] merged 60+ panel: {PANEL_MERGED}")
    df = pd.read_parquet(PANEL_MERGED)

    # Original notebook comment normalized for the public code archive.
    df[Y_VAR] = pd.to_numeric(df[Y_VAR], errors="coerce")
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df[YEAR_COL] = pd.to_numeric(df[YEAR_COL], errors="coerce")

    # Province-level processing note.
    # City-level processing note.

    # Original notebook comment normalized for the public code archive.
    df = df.dropna(subset=[Y_VAR, "age", ID_COL, PROV_COL, CLUSTER_COL, YEAR_COL]).copy()

    # Original notebook comment normalized for the public code archive.
    df["age2"] = df["age"] ** 2

    # Fixed-effects regression helper.
    df["prov_str"] = df[PROV_COL].astype(str).str.strip()
    df["prov_year"] = df["prov_str"] + "_" + df[YEAR_COL].astype(int).astype(str)

    # Original notebook comment normalized for the public code archive.
    df["urban_nbs"] = pd.to_numeric(df["urban_nbs"], errors="coerce").fillna(0).astype(int)
    grp_urban = df.groupby(ID_COL)["urban_nbs"].mean()
    df = df.merge(
        (grp_urban > 0.5).astype(int).rename("urban_group"),
        on=ID_COL,
        how="left",
    )

    print("[INFO] Notebook progress message.")
    print(df[[ID_COL, "urban_group"]].drop_duplicates()["urban_group"].value_counts())

    # Original notebook comment normalized for the public code archive.
    waves_per_id = df.groupby(ID_COL)[YEAR_COL].nunique()
    keep_ids = waves_per_id[waves_per_id >= 2].index
    df = df[df[ID_COL].isin(keep_ids)].copy()
    print(
        f"[INFO] 至少有 2 个波次的 {ID_COL} 数: {df[ID_COL].nunique()}, "
        f"总行数: {len(df)}, 年份数: {df[YEAR_COL].nunique()}"
    )

    # Original notebook comment normalized for the public code archive.
    sample_specs = {
        "all": None,
        "urban": 1,
        "rural": 0,
    }

    all_rows = []

    for window in WINDOW_LIST:
        exposure_cols = {T: f"share_flood_T{T}_{window}y" for T in T_LIST}

        for T, exp_col in exposure_cols.items():
            if exp_col not in df.columns:
                print("[INFO] Notebook progress message.")
                continue

            for sample_name, group_val in sample_specs.items():
                if group_val is None:
                    sub = df.copy()
                else:
                    sub = df[df["urban_group"] == group_val].copy()

                # Original notebook comment normalized for the public code archive.
                waves_sub = sub.groupby(ID_COL)[YEAR_COL].nunique()
                keep_ids_sub = waves_sub[waves_sub >= 2].index
                sub = sub[sub[ID_COL].isin(keep_ids_sub)].copy()

                if len(sub) < 100 or sub[CLUSTER_COL].nunique() < 10:
                    print(
                        f"[WARN] window={window}, T={T}, sample={sample_name} 样本量或城市数过小 "
                        f"(N={len(sub)}, N_city={sub[CLUSTER_COL].nunique()}), 跳过。"
                    )
                    continue

                x_cols = [exp_col, "age", "age2"]

                res = fe_reg_twoFE_city_cluster(
                    sub,
                    y_col=Y_VAR,
                    x_cols=x_cols,
                    fe1=ID_COL,
                    fe2="prov_year",
                    cluster_col=CLUSTER_COL,
                )

                row = res.loc[exp_col].copy()
                row["Y_var"] = Y_VAR
                row["window"] = window
                row["T"] = T
                row["exposure"] = exp_col
                row["sample"] = sample_name
                row["N"] = len(sub)
                row["N_id"] = sub[ID_COL].nunique()
                row["N_year"] = sub[YEAR_COL].nunique()
                row["N_city"] = sub[CLUSTER_COL].nunique()

                print("\n" + "=" * 40)
                print(
                    f"[RESULT] (prov×year FE, city cluster) Y={Y_VAR}, "
                    f"window={window}y, T={T}, sample={sample_name}"
                )
                print(res.loc[[exp_col]][["Estimate", "Pr(>|t|)"]])

                all_rows.append(row)

    if not all_rows:
        print("[INFO] Notebook progress message.")
        return

    out_df = pd.DataFrame(all_rows)
    out_df = out_df[
        [
            "Y_var", "window", "T", "exposure", "sample",
            "Estimate", "Std. Error", "t value", "Pr(>|t|)",
            "2.5%", "97.5%",
            "N", "N_id", "N_year", "N_city",
        ]
    ].sort_values(["Y_var", "window", "T", "sample"])

    print("\n" + "=" * 60)
    print("[INFO] Notebook progress message.")
    print(out_df[["Y_var", "window", "T", "sample", "Estimate", "Pr(>|t|)"]])

    out_path = OUT_DIR / f"fe_{Y_VAR}_Tall_5_10_20_30y_pid12_provYearFE_cityCluster.csv"
    out_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    run_individual_fe_city_cluster()


# ------------------------------------------------------------------------------
# Notebook cell 10
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 06_result_summary_tables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt  # Original notebook comment normalized for the public code archive.

# =============================================================================

PANEL_MERGED = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/flood_health_result/"
    "charls_health_panel_60plus_with_index_Tall_5_10_20_30y.parquet"
)

OUT_DIR = PANEL_MERGED.parent

# Original notebook comment normalized for the public code archive.
#   "health_phys", "health_mental", "health_social", "health_index_z"
Y_VAR = "health_phys"

# Original notebook comment normalized for the public code archive.
T_LIST = [2, 5, 10, 20, 50, 100]
WINDOW_LIST = [5, 10, 20, 30]

# Original notebook comment normalized for the public code archive.
ID_COL = "pid12"
CLUSTER_COL = "city_code"   # Original notebook comment normalized for the public code archive.
YEAR_COL = "year"
PROV_COL = "province"       # Original notebook comment normalized for the public code archive.


# =============================================================================

def stars_for_p(p: float) -> str:
    """
    p<0.001 -> "****"
    p<0.05  -> "**"
    p<0.10  -> "*"
    else    -> ""
    """
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

def demean_two_fe(df, cols, fe1, fe2):
    """Archived notebook note for 06_result_summary_tables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
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
    """Archived notebook note for 06_result_summary_tables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    cols_needed = [y_col] + x_cols + [fe1, fe2, cluster_col]
    df = df.dropna(subset=cols_needed).copy()

    # Original notebook comment normalized for the public code archive.
    df = df[df[cluster_col].notna()].copy()
    if df.empty:
        raise ValueError("所有观测在 cluster_col 上都缺失，无法回归。")

    # Fixed-effects regression helper.
    df = demean_two_fe(df, [y_col] + x_cols, fe1=fe1, fe2=fe2)

    y = df[f"{y_col}_dm"].to_numpy()
    X = df[[f"{c}_dm" for c in x_cols]].to_numpy()

    # Original notebook comment normalized for the public code archive.
    df["cluster_group"] = pd.Categorical(df[cluster_col]).codes
    groups = df["cluster_group"].to_numpy()

    model = sm.OLS(y, X)
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": groups})

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


# =============================================================================

def run_individual_fe_city_cluster():
    print(f"[READ] merged 60+ panel: {PANEL_MERGED}")
    df = pd.read_parquet(PANEL_MERGED)

    # Original notebook comment normalized for the public code archive.
    df[Y_VAR] = pd.to_numeric(df[Y_VAR], errors="coerce")
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df[YEAR_COL] = pd.to_numeric(df[YEAR_COL], errors="coerce")

    # Original notebook comment normalized for the public code archive.
    df = df.dropna(subset=[Y_VAR, "age", ID_COL, PROV_COL, CLUSTER_COL, YEAR_COL]).copy()

    # Original notebook comment normalized for the public code archive.
    df["age2"] = df["age"] ** 2

    # Fixed-effects regression helper.
    df["prov_str"] = df[PROV_COL].astype(str).str.strip()
    df["prov_year"] = df["prov_str"] + "_" + df[YEAR_COL].astype(int).astype(str)

    # Original notebook comment normalized for the public code archive.
    df["urban_nbs"] = pd.to_numeric(df["urban_nbs"], errors="coerce").fillna(0).astype(int)
    grp_urban = df.groupby(ID_COL)["urban_nbs"].mean()
    df = df.merge(
        (grp_urban > 0.5).astype(int).rename("urban_group"),
        on=ID_COL,
        how="left",
    )

    print("[INFO] Notebook progress message.")
    print(df[[ID_COL, "urban_group"]].drop_duplicates()["urban_group"].value_counts())

    # Original notebook comment normalized for the public code archive.
    waves_per_id = df.groupby(ID_COL)[YEAR_COL].nunique()
    keep_ids = waves_per_id[waves_per_id >= 2].index
    df = df[df[ID_COL].isin(keep_ids)].copy()
    print(
        f"[INFO] 至少有 2 个波次的 {ID_COL} 数: {df[ID_COL].nunique()}, "
        f"总行数: {len(df)}, 年份数: {df[YEAR_COL].nunique()}"
    )

    # Original notebook comment normalized for the public code archive.
    sample_specs = {
        "all": None,
        "urban": 1,
        "rural": 0,
    }

    all_rows = []

    for window in WINDOW_LIST:
        exposure_cols = {T: f"share_flood_T{T}_{window}y" for T in T_LIST}

        for T, exp_col in exposure_cols.items():
            if exp_col not in df.columns:
                print("[INFO] Notebook progress message.")
                continue

            for sample_name, group_val in sample_specs.items():
                if group_val is None:
                    sub = df.copy()
                else:
                    sub = df[df["urban_group"] == group_val].copy()

                # Original notebook comment normalized for the public code archive.
                waves_sub = sub.groupby(ID_COL)[YEAR_COL].nunique()
                keep_ids_sub = waves_sub[waves_sub >= 2].index
                sub = sub[sub[ID_COL].isin(keep_ids_sub)].copy()

                if len(sub) < 100 or sub[CLUSTER_COL].nunique() < 10:
                    print(
                        f"[WARN] window={window}, T={T}, sample={sample_name} 样本量或城市数过小 "
                        f"(N={len(sub)}, N_city={sub[CLUSTER_COL].nunique()}), 跳过。"
                    )
                    continue

                x_cols = [exp_col, "age", "age2"]

                res = fe_reg_twoFE_city_cluster(
                    sub,
                    y_col=Y_VAR,
                    x_cols=x_cols,
                    fe1=ID_COL,
                    fe2="prov_year",
                    cluster_col=CLUSTER_COL,
                )

                row = res.loc[exp_col].copy()
                row["Y_var"] = Y_VAR
                row["window"] = window
                row["T"] = T
                row["exposure"] = exp_col
                row["sample"] = sample_name
                row["N"] = len(sub)
                row["N_id"] = sub[ID_COL].nunique()
                row["N_year"] = sub[YEAR_COL].nunique()
                row["N_city"] = sub[CLUSTER_COL].nunique()

                print("\n" + "=" * 40)
                print(
                    f"[RESULT] (prov×year FE, city cluster) Y={Y_VAR}, "
                    f"window={window}y, T={T}, sample={sample_name}"
                )
                print(res.loc[[exp_col]][["Estimate", "Pr(>|t|)"]])

                all_rows.append(row)

    if not all_rows:
        print("[INFO] Notebook progress message.")
        return None

    out_df = pd.DataFrame(all_rows)
    out_df = out_df[
        [
            "Y_var", "window", "T", "exposure", "sample",
            "Estimate", "Std. Error", "t value", "Pr(>|t|)",
            "2.5%", "97.5%",
            "N", "N_id", "N_year", "N_city",
        ]
    ].sort_values(["Y_var", "window", "T", "sample"])

    print("\n" + "=" * 60)
    print("[INFO] Notebook progress message.")
    print(out_df[["Y_var", "window", "T", "sample", "Estimate", "Pr(>|t|)"]])

    out_path = OUT_DIR / f"fe_{Y_VAR}_Tall_5_10_20_30y_pid12_provYearFE_cityCluster.csv"
    out_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    return out_df


# =============================================================================

def plot_intensity_by_sample(result_df: pd.DataFrame, sample: str = "all"):
    """Archived notebook note for 06_result_summary_tables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sub = result_df[
        (result_df["Y_var"] == Y_VAR) &
        (result_df["sample"] == sample)
    ].copy()

    if sub.empty:
        print("[INFO] Notebook progress message.")
        return

    # Original notebook comment normalized for the public code archive.
    y_min = sub["Estimate"].min()
    y_max = sub["Estimate"].max()
    if not np.isfinite(y_min) or not np.isfinite(y_max):
        y_min, y_max = -0.5, 0.5
    pad = 0.1 * (y_max - y_min if y_max > y_min else 1.0)
    y_lower, y_upper = y_min - pad, y_max + pad

    plt.figure(figsize=(6, 4))

    for T in sorted(sub["T"].unique()):
        tmp = sub[sub["T"] == T].sort_values("window")

        x_vals = tmp["window"].values
        y_vals = tmp["Estimate"].values
        p_vals = tmp["Pr(>|t|)"].values

        # Original notebook comment normalized for the public code archive.
        plt.plot(
            x_vals,
            y_vals,
            marker="o",
            label=f"T={T}"
        )

        # Original notebook comment normalized for the public code archive.
        y_range = y_upper - y_lower
        offset = 0.03 * y_range  # Original notebook comment normalized for the public code archive.
        for x, y, p in zip(x_vals, y_vals, p_vals):
            s = stars_for_p(p)
            if s:
                plt.text(
                    x,
                    y + offset,
                    s,
                    ha="center",
                    va="bottom",
                    fontsize=10
                )

    plt.axhline(0, linestyle="--", linewidth=1)
    plt.xlabel("滚动窗口长度（年）")
    plt.ylabel(f"{Y_VAR} 的强度效应系数 β")
    plt.title(f"强度型洪水暴露效应：sample={sample}")
    plt.legend(title="返回期 T")
    plt.ylim(y_lower, y_upper)
    plt.tight_layout()
    plt.show()  # Original notebook comment normalized for the public code archive.


# ========== main ==========

if __name__ == "__main__":
    # Original notebook comment normalized for the public code archive.
    result_df = run_individual_fe_city_cluster()

    # Original notebook comment normalized for the public code archive.
    if result_df is not None:
        plot_intensity_by_sample(result_df, sample="all")
        plot_intensity_by_sample(result_df, sample="rural")
        plot_intensity_by_sample(result_df, sample="urban")


# ------------------------------------------------------------------------------
# Notebook cell 11
# ------------------------------------------------------------------------------
fe_health_index_z_Tall_5_10_20_30y_pid12_provYearFE_cityCluster


# ------------------------------------------------------------------------------
# Notebook cell 18
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 06_result_summary_tables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt

# =============================================================================

PANEL_MERGED = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/flood_health_result/"
    "charls_health_panel_60plus_with_index_Tall_5_10_20_30y.parquet"
)

OUT_DIR = PANEL_MERGED.parent

# Original notebook comment normalized for the public code archive.
#   "health_phys", "health_mental", "health_social", "health_index_z"
Y_VAR = "health_index_z"

# Original notebook comment normalized for the public code archive.
T_LIST = [2, 5, 10, 20, 50, 100]
WINDOW_LIST = [5, 10, 20, 30]

# Original notebook comment normalized for the public code archive.
ID_COL = "pid12"
CLUSTER_COL = "city_code"   # Original notebook comment normalized for the public code archive.
YEAR_COL = "year"
PROV_COL = "province"

# Original notebook comment normalized for the public code archive.
BASE_YEAR_FOR_TREND = 2011


# =============================================================================

def stars_for_p(p: float) -> str:
    """
    p<0.001 -> "****"
    p<0.05  -> "**"
    p<0.10  -> "*"
    else    -> ""
    """
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

def demean_two_fe(df, cols, fe1, fe2):
    """Archived notebook note for 06_result_summary_tables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
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
    """Archived notebook note for 06_result_summary_tables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    x_cols = list(x_cols)
    cols_needed = [y_col] + x_cols + [fe1, fe2, cluster_col]
    df = df.dropna(subset=cols_needed).copy()

    # Original notebook comment normalized for the public code archive.
    df = df[df[cluster_col].notna()].copy()
    if df.empty:
        raise ValueError("所有观测在 cluster_col 上都缺失，无法回归。")

    # Fixed-effects regression helper.
    df = demean_two_fe(df, [y_col] + x_cols, fe1=fe1, fe2=fe2)

    y = df[f"{y_col}_dm"].to_numpy()
    X = df[[f"{c}_dm" for c in x_cols]].to_numpy()

    # Original notebook comment normalized for the public code archive.
    df["cluster_group"] = pd.Categorical(df[cluster_col]).codes
    groups = df["cluster_group"].to_numpy()

    model = sm.OLS(y, X)
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": groups})

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


# =============================================================================

def run_individual_fe_city_cluster():
    print(f"[READ] merged 60+ panel: {PANEL_MERGED}")
    df = pd.read_parquet(PANEL_MERGED)

    # Original notebook comment normalized for the public code archive.
    df[Y_VAR] = pd.to_numeric(df[Y_VAR], errors="coerce")
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df[YEAR_COL] = pd.to_numeric(df[YEAR_COL], errors="coerce")
    df[CLUSTER_COL] = pd.to_numeric(df[CLUSTER_COL], errors="coerce")

    # Original notebook comment normalized for the public code archive.
    df = df.dropna(subset=[Y_VAR, "age", ID_COL, PROV_COL, CLUSTER_COL, YEAR_COL]).copy()

    # Original notebook comment normalized for the public code archive.
    df["age2"] = df["age"] ** 2

    # Fixed-effects regression helper.
    df["prov_str"] = df[PROV_COL].astype(str).str.strip()
    df["prov_year"] = df["prov_str"] + "_" + df[YEAR_COL].astype(int).astype(str)

    # Original notebook comment normalized for the public code archive.
    df["urban_nbs"] = pd.to_numeric(df["urban_nbs"], errors="coerce").fillna(0).astype(int)
    grp_urban = df.groupby(ID_COL)["urban_nbs"].mean()
    df = df.merge(
        (grp_urban > 0.5).astype(int).rename("urban_group"),
        on=ID_COL,
        how="left",
    )

    # Original notebook comment normalized for the public code archive.
    waves_per_id = df.groupby(ID_COL)[YEAR_COL].nunique()
    keep_ids = waves_per_id[waves_per_id >= 2].index
    df = df[df[ID_COL].isin(keep_ids)].copy()

    print(
        f"[INFO] 至少有 2 个波次的 {ID_COL} 数: {df[ID_COL].nunique()}, "
        f"总行数: {len(df)}, 年份数: {df[YEAR_COL].nunique()}, "
        f"城市数: {df[CLUSTER_COL].nunique()}"
    )

    # =============================================================================
    df["year_centered"] = df[YEAR_COL] - BASE_YEAR_FOR_TREND
    d_city = pd.get_dummies(df[CLUSTER_COL].astype("Int64").astype("category"),
                            prefix="trend_city")
    trend_df = d_city.multiply(df["year_centered"].to_numpy()[:, None])
    trend_cols = list(trend_df.columns)
    df = pd.concat([df, trend_df], axis=1)

    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    sample_specs = {
        "all": None,
        "urban": 1,
        "rural": 0,
    }

    all_rows = []

    for window in WINDOW_LIST:
        exposure_cols = {T: f"share_flood_T{T}_{window}y" for T in T_LIST}

        for T, exp_col in exposure_cols.items():
            if exp_col not in df.columns:
                print("[INFO] Notebook progress message.")
                continue

            for sample_name, group_val in sample_specs.items():
                if group_val is None:
                    sub = df.copy()
                else:
                    sub = df[df["urban_group"] == group_val].copy()

                # Original notebook comment normalized for the public code archive.
                waves_sub = sub.groupby(ID_COL)[YEAR_COL].nunique()
                keep_ids_sub = waves_sub[waves_sub >= 2].index
                sub = sub[sub[ID_COL].isin(keep_ids_sub)].copy()

                if len(sub) < 100 or sub[CLUSTER_COL].nunique() < 10:
                    print(
                        f"[WARN] window={window}, T={T}, sample={sample_name} "
                        f"样本量或城市数过小 (N={len(sub)}, N_city={sub[CLUSTER_COL].nunique()}), 跳过。"
                    )
                    continue

                # Original notebook comment normalized for the public code archive.
                x_cols = [exp_col, "age", "age2"] + trend_cols

                res = fe_reg_twoFE_city_cluster(
                    sub,
                    y_col=Y_VAR,
                    x_cols=x_cols,
                    fe1=ID_COL,
                    fe2="prov_year",
                    cluster_col=CLUSTER_COL,
                )

                row = res.loc[exp_col].copy()
                row["Y_var"] = Y_VAR
                row["window"] = window
                row["T"] = T
                row["exposure"] = exp_col
                row["sample"] = sample_name
                row["N"] = len(sub)
                row["N_id"] = sub[ID_COL].nunique()
                row["N_year"] = sub[YEAR_COL].nunique()
                row["N_city"] = sub[CLUSTER_COL].nunique()

                print("\n" + "=" * 40)
                print(
                    f"[RESULT] (prov×year FE, city trend, city cluster) "
                    f"Y={Y_VAR}, window={window}y, T={T}, sample={sample_name}"
                )
                print(res.loc[[exp_col]][["Estimate", "Pr(>|t|)"]])

                all_rows.append(row)

    if not all_rows:
        print("[INFO] Notebook progress message.")
        return None

    out_df = pd.DataFrame(all_rows)
    out_df = out_df[
        [
            "Y_var", "window", "T", "exposure", "sample",
            "Estimate", "Std. Error", "t value", "Pr(>|t|)",
            "2.5%", "97.5%",
            "N", "N_id", "N_year", "N_city",
        ]
    ].sort_values(["Y_var", "window", "T", "sample"])

    print("\n" + "=" * 60)
    print("[INFO] Notebook progress message.")
    print(out_df[["Y_var", "window", "T", "sample", "Estimate", "Pr(>|t|)"]])

    out_path = OUT_DIR / f"fe_{Y_VAR}_Tall_5_10_20_30y_pid12_provYearFE_cityTrend_cityCluster.csv"
    out_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")

    return out_df


# =============================================================================

def plot_intensity_by_sample(result_df: pd.DataFrame, sample: str = "all"):
    """Archived notebook note for 06_result_summary_tables.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sub = result_df[
        (result_df["Y_var"] == Y_VAR) &
        (result_df["sample"] == sample)
    ].copy()

    if sub.empty:
        print("[INFO] Notebook progress message.")
        return

    # Original notebook comment normalized for the public code archive.
    y_min = sub["Estimate"].min()
    y_max = sub["Estimate"].max()
    if not np.isfinite(y_min) or not np.isfinite(y_max):
        y_min, y_max = -0.5, 0.5
    pad = 0.1 * (y_max - y_min if y_max > y_min else 1.0)
    y_lower, y_upper = y_min - pad, y_max + pad
    y_range = y_upper - y_lower

    plt.figure(figsize=(6, 4))

    for T in sorted(sub["T"].unique()):
        tmp = sub[sub["T"] == T].sort_values("window")

        x_vals = tmp["window"].values
        y_vals = tmp["Estimate"].values
        p_vals = tmp["Pr(>|t|)"].values

        plt.plot(
            x_vals,
            y_vals,
            marker="o",
            label=f"T={T}"
        )

        # Original notebook comment normalized for the public code archive.
        offset = 0.03 * y_range
        for x, y, p in zip(x_vals, y_vals, p_vals):
            s = stars_for_p(p)
            if s:
                plt.text(
                    x,
                    y + offset,
                    s,
                    ha="center",
                    va="bottom",
                    fontsize=10
                )

    plt.axhline(0, linestyle="--", linewidth=1)
    plt.xlabel("滚动窗口长度（年）")
    plt.ylabel(f"{Y_VAR} 的强度效应系数 β")
    plt.title(f"强度型洪水暴露效应（含城市线性趋势）：sample={sample}")
    plt.legend(title="返回期 T")
    plt.ylim(y_lower, y_upper)
    plt.tight_layout()
    plt.show()


# ========== main ==========

if __name__ == "__main__":
    res_df = run_individual_fe_city_cluster()

    if res_df is not None:
        plot_intensity_by_sample(res_df, sample="all")
        plot_intensity_by_sample(res_df, sample="rural")
        plot_intensity_by_sample(res_df, sample="urban")


# ------------------------------------------------------------------------------
# Notebook cell 19
# ------------------------------------------------------------------------------
fe_health_index_z_Tall_5_10_20_30y_pid12_provYearFE_cityTrend_cityCluster
