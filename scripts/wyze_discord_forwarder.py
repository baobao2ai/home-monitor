#!/usr/bin/env python3
"""
wyze_discord_forwarder.py — Poll Wyze events and forward to Discord with thumbnails.
Runs every 5 min via cron.
"""

import os, sys, json, time, hashlib, argparse, requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from wyze_sdk import Client

load_dotenv(Path(__file__).parent.parent / ".env")

WYZE_EMAIL    = os.getenv("WYZE_EMAIL")
WYZE_PASSWORD = os.getenv("WYZE_PASSWORD")
WYZE_KEY_ID   = os.getenv("WYZE_KEY_ID")
WYZE_API_KEY  = os.getenv("WYZE_API_KEY")
WEBHOOK_URL   = os.getenv("DISCORD_WEBHOOK_URL", "")
STATE_FILE    = Path(__file__).parent.parent / "logs" / "wyze_forwarder_state.json"

EVENT_EMOJI = {
    "EventAlarmType.MOTION":  "🏃 Motion",
    "EventAlarmType.PERSON":  "👤 Person",
    "EventAlarmType.VEHICLE": "🚗 Vehicle",
    "EventAlarmType.PET":     "🐾 Pet",
    "EventAlarmType.SOUND":   "🔊 Sound",
    "EventAlarmType.CO":      "⚠️ CO Alert",
    "EventAlarmType.SMOKE":   "🔥 Smoke",
}

def wyze_img_headers(token: str) -> dict:
    """Headers required to download Wyze media files."""
    nonce = int(time.time() * 1000)
    return {
        "access_token": token,
        "requestid": hashlib.md5(str(nonce).encode()).hexdigest(),
        "appVer": "com.hualai___2.19.14",
        "language": "en_US",
        "User-Agent": "okhttp/4.10.0",
    }

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"last_event_time": 0, "sent_ids": []}

def save_state(state):
    STATE_FILE.parent.mkdir(exist_ok=True)
    state["sent_ids"] = state["sent_ids"][-500:]
    STATE_FILE.write_text(json.dumps(state, indent=2))

def send_event(event, token: str, dry_run=False):
    label = EVENT_EMOJI.get(str(event._alarm_type), "📷 Event")
    ts    = datetime.fromtimestamp(int(event.time) / 1000)
    msg   = f"{label} detected — **{ts.strftime('%b %d, %I:%M:%S %p')}**"

    thumb_bytes = None
    if event._files:
        url = event._files[0].url
        if url:
            try:
                r = requests.get(url, headers=wyze_img_headers(token), timeout=15)
                if r.ok:
                    thumb_bytes = r.content
            except Exception as ex:
                print(f"  [WARN] Thumbnail failed: {ex}")

    if dry_run:
        print(f"  [DRY] {msg} | img: {'yes' if thumb_bytes else 'no'} ({len(thumb_bytes) if thumb_bytes else 0}b)")
        return True

    if not WEBHOOK_URL or "YOUR_WEBHOOK" in WEBHOOK_URL:
        print("  [SKIP] Webhook not configured")
        return False

    try:
        if thumb_bytes:
            r = requests.post(WEBHOOK_URL,
                data={"content": msg},
                files={"file": (f"event_{event.id}.jpg", thumb_bytes, "image/jpeg")},
                timeout=15)
        else:
            r = requests.post(WEBHOOK_URL, json={"content": msg}, timeout=15)
        ok = r.status_code in (200, 204)
        print(f"  [{'OK' if ok else 'ERR'}] {msg}")
        return ok
    except Exception as ex:
        print(f"  [ERR] {ex}")
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit",   type=int, default=20)
    parser.add_argument("--reset",   action="store_true")
    args = parser.parse_args()

    state = load_state()
    if args.reset:
        state = {"last_event_time": 0, "sent_ids": []}

    print("[+] Connecting to Wyze...")
    try:
        client = Client(email=WYZE_EMAIL, password=WYZE_PASSWORD,
                        key_id=WYZE_KEY_ID, api_key=WYZE_API_KEY)
    except Exception as e:
        print(f"[ERROR] Auth failed: {e}"); sys.exit(1)

    print(f"[+] Fetching last {args.limit} events...")
    events = client.events.list(limit=args.limit)

    new = sorted(
        [e for e in events if int(e.time) > state["last_event_time"] and e.id not in state["sent_ids"]],
        key=lambda e: int(e.time)
    )
    print(f"[+] {len(new)} new events")

    for e in new:
        ok = send_event(e, client._token, dry_run=args.dry_run)
        if ok or args.dry_run:
            state["sent_ids"].append(e.id)
            state["last_event_time"] = max(state["last_event_time"], int(e.time))

    if not args.dry_run:
        save_state(state)
    print(f"[✓] Done")

if __name__ == "__main__":
    main()
