from pathlib import Path
import subprocess
import tempfile
import unittest
from test_usb_stations import SH, ENV

SCRIPT=(Path(__file__).resolve().parents[1]/'bundle/usb-connection-diagnostics.sh').read_text(encoding='utf-8')

class FirewallSnapshotTest(unittest.TestCase):
    def test_kernel_order_counters_and_ipv6_udp_scope_are_reported(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            setup=r'''
PATH=$TEST_BIN
BB=bb BB_OWN=bb HMGDATA="$PWD"
bb() { if [ "$1" = timeout ]; then shift 2; "$@"; else command "$@"; fi; }
iptables() { echo 'Chain INPUT (policy DROP 1 packets, 20 bytes)'; echo 'num pkts bytes target prot opt in out source destination'; echo '1 7 500 HMGAPI_IN all -- * * 0.0.0.0/0 0.0.0.0/0'; }
ip6tables() { cat <<'EOF'
Chain INPUT (policy DROP 0 packets, 0 bytes)
num pkts bytes target prot in out source destination
1 0 0 DROP all * * ::/0 ::/0
2 3 40 HMGAPI_IN all * * ::/0 ::/0
Chain OUTPUT (policy ACCEPT 0 packets, 0 bytes)
num pkts bytes target prot in out source destination
1 8 80 HMGAPI_OUT all * * ::/0 ::/0
Chain HMGAPI_IN (1 references)
num pkts bytes target prot in out source destination
1 5 100 ACCEPT udp rtwlan0 * fe80::/10 ::/0 udp dpt:6031
2 1 40 ACCEPT udp wlan0 * fe80::/10 ::/0 udp dpt:6031
Chain HMGAPI_OUT (1 references)
num pkts bytes target prot in out source destination
1 2 80 ACCEPT udp * rtwlan0 ::/0 fe80::/10 udp spt:6031
EOF
}
'''
            r=subprocess.run([SH,'-s'],input=(setup+SCRIPT+'\nusb_firewall_snapshot\n').encode(),env=ENV,cwd=root,capture_output=True,check=True)
            out=r.stdout.decode()
            self.assertFalse(r.stderr,r.stderr)
            self.assertIn('1 5 100 ACCEPT udp rtwlan0',out)
            self.assertIn('HMGAPI_input_jump_position=2 HMGAPI_output_jump_position=1',out)
            self.assertIn('IPv6_UDP6031_scoped_input_entries=1 output_entries=1',out)
            self.assertEqual(out.count('firewall_exit=0'),2)

if __name__=='__main__': unittest.main()
