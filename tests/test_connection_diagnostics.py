from pathlib import Path
import subprocess
import tempfile
import unittest
from test_usb_stations import SH, ENV

SCRIPT=(Path(__file__).resolve().parents[1]/'bundle/usb-connection-diagnostics.sh').read_text(encoding='utf-8')
AUDIO=(Path(__file__).resolve().parents[1]/'bundle/usb-carplay-audio.sh').read_text(encoding='utf-8')

class FirewallSnapshotTest(unittest.TestCase):
    def test_kernel_order_counters_and_ipv6_udp_scope_are_reported(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            setup=r'''
PATH=$TEST_BIN
BB=bb BB_OWN=bb HMGDATA="$PWD"
bb() { if [ "$1" = timeout ]; then shift 2; "$@"; else command "$@"; fi; }
iptables() { echo 'Chain INPUT (policy DROP 1 packets, 20 bytes)'; echo 'num pkts bytes target prot opt in out source destination'; echo '1 7 500 HMGAPI_IN all -- * * 0.0.0.0/0 0.0.0.0/0'; }
ip6tables() { cat <<'EOF'
Chain INPUT (policy DROP 0 packets, 0 bytes)
num pkts bytes target prot in out source destination
1 0 0 DROP all * * ::/0 ::/0
2 3 40 HMGAPI_IN all * * ::/0 ::/0
Chain OUTPUT (policy ACCEPT 0 packets, 0 bytes)
num pkts bytes target prot in out source destination
1 8 80 HMGAPI_OUT all * * ::/0 ::/0
Chain HMGAPI_IN (1 references)
num pkts bytes target prot in out source destination
1 5 100 ACCEPT udp rtwlan0 * fe80::/10 ::/0 udp dpt:6031
2 1 40 ACCEPT udp wlan0 * fe80::/10 ::/0 udp dpt:6031
Chain HMGAPI_OUT (1 references)
num pkts bytes target prot in out source destination
1 2 80 ACCEPT udp * rtwlan0 ::/0 fe80::/10 udp spt:6031
EOF
}
'''
            r=subprocess.run([SH,'-s'],input=(setup+SCRIPT+'\nusb_firewall_snapshot\n').encode(),env=ENV,cwd=root,capture_output=True,check=True)
            out=r.stdout.decode()
            self.assertFalse(r.stderr,r.stderr)
            self.assertIn('1 5 100 ACCEPT udp rtwlan0',out)
            self.assertIn('HMGAPI_input_jump_position=2 HMGAPI_output_jump_position=1',out)
            self.assertIn('IPv6_UDP6031_scoped_input_entries=1 output_entries=1',out)
            self.assertEqual(out.count('firewall_exit=0'),2)

    def test_audio_capture_keeps_milestones_without_phone_or_raw_log(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root/'proc/sys/kernel/random').mkdir(parents=True)
            boot = root/'proc/sys/kernel/random/boot_id'
            boot.write_text('new-boot\n', newline='\n')
            report = root/'usb-carplay-audio.log'
            report.write_text('boot=old-boot\nold-event\n', newline='\n')
            setup = r'''
PATH=$TEST_BIN
W="$PWD" PROC="$PWD/proc" BB=bb BB_OWN=bb UPTIME="$PWD/uptime"
bb() {
  if [ "$1" = timeout ]; then
    [ "$2" = 25 ] || return 90
    shift 2
    "$@"
  else command "$@"; fi
}
logcat() {
  [ "$1 $2 $3" = '-b main -d' ] || return 91
  for arg do [ "$arg" != -t ] || return 92; done
  status=0
  if [ ! -r "$W/captures" ]; then
    status=143
    echo '11-21 12:01:00.000 123 456 I HMG-API : [wireless] USB_CP_HANDOVER stage=waiting-after-rc19'
  fi
  echo capture >> "$W/captures"
  cat <<'EOF'
11-21 12:01:00.001 123 456 I HMG-API : [wireless] USB_CP_AUDIO bluetooth_handoff=stock
11-21 12:01:00.002 123 456 I TccCarPlay: Setup stream type: 102
11-21 12:01:00.003 123 456 I TccCarPlay: Main audio setting up AAC-LC/48000 for Private iPhone
11-21 12:01:00.004 123 456 I TccCarPlay: audio setup failed for Private iPhone
11-21 12:01:00.005 123 456 I TccCarPlay: Setup stream type: 110
11-21 12:01:00.006 123 456 I MediaFocusControl: AudioFocus requestAudioFocus() from com.daudio.av.app.btaudio.ui Private iPhone
EOF
  return "$status"
}
'''
            run = r'''
set -e
echo '100.50 1.00' > "$UPTIME"
CP_COUNT=0
usb_watch_carplay_audio
CP_STATE=bt_attach
usb_watch_carplay_audio
usb_watch_carplay_audio
wait "$USB_AUDIO_CAPTURE_PID"
grep -q '^logcat_exit=143$' "$W/usb-carplay-audio.log"
grep -q 'iap2_stage=waiting-after-rc19' "$W/usb-carplay-audio.log"
CP_COUNT=1
CP_STATE=started
usb_watch_carplay_audio
CP_COUNT=0
CP_STATE=finalized
usb_watch_carplay_audio
wait "$USB_AUDIO_CAPTURE_PID"
usb_watch_carplay_audio
'''
            result = subprocess.run([SH, '-s'], input=(setup+AUDIO+run).encode(), env=ENV,
                                    cwd=root, capture_output=True, check=True)
            self.assertFalse(result.stderr, result.stderr)
            out = report.read_text()
            self.assertEqual((root/'captures').read_text().splitlines(), ['capture', 'capture'])
            self.assertTrue(out.startswith('boot=new-boot\nlogcat_exit=0\n'))
            self.assertIn('bluetooth_handoff=stock', out)
            self.assertIn('audio_setup_request type=102', out)
            self.assertEqual(out.count('audio_stream_reported stream=main codec=aac-lc'), 1)
            self.assertIn('audio_setup_error', out)
            self.assertIn('iap2_stage=waiting-after-rc19', out)
            self.assertIn('focus_request source=bluetooth-media', out)
            for excluded in ('old-event', 'Private iPhone', 'type=110', 'com.daudio'):
                self.assertNotIn(excluded, out)

if __name__=='__main__': unittest.main()
