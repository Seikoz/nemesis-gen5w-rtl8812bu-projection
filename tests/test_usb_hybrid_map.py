from pathlib import Path
import subprocess
import tempfile
import unittest

from test_usb_stations import ENV, SH


HELPER = (Path(__file__).resolve().parents[1] / 'bundle/usb-hybrid-map.sh').read_text(encoding='utf-8')


class HybridMapTest(unittest.TestCase):
    def run_guard(self, before):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'state').mkdir()
            (root / 'required-hooks.txt').write_text('dipo.carplay.native_iap_send\n', newline='\n')
            script = '''
PATH=$TEST_BIN
W=. HMGDATA=. KP_HMG=. BB=bb BB_OWN=bb
MAP='{"whole": true, "points": {"dipo.carplay.native_iap_send": {}}}'
VERIFY=0 CHECK_FOLDER=local
bb() { if [ "$1" = timeout ]; then shift 2; "$@"; else command "$@"; fi; }
hmgapid() {
  echo "$2" >> calls
  case "$2" in
    map-car) echo "$MAP" > state/local-map.json ;;
    verify-map) echo "map $CHECK_FOLDER: 40 of 40"; return "$VERIFY" ;;
  esac
}
'''
            result = subprocess.run([SH, '-s'], input=(script + HELPER + '\n' + before +
                                    '\nusb_hybrid_map_ready\n').encode(), cwd=root, env=ENV, capture_output=True)
            calls = (root / 'calls').read_text().splitlines() if (root / 'calls').exists() else []
            return result.returncode, calls, result.stdout.decode()

    def test_generates_and_verifies_the_vehicles_map(self):
        rc, calls, _ = self.run_guard('')
        self.assertEqual((rc, calls), (0, ['map-car', 'verify-map']))

    def test_existing_map_is_verified_without_overwrite(self):
        rc, calls, _ = self.run_guard('echo "$MAP" > state/local-map.json')
        self.assertEqual((rc, calls), (0, ['verify-map']))

    def test_missing_points_or_wrong_map_do_not_pass(self):
        rc, calls, log = self.run_guard('MAP=\'{"whole": true, "missing": {"dipo.carplay.native_iap_send": "absent"}}\'')
        self.assertEqual((rc, calls), (1, ['map-car']))
        self.assertIn('Required CN7HEVPE hook missing', log)
        for before in ('VERIFY=1', 'CHECK_FOLDER=another-car', 'MAP=\'{"whole": false}\''):
            with self.subTest(before=before):
                self.assertNotEqual(self.run_guard(before)[0], 0)
