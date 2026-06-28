# Data availability

This repository contains code only. It does not redistribute restricted,
licensed, non-public, or large derived datasets.

## Data not included

The following data categories are intentionally excluded:

- CHARLS raw microdata and derived individual-level health panels.
- 2015 China 1% Population Sample Survey raw microdata and derived individual-level education panels.
- CHFS/CFHS raw household microdata and derived household-level mechanism panels.
- School POI raw records and school-level derived outputs.
- DFO and GFD raw flood datasets.
- Hydrodynamic-model outputs, rasters, NetCDF files, shapefiles, and geospatial overlays.
- Exposure-linked final analysis panels.
- Local regression outputs, plotting data, final figures, and supplementary figure outputs.

## Configuration

Each module includes a `config.example.yaml` file describing the expected local
input and output paths. Users with authorized access to the required data should
copy it to `config.yaml` and edit paths locally. `config.yaml` files should not
be committed.

## Reproducibility limitation

Because several required datasets are restricted or non-redistributable, this
repository documents the workflow rather than providing a one-command public
replication package.
