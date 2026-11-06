#!/usr/bin/env python3
"""Fixed-profile operation bodies, including bit-packed visible group masks."""
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import sys

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v86/maps'
MASK_SHA='e08b9861ae9a170c913c6425a5773ff42042a0abfe2fef8cd756cb505a8a8fa5'
COPY,CONST,RESIDUAL=0,1,2


def profile(hidden):
    if len(hidden)!=8100 or any(type(x) not in (int,bool) or x not in (0,1) for x in hidden):
        raise ValueError('fixed hidden mask shape')
    if hashlib.sha256(bytes(hidden)).hexdigest()!=MASK_SHA:
        raise ValueError('fixed hidden mask identity')


def groups():
    offset=0
    for total in (5400,1350,1350):
        for start in range(0,total,16):yield range(offset+start,offset+min(start+16,total))
        offset+=total


def _group_body(modes,hidden):
    bits=[]
    for group in groups():
        values=[int(modes[i]==RESIDUAL) for i in group if not hidden[i]]
        if not values:tag=3
        elif not any(values):tag=0
        elif all(values):tag=1
        else:tag=2
        bits.extend(((tag>>1)&1,tag&1))
        if tag==2:bits.extend(values)
    bits.extend([0]*((-len(bits))%8))
    return bytes(sum(bits[i+j]<<(7-j) for j in range(8)) for i in range(0,len(bits),8))


def encode_body(modes,hidden,*,key):
    profile(hidden)
    if type(key) is not bool or len(modes)!=8100:raise ValueError('key/operation coverage')
    visible=[]
    for mode,h in zip(modes,hidden):
        if type(mode) is not int or mode not in (COPY,CONST,RESIDUAL):raise ValueError('operation')
        if h:
            if mode!=CONST:raise ValueError('hidden CONST')
        else:
            if mode==CONST or key and mode==COPY:raise ValueError('visible/key operation')
            visible.append(int(mode==RESIDUAL))
    if key:return 0,b''
    raw=bytearray(976)
    for i,value in enumerate(visible):raw[i//8]|=value<<(7-i%8)
    runs=bytearray();at=0
    while at<len(visible):
        end=at+1
        while end<len(visible) and visible[end]==visible[at] and end-at<128:end+=1
        runs.append((visible[at]<<7)|(end-at-1));at=end
    method,body=min(((1,bytes(raw)),(2,bytes(runs)),(3,_group_body(modes,hidden))),key=lambda x:(len(x[1]),x[0]))
    assert len(body)<=976
    return method,body


def decode_body(method,body,hidden,*,key):
    """Independent grammar parser: never invokes an encoder or body builder."""
    if type(method) is not int or method not in (0,1,2,3) or type(key) is not bool:
        raise ValueError('method/key')
    if type(body) is not bytes or len(body)>976:raise ValueError('body bound')
    if len(hidden)!=8100 or any(type(x) not in (int,bool) or x not in (0,1) for x in hidden):
        raise ValueError('decoder mask shape')
    if hashlib.sha256(bytes(hidden)).hexdigest()!=MASK_SHA:raise ValueError('decoder fixed profile')
    if key:
        if method!=0 or body:raise ValueError('implicit key body')
        return [1 if h else 2 for h in hidden]
    if method==0:raise ValueError('key method on delta')
    if method==1:
        if len(body)!=976 or body[-1]&3:raise ValueError('bitset length/padding')
        values=[(body[i//8]>>(7-i%8))&1 for i in range(7806)]
        out=[];at=0
        for h in hidden:
            out.append(1 if h else 2 if values[at] else 0)
            if not h:at+=1
        return out
    if method==2:
        values=[]
        for token in body:
            count=(token&127)+1
            if len(values)+count>7806:raise ValueError('RLE overrun')
            values.extend([token>>7]*count)
        if len(values)!=7806:raise ValueError('RLE underrun')
        out=[];at=0
        for h in hidden:
            out.append(1 if h else 2 if values[at] else 0)
            if not h:at+=1
        return out
    pos=0
    def bit():
        nonlocal pos
        if pos>=len(body)*8:raise ValueError('group truncation')
        value=(body[pos//8]>>(7-pos%8))&1;pos+=1;return value
    out=[1 if h else -1 for h in hidden]
    offset=0
    for total in (5400,1350,1350):
        for start in range(0,total,16):
            indices=[i for i in range(offset+start,offset+min(start+16,total)) if not hidden[i]]
            tag=(bit()<<1)|bit()
            if not indices:
                if tag!=3:raise ValueError('empty group tag')
                continue
            if tag==3:raise ValueError('visible empty tag')
            if tag==0:values=[0]*len(indices)
            elif tag==1:values=[1]*len(indices)
            else:
                values=[bit() for _ in indices]
                if not any(values) or all(values):raise ValueError('noncanonical mixed group')
            for i,value in zip(indices,values):out[i]=2 if value else 0
        offset+=total
    left=len(body)*8-pos
    if left>=8 or any(bit() for _ in range(left)):raise ValueError('group trailing padding')
    if any(x not in (0,1,2) for x in out):raise ValueError('group coverage')
    return out


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def stat(values):return dict(min=min(values),median=statistics.median(values),max=max(values),total=sum(values))


def main():
    AREA.mkdir(parents=True,exist_ok=True)
    if (AREA/'results.json').exists():raise FileExistsError('retained map result exists')
    native=load('cu86_map_native',ROOT/'experiments/python-gamebub-v82/native/data.py')
    old=load('cu86_map_old',ROOT/'scripts/cu66-v84/prototype_mode_map_v2.py')
    rows=[];vectors={};tests=[];first_hidden=None
    for frame in native.iter_frames():
        hidden=frame['hidden_mask'];first_hidden=hidden if first_hidden is None else first_hidden
        modes=[1 if h else 0 if not frame['key'] and z else 2 for h,z in zip(hidden,frame['zero_coeff_mask'])]
        method,body=encode_body(modes,hidden,key=frame['key'])
        assert decode_body(method,body,hidden,key=frame['key'])==modes
        older=old.encode(modes,hidden,key=frame['key']);old_body=older[20:]
        assert len(body)<=len(old_body)
        # Exercise group syntax on each native map when it fits this profile,
        # even when another representation wins the byte comparison.
        grouped=_group_body(modes,hidden)
        if not frame['key'] and len(grouped)<=976:
            assert decode_body(3,grouped,hidden,key=False)==modes
        digest=hashlib.sha256(bytes(modes)).hexdigest()
        row=dict(cohort=frame['cohort'],ordinal=frame['ordinal'],fid=frame['fid'],key=frame['key'],method=method,
                 body_bytes=len(body),old_method=older[5],old_body_bytes=len(old_body),saved_bytes=len(old_body)-len(body),
                 group_candidate_bytes=len(grouped),modes_sha256=digest,body_sha256=hashlib.sha256(body).hexdigest())
        rows.append(row)
        if method not in vectors:
            vectors[method]=dict(name='native_method_'+str(method),cohort=frame['cohort'],fid=frame['fid'],key=frame['key'],method=method,body_hex=body.hex(),modes_sha256=digest)
        # Inherited bitset/RLE remain valid grammar choices even when group3
        # wins every native delta. Retain real native fallback vectors too.
        if older[5] not in vectors:
            assert decode_body(older[5],old_body,hidden,key=frame['key'])==modes
            vectors[older[5]]=dict(name='native_inherited_method_'+str(older[5]),cohort=frame['cohort'],fid=frame['fid'],key=frame['key'],method=older[5],body_hex=old_body.hex(),modes_sha256=digest)
    hidden=first_hidden
    baseline=[1 if h else 2 for h in hidden]
    # A compact valid group vector with one mixed group, independent of whether
    # selection on the corpus chooses that exact native pattern.
    synthetic=baseline.copy();visible=[i for i,h in enumerate(hidden) if not h];synthetic[visible[0]]=0
    grouped=_group_body(synthetic,hidden);assert len(grouped)<=976
    assert decode_body(3,grouped,hidden,key=False)==synthetic
    vectors.setdefault(3,dict(name='synthetic_group',key=False,method=3,body_hex=grouped.hex(),modes_sha256=hashlib.sha256(bytes(synthetic)).hexdigest()))
    def reject(name,fn):
        try:fn()
        except (ValueError,TypeError):tests.append(dict(name=name,status='PASS_REJECT'))
        else:raise AssertionError('accepted malformed '+name)
    reject('method',lambda:decode_body(4,b'',hidden,key=False))
    reject('bool_method',lambda:decode_body(True,b'',hidden,key=False))
    reject('key_method_delta',lambda:decode_body(0,b'',hidden,key=False))
    reject('nonempty_key',lambda:decode_body(0,b'\0',hidden,key=True))
    reject('other_method_key',lambda:decode_body(1,bytes(976),hidden,key=True))
    reject('body_bound',lambda:decode_body(3,bytes(977),hidden,key=False))
    reject('bitset_length',lambda:decode_body(1,bytes(975),hidden,key=False))
    reject('bitset_padding',lambda:decode_body(1,bytes(975)+b'\1',hidden,key=False))
    reject('RLE_short',lambda:decode_body(2,b'',hidden,key=False))
    reject('RLE_overrun',lambda:decode_body(2,b'\xff'*61,hidden,key=False))
    reject('group_empty',lambda:decode_body(3,b'',hidden,key=False))
    reject('group_truncated',lambda:decode_body(3,grouped[:-1],hidden,key=False))
    reject('group_extra_zero_byte',lambda:decode_body(3,grouped+b'\0',hidden,key=False))
    bad_mask=bytearray(hidden);bad_mask[0]^=1
    reject('fixed_mask',lambda:decode_body(1,bytes(976),bytes(bad_mask),key=False))
    reject('key_COPY',lambda:encode_body(synthetic,hidden,key=True))
    reject('hidden_wrong_mode',lambda:encode_body([2]*8100,hidden,key=False))
    # Mutate a known first visible group into an illegal empty tag, retaining
    # the full body so rejection is semantic rather than truncation.
    illegal=bytearray(_group_body(baseline,hidden));illegal[0]|=0xc0
    reject('visible_empty_tag',lambda:decode_body(3,bytes(illegal),hidden,key=False))
    # First group is visible; tag2 with all-one payload is noncanonical.
    bits=[1,0]+[1]*16
    bits += [0]*((-len(bits))%8)
    noncanonical=bytes(sum(bits[i+j]<<(7-j) for j in range(8)) for i in range(0,len(bits),8))
    reject('mixed_uniform',lambda:decode_body(3,noncanonical+bytes(127),hidden,key=False))
    # Additional deterministic mode patterns cover all-valid uniform and mixed
    # representations under independent decoding.
    for step in (1,2,3,7,16,31,64,127,256):
        pattern=[1 if h else int((i//step)%2)*2 for i,h in enumerate(hidden)]
        method,body=encode_body(pattern,hidden,key=False)
        assert decode_body(method,body,hidden,key=False)==pattern
        tests.append(dict(name='pattern_'+str(step),status='PASS'))
    (AREA/'frames.jsonl').write_text(''.join(json.dumps(r,separators=(',',':'))+'\n' for r in rows))
    (AREA/'vectors.json').write_text(json.dumps(dict(fixed_hidden_mask_sha256=MASK_SHA,vectors=list(vectors.values())),indent=2)+'\n')
    (AREA/'tests.json').write_text(json.dumps(dict(status='PASS',checks=len(tests),cases=tests),indent=2)+'\n')
    source_paths=[Path(__file__).resolve(),ROOT/'scripts/cu66-v84/prototype_mode_map_v2.py',ROOT/'experiments/python-gamebub-v82/native/index.json',ROOT/'experiments/python-gamebub-v82/native/data.py']
    result=dict(schema='cu66-v86-group-maps-v1',status='PASS',sources=len(rows),fixed_hidden_mask_sha256=MASK_SHA,
                source_sha256={str(p.relative_to(ROOT)):sha(p) for p in source_paths},
                method_counts={str(i):sum(r['method']==i for r in rows) for i in range(4)},body_bytes=stat([r['body_bytes'] for r in rows]),
                old_body_bytes=stat([r['old_body_bytes'] for r in rows]),saved_body_bytes=stat([r['saved_bytes'] for r in rows]),
                group_candidate_bytes=stat([r['group_candidate_bytes'] for r in rows]),checks=len(tests),vectors=len(vectors),
                body_limit=976,semantics='Exact fixed-profile modes. Raw bodies only; root CS86 header binds method and protects body with outer CRC.',
                scope='Actual metadata sizes, not full-frame bitrate or parser cycle/FPGA proof.',
                artifacts_sha256={p.name:sha(p) for p in AREA.iterdir() if p.is_file() and p.name!='results.json'})
    (AREA/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print('V86_MAPS_PASS',len(rows),len(tests),result['method_counts'],result['body_bytes'],result['saved_body_bytes'])


if __name__=='__main__':main()
