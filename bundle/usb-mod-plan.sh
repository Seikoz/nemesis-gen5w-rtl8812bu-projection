# Apply only this package's wireless-mod changes when upgrading the TCP policy.
plan_only_mod() {
  local line bad=0
  hmgapid engine plan > "$W/plan.txt" 2>&1 || return 1
  [ -s "$W/plan.txt" ] || return 1
  set -f
  while IFS= read -r line; do
    case "$line" in
      "hooks are off"*|"hooks "*"won't load"*|*" back to stock"*) bad=1 ;;
      "same     "*|"hook plan:"*|"note     "*|"WARNING"*|"") ;;
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
