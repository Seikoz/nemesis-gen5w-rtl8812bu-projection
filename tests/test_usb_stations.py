from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SH = os.environ.get('TEST_SH', 'sh')
ENV = dict(os.environ)
SHELL_DIR = Path(shutil.which(SH) or SH).parent.as_posix()
if ':/' in SHELL_DIR:
    SHELL_DIR = '/' + SHELL_DIR[0].lower() + SHELL_DIR[2:]
ENV['TEST_BIN'] = SHELL_DIR
SCRIPT = (ROOT/'bundle/usb-stations.sh').read_text(encoding='utf-8')
HEAD = 'sta_dz_bitmap=00\ntim_bitmap=00\n'


def row(mac, state='0x1', aid=1, raid=0):
    return f"==============================\nsta's macaddr:{mac}\nrtsen=0, cts2slef=0\nstate={state}, aid={aid}, macid=1, raid={raid}\n"


class StationsTest(unittest.TestCase):
    def run_case(self, table, mode='fail', ap='1', after=''):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root/'app/bin').mkdir(parents=True)
            helper = root/'app/bin/ap-station-count'
            helper.write_text('#!/bin/sh\nread -r mode < "$PWD/mode"\ncase "$mode" in fail) exit 1;; *) echo "$mode";; esac\n', newline='\n')
            helper.chmod(0o755)
            (root/'mode').write_text(mode+'\n', newline='\n')
            (root/'proc/net/rtl88x2bu/rtwlan0').mkdir(parents=True)
            file = root/'proc/net/rtl88x2bu/rtwlan0/all_sta_info'
            if table is not None: file.write_text(table, newline='\n')
            (root/'net').mkdir()
            (root/'net/address').write_text('02:00:00:00:00:01\n', newline='\n')
            (root/'uptime').write_text('200.15 6.00\n', newline='\n')
            (root/'prog').write_text('state=done\n', newline='\n')
            setup = '''
PATH=$TEST_BIN
APP="$PWD/app"
PROC="$PWD/proc"
WLAN="$PWD/net"
WIF=rtwlan0
CONF=demo.conf
UPTIME="$PWD/uptime"
PROG="$PWD/prog"
AP_SCOPE='boot=test usb=4-1:2'
HI=wifi
BB=bb
bb() { command "$@"; }
running() { [ "$AP" = 1 ]; }
usb_wifi_ready() { [ "$AP" = 1 ]; }
usb_ap_live() { [ "$AP" = 1 ]; }
usb_cp_read() { CP_STATE=${TEST_CP_STATE:-unknown}; CP_COUNT=${TEST_CP_COUNT:-0}; }
hint_write() { echo hint-cleared >> events; }
log() { echo "$*" >> events; }
prog() { echo "$*" >> progress; { echo state=done; echo "message=$*"; } > "$PROG"; }
'''
            scenario = f'AP={ap}\nwifi_events\nusb_client_progress\necho "$STA_COUNT $STA_SOURCE $WSTA $WGONE"\n' + after
            result = subprocess.run([SH, '-s'], input=(setup+SCRIPT+scenario).encode(),
                                    env=ENV, cwd=root, capture_output=True, check=True)
            self.assertFalse(result.stderr, result.stderr)
            events = (root/'events').read_text()
            progress = (root/'progress').read_text(encoding='utf-8') if (root/'progress').exists() else ''
            self.assertNotIn('02:11:22:33:44:55', events+progress)
            return result.stdout.decode(), events, progress

    def test_realtek_associated_clients_exclude_self_multicast_pending_and_duplicates(self):
        data = HEAD + row('02:00:00:00:00:01', aid=0, raid=7)
        data += row('ff:ff:ff:ff:ff:ff', aid=4) + row('01:00:5e:00:00:01', aid=2)
        data += row('02:11:22:33:44:55', aid=2, raid=0) * 2
        data += row('02:aa:bb:cc:dd:ee', state='0x1008', aid=3)
        output, _, progress = self.run_case(data)
        self.assertEqual(output.strip(), '1 realtek-associated 1')
        self.assertIn('1대', progress)

    def test_empty_table_is_zero_but_missing_truncated_or_malformed_is_unknown(self):
        output, _, _ = self.run_case(HEAD)
        self.assertEqual(output.strip(), '0 realtek-associated 0')
        for data in (None, '', HEAD+"sta's macaddr:02:11:22:33:44:55\n", HEAD+row('wrong-mac')):
            with self.subTest(data=data):
                output, events, progress = self.run_case(data)
                self.assertEqual(output.strip(), 'unknown unavailable 0')
                self.assertIn('hint-cleared', events)
                self.assertIn('확인 불가', progress)

    def test_authorized_hostapd_count_has_priority_over_driver_entries(self):
        for count in ('0', '2'):
            output, _, progress = self.run_case(HEAD+row('02:11:22:33:44:55'), mode=count)
            self.assertEqual(output.strip(), f'{count} hostapd-authorized {count}')
            self.assertIn(count+'대', progress)

    def test_ap_off_does_not_reuse_stale_driver_entries(self):
        output, _, progress = self.run_case(HEAD+row('02:11:22:33:44:55'), ap='0')
        self.assertEqual(output.strip(), '0 ap-off 0')
        self.assertFalse(progress)

    def test_progress_restores_client_count_and_preserves_reboot_notice(self):
        after = '''
usb_client_progress
echo state=done > "$PROG"
usb_client_progress
echo state=reboot > "$PROG"
STA_COUNT=3
usb_client_progress
'''
        _, _, progress = self.run_case(HEAD, mode='2', after=after)
        self.assertEqual(progress.count('Wi-Fi 접속 단말 수:'), 2)
        self.assertNotIn('3대', progress)

    def test_disconnect_and_reconnect_are_snapshots_not_accumulated_events(self):
        after = '''
echo sta_dz_bitmap=00 > "$PROC/net/rtl88x2bu/$WIF/all_sta_info"
echo tim_bitmap=00 >> "$PROC/net/rtl88x2bu/$WIF/all_sta_info"
wifi_events
echo "$STA_COUNT $STA_SOURCE $WSTA $WGONE"
echo 2 > mode
wifi_events
echo "$STA_COUNT $STA_SOURCE $WSTA $WGONE $WCONN_AT"
'''
        output, _, _ = self.run_case(HEAD+row('02:11:22:33:44:55'), after=after)
        self.assertEqual(output.splitlines(), ['1 realtek-associated 1 ', '0 realtek-associated 0 1', '2 hostapd-authorized 2  200'])


if __name__ == '__main__': unittest.main()
