#!/usr/bin/env python3
"""Validate stored GM01 run bindings, source IDs, counters and pooled metrics."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def resolve(raw):
    marker='/moonbub-30fps-study/'
    return ROOT/raw.split(marker,1)[1] if marker in raw else Path(raw)


def main():
    doc=json.loads((HERE/'results.json').read_text());count=0
    for raw,expected in doc['source_sha256'].items():assert digest(resolve(raw))==expected,raw
    delta=doc['format']['uniform_gm01_minus_ma01_bytes_720x480']
    for scene in doc['scenes']:
        manifest=scene['manifest']
        assert len(scene['records'])==36
        if Path(manifest['source']).exists():assert digest(Path(manifest['source']))==manifest['source_sha256']
        for row in scene['records']:
            assert row['input_sha256']==manifest['frame_sha256'][row['id']]
            assert row['forward_calls_total']==3*(row['id']+1) and row['analysis_count']==row['id']+1
            assert row['map_bytes']==338 and row['outer_header_crc_bytes']==50
            assert row['key']==(row['id'] in (0,6)) and row['anchor_id']==(0 if row['id']<6 else 6)
            if row['uniform_ma01_bytes'] is not None:assert row['bytes']-row['uniform_ma01_bytes']==delta
            regions=row['metrics'];a,b=regions['roi'],regions['background'];whole=regions['active']
            assert a['pixels']+b['pixels']==whole['pixels']
            assert abs((a['mse']*a['pixels']+b['mse']*b['pixels'])/whole['pixels']-whole['mse'])<1e-8
            count+=1
        for label,summary in scene['summary'].items():
            rows=[r for r in scene['records'] if r['profile']==label]
            assert len(rows)==12
            assert abs(summary['packet_mean_bytes']-sum(r['bytes'] for r in rows)/12)<1e-9
            assert summary['over_48k_cap']==sum(r['bytes']>49152 for r in rows)
    assert count==doc['combined_packet_count']==72 and doc['uniform_ma01_pixel_pairs']==24
    print(json.dumps({'source_bindings':len(doc['source_sha256']),'actual_combined_packets':count,
                      'uniform_ma01_pixel_pairs':24,'frame_forward_calls':3,
                      'outer_header_crc_bytes':50,'map_bytes':338,'uniform_packet_overhead_vs_ma01_bytes':delta,
                      'scope':'Stored evidence verification, not a new codec run or target hardware proof'},indent=2))


if __name__=='__main__':main()
