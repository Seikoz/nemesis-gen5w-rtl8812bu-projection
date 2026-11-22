import os
from pathlib import Path
import subprocess
import tempfile
import unittest


DASHBOARD = (Path(__file__).resolve().parents[1] / "bundle/usb-dashboard.sh").read_bytes()
SERVICE = (Path(__file__).resolve().parents[1] / "bundle/dashboard-service.sh").read_bytes()


class DashboardTest(unittest.TestCase):
    def run_dashboard(self, commands):
        shell = os.environ.get("TEST_SH", "sh")
        setup = b'PATH=/usr/bin:$PATH\ncall() { "$@"; }\nBB=call\n'
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [shell, "-s"], input=setup + DASHBOARD + b"\n" + commands.encode("utf-8"),
                cwd=tmp, capture_output=True, timeout=15,
            )
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", errors="replace"))
        return result.stdout.decode("utf-8").splitlines()

    def test_usb_identity_prefers_sysfs_parent_and_avoids_guessing_shared_id(self):
        lines = self.run_dashboard(r"""
usb_projection_paths() { printf '%s\n' $paths; }
WLAN=none
mkdir -p 1-1 1-2/net/rtwlan0/device
printf '0bda\n' > 1-1/idVendor
printf 'b812\n' > 1-1/idProduct
printf '12\n' > 1-1/speed
printf '802.11ac NIC\n' > 1-1/product
printf '2357\n' > 1-2/idVendor
printf '012d\n' > 1-2/idProduct
printf '480\n' > 1-2/speed
paths=1-1
dashboard_usb_summary
printf 'ipTIME A3000mini\n' > 1-1/product
dashboard_usb_summary
paths='1-1 1-2'
dashboard_usb_summary
WLAN=1-2/net/rtwlan0
dashboard_usb_summary
paths=
dashboard_usb_summary
""")
        self.assertEqual(lines, [
            "RTL8812BU (0bda:b812) · USB 12 Mbps",
            "ipTIME A3000mini (0bda:b812) · USB 12 Mbps",
            "USB 동글 여러 개 · 사용 모델 확인 불가",
            "Archer T3U V1 (2357:012d) · USB 480 Mbps",
            "지원 USB 동글 없음",
        ])

    def test_reads_only_ssid_and_one_authorized_station_rate(self):
        lines = self.run_dashboard(r"""
CONF=hostapd.conf
printf 'ssid=Car = Wi-Fi\r\nwpa_passphrase=never-display\n' > "$CONF"
dashboard_ssid
printf 'Station 00:11:22:33:44:55\n  tx bitrate: 433.3 MBit/s\n  authorized: yes\n' > stations
dashboard_station_rate < stations
printf 'Station 00:11:22:33:44:66\n  authorized: no\n' >> stations
dashboard_station_rate < stations
printf 'Station 00:11:22:33:44:55\n  tx bitrate: 433.3 MBit/s\n' | dashboard_station_rate
""")
        self.assertEqual(lines, ["Car = Wi-Fi", "433.3"])

    def test_gps_accepts_fresh_real_gps_fix_only_without_leaking_coordinates(self):
        lines = self.run_dashboard(r"""
gps_dump() {
  printf '  Last Known Locations:\n    gps: Location[gps 12.3456,78.9012 acc=5 et=%s%s]\n' "$1" "$2"
  printf '  Last Known Locations Coarse Intervals:\n'
}
gps_dump +2m3s456ms '' | dashboard_gps_fix 124
gps_dump +1d2h3m4s5ms '' | dashboard_gps_fix 93785
gps_dump +2m3s456ms '' | dashboard_gps_fix 160
gps_dump +2m3s456ms '' | dashboard_gps_fix 120
gps_dump +2m3s456ms ' mock' | dashboard_gps_fix 124
gps_dump +3s2m '' | dashboard_gps_fix 124
printf '  Last Known Locations:\n    fused: Location[fused 12.3,78.9 et=+2m3s]\n' | dashboard_gps_fix 124
""")
        self.assertEqual(lines, ["recent", "recent"])

    def test_phone_states_distinguish_ap_ready_and_session_evidence(self):
        lines = self.run_dashboard("""
CP_COUNT=1 CP_STATE=started K_AAOK=yes K_AAWAIT=no K_AARDY=yes
dashboard_phone_summary no
dashboard_phone_summary yes
CP_COUNT=0 CP_STATE=created K_AAOK=no
dashboard_phone_summary yes
CP_STATE=stale-session K_AAWAIT=yes
dashboard_phone_summary yes
""")
        self.assertEqual(lines, [
            "무선 연결 · iPhone CarPlay AP 대기 · Android Auto AP 대기",
            "무선 연결 · iPhone CarPlay 연결됨 · Android Auto 연결 감지",
            "무선 연결 · iPhone CarPlay 세션 시작 대기 · Android Auto 연결 가능",
            "무선 연결 · iPhone CarPlay 미확인 · Android Auto CarPlay 종료 대기",
        ])

    def test_dashboard_rows_fit_status_file_and_hide_sensitive_fields(self):
        lines = self.run_dashboard(r"""
call() {
  if [ "$1" = timeout ]; then shift 2; fi
  "$@"
}
BB_OWN=call
usb_projection_paths() { :; }
usb_ap_live() { return 0; }
pver() { printf '%s\n' 1.1.19; }
iw() { printf 'Station 00:11:22:33:44:55\n  authorized: yes\n  tx bitrate: 72.2 MBit/s\n'; }
dumpsys() {
  printf 'Last Known Locations:\n  gps: Location[gps 12.3,78.9 et=+30s]\nLast Known Locations Coarse Intervals:\n'
}
V_S1='설치: 끝남' K_HMGV=1.1.0-rc.8
K_OURAP=yes CP_STATE=started CP_COUNT=1 K_AAWAIT=no K_AAOK=no K_AARDY=yes
UPTIME=uptime CONF=hostapd.conf WLAN=unused WIF=rtwlan0
printf '34.00 0.00\n' > "$UPTIME"
printf 'ssid=Korea Projection\nwpa_passphrase=never-display\n' > "$CONF"
dashboard_rows 1.7.4.48 2.4.31
DASH_LIVE=1 DASH_AP_READY=yes DASH_STATIONS=
dashboard_rows 1.7.4.51 2.4.31
""")
        self.assertEqual([line.split("=", 1)[0] for line in lines], [
            "s1", "s2", "s3", "s1", "s2", "s3", "gps_fix",
        ])
        self.assertIn("KP 1.7.4.48 · Realtek 1.1.19", lines[0])
        self.assertIn("SSID Korea Projection · Wi-Fi 송신 링크 72.2 Mbps", lines[1])
        self.assertIn("차량 GPS 최근 수신 · 휴대폰 GPS 연동 확인 불가", lines[2])
        self.assertNotIn("GPS", lines[5])
        self.assertEqual(lines[6], "gps_fix=최근 수신")
        self.assertNotIn("never-display", "\n".join(lines))
        self.assertNotIn("00:11:22", "\n".join(lines))
        self.assertNotIn("12.3,78.9", "\n".join(lines))

    def test_radio_and_signal_only_show_reported_link_values(self):
        lines = self.run_dashboard(r"""
printf 'channel 149 (5745 MHz), width: 80 MHz, center1: 5775 MHz\n' | dashboard_radio
printf 'Station 00:11:22:33:44:55\n signal: -63 [-64, -65] dBm\n authorized: yes\n' | dashboard_station_signal
printf 'Station 00:11:22:33:44:55\n signal: -63 dBm\n authorized: no\n' | dashboard_station_signal
""")
        self.assertEqual(lines, ["5 GHz 채널 149 · 80 MHz", "-63"])

    def test_boot_times_and_failures_do_not_reuse_previous_boot(self):
        lines = self.run_dashboard(r"""
W=.
printf 'boot=old\nusb_480_interface_ready=14.5\nap_ready=27.9\n' > usb-boot-timing.log
dashboard_boot_times new
dashboard_boot_times old
printf 'boot=old\nreason=hostapd\nat=31\n' > dashboard-failure
dashboard_failure_summary new
dashboard_failure_summary old
""")
        self.assertEqual(lines, [
            "USB 480Mbps·인터페이스 미확인 · 핫스폿 준비 미확인",
            "USB 480Mbps·인터페이스 14초 · 핫스폿 준비 27초",
            "이번 부팅에 기록된 실패 없음",
            "핫스폿 시작 실패 · 부팅 후 31초",
        ])

    def test_foreground_lease_expires_and_rejects_future_or_non_numeric_values(self):
        module = SERVICE.decode("utf-8")
        lease_function = module[module.index("dashboard_active() {"):module.index("\npver() {")]
        lines = self.run_dashboard(lease_function + r"""
BB_OWN=call
DASH_ACTIVE=active
for request in 49 50 62 63 +62 invalid; do
    printf '%s' "$request" > "$DASH_ACTIVE"
    if dashboard_active 62; then echo "active:$request"; fi
done
""")
        self.assertEqual(lines, ["active:50", "active:62"])

    def test_collector_samples_five_seconds_apart_and_stops_on_background(self):
        schedule = SERVICE.decode("utf-8").split("\nnext=0\n", 1)[1]
        setup = r"""
printf 'this-boot\n' > boot-id
BOOT_ID=boot-id
DASH_STATE=snapshot
BB_OWN=call
simulated_seconds=0
dashboard_now() { echo "$simulated_seconds"; }
dashboard_active() {
    { [ "$1" -ge 2 ] && [ "$1" -le 9 ]; } || [ "$1" -ge 15 ]
}
dashboard_publish() {
    echo "sample:$1:$2"
    echo "$2" > "$DASH_STATE"
}
sleep() {
    simulated_seconds=$((simulated_seconds + 1))
    if [ "$simulated_seconds" = 11 ] && [ ! -e "$DASH_STATE" ]; then echo "background:cleared"; fi
    if [ "$simulated_seconds" = 21 ]; then exit 0; fi
}
next=0
"""
        self.assertEqual(self.run_dashboard(setup + schedule), [
            "sample:this-boot:2",
            "sample:this-boot:7",
            "background:cleared",
            "sample:this-boot:15",
            "sample:this-boot:20",
        ])
