#!/usr/bin/env bash
set -euo pipefail
out=$(realpath -m "$1")
setup_java="$(dirname "$(realpath "$0")")/UsbProjectionSetup.java"
mkdir -p "$out"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
rev=b573ac624e284cd7d6e0a7b9fa6c32862c528988
curl -fsSL --max-time 60 -o "$work/hmg.zip" "https://codeload.github.com/StopDragon/HMG-API/zip/$rev"
printf '%s  %s\n' 989d99692c66f5e9ac49ec40081668aa6f31a5c90f9e7f39f358d6dd0d2c78f5 "$work/hmg.zip" | sha256sum -c
unzip -q "$work/hmg.zip" -d "$work"
cd "$work/HMG-API-$rev"
mod=mods/wireless-carplay-aa
python3 - "$mod" <<'PY'
import pathlib,sys
root=pathlib.Path(sys.argv[1])/'src/hmgapi/mods/wireless'
for name in ('Wireless.java','dipo/ApCheck.java'):
    path=root/name
    data=path.read_text()
    assert data.count('WIFI_IF = "wlan0";')==1, path
    path.write_text(data.replace('WIFI_IF = "wlan0";','WIFI_IF = "rtwlan0";'))
path = root / 'dipo/Bridge.java'
data = path.read_text()
start = data.index('        try {', data.index('    static void ensureHotspot(Context c) {'))
end = data.index('\n    }', start)
data = data[:start] + '''        int decision = ApCheck.decide(false, -1, "", wlanAddrs());
        log(decision == ApCheck.SKIP_OURS ? "USB hotspot ready" : "waiting for USB hotspot");
''' + data[end:]
path.write_text(data)
PY
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
mkdir "$work/setup"
javac --release 8 -cp "$android" -d "$work/setup" "$setup_java"
"$d8" --release --min-api 19 --lib "$android" --output "$out/setup.jar" $(find "$work/setup" -name '*.class')
python3 - "$out/hooks.jar" <<'PY'
import zipfile,sys
with zipfile.ZipFile(sys.argv[1]) as z:
    dex=z.read('classes.dex')
    assert dex.startswith(b'dex\n035\0') and b'rtwlan0\0' in dex and b'\x05wlan0\0' not in dex
PY
sha256sum "$out/hooks.jar" "$out/setup.jar"
