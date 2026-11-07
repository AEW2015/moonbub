#!/usr/bin/env python3
"""Independent reference grant credits, contiguous scope, gaps and reply ownership."""
import collections
import itertools

def need(ok,why):
    if not ok:raise AssertionError(why)
def ident(e):return tuple(e[n] for n in ('epoch','generation','bank','address'))
def next_ticket(value):return 1 if value==0xffffffff else value+1

def ordered_policy(stream,base_order):
    # Keep the frozen native/reference ordering; add policy announcements just
    # ahead of their same-edge mux request. No different clocks are reordered.
    for _,group in itertools.groupby(base_order(stream),key=lambda e:e['time_ps']):
        records=list(group);announcements=[e for e in records if e['type'] in ('batch_start','batch_continue','batch_wait','batch_yield')]
        records=[e for e in records if e['type'] not in ('batch_start','batch_continue','batch_wait','batch_yield')]
        at=next((i for i,e in enumerate(records) if e['type']=='mux_req'),len(records))
        yield from records[:at];yield from announcements;yield from records[at:]

class GrantTrace:
    def __init__(self,expected_limit=None,gap_cycles=8):
        self.owner=0;self.last_reference=True;self.decision=None;self.active=None;self.group=None
        self.announcement=None;self.yielded=None;self.limit=expected_limit;self.gap_cycles=gap_cycles
        self.last_time=-1;self.wait_time=None;self.expected_gap=0;self.last_wait=None
        self.counts=collections.Counter();self.group_hist=collections.Counter();self.reasons=collections.Counter()
        self.grants=0;self.starts=0;self.continues=0;self.ref_requests=0;self.ref_responses=0;self.displays=0
        self.max_lines=0;self.max_gap=0
        self.display_wait=None;self.display_wait_max=0;self.display_wait_ends=0;self.display_wait_canceled=0;self.last_display_accept=None
    def feed(self,e):
        k=e['type'];t=e.get('time_ps',self.last_time);need(t>=self.last_time,'grant receipts reverse time');self.last_time=t
        if k=='mux_arbitrate':
            need(self.owner==0 and self.active is None,'mux selects over owned request')
            need(bool(e['last_reference'])==self.last_reference,'mux round-robin history differs')
            d,r=bool(e['display_eligible']),bool(e['reference_eligible'])
            self.decision=(1 if d and (not r or self.last_reference) else 2) if d or r else None
        elif k=='mux_owner':
            need(e['old_owner']==self.owner and e['owner']!=self.owner,'grant owner history differs')
            owner=e['owner'];need(owner in (0,1,2),'invalid grant owner')
            if owner:
                need(self.owner==0 and self.active is None and owner==self.decision,'bounded grant violates round-robin opportunity')
                self.last_reference=owner==2;self.decision=None;self.grants+=1;self.group=None
                self.wait_time=None;self.expected_gap=0;self.last_wait=None;self.yielded=None
            else:
                need(self.active is None and self.announcement is None,'grant released before matching response ACK')
                if self.owner==2:
                    need(self.yielded is not None,'reference owner release lacks checked yield')
                    self.yielded=None
                self.group=None
            self.owner=owner
        elif k=='batch_start':
            need(self.owner==2 and self.active is None and self.group is None and self.announcement is None,'reference starts over owned group')
            limit=e['limit'];need(limit in (1,4),'unsupported reference budget')
            if self.limit is None:self.limit=limit
            need(limit==self.limit,'reference grant parameter changes within run')
            legal=e['epoch']!=0 and e['generation']!=0 and e['bank']<3 and e['address']%64==0 and 0<=e['address']<=518336
            groupable=limit>1 and legal
            need(bool(e['groupable'])==groupable,'reference grouping legality differs')
            self.group=dict(base=e['address']//64,first=ident(e),last=None,requests=0,successes=0,error=False,acks=0,max_lines=limit if groupable else 1)
            self.announcement=('start',ident(e));self.starts+=1
        elif k=='batch_continue':
            g=self.group;need(self.owner==2 and g is not None and self.active is None and self.announcement is None,'continuation overwrites pending line')
            need(g['acks']==g['requests'] and g['successes']==g['requests'] and not g['error'],'continuation before successful ACK/drain')
            need(g['requests']<g['max_lines'],'reference budget exceeded')
            last=g['last'];expected=(last[0],next_ticket(last[1]),last[2],last[3]+16)
            need(ident(e)==expected and e['address']//64==g['base'],'continuation descriptor/tile boundary differs')
            need(e['lines']==g['successes'] and 0<=e['gap']<self.gap_cycles,'continuation credit/gap differs')
            self.announcement=('continue',ident(e));self.continues+=1
        elif k=='batch_wait':
            g=self.group;need(self.owner==2 and g is not None and self.active is None and not g['error'],'gap wait lacks owned successful group')
            need(g['acks']==g['requests']==g['successes'] and 0<g['successes']<g['max_lines'],'gap wait after incomplete ACK or full credit')
            if self.wait_time is None:self.expected_gap=0
            else:need(t-self.wait_time==10000,'reference reservation skips idle-gap observation')
            need(e['lines']==g['successes'] and e['gap']==self.expected_gap,'bounded gap counter differs')
            self.max_gap=max(self.max_gap,e['gap']);self.wait_time=t;self.last_wait=dict(e)
            self.expected_gap=e['gap']+1 if not e['offer'] else e['gap']
            if e['offer'] and not e['match']:need(self.announcement is None,'mismatched continuation forwarded before yield')
        elif k=='mux_req':
            need(e['owner']==self.owner and self.active is None,'mux accepts over pending reply or wrong client')
            if self.owner==2:
                need(self.group is not None and self.announcement is not None and ident(e)==self.announcement[1],'physical request differs from checked batch announcement')
                g=self.group;need(not g['error'] and g['requests']<g['max_lines'],'reference accepts beyond error/credit')
                g['requests']+=1;g['last']=ident(e);self.ref_requests+=1;self.announcement=None
                self.wait_time=None;self.expected_gap=0;self.last_wait=None
            else:self.displays+=1;self.last_display_accept=(ident(e),t)
            self.active=ident(e)
        elif k=='mux_rsp':
            need(e['owner']==self.owner and self.active==ident(e),'matching response identity/ownership differs')
            if self.owner==2:
                g=self.group;need(g is not None,'reference reply without group')
                g['acks']+=1;g['successes']+=int(not e['error']);g['error']=bool(e['error']);self.ref_responses+=1
            self.active=None
        elif k=='batch_yield':
            need(self.owner==2 and self.active is None and self.announcement is None,'reference yields accepted request before ACK')
            g=self.group;successes=g['successes'] if g else 0
            need(e['lines']==successes,'yield successful-credit count differs')
            reason=e['reason'];need(reason in (0,1,2,3,4),'unknown reference yield reason')
            if g:
                need(g['acks']==g['requests'] and bool(e['seen']),'reference yield before response ACK')
                need(bool(e['failed'])==g['error'],'yield error history differs')
                if g['error']:need(reason in (1,2),'failed line continued instead of yielding')
                if reason==0:need(successes==g['max_lines'],'reference yields early without bounded cause')
                if reason==2:need(g['error'],'error yield without error ACK')
                if reason==3:need(self.last_wait is None or (self.last_wait['offer'] and not self.last_wait['match']),'mismatch yield despite matching continuation')
                if reason==4:
                    need(self.last_wait is not None and not self.last_wait['offer'] and self.last_wait['gap']==self.gap_cycles-1 and e['gap']==self.gap_cycles-1,'timeout before exact bounded idle-gap limit')
                self.max_lines=max(self.max_lines,g['requests']);self.group_hist[g['requests']]+=1
            else:need(successes==0 and reason in (0,1),'empty grant has invalid terminal cause')
            self.reasons[reason]+=1;self.yielded=dict(e);self.wait_time=None;self.last_wait=None;self.expected_gap=0
        elif k=='batch_display_wait_start':
            need(self.display_wait is None,'display eligible wait overwrites owner')
            self.display_wait=(ident(e),t)
        elif k=='batch_display_wait_end':
            need(self.display_wait is not None and ident(e)==self.display_wait[0],'display wait descriptor differs')
            need(t-self.display_wait[1]==e['cycles']*10000 and e['cycles']>0,'display eligible wait elapsed cycles differ')
            self.display_wait_max=max(self.display_wait_max,e['cycles'])
            need(e['maximum']==self.display_wait_max,'display eligible wait maximum differs')
            if e['accepted']:need(self.last_display_accept==(ident(e),t),'display wait claims acceptance without actual request handshake')
            else:self.display_wait_canceled+=1
            self.display_wait=None;self.display_wait_ends+=1
        self.counts[k]+=1
    def finish(self):
        need(self.owner==0 and self.active is None and self.announcement is None and self.group is None,'terminal grant remains owned')
        need(self.ref_requests==self.ref_responses,'unacknowledged reference suffix')
        need(self.display_wait is None,'terminal eligible display wait remains')
        return dict(limit=self.limit,gap_cycles=self.gap_cycles,groups_started=self.starts,continuations=self.continues,reference_requests=self.ref_requests,reference_responses=self.ref_responses,
                    display_requests=self.displays,max_reference_lines_per_grant=self.max_lines,max_observed_gap=self.max_gap,group_request_histogram=dict(self.group_hist),yield_reasons=dict(self.reasons),
                    display_eligible_wait_max_cycles=self.display_wait_max,display_wait_intervals=self.display_wait_ends,display_wait_canceled=self.display_wait_canceled,all_continuations_same_tile_and_identity=True)
