#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 04_flood_exposure_channel_index_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 3
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_flood_exposure_channel_index_regression.

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

# Original notebook comment normalized for the public code archive.
CHANNEL_INDEX_FILE = Path(
    "/home/ll/jupyter_notebook/gis_data/OLDER/CHARLS/health/"
    "Health_channels_index_2011_2018.parquet"
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
    """Archived notebook note for 04_flood_exposure_channel_index_regression.

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
    # =============================================================================
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

    # =============================================================================
    print("[INFO] Notebook progress message.")
    ch = pd.read_parquet(CHANNEL_INDEX_FILE)

    # Original notebook comment normalized for the public code archive.
    needed_cols = ["ID12", "year", "fin_burden_index", "utilization_index", "poor_access_index"]
    for c in needed_cols:
        if c not in ch.columns:
            raise KeyError(f"通道指数文件中缺少列 {c}，请检查 Health_channels_index_2011_2018.parquet。")

    ch = ch[needed_cols].copy()

    # Original notebook comment normalized for the public code archive.
    ch = ch[ch["year"].between(2011, 2018)].copy()

    # Original notebook comment normalized for the public code archive.
    ch["ID12"] = pd.to_numeric(ch["ID12"], errors="coerce").astype("Int64")
    ch["pid12"] = ch["ID12"].astype("Int64").astype(str)
    ch["year"] = pd.to_numeric(ch["year"], errors="coerce").astype("Int64")

    print("[INFO] Notebook progress message.")
    print(ch["year"].value_counts().sort_index())

    # Original notebook comment normalized for the public code archive.
    panel = panel.merge(
        ch[["pid12", "year", "fin_burden_index", "utilization_index", "poor_access_index"]],
        how="left",
        on=["pid12", "year"],
        validate="m:1",  # Original notebook comment normalized for the public code archive.
    )

    print("[INFO] Notebook progress message.", panel.shape)
    print("[INFO] Notebook progress message.")
    print(
        panel[["fin_burden_index", "utilization_index", "poor_access_index"]]
        .isna()
        .mean()
    )

    # =============================================================================
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
    if "health_index_z" in merged.columns:
        print(
            f"[INFO] 合并后 non-missing health_index_z 数量: "
            f"{merged['health_index_z'].notna().sum()}"
        )
    else:
        print("[INFO] Notebook progress message.")

    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    print("[INFO] Notebook progress message.")
    print(
        merged[["fin_burden_index", "utilization_index", "poor_access_index"]]
        .isna()
        .mean()
    )

    # Original notebook comment normalized for the public code archive.
    merged.to_parquet(OUT_PANEL_MERGED_PARQUET, index=False)
    merged.to_excel(OUT_PANEL_MERGED_XLSX, index=False)
    print(
        "[SAVE] 合并后的 60+ 面板（含通道指数 + 多窗口暴露）已保存:\n"
        f"  - {OUT_PANEL_MERGED_PARQUET}\n"
        f"  - {OUT_PANEL_MERGED_XLSX}"
    )

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
# Notebook cell 6
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_flood_exposure_channel_index_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm

# =============================================================================

ROOT_FLOOD = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/flood_health_result"
)

# Original notebook comment normalized for the public code archive.
PANEL_MERGED = ROOT_FLOOD / "charls_health_panel_60plus_with_index_Tall_5_10_20_30y.parquet"

# Fixed-effects regression helper.
OUT_FE_CHANNELS = ROOT_FLOOD / "fe_channels_index_Tall_5_10_20_30y_urban_rural_results_pid12.csv"

# Original notebook comment normalized for the public code archive.
T_LIST = [2, 5, 10, 20, 50, 100]
WINDOW_LIST = [5, 10, 20, 30]

# Original notebook comment normalized for the public code archive.
ID_COL = "pid12"


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def twoway_fe_reg(df, y_col, x_cols, id_col=ID_COL, t_col="year"):
    """Archived notebook note for 04_flood_exposure_channel_index_regression.

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
# Fixed-effects regression helper.
# ================================
def run_fe_channels_multiT_urban_rural_multiwindow():
    print(f"[READ][CHANNEL] merged 60+ panel: {PANEL_MERGED}")
    df = pd.read_parquet(PANEL_MERGED)

    # Original notebook comment normalized for the public code archive.
    df["age"] = pd.to_numeric(df.get("age"), errors="coerce")
    df["year"] = pd.to_numeric(df.get("year"), errors="coerce").astype("Int64")
    df[ID_COL] = df[ID_COL].astype(str)

    # Original notebook comment normalized for the public code archive.
    df = df[df["year"].between(2011, 2018)].copy()
    print("[INFO] Notebook progress message.")
    print(df["year"].value_counts().sort_index())

    # Original notebook comment normalized for the public code archive.
    if "urban_nbs" not in df.columns:
        raise KeyError("面板中不存在 urban_nbs，无法定义长期城市/农村分组。")

    df["urban_nbs"] = pd.to_numeric(df["urban_nbs"], errors="coerce")
    df = df.dropna(subset=["age", "urban_nbs", ID_COL, "year"]).copy()
    df["age2"] = df["age"] ** 2

    # Original notebook comment normalized for the public code archive.
    df["urban_nbs"] = df["urban_nbs"].fillna(0).astype(int)
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
        f"[CHANNEL] 至少有 2 个波次的 {ID_COL} 数: {df[ID_COL].nunique()}, "
        f"总行数: {len(df)}, 年份数: {df['year'].nunique()}"
    )

    # Original notebook comment normalized for the public code archive.
    y_list = ["fin_burden_index", "utilization_index", "poor_access_index"]

    # Original notebook comment normalized for the public code archive.
    sample_specs = {
        "all": None,
        "urban": 1,
        "rural": 0,
    }

    all_rows = []

    for y_col in y_list:
        if y_col not in df.columns:
            print("[INFO] Notebook progress message.")
            continue

        df_y = df.dropna(subset=[y_col]).copy()
        if df_y.empty:
            print("[INFO] Notebook progress message.")
            continue

        print("\n" + "=" * 60)
        print("[INFO] Notebook progress message.")
        print("[INFO] Notebook progress message.", len(df_y))

        # Original notebook comment normalized for the public code archive.
        for window in WINDOW_LIST:
            exposure_cols = {T: f"share_flood_T{T}_{window}y" for T in T_LIST}

            for T, exp_col in exposure_cols.items():
                if exp_col not in df_y.columns:
                    print("[INFO] Notebook progress message.")
                    continue

                for sample_name, group_val in sample_specs.items():
                    if group_val is None:
                        sub = df_y.copy()
                    else:
                        sub = df_y[df_y["urban_group"] == group_val].copy()

                    # Original notebook comment normalized for the public code archive.
                    waves_sub = sub.groupby(ID_COL)["year"].nunique()
                    keep_ids_sub = waves_sub[waves_sub >= 2].index
                    sub = sub[sub[ID_COL].isin(keep_ids_sub)].copy()

                    if len(sub) < 100:
                        print(
                            f"[WARN][CHANNEL] Y={y_col}, window={window}, T={T}, "
                            f"{sample_name} 样本量过小 (N={len(sub)}), 跳过。"
                        )
                        continue

                    x_cols = [exp_col, "age", "age2"]

                    res = twoway_fe_reg(
                        sub,
                        y_col=y_col,
                        x_cols=x_cols,
                        id_col=ID_COL,
                        t_col="year",
                    )

                    # Original notebook comment normalized for the public code archive.
                    row = res.loc[exp_col].copy()
                    row["Y_var"] = y_col
                    row["window"] = window
                    row["T"] = T
                    row["exposure"] = exp_col
                    row["sample"] = sample_name
                    row["N"] = len(sub)
                    row["N_id"] = sub[ID_COL].nunique()
                    row["N_year"] = sub["year"].nunique()

                    # Original notebook comment normalized for the public code archive.
                    print("\n" + "-" * 40)
                    print(f"[RESULT][CHANNEL] Y={y_col}, window={window}y, T={T}, sample={sample_name}")
                    print(res.loc[[exp_col]][["Estimate", "Pr(>|t|)"]])

                    all_rows.append(row)

    if not all_rows:
        print("[INFO] Notebook progress message.")
        return

    out_df = pd.DataFrame(all_rows)
    out_df = out_df[
        [
            "Y_var",
            "window", "T", "exposure", "sample",
            "Estimate", "Std. Error", "t value", "Pr(>|t|)",
            "2.5%", "97.5%",
            "N", "N_id", "N_year",
        ]
    ]
    out_df.sort_values(["Y_var", "window", "T", "sample"], inplace=True)

    print("\n" + "=" * 60)
    print("[INFO] Notebook progress message.")
    print(out_df[["Y_var", "window", "T", "sample", "Estimate", "Pr(>|t|)"]].head(30))

    out_df.to_csv(OUT_FE_CHANNELS, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def main():
    run_fe_channels_multiT_urban_rural_multiwindow()


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 11
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_flood_exposure_channel_index_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm

# =============================================================================

ROOT_FLOOD = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/flood_health_result"
)

# Original notebook comment normalized for the public code archive.
PANEL_MERGED = ROOT_FLOOD / "charls_health_panel_60plus_with_index_Tall_5_10_20_30y.parquet"

# Fixed-effects regression helper.
OUT_FE_CHANNELS = ROOT_FLOOD / "fe_channels_index_Tall_5_10_20_30y_pid12_provYearFE_cityCluster.csv"

# Original notebook comment normalized for the public code archive.
T_LIST = [2, 5, 10, 20, 50, 100]
WINDOW_LIST = [5, 10, 20, 30]

# Original notebook comment normalized for the public code archive.
ID_COL = "pid12"
CLUSTER_COL = "city_code"   # City-level processing note.
PROV_COL = "province"       # Fixed-effects regression helper.
YEAR_COL = "year"


# ================================
# Fixed-effects regression helper.
# Fixed-effects regression helper.
# ================================
def demean_two_fe(df, cols, fe1, fe2):
    """Archived notebook note for 04_flood_exposure_channel_index_regression.

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
    """Archived notebook note for 04_flood_exposure_channel_index_regression.

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


# ================================
# Fixed-effects regression helper.
# ================================
def run_fe_channels_multiT_urban_rural_multiwindow():
    print(f"[READ][CHANNEL] merged 60+ panel: {PANEL_MERGED}")
    df = pd.read_parquet(PANEL_MERGED)

    # Original notebook comment normalized for the public code archive.
    df["age"] = pd.to_numeric(df.get("age"), errors="coerce")
    df[YEAR_COL] = pd.to_numeric(df.get(YEAR_COL), errors="coerce")
    df[ID_COL] = df[ID_COL].astype(str)

    # Original notebook comment normalized for the public code archive.
    df = df[df[YEAR_COL].isin([2011, 2013, 2015, 2018])].copy()
    df[YEAR_COL] = df[YEAR_COL].astype(int)
    print("[INFO] Notebook progress message.")
    print(df[YEAR_COL].value_counts().sort_index())

    # Original notebook comment normalized for the public code archive.
    for col in [PROV_COL, CLUSTER_COL, "urban_nbs", "age", ID_COL, YEAR_COL]:
        if col not in df.columns:
            raise KeyError(f"面板中不存在必要列 {col}，请检查。")

    # Fixed-effects regression helper.
    df["prov_str"] = df[PROV_COL].astype(str).str.strip()
    df["prov_year"] = df["prov_str"] + "_" + df[YEAR_COL].astype(int).astype(str)

    # Original notebook comment normalized for the public code archive.
    df[CLUSTER_COL] = pd.to_numeric(df[CLUSTER_COL], errors="coerce")

    # Original notebook comment normalized for the public code archive.
    df["urban_nbs"] = pd.to_numeric(df["urban_nbs"], errors="coerce")
    df = df.dropna(subset=["age", "urban_nbs", ID_COL, YEAR_COL, PROV_COL, CLUSTER_COL]).copy()
    df["age2"] = df["age"] ** 2

    # Original notebook comment normalized for the public code archive.
    df["urban_nbs"] = df["urban_nbs"].fillna(0).astype(int)
    grp_urban = df.groupby(ID_COL)["urban_nbs"].mean()
    urban_group = (grp_urban > 0.5).astype(int).rename("urban_group")
    df = df.merge(urban_group, on=ID_COL, how="left")

    print("[INFO] Notebook progress message.")
    print(df[[ID_COL, "urban_group"]].drop_duplicates()["urban_group"].value_counts())

    # Fixed-effects regression helper.
    waves_per_id = df.groupby(ID_COL)[YEAR_COL].nunique()
    keep_ids = waves_per_id[waves_per_id >= 2].index
    df = df[df[ID_COL].isin(keep_ids)].copy()
    print(
        f"[CHANNEL] 至少有 2 个波次的 {ID_COL} 数: {df[ID_COL].nunique()}, "
        f"总行数: {len(df)}, 年份数: {df[YEAR_COL].nunique()}"
    )

    # Original notebook comment normalized for the public code archive.
    y_list = ["fin_burden_index", "utilization_index", "poor_access_index"]

    # Original notebook comment normalized for the public code archive.
    sample_specs = {
        "all": None,
        "urban": 1,
        "rural": 0,
    }

    all_rows = []

    for y_col in y_list:
        if y_col not in df.columns:
            print("[INFO] Notebook progress message.")
            continue

        df_y = df.dropna(subset=[y_col]).copy()
        if df_y.empty:
            print("[INFO] Notebook progress message.")
            continue

        print("\n" + "=" * 60)
        print("[INFO] Notebook progress message.")
        print("[INFO] Notebook progress message.", len(df_y))

        # Original notebook comment normalized for the public code archive.
        for window in WINDOW_LIST:
            exposure_cols = {T: f"share_flood_T{T}_{window}y" for T in T_LIST}

            for T, exp_col in exposure_cols.items():
                if exp_col not in df_y.columns:
                    print("[INFO] Notebook progress message.")
                    continue

                for sample_name, group_val in sample_specs.items():
                    if group_val is None:
                        sub = df_y.copy()
                    else:
                        sub = df_y[df_y["urban_group"] == group_val].copy()

                    # Original notebook comment normalized for the public code archive.
                    waves_sub = sub.groupby(ID_COL)[YEAR_COL].nunique()
                    keep_ids_sub = waves_sub[waves_sub >= 2].index
                    sub = sub[sub[ID_COL].isin(keep_ids_sub)].copy()

                    # City-level processing note.
                    if len(sub) < 100 or sub[CLUSTER_COL].nunique() < 10:
                        print(
                            f"[WARN][CHANNEL] Y={y_col}, window={window}, T={T}, "
                            f"{sample_name} 样本量或城市数过小 "
                            f"(N={len(sub)}, N_city={sub[CLUSTER_COL].nunique()}), 跳过。"
                        )
                        continue

                    x_cols = [exp_col, "age", "age2"]

                    res = fe_reg_twoFE_city_cluster(
                        sub,
                        y_col=y_col,
                        x_cols=x_cols,
                        fe1=ID_COL,
                        fe2="prov_year",
                        cluster_col=CLUSTER_COL,
                    )

                    # Original notebook comment normalized for the public code archive.
                    row = res.loc[exp_col].copy()
                    row["Y_var"] = y_col
                    row["window"] = window
                    row["T"] = T
                    row["exposure"] = exp_col
                    row["sample"] = sample_name
                    row["N"] = len(sub)
                    row["N_id"] = sub[ID_COL].nunique()
                    row["N_year"] = sub[YEAR_COL].nunique()
                    row["N_city"] = sub[CLUSTER_COL].nunique()

                    # Original notebook comment normalized for the public code archive.
                    print("\n" + "-" * 40)
                    print(
                        f"[RESULT][CHANNEL] (prov×year FE, city cluster) "
                        f"Y={y_col}, window={window}y, T={T}, sample={sample_name}"
                    )
                    print(res.loc[[exp_col]][["Estimate", "Pr(>|t|)"]])

                    all_rows.append(row)

    if not all_rows:
        print("[INFO] Notebook progress message.")
        return

    out_df = pd.DataFrame(all_rows)
    out_df = out_df[
        [
            "Y_var",
            "window", "T", "exposure", "sample",
            "Estimate", "Std. Error", "t value", "Pr(>|t|)",
            "2.5%", "97.5%",
            "N", "N_id", "N_year", "N_city",
        ]
    ]
    out_df.sort_values(["Y_var", "window", "T", "sample"], inplace=True)

    print("\n" + "=" * 60)
    print("[INFO] Notebook progress message.")
    print(out_df[["Y_var", "window", "T", "sample", "Estimate", "Pr(>|t|)"]].head(30))

    out_df.to_csv(OUT_FE_CHANNELS, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")


# ================================
# Original notebook comment normalized for the public code archive.
# ================================
def main():
    run_fe_channels_multiT_urban_rural_multiwindow()


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 20
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_flood_exposure_channel_index_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# =============================================================================
ROOT_FLOOD = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/flood_health_result"
)

FE_FILE = ROOT_FLOOD / "fe_channels_index_Tall_5_10_20_30y_pid12_provYearFE_cityCluster.csv"

# Original notebook comment normalized for the public code archive.
OUT_POOL_CSV = ROOT_FLOOD / "fe_channels_index_Tall_T_pooled_windows.csv"

# Original notebook comment normalized for the public code archive.
FIG_DIR = ROOT_FLOOD / "figs_channels_T_pooled"
FIG_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
def pool_windows_group(g: pd.DataFrame) -> pd.Series:
    """Archived notebook note for 04_flood_exposure_channel_index_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    g = g.copy()

    # Original notebook comment normalized for the public code archive.
    g = g.replace([np.inf, -np.inf], np.nan)
    g = g.dropna(subset=["Estimate", "Std. Error"])
    g = g[g["Std. Error"] > 0]

    if g.empty:
        # Original notebook comment normalized for the public code archive.
        return pd.Series(
            {
                "beta_pool": np.nan,
                "se_pool": np.nan,
                "beta_abs_pool": np.nan,
                "windows_used": "",
                "n_windows": 0,
            }
        )

    # Original notebook comment normalized for the public code archive.
    w = 1.0 / (g["Std. Error"] ** 2)
    beta_pool = (g["Estimate"] * w).sum() / w.sum()
    se_pool = np.sqrt(1.0 / w.sum())

    return pd.Series(
        {
            "beta_pool": beta_pool,
            "se_pool": se_pool,
            "beta_abs_pool": abs(beta_pool),
            "windows_used": ",".join(str(int(w)) for w in sorted(g["window"].unique())),
            "n_windows": len(g),
        }
    )


# =============================================================================
def pool_all_windows():
    print("[INFO] Notebook progress message.")
    df = pd.read_csv(FE_FILE)

    # Original notebook comment normalized for the public code archive.
    df = df[df["window"].isin([5, 10, 20, 30])].copy()

    # Original notebook comment normalized for the public code archive.
    required_cols = [
        "Y_var",
        "window",
        "T",
        "sample",
        "Estimate",
        "Std. Error",
    ]
    for col in required_cols:
        if col not in df.columns:
            raise KeyError(f"输入文件缺少必要列：{col}")

    print("[INFO] Notebook progress message.", len(df))
    print("[INFO] Y_var:", df["Y_var"].unique())
    print("[INFO] sample:", df["sample"].unique())
    print("[INFO] window:", sorted(df["window"].unique()))
    print("[INFO] T:", sorted(df["T"].unique()))

    # Original notebook comment normalized for the public code archive.
    print("[INFO] Notebook progress message.")
    df_pool = (
        df.groupby(["Y_var", "sample", "T"], as_index=False)
        .apply(pool_windows_group)
        .reset_index(drop=True)
    )

    # Original notebook comment normalized for the public code archive.
    df_pool["ci_low"] = df_pool["beta_pool"] - 1.96 * df_pool["se_pool"]
    df_pool["ci_high"] = df_pool["beta_pool"] + 1.96 * df_pool["se_pool"]

    # Original notebook comment normalized for the public code archive.
    df_pool.sort_values(["Y_var", "sample", "T"], inplace=True)

    print("[INFO] Notebook progress message.")
    print(
        df_pool[
            [
                "Y_var",
                "sample",
                "T",
                "beta_pool",
                "se_pool",
                "beta_abs_pool",
                "n_windows",
                "windows_used",
            ]
        ].head(20)
    )

    # Original notebook comment normalized for the public code archive.
    df_pool.to_csv(OUT_POOL_CSV, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")

    return df_pool


# =============================================================================
def plot_by_channel_and_sample(df_pool: pd.DataFrame):
    """Archived notebook note for 04_flood_exposure_channel_index_regression.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

    # Original notebook comment normalized for the public code archive.
    y_order = [
        "fin_burden_index",
        "utilization_index",
        "poor_access_index",
    ]
    # Original notebook comment normalized for the public code archive.
    sample_order = ["all", "urban", "rural"]

    # Original notebook comment normalized for the public code archive.
    Y_LABEL = {
        "fin_burden_index": "经济负担通道（fin_burden_index）",
        "utilization_index": "医疗服务利用通道（utilization_index）",
        "poor_access_index": "医疗可及性通道（poor_access_index）",
    }
    SAMPLE_LABEL = {
        "all": "全样本",
        "urban": "城市样本",
        "rural": "农村样本",
    }

    # Original notebook comment normalized for the public code archive.
    for y_var in y_order:
        df_y = df_pool[df_pool["Y_var"] == y_var].copy()
        if df_y.empty:
            print("[INFO] Notebook progress message.")
            continue

        for sample in sample_order:
            df_ys = df_y[df_y["sample"] == sample].copy()
            if df_ys.empty:
                print("[INFO] Notebook progress message.")
                continue

            # Original notebook comment normalized for the public code archive.
            df_ys = df_ys.sort_values("T").copy()

            # =============================================================================
            fig1, ax1 = plt.subplots(figsize=(6, 4))
            ax1.errorbar(
                df_ys["T"],
                df_ys["beta_pool"],
                yerr=1.96 * df_ys["se_pool"],
                fmt="-o",
                capsize=4,
            )
            ax1.axhline(0.0, color="black", linewidth=0.8)
            ax1.set_xlabel("重现期 T (年)")
            ax1.set_ylabel("合并系数 beta_pool (单位：通道指数标准差)")
            ax1.set_title(
                f"{Y_LABEL.get(y_var, y_var)}\n{SAMPLE_LABEL.get(sample, sample)}："
                f"洪水暴露的综合影响（合并 5/10/20/30 年窗口）"
            )
            ax1.grid(True, linestyle="--", alpha=0.3)

            fig1.tight_layout()
            out_path1 = FIG_DIR / f"channels_T_pooled_{y_var}_{sample}_beta.png"
            fig1.savefig(out_path1, dpi=300)
            plt.show()
            print("[INFO] Notebook progress message.")

            # =============================================================================
            fig2, ax2 = plt.subplots(figsize=(6, 4))
            # Original notebook comment normalized for the public code archive.
            colors = []
            for b in df_ys["beta_pool"]:
                if np.isnan(b):
                    colors.append("gray")
                elif b < 0:
                    colors.append("tab:red")
                elif b > 0:
                    colors.append("tab:blue")
                else:
                    colors.append("gray")

            ax2.bar(
                df_ys["T"].astype(str),
                df_ys["beta_abs_pool"],
                color=colors,
            )
            ax2.set_xlabel("重现期 T (年)")
            ax2.set_ylabel("|beta_pool|（量级，单位：通道指数标准差）")
            ax2.set_title(
                f"{Y_LABEL.get(y_var, y_var)}\n{SAMPLE_LABEL.get(sample, sample)}："
                f"洪水暴露影响的量级（合并 5/10/20/30 年窗口）"
            )
            # Original notebook comment normalized for the public code archive.
            for x, b, y_abs in zip(
                df_ys["T"].astype(str), df_ys["beta_pool"], df_ys["beta_abs_pool"]
            ):
                if np.isnan(b) or np.isnan(y_abs):
                    continue
                sign = "+" if b > 0 else ("-" if b < 0 else "0")
                ax2.text(
                    x,
                    y_abs,
                    sign,
                    ha="center",
                    va="bottom",
                    fontsize=8,
                )

            ax2.grid(axis="y", linestyle="--", alpha=0.3)
            fig2.tight_layout()
            out_path2 = FIG_DIR / f"channels_T_pooled_{y_var}_{sample}_abs.png"
            fig2.savefig(out_path2, dpi=300)
            plt.show()
            print("[INFO] Notebook progress message.")


# =============================================================================
def main():
    # Original notebook comment normalized for the public code archive.
    df_pool = pool_all_windows()

    # Original notebook comment normalized for the public code archive.
    plot_by_channel_and_sample(df_pool)

    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()
