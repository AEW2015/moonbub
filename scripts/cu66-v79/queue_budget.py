#!/usr/bin/env python3
"""Charge actual fixture bytes to the immutable-packet queue in completed replays.

This is an endpoint model, not live ESP32 Wi-Fi/QSPI or a claim about free SRAM.
Waiting packets and the active packet remain owned through processor COMMIT ACK.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT/'fpga/experiments/cu66-v79'
NATIVE = ROOT/'experiments/cu66-native-v69'


def charge(frames):
    events = []
    for f in frames:
        identity = f['generation']
        assert 0 < f['bytes'] <= 49152
        assert f['release'] <= f['admission'] < f['ack']
        events += [(f['release'],0,identity,f['bytes']),
                   (f['admission'],1,identity,f['bytes']),
                   (f['ack'],2,identity,f['bytes'])]
    waiting, active = {}, {}
    peak_waiting_bytes = peak_owned_bytes = peak_waiting = peak_owned = 0
    for cycle, kind, identity, size in sorted(events):
        if kind == 0:
            assert identity not in waiting and identity not in active
            waiting[identity] = size
        elif kind == 1:
            assert waiting.pop(identity) == size and identity not in active
            active[identity] = size
            assert len(active) <= 1, 'current receiver is single candidate'
        else:
            assert active.pop(identity) == size
        waiting_bytes = sum(waiting.values())
        peak_waiting_bytes = max(peak_waiting_bytes, waiting_bytes)
        peak_owned_bytes = max(peak_owned_bytes, waiting_bytes+sum(active.values()))
        peak_waiting = max(peak_waiting, len(waiting))
        peak_owned = max(peak_owned, len(waiting)+len(active))
    assert not waiting and not active
    return dict(max_waiting_packets=peak_waiting,max_waiting_bytes=peak_waiting_bytes,
                max_owned_packets_including_active=peak_owned,max_owned_bytes_including_active=peak_owned_bytes,
                fixed_48KiB_slot_pool_bytes=peak_owned*49152,
                budget_bytes_required_without_drops=peak_owned_bytes,
                illustrative_budget_pass={str(size):peak_owned_bytes <= size
                                          for size in (49152,65536,131072,262144)},
                illustrative_fixed_slot_budget_pass={str(size):peak_owned*49152 <= size
                                          for size in (49152,65536,131072,262144)})


def main():
    # Unit control: the old active packet cannot be released at admission.
    control = charge([dict(generation=1,bytes=20,release=0,admission=1,ack=10),
                      dict(generation=2,bytes=30,release=5,admission=11,ack=20)])
    assert control['max_owned_bytes_including_active'] == 50
    assert control['max_waiting_packets'] == 1
    rows, pins = [], {}
    index = NATIVE/'index.tsv'
    pools = {}
    for line in index.read_text().splitlines():
        cohort, ordinal, packet = line.split('\t')[:3]
        pool = pools.setdefault(int(cohort), [])
        assert int(ordinal) == len(pool), 'fixture chronology'
        pool.append(NATIVE/packet)
    pins[str(index.relative_to(ROOT))] = hashlib.sha256(index.read_bytes()).hexdigest()
    pins[str(Path(__file__).resolve().relative_to(ROOT))] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    for path in sorted((AREA/'system').glob('cohort*/results.json')):
        d = json.loads(path.read_text())
        pins[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        if d['status'] != 'PASS_ACTUAL_DECODE_CANONICAL_AND_NATIVE_DISPLAY':
            rows.append(dict(run=path.parent.name,status='FAIL_SOURCE_CAMPAIGN',failure=d.get('failure')))
            continue
        packets = pools[d['cohort']][:len(d['timings'])]
        assert len(packets) == len(d['timings']), 'fixture/timing count mismatch'
        frames = []
        for tm, packet in zip(d['timings'],packets):
            pins[str(packet.relative_to(ROOT))] = hashlib.sha256(packet.read_bytes()).hexdigest()
            frames.append(dict(generation=tm['generation'],bytes=packet.stat().st_size,
                 release=tm['packet_complete_cycle'],admission=tm['admission_cycle'],ack=tm['commit_ack_cycle']))
        result = charge(frames)
        assert result['max_waiting_packets'] == d['summary']['max_waiting_released_unadmitted']
        assert result['max_owned_packets_including_active'] == d['summary']['max_total_released_unacked']
        rows.append(dict(run=path.parent.name,status='PASS_ENDPOINT_QUEUE_ACCOUNTING',cohort=d['cohort'],
                         sources=len(frames),packet_bytes_min=min(f['bytes']for f in frames),
                         packet_bytes_max=max(f['bytes']for f in frames),**result))
    output = dict(schema='cu79-immutable-packet-queue-budget-v1',source_sha256=pins,
        control_tests=1,runs=rows,
        contract=['Charge complete original fixtures on immutable ingress-complete, retain through processor COMMIT ACK.',
                  'Conservative equal-cycle event order: release, admission, ACK. No drop, timer reset or host backpressure inserted.',
                  'Budget values are illustrative endpoint reservations, not measured free ESP32 SRAM.',
                  'Actual-byte ownership assumes allocation sized to packets; fixed48KiB slot-pool reservations are reported separately.',
                  'Excludes Wi-Fi/lwIP/QSPI DMA copies, Slint/application buffers, stack/heap/fragmentation and target CPU execution.',
                  'No live transport, ESP32 queue-capacity qualification or permission to infer physical30fps.'])
    (AREA/'queue-budget.json').write_text(json.dumps(output,indent=2)+'\n')
    for r in rows:
        print(r['run'],json.dumps({k:v for k,v in r.items()if k not in ('run','status')}))


if __name__ == '__main__':
    main()
