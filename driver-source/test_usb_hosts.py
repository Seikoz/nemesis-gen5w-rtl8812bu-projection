"""Run real host-restart code on sysfs fixtures with bind/unbind effects simulated."""
from pathlib import Path
import os
import subprocess
import tempfile

def write(root,**values):
    root.mkdir(parents=True,exist_ok=True)
    for name,value in values.items():(root/name).write_text(str(value)+'\n')

SOURCE=Path('driver-source/usb_reset_a3000mini.c').resolve()
with tempfile.TemporaryDirectory() as td:
    root=Path(td);devices=root/'devices';devices.mkdir();drivers=root/'drivers';drivers.mkdir()
    for driver,bus,product in [('ohci-platform',3,'0001'),('ehci-platform',4,'0002'),('tcc-ehci',1,'0002')]:
        d=drivers/driver;d.mkdir();(d/'bind').write_text('untouched');(d/'unbind').write_text('untouched')
        host=root/driver;write(host/f'usb{bus}',idVendor='1d6b',idProduct=product,maxchild=1,busnum=bus,devnum=1)
        (host/'driver').symlink_to(d);(devices/f'usb{bus}').symlink_to(host/f'usb{bus}')
    dongle=root/'ohci-platform/usb3/3-1'
    write(dongle,idVendor='0bda',idProduct='b812',authorized=1,bConfigurationValue=1,bNumInterfaces=1,devnum=2,busnum=3,speed=12)
    intf=dongle/'3-1:1.0';write(intf,bInterfaceClass='ff',bInterfaceSubClass='ff',bInterfaceProtocol='ff')
    (drivers/'rtl88x2bu').mkdir();(intf/'driver').symlink_to(drivers/'rtl88x2bu')
    (devices/'3-1').symlink_to(dongle)
    flags=root/'flags';flags.write_text('0x0\n')
    wrapper=root/'test.c'
    wrapper.write_text(r'''
#define _GNU_SOURCE
#include <unistd.h>
#include <sys/types.h>
static ssize_t fixture_write(int,const void*,size_t);
#define write fixture_write
#define main helper_main
#include "SOURCE"
#undef main
#undef write
static ssize_t fixture_write(int fd,const void *data,size_t count) {
 char fdpath[64],control[PATH_MAX],name[96],device[PATH_MAX],driver[PATH_MAX],event[128];
 snprintf(fdpath,sizeof(fdpath),"/proc/self/fd/%d",fd);
 ssize_t n=readlink(fdpath,control,sizeof(control)-1);
 if(n<0) return write(fd,data,count);
 control[n]=0;
 const char *action=strrchr(control,'/');
 if(!action || (strcmp(action+1,"bind") && strcmp(action+1,"unbind")))return write(fd,data,count);
 if(count>=sizeof(name)){errno=EINVAL;return -1;}
 memcpy(name,data,count);name[count]=0;name[strcspn(name,"\n")]=0;
 snprintf(event,sizeof(event),"%s:%s",action+1,name);
 const char *fail=getenv("FAIL_HOST_ACTION");
 if(fail && !strcmp(event,fail)){errno=EIO;return -1;}
 ssize_t result=write(fd,data,count);
 if(result!=(ssize_t)count)return result;
 const char *base=getenv("HOST_FIXTURE");
 snprintf(device,sizeof(device),"%s/%s/driver",base,name);
 snprintf(driver,sizeof(driver),"%s/drivers/%s",base,name);
 if(!strcmp(action+1,"unbind")) {if(unlink(device))return -1;}
 else {if(symlink(driver,device))return -1;}
 const char *signal_at=getenv("SIGNAL_HOST_ACTION");
 if(signal_at && !strcmp(event,signal_at))raise(SIGTERM);
 return result;
}
int main(int argc,char **argv){return helper_main(argc,argv);}
'''.replace('"SOURCE"','"'+str(SOURCE)+'"'),encoding='utf-8')
    binary=root/'usb-hosts'
    subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-Os','-DUSB_HOST_TEST_NO_DELAY',
        f'-DUSB_SYSFS="{devices}"',f'-DUSB_NET_FLAGS="{flags}"',str(wrapper),'-o',str(binary)],check=True)

    def reset():
        for name in ['ohci-platform','ehci-platform','tcc-ehci']:
            link=root/name/'driver'
            if not link.exists():link.symlink_to(drivers/name)
            for action in ['bind','unbind']:(drivers/name/action).write_text('untouched')
        flags.write_text('0x0\n')

    def invoke(ok=False,env=None,port='3-1'):
        result=subprocess.run([str(binary),'--restart-hosts',str(devices/port)],
            env=dict(os.environ,HOST_FIXTURE=str(root),**(env or {})),capture_output=True,text=True,timeout=5)
        assert (result.returncode==0)==ok,result
        assert (drivers/'tcc-ehci/bind').read_text()=='untouched'
        assert (drivers/'tcc-ehci/unbind').read_text()=='untouched'
        if ok:
            assert result.stdout.index('restore ehci-platform')<result.stdout.index('restore ohci-platform'),result
            assert (root/'ehci-platform/driver').is_symlink() and (root/'ohci-platform/driver').is_symlink()
        return result

    reset();invoke(True)
    for attribute,value,original in [('idProduct','1234','b812'),('authorized','0','1'),('speed','480','12'),('bNumInterfaces','2','1')]:
        reset();(dongle/attribute).write_text(value+'\n');invoke()
        assert (drivers/'ohci-platform/unbind').read_text()=='untouched'
        (dongle/attribute).write_text(original+'\n')
    for value in ['0x1','unreadable']:
        reset();flags.write_text(value+'\n');invoke();assert (drivers/'ohci-platform/unbind').read_text()=='untouched'
    reset();(intf/'bInterfaceClass').write_text('08\n');invoke();(intf/'bInterfaceClass').write_text('ff\n')
    reset();busy=root/'ehci-platform/usb4/4-1';write(busy,idVendor='0781',idProduct='5567');invoke();
    (busy/'idVendor').unlink();(busy/'idProduct').unlink();busy.rmdir()
    reset();extra=root/'ohci-platform/usb3/3-2';write(extra,idVendor='0781',idProduct='5567');invoke()
    (extra/'idVendor').unlink();(extra/'idProduct').unlink();extra.rmdir()
    reset();(drivers/'ehci-platform/bind').unlink();invoke();assert (drivers/'ohci-platform/unbind').read_text()=='untouched'
    (drivers/'ehci-platform/bind').write_text('untouched')
    reset();(devices/'3-1.2').symlink_to(dongle);invoke(port='3-1.2');(devices/'3-1.2').unlink()

    # Failed unbind/rebind and interruption must still attempt both required restorations.
    for action in ['unbind:ohci-platform','unbind:ehci-platform','bind:ehci-platform']:
        reset();r=invoke(env={'FAIL_HOST_ACTION':action})
        assert (root/'ohci-platform/driver').is_symlink(),r
        if action!='bind:ehci-platform':assert (root/'ehci-platform/driver').is_symlink(),r
        else:
            assert 'restore ehci-platform' in r.stdout and 'restore ohci-platform' in r.stdout
        reset()
    reset();invoke(env={'SIGNAL_HOST_ACTION':'unbind:ehci-platform'})
    assert (root/'ehci-platform/driver').is_symlink() and (root/'ohci-platform/driver').is_symlink()
    reset();extra=root/'extra-ehci/usb5';write(extra,idVendor='1d6b',idProduct='0002',maxchild=1,busnum=5,devnum=1)
    (extra.parent/'driver').symlink_to(drivers/'ehci-platform');(devices/'usb5').symlink_to(extra)
    invoke();assert (drivers/'ohci-platform/unbind').read_text()=='untouched'

print('Verified real external-host restart ordering, scope rejection, internal-host preservation, failure cleanup and SIGTERM restoration.')
