package hmgapi.mods.wireless.dipo;

import java.net.InetAddress;
import java.net.NetworkInterface;
import java.util.ArrayList;
import java.util.Enumeration;

/** Korea Projection owns hostapd; the framework's built-in hotspot is not used. */
final class UsbAp {
    static volatile boolean parked;

    static boolean matches(String signal, String generation, boolean up, Iterable<String> addresses) {
        if (parked || !"1".equals(signal) || generation == null || generation.isEmpty() ||
                "off".equals(generation) || !up || addresses == null) return false;
        for (String address : addresses) if ("192.168.43.1".equals(address)) return true;
        return false;
    }

    static String prop(String name) throws Exception {
        return (String) Class.forName("android.os.SystemProperties")
                .getMethod("get", String.class, String.class).invoke(null, name, "");
    }

    static boolean ready() {
        try {
            NetworkInterface net = NetworkInterface.getByName("rtwlan0");
            if (net == null) return false;
            ArrayList<String> addresses = new ArrayList<String>();
            Enumeration<InetAddress> all = net.getInetAddresses();
            while (all.hasMoreElements()) addresses.add(all.nextElement().getHostAddress());
            return matches(prop("sys.kp.aa_ap"), prop("sys.kp.cp_gen"), net.isUp(), addresses);
        } catch (Throwable t) { return false; }
    }
}
