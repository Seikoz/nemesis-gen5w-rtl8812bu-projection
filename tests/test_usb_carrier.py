from pathlib import Path
import subprocess
import tempfile
import unittest

from test_usb_stations import ENV, SH


SCRIPT = (Path(__file__).resolve().parents[1] / 'bundle/usb-audio-carrier.sh').read_text(encoding='utf-8')
SETUP = r'''
set -e
PATH=$TEST_BIN
W="$PWD/log" BK="$PWD/backup" APP="$PWD/app" HMGDATA="$PWD/hmg" SYS_NET="$PWD/net"
BB=bb BB_OWN=bb BID=aaa1 MOD_ID=wireless-carplay-aa MOD_VER=2.4.21
PRODUCT=CN7NPE.KOR.0000.V039.001.260902 STOCK=cf3cc23dad25b181a9fc12d606468715
mkdir -p "$W" "$BK" "$APP/hmgapi" "$HMGDATA/mods" "$SYS_NET"
getprop() {
  case "$1" in
    ro.build.product) echo "$PRODUCT" ;;
    ro.board.platform) echo tcc803x ;;
  esac
}
mod_ver() { echo "${WIRELESS:-2.4.21}"; }
usb_ap_live() { [ "${LIVE:-0}" = 1 ]; }
usb_carplay_coreutils_probe() { USB_COREUTILS_MD5="$STOCK"; USB_COREUTILS_CHECK=fixture; }
bb() {
  case "$1" in
    timeout) shift 2; "$@" ;;
    sha256sum) read -r digest; echo "$digest  -" ;;
    *) command "$@" ;;
  esac
}
hmgapid() {
  echo "$2" >> "$W/calls"
  case "$2" in
    plan)
      echo 'same     /system/lib/libcarplayidentity.so [wireless-carplay-aa]'
      echo 'event    parked -> its apps and hooks hear it [wireless-carplay-aa]'
      echo 'network  firewall filter input: accept udp [wireless-carplay-aa]'
      echo 'home Wi-Fi  off'
      echo 'network  no cellular [nemesis-shortcut]'
      [ "${BLOCK:-0}" = 0 ] || echo 'change   /system/lib/other.so [other-mod]'
      return 0 ;;
    install)
      test "$5" = "$USB_CARRIER_AUTHOR" && test "$6" = --from-nemesis
      mkdir -p "$CARRIER/META-HMGAPI"
      echo "$USB_CARRIER_MANIFEST_SHA" > "$CARRIER/META-HMGAPI/manifest.json"
      [ "${INTERRUPT:-0}" = 0 ] ;;
    apply) [ "${FAIL_APPLY:-0}" = 0 ] ;;
    remove)
      test "$4" = --from-nemesis
      rm "$CARRIER/META-HMGAPI/manifest.json"
      rmdir "$CARRIER/META-HMGAPI" "$CARRIER" ;;
  esac
}
'''
FIXTURE = r'''
USB_CARRIER_ZIP_SHA=payload-check
USB_CARRIER_MANIFEST_SHA=manifest-check
USB_CARRIER_LEGACY_SHA=legacy-check
PAYLOAD="$APP/hmgapi/$USB_CARRIER_ID.zip"
CARRIER="$HMGDATA/mods/$USB_CARRIER_ID"
echo "$USB_CARRIER_ZIP_SHA" > "$PAYLOAD"
carrier_case() {
  rc=0
  usb_carrier_setup || rc=$?
  [ "$rc" = "$1" ]
}
legacy_carrier() {
  mkdir -p "$CARRIER/META-HMGAPI"
  echo "$USB_CARRIER_LEGACY_SHA" > "$CARRIER/META-HMGAPI/manifest.json"
}
'''


class AudioCarrierTest(unittest.TestCase):
    def run_case(self, script):
        with tempfile.TemporaryDirectory() as tmp:
            run = subprocess.run([SH, '-s'], input=(SETUP + SCRIPT + FIXTURE + script).encode(),
                                 env=ENV, cwd=tmp, capture_output=True, check=True)
            self.assertFalse(run.stderr, run.stderr)
            calls = Path(tmp) / 'log/calls'
            return calls.read_text().splitlines() if calls.is_file() else []

    def test_other_models_wrong_hash_and_active_hotspot_do_not_change_mods(self):
        self.assertEqual(self.run_case(r'''
PRODUCT=CN7PE.KOR.0000.V039.001.260902 carrier_case 0
WIRELESS=2.4.22 carrier_case 0
STOCK=mismatch carrier_case 0
LIVE=1 carrier_case 0
touch "$SYS_NET/wlan0"
carrier_case 0
'''), [])

    def test_install_apply_reboot_and_uninstall_once(self):
        calls = self.run_case(r'''
carrier_case 1
carrier_case 1
BID=aaa2 carrier_case 0
usb_carrier_remove
test ! -e "$CARRIER"
BID=aaa3 carrier_case 0
''')
        self.assertEqual(calls, ['plan', 'install', 'plan', 'apply', 'remove'])

    def test_manual_install_is_preserved(self):
        self.assertEqual(self.run_case(r'''
mkdir -p "$CARRIER/META-HMGAPI"
echo "$USB_CARRIER_MANIFEST_SHA" > "$CARRIER/META-HMGAPI/manifest.json"
carrier_case 0
usb_carrier_remove
test -f "$CARRIER/META-HMGAPI/manifest.json"
'''), [])

    def test_previous_bundled_carrier_is_upgraded_and_remains_bundle_owned(self):
        calls = self.run_case(r'''
legacy_carrier
echo "$USB_CARRIER_LEGACY_SHA applied aaa0" > "$BK/usb-carrier.owner"
carrier_case 1
grep -Fx "$USB_CARRIER_MANIFEST_SHA applied aaa1 managed" "$BK/usb-carrier.owner"
usb_carrier_remove
test ! -e "$CARRIER"
''')
        self.assertEqual(calls, ['plan', 'install', 'plan', 'apply', 'remove'])

    def test_previous_separately_installed_carrier_upgrades_without_taking_ownership(self):
        calls = self.run_case(r'''
legacy_carrier
carrier_case 1
grep -Fx "$USB_CARRIER_MANIFEST_SHA applied aaa1 external" "$BK/usb-carrier.owner"
usb_carrier_remove
test -d "$CARRIER"
''')
        self.assertEqual(calls, ['plan', 'install', 'plan', 'apply'])

    def test_previous_disabled_or_unrecognized_carrier_stays_untouched(self):
        self.assertEqual(self.run_case(r'''
legacy_carrier
echo "$USB_CARRIER_LEGACY_SHA applied aaa0" > "$BK/usb-carrier.owner"
touch "$CARRIER/.disabled"
carrier_case 0
rm "$CARRIER/.disabled"
echo different > "$CARRIER/META-HMGAPI/manifest.json"
carrier_case 0
usb_carrier_remove
test -d "$CARRIER"
'''), [])

    def test_foreign_plan_is_never_automatically_applied(self):
        self.assertEqual(self.run_case('BLOCK=1 carrier_case 0\n'), ['plan'])

    def test_interrupted_install_can_resume_but_is_limited_to_one_attempt_per_boot(self):
        calls = self.run_case(r'''
INTERRUPT=1 carrier_case 0
carrier_case 0
BID=aaa2 carrier_case 1
''')
        self.assertEqual(calls, ['plan', 'install', 'plan', 'plan', 'apply'])

    def test_apply_failure_can_resume_next_boot_and_a_disabled_mod_stays_disabled(self):
        calls = self.run_case(r'''
FAIL_APPLY=1 carrier_case 0
carrier_case 0
touch "$CARRIER/.disabled"
BID=aaa2 carrier_case 0
rm "$CARRIER/.disabled"
BID=aaa3 carrier_case 1
''')
        self.assertEqual(calls, ['plan', 'install', 'plan', 'apply', 'plan', 'plan', 'apply'])


if __name__ == '__main__':
    unittest.main()
