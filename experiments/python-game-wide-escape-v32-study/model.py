"""Prospective WV32 motion component: frozen narrow syntax plus sparse escapes.
This is not a GM27 frame and does not change any existing decoder limit.
"""
from pathlib import Path
import importlib.util,sys,struct,zlib,time
import numpy as np
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('escape32_frozen27',HERE.parent/'python-game-unified-v27-study/model.py')
frozen=importlib.util.module_from_spec(s);sys.modules[s.name]=frozen;s.loader.exec_module(frozen)
HEADER=struct.Struct('<4sHHHHI');ENTRY=struct.Struct('<Hbb');MAGIC=b'WV32';LIMIT=68

def _geometry(mw,mh):
 return frozen.motion_decoder._geometry(mw,mh)

def pack(vectors,return_work=False):
 started=time.perf_counter_ns();a=np.asarray(vectors)
 if a.dtype!=np.int8 or a.ndim!=3 or a.shape[2]!=2:raise ValueError('int8 motion map')
 mh,mw=a.shape[:2];n=_geometry(mw,mh)
 if np.any(np.abs(a.astype(np.int16))>LIMIT):raise ValueError('wide vector bound')
 flat=a.reshape(n,2);escaped=np.any(np.abs(flat.astype(np.int16))>18,axis=1)
 base=a.copy();base.reshape(n,2)[escaped]=0
 narrow,nwork=frozen.pack_vectors(base,return_work=True)
 entries=b''.join(ENTRY.pack(int(i),*map(int,flat[i])) for i in np.flatnonzero(escaped))
 prefix=struct.pack('<4sHHHH',MAGIC,mw,mh,len(narrow),int(escaped.sum()))
 body=narrow+entries;packet=prefix+struct.pack('<I',zlib.crc32(prefix+body)&0xffffffff)+body
 work=dict(bytes=len(packet),header_bytes=HEADER.size,narrow_bytes=len(narrow),escape_count=int(escaped.sum()),escape_bytes=len(entries),narrow_pack_work=nwork,pack_ms=(time.perf_counter_ns()-started)/1e6)
 return (packet,work) if return_work else packet

def unpack(data):
 """Bounded independent parser; never invokes the encoder or minimality search."""
 if type(data)is not bytes or len(data)<HEADER.size:raise ValueError('WV32 header')
 magic,mw,mh,nb,count,crc=HEADER.unpack_from(data);n=_geometry(mw,mh)
 if magic!=MAGIC or not 1<=nb<=1+2*n or count>n:raise ValueError('WV32 header bounds')
 if len(data)!=HEADER.size+nb+ENTRY.size*count:raise ValueError('WV32 exact length')
 if zlib.crc32(data[:12]+data[16:])&0xffffffff!=crc:raise ValueError('WV32 CRC')
 a=frozen.unpack_vectors(data[16:16+nb],mw,mh).copy();flat=a.reshape(n,2);previous=-1
 for offset in range(16+nb,len(data),ENTRY.size):
  index,dx,dy=ENTRY.unpack_from(data,offset)
  if not previous<index<n:raise ValueError('WV32 escape order/index')
  if max(abs(dx),abs(dy))>LIMIT or max(abs(dx),abs(dy))<=18:raise ValueError('WV32 escape domain')
  if np.any(flat[index]):raise ValueError('WV32 escaped base must be zero')
  flat[index]=dx,dy;previous=index
 return a
