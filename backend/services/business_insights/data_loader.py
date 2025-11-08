from __future__ import annotations

from dataclasses import dataclass
from io import StringIO
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from flask import Request


@dataclass
class DetectedSeries:
    revenue: pd.Series
    profit: pd.Series
    profit_margin: pd.Series
    churn: Optional[pd.Series]
    company_column: Optional[str]


def load_dataframe(request: Request) -> pd.DataFrame:
    """Load raw CSV data from the request and perform basic cleaning."""
    upload = request.files.get("kpi_file")
    if not upload or not upload.filename:
        raise ValueError("No file uploaded. Please attach a CSV file.")

    try:
        raw = upload.stream.read().decode("utf-8", errors="ignore")
        buffer = StringIO(raw)
        df = pd.read_csv(
            buffer,
            engine="python",
            on_bad_lines="skip",
            dtype=str,
        )
    except Exception as exc:
        raise ValueError("Unable to parse uploaded CSV file.") from exc

    if df.empty:
        raise ValueError("Uploaded CSV is empty.")

    df = df.dropna(how="all")
    df = df.apply(lambda col: col.str.strip() if col.dtype == object else col)
    return df


def coerce_numeric(series: pd.Series) -> pd.Series:
    if series.empty:
        return pd.Series(dtype=float)
    cleaned = (
        series.astype(str)
        .str.replace(r"\(([^)]+)\)", r"-\1", regex=True)
        .str.replace(r"[^\d\.\-]", "", regex=True)
    )
    return pd.to_numeric(cleaned, errors="coerce")


def identify_numeric_columns(df: pd.DataFrame) -> Tuple[List[str], Dict[str, pd.Series]]:
    numeric_cols: List[str] = []
    numeric_cache: Dict[str, pd.Series] = {}
    total_rows = len(df)
    threshold = max(3, int(0.2 * total_rows))
    for column in df.columns:
        numeric_series = coerce_numeric(df[column])
        numeric_cache[column] = numeric_series
        if numeric_series.notna().sum() >= threshold:
            numeric_cols.append(column)
    return numeric_cols, numeric_cache


def detect_columns(df: pd.DataFrame) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for column in df.columns:
        name = str(column).lower().strip()
        if any(keyword in name for keyword in ("sales", "revenue", "turnover", "amount")):
            mapping.setdefault("revenue", column)
        if "profit" in name or "margin" in name:
            mapping.setdefault("profit", column)
        if any(keyword in name for keyword in ("cost", "expense", "cogs")):
            mapping.setdefault("cost", column)
        if "churn" in name or "attrition" in name:
            mapping.setdefault("churn", column)
        if any(keyword in name for keyword in ("company", "account", "store", "branch", "segment", "customer id")):
            mapping.setdefault("company", column)
        if "region" in name:
            mapping.setdefault("region", column)
        if "segment" in name:
            mapping.setdefault("segment", column)
        if "category" in name and "sub" not in name:
            mapping.setdefault("category", column)
        if "sub-category" in name or "subcategory" in name:
            mapping.setdefault("sub_category", column)
        if "product" in name:
            mapping.setdefault("product", column)
        if "date" in name:
            mapping.setdefault("date", column)
        if "country" in name:
            mapping.setdefault("country", column)
    return mapping


def resolve_series(
    df: pd.DataFrame,
    mapping: Dict[str, str],
    numeric_cols: List[str],
    numeric_cache: Dict[str, pd.Series],
) -> DetectedSeries:
    revenue_col = mapping.get("revenue") or (numeric_cols[0] if numeric_cols else None)
    if revenue_col is None:
        raise ValueError("Unable to identify a revenue or sales column.")

    revenue_series = numeric_cache.get(revenue_col)
    revenue_series = (revenue_series if revenue_series is not None else coerce_numeric(df[revenue_col])).fillna(0.0)

    if mapping.get("profit"):
        profit_series = numeric_cache.get(mapping["profit"])
        profit_series = (profit_series if profit_series is not None else coerce_numeric(df[mapping["profit"]])).fillna(0.0)
    elif mapping.get("cost"):
        cost_series = numeric_cache.get(mapping["cost"])
        cost_series = (cost_series if cost_series is not None else coerce_numeric(df[mapping["cost"]])).fillna(0.0)
        profit_series = revenue_series - cost_series
    else:
        fallback_col = next((col for col in numeric_cols if col != revenue_col), None)
        if fallback_col:
            profit_series = numeric_cache.get(fallback_col)
            profit_series = (profit_series if profit_series is not None else coerce_numeric(df[fallback_col])).fillna(0.0)
        else:
            profit_series = revenue_series.copy()

    profit_margin = np.divide(
        profit_series,
        revenue_series.replace(0, np.nan),
    ).replace([np.inf, -np.inf], np.nan).fillna(0.0)

    churn_series: Optional[pd.Series] = None
    if mapping.get("churn"):
        churn_series = numeric_cache.get(mapping["churn"])
        churn_series = (churn_series if churn_series is not None else coerce_numeric(df[mapping["churn"]])).fillna(0.0)

    company_col = mapping.get("company")
    if company_col not in df.columns:
        company_col = "Company" if "Company" in df.columns else None

    return DetectedSeries(
        revenue=revenue_series,
        profit=profit_series,
        profit_margin=profit_margin,
        churn=churn_series,
        company_column=company_col,
    )
