# Read-only snapshots. They never add/flush rules, reset counters or start mDNS daemons.
usb_carplay_coreutils_report() {
  local library="$1" md5
  echo
  echo '== CarPlay native library fingerprint'
  if [ ! -f "$library" ]; then
    md5=missing
  elif [ ! -r "$library" ]; then
    md5=unreadable
  elif md5=$("$BB_OWN" timeout 5 "$BB_OWN" md5sum 2>/dev/null < "$library"); then
    md5=${md5%%[[:space:]]*}
    case "$md5" in *[!0-9a-f]*) md5= ;; esac
    [ "${#md5}" -eq 32 ] || md5=hash-failed
  else
    md5=hash-failed
  fi
  echo "libCarPlayCoreUtils.so.md5=$md5"
}

usb_firewall_snapshot() {
  local tool rc
  for tool in iptables ip6tables; do
    echo "=== Actual $tool filter rules: ordered rules, interfaces, peers and packet/byte counters ==="
    {
      "$BB_OWN" timeout 2 "$tool" -t filter -n -v -x -L --line-numbers 2>&1
      echo "firewall_exit=$?"
    } | "$BB" awk -v tool="$tool" '
      BEGIN {t=4;p=5;opt=6;iface_in=7;iface_out=8;src=9;dst=10}
      /^Chain / {chain=$2; keep=(chain=="INPUT" || chain=="OUTPUT" || chain=="HMGAPI_IN" || chain=="HMGAPI_OUT"); if(keep) found++}
      $1=="num" {
        opt=0
        for(i=1;i<=NF;i++) {
          if($i=="target") t=i; if($i=="prot") p=i; if($i=="opt") opt=i
          if($i=="in") iface_in=i; if($i=="out") iface_out=i
          if($i=="source") src=i; if($i=="destination") dst=i
        }
      }
      /^firewall_exit=/ {print; exit}
      chain=="INPUT" && $t=="HMGAPI_IN" {input=$1}
      chain=="OUTPUT" && $t=="HMGAPI_OUT" {output=$1}
      tool=="ip6tables" && $1 ~ /^[0-9]+$/ && $t=="ACCEPT" && $p=="udp" && /[[:space:]][sd]pt:6031([[:space:]]|$)/ {
        # Legacy ip6tables can print an opt column in the header and leave it blank in rows.
        shift_opt=(opt > 0 && $opt !~ /^[-!][-f]$/)
        if (chain=="HMGAPI_IN" && $(iface_in-shift_opt)=="rtwlan0" && $(src-shift_opt)=="fe80::/10") udp_in++
        if (chain=="HMGAPI_OUT" && $(iface_out-shift_opt)=="rtwlan0" && $(dst-shift_opt)=="fe80::/10") udp_out++
      }
      keep && rows++<320 {print}
      END {if(!found) print "Expected firewall chains unavailable; see exit status.";
           print "HMGAPI_input_jump_position=" (input==""?"missing":input) " HMGAPI_output_jump_position=" (output==""?"missing":output);
           print "IPv6_UDP6031_scoped_input_entries=" (udp_in+0) " output_entries=" (udp_out+0);
           if(rows>320) print "Rule output truncated after 320 lines."}'
  done
  echo "=== Applied HMG-API network plan (not proof of kernel traversal) ==="
  if [ -r "${HMGDATA:-/data/hmgapi}/state/net.rules" ]; then
    "$BB" awk '/rtwlan0|HMGAPI_IN|HMGAPI_OUT/ {if(n++<120) print}' "${HMGDATA:-/data/hmgapi}/state/net.rules"
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
    if [ -r "$PROC/net/dev" ]; then
      "$BB" awk -F '[: ]+' '/^[[:space:]]*rtwlan0:/ {
        sub(/^[[:space:]]+/, ""); print "rtwlan0 totals rx_bytes=" $2 " rx_packets=" $3 " rx_errors=" $4 " rx_dropped=" $5 " tx_bytes=" $10 " tx_packets=" $11 " tx_errors=" $12 " tx_dropped=" $13
      }' "$PROC/net/dev"
    fi
    for file in "$PROC/net/igmp" "$PROC/net/igmp6"; do
      [ ! -r "$file" ] || "$BB" awk '/rtwlan0/ {print}' "$file"
    done
    echo '=== mDNS service probe (unicast replies, no instance/host/TXT contents) ==='
    usb_prepare_native_tool ap-link-diagnostics &&
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
