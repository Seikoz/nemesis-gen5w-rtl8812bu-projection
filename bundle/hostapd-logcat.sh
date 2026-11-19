# Save the AP process's recent Android log before logcat rotates.
usb_capture_hostapd_logcat() {
  local pid="$1" rc="$2" observation="${3:-failure}" snapshot
  snapshot=$("$BB" mktemp "$W/.usb-hostapd-logcat.XXXXXX") || return 1
  {
    usb_ap_report_header
    echo "hostapd $observation pid=$pid exit=$rc"
    {
      "$BB_OWN" timeout 3 logcat -d -t 1200 -v threadtime '*:V' 2>/dev/null
      echo "logcat_status=$?"
    } | "$BB" awk -v pid="$pid" -v config="$CONF" '
      function hide(line, secret, out, n) {
        out = ""
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
        credentials = (ssid != "" && length(key) >= 8)
      }
      /^logcat_status=[0-9]+$/ { status = substr($0, 15); next }
      /avc:.*denied/ && $0 ~ ("pid=" pid "([^0-9]|$)") && /hostapd|net_admin|rfkill/ {
        if (tolower($0) !~ /ssid|psk|password|passphrase|secret/) lines[count++ % 80] = substr($0, 1, 512)
        next
      }
      credentials && $1 ~ /^[0-9][0-9]-[0-9][0-9]$/ &&
          $2 ~ /^[0-9][0-9]:[0-9][0-9]:[0-9][0-9]\.[0-9]+$/ &&
          $3 ~ /^[0-9]+$/ && $3 == pid && $4 ~ /^[0-9]+$/ && $5 ~ /^[VDIWEF]$/ {
        line = hide(hide($0, key), ssid)
        lower = tolower(line)
        if (lower ~ /hexdump|ssid|psk|passphrase|password|secret|key([[:space:]=:]|$)/) next
        if (lower !~ /nl80211|err|fail|invalid|denied|not permitted|not allowed|not supported|could not|cannot|no such|freq|channel|regulatory|rfkill|interface|ap-disabled|ap-enabled|ap-sta-|authenticat|associat|deauth|hw mode|terminat|fatal/) next
        gsub(/[[:xdigit:]][[:xdigit:]]:[[:xdigit:]][[:xdigit:]]:[[:xdigit:]][[:xdigit:]]:[[:xdigit:]][[:xdigit:]]:[[:xdigit:]][[:xdigit:]]:[[:xdigit:]][[:xdigit:]]/, "[mac]", line)
        lines[count++ % 80] = substr(line, 1, 512)
      }
      END {
        if (status != "0") print "logcat capture incomplete (exit " (status == "" ? "unknown" : status) ")."
        if (!credentials) print "Log entries omitted: hotspot credentials unavailable for redaction."
        else if (!count) print "No matching hostapd diagnostics in recent logcat."
        for (i = (count > 80 ? count - 80 : 0); i < count; i++) print lines[i % 80]
      }
    '
    echo "Kernel messages since hostapd start:"
    usb_ap_kernel_log "$AP_HOSTAPD_START" 30
  } > "$snapshot" && "$BB" mv -f "$snapshot" "$W/usb-hostapd-logcat-$AP_PHASE.log" || {
    "$BB" rm -f "$snapshot"
    return 1
  }
}

usb_run_hostapd() {
  local pid rc=0
  AP_HOSTAPD_START=$(usb_ap_uptime)
  hostapd "$CONF" &
  pid=$!
  usb_capture_hostapd_permissions "$pid" startup
  wait "$pid" || rc=$?
  echo "hostapd exit=$rc"
  # Normal exit or intentional TERM during AP shutdown does not replace a failure.
  case "$rc" in
    0|143) ;;
    *) usb_capture_hostapd_logcat "$pid" "$rc" ;;
  esac
}
