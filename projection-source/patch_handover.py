"""Constrain transport-0 recognition to our confirmed USB-AP Bluetooth session."""
from patch_hooks import replace_once


def patch(text):
    text = replace_once(text, '    static volatile Object sUsbApRequest;', '''    static volatile Object sUsbApRequest;
    static volatile boolean sUsbBtConfirmed;
    static volatile Object sUsbCpSession;
    static volatile Object sUsbDetachFence = new Object();
    static volatile String sUsbCpGeneration;
    static volatile int sUsbCpTransport = -1;
    static int sUsbCpAttempts;''')
    text = replace_once(text, '        sSession = true;\n        final Object request',
        '''        sSession = true;
        sUsbBtConfirmed = false;
        sUsbDetachFence = new Object();
        final Object request''')
    text = replace_once(text, '        SessionStatus.emit("created", -1);', '''        sUsbCpSession = new Object();
        sUsbDetachFence = new Object();
        sCpWireless = false;
        sCpClient = false;
        sCpConnected = false;
        sUsbCpGeneration = prop("sys.kp.cp_gen", "off");
        sUsbCpTransport = -1;
        sUsbCpAttempts = 0;
        SessionStatus.emit("created", -1);''')
    text = replace_once(text, '        sCpWireless = transport == 1 && !sUsb;\n        SessionStatus.emit(sCpWireless ? "started" : "wired", transport);', '''        sUsbCpTransport = transport;
        boolean btUsbAp = sUsbBtConfirmed && sSession && sAddr != null && usbCpApCurrent();
        sCpWireless = !sUsb && (transport == 1 || (transport == 0 && btUsbAp));
        SessionStatus.emit(sCpWireless ? "started" : (sUsb ? "wired" : "unclassified"), transport);
        log("USB_CP_ORIGIN raw_transport=" + transport + " usb=" + sUsb +
                " confirmed_bt_usb_ap=" + btUsbAp + " wireless=" + sCpWireless);''')
    text = replace_once(text, '        SessionStatus.emit("finalized", type);', '''        sUsbCpSession = null;
        sUsbBtConfirmed = false;
        SessionStatus.emit("finalized", type);''')
    start = text.index('    static void startCpClient(final String why) {')
    end = text.index('\n    private static void flushPending', start)
    text = text[:start] + '''    static boolean usbCpApCurrent() {
        String generation = prop("sys.kp.cp_gen", "off");
        return enabled() && !sUsb && sUsbCpSession != null &&
                generation.length() > 0 && !"off".equals(generation) &&
                generation.equals(sUsbCpGeneration) && ensureHotspot(context);
    }

    static synchronized void onUsbIapConnected(int component, String serial) {
        if (component == COMPONENT_USB) {
            sUsb = true;
            sSession = false;
            sUsbBtConfirmed = false;
            sUsbCpSession = null;
            sUsbDetachFence = new Object();
            sCpWireless = false;
            sCpClient = false;
            sCpConnected = false;
            synchronized (sPendingIn) { sPendingIn.clear(); }
            SessionStatus.emit("idle", -1);
        } else if (component == COMPONENT_BT_CARPLAY) {
            sUsbBtConfirmed = !sUsb && sSession && sAddr != null &&
                    serial != null && sAddr.equalsIgnoreCase(serial);
            log("USB_CP_ORIGIN component=4 confirmed=" + sUsbBtConfirmed);
        }
    }

    static void startCpClient(final String why) {
        final Object session;
        final String addr;
        final Object cp;
        synchronized (Bridge.class) {
            if (sCpClient || !usbCpApCurrent() || sAddr == null || sCp == null ||
                    (!sCpWireless && !sUsbBtConfirmed) || sUsbCpAttempts >= 2) return;
            NOW_PLAYING.reset();
            sCpClient = true;
            sCpConnected = false;
            sUsbCpAttempts++;
            session = sUsbCpSession;
            addr = sAddr;
            cp = sCp;
        }
        handler().post(new Runnable() {
            @Override public void run() {
                synchronized (Bridge.class) {
                    if (session != sUsbCpSession) return;
                    if (!sCpClient || cp != sCp || !addr.equals(sAddr) || !usbCpApCurrent()) {
                        sCpClient = false;
                        log("USB_CP_HANDOVER stage=cancelled");
                        return;
                    }
                    try {
                        Context c = context;
                        if (c == null) throw new IllegalStateException("no context");
                        Intent i = new Intent(ACTION_ATTACH);
                        i.setPackage(IAP2_PKG);
                        i.addFlags(Intent.FLAG_RECEIVER_FOREGROUND);
                        i.putExtra("component", COMPONENT_CARPLAY_CLIENT);
                        i.putExtra("serial", addr);
                        c.sendBroadcast(i);
                        log("USB_CP_HANDOVER stage=requested raw_transport=" + sUsbCpTransport);
                        log("iAP2 handover to CarPlay channel requested (" + why + ")");
                    } catch (Throwable t) {
                        sCpClient = false;
                        sCpConnected = false;
                        log("USB_CP_HANDOVER stage=send-failed");
                        error("startCpClient", t);
                    }
                }
            }
        });
    }

    static void onCpClientConnected() {
        if (!sCpClient || !usbCpApCurrent()) return;
        sCpConnected = true;
        log("USB_CP_HANDOVER stage=component5-connected raw_transport=" + sUsbCpTransport);
        IIap2Service s = sIap2;
        if (s != null) flushPending(s);
    }
''' + text[end:]
    start = text.index('    static void onSppDown(String addr) {')
    end = text.index('\n    static void sendDetach()', start)
    text = text[:start] + '''    static synchronized void onSppDown(String addr) {
        if (addr == null || !addr.equals(sAddr)) return;
        sUsbBtConfirmed = false;
        if (sCpWireless && usbCpApCurrent()) {
            sSession = false;
            log("USB_CP_HANDOVER stage=spp-down-preserved raw_transport=" + sUsbCpTransport);
            startCpClient("Bluetooth SPP ended after wireless session start");
            return;
        }
        sAddr = null;
        if (sSession) {
            sSession = false;
            sendDetach();
        }
    }
''' + text[end:]
    text = replace_once(text, '    static void sendDetach() {\n        handler()',
                        '    static void sendDetach() {\n        final Object fence = sUsbDetachFence;\n        handler()')
    # Fence only the detach broadcast, without holding Bridge across a binder operation.
    text = replace_once(text, '                    Intent i = new Intent(ACTION_DETACH);', '''                    if (fence != sUsbDetachFence || sUsb) return;
                    Intent i = new Intent(ACTION_DETACH);''')
    text = replace_once(text, '            if (component == COMPONENT_USB) sUsb = true;',
                        '            onUsbIapConnected(component, serial);')
    # The inserted observation must not separate the original if/else pair.
    text = replace_once(text, '            onUsbIapConnected(component, serial);\n            else if',
                        '            onUsbIapConnected(component, serial);\n            if')
    text = replace_once(text, '            } else if (component == COMPONENT_BT_CARPLAY) {\n                sSession = false;',
                        '            } else if (component == COMPONENT_BT_CARPLAY) {\n                sUsbBtConfirmed = false;\n                sSession = false;')
    for signature in ('onCpSessionCreated(Object cp)', 'onCpSessionStarted(int transport)',
                      'onCpSessionFinalized(int type)'):
        text = replace_once(text, 'static void ' + signature, 'static synchronized void ' + signature)
    start = text.index('    static void sendDetach() {')
    end = text.index('\n    /** SPP data', start)
    detach = text[start:end]
    detach = replace_once(detach, '                    if (fence != sUsbDetachFence',
                          '                    synchronized (Bridge.class) {\n                    if (fence != sUsbDetachFence')
    detach = replace_once(detach, '                    log("BT_DETACHED sent");',
                          '                    log("BT_DETACHED sent");\n                    }')
    text = text[:start] + detach + text[end:]
    start = text.index('    static void writeCp(byte[] data) {')
    end = text.index('\n    static synchronized void onSppDown', start)
    write = text[start:end]
    write = replace_once(write, '        final Object cp = sCp;',
                         '        final Object session = sUsbCpSession;\n        final Object cp = sCp;')
    write = replace_once(write, '        if (cp == null ||', '        if (session == null || cp == null ||')
    write = replace_once(write, '                    Object r = nativeSend().invoke(cp, b, b.length);',
        '''                    if (session != sUsbCpSession || cp != sCp || !sCpClient || !usbCpApCurrent()) return;
                    Object r = nativeSend().invoke(cp, b, b.length);''')
    text = text[:start] + write + text[end:]
    start = text.index('    static void onCpIapIn(')
    end = text.index('\n    static synchronized void onCpSessionFinalized', start)
    read = text[start:end]
    read = replace_once(read, '            if (cp != null) sCp = cp;',
        '''            if (sUsbCpSession == null || !usbCpApCurrent() || (sCp != null && cp != null && cp != sCp)) return;
            if (cp != null) sCp = cp;''')
    text = text[:start] + read + text[end:]
    return text
