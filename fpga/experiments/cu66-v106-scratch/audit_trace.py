#!/usr/bin/env python3
"""Offline independent scratch position and owner-qualified trace audit."""
import gzip,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=ROOT/'experiments/python-gamebub-v106/scratch';FPGA=ROOT/'fpga/experiments/cu66-v106-scratch'
# Literal raster-to-zigzag inverse permutation; no production helper/runner imports.
Z=(0,1,5,6,14,15,27,28,2,4,7,13,16,26,29,42,3,8,12,17,25,30,41,43,9,11,18,24,31,40,44,53,10,19,23,32,39,45,52,54,20,22,33,38,46,51,55,60,21,34,37,47,50,56,59,61,35,36,48,49,57,58,62,63)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pos(w):return (w>>19)*64+Z[(w>>13)&63]
def main():
    sp=AREA/'results.json';s=json.loads(sp.read_text());rp=ROOT/s['selected_report'];r=json.loads(rp.read_text())
    assert s['status']==r['status']=='PASS' and {k:v for k,v in s.items() if k!='selected_report'}==r
    assert r['actual_RTL_run'] and r['strict_warnings'] and not r['assertions_disabled_or_downgraded'] and r['frozen_after_focused_PASS']
    for p,h in r['source_sha256'].items():assert sha(ROOT/p)==h,p
    for p,h in r['artifacts_sha256'].items():assert sha(rp.parent/p)==h,p
    recp=FPGA/'edit-recipe.json';rec=json.loads(recp.read_text());original=ROOT/rec['original_path'];candidate=ROOT/rec['candidate_path'];text=original.read_text()
    assert rec['schema']=='v106-edit-recipe-v1' and len(rec['edits'])==9 and sha(original)==rec['original_sha256']==r['baseline_plan_sha256']=='c46f01765b79bd35929183d8475287c2b71e93c289371f0e3f212b320b175e48'
    for e in rec['edits']:
        assert text.count(e['before'])==e['expected_occurrences']==1;text=text.replace(e['before'],e['after'],1)
    assert text==candidate.read_text() and sha(candidate)==rec['candidate_sha256']==r['candidate']['sha256'] and sha(recp)==r['candidate']['recipe_sha256']
    assert original.read_text().split(');',1)[0]==candidate.read_text().split(');',1)[0]
    a=json.loads((FPGA/'adapter.json').read_text())
    for n,p in [('original',original),('candidate',candidate)]:
        t=(FPGA/('scratch_'+n+'.sv')).read_text().replace('module scratch_'+n+' (','module packed_scratch_v91g2 (',1)
        assert t.replace(a['extra_ports'],'\n);',1).replace(a['assignments'][n],'',1)==p.read_text()
    hist=(ROOT/'fpga/experiments/cu66-v91g2/tb_scratch_hazards.cpp').read_text().replace('Vpacked_scratch_v91g2','Vscratch_probe').replace('int main(int argc,char** argv)','int historical_hazards_main(int argc,char** argv)').replace('d.eval();','d.eval();need(!d.mismatch,"historical whole scratch mismatch");')
    assert hist==(FPGA/'historical_hazards.cpp').read_text()
    cmd=next(c['argv'] for c in r['commands'] if '--cc' in c['argv'])
    assert '--assert' in cmd and '-Wall' in cmd and '-std=c++17 -O2 -Wall -Wextra -Werror' in cmd and '300s' in cmd and '--kill-after=5s' in cmd and cmd[cmd.index('-j')+1]=='2'
    assert 'Verilator 5.020' in (rp.parent/'verilator.log').read_text() and '%Warning-' not in (rp.parent/'compile.log').read_text()
    assert sorted(Z)==list(range(64))
    for upper in range(1<<19):
        for low in (0,8191):assert pos((upper<<13)|low)==((upper>>6)<<6)|Z[upper&63]
    for band in range(4):
        for raster in range(64):
            rank=Z[raster];a0=(raster==0 if band==0 else 1<=rank<6 if band==1 else 6<=rank<21 if band==2 else rank>=21);b0=(rank==0 if band==0 else 1<=rank<6 if band==1 else 6<=rank<21 if band==2 else rank>=21);assert a0==b0
    runs=[]
    for run in r['runs']:
        seed=run['seed'];path=rp.parent/f'trace-{seed}.jsonl.gz';digest=hashlib.sha256();cache=reads=heads=checks=0;bankmask=offsetmask=0;last=-1
        with gzip.open(path,'rb') as f:
            for line in f:
                digest.update(line);v=json.loads(line);assert v['clock']>=last;last=v['clock']
                if v['kind']=='cache':
                    assert v['state'] in (11,20,22,27) and len(v['data'])==16 and len(v['positions'])==64 and 0<=v['valid']<16
                    for bank in range(4):
                        if v['valid']&(1<<bank):
                            bankmask|=1<<bank;raw=b''.join(x.to_bytes(4,'little') for x in v['data'][bank*4:bank*4+4])
                            for offset in range(16):
                                word=int.from_bytes(raw[offset:offset+4].ljust(4,b'\0'),'little');assert v['positions'][bank*16+offset]==pos(word);checks+=1;offsetmask|=1<<offset
                    cache+=1
                else:
                    assert v['kind']=='read' and 1<=v['band']<=3 and 0<=v['segment']<4 and 0<=v['address']<=0xffffffff and v['position']==pos(v['word']);reads+=1
                    if v['cursor']:assert v['head_position']==pos(v['head_word']);heads+=1
        verdict=run['verdict'];assert cache==verdict['cache_events']==1937 and reads==verdict['live_reads'] and heads==verdict['head_compares']
        assert digest.hexdigest()==run['trace_replay']['raw_sha256'] and bankmask==15 and offsetmask==65535
        assert verdict['full_transactions']==72 and verdict['corrupt_response_cases']==128 and verdict['read_owner_cases']==4 and verdict['dense_values']==18432 and verdict['requests']==verdict['acks']
        h=run['historical_verdict'];assert h['directed_checks']==9 and h['edges']==311 and h['physical_accepts']==h['physical_acks']==8
        runs.append(dict(seed=seed,trace=dict(path=str(path.relative_to(ROOT)),sha256=sha(path),raw_sha256=digest.hexdigest()),clock_edges=verdict['clock_edges'],cache_events=cache,offline_position_checks=checks,live_reads=reads,head_compares=heads,clocked_position_checks=verdict['cache_position_checks'],full_transactions=72,corrupt_response_cases=128,read_owner_cases=4,historical_edges=311,historical_hazards=9))
    out=dict(schema='v106-scratch-independent-trace-audit-v1',status='PASS',auditor=dict(path=str(Path(__file__).relative_to(ROOT)),sha256=sha(Path(__file__))),selected_receipt=dict(path=str(rp.relative_to(ROOT)),sha256=sha(rp)),selected_summary=dict(path=str(sp.relative_to(ROOT)),sha256=sha(sp)),candidate=r['candidate'],all_upper19_geometries=524288,band_rank_pairs=256,runs=runs,total_clock_edges=sum(v['clock_edges']+v['historical_edges'] for v in runs),total_cache_events=sum(v['cache_events'] for v in runs),total_live_reads=sum(v['live_reads'] for v in runs),total_head_compares=sum(v['head_compares'] for v in runs),limits=['Offline replay covers all retained response snapshots and each live sparse record; clocked bench additionally checks all valid positions before and after every edge.','Whole original/candidate production public comparison plus original accepted-write hazards and scratch transaction oracle; not formal arbitrary internal state equivalence or full encoded-packet integration.','New mem_rsp_data-to-position-register capture requires real parent input-delay timing. No board100MHz/CDC/hardware performance claim.'])
    (AREA/'trace-audit.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print('V106_SCRATCH_TRACE_AUDIT PASS',out['total_clock_edges'],out['total_cache_events'],out['total_live_reads'])
if __name__=='__main__':main()
