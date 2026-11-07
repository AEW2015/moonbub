#!/usr/bin/env python3
"""Finite pinned all457-frame accepted-reference V96 inventory campaign."""
import argparse
import collections
import datetime
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import signal
import struct
import subprocess
import sys
import time
import uuid

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v96/inventory'
NATIVE=ROOT/'experiments/python-gamebub-v82/native'


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--timeout',type=int,default=900)
    args=parser.parse_args()
    if not 30<=args.timeout<=3600:
        raise ValueError('finite timeout 30..3600 seconds')
    out=AREA/'attempts'/(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    index=json.loads((NATIVE/'index.json').read_text())
    sources=[Path(__file__).resolve(),AREA/'model.py',AREA/'test_model.py',NATIVE/'data.py',NATIVE/'index.json',
             ROOT/'fpga/experiments/cu66-v91l-tiled/row_to_sdram.sv',ROOT/'docs/gamebub-v91-v110-development-plan.md',
             ROOT/'docs/literature-review-2026-11-06/experiments.md']
    pins={str(p.relative_to(ROOT)):sha(p) for p in sources}
    inputs={str((NATIVE/c['path']).relative_to(ROOT)):sha(NATIVE/c['path']) for c in index['chunks']}
    for source in sources:
        target=out/'sources'/source.relative_to(ROOT)
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(source.read_bytes())
    report=dict(schema='v96-addressed-inventory-1',status='FAIL',source_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                source_sha256=pins,input_sha256=inputs,profiles=['control','cross64','cross256'],
                qualification='Exact canonical frozen V82 target experiment, not deployed CS syntax, residual pipeline, hardware service or timing evidence.',
                baseline='d856e5fa9',python=sys.version,platform=platform.platform(),hardware_tested=False,
                no_compression_claim=True,no_residual_packet_savings_estimate=True,
                bounds=dict(frames=457,tiles_per_frame=8100,slot_counts=[64,256],dictionary_slots_per_plane=True,
                            dictionary_build_scan_tiles_per_accepted_frame=8100,shard_raw_bytes=24*1024*1024,timeout_seconds=args.timeout))
    start=time.monotonic()
    archive=None
    frames_stream=None
    shards=[]
    old_signal=signal.getsignal(signal.SIGALRM)
    def expired(signum,frame):
        raise TimeoutError('finite V96 inventory watchdog')
    signal.signal(signal.SIGALRM,expired)
    signal.alarm(args.timeout)
    try:
        model=load('v96_inventory_model',AREA/'model.py')
        native=load('v96_inventory_native',NATIVE/'data.py')
        tests=load('v96_inventory_tests',AREA/'test_model.py')
        report['tests']=tests.run()
        totals={p:collections.Counter() for p in model.PROFILES}
        cohort_totals=collections.defaultdict(collections.Counter)
        cohort=None
        accepted=None
        accepted_bank=None
        dictionaries={}
        nframes=0
        shard_raw=0
        shard_frames=0
        def close_shard():
            nonlocal archive
            if archive is not None:
                archive.close()
                path=out/shard_name
                shards.append(dict(path=shard_name,raw_bytes=shard_raw,frames=shard_frames,raw_sha256=shard_hash.hexdigest(),gzip_sha256=sha(path),gzip_bytes=path.stat().st_size))
                archive=None
        frames_stream=gzip.open(out/'frames.jsonl.gz','wt',compresslevel=6)
        for frame in native.iter_frames():
            if frame['cohort']!=cohort:
                cohort=frame['cohort']
                accepted=None
                accepted_bank=None
                dictionaries={}
            if accepted:
                assert frame['previous_fid']==accepted['fid']
            dst_bank=0 if accepted_bank is None else (accepted_bank+1)%3
            assert model.raster_digest(frame['tiles'])==frame['canonical_sha256']
            same=sum(not frame['hidden_mask'][i] and not frame['copy_ref_mask'][i] and accepted is not None and tile==accepted['tiles'][i]
                     for i,tile in enumerate(frame['tiles']))
            opportunity=0
            if accepted and not frame['key']:
                for plane,(begin,count) in enumerate(zip(model.STARTS,model.COUNTS)):
                    exact={}
                    for pos in range(count):
                        value=accepted['tiles'][begin+pos]
                        prior=exact.setdefault(value,[])
                        if len(prior)<2:
                            prior.append(pos)
                    for pos in range(count):
                        tile=begin+pos
                        if not frame['hidden_mask'][tile] and not frame['copy_ref_mask'][tile]:
                            opportunity+=any(src!=pos for src in exact.get(frame['tiles'][tile],()))
            row={k:frame[k] for k in ('cohort','ordinal','fid','refid','key','previous_fid','canonical_sha256')}
            row.update(destination_bank=dst_bank,accepted_reference_bank=accepted_bank,
                       hidden_const128=sum(frame['hidden_mask']),sameposition_copy=sum(frame['copy_ref_mask']),
                       nonCOPY_exact_sameposition=same,unbounded_crossposition_opportunities_diagnostic_only=opportunity,
                       profiles={})
            packets=[]
            for profile,slots in model.PROFILES.items():
                packet,stats=model.encode(frame,accepted,profile,dst_bank,accepted_bank,dictionaries.get(profile))
                parsed,tiles=model.materialize(packet,accepted)
                assert tiles==frame['tiles']
                stats['tile_major_sha256']=hashlib.sha256(b''.join(tiles)).hexdigest()
                stats['stream_sha256']=hashlib.sha256(packet).hexdigest()
                stats['dictionary_occupancy_before']=[len(d) for d in dictionaries.get(profile,[{}, {}, {}])]
                stats['dictionary_source_scan_tiles_before']=8100 if accepted and slots else 0
                stats['dictionary_search_available']=bool(accepted and not frame['key'] and slots)
                # Separate retained predictor-volume accounting. This is not
                # measured service and is not the literal materialization fence.
                visible=8100-sum(frame['hidden_mask'])
                retained_reads=visible*64 if accepted and not frame['key'] else 0
                stats['retained_reconstruction_predictor_accounting']=dict(
                    scope='Retained delta path reads accepted sameposition64B per visible tile. CROSSCOPY replaces prediction source read; no read-volume saving inferred. Excludes entropy, transform, hashing, HUD and scanout.',
                    reference_read_bytes=retained_reads,reference_read_words16=retained_reads//2,
                    canonical_destination_write_bytes=518400,
                    avoided_residual_tiles_proxy_only=stats['ops']['CROSSCOPY'])
                row['profiles'][profile]=stats
                for key in ('stream_bytes','header_bytes','descriptor_bytes','fallback_bytes','search_queries','search_hits','candidate_slots_inspected_upper_bound','exact_tile_comparison_budget_bytes'):
                    totals[profile][key]+=stats[key]
                for op,count in stats['ops'].items():
                    totals[profile][op]+=count
                for key,value in stats['materialization_fence'].items():
                    if isinstance(value,int):
                        totals[profile]['materialization_'+key]+=value
                totals[profile]['retained_predictor_read_bytes']+=retained_reads
                totals[profile]['retained_predictor_read_words16']+=retained_reads//2
                packets.append(packet)
            meta=json.dumps(row,separators=(',',':')).encode()
            record=struct.pack('<I',len(meta))+meta+b''.join(struct.pack('<I',len(p))+p for p in packets)
            if archive is not None and shard_raw+len(record)>24*1024*1024:
                close_shard()
            if archive is None:
                shard_name='records-'+str(len(shards)).zfill(3)+'.bin.gz'
                archive=gzip.open(out/shard_name,'wb',compresslevel=6)
                shard_raw=shard_frames=0
                shard_hash=hashlib.sha256()
            archive.write(record)
            shard_hash.update(record)
            shard_raw+=len(record)
            shard_frames+=1
            frames_stream.write(json.dumps(row,separators=(',',':'))+'\n')
            cohort_totals[cohort].update(frames=1,hidden_const128=row['hidden_const128'],sameposition_copy=row['sameposition_copy'],nonCOPY_exact_sameposition=same,unbounded_crossposition_opportunities_diagnostic_only=opportunity)
            # The only update point: after every stream parsed, all exact tiles
            # and canonical SHA verified. No provisional/current-frame entry.
            accepted=frame
            accepted_bank=dst_bank
            dictionaries={p:model.dictionaries(frame['tiles'],slots) for p,slots in model.PROFILES.items()}
            nframes+=1
            if nframes==1 or nframes%25==0:
                print('V96_INVENTORY_PROGRESS',nframes,round(time.monotonic()-start,1),flush=True)
        close_shard()
        frames_stream.close()
        assert nframes==457
        assert pins=={name:sha(ROOT/name) for name in pins}
        assert inputs=={name:sha(ROOT/name) for name in inputs}
        report.update(status='PASS_ALL457_EXACT_ADDRESSED_STREAMS',frames=nframes,canonical_sha_matches=1371,
                      exact_tile_matches=457*3*8100,cohorts=dict(cohort_totals),totals=totals,shards=shards,
                      replay_command='python3 scripts/cu66-v96/inventory.py --timeout 900',
                      artifact_format='records shards: <I JSONlength + frameJSON; then3*(<I streamlength + exact research stream) in control,cross64,cross256 order',
                      source_scan_policy='Each accepted frame builds dictionaries by exact ascending8100-tile scan; final accepted dictionaries built but not queried. Diagnostic unbounded opportunities are separate and never select copies.',
                      limitations=['Frozen canonical fallback payload is fixture input, not a deployed entropy/residual packet.',
                                   'Materialization read/write fence excludes residual predictor reads; retained predictor-volume estimate is separate.',
                                   'CONST128 generated at candidate materialization writes all64B; display-generator service owned separately.',
                                   'No hardware timing, refresh/arbitration, fullpath latency, rawcapture or compression claim.',
                                   'Corpus sequential accepted frames; abort/replay ownership stress is a separate harness.'])
    except BaseException as error:
        report['failure']=repr(error)
        raise
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM,old_signal)
        if archive is not None:
            archive.close()
        if frames_stream is not None and not frames_stream.closed:
            frames_stream.close()
        report['wall_seconds']=time.monotonic()-start
        report['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()}
        (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        print('V96_INVENTORY_REPORT',report['status'],out/'results.json',flush=True)
    (AREA/'index.json').write_text(json.dumps(dict(selected_report=str((out/'results.json').relative_to(ROOT)),report_sha256=sha(out/'results.json')),indent=2)+'\n')


if __name__=='__main__':
    main()
