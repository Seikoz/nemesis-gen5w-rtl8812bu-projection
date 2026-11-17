#!/system/bin/sh
package_dir=/data/nemesis/apps/realtek.88x2bu
. "$package_dir/scripts/common.sh" || exit 1
module_is_loaded || exit 0
if ! read_boot_id; then
    echo "Cannot determine who loaded 88x2bu."
    exit 1
fi
owns_module || exit 0
if ! rmmod 88x2bu; then
    echo "88x2bu is in use. Disconnect the dongle and retry."
    exit 1
fi
