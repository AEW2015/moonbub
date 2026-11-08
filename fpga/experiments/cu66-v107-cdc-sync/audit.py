#!/usr/bin/env python3
"""Independent portable acceptance/capacity/rate audit for the new prototype."""
import gzip,hashlib,importlib.util,json
from collections import deque
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
AREA=ROOT/'experiments/python-gamebub-v107/cdc-sync'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    selected=json.loads((AREA/'results.json').read_text());receipt=ROOT/selected['selected_receipt'];assert sha(receipt)==selected['sha256'];r=json.loads(receipt.read_text());assert r['status']=='PASS_BEHAVIORAL_SYNC_BRAM_CONTROL' and r['actual_RTL_run']
    for name,h in r['source_sha256'].items():assert sha(receipt.parent/'sources'/name)==h,name
    for name,h in r['artifacts_sha256'].items():assert sha(receipt.parent/name)==h,name
    baseline_path=ROOT/r['baseline_behavioral_receipt']['path'];assert sha(baseline_path)==r['baseline_behavioral_receipt']['sha256'];baseline=json.loads(baseline_path.read_text())
    assert r['unchanged_scoreboard_sha256']==baseline['source_sha256']['fpga/experiments/cu66-v107-cdc/tb_cdc.cpp']
    for file in ('v107_async_fifo.sv','v107_reset_release.sv','v107_cdc_fabric.sv'):
        name='fpga/experiments/cu66-v107-cdc-sync/'+file;assert sha(ROOT/name)==r['source_sha256'][name]
    spec=importlib.util.spec_from_file_location('old_replay',ROOT/'scripts/cu66-v107/cdc.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    seeds=[]
    for run in r['runs']:
        seed=run['seed'];path=receipt.parent/f'{seed}.csv.gz';replay=old.replay(path);assert replay==run['replay']
        queues=[deque() for _ in range(5)];maximum=[0]*5
        with gzip.open(path,'rt') as trace:
            for line in trace:
                t,op,ch,ep,*word=line.strip().split(',');ch=int(ch)
                if op=='E':queues=[deque() for _ in range(5)]
                elif op=='W':queues[ch].append(word);maximum[ch]=max(maximum[ch],len(queues[ch]));assert len(queues[ch])<=9
                else:assert queues[ch].popleft()==word
        assert not any(queues) and maximum==[9]*5
        seeds.append(dict(seed=seed,replay=replay,max_owned_per_channel=maximum,old_variant_same_seed=run['original_same_scoreboard_replay']))
    rate=AREA/'rate';rr=json.loads((rate/'receipt.json').read_text());assert rr['status']=='PASS_NO_STALL_RATE' and rr['behavioral_receipt']['sha256']==sha(receipt)
    for name,h in rr['artifacts_sha256'].items():assert sha(rate/name)==h,name
    assert 'TEST_PASS_CDC_SYNC_RATE' in (rate/'run.log').read_text()
    queues=[deque() for _ in range(5)];accepted=[[] for _ in range(5)];delivered=[[] for _ in range(5)];latencies=[[] for _ in range(5)]
    with gzip.open(rate/'trace.csv.gz','rt') as trace:
        for line in trace:
            t,op,ch,n,latency=line.strip().split(',');t,ch,n,latency=map(int,(t,ch,n,latency))
            if op=='W':assert n==len(accepted[ch]);accepted[ch].append(t);queues[ch].append((n,t))
            else:
                expected,issued=queues[ch].popleft();assert expected==n==len(delivered[ch]) and t-issued==latency
                delivered[ch].append(t);latencies[ch].append(latency)
    metrics=[]
    for ch in range(5):
        a,b,l=accepted[ch],delivered[ch],latencies[ch]
        assert len(a)==len(b)==10000 and not queues[ch]
        assert all(y-x==2 for x,y in zip(b,b[1:]))
        assert all(y-x==2 for x,y in zip(a[1000:],a[1001:]))
        expected=rr['channels'][ch];assert min(l)==expected['min_latency_clocks']==6 and max(l)==expected['max_latency_clocks']==13
        metrics.append(dict(channel=ch,accepted=len(a),delivered=len(b),accepted_words_per_clock_finite=(len(a)-1)/(a[-1]-a[0]),accepted_words_per_clock_steady=0.5,delivered_words_per_clock=0.5,min_latency_equal_test_clocks=min(l),max_latency_equal_test_clocks=max(l),first_accepted=a[0],first_delivered=b[0],steady_after_accepted_index=1000,max_owned_in_no_stall_run=expected['max_owned']))
    result=dict(schema='v107-cdc-sync-independent-audit-v1',status='PASS_BEHAVIOR_CAPACITY_AND_MEASURED_HALF_RATE',behavioral_receipt_sha256=sha(receipt),seeds=seeds,totals={key:sum(x['replay'][key] for x in seeds) for key in ('accepted','delivered','reset_discarded')},capacity=dict(reserved_RAM_slots=8,output_slots=1,observed_max=9,all_five_channels_all_three_seeds_reached=True),rate=metrics,rate_scope='No stalls on public interfaces after initial reset, allfourtestclocks equal. Rates are measured unit ceilings, not actual board/clock-domain latency or full LCD service.',retained_testbench_failure='rate-failed-capacity-assumption: demanded full9during no-stall test, actual7; corrected requirement, no RTL change.',native_signoff=False,board_or_complete_parent_qualified=False,waivers_added=False,audit_program_sha256=sha(Path(__file__)))
    (AREA/'audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(result['status']);print(json.dumps(result['totals'],sort_keys=True))
if __name__=='__main__':main()
