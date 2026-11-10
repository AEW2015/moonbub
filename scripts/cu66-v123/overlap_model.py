#!/usr/bin/env python3
"""Finite causal overlap experiment over retained vectors; all costs are synthetic."""
from __future__ import annotations
import argparse, gzip, hashlib, heapq, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / 'experiments/python-gamebub-v122/integrated-study/spatial/attempts/20261110T004249476141Z/sources/experiments/python-gamebub-v91k/vectors/canonical_goldens.tsv.gz'
CHUNK = 64


def sha(data):
    if isinstance(data, (str, Path)):
        data = Path(data).read_bytes()
    return hashlib.sha256(data).hexdigest()


def load_vectors():
    vectors=[]
    with gzip.open(INPUT,'rt',encoding='ascii',newline='') as f:
        for line in f:
            row=line.rstrip('\n').split('\t')
            if len(row)!=3: raise ValueError('expected id/refhex/targetcanonicalhex')
            ident,refhex,targethex=row
            target=bytes.fromhex(targethex); reference=None if refhex=='-' else bytes.fromhex(refhex)
            if len(target)!=518400 or (reference is not None and len(reference)!=len(target)) or len(target)%CHUNK:
                raise ValueError('unexpected vector size')
            vectors.append({'id':ident,'reference':reference,'target':target,'target_sha256':sha(target),
                            'reference_sha256':sha(reference) if reference is not None else None})
    if len(vectors)!=6: raise ValueError('expected six retained vectors')
    return vectors


class ModelError(ValueError): pass


class Ledger:
    """Runtime-owned slots/tokens/credits and ACK-committed modeled-memory bytes."""
    def __init__(self, capacity=1):
        self.capacity=capacity; self.slots={}; self.known=set(); self.order=[]
        self.accepted=set(); self.acked=set(); self.hashed=set(); self.committed={}
        self.outstanding=None; self.debt=0; self.max_debt=0; self.hash_cursor=0
    def allocate(self,slot,token):
        if slot in self.slots: raise ModelError('slot reused before matching release')
        if token in self.known: raise ModelError('write token reused')
        self.known.add(token); self.slots[slot]=token; self.order.append(token)
    def accept(self,token,slot):
        if self.slots.get(slot)!=token: raise ModelError('accept token does not own slot')
        if token in self.accepted: raise ModelError('duplicate write acceptance')
        if self.outstanding is not None or self.debt>=self.capacity: raise ModelError('write credit limit exceeded')
        self.outstanding=token; self.accepted.add(token); self.debt+=1
        self.max_debt=max(self.max_debt,self.debt)
    def ack(self,token,payload):
        if token!=self.outstanding or token not in self.accepted or token in self.acked:
            raise ModelError('wrong, stale, or duplicate ACK token')
        self.outstanding=None; self.debt-=1; self.acked.add(token)
        self.committed[token]=bytearray(payload)
    def read_committed_for_hash(self,token):
        if token not in self.acked: raise ModelError('hash read before ACK commit')
        if self.hash_cursor>=len(self.order) or self.order[self.hash_cursor]!=token:
            raise ModelError('hash order violation')
        if token in self.hashed: raise ModelError('duplicate hash')
        return bytes(self.committed[token])
    def mark_hashed(self,token):
        if self.hash_cursor>=len(self.order) or self.order[self.hash_cursor]!=token or token not in self.acked:
            raise ModelError('hash without next ACKed token')
        if token in self.hashed: raise ModelError('duplicate hash')
        self.hashed.add(token); self.hash_cursor+=1
    def release(self,slot,token):
        if self.slots.get(slot)!=token: raise ModelError('release token does not own slot')
        if token not in self.hashed: raise ModelError('release before ordered hash')
        del self.slots[slot]
    def validate_digest(self,actual,expected):
        if actual!=expected: raise ModelError('canonical digest mismatch')
    def assert_batch_drained(self,total):
        if self.debt or self.outstanding is not None: raise ModelError('batch drain with unpaid write debt')
        if self.slots: raise ModelError('batch drain with occupied slots')
        if len(self.acked)!=total or len(self.hashed)!=total or self.hash_cursor!=total:
            raise ModelError('premature batch drain')


def simulate(vectors,slots_n,lanes_n,profile_name,data_edges,overhead_edges,compute_cycles=32,hash_cycles=12,finalize_cycles=4):
    numeric={'slots':slots_n,'lanes':lanes_n,'data_edges':data_edges,'overhead_edges':overhead_edges,
             'compute_cycles':compute_cycles,'hash_cycles':hash_cycles,'finalize_cycles':finalize_cycles}
    for label,value in numeric.items():
        if isinstance(value,bool) or not isinstance(value,int): raise ValueError(label+' must be an integer')
    if slots_n<=0 or lanes_n<=0: raise ValueError('slots and lanes must be positive')
    if compute_cycles<=0 or hash_cycles<=0 or finalize_cycles<=0: raise ValueError('compute/hash/finalize costs must be positive')
    if overhead_edges<0: raise ValueError('overhead edges cannot be negative')
    service_edges=data_edges+overhead_edges
    if data_edges<32: raise ValueError('64 bytes on a 16-bit bus require at least 32 data edges')
    if service_edges<data_edges: raise ValueError('service time cannot be below data edges')
    jobs=[]
    for vi,v in enumerate(vectors):
        for ci in range(len(v['target'])//CHUNK):
            jobs.append((vi,ci,v['target'][ci*CHUNK:(ci+1)*CHUNK]))
    n=len(jobs); ledger=Ledger(capacity=1)
    owner={s:None for s in range(slots_n)}; free_slots=set(owner)
    lane_busy=0; bus_busy=False; bus_queue=[]; hash_busy=False
    cursor=0; next_hash=0; accepted=acks=hash_count=0; max_slots=max_busq=0
    transcript=hashlib.sha256(); frame_hash=[hashlib.sha256() for _ in vectors]
    vector_start=[None]*len(vectors); vector_digest_complete=[None]*len(vectors)
    vector_finalize_pending=None; heap=[]; seq=0; now=0
    chunks_per_frame=len(vectors[0]['target'])//CHUNK
    def rec(t,event,index,detail=''):
        transcript.update(f'{t}|{event}|{index}|{detail}\n'.encode())
    def push(t,event,index):
        nonlocal seq
        seq+=1; heapq.heappush(heap,(t,seq,event,index))
    def token(i): return f'write:{i}'
    def pump(t):
        nonlocal cursor,lane_busy,bus_busy,accepted,max_slots,max_busq
        while cursor<n and free_slots and lane_busy<lanes_n:
            i=cursor; cursor+=1; slot=min(free_slots); free_slots.remove(slot)
            tok=token(i); ledger.allocate(slot,tok); owner[slot]=i
            vi,ci,_=jobs[i]
            if ci==0 and vector_start[vi] is None: vector_start[vi]=t
            lane_busy+=1; max_slots=max(max_slots,slots_n-len(free_slots))
            rec(t,'slot_alloc_compute_start',i,f'{tok};slot={slot}')
            push(t+compute_cycles,'compute_done',i)
        if not bus_busy and bus_queue:
            ready,i,slot=bus_queue.pop(0); tok=token(i); ledger.accept(tok,slot)
            bus_busy=True; accepted+=1
            rec(t,'physical_write_accept',i,f'{tok};slot={slot};ready={ready};data_edges={data_edges};overhead_edges={overhead_edges}')
            push(t+service_edges,'write_ack',i)
        max_busq=max(max_busq,len(bus_queue))
    pump(0)
    while heap:
        now,_,event,i=heapq.heappop(heap)
        if event=='vector_digest_complete':
            if vector_finalize_pending!=i: raise ModelError('wrong frame finalization token')
            vector_digest_complete[i]=now; vector_finalize_pending=None; hash_busy=False
            rec(now,'vector_digest_completion',i,vectors[i]['id'])
            vi=i
        else:
            vi,ci,data=jobs[i]; tok=token(i)
        if event=='vector_digest_complete':
            pass
        elif event=='compute_done':
            lane_busy-=1; slot=owner_inv(owner,i)
            bus_queue.append((now,i,slot)); bus_queue.sort(key=lambda x:(x[0],x[1]))
            rec(now,'computed_waiting_for_bus',i,f'{tok};slot={slot}')
        elif event=='write_ack':
            if not bus_busy: raise ModelError('ACK without active bus write')
            bus_busy=False; slot=owner_inv(owner,i)
            ledger.ack(tok,data); acks+=1; rec(now,'write_ack_commit_memory',i,tok)
        elif event=='hash_done':
            if vector_finalize_pending is not None: raise ModelError('digest overlap with finalization')
            memory_bytes=ledger.read_committed_for_hash(tok)
            if memory_bytes!=data: raise ModelError('ACK-committed bytes differ from produced payload')
            frame_hash[vi].update(memory_bytes); ledger.mark_hashed(tok); hash_count+=1
            hash_busy=False
            slot=owner_inv(owner,i); ledger.release(slot,tok); owner[slot]=None; free_slots.add(slot)
            rec(now,'ordered_hash_committed_memory_and_release',i,f'{tok};slot={slot}')
            if ci==chunks_per_frame-1:
                digest=frame_hash[vi].hexdigest()
                ledger.validate_digest(digest,vectors[vi]['target_sha256'])
                vector_finalize_pending=vi; hash_busy=True
                rec(now,'full_vector_hash_match',vi,digest)
                push(now+finalize_cycles,'vector_digest_complete',vi)
        else: raise ModelError('unknown scheduled event')
        if not hash_busy and next_hash<n and token(next_hash) in ledger.acked:
            hash_busy=True; idx=next_hash
            # Verify that the next ordered memory payload is available before service begins.
            ledger.read_committed_for_hash(token(idx))
            rec(now,'ordered_hash_start_from_committed_memory',idx,token(idx))
            push(now+hash_cycles,'hash_done',idx); next_hash+=1
        pump(now)
    if accepted!=n or acks!=n or hash_count!=n or any(x is None for x in vector_digest_complete):
        raise ModelError('incomplete frame/batch drain')
    ledger.assert_batch_drained(n)
    rec(now,'abstract_batch_drain',n,'zero_debt_all_acks_all_hashes')
    if bus_queue or bus_busy or hash_busy or any(x is not None for x in owner.values()):
        raise ModelError('resource did not drain')
    frames=[{'id':v['id'],'synthetic_compute_start_cycle':vector_start[i],'digest_complete_cycle':vector_digest_complete[i],
             'synthetic_compute_to_digest_cycles':vector_digest_complete[i]-vector_start[i],'target_sha256':v['target_sha256']}
            for i,v in enumerate(vectors)]
    return {'configuration':{'slots':slots_n,'compute_lanes':lanes_n,'service_profile':profile_name,
                'synthetic_compute_cycles_per_chunk':compute_cycles,'synthetic_data_edges_per_64B':data_edges,
                'synthetic_overhead_edges_per_request':overhead_edges,'synthetic_service_edges_per_64B':service_edges,
                'synthetic_ordered_hash_service_cycles_per_chunk':hash_cycles,
                'synthetic_full_vector_finalize_cycles':finalize_cycles},
            'aggregate_batch_model_cycles':now,'vector_count':len(vectors),'vectors':frames,'chunk_count':n,
            'bytes':sum(len(j[2]) for j in jobs),'max_owned_slots':max_slots,
            'max_waiting_computed_chunks':max_busq,'max_outstanding_writes':ledger.max_debt,
            'write_accepts':accepted,'write_acks':acks,'ordered_hash_chunks':hash_count,
            'schedule_sha256':transcript.hexdigest(),'abstract_batch_drain_after_all_acks_and_vector_digests':True,'abstract_batch_drain_cycle':now}


def owner_inv(owner,index):
    matches=[s for s,i in owner.items() if i==index]
    if len(matches)!=1: raise ModelError('chunk has no unique owned slot')
    return matches[0]


def self_tests():
    ok=[]
    l=Ledger(1); l.allocate(0,'t0'); l.accept('t0',0); l.ack('t0',b'abc')
    assert l.read_committed_for_hash('t0')==b'abc'; l.mark_hashed('t0'); l.release(0,'t0'); l.assert_batch_drained(1)
    ok.append('valid_accept_ack_ordered_hash_release_batch_drain')
    def test(name,fn):
        try: fn()
        except ModelError: ok.append(name); return
        raise AssertionError(name+' was accepted')
    def wrong_ack():
        q=Ledger(); q.allocate(0,'a'); q.accept('a',0); q.ack('other',b'x')
    test('wrong_token_ack',wrong_ack)
    def early_publish():
        q=Ledger(); q.allocate(0,'a'); q.assert_batch_drained(1)
    test('early_batch_drain',early_publish)
    def unpaid():
        q=Ledger(); q.allocate(0,'a'); q.accept('a',0); q.assert_batch_drained(1)
    test('unpaid_write_debt_on_drain',unpaid)
    def reuse():
        q=Ledger(); q.allocate(0,'a'); q.allocate(0,'b')
    test('slot_reuse_before_release',reuse)
    def duplicate_token_after_ack():
        q=Ledger(); q.allocate(0,'a'); q.accept('a',0); q.ack('a',b'x'); q.mark_hashed('a'); q.release(0,'a'); q.allocate(0,'a')
    test('token_reuse_after_ack',duplicate_token_after_ack)
    def hash_before_ack():
        q=Ledger(); q.allocate(0,'a'); q.read_committed_for_hash('a')
    test('hash_before_ack_commit',hash_before_ack)
    def out_of_order():
        q=Ledger(); q.allocate(0,'a'); q.allocate(1,'b'); q.accept('a',0); q.ack('a',b'a'); q.accept('b',1); q.ack('b',b'b'); q.read_committed_for_hash('b')
    test('out_of_order_hash',out_of_order)
    def corrupt_committed():
        q=Ledger(); payload=b'original bytes'; expected=sha(payload); q.allocate(0,'a'); q.accept('a',0); q.ack('a',payload)
        q.committed['a'][0]^=1; actual=q.read_committed_for_hash('a')
        q.validate_digest(sha(actual),expected)
    test('corrupt_committed_byte_digest_mismatch',corrupt_committed)
    try: simulate([{'id':'tiny','target':bytes(64),'target_sha256':sha(bytes(64))}],1,1,'invalid',31,0)
    except ValueError: ok.append('reject_bus_below_32_data_edges')
    else: raise AssertionError('sub-32-edge 64B bus profile was accepted')
    tiny=[{'id':'tiny','target':bytes(64),'target_sha256':sha(bytes(64))}]
    bad_calls=[('zero_compute',dict(data_edges=32,overhead_edges=0,compute_cycles=0)),
               ('negative_hash',dict(data_edges=32,overhead_edges=0,hash_cycles=-1)),
               ('float_finalize',dict(data_edges=32,overhead_edges=0,finalize_cycles=1.5)),
               ('negative_overhead',dict(data_edges=32,overhead_edges=-1))]
    for label,kwargs in bad_calls:
        try: simulate(tiny,1,1,'invalid',**kwargs)
        except ValueError: ok.append('reject_'+label)
        else: raise AssertionError(label+' invalid cost was accepted')
    return ok


def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('--self-test',action='store_true'); ap.parse_args()
    tests=self_tests(); vectors=load_vectors()
    profiles=[('synthetic_fast_overhead2',2),('synthetic_slow_overhead16',16)]
    rows=[]
    for name,overhead in profiles:
        for slots,lanes in ((1,1),(2,1),(2,2)):
            rows.append(simulate(vectors,slots,lanes,name,32,overhead))
    report={'schema':'v123-causal-spatial-overlap-synthetic-v2','script_source_sha256':sha(Path(__file__).resolve()),
      'classification':'SYNTHETIC_DISCRETE_EVENT_MODEL_ONLY','supersedes_attempt':{'path':'experiments/python-gamebub-v123/overlap-model/attempts/initial-prototype-results.json','sha256':sha(ROOT/'experiments/python-gamebub-v123/overlap-model/attempts/initial-prototype-results.json'),'reason':'Initial prototype used an impossible 8-edge 64-byte write service assumption and did not integrate ledger checks into runtime.'},'input':{'path':str(INPUT.relative_to(ROOT)),'sha256':sha(INPUT),
      'records':[{'id':v['id'],'bytes':len(v['target']),'reference_sha256':v['reference_sha256'],
                  'targetcanonical_sha256':v['target_sha256']} for v in vectors]},
      'semantics':{'chunk_bytes':CHUNK,'physical_bus_width_bits':16,'minimum_data_edges_per_chunk':32,
       'one_serialized_memory_bus':True,'maximum_outstanding_write_credit':1,'runtime_ledger_integrated':True,
       'ACK_commits_bytes_to_modeled_memory':True,'ordered_hash_reads_only_ACK_committed_memory':True,
       'hash_read_uses_assumed_local_ACK_committed_mirror':True,'hash_read_port_and_storage_costs_budgeted':False,
       'external_memory_readback_traffic_modelled':False,'write_bus_is_full_memory_bandwidth_lower_bound':False,
       'slot_release_requires_matching_token_ACK_and_ordered_hash':True,'per_vector_full_digest_must_match_targetcanonical_bytes':True,
       'reference_bytes_are_retained_and_hashed_but_not_assumed_equal_target':True,
       'synthetic_hash_service_is_abstract_and_not_SHA_core_timing':True,
       'synthetic_full_vector_finalization_cost_included':True,'latencies_calibrated_from_aggregate_counts':False},
      'synthetic_profiles':[{'name':n,'data_edges_per_64B':32,'overhead_edges_per_request':o,'service_edges_per_64B':32+o} for n,o in profiles],
      'self_tests':{'status':'PASS','cases':tests},'runs':rows,
      'interval_scope':'synthetic_compute_start_to_vector_digest_completion; not final-outer-byte to validated commit and not directly comparable to retained row fixture cycles','batch_scope':'abstract aggregate resource drain only; no immutable bank, C2/HUD, or seal publication model','claims':{'RTL':False,'C2_HUD_seal':False,'hardware_qualification':False,'125MHz':False,'FPS':False}}
    out=ROOT/'experiments/python-gamebub-v123/overlap-model/results.json'
    out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'output':str(out.relative_to(ROOT)),'runs':len(rows),'cases':len(tests),
                      'batch_model_cycles':[r['aggregate_batch_model_cycles'] for r in rows]},indent=2))
if __name__=='__main__': main()
