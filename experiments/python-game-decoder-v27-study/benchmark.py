#!/usr/bin/env python3
"""Retain every MV and bit-exact frame-parse control; interleave host timing."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics
import struct
import time
import zlib
import numpy as np
import model as m
from test_model import expanded_cases, negative_cases

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def blob(data):
    packed = zlib.compress(data, 9)
    name = 'objects/'+digest(packed)+'.zlib'
    (HERE/'objects').mkdir(exist_ok=True)
    (HERE/name).write_bytes(packed)
    return dict(path=name, raw_bytes=len(data), raw_sha256=digest(data), stored_sha256=digest(packed))


def raw(desc, directory=HERE):
    packed = (directory/desc['path']).read_bytes()
    assert digest(packed) == desc['stored_sha256']
    data = zlib.decompress(packed)
    assert len(data) == desc['raw_bytes'] and digest(data) == desc['raw_sha256']
    return data


def corpus():
    for name, early in [('results.json', False), ('early-results.json', True), ('full_results.json', False)]:
        result = json.loads((m.V26/name).read_text())
        for ci, case in enumerate(result['cases']):
            for row in case['rows']:
                attempts = row['attempts'] if name == 'full_results.json' else [row]
                for ai, attempt in enumerate(attempts):
                    desc = attempt['base_packet']
                    packet = raw(desc, m.V26)
                    yield dict(group=name, case=ci, frame=row['id'], attempt=ai, early=early,
                               scene=case['scene'], input=desc), packet


def same_meta(a, b):
    assert a.keys() == b.keys()
    for key in a:
        if key in ('vectors','scale_map'):
            np.testing.assert_array_equal(a[key], b[key])
        elif key == 'coefficients':
            for left, right in zip(a[key], b[key]):
                np.testing.assert_array_equal(left, right)
        else:
            assert a[key] == b[key], key


def stat(values):
    return dict(count=len(values), median_ms=statistics.median(values), total_ms=sum(values),
                min_ms=min(values), max_ms=max(values))


def main():
    early = m.load('decoder27_early26', m.V26/'model_early_probe.py')
    records = []
    packets = []
    maps = []
    started = time.perf_counter()
    for identity, packet in corpus():
        oracle = early if identity['early'] else m.frozen
        a = oracle.parse(packet)
        b = m.replay_parse_gm26(packet, early=identity['early'])
        same_meta(a, b)
        fields = m.HEADER.unpack_from(packet)
        nq, nv = fields[-5:-3]
        data = packet[m.HEADER.size+nq:m.HEADER.size+nq+nv]
        record = dict(identity, packet_sha256=digest(packet), packet_bytes=len(packet), key=a['key'],
                      width=a['width'],height=a['height'],block_size=a['block_size'],
                      encoded_map_bytes=len(data), vector_count=a['vectors'].shape[0]*a['vectors'].shape[1],
                      vectors_int8_bytes=a['vectors'].nbytes, mode=data[0] if data else None,
                      control_vectors=blob(a['vectors'].tobytes()),
                      coefficients_sha256=digest(b''.join(v.astype('<i2').tobytes() for v in a['coefficients'])),
                      reconstructed_tag=a['reconstructed_tag'].hex(),
                      map_times_ms={'frozen': [], 'syntax': []}, frame_parse_times_ms={'frozen': [], 'syntax': []})
        records.append(record)
        packets.append((packet, oracle, identity['early']))
        if data:
            record['control_encoded_map'] = blob(data)
            mw, mh = a['vectors'].shape[1], a['vectors'].shape[0]
            _, work = oracle.pack_vectors(a['vectors'], return_work=True) if not identity['early'] else (None, {})
            record['removed_rice_axis_trials_per_parse'] = work.get('rice_axis_trials', 0)
            record['removed_rice_value_encode_trials_per_parse'] = work.get('rice_value_encode_trials', 0)
            maps.append((len(records)-1, data, mw, mh, oracle))
    print(json.dumps(dict(event='canonical_controls',frames=len(records),maps=len(maps),elapsed_s=time.perf_counter()-started)), flush=True)
    # Five rounds, cyclic corpus rotation, alternating treatment order. Each
    # individual trial measures one real packet/map, never a synthetic loop.
    rounds = 5
    for repeat in range(rounds):
        rotation = (repeat*97) % len(maps)
        ordered = maps[rotation:]+maps[:rotation]
        for order, (index, data, mw, mh, oracle) in enumerate(ordered):
            decoders = [('frozen', oracle.unpack_vectors), ('syntax', m.unpack_vectors)]
            if (repeat+order) % 2:
                decoders.reverse()
            for label, decoder in decoders:
                start = time.perf_counter_ns()
                decoder(data, mw, mh)
                records[index]['map_times_ms'][label].append((time.perf_counter_ns()-start)/1e6)
        print(json.dumps(dict(event='map_timing_round',round=repeat+1)), flush=True)
    # Frame parsing includes CRC, quant map and all coefficient entropy parsing;
    # excludes prediction, reconstruction, HUD, transport and commit work.
    for repeat in range(3):
        rotation = (repeat*73) % len(records)
        indices = list(range(rotation,len(records)))+list(range(rotation))
        for order, index in enumerate(indices):
            packet, oracle, isearly = packets[index]
            parsers = [('frozen', lambda:oracle.parse(packet)),
                       ('syntax', lambda:m.replay_parse_gm26(packet,early=isearly))]
            if (repeat+order)%2:
                parsers.reverse()
            for label, parser in parsers:
                start = time.perf_counter_ns()
                parser()
                records[index]['frame_parse_times_ms'][label].append((time.perf_counter_ns()-start)/1e6)
        print(json.dumps(dict(event='frame_parse_timing_round',round=repeat+1)), flush=True)
    negatives = [dict(name=name,data=blob(data),mw=mw,mh=mh) for name,data,mw,mh in negative_cases()]
    expanded = [dict(name=name,data=blob(data),mw=4,mh=4,vectors=blob(a.tobytes())) for name,data,a in expanded_cases()]
    paths = {HERE/'model.py',HERE/'benchmark.py',HERE/'test_model.py',m.V26/'model.py',m.V26/'model_early_probe.py'}
    paths |= {m.V26/name for name in ('results.json','early-results.json','full_results.json')}
    paths |= {m.V26/row['input']['path'] for row in records}
    # Pin all inherited model dependencies already recorded by retained v26.
    for name in ('results.json','full_results.json'):
        paths |= {ROOT/p for p in json.loads((m.V26/name).read_text())['source_sha256']}
    pins = {str(p.relative_to(ROOT)):digest(p.read_bytes()) for p in sorted(paths)}
    groups = {}
    for name in ('results.json','early-results.json','full_results.json'):
        rows = [r for r in records if r['group']==name]
        p = [r for r in rows if not r['key']]
        groups[name] = dict(frames=len(rows),maps=len(p),mode_counts=dict(Counter(r['mode'] for r in p)),
                           encoded_map_bytes=sum(r['encoded_map_bytes'] for r in p),vector_count=sum(r['vector_count'] for r in p),
                           map_parse={label:stat([statistics.median(r['map_times_ms'][label]) for r in p]) for label in ('frozen','syntax')},
                           frame_parse={label:stat([statistics.median(r['frame_parse_times_ms'][label]) for r in rows]) for label in ('frozen','syntax')},
                           removed_rice_axis_trials=sum(r.get('removed_rice_axis_trials_per_parse',0) for r in p),
                           removed_rice_value_encode_trials=sum(r.get('removed_rice_value_encode_trials_per_parse',0) for r in p))
    result = dict(schema='gamebub-decoder-v27-study',status='PASS',profile='GM27 version1 syntax-only MV acceptance',
                  source_sha256=pins,rounds=dict(map=rounds,frame_parse=3),groups=groups,
                  canonical_frames=len(records),canonical_maps=len(maps),bit_exact_vectors_and_frame_metadata=True,
                  notes=['Retained GM26/v2 main and full attempted packets; archived early/v1 modes0..3 only.',
                         'Canonical equivalence does not preserve rejection of nonminimal GM26 maps. New acceptance requires GM27 negotiation.',
                         'Timing is Python host wall time with rotated corpus and alternating treatment order.',
                         'Per-frame parsing includes full coefficient entropy parse but excludes prediction/reconstruction/transport/commit.',
                         'Rice trial removal is an algorithmic operation count, not processor instructions or DSP clocks.',
                         'Map bytes/vector storage are MV component state, not total RF or complete receiver memory.',
                         'No native DSP/FPGA timing, physical30FPS or hardware-fit claim.'],
                  records=records,negative_vectors=negatives,expanded_language_vectors=expanded)
    (HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    (HERE/'sourcepins.json').write_text(json.dumps(pins,indent=2)+'\n')
    print(json.dumps(dict(status='PASS',frames=len(records),maps=len(maps),groups=groups)),flush=True)

if __name__ == '__main__':
    main()
