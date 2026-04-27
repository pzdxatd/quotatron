#!/usr/bin/env bash
# Flash Pi OS Lite to an SD card and prep it with wifi + ssh.
# Run on a Linux dev machine (or WSL) as a user with sudo dd access.
set -euo pipefail

DEVICE="${1:-}"
IMG="${2:-${HOME}/Downloads/raspios_lite_armhf.img}"

if [[ -z "$DEVICE" ]]; then
  echo "Usage: $0 /dev/sdX [path/to/raspios_lite.img]"
  echo "       $0 \\\\\\\\.\\\\PhysicalDriveN [...]   # WSL"
  exit 2
fi

if [[ ! -f "$IMG" ]]; then
  echo "Image not found at $IMG"
  echo "Download from: https://www.raspberrypi.com/software/operating-systems/"
  exit 1
fi

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WIFI_CONF="$HERE/wifi_profiles/wpa_supplicant.conf"

if [[ ! -f "$WIFI_CONF" ]]; then
  echo "WARN: $WIFI_CONF missing -- Pi will boot without WiFi."
  echo "Run scripts/wifi_to_wpa.py first if you want pre-configured networks."
fi

echo "=== About to flash $IMG to $DEVICE ==="
echo "    THIS WILL DESTROY ALL DATA ON $DEVICE"
echo "    Press Enter to confirm, Ctrl-C to abort..."
read -r

sudo dd bs=4M if="$IMG" of="$DEVICE" conv=fsync status=progress
sync

echo "=== Mounting boot partition to inject wifi + ssh ==="
MNT=$(mktemp -d)
# Pi OS uses partition 1 for /boot. On Linux: ${DEVICE}1 (e.g. /dev/sdb1).
# On WSL with PhysicalDriveN, you'll need to adjust manually.
if sudo mount "${DEVICE}1" "$MNT" 2>/dev/null; then
  if [[ -f "$WIFI_CONF" ]]; then
    sudo install -m 600 "$WIFI_CONF" "$MNT/wpa_supplicant.conf"
    echo "  Wrote wpa_supplicant.conf"
  fi
  sudo touch "$MNT/ssh"
  echo "  Touched ssh (enables SSH on first boot)"
  sudo umount "$MNT"
  rmdir "$MNT"
else
  echo "  WARN: could not auto-mount boot partition. Mount ${DEVICE}1 manually"
  echo "        and copy $WIFI_CONF + an empty ssh file."
  rmdir "$MNT" 2>/dev/null || true
fi

echo
echo "=== Done. Insert into Pi and boot. After it comes up: ==="
echo "  ssh pi@<pi-ip>"
echo "  git clone <REPO_URL> ~/quotatron && cd ~/quotatron && ./scripts/install.sh"
