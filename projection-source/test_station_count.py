"""Exercise the actual native client against a mock Unix hostapd endpoint."""
from pathlib import Path
import socket
import subprocess
import tempfile
import threading
import time

SOURCE = Path(__file__).with_name('ap_station_count.c')
MAC = '02:11:22:33:44:55'

with tempfile.TemporaryDirectory(prefix='kp-sta-') as td:
    root = Path(td)
    control = root/'ctrl'
    binary = root/'count'
    subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                    f'-DCONTROL_PATH="{control}"', str(SOURCE), '-o', str(binary)], check=True)

    def run(replies, expected, output):
        server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        server.bind(str(control))
        server.settimeout(2)
        commands = []
        errors = []
        def serve():
            try:
                for reply in replies:
                    command, addr = server.recvfrom(256)
                    commands.append(command.decode())
                    if reply is not None:
                        server.sendto(reply, addr)
            except Exception as exc:
                errors.append(exc)
        thread = threading.Thread(target=serve)
        thread.start()
        start = time.monotonic()
        result = subprocess.run([str(binary)], capture_output=True, timeout=3)
        thread.join(3)
        server.close()
        control.unlink()
        assert not errors, errors
        assert result.returncode == expected and result.stdout == output, result
        assert result.stderr == b''
        assert commands[0] == 'STA-FIRST'
        assert all(c == 'STA-FIRST' or c.startswith('STA-NEXT ') for c in commands)
        assert time.monotonic() - start < 2.5

    run([b'FAIL\n'], 0, b'0\n')
    run([(MAC+'\nflags=[AUTH][ASSOC][AUTHORIZED]\n').encode(), b'FAIL\n'], 0, b'1\n')
    run([(MAC+'\nflags=[AUTH][ASSOC]\n').encode(), b'FAIL\n'], 0, b'0\n')
    run([(MAC+'\nflags=[AUTH][AUTHORIZED]\n').encode(), b'FAIL\n'], 0, b'0\n')
    run([(MAC+'\ndot1xAuthAuthControlledPortStatus=1\n').encode(), b'FAIL\n'], 0, b'1\n')
    run([(MAC+'\ndot1xAuthAuthControlledPortStatus=2\n').encode(), b'FAIL\n'], 0, b'0\n')
    run([(MAC+'\nflags=[ASSOC][AUTHORIZED]\n').encode(),
         b'02:aa:bb:cc:dd:ee\nflags=[AUTH][ASSOC][AUTHORIZED]\n', b'FAIL\n'], 0, b'2\n')
    run([b'UNKNOWN COMMAND\n'], 1, b'')
    run([(MAC+'\nconnected_time=12\n').encode()], 1, b'')
    run([b'not-a-mac-address\nflags=[ASSOC][AUTHORIZED]\n'], 1, b'')
    repeated = (MAC+'\nflags=[ASSOC][AUTHORIZED]\n').encode()
    run([repeated, repeated], 1, b'')
    run([b'x'*17000], 1, b'')
    run([None], 1, b'')
    result = subprocess.run([str(binary)], capture_output=True)
    assert result.returncode != 0 and not result.stdout and not result.stderr
print('Native station counts: empty, authorized, pending, old Android MIB, multiple clients, malformed/duplicate replies, timeout and missing endpoint passed.')
