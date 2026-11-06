#!/usr/bin/env python3
"""Actual descriptor-3 constants versus addressed V88 native controls."""
import datetime,gzip,hashlib,importlib.util,json,statistics,sys,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'experiments/python-gamebub-v89/constants'


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def stats(v):return dict(min=min(v),median=statistics.median(v),max=max(v),total=sum(v))


def main():
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/(stamp+'-'+uuid.uuid4().hex[:8]);out.mkdir(parents=True)
    native=load('v89_const_native',ROOT/'experiments/python-gamebub-v82/native/data.py')
    layout=load('v89_const_layout',AREA/'layout.py');trace=load('v89_const_trace',AREA/'trace.py')
    oldlayout=load('v89_old_layout',ROOT/'experiments/python-gamebub-v87/alias/prototype.py')
    oldtrace=load('v89_old_trace',ROOT/'experiments/python-gamebub-v88/alias/trace.py')
    commitment=load('v89_const_commitment',ROOT/'scripts/cu66-v82/prototype_commitment.py')
    qualified=json.loads((ROOT/'experiments/python-gamebub-v88/alias/results.json').read_text());qp=ROOT/qualified['selected_report']
    oldrows={(r['cohort'],r['fid']):r for r in map(json.loads,qp.with_name('frames.jsonl').read_text().splitlines())}
    sources=[Path(__file__).resolve(),AREA/'layout.py',AREA/'trace.py',ROOT/'experiments/python-gamebub-v82/native/data.py',ROOT/'experiments/python-gamebub-v82/native/index.json',ROOT/'experiments/python-gamebub-v87/alias/prototype.py',ROOT/'experiments/python-gamebub-v88/alias/trace.py',ROOT/'scripts/cu66-v82/prototype_commitment.py',qp,qp.with_name('frames.jsonl')]
    pins={str(p.relative_to(ROOT)):sha(p) for p in sources}
    for p in sources:
        if p.suffix=='.py':dest=out/'sources'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
    rows=[];cohort=None;selected=[]
    with (out/'frames.jsonl').open('w') as stream:
        for frame in native.iter_frames():
            if frame['cohort']!=cohort:
                cohort=frame['cohort'];state=layout.ConstantSlots(frame['hidden_mask']);base=oldlayout.TileSlots()
                tree=commitment.CommitmentTree(granularity=16);map_role=None;banks=[bytearray(b'\xff'*2048) for _ in range(3)];oldbanks=[bytearray(b'\xff'*2048) for _ in range(3)]
            assert sum(frame['hidden_mask'])==294 and hashlib.sha256(frame['hidden_mask']).hexdigest()=='e08b9861ae9a170c913c6425a5773ff42042a0abfe2fef8cd756cb505a8a8fa5'
            frame=dict(frame,generation=frame['ordinal']+1);ground=oldrows[cohort,frame['fid']]
            plan=tree.plan(frame,frame['copy_ref_mask']);dirty={t for g in plan['recomputed_groups'] for t in g['tile_indices']}
            previous=state.accepted;presented=state.presented;oldprev=base.accepted;oldpresented=base.presented
            base.begin(frame['tiles'],frame['copy_ref_mask']);oldcandidate=list(base.candidate)
            state.begin(frame['tiles'],frame['copy_ref_mask']);candidate=list(state.candidate)
            gathered=state.image(candidate);assert gathered==frame['tiles']
            assert all(state.physical[s][i] is None for s in range(3) for i,h in enumerate(frame['hidden_mask']) if h)
            rebuilt=dict(frame,tiles=gathered,planes=[gathered[:5400],gathered[5400:6750],gathered[6750:]])
            check=tree.plan(rebuilt,frame['copy_ref_mask']);assert (check['root'].hex(),check['seal'].hex())==(ground['root'],ground['seal'])
            state.commit(frame['tiles']);state.present();base.commit(frame['fid'],oldlayout.digest(frame['tiles']));base.present();tree.commit(plan)
            candidate_role=next(i for i in range(3) if i!=map_role);roles=(map_role,map_role,candidate_role)
            events=trace.commands(frame,previous,candidate,presented,dirty,map_roles=roles)
            oldevents=oldtrace.commands(frame,oldprev,oldcandidate,oldpresented,dirty,map_roles=roles)
            trace.validate_descriptors(events,banks,frame['hidden_mask']);oldtrace.validate_descriptors(oldevents,oldbanks)
            accounts={p:trace.account(events,p) for p in ('onchip','cached','uncached')}
            controls={p:oldtrace.account(oldevents,p) for p in accounts}
            assert controls==ground['profiles'],'qualified addressed control mismatch'
            for policy,a in accounts.items():
                b=controls[policy]
                assert a['canonical_write_BL8']==b['canonical_write_BL8']-1176
                assert a['scanout_read_BL8']==b['scanout_read_BL8']-1176
                assert a['constant_candidate_bytes']==a['constant_scanout_bytes']==294*64
                assert a['memory_busy_cycles']==b['memory_busy_cycles']-39984
                assert a['decoder_memory_busy_cycles']==b['decoder_memory_busy_cycles']-18816
            row=dict(cohort=cohort,fid=frame['fid'],ordinal=frame['ordinal'],key=frame['key'],canonical_sha256=frame['canonical_sha256'],root=check['root'].hex(),seal=check['seal'].hex(),
                     tile_order_sha256=oldlayout.digest(gathered),trace_sha256=trace.digest(events),hidden_tiles=294,profiles=accounts,control_profiles=controls)
            rows.append(row);stream.write(json.dumps(row,separators=(',',':'))+'\n');stream.flush()
            if (cohort,frame['fid']) in ((0,0),(0,1),(0,3),(3,50)):
                p=out/f'c{cohort}-f{frame["fid"]}-trace.json.gz'
                with gzip.open(p,'wt') as f:json.dump(dict(hidden=list(frame['hidden_mask']),candidate=candidate,map_roles=roles,events=events,accounts=accounts),f,separators=(',',':'))
                selected.append(dict(path=str(p.relative_to(ROOT)),sha256=sha(p)))
            map_role=candidate_role
            if len(rows)%50==0:print('V89_CONSTANT_PROGRESS',len(rows),flush=True)
    assert len(rows)==457 and pins=={p:sha(ROOT/p) for p in pins}
    summaries=[]
    for policy in ('onchip','cached','uncached'):
        summaries.append(dict(policy=policy,sources=457,memory_busy_ms=stats([r['profiles'][policy]['memory_busy_cycles']/100000 for r in rows]),
                              decoder_memory_busy_ms=stats([r['profiles'][policy]['decoder_memory_busy_cycles']/100000 for r in rows]),
                              avoided_data_write_BL8=537432,avoided_scanout_read_BL8=537432,
                              generated_candidate_bytes=8598912,generated_scanout_bytes=8598912))
    report=dict(schema='cu66-v89-constant-sentinel-trace-v1',status='PASS_FIXED_PROFILE_CONSTANT_AND_NATIVE_CONTENT',native_sources=457,source_sha256=pins,summaries=summaries,
                selected_traces=selected,frames_sha256=sha(out/'frames.jsonl'),scope=['Descriptor3 meansCONST128 only at fixed hidden-profile positions; it remainsINVALID at visible positions. No new validity bitmap assumed.',
                'Candidate map is unpublished until content/generation validation. All descriptor writes/reads retained; only constant pixel stores/gathers replaced by generation.',
                'Generated constant bytes and required generator ports are explicit; no cycle/clock/continuous-display or ESP32 qualification.',
                'Physical address windows unchanged; unused constant slots are holes, not a proven smaller RAM allocation.'],physical_30fps_proven=False,validated_under10ms_proven=False)
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');(AREA/'results.json').write_text(json.dumps(dict(report,selected_report=str((out/'results.json').relative_to(ROOT))),indent=2)+'\n')
    print(report['status'],out/'results.json')


if __name__=='__main__':main()
