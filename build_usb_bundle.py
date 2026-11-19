#!/usr/bin/env python3
"""Combine the published CN7NPE packages into a NEMESIS USB package list."""

import argparse
import hashlib
import io
import zipfile
from pathlib import Path

from build_package import MODULES, PACKAGE_PATH, RESET_HELPER_PATH, ROOT, archive, build_driver_package
from build_wireless_mod import BASE_SHA256 as WIRELESS_BASE_SHA256, verify_mod


PROJECTION = "packages/korea.projection.zip"
HMG_API = "packages/hmgapi.zip"
HMG_API_SHA256 = "7c7359dee1afafa512e38ad498798ac1c059765fd4710ddcc68b446e66a739b7"
USB_LIST = f"""[nemesis]
version=1.1
type=list

[package.0]
path={PROJECTION}
name=Korea Projection CN7NPE USB Test
short-desc=v1.7.4.16 - Waits for the USB AP before CarPlay

[package.1]
path={HMG_API}
name=HMG-API
short-desc=1.1.0-rc.4 - Korea Projection dependency

[package.2]
path={PACKAGE_PATH}
name=Realtek RTL8812BU USB Driver
short-desc=v1.1.13 - Korea Projection USB dependency
"""


def read_verified_release(path, expected_sha256):
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != expected_sha256:
        raise ValueError(f"Unexpected release ZIP SHA-256: {path}")
    return content


def read_package(installer, expected_sha256, path):
    with zipfile.ZipFile(io.BytesIO(read_verified_release(installer, expected_sha256))) as usb:
        return usb.read(path)


def add_hostapd_diagnostics(package):
    hotspot = package.read("svc/hotspot.sh")
    launch = b'''usb_start_hostapd() {
  (
    rc=0
    hostapd "$CONF" || rc=$?
    echo "hostapd exit=$rc"
  ) 2>&1 | '''
    status = package.read("bin/status.sh")
    reports = b"$W/usb-hostapd.log $W/carreport.txt"
    report_read = b"    if [ -f $_f ]; then lastmask 400 < $_f"
    ap_start = b'''  $BB ifconfig $WIF $AP_IP netmask 255.255.255.0 up 2>/dev/null
  if ! running "hostapd $CONF"; then
    usb_start_hostapd &'''
    ap_end = b'''  fi
  running "hostapd $CONF" || return 1
  if our_dhcp_on; then'''
    speed_check = b"""  for device in $(usb_a3000mini_paths); do
    for intf in "$device":*; do"""
    pending = b"""usb_launch_if_needed() {
  local paths device number device_key now launch_log rc
  paths=$(usb_a3000mini_paths)
  if [ -z "$paths" ] || usb_wifi_ready; then
    KP_USB_DEVICE=
    return 0
  fi"""
    if (any(hotspot.count(at) != 1 for at in (launch, ap_start, ap_end, pending, speed_check))
            or any(status.count(at) != 1 for at in (reports, report_read))):
        raise ValueError("Expected hostapd launch and report hooks in the base package")
    bundle = ROOT / "bundle"
    diagnostics = b"\n".join((bundle / name).read_bytes() for name in (
        "usb-ap-diagnostics.sh", "hostapd-logcat.sh", "usb-ap-recovery.sh",
    ))
    return {
        "svc/hotspot.sh": hotspot
        .replace(launch, diagnostics + b"\nusb_start_hostapd() {\n  usb_run_hostapd 2>&1 | ")
        .replace(pending, pending + b'\n  usb_ap_report_waiting "$paths"')
        .replace(speed_check, b'''  for device in $(usb_a3000mini_paths); do
    speed=
    read -r speed < "$device/speed" && [ "$speed" = 480 ] || continue
    for intf in "$device":*; do''')
        .replace(b"Waiting for A3000mini on rtwlan0. Korea Projection will try Realtek Launch.",
                 b"Waiting for A3000mini at USB 480Mbps. Check Realtek speed.log.")
        .replace(b"USB Realtek Launch: rtwlan0 ready (exit $rc)",
                 b"USB Realtek Launch: rtwlan0 ready at 480Mbps (exit $rc)")
        .replace(b"USB Realtek Launch: rtwlan0 still missing (exit $rc)",
                 b"USB Realtek Launch: USB Wi-Fi not ready at 480Mbps (exit $rc)")
        .replace(b'      log "USB AP ready: rtwlan0, hostapd and DHCP/1067"',
                 b'      usb_capture_running_hostapd\n      log "USB AP ready: rtwlan0, hostapd and DHCP/1067"')
        .replace(ap_start, b'''  usb_ap_context
  if [ -n "$AP_LAST_UP" ] && [ "$AP_LAST_UP" != "$AP_SCOPE" ]; then
    log "USB device changed: restarting our AP and DHCP."
    stop_ours
    "$BB" rm -f "$W/usb.ap.ready"
    _usb_stop_wait=0
    while running "hostapd $CONF"; do
      [ "$_usb_stop_wait" -lt 5 ] || return 1
      sleep 1
      _usb_stop_wait=$((_usb_stop_wait + 1))
    done
  fi
  if ! running "hostapd $CONF"; then
    usb_prepare_ap_interface || return 1
    AP_LAST_UP=$AP_SCOPE
    usb_wifi_ready || return 1
    sleep 2
    usb_start_hostapd &''')
        .replace(ap_end, b'''  elif [ "$AP_LAST_UP" != "$AP_SCOPE" ]; then
    usb_prepare_ap_interface || return 1
    AP_LAST_UP=$AP_SCOPE
    usb_capture_running_hostapd
  else
    $BB ifconfig $WIF $AP_IP netmask 255.255.255.0 up 2>/dev/null
''' + ap_end),
        "bin/status.sh": status.replace(
            reports,
            b"/data/nemesis/logs/realtek.88x2bu/speed.log $W/usb-hostapd.log $W/usb-ap-up-boot.log $W/usb-ap-up-replug.log "
            b"$W/usb-hostapd-permissions-boot.log $W/usb-hostapd-permissions-replug.log "
            b"$W/usb-hostapd-logcat-boot.log $W/usb-hostapd-logcat-replug.log $W/carreport.txt",
        ).replace(report_read, b'''    if [ -f "$_f" ]; then
      case "$_f" in
        /data/nemesis/logs/realtek.88x2bu/speed.log|"$W"/usb-ap-up-*.log|"$W"/usb-hostapd-permissions-*.log|"$W"/usb-hostapd-logcat-*.log)
          _report_boot=$(cat "${BOOT_ID:-/proc/sys/kernel/random/boot_id}" 2>/dev/null)
          read -r _diag_boot _ < "$_f"
          if [ -n "$_report_boot" ] && [ "$_diag_boot" != "boot=$_report_boot" ]; then
            echo "(No diagnostic snapshot for this boot.)"
            continue
          fi
          ;;
      esac
      lastmask 400 < "$_f"'''),
    }


def build_projection_package(source, wireless):
    with zipfile.ZipFile(io.BytesIO(source)) as package:
        descriptor = package.read("NEMESIS.data")
        descriptor = descriptor.replace(b"package-version=1.7.4.5\n", b"package-version=1.7.4.16\n")
        descriptor = descriptor.replace(
            b'depends="!niro.carplay.hotspot"\n',
            b'depends="hmgapi@>=1.0.99.4,realtek.88x2bu@>=1.1.13,!niro.carplay.hotspot"\n',
        )
        descriptor = descriptor.replace(
            b"CN7NPE KOR 260902, HMG-API and RTL8812BU v1.1.4 required.",
            b"CN7NPE KOR 260902. Requires HMG-API 1.1.0-rc.4+ and Realtek 1.1.13+.",
        )
        preinstall = package.read("scripts/preinstall.sh")
        preinstall = preinstall.replace(
            b"Install and launch the RTL8812BU driver v1.1.4 first.",
            b"Install the RTL8812BU driver v1.1.13 or later first.",
        )
        preinstall = preinstall.replace(
            rb"grep -q '^package-version=1\.7\.4\.[12345]$'",
            rb"grep -Eq '^package-version=1\.7\.4\.([1-9]|10|11|12|13|14|15|16)$'",
        )
        old_version_guard = b'''grep -q '"version": "2.4.6"' "$mod/META-HMGAPI/manifest.json"'''
        if preinstall.count(old_version_guard) != 1:
            raise ValueError('Expected existing-author mod upgrade guard')
        preinstall = preinstall.replace(old_version_guard,
            rb'''grep -Eq '"version": "2\.4\.[67]"' "$mod/META-HMGAPI/manifest.json"''')
        preinstall = preinstall.replace(
            b'''if [ -e "$mod/mod.json" ] &&
   ! { [ -r "$installed" ] && [ -f /data/nemesis/backup/korea.projection/mod.ours ] &&''',
            b'''# NEMESIS 1.16.7 removes the previous app tree before calling preinstall.
# The ownership marker survives an update along with the installed HMG-API mod.
if [ -e "$mod/mod.json" ] &&
   ! { [ -f /data/nemesis/backup/korea.projection/mod.ours ] &&''',
        )
        preinstall = preinstall.replace(
            b'''if ! hmgapid ping >/dev/null 2>&1; then
  echo "Install and start HMG-API 1.1.0-rc.3 first."
  exit 1
fi''',
            b'''# A newly installed HMG-API may still be starting its daemon.
hmgapi_wait=0
until hmgapid ping >/dev/null 2>&1; do
  if [ "$hmgapi_wait" -ge 15 ]; then
    echo "HMG-API is not responding. Restart the head unit and retry Korea Projection."
    exit 1
  fi
  sleep 1
  hmgapi_wait=$((hmgapi_wait + 1))
done''',
        )

        changes = add_hostapd_diagnostics(package)
        old_wireless = package.read('hmgapi/wireless-carplay-aa.zip')
        if hashlib.sha256(old_wireless).hexdigest() != WIRELESS_BASE_SHA256:
            raise ValueError('Expected the original CN7NPE wireless mod 2.4.6')
        verify_mod(wireless)
        hotspot = changes['svc/hotspot.sh']
        old_digest = hashlib.md5(old_wireless, usedforsecurity=False).hexdigest().encode()
        new_digest = hashlib.md5(wireless, usedforsecurity=False).hexdigest().encode()
        if hotspot.count(b'MOD_VER=2.4.6') != 1 or hotspot.count(b'MOD_MD5=' + old_digest) != 1:
            raise ValueError('Expected mod version and checksum installer hooks')
        changes['svc/hotspot.sh'] = hotspot.replace(b'MOD_VER=2.4.6', b'MOD_VER=2.4.7').replace(
            b'MOD_MD5=' + old_digest, b'MOD_MD5=' + new_digest)
        changes['hmgapi/wireless-carplay-aa.zip'] = wireless
        # Use the original source commit so the notice survives release tag cleanup.
        source_notice = package.read("licenses/Source.md")
        old_ref = b"/tree/kp-usb-test-v0.1.4/projection-usb"
        if source_notice.count(old_ref) != 1:
            raise ValueError("Expected the Korea Projection source link in the base package")
        changes["licenses/Source.md"] = source_notice.replace(
            old_ref, b"/tree/5b0d60ed47baf868714954b6290123a702d6a5e9/projection-usb",
        ) + b'\nWireless mod 2.4.7 AP readiness ordering source (AGPL-3.0):\nhttps://github.com/Seikoz/nemesis-rtl8812bu-gen5w/tree/cn7npe-usb-bundle-v0.1.11/projection-source\n'
        changes["NEMESIS.data"] = descriptor
        changes["scripts/preinstall.sh"] = preinstall
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as updated:
            for entry in package.infolist():
                data = changes[entry.filename] if entry.filename in changes else package.read(entry)
                updated.writestr(entry, data)
        return output.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("driver", type=Path, help="Published Realtek v1.1.7 USB ZIP (reset helper)")
    parser.add_argument("projection", type=Path, help="Published Korea Projection 1.7.4.5 USB ZIP (base package)")
    parser.add_argument("hmg_api", type=Path, help="Official HMG-API 1.1.0-rc.4 NEMESIS package ZIP")
    parser.add_argument(
        "-o", "--output", type=Path,
        default=ROOT / "dist" / "NEMESIS-CN7NPE-260902-Bundle-v0.1.11-USB.zip",
    )
    parser.add_argument(
        "--diagnostic-modules", required=True, type=Path,
        help="Directory containing both 3.18.24-tcc modules built by driver-source/rebuild.sh",
    )
    parser.add_argument("--usb-reset-helper", required=True, type=Path,
                        help="Android ARMv7 helper with the scoped EHCI recovery command")
    parser.add_argument('--wireless-mod', required=True, type=Path,
                        help='Same-author signed wireless mod 2.4.7 with the AP readiness gate')
    args = parser.parse_args()
    try:
        driver_base = read_package(
            args.driver, "18e888442d26120c5b928e81427040f1586e6ec556f279bb7149b73e486a6596", PACKAGE_PATH,
        )
        with zipfile.ZipFile(io.BytesIO(driver_base)) as source:
            modules = {name: (args.diagnostic_modules / Path(name).name).read_bytes() for name in MODULES}
            helper = args.usb_reset_helper.read_bytes()
            if helper == source.read(RESET_HELPER_PATH):
                raise ValueError("The reference release helper does not include EHCI recovery")
            driver = build_driver_package(modules, helper, diagnostics=True)
        projection_base = read_package(
            args.projection, "7a41ef0f5a1e3ad4db427bd028291f1300c3449e38821179a9bc0961cb873495", PROJECTION,
        )
        guide = ROOT / "bundle"
        bundle = archive({
            "NEMESIS.data": USB_LIST.encode("ascii"),
            "INSTALL-KO.md": (guide / "INSTALL-KO.md").read_bytes(),
            "licenses/HMG-API-AGPL-3.0.txt": (guide / "licenses" / "HMG-API-AGPL-3.0.txt").read_bytes(),
            PACKAGE_PATH: driver,
            PROJECTION: build_projection_package(projection_base, args.wireless_mod.read_bytes()),
            HMG_API: read_verified_release(args.hmg_api, HMG_API_SHA256),
        })
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(bundle)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        parser.exit(1, f"Build failed: {error}\n")
    print(f"Built {args.output}")
    print(f"SHA-256 {hashlib.sha256(bundle).hexdigest()}")


if __name__ == "__main__":
    main()
