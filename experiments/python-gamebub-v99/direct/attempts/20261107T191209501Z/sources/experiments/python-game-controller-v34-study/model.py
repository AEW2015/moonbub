"""GM34 hierarchical motion frame and unchanged GM27 fallback.

Decode expands vectors into the frozen raw-vector receive grammar, never the
motion encoder. The bounded internal compatibility packet is private scratch,
not transmitted wire bytes or a native streaming hardware implementation.
"""
from pathlib import Path
import importlib.util
import struct
import sys
import zlib
from dataclasses import dataclass
import numpy as np
HERE=Path(__file__).resolve().parent

def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m

runtime=load('frame34_runtime28',HERE.parent/'python-game-runtime-v28-study/model.py')
hierarchy=load('frame34_hierarchy',HERE.parent/'python-game-hierarchy-v34-study/model.py')
motion_decoder=load('frame34_hierarchy_decoder',HERE.parent/'python-game-hierarchy-v34-study/decoder.py')
HEADER=runtime.HEADER
NO_REF=runtime.NO_REF
MAX_WIRE=49152
MAGIC=b'GM34'
roi,_id=runtime.roi,runtime._id

def seal(body):return body+struct.pack('<I',zlib.crc32(body))

_OWNER=object()
@dataclass(frozen=True)
class Motion:
    owner:object
    width:int
    height:int
    child:bytes
    packet:bytes

def prepare_motion(parent,child,width,height):
    packet,info=hierarchy.pack(parent,child,width,height,return_info=True)
    decoded=motion_decoder.unpack(packet,width,height)
    if not np.array_equal(decoded,child):raise ValueError('HM34 encoder verification')
    return Motion(_OWNER,width,height,child.tobytes(),packet),{k:v for k,v in info.items() if k!='parent'}

def wrap(packet,motion):
    """Serialize actual GM34 bytes using a paid, private motion preparation."""
    meta=runtime.parse_metadata(packet)
    if meta['key'] or meta['block_size']!=16:raise ValueError('GM34 P child16 only')
    if not isinstance(motion,Motion) or motion.owner is not _OWNER or (motion.width,motion.height)!=(meta['width'],meta['height']):raise ValueError('owned HM34 preparation/geometry')
    start=HEADER.size+meta['qmap_bytes'];nv=meta['vector_bytes']
    child=runtime.base.unpack_vectors(packet[start:start+nv],(motion.width+15)//16,(motion.height+15)//16)
    if child.tobytes()!=motion.child:raise ValueError('GM34 exact child field binding')
    fields=list(HEADER.unpack_from(packet));fields[0]=MAGIC;fields[13]=len(motion.packet)
    return seal(HEADER.pack(*fields)+packet[HEADER.size:start]+motion.packet+packet[start+nv:-4])

def promote(packet,parent_vectors):
    """Try actual hierarchical bytes; existing GM27 wins a length tie."""
    meta=runtime.parse_metadata(packet)
    if meta['key']:return packet,dict(selected='GM27',old_bytes=len(packet),new_bytes=len(packet),key=True)
    if meta['block_size']!=16:raise ValueError('GM34 child block size16')
    w,h=meta['width'],meta['height'];start=HEADER.size+meta['qmap_bytes'];nv=meta['vector_bytes']
    child=runtime.base.unpack_vectors(packet[start:start+nv],(w+15)//16,(h+15)//16)
    motion,info=prepare_motion(parent_vectors,child,w,h)
    hm=motion.packet;candidate=wrap(packet,motion)
    selected=candidate if len(candidate)<len(packet) else packet
    return selected,dict(selected=selected[:4].decode(),old_bytes=len(packet),new_bytes=len(selected),
                         candidate_bytes=len(candidate),old_motion_bytes=nv,hierarchical_motion_bytes=len(hm),
                         key=False,component={k:v for k,v in info.items() if k!='parent'})

def _expand(packet,expected_epoch=None):
    if type(packet)is not bytes or not HEADER.size+7<=len(packet)<=MAX_WIRE:raise ValueError('GM34 bounded immutable bytes')
    if packet[:4]==b'GM27':
        return packet,dict(wire_magic='GM27',wire_bytes=len(packet),internal_compatibility_bytes=len(packet))
    if packet[:4]!=MAGIC or zlib.crc32(packet[:-4])!=struct.unpack('<I',packet[-4:])[0]:raise ValueError('GM34 profile/CRC')
    f=list(HEADER.unpack_from(packet));magic,version,flags,epoch,fid,rid,w,h,bs,limit,reftag,tag,nq,nv,ny,nu,nvv=f
    roi.geometry(w,h)
    if version!=1 or flags!=0 or bs!=16 or limit!=18 or not _id(epoch) or not _id(fid):raise ValueError('GM34 P profile/identity')
    if expected_epoch is not None and epoch!=expected_epoch:raise ValueError('GM34 epoch')
    if not _id(rid) or rid>=fid or reftag==bytes(16) or tag==bytes(16):raise ValueError('GM34 past reference/tag')
    if nq!=(((w+15)//16)*((h+15)//16)+3)//4 or not 1<=nv<=MAX_WIRE:raise ValueError('GM34 map lengths')
    if min(ny,nu,nvv)<1 or len(packet)!=HEADER.size+nq+nv+ny+nu+nvv+4:raise ValueError('GM34 exact lengths')
    start=HEADER.size+nq;vectors=motion_decoder.unpack(packet[start:start+nv],w,h)
    # GM27 mode1 is literal signed dx/dy per child block. No pack_vectors,
    # motion search, minimum-size oracle or canonical encoder is called here.
    raw=b'\x01'+vectors.tobytes();f[0]=b'GM27';f[13]=len(raw)
    compat=seal(HEADER.pack(*f)+packet[HEADER.size:start]+raw+packet[start+nv:-4])
    runtime.parse_metadata(compat,expected_epoch=expected_epoch)
    return compat,dict(wire_magic='GM34',wire_bytes=len(packet),wire_vector_bytes=nv,
                       internal_raw_vector_bytes=len(raw),internal_compatibility_bytes=len(compat))

def parse_metadata(packet,*,expected_epoch=None):
    compat,detail=_expand(packet,expected_epoch);meta=runtime.parse_metadata(compat,expected_epoch=expected_epoch)
    meta.update(detail)
    if packet[:4]==MAGIC:meta['vector_bytes']=detail['wire_vector_bytes']
    return meta

def parse(packet,*,expected_epoch=None):
    compat,detail=_expand(packet,expected_epoch);meta=runtime.parse(compat,expected_epoch=expected_epoch)
    meta.update(detail)
    if packet[:4]==MAGIC:meta['vector_bytes']=detail['wire_vector_bytes']
    return meta

def decode(packet,reference=None,*,expected_epoch=None,expected_reference_id=None):
    compat,detail=_expand(packet,expected_epoch)
    pixels,meta=runtime.decode(compat,reference,expected_epoch=expected_epoch,expected_reference_id=expected_reference_id)
    meta.update(detail)
    if packet[:4]==MAGIC:meta['vector_bytes']=detail['wire_vector_bytes']
    return pixels,meta
