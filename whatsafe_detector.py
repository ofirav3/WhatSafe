"""
whatsafe_detector.py

Core domain logic for the Whatsafe project:
- Parsing WhatsApp text exports
- Computing basic statistics
- Scoring boycott risk
- Detecting a potential target
"""

from dataclasses import dataclass  # For simple data container classes
from typing import List, Dict, Tuple, Iterable, Optional  # Type hints for clarity
import re  # Regular expressions for parsing and text processing
from collections import Counter, defaultdict  # Helpful data structures for counting


# -----------------------------
# Data model
# -----------------------------

@dataclass
class Message:
    """
    Represents a single WhatsApp message.

    Attributes:
        timestamp: string representation of date + time (e.g. "01/01/2025 12:34").
        sender:    name or phone number of the sender as it appears in the export.
        text:      raw message content (possibly multi-line).
    """
    timestamp: str
    sender: str
    text: str


# -----------------------------
# Parsing layer
# -----------------------------

def parse_whatsapp_lines(lines: Iterable[str]) -> List[Message]:
    """
    Parse an iterable of lines from a WhatsApp text export into Message objects.

    This function supports:
    - The typical WhatsApp export format:
      "DD/MM/YY, HH:MM - Sender: message text"
    - Multi-line messages: lines that do not start with a timestamp are appended
      to the previous message.
    """
    # Support multiple common WhatsApp export formats.
    # 1) Android-style:
    #    "1/1/25, 12:34 - John Doe: Hello there"
    android_pattern = re.compile(
        r"^(\d{1,2}/\d{1,2}/\d{2,4}),\s+(\d{1,2}:\d{2})\s+-\s+(.*?):\s+(.*)$"
    )
    # 2) iOS-style (brackets, optional seconds):
    #    "[01/01/2025, 12:34:56] John Doe: Hello there"
    #    "[1/1/25, 12:34] John Doe: Hello there"
    ios_bracket_pattern = re.compile(
        r"^\[(\d{1,2}/\d{1,2}/\d{2,4}),\s+(\d{1,2}:\d{2}(?::\d{2})?)\]\s+(.*?):\s+(.*)$"
    )

    messages: List[Message] = []  # Collected parsed messages

    for raw_line in lines:
        # Strip whitespace and common BOM/bi-directional marks that sometimes
        # appear in WhatsApp exports (especially with RTL languages)
        line = raw_line.strip().lstrip("\ufeff\u200e\u200f")

        # Skip empty lines
        if not line:
            continue

        # Try known header patterns (iOS first is fine; order not critical)
        match = ios_bracket_pattern.match(line) or android_pattern.match(line)

        if match:
            # This line starts a new message
            date_str, time_str, sender, text = match.groups()
            timestamp = f"{date_str} {time_str}"

            messages.append(
                Message(timestamp=timestamp, sender=sender, text=text)
            )
        else:
            # If the line does not match, treat it as a continuation of the last message
            if messages:
                messages[-1].text += " " + line

    return messages


def parse_whatsapp_export(path: str) -> List[Message]:
    """
    Parse a WhatsApp export from a file path.

    This simply opens the file with UTF-8 encoding and passes its lines
    to `parse_whatsapp_lines`.
    """
    with open(path, "r", encoding="utf-8") as f:
        return parse_whatsapp_lines(f)


# -----------------------------
# Domain knowledge / keywords
# -----------------------------

# Naive list of Hebrew boycott-related words and phrases.
# In a real system, this might be extended, localized, or learned from data.
BOYCOTT_KEYWORDS = [
    "מחרימים",
    "חרם",
    "לא לדבר איתו",
    "לא לדבר איתה",
    "אל תענו לו",
    "אל תענו לה",
    "לא להזמין אותו",
    "לא להזמין אותה",
]


def contains_boycott_keyword(text: str) -> bool:
    """
    Check whether any boycott-related keyword appears in the given text.

    This is a simple, explainable keyword-based check.
    """
    # Lowercase text to make matching case-insensitive
    lowered = text.lower()

    # Return True if any keyword is a substring of the text
    return any(keyword in lowered for keyword in BOYCOTT_KEYWORDS)


# -----------------------------
# Text preprocessing
# -----------------------------

def clean_text(text: str) -> str:
    """
    Perform basic text cleanup:

    - Collapse multiple whitespace characters into a single space.
    - Strip leading and trailing whitespace.

    This helps keep statistics more consistent and avoids counting
    extra spaces as meaningful characters.
    """
    # Replace any sequence of whitespace (spaces, tabs, newlines) with a single space
    text = re.sub(r"\s+", " ", text)
    # Remove leading and trailing spaces
    return text.strip()


# -----------------------------
# Statistics per sender
# -----------------------------

def compute_basic_stats(messages: List[Message]) -> Dict[str, Dict[str, int]]:
    """
    Compute basic per-sender statistics.

    For each sender we calculate:
    - "messages":       total number of messages sent.
    - "chars":          total number of characters sent (after cleanup).
    - "boycott_msgs":   number of messages containing boycott-related keywords.

    Returns:
        A nested dictionary of the form:
        {
            "Sender A": {"messages": 10, "chars": 500, "boycott_msgs": 2},
            "Sender B": {"messages": 5,  "chars": 250, "boycott_msgs": 0},
            ...
        }
    """
    # defaultdict will automatically create the inner dict for new senders
    stats: Dict[str, Dict[str, int]] = defaultdict(
        lambda: {"messages": 0, "chars": 0, "boycott_msgs": 0}
    )

    for msg in messages:
        # Access or create the stats entry for this sender
        sender_stats = stats[msg.sender]

        # Count this message
        sender_stats["messages"] += 1

        # Clean the text and accumulate its character length
        cleaned = clean_text(msg.text)
        sender_stats["chars"] += len(cleaned)

        # If this message contains boycott-related keywords, increment the counter
        if contains_boycott_keyword(cleaned):
            sender_stats["boycott_msgs"] += 1

    return stats


# -----------------------------
# Detect potential boycott target
# -----------------------------

def detect_potential_target(messages: List[Message]) -> Tuple[Optional[str], Counter]:
    """
    Try to infer a potential "target" of a boycott.

    Heuristic approach:
    - Take only messages that contain boycott-related keywords.
    - Tokenize them into words.
    - Count how often each word appears.
    - The most common word may be a name / nickname of the target.

    Returns:
        (target_candidate, mentions_counter)

        - target_candidate: a string (most frequent word) or None if no candidate found.
        - mentions_counter: a Counter with frequencies of all words in the context
          of boycott-related messages.
    """
    mention_counter: Counter = Counter()

    for msg in messages:
        # Skip messages that do not seem related to boycott
        if not contains_boycott_keyword(msg.text):
            continue

        # Extract words using a simple regex-based tokenizer
        words = re.findall(r"\w+", msg.text)

        for w in words:
            # Ignore very short tokens; they are less likely to be meaningful names
            if len(w) < 3:
                continue
            mention_counter[w] += 1

    if not mention_counter:
        # No mentions found in messages that contain boycott-related keywords
        return None, mention_counter

    # Find the most frequent word
    target_candidate, _ = mention_counter.most_common(1)[0]
    return target_candidate, mention_counter


# -----------------------------
# Risk scoring
# -----------------------------

def score_boycott_risk(
    messages: List[Message],
    stats: Dict[str, Dict[str, int]],
) -> Dict[str, float]:
    """
    Aggregate several simple signals into a numeric boycott risk score.

    Signals:
        - keyword_ratio:
            fraction of all messages that contain boycott-related keywords.
        - sender_concentration:
            among boycott messages, share belonging to the most active sender.

    Returns:
        A dictionary with the following keys:
        - "boycott_risk":        final risk score in [0, 1].
        - "keyword_ratio":       ratio of boycott-related messages (0–1).
        - "sender_concentration":concentration of boycott messages in one sender (0–1).
        - "total_messages":      total number of messages (int).
        - "boycott_messages":    number of messages with boycott keywords (int).
    """
    # Handle case where there are no messages at all
    if not messages:
        return {
            "boycott_risk": 0.0,
            "keyword_ratio": 0.0,
            "sender_concentration": 0.0,
            "total_messages": 0.0,
            "boycott_messages": 0.0,
        }

    total_msgs = len(messages)

    # Count messages that contain boycott-related keywords
    boycott_msgs = sum(
        1 for m in messages if contains_boycott_keyword(m.text)
    )

    # Compute ratio out of all messages
    keyword_ratio = boycott_msgs / total_msgs if total_msgs > 0 else 0.0

    # Gather per-sender boycott counts
    sender_boycott_counts = [s["boycott_msgs"] for s in stats.values()]

    if sender_boycott_counts and boycott_msgs > 0:
        max_sender_boycott = max(sender_boycott_counts)
        concentration = max_sender_boycott / boycott_msgs
    else:
        concentration = 0.0

    # Simple linear combination of the two signals:
    # - keyword ratio: 70%
    # - sender concentration: 30%
    raw_score = 0.7 * keyword_ratio + 0.3 * concentration

    # Clamp score into [0, 1]
    risk_score = max(0.0, min(1.0, raw_score))

    return {
        "boycott_risk": round(risk_score, 3),
        "keyword_ratio": round(keyword_ratio, 3),
        "sender_concentration": round(concentration, 3),
        "total_messages": float(total_msgs),
        "boycott_messages": float(boycott_msgs),
    }


# -----------------------------
# Classification layer
# -----------------------------

def classify_boycott(risk_score: float) -> str:
    """
    Convert a numeric risk score into a human-readable label.

    Heuristic thresholds:
        - < 0.25  -> "No clear boycott signals detected"
        - < 0.5   -> "Low boycott risk"
        - < 0.75  -> "Medium boycott risk"
        - >= 0.75 -> "High boycott risk - possible boycott in this group"
    """
    if risk_score < 0.25:
        return "No clear boycott signals detected"
    elif risk_score < 0.5:
        return "Low boycott risk"
    elif risk_score < 0.75:
        return "Medium boycott risk"
    else:
        return "High boycott risk - possible boycott in this group"


# -----------------------------
# Orchestration helpers
# -----------------------------

def _run_full_analysis(messages: List[Message], source: str) -> Dict[str, object]:
    """
    Internal helper to run the full analysis pipeline.

    Steps:
        1) Compute per-sender statistics.
        2) Score boycott risk.
        3) Classify the risk level.
        4) Detect a potential boycott target.

    Args:
        messages: parsed messages from a WhatsApp group.
        source:   description of the source (file path or "in-memory-text").

    Returns:
        A dictionary with all analysis results, ready to be serialized to JSON.
    """
    # Step 1: compute per-sender statistics
    stats = compute_basic_stats(messages)

    # Step 2: calculate numeric risk score and related metrics
    risk_signals = score_boycott_risk(messages, stats)

    # Step 3: convert numeric risk into human-readable label
    label = classify_boycott(float(risk_signals["boycott_risk"]))

    # Step 4: guess potential target and collect mention statistics
    target_candidate, mentions = detect_potential_target(messages)

    return {
        "source": source,
        "label": label,
        "risk_signals": risk_signals,
        "per_sender_stats": dict(stats),               # convert defaultdict to dict
        "potential_target": target_candidate,
        "target_mentions": mentions.most_common(10),   # top 10 mentions
    }


def analyze_whatsapp_group(path: str) -> Dict[str, object]:
    """
    High-level helper to analyze a WhatsApp group from a file path.

    Convenience function for CLI or batch processing.
    """
    messages = parse_whatsapp_export(path)
    return _run_full_analysis(messages, source=path)


def analyze_whatsapp_text_export(content: str) -> Dict[str, object]:
    """
    High-level helper to analyze a WhatsApp export from a raw text string.

    Useful for web APIs where file contents are already loaded in memory.
    """
    lines = content.splitlines()
    messages = parse_whatsapp_lines(lines)
    return _run_full_analysis(messages, source="in-memory-text")


# -----------------------------
# Command-line entry point
# -----------------------------

if __name__ == "__main__":
    # Allow running the analysis directly from the command line:
    #   python whatsafe_detector.py path/to/whatsapp_export.txt
    import sys

    if len(sys.argv) != 2:
        print("Usage: python whatsafe_detector.py <whatsapp_export.txt>")
        sys.exit(1)

    input_path = sys.argv[1]
    result = analyze_whatsapp_group(input_path)
    print(result)
