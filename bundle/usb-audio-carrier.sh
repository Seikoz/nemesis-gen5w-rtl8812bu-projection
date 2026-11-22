# Included in Korea Projection. The signed carrier has no filesystem patch recipe.
USB_CARRIER_ID=cn7npe-usb-carplay-carrier-test
USB_CARRIER_AUTHOR=e0bc5813-b75d-81c3-be64-31b9b002baba
USB_CARRIER_STOCK_MD5=cf3cc23dad25b181a9fc12d606468715
USB_CARRIER_MANIFEST_SHA=@CARRIER_MANIFEST_SHA@
USB_CARRIER_LEGACY_SHA=88064a9295d8d6ffebc6f43d13456980a8c314d9756f3950246279bc99afe7b5
USB_CARRIER_ZIP_SHA=@CARRIER_ZIP_SHA@

usb_carrier_hash_is() {
  local sum
  [ -f "$1" ] && [ ! -L "$1" ] || return 1
  sum=$("$BB_OWN" sha256sum 2>/dev/null < "$1") || return 1
  [ "${sum%% *}" = "$2" ]
}

usb_carrier_mark() {
  echo "$USB_CARRIER_MANIFEST_SHA $1 $BID $2" > "$BK/usb-carrier.next" &&
    "$BB" mv -f "$BK/usb-carrier.next" "$BK/usb-carrier.owner"
}

usb_carrier_plan_safe() {
  local plan="$W/usb-carrier-plan.txt"
  "$BB_OWN" timeout 15 hmgapid engine plan > "$plan" 2>&1 && [ -s "$plan" ] || return 1
  "$BB" awk -v wireless="[$MOD_ID]" '
    /^same     |^hook plan:|^note     |^$|^home Wi-Fi  off$/ {next}
    /^event    |^network  firewall / {if ($NF==wireless) next}
    /^network  no cellular \[[a-z0-9-]+\]$/ {next}
    /^nothing changed/ && !/problem/ {next}
    {bad=1} END {exit bad+0}' "$plan"
}

# Called after the existing wireless setup and before starting the USB hotspot.
# Return 1 only when an applied mod needs this boot to end before use.
usb_carrier_setup() {
  local dir="$HMGDATA/mods/$USB_CARRIER_ID" payload="$APP/hmgapi/$USB_CARRIER_ID.zip"
  local hash= state= previous_boot= scope= installed= stock
  case "$(getprop ro.build.product 2>/dev/null)" in
    CN7NPE.KOR.0000.V039.001.260902|CN7NPE.KOR.S5W_M.V039.001.260902) ;;
    *) return 0 ;;
  esac
  [ "$(getprop ro.board.platform 2>/dev/null)" = tcc803x ] &&
    [ "$(mod_ver)" = "$MOD_VER" ] && [ "$MOD_VER" = 2.4.21 ] || return 0
  case "$BID" in ''|*[!0-9a-f-]*) return 0 ;; esac
  if [ -r "$BK/usb-carrier.owner" ]; then
    read -r hash state previous_boot scope < "$BK/usb-carrier.owner"
    case "$hash" in
      "$USB_CARRIER_MANIFEST_SHA"|"$USB_CARRIER_LEGACY_SHA") ;;
      *) echo 'Skipped: ownership record differs'; return 0 ;;
    esac
  fi
  scope=${scope:-managed}   # v0.1.34 created three-field records for bundled installs.
  case "$scope" in managed|external) ;; *) return 0 ;; esac
  case "$state" in
    installing|installed)
      if [ "$hash" = "$USB_CARRIER_MANIFEST_SHA" ] && [ "$previous_boot" = "$BID" ]; then
        echo 'Will recheck the pending carrier on the next boot'
        return 0
      fi ;;
  esac
  if [ -e "$dir" ] || [ -L "$dir" ]; then
    [ ! -L "$dir" ] || { echo 'Skipped: installed carrier is linked'; return 0; }
    if usb_carrier_hash_is "$dir/META-HMGAPI/manifest.json" "$USB_CARRIER_MANIFEST_SHA"; then
      installed=current
      [ -n "$state" ] || { echo 'Kept manually installed carrier'; return 0; }
    elif usb_carrier_hash_is "$dir/META-HMGAPI/manifest.json" "$USB_CARRIER_LEGACY_SHA"; then
      installed=legacy
      [ -n "$state" ] || scope=external
    else
      echo 'Skipped: installed carrier differs'
      return 0
    fi
    [ ! -e "$dir/.disabled" ] || { echo 'Kept carrier disabled'; return 0; }
    if [ "$installed" = current ] && [ "$state" = applied ] && [ "$hash" = "$USB_CARRIER_MANIFEST_SHA" ]; then
      echo 'Carrier already applied'
      [ "$previous_boot" != "$BID" ]
      return $?
    fi
  elif [ "$state" = installed ] || [ "$state" = applied ] || [ "$scope" = external ]; then
    echo 'Kept carrier removed'
    return 0
  fi
  stock=$(usb_carplay_coreutils_md5 /system/lib/libCarPlayCoreUtils.so)
  [ "$stock" = "$USB_CARRIER_STOCK_MD5" ] || { echo "Skipped: CoreUtils MD5=$stock"; return 0; }
  [ ! -e "${SYS_NET:-/sys/class/net}/wlan0" ] && ! usb_ap_live || return 0
  usb_carrier_plan_safe || { echo 'Deferred: HMG-API plan has other changes or problems'; return 0; }
  if [ "$installed" != current ]; then
    usb_carrier_hash_is "$payload" "$USB_CARRIER_ZIP_SHA" ||
      { echo 'Skipped: carrier ZIP hash differs'; return 0; }
    usb_carrier_mark installing "$scope" || return 0
    "$BB_OWN" timeout 40 hmgapid engine install "$payload" --uuid "$USB_CARRIER_AUTHOR" --from-nemesis ||
      { echo 'Carrier install failed; will recheck on next startup'; return 0; }
    usb_carrier_hash_is "$dir/META-HMGAPI/manifest.json" "$USB_CARRIER_MANIFEST_SHA" ||
      { echo 'Carrier install did not produce expected manifest'; return 0; }
  fi
  usb_carrier_mark installed "$scope" || return 0
  usb_carrier_plan_safe || { echo 'Deferred: HMG-API plan changed after installation'; return 0; }
  "$BB_OWN" timeout 45 hmgapid engine apply ||
    { echo 'Carrier apply failed; will recheck on next startup'; return 0; }
  usb_carrier_mark applied "$scope" || echo 'Could not save carrier apply status'
  echo 'Carrier applied; restart required'
  return 1
}

usb_carrier_remove() {
  local dir="$HMGDATA/mods/$USB_CARRIER_ID" hash state boot scope
  [ -f "$BK/usb-carrier.owner" ] && [ -d "$dir" ] || return 0
  read -r hash state boot scope < "$BK/usb-carrier.owner"
  [ "${scope:-managed}" = managed ] && [ ! -L "$dir" ] || return 0
  case "$hash" in "$USB_CARRIER_MANIFEST_SHA"|"$USB_CARRIER_LEGACY_SHA") ;; *) return 0 ;; esac
  usb_carrier_hash_is "$dir/META-HMGAPI/manifest.json" "$USB_CARRIER_MANIFEST_SHA" ||
    usb_carrier_hash_is "$dir/META-HMGAPI/manifest.json" "$USB_CARRIER_LEGACY_SHA" || return 0
  "$BB_OWN" timeout 40 hmgapid engine remove "$USB_CARRIER_ID" --from-nemesis && [ ! -d "$dir" ]
}
