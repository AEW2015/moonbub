`timescale 1ns/1ps
`default_nettype none
// Simulation wrapper: unchanged controller and timed functional SDRAM pin model.
module shared_sdram_timed #(parameter real T_AC_NS=2.0,parameter integer POWERUP_CYCLES=30,REFRESH_CYCLES=750)(
 input logic  clk,
 input logic  power_on_reset,
 input logic  wr_reset,
 input logic  wr_cancel,
 input logic  wr_req_valid,
 input logic  wr_rsp_ready,
 output logic  wr_req_ready,
 output logic  wr_rsp_valid,
 output logic  wr_rsp_error,
 input logic [31:0] wr_req_epoch,
 input logic [31:0] wr_req_token,
 input logic [1:0] wr_req_bank,
 input logic [19:0] wr_req_addr,
 input logic [63:0] wr_req_data,
 output logic [31:0] wr_rsp_epoch,
 output logic [31:0] wr_rsp_token,
 output logic [1:0] wr_rsp_bank,
 output logic [19:0] wr_rsp_addr,
 output logic  wr_busy,
 output logic  wr_pending,
 output logic [2:0] wr_state,
 output logic [2:0] wr_word_index,
 output logic [31:0] wr_rows,
 output logic [31:0] wr_words_accepted,
 output logic [31:0] wr_words_retired,
 output logic [31:0] wr_responses,
 output logic [31:0] wr_cancels,
 output logic [31:0] wr_invalid,
 input logic  rd_reset,
 input logic  rd_cancel,
 input logic  rd_req_valid,
 input logic  rd_rsp_ready,
 output logic  rd_req_ready,
 output logic  rd_rsp_valid,
 output logic  rd_rsp_error,
 input logic [31:0] rd_req_epoch,
 input logic [31:0] rd_req_generation,
 input logic [1:0] rd_req_bank,
 input logic [18:0] rd_req_addr,
 output logic [127:0] rd_rsp_data,
 output logic [31:0] rd_rsp_epoch,
 output logic [31:0] rd_rsp_generation,
 output logic [1:0] rd_rsp_bank,
 output logic [18:0] rd_rsp_addr,
 output logic  rd_busy,
 output logic  rd_pending,
 output logic [2:0] rd_state,
 output logic [3:0] rd_beats,
 output logic [31:0] rd_requests,
 output logic [31:0] rd_commands,
 output logic [31:0] rd_count_beats,
 output logic [31:0] rd_responses,
 output logic [31:0] rd_cancels,
 output logic [31:0] rd_invalid,
 output logic [1:0] source_owner,
 output logic [31:0] writer_grants,
 output logic [31:0] reader_grants,
 output logic [31:0] writer_commands,
 output logic [31:0] reader_commands,
 output logic [31:0] owner_releases,
 output logic  controller_valid,
 output logic  controller_write,
 output logic [23:0] controller_addr,
 output logic [15:0] controller_data,
 output logic  controller_ready,
 output logic  controller_idle,
 output logic  controller_read_valid,
 output logic [15:0] controller_read_data,
 input logic [23:0] peek_addr,
 output logic [15:0] peek_data,
 output integer writes,
 output integer readwords,
 output integer refreshes,
 output integer mrs,
 output integer activates,
 output integer precharges);
 wire read_clk;assign #2.75 read_clk=~clk;
 wire [12:0] a;wire [1:0]ba,cke,cs;wire [15:0]dq;
 wire sclk,ras,cas,we,ldqm,udqm;
 shared_sdram_service service(
  .clk(clk),
  .power_on_reset(power_on_reset),
  .wr_reset(wr_reset),
  .wr_cancel(wr_cancel),
  .wr_req_valid(wr_req_valid),
  .wr_rsp_ready(wr_rsp_ready),
  .wr_req_ready(wr_req_ready),
  .wr_rsp_valid(wr_rsp_valid),
  .wr_rsp_error(wr_rsp_error),
  .wr_req_epoch(wr_req_epoch),
  .wr_req_token(wr_req_token),
  .wr_req_bank(wr_req_bank),
  .wr_req_addr(wr_req_addr),
  .wr_req_data(wr_req_data),
  .wr_rsp_epoch(wr_rsp_epoch),
  .wr_rsp_token(wr_rsp_token),
  .wr_rsp_bank(wr_rsp_bank),
  .wr_rsp_addr(wr_rsp_addr),
  .wr_busy(wr_busy),
  .wr_pending(wr_pending),
  .wr_state(wr_state),
  .wr_word_index(wr_word_index),
  .wr_rows(wr_rows),
  .wr_words_accepted(wr_words_accepted),
  .wr_words_retired(wr_words_retired),
  .wr_responses(wr_responses),
  .wr_cancels(wr_cancels),
  .wr_invalid(wr_invalid),
  .rd_reset(rd_reset),
  .rd_cancel(rd_cancel),
  .rd_req_valid(rd_req_valid),
  .rd_rsp_ready(rd_rsp_ready),
  .rd_req_ready(rd_req_ready),
  .rd_rsp_valid(rd_rsp_valid),
  .rd_rsp_error(rd_rsp_error),
  .rd_req_epoch(rd_req_epoch),
  .rd_req_generation(rd_req_generation),
  .rd_req_bank(rd_req_bank),
  .rd_req_addr(rd_req_addr),
  .rd_rsp_data(rd_rsp_data),
  .rd_rsp_epoch(rd_rsp_epoch),
  .rd_rsp_generation(rd_rsp_generation),
  .rd_rsp_bank(rd_rsp_bank),
  .rd_rsp_addr(rd_rsp_addr),
  .rd_busy(rd_busy),
  .rd_pending(rd_pending),
  .rd_state(rd_state),
  .rd_beats(rd_beats),
  .rd_requests(rd_requests),
  .rd_commands(rd_commands),
  .rd_count_beats(rd_count_beats),
  .rd_responses(rd_responses),
  .rd_cancels(rd_cancels),
  .rd_invalid(rd_invalid),
  .source_owner(source_owner),
  .writer_grants(writer_grants),
  .reader_grants(reader_grants),
  .writer_commands(writer_commands),
  .reader_commands(reader_commands),
  .owner_releases(owner_releases),
  .controller_valid(controller_valid),
  .controller_write(controller_write),
  .controller_addr(controller_addr),
  .controller_data(controller_data),
  .controller_ready(controller_ready),
  .controller_idle(controller_idle),
  .controller_read_valid(controller_read_valid),
  .controller_read_data(controller_read_data));
 moonshine_sdram #(.POWERUP_CYCLES(POWERUP_CYCLES),.REFRESH_CYCLES(REFRESH_CYCLES)) controller(
 .clk(clk),.read_clk(read_clk),.reset(power_on_reset),.request_valid(controller_valid),.request_ready(controller_ready),
 .request_write(controller_write),.request_address(controller_addr),.request_data(controller_data),
 .response_valid(controller_read_valid),.response_data(controller_read_data),.idle(controller_idle),
 .sdram_a(a),.sdram_bs(ba),.sdram_dq(dq),.sdram_clk(sclk),.sdram_cke(cke),.sdram_cs_n(cs),
 .sdram_ras_n(ras),.sdram_cas_n(cas),.sdram_we_n(we),.sdram_ldqm(ldqm),.sdram_udqm(udqm));
 sdram_pin_model #(.T_AC_NS(T_AC_NS),.CLOCK_FLIGHT_NS(4.0)) memory(
 .clk(sclk),.a(a),.ba(ba),.cke(cke),.cs(cs),.ras(ras),.cas(cas),.we(we),.ldqm(ldqm),.udqm(udqm),.dq(dq),
 .peek_addr(peek_addr),.peek_data(peek_data),.writes(writes),.readwords(readwords),.refreshes(refreshes),.mrs(mrs),.activates(activates),.precharges(precharges));

 integer receipt_cycle=0;
 logic [1:0] receipt_owner=0;
 logic wr_offered=0,rd_offered=0;
 logic [2:0] receipt_wr_state=0,receipt_rd_state=0;
 logic receipt_idle=0;
 always @(posedge clk)begin
  receipt_cycle<=receipt_cycle+1;
  if(!power_on_reset)begin
   if(wr_reset||wr_cancel||rd_reset||rd_cancel)$display("{\"type\":\"kill\",\"cycle\":%0d,\"time_ps\":%0d,\"owner\":%0d,\"wr_reset\":%0d,\"wr_cancel\":%0d,\"rd_reset\":%0d,\"rd_cancel\":%0d}",receipt_cycle+1,longint'($realtime*1000.0),source_owner,wr_reset,wr_cancel,rd_reset,rd_cancel);
   if(source_owner==0&&(wr_req_valid||rd_req_valid))$display("{\"type\":\"arbitrate\",\"cycle\":%0d,\"time_ps\":%0d,\"wr_offer\":%0d,\"rd_offer\":%0d}",receipt_cycle+1,longint'($realtime*1000.0),wr_req_valid&&!wr_reset&&!wr_cancel,rd_req_valid&&!rd_reset&&!rd_cancel);
   if(source_owner!=receipt_owner)$display("{\"type\":\"ownership\",\"cycle\":%0d,\"time_ps\":%0d,\"old_owner\":%0d,\"owner\":%0d}",receipt_cycle+1,longint'($realtime*1000.0),receipt_owner,source_owner);
   if(wr_req_valid&&wr_req_ready)$display("{\"type\":\"wr_req\",\"cycle\":%0d,\"time_ps\":%0d,\"owner\":%0d,\"epoch\":%0d,\"token\":%0d,\"bank\":%0d,\"address\":%0d,\"data\":\"%016h\"}",receipt_cycle+1,longint'($realtime*1000.0),source_owner,wr_req_epoch,wr_req_token,wr_req_bank,wr_req_addr,wr_req_data);
   if(rd_req_valid&&rd_req_ready)$display("{\"type\":\"rd_req\",\"cycle\":%0d,\"time_ps\":%0d,\"owner\":%0d,\"epoch\":%0d,\"generation\":%0d,\"bank\":%0d,\"address\":%0d}",receipt_cycle+1,longint'($realtime*1000.0),source_owner,rd_req_epoch,rd_req_generation,rd_req_bank,rd_req_addr);
   if(controller_valid&&controller_ready)$display("{\"type\":\"ctrl_req\",\"cycle\":%0d,\"time_ps\":%0d,\"owner\":%0d,\"write\":%0d,\"address\":%0d,\"data\":%0d}",receipt_cycle+1,longint'($realtime*1000.0),source_owner,controller_write,controller_addr,controller_data);
   if(controller_read_valid)$display("{\"type\":\"controller_read\",\"cycle\":%0d,\"time_ps\":%0d,\"owner\":%0d,\"data\":%0d}",receipt_cycle+1,longint'($realtime*1000.0),source_owner,controller_read_data);
   if(wr_rsp_valid&&!wr_offered)$display("{\"type\":\"%s\",\"cycle\":%0d,\"time_ps\":%0d,\"owner\":%0d,\"epoch\":%0d,\"token\":%0d,\"bank\":%0d,\"address\":%0d,\"error\":%0d}","wr_rsp_offer",receipt_cycle+1,longint'($realtime*1000.0),source_owner,wr_rsp_epoch,wr_rsp_token,wr_rsp_bank,wr_rsp_addr,wr_rsp_error);
   if(wr_rsp_valid&&wr_rsp_ready)$display("{\"type\":\"%s\",\"cycle\":%0d,\"time_ps\":%0d,\"owner\":%0d,\"epoch\":%0d,\"token\":%0d,\"bank\":%0d,\"address\":%0d,\"error\":%0d}","wr_rsp",receipt_cycle+1,longint'($realtime*1000.0),source_owner,wr_rsp_epoch,wr_rsp_token,wr_rsp_bank,wr_rsp_addr,wr_rsp_error);
   if(rd_rsp_valid&&!rd_offered)$display("{\"type\":\"%s\",\"cycle\":%0d,\"time_ps\":%0d,\"owner\":%0d,\"epoch\":%0d,\"generation\":%0d,\"bank\":%0d,\"address\":%0d,\"error\":%0d,\"data\":\"%032h\"}","rd_rsp_offer",receipt_cycle+1,longint'($realtime*1000.0),source_owner,rd_rsp_epoch,rd_rsp_generation,rd_rsp_bank,rd_rsp_addr,rd_rsp_error,rd_rsp_data);
   if(rd_rsp_valid&&rd_rsp_ready)$display("{\"type\":\"%s\",\"cycle\":%0d,\"time_ps\":%0d,\"owner\":%0d,\"epoch\":%0d,\"generation\":%0d,\"bank\":%0d,\"address\":%0d,\"error\":%0d,\"data\":\"%032h\"}","rd_rsp",receipt_cycle+1,longint'($realtime*1000.0),source_owner,rd_rsp_epoch,rd_rsp_generation,rd_rsp_bank,rd_rsp_addr,rd_rsp_error,rd_rsp_data);
   if(source_owner!=0&&(wr_state!=receipt_wr_state||rd_state!=receipt_rd_state||controller_idle!=receipt_idle||wr_state==2||wr_state==3||rd_state==3))$display("{\"type\":\"fence\",\"cycle\":%0d,\"time_ps\":%0d,\"owner\":%0d,\"wr_state\":%0d,\"rd_state\":%0d,\"wr_pending\":%0d,\"rd_pending\":%0d,\"controller_idle\":%0d,\"wr_words_accepted\":%0d,\"wr_words_retired\":%0d,\"rd_beats\":%0d}",receipt_cycle+1,longint'($realtime*1000.0),source_owner,wr_state,rd_state,wr_pending,rd_pending,controller_idle,wr_words_accepted,wr_words_retired,rd_beats);
  end
  receipt_owner<=source_owner;receipt_wr_state<=wr_state;receipt_rd_state<=rd_state;receipt_idle<=controller_idle;
  wr_offered<=wr_rsp_valid&&!wr_rsp_ready;rd_offered<=rd_rsp_valid&&!rd_rsp_ready;
 end
endmodule
`default_nettype wire
