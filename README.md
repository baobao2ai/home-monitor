# 🏠 Home & Office AI Monitoring System

AI-powered motion detection for home and office cameras. Detects people, animals, and vehicles — compiles daily highlight clips and sends them to Discord.

**Stack:** Frigate NVR · NVIDIA GPU · Docker · ffmpeg · Python

---

## Quick Start

```bash
# 1. Install Docker (requires sudo — run once)
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER   # add yourself to docker group
newgrp docker                   # apply without logout

# 2. Clone this repo
git clone https://github.com/baobao2ai/home-monitor.git
cd home-monitor

# 3. Edit your config
cp frigate/config.example.yml frigate/config.yml
# → Edit frigate/config.yml with your camera RTSP URLs

# 4. Set your Discord webhook
cp .env.example .env
# → Edit .env with DISCORD_WEBHOOK_URL

# 5. Launch everything
docker compose up -d

# 6. Open Frigate dashboard
open http://localhost:5000
```

---

## Repository Structure

```
home-monitor/
├── docker-compose.yml          # Full stack: Frigate + GPU
├── .env.example                # Environment variables template
├── frigate/
│   ├── config.example.yml      # Frigate camera + detection config
│   └── config.yml              # Your config (gitignored)
├── scripts/
│   ├── daily_digest.py         # Compile + send daily clip digest
│   ├── storage_manager.py      # Auto-delete old clips
│   ├── test_stream.sh          # Test with phone camera (IP Webcam)
│   └── install_docker.sh       # One-command Docker install
└── docs/
    ├── setup.md                # Full setup guide
    ├── cameras.md              # Camera placement & config guide
    └── troubleshooting.md      # Common issues & fixes
```

---

## Hardware Requirements

| Item | Recommended | Notes |
|------|-------------|-------|
| GPU | NVIDIA RTX 4090 | Already installed ✅ |
| Cameras | Reolink RLC-810A | 4x PoE, 4K |
| Switch | TP-Link TL-SG1008P | 8-port PoE |
| Storage | 4TB HDD | ~60 days of clips |

## Current Status

- [x] Repository structure
- [x] Docker Compose config (GPU passthrough)
- [x] Frigate config template
- [x] Daily digest script
- [x] Storage manager
- [x] Test stream helper
- [ ] Docker installed on host
- [ ] Cameras purchased & mounted
- [ ] Live stream configured
