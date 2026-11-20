from pathlib import Path
import subprocess
import tempfile
import unittest

from test_usb_stations import ENV, SH


HELPER = (Path(__file__).resolve().parents[1] / 'bundle/usb-boot-timing.sh').read_text(encoding='utf-8')


class BootTimingTest(unittest.TestCase):
    def run_marks(self, commands):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            setup = '''
PATH=$TEST_BIN
W=. BB=bb BOOT_ID=boot-id UPTIME=uptime
bb() { command "$@"; }
echo abcd-1234 > "$BOOT_ID"
'''
            subprocess.run([SH, '-s'], input=(setup + HELPER + '\n' + commands).encode(),
                           cwd=root, env=ENV, check=True, capture_output=True)
            return (root / 'usb-boot-timing.log').read_text().splitlines()

    def test_first_observation_survives_ap_restart(self):
        lines = self.run_marks('''
echo '17.25 42.00' > uptime
usb_boot_mark usb_480_interface_ready
echo '32.71 50.00' > uptime
usb_boot_mark ap_ready
echo '95.01 300.00' > uptime
usb_boot_mark ap_ready
usb_boot_mark carplay_observed
''')
        self.assertEqual(lines, ['boot=abcd-1234', 'usb_480_interface_ready=17.25',
                                 'ap_ready=32.71', 'carplay_observed=95.01'])

    def test_new_boot_drops_previous_stages_and_rejects_invalid_uptime(self):
        lines = self.run_marks('''
echo '68.00 80.00' > uptime
usb_boot_mark ap_ready
echo dcba-4321 > boot-id
echo '3.02 5.00' > uptime
usb_boot_mark service_start
echo 'error 80.00' > uptime
if usb_boot_mark ap_ready; then exit 1; fi
''')
        self.assertEqual(lines, ['boot=dcba-4321', 'service_start=3.02'])
