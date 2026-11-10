#!/usr/bin/env python3
"""Check/write verification-only lossless admission compilation packaging.

Does not alter the production RTL, historical packaging, or selected composition.
Default is a read-only exact check; --write creates a new manifest exclusively.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
AREA = ROOT / 'fpga/experiments/cu66-v128-padding'
PRODUCTION = AREA / 'cs88_admission_v91i2a.sv'
HISTORICAL = AREA / 'packaging.json'
MANIFEST = AREA / 'compile-packaging.json'
PRODUCTION_SHA = '75305fd64f8b1b0e092f82fed74fbc9ea8b7a2a1e538cabdf57375fee77b0c3f'
HISTORICAL_SHA = '5e57caff306bb9b39e433e3cb85d2140f1ba158b4f465a370df15b07e4cff1eb'
MODULES = ['cs88_admission_v91i2a', 'cu66_scale_tdp_v107', 'cu66_mode_store_v107']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pin(path):
    return {'path': str(path.relative_to(ROOT)), 'sha256': sha(path.read_bytes())}


def build():
    data = PRODUCTION.read_bytes()
    assert sha(data) == PRODUCTION_SHA
    assert sha(HISTORICAL.read_bytes()) == HISTORICAL_SHA
    historical = json.loads(HISTORICAL.read_text())
    assert historical['production_sha256'] == PRODUCTION_SHA
    matches = list(re.finditer(rb'^module ([A-Za-z_][A-Za-z0-9_]*)\b', data, re.M))
    assert [m.group(1).decode('ascii') for m in matches] == MODULES
    offsets = [m.start() for m in matches[1:]]
    cuts = [0] + offsets + [len(data)]
    fragments = []
    pieces = []
    for index, name in enumerate(MODULES):
        piece = data[cuts[index]:cuts[index + 1]]
        declarations = re.findall(rb'^module ([A-Za-z_][A-Za-z0-9_]*)\b', piece, re.M)
        assert declarations == [name.encode('ascii')]
        assert len(re.findall(rb'^endmodule\s*$', piece, re.M)) == 1
        if index:
            assert piece.startswith(('module ' + name + ' ').encode('ascii'))
        fragments.append({'filename': name + '.sv', 'bytes': len(piece), 'sha256': sha(piece)})
        pieces.append(piece)
    assert b''.join(pieces) == data
    return {
        'schema': 'v128-padding-lossless-admission-packaging-v1',
        'role': 'verification_only_matching_filename_compile_packaging',
        'production': str(PRODUCTION.relative_to(ROOT)),
        'production_sha256': PRODUCTION_SHA,
        'historical_packaging': pin(HISTORICAL),
        'preparer': pin(Path(__file__).resolve()),
        'fragments': fragments,
        'split_byte_offsets': offsets,
        'split_rule': 'byte offsets at exact second and third module declarations; prefix comments retained in previous fragment',
        'module_count': len(MODULES),
        'module_names': MODULES,
        'lossless_concatenation': True,
        'production_bytes_changed': False,
        'warnings_disabled': False,
    }


def verify():
    """Return the manifest Path after independently reconstructing all bytes/pins."""
    expected = build()
    assert json.loads(MANIFEST.read_text()) == expected
    return MANIFEST


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='create manifest, refusing overwrite')
    args = parser.parse_args()
    expected = build()
    if args.write:
        with MANIFEST.open('x') as stream:
            stream.write(json.dumps(expected, indent=2, sort_keys=True) + '\n')
    verified = verify()
    print(json.dumps({'status': 'PASS_LOSSLESS_COMPILE_PACKAGING', 'manifest': pin(verified),
                      'production_sha256': PRODUCTION_SHA, 'split_byte_offsets': expected['split_byte_offsets'],
                      'fragment_count': len(expected['fragments']), 'actual_RTL_run': False}, sort_keys=True))


if __name__ == '__main__':
    main()
