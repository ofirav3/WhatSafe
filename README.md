# WhatSafe – WhatsApp Boycott Risk Detector

WhatSafe is a small demo app that analyzes exported WhatsApp group chats and surfaces potential “boycott” signals. It’s built as two FastAPI microservices with a shared core of pure Python domain logic.

## What the app does
- Parses a WhatsApp group chat export (.txt)
- Computes per‑sender statistics (messages, characters, boycott‑related messages)
- Aggregates simple signals into a risk score and label
- Guesses a potential target name from boycott‑related messages
- **AI-powered analysis** using OpenAI's LLM for context-aware detection (optional)
- Renders a modern UI with KPIs, a styled table, and charts

## Service split (Why two services?)
- Detection Service (FastAPI, port 8001)
  - API: `POST /api/analyze-text` accepts `{ "content": "..." }`
    - Uses keyword-based detection (fast, explainable)
  - API: `POST /api/analyze-text-ai` accepts `{ "content": "..." }`
    - Uses OpenAI LLM for sophisticated context-aware analysis (requires OPENAI_API_KEY)
  - Runs the core domain logic and returns JSON
- UI Service (FastAPI, port 8002)
  - Serves a minimal landing page (upload form + instructions)
  - Calls the Detection Service and renders an HTML results page with charts
  - Optional AI analysis section with detailed reasoning and findings

Core logic is kept in `whatsafe_detector.py` (pure Python, easy to test). The services are thin shells around it.

## Quickstart (local)
Requirements: Python 3.9+ (tested on macOS), internet (for first‑time dependency install)

```bash
cd path/to/WhatSafe   # change to the project directory on your machine
python3 -m venv .venv
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r requirements.txt

# Optional: Set up OpenAI API key for AI-powered analysis
# Create a .env file in the project root with:
#   OPENAI_API_KEY=your-api-key-here
# Or export it as an environment variable:
#   export OPENAI_API_KEY=your-api-key-here
# Get your API key from: https://platform.openai.com/api-keys

# 1) Start the Detection Service (port 8001)
./.venv/bin/python detection_service.py

# 2) In another terminal, start the UI Service (port 8002)
./.venv/bin/python ui_service.py
```

Open the UI at `http://localhost:8002`, choose a WhatsApp `.txt` file (e.g., `whatsapp_group_sample.txt` in the repo), and click Analyze.

**For detailed setup instructions, see [SETUP_GUIDE.md](SETUP_GUIDE.md)**

### Exporting a WhatsApp group chat (without media)
1) Open WhatsApp and go to the group chat
2) Tap the group name to open Group Info
3) Export Chat (iOS) / More > Export chat (Android)
4) Select “Without Media”
5) Save the `.txt` to your computer, then upload it in the UI

### Optional: Call the API directly

**Keyword-based analysis (default):**
```bash
curl -X POST http://localhost:8001/api/analyze-text \
  -H "Content-Type: application/json" \
  -d '{"content":"01/01/25, 12:00 - John: היי"}'
```

**AI-powered analysis (requires OPENAI_API_KEY):**
```bash
curl -X POST http://localhost:8001/api/analyze-text-ai \
  -H "Content-Type: application/json" \
  -d '{"content":"01/01/25, 12:00 - John: היי"}'
```

The AI endpoint provides:
- Context-aware detection (not just keyword matching)
- Confidence scores and detailed reasoning
- Better identification of potential boycott targets
- More nuanced risk assessment

**Note:** The AI endpoint requires an OpenAI API key. Get one from [OpenAI](https://platform.openai.com/api-keys) and set it as an environment variable or in a `.env` file.

## Tests
```bash
cd path/to/WhatSafe
./.venv/bin/pytest -q
```

## Libraries used
- FastAPI – web framework for Detection and UI services
- Uvicorn – ASGI server
- httpx – UI service calls Detection service
- pydantic – request models
- python‑multipart – file uploads in UI
- pandas – formatting the per‑sender table
- Chart.js (CDN) – charts in the UI
- openai – OpenAI API client for AI-powered analysis
- python-dotenv – load environment variables from .env file

## Code overview
- `whatsafe_detector.py` (core logic)
  - `parse_whatsapp_lines` – parse lines into `Message` objects
  - `compute_basic_stats` – per‑sender counts (messages/chars/boycott)
  - `score_boycott_risk` – combines keyword ratio + concentration
  - `classify_boycott` – maps score to label
  - `detect_potential_target` – simple frequency heuristic over boycott messages
  - `analyze_whatsapp_text_export` – orchestration helper used by API
- `detection_service.py` (API)
  - `POST /api/analyze-text` – returns analysis JSON (keyword-based)
  - `POST /api/analyze-text-ai` – returns AI-powered analysis JSON (requires OPENAI_API_KEY)
  - Logs exceptions and returns a minimal error JSON if something goes wrong
- `ui_service.py` (UI)
  - Landing page with upload + instructions (animated background)
  - Results page: KPIs, pandas HTML table, Chart.js bar charts
  - Optional AI analysis section with detailed reasoning and findings
- `tests/test_whatsafe.py` – unit tests (parsing, stats, scoring, full analysis, API)

## What’s missing for production
This demo is intentionally simple. A production‑grade version would need:

- Security & privacy
  - End‑to‑end encryption constraint: WhatsApp chats are E2E encrypted. The app assumes the user exports a `.txt` from their device and uploads locally. For production:
    - Client‑side processing (browser/desktop app) to avoid server access to raw text
    - End‑to‑end encrypted upload with ephemeral keys and immediate data erasure
    - On‑device analysis (mobile or desktop) using a packaged engine
  - HTTPS/TLS, content security policies, and robust input validation
  - Strict data retention policy: short‑lived processing, no storage by default

- Observability & resilience
  - Structured logging, metrics, tracing
  - Rate limiting, request size caps, timeouts and circuit breakers
  - Health checks, readiness probes, autoscaling policies

- Architecture & deployment
  - Containerization (Docker) and IaC (Terraform) for consistent deployments
  - CI/CD (tests, linting, vulnerability scans, reproducible builds)
  - Config via env vars, secrets via a vault; version‑pinned dependencies

- UX & i18n
  - Better i18n/RTL support
  - Accessibility review, mobile layout polish

- Model/Logic
  - The current approach includes both keyword‑based detection (explainable and fast) and optional AI-powered analysis using OpenAI's LLM (context-aware and nuanced). For a robust product, consider additional ML/NLP models, better target extraction, and language packs. Add human‑in‑the‑loop review where appropriate.

## Notes worth reading
- The logic is deliberately transparent (regex + simple stats) so it’s easy to audit.
- Services are thin; most logic is in a single, testable module.
- The UI focuses on clear feedback and a modern look with minimal dependencies.

## License
Demo code for evaluation purposes.


