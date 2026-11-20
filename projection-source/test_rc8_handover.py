"""Replay the vehicle's transport-0/SPP-loss sequence through actual patched methods."""
from pathlib import Path
import subprocess
import sys
import tempfile

def method(text, signature):
    start=text.index('    static '+signature)
    at=text.index('{',start); depth=1; end=at+1
    while depth:
        if text[end]=='{':depth+=1
        elif text[end]=='}':depth-=1
        end+=1
    return text[start:end]

s=Path(sys.argv[1]).read_text(encoding='utf-8')
signatures=(
 'synchronized void onCpSessionCreated(', 'synchronized void onCpSessionStarted(',
 'synchronized void onCpSessionFinalized(', 'boolean usbCpApCurrent(',
 'synchronized void onUsbIapConnected(', 'synchronized void startCpClient(', 'void onCpClientConnected(',
 'synchronized void onSppDown(', 'void sendDetach(', 'boolean dipoIgnoreDisconnect(',
 'void onCpIapIn(',
 'void writeCp(', 'boolean wirelessTransport(', 'void reattachCpClient(', 'void waitForUsbCpPeer(',
)
methods='\n'.join(method(s,x) for x in signatures)
harness=r'''
import java.util.*;
class Intent {
 static final int FLAG_RECEIVER_FOREGROUND=1;
 final String action; int component; String serial;
 Intent(String a){action=a;} void setPackage(String p){} void addFlags(int n){}
 void putExtra(String k,int n){component=n;} void putExtra(String k,String s){serial=s;}
}
class Context {
 void sendBroadcast(Intent i){
  if(Bridge.failBroadcast) throw new IllegalStateException("mock broadcast failure");
  if(i.action.equals(Bridge.ACTION_DETACH)){Bridge.detaches++;return;}
  if(i.component!=5) throw new AssertionError("Unexpected component");
  Bridge.attaches++;
  // The real iAP2 server stops component 4 before connecting component 5.
  Bridge.sSession=false;
  Bridge.sUsbBtConfirmed=false;
  if(!Bridge.dipoIgnoreDisconnect(4)) throw new AssertionError("Component 4 would end native CarPlay");
  if(Bridge.autoConnect) Bridge.onCpClientConnected();
 }
}
class Handler {
 ArrayDeque<Runnable> queue=new ArrayDeque<Runnable>();
 void post(Runnable r){queue.add(r);}
 void postDelayed(Runnable r,long delay){if(delay!=1200)throw new AssertionError("Unexpected grace period");post(r);}
 void runAll(){int n=0;while(!queue.isEmpty()){if(++n>10)throw new AssertionError("Unbounded jobs");queue.remove().run();}}
}
class IIap2Service {
 List<byte[]> reads=new ArrayList<byte[]>();
 void Iap2SvcTransportReadDone(byte[] b,int len){reads.add(Arrays.copyOf(b,len));}
}
class Playing {void reset(){}}
class Reattach {void sessionEnd(){} void sessionUp(){}}
class Dipo {static void rgSessionEnd(){} static void rgSessionUp(){} static void rgLinkDown(String s){}}
class CpTx {
 void reset(String why,boolean fresh){Bridge.tx.queue.clear();}
 void send(final Object cp,final byte[] data){ Bridge.tx.post(new Runnable(){public void run(){
  if(cp==Bridge.sCp && Bridge.sCpClient && Bridge.usbCpApCurrent())((NativeCp)cp).calls++;
 }});}
}
class NativeCp {int calls; public int send(byte[] b,int len){calls++;return 0;}}
class SessionStatus {
 static String state; static int raw;
 static void emit(String s,int t){state=s;raw=t;}
}
public class Bridge {
 static final String ACTION_ATTACH="attach",ACTION_DETACH="detach",IAP2_PKG="iap2";
 static final int COMPONENT_USB=1,COMPONENT_BT_CARPLAY=4,COMPONENT_CARPLAY_CLIENT=5,MAX_PENDING=64;
 static volatile boolean sUsb,sSession,sCpClient,sCpConnected,sCpWireless,sUsbBtConfirmed;
 static Object sCp,sUsbCpSession,sUsbDetachFence,sUsbApRequest,sUsbCpFallback,sUsbCpRxLogged,sUsbCpTxLogged;
 static String sCpSerial;
 static final Reattach sReattach=new Reattach();
 static final CpTx sCpTx=new CpTx();
 static boolean reattachEnabled(){return false;}
 static void txWatch(){}
 static String sAddr,sUsbCpGeneration;
 static int sUsbCpTransport,sUsbCpAttempts,attaches,detaches,ended;
 static int sCpSent,sCpFail;
 static boolean apReady,on,autoConnect,failBroadcast;
 static String generation;
 static final Handler handler=new Handler();
 static final Handler tx=new Handler();
 static final Playing NOW_PLAYING=new Playing();
 static final ArrayList<byte[]> sPendingIn=new ArrayList<byte[]>();
 static Context context;
 static IIap2Service sIap2;
 static Handler handler(){return handler;}
 static Handler cpTx(){return tx;}
 static java.lang.reflect.Method nativeSend() throws Exception {return NativeCp.class.getMethod("send",byte[].class,int.class);}
 static boolean enabled(){return on;}
 static boolean ensureHotspot(Context c){return apReady;}
 static String prop(String key,String fallback){return key.equals("sys.kp.cp_gen")?generation:fallback;}
 static void log(String s){} static void error(String s,Throwable t){}
 static String mask(String s){return "[mac]";}
 static void onUsbGone(){ended++;}
 static void flushPending(IIap2Service api){
  for(byte[] b:sPendingIn)api.Iap2SvcTransportReadDone(b,b.length);
  sPendingIn.clear();
 }
 METHODS
 static void check(boolean b,String why){if(!b)throw new AssertionError(why);}
 static void reset(){
  sUsb=sSession=sCpClient=sCpConnected=sCpWireless=sUsbBtConfirmed=failBroadcast=false;
  sCp=null;sUsbCpSession=null;sUsbDetachFence=new Object();sAddr=null;sUsbCpGeneration=null;
  sUsbCpTransport=-1;sUsbCpAttempts=attaches=detaches=ended=0;
  apReady=on=autoConnect=true;generation="boot-200.50-8";
  context=new Context();sIap2=new IIap2Service();handler.queue.clear();tx.queue.clear();sPendingIn.clear();
 }
 static void begin(boolean confirm){
  sSession=true;sAddr="phone-A";
  if(confirm)onUsbIapConnected(4,"phone-A");
  onCpSessionCreated(new NativeCp());
 }
 public static void main(String[]args){
  // Vehicle replay: native start(0), 1.4 s later SPP loss, component 4 -> 5.
  reset();begin(true);onCpSessionStarted(0);
  check(sCpWireless && SessionStatus.state.equals("started") && SessionStatus.raw==0,"Transport 0 lost confirmed wireless origin");
  onSppDown("phone-A");onSppDown("phone-A");
  check(!sCpClient && handler.queue.size()==1 && attaches==0,"Duplicate or premature handover");
  handler.runAll();
  check(attaches==1 && detaches==0 && sCpConnected && sCpWireless,"SPP loss detached live CarPlay");
  onCpIapIn(sCp,new byte[]{1,2,3},2);
  check(sIap2.reads.size()==1 && sIap2.reads.get(0).length==2,"CarPlay-channel iAP2 not forwarded");
  writeCp(new byte[]{8,9});tx.runAll();check(((NativeCp)sCp).calls==1,"iAP2 native output missing");
  NativeCp oldCp=(NativeCp)sCp;writeCp(new byte[]{7});
  onCpSessionFinalized(0);handler.runAll();
  tx.runAll();check(oldCp.calls==1,"Queued iAP2 output survived finalization");
  check(!sCpWireless && !sCpClient && !sCpConnected && sUsbCpSession==null && detaches==1,"Finalization did not clean up");

  for(int which=0;which<5;which++){
   reset();begin(which!=0);
   if(which==1)apReady=false;
   if(which==2)generation="another-ap";
   if(which==3)onUsbIapConnected(1,"usb-phone");
   if(which==4)on=false;
   onCpSessionStarted(0);
   check(!sCpWireless && !SessionStatus.state.equals("started"),"Unproven transport 0 became wireless");
  }
  reset();begin(true);onCpSessionStarted(7);check(!sCpWireless,"Unknown transport guessed wireless");
  reset();begin(false);onCpSessionStarted(1);check(sCpWireless,"Legacy transport 1 regressed");
  reset();begin(false);onCpSessionStarted(0);onSppDown("phone-A");handler.runAll();
  check(detaches==1 && attaches==0,"Ordinary pre-session SPP loss no longer detaches");

  // Cancel queued jobs on actual finalization, AP change, disable and wired takeover.
  for(int which=0;which<4;which++){
   reset();begin(true);onCpSessionStarted(0);onSppDown("phone-A");
   if(which==0)onCpSessionFinalized(0);
   if(which==1)generation="replugged-ap";
   if(which==2)on=false;
   if(which==3)onUsbIapConnected(1,"usb-phone");
   handler.runAll();check(attaches==0 && !sCpClient,"Stale handover executed");
  }
  reset();begin(true);onCpSessionStarted(0);onSppDown("phone-A");
  onCpSessionFinalized(0);begin(true);onCpSessionStarted(0);onSppDown("phone-A");
  handler.runAll();check(attaches==1 && detaches==0 && sCpConnected,"Old queued job ended/replaced the new session");
  onCpIapIn(oldCp,new byte[]{9},1);check(sIap2.reads.isEmpty(),"Old native owner injected data into new session");
  NativeCp current=(NativeCp)sCp;writeCp(new byte[]{9});generation="changed-ap";tx.runAll();
  check(current.calls==0,"Queued native output crossed AP generation");

  // Buffered first data is flushed only after component 5 connects.
  reset();begin(true);onCpSessionStarted(0);autoConnect=false;
  onCpIapIn(sCp,new byte[]{4,5},2);handler.runAll();
  check(attaches==1 && sPendingIn.size()==1 && sIap2.reads.isEmpty(),"First packet not buffered");
  onCpClientConnected();check(sPendingIn.isEmpty() && sIap2.reads.size()==1,"Buffered packet not flushed");
  reset();begin(true);onCpSessionStarted(0);failBroadcast=true;
  for(int i=0;i<4;i++){onSppDown("phone-A");handler.runAll();}
  check(!sCpClient && sUsbCpAttempts==2,"Failed handover stuck or retried without bound");
  reset();begin(true);onCpSessionStarted(0);onSppDown("phone-A");handler.runAll();
  reattachCpClient(1);onCpSessionFinalized(0);handler.runAll();
  check(attaches==1,"Stale upstream re-attach survived finalization");

  reset();begin(true);onCpSessionStarted(0);onSppDown("phone-A");
  onCpIapIn(sCp,new byte[]{1,2,3},3);
  check(sCpClient && sPendingIn.size()==1,"Peer packet did not start or buffer handover");
  handler.runAll();
  check(attaches==1 && sIap2.reads.size()==1,"Timer duplicated peer handover or lost the packet");
  reset();begin(true);onCpSessionStarted(1);onSppDown("phone-A");
  check(sCpClient,"Legacy transport 1 must keep immediate handover");
  handler.runAll();check(attaches==1,"Legacy transport 1 attach failed");
  System.out.println("Actual rc.8 Bridge transport-0/SPP-loss replay, iAP2 forwarding, cancellation and reconnect isolation passed");
 }
}
'''.replace('METHODS',methods)
with tempfile.TemporaryDirectory() as td:
    p=Path(td);(p/'Bridge.java').write_text(harness,encoding='utf-8')
    subprocess.run(['javac','-d',str(p),str(p/'Bridge.java')],check=True)
    subprocess.run(['java','-cp',str(p),'Bridge'],check=True,timeout=15)
