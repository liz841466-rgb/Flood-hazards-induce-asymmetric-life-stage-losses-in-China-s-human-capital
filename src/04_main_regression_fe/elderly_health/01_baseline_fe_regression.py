#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 01_baseline_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 9
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 01_baseline_fe_regression.

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
    """Archived notebook note for 01_baseline_fe_regression.

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
# Notebook cell 11
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import pandas as pd
import numpy as np
import statsmodels.api as sm

PANEL_MERGED = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/flood_health_result/"
    "charls_health_panel_60plus_with_index_Tall_5_10_20_30y.parquet"
)

def city_year_aggregate_analysis():
    print(f"[READ] merged 60+ panel: {PANEL_MERGED}")
    df = pd.read_parquet(PANEL_MERGED)

    # City-level processing note.
    df["city_code"] = pd.to_numeric(df.get("city_code"), errors="coerce")
    df["year"] = pd.to_numeric(df["year"], errors="coerce")

    df = df.dropna(subset=["city_code", "year", "health_phys"]).copy()

    # Original notebook comment normalized for the public code archive.
    flood_cols = [
        "share_flood_T2_5y", "share_flood_T5_5y",
        "share_flood_T2_20y", "share_flood_T2_30y"
    ]
    flood_cols = [c for c in flood_cols if c in df.columns]

    print("[INFO] Notebook progress message.", flood_cols)

    # City-level processing note.
    agg = (
        df.groupby(["city_code", "year"], as_index=False)
          .agg(
              health_phys_mean=("health_phys", "mean"),
              health_index_z_mean=("health_index_z", "mean"),
              N_person=("pid12", "nunique"),
              **{c: (c, "mean") for c in flood_cols}
          )
    )

    print("[INFO] Notebook progress message.", agg.shape)
    print("[INFO] Notebook progress message.", agg["year"].value_counts().sort_index())

    # Original notebook comment normalized for the public code archive.
    corr_cols = ["health_phys_mean"] + flood_cols
    print("[INFO] Notebook progress message.")
    print(agg[corr_cols].corr())

    # Fixed-effects regression helper.
    y = agg["health_phys_mean"].to_numpy()
    X = agg[["share_flood_T2_30y"]].copy() if "share_flood_T2_30y" in agg.columns else agg[flood_cols[:1]]
    X = sm.add_constant(X)

    ols = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": agg["city_code"].to_numpy()})
    print("[INFO] Notebook progress message.")
    print(ols.summary().tables[1])

    # Fixed-effects regression helper.
    # year_dum = pd.get_dummies(agg["year"].astype(int), prefix="y", drop_first=True)
    # X2 = pd.concat([agg[["share_flood_T2_30y"]], year_dum], axis=1)
    # X2 = sm.add_constant(X2)
    # ols_fe = sm.OLS(y, X2).fit(cov_type="cluster", cov_kwds={"groups": agg["city_code"].to_numpy()})
    # print("\n[OLS+Year FE] city-year: health_phys_mean ~ share_flood_T2_30y + year FE")
    # print(ols_fe.summary().tables[1])


if __name__ == "__main__":
    city_year_aggregate_analysis()


# ------------------------------------------------------------------------------
# Notebook cell 13
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 01_baseline_fe_regression.

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

ROOT_FLOOD = PANEL_MERGED.parent
OUT_DIR = ROOT_FLOOD
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_FE_YEARFE = OUT_DIR / "fe_health_phys_Tall_5_10_20_30y_pid12_yearFE.csv"

# Original notebook comment normalized for the public code archive.
T_LIST = [2, 5, 10, 20, 50, 100]
WINDOW_LIST = [5, 10, 20, 30]

# Original notebook comment normalized for the public code archive.
ID_COL = "pid12"


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def twoway_fe_reg(df, y_col, x_cols, id_col=ID_COL, t_col="year"):
    """Archived notebook note for 01_baseline_fe_regression.

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
def load_and_preprocess_panel():
    print(f"[READ] merged 60+ panel: {PANEL_MERGED}")
    df = pd.read_parquet(PANEL_MERGED)
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df["year"] = pd.to_numeric(df["year"], errors="coerce")

    # Original notebook comment normalized for the public code archive.
    df = df[df["age"] >= 60].copy()
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    if "health_phys" not in df.columns:
        raise KeyError("面板中不存在 health_phys，请确认健康指数脚本已生成该列。")

    # Original notebook comment normalized for the public code archive.
    df = df.dropna(subset=["health_phys", "age", "urban_nbs", ID_COL, "year"]).copy()
    df[ID_COL] = df[ID_COL].astype(str)
    df["age2"] = df["age"] ** 2

    # Original notebook comment normalized for the public code archive.
    df["urban_nbs"] = pd.to_numeric(df["urban_nbs"], errors="coerce").fillna(0).astype(int)
    grp_urban = df.groupby(ID_COL)["urban_nbs"].mean()
    urban_group = (grp_urban > 0.5).astype(int).rename("urban_group")
    df = df.merge(urban_group, on=ID_COL, how="left")

    print("[INFO] Notebook progress message.")
    print(df[[ID_COL, "urban_group"]].drop_duplicates()["urban_group"].value_counts())

    # Original notebook comment normalized for the public code archive.
    waves_per_id = df.groupby(ID_COL)["year"].nunique()
    keep_ids = waves_per_id[waves_per_id >= 2].index
    df = df[df[ID_COL].isin(keep_ids)].copy()
    print(
        f"[INFO] 至少有 2 个波次的 pid12 数: {df[ID_COL].nunique()}, "
        f"总行数: {len(df)}, 年份数: {df['year'].nunique()}"
    )

    return df


# ================================
# Fixed-effects regression helper.
# ================================
def run_fe_health_phys_yearFE(df: pd.DataFrame):
    df = df.copy()

    # Original notebook comment normalized for the public code archive.
    sample_specs = {
        "all": None,
        "urban": 1,
        "rural": 0,
    }

    all_rows = []

    for window in WINDOW_LIST:
        for T in T_LIST:
            exp_col = f"share_flood_T{T}_{window}y"
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
                    y_col="health_phys",
                    x_cols=x_cols,
                    id_col=ID_COL,
                    t_col="year",   # Fixed-effects regression helper.
                )

                row = res.loc[exp_col].copy()
                row["window"] = window
                row["T"] = T
                row["exposure"] = exp_col
                row["sample"] = sample_name
                row["N"] = len(sub)
                row["N_id"] = sub[ID_COL].nunique()
                row["N_year"] = sub["year"].nunique()

                # Original notebook comment normalized for the public code archive.
                print("\n" + "=" * 40)
                print(f"[RESULT] (year FE) window={window}y, T={T}, sample={sample_name}")
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

    out_df.to_csv(OUT_FE_YEARFE, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")


# ================================
# 4. main
# ================================
def main():
    df = load_and_preprocess_panel()
    run_fe_health_phys_yearFE(df)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 16
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 01_baseline_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm

# =====================================================
# Original notebook comment normalized for the public code archive.
# =====================================================

# Original notebook comment normalized for the public code archive.
PANEL_MERGED = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/flood_health_result/"
    "charls_health_panel_60plus_with_index_Tall_5_10_20_30y.parquet"
)

# Original notebook comment normalized for the public code archive.
Y_VAR = "health_phys"

# Original notebook comment normalized for the public code archive.
T_LIST = [2, 5, 10, 20, 50, 100]
WINDOW_LIST = [5, 10, 20, 30]

# Original notebook comment normalized for the public code archive.
ID_COL = "pid12"

# Original notebook comment normalized for the public code archive.
ROOT_FLOOD = PANEL_MERGED.parent
OUT_DIR = ROOT_FLOOD
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_FE_PROVYEARFE = OUT_DIR / f"fe_{Y_VAR}_Tall_5_10_20_30y_pid12_provYearFE.csv"


# =====================================================
# Original notebook comment normalized for the public code archive.
# =====================================================
def twoway_fe_reg(df, y_col, x_cols, id_col=ID_COL, t_col="year"):
    """Archived notebook note for 01_baseline_fe_regression.

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


# =====================================================
# Original notebook comment normalized for the public code archive.
# =====================================================
def load_and_preprocess_panel():
    print(f"[READ] merged 60+ panel: {PANEL_MERGED}")
    df = pd.read_parquet(PANEL_MERGED)
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df["year"] = pd.to_numeric(df["year"], errors="coerce")

    # Original notebook comment normalized for the public code archive.
    df = df[df["age"] >= 60].copy()
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    if Y_VAR not in df.columns:
        raise KeyError(f"面板中不存在因变量 {Y_VAR}，请检查或在配置区修改 Y_VAR。")

    # Province-level processing note.
    need_cols = [Y_VAR, "age", "urban_nbs", ID_COL, "year", "province"]
    missing = [c for c in need_cols if c not in df.columns]
    if missing:
        raise KeyError(f"面板缺少必要列: {missing}")

    df = df.dropna(subset=[Y_VAR, "age", "urban_nbs", ID_COL, "year", "province"]).copy()
    df[ID_COL] = df[ID_COL].astype(str)
    df["age2"] = df["age"] ** 2

    # Original notebook comment normalized for the public code archive.
    df["urban_nbs"] = pd.to_numeric(df["urban_nbs"], errors="coerce").fillna(0).astype(int)
    grp_urban = df.groupby(ID_COL)["urban_nbs"].mean()
    urban_group = (grp_urban > 0.5).astype(int).rename("urban_group")
    df = df.merge(urban_group, on=ID_COL, how="left")

    print("[INFO] Notebook progress message.")
    print(df[[ID_COL, "urban_group"]].drop_duplicates()["urban_group"].value_counts())

    # Original notebook comment normalized for the public code archive.
    waves_per_id = df.groupby(ID_COL)["year"].nunique()
    keep_ids = waves_per_id[waves_per_id >= 2].index
    df = df[df[ID_COL].isin(keep_ids)].copy()
    print(
        f"[INFO] 至少有 2 个波次的 pid12 数: {df[ID_COL].nunique()}, "
        f"总行数: {len(df)}, 年份数: {df['year'].nunique()}"
    )

    return df


# =====================================================
# Fixed-effects regression helper.
# =====================================================
def add_province_year_fe(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 01_baseline_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    df = df.copy()

    # Original notebook comment normalized for the public code archive.
    df["province_fe"] = df["province"].astype(str).str.strip()

    # Archived notebook metadata.
    df["year_int"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    # Province-level processing note.
    df = df.dropna(subset=["province_fe", "year_int"]).copy()

    # Fixed-effects regression helper.
    df["prov_year_fe"] = df["province_fe"] + "_" + df["year_int"].astype(str)

    print(
        f"[INFO] 省份×年份 FE 维度数: {df['prov_year_fe'].nunique()} "
        f"(省份数={df['province_fe'].nunique()}, 年份数={df['year_int'].nunique()})"
    )

    return df


# =====================================================
# Fixed-effects regression helper.
# =====================================================
def run_fe_health_provYearFE(df: pd.DataFrame):
    df = add_province_year_fe(df)

    # Original notebook comment normalized for the public code archive.
    sample_specs = {
        "all": None,
        "urban": 1,
        "rural": 0,
    }

    all_rows = []

    for window in WINDOW_LIST:
        for T in T_LIST:
            exp_col = f"share_flood_T{T}_{window}y"
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
                        f"[WARN] (prov×year FE) window={window}, T={T}, {sample_name} 样本量过小 "
                        f"(N={len(sub)}), 跳过。"
                    )
                    continue

                x_cols = [exp_col, "age", "age2"]
                res = twoway_fe_reg(
                    sub,
                    y_col=Y_VAR,
                    x_cols=x_cols,
                    id_col=ID_COL,
                    t_col="prov_year_fe",   # Fixed-effects regression helper.
                )

                row = res.loc[exp_col].copy()
                row["Y"] = Y_VAR
                row["window"] = window
                row["T"] = T
                row["exposure"] = exp_col
                row["sample"] = sample_name
                row["N"] = len(sub)
                row["N_id"] = sub[ID_COL].nunique()
                row["N_provyear"] = sub["prov_year_fe"].nunique()

                print("\n" + "=" * 40)
                print(
                    f"[RESULT] (prov×year FE) Y={Y_VAR}, window={window}y, "
                    f"T={T}, sample={sample_name}"
                )
                print(res.loc[[exp_col]][["Estimate", "Pr(>|t|)"]])

                all_rows.append(row)

    if not all_rows:
        print("[INFO] Notebook progress message.")
        return

    out_df = pd.DataFrame(all_rows)
    out_df = out_df[
        [
            "Y", "window", "T", "exposure", "sample",
            "Estimate", "Std. Error", "t value", "Pr(>|t|)",
            "2.5%", "97.5%",
            "N", "N_id", "N_provyear",
        ]
    ]
    out_df.sort_values(["Y", "window", "T", "sample"], inplace=True)

    print("\n" + "=" * 60)
    print("[INFO] Notebook progress message.")
    print(out_df[["Y", "window", "T", "sample", "Estimate", "Pr(>|t|)"]])

    out_df.to_csv(OUT_FE_PROVYEARFE, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")


# =====================================================
# 5. main
# =====================================================
def main():
    df = load_and_preprocess_panel()
    run_fe_health_provYearFE(df)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 20
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 01_baseline_fe_regression.

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
    """Archived notebook note for 01_baseline_fe_regression.

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
    """Archived notebook note for 01_baseline_fe_regression.

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
# Notebook cell 24
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 01_baseline_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm

PANEL_MERGED = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/flood_health_result/"
    "charls_health_panel_60plus_with_index_Tall_5_10_20_30y.parquet"
)

OUT_DIR = PANEL_MERGED.parent

Y_VAR = "health_index_z"   # Original notebook comment normalized for the public code archive.
T_LIST = [2, 5, 10, 20, 50, 100]
WINDOW_LIST = [5, 10, 20, 30]

YEAR_COL = "year"
PROV_COL = "province"
CITY_COL = "city_code"


def demean_two_fe(df, cols, fe1, fe2):
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


def fe_citylevel_cityFE_provYearFE(df, y_col, x_cols):
    """Archived notebook note for 01_baseline_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    cols_needed = [y_col, "city_code", "prov_year"] + x_cols
    df = df.dropna(subset=cols_needed).copy()
    if df.empty:
        raise ValueError("用于 city-year FE 回归的数据为空。")

    df = demean_two_fe(df, [y_col] + x_cols, fe1="city_code", fe2="prov_year")

    y = df[f"{y_col}_dm"].to_numpy()
    X = df[[f"{c}_dm" for c in x_cols]].to_numpy()

    df["cluster_group"] = pd.Categorical(df["city_code"]).codes
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


def run_cityyear_fe():
    print(f"[READ] merged 60+ panel: {PANEL_MERGED}")
    df = pd.read_parquet(PANEL_MERGED)

    # Original notebook comment normalized for the public code archive.
    df[Y_VAR] = pd.to_numeric(df[Y_VAR], errors="coerce")
    df[YEAR_COL] = pd.to_numeric(df[YEAR_COL], errors="coerce")

    # City-level processing note.
    # City-level processing note.
    df = df.dropna(subset=[Y_VAR, YEAR_COL, CITY_COL]).copy()

    # Original notebook comment normalized for the public code archive.
    df["prov_str"] = df[PROV_COL].astype(str).str.strip()
    df["prov_year"] = df["prov_str"] + "_" + df[YEAR_COL].astype(int).astype(str)

    # Original notebook comment normalized for the public code archive.
    exp_cols_all = [
        c for c in df.columns
        if c.startswith("share_flood_T") and any(c.endswith(f"_{w}y") for w in WINDOW_LIST)
    ]

    # City-level processing note.
    agg_dict = {Y_VAR: "mean"}
    for c in exp_cols_all:
        agg_dict[c] = "first"

    city_year = (
        df.groupby([CITY_COL, PROV_COL, YEAR_COL], as_index=False)
        .agg(agg_dict)
        .copy()
    )

    city_year.rename(
        columns={Y_VAR: f"{Y_VAR}_mean"},
        inplace=True,
    )

    # Fixed-effects regression helper.
    city_year["prov_str"] = city_year[PROV_COL].astype(str).str.strip()
    city_year["prov_year"] = (
        city_year["prov_str"]
        + "_"
        + city_year[YEAR_COL].astype(int).astype(str)
    )

    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.", city_year[YEAR_COL].value_counts().sort_index())

    all_rows = []

    for window in WINDOW_LIST:
        for T in T_LIST:
            exp_col = f"share_flood_T{T}_{window}y"
            if exp_col not in city_year.columns:
                print("[INFO] Notebook progress message.")
                continue

            # City-level processing note.
            if len(city_year) == 0 or city_year[CITY_COL].nunique() < 10:
                print(
                    f"[WARN] window={window}, T={T}，city-year 样本过少 "
                    f"(N_cityyear={len(city_year)}, N_city={city_year[CITY_COL].nunique()})，跳过。"
                )
                continue

            x_cols = [exp_col]
            res = fe_citylevel_cityFE_provYearFE(
                city_year,
                y_col=f"{Y_VAR}_mean",
                x_cols=x_cols,
            )

            row = res.loc[exp_col].copy()
            row["Y_var"] = Y_VAR
            row["window"] = window
            row["T"] = T
            row["exposure"] = exp_col
            row["N_cityyear"] = len(city_year)
            row["N_city"] = city_year[CITY_COL].nunique()

            print("\n" + "=" * 40)
            print(
                f"[RESULT] city-year FE: Ȳ={Y_VAR}_mean, "
                f"window={window}y, T={T}"
            )
            print(res.loc[[exp_col]][["Estimate", "Pr(>|t|)"]])

            all_rows.append(row)

    if not all_rows:
        print("[INFO] Notebook progress message.")
        return

    out_df = pd.DataFrame(all_rows)
    out_df = out_df[
        [
            "Y_var", "window", "T", "exposure",
            "Estimate", "Std. Error", "t value", "Pr(>|t|)",
            "2.5%", "97.5%",
            "N_cityyear", "N_city",
        ]
    ].sort_values(["Y_var", "window", "T"])

    print("\n" + "=" * 60)
    print("[INFO] Notebook progress message.")
    print(out_df[["Y_var", "window", "T", "Estimate", "Pr(>|t|)"]])

    out_path = OUT_DIR / f"fe_cityyear_{Y_VAR}_Tall_5_10_20_30y_cityFE_provYearFE_cityCluster.csv"
    out_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    run_cityyear_fe()


# ------------------------------------------------------------------------------
# Notebook cell 28
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 01_baseline_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm

# =============================================================================

PANEL_PATH = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/flood_health_result/"
    "charls_health_panel_60plus_with_index_Tall_5_10_20_30y.parquet"
)

ID_COL    = "pid12"
CITY_COL  = "city_code"
PROV_COL  = "province"
YEAR_COL  = "year"

# Original notebook comment normalized for the public code archive.
Y_VAR = "health_index_z"

# Original notebook comment normalized for the public code archive.
WINDOW_LIST     = [5, 10, 20, 30]
EXTREME_T_LIST  = [20, 50, 100]

OUT_PATH = PANEL_PATH.parent / f"fe_{Y_VAR}_anyflood_citytrend_individual.csv"


# =============================================================================

def fe_reg_two_way_with_cluster(df, y_col, x_cols,
                                id_col, fe2_col,
                                cluster_col):
    """Archived notebook note for 01_baseline_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

    # Original notebook comment normalized for the public code archive.
    needed_cols = [id_col, fe2_col, cluster_col, y_col] + x_cols
    work = df[needed_cols].copy()

    # Original notebook comment normalized for the public code archive.
    for col in [y_col] + x_cols:
        work[col] = pd.to_numeric(work[col], errors="coerce")

    # Original notebook comment normalized for the public code archive.
    mask_y = work[y_col].notna()
    mask_x = work[x_cols].notna().any(axis=1)
    work = work[mask_y & mask_x].copy()
    if work.empty:
        raise ValueError("没有有效观测用于回归（全部为缺失或常数）")

    cols = [y_col] + x_cols

    # Original notebook comment normalized for the public code archive.
    mu_all = work[cols].mean()

    # Fixed-effects regression helper.
    g_id  = work.groupby(id_col)[cols]
    g_fe2 = work.groupby(fe2_col)[cols]

    # Original notebook comment normalized for the public code archive.
    vals      = work[cols]
    vals_id   = g_id.transform("mean")
    vals_fe2  = g_fe2.transform("mean")
    vals_dm   = vals - vals_id - vals_fe2 + mu_all  # Original notebook comment normalized for the public code archive.

    # Original notebook comment normalized for the public code archive.
    y = vals_dm[y_col].to_numpy(dtype="float64")
    X = vals_dm[x_cols].to_numpy(dtype="float64")

    # City-level processing note.
    groups = work[cluster_col].astype("category").cat.codes.to_numpy()

    model = sm.OLS(y, X)
    fit = model.fit(
        cov_type="cluster",
        cov_kwds={"groups": groups},
    )

    coefs  = fit.params
    ses    = fit.bse
    tvals  = fit.tvalues
    pvals  = fit.pvalues
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


# =============================================================================

def run_individual_fe_citytrend_anyflood():

    print(f"[READ] merged 60+ panel: {PANEL_PATH}")
    df = pd.read_parquet(PANEL_PATH)

    # Original notebook comment normalized for the public code archive.
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df = df[(df["age"] >= 60) & df[Y_VAR].notna()].copy()

    # Original notebook comment normalized for the public code archive.
    df[YEAR_COL] = pd.to_numeric(df[YEAR_COL], errors="coerce")
    df = df[df[YEAR_COL].notna()].copy()

    # province / city
    df[PROV_COL] = df[PROV_COL].astype(str).str.strip()
    if CITY_COL not in df.columns:
        raise KeyError(f"缺少列 {CITY_COL}")
    df[CITY_COL] = df[CITY_COL].astype(str).str.strip()
    df = df[df[CITY_COL] != ""].copy()

    # Fixed-effects regression helper.
    df["prov_year"] = (
        df[PROV_COL].astype(str).str.strip()
        + "_"
        + df[YEAR_COL].astype(int).astype(str)
    )

    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    df["age2"] = df["age"] ** 2

    # Original notebook comment normalized for the public code archive.
    base_year = int(df[YEAR_COL].min())
    df["time_trend"] = df[YEAR_COL] - base_year

    # City-level processing note.
    city_dummies = pd.get_dummies(
        df[CITY_COL].astype("category"),
        prefix="city",
        drop_first=False
    )
    city_trends = city_dummies.mul(df["time_trend"], axis=0).astype("float64")
    city_trends.columns = [c + "_trend" for c in city_trends.columns]
    df = pd.concat([df, city_trends], axis=1)
    TREND_COLS = list(city_trends.columns)

    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    any_cols_created = []
    for window in WINDOW_LIST:
        for T in EXTREME_T_LIST:
            share_col = f"share_flood_T{T}_{window}y"
            if share_col not in df.columns:
                print("[INFO] Notebook progress message.")
                continue
            any_col = f"any_flood_T{T}_{window}y"
            df[any_col] = (
                pd.to_numeric(df[share_col], errors="coerce")
                .fillna(0)
                .gt(0)
                .astype(int)
            )
            any_cols_created.append(any_col)

    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    df["urban_nbs"] = pd.to_numeric(df["urban_nbs"], errors="coerce").fillna(0).astype(int)
    grp_urban   = df.groupby(ID_COL)["urban_nbs"].mean()
    urban_group = (grp_urban > 0.5).astype(int).rename("urban_group")
    df = df.merge(urban_group, on=ID_COL, how="left")

    # Original notebook comment normalized for the public code archive.
    waves_per_id = df.groupby(ID_COL)[YEAR_COL].nunique()
    keep_ids = waves_per_id[waves_per_id >= 2].index
    df = df[df[ID_COL].isin(keep_ids)].copy()

    print("[INFO] Notebook progress message.")

    sample_specs = {
        "all":   None,
        "urban": 1,
        "rural": 0,
    }

    all_rows = []

    # =============================================================================
    for window in WINDOW_LIST:
        for T in EXTREME_T_LIST:
            any_col = f"any_flood_T{T}_{window}y"
            if any_col not in df.columns:
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

                if len(sub) < 100:
                    print("[INFO] Notebook progress message.")
                    continue

                x_cols = [any_col, "age", "age2"] + TREND_COLS

                res = fe_reg_two_way_with_cluster(
                    sub,
                    y_col=Y_VAR,
                    x_cols=x_cols,
                    id_col=ID_COL,
                    fe2_col="prov_year",
                    cluster_col=CITY_COL,
                )

                row = res.loc[any_col].copy()
                row["Y_var"]   = Y_VAR
                row["window"]  = window
                row["T"]       = T
                row["exposure"] = any_col
                row["sample"]   = sample_name
                row["N"]        = len(sub)
                row["N_id"]     = sub[ID_COL].nunique()
                row["N_city"]   = sub[CITY_COL].nunique()

                print("\n" + "=" * 40)
                print(f"[RESULT] (pid FE + prov×year FE + city trend, city cluster) "
                      f"Y={Y_VAR}, window={window}y, T={T}, sample={sample_name}")
                print(res.loc[[any_col]][["Estimate", "Pr(>|t|)"]])

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
            "N", "N_id", "N_city",
        ]
    ].sort_values(["Y_var", "window", "T", "sample"])

    print("\n" + "=" * 60)
    print("[INFO] Notebook progress message.")
    print(out_df[["Y_var", "window", "T", "sample", "Estimate", "Pr(>|t|)"]])

    out_df.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    run_individual_fe_citytrend_anyflood()


# ------------------------------------------------------------------------------
# Notebook cell 31
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 01_baseline_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

# =============================================================================

PANEL_PATH = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/flood_health_result/"
    "charls_health_panel_60plus_with_index_Tall_5_10_20_30y.parquet"
)

ID_COL    = "pid12"
CITY_COL  = "city_code"
PROV_COL  = "province"
YEAR_COL  = "year"

Y_VAR = "health_phys"                    # City-level processing note.
WINDOW_LIST = [5, 10, 20, 30]
EXTREME_T_LIST = [20, 50, 100]

OUT_PATH = PANEL_PATH.parent / f"fe_cityyear_{Y_VAR}_anyflood_cityFE_citytrend.csv"


def build_cityyear_panel_with_anyflood():
    """Archived notebook note for 01_baseline_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print(f"[READ] merged 60+ panel: {PANEL_PATH}")
    df = pd.read_parquet(PANEL_PATH)

    # Original notebook comment normalized for the public code archive.
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df = df[(df["age"] >= 60) & df[Y_VAR].notna()].copy()

    # Original notebook comment normalized for the public code archive.
    df[YEAR_COL] = pd.to_numeric(df[YEAR_COL], errors="coerce")
    df = df[df[YEAR_COL].notna()].copy()

    df[PROV_COL] = df[PROV_COL].astype(str).str.strip()
    df[CITY_COL] = df[CITY_COL].astype(str).str.strip()
    df = df[(df[CITY_COL] != "") & df[PROV_COL].notna()].copy()

    # City-level processing note.
    for window in WINDOW_LIST:
        for T in EXTREME_T_LIST:
            share_col = f"share_flood_T{T}_{window}y"
            if share_col not in df.columns:
                print("[INFO] Notebook progress message.")
                continue
            any_col = f"any_flood_T{T}_{window}y"
            df[any_col] = (pd.to_numeric(df[share_col], errors="coerce").fillna(0) > 0).astype(int)

    # City-level processing note.
    # Original notebook comment normalized for the public code archive.
    # City-level processing note.
    agg_dict = {Y_VAR: "mean"}
    for window in WINDOW_LIST:
        for T in EXTREME_T_LIST:
            any_col = f"any_flood_T{T}_{window}y"
            if any_col in df.columns:
                agg_dict[any_col] = "max"

    grouped = df.groupby([CITY_COL, PROV_COL, YEAR_COL]).agg(agg_dict).reset_index()
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    grouped["prov_year"] = (
        grouped[PROV_COL].astype(str).str.strip()
        + "_"
        + grouped[YEAR_COL].astype(int).astype(str)
    )
    base_year = int(grouped[YEAR_COL].min())
    grouped["time_trend"] = grouped[YEAR_COL] - base_year

    return grouped


def run_cityyear_fe_citytrend_anyflood():
    city_year = build_cityyear_panel_with_anyflood()
    if city_year.empty:
        print("[INFO] Notebook progress message.")
        return

    all_rows = []

    for window in WINDOW_LIST:
        for T in EXTREME_T_LIST:
            any_col = f"any_flood_T{T}_{window}y"
            if any_col not in city_year.columns:
                continue

            sub = city_year.copy()
            sub = sub[sub[any_col].notna() & sub[Y_VAR].notna()].copy()

            if len(sub) < 30:
                print("[INFO] Notebook progress message.")
                continue

            # City-level processing note.
            formula = (
                f"{Y_VAR} ~ {any_col} + "
                f"C({CITY_COL}) + C(prov_year) + C({CITY_COL}):time_trend"
            )

            print("\n" + "=" * 60)
            print("[INFO] Notebook progress message.")
            print(f"       formula: {formula}")

            model = smf.ols(formula, data=sub)
            fit = model.fit(
                cov_type="cluster",
                cov_kwds={"groups": sub[CITY_COL].astype("category").cat.codes},
            )

            if any_col not in fit.params.index:
                print("[INFO] Notebook progress message.")
                continue

            est = fit.params[any_col]
            se  = fit.bse[any_col]
            t   = fit.tvalues[any_col]
            p   = fit.pvalues[any_col]
            ci_low, ci_high = fit.conf_int().loc[any_col]

            print(f"[RESULT] (city FE + prov×year FE + city trend, city cluster) "
                  f"Y={Y_VAR}, window={window}y, T={T}")
            print(f"  {any_col}: Estimate={est:.6f}, p={p:.6f}")

            row = {
                "Y_var": Y_VAR,
                "window": window,
                "T": T,
                "exposure": any_col,
                "Estimate": est,
                "Std. Error": se,
                "t value": t,
                "Pr(>|t|)": p,
                "2.5%": ci_low,
                "97.5%": ci_high,
                "N_cityyear": len(sub),
                "N_city": sub[CITY_COL].nunique(),
            }
            all_rows.append(row)

    if not all_rows:
        print("[INFO] Notebook progress message.")
        return

    out_df = pd.DataFrame(all_rows).sort_values(["Y_var", "window", "T"])
    print("\n" + "=" * 60)
    print("[INFO] Notebook progress message.")
    print(out_df[["Y_var", "window", "T", "Estimate", "Pr(>|t|)"]])

    out_df.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    run_cityyear_fe_citytrend_anyflood()


# ------------------------------------------------------------------------------
# Notebook cell 35
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 01_baseline_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm


# =============================================================================
# Original notebook comment normalized for the public code archive.
PANEL_60PLUS = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/"
    "flood_health_result/charls_health_panel_60plus_with_index_Tall_5_10_20_30y.parquet"
)

# Original notebook comment normalized for the public code archive.
FLOOD_EVENTS = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/"
    "city_flood_events_T2_5_10_20_50_100_1980_2020.csv"
)

OUT_DIR = PANEL_60PLUS.parent
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Original notebook comment normalized for the public code archive.
Y_VAR    = "health_index_z"   # Original notebook comment normalized for the public code archive.
ID_COL   = "pid12"
YEAR_COL = "year"
CITY_COL = "city_code"
PROV_COL = "province"

# Original notebook comment normalized for the public code archive.
URBAN_COL = "urban_nbs"

# Fixed-effects regression helper.
BASE_YEAR_FOR_TREND = 2011  # city-specific trend = (year - BASE_YEAR_FOR_TREND) × city_dummies

# Original notebook comment normalized for the public code archive.
INTENSITY_T_LIST     = [20, 50, 100]
INTENSITY_WINDOW_LIST = [5, 10, 20, 30]

# Original notebook comment normalized for the public code archive.
ES_T_LIST   = [50, 100]    # Original notebook comment normalized for the public code archive.
ES_K_MIN    = -4           # Original notebook comment normalized for the public code archive.
ES_K_MAX    =  4           # Original notebook comment normalized for the public code archive.
ES_K_REF    = -1           # Original notebook comment normalized for the public code archive.


# ====================================================
# Fixed-effects regression helper.
# ====================================================
def fe_reg_two_way_with_cluster_fast(
    df: pd.DataFrame,
    y_col: str,
    x_cols,
    id_col: str,
    fe2_col: str,
    cluster_col: str | None = None,
):
    """Archived notebook note for 01_baseline_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

    x_cols = list(x_cols)
    used_cols = [y_col] + x_cols

    # Fixed-effects regression helper.
    df_use = df.dropna(subset=used_cols + [id_col, fe2_col]).copy()
    if df_use.empty:
        raise ValueError("fe_reg_two_way_with_cluster_fast: 有效样本为 0。")

    # Original notebook comment normalized for the public code archive.
    cols_for_dm = used_cols

    # Fixed-effects regression helper.
    g_id = df_use.groupby(id_col)[cols_for_dm].transform("mean")
    g_f2 = df_use.groupby(fe2_col)[cols_for_dm].transform("mean")
    mu_all = df_use[cols_for_dm].mean()

    # Original notebook comment normalized for the public code archive.
    dm = df_use[cols_for_dm] - g_id - g_f2 + mu_all

    y = dm[y_col].to_numpy()
    X = dm[x_cols].to_numpy()

    model = sm.OLS(y, X)

    if cluster_col is not None:
        groups = df_use[cluster_col].astype("category").cat.codes.to_numpy()
        fit = model.fit(cov_type="cluster", cov_kwds={"groups": groups})
    else:
        fit = model.fit()

    coefs = fit.params
    ses   = fit.bse
    tvals = fit.tvalues
    pvals = fit.pvalues
    ci_low, ci_high = fit.conf_int().T

    res = pd.DataFrame(
        {
            "Estimate":  coefs,
            "Std. Error": ses,
            "t value":   tvals,
            "Pr(>|t|)":  pvals,
            "2.5%":      ci_low,
            "97.5%":     ci_high,
        },
        index=x_cols,
    )

    # Original notebook comment normalized for the public code archive.
    n      = len(df_use)
    n_id   = df_use[id_col].nunique()
    n_year = df_use[YEAR_COL].nunique()

    return res, n, n_id, n_year


# ====================================================
# Original notebook comment normalized for the public code archive.
# ====================================================
def prepare_base_panel():
    """Archived notebook note for 01_baseline_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print(f"[READ] merged 60+ panel: {PANEL_60PLUS}")
    df = pd.read_parquet(PANEL_60PLUS)

    # Original notebook comment normalized for the public code archive.
    df["age"]  = pd.to_numeric(df["age"],  errors="coerce")
    df[YEAR_COL] = pd.to_numeric(df[YEAR_COL], errors="coerce")

    # Original notebook comment normalized for the public code archive.
    df = df[df["age"] >= 60].copy()

    # Original notebook comment normalized for the public code archive.
    df = df.dropna(subset=[Y_VAR, YEAR_COL, ID_COL, CITY_COL]).copy()

    # City-level processing note.
    df[CITY_COL] = pd.to_numeric(df[CITY_COL], errors="coerce").astype("Int64")

    # Fixed-effects regression helper.
    df[PROV_COL] = df[PROV_COL].astype(str).str.strip()
    df["prov_year"] = df[PROV_COL] + "_" + df[YEAR_COL].astype(int).astype(str)

    # Original notebook comment normalized for the public code archive.
    df["age2"] = df["age"] ** 2

    # Original notebook comment normalized for the public code archive.
    df[URBAN_COL] = pd.to_numeric(df[URBAN_COL], errors="coerce").fillna(0).astype(int)
    urban_mean = df.groupby(ID_COL)[URBAN_COL].mean()
    urban_group = (urban_mean > 0.5).astype(int).rename("urban_group")
    df = df.merge(urban_group, on=ID_COL, how="left")

    # Fixed-effects regression helper.
    waves_per_id = df.groupby(ID_COL)[YEAR_COL].nunique()
    keep_ids = waves_per_id[waves_per_id >= 2].index
    df = df[df[ID_COL].isin(keep_ids)].copy()

    print(
        f"[INFO] 样本量: {len(df)}, 不同 {ID_COL}: {df[ID_COL].nunique()}, "
        f"不同 city: {df[CITY_COL].nunique()}"
    )

    # =============================================================================
    # Archived notebook metadata.
    df["year_centered"] = df[YEAR_COL] - BASE_YEAR_FOR_TREND

    # Original notebook comment normalized for the public code archive.
    # City-level processing note.
    # Original notebook comment normalized for the public code archive.
    d_city = pd.get_dummies(df[CITY_COL].astype("category"), prefix="trend_city")
    trend_df = d_city.multiply(df["year_centered"].to_numpy()[:, None])

    trend_cols = list(trend_df.columns)
    df = pd.concat([df, trend_df], axis=1)

    print("[INFO] Notebook progress message.")

    return df, trend_cols


# ====================================================
# Original notebook comment normalized for the public code archive.
# ====================================================
def run_intensity_fe():
    """Archived notebook note for 01_baseline_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

    df, trend_cols = prepare_base_panel()

    sample_specs = {
        "all":   None,
        "urban": 1,
        "rural": 0,
    }

    results = []

    for window in INTENSITY_WINDOW_LIST:
        for T in INTENSITY_T_LIST:
            exp_col = f"share_flood_T{T}_{window}y"
            if exp_col not in df.columns:
                print("[INFO] Notebook progress message.")
                continue

            print("\n" + "=" * 40)
            print("[INFO] Notebook progress message.")

            for sample_name, gval in sample_specs.items():
                if gval is None:
                    sub = df.copy()
                else:
                    sub = df[df["urban_group"] == gval].copy()

                # Original notebook comment normalized for the public code archive.
                waves_sub = sub.groupby(ID_COL)[YEAR_COL].nunique()
                keep_ids_sub = waves_sub[waves_sub >= 2].index
                sub = sub[sub[ID_COL].isin(keep_ids_sub)].copy()

                if len(sub) < 200:
                    print(
                        f"[WARN] window={window}, T={T}, sample={sample_name} "
                        f"样本量过小 (N={len(sub)}), 跳过。"
                    )
                    continue

                x_cols = [exp_col, "age", "age2"] + trend_cols

                res, N, N_id, N_year = fe_reg_two_way_with_cluster_fast(
                    sub,
                    y_col=Y_VAR,
                    x_cols=x_cols,
                    id_col=ID_COL,
                    fe2_col="prov_year",
                    cluster_col=CITY_COL,
                )

                row = res.loc[exp_col].copy()
                row["Y_var"]  = Y_VAR
                row["window"] = window
                row["T"]      = T
                row["sample"] = sample_name
                row["N"]      = N
                row["N_id"]   = N_id
                row["N_year"] = N_year

                print("[INFO] Notebook progress message.")
                print(res.loc[[exp_col]][["Estimate", "Pr(>|t|)"]])

                results.append(row)

    if not results:
        print("[INFO] Notebook progress message.")
        return

    out_df = pd.DataFrame(results)
    out_df = out_df[
        [
            "Y_var", "window", "T", "sample",
            "Estimate", "Std. Error", "t value", "Pr(>|t|)",
            "2.5%", "97.5%",
            "N", "N_id", "N_year",
        ]
    ]
    out_df.sort_values(["Y_var", "window", "T", "sample"], inplace=True)

    print("\n" + "=" * 60)
    print("[INFO] Notebook progress message.")
    print(out_df[["Y_var", "window", "T", "sample", "Estimate", "Pr(>|t|)"]])

    out_path = OUT_DIR / "fe_health_phys_INTENSITY_shareflood_Tall_5_10_20_30y_pid12_provYear_citytrend_citycluster.csv"
    out_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")


# ====================================================
# Original notebook comment normalized for the public code archive.
# ====================================================
def build_event_timing(df: pd.DataFrame):
    """Archived notebook note for 01_baseline_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

    if not FLOOD_EVENTS.exists():
        raise FileNotFoundError(f"未找到洪水事件文件: {FLOOD_EVENTS}")

    flood = pd.read_csv(FLOOD_EVENTS)
    flood["year"] = pd.to_numeric(flood["year"], errors="coerce")
    flood[CITY_COL] = pd.to_numeric(flood[CITY_COL], errors="coerce").astype("Int64")

    # Original notebook comment normalized for the public code archive.
    cities_panel = df[CITY_COL].dropna().unique()
    flood = flood[flood[CITY_COL].isin(cities_panel)].copy()

    es_dummies_dict = {}

    for T in ES_T_LIST:
        colT = f"flood_ge_T{T}"
        if colT not in flood.columns:
            print("[INFO] Notebook progress message.")
            continue

        # City-level processing note.
        first_event = (
            flood.loc[flood[colT] == 1, [CITY_COL, "year"]]
            .groupby(CITY_COL)["year"]
            .min()
            .reset_index()
            .rename(columns={"year": f"first_event_T{T}"})
        )

        df = df.merge(first_event, on=CITY_COL, how="left")

        col_first = f"first_event_T{T}"
        col_etime = f"event_time_T{T}"

        df[col_etime] = df[YEAR_COL] - df[col_first]

        # Original notebook comment normalized for the public code archive.
        ks = [k for k in range(ES_K_MIN, ES_K_MAX + 1) if k != ES_K_REF]

        dummy_cols = []
        for k in ks:
            col_dummy = f"es_T{T}_k{k}"
            mask = (df[col_etime] == k).fillna(False)
            # Original notebook comment normalized for the public code archive.
            #df[col_dummy] = (df[col_etime] == k).astype(int)
            df[col_dummy] = mask.astype("int8")  # Original notebook comment normalized for the public code archive.
            dummy_cols.append(col_dummy)

        es_dummies_dict[T] = dummy_cols

        # Original notebook comment normalized for the public code archive.
        print("[INFO] Notebook progress message.")
        print(df[col_etime].value_counts(dropna=True).sort_index())

    return df, es_dummies_dict


def run_event_study():
    """Archived notebook note for 01_baseline_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

    # City-level processing note.
    df, trend_cols = prepare_base_panel()

    # Original notebook comment normalized for the public code archive.
    df, es_dummies_dict = build_event_timing(df)

    sample_specs = {
        "all":   None,
        "urban": 1,
        "rural": 0,
    }

    results = []

    for T, dummy_cols in es_dummies_dict.items():
        if not dummy_cols:
            continue

        print("\n" + "=" * 60)
        print("[INFO] Notebook progress message.")

        for sample_name, gval in sample_specs.items():
            if gval is None:
                sub = df.copy()
            else:
                sub = df[df["urban_group"] == gval].copy()

            # Original notebook comment normalized for the public code archive.
            waves_sub = sub.groupby(ID_COL)[YEAR_COL].nunique()
            keep_ids_sub = waves_sub[waves_sub >= 2].index
            sub = sub[sub[ID_COL].isin(keep_ids_sub)].copy()

            if len(sub) < 300:
                print(
                    f"[WARN] T={T}, sample={sample_name} 样本量过小 (N={len(sub)}), 跳过 event study。"
                )
                continue

            x_cols = dummy_cols + ["age", "age2"] + trend_cols

            res, N, N_id, N_year = fe_reg_two_way_with_cluster_fast(
                sub,
                y_col=Y_VAR,
                x_cols=x_cols,
                id_col=ID_COL,
                fe2_col="prov_year",
                cluster_col=CITY_COL,
            )

            # Original notebook comment normalized for the public code archive.
            for col in dummy_cols:
                k_str = col.split("k")[-1]
                try:
                    k_val = int(k_str)
                except ValueError:
                    k_val = np.nan

                row = res.loc[col].copy()
                row["Y_var"]  = Y_VAR
                row["T"]      = T
                row["k"]      = k_val
                row["sample"] = sample_name
                row["N"]      = N
                row["N_id"]   = N_id
                row["N_year"] = N_year

                results.append(row)

            print(f"[RESULT] (Event study) Y={Y_VAR}, T={T}, sample={sample_name}")
            print(res.loc[dummy_cols][["Estimate", "Pr(>|t|)"]])

    if not results:
        print("[INFO] Notebook progress message.")
        return

    out_df = pd.DataFrame(results)
    out_df = out_df[
        [
            "Y_var", "T", "k", "sample",
            "Estimate", "Std. Error", "t value", "Pr(>|t|)",
            "2.5%", "97.5%",
            "N", "N_id", "N_year",
        ]
    ]
    out_df.sort_values(["Y_var", "T", "sample", "k"], inplace=True)

    print("\n" + "=" * 60)
    print("[INFO] Notebook progress message.")
    print(out_df[["Y_var", "T", "sample", "k", "Estimate", "Pr(>|t|)"]])

    out_path = OUT_DIR / f"eventstudy_{Y_VAR}_T50_100_pid12_provYear_citytrend_citycluster.csv"
    out_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")


# ====================================================
# Original notebook comment normalized for the public code archive.
# ====================================================
if __name__ == "__main__":
    # Original notebook comment normalized for the public code archive.
    run_intensity_fe()

    # Original notebook comment normalized for the public code archive.
    run_event_study()


# ------------------------------------------------------------------------------
# Notebook cell 36
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 01_baseline_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm

# =============================================================================

# Original notebook comment normalized for the public code archive.
PANEL_MERGED = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/flood_health_result/"
    "charls_health_panel_60plus_with_index_Tall_5_10_20_30y.parquet"
)

# Original notebook comment normalized for the public code archive.
FLOOD_EVENTS = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/"
    "city_flood_events_T2_5_10_20_50_100_1980_2020.csv"
)

OUT_DIR = PANEL_MERGED.parent
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Original notebook comment normalized for the public code archive.
#   "health_phys", "health_mental", "health_social", "health_index_z"
Y_VAR = "health_index_z"

# Original notebook comment normalized for the public code archive.
T_LIST = [2, 5, 10, 20, 50, 100]
WINDOW_LIST = [5, 10, 20, 30]

# Original notebook comment normalized for the public code archive.
ES_T_LIST = [50, 100]   # Original notebook comment normalized for the public code archive.
ES_K_MIN = -4
ES_K_MAX = 4
ES_K_REF = -1           # Original notebook comment normalized for the public code archive.

# Original notebook comment normalized for the public code archive.
ID_COL = "pid12"
CLUSTER_COL = "city_code"   # Original notebook comment normalized for the public code archive.
YEAR_COL = "year"
PROV_COL = "province"       # Original notebook comment normalized for the public code archive.
URBAN_COL = "urban_nbs"     # Original notebook comment normalized for the public code archive.


# =============================================================================

def demean_two_fe(df: pd.DataFrame, cols, fe1: str, fe2: str):
    """Archived notebook note for 01_baseline_fe_regression.

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


def fe_reg_twoFE_city_cluster(
    df: pd.DataFrame,
    y_col: str,
    x_cols,
    fe1: str,
    fe2: str,
    cluster_col: str,
):
    """Archived notebook note for 01_baseline_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    x_cols = list(x_cols)
    cols_needed = [y_col] + x_cols + [fe1, fe2, cluster_col]
    df = df.dropna(subset=cols_needed).copy()

    # Original notebook comment normalized for the public code archive.
    df = df[df[cluster_col].notna()].copy()
    if df.empty:
        raise ValueError("所有观测在 cluster_col 上都缺失，无法回归。")

    # Fixed-effects regression helper.
    dm_cols = [y_col] + x_cols
    df = demean_two_fe(df, dm_cols, fe1=fe1, fe2=fe2)

    y = df[f"{y_col}_dm"].to_numpy()
    X = df[[f"{c}_dm" for c in x_cols]].to_numpy()

    # Original notebook comment normalized for the public code archive.
    df["_cluster_group"] = pd.Categorical(df[cluster_col]).codes
    groups = df["_cluster_group"].to_numpy()

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

def prepare_panel():
    """Archived notebook note for 01_baseline_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print(f"[READ] merged 60+ panel: {PANEL_MERGED}")
    df = pd.read_parquet(PANEL_MERGED)

    # Original notebook comment normalized for the public code archive.
    df[Y_VAR] = pd.to_numeric(df[Y_VAR], errors="coerce")
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df[YEAR_COL] = pd.to_numeric(df[YEAR_COL], errors="coerce")

    # Original notebook comment normalized for the public code archive.
    df = df.dropna(
        subset=[Y_VAR, "age", ID_COL, PROV_COL, CLUSTER_COL, YEAR_COL]
    ).copy()

    # Original notebook comment normalized for the public code archive.
    df["age2"] = df["age"] ** 2

    # Fixed-effects regression helper.
    df["prov_str"] = df[PROV_COL].astype(str).str.strip()
    df["prov_year"] = df["prov_str"] + "_" + df[YEAR_COL].astype(int).astype(str)

    # Original notebook comment normalized for the public code archive.
    df[URBAN_COL] = pd.to_numeric(df[URBAN_COL], errors="coerce").fillna(0).astype(int)
    grp_urban = df.groupby(ID_COL)[URBAN_COL].mean()
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
        f"总行数: {len(df)}, 年份数: {df[YEAR_COL].nunique()}, 城市数: {df[CLUSTER_COL].nunique()}"
    )

    return df


# =============================================================================

def run_intensity_fe_city_cluster(df: pd.DataFrame):
    """Archived notebook note for 01_baseline_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

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
                        f"[WARN] [INTENSITY] window={window}, T={T}, sample={sample_name} "
                        f"样本量或城市数过小 (N={len(sub)}, N_city={sub[CLUSTER_COL].nunique()}), 跳过。"
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
                    f"[RESULT][INTENSITY] Y={Y_VAR}, window={window}y, T={T}, sample={sample_name}"
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

    out_path = OUT_DIR / f"fe_{Y_VAR}_INTENSITY_Tall_5_10_20_30y_pid12_provYearFE_cityCluster.csv"
    out_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")

    return out_df


# =============================================================================

def build_event_timing(df: pd.DataFrame):
    """Archived notebook note for 01_baseline_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if not FLOOD_EVENTS.exists():
        raise FileNotFoundError(f"未找到洪水事件文件: {FLOOD_EVENTS}")

    flood = pd.read_csv(FLOOD_EVENTS)
    flood["year"] = pd.to_numeric(flood["year"], errors="coerce")
    flood[CLUSTER_COL] = pd.to_numeric(flood[CLUSTER_COL], errors="coerce")

    # Original notebook comment normalized for the public code archive.
    cities_panel = df[CLUSTER_COL].dropna().unique()
    flood = flood[flood[CLUSTER_COL].isin(cities_panel)].copy()

    es_dummies_dict = {}

    for T in ES_T_LIST:
        colT = f"flood_ge_T{T}"
        if colT not in flood.columns:
            print("[INFO] Notebook progress message.")
            continue

        # City-level processing note.
        first_event = (
            flood.loc[flood[colT] == 1, [CLUSTER_COL, "year"]]
            .groupby(CLUSTER_COL)["year"]
            .min()
            .reset_index()
            .rename(columns={"year": f"first_event_T{T}"})
        )

        df = df.merge(first_event, on=CLUSTER_COL, how="left")

        col_first = f"first_event_T{T}"
        col_etime = f"event_time_T{T}"

        df[col_etime] = df[YEAR_COL] - df[col_first]

        # Original notebook comment normalized for the public code archive.
        ks = [k for k in range(ES_K_MIN, ES_K_MAX + 1) if k != ES_K_REF]

        dummy_cols = []
        for k in ks:
            col_dummy = f"es_T{T}_k{k}"
            # Original notebook comment normalized for the public code archive.
            mask = (df[col_etime] == k).fillna(False)
            df[col_dummy] = mask.astype("int8")  # or int
            dummy_cols.append(col_dummy)

        es_dummies_dict[T] = dummy_cols

        print("[INFO] Notebook progress message.")
        print(df[col_etime].value_counts(dropna=True).sort_index())

    return df, es_dummies_dict


def run_event_study_city_cluster(df: pd.DataFrame):
    """Archived notebook note for 01_baseline_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

    # Original notebook comment normalized for the public code archive.
    df, es_dummies_dict = build_event_timing(df)

    sample_specs = {
        "all": None,
        "urban": 1,
        "rural": 0,
    }

    results = []

    for T, dummy_cols in es_dummies_dict.items():
        if not dummy_cols:
            continue

        print("\n" + "=" * 60)
        print("[INFO] Notebook progress message.")

        for sample_name, gval in sample_specs.items():
            if gval is None:
                sub = df.copy()
            else:
                sub = df[df["urban_group"] == gval].copy()

            # Original notebook comment normalized for the public code archive.
            waves_sub = sub.groupby(ID_COL)[YEAR_COL].nunique()
            keep_ids_sub = waves_sub[waves_sub >= 2].index
            sub = sub[sub[ID_COL].isin(keep_ids_sub)].copy()

            if len(sub) < 300 or sub[CLUSTER_COL].nunique() < 10:
                print(
                    f"[WARN] [EVENT] T={T}, sample={sample_name} 样本量或城市数过小 "
                    f"(N={len(sub)}, N_city={sub[CLUSTER_COL].nunique()}), 跳过 event study。"
                )
                continue

            x_cols = dummy_cols + ["age", "age2"]

            res = fe_reg_twoFE_city_cluster(
                sub,
                y_col=Y_VAR,
                x_cols=x_cols,
                fe1=ID_COL,
                fe2="prov_year",
                cluster_col=CLUSTER_COL,
            )

            # Original notebook comment normalized for the public code archive.
            for col in dummy_cols:
                k_str = col.split("k")[-1]
                try:
                    k_val = int(k_str)
                except ValueError:
                    k_val = np.nan

                row = res.loc[col].copy()
                row["Y_var"] = Y_VAR
                row["T"] = T
                row["k"] = k_val
                row["sample"] = sample_name
                row["N"] = len(sub)
                row["N_id"] = sub[ID_COL].nunique()
                row["N_year"] = sub[YEAR_COL].nunique()
                row["N_city"] = sub[CLUSTER_COL].nunique()

                results.append(row)

            print(f"[RESULT] [EVENT] Y={Y_VAR}, T={T}, sample={sample_name}")
            print(res.loc[dummy_cols][["Estimate", "Pr(>|t|)"]])

    if not results:
        print("[INFO] Notebook progress message.")
        return None

    out_df = pd.DataFrame(results)
    out_df = out_df[
        [
            "Y_var", "T", "k", "sample",
            "Estimate", "Std. Error", "t value", "Pr(>|t|)",
            "2.5%", "97.5%",
            "N", "N_id", "N_year", "N_city",
        ]
    ].sort_values(["Y_var", "T", "sample", "k"])

    print("\n" + "=" * 60)
    print("[INFO] Notebook progress message.")
    print(out_df[["Y_var", "T", "sample", "k", "Estimate", "Pr(>|t|)"]])

    out_path = OUT_DIR / f"eventstudy_{Y_VAR}_T{'_'.join(map(str, ES_T_LIST))}_pid12_provYearFE_cityCluster.csv"
    out_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")

    return out_df


# =============================================================================

if __name__ == "__main__":
    df_panel = prepare_panel()

    # Fixed-effects regression helper.
    run_intensity_fe_city_cluster(df_panel)

    # Fixed-effects regression helper.
    run_event_study_city_cluster(df_panel)


# ------------------------------------------------------------------------------
# Notebook cell 37
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 01_baseline_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt

# =============================================================================

# Original notebook comment normalized for the public code archive.
PANEL_MERGED = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/flood_health_result/"
    "charls_health_panel_60plus_with_index_Tall_5_10_20_30y.parquet"
)

# Original notebook comment normalized for the public code archive.
FLOOD_EVENTS = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/"
    "city_flood_events_T2_5_10_20_50_100_1980_2020.csv"
)

OUT_DIR = PANEL_MERGED.parent
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Original notebook comment normalized for the public code archive.
#   "health_phys", "health_mental", "health_social", "health_index_z"
Y_VAR = "health_index_z"

# Original notebook comment normalized for the public code archive.
T_LIST = [2, 5, 10, 20, 50, 100]
WINDOW_LIST = [5, 10, 20, 30]

# Original notebook comment normalized for the public code archive.
ES_T_LIST = [50, 100]   # Original notebook comment normalized for the public code archive.
ES_K_MIN = -4
ES_K_MAX = 4
ES_K_REF = -1           # Original notebook comment normalized for the public code archive.

# Original notebook comment normalized for the public code archive.
ID_COL = "pid12"
CLUSTER_COL = "city_code"   # Original notebook comment normalized for the public code archive.
YEAR_COL = "year"
PROV_COL = "province"       # Original notebook comment normalized for the public code archive.
URBAN_COL = "urban_nbs"     # Original notebook comment normalized for the public code archive.


# =============================================================================

def demean_two_fe(df: pd.DataFrame, cols, fe1: str, fe2: str):
    """Archived notebook note for 01_baseline_fe_regression.

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


def fe_reg_twoFE_city_cluster(
    df: pd.DataFrame,
    y_col: str,
    x_cols,
    fe1: str,
    fe2: str,
    cluster_col: str,
):
    """Archived notebook note for 01_baseline_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    x_cols = list(x_cols)
    cols_needed = [y_col] + x_cols + [fe1, fe2, cluster_col]
    df = df.dropna(subset=cols_needed).copy()

    # Original notebook comment normalized for the public code archive.
    df = df[df[cluster_col].notna()].copy()
    if df.empty:
        raise ValueError("所有观测在 cluster_col 上都缺失，无法回归。")

    # Fixed-effects regression helper.
    dm_cols = [y_col] + x_cols
    df = demean_two_fe(df, dm_cols, fe1=fe1, fe2=fe2)

    y = df[f"{y_col}_dm"].to_numpy()
    X = df[[f"{c}_dm" for c in x_cols]].to_numpy()

    # Original notebook comment normalized for the public code archive.
    df["_cluster_group"] = pd.Categorical(df[cluster_col]).codes
    groups = df["_cluster_group"].to_numpy()

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

def prepare_panel():
    """Archived notebook note for 01_baseline_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print(f"[READ] merged 60+ panel: {PANEL_MERGED}")
    df = pd.read_parquet(PANEL_MERGED)

    # Original notebook comment normalized for the public code archive.
    df[Y_VAR] = pd.to_numeric(df[Y_VAR], errors="coerce")
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df[YEAR_COL] = pd.to_numeric(df[YEAR_COL], errors="coerce")

    # Original notebook comment normalized for the public code archive.
    df = df.dropna(
        subset=[Y_VAR, "age", ID_COL, PROV_COL, CLUSTER_COL, YEAR_COL]
    ).copy()

    # Original notebook comment normalized for the public code archive.
    df["age2"] = df["age"] ** 2

    # Fixed-effects regression helper.
    df["prov_str"] = df[PROV_COL].astype(str).str.strip()
    df["prov_year"] = df["prov_str"] + "_" + df[YEAR_COL].astype(int).astype(str)

    # Original notebook comment normalized for the public code archive.
    df[URBAN_COL] = pd.to_numeric(df[URBAN_COL], errors="coerce").fillna(0).astype(int)
    grp_urban = df.groupby(ID_COL)[URBAN_COL].mean()
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
        f"总行数: {len(df)}, 年份数: {df[YEAR_COL].nunique()}, 城市数: {df[CLUSTER_COL].nunique()}"
    )

    return df


# =============================================================================

def run_intensity_fe_city_cluster(df: pd.DataFrame):
    """Archived notebook note for 01_baseline_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

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
                        f"[WARN] [INTENSITY] window={window}, T={T}, sample={sample_name} "
                        f"样本量或城市数过小 (N={len(sub)}, N_city={sub[CLUSTER_COL].nunique()}), 跳过。"
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
                    f"[RESULT][INTENSITY] Y={Y_VAR}, window={window}y, T={T}, sample={sample_name}"
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

    out_path = OUT_DIR / f"fe_{Y_VAR}_INTENSITY_Tall_5_10_20_30y_pid12_provYearFE_cityCluster.csv"
    out_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")

    return out_df


# =============================================================================

def build_event_timing(df: pd.DataFrame):
    """Archived notebook note for 01_baseline_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if not FLOOD_EVENTS.exists():
        raise FileNotFoundError(f"未找到洪水事件文件: {FLOOD_EVENTS}")

    flood = pd.read_csv(FLOOD_EVENTS)
    flood["year"] = pd.to_numeric(flood["year"], errors="coerce")
    flood[CLUSTER_COL] = pd.to_numeric(flood[CLUSTER_COL], errors="coerce")

    # Original notebook comment normalized for the public code archive.
    cities_panel = df[CLUSTER_COL].dropna().unique()
    flood = flood[flood[CLUSTER_COL].isin(cities_panel)].copy()

    es_dummies_dict = {}

    for T in ES_T_LIST:
        colT = f"flood_ge_T{T}"
        if colT not in flood.columns:
            print("[INFO] Notebook progress message.")
            continue

        # City-level processing note.
        first_event = (
            flood.loc[flood[colT] == 1, [CLUSTER_COL, "year"]]
            .groupby(CLUSTER_COL)["year"]
            .min()
            .reset_index()
            .rename(columns={"year": f"first_event_T{T}"})
        )

        df = df.merge(first_event, on=CLUSTER_COL, how="left")

        col_first = f"first_event_T{T}"
        col_etime = f"event_time_T{T}"

        df[col_etime] = df[YEAR_COL] - df[col_first]

        # Original notebook comment normalized for the public code archive.
        ks = [k for k in range(ES_K_MIN, ES_K_MAX + 1) if k != ES_K_REF]

        dummy_cols = []
        for k in ks:
            col_dummy = f"es_T{T}_k{k}"
            # Original notebook comment normalized for the public code archive.
            mask = (df[col_etime] == k).fillna(False)
            df[col_dummy] = mask.astype("int8")  # or int
            dummy_cols.append(col_dummy)

        es_dummies_dict[T] = dummy_cols

        print("[INFO] Notebook progress message.")
        print(df[col_etime].value_counts(dropna=True).sort_index())

    return df, es_dummies_dict


def run_event_study_city_cluster(df: pd.DataFrame):
    """Archived notebook note for 01_baseline_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

    # Original notebook comment normalized for the public code archive.
    df, es_dummies_dict = build_event_timing(df)

    sample_specs = {
        "all": None,
        "urban": 1,
        "rural": 0,
    }

    results = []

    for T, dummy_cols in es_dummies_dict.items():
        if not dummy_cols:
            continue

        print("\n" + "=" * 60)
        print("[INFO] Notebook progress message.")

        for sample_name, gval in sample_specs.items():
            if gval is None:
                sub = df.copy()
            else:
                sub = df[df["urban_group"] == gval].copy()

            # Original notebook comment normalized for the public code archive.
            waves_sub = sub.groupby(ID_COL)[YEAR_COL].nunique()
            keep_ids_sub = waves_sub[waves_sub >= 2].index
            sub = sub[sub[ID_COL].isin(keep_ids_sub)].copy()

            if len(sub) < 300 or sub[CLUSTER_COL].nunique() < 10:
                print(
                    f"[WARN] [EVENT] T={T}, sample={sample_name} 样本量或城市数过小 "
                    f"(N={len(sub)}, N_city={sub[CLUSTER_COL].nunique()}), 跳过 event study。"
                )
                continue

            x_cols = dummy_cols + ["age", "age2"]

            res = fe_reg_twoFE_city_cluster(
                sub,
                y_col=Y_VAR,
                x_cols=x_cols,
                fe1=ID_COL,
                fe2="prov_year",
                cluster_col=CLUSTER_COL,
            )

            # Original notebook comment normalized for the public code archive.
            for col in dummy_cols:
                k_str = col.split("k")[-1]
                try:
                    k_val = int(k_str)
                except ValueError:
                    k_val = np.nan

                row = res.loc[col].copy()
                row["Y_var"] = Y_VAR
                row["T"] = T
                row["k"] = k_val
                row["sample"] = sample_name
                row["N"] = len(sub)
                row["N_id"] = sub[ID_COL].nunique()
                row["N_year"] = sub[YEAR_COL].nunique()
                row["N_city"] = sub[CLUSTER_COL].nunique()

                results.append(row)

            print(f"[RESULT] [EVENT] Y={Y_VAR}, T={T}, sample={sample_name}")
            print(res.loc[dummy_cols][["Estimate", "Pr(>|t|)"]])

    if not results:
        print("[INFO] Notebook progress message.")
        return None

    out_df = pd.DataFrame(results)
    out_df = out_df[
        [
            "Y_var", "T", "k", "sample",
            "Estimate", "Std. Error", "t value", "Pr(>|t|)",
            "2.5%", "97.5%",
            "N", "N_id", "N_year", "N_city",
        ]
    ].sort_values(["Y_var", "T", "sample", "k"])

    print("\n" + "=" * 60)
    print("[INFO] Notebook progress message.")
    print(out_df[["Y_var", "T", "sample", "k", "Estimate", "Pr(>|t|)"]])

    out_path = OUT_DIR / f"eventstudy_{Y_VAR}_T{'_'.join(map(str, ES_T_LIST))}_pid12_provYearFE_cityCluster.csv"
    out_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")

    return out_df


# =============================================================================

def plot_event_study(es_df: pd.DataFrame, T: int, sample: str = "all", title_suffix: str = ""):
    """Archived notebook note for 01_baseline_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sub = es_df[
        (es_df["Y_var"] == Y_VAR) &
        (es_df["T"] == T) &
        (es_df["sample"] == sample)
    ].copy()

    if sub.empty:
        print("[INFO] Notebook progress message.")
        return

    # Original notebook comment normalized for the public code archive.
    sub = sub.sort_values("k")

    k = sub["k"].values
    beta = sub["Estimate"].values
    ci_low = sub["2.5%"].values
    ci_high = sub["97.5%"].values

    # Original notebook comment normalized for the public code archive.
    err_low = beta - ci_low
    err_high = ci_high - beta

    plt.figure(figsize=(6, 4))
    # Original notebook comment normalized for the public code archive.
    plt.errorbar(
        k,
        beta,
        yerr=[err_low, err_high],
        fmt="o-",
        capsize=3,
    )

    # Original notebook comment normalized for the public code archive.
    plt.axhline(0, linestyle="--", linewidth=1)
    # Original notebook comment normalized for the public code archive.
    plt.axvline(0, linestyle="--", linewidth=1)

    plt.xlabel("事件时间 k (相对首次 ≥T 年一遇洪水的年份)")
    plt.ylabel(f"{Y_VAR} 的估计效应 (β_k)")
    plt.title(f"Event study: T={T}, sample={sample} {title_suffix}")
    plt.xticks(k)  # Original notebook comment normalized for the public code archive.

    plt.tight_layout()
    plt.show()


def plot_event_study_dual(es_df: pd.DataFrame, T: int, samples=("rural", "urban")):
    """Archived notebook note for 01_baseline_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    plt.figure(figsize=(6, 4))

    for sample in samples:
        sub = es_df[
            (es_df["Y_var"] == Y_VAR) &
            (es_df["T"] == T) &
            (es_df["sample"] == sample)
        ].copy()
        if sub.empty:
            print("[INFO] Notebook progress message.")
            continue
        sub = sub.sort_values("k")
        plt.plot(
            sub["k"].values,
            sub["Estimate"].values,
            marker="o",
            label=sample
        )

    plt.axhline(0, linestyle="--", linewidth=1)
    plt.axvline(0, linestyle="--", linewidth=1)
    plt.xlabel("事件时间 k")
    plt.ylabel(f"{Y_VAR} 的估计效应 (β_k)")
    plt.title(f"Event study 对比：T={T}，rural vs urban")
    plt.legend(title="sample")
    plt.xticks(sorted(es_df["k"].dropna().unique()))
    plt.tight_layout()
    plt.show()


def plot_intensity_by_sample(int_df: pd.DataFrame, sample: str = "rural"):
    """Archived notebook note for 01_baseline_fe_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sub = int_df[
        (int_df["Y_var"] == Y_VAR) &
        (int_df["sample"] == sample)
    ].copy()

    if sub.empty:
        print("[INFO] Notebook progress message.")
        return

    plt.figure(figsize=(6, 4))

    for T in sorted(sub["T"].unique()):
        tmp = sub[sub["T"] == T].sort_values("window")
        plt.plot(
            tmp["window"].values,
            tmp["Estimate"].values,
            marker="o",
            label=f"T={T}"
        )

    plt.axhline(0, linestyle="--", linewidth=1)
    plt.xlabel("滚动窗口长度（年）")
    plt.ylabel(f"{Y_VAR} 的强度效应 (β)")
    plt.title(f"强度型暴露效应：sample={sample}")
    plt.legend(title="返回期 T")
    plt.tight_layout()
    plt.show()


# =============================================================================

if __name__ == "__main__":
    # Original notebook comment normalized for the public code archive.
    df_panel = prepare_panel()

    # Fixed-effects regression helper.
    intensity_df = run_intensity_fe_city_cluster(df_panel)

    # Fixed-effects regression helper.
    es_df = run_event_study_city_cluster(df_panel)

    # Original notebook comment normalized for the public code archive.
    if es_df is not None:
        # Original notebook comment normalized for the public code archive.
        plot_event_study(es_df, T=50, sample="all",   title_suffix="(全样本)")
        plot_event_study(es_df, T=50, sample="rural", title_suffix="(农村)")
        plot_event_study(es_df, T=50, sample="urban", title_suffix="(城市)")

        plot_event_study(es_df, T=100, sample="all",   title_suffix="(全样本)")
        plot_event_study(es_df, T=100, sample="rural", title_suffix="(农村)")
        plot_event_study(es_df, T=100, sample="urban", title_suffix="(城市)")

        # Original notebook comment normalized for the public code archive.
        plot_event_study_dual(es_df, T=50, samples=("rural", "urban"))
        plot_event_study_dual(es_df, T=100, samples=("rural", "urban"))

    if intensity_df is not None:
        # Original notebook comment normalized for the public code archive.
        plot_intensity_by_sample(intensity_df, sample="all")
        plot_intensity_by_sample(intensity_df, sample="rural")
        plot_intensity_by_sample(intensity_df, sample="urban")
