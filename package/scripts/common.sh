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
    for usb in /sys/bus/usb/devices/*; do
        [ -r "$usb/idVendor" ] && [ -r "$usb/idProduct" ] || continue
        read -r vendor < "$usb/idVendor" || continue
        read -r product < "$usb/idProduct" || continue
        case "$vendor:$product" in
            @USB_IDS@) ;;
            *) continue ;;
        esac
        for usb_interface in "$usb":*; do
            [ -r "$usb_interface/bInterfaceClass" ] || continue
            read -r usb_class < "$usb_interface/bInterfaceClass" || continue
            read -r usb_subclass < "$usb_interface/bInterfaceSubClass" || continue
            read -r usb_protocol < "$usb_interface/bInterfaceProtocol" || continue
            [ "$usb_class:$usb_subclass:$usb_protocol" = ff:ff:ff ] || continue
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

report_interface() {
    for attempt in 1 2 3; do
        for net in "$usb_interface"/net/rtwlan*; do
            if [ -d "$net" ]; then
                echo "RTL8812BU ready: ${net##*/} ($vendor:$product)"
                return 0
            fi
        done
        sleep 1
    done
    echo "88x2bu loaded, but no USB Wi-Fi interface appeared ($vendor:$product)."
    return 1
}
