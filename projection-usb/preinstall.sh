#!/system/bin/sh
export PATH=/sbin:/vendor/bin:/system/sbin:/system/bin:/system/xbin

case "$(getprop ro.build.product)" in
  CN7NPE.KOR.0000.V039.001.260902|CN7NPE.KOR.S5W_M.V039.001.260902) ;;
  *) echo "Requires CN7NPE KOR V039.001.260902"; exit 1 ;;
esac
[ "$(getprop ro.board.platform)" = tcc803x ] || exit 1
if [ ! -r /data/nemesis/apps/realtek.88x2bu/NEMESIS.data ]; then
  echo "Install and launch the RTL8812BU driver v1.1.4 first."
  exit 1
fi
if ! hmgapid ping >/dev/null 2>&1; then
  echo "Install and start HMG-API 1.1.0-rc.3 first."
  exit 1
fi
if [ -d /data/nemesis/apps/usbwifi.hotspot ] ||
   [ -d /data/nemesis/apps/wireless.projection ]; then
  echo "Uninstall the competing USB hotspot or wireless.projection package first."
  exit 1
fi

installed=/data/nemesis/apps/korea.projection/NEMESIS.data
mod=/data/hmgapi/mods/wireless-carplay-aa
if [ -e "$installed" ] &&
   ! { grep -q '^name=Korea Projection CN7NPE USB Test$' "$installed" &&
       grep -q '^package-version=1\.7\.4\.[1234]$' "$installed"; }; then
  echo "Uninstall the existing Korea Projection package before installing the CN7NPE USB test."
  exit 1
fi
if [ -e "$mod/mod.json" ] &&
   ! { [ -r "$installed" ] && [ -f /data/nemesis/backup/korea.projection/mod.ours ] &&
       grep -q '"uuid": "@MOD_AUTHOR@"' "$mod/META-HMGAPI/manifest.json" &&
       grep -q '"version": "2.4.6"' "$mod/META-HMGAPI/manifest.json"; }; then
  echo "Uninstall the existing wireless-carplay-aa mod before installing the CN7NPE USB test."
  exit 1
fi
exit 0
