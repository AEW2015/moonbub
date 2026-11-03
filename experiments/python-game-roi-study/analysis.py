#!/usr/bin/env python3
"""Independently aggregate recorded RG01 comparisons; no new codec execution."""
import hashlib
import json
import math
from pathlib import Path

HERE=Path(__file__).resolve().parent


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def psnr(mse):return None if mse==0 else 10*math.log10(65025/mse)


def pool(scenes,profile,region):
    rows=[s['profiles'][profile]['metrics'][region] for s in scenes]
    pixels=sum(r['pixels'] for r in rows)
    mse=sum(r['mse']*r['pixels'] for r in rows)/pixels
    return dict(mse=mse,psnr=psnr(mse),pixels=pixels)


def main():
    path=HERE/'results.json';doc=json.loads(path.read_text())
    for source,expected in doc['source_sha256'].items():assert digest(Path(source))==expected,source
    groups={name:[s for s in doc['scenes'] if s['name'].startswith(prefix)]
            for name,prefix in (('combat','mass-effect-combat'),('second_clip','mass-effect-2600'),('synthetic','seeded-HUD'))}
    out={}
    for name,scenes in groups.items():
        pooled={profile:{region:pool(scenes,profile,region) for region in ('active','roi','background')}
                for profile in scenes[0]['profiles']}
        byte_totals={profile:sum(s['profiles'][profile]['bytes'] for s in scenes) for profile in scenes[0]['profiles']}
        comparison={region:pooled['budget_roi8mix'][region]['psnr']-pooled['uniform16'][region]['psnr']
                    for region in ('active','roi','background')}
        edge={}
        for profile in ('uniform16','budget_roi8mix'):
            total=sum(s['profiles'][profile]['metrics']['roi_edge_samples'] for s in scenes)
            edge[profile]=sum(s['profiles'][profile]['metrics']['roi_edge_gradient_mae']*s['profiles'][profile]['metrics']['roi_edge_samples']
                              for s in scenes)/total
        costs=[s['budget_policy']['total_reference_and_search_encode_ms'] for s in scenes]
        out[name]=dict(frames=len(scenes),pooled_metrics=pooled,byte_totals=byte_totals,
                       budget_vs_uniform16_pooled_psnr_delta=comparison,
                       budget_utilization_min=min(s['budget_policy']['budget_utilization'] for s in scenes),
                       budget_utilization_max=max(s['budget_policy']['budget_utilization'] for s in scenes),
                       budget_roi_edge_gradient_mae=edge,
                       reference_plus_search_encode_ms=dict(mean=sum(costs)/len(costs),min=min(costs),max=max(costs)),
                       search_attempts=[s['budget_policy']['attempts'] for s in scenes],
                       synthetic_threshold_errors=[dict(name=s['name'],uniform16=s['profiles']['uniform16']['metrics'].get('synthetic_roi_threshold_error_rate'),
                                                        budget=s['profiles']['budget_roi8mix']['metrics'].get('synthetic_roi_threshold_error_rate')) for s in scenes if s['synthetic']])
    cap={profile:dict(over_49152=sum(s['profiles'][profile]['bytes']>49152 for s in doc['scenes']),
                      max_bytes=max(s['profiles'][profile]['bytes'] for s in doc['scenes']),
                      min_bytes=min(s['profiles'][profile]['bytes'] for s in doc['scenes']),
                      mean_bytes=sum(s['profiles'][profile]['bytes'] for s in doc['scenes'])/len(doc['scenes']))
         for profile in doc['scenes'][0]['profiles']}
    # Uniform16 comparison is a same-frame byte reference, not an external link/storage cap.
    assert all(s['profiles']['budget_roi8mix']['bytes']<=s['profiles']['uniform16']['bytes'] for s in doc['scenes'])
    assert all(s['budget_policy']['attempts']<=10 for s in doc['scenes'])
    for s in doc['scenes']:
        assert s['input_sha256']==s['manifest']['frame_sha256'][s['source_index']]
        p=s['budget_policy'];assert abs(p['total_reference_and_search_encode_ms']-p['reference_uniform16_encode_ms']-sum(c['encode_wall_ms'] for c in p['candidates']))<1e-9
    result=dict(evidence='Derived stored-packet metric aggregation, not another encode or hardware test',
                source_sha256={str(HERE/'analysis.py'):digest(HERE/'analysis.py')},result_sha256=digest(path),
                groups=out,profile_49152_byte_cap_analysis=cap,
                actual_encode_decode_calls=sum(6+s['budget_policy']['attempts']-2 for s in doc['scenes']),
                selected_profile_records=sum(len(s['profiles']) for s in doc['scenes']),
                syntax_cost=dict(map_bytes_720x480=338,outer_header_crc_bytes=34,uniform_rg01_minus_ft02_bytes_720x480=318),
                gate='All18 candidate searches fit their uniform16-size reference; two synthetic selections exceed49152bytes. No target-size or real-time pass is inferred.')
    (HERE/'summary.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    for name,r in out.items():print(name,r['budget_vs_uniform16_pooled_psnr_delta'],r['reference_plus_search_encode_ms'])
    print('selectedover48KiB',cap['budget_roi8mix'])


if __name__=='__main__':main()
