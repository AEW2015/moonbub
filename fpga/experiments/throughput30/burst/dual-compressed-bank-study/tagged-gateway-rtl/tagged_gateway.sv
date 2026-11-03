`timescale 1ns/1ps
`default_nettype none
// Research-only synchronous command gateway. See README for assumptions.
module tagged_gateway #(parameter integer CAP_BYTES=49152)(
 input wire clk,reset,input wire [31:0] epoch_in,
 input wire req_valid,output wire req_ready,input wire [31:0] req_seq,
 input wire [1:0] req_op,input wire [31:0] req_epoch,input wire req_bank,
 input wire [31:0] req_generation,req_frame_id,input wire [15:0] req_length,
 input wire [31:0] req_crc,input wire [15:0] req_offset,input wire [7:0] req_data,
 output reg ack_valid,input wire ack_ready,output reg [31:0] ack_seq,
 output reg [3:0] ack_status,ack_detail,output reg [31:0] ack_epoch,
 output reg ack_bank,output reg [31:0] ack_generation,output reg [15:0] ack_count,
 output wire mem_we,mem_bank,output wire [15:0] mem_addr,output wire [7:0] mem_data,
 input wire decode_request,decode_done,decode_fail,vblank,
 output wire decode_grant,decode_bank,output wire [31:0] decode_id,
 output wire present,front_valid,output wire [31:0] front_id,
 output wire [31:0] accepted_frames,dropped_frames
);
 localparam [1:0] OP_BEGIN=0,OP_DATA=1,OP_COMMIT=2,OP_ABORT=3;
 localparam [3:0] OK=0,OUT_OF_ORDER=1,ID_CONFLICT=2,STALE_EPOCH=3,
                    STALE_TOKEN=4,BAD_OFFSET=5,CONTROL_REJECT=6,EXHAUSTED=7,INTERNAL=8;
 localparam [1:0] IDLE=0,CLASSIFY=1,FIRE=2,WAIT_RESULT=3;
 reg [1:0] state;
 wire [170:0] req_body={req_op,req_epoch,req_bank,req_generation,req_frame_id,
                         req_length,req_crc,req_offset,req_data};
 reg [170:0] pending_body,cache_body;
 reg [31:0] pending_seq,cache_seq,next_seq,epoch,generation;
 reg cache_valid,seq_exhausted,active,active_bank,faulted;
 reg [31:0] active_generation;reg [15:0] active_count;
 wire [1:0] p_op;wire [31:0] p_epoch,p_generation,p_frame_id,p_crc;
 wire p_bank;wire [15:0] p_length,p_offset;wire [7:0] p_data;
 assign {p_op,p_epoch,p_bank,p_generation,p_frame_id,p_length,p_crc,p_offset,p_data}=pending_body;
 reg [3:0] cache_status,cache_detail;reg [31:0] cache_epoch,cache_generation;
 reg cache_bank;reg [15:0] cache_count;
 reg c_begin,c_data,c_commit,c_abort;
 wire c_begin_accept,c_begin_bank,c_commit_accept,c_abort_accept,c_reject;wire [3:0] c_reason;
 assign req_ready=(state==IDLE && !ack_valid && !reset);
 two_bank_control_gateway #(.CAP_BYTES(CAP_BYTES)) control(
  .clk(clk),.reset(reset),.begin_valid(c_begin),.begin_id(p_frame_id),.begin_length(p_length),.begin_crc(p_crc),
  .byte_valid(c_data),.byte_data(p_data),.commit_valid(c_commit),.abort_valid(c_abort),.ingress_overflow(1'b0),
  .begin_accept(c_begin_accept),.begin_accept_bank(c_begin_bank),.commit_accept(c_commit_accept),.abort_accept(c_abort_accept),.reject(c_reject),.reject_reason(c_reason),
  .mem_we(mem_we),.mem_bank(mem_bank),.mem_addr(mem_addr),.mem_data(mem_data),
  .decode_request(decode_request),.decode_done(decode_done),.decode_fail(decode_fail),
  .decode_grant(decode_grant),.decode_bank(decode_bank),.decode_id(decode_id),.vblank(vblank),
  .present(present),.front_valid(front_valid),.front_id(front_id),.accepted_frames(accepted_frames),.dropped_frames(dropped_frames));

 // A completed new request consumes its sequence even on a negative response.
 // Retrying the latest exact body returns this historical ACK without side effects.
 task automatic finish_new(input [3:0] status,input [3:0] detail,
                           input bank,input [31:0] gen,input [15:0] count);
 begin
  ack_valid<=1;ack_seq<=pending_seq;ack_status<=status;ack_detail<=detail;
  ack_epoch<=epoch;ack_bank<=bank;ack_generation<=gen;ack_count<=count;
  cache_valid<=1;cache_seq<=pending_seq;cache_body<=pending_body;
  cache_status<=status;cache_detail<=detail;cache_epoch<=epoch;
  cache_bank<=bank;cache_generation<=gen;cache_count<=count;
  if(next_seq==32'hffffffff)seq_exhausted<=1;else next_seq<=next_seq+1'b1;
  state<=IDLE;
 end endtask
 task automatic reply_uncached(input [3:0] status);
 begin
  ack_valid<=1;ack_seq<=pending_seq;ack_status<=status;ack_detail<=0;
  ack_epoch<=epoch;ack_bank<=0;ack_generation<=0;ack_count<=0;state<=IDLE;
 end endtask

 always @(posedge clk) begin
  if(reset)begin
   state<=IDLE;epoch<=epoch_in;next_seq<=1;seq_exhausted<=0;generation<=0;
   active<=0;active_bank<=0;active_generation<=0;active_count<=0;faulted<=0;
   pending_body<=0;pending_seq<=0;cache_body<=0;cache_seq<=0;cache_valid<=0;
   cache_status<=0;cache_detail<=0;cache_epoch<=0;cache_bank<=0;cache_generation<=0;cache_count<=0;
   ack_valid<=0;ack_seq<=0;ack_status<=0;ack_detail<=0;ack_epoch<=0;ack_bank<=0;ack_generation<=0;ack_count<=0;
   c_begin<=0;c_data<=0;c_commit<=0;c_abort<=0;
  end else begin
   if(ack_valid && ack_ready)ack_valid<=0;
   case(state)
    IDLE:if(req_valid && req_ready)begin pending_body<=req_body;pending_seq<=req_seq;state<=CLASSIFY;end
    CLASSIFY:begin
     if(cache_valid && pending_seq==cache_seq)begin
      if(pending_body==cache_body)begin
       ack_valid<=1;ack_seq<=cache_seq;ack_status<=cache_status;ack_detail<=cache_detail;
       ack_epoch<=cache_epoch;ack_bank<=cache_bank;ack_generation<=cache_generation;ack_count<=cache_count;state<=IDLE;
      end else reply_uncached(ID_CONFLICT);
     end else if(seq_exhausted || pending_seq!=next_seq)reply_uncached(OUT_OF_ORDER);
     else if(p_epoch!=epoch)finish_new(STALE_EPOCH,0,0,0,0);
     else if(faulted)finish_new(INTERNAL,0,0,0,0);
     else if(p_op==OP_BEGIN)begin
      if(generation==32'hffffffff)finish_new(EXHAUSTED,0,0,0,0);
      else if(active)finish_new(CONTROL_REJECT,4'd2,active_bank,active_generation,active_count);
      else begin c_begin<=1;state<=FIRE;end
     end else if(!active || p_bank!=active_bank || p_generation!=active_generation)
      finish_new(STALE_TOKEN,0,p_bank,p_generation,0);
     else if(p_op==OP_DATA && p_offset!=active_count)
      finish_new(BAD_OFFSET,0,active_bank,active_generation,active_count);
     else begin
      case(p_op) OP_DATA:c_data<=1;OP_COMMIT:c_commit<=1;OP_ABORT:c_abort<=1;default:;endcase
      state<=FIRE;
     end
    end
    FIRE:begin c_begin<=0;c_data<=0;c_commit<=0;c_abort<=0;state<=WAIT_RESULT;end
    WAIT_RESULT:begin
     case(p_op)
      OP_BEGIN:if(c_begin_accept && !c_reject)begin
       generation<=generation+1'b1;active<=1;active_bank<=c_begin_bank;
       active_generation<=generation+1'b1;active_count<=0;
       finish_new(OK,0,c_begin_bank,generation+1'b1,0);
      end else if(c_reject)finish_new(CONTROL_REJECT,c_reason,0,0,0);
      else begin faulted<=1;finish_new(INTERNAL,0,0,0,0);end
      OP_DATA:if(mem_we && !c_reject && mem_bank==active_bank && mem_addr==active_count && mem_data==p_data)begin
       active_count<=active_count+1'b1;finish_new(OK,0,active_bank,active_generation,active_count+1'b1);
      end else if(c_reject)begin active<=0;finish_new(CONTROL_REJECT,c_reason,active_bank,active_generation,active_count);end
      else begin active<=0;faulted<=1;finish_new(INTERNAL,0,active_bank,active_generation,active_count);end
      OP_COMMIT:begin active<=0;if(c_reject)finish_new(CONTROL_REJECT,c_reason,active_bank,active_generation,active_count);
       else if(c_commit_accept)finish_new(OK,0,active_bank,active_generation,active_count);
       else begin faulted<=1;finish_new(INTERNAL,0,active_bank,active_generation,active_count);end end
      OP_ABORT:begin active<=0;if(c_abort_accept && !c_reject)finish_new(OK,0,active_bank,active_generation,active_count);
       else begin faulted<=1;finish_new(INTERNAL,0,active_bank,active_generation,active_count);end end
     endcase
    end
   endcase
  end
 end
endmodule
`default_nettype wire
