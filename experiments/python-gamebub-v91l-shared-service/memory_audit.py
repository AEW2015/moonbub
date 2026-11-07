#!/usr/bin/env python3
"""Independent shared-port ownership and physical SDR command/data replay.

This oracle learns memory only from observed pin WRITE commands. It never reads
the SV model's memory or accepts native preloads. Frozen timing/command checks
are hash-pinned from the already qualified controller gate.
"""
import collections
import gzip
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HELPERS={
 'experiments/python-gamebub-v91l-writepipe/verify_results.py':'0a2d293add938e48f2a726481a90e197fb53b5bce293c5800212b027bfda3004',
 'experiments/python-gamebub-v91l-sdram/verify_results.py':'c3452197f0a080482b47a1167c450f2d021f0cb10a76dc3be05b27f064ea79d3',
 'experiments/python-gamebub-v91l-rows/verify_results.py':'b19c032b7c23fe01599574e5a28e1ff0d269febde90d982d28d071da54565c7a',
}
def need(ok,why):
    if not ok: raise AssertionError(why)
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()
def load_helper(name,label):
    path=ROOT/name;need(sha(path)==HELPERS[name],'frozen independent helper changed: '+name)
    spec=importlib.util.spec_from_file_location(label,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module
pins=load_helper(next(iter(HELPERS)),'shared_frozen_writepipe_oracle')
native=load_helper(list(HELPERS)[2],'shared_frozen_native_oracle')

def events(path):
    opener=gzip.open if str(path).endswith('.gz') else open
    with opener(path,'rt') as f:
        for line in f:
            if line.startswith('{'): yield json.loads(line)

def ordered(stream):
    """Resolve pre-NBA receipts at one clock; never reorder different times.

    The wrapper prints its next arbitration before the observation that the
    old owner is now idle. They describe one pre-edge state, so consume that
    ownership observation first. A pre-edge response offer is already immutable
    when a same-edge warm kill is sampled. The bounded group holds one edge.
    """
    priority={'ownership':0,'wr_rsp_offer':1,'rd_rsp_offer':1,'kill':2,'arbitrate':3}
    timed=(e for e in stream if 'time_ps' in e)
    for _time,group in itertools.groupby(timed,key=lambda e:e['time_ps']):
        yield from sorted(group,key=lambda e:priority.get(e['type'],4))

def physical_byte(address):
    if address>=518400: return address
    base,width=(0,720) if address<345600 else (345600,360) if address<432000 else (432000,360)
    y,x=divmod(address-base,width)
    return base+((y//8)*(width//8)+x//8)*64+(y%8)*8+x%8

def numeric(data): return int(data,16) if isinstance(data,str) else data
def identity(event,writer):
    fields=('epoch','token','bank','address') if writer else ('epoch','generation','bank','address')
    return tuple(event[k] for k in fields)

class Replay:
    def __init__(self,require_written_reads=False):
        self.pin=pins.PinOracle();self.owner=0;self.active=None;self.decision=None;self.last_reader=True
        self.counts=collections.Counter();self.time=-1;self.require_written_reads=require_written_reads
        self.grants=[];self.completed=[];self.written=set();self.last_native_write=None

    def feed(self,e):
        k=e['type'];self.counts[k]+=1;t=e.get('time_ps',self.time)
        need(t>=self.time,'shared receipts reverse time');self.time=t
        if k=='preload': raise AssertionError('native preload is forbidden in shared physical join')
        if k=='arbitrate':
            need(self.owner==0 and self.active is None,'arbitration while a logical owner remains')
            w,r=bool(e['wr_offer']),bool(e['rd_offer'])
            self.decision=(1 if w and (not r or self.last_reader) else 2) if w or r else None
        elif k=='ownership':
            need(e['old_owner']==self.owner,'ownership history differs')
            o=e['owner'];need(o in (0,1,2) and o!=self.owner,'invalid owner transition')
            if o:
                need(self.owner==0 and self.active is None,'bridge owner switched without release')
                need(self.decision==o,'round-robin grant differs from eligible offers')
                self.last_reader=o==2;self.grants.append(o);self.decision=None
            else:
                need(self.active is None,'owner released before logical response ACK')
                need(not self.pin.reads and not self.pin.controller_reads,'owner released before BL8 drain')
            self.owner=o
        elif k in ('wr_req','rd_req'):
            writer=k=='wr_req';o=1 if writer else 2
            need(self.owner==e['owner']==o and self.active is None,'overlapping or ungranted bridge request')
            address=e['address'];bank=e['bank']
            valid=e['epoch']!=0 and bank<3 and address%(8 if writer else 16)==0 and 0<=address<=(560632 if writer else 518384)
            if not writer: valid=valid and e['generation']!=0
            self.active=dict(e,writer=writer,valid=valid,killed=False,commands=[],words=[],offered=None,
                             last_fence=None,idles=0,write_idle=None,saw_write_busy=False)
        elif k=='kill':
            need(any(e.get(n,0) for n in ('wr_reset','wr_cancel','rd_reset','rd_cancel')),'kill without asserted reset/cancel')
            if self.active is not None and self.active['offered'] is None:
                names=('wr_reset','wr_cancel') if self.active['writer'] else ('rd_reset','rd_cancel')
                if any(e.get(n,0) for n in names): self.active['killed']=True
        elif k=='ctrl_req':
            a=self.active;need(a is not None and a['valid'] and not a['killed'] and a['offered'] is None,'command lacks live valid bridge owner')
            need(e['owner']==self.owner==(1 if a['writer'] else 2),'controller request owner differs')
            index=len(a['commands']);need(index<(4 if a['writer'] else 1),'bridge command credit overflow')
            base=(a['bank']<<22)|((physical_byte(a['address']) if a['writer'] else a['address'])>>1)
            need(e['write']==int(a['writer']) and e['address']==base+(index if a['writer'] else 0),'physical command address/op differs from logical intent')
            expected=(numeric(a['data'])>>(16*index))&65535 if a['writer'] else 0
            need(e['data']==expected,'physical write word differs from accepted row payload')
            a['commands'].append(dict(e,seen=False,pin_time=None))
        elif k=='pin':
            if e['command'] in (4,5):
                a=self.active;need(a is not None,'pin column command has no logical owner')
                command=next((c for c in a['commands'] if not c['seen']),None)
                need(command is not None,'pin column command has no accepted controller request')
                row=self.pin.open_rows.get(e['bank']);need(row is not None,'pin column into closed row')
                address=(e['bank']<<22)|(row<<9)|e['address']
                need(address==command['address'] and (e['command']==4)==bool(command['write']),'pin address/op differs from controller owner')
                need(t>command['time_ps'],'pin column command precedes acceptance')
                if e['command']==4:
                    need(e['dq']==command['data'],'pin DQ differs from accepted write word')
                    self.written.add(address)
                elif self.require_written_reads:
                    need(all(address+i in self.written for i in range(8)),'native RGB reads bytes never physically written')
                command['seen']=True;command['pin_time']=t
            self.pin.command(e)
        elif k=='read': self.pin.read(e)
        elif k=='controller_read':
            self.pin.controller_read(e);a=self.active
            need(a is not None and not a['writer'] and self.owner==e['owner']==2,'read capture routed to wrong client')
            need(len(a['words'])<8,'extra BL8 captured word');a['words'].append(e['data'])
        elif k=='fence':
            need(e['owner']==self.owner and self.owner in (1,2),'fence from ungranted client')
            a=self.active
            if a is not None:
                if not a['writer'] and e['rd_state']==3:
                    need(len(a['words'])==8 and e['rd_beats']==8 and e['rd_pending']==1,'read fence before complete owned burst')
                    if a['last_fence'] is not None: need(t-a['last_fence']==10000,'read fence samples not consecutive')
                    a['last_fence']=t;a['idles']=a['idles']+1 if e['controller_idle'] else 0
                if a['writer'] and e['wr_state']==2: a['saw_write_busy']=True
                if a['writer'] and e['wr_state']==3 and e['controller_idle']:
                    need(a['saw_write_busy'],'write idle before WAIT_BUSY fence');a['write_idle']=t
        elif k in ('wr_rsp_offer','rd_rsp_offer','wr_rsp','rd_rsp'):
            a=self.active;writer=k.startswith('wr_');need(a is not None and a['writer']==writer,'response without matching bridge owner')
            need(e['owner']==self.owner==(1 if writer else 2),'response from wrong owner')
            need(identity(e,writer)==identity(a,writer),'bridge response identity changed')
            offered={key:value for key,value in e.items() if key not in ('type','cycle','time_ps')}
            if k.endswith('_offer'):
                need(a['offered'] is None,'duplicate logical response offer')
                need(e['error']==int(not a['valid'] or a['killed']),'response error disagrees with rejection/cancel')
                commands=a['commands'];need(all(c['seen'] for c in commands),'response offered before physical commands reach pins')
                if not e['error']: need(len(commands)==(4 if writer else 1),'successful response lacks full physical service')
                if writer and commands:
                    need(a['write_idle'] is not None and t>=a['write_idle']+10000,'write response before idle/drain fence')
                    need(t-commands[-1]['pin_time']>=41000,'write response before actual command recovery')
                if not writer:
                    if commands:
                        need(len(a['words'])==8 and a['idles']==2,'read response before eight words/two idle observations')
                        need(t>=a['last_fence']+10000 and t-commands[0]['pin_time']>=131000,'read response precedes final drain/recovery')
                    value=0 if e['error'] else sum(v<<(16*i) for i,v in enumerate(a['words']))
                    need(numeric(e['data'])==value,'held BL8 response payload differs from captured words')
                a['offered']=offered
            else:
                need(a['offered']==offered,'held response mutated before ACK')
                need(not self.pin.reads and not self.pin.controller_reads,'logical ACK before unbackpressured read drain')
                self.completed.append(dict(writer=writer,identity=identity(a,writer),error=e['error'],
                                           request_time_ps=a['time_ps'],ack_time_ps=t,commands=len(a['commands'])))
                self.active=None

    def finish(self):
        need(self.active is None,'terminal state still owns logical request/response')
        need(self.owner==0,'terminal state still owns arbiter grant')
        need(not self.pin.reads and not self.pin.controller_reads,'terminal physical read words not drained')
        return dict(counts=dict(self.counts),grants=len(self.grants),completed=len(self.completed),
                    logical_write_transactions=sum(c['writer'] for c in self.completed),
                    logical_read_transactions=sum(not c['writer'] for c in self.completed),
                    physical_write_words=self.pin.counts[4],physical_read_commands=self.pin.counts[5],
                    physical_captured_words=self.pin.counts['controller_read_beats'],
                    refreshes=self.pin.counts[1],written_word_addresses=len(self.written),
                    require_prior_pin_write_for_every_native_read=self.require_written_reads)
