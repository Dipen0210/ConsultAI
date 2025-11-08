# ConsultAI Frontend

React + Vite frontend that connects to the ConsultAI Flask backend.

## Setup

```bash
cd frontend
npm install
# optional: define API base URL for deployed backend
# echo "VITE_API_BASE_URL=https://your-backend.example.com/api" > .env.local
```

## Development

```bash
npm run dev
```

Then open `http://localhost:5173`.

## Styling

- Tailwind CSS is configured via `tailwind.config.js` and `postcss.config.js`.
- Utility classes are available throughout the app; update or extend styles by editing `src/index.css`.

### Features

- Home page sanity message.
- Health check component that pings the Flask backend at `http://127.0.0.1:5000/api/health`.

Ensure the backend is running locally before starting the frontend. If the backend is unavailable, the HealthCheck component will display `Backend not reachable`.
