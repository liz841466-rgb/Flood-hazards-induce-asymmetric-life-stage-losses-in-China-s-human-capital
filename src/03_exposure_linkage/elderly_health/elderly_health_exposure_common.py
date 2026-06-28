#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Common helper functions for elderly-health exposure-linkage scripts.

This file contains generic utilities only. The original notebook logic is
preserved in the archived workflow scripts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd


RETURN_PERIODS = [2, 5, 10, 20, 50, 100]
ROLLING_WINDOWS = [5, 10, 20, 30]


def ensure_dir(path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def normalize_code_series(s: pd.Series, width: int | None = None) -> pd.Series:
    out = s.astype("string").str.strip()
    if width is not None:
        out = out.str.zfill(width)
    return out


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


def build_rolling_count_exposure(
    event_df: pd.DataFrame,
    group_col: str,
    year_col: str,
    event_col: str,
    target_years: Sequence[int],
    windows: Sequence[int] = ROLLING_WINDOWS,
    include_current_year: bool = False,
) -> pd.DataFrame:
    """
    Build rolling count exposure for each group and target year.

    This helper is generic and is not a substitute for the original notebook
    logic. It is provided for transparent local reuse.
    """
    require_columns(event_df, [group_col, year_col, event_col], "event_df")

    df = event_df[[group_col, year_col, event_col]].copy()
    df[year_col] = pd.to_numeric(df[year_col], errors="coerce").astype("Int64")
    df[event_col] = pd.to_numeric(df[event_col], errors="coerce").fillna(0)

    groups = sorted(df[group_col].dropna().unique())
    rows = []

    for g in groups:
        gdf = df[df[group_col] == g].set_index(year_col)[event_col].sort_index()
        for y in target_years:
            row = {group_col: g, "target_year": int(y)}
            for w in windows:
                start = int(y) - int(w) + (0 if include_current_year else 1)
                end = int(y) if include_current_year else int(y) - 1
                years = list(range(start, end + 1))
                row[f"{event_col}_{w}y_count"] = float(gdf.reindex(years).fillna(0).sum())
            rows.append(row)

    return pd.DataFrame(rows)


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
