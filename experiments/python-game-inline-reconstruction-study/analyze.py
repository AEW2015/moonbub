#!/usr/bin/env python3
"""Untimed generated-tile/tag proof and matched conditional-service comparison."""
import argparse,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build():
    d=json.loads((HERE/'results.json').read_text());frames=d['frames'];native=[f for f in frames if f['cohort'].startswith('native')]
    assert len(frames)==16 and len(native)==12
    assert all(f['private_tag_hex']==f['canonical_fixture_tag_hex'] for f in frames)
    assert all((f['publication_tag_hex'] is not None)==f['published'] for f in frames)
    assert all(f['output_written_after_tag_push'] and f['selected_ui_word_errors']==0 for f in frames)
    summaries=[]
    for c in d['cases']:
        rows=[r['schedule'] for r in c['rows'] if r['cohort'].startswith('native')]
        for r in rows:
            assert r['config']['tag_hash_MBps']==r['inline_config']['hash_MBps']
            assert r['tag_bank_reread_bytes']==0
        old=sum(r['baseline_serial_frame_ms'] for r in rows)/len(rows);new=sum(r['frame_done_ms'] for r in rows)/len(rows)
        summaries.append(dict(profile=c['profile'],baseline_serial_mean_ms=old,inline_mean_ms=new,matched_service_saving_percent=100*(1-new/old),
            native_budget_misses=sum(r['missed_frame_budget'] for r in rows),
            eliminated_physical_tag_bank_bytes=sum(r['eliminated_physical_tag_bank_bytes'] for r in rows),
            eliminated_v19_tag_read_planning_bytes=sum(r['eliminated_v19_tag_read_planning_bytes'] for r in rows),
            canonical_bytes_hashed=sum(r['canonical_bytes_hashed'] for r in rows),sha256_padding_service_bytes=sum(r['sha256_padding_service_bytes'] for r in rows),
            sha256_compression_service_bytes=sum(r['sha256_compression_service_bytes'] for r in rows),max_hash_backpressure_ms=max(r['hash_backpressure_ms'] for r in rows),
            max_local_planning_bytes=max(r['local_planning_bytes'] for r in rows),max_additional_tagger_arrays_bytes=max(r['additional_tagger_ndarray_bytes'] for r in rows)))
    objects={f['tile_stream']['path']:f['tile_stream'] for f in frames}
    return dict(results_sha256=sha(HERE/'results.json'),analyzer_sha256=sha(HERE/'analyze.py'),counts=d['counts'],
        actual_generated_frames=16,published_decisions=sum(f['published'] for f in frames),native_published_decisions=sum(f['published'] for f in native),
        ordinary_decisions_without_publication=sum(not f['published'] for f in frames),
        generated_golden_unique_objects=len(objects),generated_golden_stored_bytes=sum((HERE/p).stat().st_size for p in objects),
        generated_golden_raw_bytes=sum(x['raw_bytes'] for x in objects.values()),
        native_tagger_local_array_bytes_max=max(f['tagger_local_ndarray_bytes'] for f in native),profiles=summaries,
        every_native_profile_misses_33ms=all(x['native_budget_misses']==12 for x in summaries),
        limitations=['Actual producer tags newly generated clipped tiles before external output write; it does not hash posthoc reconstructed planes.',
            'All16private tags are exact; only KEY/PROMOTE eligible decisions expose publication_tag after explicit validated completion.',
            'Functional ordinary-P hashes are diagnostic probes, while timing charges hash work only for eligible publications, matching v19 baseline.',
            'Per-profile hash/expansion service assumptions match baseline and inline designs; new copy work and stripe holding/backpressure are paid.',
            'The7.05percent default gain is a conditional schedule result; exact byte/tag proof does not establish target clock, FPGA fit or30fps.',
            'Tagger ndarray bound excludes parser/input/coefficient inverse temporaries/external banks/oracle/export arrays and Python hash/control heap.',
            'Native12decisions reuse6 acquisitions; flatcontrols are not gameplayFPS. No joint gateway/ESP ISA/RF or physical scanline proof.'])
def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();d=build();path=HERE/'analysis.json'
    if args.check:assert json.loads(path.read_text())==d
    else:path.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')
    print('PASS:actual-generated-tile canonical tags/publication gates, IT20 object inventory, matched inline service and paid backpressure; nohardwarefpsclaim')
if __name__=='__main__':main()
