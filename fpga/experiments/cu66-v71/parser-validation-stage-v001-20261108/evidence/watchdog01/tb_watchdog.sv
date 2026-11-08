`timescale 1ns/1ps
module tb_watchdog;
reg clk=0,rst=1;always #5 clk=~clk;
wire busy,error,done;wire[7:0]error_code,stage;reg[7:0]header[0:59];integer checks=0;
cu71_receiver_final_v022 #(.WATCHDOG_CYCLES(32'd3000000000)) dut(.clk(clk),.rst(rst),.abort_i('0),.clear_fault('0),.start_valid('0),.start_generation('0),.start_packet_bytes('0),.packet_req_ready('0),.packet_rsp_valid('0),.packet_rsp_generation('0),.packet_rsp_sequence('0),.packet_rsp_address('0),.packet_rsp_data('0),.ref_req_ready('0),.ref_rsp_valid('0),.ref_rsp_generation('0),.ref_rsp_bank('0),.ref_rsp_plane('0),.ref_rsp_index('0),.ref_rsp_pixels('0),.ref_rsp_error('0),.write_ready('0),.write_done_valid('0),.write_done_generation('0),.write_done_bank('0),.write_done_plane('0),.write_done_index('0),.write_done_error('0),.memory_drained('0),.hud_prepare_ready('0),.hud_result_valid('0),.hud_result_generation('0),.hud_result_frame_id('0),.hud_result_reference_id('0),.hud_result_tag('0),.hud_result_words('0),.hud_result_success('0),.hud_drain_valid('0),.hud_drain_generation('0),.hud_drain_frame_id('0),.hud_drain_bank('0),.hud_drain_tag('0),.hud_drain_words('0),.hud_drain_success('0),.software_command_ready('0),.software_ack_valid('0),.software_ack_opcode('0),.software_ack_generation('0),.software_ack_frame_id('0),.software_ack_success('0),.cache_prepare_start_ready('0),.cache_prepare_result_valid('0),.cache_prepare_result_generation('0),.cache_prepare_result_frame_id('0),.cache_prepare_result_success('0),.cache_prepare_result_slot('0),.cache_worker_drained('0),.presentation_ready('0),.vblank('0),.scanout_drained('0),.presented_generation('0),.presented_frame_id('0),.presented_cache_slot('0),.diag_address('0),.busy(busy),.error(error),.error_code(error_code),.stage(stage),.done(done));
task tick;begin @(posedge clk);#1;end endtask
task ck(input bit ok,input string s);begin checks++;if(!ok)$fatal(1,"%s code=%02x stage=%0d age=%0d",s,error_code,stage,dut.age);end endtask
task setup(input reg[31:0]age);
 begin
  @(negedge clk);rst=1;tick();@(negedge clk);rst=0;
  // Actual receiver+actual parser. Unrelated bank/base datapaths are explicitly inert.
  dut.state=dut.METADATA;dut.age=age;dut.packet_length=49152;
  dut.parser.state=dut.parser.CHECK_INNER;dut.parser.packet_bytes=49152;dut.parser.inner_bytes=1000;dut.parser.inner_length_total=1000;
  dut.parser.outer_validated=1;dut.parser.inner_validated=0;
  for(integer j=0;j<60;j++)dut.parser.inner_header[j]=header[j];
  dut.parser.metadata_key=header[5][0];dut.parser.metadata_frame_id={header[13],header[12],header[11],header[10]};dut.parser.metadata_reference_id={header[17],header[16],header[15],header[14]};
  for(integer j=0;j<16;j++)dut.parser.metadata_reference_tag[127-8*j-:8]=header[24+j];
  // A known code7-only zero plane length. Code6 remains good.
  for(integer j=0;j<4;j++)dut.parser.inner_header[48+j]=0;
 end
endtask
task cutoff(input reg[31:0]age,input reg[7:0]wanted);
 begin setup(age);tick();tick();tick();
  ck(error&&error_code==wanted,"actual owner cutoff priority");
  $display("WATCHDOG initial_age=%0d code=%02x",age,error_code);
 end
endtask
initial begin
 $readmemh("header.hex",header);
 // These services cannot fire in this focused METADATA control test.
 force dut.bank_error=0;force dut.b_error=0;force dut.b_req_valid=0;force dut.q_rsp_valid=0;
 cutoff(32'd2999999998,8'h17);
`ifdef STAGED
 cutoff(32'd2999999999,8'h7f);
`else
 cutoff(32'd2999999999,8'h17);
`endif
 cutoff(32'd3000000000,8'h7f);
 // Both causes simultaneously true: unchanged parser-error-before-watchdog ordering.
 setup(32'd3000000000);force dut.p_error=1;force dut.p_code=8'd6;tick();
 ck(error&&error_code==8'h16,"simultaneous parser code6 wins watchdog");release dut.p_error;release dut.p_code;
 $display("WATCHDOG_ACTUAL_RECEIVER_CONTROL_PASS checks=%0d",checks);$finish;
end
endmodule
