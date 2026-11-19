"""Exercise the patched Bridge methods with a deterministic Android event queue."""
from pathlib import Path
import subprocess
import sys
import tempfile


def method(text, signature):
    start = text.index('    static ' + signature)
    opening = text.index('{', start)
    depth = 1
    end = opening + 1
    while depth:
        if text[end] == '{':
            depth += 1
        elif text[end] == '}':
            depth -= 1
        end += 1
    return text[start:end]


source = Path(sys.argv[1]).read_text(encoding='utf-8')
methods = '\n'.join(method(source, signature) for signature in (
    'synchronized void onSppUp(', 'synchronized void cancelUsbApRequest(',
    'boolean ensureHotspot(',
))
harness = r'''
import java.util.ArrayDeque;
import java.util.ArrayList;
class Intent {
    static final int FLAG_RECEIVER_FOREGROUND = 1;
    Intent(String action) {}
    void setPackage(String value) {}
    void addFlags(int value) {}
    void putExtra(String key, Object value) {}
}
class Context {
    void sendBroadcast(Intent i) {
        if (Bridge.failBroadcast) throw new RuntimeException("test failure");
        Bridge.attached++;
    }
}
class HfDeviceBTCMManager {
    boolean IbtcmIsSppConnectedDevice(String addr) { return Bridge.connected; }
}
class ApCheck {
    static final String AA_AP_PROP = "sys.kp.aa_ap";
    static final int SKIP_OURS = 2;
    static int decide(boolean on, int mode, String prop, String[] addresses) {
        for (String address : addresses) if (address.equals("192.168.43.1")) return SKIP_OURS;
        return 0;
    }
}
class Handler {
    ArrayDeque<Runnable> queue = new ArrayDeque<Runnable>();
    void post(Runnable runnable) { queue.add(runnable); }
    void postDelayed(Runnable runnable, int delay) {
        if (delay != 1000) throw new AssertionError("Unexpected retry interval");
        queue.add(runnable);
    }
    void next() { queue.remove().run(); }
}
class Retry { void cancel() {} }
class SessionStatus { static void emit(String state, int transport) {} }
class Bridge {
    static volatile Object sUsbApRequest;
    static boolean sSession, sCpClient, sCpWireless, sUsb;
    static String sAddr, apProperty;
    static boolean on, connected, addressReady, failBroadcast;
    static int attached;
    static final String ACTION_ATTACH = "BT_ATTACHED", IAP2_PKG = "iap2";
    static final int COMPONENT_BT_CARPLAY = 4;
    static final Retry SPP_RETRY = new Retry();
    static final Handler h = new Handler();
    static HfDeviceBTCMManager sBtcm;
    static Context context;
    static Handler handler() { return h; }
    static boolean enabled() { return on; }
    static String prop(String name, String fallback) { return apProperty; }
    static String[] wlanAddrs() { return new String[] { addressReady ? "192.168.43.1" : "192.168.1.2" }; }
    static String mask(String address) { return "[mac]"; }
    static void log(String message) {}
    static void error(String where, Throwable t) {}
METHODS
    static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
    static void reset() {
        h.queue.clear(); sUsbApRequest = null;
        sSession = sCpClient = sCpWireless = sUsb = failBroadcast = false;
        sAddr = null; attached = 0; apProperty = "0";
        on = connected = addressReady = true;
        sBtcm = new HfDeviceBTCMManager(); context = new Context();
    }
    public static void main(String[] args) {
        reset(); onSppUp("phone-A"); onSppUp("phone-A");
        check(h.queue.size() == 1, "Duplicate SPP events queued duplicate attempts");
        for (int i = 0; i < 79; i++) h.next();
        check(attached == 0 && h.queue.size() == 1, "iAP2 started before AP property");
        apProperty = "1"; h.next();
        check(attached == 1 && h.queue.isEmpty(), "No start when AP became ready");
        onSppUp("phone-A"); check(h.queue.isEmpty(), "Duplicate attach after successful start");

        reset(); apProperty = "1"; addressReady = false; onSppUp("phone-A"); h.next();
        check(attached == 0, "AP property alone was accepted without rtwlan0 address");
        addressReady = true; h.next(); check(attached == 1, "No start after address appeared");

        reset(); onSppUp("phone-A"); h.next(); connected = false; h.next();
        check(attached == 0 && !sSession && h.queue.isEmpty(), "Bluetooth loss did not cancel");

        reset(); onSppUp("phone-A"); h.next();
        // A stale timer from an earlier connection must not affect a new session.
        sSession = false; sAddr = null; onSppUp("phone-A"); apProperty = "1";
        h.next(); check(attached == 0 && sSession, "Stale attempt changed new session");
        h.next(); check(attached == 1, "New same-address connection failed");

        for (String state : new String[] {"usb", "wireless", "client", "disabled", "context", "manager"}) {
            reset(); onSppUp("phone-A"); h.next(); apProperty = "1";
            if (state.equals("usb")) sUsb = true;
            if (state.equals("wireless")) sCpWireless = true;
            if (state.equals("client")) sCpClient = true;
            if (state.equals("disabled")) on = false;
            if (state.equals("context")) context = null;
            if (state.equals("manager")) sBtcm = null;
            h.next(); check(attached == 0 && !sSession && h.queue.isEmpty(), "Did not cancel: " + state);
        }

        reset(); onSppUp("phone-A");
        for (int i = 0; i < 181; i++) h.next();
        check(attached == 0 && !sSession && h.queue.isEmpty(), "AP wait was unbounded");
        apProperty = "1"; onSppUp("phone-A"); h.next();
        check(attached == 1, "Retry after timeout failed");

        reset(); apProperty = "1"; failBroadcast = true; onSppUp("phone-A"); h.next();
        check(!sSession && sUsbApRequest == null, "Broadcast exception left stale session flag");
        System.out.println("Bridge ordering, delayed AP readiness, duplicate/stale attempts, cancellation, timeout and error tests passed.");
    }
}
'''.replace('METHODS', methods)
with tempfile.TemporaryDirectory() as td:
    path = Path(td)
    (path/'Bridge.java').write_text(harness)
    subprocess.run(['javac', '--release', '8', '-d', str(path), str(path/'Bridge.java')], check=True)
    subprocess.run(['java', '-cp', str(path), 'Bridge'], check=True)
