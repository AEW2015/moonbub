#!/usr/bin/env python3
"""Untimed mandatory coverage, paid retry and matched-quality reconciliation."""
from pathlib import Path
import argparse,hashlib,json
HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build():
    d=json.loads((HERE/'results.json').read_text());summaries=[];coverage=[]
    for case in d['cases']:
        rows=case['rows'];accepted=[r for r in rows if r['accepted']]
        for r in accepted:
            assert r['selected_word_errors']==0 and r['packet_bytes']<=49152
            coverage.append(dict(scene=case['scene'],policy=case['policy'],id=r['id'],selected=r['selected_rectangles'],omitted=r['omitted_rectangles'],selected_words=r['selected_words']))
        if case['policy']=='mandatory':assert len(accepted)==48 and all(not r['omitted_rectangles'] and r['selected_words']==21120 for r in accepted)
        summaries.append(dict(scene=case['scene'],policy=case['policy'],accepted=len(accepted),full_ui=sum(not r['omitted_rectangles'] for r in accepted),
            partial_ui=sum(bool(r['omitted_rectangles']) for r in accepted),selected_words=sum(r['selected_words'] for r in accepted),
            packet_bytes=sum(r['packet_bytes'] for r in accepted),max_packet_bytes=max(r['packet_bytes'] for r in accepted),
            background_profile_counts={k:sum(str(r['selected_profile'])==k for r in accepted) for k in sorted({str(r['selected_profile']) for r in accepted})},
            losing_builds=sum(sum(not a['accepted'] for a in r['attempts']) for r in rows),
            paid_rejected_build_ms=sum(a['build_ms'] for r in rows for a in r['attempts'] if not a['accepted']),
            paid_discard_ms=sum(a['discard_ms'] for r in rows for a in r['attempts']),
            paid_patch_prepare_ms=sum(r['patch_prepare_ms'] for r in rows),
            maximum_attempts=max(len(r['attempts']) for r in rows)))
    pairs=[]
    for scene in ('mass-effect-2600','mass-effect-7200'):
        cases={c['policy']:c for c in d['cases'] if c['scene']==scene};a,b=cases['baseline'],cases['mandatory'];assert a['manifest']['frame_sha256']==b['manifest']['frame_sha256']
        aa={r['id']:r for r in a['rows'] if r['accepted']};bb={r['id']:r for r in b['rows'] if r['accepted']};ids=sorted(aa.keys()&bb.keys())
        same=[i for i in ids if aa[i]['packet_sha256']==bb[i]['packet_sha256']]
        if scene=='mass-effect-2600':assert len(same)==48
        base_bytes=sum(aa[i]['packet_bytes'] for i in ids);mandatory_bytes=sum(bb[i]['packet_bytes'] for i in ids)
        pairs.append(dict(scene=scene,matched_ids=ids,byte_identical_ids=same,baseline_packet_bytes=base_bytes,mandatory_packet_bytes=mandatory_bytes,
            packet_byte_change_percent=100*(mandatory_bytes/base_bytes-1),baseline_active_rgb565_mse=sum(aa[i]['active_rgb565_mse'] for i in ids)/len(ids),
            mandatory_active_rgb565_mse=sum(bb[i]['active_rgb565_mse'] for i in ids)/len(ids),
            same_reference_comparison=next(x for x in d['comparisons'] if x['scene']==scene),
            meaning='Actual same-source-ID policy comparison; adapted key/promotion quantization changes later reference history. Byte/MSE deltas are not isolated coding efficiency or lossless background claims.'))
    refs=[]
    def walk(v):
        if isinstance(v,dict):
            if {'path','raw_sha256','stored_sha256'}<=v.keys():refs.append(v)
            else:
                for x in v.values():walk(x)
        elif isinstance(v,list):
            for x in v:walk(x)
    walk(d['cases']);paths={r['path'] for r in refs};assert len(paths)==len(list((HERE/'objects').iterdir()))
    return dict(results_sha256=sha(HERE/'results.json'),analyzer_sha256=sha(HERE/'analyze.py'),counts=d['counts'],summary=summaries,
        matched_source_comparisons=pairs,per_decoded_coverage=coverage,golden_object_count=len(paths),golden_stored_bytes=sum((HERE/p).stat().st_size for p in paths),
        scope='Actual component bytes/pixels/reference ACKs; no pacedwire/deadline/ESP ISA/RF/FPGA fit or30fps proof. All mandatory native outputs have full requested HUD coverage; background quantization is lossy and explicitly measured. Same existing29.88fps source windows, not fresh heldout validation.')
def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();out=build();path=HERE/'analysis.json'
    if args.check:assert json.loads(path.read_text())==out
    else:path.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    print('PASS:all96mandatorynativeframesfullHUD/cap/exactwords;paidretrycosts and matchedsource quality;20goldens;noFPSclaim')
if __name__=='__main__':main()
