#!/usr/bin/env python3
"""Qualify the V91 reader on frozen BR88 chunks; paired host timings only."""
from array import array
import datetime
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import random
import statistics
import struct
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v91'
SELECTED = {(0, 0), (0, 1), (0, 3), (3, 50)}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def packed(values):
    # Explicit portable little-endian signed-int16 wire identity.
    return struct.pack('<' + str(len(values)) + 'h', *values)


def distribution(values):
    ordered = sorted(values)
    return dict(count=len(values), min=min(values), median=statistics.median(values),
                p95=ordered[min(len(ordered)-1, int(.95*len(ordered)))],
                p99=ordered[min(len(ordered)-1, int(.99*len(ordered)))],
                max=max(values), total=sum(values))


def main():
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    attempt = AREA / 'attempts' / (stamp + '-' + uuid.uuid4().hex[:8])
    attempt.mkdir(parents=True)
    old_area = ROOT / 'experiments/python-gamebub-v88/entropy'
    native_area = ROOT / 'experiments/python-gamebub-v82/native'
    old_index = json.loads((old_area / 'index.json').read_text())
    sources = [Path(__file__).resolve(), AREA/'parser.py', old_area/'codec.py',
               old_area/'data.py', old_area/'index.json',
               ROOT/'experiments/python-gamebub-v85/residual/data.py',
               ROOT/'experiments/python-gamebub-v85/residual/index.json',
               native_area/'data.py', native_area/'index.json']
    pins = {str(p.relative_to(ROOT)): sha(p) for p in sources}
    for p in (AREA/'parser.py', Path(__file__).resolve()):
        (attempt/p.name).write_bytes(p.read_bytes())
    frozen = load('v91_frozen_reader', old_area/'codec.py')
    word = load('v91_word_reader', AREA/'parser.py')
    corpus = load('v91_frozen_br88_data', old_area/'data.py')
    native = load('v91_frozen_tiles', native_area/'data.py')
    records, bench, seen = [], [], set()
    totals = {k:0 for k in word.COUNTERS}
    counts = dict(frames=0, chunks=0, coefficient_values=0, chunk_bytes=0)
    start = time.monotonic()
    status = dict(schema='cu66-v91-corpus-v1', status='FAIL', source_sha256=pins,
                  parent_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip())
    try:
        with gzip.open(attempt/'frames.jsonl.gz', 'wt') as output:
            for frame, original in zip(corpus.iter_frames(), native.iter_frames(), strict=True):
                identity=(frame['cohort'], frame['fid'])
                assert identity not in seen
                seen.add(identity)
                for key in ('cohort','fid','ordinal','key','canonical_sha256','hud_sha256','display_sha256'):
                    assert frame[key] == original[key], (identity,key)
                assert frame['zero_mask'] == ''.join(str(v) for v in original['zero_coeff_mask'])
                frame_hash = hashlib.sha256()
                frame_stats = {k:0 for k in word.COUNTERS}
                chunk_rows=[]
                offset=0
                for axis, plane_count in enumerate((5400,1350,1350)):
                    indices=[offset+t for t in range(plane_count)
                             if not original['hidden_mask'][offset+t]
                             and (frame['key'] or frame['zero_mask'][offset+t]=='0')]
                    tile_coefficients={}
                    cursor=0
                    for chunk_id, chunk in enumerate(frame['variants']['65536'][axis]):
                        packet, blocks=chunk['br88'],chunk['blocks']
                        assert hashlib.sha256(packet).hexdigest()==chunk['br88_sha256']
                        decoded=frozen.decode(packet,blocks)
                        observed={}
                        got=word.decode(packet,blocks,stats=observed)
                        assert got==decoded,(identity,axis,chunk_id,'vector')
                        raw=packed(got)
                        assert hashlib.sha256(raw).hexdigest()==chunk['coefficient_sha256']
                        assert observed['logical_bits']==sum(chunk['br88_bits'])
                        assert observed['symbols']==sum(chunk['rice_values'])
                        assert observed['prefix_queries']==observed['symbols']==observed['suffix_extracts']
                        assert observed['max_reservoir_bits']<=63
                        for key in totals:
                            if key=='max_reservoir_bits':
                                totals[key]=max(totals[key],observed[key])
                                frame_stats[key]=max(frame_stats[key],observed[key])
                            else:
                                totals[key]+=observed[key];frame_stats[key]+=observed[key]
                        for block in range(blocks):
                            tile_coefficients[indices[cursor]]=raw[block*128:(block+1)*128]
                            cursor+=1
                        counts['chunks']+=1;counts['coefficient_values']+=len(got);counts['chunk_bytes']+=len(packet)
                        chunk_rows.append(dict(axis=axis,chunk=chunk_id,blocks=blocks,
                                               bytes=len(packet),coefficient_sha256=chunk['coefficient_sha256'],
                                               packet_sha256=chunk['br88_sha256'], counters=observed))
                        if identity in SELECTED:
                            bench.append(dict(id=f'c{identity[0]}-f{identity[1]}-p{axis}-{chunk_id}',
                                              source=identity,packet=packet,blocks=blocks,
                                              coefficient_sha256=chunk['coefficient_sha256']))
                    assert cursor==len(indices)
                    for tile in range(offset,offset+plane_count):
                        frame_hash.update(tile_coefficients.get(tile,bytes(128)))
                    offset+=plane_count
                assert frame_hash.hexdigest()==frame['canonical_coefficients_sha256'],identity
                row=dict(cohort=identity[0],fid=identity[1],chunks=chunk_rows,
                         canonical_coefficients_sha256=frame_hash.hexdigest(),counters=frame_stats)
                output.write(json.dumps(row,separators=(',',':'))+'\n')
                records.append(row)
                counts['frames']+=1
                if counts['frames']%25==0:
                    print('V91_CORPUS_PROGRESS',counts['frames'],round(time.monotonic()-start,2),flush=True)
        assert counts==dict(frames=457,chunks=1371,coefficient_values=86444480,chunk_bytes=4805106),counts
        assert totals['logical_bits']==old_index['BR88_bit_reads']==37656819
        assert totals['symbols']==11435381
        # Same frozen in-memory packets, paired alternating measurement order;
        # file loading, hashes, output comparison and canonical scatter excluded.
        # CRC, grammar, bit parsing and coefficient-list construction included.
        rng=random.Random(910091)
        for item in bench:
            for decoder in (frozen.decode,word.decode):
                assert hashlib.sha256(packed(decoder(item['packet'],item['blocks']))).hexdigest()==item['coefficient_sha256']
        timings=[]
        for repeat in range(7):
            order=bench[:];rng.shuffle(order)
            for i,item in enumerate(order):
                variants=[('bit',frozen.decode),('word32',word.decode)]
                if (repeat+i)%2:variants.reverse()
                for label,decoder in variants:
                    t0=time.perf_counter_ns()
                    got=decoder(item['packet'],item['blocks'])
                    ns=time.perf_counter_ns()-t0
                    assert hashlib.sha256(packed(got)).hexdigest()==item['coefficient_sha256']
                    timings.append(dict(repeat=repeat,chunk=item['id'],variant=label,ns=ns))
        (attempt/'timings.json').write_text(json.dumps(timings,indent=2)+'\n')
        sums={label:[sum(r['ns'] for r in timings if r['repeat']==rep and r['variant']==label)
                     for rep in range(7)] for label in ('bit','word32')}
        status.update(status='PASS',counts=counts,counters=totals,
                      canonical_frame_hash_matches=457,chunk_hash_matches=1371,
                      cpu_benchmark=dict(selected_sources=sorted(SELECTED),chunks=len(bench),repetitions=7,
                                         samples=len(timings),seed=910091,
                                         scope='Host Python decode calls, including CRC/grammar/scatter into residual coefficient vector; excludes IO/hash/canonical-frame-scatter/transforms/HUD/transport.',
                                         total_ns_per_repeat={k:distribution(v) for k,v in sums.items()},
                                         median_bit_over_word32=statistics.median(sums['bit'])/statistics.median(sums['word32'])),
                      environment=dict(python=sys.version,platform=platform.platform(),implementation=platform.python_implementation()),
                      physical_30fps_proven=False,complete_under10ms_proven=False,
                      fpga_cycles_measured_by_this_script=False,
                      limitations=['457 related source frames only','CPU timings are not FPGA/ESP32 performance','Coefficients qualified; full reconstruction/HUD/publication not rerun here'])
        assert pins=={k:sha(ROOT/k) for k in pins},'input changed during run'
    except BaseException as exc:
        status.update(status='FAIL',failure=repr(exc))
        raise
    finally:
        status['wall_seconds']=time.monotonic()-start
        status['artifacts_sha256']={p.name:sha(p) for p in attempt.iterdir() if p.is_file()}
        (attempt/'results.json').write_text(json.dumps(status,indent=2)+'\n')
        if status['status']=='PASS':
            (AREA/'corpus-results.json').write_text(json.dumps(dict(status,selected_report=str((attempt/'results.json').relative_to(ROOT))),indent=2)+'\n')
        print('V91_CORPUS_REPORT',status['status'],attempt/'results.json',flush=True)


if __name__=='__main__':main()
