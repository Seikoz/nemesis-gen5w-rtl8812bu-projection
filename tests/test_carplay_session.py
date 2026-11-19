from pathlib import Path
import tempfile
import subprocess
import unittest

from test_usb_stations import SH, ENV

SCRIPT = (Path(__file__).resolve().parents[1]/'bundle/usb-carplay-session.sh').read_text(encoding='utf-8')
GEN = '12345678-200.50-8'


class SessionTest(unittest.TestCase):
    def run_case(self, record='', commands='usb_cp_read; echo "$CP_COUNT $CP_STATE $CP_SOURCE"'):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            (p/'proc/123').mkdir(parents=True)
            (p/'proc/sys/kernel/random').mkdir(parents=True)
            (p/'proc/sys/kernel/random/boot_id').write_text('12345678-boot\n')
            (p/'proc/123/stat').write_text('123 (DiPO with ) spaces) S '+'0 '*18+'77 0\n')
            (p/'net').mkdir()
            (p/'net/ifindex').write_text('8\n')
            (p/'uptime').write_text('202.50 1.00\n')
            (p/'sys.kp.cp_session').write_text(record+'\n')
            (p/'sys.kp.cp_gen').write_text(GEN+'\n')
            (p/'ap').write_text('1\n')
            (p/'logcat').write_text('')
            setup = r'''
PATH=$TEST_BIN
W="$PWD" PROC="$PWD/proc" WLAN="$PWD/net" UPTIME="$PWD/uptime" AAPROP=ap BB=bb BB_OWN=bb
CPN="$PWD/cpn"
bb() { if [ "$1" = timeout ]; then shift 2; "$@"; else command "$@"; fi; }
getprop() { cat "$PWD/$1" 2>/dev/null; }
setprop() { printf '%s\n' "$2" > "$PWD/$1"; }
usb_wifi_ready() { [ "$(cat ap)" = 1 ]; }
logcat() { cat "$PWD/logcat"; }
log() { echo "$*" >> messages; }
usb_client_progress() { :; }
usb_connection_tick() { :; }
'''
            r = subprocess.run([SH,'-s'],input=(setup+SCRIPT+'\n'+commands).encode(),
                               env=ENV,cwd=p,capture_output=True,check=True)
            self.assertFalse(r.stderr, r.stderr)
            return r.stdout.decode(), {x.name:x.read_text() for x in p.iterdir() if x.is_file()}

    def event(self,state='started',transport=1,gen=GEN):
        return f'v1,123,77,{gen},201000,2,{state},{transport}'

    def test_started_only_and_lifecycle(self):
        for state in ('idle','bt_attach','created','wired','finalized'):
            out,_=self.run_case(self.event(state))
            self.assertEqual(out.strip(),f'0 {state} session-callback')
        out,_=self.run_case(self.event())
        self.assertEqual(out.strip(),'1 started session-callback')
        out,_=self.run_case(self.event(transport=0))
        self.assertTrue(out.startswith('0 '))

    def test_stale_ap_reboot_dead_process_and_pid_reuse(self):
        for commands,status in (
            ('echo off > sys.kp.cp_gen','stale-ap'),
            ('rm proc/123/stat','process-gone'),
            ("sed 's/77/78/' proc/123/stat > changed; mv changed proc/123/stat",'process-gone'),
            ("echo '300.50 1.00' > uptime",'stale-session'),
        ):
            out,_=self.run_case(self.event(),commands+'\nusb_cp_read; echo "$CP_COUNT $CP_STATE"')
            self.assertEqual(out.strip(),'0 '+status)
        out,_=self.run_case('',f"echo 'boot=old {self.event()}' > usb-cp-state\nusb_cp_read; echo \"$CP_COUNT $CP_STATE\"")
        self.assertEqual(out.strip(),'0 unknown')
        out,_=self.run_case(self.event(),'echo 0 > ap\nusb_cp_read; echo "$CP_COUNT"')
        self.assertEqual(out.strip(),'0')

    def test_logcat_fallback_keeps_all_stages_without_raw_data(self):
        events=[self.event('created'),self.event().replace(',2,started',',3,started'),
                self.event('finalized').replace(',2,finalized',',4,finalized')]
        commands="cat > logcat <<'EOF'\nprivate SSID password phone-name\n"+'\n'.join('I/HMG-API: USB_CP_EVENT '+x for x in events)+"\nUSB_CP_EVENT malformed,sensitive\nEOF\nusb_cp_poll; usb_cp_poll; usb_cp_read; echo \"$CP_COUNT $CP_STATE\""
        out,files=self.run_case('',commands)
        self.assertEqual(out.strip(),'0 finalized')
        self.assertEqual(files['usb-carplay-events.log'].splitlines(),['boot=12345678-boot']+events)
        self.assertNotIn('sensitive',files['usb-carplay-events.log'])

    def test_ap_generation_survives_service_restart_and_changes_on_ap_cycle(self):
        out,_=self.run_case('',r'''
usb_cp_generation 1; getprop sys.kp.cp_gen
usb_cp_generation 0; getprop sys.kp.cp_gen
echo 0 > ap
echo '201.50 1.00' > uptime
usb_cp_generation 1; getprop sys.kp.cp_gen
''')
        self.assertEqual(out.splitlines(),[GEN,'off','12345678-201.50-8'])


if __name__=='__main__': unittest.main()
