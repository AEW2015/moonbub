"""Actual decision blocks under separately proved post-reset reachable invariant."""
from pathlib import Path
parent=Path(__file__).with_name('test_tag_feedback_cut.py');s=parent.read_text();s=s.replace('direct-system/tag-feedback-cut-v002','direct-system/tag-phase-cut-v003')
s=s.replace("logic=text[start:end];","logic=((d/'qualifier-logic.txt').read_text()if kind=='new'else'')+text[start:end];")
s=s.replace('reg fail_without_tag;','reg fail_for_tag_valid;')
s=s.replace(',output same);',',output same,output invariant,output same_errors);')
s=s.replace("miter+='assign same=","miter+='assign invariant=(fs!=5)||!write_pending;\\nassign same_errors=(old_fail==new_fail)&&(old_code==new_code)&&(old_kill==new_kill);\\nassign same=")
s=s.replace("modules=''","modules='`default_nettype none\\n'")
s=s.replace('wire same;tagcut_miter dut(.*);','wire same,invariant,same_errors;tagcut_miter dut(.*);')
s=s.replace('task check;begin #1;if(dut.old_tag',"task check;begin #1;if((^fs)!==1'bx && (fs!==4'd5 || write_pending===1'b0))begin if(dut.old_tag")
s=s.replace('checks++;end endtask','checks++;end end endtask')
s=s.replace(' $display("TAG_FEEDBACK_CUT_FOURSTATE_PASS', ''' clear_flags();fs=5;abort_i=0;write_done=1;write_pending=1;write_error=1;rows_result_valid=0;hash_value=0;wanted_tag=0;#1;
 if(dut.old_tag!==0 || dut.new_tag!==1 || dut.old_fail!==dut.new_fail || dut.old_code!==dut.new_code)$fatal(1,"expected unreachable-state counterexample absent");
 $display("EXPECTED_UNREACHABLE_RESULT_WITH_PENDING_WRITE_TAG_DIFF old=0 new=1 errors_unchanged=1");
 $display("TAG_FEEDBACK_CUT_FOURSTATE_PASS''')
s=s.replace('sat -verify -prove same 1','sat -set invariant 1 -verify -prove same 1')
s=s.replace("'SAT_state_assumptions':'None, all16binaryfs values'","'SAT_state_assumptions':'Only separately proved RESULT_HOLD->!write_pending; all other inputs/child errors unconstrained'")
s=s.replace("'fourstate_fs_values':256,'fourstate_checks':47648","'fourstate_scope':'Post-reset known FSM/writepending controls; arbitrary X/Z error/data; packed unknown FSM deliberately not claimed equivalent','unreachable_counterexample_retained':True")
s=s.replace('PASS_ACTUAL_DECISION_BLOCK_UNCONSTRAINED_BINARY_SAT_AND_PACKED_FOURSTATE','PASS_REACHABLE_STATE_DECISION_BLOCK_BINARY_AND_FOURSTATE_EQUIVALENCE')
s=s.replace('packed_fs4state=256','generated_fs4state256_filtered_to_known_postreset_controls=1')
exec(compile(s,str(parent),'exec'),globals())
