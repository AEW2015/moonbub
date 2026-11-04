#!/usr/bin/env python3
"""Replay real AR02 frame sizes through a hypothetical firmware-shaped gateway."""
from dataclasses import replace
import hashlib,json
from pathlib import Path
import gateway,facts
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
TRACE='experiments/python-game-refresh-v16-study/results.json'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def run():
    f=facts.extract();paths=[HERE/n for n in ['gateway.py','facts.py','benchmark.py','verify.py','test_gateway.py']]+[ROOT/TRACE]
    pins={p.relative_to(ROOT).as_posix():sha(p) for p in paths};pins.update(f['source_sha256'])
    data=json.loads((ROOT/TRACE).read_text());workloads=[]
    for profile in ['gm_initial_only','gm_refresh30','gm_refresh30_coarse']:
        candidates=[c for c in data['cases'] if c['profile']==profile]
        if not candidates:continue
        c=candidates[0];frames=[dict(id=p['id'],bytes=p['bytes']) for p in c['result']['packets'] if p['admitted']]
        workloads.append(dict(profile=profile,frames=frames,source_scope='Actual admitted v16 AR02 frame sizes re-scheduled by sourceID at30fps; not complete180inputframes and not MSV1 JPEG bytes.'))
    assert len(workloads)>=2,[c['profile'] for c in data['cases']]
    workloads.append(dict(profile='cap_stress_60',frames=[dict(id=i,bytes=49152) for i in range(60)],
                          source_scope='Hypothetical60maximumAR02sizeframesat30HzusingMSV1shaped1024+40+28transport; notinstalledprotocolinteroperability.'))
    base=gateway.Config(cpu_hz=f['cpu_hz'],mailbox_packets=f['udp_mailbox_packets'],chunk=f['payload_bytes'],header=f['header_bytes'],
                        qspi_write_hz=f['qspi_write_clock_cap_hz'],qspi_read_hz=f['qspi_read_clock_cap_hz'])
    profiles=[replace(base,name='optimistic',cpu_fraction=.8,crc_cycles_per_bit_step=3,packet_fixed_cycles=500,driver_call_us=5,poll_jitter_us=0,abort_recovery_ms=0),
              base,replace(base,name='conservative',cpu_fraction=.35,crc_cycles_per_bit_step=10,packet_fixed_cycles=4000,driver_call_us=60,poll_jitter_us=100),
              replace(base,name='nominal_burst8',burst_packets=8),
              replace(base,name='nominal_lock_busy',lock_busy_ms=.5,lock_phase_ms=5),
              replace(base,name='lock_busy_abort100ms',lock_busy_ms=.5,lock_phase_ms=5,abort_recovery_ms=100),
              replace(base,name='slow_fpga_unsafe_credit',fifo_bytes=2048,fpga_drain_bytes_per_second=400_000),
              replace(base,name='slow_fpga_bounded_wait',fifo_bytes=2048,fpga_drain_bytes_per_second=400_000,fifo_policy='bounded_fifo_wait',maximum_fifo_wait_ms=4)]
    rows=[dict(workload=w['profile'],result=gateway.simulate(w['frames'],cfg)) for w in workloads for cfg in profiles]
    sweep=[]
    for mbps in [4,8,12,16,24]:
        for burst in [1,4,8,12]:
            cfg=replace(base,wifi_payload_mbps=mbps,burst_packets=burst,name=f'link{mbps}_burst{burst}')
            r=gateway.simulate(workloads[0]['frames'],cfg)
            sweep.append(dict(link_mbps=mbps,burst=burst,completed=r['completed_frames'],frames=r['frames'],mailbox_full=r['counters'].get('mailbox_full',0),peak_mailbox=r['peak_mailbox'],max_age_ms=r['maximum_completed_age_ms']))
    ram=[gateway.ram_budget(f,available_internal_bytes=n*1024) for n in [256,320,384]]
    assert pins=={p:sha(ROOT/p) for p in pins}
    return dict(facts=f,source_sha256=pins,workloads=workloads,scenarios=rows,link_burst_sweep=sweep,ram_scenarios=ram,
                note='Hypothetical AR02 port gateway sensitivity using current MSV1 JPEG firmware constraints, not firmware interoperability or ESP32/Renode/ISA emulation.',
                limits=['CPUcycles/CRC/copy/drivercosts andWiFi/UIshare unmeasured','One serialized gateway task; no dualcore/ISR/cache/lwIP scheduler emulation',
                        'Radio losses/retransmits/TCPIP buffers and actualSPI arbitration absent','Bounded FIFOwait assumes new FIFOcredit contract; installed register is remainingframe only',
                        'RAM reserves illustrative; network payload reserves may alias; no measuredfreeheap/largestblock orPSRAM',
                        'Completegatewayframes notdecoded/displayed frames; AR02 feedback/dependencies notmodeled'])

def main():
    d=run();(HERE/'results.json').write_text(json.dumps(d,indent=2)+'\n')
    for row in d['scenarios']:
        r=row['result'];print(row['workload'],r['config']['name'],r['completed_frames'],r['frames'],r['counters'],r['maximum_completed_age_ms'])
if __name__=='__main__':main()
