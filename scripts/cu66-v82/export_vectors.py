#!/usr/bin/env python3
"""Export exact compact TREE-2 message bytes for a future independent RTL port."""
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v82'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result


def main():
    native = module('vector_native', AREA / 'native/data.py')
    codec = module('vector_commitment', ROOT / 'scripts/cu66-v82/prototype_commitment.py')
    frames = list(itertools.islice(native.iter_frames(), 2))
    tree = codec.CommitmentTree(granularity=16)
    vectors = []
    def add(name, message, expected, **metadata):
        digest = hashlib.sha256(message).digest()
        assert digest == expected
        vectors.append(dict(name=name, message_hex=message.hex(), bytes=len(message),
                            SHA256=digest.hex(), compression_blocks=(len(message)+9+63)//64,
                            **metadata))
    for ordinal, original in enumerate(frames):
        frame = dict(original, generation=ordinal + 1)
        plan = tree.plan(frame, frame['copy_ref_mask'])
        full = tree.full(frame)
        assert (plan['root'], plan['seal']) == (full['root'], full['seal'])
        f = plan['frame']
        if ordinal == 0:
            add('profile_context', tree.header, tree.profile_context)
            add('key_leaf0', tree._leaf_message(0, f['tiles']), plan['nodes'][tree.L])
            i = tree.leaf_count
            add('key_empty_first', tree._empty_message(i), plan['nodes'][tree.L+i], padded_leaf_index=i)
            add('key_internal_bottom0', tree._internal_message(1, 0, plan['nodes'][tree.L], plan['nodes'][tree.L+1]), plan['nodes'][tree.L//2])
            add('key_root', tree._internal_message(tree.L.bit_length()-1, 0, plan['nodes'][2], plan['nodes'][3]), plan['root'])
        else:
            mixed = next(g for g in plan['recomputed_groups'] if g['copied_tiles'] and len(g['copied_tiles']) < g['count'])
            i = mixed['leaf']
            add('delta_mixed_leaf', tree._leaf_message(i, f['tiles']), plan['nodes'][tree.L+i],
                plane=mixed['plane'], start=mixed['start'], count=mixed['count'],
                copied_tile_indices=mixed['copied_tiles'], previous_digest=tree.nodes[tree.L+i].hex())
        add(('key' if ordinal == 0 else 'delta') + '_frame_seal',
            tree._seal_message(f, plan['previous_root'], plan['root']), plan['seal'],
            fid=f['fid'], generation=f['generation'], content_root=plan['root'].hex())
        tree.commit(plan)
    paths = [Path(__file__).resolve(), ROOT/'scripts/cu66-v82/prototype_commitment.py', AREA/'native/data.py', AREA/'native/index.json']
    report = dict(schema='cu82-compact-message-testvectors-v1', profile=codec.PROFILE,
                  granularity=16, status='PASS',
                  source_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
                  vectors=vectors,
                  scope='Exact SHA input serialization and expected digests, not a network packet format or hardware test.')
    (AREA/'compact-message-vectors.json').write_text(json.dumps(report, indent=2)+'\n')
    print('V82_COMPACT_VECTORS_PASS', len(vectors))


if __name__ == '__main__':
    main()
