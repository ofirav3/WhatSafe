import json
import os
import sys
from typing import List

# Ensure project root is on sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from whatsafe_detector import (
    parse_whatsapp_lines,
    compute_basic_stats,
    score_boycott_risk,
    analyze_whatsapp_text_export,
)


def sample_lines() -> List[str]:
    return [
        "01/01/25, 12:00 - Dan: היי",
        "01/01/25, 12:01 - Maya: צריך חרם?",
        "01/01/25, 12:02 - Ofir: מדברים על זה",
        "01/01/25, 12:03 - Maya: כן, אולי לא להזמין אותו",
    ]


def test_parse_whatsapp_lines_basic():
    msgs = parse_whatsapp_lines(sample_lines())
    assert len(msgs) == 4
    assert msgs[0].sender == "Dan"
    assert "חרם" in msgs[1].text


def test_stats_and_scoring():
    msgs = parse_whatsapp_lines(sample_lines())
    stats = compute_basic_stats(msgs)
    assert set(stats.keys()) == {"Dan", "Maya", "Ofir"}
    signals = score_boycott_risk(msgs, stats)
    assert 0.0 <= signals["boycott_risk"] <= 1.0
    assert signals["total_messages"] == float(len(msgs))


def test_full_analysis_helper():
    content = "\n".join(sample_lines())
    result = analyze_whatsapp_text_export(content)
    assert result["label"] in {
        "No clear boycott signals detected",
        "Low boycott risk",
        "Medium boycott risk",
        "High boycott risk - possible boycott in this group",
    }
    assert "risk_signals" in result and "per_sender_stats" in result


def test_detection_service_endpoint():
    from detection_service import app
    from starlette.testclient import TestClient

    client = TestClient(app)
    payload = {"content": "\n".join(sample_lines())}
    r = client.post("/api/analyze-text", json=payload)
    assert r.status_code == 200
    data = r.json()
    # Either a valid result or structured error from our handler
    assert isinstance(data, dict)
    if "error" in data:
        # Should include detail
        assert "detail" in data
    else:
        assert "risk_signals" in data and "per_sender_stats" in data


