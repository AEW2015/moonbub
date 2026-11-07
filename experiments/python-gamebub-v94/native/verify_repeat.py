#!/usr/bin/env python3
"""Compare actual packet bytes and decoder metrics across two finished campaigns."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

AREA = Path(__file__).resolve().parent
ROOT = AREA.parents[2]
METRICS = ('ab_decisions', 'ab_renorm', 'literal_bits', 'ans_symbols', 'ans_renorm_bytes', 'model_tables', 'model_entries', 'ans_lanes')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('first', type=Path)
    parser.add_argument('second', type=Path)
    args = parser.parse_args()
    indexes = [json.loads(p.read_text()) for p in (args.first, args.second)]
    assert all(d['status'] == 'PASS_NATIVE_ALL_9_INDEPENDENT_PYTHON_ALL_8_COMPOSITION_LOCAL' for d in indexes)
    assert indexes[0]['source_sha256'] == indexes[1]['source_sha256']
    spec = importlib.util.spec_from_file_location('ec94_repeat_data', AREA / 'data.py')
    data = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(data)
    frames = chunks = packets = packet_bytes = 0
    digest = hashlib.sha256()
    candidate_metrics = [{key: 0 for key in METRICS} for _ in range(9)]
    candidate_bytes = [0] * 9
    choices = [0] * 8
    for left, right in zip(data.iter_frames(index_path=args.first), data.iter_frames(index_path=args.second), strict=True):
        assert all(left[k] == right[k] for k in ('cohort', 'fid', 'ordinal', 'key', 'canonical_coefficients_sha256'))
        for lp, rp in zip(left['variants']['65536'], right['variants']['65536'], strict=True):
            for lc, rc in zip(lp, rp, strict=True):
                assert lc['ec94'] == rc['ec94'], 'actual packet bytes changed'
                for lm, rm in zip(lc['ec94_stats']['masks'], rc['ec94_stats']['masks'], strict=True):
                    assert lm == rm, 'packet SHA, selector, or decoder metrics changed'
                assert lc['ec94_stats']['method_stream_bytes'] == rc['ec94_stats']['method_stream_bytes']
                for i, packet in enumerate(lc['ec94']):
                    digest.update(len(packet).to_bytes(4, 'little'))
                    digest.update(packet)
                    packets += 1
                    packet_bytes += len(packet)
                    candidate_bytes[i] += len(packet)
                    for key in METRICS:
                        candidate_metrics[i][key] += sum(lc['ec94_stats']['masks'][i][key])
                for alternative in lc['ec94_stats']['masks'][8]['methods']:
                    choices[alternative] += 1
                chunks += 1
        frames += 1
    assert frames == 457 and chunks == 1371 and packets == 12339
    report = dict(schema='ec94-repeat-actual-packets-v1', status='PASS', native_sources=frames, chunks=chunks,
                  actual_packets=packets, actual_packet_bytes=packet_bytes, all_packet_framed_sha256=digest.hexdigest(),
                  compared_reports=[str(p.resolve().relative_to(ROOT)) for p in (args.first, args.second)],
                  source_sha256=indexes[0]['source_sha256'], candidate_bytes=candidate_bytes,
                  candidate_decoder_metrics=candidate_metrics, local_alternative_context_counts=choices,
                  verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (AREA / 'repeat-check.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: report[key] for key in ('status', 'actual_packets', 'all_packet_framed_sha256', 'local_alternative_context_counts')}))


if __name__ == '__main__':
    main()
