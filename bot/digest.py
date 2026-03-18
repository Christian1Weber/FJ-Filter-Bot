"""
Daily Digest Job – Runs at 08:00 and 22:00 CET via GitHub Actions.
1. Fetch all messages from the last ~14 hours
2. Light keyword filter to remove pure noise
3. Send everything to LLM for a comprehensive German briefing
4. Post digest to #fj-daily-briefing
"""
import sys
from datetime import datetime, timezone

from bot.config import (
    DISCORD_BOT_TOKEN, SOURCE_CHANNEL_ID, DIGEST_CHANNEL_ID,
    DIGEST_LOOKBACK_HOURS,
)
from bot.discord_api import (
    fetch_messages_since_hours, extract_text_from_messages, post_message,
)
from bot.keyword_filter import deduplicate_messages
from bot.llm_filter import generate_digest


def get_briefing_title() -> str:
    """Generate a title based on current time."""
    now = datetime.now(timezone.utc)
    hour_utc = now.hour

    # 08:00 CET = 07:00 UTC (winter) / 06:00 UTC (summer)
    # 22:00 CET = 21:00 UTC (winter) / 20:00 UTC (summer)
    if 5 <= hour_utc <= 9:
        return "☀️ Morgen-Briefing"
    else:
        return "🌙 Abend-Briefing"


def split_message(text: str, max_length: int = 1950) -> list[str]:
    """Split long messages to fit Discord's 2000 char limit."""
    if len(text) <= max_length:
        return [text]

    parts = []
    current = ""

    for line in text.split("\n"):
        if len(current) + len(line) + 1 > max_length:
            if current:
                parts.append(current.strip())
            current = line + "\n"
        else:
            current += line + "\n"

    if current.strip():
        parts.append(current.strip())

    return parts


def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Starting digest job...")

    # Step 1: Fetch messages from the lookback period
    print(f"Fetching messages from last {DIGEST_LOOKBACK_HOURS} hours...")
    raw_messages = fetch_messages_since_hours(
        DISCORD_BOT_TOKEN, SOURCE_CHANNEL_ID, hours_ago=DIGEST_LOOKBACK_HOURS
    )
    print(f"Fetched {len(raw_messages)} raw messages")

    if not raw_messages:
        print("No messages in lookback period. Posting notice.")
        post_message(
            DISCORD_BOT_TOKEN, DIGEST_CHANNEL_ID,
            f"**{get_briefing_title()}** – Keine Nachrichten im Berichtszeitraum."
        )
        return

    # Step 2: Extract and deduplicate
    messages = extract_text_from_messages(raw_messages)
    messages = deduplicate_messages(messages, similarity_threshold=0.7)
    print(f"After extraction + dedup: {len(messages)} messages")

    # Step 3: Generate digest via LLM
    print("Generating digest via Gemini...")
    digest_text = generate_digest(messages)

    if not digest_text:
        print("Gemini returned empty digest. Exiting.")
        return

    # Step 4: Format and post
    title = get_briefing_title()
    date_str = datetime.now(timezone.utc).strftime("%d.%m.%Y")
    header = f"**{title} – {date_str}**\n{'─' * 35}\n\n"

    full_text = header + digest_text
    footer = f"\n\n{'─' * 35}\n📊 *{len(messages)} Nachrichten analysiert*"
    full_text += footer

    # Split if too long for Discord
    parts = split_message(full_text)

    for i, part in enumerate(parts):
        try:
            post_message(DISCORD_BOT_TOKEN, DIGEST_CHANNEL_ID, part)
            print(f"  Posted part {i + 1}/{len(parts)} ({len(part)} chars)")
        except Exception as e:
            print(f"  Error posting part {i + 1}: {e}")

    print(f"Done. Posted digest in {len(parts)} message(s).")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FATAL ERROR: {e}", file=sys.stderr)
        sys.exit(1)
