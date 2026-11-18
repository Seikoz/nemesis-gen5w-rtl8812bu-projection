#!/usr/bin/env python3
"""Combine the published CN7NPE packages into a NEMESIS USB package list."""

import argparse
import hashlib
import io
import zipfile
from pathlib import Path

from build_package import MODULES, PACKAGE_PATH, RESET_HELPER_PATH, ROOT, archive, build_driver_package


PROJECTION = "packages/korea.projection.zip"
HMG_API = "packages/hmgapi.zip"
HMG_API_SHA256 = "5cc86084896231c80de593a5f51b44ddc1f84add1cc55f1ca56a9d73e76eeea8"
USB_LIST = f"""[nemesis]
version=1.1
type=list

[package.0]
path={PROJECTION}
name=Korea Projection CN7NPE USB Test
short-desc=v1.7.4.7 - Installs HMG-API and Realtek as needed

[package.1]
path={HMG_API}
name=HMG-API
short-desc=1.1.0-rc.3 - Korea Projection dependency

[package.2]
path={PACKAGE_PATH}
name=Realtek RTL8812BU USB Driver
short-desc=v1.1.9 - Korea Projection USB dependency
"""


def read_verified_release(path, expected_sha256):
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != expected_sha256:
        raise ValueError(f"Unexpected release ZIP SHA-256: {path}")
    return content


def read_package(installer, expected_sha256, path):
    with zipfile.ZipFile(io.BytesIO(read_verified_release(installer, expected_sha256))) as usb:
        return usb.read(path)


def build_projection_package(source):
    with zipfile.ZipFile(io.BytesIO(source)) as package:
        descriptor = package.read("NEMESIS.data")
        descriptor = descriptor.replace(b"package-version=1.7.4.5\n", b"package-version=1.7.4.7\n")
        descriptor = descriptor.replace(
            b'depends="!niro.carplay.hotspot"\n',
            b'depends="hmgapi@>=1.0.99.3,realtek.88x2bu@>=1.1.9,!niro.carplay.hotspot"\n',
        )
        descriptor = descriptor.replace(
            b"CN7NPE KOR 260902, HMG-API and RTL8812BU v1.1.4 required.",
            b"CN7NPE KOR 260902. Requires HMG-API 1.1.0-rc.3+ and Realtek 1.1.9+.",
        )
        preinstall = package.read("scripts/preinstall.sh")
        preinstall = preinstall.replace(
            b"Install and launch the RTL8812BU driver v1.1.4 first.",
            b"Install the RTL8812BU driver v1.1.9 or later first.",
        )
        preinstall = preinstall.replace(b"[12345]", b"[1234567]")
        preinstall = preinstall.replace(
            b'''if ! hmgapid ping >/dev/null 2>&1; then
  echo "Install and start HMG-API 1.1.0-rc.3 first."
  exit 1
fi''',
            b'''# A newly installed HMG-API may still be starting its daemon.
hmgapi_wait=0
until hmgapid ping >/dev/null 2>&1; do
  if [ "$hmgapi_wait" -ge 15 ]; then
    echo "HMG-API is not responding. Restart the head unit and retry Korea Projection."
    exit 1
  fi
  sleep 1
  hmgapi_wait=$((hmgapi_wait + 1))
done''',
        )

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
    parser.add_argument("hmg_api", type=Path, help="Official HMG-API 1.1.0-rc.3 NEMESIS package ZIP")
    parser.add_argument(
        "-o", "--output", type=Path,
        default=ROOT / "dist" / "NEMESIS-CN7NPE-260902-Bundle-v0.1.2-USB.zip",
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
        guide = ROOT / "bundle"
        bundle = archive({
            "NEMESIS.data": USB_LIST.encode("ascii"),
            "INSTALL-KO.md": (guide / "INSTALL-KO.md").read_bytes(),
            "licenses/HMG-API-AGPL-3.0.txt": (guide / "licenses" / "HMG-API-AGPL-3.0.txt").read_bytes(),
            PACKAGE_PATH: driver,
            PROJECTION: build_projection_package(projection_base),
            HMG_API: read_verified_release(args.hmg_api, HMG_API_SHA256),
        })
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(bundle)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        parser.exit(1, f"Build failed: {error}\n")
    print(f"Built {args.output}")
    print(f"SHA-256 {hashlib.sha256(bundle).hexdigest()}")


if __name__ == "__main__":
    main()
