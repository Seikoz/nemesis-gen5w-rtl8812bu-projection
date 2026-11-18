#!/usr/bin/env python3
"""Combine the published CN7NPE packages into a NEMESIS USB package list."""

import argparse
import hashlib
import io
import zipfile
from pathlib import Path

from build_package import MODULES, PACKAGE_PATH, RESET_HELPER_PATH, ROOT, archive, build_driver_package


PROJECTION = "packages/korea.projection.zip"
USB_LIST = f"""[nemesis]
version=1.1
type=list

[package.0]
path={PROJECTION}
name=Korea Projection CN7NPE USB Test
short-desc=v1.7.4.6 - Installs or updates Realtek as needed

[package.1]
path={PACKAGE_PATH}
name=Realtek RTL8812BU USB Driver
short-desc=v1.1.8 - Korea Projection USB dependency
"""


def read_package(installer, expected_sha256, path):
    content = installer.read_bytes()
    if hashlib.sha256(content).hexdigest() != expected_sha256:
        raise ValueError(f"Unexpected release ZIP SHA-256: {installer}")
    with zipfile.ZipFile(io.BytesIO(content)) as usb:
        return usb.read(path)


def build_projection_package(source):
    with zipfile.ZipFile(io.BytesIO(source)) as package:
        descriptor = package.read("NEMESIS.data")
        descriptor = descriptor.replace(b"package-version=1.7.4.5\n", b"package-version=1.7.4.6\n")
        descriptor = descriptor.replace(
            b'depends="!niro.carplay.hotspot"\n',
            b'depends="realtek.88x2bu@>=1.1.8,!niro.carplay.hotspot"\n',
        )
        descriptor = descriptor.replace(b"RTL8812BU v1.1.4 required.", b"RTL8812BU v1.1.8 or later required.")
        preinstall = package.read("scripts/preinstall.sh")
        preinstall = preinstall.replace(b"Install and launch the RTL8812BU driver v1.1.4 first.",
                                        b"Install the RTL8812BU driver v1.1.8 or later first.")
        preinstall = preinstall.replace(b"[12345]", b"[123456]")

        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as updated:
            for entry in package.infolist():
                name = entry.filename
                if name == "NEMESIS.data":
                    data = descriptor
                elif name == "scripts/preinstall.sh":
                    data = preinstall
                else:
                    data = package.read(entry)
                updated.writestr(entry, data)
        return output.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("driver", type=Path, help="Published Realtek v1.1.7 USB ZIP (kernel modules and reset helper)")
    parser.add_argument("projection", type=Path, help="Published Korea Projection 1.7.4.5 USB ZIP (base package)")
    parser.add_argument(
        "-o", "--output", type=Path,
        default=ROOT / "dist" / "NEMESIS-CN7NPE-260902-Bundle-v0.1.1-USB.zip",
    )
    args = parser.parse_args()
    try:
        driver_base = read_package(
            args.driver, "18e888442d26120c5b928e81427040f1586e6ec556f279bb7149b73e486a6596", PACKAGE_PATH,
        )
        with zipfile.ZipFile(io.BytesIO(driver_base)) as source:
            modules = {name: source.read(name) for name in MODULES}
            driver = build_driver_package(modules, source.read(RESET_HELPER_PATH))
        projection_base = read_package(
            args.projection, "7a41ef0f5a1e3ad4db427bd028291f1300c3449e38821179a9bc0961cb873495", PROJECTION,
        )
        bundle = archive({
            "NEMESIS.data": USB_LIST.encode("ascii"),
            "INSTALL-KO.md": (ROOT / "bundle" / "INSTALL-KO.md").read_bytes(),
            PACKAGE_PATH: driver,
            PROJECTION: build_projection_package(projection_base),
        })
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(bundle)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        parser.exit(1, f"Build failed: {error}\n")
    print(f"Built {args.output}")
    print(f"SHA-256 {hashlib.sha256(bundle).hexdigest()}")


if __name__ == "__main__":
    main()
