# consultAI

ConsultAI is a lightweight consulting co-pilot: upload KPI snapshots, simulate market entry decisions, or ask the AI advisor for quick strategy pointers. A Flask backend handles the scoring/ML logic while a React (Vite + Tailwind) frontend gives consultants a ready-to-share interface.

## What we’re doing (and why)

### Market Entry Lab

- **Data sources**: the backend blends macro indicators (GDP growth, inflation stability, internet penetration, population scale, purchasing power, corruption, operating-cost indices) pulled from curated CSVs.
- **Why these metrics?** They cover momentum (GDP), risk (inflation, corruption), readiness (internet), scale (population), and affordability (purchasing power & cost indexes) – the typical top-down filters a consulting team applies before deep dives.
- **How scoring works**: the user describes their profile (industry, business model, presence mode, risk appetite, customer type, capital). We translate that profile into metric weights, normalize country scores, invert “bad” metrics (e.g., high inflation is penalized), and produce a weighted score for 120+ economies.
- **Explainable AI**: besides the ranked list, we surface the actual weights used, the raw metric contributions per country, and an explainable narrative. If a Hugging Face key is provided, the narrative is authored by `google/flan-t5-base`; otherwise, we fall back to a deterministic explanation so users always know *why* a market surfaced.
- **Output**: the frontend renders MarketResultCards, metric breakdown tables, and a “How this decision was made” block so the shortlist is board-ready.

### Business Insights Studio

- **Input**: users upload a CSV of KPIs (revenue, profit, churn, region, product/category/segment labels, etc.).
- **Processing steps**:
  1. Clean and normalize the CSV using pandas/scikit-learn.
  2. Build scatter/line/bar data for clusters, revenue trend, segment/category/region breakdowns, top products, and forecasts.
  3. Detect anomalies/alerts (e.g., segments with discount pressure, low margin, negative profit trends) and return actionable snippets.
  4. Summarize KPIs (total revenue, average margin/churn, number of companies) and feed them to the optional HuggingFace model for a consultant-style recommendation.
- **Outputs**: the frontend renders KPI cards, Recharts visualizations, alert lists, “key improvement area” callouts, and a narrative section. Users can export the entire section to PDF via html2canvas + jsPDF to drop into decks or share with clients.

### AI Advisor

- **Endpoint**: `/api/advisor` takes a natural-language question plus optional context and either calls Hugging Face (`HF_API_KEY` required) or falls back to a deterministic 3-bullet answer if the model isn’t reachable.
- **Use case**: quick storyline drafts (“What should we highlight about LATAM expansion?”) without leaving the app.

## Structure

- `backend/` – Flask API exposing health, market-entry scoring, business-insights, and AI advisor endpoints.
- `frontend/` – React SPA that consumes the API to run analyses and chat with the advisor.
