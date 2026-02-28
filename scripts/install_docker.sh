#!/bin/bash
# install_docker.sh — One-command Docker + NVIDIA Container Toolkit install
# Run with: sudo bash scripts/install_docker.sh

set -e
echo "[+] Installing Docker..."
curl -fsSL https://get.docker.com | sh

echo "[+] Adding $SUDO_USER to docker group..."
usermod -aG docker "$SUDO_USER"

echo "[+] Installing NVIDIA Container Toolkit (for GPU passthrough)..."
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

apt-get update -qq
apt-get install -y nvidia-container-toolkit

echo "[+] Configuring Docker daemon for NVIDIA..."
nvidia-ctk runtime configure --runtime=docker
systemctl restart docker

echo ""
echo "✅ Done! Docker + NVIDIA GPU support installed."
echo ""
echo "Next steps:"
echo "  1. Log out and back in (or run: newgrp docker)"
echo "  2. Test GPU in Docker: docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi"
echo "  3. Then: docker compose up -d"
