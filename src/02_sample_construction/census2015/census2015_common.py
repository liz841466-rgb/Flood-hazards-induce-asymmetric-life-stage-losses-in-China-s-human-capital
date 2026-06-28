#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Common helper functions for 2015 census sample-construction code.

This file intentionally contains generic utilities only. The original notebook
logic is preserved in the stage scripts and legacy notebook exports.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd


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
