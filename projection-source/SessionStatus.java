package hmgapi.mods.wireless.dipo;

import android.os.Process;
import android.os.SystemClock;
import java.io.BufferedReader;
import java.io.FileReader;

/** Session callbacks only: no phone identity, credentials or packet data. */
final class SessionStatus {
    private static long sequence;
    private static long epoch;
    private static boolean warned;

    static synchronized void emit(String state, int transport) {
        final long request = ++epoch;
        final String generation = generation();
        write(state, transport, generation);
        if ("started".equals(state)) {
            // Refresh only the state established by a real callback. A later callback cancels
            // this chain. Retain the original AP generation even if the AP is recreated.
            Bridge.handler().postDelayed(new Runnable() {
                @Override public void run() {
                    synchronized (SessionStatus.class) {
                        if (epoch != request) return;
                        write("started", 1, generation);
                        Bridge.handler().postDelayed(this, 15000);
                    }
                }
            }, 15000);
        }
    }

    private static String generation() {
        try {
            return (String) Class.forName("android.os.SystemProperties")
                    .getMethod("get", String.class, String.class).invoke(null, "sys.kp.cp_gen", "off");
        } catch (Throwable t) { return "off"; }
    }

    private static void write(String state, int transport, String generation) {
        try {
            String start;
            BufferedReader r = new BufferedReader(new FileReader("/proc/self/stat"));
            try {
                String line = r.readLine();
                start = line.substring(line.lastIndexOf(')') + 2).split(" +")[19];
            } finally { r.close(); }
            Class<?> props = Class.forName("android.os.SystemProperties");
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
