from pathlib import Path
import hashlib
import subprocess
import tempfile
import unittest
from test_usb_stations import SH, ENV

ROOT=Path(__file__).resolve().parents[1]
SCRIPT='\n'.join((ROOT/'bundle'/n).read_text(encoding='utf-8') for n in ('usb-mod-plan.sh','usb-audio-apply.sh'))
PLAN='''change   /system/lib/libcarplayidentity.so [wireless-carplay-aa] -> hash [restart the head unit]
change   /system/lib/libcarplaylog.so [wireless-carplay-aa] -> hash [restart the head unit]
update   /system/lib/libleafiaaac.so [wireless-carplay-aa] -> hash [restart the head unit]
event    parked -> its apps and hooks hear it [wireless-carplay-aa]
event    unparked -> its apps and hooks hear it [wireless-carplay-aa]
event    shutdown -> its apps and hooks hear it [wireless-carplay-aa]
event    wake -> its apps and hooks hear it [wireless-carplay-aa]
home Wi-Fi  off
network  no cellular [nemesis-shortcut]
network  no cellular [wireless-carplay-aa]
'''

class AudioApplyTest(unittest.TestCase):
    def run_case(self,plan=PLAN,commands='',repeat=''):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            for name in ('log','backup','payload','data/mods/wireless-carplay-aa'):(p/name).mkdir(parents=True)
            (p/'backup/mod.ours').touch();(p/'input').write_text(plan,newline='\n')
            files={'mod.json':'{"version":"2.4.11"}', 'patches.json':'{"changes":[]}',
                   'files/libleafiaaac.so':'converter', 'files/libcarplayidentity.so':'identity',
                   'files/libcarplaylog.so':'logger','META-HMGAPI/manifest.json':'signed manifest'}
            hashes=[]
            for name,content in files.items():
                f=p/'data/mods/wireless-carplay-aa'/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(content)
                hashes.append(hashlib.md5(f.read_bytes(),usedforsecurity=False).hexdigest()+'  '+name)
            (p/'payload/usb-mod-files.md5').write_text('\n'.join(hashes)+'\n',newline='\n')
            setup='''
PATH=$TEST_BIN
W="$PWD/log" BK="$PWD/backup" HMGDATA="$PWD/data" KP_HMG="$PWD/payload"
MOD_ID=wireless-carplay-aa MOD_VER=2.4.11 BID=a1111111-1111-1111-1111-111111111111 AAPROP=ap BB=bb
AP=0 PLAN_EXIT=0 APPLY_EXIT=0 INSTALLED=2.4.11
bb() { command "$@"; }
usb_target() { return 0; }
mod_ver() { echo "$INSTALLED"; }
getprop() { echo "$AP"; }
log() { echo "$*" >> "$W/messages"; }
usb_network() { echo network >> "$PWD/calls"; return 0; }
hmgapid() {
 case "$2" in
  plan) echo plan >> "$PWD/calls"; cat "$PWD/input"; return "$PLAN_EXIT" ;;
  apply) echo apply >> "$PWD/calls"; [ "$APPLY_EXIT" = 0 ] || return "$APPLY_EXIT"
   echo 'same     /system/lib/libleafiaaac.so [wireless-carplay-aa]' > "$PWD/input" ;;
 esac
}
'''
            script=setup+SCRIPT+'\n'+commands+'\nusb_audio_reconcile; echo first=$?:$USB_AUDIO_STATUS\n'+repeat
            result=subprocess.run([SH,'-s'],input=script.encode(),cwd=p,env=ENV,capture_output=True,check=True)
            self.assertFalse(result.stderr,result.stderr)
            return result.stdout.decode(),{f.relative_to(p).as_posix():f.read_text() for f in p.rglob('*') if f.is_file()}

    def test_same_version_pending_files_apply_once_and_require_reboot(self):
        out,files=self.run_case(repeat='usb_audio_reconcile; echo second=$?:$USB_AUDIO_STATUS')
        self.assertIn('first=1:applied',out);self.assertIn('second=1:applied',out)
        self.assertEqual(files['calls'].splitlines().count('apply'),1)
        self.assertIn('applied',files['backup/usb-audio-apply'])

    def test_next_boot_with_applied_files_does_not_reapply(self):
        out,files=self.run_case(repeat='BID=b2222222-2222-2222-2222-222222222222; usb_audio_reconcile; echo next=$?:$USB_AUDIO_STATUS')
        self.assertIn('next=0:none',out);self.assertEqual(files['calls'].splitlines().count('apply'),1)

    def test_foreign_unknown_restore_or_failed_plan_never_applies(self):
        for extra in ('change   /system/file [other-mod] -> hash\n','problem  failed\n','unknown new output\n',
                      'setting  prop/example = x [wireless-carplay-aa] back to stock\n'):
            out,files=self.run_case(plan=PLAN+extra)
            self.assertIn('first=2:foreign-or-unknown-plan',out);self.assertNotIn('apply',files['calls'].splitlines())
        out,files=self.run_case(commands='PLAN_EXIT=1')
        self.assertIn('first=2:',out);self.assertNotIn('apply',files['calls'].splitlines())

    def test_custom_pinned_unowned_or_corrupt_installed_files_are_preserved(self):
        for command in ('rm backup/mod.ours','touch backup/mod.pin',
                        'echo edited > data/mods/wireless-carplay-aa/patches.json',
                        'rm data/mods/wireless-carplay-aa/files/libleafiaaac.so'):
            out,files=self.run_case(commands=command)
            self.assertIn('first=2:installed-files-differ',out);self.assertNotIn('apply',files['calls'].splitlines())

    def test_disabled_older_or_other_target_is_not_changed(self):
        for command in ('touch data/mods/wireless-carplay-aa/.disabled','INSTALLED=2.4.10','usb_target() { return 1; }'):
            out,files=self.run_case(commands=command)
            self.assertIn('first=0:none',out);self.assertNotIn('calls',files)

    def test_no_audio_changes_does_not_apply_other_owned_changes(self):
        out,files=self.run_case(plan='change   /system/elsewhere [wireless-carplay-aa] -> hash\n')
        self.assertIn('first=0:none',out);self.assertNotIn('apply',files['calls'].splitlines())

    def test_active_ap_never_applies_support_libraries(self):
        out,files=self.run_case(commands='AP=1')
        self.assertIn('first=2:ap-active',out);self.assertNotIn('apply',files['calls'].splitlines())

    def test_failure_or_interrupted_apply_never_retries_in_same_boot(self):
        out,files=self.run_case(commands='APPLY_EXIT=1',repeat='usb_audio_reconcile; echo retry=$?:$USB_AUDIO_STATUS')
        self.assertIn('first=2:apply-failed',out);self.assertIn('retry=2:failed',out)
        self.assertEqual(files['calls'].splitlines().count('apply'),1)
        out,files=self.run_case(commands='echo "$BID $MOD_VER applying" > backup/usb-audio-apply')
        self.assertIn('first=2:applying',out);self.assertNotIn('calls',files)

if __name__=='__main__':unittest.main()
