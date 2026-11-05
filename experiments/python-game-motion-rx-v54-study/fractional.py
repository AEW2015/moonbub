"""Directed six-frame fractional-motion fixture, coefficient-exact AB38 recode."""
from pathlib import Path
import hashlib,json,sys,zlib
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE.parent/'python-game-stream-rx-v48-study'));import receiver as stream
h=stream.h;SOURCE=HERE.parent/'python-game-implicit-v37-study'
enc=h.module('motionrx54_frozen_AB38_encoder',HERE.parent/'python-game-binary-v38-study/model.py')
def blob(b):
 stored=zlib.compress(b,9);p='objects/'+h.digest(stored)+'.zlib';(HERE/'objects').mkdir(exist_ok=True);(HERE/p).write_bytes(stored);return dict(path=p,raw_bytes=len(b),raw_sha256=h.digest(b),stored_sha256=h.digest(stored))
def main():
 data=h.load(SOURCE/'results.json');source=next(c for c in data['cases'] if c['kind']=='fractional_motion');pins={p:v for p,v in h.old.old.pins().items()};pins.update({p.relative_to(ROOT).as_posix():h.sha(p) for p in(SOURCE/'results.json',Path(__file__),HERE.parent/'python-game-binary-v38-study/model.py')});rows=[];rx=stream.Receiver()
 for r in source['rows']:
  old=h.raw(r['packet'],SOURCE);meta=h.f.parse(old);outer=list(h.f.HEADER.unpack_from(old));inner=old[h.f.HEADER.size:h.f.HEADER.size+outer[11]];fields=list(h.m.HEADER.unpack_from(inner));mapend=h.m.HEADER.size+fields[12]+fields[13];maps=inner[h.m.HEADER.size:mapend];payloads=[];attempts=[]
  for axis,(c,safe) in enumerate(zip(meta['coefficients'],h.f.f.safe_blocks(),strict=True)):
   options=[];trials=[]
   for compact in(False,True):
    coeff=c[~safe.reshape(-1)] if compact else c;bw=1 if compact else 90 if axis==0 else 45;packet,work=enc.encode(coeff,bw);np.testing.assert_array_equal(h.block.frozen.decode(packet,len(coeff),bw),coeff);options.append(bytes([6 if compact else 5])+packet);trials.append(dict(compact=compact,packet=blob(packet),coefficient_sha256=h.digest(coeff.astype('<i2').tobytes()),work=work))
   selected=min(range(2),key=lambda i:len(options[i]));payloads.append(options[selected]);attempts.append(dict(plane=axis,selected=selected,option_bytes=list(map(len,options)),trials=trials))
  fields[0]=b'GS38';fields[14:17]=map(len,payloads)
  body=h.m.HEADER.pack(*fields)+maps+b''.join(payloads);newinner=body+__import__('struct').pack('<I',zlib.crc32(body));outer[0]=b'CS38';outer[8]=stream.envelope.PROFILE;outer[11]=len(newinner);body=h.f.HEADER.pack(*outer)+newinner+meta['hud'];wire=body+__import__('struct').pack('<I',zlib.crc32(body));assert len(wire)<=49152
  out,patches,parsed,_=rx.receive(wire);assert h.m.C.reference_tag(out).hex()==r['normalized_tag'];rows.append(dict(id=r['id'],source_packet=r['packet'],packet=blob(wire),complete_bytes=len(wire),normalized_tag=r['normalized_tag'],display_sha256=r['display_sha256'],attempts=attempts))
 result=dict(schema='gamebub-motion-rx-v54-fractional',source_sha256=pins,rows=rows,source_folder=SOURCE.relative_to(ROOT).as_posix(),scope=['Sixreuseddirectedfractionalmotionframes,notnewcaptures;full/compactAB38forcedforarithmetic-only48capability.','Everycoefficient/map/HUD/base/canonicaltagpreserved;newwireonlyentropyprofile,notnewquality.','All36actualABalternativesretained;allfinalCS38packetsfitcap.']);(HERE/'fractional.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(frames=len(rows),AB38_alternatives=36,max_complete_bytes=max(r['complete_bytes'] for r in rows))),flush=True)
if __name__=='__main__':main()
