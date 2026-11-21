usb_ap_ht_capab() {
  if [ "$(getprop persist.kp.ap.ht20 2>/dev/null)" = 1 ]; then
    echo '[SHORT-GI-20]'
  else
    echo '[HT40+][SHORT-GI-20][SHORT-GI-40]'
  fi
}

# Only a confirmed BT attach on the current AP can start this window.
# Keep the first attach after the last terminal event, even if created or
# another attach has since replaced it in the live property.
usb_ap_hold_restart() {
  local uptime header
  [ "$(getprop persist.kp.ap.hold 2>/dev/null)" = 1 ] && usb_ap_live || return 1
  usb_cp_read
  case "$CP_STATE" in bt_attach|created) ;; *) USB_AP_HOLD_ANCHOR=; return 1 ;; esac
  read -r uptime _ < "$UPTIME" || return 1
  case "$uptime" in ''|*[!0-9.]*|.*|*.*.*) return 1 ;; esac
  read -r USB_AP_HOLD_REMAINING USB_AP_HOLD_ANCHOR <<EOF
$(
    {
      if [ -r "$W/usb-carplay-events.log" ]; then
        {
          IFS= read -r header
          [ "$header" != "boot=$CP_EVENT_BOOT" ] || "$BB" cat
        } < "$W/usb-carplay-events.log"
      fi
      [ "$CP_EVENT_BOOT" != "${USB_AP_HOLD_BOOT:-}" ] || echo "${USB_AP_HOLD_ANCHOR:-}"
      echo "$CP_EVENT_RECORD"
    } | usb_cp_record_shape |
    "$BB" awk -F, -v current="$CP_EVENT_RECORD" -v up="$uptime" '
      BEGIN {split(current, event, ","); now=int(up*1000); if (event[5]+0>now) exit}
      $2!=event[2] || $3!=event[3] || $4!=event[4] || $6+0>event[6]+0 || $5+0>now {next}
      $7=="bt_attach" {attach[$6+0]=$0; first_time[$6+0]=$5+0; next}
      $7!="created" && $6+0>ended {ended=$6+0}
      END {
        for (seq in attach)
          if (seq+0>ended && (anchor=="" || first_time[seq]<first)) {first=first_time[seq]; anchor=attach[seq]}
        left=int((90000-now+first)/1000)
        print (anchor!="" && left>0 ? left : 0), anchor
      }')
EOF
  USB_AP_HOLD_BOOT=$CP_EVENT_BOOT
  [ "${USB_AP_HOLD_REMAINING:-0}" -gt 0 ] || return 1
  if [ "$USB_AP_HOLD_REMAINING" -lt 30 ]; then
    USB_AP_RECHECK=$USB_AP_HOLD_REMAINING
  fi
  return 0
}
