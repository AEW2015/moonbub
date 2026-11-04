#!/usr/bin/env python3
"""Bounded memory/line scheduling from retained actual native packet traces."""
from dataclasses import replace
import hashlib,importlib.util,json,sys,time
from pathlib import Path
import numpy as np
import model
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE.parent/'python-game-unified-codec-study'))
import unified_codec as codec

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def input_traces():
    d=json.loads((HERE.parent/'python-game-decoder-budget-study/results.json').read_text());out=[]
    for t in d['traces']:
        if 'native' not in t['label'] or '_gm_' not in t['label']:continue
        m=codec.identity(bytes.fromhex(t['packet_hex']),decode=True);stripes=[]
        for plane,c in enumerate(m['parsed']['coefficients']):
            w,h=(720,480) if plane==0 else (360,240)
            a=c.reshape((h//8,w//8,64))
            for row in range(len(a)):
                blocks=a[row];general=np.any(blocks[:,1:]!=0,axis=1);dc=~general&(blocks[:,0]!=0)
                stripes.append(dict(plane=plane,width=w,rows=8,y=row*8,blocks=len(blocks),general=int(general.sum()),dc=int(dc.sum()),zero=int((~general&~dc).sum())))
        item={k:t[k] for k in ['label','width','height','key','publication','packet_bytes','packet_sha256','plane_payload_bytes','crc_validation_bytes','ui_pixels']}
        item['stripes']=stripes;item['coefficient_source']='actual retained GM01 coefficients decoded by frozen AR02 parser'
        assert sum(s['general'] for s in stripes)==sum(p['general_inverse'] for p in t['planes'])
        out.append(item)
    assert len(out)==3
    return out

def pins():
    data=json.loads((HERE.parent/'python-game-decoder-budget-study/results.json').read_text())
    paths={ROOT/p for p in data['source_sha256']}
    paths.add(HERE.parent/'python-game-decoder-budget-study/results.json')
    paths.update(HERE/n for n in ['model.py','benchmark.py','verify.py','test_model.py'])
    return {p.relative_to(ROOT).as_posix():digest(p) for p in sorted(paths)}

def build():
    before=pins();traces=input_traces();native_p=traces[2];cases=[];started=time.perf_counter()
    nominal=model.Config();fast=replace(nominal,name='hypothetical_fast',read_cycles=8,write_cycles=8,mac_lanes=16,entropy_bits_per_cycle=8,sample_positions_per_cycle=4)
    # Traffic templates: one warm-start key, then ordinary Ps with a native
    # promotion demand every16IDs. This is not a byte-valid AR02 reference stream.
    pattern=[traces[0]]+[traces[1] if i%16==0 else native_p for i in range(1,30)]
    scenarios=[('nominal_baseline',nominal),('nominal_streaming',replace(nominal,mode='streaming')),
               ('fast_baseline',fast),('fast_streaming',replace(fast,mode='streaming')),
               ('fast_streaming_one_line',replace(fast,mode='streaming',prefetch_lines=1)),
               ('fast_streaming_stall_4lines',replace(fast,mode='streaming',stall_cycles=20000,stall_period=100000,stall_phase=20000)),
               ('fast_streaming_stall_8lines',replace(fast,mode='streaming',prefetch_lines=8,stall_cycles=20000,stall_period=100000,stall_phase=20000)),
               ('current_2MiB_window',replace(nominal,address_window_bytes=2*1024*1024))]
    for name,cfg in scenarios:
        cfg=replace(cfg,name=name);r=model.simulate(pattern,cfg);cases.append(dict(name=name,result=r))
        print(json.dumps(summary(cases[-1])),flush=True)
    # Explicit short phase sweep: unchanged traffic and service, varied relative
    # refresh/stall phase; repeated templates are not additional native samples.
    phase=[]
    for offset in [0,195,390,585]:
        cfg=replace(fast,mode='streaming',name='phase'+str(offset),frames=6,drain_ms=100,refresh_phase=offset,prefetch_lines=2,stall_cycles=5000,stall_period=100000,stall_phase=offset)
        r=model.simulate(pattern,cfg);phase.append(dict(name=cfg.name,result=r))
    assert before==pins()
    return dict(evidence='Request-level bounded memory/scanline schedule from actual decoded coefficient-count templates; conditional, not command-level RTL or physical deadline proof',
                source_sha256=before,input_traces=traces,cases=cases,phase_cases=phase,python_wall_seconds=time.perf_counter()-started,
                limits=['One chip/bank address mapping, assumed 8MiBimplementedwindow;2MiBwindow explicitlyrejected',
                        '800x480landscape-equivalent uniform60Hzscan;no fittedpanelblanking/physicalorientationproof',
                        'Warm-startblackfront andprefilledscanlineFIFO excludedfromobservedservice;all3panelborderspreinitialized',
                        'Actualcoefficientblockcounts butbyte/workdemandtemplates repeated;notvalidAR02packet/referenceidentityreplay',
                        'Streamingentropybytes apportionedbyblockcount;boundedproducer/actualparsernotimplemented',
                        'AssumedintegerissueCRC/SHA/pairedchroma rates;noDSPwidth/map/clockclosureproof',
                        'Request-levelrowhit/rowchange/turnaround/refresh/stalls;notJEDECcommand/timingorelectricalpartmodel',
                        'FIFO/metadata/stripeallocations arecapacitybudgets,notBRAMpacking/fitting',
                        'No RF/ESP/capture service;complete packet readyatcapture;do notcombineFPSarithmeticallywithgatewaystudy'])

def summary(case):
    r=case['result']
    return dict(name=case['name'],status=r['status'],external_bytes=r['allocation']['external_address_end'],local_bytes=r['allocation']['local_total'],
                misses=r.get('display_line_misses'),strict=r.get('strict_presentations'),eventual=r.get('eventual_presentations'),
                steady_ids_per_second=r.get('steady_ids_per_second'),clean_steady_ids_per_second=r.get('clean_steady_ids_per_second'),clean_eventual=r.get('clean_eventual_unique_ids'),completed=len(r.get('completed',[])),drops=r.get('drops_by_reason'),
                decoder_drained=r.get('decoder_drained'),unresolved=r.get('unresolved_ids'))
if __name__=='__main__':
    d=build();(HERE/'results.json').write_text(json.dumps(d,indent=2)+'\n')
