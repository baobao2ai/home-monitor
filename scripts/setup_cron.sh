#!/bin/bash
# setup_cron.sh — Install daily cron jobs for digest + storage manager
# Run once after setup: bash scripts/setup_cron.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON="python3"
LOG_DIR="$REPO_DIR/logs"

mkdir -p "$LOG_DIR"

# Daily digest at 11 PM
DIGEST_JOB="0 23 * * * cd $REPO_DIR && $PYTHON scripts/daily_digest.py >> $LOG_DIR/digest.log 2>&1"

# Storage manager at midnight
STORAGE_JOB="0 0 * * * cd $REPO_DIR && $PYTHON scripts/storage_manager.py >> $LOG_DIR/storage.log 2>&1"

# Add to crontab (avoid duplicates)
(crontab -l 2>/dev/null | grep -v "daily_digest\|storage_manager"; echo "$DIGEST_JOB"; echo "$STORAGE_JOB") | crontab -

echo "✅ Cron jobs installed:"
echo "  - Daily digest:   11:00 PM every day"
echo "  - Storage cleanup: 12:00 AM every day"
echo ""
echo "Logs: $LOG_DIR/"
echo ""
crontab -l | grep -E "daily_digest|storage_manager"
