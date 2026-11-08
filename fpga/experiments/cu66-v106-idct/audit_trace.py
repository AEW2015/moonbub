#!/usr/bin/env python3
"""Independently audit retained IDCT tiles, signed products, FSM and cycle traces."""
import gzip,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
AREA=ROOT/'experiments/python-gamebub-v106/idct'
FPGA=ROOT/'fpga/experiments/cu66-v106-idct'
HALF=((5793,5793,5793,5793),(8035,6811,4551,1598),(7568,3135,-3135,-7568),(6811,-1598,-8035,-4551),(5793,-5793,-5793,5793),(4551,-8035,1598,6811),(3135,-7568,7568,-3135),(1598,-4551,6811,-8035))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def signed(v,b):return v-(1<<b) if v&(1<<(b-1)) else v
def unpack(v,b):return [signed((int(v,16)>>(b*i))&((1<<b)-1),b) for i in range(64)]
def matrix(tile):
    if any(not -522240<=v<=522240 for v in tile):return [0]*64,1
    # Separate direct 8x8 matrix, not the mirrored hardware schedule or its tasks.
    b=[[HALF[k][p] if p<4 else (-1 if k&1 else 1)*HALF[k][7-p] for p in range(8)] for k in range(8)]
    m=[[(sum(tile[8*r+k]*b[k][p] for k in range(8))+8192)//16384 for p in range(8)] for r in range(8)]
    return [(sum(m[k][c]*b[k][r] for k in range(8))+8192)//16384 for r in range(8) for c in range(8)],0

def main():
    sp=AREA/'results.json';s=json.loads(sp.read_text());rp=ROOT/s['selected_report'];r=json.loads(rp.read_text())
    assert s['status']==r['status']=='PASS' and {k:v for k,v in s.items() if k!='selected_report'}==r
    assert r['actual_RTL_run'] and r['strict_warnings'] and not r['assertions_disabled_or_downgraded'] and r['frozen_after_focused_PASS']
    for p,h in r['source_sha256'].items():assert sha(ROOT/p)==h,p
    for p,h in r['artifacts_sha256'].items():assert sha(rp.parent/p)==h,p
    recp=FPGA/'edit-recipe.json';rec=json.loads(recp.read_text());original=ROOT/rec['original_path'];candidate=ROOT/rec['candidate_path'];text=original.read_text()
    assert rec['schema']=='v106-edit-recipe-v1' and len(rec['edits'])==11 and sha(original)==rec['original_sha256']
    for e in rec['edits']:
        assert text.count(e['before'])==e['expected_occurrences']==1;text=text.replace(e['before'],e['after'],1)
    assert text==candidate.read_text() and sha(candidate)==rec['candidate_sha256']==r['candidate']['sha256'] and sha(recp)==r['candidate']['recipe_sha256']
    assert original.read_text().split(');',1)[0]==candidate.read_text().split(');',1)[0]
    adapter=json.loads((FPGA/'adapter.json').read_text())
    for n,p in [('original',original),('candidate',candidate)]:
        t=(FPGA/('idct_'+n+'.sv')).read_text().replace('module idct_'+n+' (','module cu66_idct8x8 (',1)
        assert t.replace(adapter['extra_ports'],'\n);',1).replace(adapter['assignments'],'',1)==p.read_text()
    cmd=next(c['argv'] for c in r['commands'] if '--cc' in c['argv'])
    assert '--assert' in cmd and '-Wall' in cmd and '-std=c++17 -O2 -Wall -Wextra -Werror' in cmd and '300s' in cmd and '--kill-after=5s' in cmd and cmd[cmd.index('-j')+1]=='2'
    assert 'Verilator 5.020' in (rp.parent/'verilator.log').read_text() and '%Warning-' not in (rp.parent/'compile.log').read_text()
    vector_path=AREA/'vectors.hex.gz';raw=gzip.decompress(vector_path.read_bytes());model=json.loads((AREA/'model.json').read_text())
    assert sha(vector_path)==model['vectors']['sha256'] and hashlib.sha256(raw).hexdigest()==model['vectors']['raw_sha256']
    lines=raw.decode().splitlines();historic=(ROOT/'fpga/experiments/cu66-v69/inverse/tiles.hex').read_text().splitlines();assert lines[:3471]==historic and len(lines)==4303
    for line in lines:
        ident,tile,output,error=line.split();expected,bad=matrix(unpack(tile,20));assert expected==unpack(output,24) and bad==int(error),ident
    runs=[]
    for run in r['runs']:
        seed=run['seed'];path=rp.parent/f'trace-{seed}.jsonl.gz';digest=hashlib.sha256();products=[0]*8;cycles=0;rows=muls=0;states=set();guards=set();prior=None
        with gzip.open(path,'rb') as f:
            for line in f:
                digest.update(line);v=json.loads(line);state=v['state'];k=v['k'];g=v['group'];kill=bool(v['rst'] or v['abort'])
                assert v['clock']==rows and 0<=state<10 and 0<=k<8 and 0<=g<4 and bool(v['kill'])==kill
                assert bool(v['mul'])==(state in (1,3,5,7)) and bool(v['in_ready'])==(state==0 and not kill)
                if prior:
                    assert prior['next_state']==state
                    if prior['kill']:assert k==g==0
                    elif prior['state'] in (1,3,5,7):assert (k,g)==(prior['k'],prior['group'])
                    elif prior['state'] in (2,4):assert (k,g)==((0 if prior['k']==7 else prior['k']+1),(0 if prior['k']==7 and prior['group']==3 else prior['group']+1 if prior['k']==7 else prior['group']))
                assert v['basis']==[HALF[k][i%4] for i in range(8)]
                assert all(-(1<<23)<=x<(1<<23) for x in v['samples'])
                if state not in (1,3,5,7):assert v['samples']==[0]*8
                if kill:products=[0]*8;cycles=0;expected_state=0;guards.add((state,v['rst']+2*v['abort']))
                else:
                    if v['mul']:products=[x*y for x,y in zip(v['samples'],v['basis'])];muls+=1
                    if state==0 and v['in_valid'] and v['in_ready']:cycles=0
                    elif state not in (0,9):cycles=(cycles+1)&0xffffffff
                    expected_state={1:2,3:4,5:6,6:7,7:8,8:9}.get(state)
                    if state==0:assert v['next_state'] in ((1,5,9) if v['in_valid'] else (0,));expected_state=v['next_state']
                    elif state==2:expected_state=3 if k==7 and g==3 else 1
                    elif state==4:expected_state=9 if k==7 and g==3 else 3
                    elif state==9:expected_state=0 if v['out_ready'] else 9
                assert v['products']==products and v['cycles']==cycles and v['next_state']==expected_state
                assert all(-(1<<37)<=x<(1<<37) for x in products)
                states.add(state);prior=v;rows+=1
        verdict=run['verdict'];assert states==set(range(10)) and {(state,guard) for state in range(10) for guard in (1,2,3)}<=guards
        assert digest.hexdigest()==run['trace_replay']['raw_sha256'] and rows==verdict['clock_edges'] and muls==verdict['multiply_edges']==122024
        assert verdict['tiles']==4303 and verdict['completed_tiles']==4333 and verdict['directed_abort_reset_cases']==30 and verdict['states']==verdict['abort_state_mask']==1023
        runs.append(dict(seed=seed,trace=dict(path=str(path.relative_to(ROOT)),sha256=sha(path),raw_sha256=digest.hexdigest()),clock_edges=rows,multiply_edges=muls,states=10,all_state_guard_pairs=30,tiles=4303,completed_tiles=4333))
    out=dict(schema='v106-idct-independent-trace-audit-v1',status='PASS',auditor=dict(path=str(Path(__file__).relative_to(ROOT)),sha256=sha(Path(__file__))),selected_receipt=dict(path=str(rp.relative_to(ROOT)),sha256=sha(rp)),selected_summary=dict(path=str(sp.relative_to(ROOT)),sha256=sha(sp)),candidate=r['candidate'],independent_integer_gold_tiles=4303,historic_tiles=3471,runs=runs,total_clock_edges=sum(x['clock_edges'] for x in runs),total_multiply_edges=sum(x['multiply_edges'] for x in runs),limits=['Reachable clocked two-state complete production comparison and independent integer/product/cycle oracle; not formal arbitrary internal state equivalence.','Trace replays all products, states and public active_cycles. Complete output vectors checked by frozen actual C++ bench; offline auditor independently recomputes all4303 vector goldens.','No native mapping/timing or hardware performance claim.'])
    (AREA/'trace-audit.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print('V106_IDCT_TRACE_AUDIT PASS',out['total_clock_edges'])
if __name__=='__main__':main()
