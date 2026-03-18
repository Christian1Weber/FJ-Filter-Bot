"""
Highlights Job – Runs every 15 minutes via GitHub Actions.
1. Fetch new messages from Financial Juice channel
2. Keyword pre-filter (Stage 1)
3. LLM relevance scoring + German translation (Stage 2)
4. Post highlights to #fj-highlights-de
"""
import sys
from datetime import datetime, timezone

from bot.config import (
    DISCORD_BOT_TOKEN, SOURCE_CHANNEL_ID, HIGHLIGHTS_CHANNEL_ID,
    RELEVANCE_THRESHOLD, LOOKBACK_MINUTES, CATEGORY_EMOJI,
)
from bot.discord_api import (
    fetch_messages_since, extract_text_from_messages, post_message,
)
from bot.keyword_filter import batch_filter, deduplicate_messages
from bot.llm_filter import evaluate_messages


def format_highlight(msg: dict) -> str:
    """Format a single highlight message for Discord."""
    emoji = CATEGORY_EMOJI.get(msg.get("category", "other"), "📌")
    summary = msg.get("summary_de", msg["content"])
    score = msg.get("score", 0)

    # Color indicator based on score
    if score >= 9:
        indicator = "🔴"
    elif score >= 7:
        indicator = "🟡"
    else:
        indicator = "🔵"

    return f"{indicator} {summary}"


def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Starting highlights job...")

    # Step 1: Fetch recent messages
    print(f"Fetching messages from last {LOOKBACK_MINUTES} minutes...")
    raw_messages = fetch_messages_since(
        DISCORD_BOT_TOKEN, SOURCE_CHANNEL_ID, minutes_ago=LOOKBACK_MINUTES
    )
    print(f"Fetched {len(raw_messages)} raw messages")

    if not raw_messages:
        print("No new messages. Exiting.")
        return

    # Extract text content
    messages = extract_text_from_messages(raw_messages)
    print(f"Extracted {len(messages)} text messages")

    if not messages:
        print("No text content found. Exiting.")
        return

    # Step 2: Deduplicate
    messages = deduplicate_messages(messages)
    print(f"After dedup: {len(messages)} messages")

    # Step 3: Keyword pre-filter (Stage 1)
    high, medium, noise = batch_filter(messages)
    print(f"Keyword filter: {len(high)} high, {len(medium)} medium, {len(noise)} noise")

    # Only send high + medium to LLM
    to_evaluate = high + medium
    if not to_evaluate:
        print("All messages filtered as noise. Exiting.")
        return

    # Step 4: LLM evaluation (Stage 2)
    print(f"Sending {len(to_evaluate)} messages to Gemini...")
    evaluated = evaluate_messages(to_evaluate)

    # Step 5: Filter by relevance threshold and post
    highlights = [m for m in evaluated if m.get("score", 0) >= RELEVANCE_THRESHOLD and m.get("summary_de")]
    print(f"Highlights to post: {len(highlights)}")

    if not highlights:
        print("No highlights above threshold. Exiting.")
        return

    # Sort by score (highest first)
    highlights.sort(key=lambda x: x.get("score", 0), reverse=True)

    # Post to Discord
    posted = 0
    for msg in highlights:
        try:
            text = format_highlight(msg)
            post_message(DISCORD_BOT_TOKEN, HIGHLIGHTS_CHANNEL_ID, text)
            posted += 1
            print(f"  Posted (score {msg.get('score')}): {text[:80]}...")
        except Exception as e:
            print(f"  Error posting: {e}")

    print(f"Done. Posted {posted} highlights.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FATAL ERROR: {e}", file=sys.stderr)
        sys.exit(1)
