"""Execute the real callback record writer with Android property stubs on Linux CI."""
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as td:
    p=Path(td)
    files={
        'hmgapi/mods/wireless/dipo/SessionStatus.java':(ROOT/'SessionStatus.java').read_text(),
        'android/os/Process.java':'''package android.os;
public class Process {public static int myPid(){return (int)ProcessHandle.current().pid();}}''',
        'android/os/SystemClock.java':'''package android.os;
public class SystemClock {public static long elapsedRealtime(){return 123456;}}''',
        'android/os/Handler.java':'''package android.os;
public class Handler {
 public java.util.ArrayDeque<Runnable> queue=new java.util.ArrayDeque<Runnable>();
 public void postDelayed(Runnable r,long delay){if(delay!=15000) throw new AssertionError(); queue.add(r);}
}''',
        'android/os/SystemProperties.java':'''package android.os;
public class SystemProperties {
 public static String value,gen="12345678-100.10-8"; public static boolean fail;
 public static String get(String k,String v){return gen;}
 public static void set(String k,String v){if(fail) throw new SecurityException(); value=v;}
}''',
        'hmgapi/mods/wireless/dipo/Bridge.java':'''package hmgapi.mods.wireless.dipo;
public class Bridge {
 static android.os.Handler h=new android.os.Handler();
 static android.os.Handler handler(){return h;}
 static java.util.List<String> lines=new java.util.ArrayList<String>();
 static void log(String v){lines.add(v);}
 public static void main(String[] args){
  SessionStatus.emit("created",-1);
  String[] fields=android.os.SystemProperties.value.split(",");
  if(fields.length!=8 || !fields[0].equals("v1") || !fields[3].equals("12345678-100.10-8") ||
    !fields[4].equals("123456") || !fields[6].equals("created") || Long.parseLong(fields[2])<=0)
    throw new AssertionError("Bad callback record");
  SessionStatus.emit("started",0);
  if(!android.os.SystemProperties.value.endsWith(",2,started,0")) throw new AssertionError("Missing transport-0 start");
  android.os.SystemProperties.gen="new-ap-generation";
  h.queue.remove().run();
  if(!android.os.SystemProperties.value.contains(",12345678-100.10-8,") ||
      !android.os.SystemProperties.value.endsWith(",3,started,0")) throw new AssertionError("Heartbeat changed AP identity/raw transport");
  android.os.SystemProperties.fail=true;
  SessionStatus.emit("finalized",1);
  int n=lines.size(); h.queue.remove().run();
  if(lines.size()!=n) throw new AssertionError("Heartbeat survived finalization");
  SessionStatus.emit("idle",-1); SessionStatus.emit("idle",-1);
  int fallback=0;
  for(String line:lines) if(line.contains("fallback required")) fallback++;
  if(fallback!=1 || !lines.get(lines.size()-1).endsWith(",6,idle,-1")) throw new AssertionError("Lost fallback event");
  System.out.println("Session status records, proc starttime and property-denied fallback passed");
 }
}''',
    }
    for n,s in files.items():
        f=p/n; f.parent.mkdir(parents=True,exist_ok=True); f.write_text(s,encoding='utf-8')
    subprocess.run(['javac','-d',str(p)]+[str(p/n) for n in files],check=True)
    subprocess.run(['java','-cp',str(p),'hmgapi.mods.wireless.dipo.Bridge'],check=True,timeout=10)
