#!/usr/bin/env python3
"""Independent fixed-mask proof via original HUD geometry and safe-block grid."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
import numpy as np
ROOT=Path(__file__).resolve().parent.parent

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m;spec.loader.exec_module(m);return m

def main():
    result=json.loads((ROOT/'docs/prototype-v67-mask-program.json').read_text())
    h=module('mask67_independent_geometry_helpers',ROOT/'experiments/python-game-filter-qual-v67-study/helpers.py')
    subject=module('mask67_predicate_under_test',ROOT/'experiments/derive_filter_mask_v67.py')
    for name,want in result['source_sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==want,name
    # Independently derive the complete 8x8 blocks strictly inside each HUD box.
    expected=[]
    for x,y,w,hh in h.h.f.f.n.RECTS:
        left=((x+7)//8)*8;top=((y+7)//8)*8
        right=((x+w)//8)*8;bottom=((y+hh)//8)*8
        if right>left and bottom>top:expected.append([left,top,right-left,bottom-top])
    assert expected==result['rectangles_xywh_u16']
    encoded=struct.pack('<16H',*(v for r in expected for v in r))
    assert len(encoded)==32
    # The manifest's packed bytes are independent of JSON integer/object layout.
    assert encoded.hex()==result['packed_rectangles_little_endian_hex']
    safe=np.asarray(h.h.f.f.safe_blocks()[0],dtype=bool).reshape(60,90)
    oracle=np.repeat(np.repeat(safe,8,axis=0),8,axis=1)
    assert oracle.shape==(480,720) and int(oracle.sum())==16384
    first=subject.owned_row(56);saved=first.copy()
    for y in range(480):
        row=subject.owned_row(y)
        assert row.shape==(720,) and row.dtype==np.bool_ and row.nbytes==720
        assert row.flags.owndata and not row.flags.writeable
        np.testing.assert_array_equal(row,oracle[y])
    np.testing.assert_array_equal(first,saved)
    assert hashlib.sha256(oracle.tobytes()).hexdigest()==result['verification']['row_major_mask_sha256']
    xs=np.arange(8,720,8);ys=np.arange(8,480,8)
    horizontal=oracle[:,xs-2]|oracle[:,xs-1]|oracle[:,xs]|oracle[:,xs+1]
    vertical=oracle[ys-2,:]|oracle[ys-1,:]|oracle[ys,:]|oracle[ys+1,:]
    for name,array in [('horizontal',horizontal),('vertical',vertical)]:
        v=result['verification']
        assert array.size==v[name+'_four_tap_footprints_checked']
        assert int(array.sum())==v[name+'_blocked_footprints']
        assert hashlib.sha256(array.tobytes()).hexdigest()==v[name+'_blocked_sha256']
    print(json.dumps(dict(HUD_rectangles_derived=len(expected),descriptor_bytes=len(encoded),
        pixels_checked=int(oracle.size),excluded_pixels=int(oracle.sum()),
        horizontal_tap_groups=int(horizontal.size),vertical_tap_groups=int(vertical.size),
        source_sha256_bindings=len(result['source_sha256']),hardware_fit_proven=False)))

if __name__=='__main__':main()
