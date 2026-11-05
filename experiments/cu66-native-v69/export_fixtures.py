#!/usr/bin/env python3
"""Explicit CU66 native/RTL fixtures from retained frozen40/66 histories."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,zlib,collections
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
s=importlib.util.spec_from_file_location('native69_frozen66',HERE.parent/'python-game-canonical-tag-v66-study/helpers.py');h=importlib.util.module_from_spec(s);sys.modules[s.name]=h;s.loader.exec_module(h)
w=h.bound('native69_frozen66_protocol',HERE.parent/'python-game-canonical-tag-v66-study/protocol.py',h)
def digest(b):return hashlib.sha256(b).hexdigest()
def put(data,suffix):
 rel='fixtures/'+digest(data)+suffix;p=HERE/rel;p.parent.mkdir(exist_ok=True);p.write_bytes(data);return dict(path=rel,bytes=len(data),sha256=digest(data))
def main():
 table=h.load(HERE.parent/'python-game-canonical-tag-v66-study/results.json');cases=[];index=[];counts=collections.Counter();safe=h.f.f.safe_blocks();profile=w.PROFILES['CU66']['profile']
 constants='#pragma once\n#include <cstdint>\nnamespace cu66 {\n'
 def arr(name,a,ctype):
  nonlocal constants
  a=np.asarray(a);dims=''.join('['+str(n)+']'for n in a.shape)
  def nested(x):return '{'+','.join(nested(v)if np.ndim(v)else str(int(v))for v in x)+'}'
  constants+='inline constexpr '+ctype+' '+name+dims+'='+nested(a)+';\n'
 arr('PROFILE',np.frombuffer(profile,np.uint8),'uint8_t');arr('DCT',h.m.ft.Q14,'int32_t');arr('QTABLES',[[h.m.ft.qtable(scale,bool(c))for scale in (8,16,32)]for c in(0,1)],'int16_t');arr('RECTS',h.f.f.n.RECTS,'uint16_t')
 for axis,mask in enumerate(safe):arr('SAFE'+str(axis),mask.reshape(-1),'uint8_t')
 constants+='}\n';(HERE/'generated_constants.hpp').write_text(constants)
 for caseid,source in enumerate(c for c in table['cases']if c['source_folder']=='python-game-binary-qual-v40-study'):
  rx=h.oldrx.Receiver();rows=[];oldtable=h.load(HERE.parent/source['source_folder']/'results.json')['cases'];oldcase=next(c for c in oldtable if c['scene']==source['scene'])
  for row,oldrow in zip(source['rows'],oldcase['rows'],strict=True):
   pkt=h.raw(row['profiles']['CU66']['packet'],HERE.parent/'python-game-canonical-tag-v66-study');oldpkt=h.raw(oldrow['packet'],HERE.parent/source['source_folder']);out=rx.receive(oldpkt);planes,hud,meta=out[:3]
   yuv=b''.join(p.astype(np.uint8).tobytes()for p in planes);words=b''.join(p['words'].astype('<u2').tobytes()for p in hud);display=h.f.f.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(planes)),tuple(p['words']for p in hud)).astype('<u2').tobytes()
   packet=put(pkt,'.cu66');outer=w.OUTER.unpack_from(pkt);inner=pkt[w.OUTER.size:w.OUTER.size+outer[-2]];fields=w.INNER.unpack_from(inner);pos=w.INNER.size+fields[-5]+fields[-4];payloads=[]
   for axis,(size,mask,fullcoeff)in enumerate(zip(fields[-3:],safe,meta['coefficients'],strict=True)):
    payload=inner[pos:pos+size];pos+=size;dispatch=payload[0];assert dispatch in(5,6);coeff=fullcoeff[~mask.reshape(-1)]if dispatch==6 else fullcoeff;bw=1 if dispatch==6 else(90 if axis==0 else 45)
    payloads.append(dict(axis=axis,dispatch=dispatch,blocks=len(coeff),blocks_w=bw,full_blocks=len(fullcoeff),full_blocks_w=90 if axis==0 else 45,safe_hidden_mask=put(mask.astype(np.uint8).tobytes(),'.mask'),packet=put(payload[1:],'.ab38'),expected_coefficients=put(zlib.compress(coeff.astype('<i2').tobytes(),9),'.coeff.i16.zlib'),expected_coefficients_raw_sha256=digest(coeff.astype('<i2').tobytes())))
   hm=h.f.f.hud._meta(meta['hud'])
   for kind,data in zip(hm['types'],hm['payloads']):counts[(meta['hud'][:4].decode(),kind,data[:4].decode(),data[5])]+=1
   record=dict(id=row['id'],key=row['key'],reference_id=meta['reference_id'],packet=packet,source_old_packet=oldrow['packet'],canonical_yuv_u8_sha256=digest(yuv),hud_words_u16le_sha256=digest(words),display_rgb565_u16le_sha256=digest(display),canonical_tag=w.tag_u8(planes).hex(),planes=payloads)
   if row['id']==0:record['directed_first_expected']={k:put(v,suff)for k,v,suff in [('yuv',yuv,'.yuv'),('hud',words,'.hud'),('display',display,'.rgb565')]}
   rows.append(record);index.append('\t'.join(map(str,(caseid,row['id'],packet['path'],record['canonical_yuv_u8_sha256'],record['hud_words_u16le_sha256'],record['display_rgb565_u16le_sha256']))))
  cases.append(dict(id=caseid,scene=source['scene'],rows=rows));print(json.dumps(dict(scene=source['scene'],frames=len(rows))),flush=True)
 pins={p:sha for p,sha in table['source_sha256'].items()};pins['experiments/python-game-canonical-tag-v66-study/results.json']=h.sha(HERE.parent/'python-game-canonical-tag-v66-study/results.json')
 manifest=dict(schema='cu66-native-v69-fixtures',capabilities=dict(wire='CU66/GU66',epoch=25,width=720,height=480,base_dispatch=[5,6],zero_motion_only=True,hud_envelopes=['HU25','HX32','HX33']),source_sha256=pins,cases=cases,hud_distribution=[dict(envelope=k[0],kind=k[1],patch_magic=k[2],mode=k[3],count=v)for k,v in sorted(counts.items())],physical_30fps_proven=False)
 (HERE/'planes.tsv').write_text('\n'.join('\t'.join(map(str,(p['packet']['path'],p['blocks'],p['blocks_w'],p['expected_coefficients_raw_sha256']))) for c in cases for r in c['rows'] for p in r['planes'])+'\n');(HERE/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(HERE/'index.tsv').write_text('\n'.join(index)+'\n');print('frames',len(index),flush=True)
if __name__=='__main__':main()
