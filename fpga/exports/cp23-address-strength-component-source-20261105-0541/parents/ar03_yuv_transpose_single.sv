`timescale 1ns/1ps
// One-stripe, owner-scoped WORD-input transpose. Fixed720x480 only.
// No publication, frame switch, HUD, runtime reset/rekey, or physical map.
module ar03_yuv_transpose_single #(
 parameter[23:0]APERTURE_BASE=24'h100000,parameter integer APERTURE_WORDS=262144
)(
 input wire clk,reset,
 input wire start_valid,output wire start_ready,output wire start_rejected,
 input wire[63:0]start_owner,input wire[31:0]start_epoch,start_frame,
 input wire[15:0]start_width,start_height,input wire[23:0]start_base,
 input wire in_valid,output wire in_ready,input wire[23:0]in_address,input wire[15:0]in_data,
 input wire[63:0]in_owner,input wire[31:0]in_epoch,in_frame,
 input wire upstream_flush,upstream_discard,abort,fault,
 output wire pixel_valid,input wire pixel_ready,output wire[23:0]pixel_address,output wire[15:0]pixel_data,
 output wire force_flush,discard,input wire memory_idle,
 output wire store_idle,output wire done,failed,aborted,
 input wire release_valid,input wire[63:0]release_owner,input wire[31:0]release_epoch,release_frame,
 output wire release_rejected,
 output reg[63:0]owner,output reg[31:0]input_words,processed_bytes,output_words,
 output reg[31:0]stripe_high_water,output reg[3:0]error_code,output reg[3:0]state
);
 localparam IDLE=0,FILL=1,DRAIN=2,WAIT_END=3,FLUSH=4,DONE=5,ABORT_DRAIN=6,FAILED=7,ABORTED=8;
 localparam TOTAL_WORDS=259200;
 reg[31:0]epoch,frame;reg[23:0]base;
 (* ram_style="block" *)reg[7:0]stripe[0:11519];
 reg skid_valid,skid_high;reg[15:0]skid;
 reg[1:0]plane;reg[8:0]stripe_y;reg[9:0]fill_x,drain_x;reg[3:0]fill_row,drain_row;
 reg[13:0]stripe_bytes;reg finish_seen,was_abort;
 reg read_high,out_valid;reg[7:0]low_read;reg[15:0]out_data;reg[23:0]out_address;
 wire[9:0]pw=plane==0?10'd720:10'd360;
 wire[8:0]ph=plane==0?9'd480:9'd240;
 wire[23:0]plane_base=plane==0?24'd0:plane==1?24'd172800:24'd216000;
 wire active=state==FILL||state==DRAIN||state==WAIT_END||state==FLUSH;
 wire terminal=state==DONE||state==FAILED||state==ABORTED;
 wire[31:0]fill_address={28'd0,fill_row}*{22'd0,pw}+{22'd0,fill_x};
 wire[31:0]low_address={28'd0,drain_row}*{22'd0,pw}+{22'd0,drain_x};
 wire[31:0]high_address=({28'd0,drain_row}+32'd1)*{22'd0,pw}+{22'd0,drain_x};
 wire[31:0]absolute_drain_y={23'd0,stripe_y}+{28'd0,drain_row};
 wire identity=in_owner==owner&&in_epoch==epoch&&in_frame==frame;
 wire address_ok=in_address==base+input_words;
 wire offer_space=active&&!skid_valid&&input_words<TOTAL_WORDS&&state!=WAIT_END&&state!=FLUSH;
 wire bad_word=in_valid&&offer_space&&(!identity||!address_ok);
 wire extra_word=in_valid&&active&&!skid_valid&&input_words==TOTAL_WORDS;
 wire accept=in_valid&&in_ready;
 wire premature_end=upstream_flush&&active&&input_words!=TOTAL_WORDS&&!(accept&&input_words==TOTAL_WORDS-1);
 wire cancel_active=active&&(abort||fault||upstream_discard||bad_word||extra_word||premature_end);
 wire[24:0]end_address={1'b0,start_base}+25'd259200;
 wire admission=start_owner!=0&&start_epoch!=32'hffffffff&&start_frame!=32'hffffffff&&
  start_width==720&&start_height==480&&start_base[2:0]==0&&start_base>=APERTURE_BASE&&
  end_address<=({1'b0,APERTURE_BASE}+APERTURE_WORDS)&&end_address<=25'h1000000;
 wire release_match=owner!=0&&release_owner==owner&&release_epoch==epoch&&release_frame==frame;
 assign start_ready=state==IDLE&&!reset&&!abort&&!fault;
 assign start_rejected=start_valid&&start_ready&&!admission;
 assign in_ready=offer_space&&identity&&address_ok&&!reset&&!abort&&!fault&&!upstream_discard;
 assign pixel_valid=state==DRAIN&&out_valid&&!reset&&!cancel_active;
 assign pixel_address=out_address;assign pixel_data=out_data;
 // Upstream FLUSH cannot reach the packer until all local output has drained.
 assign force_flush=state==FLUSH&&!reset&&!cancel_active;
 assign discard=reset||state==IDLE||state==ABORT_DRAIN||state==FAILED||state==ABORTED||cancel_active;
 // Includes this adapter's final flush fence; never asserts in WAIT_END/FLUSH.
 assign store_idle=(state==IDLE||terminal)&&!skid_valid&&!out_valid&&stripe_bytes==0&&memory_idle;
 assign done=state==DONE;assign failed=state==FAILED;assign aborted=state==ABORTED;
 assign release_rejected=release_valid&&(!terminal||!release_match||!store_idle);
 always @(posedge clk)begin
  if(reset)begin
   state<=IDLE;owner<=0;epoch<=0;frame<=0;base<=0;input_words<=0;processed_bytes<=0;output_words<=0;
   skid_valid<=0;skid_high<=0;skid<=0;plane<=0;stripe_y<=0;fill_x<=0;fill_row<=0;
   drain_x<=0;drain_row<=0;stripe_bytes<=0;stripe_high_water<=0;finish_seen<=0;was_abort<=0;
   read_high<=0;low_read<=0;out_valid<=0;out_data<=0;out_address<=0;error_code<=0;
  end else if(cancel_active)begin
   state<=ABORT_DRAIN;was_abort<=abort;error_code<=abort?4'd5:fault||upstream_discard?4'd4:bad_word?(!identity?4'd2:4'd3):4'd6;
   skid_valid<=0;out_valid<=0;stripe_bytes<=0;read_high<=0;
  end else begin
   if(upstream_flush&&active)finish_seen<=1;
   if(accept)begin skid<=in_data;skid_valid<=1;skid_high<=0;input_words<=input_words+1;end
   case(state)
    IDLE:if(start_valid&&start_ready&&admission)begin
     // IDLE's normal upstream discard does not cancel this guarded START.
     owner<=start_owner;epoch<=start_epoch;frame<=start_frame;base<=start_base;
     input_words<=0;processed_bytes<=0;output_words<=0;plane<=0;stripe_y<=0;fill_x<=0;fill_row<=0;
     stripe_bytes<=0;stripe_high_water<=0;finish_seen<=0;was_abort<=0;error_code<=0;
     skid_valid<=0;out_valid<=0;read_high<=0;state<=FILL;
    end
    FILL:if(skid_valid)begin
     stripe[fill_address]<=skid_high?skid[15:8]:skid[7:0];
     stripe_bytes<=stripe_bytes+1;processed_bytes<=processed_bytes+1;
     if(stripe_bytes+1>stripe_high_water)stripe_high_water<=stripe_bytes+1;
     if(skid_high)begin skid_valid<=0;skid_high<=0;end else skid_high<=1;
     if(fill_x==pw-1)begin
      fill_x<=0;
      if(fill_row==15)begin fill_row<=0;drain_x<=0;drain_row<=0;read_high<=0;state<=DRAIN;end
      else fill_row<=fill_row+1;
     end else fill_x<=fill_x+1;
    end
    DRAIN:begin
     if(out_valid&&pixel_ready)begin
      out_valid<=0;output_words<=output_words+1;
      if(drain_row==14)begin
       drain_row<=0;
       if(drain_x==pw-1)begin
        drain_x<=0;stripe_bytes<=0;fill_x<=0;fill_row<=0;
        if(stripe_y+16==ph)begin
         stripe_y<=0;
         if(plane==2)state<=finish_seen||upstream_flush?FLUSH:WAIT_END;
         else begin plane<=plane+1;state<=FILL;end
        end else begin stripe_y<=stripe_y+16;state<=FILL;end
       end else drain_x<=drain_x+1;
      end else drain_row<=drain_row+2;
     end else if(!out_valid)begin
      // One byte read per cycle; data registers have validity-controlled use.
      if(!read_high)begin low_read<=stripe[low_address];read_high<=1;end
      else begin
       out_data<={stripe[high_address],low_read};
       out_address<=base+plane_base+drain_x*(ph>>1)+(absolute_drain_y>>1);
       out_valid<=1;read_high<=0;
      end
     end
    end
    WAIT_END:if(finish_seen||upstream_flush)state<=FLUSH;
    FLUSH:if(memory_idle)state<=DONE;
    ABORT_DRAIN:if(memory_idle)state<=was_abort?ABORTED:FAILED;
    DONE,FAILED,ABORTED:if(release_valid&&release_match&&store_idle)begin state<=IDLE;owner<=0;epoch<=0;frame<=0;end
   endcase
  end
 end
endmodule
