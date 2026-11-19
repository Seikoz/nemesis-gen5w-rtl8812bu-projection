import ipaddress
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build_wireless_mod import dynamic_tcp_rules, ipv6_udp_rules


def accepts(packet):
    chain, interface, peer, protocol, source, destination = packet
    for rule in dynamic_tcp_rules():
        if rule['chain'] != chain or rule['proto'] != protocol:
            continue
        direction, side = ('in', 'from') if chain == 'input' else ('out', 'to')
        if rule[direction] != interface or ipaddress.ip_address(peer) not in ipaddress.ip_network(rule[side]):
            continue
        for ports in rule['ports']:
            low, high = map(int, ports.split('-'))
            if low <= destination <= high or (rule['both_ways'] and low <= source <= high):
                return True
    return False


class TcpPolicyTest(unittest.TestCase):
    def test_observed_negotiated_ports_and_return_traffic(self):
        for packet in (
            ('input', 'rtwlan0', 'fe80::1234', 'tcp', 54861, 39818),
            ('output', 'rtwlan0', '192.168.43.2', 'tcp', 40339, 54861),
            ('output', 'rtwlan0', '192.168.43.2', 'tcp', 40343, 54861),
            ('input', 'rtwlan0', '192.168.43.2', 'tcp', 54861, 40339),
            ('output', 'rtwlan0', 'fe80::1234', 'tcp', 39818, 54861),
        ):
            with self.subTest(packet=packet): self.assertTrue(accepts(packet))

    def test_scope_is_limited_to_local_usb_ap_tcp(self):
        for packet in (
            ('input', 'wlan0', '192.168.43.2', 'tcp', 54861, 39818),
            ('output', 'rmnet0', '192.168.43.2', 'tcp', 40339, 54861),
            ('input', 'rtwlan0', '192.168.1.2', 'tcp', 54861, 39818),
            ('output', 'rtwlan0', '8.8.8.8', 'tcp', 40339, 54861),
            ('input', 'rtwlan0', '2001:db8::1', 'tcp', 54861, 39818),
            ('input', 'rtwlan0', 'fe80::1234', 'udp', 54861, 39818),
            ('input', 'rtwlan0', '192.168.43.2', 'tcp', 80, 443),
        ):
            with self.subTest(packet=packet): self.assertFalse(accepts(packet))

    def test_exact_policy_shape(self):
        rules = dynamic_tcp_rules()
        self.assertEqual(len(rules), 4)
        for rule in rules:
            self.assertEqual(rule['action'], 'accept')
            self.assertEqual(rule['ports'], ['1024-65535'])
            self.assertEqual(rule['ip'], ipaddress.ip_network(rule.get('from', rule.get('to'))).version)

    def test_ipv6_udp_6031_is_scoped_to_the_usb_link(self):
        rules=ipv6_udp_rules()
        self.assertEqual(len(rules),2)
        for rule in rules:
            self.assertEqual(rule['ip'],6)
            self.assertEqual(rule['proto'],'udp')
            self.assertEqual(rule['ports'],[6031])
            self.assertTrue(rule['both_ways'])
            self.assertEqual(rule.get('in',rule.get('out')),'rtwlan0')
            prefix=ipaddress.ip_network(rule.get('from',rule.get('to')))
            self.assertIn(ipaddress.ip_address('fe80::1234'),prefix)
            self.assertNotIn(ipaddress.ip_address('2001:db8::1'),prefix)


if __name__ == '__main__': unittest.main()
