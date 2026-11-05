"""Independent candidate stream decode and actual byte winner qualification."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,zlib
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];SOURCE=HERE.parent/'python-game-binary-qual-v40-study'
s=importlib.util.spec_from_file_location('rice46_independent_old_decoder',HERE.parent/'python-game-binary-v38-study/decoder.py');old=importlib.util.module_from_spec(s);sys.modules[s.name]=old;s.loader.exec_module(old)
def digest(b):return hashlib.sha256(b).hexdigest()
def raw(folder,d):
 p=Path(d['path']);assert not p.is_absolute() and '..' not in p.parts;stored=(folder/p).read_bytes();assert digest(stored)==d['stored_sha256'];z=zlib.decompressobj();b=z.decompress(stored,d['raw_bytes']+1);assert z.eof and not z.unused_data and not z.unconsumed_tail and len(b)==d['raw_bytes'] and digest(b)==d['raw_sha256'];return b
class Reader(old.ArithmeticReader):
 def __init__(self,*a):super().__init__(*a);self.decisions=0;self.maximum=0
 def decode(self,index):
  before=self.pos;v=super().decode(index);self.decisions+=1;self.maximum=max(self.maximum,self.pos-before);return v

def decode_stream(packet,n,bw,stream,count):
 k0,k1,bits=struct.unpack_from('<BBI',packet);r=Reader(packet[6:],bits)
 if stream==0:
  assert k0<=13 and k1==255;out=np.zeros(n,np.int32);prev=0
  for i in range(n):
   if i%bw==0:prev=0
   prev+=old.signed(r.rice(k0,14));assert -2048<=prev<=2048;out[i]=prev
 else:
  lo,hi=((1,6),(6,21),(21,64))[stream-1];assert k0<=19 and k1<=11;out=np.zeros(n*(hi-lo),np.int16);index=-1
  for _ in range(count):
   index+=r.rice(k0,24)+1;assert index<len(out);value=old.signed(r.rice(k1,12,True)+1);assert value and -2048<=value<=2048;out[index]=value
 work=dict(binary_decisions=r.decisions,renorm_steps=r.pos-16,max_renorm_per_bit=r.maximum);r.finish();return out,work

def main():
 data=json.loads((HERE/'results.json').read_text());source=json.loads((SOURCE/'results.json').read_text());assert len(data['cases'])==4
 for p,h in data['source_sha256'].items():assert digest((ROOT/p).read_bytes())==h,p
 packets=streams=changes=oldbytes=newbytes=frames=0
 for c,prior in zip(data['cases'],source['cases'],strict=True):
  assert c['scene']==prior['scene'] and len(c['rows'])==6
  for r,f in zip(c['rows'],prior['rows'][:6],strict=True):
   assert r['id']==f['id'];frames+=1
   for p,baseline in zip(r['planes'],f['attempts'],strict=True):
    assert p['plane']==baseline['plane']
    for a,t in zip(p['alternatives'],baseline['trials'],strict=True):
     assert a['source_packet']==t['packet'] and a['compact']==t['compact'];original=raw(SOURCE,t['packet']);hdr=old.FRAME.unpack_from(original);n,bw=hdr[3:5];assert not hdr[2];coeff=old.decode(original,n,bw);zig=coeff.reshape(n,64)[:,old.ORDER];assert digest(coeff.astype('<i2').tobytes())==a['coefficient_sha256'];selected=[];pos=old.FRAME.size;counts=hdr[-3:]
     for index,trial in enumerate(a['trials']):
      assert trial['stream']==index;candidate_bytes=[]
      baseline_stream=original[pos:pos+hdr[6+index]];pos+=hdr[6+index];basek=struct.unpack_from('<BB',baseline_stream)
      if index==0:
       keys=[(k,255) for k in dict.fromkeys((basek[0],max(0,basek[0]-1),min(13,basek[0]+1)))];expected=zig[:,0]
      else:
       kr,kv=basek;rs=tuple(dict.fromkeys((kr,max(0,kr-1),min(19,kr+1))));vs=tuple(dict.fromkeys((kv,max(0,kv-1),min(11,kv+1))));keys=[basek]+sorted(((x,y) for x in rs for y in vs if(x,y)!=basek),key=lambda q:(abs(q[0]-kr)+abs(q[1]-kv),q));lo,hi=((1,6),(6,21),(21,64))[index-1];expected=zig[:,lo:hi].reshape(-1)
      assert len(keys)==len(trial['candidates'])
      for candidate,key in zip(trial['candidates'],keys,strict=True):
       wire=raw(HERE,candidate['packet']);assert struct.unpack_from('<BB',wire)==key==(candidate['k0'],candidate['k1']);out,work=decode_stream(wire,n,bw,index,None if index==0 else counts[index-1]);np.testing.assert_array_equal(out,expected);assert work==candidate['work'];assert candidate['bytes']==len(wire);candidate_bytes.append(wire);streams+=1
      assert candidate_bytes[0]==baseline_stream;winner=min(range(len(candidate_bytes)),key=lambda j:len(candidate_bytes[j]));assert winner==trial['selected'];changes+=winner!=0;selected.append(candidate_bytes[winner])
     assert pos==len(original)-4
     body=old.FRAME.pack(b'AB38',1,0,n,bw,0,*map(len,selected),*counts)+b''.join(selected)
     if sum(map(len,selected))>=128*n:body=old.FRAME.pack(b'AB38',1,1,n,bw,0,128*n,0,0,0,0,0,0)+coeff.astype('<i2').tobytes()
     packet=body+struct.pack('<I',zlib.crc32(body));assert packet==raw(HERE,a['packet']);np.testing.assert_array_equal(old.decode(packet,n,bw),coeff);assert a['old_bytes']==len(original) and a['bytes']==len(packet)<=len(original);oldbytes+=len(original);newbytes+=len(packet);packets+=1
 summary=dict(frames=frames,AB38_packets=packets,old_component_bytes=oldbytes,searched_component_bytes=newbytes,attempted_stream_encodes=streams,changed_streams=changes);assert summary==data['summary'];assert packets==144
 print(json.dumps(dict(**summary,all_streams_independently_decoded=True,unchanged_AB38_wire=True,encoder_imported=False,complete_frame_savings_or_30fps_proven=False)))
if __name__=='__main__':main()
