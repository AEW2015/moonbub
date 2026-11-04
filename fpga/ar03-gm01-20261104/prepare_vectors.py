"""Actual pinned AR03 _inner oracle, retained GM01 packets and scoped negatives."""
import argparse,hashlib,json,struct,sys,zlib,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args()
ROOT=a.source.resolve();OUT=Path(__file__).resolve().parent
COMMIT='27a4dde6a7e2ea4fab09d892551ef542f05c8965'
sha=lambda b:hashlib.sha256(b).hexdigest()
def bind(rel):
 raw=(ROOT/rel).read_bytes();assert raw==subprocess.check_output(['git','-C',str(ROOT),'show',COMMIT+':'+rel]),rel
 return sha(raw)
assert subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()==COMMIT
initial={r:bind(r)for r in ['experiments/python-game-local-refresh-study/local_codec.py','experiments/python-game-codec-study/game_codec.py','experiments/python-game-roi-study/roi_codec.py','experiments/python-game-mandatory-hud-study/results.json']}
assert sys.dont_write_bytecode and sys.pycache_prefix,'Use -B -X pycache_prefix=<initially absent isolated path>'
assert not Path(sys.pycache_prefix).exists(),'Fresh prefix must be absent (no inherited bytecode)'
sys.path.insert(0,str(ROOT/'experiments/python-game-local-refresh-study'))
import local_codec as oracle
import numpy as np
gm=oracle.gm;H=gm.HEADER;assert H.size==46 and gm.word_coeff.PAYLOAD_OVERHEAD==26
CASES=[]
def seal(b):return b[:-4]+struct.pack('<I',zlib.crc32(b[:-4]))
def scope(b,expected):
 if not 50<=len(b)<=49152:raise ValueError('bounded inner size')
 if b[:4]!=b'GM01':raise ValueError('unsupported dispatch')
 m=oracle._inner(b,expected[0],False)
 if (m['frame_id'],m['reference_id'],m['key'])!=expected[1:]:raise ValueError('outer crossidentity')
 return m
def add(name,b,accept,expected=None,total=None,skip=False,early=False,native=False):
 f=H.unpack_from(b)if len(b)>=46 else None
 if expected is None:expected=(f[3],f[4],f[5],bool(f[2]&1))
 try:scope(b,expected);ok=True;err=None
 except(ValueError,struct.error,IndexError)as e:ok=False;err=str(e)
 assert ok==accept,(name,ok,accept,err)
 try:oracle._inner(b,expected[0],False);oracle_ok=True
 except(ValueError,struct.error,IndexError):oracle_ok=False
 full_ok=None;full_error=None
 if accept:
  try:gm.parse(b,expected[0]);full_ok=True
  except(ValueError,struct.error,IndexError)as e:full_ok=False;full_error=str(e)
 nmap=f[12]if f else 0
 row=dict(id=len(CASES),name=name,bytes=len(b),sha256=sha(b),expected=bool(accept and not early and not skip),scope_expected=accept,oracle_inner_decode_false=oracle_ok,gm_parse=full_ok,gm_parse_error=full_error,error=err,identity=list(expected),total=len(b)if total is None else total,skip=skip,early=early,native=native,fields=list(f[:1])+list(f[1:])if f else None)
 if f:row['fields'][0]=f[0].decode(errors='replace')
 if accept:
  w,h=f[6:8];mapped=b[46:46+nmap];scales=gm.roi.unpack_map(mapped,f[10],f[11]);row['scale_map']=scales.reshape(-1).tolist()
 CASES.append((row,b));return b
manifest_path=ROOT/'experiments/python-game-mandatory-hud-study/results.json';manifest=json.loads(manifest_path.read_text());native_all=[];sr_count=0
for ci,c in enumerate(manifest['cases']):
 for v in c['vectors']:
  d=v['packet'];stored=(manifest_path.parent/d['path']).read_bytes();b=zlib.decompress(stored)
  assert sha(stored)==d['stored_sha256']and sha(b)==d['raw_sha256']and len(b)==d['raw_bytes']
  outer=oracle.HEADER.unpack_from(b);inner=b[61:61+outer[10]]
  if inner[:4]==b'GM01':native_all.append(add(f'native-{ci}-{v["id"]}',inner,True,native=True))
  else:sr_count+=1;add(f'unsupported-native-SR01-{ci}-{v["id"]}',inner,False)
assert native_all
def synthetic(w,h,epoch=1,frame=0,key=True):
 mw,mh=gm.roi.geometry(w,h);scales=np.resize(np.array([8,16,32],np.uint8),mw*mh).reshape(mh,mw)
 payloads=[]
 for pw,ph in [(w,h),(w//2,h//2),(w//2,h//2)]:
  bw,bh=(pw+7)//8,(ph+7)//8;payloads.append(gm.token_coeff.encode_coefficients(np.zeros((bw*bh,8,8),np.int16),bw))
 mapped=gm.roi.pack_map(scales)
 body=H.pack(b'GM01',1,int(key),epoch,frame,0xffffffff if key else frame-1,w,h,0,0,mw,mh,len(mapped),*[len(x)for x in payloads])+mapped+b''.join(payloads)
 return body+struct.pack('<I',zlib.crc32(body))
small=add('synthetic-2x2-padding',synthetic(2,2),True)
odd=add('synthetic-34x18-padding-and-block-edges',synthetic(34,18),True)
add('synthetic-2048x168-near-area-max',synthetic(2048,168),True)
add('synthetic-168x2048-tall',synthetic(168,2048),True)
add('epoch-zero',synthetic(18,18,epoch=0),True)
add('frame-max-minus-one',synthetic(18,18,frame=0xfffffffe),True)
add('delta-reference-max-minus-two',synthetic(18,18,frame=0xfffffffe,key=False),True)
base=native_all[0]
def mutation(name,b,at,data,accept=False,reseal=True,expected=None):
 x=bytearray(b);x[at:at+len(data)]=data;return add(name,seal(bytes(x))if reseal else bytes(x),accept,expected=expected)
for name,at,data in [('magic',0,b'BAD!'),('version',4,b'\x02'),('flags',5,b'\x03'),('epoch-sentinel',6,b'\xff'*4),('frame-sentinel',10,b'\xff'*4),('width-zero',18,b'\0\0'),('width-odd',18,b'\x03\0'),('width-too-large',18,struct.pack('<H',2050)),('height-zero',20,b'\0\0'),('area-too-large',20,struct.pack('<H',2048)),('AR03-dx-nonzero',22,b'\x02\0'),('AR03-dy-negative',24,b'\xfe\xff'),('map-width',26,b'\0\0'),('map-height',28,b'\0\0'),('map-byte-overflow',30,b'\xff'*4),('plane-length-small',34,struct.pack('<I',25)),('plane-length-overflow',38,b'\xff'*4)]:mutation(name,base,at,data)
mutation('unsupported-SR01',base,0,b'SR01')
mutation('map-code-three',small,46,b'\xc0')
mutation('map-padding-nonzero',small,46,b'\x01')
mutation('second-padding-nonzero',odd,47,bytes([odd[47]|1]))
mutation('inner-crc-corrupt',base,len(base)-1,bytes([base[-1]^1]),reseal=False)
add('inner-truncated',base[:-1],False)
add('inner-extra-trailer-byte',base+b'\0',False)
f=H.unpack_from(base);expect=(f[3],f[4],f[5],bool(f[2]))
add('outer-frame-crossidentity',base,False,expected=(expect[0],expect[1]+1,expect[2],expect[3]))
add('outer-epoch-crossidentity',base,False,expected=(expect[0]+1,*expect[1:]))
add('outer-reference-crossidentity',base,False,expected=(expect[0],expect[1],expect[2]^1,expect[3]))
add('outer-key-crossidentity',base,False,expected=(*expect[:3],not expect[3]))
mutation('key-reference-not-sentinel',small,14,bytes(4))
delta=synthetic(18,18,frame=4,key=False);mutation('delta-reference-not-older',delta,14,struct.pack('<I',4))
# The preceding certificate accepts the bad-innerCRC packet if its outerCRC is recomputed.
outer=next(zlib.decompress((manifest_path.parent/v['packet']['path']).read_bytes())for c in manifest['cases']for v in c['vectors']if zlib.decompress((manifest_path.parent/v['packet']['path']).read_bytes())[61:65]==b'GM01')
of=oracle.HEADER.unpack_from(outer);bad=bytearray(outer);bad[61+of[10]-1]^=1;bad=seal(bytes(bad));assert zlib.crc32(bad[:-4])==struct.unpack('<I',bad[-4:])[0]
(OUT/'outer-valid-inner-crc-invalid.ar03').write_bytes(bad)
add('outer-valid-inner-crc-invalid',bad[61:61+of[10]],False)
# This layer does not validate CP02; corrupt CP02 CRC and repair inner CRC.
f=H.unpack_from(small);pos=46+f[12]+f[13]-1
badcp=mutation('scope-CP02-crc-downstream',small,pos,bytes([small[pos]^1]),True)
assert CASES[-1][0]['gm_parse']is False
assert CASES[-1][0]['gm_parse_error']=='coefficient CRC'
add('early-last',base[:-1],False,total=len(base),early=True)
add('start-over-cap',small,True,total=49153,skip=True)
add('start-under-min',small,True,total=49,skip=True)
rows=[]
with(OUT/'vectors.hex').open('w')as out:
 for row,b in CASES:
  e=row['identity'];out.write(' '.join(f'{int(x):x}'for x in [row['total'],len(b),row['expected'],*e,row['skip']])+'\n')
  out.write(' '.join(f'{x:02x}'for x in b)+'\n');rows.append(row)
imported={}
for module in tuple(sys.modules.values()):
 fn=getattr(module,'__file__',None)
 if not fn:continue
 path=Path(fn).resolve()
 try:rel=path.relative_to(ROOT).as_posix()
 except ValueError:continue
 if path.suffix=='.py':imported[rel]=bind(rel)
assert not Path(sys.pycache_prefix).exists()
import av,PIL
env=dict(interpreter=sys.executable,python=sys.version,pycache_prefix=sys.pycache_prefix,dont_write_bytecode=sys.dont_write_bytecode,fresh_prefix_created=False,imports={name:dict(version=m.__version__,path=str(Path(m.__file__).resolve()))for name,m in [('numpy',np),('Pillow',PIL),('av',av)]})
(OUT/'python-environment.json').write_text(json.dumps(env,indent=2)+'\n')
native_repo=Path('C:/Users/lavat/codex/sunshine-gamebub-dxgi-work');nc='c9c0bf4bcbe5c95f38b50bf6e190b84822886d53';native={}
for name in ['body_decoder.h','inner_encoder.h','v20.h','conformance.cpp']:
 raw=subprocess.check_output(['git','-C',str(native_repo),'show',nc+':tools/gamebub/native/'+name]);native[name]=dict(commit=nc,git_path='tools/gamebub/native/'+name,sha256=sha(raw))
report=dict(schema='gm01-section-vectors-v1',source_commit=COMMIT,initial_bindings=initial,imported_repo_sources=imported,native_review=native,native_GM01=len(native_all),unsupported_native_SR01=sr_count,cases=rows,inputs_sha256=sha((OUT/'vectors.hex').read_bytes()))
(OUT/'vectors.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(cases=len(rows),native_GM01=len(native_all),unsupported_native_SR01=sr_count,certified=sum(r['expected']for r in rows),inputs_sha256=report['inputs_sha256']),indent=2))
