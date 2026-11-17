"""Build the signed CN7NPE USB installer from the pinned Korea Projection package."""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import uuid
import zipfile

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec


HERE = Path(__file__).resolve().parent
UPSTREAM_SHA256 = "d33dae33b27cad30d82b47dda557732780b4813c5d0815ed6f22b21c4d0a4315"
MOD = "wireless-carplay-aa"
MOD_VERSION = "2.4.6"
PACKAGE_VERSION = "1.7.4.1"
MOD_PATH = f"hmgapi/{MOD}.zip"
PACKAGE_PATH = "packages/korea.projection.zip"


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def read_zip(data):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        files = {}
        for item in archive.infolist():
            if item.is_dir():
                continue
            name = item.filename
            path = PurePosixPath(name)
            if path.is_absolute() or ".." in path.parts or "\\" in name or name in files:
                raise ValueError(f"Unsafe ZIP entry {name}")
            files[name] = archive.read(item)
        return files


def zip_bytes(files):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            entry = zipfile.ZipInfo(name)
            mode = 0o100755 if name.endswith(".sh") or name == "bin/busybox" else 0o100644
            entry.create_system = 3
            entry.external_attr = mode << 16
            archive.writestr(entry, data, compress_type=zipfile.ZIP_DEFLATED)
    return stream.getvalue()


def replace(text, old, new, count=1):
    if text.count(old) != count:
        raise ValueError(f"Unexpected upstream match count for {old[:80]}")
    return text.replace(old, new)


def function(text, name, body):
    pattern = rf"^({re.escape(name)}\(\) \{{\n).*?^\}}$"
    text, count = re.subn(pattern, lambda match: match[1] + body + "\n}", text,
                          flags=re.MULTILINE | re.DOTALL)
    if count != 1:
        raise ValueError(f"Expected one upstream function named {name}")
    return text


def encode_public_key(key):
    return key.public_key().public_bytes(serialization.Encoding.DER,
                                         serialization.PublicFormat.SubjectPublicKeyInfo)


def signing_key(path):
    if not path.exists():
        key = ec.generate_private_key(ec.SECP256R1())
        with path.open("xb") as out:
            out.write(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                        serialization.NoEncryption()))
    key = serialization.load_pem_private_key(path.read_bytes(), None)
    if not isinstance(key, ec.EllipticCurvePrivateKey) or not isinstance(key.curve, ec.SECP256R1):
        raise ValueError("Expected an HMG-API P-256 signing key")
    return key


def network_rules():
    carplay = ["5000-5001", 5020, "6000-6003", 6011, 6020, 6030, 7000]
    rules = [
        {"chain": "input", "in": "rtwlan0", "ip": 4, "proto": "udp",
         "source_ports": [68], "ports": [1067]},
        {"chain": "output", "out": "rtwlan0", "ip": 4, "proto": "udp",
         "source_ports": [1067], "ports": [68]},
        {"chain": "input", "in": "rtwlan0", "ip": 6, "proto": "icmpv6",
         "from": "fe80::/10"},
        {"chain": "input", "in": "rtwlan0", "ip": 6, "proto": "icmpv6",
         "from": "::/128", "icmp_type": "neighbor-solicitation"},
    ]
    for chain, direction, side in (("input", "in", "from"), ("output", "out", "to")):
        for prefix, multicast in (("192.168.43.0/24", "224.0.0.251"),
                                  ("fe80::/10", "ff02::fb")):
            interface = {"chain": chain, direction: "rtwlan0"}
            rules.append({**interface, side: prefix, "proto": "tcp+udp", "ports": carplay,
                          "both_ways": True})
            rules.append({**interface, side: prefix, "proto": "udp", "ports": [5353],
                          "both_ways": True})
            if chain == "output":
                rules.append({**interface, "to": multicast, "proto": "udp", "ports": [5353]})
    return [{**rule, "action": "accept"} for rule in rules]


def signed_mod(original, hooks, key):
    files = {name: data for name, data in read_zip(original).items()
             if not name.startswith("META-HMGAPI/")}
    mod = json.loads(files["mod.json"])
    if mod["id"] != MOD or mod["version"] != "2.4.5":
        raise ValueError("Unexpected upstream HMG-API mod")
    mod.update(name="Korea Projection CN7NPE USB test", version=MOD_VERSION,
               description="Wireless CarPlay on the Realtek USB hotspot for CN7NPE KOR 260902.",
               system=[{"model": ["CN7NPE"], "region": "KOR", "firmware": "260902"}],
               network={"rules": network_rules()})
    files["mod.json"] = json_bytes(mod)
    files["hooks.jar"] = hooks
    public = encode_public_key(key)
    author = bytearray(hashlib.sha256(public).digest()[:16])
    author[6] = (author[6] & 0x0F) | 0x80
    author[8] = (author[8] & 0x3F) | 0x80
    manifest = json_bytes({
        "format": 1, "id": MOD, "version": MOD_VERSION, "uuid": str(uuid.UUID(bytes=bytes(author))),
        "key": base64.b64encode(public).decode(),
        "files": {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())},
    })
    algorithm = ec.ECDSA(hashes.SHA256())
    signature = key.sign(manifest, algorithm)
    key.public_key().verify(signature, manifest, algorithm)
    files["META-HMGAPI/manifest.json"] = manifest
    files["META-HMGAPI/signature"] = base64.b64encode(signature) + b"\n"
    return zip_bytes(files)


def patch_service(text, mod):
    for old, new in (
        ('WIF=${WIF:-wlan0}', 'WIF=rtwlan0'),
        ('/data/misc/wifi/hostapd-kp.conf', '/data/misc/wifi/hostapd-kp-usb.conf'),
        ('ctrl_interface=/data/misc/wifi/hostapd', 'ctrl_interface=/data/misc/wifi/hostapd-kp-usb'),
        ('driver=nl80211\n', 'driver=nl80211\ncountry_code=KR\n'),
        ('MOD_MD5=3ae048506f637548561f09fd5e549337',
         f'MOD_MD5={hashlib.md5(mod, usedforsecurity=False).hexdigest()}'),
        ('MOD_VER=2.4.5', f'MOD_VER={MOD_VERSION}'),
        ('  up\n  aa_sig\n', '  up\n  usb_ap_progress\n  aa_sig\n'),
        ('    up\n    aa_sig\n', '    up\n    usb_ap_progress\n    aa_sig\n'),
        ('  if setup_done && { [ ! -f $PROG ]', '  if usb_ap_live && { [ ! -f $PROG ]'),
        ('main() {\n  umask 077\n', 'main() {\n  umask 077\n  usb_target || return 1\n'),
        ('  if ! car_in "$prod" "$CARS_OK"; then', '  if ! usb_target; then'),
        ('  elif setup_done; then prog 100 done ', '  elif usb_ap_live; then prog 100 done '),
    ):
        text = replace(text, old, new)
    text = replace(text, '--dhcp-authoritative --pid-file',
                   '--port=0 --dhcp-authoritative --dhcp-alternate-port=1067,68 --pid-file', 2)
    text = replace(text, 'up() {\n  $BB ifconfig',
                   'up() {\n  usb_wifi_ready || { stop_ours; return 1; }\n  $BB ifconfig')
    text = replace(text, '  if our_dhcp_on; then\n',
                   '  running "hostapd $CONF" || return 1\n  if our_dhcp_on; then\n', 1)
    text = replace(text, '    elif ptrack 70 run',
                   '    elif ! usb_network allow > "$W/usb-network.log" 2>&1; then\n'
                   '      _fail=1; LAST_MSG="HMG-API USB firewall setup failed (usb-network.log)."\n'
                   '    elif ptrack 70 run')
    text = replace(text, '  usb_seen_write\n', '  usb_seen_write\n'
                   '  if ! usb_wifi_ready; then\n'
                   '    prog 100 fail "Waiting for A3000mini on rtwlan0. Check Realtek driver Launch."\n'
                   '  fi\n'
                   '  while ! usb_wifi_ready; do\n'
                   '    sleep 2 & wait $!\n'
                   '  done\n')
    text = replace(text, '  parse_conf $SRC\n  if [ "${NS:-0}" -lt 4 ]',
                   '  while ! parse_conf "$SRC"; do\n'
                   '    prog 100 fail "Waiting for OEM CarPlay Wi-Fi credentials (usb-credentials.log)."\n'
                   '    sleep 15 & wait $!; req_tick\n'
                   '  done\n  if [ "${NS:-0}" -lt 4 ]')
    # The USB AP never takes ownership of stock wpa_supplicant or Wi-Fi settings.
    for name in ("take_wlan0", "wifi_lock", "wifi_unlock", "apon_off", "apon_restore",
                 "ap_tick", "wifi_restore_off", "stock_ap_mode"):
        text = function(text, name, "  return 0")
    text = function(text, "ap_yield", "  return 1")
    text = function(text, "try_ready", '  usb_target && setup_done && usb_wifi_ready && ! fix_running && ! prog_reboot_this_boot')
    text = function(text, "wifi_chip_seen", "  usb_wifi_ready")
    text = function(text, "wake_wifi", """  _kp_usb_wait=0
  while ! usb_wifi_ready; do
    [ "$_kp_usb_wait" -lt 15 ] || return 3
    _kp_usb_wait=$((_kp_usb_wait + 1))
    sleep 2
  done
  return 0""")
    text = function(text, "parse_conf", """  NS=0
  _kp_credentials=$(usb_setup credentials 2>"$W/usb-credentials.log") || return 1
  {
    IFS= read -r S2
    IFS= read -r S4
  } <<CREDENTIALS
$_kp_credentials
CREDENTIALS
  unset _kp_credentials
  [ -n "$S2" ] && [ "${#S4}" -ge 8 ] || return 1
  NS=4""")
    # The previous fallback scanned for any dnsmasq command on the unit.
    text = replace(text, '  elif [ ! -f $DNSPID ] && [ "${STOCK_MODE:-0}" != 1 ] && ! stock_ap_on; then\n'
                   '    for p in $($PS | $BB grep -v grep | $BB grep "$DNSMASQ" | $BB awk \'{print $1}\'); do\n'
                   '      by_netd $p || kill $p 2>/dev/null\n    done\n', '')
    text = replace(text, '[ "$HOTSPOT_LIB" = 1 ] || main',
                   (HERE / "usb_runtime.sh").read_text(encoding="utf-8") +
                   '\n[ "$HOTSPOT_LIB" = 1 ] || main')
    return re.sub(r'(?m)^WIFI_CHECK_MSG=.*$',
                  'WIFI_CHECK_MSG="USB Wi-Fi missing. Check A3000mini and RTL8812BU Launch, then restart."',
                  text)


def build(args):
    upstream = args.upstream.read_bytes()
    if hashlib.sha256(upstream).hexdigest() != UPSTREAM_SHA256:
        raise ValueError("Korea Projection release digest differs from v1.7.4")
    files = read_zip(upstream)
    compiled = read_zip(args.compiled.read_bytes())
    for name in ("hooks.jar", "setup.jar"):
        dex = read_zip(compiled[name])["classes.dex"]
        if not dex.startswith(b"dex\n035\0") or (name == "hooks.jar" and b"rtwlan0\0" not in dex):
            raise ValueError(f"Invalid Android API 19 DEX in {name}")
    files[MOD_PATH] = signed_mod(files[MOD_PATH], compiled["hooks.jar"], signing_key(args.key))
    files["hmgapi/setup.jar"] = compiled["setup.jar"]
    files["scripts/preinstall.sh"] = (HERE / "preinstall.sh").read_bytes().replace(b"\r\n", b"\n")
    files["svc/hotspot.sh"] = patch_service(files["svc/hotspot.sh"].decode(), files[MOD_PATH]).encode()
    status = files["bin/status.sh"].decode()
    status = replace(status, 'WIF=${WIF:-wlan0}', 'WIF=rtwlan0')
    status = replace(status, 'https://github.com/StopDragon/korea-projection/issues/new?template=car-report.yml',
                     'https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/issues')
    files["bin/status.sh"] = status.encode()
    uninstall = files["scripts/preun.sh"].decode()
    uninstall = replace(uninstall, 'if ! { has_bb && stock_ap_on; }; then $BB ifconfig wlan0 0.0.0.0 2>/dev/null; fi',
                        'if has_bb && usb_wifi_ready; then $BB ifconfig "$WIF" 0.0.0.0 2>/dev/null; fi')
    uninstall = replace(uninstall, '[ -f $BK/wifi_on ] && [ "$(cat $BK/wifi_on 2>/dev/null)" != 1 ] && svc wifi disable',
                        'if [ $modhold = 1 ] || [ -f "$HMGDATA/mods/$MOD_ID/mod.json" ] || ! usb_network restore; then\n'
                        '  echo "USB projection rollback is incomplete. Check HMG-API and retry uninstall."\n'
                        '  exit 1\n'
                        'fi')
    uninstall = re.sub(r'(?m)^if \[ -f \$BK/wifi_on \].*; then\n  settings put global wifi_on 1\nfi\n', '', uninstall)
    files["scripts/preun.sh"] = uninstall.encode()
    meta = files["NEMESIS.data"].decode()
    meta = replace(meta, 'name=Korea Projection: Wireless for Korean Cars', 'name=Korea Projection CN7NPE USB Test')
    meta = replace(meta, 'package-version=1.7.4', f'package-version={PACKAGE_VERSION}')
    meta = replace(meta, 'short-desc="Wireless CarPlay and Android Auto for Korean Hyundai/Kia cars"',
                   'short-desc="Experimental wireless CarPlay for CN7NPE 260902 and A3000mini"')
    meta = re.sub(r'(?ms)^detailed-desc=".*?"\nos=.*?\nmodels=.*?\n',
                  'detailed-desc="CN7NPE KOR 260902, HMG-API and RTL8812BU v1.1.4 required."\n'
                  'os="CN7NPE.KOR.*.260902"\nmodels="cn7npe_kr"\n', meta, count=1)
    meta = replace(meta, 'postinstall=scripts/post.sh', 'preinstall=scripts/preinstall.sh\npostinstall=scripts/post.sh')
    files["NEMESIS.data"] = meta.encode()
    upstream_source = read_zip(args.source.read_bytes())
    files["licenses/KoreaProjection-AGPL-3.0.txt"] = upstream_source["korea-projection-1.7.4/LICENSE"]
    files["licenses/Source.md"] = (HERE / "README.md").read_bytes()
    output = zip_bytes({
        "NEMESIS.data": f"[nemesis]\nversion=1.0\ntype=install\npath={PACKAGE_PATH}\n".encode(),
        PACKAGE_PATH: zip_bytes(files),
        "INSTALL-KO.md": (HERE / "README.md").read_bytes(),
    })
    args.output.write_bytes(output)
    print(f"SHA-256 {hashlib.sha256(output).hexdigest()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("upstream", "source", "compiled", "key", "output"):
        parser.add_argument(f"--{option}", required=True, type=Path)
    build(parser.parse_args())
