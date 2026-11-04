"""Replay frozen accepted packets, then rotate/interleave actual P predictors."""
from pathlib import Path
import argparse
import hashlib
import json
import platform
import time
import zlib
import numpy as np
import model as m

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
V27=HERE.parent/'python-game-unified-v27-study'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def raw(desc):
    path=Path(desc['path'])
    assert not path.is_absolute() and '..' not in path.parts
    stored=(V27/path).read_bytes();assert hashlib.sha256(stored).hexdigest()==desc['stored_sha256']
    data=zlib.decompress(stored)
    assert len(data)==desc['raw_bytes'] and hashlib.sha256(data).hexdigest()==desc['raw_sha256']
    return data


def stats(values):
    return dict(mean_ms=float(np.mean(values)),median_ms=float(np.median(values)),
                p95_ms=float(np.percentile(values,95)),minimum_ms=float(min(values)),maximum_ms=float(max(values)))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--rounds',type=int,default=5);args=parser.parse_args()
    data=json.loads((V27/'results.json').read_text());cases=[];all_inputs=[];decoded_count=0
    started=time.perf_counter();frozen_identity=m.frozen.predict
    for case in data['cases']:
        reference=None;previous=None;refid=None;rows=[]
        for row in case['rows']:
            if row['key']:reference=None;previous=None;refid=None
            packet=raw(row['base_packet'])
            opts=dict(expected_epoch=25,expected_reference_id=refid)
            old,meta=m.frozen.decode(packet,reference,**opts)
            new,new_meta=m.decode(packet,reference,**opts)
            for a,b in zip(old,new):np.testing.assert_array_equal(a,b)
            assert meta['reconstructed_tag']==new_meta['reconstructed_tag']
            decoded_count+=1
            if case['policy']=='unified_causal' and not row['key']:
                prediction,work=m.predict_with_info(reference,meta['vectors'],meta['block_size'])
                for a,b in zip(prediction,m.frozen.predict(reference,meta['vectors'],meta['block_size'])):np.testing.assert_array_equal(a,b)
                desc=dict(scene=case['scene'],frame_id=row['id'],reference_id=refid,block_size=meta['block_size'],
                          base_packet=row['base_packet'],reference_packet=previous,reference_tag=meta['reference_tag'].hex(),
                          reference_plane_shapes=[list(p.shape) for p in reference],
                          reference_plane_sha256=[hashlib.sha256(p.astype('<i2',copy=False).tobytes()).hexdigest() for p in reference],
                          vector_dtype='int8',vector_shape=list(meta['vectors'].shape),
                          vectors_hex=meta['vectors'].tobytes().hex(),work=work,old_ms=[],new_ms=[])
                rows.append(desc);all_inputs.append((reference,meta['vectors'],meta['block_size'],desc))
            reference=old;previous=row['base_packet'];refid=row['id']
        cases.append(dict(scene=case['scene'],policy=case['policy'],accepted_frames=len(case['rows']),P_rows=rows))
    print(json.dumps(dict(stage='packet_replay',accepted_frames=decoded_count,P_inputs=len(all_inputs),seconds=time.perf_counter()-started)),flush=True)
    # All distinct P inputs are warmed once; function order alternates per call,
    # and each round rotates and reverses order to reduce locality/order bias.
    for ref,v,bs,_ in all_inputs:m.predict(ref,v,bs);m.frozen.predict(ref,v,bs)
    count=len(all_inputs)
    for r in range(args.rounds):
        order=np.roll(np.arange(count),r*17)
        if r%2:order=order[::-1]
        for j,i in enumerate(order):
            ref,v,bs,desc=all_inputs[i]
            functions=[('old_ms',m.frozen.predict),('new_ms',m.predict)]
            if (j+r)%2:functions.reverse()
            for key,fn in functions:
                start=time.perf_counter_ns();fn(ref,v,bs);desc[key].append((time.perf_counter_ns()-start)/1e6)
        print(json.dumps(dict(stage='timing',round=r+1,rounds=args.rounds)),flush=True)
    old=[x for _,_,_,d in all_inputs for x in d['old_ms']];new=[x for _,_,_,d in all_inputs for x in d['new_ms']]
    pins=dict(data['source_sha256'])
    own_sources=sorted(HERE.glob('*.py'))+[HERE/'README.md']
    pins.update({p.relative_to(ROOT).as_posix():sha(p) for p in [V27/'results.json',V27/'model.py',*own_sources]})
    assert m.frozen.predict is frozen_identity
    result=dict(schema='gamebub-taps-v28',source_sha256=pins,cases=cases,versions=dict(python=platform.python_version(),numpy=np.__version__),
                replay=dict(accepted_frames=decoded_count,bit_exact=True,reconstructed_tags_exact=True,global_predict_unmodified=True),
                timing=dict(rounds=args.rounds,P_inputs=count,old=stats(old),new=stats(new),mean_speedup=float(np.mean(old)/np.mean(new)),
                            method='Warm all exact references/maps once; rotate by 17 and reverse alternate rounds; alternate old/new function order per input. Predictor only, validations included.'),
                logical_reads=dict(old=sum(d['work']['frozen_reference_sample_fetches'] for *_,d in all_inputs),
                                   new=sum(d['work']['reference_sample_fetches'] for *_,d in all_inputs)),
                memory=dict(compressed_complete_packet_cap_bytes=49152,reference_plane_bytes=1036800,prediction_plane_bytes=1036800,
                            frozen_predictor_reference_gathers_per_P=2073600,reference_samples_per_P=518400,
                            note='Compressed packet cap is separate from full int16 Python planes and temporary arrays. No fitted line buffers, FPGA DSP fit, native frame rate, or physical link claim.'))
    (HERE/'results.json').write_text(json.dumps(result,separators=(',',':'))+'\n')
    print(json.dumps({k:result[k] for k in ('replay','timing','logical_reads','memory')}),flush=True)


if __name__=='__main__':main()
