#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "[deploy] Pulling latest changes..."
git pull

echo "[deploy] Restarting bot service..."
sudo systemctl restart clockbot

echo "[deploy] Done. Status:"
sudo systemctl status clockbot --no-pager -l
