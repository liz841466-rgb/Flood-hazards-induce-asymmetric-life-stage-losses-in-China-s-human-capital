#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Common helper functions for GFD/POD-style event validation scripts.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def ensure_dir(path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def binary_metrics(tp, fp, fn):
    tp = float(tp)
    fp = float(fp)
    fn = float(fn)
    pod = tp / (tp + fn) if (tp + fn) > 0 else np.nan
    far = fp / (tp + fp) if (tp + fp) > 0 else np.nan
    csi = tp / (tp + fp + fn) if (tp + fp + fn) > 0 else np.nan
    return {"POD": pod, "FAR": far, "CSI": csi}


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
