"""Port pinned official wireless 2.2.0-rc.8 to the verified CN7NPE USB AP."""
from pathlib import Path
import sys

from patch_cp_tbt import patch_cp_tbt

HERE = Path(__file__).parent

def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Expected one rc.8 anchor: ' + old[:100])
    return text.replace(old, new)

def method(text, signature, new):
    start = text.index('    ' + signature)
    at = text.index('{', start)
    depth, end = 1, at + 1
    while depth:
        if text[end] == '{': depth += 1
        elif text[end] == '}': depth -= 1
        end += 1
    return text[:start] + new.rstrip() + text[end:]

def patch(mod, old):
    root = mod / 'src/hmgapi/mods/wireless'
    path = root / 'dipo/Bridge.java'
    text = path.read_text(encoding='utf-8')
    text = once(text, 'return !"0".equals(prop("persist.ev6.cpwl.enable", "1"));',
                'return !UsbAp.parked && !"0".equals(prop("persist.ev6.cpwl.enable", "1"));')
    text = once(text, '    static volatile String sAddr;', '''    static volatile Object sUsbApRequest, sUsbCpSession;
    static volatile Object sUsbDetachFence = new Object();
    static volatile boolean sUsbBtConfirmed;
    static volatile String sUsbCpGeneration;
    static volatile int sUsbCpTransport = -1;
    static Object sUsbCpFallback;
    static volatile Object sUsbCpRxLogged;
    static volatile Object sUsbCpTxLogged;
    static volatile Object sUsbCpTxAccepted, sUsbCpWaitPeer;
    static volatile Object sUsbCpSendFence = new Object();
    static int sUsbCpAttempts;
    static volatile String sAddr;''')
    text = method(text, 'static void onSppUp(final String addr)', '''    static synchronized void onSppUp(final String addr) {
        if (addr == null || sSession || sCpClient || sCpWireless || !enabled() || sUsb) return;
        Context cx = context;
        if (cx == null || !Choice.allowed(cx.getContentResolver(), Choice.CARPLAY, addr)) return;
        sAddr = addr;
        sSession = true;
        sUsbBtConfirmed = false;
        sUsbDetachFence = new Object();
        final Object request = new Object();
        sUsbApRequest = request;
        handler().post(new Runnable() {
            private int waits;
            @Override public void run() {
                try {
                    if (sUsbApRequest != request || !sSession || !addr.equals(sAddr)) return;
                    HfDeviceBTCMManager manager = sBtcm;
                    if (!enabled() || sUsb || sCpClient || sCpWireless || UsbAp.parked || manager == null ||
                            !manager.IbtcmIsSppConnectedDevice(addr)) { cancelUsbApRequest(request); return; }
                    Context c = context;
                    if (c == null || !Choice.allowed(c.getContentResolver(), Choice.CARPLAY, addr)) {
                        cancelUsbApRequest(request); return;
                    }
                    if (!ensureHotspot(c)) {
                        if (waits++ >= 180) {
                            cancelUsbApRequest(request);
                            log("USB hotspot wait timed out; reconnect Bluetooth after AP is ready"); return;
                        }
                        if (waits == 1 || waits % 30 == 0) log("waiting for USB hotspot before Bluetooth iAP2 (" + waits + "s)");
                        handler().postDelayed(this, 1000); return;
                    }
                    synchronized (Bridge.class) {
                        if (sUsbApRequest != request || !sSession || !addr.equals(sAddr) ||
                                !enabled() || sUsb || sCpClient || sCpWireless || !ensureHotspot(c)) return;
                        SessionStatus.emit("bt_attach", -1);
                        log("USB hotspot ready; starting Bluetooth iAP2");
                        Intent i = new Intent(ACTION_ATTACH);
                        i.setPackage(IAP2_PKG); i.addFlags(Intent.FLAG_RECEIVER_FOREGROUND);
                        i.putExtra("component", COMPONENT_BT_CARPLAY); i.putExtra("serial", addr);
                        c.sendBroadcast(i); sUsbApRequest = null;
                    }
                } catch (Throwable t) { cancelUsbApRequest(request); error("onSppUp", t); }
            }
        });
    }

    static synchronized void cancelUsbApRequest(Object request) {
        if (sUsbApRequest == request) { sUsbApRequest = null; sSession = false; }
    }

    static boolean usbCpApCurrent() {
        String generation = prop("sys.kp.cp_gen", "off");
        return enabled() && !sUsb && sUsbCpSession != null &&
                generation.equals(sUsbCpGeneration) && ensureHotspot(context);
    }

    static boolean wirelessTransport(int transport) {
        return !sUsb && (transport == 1 || (transport == 0 && usbCpApCurrent() &&
                ((sUsbBtConfirmed && sSession && sAddr != null) || (sCpWireless && sUsbCpTransport == 0))));
    }

    static synchronized void onUsbIapConnected(int component, String serial) {
        if (component == COMPONENT_USB) {
            sUsb = true; sSession = false; sUsbApRequest = null; sUsbBtConfirmed = false;
            sUsbCpSession = null; sUsbDetachFence = new Object();
            sUsbCpWaitPeer = null; sUsbCpTxAccepted = null;
            sCpWireless = false; sCpClient = false; sCpConnected = false;
            sReattach.sessionEnd(); sCpTx.reset("USB takeover", false);
            synchronized (sPendingIn) { sPendingIn.clear(); }
            SessionStatus.emit("idle", -1);
        } else if (component == COMPONENT_BT_CARPLAY) {
            sUsbBtConfirmed = !sUsb && sSession && sAddr != null && serial != null && sAddr.equalsIgnoreCase(serial);
            log("USB_CP_ORIGIN component=4 confirmed=" + sUsbBtConfirmed);
        }
    }''')
    text = method(text, 'static void ensureHotspot(Context c)', '''    static boolean ensureHotspot(Context c) {
        return c != null && UsbAp.ready();
    }''')
    text = once(text, '        if (sBt == null) sBt = new BtListener();',
                '        if (sBt == null) { sBt = new BtListener(); SessionStatus.emit("idle", -1); }')
    text = once(text, '    static void onCpSessionCreated(Object cp) {', '''    static synchronized void onCpSessionCreated(Object cp) {
        sReattach.sessionEnd(); sCpTx.reset("new CarPlay session", false);
        synchronized (sPendingIn) { sPendingIn.clear(); }
        sUsbCpSession = new Object(); sUsbDetachFence = new Object();
        sUsbCpFallback = null; sUsbCpRxLogged = null; sUsbCpTxLogged = null;
        sUsbCpWaitPeer = null; sUsbCpTxAccepted = null;
        sUsbCpGeneration = prop("sys.kp.cp_gen", "off"); sUsbCpAttempts = 0;
        sUsbCpTransport = -1; sCpWireless = false; sCpClient = false; sCpConnected = false;
        SessionStatus.emit("created", -1);''')
    text = once(text, '    static void onCpSessionStarted(int transport) {\n        sCpWireless = transport == 1 && !sUsb;', '''    static synchronized void onCpSessionStarted(int transport) {
        sUsbCpTransport = transport;
        sCpWireless = wirelessTransport(transport);
        SessionStatus.emit(sCpWireless ? "started" : (sUsb ? "wired" : "unclassified"), transport);
        log("USB_CP_ORIGIN raw_transport=" + transport + " confirmed_bt=" + sUsbBtConfirmed + " wireless=" + sCpWireless);''')
    text = once(text, '    static void onCpSessionFinalized(int type) {', '''    static synchronized void onCpSessionFinalized(int type) {
        sUsbCpSession = null; sUsbBtConfirmed = false; sUsbApRequest = null;
        sUsbCpFallback = null; sUsbCpRxLogged = null; sUsbCpTxLogged = null;
        sUsbCpWaitPeer = null; sUsbCpTxAccepted = null;
        SessionStatus.emit("finalized", type);''')
    text = method(text, 'static void onCpIapIn(Object cp, byte[] data, int len)', '''    static void onCpIapIn(Object cp, byte[] data, int len) {
        if (data == null || data.length == 0 || len <= 0) return;
        try {
            final byte[] packet = java.util.Arrays.copyOf(data, Math.min(len, data.length));
            final IIap2Service service;
            synchronized (Bridge.class) {
                if (!usbCpApCurrent() || cp == null || cp != sCp) return;
                final Object session = sUsbCpSession;
                if (sUsbCpRxLogged != session) {
                    sUsbCpRxLogged = session;
                    log("USB_CP_HANDOVER stage=first-peer-data len=" + packet.length + " client=" + sCpClient);
                }
                final boolean resume = sUsbCpWaitPeer == session;
                if (resume) {
                    sUsbCpWaitPeer = null;
                    sCpClient = false; sCpConnected = false;
                    sUsbCpSendFence = new Object();
                    sCpTx.reset("peer data after initial rc=19", false);
                    log("USB_CP_HANDOVER stage=resume-on-peer");
                }
                service = sCpConnected ? sIap2 : null;
                if (service == null) {
                    synchronized (sPendingIn) {
                        if (sPendingIn.size() < MAX_PENDING) sPendingIn.add(packet);
                    }
                    if (!sCpClient) startCpClient(resume ? "peer data after initial rc=19" : "iAP2 data from CarPlay channel");
                    return;
                }
            }
            flushPending(service);
            service.Iap2SvcTransportReadDone(packet, packet.length);
        } catch (Throwable t) {
            error("onCpIapIn", t);
        }
    }''')
    text = once(text, '    static void startCpClient(final String why) {',
                '    static synchronized void startCpClient(final String why) {')
    text = once(text, '        if (sCpClient) return;\n        sCpClient = true;', '''        if (sCpClient || !usbCpApCurrent() || sUsbCpWaitPeer == sUsbCpSession || sAddr == null || sCp == null ||
                (!sCpWireless && !sUsbBtConfirmed) || sUsbCpAttempts >= 2) return;
        sUsbCpAttempts++;
        sUsbCpFallback = null;
        sUsbCpTxLogged = null;
        sCpClient = true;''')
    # Both initial handover and upstream re-attach retain their native send/watchdog logic.
    for start_signature, end_signature in (
        ('    static synchronized void startCpClient(', '\n    static void onCpClientConnected'),
        ('    static void reattachCpClient(', '\n    static final class ReattachHost')):
        start=text.index(start_signature); end=text.index(end_signature,start)
        block=text[start:end]
        block=once(block, '        handler().post(new Runnable()', '        final Object session = sUsbCpSession;\n        final Object cp = sCp;\n        handler().post(new Runnable()')
        block=once(block, '                    Context c = context;', '''                    if (session != sUsbCpSession || sUsbCpWaitPeer == session) return;
                    if (cp != sCp || !sCpClient || !usbCpApCurrent()) { sCpClient = false; return; }
                    Context c = context;''')
        if 'startCpClient' in start_signature:
            block=once(block, '                    error("startCpClient", t);',
                       '                    if (session == sUsbCpSession) { sCpClient = false; sCpConnected = false; }\n                    error("startCpClient", t);')
        text=text[:start]+block+text[end:]
    text=once(text, '        sCpConnected = true;\n        IIap2Service',
              '        if (!sCpClient || !usbCpApCurrent() || sUsbCpWaitPeer == sUsbCpSession) return;\n        sCpConnected = true;\n        log("USB_CP_HANDOVER stage=component5-connected");\n        IIap2Service')
    text=once(text, '        if (cp == null || data == null || data.length == 0 || !sCpClient) return;',
              '        if (cp == null || data == null || data.length == 0 || !sCpClient || sUsbCpWaitPeer == sUsbCpSession) return;')
    text=once(text, '        sCpTx.reset("re-attach #" + attempt, true);',
              '        sUsbCpSendFence = new Object();\n        sCpTx.reset("re-attach #" + attempt, true);')
    text = once(text, '            Object r = nativeSend().invoke(cp, b, len);\n            return r instanceof Integer ? (Integer) r : -1;', '''            final Object session = sUsbCpSession;
            if (session == null || cp != sCp || !sCpClient || sUsbCpWaitPeer == session || !usbCpApCurrent()) return -1;
            final Object sendFence = sUsbCpSendFence;
            final boolean peerSeen = sUsbCpRxLogged == session;
            Object r = nativeSend().invoke(cp, b, len);
            int rc = r instanceof Integer ? (Integer) r : -1;
            synchronized (Bridge.class) {
                if (sUsbCpSession != session || sUsbCpSendFence != sendFence || cp != sCp || !sCpClient || !usbCpApCurrent()) return rc;
                if (sUsbCpTxLogged != session) {
                    sUsbCpTxLogged = session;
                    log("USB_CP_HANDOVER stage=first-native-send rc=" + rc + " len=" + len + " peer_seen=" + peerSeen);
                }
                if (rc == 0 && sUsbCpTxAccepted != session) {
                    sUsbCpTxAccepted = session;
                    log("USB_CP_HANDOVER stage=native-send-accepted");
                } else if (rc == 19 && sCpWireless && sUsbCpTransport == 0 &&
                           sUsbCpRxLogged != session && sUsbCpTxAccepted != session && sUsbCpWaitPeer != session) {
                    // This fingerprint is an initial rejection without evidence of a live tunnel.
                    // Let an inbound callback rearm the handover with a fresh server session.
                    sUsbCpWaitPeer = session;
                    sCpConnected = false;
                    sReattach.sessionEnd();
                    log("USB_CP_HANDOVER stage=waiting-after-rc19");
                }
            }
            return rc;''')
    text=once(text, '    static void onSppDown(String addr) {', '    static synchronized void onSppDown(String addr) {')
    text=once(text, '        if (!sCpClient || sUsb) {\n            log("re-attach #',
                    '        if (!sCpClient || sUsb || sUsbCpWaitPeer == sUsbCpSession) {\n            log("re-attach #')
    text=once(text, '        if (sCpWireless) {\n            sSession = false;', '''        sUsbApRequest = null;
        sUsbBtConfirmed = false;
        if (sCpWireless && usbCpApCurrent()) {
            log("USB_CP_HANDOVER stage=spp-down-preserved raw_transport=" + sUsbCpTransport);
            sSession = false;''')
    text = once(text, '            startCpClient("bluetooth dropped during wireless CarPlay");', '''            if (sUsbCpTransport == 0) waitForUsbCpPeer();
            else startCpClient("bluetooth dropped during wireless CarPlay");''')
    text = once(text, '    static void sendDetach() {', '''    // A transport-0 session may start before the tunneled iAP2 channel is ready.
    // Let a peer packet win, then keep the accessory-initiated fallback.
    static void waitForUsbCpPeer() {
        final Object session = sUsbCpSession;
        if (session == null || sCpClient || sUsbCpFallback == session) return;
        sUsbCpFallback = session;
        log("USB_CP_HANDOVER stage=waiting-for-peer timeout_ms=4000");
        handler().postDelayed(new Runnable() {
            @Override public void run() {
                synchronized (Bridge.class) {
                    if (sUsbCpFallback != session || sUsbCpSession != session) return;
                    sUsbCpFallback = null;
                    if (!sCpClient && sCpWireless && usbCpApCurrent()) {
                        log("USB_CP_HANDOVER stage=peer-wait-expired");
                        startCpClient("peer wait expired after wireless Bluetooth handover");
                    }
                }
            }
        }, 4000);
    }

    static void sendDetach() {''')
    text=once(text, '    static void sendDetach() {\n        handler()',
              '    static void sendDetach() {\n        final Object fence = sUsbDetachFence;\n        handler()')
    text=once(text, '                    Intent i = new Intent(ACTION_DETACH);',
              '                    if (fence != sUsbDetachFence || sUsb) return;\n                    Intent i = new Intent(ACTION_DETACH);')
    text=once(text, '            if (component == COMPONENT_USB) sUsb = true;\n            else if',
              '            onUsbIapConnected(component, serial);\n            if')
    text=once(text, '            } else if (component == COMPONENT_BT_CARPLAY) {\n                sSession = false;',
              '            } else if (component == COMPONENT_BT_CARPLAY) {\n                sUsbBtConfirmed = false;\n                sSession = false;')
    path.write_text(text,encoding='utf-8',newline='\n')
    for name in ('UsbAp.java','SessionStatus.java'):
        (path.parent/name).write_bytes((HERE/name).read_bytes())

    path = root / 'dipo/Dipo.java'
    text = path.read_text(encoding='utf-8')
    text = once(text, '                    log("DiPO: Bluetooth kept up for wireless CarPlay (disableBluetooth skipped)");',
                '''                    if (Bridge.sUsbCpTransport == 0 && Bridge.usbCpApCurrent()) {
                        log("USB_CP_AUDIO bluetooth_handoff=preserved");
                    }
                    log("DiPO: Bluetooth kept up for wireless CarPlay (disableBluetooth skipped)");''')
    path.write_text(text, encoding='utf-8', newline='\n')
    patch_cp_tbt(root / 'dipo', once)

    # The car's checked 351-point map predates these eight points. Declaring them
    # would refuse the whole mod, not just the optional feature. Do not register
    # their consumers in this target build (metadata is restricted by the signer).
    path=root/'Wireless.java';text=path.read_text(encoding='utf-8')
    text=once(text, '    @Override\n    public void appLoaded(', '''    private final hmgapi.mods.cn7npecarrier.UsbWifiCarrier usbWifiCarrier =
            new hmgapi.mods.cn7npecarrier.UsbWifiCarrier();

    @Override
    public void appLoaded(''')
    text=once(text, '        if (NAVIGATION.equals(app.packageName)) navigation(mod, app);', '''        if (DIPO.equals(app.packageName) && mod.settingBoolean("bridge", true)) {
            usbWifiCarrier.appLoaded(mod, app);
        }
        if (NAVIGATION.equals(app.packageName)) navigation(mod, app);''')
    carrier = root.parent / 'cn7npecarrier'
    carrier.mkdir(exist_ok=True)
    (carrier / 'UsbWifiCarrier.java').write_bytes((HERE / 'cn7npe-carrier/UsbWifiCarrier.java').read_bytes())
    text=once(text, '            PpManager.zygote(mod);', '            mod.log("USB target: projection manager awaits a checked map with PPService points");')
    text=once(text, '        if (SYSTEM_POPUP.equals(app.packageName) && mod.settingBoolean("menu", true)) popupSettings(mod, app);',
              '        // US/Canada popup hook is not declared for this Korean target map.')
    start=text.index('        if (GPM.equals(app.packageName) && mod.settingBoolean("park", true)) {')
    end=text.index('        if (BTSETTINGS.equals',start)
    text=text[:start]+'        // AA park requires receiver_service.on_create, newer than the checked map.\n'+text[end:]
    text=once(text, '        if (GPM.equals(app.packageName) && mod.settingBoolean("usb_drives", true)) usbDrives(mod, app);', '''        if ((GPM.equals(app.packageName) || AaWifi.PHONEPROJ.equals(app.packageName)) && mod.settingBoolean("aa_ap", true)) AaWifi.hook(mod, app);
        if (GPM.equals(app.packageName)) aaReady(mod, app, mod.settingBoolean("aa_ready_resend", true));
        if (GPM.equals(app.packageName) && mod.settingBoolean("usb_drives", true)) usbDrives(mod, app);''')
    old_wireless=(old/'Wireless.java').read_text(encoding='utf-8')
    start=old_wireless.index('    /** AaReady 훅')
    end=old_wireless.index('    /**',old_wireless.index('\n    private static void aaReadyHooks',start)+1)
    # Stop before usbDrives, after the entire ready helper method.
    end=old_wireless.index('    private void usbDrives',start)
    appendix=old_wireless[start:end]
    # The intervening usbDrives doc comment is harmless; import Hooks explicitly.
    text=once(text,'import hmgapi.hook.Car;','import hmgapi.hook.Car;\nimport hmgapi.hook.Hooks;')
    text=text.rstrip()[:-1]+appendix+'\n}\n'
    path.write_text(text,encoding='utf-8',newline='\n')
    for name in ('AaWifi.java','AaReady.java','Mac.java'):
        (root/name).write_bytes((old/name).read_bytes())

    path=root/'dipo/ParkCp.java';text=path.read_text(encoding='utf-8')
    text=once(text,'wireless = p.args.length > 0 && Integer.valueOf(WIRELESS).equals(p.args[0]);',
              'wireless = p.args.length > 0 && p.args[0] instanceof Integer && Bridge.wirelessTransport((Integer) p.args[0]);')
    text=once(text,'if (CarEvents.PARKED.equals(event) || CarEvents.SHUTDOWN.equals(event)) end(mod, cl, main, event);',
              'if (CarEvents.PARKED.equals(event) || CarEvents.SHUTDOWN.equals(event)) { UsbAp.parked = true; Bridge.cancelUsbApRequest(Bridge.sUsbApRequest); end(mod, cl, main, event); }')
    text=once(text,'else if (CarEvents.UNPARKED.equals(event)) back(mod, cl, main, event, 0);',
              'else if (CarEvents.UNPARKED.equals(event)) { UsbAp.parked = false; back(mod, cl, main, event, 0); }')
    text=once(text,'else if (CarEvents.WAKE.equals(event)) back(mod, cl, main, event, WAKE_DELAY_MS);',
              'else if (CarEvents.WAKE.equals(event)) { UsbAp.parked = false; back(mod, cl, main, event, WAKE_DELAY_MS); }')
    text=once(text,'        Runnable again = new Runnable() {','        Runnable again = new Runnable() {\n            private int waits;')
    text=once(text,'                    if (!ended) return;\n                    ended = false;', '''                    if (!ended || UsbAp.parked) return;
                    if (!UsbAp.ready()) {
                        if (waits++ < 180) main.postDelayed(this, 1000);
                        else mod.log("USB CarPlay wake: AP wait timed out");
                        return;
                    }
                    ended = false;''')
    path.write_text(text,encoding='utf-8',newline='\n')

if __name__ == '__main__':
    patch(Path(sys.argv[1]), Path(sys.argv[2]))
