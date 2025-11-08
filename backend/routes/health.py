from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint for uptime monitoring."""
    return jsonify({"status": "ok", "message": "ConsultAI backend running"})
