# Changes must belong to our mod. rc.7 also prints unchanged global state.
plan_only_mod() {
  local line owner bad=0
  hmgapid engine plan > "$W/plan.txt" 2>&1 || return 1
  [ -s "$W/plan.txt" ] || return 1
  set -f
  while IFS= read -r line; do
    case "$line" in
      "hooks are off"*|"hooks "*"won't load"*|*" back to stock"*) bad=1 ;;
      "same     "*|"hook plan:"*|"note     "*|"WARNING"*|"") ;;
      "home Wi-Fi  off") ;;
      "network  no cellular ["*"]")
        set -- $line
        [ "$#" -eq 4 ] || { bad=1; continue; }
        owner=${4#\[}; owner=${owner%\]}
        case "$owner" in ''|*[!a-z0-9-]*) bad=1 ;; esac ;;
      "event    parked -> its apps and hooks hear it [$MOD_ID]"|\
      "event    unparked -> its apps and hooks hear it [$MOD_ID]"|\
      "event    shutdown -> its apps and hooks hear it [$MOD_ID]"|\
      "event    wake -> its apps and hooks hear it [$MOD_ID]") ;;
      "change   "*|"update   "*)
        set -- $line
        [ "$3" = "[$MOD_ID]" ] || bad=1 ;;
      "setting  "*"[$MOD_ID]"*|"network  "*"[$MOD_ID]"*) ;;
      "nothing changed"*problem*) bad=1 ;;
      "nothing changed"*) ;;
      *) bad=1 ;;
    esac
  done < "$W/plan.txt"
  set +f
  return "$bad"
}
