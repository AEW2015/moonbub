"""Actual re-encoded AB38 context observations; counts are not elapsed clocks."""
from array import array
import gzip
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parent
FIELDS=('decisions','renorm','stream_bytes','rice_values','events','raw_bytes',
        'header_bytes','crc_bytes','emits','raw_bits','prob_init')
WORK_BYTES=8100*55*4


def iter_frames(root=None,*,verify=True):
    root=Path(root) if root is not None else ROOT
    index=json.loads((root/'index.json').read_text());path=root/index['data']['path']
    if verify:assert hashlib.sha256(path.read_bytes()).hexdigest()==index['data']['gzip_sha256']
    raw=hashlib.sha256();count=0
    with gzip.open(path,'rb') as stream:
        while True:
            prefix=stream.read(4)
            if not prefix:break
            assert len(prefix)==4
            n,=struct.unpack('<I',prefix);assert 1<=n<=262144
            meta=stream.read(n);payload=stream.read(WORK_BYTES)
            assert len(meta)==n and len(payload)==WORK_BYTES
            raw.update(prefix);raw.update(meta);raw.update(payload)
            frame=json.loads(meta)
            if verify:
                expected=index['frames'][count]
                for key in ('cap','cohort','fid','ordinal','canonical_coefficients_sha256','work_sha256'):
                    assert frame[key]==expected[key]
                assert hashlib.sha256(payload).hexdigest()==frame['work_sha256']
            words=array('I');words.frombytes(payload)
            if sys.byteorder!='little':words.byteswap()
            shared=[];contexts=[]
            for tile in range(8100):
                at=tile*55
                shared.append(dict(zip(FIELDS,words[at:at+11])))
                contexts.append([dict(zip(FIELDS,words[at+11+c*11:at+22+c*11])) for c in range(4)])
            frame['shared_work']=shared;frame['context_work']=contexts
            count+=1;yield frame
    if verify:
        assert count==index['record_count']==914
        assert raw.hexdigest()==index['data']['raw_sha256']
