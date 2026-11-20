# The root AP service publishes a new generation before advertising AP readiness.
# A callback from an older boot, netdev, AP cycle or dead DiPO process cannot connect the UI.
usb_cp_generation() {
  local generation index= boot= up=
  generation=$(getprop sys.kp.cp_gen 2>/dev/null)
  if [ "$1" = 1 ]; then
    read -r index < "$WLAN/ifindex" || index=unknown
    if [ "$(getprop "$AAPROP" 2>/dev/null)" = 1 ]; then
      case "$generation" in *-"$index") return 0 ;; esac
    fi
    read -r boot < "$PROC/sys/kernel/random/boot_id" || boot=unknown
    read -r up _ < "$UPTIME" || up=unknown
    generation="${boot%%-*}-$up-$index"
    setprop sys.kp.cp_gen "$generation" 2>/dev/null || return 1
  elif [ "$generation" != off ]; then
    setprop sys.kp.cp_gen off 2>/dev/null || return 1
  fi
}

# Only the strict machine record emitted by our session hooks is consumed.
usb_cp_record_shape() {
  "$BB" awk -F, 'NF==8 && $1=="v1" && $2~/^[1-9][0-9]*$/ &&
    $3~/^[0-9]+$/ && $4~/^[a-zA-Z0-9.-]+$/ && $5~/^[0-9]+$/ && $6~/^[0-9]+$/ &&
    $7~/^(idle|bt_attach|created|started|wired|unclassified|finalized)$/ && $8~/^-?[0-9]+$/ {print}'
}

usb_cp_read() {
  local property cached= boot= record pid start generation millis seq state transport actual=
  CP_STATE=unknown CP_SOURCE=unavailable CP_COUNT=0
  property=$(getprop sys.kp.cp_session 2>/dev/null | usb_cp_record_shape)
  read -r boot < "$PROC/sys/kernel/random/boot_id" || return 0
  if [ -r "$W/usb-cp-state" ]; then
    read -r record cached < "$W/usb-cp-state"
    [ "$record" = "boot=$boot" ] || cached=
  fi
  record=$("$BB" printf '%s\n%s\n' "$cached" "$property" | usb_cp_record_shape |
    "$BB" awk -F, '$5+0>time || ($5+0==time && $6+0>=seq) {v=$0; time=$5+0; seq=$6+0} END {print v}')
  [ -n "$record" ] || return 0
  IFS=, read -r record pid start generation millis seq state transport <<EOF
$record
EOF
  [ "$generation" = "$(getprop sys.kp.cp_gen 2>/dev/null)" ] && [ "$generation" != off ] || {
    CP_STATE=stale-ap; return 0;
  }
  # /proc/<pid>/stat comm may contain spaces or parentheses. starttime is field 22.
  actual=$("$BB" awk '{sub(/^.*\) /, ""); print $20}' "$PROC/$pid/stat" 2>/dev/null)
  [ -n "$actual" ] && [ "$actual" = "$start" ] || { CP_STATE=process-gone; return 0; }
  if [ "$state" = started ] && ! "$BB" awk -v event="$millis" '
    NR==1 {now=$1*1000; exit !(now>=event && now-event<=60000)}' "$UPTIME" 2>/dev/null; then
    CP_STATE=stale-session; return 0
  fi
  CP_STATE=$state CP_SOURCE=session-callback
  if [ "$state" = started ] && { [ "$transport" = 0 ] || [ "$transport" = 1 ]; } &&
     [ "$(getprop "$AAPROP" 2>/dev/null)" = 1 ] && usb_wifi_ready; then CP_COUNT=1; fi
}

usb_cp_poll() {
  local snapshot boot= record old= selected property
  read -r boot < "$PROC/sys/kernel/random/boot_id" || return 0
  snapshot=$("$BB" mktemp "$W/.usb-cp-events.XXXXXX") || return 0
  # The raw buffer is never written to the report: copy only our exact records.
  {
    "$BB_OWN" timeout 3 logcat -d -t 2000 -v brief '*:V' 2>/dev/null
    echo "USB_CP_CAPTURE_EXIT=$?"
  } | "$BB" awk -v file="$W/usb-cp-capture.log" -v boot="$boot" '
    /^USB_CP_CAPTURE_EXIT=[0-9]+$/ {print "boot=" boot > file; print > file; close(file); next}
    /USB_CP_EVENT v1,/ {sub(/^.*USB_CP_EVENT /, ""); print}' |
    usb_cp_record_shape > "$snapshot"
  property=$(getprop sys.kp.cp_session 2>/dev/null | usb_cp_record_shape)
  [ -z "$property" ] || "$BB" printf '%s\n' "$property" >> "$snapshot"
  if [ -r "$W/usb-cp-state" ]; then
    read -r record old < "$W/usb-cp-state"
    [ "$record" = "boot=$boot" ] || old=
  fi
  # Keep the original events (including created -> started -> finalized in one poll).
  {
    echo "boot=$boot"
    { [ ! -f "$W/usb-carplay-events.log" ] ||
        "$BB" awk -v b="boot=$boot" 'NR==1 {ok=($0==b);next} ok {print}' "$W/usb-carplay-events.log"
      cat "$snapshot"
    } | "$BB" awk '!seen[$0]++ {line[n++%120]=$0} END {for(i=(n>120?n-120:0);i<n;i++) print line[i%120]}'
  } > "$W/.usb-carplay-events.next" && "$BB" mv -f "$W/.usb-carplay-events.next" "$W/usb-carplay-events.log"
  selected=$( { "$BB" printf '%s\n' "$old"; cat "$snapshot"; } | usb_cp_record_shape |
    "$BB" awk -F, '$5+0>time || ($5+0==time && $6+0>=seq) {v=$0;time=$5+0;seq=$6+0} END {print v}')
  if [ -n "$selected" ]; then
    echo "boot=$boot $selected" > "$W/.usb-cp-state.next" &&
      "$BB" mv -f "$W/.usb-cp-state.next" "$W/usb-cp-state"
  fi
  "$BB" rm -f "$snapshot"
}

cp_count() { usb_cp_read; echo "$CP_COUNT"; }

cp_watch() {
  usb_cp_poll
  usb_cp_read
  if [ "${CP_LAST_STATE:-}" != "$CP_STATE:$CP_COUNT" ]; then
    log "USB CarPlay session=$CP_STATE connected=$CP_COUNT source=$CP_SOURCE"
    CP_LAST_STATE="$CP_STATE:$CP_COUNT"
  fi
  echo "$CP_COUNT" > "$CPN"
  usb_watch_carplay_audio
  usb_client_progress
  usb_connection_tick
}
