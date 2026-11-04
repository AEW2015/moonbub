#!/usr/bin/env python3
"""Recompute firmware facts and deterministic gateway evidence, without hardware."""
import hashlib,json
from pathlib import Path
import facts,gateway
from dataclasses import replace
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def main():
    d=json.loads((HERE/'results.json').read_text())
    for rel,expected in d['source_sha256'].items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==expected,rel
    assert d['facts']==facts.extract()
    workloads={w['profile']:w['frames'] for w in d['workloads']}
    for row in d['scenarios']:
        r=row['result'];assert r==gateway.simulate(workloads[row['workload']],gateway.Config(**r['config']))
        assert r['peak_mailbox']<=6 and r['peak_dma_working_packets']<=1 and r['queue_drained']
        assert r['packets']==r['counters']['arrived']==r['counters']['serviced']+r['counters'].get('mailbox_full',0)
        assert r['completed_frames']+len(r['failed_frames'])==r['frames']
        assert not r['protocol_supported_by_current_firmware'] and not r['physical_30fps_proven']
    for row in d['link_burst_sweep']:
        r=gateway.simulate(d['workloads'][0]['frames'],replace(gateway.Config(),wifi_payload_mbps=row['link_mbps'],burst_packets=row['burst'],name=f"link{row['link_mbps']}_burst{row['burst']}"))
        assert row==dict(link_mbps=row['link_mbps'],burst=row['burst'],completed=r['completed_frames'],frames=r['frames'],mailbox_full=r['counters'].get('mailbox_full',0),peak_mailbox=r['peak_mailbox'],max_age_ms=r['maximum_completed_age_ms'])
    for r in d['ram_scenarios']:assert r==gateway.ram_budget(d['facts'],available_internal_bytes=r['assumed_available_internal_bytes'])
    print('PASS:source-extractedESP32constraints;bounded6UDP+1DMA;deterministicCPU/QSPI/FIFO/lockscenarios;noESPqualification')
if __name__=='__main__':main()
