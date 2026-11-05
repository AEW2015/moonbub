#!/usr/bin/env python3
"""Compare exact key+P command-model runs without inferring physical cadence."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'fpga/experiments/cu66-v71/system'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    old_path = ROOT / 'fpga/experiments/cu66-v70/system/full-strip/results.json'
    new_path = AREA / 'full-strip/results.json'
    old, new = [json.loads(p.read_text()) for p in (old_path, new_path)]
    assert old['strip'] and new['strip'] and old['clocks'] == new['clocks']
    assert old['status'] == new['status'] == 'PASS_FUNCTIONAL_MEMORY_AND_FRAMEBUFFERS'
    common = old['source_sha256'].keys() & new['source_sha256'].keys()
    assert common and all(old['source_sha256'][p] == new['source_sha256'][p] for p in common)
    assert new['summary']['complete_frames'] == 2
    assert len({f['fid'] for f in new['frames']}) == 2
    period_ps = new['clocks']['memory_period_ps']
    rows = []
    for a, b, timing in zip(old['frames'], new['frames'], new['timings'], strict=True):
        assert (a['fid'], a['key'], a['generation']) == (b['fid'], b['key'], b['generation'])
        assert a['actual_writes'] == b['actual_writes'] == 664320
        assert timing['fid'] == b['fid'] and timing['generation'] == b['generation']
        assert timing['packet_complete_cycle'] <= timing['admission_cycle'] < timing['validated_ready_cycle'] < timing['rgb_ready_cycle'] <= timing['commit_ack_cycle']
        rows.append(dict(
            fid=b['fid'], key=bool(b['key']), v70=a, v71=b,
            v70_transaction_model_ms=a['cycles'] * period_ps / 1e9,
            v71_transaction_model_ms=b['cycles'] * period_ps / 1e9,
            transaction_cycle_reduction_percent=100 * (a['cycles'] - b['cycles']) / a['cycles'],
            v71_validated_decode_model_ms=timing['validated_decode_model_cycles'] * period_ps / 1e9,
            v71_composition_model_ms=timing['composition_model_cycles'] * period_ps / 1e9,
            complete_rasters=timing['complete_rasters']))
    result = dict(
        status='PASS_EXACT_OUTPUT_COMPARISON', frames=rows,
        shared_source_pins_compared=len(common),
        summary=dict(v70_underruns=old['summary']['total_underruns'],
                     v71_underruns=new['summary']['total_underruns'],
                     v71_distinct_complete_presentations=new['summary']['distinct_complete_presentations']),
        clocks=new['clocks'],
        input_sha256={str(p.relative_to(ROOT)): sha(p) for p in (old_path, new_path)},
        script_sha256=sha(Path(__file__).resolve()),
        limitations=[
            'decoder-paced chronological key+P pair; not a fixed-arrival sustained-throughput campaign',
            'transaction duration changes concurrent LCD work; compare timings, not normalized underrun rates',
            'model latency omits processor execution and live transport; not validated target decoding',
            'no target fit/Fmax, physical SDRAM, CDC signoff, 30fps, or sub10ms proof'])
    (AREA / 'comparison.json').write_text(json.dumps(result, indent=2) + '\n')
    for row in rows:
        print(f"FRAME{row['fid']} transaction_ms_v70={row['v70_transaction_model_ms']:.5f} v71={row['v71_transaction_model_ms']:.5f} reduction={row['transaction_cycle_reduction_percent']:.3f}% validated_model_ms={row['v71_validated_decode_model_ms']:.5f}")
    print('V71_COMPARISON_PASS ' + json.dumps(result['summary'], sort_keys=True))

if __name__ == '__main__':
    main()
