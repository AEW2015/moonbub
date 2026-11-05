`timescale 1ns/1ps
`default_nettype none
// CP23 outer integrity diagnostic only. No decoded-frame acceptance or ACK.
module cp23_envelope(
 input wire clk,reset,
 input wire start_valid,output wire start_ready,input wire[63:0]start_owner,
 input wire[31:0]start_epoch,start_frame,start_bytes,
 input wire in_valid,output wire in_ready,input wire[7:0]in_byte,input wire in_last,
 input wire abort_valid,input wire[63:0]abort_owner,input wire[31:0]abort_epoch,abort_frame,
 output wire abort_rejected,
 output wire result_valid,input wire result_ready,output reg[3:0]result_code,
 output reg envelope_checked,output wire payload_supported,output wire component_magic_known,
 output wire[63:0]result_owner,output wire[31:0]result_epoch,result_frame,
 output wire[31:0]base_bytes,hud_bytes,received_bytes
);
 localparam IDLE=0,HEADER=1,CHECK=2,HSTART=3,BODY=4,FINISH=5,RESULT=6;
 // 1 metadata,2 header/length,3 identity,4 CRC,5 SHA,6 framing,7 SHA child,8 abort,
 // 9 outer checked but full AR03/HC22/HD22 payload decoder is NOT implemented.
 reg[2:0]state=IDLE;reg[63:0]owner;reg[31:0]epoch,frame,total,count,nb,nh,hepoch,hframe;
 reg[31:0]magic,base_magic,hud_magic,crc,wire_crc;reg[7:0]version;
 reg[127:0]bh,hh;integer bitpos;
 wire abort_live=abort_valid&&state!=IDLE&&abort_owner==owner&&abort_epoch==epoch&&abort_frame==frame;
 wire abort_incoming=abort_valid&&state==IDLE&&start_valid&&abort_owner==start_owner&&abort_epoch==start_epoch&&abort_frame==start_frame;
 assign abort_rejected=abort_valid&&!abort_live&&!abort_incoming;
 assign start_ready=state==IDLE&&!reset&&!abort_incoming;
 assign result_valid=state==RESULT&&!reset&&!abort_live;
 assign result_owner=owner;assign result_epoch=epoch;assign result_frame=frame;
 assign base_bytes=nb;assign hud_bytes=nh;assign received_bytes=count;
 assign payload_supported=1'b0;
 assign component_magic_known=base_magic==32'h33305241&&hud_magic==32'h32324348;
 wire bs,hs,bi,hi,bv,hv,be,he;wire[255:0]bd,hd;wire[63:0]bo,ho;wire[31:0]bep,hep;wire[1:0]bec,hec;
 wire cancel_children=reset||abort_live||state==RESULT;
 wire launch=state==HSTART&&bs&&hs&&!reset&&!abort_live;
 wire body_base=count>=53&&count<53+nb;
 wire body_hud=count>=53+nb&&count<total-4;
 assign in_ready=!reset&&!abort_live&&(state==HEADER||(state==BODY&&(!body_base||bi)&&(!body_hud||hi)));
 sha256_bytes #(.MAX_BYTES(49152))base_sha(.clk(clk),.reset(reset),.abort(cancel_children),.start_valid(launch),.start_ready(bs),.start_owner(owner),.start_epoch(epoch),.start_length({32'd0,nb}),.in_valid(in_valid&&in_ready&&state==BODY&&body_base),.in_ready(bi),.in_byte(in_byte),.in_last(count==52+nb),.out_valid(bv),.out_ready(1'b0),.out_digest(bd),.out_owner(bo),.out_epoch(bep),.error_valid(be),.error_ready(1'b0),.error_code(bec));
 sha256_bytes #(.MAX_BYTES(49152))hud_sha(.clk(clk),.reset(reset),.abort(cancel_children),.start_valid(launch),.start_ready(hs),.start_owner(owner),.start_epoch(epoch),.start_length({32'd0,nh}),.in_valid(in_valid&&in_ready&&state==BODY&&body_hud),.in_ready(hi),.in_byte(in_byte),.in_last(count==total-5),.out_valid(hv),.out_ready(1'b0),.out_digest(hd),.out_owner(ho),.out_epoch(hep),.error_valid(he),.error_ready(1'b0),.error_code(hec));
 function automatic[31:0]crc_byte(input[31:0]old,input[7:0]value);
 reg[31:0]v;integer j;begin v=old^value;for(j=0;j<8;j=j+1)v=v[0]?(v>>1)^32'hedb88320:v>>1;crc_byte=v;end endfunction
 task fail(input[3:0]code);begin state<=RESULT;result_code<=code;envelope_checked<=0;end endtask
 always @(posedge clk)begin
  if(reset)begin state<=IDLE;owner<=0;epoch<=0;frame<=0;total<=0;count<=0;nb<=0;nh<=0;hepoch<=0;hframe<=0;magic<=0;version<=0;base_magic<=0;hud_magic<=0;crc<=32'hffffffff;wire_crc<=0;bh<=0;hh<=0;result_code<=0;envelope_checked<=0;end
  else if(abort_live)fail(8);
  else begin
   if(state==IDLE&&start_valid&&start_ready)begin
    owner<=start_owner;epoch<=start_epoch;frame<=start_frame;total<=start_bytes;count<=0;nb<=0;nh<=0;hepoch<=0;hframe<=0;magic<=0;version<=0;base_magic<=0;hud_magic<=0;crc<=32'hffffffff;wire_crc<=0;bh<=0;hh<=0;result_code<=0;envelope_checked<=0;
    if(start_owner==0||start_epoch==0||start_epoch==32'hffffffff||start_frame==32'hffffffff||start_bytes<57||start_bytes>49152)fail(1);else state<=HEADER;
   end
   if((state==HEADER||state==BODY)&&in_valid&&in_ready)begin
    count<=count+1;
    if(in_last!=(count==total-1))fail(6);
    else begin
     if(count<total-4)crc<=crc_byte(crc,in_byte);
     if(state==HEADER)begin
      if(count<4)magic[count*8+:8]<=in_byte;
      if(count==4)version<=in_byte;
      if(count>=5&&count<9)hepoch[(count-5)*8+:8]<=in_byte;
      if(count>=9&&count<13)hframe[(count-9)*8+:8]<=in_byte;
      if(count>=13&&count<17)nb[(count-13)*8+:8]<=in_byte;
      if(count>=17&&count<21)nh[(count-17)*8+:8]<=in_byte;
      if(count>=21&&count<37)bh[127-(count-21)*8-:8]<=in_byte;
      if(count>=37&&count<53)hh[127-(count-37)*8-:8]<=in_byte;
      if(count==52)state<=CHECK;
     end else begin
      if(count>=53&&count<57)base_magic[(count-53)*8+:8]<=in_byte;
      if(count>=53+nb&&count<57+nb)hud_magic[(count-53-nb)*8+:8]<=in_byte;
      if(count>=total-4)wire_crc[(count-(total-4))*8+:8]<=in_byte;
      if(count==total-1)begin
       if({in_byte,wire_crc[23:0]}!=~crc)fail(4);else state<=FINISH;
      end
     end
    end
   end
   if(state==CHECK)begin
    if(magic!=32'h33325043||version!=1||nb==0||nh==0||nb>49152||nh>49152||({2'b0,nb}+{2'b0,nh}+34'd57)!={2'b0,total})fail(2);
    else if(hepoch!=epoch||hframe!=frame)fail(3);
    else state<=HSTART;
   end
   if(launch)state<=BODY;
   if((state==BODY||state==FINISH)&&(be||he))fail(7);
   if(state==FINISH&&bv&&hv)begin
    if(bo!=owner||ho!=owner||bep!=epoch||hep!=epoch||bd[255:128]!=bh||hd[255:128]!=hh)fail(5);
    else begin state<=RESULT;result_code<=9;envelope_checked<=1;end
   end
   if(state==RESULT&&result_valid&&result_ready)state<=IDLE;
  end
 end
endmodule
`default_nettype wire
