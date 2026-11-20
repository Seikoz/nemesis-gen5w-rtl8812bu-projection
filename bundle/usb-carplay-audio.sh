# Keep only audio milestones and source categories. Native logs may name the phone.
usb_capture_carplay_audio() {
  local boot snapshot output previous file="$W/usb-carplay-audio.log"
  read -r boot < "$PROC/sys/kernel/random/boot_id" || return 0
  snapshot=$("$BB" mktemp "$W/.usb-cp-audio.XXXXXX") || return 0
  output=$("$BB" mktemp "$W/.usb-cp-audio.XXXXXX") || { "$BB" rm -f "$snapshot"; return 0; }
  {
    "$BB_OWN" timeout 3 logcat -d -t 4000 -v threadtime 'TccCarPlay:V' 'MediaFocusControl:I' 'HMG-API:I' '*:S' 2>/dev/null
    echo "logcat_exit=$?"
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
        }
      } else if (line ~ /[[:space:]]mediafocuscontrol[[:space:]]*:/) {
        source=(line ~ /btaudio/ ? "bluetooth-media" : (line ~ /[.]dipo|carplay/ ? "carplay" : "other"))
        if (line ~ /requestaudiofocus\(\) from/) event="focus_request source=" source
        else if (line ~ /abandonaudiofocus\(\) from/) event="focus_abandon source=" source
      } else if (line ~ /[[:space:]]hmg-api[[:space:]]*:/ && line ~ /usb_cp_audio bluetooth_handoff=(stock|preserved)[[:space:]]*$/) {
        event="bluetooth_handoff=" (line ~ /=stock[[:space:]]*$/ ? "stock" : "preserved")
      }
      if (event!="") print $1, $2, event
    }' > "$snapshot"
  previous=/dev/null
  [ ! -r "$file" ] || previous=$file
  {
    echo "boot=$boot"
    "$BB" awk -v b="boot=$boot" '
      FILENAME!=ARGV[ARGC-1] {
        if (FNR==1) {keep=($0==b); next}
        if (!keep || /^logcat_exit=/) next
      }
      /^logcat_exit=/ {status=$0; next}
      !seen[$0]++ {items[n++%160]=$0}
      END {
        if (status!="") print status
        for (i=(n>160?n-160:0); i<n; i++) print items[i%160]
      }' "$previous" "$snapshot"
  } > "$output" && "$BB" mv -f "$output" "$file"
  "$BB" rm -f "$snapshot" "$output"
}

usb_watch_carplay_audio() {
  local now
  if [ "$CP_COUNT" = 1 ]; then
    read -r now _ < "$UPTIME" || return 0
    now=${now%%.*}
    case "$now" in ""|*[!0-9]*) return 0 ;; esac
    [ "$now" -lt "${USB_AUDIO_CAPTURE_NEXT:-0}" ] && return 0
    USB_AUDIO_CAPTURE_NEXT=$((now + 12))
  elif [ -n "${USB_AUDIO_CAPTURE_NEXT:-}" ]; then
    USB_AUDIO_CAPTURE_NEXT=
  else
    return 0
  fi
  usb_capture_carplay_audio
}
