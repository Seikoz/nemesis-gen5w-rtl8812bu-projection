# Included in hotspot.sh by build.py.
usb_target() {
  case "$(getprop ro.build.product)" in
    CN7NPE.KOR.0000.V039.001.260902|CN7NPE.KOR.S5W_M.V039.001.260902) ;;
    *) return 1 ;;
  esac
  [ "$(getprop ro.board.platform)" = tcc803x ]
}

usb_a3000mini_paths() (
  for device in "$USB_SYS"/*; do
    [ -r "$device/idVendor" ] && [ -r "$device/idProduct" ] || continue
    read -r vendor < "$device/idVendor" && read -r product < "$device/idProduct" || continue
    [ "$vendor:$product" != 0bda:b812 ] || echo "$device"
  done
)

usb_wifi_ready() (
  [ -d "$WLAN" ] && [ -d "$PROC/net/rtl88x2bu/$WIF" ] || return 1
  for device in $(usb_a3000mini_paths); do
    for intf in "$device":*; do
      [ -d "$intf/driver" ] || continue
      driver=$(cd -P "$intf/driver" && pwd -P) || continue
      [ "${driver##*/}" = rtl88x2bu ] && return 0
    done
  done
  return 1
)

usb_launch_if_needed() {
  local paths device number device_key now launch_log rc
  paths=$(usb_a3000mini_paths)
  if [ -z "$paths" ] || usb_wifi_ready; then
    KP_USB_DEVICE=
    return 0
  fi
  for device in $paths; do break; done
  number=
  if [ -r "$device/devnum" ]; then read -r number < "$device/devnum"; fi
  device_key="${device##*/}:$number"
  if [ "${KP_USB_DEVICE:-}" != "$device_key" ]; then
    KP_USB_DEVICE=$device_key
    KP_USB_TRIES=0
    KP_USB_LAST=0
  fi
  [ "$KP_USB_TRIES" -lt 3 ] || return 0
  now=$(prog_up)
  case "$now" in ''|*[!0-9]*) return 0 ;; esac
  [ "$KP_USB_TRIES" -eq 0 ] || [ "$((now - KP_USB_LAST))" -ge 12 ] || return 0
  KP_USB_LAST=$now
  KP_USB_TRIES=$((KP_USB_TRIES + 1))
  launch_log="$W/usb-realtek-launch.log"
  rc=0
  if [ "$KP_USB_TRIES" -eq 1 ]; then
    log "USB Realtek Launch: NEMESIS pkg-launch ($device_key)"
    "$BB_OWN" timeout 20 /system/xbin/nemesis pkg-launch realtek.88x2bu >> "$launch_log" 2>&1 || rc=$?
  elif [ "$KP_USB_TRIES" -eq 2 ]; then
    # Use the same script and arguments as the Launch button if dispatch did not create rtwlan0.
    log "USB Realtek Launch: direct load.sh ($device_key, attempt $KP_USB_TRIES)"
    /system/bin/sh /data/nemesis/apps/realtek.88x2bu/scripts/load.sh >> "$launch_log" 2>&1 || rc=$?
  else
    # The driver's boot mode checks the USB ID, authorization and interface
    # before reapplying the existing configuration at most once per boot.
    log "USB Realtek Launch: guarded driver boot recovery ($device_key)"
    /system/bin/sh /data/nemesis/apps/realtek.88x2bu/scripts/load.sh --boot >> "$launch_log" 2>&1 || rc=$?
  fi
  if usb_wifi_ready; then
    log "USB Realtek Launch: rtwlan0 ready (exit $rc)"
  else
    log "USB Realtek Launch: rtwlan0 still missing (exit $rc)"
  fi
}

usb_setup() {
  CLASSPATH="$APP/hmgapi/setup.jar" /system/bin/app_process /system/bin usbprojection.UsbProjectionSetup "$@"
}

usb_network() {
  usb_setup "$1" "$HMGDATA/settings/hmgapi.json" "$BK/usb-network.ours"
}

usb_start_hostapd() {
  (
    rc=0
    hostapd "$CONF" || rc=$?
    echo "hostapd exit=$rc"
  ) 2>&1 | "$BB" awk -v config="$CONF" '
    function hide(line, secret, out, n) {
      if (secret == "") return line
      while ((n = index(line, secret)) > 0) {
        out = out substr(line, 1, n - 1) "[redacted]"
        line = substr(line, n + length(secret))
      }
      return out line
    }
    BEGIN {
      while ((getline row < config) > 0) {
        if (index(row, "ssid=") == 1) ssid = substr(row, 6)
        if (index(row, "wpa_passphrase=") == 1) key = substr(row, 16)
      }
      close(config)
      print "hostapd startup: rtwlan0, KR, channel 149, HT40+"
    }
    emitted < 80 {
      line = hide(hide($0, ssid), key)
      lower = tolower(line)
      if (lower ~ /hexdump|ssid|password|passphrase|wpa_psk|pairwise key|group key/) {
        if (lower ~ /fail|error|invalid|unknown/) {
          print "hostapd reported an SSID or key configuration error."
          emitted++
        }
        next
      }
      if (lower ~ /nl80211|err|fail|could not|cannot|not supported|not permitted|no such|invalid|unknown|disabled|enabled|frequency|freq=|channel|regulatory|ctrl_iface|ht40|configuration file|hostapd exit=/) {
        print line
        emitted++
      }
    }
  ' > "$W/usb-hostapd.log"
}

usb_ap_live() {
  usb_wifi_ready && running "hostapd $CONF" && wlan_has_ip && our_dhcp_on
}

usb_ap_progress() {
  if usb_ap_live; then
    if [ ! -f "$W/usb.ap.ready" ]; then
      : > "$W/usb.ap.ready"
      log "USB AP ready: rtwlan0, hostapd and DHCP/1067"
      prog 100 done "USB Wi-Fi AP ready (rtwlan0). Pair the iPhone over Bluetooth."
    fi
  elif [ -f "$W/usb.ap.ready" ]; then
    rm -f "$W/usb.ap.ready"
    prog 100 fail "USB Wi-Fi AP lost (rtwlan0). Check the dongle and driver."
  elif usb_wifi_ready && ! running "hostapd $CONF" && [ -s "$W/usb-hostapd.log" ]; then
    prog 100 fail "USB Wi-Fi is ready, but hostapd failed. Save the Korea Projection report."
  fi
}
