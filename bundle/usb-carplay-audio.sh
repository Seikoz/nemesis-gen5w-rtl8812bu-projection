# Keep only known playback, volume and display events. Native logs may name the phone.
usb_capture_carplay_mixer() {
  local stamp rc=0
  stamp=$("$BB" date '+%m-%d %H:%M:%S') || return 0
  {
    "$BB_OWN" timeout 4 dumpsys media.audio_flinger 2>/dev/null || rc=$?
    echo "mixer_dump_exit=$rc"
  } | "$BB" awk -v stamp="$stamp" '
    function reset_output() {
      handle=standby=rate=hal=normal=partial=empty="unknown"
    }
    function output() {
      if (!playback || rate=="unknown" || printed>=8) return
      print stamp, "mixer_output_handle=" handle, "standby=" standby, "sample_rate_hz=" rate,
        "hal_frames=" hal, "normal_frames=" normal, "underrun_partial=" partial, "underrun_empty=" empty
      printed++
    }
    /^mixer_dump_exit=[0-9]+$/ {status=$0; next}
    {
      line=tolower($0)
      sub(/^[[:space:]]*/, "", line)
      if (line ~ /^output thread [^[:space:]]+ (internals|type [0-9]+)/) {
        output()
        reset_output()
        playback=1
      } else if (line ~ /^(input|record) thread /) {
        output()
        playback=0
      } else if (playback && line ~ /^io handle: [0-9]+[[:space:]]*$/) {
        handle=$3+0
      } else if (playback && line ~ /^standby: [01][[:space:]]*$/) {
        standby=$2+0
      } else if (playback && line ~ /^sample rate: [0-9]+[[:space:]]*$/) {
        rate=$3+0
      } else if (playback && line ~ /^hal frame count: [0-9]+[[:space:]]*$/) {
        hal=$4+0
      } else if (playback && line ~ /^normal frame count: [0-9]+[[:space:]]*$/) {
        normal=$4+0
      } else if (playback && line ~ /^normal mixer raw underrun counters: partial=[0-9]+ empty=[0-9]+[[:space:]]*$/) {
        split($6, p, "="); split($7, e, "=")
        partial=p[2]+0; empty=e[2]+0
      }
    }
    END {
      output()
      if (status!="") print stamp, status, "outputs_seen=" (printed+0)
    }'
}

usb_capture_carplay_audio() {
  local boot snapshot output previous rc dipo_pid= file="$W/usb-carplay-audio.log"
  read -r boot < "$PROC/sys/kernel/random/boot_id" || return 0
  snapshot=$("$BB" mktemp "$W/.usb-cp-audio.XXXXXX") || return 0
  output=$("$BB" mktemp "$W/.usb-cp-audio.XXXXXX") || { "$BB" rm -f "$snapshot"; return 0; }
  if [ "${CP_EVENT_BOOT:-}" = "$boot" ]; then
    IFS=, read -r _ dipo_pid _ <<EOF
${CP_EVENT_RECORD:-}
EOF
  fi
  {
    rc=0
    "$BB_OWN" timeout 25 logcat -b main -b system -d -v threadtime \
      'TccCarPlay:V' 'CarPlay_:D' 'LeafiaAAC:I' 'AudioTrack:W' 'MediaFocusControl:D' \
      'MicomAudioService:D' 'ACodec:W' 'OMXCodec:W' 'HMG-API:I' '*:S' 2>/dev/null || rc=$?
    echo "logcat_exit=$rc"
  } | "$BB" awk -v dipo_pid="$dipo_pid" '
    function diagnostic_field(line, key, allowed,    value) {
      if (!match(line, key "[[:space:]]*[a-z0-9_]+")) return "unseen"
      value=substr(line, RSTART, RLENGTH)
      sub(/^[^:.]+[:.][[:space:]]*/, "", value)
      return value ~ allowed ? value : "other"
    }
    function number_field(line, key,    value) {
      if (!match(line, "(^|[^a-z0-9_])" key "[[:space:]]*:[[:space:]]*-?[0-9]+([,[:space:]]|$)"))
        return "unseen"
      value=substr(line, RSTART, RLENGTH)
      sub(/^[^:]+:[[:space:]]*/, "", value)
      sub(/[,[:space:]]+$/, "", value)
      return length(value)<=8 ? value : "unseen"
    }
    function audio_route(line) {
      if (line ~ /mainhigh|main buffered audio|buffered main audio/) return "main_buffered"
      if (line ~ /alt(ernate)? audio/) return "alt"
      if (line ~ /main audio/) return "main"
      return "other"
    }
    /^logcat_exit=[0-9]+$/ {print; next}
    $1 !~ /^[0-9][0-9]-[0-9][0-9]$/ || $2 !~ /^[0-9][0-9]:[0-9][0-9]:[0-9][0-9]([.][0-9]+)?$/ {next}
    {
      line=tolower($0); event=""
      if (line ~ /[[:space:]]tcccarplay[[:space:]]*:/) {
        native++
        if (line ~ /tcccarplay_iapsendmessage\(\)[[:space:]]*:/) native_iap_send++
        if (line ~ /audio/ && line ~ /setup.*(fail|error)|failed to (set up|start|open)/) event="audio_setup_error"
        else if (line ~ /teardown stream type:[[:space:]]*10[0-3]([^0-9]|$)/) {
          event="audio_teardown_request type=" diagnostic_field(line, "teardown stream type:", "^10[0-3]$")
        } else if (line ~ /audio/ && line ~ /(stopped|torn down|teardown|tear down)/ && audio_route(line)!="other") {
          event="audio_stream_stopped stream=" audio_route(line)
        } else if (line ~ /setting up (aac|opus|pcm)|audio stream.*(started|prepared)/) {
          route=audio_route(line)
          codec=(line ~ /aac-eld/ ? "aac-eld" : (line ~ /aac-lc/ ? "aac-lc" : (line ~ /opus/ ? "opus" : (line ~ /pcm/ ? "pcm" : "unknown"))))
          event="audio_stream_reported stream=" route " codec=" codec
        } else if (line ~ /setup stream type:[[:space:]]*(100|101|102|103)([^0-9]|$)/) {
          event="audio_setup_request type=" diagnostic_field(line, "setup stream type:", "^10[0-3]$")
        } else if (line ~ /setup stream type:[[:space:]]*130([^0-9]|$)/) event="iap2_setup_request type=130"
        else if (line ~ /(^|[^a-z])flushbuffered([^a-z]|$)|flush(ing|ed)? buffered audio/) event="buffered_audio_flush_reported"
        else if (line ~ /audio.*(underrun|underflow)|(underrun|underflow).*audio/) event="native_audio_underrun_reported"
        else if (line ~ /audio.*(resum(ed|ing)|rebuffer(ing)?)/) event="native_audio_resume_or_refill_reported"
        else if (line ~ /(video|screen|decoder|render)/ && line ~ /(stall|timeout|timed out|fail|error)/)
          event="native_video_error"
        else if (match(line, /(video|screen)( stream)?[^[:alnum:]]+(stopped|paused|resumed|started)([^a-z]|$)/)) {
          state=substr(line, RSTART, RLENGTH)
          sub(/^(video|screen)( stream)?[^[:alnum:]]+/, "", state)
          sub(/[^a-z]+$/, "", state)
          event="native_video_state state=" state
        }
      } else if (line ~ /[[:space:]]leafiaaac[[:space:]]*:/) {
        if (line ~ /aac-lc decoder up:/) event="aac_music_decoder_started"
        else if (line ~ /first packet decoded: [0-9]+ frames, [0-9]+ ch, [0-9]+ hz/) event="aac_music_first_packet_decoded"
      } else if (dipo_pid ~ /^[1-9][0-9]*$/ && $3==dipo_pid && line ~ /[[:space:]]audiotrack[[:space:]]*:/) {
        if (line ~ /underrun|underflow|disabled due to previous underrun/) event="dipo_audio_track_underrun_reported"
      } else if (line ~ /[[:space:]]carplay_[[:space:]]*:.*\[[[:space:]]*diposervice[[:space:]]*\]/) {
        if (line ~ /updatecarplaymusicssosd/) event="carplay_music_metadata_updated"
        else if (line ~ /changeaudiofocus\(\).*resourceowner[.].*audioty(pe|e):/) {
          owner=diagnostic_field(line, "resourceowner[.]", "^(controller|accessory|none|unknown)$")
          type=diagnostic_field(line, "audioty(pe|e):", "^(media|telephony|speech|default|unknown)$")
          music=diagnostic_field(line, "mismusicaudiofocusgained:", "^(true|false)$")
          event="dipo_audio_focus owner=" owner " type=" type " music_focus=" music
        } else if (line ~ /onchangealtaudiomode\(\).*altaudio:/) {
          mode=diagnostic_field(line, "altaudio:", "^(same|enable|disable)$")
          event="dipo_alt_audio_mode mode=" mode
        } else if (line ~ /onchangemainaudiomode\(\).*mainaudio:/) {
          mode=diagnostic_field(line, "mainaudio:", "^(same|enable|disable)$")
          if (line ~ /mismusicaudiofocusgained:/) {
            phone=diagnostic_field(line, "misphoneaudiofocusgained:", "^(true|false)$")
            siri=diagnostic_field(line, "missiriaudiofocusgained:", "^(true|false)$")
            music=diagnostic_field(line, "mismusicaudiofocusgained:", "^(true|false)$")
            event="dipo_audio_mode mode=" mode " phone_focus=" phone " siri_focus=" siri " music_focus=" music
          }
        }
      } else if (line ~ /[[:space:]]mediafocuscontrol[[:space:]]*:/) {
        source=(line ~ /btaudio/ ? "bluetooth-media" : (line ~ /[.]dipo|carplay/ ? "carplay" : "other"))
        if (line ~ /requestaudiofocus\(\) from/) event="focus_request source=" source
        else if (line ~ /abandonaudiofocus\(\) from/) event="focus_abandon source=" source
        else if (line ~ /dispatchaudiofocuschange|audio focus (gain|loss)/)
          event="focus_dispatch source=" source " change=" number_field(line, "focuschange")
      } else if (line ~ /[[:space:]]micomaudioservice[[:space:]]*:/) {
        if (line ~ /setvolumegroupinfomember/) {
          group=number_field(line, "volumegroup")
          member=number_field(line, "member")
          if (group!="unseen" && member!="unseen")
            event="vehicle_volume_group group=" group " member=" member " value1=" number_field(line, "value1") " value2=" number_field(line, "value2")
        } else if (line ~ /setvolumeslot/) {
          slot=number_field(line, "slot")
          volume=number_field(line, "volume")
          if (slot!="unseen" && volume!="unseen")
            event="vehicle_volume_slot slot=" slot " level=" volume
        }
      } else if (dipo_pid ~ /^[1-9][0-9]*$/ && $3==dipo_pid &&
        line ~ /[[:space:]](acodec|omxcodec)[[:space:]]*:/ && line ~ /error|failed|timeout|timed out/) {
        event="dipo_codec_error"
      } else if (line ~ /[[:space:]]hmg-api[[:space:]]*:/) {
        if (line ~ /carplay: route guidance start-only result=(true|false)[[:space:]]*$/)
          event="hud_guidance_start=" (line ~ /=true[[:space:]]*$/ ? "true" : "false")
        else if (line ~ /carplay: first hud turn submitted[[:space:]]*$/) event="hud_first_turn_submitted"
        else if (line ~ /usb_cp_audio bluetooth_handoff=(stock|preserved)[[:space:]]*$/)
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
      if (event ~ /(underrun_reported|video_error|codec_error)$/) {
        second=$1 " " substr($2, 1, 8)
        if (last_repeated[event]==second) next
        last_repeated[event]=second
      }
      if (event!="") {print $1, $2, event; matched++}
    }
    END {print "capture_rows=" (matched+0) " native_rows=" (native+0) " native_iap_send_rows=" (native_iap_send+0)}' > "$snapshot"
  [ "${1:-0}" != 1 ] || usb_capture_carplay_mixer >> "$snapshot"
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
      !seen[$0]++ {items[n++%1200]=$0}
      END {
        if (status!="") print status
        if (counts!="") print counts
        for (i=(n>1200?n-1200:0); i<n; i++) print items[i%1200]
      }' "$previous" "$snapshot"
  } > "$output" && "$BB" mv -f "$output" "$file"; then
    [ -z "${USB_TRIAL_DIR:-}" ] || usb_trial_save usb-carplay-audio.log
  fi
  "$BB" rm -f "$snapshot" "$output"
}

usb_watch_carplay_audio() {
  local now mixer=0
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
  if [ "$CP_COUNT" = 1 ] && [ "${USB_AUDIO_MIXER_SAMPLES:-0}" -lt 2 ]; then
    USB_AUDIO_MIXER_SAMPLES=$((${USB_AUDIO_MIXER_SAMPLES:-0} + 1))
    mixer=1
  fi
  usb_capture_carplay_audio "$mixer" &
  USB_AUDIO_CAPTURE_PID=$!
}
