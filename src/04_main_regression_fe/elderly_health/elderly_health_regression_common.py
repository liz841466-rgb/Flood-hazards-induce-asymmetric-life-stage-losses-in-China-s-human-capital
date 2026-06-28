#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Common helper functions for elderly-health fixed-effects regression scripts.

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


def add_constant_if_needed(df: pd.DataFrame, const_name: str = "const") -> pd.DataFrame:
    out = df.copy()
    if const_name not in out.columns:
        out[const_name] = 1.0
    return out


def star_pvalue(p: float) -> str:
    if pd.isna(p):
        return ""
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""


def format_coef_with_se(coef, se, p=None, digits: int = 3) -> str:
    if pd.isna(coef):
        return ""
    stars = star_pvalue(p) if p is not None else ""
    if pd.isna(se):
        return f"{coef:.{digits}f}{stars}"
    return f"{coef:.{digits}f}{stars} ({se:.{digits}f})"


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
