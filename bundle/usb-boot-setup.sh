# Only skip the delayed repair worker when this boot's checks show no work for it.
usb_boot_setup_complete() {
  local plan="$W/plan.txt" status="$W/usb-boot-setup.log" path
  [ "$USB_AUDIO_PLAN_SAFE" = 1 ] && setup_done || return 1
  ! prog_reboot_this_boot && ! fix_running || return 1
  [ -f "$BK/automap.checked" ] && [ ! -f "$BK/automap.bad" ] && [ ! -s "$BK/map.bad" ] || return 1
  [ -s "$HMGDATA/state/local-map.json" ] && [ ! -e "$HMGDATA/state/journal.json" ] || return 1
  "$BB" grep -Eq '"ok"[[:space:]]*:[[:space:]]*true' "$HMGDATA/state/map-check.json" || return 1
  usb_audio_owned_files > "$status" 2>&1 || return 1
  # The rc.7 plan must explicitly match the live projection permissions and files.
  "$BB" grep -Eq '^(change|update|setting|WARNING|problem)[[:space:]:]' "$plan" && return 1
  for path in \
    /system/etc/permissions/com.hkmc.software.connectivity.carplay_wireless.xml \
    /system/etc/permissions/com.hkmc.software.connectivity.androidauto_wireless.xml \
    /system/lib/libcarplayidentity.so /system/lib/libcarplaylog.so /system/lib/libleafiaaac.so; do
    "$BB" grep -Fxq "same     $path [$MOD_ID]" "$plan" || return 1
  done
  # Status also detects missing managed files whose owners are absent from the plan.
  "$BB_OWN" timeout 8 hmgapid engine status >> "$status" 2>&1 || return 1
  [ ! -e "$HMGDATA/state/journal.json" ] || return 1
  log "USB boot: existing wireless setup checked; skipping delayed permission repair."
}
