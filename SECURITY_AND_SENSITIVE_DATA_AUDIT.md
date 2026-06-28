# Security and sensitive-data checklist

This repository is intended to contain code and documentation only.

## Do not commit

- CHARLS raw microdata or derived individual-level panels.
- 2015 Census raw microdata or derived individual-level panels.
- CHFS/CFHS raw household data or household-level processed panels.
- School POI raw point records.
- DFO/GFD raw files, event masks, or downloaded archives.
- Hydrodynamic model outputs, rasters, shapefiles, NetCDF files, or other large geospatial data.
- Exposure-linked final analysis panels.
- Local regression outputs, plotting data, final tables, or final figures.

## Public repository contents

The public repository should contain source code, concise workflow
documentation, and `config.example.yaml` templates only. Local `config.yaml`
files should remain untracked.

## Review before release

Review new files manually before pushing to GitHub, especially files with data,
output, figure, table, raster, shapefile, census, CHARLS, CHFS/CFHS, or POI in
their names or paths.
