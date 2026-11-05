#!/usr/bin/env python3
"""Export bit-exact entropy fixtures from frozen AB38 syntax and native-v69 data."""
from pathlib import Path
import hashlib,importlib.util,json,struct,zlib,os
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def module(n,p):
 s=importlib.util.spec_from_file_location(n,p);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
encoder=module('entropy69_frozen_encoder',ROOT/'experiments/python-game-binary-v38-study/model.py')
decoder=module('entropy69_frozen_independent_decoder',ROOT/'experiments/python-game-binary-v38-study/decoder.py')
NATIVE=ROOT/'experiments/cu66-native-v69';OUT=HERE/'fixtures'
def sha(data):return hashlib.sha256(data).hexdigest()
def save(data,ext):
 p=OUT/(sha(data)+ext);p.write_bytes(data);return p

def forced(a,bw,raw=False):
 if raw:
  payload=a.astype('<i2').tobytes();return encoder.seal(encoder.HEADER.pack(b'AB38',1,1,len(a),bw,0,len(payload),0,0,0,0,0,0)+payload)
 zig=a.reshape(-1,64)[:,encoder.ZIGZAG].astype(np.int32);dc=zig[:,0].copy();dc[1:]-=zig[:-1,0];dc[::bw]=zig[::bw,0];dc=encoder.mapped(dc)
 c=encoder.BinaryEncoder()
 for x in dc:c.rice(x,0,14,0)
 body,bits=c.finish();streams=[encoder.STREAM.pack(0,255,bits)+body];counts=[]
 for lo,hi in encoder.BANDS:
  seq=zig[:,lo:hi].reshape(-1);idx=np.flatnonzero(seq);counts.append(len(idx));c=encoder.BinaryEncoder()
  for run,level in zip(np.diff(np.r_[-1,idx])-1,encoder.mapped(seq[idx])-1,strict=True):c.rice(run,0,24,0);c.rice(level,0,12,1)
  body,bits=c.finish();streams.append(encoder.STREAM.pack(0,0,bits)+body)
 return encoder.seal(encoder.HEADER.pack(b'AB38',1,0,len(a),bw,0,*map(len,streams),*counts)+b''.join(streams))

def main():
 OUT.mkdir(parents=True,exist_ok=True);directed=[];rng=np.random.default_rng(6901)
 def add(name,packet,blocks,bw,dispatch=5,expected=None,error=False):
  if error:
   try:decoder.decode(packet,blocks,bw)
   except ValueError:pass
   else:
    assert dispatch not in(5,6)or(dispatch==6 and bw!=1),'malformed accepted by independent Python decoder'
   ep='-'
  else:
   actual=decoder.decode(packet,blocks,bw)
   if expected is not None:np.testing.assert_array_equal(actual,expected)
   ep=os.path.relpath(save(zlib.compress(actual.astype('<i2').tobytes(),9),'.coeff.zlib'),HERE)
  pp=save(packet,'.ab38');directed.append((name,os.path.relpath(pp,HERE),ep,str(blocks),str(bw),str(dispatch),'1'if error else'0'))
  return packet
 a=np.zeros((8,8,8),np.int16);zero=add('zero_8',forced(a,4),8,4,expected=a)
 a=np.zeros((12,8,8),np.int16);a[:,0,0]=np.tile([-2048,2048,0],4);add('DC_row_reset_extremes',forced(a,3),12,3,expected=a)
 a=np.zeros((64,8,8),np.int16);a[0,0,0]=-2048;a[1,0,0]=2048;a[30,7,7]=2048;a[40,2,1]=-2048;a[63,4,3]=-1;add('forced_rice_escapes',forced(a,8),64,8,expected=a)
 a=rng.integers(-31,32,(64,8,8),dtype=np.int16);a[rng.random(a.shape)<.91]=0;packet,_=encoder.encode(a,8);add('sparse_seed6901',packet,64,8,expected=a)
 a=rng.integers(-2048,2049,(8,8,8),dtype=np.int16);raw=add('raw_signed_extremes',forced(a,4,True),8,4,expected=a)
 a=np.zeros((32,8,8),np.int16);a[:,0,0]=np.arange(32)-16;add('compact_bw1',forced(a,1),32,1,dispatch=6,expected=a)
 def edit(packet,offset,value,reseal=True):
  b=bytearray(packet[:-4]);b[offset]=value;return encoder.seal(bytes(b))if reseal else bytes(b)+packet[-4:]
 add('bad_crc',edit(zero,50,zero[50]^1,False),8,4,error=True)
 add('bad_magic_resealed',edit(zero,0,0),8,4,error=True)
 add('bad_version_resealed',edit(zero,4,2),8,4,error=True)
 add('bad_flags_resealed',edit(zero,5,2),8,4,error=True)
 add('bad_header_geometry',edit(zero,6,7),8,4,error=True)
 add('bad_requested_geometry',zero,9,3,error=True)
 add('unsupported_dispatch4',zero,8,4,dispatch=4,error=True)
 add('compact_requires_bw1',zero,8,4,dispatch=6,error=True)
 add('bad_dc_k',edit(zero,42,14),8,4,error=True)
 add('bad_dc_reserved',edit(zero,43,0),8,4,error=True)
 fields=encoder.HEADER.unpack_from(zero);off=42+fields[6]
 add('bad_run_k',edit(zero,off,20),8,4,error=True)
 add('bad_level_k',edit(zero,off+1,12),8,4,error=True)
 # Last low padding bit is outside the explicitly declared bit length.
 dc_bits=struct.unpack_from('<I',zero,44)[0];last=42+fields[6]-1
 if dc_bits%8:add('bad_padding_resealed',edit(zero,last,zero[last]|1),8,4,error=True)
 # A declared termination bit must be zero even with correct padding and CRC.
 body_start=48;bit=dc_bits-1;pos=body_start+bit//8
 add('bad_termination_resealed',edit(zero,pos,zero[pos]|(1<<(7-bit%8))),8,4,error=True)
 b=bytearray(raw[:-4]);b[42:44]=struct.pack('<h',2049);add('bad_raw_range',encoder.seal(bytes(b)),8,4,error=True)
 # Every unsupported dispatch is explicit, not silently interpreted as AB38.
 for dispatch in(0,1,2,3,7):add('unsupported_dispatch'+str(dispatch),zero,8,4,dispatch=dispatch,error=True)
 for blocks,bw,name in((0,1,'zero_blocks'),(8101,1,'too_many_blocks'),(8,0,'zero_width'),(8,257,'too_wide'),(8,3,'nondivisible')):
  add('bad_config_'+name,zero,blocks,bw,error=True)
 # Seeded coefficient generation and payload mutations are qualified against the
 # independent frozen decoder, never assumed to reject merely because mutated.
 directed_count=len(directed);stress=[]
 for seed in(69011,69012,69013):
  rr=np.random.default_rng(seed)
  for index in range(24):
   count=int(rr.choice((1,2,3,4,8,12,16,32,64)))
   width=int(rr.choice([v for v in range(1,min(count,90)+1)if count%v==0]))
   radius=int(rr.choice((3,31,255,2048)));a=rr.integers(-radius,radius+1,(count,8,8),dtype=np.int16)
   a[rr.random(a.shape)<float(rr.choice((0,.5,.9,.99,1)))]=0
   pp,_=encoder.encode(a,width);start=len(directed);add('random_coeff_'+str(seed)+'_'+str(index),pp,count,width,expected=a);stress.extend(directed[start:]);del directed[start:]
 # Mutate a small sparse arithmetic stream, reseal CRC, preserve all outcomes.
 sample=np.zeros((32,8,8),np.int16);sample[:,0,0]=np.arange(32)-16;sample[20,7,7]=-31;pp=forced(sample,8)
 rr=np.random.default_rng(69021)
 for index in range(48):
  bad=bytearray(pp[:-4]);offset=int(rr.integers(42,len(bad)));bad[offset]^=1<<int(rr.integers(0,8));bad=encoder.seal(bytes(bad));start=len(directed)
  try:out=decoder.decode(bad,32,8)
  except ValueError:add('mutated_resealed_'+str(index),bad,32,8,error=True)
  else:add('mutated_valid_'+str(index),bad,32,8,expected=out)
  stress.extend(directed[start:]);del directed[start:]
 (HERE/'stress.tsv').write_text('\n'.join('\t'.join(r)for r in stress)+'\n')
 (HERE/'directed.tsv').write_text('\n'.join('\t'.join(r)for r in directed)+'\n')
 native=json.loads((NATIVE/'manifest.json').read_text());rows=[];pins={str((ROOT/'experiments/python-game-binary-v38-study'/p).relative_to(ROOT)):sha((ROOT/'experiments/python-game-binary-v38-study'/p).read_bytes())for p in('model.py','decoder.py')}
 pins[str((NATIVE/'manifest.json').relative_to(ROOT))]=sha((NATIVE/'manifest.json').read_bytes())
 for c in native['cases']:
  for row in c['rows']:
   for p in row['planes']:
    packet=(NATIVE/p['packet']['path']).read_bytes();stored=(NATIVE/p['expected_coefficients']['path']).read_bytes();expected=zlib.decompress(stored)
    assert sha(packet)==p['packet']['sha256']and sha(stored)==p['expected_coefficients']['sha256']and sha(expected)==p['expected_coefficients_raw_sha256']
    actual=decoder.decode(packet,p['blocks'],p['blocks_w']);assert actual.astype('<i2').tobytes()==expected
    rows.append((c['scene']+'_'+str(row['id'])+'_'+str(p['axis']),os.path.relpath(NATIVE/p['packet']['path'],HERE),os.path.relpath(NATIVE/p['expected_coefficients']['path'],HERE),str(p['blocks']),str(p['blocks_w']),str(p['dispatch']),'0'))
 (HERE/'actual.tsv').write_text('\n'.join('\t'.join(r)for r in rows)+'\n')
 (HERE/'smoke.tsv').write_text('\n'.join('\t'.join(r)for r in directed+rows[:24])+'\n')
 (HERE/'fixture-evidence.json').write_text(json.dumps(dict(schema='cu66-entropy-v69-fixtures',directed_cases=len(directed),stress_cases=len(stress),actual_planes=len(rows),source_sha256=pins,directed_vectors_seed=6901,no_new_game_captures=True),indent=2)+'\n')
 print(json.dumps(dict(directed_cases=len(directed),stress_cases=len(stress),actual_planes=len(rows))))
if __name__=='__main__':main()
