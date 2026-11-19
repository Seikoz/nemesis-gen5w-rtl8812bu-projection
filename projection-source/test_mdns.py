"""Exercise the actual DNS decoder, including compressed names and hostile lengths."""
import struct
import subprocess
import sys
import unittest

BINARY = sys.argv.pop(1)

def name(s):
    return b''.join(bytes([len(x)])+x.encode() for x in s.split('.'))+b'\0'

def rr(owner,kind,data):
    return name(owner)+struct.pack('!HHIH',kind,1,120,len(data))+data

def packet(*records):
    return struct.pack('!6H',0x4b50,0x8400,0,len(records),0,0)+b''.join(records)

class MdnsTest(unittest.TestCase):
    def decode(self,data,ok=True):
        r=subprocess.run([BINARY,'--decode'],input=data,capture_output=True,timeout=3)
        self.assertEqual(r.returncode,0 if ok else 1,r.stderr)
        return r.stdout.decode()

    def test_services_ports_and_no_private_content(self):
        output=self.decode(packet(
            rr('_airplay._tcp.local',12,name('Private-Phone._airplay._tcp.local')),
            rr('Private-Phone._carplay-ctrl._tcp.local',33,struct.pack('!HHH',0,0,54861)+name('private-host.local')),
            rr('Private-Phone._airplay._tcp.local',16,b'password=SecretKey'),
        ))
        self.assertIn('service=_airplay._tcp record=PTR',output)
        self.assertIn('service=_carplay-ctrl._tcp record=SRV port=54861',output)
        for value in ('Private','private','password','SecretKey'): self.assertNotIn(value,output)

    def test_compressed_name_and_malformed_bounds(self):
        r=rr('_airplay._tcp.local',12,name('p._airplay._tcp.local'))
        compressed=b'\xc0\x0c'+struct.pack('!HHIH',33,1,120,8)+struct.pack('!HHH',0,0,5000)+b'\xc0\x0c'
        self.assertIn('port=5000',self.decode(packet(r,compressed)))
        for data in (b'',b'x'*11,packet(b'\xc0\x0c'+b'\0'*10),packet(r[:-1]),packet(b'\xff\xff'+b'\0'*10)):
            self.decode(data,False)
        for n in range(len(r)):
            self.decode(packet(r[:n]),False)

if __name__=='__main__': unittest.main()
