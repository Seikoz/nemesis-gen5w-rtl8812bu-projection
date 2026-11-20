#!/usr/bin/env bash
set -euo pipefail
out=$(realpath -m "$1")
src=$(dirname "$(realpath "$0")")
mkdir -p "$out"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
download() {
  curl -fsSL --max-time 90 -o "$work/$1.zip" "$2"
  printf '%s  %s\n' "$3" "$work/$1.zip" | sha256sum -c
  mkdir "$work/$1"
  unzip -q "$work/$1.zip" -d "$work/$1"
}
download mod https://codeload.github.com/Open-HMG/hmgapi-wireless-cp-aa/zip/c47c0bbf8513e725c9852acb932bdde39e3d7edc 5954b64ca3f962542192c2956e37d61c19f68c3f4dcf1d03b3c4f5bf141df59a
download core https://codeload.github.com/Open-HMG/HMG-API/zip/5732e261f544ef780bc0e4a5f7400ccc1b98edaa d0fa2e5135adb120e7f43f36d30a436eb39c86ead332ec1aaecc626f790f7347
download old https://codeload.github.com/StopDragon/HMG-API/zip/b573ac624e284cd7d6e0a7b9fa6c32862c528988 989d99692c66f5e9ac49ec40081668aa6f31a5c90f9e7f39f358d6dd0d2c78f5
download sdk https://github.com/Open-HMG/HMG-API/releases/download/v1.1.0-rc.7/hmgapi-mod-sdk-1.1.0-rc.7.zip ea5a9b2b84a48ebf25fe09b2a34bf22162b8b06f8b0f9bd6b43ff4aae234070a
export HMGAPI_SDK="$work/sdk"
mod="$work/mod/hmgapi-wireless-cp-aa-c47c0bbf8513e725c9852acb932bdde39e3d7edc/wireless-carplay-aa"
core="$work/core/HMG-API-5732e261f544ef780bc0e4a5f7400ccc1b98edaa"
old="$work/old/HMG-API-b573ac624e284cd7d6e0a7b9fa6c32862c528988/mods/wireless-carplay-aa"
python3 "$src/patch_rc8.py" "$mod" "$old/src/hmgapi/mods/wireless"
export JAVA_HOME="$JAVA_HOME_17_X64"
export PATH="$JAVA_HOME/bin:$PATH"
export ANDROID_JAR=$(find "$ANDROID_HOME/platforms" -name android.jar | sort -V | tail -1)
d8=$(find "$ANDROID_HOME/build-tools" -name d8 | sort -V | tail -1)
python3 -m unittest discover -s "$src/../tests" -v
python3 "$src/test_rc8_handover.py" "$mod/src/hmgapi/mods/wireless/dipo/Bridge.java"
python3 "$src/test_rc8_ap.py" "$mod/src/hmgapi/mods/wireless"
python3 "$src/test_rc8_park.py" "$mod/src/hmgapi/mods/wireless/dipo/ParkCp.java"
python3 "$src/test_session_status.py"
# The upstream sender's blocked-call/generation tests and reconnection tests.
for suite in reattach recipes projection cn7npe; do
  [ ! -f "$mod/tools/$suite/test.sh" ] || sh "$mod/tools/$suite/test.sh"
done
mkdir -p "$work/runtime-stubs" "$work/runtime" "$work/mod-stubs" "$work/classes"
javac --release 8 -cp "$ANDROID_JAR" -d "$work/runtime-stubs" $(find "$core/core/runtime/stubs" -name '*.java')
javac --release 8 -cp "$ANDROID_JAR:$work/runtime-stubs" -d "$work/runtime" $(find "$core/core/runtime/java" -name '*.java')
javac --release 8 -cp "$ANDROID_JAR" -d "$work/mod-stubs" $(find "$mod/stubs" -name '*.java')
javac --release 8 -cp "$ANDROID_JAR:$work/runtime:$work/mod-stubs" -d "$work/classes" $(find "$mod/src" -name '*.java')
"$d8" --release --min-api 19 --lib "$ANDROID_JAR" --classpath "$work/runtime" --classpath "$work/mod-stubs" --output "$out/hooks.jar" $(find "$work/classes" -name '*.class')
python3 - "$out/hooks.jar" <<'PY'
import zipfile,sys
with zipfile.ZipFile(sys.argv[1]) as z:
    dex=z.read('classes.dex')
    assert dex.startswith(b'dex\n035\0') and b'rtwlan0\0' in dex and b'\x05wlan0\0' not in dex
    for token in (b'USB hotspot ready; starting Bluetooth iAP2',b'USB_CP_EVENT',b'UsbAp;',b'ParkCp;',b'CpTx;'):
        assert token in dex,token
PY
sha256sum "$out/hooks.jar"
python3 "$src/test_rc8_package.py" "$out/hooks.jar" cn7npe
python3 "$src/test_rc8_package.py" "$out/hooks.jar" cn7pe
python3 "$src/patch_hybrid_rc8.py" "$mod/src/hmgapi/mods/wireless"
mkdir -p "$work/hybrid-classes"
javac --release 8 -cp "$ANDROID_JAR:$work/runtime:$work/mod-stubs" -d "$work/hybrid-classes" $(find "$mod/src" -name '*.java')
"$d8" --release --min-api 19 --lib "$ANDROID_JAR" --classpath "$work/runtime" --classpath "$work/mod-stubs" --output "$out/hooks-hybrid.jar" $(find "$work/hybrid-classes" -name '*.class')
sha256sum "$out/hooks-hybrid.jar"
python3 "$src/test_rc8_package.py" "$out/hooks.jar" cn7hevpe "$out/hooks-hybrid.jar"
