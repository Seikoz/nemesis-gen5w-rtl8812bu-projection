#!/system/bin/sh
package_dir=$PWD
. "$package_dir/scripts/common.sh" || exit 1
select_module && check_conflict
