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
if [ -e /data/hmgapi/mods/wireless-carplay-aa/mod.json ] ||
   [ -e /data/nemesis/apps/korea.projection/NEMESIS.data ] ||
   [ -d /data/nemesis/apps/usbwifi.hotspot ] ||
   [ -d /data/nemesis/apps/wireless.projection ]; then
  echo "Uninstall the existing Korea Projection, wireless CarPlay mod or competing USB hotspot first."
  exit 1
fi
exit 0
