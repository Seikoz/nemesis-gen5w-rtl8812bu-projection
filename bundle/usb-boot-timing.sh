# First observations on this boot, in seconds since kernel startup.
usb_boot_mark() {
  local stage="$1" file="$W/usb-boot-timing.log" boot="$BID" saved= up=
  case "$stage" in
    service_start|android_ready|usb_480_interface_ready|ap_prerequisites_ready|ap_ready|carplay_observed) ;;
    *) return 1 ;;
  esac
  [ -n "$boot" ] || read -r boot < "$BOOT_ID" || return 1
  case "$boot" in ''|*[!0-9a-f-]*) return 1 ;; esac
  read -r up _ < "$UPTIME" || return 1
  case "$up" in ''|*[!0-9.]*|.*|*.*.*) return 1 ;; esac
  if [ -r "$file" ]; then
    read -r saved < "$file"
  fi
  if [ "$saved" != "boot=$boot" ]; then
    echo "boot=$boot" > "$file" || return 1
  fi
  "$BB" grep -q "^$stage=" "$file" && return 0
  echo "$stage=$up" >> "$file"
}
