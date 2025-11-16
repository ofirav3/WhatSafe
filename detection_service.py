"""
detection_service.py

FastAPI microservice for Whatsafe:
- Exposes an HTTP API for analyzing WhatsApp text.
- Uses the domain logic from whatsafe_detector.py.
"""

from typing import Dict, Any  # Type hints for clarity
import logging
import traceback
import os  # For environment variables
import json  # For parsing JSON responses

from fastapi import FastAPI, HTTPException  # FastAPI web framework
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel  # For request body validation
from openai import OpenAI  # OpenAI API client
from dotenv import load_dotenv  # Load environment variables from .env file

# Load environment variables from .env file if it exists
load_dotenv()

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

# CORS for local frontend dev (Vite on 5173 and legacy UI on 8002)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("detection_service")

# Initialize OpenAI client (API key from environment variable)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
else:
    openai_client = None
    logger.warning("OPENAI_API_KEY not found in environment variables. OpenAI features will be disabled.")


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


def analyze_with_openai(content: str) -> Dict[str, Any]:
    """
    Analyze WhatsApp text using OpenAI's LLM to detect boycott activity.

    This function uses OpenAI's API to perform a more sophisticated analysis
    than the keyword-based approach, understanding context and nuance.

    Args:
        content: The full WhatsApp export as a single text string.

    Returns:
        A dictionary with OpenAI analysis results including:
        - boycott_detected: boolean indicating if boycott activity was detected
        - confidence: confidence score (0-1)
        - reasoning: explanation from the AI
        - risk_level: "none", "low", "medium", or "high"
        - boycott_details: detailed findings
        - potential_targets: list of potential boycott targets mentioned
    """
    if not openai_client:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
        )

    # Create a prompt for the OpenAI model
    system_prompt = """You are an expert analyst specializing in detecting boycott activity in group chat conversations. 
Your task is to analyze WhatsApp group chat exports and identify any boycott-related behavior.

A boycott may include:
- Explicit calls to stop talking to someone
- Instructions to ignore or exclude specific individuals
- Coordinated efforts to isolate someone from the group
- References to "boycott", "blocking", "excluding", or similar terms
- Mentions of not inviting someone to events or activities
- Group decisions to ostracize a member

Analyze the conversation and provide:
1. Whether boycott activity is detected (true/false)
2. Confidence level (0.0 to 1.0)
3. Risk level: "none", "low", "medium", or "high"
4. Clear reasoning for your assessment
5. Specific details about what boycott behavior was found
6. Names or identifiers of potential targets mentioned

Respond in JSON format with these keys: boycott_detected, confidence, risk_level, reasoning, boycott_details, potential_targets."""

    user_prompt = f"""Analyze the following WhatsApp group chat export for boycott activity:

{content}

Provide a JSON response with your analysis."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Using gpt-4o-mini for cost efficiency, can be changed to gpt-4 or gpt-4-turbo
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,  # Lower temperature for more consistent analysis
        )

        # Parse the JSON response
        ai_analysis = json.loads(response.choices[0].message.content)

        # Structure the response similar to the existing analysis format
        result = {
            "source": "openai-ai-analysis",
            "label": ai_analysis.get("risk_level", "unknown").upper() + " risk",
            "boycott_detected": ai_analysis.get("boycott_detected", False),
            "confidence": ai_analysis.get("confidence", 0.0),
            "risk_level": ai_analysis.get("risk_level", "none"),
            "reasoning": ai_analysis.get("reasoning", ""),
            "boycott_details": ai_analysis.get("boycott_details", ""),
            "potential_targets": ai_analysis.get("potential_targets", []),
            "model_used": "gpt-4o-mini",
        }

        return result

    except Exception as exc:
        logger.error("Error calling OpenAI API: %s", exc)
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error calling OpenAI API: {str(exc)}"
        )


@app.post("/api/analyze-text-ai")
def analyze_text_ai(request: AnalyzeRequest) -> Dict[str, Any]:
    """
    Analyze the given WhatsApp text using OpenAI's LLM to detect boycott activity.

    This endpoint uses AI/LLM analysis for more sophisticated detection than
    the keyword-based approach. It understands context and nuance.

    Requires OPENAI_API_KEY environment variable to be set.

    Example request:
        POST /api/analyze-text-ai
        {
            "content": "01/01/25, 12:00 - John: היי..."
        }

    Returns:
        JSON response with AI analysis including:
        - boycott_detected: boolean
        - confidence: float (0-1)
        - risk_level: "none" | "low" | "medium" | "high"
        - reasoning: string explanation
        - boycott_details: string with details
        - potential_targets: list of potential targets
    """
    try:
        result = analyze_with_openai(request.content)
        return result
    except HTTPException:
        # Re-raise HTTP exceptions (like missing API key)
        raise
    except Exception as exc:
        logger.error("Unhandled error in analyze_text_ai: %s", exc)
        traceback.print_exc()
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
