#!/usr/bin/env bash
set -euo pipefail

work=$(mktemp -d)
sudo install -d -o "$USER" /opt/src /opt/arm-eabi-4.7
driver_rev=04ed7009bac4b235fe1880ba29e23159f49a6121
grt_rev=bcfe084b198475c6edf138b8ee8e080bb48b7902
aosp_url=https://android.googlesource.com/platform/prebuilts/gcc/linux-x86/arm/arm-eabi-4.7
aosp_rev=8b880805d454664b3eed11d0f053cdeafa1ff06e
grt="https://raw.githubusercontent.com/GRT47/HKG_5W_USB_Wlan/$grt_rev/package_usbwifi_hotspot/kernel_build"

fetch() {
    curl --fail --silent --show-error --location --retry 2 --max-time 90 -o "$2" "$1"
    printf '%s  %s\n' "$3" "$2" | sha256sum --check
}
fetch "https://codeload.github.com/cilynx/rtl88x2bu/zip/$driver_rev" "$work/driver.zip" 60dd1192ad0bb71e67a49b96640888a2881784f8a6b613d131d370a09c3544a0
fetch "https://cdn.kernel.org/pub/linux/kernel/v3.x/linux-3.18.24.tar.xz" "$work/linux.tar.xz" ed54cf8c3ac6b95fc17b07b3a236bc42719c96fee08fe696cabfb5b8e07f8c1b
fetch "$grt/build_both_ko.sh" "$work/build_both_ko.sh" d8fb658cccfb14ad6e69f2a6d8e0e126798d6755105e57035b153ad86c2d8878
fetch "$grt/config_tcc803x.txt" "$work/config_tcc803x.txt" d35af8a0e9d098a47720ea66de594f21691d3d9608ce388ed199e0a5f82f9913
fetch "$grt/config_tcc897x.txt" "$work/config_tcc897x.txt" 5ab80920ccba78220fc174a433acbc18ec8034330bf806a75907bf73942605f7
fetch "https://github.com/GRT47/HKG_5W_USB_Wlan/releases/download/v2.0.7/HKG_5W_USBWifi_Hotspot.zip" "$work/original.zip" 1545bc400cfc32693f2fd0a1db155441ee753f35bf25d0b1485cf7d1b46673c3
if curl -fsSL --max-time 80 -o "$work/toolchain.tar.gz" "$aosp_url/+archive/$aosp_rev.tar.gz"; then
    tar -xzf "$work/toolchain.tar.gz" -C /opt/arm-eabi-4.7
else
    git -C /opt/arm-eabi-4.7 init --quiet
    git -C /opt/arm-eabi-4.7 -c http.version=HTTP/1.1 fetch --depth=1 "$aosp_url" "$aosp_rev"
    git -C /opt/arm-eabi-4.7 checkout --detach FETCH_HEAD
fi
export PATH="/opt/arm-eabi-4.7/bin:$PATH" ARCH=arm CROSS_COMPILE=arm-eabi-
arm-eabi-gcc --version

unzip -q "$work/driver.zip" -d /opt/src
mv "/opt/src/rtl88x2bu-$driver_rev" /opt/src/rtl88x2bu
tar -xJf "$work/linux.tar.xz" -C /opt/src
cp "$work/config_tcc803x.txt" /opt/src/linux-3.18.24/.config.tcc803x
cp "$work/config_tcc897x.txt" /opt/src/linux-3.18.24/.config.tcc897x

# Retain the pinned upstream driver patches and the 88x2bu build commands.
# The WSL chroot and 8851bu build are outside this build.
python3 - "$work" <<'PY'
import pathlib
import sys

work = pathlib.Path(sys.argv[1])
source = (work / "build_both_ko.sh").read_text()
patch_start = source.index("# Patch Makefile for GCC 4.7")
patch_end = source.index("\ngit diff --stat", patch_start)
kernel_start = source.index("prepare_kernel() {", patch_end)
kernel_end = source.index("\nOUT_MODS=", kernel_start)
module_start = source.index("\n# 1. Build 88x2bu_tcc897x.ko", kernel_end)
last_copy = source.index('cp /opt/src/rtl88x2bu/88x2bu.ko "$OUT_MODS/88x2bu.ko"', module_start)
module_end = source.index("\nfi\n", last_copy) + 4
sections = [source[patch_start:patch_end], source[kernel_start:kernel_end], source[module_start:module_end]]
(work / "rtl-build.sh").write_text("\n".join(sections) + "\n")
PY

export OUT_MODS="$work/rebuilt"
mkdir -p "$OUT_MODS"
cd /opt/src/rtl88x2bu
bash -e "$work/rtl-build.sh" > "$work/build.log" 2>&1 || { tail -n 120 "$work/build.log"; exit 1; }

unzip -p "$work/original.zip" packages/usbwifi.hotspot.zip > "$work/original-package.zip"
for module in 88x2bu.ko 88x2bu_tcc897x.ko; do
    old="$work/original-$module"
    new="$work/rebuilt/$module"
    unzip -p "$work/original-package.zip" "modules/$module" > "$old"
    echo "::group::$module verification"
    sha256sum "$old" "$new"
    for candidate in "$old" "$new"; do
        modinfo "$candidate"
        readelf -Ws "$candidate" | awk '$7 == "UND" && $8 != "" {print $8}' | sort -u > "$candidate.symbols"
    done
    diff -u "$old.symbols" "$new.symbols" || true
    if cmp -s "$old" "$new"; then echo "$module MATCH"; else echo "$module DIFFERS"; fi
    echo "::endgroup::"
done
