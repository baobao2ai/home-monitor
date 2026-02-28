#!/usr/bin/env python3
"""
storage_manager.py — Auto-delete old clips and manage disk usage.

Runs daily via cron. Keeps the last N days of clips, removes the rest.
Also warns if disk usage exceeds threshold.

Usage:
    python3 storage_manager.py
    python3 storage_manager.py --dry-run       # show what would be deleted
    python3 storage_manager.py --days 14       # override retention days
"""

import os
import shutil
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

STORAGE_PATH    = Path(os.getenv("STORAGE_PATH", "./storage"))
RETENTION_DAYS  = int(os.getenv("CLIP_RETENTION_DAYS", "30"))
WARN_DISK_PCT   = 85   # Warn if disk usage exceeds this %
WEBHOOK_URL     = os.getenv("DISCORD_WEBHOOK_URL", "")


def check_disk():
    """Check disk usage and warn if over threshold."""
    try:
        usage = shutil.disk_usage(STORAGE_PATH)
        pct   = usage.used / usage.total * 100
        free_gb = usage.free / 1e9
        print(f"[DISK] {pct:.1f}% used, {free_gb:.1f}GB free")
        if pct > WARN_DISK_PCT and WEBHOOK_URL:
            import requests
            requests.post(WEBHOOK_URL, json={
                "content": f"⚠️ **Storage Warning**: Disk is {pct:.1f}% full ({free_gb:.1f}GB free). Consider increasing retention policy."
            })
        return pct
    except Exception as e:
        print(f"[WARN] Could not check disk: {e}")
        return 0


def delete_old_clips(retention_days: int, dry_run: bool = False) -> tuple[int, int]:
    """Delete clips older than retention_days. Returns (deleted_count, freed_bytes)."""
    cutoff    = datetime.now() - timedelta(days=retention_days)
    deleted   = 0
    freed     = 0

    clips_dir = STORAGE_PATH / "clips"
    if not clips_dir.exists():
        print(f"[WARN] Clips directory not found: {clips_dir}")
        return 0, 0

    for camera_dir in clips_dir.iterdir():
        if not camera_dir.is_dir():
            continue
        for clip in camera_dir.glob("*.mp4"):
            mtime = datetime.fromtimestamp(clip.stat().st_mtime)
            if mtime < cutoff:
                size = clip.stat().st_size
                if dry_run:
                    print(f"  [DRY] Would delete: {clip} ({size // 1024}KB, {mtime.date()})")
                else:
                    clip.unlink()
                    print(f"  [DEL] {clip.name} ({size // 1024}KB)")
                deleted += 1
                freed   += size

    return deleted, freed


def delete_old_recordings(retention_days: int, dry_run: bool = False) -> tuple[int, int]:
    """Delete continuous recording segments older than retention_days."""
    cutoff  = datetime.now() - timedelta(days=retention_days)
    deleted = 0
    freed   = 0

    rec_dir = STORAGE_PATH / "recordings"
    if not rec_dir.exists():
        return 0, 0

    # Frigate stores recordings as: recordings/YYYY-MM/DD/HH/MM.SS.mp4
    for f in rec_dir.rglob("*.mp4"):
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        if mtime < cutoff:
            size = f.stat().st_size
            if dry_run:
                print(f"  [DRY] Would delete recording: {f.name} ({size // 1024}KB)")
            else:
                f.unlink()
            deleted += 1
            freed   += size

    # Remove empty directories
    if not dry_run:
        for d in sorted(rec_dir.rglob("*"), reverse=True):
            if d.is_dir():
                try:
                    d.rmdir()   # only removes if empty
                except OSError:
                    pass

    return deleted, freed


def main():
    parser = argparse.ArgumentParser(description="Storage manager for home-monitor")
    parser.add_argument("--days",    type=int, default=RETENTION_DAYS, help="Retention days")
    parser.add_argument("--dry-run", action="store_true",               help="Simulate without deleting")
    args = parser.parse_args()

    print(f"[+] Storage manager running — retaining {args.days} days of clips")
    print(f"[+] Storage path: {STORAGE_PATH.absolute()}")
    if args.dry_run:
        print("[!] DRY RUN — nothing will be deleted")

    check_disk()

    print(f"\n[+] Cleaning clips older than {args.days} days...")
    d1, f1 = delete_old_clips(args.days, args.dry_run)

    print(f"\n[+] Cleaning recordings older than {args.days} days...")
    d2, f2 = delete_old_recordings(args.days, args.dry_run)

    total_deleted = d1 + d2
    total_freed   = (f1 + f2) / 1e6

    print(f"\n[✓] Done: {total_deleted} files deleted, {total_freed:.1f}MB freed")
    if args.dry_run:
        print("[!] Dry run — run without --dry-run to actually delete")


if __name__ == "__main__":
    main()
