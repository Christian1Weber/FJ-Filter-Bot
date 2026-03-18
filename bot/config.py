"""
Configuration for the Financial Juice Filter Bot.
Adjust keywords, weights, and thresholds here.
"""
import os

# ── Discord ──────────────────────────────────────────────
DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
SOURCE_CHANNEL_ID = os.environ["SOURCE_CHANNEL_ID"]
HIGHLIGHTS_CHANNEL_ID = os.environ["HIGHLIGHTS_CHANNEL_ID"]
DIGEST_CHANNEL_ID = os.environ["DIGEST_CHANNEL_ID"]

# ── Gemini ───────────────────────────────────────────────
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GEMINI_MODEL = "gemini-2.0-flash"

# ── Filter Settings ──────────────────────────────────────
# Minimum score (1-10) from LLM to be posted as highlight
RELEVANCE_THRESHOLD = 7

# How many minutes back to look for new messages (highlights job)
LOOKBACK_MINUTES = 20

# How many hours back to look for digest
DIGEST_LOOKBACK_HOURS = 14  # covers 22:00→08:00 and 08:00→22:00

# ── Keyword Pre-Filter (Stage 1) ────────────────────────
# Messages matching HIGH keywords skip straight to LLM evaluation.
# Messages matching MEDIUM get evaluated too but with lower base score.
# Messages matching NONE of these are discarded before LLM.

PRIO_HIGH_KEYWORDS = [
    # Central Banks & Rates
    "fomc", "fed ", "fed's", "powell", "rate decision", "rate cut", "rate hike",
    "basis points", "dot plot", "sep ", "projections", "ecb", "boj", "boe",
    "lagarde", "ueda", "bailey",
    # Macro Data
    "cpi", "pce", "nfp", "non-farm", "payroll", "gdp", "pmi", "ism",
    "jobless claims", "unemployment", "retail sales", "inflation",
    # Energy / Oil (critical for MGC correlation)
    "wti", "brent", "crude", "oil price", "opec", "barrel",
    "natural gas", "lng", "energy crisis", "gasoline", "diesel",
    "strait of hormuz", "hormuz", "ras laffan",
    # Gold specific
    "gold", "xau", "bullion", "central bank gold", "mgc",
    # Index Moves
    "s&p", "spx", "nasdaq", "ndx", "mnq", "dow ", "vix",
    "futures settle", "moc imbalance",
    # Geopolitical Escalation
    "missile", "attack", "strike", "war ", "nuclear", "sanctions",
    "escalat", "evacuat", "intercept", "ballistic",
    # Capital Flows
    "tic ", "capital flow", "treasury hold", "net capital",
]

PRIO_MEDIUM_KEYWORDS = [
    # Central Bank Officials (not top tier)
    "boc", "macklem", "rba", "snb", "pboc", "riksbank",
    # Macro Context
    "tariff", "trade deal", "usmca", "supply chain",
    "productivity", "labor market", "housing",
    "consumer confidence", "consumer survey",
    # Earnings (major)
    "earnings", "revenue", "eps", "guidance",
    "aapl", "msft", "nvda", "googl", "amzn", "meta", "tsla",
    "$mu", "$f",
    # Ratings & Credit
    "fitch", "moody", "s&p global", "downgrad", "upgrad", "default",
    # Geopolitical Context
    "iran", "israel", "saudi", "qatar", "uae", "russia",
    "china", "taiwan", "ukraine",
    # Policy
    "biden", "trump", "vance", "yellen", "bessent",
]

NOISE_KEYWORDS = [
    # Stuff we always skip
    "fx options expir", "greek hedging", "press conference ends",
    "watch live", "http", ".pdf", "preview=true",
]

# ── Emoji mapping for Discord embeds ────────────────────
CATEGORY_EMOJI = {
    "fed": "🏦",
    "rates": "📊",
    "oil": "🛢️",
    "energy": "⛽",
    "gold": "🥇",
    "geopolitical": "🌍",
    "macro": "📈",
    "earnings": "🏢",
    "flows": "💰",
    "other": "📌",
}
