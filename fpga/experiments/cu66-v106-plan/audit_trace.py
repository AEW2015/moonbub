#!/usr/bin/env python3
"""Offline direct modular-prefix replay of frozen production-module PLAN evidence."""
import gzip,hashlib,itertools,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=ROOT/'experiments/python-gamebub-v106/plan';FPGA=ROOT/'fpga/experiments/cu66-v106-plan';MASK=2**32-1

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    summary_path=AREA/'results.json';s=json.loads(summary_path.read_text());rp=ROOT/s['selected_report'];r=json.loads(rp.read_text())
    assert s['status']==r['status']=='PASS' and {k:v for k,v in s.items() if k!='selected_report'}==r
    assert r['actual_RTL_run'] and r['strict_warnings'] and not r['assertions_disabled_or_downgraded'] and r['frozen_after_focused_PASS']
    for p,h in r['source_sha256'].items():assert sha(ROOT/p)==h
    for p,h in r['artifacts_sha256'].items():assert sha(rp.parent/p)==h
    recipe_path=FPGA/'edit-recipe.json';recipe=json.loads(recipe_path.read_text());text=(ROOT/recipe['original_path']).read_text()
    assert recipe['schema']=='v106-edit-recipe-v1' and len(recipe['edits'])==2
    assert sha(ROOT/recipe['original_path'])==recipe['original_sha256']
    for e in recipe['edits']:
        assert e['expected_occurrences']==text.count(e['before'])==1;text=text.replace(e['before'],e['after'],1)
    assert text==(ROOT/recipe['candidate_path']).read_text() and sha(ROOT/recipe['candidate_path'])==recipe['candidate_sha256']==r['candidate']['sha256']
    assert sha(recipe_path)==r['candidate']['recipe_sha256']
    adapter=json.loads((FPGA/'adapter.json').read_text())
    for name,source in [('original',ROOT/recipe['original_path']),('candidate',ROOT/recipe['candidate_path'])]:
        actual=(FPGA/('plan_'+name+'.sv')).read_text().replace('module plan_'+name+' (','module packed_scratch_v91g2 (',1)
        assert actual.replace(adapter['extra_ports'],'\n);',1).replace(adapter['assignments'],'',1)==source.read_text()
    # Complete bit-level compressor truth table; modular word equivalence follows by weighted sum.
    for a,b,c in itertools.product(range(2),repeat=3):assert a+b+c==(a^b^c)+2*((a&b)|(a&c)|(b&c))
    trace=rp.parent/'trace.tsv.gz';digest=hashlib.sha256();blocks_seen=set();rows=valid=high=0
    align=lambda n:((n&MASK)+15)&0xfffffff0
    with gzip.open(trace,'rb') as stream:
        for line in stream:
            digest.update(line);b,raw,c1,c2,c3,*actual=map(int,line.split())
            assert 0<=b<131072 and raw in (0,1) and all(0<=c<=MASK for c in (c1,c2,c3))
            p1=(32+align(2*b))&MASK;p2=(p1+align(4*c1))&MASK;p3=(p2+align(4*c2))&MASK
            used=(32+128*b)&MASK if raw else (p3+align(4*c3))&MASK
            assert actual==[p1,p2,p3,used]
            invalid=b==0 or b>8192 or c1>5*b or c2>15*b or c3>43*b or (raw and (c1 or c2 or c3)) or used>262144
            valid+=not invalid;high+=any(c>=2**30 for c in (c1,c2,c3));blocks_seen.add(b);rows+=1
    assert rows==r['model']['rows']==r['trace_replay']['rows']==290816
    assert valid==r['model']['valid_plan_inputs']==6132 and high==r['model']['high_count_inputs']==165393
    assert blocks_seen==set(range(131072))
    assert digest.hexdigest()==r['raw_trace_sha256']==r['trace_replay']['raw_sha256']==r['model']['vectors']['raw_sha256']
    vectors=ROOT/r['model']['vectors']['path'];assert sha(vectors)==r['model']['vectors']['sha256'] and sha(vectors)==sha(trace)
    verdicts=r['terminal_verdicts'];assert verdicts[0]==dict(type='plan_verdict',status='TEST_PASS',rows=290816,clocked_begin_cases=9088,priority_checks=1)
    assert verdicts[1]==dict(type='scratch_hazards_verdict',status='TEST_PASS',directed_checks=9,edges=311,physical_accepts=8,physical_acks=8)
    cmd=next(c['argv'] for c in r['commands'] if '--cc' in c['argv'])
    assert '--assert' in cmd and '-Wall' in cmd and '-std=c++17 -O2 -Wall -Wextra -Werror' in cmd and '300s' in cmd and '--kill-after=5s' in cmd and cmd[cmd.index('-j')+1]=='2'
    assert 'Verilator 5.020' in (rp.parent/'verilator.log').read_text() and '%Warning-' not in (rp.parent/'compile.log').read_text()
    out=dict(schema='v106-plan-independent-trace-audit-v1',status='PASS',
        auditor=dict(path=str(Path(__file__).relative_to(ROOT)),sha256=sha(Path(__file__))),
        selected_receipt=dict(path=str(rp.relative_to(ROOT)),sha256=sha(rp)),
        selected_summary=dict(path=str(summary_path.relative_to(ROOT)),sha256=sha(summary_path)),
        trace_sha256=sha(trace),raw_trace_sha256=digest.hexdigest(),candidate=r['candidate'],
        prefix_rows=rows,all17bit_block_values=len(blocks_seen),valid_plan_inputs=valid,high_count_inputs=high,
        clocked_begin_cases=9088,priority_checks=1,accepted_write_hazard_checks=9,public_port_count=len(json.loads((FPGA/'ports.json').read_text())),
        limits=['Offline arithmetic trace replay; clocked error/owner assertions are bound by retained complete-module bench and terminal verdicts.',
            'Universal CSA bit identity plus deterministic tests; not exhaustive over all3x32bit count combinations.',
            'No routed timing, hardware FPS or complete validated latency qualification.'])
    (AREA/'trace-audit.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print('V106_PLAN_TRACE_AUDIT PASS',rows)
if __name__=='__main__':main()
