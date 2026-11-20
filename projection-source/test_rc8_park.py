"""Exercise the rebased ParkCp's actual end/back methods with a deterministic main queue."""
from pathlib import Path
import subprocess,sys,tempfile

source=Path(sys.argv[1]).read_text(encoding='utf-8')
def method(signature):
    start=source.index('    static '+signature);at=source.index('{',start);end=at+1;depth=1
    while depth:
        if source[end]=='{':depth+=1
        elif source[end]=='}':depth-=1
        end+=1
    return source[start:end]
methods='\n'.join(method(s) for s in ('void end(', 'void back('))
harness=r'''
import java.util.*;
class ModContext {void log(String s){} void error(String s,Throwable t){throw new AssertionError(t);}}
class Handler {ArrayDeque<Runnable> q=new ArrayDeque<Runnable>();void postDelayed(Runnable r,long ms){q.add(r);}void next(){q.remove().run();}}
class UsbAp {static boolean parked,up;static boolean ready(){return up&&!parked;}}
class Choice {static final int CARPLAY=1;static boolean allow;static boolean allowedKind(Object r,int k){return allow;}static boolean busy(Object r){return false;}static String describe(Object r){return "test";}}
class Points {static int disconnects,advertise;static Object call(ClassLoader cl,String name,Object svc){if(name.endsWith("disconnect"))disconnects++;else advertise++;return null;}}
public class ParkCp {
 static Object service=new Object(),cr=new Object();static boolean wireless,ended;
 static void onMain(ModContext mod,Handler main,Runnable r){main.q.add(r);}
 METHODS
 static void check(boolean b,String s){if(!b)throw new AssertionError(s);}
 static void reset(){UsbAp.parked=false;UsbAp.up=true;Choice.allow=true;wireless=false;ended=false;Points.disconnects=Points.advertise=0;}
 public static void main(String[]a){
  ModContext mod=new ModContext();Handler main=new Handler();
  reset();end(mod,null,main,"parked");check(main.q.isEmpty()&&Points.disconnects==0,"Ended a wired session");
  wireless=true;end(mod,null,main,"parked");main.next();check(ended&&Points.disconnects==1,"Wireless park did not disconnect");
  wireless=false;UsbAp.up=false;back(mod,null,main,"wake",8000);main.next();
  check(Points.advertise==0&&main.q.size()==1,"Advertised before USB AP ready");
  UsbAp.up=true;main.next();check(Points.advertise==1&&!ended,"No advertisement after USB AP ready");
  reset();ended=true;UsbAp.up=false;back(mod,null,main,"wake",0);
  for(int i=0;i<181;i++)main.next();check(main.q.isEmpty()&&Points.advertise==0,"Wake wait unbounded");
  reset();ended=true;back(mod,null,main,"wake",8000);UsbAp.parked=true;main.next();
  check(main.q.isEmpty()&&Points.advertise==0,"Old wake advertised after parking again");
  reset();ended=true;Choice.allow=false;back(mod,null,main,"wake",0);main.next();check(Points.advertise==0,"Advertised over a chosen other phone");
  reset();ended=true;wireless=true;back(mod,null,main,"wake",0);main.next();check(Points.advertise==0,"Duplicated automatic reconnect");
  System.out.println("Actual rc.8 USB ParkCp park/wake, AP delay, timeout and stale wake checks passed");
 }
}'''.replace('METHODS',methods)
with tempfile.TemporaryDirectory() as td:
    path=Path(td);(path/'ParkCp.java').write_text(harness)
    subprocess.run(['javac','--release','8','-d',str(path),str(path/'ParkCp.java')],check=True)
    subprocess.run(['java','-cp',str(path),'ParkCp'],check=True)
