#!/usr/bin/env python3
"""Reaudit selected alias DAGs with the frozen independent V87 auditor."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v88'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    selected=AREA/'alias/probe.json';report=json.loads(selected.read_text())
    assert report['status']=='PASS_SELECTED_CAUSAL_ALIAS_REPLAY' and report['schedules']==len(report['rows'])==10
    auditor_path=ROOT/'scripts/cu66-v87/audit_coupled.py'
    spec=importlib.util.spec_from_file_location('v88_independent_alias_graph_audit',auditor_path)
    audit=importlib.util.module_from_spec(spec);sys.modules[spec.name]=audit;spec.loader.exec_module(audit)
    pins={str(selected.relative_to(ROOT)):sha(selected),str(auditor_path.relative_to(ROOT)):sha(auditor_path),
          str(Path(__file__).resolve().relative_to(ROOT)):sha(Path(__file__).resolve())}
    results=[]
    for row in report['rows']:
        p=ROOT/row['witness'];assert sha(p)==row['witness_sha256'];pins[str(p.relative_to(ROOT))]=sha(p)
        with gzip.open(p,'rt') as f:w=json.load(f)
        result=audit.verify(w['workload'],w['result']['timeline'],w['capacities'],w['windows'])
        assert result['timeline_sha256']==row['timeline_sha256']
        assert result['finish_cycles']==w['result']['finish_cycles']
        by_id={r['id']:r for r in w['result']['timeline']}
        assert by_id[w['workload']['alias_trace']['decode_complete']]['finish']/100000==row['conditional_decode_ms']
        assert result['finish_cycles']/100000==row['conditional_base_gather_complete_ms']
        assert result['resource_work_cycles']['memory']==row['memory_work_cycles']
        if row['alias']:
            jobs=w['workload']['jobs'];stats=w['workload']['alias_trace']
            # Publication and descriptor visibility must follow every actual
            # provisional data store, including stores added to old elisions.
            links={j['id']:j['deps'] for j in jobs};ancestors=set();pending=[stats['decode_complete']]
            while pending:
                i=pending.pop()
                if i not in ancestors:ancestors.add(i);pending.extend(links[i])
            assert all(j['id'] in ancestors for j in jobs if j['kind'] in ('canonical_write','alias_descriptor_valid_write'))
            assert sum(j.get('alias_added',False) for j in jobs)==stats['added_nonCOPY_store_tiles']
        results.append(dict(cohort=row['cohort'],fid=row['fid'],configuration=row['configuration'],alias=row['alias'],audit=result))
    assert report['unique_sources']==len({(r['cohort'],r['fid']) for r in report['rows']})==4
    assert any(r['alias'] and r['alias_changes']['added_nonCOPY_store_tiles']>0 for r in report['rows'])
    assert pins=={name:sha(ROOT/name) for name in pins}
    output=dict(schema='cu66-v88-independent-alias-probe-audit-v1',status='PASS_INDEPENDENT_ALIAS_DAG_AND_CONSUMER_AUDIT',
                source_sha256=pins,unique_sources=4,schedules=10,results=results,
                scope='Retained task DAG, dependency/resource/credit/context/publication verification. Actual decoder arithmetic and physical hardware timing remain unqualified.')
    (AREA/'alias-probe-audit.json').write_text(json.dumps(output,indent=2)+'\n')
    print(output['status'],'sources=4 schedules=10')


if __name__=='__main__':main()
