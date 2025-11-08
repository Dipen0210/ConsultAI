"""Market Entry Strategy Advisor with dynamic weighting."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict

import pandas as pd
from flask import Blueprint, jsonify, request
from sklearn.preprocessing import MinMaxScaler

try:
    from backend.services.hf_client import generate_explainable_summary
    from backend.utils.weights_mapper import get_weights_for_profile
except ImportError:  # pragma: no cover - fallback when running as script
    from services.hf_client import generate_explainable_summary
    from utils.weights_mapper import get_weights_for_profile

market_entry_bp = Blueprint("market_entry", __name__)

CORE_FEATURES = [
    "GDP_Growth",
    "Inflation",
    "Internet_Penetration",
    "Population_Millions",
]
AUX_FEATURES = [
    "corruption_index_corruption",
    "cost_index_cost_of_living",
    "purchasing_power_index_cost_of_living",
]
SCORING_FEATURES = CORE_FEATURES + AUX_FEATURES
NEGATIVE_FEATURES = {"Inflation", "corruption_index_corruption", "cost_index_cost_of_living"}
REQUIRED_PAYLOAD_FIELDS = [
    "industry",
    "business_model",
    "presence_mode",
    "risk_profile",
    "customer_type",
]
REGION_COLUMN = "Region"


def _dataset_path() -> Path:
    override = os.getenv("MARKET_DATA_CSV")
    if override:
        candidate = Path(override).expanduser()
        if candidate.exists():
            return candidate
    return Path(__file__).resolve().parents[1] / "data" / "all_data.csv"


def _load_dataset() -> pd.DataFrame:
    path = _dataset_path()
    if not path.exists():
        raise FileNotFoundError(
            "Market dataset not found. Run backend/data/fetch_market_data.py first."
        )

    df = pd.read_csv(path)
    missing = set(["Country", REGION_COLUMN] + SCORING_FEATURES) - set(df.columns)
    if missing:
        raise ValueError(
            f"Dataset missing required columns: {', '.join(sorted(missing))}"
        )

    df = df.dropna(subset=SCORING_FEATURES)
    df = df[df["Internet_Penetration"] > 0]
    if df.empty:
        raise ValueError("No usable market rows remain after cleaning.")
    return df


def _parse_payload(payload: Dict[str, object]) -> Dict[str, object]:
    missing = [field for field in REQUIRED_PAYLOAD_FIELDS if not payload.get(field)]
    if missing:
        raise ValueError(
            f"Missing required fields: {', '.join(field for field in missing)}"
        )

    parsed = {
        "industry": payload.get("industry"),
        "business_model": payload.get("business_model"),
        "presence_mode": payload.get("presence_mode"),
        "target_market": payload.get("target_market") or "Mass Market",
        "risk_profile": payload.get("risk_profile"),
        "capital": payload.get("capital") or 0,
        "customer_type": payload.get("customer_type") or "B2C",
        "regions": payload.get("regions") or [],
    }
    return parsed


def _filter_by_regions(df: pd.DataFrame, regions: list[str]) -> pd.DataFrame:
    cleaned = [region.strip().lower() for region in regions if region]
    if not cleaned:
        return df
    filtered = df[
        df[REGION_COLUMN]
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(cleaned)
    ]
    if filtered.empty:
        raise ValueError("No countries match the selected regions.")
    return filtered


def _build_metric_breakdown(
    ranked_df: pd.DataFrame, weights: Dict[str, float], limit: int = 5
) -> list[Dict[str, object]]:
    breakdown = []
    for _, row in ranked_df.head(limit).iterrows():
        metrics = {}
        for metric in SCORING_FEATURES:
            normalized = float(row[metric])
            weight = weights.get(metric, 0.0)
            metrics[metric] = {
                "raw": float(row.get(f"{metric}_raw", row[metric])),
                "normalized": round(normalized, 4),
                "weight": weight,
                "contribution": round(float(row.get(f"{metric}_contribution", 0.0)), 4),
            }
        breakdown.append(
            {
                "country": row["Country"],
                "score": row["Score"],
                "metrics": metrics,
            }
        )
    return breakdown


@market_entry_bp.route("/api/market-entry", methods=["POST"])
def market_entry():
    payload = request.get_json(silent=True) or {}

    try:
        inputs = _parse_payload(payload)
        dataset = _filter_by_regions(_load_dataset(), inputs["regions"])

        scaler = MinMaxScaler()
        normalized = scaler.fit_transform(dataset[SCORING_FEATURES])
        df_norm = pd.DataFrame(
            normalized, columns=SCORING_FEATURES, index=dataset.index
        )
        df_norm["Country"] = dataset["Country"].values
        for column in SCORING_FEATURES:
            df_norm[f"{column}_raw"] = dataset[column].values

        weights = get_weights_for_profile(
            inputs["industry"],
            inputs["business_model"],
            inputs["presence_mode"],
            inputs["target_market"],
            inputs["risk_profile"],
            inputs["capital"],
            inputs["customer_type"],
        )

        contributions = []
        score_series = pd.Series(0, index=df_norm.index, dtype=float)
        for feature in SCORING_FEATURES:
            weight = weights.get(feature, 0.0)
            if weight == 0:
                df_norm[f"{feature}_contribution"] = 0.0
                continue
            values = df_norm[feature]
            if feature in NEGATIVE_FEATURES:
                contribution = weight * (1 - values)
            else:
                contribution = weight * values
            df_norm[f"{feature}_contribution"] = contribution
            score_series += contribution
        df_norm["Score"] = score_series

        ranked = (
            df_norm.sort_values("Score", ascending=False)
            .reset_index(drop=True)
            .copy()
        )
        ranked["Score"] = ranked["Score"].round(4)
        top_markets = ranked.head(5)[["Country", "Score"]].to_dict(orient="records")
        chart_data = {
            "countries": ranked["Country"].head(10).tolist(),
            "scores": ranked["Score"].head(10).tolist(),
        }
        breakdown = _build_metric_breakdown(ranked, weights)

        leaders = [entry["Country"] for entry in top_markets]
        customer_type = inputs["customer_type"]
        if not leaders:
            summary = "No markets met the criteria. Adjust your profile inputs and retry."
        elif len(leaders) == 1:
            summary = (
                f"Consider prioritizing {leaders[0]} for a {customer_type} {inputs['industry'].lower()} expansion "
                f"given the selected {inputs['risk_profile'].lower()} risk profile."
            )
        else:
            summary = (
                f"For a {customer_type} {inputs['industry']} company operating a {inputs['business_model']} model "
                f"with a {inputs['presence_mode'].lower()} presence and {inputs['risk_profile'].lower()} risk appetite, "
                f"consider {', '.join(leaders[:-1])} and {leaders[-1]} as leading expansion markets."
            )

        explainable_summary = generate_explainable_summary(
            weights,
            inputs,
            leaders,
            breakdown[:3],
        )

        response_data = {
            "top_markets": top_markets,
            "weights_used": weights,
            "summary": summary,
            "chart_data": chart_data,
            "explainable_summary": explainable_summary,
            "metric_breakdown": breakdown,
        }
        return jsonify({"status": "success", "data": response_data})
    except (ValueError, FileNotFoundError) as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    except Exception as exc:  # pragma: no cover
        return jsonify({"status": "error", "message": f"Unexpected error: {exc}"}), 500
