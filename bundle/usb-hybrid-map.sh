# HMG-API rc.7 has no shipped map for CN7HEVPE. Create one from this unit.
usb_hybrid_map_ready() {
  local map="$HMGDATA/state/local-map.json" points="$KP_HMG/required-hooks.txt" point
  if [ ! -s "$map" ]; then
    "$BB_OWN" timeout 180 hmgapid engine map-car --write || return 1
  fi
  [ -s "$map" ] && [ -s "$points" ] || return 1
  "$BB" grep -Fq '"whole": true' "$map" || return 1
  while IFS= read -r point; do
    if ! "$BB" grep -Fq "\"$point\": {" "$map"; then
      echo "Required CN7HEVPE hook missing: $point"
      return 1
    fi
  done < "$points"
  "$BB_OWN" timeout 45 hmgapid engine verify-map > "$W/.cn7hevpe-map-check" 2>&1
  local rc=$?
  cat "$W/.cn7hevpe-map-check"
  [ "$rc" -eq 0 ] && "$BB" grep -q '^map local:' "$W/.cn7hevpe-map-check"
}
