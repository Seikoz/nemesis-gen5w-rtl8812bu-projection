# Snapshot the AP's current clients instead of accumulating vendor log messages.
usb_realtek_associated_count() {
  local file="$PROC/net/rtl88x2bu/$WIF/all_sta_info" own=
  [ -r "$file" ] && read -r own < "$WLAN/address" || return 1
  "$BB" awk -v own="$own" '
    function hex(s, i, n, d) {
      n=0; s=tolower(s); sub(/^0x/, "", s)
      if (s == "") return -1
      for (i=1; i<=length(s); i++) {
        d=index("0123456789abcdef",substr(s,i,1))-1
        if (d<0) return -1
        n=n*16+d
      }
      return n
    }
    /^sta_dz_bitmap=/ { header1=1 }
    /^tim_bitmap=/ { header2=1 }
    /^sta.s macaddr:/ {
      if (mac!="") bad=1
      mac=tolower(substr($0,index($0,":")+1))
      if (split(mac,oct,":")!=6) bad=1
      for (i=1;i<=6;i++) if (length(oct[i])!=2 || hex(oct[i])<0) bad=1
      next
    }
    /^state=0x/ {
      if (mac=="") { bad=1; next }
      state=$0; sub(/^state=/,"",state); sub(/,.*/,"",state)
      aid=$0; sub(/^[^,]*,[[:space:]]*aid=/,"",aid); sub(/,.*/,"",aid)
      state=hex(state)
      if (state<0 || aid !~ /^[0-9]+$/) bad=1
      if (state%2==1 && aid+0>0 && hex(substr(mac,1,2))%2==0 && mac!=tolower(own) && !(mac in seen)) {
        seen[mac]=1; n++
      }
      mac=""
    }
    END {
      if (!header1 || !header2 || mac!="" || bad) exit 1
      print n+0
    }' "$file" 2>/dev/null
}

usb_client_progress() {
  usb_cp_read
  usb_ap_live || { USB_CLIENT_DISPLAY=; return 0; }
  [ ! -f "$PROG" ] || "$BB" grep -q '^state=done$' "$PROG" || return 0
  if [ "${USB_CLIENT_DISPLAY:-}" = "$AP_SCOPE:$STA_COUNT:$STA_SOURCE:$CP_STATE:$CP_COUNT" ] &&
     "$BB" grep -q 'Wi-Fi 접속 단말 수:' "$PROG" 2>/dev/null; then return 0; fi
  USB_CLIENT_DISPLAY="$AP_SCOPE:$STA_COUNT:$STA_SOURCE:$CP_STATE:$CP_COUNT"
  local session_text='CarPlay 세션 확인 불가 (연결 미확인).'
  case "$CP_STATE" in
    idle|bt_attach) session_text='카플레이 연결 대기 중 (세션 시작 미확인).' ;;
    created) session_text='카플레이 세션 생성됨 (시작 대기).' ;;
    finalized) session_text='카플레이 세션 종료됨.' ;;
    stale-ap|stale-session|process-gone) session_text='카플레이 세션 재확인 대기 중.' ;;
    wired) session_text='유선 카플레이 세션 감지됨.' ;;
  esac
  if [ "$CP_COUNT" = 1 ]; then session_text='무선 카플레이 연결됨 (실제 세션 시작 확인).'; fi
  if [ "$STA_COUNT" = unknown ]; then
    prog 100 done "USB Wi-Fi AP ready (rtwlan0). $session_text Wi-Fi 접속 단말 수: 확인 불가."
  else
    prog 100 done "USB Wi-Fi AP ready (rtwlan0). $session_text Wi-Fi 접속 단말 수: ${STA_COUNT}대."
  fi
}

wifi_events() {
  local count= previous="${WSTA:-0}"
  STA_COUNT=unknown STA_SOURCE=unavailable WSTA=0 WGONE=
  if ! running "hostapd $CONF" || ! usb_wifi_ready; then
    STA_COUNT=0 STA_SOURCE=ap-off
  elif count=$("$APP/bin/ap-station-count" 2>/dev/null); then
    STA_COUNT=$count STA_SOURCE=hostapd-authorized
  elif count=$(usb_realtek_associated_count); then
    STA_COUNT=$count STA_SOURCE=realtek-associated
  fi
  case "$STA_COUNT" in ''|*[!0-9]*) STA_COUNT=unknown ;; *) WSTA=$STA_COUNT ;; esac
  if [ "$STA_COUNT" = unknown ] && [ "${HI:-}" = wifi ]; then
    HI= HI_T= HI_U=
    hint_write
  fi
  if [ "$STA_COUNT" != unknown ]; then
    if [ "$WSTA" -gt 0 ] && [ "$previous" -eq 0 ]; then
      read -r WCONN_AT _ < "$UPTIME"
      WCONN_AT=${WCONN_AT%%.*}
    elif [ "$WSTA" -eq 0 ] && [ "$previous" -gt 0 ]; then
      WGONE=1
    fi
  fi
  if [ "${STA_LAST:-}" != "$STA_COUNT:$STA_SOURCE" ]; then
    log "USB Wi-Fi clients=$STA_COUNT source=$STA_SOURCE"
    STA_LAST="$STA_COUNT:$STA_SOURCE"
  fi
}
