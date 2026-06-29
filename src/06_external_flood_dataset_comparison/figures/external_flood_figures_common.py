#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Common helper functions for external flood comparison figure scripts.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def ensure_dir(path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


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
