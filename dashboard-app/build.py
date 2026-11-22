"""Build and verify the Android 4.4 projection dashboard APK."""

import argparse
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


SOURCE = Path(__file__).resolve().parent


def run(*args):
    subprocess.run([str(arg) for arg in args], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--android-jar", required=True, type=Path)
    parser.add_argument("--build-tools", required=True, type=Path)
    parser.add_argument("--r8", required=True, type=Path)
    parser.add_argument("--jdk", required=True, type=Path)
    parser.add_argument("--keystore", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if not os.environ.get("KP_DASHBOARD_STORE_PASSWORD"):
        parser.error("Set KP_DASHBOARD_STORE_PASSWORD for the dashboard signing key")

    extension = ".exe" if os.name == "nt" else ""
    java = args.jdk / "bin" / ("java" + extension)
    javac = args.jdk / "bin" / ("javac" + extension)
    aapt = args.build_tools / ("aapt" + extension)
    zipalign = args.build_tools / ("zipalign" + extension)
    apksigner = args.build_tools / "apksigner.jar"
    if not apksigner.is_file():
        apksigner = args.build_tools / "lib/apksigner.jar"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="projection-dashboard-") as temporary:
        workspace = Path(temporary)
        classes = workspace / "classes"
        classes.mkdir()
        run(javac, "--release", "8", "-encoding", "UTF-8", "-cp", args.android_jar,
            "-d", classes, *sorted((SOURCE / "src").glob("*.java")))
        java_archive = workspace / "dashboard.jar"
        with ZipFile(java_archive, "w") as jar:
            for file in sorted(classes.rglob("*.class")):
                jar.write(file, file.relative_to(classes).as_posix())
        run(java, "-cp", args.r8, "com.android.tools.r8.D8", "--min-api", "19",
            "--lib", args.android_jar, "--release", "--output", workspace, java_archive)

        base = workspace / "base.apk"
        aligned = workspace / "aligned.apk"
        run(aapt, "package", "-f", "-M", SOURCE / "AndroidManifest.xml",
            "-I", args.android_jar, "-S", SOURCE / "res", "-F", base)
        with ZipFile(base, "a") as unsigned:
            entry = ZipInfo("classes.dex", date_time=(1980, 1, 1, 0, 0, 0))
            unsigned.writestr(entry, (workspace / "classes.dex").read_bytes(), compress_type=ZIP_DEFLATED)
        run(zipalign, "-f", "4", base, aligned)
        run(java, "-jar", apksigner, "sign", "--min-sdk-version", "19", "--ks", args.keystore,
            "--ks-key-alias", "projection-dashboard", "--ks-pass", "env:KP_DASHBOARD_STORE_PASSWORD",
            "--v1-signing-enabled", "true", "--v2-signing-enabled", "false",
            "--v3-signing-enabled", "false", "--v4-signing-enabled", "false",
            "--out", args.output, aligned)
        run(java, "-jar", apksigner, "verify", "--min-sdk-version", "19", "--verbose", args.output)


if __name__ == "__main__":
    main()
