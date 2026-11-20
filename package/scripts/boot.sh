#!/system/bin/sh
package_dir=/data/nemesis/apps/realtek.88x2bu
. "$package_dir/scripts/common.sh" || exit 1

trap 'exit 0' HUP INT TERM

pause() {
    sleep "$1" & wait $!
}

# Remember the first enumeration even if the net device never comes UP.
record_a3000mini_boot() (
    [ "$vendor:$product" = 0bda:b812 ] && read_boot_id || exit 0
    dir=/data/nemesis/logs/realtek.88x2bu
    marker="$dir/first-usb-device"
    if [ -r "$marker" ]; then
        read -r recorded _ < "$marker"
        [ "$recorded" != "$boot_id" ] || exit 0
    fi
    read -r number < "$usb/devnum" && read -r up_seconds _ < /proc/uptime || exit 0
    case "$number" in ''|*[!0-9]*) exit 0 ;; esac
    umask 022
    mkdir -p "$dir" || exit 0
    # This service is the sole writer. The head unit may not provide mv.
    echo "$boot_id ${usb##*/}:$number $up_seconds" > "$marker"
) 2>/dev/null

loader="$package_dir/scripts/load.sh"
read -r uptime _ < /proc/uptime
echo "RTL8812BU: early preload (uptime ${uptime:-unknown}s)"
identify_dongle && record_a3000mini_boot
/system/bin/sh "$loader" --boot-early

# Match the time when Manager can launch packages normally.
while [ "$(getprop sys.boot_completed)" != 1 ]; do
    pause 2
done
select_module && check_conflict || exit 1

attempt=0
last_device=
last_speed_device=
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
            record_a3000mini_boot
        fi

        usb_speed=
        if [ "$vendor:$product" = 0bda:b812 ] &&
           read -r usb_speed < "$usb/speed" && [ "$usb_speed" = 12 ] &&
           [ "$last_speed_device" != "$device" ]; then
            last_speed_device=$device
            echo "A3000mini is on 12Mbps; requesting scoped EHCI recovery."
            /system/bin/sh "$loader" --boot-speed
        fi

        if find_wifi_interface >/dev/null; then
            attempt=0
        elif [ "$attempt" -lt 3 ]; then
            attempt=$((attempt + 1))
            echo "Automatic Launch $attempt for $vendor:$product on $device."
            if [ "$attempt" -eq 2 ] && [ "$vendor:$product" = 0bda:b812 ] &&
               is_avante_boot_reset_target; then
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
