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


# The project now uses a NestJS server as the primary API.
# Python API endpoint tests have been removed.


