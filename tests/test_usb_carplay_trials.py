from pathlib import Path
import subprocess
import tempfile
import unittest

from test_usb_stations import ENV, SH

SCRIPT = (Path(__file__).resolve().parents[1] / 'bundle/usb-carplay-trials.sh').read_text(encoding='utf-8')
SETUP = r'''
set -eu
PATH=$TEST_BIN
BB=bb BK="$PWD/backup" W="$PWD/work" MOD_VER=2.4.21
HT=0 HOLD=0
bb() { command "$@"; }
getprop() { [ "$1" = persist.kp.ap.hold ] && echo "$HOLD"; }
usb_ap_ht_capab() { if [ "$HT" = 1 ]; then echo '[SHORT-GI-20]'; else echo '[HT40+]'; fi; }
lastmask() { cat; }
usb_ap_live() { return 0; }
mkdir -p "$W"
start() {
  BID="00000000-0000-0000-0000-00000000000$1"
  usb_trial_begin
}
save() {
  {
    echo "boot=$BID"
    echo "$2"
  } > "$W/$1"
  usb_trial_save "$1"
}
'''


class CarPlayTrialsTest(unittest.TestCase):
    def run_archive(self, body):
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run([SH, '-s'], input=(SETUP + SCRIPT + body).encode(),
                                    cwd=folder, env=ENV, capture_output=True, check=True)
            self.assertFalse(result.stderr, result.stderr)
            return result.stdout.decode()

    def test_three_boots_export_their_own_options_and_diagnostics(self):
        out = self.run_archive(r'''
start 1
save usb-carplay-audio.log 'A-only iap2_send_failed rc=19'
save usb-carplay-events.log 'A-only bt_attach'
HT=1
start 2
usb_trial_save usb-carplay-audio.log
save usb-carplay-events.log 'B-only started'
save usb-carplay-audio.log 'B-only audio_setup_request type=102'
HT=0 HOLD=1
start 3
usb_trial_ap_event 'ap_restart_deferred reason=bt_iap2 remaining_seconds=50'
save usb-carplay-audio.log 'C-only iap2_stage=resume-on-peer'
start 3
USB_TRIAL_DIR=
usb_trial_report
''')
        a, b, c = out.split('=== Trial boot ')[1:]
        self.assertIn('trial=A ht20=0 restart_hold=0', a)
        self.assertIn('A-only iap2_send_failed rc=19', a)
        self.assertIn('A-only bt_attach', a)
        self.assertIn('trial=B ht20=1 restart_hold=0', b)
        self.assertIn('B-only started', b)
        self.assertIn('B-only audio_setup_request type=102', b)
        self.assertNotIn('A-only', b)
        self.assertIn('trial=C ht20=0 restart_hold=1', c)
        self.assertIn('ap_restart_deferred reason=bt_iap2', c)
        self.assertIn('C-only iap2_stage=resume-on-peer', c)

    def test_older_boots_are_pruned_and_unrelated_files_are_preserved(self):
        out = self.run_archive(r'''
for i in 0 1 2 3 4 5 6 7 8; do
  start "$i"
  save usb-carplay-audio.log "boot-sample-$i"
done
root="$BK/usb-carplay-trials"
test ! -d "$root/00000000-0000-0000-0000-000000000000"
touch "$root/other"
start 9
save usb-carplay-audio.log 'boot-sample-9'
test -f "$root/other"
usb_trial_report
''')
        self.assertEqual(out.count('=== Trial boot '), 8)
        self.assertNotIn('boot-sample-1', out)
        self.assertIn('boot-sample-2', out)
        self.assertIn('boot-sample-9', out)

    def test_partial_trial_rejects_stale_audio_and_capture_window_is_bounded(self):
        out = self.run_archive(r'''
start 1
save usb-carplay-audio.log 'old audio'
start 2
usb_trial_save usb-carplay-audio.log
usb_trial_audio_window 100
usb_trial_audio_window 279
if usb_trial_audio_window 280; then exit 99; fi
usb_trial_report
''')
        second = out.split('=== Trial boot ')[2]
        self.assertNotIn('old audio', second)
        self.assertIn('No observations saved for this boot', second)
