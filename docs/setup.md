# Full Setup Guide

## Step 1 — Install Docker & NVIDIA Toolkit

```bash
sudo bash scripts/install_docker.sh
# Log out and back in after this
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi   # verify GPU works
```

## Step 2 — Configure Environment

```bash
cp .env.example .env
nano .env
# Fill in: DISCORD_WEBHOOK_URL
```

To get a Discord webhook:
1. Open Discord → your server → any channel → Edit Channel → Integrations → Webhooks
2. Create Webhook → Copy URL → paste into `.env`

## Step 3 — Configure Frigate

```bash
cp frigate/config.example.yml frigate/config.yml
nano frigate/config.yml
```

Replace camera RTSP URLs with your actual camera IPs. For Reolink cameras:
```
rtsp://admin:PASSWORD@192.168.1.X:554/h264Preview_01_main
```

## Step 4 — Create Storage Directories

```bash
mkdir -p storage/clips storage/recordings logs
```

## Step 5 — Test with Phone (Before Cameras Arrive)

```bash
# Install "IP Webcam" on Android, start the server
bash scripts/test_stream.sh 192.168.1.X   # your phone's IP
```

Visit http://localhost:5000 — you should see your phone feed with detection overlay.

## Step 6 — Launch Production Stack

```bash
docker compose up -d
docker compose logs -f frigate   # watch logs
```

## Step 7 — Set Up Daily Digest Cron

```bash
bash scripts/setup_cron.sh
```

## Step 8 — Test Digest

```bash
# Dry run (no Discord send)
python3 scripts/daily_digest.py --dry-run

# Real run
python3 scripts/daily_digest.py
```

## Verify GPU is Being Used

```bash
watch -n1 nvidia-smi
# Walk in front of a camera — GPU utilization should spike briefly
```
