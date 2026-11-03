"""AA01 actual-byte asynchronous reference-only key experiment.

Control transaction IDs and visible capture IDs are separate. A key installs
an anchor but never presents pixels; displays name an immutable ACKed anchor.
There are at most two persistent anchors, two display credits, and one control
transaction. Retirement requires all old display ACKs AND physical reads to
drain. Key retries resend the same exact bytes; they cannot create a third key.
This is a Python protocol oracle, not a device/control implementation.
"""
from pathlib import Path
import hashlib
import struct
import sys
import zlib

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'python-motion-study'))
import motion_codec as mt

KEY,DISPLAY,RETIRE=1,2,3
HEADER=struct.Struct('<4sBBIIIIII')
CRC=struct.Struct('<I')
NONE=mt.NO_REF
MAX_PACKET=1_100_100


def pack(kind,epoch,tx,anchor,capture,keep,payload=b''):
    head=HEADER.pack(b'AA01',1,kind,epoch,tx,anchor,capture,keep,len(payload))
    body=head+payload
    return body+CRC.pack(zlib.crc32(body))


def parse(packet):
    if not isinstance(packet,bytes) or not HEADER.size+4<=len(packet)<=MAX_PACKET:
        raise ValueError('async packet bound')
    magic,version,kind,epoch,tx,anchor,capture,keep,size=HEADER.unpack_from(packet)
    if magic!=b'AA01' or version!=1 or kind not in (KEY,DISPLAY,RETIRE) or epoch==NONE or tx==NONE:
        raise ValueError('async profile/identity')
    if len(packet)!=HEADER.size+size+4 or zlib.crc32(packet[:-4])!=CRC.unpack(packet[-4:])[0]:
        raise ValueError('async length/CRC')
    if kind in (KEY,DISPLAY) and (capture==NONE or keep!=NONE or not size):
        raise ValueError('async image descriptor')
    if kind==RETIRE and (capture!=NONE or keep==NONE or anchor==NONE or not anchor<keep<tx or size):
        raise ValueError('async retirement descriptor')
    return dict(kind=kind,epoch=epoch,tx=tx,anchor=anchor,capture=capture,keep=keep,
                payload=packet[HEADER.size:-4])


class Encoder:
    def __init__(self,epoch=1,window=2):
        if type(epoch) is not int or not 0<=epoch<NONE or type(window) is not int or not 1<=window<=2:
            raise ValueError('bounded epoch/window')
        self.epoch,self.window=epoch,window
        self.anchors={};self.active=None;self.candidate=None;self.retiring=None
        self.pending={};self.readers={};self.next_tx=1;self.last_capture=-1
        self.peak_anchors=0;self.peak_display_credits=0

    def _tx(self):
        if self.next_tx>=NONE:raise ValueError('transaction sequence exhausted')
        value=self.next_tx;self.next_tx+=1;return value

    def _check_capture(self,capture):
        if type(capture) is not int or not 0<=capture<NONE:raise ValueError('capture ID')

    def can_key(self):
        return self.candidate is None and self.retiring is None and len(self.anchors)<2

    def can_display(self):
        return self.active is not None and sum(r['kind']==DISPLAY for r in self.pending.values())<self.window

    def prepare_key(self,rgb,capture,quant_scale=8):
        self._check_capture(capture)
        if not self.can_key():raise ValueError('candidate/retirement capacity')
        tx=self._tx();scratch=mt.Encoder(self.epoch)
        payload=scratch.prepare(rgb,tx,quant_scale=quant_scale,force_key=True)
        packet=pack(KEY,self.epoch,tx,tx,capture,NONE,payload)
        self.anchors[tx]=scratch._pending[1]
        self.candidate=tx
        self.pending[tx]=dict(kind=KEY,anchor=tx,packet=packet,
                              expected=hashlib.sha256(scratch.prepared_rgb().tobytes()).hexdigest())
        self.peak_anchors=max(self.peak_anchors,len(self.anchors))
        return packet

    def discard_unsent_key(self,tx):
        if tx!=self.candidate:raise ValueError('not candidate')
        self.pending.pop(tx);self.anchors.pop(tx);self.candidate=None

    def retry_key(self):
        if self.candidate is None:raise ValueError('no candidate')
        return self.pending[self.candidate]['packet']

    def prepare_display(self,rgb,capture,quant_scale=8,mode='global'):
        self._check_capture(capture)
        if not self.can_display() or capture<=self.last_capture:raise ValueError('display credits/order')
        source=mt.ft._check_rgb(rgb)
        if self.anchors[self.active][0].shape!=source.shape[:2]:raise ValueError('display requires matching anchor geometry')
        tx=self._tx();scratch=mt.Encoder(self.epoch)
        scratch.reference_id,scratch._reference=self.active,self.anchors[self.active]
        payload=scratch.prepare(rgb,tx,quant_scale=quant_scale,mode=mode)
        packet=pack(DISPLAY,self.epoch,tx,self.active,capture,NONE,payload)
        self.pending[tx]=dict(kind=DISPLAY,anchor=self.active,
                             expected=hashlib.sha256(scratch.prepared_rgb().tobytes()).hexdigest())
        self.readers[tx]=self.active;self.last_capture=capture
        self.peak_display_credits=max(self.peak_display_credits,sum(r['kind']==DISPLAY for r in self.pending.values()))
        return packet

    def expected_hash(self,tx):return self.pending[tx]['expected']

    def mark_drained(self,tx):self.readers.pop(tx,None)

    def can_retire(self):
        old=self.retiring
        return old is not None and old not in self.readers.values() and not any(
            r['kind']==DISPLAY and r['anchor']==old for r in self.pending.values()) and not any(
            r['kind']==RETIRE for r in self.pending.values())

    def prepare_retire(self):
        if not self.can_retire():raise ValueError('old anchor still has readers/ACKs')
        tx=self._tx();old=self.retiring
        packet=pack(RETIRE,self.epoch,tx,old,NONE,self.active)
        self.pending[tx]=dict(kind=RETIRE,anchor=old)
        return packet

    def ack(self,tx,epoch):
        if type(epoch) is not int or epoch!=self.epoch or type(tx) is not int:raise ValueError('ACK epoch/identity')
        row=self.pending.pop(tx,None)
        if row is None:return False
        if row['kind']==KEY:
            if tx!=self.candidate:raise ValueError('candidate ACK mismatch')
            self.retiring=self.active;self.active=tx;self.candidate=None
        elif row['kind']==RETIRE:
            self.anchors.pop(row['anchor']);self.retiring=None
        # Display ACK and transport/physical drain are intentionally separate.
        # A caller cannot retire a reference merely by returning credit.
        return True

    def expire(self,tx):
        row=self.pending.get(tx)
        if row is None:return None
        if row['kind']==KEY:return 'retry_key'
        self.pending.pop(tx)
        return 'retire_retry' if row['kind']==RETIRE else 'display_expired'

    def retained_reference_bytes(self):return sum(a.nbytes for p in self.anchors.values() for a in p)
    def retry_cache_bytes(self):
        return len(self.pending[self.candidate]['packet']) if self.candidate is not None else 0


class Receiver:
    def __init__(self,epoch=1):
        mt.Receiver(epoch)
        self.epoch=epoch;self.anchors={};self.key_hashes={};self.last_key_tx=0;self.last_capture=-1
        self.peak_anchors=0

    def receive(self,packet):
        row=parse(packet)
        if row['epoch']!=self.epoch:raise ValueError('receiver epoch')
        kind,tx=row['kind'],row['tx']
        if kind==RETIRE:
            if row['keep'] not in self.anchors:raise ValueError('retirement keep anchor missing')
            self.anchors.pop(row['anchor'],None);self.key_hashes.pop(row['anchor'],None)
            return None,dict(row,committed=True,display=False,duplicate=False)
        inner=mt.HEADER.unpack_from(row['payload']) if len(row['payload'])>=mt.HEADER.size else None
        if inner is None or inner[2]!=self.epoch or inner[3]!=tx:
            raise ValueError('inner transaction mismatch')
        if kind==KEY:
            if row['anchor']!=tx or inner[4]!=NONE:raise ValueError('key reference')
            hashed=hashlib.sha256(packet).hexdigest()
            if tx in self.anchors:
                if self.key_hashes[tx]!=hashed:raise ValueError('conflicting key retry')
                return None,dict(row,committed=True,display=False,duplicate=True)
            if tx<=self.last_key_tx or len(self.anchors)>=2:raise ValueError('stale/third anchor')
            scratch=mt.Receiver(self.epoch);rgb,info=scratch.receive(row['payload'])
            self.anchors[tx]=scratch._reference;self.key_hashes[tx]=hashed;self.last_key_tx=tx
            self.peak_anchors=max(self.peak_anchors,len(self.anchors))
            return rgb,dict(row,committed=True,display=False,duplicate=False)
        if row['capture']<=self.last_capture or row['anchor'] not in self.anchors or inner[4]!=row['anchor']:
            raise ValueError('stale capture/missing anchor')
        scratch=mt.Receiver(self.epoch)
        scratch.reference_id,scratch._reference=row['anchor'],self.anchors[row['anchor']]
        rgb,info=scratch.receive(row['payload'])
        self.last_capture=row['capture']
        return rgb,dict(row,committed=True,display=True,duplicate=False)

    def retained_reference_bytes(self):return sum(a.nbytes for p in self.anchors.values() for a in p)
