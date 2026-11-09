#!/usr/bin/env python3
"""Reversible peer-only interpretation of an actual owner-tagged private kill."""
import hashlib,json,pathlib
R=pathlib.Path(__file__).resolve().parents[3];S=R/'fpga/experiments/cu66-v114-control-peer';BASE=R/'fpga/experiments/cu66-v114-harness/bench_transport_base.hpp'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert sha(BASE)=='2e4c84900729de653e0927f5b86aebee25131679eac9fbec86d9a6ce04d66971'
 before='            need(bool(d.queue_push)==bool(d.frame_read_rsp),"queue response push conservation");'
 after='''            const bool local_cancel_scope=d.rootp->cs88_pipeline_v91k__DOT__base_abort&&
                d.rootp->cs88_pipeline_v91k__DOT__base_kill_valid&&
                d.rootp->cs88_pipeline_v91k__DOT__base_kill_owner==d.rootp->cs88_pipeline_v91k__DOT__owner_sequence;
            if(local_cancel_scope)need(!d.queue_push&&!d.queue_pop&&!d.stage_write&&!d.frame_read_req,"owner-tagged private kill leaked refill traffic");
            else need(bool(d.queue_push)==bool(d.frame_read_rsp),"queue response push conservation");'''
 text=BASE.read_text();assert text.count(before)==1;derived=text.replace(before,after,1);assert derived.count(after)==1 and derived.replace(after,before,1)==text
 p=S/'bench_peer_base.hpp';p.write_text(derived)
 q=dict(schema='v114-peer-only-owner-tagged-private-cancel-oracle-v1',original=str(BASE.relative_to(R)),original_sha256=sha(BASE),derived=str(p.relative_to(R)),derived_sha256=sha(p),edits=[dict(before=before,after=after)],reverse_verified=True,old_queue_check_retained_outside_exact_local_cancel_scope=True,all_other_original_need_checks_unchanged=True,old_synchronous_replay_binding_check_unchanged=True,source_or_shared_harness_changed=False,scope='Only registered matching-owner base_abort qualifies the private queue cancel boundary; independent before/after hooks additionally require exact queued/pending cancellation deltas and empty canceled owners.')
 (S/'derivation.json').write_text(json.dumps(q,indent=2,sort_keys=True)+'\n');print('PASS_PEER_ONLY_REVERSIBLE_PRIVATE_CANCEL_DERIVATION_NOT_RTL')
if __name__=='__main__':main()
