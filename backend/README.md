# ConsultAI Backend

Simple Flask backend that exposes health and market scoring endpoints for ConsultAI.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# add your HF token to backend/.env or export HF_API_KEY
```

## Run

```bash
export FLASK_APP=app.py
flask run
```

## Endpoints

- Health check: `GET /api/health`
- Market entry scoring: `POST /api/market-entry`
- Business insights: `POST /api/business-insights` (multipart form upload)
- GPT advisor (Hugging Face router, default Llama 3.3 70B Instruct): `POST /api/advisor`

### Sample request

```bash
curl -X POST http://127.0.0.1:5000/api/market-entry \
  -H "Content-Type: application/json" \
  -d '{"company_name":"EcoStore","industry":"Retail","target_regions":["Asia"],"weights":{"growth":0.4,"risk":0.2,"digital":0.3,"ease_of_business":0.1},"time_horizon":"2024-2030"}'
```

```bash
curl -X POST http://127.0.0.1:5000/api/business-insights \
  -F "kpi_file=@data/company_kpi.csv" \
  -F "include_forecast=true" \
  -F "anomaly_threshold=0.2"
```

```bash
curl -X POST http://127.0.0.1:5000/api/advisor \
  -H "Content-Type: application/json" \
  -d '{"question":"Which region should I expand next year?","context":{"module":"market_entry"}}'
```

### Customising the advisor model

Set `HF_MODEL_ID` in your environment or `.env` file to any Hugging Face router model you have access to (for example, `meta-llama/Llama-3.3-70B-Instruct:cerebras`). Remember to keep `HF_API_KEY` configured with a token that has permission to use the chosen model.

- The backend talks to the OpenAI-compatible endpoint at `https://router.huggingface.co/v1/chat/completions`. If you are using a private deployment, override `HF_API_BASE_URL`.
- Test your token/model pair quickly with:

  ```bash
  curl -X POST \
    -H "Authorization: Bearer $HF_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"model":"'"$HF_MODEL_ID"'","messages":[{"role":"user","content":"Ping"}]}' \
    "https://router.huggingface.co/v1/chat/completions"
  ```
