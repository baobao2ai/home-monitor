# 🏠 Home Monitor

Wyze camera event monitoring — polls Wyze cloud API and forwards motion events with thumbnails to Discord.

**Stack:** Python · Wyze SDK · Discord Webhooks · cron

---

## Architecture

```
Wyze Cam V4 → Wyze Cloud → wyze_discord_forwarder.py → Discord
```

No local NVR needed. Events and thumbnails pulled directly from Wyze's API.

---

## Quick Start

```bash
git clone https://github.com/baobao2ai/home-monitor.git
cd home-monitor
python3 -m venv venv
venv/bin/pip install -r requirements.txt

cp .env.example .env
# Edit .env with your credentials

# Test
venv/bin/python scripts/wyze_discord_forwarder.py --dry-run

# Install cron (runs every 5 min)
REPO=$(pwd)
(crontab -l 2>/dev/null; echo "*/5 * * * * cd $REPO && $REPO/venv/bin/python scripts/wyze_discord_forwarder.py >> $REPO/logs/wyze_forwarder.log 2>&1") | crontab -
```

---

## Files

```
home-monitor/
├── scripts/
│   └── wyze_discord_forwarder.py   # Main script
├── docs/
│   ├── setup.md                    # Full setup guide
│   ├── wifi-hotspot.md             # Hotspot setup (no-router env)
│   └── troubleshooting.md          # Common issues
├── logs/                           # Runtime logs (gitignored)
├── .env.example                    # Config template
├── requirements.txt
└── README.md
```

---

## .env Configuration

```env
WYZE_EMAIL=your@email.com
WYZE_PASSWORD=yourpassword
WYZE_KEY_ID=your-key-id          # From developer-api-console.wyze.com
WYZE_API_KEY=your-api-key
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

Get Wyze API keys at: https://developer-api-console.wyze.com

---

## Network Setup (No-Router Environment)

See `docs/wifi-hotspot.md` for connecting the camera via a machine-hosted WiFi hotspot with internet sharing.
