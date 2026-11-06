#!/usr/bin/env python3
"""Independent retained full-corpus work checks and witness DAG reconstruction."""
from array import array
import argparse,gzip,hashlib,importlib.util,json,re,statistics,struct,sys,tarfile
from pathlib import Path
AREA=Path(__file__).resolve().parent;ROOT=AREA.parents[2]
FETCH={'stream_bytes','raw_bytes','header_bytes','crc_bytes'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,p):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def stats(v):return dict(min=min(v),median=statistics.median(v),max=max(v),total=sum(v))


def main():
    p=argparse.ArgumentParser();p.add_argument('--session',required=True,type=Path);p.add_argument('--verify',action='store_true');args=p.parse_args()
    path=args.session.resolve();path=path/'results.json' if path.is_dir() else path
    session=json.loads(path.read_text());assert session['status']=='PASS' and session['synthetic_checks']==len(session['synthetic'])==18
    for name,digest in session['source_sha256'].items():assert sha(ROOT/name)==digest
    native=json.loads((AREA/'index.json').read_text());assert native['native_sources']==457 and native['record_count']==914
    verified=json.loads((AREA/'verification.json').read_text());assert verified['status']=='PASS' and verified['variant_records']==914
    assert verified['index_sha256']==sha(AREA/'index.json')
    lookup={(f['cap'],f['cohort'],f['fid']):f for f in native['frames']};assert len(lookup)==914
    costs=load('cu86_audit_costs',ROOT/'scripts/cu66-v84/prototype_pipeline.py')
    rows=[];report_paths=[];witness_paths=[];by_key={};expected_counts=(119,119,119,100)
    assert [r['cohort'] for r in session['cohorts']]==list(range(4))
    source_pins=None
    for record in session['cohorts']:
        cohort=record['cohort'];assert record['exit_code']==0
        log=ROOT/record['log'];assert sha(log)==record['log_sha256']
        report_path=ROOT/record['report'];report=json.loads(report_path.read_text());report_paths.append(report_path)
        assert report['status']=='PASS_FULL_COHORT_REENCODED_FRONT_MODEL' and report['cohort']==cohort and report['full_corpus_scheduling'] is True
        assert report['limit_records']==0 and report['window']==8 and report['physical_timing_proven'] is False
        assert report['native_sources_scheduled']==expected_counts[cohort] and report['variant_records_scheduled']==2*expected_counts[cohort]
        assert report['schedules']==12*expected_counts[cohort]
        pins=report['source_sha256']
        for name,digest in pins.items():assert sha(ROOT/name)==digest
        if source_pins is None:source_pins=pins
        assert source_pins==pins
        with tarfile.open(report_path.parent/'sources.tar.gz','r:gz') as tar:
            members=tar.getmembers();assert {m.name for m in members}=={n for n in pins if not n.endswith('.gz')}
            for member in members:assert hashlib.sha256(tar.extractfile(member).read()).hexdigest()==pins[member.name]
        assert sha(report_path.parent/'sources.tar.gz')==report['source_archive_sha256']
        actual={f.name for f in report_path.parent.iterdir() if f.is_file() and f.name!='results.json'}
        assert actual==report['artifacts_sha256'].keys()
        for name,digest in report['artifacts_sha256'].items():assert sha(report_path.parent/name)==digest
        part=[json.loads(s) for s in (report_path.parent/'rows.jsonl').read_text().splitlines()]
        expected={(cap,f['cohort'],f['fid'],cost,lanes) for f in native['frames'] if f['cohort']==cohort for cap in (f['cap'],) for cost in ('LOW','HIGH') for lanes in (1,2,4)}
        assert len(part)==len(expected)
        keys=set()
        for row in part:
            key=(row['cap'],row['cohort'],row['fid'],row['cost'],row['lanes']);assert key not in keys and key in expected and key not in by_key
            keys.add(key);by_key[key]=row
            frame=lookup[key[:3]];assert row['ordinal']==frame['ordinal'] and row['key']==frame['key']
            weights=getattr(costs,row['cost']);shared=frame['shared_totals'];contexts=frame['context_totals']
            fetch=sum(v*weights[k] for k,v in shared.items() if k!='emits')+sum(sum(v*weights[k] for k,v in c.items() if k in FETCH) for c in contexts)
            compute=[sum(v*weights[k] for k,v in c.items() if k not in FETCH) for c in contexts];emit=shared['emits']*weights['emits'];lanes=row['lanes']
            assert row['resource_work_cycles']==dict(fetch=fetch,arithmetic=sum(compute),emit=emit)
            floor=max(fetch,emit,max(compute),(sum(compute)+lanes-1)//lanes)
            assert row['necessary_work_floor_cycles']==floor<=row['finish_cycles']
            assert row['model_ms']==row['finish_cycles']*1e-5 and row['window']==8 and 0<row['window_peak']<=8
            assert 0<=row['resource_peaks']['fetch']<=1 and 0<=row['resource_peaks']['emit']<=1 and 0<=row['resource_peaks']['arithmetic']<=lanes
            assert re.fullmatch('[0-9a-f]{64}',row['timeline_sha256'])
        assert keys==expected
        own_summary=[]
        for cap in (256,65536):
            for cost in ('LOW','HIGH'):
                for lanes in (1,2,4):
                    selected=[r for r in part if (r['cap'],r['cost'],r['lanes'])==(cap,cost,lanes)]
                    own_summary.append(dict(cap=cap,cost=cost,window=8,lanes=lanes,sources=len(selected),model_ms=stats([r['model_ms'] for r in selected]),conditional_front_under10ms=sum(r['finish_cycles']<1_000_000 for r in selected)))
        assert own_summary==report['summaries']
        rows+=part;witness_paths+=sorted(report_path.parent.glob('witness-*.json.gz'))
    assert len(rows)==len(by_key)==5484 and len(witness_paths)==4
    # Reconstruct the four retained corner DAGs using an independent frozen
    # constructor, not the producer's current model.build function.
    selected_frames={};raw=hashlib.sha256();count=0
    with gzip.open(AREA/native['data']['path'],'rb') as stream:
        while True:
            prefix=stream.read(4)
            if not prefix:break
            n,=struct.unpack('<I',prefix);head=stream.read(n);payload=stream.read(8100*55*4)
            assert len(head)==n and len(payload)==8100*55*4
            raw.update(prefix);raw.update(head);raw.update(payload);frame=json.loads(head);count+=1
            if frame['cohort']==3 and frame['fid']==50:
                words=array('I');words.frombytes(payload)
                if sys.byteorder!='little':words.byteswap()
                shared=[];contexts=[]
                for tile in range(8100):
                    at=tile*55;shared.append(list(words[at:at+11]));contexts.append([list(words[at+11+c*11:at+22+c*11]) for c in range(4)])
                selected_frames[frame['cap']]=dict(shared=shared,contexts=contexts)
    assert count==914 and raw.hexdigest()==native['data']['raw_sha256'] and selected_frames.keys()=={256,65536}
    constructor=load('cu86_independent_context_constructor',ROOT/'experiments/python-gamebub-v85/contexts/audit_model.py')
    generic=load('cu86_independent_context_timeline',ROOT/'experiments/python-gamebub-v83/audit.py')
    witnesses=[]
    for source in witness_paths:
        match=re.fullmatch(r'witness-cap(256|65536)-c3-f50-low-w8-l([12])\.json\.gz',source.name);assert match
        cap,lanes=map(int,match.groups())
        with gzip.open(source,'rt') as stream:w=json.load(stream)
        jobs=constructor.reconstruct(selected_frames[cap],native['fields'],costs.LOW,8);assert jobs==w['workload']['jobs']
        checked=generic.verify(jobs,w['result']['timeline'],dict(fetch=1,arithmetic=lanes,emit=1))
        row=by_key[(cap,3,50,'LOW',lanes)]
        assert checked['finish_cycles']==row['finish_cycles'] and checked['resource_work_cycles']==row['resource_work_cycles']
        timeline_hash=hashlib.sha256(json.dumps(w['result']['timeline'],sort_keys=True,separators=(',',':')).encode()).hexdigest();assert timeline_hash==row['timeline_sha256']
        witnesses.append(dict(path=str(source.relative_to(ROOT)),sha256=sha(source),jobs=len(jobs),cap=cap,lanes=lanes,independent_DAG_reconstruction=True))
    summaries=[]
    for cap in (256,65536):
        for cost in ('LOW','HIGH'):
            for lanes in (1,2,4):
                chosen=[r for r in rows if (r['cap'],r['cost'],r['lanes'])==(cap,cost,lanes)]
                assert len(chosen)==457
                summaries.append(dict(cap=cap,cost=cost,window=8,lanes=lanes,sources=457,model_ms=stats([r['model_ms'] for r in chosen]),conditional_front_under10ms=sum(r['finish_cycles']<1_000_000 for r in chosen)))
    result=dict(schema='cu66-v86-context-model-audit-v1',status='PASS',native_sources=457,variant_records=914,schedules=5484,synthetic_checks=18,
                session=str(path.relative_to(ROOT)),session_sha256=sha(path),summaries=summaries,independently_reconstructed_witnesses=witnesses,
                source_sha256={str(Path(__file__).relative_to(ROOT)):sha(Path(__file__)),str((AREA/'verification.json').relative_to(ROOT)):sha(AREA/'verification.json'),
                               **{str(p.relative_to(ROOT)):sha(p) for p in report_paths}},
                scope='Full457 actual residual streams under conditional standalone frontend model; no full decoder/RTL/FPGA/ESP32 or sustained30fps/validatedunder10ms proof.')
    dest=AREA/'model-verification.json'
    if args.verify:assert json.loads(dest.read_text())==result
    else:
        if dest.exists():raise FileExistsError(dest)
        dest.write_text(json.dumps(result,indent=2)+'\n')
    print('V86_REENCODED_CONTEXT_MODEL_AUDIT_PASS sources=457 variants=2 schedules=5484 witnesses=4')


if __name__=='__main__':main()
