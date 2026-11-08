#!/usr/bin/env python3
"""Independently replay all prepared counter edges and audit frozen telemetry evidence."""
import gzip,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=ROOT/'experiments/python-gamebub-v106/telemetry';FPGA=ROOT/'fpga/experiments/cu66-v106-telemetry';MASK=2**64-1

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    sp=AREA/'results.json';summary=json.loads(sp.read_text());rp=ROOT/summary['selected_report'];r=json.loads(rp.read_text())
    assert summary['status']==r['status']=='PASS' and {k:v for k,v in summary.items() if k!='selected_report'}==r
    assert r['actual_RTL_run'] and r['strict_warnings'] and not r['assertions_disabled_or_downgraded'] and r['frozen_after_focused_PASS']
    for p,h in r['source_sha256'].items():assert sha(ROOT/p)==h
    for p,h in r['artifacts_sha256'].items():assert sha(rp.parent/p)==h
    recipe_path=FPGA/'edit-recipe.json';recipe=json.loads(recipe_path.read_text());original=ROOT/recipe['original_path'];candidate=ROOT/recipe['candidate_path']
    assert recipe['schema']=='v106-edit-recipe-v1' and len(recipe['edits'])==3 and sha(original)==recipe['original_sha256']
    text=original.read_text()
    for e in recipe['edits']:
        assert text.count(e['before'])==e['expected_occurrences']==1;text=text.replace(e['before'],e['after'],1)
    assert text==candidate.read_text() and sha(candidate)==recipe['candidate_sha256']==r['candidate']['sha256'] and sha(recipe_path)==r['candidate']['recipe_sha256']
    assert original.read_text()[:original.read_text().index(');')+2]==candidate.read_text()[:candidate.read_text().index(');')+2]
    for name,source in [('original',original),('candidate',candidate)]:
        assert (FPGA/('telemetry_'+name+'.sv')).read_text().replace('module telemetry_'+name+' #','module br88_pipeline_v91h #',1)==source.read_text()
    historical=ROOT/'fpga/experiments/cu66-v91h/tb_pipeline.cpp'
    adapted=historical.read_text().replace('Vbr88_pipeline_v91h','Vtelemetry_probe').replace('int main(int argc,char** argv)','int historical_pipeline_main(int argc,char** argv)').replace('        d.clk=1;d.eval();','        telemetry_pre(d);d.clk=1;d.eval();telemetry_post(d);',1)
    assert adapted==(FPGA/'historical_pipeline.cpp').read_text()
    cmd=next(c['argv'] for c in r['commands'] if '--cc' in c['argv'])
    assert '--assert' in cmd and '-Wall' in cmd and '--public-flat-rw' in cmd and '-std=c++17 -O2 -Wall -Wextra -Werror' in cmd and '300s' in cmd and '--kill-after=5s' in cmd and cmd[cmd.index('-j')+1]=='2'
    assert 'Verilator 5.020' in (rp.parent/'verilator.log').read_text() and '%Warning-' not in (rp.parent/'compile.log').read_text()
    trace=rp.parent/'trace.jsonl.gz';digest=hashlib.sha256();values=[0]*52;prepared_edges=prepares=checkpoints=0;historical=False;coverage=set();active_prepare=None;last_hist=None
    with gzip.open(trace,'rb') as f:
        for line in f:
            digest.update(line);v=json.loads(line)
            if 'model_start' in v:historical=True;continue
            if 'prepare' in v:
                assert not historical;kind,word,carry,action=(v[k] for k in ('kind','word','carry','action'))
                assert kind in (0,1,2) and 0<=word<(4,16,32)[kind] and 1<=carry<=64 and 0<=action<16
                base=MASK if carry==64 else (1<<carry)-1;expected=[]
                for i in range(52):
                    salt=((0x9e3779b97f4a7c15*(i+1))&MASK)^1069001
                    upper=0 if carry>=63 else (salt>>(carry+1))<<(carry+1)
                    expected.append(base|upper)
                assert v['counts']==expected
                values=expected;prepares+=1;coverage.add((kind,word,carry,action));active_prepare=v;continue
            assert len(v['counts'])==52 and all(0<=x<=MASK for x in v['counts'])
            if historical:
                assert v['phase']=='historical'
                if v['guards']:assert v['counts']==[0]*52
                elif last_hist and not last_hist['guards']:
                    deltas=[sum(v['counts'][lo:hi])-sum(last_hist['counts'][lo:hi]) for lo,hi in ((0,4),(4,20),(20,52))]
                    assert deltas[0]==deltas[1]==deltas[2] and 0<=deltas[0]<=v['clock']-last_hist['clock']
                last_hist=v;checkpoints+=1;continue
            assert v['phase']=='prepared'
            if active_prepare:
                assert v['guards']==(active_prepare['action']&7) and bool(v['running'])==bool(active_prepare['action']&8)
                if active_prepare['action']==8:
                    actual=(v['emitter'],v['packet'],v['scratch'])[active_prepare['kind']]
                    assert actual==active_prepare['word']
                active_prepare=None
            if v['guards']:values=[0]*52
            elif v['running']:
                for index in (v['emitter'],4+v['packet'],20+v['scratch']):values[index]=(values[index]+1)&MASK
            assert v['counts']==values;prepared_edges+=1
    expected_coverage={(kind,word,carry,action) for kind,size in enumerate((4,16,32)) for word in range(size) for carry in range(1,65) for action in range(16)}
    assert coverage==expected_coverage and prepares==53248 and prepared_edges==106497 and checkpoints==31404
    assert digest.hexdigest()==r['raw_trace_sha256']==r['trace_replay']['raw_sha256']
    verdict=r['terminal_verdict'];assert verdict['status']=='TEST_PASS' and verdict['prepared_cases']==53248 and verdict['prepared_edges']==106497 and verdict['historical_edges']==7982233 and verdict['historical_trace_rows']==31404
    historical_verdict=r['historical_verdict'];assert historical_verdict['status']=='TEST_PASS' and historical_verdict['packets']==20 and historical_verdict['configurations']==2 and historical_verdict['dense_comparisons']==4501888 and historical_verdict['directed_checks']==56 and historical_verdict['sync_staging_checks']==9
    out=dict(schema='v106-telemetry-independent-trace-audit-v1',status='PASS',
        auditor=dict(path=str(Path(__file__).relative_to(ROOT)),sha256=sha(Path(__file__))),
        selected_receipt=dict(path=str(rp.relative_to(ROOT)),sha256=sha(rp)),selected_summary=dict(path=str(sp.relative_to(ROOT)),sha256=sha(sp)),
        trace_sha256=sha(trace),raw_trace_sha256=digest.hexdigest(),candidate=r['candidate'],
        prepared_cases=prepares,prepared_edges=prepared_edges,counter_words=52,carry_positions=64,guard_running_combinations=16,
        historical_edges=7982233,historical_checkpoints=checkpoints,historical_packets=20,historical_profiles=2,dense_comparisons=4501888,directed_checks=56,sync_staging_checks=9,
        limits=['Prepared actual-module child/controller/counter states are not complete packet reachability or four-state/formal equivalence.',
            'All prepared edges replayed; historical checkpoints sampled every256edges pluskill, while clocked C++oracle/fullmodulecomparison runs oneveryhistoricaledge.',
            'No native mapping/timing, hardware FPS or complete latency qualification.'])
    (AREA/'trace-audit.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print('V106_TELEMETRY_TRACE_AUDIT PASS',prepared_edges,checkpoints)
if __name__=='__main__':main()
