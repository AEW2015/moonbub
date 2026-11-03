#!/usr/bin/env python3
"""Independent stored accounting/identity/quality checks, no timed codec rerun."""
import hashlib
import json
import math
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent


def resolve(path):
    marker='/moonbub-30fps-study/'
    return ROOT/path.split(marker,1)[1] if marker in path else Path(path)


def main():
    d=json.loads((HERE/'results.json').read_text())
    for path,h in d['source_sha256'].items():assert hashlib.sha256(resolve(path).read_bytes()).hexdigest()==h,path
    total=0;comparisons=[];missing_media=[]
    for scene in d['scenes']:
        n=scene['manifest']['frame_count'];rows=scene['records'];assert len(rows)==3*n
        by={}
        for r in rows:
            total+=1;by.setdefault(r['profile'],{})[r['id']]=r
            assert r['input_sha256']==scene['manifest']['frame_sha256'][r['id']]
            assert r['key']==(r['id']%scene['key_period']==0)
            anchor=r['id']-r['id']%scene['key_period']
            assert r['reference_id']==(0xffffffff if r['key'] else anchor)
            assert r['anchor_id']==anchor
            assert r['cap_fit']==(r['bytes']<=49152)
            assert r['prepare_ms']>=0 and r['receive_ms']>=0
            assert r['forward_ipv4_udp_size_calculation']==r['bytes']+59*math.ceil(r['bytes']/1024)
            if r['profile']=='bm_block4':
                s=r['block_services'];assert s['service_ms']<=r['prepare_ms']+1e-7
                assert r['vector_bytes']==s['vector_bytes'] and r['map_bytes']==s['map_bytes']
                assert all(s[k]>=0 for k in ('search_prediction_ms','transform_quantize_ms','packet_vectors_entropy_ms','key_reconstruction_ms'))
                assert s['search']['candidate_count']==(0 if r['key'] else 25)
                if r['zero_residual']:assert not r['key'] and r['bytes']==r['map_bytes']+r['vector_bytes']+r['header_crc_bytes']
            else:assert r['global_vector_bytes_inside_header']==4
        for i in range(n):
            if i%scene['key_period']==0:assert len({v[i]['rgb_sha256'] for v in by.values()})==1
        for profile,table in by.items():
            summary=scene['summary'][profile];rr=list(table.values());assert len(rr)==n
            assert summary['frames']==n and summary['cap_fail']==sum(not r['cap_fit'] for r in rr)
            assert abs(summary['mean_bytes']-sum(r['bytes'] for r in rr)/n)<1e-7
            assert summary['zero_residual']==sum(r['zero_residual'] for r in rr)
            for region in ('active','roi','background'):
                pixels=sum(r['metrics'][region]['pixels'] for r in rr)
                if pixels:
                    mse=sum(r['metrics'][region]['pixels']*r['metrics'][region]['mse'] for r in rr)/pixels
                    assert abs(mse-summary['regions'][region]['mse'])<1e-7
        for control in ('gm_zero','gm_global'):
            a=scene['summary'][control];b=scene['summary']['bm_block4']
            comparisons.append(dict(scene=scene['name'],control=control,frames=n,
                control_mean_bytes=a['mean_bytes'],block_mean_bytes=b['mean_bytes'],
                complete_byte_change_percent=(b['mean_bytes']/a['mean_bytes']-1)*100,
                active_psnr_change_db=None if a['regions']['active']['psnr'] is None or b['regions']['active']['psnr'] is None else b['regions']['active']['psnr']-a['regions']['active']['psnr'],
                prepare_control_ms=a['prepare_mean_ms'],prepare_block_ms=b['prepare_mean_ms'],
                receive_control_ms=a['receive_mean_ms'],receive_block_ms=b['receive_mean_ms']))
        if not scene['manifest'].get('synthetic'):
            m=scene['manifest'];path=Path(m['source'])
            if path.exists():assert hashlib.sha256(path.read_bytes()).hexdigest()==m['source_sha256']
            else:missing_media.append(str(path))
    assert total==d['packet_count']==612
    out=dict(missing_external_media=sorted(set(missing_media)),source_bindings=len(d['source_sha256']),actual_packets=total,comparisons=comparisons,
             scope='Stored same-source algorithm accounting/quality only; no paced transport, native decoder or hardware proof')
    if '--write-summary' in sys.argv:(HERE/'summary.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))


if __name__=='__main__':main()
