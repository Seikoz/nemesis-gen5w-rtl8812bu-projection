package io.github.seikoz.projectiondashboard;

import android.app.Activity;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.location.GpsSatellite;
import android.location.GpsStatus;
import android.location.LocationManager;
import android.os.Bundle;
import android.os.Handler;
import android.os.SystemClock;
import android.view.Gravity;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;

public final class DashboardActivity extends Activity {
    private static final File SNAPSHOT = new File("/data/local/tmp/korea-projection-dashboard.txt");
    private static final File BOOT_ID = new File("/proc/sys/kernel/random/boot_id");
    private static final File HMG_STATE = new File("/data/hmgapi/public/state.json");
    private static final String UNKNOWN = "확인 불가";
    private static final int BACKGROUND = 0xff101620;
    private static final int PANEL = 0xff1a2432;
    private static final int TEXT = 0xfff3f6fa;
    private static final int TEAL = 0xff7de1cb;
    private static final int AMBER = 0xffffce79;

    private final Handler handler = new Handler();
    private File active;
    private String bootId;
    private LocationManager locationManager;
    private boolean listeningForSatellites;
    private long satelliteSample = -1;
    private String satelliteSummary = UNKNOWN;
    private String gpsFix = UNKNOWN;
    private long heartbeat = -1;
    private long displayedSample = -1;
    private TextView freshness, boot, connection, gps, network, failure, hud, version;
    private final GpsStatus.Listener satelliteListener = this::readSatellites;
    private final Runnable tick = new Runnable() {
        @Override public void run() {
            long seconds = SystemClock.elapsedRealtime() / 1000;
            if (heartbeat < 0 || seconds - heartbeat >= 4) {
                if (writeLease(seconds)) heartbeat = seconds;
            }
            readSnapshot(seconds);
            showGps(seconds);
            handler.postDelayed(this, 1000);
        }
    };

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        active = new File(getFilesDir(), "active");
        bootId = readFile(BOOT_ID, 128).trim();
        locationManager = (LocationManager) getSystemService(LOCATION_SERVICE);
        buildScreen();
        DashboardShortcut.request(this, false);
    }

    @Override protected void onResume() {
        super.onResume();
        heartbeat = -1;
        satelliteSample = -1;
        startSatelliteListener();
        handler.removeCallbacks(tick);
        handler.post(tick);
    }

    @Override protected void onPause() {
        handler.removeCallbacks(tick);
        active.delete();
        if (listeningForSatellites) {
            listeningForSatellites = false;
            locationManager.removeGpsStatusListener(satelliteListener);
        }
        super.onPause();
    }

    private void startSatelliteListener() {
        if (locationManager == null) return;
        try {
            // Observe the native receiver's existing activity without requesting location fixes.
            listeningForSatellites = locationManager.addGpsStatusListener(satelliteListener);
        } catch (SecurityException error) {
            listeningForSatellites = false;
        }
    }

    private void readSatellites(int event) {
        if (!listeningForSatellites) return;
        if (event == GpsStatus.GPS_EVENT_STOPPED) {
            satelliteSample = -1;
            return;
        }
        if (event != GpsStatus.GPS_EVENT_SATELLITE_STATUS) return;
        GpsStatus status = locationManager.getGpsStatus(null);
        if (status == null) return;
        int received = 0;
        int used = 0;
        double sum = 0;
        for (GpsSatellite satellite : status.getSatellites()) {
            if (satellite.usedInFix()) used++;
            float snr = satellite.getSnr();
            if (snr > 0 && !Float.isInfinite(snr)) {
                received++;
                sum += snr;
            }
        }
        String signal = received == 0 ? UNKNOWN : Math.round(sum / received) + " dB";
        satelliteSummary = "수신 " + received + "기 · 위치 계산 " + used + "기 · 평균 SNR " + signal;
        satelliteSample = SystemClock.elapsedRealtime() / 1000;
    }

    private void showGps(long now) {
        String satellites = satelliteSample >= 0 && now - satelliteSample < 10
                ? satelliteSummary : "위성 수와 감도 확인 불가";
        String text = "차량 GPS " + gpsFix + "\n" + satellites + "\n휴대폰 GPS 연동 확인 불가";
        if (!text.contentEquals(gps.getText())) gps.setText(text);
    }

    private boolean writeLease(long seconds) {
        try (FileOutputStream out = new FileOutputStream(active)) {
            out.write(Long.toString(seconds).getBytes(StandardCharsets.US_ASCII));
            return true;
        } catch (IOException | SecurityException error) {
            freshness.setText("대시보드 서비스에 연결할 수 없습니다");
            return false;
        }
    }

    private void readSnapshot(long now) {
        Map<String, String> values = new HashMap<>();
        for (String line : readFile(SNAPSHOT, 8192).split("\n")) {
            int separator = line.indexOf('=');
            if (separator > 0) values.put(line.substring(0, separator), line.substring(separator + 1));
        }
        long sample;
        try {
            sample = Long.parseLong(values.get("sample"));
        } catch (NumberFormatException error) {
            sample = -1;
        }
        if (bootId.isEmpty() || !bootId.equals(values.get("boot")) || sample < 0 ||
                sample > now || now - sample > 12) {
            freshness.setText("상태 확인 중");
            freshness.setTextColor(AMBER);
            if (displayedSample >= 0) clearSample();
            return;
        }
        if (sample == displayedSample) return;
        displayedSample = sample;
        freshness.setText("마지막 확인 " + value(values, "checked") + " · 5초마다 갱신");
        freshness.setTextColor(TEAL);
        boot.setText(value(values, "s4"));
        failure.setText(value(values, "s5"));
        connection.setText(join(value(values, "s3"), values.get("stage")));
        gpsFix = value(values, "gps_fix");
        network.setText(join(value(values, "s2"), values.get("s6")));
        version.setText(value(values, "s1"));
        hud.setText(hudStatus());
    }

    private void clearSample() {
        displayedSample = -1;
        gpsFix = UNKNOWN;
        for (TextView row : new TextView[] {boot, failure, connection, network, version, hud}) {
            row.setText(UNKNOWN);
        }
    }

    private String hudStatus() {
        try {
            JSONObject state = new JSONObject(readFile(HMG_STATE, 262144)).getJSONObject("mods");
            JSONObject phone = state.optJSONObject("wired-carplay-tbt-lx2pe");
            JSONObject wireless = state.optJSONObject("wireless-carplay-aa");
            boolean phoneOn = phone != null && phone.getBoolean("enabled");
            boolean wirelessOn = wireless != null && wireless.getBoolean("enabled") &&
                    wireless.getJSONObject("settings").getBoolean("tbt");
            String phoneStatus = phone == null ? "미설치" : phoneOn ? "켜짐" : "꺼짐";
            String wirelessStatus = wireless == null ? "미설치" : wirelessOn ? "켜짐" : "꺼짐";
            String status = "Phone Projection TBT " + phoneStatus + " · Wireless Mode HUD " + wirelessStatus;
            return phoneOn && wirelessOn ? status + "\n두 HUD 설정이 모두 켜져 있습니다" : status;
        } catch (Exception error) {
            return "HUD 설정 확인 불가";
        }
    }

    private static String value(Map<String, String> values, String key) {
        String value = values.get(key);
        return value == null || value.isEmpty() ? UNKNOWN : value;
    }

    private static String join(String primary, String secondary) {
        return secondary == null || secondary.isEmpty() ? primary : primary + "\n" + secondary;
    }

    private static String readFile(File file, int limit) {
        try (FileInputStream in = new FileInputStream(file);
             ByteArrayOutputStream data = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[4096];
            int size;
            while ((size = in.read(buffer)) != -1) {
                if (data.size() + size > limit) return "";
                data.write(buffer, 0, size);
            }
            return new String(data.toByteArray(), StandardCharsets.UTF_8);
        } catch (IOException | SecurityException error) {
            return "";
        }
    }

    private void addShortcut() {
        boolean sent = DashboardShortcut.request(this, true);
        Toast.makeText(this, sent ? "런처에 바로가기 추가를 요청했습니다" : "바로가기 요청을 보낼 수 없습니다",
                Toast.LENGTH_SHORT).show();
    }

    private void buildScreen() {
        LinearLayout root = column();
        root.setBackgroundColor(BACKGROUND);
        root.setPadding(dp(20), dp(10), dp(20), dp(10));
        LinearLayout header = new LinearLayout(this);
        header.setGravity(Gravity.CENTER_VERTICAL);
        LinearLayout labels = column();
        TextView title = text("무선 연결 대시보드", 25, TEXT);
        title.setTypeface(null, Typeface.BOLD);
        labels.addView(title);
        freshness = text("상태 확인 중", 15, TEAL);
        labels.addView(freshness);
        header.addView(labels, new LinearLayout.LayoutParams(0, -2, 1));
        Button shortcut = new Button(this);
        shortcut.setText("홈 바로가기 추가");
        shortcut.setOnClickListener(view -> addShortcut());
        header.addView(shortcut, new LinearLayout.LayoutParams(-2, dp(52)));
        root.addView(header);

        ScrollView scroll = new ScrollView(this);
        LinearLayout grid = column();
        grid.setPadding(0, dp(10), 0, 0);
        boolean wide = getResources().getConfiguration().screenWidthDp >= 650;
        LinearLayout left = column();
        LinearLayout right = wide ? column() : left;
        if (wide) {
            grid.setOrientation(LinearLayout.HORIZONTAL);
            grid.addView(left, new LinearLayout.LayoutParams(0, -2, 1));
            LinearLayout.LayoutParams second = new LinearLayout.LayoutParams(0, -2, 1);
            second.leftMargin = dp(10);
            grid.addView(right, second);
        } else {
            grid.addView(left);
        }
        boot = card(left, "부팅 후 준비 시간");
        connection = card(left, "카플레이 · 안드로이드 오토");
        gps = card(left, "GPS 연동 상태");
        failure = card(left, "가장 최근 실패");
        network = card(right, "무선랜과 핫스폿");
        hud = card(right, "HUD 길안내");
        version = card(right, "설치 버전");
        scroll.addView(grid);
        root.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
        setContentView(root);
    }

    private TextView card(LinearLayout column, String label) {
        LinearLayout card = column();
        GradientDrawable background = new GradientDrawable();
        background.setColor(PANEL);
        background.setCornerRadius(dp(8));
        card.setBackground(background);
        card.setPadding(dp(12), dp(10), dp(12), dp(10));
        TextView heading = text(label, 15, TEAL);
        heading.setTypeface(null, Typeface.BOLD);
        card.addView(heading);
        TextView content = text(UNKNOWN, 17, TEXT);
        content.setPadding(0, dp(4), 0, 0);
        card.addView(content);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
        params.bottomMargin = dp(8);
        column.addView(card, params);
        return content;
    }

    private LinearLayout column() {
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        return layout;
    }

    private TextView text(String label, int sp, int color) {
        TextView view = new TextView(this);
        view.setText(label);
        view.setTextSize(sp);
        view.setTextColor(color);
        return view;
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
