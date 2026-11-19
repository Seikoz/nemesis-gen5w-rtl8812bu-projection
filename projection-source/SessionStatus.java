package hmgapi.mods.wireless.dipo;

import android.os.Process;
import android.os.SystemClock;
import java.io.BufferedReader;
import java.io.FileReader;

/** Session callbacks only: no phone identity, credentials or packet data. */
final class SessionStatus {
    private static long sequence;
    private static boolean warned;

    static synchronized void emit(String state, int transport) {
        try {
            String start;
            BufferedReader r = new BufferedReader(new FileReader("/proc/self/stat"));
            try {
                String line = r.readLine();
                start = line.substring(line.lastIndexOf(')') + 2).split(" +")[19];
            } finally { r.close(); }
            Class<?> props = Class.forName("android.os.SystemProperties");
            String generation = (String) props.getMethod("get", String.class, String.class)
                    .invoke(null, "sys.kp.cp_gen", "off");
            String record = "v1," + Process.myPid() + "," + start + "," + generation + "," +
                    SystemClock.elapsedRealtime() + "," + (++sequence) + "," + state + "," + transport;
            // A root collector can recover this exact record if property writes are denied.
            Bridge.log("USB_CP_EVENT " + record);
            try {
                props.getMethod("set", String.class, String.class)
                        .invoke(null, "sys.kp.cp_session", record);
            } catch (Throwable t) {
                if (!warned) {
                    warned = true;
                    Bridge.log("USB_CP_STATUS property write unavailable; logcat fallback required");
                }
            }
        } catch (Throwable t) {
            Bridge.log("USB_CP_STATUS unavailable: " + t.getClass().getSimpleName());
        }
    }
}
