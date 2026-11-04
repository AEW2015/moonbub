"""Verify source pins, accepted old packet pixels/tags and retained MV inputs."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np
import model as m
_spec=importlib.util.spec_from_file_location('taps28_replay_helpers',Path(__file__).resolve().with_name('benchmark.py'))
b=importlib.util.module_from_spec(_spec);sys.modules[_spec.name]=b;_spec.loader.exec_module(b)


def main():
    result=json.loads((b.HERE/'results.json').read_text())
    for name,digest in result['source_sha256'].items():
        assert b.sha(b.ROOT/name)==digest,name
    source=json.loads((b.V27/'results.json').read_text())
    decoded=P_inputs=0;old_reads=new_reads=0
    for case,retained in zip(source['cases'],result['cases']):
        assert (case['scene'],case['policy'])==(retained['scene'],retained['policy'])
        rows=iter(retained['P_rows']);ref=None;previous=None;refid=None
        for row in case['rows']:
            if row['key']:ref=None;previous=None;refid=None
            packet=b.raw(row['base_packet']);opts=dict(expected_epoch=25,expected_reference_id=refid)
            old,meta=m.frozen.decode(packet,ref,**opts);new,got=m.decode(packet,ref,**opts)
            for a,c in zip(old,new):np.testing.assert_array_equal(a,c)
            assert meta['reconstructed_tag']==got['reconstructed_tag'];decoded+=1
            if case['policy']=='unified_causal' and not row['key']:
                saved=next(rows);P_inputs+=1
                assert saved['base_packet']==row['base_packet'] and saved['reference_packet']==previous
                assert saved['reference_tag']==meta['reference_tag'].hex() and saved['reference_id']==refid
                assert saved['vectors_hex']==meta['vectors'].tobytes().hex()
                assert saved['reference_plane_sha256']==[hashlib.sha256(p.astype('<i2',copy=False).tobytes()).hexdigest() for p in ref]
                pred,work=m.predict_with_info(ref,meta['vectors'],meta['block_size'])
                for a,c in zip(pred,m.frozen.predict(ref,meta['vectors'],meta['block_size'])):np.testing.assert_array_equal(a,c)
                assert work==saved['work']
                assert len(saved['old_ms'])==len(saved['new_ms'])==result['timing']['rounds']
                old_reads+=work['frozen_reference_sample_fetches'];new_reads+=work['reference_sample_fetches']
            ref=old;previous=row['base_packet'];refid=row['id']
        assert next(rows,None) is None
    assert decoded==192 and P_inputs==92
    assert result['logical_reads']==dict(old=old_reads,new=new_reads)
    print(json.dumps(dict(source_pins=len(result['source_sha256']),accepted_old_GM27_packets=decoded,
                          exact_causal_P_inputs=P_inputs,pixels_and_tags_exact=True,logical_reads=result['logical_reads'])))


if __name__=='__main__':main()
