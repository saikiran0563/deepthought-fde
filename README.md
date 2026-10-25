# Callflow — DeepThought FDE

A cold-call companion that guides a representative through eight conversation stages, captures the prospect's exact words, records outcomes and follow-ups, and keeps call history. An optional Gemini-powered coach gives contextual suggestions for the current stage.

## Features

- Eight-stage call guide: Opening, Purpose, Permission, Their business, Their need, Objection, Next step, and Close.
- Start a call, move between stages, and end at any stage.
- Capture the prospect's exact words separately from internal notes.
- Record outcome and agreed next step.
- Browse call history and reopen saved call summaries.
- AI coaching endpoint with input validation and friendly handling for missing keys, quota limits, and upstream errors.
- SQLAlchemy database configuration: SQLite is the local fallback; PostgreSQL/Supabase is supported through `DATABASE_URL`.
- Backend tests and a frontend production-build check in GitHub Actions.

## Technology

- Frontend: React, Vite, Lucide
- Backend: Flask, Flask-CORS, Flask-SQLAlchemy
- Database: SQLite for local fallback; PostgreSQL on Supabase
- AI: Gemini API called by Flask only (the API key is never sent to the browser)
- Deployment configuration: Render (backend) and Vercel (frontend)

## Project layout

```text
deepthought-fde/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── coach.py
│   │   ├── config.py
│   │   ├── models.py
│   │   └── routes.py
│   ├── tests/
│   ├── .env.example
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── src/
│   ├── .env.example
│   ├── package.json
│   └── vite.config.js
├── .github/workflows/ci.yml
└── render.yaml
```

## Run locally (Windows PowerShell)

### 1. Backend

From the repository root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

Update the values in `backend/.env`:

- `DATABASE_URL`: leave unset/empty to use local SQLite, or use your Supabase PostgreSQL session-pooler connection string (port 5432). Use the exact host and username shown by your Supabase project's Connect panel; URL-encode special characters in the password.
- `GEMINI_API_KEY`: optional for the app to start, required to use AI coaching. Create a key in [Google AI Studio](https://aistudio.google.com/apikey).
- `GEMINI_MODEL`: defaults to `gemini-3.8-flash`; change this if the model isn't enabled for your API key.
- `CORS_ORIGINS`: for local development, use `http://127.0.0.1:5173,http://localhost:5173`.

Start Flask:

```powershell
python run.py
```

Health check: http://127.0.0.1:5000/api/health

### 2. Frontend

Open a second terminal from the repository root:

```powershell
cd frontend
npm ci
Copy-Item .env.example .env.local
npm run dev
```

Open the local URL printed by Vite, typically http://127.0.0.1:5173.

Set `VITE_API_BASE_URL=http://127.0.0.1:5000/api` in `frontend/.env.local` for local development.

### 3. Tests and production build

Backend tests:

```powershell
cd backend
python -m pytest -v
```

Frontend production build:

```powershell
cd frontend
npm run build
```

The AI endpoint tests mock the Gemini HTTP response; they do not use API credits.

## API overview

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Basic health check |
| GET | `/api/stages` | Return the eight call stages |
| GET | `/api/stages/<stage_id>` | Return one stage's guide |
| GET | `/api/outcomes` | Return available call outcomes |
| POST | `/api/calls` | Start a call |
| GET | `/api/calls` | List call history |
| GET | `/api/calls/<call_id>` | Get a call |
| PATCH | `/api/calls/<call_id>` | Save notes, outcome, next step, or stage |
| POST | `/api/calls/<call_id>/end` | End a call and save its final state |
| POST | `/api/coach` | Get stage-specific AI coaching |

The coaching request accepts `stage_id`, `prospect_words`, and `notes`. The response includes `stage_name` and generated `coaching`.

## Deploy

### Backend on Render

This repository includes `render.yaml`. In Render, create a Blueprint from this GitHub repository and configure the secret environment variables when prompted:

- `DATABASE_URL`: Supabase PostgreSQL session-pooler URL with SSL required.
- `GEMINI_API_KEY`: Google AI Studio API key.
- `CORS_ORIGINS`: exact deployed Vercel origin (for example, `https://your-app.vercel.app`); include other origins only when needed.

The service uses `backend` as its root directory, starts with Gunicorn, and checks `/api/health`. The free Render instance may spin down after inactivity; the first request after idle can take longer.

### Frontend on Vercel

Import the GitHub repository in Vercel and set the Root Directory to `frontend`. Vercel should detect Vite automatically. Add this environment variable in Vercel's project settings:

- `VITE_API_BASE_URL=https://YOUR-RENDER-SERVICE.onrender.com/api`

Redeploy after setting or changing the variable. Add the actual Vercel origin to the Render `CORS_ORIGINS` setting, then redeploy/restart the backend.

## Security and privacy

- Never commit `.env`, `.env.local`, database credentials, or the Gemini API key.
- Only the Flask backend should read `GEMINI_API_KEY`; do not create a `VITE_GEMINI_API_KEY` variable.
- AI coaching sends the entered prospect words and notes to the configured AI provider. Use fictional/sample data for testing and avoid sensitive or confidential content.
- The demo is intended as a small assignment prototype. It does not currently include user authentication or per-user call isolation; do not store real prospect records in a public deployment without adding access controls and reviewing privacy requirements.
- Free-tier eligibility, limits, availability, and provider policies can change. Verify each provider's current terms before relying on a free API quota.

## Assignment checklist

- [x] Eight-stage call guide
- [x] Calls can end at any stage
- [x] Capture prospect's exact words
- [x] Track call outcome and next step
- [x] Call history
- [x] Flask health endpoint and call-management API
- [x] Optional Gemini coach endpoint
- [x] GitHub Actions checks
- [ ] Configure and verify hosted Render service
- [ ] Configure and verify Vercel frontend
- [ ] Test AI coaching using the deployed secret key
- [ ] Record the required demo video and submit the hosted URLs
