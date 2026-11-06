#!/usr/bin/env python3
"""V2 research metadata: implicit hidden tiles and implicit key operations."""
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import struct
import sys
import zlib

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v84/mode-map-v2'
HEADER=struct.Struct('>4sBBBBHHHHI')
MAGIC=b'CM84'
VERSION=2
IMPLICIT_KEY, VISIBLE_BITS, VISIBLE_RLE=0,1,2
COPY_REF,CONST128,RESIDUAL=0,1,2
FIXED_MASK_SHA256='e08b9861ae9a170c913c6425a5773ff42042a0abfe2fef8cd756cb505a8a8fa5'
VISIBLE_COUNT=7806
BODY_CAP=976


def fixed_profile(hidden_mask):
    if len(hidden_mask)!=8100 or any(type(h) not in (int,bool) or h not in (0,1) for h in hidden_mask):
        raise ValueError('fixed profile mask bounds')
    if hashlib.sha256(bytes(hidden_mask)).hexdigest()!=FIXED_MASK_SHA256:
        raise ValueError('fixed profile mask identity')


def encode(modes,hidden_mask,*,key):
    fixed_profile(hidden_mask)
    if type(key) is not bool or len(modes)!=8100:
        raise ValueError('encoder key/coverage')
    visible=[]
    for mode,hidden in zip(modes,hidden_mask):
        if type(mode) is not int or mode not in (COPY_REF,CONST128,RESIDUAL):
            raise ValueError('encoder operation')
        if hidden:
            if mode!=CONST128:
                raise ValueError('encoder hidden CONST required')
        else:
            if mode==CONST128 or key and mode==COPY_REF:
                raise ValueError('encoder visible/key operation')
            visible.append(int(mode==RESIDUAL))
    assert len(visible)==7806
    if key:
        method,body=IMPLICIT_KEY,b''
    else:
        bits=bytearray(976)
        for i,value in enumerate(visible):
            bits[i//8]|=value<<(7-i%8)
        rle=bytearray();at=0
        while at<len(visible):
            end=at+1
            while end<len(visible) and visible[end]==visible[at] and end-at<128:
                end+=1
            rle.append((visible[at]<<7)|(end-at-1))
            at=end
        method,body=min(((VISIBLE_BITS,bytes(bits)),(VISIBLE_RLE,bytes(rle))),key=lambda x:(len(x[1]),x[0]))
    assert len(body)<=976
    return HEADER.pack(MAGIC,2,method,int(key),16,720,480,8100,len(body),zlib.crc32(body))+body


def decode(packet,hidden_mask,*,key_expected=None):
    """Independent V2 parser; no encoder/body-builder calls or entropy decoding."""
    if not isinstance(packet,bytes) or not 20<=len(packet)<=996:
        raise ValueError('decoder packet bound')
    if len(hidden_mask)!=8100 or any(type(h) not in (int,bool) or h not in (0,1) for h in hidden_mask):
        raise ValueError('decoder mask bounds')
    if hashlib.sha256(bytes(hidden_mask)).hexdigest()!='e08b9861ae9a170c913c6425a5773ff42042a0abfe2fef8cd756cb505a8a8fa5':
        raise ValueError('decoder fixed mask identity')
    magic,version,method,key,group,width,height,tiles,size,crc=HEADER.unpack_from(packet)
    if magic!=b'CM84' or version!=2 or method not in (0,1,2) or key not in (0,1):
        raise ValueError('decoder V2 capability/method')
    if (group,width,height,tiles)!=(16,720,480,8100):
        raise ValueError('decoder geometry')
    if key_expected is not None and (type(key_expected) is not bool or bool(key)!=key_expected):
        raise ValueError('decoder frame key binding')
    if size>976 or len(packet)!=20+size:
        raise ValueError('decoder exact length')
    body=packet[20:]
    if zlib.crc32(body)!=crc:
        raise ValueError('decoder body CRC')
    if key:
        if method!=0 or body:
            raise ValueError('decoder keys require implicit non-COPY method')
        visible=[1]*7806
    elif method==0:
        raise ValueError('decoder implicit key method on delta')
    elif method==1:
        if size!=976 or body[-1]&3:
            raise ValueError('decoder bitset length/padding')
        visible=[(body[i//8]>>(7-i%8))&1 for i in range(7806)]
    else:
        visible=[]
        for token in body:
            run=(token&127)+1
            if len(visible)+run>7806:
                raise ValueError('decoder visible RLE overrun')
            visible.extend([token>>7]*run)
        if len(visible)!=7806:
            raise ValueError('decoder visible RLE underrun')
    modes=[];at=0
    for hidden in hidden_mask:
        if hidden:
            modes.append(1)
        else:
            modes.append(2 if visible[at] else 0)
            at+=1
    if at!=7806 or len(modes)!=8100:
        raise ValueError('decoder profile coverage')
    return modes


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec)
    sys.modules[name]=mod;spec.loader.exec_module(mod);return mod


def stats(values):
    return dict(min=min(values),median=statistics.median(values),max=max(values),total=sum(values))


def main():
    AREA.mkdir(parents=True,exist_ok=True)
    if (AREA/'results.json').exists():
        raise FileExistsError('refusing to overwrite V2 retained result')
    native=load('cu84_mode2_native',ROOT/'experiments/python-gamebub-v82/native/data.py')
    v1_path=ROOT/'experiments/python-gamebub-v84/mode-map/frames.jsonl'
    v1=[json.loads(line) for line in v1_path.read_text().splitlines()]
    paths=[Path(__file__).resolve(),v1_path,ROOT/'scripts/cu66-v84/prototype_mode_map.py',
           ROOT/'experiments/python-gamebub-v84/mode-map/results.json',
           ROOT/'experiments/python-gamebub-v84/entropy/index.json',
           ROOT/'experiments/python-gamebub-v82/native/index.json',
           ROOT/'experiments/python-gamebub-v82/native/data.py']
    report=dict(schema='cu66-v84-mode-map-v2-v1',status='FAIL',source_sha256={str(p.relative_to(ROOT)):sha(p) for p in paths})
    rows=[];packets=[];method_counts=dict.fromkeys(('implicit_key','visible_bits','visible_RLE'),0)
    try:
        for frame in native.iter_frames():
            hidden=frame['hidden_mask'];fixed_profile(hidden)
            modes=[1 if h else 0 if c else 2 for h,c in zip(hidden,frame['copy_ref_mask'])]
            packet=encode(modes,hidden,key=frame['key'])
            decoded=decode(packet,hidden,key_expected=frame['key'])
            assert decoded==modes
            before=v1[len(rows)]
            digest=hashlib.sha256(bytes(decoded)).hexdigest()
            assert (frame['cohort'],frame['fid'],frame['packet_sha256'],digest)==(before['cohort'],before['fid'],before['packet_sha256'],before['decoded_modes_sha256'])
            method=packet[5];method_counts[('implicit_key','visible_bits','visible_RLE')[method]]+=1
            assert len(packet)<=996 and len(packet)<=before['total_bytes']
            rows.append(dict(cohort=frame['cohort'],fid=frame['fid'],key=frame['key'],method=method,
                             original_packet_sha256=frame['packet_sha256'],decoded_modes_sha256=digest,
                             fixed_hidden_mask_sha256=FIXED_MASK_SHA256,body_bytes=len(packet)-20,
                             total_bytes=len(packet),v1_total_bytes=before['total_bytes'],
                             saved_metadata_bytes=before['total_bytes']-len(packet),encoded_sha256=hashlib.sha256(packet).hexdigest()))
            packets.append(packet)
        assert len(rows)==457
        key_cases=[i for i,r in enumerate(rows) if r['key']]
        delta_cases=[i for i,r in enumerate(rows) if not r['key']]
        assert len(key_cases)==20 and all(rows[i]['body_bytes']==0 for i in key_cases)
        vector_indices=[key_cases[0],delta_cases[0],max(range(457),key=lambda i:rows[i]['body_bytes'])]
        vectors=[dict(label=label,**rows[i],packet_hex=packets[i].hex()) for label,i in zip(('key','delta','max_body'),vector_indices)]
        tests=[]
        def rejected(name,packet,mask=hidden,**kwargs):
            try:
                decode(packet,mask,**kwargs)
            except ValueError as exc:
                tests.append(dict(name=name,status='PASS_REJECT',error=str(exc)))
            else:
                raise AssertionError('accepted malformed '+name)
        def packet_for(method,body,key=False,version=2):
            return HEADER.pack(MAGIC,version,method,int(key),16,720,480,8100,len(body),zlib.crc32(body))+body
        implicit=packet_for(0,b'',True)
        assert decode(implicit,hidden)==[1 if h else 2 for h in hidden]
        tests.append(dict(name='implicit_key_positive',status='PASS'))
        bitset=bytes([255])*975+b'\xfc'
        assert decode(packet_for(1,bitset),hidden)==[1 if h else 2 for h in hidden]
        tests.append(dict(name='visible_bits_positive_padding',status='PASS'))
        rle=bytes([255])*60+bytes([253])
        assert decode(packet_for(2,rle),hidden)==[1 if h else 2 for h in hidden]
        tests.append(dict(name='visible_RLE_positive_partial_run',status='PASS'))
        for n in (0,1,19):
            rejected('truncated_header_'+str(n),implicit[:n])
        rejected('V1_rejected',packet_for(0,b'',True,version=1))
        rejected('unknown_method',implicit[:5]+b'\x03'+implicit[6:])
        rejected('bad_magic',b'BAD!'+implicit[4:])
        rejected('geometry_mismatch',implicit[:8]+b'\x00\x01'+implicit[10:])
        rejected('implicit_on_delta',packet_for(0,b''))
        rejected('key_COPY_bitset',packet_for(1,bytes(976),True))
        rejected('key_COPY_RLE',packet_for(2,bytes([127])*60+bytes([125]),True))
        rejected('key_body_not_empty',packet_for(0,b'\0',True))
        rejected('key_flag_mismatch',implicit,key_expected=False)
        rejected('bad_key_flag',implicit[:6]+b'\x02'+implicit[7:])
        rejected('wrong_profile_hidden_mask',implicit,mask=bytes(8100))
        rejected('truncated_bitset',packet_for(1,bitset[:-1]))
        rejected('nonzero_bit_padding',packet_for(1,bitset[:-1]+b'\xff'))
        bad=packet_for(1,bitset)
        rejected('CRC_corruption',bad[:-1]+b'\xf8')
        rejected('exact_length_trailing_byte',bad+b'\0')
        rejected('empty_RLE',packet_for(2,b''))
        rejected('RLE_underrun',packet_for(2,bytes([255])*60))
        rejected('RLE_overrun',packet_for(2,bytes([255])*61))
        rejected('packet_cap',bytes(997))
        try:
            encode([1 if h else 0 for h in hidden],hidden,key=True)
        except ValueError:
            tests.append(dict(name='encoder_rejects_key_COPY',status='PASS_REJECT'))
        else:
            raise AssertionError('encoder keyCOPY accepted')
        # Header and mode bits are not an authenticated reference/content proof.
        (AREA/'frames.jsonl').write_text(''.join(json.dumps(r,separators=(',',':'))+'\n' for r in rows))
        (AREA/'vectors.json').write_text(json.dumps(dict(schema='cu84-mode-map-v2-vectors-v1',vectors=vectors),indent=2)+'\n')
        (AREA/'tests.json').write_text(json.dumps(dict(status='PASS',count=len(tests),checks=tests),indent=2)+'\n')
        (AREA/'source.py').write_bytes(Path(__file__).read_bytes())
        report.update(status='PASS',sources=457,keys=20,deltas=437,method_counts=method_counts,
                      fixed_hidden_mask_sha256=FIXED_MASK_SHA256,visible_count=7806,
                      body_bytes=stats([r['body_bytes'] for r in rows]),
                      total_bytes=stats([r['total_bytes'] for r in rows]),
                      saved_vs_v1_metadata_bytes=stats([r['saved_metadata_bytes'] for r in rows]),
                      v1_total_bytes=sum(r['v1_total_bytes'] for r in rows),
                      tests=len(tests),vectors=len(vectors),body_cap=976,packet_cap=996,
                      artifacts_sha256={p.name:sha(p) for p in sorted(AREA.iterdir()) if p.is_file() and p.name!='results.json'},
                      scope='Operation metadata only, identical native V1 semantics. No residual reencoding, actual stream bitrate savings, hardware or entropy-skip claim.')
    except BaseException as exc:
        report['failure']=repr(exc)
        (AREA/'source.py').write_bytes(Path(__file__).read_bytes())
        raise
    finally:
        (AREA/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        print('V84_MODE_MAP_V2_REPORT',report['status'],AREA/'results.json',flush=True)


if __name__=='__main__':
    main()
