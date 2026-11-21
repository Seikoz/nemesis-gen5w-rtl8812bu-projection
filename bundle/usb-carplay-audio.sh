# Keep only audio milestones and source categories. Native logs may name the phone.
usb_capture_carplay_audio() {
  local boot snapshot output previous rc file="$W/usb-carplay-audio.log"
  read -r boot < "$PROC/sys/kernel/random/boot_id" || return 0
  snapshot=$("$BB" mktemp "$W/.usb-cp-audio.XXXXXX") || return 0
  output=$("$BB" mktemp "$W/.usb-cp-audio.XXXXXX") || { "$BB" rm -f "$snapshot"; return 0; }
  {
    rc=0
    "$BB_OWN" timeout 25 logcat -b main -d -v threadtime 'TccCarPlay:V' 'MediaFocusControl:I' 'HMG-API:I' '*:S' 2>/dev/null || rc=$?
    echo "logcat_exit=$rc"
  } | "$BB" awk '
    /^logcat_exit=[0-9]+$/ {print; next}
    $1 !~ /^[0-9][0-9]-[0-9][0-9]$/ || $2 !~ /^[0-9:.]+$/ {next}
    {
      line=tolower($0); event=""
      if (line ~ /[[:space:]]tcccarplay[[:space:]]*:/) {
        if (line ~ /audio/ && line ~ /setup.*(fail|error)|failed to (set up|start|open)/) event="audio_setup_error"
        else if (line ~ /setting up (aac|opus|pcm)|audio stream.*(started|prepared)/) {
          route=(line ~ /alt audio/ ? "alt" : (line ~ /main audio/ ? "main" : "other"))
          codec=(line ~ /aac-eld/ ? "aac-eld" : (line ~ /aac-lc/ ? "aac-lc" : (line ~ /opus/ ? "opus" : (line ~ /pcm/ ? "pcm" : "unknown"))))
          event="audio_stream_reported stream=" route " codec=" codec
        } else if (line ~ /setup stream type:[[:space:]]*(100|101|102|103)([^0-9]|$)/) {
          match(line, /10[0-3]([^0-9]|$)/); event="audio_setup_request type=" substr(line,RSTART,3)
        } else if (line ~ /setup stream type:[[:space:]]*130([^0-9]|$)/) event="iap2_setup_request type=130"
      } else if (line ~ /[[:space:]]mediafocuscontrol[[:space:]]*:/) {
        source=(line ~ /btaudio/ ? "bluetooth-media" : (line ~ /[.]dipo|carplay/ ? "carplay" : "other"))
        if (line ~ /requestaudiofocus\(\) from/) event="focus_request source=" source
        else if (line ~ /abandonaudiofocus\(\) from/) event="focus_abandon source=" source
      } else if (line ~ /[[:space:]]hmg-api[[:space:]]*:/) {
        if (line ~ /usb_cp_audio bluetooth_handoff=(stock|preserved)[[:space:]]*$/)
          event="bluetooth_handoff=" (line ~ /=stock[[:space:]]*$/ ? "stock" : "preserved")
        else if (match(line, /usb_cp_handover stage=first-native-send rc=-?[0-9]+ len=[0-9]+ peer_seen=(false|true)/)) {
          event=substr(line, RSTART, RLENGTH)
          sub(/^usb_cp_handover stage=/, "iap2_stage=", event)
        } else if (match(line, /usb_cp_handover stage=(waiting-for-peer|peer-wait-expired|first-peer-data|spp-down-preserved|waiting-after-rc19|resume-on-peer|native-send-accepted|component5-connected)([[:space:]]|$)/)) {
          event=substr(line, RSTART, RLENGTH)
          sub(/^usb_cp_handover stage=/, "iap2_stage=", event)
          sub(/[[:space:]]+$/, "", event)
        } else if (match(line, /carplay-channel iap2 send failed rc=-?[0-9]+ len=[0-9]+/)) {
          event=substr(line, RSTART, RLENGTH)
          sub(/^carplay-channel iap2 send failed/, "iap2_send_failed", event)
        } else if (line ~ /iap2 connect success comp=4([[:space:]]|$)/) event="iap2_stage=bluetooth-ready"
        else if (line ~ /iap2 connect success comp=5([[:space:]]|$)/) event="iap2_stage=component5-ready"
        else if (line ~ /action_iap2_connectfail.*limitmaxresend/) event="iap2_retry_limit"
        else if (line ~ /carplay log: on /) event="native_logging=enabled"
        else if (line ~ /carplay log: logcontrol failed|carplay log: can.t switch it on/) event="native_logging=error"
      }
      if (event!="") {print $1, $2, event; matched++}
      if (line ~ /[[:space:]]tcccarplay[[:space:]]*:/) native++
    }
    END {print "capture_rows=" (matched+0) " native_rows=" (native+0)}' > "$snapshot"
  previous=/dev/null
  [ ! -r "$file" ] || previous=$file
  if {
    echo "boot=$boot"
    "$BB" awk -v b="boot=$boot" '
      FILENAME!=ARGV[ARGC-1] {
        if (FNR==1) {keep=($0==b); next}
        if (!keep || /^(logcat_exit|capture_rows)=/) next
      }
      /^logcat_exit=/ {status=$0; next}
      /^capture_rows=/ {counts=$0; next}
      !seen[$0]++ {items[n++%160]=$0}
      END {
        if (status!="") print status
        if (counts!="") print counts
        for (i=(n>160?n-160:0); i<n; i++) print items[i%160]
      }' "$previous" "$snapshot"
  } > "$output" && "$BB" mv -f "$output" "$file"; then
    [ -z "${USB_TRIAL_DIR:-}" ] || usb_trial_save usb-carplay-audio.log
  fi
  "$BB" rm -f "$snapshot" "$output"
}

usb_watch_carplay_audio() {
  local now
  if [ -n "${USB_AUDIO_CAPTURE_PID:-}" ]; then
    kill -0 "$USB_AUDIO_CAPTURE_PID" 2>/dev/null && return 0
    wait "$USB_AUDIO_CAPTURE_PID" 2>/dev/null || :
    USB_AUDIO_CAPTURE_PID=
  fi
  read -r now _ < "$UPTIME" || return 0
  now=${now%%.*}
  case "$now" in ""|*[!0-9]*) return 0 ;; esac
  if [ "$CP_COUNT" = 1 ] || [ "${CP_STATE:-}" = bt_attach ] || [ "${CP_STATE:-}" = created ] ||
    { [ -n "${USB_TRIAL_DIR:-}" ] && usb_trial_audio_window "$now"; }; then
    [ "$now" -lt "${USB_AUDIO_CAPTURE_NEXT:-0}" ] && return 0
    USB_AUDIO_CAPTURE_NEXT=$((now + 30))
  elif [ -n "${USB_AUDIO_CAPTURE_NEXT:-}" ]; then
    USB_AUDIO_CAPTURE_NEXT=
  else
    return 0
  fi
  # Logcat latency must not block AP supervision or overwrite results from an active capture.
  usb_capture_carplay_audio &
  USB_AUDIO_CAPTURE_PID=$!
}
