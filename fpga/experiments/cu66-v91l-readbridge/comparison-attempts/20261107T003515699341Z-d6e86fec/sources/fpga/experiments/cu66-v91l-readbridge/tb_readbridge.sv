`timescale 1ns/1ps
`default_nettype none
module tb_readbridge #(parameter real T_AC_NS=2.0,parameter integer RETAIN=1);
 logic clk=0;initial forever #5 clk=!clk;
 wire read_clk;assign #2.75 read_clk=~clk;
 logic power_on_reset=1,reset=0,cancel=0,hold_command=0;
 logic direct_valid=0,direct_ready=0,native_mode=0,raw_mode=0,raw_valid=0,raw_write=0;
 logic[18:0] direct_addr=0;logic[1:0]direct_bank=0;logic[31:0]direct_epoch=1,direct_generation=1;
 wire req_valid,req_ready,rsp_valid,rsp_ready,rsp_error;wire[18:0]req_addr,rsp_addr;wire[1:0]req_bank,rsp_bank;wire[31:0]req_epoch,req_generation,rsp_epoch,rsp_generation;wire[127:0]rsp_data;
 wire b_valid,b_ready,b_write,c_ready,c_idle,c_read_valid;wire[23:0]b_addr;wire[15:0]b_data,c_read_data;
 wire bridge_busy,bridge_pending;wire[2:0]bridge_state;wire[3:0]bridge_beats;
 wire[31:0]bridge_requests,bridge_commands,bridge_count_beats,bridge_responses,bridge_cancels,bridge_invalid;
 logic[23:0]raw_addr=0;logic[15:0]raw_data=0;
 wire c_valid=raw_mode?raw_valid:(b_valid&&!hold_command);wire c_write=raw_mode?raw_write:b_write;
 wire[23:0]c_addr=raw_mode?raw_addr:b_addr;wire[15:0]c_data=raw_mode?raw_data:b_data;
 assign b_ready=!raw_mode&&!hold_command&&c_ready;
 wire[12:0]a;wire[1:0]ba,cke,cs;wire[15:0]dq;wire sclk,ras,cas,we,ldqm,udqm;
 logic[23:0]peek_addr=0;wire[15:0]peek_data;integer writes,readwords,refreshes,mrs,activates,precharges;
 logic r_start=0,r_finish=0,r_req_valid=0,r_rsp_ready=0;logic[1:0]r_bank=0;logic[31:0]r_epoch=100,r_generation=200,r_token=0;logic[18:0]r_req_addr=0;
 wire r_start_ready,r_active,r_busy,r_req_ready,r_rsp_valid,r_pending;wire[3:0]r_error,r_rsp_error;wire[2:0]r_state;wire[127:0]r_rsp_data;wire[18:0]r_rsp_addr;wire[1:0]r_rsp_bank;wire[31:0]r_rsp_epoch,r_rsp_generation,r_rsp_token;
 wire r_mem_valid,r_mem_ready;wire[18:0]r_mem_addr;wire[1:0]r_mem_bank;wire[31:0]r_mem_epoch,r_mem_generation;
 wire[31:0]r_requests,r_responses,r_errors,r_physical_requests,r_physical_responses,r_hits,r_scratch_hits;wire[7:0]r_fragments;
 integer cycle=0,checks=0,seed=0,raw_read_words=0;logic[31:0]prng=1;
 logic ctrl_owned=0,ctrl_saw_busy=0;integer ctrl_beats=0;logic[23:0]ctrl_owned_addr=0;logic ctrl_owned_write=0;logic[15:0]ctrl_owned_data=0;
 string preload_file,native_file;integer fd,scan;logic[159:0]native_line;
 assign req_valid=native_mode?r_mem_valid:direct_valid;assign req_addr=native_mode?r_mem_addr:direct_addr;assign req_bank=native_mode?r_mem_bank:direct_bank;assign req_epoch=native_mode?r_mem_epoch:direct_epoch;assign req_generation=native_mode?r_mem_generation:direct_generation;
 assign r_mem_ready=native_mode&&req_ready;assign rsp_ready=native_mode?r_mem_ready_response:direct_ready;
 wire r_mem_ready_response;
 bl8_read_bridge bridge(.clk(clk),.power_on_reset(power_on_reset),.reset(reset),.cancel(cancel),.req_valid(req_valid),.req_ready(req_ready),.req_addr(req_addr),.req_bank(req_bank),.req_epoch(req_epoch),.req_generation(req_generation),.rsp_valid(rsp_valid),.rsp_ready(rsp_ready),.rsp_data(rsp_data),.rsp_addr(rsp_addr),.rsp_bank(rsp_bank),.rsp_epoch(rsp_epoch),.rsp_generation(rsp_generation),.rsp_error(rsp_error),.ctrl_valid(b_valid),.ctrl_ready(b_ready),.ctrl_write(b_write),.ctrl_addr(b_addr),.ctrl_data(b_data),.ctrl_read_valid(c_read_valid&&!raw_mode),.ctrl_read_data(c_read_data),.ctrl_idle(c_idle),.busy(bridge_busy),.pending(bridge_pending),.state(bridge_state),.beat_count(bridge_beats),.count_requests(bridge_requests),.count_commands(bridge_commands),.count_beats(bridge_count_beats),.count_responses(bridge_responses),.count_cancels(bridge_cancels),.count_invalid(bridge_invalid));
 tile_rowpair_reader #(.RETAIN_ROWS(RETAIN!=0)) reader(.clk(clk),.power_on_reset(power_on_reset),.reset(reset),.cancel(cancel),.start(r_start),.start_ready(r_start_ready),.start_bank(r_bank),.start_epoch(r_epoch),.start_generation(r_generation),.finish(r_finish),.active(r_active),.busy(r_busy),.session_error(r_error),.req_valid(r_req_valid),.req_ready(r_req_ready),.req_addr(r_req_addr),.req_bank(r_bank),.req_epoch(r_epoch),.req_generation(r_generation),.req_token(r_token),.rsp_valid(r_rsp_valid),.rsp_ready(r_rsp_ready),.rsp_data(r_rsp_data),.rsp_addr(r_rsp_addr),.rsp_bank(r_rsp_bank),.rsp_epoch(r_rsp_epoch),.rsp_generation(r_rsp_generation),.rsp_token(r_rsp_token),.rsp_error(r_rsp_error),.mem_req_valid(r_mem_valid),.mem_req_ready(r_mem_ready),.mem_req_addr(r_mem_addr),.mem_req_bank(r_mem_bank),.mem_req_epoch(r_mem_epoch),.mem_req_generation(r_mem_generation),.mem_rsp_valid(rsp_valid&&native_mode),.mem_rsp_ready(r_mem_ready_response),.mem_rsp_data(rsp_data),.mem_rsp_addr(rsp_addr),.mem_rsp_bank(rsp_bank),.mem_rsp_epoch(rsp_epoch),.mem_rsp_generation(rsp_generation),.mem_rsp_error(rsp_error),.physical_pending(r_pending),.state(r_state),.count_requests(r_requests),.count_responses(r_responses),.count_errors(r_errors),.count_physical_requests(r_physical_requests),.count_physical_responses(r_physical_responses),.count_row_hits(r_hits),.count_scratch_hits(r_scratch_hits),.valid_fragments(r_fragments));
 moonshine_sdram #(.POWERUP_CYCLES(30),.REFRESH_CYCLES(750)) controller(.clk(clk),.read_clk(read_clk),.reset(power_on_reset),.request_valid(c_valid),.request_ready(c_ready),.request_write(c_write),.request_address(c_addr),.request_data(c_data),.response_valid(c_read_valid),.response_data(c_read_data),.idle(c_idle),.sdram_a(a),.sdram_bs(ba),.sdram_dq(dq),.sdram_clk(sclk),.sdram_cke(cke),.sdram_cs_n(cs),.sdram_ras_n(ras),.sdram_cas_n(cas),.sdram_we_n(we),.sdram_ldqm(ldqm),.sdram_udqm(udqm));
 sdram_pin_model #(.T_AC_NS(T_AC_NS)) memory(.clk(sclk),.a(a),.ba(ba),.cke(cke),.cs(cs),.ras(ras),.cas(cas),.we(we),.ldqm(ldqm),.udqm(udqm),.dq(dq),.peek_addr(peek_addr),.peek_data(peek_data),.*);
 function automatic logic[31:0]random32();prng=prng*32'd1664525+32'd1013904223;return prng;endfunction
 function automatic logic[127:0]initial_burst(input logic[1:0]bank,input logic[18:0]address);
  logic[127:0]value;logic[23:0]wordaddr;
  assert(address[3:0]==0)else $fatal(1,"initial burst alignment");
  for(integer j=0;j<8;j=j+1)begin wordaddr={bank,4'b0000,address[18:1]}+24'(j);assert(wordaddr[23:22]==bank&&wordaddr[21:0]<259200)else $fatal(1,"initial pattern aperture");value[j*16+:16]=wordaddr[15:0]^16'h5a3c;end
  return value;
 endfunction
 task automatic pass(input string name);checks=checks+1;$display("{\"type\":\"check\",\"name\":\"%s\",\"status\":\"PASS\"}",name);endtask
 initial forever begin
  @(posedge clk);cycle=cycle+1;if(cycle>30000000)$fatal(1,"clock watchdog");
  if(!power_on_reset)begin
   if(c_valid&&c_ready)begin
    assert(!ctrl_owned)else $fatal(1,"controller owner overlap");ctrl_owned=1;ctrl_saw_busy=0;ctrl_beats=0;ctrl_owned_addr=c_addr;ctrl_owned_write=c_write;ctrl_owned_data=c_data;
    $display("{\"type\":\"controller_req\",\"cycle\":%0d,\"time_ps\":%0d,\"write\":%0d,\"address\":%0d,\"data\":%0d}",cycle,longint'($realtime*1000.0),c_write,c_addr,c_data);
   end
   if(c_read_valid)begin ctrl_beats=ctrl_beats+1;$display("{\"type\":\"controller_read\",\"cycle\":%0d,\"time_ps\":%0d,\"data\":%0d}",cycle,longint'($realtime*1000.0),c_read_data);end
   if(ctrl_owned&&!c_idle)ctrl_saw_busy=1;
   if(ctrl_owned&&ctrl_saw_busy&&c_idle&&(ctrl_owned_write||ctrl_beats==8))begin
    $display("{\"type\":\"controller_done\",\"cycle\":%0d,\"time_ps\":%0d,\"write\":%0d,\"address\":%0d,\"data\":%0d}",cycle,longint'($realtime*1000.0),ctrl_owned_write,ctrl_owned_addr,ctrl_owned_data);ctrl_owned=0;
   end
   if(req_valid&&req_ready)$display("{\"type\":\"bridge_req\",\"cycle\":%0d,\"time_ps\":%0d,\"bank\":%0d,\"address\":%0d,\"epoch\":%0d,\"generation\":%0d}",cycle,longint'($realtime*1000.0),req_bank,req_addr,req_epoch,req_generation);
   if(rsp_valid)$display("{\"type\":\"bridge_offer\",\"cycle\":%0d,\"time_ps\":%0d,\"bank\":%0d,\"address\":%0d,\"epoch\":%0d,\"generation\":%0d,\"error\":%0d,\"ready\":%0d,\"data\":\"%032x\"}",cycle,longint'($realtime*1000.0),rsp_bank,rsp_addr,rsp_epoch,rsp_generation,rsp_error,rsp_ready,rsp_data);
   if(rsp_valid&&rsp_ready)$display("{\"type\":\"bridge_rsp\",\"cycle\":%0d,\"time_ps\":%0d,\"bank\":%0d,\"address\":%0d,\"epoch\":%0d,\"generation\":%0d,\"error\":%0d,\"data\":\"%032x\"}",cycle,longint'($realtime*1000.0),rsp_bank,rsp_addr,rsp_epoch,rsp_generation,rsp_error,rsp_data);
   if(reset||cancel)$display("{\"type\":\"kill\",\"cycle\":%0d,\"time_ps\":%0d,\"reset\":%0d,\"cancel\":%0d,\"pending\":%0d,\"state\":%0d,\"beats\":%0d}",cycle,longint'($realtime*1000.0),reset,cancel,bridge_pending,bridge_state,bridge_beats);
   if(native_mode&&r_req_valid&&r_req_ready)$display("{\"type\":\"reader_req\",\"cycle\":%0d,\"time_ps\":%0d,\"bank\":%0d,\"address\":%0d,\"epoch\":%0d,\"generation\":%0d,\"token\":%0d}",cycle,longint'($realtime*1000.0),r_bank,r_req_addr,r_epoch,r_generation,r_token);
   if(native_mode&&r_rsp_valid&&r_rsp_ready)$display("{\"type\":\"reader_rsp\",\"cycle\":%0d,\"time_ps\":%0d,\"bank\":%0d,\"address\":%0d,\"epoch\":%0d,\"generation\":%0d,\"token\":%0d,\"error\":%0d,\"data\":\"%032x\"}",cycle,longint'($realtime*1000.0),r_rsp_bank,r_rsp_addr,r_rsp_epoch,r_rsp_generation,r_rsp_token,r_rsp_error,r_rsp_data);
  end
 end
 task automatic offer(input logic[1:0]bank,input logic[18:0]address);
  @(negedge clk);direct_bank=bank;direct_addr=address;direct_epoch=direct_epoch+1;direct_generation=direct_generation+1;direct_valid=1;
  while(!req_ready)@(negedge clk);@(negedge clk);direct_valid=0;
 endtask
 task automatic response(input bit expected_error,input logic[127:0]expected);
  while(!rsp_valid)@(negedge clk);
  assert(rsp_bank==direct_bank&&rsp_addr==direct_addr&&rsp_epoch==direct_epoch&&rsp_generation==direct_generation&&rsp_error==expected_error&&!bridge_pending)else $fatal(1,"bridge response identity/error/drain");
  assert(rsp_data==(expected_error?128'd0:expected))else $fatal(1,"bridge exact data mismatch");
  direct_ready=1;@(negedge clk);direct_ready=0;
 endtask
 task automatic raw_word(input logic[1:0]bank,input logic[18:0]address,input logic[15:0]data);
  assert(address[0]==0)else $fatal(1,"raw word alignment");
  assert(!bridge_busy&&!ctrl_owned)else $fatal(1,"raw write overlaps bridge");raw_mode=1;@(negedge clk);raw_addr={bank,4'b0000,address[18:1]};raw_data=data;raw_write=1;raw_valid=1;
  while(!c_ready)@(negedge clk);@(negedge clk);raw_valid=0;
  while(!c_idle)@(negedge clk);@(negedge clk);raw_mode=0;
 endtask
 task automatic raw_fourth_bank();
  integer n;
  assert(!bridge_busy&&!ctrl_owned)else $fatal(1,"raw read overlaps bridge");
  raw_mode=1;@(negedge clk);raw_addr=24'hc00200;raw_data=0;raw_write=0;raw_valid=1;
  while(!c_ready)@(negedge clk);@(negedge clk);raw_valid=0;n=0;
  while(n<8)begin
   if(c_read_valid)begin assert(c_read_data==((16'h0200+16'(n))^16'h5a3c))else $fatal(1,"raw fourth bank mismatch");n=n+1;raw_read_words=raw_read_words+1;end
   @(negedge clk);
  end
  @(negedge clk);raw_mode=0;
 endtask
 task automatic kill_probe(input bit warm_reset,input integer target);
  integer beats_before;
  beats_before=int'(bridge_count_beats);hold_command=target<0;offer(0,4096);
  if(target>=0)begin while(!bridge_pending)@(negedge clk);while(int'(bridge_count_beats)-beats_before<target)@(negedge clk);end
  reset=warm_reset;cancel=!warm_reset;@(negedge clk);reset=0;cancel=0;hold_command=0;
  response(1,0);assert(!bridge_busy)else $fatal(1,"cancellation did not drain");
  pass($sformatf("%s_cancel_after_%0d_beats",warm_reset?"reset":"cancel",target));
 endtask
 initial begin
  if(!$value$plusargs("SEED=%d",seed))seed=912601;prng=32'(seed);
  $display("{\"type\":\"config\",\"seed\":%0d,\"retain\":%0d,\"t_ac_ns\":%0.3f,\"clock_flight_ns\":4.000,\"read_phase_ns\":7.750,\"bridge_idle_fence_cycles\":2}",seed,RETAIN,T_AC_NS);
  repeat(4)@(negedge clk);power_on_reset=0;while(!c_ready)@(negedge clk);
  for(integer b=0;b<3;b=b+1)begin offer(2'(b),19'd1024);response(0,initial_burst(2'(b),1024));end
  pass("three_allowed_banks_exact_bl8_gather");raw_fourth_bank();pass("reserved_fourth_bank_raw_controller_read_probe");
  for(integer j=0;j<8;j=j+1)raw_word(0,19'(2048+j*2),16'hbe00+16'(j));
  offer(0,2048);begin logic[127:0]e;for(integer j=0;j<8;j=j+1)e[j*16+:16]=16'hbe00+16'(j);response(0,e);end
  raw_word(0,2048,16'hcafe);peek_addr=24'd1024;#1;assert(peek_data==16'hcafe)else $fatal(1,"post-read write mismatch");pass("write_read_write_turnaround_no_pin_contention");
  for(integer n=0;n<8;n=n+1)begin logic[1:0]bank;logic[18:0]address;bank=2'(random32()%3);address=19'(8192+(random32()%31888)*16);offer(bank,address);response(0,initial_burst(bank,address));end
  pass("seeded_exact_read_bursts");
  for(integer r=0;r<2;r=r+1)begin kill_probe(1'(r),-1);kill_probe(1'(r),0);kill_probe(1'(r),3);kill_probe(1'(r),7);end
  for(integer bad=0;bad<5;bad=bad+1)begin
   integer commands;commands=int'(bridge_commands);
   @(negedge clk);direct_bank=bad==0?2'd3:2'd0;direct_addr=bad==1?19'd1:bad==2?19'd518400:19'd0;
   direct_epoch=bad==3?32'd0:32'd500;direct_generation=bad==4?32'd0:32'd600;direct_valid=1;
   while(!req_ready)@(negedge clk);@(negedge clk);direct_valid=0;response(1,0);
   assert(int'(bridge_commands)==commands)else $fatal(1,"invalid request emitted command");
  end
  direct_epoch=500;direct_generation=600;
  pass("invalid_range_bank_alignment_and_zero_ids_no_controller_request");
  offer(3,0);while(!rsp_valid)@(negedge clk);reset=1;
  repeat(5)begin @(negedge clk);assert(rsp_valid&&rsp_error&&rsp_data==0)else $fatal(1,"held error changed");end
  reset=0;response(1,0);pass("held_error_survives_reset_backpressure");
  offer(0,0);while(!rsp_valid)@(negedge clk);begin logic[127:0]saved;saved=rsp_data;cancel=1;repeat(5)begin @(negedge clk);assert(rsp_valid&&!rsp_error&&rsp_data==saved)else $fatal(1,"held success changed");end cancel=0;response(0,saved);end
  pass("held_success_survives_cancel_backpressure");
  repeat(1600)@(negedge clk);assert(refreshes>=4&&mrs==1)else $fatal(1,"refresh initialization missing");offer(2,518384);response(0,initial_burst(2,518384));pass("periodic_refresh_and_aperture_edge");
  if($value$plusargs("PRELOAD=%s",preload_file))begin
   assert($value$plusargs("NATIVE_LINES=%s",native_file))else $fatal(1,"native logical fixture missing");
   $display("{\"type\":\"preload\",\"cycle\":%0d,\"time_ps\":%0d,\"file\":\"%s\",\"scope\":\"direct_model_preload_outside_fences_not_physical_writes\"}",cycle,longint'($realtime*1000.0),preload_file);
   $readmemh(preload_file,memory.mem);native_mode=1;fd=$fopen(native_file,"r");assert(fd!=0)else $fatal(1,"native file open");
   for(integer frame=0;frame<2;frame=frame+1)begin
    assert(r_start_ready)else $fatal(1,"reader start before drain");r_bank=2'(frame);r_epoch=32'(1000+frame);r_generation=32'(2000+frame);r_start=1;@(negedge clk);r_start=0;
    $display("{\"type\":\"frame_begin\",\"cycle\":%0d,\"time_ps\":%0d,\"bank\":%0d}",cycle,longint'($realtime*1000.0),frame);
    for(integer n=0;n<32400;n=n+1)begin
     scan=$fscanf(fd,"%h\n",native_line);assert(scan==1&&native_line[159:149]==0&&native_line[148:147]==2'(frame))else $fatal(1,"native fixture row");
     r_req_addr=native_line[146:128];r_token=r_token+1;r_req_valid=1;while(!r_req_ready)@(negedge clk);@(negedge clk);r_req_valid=0;
     while(!r_rsp_valid)@(negedge clk);
     assert(r_rsp_data==native_line[127:0]&&r_rsp_error==0&&r_rsp_bank==r_bank&&r_rsp_epoch==r_epoch&&r_rsp_generation==r_generation&&r_rsp_addr==r_req_addr&&r_rsp_token==r_token)else $fatal(1,"native canonical exact mismatch");
     r_rsp_ready=1;@(negedge clk);r_rsp_ready=0;
    end
    $display("{\"type\":\"frame_end\",\"cycle\":%0d,\"time_ps\":%0d,\"bank\":%0d,\"reader_requests\":%0d,\"reader_responses\":%0d,\"physical_requests\":%0d,\"physical_responses\":%0d,\"row_hits\":%0d,\"scratch_hits\":%0d,\"valid_fragments\":%0d}",cycle,longint'($realtime*1000.0),frame,r_requests,r_responses,r_physical_requests,r_physical_responses,r_hits,r_scratch_hits,r_fragments);
    assert(!r_pending&&r_error==0&&r_errors==0&&r_active&&r_state==0)else $fatal(1,"native reader not drained");r_finish=1;@(negedge clk);r_finish=0;assert(!r_busy)else $fatal(1,"reader finish failed");
   end
   $fclose(fd);native_mode=0;pass("native_source_prefill_through_real_controller");
  end
  repeat(3)@(negedge clk);assert(!ctrl_owned&&!bridge_pending&&!bridge_busy&&bridge_count_beats==bridge_commands*8&&bridge_requests==bridge_responses&&readwords==int'(bridge_count_beats)+raw_read_words)else $fatal(1,"final read owner/count mismatch");
  $display("{\"type\":\"verdict\",\"status\":\"TEST_PASS\",\"seed\":%0d,\"retain\":%0d,\"t_ac_ns\":%0.3f,\"checks\":%0d,\"requests\":%0d,\"commands\":%0d,\"beats\":%0d,\"responses\":%0d,\"cancels\":%0d,\"invalid\":%0d,\"writes\":%0d,\"read_words\":%0d,\"refreshes\":%0d,\"activates\":%0d,\"precharges\":%0d,\"cycles\":%0d}",seed,RETAIN,T_AC_NS,checks,bridge_requests,bridge_commands,bridge_count_beats,bridge_responses,bridge_cancels,bridge_invalid,writes,readwords,refreshes,activates,precharges,cycle);
  $finish;
 end
 initial begin #300000000;$fatal(1,"time watchdog");end
endmodule
`default_nettype wire
