#!/usr/bin/env python3
"""Independent archive/grammar/history verification, no reuse encoder import."""
from pathlib import Path
import hashlib
import importlib.util
import json
import struct
import sys
import zlib
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
CONTROL=HERE.parent/'python-game-controller-v34-study'

def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);o=importlib.util.module_from_spec(s);sys.modules[name]=o;s.loader.exec_module(o);return o

def sha(data):return hashlib.sha256(data).hexdigest()
def raw(desc,folder=HERE):
    name=Path(desc['path']);assert not name.is_absolute() and '..' not in name.parts
    stored=(folder/name).read_bytes();assert sha(stored)==desc['stored_sha256']
    dc=zlib.decompressobj();data=dc.decompress(stored,desc['raw_bytes']+1)
    assert dc.eof and not dc.unused_data and not dc.unconsumed_tail
    assert len(data)==desc['raw_bytes'] and sha(data)==desc['raw_sha256']
    return data

def main():
    result=json.loads((HERE/'results.json').read_text())
    for name,value in result['source_sha256'].items():assert sha((ROOT/name).read_bytes())==value,name
    original=json.loads((CONTROL/'results.json').read_text())
    assert sha((CONTROL/'results.json').read_bytes())==result['input_controller_results_sha256']
    dec=load('reuse35_verify_syntax',HERE.parent/'python-game-hierarchy-v34-study/decoder.py')
    frame=load('reuse35_verify_frame',CONTROL/'model.py')
    rows={(r['scene'],r['policy'],r['id']):r for r in result['rows']}
    components=variants=pixel_decodes=0
    for case in original['cases']:
        if case['policy']=='control':continue
        reference=None
        for prior in case['rows']:
            if prior['key']:reference=None
            if not prior['key']:
                row=rows[(case['scene'],case['policy'],prior['id'])]
                pb,cb=raw(row['parent_bytes']),raw(row['child_bytes'])
                parent=dec.unpack_gm27(pb,23,15);child=dec.unpack_gm27(cb,45,30)
                assert sha(parent.tobytes())==row['parent_array_sha256']
                assert sha(child.tobytes())==row['child_array_sha256']
                component=raw(row['component']);expanded,info=dec.unpack(component,720,480,return_info=True)
                np.testing.assert_array_equal(expanded,child)
                if info['parent'] is not None:np.testing.assert_array_equal(info['parent'],parent)
                oldinfo=row['original_component_info'];newinfo=row['new_component_info']
                for key in oldinfo:assert oldinfo[key]==newinfo[key],key
                assert newinfo['work']['frozen_pack_vectors_calls']==0
                assert newinfo['work']['cache_maps_validated']==2
                assert newinfo['work']['hm34_candidates_costed']==3
                assert newinfo['work']['hm34_candidates_serialized']==1
                charged=row['already_charged_analysis']
                assert charged['parent_motion_map']==prior['analyses']['half32']['work']['motion_map']
                assert charged['child_motion_map']==prior['analyses']['child']['work']['motion_map']
                assert charged['parent_ms']==prior['analyses']['half32']['wall_ms']
                assert charged['child_ms']==prior['analyses']['child']['wall_ms']
                components+=1
                for v in row['variants']:
                    packet=raw(v['frame']);oldpacket=raw(v['original_base_packet'],CONTROL)
                    assert packet==oldpacket
                    meta=frame.parse_metadata(packet);offset=frame.HEADER.size+meta['qmap_bytes']
                    assert packet[offset:offset+meta['vector_bytes']]==component
                    assert meta['reconstructed_tag'].hex()==v['reconstructed_tag']
                    # Pixel decode verifies frame CRC and reconstructed pixel tag
                    # on the original accepted causal reference. Byte identity
                    # gives the same exact result for old and reused frames.
                    pixels,decoded=frame.decode(packet,reference,expected_epoch=25,
                                                expected_reference_id=prior['reference_id'])
                    assert decoded['reconstructed_tag'].hex()==v['reconstructed_tag']
                    variants+=1;pixel_decodes+=1
            # Reconstruct the original accepted history, not a fixed reference.
            selected=raw(prior['base_packet'],CONTROL)
            reference,meta=frame.decode(selected,reference,expected_epoch=25,
                                       expected_reference_id=None if prior['key'] else prior['reference_id'])
            assert meta['reconstructed_tag'].hex()==prior['reconstructed_tag']
        print(json.dumps(dict(scene=case['scene'],policy=case['policy'],verified_components=components,verified_variants=variants)),flush=True)
    assert components==184 and variants==368 and len(rows)==184
    print(json.dumps(dict(ok=True,components=components,exact_frame_bytes=variants,
                          causal_pixel_tag_verified_frames=pixel_decodes,selected_history_frames=192,
                          independent_syntax_decoder=True,reuse_encoder_imported=False)),flush=True)
if __name__=='__main__':main()
