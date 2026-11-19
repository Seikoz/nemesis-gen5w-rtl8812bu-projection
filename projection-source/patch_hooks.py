"""Apply the CN7NPE USB changes to the pinned wireless-mod sources."""
from pathlib import Path
import sys


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f"Expected exactly one source anchor: {old[:80]}")
    return text.replace(old, new)


def patch(root):
    for name in ('Wireless.java', 'dipo/ApCheck.java'):
        path = root / name
        path.write_text(replace_once(path.read_text(encoding='utf-8'), 'WIFI_IF = "wlan0";',
                                     'WIFI_IF = "rtwlan0";'), encoding='utf-8', newline='\n')
    path = root / 'dipo/Bridge.java'
    text = path.read_text(encoding='utf-8')
    text = replace_once(text, '    static synchronized void onSppUp(final String addr) {',
                        '    static volatile Object sUsbApRequest;\n\n'
                        '    static synchronized void onSppUp(final String addr) {')
    start = text.index('    static synchronized void onSppUp(final String addr) {')
    end = text.index('\n    static void onUsbGone()', start)
    text = text[:start] + '''    static synchronized void onSppUp(final String addr) {
        if (addr == null || sSession) return;
        SPP_RETRY.cancel();
        sAddr = addr;
        if (sCpClient || sCpWireless || !enabled() || sUsb) return;
        sSession = true;
        final Object request = new Object();
        sUsbApRequest = request;
        handler().post(new Runnable() {
            private int apWaits;

            @Override
            public void run() {
                try {
                    if (sUsbApRequest != request || !sSession || !addr.equals(sAddr)) return;
                    HfDeviceBTCMManager manager = sBtcm;
                    if (!enabled() || sUsb || sCpClient || sCpWireless || manager == null ||
                            !manager.IbtcmIsSppConnectedDevice(addr)) {
                        cancelUsbApRequest(request);
                        log("USB hotspot wait cancelled: Bluetooth or CarPlay state changed");
                        return;
                    }
                    Context c = context;
                    if (c == null) {
                        cancelUsbApRequest(request);
                        log("no context, cannot start session");
                        return;
                    }
                    if (!ensureHotspot(c)) {
                        if (apWaits >= 180) {
                            cancelUsbApRequest(request);
                            log("USB hotspot wait timed out; reconnect Bluetooth after AP is ready");
                            return;
                        }
                        if (apWaits == 0 || apWaits % 30 == 0)
                            log("waiting for USB hotspot before Bluetooth iAP2 (" + apWaits + "s)");
                        apWaits++;
                        handler().postDelayed(this, 1000);
                        return;
                    }
                    synchronized (Bridge.class) {
                        // A disconnect/reconnect may have replaced this queued attempt.
                        if (sUsbApRequest != request || !sSession || !addr.equals(sAddr) ||
                                !enabled() || sUsb || sCpClient || sCpWireless) return;
                        log("USB hotspot ready; starting Bluetooth iAP2");
                        Intent i = new Intent(ACTION_ATTACH);
                        i.setPackage(IAP2_PKG);
                        i.addFlags(Intent.FLAG_RECEIVER_FOREGROUND);
                        i.putExtra("component", COMPONENT_BT_CARPLAY);
                        i.putExtra("serial", addr);
                        c.sendBroadcast(i);
                        sUsbApRequest = null;
                        log("BT_ATTACHED sent for " + mask(addr));
                    }
                } catch (Throwable t) {
                    cancelUsbApRequest(request);
                    error("onSppUp", t);
                }
            }
        });
    }

    static synchronized void cancelUsbApRequest(Object request) {
        if (sUsbApRequest == request) {
            sUsbApRequest = null;
            sSession = false;
        }
    }
''' + text[end:]
    start = text.index('    static void ensureHotspot(Context c) {')
    end = text.index('\n    }', start) + len('\n    }')
    text = text[:start] + '''    static boolean ensureHotspot(Context c) {
        // Korea Projection publishes this only after its hostapd has an AP address.
        // An interface address alone can exist before the AP has started.
        return "1".equals(prop(ApCheck.AA_AP_PROP, "")) &&
                ApCheck.decide(false, -1, "", wlanAddrs()) == ApCheck.SKIP_OURS;
    }''' + text[end:]
    for old, new in (
        ('if (sBt == null) sBt = new BtListener();',
         'if (sBt == null) { sBt = new BtListener(); SessionStatus.emit("idle", -1); }'),
        ('log("USB hotspot ready; starting Bluetooth iAP2");',
         'SessionStatus.emit("bt_attach", -1);\n                        log("USB hotspot ready; starting Bluetooth iAP2");'),
        ('static void onCpSessionCreated(Object cp) {',
         'static void onCpSessionCreated(Object cp) {\n        SessionStatus.emit("created", -1);'),
        ('sCpWireless = transport == 1 && !sUsb;',
         'sCpWireless = transport == 1 && !sUsb;\n        SessionStatus.emit(sCpWireless ? "started" : "wired", transport);'),
        ('static void onCpSessionFinalized(int type) {',
         'static void onCpSessionFinalized(int type) {\n        SessionStatus.emit("finalized", type);'),
    ):
        text = replace_once(text, old, new)
    path.write_text(text, encoding='utf-8', newline='\n')
    (path.parent / 'SessionStatus.java').write_text(
        (Path(__file__).parent / 'SessionStatus.java').read_text(encoding='utf-8'),
        encoding='utf-8', newline='\n')


if __name__ == '__main__':
    patch(Path(sys.argv[1]) / 'src/hmgapi/mods/wireless')
