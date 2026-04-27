from pathlib import Path
import sys
sys.path.insert(0, "scripts")
from wifi_to_wpa import parse_profile, write_wpa_conf, ProfileResult


def test_parses_wpa3sae_profile_with_cleartext_psk(tmp_path: Path) -> None:
    xml = tmp_path / "p.xml"
    xml.write_text('''<?xml version="1.0"?>
<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
  <name>TestNet</name>
  <SSIDConfig><SSID><hex>54657374</hex><name>Test</name></SSID></SSIDConfig>
  <connectionType>ESS</connectionType>
  <connectionMode>auto</connectionMode>
  <MSM><security>
    <authEncryption><authentication>WPA3SAE</authentication><encryption>AES</encryption><useOneX>false</useOneX></authEncryption>
    <sharedKey><keyType>passPhrase</keyType><protected>false</protected><keyMaterial>secret123</keyMaterial></sharedKey>
  </security></MSM>
</WLANProfile>''')
    res = parse_profile(xml)
    assert res.kind == "ok"
    assert res.ssid == "TestNet"
    assert res.psk == "secret123"
    assert res.key_mgmt == "SAE WPA-PSK"


def test_skips_dpapi_protected() -> None:
    xml_text = '''<?xml version="1.0"?>
<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
  <name>X</name><SSIDConfig><SSID><name>X</name></SSID></SSIDConfig>
  <MSM><security>
    <authEncryption><authentication>WPA2PSK</authentication><encryption>AES</encryption><useOneX>false</useOneX></authEncryption>
    <sharedKey><keyType>passPhrase</keyType><protected>true</protected><keyMaterial>encrypted</keyMaterial></sharedKey>
  </security></MSM>
</WLANProfile>'''
    from io import StringIO
    res = parse_profile(StringIO(xml_text))
    assert res.kind == "skip"
    assert "DPAPI" in res.reason


def test_writes_priority_ordered_blocks(tmp_path: Path) -> None:
    profiles = [
        ProfileResult(kind="ok", ssid="A", psk="aaaaaaaa", key_mgmt="WPA-PSK", reason=""),
        ProfileResult(kind="ok", ssid="B", psk="bbbbbbbb", key_mgmt="WPA-PSK", reason=""),
    ]
    out = tmp_path / "wpa_supplicant.conf"
    write_wpa_conf(profiles, out, country="PL", prefer=["B"])
    text = out.read_text()
    # B comes before A because of --prefer
    assert text.index('ssid="B"') < text.index('ssid="A"')
    assert "priority=" in text
