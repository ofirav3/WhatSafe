"""
detection_service.py

FastAPI microservice for Whatsafe:
- Exposes an HTTP API for analyzing WhatsApp text.
- Uses the domain logic from whatsafe_detector.py.
"""

from typing import Dict, Any  # Type hints for clarity
import logging
import traceback

from fastapi import FastAPI  # FastAPI web framework
from pydantic import BaseModel  # For request body validation

# Domain logic import with robust fallback to load from local file path explicitly
try:
    from whatsafe_detector import analyze_whatsapp_text_export  # Preferred import
    _analyze_text = analyze_whatsapp_text_export
except Exception:
    import os
    import importlib.util

    _dir = os.path.dirname(os.path.abspath(__file__))
    _module_path = os.path.join(_dir, "whatsafe_detector.py")

    spec = importlib.util.spec_from_file_location(
        "whatsafe_detector_local", _module_path
    )
    if spec is None or spec.loader is None:
        raise ImportError("Failed to locate whatsafe_detector.py")
    _wd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_wd)

    def _analyze_text(content: str) -> Dict[str, Any]:
        lines = content.splitlines()
        messages = _wd.parse_whatsapp_lines(lines)
        return _wd._run_full_analysis(messages, source="in-memory-text")


class AnalyzeRequest(BaseModel):
    """
    Request body model for the detection API.

    Attributes:
        content: the full WhatsApp export as a single text string.
    """
    content: str


# Create a FastAPI application instance for the detection microservice
app = FastAPI(
    title="Whatsafe Detection Service",
    description="Microservice that analyzes WhatsApp text for boycott risk.",
    version="1.0.0",
)

# Basic logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("detection_service")


@app.post("/api/analyze-text")
def analyze_text(request: AnalyzeRequest) -> Dict[str, Any]:
    """
    Analyze the given WhatsApp text and return the full analysis result.

    This endpoint is meant to be called by other services (e.g., the UI service)
    rather than directly by end-users.
    """
    try:
        # Run the analysis using the shared domain logic function
        result = _analyze_text(request.content)
        # FastAPI automatically converts this dict to JSON in the HTTP response
        return result
    except Exception as exc:
        # Log full traceback on server for debugging
        logger.error("Unhandled error in analyze_text: %s", exc)
        traceback.print_exc()
        # Return a minimal error payload
        return {"error": "internal_error", "detail": str(exc)}


if __name__ == "__main__":
    # Allow running this microservice with:
    #   python detection_service.py
    import uvicorn  # ASGI server for running FastAPI apps
    print("Starting Whatsafe Detection Service on http://0.0.0.0:8001 …")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,   # Detection service listens on port 8001
        # Note: 'reload' requires passing an import string (e.g., "detection_service:app").
        # When running as a script, keep reload disabled to avoid warnings.
        reload=False,
        log_level="info",
    )
