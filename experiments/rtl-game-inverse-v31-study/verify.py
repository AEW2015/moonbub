#!/usr/bin/env python3
"""Verify retained Q14 arithmetic, source closure, simulation ledgers and mapping."""
from pathlib import Path
import hashlib,importlib.util,json,re,sys,zlib
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    vectors=json.loads((HERE/'vectors.json').read_text());results=json.loads((HERE/'results/results.json').read_text())
    for rel,want in {**vectors['source_sha256'],**results['source_sha256']}.items():
        q=Path(rel);assert not q.is_absolute() and '..' not in q.parts;assert sha(ROOT/q)==want,rel
    assert sha(HERE/'vectors.json')==results['vectors_sha256']
    arrays={}
    for name,desc in vectors['files'].items():
        q=Path(desc['path']);assert not q.is_absolute() and '..' not in q.parts
        packed=(HERE/q).read_bytes();assert hashlib.sha256(packed).hexdigest()==desc['stored_sha256']
        dc=zlib.decompressobj();raw=dc.decompress(packed,desc['raw_bytes']+1)
        assert dc.eof and not dc.unused_data and not dc.unconsumed_tail and len(raw)==desc['raw_bytes'] and hashlib.sha256(raw).hexdigest()==desc['raw_sha256']
        arrays[name]=np.array([int(v,16) for v in raw.split()],np.int64)
    for name,bits in (('coeff',20),('residual',24)):
        a=arrays[name];a[a>=(1<<(bits-1))]-=1<<bits
    count=vectors['blocks'];assert count==33054 and vectors['samples']==count*64
    coeff=arrays['coeff'].reshape(count,8,8);prediction=arrays['prediction'].reshape(count,8,8)
    spec=importlib.util.spec_from_file_location('v31_verify_ft',HERE.parent/'python-transform-study/fixed_codec.py')
    ft=importlib.util.module_from_spec(spec);sys.modules[spec.name]=ft;spec.loader.exec_module(ft)
    residual=ft.inverse(coeff);np.testing.assert_array_equal(residual.reshape(-1),arrays['residual'])
    np.testing.assert_array_equal(np.clip(residual+prediction,0,255).reshape(-1),arrays['pixel'])
    kinds=np.where(np.any(coeff.reshape(count,64)[:,1:]!=0,axis=1),2,np.where(coeff[:,0,0]!=0,1,0))
    np.testing.assert_array_equal(kinds,arrays['kind'])
    assert np.abs(coeff).max()<=522240 and np.abs(residual).max()<=vectors['arithmetic']['proven_output_abs_bound']<2**23
    # Independently bind the real vector groups to actual accepted packet
    # histories, not only to the serialized inverse inputs and NumPy outputs.
    spec=importlib.util.spec_from_file_location('v31_verify_runtime',HERE.parent/'python-game-runtime-v28-study/model.py')
    codec=importlib.util.module_from_spec(spec);sys.modules[spec.name]=codec;spec.loader.exec_module(codec)
    old_dir=HERE.parent/'python-game-controller-v30-study';old=json.loads((old_dir/'results.json').read_text())
    def plane_blocks(a):
        h,w=a.shape;return a.reshape(h//8,8,w//8,8).transpose(0,2,1,3).reshape(-1,8,8)
    source_groups=0
    for case in old['cases']:
        if case['policy']!='band_strict':continue
        ref=None
        for row in case['rows']:
            if row['key']:ref=None
            desc=row['base_packet'];packed=(old_dir/desc['path']).read_bytes()
            assert hashlib.sha256(packed).hexdigest()==desc['stored_sha256']
            dc=zlib.decompressobj();packet=dc.decompress(packed,desc['raw_bytes']+1)
            assert dc.eof and not dc.unused_data and not dc.unconsumed_tail and len(packet)==desc['raw_bytes'] and hashlib.sha256(packet).hexdigest()==desc['raw_sha256']
            output,meta=codec.decode(packet,ref,expected_epoch=25,expected_reference_id=None if row['key'] else row['reference_id'])
            group=next((g for g in vectors['groups'] if g.get('scene')==case['scene'] and g.get('frame_id')==row['id']),None)
            if group:
                pred=tuple(np.full_like(a,128) for a in output) if row['key'] else codec.taps.predict(ref,meta['vectors'],32)
                start=group['start_block']
                for plane,c in enumerate(meta['coefficients']):
                    n=len(c);sl=slice(start,start+n)
                    np.testing.assert_array_equal(coeff[sl],c.astype(np.int64)*codec.roi.block_tables(meta['scale_map'],720,480,plane))
                    np.testing.assert_array_equal(prediction[sl],plane_blocks(pred[plane]))
                    np.testing.assert_array_equal(arrays['pixel'].reshape(count,8,8)[sl],plane_blocks(output[plane]))
                    start+=n
                assert start==group['start_block']+8100;source_groups+=1
            ref=output
    assert source_groups==4
    for case in results['simulations']:
        text=(HERE/'results'/case['log']).read_text()
        assert 'RESET_ABORT_PASS partial_load=1 partial_compute=1 stalled_output=1' in text
        assert f'TEST_PASS blocks={count} samples={count*64} bypass={case["bypass"]} stalls={case["stalls"]}' in text
        blocks=[tuple(map(int,row)) for row in re.findall(r'^BLOCK id=(\d+) kind=(\d+) cycles=(\d+)$',text,re.M)]
        assert len(blocks)==count and [b[0] for b in blocks]==list(range(count))
        assert [b[1] for b in blocks]==kinds.tolist()
        assert sum(b[2] for b in blocks)==case['service_cycles']
        if not case['stalls']:
            expected=np.full(count,260) if not case['bypass'] else np.where(kinds==0,128,np.where(kinds==1,132,260))
            np.testing.assert_array_equal(np.array(blocks)[:,2],expected)
        for record,group in zip(case['frames'],[g for g in vectors['groups'] if 'scene' in g]):
            assert (record['scene'],record['frame_id'],record['blocks'])==(group['scene'],group['frame_id'],8100)
            assert sum(b[2] for b in blocks[group['start_block']:group['start_block']+8100])==record['service_cycles']
            assert record['projection_ms_at_assumed_100MHz']==record['service_cycles']/100000
    assert (HERE/'results/lint.log').read_text()==''
    for name in ('iverilog-run.log','mapped-run.log'):
        text=(HERE/'results'/name).read_text()
        assert f'TEST_PASS blocks={vectors["directed_random_blocks"]}' in text and 'RESET_ABORT_PASS' in text
        assert len(re.findall(r'^BLOCK ',text,re.M))==vectors['directed_random_blocks']
    stat=json.loads((HERE/'results/yosys-stat.json').read_text())
    cells=stat['modules']['\\inverse_q14']['num_cells_by_type']
    assert cells==results['mapped_cell_counts'] and cells['DSP48E1']==8
    assert not any(cells.get(t,0) for t in ('RAMB18E1','RAMB36E1'))
    for name,d in json.loads((HERE/'results/mapped-artifacts.json').read_text()).items():
        q=Path(d['path']);assert not q.is_absolute() and '..' not in q.parts and 0<d['raw_bytes']<64000000
        packed=(HERE/q).read_bytes();assert hashlib.sha256(packed).hexdigest()==d['stored_sha256']
        dc=zlib.decompressobj();raw=dc.decompress(packed,d['raw_bytes']+1)
        assert dc.eof and not dc.unused_data and not dc.unconsumed_tail and len(raw)==d['raw_bytes'] and hashlib.sha256(raw).hexdigest()==d['raw_sha256']
        if name=='mapped.json':
            net=json.loads(raw);actual={}
            for c in net['modules']['inverse_q14']['cells'].values():actual[c['type']]=actual.get(c['type'],0)+1
            assert actual==cells
    assert all(results[k] is False for k in ('physical_30fps_proven','vivado_timing_closed','full_decoder_implemented'))
    manifest=json.loads((ROOT/'docs/prototype-v31-provenance.json').read_text())
    for rel,want in manifest['file_sha256'].items():assert sha(ROOT/rel)==want,rel
    print(json.dumps(dict(rtl_cases=3,blocks_per_case=count,checked_samples=3*count*64,
                          four_state_rtl_blocks=results['iverilog_directed_blocks'],mapped_functional_blocks=results['mapped_directed_blocks'],
                          mapped_DSP48E1=cells['DSP48E1'],real_component_frames_replayed=source_groups,
                          arithmetic_and_cycle_ledgers_replayed=True,physical_30fps_proven=False)))

if __name__=='__main__':main()
