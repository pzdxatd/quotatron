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
# uv may have been installed in a previous session; ensure PATH covers it.
export PATH="$HOME/.local/bin:$PATH"

echo "==> Fetching Waveshare e-paper driver..."
# The Waveshare repo path has shifted over time. Try a few candidates.
WAVESHARE_TARGET="$HERE/src/quotatron/display/_waveshare"
WAVESHARE_TMP="$(mktemp -d)"
trap 'rm -rf "$WAVESHARE_TMP"' EXIT

CLONED=0
for repo in "https://github.com/waveshare/e-Paper" "https://github.com/waveshareteam/e-Paper"; do
  echo "  trying $repo ..."
  if git clone --depth 1 "$repo" "$WAVESHARE_TMP" 2>&1 | tail -3; then
    CLONED=1
    echo "  cloned: $repo"
    break
  fi
  rm -rf "$WAVESHARE_TMP" && mkdir -p "$WAVESHARE_TMP"
done

if [[ "$CLONED" == "1" ]]; then
  # Discover the actual location of epd2in13_V3.py — the path moves around.
  FOUND=$(find "$WAVESHARE_TMP" -name "epd2in13_V3.py" -print -quit 2>/dev/null)
  if [[ -n "$FOUND" ]]; then
    SRC_DIR="$(dirname "$FOUND")"
    echo "  found driver at: ${SRC_DIR#$WAVESHARE_TMP/}"
    for f in epd2in13_V2.py epd2in13_V3.py epd2in13_V4.py epdconfig.py; do
      if [[ -f "$SRC_DIR/$f" ]]; then
        cp "$SRC_DIR/$f" "$WAVESHARE_TARGET/" && echo "    vendored $f"
      else
        echo "    MISSING $f in $SRC_DIR"
      fi
    done
  else
    echo "  ERROR: clone succeeded but no epd2in13_V3.py found in tree."
    echo "  Inspect: ls $WAVESHARE_TMP"
  fi
else
  echo "  WARN: could not clone Waveshare repo. Vendoring skipped."
  echo "  Manual fallback:"
  echo "    cd /tmp && git clone https://github.com/waveshare/e-Paper"
  echo "    find /tmp/e-Paper -name 'epd2in13*.py' -o -name 'epdconfig.py'"
  echo "    cp <those-files> $WAVESHARE_TARGET/"
fi

# Quick sanity check: does the wrapper instantiate? (Stubs raise RuntimeError.)
if python3 -c "from quotatron.display._waveshare.epd2in13_V3 import EPD; EPD()" 2>/dev/null; then
  echo "  OK: real driver vendored"
else
  echo "  WARN: stubs still in place. Display will fail to init at runtime."
  echo "        See manual fallback above."
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
