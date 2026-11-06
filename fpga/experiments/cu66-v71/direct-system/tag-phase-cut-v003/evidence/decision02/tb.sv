`timescale 1ns/1ps
module tb;
reg [3:0] fs=0;
reg  abort_i=0;
reg  write_done=0;
reg  write_pending=0;
reg  write_error=0;
reg  e_error=0;
reg [7:0] e_code=0;
reg  s_error=0;
reg [7:0] s_code=0;
reg  dq_valid=0;
reg  dq_error=0;
reg  idct_valid=0;
reg  idct_error=0;
reg  recon_valid=0;
reg  recon_error=0;
reg [31:0] recon_id=0;
reg [31:0] tid=0;
reg  rows_error=0;
reg [7:0] rows_code=0;
reg  rows_result_valid=0;
reg [255:0] hash_value=0;
reg [127:0] wanted_tag=0;
wire same,invariant,same_errors;tagcut_miter dut(.*);integer checks=0,f,c,t,i,k;
function automatic bit4(input integer n);case(n)0:bit4=0;1:bit4=1;2:bit4=1'bx;3:bit4=1'bz;endcase endfunction
task check;begin #1;if((^fs)!==1'bx && (fs!==4'd5 || write_pending===1'b0))begin if(dut.old_tag!==dut.new_tag||dut.old_fail!==dut.new_fail||dut.old_code!==dut.new_code||dut.old_kill!==dut.new_kill)$fatal(1,"4state decision mismatch fs=%b",fs);checks++;end end endtask
task clear_flags;begin write_done=0;write_pending=0;write_error=0;e_error=0;s_error=0;dq_valid=0;dq_error=0;idct_valid=0;idct_error=0;recon_valid=0;recon_error=0;rows_error=0;end endtask
initial begin
 e_code=8'h03;s_code=8'h04;rows_code=8'h05;recon_id=0;tid=0;
 // Every packed4state value, higher-error prefix context and tag/valid condition.
 for(f=0;f<256;f++)begin
  for(k=0;k<4;k++)fs[k]=bit4((f>>(2*k))&3);
  for(c=0;c<9;c++)begin
   clear_flags();case(c)1:begin write_done=1;write_pending=1;write_error=1;end
    2:e_error=1;3:s_error=1;4:begin dq_valid=1;dq_error=1;end
    5:begin idct_valid=1;idct_error=1;end 6:begin recon_valid=1;recon_error=1;end
    7:rows_error=1;8:begin write_done=1;write_pending=1;write_error=1;e_error=1;s_error=1;rows_error=1;end endcase
   for(t=0;t<4;t++)begin rows_result_valid=bit4(t);hash_value=0;wanted_tag=1;check();wanted_tag=0;check();wanted_tag[17]=1'bx;check();end
  end
 end
 // Unknown higher-priority flags and metadata; compare actual procedural-if behavior.
 for(i=0;i<20000;i++)begin for(k=0;k<4;k++)fs[k]=bit4($unsigned($random)%4);abort_i=$random;write_done=bit4($unsigned($random)%4);write_pending=$random;write_error=bit4($unsigned($random)%4);e_error=bit4($unsigned($random)%4);s_error=bit4($unsigned($random)%4);dq_valid=$random;dq_error=bit4($unsigned($random)%4);idct_valid=$random;idct_error=bit4($unsigned($random)%4);recon_valid=$random;recon_error=bit4($unsigned($random)%4);rows_error=bit4($unsigned($random)%4);rows_result_valid=bit4($unsigned($random)%4);hash_value=0;wanted_tag=0;if(i%3==0)hash_value[128+i%128]=bit4(2+i%2);else wanted_tag[i%128]=1;check();end
 clear_flags();fs=5;abort_i=0;write_done=1;write_pending=1;write_error=1;rows_result_valid=0;hash_value=0;wanted_tag=0;#1;
 if(dut.old_tag!==0 || dut.new_tag!==1 || dut.old_fail!==dut.new_fail || dut.old_code!==dut.new_code)$fatal(1,"expected unreachable-state counterexample absent");
 $display("EXPECTED_UNREACHABLE_RESULT_WITH_PENDING_WRITE_TAG_DIFF old=0 new=1 errors_unchanged=1");
 $display("TAG_FEEDBACK_CUT_FOURSTATE_PASS checks=%0d packed_fs4state=256",checks);$finish;
end endmodule
