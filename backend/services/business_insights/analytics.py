from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from pandas.api.types import is_datetime64_any_dtype
from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler

from .data_loader import DetectedSeries, coerce_numeric


@dataclass
class InsightPayload:
    clusters: List[Dict[str, float]]
    cluster_scatter: List[Dict[str, float]]
    trend_data: List[Dict[str, float]]
    segment_breakdown: List[Dict[str, float]]
    category_breakdown: List[Dict[str, float]]
    region_breakdown: List[Dict[str, float]]
    product_leaders: List[Dict[str, float]]
    alerts: List[Dict[str, float]]


def build_cluster_payload(revenue: pd.Series, profit: pd.Series, profit_margin: pd.Series) -> Dict[str, object]:
    features = pd.DataFrame(
        {
            "Revenue": revenue,
            "ProfitMargin": profit_margin,
            "Profit": profit,
        }
    )

    clean_features = features.replace([np.inf, -np.inf], np.nan).dropna()
    if clean_features.shape[0] < 3:
        raise ValueError("Not enough valid data points for clustering.")

    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(clean_features)

    n_clusters = min(3, clean_features.shape[0])
    kmeans = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
    labels = kmeans.fit_predict(scaled)

    clean_features = clean_features.copy()
    clean_features["Cluster"] = labels

    cluster_scatter = [
        {
            "x": float(row["ProfitMargin"]),
            "y": float(row["Revenue"]),
            "cluster": int(row["Cluster"]),
        }
        for _, row in clean_features.iterrows()
    ]

    clusters = []
    for cluster_id, subset in clean_features.groupby("Cluster"):
        clusters.append(
            {
                "cluster": int(cluster_id),
                "avg_profit": round(float(subset["Profit"].mean()), 2),
                "avg_profit_margin": round(float(subset["ProfitMargin"].mean()), 4),
                "count": int(subset.shape[0]),
            }
        )
    clusters.sort(key=lambda item: item["cluster"])

    return {"cluster_scatter": cluster_scatter, "clusters": clusters}


def build_forecast(revenue_series: pd.Series, periods: int = 12) -> Dict[str, List[float]]:
    revenue_series = revenue_series.dropna()
    base = float(revenue_series.tail(12).mean()) if not revenue_series.empty else 0.0
    months = pd.period_range(start=pd.Timestamp.today().to_period("M"), periods=periods, freq="M")
    revenue_forecast = [round(base * (1 + 0.01 * idx), 2) for idx in range(periods)]
    return {
        "dates": [str(period) for period in months],
        "revenue_forecast": revenue_forecast,
    }


def build_kpi_summary(df: pd.DataFrame, mapping: Dict[str, str], detected: DetectedSeries) -> Dict[str, float]:
    summary = {
        "total_revenue": round(float(detected.revenue.sum()), 2),
        "avg_profit_margin": round(float(detected.profit_margin.mean()), 4),
        "num_companies": int(df[detected.company_column].nunique()) if detected.company_column else int(len(df)),
    }
    if detected.churn is not None:
        summary["avg_churn"] = round(float(detected.churn.mean()), 4)
    else:
        summary["avg_churn"] = None
    return summary


def _safe_groupby_sum(df: pd.DataFrame, column: Optional[str], values: pd.Series) -> Optional[pd.Series]:
    if not column or column not in df.columns:
        return None
    grouped = values.groupby(df[column]).sum().sort_values(ascending=False)
    return grouped


def _prepare_breakdown(
    grouping: Optional[pd.Series],
    profit_series: pd.Series,
    df: pd.DataFrame,
    column: Optional[str],
) -> List[Dict[str, float]]:
    if grouping is None or column not in df.columns:
        return []
    profit_group = profit_series.groupby(df[column]).sum()
    records = []
    for label, revenue in grouping.head(5).items():
        profit = profit_group.get(label, 0.0)
        margin = 0.0 if revenue == 0 else float(profit) / float(revenue)
        records.append(
            {
                "label": str(label),
                "revenue": round(float(revenue), 2),
                "profit": round(float(profit), 2),
                "profit_margin": round(float(margin), 4),
            }
        )
    return records


def build_dimension_insights(
    df: pd.DataFrame,
    mapping: Dict[str, str],
    detected: DetectedSeries,
) -> Dict[str, List[Dict[str, float]]]:
    segment_group = _safe_groupby_sum(df, mapping.get("segment"), detected.revenue)
    category_group = _safe_groupby_sum(df, mapping.get("category"), detected.revenue)
    region_group = _safe_groupby_sum(df, mapping.get("region"), detected.revenue)
    product_group = _safe_groupby_sum(df, mapping.get("product"), detected.revenue)

    products = []
    if product_group is not None:
        profit_group = detected.profit.groupby(df[mapping.get("product")]).sum()
        for label, revenue in product_group.head(5).items():
            profit = profit_group.get(label, 0.0)
            products.append(
                {
                    "product": str(label),
                    "revenue": round(float(revenue), 2),
                    "profit": round(float(profit), 2),
                }
            )

    return {
        "segments": _prepare_breakdown(segment_group, detected.profit, df, mapping.get("segment")),
        "categories": _prepare_breakdown(category_group, detected.profit, df, mapping.get("category")),
        "regions": _prepare_breakdown(region_group, detected.profit, df, mapping.get("region")),
        "products": products,
    }


def build_trend_data(
    df: pd.DataFrame,
    mapping: Dict[str, str],
    detected: DetectedSeries,
) -> List[Dict[str, float]]:
    date_col = mapping.get("date")
    if not date_col or date_col not in df.columns:
        # search for generic date column
        for candidate in df.columns:
            if "date" in candidate.lower():
                date_col = candidate
                break

    if not date_col or date_col not in df.columns:
        return []

    dates = pd.to_datetime(df[date_col], errors="coerce")
    if dates.isna().all():
        return []

    df_copy = pd.DataFrame(
        {
            "date": dates,
            "Revenue": detected.revenue,
            "Profit": detected.profit,
        }
    ).dropna(subset=["date"])

    if df_copy.empty:
        return []

    df_copy["period"] = df_copy["date"].dt.to_period("M")
    aggregated = df_copy.groupby("period").agg({"Revenue": "sum", "Profit": "sum"}).sort_index().tail(12)
    return [
        {
            "period": str(period),
            "revenue": round(float(row["Revenue"]), 2),
            "profit": round(float(row["Profit"]), 2),
        }
        for period, row in aggregated.iterrows()
    ]


def build_alerts(
    df: pd.DataFrame,
    mapping: Dict[str, str],
    detected: DetectedSeries,
    numeric_cache: Dict[str, pd.Series],
) -> List[Dict[str, float]]:
    alerts: List[Dict[str, float]] = []

    discount_col = None
    for column in df.columns:
        if "discount" in column.lower() or "markdown" in column.lower():
            discount_col = column
            break

    if discount_col:
        discount_series = numeric_cache.get(discount_col)
        if discount_series is None:
            discount_series = coerce_numeric(df[discount_col])
        df_discount = pd.DataFrame(
            {
                "discount": discount_series,
                "profit": detected.profit,
                "revenue": detected.revenue,
                "label": df.get(mapping.get("product") or mapping.get("segment") or discount_col),
            }
        )
        df_discount = df_discount.replace([np.inf, -np.inf], np.nan).dropna(subset=["discount", "profit"])

        high_discount_losses = df_discount[df_discount["profit"] < 0].nlargest(5, "discount")
        for _, row in high_discount_losses.iterrows():
            alerts.append(
                {
                    "title": str(row["label"]) if pd.notna(row["label"]) else "High discount loss",
                    "description": "High discount with negative profit",
                    "discount": round(float(row["discount"]), 2),
                    "profit": round(float(row["profit"]), 2),
                }
            )

    label_key = mapping.get("product") or mapping.get("segment") or mapping.get("category")
    low_margin = pd.DataFrame(
        {
            "profit_margin": detected.profit_margin,
            "profit": detected.profit,
            "label": df[label_key] if label_key and label_key in df.columns else None,
        }
    )
    low_margin = low_margin.replace([np.inf, -np.inf], np.nan).dropna(subset=["profit_margin"])
    low_margin_records = low_margin.nsmallest(5, "profit_margin")
    for _, row in low_margin_records.iterrows():
        if row["profit_margin"] > 0.15:
            continue
        alerts.append(
            {
                "title": str(row["label"]) if pd.notna(row["label"]) else "Low margin item",
                "description": "Profit margin below 15%",
                "profit_margin": round(float(row["profit_margin"]), 4),
                "profit": round(float(row["profit"]), 2),
            }
        )

    return alerts[:5]
