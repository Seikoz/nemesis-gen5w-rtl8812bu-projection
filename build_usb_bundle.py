#!/usr/bin/env python3
"""Combine the published CN7NPE packages into a NEMESIS USB package list."""

import argparse
import hashlib
import io
import zipfile
from pathlib import Path

from build_package import ROOT, archive


REALTEK = "packages/realtek.88x2bu.zip"
PROJECTION = "packages/korea.projection.zip"
USB_LIST = f"""[nemesis]
version=1.1
type=list

[package.0]
path={REALTEK}
name=Realtek RTL8812BU USB Driver
short-desc=v1.1.7 - Install first

[package.1]
path={PROJECTION}
name=Korea Projection CN7NPE USB Test
short-desc=v1.7.4.5 - Requires Realtek and HMG-API
"""


def read_package(installer, expected_sha256, path):
    content = installer.read_bytes()
    if hashlib.sha256(content).hexdigest() != expected_sha256:
        raise ValueError(f"Unexpected release ZIP SHA-256: {installer}")
    with zipfile.ZipFile(io.BytesIO(content)) as usb:
        return usb.read(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("driver", type=Path, help="Published Realtek v1.1.7 USB ZIP")
    parser.add_argument("projection", type=Path, help="Published Korea Projection 1.7.4.5 USB ZIP")
    parser.add_argument(
        "-o", "--output", type=Path,
        default=ROOT / "dist" / "NEMESIS-CN7NPE-260902-Bundle-v0.1.0-USB.zip",
    )
    args = parser.parse_args()
    try:
        bundle = archive({
            "NEMESIS.data": USB_LIST.encode("ascii"),
            "INSTALL-KO.md": (ROOT / "bundle" / "INSTALL-KO.md").read_bytes(),
            REALTEK: read_package(
                args.driver, "18e888442d26120c5b928e81427040f1586e6ec556f279bb7149b73e486a6596", REALTEK,
            ),
            PROJECTION: read_package(
                args.projection, "7a41ef0f5a1e3ad4db427bd028291f1300c3449e38821179a9bc0961cb873495", PROJECTION,
            ),
        })
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(bundle)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        parser.exit(1, f"Build failed: {error}\n")
    print(f"Built {args.output}")
    print(f"SHA-256 {hashlib.sha256(bundle).hexdigest()}")


if __name__ == "__main__":
    main()
