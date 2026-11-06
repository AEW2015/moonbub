#!/usr/bin/env python3
"""Full-corpus absolute-cap resource-score policy from actual mixed work."""
import datetime,hashlib,importlib.util,json,statistics,sys,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'experiments/python-gamebub-v90/policy'


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def stats(v):return dict(min=min(v),median=statistics.median(v),max=max(v),total=sum(v))


def main():
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/(stamp+'-'+uuid.uuid4().hex[:8]);out.mkdir(parents=True)
    data=load('v90_policy_data',AREA/'data.py');model=load('v90_policy_model',AREA/'model.py')
    alias_selected=ROOT/'experiments/python-gamebub-v88/alias/results.json';alias=json.loads(alias_selected.read_text());alias_report=ROOT/alias['selected_report'];alias_rows=alias_report.with_name('frames.jsonl')
    alias_rows_by_id={(r['cohort'],r['fid']):r for r in map(json.loads,alias_rows.read_text().splitlines())}
    control=ROOT/'experiments/python-gamebub-v82/execution/attempt-20261106T052617072164Z-c382bb87/g16-frames.jsonl'
    controls={(r['cohort'],r['fid']):r for r in map(json.loads,control.read_text().splitlines())}
    candidate_rows=data.candidate_rows()
    sources=[Path(__file__).resolve(),AREA/'model.py',AREA/'data.py',ROOT/'experiments/python-gamebub-v89/observations/data.py',
             ROOT/'experiments/python-gamebub-v89/observations/index.json',ROOT/'experiments/python-gamebub-v86/contexts/index.json',
             data.candidate_path(),alias_selected,alias_report,alias_rows,control]
    for folder in ('experiments/python-gamebub-v89/observations','experiments/python-gamebub-v86/contexts'):
        index=json.loads((ROOT/folder/'index.json').read_text());sources.append(ROOT/folder/index['data']['path'])
    pins={str(p.relative_to(ROOT)):sha(p)for p in sources}
    for p in sources:
        if p.suffix=='.py':d=out/'sources'/p.relative_to(ROOT);d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(p.read_bytes())
    report=dict(schema='cu66-v90-resource-score-policy-v1',status='FAIL',source_sha256=pins,cap_bytes=49152,
                formula='prefix+memory_busy+inner_fetch+max(ceil(sum_context_compute/2),max_context_compute)+emission',
                freeze='Policy model/data frozen before exact four-source timing results; no fitted parameters.',
                scope=['Actual component work and complete packet bytes; serialization score ranks candidates and is not measured or predicted completion latency.',
                       'Necessary work floor is separately priced. Passing it is insufficient for10ms; score is neither a certified upper nor lower completion bound.',
                       'Host components prepared offline; no live encoder or ESP32 benchmark. Input corpus457sources in four reset histories.'],
                physical_30fps_proven=False,validated_under10ms_proven=False)
    candidates=[];selected=[];count=0
    with (out/'candidates.jsonl').open('w') as candidate_file,(out/'selections.jsonl').open('w') as selected_file:
        for base,ab,br in data.iter_raw():
            ident=base['cohort'],base['fid'];ar=alias_rows_by_id[ident];co=controls[ident]
            assert base['canonical_sha256']==ar['canonical_sha256'] and ar['root']==co['root'] and ar['seal']==co['seal']
            ab_totals=data.plane_totals(ab);br_totals=data.plane_totals(br)
            residual_tiles=sum(c['blocks']for c in base['chunks']);options={cost:[]for cost in ('LOW','HIGH')}
            for mask in range(8):
                native=candidate_rows[(*ident,mask)];shared,contexts=data.merged_totals(ab_totals,br_totals,mask)
                assert sum(r['plain_bits']for r in contexts)==native['BR88_bits']
                assert sum(r['decisions']for r in contexts)==native['remaining_decisions']
                assert sum(r['renorm']for r in contexts)==native['remaining_renorm']
                assert shared['crc_bytes']==native['components']['chunk_payloads']
                metadata=sum(native['components'][k]for k in ('header','mode_body','qmap','chunk_directory'))
                row=dict(cohort=ident[0],fid=ident[1],ordinal=base['ordinal'],key=base['key'],mask=mask,packet_sha256=native['packet_sha256'],wire_bytes=native['wire_bytes'],metadata_bytes=metadata,
                         fits_49152=native['wire_bytes']<=49152,shared_totals=shared,context_totals=contexts,
                         canonical_sha256=base['canonical_sha256'],canonical_coefficients_sha256=base['canonical_coefficients_sha256'],
                         root=co['root'],seal=co['seal'],costs={})
                for cost,weights in (('LOW',model.LOW),('HIGH',model.HIGH)):
                    features=model.feature(shared,contexts,weights,native['wire_bytes'],metadata,ar['profiles']['onchip']['decoder_memory_busy_cycles'],co['hash_compression_blocks']*64,residual_tiles)
                    row['costs'][cost]=features
                    options[cost].append(dict(mask=mask,wire_bytes=row['wire_bytes'],packet_sha256=row['packet_sha256'],**features))
                candidate_file.write(json.dumps(row,separators=(',',':'))+'\n');candidates.append(row)
            for cost in ('LOW','HIGH'):
                choice=model.select(options[cost]);payload=data.blend(ab,br,choice['mask'])
                row=dict(policy='resource_score_'+cost,cost=cost,cohort=ident[0],fid=ident[1],ordinal=base['ordinal'],key=base['key'],
                         canonical_sha256=base['canonical_sha256'],canonical_coefficients_sha256=base['canonical_coefficients_sha256'],
                         work_sha256=hashlib.sha256(payload).hexdigest(),root=co['root'],seal=co['seal'],**choice)
                selected_file.write(json.dumps(row,separators=(',',':'))+'\n');selected.append(row)
            count+=1
            if count%50==0:print('V90_POLICY_PROGRESS',count,flush=True)
    assert count==457 and len(candidates)==3656 and len(selected)==914
    summaries=[]
    for cost in ('LOW','HIGH'):
        rr=[r for r in selected if r['cost']==cost]
        summaries.append(dict(cost=cost,sources=457,wire_bytes=stats([r['wire_bytes']for r in rr]),
                              selected_masks={str(m):sum(r['mask']==m for r in rr)for m in range(8)},
                              resource_score_cycles=stats([r['resource_score_cycles']for r in rr]),
                              necessary_work_floor_cycles=stats([r['necessary_work_floor_cycles']for r in rr]),
                              necessary_floor_strictly_under10ms=sum(r['necessary_work_floor_cycles']<1000000 for r in rr),fits_49152=sum(r['wire_bytes']<=49152 for r in rr)))
    assert pins=={p:sha(ROOT/p)for p in pins},'executed source mutation'
    report.update(status='PASS_ACTUAL_WORK_RESOURCE_SCORE_SELECTION',native_sources=457,candidate_records=3656,selected_packets=914,summaries=summaries,
                  artifacts_sha256={str(p.relative_to(out)):sha(p)for p in out.rglob('*')if p.is_file()})
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');(AREA/'results.json').write_text(json.dumps(dict(report,selected_report=str((out/'results.json').relative_to(ROOT))),indent=2)+'\n')
    print('V90_POLICY_PASS',out/'results.json',flush=True)


if __name__=='__main__':main()
