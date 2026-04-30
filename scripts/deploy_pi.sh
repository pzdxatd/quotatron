#!/usr/bin/env bash
# Cross-compile the production venv for Pi Zero W in Docker, then rsync and
# restart the service.  Run from project root inside WSL2:
#
#   bash scripts/deploy_pi.sh [pi@192.168.8.32] [password]
#   # or via make:
#   make deploy-pi PI_HOST=pi@192.168.8.32 PI_PASS=yourpassword
#
# TIP: Set up SSH keys once to avoid passwords entirely:
#   ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_pi   # skip if you have a key already
#   ssh-copy-id -i ~/.ssh/id_pi pi@192.168.8.32
#   # then just: make deploy-pi PI_HOST=pi@192.168.8.32
#
# First build: ~5 min (QEMU arm/v6 compiling Pillow + spidev).
# Subsequent builds: <30 s (Docker layer cache; re-runs only changed layers).
# Subsequent deploys after a source-only change: ~10 s (rsync diff).
set -euo pipefail

HOST="${1:-pi@quotatron.local}"
PI_PASS="${2:-${PI_PASS:-}}"     # password: 2nd arg or PI_PASS env var
IMAGE="quotatron-pizero:latest"
# Must be on the WSL2-native ext4 filesystem, NOT /mnt/c/ (NTFS).
# docker cp to NTFS silently mangles Unix symlinks and drops execute bits,
# which breaks the Python venv's bin/ directory entirely.
OUT="/tmp/quotatron-pi-build"

# ── SSH/rsync helpers ─────────────────────────────────────────────────────────
if [[ -n "$PI_PASS" ]]; then
  if ! command -v sshpass &>/dev/null; then
    echo "==> Installing sshpass (required for PI_PASS option)..."
    sudo apt-get install -y --no-install-recommends sshpass -qq
  fi
  export SSHPASS="$PI_PASS"
  SSH="sshpass -e ssh -o StrictHostKeyChecking=accept-new"
  RSYNC_RSH="sshpass -e ssh -o StrictHostKeyChecking=accept-new"
  SUDO_PREFIX="echo '$PI_PASS' | sudo -S"
else
  SSH="ssh"
  RSYNC_RSH="ssh"
  SUDO_PREFIX="sudo"
fi

# ── 0. Export pinned requirements from uv.lock ────────────────────────────────
# uv has no linux/arm/v6 wheel, so we give plain pip a frozen requirements.txt
# generated on the host (x86). -e lines (editable project) are stripped because
# the project is installed separately via `pip install -e .` inside the image.
#
# uv is Windows-only in this setup; WSL2's Windows PATH integration exposes it
# as uv.exe. Fall back to uv if somehow available natively in WSL2.
echo "==> Exporting requirements from uv.lock..."
if command -v uv.exe &>/dev/null; then
  uv.exe export --no-dev --extra hardware --no-hashes | grep -v "^-e " | tr -d '\r' > requirements-pi.txt
elif command -v uv &>/dev/null; then
  uv export --no-dev --extra hardware --no-hashes | grep -v "^-e " > requirements-pi.txt
else
  echo "ERROR: uv not found in WSL2 PATH and uv.exe (Windows) not reachable."
  echo ""
  echo "Fix: run this once from a Windows PowerShell / cmd terminal, then retry:"
  echo "  cd C:\\Users\\LCFR\\Desktop\\Quotatron"
  echo "  uv export --no-dev --extra hardware --no-hashes | Out-File requirements-pi.txt -Encoding utf8"
  echo ""
  echo "Or install uv inside WSL2 (one-time, doesn't affect Windows):"
  echo "  curl -LsSf https://astral.sh/uv/install.sh | sh && source \$HOME/.local/bin/env"
  exit 1
fi

# ── 1. Ensure QEMU arm/v6 binfmt is registered ────────────────────────────────
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
$SSH "$HOST" "mkdir -p ~/quotatron"

# .venv: exact mirror — must match the cross-compiled build
rsync -avz --delete --rsh="$RSYNC_RSH" "$OUT/.venv/" "$HOST:~/quotatron/.venv/"
# source + data: sync without delete so Pi-local edits (e.g. quotes) survive
rsync -avz --rsh="$RSYNC_RSH" src/     "$HOST:~/quotatron/src/"
rsync -avz --rsh="$RSYNC_RSH" config/  "$HOST:~/quotatron/config/"
rsync -avz --rsh="$RSYNC_RSH" content/ "$HOST:~/quotatron/content/"
rsync -avz --rsh="$RSYNC_RSH" systemd/ "$HOST:~/quotatron/systemd/"

# ── 5. Install service and restart ────────────────────────────────────────────
echo "==> Installing systemd unit and restarting..."
$SSH "$HOST" "
  $SUDO_PREFIX install -m 644 ~/quotatron/systemd/quotatron.service \
    /etc/systemd/system/quotatron.service
  $SUDO_PREFIX systemctl daemon-reload
  $SUDO_PREFIX systemctl enable quotatron
  $SUDO_PREFIX systemctl restart quotatron
"

echo ""
echo "Done.  Tail logs:  ssh $HOST 'journalctl -u quotatron -f'"
