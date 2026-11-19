#!/system/bin/sh
package_dir=/data/nemesis/apps/realtek.88x2bu
. "$package_dir/scripts/common.sh" || exit 1

launch_mode=manual
log_name=launch
case "${1:-}" in
    --boot|--boot-early)
        launch_mode=boot
        log_name=boot
        ;;
esac
boot_phase="${1:-manual}"

if ! select_module || ! check_conflict; then
    save_launch_log "Driver load prerequisites failed; see preload.log for a boot attempt." failure
    exit 1
fi
check_korea_projection
identify_dongle
if ! read_boot_id; then
    echo "Cannot read the kernel boot ID."
    exit 1
fi
if ! module_is_loaded; then
    if insmod "$package_dir/modules/$module_file" 'ifname=rtwlan%d' 'if2name=rtwlan%d' \
        'rtw_power_mgnt=0' 'rtw_ips_mode=0' 'rtw_enusbss=0'; then
        if ! echo "$boot_id" > "$package_dir/.loaded-boot"; then
            rmmod 88x2bu
            echo "Cannot save this package's module state."
            exit 1
        fi
    elif ! module_is_loaded; then
        message="88x2bu failed to load on $platform."
        save_launch_log "$message" failure
        echo "$message"
        exit 1
    fi
fi
if ! owns_module && ! { sleep 1 && owns_module; }; then
    # Launch and the boot service can both observe a newly inserted module.
    message="88x2bu is already loaded by another package or tool."
    save_launch_log "$message" failure
    echo "$message"
    exit 1
fi
report_interface
