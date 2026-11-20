"""Rebase the signed RTL8812BU mod on official wireless 2.2.0-rc.8."""
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
VERSION = '2.4.17'
HYBRID_VERSION = '2.4.18'
HYBRID_OMIT = {'btsettings.projection_helper.open_wireless_page', 'dipo.carplay.disable_bluetooth'}
DISPLAY_NAME = 'HMG-API Wireless Mode'
UPSTREAM_SHA256 = '4837efbfc1e71a7f30c65c7d914dc7d00aa788cc7ab4ea17b1a1860e6e96d4ee'
UPSTREAM_AUTHOR = '7251ce71-a146-8a1e-958b-dbffc6af7359'
PREVIOUS_SHA256 = 'd434b002668558ebad10a84e6cbf12312fb3d95a9cc3e7ff1461e760819d8141'
UNMAPPED_RC4 = {
    'framework.activity.start_activity_for_result', 'gpm.receiver_service.on_create',
    'framework.pp_service.connect_pp', 'framework.pp_service.send_connect_pp_from_bt',
    'framework.pp_service.disconnect_pp', 'framework.pp_service.cancel_connection_pp',
    'framework.pp_service.on_wireless_connected', 'framework.pp_service.on_wireless_disconnected',
}


def dynamic_tcp_rules():
    """Permit negotiated peer TCP ports only on the local USB AP link."""
    return [
        {'chain': chain, direction: 'rtwlan0', 'ip': family, side: prefix,
         'proto': 'tcp', 'ports': ['1024-65535'], 'both_ways': True, 'action': 'accept'}
        for chain, direction, side in (('input', 'in', 'from'), ('output', 'out', 'to'))
        for family, prefix in ((4, '192.168.43.0/24'), (6, 'fe80::/10'))
    ]


def ipv6_udp_rules():
    """The wired CarPlay 6031 exception, limited to USB AP link-local peers."""
    return [
        {'chain': chain, direction: 'rtwlan0', 'ip': 6, side: 'fe80::/10',
         'proto': 'udp', 'ports': [6031], 'both_ways': True, 'action': 'accept'}
        for chain, direction, side in (('input', 'in', 'from'), ('output', 'out', 'to'))
    ]


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode()


def verify_mod(data, version=VERSION, author=AUTHOR):
    with zipfile.ZipFile(io.BytesIO(data)) as package:
        names = package.namelist()
        if len(names) != len(set(names)) or package.testzip() is not None:
            raise ValueError('Duplicate or damaged mod archive entries')
        files = {name: package.read(name) for name in names}
    manifest_bytes = files.pop('META-HMGAPI/manifest.json')
    signature = base64.b64decode(files.pop('META-HMGAPI/signature'), validate=False)
    manifest = json.loads(manifest_bytes)
    mod = json.loads(files['mod.json'])
    if manifest['uuid'] != author or manifest['id'] != MOD or manifest['version'] != version:
        raise ValueError('Unexpected wireless mod author, ID or version')
    if mod['id'] != MOD or mod['version'] != version:
        raise ValueError('Signed manifest does not match mod metadata')
    public = base64.b64decode(manifest['key'], validate=True)
    derived = bytearray(hashlib.sha256(public).digest()[:16])
    derived[6] = (derived[6] & 0x0f) | 0x80
    derived[8] = (derived[8] & 0x3f) | 0x80
    if str(uuid.UUID(bytes=bytes(derived))) != author:
        raise ValueError('Signing key does not match the existing author')
    key = serialization.load_der_public_key(public)
    if not isinstance(key, ec.EllipticCurvePublicKey) or not isinstance(key.curve, ec.SECP256R1):
        raise ValueError('Expected the existing P-256 author key')
    key.verify(signature, manifest_bytes, ec.ECDSA(hashes.SHA256()))
    if manifest['files'] != {n: hashlib.sha256(b).hexdigest() for n, b in files.items()}:
        raise ValueError('Signed payload hash mismatch')
    return files, public


def rebase_files(base, hooks, previous):
    if hashlib.sha256(base).hexdigest() != UPSTREAM_SHA256:
        raise ValueError('Expected official wireless 2.2.0-rc.8')
    if hashlib.sha256(previous).hexdigest() != PREVIOUS_SHA256:
        raise ValueError('Expected the verified previous USB mod 2.4.10')
    files, _ = verify_mod(base, '2.2.0-rc.8', UPSTREAM_AUTHOR)
    old_files, public = verify_mod(previous, '2.4.10')
    with zipfile.ZipFile(io.BytesIO(hooks)) as jar:
        dex = jar.read('classes.dex')
        if (jar.testzip() is not None or not dex.startswith(b'dex\n035\0') or
                b'rtwlan0\0' not in dex or b'\x05wlan0\0' in dex or
                b'USB hotspot ready; starting Bluetooth iAP2' not in dex or
                b'USB_CP_EVENT ' not in dex or b'sys.kp.cp_session' not in dex or
                b'USB_CP_HANDOVER stage=spp-down-preserved raw_transport=' not in dex or
                b'USB_CP_HANDOVER stage=first-native-send' not in dex or
                b'USB_CP_HANDOVER stage=first-peer-data' not in dex or b'UsbAp;' not in dex or b'ParkCp;' not in dex or b'CpTx;' not in dex or
                b'USB_CP_AUDIO bluetooth_handoff=stock' not in dex or b'stock_bt_handoff' not in dex):
            raise ValueError('Expected Android API 19 rc.8 USB hooks')
    mod = json.loads(files['mod.json'])
    mod['version'] = VERSION
    mod['name'] = DISPLAY_NAME
    mod['description'] = 'Official rc.8 adapted for CN7PE and CN7NPE KOR 260902 and the Korea Projection rtwlan0 AP.'
    mod['hmgapi'] = '>=1.1.0-rc.7'
    mod['system'] = [{'model': ['CN7PE', 'CN7NPE'], 'region': 'KOR', 'firmware': '260902'}]
    mod.pop('wifi')  # built-in wlan0/SDIO management must not own the USB hostapd
    mod['hooks']['points'] = {k:v for k,v in mod['hooks']['points'].items() if k not in UNMAPPED_RC4}
    mod['network'] = json.loads(old_files['mod.json'])['network']
    mod['network']['rules'].append({
        'chain':'input','in':'rtwlan0','from':'192.168.43.0/24','to':'192.168.43.1',
        'ip':4,'proto':'tcp','ports':[40515],'state':['new'],'action':'accept','when':'settings.aa_firewall',
    })
    patches = json.loads(files['patches.json'])
    patches['cars'] = {'CN7NPE.KOR.': 'usb_cn7npe', 'CN7PE.KOR.': 'usb_cn7pe'}
    patches['changes'].insert(0,json.loads(old_files['patches.json'])['changes'][0])
    files['patches/usb_cn7npe/stock'] = b''
    files['patches/usb_cn7npe/expect'] = b''
    files['patches/usb_cn7pe/stock'] = b''
    files['patches/usb_cn7pe/expect'] = b''
    files['patches.json'] = json_bytes(patches)
    settings = json.loads(files['settings.json'])
    settings['settings'] = [x for x in settings['settings'] if x['key'] != 'cp_firewall']
    for entry in settings['settings']:
        if entry['key'] == 'aa_firewall': entry['default'] = True
    keys = {x['key'] for x in settings['settings']}
    for entry in json.loads(old_files['settings.json'])['settings']:
        if entry['key'] in ('aa_ap','aa_ready_resend') and entry['key'] not in keys:
            settings['settings'].append(entry)
    settings['settings'].append({
        'key': 'stock_bt_handoff',
        'type': 'toggle',
        'default': False,
        'title': 'Stock Bluetooth handoff (CarPlay audio test)',
        'description': 'CN7PE/CN7NPE KOR 260902 only. For a confirmed USB Wi-Fi CarPlay session, allow the head unit to handle the iPhone Bluetooth handoff when requested. Compare audio and connection stability. Turn off to restore the previous behavior. Takes effect after the head unit restarts.',
    })
    files['settings.json'] = json_bytes(settings)
    files['USB-SOURCE.md'] = (
        f'HMG-API USB wireless mod {VERSION} (local upgrade version), based on official 2.2.0-rc.8.\n'
        'Official source: https://github.com/Open-HMG/hmgapi-wireless-cp-aa/tree/c47c0bbf8513e725c9852acb932bdde39e3d7edc\n'
        'USB/AA source: https://github.com/StopDragon/HMG-API/tree/b573ac624e284cd7d6e0a7b9fa6c32862c528988/mods/wireless-carplay-aa\n'
        'Local patches: https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/tree/cn7npe-usb-bundle-v0.1.27/projection-source\n'
        'AGPL-3.0. Signed by the existing local author; not an unmodified official package.\n'
        'Eight hooks newer than the checked 351-point map are omitted; their consumers are not registered.\n'
    ).encode()
    files['mod.json'] = json_bytes(mod)
    files['hooks.jar'] = hooks
    return files, public


def build_mod(base, hooks, previous, key_path):
    files, public = rebase_files(base, hooks, previous)
    return sign_files(files, public, key_path)


def rename_mod(previous, key_path):
    """Update only display metadata, retaining all published executable payloads."""
    files, public = verify_mod(previous, '2.4.12')
    mod = json.loads(files['mod.json'])
    mod.update(name=DISPLAY_NAME, version=VERSION)
    files['mod.json'] = json_bytes(mod)
    return sign_files(files, public, key_path)


def hybrid_files(files, hooks):
    """Build the CN7HEVPE variant with only the available hook points."""
    with zipfile.ZipFile(io.BytesIO(hooks)) as jar:
        dex = jar.read('classes.dex')
        if (jar.testzip() is not None or not dex.startswith(b'dex\n035\0') or
                b'stage=first-native-send' not in dex or b'rtwlan0\0' not in dex or b'stock_bt_handoff' in dex or
                any(point.rsplit('.', 1)[-1].encode() in dex for point in HYBRID_OMIT)):
            raise ValueError('Expected the CN7HEVPE hooks with the two optional consumers removed')
    files = dict(files)
    files['hooks.jar'] = hooks
    mod = json.loads(files['mod.json'])
    mod['version'] = HYBRID_VERSION
    mod['description'] = 'Official rc.8 adapted for CN7HEVPE KOR 260902 and the Korea Projection rtwlan0 AP.'
    mod['system'] = [{'model': ['CN7HEVPE'], 'region': 'KOR', 'firmware': '260902'}]
    for point in HYBRID_OMIT:
        del mod['hooks']['points'][point]
    files['mod.json'] = json_bytes(mod)
    patches = json.loads(files['patches.json'])
    for patchset in patches['cars'].values():
        for name in ('stock', 'expect'):
            del files[f'patches/{patchset}/{name}']
    patches['cars'] = {'CN7HEVPE.KOR.': 'usb_cn7hevpe'}
    for name in ('stock', 'expect'):
        files[f'patches/usb_cn7hevpe/{name}'] = b''
    files['patches.json'] = json_bytes(patches)
    settings = json.loads(files['settings.json'])
    settings['settings'] = [entry for entry in settings['settings'] if entry['key'] != 'stock_bt_handoff']
    files['settings.json'] = json_bytes(settings)
    files['USB-SOURCE.md'] += (
        f'\nCN7HEVPE variant {HYBRID_VERSION}: separate hybrid patch set and hook declaration.\n'
        'Source: https://github.com/Seikoz/nemesis-rtl8812bu-gen5w/tree/cn7npe-usb-bundle-v0.1.27\n'
    ).encode()
    return files


def sign_files(files, public, key_path, version=VERSION):
    key = serialization.load_pem_private_key(key_path.read_bytes(), None)
    if key.public_key().public_bytes(serialization.Encoding.DER,
                                     serialization.PublicFormat.SubjectPublicKeyInfo) != public:
        raise ValueError('Use the existing mod author key to preserve upgrade compatibility')
    manifest = json_bytes({
        'format': 1, 'id': MOD, 'version': version, 'uuid': AUTHOR,
        'key': base64.b64encode(public).decode(),
        'files': {n: hashlib.sha256(b).hexdigest() for n, b in sorted(files.items())},
    })
    files['META-HMGAPI/manifest.json'] = manifest
    files['META-HMGAPI/signature'] = base64.b64encode(key.sign(manifest, ec.ECDSA(hashes.SHA256()))) + b'\n'
    result = archive(files)
    verify_mod(result, version)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-mod', type=Path)
    parser.add_argument('--hooks', type=Path)
    variants = parser.add_mutually_exclusive_group()
    variants.add_argument('--rename-only', action='store_true', help='Relabel the verified 2.4.12 mod without rebuilding code')
    variants.add_argument('--hybrid', action='store_true', help=f'Adapt the signed {VERSION} mod for CN7HEVPE')
    parser.add_argument('--previous-mod', type=Path, required=True)
    parser.add_argument('--key', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.hybrid:
        if args.base_mod or not args.hooks:
            parser.error('--hybrid needs --hooks, --previous-mod, --key and --output')
        files, public = verify_mod(args.previous_mod.read_bytes())
        content = sign_files(hybrid_files(files, args.hooks.read_bytes()), public, args.key, HYBRID_VERSION)
    elif args.rename_only:
        if args.base_mod or args.hooks:
            parser.error('--rename-only uses only --previous-mod, --key and --output')
        content = rename_mod(args.previous_mod.read_bytes(), args.key)
    else:
        if not args.base_mod or not args.hooks:
            parser.error('--base-mod and --hooks are required unless --rename-only is used')
        content = build_mod(args.base_mod.read_bytes(), args.hooks.read_bytes(), args.previous_mod.read_bytes(), args.key)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(content)
    print('Built wireless mod', HYBRID_VERSION if args.hybrid else VERSION)
    print('SHA-256', hashlib.sha256(content).hexdigest())
