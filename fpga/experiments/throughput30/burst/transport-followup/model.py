#!/usr/bin/env python3
"""Packet-level MSV1/UDP timeline and *analytical* bounded presentation model.

All rates are assumptions, not RF/hardware observations. The decoder service
model repeats 10 RTL measurements; the conceptual receiver queue is not the
ESP32 implementation. Input frames repeat the 10 local fixture JPEGs.
"""
from __future__ import annotations
import argparse, hashlib, heapq, json, math, random, re, sys
from dataclasses import dataclass
from pathlib import Path

ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT/'host'))
from moonshine.protocol import Reassembler, packets, VIDEO, MAX_PAYLOAD

CLOCK=100_000_000
FRAME_PERIOD_NUM=10_000_000
FRAME_PERIOD_DEN=3
IP_UDP_BYTES=28
REFRESH_CYCLES=(2*17.029*541*834)/10

@dataclass(frozen=True)
class Scenario:
    rate_bps:int=8_000_000
    payload_only_service:bool=False
    jitter_us:int=0
    loss_ppm:int=0
    bad_rate_bps:int=0
    bad_period_ms:int=1000
    bad_duration_ms:int=0
    sender_age_ms:int=100
    receiver_age_ms:int=100
    seed:int=1


def read_timings(path:Path):
    rows=[]
    for line in path.read_text().splitlines():
        if line.startswith('FRAME_RESULT '):
            row={k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',line)}
            if 'pending_cycle' in row:rows.append(row)
    if len(rows)!=10:raise ValueError('expected ten timed RTL frames with pending_cycle')
    return rows


def load_fixtures(path:Path):
    meta=json.loads((path/'manifest.json').read_text())
    if len(meta['frames'])!=10:raise ValueError('expected exactly ten reference frames')
    result=[]
    for row in meta['frames']:
        data=(path/f"{row['id']:04d}.jpg").read_bytes()
        if hashlib.sha256(data).hexdigest()!=row['jpeg_sha256']:raise ValueError('JPEG hash mismatch')
        result.append(data)
    return result


def run(jpegs,timings,scenario:Scenario,count=1800,collect=False):
    if len(jpegs)!=10 or len(timings)!=10 or count<=0:raise ValueError('expected ten reference frames and count>0')
    if scenario.rate_bps<=0 or scenario.jitter_us<0 or not 0<=scenario.loss_ppm<=1_000_000:raise ValueError('invalid rate, jitter, or loss')
    if not 0<=scenario.bad_duration_ms<=scenario.bad_period_ms or scenario.bad_period_ms<=0:raise ValueError('invalid bad-service window')
    if scenario.bad_duration_ms and scenario.bad_rate_bps<=0:raise ValueError('bad service rate required')
    if scenario.sender_age_ms<=0 or scenario.receiver_age_ms<=0:raise ValueError('positive deadlines required')
    rng=random.Random(scenario.seed); events=[]; serial=0
    def add(at,kind,payload):
        nonlocal serial
        serial+=1;heapq.heappush(events,(at,serial,kind,payload))
    for i in range(count):add(i*FRAME_PERIOD_NUM//FRAME_PERIOD_DEN,'capture',i)
    sender_busy=False;sender_pending=None;video_busy=False;video_pending=None
    receiver=Reassembler(); earliest_swap=timings[0]['present_cycle']-timings[0]['arrival_cycle']
    stats={'captured':0,'send_started':0,'send_completed':0,'sender_replaced':0,'sender_expired':0,
           'packets_sent':0,'packets_lost':0,'packets_received':0,'packet_rejects':0,'received_complete':0,
           'receiver_replaced':0,'receiver_expired':0,'presented':0,'wire_bytes':0,'jpeg_payload_bytes':0,
           'sender_queue_highwater_frames':0,'receiver_queue_highwater_frames':0,
           'sender_queue_highwater_bytes':0,'receiver_queue_highwater_bytes':0,'max_sender_age_ms':0.,
           'max_receive_age_ms':0.,'max_present_age_ms':0.,'presentation_intervals_ms':[]}
    presentations=[]; delivered=[]; frame_wire_sent=[]
    def capture_time(i):return i*FRAME_PERIOD_NUM//FRAME_PERIOD_DEN
    def rate_at(t):
        if scenario.bad_duration_ms and t%(scenario.bad_period_ms*100_000)<scenario.bad_duration_ms*100_000:
            return scenario.bad_rate_bps
        return scenario.rate_bps
    def start_send(i,start):
        nonlocal sender_busy
        sender_busy=True;stats['send_started']+=1
        payload=jpegs[i%10]; ts_us=capture_time(i)//100
        wire=packets(payload,i,ts_us); current=start;framebytes=0
        for p in wire:
            # Assumes IPv4/UDP; excludes MAC, PHY, retransmissions, FEC and audio.
            length=len(p)+IP_UDP_BYTES;framebytes+=length
            # Rate is sampled at packet-start and held for this packet.
            bps=rate_at(current)
            service_bytes=(len(p)-VIDEO.size) if scenario.payload_only_service else length
            duration=(service_bytes*8*CLOCK+bps-1)//bps
            current+=duration;stats['packets_sent']+=1;stats['wire_bytes']+=length
            if rng.randrange(1_000_000)<scenario.loss_ppm:stats['packets_lost']+=1
            else:
                delay=rng.randrange(scenario.jitter_us+1)*100 if scenario.jitter_us else 0
                add(current+delay,'packet',p)
        stats['jpeg_payload_bytes']+=len(payload)
        frame_wire_sent.append(framebytes)
        add(current,'send_end',i)
    def start_video(i,start):
        nonlocal video_busy
        video_busy=True
        source=timings[i%10]
        # These samples include optimistic register upload + measured decoder and
        # write/staging time; service is assumed invariant across later contention.
        ready=start+source['upload_cycles']+source['pending_cycle']-source['commit_cycle']
        phase=earliest_swap
        refresh_index=math.ceil((ready-phase)/REFRESH_CYCLES-1e-10)
        finish=round(phase+refresh_index*REFRESH_CYCLES)
        if finish<ready:finish=round(phase+(refresh_index+1)*REFRESH_CYCLES)
        add(finish,'swap',i)
    while events:
        now,_,kind,value=heapq.heappop(events)
        if kind=='capture':
            i=value;stats['captured']+=1
            if not sender_busy:start_send(i,now)
            else:
                if sender_pending is not None:stats['sender_replaced']+=1
                sender_pending=i
                stats['sender_queue_highwater_frames']=1
                stats['sender_queue_highwater_bytes']=max(stats['sender_queue_highwater_bytes'],len(jpegs[i%10]))
        elif kind=='send_end':
            stats['send_completed']+=1;sender_busy=False
            if sender_pending is not None:
                i=sender_pending;sender_pending=None
                age=now-capture_time(i)
                if age>scenario.sender_age_ms*100_000:stats['sender_expired']+=1
                else:
                    stats['max_sender_age_ms']=max(stats['max_sender_age_ms'],age/100_000)
                    start_send(i,now)
        elif kind=='packet':
            stats['packets_received']+=1
            try:result=receiver.accept(value)
            except ValueError:stats['packet_rejects']+=1;continue
            if result:
                header,data=result;i=header.frame_id
                if data != jpegs[i%10]:raise AssertionError('MSV1 reassembled wrong payload')
                stats['received_complete']+=1;delivered.append(i)
                age=now-capture_time(i);stats['max_receive_age_ms']=max(stats['max_receive_age_ms'],age/100_000)
                if age>scenario.receiver_age_ms*100_000:stats['receiver_expired']+=1
                elif not video_busy:start_video(i,now)
                else:
                    if video_pending is not None:stats['receiver_replaced']+=1
                    video_pending=i;stats['receiver_queue_highwater_frames']=1
                    stats['receiver_queue_highwater_bytes']=max(stats['receiver_queue_highwater_bytes'],len(data))
        elif kind=='swap':
            i=value;stats['presented']+=1;video_busy=False;presentations.append((i,now))
            stats['max_present_age_ms']=max(stats['max_present_age_ms'],(now-capture_time(i))/100_000)
            if video_pending is not None:
                i=video_pending;video_pending=None
                if now-capture_time(i)>scenario.receiver_age_ms*100_000:stats['receiver_expired']+=1
                else:start_video(i,now)
    if presentations:
        stats['presentation_intervals_ms']=[(b[1]-a[1])/100_000 for a,b in zip(presentations,presentations[1:])]
        if len(presentations)>1:
            stats['displayed_fps_over_span']=(len(presentations)-1)*CLOCK/(presentations[-1][1]-presentations[0][1])
        stats['displayed_fps_per_capture_duration']=len(presentations)*30/count
        ints=sorted(stats['presentation_intervals_ms'])
        if ints:stats['presentation_interval_p95_ms']=ints[math.ceil(.95*len(ints))-1]
    stats['wire_overhead_fraction']=(stats['wire_bytes']-stats['jpeg_payload_bytes'])/stats['wire_bytes'] if stats['wire_bytes'] else 0
    stats['largest_wire_frame_bytes']=max(frame_wire_sent,default=0)
    stats['actual_msv1_header_bytes']=VIDEO.size;stats['ip_udp_header_bytes']=IP_UDP_BYTES
    stats['max_packet_payload_bytes']=MAX_PAYLOAD
    if not collect:stats.pop('presentation_intervals_ms')
    else:
        stats['presented_ids']=[i for i,_ in presentations];stats['complete_ids']=delivered
        stats['presented_records']=[{'id':i,'cycle':t} for i,t in presentations]
    return stats


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixtures',type=Path,required=True)
    parser.add_argument('--timings',type=Path,default=ROOT/'fpga/experiments/throughput30/burst/cadence-study/verilator-65hz.log')
    parser.add_argument('--frames',type=int,default=1800);parser.add_argument('--seed',type=int,default=13)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();jpegs=load_fixtures(args.fixtures);timings=read_timings(args.timings)
    cases={'ideal_12mbps':Scenario(rate_bps=12_000_000,seed=args.seed),
           'ideal_8mbps':Scenario(rate_bps=8_000_000,seed=args.seed),
           'ideal_4mbps':Scenario(rate_bps=4_000_000,seed=args.seed),
           'jitter_8mbps':Scenario(rate_bps=8_000_000,jitter_us=1200,seed=args.seed),
           'loss_8mbps':Scenario(rate_bps=8_000_000,loss_ppm=5000,seed=args.seed),
           'bursts_8mbps':Scenario(rate_bps=8_000_000,bad_rate_bps=2_000_000,bad_period_ms=1000,bad_duration_ms=80,seed=args.seed)}
    output={'scope':'analytical event simulation of actual host MSV1 packetizer and reference reassembler; no device code or radio simulation',
            'frames':args.frames,'source':'10 synthetic JPEGs repeated, 30Hz; not unique gameplay','timing_source':str(args.timings.relative_to(ROOT)),
            'fixture_sha256':[hashlib.sha256(x).hexdigest() for x in jpegs],
            'caveats':['all link parameters are assumptions, not measured Wi-Fi','per-packet sampled service, independent loss and jitter; no correlated radio model',
                       'video service repeats 10 RTL measured durations irrespective of contention','receiver one-frame queue is conceptual, not implemented firmware',
                       'software CRC/computation time and QSPI transport are omitted','wire bytes count MSV1 + UDP + IPv4, not Wi-Fi MAC/PHY, FEC, retransmission or audio'],
            'cases':{name:{'scenario':vars(s),'result':run(jpegs,timings,s,args.frames)} for name,s in cases.items()}}
    args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(output,indent=2)+'\n')
    for name,c in output['cases'].items():
        x=c['result'];print(f"{name}: sent={x['send_completed']}/{args.frames} complete={x['received_complete']} presented={x['presented']} sender_replaced={x['sender_replaced']} receiver_replaced={x['receiver_replaced']} max_age_ms={x['max_present_age_ms']:.1f}")
if __name__=='__main__':main()
