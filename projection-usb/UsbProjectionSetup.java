package usbprojection;

import android.os.IBinder;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.lang.reflect.Method;
import org.json.JSONArray;
import org.json.JSONObject;

public final class UsbProjectionSetup {
    private static final String MOD = "wireless-carplay-aa";

    private UsbProjectionSetup() {}

    public static void main(String[] args) {
        try {
            if (args.length == 1 && "credentials".equals(args[0])) {
                credentials();
            } else if (args.length == 3 && ("allow".equals(args[0]) || "restore".equals(args[0]))) {
                allowNetwork(new File(args[1]), new File(args[2]), "allow".equals(args[0]));
            } else {
                throw new IllegalArgumentException("command");
            }
        } catch (Exception exception) {
            // Avoid emitting credentials or contents of the owner's settings file.
            System.err.println("USB projection " + args[0] + " failed (" + exception.getClass().getSimpleName() + ")");
            System.exit(1);
        }
    }

    private static void credentials() throws Exception {
        IBinder service = (IBinder) Class.forName("android.os.ServiceManager")
                .getMethod("getService", String.class).invoke(null, "wifi");
        Class<?> wifi = Class.forName("android.net.wifi.IWifiManager");
        Object proxy = Class.forName(wifi.getName() + "$Stub")
                .getMethod("asInterface", IBinder.class).invoke(null, service);
        Method getter = wifi.getMethod("getWifiApConfiguration");
        for (int attempt = 0; attempt < 6; attempt++) {
            Object config = getter.invoke(proxy);
            if (config != null) {
                String ssid = (String) config.getClass().getField("ConnectivitySSID").get(config);
                String key = (String) config.getClass().getField("ConnectivityPSK").get(config);
                if (ssid != null && !ssid.isEmpty() && ssid.getBytes("UTF-8").length <= 32
                        && !ssid.matches("(?s).*[\\p{Cntrl}].*")
                        && key != null && key.matches("[ -~]{8,63}")) {
                    System.out.println(ssid);
                    System.out.println(key);
                    return;
                }
            }
            if (attempt == 0) {
                // OEM's passkey initializer. This does not turn on the stock AP.
                wifi.getMethod("renewPasskey").invoke(proxy);
            }
            Thread.sleep(500);
        }
        throw new IOException("missing OEM connectivity credentials");
    }

    private static void allowNetwork(File file, File marker, boolean allow) throws Exception {
        if (!allow && !marker.isFile()) return;
        JSONObject config = file.isFile() ? new JSONObject(read(file)) : new JSONObject();
        JSONObject overrides = config.has("overrides") ? config.getJSONObject("overrides") : new JSONObject();
        boolean hadList = overrides.has("allow_network");
        JSONArray before = hadList ? overrides.getJSONArray("allow_network") : new JSONArray();
        JSONArray after = new JSONArray();
        boolean present = false;
        for (int i = 0; i < before.length(); i++) {
            Object rule = before.get(i);
            if (MOD.equals(rule)) present = true;
            else after.put(rule);
        }
        if (allow && present) return;
        if (!allow && !present) {
            marker.delete();
            return;
        }
        if (allow) {
            // Write ownership before changing config so an interrupted install can roll back.
            if (!marker.isFile()) atomicWrite(marker, hadList ? "list\n" : "new\n");
            after.put(MOD);
        }
        if (!allow && after.length() == 0 && "new\n".equals(read(marker))) {
            overrides.remove("allow_network");
        } else {
            overrides.put("allow_network", after);
        }
        if (overrides.length() == 0) config.remove("overrides");
        else config.put("overrides", overrides);
        atomicWrite(file, config.toString(2) + "\n");
        if (!allow) marker.delete();
    }

    private static String read(File file) throws IOException {
        if (file.length() > 1024 * 1024) throw new IOException("settings too large");
        java.io.ByteArrayOutputStream bytes = new java.io.ByteArrayOutputStream();
        try (FileInputStream input = new FileInputStream(file)) {
            byte[] buffer = new byte[4096];
            int size;
            while ((size = input.read(buffer)) != -1) bytes.write(buffer, 0, size);
        }
        return bytes.toString("UTF-8");
    }

    private static void atomicWrite(File target, String text) throws IOException {
        File folder = target.getParentFile();
        if (!folder.isDirectory() && !folder.mkdirs()) throw new IOException("settings directory");
        File temp = File.createTempFile(".kp-usb-", ".tmp", folder);
        try {
            try (FileOutputStream output = new FileOutputStream(temp)) {
                output.write(text.getBytes("UTF-8"));
                output.getFD().sync();
            }
            if (!temp.renameTo(target)) throw new IOException("rename");
        } finally {
            temp.delete();
        }
    }
}
