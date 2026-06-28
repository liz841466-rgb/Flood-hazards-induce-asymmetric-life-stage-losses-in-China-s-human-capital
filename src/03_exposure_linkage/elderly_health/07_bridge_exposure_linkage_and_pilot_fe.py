#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 07_bridge_exposure_linkage_and_pilot_fe.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 6
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 07_bridge_exposure_linkage_and_pilot_fe.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import pandas as pd
from pyfixest.estimation import feols

# =============================================================================

# Original notebook comment normalized for the public code archive.
PANEL_60 = Path(
    "/home/ll/jupyter_notebook/gis_data/OLDER/CHARLS/health/charls_outputs_60plus/"
    "charls_health_panel_60plus_collapsed.parquet"
)

# Original notebook comment normalized for the public code archive.
FLOOD_5Y = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/flood_health_result/"
    "city_flood_T10_5y_1980_2020.parquet"
)

OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/flood_health_result"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_PANEL_MERGED = OUT_DIR / "charls_health_panel_60plus_T10_5y.parquet"
OUT_FE_SUMMARY   = OUT_DIR / "fe_health_T10_5y_results.csv"


def merge_panel_flood():
    print(f"[READ] panel: {PANEL_60}")
    panel = pd.read_parquet(PANEL_60)

    print(f"[READ] flood 5y: {FLOOD_5Y}")
    f5 = pd.read_parquet(FLOOD_5Y)

    # City-level processing note.
    panel["city_code"] = pd.to_numeric(panel["city_code"], errors="coerce")
    f5["city_code"] = pd.to_numeric(f5["city_code"], errors="coerce")

    # City-level processing note.
    merged = panel.merge(
        f5[["city_code", "year",
            "num_flood_T10_5y",
            "share_flood_T10_5y",
            "any_flood_T10_5y"]],
        how="left",
        on=["city_code", "year"],
        validate="m:1",
    )

    # Original notebook comment normalized for the public code archive.
    for c in ["num_flood_T10_5y", "share_flood_T10_5y", "any_flood_T10_5y"]:
        if c in merged.columns:
            merged[c] = merged[c].fillna(0)

    print("[INFO] Notebook progress message.")
    merged.to_parquet(OUT_PANEL_MERGED, index=False)
    print("[INFO] Notebook progress message.")

    return merged


def run_fe_reg(df: pd.DataFrame):
    # Original notebook comment normalized for the public code archive.
    df["age2"] = df["age"] ** 2

    # Original notebook comment normalized for the public code archive.
    df = df.dropna(subset=["share_flood_T10_5y", "health_z", "age"])

    # Fixed-effects regression helper.
    counts = df.groupby("ID12")["year"].nunique()
    keep_ids = counts[counts >= 2].index
    df = df[df["ID12"].isin(keep_ids)].copy()

    print(
        f"[INFO] 用于 FE 回归的样本量: {len(df)}, "
        f"个体数: {df['ID12'].nunique()}, 年份数: {df['year'].nunique()}"
    )

    # Original notebook comment normalized for the public code archive.
    # health_z_it = β * share_flood_T10_5y_ct + γ1 age_it + γ2 age_it^2 + α_i + λ_t + ε_it
    fml = "health_z ~ share_flood_T10_5y + age + age2 | ID12 + year"

    fit = feols(fml, data=df, vcov={"CRV1": "ID12"})  # Original notebook comment normalized for the public code archive.

    res = fit.tidy()
    print(res)

    # Original notebook comment normalized for the public code archive.
    res.to_csv(OUT_FE_SUMMARY, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")


def main():
    merged = merge_panel_flood()
    run_fe_reg(merged)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 9
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 07_bridge_exposure_linkage_and_pilot_fe.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm

# =============================================================================

# Original notebook comment normalized for the public code archive.
PANEL_60 = Path(
    "/home/ll/jupyter_notebook/gis_data/OLDER/CHARLS/health/charls_outputs_60plus/"
    "charls_health_panel_60plus_collapsed.parquet"
)

# Original notebook comment normalized for the public code archive.
FLOOD_5Y_ALLT = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/flood_health_result/"
    "city_flood_Tall_5y_1980_2020.parquet"
)

OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/flood_health_result"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_PANEL_MERGED = OUT_DIR / "charls_health_panel_60plus_Tall_5y.parquet"
OUT_FE_SUMMARY   = OUT_DIR / "fe_health_Tall_5y_urban_rural_results.csv"

T_LIST = [2, 5, 10, 20, 50, 100]


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def twoway_fe_reg(df, y_col, x_cols, id_col="ID12", t_col="year"):
    """Archived notebook note for 07_bridge_exposure_linkage_and_pilot_fe.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()

    # Original notebook comment normalized for the public code archive.
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
def merge_panel_flood_allT():
    print(f"[READ] panel: {PANEL_60}")
    panel = pd.read_parquet(PANEL_60)

    print(f"[READ] flood 5y (all T): {FLOOD_5Y_ALLT}")
    f5 = pd.read_parquet(FLOOD_5Y_ALLT)

    # City-level processing note.
    panel["city_code"] = pd.to_numeric(panel["city_code"], errors="coerce")
    f5["city_code"] = pd.to_numeric(f5["city_code"], errors="coerce")

    # City-level processing note.
    exp_cols = [c for c in f5.columns if "flood_T" in c and c.endswith("_5y")]
    keep_cols = ["city_code", "year"] + exp_cols

    merged = panel.merge(
        f5[keep_cols],
        how="left",
        on=["city_code", "year"],
        validate="m:1",
    )

    # Original notebook comment normalized for the public code archive.
    for c in exp_cols:
        merged[c] = merged[c].fillna(0)

    print("[INFO] Notebook progress message.")
    merged.to_parquet(OUT_PANEL_MERGED, index=False)
    print("[INFO] Notebook progress message.")

    return merged


# ================================
# Fixed-effects regression helper.
# ================================
def run_fe_multiT_urban_rural(df: pd.DataFrame):
    df = df.copy()

    # Original notebook comment normalized for the public code archive.
    df = df.dropna(subset=["health_z", "age", "urban_nbs"]).copy()
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df = df.dropna(subset=["age"]).copy()
    df["age2"] = df["age"] ** 2

    # =============================================================================
    df["urban_nbs"] = pd.to_numeric(df["urban_nbs"], errors="coerce").fillna(0).astype(int)
    grp_urban = df.groupby("ID12")["urban_nbs"].mean()
    # Original notebook comment normalized for the public code archive.
    urban_group = (grp_urban > 0.5).astype(int).rename("urban_group")
    df = df.merge(urban_group, on="ID12", how="left")

    print("[INFO] Notebook progress message.")
    print(df[["ID12", "urban_group"]].drop_duplicates()["urban_group"].value_counts())

    # Original notebook comment normalized for the public code archive.
    waves_per_id = df.groupby("ID12")["year"].nunique()
    keep_ids = waves_per_id[waves_per_id >= 2].index
    df = df[df["ID12"].isin(keep_ids)].copy()
    print(
        f"[INFO] 至少有 2 个波次的 ID 数: {df['ID12'].nunique()}, "
        f"总行数: {len(df)}, 年份数: {df['year'].nunique()}"
    )

    # Original notebook comment normalized for the public code archive.
    exposure_cols = {T: f"share_flood_T{T}_5y" for T in T_LIST}

    # Original notebook comment normalized for the public code archive.
    sample_specs = {
        "all": None,
        "urban": 1,
        "rural": 0,
    }

    all_rows = []

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
            waves_sub = sub.groupby("ID12")["year"].nunique()
            keep_ids_sub = waves_sub[waves_sub >= 2].index
            sub = sub[sub["ID12"].isin(keep_ids_sub)].copy()

            if len(sub) < 100:
                print("[INFO] Notebook progress message.")
                continue

            print("\n" + "=" * 60)
            print("[INFO] Notebook progress message.")
            print(
                f"[INFO] N = {len(sub)}, ID 数 = {sub['ID12'].nunique()}, "
                f"年份数 = {sub['year'].nunique()}"
            )

            x_cols = [exp_col, "age", "age2"]
            res = twoway_fe_reg(
                sub,
                y_col="health_z",
                x_cols=x_cols,
                id_col="ID12",
                t_col="year",
            )

            # Original notebook comment normalized for the public code archive.
            row = res.loc[exp_col].copy()
            row["T"] = T
            row["exposure"] = exp_col
            row["sample"] = sample_name
            row["N"] = len(sub)
            row["N_id"] = sub["ID12"].nunique()
            row["N_year"] = sub["year"].nunique()

            print(res.loc[[exp_col]])

            all_rows.append(row)

    if not all_rows:
        print("[INFO] Notebook progress message.")
        return

    out_df = pd.DataFrame(all_rows)
    out_df = out_df[
        [
            "T", "exposure", "sample",
            "Estimate", "Std. Error", "t value", "Pr(>|t|)",
            "2.5%", "97.5%",
            "N", "N_id", "N_year",
        ]
    ]
    out_df.sort_values(["T", "sample"], inplace=True)

    print("\n" + "=" * 60)
    print("[INFO] Notebook progress message.")
    print(out_df)

    out_df.to_csv(OUT_FE_SUMMARY, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def main():
    merged = merge_panel_flood_allT()
    run_fe_multiT_urban_rural(merged)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 10
# ------------------------------------------------------------------------------
# Display only Estimate and Pr(>|t|) for all, urban, and rural sample subsets.
