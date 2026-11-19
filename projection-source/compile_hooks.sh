#!/usr/bin/env bash
set -euo pipefail
out=$(realpath -m "$1")
source_dir=$(dirname "$(realpath "$0")")
python3 -m unittest discover -s "$source_dir/../tests" -v
mkdir -p "$out"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
rev=b573ac624e284cd7d6e0a7b9fa6c32862c528988
curl -fsSL --max-time 60 -o "$work/hmg.zip" "https://codeload.github.com/StopDragon/HMG-API/zip/$rev"
printf '%s  %s\n' 989d99692c66f5e9ac49ec40081668aa6f31a5c90f9e7f39f358d6dd0d2c78f5 "$work/hmg.zip" | sha256sum -c
unzip -q "$work/hmg.zip" -d "$work"
cd "$work/HMG-API-$rev"
mod=mods/wireless-carplay-aa
python3 "$source_dir/patch_hooks.py" "$mod"
python3 "$source_dir/test_ap_wait.py" "$mod/src/hmgapi/mods/wireless/dipo/Bridge.java"
python3 "$source_dir/test_session_status.py"
export JAVA_HOME="$JAVA_HOME_17_X64"
export PATH="$JAVA_HOME/bin:$PATH"
android=$(find "$ANDROID_HOME/platforms" -name android.jar | sort -V | tail -1)
d8=$(find "$ANDROID_HOME/build-tools" -name d8 | sort -V | tail -1)
mkdir -p "$work/runtime-stubs" "$work/runtime" "$work/mod-stubs" "$work/classes"
javac --release 8 -cp "$android" -d "$work/runtime-stubs" $(find core/runtime/stubs -name '*.java')
javac --release 8 -cp "$android:$work/runtime-stubs" -d "$work/runtime" $(find core/runtime/java -name '*.java')
javac --release 8 -cp "$android" -d "$work/mod-stubs" $(find "$mod/stubs" -name '*.java')
javac --release 8 -cp "$android:$work/runtime:$work/mod-stubs" -d "$work/classes" $(find "$mod/src" -name '*.java')
"$d8" --release --min-api 19 --lib "$android" --classpath "$work/runtime" --classpath "$work/mod-stubs" --output "$out/hooks.jar" $(find "$work/classes" -name '*.class')
python3 - "$out/hooks.jar" <<'PY'
import zipfile,sys
with zipfile.ZipFile(sys.argv[1]) as z:
    dex=z.read('classes.dex')
    assert dex.startswith(b'dex\n035\0') and b'rtwlan0\0' in dex and b'\x05wlan0\0' not in dex
    assert b'USB hotspot ready; starting Bluetooth iAP2' in dex
PY
sha256sum "$out/hooks.jar"
