# Compose the existing StatusActivity summary rows. These are display-only.
dashboard_usb_device() (
  net_device=$(cd -P "$WLAN/device" 2>/dev/null && pwd -P) || net_device=
  found= count=0
  for device in $(usb_projection_paths); do
    count=$((count + 1))
    found=$device
    [ -n "$net_device" ] || continue
    path=$(cd -P "$device" && pwd -P) || continue
    case "$net_device" in "$path"|"$path"/*) echo "$device"; exit 0 ;; esac
  done
  case "$count" in
    0) return 0 ;;
    1) echo "$found" ;;
    *) echo multiple ;;
  esac
)

dashboard_usb_summary() (
  device=$(dashboard_usb_device)
  case "$device" in
    '') echo '지원 USB 동글 없음'; exit 0 ;;
    multiple) echo 'USB 동글 여러 개 · 사용 모델 확인 불가'; exit 0 ;;
  esac
  vendor= product= label= speed=
  read -r vendor < "$device/idVendor" && read -r product < "$device/idProduct" || exit 0
  case "$vendor:$product" in
    2357:012d) model='Archer T3U V1' ;;
    0bda:b812)
      { IFS= read -r label < "$device/product"; } 2>/dev/null
      case "$label" in
        *[Aa]3000[Mm][Ii][Nn][Ii]*) model='ipTIME A3000mini' ;;
        *NX-AC1300*|*NX1126*) model='NEXI NX-AC1300' ;;
        *) model='RTL8812BU' ;;
      esac
      ;;
    *) exit 0 ;;
  esac
  { read -r speed < "$device/speed"; } 2>/dev/null
  case "$speed" in
    1.5|12|480|5000|10000|20000) echo "$model ($vendor:$product) · USB $speed Mbps" ;;
    *) echo "$model ($vendor:$product) · USB 속도 미확인" ;;
  esac
)

dashboard_station_rate() {
  # A rate belongs to a specific station. With multiple stations there is no
  # evidence for which station is the CarPlay or Android Auto peer.
  "$BB" awk '
    /^Station / {count++; authorized=0; rate=""; next}
    $1=="authorized:" && $2=="yes" {authorized=1}
    $1=="tx" && $2=="bitrate:" && $3 ~ /^[0-9]+([.][0-9]+)?$/ &&
      $3+0>0 && $4=="MBit/s" {rate=$3}
    END {if (count==1 && authorized && rate!="") print rate}
  '
}

dashboard_radio() {
  "$BB" awk '
    $1=="channel" && $2~/^[0-9]+$/ {
      ch=$2; f=$3; sub(/^\(/,"",f)
      if (f !~ /^[0-9]+$/ || $4 !~ /^MHz[)]?/) next
      split($0,w,"width: ")
      split(w[2],fields," ")
      width=(fields[1]~/^[0-9]+$/ && fields[2]~/^MHz[,)]?$/) ? " · " fields[1] " MHz" : ""
      band=(f>=5925 && f<=7125) ? "6 GHz" : ((f>=4900 && f<5925) ? "5 GHz" : ((f>=2400 && f<2500) ? "2.4 GHz" : f " MHz"))
      print band " 채널 " ch width
      exit
    }
  '
}

dashboard_station_signal() {
  "$BB" awk '
    /^Station / {count++; authorized=0; signal=""; next}
    $1=="authorized:" && $2=="yes" {authorized=1}
    $1=="signal:" && $2 ~ /^-[0-9]+$/ && $2+0>=-127 && $NF=="dBm" {signal=$2}
    END {if (count==1 && authorized && signal!="") print signal}
  '
}

dashboard_ssid() {
  # Read only the active USB AP name. Never emit the rest of the hostapd config.
  LC_ALL=C "$BB" awk '/^ssid=/ {gsub(/[[:cntrl:]]/, ""); print substr($0,6,32); exit}' "$CONF" 2>/dev/null
}

dashboard_gps_fix() {
  # Android 4.4 exposes local GPS provider fixes with elapsed-realtime ages.
  "$BB" awk -v now="$1" '
    function elapsed(value, n, part, suffix, total, previous, order) {
      if (value !~ /^\+/) return -1
      sub(/^\+/, "", value)
      previous=6
      while (match(value, /^[0-9]+(ms|[dhms])/)) {
        part=substr(value,1,RLENGTH)
        value=substr(value,RLENGTH+1)
        suffix=part
        sub(/^[0-9]+/, "", suffix)
        n=part+0
        if (suffix=="d") {order=5; total+=n*86400}
        else if (suffix=="h") {order=4; total+=n*3600}
        else if (suffix=="m") {order=3; total+=n*60}
        else if (suffix=="s") {order=2; total+=n}
        else {order=1; total+=n/1000}
        if (order>=previous) return -1
        previous=order
      }
      return (value=="" && previous!=6) ? total : -1
    }
    /^[[:space:]]*Last Known Locations:$/ {section=1; next}
    section && /^[[:space:]]*Last Known Locations Coarse Intervals:$/ {exit}
    section && /^[[:space:]]*gps: Location\[gps / && $0 !~ /[[:space:]]mock([[:space:]]|\]|$)/ {
      for (i=1; i<=NF; i++) if ($i ~ /^et=\+/) {
        stamp=$i; sub(/^et=/, "", stamp); sub(/\]$/, "", stamp)
        seconds=elapsed(stamp)
        if (seconds>=0 && now>=seconds && now-seconds<=30) print "recent"
        exit
      }
    }
  '
}

dashboard_phone_summary() (
  carplay='미연결' aa='미연결'
  if [ "$1" != yes ]; then
    carplay='AP 대기'; aa='AP 대기'
  else
    case "$CP_COUNT:$CP_STATE" in
      1:*) carplay='연결됨' ;;
      0:bt_attach) carplay='블루투스 연결 중' ;;
      0:created) carplay='세션 시작 대기' ;;
      0:finalized|0:idle|0:wired) ;;
      *) carplay='미확인' ;;
    esac
    if [ "$K_AAWAIT" = yes ]; then aa='CarPlay 종료 대기'
    elif [ "$K_AAOK" = yes ]; then aa='연결 감지'
    elif [ "${DASH_AA_SIGNAL:-}" = bt ]; then aa='블루투스 연결 재시도 대기'
    elif [ "$K_AARDY" = yes ]; then aa='연결 가능'
    else aa='미확인'; fi
  fi
  echo "무선 연결 · iPhone CarPlay $carplay · Android Auto $aa"
)

dashboard_rows() (
  usb=$(dashboard_usb_summary)
  ap=no ap_label='대기' ssid= rate= gps=
  if [ "$K_OURAP" = yes ] && { [ "${DASH_AP_READY:-}" = yes ] || usb_ap_live; }; then
    ap=yes ap_label='준비됨'
    ssid=$(dashboard_ssid)
    if [ "${DASH_LIVE:-0}" = 1 ]; then
      rate=$(dashboard_station_rate <<EOF
$DASH_STATIONS
EOF
)
    elif command -v iw >/dev/null 2>&1; then
      rate=$("$BB_OWN" timeout 2 iw dev "$WIF" station dump 2>/dev/null | dashboard_station_rate)
    fi
  fi
  [ -z "$rate" ] || rate="$rate Mbps"
  read -r uptime _ < "$UPTIME" || uptime=
  case "$uptime" in
    ''|*[!0-9.]*) ;;
    *) gps=$("$BB_OWN" timeout 2 dumpsys location short 2>/dev/null | dashboard_gps_fix "$uptime") ;;
  esac
  case "$gps" in
    recent) gps='최근 수신' ;;
    *) gps='수신 미확인' ;;
  esac
  driver=$(pver "${KP_REALTEK_DESCRIPTOR:-/data/nemesis/apps/realtek.88x2bu/NEMESIS.data}")
  echo "s1=$V_S1 · 합본 v@BUNDLE_VERSION@ · KP ${1:-미확인} · Realtek ${driver:-미확인} · HMG-API ${K_HMGV:-미확인} · Wireless ${2:-미확인}"
  echo "s2=무선랜 ${usb:-미확인} · 핫스폿 $ap_label · SSID ${ssid:-미확인} · Wi-Fi 송신 링크 ${rate:-미확인}"
  if [ "${DASH_LIVE:-0}" = 1 ]; then
    echo "s3=$(dashboard_phone_summary "$ap")"
    echo "gps_fix=$gps"
  else
    echo "s3=$(dashboard_phone_summary "$ap") · 차량 GPS $gps · 휴대폰 GPS 연동 확인 불가"
  fi
)

dashboard_boot_times() {
  "$BB" awk -F= -v boot="$1" '
    NR==1 && $0!="boot=" boot {exit}
    $2~/^[0-9]+([.][0-9]+)?$/ {
      if ($1=="usb_480_interface_ready") usb=int($2) "초"
      if ($1=="ap_ready") ap=int($2) "초"
    }
    END {
      print "USB 480Mbps·인터페이스 " (usb!=""?usb:"미확인") " · 핫스폿 준비 " (ap!=""?ap:"미확인")
    }' "$W/usb-boot-timing.log" 2>/dev/null
}

dashboard_boot_value() {
  "$BB" awk -F= -v boot="$1" -v key="$2" '
    $1=="boot" {current=($2==boot)}
    $1==key {value=$2}
    END {if (current) print value}' "$3" 2>/dev/null
}

dashboard_note_failure() (
  boot=${BID:-}
  [ -n "$boot" ] || read -r boot < "$BOOT_ID" || exit 0
  read -r up _ < "$UPTIME" || exit 0
  case "$1" in
    *480Mbps*) code=usb ;;
    *hostapd*) code=hostapd ;;
    *"AP lost"*) code=ap_lost ;;
    *"차량 지도"*) code=map ;;
    *"오디오 자동 적용"*) code=audio ;;
    *credentials*|*softap.conf*) code=credentials ;;
    *) code=setup ;;
  esac
  umask 077
  tmp=$("$BB_OWN" mktemp "$W/.dashboard-failure.XXXXXX") || exit 0
  echo "boot=$boot" > "$tmp" && echo "reason=$code" >> "$tmp" &&
    echo "at=${up%%.*}" >> "$tmp" &&
    "$BB_OWN" mv -f "$tmp" "$W/dashboard-failure" || "$BB_OWN" rm -f "$tmp"
)

dashboard_failure_summary() (
  reason=$(dashboard_boot_value "$1" reason "$W/dashboard-failure")
  at=$(dashboard_boot_value "$1" at "$W/dashboard-failure")
  case "$reason" in
    usb) message='USB 480Mbps 인식 대기' ;;
    hostapd) message='핫스폿 시작 실패' ;;
    ap_lost) message='핫스폿 연결 끊김' ;;
    map) message='HMG-API 차량 지도 확인 실패' ;;
    audio) message='오디오 자동 적용 보류' ;;
    credentials) message='순정 Wi-Fi 설정 읽기 실패' ;;
    setup) message='무선 설정 실패' ;;
    *) echo '이번 부팅에 기록된 실패 없음'; exit 0 ;;
  esac
  case "$at" in ''|*[!0-9]*) echo "$message" ;; *) echo "$message · 부팅 후 ${at}초" ;; esac
)
