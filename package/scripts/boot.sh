#!/system/bin/sh
package_dir=/data/nemesis/apps/realtek.88x2bu
. "$package_dir/scripts/common.sh" || exit 1

trap 'exit 0' HUP INT TERM

pause() {
    sleep "$1" & wait $!
}

loader="$package_dir/scripts/load.sh"
read -r uptime _ < /proc/uptime
echo "RTL8812BU: early preload (uptime ${uptime:-unknown}s)"
/system/bin/sh "$loader" --boot-early

# Match the time when Manager can launch packages normally.
while [ "$(getprop sys.boot_completed)" != 1 ]; do
    pause 2
done
select_module && check_conflict || exit 1

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
            echo "Automatic Launch $attempt for $vendor:$product on $device."
            if [ "$attempt" -eq 2 ] && [ "$vendor:$product" = 0bda:b812 ] &&
               is_cn7npe_boot_reset_target; then
                output=$(/system/bin/sh "$loader" --boot 2>&1)
            else
                output=$(/system/xbin/nemesis pkg-launch realtek.88x2bu 2>&1)
            fi
            result=$?
            echo "driver startup exit=$result: $output"
        fi
    fi
    pause 5
done
