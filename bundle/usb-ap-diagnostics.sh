# Record one boot's USB identity independently of network registration.
usb_ap_context() {
  local paths first_boot= first_device= marker="/data/nemesis/logs/realtek.88x2bu/first-usb-device"
  AP_BOOT= AP_PORT= AP_NUMBER= AP_USB_SPEED= AP_FIRST= AP_FIRST_UP= AP_PHASE=boot
  [ ! -r "$PROC/sys/kernel/random/boot_id" ] || read -r AP_BOOT < "$PROC/sys/kernel/random/boot_id"
  paths=${1-$(usb_a3000mini_paths)}
  set -- $paths
  if [ "$#" -eq 1 ]; then
    AP_PORT=${1##*/}
    [ ! -r "$1/devnum" ] || read -r AP_NUMBER < "$1/devnum"
    [ ! -r "$1/speed" ] || read -r AP_USB_SPEED < "$1/speed"
  fi
  AP_DEVICE="${AP_PORT:-unknown}:${AP_NUMBER:-unknown}"
  # Include a fallback for service restarts or a boot-loader enumeration race.
  if [ -r "$marker" ]; then
    read -r first_boot first_device AP_FIRST_UP < "$marker"
  fi
  if [ "$first_boot" = "$AP_BOOT" ] && [ -n "$first_device" ]; then
    AP_FIRST=$first_device
  else
    AP_FIRST_UP=
    if [ "$AP_FIRST_BOOT" != "$AP_BOOT" ]; then
      AP_FIRST_BOOT=$AP_BOOT
      AP_FIRST_DEVICE=
    fi
    if [ -z "$AP_FIRST_DEVICE" ] && [ -n "$AP_NUMBER" ]; then
      AP_FIRST_DEVICE=$AP_DEVICE
    fi
    AP_FIRST=$AP_FIRST_DEVICE
  fi
  if [ -n "$AP_FIRST" ] && [ -n "$AP_NUMBER" ] && [ "$AP_DEVICE" != "$AP_FIRST" ]; then
    AP_PHASE=replug
  fi
  AP_SCOPE="boot=${AP_BOOT:-unknown} usb=$AP_DEVICE"
  AP_UP_FILE="$W/usb-ap-up-$AP_PHASE.log"
}

usb_ap_uptime() {
  local seconds=
  [ ! -r "$PROC/uptime" ] || read -r seconds _ < "$PROC/uptime"
  echo "${seconds:-unknown}"
}

usb_ap_kernel_log() {
  local since="$1" limit="$2"
  {
    dmesg 2>/dev/null
    echo "dmesg_exit=$?"
  } | "$BB" awk -v port="$AP_PORT" -v since="$since" -v limit="$limit" '
    /^dmesg_exit=[0-9]+$/ { status = substr($0,12); next }
    {
      line = $0
      lower = tolower(line)
      if (lower ~ /serialnumber|hexdump|ssid|passphrase|password|wpa_psk|secret/) next
      if (since != "" && since != "unknown") {
        ts = line
        sub(/^<[0-9]+>/, "", ts)
        if (ts ~ /^\[[[:space:]]*[0-9]+\.[0-9]+\]/) {
          sub(/^\[/, "", ts)
          if (ts + 0 < since + 0) next
        }
      }
      if (lower ~ /88x2bu|rtwlan0|(^|[[:space:]])rtw:/ ||
          lower ~ /avc:.*denied.*(hostapd|net_admin|rfkill)/ ||
          lower ~ /ehci-platform|ohci-platform|ehci-mux|ohci-mux/ ||
          (lower ~ /usb [0-9]+-1:/ &&
           lower ~ /new .*usb device|idvendor|descriptor|disconnect|reset|error|config|unable|failed/)) {
        rows[n++ % limit] = substr(line,1,512)
      }
    }
    END {
      if (status != "0") print "dmesg unavailable (exit " (status == "" ? "unknown" : status) ")"
      else if (!n) print "No matching kernel messages."
      for (i = (n > limit ? n - limit : 0); i < n; i++) print rows[i % limit]
    }'
}

usb_ap_report_header() {
  local parameter value
  echo "$AP_SCOPE phase=$AP_PHASE first_usb=${AP_FIRST:-unknown} first_seen_uptime=${AP_FIRST_UP:-unknown} uptime=$(usb_ap_uptime) time=$(date '+%m-%d %H:%M:%S')"
  echo "usb_speed_mbps=${AP_USB_SPEED:-unknown}"
  for parameter in rtw_power_mgnt rtw_ips_mode rtw_enusbss; do
    value=unavailable
    [ ! -r "/sys/module/88x2bu/parameters/$parameter" ] ||
      read -r value < "/sys/module/88x2bu/parameters/$parameter"
    echo "$parameter=$value"
  done
}

# Retain the first and latest observations of each phase in this boot.
usb_ap_publish_attempt() {
  local snapshot="$1" file="$2" next first
  next=$("$BB" mktemp "$W/.usb-ap-report.XXXXXX") || { "$BB" rm -f "$snapshot"; return 1; }
  if [ -r "$file" ] && read -r first < "$file"; then
    case "$first" in
      "boot=${AP_BOOT:-unknown} "*)
        "$BB" awk '/^=== Latest observation ===$/{exit} {print}' "$file" > "$next"
        echo '=== Latest observation ===' >> "$next"
        ;;
    esac
  fi
  if "$BB" cat "$snapshot" >> "$next" && "$BB" mv -f "$next" "$file"; then
    "$BB" rm -f "$snapshot"
  else
    "$BB" rm -f "$snapshot" "$next"
    return 1
  fi
}

usb_ap_report_waiting() {
  local snapshot
  usb_ap_context "$1"
  [ -n "$AP_NUMBER" ] || return 0
  [ "$AP_WAIT_RECORDED" != "$AP_SCOPE" ] || return 0
  snapshot=$("$BB" mktemp "$W/.usb-ap-wait.XXXXXX") || return 0
  {
    usb_ap_report_header
    echo "rtwlan0 not ready; the service has not attempted UP."
    usb_ap_kernel_log "" 30
  } > "$snapshot"
  if usb_ap_publish_attempt "$snapshot" "$AP_UP_FILE"; then
    AP_WAIT_RECORDED=$AP_SCOPE
  fi
}

usb_ap_process_info() {
  local pid="$1" context
  if [ -r "$PROC/$pid/status" ]; then
    "$BB" awk '/^(Name|Uid|Gid|CapInh|CapPrm|CapEff|CapBnd|CapAmb|NoNewPrivs|Seccomp):/ { print }' "$PROC/$pid/status" 2>/dev/null
  else
    echo "Process status unavailable."
  fi
  context=$("$BB" cat "$PROC/$pid/attr/current" 2>/dev/null)
  echo "selinux_context=${context:-unavailable}"
}

usb_capture_hostapd_permissions() {
  local pid="$1" observation="$2" snapshot name= count=0
  snapshot=$("$BB" mktemp "$W/.usb-hostapd-permissions.XXXXXX") || return 0
  {
    usb_ap_report_header
    echo "hostapd pid=$pid observation=$observation"
    # After exec, the kernel sets comm to hostapd. Avoid sampling the launcher.
    while [ "$count" -lt 5 ] && [ -r "$PROC/$pid/comm" ]; do
      read -r name < "$PROC/$pid/comm" 2>/dev/null || break
      [ "$name" != hostapd ] || break
      count=$((count + 1))
      "$BB_OWN" sleep 0.05
    done
    if [ "$name" = hostapd ]; then
      usb_ap_process_info "$pid"
    else
      echo "hostapd process exited or could not be sampled after exec."
    fi
    echo "Hostapd startup kernel messages:"
    usb_ap_kernel_log "$AP_HOSTAPD_START" 30
  } > "$snapshot"
  usb_ap_publish_attempt "$snapshot" "$W/usb-hostapd-permissions-$AP_PHASE.log"
}

usb_capture_running_hostapd() {
  local pid args
  AP_HOSTAPD_START=$(usb_ap_uptime)
  for pid in $("$BB_OWN" pidof hostapd 2>/dev/null); do
    [ -r "$PROC/$pid/cmdline" ] || continue
    args=$("$BB_OWN" tr '\000' ' ' 2>/dev/null < "$PROC/$pid/cmdline")
    case "$args" in
      *"hostapd $CONF "*)
        usb_capture_hostapd_permissions "$pid" already-running
        usb_capture_hostapd_logcat "$pid" 0 running
        return
        ;;
    esac
  done
}
