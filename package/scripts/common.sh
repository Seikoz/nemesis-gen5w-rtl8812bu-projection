#!/system/bin/sh
export PATH=/sbin:/vendor/bin:/system/sbin:/system/bin:/system/xbin

select_module() {
    platform=$(getprop ro.board.platform)
    case "$platform" in
        tcc803x) module_file=88x2bu.ko ;;
        tcc897x) module_file=88x2bu_tcc897x.ko ;;
        *) echo "Unsupported Gen5W platform: $platform"; return 1 ;;
    esac
    if ! read -r release < /proc/sys/kernel/osrelease; then
        echo "Cannot read the kernel release."
        return 1
    fi
    if [ "$release" != 3.18.24-tcc ]; then
        echo "Unsupported kernel: $release"
        return 1
    fi
    if [ ! -s "$package_dir/modules/$module_file" ]; then
        echo "Missing module: $module_file"
        return 1
    fi
}

module_is_loaded() {
    while read -r module_name rest; do
        [ "$module_name" = 88x2bu ] && return 0
    done < /proc/modules
    return 1
}

identify_dongle() {
    local device intf vid pid usb_class usb_subclass usb_protocol
    for device in /sys/bus/usb/devices/*; do
        [ -r "$device/idVendor" ] && [ -r "$device/idProduct" ] || continue
        read -r vid < "$device/idVendor" || continue
        read -r pid < "$device/idProduct" || continue
        case "$vid:$pid" in
            @USB_IDS@) ;;
            *) continue ;;
        esac
        for intf in "$device":*; do
            [ -r "$intf/bInterfaceClass" ] || continue
            read -r usb_class < "$intf/bInterfaceClass" || continue
            read -r usb_subclass < "$intf/bInterfaceSubClass" || continue
            read -r usb_protocol < "$intf/bInterfaceProtocol" || continue
            [ "$usb_class:$usb_subclass:$usb_protocol" = ff:ff:ff ] || continue
            usb=$device
            usb_interface=$intf
            vendor=$vid
            product=$pid
            return 0
        done
    done
    return 1
}

read_boot_id() {
    read -r boot_id < /proc/sys/kernel/random/boot_id && [ -n "$boot_id" ]
}

owns_module() {
    [ -r "$package_dir/.loaded-boot" ] &&
        read -r loaded_boot < "$package_dir/.loaded-boot" &&
        [ "$loaded_boot" = "$boot_id" ]
}

check_conflict() {
    if [ -d /data/nemesis/apps/usbwifi.hotspot ] ||
       [ -d /data/nemesis/packages/usbwifi.hotspot ]; then
        echo "Remove USB WiFi Hotspot Enabler before using this driver."
        return 1
    fi
}

bound_usb_driver() {
    local driver_path
    driver_path=$(cd -P "$usb_interface/driver" 2>/dev/null && pwd -P) || return 1
    echo "${driver_path##*/}"
}

retry_usb_bind() {
    local bind_path=/sys/bus/usb/drivers/rtl88x2bu/bind authorized
    [ -L "$usb_interface/driver" ] && return 0
    if [ -r "$usb/authorized" ] &&
       read -r authorized < "$usb/authorized" && [ "$authorized" = 0 ]; then
        bind_result="skipped: USB device deauthorized"
    elif [ ! -w "$bind_path" ]; then
        bind_result="unavailable: $bind_path is not writable"
    elif bind_error=$( (echo "${usb_interface##*/}" > "$bind_path") 2>&1); then
        bind_result="requested for ${usb_interface##*/}"
    else
        bind_result="failed for ${usb_interface##*/}: $bind_error"
    fi
}

find_wifi_interface() {
    local net usb_path net_path net_name driver_module
    usb_path=$(cd -P "$usb" 2>/dev/null && pwd -P) || return 1
    driver_module=$(cd -P "$usb_interface/driver/module" 2>/dev/null && pwd -P)
    for net in /sys/class/net/*; do
        [ -d "$net" ] || continue
        net_name=${net##*/}
        net_path=$(cd -P "$net" 2>/dev/null && pwd -P) || continue
        case "$net_path" in
            "$usb_path"/*)
                echo "$net_name"
                return 0
                ;;
            */virtual/net/*)
                # A virtual netdev needs both the USB binding and the 88x2bu proc entry.
                if { [ "$driver_module" = /sys/module/88x2bu ] ||
                     [ "$(bound_usb_driver)" = rtl88x2bu ]; } &&
                   [ -d "/proc/net/rtl88x2bu/$net_name" ]; then
                    echo "$net_name"
                    return 0
                fi
                ;;
        esac
    done
    return 1
}

save_launch_log() (
    umask 022
    log_dir=/data/nemesis/logs/realtek.88x2bu
    mkdir -p "$log_dir" || exit 1
    {
        echo "$1"
        echo "platform=$platform kernel=$release module=$module_file"
        if [ -n "$usb_interface" ]; then
            echo "usb=$vendor:$product path=${usb_interface##*/} driver=$(bound_usb_driver || echo unbound)"
            for field in authorized bConfigurationValue speed; do
                [ -r "$usb/$field" ] && read -r value < "$usb/$field" && echo "usb.$field=$value"
            done
            for field in modalias bNumEndpoints; do
                [ -r "$usb_interface/$field" ] && read -r value < "$usb_interface/$field" &&
                    echo "interface.$field=$value"
            done
        fi
        echo "manual_bind=${bind_result:-not attempted}"
        if [ -r /sys/bus/usb/drivers_autoprobe ] &&
           read -r value < /sys/bus/usb/drivers_autoprobe; then
            echo "usb.drivers_autoprobe=$value"
        fi
        for net in /sys/class/net/*; do
            [ -d "$net" ] || continue
            echo "net=${net##*/} path=$(cd -P "$net" 2>/dev/null && pwd -P)"
        done
        if [ "$2" = failure ]; then
            echo "Kernel messages for 88x2bu and this USB port:"
            dmesg | while IFS= read -r line; do
                case "$line" in *"SerialNumber:"*) continue ;; esac
                case "$line" in
                    *RTW:*|*88x2bu*) echo "$line" ;;
                    *) if [ -n "$usb" ]; then
                           case "$line" in *"usb ${usb##*/}:"*|*" ${usb_interface##*/}:"*) echo "$line" ;; esac
                       fi ;;
                esac
            done
        fi
    } > "$log_dir/launch.log"
) 2>/dev/null

report_interface() {
    local attempt net_name driver message
    if ! identify_dongle; then
        message="88x2bu loaded. Plug in a supported dongle and press Launch again."
        save_launch_log "$message" success
        echo "$message"
        return 0
    fi
    for attempt in 0 1 2 3 4 5; do
        [ "$attempt" = 0 ] || sleep 1
        identify_dongle || continue
        if net_name=$(find_wifi_interface); then
            message="RTL8812BU ready: $net_name ($vendor:$product)"
            save_launch_log "$message" success
            echo "$message"
            return 0
        fi
        [ "$attempt" = 2 ] && retry_usb_bind
    done
    driver=$(bound_usb_driver || echo unbound)
    message="88x2bu loaded, no Wi-Fi interface ($vendor:$product, USB driver: $driver)."
    save_launch_log "$message" failure
    echo "$message"
    return 1
}
