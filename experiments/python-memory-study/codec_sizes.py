#!/usr/bin/env python3
"""Feed real offline JPEG sizes into the independent memory-only what-if model."""
import argparse
import hashlib
import json
from pathlib import Path

from model import Config, simulate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--codec-results', type=Path,
                        default=Path(__file__).resolve().parent.parent/'python-codec-study/results.json')
    parser.add_argument('--output', type=Path,
                        default=Path(__file__).with_name('codec-size-results.json'))
    args = parser.parse_args()
    codec_results = json.loads(args.codec_results.read_text())
    rows = []
    for source in codec_results['rows']:
        if source['corpus'] == 'synthetic-hud' or source['profile'] not in ('jpeg-q80', 'jpeg-budget8'):
            continue
        sizes = tuple(frame['bytes'] for frame in source['per_frame'])
        for storage in ('bram', 'sdram', 'sram'):
            cfg = Config(storage=storage, frames=len(sizes), frame_sizes=sizes,
                         fps=30, scan_hz=60, reference=False)
            row = simulate(cfg)
            row['codec_corpus'] = source['corpus']
            row['codec_profile'] = source['profile']
            rows.append(row)
            print(source['corpus'], source['profile'], storage,
                  row['reconstructed_by_window'], row['cap_drops'],
                  row['frame_memory_age_ms']['maximum'], flush=True)
    result = {'evidence': 'memory-only service of actual offline JPEG sizes; no network/decoder/board',
              'codec_results_sha256': hashlib.sha256(args.codec_results.read_bytes()).hexdigest(),
              'model_sha256': hashlib.sha256(Path(__file__).with_name('model.py').read_bytes()).hexdigest(),
              'driver_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'scenario_count': len(rows), 'scenarios': rows}
    args.output.write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    main()
