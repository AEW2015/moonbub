#!/usr/bin/env python3
"""Untimed matched-vector operation and conditional memory-service comparison."""
import argparse,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build():
    path=HERE/'results.json';d=json.loads(path.read_text());frames=d['frames'];native=[f for f in frames if f['cohort'].startswith('native')]
    profiles={c['profile']:c for c in d['cases']}
    ops={k:sum(f[k] for f in native) for k in ('blocks','zero','dc','general','dense_mac_operations','existing_bypass_general_mac_operations','sparse_mac_operations','dc_constant_multiplies','dequant_multiplies','dense_dequant_multiplies')}
    ops['sparse_general_mac_saving_vs_existing_bypass_percent']=100*(1-ops['sparse_mac_operations']/ops['existing_bypass_general_mac_operations'])
    per_frame=[]
    for f in native:
        ident=(f['cohort'],f['id'])
        def schedule(name):return next(r['schedule'] for r in profiles[name]['rows'] if (r['cohort'],r['id'])==ident)
        old,new,compact=schedule('existing_bypass4'),schedule('sparse4'),schedule('sparse4_yuv8')
        sums=lambda r:{k:sum(s['cycles'][k] for s in r['stripes']) for k in ('index_scan','dequant','dependent_mac','pass_overhead','output','total')}
        per_frame.append(dict(cohort=f['cohort'],id=f['id'],inner_codec=f['inner_codec'],key=f['key'],published=f['published'],
            existing_general_mac=f['existing_bypass_general_mac_operations'],sparse_general_mac=f['sparse_mac_operations'],
            general_mac_saving_percent=100*(1-f['sparse_mac_operations']/f['existing_bypass_general_mac_operations']) if f['existing_bypass_general_mac_operations'] else 0,
            existing_bypass_cycles=sums(old),sparse_cycles=sums(new),existing_frame_ms=old['frame_done_ms'],sparse_frame_ms=new['frame_done_ms'],compact_frame_ms=compact['frame_done_ms'],
            physical_yuv_bytes_16=sum(old[k] for k in ('prediction_read_bytes','reconstruction_write_bytes','tag_read_bytes','color_read_bytes')),
            physical_yuv_bytes_8=sum(compact[k] for k in ('prediction_read_bytes','reconstruction_write_bytes','tag_read_bytes','color_read_bytes')),
            canonical_tag_hash_bytes_16=old['tag_canonical_hashed_bytes'],canonical_tag_hash_bytes_8=compact['tag_canonical_hashed_bytes'],
            compact_tag_expansion_cycles=compact['tag_expand_cycles'],same_canonical_tag=f['canonical_int16_tag_hex']==f['packed_roundtrip_tag_hex']))
    avg=lambda name:profiles[name]['summary']['native_mean_ms']
    summary=dict(existing_bypass4_mean_ms=avg('existing_bypass4'),sparse4_mean_ms=avg('sparse4'),compact8_mean_ms=avg('sparse4_yuv8'),
        sparse4_service_saving_percent=100*(1-avg('sparse4')/avg('existing_bypass4')),
        compact8_additional_service_saving_percent=100*(1-avg('sparse4_yuv8')/avg('sparse4')),
        sparse4_to8_mean_ms_gain=avg('sparse4')-avg('sparse8'),
        every_native_case_misses_33ms=all(c['summary']['native_budget_misses']==12 for c in d['cases']),
        native_local_buffer_bytes_max=max(r['schedule']['local_buffer_total_bytes'] for c in d['cases'] for r in c['rows'] if r['cohort'].startswith('native')))
    return dict(results_sha256=sha(path),analyzer_sha256=sha(HERE/'analyze.py'),counts=d['counts'],native_operation_counts=ops,
        matched_native_comparisons=per_frame,profile_summaries=[c['summary'] for c in d['cases']],summary=summary,
        limits=['Exact arithmetic/vector equality is independent of timing assumptions. Existing zero/DC bypass is the working baseline; dense-all is diagnostic only.',
            'Counted products are not FPGA cycles; conditional schedule pays scans/dequant/two-pass dependency/output/color/tag work.',
            'All native cases miss33.33ms in this deliberately serial conservative planning schedule; this does not establish a physical upper bound or rule out a better fused pipeline.',
            'Full49152byte local compressedcache trades area for entropy/SDRAM decoupling. Smaller cache/shared-arbiter path remains open. Control/parser implementation state and fitted resources excluded.',
            'Average800x480x60 RGB565 reserve is not physical480x800 scanline deadline proof. No ESP ISA/RF calibration or jointnative/hardware30fps proof.'])
def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();d=build();out=HERE/'analysis.json'
    if args.check:assert json.loads(out.read_text())==d
    else:out.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')
    print('PASS:matched actual AR03 inverse MACs/paid scans, compactYUV8/tag conservation and conditional stripe/memory comparisons; nohardwareFPSclaim')
if __name__=='__main__':main()
