"""HC21 acknowledged display-only patch cache. No AR03/YUV state is touched."""
from pathlib import Path
import hashlib, importlib.util, struct, sys, time, zlib
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'python-game-mandatory-hud-study'))
# The frozen import tree uses several historic modules named model. Load this
# unique module explicitly instead of relying on a global model import.
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module
legacy=load('hc21_legacy_mandatory',HERE.parent/'python-game-mandatory-hud-study/model.py')
hd=load('hc21_delta',HERE.parent/'python-game-hud-delta-study/model.py')
RECTANGLES=legacy.RECTANGLES
HEADER=struct.Struct('<4sBIIIBBII16s16s4I4B')
ACK=struct.Struct('<4sBIIIB16s16s')
CRC=struct.Struct('<I')
NO_REF=255;INVALID=0xffffffff;ZERO=bytes(16);MAX_PACKET=49152
LEGACY,DELTA=0,1
WORDS=sum(w*h for x,y,w,h in RECTANGLES);BANK_BYTES=2*WORDS

def seal(body):return body+CRC.pack(zlib.crc32(body))
def sha(data):return hashlib.sha256(data).digest()[:16]
def tag(patches):
    h=hashlib.sha256()
    for rect,p in zip(RECTANGLES,patches):h.update(struct.pack('<4H',*rect));h.update(np.asarray(p,dtype='<u2').tobytes())
    return h.digest()[:16]
def check_id(value,*,epoch=False):
    if type(value)is not int or not (int(epoch)<=value<INVALID):raise ValueError('bounded epoch/frame/generation')
def extract(rgb):
    a=legacy.codec.gm.ft._check_rgb(rgb)
    if a.shape!=(480,720,3):raise ValueError('HC21 fixed canvas')
    return tuple(legacy.codec.corpus.rgb565(a[y:y+h,x:x+w]) for x,y,w,h in RECTANGLES)
def immutable(patches):
    out=[]
    for p in patches:
        p.setflags(write=False);out.append(p)
    return tuple(out)
def parse(packet):
    if type(packet)is not bytes or not HEADER.size+4<=len(packet)<=MAX_PACKET:raise ValueError('HC21 bounded bytes')
    if zlib.crc32(packet[:-4])!=CRC.unpack(packet[-4:])[0]:raise ValueError('HC21 CRC')
    fields=HEADER.unpack_from(packet)
    magic,version,epoch,frame,generation,dest,refslot,refframe,refgen,reftag,newtag,*rest=fields
    sizes,modes=rest[:4],rest[4:]
    if magic!=b'HC21' or version!=1:raise ValueError('HC21 version')
    for x in (frame,generation):check_id(x)
    check_id(epoch,epoch=True)
    if dest not in (0,1) or refslot not in (0,1,NO_REF) or newtag==ZERO:raise ValueError('HC21 slots/tag')
    if refslot==NO_REF:
        if (refframe,refgen,reftag)!=(INVALID,INVALID,ZERO) or dest!=0:raise ValueError('HC21 full identity')
    elif dest==refslot or refframe>=frame or refgen>=generation or reftag==ZERO:raise ValueError('HC21 reference identity')
    if any(m not in (LEGACY,DELTA) for m in modes) or any(n<=0 or n>MAX_PACKET for n in sizes):raise ValueError('HC21 patch types/length')
    if len(packet)!=HEADER.size+sum(sizes)+4:raise ValueError('HC21 exact body')
    pos=HEADER.size;pieces=[]
    for n in sizes:pieces.append(packet[pos:pos+n]);pos+=n
    return dict(epoch=epoch,frame=frame,generation=generation,dest=dest,refslot=refslot,refframe=refframe,refgen=refgen,reftag=reftag,newtag=newtag,sizes=sizes,modes=modes,pieces=pieces,bodytag=sha(packet))
def ack_for(m):return seal(ACK.pack(b'HA21',1,m['epoch'],m['frame'],m['generation'],m['dest'],m['bodytag'],m['newtag']))
def parse_ack(data):
    if type(data)is not bytes or len(data)!=ACK.size+4 or zlib.crc32(data[:-4])!=CRC.unpack(data[-4:])[0]:raise ValueError('HA21 length/CRC')
    magic,version,epoch,frame,generation,dest,bodytag,newtag=ACK.unpack(data[:-4])
    if magic!=b'HA21' or version!=1 or dest not in (0,1):raise ValueError('HA21 profile')
    check_id(epoch,epoch=True);check_id(frame);check_id(generation)
    return dict(epoch=epoch,frame=frame,generation=generation,dest=dest,bodytag=bodytag,newtag=newtag)

class Sender:
    def __init__(self,epoch=1):
        check_id(epoch,epoch=True);self.epoch=epoch;self.confirmed=None;self.pending=None;self.last_frame=-1;self.generation=0
        self.selector=legacy.ui.PatchSelector(rectangles=RECTANGLES)
    def prepare(self,rgb,frame):
        check_id(frame)
        if self.pending is not None:raise ValueError('unresolved HC21 transaction')
        if frame<=self.last_frame:raise ValueError('HC21 monotonic frame')
        current=extract(rgb);ref=self.confirmed;generation=self.generation+1;check_id(generation)
        selection=self.selector.select(rgb,MAX_PACKET*2)
        if len(selection.patches)!=4:raise ValueError('HC21 full legacy patch preparation')
        payload=[];modes=[];detail=[]
        for i,(full,words) in enumerate(zip(selection.patches,current)):
            delta=hd.encode(words,None if ref is None else ref['patches'][i])
            mode,data=(LEGACY,full) if len(full)<=len(delta) else (DELTA,delta)
            modes.append(mode);payload.append(data)
            detail.append(dict(kind='legacy' if mode==LEGACY else hd.inspect(delta)['mode'],legacy_bytes=len(full),delta_bytes=len(delta),selected_bytes=len(data)))
        dest=0 if ref is None else 1-ref['dest']
        newtag=tag(current)
        body=HEADER.pack(b'HC21',1,self.epoch,frame,generation,dest,NO_REF if ref is None else ref['dest'],INVALID if ref is None else ref['frame'],INVALID if ref is None else ref['generation'],ZERO if ref is None else ref['newtag'],newtag,*(len(p) for p in payload),*modes)+b''.join(payload)
        packet=seal(body)
        if len(packet)>MAX_PACKET:raise ValueError('HC21 complete cap')
        m=parse(packet);m['patches']=immutable(current);m['packet']=packet
        self.pending=m;self.last_frame=frame;self.generation=generation
        changed=WORDS if ref is None else sum(int(np.count_nonzero(a!=b)) for a,b in zip(current,ref['patches']))
        info=dict(frame=frame,generation=generation,legacy_patch_bytes=selection.used_bytes,sidecar_bytes=len(packet),ack_bytes=ACK.size+4,patches=detail,
            changed_words_vs_confirmed=changed,exact_words=WORDS,
            ref_read_bytes=sum(2*rect[2]*rect[3] for rect,mode,piece in zip(RECTANGLES,modes,payload)if mode==DELTA and hd.inspect(piece)['mode']!=hd.RAW),destination_write_bytes=BANK_BYTES,
            sender_pixel_bytes=BANK_BYTES*(1+int(ref is not None)),receiver_pixel_bank_bytes=2*BANK_BYTES,receiver_atomic_staging_bytes=BANK_BYTES,
            sender_legacy_cache_bytes=self.selector.cache.persistent_bytes(),sender_pending_packet_bytes=len(packet),
            scope='HC21 standalone; unchanged AR03 base not serialized here')
        return packet,info
    def retry(self):
        if self.pending is None:raise ValueError('nothing to retry')
        return self.pending['packet']
    def accept_ack(self,data):
        a=parse_ack(data);p=self.pending
        if p is None or a!={k:p[k] for k in a}:raise ValueError('HA21 exact outstanding identity')
        self.confirmed={k:p[k] for k in ('epoch','frame','generation','dest','newtag','patches')};self.pending=None
    def reset(self,epoch):
        check_id(epoch,epoch=True)
        if epoch<=self.epoch:raise ValueError('HC21 reset needs higher epoch')
        self.__init__(epoch)

class Receiver:
    def __init__(self,epoch=1):
        check_id(epoch,epoch=True);self.epoch=epoch;self.banks=[None,None];self.readers=[0,0];self.last_frame=-1;self.last_generation=0;self.last_bodytag=None;self.last_ack=None;self.display=None;self._leases={};self._next_lease=0
    def acquire(self,slot):
        if slot not in (0,1) or self.banks[slot]is None:raise ValueError('empty cache lease')
        if len(self._leases)>=8:raise ValueError('HC21 eight display-reader descriptors')
        if self._next_lease>=INVALID:raise ValueError('HC21 lease token exhausted; drain and reset epoch')
        self._next_lease+=1;lease=(self.epoch,slot,self.banks[slot]['generation'],self._next_lease)
        self._leases[lease]=slot;self.readers[slot]+=1;return lease
    def release(self,lease):
        if type(lease)is not tuple or lease not in self._leases:raise ValueError('invalid cache lease')
        slot=self._leases.pop(lease);self.readers[slot]-=1
    def receive(self,packet):
        m=parse(packet)
        if m['epoch']!=self.epoch:raise ValueError('HC21 epoch')
        if m['frame']==self.last_frame and m['generation']==self.last_generation and m['bodytag']==self.last_bodytag:return self.last_ack
        if m['frame']<=self.last_frame or m['generation']<=self.last_generation:raise ValueError('HC21 stale/reordered')
        if self.readers[m['dest']]:raise ValueError('HC21 destination has live scanout reader')
        ref=None if m['refslot']==NO_REF else self.banks[m['refslot']]
        if m['refslot']!=NO_REF and (ref is None or (ref['frame'],ref['generation'],ref['newtag'])!=(m['refframe'],m['refgen'],m['reftag'])):raise ValueError('HC21 missing exact reference')
        decoded=[]
        for i,(mode,piece,rect) in enumerate(zip(m['modes'],m['pieces'],RECTANGLES)):
            if mode==LEGACY:
                d=legacy.ui.validate_patches((piece,),720,480)[0]
                if tuple(d['rect'])!=rect:raise ValueError('HC21 declared legacy region')
                words=d['words']
            else:words=hd.decode(piece,None if ref is None else ref['patches'][i])
            if words.shape!=(rect[3],rect[2]) or words.dtype!=np.uint16:raise ValueError('HC21 patch geometry')
            decoded.append(words)
        if tag(decoded)!=m['newtag']:raise ValueError('HC21 decoded complete tag')
        # No mutation above this point. Full output/ACK publication is atomic.
        bank={k:m[k] for k in ('epoch','frame','generation','dest','newtag')};bank['patches']=immutable(decoded)
        ack=ack_for(m);self.banks[m['dest']]=bank;self.display=bank
        self.last_frame=m['frame'];self.last_generation=m['generation'];self.last_bodytag=m['bodytag'];self.last_ack=ack
        return ack
    def reset(self,epoch):
        check_id(epoch,epoch=True)
        if epoch<=self.epoch or any(self.readers):raise ValueError('HC21 reset requires later epoch and drained readers')
        self.__init__(epoch)
