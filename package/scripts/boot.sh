#!/system/bin/sh
package_dir=/data/nemesis/apps/realtek.88x2bu
. "$package_dir/scripts/common.sh" || exit 1

trap 'exit 0' HUP INT TERM

pause() {
    sleep "$1" & wait $!
}

# Match the time when Manager can launch packages normally.
while [ "$(getprop sys.boot_completed)" != 1 ]; do
    pause 2
done
select_module && check_conflict || exit 1

log_dir=/data/nemesis/logs/realtek.88x2bu
if mkdir -p "$log_dir"; then
    echo "Automatic NEMESIS Launch started after Android boot." > "$log_dir/boot.log"
fi

boot_log() {
    printf '%s\n' "$1"
    printf '%s\n' "$1" >> "$log_dir/boot.log"
}

attempt=0
last_device=
while :; do
    if ! identify_dongle; then
        attempt=0
        last_device=
    else
        # devnum also changes if Android replaces the device at the same port.
        device_number=
        if [ -r "$usb/devnum" ]; then
            read -r device_number < "$usb/devnum"
        fi
        device="${usb##*/}:$device_number"
        if [ "$device" != "$last_device" ]; then
            attempt=0
            last_device=$device
        fi

        if find_wifi_interface >/dev/null; then
            attempt=0
        elif [ "$attempt" -lt 3 ]; then
            attempt=$((attempt + 1))
            boot_log "Automatic Launch $attempt for $vendor:$product on $device."
            output=$(/system/xbin/nemesis pkg-launch realtek.88x2bu 2>&1)
            result=$?
            boot_log "pkg-launch exit=$result: $output"
        fi
    fi
    pause 5
done
