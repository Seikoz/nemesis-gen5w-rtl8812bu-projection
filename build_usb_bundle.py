#!/usr/bin/env python3
"""Combine the published CN7NPE packages into a NEMESIS USB package list."""

import argparse
import hashlib
import io
import struct
import zipfile
from pathlib import Path

from build_package import MODULES, PACKAGE_PATH, RESET_HELPER_PATH, ROOT, archive, build_driver_package
from build_wireless_mod import BASE_SHA256 as WIRELESS_BASE_SHA256, verify_mod


PROJECTION = "packages/korea.projection.zip"
HMG_API = "packages/hmgapi.zip"
HMG_API_SHA256 = "16bea991f1c541acccea658f766971fac0b9d41caf34d6ca7523c9007fc41a63"
USB_LIST = f"""[nemesis]
version=1.1
type=list

[package.0]
path={PROJECTION}
name=Korea Projection CN7NPE BETA
short-desc=v1.7.4.27 - Installs HMG-API, wireless mode and Realtek driver

[package.1]
path={HMG_API}
name=HMG-API
short-desc=1.1.0-rc.7 - Core runtime and mod manager

[package.2]
path={PACKAGE_PATH}
name=Realtek Wi-Fi Driver
short-desc=v1.1.17 - RTL8812BU USB Wi-Fi driver
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
    # Existing report entries are extended after the hostapd/status integration.
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
    driver_timeout = b'"$BB_OWN" timeout 20 /system/xbin/nemesis pkg-launch realtek.88x2bu'
    if (any(hotspot.count(at) != 1 for at in (launch, ap_start, ap_end, pending, speed_check))
            or hotspot.count(driver_timeout) != 1
            or any(status.count(at) != 1 for at in (reports, report_read))):
        raise ValueError("Expected hostapd launch and report hooks in the base package")
    bundle = ROOT / "bundle"
    diagnostics = b"\n".join((bundle / name).read_bytes() for name in (
        "usb-ap-diagnostics.sh", "hostapd-logcat.sh", "usb-ap-recovery.sh",
    ))
    return {
        "svc/hotspot.sh": hotspot
        .replace(driver_timeout, driver_timeout.replace(b'timeout 20', b'timeout 90'))
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


def add_station_counts(hotspot):
    start = hotspot.index(b'\nwifi_events() {') + 1
    end = hotspot.index(b'\n}\n', start) + 3
    # Replace the vendor log accumulator, including its stale restart cache.
    hotspot = hotspot[:start] + (ROOT / 'bundle/usb-stations.sh').read_bytes() + hotspot[end:]
    for old, new, count in (
        (b'[ "$HA" = ok ] && [ -n "$WGONE" ]',
         b'[ "${STA_COUNT:-unknown}" != unknown ] && [ "$HA" = ok ] && [ -n "$WGONE" ]', 1),
        (b'if [ "$HA" = ok ] && [ "${WSTA:-0}" = 0 ]; then',
         b'if [ "${STA_COUNT:-unknown}" != unknown ] && [ "$HA" = ok ] && [ "${WSTA:-0}" = 0 ]; then', 1),
        (b'if [ -n "$IPH_AT" ]; then',
         b'if [ -n "$IPH_AT" ] && [ "${STA_COUNT:-unknown}" != unknown ]; then', 1),
        (b'sta=${WSTA:-0} rx=', b'sta=${STA_COUNT:-unknown} sta_source=${STA_SOURCE:-unavailable} rx=', 1),
        (b'wifi_events; aa_events; cp_watch', b'wifi_events; usb_client_progress; aa_events; cp_watch', 2),
    ):
        if hotspot.count(old) != count:
            raise ValueError(f'Expected station counter integration hook: {old[:80]}')
        hotspot = hotspot.replace(old, new)
    start = hotspot.index(b'\nmain() {')
    end = hotspot.index(b'\n}\n', start)
    main = hotspot[start:end]
    old_ready = 'prog 100 done "무선 카플레이·안드로이드 오토 준비됨."'.encode()
    if main.count(old_ready) != 1:
        raise ValueError('Expected the main loop AP readiness message')
    hotspot = hotspot[:start] + main.replace(old_ready, b'USB_CLIENT_DISPLAY=; usb_client_progress') + hotspot[end:]
    return hotspot


def add_network_upgrade(hotspot):
    update = '  log "무선 모드 업데이트함: $_iv → $MOD_VER"\n'.encode()
    if hotspot.count(update) != 1:
        raise ValueError('Expected successful wireless mod upgrade hook')
    hotspot = hotspot.replace(update, update + b'''  if usb_target && ! usb_network allow > "$W/usb-network.log" 2>&1; then
    log "USB wireless network setup failed; see usb-network.log."
    return 1
  fi
''')
    start = hotspot.index(b'\nplan_only_mod() {') + 1
    end = hotspot.index(b'\n}\n', start) + 3
    hotspot = hotspot[:start] + (ROOT / 'bundle/usb-mod-plan.sh').read_bytes() + b'\n' + (
        ROOT / 'bundle/usb-audio-apply.sh').read_bytes() + hotspot[end:]
    worker = b'  if ! fix_running; then\n    fix_perms &'
    if hotspot.count(worker) != 1:
        raise ValueError('Expected delayed permission worker')
    hotspot = hotspot[:start] + (ROOT / 'bundle/usb-boot-setup.sh').read_bytes() + b'\n' + hotspot[start:]
    hotspot = hotspot.replace(worker, b'''  if ! fix_running && ! usb_boot_setup_complete; then
    log "USB boot: using delayed HMG-API setup and permission checks."
    fix_perms &''')
    gate = '  # 시계가 맞춰진 뒤의 시각으로 다시 잡는다(경과 시간)\n'.encode()
    if hotspot.count(gate) != 1:
        raise ValueError('Expected startup gate after live USB readiness')
    hotspot = hotspot.replace(gate, '''  log "USB readiness passed: rtwlan0 and 480Mbps; checking wireless/audio setup."
  usb_audio_reconcile > "$W/usb-audio-apply.log" 2>&1
  _usb_audio_rc=$?
  case "$_usb_audio_rc" in
    1)
      log "USB audio support applied; AP waits for reboot."
      prog 100 reboot "오디오 지원 파일을 자동 적용했습니다. 지금 재부팅을 눌러 주세요."
      idle_req ;;
    2)
      log "USB audio setup blocked: $USB_AUDIO_STATUS; see usb-audio-apply.log."
      prog 100 fail "오디오 자동 적용을 보류했습니다. HMG-API 변경 사항과 제보 로그를 확인해 주세요."
      idle_req ;;
  esac
'''.encode() + gate)
    at = b'''  if plan_nothing; then
    return 0
  fi'''
    if hotspot.count(at) != 1:
        raise ValueError('Expected wireless-mod update plan hook')
    return hotspot.replace(at, at + b'''
  if usb_target && plan_only_mod; then
    if hmgapid engine apply > "$W/mod-apply.txt" 2>&1; then
      log "USB wireless mod policy applied automatically."
      return 0
    fi
    log "USB wireless mod policy apply failed; see mod-apply.txt."
  fi''')


def add_session_diagnostics(hotspot, status):
    start = hotspot.index(b'\ncp_count() {') + 1
    end = hotspot.index(b'\n}\n', hotspot.index(b'\ncp_watch() {', start)) + 3
    definitions = b'\n'.join((ROOT / 'bundle' / name).read_bytes() for name in (
        'usb-carplay-session.sh', 'usb-connection-diagnostics.sh'))
    hotspot = hotspot[:start] + definitions + b'\n' + hotspot[end:]
    anchor = b'  if [ "$_a" = "$(getprop $AAPROP 2>/dev/null)" ]; then'
    if hotspot.count(anchor) != 1:
        raise ValueError('Expected AP property generation hook')
    hotspot = hotspot.replace(anchor, b'  usb_cp_generation "$_a"\n' + anchor)
    anchor = b'logs() {\n'
    if status.count(anchor) != 1:
        raise ValueError('Expected report collection hook')
    status = status.replace(anchor, anchor + b'  usb_cp_poll\n  usb_ap_live && usb_connection_snapshot report\n')
    anchor = b'$W/usb-hostapd.log '
    if status.count(anchor) != 1:
        raise ValueError('Expected report file list')
    status = status.replace(anchor, anchor + b'$W/usb-carplay-events.log $W/usb-cp-capture.log $W/usb-connection-first.log $W/usb-connection-latest.log ')
    status = status.replace(b'"$W"/usb-ap-up-*.log|',
                            b'"$W"/usb-carplay-events.log|"$W"/usb-cp-capture.log|"$W"/usb-connection-*.log|"$W"/usb-ap-up-*.log|')
    anchor = b'      lastmask 400 < "$_f"'
    if status.count(anchor) != 1:
        raise ValueError('Expected report snapshot size hook')
    status = status.replace(anchor, b'      case "$_f" in "$W"/usb-connection-*.log) lastmask 1400 < "$_f" ;; *) lastmask 400 < "$_f" ;; esac')
    anchor = b'  echo "cp_conn=$K_CP"'
    if status.count(anchor) != 1:
        raise ValueError('Expected report session summary')
    status = status.replace(anchor, anchor + b'\n  usb_cp_read\n  echo "cp_session=$CP_STATE"\n  echo "cp_source=$CP_SOURCE"')
    anchor = '  echo "- 지금 카플레이 연결 수: $K_CP"'.encode()
    status = status.replace(anchor, anchor + '\n  usb_cp_read\n  echo "- 카플레이 세션 판정: $CP_STATE ($CP_SOURCE)"'.encode())
    return hotspot, status


def build_projection_package(source, wireless, station_counter, link_diagnostics):
    if (station_counter[:6] != b'\x7fELF\x01\x01' or len(station_counter) < 20 or
            struct.unpack_from('<HH', station_counter, 16) != (3, 40) or
            b'/system/bin/linker\0' not in station_counter or
            b'/data/misc/wifi/hostapd-kp-usb/rtwlan0\0' not in station_counter):
        raise ValueError('Expected the Android ARMv7 AP station counter')
    if (link_diagnostics[:6] != b'\x7fELF\x01\x01' or len(link_diagnostics) < 20 or
            struct.unpack_from('<HH', link_diagnostics, 16) != (3, 40) or
            b'/system/bin/linker\0' not in link_diagnostics or b'_carplay-ctrl._tcp.local\0' not in link_diagnostics):
        raise ValueError('Expected the Android ARMv7 mDNS diagnostics helper')
    with zipfile.ZipFile(io.BytesIO(source)) as package:
        descriptor = package.read("NEMESIS.data")
        descriptor = descriptor.replace(b"package-version=1.7.4.5\n", b"package-version=1.7.4.27\n")
        descriptor = descriptor.replace(
            b'depends="!niro.carplay.hotspot"\n',
            b'depends="hmgapi@>=1.0.99.7,realtek.88x2bu@>=1.1.17,!niro.carplay.hotspot"\n',
        )
        descriptor = descriptor.replace(
            b"CN7NPE KOR 260902, HMG-API and RTL8812BU v1.1.4 required.",
            b"CN7NPE KOR 260902. Requires HMG-API 1.1.0-rc.7+ and Realtek 1.1.17+.",
        )
        descriptor = descriptor.replace(b'name=Korea Projection CN7NPE USB Test\n', b'name=Korea Projection CN7NPE BETA\n')
        preinstall = package.read("scripts/preinstall.sh")
        preinstall = preinstall.replace(
            b"grep -q '^name=Korea Projection CN7NPE USB Test$'",
            b"grep -Eq '^name=Korea Projection CN7NPE (USB Test|BETA)$'",
        )
        preinstall = preinstall.replace(
            b"Install and launch the RTL8812BU driver v1.1.4 first.",
            b"Install the RTL8812BU driver v1.1.17 or later first.",
        )
        preinstall = preinstall.replace(
            rb"grep -q '^package-version=1\.7\.4\.[12345]$'",
            rb"grep -Eq '^package-version=1\.7\.4\.([1-9]|10|11|12|13|14|15|16|17|18|19|20|21|22|23|24|25|26|27)$'",
        )
        old_version_guard = b'''grep -q '"version": "2.4.6"' "$mod/META-HMGAPI/manifest.json"'''
        if preinstall.count(old_version_guard) != 1:
            raise ValueError('Expected existing-author mod upgrade guard')
        preinstall = preinstall.replace(old_version_guard,
            rb'''grep -Eq '"version": "2\.4\.([6-9]|10|11|12|13)"' "$mod/META-HMGAPI/manifest.json"''')
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
        hotspot = add_network_upgrade(add_station_counts(changes['svc/hotspot.sh']))
        hotspot, changes['bin/status.sh'] = add_session_diagnostics(hotspot, changes['bin/status.sh'])
        changes['bin/status.sh'] = changes['bin/status.sh'].replace(b'$W/mod-apply.txt', b'$W/mod-apply.txt $W/usb-audio-apply.log $W/usb-mod-files-check.log $W/usb-boot-setup.log')
        old_digest = hashlib.md5(old_wireless, usedforsecurity=False).hexdigest().encode()
        new_digest = hashlib.md5(wireless, usedforsecurity=False).hexdigest().encode()
        if hotspot.count(b'MOD_VER=2.4.6') != 1 or hotspot.count(b'MOD_MD5=' + old_digest) != 1:
            raise ValueError('Expected mod version and checksum installer hooks')
        changes['svc/hotspot.sh'] = hotspot.replace(b'MOD_VER=2.4.6', b'MOD_VER=2.4.13').replace(
            b'MOD_MD5=' + old_digest, b'MOD_MD5=' + new_digest)
        changes['hmgapi/wireless-carplay-aa.zip'] = wireless
        with zipfile.ZipFile(io.BytesIO(wireless)) as signed_mod:
            checksums = ''.join(hashlib.md5(signed_mod.read(name), usedforsecurity=False).hexdigest() +
                                '  ' + name + '\n' for name in sorted(signed_mod.namelist()))
        # Use the original source commit so the notice survives release tag cleanup.
        source_notice = package.read("licenses/Source.md")
        old_ref = b"/tree/kp-usb-test-v0.1.4/projection-usb"
        if source_notice.count(old_ref) != 1:
            raise ValueError("Expected the Korea Projection source link in the base package")
        changes["licenses/Source.md"] = source_notice.replace(b"Korea Projection CN7NPE USB Test", b"Korea Projection CN7NPE BETA").replace(
            old_ref, b"/tree/5b0d60ed47baf868714954b6290123a702d6a5e9/projection-usb",
        ) + b'\nWireless mod 2.4.13 session callbacks, scoped TCP/UDP policy and link diagnostic sources (AGPL-3.0):\nhttps://github.com/Seikoz/nemesis-rtl8812bu-gen5w/tree/cn7npe-usb-bundle-v0.1.22/projection-source\nhttps://github.com/Seikoz/nemesis-rtl8812bu-gen5w/tree/cn7npe-usb-bundle-v0.1.22/bundle\n'
        changes["NEMESIS.data"] = descriptor
        changes["scripts/preinstall.sh"] = preinstall
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as updated:
            for entry in package.infolist():
                data = changes[entry.filename] if entry.filename in changes else package.read(entry)
                updated.writestr(entry, data)
            for name, data in (('ap-station-count', station_counter), ('ap-link-diagnostics', link_diagnostics)):
                entry = zipfile.ZipInfo('bin/' + name, date_time=(1980, 1, 1, 0, 0, 0))
                entry.create_system = 3
                entry.external_attr = 0o100755 << 16
                updated.writestr(entry, data, compress_type=zipfile.ZIP_DEFLATED)
            entry = zipfile.ZipInfo('hmgapi/usb-mod-files.md5', date_time=(1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            updated.writestr(entry, checksums.encode('ascii'), compress_type=zipfile.ZIP_DEFLATED)
        return output.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("driver", type=Path, help="Published Realtek v1.1.7 USB ZIP (reset helper)")
    parser.add_argument("projection", type=Path, help="Published Korea Projection 1.7.4.5 USB ZIP (base package)")
    parser.add_argument("hmg_api", type=Path, help="Official HMG-API 1.1.0-rc.7 NEMESIS package ZIP")
    parser.add_argument(
        "-o", "--output", type=Path,
        default=ROOT / "dist" / "NEMESIS-CN7NPE-260902-Bundle-v0.1.22-USB.zip",
    )
    parser.add_argument(
        "--diagnostic-modules", required=True, type=Path,
        help="Directory containing both 3.18.24-tcc modules built by driver-source/rebuild.sh",
    )
    parser.add_argument("--usb-reset-helper", required=True, type=Path,
                        help="Android ARMv7 helper with the scoped EHCI recovery command")
    parser.add_argument('--wireless-mod', required=True, type=Path,
                        help='Same-author signed wireless mod 2.4.13 with session callbacks and local TCP/UDP rules')
    parser.add_argument('--station-counter', required=True, type=Path,
                        help='Android ARMv7 read-only hostapd station counter')
    parser.add_argument('--link-diagnostics', required=True, type=Path,
                        help='Android ARMv7 bounded mDNS diagnostic probe')
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
            PROJECTION: build_projection_package(projection_base, args.wireless_mod.read_bytes(), args.station_counter.read_bytes(), args.link_diagnostics.read_bytes()),
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
