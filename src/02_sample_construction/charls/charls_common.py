#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archived notebook note for charls_common.

This public compact repository keeps notebook-export code for workflow auditability. Restricted raw data and derived individual-level panels are not included."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd


CHARLS_WAVES = [2011, 2013, 2015, 2018, 2020]


def ensure_dir(path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def normalize_id_series(s: pd.Series) -> pd.Series:
    return s.astype("string").str.strip()


def require_columns(df: pd.DataFrame, columns: Sequence[str], table_name: str = "dataframe") -> None:
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise KeyError(f"{table_name} is missing required columns: {missing}")


def coerce_numeric(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    out = df.copy()
    for c in columns:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    return out


def row_mean_with_min_valid(df: pd.DataFrame, columns: Sequence[str], min_valid: int = 1) -> pd.Series:
    vals = df[list(columns)]
    n_valid = vals.notna().sum(axis=1)
    out = vals.mean(axis=1, skipna=True)
    out[n_valid < min_valid] = np.nan
    return out


def save_table(df: pd.DataFrame, path, index: bool = False) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    suffix = path.suffix.lower()
    if suffix == ".csv":
        df.to_csv(path, index=index, encoding="utf-8-sig")
    elif suffix in [".parquet", ".pq"]:
        df.to_parquet(path, index=index)
    elif suffix in [".xlsx", ".xls"]:
        df.to_excel(path, index=index)
    else:
        raise ValueError(f"Unsupported output suffix: {suffix}")
