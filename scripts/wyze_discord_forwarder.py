#!/usr/bin/env python3
"""
wyze_discord_forwarder.py — Poll Wyze events and forward to Discord.

Runs every N minutes via cron. Tracks last-seen event to avoid duplicates.
Sends thumbnail image + event details to Discord webhook.

Usage:
    python3 scripts/wyze_discord_forwarder.py
    python3 scripts/wyze_discord_forwarder.py --dry-run
    python3 scripts/wyze_discord_forwarder.py --limit 10   # check last N events
"""

import os
import sys
import json
import argparse
import requests
import tempfile
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from wyze_sdk import Client
from wyze_sdk.models.events import EventAlarmType

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────
WYZE_EMAIL   = os.getenv("WYZE_EMAIL")
WYZE_PASSWORD = os.getenv("WYZE_PASSWORD")
WYZE_KEY_ID  = os.getenv("WYZE_KEY_ID")
WYZE_API_KEY = os.getenv("WYZE_API_KEY")
WEBHOOK_URL  = os.getenv("DISCORD_WEBHOOK_URL", "")
STATE_FILE   = Path(__file__).parent.parent / "logs" / "wyze_forwarder_state.json"

# Event type labels
EVENT_LABELS = {
    "EventAlarmType.MOTION":  ("🏃 Motion", 0xFF6B35),
    "EventAlarmType.PERSON":  ("👤 Person", 0xE74C3C),
    "EventAlarmType.VEHICLE": ("🚗 Vehicle", 0x3498DB),
    "EventAlarmType.PET":     ("🐾 Pet",    0x27AE60),
    "EventAlarmType.SOUND":   ("🔊 Sound",  0x9B59B6),
    "EventAlarmType.CO":      ("⚠️ CO",     0xE74C3C),
    "EventAlarmType.SMOKE":   ("🔥 Smoke",  0xE74C3C),
}

def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"last_event_time": 0, "sent_ids": []}

def save_state(state: dict):
    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))

def wyze_client() -> Client:
    return Client(
        email=WYZE_EMAIL,
        password=WYZE_PASSWORD,
        key_id=WYZE_KEY_ID,
        api_key=WYZE_API_KEY,
    )

def download_thumbnail(url: str) -> bytes | None:
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return r.content
    except Exception as e:
        print(f"  [WARN] Could not download thumbnail: {e}")
        return None

def send_to_discord(event, dry_run: bool = False):
    alarm_type = str(event._alarm_type)
    label, color = EVENT_LABELS.get(alarm_type, ("📷 Event", 0x95A5A6))

    ts_ms = int(event.time)
    ts    = datetime.fromtimestamp(ts_ms / 1000)
    time_str = ts.strftime("%b %d %Y, %I:%M:%S %p")

    msg = f"{label} detected at **{time_str}**"

    # Get thumbnail URL if available
    thumb_url = None
    thumb_bytes = None
    if event._files:
        for f in event._files:
            if hasattr(f, 'url') and f.url:
                thumb_url = f.url
                break

    if dry_run:
        print(f"  [DRY] Would send: {msg}")
        print(f"  [DRY] Thumbnail: {thumb_url[:60] if thumb_url else 'none'}...")
        return True

    if not WEBHOOK_URL or "YOUR_WEBHOOK" in WEBHOOK_URL:
        print("  [SKIP] DISCORD_WEBHOOK_URL not configured in .env")
        return False

    # Download thumbnail
    if thumb_url:
        thumb_bytes = download_thumbnail(thumb_url)

    if thumb_bytes:
        # Send with image attachment
        r = requests.post(
            WEBHOOK_URL,
            data={"content": msg},
            files={"file": (f"event_{event.id}.jpg", thumb_bytes, "image/jpeg")},
            timeout=15
        )
    else:
        # Text only
        r = requests.post(WEBHOOK_URL, json={"content": msg}, timeout=15)

    ok = r.status_code in (200, 204)
    if ok:
        print(f"  [OK] Sent: {msg}")
    else:
        print(f"  [ERR] Discord returned {r.status_code}: {r.text[:100]}")
    return ok

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit",   type=int, default=20)
    parser.add_argument("--reset",   action="store_true", help="Reset state (resend all recent events)")
    args = parser.parse_args()

    state = load_state()
    if args.reset:
        state = {"last_event_time": 0, "sent_ids": []}
        print("[!] State reset")

    print(f"[+] Connecting to Wyze API...")
    try:
        client = wyze_client()
    except Exception as e:
        print(f"[ERROR] Auth failed: {e}")
        sys.exit(1)

    print(f"[+] Fetching last {args.limit} events...")
    try:
        events = client.events.list(limit=args.limit)
    except Exception as e:
        print(f"[ERROR] Could not fetch events: {e}")
        sys.exit(1)

    print(f"[+] Found {len(events)} events, last seen time: {state['last_event_time']}")

    new_events = []
    for e in events:
        ts = int(e.time)
        if ts > state["last_event_time"] and e.id not in state["sent_ids"]:
            new_events.append(e)

    # Process oldest first
    new_events.sort(key=lambda e: int(e.time))
    print(f"[+] {len(new_events)} new events to forward")

    sent_count = 0
    for e in new_events:
        print(f"  Processing: {e.id} | {e._alarm_type} | {datetime.fromtimestamp(int(e.time)/1000)}")
        ok = send_to_discord(e, dry_run=args.dry_run)
        if ok or args.dry_run:
            state["sent_ids"].append(e.id)
            state["last_event_time"] = max(state["last_event_time"], int(e.time))
            sent_count += 1

    # Keep sent_ids list bounded
    state["sent_ids"] = state["sent_ids"][-500:]

    if not args.dry_run:
        save_state(state)

    print(f"\n[✓] Done: {sent_count}/{len(new_events)} events forwarded")

if __name__ == "__main__":
    main()
