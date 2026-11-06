`timescale 1ns/1ps
`default_nettype none
// Private canonical-byte sink. Its in_ready is connected directly to the
// existing ar03_key_tagged sample_ready, which jointly advances raster and SHA.
// No reference publication, RGB, AF03, network admission or board memory map.
module ar03_yuv_store #(
 parameter integer TOTAL_BYTES=518400,
 parameter [23:0] APERTURE_BASE=24'h100000,
 parameter integer APERTURE_WORDS=262144
)(
 input wire clk,reset,
 input wire start_valid,output wire start_ready,
 input wire [63:0] start_owner,input wire [31:0] start_epoch,start_frame,
 input wire [23:0] start_base,
 input wire in_valid,output wire in_ready,input wire [7:0] in_byte,
 input wire [63:0] in_owner,input wire [31:0] in_epoch,in_frame,input wire in_last,
 input wire abort,input wire fault,input wire integrity_valid,input wire release_result,
 output wire pixel_valid,input wire pixel_ready,
 output wire [23:0] pixel_address,output wire [15:0] pixel_data,
 output wire force_flush,output wire discard,input wire memory_idle,
 output wire busy,output wire done,output wire failed,output wire aborted,
 output reg [63:0] owner,output reg [31:0] accepted_bytes,
 output reg [31:0] accepted_words,output reg [3:0] error_code,
 output reg [3:0] state
);
 localparam IDLE=0,RUN=1,FINISH_WORD=2,FLUSH=3,DONE=4,
            ABORT_DRAIN=5,FAILED=6,ABORTED=7,VERIFY=8;
 localparam integer WORDS=(TOTAL_BYTES+1)/2;
 reg [31:0] epoch,frame;
 reg [23:0] base;
 reg half_valid,word_valid;
 reg [7:0] low_byte;
 reg [15:0] word_data;
 reg [23:0] word_address;
 reg was_abort;
 wire active=(state==RUN||state==FINISH_WORD||state==FLUSH||state==VERIFY);
 wire identity_ok=in_owner==owner&&in_epoch==epoch&&in_frame==frame;
 wire last_ok=in_last==(accepted_bytes==TOTAL_BYTES-1);
 wire terminal=(state==DONE||state==FAILED||state==ABORTED);
 wire [24:0] region_end={1'b0,start_base}+WORDS;
 wire admission_ok=TOTAL_BYTES>0&&!TOTAL_BYTES[0]&&start_owner!=0&&
  start_epoch!=32'hffffffff&&start_frame!=32'hffffffff&&
  start_base>=APERTURE_BASE&&region_end<=({1'b0,APERTURE_BASE}+APERTURE_WORDS)&&
  region_end<=25'h1000000;
 assign start_ready=state==IDLE&&!reset;
 assign in_ready=state==RUN&&!word_valid&&identity_ok&&last_ok&&!abort&&!fault&&!reset;
 assign pixel_valid=word_valid&&(state==RUN||state==FINISH_WORD)&&!abort&&!fault&&!reset;
 assign pixel_address=word_address;
 assign pixel_data=word_data;
 assign force_flush=state==FLUSH;
 // Discard cannot undo a physical burst already accepted by the controller.
 // ABORT_DRAIN retains ownership until memory_idle proves that burst drained.
 assign discard=reset||state==IDLE||state==ABORT_DRAIN||state==FAILED||state==ABORTED||
  (active&&(abort||fault));
 assign busy=active||state==ABORT_DRAIN;
 assign done=state==DONE;
 assign failed=state==FAILED;
 assign aborted=state==ABORTED;
 always @(posedge clk)begin
  if(reset)begin
   state<=IDLE;owner<=0;epoch<=0;frame<=0;base<=0;accepted_bytes<=0;
   accepted_words<=0;half_valid<=0;word_valid<=0;low_byte<=0;word_data<=0;
   word_address<=0;error_code<=0;was_abort<=0;
  end else if(active&&(abort||fault))begin
   state<=ABORT_DRAIN;half_valid<=0;word_valid<=0;
   was_abort<=abort;error_code<=abort?4'd5:4'd4;
  end else begin
   if(pixel_valid&&pixel_ready)begin word_valid<=0;accepted_words<=accepted_words+1'b1;end
   case(state)
    IDLE:if(start_valid)begin
     owner<=start_owner;epoch<=start_epoch;frame<=start_frame;base<=start_base;
     accepted_bytes<=0;accepted_words<=0;half_valid<=0;word_valid<=0;was_abort<=0;
     error_code<=admission_ok?0:1;state<=admission_ok?RUN:ABORT_DRAIN;
    end
    RUN:begin
     if(in_valid&&(!identity_ok||!last_ok))begin
      error_code<=!identity_ok?2:3;state<=ABORT_DRAIN;half_valid<=0;word_valid<=0;was_abort<=0;
     end else if(in_valid&&in_ready)begin
      accepted_bytes<=accepted_bytes+1'b1;
      if(!half_valid)begin low_byte<=in_byte;half_valid<=1;end
      else begin
       word_data<={in_byte,low_byte};word_address<=base+(accepted_bytes>>1);
       word_valid<=1;half_valid<=0;
      end
      if(in_last)state<=FINISH_WORD;
     end
    end
    FINISH_WORD:if(!word_valid)state<=FLUSH;
    FLUSH:if(memory_idle)state<=VERIFY;
    VERIFY:if(integrity_valid&&memory_idle)state<=DONE;
    ABORT_DRAIN:if(memory_idle)state<=was_abort?ABORTED:FAILED;
    DONE,FAILED,ABORTED:if(release_result&&memory_idle)begin
     owner<=0;epoch<=0;frame<=0;state<=IDLE;
    end
    default:state<=IDLE;
   endcase
  end
 end
endmodule
`default_nettype wire
