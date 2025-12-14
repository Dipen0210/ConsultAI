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

## Visuals

<img width="1470" height="737" alt="Screenshot 2025-12-14 at 3 41 18 PM" src="https://github.com/user-attachments/assets/6dd672ef-5310-4921-a76f-8a0feed92af4" />

<img width="1469" height="814" alt="Screenshot 2025-12-14 at 3 40 56 PM" src="https://github.com/user-attachments/assets/afe784c2-baa2-4fe4-bddd-9547a2e9a000" />

<img width="1213" height="407" alt="Screenshot 2025-12-14 at 3 40 35 PM" src="https://github.com/user-attachments/assets/44d041d5-82e7-43e5-b828-e0ed3b1f7c77" />

<img width="1470" height="637" alt="Screenshot 2025-12-14 at 3 40 28 PM" src="https://github.com/user-attachments/assets/71b3a90f-dbaf-44f6-ba04-367dcfedfcc2" />

<img width="1465" height="802" alt="Screenshot 2025-12-14 at 3 40 15 PM" src="https://github.com/user-attachments/assets/3e6fdc68-f08f-4cce-97bc-1aa1e7904378" />

<img width="1295" height="549" alt="Screenshot 2025-12-14 at 3 39 57 PM" src="https://github.com/user-attachments/assets/ecccacd0-575e-4876-bc12-d3a91b24082b" />

<img width="1110" height="649" alt="Screenshot 2025-12-14 at 3 39 41 PM" src="https://github.com/user-attachments/assets/e8a23cef-86c5-4b7c-8171-0191101a3b15" />

<img width="1108" height="670" alt="Screenshot 2025-12-14 at 3 39 26 PM" src="https://github.com/user-attachments/assets/983a652f-a018-43c9-b71a-affb5a380f44" />

<img width="1117" height="787" alt="Screenshot 2025-12-14 at 3 39 11 PM" src="https://github.com/user-attachments/assets/7681fda7-6ab4-4ae7-ae73-8b5f4296b836" />

<img width="1469" height="825" alt="Screenshot 2025-12-14 at 3 38 34 PM" src="https://github.com/user-attachments/assets/a048a5b5-31a7-495c-ae6b-d746be035412" />

<img width="1470" height="759" alt="Screenshot 2025-12-14 at 3 38 17 PM" src="https://github.com/user-attachments/assets/f4677ce6-61a3-4e94-9004-2cc83d815505" />
