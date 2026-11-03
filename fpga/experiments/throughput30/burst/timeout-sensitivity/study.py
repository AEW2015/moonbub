#!/usr/bin/env python3
"""Seeded frame-scoped missing-packet inactivity sensitivity; not real radio."""
import argparse, collections, importlib.util, json, statistics
from pathlib import Path
HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'transport-followup/recovery-study/study.py'
spec=importlib.util.spec_from_file_location('existing_recovery_study',SOURCE)
source=importlib.util.module_from_spec(spec);spec.loader.exec_module(source)
CLOCK=source.CLOCK
THRESHOLDS_MS=(1,2,3,5,10,20)

def classify(arrivals,count,frames):
    groups=[[] for _ in range(count)]
    for e in arrivals:groups[e['fid']].append(e)
    classes=[]
    for fid,g in enumerate(groups):
        n=len(list(source.packets(frames[fid%10],fid,(fid*source.PERIOD_NUM//source.PERIOD_DEN)//100)))
        seen={e['index'] for e in g};order=[e['index'] for e in g]
        if len(seen)==n:
            label='complete_ordered' if order==list(range(n)) else 'complete_reordered'
        elif 0 not in seen:label='missing_sof'
        elif seen==set(range(n-1)) and order==list(range(n-1)):label='missing_eof_only_ordered'
        else:label='other_loss_or_reorder'
        classes.append(label)
    return classes

def evaluate(arrivals,count,threshold_cycles):
    """Before an arrival at the exact deadline, timeout wins the tie.

    Per accepted packet timer resets. Reject first missing/reordered offset;
    a newer SOF supersedes prior active frame if the timer has not fired.
    """
    outcomes=[None]*count;active=None;expected=0;deadline=None;last=None
    def finish(fid,kind,at,last_at):outcomes[fid]={'kind':kind,'at':at,'last_accepted':last_at,'accepted_count':expected}
    for e in arrivals:
        at=e['at'];fid=e['fid'];idx=e['index']
        if active is not None and deadline<=at:
            finish(active,'timeout',deadline,last);active=None;deadline=None
        if idx==0:
            if outcomes[fid] is not None:continue
            if active is not None:finish(active,'superseded',at,last)
            active=fid;expected=0
        if active!=fid:continue
        if idx!=expected:
            finish(fid,'sequence_error',at,last);active=None;deadline=None;continue
        expected+=1;last=at
        if expected==e['count']:
            finish(fid,'complete',at,last);active=None;deadline=None
        else:deadline=at+threshold_cycles
    if active is not None:finish(active,'timeout',deadline,last)
    return [o if o is not None else {'kind':'no_start','at':None,'last_accepted':None} for o in outcomes]

def percentile(values,q):
    if not values:return None
    ordered=sorted(values);return ordered[((len(ordered)-1)*q+99)//100]

def run(fixtures,frames_count,seed_count,rate):
    frames=source.fixture_data(fixtures);output={}
    for jitter in (300,1200,3000):
      for channel in ('none','iid'):
        key=f'jitter_{jitter}us_{channel}'
        per={ms:collections.Counter() for ms in THRESHOLDS_MS};delays={ms:[] for ms in THRESHOLDS_MS}
        class_counts=collections.Counter();wire_totals=collections.Counter()
        for seed in range(73,73+seed_count):
            arrivals,stats=source.simulate_link(frames,frames_count,rate,seed,channel,False,jitter_us=jitter)
            if stats['sender_replaced'] or stats['sender_expired'] or stats['sender_max_wait_ms']!=0:raise ValueError('sender queue changed timing; cannot use nominal serialization')
            wire_totals.update({k:stats[k] for k in ('sent_data','lost_data','captures')})
            classes=classify(arrivals,frames_count,frames);class_counts.update(classes)
            # Earliest nominal sender transmission end for EOF; excludes any
            # receive jitter/real radio. Existing simulator serializes L3 bytes.
            eof_finish=[]
            for fid in range(frames_count):
                t=fid*source.PERIOD_NUM//source.PERIOD_DEN
                for pkt in source.packets(frames[fid%10],fid,t//100):t+=((len(pkt)+source.IP_UDP)*8*CLOCK+rate-1)//rate
                eof_finish.append(t)
            for ms in THRESHOLDS_MS:
                result=evaluate(arrivals,frames_count,ms*100000);ctr=per[ms]
                for fid,(category,o) in enumerate(zip(classes,result,strict=True)):
                    ctr['frames']+=1;ctr['outcome_'+o['kind']]+=1
                    if category=='complete_ordered':
                        ctr['complete_ordered_frames']+=1
                        if o['kind']=='timeout':ctr['false_timeout_complete_ordered']+=1
                        if o['kind']=='complete':ctr['delivered_complete_ordered']+=1
                    if category=='missing_eof_only_ordered':
                        ctr['missing_eof_only_ordered']+=1
                        ctr['missing_eof_'+o['kind']]+=1
                        if o['kind']=='timeout' and o['accepted_count']<len(list(source.packets(frames[fid%10],fid,0)))-1:
                            ctr['missing_eof_early_timeout_before_last_received']+=1
                        if o['kind']=='timeout' and o['accepted_count']==len(list(source.packets(frames[fid%10],fid,0)))-1:
                            ctr['missing_eof_timeout_after_last_received']+=1
                            # Relative to hypothetical EOF wire serialization
                            # end; loss has no actual receiver arrival time.
                            delays[ms].append((o['at']-eof_finish[fid])/100000)
        output[key]={'jitter_us_uniform_max':jitter,'channel':channel,'frame_classes':dict(class_counts),'wire':dict(wire_totals),
          'thresholds':{str(ms):{**dict(per[ms]),'missing_eof_timeout_delay_vs_nominal_wire_end_ms':{
              'samples':len(delays[ms]),'median':statistics.median(delays[ms]) if delays[ms] else None,
              'p95':percentile(delays[ms],95),'max':max(delays[ms]) if delays[ms] else None,
              'min':min(delays[ms]) if delays[ms] else None}} for ms in THRESHOLDS_MS}}
    return {'scope':'synthetic event-level simulation, no real Wi-Fi, CPU or RTL execution',
      'frames_per_seed':frames_count,'seed_count':seed_count,'seeds_start':73,'assumed_rate_bps_l3':rate,
      'thresholds_ms':list(THRESHOLDS_MS),'on_exact_deadline':'timeout before packet',
      'timer':'per active frame, resets on each accepted packet, stops on EOF/error/superseding SOF',
      'cases':output}

def main():
 p=argparse.ArgumentParser();p.add_argument('--fixtures',type=Path,required=True);p.add_argument('--frames',type=int,default=300);p.add_argument('--seeds',type=int,default=10);p.add_argument('--rate',type=int,default=8000000);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if a.frames<1 or a.seeds<1 or a.rate<1:p.error('positive parameters required')
 result=run(a.fixtures,a.frames,a.seeds,a.rate);a.output.write_text(json.dumps(result,indent=2)+'\n')
 print('TIMEOUT_STUDY_PASS',len(result['cases']),'cases',a.frames,'frames/seed',a.seeds,'seeds')
if __name__=='__main__':main()
