"""Run the real rc.7 patch engine on the Avante USB mod, without SDIO hardware."""
from pathlib import Path
from io import BytesIO
from zipfile import ZipFile
import hashlib,json,os,subprocess,sys,tempfile,urllib.request

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from build_wireless_mod import rebase_files
sdk=Path(os.environ['HMGAPI_SDK'])
model=sys.argv[2].lower()
assert model in ('cn7npe','cn7pe')
product=f'{model.upper()}.KOR.0000.V039.001.260902'
onebin=f'{model}_kr'
def fetch(url,digest):
    with urllib.request.urlopen(url,timeout=60) as response:data=response.read()
    assert hashlib.sha256(data).hexdigest()==digest
    return data
base=fetch('https://github.com/Open-HMG/HMG-API/releases/download/v1.1.0-rc.7/wireless-carplay-aa-2.2.0-rc.8.zip',
           '4837efbfc1e71a7f30c65c7d914dc7d00aa788cc7ab4ea17b1a1860e6e96d4ee')
bundle=fetch('https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/releases/download/cn7npe-usb-bundle-v0.1.17/NEMESIS-CN7NPE-260902-Bundle-v0.1.17-USB.zip',
             '773ebcc1e222caddbe4497b45fa1777a7ad6f5918c0533b4f8e62c0f52dddab4')
with ZipFile(BytesIO(bundle)) as b:
    with ZipFile(BytesIO(b.read('packages/korea.projection.zip'))) as kp:
        previous=kp.read('hmgapi/wireless-carplay-aa.zip')
    with ZipFile(BytesIO(b.read('packages/hmgapi.zip'))) as core:
        points=core.read('payload/maps/points.txt')
# The USB package keeps the same HMG-API rc.7 core on both vehicles.
if model=='cn7pe':
    official=fetch('https://github.com/Open-HMG/HMG-API/releases/download/v1.1.0-rc.7/hmgapi-1.1.0-rc.7-nemesis-package.zip',
                   '16bea991f1c541acccea658f766971fac0b9d41caf34d6ca7523c9007fc41a63')
    with ZipFile(BytesIO(official)) as core:
        prefix='payload/maps/hyundai/cn7pe/kor/260902/'
        vehicle=set()
        for name in core.namelist():
            if name.startswith(prefix) and name.endswith('.json') and not name.endswith('/car.json'):
                vehicle.update(json.loads(core.read(name)))
        points=('\n'.join(sorted(vehicle))+'\n').encode()
files,_=rebase_files(base,Path(sys.argv[1]).read_bytes(),previous)
assert set(json.loads(files['mod.json'])['hooks']['points']) <= set(points.decode().splitlines())
def write(path,content):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(content.encode() if isinstance(content,str) else content)
with tempfile.TemporaryDirectory() as temporary:
    root=Path(temporary);data=root/'data/hmgapi'
    for name,content in files.items():write(data/'mods/wireless-carplay-aa'/name,content)
    write(root/'system/build.prop',f'ro.build.product={product}\n')
    write(root/'props.txt','ro.board.platform=tcc803x\nro.build.version.release=4.4.2\n')
    cfg=root/'system/onebin'/onebin/'featurexml.cfg'
    write(cfg,'-/system/etc/permissions/com.hkmc.software.wifihotspot.xml\n')
    settings={'updates':False,'other':'retained','overrides':{'allow_network':['wireless-carplay-aa']}}
    write(data/'settings/hmgapi.json',json.dumps(settings))
    before={p.relative_to(root/'system'):p.read_bytes() for p in (root/'system').rglob('*') if p.is_file()}
    def engine(command):
        env=dict(os.environ,HMGAPI_ROOT=str(root),HMGAPI_HOST='1',
                 HMGAPI_PRODUCT=product,HMGAPI_ONEBIN=onebin,
                 HMGAPI_LPATCH=str(sdk/'bin/lpatch-host'))
        env.pop('HMGAPI_TEST_ANY_CAR',None)
        r=subprocess.run(['java','-cp',str(sdk/'lib/hmgapi-engine.jar'),'hmgapi.engine.Engine',command],
                         env=env,capture_output=True,text=True,timeout=45)
        assert r.returncode==0,r.stdout+r.stderr
        assert 'left out' not in r.stdout,r.stdout
        return r.stdout
    engine('plan');engine('apply')
    assert cfg.read_text().startswith('#-/system')
    rules=(data/'state/net.rules').read_text()
    assert 'rtwlan0' in rules and 'wlan0' not in rules.replace('rtwlan0','')
    for expected in ('1024:65535','6031','40515'):assert expected in rules,(expected,rules)
    assert not (root/'sys/bus/sdio/devices/mmc1:0001:1').exists()
    for name in ('libleafiaaac.so','libcarplayidentity.so','libcarplaylog.so'):
        assert (root/'system/lib'/name).read_bytes()==files['files/'+name]
    engine('apply');engine('restore')
    after={p.relative_to(root/'system'):p.read_bytes() for p in (root/'system').rglob('*') if p.is_file()}
    assert before==after,(before.keys(),after.keys())
    assert json.loads((data/'settings/hmgapi.json').read_text())==settings
    # Real HookPlan: a checked map with the previous 351 points must load the USB
    # build; the unmodified upstream declaration must be refused on that map.
    write(root/'points.txt',points);write(root/'mod.json',files['mod.json'])
    with ZipFile(BytesIO(base)) as upstream:write(root/'upstream.json',upstream.read('mod.json'))
    write(root/'HookCheck.java',r'''
import java.nio.file.*;import java.util.*;import hmgapi.engine.*;
class HookCheck {
 public static void main(String[] a)throws Exception {
  Set<String> known=new HashSet<String>(Files.readAllLines(Paths.get(a[0])));
  Map<String,Map<String,Object>> mods=new LinkedHashMap<String,Map<String,Object>>();
  mods.put("wireless-carplay-aa",Json.object(new String(Files.readAllBytes(Paths.get(a[1])),"UTF-8")));
  if(!HookPlan.of(mods,known).refused.isEmpty())throw new AssertionError(HookPlan.of(mods,known).refused);
  mods.put("wireless-carplay-aa",Json.object(new String(Files.readAllBytes(Paths.get(a[2])),"UTF-8")));
  if(HookPlan.of(mods,known).refused.isEmpty())throw new AssertionError("Unmapped upstream hooks accepted");
  System.out.println("Actual HookPlan accepts USB hooks and refuses unmodified rc.8 on the vehicle fixture");
 }
}''')
    subprocess.run(['javac','--release','8','-cp',str(sdk/'lib/hmgapi-engine.jar'),'-d',str(root),str(root/'HookCheck.java')],check=True)
    subprocess.run(['java','-cp',str(root)+os.pathsep+str(sdk/'lib/hmgapi-engine.jar'),'HookCheck',
                    str(root/'points.txt'),str(root/'mod.json'),str(root/'upstream.json')],check=True)
print(f'Actual rc.7 engine: {model.upper()} KOR USB plan/apply/reapply/byte-exact restore, native files, scoped rules and no-SDIO checks passed')
