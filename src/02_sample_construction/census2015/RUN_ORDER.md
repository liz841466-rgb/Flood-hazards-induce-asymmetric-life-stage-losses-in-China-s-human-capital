# Run order for the 2015 Census workflow

This file documents the intended order of the archived notebook workflow.
The scripts preserve the original notebook code cells and may require local
path edits or `config.yaml` before execution.

## 00. Raw data inspection and file-structure diagnostics

Source notebook: internal original notebook (non-public source filename omitted).

GitHub script: `00_raw_data_inspection.py`

Inspect raw 2015 census files, file encodings, metadata, column structure, and
the feasibility of chunked or Stata-based reading.

## 01. Region-code and educational-attainment variable extraction

Source notebook: internal original notebook (non-public source filename omitted).

GitHub script: `01_extract_region_education_variables.py`

Extract and inspect geographic codes, province/prefecture/county identifiers,
and education-related variables used to construct education outcomes.

## 02. Core 2015 census education microdata construction

Source notebook: internal original notebook (non-public source filename omitted).

GitHub script: `02_build_census2015_microdata_base.py`

Build the main individual-level education microdata base, including demographic
variables, county codes, birth year, education outcomes, and sample filters.

## 03. County-by-birth-cohort scaffold and analysis-design notes

Source notebook: internal original notebook (non-public source filename omitted).

GitHub script: `03_build_county_birthyear_scaffold.py`

Prepare or document the county-by-birth-year structure used later to link
childhood flood exposure windows to the 2015 census education sample.

## Data restriction

Do not commit raw census files, Stata/SPSS files, individual-level processed
data, or merged exposure-microdata files to GitHub.
