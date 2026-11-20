# Reconcile the same installed version too: v0.1.18 could install the hooks while
# its rc.7 plan was refused. Never start the AP with newly applied, stale libraries.
usb_audio_pending() {
  local line
  USB_AUDIO_PENDING=0
  while IFS= read -r line; do
    case "$line" in
      "change   "*|"update   "*)
        set -- $line
        [ "$3" = "[$MOD_ID]" ] || continue
        case "$2" in
          /system/lib/libleafiaaac.so|/system/lib/libcarplayidentity.so|/system/lib/libcarplaylog.so)
            USB_AUDIO_PENDING=1 ;;
        esac ;;
    esac
  done < "$W/plan.txt"
}

usb_audio_owned_files() {
  local actual expected name checked=0
  if ! { [ -f "$BK/mod.ours" ] && [ ! -f "$BK/mod.pin" ] &&
    [ "$(mod_ver)" = "$MOD_VER" ]; }; then
    echo "Ownership, version or pin check failed."
    return 1
  fi
  [ -s "$KP_HMG/usb-mod-files.md5" ] || return 1
  while read -r expected name; do
    case "$name" in ''|/*|*..*) return 1 ;; esac
    if [ ! -f "$HMGDATA/mods/$MOD_ID/$name" ] || [ -L "$HMGDATA/mods/$MOD_ID/$name" ]; then
      echo "Missing or linked bundled file: $name"; return 1
    fi
    actual=$("$BB" md5sum < "$HMGDATA/mods/$MOD_ID/$name") || return 1
    [ "${actual%% *}" = "$expected" ] || { echo "Bundled file differs: $name"; return 1; }
    checked=$((checked + 1))
  done < "$KP_HMG/usb-mod-files.md5"
  echo "Verified $checked bundled mod files."
}

usb_audio_marker() {
  echo "$BID $MOD_VER $1" > "$BK/.usb-audio-apply.next" &&
    "$BB" mv -f "$BK/.usb-audio-apply.next" "$BK/usb-audio-apply"
}

# 0: no repair; 1: successfully applied this boot, reboot required; 2: manual action.
usb_audio_reconcile() {
  local marked_boot= marked_version= marked_state= safe=0
  USB_AUDIO_STATUS=none
  usb_target || return 0
  echo "boot=$BID expected_mod=$MOD_VER audio setup before AP startup"
  [ ! -f "$HMGDATA/mods/$MOD_ID/.disabled" ] || return 0
  [ -f "$HMGDATA/mods/$MOD_ID/mod.json" ] && [ "$(mod_ver)" = "$MOD_VER" ] || return 0
  case "$BID" in ''|*[!0-9a-f-]*) USB_AUDIO_STATUS=invalid-boot; return 2 ;; esac
  if [ -r "$BK/usb-audio-apply" ]; then
    read -r marked_boot marked_version marked_state < "$BK/usb-audio-apply"
    if [ "$marked_boot" = "$BID" ] && [ "$marked_version" = "$MOD_VER" ]; then
      USB_AUDIO_STATUS=$marked_state
      [ "$marked_state" != applied ] || return 1
      return 2
    fi
  fi
  plan_only_mod && safe=1
  [ -s "$W/plan.txt" ] || { USB_AUDIO_STATUS=plan-unavailable; return 2; }
  usb_audio_pending
  [ "$USB_AUDIO_PENDING" = 1 ] || return 0
  if [ "$safe" != 1 ]; then
    USB_AUDIO_STATUS=foreign-or-unknown-plan
    log "USB audio apply blocked: plan includes unrelated changes or problems."
    return 2
  fi
  if ! usb_audio_owned_files > "$W/usb-mod-files-check.log" 2>&1; then
    USB_AUDIO_STATUS=installed-files-differ
    log "USB audio apply blocked: installed mod is pinned, foreign or differs from the bundled files."
    return 2
  fi
  # This gate runs before AP startup, not while a CarPlay session is active.
  if [ "$(getprop "$AAPROP" 2>/dev/null)" = 1 ]; then
    USB_AUDIO_STATUS=ap-active
    return 2
  fi
  usb_audio_marker applying || { USB_AUDIO_STATUS=marker-failed; return 2; }
  if ! usb_network allow > "$W/usb-network.log" 2>&1; then
    usb_audio_marker failed
    USB_AUDIO_STATUS=network-setup-failed
    return 2
  fi
  # Re-read the plan after the settings update; do not use a stale saved report.
  if ! plan_only_mod; then
    usb_audio_marker blocked
    USB_AUDIO_STATUS=plan-changed
    return 2
  fi
  if hmgapid engine apply > "$W/mod-apply.txt" 2>&1; then
    usb_audio_marker applied || { USB_AUDIO_STATUS=marker-failed; return 2; }
    USB_AUDIO_STATUS=applied
    log "USB audio support files applied automatically; reboot required before AP startup."
    return 1
  fi
  usb_audio_marker failed
  USB_AUDIO_STATUS=apply-failed
  log "USB audio support apply failed; see mod-apply.txt."
  return 2
}
