"""Verified actual BR88 chunks merged with the frozen residual components."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import struct

ROOT=Path(__file__).resolve().parents[3]
AREA=Path(__file__).resolve().parent


def iter_frames(*,verify=True):
    index=json.loads((AREA/'index.json').read_text());path=AREA/index['data']['path']
    if verify:assert hashlib.sha256(path.read_bytes()).hexdigest()==index['data']['gzip_sha256']
    spec=importlib.util.spec_from_file_location('br88_old_data',ROOT/'experiments/python-gamebub-v85/residual/data.py')
    old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    digest=hashlib.sha256();count=0
    with gzip.open(path,'rb') as stream:
        def take(n):
            data=stream.read(n);assert len(data)==n,'BR88 component truncation';digest.update(data);return data
        for frame in old.iter_frames():
            size,=struct.unpack('<I',take(4));assert 1<=size<=65536
            meta=json.loads(take(size))
            for key in ('cohort','fid','ordinal','key','canonical_coefficients_sha256'):assert frame[key]==meta[key]
            for axis,plane in enumerate(frame['variants']['65536']):
                assert len(plane)==len(meta['planes'][axis])
                for chunk,observation in zip(plane,meta['planes'][axis],strict=True):
                    assert chunk['blocks']==observation['blocks'] and len(chunk['data'])==observation['old_bytes']
                    data=take(observation['new_bytes'])
                    if verify:assert hashlib.sha256(data).hexdigest()==observation['br88_sha256']
                    chunk.update(observation,br88=data)
            count+=1;yield frame
        assert stream.read(1)==b''
    if verify:assert count==index['native_sources']==457 and digest.hexdigest()==index['data']['raw_sha256']
