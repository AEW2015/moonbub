#!/usr/bin/env python3
"""A bounded research operation map, not a replacement residual/wire codec."""
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import struct
import sys
import zlib

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v84/mode-map'
COPY_REF, CONST128, RESIDUAL = 0, 1, 2
FLAT, GROUP16, RLE64 = 0, 1, 2
TILES = 8100
PLANES = (5400, 1350, 1350)
BODY_CAP = 2025
HEADER = struct.Struct('>4sBBBBHHHHI')
MAGIC = b'CM84'


def group_ranges():
    offset = 0
    for count in PLANES:
        for start in range(0, count, 16):
            yield offset + start, min(16, count - start)
        offset += count


def pack2(values):
    out = bytearray((len(values)+3)//4)
    for i,value in enumerate(values):
        if type(value) is not int or value not in (0,1,2):
            raise ValueError('unknown encoder tile operation')
        out[i//4] |= value << (6-2*(i%4))
    return bytes(out)


def bodies(modes):
    if len(modes) != TILES:
        raise ValueError('encoder tile coverage')
    flat = pack2(modes)
    group = bytearray()
    for start,count in group_ranges():
        values = modes[start:start+count]
        if all(v==values[0] for v in values):
            group.append(values[0])
        else:
            group.append(3)
            group.extend(pack2(values))
    rle = bytearray()
    at = 0
    while at<TILES:
        stop=at+1
        while stop<TILES and modes[stop]==modes[at] and stop-at<64:
            stop += 1
        rle.append(((stop-at-1)<<2)|modes[at])
        at=stop
    return [flat, bytes(group), bytes(rle)]


def encode(modes, hidden_mask, *, key):
    modes = list(modes)
    if type(key) is not bool or len(hidden_mask)!=TILES or len(modes)!=TILES:
        raise ValueError('encoder profile/coverage')
    if any(type(h) not in (int,bool) or h not in (0,1) for h in hidden_mask):
        raise ValueError('encoder hidden mask')
    for mode,hidden in zip(modes,hidden_mask):
        if type(mode) is not int or mode not in (COPY_REF,CONST128,RESIDUAL):
            raise ValueError('encoder tile mode')
        if (mode==CONST128) != bool(hidden) or (key and mode==COPY_REF):
            raise ValueError('encoder mode/profile disagreement')
    candidates = bodies(modes)
    method = min(range(3),key=lambda k:(len(candidates[k]),k))
    body=candidates[method]
    assert len(body)<=BODY_CAP
    return HEADER.pack(MAGIC,1,method,int(key),16,720,480,TILES,len(body),zlib.crc32(body)) + body


def decode(packet, hidden_mask, *, key_expected=None):
    """Independent bounded grammar parser; never calls encoder or body builders.

    The mask is part of the receiver's fixed profile, not a sender-supplied map.
    This parser checks operation metadata, not residual semantics/content roots.
    """
    if not isinstance(packet,bytes) or not HEADER.size <= len(packet) <= HEADER.size+BODY_CAP:
        raise ValueError('decoder packet bound')
    if len(hidden_mask)!=8100 or any(type(h) not in (int,bool) or h not in (0,1) for h in hidden_mask):
        raise ValueError('decoder fixed hidden profile')
    magic,version,method,flags,group,width,height,tiles,length,crc = HEADER.unpack_from(packet)
    if magic!=b'CM84' or version!=1 or method not in (0,1,2) or flags not in (0,1):
        raise ValueError('decoder capability/version/method')
    if (group,width,height,tiles)!=(16,720,480,8100):
        raise ValueError('decoder geometry')
    if key_expected is not None and (type(key_expected) is not bool or bool(flags)!=key_expected):
        raise ValueError('decoder unexpected key flag')
    if length>2025 or len(packet)!=20+length:
        raise ValueError('decoder exact body length')
    body=packet[20:]
    if zlib.crc32(body)!=crc:
        raise ValueError('decoder CRC32')
    modes=[]
    if method==0:
        if len(body)!=2025:
            raise ValueError('decoder flat length')
        for byte in body:
            for shift in (6,4,2,0):
                op=(byte>>shift)&3
                if op==3:
                    raise ValueError('decoder flat unknown operation')
                modes.append(op)
    elif method==1:
        # Rebuild plane/group coverage independently, including partial leaves.
        cursor=0
        for plane_count in (5400,1350,1350):
            left=plane_count
            while left:
                count=min(16,left)
                if cursor>=len(body):
                    raise ValueError('decoder truncated group tag')
                tag=body[cursor];cursor+=1
                if tag<3:
                    modes.extend([tag]*count)
                elif tag==3:
                    take=(count+3)//4
                    if cursor+take>len(body):
                        raise ValueError('decoder truncated mixed group')
                    chunk=body[cursor:cursor+take];cursor+=take
                    for i in range(count):
                        op=(chunk[i//4]>>(6-2*(i%4)))&3
                        if op==3:
                            raise ValueError('decoder mixed unknown operation')
                        modes.append(op)
                    if count%4 and chunk[-1]&((1<<(2*(4-count%4)))-1):
                        raise ValueError('decoder mixed nonzero padding')
                else:
                    raise ValueError('decoder unknown group tag')
                left-=count
        if cursor!=len(body):
            raise ValueError('decoder trailing group body')
    else:
        for token in body:
            op=token&3
            run=(token>>2)+1
            if op==3:
                raise ValueError('decoder run unknown operation')
            if len(modes)+run>8100:
                raise ValueError('decoder run tile overrun')
            modes.extend([op]*run)
    if len(modes)!=8100:
        raise ValueError('decoder tile coverage')
    for op,hidden in zip(modes,hidden_mask):
        if hidden and op!=1:
            raise ValueError('decoder missing hidden CONST128')
        if not hidden and op==1:
            raise ValueError('decoder visible CONST128 forbidden')
        if flags and op==0:
            raise ValueError('decoder COPY forbidden on key')
    return modes


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod
    spec.loader.exec_module(mod)
    return mod


def stats(values):
    return dict(min=min(values),median=statistics.median(values),max=max(values),total=sum(values))


def main():
    AREA.mkdir(parents=True,exist_ok=True)
    if (AREA/'results.json').exists():
        raise FileExistsError('refusing to overwrite retained mode-map results')
    native=load('cu84_modemap_native',ROOT/'experiments/python-gamebub-v82/native/data.py')
    entropy_path=ROOT/'experiments/python-gamebub-v84/entropy/index.json'
    entropy=json.loads(entropy_path.read_text())
    rows=[];vectors=[];method_counts=dict.fromkeys(('flat2','group16','rle64'),0)
    report=dict(schema='cu66-v84-mode-map-v1',status='FAIL',source_sha256={
        str(Path(__file__).relative_to(ROOT)):sha(Path(__file__)),
        str(entropy_path.relative_to(ROOT)):sha(entropy_path),
        'experiments/python-gamebub-v82/native/index.json':sha(ROOT/'experiments/python-gamebub-v82/native/index.json'),
        'experiments/python-gamebub-v82/native/data.py':sha(ROOT/'experiments/python-gamebub-v82/native/data.py')})
    try:
        fixed_hidden=None
        for original in native.iter_frames():
            meta=entropy['frames'][len(rows)]
            assert (original['cohort'],original['fid'],original['packet_sha256'])==(meta['cohort'],meta['fid'],meta['packet_sha256'])
            hidden=original['hidden_mask']
            if fixed_hidden is None:
                fixed_hidden=hidden
            assert fixed_hidden==hidden
            modes=[CONST128 if h else COPY_REF if c else RESIDUAL for h,c in zip(hidden,original['copy_ref_mask'])]
            candidates=bodies(modes)
            packet=encode(modes,hidden,key=original['key'])
            assert decode(packet,hidden,key_expected=original['key'])==modes
            method=packet[5]
            lengths=[len(x) for x in candidates]
            assert method==min(range(3),key=lambda k:(lengths[k],k))
            method_counts[('flat2','group16','rle64')[method]]+=1
            row=dict(cohort=original['cohort'],fid=original['fid'],key=original['key'],
                     packet_sha256=original['packet_sha256'],method=method,
                     candidate_body_bytes=dict(zip(('flat2','group16','rle64'),lengths)),
                     selected_body_bytes=len(packet)-20,header_bytes=20,total_bytes=len(packet),
                     operation_counts={str(k):modes.count(k) for k in (0,1,2)},
                     decoded_modes_sha256=hashlib.sha256(bytes(modes)).hexdigest(),
                     encoded_sha256=hashlib.sha256(packet).hexdigest())
            rows.append(row)
            if len(vectors)<4 or original['cohort']==3 and original['ordinal']==0:
                vectors.append(dict(cohort=original['cohort'],fid=original['fid'],packet_hex=packet.hex(),
                                    packet_sha256=hashlib.sha256(packet).hexdigest(),
                                    modes_sha256=hashlib.sha256(bytes(modes)).hexdigest()))
        assert len(rows)==457
        assert max(r['selected_body_bytes'] for r in rows)<=2025
        tests=[]
        def rejected(name,packet,mask,**kwargs):
            try:
                decode(packet,mask,**kwargs)
            except ValueError as exc:
                tests.append(dict(name=name,status='PASS_REJECT',error=str(exc)))
            else:
                raise AssertionError('accepted malformed '+name)
        def packet_for(method,body,key=False):
            return HEADER.pack(MAGIC,1,method,int(key),16,720,480,TILES,len(body),zlib.crc32(body))+body
        visible=bytes(8100)
        all_residual=[RESIDUAL]*8100
        flat=pack2(all_residual)
        good=packet_for(FLAT,flat)
        assert decode(good,visible)==all_residual
        tests.append(dict(name='independent_flat_positive',status='PASS'))
        for n in (0,1,19,20,100,len(good)-1):
            rejected('truncation_'+str(n),good[:n],visible)
        rejected('CRC_corruption',good[:-1]+bytes([good[-1]^1]),visible)
        rejected('unknown_method',good[:5]+b'\x03'+good[6:],visible)
        rejected('wrong_version',good[:4]+b'\x02'+good[5:],visible)
        rejected('wrong_geometry',good[:8]+b'\x00\x01'+good[10:],visible)
        rejected('trailing_body',good+b'\0',visible)
        rejected('flat_unknown_opcode',packet_for(FLAT,b'\xff'+flat[1:]),visible)
        rejected('key_COPY',packet_for(FLAT,pack2([COPY_REF]*8100),True),visible)
        rejected('visible_CONST',packet_for(FLAT,pack2([CONST128]*8100)),visible)
        rejected('hidden_not_CONST',good,bytes([1])+visible[1:])
        rejected('unexpected_key_flag',good,visible,key_expected=True)
        rejected('bad_hidden_mask_length',good,visible[:-1])
        rejected('RLE_unknown_opcode',packet_for(RLE64,b'\xff'),visible)
        rejected('RLE_overrun',packet_for(RLE64,bytes([0xfe])*127),visible)
        rejected('RLE_underrun',packet_for(RLE64,b'\x02'),visible)
        rejected('group_bad_tag',packet_for(GROUP16,b'\x04'+bytes([2])*507),visible)
        rejected('group_truncated',packet_for(GROUP16,bytes([2])*507),visible)
        rejected('mixed_truncated',packet_for(GROUP16,b'\x03'),visible)
        rejected('mixed_unknown_opcode',packet_for(GROUP16,b'\x03\xff\x00\x00\x00'+bytes([2])*507),visible)
        # The last chroma group has six tiles: four padding bits must be zero.
        mixed_partial=bytes([2])*507+b'\x03\xaa\xa1'
        rejected('mixed_nonzero_padding',packet_for(GROUP16,mixed_partial),visible)
        # All three methods must have independent positive grammar coverage.
        assert decode(packet_for(GROUP16,bytes([2])*508),visible)==all_residual
        assert decode(packet_for(RLE64,bytes([0xfe])*126+bytes([((36-1)<<2)|2])),visible)==all_residual
        tests.extend((dict(name='independent_group_positive',status='PASS'),dict(name='independent_RLE_positive',status='PASS')))
        (AREA/'frames.jsonl').write_text(''.join(json.dumps(r,separators=(',',':'))+'\n' for r in rows))
        (AREA/'vectors.json').write_text(json.dumps(dict(schema='cu84-mode-map-vectors-v1',vectors=vectors),indent=2)+'\n')
        (AREA/'tests.json').write_text(json.dumps(dict(status='PASS',checks=tests,count=len(tests)),indent=2)+'\n')
        report.update(status='PASS',sources=457,method_counts=method_counts,
                      selected_body_bytes=stats([r['selected_body_bytes'] for r in rows]),
                      total_bytes=stats([r['total_bytes'] for r in rows]),
                      flat2_body_bytes=2025,header_bytes=20,maximum_packet_bytes=2045,
                      maximum_parser_output_modes=8100,tests=len(tests),vectors=len(vectors),
                      artifacts_sha256={p.name:sha(p) for p in sorted(AREA.iterdir()) if p.is_file() and p.name!='results.json'},
                      scope='Operation metadata only. Adds bytes to unchanged AB38; no new residual codec, bitrate saving, entropy skip, timing or hardware claim.')
    except BaseException as exc:
        report['failure']=repr(exc)
        raise
    finally:
        (AREA/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        print('V84_MODE_MAP_REPORT',report['status'],AREA/'results.json',flush=True)


if __name__=='__main__':
    main()
