`timescale 1ns/1ps
`default_nettype none
// Single-clock research writer. External drain and ownership are assumed.
// No CRC, CDC, physical timing, response, timeout, or published metadata.
module sdram_jpeg_writer #(
 parameter integer BASE_WORDS='h060000,
 parameter integer CAP_BYTES=262144,
 parameter integer END_WORDS='h080000
)(
 input wire clk,reset,
 input wire begin_valid,output wire begin_ready,input wire[31:0]declared_length,
 output reg begin_accept,begin_reject,
 input wire byte_valid,output wire byte_ready,input wire[7:0]byte_data,
 input wire abort,input wire sink_fault,input wire write_drain_done,
 output wire write_valid,input wire write_ready,output wire[23:0]write_address,output wire[127:0]write_data,
 output reg active,done,aborted,failed,output reg faulted,
 output reg[31:0]accepted_bytes,output reg[31:0]issued_bursts
);
 reg[31:0]length;reg[3:0]byte_index;reg[127:0]buffer;
 reg buffer_full,await_drain,aborting,failing,offer_locked;
 assign begin_ready=!reset&&!active&&!faulted&&!sink_fault&&!abort;
 assign byte_ready=!reset&&active&&!abort&&!sink_fault&&!aborting&&!failing&&!await_drain&&!buffer_full&&(accepted_bytes<length);
 // Once observed valid while stalled, an offer cannot be withdrawn even if
 // abort/fault arrives. Finish that handshake, then drain without publication.
 assign write_valid=!reset&&active&&!await_drain&&buffer_full&&
                    (offer_locked||(!abort&&!sink_fault&&!aborting&&!failing));
 assign write_address=24'(BASE_WORDS+issued_bursts*8);
 assign write_data=buffer;
 always @(posedge clk)begin
  if(reset)begin
   begin_accept<=0;begin_reject<=0;active<=0;done<=0;aborted<=0;failed<=0;faulted<=0;
   accepted_bytes<=0;issued_bursts<=0;length<=0;byte_index<=0;buffer<=0;
   buffer_full<=0;await_drain<=0;aborting<=0;failing<=0;offer_locked<=0;
  end else begin
   begin_accept<=0;begin_reject<=0;done<=0;aborted<=0;failed<=0;
   if(begin_valid&&begin_ready)begin
    if(declared_length==0||declared_length>CAP_BYTES||BASE_WORDS<0||BASE_WORDS%8!=0||
       END_WORDS>1048576||BASE_WORDS+((CAP_BYTES+15)/16)*8>END_WORDS)begin_reject<=1;
    else begin
     length<=declared_length;accepted_bytes<=0;issued_bursts<=0;byte_index<=0;
     buffer<=0;buffer_full<=0;await_drain<=0;aborting<=0;failing<=0;offer_locked<=0;active<=1;begin_accept<=1;
    end
   end
   if(active)begin
    if(write_valid&&!write_ready)offer_locked<=1;
    if(sink_fault && !failing)begin
     faulted<=1;failing<=1;aborting<=0;
     if(!offer_locked)begin buffer_full<=0;await_drain<=1;end
     else if(write_valid&&write_ready)begin buffer_full<=0;offer_locked<=0;issued_bursts<=issued_bursts+1'b1;await_drain<=1;end
    end
    else if(abort && !aborting && !failing)begin
     aborting<=1;
     if(!offer_locked)begin buffer_full<=0;await_drain<=1;end
     else if(write_valid&&write_ready)begin buffer_full<=0;offer_locked<=0;issued_bursts<=issued_bursts+1'b1;await_drain<=1;end
    end
    else if((aborting||failing)&&offer_locked)begin
     if(write_valid&&write_ready)begin buffer_full<=0;offer_locked<=0;issued_bursts<=issued_bursts+1'b1;await_drain<=1;end
    end
    else if(await_drain && write_drain_done)begin
     active<=0;await_drain<=0;
     if(failing)begin failed<=1;failing<=0;end
     else if(aborting)begin aborted<=1;aborting<=0;end
     else done<=1;
    end else begin
     if(byte_valid&&byte_ready)begin
      buffer[byte_index*8+:8]<=byte_data;accepted_bytes<=accepted_bytes+1'b1;
      if(byte_index==15 || accepted_bytes+1'b1==length)begin buffer_full<=1;byte_index<=0;end
      else byte_index<=byte_index+1'b1;
     end
     if(write_valid&&write_ready)begin
      buffer_full<=0;buffer<=0;offer_locked<=0;issued_bursts<=issued_bursts+1'b1;
      if(accepted_bytes==length)await_drain<=1;
     end
    end
   end
  end
 end
endmodule
`default_nettype wire
