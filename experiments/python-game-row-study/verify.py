#!/usr/bin/env python3
"""Verify stored row-codec comparisons without rerunning timed encoding."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent


def main():
    d=json.loads((HERE/'results.json').read_text())
    for path,expected in d['source_sha256'].items():
        p=Path(path)
        if '/moonbub-30fps-study/' in path:p=ROOT/path.split('/moonbub-30fps-study/',1)[1]
        assert hashlib.sha256(p.read_bytes()).hexdigest()==expected,path
    real=0;frames=0;row_win=0;patches=0
    for case in d['cases']:
        assert len(case['profiles'])==4
        for r in case['profiles']:
            frames+=1
            assert r['rgb565_word_mismatches']==0
            assert r['over_cap']==(r['packet_bytes']>d['cap'])
            assert r['packet_bytes']==r['base_bytes']+22+sum(4+p['chosen_bytes'] for p in r['patches'])
            assert r['selected_region_pixels']==sum(w*h for x,y,w,h in r['rectangles'])
            assert abs(r['charged_prepare_sum_ms']-(r['base_prepare_ms_reused']+r['patch_search_and_wrapper_ms']))<1e-8
            assert r['forward_ipv4_udp_bytes_accounting_only']==r['packet_bytes']+59*((r['packet_bytes']+1023)//1024)
            for p in r['patches']:
                patches+=1
                if r['method']=='adaptive_row':
                    assert p['chosen_bytes']==min(p['hp01_bytes'],p['hr01_bytes'])
                    assert p['hr01_bytes']==min(a['bytes'] for a in p['attempts'])
                    assert 2<=p['candidate_count']<=3
            assert not r['installed_gf02_adapter_accepts_hg01']
        if case['source_kind']=='real_precompressed':
            real+=1
            for region in ('broad','compact'):
                control=next(r for r in case['profiles'] if r['region_set']==region and r['method']=='hp01')
                row=next(r for r in case['profiles'] if r['region_set']==region and r['method']=='adaptive_row')
                assert row['packet_bytes']<=control['packet_bytes']
                row_win+=row['packet_bytes']<control['packet_bytes']
    assert len(d['cases'])==20 and real==16 and frames==80 and patches==240 and row_win==32
    broad=d['summary']['real_precompressed/broad'];compact=d['summary']['real_precompressed/compact']
    assert broad['hp01']['fit_frames']==0 and broad['adaptive_row']['fit_frames']==8
    assert compact['hp01']['fit_frames']==compact['adaptive_row']['fit_frames']==16
    print(json.dumps({'source_bindings':len(d['source_sha256']),'inputs':20,'real_inputs':real,'actual_wrapped_decodes':frames,
        'actual_chosen_patch_packets':patches,'real_paired_packet_size_wins':row_win,'rgb565_selected_regions_all_exact':True,
        'real_broad_fit_hp01_then_row':[0,8],'real_compact_fit_both':16,
        'scope':'Stored software comparisons; no target transport or real-time proof'},indent=2))


if __name__=='__main__':main()
