# AI-Powered Corporate Financial Analysis Platform

Excel is the data-entry interface; the website is the review, calculation, comparison and decision-support environment.
**Upload → Review → Confirm → Analyze → Interpret → Report.** Nothing is approved automatically.

## Run

```bash
pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..
python -m uvicorn app.main:app --app-dir backend --port 8000
```
Open http://localhost:8000. Data is stored in `backend/data/platform.db` (SQLite). For PostgreSQL set
`DATABASE_URL=postgresql+psycopg://user:pass@host/db` (and `pip install psycopg[binary]`).

Optional: set `ANTHROPIC_API_KEY` to let the AI Analyst chat answer in natural language (Claude Opus 5.5).
Without it, the chat falls back to the deterministic findings. The AI only explains; it never does the maths.

Tests: `cd backend && python -m pytest tests -q` (62 tests).

## Publish online with a real link (Render)

1. Push this folder to a GitHub repository.
2. On https://render.com sign in with GitHub, then **New → Blueprint** and pick the repository.
   Render reads `render.yaml`: one web service (Docker) and one PostgreSQL database.
3. When asked for `FAP_PASSWORD`, type the password people will use to sign in. `FAP_SECRET` is generated for you.
4. Wait for the build (about 5–10 minutes). Your link is `https://financial-analysis-platform-XXXX.onrender.com`.

Notes: on Render's free plan the service sleeps after 15 minutes without visits (the next visit takes ~1 minute to wake),
and the free database has a time limit set by Render — upgrade the database plan to keep data long-term.
Locally, without `FAP_PASSWORD`, the platform stays open as before.

## Architecture

| Layer | Location | Notes |
|---|---|---|
| Methodology database | `backend/app/methodology.py`, `docs/METHODOLOGY.md` | Generated from the same registry the engine executes |
| Excel template & sample | `backend/app/excel_template.py` | 7 sheets, EN/AR instructions, dropdowns, 5-year sample |
| Ingestion & validation | `backend/app/ingest.py` | Long or wide layout; duplicates, types, years, currency, missing values/openings |
| Classification engine | `backend/app/classify.py`, `taxonomy.py` | Explainable EN/AR rules, confidence, questions for ambiguous accounts |
| Assumption engine | `backend/app/assumptions.py` | 14 explicit assumptions with alternatives and simulated impact |
| Calculation engine | `backend/app/engine/` | Decimal arithmetic; aggregates, 50+ ratios, trends, sources & uses, forecasting |
| AI analyst | `backend/app/observations.py`, `llm.py` | 3-level review; finding / data / reasoning / hypothesis / impact / confidence / action |
| Forecasting & planning | `backend/app/engine/forecast.py`, `forecasting.py`, `frontend/src/Forecasting.tsx` | Forecasted position (staged hierarchy, Lecture 5 / Q4), % of sales & AFN (Lecture 6), break-even & DOL (Lecture 8), cash budget (Lecture 7) |
| Reports | `backend/app/reports.py` | Excel + PDF from the same data as the dashboard |
| API | `backend/app/main.py` | FastAPI; roles via `X-User-Id` header; audit log on every decision |
| Dashboard | `frontend/src/` | React + TypeScript + Recharts; English/Arabic with RTL |

**Data governance:** `raw_items` (original Excel rows, never modified) → `account_values` (parsed values, linked to the raw row)
→ `classifications` (suggested and approved categories kept side by side). Every result has a status:
verified / approved assumption / provisional / needs info / invalid, and drills down to the original accounts.

## Course methodology (academic default)
ROI = EBIT / TA · ROE = EBT / Equity · ROBF = (ROI − I/BF) × BF/OE, so ROE = ROI + ROBF · 360-day year · closing balances ·
ACP = AR×360/credit sales (all sales assumed credit if not given) · ASP = Inv×360/COGS · liquidity of inventory = ACP + ASP ·
best liquidity measure rule · EVA = NP − (I + PS div + CS div + 10% × R/E) · Sources & Uses with golden-rule and internal/external split.
Professional alternatives are separate, labelled and configurable (see `docs/METHODOLOGY.md`).

## Known limitations
- Online access is protected by one shared password (`FAP_PASSWORD`). Inside the platform, people pick their role from a list; there are no individual user accounts yet.
- Benchmark presets are course teaching examples or generic rules of thumb, not real industry data; enter your own.
- PDF export is in English only. The UI supports Arabic.
- The Q4 handwritten solution's EVA "after" uses 179 (the N/P balance) as net profit and gets −79. The platform uses the forecast net profit (≈138), which gives ≈ −120. Since "before" is ≈ −109, EVA actually falls, so the solution's conclusion ("EVA increases → accept") reverses. Check this one with the instructor.
