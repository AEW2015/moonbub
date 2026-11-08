from pathlib import Path
import sys,importlib.util,json,hashlib,struct,zlib
sys.dont_write_bytecode=True
import numpy as np
P=Path(__file__).resolve().parent;D=Path('C:/moon/dev/experiments/cu66-source-bridge-20261108/dependencies');out=P/'stream04';out.mkdir(exist_ok=False)
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
baseline=load('baseline',D/'python-game-hud-runs-v33-study/baseline.py');hs32=baseline.old;h=baseline.h;dec33=load('decoder',D/'python-game-hud-runs-v33-study/decoder.py');hs33=load('v58_hs33_stream',D/'python-game-hud-runs-v33-study/model.py');sha=lambda b:hashlib.sha256(b).hexdigest();pins={str(Path(m.__file__).resolve()):sha(Path(m.__file__).read_bytes())for m in list(sys.modules.values())if getattr(m,'__file__',None)and str(Path(m.__file__).resolve()).lower().startswith(str(D).lower())and Path(m.__file__).suffix=='.py'};rows=[];meta=[]
def decode(packet,ref):return h.decode(packet,ref)if packet[:4]==b'HD25'else hs32._decode_patch(packet,ref)if packet[:4]==b'HS32'else dec33.decode_patch(packet,ref)
def add(name,packet,ref,w,hh,current=None,target=''):
 error=None
 try:a=decode(packet,ref)
 except ValueError as e:error=str(e)
 if current is None:assert error is not None,(name,'unexpected Pythonaccept')
 else:assert error is None and np.array_equal(a,current),(name,error)
 pn=name+'.packet';rn=name+'.reference.u16'if ref is not None else'-';en=name+'.expected.u16'if current is not None else'-';(out/pn).write_bytes(packet)
 if ref is not None:(out/rn).write_bytes(ref.astype('<u2').tobytes())
 if current is not None:(out/en).write_bytes(current.astype('<u2').tobytes())
 rows.append([name,pn,rn,en,str(w),str(hh),'1'if current is not None else'0']);meta.append({'name':name,'target':target,'python_rejection':error,'packet_sha256':sha(packet),'observed_magic':packet[:4].decode(),'observed_mode':packet[5],'w':w,'h':hh})
def hd(mode,a,ref,body):return h._pack(mode,a,h.ZERO if ref is None else h._tag(ref),body)
def repayload(packet,body):
 hdr=list(h.HEADER.unpack_from(packet));hdr[5]=len(body);b=h.HEADER.pack(*hdr)+body;return b+struct.pack('<I',zlib.crc32(b))
def reseal(b):return b+struct.pack('<I',zlib.crc32(b))
for value,label in[(0,'zero-run'),(0x1234,'nonzero-repeat')]:
 a=np.full((8,16),value,np.uint16);add('planes-'+label,hd(6,a,None,h._planes_encode(a)),None,16,8,a,'HD25 RLE '+label)
a=np.arange(128,dtype=np.uint16).reshape(8,16)*257;add('planes-literals',hd(6,a,None,h._planes_encode(a)),None,16,8,a,'HD25 literal tokens')
# Small multicode HS32 with non-byte-aligned actual Huffman data.
w,hh=13,7;y,x=np.indices((hh,w));ref=np.full((hh,w),(10<<11)|(20<<5)|10,np.uint16);delta=x%3;a=(((10+delta).astype(np.uint16)<<11)|((20+delta).astype(np.uint16)<<5)|(10+delta).astype(np.uint16));payload,_=hs32._encode_patch(a,ref,1);packet=hs32._pack_patch(a,ref,1,payload);add('hs32-stream-control',packet,ref,w,hh,a,'small nonconstant Huffman')
ns,nb=hs32.STREAM.unpack_from(payload);assert ns>=3 and nb%8;tail=hs32.STREAM.size+2*ns+(nb+7)//8-1;bad=bytearray(payload);bad[tail]|=1;add('hs32-huffman-padding',repayload(packet,bytes(bad)),ref,w,hh,target='nonzero Huffman pad')
bad=bytearray(payload)
for i in range(ns):bad[hs32.STREAM.size+2*i+1]=1
add('hs32-huffman-oversubscribed',repayload(packet,bytes(bad)),ref,w,hh,target='canonical table oversubscription')
add('hs32-huffman-truncated',repayload(packet,payload[:-1]),ref,w,hh,target='truncated channel bits')
# Constant Huffman stream must have zero coded bits.
p1,_=hs32._huff_encode(np.full(w*hh,2,np.uint16));body=p1+p1+p1;constant=hs32._pack_patch(ref,ref,1,body);bad=bytearray(body);struct.pack_into('<I',bad,2,1);bad[8:8]=b'\0';add('hs32-constant-has-bits',repayload(constant,bytes(bad)),ref,w,hh,target='constant Huffman coded-bit count')
# Component range failure after streaming signed zigzag; syntactically legal Huffman.
r0=np.zeros((hh,w),np.uint16);neg,_=hs32._huff_encode(np.ones(w*hh,np.uint16));add('hs32-negative-component',hs32._pack_patch(r0,r0,1,neg*3),r0,w,hh,target='reconstructed component below zero')
# HS33 exact zero run, then padding/run expansion/nonzero-symbol controls.
w,hh=16,8;ref=np.full((hh,w),(10<<11)|(20<<5)|10,np.uint16);payload,work=hs33._encode_patch(ref,ref,1);assert all(v['selected']['scheme']==1 for v in work);packet=hs33._pack_patch(ref,ref,1,payload);add('hs33-zero-run-control',packet,ref,w,hh,ref,'scheme1 empty symbol expansion')
scheme,k,events,size,nb=hs33.CHANNEL.unpack_from(payload);assert scheme==1 and events==size==0 and nb%8;tail=hs33.CHANNEL.size+size+(nb+7)//8-1;bad=bytearray(payload);bad[tail]|=1;add('hs33-rice-run-padding',repayload(packet,bytes(bad)),ref,w,hh,target='nonzero run Rice padding')
_,nextpos=dec33.decode_channel(payload,0,w*hh,62);suffix=payload[nextpos:]
def channel(scheme,symbols,runs):
 stream,_=hs32._huff_encode(np.asarray(symbols,np.uint16))if len(symbols)else(b'',{})
 k,nb,bits=hs33._rice_encode(np.asarray(runs,np.int64));return hs33.CHANNEL.pack(scheme,k,len(symbols),len(stream),nb)+stream+bits
add('hs33-zero-run-overflow',repayload(packet,channel(1,[],[w*hh+1])+suffix),ref,w,hh,target='run exceeds remaining count')
add('hs33-zero-run-zero-symbol',repayload(packet,channel(1,[0],[0,w*hh-1])+suffix),ref,w,hh,target='zero forbidden as explicit nonzero event')
add('hs33-repeat-adjacent-equal',repayload(packet,channel(2,[2,2],[63,63])+suffix),ref,w,hh,target='adjacent equal repeat symbols forbidden')
# HD25 component Rice: stream padding and range, using frozen encoder output.
w,hh=13,7;y,x=np.indices((hh,w));ref=np.full((hh,w),(10<<11)|(20<<5)|10,np.uint16);a=ref.copy();a[1,2]^=1;payload=h._rice_encode(a,ref);packet=hd(8,a,ref,payload);add('hd25-rice-control',packet,ref,w,hh,a,'component Rice signed residual')
kscounts=h.RICE.unpack_from(payload);counts=kscounts[3:];pos=h.RICE.size
for channel_id,n in enumerate(counts):
 if n%8:
  bad=bytearray(payload);bad[pos+(n+7)//8-1]|=1;add('hd25-rice-padding',repayload(packet,bytes(bad)),ref,w,hh,target='nonzero component Rice padding');break
 pos+=(n+7)//8
else:raise AssertionError('need actual nonaligned Rice stream')
r0=np.zeros((hh,w),np.uint16);fake=np.full((hh,w),(1<<11)|(1<<5)|1,np.uint16);add('hd25-rice-negative-component',hd(8,r0,r0,h._rice_encode(r0,fake)),r0,w,hh,target='component range before output')
# RLE tokens deliberately malformed using the source-defined token classes.
for name,lo,target in[('short-literal',b'\x7f\x01','literal data truncated'),('run-overflow',b'\xbf\xbf','zero run exceeds91words'),('repeat-zero',b'\xff\0','nonzero repeat carries zero')]:
 hi=h.rle_encode(bytes(w*hh));body=h.LENGTHS.pack(len(lo),len(hi))+lo+hi;add('hd25-rle-'+name,hd(6,r0,None,body),None,w,hh,target=target)
# One tag/reference control each; preserve repaired framing/CRC for semantic errors.
body=bytearray(packet[:-4]);body[30]^=1;add('output-tag-mismatch',reseal(bytes(body)),ref,w,hh,target='decoded output tag mismatch')
wrong=ref.copy();wrong[0,0]^=1;add('reference-tag-mismatch',packet,wrong,w,hh,target='exact reference tag')
# Invalid motion field/range controls directly mutate existing legal packet prefixes.
pos=P/'positive03';base=(pos/'hd25-mode4-grammar0.packet').read_bytes();refm=np.fromfile(pos/'hd25-mode4-grammar0.reference.u16',dtype='<u2').reshape(8,16);body=bytearray(base[h.HEADER.size:-4]);body[0]=5;add('motion-global-range',repayload(base,bytes(body)),refm,16,8,target='motion vector beyondradius4')
base=(pos/'hd25-mode5-grammar0.packet').read_bytes();refm=np.fromfile(pos/'hd25-mode5-grammar0.reference.u16',dtype='<u2').reshape(16,64);body=bytearray(base[h.HEADER.size:-4]);struct.pack_into('<H',body,h.TILE.size+4,0);add('motion-zero-run',repayload(base,bytes(body)),refm,64,16,target='motion run lengthzero')
(out/'index.tsv').write_text(''.join('\t'.join(r)+'\n'for r in rows),newline='\n');(out/'cases.json').write_text(json.dumps(meta,indent=2)+'\n');assert all(sha(Path(n).read_bytes())==v for n,v in pins.items());(out/'MANIFEST.json').write_text(json.dumps({'status':'PYTHON_REFERENCE_POSITIVES_AND_TARGETED_NEGATIVES_PASS_OLD_NATIVE_PENDING','cases':len(rows),'positives':sum(r[-1]=='1'for r in rows),'negatives':sum(r[-1]=='0'for r in rows),'source_dependencies':pins,'files':{f.name:sha(f.read_bytes())for f in out.iterdir()if f.is_file()}},indent=2)+'\n');print('STREAM_CASES',len(rows),'positive',sum(r[-1]=='1'for r in rows),'negative',sum(r[-1]=='0'for r in rows),flush=True)
