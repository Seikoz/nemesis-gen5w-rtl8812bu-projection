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
  paths=$(usb_a3000mini_paths)
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
  local up_error up_rc boot_id= hostapd_eperm=0 rebind_rc retry_error retry_rc snapshot
  up_error=$("$BB" ifconfig "$WIF" "$AP_IP" netmask 255.255.255.0 up 2>&1)
  up_rc=$?
  read -r boot_id < "$PROC/sys/kernel/random/boot_id"
  if [ -n "$boot_id" ] &&
     "$BB" grep -F -q "boot=$boot_id " "$W/usb-hostapd-logcat.log" 2>/dev/null &&
     "$BB" grep -F -q "Could not set interface $WIF flags (UP): Operation not permitted" +       "$W/usb-hostapd-logcat.log"; then
    hostapd_eperm=1
  fi
  [ "$up_rc" -ne 0 ] || [ "$hostapd_eperm" = 1 ] || return 0
  if [ -n "$boot_id" ] && [ -d "$W/.ap-rebind-$boot_id" ] && [ -s "$W/usb-ap-up.log" ]; then
    return 0
  fi
  snapshot=$("$BB" mktemp "$W/.usb-ap-up.XXXXXX") || return 1
  {
    echo "rtwlan0 preflight at $(date '+%m-%d %H:%M:%S'): ifconfig exit=$up_rc"
    [ -z "$up_error" ] || echo "$up_error"
    echo "hostapd_up_eperm=$hostapd_eperm"
    "$BB" awk '/^(Uid|CapEff|CapBnd):/ { print }' "$PROC/$$/status" 2>/dev/null
    echo "service_context=$("$BB" cat "$PROC/$$/attr/current" 2>/dev/null)"
    case "$hostapd_eperm:$up_rc:$up_error" in
      1:*|0:[1-9]*:*"Operation not permitted"*)
        if usb_ap_net_admin; then
          usb_ap_rebind "$boot_id"
          rebind_rc=$?
          echo "A3000mini rebind exit=$rebind_rc"
          if [ "$rebind_rc" -eq 0 ]; then
            retry_error=$("$BB" ifconfig "$WIF" "$AP_IP" netmask 255.255.255.0 up 2>&1)
            retry_rc=$?
            echo "rtwlan0 retry: ifconfig exit=$retry_rc"
            [ -z "$retry_error" ] || echo "$retry_error"
          fi
        else
          echo "A3000mini rebind skipped: service CAP_NET_ADMIN unavailable."
        fi
        ;;
    esac
    echo "Recent kernel messages:"
    dmesg 2>/dev/null | "$BB" awk '
      /SerialNumber|hexdump|ssid|passphrase|password|wpa_psk|secret/ { next }
      /RTW:|rtl88x2bu|rtwlan0/ || /avc:.*denied.*(hostapd|net_admin|rfkill)/ { print }
    ' | "$BB" tail -n 50
  } > "$snapshot"
  "$BB" mv -f "$snapshot" "$W/usb-ap-up.log" || "$BB" rm -f "$snapshot"
}
