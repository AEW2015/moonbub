"""Pinned dense-Q14 golden tiles, normative extremes plus retained gameplay."""
from pathlib import Path
import hashlib,importlib.util,json,sys
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
ft=module('idct69_dense_golden',ROOT/'experiments/python-transform-study/fixed_codec.py')
h=module('idct69_frozen43_helpers',ROOT/'experiments/python-game-direct-rx-v43-study/helpers.py')
before=sys.modules.get('helpers')
try:
    sys.modules['helpers']=h
    rx=module('idct69_frozen43_receiver',ROOT/'experiments/python-game-direct-rx-v43-study/receiver.py')
finally:
    if before is None:sys.modules.pop('helpers',None)
    else:sys.modules['helpers']=before

def packed(a,bits):
    mask=(1<<bits)-1
    return ''.join(f'{int(v)&mask:0{bits//4}x}' for v in a.reshape(-1)[::-1])

def main():
    rng=np.random.default_rng(690045);tiles=[];records=[]
    def add(a,kind):
        a=np.asarray(a,np.int64);assert a.shape==(8,8)
        bad=bool(np.any(a < -522240) or np.any(a > 522240))
        expected=np.zeros((8,8),np.int64) if bad else ft.inverse(a)
        assert np.all(expected>=-(1<<23)) and np.all(expected<(1<<23))
        tiles.append(f'{len(tiles)+1} {packed(a,20)} {packed(expected,24)} {int(bad)}\n');records.append(kind)
    add(np.zeros((8,8),np.int64),'zero')
    for dc in(-522240,-2048,-2,-1,1,2,2048,522240):
        a=np.zeros((8,8),np.int64);a[0,0]=dc;add(a,'DC')
    for index in range(64):
        for sign in(-1,1):
            a=np.zeros((8,8),np.int64);a.flat[index]=sign*522240;add(a,'normative-impulse')
    for _ in range(256):add(rng.integers(-522240,522241,(8,8),dtype=np.int64),'normative-random')
    add(np.full((8,8),522240,np.int64),'normative-positive')
    add(np.full((8,8),-522240,np.int64),'normative-negative')
    for bad in(-524288,-522241,522241,524287):
        a=np.zeros((8,8),np.int64);a[2,5]=bad;add(a,'invalid-domain')
    source=ROOT/'experiments/python-game-binary-qual-v40-study';data=h.load(source/'results.json')
    packet_pins={}
    for c in data['cases']:
        for fid in (0,1,24,len(c['rows'])-1):
            row=c['rows'][fid];packet=h.raw(row['packet'],source);parsed=rx.parse(packet)
            packet_pins[c['scene']+'/'+str(fid)]=hashlib.sha256(packet).hexdigest()
            for axis,coeff in enumerate(parsed['coefficients']):
                a=coeff.astype(np.int64)*h.m.roi.block_tables(parsed['qmap'],720,480,axis)
                selected=rng.choice(len(a),64,replace=False)
                for index in selected:add(a[index],'gameplay')
    (HERE/'tiles.hex').write_text(''.join(tiles))
    paths=[Path(__file__),ROOT/'experiments/python-transform-study/fixed_codec.py',source/'results.json',ROOT/'experiments/python-game-direct-rx-v43-study/receiver.py']
    result={'schema':'cu66-idct-v69-fixtures','tiles':len(tiles),'kinds':{k:records.count(k) for k in sorted(set(records))},
            'seed':690045,'fixture_sha256':hashlib.sha256((HERE/'tiles.hex').read_bytes()).hexdigest(),
            'source_sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
            'source_packet_sha256':packet_pins,'input_signed_bits':20,'output_signed_bits':24,'rounding':'two separate (x+8192) arithmetic >>14',
            'scope':'Independent dense matrix oracle. Gameplay sampling plus normative-domain vectors, not all full frames or FPGA timing proof.'}
    (HERE/'fixtures.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'tiles':len(tiles),'kinds':result['kinds']}))
if __name__=='__main__':main()
