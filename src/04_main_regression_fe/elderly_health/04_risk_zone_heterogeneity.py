#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for 04_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


# ------------------------------------------------------------------------------
# Notebook cell 2
# ------------------------------------------------------------------------------
# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-

# """
# Original notebook comment normalized for the public code archive.
# ================================================

# Original notebook comment normalized for the public code archive.
# ----
# Original notebook comment normalized for the public code archive.
#     risk_area_share_rp100_dgt03_city
# Original notebook comment normalized for the public code archive.

# Original notebook comment normalized for the public code archive.
#     - bottom tercile -> low
#     - middle tercile -> middle
#     - top tercile    -> high

# Original notebook comment normalized for the public code archive.
# ----
# 1) city_risk_zone_rp100_dgt03.csv
# 2) city_risk_zone_rp100_dgt03.parquet
# 3) city_risk_zone_rp100_dgt03.gpkg

# Original notebook comment normalized for the public code archive.
# ----
# Original notebook comment normalized for the public code archive.
# City-level processing note.
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# """

# from pathlib import Path
# import numpy as np
# import pandas as pd
# import geopandas as gpd
# import rasterio
# from rasterio.features import rasterize
# from rasterio.transform import Affine


# # =========================================================
# # 0. CONFIG
# # =========================================================

# Original notebook comment normalized for the public code archive.
# RP100_TIF = Path(
#     "/home/ll/jupyter_notebook/result/fixed_rp_maps/"
#     "rp100_inundation_depth_p50.tif"
# )

# Original notebook comment normalized for the public code archive.
# CITY_SHP = Path(
#     "/home/ll/jupyter_notebook/gis_data/China/city/city.shp"
# )

# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
# ID field handling.
# City-level processing note.

# Original notebook comment normalized for the public code archive.
# RP_LABEL = "RP100"
# DEPTH_THRESHOLD = 0.3

# Original notebook comment normalized for the public code archive.
# OUT_DIR = Path("/home/ll/jupyter_notebook/result/impact_assessment/older")
# OUT_DIR.mkdir(parents=True, exist_ok=True)

# OUT_CSV = OUT_DIR / "city_risk_zone_rp100_dgt03.csv"
# OUT_PARQUET = OUT_DIR / "city_risk_zone_rp100_dgt03.parquet"
# OUT_GPKG = OUT_DIR / "city_risk_zone_rp100_dgt03.gpkg"

# Original notebook comment normalized for the public code archive.
# EARTH_RADIUS_KM = 6371.0088


# # =========================================================
# # 1. HELPERS
# # =========================================================

# def normalize_code_as_str(s: pd.Series) -> pd.Series:
#     """
# Original notebook comment normalized for the public code archive.
#     """
#     x = s.astype(str).str.strip()
#     x = x.str.replace(r"\.0$", "", regex=True)
#     return x


# def load_raster_geotiff(fp: Path):
#     """
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
#       depth: float32 (rows, cols)
#       transform: Affine
#       crs: rasterio CRS
#     """
#     if not fp.exists():
# Original notebook comment normalized for the public code archive.

#     with rasterio.open(fp) as src:
#         depth = src.read(1).astype("float32")
#         transform = src.transform
#         crs = src.crs
#         nodata = src.nodata

#     if nodata is not None:
#         depth = np.where(depth == nodata, np.nan, depth)

#     if crs is None:
# Original notebook comment normalized for the public code archive.

#     return depth, transform, crs


# def pixel_area_km2_by_row(transform: Affine, nrows: int, crs) -> np.ndarray:
#     """
# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.
#     """
#     if not crs.is_geographic:
# Original notebook comment normalized for the public code archive.

#     dlon_deg = abs(transform.a)
#     dlon_rad = np.deg2rad(dlon_deg)

#     row_index = np.arange(nrows)
#     lat_top = transform.f + row_index * transform.e
#     lat_bottom = transform.f + (row_index + 1) * transform.e

#     lat_top_rad = np.deg2rad(lat_top)
#     lat_bottom_rad = np.deg2rad(lat_bottom)

#     area_row = (
#         (EARTH_RADIUS_KM ** 2)
#         * dlon_rad
#         * np.abs(np.sin(lat_top_rad) - np.sin(lat_bottom_rad))
#     )
#     return area_row.reshape(-1, 1).astype("float64")


# def load_cities(target_crs):
#     """
# City-level processing note.
#     """
#     gdf = gpd.read_file(CITY_SHP)
#     if gdf.crs is None:
# City-level processing note.

#     gdf = gdf.to_crs(target_crs).copy()

#     if CITY_ID_FIELD not in gdf.columns:
# ID field handling.
#     if CITY_NAME_FIELD not in gdf.columns:
# City-level processing note.

#     gdf["city_code"] = normalize_code_as_str(gdf[CITY_ID_FIELD])
#     if CITY_NAME_FIELD in gdf.columns:
#         gdf["city_name"] = gdf[CITY_NAME_FIELD].astype(str).str.strip()
#     else:
#         gdf["city_name"] = ""

#     gdf = gdf.dropna(subset=["city_code", "geometry"]).copy()
#     gdf = gdf.reset_index(drop=True)
#     gdf["raster_id"] = np.arange(1, len(gdf) + 1, dtype=np.int32)

#     return gdf[["city_code", "city_name", "raster_id", "geometry"]]


# def rasterize_cities(gdf_city, out_shape, transform):
#     shapes = [(geom, rid) for geom, rid in zip(gdf_city.geometry, gdf_city["raster_id"])]
#     rid_grid = rasterize(
#         shapes=shapes,
#         out_shape=out_shape,
#         transform=transform,
#         fill=0,
#         dtype="int32",
#         all_touched=False
#     )
#     return rid_grid


# def assign_terciles_ranked(df, value_col):
#     """
# Original notebook comment normalized for the public code archive.
#     """
#     out = df.copy()
#     valid = out[value_col].notna()

#     sub = out.loc[valid].sort_values([value_col, "city_code"]).reset_index(drop=True)
#     n = len(sub)
#     if n < 3:
# Original notebook comment normalized for the public code archive.

#     pos = np.arange(n)
#     tercile = np.floor(3 * pos / n).astype(int) + 1   # 1,2,3

#     sub["risk_tercile"] = tercile
#     sub["risk_group"] = sub["risk_tercile"].map({
#         1: "low",
#         2: "middle",
#         3: "high",
#     })

#     out = out.merge(
#         sub[["city_code", "risk_tercile", "risk_group"]],
#         on="city_code",
#         how="left"
#     )
#     out["top_bottom_sample"] = out["risk_group"].isin(["low", "high"]).astype(int)
#     return out


# # =========================================================
# # 2. MAIN
# # =========================================================

# def main():
# Original notebook comment normalized for the public code archive.
#     depth, transform, crs = load_raster_geotiff(RP100_TIF)
#     nrows, ncols = depth.shape
#     print(f"[INFO] raster shape = {nrows} x {ncols}, CRS = {crs}")

# Original notebook comment normalized for the public code archive.
#     gdf_city = load_cities(crs)
# City-level processing note.

# Original notebook comment normalized for the public code archive.
#     rid_grid = rasterize_cities(gdf_city, depth.shape, transform)

# Original notebook comment normalized for the public code archive.
#     area_row = pixel_area_km2_by_row(transform, nrows, crs)
#     area_grid = np.broadcast_to(area_row, depth.shape)

# Original notebook comment normalized for the public code archive.
#     rid_flat = rid_grid.ravel()
#     depth_flat = depth.ravel()
#     area_flat = area_grid.ravel()

#     in_city = rid_flat > 0

# Original notebook comment normalized for the public code archive.
#     total_area = np.bincount(
#         rid_flat[in_city],
#         weights=area_flat[in_city],
#         minlength=len(gdf_city) + 1
#     )

# Original notebook comment normalized for the public code archive.
#     inund_mask = in_city & np.isfinite(depth_flat) & (depth_flat > DEPTH_THRESHOLD)
#     inund_area = np.bincount(
#         rid_flat[inund_mask],
#         weights=area_flat[inund_mask],
#         minlength=len(gdf_city) + 1
#     )

# Original notebook comment normalized for the public code archive.
#     df = gdf_city[["city_code", "city_name", "raster_id"]].copy()
#     df["city_total_area_km2_raster"] = df["raster_id"].map(lambda x: float(total_area[x]))
#     df["inund_area_km2_rp100_dgt03"] = df["raster_id"].map(lambda x: float(inund_area[x]))

#     df["risk_area_share_rp100_dgt03_city"] = np.where(
#         df["city_total_area_km2_raster"] > 0,
#         df["inund_area_km2_rp100_dgt03"] / df["city_total_area_km2_raster"],
#         np.nan
#     )

#     df["rp_label"] = RP_LABEL
#     df["depth_threshold_m"] = DEPTH_THRESHOLD

# Original notebook comment normalized for the public code archive.
#     df = assign_terciles_ranked(df, "risk_area_share_rp100_dgt03_city")

#     out_cols = [
#         "city_code",
#         "city_name",
#         "rp_label",
#         "depth_threshold_m",
#         "city_total_area_km2_raster",
#         "inund_area_km2_rp100_dgt03",
#         "risk_area_share_rp100_dgt03_city",
#         "risk_tercile",
#         "risk_group",
#         "top_bottom_sample",
#     ]
#     df_out = df[out_cols].copy()

#     df_out.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
#     df_out.to_parquet(OUT_PARQUET, index=False)

# Original notebook comment normalized for the public code archive.
# Original notebook comment normalized for the public code archive.

#     gdf_map = gdf_city.merge(df_out, on="city_code", how="left")
#     gdf_map.to_file(OUT_GPKG, layer="city_risk_zone", driver="GPKG")
# Original notebook comment normalized for the public code archive.

#     print("\n[SUMMARY] risk_group count:")
#     print(df_out["risk_group"].value_counts(dropna=False).sort_index())

#     print("\n[SUMMARY] area share by group:")
#     print(
#         df_out.groupby("risk_group", dropna=False)["risk_area_share_rp100_dgt03_city"]
#         .describe()
#     )

#     print("\n[HEAD]")
#     print(df_out.head())


# if __name__ == "__main__":
#     main()


# ------------------------------------------------------------------------------
# Notebook cell 4
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import geopandas as gpd
from pyproj import Geod

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)


# =========================================================
# 0. PATHS & CONFIG
# =========================================================

# Original notebook comment normalized for the public code archive.
COUNTY_SHP = Path("/home/ll/jupyter_notebook/gis_data/China/country/country.shp")
CITY_SHP   = Path("/home/ll/jupyter_notebook/gis_data/China/city/city.shp")

# Original notebook comment normalized for the public code archive.
COUNTY_RISK_PARQUET = Path(
    "/home/ll/jupyter_notebook/result/flood_risk_zone_rp100_dgt03/"
    "county_risk_zone_rp100_dgt03.parquet"
)

# Original notebook comment normalized for the public code archive.
OUT_DIR = Path("/home/ll/jupyter_notebook/result/impact_assessment/older")
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_CSV = OUT_DIR / "city_risk_zone_rp100_dgt03.csv"
OUT_PARQUET = OUT_DIR / "city_risk_zone_rp100_dgt03.parquet"
OUT_GPKG = OUT_DIR / "city_risk_zone_rp100_dgt03.gpkg"

# County-level processing note.
COUNTY_CODE_FIELD = "县代码"
COUNTY_NAME_FIELD = "县"
CITY_CODE_IN_COUNTY_FIELD = "市代码"
CITY_NAME_IN_COUNTY_FIELD = "市"

# City-level processing note.
CITY_CODE_FIELD = "市代码"
CITY_NAME_FIELD = "市"

# Original notebook comment normalized for the public code archive.
DOMINANCE_THRESHOLD = 0.50

# Original notebook comment normalized for the public code archive.
RP_LABEL = "RP100"
DEPTH_THRESHOLD_M = 0.3
CLASSIFICATION_METHOD = "county_area_weighted_dominance"


# =========================================================
# 1. HELPERS
# =========================================================

def normalize_code(s: pd.Series) -> pd.Series:
    x = s.astype(str).str.strip()
    x = x.replace({"nan": pd.NA, "None": pd.NA, "": pd.NA})
    x = x.str.replace(r"\.0$", "", regex=True)
    return x


def normalize_name(s: pd.Series) -> pd.Series:
    x = s.astype(str).str.strip()
    x = x.replace({"nan": pd.NA, "None": pd.NA, "": pd.NA})
    return x


def compute_geodesic_area_km2(gdf: gpd.GeoDataFrame) -> pd.Series:
    """Archived notebook note for 04_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if gdf.crs is None:
        raise ValueError("输入 GeoDataFrame 缺少 CRS。")
    if not gdf.crs.is_geographic:
        gdf = gdf.to_crs(4326)

    geod = Geod(ellps="WGS84")
    areas = []

    for geom in gdf.geometry:
        if geom is None or geom.is_empty:
            areas.append(np.nan)
            continue

        try:
            area_m2, _ = geod.geometry_area_perimeter(geom)
            areas.append(abs(area_m2) / 1e6)
        except Exception:
            areas.append(np.nan)

    return pd.Series(areas, index=gdf.index, dtype="float64")


def classify_city_risk(row, threshold=0.60):
    """Archived notebook note for 04_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    sh = row["share_high_area_in_city"]
    sl = row["share_low_area_in_city"]

    if pd.notna(sh) and sh >= threshold:
        return "high"
    if pd.notna(sl) and sl >= threshold:
        return "low"
    return "middle"


# =========================================================
# 2. LOAD DATA
# =========================================================

def load_inputs():
    print("[INFO] Notebook progress message.")
    gdf_county = gpd.read_file(COUNTY_SHP)
    print(f"[INFO] county.shp shape = {gdf_county.shape}, CRS = {gdf_county.crs}")

    print("[INFO] Notebook progress message.")
    gdf_city = gpd.read_file(CITY_SHP)
    print(f"[INFO] city.shp shape = {gdf_city.shape}, CRS = {gdf_city.crs}")

    print("[INFO] Notebook progress message.")
    df_risk = pd.read_parquet(COUNTY_RISK_PARQUET)
    print(f"[INFO] county risk shape = {df_risk.shape}")

    return gdf_county, gdf_city, df_risk


# =========================================================
# 3. PREPARE COUNTY TABLE
# =========================================================

def prepare_county_table(gdf_county: gpd.GeoDataFrame, df_risk: pd.DataFrame) -> pd.DataFrame:
    required_county_cols = [
        COUNTY_CODE_FIELD,
        COUNTY_NAME_FIELD,
        CITY_CODE_IN_COUNTY_FIELD,
        CITY_NAME_IN_COUNTY_FIELD,
        "geometry",
    ]
    miss_county = [c for c in required_county_cols if c not in gdf_county.columns]
    if miss_county:
        raise KeyError(f"county.shp 缺少字段：{miss_county}")

    gdf_county = gdf_county.copy()
    gdf_county["county_code"] = normalize_code(gdf_county[COUNTY_CODE_FIELD])
    gdf_county["county_name"] = normalize_name(gdf_county[COUNTY_NAME_FIELD])
    gdf_county["city_code"] = normalize_code(gdf_county[CITY_CODE_IN_COUNTY_FIELD])
    gdf_county["city_name"] = normalize_name(gdf_county[CITY_NAME_IN_COUNTY_FIELD])

    # Original notebook comment normalized for the public code archive.
    risk_code_candidates = ["county_code", "县代码"]
    risk_code_col = next((c for c in risk_code_candidates if c in df_risk.columns), None)
    if risk_code_col is None:
        raise KeyError("县级风险表中找不到 county_code 或 县代码 字段。")

    required_risk_cols = [risk_code_col, "risk_group", "risk_area_share_rp100_dgt03"]
    miss_risk = [c for c in required_risk_cols if c not in df_risk.columns]
    if miss_risk:
        raise KeyError(f"县级风险表缺少字段：{miss_risk}")

    df_risk = df_risk.copy()
    df_risk["county_code"] = normalize_code(df_risk[risk_code_col])

    # Original notebook comment normalized for the public code archive.
    if "county_total_area_km2_raster" in df_risk.columns:
        df_risk["county_area_km2_weight"] = pd.to_numeric(
            df_risk["county_total_area_km2_raster"], errors="coerce"
        )
        area_source = "county_total_area_km2_raster"
    else:
        # County-level processing note.
        print("[INFO] Notebook progress message.")
        gdf_county["county_area_km2_geom"] = compute_geodesic_area_km2(gdf_county)
        area_source = "county_area_km2_geom"

    # Original notebook comment normalized for the public code archive.
    df_county = gdf_county.merge(
        df_risk.drop_duplicates(subset=["county_code"]),
        how="left",
        on="county_code",
        validate="1:1",
        suffixes=("", "_risk")
    )

    # Original notebook comment normalized for the public code archive.
    if area_source == "county_total_area_km2_raster":
        df_county["county_area_km2_weight"] = pd.to_numeric(
            df_county["county_area_km2_weight"], errors="coerce"
        )
    else:
        df_county["county_area_km2_weight"] = pd.to_numeric(
            df_county["county_area_km2_geom"], errors="coerce"
        )

    # Original notebook comment normalized for the public code archive.
    match_rate = df_county["risk_group"].notna().mean()
    print("[INFO] Notebook progress message.")

    if match_rate < 0.95:
        raise ValueError("县级风险表与 county.shp 的匹配率过低，请检查县代码。")

    return df_county


# =========================================================
# 4. AGGREGATE COUNTY -> CITY
# =========================================================

def aggregate_to_city(df_county: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 04_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    print("[INFO] Notebook progress message.")

    df = df_county.copy()

    # City-level processing note.
    df = df[df["city_code"].notna()].copy()

    # Original notebook comment normalized for the public code archive.
    df["county_area_km2_weight"] = pd.to_numeric(df["county_area_km2_weight"], errors="coerce")
    df["risk_area_share_rp100_dgt03"] = pd.to_numeric(df["risk_area_share_rp100_dgt03"], errors="coerce")

    # Original notebook comment normalized for the public code archive.
    df["area_high_km2"] = np.where(df["risk_group"] == "high", df["county_area_km2_weight"], 0.0)
    df["area_low_km2"] = np.where(df["risk_group"] == "low", df["county_area_km2_weight"], 0.0)
    df["area_middle_km2"] = np.where(df["risk_group"] == "middle", df["county_area_km2_weight"], 0.0)

    # Original notebook comment normalized for the public code archive.
    df["risk_x_area"] = df["risk_area_share_rp100_dgt03"] * df["county_area_km2_weight"]

    def agg_one(g: pd.DataFrame) -> pd.Series:
        total_area = g["county_area_km2_weight"].sum(min_count=1)
        high_area = g["area_high_km2"].sum(min_count=1)
        low_area = g["area_low_km2"].sum(min_count=1)
        middle_area = g["area_middle_km2"].sum(min_count=1)

        # Original notebook comment normalized for the public code archive.
        risk_num = g["risk_x_area"].sum(min_count=1)
        risk_den = g["county_area_km2_weight"].sum(min_count=1)
        risk_cont = risk_num / risk_den if pd.notna(risk_den) and risk_den > 0 else np.nan

        return pd.Series({
            "city_name_from_county": g["city_name"].dropna().iloc[0] if g["city_name"].notna().any() else pd.NA,
            "n_counties_total": g["county_code"].nunique(),
            "n_counties_high": (g["risk_group"] == "high").sum(),
            "n_counties_middle": (g["risk_group"] == "middle").sum(),
            "n_counties_low": (g["risk_group"] == "low").sum(),
            "city_total_area_km2_raster": total_area,
            "city_high_county_area_km2": high_area,
            "city_middle_county_area_km2": middle_area,
            "city_low_county_area_km2": low_area,
            "share_high_area_in_city": high_area / total_area if pd.notna(total_area) and total_area > 0 else np.nan,
            "share_middle_area_in_city": middle_area / total_area if pd.notna(total_area) and total_area > 0 else np.nan,
            "share_low_area_in_city": low_area / total_area if pd.notna(total_area) and total_area > 0 else np.nan,
            "risk_area_share_rp100_dgt03_city": risk_cont,
        })

    df_city = (
        df.groupby("city_code", as_index=False)
          .apply(agg_one)
          .reset_index(drop=True)
    )

    # Original notebook comment normalized for the public code archive.
    df_city["risk_group"] = df_city.apply(
        classify_city_risk, axis=1, threshold=DOMINANCE_THRESHOLD
    )

    # Original notebook comment normalized for the public code archive.
    df_city["risk_tercile"] = df_city["risk_group"].map({
        "low": 1,
        "middle": 2,
        "high": 3,
    }).astype("Int64")

    df_city["top_bottom_sample"] = df_city["risk_group"].isin(["low", "high"]).astype(int)

    # Original notebook comment normalized for the public code archive.
    df_city["rp_label"] = RP_LABEL
    df_city["depth_threshold_m"] = DEPTH_THRESHOLD_M
    df_city["classification_method"] = CLASSIFICATION_METHOD
    df_city["dominance_threshold"] = DOMINANCE_THRESHOLD

    return df_city


# =========================================================
# 5. MERGE CITY GEOMETRY & SAVE
# =========================================================

def merge_city_geometry_and_save(gdf_city: gpd.GeoDataFrame, df_city_risk: pd.DataFrame):
    required_city_cols = [CITY_CODE_FIELD, CITY_NAME_FIELD, "geometry"]
    miss = [c for c in required_city_cols if c not in gdf_city.columns]
    if miss:
        raise KeyError(f"city.shp 缺少字段：{miss}")

    gdf_city = gdf_city.copy()
    gdf_city["city_code"] = normalize_code(gdf_city[CITY_CODE_FIELD])
    gdf_city["city_name"] = normalize_name(gdf_city[CITY_NAME_FIELD])

    # Original notebook comment normalized for the public code archive.
    gdf_out = gdf_city.merge(
        df_city_risk,
        how="left",
        on="city_code",
        validate="1:1",
        suffixes=("", "_agg")
    )

    # City-level processing note.
    if "city_name_from_county" in gdf_out.columns:
        gdf_out["city_name_final"] = gdf_out["city_name"]
        miss_name = gdf_out["city_name_final"].isna() | (gdf_out["city_name_final"] == "")
        gdf_out.loc[miss_name, "city_name_final"] = gdf_out.loc[miss_name, "city_name_from_county"]
    else:
        gdf_out["city_name_final"] = gdf_out["city_name"]

    # City-level processing note.
    gdf_out = gdf_out.rename(columns={"city_name_final": "city_name_out"})

    out_cols = [
        "city_code",
        "city_name_out",
        "rp_label",
        "depth_threshold_m",
        "classification_method",
        "dominance_threshold",
        "n_counties_total",
        "n_counties_high",
        "n_counties_middle",
        "n_counties_low",
        "city_total_area_km2_raster",
        "city_high_county_area_km2",
        "city_middle_county_area_km2",
        "city_low_county_area_km2",
        "share_high_area_in_city",
        "share_middle_area_in_city",
        "share_low_area_in_city",
        "risk_area_share_rp100_dgt03_city",
        "risk_tercile",
        "risk_group",
        "top_bottom_sample",
    ]

    # Original notebook comment normalized for the public code archive.
    miss_out = [c for c in out_cols if c not in gdf_out.columns]
    if miss_out:
        raise KeyError(f"最终输出缺少字段：{miss_out}")

    df_tab = gdf_out[out_cols].copy()
    df_tab = df_tab.rename(columns={"city_name_out": "city_name"})

    # Original notebook comment normalized for the public code archive.
    df_tab.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    df_tab.to_parquet(OUT_PARQUET, index=False)

    # Original notebook comment normalized for the public code archive.
    gdf_map = gdf_out[out_cols + ["geometry"]].copy()
    gdf_map = gdf_map.rename(columns={"city_name_out": "city_name"})

    if OUT_GPKG.exists():
        OUT_GPKG.unlink()

    gdf_map.to_file(OUT_GPKG, layer="city_risk_zone", driver="GPKG")

    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")

    # Original notebook comment normalized for the public code archive.
    print("\n[SUMMARY] risk_group count:")
    print(df_tab["risk_group"].value_counts(dropna=False).sort_index())

    print("\n[SUMMARY] weighted continuous risk by group:")
    print(
        df_tab.groupby("risk_group", dropna=False)["risk_area_share_rp100_dgt03_city"]
        .describe()
    )

    print("\n[SUMMARY] share_high_area_in_city by group:")
    print(
        df_tab.groupby("risk_group", dropna=False)["share_high_area_in_city"]
        .describe()
    )

    print("\n[HEAD]")
    print(df_tab.head())

# =========================================================
# 6. MAIN
# =========================================================

def main():
    gdf_county, gdf_city, df_risk = load_inputs()
    df_county = prepare_county_table(gdf_county, df_risk)
    df_city_risk = aggregate_to_city(df_county)
    merge_city_geometry_and_save(gdf_city, df_city_risk)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 7
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm

# =========================================================
# 0. CONFIG
# =========================================================

# City-level processing note.
PANEL_MERGED = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/flood_health_result/"
    "charls_health_panel_60plus_with_index_Tall_5_10_20_30y.parquet"
)

# Original notebook comment normalized for the public code archive.
CITY_RISK_PARQUET = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/"
    "city_risk_zone_rp100_dgt03.parquet"
)

OUT_DIR = PANEL_MERGED.parent
OUT_DIR.mkdir(parents=True, exist_ok=True)

Y_VAR = "health_index_z"

T_LIST = [2, 5, 10, 20, 50, 100]
WINDOW_LIST = [5, 10, 20, 30]

ID_COL = "pid12"
CITY_COL = "city_code"
YEAR_COL = "year"
PROV_COL = "province"

# Original notebook comment normalized for the public code archive.
RISK_GROUPS = ["low", "high"]

# Original notebook comment normalized for the public code archive.
SAMPLE_SPECS = {
    "all": None,
    "urban": 1,
    "rural": 0,
}

# Original notebook comment normalized for the public code archive.
MIN_NOBS = 100
MIN_NCITY = 10


# =========================================================
# 1. HELPERS
# =========================================================

def normalize_code_as_str(s: pd.Series) -> pd.Series:
    x = s.astype(str).str.strip()
    x = x.str.replace(r"\.0$", "", regex=True)
    return x


def demean_two_fe(df, cols, fe1, fe2):
    """Archived notebook note for 04_risk_zone_heterogeneity.

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
    """Archived notebook note for 04_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    cols_needed = [y_col] + x_cols + [fe1, fe2, cluster_col]
    df = df.dropna(subset=cols_needed).copy()

    df = df[df[cluster_col].notna()].copy()
    if df.empty:
        raise ValueError("所有观测在 cluster_col 上都缺失，无法回归。")

    df = demean_two_fe(df, [y_col] + x_cols, fe1=fe1, fe2=fe2)

    y = df[f"{y_col}_dm"].to_numpy()
    X = df[[f"{c}_dm" for c in x_cols]].to_numpy()

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


def load_city_risk():
    df = pd.read_parquet(CITY_RISK_PARQUET)

    needed = ["city_code", "risk_group", "risk_area_share_rp100_dgt03_city", "top_bottom_sample"]
    miss = [c for c in needed if c not in df.columns]
    if miss:
        raise KeyError(f"风险表缺少列：{miss}")

    df["city_code"] = normalize_code_as_str(df["city_code"])
    df = df[df["risk_group"].isin(RISK_GROUPS)].copy()

    return df[["city_code", "risk_group", "risk_area_share_rp100_dgt03_city"]].drop_duplicates("city_code")


# =========================================================
# 2. MAIN REGRESSION
# =========================================================

def run_individual_fe_city_cluster_highlowrisk():
    print(f"[READ] merged 60+ panel: {PANEL_MERGED}")
    df = pd.read_parquet(PANEL_MERGED)

    print(f"[READ] city risk table: {CITY_RISK_PARQUET}")
    df_risk = load_city_risk()

    # City-level processing note.
    df[CITY_COL] = normalize_code_as_str(df[CITY_COL])

    # Original notebook comment normalized for the public code archive.
    df = df.merge(df_risk, how="left", left_on=CITY_COL, right_on="city_code", validate="m:1")
    df = df[df["risk_group"].isin(RISK_GROUPS)].copy()

    print("[INFO] Notebook progress message.")
    print(df["risk_group"].value_counts(dropna=False))

    # Original notebook comment normalized for the public code archive.
    df[Y_VAR] = pd.to_numeric(df[Y_VAR], errors="coerce")
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df[YEAR_COL] = pd.to_numeric(df[YEAR_COL], errors="coerce")

    # Original notebook comment normalized for the public code archive.
    df = df.dropna(subset=[Y_VAR, "age", ID_COL, PROV_COL, CITY_COL, YEAR_COL, "risk_group"]).copy()

    # Original notebook comment normalized for the public code archive.
    df["age2"] = df["age"] ** 2

    # province × year FE
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
        f"总行数: {len(df)}, 年份数: {df[YEAR_COL].nunique()}, 城市数: {df[CITY_COL].nunique()}"
    )

    all_rows = []

    for window in WINDOW_LIST:
        exposure_cols = {T: f"share_flood_T{T}_{window}y" for T in T_LIST}

        for T, exp_col in exposure_cols.items():
            if exp_col not in df.columns:
                print("[INFO] Notebook progress message.")
                continue

            for sample_name, group_val in SAMPLE_SPECS.items():
                for risk_group in RISK_GROUPS:
                    sub = df.copy()

                    # all / rural / urban
                    if group_val is not None:
                        sub = sub[sub["urban_group"] == group_val].copy()

                    # low / high
                    sub = sub[sub["risk_group"] == risk_group].copy()

                    # Original notebook comment normalized for the public code archive.
                    waves_sub = sub.groupby(ID_COL)[YEAR_COL].nunique()
                    keep_ids_sub = waves_sub[waves_sub >= 2].index
                    sub = sub[sub[ID_COL].isin(keep_ids_sub)].copy()

                    if len(sub) < MIN_NOBS or sub[CITY_COL].nunique() < MIN_NCITY:
                        print(
                            f"[WARN] window={window}, T={T}, sample={sample_name}, risk={risk_group} "
                            f"样本量或城市数过小 (N={len(sub)}, N_city={sub[CITY_COL].nunique()})，跳过。"
                        )
                        continue

                    x_cols = [exp_col, "age", "age2"]

                    res = fe_reg_twoFE_city_cluster(
                        sub,
                        y_col=Y_VAR,
                        x_cols=x_cols,
                        fe1=ID_COL,
                        fe2="prov_year",
                        cluster_col=CITY_COL,
                    )

                    row = res.loc[exp_col].copy()
                    row["Y_var"] = Y_VAR
                    row["window"] = window
                    row["T"] = T
                    row["exposure"] = exp_col
                    row["sample"] = sample_name
                    row["risk_group"] = risk_group
                    row["N"] = len(sub)
                    row["N_id"] = sub[ID_COL].nunique()
                    row["N_year"] = sub[YEAR_COL].nunique()
                    row["N_city"] = sub[CITY_COL].nunique()
                    row["mean_depvar"] = sub[Y_VAR].mean()

                    print("\n" + "=" * 60)
                    print(
                        f"[RESULT] Y={Y_VAR}, window={window}y, T={T}, "
                        f"sample={sample_name}, risk_group={risk_group}"
                    )
                    print(res.loc[[exp_col]][["Estimate", "Pr(>|t|)"]])

                    all_rows.append(row)

    if not all_rows:
        print("[INFO] Notebook progress message.")
        return

    out_df = pd.DataFrame(all_rows)
    out_df = out_df[
        [
            "Y_var", "window", "T", "exposure", "sample", "risk_group",
            "Estimate", "Std. Error", "t value", "Pr(>|t|)",
            "2.5%", "97.5%",
            "N", "N_id", "N_year", "N_city", "mean_depvar",
        ]
    ].sort_values(["Y_var", "sample", "risk_group", "window", "T"])

    print("\n" + "=" * 80)
    print("[INFO] Notebook progress message.")
    print(out_df.head(20))

    out_path = OUT_DIR / f"fe_{Y_VAR}_Tall_5_10_20_30y_pid12_provYearFE_cityCluster_highlowRisk.csv"
    out_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")


if __name__ == "__main__":
    run_individual_fe_city_cluster_highlowrisk()


# ------------------------------------------------------------------------------
# Notebook cell 8
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
from math import erf, sqrt

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# =========================================================
# 0. PATHS & CONFIG
# =========================================================

OUT_DIR = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/flood_health_result"
)

RES_CSV = OUT_DIR / "fe_health_index_z_Tall_5_10_20_30y_pid12_provYearFE_cityCluster_highlowRisk.csv"

Y_VAR = "health_index_z"
SAMPLES = ["all", "rural", "urban"]
RISK_GROUPS = ["low", "high"]
T_LIST = [2, 5, 10, 20, 50, 100]

OUT_AGG_CSV = OUT_DIR / "fe_health_index_z_Tall_windowAgg_over_T_highlowRisk.csv"
OUT_GRID_CSV = OUT_DIR / "betaT_health_index_z_highlowRisk_meta_grid.csv"

OUT_FIG_COMBINED = OUT_DIR / "betaT_health_index_z_highlowRisk_all_rural_urban.png"
OUT_FIG_ALL = OUT_DIR / "betaT_health_index_z_highlowRisk_all.png"
OUT_FIG_RURAL = OUT_DIR / "betaT_health_index_z_highlowRisk_rural.png"
OUT_FIG_URBAN = OUT_DIR / "betaT_health_index_z_highlowRisk_urban.png"


# =========================================================
# 1. SMALL TOOLS
# =========================================================

def norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))


def stars_for_p(p: float) -> str:
    try:
        p = float(p)
    except (TypeError, ValueError):
        return ""
    if np.isnan(p):
        return ""
    if p < 0.001:
        return "***"
    elif p < 0.05:
        return "**"
    elif p < 0.10:
        return "*"
    else:
        return ""


# =========================================================
# 2. READ FE RESULTS
# =========================================================

def read_fe_result() -> pd.DataFrame:
    print("[INFO] Notebook progress message.")
    df = pd.read_csv(RES_CSV)

    needed = [
        "Y_var", "window", "T", "sample", "risk_group",
        "Estimate", "Std. Error", "Pr(>|t|)",
        "2.5%", "97.5%", "N"
    ]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise KeyError(f"结果文件缺少必要列: {missing}")

    df = df[df["Y_var"] == Y_VAR].copy()

    df["window"] = pd.to_numeric(df["window"], errors="coerce")
    df["T"] = pd.to_numeric(df["T"], errors="coerce")

    for col in ["Estimate", "Std. Error", "Pr(>|t|)", "2.5%", "97.5%", "N"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["window", "T", "Estimate", "Std. Error", "sample", "risk_group"])
    df["window"] = df["window"].astype(int)
    df["T"] = df["T"].astype(int)
    df["sample"] = df["sample"].astype(str)
    df["risk_group"] = df["risk_group"].astype(str)

    print("[INFO] Notebook progress message.")
    print(df.head())
    return df


# =========================================================
# 3. AGGREGATE ACROSS WINDOW
# =========================================================

def aggregate_across_window(df: pd.DataFrame) -> pd.DataFrame:
    """Archived notebook note for 04_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    group_cols = ["Y_var", "sample", "risk_group", "T"]

    def agg_one(g: pd.DataFrame) -> pd.Series:
        est = g["Estimate"].to_numpy(float)
        se = g["Std. Error"].to_numpy(float)

        var = se ** 2
        var[var <= 0] = 1e-12
        w = 1.0 / var

        beta_w = float(np.sum(w * est) / np.sum(w))
        var_w = float(1.0 / np.sum(w))
        se_w = float(np.sqrt(var_w))

        if se_w > 0:
            t_val = beta_w / se_w
            p_val = 2.0 * (1.0 - norm_cdf(abs(t_val)))
        else:
            t_val = np.nan
            p_val = np.nan

        ci_low = beta_w - 1.96 * se_w
        ci_high = beta_w + 1.96 * se_w

        win_list = sorted(g["window"].astype(int).unique().tolist())

        return pd.Series(
            {
                "Estimate": beta_w,
                "Std. Error": se_w,
                "t value": t_val,
                "Pr(>|t|)": p_val,
                "2.5%": ci_low,
                "97.5%": ci_high,
                "n_window": len(win_list),
                "window_list": ",".join(str(w) for w in win_list),
                "N_min": g["N"].min(),
                "N_max": g["N"].max(),
            }
        )

    print("[INFO] Notebook progress message.")
    df_T = (
        df.groupby(group_cols, as_index=False)
          .apply(agg_one)
    )

    df_T = df_T.sort_values(["sample", "risk_group", "T"]).reset_index(drop=True)
    df_T.to_csv(OUT_AGG_CSV, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")

    print("[INFO] Notebook progress message.")
    print(df_T.head(12))
    return df_T


# =========================================================
# 4. FIT META-REGRESSION OVER T
# =========================================================

def fit_beta_curve_and_grid(df_T: pd.DataFrame):
    """Archived notebook note for 04_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    grid_all = []

    for sample in SAMPLES:
        for risk_group in RISK_GROUPS:
            sub = df_T[
                (df_T["Y_var"] == Y_VAR) &
                (df_T["sample"] == sample) &
                (df_T["risk_group"] == risk_group) &
                (df_T["T"].isin(T_LIST))
            ].copy()

            if sub.empty:
                print("[INFO] Notebook progress message.")
                continue

            sub = sub.sort_values("T")
            T_vals = sub["T"].to_numpy(float)
            est = sub["Estimate"].to_numpy(float)
            se = sub["Std. Error"].to_numpy(float)

            var = se ** 2
            var[var <= 0] = 1e-12
            w = 1.0 / var

            logT = np.log(T_vals)

            if len(T_vals) >= 3:
                X = np.column_stack([np.ones_like(logT), logT, logT**2])
                degree = 2
            elif len(T_vals) == 2:
                X = np.column_stack([np.ones_like(logT), logT])
                degree = 1
            else:
                X = np.ones((len(logT), 1))
                degree = 0

            model = sm.WLS(est, X, weights=w)
            fit = model.fit()

            gamma = np.asarray(fit.params, dtype="float64")
            Sigma = np.asarray(fit.cov_params(), dtype="float64")

            print("[INFO] Notebook progress message.")
            print(fit.summary())

            T_min, T_max = float(T_vals.min()), float(T_vals.max())
            logT_grid = np.linspace(np.log(T_min), np.log(T_max), 200)
            T_grid = np.exp(logT_grid)

            def design_vec(lt: float) -> np.ndarray:
                if degree == 2:
                    return np.array([1.0, lt, lt**2], dtype="float64")
                elif degree == 1:
                    return np.array([1.0, lt], dtype="float64")
                else:
                    return np.array([1.0], dtype="float64")

            beta_grid = []
            se_grid = []
            for lt in logT_grid:
                v = design_vec(lt)
                b = float(v @ gamma)
                var_b = float(v @ Sigma @ v)
                var_b = max(var_b, 0.0)
                beta_grid.append(b)
                se_grid.append(np.sqrt(var_b))

            beta_grid = np.array(beta_grid)
            se_grid = np.array(se_grid)
            ci_low = beta_grid - 1.96 * se_grid
            ci_high = beta_grid + 1.96 * se_grid

            grid_df = pd.DataFrame({
                "Y_var": Y_VAR,
                "sample": sample,
                "risk_group": risk_group,
                "T_grid": T_grid,
                "beta_grid": beta_grid,
                "se_grid": se_grid,
                "ci_low": ci_low,
                "ci_high": ci_high,
            })
            grid_all.append(grid_df)

    if not grid_all:
        raise RuntimeError("没有任何成功拟合的 β(T) 曲线。")

    meta_grid_df = pd.concat(grid_all, ignore_index=True)
    meta_grid_df.to_csv(OUT_GRID_CSV, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")

    return meta_grid_df


# =========================================================
# 5. PLOTTING
# =========================================================

def compute_global_ylim(df_T: pd.DataFrame, df_grid: pd.DataFrame):
    vals = []

    for col in ["2.5%", "97.5%"]:
        if col in df_T.columns:
            vals.extend(df_T[col].dropna().tolist())

    for col in ["ci_low", "ci_high"]:
        if col in df_grid.columns:
            vals.extend(df_grid[col].dropna().tolist())

    vals = np.array(vals, dtype=float)
    vals = vals[np.isfinite(vals)]

    if vals.size == 0:
        return (-0.5, 0.5)

    ymin = vals.min()
    ymax = vals.max()
    yr = ymax - ymin
    pad = 0.08 * yr if yr > 0 else 0.1
    return (ymin - pad, ymax + pad)


def plot_one_panel(ax, df_T: pd.DataFrame, df_grid: pd.DataFrame, sample: str, ylims=None):
    """Archived notebook note for 04_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    style_map = {
        "low":  {"color": "#1f77b4", "label": "Low-risk"},
        "high": {"color": "#d62728", "label": "High-risk"},
    }

    subT = df_T[(df_T["sample"] == sample) & (df_T["Y_var"] == Y_VAR)].copy()
    subG = df_grid[(df_grid["sample"] == sample) & (df_grid["Y_var"] == Y_VAR)].copy()

    if subT.empty or subG.empty:
        ax.text(0.5, 0.5, f"No data: {sample}", ha="center", va="center", transform=ax.transAxes)
        return

    # Original notebook comment normalized for the public code archive.
    vals = []
    vals.extend(subT["2.5%"].dropna().tolist())
    vals.extend(subT["97.5%"].dropna().tolist())
    vals.extend(subG["ci_low"].dropna().tolist())
    vals.extend(subG["ci_high"].dropna().tolist())
    vals = np.array(vals, dtype=float)
    vals = vals[np.isfinite(vals)]
    yr = vals.max() - vals.min() if vals.size > 0 else 1.0
    offset = 0.03 * yr if yr > 0 else 0.03

    for risk_group in RISK_GROUPS:
        color = style_map[risk_group]["color"]

        # Original notebook comment normalized for the public code archive.
        g = subG[subG["risk_group"] == risk_group].copy()
        g = g.sort_values("T_grid")
        ax.plot(
            g["T_grid"].to_numpy(float),
            g["beta_grid"].to_numpy(float),
            color=color,
            linewidth=2.0,
            label=style_map[risk_group]["label"]
        )
        ax.fill_between(
            g["T_grid"].to_numpy(float),
            g["ci_low"].to_numpy(float),
            g["ci_high"].to_numpy(float),
            color=color,
            alpha=0.18
        )

        # Original notebook comment normalized for the public code archive.
        t = subT[subT["risk_group"] == risk_group].copy()
        t = t.sort_values("T")
        if not t.empty:
            xmult = 0.96 if risk_group == "low" else 1.04
            T_vals = t["T"].to_numpy(float) * xmult
            est = t["Estimate"].to_numpy(float)
            se = t["Std. Error"].to_numpy(float)
            ci_low = est - 1.96 * se
            ci_high = est + 1.96 * se

            ax.errorbar(
                T_vals,
                est,
                yerr=[est - ci_low, ci_high - est],
                fmt="o",
                linestyle="none",
                capsize=4,
                color=color
            )

            pvals = t["Pr(>|t|)"].to_numpy(float)
            for T0, b, p in zip(T_vals, est, pvals):
                star = stars_for_p(p)
                if star:
                    ax.text(
                        T0,
                        b + offset,
                        star,
                        ha="center",
                        va="bottom",
                        fontsize=10,
                        color=color,
                    )

    ax.axhline(0, linestyle="--", linewidth=1, color="gray")
    ax.set_xscale("log")
    ax.set_xlim(min(T_LIST) * 0.9, max(T_LIST) * 1.1)
    ax.set_xticks(T_LIST)
    ax.get_xaxis().set_major_formatter(mticker.ScalarFormatter())
    ax.get_xaxis().set_minor_formatter(mticker.NullFormatter())

    if ylims is not None:
        ax.set_ylim(*ylims)

    title_map = {
        "all": "All sample",
        "rural": "Rural sample",
        "urban": "Urban sample",
    }
    ax.set_title(title_map.get(sample, sample), fontsize=13)


def plot_combined(df_T: pd.DataFrame, df_grid: pd.DataFrame):
    """Archived notebook note for 04_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.8), sharey=True)
    ylims = compute_global_ylim(df_T, df_grid)

    for ax, sample in zip(axes, SAMPLES):
        plot_one_panel(ax, df_T, df_grid, sample=sample, ylims=ylims)
        ax.set_xlabel("Flood return period T (years, log scale)", fontsize=12)

    axes[0].set_ylabel("Effect on health_index_z", fontsize=13)

    handles, labels = axes[0].get_legend_handles_labels()
    if handles:
        fig.legend(
            handles, labels,
            loc="upper center",
            ncol=2,
            frameon=False,
            fontsize=12,
            bbox_to_anchor=(0.5, 1.02)
        )

    fig.suptitle(
        "Nonlinear severity profile β(T) of flood exposure on older adults' health_index_z\n"
        "Comparison between low- and high-background-risk cities",
        fontsize=17, y=1.08
    )

    fig.text(
        0.5, -0.02,
        "Notes: β(T) is estimated by weighted meta-regression over return periods; "
        "shaded bands denote 95% CI; stars: *** p<0.01, ** p<0.05, * p<0.10.",
        ha="center", fontsize=10
    )

    plt.tight_layout()
    plt.savefig(OUT_FIG_COMBINED, dpi=250, bbox_inches="tight")
    plt.show()
    print("[INFO] Notebook progress message.")


def plot_single(df_T: pd.DataFrame, df_grid: pd.DataFrame, sample: str, out_path: Path):
    """Archived notebook note for 04_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    ylims = compute_global_ylim(
        df_T[(df_T["sample"] == sample)],
        df_grid[(df_grid["sample"] == sample)]
    )

    plot_one_panel(ax, df_T, df_grid, sample=sample, ylims=ylims)

    ax.set_xlabel("Flood return period T (years, log scale)", fontsize=12)
    ax.set_ylabel("Effect on health_index_z", fontsize=13)

    title_map = {
        "all": "All sample",
        "rural": "Rural sample",
        "urban": "Urban sample",
    }
    ax.set_title(
        "Nonlinear severity profile β(T) of flood exposure on older adults' health_index_z\n"
        f"Comparison between low- and high-background-risk cities ({title_map.get(sample, sample)})",
        fontsize=14
    )

    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(handles, labels, frameon=False, fontsize=11, loc="best")

    fig.text(
        0.5, -0.03,
        "Notes: shaded bands denote 95% CI; stars: *** p<0.01, ** p<0.05, * p<0.10.",
        ha="center", fontsize=10
    )

    plt.tight_layout()
    plt.savefig(out_path, dpi=250, bbox_inches="tight")
    plt.show()
    print("[INFO] Notebook progress message.")


# =========================================================
# 6. MAIN
# =========================================================

def main():
    df_fe = read_fe_result()
    df_Tagg = aggregate_across_window(df_fe)
    df_grid = fit_beta_curve_and_grid(df_Tagg)

    plot_combined(df_Tagg, df_grid)
    plot_single(df_Tagg, df_grid, sample="all", out_path=OUT_FIG_ALL)
    plot_single(df_Tagg, df_grid, sample="rural", out_path=OUT_FIG_RURAL)
    plot_single(df_Tagg, df_grid, sample="urban", out_path=OUT_FIG_URBAN)


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 9
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.features import rasterize
from rasterio.transform import Affine
from pyfixest.estimation import feols

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)
warnings.simplefilter("ignore", RuntimeWarning)

# =========================================================
# 0. CONFIG
# =========================================================

FIXED_RP_DIR = Path("/home/ll/jupyter_notebook/result/fixed_rp_maps")
RP_TIF_MAP = {
    20: FIXED_RP_DIR / "rp20_inundation_depth_p50.tif",
    50: FIXED_RP_DIR / "rp50_inundation_depth_p50.tif",
    100: FIXED_RP_DIR / "rp100_inundation_depth_p50.tif",
}

COUNTY_SHP = Path("/home/ll/jupyter_notebook/gis_data/China/country/country.shp")
COUNTY_CODE_FIELD = "县代码"
COUNTY_NAME_FIELD = "县"

EDU_PARQUET = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/flood/"
    "edu_micro_2015_with_storage_BM_T2_5_10_20_50_100.parquet"
)

BASE_OUT = Path("/home/ll/jupyter_notebook/result/impact_assessment/风险分区_稳健性分析")
OUT_DIR = BASE_OUT / "children_education_corrected"
COUNTY_RISK_DIR = OUT_DIR / "county_risk_tables"
REG_DIR = OUT_DIR / "regression_results"

COUNTY_RISK_DIR.mkdir(parents=True, exist_ok=True)
REG_DIR.mkdir(parents=True, exist_ok=True)

OUT_MASTER_CSV = REG_DIR / "edu_robustness_corrected_9scenarios_all_results.csv"
OUT_MASTER_PARQUET = REG_DIR / "edu_robustness_corrected_9scenarios_all_results.parquet"
OUT_SUMMARY_CSV = REG_DIR / "edu_robustness_corrected_9scenarios_summary.csv"

RP_LIST = [20, 50, 100]
DEPTH_LIST = [0.1, 0.3, 0.5]

BIRTH_MIN, BIRTH_MAX = 1980, 2000
AGE_MIN, AGE_MAX = 15, 35
ONLY_NON_MIGRANT = True

RISK_GROUPS = ["low", "high"]
SAMPLE_TYPES = ["all", "rural", "urban"]
T_LIST_DEFAULT = [2, 5, 10, 20, 50, 100]

DEPVAR = "edu_years"
CONTROL_FML = "C(M34) + C(M37) + C(M15) + C(M16)"

EARTH_RADIUS_KM = 6371.0088

# =========================================================
# 1. HELPERS
# =========================================================

def scen_tag(rp: int, depth_thr: float) -> str:
    return f"rp{rp}_d{int(round(depth_thr * 100)):03d}"

def ensure_numeric(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def normalize_county_code(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").astype("Int64")

def detect_T_list(df):
    ts = set()
    for c in df.columns:
        if c.startswith("share_flood_ge_T"):
            try:
                ts.add(float(c.replace("share_flood_ge_T", "")))
            except Exception:
                pass
    return sorted(ts) if ts else T_LIST_DEFAULT

def get_nobs(fit, fallback_df):
    for attr in ["nobs", "_N", "N"]:
        if hasattr(fit, attr):
            try:
                v = getattr(fit, attr)
                if isinstance(v, (int, float)):
                    return int(v)
            except Exception:
                pass
    return int(len(fallback_df))

def normalize_tidy(res):
    res = res.reset_index()
    if res.columns[0] != "Term":
        res = res.rename(columns={res.columns[0]: "Term"})

    rename_map = {}
    for c in res.columns:
        lc = c.lower().replace(" ", "").replace(".", "")
        if lc in ["estimate", "coef", "coefficient"]:
            rename_map[c] = "Estimate"
        elif lc in ["stderr", "stderror", "std_error", "std"]:
            rename_map[c] = "StdError"
        elif lc in ["pvalue", "p>|t|", "pr(>|t|)", "p"]:
            rename_map[c] = "PValue"
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

def build_is_urban_is_migrant(df):
    if "is_urban" not in df.columns and "M2" in df.columns:
        suffix = pd.to_numeric(df["M2"], errors="coerce") % 100
        df["is_urban"] = np.where((suffix >= 1) & (suffix <= 20), 1, 0)
        df.loc[pd.isna(df["M2"]), "is_urban"] = np.nan

    if "is_migrant" not in df.columns and "M38" in df.columns:
        M38 = pd.to_numeric(df["M38"], errors="coerce")
        df["is_migrant"] = np.where(M38 == 1, 0, 1)
        df.loc[pd.isna(M38), "is_migrant"] = np.nan
    return df

# =========================================================
# 2. COUNTY RISK
# =========================================================

def load_raster_geotiff(fp: Path):
    with rasterio.open(fp) as src:
        arr = src.read(1).astype("float32")
        transform = src.transform
        crs = src.crs
        nodata = src.nodata
        if nodata is not None:
            arr = np.where(arr == nodata, np.nan, arr)
    return arr, transform, crs

def pixel_area_km2_by_row(transform: Affine, nrows: int, crs):
    if not crs.is_geographic:
        raise ValueError("当前脚本按经纬度网格计算面积，请保证输入为地理坐标系。")

    dlon_deg = abs(transform.a)
    dlon_rad = np.deg2rad(dlon_deg)

    row_index = np.arange(nrows)
    lat_top = transform.f + row_index * transform.e
    lat_bottom = transform.f + (row_index + 1) * transform.e

    lat_top_rad = np.deg2rad(lat_top)
    lat_bottom_rad = np.deg2rad(lat_bottom)

    area_row = (
        (EARTH_RADIUS_KM ** 2)
        * dlon_rad
        * np.abs(np.sin(lat_top_rad) - np.sin(lat_bottom_rad))
    )
    return area_row.reshape(-1, 1).astype("float64")

def load_counties(target_crs):
    gdf = gpd.read_file(COUNTY_SHP)
    if gdf.crs is None:
        raise ValueError("COUNTY_SHP 缺少 CRS。")

    need = [COUNTY_CODE_FIELD, COUNTY_NAME_FIELD, "geometry"]
    miss = [c for c in need if c not in gdf.columns]
    if miss:
        raise KeyError(f"county.shp 缺少字段: {miss}")

    gdf = gdf.to_crs(target_crs).copy()
    gdf["county_code"] = normalize_county_code(gdf[COUNTY_CODE_FIELD])
    gdf["county_name"] = gdf[COUNTY_NAME_FIELD].astype(str).str.strip()

    gdf = gdf.dropna(subset=["county_code", "geometry"]).copy()
    gdf = gdf.reset_index(drop=True)
    gdf["raster_id"] = np.arange(1, len(gdf) + 1, dtype=np.int32)

    return gdf[["county_code", "county_name", "raster_id", "geometry"]]

def rasterize_counties(gdf_county, out_shape, transform):
    shapes = [(geom, rid) for geom, rid in zip(gdf_county.geometry, gdf_county["raster_id"])]
    rid_grid = rasterize(
        shapes=shapes,
        out_shape=out_shape,
        transform=transform,
        fill=0,
        dtype="int32",
        all_touched=False
    )
    return rid_grid

def assign_terciles_ranked(df, value_col):
    """Archived notebook note for 04_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    out = df.copy()
    valid = out[value_col].notna()

    sub = out.loc[valid].sort_values([value_col, "county_code"]).reset_index(drop=True)
    n = len(sub)
    if n < 3:
        raise ValueError("有效县数量少于 3，无法构造 tercile 分组。")

    pos = np.arange(n)
    tercile = np.floor(3 * pos / n).astype(int) + 1

    sub["risk_tercile"] = tercile
    sub["risk_group"] = sub["risk_tercile"].map({
        1: "low",
        2: "middle",
        3: "high",
    })

    out = out.merge(
        sub[["county_code", "risk_tercile", "risk_group"]],
        on="county_code",
        how="left",
        validate="1:1"
    )
    out["top_bottom_sample"] = out["risk_group"].isin(["low", "high"]).astype(int)
    return out

def build_county_risk_table(rp: int, depth_thr: float) -> pd.DataFrame:
    tag = scen_tag(rp, depth_thr)
    out_parquet = COUNTY_RISK_DIR / f"county_risk_{tag}.parquet"
    out_csv = COUNTY_RISK_DIR / f"county_risk_{tag}.csv"

    if out_parquet.exists():
        return pd.read_parquet(out_parquet)

    tif = RP_TIF_MAP[rp]
    if not tif.exists():
        raise FileNotFoundError(f"找不到栅格: {tif}")

    depth, transform, crs = load_raster_geotiff(tif)
    nrows, ncols = depth.shape

    gdf_county = load_counties(crs)
    rid_grid = rasterize_counties(gdf_county, depth.shape, transform)

    area_row = pixel_area_km2_by_row(transform, nrows, crs)
    area_grid = np.broadcast_to(area_row, depth.shape)

    rid_flat = rid_grid.ravel()
    area_flat = area_grid.ravel()
    depth_flat = depth.ravel()

    in_county = rid_flat > 0

    total_area = np.bincount(
        rid_flat[in_county],
        weights=area_flat[in_county],
        minlength=len(gdf_county) + 1
    )

    inund_mask = in_county & np.isfinite(depth_flat) & (depth_flat > depth_thr)
    inund_area = np.bincount(
        rid_flat[inund_mask],
        weights=area_flat[inund_mask],
        minlength=len(gdf_county) + 1
    )

    df = gdf_county[["county_code", "county_name", "raster_id"]].copy()
    df["rp"] = rp
    df["depth_threshold_m"] = depth_thr
    df["county_total_area_km2_raster"] = df["raster_id"].map(lambda x: float(total_area[x]))
    df["inund_area_km2"] = df["raster_id"].map(lambda x: float(inund_area[x]))
    df["risk_area_share"] = np.where(
        df["county_total_area_km2_raster"] > 0,
        df["inund_area_km2"] / df["county_total_area_km2_raster"],
        np.nan
    )
    df = df.drop(columns=["raster_id"])

    df = assign_terciles_ranked(df, "risk_area_share")

    df.to_parquet(out_parquet, index=False)
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")
    return df

# =========================================================
# 3. EDUCATION REGRESSION
# =========================================================

def load_edu_base():
    df = pd.read_parquet(EDU_PARQUET)

    num_cols = [
        "M2", "M38", "birth_year", "age_2015",
        "M34", "M37", "M15", "M16", DEPVAR
    ]
    df = ensure_numeric(df, num_cols)
    df = build_is_urban_is_migrant(df)

    if "county_code" in df.columns:
        df["county_code"] = normalize_county_code(df["county_code"])
    else:
        df["county_code"] = normalize_county_code(df["M2"])

    df["M2"] = pd.to_numeric(df["M2"], errors="coerce")
    df["birth_year"] = pd.to_numeric(df["birth_year"], errors="coerce")

    df = df.dropna(subset=["county_code", "M2", "birth_year"]).copy()
    df["M2"] = df["M2"].astype(np.int64)
    df["birth_year"] = df["birth_year"].astype(np.int64)

    df["prov_code"] = (df["M2"] // 10000).astype(np.int64)
    df["prov_birth_fe"] = df["prov_code"].astype(str) + "_" + df["birth_year"].astype(str)
    df["birth_year_c"] = df["birth_year"] - 1995

    return df.reset_index(drop=True)

def prepare_sample(df_all, main_share, main_years, risk_group, sample_type):
    df = df_all.copy()

    mask = pd.Series(True, index=df.index)
    mask &= (df["risk_group"] == risk_group)

    if ONLY_NON_MIGRANT:
        mask &= (df["is_migrant"] == 0)

    if sample_type == "rural":
        mask &= (df["is_urban"] == 0)
    elif sample_type == "urban":
        mask &= (df["is_urban"] == 1)
    elif sample_type == "all":
        pass
    else:
        raise ValueError(f"未知 sample_type: {sample_type}")

    if "age_2015" in df.columns:
        mask &= df["age_2015"].between(AGE_MIN, AGE_MAX)
    mask &= df["birth_year"].between(BIRTH_MIN, BIRTH_MAX)

    dfm = df.loc[mask].copy()

    need_cols = ["M2", "county_code", "birth_year", DEPVAR, main_share, main_years]
    dfm = dfm.dropna(subset=need_cols)

    for c in ["M34", "M37", "M15", "M16"]:
        dfm[c] = pd.to_numeric(dfm[c], errors="coerce")
        dfm = dfm.dropna(subset=[c])
        dfm[c] = dfm[c].astype(int).astype("category")
        dfm[c] = dfm[c].cat.remove_unused_categories()

    dfm[DEPVAR] = pd.to_numeric(dfm[DEPVAR], errors="coerce")
    dfm = dfm.dropna(subset=[DEPVAR])

    return dfm.reset_index(drop=True)

def run_linear(dfm, main_share):
    fml = (
        f"{DEPVAR} ~ {main_share} + {CONTROL_FML} + i(M2, birth_year_c) "
        f"| M2 + prov_birth_fe"
    )
    fit = feols(fml, data=dfm, vcov={"CRV1": "M2"})
    res = normalize_tidy(fit.tidy())

    key = res[res["Term"].astype(str).str.contains(main_share, na=False)].copy()
    if key.empty:
        return None

    row = key.iloc[0]
    est = float(row["Estimate"])
    se = float(row.get("StdError", np.nan))
    pv = float(row.get("PValue", np.nan))

    return {
        "Estimate": est,
        "StdError": se,
        "PValue": pv,
        "CI_low": est - 1.96 * se if np.isfinite(se) else np.nan,
        "CI_high": est + 1.96 * se if np.isfinite(se) else np.nan,
        "nobs": get_nobs(fit, dfm),
        "mean_depvar": float(dfm[DEPVAR].mean()),
    }

# =========================================================
# 4. MAIN
# =========================================================

def main():
    edu = load_edu_base()
    T_list = detect_T_list(edu)

    all_results = []
    summary_rows = []

    for rp in RP_LIST:
        for depth_thr in DEPTH_LIST:
            scen = scen_tag(rp, depth_thr)
            print("\n" + "=" * 80)
            print(f"[SCENARIO] {scen}")
            print("=" * 80)

            risk = build_county_risk_table(rp, depth_thr)

            df_all = edu.merge(
                risk[["county_code", "risk_area_share", "risk_tercile", "risk_group", "top_bottom_sample"]],
                on="county_code",
                how="left",
                validate="m:1"
            )

            summary_rows.append({
                "scenario": scen,
                "rp": rp,
                "depth_threshold_m": depth_thr,
                "n_county_total": int(risk["county_code"].nunique()),
                "n_county_low": int((risk["risk_group"] == "low").sum()),
                "n_county_middle": int((risk["risk_group"] == "middle").sum()),
                "n_county_high": int((risk["risk_group"] == "high").sum()),
                "n_micro_total": int(len(df_all)),
                "n_micro_top_bottom": int(df_all["risk_group"].isin(["low", "high"]).sum()),
            })

            for T in T_list:
                T_str = str(int(T)) if float(T).is_integer() else str(T)
                main_ret = f"flood_ge_T{T_str}"
                main_share = f"share_{main_ret}"
                main_years = f"years_{main_ret}"

                if main_share not in df_all.columns or main_years not in df_all.columns:
                    continue

                for sample_type in SAMPLE_TYPES:
                    for rg in RISK_GROUPS:
                        try:
                            dfm = prepare_sample(df_all, main_share, main_years, rg, sample_type)
                            print(
                                f"[RUN] {scen} | T={T_str:>3s} | sample={sample_type:>5s} | "
                                f"risk={rg:>4s} | N={len(dfm):,}"
                            )
                            if len(dfm) == 0:
                                continue

                            res = run_linear(dfm, main_share)
                            if res is None:
                                continue

                            all_results.append({
                                "scenario": scen,
                                "rp": rp,
                                "depth_threshold_m": depth_thr,
                                "sample_type": sample_type,
                                "risk_group": rg,
                                "T": float(T),
                                "T_str": T_str,
                                "depvar": DEPVAR,
                                "main_share": main_share,
                                "main_years": main_years,
                                "age_min": AGE_MIN,
                                "age_max": AGE_MAX,
                                "birth_min": BIRTH_MIN,
                                "birth_max": BIRTH_MAX,
                                "only_non_migrant": ONLY_NON_MIGRANT,
                                **res
                            })
                        except Exception as e:
                            print(f"[ERROR] {scen} | T={T_str} | sample={sample_type} | risk={rg} -> {e}")

            if all_results:
                pd.DataFrame(all_results).to_csv(OUT_MASTER_CSV, index=False, encoding="utf-8-sig")
                pd.DataFrame(all_results).to_parquet(OUT_MASTER_PARQUET, index=False)
            pd.DataFrame(summary_rows).to_csv(OUT_SUMMARY_CSV, index=False, encoding="utf-8-sig")

    out = pd.DataFrame(all_results)
    summ = pd.DataFrame(summary_rows)

    if not out.empty:
        out = out.sort_values(["scenario", "sample_type", "risk_group", "T"]).reset_index(drop=True)
        out.to_csv(OUT_MASTER_CSV, index=False, encoding="utf-8-sig")
        out.to_parquet(OUT_MASTER_PARQUET, index=False)
        print("[INFO] Notebook progress message.")
        print("[INFO] Notebook progress message.")

    if not summ.empty:
        summ = summ.sort_values(["rp", "depth_threshold_m"]).reset_index(drop=True)
        summ.to_csv(OUT_SUMMARY_CSV, index=False, encoding="utf-8-sig")
        print("[INFO] Notebook progress message.")

    print("\n[ALL DONE] Children education corrected robustness analysis finished.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 12
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
from math import erf, sqrt
import warnings

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.features import rasterize
from rasterio.transform import Affine
import statsmodels.api as sm

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)
warnings.simplefilter("ignore", RuntimeWarning)

# =========================================================
# 0. CONFIG
# =========================================================

FIXED_RP_DIR = Path("/home/ll/jupyter_notebook/result/fixed_rp_maps")
RP_TIF_MAP = {
    20: FIXED_RP_DIR / "rp20_inundation_depth_p50.tif",
    50: FIXED_RP_DIR / "rp50_inundation_depth_p50.tif",
    100: FIXED_RP_DIR / "rp100_inundation_depth_p50.tif",
}

COUNTY_SHP = Path("/home/ll/jupyter_notebook/gis_data/China/country/country.shp")
CITY_SHP = Path("/home/ll/jupyter_notebook/gis_data/China/city/city.shp")

COUNTY_CODE_FIELD = "县代码"
COUNTY_NAME_FIELD = "县"
CITY_CODE_IN_COUNTY_FIELD = "市代码"
CITY_NAME_IN_COUNTY_FIELD = "市"

CITY_CODE_FIELD = "市代码"
CITY_NAME_FIELD = "市"

PANEL_MERGED = Path(
    "/home/ll/jupyter_notebook/result/impact_assessment/older/flood_health_result/"
    "charls_health_panel_60plus_with_index_Tall_5_10_20_30y.parquet"
)

BASE_OUT = Path("/home/ll/jupyter_notebook/result/impact_assessment/风险分区_稳健性分析")
OUT_DIR = BASE_OUT / "older_health_corrected"
COUNTY_RISK_DIR = OUT_DIR / "county_risk_tables"
CITY_RISK_DIR = OUT_DIR / "city_risk_tables"
REG_DIR = OUT_DIR / "regression_results"

for p in [COUNTY_RISK_DIR, CITY_RISK_DIR, REG_DIR]:
    p.mkdir(parents=True, exist_ok=True)

OUT_FE_DETAIL_CSV = REG_DIR / "older_health_corrected_27scenarios_window_specific.csv"
OUT_FE_DETAIL_PARQUET = REG_DIR / "older_health_corrected_27scenarios_window_specific.parquet"

OUT_FE_AGG_CSV = REG_DIR / "older_health_corrected_27scenarios_window_aggregated.csv"
OUT_FE_AGG_PARQUET = REG_DIR / "older_health_corrected_27scenarios_window_aggregated.parquet"

OUT_SUMMARY_CSV = REG_DIR / "older_health_corrected_27scenarios_summary.csv"

RP_LIST = [20, 50, 100]
DEPTH_LIST = [0.1, 0.3, 0.5]
DOMINANCE_LIST = [0.5, 0.6, 0.7]

Y_VAR = "health_index_z"
ID_COL = "pid12"
CITY_COL = "city_code"
YEAR_COL = "year"
PROV_COL = "province"

RISK_GROUPS = ["low", "high"]
SAMPLE_SPECS = {
    "all": None,
    "urban": 1,
    "rural": 0,
}

T_LIST = [2, 5, 10, 20, 50, 100]
WINDOW_LIST = [5, 10, 20, 30]

MIN_NOBS = 100
MIN_NCITY = 10

EARTH_RADIUS_KM = 6371.0088

# =========================================================
# 1. HELPERS
# =========================================================

def county_tag(rp: int, depth_thr: float) -> str:
    return f"rp{rp}_d{int(round(depth_thr * 100)):03d}"

def city_tag(rp: int, depth_thr: float, dom: float) -> str:
    return f"rp{rp}_d{int(round(depth_thr * 100)):03d}_dom{int(round(dom * 100)):03d}"

def normalize_code_str(s: pd.Series) -> pd.Series:
    x = s.astype(str).str.strip()
    x = x.replace({"nan": pd.NA, "None": pd.NA, "": pd.NA})
    x = x.str.replace(r"\.0$", "", regex=True)
    return x

def normalize_county_code(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").astype("Int64")

def norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))

def assign_terciles_ranked(df, value_col):
    out = df.copy()
    valid = out[value_col].notna()

    sub = out.loc[valid].sort_values([value_col, "county_code"]).reset_index(drop=True)
    n = len(sub)
    if n < 3:
        raise ValueError("有效县数量少于 3，无法构造 tercile 分组。")

    pos = np.arange(n)
    tercile = np.floor(3 * pos / n).astype(int) + 1

    sub["risk_tercile"] = tercile
    sub["risk_group"] = sub["risk_tercile"].map({
        1: "low",
        2: "middle",
        3: "high",
    })

    out = out.merge(
        sub[["county_code", "risk_tercile", "risk_group"]],
        on="county_code",
        how="left",
        validate="1:1"
    )
    out["top_bottom_sample"] = out["risk_group"].isin(["low", "high"]).astype(int)
    return out

# =========================================================
# 2. COUNTY RISK
# =========================================================

def load_raster_geotiff(fp: Path):
    with rasterio.open(fp) as src:
        arr = src.read(1).astype("float32")
        transform = src.transform
        crs = src.crs
        nodata = src.nodata
        if nodata is not None:
            arr = np.where(arr == nodata, np.nan, arr)
    return arr, transform, crs

def pixel_area_km2_by_row(transform: Affine, nrows: int, crs):
    if not crs.is_geographic:
        raise ValueError("当前脚本按经纬度网格计算面积，请保证输入为地理坐标系。")

    dlon_deg = abs(transform.a)
    dlon_rad = np.deg2rad(dlon_deg)

    row_index = np.arange(nrows)
    lat_top = transform.f + row_index * transform.e
    lat_bottom = transform.f + (row_index + 1) * transform.e

    lat_top_rad = np.deg2rad(lat_top)
    lat_bottom_rad = np.deg2rad(lat_bottom)

    area_row = (
        (EARTH_RADIUS_KM ** 2)
        * dlon_rad
        * np.abs(np.sin(lat_top_rad) - np.sin(lat_bottom_rad))
    )
    return area_row.reshape(-1, 1).astype("float64")

def load_counties_for_raster(target_crs):
    gdf = gpd.read_file(COUNTY_SHP)
    if gdf.crs is None:
        raise ValueError("COUNTY_SHP 缺少 CRS。")

    need = [
        COUNTY_CODE_FIELD, COUNTY_NAME_FIELD,
        CITY_CODE_IN_COUNTY_FIELD, CITY_NAME_IN_COUNTY_FIELD,
        "geometry"
    ]
    miss = [c for c in need if c not in gdf.columns]
    if miss:
        raise KeyError(f"county.shp 缺少字段: {miss}")

    gdf = gdf.to_crs(target_crs).copy()
    gdf["county_code"] = normalize_county_code(gdf[COUNTY_CODE_FIELD])
    gdf["county_name"] = gdf[COUNTY_NAME_FIELD].astype(str).str.strip()
    gdf["city_code"] = normalize_code_str(gdf[CITY_CODE_IN_COUNTY_FIELD])
    gdf["city_name"] = gdf[CITY_NAME_IN_COUNTY_FIELD].astype(str).str.strip()

    gdf = gdf.dropna(subset=["county_code", "geometry"]).copy()
    gdf = gdf.reset_index(drop=True)
    gdf["raster_id"] = np.arange(1, len(gdf) + 1, dtype=np.int32)

    return gdf[["county_code", "county_name", "city_code", "city_name", "raster_id", "geometry"]]

def rasterize_counties(gdf_county, out_shape, transform):
    shapes = [(geom, rid) for geom, rid in zip(gdf_county.geometry, gdf_county["raster_id"])]
    rid_grid = rasterize(
        shapes=shapes,
        out_shape=out_shape,
        transform=transform,
        fill=0,
        dtype="int32",
        all_touched=False
    )
    return rid_grid

def build_county_risk_table(rp: int, depth_thr: float) -> pd.DataFrame:
    tag = county_tag(rp, depth_thr)
    out_parquet = COUNTY_RISK_DIR / f"county_risk_{tag}.parquet"
    out_csv = COUNTY_RISK_DIR / f"county_risk_{tag}.csv"

    if out_parquet.exists():
        return pd.read_parquet(out_parquet)

    tif = RP_TIF_MAP[rp]
    if not tif.exists():
        raise FileNotFoundError(f"找不到栅格: {tif}")

    depth, transform, crs = load_raster_geotiff(tif)
    nrows, ncols = depth.shape

    gdf_county = load_counties_for_raster(crs)
    rid_grid = rasterize_counties(gdf_county, depth.shape, transform)

    area_row = pixel_area_km2_by_row(transform, nrows, crs)
    area_grid = np.broadcast_to(area_row, depth.shape)

    rid_flat = rid_grid.ravel()
    area_flat = area_grid.ravel()
    depth_flat = depth.ravel()

    in_county = rid_flat > 0

    total_area = np.bincount(
        rid_flat[in_county],
        weights=area_flat[in_county],
        minlength=len(gdf_county) + 1
    )

    inund_mask = in_county & np.isfinite(depth_flat) & (depth_flat > depth_thr)
    inund_area = np.bincount(
        rid_flat[inund_mask],
        weights=area_flat[inund_mask],
        minlength=len(gdf_county) + 1
    )

    df = gdf_county[["county_code", "county_name", "city_code", "city_name", "raster_id"]].copy()
    df["rp"] = rp
    df["depth_threshold_m"] = depth_thr
    df["county_total_area_km2_raster"] = df["raster_id"].map(lambda x: float(total_area[x]))
    df["inund_area_km2"] = df["raster_id"].map(lambda x: float(inund_area[x]))
    df["risk_area_share"] = np.where(
        df["county_total_area_km2_raster"] > 0,
        df["inund_area_km2"] / df["county_total_area_km2_raster"],
        np.nan
    )
    df = df.drop(columns=["raster_id"])

    df = assign_terciles_ranked(df, "risk_area_share")

    df.to_parquet(out_parquet, index=False)
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")
    return df

# =========================================================
# 3. COUNTY -> CITY AGGREGATION
# =========================================================

def classify_city_risk(row, threshold=0.60):
    sh = row["share_high_area_in_city"]
    sl = row["share_low_area_in_city"]

    if pd.notna(sh) and sh >= threshold:
        return "high"
    if pd.notna(sl) and sl >= threshold:
        return "low"
    return "middle"

def build_city_risk_table(rp: int, depth_thr: float, dominance_threshold: float) -> pd.DataFrame:
    tag = city_tag(rp, depth_thr, dominance_threshold)
    out_parquet = CITY_RISK_DIR / f"city_risk_{tag}.parquet"
    out_csv = CITY_RISK_DIR / f"city_risk_{tag}.csv"

    if out_parquet.exists():
        return pd.read_parquet(out_parquet)

    df_county = build_county_risk_table(rp, depth_thr).copy()

    # Original notebook comment normalized for the public code archive.
    # City-level processing note.
    # City-level processing note.
    df_county["county_area_km2_weight"] = pd.to_numeric(
        df_county["county_total_area_km2_raster"], errors="coerce"
    )
    df_county["risk_area_share"] = pd.to_numeric(df_county["risk_area_share"], errors="coerce")

    df_county["area_high_km2"] = np.where(
        df_county["risk_group"] == "high",
        df_county["county_area_km2_weight"], 0.0
    )
    df_county["area_low_km2"] = np.where(
        df_county["risk_group"] == "low",
        df_county["county_area_km2_weight"], 0.0
    )
    df_county["area_middle_km2"] = np.where(
        df_county["risk_group"] == "middle",
        df_county["county_area_km2_weight"], 0.0
    )
    df_county["risk_x_area"] = df_county["risk_area_share"] * df_county["county_area_km2_weight"]

    rows = []
    for city_code, g in df_county.groupby("city_code", dropna=False):
        if pd.isna(city_code):
            continue

        total_area = g["county_area_km2_weight"].sum(min_count=1)
        high_area = g["area_high_km2"].sum(min_count=1)
        low_area = g["area_low_km2"].sum(min_count=1)
        middle_area = g["area_middle_km2"].sum(min_count=1)

        risk_num = g["risk_x_area"].sum(min_count=1)
        risk_den = g["county_area_km2_weight"].sum(min_count=1)
        risk_cont = risk_num / risk_den if pd.notna(risk_den) and risk_den > 0 else np.nan

        rows.append({
            "city_code": city_code,
            "city_name_from_county": g["city_name"].dropna().iloc[0] if g["city_name"].notna().any() else pd.NA,
            "n_counties_total": g["county_code"].nunique(),
            "n_counties_high": (g["risk_group"] == "high").sum(),
            "n_counties_middle": (g["risk_group"] == "middle").sum(),
            "n_counties_low": (g["risk_group"] == "low").sum(),
            "city_total_area_km2_raster": total_area,
            "city_high_county_area_km2": high_area,
            "city_middle_county_area_km2": middle_area,
            "city_low_county_area_km2": low_area,
            "share_high_area_in_city": high_area / total_area if pd.notna(total_area) and total_area > 0 else np.nan,
            "share_middle_area_in_city": middle_area / total_area if pd.notna(total_area) and total_area > 0 else np.nan,
            "share_low_area_in_city": low_area / total_area if pd.notna(total_area) and total_area > 0 else np.nan,
            "risk_area_share_city": risk_cont,
        })

    df_city = pd.DataFrame(rows)

    if df_city.empty:
        raise RuntimeError(f"{tag} 聚合后 df_city 为空。")

    df_city["risk_group"] = df_city.apply(
        classify_city_risk, axis=1, threshold=dominance_threshold
    )
    df_city["risk_tercile"] = df_city["risk_group"].map({
        "low": 1,
        "middle": 2,
        "high": 3,
    }).astype("Int64")
    df_city["top_bottom_sample"] = df_city["risk_group"].isin(["low", "high"]).astype(int)
    df_city["rp"] = rp
    df_city["depth_threshold_m"] = depth_thr
    df_city["dominance_threshold"] = dominance_threshold

    # City-level processing note.
    gdf_city = gpd.read_file(CITY_SHP)
    need = [CITY_CODE_FIELD, CITY_NAME_FIELD]
    miss = [c for c in need if c not in gdf_city.columns]
    if miss:
        raise KeyError(f"city.shp 缺少字段: {miss}")

    gdf_city["city_code"] = normalize_code_str(gdf_city[CITY_CODE_FIELD])
    gdf_city["city_name"] = gdf_city[CITY_NAME_FIELD].astype(str).str.strip()

    df_city_final = gdf_city[["city_code", "city_name"]].drop_duplicates("city_code").merge(
        df_city,
        on="city_code",
        how="left",
        validate="1:1"
    )

    # City-level processing note.
    miss_name = df_city_final["city_name"].isna() | (df_city_final["city_name"] == "")
    df_city_final.loc[miss_name, "city_name"] = df_city_final.loc[miss_name, "city_name_from_county"]

    df_city_final.to_parquet(out_parquet, index=False)
    df_city_final.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print("[INFO] Notebook progress message.")
    return df_city_final

# =========================================================
# 4. HEALTH FE
# =========================================================

def demean_two_fe(df, cols, fe1, fe2):
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
    cols_needed = [y_col] + x_cols + [fe1, fe2, cluster_col]
    df = df.dropna(subset=cols_needed).copy()

    df = df[df[cluster_col].notna()].copy()
    if df.empty:
        raise ValueError("cluster_col 全缺失，无法回归。")

    df = demean_two_fe(df, [y_col] + x_cols, fe1=fe1, fe2=fe2)

    y = df[f"{y_col}_dm"].to_numpy()
    X = df[[f"{c}_dm" for c in x_cols]].to_numpy()

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

def load_health_base():
    print(f"[READ] HEALTH PANEL: {PANEL_MERGED}")
    df = pd.read_parquet(PANEL_MERGED)

    df[CITY_COL] = normalize_code_str(df[CITY_COL])
    df[Y_VAR] = pd.to_numeric(df[Y_VAR], errors="coerce")
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df[YEAR_COL] = pd.to_numeric(df[YEAR_COL], errors="coerce")

    df = df.dropna(subset=[Y_VAR, "age", ID_COL, PROV_COL, CITY_COL, YEAR_COL]).copy()
    df["age2"] = df["age"] ** 2

    df["prov_str"] = df[PROV_COL].astype(str).str.strip()
    df["prov_year"] = df["prov_str"] + "_" + df[YEAR_COL].astype(int).astype(str)

    df["urban_nbs"] = pd.to_numeric(df["urban_nbs"], errors="coerce").fillna(0).astype(int)
    grp_urban = df.groupby(ID_COL)["urban_nbs"].mean()
    df = df.merge(
        (grp_urban > 0.5).astype(int).rename("urban_group"),
        on=ID_COL,
        how="left",
    )

    waves_per_id = df.groupby(ID_COL)[YEAR_COL].nunique()
    keep_ids = waves_per_id[waves_per_id >= 2].index
    df = df[df[ID_COL].isin(keep_ids)].copy()

    print(
        f"[INFO] base panel -> N={len(df):,}, "
        f"N_id={df[ID_COL].nunique():,}, "
        f"N_city={df[CITY_COL].nunique():,}, "
        f"N_year={df[YEAR_COL].nunique():,}"
    )
    return df.reset_index(drop=True)

def aggregate_across_window(detail_df: pd.DataFrame) -> pd.DataFrame:
    group_cols = [
        "scenario", "rp", "depth_threshold_m", "dominance_threshold",
        "sample", "risk_group", "T"
    ]
    rows = []

    for keys, g in detail_df.groupby(group_cols, dropna=False):
        est = g["Estimate"].to_numpy(float)
        se = g["Std. Error"].to_numpy(float)

        var = se ** 2
        var[var <= 0] = 1e-12
        w = 1.0 / var

        beta_w = float(np.sum(w * est) / np.sum(w))
        var_w = float(1.0 / np.sum(w))
        se_w = float(np.sqrt(var_w))

        if se_w > 0:
            t_val = beta_w / se_w
            p_val = 2.0 * (1.0 - norm_cdf(abs(t_val)))
        else:
            t_val = np.nan
            p_val = np.nan

        ci_low = beta_w - 1.96 * se_w
        ci_high = beta_w + 1.96 * se_w

        scenario, rp, depth_thr, dom, sample, risk_group, T = keys

        rows.append({
            "scenario": scenario,
            "rp": rp,
            "depth_threshold_m": depth_thr,
            "dominance_threshold": dom,
            "sample": sample,
            "risk_group": risk_group,
            "T": T,
            "Estimate": beta_w,
            "Std. Error": se_w,
            "t value": t_val,
            "Pr(>|t|)": p_val,
            "2.5%": ci_low,
            "97.5%": ci_high,
            "n_window": int(g["window"].nunique()),
            "window_list": ",".join(str(int(x)) for x in sorted(g["window"].unique())),
            "N_min": int(g["N"].min()),
            "N_max": int(g["N"].max()),
            "N_id_min": int(g["N_id"].min()),
            "N_id_max": int(g["N_id"].max()),
            "N_city_min": int(g["N_city"].min()),
            "N_city_max": int(g["N_city"].max()),
        })

    out = pd.DataFrame(rows)
    return out.sort_values(["scenario", "sample", "risk_group", "T"]).reset_index(drop=True)

# =========================================================
# 5. MAIN
# =========================================================

def main():
    health_base = load_health_base()

    detail_rows = []
    summary_rows = []

    for rp in RP_LIST:
        for depth_thr in DEPTH_LIST:
            # Original notebook comment normalized for the public code archive.
            _ = build_county_risk_table(rp, depth_thr)

            for dom in DOMINANCE_LIST:
                scen = city_tag(rp, depth_thr, dom)
                print("\n" + "=" * 90)
                print(f"[SCENARIO] {scen}")
                print("=" * 90)

                city_risk = build_city_risk_table(rp, depth_thr, dom)

                # Original notebook comment normalized for the public code archive.
                match_rate = health_base[CITY_COL].isin(set(city_risk["city_code"].dropna())).mean()
                print("[INFO] Notebook progress message.")

                df = health_base.merge(
                    city_risk[["city_code", "risk_group", "risk_area_share_city", "top_bottom_sample"]],
                    how="left",
                    left_on=CITY_COL,
                    right_on="city_code",
                    validate="m:1"
                )

                df = df[df["risk_group"].isin(RISK_GROUPS)].copy()

                print("[INFO] Notebook progress message.")
                print(df["risk_group"].value_counts(dropna=False))

                summary_rows.append({
                    "scenario": scen,
                    "rp": rp,
                    "depth_threshold_m": depth_thr,
                    "dominance_threshold": dom,
                    "n_city_total": int(city_risk["city_code"].nunique()),
                    "n_city_low": int((city_risk["risk_group"] == "low").sum()),
                    "n_city_middle": int((city_risk["risk_group"] == "middle").sum()),
                    "n_city_high": int((city_risk["risk_group"] == "high").sum()),
                    "panel_city_match_rate": float(match_rate),
                    "n_panel_after_merge": int(len(df)),
                })

                for sample_name, group_val in SAMPLE_SPECS.items():
                    for risk_group in RISK_GROUPS:
                        sub_base = df.copy()

                        if group_val is not None:
                            sub_base = sub_base[sub_base["urban_group"] == group_val].copy()

                        sub_base = sub_base[sub_base["risk_group"] == risk_group].copy()

                        waves_sub = sub_base.groupby(ID_COL)[YEAR_COL].nunique()
                        keep_ids_sub = waves_sub[waves_sub >= 2].index
                        sub_base = sub_base[sub_base[ID_COL].isin(keep_ids_sub)].copy()

                        print(
                            f"[BASE] {scen} | sample={sample_name:>5s} | risk={risk_group:>4s} | "
                            f"N={len(sub_base):,} | N_id={sub_base[ID_COL].nunique():,} | "
                            f"N_city={sub_base[CITY_COL].nunique():,}"
                        )

                        if len(sub_base) < MIN_NOBS or sub_base[CITY_COL].nunique() < MIN_NCITY:
                            continue

                        for window in WINDOW_LIST:
                            for T in T_LIST:
                                exp_col = f"share_flood_T{T}_{window}y"
                                if exp_col not in sub_base.columns:
                                    continue

                                sub = sub_base.dropna(subset=[exp_col]).copy()
                                if len(sub) < MIN_NOBS or sub[CITY_COL].nunique() < MIN_NCITY:
                                    continue

                                try:
                                    res = fe_reg_twoFE_city_cluster(
                                        sub,
                                        y_col=Y_VAR,
                                        x_cols=[exp_col, "age", "age2"],
                                        fe1=ID_COL,
                                        fe2="prov_year",
                                        cluster_col=CITY_COL,
                                    )

                                    row = res.loc[exp_col].copy()
                                    detail_rows.append({
                                        "scenario": scen,
                                        "rp": rp,
                                        "depth_threshold_m": depth_thr,
                                        "dominance_threshold": dom,
                                        "Y_var": Y_VAR,
                                        "window": window,
                                        "T": T,
                                        "exposure": exp_col,
                                        "sample": sample_name,
                                        "risk_group": risk_group,
                                        "Estimate": float(row["Estimate"]),
                                        "Std. Error": float(row["Std. Error"]),
                                        "t value": float(row["t value"]),
                                        "Pr(>|t|)": float(row["Pr(>|t|)"]),
                                        "2.5%": float(row["2.5%"]),
                                        "97.5%": float(row["97.5%"]),
                                        "N": int(len(sub)),
                                        "N_id": int(sub[ID_COL].nunique()),
                                        "N_year": int(sub[YEAR_COL].nunique()),
                                        "N_city": int(sub[CITY_COL].nunique()),
                                        "mean_depvar": float(sub[Y_VAR].mean()),
                                    })

                                    print(
                                        f"[RUN] {scen} | sample={sample_name:>5s} | risk={risk_group:>4s} | "
                                        f"window={window:>2d} | T={T:>3d} | "
                                        f"beta={float(row['Estimate']): .6f} | p={float(row['Pr(>|t|)']):.4f}"
                                    )
                                except Exception as e:
                                    print(
                                        f"[ERROR] {scen} | sample={sample_name} | risk={risk_group} | "
                                        f"window={window} | T={T} -> {e}"
                                    )

                if detail_rows:
                    pd.DataFrame(detail_rows).to_csv(OUT_FE_DETAIL_CSV, index=False, encoding="utf-8-sig")
                    pd.DataFrame(detail_rows).to_parquet(OUT_FE_DETAIL_PARQUET, index=False)
                pd.DataFrame(summary_rows).to_csv(OUT_SUMMARY_CSV, index=False, encoding="utf-8-sig")

    detail_df = pd.DataFrame(detail_rows)
    summary_df = pd.DataFrame(summary_rows)

    if detail_df.empty:
        print("[INFO] Notebook progress message.")
        return

    detail_df = detail_df.sort_values(
        ["scenario", "sample", "risk_group", "window", "T"]
    ).reset_index(drop=True)
    detail_df.to_csv(OUT_FE_DETAIL_CSV, index=False, encoding="utf-8-sig")
    detail_df.to_parquet(OUT_FE_DETAIL_PARQUET, index=False)
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")

    agg_df = aggregate_across_window(detail_df)
    agg_df.to_csv(OUT_FE_AGG_CSV, index=False, encoding="utf-8-sig")
    agg_df.to_parquet(OUT_FE_AGG_PARQUET, index=False)
    print("[INFO] Notebook progress message.")
    print("[INFO] Notebook progress message.")

    if not summary_df.empty:
        summary_df = summary_df.sort_values(
            ["rp", "depth_threshold_m", "dominance_threshold"]
        ).reset_index(drop=True)
        summary_df.to_csv(OUT_SUMMARY_CSV, index=False, encoding="utf-8-sig")
        print("[INFO] Notebook progress message.")

    print("\n[ALL DONE] Older health corrected robustness analysis finished.")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------------------
# Notebook cell 15
# ------------------------------------------------------------------------------
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Archived notebook note for 04_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from pathlib import Path
import warnings

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter, NullFormatter

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)
warnings.simplefilter("ignore", RuntimeWarning)

# =========================================================
# 0. PATHS
# =========================================================

BASE_DIR = Path("/home/ll/jupyter_notebook/result/impact_assessment/风险分区_稳健性分析")

# =============================================================================
EDU_RES_CSV = (
    BASE_DIR
    / "children_education_corrected"
    / "regression_results"
    / "edu_robustness_corrected_9scenarios_all_results.csv"
)

EDU_OUT_DIR = (
    BASE_DIR
    / "children_education_corrected"
    / "visualization"
)
EDU_OUT_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
OLDER_RES_CSV = (
    BASE_DIR
    / "older_health_corrected"
    / "regression_results"
    / "older_health_corrected_27scenarios_window_aggregated.csv"
)

OLDER_OUT_DIR = (
    BASE_DIR
    / "older_health_corrected"
    / "visualization"
)
OLDER_OUT_DIR.mkdir(parents=True, exist_ok=True)

# =========================================================
# 1. GLOBAL CONFIG
# =========================================================

RP_ORDER = [20, 50, 100]
DEPTH_ORDER = [0.1, 0.3, 0.5]
T_ORDER = [2, 5, 10, 20, 50, 100]
SAMPLE_ORDER = ["all", "rural", "urban"]
DOM_ORDER = [0.5, 0.6, 0.7]
RISK_ORDER = ["low", "high"]

STYLE_MAP = {
    "low": {
        "color": "#1f77b4",
        "label": "Low-risk",
        "xmult": 0.96,
    },
    "high": {
        "color": "#d62728",
        "label": "High-risk",
        "xmult": 1.04,
    },
}

# =========================================================
# 2. SMALL TOOLS
# =========================================================

def stars_for_p(p):
    try:
        p = float(p)
    except Exception:
        return ""
    if np.isnan(p):
        return ""
    if p < 0.01:
        return "***"
    elif p < 0.05:
        return "**"
    elif p < 0.10:
        return "*"
    return ""


def safe_numeric(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def compute_ylims(df, low_col="CI_low", high_col="CI_high"):
    vals = pd.concat(
        [
            df[low_col].replace([np.inf, -np.inf], np.nan),
            df[high_col].replace([np.inf, -np.inf], np.nan),
        ],
        axis=0,
    ).dropna()

    if vals.empty:
        return (-1.0, 1.0)

    ymin = float(vals.min())
    ymax = float(vals.max())
    yr = ymax - ymin
    pad = 0.10 * yr if yr > 0 else 0.15
    return (ymin - pad, ymax + pad)


def format_panel_title(rp, depth_thr):
    return f"RP{int(rp)} | depth > {depth_thr:.1f} m"


def plot_one_panel(ax, sub_df, ylims=None, ylabel=None):
    """Archived notebook note for 04_risk_zone_heterogeneity.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""
    if sub_df.empty:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes, fontsize=11)
        ax.set_axis_off()
        return

    # Original notebook comment normalized for the public code archive.
    vals = pd.concat(
        [
            sub_df["CI_low"].replace([np.inf, -np.inf], np.nan),
            sub_df["CI_high"].replace([np.inf, -np.inf], np.nan),
        ],
        axis=0,
    ).dropna()

    if vals.empty:
        y_offset = 0.05
    else:
        y_range = float(vals.max() - vals.min())
        y_offset = 0.04 * y_range if y_range > 0 else 0.05

    for rg in RISK_ORDER:
        sub = sub_df[sub_df["risk_group"] == rg].copy()
        if sub.empty:
            continue

        sub["T"] = pd.to_numeric(sub["T"], errors="coerce")
        sub = sub.dropna(subset=["T"]).sort_values("T")

        xs_base = sub["T"].to_numpy(float)
        xs = xs_base * STYLE_MAP[rg]["xmult"]

        ys = sub["Estimate"].to_numpy(float)
        lo = sub["CI_low"].to_numpy(float)
        hi = sub["CI_high"].to_numpy(float)
        pv = sub["PValue"].to_numpy(float)

        yerr = np.vstack([ys - lo, hi - ys])

        ax.errorbar(
            xs,
            ys,
            yerr=yerr,
            fmt="o-",
            capsize=4,
            lw=1.8,
            ms=6.5,
            color=STYLE_MAP[rg]["color"],
            label=STYLE_MAP[rg]["label"],
        )

        for x, y, p in zip(xs, ys, pv):
            s = stars_for_p(p)
            if s:
                ax.text(
                    x,
                    y + y_offset,
                    s,
                    ha="center",
                    va="bottom",
                    fontsize=11,
                    color=STYLE_MAP[rg]["color"],
                )

    ax.axhline(0, color="gray", linestyle="--", linewidth=1)

    ax.set_xscale("log")
    ax.set_xticks(T_ORDER)
    ax.get_xaxis().set_major_formatter(ScalarFormatter())
    ax.get_xaxis().set_minor_formatter(NullFormatter())

    if ylims is not None:
        ax.set_ylim(*ylims)

    if ylabel is not None:
        ax.set_ylabel(ylabel, fontsize=12)

    ax.tick_params(axis="both", labelsize=10)


def save_figure(fig, png_path: Path, pdf_path: Path):
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(pdf_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[SAVED] {png_path}")
    print(f"[SAVED] {pdf_path}")


# =========================================================
# 3. EDUCATION
# =========================================================

def read_edu_result() -> pd.DataFrame:
    print(f"[READ] Education results: {EDU_RES_CSV}")
    df = pd.read_csv(EDU_RES_CSV)

    need = [
        "scenario", "rp", "depth_threshold_m", "sample_type", "risk_group",
        "T", "Estimate", "StdError", "PValue", "CI_low", "CI_high"
    ]
    miss = [c for c in need if c not in df.columns]
    if miss:
        raise KeyError(f"教育结果文件缺少必要列: {miss}")

    df = safe_numeric(
        df,
        ["rp", "depth_threshold_m", "T", "Estimate", "StdError", "PValue", "CI_low", "CI_high"]
    )

    df["sample_type"] = df["sample_type"].astype(str)
    df["risk_group"] = df["risk_group"].astype(str)
    df = df.dropna(subset=["rp", "depth_threshold_m", "T", "Estimate", "CI_low", "CI_high"])

    print("[INFO] Education result head:")
    print(df.head())
    return df


def plot_edu_sample(df: pd.DataFrame, sample_type: str):
    sub_all = df[df["sample_type"] == sample_type].copy()
    if sub_all.empty:
        print("[INFO] Notebook progress message.")
        return

    ylims = compute_ylims(sub_all, "CI_low", "CI_high")

    fig, axes = plt.subplots(
        3, 3,
        figsize=(15.5, 12.0),
        sharex=True,
        sharey=True
    )

    for i, depth_thr in enumerate(DEPTH_ORDER):
        for j, rp in enumerate(RP_ORDER):
            ax = axes[i, j]
            sub = sub_all[
                np.isclose(sub_all["depth_threshold_m"], depth_thr) &
                np.isclose(sub_all["rp"], rp)
            ].copy()

            plot_one_panel(
                ax,
                sub_df=sub,
                ylims=ylims,
                ylabel="Effect on years of schooling" if j == 0 else None,
            )

            ax.set_title(format_panel_title(rp, depth_thr), fontsize=12)

            if i == 2:
                ax.set_xlabel("Flood return period T (years, log scale)", fontsize=11)

    handles, labels = axes[0, 0].get_legend_handles_labels()
    if handles:
        fig.legend(
            handles, labels,
            loc="upper center",
            ncol=2,
            frameon=False,
            fontsize=12,
            bbox_to_anchor=(0.5, 0.98)
        )

    sample_title_map = {
        "all": "All sample",
        "rural": "Rural sample",
        "urban": "Urban sample",
    }

    fig.suptitle(
        "Children's education: robustness across RP and depth thresholds\n"
        f"{sample_title_map.get(sample_type, sample_type)}",
        fontsize=17,
        y=1.02
    )

    fig.text(
        0.5,
        0.01,
        "Notes: rows = depth thresholds; columns = RP maps; "
        "error bars = 95% CI; *** p<0.01, ** p<0.05, * p<0.10.",
        ha="center",
        fontsize=10.5
    )

    plt.tight_layout(rect=[0.02, 0.04, 0.98, 0.95])

    out_png = EDU_OUT_DIR / f"edu_robustness_{sample_type}_3x3.png"
    out_pdf = EDU_OUT_DIR / f"edu_robustness_{sample_type}_3x3.pdf"
    save_figure(fig, out_png, out_pdf)


def run_education_visualization():
    df = read_edu_result()
    for sample_type in SAMPLE_ORDER:
        plot_edu_sample(df, sample_type)


# =========================================================
# 4. OLDER HEALTH
# =========================================================

def read_older_result() -> pd.DataFrame:
    print(f"[READ] Older-health aggregated results: {OLDER_RES_CSV}")
    df = pd.read_csv(OLDER_RES_CSV)

    need = [
        "scenario", "rp", "depth_threshold_m", "dominance_threshold",
        "sample", "risk_group", "T",
        "Estimate", "Std. Error", "Pr(>|t|)", "2.5%", "97.5%"
    ]
    miss = [c for c in need if c not in df.columns]
    if miss:
        raise KeyError(f"老年健康聚合结果缺少必要列: {miss}")

    df = df.rename(
        columns={
            "sample": "sample_type",
            "Std. Error": "StdError",
            "Pr(>|t|)": "PValue",
            "2.5%": "CI_low",
            "97.5%": "CI_high",
        }
    )

    df = safe_numeric(
        df,
        [
            "rp", "depth_threshold_m", "dominance_threshold", "T",
            "Estimate", "StdError", "PValue", "CI_low", "CI_high"
        ]
    )

    df["sample_type"] = df["sample_type"].astype(str)
    df["risk_group"] = df["risk_group"].astype(str)
    df = df.dropna(
        subset=["rp", "depth_threshold_m", "dominance_threshold", "T", "Estimate", "CI_low", "CI_high"]
    )

    print("[INFO] Older-health aggregated result head:")
    print(df.head())
    return df


def plot_older_sample_dom(df: pd.DataFrame, sample_type: str, dom: float):
    sub_all = df[
        (df["sample_type"] == sample_type) &
        (np.isclose(df["dominance_threshold"], dom))
    ].copy()

    if sub_all.empty:
        print("[INFO] Notebook progress message.")
        return

    ylims = compute_ylims(sub_all, "CI_low", "CI_high")

    fig, axes = plt.subplots(
        3, 3,
        figsize=(15.5, 12.0),
        sharex=True,
        sharey=True
    )

    for i, depth_thr in enumerate(DEPTH_ORDER):
        for j, rp in enumerate(RP_ORDER):
            ax = axes[i, j]
            sub = sub_all[
                np.isclose(sub_all["depth_threshold_m"], depth_thr) &
                np.isclose(sub_all["rp"], rp)
            ].copy()

            plot_one_panel(
                ax,
                sub_df=sub,
                ylims=ylims,
                ylabel="Effect on health_index_z" if j == 0 else None,
            )

            ax.set_title(format_panel_title(rp, depth_thr), fontsize=12)

            if i == 2:
                ax.set_xlabel("Flood return period T (years, log scale)", fontsize=11)

    handles, labels = axes[0, 0].get_legend_handles_labels()
    if handles:
        fig.legend(
            handles, labels,
            loc="upper center",
            ncol=2,
            frameon=False,
            fontsize=12,
            bbox_to_anchor=(0.5, 0.98)
        )

    sample_title_map = {
        "all": "All sample",
        "rural": "Rural sample",
        "urban": "Urban sample",
    }

    fig.suptitle(
        "Older adults' health: robustness across RP, depth, and city dominance threshold\n"
        f"{sample_title_map.get(sample_type, sample_type)} | dominance threshold = {dom:.1f}",
        fontsize=17,
        y=1.02
    )

    fig.text(
        0.5,
        0.01,
        "Notes: rows = depth thresholds; columns = RP maps; "
        "error bars = 95% CI from across-window aggregated estimates; "
        "*** p<0.01, ** p<0.05, * p<0.10.",
        ha="center",
        fontsize=10.2
    )

    plt.tight_layout(rect=[0.02, 0.04, 0.98, 0.95])

    dom_tag = f"dom{int(round(dom * 100)):03d}"
    out_png = OLDER_OUT_DIR / f"older_health_robustness_{sample_type}_{dom_tag}_3x3.png"
    out_pdf = OLDER_OUT_DIR / f"older_health_robustness_{sample_type}_{dom_tag}_3x3.pdf"
    save_figure(fig, out_png, out_pdf)


def run_older_visualization():
    df = read_older_result()
    for sample_type in SAMPLE_ORDER:
        for dom in DOM_ORDER:
            plot_older_sample_dom(df, sample_type, dom)


# =========================================================
# 5. MAIN
# =========================================================

def main():
    print("\n" + "=" * 90)
    print("[STEP] Education visualization")
    print("=" * 90)
    run_education_visualization()

    print("\n" + "=" * 90)
    print("[STEP] Older-health visualization")
    print("=" * 90)
    run_older_visualization()

    print("[INFO] Notebook progress message.")
    print(f"[OUT] Education figs -> {EDU_OUT_DIR}")
    print(f"[OUT] Older-health figs -> {OLDER_OUT_DIR}")


if __name__ == "__main__":
    main()
