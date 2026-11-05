#!/usr/bin/env python3
"""Offline replay of archived V40 canvases without requiring original media."""
from __future__ import annotations
import importlib.util,json,sys
from fractions import Fraction
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent.parent
SOURCE=ROOT/'experiments/python-game-source-v40-study'

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:raise RuntimeError(f'cannot import frozen verifier {path}')
    value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value);return value

# Reuse frozen source-verifier primitives/constants as functions. Its main is
# deliberately not called: that path reopens the original external media files.
frozen=module('v40_archived_canvas_frozen_source_verify',SOURCE/'verify.py')

def main():
    manifest=json.loads((SOURCE/'manifest.json').read_text())
    if manifest.get('schema')!='gamebub-source-qualification-v40':raise ValueError('unexpected source manifest schema')
    if manifest['source_code_sha256']!=frozen.source_pins():raise ValueError('source pin mismatch')
    if manifest['external_media_sha256']!=frozen.EXPECTED_MEDIA_SHA256:raise ValueError('external media hash table mismatch')
    calibration=frozen.calibration_prefixes();objects=set();total_rows=0;reports=[]
    for case in manifest['cases']:
        name=case['name']
        if name not in frozen.WINDOWS or case['media_file']!=f'media/{name}.mp4':raise ValueError('unexpected qualification media')
        t0,t1=frozen.WINDOWS[name]
        if case['requested_interval_seconds_half_open']!={'start':str(t0),'end':str(t1)}:raise ValueError(f'window mismatch for {name}')
        # Validate the preparation's before/after evidence against the frozen
        # expected digest table. The source media is intentionally unavailable;
        # this verifier does not reopen or freshly hash that external file.
        expected=frozen.EXPECTED_MEDIA_SHA256[name]
        if case['media_sha256_before']!=expected or case['media_sha256_after']!=expected or not case['sha_before_after_match']:
            raise ValueError(f'external media hash evidence mismatch for {name}')
        if case['decoded_frame_count_actual']!=case['decoded_frame_count_reported']-case['reported_minus_decoded_frame_count']:
            raise ValueError(f'decoded frame-count arithmetic mismatch for {name}')
        if not 0<case['selected_frame_count']<=144:raise ValueError(f'invalid selected-frame count for {name}')
        rows=case['frames']
        if len(rows)!=case['selected_frame_count']:raise ValueError(f'selected row count mismatch for {name}')
        previous=None;unique_canvas=set();unique_native=set();overlaps={k:[] for k in calibration}
        prefix_hashes={k:{r['canvas_rgb_sha256'] for r in v['first_12']} for k,v in calibration.items()}
        for index,row in enumerate(rows):
            if row['id']!=index:raise ValueError(f'unordered selected IDs for {name}')
            timestamp=Fraction(*row['time_base'])*row['pts']
            if str(timestamp)!=row['timestamp_fraction'] or float(timestamp)!=row['timestamp_seconds']:
                raise ValueError(f'timestamp mismatch for {name}/{index}')
            if not t0<=timestamp<t1:raise ValueError(f'frame outside PTS interval for {name}/{index}')
            if not 0<=row['decoded_order']<case['decoded_frame_count_actual']:
                raise ValueError(f'invalid decoded-order index for {name}/{index}')
            if previous is not None and timestamp<=previous:raise ValueError(f'timestamps not increasing for {name}')
            gap=None if previous is None else str(timestamp-previous)
            if row['gap_from_previous_selected_seconds']!=gap:raise ValueError(f'PTS gap mismatch for {name}/{index}')
            previous=timestamp
            raw=frozen.read_canvas(row['canvas_rgb24'])
            canvas=np.frombuffer(raw,np.uint8).reshape(480,720,3)
            canvas_hash=frozen.digest(raw)
            if canvas_hash!=row['canvas_rgb_sha256']:raise ValueError(f'canvas hash mismatch for {name}/{index}')
            words=frozen.corpus.rgb565(canvas).astype('<u2',copy=False)
            if frozen.digest(np.ascontiguousarray(words).tobytes())!=row['rgb565_sha256']:
                raise ValueError(f'RGB565 hash mismatch for {name}/{index}')
            planes=frozen.ft.rgb_to_planes(canvas)
            yuv=b''.join(np.ascontiguousarray(p.astype(np.uint8)).tobytes() for p in planes)
            if frozen.digest(yuv)!=row['common_yuv420_u8_sha256']:raise ValueError(f'YUV hash mismatch for {name}/{index}')
            if tuple(row['active_rect_xywh'])!=tuple(case['active_rect_xywh']):raise ValueError(f'active rect mismatch for {name}/{index}')
            objects.add(row['canvas_rgb24']['stored_sha256']);unique_canvas.add(canvas_hash);unique_native.add(row['native_rgb_sha256'])
            for cal_name,hashes in prefix_hashes.items():
                if canvas_hash in hashes:overlaps[cal_name].append({'qualification_id':index,'canvas_rgb_sha256':canvas_hash})
        if len(unique_canvas)!=case['selected_unique_canvas_frames']:raise ValueError(f'unique canvas count mismatch for {name}')
        if len(unique_native)!=case['selected_unique_native_rgb_frames']:raise ValueError(f'unique native count mismatch for {name}')
        for cal_name,matches in overlaps.items():
            recorded=case['calibration_hash_overlap'][cal_name]
            if recorded['frame_hash_overlap_count']!=len(matches) or recorded['matches']!=matches:
                raise ValueError(f'calibration overlap mismatch for {name}/{cal_name}')
        if [r['decoded_order'] for r in rows]!=sorted(r['decoded_order'] for r in rows):
            raise ValueError(f'decoded order mismatch for {name}')
        total_rows+=len(rows)
        reports.append({'clip':name,'selected_frames':len(rows),'unique_canvas_frames':len(unique_canvas),
            'first_timestamp':rows[0]['timestamp_fraction'],'last_timestamp':rows[-1]['timestamp_fraction'],
            'ab38_calibration_overlaps':{k:len(v) for k,v in overlaps.items()}})
    if len(manifest['cases'])!=len(frozen.WINDOWS) or {c['name'] for c in manifest['cases']}!=set(frozen.WINDOWS):
        raise ValueError('qualification cohort mismatch')
    if manifest['counts']['clips']!=len(frozen.WINDOWS) or manifest['counts']['selected_frames']!=total_rows:
        raise ValueError('manifest aggregate count mismatch')
    if manifest['counts']['content_addressed_objects']!=len(objects):raise ValueError('manifest object count mismatch')
    raw_total=sum(r['canvas_rgb24']['raw_bytes'] for c in manifest['cases'] for r in c['frames'])
    if manifest['counts']['stored_rgb24_raw_bytes']!=raw_total:raise ValueError('manifest storage count mismatch')
    print(json.dumps({'verified_clips':len(reports),'verified_frames':total_rows,'verified_objects':len(objects),
        'reports':reports,'archived_canvas_replay':True,'original_media_redecode':False,
        'current_external_hash_check':False,'declared_media_hash_evidence_checked':True},indent=2),flush=True)
if __name__=='__main__':main()
