## Whatsafe – simple architecture

### Overview
- Two FastAPI microservices:
  - Detection Service (port 8001): exposes POST /api/analyze-text
  - UI Service (port 8002): serves HTML upload form and calls detection
- Core domain logic in `whatsafe_detector.py` used by Detection Service.

### Data flow
1. Browser requests UI (GET /) → UI returns HTML form.
2. User uploads WhatsApp `.txt` file (POST /analyze on UI).
3. UI reads file bytes, decodes text, calls Detection Service:
   - POST http://localhost:8001/api/analyze-text { content: "..." }
4. Detection Service executes domain logic:
   - Parse messages → compute stats → score → classify → detect target.
5. Detection returns JSON result to UI.
6. UI renders human-readable HTML with risk, signals, per-sender stats, target.

### Modules
- `whatsafe_detector.py` (pure logic):
  - parse_whatsapp_lines, compute_basic_stats, score_boycott_risk,
    classify_boycott, detect_potential_target, analyze_* helpers.
- `detection_service.py` (FastAPI):
  - POST /api/analyze-text accepts JSON, returns analysis JSON.
- `ui_service.py` (FastAPI):
  - GET / renders form; POST /analyze forwards to detection and renders HTML.

### Operational concerns
- Run detection on 8001; run UI on 8002 to avoid conflicts.
- Use venv to ensure consistent Python deps.
- Log server-side exceptions; return minimal error JSON from detection.
- UI shows friendly error page if detection is unavailable or returns error.

### Non-goals
- Advanced NLP/ML; persistent storage; auth; multi-tenant routing.


