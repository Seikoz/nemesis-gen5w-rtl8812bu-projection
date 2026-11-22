#!/system/bin/sh
# Show read-only status on demand. The app can request samples, not commands.
APP=${APP:-/data/nemesis/apps/korea.projection}
HOTSPOT_LIB=1 . "$APP/svc/hotspot.sh"
has_bb || exit 1

DASH_APP=/data/data/io.github.seikoz.projectiondashboard
DASH_ACTIVE=$DASH_APP/files/active
DASH_STATE=/data/local/tmp/korea-projection-dashboard.txt
umask 077

dashboard_now() {
  local now
  read -r now _ < "$UPTIME" || return 1
  now=${now%%.*}
  case "$now" in ''|*[!0-9]*) return 1 ;; esac
  echo "$now"
}

dashboard_active() {
  local lease
  [ -f "$DASH_ACTIVE" ] && [ ! -L "$DASH_ACTIVE" ] || return 1
  lease=$("$BB_OWN" head -c 16 "$DASH_ACTIVE" 2>/dev/null) || return 1
  case "$lease" in ''|0[0-9]*|*[!0-9]*|??????????*) return 1 ;; esac
  [ "$1" -ge "$lease" ] && [ "$(($1 - lease))" -le 12 ]
}

pver() {
  "$BB" awk -F= '$1=="package-version" {print $2; exit}' "$1" 2>/dev/null
}

dashboard_live_values() (
  DASH_LIVE=1 DASH_AP_READY=no DASH_STATIONS=
  K_OURAP=no K_AAOK=no K_AAWAIT=no K_AARDY=no DASH_AA_SIGNAL=
  wifi='핫스폿 대기' clients=unknown signal= stage=
  usb_cp_read
  if usb_ap_live; then
    DASH_AP_READY=yes K_OURAP=yes wifi='채널 미확인'
    DASH_AA_SIGNAL=$(dashboard_boot_value "$1" aa "$HINT")
    case "$DASH_AA_SIGNAL" in ok) K_AAOK=yes ;; cpwait) K_AAWAIT=yes ;; esac
    aa_ready=$(dashboard_boot_value "$1" aa_ready "$HINT")
    case "$aa_ready" in ''|*[!0-9]*) ;; *) K_AARDY=yes ;; esac
    if command -v iw >/dev/null 2>&1; then
      wifi=$("$BB_OWN" timeout 1 iw dev "$WIF" info 2>/dev/null | dashboard_radio)
      DASH_STATIONS=$("$BB_OWN" timeout 1 iw dev "$WIF" station dump 2>/dev/null | "$BB_OWN" head -c 32768)
      signal=$(dashboard_station_signal <<EOF
$DASH_STATIONS
EOF
)
    fi
    if [ -z "$wifi" ] || [ "$wifi" = '채널 미확인' ]; then
      channel=$("$BB" awk -F= '$1=="channel" && $2~/^[1-9][0-9]*$/ {print $2; exit}' "$CONF" 2>/dev/null)
      if [ -n "$channel" ]; then wifi="설정 채널 $channel"; fi
    fi
    if [ -x "$APP/bin/ap-station-count" ]; then
      clients=$("$BB_OWN" timeout 1 "$APP/bin/ap-station-count" 2>/dev/null) || clients=unknown
    fi
    case "$clients" in ''|*[!0-9]*) clients=$(usb_realtek_associated_count) || clients=unknown ;; esac
  fi
  case "$clients" in ''|*[!0-9]*) clients='미확인' ;; *) clients="${clients}대" ;; esac
  [ -z "$signal" ] || signal="$signal dBm"
  case "$(dashboard_boot_value "$1" iph "$HINT")" in
    wifi) stage='iPhone의 Wi-Fi 접속 대기' ;;
    nocp) stage='Wi-Fi 단말 감지 · CarPlay 세션 대기' ;;
  esac
  if [ -z "$stage" ] && [ "$DASH_AP_READY" = no ] && usb_wifi_ready; then
    if running "hostapd $CONF"; then stage='핫스폿 주소·DHCP 준비 대기'
    else stage='USB 준비됨 · 핫스폿 시작 대기'; fi
  fi
  [ "$CP_COUNT" != 1 ] || stage='CarPlay 세션 시작 확인'
  K_HMGV=$("$BB" awk '$1=="version" {print $2; exit}' "$HMGDATA/installed.txt" 2>/dev/null)
  V_S1='설치 버전'
  echo "boot=$1"
  echo "sample=$2"
  echo "checked=$(date '+%H:%M:%S')"
  dashboard_rows "$(pver "$APP/NEMESIS.data")" "$(mod_ver)"
  echo "s4=$(dashboard_boot_times "$1")"
  echo "s5=$(dashboard_failure_summary "$1")"
  echo "s6=${wifi:-채널 미확인} · 접속 $clients · 신호 ${signal:-미확인}"
  echo "stage=$stage"
)

dashboard_publish() (
  local owner tmp
  owner=$("$BB_OWN" stat -c %u "$DASH_APP" 2>/dev/null) || exit 1
  case "$owner" in ''|*[!0-9]*) exit 1 ;; esac
  [ "$owner" -ge 10000 ] || exit 1
  tmp=$("$BB_OWN" mktemp "${DASH_STATE}.XXXXXX") || exit 1
  trap '"$BB_OWN" rm -f "$tmp"' EXIT
  dashboard_live_values "$1" "$2" > "$tmp" &&
    "$BB_OWN" chown "0:$owner" "$tmp" &&
    "$BB_OWN" chmod 0640 "$tmp" &&
    "$BB_OWN" mv -f "$tmp" "$DASH_STATE"
)

# The service sleeps without running probes when no foreground app holds a lease.
trap 'exit 0' TERM INT
trap '"$BB_OWN" rm -f "$DASH_STATE"' EXIT
next=0
boot=
read -r boot < "$BOOT_ID" || exit 1
[ -n "$boot" ] || exit 1
while :; do
  now=$(dashboard_now) || now=
  if [ -n "$now" ] && dashboard_active "$now"; then
    if [ "$now" -ge "$next" ]; then
      dashboard_publish "$boot" "$now"
      next=$((now + 5))
    fi
  else
    [ ! -e "$DASH_STATE" ] || "$BB_OWN" rm -f "$DASH_STATE"
    next=0
  fi
  sleep 1
done
