# Retire only an older stand-alone carrier that this bundle installed.
USB_CARRIER_ID=cn7npe-usb-carplay-carrier-test
USB_CARRIER_CURRENT_SHA=9305b000223812fe289428eba59f21c306feee2d97385360e42fea3500d477d2
USB_CARRIER_LEGACY_SHA=88064a9295d8d6ffebc6f43d13456980a8c314d9756f3950246279bc99afe7b5

usb_carrier_cleanup() {
  local dir="$HMGDATA/mods/$USB_CARRIER_ID" owner="$BK/usb-carrier.owner"
  local manifest hash state boot scope digest
  manifest="$dir/META-HMGAPI/manifest.json"
  [ -f "$owner" ] && [ ! -L "$owner" ] && [ -d "$dir" ] && [ ! -L "$dir" ] &&
    [ -f "$manifest" ] && [ ! -L "$manifest" ] || return 0
  read -r hash state boot scope < "$owner" || return 0
  [ "${scope:-managed}" = managed ] || return 0
  case "$hash" in "$USB_CARRIER_CURRENT_SHA"|"$USB_CARRIER_LEGACY_SHA") ;; *) return 0 ;; esac
  case "$state" in installing|installed|applied) ;; *) return 0 ;; esac
  digest=$("$BB_OWN" sha256sum 2>/dev/null < "$manifest") || return 0
  case "${digest%% *}" in "$USB_CARRIER_CURRENT_SHA"|"$USB_CARRIER_LEGACY_SHA") ;; *) return 0 ;; esac
  [ ! -e "$HMGDATA/mods/$MOD_ID/.disabled" ] && usb_audio_owned_files || return 0
  if "$BB_OWN" timeout 40 hmgapid engine remove "$USB_CARRIER_ID" --from-nemesis && [ ! -d "$dir" ]; then
    "$BB" rm -f "$owner"
    echo 'Removed the old bundled stand-alone CN7NPE audio carrier'
  else
    echo 'Could not remove the old bundled audio carrier; will check again on the next start'
  fi
}
