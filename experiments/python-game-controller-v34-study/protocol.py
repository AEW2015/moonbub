"""CP34 host reference: bounded fixed-HUD profile and atomic base/HUD commit."""
from pathlib import Path
from dataclasses import dataclass
import hashlib
import importlib.util
import struct
import sys
import zlib
HERE=Path(__file__).resolve().parent

def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m

base=load('cp34_frame',HERE/'model.py')
# The frozen decoder uses one basename import. Bind it only during module load
# and restore the caller's import table; all decoder references are then local.
_missing=object();_previous=sys.modules.get('baseline',_missing)
try:
    sys.modules['baseline']=load('cp34_hud_baseline',HERE.parent/'python-game-hud-runs-v33-study/baseline.py')
    hud=load('cp34_hud33',HERE.parent/'python-game-hud-runs-v33-study/decoder.py')
finally:
    if _previous is _missing:sys.modules.pop('baseline',None)
    else:sys.modules['baseline']=_previous
CAP,MAX_HUD_WORDS,NO_SLOT=49152,21120,255
NO_REF=base.NO_REF
PAIR=struct.Struct('<4sBBIIBBII16s16s')
ACK=struct.Struct('<4sBII16s16s16s')
KEY,PUBLISH=1,2

def seal(body):return body+struct.pack('<I',zlib.crc32(body))
def digest(data):return hashlib.sha256(data).digest()[:16]
def checked(data,minimum,maximum,label):
    if type(data)is not bytes or not minimum<=len(data)<=maximum:raise ValueError(label+' bounded bytes')
    if zlib.crc32(data[:-4])!=struct.unpack('<I',data[-4:])[0]:raise ValueError(label+' CRC')

def parse_hud(packet):
    checked(packet,hud.p.HUD.size+4,CAP,'CP34 HUD')
    meta=hud._meta(packet)
    if sum(w*h for x,y,w,h in meta['rectangles'])>MAX_HUD_WORDS:raise ValueError('CP34 fixed-HUD word budget')
    # Validate inner geometry before any legacy decoder allocates pixel arrays.
    for rect,kind,payload in zip(meta['rectangles'],meta['types'],meta['payloads'],strict=True):
        if kind==1:
            if hud.p.ui._header(payload,meta['width'],meta['height'])!=rect:raise ValueError('CP34 full-patch rectangle')
        else:
            checked(payload,hud.h.HEADER.size+4,CAP,'CP34 HUD patch')
            magic,version,mode,w,h,length,ref,tag=hud.h.HEADER.unpack_from(payload)
            if magic!={2:b'HD25',3:b'HS32',4:b'HS33'}[kind] or version!=1 or (w,h)!=(rect[2],rect[3]):raise ValueError('CP34 inner patch geometry/profile')
            if len(payload)!=hud.h.HEADER.size+length+4:raise ValueError('CP34 inner patch length')
    return meta

def parse_pair(packet):
    checked(packet,PAIR.size+base.HEADER.size+hud.p.HUD.size+12,CAP,'CP34')
    magic,version,flags,epoch,fid,source,dest,nb,nh,bt,ht=PAIR.unpack_from(packet)
    if magic!=b'CP34' or version!=1 or flags not in (KEY|PUBLISH,PUBLISH) or not base._id(epoch) or not base._id(fid):raise ValueError('CP34 published profile/identity')
    key=bool(flags&KEY)
    if key and (source!=NO_SLOT or dest!=0) or not key and (source not in (0,1) or dest!=1-source):raise ValueError('CP34 bank rule')
    if nb<base.HEADER.size+7 or nh<hud.p.HUD.size+4 or len(packet)!=PAIR.size+nb+nh+4:raise ValueError('CP34 exact inner lengths')
    b,h=packet[PAIR.size:PAIR.size+nb],packet[PAIR.size+nb:-4]
    if digest(b)!=bt or digest(h)!=ht:raise ValueError('CP34 component SHA binding')
    bm,hm=base.parse_metadata(b,expected_epoch=epoch),parse_hud(h)
    if bm['frame_id']!=fid or hm['frame_id']!=fid or hm['epoch']!=epoch or bm['key']!=key or (bm['width'],bm['height'])!=(hm['width'],hm['height']):raise ValueError('CP34 coherent identities')
    if key and hm['reference_id']!=NO_REF:raise ValueError('CP34 independent HUD key')
    if not key and hm['reference_id']!=bm['reference_id']:raise ValueError('CP34 shared accepted frame identity')
    return dict(epoch=epoch,frame_id=fid,key=key,publish=True,source_slot=source,destination_slot=dest,
                base=b,hud=h,base_meta=bm,hud_meta=hm,pair_tag=digest(packet))

def encode_pair(b,h,*,epoch,frame_id,source_slot=NO_SLOT,destination_slot=0,key=True):
    if type(key)is not bool or type(source_slot)is not int or type(destination_slot)is not int or not 0<=source_slot<=255 or not 0<=destination_slot<=255:raise ValueError('CP34 declared flags/slots')
    if type(b)is not bytes or type(h)is not bytes:raise ValueError('CP34 immutable components')
    packet=seal(PAIR.pack(b'CP34',1,PUBLISH|(KEY if key else 0),epoch,frame_id,source_slot,destination_slot,len(b),len(h),digest(b),digest(h))+b+h)
    parse_pair(packet);return packet

def validate_ack(ack,pair):
    checked(ack,ACK.size+4,ACK.size+4,'JA34');meta=parse_pair(pair)
    magic,version,epoch,fid,pt,bt,ht=ACK.unpack_from(ack)
    if (magic,version,epoch,fid,pt,bt,ht)!=(b'JA34',1,meta['epoch'],meta['frame_id'],meta['pair_tag'],meta['base_meta']['reconstructed_tag'],meta['hud_meta']['reconstructed_tag']):raise ValueError('JA34 exact pair/output binding')
    return dict(epoch=epoch,frame_id=fid,pair_tag=pt.hex(),base_tag=bt.hex(),hud_tag=ht.hex(),destination_slot=meta['destination_slot'])

@dataclass(frozen=True)
class Bank:
    frame_id:int
    tag:bytes
    planes:tuple

class Receiver:
    def __init__(self,epoch=25,width=720,height=480):
        if not base._id(epoch):raise ValueError('CP34 epoch')
        base.roi.geometry(width,height);self.epoch,self.width,self.height=epoch,width,height
        self.banks=(None,None);self.hud=();self.hud_id=NO_REF;self.last_frame_id=-1;self.last_ack=None

    def receive(self,pair,*,write_drained=True,vblank=True):
        if type(write_drained)is not bool or type(vblank)is not bool or not write_drained or not vblank:raise ValueError('CP34 modeled publication gates')
        meta=parse_pair(pair);bm=meta['base_meta']
        if meta['epoch']!=self.epoch or meta['frame_id']<=self.last_frame_id or (bm['width'],bm['height'])!=(self.width,self.height):raise ValueError('CP34 epoch/monotonic canvas')
        if meta['key']:reference=None;rid=None;hudref=None;hudrid=None
        else:
            bank=self.banks[meta['source_slot']]
            if bank is None or bank.frame_id!=bm['reference_id'] or bank.tag!=bm['reference_tag']:raise ValueError('CP34 actual source-bank identity')
            reference,rid,hudref,hudrid=bank.planes,bank.frame_id,self.hud,self.hud_id
        pixels,_=base.decode(meta['base'],reference,expected_epoch=self.epoch,expected_reference_id=rid)
        patches,hm=hud.decode_hud(meta['hud'],hudref,expected_epoch=self.epoch,expected_reference_id=hudrid)
        ack=seal(ACK.pack(b'JA34',1,self.epoch,meta['frame_id'],meta['pair_tag'],bm['reconstructed_tag'],hm['reconstructed_tag']))
        # All parsing, staged decode and ACK construction precede publication.
        banks=[None,None] if meta['key'] else list(self.banks)
        banks[meta['destination_slot']]=Bank(meta['frame_id'],bm['reconstructed_tag'],pixels)
        self.banks,self.hud,self.hud_id,self.last_frame_id,self.last_ack=tuple(banks),patches,meta['frame_id'],meta['frame_id'],ack
        return pixels,patches,ack
