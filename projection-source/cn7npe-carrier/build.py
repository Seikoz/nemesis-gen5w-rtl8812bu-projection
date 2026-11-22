#!/usr/bin/env python3
"""Build the signed carrier input for build_usb_bundle.py."""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
import uuid
from zipfile import ZIP_DEFLATED, ZipFile

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec


HERE = Path(__file__).resolve().parent
def run(*args):
    subprocess.run(list(map(str, args)), check=True)


def sign(mod, key_path):
    """Use the HMG-API manifest format without exporting private key material."""
    private_key = serialization.load_pem_private_key(key_path.read_bytes(), password=None)
    public = private_key.public_key().public_bytes(
        serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    fingerprint = bytearray(hashlib.sha256(public).digest()[:16])
    fingerprint[6] = (fingerprint[6] & 0x0f) | 0x80
    fingerprint[8] = (fingerprint[8] & 0x3f) | 0x80
    identity = json.loads((mod / "mod.json").read_text(encoding="utf-8"))
    manifest = {
        "format": 1,
        "id": identity["id"],
        "version": identity["version"],
        "uuid": str(uuid.UUID(bytes=bytes(fingerprint))),
        "key": base64.b64encode(public).decode("ascii"),
        "files": {
            file.relative_to(mod).as_posix(): hashlib.sha256(file.read_bytes()).hexdigest()
            for file in sorted(mod.rglob("*")) if file.is_file()
        },
    }
    payload = json.dumps(manifest, indent=2).encode("utf-8") + b"\n"
    signature = private_key.sign(payload, ec.ECDSA(hashes.SHA256()))
    meta = mod / "META-HMGAPI"
    meta.mkdir()
    (meta / "manifest.json").write_bytes(payload)
    (meta / "signature").write_bytes(base64.b64encode(signature) + b"\n")
    return f'{identity["id"]}-{identity["version"]}.zip'


def build(args, work):
    exe = ".exe" if os.name == "nt" else ""
    java, javac = (args.jdk / "bin" / (name + exe) for name in ("java", "javac"))
    engine = args.sdk / "lib/hmgapi-engine.jar"
    runtime = args.sdk / "lib/hmgapi-runtime.jar"
    stubs = args.sdk / "lib/hmgapi-runtime-stubs.jar"
    classpath = os.pathsep.join(map(str, (runtime, stubs, engine)))
    classes, usb, mod = (work / name for name in ("classes", "usb", "mod"))
    classes.mkdir()
    usb.mkdir()
    (mod / "recipes").mkdir(parents=True)
    recipe = HERE / "recipes/usb-wifi-name.recipe"
    run(javac, "--release", "8", "-cp", classpath, "-d", classes,
        HERE / "UsbWifiCarrier.java", HERE / "CarrierTest.java")
    run(java, "-cp", str(classes) + os.pathsep + classpath,
        "hmgapi.mods.cn7npecarrier.CarrierTest", recipe, usb)

    bytecode = work / "classes.jar"
    with ZipFile(bytecode, "w", ZIP_DEFLATED) as jar:
        for file in sorted(classes.rglob("UsbWifiCarrier*.class")):
            jar.write(file, file.relative_to(classes).as_posix())
    run(java, "-cp", args.r8, "com.android.tools.r8.D8", "--min-api", "19",
        "--lib", args.jdk, "--classpath", runtime, "--output", mod / "hooks.jar", bytecode)
    with ZipFile(mod / "hooks.jar") as jar:
        if jar.testzip() or not jar.read("classes.dex").startswith(b"dex\n035\0"):
            raise ValueError("Unexpected DEX for Gen5W Android 4.4")
    shutil.copyfile(recipe, mod / "recipes" / recipe.name)
    shutil.copyfile(HERE / "mod.json", mod / "mod.json")
    name = sign(mod, args.key)
    run(java, "-cp", engine, "hmgapi.engine.Signing", "verify", mod)
    with ZipFile(work / name, "w", ZIP_DEFLATED) as archive:
        for file in sorted(mod.rglob("*")):
            if file.is_file():
                archive.write(file, file.relative_to(mod).as_posix())
    return work / name


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    for name in ("jdk", "sdk", "r8", "key"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="cn7npe-carrier-") as folder:
        carrier = build(args, Path(folder))
        shutil.copyfile(carrier, args.output)
    print(f"Built {args.output}")
    print(f"SHA-256 {hashlib.sha256(args.output.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
