#!/usr/bin/env python3
"""Recompute the finite full-UI cadence result; no new benchmark timing."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def build():
    path = HERE / 'results.json'
    d = json.loads(path.read_text())
    cases = {c['profile']: c for c in d['cases'] if c['source'] == 'mass-effect-2600-heldout180'}
    c = cases['gm_ui']; r = c['result']
    ids = [p['id'] for p in r['presented'] if 500 <= p['at_ms'] < 5500]
    commits = {p['id']: p for p in r['commits']}
    assert ids == list(range(12, 162))
    assert len({commits[i]['rgb_sha256'] for i in ids}) == 150
    assert len({c['manifest']['frame_sha256'][i] for i in ids}) == 150
    assert [p['id'] for p in r['drops']] == [1, 2]
    assert (r['presented_strict'], r['presented_eventual']) == (175, 178)
    assert all(p['selected_exact_pixels'] == 21120 and p['selected_ui_mismatches'] == 0 for p in commits.values())
    rows = []
    for name, case in cases.items():
        result = case['result']
        rows.append(dict(profile=name, strict=result['presented_strict'], eventual=result['presented_eventual'],
                         diagnostic_ids_per_second=result['diagnostic_ids_per_second']))
    return dict(results_sha256=sha(path), analysis_sha256=sha(HERE/'analyze.py'),
                steady_window_ms=[500,5500], steady_source_ids=ids, distinct_input_hashes=150,
                distinct_decoded_hashes=150, modeled_ids_per_second=30,
                gm_ui_strict=175, gm_ui_eventual=178, gm_ui_startup_drops=[1,2],
                exact_original_rgb565_pixels_per_decoded_frame=21120, selected_word_errors=0,
                long_profiles=rows,
                scope='Offline precompressed inputs; measured Python costs on independent serialized virtual servers. Assumed links/vblank. Initial key only. No live/native/shared-CPU or hardware 30 fps proof.')

def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--check', action='store_true'); args = parser.parse_args()
    out = build(); path = HERE/'ui-cadence.json'
    if args.check:
        assert json.loads(path.read_text()) == out
    else:
        path.write_text(json.dumps(out,indent=2)+'\n')
    print('PASS: GM+all-four-UI;150 distinct input/decoded IDs over5 modeled seconds;178of180 eventual;2 startup drops;exact selected RGB565')

if __name__ == '__main__':
    main()
