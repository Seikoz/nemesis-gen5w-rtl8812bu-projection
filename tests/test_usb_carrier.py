from pathlib import Path
import subprocess
import tempfile
import unittest

from test_usb_stations import ENV, SH


SCRIPT = (Path(__file__).resolve().parents[1] / 'bundle/usb-audio-carrier.sh').read_text(encoding='utf-8')
SETUP = r"""
set -e
PATH=$TEST_BIN
W="$PWD/log" BK="$PWD/backup" HMGDATA="$PWD/hmg"
BB=bb BB_OWN=bb MOD_ID=wireless-carplay-aa
mkdir -p "$W" "$BK" "$HMGDATA/mods/$MOD_ID"
bb() {
  case "$1" in
    timeout) shift 2; "$@" ;;
    sha256sum) read -r digest; echo "$digest  -" ;;
    *) command "$@" ;;
  esac
}
usb_audio_owned_files() { [ "${VERIFIED:-1}" = 1 ]; }
hmgapid() {
  test "$1" = engine && test "$2" = remove && test "$3" = "$USB_CARRIER_ID" && test "$4" = --from-nemesis
  echo remove >> "$W/calls"
  [ "${FAILED:-0}" = 0 ] || return 1
  rm "$CARRIER/META-HMGAPI/manifest.json"
  rmdir "$CARRIER/META-HMGAPI" "$CARRIER"
}
"""
FIXTURE = r"""
CARRIER="$HMGDATA/mods/$USB_CARRIER_ID"
OWNER="$BK/usb-carrier.owner"
mod_fixture() {
  mkdir -p "$CARRIER/META-HMGAPI"
  echo "$1" > "$CARRIER/META-HMGAPI/manifest.json"
}
"""


class AudioCarrierMigrationTest(unittest.TestCase):
    def run_case(self, script):
        with tempfile.TemporaryDirectory() as tmp:
            run = subprocess.run([SH, '-s'], input=(SETUP + SCRIPT + FIXTURE + script).encode(),
                                 env=ENV, cwd=tmp, capture_output=True, check=True)
            self.assertFalse(run.stderr, run.stderr)
            calls = Path(tmp) / 'log/calls'
            return calls.read_text().splitlines() if calls.is_file() else []

    def test_managed_legacy_carrier_is_removed_once(self):
        self.assertEqual(self.run_case(r"""
mod_fixture "$USB_CARRIER_CURRENT_SHA"
echo "$USB_CARRIER_LEGACY_SHA applied aaa1" > "$OWNER"
usb_carrier_cleanup
usb_carrier_cleanup
test ! -e "$CARRIER" && test ! -e "$OWNER"
"""), ['remove'])

    def test_absent_manual_and_modified_carriers_are_preserved(self):
        self.assertEqual(self.run_case(r"""
echo "$USB_CARRIER_CURRENT_SHA applied aaa1 managed" > "$OWNER"
usb_carrier_cleanup
test -f "$OWNER"
mod_fixture wrong-digest
usb_carrier_cleanup
test -d "$CARRIER"
mod_fixture "$USB_CARRIER_CURRENT_SHA"
echo "$USB_CARRIER_CURRENT_SHA applied aaa1 external" > "$OWNER"
usb_carrier_cleanup
rm "$OWNER"
usb_carrier_cleanup
test -d "$CARRIER"
"""), [])

    def test_cleanup_waits_for_the_verified_enabled_replacement(self):
        self.assertEqual(self.run_case(r"""
mod_fixture "$USB_CARRIER_CURRENT_SHA"
echo "$USB_CARRIER_CURRENT_SHA applied aaa1 managed" > "$OWNER"
VERIFIED=0 usb_carrier_cleanup
touch "$HMGDATA/mods/$MOD_ID/.disabled"
usb_carrier_cleanup
test -d "$CARRIER" && test -f "$OWNER"
"""), [])

    def test_failed_cleanup_retains_ownership_and_can_retry(self):
        self.assertEqual(self.run_case(r"""
mod_fixture "$USB_CARRIER_LEGACY_SHA"
echo "$USB_CARRIER_LEGACY_SHA installed aaa1 managed" > "$OWNER"
FAILED=1 usb_carrier_cleanup
test -f "$OWNER" && test -d "$CARRIER"
usb_carrier_cleanup
test ! -e "$OWNER" && test ! -e "$CARRIER"
"""), ['remove', 'remove'])
