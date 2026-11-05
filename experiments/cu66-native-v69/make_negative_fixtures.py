#!/usr/bin/env python3
"""Retained malformed/CAPABILITY cases; rebuild enclosing CRCs deliberately."""
from pathlib import Path
import importlib.util,json,struct,sys,zlib
import numpy as np
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('native69_export_helpers',HERE/'export_fixtures.py');e=importlib.util.module_from_spec(s);sys.modules[s.name]=e;s.loader.exec_module(e)
h,w=e.h,e.w
seal=lambda body:body+struct.pack('<I',zlib.crc32(body))
def main():
 manifest=h.load(HERE/'manifest.json');c=manifest['cases'][0];key=c['rows'][0];p=c['rows'][1];packet=(HERE/p['packet']['path']).read_bytes();of=list(w.OUTER.unpack_from(packet));inner=packet[w.OUTER.size:w.OUTER.size+of[-2]];hud=packet[w.OUTER.size+of[-2]:-4];inf=list(w.INNER.unpack_from(inner));body=inner[w.INNER.size:-4]
 def build(outer=None,fields=None,basebody=None,overlay=None,basebytes=None):
  outer=list(of if outer is None else outer);fields=list(inf if fields is None else fields);basebody=body if basebody is None else basebody;overlay=hud if overlay is None else overlay;base=seal(w.INNER.pack(*fields)+basebody)if basebytes is None else basebytes;outer[-2:]=[len(base),len(overlay)];return seal(w.OUTER.pack(*outer)+base+overlay)
 rows=[]
 def add(name,data,category='malformed',validated_frozen=False):
  desc=e.put(data,'.negative');rows.append(dict(name=name,category=category,packet=desc,valid_frozen_CU66=validated_frozen))
 add('empty',b'');add('truncated',packet[:31]);add('oversized',packet+bytes(49153-len(packet)));bad=bytearray(packet);bad[-1]^=1;add('outer_crc',bytes(bad))
 for name,index,value in [('profile',8,b'X'*16),('output_zero',10,bytes(16)),('output_wrong',10,b'Y'*16),('replay_frame',4,0),('wrong_epoch',3,26),('wrong_geometry',6,718)]:
  outer=list(of);outer[index]=value;add(name,build(outer=outer))
 fields=list(inf);outer=list(of);fields[10]=outer[9]=b'R'*16;add('reference_tag',build(outer=outer,fields=fields))
 fields=list(inf);outer=list(of);fields[5]=outer[5]=0xffffffff;add('reference_id',build(outer=outer,fields=fields))
 bad=bytearray(inner);bad[-1]^=1;add('inner_crc',build(basebytes=bytes(bad)))
 for name,pos,value in [('qmap_code',0,body[0]|192),('qmap_padding',inf[11]-1,body[inf[11]-1]|1),('nonzero_motion',inf[11]+1,1),('unsupported_vector_grammar',inf[11],1)]:
  b=bytearray(body);b[pos]=value;add(name,build(basebody=bytes(b)))
 first=inf[11]+inf[12]
 b=bytearray(body);b[first]=2;add('unsupported_legacy_dispatch_seed',build(basebody=bytes(b)),category='unsupported_capability')
 b=bytearray(body);b[first]=255;add('unknown_dispatch',build(basebody=bytes(b)))
 b=bytearray(body);b[first+1+inf[13]-2]^=1;add('nested_AB_crc',build(basebody=bytes(b)))
 # Valid nested checksum but invalid declared AB geometry.
 b=bytearray(body);ab=bytearray(b[first+1:first+inf[13]]);ab[6]^=1;ab=bytearray(seal(ab[:-4]));b[first+1:first+inf[13]]=ab;add('AB_geometry_resealed',build(basebody=bytes(b)))
 b=bytearray(hud);b[-1]^=1;add('HUD_crc',build(overlay=bytes(b)))
 b=bytearray(hud);b[38]^=1;add('late_HUD_output_tag',build(overlay=seal(b[:-4])))
 # Old and cross-profile packets are valid at their own API, unsupported here.
 source40=HERE.parent/'python-game-binary-qual-v40-study';oldcase=h.load(source40/'results.json')['cases'][0];oldpacket=h.raw(oldcase['rows'][1]['packet'],source40);add('legacy_CS38_valid_profile',oldpacket,'unsupported_profile')
 rx=h.oldrx.Receiver();firstold=h.raw(oldcase['rows'][0]['packet'],source40);rx.receive(firstold);prior=rx.ref;out=rx.receive(oldpacket);cs66,_=w.convert(oldpacket,'CS66',reference=prior,normalized=out[0]);add('CS66_valid_profile',cs66,'unsupported_profile')
 # True zero-motion CU66 packets using legacy coefficient payloads, not just
 # relabeled arithmetic bodies. All are checked by frozen66 after packing.
 r66=h.bound('native69_frozen66receiver',HERE.parent/'python-game-canonical-tag-v66-study/receiver.py',h)
 full=out[2]['coefficients'];axis=2;bw=45
 try:
  legacy,_=h.m.base._encode_plane(full[axis],bw)
 except AttributeError:
  legacy,_=h.m.base.old._encode_plane(full[axis],bw)
 pos=first+inf[13]+inf[14];newbody=body[:pos]+legacy;fields=list(inf);fields[15]=len(legacy);candidate=build(fields=fields,basebody=newbody)
 reference_packet=(HERE/key['packet']['path']).read_bytes();probe=r66.Receiver('CU66');probe.receive(reference_packet);probe.receive(candidate);add('actual_legacy_coefficient_packet',candidate,'unsupported_capability',True)
 # Nonzero hidden coefficients must reject even when normalization would
 # erase their output; use a genuine full AB38 encode with valid nested CRC.
 ab=h.module('native69_AB38_encoder',HERE.parent/'python-game-binary-v38-study/model.py')
 altered=full[0].copy();mask=h.f.f.safe_blocks()[0].reshape(-1);altered[np.flatnonzero(mask)[0],0,0]=1
 payload,_=ab.encode(altered,90);replacement=b'\x05'+payload;fields=list(inf);fields[13]=len(replacement);candidate=build(fields=fields,basebody=body[:first]+replacement+body[first+inf[13]:]);add('hidden_nonzero_coefficient_resealed',candidate)
 # Real frozen47 nonzero-motion frame at the same key0 incoming canonical
 # state. This is valid CU66, but outside native's advertised zero-MV scope.
 motionfolder=HERE.parent/'python-game-motion-v47-study';mc=next(v for v in h.load(motionfolder/'results.json')['cases']if v['scene']==c['scene']and v['policy']=='global_grid')
 mr=h.oldrx.Receiver();mr.receive(h.raw(mc['rows'][0]['packet'],motionfolder));prior=mr.ref;mp=h.raw(mc['rows'][1]['packet'],motionfolder);mo=mr.receive(mp);assert np.any(mo[2]['vectors']);converted,_=w.convert(mp,'CU66',reference=prior,normalized=mo[0]);probe=r66.Receiver('CU66');probe.receive(reference_packet);probe.receive(converted);add('actual_nonzero_motion_CU66',converted,'unsupported_capability',True)
 (HERE/'negative_manifest.json').write_text(json.dumps(dict(schema='cu66-native-v69-negative',seed_key_packet=key['packet'],valid_next_packet=p['packet'],recovery_key_packet=c['rows'][24]['packet'],cases=rows),indent=2)+'\n');(HERE/'negative.tsv').write_text('\n'.join(x['name']+'\t'+x['packet']['path']for x in rows)+'\n');print('negative cases',len(rows),flush=True)
if __name__=='__main__':main()
