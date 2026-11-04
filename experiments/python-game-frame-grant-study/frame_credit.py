"""FG19 prospective bounded frame-slot ownership, distinct from PC18 and AF03.

All messages are serialized and CRC-bound. Epoch is fixed to 1 for this laboratory
session; reset/rekey negotiation is outside this model. Sequence numbers never
wrap. Unknown control outcome is a bounded safe stop, never an invented grant.
"""
import struct,zlib,math
from collections import deque,Counter
FMT=struct.Struct('!4sBBHIIQII')
REQUEST,CANCEL,GRANT,BUSY,RELEASE,CANCELED,FINISH,FINISHED=range(1,9)
NO_SLOT=65535

def seal(kind,slot,fid,seq,total,crc):
    b=FMT.pack(b'FG19',1,kind,slot,1,fid,seq,total,crc)
    return b+struct.pack('!I',zlib.crc32(b))
def parse(b):
    if type(b)is not bytes or len(b)!=FMT.size+4 or zlib.crc32(b[:-4])!=struct.unpack('!I',b[-4:])[0]:raise ValueError('FG19 length/CRC')
    magic,version,kind,slot,epoch,fid,seq,total,crc=FMT.unpack_from(b)
    if magic!=b'FG19' or version!=1 or epoch!=1 or kind not in range(1,9) or not seq or not 0<total<=49152 or slot not in (0,1,NO_SLOT):raise ValueError('FG19 fields')
    if (kind==BUSY and slot!=NO_SLOT) or (kind in (REQUEST,GRANT,RELEASE,FINISHED) and slot==NO_SLOT):raise ValueError('FG19 slot')
    return dict(kind=kind,slot=slot,epoch=epoch,frame=fid,seq=seq,total=total,crc=crc)

def identity(x):return x['epoch'],x['frame'],x['seq'],x['total'],x['crc']

class Protocol:
    def __init__(self,cfg,event,timed):
        self.cfg,self.event,self.timed=cfg,event,timed;self.engine=None
        self.outgoing=deque();self.pending=None;self.onwire=False;self.seq=0
        self.receiver=[None,None];self.host={};self.history=[];self.counter=Counter();self.peak_receiver=self.peak_host=0
        self.stopped=False;self.stop_reason=None;self.last_request_seq=0;self.released_seq=0
        self.fault_grant=self.fault_release=False;self.feedback_owned=0;self.peak_feedback=0
    def request(self,fid,total,crc,now):
        if self.stopped or self.pending is not None or len(self.host)>=2:return False
        slot=next(i for i in range(2) if i not in {r['slot'] for r in self.host.values()})
        self.seq+=1;x=dict(kind=REQUEST,slot=slot,epoch=1,frame=fid,seq=self.seq,total=total,crc=crc)
        self._send(x,now);return True
    def cancel(self,fid,now):
        if self.stopped or self.pending is not None:return False
        x=self.host.get(fid)
        if x is None or fid in getattr(self.engine,'frames',{}):return False
        self._send(dict(x,kind=CANCEL),now);return True
    def finish(self,fid,now):
        x=self.host.get(fid)
        if self.stopped or self.pending is not None or x is None or x.get('finish_sent'):return False
        x['finish_sent']=True;self._send(dict(x,kind=FINISH),now);return True
    def _send(self,x,now):
        assert self.pending is None and len(self.outgoing)==0
        data,w=self.timed('frame_control_build',x['frame'],lambda:seal(x['kind'],x['slot'],x['frame'],x['seq'],x['total'],x['crc']))
        item=dict(control=True,frame_control=True,frame=x['frame'],data=data,ready_ms=w['done_ms'],identity=identity(x),kind=x['kind'],slot=x['slot'])
        self.pending=item;self.outgoing.append(item)
        self.event(w['done_ms'],'gw_wake',None);self.event(now+self.cfg.frame_control_timeout_ms,'fg_timeout',item)
        self.history.append(dict(event={REQUEST:'sender_request',CANCEL:'sender_cancel',FINISH:'sender_finish'}[x['kind']],at_ms=now,**x))
    def reply(self,x,now):
        data,w=self.timed('frame_reply_build',x['frame'],lambda:seal(x['kind'],x['slot'],x['frame'],x['seq'],x['total'],x['crc']))
        self.feedback_owned+=1;self.peak_feedback=max(self.peak_feedback,self.feedback_owned);assert self.feedback_owned<=4
        deliver=True
        if x['kind']==GRANT and self.cfg.lose_first_frame_grant and not self.fault_grant:self.fault_grant=True;deliver=False
        if x['kind']==RELEASE and self.cfg.lose_first_frame_release and not self.fault_release:self.fault_release=True;deliver=False
        self.engine.reverse(data,'frame',x,w['done_ms'],deliver=deliver)
        if not deliver:self.event(max(w['done_ms'],self.engine.reverse_free),'fg_reply_lost',x)
        self.history.append(dict(event='receiver_reply',at_ms=w['done_ms'],delivered=deliver,**x))
        if self.cfg.duplicate_frame_release and x['kind']==RELEASE and not getattr(self,'duplicated_release',False):
            self.duplicated_release=True;self.event(w['done_ms']+100,'fg_duplicate_release',data)
        return w['done_ms']
    def receive(self,x,now):
        if x['kind'] not in (REQUEST,CANCEL,FINISH):raise ValueError('FG19 receiver direction')
        fid=x['frame'];owned=next((r for r in self.receiver if r is not None and r['frame']==fid),None)
        if x['kind']==REQUEST:
            if owned is not None:
                out=dict(owned,kind=GRANT) if identity(owned)==identity(x) else dict(x,kind=BUSY,slot=NO_SLOT)
            elif x['seq']<=max(self.last_request_seq,self.released_seq):out=dict(x,kind=BUSY,slot=NO_SLOT)
            else:
                self.last_request_seq=x['seq'];slot=x['slot'] if x['slot'] in (0,1) and self.receiver[x['slot']] is None else None
                if slot is None:out=dict(x,kind=BUSY,slot=NO_SLOT)
                else:
                    out=dict(x,kind=GRANT,slot=slot);self.receiver[slot]=dict(out,seen=set(),expected=math.ceil(x['total']/1008),releasing=False,finished=False)
                    self.counter['granted']+=1
            self.peak_receiver=max(self.peak_receiver,sum(r is not None for r in self.receiver));assert self.peak_receiver<=2
        elif x['kind']==FINISH:
            slot=x['slot'];r=self.receiver[slot] if slot in (0,1) else None
            if r is not None and identity(r)==identity(x):
                r['finished']=True;self.counter['finish_received']+=1
                self.history.append(dict(event='receiver_finish',at_ms=now,**x))
                if self.cfg.frame_finish_ack:return self.reply(dict(x,kind=FINISHED),now)
                return now
            out=dict(x,kind=BUSY,slot=NO_SLOT)
        else:
            slot=x['slot'];r=self.receiver[slot] if slot in (0,1) else None
            if r is not None and identity(r)==identity(x) and not r['seen']:
                self.receiver[slot]=None;self.released_seq=max(self.released_seq,x['seq']);out=dict(x,kind=CANCELED)
                self.counter['cancel_applied']+=1
            else:
                self.counter['cancel_rejected']+=1;out=dict(x,kind=BUSY,slot=NO_SLOT)
        self.history.append(dict(event='receiver_control',at_ms=now,**x))
        return self.reply({k:v for k,v in out.items() if k in ('kind','slot','epoch','frame','seq','total','crc')},now)
    def receive_reply(self,data,meta,now):
        def decode():
            try:return parse(data),None
            except ValueError as e:return None,str(e)
        (x,error),w=self.timed('frame_reply_parse',meta['frame'],decode)
        self.event(w['done_ms'],'fg_reply_parsed',(x,error,meta));return w['done_ms']
    def apply_reply(self,value,now):
        x,error,meta=value;self.feedback_owned-=1
        if error or x['kind'] not in (GRANT,BUSY,RELEASE,CANCELED,FINISHED):self.counter['bad_reply']+=1;return None
        fid=x['frame'];p=self.pending
        if x['kind']==RELEASE:
            old=self.host.get(fid)
            if (old is not None and identity(old)==identity(x) and old['slot']==x['slot']
                    and (old.get('finish_confirmed') or (not self.cfg.frame_finish_ack and p is not None and p['kind']==FINISH and p['identity']==identity(x) and p['slot']==x['slot']))):
                self.host.pop(fid)
                if p is not None and p['kind']==FINISH and p['identity']==identity(x):self.pending=None;self.onwire=False
                self.counter['release_applied']+=1;self.history.append(dict(event='sender_released',at_ms=now,**x));return ('released',fid)
            self.counter['stale_release']+=1;return None
        if p is None or p['identity']!=identity(x):self.counter['stale_reply']+=1;return None
        allowed={REQUEST:{GRANT,BUSY},CANCEL:{CANCELED,BUSY},FINISH:{FINISHED} if self.cfg.frame_finish_ack else set()}
        if x['kind'] not in allowed[p['kind']]:self.counter['wrong_kind_reply']+=1;return None
        if x['kind'] in (CANCELED,FINISHED):
            old=self.host.get(fid)
            if x['slot']!=p['slot'] or old is None or identity(old)!=identity(x) or old['slot']!=x['slot']:
                self.counter['wrong_slot_reply']+=1;return None
        if x['kind']==GRANT and (x['slot']!=p['slot'] or x['slot'] in [r['slot'] for r in self.host.values()]):
            self.counter['occupied_slot_reply']+=1;return None
        self.pending=None;self.onwire=False
        if x['kind']==FINISHED:
            self.host[fid]['finish_confirmed']=True;self.counter['finish_confirmed']+=1;return ('finish_confirmed',fid)
        if x['kind']==GRANT and p['kind']==REQUEST:
            self.host[fid]=x;self.peak_host=max(self.peak_host,len(self.host));assert len(self.host)<=2
            self.history.append(dict(event='sender_granted',at_ms=now,**x));return ('granted',fid)
        if x['kind']==CANCELED and p['kind']==CANCEL:
            old=self.host.get(fid)
            if old is not None and identity(old)==identity(x):self.host.pop(fid)
            self.counter['cancel_confirmed']+=1;return ('canceled',fid)
        return ('busy',fid)
    def allowed(self,fields):
        magic,version,epoch,fid,total,index,count,length,checksum,crc=fields
        if (magic!=b'GF03' or version!=3 or epoch!=1 or not 0<total<=49152 or count!=math.ceil(total/1008) or not 0<=index<count or length!=min(1008,total-index*1008)):return None
        return next((r for r in self.receiver if r is not None and (r['epoch'],r['frame'],r['total'],r['crc'])==(fields[2],fid,total,crc)),None)
    def consumed(self,fields):
        r=self.allowed(fields)
        if r is not None:r['seen'].add(fields[5])
    def release_ready(self,now,receiver_drained):
        for i,r in enumerate(self.receiver):
            if r is not None and not r['releasing'] and r['finished'] and receiver_drained(r['frame']):
                r['releasing']=True;x={k:r[k] for k in ('slot','epoch','frame','seq','total','crc')};x['kind']=RELEASE
                # State is released at actual receive-side drain, not at delivery
                # of the signal; a lost signal conservatively pins the sender.
                self.receiver[i]=None;self.released_seq=max(self.released_seq,r['seq']);self.reply(x,now)
                self.event(now+self.cfg.frame_control_timeout_ms,'fg_release_timeout',x)
                self.counter['receiver_released']+=1
    def stop(self,reason,now):
        if not self.stopped:self.stopped=True;self.stop_reason=reason;self.history.append(dict(event='safe_stop',reason=reason,at_ms=now))
    def snapshot(self):
        return dict(history=self.history,counters=dict(self.counter),peak_receiver=self.peak_receiver,peak_host=self.peak_host,
            peak_feedback=self.peak_feedback,receiver_owned=[dict(r,seen=sorted(r['seen'])) for r in self.receiver if r is not None],host_owned=list(self.host.values()),
            pending=self.pending is not None,feedback_owned=self.feedback_owned,safe_stop=self.stopped,safe_stop_reason=self.stop_reason)
