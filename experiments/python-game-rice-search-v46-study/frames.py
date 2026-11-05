"""Actual CS38 packet choices using retained searched full/compact AB38 payloads."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,zlib
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];BASE=HERE.parent/'python-game-binary-v38-study';SOURCE=HERE.parent/'python-game-binary-qual-v40-study'
def mod(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
h=mod('helpers',BASE/'helpers.py');frame=mod('rice46_frame_frozen_adapter',BASE/'frame_verify.py')
def digest(b):return hashlib.sha256(b).hexdigest()
def raw(folder,d):return h.raw(d,folder)
def blob(data):
 packed=zlib.compress(data,9);p='objects/'+digest(packed)+'.zlib';(HERE/'objects').mkdir(exist_ok=True);(HERE/p).write_bytes(packed);return dict(path=p,raw_bytes=len(data),raw_sha256=digest(data),stored_sha256=digest(packed))
def main():
 search=h.load(HERE/'results.json');source=h.load(SOURCE/'results.json');pins=dict(search['source_sha256']);pins.update({(HERE/n).relative_to(ROOT).as_posix():h.sha(HERE/n) for n in('results.json','frames.py')});cases=[]
 for c,old in zip(search['cases'],source['cases'],strict=True):
  rx=frame.Receiver();oracle=frame.Receiver();rows=[]
  for row,prior in zip(c['rows'],old['rows'][:6],strict=True):
   original=raw(SOURCE,prior['packet']);outer=list(h.f.HEADER.unpack_from(original));inner=original[h.f.HEADER.size:h.f.HEADER.size+outer[11]];fields=list(h.f.m.HEADER.unpack_from(inner));mapend=h.f.m.HEADER.size+fields[12]+fields[13];maps=inner[h.f.m.HEADER.size:mapend];pos=mapend;payloads=[];work=[]
   for axis,(plane,size) in enumerate(zip(row['planes'],fields[14:17],strict=True)):
    previous=inner[pos:pos+size];pos+=size;options=[previous]+[bytes([6 if a['compact'] else 5])+raw(HERE,a['packet']) for a in plane['alternatives']];selected=min(range(len(options)),key=lambda i:len(options[i]));payloads.append(options[selected]);work.append(dict(plane=axis,option_bytes=list(map(len,options)),selected=selected))
   fields[14:17]=map(len,payloads);newinner=frame.seal(h.f.m.HEADER.pack(*fields)+maps+b''.join(payloads));outer[11]=len(newinner);hud=original[h.f.HEADER.size+len(inner):-4];packet=frame.seal(h.f.HEADER.pack(*outer)+newinner+hud);assert len(packet)<=len(original)<=49152
   a,pa,ma,_=rx.receive(packet);b,pb,mb,_=oracle.receive(original)
   for x,y in zip(a,b,strict=True):np.testing.assert_array_equal(x,y)
   for x,y in zip(pa,pb,strict=True):np.testing.assert_array_equal(x['words'],y['words'])
   rows.append(dict(id=row['id'],source_packet=prior['packet'],packet=blob(packet),old_complete_bytes=len(original),complete_bytes=len(packet),bytes_saved=len(original)-len(packet),planes=work,normalized_tag=h.f.m.C.reference_tag(a).hex(),source_quality=prior['quality']))
  summary=dict(frames=len(rows),old_complete_bytes=sum(r['old_complete_bytes'] for r in rows),complete_bytes=sum(r['complete_bytes'] for r in rows),bytes_saved=sum(r['bytes_saved'] for r in rows));cases.append(dict(scene=c['scene'],rows=rows,summary=summary))
 assert all(h.sha(ROOT/p)==v for p,v in pins.items());summary={k:sum(c['summary'][k] for c in cases) for k in('frames','old_complete_bytes','complete_bytes','bytes_saved')}
 (HERE/'frames.json').write_text(json.dumps(dict(schema='gamebub-rice-search-v46-frames',source_sha256=pins,cases=cases,summary=summary,scope=['ActualCS38completepackets,legacy-selectedpayloadfallbackplussearchedfull/compact;tiesoldfirst.','Exactcanonicalrefs/HUD/coefficientsandunchangedquality;6frameprefixespercliponly.','Frameproofadapterreencodesoldentropy;noimprovednativeFPGAreceiverorFPSclaim.','SourceCS37/CS38encodingexternallypaid,plusall2917searchstreamencodes;noendtoendtiming.']),indent=2)+'\n');print(json.dumps(dict(summary=summary,cases=[dict(scene=c['scene'],**c['summary']) for c in cases])),flush=True)
if __name__=='__main__':main()
