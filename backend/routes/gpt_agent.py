from typing import Any, Dict, Tuple

from dotenv import load_dotenv
from flask import Blueprint, jsonify, request

try:
    from backend.services.hf_client import run_chat_with_fallback
except ImportError:  # pragma: no cover - fallback when running as script
    from services.hf_client import run_chat_with_fallback

SYSTEM_PROMPT = (
    "You are a senior management consultant. Answer every question in exactly three "
    "clear bullet points using a professional and factual tone. Highlight assumptions "
    "only when material to the recommendation."
)

load_dotenv()

gpt_agent_bp = Blueprint("gpt_agent", __name__)


def _build_prompt(question: str, context: Dict[str, Any]) -> str:
    context_text = _format_context(context)
    cleaned_question = (question or "").strip() or "What should our next strategic move be?"
    return f"Question: {cleaned_question}\nContext: {context_text}"


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


def _generate_answer(question: str, context: Dict[str, Any]) -> Tuple[str, str, str | None]:
    """Return (answer, source, warning)."""
    prompt = _build_prompt(question, context)

    return run_chat_with_fallback(
        SYSTEM_PROMPT,
        prompt,
        lambda: _fallback_answer(question, context),
    )


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
