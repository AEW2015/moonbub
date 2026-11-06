#!/usr/bin/env python3
"""Mutate a qualified witness to check independent rejection of model gaps."""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
AUDITOR=ROOT/'scripts/cu66-v87/audit_coupled.py'


def main():
    p=argparse.ArgumentParser();p.add_argument('witness');p.add_argument('--output',required=True);args=p.parse_args()
    path=Path(args.witness);d=json.loads(gzip.decompress(path.read_bytes()))
    work=d.get('workload',d.get('work'));timeline=d['result']['timeline'];caps=d['capacities']
    windows=d.get('windows',d.get('config',{}).get('windows'))
    spec=importlib.util.spec_from_file_location('independent_cu87_audit',AUDITOR);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    positive=module.verify(work,timeline,caps,windows)
    by_id={j['id']:j for j in work['jobs']};front=work['frontend'];checks=[]
    def check(label,modify,restore,custom_windows=windows):
        modify()
        try:
            try:module.verify(work,timeline,caps,custom_windows)
            except (AssertionError,ValueError,KeyError,TypeError)as exc:
                checks.append(dict(name=label,status='PASS_REJECT',exception=type(exc).__name__,detail=str(exc)))
            else:raise RuntimeError('auditor accepted mutation '+label)
        finally:restore()
    setup=by_id[front['setups'][front['window']]];old=list(setup['deps']);release=front['consumers'][0]
    check('consumer_release_edge_removed',lambda:setup.update(deps=[x for x in old if x!=release]),lambda:setup.update(deps=old))
    check('coefficient_released_on_emitter',lambda:setup.update(deps=[x for x in old if x!=release]+[front['emits'][0]]),lambda:setup.update(deps=old))
    record=work['credits']['constraints']['coefficients'][0];consumer=record['consumer'];producer=record['producer']
    check('declared_consumer_replaced_by_emit',lambda:record.update(consumer=front['emits'][0]),lambda:record.update(consumer=consumer))
    check('declared_producer_delayed_until_emit',lambda:record.update(producer=front['emits'][0]),lambda:record.update(producer=producer))
    fetched=next(j for j in work['jobs']if j['kind']=='context_fetch' and j['tile']==1 and j['context']==0)
    prev=next(j['id']for j in work['jobs']if j['kind']=='context_compute' and j['tile']==0 and j['context']==0)
    old_fetch=list(fetched['deps'])
    check('probability_context_order_removed',lambda:fetched.update(deps=[x for x in old_fetch if x!=prev]),lambda:fetched.update(deps=old_fetch))
    first=by_id[front['setups'][0]];old_first=list(first['deps']);group=work['groups'][first['group']]['start']
    check('group_admission_edge_removed',lambda:first.update(deps=[x for x in old_first if x!=group]),lambda:first.update(deps=old_first))
    next_id=max(by_id)+1
    orphan=dict(id=next_id,deps=[],resource=None,duration=0,kind='unfenced_probe')
    orphan_time=dict(id=next_id,start=0,finish=0,resource=None)
    check('publication_omits_operation',lambda:(work['jobs'].append(orphan),timeline.append(orphan_time)),lambda:(work['jobs'].pop(),timeline.pop()))
    assert positive['resource_peaks']['arithmetic']>1
    lanes=caps['arithmetic']
    check('arithmetic_resource_oversubscribed',lambda:caps.update(arithmetic=1),lambda:caps.update(arithmetic=lanes))
    check('memory_reserved_window_overlap',lambda:None,lambda:None,dict(period=10000,blocked=[(0,10000)]))
    # A repeat positive proves all in-place changes were restored.
    assert module.verify(work,timeline,caps,windows)==positive
    output=dict(schema='cu66-v87-auditor-mutation-checks-v1',status='PASS',
                witness=str(path),witness_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                auditor_sha256=hashlib.sha256(AUDITOR.read_bytes()).hexdigest(),
                test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                positive_audit=positive,rejected_mutations=checks,checks=len(checks),repeat_positive='PASS',
                scope='Nine targeted graph/resource/credit mutations on one native-source witness, not a decoder or hardware fault campaign.')
    Path(args.output).write_text(json.dumps(output,indent=2)+'\n')
    print('V87_INDEPENDENT_AUDITOR_MUTATIONS_PASS checks='+str(len(checks)))

if __name__=='__main__':main()
