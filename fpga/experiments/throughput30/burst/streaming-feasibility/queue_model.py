#!/usr/bin/env python3
"""Synthetic bounded packet queue and single busy sink; not RTL or firmware."""
import argparse, hashlib, heapq, json, re, sys
from collections import deque
from pathlib import Path
ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'host'))
from moonshine.protocol import packets, parse_packet, Reassembler
BURST = ROOT/'fpga/experiments/throughput30/burst'
CYCLES_PER_MS = 100000

def load_events(fixtures, trace):
    entries=[json.loads(x) for x in trace.read_text().splitlines()]
    by_id={}
    for e in entries:
        if e['id'] not in by_id:
            jpg=(fixtures/f"{e['id']:04}.jpg").read_bytes()
            by_id[e['id']]={parse_packet(p).offset:p for p in packets(jpg,e['id'],e['capture_cycle']//100)}
        wire=by_id[e['id']][e['offset']]
        if hashlib.sha256(wire).hexdigest()!=e['datagram_sha256']: raise ValueError('datagram hash mismatch')
        e['wire']=wire
    if len(entries)!=267 or {e['id'] for e in entries}!=set(range(10)): raise ValueError('unexpected trace')
    return entries

def measured_release_cycles(log):
    lines=log.read_text().splitlines()
    if 'TEST_PASS_NETWORK_QSPI_TRACE' not in lines: raise ValueError('missing RTL pass')
    rr=[{k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',s)} for s in lines if s.startswith('FRAME_RESULT ')]
    if len(rr)!=10: raise ValueError('expected 10 frames')
    return max(r['present_cycle']-r['commit_cycle'] for r in rr)

def simulate(arrivals, capacity, policy, service_per_kib, release_cycles, deadline_cycles=5000000, timeout_cycles=10000000):
    # A live packet (including the in-flight packet) occupies payload+40 bytes.
    # Busy release is a calibrated fixed delay, no QSPI control/abort timing.
    queue=deque(); occupied=0; max_bytes=0; now=0; inflight=None; active=None
    receiver=Reassembler(); failed=set(); completed=[]; drops={}; busy_until=0; max_age=0; active_started=None
    timeline=[]; serial=0
    def event(t,kind,content=None):
        nonlocal serial
        serial+=1; heapq.heappush(timeline,(t,serial,kind,content))
    for e in arrivals:event(e['arrival_cycle'],'packet',e)
    def fail(fid,reason):
        nonlocal occupied,queue,active,active_started
        if fid in failed or any(x['id']==fid for x in completed): return
        failed.add(fid);drops[fid]=dict(id=fid,reason=reason,cycle=now)
        kept=deque()
        while queue:
            e=queue.popleft()
            if e['id']==fid: occupied-=len(e['wire'])
            else: kept.append(e)
        queue=kept
        if active==fid: receiver.reset(False);active=None;active_started=None
    def schedule_service():
        nonlocal inflight
        if inflight is not None or not queue: return
        e=queue[0]; fid=e['id']
        if fid in failed: raise AssertionError('failed frame in queue')
        if active is None and policy=='fresh' and now-e['capture_cycle']>=deadline_cycles:
            fail(fid,'begin_deadline');schedule_service();return
        if active is None and now<busy_until:
            event(busy_until,'wake');return
        if active is not None and active!=fid:
            # A new SOF before the previous EOF aborts the incomplete frame.
            fail(active,'superseded_incomplete')
        e=queue.popleft();inflight=e
        duration=max(1,(len(e['wire'])-40)*service_per_kib//1024)
        event(now+duration,'service',e)
    while timeline:
        now,_,kind,e=heapq.heappop(timeline)
        if kind=='packet':
            fid=e['id'];h=parse_packet(e['wire'])
            if fid in failed:continue
            if policy=='fresh' and h.offset==0:
                current = active if active is not None else (inflight['id'] if inflight is not None else None)
                if current is not None and current != fid:
                    fail(fid,'active_in_progress');continue
                protected={active, inflight['id'] if inflight is not None else None}
                for old_id in sorted({q['id'] for q in queue} - protected - {fid}):
                    fail(old_id,'superseded_waiting')
            if policy=='fresh' and fid!=active and (inflight is None or fid!=inflight['id']) and now-e['capture_cycle']>=deadline_cycles:
                fail(fid,'begin_deadline');continue
            if policy=='drop-busy' and h.offset==0 and (now<busy_until or (active is not None and active!=fid)):
                fail(fid,'busy_sof');continue
            if occupied+len(e['wire'])>capacity:
                fail(fid,'queue_full');continue
            occupied+=len(e['wire']);max_bytes=max(max_bytes,occupied);queue.append(e)
            schedule_service()
        elif kind=='service':
            if inflight is not e: raise AssertionError('unexpected service')
            inflight=None;occupied-=len(e['wire']);fid=e['id']
            if fid not in failed:
                h=parse_packet(e['wire'])
                if active is None:
                    if h.offset!=0:fail(fid,'missing_sof');schedule_service();continue
                    if now<busy_until:raise AssertionError('busy begin')
                    active=fid;active_started=now;event(now+timeout_cycles,'timeout',(fid,now))
                try:done=receiver.accept(e['wire'])
                except ValueError:fail(fid,'receiver_rejected');schedule_service();continue
                if done:
                    if done[1] != b''.join(parse_packet(x['wire']).payload for x in arrivals if x['id']==fid):
                        raise AssertionError('reconstructed content mismatch')
                    active=None;active_started=None;busy_until=now+release_cycles
                    age=busy_until-e['capture_cycle'];max_age=max(max_age,age)
                    completed.append(dict(id=fid,commit_cycle=now,present_cycle=busy_until,age_ms=age/CYCLES_PER_MS))
            schedule_service()
        elif kind=='timeout':
            fid,started=e
            if active==fid and active_started==started: fail(fid,'receive_timeout')
            schedule_service()
        else:
            schedule_service()
    if inflight is not None or queue or active is not None or occupied!=0: raise ValueError('unfinished state')
    if {x['id'] for x in completed}|set(drops)!={x['id'] for x in arrivals}:raise ValueError('frame accounting')
    return dict(policy=policy,capacity_bytes=capacity,completed=completed,dropped=list(drops.values()),
                max_staged_bytes=max_bytes,max_age_ms=max_age/CYCLES_PER_MS)

def main():
    p=argparse.ArgumentParser();p.add_argument('--fixtures',type=Path,required=True)
    p.add_argument('--large-bytes',type=int,default=32768);p.add_argument('--service-us-per-kib',type=int,default=200)
    p.add_argument('--deadline-ms',type=int,default=50);p.add_argument('--output',type=Path);a=p.parse_args()
    if a.large_bytes<5320 or a.service_us_per_kib<1 or a.deadline_ms<1:p.error('invalid size or service')
    trace=BURST/'network-rtl-study/results-clean/packet-trace.jsonl';log=BURST/'latency-followup/results/baseline/run.log'
    arrivals=load_events(a.fixtures,trace);release=measured_release_cycles(log)
    result=dict(scope='synthetic Python discrete event model; no RTL/target execution',
      clock_hz=100000000,release_cycles=release,service_us_per_kib=a.service_us_per_kib,
      capacity_accounting='full datagram incl 40 byte header and in-flight packet; excludes socket/allocator overhead',
      cases=[simulate(arrivals,5320,'drop-busy',a.service_us_per_kib*100,release),
             simulate(arrivals,a.large_bytes,'buffer-busy',a.service_us_per_kib*100,release),
             simulate(arrivals,5320,'fresh',a.service_us_per_kib*100,release,a.deadline_ms*CYCLES_PER_MS),
             simulate(arrivals,a.large_bytes,'fresh',a.service_us_per_kib*100,release,a.deadline_ms*CYCLES_PER_MS)],
      freshness_deadline_ms=a.deadline_ms, frame_receive_timeout_ms=100,
      caveat='one no-loss synthetic 10-frame trace; fixed sampled max commit-to-present, estimated QSPI service, zero CPU/abort time; not validated on actual hardware')
    out=json.dumps(result,indent=2)+'\n';print(out,end='')
    if a.output:a.output.write_text(out)
if __name__=='__main__':main()
