#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 05_pathway_analysis.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 5
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 05_pathway_analysis.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
from pyfixest.estimation import feols
import warnings

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)

# ------------------------------------------------
# Original notebook comment normalized for the public code archive.
# ------------------------------------------------

PANEL_FILE = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/flood_health_result/"
    "charls_health_panel_60plus_with_index_Tall_5_10_20_30y.parquet"
)

# Original notebook comment normalized for the public code archive.
FLOOD_VAR = "share_flood_T10_10y"   # Original notebook comment normalized for the public code archive.

# Original notebook comment normalized for the public code archive.
HEALTH_VAR = "health_index_z"

# Fixed-effects regression helper.
ID_VAR      = "pid12"
YEAR_VAR    = "year"
CLUSTER_VAR = "city_code"   # City-level processing note.
PROV_VAR    = "province"    # Fixed-effects regression helper.

# Original notebook comment normalized for the public code archive.
MEDIATOR_VARS = {
    "fin_burden_index": "医疗支出负担指数（大 ⇒ 负担更重）",
    "utilization_index": "医疗利用不足/未满足需求指数（大 ⇒ 医疗利用更不足）",
    "poor_access_index": "医疗可达性差指数（大 ⇒ 可达性更差）",
}

# Original notebook comment normalized for the public code archive.
CONTROL_VARS = [
    #"age", "urban_nbs",
    # "age_sq", "female", "edu_years", "ln_income", "married", "urban_group"
]

# ------------------------------------------------
# Original notebook comment normalized for the public code archive.
# ------------------------------------------------

df = pd.read_parquet(PANEL_FILE)

# Original notebook comment normalized for the public code archive.
needed_cols = (
    [ID_VAR, YEAR_VAR, CLUSTER_VAR, HEALTH_VAR, FLOOD_VAR, PROV_VAR]
    + list(MEDIATOR_VARS.keys())
    + CONTROL_VARS
)

missing_cols = [c for c in needed_cols if c not in df.columns]
if missing_cols:
    print("[INFO] Notebook progress message.", missing_cols)

existing_cols = [c for c in needed_cols if c in df.columns]
df = df[existing_cols].copy()

print("[INFO] Notebook progress message.", df.shape)
print("[INFO] Notebook progress message.", df.columns.tolist())

df = df.sort_values([ID_VAR, YEAR_VAR])

# ------------------------------------------------
# Original notebook comment normalized for the public code archive.
# ------------------------------------------------

# Original notebook comment normalized for the public code archive.
df["F_pre"] = df.groupby(ID_VAR)[FLOOD_VAR].shift(1)

# Original notebook comment normalized for the public code archive.
df["health_next"] = df.groupby(ID_VAR)[HEALTH_VAR].shift(-1)

# Original notebook comment normalized for the public code archive.
df_med = df.dropna(subset=["F_pre", "health_next"]).copy()

print("[INFO] Notebook progress message.", df_med.shape)
print(df_med[[ID_VAR, YEAR_VAR, "F_pre", HEALTH_VAR, "health_next"]].head())

# ------------------------------------------------
# Fixed-effects regression helper.
# ------------------------------------------------

def build_rhs(main_term: str, cols_in_data) -> str:
    """Archived notebook note for 05_pathway_analysis.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    valid_controls = [c for c in CONTROL_VARS if c in cols_in_data]
    if valid_controls:
        return main_term + " + " + " + ".join(valid_controls)
    else:
        return main_term

# Fixed-effects regression helper.
if PROV_VAR in df_med.columns:
    FE_SPEC = f"{ID_VAR} + {PROV_VAR}^{YEAR_VAR}"
else:
    FE_SPEC = f"{ID_VAR} + {YEAR_VAR}"

print("[INFO] Notebook progress message.", FE_SPEC)

# Original notebook comment normalized for the public code archive.
cluster_arg = CLUSTER_VAR if CLUSTER_VAR in df_med.columns else None
print("[INFO] Notebook progress message.", cluster_arg)

# ------------------------------------------------
# Original notebook comment normalized for the public code archive.
# ------------------------------------------------

results = []

for m_var, m_desc in MEDIATOR_VARS.items():
    if m_var not in df_med.columns:
        print("[INFO] Notebook progress message.")
        continue

    print("\n" + "=" * 80)
    print(f"[MEDIATOR] {m_var}: {m_desc}")

    # =============================================================================
    # M_it = α F_pre_ct + X_it + FE + ε_it
    rhs_m = build_rhs("F_pre", df_med.columns)
    formula_m = f"{m_var} ~ {rhs_m}"
    print("[INFO] Notebook progress message.", formula_m)

    # Fixed-effects regression helper.
    res_m = feols(
        formula_m,
        data=df_med,
        fe=FE_SPEC,
        cluster=cluster_arg
    )

    print(res_m.summary())

    try:
        alpha = res_m.coef["F_pre"]
        se_alpha = res_m.se["F_pre"]
    except KeyError:
        print("[INFO] Notebook progress message.")
        continue

    # =============================================================================
    # health_next_i,t+1 = β F_pre_ct + γ M_it + X_it + FE + u_i,t+1
    rhs_h = build_rhs("F_pre + " + m_var, df_med.columns)
    formula_h = f"health_next ~ {rhs_h}"
    print("[INFO] Notebook progress message.", formula_h)

    res_h = feols(
        formula_h,
        data=df_med,
        fe=FE_SPEC,
        cluster=cluster_arg
    )

    print(res_h.summary())

    try:
        beta = res_h.coef["F_pre"]
        se_beta = res_h.se["F_pre"]
        gamma = res_h.coef[m_var]
        se_gamma = res_h.se[m_var]
    except KeyError:
        print("[INFO] Notebook progress message.")
        continue

    # =============================================================================
    # Original notebook comment normalized for the public code archive.
    indirect = alpha * gamma
    # Original notebook comment normalized for the public code archive.
    var_indirect = (gamma ** 2) * (se_alpha ** 2) + (alpha ** 2) * (se_gamma ** 2)
    se_indirect = np.sqrt(var_indirect)

    # Original notebook comment normalized for the public code archive.
    direct = beta
    se_direct = se_beta

    # Original notebook comment normalized for the public code archive.
    total = direct + indirect
    se_total = np.sqrt(se_direct ** 2 + se_indirect ** 2)

    results.append(
        dict(
            mediator=m_var,
            mediator_desc=m_desc,
            flood_var=FLOOD_VAR,
            alpha=alpha,
            se_alpha=se_alpha,
            gamma=gamma,
            se_gamma=se_gamma,
            indirect=indirect,
            se_indirect=se_indirect,
            direct=direct,
            se_direct=se_direct,
            total=total,
            se_total=se_total,
        )
    )

# ------------------------------------------------
# Original notebook comment normalized for the public code archive.
# ------------------------------------------------

if results:
    df_res = pd.DataFrame(results)
    out_csv = (
        PANEL_FILE.parent
        / f"mediation_health_{HEALTH_VAR}_{FLOOD_VAR}_pid12_provYearFE_cityCluster.csv"
    )
    df_res.to_csv(out_csv, index=False)

    print("\n" + "=" * 80)
    print("[INFO] Notebook progress message.")
    print(df_res)
    print("[INFO] Notebook progress message.")
else:
    print("[INFO] Notebook progress message.")


# ------------------------------------------------------------------------------
# Notebook cell 7
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 05_pathway_analysis.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import pyfixest as pf
import matplotlib.pyplot as plt


# =============================================================================
DATA = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/flood_health_result/"
    "charls_health_panel_60plus_with_index_Tall_5_10_20_30y.parquet"
)

ID_COL = "pid12"
YEAR_COL = "year"
CITY_COL = "city_code"
PROV_COL = "province"

HEALTH_VAR = "health_index_z"

# Original notebook comment normalized for the public code archive.
MEDIATORS = [
    ("fin_burden_index", "医疗支出负担指数（大 ⇒ 负担更重）"),
    ("utilization_index", "医疗利用不足指数（大 ⇒ 未满足需求越多）"),
    ("poor_access_index", "医疗可及性差指数（大 ⇒ 可达性越差）"),
]


def prepare_panel(df: pd.DataFrame, flood_var: str) -> pd.DataFrame:
    """Archived notebook note for 05_pathway_analysis.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    cols_needed = [
        ID_COL,
        YEAR_COL,
        CITY_COL,
        PROV_COL,
        HEALTH_VAR,
        flood_var,
    ] + [m for m, _ in MEDIATORS]

    df = df[cols_needed].copy()

    # Fixed-effects regression helper.
    df["prov_year_fe"] = df[PROV_COL].astype(str) + "_" + df[YEAR_COL].astype(str)

    # Original notebook comment normalized for the public code archive.
    df["F_pre"] = df[flood_var]

    # Original notebook comment normalized for the public code archive.
    df = df.sort_values([ID_COL, YEAR_COL])
    df["health_next"] = df.groupby(ID_COL)[HEALTH_VAR].shift(-1)

    # Original notebook comment normalized for the public code archive.
    df_med = df.loc[df["F_pre"].notna() & df["health_next"].notna()].copy()
    return df_med


def run_feols(formula: str, data: pd.DataFrame, cluster_var: str):
    """Archived notebook note for 05_pathway_analysis.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    fit = pf.feols(
        fml=formula,
        data=data,
        vcov={"CRV1": cluster_var},
    )
    return fit


def extract_coef_se(fit, var_name: str):
    """Archived notebook note for 05_pathway_analysis.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    coefs = fit.coef()
    ses = fit.se()
    if var_name not in coefs.index:
        raise KeyError(f"在回归结果中找不到变量 {var_name}")
    return float(coefs[var_name]), float(ses[var_name])

def plot_mediation_by_mediator(df: pd.DataFrame,
                               mediator: str,
                               effect_type: str = "indirect",
                               title: str = None):
    """Archived notebook note for 05_pathway_analysis.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sub = df[df["mediator"] == mediator].copy()
    if sub.empty:
        print("[INFO] Notebook progress message.")
        return

    # Original notebook comment normalized for the public code archive.
    if "T" not in sub.columns or "window" not in sub.columns:
        tw = sub["flood_var"].str.extract(r"share_flood_T(\d+)_([0-9]+)y")
        sub["T"] = tw[0].astype(int)
        sub["window"] = tw[1].astype(int)

    effect_map = {
        "indirect": "indirect",        # a*b
        "direct": "c_prime",           # c'
        "total": "total_effect",       # c' + a*b
    }
    se_map = {
        "indirect": "se_indirect",
        "direct": "se_cprime",
        # Fixed-effects regression helper.
    }

    effect_col = effect_map.get(effect_type, effect_type)
    if effect_col not in sub.columns:
        print("[INFO] Notebook progress message.")
        return

    se_col = se_map.get(effect_type, None)

    plt.figure(figsize=(6, 4))

    for w in sorted(sub["window"].unique()):
        tmp = sub[sub["window"] == w].sort_values("T")
        x = tmp["T"].values
        y = tmp[effect_col].values

        if se_col and se_col in tmp.columns:
            yerr = 1.96 * tmp[se_col].values  # Original notebook comment normalized for the public code archive.
            plt.errorbar(
                x, y, yerr=yerr,
                marker="o", linestyle="-",
                label=f"窗口={w}年"
            )
        else:
            plt.plot(
                x, y,
                marker="o", linestyle="-",
                label=f"窗口={w}年"
            )

    plt.axhline(0, linestyle="--", linewidth=1)

    plt.xlabel("洪水返回期 T（年）")
    ylabel_map = {
        "indirect": "间接效应 a×b（F → M → health_next）",
        "direct":   "直接效应 c'（F → health_next，控制 M）",
        "total":    "总效应 c' + a×b（F 对 health_next 的近似总效应）",
    }
    plt.ylabel(ylabel_map.get(effect_type, effect_col))

    if title is None:
        title = f"{mediator} 的 {ylabel_map.get(effect_type, effect_col)}"
    plt.title(title)

    plt.legend(title="暴露窗口长度")
    plt.tight_layout()
    plt.show()


def main():
    # Original notebook comment normalized for the public code archive.
    df_all = pd.read_parquet(DATA)
    print("[INFO] Notebook progress message.", df_all.shape)
    print("[INFO] Notebook progress message.", list(df_all.columns))

    # Original notebook comment normalized for the public code archive.
    flood_vars = [c for c in df_all.columns if c.startswith("share_flood_T")]
    flood_vars = sorted(flood_vars)
    print("[INFO] Notebook progress message.")
    for v in flood_vars:
        print("   -", v)

    if not flood_vars:
        print("[INFO] Notebook progress message.")
        return

    results = []

    # Original notebook comment normalized for the public code archive.
    for f_var in flood_vars:
        print("\n" + "=" * 80)
        print("[INFO] Notebook progress message.")

        df_med = prepare_panel(df_all, flood_var=f_var)
        print("[INFO] Notebook progress message.", df_med.shape)

        if df_med.empty:
            print("[INFO] Notebook progress message.")
            continue

        print("[INFO] Notebook progress message.")
        print("[INFO] Notebook progress message.")

        for m_var, m_label in MEDIATORS:
            if m_var not in df_med.columns:
                print("[INFO] Notebook progress message.")
                continue

            print("\n" + "-" * 80)
            print(f"[MEDIATOR] {m_var}: {m_label}")

            # =============================================================================
            # M_it = a F_pre_it + FE + ε
            fml_m = f"{m_var} ~ F_pre | {ID_COL} + prov_year_fe"
            print("[INFO] Notebook progress message.", fml_m)
            fit_m = run_feols(fml_m, data=df_med, cluster_var=CITY_COL)
            print(fit_m.summary())

            a, se_a = extract_coef_se(fit_m, "F_pre")
            print(f"[STEP 1] F_pre → {m_var}: a = {a:.4f}, se(a) = {se_a:.4f}")

            # =============================================================================
            # health_next = c' F_pre + b M_it + d health_it + FE + ε
            fml_y = (
                f"health_next ~ F_pre + {m_var} + {HEALTH_VAR} "
                f"| {ID_COL} + prov_year_fe"
            )
            print("[INFO] Notebook progress message.", fml_y)
            fit_y = run_feols(fml_y, data=df_med, cluster_var=CITY_COL)
            print(fit_y.summary())

            b, se_b = extract_coef_se(fit_y, m_var)
            c_prime, se_cprime = extract_coef_se(fit_y, "F_pre")

            print(f"[STEP 2] {m_var} → health_next: b = {b:.4f}, se(b) = {se_b:.4f}")
            print(
                f"[STEP 2] 直接效应 F_pre → health_next (c') = "
                f"{c_prime:.4f}, se(c') = {se_cprime:.4f}"
            )

            # =============================================================================
            indirect = a * b
            # Original notebook comment normalized for the public code archive.
            var_indirect = (b ** 2) * (se_a ** 2) + (a ** 2) * (se_b ** 2)
            se_indirect = float(np.sqrt(var_indirect))

            total = c_prime + indirect

            print("[INFO] Notebook progress message.")
            print("[INFO] Notebook progress message.")

            results.append(
                dict(
                    flood_var=f_var,
                    mediator=m_var,
                    mediator_label=m_label,
                    a=a,
                    se_a=se_a,
                    b=b,
                    se_b=se_b,
                    indirect=indirect,
                    se_indirect=se_indirect,
                    c_prime=c_prime,
                    se_cprime=se_cprime,
                    total_effect=total,
                    n=df_med.shape[0],
                )
            )

    # Original notebook comment normalized for the public code archive.
    if results:
        out_df = pd.DataFrame(results)

        # =============================================================================
        tw = out_df["flood_var"].str.extract(r"share_flood_T(\d+)_([0-9]+)y")
        out_df["T"] = tw[0].astype(int)
        out_df["window"] = tw[1].astype(int)

        out_path = DATA.with_name(DATA.stem + "_mediation_results.csv")
        out_df.to_csv(out_path, index=False)
        print("[INFO] Notebook progress message.", out_path)

        # =============================================================================
        for m_var, m_label in MEDIATORS:
            if m_var in out_df["mediator"].unique():
                print("[INFO] Notebook progress message.")
                plot_mediation_by_mediator(
                    df=out_df,
                    mediator=m_var,
                    effect_type="indirect",
                    title=f"间接效应 a×b：{m_label}"
                )

        # Original notebook comment normalized for the public code archive.
        # for m_var, m_label in MEDIATORS:
        #     if m_var in out_df["mediator"].unique():
        #         plot_mediation_by_mediator(
        #             df=out_df,
        #             mediator=m_var,
        #             effect_type="direct",
        # Original notebook comment normalized for the public code archive.
        #         )

    else:
        print("[INFO] Notebook progress message.")



if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 10
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 05_pathway_analysis.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import pyfixest as pf

# =============================================================================
DATA = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/flood_health_result/"
    "charls_health_panel_60plus_with_index_Tall_5_10_20_30y.parquet"
)

ID_COL = "pid12"
YEAR_COL = "year"
CITY_COL = "city_code"
PROV_COL = "province"

HEALTH_VAR = "health_index_z"

# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
MEDIATORS = [
    dict(
        var="fin_burden_index",
        label="医疗支出指数（数值变小 ⇒ 支出减少 / 可能未支付必要医疗）",
        worse_when="smaller",
    ),
    dict(
        var="utilization_index",
        label="医疗利用不足指数（数值变大 ⇒ 该看病没有看）",
        worse_when="larger",
    ),
    dict(
        var="poor_access_index",
        label="就医受阻指数（数值越小 ⇒ 被洪水阻断的看病越多）",
        worse_when="smaller",
    ),
]

MEDIATOR_VARS = [m["var"] for m in MEDIATORS]


def prepare_panel(df: pd.DataFrame, flood_var: str) -> pd.DataFrame:
    """Archived notebook note for 05_pathway_analysis.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    cols_needed = [
        ID_COL,
        YEAR_COL,
        CITY_COL,
        PROV_COL,
        HEALTH_VAR,
        flood_var,
    ] + MEDIATOR_VARS

    df = df[cols_needed].copy()

    # Fixed-effects regression helper.
    df["prov_year_fe"] = df[PROV_COL].astype(str) + "_" + df[YEAR_COL].astype(str)

    # Original notebook comment normalized for the public code archive.
    df["F_pre"] = df[flood_var]

    # Original notebook comment normalized for the public code archive.
    df = df.sort_values([ID_COL, YEAR_COL])
    df["health_next"] = df.groupby(ID_COL)[HEALTH_VAR].shift(-1)

    # Original notebook comment normalized for the public code archive.
    df_med = df.loc[df["F_pre"].notna() & df["health_next"].notna()].copy()
    return df_med


def run_feols(formula: str, data: pd.DataFrame, cluster_var: str):
    """Archived notebook note for 05_pathway_analysis.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    fit = pf.feols(
        fml=formula,
        data=data,
        vcov={"CRV1": cluster_var},
    )
    return fit


def extract_coef_se(fit, var_name: str):
    """Archived notebook note for 05_pathway_analysis.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    coefs = fit.coef()
    ses = fit.se()
    if var_name not in coefs.index:
        raise KeyError(f"在回归结果中找不到变量 {var_name}")
    return float(coefs[var_name]), float(ses[var_name])


def main():
    # Original notebook comment normalized for the public code archive.
    df_all = pd.read_parquet(DATA)
    print("[INFO] Notebook progress message.", df_all.shape)
    print("[INFO] Notebook progress message.", list(df_all.columns))

    # Original notebook comment normalized for the public code archive.
    flood_vars = [c for c in df_all.columns if c.startswith("share_flood_T")]
    flood_vars = sorted(flood_vars)
    print("[INFO] Notebook progress message.")
    for v in flood_vars:
        print("   -", v)

    if not flood_vars:
        print("[INFO] Notebook progress message.")
        return

    results = []

    # Original notebook comment normalized for the public code archive.
    for f_var in flood_vars:
        print("\n" + "=" * 80)
        print("[INFO] Notebook progress message.")

        df_med = prepare_panel(df_all, flood_var=f_var)
        print("[INFO] Notebook progress message.", df_med.shape)

        if df_med.empty:
            print("[INFO] Notebook progress message.")
            continue

        print("[INFO] Notebook progress message.")
        print("[INFO] Notebook progress message.")

        for m in MEDIATORS:
            m_var = m["var"]
            m_label = m["label"]
            worse_when = m["worse_when"]

            if m_var not in df_med.columns:
                print("[INFO] Notebook progress message.")
                continue

            print("\n" + "-" * 80)
            print("[INFO] Notebook progress message.")

            # =============================================================================
            # M_it = a F_pre_it + FE + ε
            fml_m = f"{m_var} ~ F_pre | {ID_COL} + prov_year_fe"
            print("[INFO] Notebook progress message.", fml_m)
            fit_m = run_feols(fml_m, data=df_med, cluster_var=CITY_COL)
            print(fit_m.summary())

            a, se_a = extract_coef_se(fit_m, "F_pre")
            print(f"[STEP 1] F_pre → {m_var}: a = {a:.4f}, se(a) = {se_a:.4f}")

            # =============================================================================
            # health_next = c' F_pre + b M_it + d health_it + FE + ε
            fml_y = (
                f"health_next ~ F_pre + {m_var} + {HEALTH_VAR} "
                f"| {ID_COL} + prov_year_fe"
            )
            print("[INFO] Notebook progress message.", fml_y)
            fit_y = run_feols(fml_y, data=df_med, cluster_var=CITY_COL)
            print(fit_y.summary())

            b, se_b = extract_coef_se(fit_y, m_var)
            c_prime, se_cprime = extract_coef_se(fit_y, "F_pre")

            print(f"[STEP 2] {m_var} → health_next: b = {b:.4f}, se(b) = {se_b:.4f}")
            print(
                f"[STEP 2] 直接效应 F_pre → health_next (c') = "
                f"{c_prime:.4f}, se(c') = {se_cprime:.4f}"
            )

            # =============================================================================
            indirect = a * b
            # Original notebook comment normalized for the public code archive.
            var_indirect = (b ** 2) * (se_a ** 2) + (a ** 2) * (se_b ** 2)
            se_indirect = float(np.sqrt(var_indirect))

            total = c_prime + indirect

            print("[INFO] Notebook progress message.")
            print("[INFO] Notebook progress message.")

            results.append(
                dict(
                    flood_var=f_var,
                    mediator=m_var,
                    mediator_label=m_label,
                    mediator_worse_when=worse_when,  # Original notebook comment normalized for the public code archive.
                    a=a,
                    se_a=se_a,
                    b=b,
                    se_b=se_b,
                    indirect=indirect,
                    se_indirect=se_indirect,
                    c_prime=c_prime,
                    se_cprime=se_cprime,
                    total_effect=total,
                    n=df_med.shape[0],
                )
            )

    # Original notebook comment normalized for the public code archive.
    if results:
        out_df = pd.DataFrame(results)
        out_path = DATA.with_name(DATA.stem + "_mediation_results_with_direction.csv")
        out_df.to_csv(out_path, index=False)
        print("[INFO] Notebook progress message.", out_path)
    else:
        print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    main()
