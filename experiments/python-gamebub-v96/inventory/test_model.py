"""Finite exact stream, address and accepted-reference tests."""
import copy
import hashlib
import importlib.util
from pathlib import Path
import struct

spec = importlib.util.spec_from_file_location('v96_inventory_test_model', Path(__file__).with_name('model.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def reject(fn):
    try:
        fn()
    except (ValueError, KeyError, TypeError):
        return
    raise AssertionError('invalid record accepted')


def fixture():
    tiles = [hashlib.sha256(struct.pack('<I', i)).digest()*2 for i in range(8100)]
    tiles[0] = m.CONST
    return dict(cohort=0, ordinal=0, fid=1, refid=0xffffffff, key=True,
                previous_fid=None, tiles=tiles, hidden_mask=bytes([1])+bytes(8099),
                copy_ref_mask=bytes(8100), canonical_sha256=m.raster_digest(tiles))


def run():
    checks = []
    for plane,(start,count,width) in enumerate(zip(m.STARTS,m.COUNTS,m.WIDTHS)):
        for pos in range(count):
            by,bx=divmod(pos,width//8)
            for y in range(8):
                for x in range(8):
                    logical=m.BASES[plane]+(by*8+y)*width+bx*8+x
                    assert m.physical_byte(logical)==m.BASES[plane]+pos*64+y*8+x
        assert m.address(plane,count-1,2)[1] < 3*m.BANK_STRIDE
    assert m.physical_byte(518400)==518400 and m.physical_byte(560639)==560639
    checks.append('all518400 canonical byte addresses independently match tiled bridge; HUD unchanged')
    a=fixture()
    key,stats=m.encode(a,None,'cross64',0,None)
    assert m.materialize(key,None)[1]==a['tiles']
    assert stats['ops']['CROSSCOPY']==stats['ops']['COPY_REF']==stats['search_queries']==0
    checks.append('initial key has no accepted dictionary or reference read')
    b=copy.deepcopy(a)
    b.update(ordinal=1,fid=2,refid=1,key=False,previous_fid=1)
    b['tiles'][1]=a['tiles'][5399]
    b['copy_ref_mask']=bytes([0,0,1])+bytes(8097)
    b['canonical_sha256']=m.raster_digest(b['tiles'])
    for profile in m.PROFILES:
        wire,stats=m.encode(b,a,profile,1,0)
        assert m.materialize(wire,a)[1]==b['tiles']
        assert stats['ops']['COPY_REF']==1 and stats['ops']['CONST128']==1
        assert stats['materialization_fence']['destination_write_bytes']==518400
        if profile!='control':
            assert stats['ops']['CROSSCOPY']==1
            rec=m.parse(wire)[1][1][0]
            assert rec[3]==5399 and rec[7]==m.BANK_STRIDE+64 and rec[9]==5399*64
    checks.append('control/cross64/cross256 exact accepted-only materialization and explicit source positions')
    before=m.dictionaries(a['tiles'],64)
    # Encoding an aborted proposal cannot mutate an accepted dictionary.
    wire,_=m.encode(b,a,'cross64',1,0,before)
    assert before==m.dictionaries(a['tiles'],64)
    assert m.encode(b,a,'cross64',1,0,before)[0]==wire
    checks.append('aborted proposal leaves accepted dictionary unchanged; replay byte-identical')
    reject(lambda:m.materialize(wire,dict(a,fid=999)))
    reject(lambda:m.parse(wire[:-1]))
    reject(lambda:m.parse(wire+b'x'))
    corrupt=bytearray(wire)
    n,=struct.unpack_from('<I',wire,8)
    corrupt[16+n+8]^=1  # destination relative physical byte
    reject(lambda:m.parse(corrupt))
    reject(lambda:m.encode(b,a,'cross64',0,0) and m.parse(m.encode(b,a,'cross64',0,0)[0]))
    checks.append('wrong accepted identity, truncation, extra bytes, bad addresses and same bank ownership reject')
    return checks


if __name__=='__main__':
    import json
    print(json.dumps(dict(status='PASS',checks=run()),indent=2))
