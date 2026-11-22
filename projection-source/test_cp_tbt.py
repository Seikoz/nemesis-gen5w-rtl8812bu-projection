"""Replay route and maneuver notifications through the actual CarPlay HUD handler."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


STUBS = {
    'android/content/Context.java': 'package android.content; public class Context {}',
    'android/text/format/DateFormat.java': '''
package android.text.format;
public class DateFormat { public static boolean is24HourFormat(android.content.Context c) { return true; } }
''',
    'hmgapi/hook/Car.java': '''
package hmgapi.hook;
public class Car {
    public static final int DISTANCE_KM = 0, DISTANCE_MILES = 1;
    public static int distanceUnit(android.content.Context c) { return DISTANCE_KM; }
}
''',
    'hmgapi/hook/Cluster.java': '''
package hmgapi.hook;
public class Cluster {
    public static final int UNIT_M=0, UNIT_KM=1, UNIT_MI=2, UNIT_FT=3, UNIT_YD=4;
    public int frames, type, unit;
    public float direction, meters;
    public boolean roadAfterTurn;
    public void tbtInfo(int t, int side, float dir, float d, int err, int combi, int u, int bar, int mode) {
        frames++; type=t; direction=dir; meters=d; unit=u;
    }
    public void crossroadName(String name) { roadAfterTurn = frames > 0; }
    public void destinationName(int t, String name) {}
    public void tbtSubInfo(float d, int a, int b, int c, int e, int f, int g, float h, int i, int j) {}
    public void tbtSubInfo2C(int a, int b, int c, int d, int e, int f, int g, int h, int i) {}
    public void turnListNew(byte[] data) {}
    public void laneInfo(byte[] data) {}
    public void turnList(Turn[] turns) {}
    public static class Turn {
        public int type, traffic, no, unit;
        public float direction, distance;
        public String name, exitNumber;
    }
}
''',
    'com/tcc/iap2/Iap2NotiMsg.java': '''
package com.tcc.iap2;
public class Iap2NotiMsg {
    private final Iap2ObjGroup group;
    public Iap2NotiMsg(Iap2ObjItem... items) { group = new Iap2ObjGroup(items); }
    public Iap2ObjGroup getItemGroup() { return group; }
    public static class Iap2ObjGroup {
        final Iap2ObjItem[] items;
        Iap2ObjGroup(Iap2ObjItem[] items) { this.items=items; }
        public int getItemCnt() { return items.length; }
        public Iap2ObjItem getObjItem(int n) { return items[n]; }
    }
    public static class Iap2ObjItem {
        final int id, type;
        final int[] values;
        public Iap2ObjItem(int id, int type, int... values) { this.id=id; this.type=type; this.values=values; }
        public int getItemId() { return id; }
        public int getItemParamType() { return type; }
        public int getItemObjCount() { return values.length; }
        public int[] getItemIntArray() { return values; }
        public String[] getItemStringArray() { return null; }
        public long[] getItemLongArray() { return null; }
        public Iap2ObjGroup[] getItemGroupArray() { return null; }
    }
}
''',
    'hmgapi/mods/wireless/dipo/Dipo.java': '''
package hmgapi.mods.wireless.dipo;
class Dipo { static void log(String message) {} }
''',
    'hmgapi/mods/wireless/dipo/HudReplay.java': '''
package hmgapi.mods.wireless.dipo;
import com.tcc.iap2.Iap2NotiMsg;
import com.tcc.iap2.Iap2NotiMsg.Iap2ObjItem;
import hmgapi.hook.Cluster;
public class HudReplay {
    static Iap2ObjItem i(int id, int type, int... v) { return new Iap2ObjItem(id, type, v); }
    static void check(boolean ok, String message) { if (!ok) throw new AssertionError(message); }
    public static void main(String[] args) {
        Cluster c = new Cluster();
        CpTurns h = new CpTurns(null, c, null);
        h.routeGuidance(new Iap2NotiMsg(i(0,5,1), i(1,8,1), i(13,5,5)));
        check(c.frames == 0, "no output until the selected maneuver is known");
        h.maneuver(new Iap2NotiMsg(i(0,5,1), i(1,5,6), i(3,8,1), i(5,6,700)));
        check(c.frames == 0, "unrelated maneuver");
        h.maneuver(new Iap2NotiMsg(i(0,5,1), i(1,5,5), i(3,8,1), i(11,1,-45), i(5,6,700)));
        check(c.frames == 1 && c.type == 145 && c.direction == 315 && c.roadAfterTurn, "late maneuver or HUD frame order");
        check(c.meters == 700 && c.unit == Cluster.UNIT_M, "initial maneuver distance");
        h.maneuver(new Iap2NotiMsg(i(0,5,1), i(1,5,5), i(5,6,650)));
        check(c.frames == 2 && c.direction == 315 && c.meters == 650, "partial update must retain angle");
        h.routeGuidance(new Iap2NotiMsg(i(0,5,1), i(10,6,410)));
        check(c.frames == 3 && c.meters == 410, "current route distance overrides maneuver distance");
        h.routeGuidance(new Iap2NotiMsg(i(0,5,1), i(13,5,6)));
        check(c.frames == 4 && c.meters == 700, "a new maneuver must not inherit the previous distance");
        h.routeGuidance(new Iap2NotiMsg(i(0,5,1), i(1,8,0)));
        h.maneuver(new Iap2NotiMsg(i(0,5,1), i(1,5,5), i(3,8,1), i(5,6,500)));
        check(c.frames == 4, "late maneuver repainted an inactive route");
        h.routeGuidance(new Iap2NotiMsg(i(0,5,1), i(1,8,1), i(13,5,8)));
        h.maneuver(new Iap2NotiMsg(i(0,5,1), i(1,5,8), i(3,8,2)));
        check(c.frames == 4, "missing distance must not display zero");
        h.routeGuidance(new Iap2NotiMsg(i(0,5,1), i(10,6,0)));
        check(c.frames == 5 && c.meters == 0 && c.direction == 90, "explicit zero and default right angle");
    }
}
''',
}

with tempfile.TemporaryDirectory() as folder:
    root = Path(folder)
    for name, source in STUBS.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding='utf-8')
    shutil.copyfile(sys.argv[1], root / 'hmgapi/mods/wireless/dipo/CpTurns.java')
    subprocess.run(['javac', '--release', '8', '-encoding', 'UTF-8', '-d', str(root),
                    *map(str, root.rglob('*.java'))], check=True, timeout=30)
    subprocess.run(['java', '-cp', str(root), 'hmgapi.mods.wireless.dipo.HudReplay'], check=True, timeout=15)
print('CarPlay HUD replay: late maneuver, numeric distance, angle, output order and route stop passed')
