# Troubleshooting

## GPU Not Being Used

**Symptom:** `nvidia-smi` shows 0% GPU during detection

```bash
# Check Frigate logs
docker compose logs frigate | grep -i "tensor\|cuda\|gpu"

# Verify NVIDIA container toolkit
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

# Fix: reinstall NVIDIA container toolkit
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

## Camera Stream Not Connecting

**Symptom:** Frigate shows "offline" for a camera

```bash
# Test RTSP URL directly
ffprobe -v quiet rtsp://admin:PASSWORD@192.168.1.101:554/h264Preview_01_main

# Common fixes:
# 1. Wrong password — check Reolink app settings
# 2. RTSP not enabled — enable in camera web UI (port 554)
# 3. Firewall — check router isn't blocking between devices
# 4. Try sub stream URL instead of main stream
```

## Frigate Using Too Much CPU

```yaml
# In config.yml — use sub stream for detect (lower resolution)
cameras:
  front_door:
    ffmpeg:
      inputs:
        - path: rtsp://...main   # 4K
          roles: [record]
        - path: rtsp://...sub    # 720p — much less CPU
          roles: [detect]
    detect:
      width: 1280
      height: 720
      fps: 5   # Lower FPS = less CPU
```

## Daily Digest Not Sending

```bash
# Test manually
python3 scripts/daily_digest.py --dry-run

# Check webhook URL
grep DISCORD_WEBHOOK_URL .env

# Check Frigate API
curl http://localhost:5000/api/events?limit=5

# Check logs
tail -50 logs/digest.log
```

## Storage Filling Up

```bash
# Check usage
df -h ./storage

# Dry run storage manager
python3 scripts/storage_manager.py --dry-run

# Reduce retention (default 30 days)
# Edit .env: CLIP_RETENTION_DAYS=14
python3 scripts/storage_manager.py --days 14
```

## False Positives (Too Many Alerts)

```yaml
# In config.yml — raise confidence thresholds
objects:
  filters:
    person:
      min_score: 0.75    # Raise from 0.6 to 0.75
      threshold: 0.8
    
# Add motion mask for areas causing false triggers (e.g. waving trees)
cameras:
  front_door:
    motion:
      mask:
        - 0,0,500,0,500,300,0,300   # Mask top-left corner
```
