# Linux reports EPERM for both a permissions denial and some 88x2bu open failures.
usb_ap_net_admin() {
  local caps
  caps=$("$BB" awk '$1 == "CapEff:" { print $2; exit }' "$PROC/$$/status" 2>/dev/null)
  case "$caps" in ''|*[!0-9a-fA-F]*) return 1 ;; esac
  caps=${caps#"${caps%????}"}
  [ "$((0x$caps & 4096))" -ne 0 ]
}

usb_ap_rebind() (
  local boot_id="$1" paths dev driver intf devnum current vendor product authorized config marker stale attempt
  usb_target && usb_wifi_ready && ! running "hostapd $CONF" || return 1
  paths=$(usb_projection_paths)
  set -- $paths
  [ "$#" -eq 1 ] || return 1
  dev=$1
  driver="${USB_SYS%/devices}/drivers/rtl88x2bu"
  intf="${dev##*/}:1.0"
  set -- "$driver/"*:*
  [ "$#" -eq 1 ] && [ "$1" = "$driver/$intf" ] && [ -L "$1" ] || return 1
  [ -w "$driver/unbind" ] && [ -w "$driver/bind" ] || return 1
  cd -P "$dev" || return 1
  read -r vendor < idVendor && read -r product < idProduct &&
    [ "$vendor:$product" = 0bda:b812 ] && [ -L "$intf/driver" ] &&
    read -r devnum < devnum && read -r authorized < authorized &&
    read -r config < bConfigurationValue && [ "$authorized:$config" = 1:1 ] || return 1
  case "$boot_id" in ''|*[!0-9a-f-]*) return 1 ;; esac
  marker="$W/.ap-rebind-$boot_id"
  if ! mkdir "$marker" 2>/dev/null; then
    echo "A3000mini rebind already attempted this boot or marker unavailable."
    return 1
  fi
  for stale in "$W"/.ap-rebind-*; do
    [ "$stale" = "$marker" ] || rmdir "$stale" 2>/dev/null
  done

  stop_ours
  echo "Rebinding A3000mini interface $intf (device $devnum)."
  echo "$intf" > "$driver/unbind" || return 1
  # The pinned device must still be at that port after unbind.
  read -r current < devnum && [ "$current" = "$devnum" ] &&
    read -r vendor < idVendor && read -r product < idProduct &&
    [ "$vendor:$product" = 0bda:b812 ] || return 1
  if [ ! -L "$intf/driver" ]; then
    echo "$intf" > "$driver/bind" || return 1
  fi
  attempt=0
  while ! usb_wifi_ready; do
    [ "$attempt" -lt 5 ] || return 1
    sleep 1
    attempt=$((attempt + 1))
  done
)

usb_prepare_ap_interface() {
  local up_error up_rc hostapd_eperm=0 rebind_rc retry_error retry_rc snapshot started
  local failure_log="$W/usb-hostapd-logcat-$AP_PHASE.log"
  if [ -n "$AP_BOOT" ] &&
     [ -r "$failure_log" ] &&
     "$BB" awk -v scope="$AP_SCOPE " -v iface="$WIF" '
       NR == 1 && index($0, scope) != 1 { exit }
       index($0, "Could not set interface " iface " flags (UP): Operation not permitted") { matched = 1; exit }
       END { exit !matched }
     ' "$failure_log" 2>/dev/null; then
    hostapd_eperm=1
  fi
  snapshot=$("$BB" mktemp "$W/.usb-ap-up.XXXXXX")
  if [ -z "$snapshot" ]; then
    "$BB" ifconfig "$WIF" "$AP_IP" netmask 255.255.255.0 up 2>/dev/null
    return
  fi
  {
    usb_ap_report_header
    echo "Korea Projection service permissions:"
    usb_ap_process_info "$$"
    echo "Kernel messages before UP:"
    usb_ap_kernel_log "" 20
    started=$(usb_ap_uptime)
    up_error=$("$BB" ifconfig "$WIF" "$AP_IP" netmask 255.255.255.0 up 2>&1)
    up_rc=$?
    echo "rtwlan0 ifconfig UP exit=$up_rc uptime=$started"
    [ -z "$up_error" ] || echo "$up_error"
    echo "hostapd_up_eperm=$hostapd_eperm"
    case "$hostapd_eperm:$up_rc:$up_error" in
      1:*|0:[1-9]*:*"Operation not permitted"*)
        if [ "$AP_USB_ID" != 0bda:b812 ]; then
          echo "USB AP rebind skipped for ID ${AP_USB_ID:-unknown}."
        elif [ -d "$W/.ap-rebind-$AP_BOOT" ]; then
          echo "A3000mini rebind already attempted this boot."
        elif usb_ap_net_admin; then
          usb_ap_rebind "$AP_BOOT"
          rebind_rc=$?
          echo "A3000mini rebind exit=$rebind_rc"
          if [ "$rebind_rc" -eq 0 ]; then
            retry_error=$("$BB" ifconfig "$WIF" "$AP_IP" netmask 255.255.255.0 up 2>&1)
            retry_rc=$?
            up_rc=$retry_rc
            echo "rtwlan0 retry: ifconfig exit=$retry_rc"
            [ -z "$retry_error" ] || echo "$retry_error"
          fi
        else
          echo "A3000mini rebind skipped: service CAP_NET_ADMIN unavailable."
        fi
        ;;
    esac
    echo "Kernel messages since UP:"
    usb_ap_kernel_log "$started" 40
  } > "$snapshot"
  usb_ap_publish_attempt "$snapshot" "$AP_UP_FILE"
  return "$up_rc"
}
