"""Dynamic weighting for the market-entry advisor."""

from __future__ import annotations

from typing import Dict

BASE_WEIGHTS: Dict[str, float] = {
    "GDP_Growth": 0.22,
    "Inflation": 0.12,
    "Internet_Penetration": 0.18,
    "Population_Millions": 0.18,
    "purchasing_power_index_cost_of_living": 0.12,
    "corruption_index_corruption": 0.09,
    "cost_index_cost_of_living": 0.09,
}


def _adjust(weights: Dict[str, float], key: str, delta: float) -> None:
    weights[key] = max(0.0, weights.get(key, 0.0) + delta)


def _normalize(weights: Dict[str, float]) -> Dict[str, float]:
    total = sum(weights.values())
    if total == 0:
        return BASE_WEIGHTS.copy()
    return {k: round(v / total, 3) for k, v in weights.items()}


def get_weights_for_profile(
    industry: str | None,
    business_model: str | None,
    presence_mode: str | None,
    target_market: str | None,
    risk_profile: str | None,
    capital: float | int | None = None,
    customer_type: str | None = None,
) -> Dict[str, float]:
    """Map user preferences to indicator weights."""
    weights = BASE_WEIGHTS.copy()
    industry = (industry or "").strip()
    business_model = (business_model or "").strip()
    presence_mode = (presence_mode or "").strip()
    target_market = (target_market or "").strip()
    risk_profile = (risk_profile or "").strip()
    customer_type = (customer_type or "").strip()

    # Industry lens
    digital_first = {
        "Technology",
        "Finance",
        "Media",
        "Telecom",
        "Healthcare",
        "Entertainment & Media",
        "Education",
    }
    population_driven = {
        "Retail",
        "Manufacturing",
        "Hospitality",
        "Consumer Goods",
        "Transportation & Logistics",
        "Construction & Real Estate",
        "Agriculture",
        "Professional Services",
    }

    if industry in digital_first:
        _adjust(weights, "Internet_Penetration", 0.12)
        _adjust(weights, "purchasing_power_index_cost_of_living", 0.05)
        _adjust(weights, "GDP_Growth", -0.04)
    elif industry in population_driven:
        _adjust(weights, "Population_Millions", 0.1)
        _adjust(weights, "cost_index_cost_of_living", 0.04)
    elif industry == "Energy":
        _adjust(weights, "GDP_Growth", 0.1)
        _adjust(weights, "Inflation", 0.05)

    # Business model emphasis
    digital_models = {
        "Online",
        "Subscription",
        "Marketplace",
        "Platform",
        "Dropshipping",
        "Licensing/IP",
        "Brokerage",
    }
    if business_model in digital_models:
        _adjust(weights, "Internet_Penetration", 0.1)
        _adjust(weights, "Population_Millions", -0.05)
    elif business_model in {"Brick-and-Mortar", "Franchise", "Product-based", "Manufacturing"}:
        _adjust(weights, "Population_Millions", 0.1)
    elif business_model == "Service-based":
        _adjust(weights, "GDP_Growth", 0.05)
        _adjust(weights, "corruption_index_corruption", 0.03)

    # Presence mode
    if presence_mode == "Digital":
        _adjust(weights, "Internet_Penetration", 0.05)
    elif presence_mode == "Physical":
        _adjust(weights, "Population_Millions", 0.05)
    elif presence_mode == "Hybrid":
        _adjust(weights, "GDP_Growth", 0.025)
        _adjust(weights, "Internet_Penetration", 0.025)

    # Target market positioning
    if target_market == "Mass Market":
        _adjust(weights, "Population_Millions", 0.05)
    elif target_market == "Premium":
        _adjust(weights, "GDP_Growth", 0.05)
    elif target_market == "Budget":
        _adjust(weights, "Inflation", 0.05)
        _adjust(weights, "cost_index_cost_of_living", 0.04)
    elif target_market == "Niche":
        _adjust(weights, "Internet_Penetration", 0.05)

    # Risk appetite adjustments
    if risk_profile == "High":
        _adjust(weights, "Inflation", -0.05)  # penalize inflation less
        _adjust(weights, "GDP_Growth", 0.05)
    elif risk_profile == "Low":
        _adjust(weights, "Inflation", 0.05)
        _adjust(weights, "corruption_index_corruption", 0.05)
        _adjust(weights, "GDP_Growth", -0.025)

    # Capital availability (rough heuristic thresholds)
    try:
        capital_value = float(capital) if capital is not None else 0.0
    except (TypeError, ValueError):
        capital_value = 0.0

    if capital_value >= 50_000_000:
        _adjust(weights, "Population_Millions", 0.05)
        _adjust(weights, "GDP_Growth", 0.025)
    elif 0 < capital_value < 5_000_000:
        _adjust(weights, "Inflation", 0.025)  # need stability
        _adjust(weights, "Internet_Penetration", 0.025)  # favor digital reach

    # Customer type emphasis
    if customer_type == "B2C":
        _adjust(weights, "Population_Millions", 0.08)
        _adjust(weights, "Internet_Penetration", 0.05)
        _adjust(weights, "purchasing_power_index_cost_of_living", 0.05)
        _adjust(weights, "cost_index_cost_of_living", 0.03)
    elif customer_type == "B2B":
        _adjust(weights, "GDP_Growth", 0.05)
        _adjust(weights, "Inflation", 0.08)
        _adjust(weights, "corruption_index_corruption", 0.05)
    elif customer_type == "B2G":
        _adjust(weights, "GDP_Growth", 0.1)
        _adjust(weights, "Inflation", 0.05)
        _adjust(weights, "corruption_index_corruption", 0.05)
    elif customer_type == "C2C":
        _adjust(weights, "Internet_Penetration", 0.1)
        _adjust(weights, "Population_Millions", 0.05)
        _adjust(weights, "purchasing_power_index_cost_of_living", 0.04)
    elif customer_type == "B2B2C":
        _adjust(weights, "Internet_Penetration", 0.05)
        _adjust(weights, "GDP_Growth", 0.05)
        _adjust(weights, "purchasing_power_index_cost_of_living", 0.03)

    return _normalize(weights)
