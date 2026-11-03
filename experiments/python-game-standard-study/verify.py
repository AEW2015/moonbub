#!/usr/bin/env python3
"""Recompute stored source equality, packet accounting and pooled RD metrics."""
import hashlib
import json
import math
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parent.parent


def load(name):return json.loads((HERE/name).read_text())


def pins(data):
    for path,expected in data['source_sha256'].items():
        p=Path(path)
        if '/moonbub-30fps-study/' in path:p=ROOT/path.split('/moonbub-30fps-study/',1)[1]
        assert hashlib.sha256(p.read_bytes()).hexdigest()==expected,path
    return len(data['source_sha256'])


def quality(case):
    for region in ('active','roi','background'):
        rows=[r['quality'][region] for r in case['records']]
        mse=sum(r['squared_error_sum'] for r in rows)/sum(r['pixels'] for r in rows)
        actual=case['summary']['pooled'][region]
        assert math.isclose(mse,actual['mse'],rel_tol=1e-12)
        assert math.isclose(10*math.log10(65025/mse),actual['psnr'],rel_tol=1e-12)


def main():
    d=load('results.json');f=load('color-floor.json');bindings=pins(d)+pins(f)
    assert len(d['cases'])==18 and len(f['cases'])==4
    inputs={};frames=0;native=0;table=[]
    for case in d['cases']:
        source=case['source'];manifest=case['manifest'];hashes=manifest['frame_sha256']
        if source in inputs:assert inputs[source]==hashes
        else:inputs[source]=hashes
        assert [r['id'] for r in case['records']]==list(range(60))
        assert [r['id'] for r in case['records'] if r['is_key']]==[0,30]
        frames+=60;quality(case)
        total=sum(r['bytes'] for r in case['records']);s=case['summary']
        assert total==s['coded_bytes'] and s['mean_bytes']==total/60
        assert s['coded_mbps_at_hypothetical30']==total/60*8*30/1e6
        if 'reference' in case:
            native+=60;r=case['reference']
            assert sorted(r['output_pts'])==list(range(60))
            assert not r['unconsumed_options']
            assert total==r['coded_bytes']==sum(p['bytes'] for p in r['packets'])+r['extradata_bytes']
            assert all(p['pts']==p['dts'] for p in r['packets'])
            assert r['packets_returned_only_at_flush']==0
        table.append({'source':source,'profile':case['profile'],'coded_mbps':s['coded_mbps_at_hypothetical30'],
                      'active_psnr':s['pooled']['active']['psnr'],'roi_psnr':s['pooled']['roi']['psnr']})
    for case in f['cases']:
        assert case['manifest']['frame_sha256']==inputs[case['source']]
        assert case['distinct_input_rgb_hashes']==len(set(inputs[case['source']]))
        quality(case)
    common=load('common-color-results.json');bindings+=pins(common)
    assert common['prior_results_sha256']==hashlib.sha256((HERE/'results.json').read_bytes()).hexdigest()
    assert len(common['cases'])==18
    common_native=0
    for case in common['cases']:
        assert case['manifest']['frame_sha256']==inputs[case['source']]
        assert [r['id'] for r in case['records']]==list(range(60))
        assert [r['id'] for r in case['records'] if r['is_key']]==[0,30]
        quality(case)
        if 'reference' in case and 'packets_only_at_flush' in case['reference']:
            common_native+=60;r=case['reference']
            assert r['packets_only_at_flush']==0
            assert all(p['pts']==p['dts'] for p in r['packets'])
            assert sum(p['bytes'] for p in r['packets'])+r['extradata_bytes']==case['summary']['coded_bytes']
            assert sum(r['bytes'] for r in case['records'])==case['summary']['coded_bytes']
        else:
            original=next(c for c in d['cases'] if c['source']==case['source'] and c['profile']==case['profile'])
            assert case['records']==original['records'] and case['summary']==original['summary']
    assert common_native==720
    assert frames==1080 and native==720
    print(json.dumps({'source_bindings':bindings,'profile_cases':18,'actual_decoded_outputs':frames,
        'native_hevc_av1_outputs_initial':native,'additional_common_color_native_outputs':common_native,
        'total_actual_codec_outputs_across_campaigns':frames+common_native,'same_source_ids_per_clip':60,
        'distinct_rgb_hashes':{k:len(set(v)) for k,v in inputs.items()},
        'key_ids_all_profiles':[0,30],'color_conversion_probes':4,'rd_points':table,
        'scope':'Storedsame-sourceCPUreferencechecks; not matchedquality/perceptual/targetdecodeor30fpsqualification'},indent=2))


if __name__=='__main__':main()
