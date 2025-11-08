# consultAI

ConsultAI is a lightweight consulting co-pilot: upload KPI snapshots, simulate market entry decisions, or ask the AI advisor for quick strategy pointers. A Flask backend handles the scoring/ML logic while a React (Vite + Tailwind) frontend gives consultants a ready-to-share interface.

## What’s inside

- **Market Entry Lab** – Takes weighted KPIs (GDP, inflation, digital readiness, etc.) and recommends expansion markets with explainable metrics.
- **Business Insights Studio** – Accepts CSV KPI dumps, clusters segments, forecasts revenue, and spits out alerts plus PDF-ready visuals.
- **AI Advisor** – Chat endpoint (Hugging Face powered or deterministic fallback) that returns crisp consulting-style bullets.

## Structure

- `backend/` – Flask API exposing health, market-entry scoring, business-insights, and AI advisor endpoints.
- `frontend/` – React SPA that consumes the API to run analyses and chat with the advisor.

## Local Development

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=app.py
flask run  # http://127.0.0.1:5000
```

### Frontend
```bash
cd frontend
npm install
npm run dev  # http://localhost:5173
```

Ensure the backend is running so the frontend proxy (`/api`) resolves correctly.

## Environment

- Set `HF_API_KEY` before launching the backend if you want the AI advisor to hit Hugging Face.
- `.gitignore` excludes `__pycache__/`, `node_modules/`, build output, venvs, and `.env` files.

## Production Build

```bash
cd frontend
npm run build
```
Serve `frontend/dist` behind your preferred web server and proxy `/api/` to the Flask backend.
