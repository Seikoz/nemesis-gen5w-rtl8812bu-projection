# Read-only snapshots. They never add/flush rules, reset counters or start mDNS daemons.
usb_firewall_snapshot() {
  local tool rc
  for tool in iptables ip6tables; do
    echo "=== Actual $tool filter rules: ordered rules, interfaces, peers and packet/byte counters ==="
    {
      "$BB_OWN" timeout 2 "$tool" -t filter -n -v -x -L --line-numbers 2>&1
      echo "firewall_exit=$?"
    } | "$BB" awk '
      /^Chain / {keep=($2=="INPUT" || $2=="OUTPUT" || $2=="HMGAPI_IN" || $2=="HMGAPI_OUT"); if(keep) found++}
      /^firewall_exit=/ {print; exit}
      keep && rows++<320 {print}
      END {if(!found) print "Expected firewall chains unavailable; see exit status.";
           if(rows>320) print "Rule output truncated after 320 lines."}'
  done
  echo "=== Applied HMG-API network plan (not proof of kernel traversal) ==="
  if [ -r /data/hmgapi/state/net.rules ]; then
    "$BB" awk '/rtwlan0|HMGAPI_IN|HMGAPI_OUT/ {if(n++<120) print}' /data/hmgapi/state/net.rules
  else echo "HMG-API state/net.rules unavailable"; fi
}

usb_connection_snapshot() {
  local reason="$1" snapshot boot=
  snapshot=$("$BB" mktemp "$W/.usb-link.XXXXXX") || return 0
  read -r boot < "$PROC/sys/kernel/random/boot_id" || boot=unknown
  {
    echo "boot=$boot reason=$reason uptime=$(usb_ap_uptime)"
    echo "AP_generation=$(getprop sys.kp.cp_gen 2>/dev/null)"
    usb_cp_read
    echo "CarPlay_session=$CP_STATE connected=$CP_COUNT source=$CP_SOURCE"
    echo "WiFi_clients=${STA_COUNT:-unknown} source=${STA_SOURCE:-unavailable}"
    echo '=== Interface addresses and multicast membership ==='
    "$BB_OWN" timeout 2 ip addr show dev "$WIF" 2>&1
    for file in "$PROC/net/igmp" "$PROC/net/igmp6"; do
      [ ! -r "$file" ] || "$BB" awk '/rtwlan0/ {print}' "$file"
    done
    echo '=== mDNS service probe (unicast replies, no instance/host/TXT contents) ==='
    "$BB_OWN" timeout 3 "$APP/bin/ap-link-diagnostics" 2>&1
    echo "mdns_probe_exit=$?"
    echo '=== TCP and mDNS socket states: hex endpoints, no application payload ==='
    for file in tcp tcp6 udp udp6; do
      [ -r "$PROC/net/$file" ] || continue
      echo "socket_table=$file"
      "$BB" awk 'NR==1 || (FILENAME~/tcp/ && ($4=="01" || $4=="02" || $4=="03" || $4=="0A")) ||
        (FILENAME~/udp/ && ($2~/:14E9$/ || $3~/:14E9$/)) {if(n++<70) print $1,$2,$3,$4}' "$PROC/net/$file"
    done
    usb_firewall_snapshot
  } > "$snapshot"
  # First and latest snapshots survive unplugging the dongle to insert a report USB.
  if [ -r "$W/usb-connection-first.log" ]; then
    read -r reason _ < "$W/usb-connection-first.log"
  else reason=; fi
  if [ "$reason" != "boot=$boot" ]; then
    "$BB" cp "$snapshot" "$W/usb-connection-first.log"
  fi
  "$BB" mv -f "$snapshot" "$W/usb-connection-latest.log"
}

usb_connection_tick() {
  local key generation
  generation=$(getprop sys.kp.cp_gen 2>/dev/null)
  usb_ap_live || return 0
  key="$generation:${STA_COUNT:-unknown}:$CP_STATE"
  if [ "${USB_LINK_KEY:-}" != "$key" ]; then
    USB_LINK_KEY=$key
    USB_LINK_RETRIES=0
    usb_connection_snapshot transition
  elif [ "$CP_COUNT" = 0 ] && [ "${STA_COUNT:-0}" != 0 ] && [ "${USB_LINK_RETRIES:-0}" -lt 2 ]; then
    USB_LINK_RETRIES=$((${USB_LINK_RETRIES:-0}+1))
    usb_connection_snapshot "waiting-$USB_LINK_RETRIES"
  fi
}
