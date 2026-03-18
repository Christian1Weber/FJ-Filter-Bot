# 🧃 Financial Juice Discord Filter Bot

Automatische Filterung, Übersetzung und Zusammenfassung von Financial Juice Nachrichten auf Discord.

## Was macht der Bot?

| Channel | Funktion | Frequenz |
|---|---|---|
| `#fj-highlights-de` | Wichtigste Nachrichten gefiltert & auf Deutsch übersetzt | Alle 15 Minuten |
| `#fj-daily-briefing` | Knackiges Tages-Briefing aller Nachrichten | 08:00 + 22:00 Uhr CET |

## Tech-Stack (100% kostenlos)

- **GitHub Actions** – Läuft automatisch im Hintergrund (kein eigener Server nötig)
- **Google Gemini API** – Free Tier (1 Mio. Tokens/Tag, 1.500 Requests/Tag)
- **Discord REST API** – Liest und schreibt Nachrichten

---

## 🚀 Schritt-für-Schritt Einrichtung

### Schritt 1: Discord Bot erstellen

1. Gehe zu https://discord.com/developers/applications
2. Klick **"New Application"** → Name: `FJ Filter Bot` → Create
3. Links auf **"Bot"** klicken
4. Klick **"Reset Token"** → Token kopieren und **sicher speichern** (wird nur einmal angezeigt!)
5. Unter **"Privileged Gateway Intents"**:
   - ✅ **Message Content Intent** aktivieren
6. Klick **"Save Changes"**

### Schritt 2: Bot zum Server einladen

1. Links auf **"OAuth2"** klicken
2. Unter **"OAuth2 URL Generator"**:
   - Scopes: ✅ `bot`
   - Bot Permissions: ✅ `Read Message History`, ✅ `Send Messages`, ✅ `Embed Links`
3. Die generierte URL kopieren und im Browser öffnen
4. Deinen Discord Server auswählen → Autorisieren

### Schritt 3: Discord Channel IDs herausfinden

1. In Discord: **Einstellungen → Erweitert → Entwicklermodus** aktivieren
2. Erstelle zwei neue Channels auf deinem Server:
   - `#fj-highlights-de`
   - `#fj-daily-briefing`
3. **Rechtsklick** auf den Financial Juice Quell-Channel → **"ID kopieren"**
4. Dasselbe für `#fj-highlights-de` und `#fj-daily-briefing`
5. Notiere alle drei IDs

### Schritt 4: Google Gemini API Key holen

1. Gehe zu https://aistudio.google.com/apikey
2. Klick **"Create API Key"**
3. Key kopieren und **sicher speichern**

### Schritt 5: GitHub Repository erstellen

1. Gehe zu https://github.com/new
2. Repository Name: `fj-filter-bot`
3. **Public** auswählen (damit GitHub Actions kostenlos & unlimitiert läuft)
4. Repository erstellen

### Schritt 6: Secrets in GitHub eintragen

1. Im Repository: **Settings → Secrets and variables → Actions**
2. Klick **"New repository secret"** für jeden dieser Werte:

| Secret Name | Wert |
|---|---|
| `DISCORD_BOT_TOKEN` | Dein Discord Bot Token aus Schritt 1 |
| `SOURCE_CHANNEL_ID` | Channel-ID des Financial Juice Channels |
| `HIGHLIGHTS_CHANNEL_ID` | Channel-ID von #fj-highlights-de |
| `DIGEST_CHANNEL_ID` | Channel-ID von #fj-daily-briefing |
| `GEMINI_API_KEY` | Dein Google Gemini API Key aus Schritt 4 |

### Schritt 7: Code hochladen

Alle Dateien aus diesem Repository in dein GitHub Repository hochladen. Am einfachsten:

```bash
git clone https://github.com/DEIN-USERNAME/fj-filter-bot.git
cd fj-filter-bot
# Alle Dateien aus diesem Paket hierhin kopieren
git add .
git commit -m "Initial setup"
git push
```

### Schritt 8: GitHub Actions aktivieren

1. Im Repository: **Actions** Tab
2. Falls nötig: **"I understand my workflows, go ahead and enable them"** klicken
3. Die Workflows starten automatisch nach dem Push

---

## ✅ Fertig!

Der Bot läuft jetzt automatisch:
- **Alle 15 Minuten** werden neue Nachrichten geprüft und Highlights gepostet
- **Um 08:00 und 22:00 CET** wird das Daily Briefing erstellt

## Troubleshooting

- **Actions laufen nicht?** → Prüfe unter Actions Tab ob Workflows aktiv sind
- **Bot postet nichts?** → Prüfe ob Bot die richtigen Channel-Berechtigungen hat
- **Fehler in den Logs?** → Actions → Workflow Run anklicken → Logs prüfen
- **Gemini Fehler?** → Free Tier Limit erreicht? Prüfe https://aistudio.google.com/

## Anpassungen

- **Filter-Keywords anpassen:** `bot/keyword_filter.py` editieren
- **Relevanz-Schwelle ändern:** In `bot/config.py` den `RELEVANCE_THRESHOLD` anpassen
- **Frequenz ändern:** In `.github/workflows/highlights.yml` den Cron-Ausdruck ändern
- **Digest-Zeiten ändern:** In `.github/workflows/digest.yml` den Cron-Ausdruck ändern
