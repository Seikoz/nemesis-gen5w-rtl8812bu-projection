"""Exercise the real loader with non-executable extracted files on a POSIX host."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest
from test_usb_stations import SH, ENV

ROOT=Path(__file__).resolve().parents[1]
COMMON=(ROOT/'package/scripts/common.sh').read_text(encoding='utf-8').replace(
    'local log_dir=/data/nemesis/logs/realtek.88x2bu','local log_dir="$PWD/log"')
TOOLS=(ROOT/'bundle/usb-stations.sh').read_text(encoding='utf-8')

@unittest.skipUnless(os.name=='posix','Real executable-bit semantics are verified on Linux CI')
class RecoveryPermissionTest(unittest.TestCase):
    def test_kernel_recovery_log_tracks_reassigned_buses_and_filters_secrets(self):
        command = '''
PATH=$TEST_BIN
dmesg() { printf '%s\\n' \\
 '[ 10.000001] usb 3-1: old event' \\
 '[ 21.332766] usb 4-1: new high-speed USB device' \\
 '[ 21.462789] usb 4-1: device descriptor read/64, error -71' \\
 '[ 24.000000] ehci-platform ehci-mux.0: new USB bus registered' \\
 '[ 36.112778] usb 3-1: new full-speed USB device' \\
 '[ 36.200000] usb 3-1: SerialNumber: private' \\
 '[ 36.300000] unrelated event'; }
recovery_kernel_log 20
'''
        r=subprocess.run([SH,'-s'],input=(COMMON+command).encode(),env=ENV,capture_output=True,check=True)
        output=r.stdout.decode()
        for expected in ('usb 4-1: new high-speed','error -71','ehci-mux.0','usb 3-1: new full-speed'):
            self.assertIn(expected,output)
        for excluded in ('old event','private','unrelated event'):
            self.assertNotIn(excluded,output)

    def run_case(self,helper=None,commands='recover_high_speed; echo rc=$?'):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/'app/bin').mkdir(parents=True);(p/'usb/3-1').mkdir(parents=True)
            (p/'usb/3-1/speed').write_text('12\n')
            binary=p/'app/bin/usb-reset-a3000mini'
            if helper is None:helper='''#!/bin/sh
echo "$1 ${2##*/}" >> "$PWD/called"
[ "$1" = --high-speed ] || exit 2
mkdir -p "$PWD/usb/4-1"
echo 480 > "$PWD/usb/4-1/speed"
'''
            binary.write_text(helper,newline='\n');binary.chmod(0o644)
            setup=r'''
PATH=$TEST_BIN
package_dir="$PWD/app"
is_cn7npe_boot_reset_target() { return 0; }
read_boot_id() { boot_id=a1111111-1111-1111-1111-111111111111; }
identify_dongle() {
 vendor=0bda product=b812
 if [ -e "$PWD/usb/4-1/speed" ]; then usb="$PWD/usb/4-1"; else usb="$PWD/usb/3-1"; fi
}
sleep() { :; }
'''
            r=subprocess.run([SH,'-s'],input=(COMMON+setup+commands).encode(),env=ENV,cwd=p,capture_output=True,check=True)
            files={x.relative_to(p).as_posix():x.read_text() for x in p.rglob('*') if x.is_file()}
            markers=[x.name for x in (p/'app').glob('.usb-speed-tried-*')]
            return r.stdout.decode(),r.stderr.decode(),files,markers,(binary.stat().st_mode&0o777 if binary.exists() else None)

    def test_missing_execute_bit_is_repaired_before_ehci_request(self):
        out,err,files,markers,mode=self.run_case()
        self.assertIn('rc=0',out);self.assertEqual(err,'')
        self.assertEqual(mode,0o755)
        self.assertEqual(files['called'],'--high-speed 3-1\n')
        self.assertEqual(len(markers),1)
        self.assertIn('repairing mode to 0755',files['log/speed.log'])
        self.assertIn('Verified usb=4-1 speed_after=480',files['log/speed.log'])

    def test_chmod_failure_spends_no_hardware_attempt_and_can_recover_same_boot(self):
        out,err,files,markers,mode=self.run_case(commands=r'''
chmod() { return 1; }
recover_high_speed; echo first=$?
find "$package_dir" -name '.usb-speed-tried-*' > before
unset -f chmod
recover_high_speed; echo second=$?
''')
        self.assertEqual(err,'');self.assertIn('first=2',out);self.assertIn('second=0',out)
        self.assertEqual(files['before'],'');self.assertEqual(len(markers),1)
        self.assertEqual(files['called'].count('--high-speed'),1)

    def test_already_480_or_other_target_does_not_execute_or_chmod(self):
        for command in ('echo 480 > usb/3-1/speed','is_cn7npe_boot_reset_target() { return 1; }'):
            out,err,files,markers,mode=self.run_case(commands=command+'\nrecover_high_speed; echo rc=$?')
            self.assertEqual(err,'');self.assertIn('rc=0',out)
            self.assertNotIn('called',files);self.assertEqual(markers,[]);self.assertEqual(mode,0o644)

    def test_native_refusal_remains_bounded_and_is_not_reported_as_480(self):
        helper='#!/bin/sh\necho refused >> "$PWD/called"\nexit 7\n'
        out,err,files,markers,_=self.run_case(helper,commands='recover_high_speed; recover_high_speed; recover_high_speed; echo rc=$?')
        self.assertEqual(err,'');self.assertIn('rc=1',out)
        self.assertEqual(files['called'],'refused\nrefused\n');self.assertEqual(len(markers),2)
        self.assertNotIn('speed_after=480',files['log/speed.log'])

    def test_second_stage_uses_host_restart_and_verifies_actual_480(self):
        helper='''#!/bin/sh
echo "$1" >> "$PWD/called"
if [ "$1" = --restart-hosts ]; then
 mkdir -p "$PWD/usb/4-1"; echo 480 > "$PWD/usb/4-1/speed"
fi
'''
        out,err,files,markers,_=self.run_case(helper)
        self.assertEqual(err,'');self.assertIn('rc=0',out)
        self.assertEqual(files['called'].splitlines(),['--high-speed','--restart-hosts'])
        self.assertEqual(len(markers),2)
        self.assertIn('Recovery stage=external-host-restart EHCI-first',files['log/speed.log'])
        self.assertIn('speed_after=480',files['log/speed.log'])

    def test_symlink_and_missing_helper_are_rejected_before_attempt(self):
        for command in ('mv app/bin/usb-reset-a3000mini outside; ln -s "$PWD/outside" app/bin/usb-reset-a3000mini',
                        'rm app/bin/usb-reset-a3000mini'):
            out,err,files,markers,_=self.run_case(commands=command+'\nrecover_high_speed; echo rc=$?')
            self.assertIn('rc=2',out);self.assertEqual(markers,[]);self.assertNotIn('called',files)

    def test_projection_native_tools_are_repaired_and_names_are_scoped(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/'bin').mkdir()
            for name in ('ap-station-count','ap-link-diagnostics','outside'):
                f=p/'bin'/name;f.write_text('#!/bin/sh\necho ran\n',newline='\n');f.chmod(0o644)
            setup='PATH=$TEST_BIN\nAPP="$PWD"\n'
            commands='''
usb_prepare_native_tool ap-station-count && "$APP/bin/ap-station-count"
usb_prepare_native_tool ap-link-diagnostics && "$APP/bin/ap-link-diagnostics"
usb_prepare_native_tool outside; echo rejected=$?
'''
            r=subprocess.run([SH,'-s'],input=(setup+TOOLS+commands).encode(),env=ENV,cwd=p,capture_output=True,check=True)
            self.assertEqual(r.stdout.decode().splitlines(),['ran','ran','rejected=1'])
            self.assertEqual((p/'bin/outside').stat().st_mode&0o777,0o644)

if __name__=='__main__':unittest.main()
