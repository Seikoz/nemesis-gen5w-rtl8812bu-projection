#!/system/bin/sh
export PATH=/sbin:/vendor/bin:/system/sbin:/system/bin:/system/xbin
loader=/data/nemesis/apps/realtek.88x2bu/scripts/load.sh

run_attempt() {
    echo "RTL8812BU: $1"
    /system/bin/sh "$loader" "$2"
    result=$?
    echo "RTL8812BU: $1 exit=$result"
}

run_attempt early --boot-early

# NEMESIS can start shell services before Android is up and before the USB
# stack has finished setting up the port. Keep the early preload, then retry.
waited=0
while [ "$(getprop sys.boot_completed)" != 1 ] && [ "$waited" -lt 90 ]; do
    sleep 2
    waited=$((waited + 2))
done
echo "RTL8812BU: boot_completed=$(getprop sys.boot_completed) waited=${waited}s"

# Recheck even after an early success. The booting unit can enumerate the same
# device again after the first attempt has already observed it.
for delay in 5 10 25; do
    sleep "$delay"
    run_attempt "late check (+${delay}s)" --boot
done
exit "$result"
