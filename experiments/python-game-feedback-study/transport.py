"""GF02 laboratory chunks and GA01 decoded-frame feedback.

GF02 adds a GM01-body content tag to GF01. Delivered read pins survive all
conflicting metadata/duplicate errors. No firmware/network/hardware is implied.
"""
from dataclasses import dataclass
import math
import struct
import zlib

HEADER=struct.Struct('!4sBIIIHHHII')
MAX_FRAME=49152
PAYLOAD=1024
NO_ID=0xffffffff


def _identity(value):
    return type(value) is int and 0<=value<NO_ID


def datagrams(data,epoch,frame,*,max_frame=MAX_FRAME):
    if type(data) is not bytes or type(max_frame) is not int or not 1<=max_frame<=MAX_FRAME or not 0<len(data)<=max_frame or not _identity(epoch) or not _identity(frame):
        raise ValueError('GF02 identity/frame bound')
    count=math.ceil(len(data)/PAYLOAD);checksum=zlib.crc32(data);tag=content_crc(data)
    return [HEADER.pack(b'GF02',2,epoch,frame,len(data),i,count,len(data[i*PAYLOAD:(i+1)*PAYLOAD]),checksum,tag)+data[i*PAYLOAD:(i+1)*PAYLOAD]
            for i in range(count)]


@dataclass(frozen=True)
class Complete:
    epoch:int
    frame:int
    data:bytes
    frame_crc:int=0


class Reassembler:
    def __init__(self,epoch=1,*,slots=2,max_frame=MAX_FRAME,timeout_ms=150):
        if not _identity(epoch) or type(slots) is not int or not 1<=slots<=2 or type(max_frame) is not int or not 1<=max_frame<=MAX_FRAME or not math.isfinite(timeout_ms) or timeout_ms<=0:
            raise ValueError('GF02 configuration')
        self.epoch=epoch;self.slot_limit=slots;self.max_frame=max_frame;self.timeout_ms=timeout_ms
        self.pending={};self.committed=-1;self.now=-math.inf;self.peak_payload_bytes=0;self.peak_slots=0

    def expire(self,now_ms):
        if not math.isfinite(now_ms) or now_ms<self.now:raise ValueError('GF02 monotonic time')
        self.now=now_ms
        expired=[frame for frame,row in self.pending.items() if 'complete' not in row and now_ms-row['began']>=self.timeout_ms]
        for frame in expired:del self.pending[frame]
        return expired

    def feed(self,packet,now_ms):
        self.expire(now_ms)
        if type(packet) is not bytes or len(packet)<HEADER.size:
            raise ValueError('GF02 truncated/type')
        magic,version,epoch,frame,total,index,count,length,checksum,tag=HEADER.unpack_from(packet)
        if (magic!=b'GF02' or version!=2 or epoch!=self.epoch or not _identity(frame) or frame<=self.committed
            or not 0<total<=self.max_frame or count!=math.ceil(total/PAYLOAD) or not 0<=index<count
            or length!=min(PAYLOAD,total-index*PAYLOAD) or len(packet)!=HEADER.size+length):
            raise ValueError('GF02 header/geometry/session/replay')
        metadata=(total,count,checksum,tag)
        row=self.pending.get(frame)
        if row is None:
            if len(self.pending)>=self.slot_limit:raise ValueError('GF02 busy')
            row={'metadata':metadata,'data':bytearray(total),'seen':set(),'began':now_ms}
            self.pending[frame]=row
            self.peak_payload_bytes=max(self.peak_payload_bytes,sum(len(r['data']) for r in self.pending.values()))
            self.peak_slots=max(self.peak_slots,len(self.pending))
        elif row['metadata']!=metadata:
            if 'complete' not in row:del self.pending[frame]
            raise ValueError('GF02 inconsistent frame metadata')
        offset=index*PAYLOAD;payload=packet[HEADER.size:]
        if index in row['seen']:
            if row['data'][offset:offset+length]!=payload:
                if 'complete' not in row:del self.pending[frame]
                raise ValueError('GF02 conflicting duplicate')
            return None
        row['data'][offset:offset+length]=payload;row['seen'].add(index)
        if len(row['seen'])!=count:return None
        data=bytes(row['data'])
        if zlib.crc32(data)!=checksum or content_crc(data)!=tag:
            del self.pending[frame]
            raise ValueError('GF02 complete CRC')
        row['data']=data
        row['complete']=Complete(epoch,frame,data,tag)
        return row['complete']

    def _owned(self,completed):
        if not isinstance(completed,Complete) or completed.epoch!=self.epoch:
            raise ValueError('GF02 stale/foreign completion')
        row=self.pending.get(completed.frame)
        if row is None or row.get('complete') is not completed:
            raise ValueError('GF02 unowned completion')
        return row

    def commit(self,completed):
        # Decode/read completion releases the exact delivered slot. Older
        # delivered readers remain pinned; only older partial assembly is safe
        # to discard here. This is not authentication or a serialized wire ACK.
        self._owned(completed)
        if completed.frame<=self.committed:raise ValueError('GF02 stale decode commit')
        del self.pending[completed.frame]
        self.committed=completed.frame
        obsolete=[frame for frame,row in self.pending.items() if frame<=self.committed and 'complete' not in row]
        for frame in obsolete:del self.pending[frame]
        return obsolete

    def reject(self,completed):
        # Explicitly signals that a rejected/obsolete decoder finished reading.
        self._owned(completed)
        del self.pending[completed.frame]

    def reset(self,epoch):
        if not _identity(epoch):raise ValueError('GF02 reset epoch')
        if any('complete' in row for row in self.pending.values()):
            raise ValueError('GF02 delivered readers must drain before reset')
        self.epoch=epoch;self.pending.clear();self.committed=-1

    def payload_bytes(self):return sum(len(row['data']) for row in self.pending.values())


ACK=0
NACK=1
FEEDBACK=struct.Struct('!4sBBHIII')
FEEDBACK_SIZE=FEEDBACK.size+4


def content_crc(data):
    """GM01 body CRC, excluding its trailing little-endian CRC field.

    CRC32 of a complete valid GM01 frame is a fixed residue and cannot serve
    as a content-specific tag. The tag below matches the parsed body/footer.
    This is a checksum binding, not an authentication mechanism.
    """
    if type(data) is not bytes:raise ValueError('expected immutable frame bytes')
    return zlib.crc32(data[:-4])


@dataclass(frozen=True)
class Feedback:
    epoch:int
    frame:int
    status:int
    reason:int
    frame_crc:int


def _feedback_fields(epoch,frame,status,frame_crc,reason):
    if (not _identity(epoch) or not _identity(frame) or type(status) is not int or status not in (ACK,NACK)
        or type(frame_crc) is not int or not 0<=frame_crc<=0xffffffff
        or type(reason) is not int or not 0<=reason<=7 or (status==ACK and reason!=0) or (status==NACK and reason==0)):
        raise ValueError('GA01 fields')


def feedback_datagram(epoch,frame,status=ACK,frame_crc=0,reason=0):
    _feedback_fields(epoch,frame,status,frame_crc,reason)
    body=FEEDBACK.pack(b'GA01',1,status,reason,epoch,frame,frame_crc)
    return body+struct.pack('!I',zlib.crc32(body))


def parse_feedback(data):
    if type(data) is not bytes or len(data)!=FEEDBACK_SIZE:raise ValueError('GA01 exact length/type')
    magic,version,status,reason,epoch,frame,tag=FEEDBACK.unpack_from(data)
    if magic!=b'GA01' or version!=1 or zlib.crc32(data[:-4])!=struct.unpack('!I',data[-4:])[0]:
        raise ValueError('GA01 profile/CRC')
    _feedback_fields(epoch,frame,status,tag,reason)
    return Feedback(epoch,frame,status,reason,tag)


def matches_feedback(feedback,epoch,frame,frame_crc):
    return (isinstance(feedback,Feedback) and feedback.epoch==epoch and feedback.frame==frame
            and feedback.frame_crc==frame_crc)
