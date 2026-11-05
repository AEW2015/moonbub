#!/usr/bin/env python3
"""Export fixed-footprint mask bytes from retained native manifest objects."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
NATIVE = ROOT / 'experiments/cu66-native-v69'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    manifest_path = NATIVE / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    assert manifest['schema'] == 'cu66-native-v69-fixtures'
    selected = {}
    for plane, axis in (('y', 0), ('cb', 1), ('cr', 2)):
        chosen = None
        for case in manifest['cases']:
            for row in case['rows']:
                entry = row['planes'][axis]
                if entry['axis'] == axis and entry['full_blocks'] in (5400, 1350):
                    chosen = entry['safe_hidden_mask']
                    break
            if chosen:
                break
        assert chosen, plane
        data = (NATIVE / chosen['path']).read_bytes()
        assert len(data) == chosen['bytes']
        assert sha(data) == chosen['sha256']
        assert set(data) <= {0, 1}
        expected_count = 5400 if plane == 'y' else 1350
        assert len(data) == expected_count
        selected[plane] = {
            'source_path': chosen['path'],
            'source_sha256': chosen['sha256'],
            'bytes': len(data),
            'hidden_blocks': data.count(1),
            'visible_blocks': data.count(0),
        }
        (HERE / f'mask_{plane}.hex').write_text(''.join(f'{b:02x}\n' for b in data))

    assert selected['y']['hidden_blocks'] == 256
    assert selected['cb']['hidden_blocks'] == selected['cr']['hidden_blocks'] == 19
    result = {
        'schema': 'cu66-expand-independent-mask-v1',
        'source_manifest': 'experiments/cu66-native-v69/manifest.json',
        'source_manifest_sha256': sha(manifest_path.read_bytes()),
        'plane_masks': selected,
        'full_blocks': {'y': 5400, 'cb': 1350, 'cr': 1350},
        'compact_blocks': {'y': 5144, 'cb': 1331, 'cr': 1331},
    }
    (HERE / 'masks.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': 'PASS', 'plane_masks': selected}, indent=2))


if __name__ == '__main__':
    main()
