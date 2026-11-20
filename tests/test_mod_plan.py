from pathlib import Path
import subprocess
import tempfile
import unittest

from test_usb_stations import SH, ENV

SCRIPT = (Path(__file__).resolve().parents[1]/'bundle/usb-mod-plan.sh').read_text(encoding='utf-8')


class ModPlanTest(unittest.TestCase):
    def test_only_owned_wireless_changes_are_automatically_applied(self):
        cases = (
            ('network  firewall filter input: accept tcp port 1024-65535 in rtwlan0 [wireless-carplay-aa]\n', 0, 0),
            ('same     /system/file\nsetting  prop/persist.sys.iap2.wifi = t [wireless-carplay-aa]\n', 0, 0),
            ('change   /system/file [wireless-carplay-aa] -> hash\nhook plan: enabled\n', 0, 0),
            ('nothing changed\n', 0, 0),
            ('change   /system/lib/libcarplayidentity.so [wireless-carplay-aa] -> hash [restart the head unit]\n'
             'update   /system/lib/libleafiaaac.so [wireless-carplay-aa] -> hash\n'
             'event    parked -> its apps and hooks hear it [wireless-carplay-aa]\n'
             'event    unparked -> its apps and hooks hear it [wireless-carplay-aa]\n'
             'event    shutdown -> its apps and hooks hear it [wireless-carplay-aa]\n'
             'event    wake -> its apps and hooks hear it [wireless-carplay-aa]\n'
             'home Wi-Fi  off\nnetwork  no cellular [nemesis-shortcut]\n', 0, 0),
            ('event    parked -> its apps and hooks hear it [other-mod]\n', 0, 1),
            ('event    parked -> unknown command [wireless-carplay-aa]\n', 0, 1),
            ('home Wi-Fi  on\n', 0, 1),
            ('network  no cellular [bad] extra\n', 0, 1),
            ('network  firewall filter input: accept tcp port 5555 [other-mod]\n', 0, 1),
            ('change   /system/file [other-mod] -> hash\n', 0, 1),
            ('setting  prop/example = x [wireless-carplay-aa] back to stock\n', 0, 1),
            ('hooks are off: example\n', 0, 1),
            ('problem  unable to prepare policy\n', 0, 1),
            ('unexpected plan output\n', 0, 1),
            ('', 0, 1),
            ('network  example [wireless-carplay-aa]\n', 1, 1),
        )
        for plan, cli_exit, expected in cases:
            with self.subTest(plan=plan, cli_exit=cli_exit), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                (root/'plan-input').write_text(plan, newline='\n')
                setup = '''
PATH=$TEST_BIN
W="$PWD"
MOD_ID=wireless-carplay-aa
hmgapid() { cat "$PWD/plan-input"; return "$PLAN_EXIT"; }
'''
                result = subprocess.run([SH, '-s'], input=(setup+SCRIPT+f'\nPLAN_EXIT={cli_exit}\nplan_only_mod\necho "$?"\n').encode(),
                                        cwd=root, env=ENV, capture_output=True, check=True)
                self.assertFalse(result.stderr, result.stderr)
                self.assertEqual(result.stdout.strip(), str(expected).encode())


if __name__ == '__main__': unittest.main()
