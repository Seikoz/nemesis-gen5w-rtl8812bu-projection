#!/usr/bin/env python3
"""Build the NEMESIS USB installer from the pinned Gen5W release."""

import argparse
import hashlib
import io
import re
import struct
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RELEASE = "https://github.com/GRT47/HKG_5W_USB_Wlan/releases/tag/v2.0.7"
ASSET = RELEASE.replace("/tag/", "/download/") + "/HKG_5W_USBWifi_Hotspot.zip"
ASSET_SHA256 = "1545bc400cfc32693f2fd0a1db155441ee753f35bf25d0b1485cf7d1b46673c3"
MODULES = ("modules/88x2bu.ko", "modules/88x2bu_tcc897x.ko")
VERMAGIC = b"vermagic=3.18.24-tcc SMP preempt mod_unload ARMv7 p2v8 \0"
USB_ALIAS = re.compile(
    rb"alias=usb:v([0-9A-F]{4})p([0-9A-F]{4})d\*dc\*dsc\*dp\*icFFiscFFipFFin\*\0"
)
PACKAGE_PATH = "packages/realtek.88x2bu.zip"
RESET_HELPER_PATH = "bin/usb-reset-a3000mini"
USB_DESCRIPTOR = f"[nemesis]\nversion=1.0\ntype=install\npath={PACKAGE_PATH}\n"


def load_modules(upstream):
    if upstream is None:
        with urllib.request.urlopen(ASSET, timeout=45) as response:
            content = response.read()
    else:
        content = upstream.read_bytes()

    actual_hash = hashlib.sha256(content).hexdigest()
    if actual_hash != ASSET_SHA256:
        raise ValueError(f"Upstream ZIP SHA-256 mismatch: {actual_hash}")

    with zipfile.ZipFile(io.BytesIO(content)) as release_zip:
        package_bytes = release_zip.read("packages/usbwifi.hotspot.zip")
    with zipfile.ZipFile(io.BytesIO(package_bytes)) as package_zip:
        return {path: package_zip.read(path) for path in MODULES}


def usb_ids(path, module):
    if (
        len(module) < 20
        or module[:6] != b"\x7fELF\x01\x01"
        or struct.unpack_from("<HH", module, 16) != (1, 40)
    ):
        raise ValueError(f"{path}: expected a relocatable 32-bit little-endian ARM ELF")
    if VERMAGIC not in module or b"depends=\0" not in module:
        raise ValueError(f"{path}: unexpected kernel module metadata")

    ids = {f"{vid.decode()}:{pid.decode()}".lower() for vid, pid in USB_ALIAS.findall(module)}
    if not {"0bda:b812", "0bda:b82c"}.issubset(ids):
        raise ValueError(f"{path}: missing expected Realtek USB aliases")
    return ids


def archive(files):
    output = io.BytesIO()
    with zipfile.ZipFile(output, mode="w") as package:
        for name, data in sorted(files.items()):
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            mode = 0o100755 if name.endswith(".sh") or name == RESET_HELPER_PATH else 0o100644
            entry.external_attr = mode << 16
            package.writestr(entry, data, compress_type=zipfile.ZIP_DEFLATED)
    return output.getvalue()


def build_driver_package(modules, helper, *, diagnostics=False):
    files = dict(modules)
    if diagnostics:
        markers = (
            b"Gen5W chip-init failed stage=halmac-firmware",
            b"Gen5W halmac failed stage=firmware-download",
            b"Gen5W halmac failed stage=power-switch",
            b"Gen5W USB netdevs unregistered on disconnect",
            b"Gen5W chip-init failed iface=%s stage=netdev-open-hal",
        )
        for path in MODULES:
            if not all(marker in files[path] for marker in markers):
                raise ValueError(f"{path}: missing Gen5W chip initialization diagnostics")
    ids_by_module = [usb_ids(path, files[path]) for path in MODULES]
    if ids_by_module[0] != ids_by_module[1]:
        raise ValueError("The platform modules have different USB aliases")

    if (len(helper) < 52 or helper[:6] != b"\x7fELF\x01\x01"
            or struct.unpack_from("<HH", helper, 16) != (3, 40)
            or b"/system/bin/linker\0" not in helper):
        raise ValueError("The USB reset helper must be a 32-bit ARM Android PIE executable")
    if diagnostics and b"USB high-speed:" not in helper:
        raise ValueError("The USB reset helper does not include scoped EHCI recovery")
    if diagnostics and b"USB cold recovery:" not in helper:
        raise ValueError("The USB reset helper does not include external host restart")
    files[RESET_HELPER_PATH] = helper

    package_dir = ROOT / "package"
    for path in sorted(package_dir.rglob("*")):
        if path.is_file():
            name = path.relative_to(package_dir).as_posix()
            text = path.read_text(encoding="utf-8")
            if diagnostics and name == "NEMESIS.data":
                text = text.replace("package-version=1.1.9\n", "package-version=1.1.19\n")
            if diagnostics and name == "MODULE-SOURCE.txt":
                text = (
                    "The Gen5W diagnostic modules are based on GRT47 v2.0.7. "
                    "See MODULE-LICENSE.txt.\n"
                    "Corresponding source, diagnostic patch and build instructions:\n"
                    "https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/tree/cn7npe-usb-bundle-v0.1.17/driver-source\n"
                    "USB recovery helper and loader source:\n"
                    "https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/blob/cn7npe-usb-bundle-v0.1.17/driver-source/usb_reset_a3000mini.c\n"
                    "https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/tree/cn7npe-usb-bundle-v0.1.17/package/scripts\n"
                )
            if name == "scripts/common.sh":
                if text.count("@USB_IDS@") != 1:
                    raise ValueError("Missing or repeated USB ID placeholder")
                text = text.replace("@USB_IDS@", "|".join(sorted(ids_by_module[0])))
            files[name] = text.encode("utf-8")

    return archive(files)


def build(upstream, output, reset_helper):
    driver = build_driver_package(load_modules(upstream), reset_helper.read_bytes())
    usb = archive({"NEMESIS.data": USB_DESCRIPTOR.encode("utf-8"), PACKAGE_PATH: driver})
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(usb)
    print(f"Built {output}")
    print(f"SHA-256 {hashlib.sha256(usb).hexdigest()}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", type=Path, help="Local copy of the upstream release ZIP")
    parser.add_argument("--usb-reset-helper", required=True, type=Path,
                        help="Android API 19 ARMv7 USB reset executable")
    parser.add_argument(
        "-o", "--output", type=Path, default=ROOT / "dist" / "NEMESIS-RTL8812BU-Gen5W-USB.zip"
    )
    args = parser.parse_args()
    try:
        build(args.upstream, args.output, args.usb_reset_helper)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        parser.exit(1, f"Build failed: {error}\n")


if __name__ == "__main__":
    main()
