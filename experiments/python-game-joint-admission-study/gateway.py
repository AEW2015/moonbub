"""Serialized GF03+PC18/QC18 packet-credit engine; conditional ESP service."""
from collections import deque,Counter
import importlib.util
from pathlib import Path
import math,struct,sys,zlib
import framing
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('joint_esp_costs',HERE.parent/'python-game-esp32-gateway-study/gateway.py')
frozen=importlib.util.module_from_spec(s);sys.modules[s.name]=frozen;s.loader.exec_module(frozen)
TOKEN=struct.Struct('!IHHQ') #16bytes epoch/slot/reserved/sequence
REPLY=struct.Struct('!4sIHHQBI')
QUERY=struct.Struct('!4sIHHQI')
def unwrap(data):
    if type(data)is not bytes or len(data)<TOKEN.size+framing.HEADER.size or len(data)>1064:raise ValueError('wrapped datagram bounds')
    epoch,slot,reserved,seq=TOKEN.unpack_from(data)
    if epoch!=1 or not 0<=slot<6 or reserved or not seq:raise ValueError('packet token identity')
    fields=framing.HEADER.unpack_from(data,TOKEN.size)
    if fields[0]!=b'GF03' or fields[1]!=3 or fields[2]!=epoch or len(data)!=TOKEN.size+framing.HEADER.size+fields[7]:raise ValueError('wrapped GF03 route')
    return dict(slot=slot,seq=seq,frame=fields[3],index=fields[5],crc=zlib.crc32(data[:TOKEN.size+framing.HEADER.size]))

def seal(b):return b+struct.pack('!I',zlib.crc32(b))
def parse(b,fmt,magic):
    if type(b)is not bytes or len(b)!=fmt.size+4 or zlib.crc32(b[:-4])!=struct.unpack('!I',b[-4:])[0]:raise ValueError('credit length/CRC')
    x=fmt.unpack_from(b)
    if (x[0]!=magic or x[1]!=1 or not 0<=x[2]<6 or not x[4]
            or (x[3]!=0 if magic==b'QC18' else x[3] not in (0,1))
            or (magic==b'PC18' and x[5] not in (0,1,2))):raise ValueError('credit identity/profile')
    return x

class Engine:
    def __init__(self,cfg,ingress,event,timed,feedback_rows):
        self.cfg,self.ingress,self.event,self.timed,self.feedback_rows=cfg,ingress,event,timed,feedback_rows
        self.cost=frozen.Config(cpu_fraction=cfg.esp_cpu_fraction,driver_call_us=cfg.esp_driver_us,qspi_write_hz=int(cfg.qspi_mbps*1e6/4))
        self.frames={};self.pending=deque();self.tokens=[None]*6;self.seqs=[0]*6;self.ledger=[None]*6
        self.control=None;self.control_queue=deque();self.wire_busy=False;self.worker=None;self.mailbox=deque()
        self.pacing_until=0.;self.reverse_free=0.;self.fifo=0.;self.fifo_at=0.
        self.now=0.;self.counter=Counter();self.wire=[];self.credit_rows=[];self.completions=[];self.rejections=[]
        self.peak_mailbox=self.peak_tokens=self.peak_fifo=self.peak_control=0;self.lost_credit=False;self.duplicate=False
    def enqueue(self,fid,chunks):
        assert fid not in self.frames
        self.frames[fid]=dict(chunks=chunks,next=0,consumed=0,credit_owned=0,queries=0,route=None,errors=[])
        self.pending.append(fid)
    def queued_bytes(self):
        return sum(sum(len(c)+TOKEN.size+28 for c in r['chunks'][r['next']:]) for r in self.frames.values())
    def frame_drained(self,fid):
        r=self.frames.get(fid)
        return r is None or (r['next']==len(r['chunks']) and r['consumed']==len(r['chunks']) and r['credit_owned']==0)
    def forget(self,fid):
        assert self.frame_drained(fid);self.frames.pop(fid,None)
    def reverse(self,data,kind,value,now,deliver=True):
        start=max(now,self.reverse_free);done=start+(len(data)+28)*8/(self.cfg.feedback_mbps*1000)
        self.reverse_free=done
        self.feedback_rows.append(dict(kind='wire',channel=kind,id=value[0] if kind=='af' else value['frame'],start_ms=start,done_ms=done,bytes=len(data)+28))
        if kind=='af' and value[0]==self.cfg.corrupt_af_frame and not getattr(self,'corrupted_af',False):
            self.corrupted_af=True;data=data[:-1]+bytes([data[-1]^1])
        if deliver:self.event(done+self.cfg.feedback_latency_ms,'gw_reply',(data,kind,value))
        elif kind=='af':self.event(done,'gw_lost_af',value)
    def drain(self,t):
        self.fifo=max(0.,self.fifo-(t-self.fifo_at)*self.cfg.fifo_drain_bytes_ms);self.fifo_at=t
    def pump(self,now):
        self.now=now
        if not self.wire_busy:
            control=self.control_queue.popleft() if self.control_queue and self.control_queue[0]['ready_ms']<=now+1e-9 else None
            free=next((i for i,t in enumerate(self.tokens) if t is None),None)
            while self.pending and self.frames[self.pending[0]]['next']==len(self.frames[self.pending[0]]['chunks']):self.pending.popleft()
            if control is not None:
                data=control['data'];item=control
            elif self.pending and free is not None and now>=self.pacing_until-1e-9:
                fid=self.pending[0];r=self.frames[fid];index=r['next'];chunk=r['chunks'][index]
                self.seqs[free]+=1;seq=self.seqs[free]
                data,w=self.timed('packet_wrap',fid,lambda:TOKEN.pack(1,free,0,seq)+chunk)
                item=dict(control=False,frame=fid,index=index,slot=free,seq=seq,data=data,crc=zlib.crc32(data[:TOKEN.size+framing.HEADER.size]))
                self.tokens[free]=item;r['next']+=1;r['credit_owned']+=1
                self.pacing_until=now+self.cfg.pacing_ms
                self.event(now+self.cfg.packet_credit_timeout_ms,'gw_credit_timeout',item)
                self.event(self.pacing_until,'gw_wake',None)
                now=w['done_ms']
            else:item=None
            if item is not None:
                self.wire_busy=True;done=now+(len(data)+28)*8/(self.cfg.link_mbps*1000)
                self.wire.append(dict(id=item['frame'],control=item['control'],start_ms=now,done_ms=done,bytes=len(data)+28))
                self.event(done,'gw_wire_done',item)
        if self.worker is None and self.mailbox:
            item=self.mailbox.popleft();self.worker=item
            if item['control']:
                def decode_query():
                    try:return parse(item['data'],QUERY,b'QC18'),None
                    except ValueError as e:return None,str(e)
                (query,error),w=self.timed('query_parse',item['frame'],decode_query)
                self.event(w['done_ms']+self.cfg.control_cpu_ms,'gw_malformed_done' if error else 'gw_worker_done',item if error else (item,query,None));return
            def decode_data():
                try:return unwrap(item['data']),None
                except (ValueError,struct.error) as e:return None,str(e)
            (decoded,error),w=self.timed('packet_header_parse',item['frame'],decode_data)
            if error is not None:
                self.event(w['done_ms'],'gw_malformed_done',item);return
            # frame remains the sender ownership handle for accounting only;
            # all receiver ledger/route fields come from received bytes.
            item=dict(item,slot=decoded['slot'],seq=decoded['seq'],crc=decoded['crc'],wire_frame=decoded['frame'],index=decoded['index']);self.worker=item
            fid=item['frame'];r=self.frames[fid];chunk=item['data'][TOKEN.size:]
            fields=framing.HEADER.unpack_from(chunk);r['route']=dict(epoch=fields[2],frame_id=fields[3],body_crc=fields[-1])
            payload=len(chunk)
            cost=frozen.packet_service_us(payload,item['index'],self.cost)
            finish=w['done_ms']+sum(cost[k] for k in ('cpu_us','poll_us','dma_blocking_us'))/1000
            self.drain(finish);wait=max(0.,self.fifo+payload-self.cfg.fifo_bytes)/self.cfg.fifo_drain_bytes_ms
            if wait>self.cfg.maximum_fifo_wait_ms:
                self.event(finish,'gw_worker_done',(item,None,'fifo_wait_timeout'));return
            finish+=wait;self.drain(finish);self.fifo+=payload;self.peak_fifo=max(self.peak_fifo,self.fifo)
            self.event(finish,'gw_feed',item)
        self.peak_tokens=max(self.peak_tokens,sum(t is not None for t in self.tokens))
        self.peak_control=max(self.peak_control,int(self.control is not None))
        assert self.peak_tokens<=6 and self.peak_mailbox<=6 and self.peak_control<=1
    def step(self,kind,value,now):
        self.now=now
        if kind=='gw_wake':pass
        elif kind=='gw_wire_done':
            self.wire_busy=False
            t=now if not self.cfg.aggregate_ms else math.ceil((now-1e-10)/self.cfg.aggregate_ms)*self.cfg.aggregate_ms
            self.event(t,'gw_arrival',value)
        elif kind=='gw_arrival':
            self.counter['arrived']+=1
            if len(self.mailbox)>=6:raise AssertionError('bounded credits exceeded mailbox')
            self.mailbox.append(value);self.peak_mailbox=max(self.peak_mailbox,len(self.mailbox))
        elif kind=='gw_feed':
            item=value;fid=item['frame'];r=self.frames[fid];data=item['data'][TOKEN.size:]
            if self.cfg.drop_packet_frame==fid and item['index']==0:
                result,error=None,'injected_packet_loss'
            else:
                if self.cfg.corrupt_packet_frame==fid and item['index']==0:data=data[:-1]+bytes([data[-1]^1])
                def feed():
                    try:return self.ingress.feed(data,now),None
                    except ValueError as e:return None,str(e)
                (result,error),w=self.timed('fpga_ingress_feed',fid,feed)
                self.event(w['done_ms'],'gw_worker_done',(item,result,error));return
            self.event(now,'gw_worker_done',(item,result,error))
        elif kind=='gw_worker_done':
            item,result,error=value;assert self.worker is item;self.worker=None
            if item['control']:
                slot,seq,crc=result[2],result[4],result[5]
                entry=self.ledger[slot] if 0<=slot<6 else None
                if entry is None or (entry['seq'],entry['crc'])!=(seq,crc):
                    entry=dict(frame=item['frame'],slot=slot,seq=seq,crc=crc,status=2)
                ready=self.send_credit(entry,True,now)
                self.worker=item;self.event(ready,'gw_release_worker',item)
                self.counter['queries_consumed']+=1
            else:
                fid=item['frame'];r=self.frames[fid];r['consumed']+=1
                entry={k:item[k] for k in ('frame','slot','seq','crc')};entry['status']=int(error is not None)
                self.ledger[item['slot']]=entry
                ready=self.send_credit(entry,False,now)
                self.worker=item;self.event(ready,'gw_release_worker',item)
                if error is not None:r['errors'].append(error);self.rejections.append((fid,error,r['route']))
                if result is not None:self.completions.append((fid,result))
        elif kind=='gw_lost_af':
            return ('af_lost',value)
        elif kind=='gw_malformed_done':
            assert self.worker is value;self.worker=None;self.counter['malformed_rejected']+=1
            if not value['control']:
                self.frames[value['frame']]['consumed']+=1
                self.rejections.append((value['frame'],'malformed_prefix',None))
            # No trusted received token => no invented credit; session reset needed.
        elif kind=='gw_release_worker':
            assert self.worker is value;self.worker=None
        elif kind=='gw_duplicate_ready':
            data,entry=value;self.reverse(data,'credit',entry,now)
        elif kind=='gw_reply':
            data,channel,meta=value
            if channel=='af':return ('af',(meta[0],data))
            def decode():
                try:return parse(data,REPLY,b'PC18'),None
                except ValueError as e:return None,str(e)
            (x,error),w=self.timed('credit_parse',meta['frame'],decode)
            if error is not None:self.counter['bad_credit']+=1
            else:self.event(w['done_ms'],'gw_credit_parsed',(x,meta))
        elif kind=='gw_credit_parsed':
            x,meta=value;slot,seq,status,crc=x[2],x[4],x[5],x[6]
            if x[3]&1 and self.control is not None and (slot,seq,crc)==self.control['key']:self.control=None
            token=self.tokens[slot] if 0<=slot<6 else None
            if token is not None and (token['seq'],token['crc'])==(seq,crc) and status in (0,1):
                self.tokens[slot]=None;self.frames[token['frame']]['credit_owned']-=1;self.counter['credits_applied']+=1
                self.credit_rows.append(dict(frame=token['frame'],slot=slot,seq=seq,at_ms=now,status=status))
            else:self.counter['stale_credit']+=1
        elif kind=='gw_credit_timeout':
            token=value;slot=token['slot'];current=self.tokens[slot]
            if current is token and self.control is None and self.frames[token['frame']]['queries']<self.cfg.max_credit_queries:
                self.frames[token['frame']]['queries']+=1
                data,w=self.timed('query_build',token['frame'],lambda:seal(QUERY.pack(b'QC18',1,slot,0,token['seq'],token['crc'])))
                self.control=dict(control=True,frame=token['frame'],target=token,key=(slot,token['seq'],token['crc']),data=data,ready_ms=w['done_ms'])
                self.control_queue.append(self.control);self.event(w['done_ms'],'gw_wake',None)
        else:raise AssertionError(kind)
        self.pump(now);return None
    def send_credit(self,entry,queried,now):
        lost=self.cfg.lose_all_packet_credits or (self.cfg.lose_first_packet_credit and not self.lost_credit)
        if lost:self.lost_credit=True;self.counter['credit_dropped']+=1
        data,w=self.timed('credit_build',entry['frame'],lambda:seal(REPLY.pack(b'PC18',1,entry['slot'],int(queried),entry['seq'],entry['status'],entry['crc'])))
        self.reverse(data,'credit',entry,w['done_ms'],deliver=not lost)
        if self.cfg.duplicate_packet_credit and not self.duplicate:
            self.duplicate=True;self.event(w['done_ms']+40,'gw_duplicate_ready',(data,entry))
        return w['done_ms']
