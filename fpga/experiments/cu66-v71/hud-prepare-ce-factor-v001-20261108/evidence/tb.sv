`timescale 1ns/1ps
module tb;
reg [3:0] state;
reg  rst;
reg  abort_i;
reg  abort_allowed;
reg  hud_pending;
reg  hud_requested;
reg  p_error;
reg  bank_error;
reg  b_error;
reg [7:0] p_code;
reg [7:0] bank_code;
reg [7:0] b_code;
reg  hud_result_valid;
reg [63:0] hud_result_generation;
reg [31:0] hud_result_frame_id;
reg [31:0] hud_result_reference_id;
reg [127:0] hud_result_tag;
reg [15:0] hud_result_words;
reg  hud_result_success;
reg  hud_drain_valid;
reg [63:0] hud_drain_generation;
reg [31:0] hud_drain_frame_id;
reg [1:0] hud_drain_bank;
reg [127:0] hud_drain_tag;
reg [15:0] hud_drain_words;
reg  hud_drain_success;
reg [63:0] active_generation;
reg [31:0] fid;
reg [31:0] rid;
reg [127:0] hud_expected;
reg [1:0] bank_write;
reg  cache_prepare_result_valid;
reg  cache_prepare_match;
reg  cache_prepare_result_success;
reg  ref_rsp_valid;
reg  ref_match;
reg  ref_rsp_error;
reg  q_rsp_valid;
reg [10:0] q_rsp_index;
reg [10:0] q_expected_index;
reg  packet_pending;
reg  p_req_valid;
reg  b_req_valid;
reg [16:0] calculated_packet_address;
reg [15:0] packet_length;
reg [31:0] age;
wire[2:0]old_p,new_p,old_f,new_f,old_nh,new_nh,old_ce,new_ce;wire[7:0]old_code[0:2],new_code[0:2];
ce_control #(.WATCHDOG_CYCLES(32'd0)) control0(.state(state),.rst(rst),.abort_i(abort_i),.abort_allowed(abort_allowed),.hud_pending(hud_pending),.hud_requested(hud_requested),.p_error(p_error),.bank_error(bank_error),.b_error(b_error),.p_code(p_code),.bank_code(bank_code),.b_code(b_code),.hud_result_valid(hud_result_valid),.hud_result_generation(hud_result_generation),.hud_result_frame_id(hud_result_frame_id),.hud_result_reference_id(hud_result_reference_id),.hud_result_tag(hud_result_tag),.hud_result_words(hud_result_words),.hud_result_success(hud_result_success),.hud_drain_valid(hud_drain_valid),.hud_drain_generation(hud_drain_generation),.hud_drain_frame_id(hud_drain_frame_id),.hud_drain_bank(hud_drain_bank),.hud_drain_tag(hud_drain_tag),.hud_drain_words(hud_drain_words),.hud_drain_success(hud_drain_success),.active_generation(active_generation),.fid(fid),.rid(rid),.hud_expected(hud_expected),.bank_write(bank_write),.cache_prepare_result_valid(cache_prepare_result_valid),.cache_prepare_match(cache_prepare_match),.cache_prepare_result_success(cache_prepare_result_success),.ref_rsp_valid(ref_rsp_valid),.ref_match(ref_match),.ref_rsp_error(ref_rsp_error),.q_rsp_valid(q_rsp_valid),.q_rsp_index(q_rsp_index),.q_expected_index(q_expected_index),.packet_pending(packet_pending),.p_req_valid(p_req_valid),.b_req_valid(b_req_valid),.calculated_packet_address(calculated_packet_address),.packet_length(packet_length),.age(age),.hud_prepare_valid(old_p[0]),.fatal(old_f[0]),.fatal_code(old_code[0]),.fatal_non_hud(old_nh[0]),.capture_effective(old_ce[0]));
ce_candidate #(.WATCHDOG_CYCLES(32'd0)) candidate0(.state(state),.rst(rst),.abort_i(abort_i),.abort_allowed(abort_allowed),.hud_pending(hud_pending),.hud_requested(hud_requested),.p_error(p_error),.bank_error(bank_error),.b_error(b_error),.p_code(p_code),.bank_code(bank_code),.b_code(b_code),.hud_result_valid(hud_result_valid),.hud_result_generation(hud_result_generation),.hud_result_frame_id(hud_result_frame_id),.hud_result_reference_id(hud_result_reference_id),.hud_result_tag(hud_result_tag),.hud_result_words(hud_result_words),.hud_result_success(hud_result_success),.hud_drain_valid(hud_drain_valid),.hud_drain_generation(hud_drain_generation),.hud_drain_frame_id(hud_drain_frame_id),.hud_drain_bank(hud_drain_bank),.hud_drain_tag(hud_drain_tag),.hud_drain_words(hud_drain_words),.hud_drain_success(hud_drain_success),.active_generation(active_generation),.fid(fid),.rid(rid),.hud_expected(hud_expected),.bank_write(bank_write),.cache_prepare_result_valid(cache_prepare_result_valid),.cache_prepare_match(cache_prepare_match),.cache_prepare_result_success(cache_prepare_result_success),.ref_rsp_valid(ref_rsp_valid),.ref_match(ref_match),.ref_rsp_error(ref_rsp_error),.q_rsp_valid(q_rsp_valid),.q_rsp_index(q_rsp_index),.q_expected_index(q_expected_index),.packet_pending(packet_pending),.p_req_valid(p_req_valid),.b_req_valid(b_req_valid),.calculated_packet_address(calculated_packet_address),.packet_length(packet_length),.age(age),.hud_prepare_valid(new_p[0]),.fatal(new_f[0]),.fatal_code(new_code[0]),.fatal_non_hud(new_nh[0]),.capture_effective(new_ce[0]));
ce_control #(.WATCHDOG_CYCLES(32'd1)) control1(.state(state),.rst(rst),.abort_i(abort_i),.abort_allowed(abort_allowed),.hud_pending(hud_pending),.hud_requested(hud_requested),.p_error(p_error),.bank_error(bank_error),.b_error(b_error),.p_code(p_code),.bank_code(bank_code),.b_code(b_code),.hud_result_valid(hud_result_valid),.hud_result_generation(hud_result_generation),.hud_result_frame_id(hud_result_frame_id),.hud_result_reference_id(hud_result_reference_id),.hud_result_tag(hud_result_tag),.hud_result_words(hud_result_words),.hud_result_success(hud_result_success),.hud_drain_valid(hud_drain_valid),.hud_drain_generation(hud_drain_generation),.hud_drain_frame_id(hud_drain_frame_id),.hud_drain_bank(hud_drain_bank),.hud_drain_tag(hud_drain_tag),.hud_drain_words(hud_drain_words),.hud_drain_success(hud_drain_success),.active_generation(active_generation),.fid(fid),.rid(rid),.hud_expected(hud_expected),.bank_write(bank_write),.cache_prepare_result_valid(cache_prepare_result_valid),.cache_prepare_match(cache_prepare_match),.cache_prepare_result_success(cache_prepare_result_success),.ref_rsp_valid(ref_rsp_valid),.ref_match(ref_match),.ref_rsp_error(ref_rsp_error),.q_rsp_valid(q_rsp_valid),.q_rsp_index(q_rsp_index),.q_expected_index(q_expected_index),.packet_pending(packet_pending),.p_req_valid(p_req_valid),.b_req_valid(b_req_valid),.calculated_packet_address(calculated_packet_address),.packet_length(packet_length),.age(age),.hud_prepare_valid(old_p[1]),.fatal(old_f[1]),.fatal_code(old_code[1]),.fatal_non_hud(old_nh[1]),.capture_effective(old_ce[1]));
ce_candidate #(.WATCHDOG_CYCLES(32'd1)) candidate1(.state(state),.rst(rst),.abort_i(abort_i),.abort_allowed(abort_allowed),.hud_pending(hud_pending),.hud_requested(hud_requested),.p_error(p_error),.bank_error(bank_error),.b_error(b_error),.p_code(p_code),.bank_code(bank_code),.b_code(b_code),.hud_result_valid(hud_result_valid),.hud_result_generation(hud_result_generation),.hud_result_frame_id(hud_result_frame_id),.hud_result_reference_id(hud_result_reference_id),.hud_result_tag(hud_result_tag),.hud_result_words(hud_result_words),.hud_result_success(hud_result_success),.hud_drain_valid(hud_drain_valid),.hud_drain_generation(hud_drain_generation),.hud_drain_frame_id(hud_drain_frame_id),.hud_drain_bank(hud_drain_bank),.hud_drain_tag(hud_drain_tag),.hud_drain_words(hud_drain_words),.hud_drain_success(hud_drain_success),.active_generation(active_generation),.fid(fid),.rid(rid),.hud_expected(hud_expected),.bank_write(bank_write),.cache_prepare_result_valid(cache_prepare_result_valid),.cache_prepare_match(cache_prepare_match),.cache_prepare_result_success(cache_prepare_result_success),.ref_rsp_valid(ref_rsp_valid),.ref_match(ref_match),.ref_rsp_error(ref_rsp_error),.q_rsp_valid(q_rsp_valid),.q_rsp_index(q_rsp_index),.q_expected_index(q_expected_index),.packet_pending(packet_pending),.p_req_valid(p_req_valid),.b_req_valid(b_req_valid),.calculated_packet_address(calculated_packet_address),.packet_length(packet_length),.age(age),.hud_prepare_valid(new_p[1]),.fatal(new_f[1]),.fatal_code(new_code[1]),.fatal_non_hud(new_nh[1]),.capture_effective(new_ce[1]));
ce_control #(.WATCHDOG_CYCLES(32'd3000000000)) control2(.state(state),.rst(rst),.abort_i(abort_i),.abort_allowed(abort_allowed),.hud_pending(hud_pending),.hud_requested(hud_requested),.p_error(p_error),.bank_error(bank_error),.b_error(b_error),.p_code(p_code),.bank_code(bank_code),.b_code(b_code),.hud_result_valid(hud_result_valid),.hud_result_generation(hud_result_generation),.hud_result_frame_id(hud_result_frame_id),.hud_result_reference_id(hud_result_reference_id),.hud_result_tag(hud_result_tag),.hud_result_words(hud_result_words),.hud_result_success(hud_result_success),.hud_drain_valid(hud_drain_valid),.hud_drain_generation(hud_drain_generation),.hud_drain_frame_id(hud_drain_frame_id),.hud_drain_bank(hud_drain_bank),.hud_drain_tag(hud_drain_tag),.hud_drain_words(hud_drain_words),.hud_drain_success(hud_drain_success),.active_generation(active_generation),.fid(fid),.rid(rid),.hud_expected(hud_expected),.bank_write(bank_write),.cache_prepare_result_valid(cache_prepare_result_valid),.cache_prepare_match(cache_prepare_match),.cache_prepare_result_success(cache_prepare_result_success),.ref_rsp_valid(ref_rsp_valid),.ref_match(ref_match),.ref_rsp_error(ref_rsp_error),.q_rsp_valid(q_rsp_valid),.q_rsp_index(q_rsp_index),.q_expected_index(q_expected_index),.packet_pending(packet_pending),.p_req_valid(p_req_valid),.b_req_valid(b_req_valid),.calculated_packet_address(calculated_packet_address),.packet_length(packet_length),.age(age),.hud_prepare_valid(old_p[2]),.fatal(old_f[2]),.fatal_code(old_code[2]),.fatal_non_hud(old_nh[2]),.capture_effective(old_ce[2]));
ce_candidate #(.WATCHDOG_CYCLES(32'd3000000000)) candidate2(.state(state),.rst(rst),.abort_i(abort_i),.abort_allowed(abort_allowed),.hud_pending(hud_pending),.hud_requested(hud_requested),.p_error(p_error),.bank_error(bank_error),.b_error(b_error),.p_code(p_code),.bank_code(bank_code),.b_code(b_code),.hud_result_valid(hud_result_valid),.hud_result_generation(hud_result_generation),.hud_result_frame_id(hud_result_frame_id),.hud_result_reference_id(hud_result_reference_id),.hud_result_tag(hud_result_tag),.hud_result_words(hud_result_words),.hud_result_success(hud_result_success),.hud_drain_valid(hud_drain_valid),.hud_drain_generation(hud_drain_generation),.hud_drain_frame_id(hud_drain_frame_id),.hud_drain_bank(hud_drain_bank),.hud_drain_tag(hud_drain_tag),.hud_drain_words(hud_drain_words),.hud_drain_success(hud_drain_success),.active_generation(active_generation),.fid(fid),.rid(rid),.hud_expected(hud_expected),.bank_write(bank_write),.cache_prepare_result_valid(cache_prepare_result_valid),.cache_prepare_match(cache_prepare_match),.cache_prepare_result_success(cache_prepare_result_success),.ref_rsp_valid(ref_rsp_valid),.ref_match(ref_match),.ref_rsp_error(ref_rsp_error),.q_rsp_valid(q_rsp_valid),.q_rsp_index(q_rsp_index),.q_expected_index(q_expected_index),.packet_pending(packet_pending),.p_req_valid(p_req_valid),.b_req_valid(b_req_valid),.calculated_packet_address(calculated_packet_address),.packet_length(packet_length),.age(age),.hud_prepare_valid(new_p[2]),.fatal(new_f[2]),.fatal_code(new_code[2]),.fatal_non_hud(new_nh[2]),.capture_effective(new_ce[2]));

integer checked=0,unknown_cases=0,st,mask,flags,i;
task defaults;begin
state=0;rst=0;abort_i=0;abort_allowed=0;hud_pending=0;hud_requested=0;p_error=0;bank_error=0;b_error=0;p_code=0;bank_code=0;b_code=0;hud_result_valid=0;hud_result_generation=0;hud_result_frame_id=0;hud_result_reference_id=0;hud_result_tag=0;hud_result_words=0;hud_result_success=0;hud_drain_valid=0;hud_drain_generation=0;hud_drain_frame_id=0;hud_drain_bank=0;hud_drain_tag=0;hud_drain_words=0;hud_drain_success=0;active_generation=0;fid=0;rid=0;hud_expected=0;bank_write=0;cache_prepare_result_valid=0;cache_prepare_match=0;cache_prepare_result_success=0;ref_rsp_valid=0;ref_match=0;ref_rsp_error=0;q_rsp_valid=0;q_rsp_index=0;q_expected_index=0;packet_pending=0;p_req_valid=0;b_req_valid=0;calculated_packet_address=0;packet_length=0;age=0;
abort_allowed=1;active_generation=64'h1234567800000042;fid=37;rid=36;hud_expected=128'h123456789abcdef013579bdf2468ace0;bank_write=1;
hud_result_generation=active_generation;hud_result_frame_id=fid;hud_result_reference_id=rid;hud_result_tag=hud_expected;hud_result_words=21120;hud_result_success=1;
hud_drain_generation=active_generation;hud_drain_frame_id=fid;hud_drain_bank=bank_write;hud_drain_tag=hud_expected;hud_drain_words=21120;hud_drain_success=1;
cache_prepare_match=1;cache_prepare_result_success=1;ref_match=1;q_rsp_index=5;q_expected_index=5;packet_pending=1;packet_length=1024;calculated_packet_address=512;
p_code=8'h08;bank_code=8'h07;b_code=8'h39;
end endtask
task check;integer n;begin
 #1;
 for(n=0;n<3;n=n+1)begin
  if(old_p[n]!==new_p[n]||old_ce[n]!==new_ce[n]||old_f[n]!==new_f[n]||old_code[n]!==new_code[n]||old_nh[n]!==new_nh[n])
   $fatal(1,"miter mismatch state=%b mask=%h flags=%h wdcase=%0d oldprep=%b newprep=%b oldfatal=%b newfatal=%b",state,mask,flags,n,old_p[n],new_p[n],old_f[n],new_f[n]);
 end
 checked=checked+1;
end endtask
initial begin
 defaults();
 // Every encoded state, eight independent non-HUD fault drivers, two HUD
 // failure drivers and requested/abort/reset/pending combinations.
 for(st=0;st<16;st=st+1)begin
  state=st;
  for(mask=0;mask<1024;mask=mask+1)begin
   p_error=mask[0];bank_error=mask[1];b_error=mask[2];
   cache_prepare_result_valid=mask[3];cache_prepare_result_success=!mask[3];
   ref_rsp_valid=mask[4];ref_rsp_error=mask[4];q_rsp_valid=mask[5];q_rsp_index=mask[5]?6:5;
   packet_pending=!mask[6];p_req_valid=mask[6];calculated_packet_address=mask[6]?1024:512;
   age=mask[7]?32'd3000000000:0;hud_result_valid=mask[8];hud_result_success=!mask[8];hud_drain_valid=mask[9];hud_drain_success=!mask[9];
   for(flags=0;flags<16;flags=flags+1)begin hud_requested=flags[0];abort_i=flags[1];rst=flags[2];hud_pending=flags[3];check();end
  end
 end
 $display("CE_EXHAUSTIVE_PASS states16 fault_masks1024 control_flags16 checked=%0d watchdog_profiles3",checked);
 for(st=0;st<16;st=st+1)for(i=0;i<17;i=i+1)for(flags=0;flags<16;flags=flags+1)begin
  defaults();state=st;hud_requested=flags[0];abort_i=flags[1];rst=flags[2];hud_pending=flags[3];hud_result_valid=1;hud_drain_valid=1;
  case(i)
   0:hud_result_generation^=64'd1;1:hud_result_generation^=64'h8000000000000000;
   2:hud_result_frame_id^=1;3:hud_result_frame_id^=32'h80000000;
   4:hud_result_reference_id^=1;5:hud_result_words=21119;6:hud_result_words=21121;
   7:hud_result_tag^=128'd1;8:hud_result_tag^=128'h80000000000000000000000000000000;
   9:hud_drain_generation^=1;10:hud_drain_frame_id^=1;11:hud_drain_bank=3;
   12:hud_drain_tag^=1;13:hud_drain_words=0;14:age=1;15:age=32'd2999999999;16:age=32'hffffffff;
  endcase
  ref_rsp_valid=flags[1];ref_rsp_error=flags[1];check();
 end
 for(st=0;st<16;st=st+1)begin defaults();state=st;abort_i=1;abort_allowed=0;b_req_valid=1;packet_pending=0;calculated_packet_address=1024;check();end
 // Directed four-state checks are NOT an exhaustive X/Z formal proof.
 for(st=0;st<16;st=st+1)for(i=0;i<12;i=i+1)begin
  defaults();state=st;hud_result_valid=1;hud_drain_valid=1;
  case(i)
   0:hud_requested=1'bx;1:hud_requested=1'bz;2:abort_i=1'bx;3:rst=1'bx;
   4:state=4'bx101;5:state=4'bz100;6:hud_pending=1'bx;7:hud_result_generation=64'bx;
   8:hud_drain_generation=64'bx;9:hud_result_success=1'bx;10:q_rsp_valid=1'bx;11:p_error=1'bx;
  endcase
  check();unknown_cases=unknown_cases+1;
 end
 $display("CE_DIRECTED_PASS identity_classes17 unknown_cases=%0d total_stimuli=%0d watchdog_profiles3",unknown_cases,checked);
 $display("CE_SOURCE_EXTRACTED_MITER_PASS no_latency_change full_fatal_code_preserved");$finish;
end
initial begin #10000000;$fatal(1,"miter watchdog");end
endmodule
