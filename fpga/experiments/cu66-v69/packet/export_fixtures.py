#!/usr/bin/env python3
"""Independent structural CU66 oracle; payload semantics deliberately deferred."""
from pathlib import Path
import hashlib,json,struct,zlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];NATIVE=ROOT/'experiments/cu66-native-v69'
OUTER=struct.Struct('<4sBBHIIHH16s16s16sII');INNER=struct.Struct('<4sBBIIIHHBB16sIIIII');HUD=struct.Struct('<4sBBIIIHH16s16s4I4B16H')
RECTS=((22,54,160,24),(22,82,160,24),(168,360,320,24),(168,390,240,24));PROFILE=hashlib.sha256(b'CU66:canonical-only-cached-ref-sha128-u8-v1:'+json.dumps(RECTS,separators=(',',':')).encode()).digest()[:16]
NO_REF=0xffffffff;ZERO=bytes(16)
def sha(data):return hashlib.sha256(data).hexdigest()
def check(value):
 if not value:raise ValueError('structural contract')
def crc(data):check(len(data)>=4 and zlib.crc32(data[:-4])==struct.unpack_from('<I',data,len(data)-4)[0])
def oracle(packet,cfg):
 check(733<=len(packet)<=49152);crc(packet);o=OUTER.unpack_from(packet);magic,v,flags,epoch,fid,rid,w,hh,profile,rt,ot,nb,nh=o
 check((magic,v,epoch,w,hh,profile)==(b'CU66',1,25,720,480,PROFILE)and flags in(2,3));key=bool(flags&1);check(fid!=NO_REF and ot!=ZERO and(not cfg['last_valid']or fid>cfg['last_id']));check(nb>=543 and nh>=110 and nb<=len(packet)and nh<=len(packet)and nb+nh+80==len(packet))
 if key:check(rid==NO_REF and rt==ZERO)
 else:check(cfg['ref_valid']and rid==cfg['ref_id']and rid<fid and rt!=ZERO and rt.hex()==cfg['ref_tag'])
 inner=packet[76:76+nb];hud=packet[76+nb:-4];crc(inner);crc(hud);f=INNER.unpack_from(inner);im,iv,ik,ie,iff,ir,iw,ih,bs,limit,irt,nq,nv,*lengths=f
 check((im,iv,ik,ie,iff,ir,iw,ih,irt)==(b'GU66',1,int(key),25,fid,rid,720,480,rt)and bs in(16,32)and limit==18);check(nq==338 and nv==(0 if key else 3)and all(47<=n<=len(packet)for n in lengths)and nq+nv+sum(lengths)+64==nb)
 mapped=inner[60:398];codes=[(byte>>shift)&3 for byte in mapped for shift in(6,4,2,0)];check(all(c<=2 for c in codes[:1350])and codes[1350:]==[0,0]);check(key or inner[398:401]==bytes(3))
 planes=[];pos=60+nq+nv
 for axis,n in enumerate(lengths):
  dispatch=inner[pos];check(dispatch in(5,6));full=5400 if axis==0 else 1350;compact=5144 if axis==0 else 1331;planes.append(dict(addr=76+pos+1,bytes=n-1,dispatch=dispatch,blocks=compact if dispatch==6 else full,blocks_w=1 if dispatch==6 else 90 if axis==0 else 45));pos+=n
 hm=HUD.unpack_from(hud);hm_magic,hm_v,count,he,hf,hr,hw,hh2,hrt,hot=hm[:10];lens=hm[10:14];kinds=hm[14:18];rects=tuple(tuple(hm[18+4*i:22+4*i])for i in range(4));check(hm_magic in(b'HU25',b'HX32',b'HX33')and(hm_v,count,he,hf,hr,hw,hh2)==(1,4,25,fid,rid,720,480)and hot!=ZERO);check((hrt==ZERO)if key else(hrt!=ZERO));maxkind={b'HU25':2,b'HX32':3,b'HX33':4}[hm_magic];check(rects==RECTS and all(1<=n<=len(packet)for n in lens)and all(1<=k<=maxkind for k in kinds)and sum(lens)+110==nh)
 return dict(key=key,id=fid,reference_id=rid,reference_tag=rt.hex(),output_tag=ot.hex(),block_size=bs,planes=planes,hud_addr=76+nb,hud_bytes=nh,hud_reference_tag=hrt.hex(),hud_output_tag=hot.hex(),qmap=bytes(codes[:1350]))
def put(data,suffix):
 rel='fixtures/'+sha(data)+suffix;(HERE/'fixtures').mkdir(exist_ok=True);(HERE/rel).write_bytes(data);return dict(path=rel,bytes=len(data),sha256=sha(data))
def main():
 native=json.loads((NATIVE/'manifest.json').read_text());negative=json.loads((NATIVE/'negative_manifest.json').read_text());cases=[];index=[]
 def add(name,packet,cfg,full_valid):
  blob=put(packet,'.cu66');expected=None
  try:expected=oracle(packet,cfg)
  except(ValueError,struct.error,IndexError):pass
  mode=1 if full_valid else 2 if expected is not None else 0
  meta=None
  if expected is not None:
   qmap=put(expected.pop('qmap'),'.qmap');parts=[int(expected['key']),expected['id'],expected['reference_id'],expected['reference_tag'],expected['output_tag'],expected['block_size'],expected['hud_addr'],expected['hud_bytes'],expected['hud_reference_tag'],expected['hud_output_tag'],qmap['path']]
   for p in expected['planes']:parts.extend(p[k]for k in('addr','bytes','dispatch','blocks','blocks_w'))
   meta=put(('\t'.join(map(str,parts))+'\n').encode(),'.meta');expected['qmap']=qmap
  record=dict(name=name,packet=blob,mode=mode,mode_description={0:'structurally rejected',1:'stored full decoder qualified; parser metadata accepted',2:'parser metadata only; semantic downstream rejection required'}[mode],cfg=cfg,expected=expected,meta=meta);cases.append(record);index.append('\t'.join(map(str,(name,blob['path'],mode,int(cfg['last_valid']),cfg['last_id'],int(cfg['ref_valid']),cfg['ref_id'],cfg['ref_tag'],'-'if meta is None else meta['path']))))
 for c in native['cases']:
  cfg=dict(last_valid=False,last_id=0,ref_valid=False,ref_id=0,ref_tag=ZERO.hex())
  for r in c['rows']:
   packet=(NATIVE/r['packet']['path']).read_bytes();assert sha(packet)==r['packet']['sha256'];add(c['scene']+'_'+str(r['id']),packet,dict(cfg),True);assert cases[-1]['mode']==1;cfg=dict(last_valid=True,last_id=r['id'],ref_valid=True,ref_id=r['id'],ref_tag=r['canonical_tag'])
 cfg=dict(last_valid=True,last_id=0,ref_valid=True,ref_id=0,ref_tag=native['cases'][0]['rows'][0]['canonical_tag'])
 for r in negative['cases']:add('negative_'+r['name'],(NATIVE/r['packet']['path']).read_bytes(),dict(cfg),False)
 result=dict(schema='cu66-packet-v69-fixtures',source_sha256={str((NATIVE/name).relative_to(ROOT)):sha((NATIVE/name).read_bytes())for name in('manifest.json','negative_manifest.json')},cases=cases,accepted_full_frames=sum(c['mode']==1 for c in cases),deferred_semantic_failures=sum(c['mode']==2 for c in cases),structural_rejections=sum(c['mode']==0 for c in cases),tags_wire_byte0_bits='127:120',canonical_or_HUD_semantic_decode_proven=False)
 (HERE/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');(HERE/'cases.tsv').write_text('\n'.join(index)+'\n');print(json.dumps({k:result[k]for k in('accepted_full_frames','deferred_semantic_failures','structural_rejections')}))
if __name__=='__main__':main()
