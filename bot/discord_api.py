"""
Discord REST API client – no persistent connection needed.
Reads messages from source channel, posts to target channels.
"""
import requests
import time
from datetime import datetime, timezone

BASE_URL = "https://discord.com/api/v10"

# Discord epoch for snowflake ID calculation
DISCORD_EPOCH = 1420070400000


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json",
    }


def snowflake_from_timestamp(dt: datetime) -> str:
    """Convert a datetime to a Discord snowflake ID (for 'after' parameter)."""
    ts_ms = int(dt.timestamp() * 1000)
    snowflake = (ts_ms - DISCORD_EPOCH) << 22
    return str(snowflake)


def fetch_messages(token: str, channel_id: str, after_snowflake: str = None, limit: int = 100) -> list[dict]:
    """
    Fetch messages from a Discord channel.
    Uses pagination to get all messages after a given snowflake.
    Returns messages in chronological order (oldest first).
    """
    all_messages = []
    url = f"{BASE_URL}/channels/{channel_id}/messages"

    while True:
        params = {"limit": min(limit, 100)}
        if after_snowflake:
            params["after"] = after_snowflake

        resp = requests.get(url, headers=_headers(token), params=params)

        if resp.status_code == 429:
            # Rate limited – wait and retry
            retry_after = resp.json().get("retry_after", 5)
            print(f"Rate limited, waiting {retry_after}s...")
            time.sleep(retry_after)
            continue

        resp.raise_for_status()
        messages = resp.json()

        if not messages:
            break

        all_messages.extend(messages)

        # Discord returns newest first; if we got fewer than 100, we have all
        if len(messages) < 100:
            break

        # The 'after' parameter returns messages AFTER the given ID
        # Messages come newest-first, so the last element is the oldest
        # To paginate forward, use the newest message ID as 'after'
        after_snowflake = messages[0]["id"]

        time.sleep(0.5)  # Be nice to Discord API

    # Reverse to chronological order (oldest first)
    all_messages.reverse()
    return all_messages


def fetch_messages_since(token: str, channel_id: str, minutes_ago: int = 20) -> list[dict]:
    """Fetch all messages from the last N minutes."""
    from datetime import timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    snowflake = snowflake_from_timestamp(cutoff)
    return fetch_messages(token, channel_id, after_snowflake=snowflake)


def fetch_messages_since_hours(token: str, channel_id: str, hours_ago: int = 14) -> list[dict]:
    """Fetch all messages from the last N hours (for digest)."""
    from datetime import timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    snowflake = snowflake_from_timestamp(cutoff)
    return fetch_messages(token, channel_id, after_snowflake=snowflake)


def post_message(token: str, channel_id: str, content: str) -> dict:
    """Post a simple text message to a Discord channel."""
    url = f"{BASE_URL}/channels/{channel_id}/messages"
    payload = {"content": content}

    resp = requests.post(url, headers=_headers(token), json=payload)

    if resp.status_code == 429:
        retry_after = resp.json().get("retry_after", 5)
        time.sleep(retry_after)
        resp = requests.post(url, headers=_headers(token), json=payload)

    resp.raise_for_status()
    return resp.json()


def post_embed(token: str, channel_id: str, title: str, description: str,
               color: int = 0x22c55e, footer: str = None) -> dict:
    """Post a rich embed message to a Discord channel."""
    url = f"{BASE_URL}/channels/{channel_id}/messages"

    embed = {
        "title": title,
        "description": description[:4096],  # Discord embed limit
        "color": color,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if footer:
        embed["footer"] = {"text": footer}

    payload = {"embeds": [embed]}

    resp = requests.post(url, headers=_headers(token), json=payload)

    if resp.status_code == 429:
        retry_after = resp.json().get("retry_after", 5)
        time.sleep(retry_after)
        resp = requests.post(url, headers=_headers(token), json=payload)

    resp.raise_for_status()
    return resp.json()


def extract_text_from_messages(messages: list[dict]) -> list[dict]:
    """
    Extract clean text content from Discord message objects.
    Returns list of {timestamp, content, id} dicts.
    Filters out empty messages and bot commands.
    """
    cleaned = []
    for msg in messages:
        content = msg.get("content", "").strip()
        if not content:
            # Check embeds
            for embed in msg.get("embeds", []):
                if embed.get("description"):
                    content = embed["description"].strip()
                    break

        if content and len(content) > 5:
            cleaned.append({
                "id": msg["id"],
                "timestamp": msg["timestamp"],
                "content": content,
            })

    return cleaned
