#!/usr/bin/env python3
"""Independent retained-context model counts and two witness DAG reconstructions."""
import argparse,gzip,hashlib,importlib.util,json,statistics,sys,tarfile
from pathlib import Path

AREA=Path(__file__).resolve().parent
ROOT=AREA.parents[2]
FETCH={'stream_bytes','raw_bytes','header_bytes','crc_bytes'}


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stats(v):return dict(min=min(v),median=statistics.median(v),max=max(v),total=sum(v))
def load(n,p):
    spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);sys.modules[n]=m;spec.loader.exec_module(m);return m


def reconstruct(frame,fields,weights,window):
    jobs=[];last_setup=None;emits=[];last=[None]*4
    def add(kind,resource,duration,deps,**extra):
        ident=len(jobs);jobs.append(dict(id=ident,deps=sorted(set(d for d in deps if d is not None)),
                                       kind=kind,resource=resource,duration=duration,**extra));return ident
    for tile,(shared,contexts)in enumerate(zip(frame['shared'],frame['contexts'],strict=True)):
        shared=dict(zip(fields,shared));contexts=[dict(zip(fields,c))for c in contexts]
        deps=[last_setup]+([emits[tile-window]]if tile>=window else [])
        last_setup=add('shared_setup','fetch',sum(v*weights[k]for k,v in shared.items()if k!='emits'),deps,tile=tile)
        frontier=[]
        for context,work in enumerate(contexts):
            fetched=add('context_fetch','fetch',sum(v*weights[k]for k,v in work.items()if k in FETCH),
                        [last_setup,last[context]],tile=tile,context=context)
            done=add('context_compute','arithmetic',sum(v*weights[k]for k,v in work.items()if k not in FETCH),
                     [fetched],tile=tile,context=context)
            last[context]=done;frontier.append(done)
        emits.append(add('tile_emit','emit',shared['emits']*weights['emits'],frontier+([emits[-1]]if emits else []),tile=tile))
    add('complete',None,0,[emits[-1]])
    return jobs


def main():
    p=argparse.ArgumentParser();p.add_argument('--attempt',required=True,type=Path);p.add_argument('--verify',action='store_true');args=p.parse_args()
    attempt=args.attempt.resolve();report=json.loads((attempt/'results.json').read_text())
    assert report['status']=='PASS_SELECTED_CONTEXT_MODEL'
    assert report['sources_scheduled']==25 and report['schedules']==300 and report['synthetic_checks']==18
    assert report['physical_timing_proven']is report['full_corpus_scheduling']is False
    for name,digest in report['source_sha256'].items():assert sha(ROOT/name)==digest,name
    for name,digest in report['artifacts_sha256'].items():assert sha(attempt/name)==digest,name
    with tarfile.open(attempt/'sources.tar.gz','r:gz')as tar:
        expected={name for name in report['source_sha256']if not name.endswith('.gz')}
        assert {m.name for m in tar.getmembers()}==expected
        for m in tar.getmembers():assert hashlib.sha256(tar.extractfile(m).read()).hexdigest()==report['source_sha256'][m.name]
    costs=load('cu85_context_audit_weights',ROOT/'scripts/cu66-v84/prototype_pipeline.py')
    index=json.loads((AREA/'index.json').read_text());by_id={(f['cohort'],f['fid']):f for f in index['frames']}
    selected={(f['cohort'],f['fid'])for f in index['frames']if f['ordinal']<6 or f['cohort']==3 and f['fid']==50}
    rows=[json.loads(s)for s in(attempt/'rows.jsonl').read_text().splitlines()]
    keys={(r['cohort'],r['fid'],r['cost'],r['window'],r['lanes'])for r in rows}
    assert len(rows)==len(keys)==300
    assert keys=={(*f,c,w,l)for f in selected for c in('LOW','HIGH')for w in(8,64)for l in(1,2,4)}
    for row in rows:
        frame=by_id[row['cohort'],row['fid']];weights=getattr(costs,row['cost'])
        shared=frame['shared_totals'];contexts=frame['context_totals']
        fetch=sum(v*weights[k]for k,v in shared.items()if k!='emits')+sum(sum(v*weights[k]for k,v in c.items()if k in FETCH)for c in contexts)
        compute=[sum(v*weights[k]for k,v in c.items()if k not in FETCH)for c in contexts]
        emit=shared['emits']*weights['emits'];lanes=row['lanes']
        assert row['resource_work_cycles']==dict(fetch=fetch,arithmetic=sum(compute),emit=emit)
        floor=max(fetch,emit,max(compute),(sum(compute)+lanes-1)//lanes)
        assert row['necessary_work_floor_cycles']==floor<=row['finish_cycles']
        assert row['model_ms']==row['finish_cycles']*1e-5
        assert 0<row['window_peak']<=row['window']
        assert row['resource_peaks']['arithmetic']<=lanes and row['resource_peaks']['fetch']<=1 and row['resource_peaks']['emit']<=1
    summaries=[]
    for cost in('LOW','HIGH'):
        for window in(8,64):
            for lanes in(1,2,4):
                chosen=[r for r in rows if(r['cost'],r['window'],r['lanes'])==(cost,window,lanes)]
                summaries.append(dict(cost=cost,window=window,lanes=lanes,sources=25,model_ms=stats([r['model_ms']for r in chosen])))
    assert summaries==report['summaries']
    # Scan compressed raw records while parsing only the retained witness source.
    witness_frame=None;raw_hash=hashlib.sha256();count=0
    with gzip.open(AREA/index['data']['path'],'rb')as stream:
        for line in stream:
            raw_hash.update(line);count+=1
            if line.startswith(b'{"cohort":3,"ordinal":50,"fid":50,'):witness_frame=json.loads(line)
    assert count==457 and raw_hash.hexdigest()==index['data']['raw_sha256'] and witness_frame is not None
    generic=load('cu85_context_audit_timeline',ROOT/'experiments/python-gamebub-v83/audit.py')
    witness_records=[]
    for path in sorted(attempt.glob('witness-*.json.gz')):
        with gzip.open(path,'rt')as stream:w=json.load(stream)
        lanes=int(path.stem.split('-l')[-1].split('.')[0]);work=w['workload'];result=w['result']
        assert work['window']==8
        expected=reconstruct(witness_frame,index['fields'],costs.LOW,8)
        assert work['jobs']==expected
        timeline=generic.verify(expected,result['timeline'],dict(fetch=1,arithmetic=lanes,emit=1))
        assert timeline['finish_cycles']==result['finish_cycles']
        row=next(r for r in rows if(r['cohort'],r['fid'],r['cost'],r['window'],r['lanes'])==(3,50,'LOW',8,lanes))
        assert row['finish_cycles']==timeline['finish_cycles'] and row['resource_work_cycles']==timeline['resource_work_cycles']
        witness_records.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path),lanes=lanes,jobs=len(expected),independent_DAG_reconstruction=True))
    assert len(witness_records)==2
    result=dict(schema='cu66-v85-context-model-audit-v1',status='PASS',selected_sources=25,schedules=300,
                synthetic_checks=18,independently_reconstructed_witnesses=witness_records,
                source_sha256={str(Path(__file__).relative_to(ROOT)):sha(Path(__file__)),
                               str((attempt/'results.json').relative_to(ROOT)):sha(attempt/'results.json'),
                               str((AREA/'verification.json').relative_to(ROOT)):sha(AREA/'verification.json')},
                scope='Selected standalone conditional model; no full457 latency, RTL speed or full decoder/ESP32 proof.')
    dest=AREA/'model-verification.json'
    if args.verify:assert json.loads(dest.read_text())==result
    else:
        if dest.exists():raise FileExistsError(dest)
        dest.write_text(json.dumps(result,indent=2)+'\n')
    print('V85_CONTEXT_MODEL_AUDIT_PASS selected_sources=25 schedules=300 witnesses=2')


if __name__=='__main__':main()
