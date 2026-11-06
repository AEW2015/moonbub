#!/usr/bin/env python3
"""Independent flat-plane SHA and safe COPY/equality linkage for execution models."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v82'


def main():
    spec = importlib.util.spec_from_file_location('v82_input_loader', AREA / 'native/data.py')
    native = importlib.util.module_from_spec(spec); spec.loader.exec_module(native)
    count = keys = copies = hidden = 0
    previous = None; cohort = None
    for frame in native.iter_frames():
        if cohort != frame['cohort']:
            cohort = frame['cohort']; previous = None
        digest = hashlib.sha256()
        start = 0
        for width, height in ((720, 480), (360, 240), (360, 240)):
            columns = width // 8
            for y in range(height):
                tile_y, pixel_y = divmod(y, 8)
                digest.update(b''.join(frame['tiles'][start + tile_y * columns + x][pixel_y * 8:pixel_y * 8 + 8]
                                       for x in range(columns)))
            start += columns * (height // 8)
        assert digest.hexdigest() == frame['canonical_sha256']
        same = bytes(int(previous is not None and old == tile) for old, tile in
                     zip(previous if previous is not None else [None] * 8100, frame['tiles']))
        assert same == frame['same_mask']
        if not frame['key']:
            assert same == bytes(int(c or h) for c, h in zip(frame['copy_ref_mask'], frame['hidden_mask']))
        assert all(not c or (not frame['key'] and not h and z and s)
                   for c, h, z, s in zip(frame['copy_ref_mask'], frame['hidden_mask'], frame['zero_coeff_mask'], same))
        assert all(not h or tile == bytes([128]) * 64 for h, tile in zip(frame['hidden_mask'], frame['tiles']))
        count += 1; keys += frame['key']; copies += sum(frame['copy_ref_mask']); hidden += sum(frame['hidden_mask'])
        previous = frame['tiles']
    assert (count, keys, copies, hidden) == (457, 20, 2216647, 134358)
    result = dict(schema='cu82-execution-input-verification-v1', status='PASS', sources=count,
                  keys=keys, safe_COPY_REF_tiles=copies, CONST128_tiles=hidden,
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  native_index_sha256=hashlib.sha256((AREA / 'native/index.json').read_bytes()).hexdigest(),
                  checks=['All original flat canonical plane SHA256s recomputed from actual tile bytes.',
                          'Every same_mask bit independently compared to previous accepted pixels.',
                          'On this corpus every visible equal delta tile is encoded-zero COPY eligible; no oracle-only skip is credited.',
                          'Keys do not COPY; hidden constants generated as 128.'],
                  scope='Native data linkage only; no hardware equality gate or new sender authentication.')
    (AREA / 'execution-input-verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print('V82_EXECUTION_INPUTS_PASS', count, 'frames')


if __name__ == '__main__':
    main()
