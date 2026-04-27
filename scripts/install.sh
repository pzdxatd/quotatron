#!/usr/bin/env bash
# Quotatron on-Pi installer. Run as the `pi` user. Idempotent.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$HERE"

echo "==> Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y --no-install-recommends \
  python3 python3-pip python3-spidev python3-pil fonts-dejavu \
  git curl ca-certificates

echo "==> Disabling GUI (boot to CLI only)..."
sudo systemctl set-default multi-user.target
for svc in lightdm gdm gdm3 sddm; do
  if systemctl list-unit-files 2>/dev/null | grep -q "^${svc}.service"; then
    sudo systemctl disable "$svc" 2>/dev/null || true
    sudo systemctl stop "$svc" 2>/dev/null || true
  fi
done
# raspi-config: CLI auto-login (option B1), in case Pi OS Lite-with-desktop was flashed.
sudo raspi-config nonint do_boot_behaviour B1 2>/dev/null || true

echo "==> Enabling SPI..."
sudo raspi-config nonint do_spi 0

echo "==> Installing uv..."
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # uv installs to ~/.local/bin/uv; ensure PATH for this session.
  export PATH="$HOME/.local/bin:$PATH"
fi

echo "==> Fetching Waveshare e-paper driver..."
# The Waveshare repo path has shifted over time. Try a few candidates.
WAVESHARE_TARGET="$HERE/src/quotatron/display/_waveshare"
WAVESHARE_TMP="$(mktemp -d)"
trap 'rm -rf "$WAVESHARE_TMP"' EXIT

CANDIDATE_PATHS=(
  "RaspberryPi_JetsonNano_HATs/python/lib/waveshare_epd"
  "RaspberryPi/python/lib/waveshare_epd"
)

CLONED=0
if git clone --depth 1 https://github.com/waveshare/e-Paper "$WAVESHARE_TMP" 2>/dev/null; then
  CLONED=1
elif git clone --depth 1 https://github.com/waveshareteam/e-Paper "$WAVESHARE_TMP" 2>/dev/null; then
  CLONED=1
fi

if [[ "$CLONED" == "1" ]]; then
  for path in "${CANDIDATE_PATHS[@]}"; do
    if [[ -d "$WAVESHARE_TMP/$path" ]]; then
      cp "$WAVESHARE_TMP/$path"/{epd2in13_V2.py,epd2in13_V3.py,epd2in13_V4.py,epdconfig.py} \
         "$WAVESHARE_TARGET/" 2>/dev/null && {
        echo "  Vendored Waveshare driver from $path"
        break
      }
    fi
  done
fi

if ! python3 -c "from quotatron.display._waveshare.epd2in13_V3 import EPD; EPD()" 2>/dev/null; then
  echo "  WARN: Waveshare driver not available -- leaving stubs in place. Display will fail to init."
fi

echo "==> Syncing dependencies (production only)..."
uv sync --no-dev --extra hardware

echo "==> Installing wpa_supplicant.conf..."
if [[ -f wifi_profiles/wpa_supplicant.conf ]]; then
  sudo install -m 600 -o root -g root \
    wifi_profiles/wpa_supplicant.conf \
    /etc/wpa_supplicant/wpa_supplicant.conf
  sudo wpa_cli -i wlan0 reconfigure 2>/dev/null || true
  echo "  OK"
else
  echo "  SKIP: wifi_profiles/wpa_supplicant.conf missing -- connect WiFi manually"
fi

echo "==> Installing systemd unit..."
sudo install -m 644 systemd/quotatron.service /etc/systemd/system/quotatron.service
sudo systemctl daemon-reload
sudo systemctl enable --now quotatron

echo
echo "==> Done. Logs: journalctl -u quotatron -f"
