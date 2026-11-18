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

check_korea_projection() {
    local descriptor=/data/nemesis/apps/korea.projection/NEMESIS.data line
    projection_version=
    [ -r "$descriptor" ] || return 0
    while IFS= read -r line || [ -n "$line" ]; do
        case "$line" in
            package-version=*)
                projection_version=${line#package-version=}
                projection_version=${projection_version#\"}
                projection_version=${projection_version%\"}
                return 0
                ;;
        esac
    done < "$descriptor"
}

projection_rejects_usb() {
    case "$projection_version" in
        1.7.4.[123456]) return 1 ;; # CN7NPE Korea Projection USB test packages
        1.7|1.7.*) return 0 ;;
    esac
    return 1
}

is_cn7npe_boot_reset_target() {
    [ "$platform" = tcc803x ] || return 1
    case "$(getprop ro.build.product)" in
        CN7NPE.KOR.0000.V039.001.260902|CN7NPE.KOR.S5W_M.V039.001.260902) return 0 ;;
    esac
    return 1
}

claim_boot_recovery() {
    local marker stale
    case "$boot_id" in ''|*[!0-9a-f-]*) return 2 ;; esac
    marker="$package_dir/.usb-recovery-$boot_id"
    # Keep reset and reconfiguration in one attempt when both services retry.
    mkdir "$marker" 2>/dev/null || return 1
    for stale in "$package_dir"/.usb-recovery-*; do
        [ "$stale" = "$marker" ] || rmdir "$stale" 2>/dev/null
    done
    return 0
}

reset_boot_dongle() {
    local helper="$package_dir/bin/usb-reset-a3000mini"
    [ -x "$helper" ] || chmod 755 "$helper" || return 2
    "$helper" "$usb"
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

reconfigure_boot_dongle() (
    # Pin the directory so another USB device at the same port cannot be substituted.
    cd -P "$usb" 2>/dev/null || return 1
    local vid pid authorized count config class subclass protocol attempted intf
    intf=${usb_interface##*/}
    read -r vid < idVendor && [ "$vid" = 0bda ] &&
        read -r pid < idProduct && [ "$pid" = b812 ] &&
        read -r authorized < authorized && [ "$authorized" = 1 ] &&
        read -r count < bNumInterfaces && [ "$count" = 1 ] &&
        read -r config < bConfigurationValue && [ "$config" = 1 ] &&
        read -r class < "$intf/bInterfaceClass" &&
        read -r subclass < "$intf/bInterfaceSubClass" &&
        read -r protocol < "$intf/bInterfaceProtocol" &&
        [ "$class:$subclass:$protocol" = ff:ff:ff ] &&
        [ ! -L "$intf/driver" ] && [ -w bConfigurationValue ] || return 1
    if [ -r "$package_dir/.reconfigured-boot" ] &&
       read -r attempted < "$package_dir/.reconfigured-boot" &&
       [ "$attempted" = "$boot_id" ]; then
        return 1
    fi
    # Reapply the existing configuration to reprobe this unbound device once per boot.
    echo "$boot_id" > "$package_dir/.reconfigured-boot" || return 1
    echo "$config" > bConfigurationValue
)

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
        if [ "$launch_mode" = boot ]; then
            echo "usb_device_reset=${boot_reset:-not attempted}"
            echo "boot_reconfigure=${boot_reconfigure:-not attempted}"
        fi
        if [ -n "$projection_version" ]; then
            echo "korea_projection.version=$projection_version"
            if projection_rejects_usb; then
                echo "korea_projection.usb_wifi=unsupported"
            else
                echo "korea_projection.usb_wifi=not_checked"
            fi
        fi
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
    } > "$log_dir/$log_name.log"
) 2>/dev/null

wait_for_interface() {
    local attempt=0 limit=$1
    while [ "$attempt" -le "$limit" ]; do
        if identify_dongle; then
            net_name=$(find_wifi_interface) && return 0
            if [ "$attempt" -ge 2 ] && [ -z "$bind_result" ]; then
                retry_usb_bind
            fi
        fi
        [ "$attempt" -eq "$limit" ] || sleep 1
        attempt=$((attempt + 1))
    done
    return 1
}

report_interface() {
    local net_name driver message ready=0 limit=5 boot_reset= boot_reconfigure= bind_result=
    if [ "$launch_mode" = boot ]; then
        if [ "$boot_phase" = --boot-early ]; then
            limit=3
        else
            limit=12
        fi
    elif ! identify_dongle; then
        message="88x2bu loaded. Plug in a supported dongle and press Launch again."
        save_launch_log "$message" success
        echo "$message"
        return 0
    fi
    if wait_for_interface "$limit"; then
        ready=1
    elif [ "$boot_phase" = --boot ] && identify_dongle &&
         [ "$vendor:$product" = 0bda:b812 ] && [ ! -L "$usb_interface/driver" ] &&
         claim_boot_recovery; then
        if is_cn7npe_boot_reset_target; then
            local reset_result
            if reset_result=$(reset_boot_dongle 2>&1); then
                boot_reset="$reset_result"
                bind_result=
                wait_for_interface 8 && ready=1
            else
                boot_reset="skipped or failed${reset_result:+: $reset_result}"
            fi
            echo "A3000mini USB device reset: ${boot_reset:-requested}"
        fi
        if [ "$ready" -eq 0 ] && identify_dongle; then
            local reconfigure_error
            if reconfigure_error=$(reconfigure_boot_dongle 2>&1); then
                boot_reconfigure="requested"
                bind_result=
                wait_for_interface 5 && ready=1
            else
                boot_reconfigure="skipped or failed${reconfigure_error:+: $reconfigure_error}"
            fi
        fi
    fi
    if [ "$ready" -eq 1 ]; then
        message="RTL8812BU ready: $net_name ($vendor:$product)"
        save_launch_log "$message" success
        echo "$message"
        if projection_rejects_usb; then
            echo "Korea Projection $projection_version does not support USB Wi-Fi."
        fi
        return 0
    fi
    if ! identify_dongle; then
        message="88x2bu loaded, no supported USB dongle detected."
        save_launch_log "$message" failure
        echo "$message"
        return 1
    fi
    driver=$(bound_usb_driver || echo unbound)
    message="88x2bu loaded, no Wi-Fi interface ($vendor:$product, USB driver: $driver)."
    save_launch_log "$message" failure
    echo "$message"
    return 1
}
