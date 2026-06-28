# School POI workflow run order

This folder archives the existing Jupyter workflow used to construct
school POI / education-facility data and related auxiliary spatial attributes.

The scripts preserve notebook code cells. They are organized according to
the original workflow rather than refactored into a new production pipeline.

## Main workflow

1. `01_province_level_school_poi_cleaning_template.py`
   - Purpose: Province-level school POI cleaning template
   - Source notebooks: representative province notebooks

2. `02_remove_universities_and_filter_school_types.py`
   - Purpose: Remove universities and filter school types by province
   - Source notebook: internal original notebook (non-public source filename omitted).

3. `03_merge_national_school_poi.py`
   - Purpose: Merge province-level school POI outputs into a national table
   - Source notebook: internal original notebook (non-public source filename omitted).

4. `04_school_poi_exploratory_analysis.py`
   - Purpose: Exploratory analysis for school POI data
   - Source notebook: internal original notebook (non-public source filename omitted).

5. `05_generate_school_poi_by_province_optimized.py`
   - Purpose: Generate school POI data by province using optimized batch workflow
   - Source notebook: internal original notebook (non-public source filename omitted).

6. `06_extract_euluc_clcd_for_school_points.py`
   - Purpose: Extract EULUC and CLCD attributes for school points
   - Source notebook: internal original notebook (non-public source filename omitted).

7. `07_generate_annual_urban_landuse_layers.py`
   - Purpose: Generate annual urban land-use layers
   - Source notebook: internal original notebook (non-public source filename omitted).

8. `08_generate_annual_nighttime_light_layers.py`
   - Purpose: Generate annual nighttime-light layers
   - Source notebook: internal original notebook (non-public source filename omitted).

9. `09_read_nighttime_light_and_population_density.py`
   - Purpose: Read nighttime-light and population-density data
   - Source notebook: internal original notebook (non-public source filename omitted).

10. `10_infer_school_establishment_year_multisource.py`
   - Purpose: Infer school establishment year using multisource evidence
   - Source notebook: internal original notebook (non-public source filename omitted).

11. `11_manual_corrections.py`
   - Purpose: Manual correction notebooks
   - Source notebook: internal original notebook (non-public source filename omitted).

## Province notebooks

Province-specific notebooks in the local province-notebook folder are treated as repeated local
implementations of the same province-level cleaning logic.

Only representative province notebooks are exported as the main template by
default. Set `EXPORT_ALL_PROVINCE_LEGACY=1` before running the organizer if
all province notebooks should also be exported under `legacy_notebook_exports/`.

## Notes

- Raw POI data, geospatial rasters, and school-level processed outputs are not included.
- Before public release, local absolute paths inside exported notebook code can be
  replaced by `config.yaml` or command-line arguments if a reusable pipeline is needed.
