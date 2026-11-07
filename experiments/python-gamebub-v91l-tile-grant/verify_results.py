#!/usr/bin/env python3
"""Preserve frozen native/pin/lease oracles; add independent grant policy replay."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
OLD=ROOT/'experiments/python-gamebub-v91l-overlap'
BASELINE='4d6872f428beb902498d2cee4c509e643cd5aa78'
# Import exact frozen audit rather than copying and relaxing its pixel, SHA,
# scratch, physical memory, history or display/publication checks.
for name in ('verify_results.py','lease_trace.py'):
    expected=subprocess.check_output(['git','show',BASELINE+':'+str((OLD/name).relative_to(ROOT))],cwd=ROOT)
    assert expected==(OLD/name).read_bytes(),'frozen overlap verifier changed: '+name
sys.path.insert(0,str(OLD))
spec=importlib.util.spec_from_file_location('frozen_native_overlap_verifier',OLD/'verify_results.py')
control=importlib.util.module_from_spec(spec);spec.loader.exec_module(control)
need,sha,events,native=control.need,control.sha,control.events,control.native
from grant_trace import GrantTrace,ordered_policy

class PolicyMemory(control.ScratchReplay):
    def __init__(self,require_written_reads=False):
        super().__init__(require_written_reads);self.policy=GrantTrace()
    def feed(self,event):
        self.policy.feed(event);super().feed(event)
    def finish(self):
        result=super().finish();result['reference_grant_policy']=self.policy.finish();return result

# Frozen audit looks up its memory checker through this global. The subclass
# forwards every event unmodified to the old oracle and adds policy checks.
control.ScratchReplay=PolicyMemory

BASE_ORDER=control.ordered_scratch
control.ordered_scratch=lambda stream:ordered_policy(stream,BASE_ORDER)

def normalized_unit(raw,limit):
    """Keep checked POR boundaries; verify/deduplicate the REF1 legacy twin."""
    from collections import Counter
    import itertools
    segments=[];current=None
    for e in raw:
        if e['type']=='check' and e.get('label')=='cold_owner_idle':
            if current is not None:segments.append(current)
            current=[]
        elif current is not None and 'time_ps' in e:current.append(e)
    if current is not None:segments.append(current)
    need(segments,'missing source-reviewed cold-reset boundaries')
    normalized=[]
    for segment in segments:
        trace=[]
        for _,group in itertools.groupby(segment,key=lambda e:e['time_ps']):
            group=list(group)
            if limit==1:
                copies=Counter(json.dumps(e,sort_keys=True) for e in group if e['type'].startswith('mux_'))
                need(all(n==2 for n in copies.values()),'legacy/candidate REF1 receipts are not exact pairs')
                used=set();result=[]
                for e in group:
                    if e['type'].startswith('mux_'):
                        key=json.dumps(e,sort_keys=True)
                        if key in used:continue
                        used.add(key)
                    result.append(e)
                group=result
            trace.extend(group)
        normalized.append(list(ordered_policy(trace,BASE_ORDER)))
    actual=[e for segment in normalized for e in segment if e['type']=='mux_req']
    observed=[e for e in raw if e['type']=='unit_mem_accept']
    need(len(actual)==len(observed)==60,'unit accepted request coverage differs')
    for a,b in zip(actual,observed):
        need(all(a[n]==b[n] for n in ('owner','epoch','generation','bank','address')) and a['time_ps']==b['cycle']*10000+5000,'actual unit request differs from driver handshake witness')
    return normalized

def policy_negatives(segments):
    tests=[
        ('group legality',lambda e:e['type']=='batch_start',lambda e:dict(e,groupable=1-e['groupable']),'grouping legality'),
        ('budget parameter',lambda e:e['type']=='batch_start',lambda e:dict(e,limit=1),'parameter changes'),
        ('continuation epoch',lambda e:e['type']=='batch_continue',lambda e:dict(e,epoch=e['epoch']^1),'continuation descriptor'),
        ('continuation ticket',lambda e:e['type']=='batch_continue',lambda e:dict(e,generation=e['generation']^1),'continuation descriptor'),
        ('continuation bank',lambda e:e['type']=='batch_continue',lambda e:dict(e,bank=e['bank']^1),'continuation descriptor'),
        ('continuation address',lambda e:e['type']=='batch_continue',lambda e:dict(e,address=e['address']+16),'continuation descriptor'),
        ('continuation tile',lambda e:e['type']=='batch_continue',lambda e:dict(e,address=e['address']+64),'continuation descriptor'),
        ('continuation credit',lambda e:e['type']=='batch_continue',lambda e:dict(e,lines=e['lines']+1),'continuation credit'),
        ('gap counter',lambda e:e['type']=='batch_wait',lambda e:dict(e,gap=e['gap']+1),'bounded gap counter'),
        ('yield credits',lambda e:e['type']=='batch_yield',lambda e:dict(e,lines=e['lines']+1),'yield successful-credit'),
        ('timeout cause',lambda e:e['type']=='batch_yield' and e['reason']==4,lambda e:dict(e,reason=0),'yields early'),
        ('yield missing',lambda e:e['type']=='batch_yield',lambda e:dict(e,type='mutated_missing_yield'),'release lacks checked yield'),
        ('request intent',lambda e:e['type']=='mux_req' and e['owner']==2,lambda e:dict(e,epoch=e['epoch']^1),'request differs from checked batch'),
        ('response identity',lambda e:e['type']=='mux_rsp',lambda e:dict(e,generation=e['generation']^1),'response identity/ownership'),
        ('wait elapsed clocks',lambda e:e['type']=='batch_display_wait_end',lambda e:dict(e,cycles=e['cycles']+1),'wait elapsed cycles'),
        ('wait descriptor',lambda e:e['type']=='batch_display_wait_end',lambda e:dict(e,address=e['address']^16),'wait descriptor'),
        ('wait maximum',lambda e:e['type']=='batch_display_wait_end',lambda e:dict(e,maximum=e['maximum']+1),'wait maximum'),
        ('ACK witness',lambda e:e['type']=='batch_yield' and e['seen'],lambda e:dict(e,seen=0),'yield before response ACK')]
    results=[]
    for label,predicate,mutate,cause in tests:
        found=next((s,i,e) for s,segment in enumerate(segments) for i,e in enumerate(segment) if predicate(e))
        s,index,original=found;corrupted=mutate(original);oracle=GrantTrace(4)
        try:
            for i,e in enumerate(segments[s]):oracle.feed(corrupted if i==index else e)
            oracle.finish()
        except AssertionError as error:
            need(cause in str(error),'policy negative rejected for unrelated cause '+label+': '+str(error))
            results.append(dict(label=label,segment=s,index=index,original=original,corrupted=corrupted,rejected=True,reason=str(error)))
        else:raise AssertionError('policy oracle accepted corruption '+label)
    return results

def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--unit-only',action='store_true');args=ap.parse_args()
    reviewed=json.loads((HERE/'reviewed-source-hashes.json').read_text())
    for name,digest in reviewed.items():need(sha(ROOT/name)==digest,'reviewed tile-grant source differs: '+name)
    shared=control.prior.control.prior;shared.BASELINE=BASELINE;shared.REVIEWED=reviewed
    up,unit=shared.provenance('fpga/experiments/cu66-v91l-tile-grant/results.json','PASS_BOUNDED_REFERENCE_TILE_GRANTS')
    need(len(unit['modes'])==2 and {m['reference_lines'] for m in unit['modes']}=={1,4} and unit['gap_cycles']==8 and unit['payload_memory_bytes']==0 and not unit['hardware_tested'],'unit parameter/scope grid differs')
    tested=[];negatives=[];allchecks=0
    for mode in unit['modes']:
        raw=list(events(up.parent/mode['event_log']));checks=[e for e in raw if e['type']=='check']
        expected=1022 if mode['reference_lines']==1 else 1034
        need(len(checks)==mode['verdict']['checks']==expected and all(e['status']=='PASS' for e in checks),'directed unit entries incomplete')
        segments=normalized_unit(raw,mode['reference_lines']);need(len(segments)==20,'cold-reset scenario count differs')
        results=[]
        for trace in segments:
            oracle=GrantTrace(mode['reference_lines'])
            for event in trace:oracle.feed(event)
            results.append(oracle.finish())
        tested.append(dict(mode=mode['mode'],reference_lines=mode['reference_lines'],checks=expected,source_reviewed_POR_scenarios=20,policies=results))
        if mode['reference_lines']==4:negatives=policy_negatives(segments)
        allchecks+=expected
    frozen_audit=json.loads((OLD/'audit.json').read_text())
    inherited={**frozen_audit['inherited_checker_sha256'],str((OLD/'verify_results.py').relative_to(ROOT)):sha(OLD/'verify_results.py'),str((OLD/'lease_trace.py').relative_to(ROOT)):sha(OLD/'lease_trace.py')}
    need(inherited[str((OLD/'verify_results.py').relative_to(ROOT))]==frozen_audit['verifier_sha256'] and inherited[str((OLD/'lease_trace.py').relative_to(ROOT))]==frozen_audit['lease_verifier_sha256'],'frozen exact native/lease checker changed')
    result=dict(schema='cu66-v91l-tile-grant-independent-audit-v1',status='PASS_INDEPENDENT_BOUNDED_GRANT_UNIT',unit_report=str(up.relative_to(ROOT)),unit_report_sha256=sha(up),unit_modes=tested,directed_checks=allchecks,checker_negative_controls=negatives,reviewed_source_sha256=reviewed,inherited_checker_sha256=inherited,original_helper_sha256=frozen_audit['original_helper_sha256'],verifier_sha256=sha(Path(__file__)),grant_verifier_sha256=sha(HERE/'grant_trace.py'))
    if not args.unit_only:
        lp,live=shared.provenance('fpga/experiments/cu66-v91l-tile-grant-live/results.json','PASS_EXACT_BOUNDED_TILE_GRANT_NATIVE_OVERLAP')
        need(live['native_decode_display_overlap'] and live['all_external_memory_endpoints_rtl'] and not live['serial_live_commit_then_rgb'] and not live['scratch_memory_actors'] and not live['physical_preload'],'memory/pixel actor or serial workaround introduced')
        need(not live['physical_hardware_tested'] and not live['hardware_30fps_proven'] and not live['full_rtl_hud_decoder'] and not live['full_rtl_hud_overlay'] and not live['full_live_physical_service_complete'],'unsupported hardware/complete scope')
        need(len(live['modes'])==5 and {(m['seed'],m['t_ac_ns'],m['guard_mode']) for m in live['modes']}=={(s,t,False) for s in (912901,912902) for t in (2,7)}|{(912901,2,True)},'natural/guard grid incomplete')
        fixtures=native.expected_frames(lp.parent);goldens={}
        for line in gzip.open(lp.parent/'inputs/rgb_goldens.tsv.gz','rt'):
            ident,data=line.rstrip().split('\t')
            if ident in ('actual_001','actual_006'):goldens[ident]=bytes.fromhex(data)
        modes=[]
        for mode in live['modes']:
            audited=control.audit_mode(lp.parent,mode,fixtures,goldens);policy=audited['physical']['reference_grant_policy']
            need(policy['limit']==4 and policy['groups_started']==7806 and policy['continuations']==23418 and policy['reference_requests']==policy['reference_responses']==31224,'native reference schedule not exactly four chunks per source tile')
            need(policy['max_reference_lines_per_grant']==4 and policy['display_requests']==64800 and policy['group_request_histogram']=={4:7806} and policy['yield_reasons']=={0:7806},'native credit/yield/display schedule differs')
            modes.append(audited);print('AUDITED_BOUNDED_GRANT',mode['seed'],mode['t_ac_ns'],mode['guard_mode'],flush=True)
        result.update(status='PASS_INDEPENDENT_BOUNDED_REFERENCE_GRANTS',live_report=str(lp.relative_to(ROOT)),live_report_sha256=sha(lp),live_modes=modes,exact_native_RGB_outputs=10,distinct_native_source_images=2,rtl_sha_jobs=10250,
            scope='One scheduling change, four contiguous16B reference chunks per bounded source-tile turn. Frozen exact native/pin/validation/display-lease checks retained, 4 natural modes and separate guarded source-publication test; no codec-byte/quality/hardware cadence claim.')
    (HERE/('audit-unit.json' if args.unit_only else 'audit.json')).write_text(json.dumps(result,indent=2)+'\n');print(result['status'],flush=True)
if __name__=='__main__':main()
