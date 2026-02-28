#!/usr/bin/env python3
"""
daily_digest.py — Compile today's motion clips and send to Discord.

Usage:
    python3 daily_digest.py
    python3 daily_digest.py --date 2026-02-28   # specific date
    python3 daily_digest.py --dry-run            # print summary, don't send

Requires:
    pip install requests python-dotenv
    ffmpeg installed on host
"""

import os
import sys
import json
import shutil
import argparse
import requests
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────
FRIGATE_API   = os.getenv("FRIGATE_API", "http://localhost:5000")
WEBHOOK_URL   = os.getenv("DISCORD_WEBHOOK_URL", "")
STORAGE_PATH  = Path(os.getenv("STORAGE_PATH", "./storage"))
MAX_CLIP_SIZE = 8 * 1024 * 1024   # 8MB Discord limit per file
MAX_CLIPS     = 10                 # Max clips to include in digest


def get_events(date_str: str) -> list[dict]:
    """Fetch events from Frigate API for a given date."""
    start = datetime.strptime(date_str, "%Y-%m-%d")
    end   = start + timedelta(days=1)

    url = f"{FRIGATE_API}/api/events"
    params = {
        "after":  int(start.timestamp()),
        "before": int(end.timestamp()),
        "has_clip": 1,
        "limit":  500,
    }

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        print(f"[ERROR] Failed to fetch events from Frigate: {e}")
        return []


def score_event(event: dict) -> float:
    """Score an event by confidence + object priority."""
    priority = {"person": 3, "car": 2, "dog": 2, "cat": 2, "bicycle": 1}
    label    = event.get("label", "")
    score    = event.get("top_score", 0) * 100
    return score + priority.get(label, 0) * 5


def download_clip(event: dict, dest: Path) -> Path | None:
    """Download a clip from Frigate to a local path."""
    event_id = event["id"]
    url = f"{FRIGATE_API}/api/events/{event_id}/clip.mp4"
    dest_file = dest / f"{event_id}.mp4"

    try:
        r = requests.get(url, stream=True, timeout=30)
        r.raise_for_status()
        with open(dest_file, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        size = dest_file.stat().st_size
        if size > MAX_CLIP_SIZE:
            print(f"  [SKIP] {event_id} too large ({size//1024}KB)")
            dest_file.unlink()
            return None
        return dest_file
    except Exception as e:
        print(f"  [ERROR] Failed to download {event_id}: {e}")
        return None


def compile_highlight_reel(clips: list[Path], output: Path) -> bool:
    """Combine clips into a single highlight reel using ffmpeg."""
    if not clips:
        return False

    # Write concat list
    list_file = output.parent / "concat.txt"
    with open(list_file, "w") as f:
        for clip in clips:
            f.write(f"file '{clip.absolute()}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
        str(output)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    list_file.unlink(missing_ok=True)

    if result.returncode != 0:
        print(f"[ERROR] ffmpeg failed: {result.stderr}")
        return False
    return True


def send_to_discord(date_str: str, events: list[dict], reel_path: Path | None, dry_run: bool = False):
    """Send daily digest summary + highlight reel to Discord."""

    # Build summary text
    by_camera = {}
    by_label  = {}
    for e in events:
        cam   = e.get("camera", "unknown")
        label = e.get("label", "unknown")
        by_camera[cam]   = by_camera.get(cam, 0) + 1
        by_label[label]  = by_label.get(label, 0) + 1

    camera_lines = "\n".join(f"  📹 **{cam}**: {n} events" for cam, n in sorted(by_camera.items()))
    label_lines  = "\n".join(f"  • {n}x {label}" for label, n in sorted(by_label.items(), key=lambda x: -x[1]))

    total   = len(events)
    weekday = datetime.strptime(date_str, "%Y-%m-%d").strftime("%A, %b %d")

    message = (
        f"📋 **Daily Motion Digest — {weekday}**\n\n"
        f"**{total} events detected**\n\n"
        f"**By camera:**\n{camera_lines}\n\n"
        f"**Objects detected:**\n{label_lines}\n"
    )

    if total == 0:
        message += "\n🌙 Quiet day — no motion detected."

    if dry_run:
        print("─" * 60)
        print("[DRY RUN] Would send to Discord:")
        print(message)
        if reel_path:
            print(f"[DRY RUN] Would attach: {reel_path} ({reel_path.stat().st_size // 1024}KB)")
        return

    if not WEBHOOK_URL:
        print("[ERROR] DISCORD_WEBHOOK_URL not set in .env")
        return

    # Send text message
    r = requests.post(WEBHOOK_URL, json={"content": message})
    if r.status_code not in (200, 204):
        print(f"[ERROR] Discord text send failed: {r.status_code} {r.text}")
        return
    print(f"[OK] Digest sent to Discord")

    # Send highlight reel if it exists and is small enough
    if reel_path and reel_path.exists():
        size = reel_path.stat().st_size
        if size <= MAX_CLIP_SIZE:
            with open(reel_path, "rb") as f:
                r = requests.post(WEBHOOK_URL, files={"file": (reel_path.name, f, "video/mp4")})
            if r.status_code in (200, 204):
                print(f"[OK] Highlight reel sent ({size // 1024}KB)")
            else:
                print(f"[ERROR] Failed to send reel: {r.status_code}")
        else:
            print(f"[WARN] Reel too large for Discord ({size // 1024 // 1024}MB), skipping")


def main():
    parser = argparse.ArgumentParser(description="Daily motion digest")
    parser.add_argument("--date",    default=datetime.now().strftime("%Y-%m-%d"), help="Date (YYYY-MM-DD)")
    parser.add_argument("--dry-run", action="store_true", help="Print summary without sending")
    args = parser.parse_args()

    print(f"[+] Fetching events for {args.date}...")
    events = get_events(args.date)
    print(f"[+] Found {len(events)} events")

    if not events:
        send_to_discord(args.date, [], None, args.dry_run)
        return

    # Sort by score, take top N
    events.sort(key=score_event, reverse=True)
    top_events = events[:MAX_CLIPS]
    print(f"[+] Top {len(top_events)} events selected for highlight reel")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        clips = []

        print("[+] Downloading clips...")
        for e in top_events:
            clip = download_clip(e, tmp_path)
            if clip:
                clips.append(clip)
                print(f"  ✓ {e['camera']} — {e['label']} ({int(e.get('top_score',0)*100)}%)")

        reel = None
        if clips:
            reel_path = tmp_path / f"digest_{args.date}.mp4"
            print(f"[+] Compiling highlight reel ({len(clips)} clips)...")
            if compile_highlight_reel(clips, reel_path):
                reel = reel_path
                print(f"[+] Reel: {reel.stat().st_size // 1024}KB")

        send_to_discord(args.date, events, reel, args.dry_run)


if __name__ == "__main__":
    main()
