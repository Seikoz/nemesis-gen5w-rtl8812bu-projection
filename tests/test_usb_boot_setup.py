import subprocess
import tempfile
import unittest
from pathlib import Path

from test_usb_stations import ENV, SH


ROOT = Path(__file__).resolve().parents[1]
HELPER = (ROOT / 'bundle/usb-boot-setup.sh').read_text(encoding='utf-8')
LIVE_FILES = (
    '/system/etc/permissions/com.hkmc.software.connectivity.carplay_wireless.xml',
    '/system/etc/permissions/com.hkmc.software.connectivity.androidauto_wireless.xml',
    '/system/lib/libcarplayidentity.so',
    '/system/lib/libcarplaylog.so',
    '/system/lib/libleafiaaac.so',
)
PLAN = ''.join(f'same     {path} [wireless-carplay-aa]\n' for path in LIVE_FILES)
PLAN += 'home Wi-Fi  off\nnetwork  no cellular [wireless-carplay-aa]\n'


class BootSetupTest(unittest.TestCase):
    def run_gate(self, before='', plan=PLAN):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ('work', 'backup', 'hmg/state'):
                (root / name).mkdir(parents=True)
            (root / 'backup/automap.checked').touch()
            (root / 'hmg/state/local-map.json').write_text('{"fixture":true}')
            (root / 'hmg/state/map-check.json').write_text('{"ok":true}')
            (root / 'work/plan.txt').write_text(plan, newline='\n')
            script = '''
PATH=$TEST_BIN
W=work BK=backup HMGDATA=hmg BB=bb BB_OWN=bb MOD_ID=wireless-carplay-aa
USB_AUDIO_PLAN_SAFE=1
bb() { if [ "$1" = timeout ]; then shift 2; "$@"; else command "$@"; fi; }
setup_done() { return 0; }
prog_reboot_this_boot() { return 1; }
fix_running() { return 1; }
usb_audio_owned_files() { return 0; }
hmgapid() { [ "$*" = 'engine status' ] && echo 'ok managed files'; }
log() { echo "$*"; }
'''
            script += HELPER + '\n' + before + '\nusb_boot_setup_complete\n'
            return subprocess.run([SH, '-s'], input=script.encode(), cwd=root, env=ENV, capture_output=True)

    def test_ready_install_skips_only_delayed_worker(self):
        run = self.run_gate()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn(b'skipping delayed permission repair', run.stdout)

    def test_unready_or_unverified_setup_keeps_existing_worker(self):
        for cause in (
            'USB_AUDIO_PLAN_SAFE=0', 'setup_done() { return 1; }',
            'prog_reboot_this_boot() { return 0; }', 'fix_running() { return 0; }',
            'rm backup/automap.checked', 'touch backup/automap.bad',
            'touch hmg/state/journal.json', 'echo "{}" > hmg/state/map-check.json',
            'usb_audio_owned_files() { return 1; }', 'hmgapid() { return 4; }',
        ):
            with self.subTest(cause=cause):
                self.assertEqual(self.run_gate(before=cause).returncode, 1)

    def test_pending_changes_or_missing_live_matches_keep_worker(self):
        for plan in (
            PLAN + 'change   /system/extra [wireless-carplay-aa]\n',
            PLAN + 'setting  prop/example = t [wireless-carplay-aa]\n',
            PLAN + 'WARNING: pending trial\n',
            '\n'.join(PLAN.splitlines()[1:]) + '\n',
        ):
            with self.subTest(plan=plan):
                self.assertEqual(self.run_gate(plan=plan).returncode, 1)
