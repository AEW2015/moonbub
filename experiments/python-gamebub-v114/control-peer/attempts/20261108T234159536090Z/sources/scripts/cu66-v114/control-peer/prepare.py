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
 (S/'derivation.json').write_text(json.dumps(q,indent=2,sort_keys=True)+'\n')
 sources=[R/'fpga/experiments/cu66-v113-inverse/cu66_inverse_stream_v91j.sv',R/'fpga/experiments/cu66-v110-fault/cu66_reconstruct_stream_v91k.sv'];tasks=[]
 for source in sources:
  text=source.read_text();begin='    task automatic fail(input logic [7:0] reason);';assert text.count(begin)==1;body=text[text.index(begin):];body=body[:body.index('    endtask')+len('    endtask')];tasks.append(dict(path=str(source.relative_to(R)),sha256=sha(source),task_text=body))
 inverse=sources[0].read_text();recon=sources[1].read_text();assert all(s in inverse for s in ['FREE=0','M_IDLE=0','A_EMPTY=0','R_FREE=0'])and 'IDLE=0'in recon
 cpp=(S/'tb_peer.cpp').read_text();body=cpp[cpp.index('static void inject('):cpp.index('static void masked(')]
 injection=dict(schema='v114-prepared-complete-actual-fail-task-poststates-v1',actual_RTL_task_sources=tasks,cpp=str((S/'tb_peer.cpp').relative_to(R)),cpp_sha256=sha(S/'tb_peer.cpp'),injection_body_sha256=hashlib.sha256(body.encode()).hexdigest(),inverse_reason=5,reconstruction_reason=3,actual_task_state_effects_included=True,zero_encoded_states=['inverse.FREE','inverse.M_IDLE','inverse.A_EMPTY','inverse.R_FREE','reconstruction.IDLE'],physical_reference_or_scratch_ledger_assigned=False,counters_and_unowned_private_payloads_unchanged_as_in_actual_tasks=True,prepared_poststates_not_natural_packet_fault_claim=True,old_incomplete_fixture_diagnostic='experiments/python-gamebub-v114/control-peer/diagnostics/20261108T234045208670Z/receipt.json')
 (S/'fault-injection-contract.json').write_text(json.dumps(injection,indent=2,sort_keys=True)+'\n');print('PASS_PEER_ONLY_REVERSIBLE_PRIVATE_CANCEL_AND_COMPLETE_FAIL_POSTSTATE_PREPARATION_NOT_RTL')
if __name__=='__main__':main()
