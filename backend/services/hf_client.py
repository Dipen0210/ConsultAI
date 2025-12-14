"""Helpers for interacting with the Hugging Face router across modules."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Tuple

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:  # fallback to default search path
    load_dotenv()

DEFAULT_MODEL = "meta-llama/Llama-3.3-70B-Instruct:cerebras"
MODEL = os.getenv("HF_MODEL_ID", DEFAULT_MODEL)
BASE_API_URL = os.getenv("HF_API_BASE_URL", "https://router.huggingface.co/v1").rstrip("/")
CHAT_COMPLETIONS_URL = f"{BASE_API_URL}/chat/completions"

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


def _call_chat_completion(
    api_key: str,
    system_prompt: str,
    user_prompt: str,
    *,
    max_tokens: int = 320,
    temperature: float = 0.2,
    top_p: float = 0.9,
) -> str:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
    }

    response = requests.post(CHAT_COMPLETIONS_URL, headers=headers, json=payload, timeout=45)
    if response.status_code == 503:
        raise RuntimeError("Model is warming up, please retry.")

    try:
        response_json = response.json()
    except ValueError as exc:
        raise RuntimeError("Invalid response from Hugging Face router.") from exc

    if isinstance(response_json, dict) and response_json.get("error"):
        error_message = (
            response_json["error"].get("message") if isinstance(response_json["error"], dict) else response_json["error"]
        )
        raise RuntimeError(error_message or "Unknown error returned from Hugging Face router.")

    choices = response_json.get("choices")
    if not choices:
        raise RuntimeError("No choices returned by Hugging Face router.")

    message = choices[0].get("message") or {}
    content = (message.get("content") or "").strip()
    if not content:
        raise RuntimeError("Empty response message from Hugging Face router.")
    return content


def run_chat_with_fallback(
    system_prompt: str,
    user_prompt: str,
    fallback_builder: Callable[[], str],
    *,
    max_tokens: int = 320,
    temperature: float = 0.2,
    top_p: float = 0.9,
) -> Tuple[str, str, str | None]:
    """Execute a chat completion and fall back to heuristic text if it fails."""
    api_key = os.getenv("HF_API_KEY")
    if not api_key:
        warning = "HF API key not configured; using heuristic response."
        return fallback_builder(), "fallback", warning

    try:
        result = _call_chat_completion(
            api_key,
            system_prompt,
            user_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )
        return result.strip(), "huggingface", None
    except (requests.RequestException, RuntimeError) as exc:
        warning = f"Hugging Face response unavailable: {exc}"
        return fallback_builder(), "fallback", warning


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
) -> Tuple[str, str, str | None]:
    """Produce a natural-language explanation of the scoring approach."""
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

    system_prompt = (
        "You are an explainable AI analyst for strategy teams. "
        "Produce a concise briefing that mixes narrative context with concrete metrics, "
        "so executives understand why each market surfaced. Always prefix each paragraph or bullet with “• ”."
    )
    user_prompt = (
        f"Top markets: {leaders_text}.\n"
        f"{metrics_section}\n"
        f"Highlights:\n{breakdown_section or 'No breakdown available.'}\n"
        f"Profile: {profile_text}.\n"
        "Structure the answer as:\n"
        "1. **Weighting context** – brief paragraph explaining how the weight mix steers the shortlist (prefix with “• ”).\n"
        "2. **Market callouts** – bullet list, one bullet per market, format "
        "'• **Country** – metric A, metric B, risk watchout'. Prioritize growth %, inflation %, digital reach %, population, or cost indices.\n"
        "3. **Executive takeaway** – 1–2 sentences on fit vs. capital/risk posture, also prefixed with “• ”.\n"
        "4. **Action points** – exactly two bullets with next diligence steps, each prefixed with “• ”.\n"
        f"{('Recommendation hint: ' + recommendation) if recommendation else ''}\n"
        "Keep the tone consultant-like, concise, and use bold text where shown."
    )

    text, source, warning = run_chat_with_fallback(
        system_prompt,
        user_prompt,
        lambda: _fallback_explanation(weights, leaders, metric_breakdown),
        max_tokens=360,
        temperature=0.3,
    )

    if recommendation and recommendation not in text:
        text = f"{text}\nRecommendation: {recommendation}"
    return text, source, warning


def _format_currency(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"${value:,.0f}"


def _format_percentage(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"


def _collect_dimension_highlights(dimension_insights: Dict[str, List[Dict[str, float]]]) -> List[str]:
    highlights = []
    segments = dimension_insights.get("segments") or []
    regions = dimension_insights.get("regions") or []
    categories = dimension_insights.get("categories") or []

    if segments:
        highlights.append(f"Top segment: {segments[0]['label']} ({_format_currency(segments[0]['revenue'])} revenue).")
    if regions:
        highlights.append(f"Top region: {regions[0]['label']} ({_format_currency(regions[0]['revenue'])} revenue).")
    if categories:
        highlights.append(
            f"Leading category: {categories[0]['label']} ({_format_currency(categories[0]['revenue'])} revenue)."
        )
    return highlights


def _fallback_business_summary(summary_parts: List[str] | None) -> str:
    if summary_parts:
        return " ".join(summary_parts)
    return (
        "Revenue and profit margin analysis completed. Higher-margin clusters show strong performance. "
        "Review any flagged discounts and low-margin items for corrective actions."
    )


def generate_business_insights_summary(
    kpi_summary: Dict[str, float],
    dimension_insights: Dict[str, List[Dict[str, float]]],
    alerts: List[Dict[str, object]],
    trend_data: List[Dict[str, float]],
    summary_parts: List[str] | None = None,
) -> Tuple[str, str, str | None]:
    """Return a consultant-style business insights narrative using the shared LLM."""
    highlights = _collect_dimension_highlights(dimension_insights)
    if alerts:
        highlights.append(f"{len(alerts)} alert(s) require attention across discounts, margin pressure, or churn.")
    if trend_data:
        last_point = trend_data[-1]
        highlights.append(
            f"Latest period ({last_point['period']}) revenue: {_format_currency(last_point['revenue'])}, "
            f"profit: {_format_currency(last_point['profit'])}."
        )

    kpi_lines = [
        f"Total revenue: {_format_currency(kpi_summary.get('total_revenue'))}",
        f"Avg profit margin: {_format_percentage(kpi_summary.get('avg_profit_margin'))}",
        f"Avg churn: {_format_percentage(kpi_summary.get('avg_churn'))}",
        f"Companies tracked: {kpi_summary.get('num_companies')}",
    ]

    system_prompt = (
        "You are a senior consulting analyst. Provide an optional one-sentence intro "
        "followed by exactly three recommendation bullets. Each bullet must begin with '• ' "
        "and a capitalized label such as 'Performance:', 'Risks:', or 'Next steps:'. "
        "Avoid markdown asterisks or numbered lists."
    )
    user_prompt = (
        "Key KPIs:\n"
        + "\n".join(f"- {line}" for line in kpi_lines)
        + "\nHighlights:\n"
        + "\n".join(f"- {line}" for line in (highlights or ["No standout segments captured."]))
        + "\nInstructions: Intro sentence optional. Then produce exactly three bullets (Performance, Risks, Next steps) "
        "prefixed with '• ' and ending with concrete recommendations."
    )

    return run_chat_with_fallback(
        system_prompt,
        user_prompt,
        lambda: _fallback_business_summary(summary_parts),
        max_tokens=280,
        temperature=0.25,
    )
