#!/usr/bin/env python3
"""Finite source-size admission/pacing/credit evidence; no hardware rates."""
from dataclasses import replace
import hashlib
import importlib.util
import json
from pathlib import Path
import model

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
TRACE=ROOT/'experiments/python-game-refresh-v16-study/results.json'
FACTS=ROOT/'experiments/python-game-esp32-gateway-study/results.json'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pins():
    paths=[HERE/name for name in ('model.py','benchmark.py','verify.py','test_model.py')]
    paths.extend([Path(model.frozen.__file__),TRACE,FACTS])
    d=json.loads(FACTS.read_text())
    paths.extend(ROOT/name for name in d['facts']['source_sha256'])
    return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(set(paths))}
def workloads():
    d=json.loads(TRACE.read_text());out=[]
    for profile in ('gm_initial_only','gm_refresh30','gm_refresh30_coarse'):
        c=next(c for c in d['cases'] if c['profile']==profile)
        frames=[dict(id=p['id'],bytes=p['bytes']) for p in c['result']['packets'] if p['admitted']]
        out.append(dict(profile=profile,frames=frames,scope='Retained admitted AR02 body sizes re-scheduled at sourceID/30, not actual encode completion or a joint codec run. Missing captureIDs stay missing.'))
    out.append(dict(profile='cap_stress60',frames=[dict(id=i,bytes=49152) for i in range(60)],scope='Synthetic maximum-size bodies, not encoded native frames.'))
    return out

def brief(row):
    r=row['result'];return dict(workload=row['workload'],profile=row['profile'],source_frames=r['input_frames'],capture_ids=r['capture_id_denominator'],admitted=len(r['admissions']),
        strict=r['strict_complete'],eventual=r['eventual_complete'],max_age_ms=r['maximum_gateway_age_ms'],
        data_bytes=r['ipv4_udp_data_bytes'],feedback_bytes=r['feedback_wire_bytes'],query_bytes=r['query_wire_bytes'],
        drops=dict(__import__('collections').Counter(d['reason'] for d in r['drops'])),mailbox_drops=r['counters'].get('mailbox_full',0),
        queries=r['counters'].get('credit_queries',0),all_issued=r['all_admitted_packets_issued'],
        peak_credits=r['peak_packet_credits'],peak_mailbox=r['peak_receiver_mailbox'])

def build():
    before=pins();cfg=model.frozen.Config(chunk=1008,header=56,fifo_policy='bounded_fifo_wait');p=model.Policy()
    profiles=[('paced',cfg,replace(p,aggregate_ms=0)),('aggregate2',cfg,replace(p,aggregate_ms=2)),
        ('aggregate8',cfg,p),('feedback20',cfg,replace(p,aggregate_ms=2,feedback_latency_ms=20)),
        ('feedback_recovery',cfg,replace(p,aggregate_ms=2,drop_first_feedback=True,inject_stale_feedback=True,inject_foreign_feedback=True)),
        ('feedback_blackhole',cfg,replace(p,aggregate_ms=2,lose_all_feedback=True)),
        ('conservative_worker',replace(cfg,cpu_fraction=.35,crc_cycles_per_bit_step=10,packet_fixed_cycles=4000,driver_call_us=60,poll_jitter_us=100),replace(p,aggregate_ms=2)),
        ('slow_true_fifo',replace(cfg,fifo_bytes=2048,fpga_drain_bytes_per_second=400000,maximum_fifo_wait_ms=10),replace(p,aggregate_ms=2)),
        ('slow_unsafe_fifo',replace(cfg,fifo_policy='remaining_frame_credit',fifo_bytes=2048,fpga_drain_bytes_per_second=400000),replace(p,aggregate_ms=2))]
    inputs=workloads();rows=[]
    for w in inputs:
        for label,c,policy in profiles:
            row=dict(workload=w['profile'],profile=label,result=model.run(w['frames'],c,policy));rows.append(row)
    assert pins()==before
    return dict(evidence='Bounded prospective host frame admission and consumed-packet credit pacing under firmware-shaped service assumptions',source_sha256=before,
        case_count=len(rows),workloads=inputs,cases=rows,summary=[brief(r) for r in rows],
        prospective_framing=dict(header_bytes=56,payload_bytes=1008,max_udp_datagram_bytes=1064,esp_dma_allocation_bytes=1065,
            credit_extension='Budgeted16bytes:sessionu32,slotu16,reservedu16,seq64;notserializedwireimplementation',feedback_ipv4_udp_bytes=92,query_ipv4_udp_bytes=60),
        bounds='Oneactivehostframe+one latest source;≤6data tokens+onecontrolquery;oneDMAbuffer+6UDPmailbox;6creditledgerrows;no creditreclaimed on timeout.',
        limitations=['No FPGA decode/UI/presentation or AR02 dependency/ACK integration; sizes only, sourceIDs retained. Latestdropping opaque alreadyencoded key/promotion/P packets may invalidate reference history; not decoder-valid trace.',
          'Packet-consumed credits are not decoded reference-publication ACKs. Live admission needs candidate-before-commit integration or safe expire/fallback with tagged reference state.',
          'New packet-consumption credit/ledger query protocol unsupported by installed MSV1 firmware; GF02 framing differs',
          'Costs configured from v16 assumption model, not calibrated ESP32 ISA/firmware/RF traces',
          'Prospective trueFIFOwait contract is not current remaining-frame register; current FIFOunsafe case remains separate',
          'Admission estimate uses configured costs not receiverqueue/FIFO/ledger future state; it is not a deadline proof',
          'Aggregation buckets/feedback fault delivery are declared synthetic service patterns, not RF emulator',
          'No adaptive decode quality or pixel comparison; admission maydrop sourceIDs and cannot establish30distinctdisplayedFPS',
          'All-feedbackloss leaves admitted frame partly issued and credits held; safety-stop is not successful physical/protocol drain'])

def main():
    d=build();(HERE/'results.json').write_text(json.dumps(d,separators=(',',':'))+'\n')
    for r in d['summary']:print(json.dumps(r),flush=True)
if __name__=='__main__':main()
