"""
Stage 2: LLM-based relevance scoring and German translation.
Uses Google Gemini free tier.
"""
import json
import requests
import time
from bot.config import GEMINI_API_KEY, GEMINI_MODEL

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

# ── Prompts ──────────────────────────────────────────────

HIGHLIGHT_SYSTEM_PROMPT = """Du bist ein Echtzeit-Nachrichtenfilter für einen Futures-Trader, der Micro Nasdaq (MNQ) und Micro Gold (MGC) handelt.

Du erhältst Finanznachrichten auf Englisch vom Financial Juice News-Feed.

Deine Aufgabe:
1. Bewerte die MARKTRELEVANZ jeder Nachricht auf einer Skala von 1-10
2. Wenn Score ≥ 7: Übersetze und fasse die Nachricht knapp auf Deutsch zusammen
3. Ordne eine Kategorie zu

SCORING-KRITERIEN:
- 9-10: Direkt marktbewegend (Zinsentscheide, große Makrodaten, Kriegseskalation mit Energieimpact, Ölpreisbewegungen)
- 7-8: Wichtiger Kontext (Zentralbank-Aussagen, geopolitische Entwicklungen, Kapitalflüsse, bedeutende Earnings)
- 4-6: Hintergrund (Analysten-Meinungen, Sekundärmeldungen, regionale Politik)
- 1-3: Noise (Duplikate, Links, unwichtige Details, irrelevante Regionen)

KATEGORIEN: fed, rates, oil, energy, gold, geopolitical, macro, earnings, flows, other

WICHTIG:
- Fasse ZUSAMMEN, übersetze nicht wörtlich. Kurz und knackig.
- Wenn eine Nachricht ein Update zu einer vorherigen ist, erwähne den Kontext
- Beginne wichtige Nachrichten mit einem passenden Emoji

Antworte IMMER als JSON-Array. Jedes Element:
{"score": 8, "category": "fed", "summary_de": "🏦 Fed hält Zinsen bei 3,50-3,75%..."}

Wenn der Score unter 7 liegt:
{"score": 3, "category": "other", "summary_de": null}
"""

DIGEST_SYSTEM_PROMPT = """Du bist ein Finanzjournalist der ein knackiges deutsches Market Briefing schreibt für einen Futures-Trader (MNQ + MGC).

Du erhältst ALLE Nachrichten eines Zeitraums vom Financial Juice News-Feed.

Erstelle ein strukturiertes Briefing mit diesen Regeln:
- Maximal 5 Abschnitte, nach Wichtigkeit sortiert
- Jeder Abschnitt hat eine Emoji-Überschrift und 2-4 Sätze
- Am Ende ein "📌 Ausblick"-Abschnitt mit den wichtigsten Punkten für die nächsten Stunden
- Sprache: Deutsch, professionell aber knackig
- Verwende **fett** für Schlüsselzahlen und -fakten
- Erwähne konkrete Preise/Zahlen wo vorhanden
- Ignoriere Noise und Duplikate

Format:
## 🏦 [Überschrift]
[2-4 Sätze Text]

## 🛢️ [Überschrift]
[2-4 Sätze Text]

...

## 📌 Ausblick
[Bullet Points was als nächstes zu beachten ist]
"""


def _call_gemini(system_prompt: str, user_content: str, max_retries: int = 3) -> str:
    """Call Gemini API with retry logic."""
    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"{system_prompt}\n\n---\n\n{user_content}"}]
            }
        ],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 4096,
        }
    }

    for attempt in range(max_retries):
        try:
            resp = requests.post(GEMINI_URL, headers=headers, params=params, json=payload, timeout=60)

            if resp.status_code == 429:
                wait = min(2 ** attempt * 5, 60)
                print(f"Gemini rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue

            resp.raise_for_status()
            data = resp.json()

            # Extract text from Gemini response
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")

            return ""

        except Exception as e:
            print(f"Gemini API error (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)

    return ""


def evaluate_messages(messages: list[dict]) -> list[dict]:
    """
    Send messages to Gemini for relevance scoring and translation.
    Processes in batches of up to 15 messages to stay within token limits.
    """
    if not messages:
        return []

    results = []
    batch_size = 15

    for i in range(0, len(messages), batch_size):
        batch = messages[i:i + batch_size]

        # Format messages for the prompt
        formatted = []
        for idx, msg in enumerate(batch):
            ts = msg.get("timestamp", "")[:16]
            formatted.append(f"[{idx}] ({ts}) {msg['content']}")

        user_content = (
            f"Bewerte diese {len(batch)} Nachrichten:\n\n"
            + "\n".join(formatted)
            + "\n\nAntwort als JSON-Array mit genau "
            + f"{len(batch)} Elementen, eines pro Nachricht in derselben Reihenfolge."
        )

        raw = _call_gemini(HIGHLIGHT_SYSTEM_PROMPT, user_content)

        # Parse JSON from response
        try:
            # Clean markdown code fences if present
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            parsed = json.loads(cleaned)

            if isinstance(parsed, list):
                for j, item in enumerate(parsed):
                    if j < len(batch):
                        batch[j]["score"] = item.get("score", 0)
                        batch[j]["category"] = item.get("category", "other")
                        batch[j]["summary_de"] = item.get("summary_de")
                        results.append(batch[j])
            else:
                # Fallback: add unparsed messages with low score
                for msg in batch:
                    msg["score"] = 0
                    msg["summary_de"] = None
                    results.append(msg)

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            print(f"Failed to parse Gemini response: {e}")
            print(f"Raw response: {raw[:500]}")
            # Fallback
            for msg in batch:
                msg["score"] = 0
                msg["summary_de"] = None
                results.append(msg)

        # Respect rate limits between batches
        if i + batch_size < len(messages):
            time.sleep(4)

    return results


def generate_digest(messages: list[dict]) -> str:
    """
    Generate a daily briefing digest from all messages.
    Returns formatted German markdown text.
    """
    if not messages:
        return "Keine Nachrichten im Berichtszeitraum."

    # Format all messages for digest prompt
    formatted = []
    for msg in messages:
        ts = msg.get("timestamp", "")[:16]
        formatted.append(f"({ts}) {msg['content']}")

    user_content = (
        f"Hier sind {len(messages)} Nachrichten aus dem Financial Juice Feed.\n"
        f"Erstelle daraus ein knackiges deutsches Market Briefing:\n\n"
        + "\n".join(formatted)
    )

    return _call_gemini(DIGEST_SYSTEM_PROMPT, user_content)
