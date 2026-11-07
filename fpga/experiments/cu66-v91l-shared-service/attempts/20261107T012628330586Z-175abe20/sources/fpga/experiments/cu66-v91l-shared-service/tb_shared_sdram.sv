`timescale 1ns/1ps
`default_nettype none
module tb_shared_sdram #(parameter real T_AC_NS=2.0);
 logic  clk=0;
 logic  power_on_reset=0;
 logic  wr_reset=0;
 logic  wr_cancel=0;
 logic  wr_req_valid=0;
 logic  wr_rsp_ready=0;
 logic  wr_req_ready /* verilator public_flat_rw */;
 logic  wr_rsp_valid /* verilator public_flat_rw */;
 logic  wr_rsp_error /* verilator public_flat_rw */;
 logic [31:0] wr_req_epoch=0;
 logic [31:0] wr_req_token=0;
 logic [1:0] wr_req_bank=0;
 logic [19:0] wr_req_addr=0;
 logic [63:0] wr_req_data=0;
 logic [31:0] wr_rsp_epoch /* verilator public_flat_rw */;
 logic [31:0] wr_rsp_token /* verilator public_flat_rw */;
 logic [1:0] wr_rsp_bank /* verilator public_flat_rw */;
 logic [19:0] wr_rsp_addr /* verilator public_flat_rw */;
 logic  wr_busy /* verilator public_flat_rw */;
 logic  wr_pending /* verilator public_flat_rw */;
 logic [2:0] wr_state /* verilator public_flat_rw */;
 logic [2:0] wr_word_index /* verilator public_flat_rw */;
 logic [31:0] wr_rows /* verilator public_flat_rw */;
 logic [31:0] wr_words_accepted /* verilator public_flat_rw */;
 logic [31:0] wr_words_retired /* verilator public_flat_rw */;
 logic [31:0] wr_responses /* verilator public_flat_rw */;
 logic [31:0] wr_cancels /* verilator public_flat_rw */;
 logic [31:0] wr_invalid /* verilator public_flat_rw */;
 logic  rd_reset=0;
 logic  rd_cancel=0;
 logic  rd_req_valid=0;
 logic  rd_rsp_ready=0;
 logic  rd_req_ready /* verilator public_flat_rw */;
 logic  rd_rsp_valid /* verilator public_flat_rw */;
 logic  rd_rsp_error /* verilator public_flat_rw */;
 logic [31:0] rd_req_epoch=0;
 logic [31:0] rd_req_generation=0;
 logic [1:0] rd_req_bank=0;
 logic [18:0] rd_req_addr=0;
 logic [127:0] rd_rsp_data /* verilator public_flat_rw */;
 logic [31:0] rd_rsp_epoch /* verilator public_flat_rw */;
 logic [31:0] rd_rsp_generation /* verilator public_flat_rw */;
 logic [1:0] rd_rsp_bank /* verilator public_flat_rw */;
 logic [18:0] rd_rsp_addr /* verilator public_flat_rw */;
 logic  rd_busy /* verilator public_flat_rw */;
 logic  rd_pending /* verilator public_flat_rw */;
 logic [2:0] rd_state /* verilator public_flat_rw */;
 logic [3:0] rd_beats /* verilator public_flat_rw */;
 logic [31:0] rd_requests /* verilator public_flat_rw */;
 logic [31:0] rd_commands /* verilator public_flat_rw */;
 logic [31:0] rd_count_beats /* verilator public_flat_rw */;
 logic [31:0] rd_responses /* verilator public_flat_rw */;
 logic [31:0] rd_cancels /* verilator public_flat_rw */;
 logic [31:0] rd_invalid /* verilator public_flat_rw */;
 logic [1:0] source_owner /* verilator public_flat_rw */;
 logic [31:0] writer_grants /* verilator public_flat_rw */;
 logic [31:0] reader_grants /* verilator public_flat_rw */;
 logic [31:0] writer_commands /* verilator public_flat_rw */;
 logic [31:0] reader_commands /* verilator public_flat_rw */;
 logic [31:0] owner_releases /* verilator public_flat_rw */;
 logic  controller_valid /* verilator public_flat_rw */;
 logic  controller_write /* verilator public_flat_rw */;
 logic [23:0] controller_addr /* verilator public_flat_rw */;
 logic [15:0] controller_data /* verilator public_flat_rw */;
 logic  controller_ready /* verilator public_flat_rw */;
 logic  controller_idle /* verilator public_flat_rw */;
 logic  controller_read_valid /* verilator public_flat_rw */;
 logic [15:0] controller_read_data /* verilator public_flat_rw */;
 logic [23:0] peek_addr=0;
 logic [15:0] peek_data /* verilator public_flat_rw */;
 integer writes /* verilator public_flat_rw */;
 integer readwords /* verilator public_flat_rw */;
 integer refreshes /* verilator public_flat_rw */;
 integer mrs /* verilator public_flat_rw */;
 integer activates /* verilator public_flat_rw */;
 integer precharges /* verilator public_flat_rw */;
 shared_sdram_timed #(.T_AC_NS(T_AC_NS),.REFRESH_CYCLES(80)) dut(.*);
 initial forever #5 clk=~clk;
 integer checks=0;
 task automatic check(input bit ok,input string label_text);
  assert(ok)else $fatal(1,"check FAILED: %s",label_text);
  checks=checks+1;$display("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%s\"}",label_text);
 endtask
 task automatic step(input integer count=1);repeat(count)@(negedge clk);endtask
 task automatic quiet;while(source_owner!=0||!controller_ready||!controller_idle)step();endtask
 task automatic wr_issue(input logic [19:0] address,input logic [63:0] data,input logic [1:0] bank=0);
  wr_req_addr=address;wr_req_data=data;wr_req_bank=bank;wr_req_token=wr_req_token+1;wr_req_valid=1;
  do begin @(posedge clk);end while(!wr_req_ready);
  @(negedge clk);wr_req_valid=0;
 endtask
 task automatic rd_issue(input logic [18:0] address,input logic [1:0] bank=0);
  rd_req_addr=address;rd_req_bank=bank;rd_req_generation=rd_req_generation+1;rd_req_valid=1;
  do begin @(posedge clk);end while(!rd_req_ready);
  @(negedge clk);rd_req_valid=0;
 endtask
 task automatic wr_finish(input bit expected_error=0);
  while(!wr_rsp_valid)step();
  check(wr_rsp_error==expected_error,"writer_expected_error");
  wr_rsp_ready=1;step();wr_rsp_ready=0;
 endtask
 task automatic rd_finish(input bit expected_error=0);
  while(!rd_rsp_valid)step();
  check(rd_rsp_error==expected_error,"reader_expected_error");
  if(expected_error)check(rd_rsp_data==0,"canceled_read_data_zero");
  rd_rsp_ready=1;step();rd_rsp_ready=0;
 endtask
 function automatic logic [127:0] initial_line(input logic [23:0] word_address);
  logic [127:0] result;
  for(integer i=0;i<8;i=i+1)result[i*16+:16]=16'(word_address+24'(i))^16'h5a3c;
  return result;
 endfunction
 task automatic audit_words(input logic [23:0] address,input logic [63:0] data,input integer count=4);
  for(integer i=0;i<count;i=i+1)begin
   peek_addr=address+24'(i);#1;check(peek_data==data[i*16+:16],"actual_pin_memory_word");
  end
 endtask
 integer before_commands,before_writes,before_reads,grants_seen;
 logic [1:0] last_owner;
 logic [127:0] saved_read;
 logic [63:0] payload;
 initial begin
  power_on_reset=1;wr_req_epoch=1;rd_req_epoch=2;rd_req_generation=10;
  step(4);power_on_reset=0;quiet();
   $display("INIT_COUNTERS mrs=%0d refreshes=%0d writes=%0d",mrs,refreshes,writes);
  check(mrs==1&&refreshes>=2,"controller_initialized_real_pins");
  // Concurrent clients in separate physical banks; writer owns the full prefix.
  fork
   begin wr_issue(0,64'h1122334455667788,1);wr_finish();end
   rd_issue(0,2);
  join
  // The reader may only accept after the held writer response was acknowledged.
  rd_finish();quiet();audit_words(24'h400000,64'h1122334455667788);
  check(rd_rsp_data==initial_line(24'h800000),"concurrent_different_banks");
  // Write ACK orders subsequent physical BL8 data, with independent pin peeks.
  wr_issue(0,64'h0123456789abcdef);wr_finish();quiet();
  audit_words(0,64'h0123456789abcdef);
  rd_issue(0);while(!rd_rsp_valid)step();
  check(rd_rsp_data[63:0]==64'h0123456789abcdef,"write_ack_then_same_address_read");
  saved_read=rd_rsp_data;before_commands=integer'(writer_commands+reader_commands);
  wr_req_valid=1;wr_req_addr=8;wr_req_data=64'h8877665544332211;
  rd_cancel=1;rd_reset=1;
  repeat(9)begin step();check(source_owner==2&&rd_rsp_valid&&rd_rsp_data==saved_read&&!rd_rsp_error&&integer'(writer_commands+reader_commands)==before_commands,"held_success_immutable_and_ownership_blocked");end
  rd_cancel=0;rd_reset=0;rd_rsp_ready=1;step();rd_rsp_ready=0;
  do begin @(posedge clk);end while(!wr_req_ready);
  @(negedge clk);wr_req_valid=0;wr_finish();quiet();
  audit_words(32,64'h8877665544332211);
  // Both clients continually offer requests across each ACK; strict round robin.
  wr_req_valid=1;rd_req_valid=1;wr_rsp_ready=1;rd_rsp_ready=1;
  wr_req_addr=32;rd_req_addr=64;wr_req_data=64'h5555aaaa3333cccc;
  grants_seen=0;last_owner=0;
  while(grants_seen<8)begin
   step();
   if(source_owner!=0&&source_owner!=last_owner)begin
    if(last_owner!=0)check(source_owner!=last_owner,"round_robin_whole_transaction");
    last_owner=source_owner;grants_seen=grants_seen+1;
   end
  end
  wr_req_valid=0;rd_req_valid=0;
  while(source_owner!=0)step();wr_rsp_ready=0;rd_rsp_ready=0;quiet();
  check(grants_seen==8,"continuous_valid_reaccept_guard_and_fairness");
  // Invalid identities are accepted logically but produce no physical command.
  before_commands=integer'(writer_commands+reader_commands);
  wr_req_epoch=0;wr_issue(0,0);wr_finish(1);quiet();wr_req_epoch=1;
  wr_issue(1,0);wr_finish(1);quiet();wr_issue(0,0,3);wr_finish(1);quiet();
  rd_req_epoch=0;rd_issue(0);rd_finish(1);quiet();rd_req_epoch=2;
  rd_req_generation=32'hffffffff;rd_issue(0);rd_finish(1);quiet();
  rd_issue(1);rd_finish(1);quiet();rd_issue(0,3);rd_finish(1);quiet();
  check(integer'(writer_commands+reader_commands)==before_commands,"invalid_identities_no_physical_commands");
  // Cancellation after logical accept and before any controller command.
  before_commands=integer'(writer_commands+reader_commands);
  wr_issue(0,0);wr_cancel=1;wr_finish(1);wr_cancel=0;quiet();
  rd_issue(0);rd_cancel=1;rd_finish(1);rd_cancel=0;quiet();
  check(integer'(writer_commands+reader_commands)==before_commands,"cancel_before_command");
  // Cancel each accepted writer prefix and drain unchanged physical controller.
  for(integer prefix=1;prefix<=3;prefix=prefix+1)begin
   before_writes=writes;before_commands=integer'(writer_commands);
   payload=64'hf1e2d3c4b5a69788^64'(prefix);
   wr_issue(128,payload);
   while(integer'(writer_commands)-before_commands<prefix)step();
   wr_cancel=1;wr_finish(1);wr_cancel=0;quiet();
   check(integer'(writer_commands)-before_commands==prefix&&writes-before_writes==prefix&&!wr_pending,"canceled_writer_prefix_physically_drained");
   audit_words(512,payload,prefix);
  end
  // Cancel accepted BL8 before capture 0 and after capture 3; warm reset same drain.
  for(integer captures=0;captures<=3;captures=captures+3)begin
   before_reads=readwords;rd_issue(0);
   while(!rd_pending||integer'(rd_beats)<captures)step();
   rd_cancel=1;rd_finish(1);rd_cancel=0;quiet();
   check(readwords-before_reads==8&&!rd_pending,"canceled_read_all_eight_physical_beats_drained");
  end
  before_writes=writes;before_commands=integer'(writer_commands);wr_issue(256,64'h0a0b0c0d0e0f0102);
  while(integer'(writer_commands)-before_commands<2)step();wr_reset=1;wr_finish(1);wr_reset=0;quiet();
  check(writes-before_writes==2,"warm_writer_reset_prefix_drain");
  before_reads=readwords;rd_issue(0);while(rd_beats<3)step();rd_reset=1;rd_finish(1);rd_reset=0;quiet();
  check(readwords-before_reads==8,"warm_reader_reset_complete_drain");
  // Post-reset read/write turnarounds and periodic refresh remain operational.
  wr_issue(512,64'hfeedfacec001d00d,2);wr_finish();quiet();
  rd_issue(0,2);rd_finish();quiet();step(200);quiet();
  check(refreshes>3&&activates>3&&precharges>3,"periodic_refresh_and_read_write_turnarounds");
  $display("{\"type\":\"verdict\",\"status\":\"TEST_PASS\",\"checks\":%0d,\"t_ac_ns\":%0f,\"observation_checksum\":%0d}",checks,T_AC_NS,^{wr_req_ready,wr_rsp_valid,wr_rsp_error,wr_rsp_epoch,wr_rsp_token,wr_rsp_bank,wr_rsp_addr,wr_busy,wr_pending,wr_state,wr_word_index,wr_rows,wr_words_accepted,wr_words_retired,wr_responses,wr_cancels,wr_invalid,rd_req_ready,rd_rsp_valid,rd_rsp_error,rd_rsp_data,rd_rsp_epoch,rd_rsp_generation,rd_rsp_bank,rd_rsp_addr,rd_busy,rd_pending,rd_state,rd_beats,rd_requests,rd_commands,rd_count_beats,rd_responses,rd_cancels,rd_invalid,source_owner,writer_grants,reader_grants,writer_commands,reader_commands,owner_releases,controller_valid,controller_write,controller_addr,controller_data,controller_ready,controller_idle,controller_read_valid,controller_read_data,peek_data,writes,readwords,refreshes,mrs,activates,precharges});
  $finish;
 end
 initial begin #2000000;$fatal(1,"finite shared-service watchdog");end
endmodule
`default_nettype wire
