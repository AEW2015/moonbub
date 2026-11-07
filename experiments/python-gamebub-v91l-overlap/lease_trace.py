#!/usr/bin/env python3
"""Independent immutable descriptor and two-sample physical drain oracle."""

def need(ok,why):
    if not ok:raise AssertionError(why)

class LeaseTrace:
    def __init__(self):
        self.active=None;self.offered=None;self.previous_fence=None;self.idles=0;self.last_time=-1
        self.requests=0;self.accepted=0;self.rejected=0;self.releases=0;self.aliases=0;self.terminals=0
        self.expected_terminal=False;self.expected_error=0

    def feed(self,e):
        k=e['type'];t=e.get('time_ps',self.last_time)
        need(t>=self.last_time,'lease receipts reverse time');self.last_time=t
        if k=='lease_request':
            self.requests+=1
            need(self.active is None and self.offered is None,'lease start overwrites owned display descriptor')
            good=bool(e['accepted_valid']) and e['accepted_bank']<3 and e['bank']==e['accepted_bank'] and e['epoch']!=0 and 0<e['accepted_generation']<(1<<32) and e['generation32']==e['accepted_generation']
            need(e['accepted']==int(good) and e['rejected']==int(not good),'lease start descriptor qualification differs')
            if good:
                self.accepted+=1;self.offered=dict(bank=e['bank'],epoch=e['epoch'],fid=e['accepted_fid'],generation=e['accepted_generation'],time_ps=t)
            else:self.rejected+=1
        elif k=='lease_owner':
            need(bool(e['old_active'])==bool(self.active) and e['active']!=e['old_active'],'lease owner history differs')
            if e['active']:
                need(self.offered is not None and self.active is None,'display lease appears without accepted start')
                need(all(e[n]==self.offered[n] for n in ('bank','epoch','fid','generation')),'lease captured descriptor differs')
                need(t==self.offered['time_ps']+10000,'lease capture not on accepted start edge')
                self.active=self.offered;self.offered=None;self.idles=0;self.previous_fence=None
                self.expected_terminal=False;self.expected_error=0
            else:
                need(self.active is not None and all(e[n]==self.active[n] for n in ('bank','epoch','fid','generation')),'released lease descriptor changed')
                need(self.idles==2 and self.previous_fence is not None and t==self.previous_fence+10000,'lease released before two consecutive terminal drain observations')
                self.active=None;self.idles=0;self.previous_fence=None;self.releases+=1
        elif k=='lease_fence':
            need(self.active is not None and e['active']==1,'lease drain without owner')
            need(bool(e['terminal'])==self.expected_terminal and e['terminal_error']==self.expected_error,
                 'lease terminal/error history differs')
            terminal=bool(e['terminal'] or e['reset'] or e['cancel'] or e['engine_done'] or e['engine_error'])
            drained=not any(e[n] for n in ('engine_busy','engine_draining','reader_busy','reader_pending')) and e['mux_owner']!=1
            if self.previous_fence is not None:need(t-self.previous_fence==10000,'terminal lease drain observation skipped a clock')
            need(e['idle_samples']==self.idles,'lease drain counter differs')
            self.previous_fence=t;self.idles=self.idles+1 if terminal and drained else 0
            need(self.idles<=2,'lease failed to release after complete terminal drain')
            self.terminals+=int(terminal)
            self.expected_terminal=terminal
            if self.expected_error==0:
                if e['reset'] or e['cancel']:self.expected_error=2
                elif e['engine_error']:self.expected_error=e['engine_error']
        elif k=='lease_alias_block':
            need(bool(e['lease_active'])==bool(self.active),'alias active metadata differs')
            if self.active is not None:need(e['lease_bank']==self.active['bank'],'alias source-bank metadata differs')
            need((e['lease_active'] and self.active is not None and e['candidate_bank']==self.active['bank']) or
                 (e['engine_start'] and self.offered is not None and e['candidate_bank']==self.offered['bank']),
                 'candidate alias blocked outside active/same-edge display lease')
            self.aliases+=1

    def finish(self):
        need(self.active is None and self.offered is None,'terminal display lease remains')
        need(self.accepted==self.releases,'display lease start/release accounting differs')
        return dict(requests=self.requests,accepted=self.accepted,rejected=self.rejected,releases=self.releases,
                    alias_blocks=self.aliases,terminal_observations=self.terminals,immutable_descriptor_and_two_idle_drain=True)
