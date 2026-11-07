#!/usr/bin/env python3
"""Trace oracle for full-width reference identity and 4x16B assembly.

Error replies may contain a discarded partial prefix; the error flag is the
consumer contract. Unit cancellation timing is additionally checked by the
source-pinned SV bench, not inferred from an unrecorded reset input.
"""
from reference_trace import descriptor,physical,need,BASES

class TileTrace:
    def __init__(self):
        self.active=None;self.line=None;self.requests=0;self.responses=0;self.lines=0;self.returns=0
        self.success=0;self.errors=0;self.high_generations=set();self.valid_fid_zero=0
    def feed(self,e):
        k=e['type']
        if k=='ref_req':
            need(self.active is None,'new reference overwrites held tile owner')
            p,t=e['plane'],e['tile']
            legal=bool(e['lease_valid'] and e['bank']<3 and e['epoch']!=0 and e['generation']!=0 and
                       e['fid']==e['accepted_fid'] and e['generation']==e['accepted_generation'] and
                       ((p==0 and t<5400) or (p in (1,2) and t<1350)))
            self.active=dict(identity=descriptor(e),bank=e['bank'],base=(BASES[p] if p<3 else 0)+t*64,
                             valid=legal,chunk=0,chunks=[],offered=None)
            self.requests+=1
            if legal and e['generation']>0xffffffff:self.high_generations.add(e['generation'])
            if legal and e['fid']==0:self.valid_fid_zero+=1
        elif k=='ref_line_req':
            a=self.active;need(a is not None and a['valid'] and self.line is None,'line request lacks legal owned tile')
            need(descriptor(e)==a['identity'] and e['bank']==a['bank'],'reference line changed full identity')
            need(e['line']==a['chunk']<4 and e['address']==a['base']+16*a['chunk'] and e['ticket']!=0,'reference line address/index/ticket differs')
            self.line=e;self.lines+=1
        elif k=='ref_line_rsp':
            a=self.active;need(a is not None and self.line is not None,'reference line reply without owner')
            need(descriptor(e)==a['identity'] and physical(e,True)==physical(self.line,True) and e['line']==self.line['line'],'reference line reply identity/ticket differs')
            # A warm cancellation can discard this last matched line even when
            # its memory error flag is clear; save input bytes for prefix checks.
            a['chunks'].append((int(e['data'],16).to_bytes(16,'little'),e['error']))
            a['chunk']+=1;self.line=None;self.returns+=1
        elif k in ('ref_rsp_offer','ref_rsp'):
            a=self.active;need(a is not None and self.line is None,'outer reference response before owned line drain')
            need(descriptor(e)==a['identity'] and e['bank']==a['bank'],'outer reference response changed full identity')
            value=int(e['data'],16).to_bytes(64,'little')
            body={n:v for n,v in e.items() if n not in ('type','time_ps','cycle')}
            if k=='ref_rsp_offer':
                need(a['offered'] is None,'duplicate reference response offer')
                if not e['error']:
                    need(a['valid'] and a['chunk']==4 and not any(error for _,error in a['chunks']),'successful tile before four valid line returns')
                    need(value==b''.join(raw for raw,_ in a['chunks']),'assembled reference bytes differ')
                else:
                    candidates=[b''.join(raw for raw,_ in a['chunks'][:n])+bytes(64-16*n) for n in range(len(a['chunks'])+1)]
                    need(value in candidates,'error tile contains bytes outside received prefix')
                if not a['valid']:need(e['error']==1 and a['chunk']==0,'invalid reference caused physical line traffic/success')
                a['offered']=body
            else:
                need(a['offered']==body,'held reference reply mutated before ACK')
                self.responses+=1;self.errors+=bool(e['error']);self.success+=not e['error'];self.active=None
    def finish(self):
        need(self.active is None and self.line is None and self.requests==self.responses,'reference unit ends with accepted owner')
        need(self.lines==self.returns,'reference unit line credits differ')
        return dict(requests=self.requests,responses=self.responses,successful_tiles=self.success,error_tiles=self.errors,
                    line_requests=self.lines,line_responses=self.returns,distinct_high64_generations=len(self.high_generations),
                    valid_frame_id_zero_requests=self.valid_fid_zero,
                    scope='All recorded handshakes/identity/assembly replayed; cancellation stimuli and wrong unaccepted replies remain source-reviewed bench assertions.')

class MuxTrace:
    def __init__(self):self.owner=0;self.decision=None;self.last_reference=True;self.active=None;self.grants=0;self.acks=0;self.returned=None
    def feed(self,e):
        k=e['type']
        if k=='mux_arbitrate':
            need(self.owner==0 and self.active is None,'mux arbitration during held physical owner')
            d,r=e['display_eligible'],e['reference_eligible']
            self.decision=(1 if d and (not r or self.last_reference) else 2) if d or r else None
        elif k=='mux_owner':
            need(e['old_owner']==self.owner and e['owner'] in (0,1,2) and e['owner']!=self.owner,'mux owner history differs')
            if e['owner']:
                need(self.owner==0 and self.active is None and e['owner']==self.decision,'mux fairness/grant differs')
                self.last_reference=e['owner']==2;self.grants+=1
            else:need(self.active is None,'mux releases accepted read before ACK')
            self.owner=e['owner']
        elif k=='mux_req':
            need(self.active is None and e['owner']==self.owner and self.owner in (1,2),'mux repeated/unowned acceptance')
            self.active=physical(e)
            self.returned=None
        elif k=='rd_req':
            need(self.active==physical(e),'mux request differs from accepted physical bridge read')
        elif k=='rd_rsp':
            need(self.active==physical(e),'physical return differs from mux owner')
            self.returned=(e['error'],int(e['data'],16))
        elif k=='mux_rsp':
            need(self.active==physical(e) and e['owner']==self.owner,'mux routes response to wrong owner')
            need(self.returned==(e['error'],int(e['data'],16)),'mux response data differs from physical return')
            self.active=None;self.acks+=1
    def finish(self):
        need(self.active is None and self.owner==0,'mux terminal owner remains')
        return dict(grants=self.grants,responses=self.acks)
