from pathlib import Path
import sys,importlib.util,json,hashlib,struct,zlib,shutil
sys.dont_write_bytecode=True
import numpy as np
P=Path(__file__).resolve().parent;D=Path('C:/moon/dev/experiments/cu66-source-bridge-20261108/dependencies');out=P/'positive03';out.mkdir(exist_ok=False)
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
baseline=load('baseline',D/'python-game-hud-runs-v33-study/baseline.py');hs32=baseline.old;h=baseline.h
dec33=load('decoder',D/'python-game-hud-runs-v33-study/decoder.py');hs33=load('v58_hs33',D/'python-game-hud-runs-v33-study/model.py')
sha=lambda b:hashlib.sha256(b).hexdigest();src={str(Path(m.__file__).resolve()):sha(Path(m.__file__).read_bytes())for m in list(sys.modules.values())if getattr(m,'__file__',None)and str(Path(m.__file__).resolve()).lower().startswith(str(D).lower())and Path(m.__file__).suffix=='.py'}
(P/'dependency-bindings.json').write_text(json.dumps(src,indent=2)+'\n');rows=[];metadata=[]
def words(w,hh,style='pattern'):
 y,x=np.indices((hh,w));return (((x+y)%21+3).astype(np.uint16)<<11)|(((2*x+y)%41+9).astype(np.uint16)<<5)|((x+2*y)%21+3).astype(np.uint16)
def add(name,packet,ref,current,details=None):
 mode=packet[5];magic=packet[:4].decode();w,hh=current.shape[1],current.shape[0]
 decoded=h.decode(packet,ref)if magic=='HD25'else hs32._decode_patch(packet,ref)if magic=='HS32'else dec33.decode_patch(packet,ref)
 assert np.array_equal(decoded,current),(name,'reference roundtrip')
 pn=name+'.packet';en=name+'.expected.u16';rn=name+'.reference.u16'if ref is not None else'-';(out/pn).write_bytes(packet);(out/en).write_bytes(current.astype('<u2').tobytes())
 if ref is not None:(out/rn).write_bytes(ref.astype('<u2').tobytes())
 rows.append([name,pn,rn,en,str(w),str(hh),'1']);metadata.append({'name':name,'magic':magic,'observed_mode':mode,'w':w,'h':hh,'packet_sha256':sha(packet),'expected_sha256':sha(current.astype('<u2').tobytes()),**(details or{})})
def prefix(ref,plain,tiledfield=0):
 if plain==1:return ref,b''
 if plain==2:
  b=struct.pack('<bb',1,-1);return h.predict(ref,1,-1),b
 hh,w=ref.shape;count=((w+15)//16)*((hh+7)//8)
 vec=[(1,-1)]*count if tiledfield else[(i%3-1,(i//3)%3-1)for i in range(count)]
 field,v=h._vector_bytes(vec);assert field==tiledfield,(field,tiledfield,count)
 b=h.TILE.pack(h.TW,h.TH,h.RADIUS,field,count)+struct.pack('<I',len(v))+v
 return hs32._motion_reference(ref,3,b,w,hh)[0],b
ref=words(16,8);cur=ref.copy();cur[1,2]^=3;cur[5,9]^=1
for mode in range(10):
 r=None if mode in[0,6,7,9]else ref
 if mode==0:payload=cur.astype('<u2').tobytes();a=cur
 elif mode==1:payload=b'';a=ref
 elif mode==2:payload=h._span_encode(cur^ref);a=cur
 elif mode==3:payload=h._planes_encode(cur^ref);a=cur
 elif mode in[4,5]:continue
 elif mode==6:payload=h._planes_encode(cur);a=cur
 elif mode==7:
  a=cur;left=a.copy();left[:,1:]^=a[:,:-1];payload=h._planes_encode(left)
 elif mode==8:payload=h._rice_encode(cur,ref);a=cur
 elif mode==9:payload=h._rice_encode(cur,left=True);a=cur
 packet=h._pack(mode,a,h.ZERO if r is None else h._tag(r),payload);assert packet[5]==mode;add('hd25-mode'+str(mode),packet,r,a)
for mode in[4,5]:
 for grammar in[0,1,2]:
  ref=words(64,16)if mode==5 else words(16,8);pred,pre=prefix(ref,2 if mode==4 else 3,1 if mode==5 else 0);a=pred.copy();a[1,2]^=1
  body=h._span_encode(a^pred)if grammar==0 else h._planes_encode(a^pred)if grammar==1 else h._rice_encode(a,pred)
  packet=h._pack(mode,a,h._tag(ref),pre+bytes([grammar])+body);add('hd25-mode'+str(mode)+'-grammar'+str(grammar),packet,ref,a,{'residual_grammar':grammar,'vector_field':1 if mode==5 else None})
# Explicit raw-vector tiled variant, using exactly the frozen prefix/prediction grammar.
ref=words(64,16);pred,pre=prefix(ref,3,0);add('hd25-mode5-raw-vectors',h._pack(5,pred,h._tag(ref),pre+b'\0'+h._span_encode(pred^pred)),ref,pred,{'residual_grammar':0,'vector_field':0})
for magic,enc in[('HS32',hs32),('HS33',hs33)]:
 for mode in[0,1,2,3,9,10,11]:
  ref=words(64,16);plain=mode&7;pred,pre=(None,b'')if plain==0 else prefix(ref,plain,1 if plain==3 else 0);a=words(64,16)if pred is None else pred.copy();a[1,2]^=1
  payload,work=enc._encode_patch(a,pred,mode,pre);packet=enc._pack_patch(a,ref,mode,payload);assert packet[5]==mode
  add(magic.lower()+'-mode'+str(mode),packet,None if plain==0 else ref,a,{'channels':work})
# Patterns force real encoder selections for all three HS33 schemes; no hand-guessed packets.
for desired in[0,1,2]:
 hh,w=8,64;ref=np.full((hh,w),(10<<11)|(20<<5)|10,np.uint16);y,x=np.indices((hh,w));delta=(x%2+1)if desired==0 else np.where((x==3)&(y==2),1,0)if desired==1 else np.where(x<32,1,2)
 a=(((10+delta).astype(np.uint16)<<11)|((20+delta).astype(np.uint16)<<5)|(10+delta).astype(np.uint16));payload,work=hs33._encode_patch(a,ref,1);actual=[v['selected']['scheme']for v in work];assert actual==[desired]*3,(desired,actual)
 add('hs33-scheme'+str(desired),hs33._pack_patch(a,ref,1,payload),ref,a,{'required_scheme':desired,'observed_channel_schemes':actual,'channels':work})
for count,w,hh in[(3840,80,48),(5760,96,60),(7680,120,64)]:
 a=words(w,hh);assert a.size==count;add('hd25-raw-geometry'+str(count),h._pack(0,a,h.ZERO,a.astype('<u2').tobytes()),None,a,{'geometry_boundary_words':count})
(out/'index.tsv').write_text(''.join('\t'.join(r)+'\n'for r in rows),newline='\n');(out/'cases.json').write_text(json.dumps(metadata,indent=2)+'\n');assert all(sha(Path(n).read_bytes())==v for n,v in src.items());files={f.name:sha(f.read_bytes())for f in out.iterdir()if f.is_file()};(out/'MANIFEST.json').write_text(json.dumps({'status':'PYTHON_REFERENCE_PASS_OLD_NATIVE_PENDING','source_dependencies':src,'cases':len(rows),'HD25_modes':sorted({m['observed_mode']for m in metadata if m['magic']=='HD25'}),'HS32_modes':sorted({m['observed_mode']for m in metadata if m['magic']=='HS32'}),'HS33_modes':sorted({m['observed_mode']for m in metadata if m['magic']=='HS33'}),'files':files},indent=2)+'\n');print(json.dumps({'positive_cases':len(rows),'index':str(out/'index.tsv'),'HD25_modes':list(range(10)),'motion_grammars':[0,1,2],'HS_modes':[0,1,2,3,9,10,11],'HS33_selected_schemes':[0,1,2]}),flush=True)
