"""Remove the two optional consumers omitted from the CN7HEVPE manifest."""
from pathlib import Path
import sys

from patch_rc8 import method, once


def patch(root):
    wireless = root / 'Wireless.java'
    source = wireless.read_text(encoding='utf-8')
    source = once(source,
                  '        if (BTSETTINGS.equals(app.packageName) && mod.settingBoolean("menu", true)) phoneProjectionMenu(mod, app);\n',
                  '')
    source = method(source, 'private void phoneProjectionMenu(', '')
    source = once(source, '''    private final hmgapi.mods.cn7npecarrier.UsbWifiCarrier usbWifiCarrier =
            new hmgapi.mods.cn7npecarrier.UsbWifiCarrier();

''', '')
    source = once(source, '''        if (DIPO.equals(app.packageName) && mod.settingBoolean("bridge", true)) {
            usbWifiCarrier.appLoaded(mod, app);
        }
''', '')
    wireless.write_text(source, encoding='utf-8', newline='\n')
    (root.parent / 'cn7npecarrier/UsbWifiCarrier.java').unlink()

    dipo = root / 'dipo/Dipo.java'
    source = dipo.read_text(encoding='utf-8')
    start = source.index("        // the CarPlay library's disableBluetooth:")
    end = source.index("        // DiPO's own wireless CarPlay", start)
    dipo.write_text(source[:start] + source[end:], encoding='utf-8', newline='\n')


if __name__ == '__main__':
    patch(Path(sys.argv[1]))
