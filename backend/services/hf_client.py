"""Helpers for interacting with Hugging Face Inference API."""

from __future__ import annotations

import os
from typing import Dict, Iterable, List

import requests

MODEL_ID = os.getenv("HF_EXPLAIN_MODEL", "google/flan-t5-base")
API_URL = f"https://api-inference.huggingface.co/models/{MODEL_ID}"

METRIC_DESCRIPTIONS = {
    "GDP_Growth": "GDP growth captures how quickly an economy expands year over year.",
    "Internet_Penetration": "Internet penetration reflects digital readiness and online reach.",
    "Population_Millions": "Population shows the scale of potential customers in millions.",
    "purchasing_power_index_cost_of_living": "Purchasing power shows how much consumers can actually spend.",
    "Inflation": "Inflation penalizes markets where prices are rising too fast.",
    "corruption_index_corruption": "Corruption index captures governance risk—lower is better.",
    "cost_index_cost_of_living": "Cost index approximates operating expenses—lower is better.",
}

NEGATIVE_METRICS = {"Inflation", "corruption_index_corruption", "cost_index_cost_of_living"}

METRIC_LABELS = {
    "GDP_Growth": "growth",
    "Internet_Penetration": "digital reach",
    "Population_Millions": "market scale",
    "purchasing_power_index_cost_of_living": "consumer spending power",
    "Inflation": "price stability",
    "corruption_index_corruption": "governance risk",
    "cost_index_cost_of_living": "operating cost",
}


def _format_metric_weights(weights: Dict[str, float]) -> str:
    top_weights = sorted(weights.items(), key=lambda item: item[1], reverse=True)[:5]
    phrases = []
    for metric, weight in top_weights:
        if weight <= 0:
            continue
        label = METRIC_LABELS.get(metric, metric)
        phrases.append(f"{label} (~{weight * 100:.0f}%)")
    return "Emphasis mix: " + ", ".join(phrases)


def _format_breakdown_lines(breakdown: Iterable[Dict[str, object]]) -> str:
    lines = []
    for entry in breakdown:
        metrics = entry["metrics"]
        top_metrics = sorted(
            metrics.items(), key=lambda item: item[1]["contribution"], reverse=True
        )[:3]
        fragments = []
        for metric, detail in top_metrics:
            label = METRIC_LABELS.get(metric, metric.replace("_", " "))
            raw = detail["raw"]
            if metric == "Population_Millions":
                raw_text = f"{raw:.0f}M people"
            elif metric == "Internet_Penetration":
                raw_text = f"{raw:.0f}% online"
            elif metric == "GDP_Growth":
                raw_text = f"{raw:.1f}% growth"
            elif metric == "purchasing_power_index_cost_of_living":
                raw_text = f"index {raw:.1f}"
            elif metric == "corruption_index_corruption":
                raw_text = f"score {raw:.0f}"
            elif metric == "cost_index_cost_of_living":
                raw_text = f"index {raw:.1f}"
            elif metric == "Inflation":
                raw_text = f"{raw:.1f}% inflation"
            else:
                raw_text = f"{raw:.2f}"
            fragments.append(f"{label}: {raw_text}")
        lines.append(f"• {entry['country']} – " + "; ".join(fragments))
    return "\n".join(lines)


def _build_recommendation(
    profile: Dict[str, str],
    breakdown: Iterable[Dict[str, object]] | None,
) -> str | None:
    entries = list(breakdown or [])
    if not entries:
        return None
    leader = entries[0]
    metrics = leader["metrics"]
    top_metrics = sorted(
        metrics.items(), key=lambda item: item[1]["contribution"], reverse=True
    )[:2]
    phrases = []
    for metric, detail in top_metrics:
        label = METRIC_LABELS.get(metric, metric.replace("_", " "))
        qualifier = "high" if metric not in NEGATIVE_METRICS else "low"
        phrases.append(f"{qualifier} {label}")
    overview = ", ".join(phrases)
    customer_type = profile.get("customer_type", "your")
    return f"For a {customer_type} profile, {leader['country']} stands out thanks to {overview}."


def _fallback_explanation(
    weights: Dict[str, float],
    leaders: Iterable[str],
    breakdown: Iterable[Dict[str, object]] | None = None,
) -> str:
    leader_text = ", ".join(leaders) if leaders else "the highlighted countries"
    rationale = (
        f"We ranked {leader_text} by blending GDP growth, digital adoption, market scale, "
        f"consumer purchasing power, price stability, governance risk, and operating cost. "
        "Lower corruption and cost indices improve scores, while lower inflation rewards stability."
    )
    breakdown_text = _format_breakdown_lines(breakdown or [])
    recommendation = _build_recommendation({}, breakdown)
    body = f"{rationale}\nKey highlights:\n{breakdown_text}" if breakdown_text else rationale
    if recommendation:
        body = f"{body}\nRecommendation: {recommendation}"
    return body


def generate_explainable_summary(
    weights: Dict[str, float],
    profile: Dict[str, str],
    leaders: List[str],
    metric_breakdown: List[Dict[str, object]] | None = None,
) -> str:
    """Produce a natural-language explanation of the scoring approach."""
    api_key = os.getenv("HF_API_KEY")
    if not api_key:
        return _fallback_explanation(weights, leaders, metric_breakdown)

    metrics_section = _format_metric_weights(weights)
    leaders_text = ", ".join(leaders[:3]) if leaders else "the shortlisted markets"
    top_breakdown = (metric_breakdown or [])[:3]
    breakdown_section = _format_breakdown_lines(top_breakdown)
    recommendation = _build_recommendation(profile, top_breakdown)
    profile_text = (
        f"Industry: {profile.get('industry')}, "
        f"Business model: {profile.get('business_model')}, "
        f"Presence: {profile.get('presence_mode')}, "
        f"Customer type: {profile.get('customer_type')}, "
        f"Risk appetite: {profile.get('risk_profile')}, "
        f"Capital: {profile.get('capital')}"
    )

    prompt = (
        "You are an explainable AI assistant for strategy consultants. "
        "Describe in 4 short sentences why certain markets scored highest. "
        "Be plain-language, cite what each metric means, mention how the weights interact "
        "across growth, digital readiness, scale, consumer purchasing power, inflation stability, "
        "governance risk, and operating cost, "
        "and reference the strongest metric for each highlighted country. "
        f"Top markets: {leaders_text}. {metrics_section} {breakdown_section} "
        f"Business profile: {profile_text}. {('Recommendation: ' + recommendation) if recommendation else ''}"
        "Keep the tone concise and educational."
    )

    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"inputs": prompt, "parameters": {"max_new_tokens": 150, "temperature": 0.3}}

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        return _fallback_explanation(weights, leaders, metric_breakdown)

    text = ""
    if isinstance(data, list) and data:
        text = (data[0] or {}).get("generated_text", "")
    elif isinstance(data, dict):
        text = data.get("generated_text") or data.get("summary_text") or ""

    final_text = text.strip() or _fallback_explanation(weights, leaders, metric_breakdown)
    if recommendation and recommendation not in final_text:
        final_text = f"{final_text}\nRecommendation: {recommendation}"
    return final_text
