#!/usr/bin/env python3
"""Selected-source CS88 producer work coupled to actual COPY-alias memory."""
from __future__ import annotations
import datetime,gzip,hashlib,importlib.util,json,statistics,sys,time,uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v89/joint'
OBS=ROOT/'experiments/python-gamebub-v89/observations'
POLICIES=('AB38_control','feedback_overhead5','feedback_overhead15','all_BR88')
SELECTED={(0,0),(0,1),(0,3),(3,50)}


def load(name,p):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stats(v):return dict(min=min(v),median=statistics.median(v),max=max(v),total=sum(v))


def main():
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=AREA/'attempts'/(stamp+'-'+uuid.uuid4().hex[:8]);out.mkdir(parents=True)
    repricer=load('v89_joint_reprice',AREA/'model.py')
    data=load('v89_joint_observations',OBS/'data.py')
    alias=load('v89_joint_alias',ROOT/'experiments/python-gamebub-v88/alias/probe.py')
    scheduler=load('v89_joint_scheduler',ROOT/'experiments/python-gamebub-v83/scheduler.py')
    generic=load('v89_joint_generic',ROOT/'experiments/python-gamebub-v83/audit.py')
    independent=load('v89_joint_independent',ROOT/'scripts/cu66-v87/audit_coupled.py')
    credits=load('v89_joint_credits',ROOT/'experiments/python-gamebub-v84/credits.py')
    front_audit=load('v89_joint_front_audit',ROOT/'experiments/python-gamebub-v87/coupled/model.py')
    old=json.loads((ROOT/'experiments/python-gamebub-v88/alias/probe.json').read_text())
    wire_selected=json.loads((ROOT/'experiments/python-gamebub-v88/wire/results.json').read_text())
    wire_rows=(ROOT/wire_selected['selected_report']).with_name('frames.jsonl')
    native_packets={(r['cohort'],r['fid'],r['policy']):r for r in map(json.loads,wire_rows.read_text().splitlines())}
    sources=[Path(__file__).resolve(),AREA/'model.py',OBS/'data.py',OBS/'index.json',
             ROOT/'experiments/python-gamebub-v88/alias/probe.py',ROOT/'experiments/python-gamebub-v88/alias/probe.json',
             ROOT/'experiments/python-gamebub-v83/scheduler.py',ROOT/'experiments/python-gamebub-v83/audit.py',
             ROOT/'scripts/cu66-v87/audit_coupled.py',ROOT/'experiments/python-gamebub-v84/credits.py',ROOT/'experiments/python-gamebub-v87/coupled/model.py',
             ROOT/'experiments/python-gamebub-v88/wire/results.json',ROOT/wire_selected['selected_report'],wire_rows]
    # Saved source workloads/physical snapshots are the independently qualified
    # V88 inputs. New primitive work and complete CS88 bytes replace producer
    # task durations; backend edges remain intact.
    originals={};snapshots={};controls=[]
    for r in old['rows']:
        p=ROOT/r['witness'];sources.append(p)
        with gzip.open(p,'rt') as f:w=json.load(f)
        key=(r['cohort'],r['fid']);source=ROOT/w['source_witness'];trace=ROOT/w['source_trace']
        sources.extend((source,trace))
        with gzip.open(source,'rt') as f:original=json.load(f)
        with gzip.open(trace,'rt') as f:snapshot=json.load(f)
        if key not in originals or original['config']['name']=='low_lanes2':originals[key]=original
        snapshots[key]=snapshot
        controls.append((r,original,snapshot))
    assert set(originals)==SELECTED
    pins={str(p.relative_to(ROOT)):sha(p) for p in set(sources)}
    for p in set(sources):
        if p.suffix=='.py':
            dest=out/'sources'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
    report=dict(schema='cu66-v89-selected-joint-v1',status='FAIL',source_sha256=pins,
                selected_source_ids=[list(x)for x in sorted(SELECTED)],policies=list(POLICIES),
                clock_MHz_assumption=100,physical_30fps_proven=False,validated_under10ms_proven=False,
                scope=['Selected four sources, actual mixed CS88 producer observations and complete packet scans, one causal backend graph.',
                       'LOW/HIGH are assumed primitive costs, including plain_bits 1/2 cycles plus symbol/event costs; not RTL clock bounds.',
                       'Nominal 64-cycle dequant/inverse/reconstruction, one/two-server scheduling assumptions; fixed on-chip alias descriptor ports.',
                       'Publication latency excludes later full YUV gather; neither models continuous LCD/RGB565/HUD composition, physical refresh/row timings or ESP32 ingress.',
                       'Native pixel/packet correctness belongs to qualified observation and V88 oracles; scheduling does not execute inverse arithmetic.'])
    rows=[];baseline=[];started=time.monotonic()
    capacities=dict(memory=1,inverse=1,reconstruct=1,hash=1,tree_r=1,tree_w=1,map_r=1,map_w=1,fetch=1,arithmetic=2,emit=1,dequant=1,alias_map_r=1,alias_map_w=1)
    try:
        for expected,original,snapshot in controls:
            work=alias.transform(original,snapshot,expected['alias'])
            result=scheduler.schedule(work['jobs'],capacities,original['config']['windows'],retain_timeline=True)
            timed={r['id']:r for r in result['timeline']};decode=timed[work['alias_trace']['decode_complete']]['finish']
            assert decode/100000==expected['conditional_decode_ms']
            assert result['finish_cycles']/100000==expected['conditional_base_gather_complete_ms']
            baseline.append(dict(cohort=expected['cohort'],fid=expected['fid'],configuration=expected['configuration'],alias=expected['alias'],decode_cycles=decode,complete_cycles=result['finish_cycles']))
        assert len(baseline)==10
        seen=set()
        with (out/'rows.jsonl').open('w') as output:
            for group in data.iter_policies(POLICIES,only=SELECTED):
                if not group:raise ValueError('empty observation group')
                key=(group[0]['cohort'],group[0]['fid'])
                if key not in SELECTED:continue
                assert key not in seen;seen.add(key)
                assert {f['policy'] for f in group}==set(POLICIES)
                original=originals[key];snapshot=snapshots[key]
                for frame in group:
                    assert (frame['cohort'],frame['fid'])==key
                    native_packet=native_packets[(*key,frame['policy'])]
                    assert frame['packet_sha256']==native_packet['packet_sha256']
                    assert frame['wire_bytes']==native_packet['wire_bytes'] and frame['mask']==native_packet['mask']
                    assert frame['canonical_sha256']==snapshot['frame']['canonical_sha256']==native_packet['decoded']['canonical_sha256']
                    assert frame['canonical_coefficients_sha256']==native_packet['decoded']['coefficient_sha256']
                    for cost,weights in (('LOW',repricer.LOW),('HIGH',repricer.HIGH)):
                        priced=repricer.reprice(original['workload'],frame['shared_work'],frame['context_work'],weights,
                                               wire_bytes=frame['wire_bytes'],metadata_bytes=frame['metadata_bytes'])
                        for enabled in (False,True):
                            work=alias.transform(dict(original,workload=priced),snapshot,enabled)
                            result=scheduler.schedule(work['jobs'],capacities,None,retain_timeline=True)
                            audit=generic.verify(work['jobs'],result['timeline'],capacities,None,work['groups'],4)
                            lifetimes=credits.audit_lifetimes(work,result['timeline'])
                            front=front_audit.audit(work,result,2)
                            # Every actual selected schedule is independently
                            # checked; a subset retains complete JSON witnesses.
                            other=independent.verify(work,result['timeline'],capacities,None)
                            timed={r['id']:r for r in result['timeline']};decode=timed[work['alias_trace']['decode_complete']]['finish']
                            row=dict(cohort=key[0],fid=key[1],policy=frame['policy'],cost=cost,alias=enabled,
                                     packet_sha256=frame['packet_sha256'],wire_bytes=frame['wire_bytes'],metadata_bytes=frame['metadata_bytes'],
                                     mask=frame['mask'],observation_work_sha256=frame['work_sha256'],decode_cycles=decode,conditional_decode_ms=decode/100000,
                                     full_gather_cycles=result['finish_cycles'],conditional_base_gather_complete_ms=result['finish_cycles']/100000,
                                     producer_work_cycles=work['frontend']['work_cycles'],memory_work_cycles=audit['resource_work_cycles']['memory'],
                                     alias_changes=work['alias_trace'],credit_peaks=lifetimes,independent_audit=other,
                                     timeline_sha256=other['timeline_sha256'])
                            # Keep all hard-source policies, plus key/control15
                            # comparisons and the restored-store branch.
                            retain=(key==(3,50) and frame['policy'] in ('AB38_control','feedback_overhead15')) or (
                                key!=(3,50) and frame['policy'] in ('AB38_control','feedback_overhead15') and cost=='LOW' and enabled) or (
                                key==(3,50) and frame['policy']=='all_BR88' and cost=='HIGH' and enabled)
                            if retain:
                                witness=out/f"c{key[0]}-f{key[1]}-{frame['policy']}-{cost}-alias{int(enabled)}.json.gz"
                                with gzip.open(witness,'wt') as f:json.dump(dict(capacities=capacities,windows=None,workload=work,result=result,audit=audit,credits=lifetimes,frontend_audit=front,independent_audit=other),f,separators=(',',':'))
                                row.update(witness=str(witness.relative_to(ROOT)),witness_sha256=sha(witness))
                            output.write(json.dumps(row,separators=(',',':'))+'\n');output.flush();rows.append(row)
                            print('V89_JOINT_PROGRESS',len(rows),key,frame['policy'],cost,enabled,round(time.monotonic()-started,2),flush=True)
        assert seen==SELECTED and len(rows)==64
        summaries=[]
        for policy in POLICIES:
            for cost in ('LOW','HIGH'):
                for enabled in (False,True):
                    selected=[r for r in rows if (r['policy'],r['cost'],r['alias'])==(policy,cost,enabled)]
                    summaries.append(dict(policy=policy,cost=cost,alias=enabled,sources=len(selected),conditional_decode_ms=stats([r['conditional_decode_ms']for r in selected]),conditional_under10ms=sum(r['decode_cycles']<1000000 for r in selected)))
        assert pins=={p:sha(ROOT/p)for p in pins},'executed source mutation'
        report.update(status='PASS_SELECTED_ACTUAL_JOINT_SCHEDULES',unique_sources=4,schedules=64,frozen_CS86_control_matches=baseline,summaries=summaries)
    except BaseException as exc:
        report['failure']=repr(exc);raise
    finally:
        report['wall_seconds']=time.monotonic()-started
        report['artifacts_sha256']={str(p.relative_to(out)):sha(p)for p in out.rglob('*')if p.is_file()}
        (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');print('V89_JOINT_REPORT',out/'results.json',report['status'],flush=True)
    (AREA/'results.json').write_text(json.dumps(dict(report,selected_report=str((out/'results.json').relative_to(ROOT))),indent=2)+'\n')


if __name__=='__main__':main()
