"""GF01 laboratory chunk framing; not the installed JPEG/MSV1 transport.

Fixed canonical chunks permit bounded reordering/duplicate checks. Only a fully
reassembled CRC-checked frame is returned. Decode/reference ACK is external;
call commit only after a matching codec receiver accepts that exact frame.
"""
from dataclasses import dataclass
import math
import struct
import zlib

HEADER=struct.Struct('!4sBIIIHHHI')
MAX_FRAME=49152
PAYLOAD=1024
NO_ID=0xffffffff


def _identity(value):
    return type(value) is int and 0<=value<NO_ID


def datagrams(data,epoch,frame,*,max_frame=MAX_FRAME):
    if type(data) is not bytes or type(max_frame) is not int or not 1<=max_frame<=MAX_FRAME or not 0<len(data)<=max_frame or not _identity(epoch) or not _identity(frame):
        raise ValueError('GF01 identity/frame bound')
    count=math.ceil(len(data)/PAYLOAD);checksum=zlib.crc32(data)
    return [HEADER.pack(b'GF01',1,epoch,frame,len(data),i,count,len(data[i*PAYLOAD:(i+1)*PAYLOAD]),checksum)+data[i*PAYLOAD:(i+1)*PAYLOAD]
            for i in range(count)]


@dataclass(frozen=True)
class Complete:
    epoch:int
    frame:int
    data:bytes


class Reassembler:
    def __init__(self,epoch=1,*,slots=2,max_frame=MAX_FRAME,timeout_ms=150):
        if not _identity(epoch) or type(slots) is not int or not 1<=slots<=2 or type(max_frame) is not int or not 1<=max_frame<=MAX_FRAME or not math.isfinite(timeout_ms) or timeout_ms<=0:
            raise ValueError('GF01 configuration')
        self.epoch=epoch;self.slot_limit=slots;self.max_frame=max_frame;self.timeout_ms=timeout_ms
        self.pending={};self.committed=-1;self.now=-math.inf;self.peak_payload_bytes=0;self.peak_slots=0

    def expire(self,now_ms):
        if not math.isfinite(now_ms) or now_ms<self.now:raise ValueError('GF01 monotonic time')
        self.now=now_ms
        expired=[frame for frame,row in self.pending.items() if 'complete' not in row and now_ms-row['began']>=self.timeout_ms]
        for frame in expired:del self.pending[frame]
        return expired

    def feed(self,packet,now_ms):
        self.expire(now_ms)
        if type(packet) is not bytes or len(packet)<HEADER.size:
            raise ValueError('GF01 truncated/type')
        magic,version,epoch,frame,total,index,count,length,checksum=HEADER.unpack_from(packet)
        if (magic!=b'GF01' or version!=1 or epoch!=self.epoch or not _identity(frame) or frame<=self.committed
            or not 0<total<=self.max_frame or count!=math.ceil(total/PAYLOAD) or not 0<=index<count
            or length!=min(PAYLOAD,total-index*PAYLOAD) or len(packet)!=HEADER.size+length):
            raise ValueError('GF01 header/geometry/session/replay')
        metadata=(total,count,checksum)
        row=self.pending.get(frame)
        if row is None:
            if len(self.pending)>=self.slot_limit:raise ValueError('GF01 busy')
            row={'metadata':metadata,'data':bytearray(total),'seen':set(),'began':now_ms}
            self.pending[frame]=row
            self.peak_payload_bytes=max(self.peak_payload_bytes,sum(len(r['data']) for r in self.pending.values()))
            self.peak_slots=max(self.peak_slots,len(self.pending))
        elif row['metadata']!=metadata:
            del self.pending[frame]
            raise ValueError('GF01 inconsistent frame metadata')
        offset=index*PAYLOAD;payload=packet[HEADER.size:]
        if index in row['seen']:
            if row['data'][offset:offset+length]!=payload:
                del self.pending[frame]
                raise ValueError('GF01 conflicting duplicate')
            return None
        row['data'][offset:offset+length]=payload;row['seen'].add(index)
        if len(row['seen'])!=count:return None
        data=bytes(row['data'])
        if zlib.crc32(data)!=checksum:
            del self.pending[frame]
            raise ValueError('GF01 complete CRC')
        row['data']=data
        row['complete']=Complete(epoch,frame,data)
        return row['complete']

    def _owned(self,completed):
        if not isinstance(completed,Complete) or completed.epoch!=self.epoch:
            raise ValueError('GF01 stale/foreign completion')
        row=self.pending.get(completed.frame)
        if row is None or row.get('complete') is not completed:
            raise ValueError('GF01 unowned completion')
        return row

    def commit(self,completed):
        # Decode/read completion releases the exact delivered slot. Older
        # delivered readers remain pinned; only older partial assembly is safe
        # to discard here. This is not authentication or a serialized wire ACK.
        self._owned(completed)
        if completed.frame<=self.committed:raise ValueError('GF01 stale decode commit')
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
        if not _identity(epoch):raise ValueError('GF01 reset epoch')
        if any('complete' in row for row in self.pending.values()):
            raise ValueError('GF01 delivered readers must drain before reset')
        self.epoch=epoch;self.pending.clear();self.committed=-1

    def payload_bytes(self):return sum(len(row['data']) for row in self.pending.values())
