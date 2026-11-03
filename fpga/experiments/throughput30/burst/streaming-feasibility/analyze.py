#!/usr/bin/env python3
"""Conditional packet-burst storage bound; not an RTL or target execution."""
import argparse, hashlib, json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'host'))
from moonshine.protocol import packets, parse_packet

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--fixtures', required=True, type=Path)
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    burst = ROOT/'fpga/experiments/throughput30/burst'
    trace = burst/'network-rtl-study/results-clean/packet-trace.jsonl'
    log = burst/'latency-followup/results/baseline/run.log'
    events = [json.loads(s) for s in trace.read_text().splitlines()]
    rows = [{k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',line)}
            for line in log.read_text().splitlines() if line.startswith('FRAME_RESULT ')]
    assert len(rows)==10 and len(events)==267
    assert all(e['reference_outcome'] in ('partial','done') for e in events)
    for i in (0, 1):
        group = [e for e in events if e['id']==i]
        jpeg = (a.fixtures/f'{i:04}.jpg').read_bytes()
        payload = list(packets(jpeg, i, group[0]['capture_cycle']//100))
        byoff = {parse_packet(x).offset:x for x in payload}
        assert len(group)==len(payload)
        for e in group:
            packet=byoff[e['offset']]
            assert hashlib.sha256(packet).hexdigest()==e['datagram_sha256']
            assert len(parse_packet(packet).payload)==e['payload_bytes']
    frame0=[e for e in events if e['id']==0]
    frame1=sorted((e for e in events if e['id']==1), key=lambda e:e['arrival_cycle'])
    assert frame1[0]['offset']==0
    eof0=next(e['arrival_cycle'] for e in frame0 if e['reference_outcome']=='done')
    # Sampled minimum from this baseline only; emphatically not a certified bound.
    sampled_min=min(r['decode_ready_cycle']-r['commit_cycle'] for r in rows)
    def scenario(decode):
        until=eof0+decode
        backlog=[e for e in frame1 if e['arrival_cycle']<until]
        return dict(decode_cycles=decode, hypothetical_core_free_cycle=until,
                    incoming_packets_before_free=len(backlog),
                    incoming_payload_bytes_before_free=sum(e['payload_bytes'] for e in backlog),
                    fifth_packet_cycle=frame1[4]['arrival_cycle'], sixth_packet_cycle=frame1[5]['arrival_cycle'])
    result=dict(trace_scope='clean 8 Mbps synthetic trace, first adjacent frames only',
                frame0_complete_cycle=eof0, frame1_sof_cycle=frame1[0]['arrival_cycle'],
                slot_count=5, slot_payload_capacity=1024,
                sampled_min_decode_ms=sampled_min/100000,
                sampled_decode_scenario=scenario(sampled_min), zero_decode_control=scenario(0),
                caveat='Instant QSPI and CRC, no vblank wait; sampled decode not a proven lower bound, not RTL streaming or target execution')
    if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__': main()
