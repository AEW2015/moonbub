#!/usr/bin/env python3
"""Source-bound same-edge certified private kill; no command/controller latency edit."""
import hashlib,json,pathlib,sys
sys.dont_write_bytecode=True
R=pathlib.Path(__file__).resolve().parents[3];S=R/'fpga/experiments/cu66-v115-owner'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 original=R/'fpga/experiments/cu66-v114-control/cs88_pipeline_v91k.sv';assert sha(original)=='9e6d2b88ad0f06ca0df5a5218be0d78a9fa9d9e8151d3b0b43aebaafc3ba76bd';text=original.read_text();edits=[]
 def edit(before,after):
  nonlocal text
  assert text.count(before)==1,before[:80];text=text.replace(before,after,1);edits.append(dict(before=before,after=after))
 edit('    logic base_kill_valid, base_kill_sent;','''    logic base_kill_valid, base_kill_sent;
    // IV115.O1: authorization is born with the real registered kill tuple and
    // retained until a new command/reset revokes it. It is not a second copy of
    // the one-edge valid pulse. Raw valid/tag remain visible to old probes.
    logic base_kill_authorized;''')
 edit('    assign base_abort=abort_packet||(base_kill_valid&&base_kill_owner==owner_sequence);','''    // Current real transitions capture the owner atomically at both kill births.
    // A retired private valid/tag injection after a new command has no certificate.
    assign base_abort=abort_packet||(base_kill_valid&&base_kill_authorized);''')
 edit('            base_kill_owner<=0;base_kill_sent<=0;terminal_valid<=0;terminal_cause<=0;','            base_kill_owner<=0;base_kill_sent<=0;base_kill_authorized<=0;terminal_valid<=0;terminal_cause<=0;')
 edit('            if(!base_kill_sent)begin base_kill_valid<=1;base_kill_owner<=owner_sequence;base_kill_sent<=1;end','            if(!base_kill_sent)begin base_kill_valid<=1;base_kill_owner<=owner_sequence;base_kill_sent<=1;base_kill_authorized<=1;end')
 edit('                terminal_valid<=0;terminal_cause<=0;base_kill_sent<=0;cache_abort_rearm<=0;','                terminal_valid<=0;terminal_cause<=0;base_kill_sent<=0;base_kill_authorized<=0;cache_abort_rearm<=0;')
 edit('                    base_kill_valid<=1;base_kill_owner<=owner_sequence;base_kill_sent<=1;','                    base_kill_valid<=1;base_kill_owner<=owner_sequence;base_kill_sent<=1;base_kill_authorized<=1;')
 edit('`ifndef SYNTHESIS\n    always_ff @(posedge clk)begin','''`ifndef SYNTHESIS
    // Independent literal birth predicate follows the sole always_ff priority.
    // The certificate is NOT proof of arbitrary private register fault recovery.
    logic certificate_birth;
    assign certificate_birth=!reset &&
        ((abort_packet && !base_kill_sent) ||
         (!abort_packet && !command_accept && !accepted_start && qualified_fault &&
          !terminal_valid && (inverse_fault||reconstruction_fault) && !base_kill_sent));
    assert property(@(posedge clk) certificate_birth |=>
        base_kill_valid && base_kill_authorized &&
        base_kill_owner==$past(owner_sequence) && owner_sequence==$past(owner_sequence))
        else $fatal(1,"real kill birth lost certificate or captured owner");
    assert property(@(posedge clk) base_kill_valid && base_kill_authorized |->
        base_kill_owner==owner_sequence && base_abort && coefficients.abort_packet)
        else $fatal(1,"certified kill owner/delivery edge differs");
    assert property(@(posedge clk) base_kill_valid && base_kill_authorized |->
        $past(certificate_birth))
        else $fatal(1,"certified pulse has no actual birth");
    assert property(@(posedge clk) base_kill_valid && base_kill_authorized |=>
        !base_kill_valid)
        else $fatal(1,"private kill pulse extended beyond original edge");
    assert property(@(posedge clk) reset || command_accept |=> !base_kill_authorized)
        else $fatal(1,"new command/reset retained old kill authorization");
    assert property(@(posedge clk) !reset && !command_accept && !certificate_birth |=>
        $stable(base_kill_authorized))
        else $fatal(1,"kill authorization changed without birth or revocation");
    assert property(@(posedge clk) !abort_packet && base_kill_valid && !base_kill_authorized |->
        !base_abort && !coefficients.abort_packet)
        else $fatal(1,"uncertified stale private pulse canceled producer");
    assert property(@(posedge clk) abort_packet |-> base_abort && coefficients.abort_packet)
        else $fatal(1,"external abort lost its original direct edge");
    always_ff @(posedge clk)begin''')
 target=S/'cs88_pipeline_v91k.sv';target.write_text(text);reverse=text
 for e in reversed(edits):assert reverse.count(e['after'])==1;reverse=reverse.replace(e['after'],e['before'],1)
 assert reverse==original.read_text()
 recipe=dict(schema='v115-owner-held-certificate-no-new-edge-v1',original=str(original.relative_to(R)),original_sha256=sha(original),candidate=str(target.relative_to(R)),candidate_sha256=sha(target),edits=edits,contract='IV115.O1: keep raw valid/tag and original private/external kill edges; real birth captures tag and held authorization atomically; reset/new command revokes authorization. Preserve stale-private-injection oracle after new admission. No extra public cycle, physical drain or counter change.',original_assertions_removed=0,source_review_required=True,qualification_status='PREPARED_NOT_RUN',arbitrary_private_corruption_recovery_claim=False)
 (S/'edit-recipe.json').write_text(json.dumps(recipe,indent=2,sort_keys=True)+'\n');print('PREPARED',recipe['candidate_sha256'])
if __name__=='__main__':main()
