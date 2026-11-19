"""Build a same-author wireless-mod update from the published 2.4.6 payload."""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import uuid
import zipfile

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from build_package import archive

BASE_SHA256 = '5b1a36e6652fe61aeb3ad381eff1175e9c6be167849bd07f4fc297f104f4154e'
AUTHOR = 'e0bc5813-b75d-81c3-be64-31b9b002baba'
MOD = 'wireless-carplay-aa'
VERSION = '2.4.8'


def dynamic_tcp_rules():
    """Permit negotiated peer TCP ports only on the local USB AP link."""
    return [
        {'chain': chain, direction: 'rtwlan0', 'ip': family, side: prefix,
         'proto': 'tcp', 'ports': ['1024-65535'], 'both_ways': True, 'action': 'accept'}
        for chain, direction, side in (('input', 'in', 'from'), ('output', 'out', 'to'))
        for family, prefix in ((4, '192.168.43.0/24'), (6, 'fe80::/10'))
    ]


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode()


def verify_mod(data, version=VERSION):
    with zipfile.ZipFile(io.BytesIO(data)) as package:
        names = package.namelist()
        if len(names) != len(set(names)) or package.testzip() is not None:
            raise ValueError('Duplicate or damaged mod archive entries')
        files = {name: package.read(name) for name in names}
    manifest_bytes = files.pop('META-HMGAPI/manifest.json')
    signature = base64.b64decode(files.pop('META-HMGAPI/signature'), validate=False)
    manifest = json.loads(manifest_bytes)
    mod = json.loads(files['mod.json'])
    if manifest['uuid'] != AUTHOR or manifest['id'] != MOD or manifest['version'] != version:
        raise ValueError('Unexpected wireless mod author, ID or version')
    if mod['id'] != MOD or mod['version'] != version:
        raise ValueError('Signed manifest does not match mod metadata')
    public = base64.b64decode(manifest['key'], validate=True)
    author = bytearray(hashlib.sha256(public).digest()[:16])
    author[6] = (author[6] & 0x0f) | 0x80
    author[8] = (author[8] & 0x3f) | 0x80
    if str(uuid.UUID(bytes=bytes(author))) != AUTHOR:
        raise ValueError('Signing key does not match the existing author')
    key = serialization.load_der_public_key(public)
    if not isinstance(key, ec.EllipticCurvePublicKey) or not isinstance(key.curve, ec.SECP256R1):
        raise ValueError('Expected the existing P-256 author key')
    key.verify(signature, manifest_bytes, ec.ECDSA(hashes.SHA256()))
    if manifest['files'] != {n: hashlib.sha256(b).hexdigest() for n, b in files.items()}:
        raise ValueError('Signed payload hash mismatch')
    return files, public


def build_mod(base, hooks, key_path):
    if hashlib.sha256(base).hexdigest() != BASE_SHA256:
        raise ValueError('Expected the published CN7NPE wireless mod 2.4.6')
    files, public = verify_mod(base, '2.4.6')
    with zipfile.ZipFile(io.BytesIO(hooks)) as jar:
        dex = jar.read('classes.dex')
        if (jar.testzip() is not None or not dex.startswith(b'dex\n035\0') or
                b'rtwlan0\0' not in dex or b'\x05wlan0\0' in dex or
                b'USB hotspot ready; starting Bluetooth iAP2' not in dex):
            raise ValueError('Expected Android API 19 USB AP wait hooks')
    key = serialization.load_pem_private_key(key_path.read_bytes(), None)
    if key.public_key().public_bytes(serialization.Encoding.DER,
                                     serialization.PublicFormat.SubjectPublicKeyInfo) != public:
        raise ValueError('Use the existing mod author key to preserve upgrade compatibility')
    mod = json.loads(files['mod.json'])
    mod['version'] = VERSION
    mod['network']['rules'].extend(dynamic_tcp_rules())
    files['mod.json'] = json_bytes(mod)
    files['hooks.jar'] = hooks
    manifest = json_bytes({
        'format': 1, 'id': MOD, 'version': VERSION, 'uuid': AUTHOR,
        'key': base64.b64encode(public).decode(),
        'files': {n: hashlib.sha256(b).hexdigest() for n, b in sorted(files.items())},
    })
    files['META-HMGAPI/manifest.json'] = manifest
    files['META-HMGAPI/signature'] = base64.b64encode(key.sign(manifest, ec.ECDSA(hashes.SHA256()))) + b'\n'
    result = archive(files)
    verify_mod(result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-mod', type=Path, required=True)
    parser.add_argument('--hooks', type=Path, required=True)
    parser.add_argument('--key', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    content = build_mod(args.base_mod.read_bytes(), args.hooks.read_bytes(), args.key)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(content)
    print('Built wireless mod', VERSION)
    print('SHA-256', hashlib.sha256(content).hexdigest())
