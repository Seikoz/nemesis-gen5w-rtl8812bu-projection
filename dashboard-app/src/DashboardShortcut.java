package io.github.seikoz.projectiondashboard;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;

public final class DashboardShortcut extends BroadcastReceiver {
    static final String REGISTER = "io.github.seikoz.projectiondashboard.REGISTER_SHORTCUT";
    private static final String REQUESTED = "requested";

    @Override public void onReceive(Context context, Intent intent) {
        if (REGISTER.equals(intent.getAction())) request(context, false);
    }

    static boolean request(Context context, boolean manual) {
        SharedPreferences state = context.getSharedPreferences("launcher_shortcut", Context.MODE_PRIVATE);
        if (!manual && state.getBoolean(REQUESTED, false)) return false;

        Intent open = new Intent(context, DashboardActivity.class);
        open.setAction(Intent.ACTION_MAIN);
        open.addCategory(Intent.CATEGORY_LAUNCHER);

        Intent shortcut = new Intent("com.android.launcher.action.INSTALL_SHORTCUT");
        shortcut.putExtra(Intent.EXTRA_SHORTCUT_INTENT, open);
        shortcut.putExtra(Intent.EXTRA_SHORTCUT_NAME, context.getApplicationInfo()
                .loadLabel(context.getPackageManager()).toString());
        shortcut.putExtra(Intent.EXTRA_SHORTCUT_ICON_RESOURCE,
                Intent.ShortcutIconResource.fromContext(context, context.getApplicationInfo().icon));
        shortcut.putExtra("duplicate", false);
        try {
            context.sendBroadcast(shortcut);
        } catch (SecurityException ex) {
            return false;
        }
        state.edit().putBoolean(REQUESTED, true).apply();
        return true;
    }
}
