import os
from typing import Any, Dict, Tuple

import requests
from dotenv import load_dotenv
from flask import Blueprint, jsonify, request

MODEL = "google/flan-t5-base"
API_URL = f"https://api-inference.huggingface.co/models/{MODEL}"

load_dotenv()

gpt_agent_bp = Blueprint("gpt_agent", __name__)


def _build_prompt(question: str, context: Dict[str, Any]) -> str:
    return (
        "You are a senior management consultant. "
        "Answer clearly in 3 bullet points using professional, factual tone. "
        f"Question: {question}\nContext: {context}"
    )


def _parse_generated_text(payload: Any) -> str:
    if isinstance(payload, list) and payload:
        first = payload[0] or {}
        return (first.get("generated_text") or first.get("summary_text") or "").strip()
    if isinstance(payload, dict):
        return (payload.get("generated_text") or payload.get("summary_text") or "").strip()
    return ""


def _format_context(context: Dict[str, Any]) -> str:
    if not context:
        return "key assumptions are not yet documented."
    fragments = []
    for key, value in context.items():
        label = key.replace("_", " ").strip().capitalize()
        if isinstance(value, dict):
            detail = ", ".join(f"{k}: {v}" for k, v in value.items())
        elif isinstance(value, (list, tuple, set)):
            detail = ", ".join(str(item) for item in value)
        else:
            detail = str(value)
        fragments.append(f"{label}: {detail}")
    return "; ".join(fragments)


def _fallback_answer(question: str, context: Dict[str, Any]) -> str:
    context_text = _format_context(context)
    clarified_question = question.strip() or "the strategic question"
    bullets = [
        f"Clarify the intent behind “{clarified_question}”, align on time horizon, and define measurable success metrics before debating options.",
        f"Review available evidence ({context_text}) to size the opportunity, test sensitivities, and surface the 2–3 critical assumptions that could change the answer.",
        "Translate the findings into a sequenced action plan covering deeper analysis, stakeholder alignment, and next executive touchpoints over the next 2–4 weeks.",
    ]
    return "\n".join(f"• {line}" for line in bullets)


def _call_hf_api(prompt: str, api_key: str) -> str:
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"inputs": prompt, "parameters": {"max_new_tokens": 120}}
    response = requests.post(API_URL, headers=headers, json=payload, timeout=30)

    if response.status_code == 503:
        raise RuntimeError("Model is warming up, please retry.")

    try:
        response_json = response.json()
    except ValueError as exc:
        raise RuntimeError("Invalid response from Hugging Face API.") from exc

    if isinstance(response_json, dict) and response_json.get("error"):
        raise RuntimeError(response_json["error"])

    answer = _parse_generated_text(response_json)
    if not answer:
        raise RuntimeError("No generated text received from model.")
    return answer


def _generate_answer(question: str, context: Dict[str, Any]) -> Tuple[str, str, str | None]:
    """Return (answer, source, warning)."""
    api_key = os.getenv("HF_API_KEY")
    prompt = _build_prompt(question, context)

    if api_key:
        try:
            return _call_hf_api(prompt, api_key), "huggingface", None
        except (requests.RequestException, RuntimeError) as exc:
            warning = f"Hugging Face response unavailable: {exc}"
            return _fallback_answer(question, context), "fallback", warning

    warning = "HF API key not configured; using heuristic advisor response."
    return _fallback_answer(question, context), "fallback", warning


@gpt_agent_bp.route("/api/advisor", methods=["POST"])
def advisor():
    data = request.get_json(silent=True) or {}
    question = data.get("question")
    context = data.get("context", {})

    if not question:
        return jsonify({"status": "error", "message": "Field 'question' is required."}), 400

    answer, source, warning = _generate_answer(question, context)

    payload = {
        "status": "success",
        "data": {"answer": answer, "source": source},
        "message": "Consulting recommendation generated.",
    }
    if warning:
        payload["warning"] = warning

    return jsonify(payload), 200
