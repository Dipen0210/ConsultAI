import os
import sys
from pathlib import Path

from flask import Flask
from flask_cors import CORS

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from backend.routes.business_insights import business_insights_bp
    from backend.routes.gpt_agent import gpt_agent_bp
    from backend.routes.health import health_bp
    from backend.routes.market_entry import market_entry_bp
except ImportError:  # pragma: no cover - fallback when running as script
    from routes.business_insights import business_insights_bp
    from routes.gpt_agent import gpt_agent_bp
    from routes.health import health_bp
    from routes.market_entry import market_entry_bp


def create_app() -> Flask:
    """Application factory for the ConsultAI backend."""
    app = Flask(__name__)

    default_origins = {"http://localhost:5173", "http://127.0.0.1:5173"}
    extra_origins = os.getenv("CORS_ALLOW_ORIGINS")
    if extra_origins:
        default_origins.update(
            origin.strip() for origin in extra_origins.split(",") if origin.strip()
        )

    CORS(
        app,
        origins=list(default_origins),
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Accept"],
    )

    app.register_blueprint(health_bp)
    app.register_blueprint(market_entry_bp)
    app.register_blueprint(business_insights_bp)
    app.register_blueprint(gpt_agent_bp)
    return app


app = create_app()


if __name__ == "__main__":
    app.run()
