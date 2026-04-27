#!/usr/bin/env python3
"""One-time converter: Windows WiFi XML profiles -> wpa_supplicant.conf

Usage:
  uv run python scripts/wifi_to_wpa.py \
    --input "C:/Users/LCFR/Desktop/Format/wifi_profiles" \
    --output wifi_profiles/wpa_supplicant.conf \
    --country PL \
    [--prefer "Home_5G,Office"]
"""
from __future__ import annotations
import argparse
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET
from typing import IO, Union

NS = {"w": "http://www.microsoft.com/networking/WLAN/profile/v1"}

AUTH_MAP = {
    "WPA3SAE": "SAE WPA-PSK",
    "WPA2PSK": "WPA-PSK",
    "WPAPSK": "WPA-PSK",
    "open": "NONE",
}


@dataclass
class ProfileResult:
    kind: str   # "ok" | "skip"
    ssid: str
    psk: str
    key_mgmt: str
    reason: str


def parse_profile(src: Union[Path, IO[str]]) -> ProfileResult:
    if isinstance(src, (str, Path)):
        tree = ET.parse(str(src))
        root = tree.getroot()
    else:
        root = ET.fromstring(src.read())
    profile_name = root.find("w:name", NS)
    ssid_elem = root.find(".//w:SSID/w:name", NS)
    ssid_hex = root.find(".//w:SSID/w:hex", NS)
    if profile_name is not None and profile_name.text:
        ssid = profile_name.text
    elif ssid_hex is not None and ssid_hex.text:
        ssid = bytes.fromhex(ssid_hex.text).decode("utf-8", errors="replace")
    elif ssid_elem is not None and ssid_elem.text:
        ssid = ssid_elem.text
    else:
        return ProfileResult("skip", "", "", "", "no SSID")

    auth = root.find(".//w:authentication", NS)
    auth_text = auth.text if auth is not None else "open"
    if auth_text not in AUTH_MAP:
        return ProfileResult("skip", ssid, "", "", f"unsupported auth: {auth_text}")

    if auth_text == "open":
        return ProfileResult("ok", ssid, "", "NONE", "")

    protected = root.find(".//w:sharedKey/w:protected", NS)
    if protected is not None and protected.text == "true":
        return ProfileResult("skip", ssid, "", "", "DPAPI-encrypted")
    psk_elem = root.find(".//w:sharedKey/w:keyMaterial", NS)
    if psk_elem is None or not psk_elem.text:
        return ProfileResult("skip", ssid, "", "", "missing key")
    psk = psk_elem.text
    if not (8 <= len(psk) <= 63 or (len(psk) == 64 and all(c in "0123456789abcdefABCDEF" for c in psk))):
        return ProfileResult("skip", ssid, "", "", "invalid PSK length")

    return ProfileResult("ok", ssid, psk, AUTH_MAP[auth_text], "")


def write_wpa_conf(
    profiles: list[ProfileResult],
    out_path: Path,
    country: str = "PL",
    prefer: list[str] | None = None,
) -> None:
    prefer = prefer or []
    seen: dict[str, ProfileResult] = {}
    for p in profiles:
        if p.kind == "ok":
            seen[p.ssid] = p   # last wins (dedup)

    ordered: list[ProfileResult] = []
    for s in prefer:
        if s in seen:
            ordered.append(seen.pop(s))
    ordered.extend(seen.values())

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        f.write("ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n")
        f.write("update_config=1\n")
        f.write(f"country={country}\n\n")
        for i, p in enumerate(ordered):
            f.write("network={\n")
            f.write(f'    ssid="{p.ssid}"\n')
            f.write(f"    key_mgmt={p.key_mgmt}\n")
            if p.psk:
                f.write(f'    psk="{p.psk}"\n')
            f.write(f"    priority={max(1, len(ordered) - i)}\n")
            f.write("}\n\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Directory containing WiFi-*.xml files")
    parser.add_argument("--output", default="wifi_profiles/wpa_supplicant.conf")
    parser.add_argument("--country", default="PL")
    parser.add_argument("--prefer", default="", help="Comma-separated SSIDs to prefer")
    args = parser.parse_args()

    in_dir = Path(args.input)
    xmls = sorted(in_dir.glob("WiFi-*.xml"))
    profiles: list[ProfileResult] = []
    for x in xmls:
        try:
            profiles.append(parse_profile(x))
        except Exception as e:
            print(f"  FAIL {x.name}: parse error {e}")

    ok = [p for p in profiles if p.kind == "ok"]
    skipped = [p for p in profiles if p.kind == "skip"]
    write_wpa_conf(ok, Path(args.output), args.country,
                   [s.strip() for s in args.prefer.split(",") if s.strip()])
    print(f"OK {len(ok)} profiles converted")
    for p in skipped:
        print(f"WARN skipped {p.ssid}: {p.reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
