"""AB38 block iterator: bounded coefficient staging, frozen binary primitive.

This changes delivery order/buffering only. It does not implement a target port.
Four frozen binary reader states remain live; compressed input is retained.
"""
from pathlib import Path
import importlib.util,struct,sys,zlib
import numpy as np
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('blockrx44_frozen_binary38',HERE.parent/'python-game-binary-v38-study/decoder.py')
frozen=importlib.util.module_from_spec(spec);sys.modules[spec.name]=frozen;spec.loader.exec_module(frozen)
BANDS=((1,6),(6,21),(21,64))
class TileReader:
 def __init__(self,packet,blocks,blocks_w):
  if type(blocks)is not int or not 1<=blocks<=65536 or type(blocks_w)is not int or not 1<=blocks_w<=256 or blocks%blocks_w:raise ValueError('bounded requested coefficient geometry')
  H=frozen.FRAME
  if type(packet)is not bytes or not H.size+4<=len(packet)<=H.size+4+128*blocks:raise ValueError('AB38 bounded packet')
  if zlib.crc32(packet[:-4])!=struct.unpack('<I',packet[-4:])[0]:raise ValueError('AB38 CRC')
  magic,version,flags,n,bw,reserved,*tail=H.unpack_from(packet);lengths=tail[:4];counts=tail[4:]
  if(magic,version,n,bw,reserved)!=(b'AB38',1,blocks,blocks_w,0) or flags not in(0,1):raise ValueError('AB38 profile')
  if len(packet)!=H.size+4+sum(lengths):raise ValueError('AB38 exact lengths')
  self.packet=packet;self.blocks=blocks;self.blocks_w=blocks_w;self.block=0;self.previous_dc=0;self.raw=bool(flags);self.finished=False;self.failed=False
  self.streams=[];self.events=[]
  if flags:
   if lengths!=[128*blocks,0,0,0] or any(counts):raise ValueError('AB38 raw syntax')
   self.raw_offset=H.size;return
  pos=H.size
  for size in lengths:
   if size<9:raise ValueError('AB38 stream bound')
   chunk=memoryview(packet)[pos:pos+size];pos+=size;k0,k1,bits=struct.unpack_from('<BBI',chunk)
   self.streams.append((k0,k1,frozen.ArithmeticReader(chunk[6:],bits)))
  kd,unused,_=self.streams[0]
  if kd>13 or unused!=255:raise ValueError('AB38 DC parameters')
  for (lo,hi),count,(kr,kv,reader) in zip(BANDS,counts,self.streams[1:],strict=True):
   if kr>19 or kv>11 or count>blocks*(hi-lo):raise ValueError('AB38 band parameters/count')
   # one pending nonzero position/value per AC band; no block-sized stream arrays
   event=dict(lo=lo,hi=hi,left=count,index=-1,value=0,kr=kr,kv=kv,reader=reader)
   self._advance(event);self.events.append(event)
 def _advance(self,event):
  if not event['left']:
   event['reader'].finish();event['index']=self.blocks*(event['hi']-event['lo']);event['value']=0;return
  event['index']+=event['reader'].rice(event['kr'],24)+1
  if event['index']>=self.blocks*(event['hi']-event['lo']):raise ValueError('AB38 run bound')
  value=frozen.signed(event['reader'].rice(event['kv'],12,True)+1)
  if not value or not -2048<=value<=2048:raise ValueError('AB38 level domain')
  event['value']=value;event['left']-=1
 def __iter__(self):return self
 def __next__(self):
  if self.failed:raise ValueError('failed coefficient iterator')
  if self.finished:raise StopIteration
  try:return self._next()
  except Exception:self.failed=True;raise
 def _next(self):
  if self.raw:
   offset=self.raw_offset+128*self.block;tile=np.frombuffer(self.packet,dtype='<i2',count=64,offset=offset).copy().reshape(8,8)
   if np.any(tile<-2048) or np.any(tile>2048):raise ValueError('AB38 raw coefficient range')
  else:
   tile=np.zeros((8,8),np.int16);flat=tile.reshape(-1);kd,_,reader=self.streams[0]
   if self.block%self.blocks_w==0:self.previous_dc=0
   self.previous_dc+=frozen.signed(reader.rice(kd,14))
   if not -2048<=self.previous_dc<=2048:raise ValueError('AB38 DC bounds')
   flat[0]=self.previous_dc
   for event in self.events:
    width=event['hi']-event['lo'];begin=self.block*width;end=begin+width
    while event['index']<end:
     if event['index']<begin:raise ValueError('AB38 cursor order')
     flat[frozen.ORDER[event['lo']+event['index']-begin]]=event['value'];self._advance(event)
  self.block+=1
  if self.block==self.blocks:
   if not self.raw:
    self.streams[0][2].finish()
    for e in self.events:
     if e['left'] or e['index']!=self.blocks*(e['hi']-e['lo']):raise ValueError('AB38 remaining event')
   self.finished=True
  return tile
 def logical_workspace(self):
  return dict(coefficient_tile_bytes=128,probability_state_bytes=0 if self.raw else 352,AC_pending_events=0 if self.raw else 3,
              retained_compressed_input_bytes=len(self.packet),full_coefficient_frame_staged=False,
              Python_heap_bytes_measured=False,target_memory_fit_proven=False)
