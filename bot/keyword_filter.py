"""
Stage 1: Keyword-based pre-filter.
Classifies messages as HIGH / MEDIUM / NOISE before sending to LLM.
This saves LLM tokens by filtering obvious noise.
"""
from bot.config import PRIO_HIGH_KEYWORDS, PRIO_MEDIUM_KEYWORDS, NOISE_KEYWORDS


def classify_message(text: str) -> str:
    """
    Classify a message based on keyword matching.

    Returns:
        "high"   – Definitely send to LLM for evaluation
        "medium" – Send to LLM but lower priority
        "noise"  – Skip entirely, don't waste LLM tokens
    """
    text_lower = text.lower()

    # Check noise first (links, expiries, etc.)
    for kw in NOISE_KEYWORDS:
        if kw in text_lower:
            return "noise"

    # Check high-priority keywords
    high_matches = sum(1 for kw in PRIO_HIGH_KEYWORDS if kw in text_lower)
    if high_matches >= 1:
        return "high"

    # Check medium-priority keywords
    medium_matches = sum(1 for kw in PRIO_MEDIUM_KEYWORDS if kw in text_lower)
    if medium_matches >= 1:
        return "medium"

    # No keyword match at all – likely noise
    return "noise"


def batch_filter(messages: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Filter a batch of messages into three groups.

    Returns:
        (high_messages, medium_messages, noise_messages)
    Each message dict gets an added 'keyword_class' field.
    """
    high, medium, noise = [], [], []

    for msg in messages:
        classification = classify_message(msg["content"])
        msg["keyword_class"] = classification

        if classification == "high":
            high.append(msg)
        elif classification == "medium":
            medium.append(msg)
        else:
            noise.append(msg)

    return high, medium, noise


def deduplicate_messages(messages: list[dict], similarity_threshold: float = 0.6) -> list[dict]:
    """
    Remove near-duplicate messages (common with Financial Juice updates).
    Uses simple word overlap ratio.
    """
    if not messages:
        return messages

    unique = [messages[0]]

    for msg in messages[1:]:
        is_duplicate = False
        msg_words = set(msg["content"].lower().split())

        for existing in unique[-10:]:  # Check against last 10 unique messages
            existing_words = set(existing["content"].lower().split())

            if not msg_words or not existing_words:
                continue

            overlap = len(msg_words & existing_words)
            ratio = overlap / max(len(msg_words), len(existing_words))

            if ratio >= similarity_threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            unique.append(msg)

    return unique
