#!/usr/bin/env python3
"""Independent native reference intent / mux / physical read receipt oracle."""
import itertools

def need(ok,why):
    if not ok:raise AssertionError(why)
BASES=(0,345600,432000)

def ordered_reference(stream):
    # Same-edge pre-NBA observations describe one state. Establish owners and
    # accepted source intents before their inner handshakes, then retire returns
    # from physical port toward the outer reconstruction consumer.
    priority={'ownership':0,'mux_owner':0,'wr_rsp_offer':1,'rd_rsp_offer':1,'ref_rsp_offer':1,
              'kill':2,'arbitrate':3,'mux_arbitrate':3,
              'reference_req':4,'ref_req':5,'ref_line_req':6,'reference_line_req':7,
              'mux_req':8,'rd_req':9,'rd_rsp':10,'mux_rsp':11,
              'ref_line_rsp':12,'reference_line_rsp':13,'ref_rsp':14,'reference_rsp':15}
    for _time,group in itertools.groupby((e for e in stream if 'time_ps' in e),key=lambda e:e['time_ps']):
        yield from sorted(group,key=lambda e:priority.get(e['type'],9))

def descriptor(e):return tuple(e[k] for k in ('epoch','fid','generation','plane','tile'))
def physical(e,sv=False):return e['epoch'],e['ticket' if sv else 'generation'],e['bank'],e['address']

class ReferenceTraffic:
    def __init__(self,cases,frames):
        self.cases=cases;self.frames=frames;self.active=None;self.line=None;self.last_time=-1
        self.requests=0;self.responses=0;self.lines=0;self.line_responses=0
        self.by_frame={};self.sequences={};self.mux_owner=0;self.mux_decision=None;self.last_reference=True
        self.mux_active=None;self.mux_grants=0
        for fid,key in ((0,'actual_001'),(1,'actual_006')):
            modes=cases[key]['operations'];need(len(modes)==8100,'native mode-map extent differs')
            self.sequences[fid]=[] if fid==0 else [(p,t) for p,count,offset in ((0,5400,0),(1,1350,5400),(2,1350,6750))
                                                for t in range(count) if modes[offset+t]!=1]
        need(len(self.sequences[1])==7806,'source-derived reference schedule differs')

    def advance(self,t):
        if t!=self.last_time:
            if self.line is not None and self.line['response_seen']=={'SV','CXX','MUX','PHYSICAL'}:
                need(self.active is not None,'completed line lost outer owner')
                self.active['chunks'].append(self.line['payload']);self.line=None;self.line_responses+=1
            if self.active is not None and self.active['response_seen']=={'SV','CXX'}:
                need(self.line is None and len(self.active['chunks'])==4,'outer response before four line drains')
                self.active=None;self.responses+=1
            self.last_time=t

    def feed(self,e,current,done):
        k=e['type'];self.advance(e['time_ps'])
        if k=='mux_arbitrate':
            need(self.mux_owner==0 and self.mux_active is None,'reader mux arbitrates over owned response')
            d,r=bool(e['display_eligible']),bool(e['reference_eligible'])
            self.mux_decision=(1 if d and (not r or self.last_reference) else 2) if d or r else None
        elif k=='mux_owner':
            need(e['old_owner']==self.mux_owner,'reader mux owner history differs')
            owner=e['owner'];need(owner in (0,1,2) and owner!=self.mux_owner,'invalid mux owner transition')
            if owner:
                need(self.mux_owner==0 and self.mux_active is None and owner==self.mux_decision,'reader mux fairness/grant differs')
                self.last_reference=owner==2;self.mux_decision=None;self.mux_grants+=1
            else:need(self.mux_active is None,'reader mux releases before response ACK')
            self.mux_owner=owner
        elif k in ('ref_req','reference_req'):
            need(current is not None and current['commit'] is None and current['fid']==1,'reference outside live delta reconstruction')
            fid=current['fid'];counts=self.by_frame.setdefault(fid,dict(tiles=0,lines=0,bytes=0))
            plane,tile=e['plane'],e['tile']
            if self.active is None:
                need((plane,tile)==self.sequences[fid][counts['tiles']],'reference tile order/mode differs')
                bank=current['accepted_ref_bank'];generation=current['accepted_generation'];reference_fid=current['accepted_fid']
                need(current['accepted_ref_valid'] and done and bank==done[-1]['bank'] and reference_fid==done[-1]['fid'],'reference source is not accepted key bank')
                need(e['epoch']==current['epoch'] and e['fid']==reference_fid and e['generation']==generation,'full reference identity differs from captured accepted lease')
                frame=self.frames[f'c0_f{reference_fid}'];base=BASES[plane]+tile*64
                self.active=dict(identity=descriptor(e),bank=bank,base=base,payload=frame['tiles'][base:base+64],
                                 request_seen=set(),response_seen=set(),chunks=[])
                counts['tiles']+=1;self.requests+=1
            a=self.active;need(descriptor(e)==a['identity'],'reference request identity differs across observers')
            observer='SV' if k=='ref_req' else 'CXX';need(observer not in a['request_seen'],'duplicate reference request receipt')
            if observer=='SV':
                need(e['lease_valid'] and e['accepted_fid']==e['fid'] and e['accepted_generation']==e['generation'] and e['accepted_bank']==a['bank'],'accepted descriptor mismatch/high-generation narrowing')
                need(e['bank']==a['bank'],'reference SV source bank differs')
            else:need(e['source_bank']==a['bank'],'reference C++ source bank differs')
            a['request_seen'].add(observer)
        elif k in ('ref_line_req','reference_line_req'):
            a=self.active;need(a is not None and a['request_seen']=={'SV','CXX'},'reference line lacks full accepted descriptor')
            if k=='ref_line_req':
                need(self.line is None and descriptor(e)==a['identity'],'reference line overwrites owner or changes outer metadata')
                index=len(a['chunks']);need(index<4 and e['line']==index,'reference chunk index/order differs')
                need(e['bank']==a['bank'] and e['address']==a['base']+16*index and e['ticket']!=0,'physical reference address/ticket differs')
                self.line=dict(identity=physical(e,True),request_seen={'SV'},response_seen=set(),payload=a['payload'][16*index:16*(index+1)])
                self.lines+=1;self.by_frame[1]['lines']+=1
            else:
                need(self.line is not None and physical(e)==self.line['identity'],'C++ physical reference offer differs')
                need('CXX' not in self.line['request_seen'],'duplicate C++ physical line request');self.line['request_seen'].add('CXX')
        elif k=='mux_req':
            need(e['owner']==self.mux_owner and self.mux_active is None,'read mux double acceptance or wrong owner')
            self.mux_active=physical(e)
            if e['owner']==2:
                need(self.line is not None and physical(e)==self.line['identity'],'mux reference request differs from tile chunk')
                self.line['request_seen'].add('MUX')
            else:need(current is not None and current['rgb'] is not None,'display mux request outside RGB lease')
        elif k=='rd_req' and self.mux_owner==2:
            need(self.line is not None and physical(e)==self.line['identity'],'physical bridge accepted a different reference line')
            self.line['request_seen'].add('PHYSICAL')
        elif k in ('rd_rsp','mux_rsp','ref_line_rsp','reference_line_rsp') and (k not in ('rd_rsp','mux_rsp') or self.mux_owner==2):
            need(self.line is not None,'reference line response has no owner')
            sv=k=='ref_line_rsp';need(physical(e,sv)==self.line['identity'],'reference line response identity/ticket differs')
            need(not e['error'],'native reference physical read failed')
            payload=int(e['data'],16).to_bytes(16,'little') if k!='reference_line_rsp' else bytes.fromhex(e['data'])
            need(payload==self.line['payload'],'reference line bytes differ from actual accepted source')
            observer={'rd_rsp':'PHYSICAL','mux_rsp':'MUX','ref_line_rsp':'SV','reference_line_rsp':'CXX'}[k]
            need(observer not in self.line['response_seen'],'duplicate reference line response receipt')
            self.line['response_seen'].add(observer)
            need(self.line['request_seen']=={'SV','CXX','MUX','PHYSICAL'},'reference line returned without every accepted handshake')
            if k=='mux_rsp':
                need(e['owner']==self.mux_owner==2 and self.mux_active==physical(e),'mux reference return does not match its owner');self.mux_active=None
        elif k=='mux_rsp':
            need(e['owner']==self.mux_owner==1 and self.mux_active==physical(e),'display return routed to wrong mux client');self.mux_active=None
        elif k in ('ref_rsp_offer','ref_rsp','reference_rsp'):
            a=self.active;need(a is not None and descriptor(e)==a['identity'],'outer reference reply identity differs')
            need(e['source_bank' if k=='reference_rsp' else 'bank']==a['bank'],'outer reference source bank differs')
            need(not e['error'] and self.line is None and len(a['chunks'])==4,'reference returned before complete physical assembly')
            payload=bytes.fromhex(e['data']) if k=='reference_rsp' else int(e['data'],16).to_bytes(64,'little')
            need(payload==a['payload']==b''.join(a['chunks']),'assembled reference tile differs from accepted pixels')
            if k!='ref_rsp_offer':
                observer='CXX' if k=='reference_rsp' else 'SV'
                need(observer not in a['response_seen'],'duplicate outer reference response');a['response_seen'].add(observer)
                if observer=='CXX':self.by_frame[1]['bytes']+=64
        elif k=='native_commit':
            need(self.active is None and self.line is None,'publication before reference drain')
            expected=0 if current['fid']==0 else 7806
            need(self.by_frame.get(current['fid'],{}).get('tiles',0)==expected,'reference source request count incomplete')

    def is_reference_read(self,e):
        return self.mux_owner==2 and self.line is not None and physical(e)==self.line['identity']

    def finish(self):
        self.advance(self.last_time+1)
        need(self.active is None and self.line is None and self.mux_active is None and self.mux_owner==0,'terminal reference/mux owner remains')
        need(self.requests==self.responses==7806 and self.lines==self.line_responses==31224,'native reference totals differ')
        need(self.by_frame[1]['bytes']==499584,'reference byte total differs')
        return dict(tile_requests=self.requests,tile_responses=self.responses,physical_BL8_reads=self.lines,
                    captured_x16_words=self.lines*8,reference_bytes=499584,per_frame=self.by_frame,
                    mux_grants=self.mux_grants,all_tiles_byte_exact=True,full64_reference_identity_checked=True)
