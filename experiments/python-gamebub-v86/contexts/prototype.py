#!/usr/bin/env python3
"""Full-corpus prospective context scheduling on actual re-encoded chunks."""
from array import array
import argparse,datetime,gzip,hashlib,importlib.util,json,statistics,struct,sys,tarfile,time,uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3];AREA=Path(__file__).resolve().parent
FIELDS=('decisions','renorm','stream_bytes','rice_values','events','raw_bytes','header_bytes','crc_bytes','emits','raw_bits','prob_init')
LOW=dict(decisions=2,renorm=2,stream_bytes=2,rice_values=1,events=1,raw_bytes=2,header_bytes=2,crc_bytes=2,emits=1,raw_bits=1,prob_init=1)
HIGH=dict(decisions=4,renorm=4,stream_bytes=4,rice_values=1,events=1,raw_bytes=4,header_bytes=4,crc_bytes=4,emits=1,raw_bits=2,prob_init=1)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,p):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def stats(v):return dict(min=min(v),median=statistics.median(v),max=max(v),total=sum(v))


def iter_cohort(index,cohort):
    path=AREA/index['data']['path'];assert sha(path)==index['data']['gzip_sha256']
    digest=hashlib.sha256();count=0
    with gzip.open(path,'rb') as stream:
        while True:
            prefix=stream.read(4)
            if not prefix:break
            n,=struct.unpack('<I',prefix);assert 1<=n<=262144
            head=stream.read(n);payload=stream.read(8100*55*4)
            assert len(head)==n and len(payload)==8100*55*4
            digest.update(prefix);digest.update(head);digest.update(payload)
            frame=json.loads(head);expected=index['frames'][count];count+=1
            for k in ('cap','cohort','fid','ordinal','canonical_coefficients_sha256','work_sha256'):assert frame[k]==expected[k]
            assert hashlib.sha256(payload).hexdigest()==frame['work_sha256']
            if frame['cohort']!=cohort:continue
            words=array('I');words.frombytes(payload)
            if sys.byteorder!='little':words.byteswap()
            shared=[];contexts=[]
            for tile in range(8100):
                at=tile*55;shared.append(dict(zip(FIELDS,words[at:at+11])))
                contexts.append([dict(zip(FIELDS,words[at+11+c*11:at+22+c*11])) for c in range(4)])
            frame['shared_work']=shared;frame['context_work']=contexts;yield frame
    assert count==914 and digest.hexdigest()==index['data']['raw_sha256']


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--cohort',required=True,type=int,choices=range(4));parser.add_argument('--limit-records',type=int,default=0)
    args=parser.parse_args();stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=AREA/'model-attempts'/f'{stamp}-{uuid.uuid4().hex[:8]}';out.mkdir(parents=True)
    index=json.loads((AREA/'index.json').read_text())
    sources=[Path(__file__).resolve(),AREA/'model.py',AREA/'data.py',AREA/'index.json',AREA/index['data']['path'],
             ROOT/'experiments/python-gamebub-v83/scheduler.py',ROOT/'scripts/cu66-v84/prototype_pipeline.py']
    pins={str(p.relative_to(ROOT)):sha(p) for p in sources}
    with tarfile.open(out/'sources.tar.gz','w:gz') as tar:
        for p in sources:
            if p.suffix!='.gz':tar.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
    report=dict(schema='cu66-v86-reencoded-context-model-v1',status='FAIL',source_sha256=pins,cohort=args.cohort,
                source_archive_sha256=sha(out/'sources.tar.gz'),clock_mhz_assumption=100,physical_timing_proven=False,
                full_corpus_scheduling=not args.limit_records,limit_records=args.limit_records,window=8)
    started=time.monotonic()
    try:
        model=load('cu86_context_model',AREA/'model.py')
        scheduler=load('cu86_context_scheduler',ROOT/'experiments/python-gamebub-v83/scheduler.py')
        old=load('cu86_context_weights',ROOT/'scripts/cu66-v84/prototype_pipeline.py');assert LOW==old.LOW and HIGH==old.HIGH
        cases=[];processed=0
        with (out/'rows.jsonl').open('w') as stream:
            for frame in iter_cohort(index,args.cohort):
                if args.limit_records and processed>=args.limit_records:break
                for cost,weights in (('LOW',LOW),('HIGH',HIGH)):
                    w=model.build(frame['shared_work'],frame['context_work'],weights,8)
                    for lanes in (1,2,4):
                        r=scheduler.schedule(w['jobs'],dict(fetch=1,arithmetic=lanes,emit=1),retain_timeline=True)
                        a=model.audit(w,r,lanes)
                        row=dict(cap=frame['cap'],cohort=frame['cohort'],fid=frame['fid'],ordinal=frame['ordinal'],key=frame['key'],cost=cost,
                                 lanes=lanes,window=8,model_ms=r['finish_cycles']*1e-5,
                                 timeline_sha256=hashlib.sha256(json.dumps(r['timeline'],sort_keys=True,separators=(',',':')).encode()).hexdigest(),**a)
                        cases.append(row);stream.write(json.dumps(row,separators=(',',':'))+'\n')
                        if frame['cohort']==3 and frame['fid']==50 and cost=='LOW' and lanes in (1,2):
                            with gzip.open(out/f"witness-cap{frame['cap']}-c3-f50-low-w8-l{lanes}.json.gz",'wt') as target:
                                json.dump(dict(workload=w,result=r,audit=a),target,separators=(',',':'))
                processed+=1
                if processed==1 or processed%10==0:print('REENCODED_CONTEXT_MODEL_PROGRESS',args.cohort,processed,len(cases),round(time.monotonic()-started,2),flush=True)
        expected=2*(119,119,119,100)[args.cohort]
        assert processed==(args.limit_records or expected)
        summaries=[]
        for cap in (256,65536):
            for cost in ('LOW','HIGH'):
                for lanes in (1,2,4):
                    selected=[r for r in cases if (r['cap'],r['cost'],r['lanes'])==(cap,cost,lanes)]
                    if selected:summaries.append(dict(cap=cap,cost=cost,window=8,lanes=lanes,sources=len(selected),
                                                       model_ms=stats([r['model_ms'] for r in selected]),
                                                       conditional_front_under10ms=sum(r['finish_cycles']<1_000_000 for r in selected)))
        assert pins=={name:sha(ROOT/name) for name in pins},'source mutation'
        report.update(status='PASS_SMOKE_ONLY' if args.limit_records else 'PASS_FULL_COHORT_REENCODED_FRONT_MODEL',
                      variant_records_scheduled=processed,native_sources_scheduled=processed//2,schedules=len(cases),summaries=summaries,
                      artifacts_sha256={p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name!='results.json'},
                      scope=['Actual re-encoded residual AB38 inputs, both chunk profiles; no old-stream work scaling.',
                             'One shared fetch/control server and one emitter; per-context order and ordered four-way tile rendezvous.',
                             'Fetch batch precedes arithmetic batch per tile/context; not an RTL instruction trace.',
                             'Window8 bounds admitted coefficient assembly with immediate external consumer; not full pipeline/FIFO/physical RAM proof.',
                             'COPY/CONST have no residual entropy and one local emit; map/outer CRC/parsing and HUD/dequant/reconstruction/memory/display/ESP32 are excluded.',
                             'Weights/100MHz are hypothetical inputs, not measured FPGA clocks, fit, DSP or validated under10ms/30fps proof.'])
    except BaseException as exc:report['failure']=repr(exc);raise
    finally:
        report['wall_seconds']=time.monotonic()-started
        (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        print('REENCODED_CONTEXT_MODEL_REPORT',out/'results.json',report['status'],flush=True)


if __name__=='__main__':main()
