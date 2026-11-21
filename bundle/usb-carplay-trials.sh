usb_trial_boot_id() {
  case "$1" in
    ''|*[!0-9a-f-]*) return 1 ;;
    ????????-????-????-????-????????????) return 0 ;;
    *) return 1 ;;
  esac
}

# Persist completed observations as they are made, even if shutdown is abrupt.
usb_trial_begin() {
  local boot="$BID" root="$BK/usb-carplay-trials" dir other profile ht20=0 hold=0 order
  usb_trial_boot_id "$boot" || return 1
  dir="$root/$boot"
  [ ! -L "$root" ] && [ ! -L "$dir" ] || return 1
  "$BB" mkdir -p "$dir" || return 1
  if [ ! -s "$dir/trial.txt" ]; then
    [ "$(usb_ap_ht_capab)" != '[SHORT-GI-20]' ] || ht20=1
    [ "$(getprop persist.kp.ap.hold 2>/dev/null)" != 1 ] || hold=1
    case "$ht20:$hold" in 0:0) profile=A ;; 1:0) profile=B ;; 0:1) profile=C ;; *) profile=D ;; esac
    {
      echo "boot=$boot"
      echo "trial=$profile ht20=$ht20 restart_hold=$hold"
      echo "started_at=$(date '+%m-%d %H:%M:%S')"
      echo "wireless_mode=$MOD_VER"
    } > "$dir/trial.next" && "$BB" mv -f "$dir/trial.next" "$dir/trial.txt" || return 1
  fi
  # Index in boot order rather than wall time, which may be reset at startup.
  order="$root/order"
  {
    [ ! -r "$order" ] || "$BB" cat "$order"
    echo "$boot"
  } | "$BB" awk 'NF==1 && length($0)==36 && $0~/^[0-9a-f-]+$/ && !seen[$0]++ {
    boots[n++%8]=$0
  } END {for (i=(n>8?n-8:0); i<n; i++) print boots[i%8]}' > "$root/order.next" &&
    "$BB" mv -f "$root/order.next" "$order" || return 1
  USB_TRIAL_DIR=$dir
  USB_TRIAL_BOOT=$boot
  for other in "$root"/*; do
    [ -d "$other" ] && [ ! -L "$other" ] && usb_trial_boot_id "${other##*/}" || continue
    "$BB" grep -Fxq "${other##*/}" "$order" && continue
    "$BB" rm -f "$other"/trial.txt "$other"/trial.next "$other"/ap-events.log "$other"/ap-events.log.next \
      "$other"/usb-carplay-events.log "$other"/usb-carplay-events.log.?????? \
      "$other"/usb-cp-capture.log "$other"/usb-cp-capture.log.?????? \
      "$other"/usb-carplay-audio.log "$other"/usb-carplay-audio.log.?????? \
      "$other"/usb-boot-timing.log "$other"/usb-boot-timing.log.??????
    "$BB" rmdir "$other" 2>/dev/null || :
  done
}

usb_trial_save() {
  local name="$1" file="$W/$1" header temp
  [ -n "${USB_TRIAL_DIR:-}" ] && [ -r "$file" ] || return 0
  read -r header _ < "$file" || return 0
  [ "$header" = "boot=$USB_TRIAL_BOOT" ] || return 0
  temp=$("$BB" mktemp "$USB_TRIAL_DIR/$name.XXXXXX") || return 1
  if "$BB" cp "$file" "$temp" && "$BB" mv -f "$temp" "$USB_TRIAL_DIR/$name"; then
    return 0
  fi
  "$BB" rm -f "$temp"
  return 1
}

usb_trial_ap_event() {
  local file
  [ -n "${USB_TRIAL_DIR:-}" ] || return 0
  file="$USB_TRIAL_DIR/ap-events.log"
  {
    [ ! -r "$file" ] || "$BB" cat "$file"
    echo "$(date '+%m-%d %H:%M:%S') $*"
  } | "$BB" awk '{ev[n++%40]=$0} END {for (i=(n>40?n-40:0); i<n; i++) print ev[i%40]}' > "$file.next" &&
    "$BB" mv -f "$file.next" "$file"
}

# Catch brief or failed attempts near startup, even if the state poll missed them.
usb_trial_audio_window() {
  local now="$1"
  [ -n "${USB_TRIAL_DIR:-}" ] && usb_ap_live || return 1
  if [ -z "${USB_TRIAL_AUDIO_UNTIL:-}" ]; then
    USB_TRIAL_AUDIO_UNTIL=$((now + 180))
  fi
  [ "$now" -lt "$USB_TRIAL_AUDIO_UNTIL" ]
}

usb_trial_report() {
  local root="$BK/usb-carplay-trials" boot dir name
  [ -s "$root/order" ] || return 0
  echo
  echo "== USB CarPlay trial history (last eight boots)"
  while IFS= read -r boot; do
    usb_trial_boot_id "$boot" || continue
    dir="$root/$boot"
    [ ! -L "$dir" ] && [ -s "$dir/trial.txt" ] || continue
    echo
    echo "=== Trial boot $boot"
    lastmask 20 < "$dir/trial.txt"
    for name in ap-events.log usb-boot-timing.log usb-carplay-events.log usb-cp-capture.log usb-carplay-audio.log; do
      echo "--- $name"
      if [ -s "$dir/$name" ]; then
        lastmask 180 < "$dir/$name"
      else
        echo "(No observations saved for this boot.)"
      fi
    done
  done < "$root/order"
}
