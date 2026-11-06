"""Actual BR88 observations blended with frozen AB38 work by qualified packet mask.

Operation counts are not elapsed clocks. Each returned work hash covers the
actual 12-field shared/four-context canonical tile array in little-endian u32.
"""
from array import array
import gzip
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[3]
AREA=Path(__file__).resolve().parent
FIELDS=('decisions','renorm','stream_bytes','rice_values','events','raw_bytes',
        'header_bytes','crc_bytes','emits','raw_bits','prob_init','plain_bits')
POLICIES=('AB38_control','byte_min','feedback_overhead5','feedback_overhead15','all_BR88')
PLANE_TILES=(5400,1350,1350)


def _records(area,fields,count,verify):
    index=json.loads((area/'index.json').read_text());p=area/index['data']['path']
    if verify:assert hashlib.sha256(p.read_bytes()).hexdigest()==index['data']['gzip_sha256']
    digest=hashlib.sha256();processed=0;size=8100*5*fields*4
    with gzip.open(p,'rb') as stream:
        while True:
            prefix=stream.read(4)
            if not prefix:break
            assert len(prefix)==4
            n,=struct.unpack('<I',prefix);assert 1<=n<=262144
            meta=stream.read(n);payload=stream.read(size)
            assert len(meta)==n and len(payload)==size
            digest.update(prefix);digest.update(meta);digest.update(payload)
            frame=json.loads(meta)
            if verify:
                expected=index['frames'][processed]
                for key in ('cap','cohort','fid','ordinal','canonical_coefficients_sha256','work_sha256'):assert frame[key]==expected[key]
                assert hashlib.sha256(payload).hexdigest()==frame['work_sha256']
            processed+=1;yield frame,payload
    if verify:assert processed==count==index['record_count'] and digest.hexdigest()==index['data']['raw_sha256']


def _widen(payload):
    # Frozen AB38 work has 11 fields. Append an exact zero plain-bit field to
    # each shared/context row; do not alter or project any old primitive count.
    return b''.join(payload[i:i+44]+bytes(4) for i in range(0,len(payload),44))


def _expand(payload):
    words=array('I');words.frombytes(payload)
    if sys.byteorder!='little':words.byteswap()
    shared=[];contexts=[]
    for tile in range(8100):
        at=tile*60
        shared.append(dict(zip(FIELDS,words[at:at+12])))
        contexts.append([dict(zip(FIELDS,words[at+12+c*12:at+24+c*12])) for c in range(4)])
    return shared,contexts


def iter_policies(policies=('AB38_control','feedback_overhead5','feedback_overhead15','all_BR88'),*,verify=True,only=None):
    policies=tuple(policies)
    if not policies or len(set(policies))!=len(policies) or any(p not in POLICIES for p in policies):raise ValueError('policy list')
    selected=json.loads((ROOT/'experiments/python-gamebub-v88/wire/results.json').read_text())
    rows_path=(ROOT/selected['selected_report']).with_name('frames.jsonl')
    rows={(r['policy'],r['cohort'],r['fid']):r for r in map(json.loads,rows_path.read_text().splitlines())}
    assert len(rows)==2285
    old=((frame,payload) for frame,payload in _records(ROOT/'experiments/python-gamebub-v86/contexts',11,914,verify) if frame['cap']==65536)
    for (br,bpayload),(ab,apayload) in zip(_records(AREA,12,457,verify),old,strict=True):
        for key in ('cohort','fid','ordinal','key','canonical_coefficients_sha256'):assert br[key]==ab[key]
        if only is not None and (br['cohort'],br['fid']) not in only:continue
        apayload=_widen(apayload);assert len(apayload)==len(bpayload)==8100*240
        result=[]
        for policy in policies:
            row=rows[policy,br['cohort'],br['fid']]
            assert row['decoded']['coefficient_sha256']==br['canonical_coefficients_sha256']
            offset=0;pieces=[]
            for axis,tiles in enumerate(PLANE_TILES):
                source=bpayload if row['mask']&(1<<axis) else apayload
                pieces.append(source[offset*240:(offset+tiles)*240]);offset+=tiles
            payload=b''.join(pieces);shared,contexts=_expand(payload)
            frame={k:v for k,v in br.items() if k not in ('work_sha256','shared_totals','context_totals','chunks')}
            frame.update(policy=policy,mask=row['mask'],shared_work=shared,context_work=contexts,
                         wire_bytes=row['wire_bytes'],metadata_bytes=sum(row['components'][k] for k in ('header','mode_body','qmap','chunk_directory')),
                         packet_sha256=row['packet_sha256'],work_sha256=hashlib.sha256(payload).hexdigest(),
                         BR88_bits=row['BR88_bits'],remaining_decisions=row['remaining_decisions'],remaining_renorm=row['remaining_renorm'])
            assert sum(w['plain_bits'] for tile in contexts for w in tile)==row['BR88_bits']
            assert sum(w['decisions'] for tile in contexts for w in tile)==row['remaining_decisions']
            assert sum(w['renorm'] for tile in contexts for w in tile)==row['remaining_renorm']
            assert sum(w['crc_bytes'] for w in shared)==row['components']['chunk_payloads']
            result.append(frame)
        yield result


def iter_frames(policy='AB38_control',*,verify=True,only=None):
    for frames in iter_policies((policy,),verify=verify,only=only):yield frames[0]
