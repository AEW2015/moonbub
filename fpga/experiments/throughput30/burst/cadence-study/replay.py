#!/usr/bin/env python3
"""Repeat per-frame service observations in an ideal frame-boundary/one-slot model.

This is a model, not an RTL run: service times repeat, ignoring variation due to
content, scanout contention, transport, and radio. Validate the original ten
frame sequence before using extrapolation. The one-slot queue is conceptual.
"""
import argparse, json, math, re
from pathlib import Path


def read_frames(log):
    rows=[]
    for line in log.read_text().splitlines():
        if line.startswith('FRAME_RESULT '):
            d={k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',line)}
            rows.append(d)
    if len(rows)!=10 or any('pending_cycle' not in r for r in rows):
        raise ValueError('Need 10 completed FRAME_RESULT rows with pending_cycle')
    return rows


def run(rows, pixel_half_ns, count):
    # 100 MHz, H_TOTAL 541 and V_TOTAL 834. First sampled presentation fixes
    # phase; ideal boundaries are rounded to a core cycle (CDC can add jitter).
    interval=(2*pixel_half_ns*541*834)/10
    origin=rows[0]['present_cycle']
    epoch=rows[0]['arrival_cycle']
    previous_present=None; previous_start=None; records=[]; overflow=[]
    for i in range(count):
        arrival=epoch+(i*10000000)//3
        if previous_start is not None and previous_start>arrival:
            overflow.append(i+1)
        start=max(arrival+1,previous_present+1 if previous_present else arrival+1)
        r=rows[i%len(rows)]
        # Upload duration and decoder/staging time from this sample frame.
        ready=start+r['upload_cycles']+(r['pending_cycle']-r['commit_cycle'])
        boundary=math.ceil((ready-origin)/interval-1e-10)
        present=round(origin+boundary*interval)
        if present<ready: present=round(origin+(boundary+1)*interval)
        records.append({'id':i+1,'arrival':arrival,'start':start,'ready':ready,'present':present})
        previous_start, previous_present=start,present
    errs=[a['present']-b['present_cycle'] for a,b in zip(records[:10],rows)]
    span=records[-1]['present']-records[0]['present']
    ages=[x['present']-x['arrival'] for x in records]
    return {'model':'repeated measured upload/decode service; ideal display boundaries; one waiting frame; no loss or transport',
            'input_fps':30,'modeled_frames':count,'pixel_half_ns':pixel_half_ns,
            'lcd_hz':1e9/(2*pixel_half_ns*541*834),
            'baseline_present_error_cycles':errs,'baseline_max_abs_error_cycles':max(map(abs,errs)),
            'modeled_presentation_fps':(count-1)*100000000/span,
            'max_modeled_age_ms':max(ages)/100000,'hypothetical_queue_overflow_frame_ids':overflow[:20],
            'hypothetical_queue_overflow_count':len(overflow),
            'caveat':'extrapolation assumes the same 10 decoder service times repeat irrespective of future LCD contention; not a measured 60-second RTL simulation or ESP32 queue proof'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log',type=Path);parser.add_argument('--half-ns',type=float,default=17.029);parser.add_argument('--frames',type=int,default=1800)
    args=parser.parse_args()
    if args.frames<10 or args.half_ns<=0: parser.error('need >= 10 frames and positive clock period')
    result=run(read_frames(args.log),args.half_ns,args.frames)
    print(json.dumps(result,indent=2))
    if result['baseline_max_abs_error_cycles'] > 2:
        raise SystemExit('model does not reproduce the ten measured swap times')
if __name__=='__main__':main()
