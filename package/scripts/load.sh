#!/system/bin/sh
package_dir=/data/nemesis/apps/realtek.88x2bu
. "$package_dir/scripts/common.sh" || exit 1

select_module && check_conflict || exit 1
check_korea_projection
identify_dongle
if ! read_boot_id; then
    echo "Cannot read the kernel boot ID."
    exit 1
fi
if module_is_loaded; then
    if ! owns_module; then
        echo "88x2bu is already loaded by another package or tool."
        exit 1
    fi
    report_interface
    exit $?
fi

if ! insmod "$package_dir/modules/$module_file" 'ifname=rtwlan%d' 'if2name=rtwlan%d'; then
    message="88x2bu failed to load on $platform."
    save_launch_log "$message" failure
    echo "$message"
    exit 1
fi
if ! echo "$boot_id" > "$package_dir/.loaded-boot"; then
    rmmod 88x2bu
    echo "Cannot save this package's module state."
    exit 1
fi
report_interface
