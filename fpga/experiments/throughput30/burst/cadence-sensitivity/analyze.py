#!/usr/bin/env python3
"""Compare phase/clock sensitivity using recorded nominal-65 Hz and hypothetical-60 Hz traces."""
import argparse
import json
import math
import re
from pathlib import Path

CORE_HZ = 100_000_000
H_TOTAL, V_TOTAL = 541, 834
CAPTURE_WINDOW_SECONDS = 60


def read_frames(path):
    rows=[]
    for line in Path(path).read_text().splitlines():
        if line.startswith('FRAME_RESULT '):
            d={k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',line)}
            rows.append(d)
    required=('arrival_cycle','commit_cycle','pending_cycle','present_cycle','upload_cycles')
    if len(rows)!=10 or any(k not in r for r in rows for k in required):
        raise ValueError('expected ten complete FRAME_RESULT records')
    return rows


def replay(rows, half_ns, display_ppm=0, source_ppm=0, phase_fraction=0.0, frames=1800):
    refresh_cycles=2*half_ns*H_TOTAL*V_TOTAL*CORE_HZ/1e9
    source_period=CORE_HZ/(30*(1+source_ppm/1e6))
    display_interval=refresh_cycles/(1+display_ppm/1e6)
    origin=rows[0]['present_cycle'] + phase_fraction*display_interval
    epoch=rows[0]['arrival_cycle']
    previous_present=None
    records=[]
    for i in range(frames):
        arrival=epoch+i*source_period
        start=max(arrival+1,previous_present+1 if previous_present is not None else arrival+1)
        row=rows[i%len(rows)]
        ready=start+row['upload_cycles']+(row['pending_cycle']-row['commit_cycle'])
        boundary=max(0,math.ceil((ready-origin)/display_interval-1e-12))
        present=origin+boundary*display_interval
        while present+1e-8<ready:
            boundary+=1
            present=origin+boundary*display_interval
        records.append({'id':i+1,'arrival':arrival,'ready':ready,'present':present})
        previous_present=present

    window_end=epoch+CAPTURE_WINDOW_SECONDS*CORE_HZ
    captured=sum(r['arrival']<window_end for r in records)
    presented=sum(r['present']<window_end for r in records)
    gap_count=0
    gap_ms_min=None
    gap_ms_max=None
    for prev,cur in zip(records,records[1:]):
        if cur['present']<window_end:
            delta=cur['present']-prev['present']
            if delta>1.1*source_period:
                gap_ms=delta*1000/CORE_HZ
                gap_count+=1
                gap_ms_min=gap_ms if gap_ms_min is None else min(gap_ms_min,gap_ms)
                gap_ms_max=gap_ms if gap_ms_max is None else max(gap_ms_max,gap_ms)
    selected=records[:presented]
    ages=[r['present']-r['arrival'] for r in selected]
    interval_values=[b['present']-a['present'] for a,b in zip(selected,selected[1:])]
    end_delta=records[-1]['present']-records[0]['present']
    return {'frames_simulated':frames,'display_ppm':display_ppm,'source_ppm':source_ppm,
            'phase_fraction':phase_fraction,'refresh_hz':1e9/(2*half_ns*H_TOTAL*V_TOTAL)*(1+display_ppm/1e6),
            'rate_fps_first_to_last':(frames-1)*CORE_HZ/end_delta,
            'capture_window_seconds':CAPTURE_WINDOW_SECONDS,
            'captures_in_window':captured,'presentations_in_window':presented,
            'max_arrival_to_presentation_age_ms':max(ages)*1000/CORE_HZ if ages else None,
            'long_gap_threshold_source_periods':1.1,'long_gap_count_in_window':gap_count,
            'long_gap_ms_range':[gap_ms_min,gap_ms_max] if gap_count else None,
            'presentation_interval_ms_range':[min(interval_values)*1000/CORE_HZ,max(interval_values)*1000/CORE_HZ] if interval_values else None}


def build_comparison(rows65,rows60,ppm,phase_steps,frames):
    pairs=[]
    for dppm in ppm:
        for sppm in ppm:
            for k in range(phase_steps):
                phase=k/phase_steps
                a=replay(rows65,17.029,dppm,sppm,phase,frames)
                b=replay(rows60,18.470,dppm,sppm,phase,frames)
                pairs.append({'display_ppm':dppm,'source_ppm':sppm,'phase_fraction':phase,'nominal_65hz':a,'hypothetical_60hz':b,
                              'delta_60_minus_65':{
                                  'max_age_ms':b['max_arrival_to_presentation_age_ms']-a['max_arrival_to_presentation_age_ms'],
                                  'presentations_in_window':b['presentations_in_window']-a['presentations_in_window'],
                                  'long_gap_count':b['long_gap_count_in_window']-a['long_gap_count_in_window']}})
    def summary(clock):
        vals=[p[clock] for p in pairs]
        return {'fps_range':[min(x['rate_fps_first_to_last'] for x in vals),max(x['rate_fps_first_to_last'] for x in vals)],
                'max_age_ms_range':[min(x['max_arrival_to_presentation_age_ms'] for x in vals),max(x['max_arrival_to_presentation_age_ms'] for x in vals)],
                'capture_count_in_60s_range':[min(x['captures_in_window'] for x in vals),max(x['captures_in_window'] for x in vals)],
                'presentation_count_in_60s_range':[min(x['presentations_in_window'] for x in vals),max(x['presentations_in_window'] for x in vals)],
                'long_gap_count_range':[min(x['long_gap_count_in_window'] for x in vals),max(x['long_gap_count_in_window'] for x in vals)]}
    return {'model':'paired analytical replay repeating measured ten-frame service traces; identical phase and ppm grid; ideal periodic display boundaries',
            'capture_window_seconds':CAPTURE_WINDOW_SECONDS,'simulated_frames_per_case':frames,
            'source_evidence':{'nominal_65hz':'../cadence-study/verilator-65hz.log','hypothetical_60hz':'../cadence-study/verilator-60hz-hypothetical.log'},
            'phase_steps_per_clock_pair':phase_steps,'ppm_values':ppm,'paired_case_count':len(pairs),
            'nominal_65hz_summary':summary('nominal_65hz'),'hypothetical_60hz_summary':summary('hypothetical_60hz'),
            'interpretation':{'long_gap':'Presentation interval exceeds 1.1 of the modeled source periods. This cadence marker does not prove a lost frame.',
                              'capture_window':'Counts modeled source arrivals and LCD presentations before epoch + 60 seconds; 1,800 captures represent a nominal 30 Hz source sampled over a half-open 60-second window.',
                              'backlog':'Each modeled frame starts no earlier than one cycle after the prior presentation. Arrivals can therefore wait indefinitely behind prior presentations. The model has an unbounded hypothetical backlog and no drop queue; long ages depend on this scheduling rule and are not a finite-queue or transport prediction.',
                              'limits':['only the first ten measured service patterns are repeated','not an 1,800-frame RTL run','no bounded queue or drop policy; no network, ESP32, RF, capture, or hardware behavior','ppm and phase values are hypothetical, not measured tolerances','no sustained 30 displayed fps or hardware proof']},
            'paired_cases':pairs}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('nominal_65hz_log',type=Path)
    p.add_argument('hypothetical_60hz_log',type=Path)
    p.add_argument('--frames',type=int,default=1800)
    p.add_argument('--ppm',type=float,nargs='*',default=[-1000,-500,-100,-10,0,10,100,500,1000])
    p.add_argument('--phase-steps',type=int,default=20)
    p.add_argument('--output',type=Path)
    p.add_argument('--summary',type=Path)
    a=p.parse_args()
    if a.frames<10 or a.phase_steps<2: p.error('need >=10 frames and >=2 phase steps')
    result=build_comparison(read_frames(a.nominal_65hz_log),read_frames(a.hypothetical_60hz_log),a.ppm,a.phase_steps,a.frames)
    encoded=json.dumps(result,indent=2)+'\n'
    if a.output: a.output.write_text(encoded)
    if a.summary:
        lines=['# Cadence sensitivity summary','','**Analytical sensitivity estimate only; not an 1,800-frame RTL run or hardware proof.**','',
               f"Paired cases: {result['paired_case_count']}; captures modeled per case: {a.frames}; capture window: 60 s; phase steps: {a.phase_steps}; ppm set: {a.ppm}.",'',
               '| Modeled timing | First-to-last rate (fps) | Max age (ms) | Captures / 60 s | Presents / 60 s | Gaps / 60 s |',
               '|---|---:|---:|---:|---:|---:|']
        for label,key in [('Nominal ~65 Hz','nominal_65hz_summary'),('Hypothetical ~60 Hz','hypothetical_60hz_summary')]:
            x=result[key]
            lines.append(f"| {label} | {x['fps_range'][0]:.4f}–{x['fps_range'][1]:.4f} | {x['max_age_ms_range'][0]:.3f}–{x['max_age_ms_range'][1]:.3f} | {x['capture_count_in_60s_range'][0]}–{x['capture_count_in_60s_range'][1]} | {x['presentation_count_in_60s_range'][0]}–{x['presentation_count_in_60s_range'][1]} | {x['long_gap_count_range'][0]}–{x['long_gap_count_range'][1]} |")
        lines += ['', 'Each paired case applies the same display/source ppm offsets and phase fraction to both traces. Gap count and duration range report intervals greater than 1.1 modeled source periods; gaps do not prove frame loss. Capture count is source arrivals in the half-open 60-second window. Arrivals wait for prior presentations with no backlog limit or drop policy, so long age results depend on this unbounded scheduling assumption. Service traces repeat ten measured frames and ignore variable contention.']
        a.summary.write_text('\n'.join(lines)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='paired_cases'},indent=2))

if __name__=='__main__': main()
