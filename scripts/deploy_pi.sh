#!/usr/bin/env bash
# Cross-compile the production venv for Pi Zero W in Docker, then rsync and
# restart the service.  Run from project root inside WSL2:
#
#   bash scripts/deploy_pi.sh [pi@quotatron.local]
#
# First build: ~5 min (QEMU arm/v6 compiling Pillow + spidev).
# Subsequent builds: <30 s (Docker layer cache; re-runs only changed layers).
# Subsequent deploys after a source-only change: ~10 s (rsync diff).
set -euo pipefail

HOST="${1:-pi@quotatron.local}"
IMAGE="quotatron-pizero:latest"
OUT=".pi-build"

# ── 1. Ensure QEMU arm/v6 binfmt is registered ────────────────────────────────
# Docker Desktop on Windows pre-registers this; the command is idempotent.
echo "==> Registering arm/v6 QEMU binfmt..."
docker run --rm --privileged tonistiigi/binfmt --install arm 2>/dev/null || true

# ── 2. Cross-compile venv ──────────────────────────────────────────────────────
echo "==> Building linux/arm/v6 venv (first build caches deps; later builds are fast)..."
docker buildx build \
  --platform linux/arm/v6 \
  --load \
  -f Dockerfile.pizero \
  -t "$IMAGE" \
  .

# ── 3. Extract .venv from the image ───────────────────────────────────────────
echo "==> Extracting .venv..."
CID=$(docker create --platform linux/arm/v6 "$IMAGE")
rm -rf "$OUT" && mkdir -p "$OUT"
docker cp "$CID:/home/pi/quotatron/.venv" "$OUT/"
docker rm "$CID"

# ── 4. Sync to Pi ─────────────────────────────────────────────────────────────
echo "==> Syncing to $HOST..."
ssh "$HOST" "mkdir -p ~/quotatron"

# .venv: exact mirror — must match the cross-compiled build
rsync -avz --delete "$OUT/.venv/" "$HOST:~/quotatron/.venv/"
# source + data: sync without delete so Pi-local edits (e.g. quotes) survive
rsync -avz src/      "$HOST:~/quotatron/src/"
rsync -avz config/   "$HOST:~/quotatron/config/"
rsync -avz content/  "$HOST:~/quotatron/content/"
rsync -avz systemd/  "$HOST:~/quotatron/systemd/"

# ── 5. Install service and restart ────────────────────────────────────────────
echo "==> Installing systemd unit and restarting..."
ssh "$HOST" "
  sudo install -m 644 ~/quotatron/systemd/quotatron.service \
    /etc/systemd/system/quotatron.service
  sudo systemctl daemon-reload
  sudo systemctl enable quotatron
  sudo systemctl restart quotatron
"

echo ""
echo "Done.  Tail logs:  ssh $HOST 'journalctl -u quotatron -f'"
