#!/usr/bin/env python3
"""Independently audit frozen recipes, LUT constants and all retained RTL truth rows."""
import gzip,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
AREA=ROOT/'experiments/python-gamebub-v106/math'
FPGA=ROOT/'fpga/experiments/cu66-v106-math'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    summary_path=AREA/'results.json';summary=json.loads(summary_path.read_text());rp=ROOT/summary['selected_report'];r=json.loads(rp.read_text())
    assert summary['status']==r['status']=='PASS' and {k:v for k,v in summary.items() if k!='selected_report'}==r
    assert r['actual_RTL_run'] and r['frozen_after_focused_PASS'] and r['strict_warnings'] and not r['assertions_disabled_or_downgraded']
    for p,h in r['source_sha256'].items():assert sha(ROOT/p)==h
    for p,h in r['artifacts_sha256'].items():assert sha(rp.parent/p)==h
    assert len(r['production'])==6
    helpers={};source_contracts=[]
    for source in r['production']:
        candidate=ROOT/source['path'];recipe_path=ROOT/source['recipe_path'];recipe=json.loads(recipe_path.read_text())
        assert sha(candidate)==source['sha256']==recipe['candidate_sha256'] and sha(recipe_path)==source['recipe_sha256']
        assert recipe['schema']=='v106-edit-recipe-v1' and len(recipe['edits'])==1
        original=ROOT/recipe['original_path'];assert sha(original)==recipe['original_sha256']
        edit=recipe['edits'][0];before=original.read_text()
        assert edit['expected_occurrences']==1 and before.count(edit['before'])==1
        assert before.replace(edit['before'],edit['after'],1)==candidate.read_text()
        if recipe['variant'] in helpers:assert helpers[recipe['variant']]==edit['after']
        helpers[recipe['variant']]=edit['after'];source_contracts.append(source)
    banks={}
    for bank,text in re.findall(r"6'd(\d+):begin(.*?)end",helpers['lut'],re.S):
        b=int(bank);assert b not in banks
        banks[b]={int(bit):int(value,16) for bit,value in re.findall(r"lut(\d+)=64'h([0-9a-f]{16});",text)}
        assert set(banks[b])==set(range(11))
    assert set(banks)==set(range(64))
    digest=hashlib.sha256();seen=set();wrap=0;largest=0
    trace=rp.parent/'trace.tsv.gz'
    with gzip.open(trace,'rb') as stream:
        for line in stream:
            digest.update(line);plane,tile,*actual=map(int,line.split())
            assert plane in range(4) and tile in range(8192) and (plane,tile) not in seen
            seen.add((plane,tile));row,col=divmod(tile,90)
            raw=(row//2)*45+col//2;expected=(raw if plane==0 else tile)%2048
            bank=tile//128;index=(tile%128)//2
            lut=sum(((banks[bank][bit]>>index)%2)*(2**bit) for bit in range(11)) if plane==0 else tile%2048
            assert actual==[expected]*3 and lut==expected
            if plane==0:wrap+=raw>=2048;largest=max(largest,raw)
    assert len(seen)==32768 and wrap==44 and largest==2069
    assert digest.hexdigest()==r['raw_trace_sha256'] and r['trace_replay']['rows']==32768
    assert r['terminal_verdict']==dict(cases=32768,planes=4,status='TEST_PASS',tile_inputs_per_plane=8192)
    cmd=next(c['argv'] for c in r['commands'] if '--cc' in c['argv'])
    assert '--assert' in cmd and '-Wall' in cmd and '-std=c++17 -O2 -Wall -Wextra -Werror' in cmd
    assert 'timeout' in cmd and '300s' in cmd and cmd[cmd.index('-j')+1]=='2'
    assert 'Verilator 5.020' in (rp.parent/'verilator.log').read_text() and '%Warning-' not in (rp.parent/'compile.log').read_text()
    out=dict(schema='v106-math-independent-trace-audit-v1',status='PASS',
        auditor=dict(path=str(Path(__file__).relative_to(ROOT)),sha256=sha(Path(__file__))),
        selected_receipt=dict(path=str(rp.relative_to(ROOT)),sha256=sha(rp)),
        selected_summary=dict(path=str(summary_path.relative_to(ROOT)),sha256=sha(summary_path)),
        trace_sha256=sha(trace),raw_trace_sha256=digest.hexdigest(),production=source_contracts,
        rows=len(seen),plane_values=4,tile_values_per_plane=8192,LUT_constants_reconstructed=64*11,
        Y_return_wrap_inputs=wrap,largest_untruncated_Y_value=largest,
        limits=['Exhaustive two-state combinational equivalence only; integrated cycles/guards and native timing are separate checks.'])
    (AREA/'trace-audit.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print('V106_MATH_AUDIT PASS',len(seen))
if __name__=='__main__':main()
