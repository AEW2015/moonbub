"""Actual arbitrary whole-plane AB38/BR88 masks; no projected work counts."""
from array import array
import importlib.util
import json
import hashlib
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('v90_frozen_observation_reader',ROOT/'experiments/python-gamebub-v89/observations/data.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
FIELDS=old.FIELDS
PLANE_TILES=(5400,1350,1350)


def candidate_path():
    selected=json.loads((ROOT/'experiments/python-gamebub-v88/wire/results.json').read_text())
    return (ROOT/selected['selected_report']).with_name('candidates.jsonl')


def candidate_rows():
    rows=[json.loads(line) for line in candidate_path().read_text().splitlines()]
    result={(r['cohort'],r['fid'],r['mask']):r for r in rows}
    assert len(rows)==len(result)==3656
    assert all({m for c,f,m in result if (c,f)==key}==set(range(8)) for key in {(c,f)for c,f,m in result})
    return result


def iter_raw(*,only=None,verify=True):
    """Yield actual paired canonical arrays once per source; readers verify EOF."""
    br_area=ROOT/'experiments/python-gamebub-v89/observations'
    ab_area=ROOT/'experiments/python-gamebub-v86/contexts'
    ab=((f,p) for f,p in old._records(ab_area,11,914,verify) if f['cap']==65536)
    for (br,bpayload),(frame,apayload) in zip(old._records(br_area,12,457,verify),ab,strict=True):
        for key in ('cohort','fid','ordinal','key','canonical_coefficients_sha256'):
            assert br[key]==frame[key]
        if only is not None and (br['cohort'],br['fid']) not in only:continue
        apayload=old._widen(apayload)
        assert len(apayload)==len(bpayload)==8100*240
        assert len(br['chunks'])==3 and [c['axis']for c in br['chunks']]==[0,1,2]
        yield br,apayload,bpayload


def blend(ab,br,mask):
    if type(mask)is not int or not 0<=mask<8:raise ValueError('three-plane mask')
    parts=[];offset=0
    for axis,count in enumerate(PLANE_TILES):
        source=br if mask&(1<<axis) else ab
        parts.append(source[offset*240:(offset+count)*240]);offset+=count
    return b''.join(parts)


def iter_masks(masks=range(8),*,only=None,verify=True):
    masks=tuple(masks)
    if not masks or len(set(masks))!=len(masks) or any(type(m)is not int or not 0<=m<8 for m in masks):
        raise ValueError('mask list')
    candidates=candidate_rows()
    for base,ab,br in iter_raw(only=only,verify=verify):
        result=[]
        for mask in masks:
            row=candidates[base['cohort'],base['fid'],mask]
            payload=blend(ab,br,mask);shared,contexts=old._expand(payload)
            frame={k:v for k,v in base.items() if k not in ('work_sha256','shared_totals','context_totals','chunks')}
            frame.update(mask=mask,policy='mask_'+str(mask),shared_work=shared,context_work=contexts,
                         wire_bytes=row['wire_bytes'],metadata_bytes=sum(row['components'][k] for k in ('header','mode_body','qmap','chunk_directory')),
                         packet_sha256=row['packet_sha256'],work_sha256=hashlib.sha256(payload).hexdigest(),
                         BR88_bits=row['BR88_bits'],remaining_decisions=row['remaining_decisions'],remaining_renorm=row['remaining_renorm'],fits_49152=row['wire_bytes']<=49152)
            assert sum(r['plain_bits'] for tile in contexts for r in tile)==row['BR88_bits']
            assert sum(r['decisions'] for tile in contexts for r in tile)==row['remaining_decisions']
            assert sum(r['renorm'] for tile in contexts for r in tile)==row['remaining_renorm']
            assert sum(r['crc_bytes'] for r in shared)==row['components']['chunk_payloads']
            result.append(frame)
        yield result


def plane_totals(payload):
    """Exact summation of packed actual work; avoids eight dict expansions."""
    words=array('I');words.frombytes(payload)
    if sys.byteorder!='little':words.byteswap()
    output=[];begin=0
    for count in PLANE_TILES:
        stop=(begin+count)*60;start=begin*60
        rows=[{field:sum(words[start+row*12+i:stop:60]) for i,field in enumerate(FIELDS)}for row in range(5)]
        output.append(dict(shared=rows[0],contexts=rows[1:]))
        begin+=count
    return output


def merged_totals(ab,br,mask):
    shared={k:0 for k in FIELDS};contexts=[dict(shared)for _ in range(4)]
    for axis in range(3):
        selected=br[axis] if mask&(1<<axis) else ab[axis]
        for k,v in selected['shared'].items():shared[k]+=v
        for c in range(4):
            for k,v in selected['contexts'][c].items():contexts[c][k]+=v
    return shared,contexts
