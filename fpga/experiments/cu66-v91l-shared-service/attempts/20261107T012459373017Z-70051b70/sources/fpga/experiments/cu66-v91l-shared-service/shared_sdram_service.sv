`timescale 1ns/1ps
`default_nettype none
// Transaction ownership includes bridge drain and any held logical response.
module shared_sdram_service(
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
 input logic  controller_ready,
 input logic  controller_idle,
 input logic  controller_read_valid,
 input logic [15:0] controller_read_data);
 localparam logic [1:0] OWNER_NONE=0,OWNER_WRITER=1,OWNER_READER=2;
 logic last_reader,accepted,initialized=0;
 wire wr_owned=source_owner==OWNER_WRITER;
 wire rd_owned=source_owner==OWNER_READER;
 wire wr_valid,rd_valid,wr_ready,rd_ready,wr_drained;
 wire wr_ctrl_valid,rd_ctrl_valid,wr_ctrl_write,rd_ctrl_write;
 wire [23:0] wr_ctrl_addr,rd_ctrl_addr;
 wire [15:0] wr_ctrl_data,rd_ctrl_data;
 assign wr_valid=wr_req_valid&&wr_owned&&!accepted;
 assign rd_valid=rd_req_valid&&rd_owned&&!accepted;
 assign wr_req_ready=wr_ready&&wr_owned&&!accepted;
 assign rd_req_ready=rd_ready&&rd_owned&&!accepted;
 assign controller_valid=(wr_owned&&wr_ctrl_valid)||(rd_owned&&rd_ctrl_valid);
 assign controller_write=wr_owned&&wr_ctrl_write;
 assign controller_addr=wr_owned?wr_ctrl_addr:rd_ctrl_addr;
 assign controller_data=wr_owned?wr_ctrl_data:rd_ctrl_data;
 always_ff @(posedge clk)begin
  initialized<=1;
  if(power_on_reset)begin
   source_owner<=OWNER_NONE;last_reader<=1;accepted<=0;
   writer_grants<=0;reader_grants<=0;writer_commands<=0;reader_commands<=0;owner_releases<=0;
  end else begin
   if(controller_valid&&controller_ready)begin
    if(wr_owned)writer_commands<=writer_commands+1;
    if(rd_owned)reader_commands<=reader_commands+1;
   end
   if(source_owner==OWNER_NONE)begin
    accepted<=0;
    if(wr_req_valid&&!wr_reset&&!wr_cancel&&(!rd_req_valid||rd_reset||rd_cancel||last_reader))begin
     source_owner<=OWNER_WRITER;writer_grants<=writer_grants+1;last_reader<=0;
    end else if(rd_req_valid&&!rd_reset&&!rd_cancel)begin
     source_owner<=OWNER_READER;reader_grants<=reader_grants+1;last_reader<=1;
    end
   end else begin
    if((wr_owned&&wr_req_valid&&wr_req_ready)||(rd_owned&&rd_req_valid&&rd_req_ready))accepted<=1;
    if((accepted&&((wr_owned&&!wr_busy)||(rd_owned&&!rd_busy)))||
       (!accepted&&((wr_owned&&(wr_reset||wr_cancel||!wr_req_valid))||(rd_owned&&(rd_reset||rd_cancel||!rd_req_valid)))))begin
     source_owner<=OWNER_NONE;accepted<=0;owner_releases<=owner_releases+1;
    end
   end
  end
 end
 row_to_sdram writer(
  .clk(clk),
  .power_on_reset(power_on_reset),
  .reset(wr_reset),
  .cancel(wr_cancel),
  .req_valid(wr_valid),
  .req_ready(wr_ready),
  .rsp_ready(wr_rsp_ready),
  .rsp_valid(wr_rsp_valid),
  .rsp_error(wr_rsp_error),
  .req_epoch(wr_req_epoch),
  .req_token(wr_req_token),
  .req_bank(wr_req_bank),
  .req_addr(wr_req_addr),
  .req_data(wr_req_data),
  .rsp_epoch(wr_rsp_epoch),
  .rsp_token(wr_rsp_token),
  .rsp_bank(wr_rsp_bank),
  .rsp_addr(wr_rsp_addr),
  .ctrl_valid(wr_ctrl_valid),
  .ctrl_ready(controller_ready&&wr_owned),
  .ctrl_idle(controller_idle),
  .ctrl_write(wr_ctrl_write),
  .ctrl_addr(wr_ctrl_addr),
  .ctrl_data(wr_ctrl_data),
  .busy(wr_busy),
  .state(wr_state),
  .word_pending(wr_pending),
  .drained(wr_drained),
  .word_index(wr_word_index),
  .count_rows(wr_rows),
  .count_words_accepted(wr_words_accepted),
  .count_words_retired(wr_words_retired),
  .count_responses(wr_responses),
  .count_cancels(wr_cancels),
  .count_invalid(wr_invalid));
 bl8_read_bridge reader(
  .clk(clk),
  .power_on_reset(power_on_reset),
  .reset(rd_reset),
  .cancel(rd_cancel),
  .req_valid(rd_valid),
  .req_ready(rd_ready),
  .rsp_ready(rd_rsp_ready),
  .rsp_valid(rd_rsp_valid),
  .rsp_error(rd_rsp_error),
  .req_epoch(rd_req_epoch),
  .req_generation(rd_req_generation),
  .req_bank(rd_req_bank),
  .req_addr(rd_req_addr),
  .rsp_data(rd_rsp_data),
  .rsp_epoch(rd_rsp_epoch),
  .rsp_generation(rd_rsp_generation),
  .rsp_bank(rd_rsp_bank),
  .rsp_addr(rd_rsp_addr),
  .ctrl_valid(rd_ctrl_valid),
  .ctrl_ready(controller_ready&&rd_owned),
  .ctrl_idle(controller_idle),
  .ctrl_write(rd_ctrl_write),
  .ctrl_addr(rd_ctrl_addr),
  .ctrl_data(rd_ctrl_data),
  .busy(rd_busy),
  .state(rd_state),
  .pending(rd_pending),
  .beat_count(rd_beats),
  .count_requests(rd_requests),
  .count_commands(rd_commands),
  .count_beats(rd_count_beats),
  .ctrl_read_valid(controller_read_valid&&rd_owned),
  .ctrl_read_data(controller_read_data),
  .count_responses(rd_responses),
  .count_cancels(rd_cancels),
  .count_invalid(rd_invalid));
 always_ff @(posedge clk)begin
  if(power_on_reset&&initialized)assert(source_owner==OWNER_NONE&&!wr_busy&&!rd_busy)else $fatal(1,"cold reset requires quiescent service");
  if(!power_on_reset)begin
   assert(source_owner<=OWNER_READER);
   assert(!(wr_busy&&rd_busy));
   if(wr_busy)assert(wr_owned);
   if(rd_busy)assert(rd_owned);
   if(controller_valid)assert((wr_owned&&controller_write)||(rd_owned&&!controller_write));
   if(controller_read_valid)assert(rd_owned&&rd_pending)else $fatal(1,"unowned physical read beat");
   if(wr_rsp_valid)assert(wr_owned&&wr_drained==0&&!wr_pending);
   if(rd_rsp_valid)assert(rd_owned&&!rd_pending);
   assert(rd_ctrl_write==0&&rd_ctrl_data==0);
  end
 end
endmodule
`default_nettype wire
