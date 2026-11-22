from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from test_usb_stations import SH, ENV

SCRIPT=(Path(__file__).resolve().parents[1]/'bundle/usb-connection-diagnostics.sh').read_text(encoding='utf-8')
AUDIO=(Path(__file__).resolve().parents[1]/'bundle/usb-carplay-audio.sh').read_text(encoding='utf-8')
TRIALS=(Path(__file__).resolve().parents[1]/'bundle/usb-carplay-trials.sh').read_text(encoding='utf-8')

class FirewallSnapshotTest(unittest.TestCase):
    def test_coreutils_report_hashes_at_export_and_handles_read_errors(self):
        with tempfile.TemporaryDirectory() as td:
            library = Path(td) / 'test library.so'
            library.write_bytes(b'abc')
            setup = r'''
set -e
PATH=$TEST_BIN
BB=selected BB_OWN=bundled
printf() { return 127; }
selected() {
  [ "$1 $#" = 'md5sum 1' ] || return 90
  case "${mode:-}" in
    failed|fallback) return 13 ;;
    invalid|tab-fallback) echo 'not-a-valid-md5 private-text' ;;
    *) "$TEST_PYTHON" -c 'import hashlib, sys; print(hashlib.md5(sys.stdin.buffer.read(), usedforsecurity=False).hexdigest(), " -")' ;;
  esac
}
bundled() {
  [ "$1 $2 $#" = 'md5sum test library.so 2' ] || return 91
  case "${mode:-}" in
    failed) return 1 ;;
    invalid) echo 'invalid bundled output' ;;
    *) "$TEST_PYTHON" -c 'import hashlib, pathlib, sys; print(hashlib.md5(pathlib.Path(sys.argv[1]).read_bytes(), usedforsecurity=False).hexdigest() + chr(9) + sys.argv[1])' "$2" ;;
  esac
}
'''
            run = r'''
usb_carplay_coreutils_report 'test library.so'
usb_carplay_coreutils_report 'missing.so'
mode=failed usb_carplay_coreutils_report 'test library.so'
mode=invalid usb_carplay_coreutils_report 'test library.so'
mode=fallback usb_carplay_coreutils_report 'test library.so'
mode=tab-fallback usb_carplay_coreutils_report 'test library.so'
command printf changed > 'test library.so'
usb_carplay_coreutils_report 'test library.so'
'''
            env = dict(ENV, TEST_PYTHON=Path(sys.executable).as_posix())
            result = subprocess.run([SH, '-s'], input=(setup+SCRIPT+run).encode(), env=env,
                                    cwd=td, capture_output=True, check=True)
            self.assertFalse(result.stderr, result.stderr)
            self.assertEqual([line for line in result.stdout.decode().splitlines() if line],
                             ['== CarPlay native library fingerprint',
                              'libCarPlayCoreUtils.so.md5=900150983cd24fb0d6963f7d28e17f72',
                              'libCarPlayCoreUtils.so.check=selected-stdin(exit=0)',
                              '== CarPlay native library fingerprint',
                              'libCarPlayCoreUtils.so.md5=missing',
                              'libCarPlayCoreUtils.so.check=not-run',
                              '== CarPlay native library fingerprint',
                              'libCarPlayCoreUtils.so.md5=hash-failed',
                              'libCarPlayCoreUtils.so.check=selected-stdin(exit=13) bundled-file(exit=1)',
                              '== CarPlay native library fingerprint',
                              'libCarPlayCoreUtils.so.md5=hash-failed',
                              'libCarPlayCoreUtils.so.check=selected-stdin(exit=0) bundled-file(exit=0)',
                              '== CarPlay native library fingerprint',
                              'libCarPlayCoreUtils.so.md5=900150983cd24fb0d6963f7d28e17f72',
                              'libCarPlayCoreUtils.so.check=selected-stdin(exit=13) bundled-file(exit=0)',
                              '== CarPlay native library fingerprint',
                              'libCarPlayCoreUtils.so.md5=900150983cd24fb0d6963f7d28e17f72',
                              'libCarPlayCoreUtils.so.check=selected-stdin(exit=0) bundled-file(exit=0)',
                              '== CarPlay native library fingerprint',
                              'libCarPlayCoreUtils.so.md5=8977dfac2f8e04cb96e66882235f5aba',
                              'libCarPlayCoreUtils.so.check=selected-stdin(exit=0)'])

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
num pkts bytes target prot opt in out source destination
1 5 100 ACCEPT udp rtwlan0 * fe80::/10 ::/0 udp dpt:6031
2 1 40 ACCEPT udp wlan0 * fe80::/10 ::/0 udp dpt:6031
3 1 40 ACCEPT udp -- rtwlan0 * fe80::/10 ::/0 udp spt:6031
4 1 40 ACCEPT udp -- rtwlan0 * fe80::/10 ::/0 udp spt:60310
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
            self.assertIn('IPv6_UDP6031_scoped_input_entries=2 output_entries=1',out)
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
CP_EVENT_BOOT=new-boot CP_EVENT_RECORD=v1,123,99,gen,100,1,started,1
USB_TRIAL_DIR="$W/trial" USB_TRIAL_BOOT=new-boot
mkdir "$USB_TRIAL_DIR"
usb_ap_live() { return 1; }
bb() {
  if [ "$1" = timeout ]; then
    [ "$2" = 25 ] || return 90
    shift 2
    "$@"
  else command "$@"; fi
}
logcat() {
  [ "$1 $2 $3" = '-b main -d' ] || return 91
  dipo_tag=0
  for arg do
    [ "$arg" != -t ] || return 92
    [ "$arg" != CarPlay_:I ] || dipo_tag=1
  done
  [ "$dipo_tag" = 1 ] || return 93
  status=0
  if [ ! -r "$W/captures" ]; then
    status=143
    echo '11-21 12:01:00.000 123 456 I HMG-API : [wireless] USB_CP_HANDOVER stage=waiting-after-rc19'
  fi
  echo capture >> "$W/captures"
  cat <<'EOF'
11-21 12:01:00.001 123 456 I HMG-API : [wireless] USB_CP_AUDIO bluetooth_handoff=stock
11-21 12:01:00.002 100 456 I TccCarPlay: Setup stream type: 102
11-21 12:01:00.003 123 456 I TccCarPlay: Main audio setting up AAC-LC/48000 for Private iPhone
11-21 12:01:00.004 123 456 I TccCarPlay: audio setup failed for Private iPhone
11-21 12:01:00.005 123 456 I TccCarPlay: Setup stream type: 110
11-21 12:01:00.006 123 456 I MediaFocusControl: AudioFocus requestAudioFocus() from com.daudio.av.app.btaudio.ui Private iPhone
11-21 12:01:00.007 123 456 I TccCarPlay: Setup stream type: 130 for Private iPhone
11-21 12:01:00.008 123 456 I HMG-API : USB_CP_HANDOVER stage=first-native-send rc=19 len=6 peer_seen=false Private iPhone
11-21 12:01:00.009 123 456 I HMG-API : CarPlay-channel iAP2 send failed rc=19 len=6 Private iPhone
11-21 12:01:00.010 123 456 I HMG-API : ACTION_IAP2_CONNECTFAIL / LimitMaxResend Private iPhone
11-21 12:01:00.011 123 456 I CarPlay_: [ DipoService ] changeAudioFocus() ResourceOwner.CONTROLLER AudioTye:Media, mIsMusicAudioFocusGained:true
11-21 12:01:00.012 123 456 I CarPlay_: [ DipoService ] changeAudioFocus() ResourceOwner.CONTROLLER AudioTye:Unknown, mIsMusicAudioFocusGained:true
11-21 12:01:00.013 123 456 I CarPlay_: [ DipoService ] onChangeMainAudioMode() MainAudio: SAME AudioFocus Gain , mIsPhoneAudioFocusGained: false, mIsSiriAudioFocusGained: false, mIsMusicAudioFocusGained: true
11-21 12:01:00.014 123 456 I TccCarPlay: [TccCarPlay] TccCarPlay_iAPSendMessage() : data(0x6015C788) size(9)
11-21 12:01:00.015 123 456 I CarPlay_: [ DipoService ] changeAudioFocus() ResourceOwner.PrivateDevice AudioTye:PrivateDevice, mIsMusicAudioFocusGained:true
11-21 12:01:00.016 123 456 I CarPlay_: [ DipoService ] updateCarPlayMusicSSOSD : PrivateDevice
11-21 12:01:00.017 123 456 I TccCarPlay: FLUSHBUFFERED Private iPhone
11-21 12:01:00.018 123 456 I TccCarPlay: Main buffered audio setting up AAC-LC for Private iPhone
11-21 12:01:00.019 123 456 I LeafiaAAC: AAC-LC decoder up: 48000 Hz, 2 ch, 1024 frames/packet
11-21 12:01:00.020 123 456 I LeafiaAAC: first packet decoded: 1024 frames, 2 ch, 48000 Hz
11-21 12:01:00.021 123 456 W AudioTrack: disabled due to previous underrun
11-21 12:01:00.022 123 456 W AudioTrack: another underrun
11-21 12:01:01.022 345 456 W AudioTrack: unrelated underrun
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
            result = subprocess.run([SH, '-s'], input=(setup+AUDIO+TRIALS+run).encode(), env=ENV,
                                    cwd=root, capture_output=True, check=True)
            self.assertFalse(result.stderr, result.stderr)
            out = report.read_text()
            self.assertEqual((root/'trial/usb-carplay-audio.log').read_text(), out)
            self.assertEqual((root/'captures').read_text().splitlines(), ['capture', 'capture'])
            self.assertTrue(out.startswith('boot=new-boot\nlogcat_exit=0\n'))
            self.assertIn('bluetooth_handoff=stock', out)
            self.assertIn('audio_setup_request type=102', out)
            self.assertEqual(out.count('audio_stream_reported stream=main codec=aac-lc'), 1)
            self.assertIn('audio_setup_error', out)
            self.assertIn('iap2_stage=waiting-after-rc19', out)
            self.assertIn('iap2_setup_request type=130', out)
            self.assertIn('iap2_stage=first-native-send rc=19 len=6 peer_seen=false', out)
            self.assertIn('iap2_send_failed rc=19 len=6', out)
            self.assertIn('iap2_retry_limit', out)
            self.assertIn('focus_request source=bluetooth-media', out)
            self.assertIn('dipo_audio_focus owner=controller type=media music_focus=true', out)
            self.assertIn('dipo_audio_focus owner=controller type=unknown music_focus=true', out)
            self.assertIn('dipo_audio_focus owner=other type=other music_focus=true', out)
            self.assertIn('dipo_audio_mode mode=same phone_focus=false siri_focus=false music_focus=true', out)
            self.assertIn('carplay_music_metadata_updated', out)
            self.assertIn('buffered_audio_flush_reported', out)
            self.assertIn('audio_stream_reported stream=main_buffered codec=aac-lc', out)
            self.assertIn('aac_music_decoder_started', out)
            self.assertIn('aac_music_first_packet_decoded', out)
            self.assertEqual(out.count('dipo_audio_track_underrun_reported'), 1)
            self.assertIn('native_iap_send_rows=1', out)
            for excluded in ('old-event', 'Private iPhone', 'type=110', 'com.daudio', 'PrivateDevice', '0x6015C788'):
                self.assertNotIn(excluded.lower(), out.lower())

    def test_output_snapshot_is_bounded_and_only_keeps_playback_fields(self):
        with tempfile.TemporaryDirectory() as td:
            setup = r'''
PATH=$TEST_BIN
BB=bb BB_OWN=bb UPTIME="$PWD/uptime"
bb() {
  case "$1" in
    timeout) [ "$2" = 4 ] || return 90; shift 2; "$@" ;;
    date) echo '11-22 21:15:10' ;;
    *) command "$@" ;;
  esac
}
dumpsys() {
  [ "$1" = media.audio_flinger ] || return 91
  cat <<'EOF'
Output thread 0xabcdef internals
Normal frame count: 960
io handle: 2
standby: 0
Sample rate: 48000
HAL frame count: 240
Normal mixer raw underrun counters: partial=5 empty=7
unrelated field: private audio route
Input thread 0x1234 internals
Sample rate: 99999
EOF
  return 124
}
'''
            run = r'''
set -e
usb_capture_carplay_mixer
usb_capture_carplay_audio() { echo "snapshot_requested=$1"; }
CP_COUNT=1 CP_STATE=started
for seconds in 10 40 70; do
  echo "$seconds.00 0.00" > "$UPTIME"
  usb_watch_carplay_audio
  wait "$USB_AUDIO_CAPTURE_PID"
done
'''
            result = subprocess.run([SH, '-s'], input=(setup+AUDIO+run).encode(), env=ENV,
                                    cwd=td, capture_output=True, check=True)
            out = result.stdout.decode()
            self.assertFalse(result.stderr, result.stderr)
            self.assertIn('mixer_output_handle=2 standby=0 sample_rate_hz=48000 hal_frames=240 normal_frames=960 '
                          'underrun_partial=5 underrun_empty=7', out)
            self.assertIn('mixer_dump_exit=124 outputs_seen=1', out)
            self.assertNotIn('private audio route', out)
            self.assertNotIn('99999', out)
            self.assertEqual([line for line in out.splitlines() if line.startswith('snapshot_requested=')],
                             ['snapshot_requested=1', 'snapshot_requested=1', 'snapshot_requested=0'])

if __name__=='__main__': unittest.main()
