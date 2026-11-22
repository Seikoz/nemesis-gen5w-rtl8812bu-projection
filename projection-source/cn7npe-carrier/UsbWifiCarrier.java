// SPDX-License-Identifier: AGPL-3.0-only
// Adapted from UsbWifiCarrier.java in CN7PE-260902-A3000MINI-All-in-One-1.0.0.
package hmgapi.mods.cn7npecarrier;

import hmgapi.hook.LoadedApp;
import hmgapi.hook.ModContext;
import hmgapi.hook.ModEntry;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileReader;
import java.io.IOException;
import java.lang.reflect.Method;
import java.net.InetAddress;
import java.net.NetworkInterface;
import java.security.MessageDigest;
import java.util.Enumeration;
import java.util.concurrent.atomic.AtomicBoolean;

public final class UsbWifiCarrier extends ModEntry {
    private static final String DIPO = "com.daudio.app.dipo";
    private static final String LIBRARY = "libCarPlayCoreUtils.so";
    private static final String STOCK_MD5 = "cf3cc23dad25b181a9fc12d606468715";
    private static final File STOCK_FILE = new File("/system/lib", LIBRARY);
    private static final File NET = new File("/sys/class/net");
    private static final File USB = new File("/sys/bus/usb/devices");
    private static final char[] HEX = "0123456789abcdef".toCharArray();
    // On CN7NPE the AP has taken 151 seconds after boot to come up.
    private static final int AP_WAIT_POLLS = 960;
    private final AtomicBoolean started = new AtomicBoolean();

    @Override
    public void appLoaded(final ModContext mod, final LoadedApp app) {
        if (!DIPO.equals(app.packageName) || !DIPO.equals(app.processName)
                || !mod.enabled() || !started.compareAndSet(false, true)) return;
        Thread worker = new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    checkAndRequest(mod, app);
                } catch (InterruptedException interrupted) {
                    Thread.currentThread().interrupt();
                } catch (Exception error) {
                    mod.error("USB Wi-Fi carrier precondition failed", error);
                }
            }
        }, "cn7npe-usb-carplay-carrier");
        worker.setDaemon(true);
        worker.start();
    }

    private static void checkAndRequest(ModContext mod, LoadedApp app) throws Exception {
        Method get = Class.forName("android.os.SystemProperties")
                .getMethod("get", String.class, String.class);
        if (!target(property(get, "ro.build.product"), property(get, "ro.board.platform"))) {
            mod.log("Carrier skipped: different product or platform");
            return;
        }
        String stockMd5 = md5(STOCK_FILE);
        if (!supportsFingerprint(stockMd5)) {
            mod.log("Carrier skipped: CarPlay CoreUtils MD5 mismatch; found " + stockMd5);
            return;
        }
        mod.log("Carrier: CarPlay CoreUtils MD5 matched; waiting for supported USB Wi-Fi AP");
        for (int poll = 0; poll < AP_WAIT_POLLS; poll++) {
            if (!mod.enabled()) return;
            if (new File(NET, "wlan0").exists() || NetworkInterface.getByName("wlan0") != null) {
                mod.log("Carrier skipped: stock wlan0 present");
                return;
            }
            if (usbApReady(get) && hasSupportedAdapter(USB)) {
                if (mod.enabled()) mod.nativePatch(app, LIBRARY);
                return;
            }
            Thread.sleep(250);
        }
        mod.log("Carrier skipped: supported USB Wi-Fi AP did not become ready in 240 seconds");
    }

    static boolean target(String product, String platform) {
        return "tcc803x".equals(platform)
                && ("CN7NPE.KOR.0000.V039.001.260902".equals(product)
                || "CN7NPE.KOR.S5W_M.V039.001.260902".equals(product));
    }

    static boolean supportsFingerprint(String md5) {
        return STOCK_MD5.equals(md5);
    }

    private static String property(Method get, String name) throws Exception {
        return (String) get.invoke(null, name, "");
    }

    private static boolean usbApReady(Method get) throws Exception {
        if (!"1".equals(property(get, "sys.kp.aa_ap"))) return false;
        String generation = property(get, "sys.kp.cp_gen");
        if (generation.isEmpty() || "off".equals(generation)) return false;
        NetworkInterface net = NetworkInterface.getByName("rtwlan0");
        if (net == null || !net.isUp()) return false;
        for (Enumeration<InetAddress> addresses = net.getInetAddresses(); addresses.hasMoreElements();) {
            if ("192.168.43.1".equals(addresses.nextElement().getHostAddress())) return true;
        }
        return false;
    }

    static boolean hasSupportedAdapter(File root) {
        File[] devices = root.listFiles();
        if (devices == null) return false;
        for (File device : devices) {
            String id = readLine(new File(device, "idVendor")) + ":" + readLine(new File(device, "idProduct"));
            if ("0bda:b812".equalsIgnoreCase(id) || "2357:012d".equalsIgnoreCase(id)) return true;
        }
        return false;
    }

    private static String readLine(File file) {
        try (BufferedReader in = new BufferedReader(new FileReader(file))) {
            String line = in.readLine();
            return line == null ? "" : line.trim();
        } catch (IOException error) {
            return "";
        }
    }

    static String md5(File file) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("MD5");
        try (FileInputStream in = new FileInputStream(file)) {
            byte[] buffer = new byte[8192];
            for (int read; (read = in.read(buffer)) != -1;) digest.update(buffer, 0, read);
        }
        StringBuilder result = new StringBuilder(32);
        for (byte value : digest.digest()) {
            result.append(HEX[(value & 0xff) >>> 4]).append(HEX[value & 0x0f]);
        }
        return result.toString();
    }
}
