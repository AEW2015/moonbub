#!/usr/bin/env python3
"""Export directed and seeded control-clock vectors from the Python oracle."""
import hashlib
import json
import random
from pathlib import Path

from reference import Controller, NO_ID

HERE = Path(__file__).resolve().parent
SEED = 69004601
INPUT_FIELDS = ('rst', 'abort_i', 'drain_done', 'begin_valid', 'begin_id',
                'begin_key', 'begin_reference_id', 'commit_valid', 'commit_ok',
                'vblank', 'scanout_drained')
PRE_FIELDS = ('begin_ready', 'commit_ready')
POST_FIELDS = ('active', 'aborting', 'write_bank', 'read_bank_valid', 'read_bank',
               'ref_valid', 'ref_bank', 'ref_id', 'front_valid', 'front_bank',
               'front_id', 'pending_valid', 'pending_bank', 'pending_id',
               'begin_accepted', 'frame_committed', 'frame_presented', 'aborted',
               'error', 'error_code', 'accepted_count', 'presented_count')
HEX_FIELDS = {'begin_id', 'begin_reference_id', 'ref_id', 'front_id', 'pending_id'}


def main():
    rng = random.Random(SEED)
    dut = Controller()
    vectors = []
    labels = []

    def cycle(label='', **kwargs):
        values = dict(rst=0, abort_i=0, drain_done=0, begin_valid=0,
                      begin_id=NO_ID, begin_key=0, begin_reference_id=NO_ID,
                      commit_valid=0, commit_ok=0, vblank=0, scanout_drained=0)
        values.update(kwargs)
        pre, post = dut.step(values)
        vector = {**values, **{f'pre_{k}': v for k, v in pre.items()}, **post}
        vectors.append(vector)
        labels.append(label)
        return vector

    cycle('initial reset', rst=1)
    a = cycle('sentinel frame ID rejected', begin_valid=1, begin_id=NO_ID,
              begin_key=1, begin_reference_id=NO_ID)
    assert a['error'] and a['error_code'] == 1 and not a['active']
    a = cycle('key with non-sentinel reference rejected', begin_valid=1,
              begin_id=5, begin_key=1, begin_reference_id=0)
    assert a['error'] and a['error_code'] == 1
    a = cycle('valid key begins', begin_valid=1, begin_id=5, begin_key=1,
              begin_reference_id=NO_ID)
    assert a['begin_accepted'] and a['write_bank'] == 0 and not a['read_bank_valid']
    a = cycle('key commit', commit_valid=1, commit_ok=1)
    assert a['frame_committed'] and a['ref_bank'] == a['pending_bank'] == 0
    a = cycle('mismatched P reference rejected', begin_valid=1, begin_id=6,
              begin_key=0, begin_reference_id=4)
    assert a['error'] and a['error_code'] == 2
    a = cycle('valid P begins', begin_valid=1, begin_id=6, begin_key=0,
              begin_reference_id=5)
    assert a['begin_accepted'] and a['write_bank'] == 1 and a['read_bank_valid']
    a = cycle('commit blocked by unpresented pending frame', commit_valid=1,
              commit_ok=1)
    assert not a['pre_commit_ready'] and a['active'] and a['pending_valid']
    a = cycle('undrained vblank retains all leases', vblank=1,
              scanout_drained=0, commit_valid=1, commit_ok=1)
    assert not a['frame_presented'] and not a['frame_committed']
    a = cycle('safe swap and next commit are atomic', vblank=1,
              scanout_drained=1, commit_valid=1, commit_ok=1)
    assert a['frame_presented'] and a['frame_committed']
    assert (a['front_bank'], a['pending_bank'], a['ref_bank']) == (0, 1, 1)
    a = cycle('failed commit accepted despite full pending slot', begin_valid=1,
              begin_id=7, begin_key=0, begin_reference_id=6)
    assert a['begin_accepted'] and a['write_bank'] == 2
    a = cycle('failed commit aborts immediately', commit_valid=1, commit_ok=0)
    assert a['error'] and a['error_code'] == 4 and a['active'] and a['aborting']
    assert a['ref_id'] == 6 and a['front_id'] == 5 and a['pending_id'] == 6
    a = cycle('held abort gates begin', abort_i=1, begin_valid=1,
              begin_id=8, begin_reference_id=6)
    assert a['active'] and a['aborting'] and not a['pre_begin_ready']
    a = cycle('abort may present previously good pending frame', abort_i=1,
              vblank=1, scanout_drained=1)
    assert a['frame_presented'] and a['aborting'] and a['front_id'] == 6
    a = cycle('drain completes while abort remains asserted', abort_i=1,
              drain_done=1)
    assert a['aborted'] and not a['active'] and not a['pre_begin_ready']
    a = cycle('begin resumes after abort deasserts', begin_valid=1, begin_id=8,
              begin_key=0, begin_reference_id=6)
    assert a['begin_accepted'] and a['write_bank'] == 0
    a = cycle('candidate committed; old front kept leased', commit_valid=1,
              commit_ok=1)
    assert a['frame_committed'] and a['front_bank'] == 1 and a['ref_bank'] == 0
    a = cycle('last free bank is candidate while front reads', begin_valid=1,
              begin_id=9, begin_key=0, begin_reference_id=8)
    assert a['begin_accepted'] and a['write_bank'] == 2
    a = cycle('no fourth bank while front/reference/pending/candidate leased',
              begin_valid=1, begin_id=10, begin_reference_id=8)
    assert not a['pre_begin_ready'] and a['active']
    a = cycle('drained low retains pending and front leases', vblank=1,
              scanout_drained=0, commit_valid=1, commit_ok=1)
    assert a['active'] and a['front_id'] == 6 and a['pending_id'] == 8
    a = cycle('safe swap plus commit frees old front only after drain',
              vblank=1, scanout_drained=1, commit_valid=1, commit_ok=1)
    assert a['frame_presented'] and a['frame_committed']
    assert a['front_id'] == 8 and a['ref_id'] == a['pending_id'] == 9
    a = cycle('order and missing P reference errors', begin_valid=1,
              begin_id=9, begin_key=1, begin_reference_id=NO_ID)
    assert a['error'] and a['error_code'] == 1
    a = cycle('missing P reference errors', begin_valid=1, begin_id=10,
              begin_key=0, begin_reference_id=NO_ID)
    assert a['error'] and a['error_code'] == 2
    a = cycle('abort wins concurrent otherwise-good commit', begin_valid=1,
              begin_id=10, begin_key=0, begin_reference_id=9)
    assert a['begin_accepted']
    a = cycle('abort wins commit while good pending safely swaps', abort_i=1,
              commit_valid=1, commit_ok=1, vblank=1, scanout_drained=1)
    assert a['aborting'] and not a['frame_committed'] and a['frame_presented']
    a = cycle('abort drain frees candidate only', drain_done=1, abort_i=1)
    assert a['aborted'] and a['ref_id'] == 9 and a['front_id'] == 9
    a = cycle('reset flushes all leases', rst=1)
    assert not a['ref_valid'] and not a['front_valid'] and not a['pending_valid']
    assert a['ref_id'] == a['front_id'] == a['pending_id'] == NO_ID

    # Seeded legal/illegal traffic adds ordering, reset, queue-full and abort
    # interleavings without replacing the explicit lease-edge cases above.
    next_id = 11
    for i in range(400):
        active = dut.active
        aborting = dut.aborting
        kwargs = {}
        if i % 97 == 96:
            kwargs['rst'] = 1
        else:
            kwargs['vblank'] = int(rng.random() < 0.24)
            kwargs['scanout_drained'] = int(rng.random() < 0.55)
            if active:
                if aborting:
                    kwargs['abort_i'] = int(rng.random() < 0.7)
                    kwargs['drain_done'] = int(rng.random() < 0.35)
                elif rng.random() < 0.16:
                    kwargs['abort_i'] = 1
                elif rng.random() < 0.68:
                    kwargs['commit_valid'] = 1
                    kwargs['commit_ok'] = int(rng.random() < 0.8)
            elif rng.random() < 0.33:
                kwargs['begin_valid'] = 1
                candidate_id = next_id
                next_id += 1
                kwargs['begin_id'] = candidate_id
                if not dut.ref_valid or rng.random() < 0.28:
                    kwargs['begin_key'] = 1
                    kwargs['begin_reference_id'] = NO_ID if rng.random() < 0.9 else dut.ref_id
                else:
                    kwargs['begin_key'] = 0
                    choice = rng.random()
                    kwargs['begin_reference_id'] = (
                        dut.ref_id if choice < 0.82 else
                        (NO_ID if choice < 0.91 else max(0, dut.ref_id - 1)))
        cycle(f'seeded-{SEED}-{i}', **kwargs)

    fields = INPUT_FIELDS + tuple(f'pre_{f}' for f in PRE_FIELDS) + POST_FIELDS
    lines = []
    for vector in vectors:
        values = []
        for field in fields:
            value = vector[field]
            values.append(f'{int(value):08x}' if field in HEX_FIELDS else str(int(value)))
        lines.append(' '.join(values))
    encoded = ('\n'.join(lines) + '\n').encode()
    (HERE / 'vectors.txt').write_bytes(encoded)
    summary = {
        'schema': 'cu66-bank-v69-control-vectors-v1',
        'seed': SEED,
        'cycles': len(vectors),
        'fields': list(fields),
        'vectors_sha256': hashlib.sha256(encoded).hexdigest(),
        'source_sha256': {
            name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
            for name in ('reference.py', 'export_vectors.py')
        },
        'input_fields': list(INPUT_FIELDS),
        'pre_edge_ready_fields': list(PRE_FIELDS),
        'post_edge_fields': list(POST_FIELDS),
        'directed_cases': labels[:len(labels)-400],
        'model_scope': 'Three-bank register/lease transitions in one control clock domain only; DMA reset/isolation, CDC and physical scanout are external.',
    }
    (HERE / 'vectors.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({'cycles': len(vectors), 'seed': SEED,
                      'vectors_sha256': summary['vectors_sha256']}))


if __name__ == '__main__':
    main()
