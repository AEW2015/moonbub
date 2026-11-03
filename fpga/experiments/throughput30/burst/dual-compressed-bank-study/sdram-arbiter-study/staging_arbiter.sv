`timescale 1ns/1ps
`default_nettype none
// Research-only synchronous command arbiter. Inputs and reads are BL8 words;
// clients must retain valid/address/payload until ready. Read sinks must always
// consume each returned beat; this module contains no response FIFO or CDC.
module staging_arbiter(
 input wire clk,reset,
 input wire display_valid,output wire display_ready,input wire[23:0]display_addr,
 output wire display_data_valid,output wire[15:0]display_data,
 input wire pixel_valid,output wire pixel_ready,input wire[23:0]pixel_addr,input wire[127:0]pixel_data,
 input wire jwrite_valid,output wire jwrite_ready,input wire[23:0]jwrite_addr,input wire[127:0]jwrite_data,
 input wire jread_valid,output wire jread_ready,input wire[23:0]jread_addr,
 output wire jread_data_valid,output wire[15:0]jread_data,
 output wire request_valid,input wire request_ready,output wire request_write,
 output wire[23:0]request_addr,output wire[127:0]request_data,
 input wire response_valid,input wire[15:0]response_data,
 output wire read_busy,output reg protocol_fault
);
 localparam [2:0] NONE=0,DISPLAY=1,PIXEL=2,JWRITE=3,JREAD=4;
 reg[2:0] selected;reg[1:0] rr;reg pending_read,pending_owner;reg[2:0]read_beat;
 always @* begin
  selected=NONE;
  if(display_valid) selected=DISPLAY;
  else case(rr)
   0:if(pixel_valid)selected=PIXEL;else if(jwrite_valid)selected=JWRITE;else if(jread_valid)selected=JREAD;
   1:if(jwrite_valid)selected=JWRITE;else if(jread_valid)selected=JREAD;else if(pixel_valid)selected=PIXEL;
   default:if(jread_valid)selected=JREAD;else if(pixel_valid)selected=PIXEL;else if(jwrite_valid)selected=JWRITE;
  endcase
 end
 assign request_addr=selected==DISPLAY?display_addr:selected==PIXEL?pixel_addr:selected==JWRITE?jwrite_addr:jread_addr;
 assign request_data=selected==PIXEL?pixel_data:jwrite_data;
 assign request_write=(selected==PIXEL || selected==JWRITE);
 wire selected_aligned=request_addr[2:0]==0;
 assign request_valid=(selected!=NONE)&&selected_aligned&&!pending_read&&!protocol_fault&&!reset;
 wire grant=request_valid && request_ready;
 assign display_ready=grant && selected==DISPLAY;
 assign pixel_ready=grant && selected==PIXEL;
 assign jwrite_ready=grant && selected==JWRITE;
 assign jread_ready=grant && selected==JREAD;
 assign display_data_valid=response_valid && pending_read && !pending_owner;
 assign jread_data_valid=response_valid && pending_read && pending_owner;
 assign display_data=response_data;assign jread_data=response_data;assign read_busy=pending_read;
 always @(posedge clk)begin
  if(reset)begin rr<=0;pending_read<=0;pending_owner<=0;read_beat<=0;protocol_fault<=0;end
  else begin
   if((selected!=NONE && !selected_aligned && !pending_read && request_ready) || (response_valid && !pending_read))protocol_fault<=1;
   if(grant)begin
    case(selected)
     PIXEL:rr<=1;JWRITE:rr<=2;JREAD:rr<=0;default:;
    endcase
    if(selected==DISPLAY || selected==JREAD)begin pending_read<=1;pending_owner<=(selected==JREAD);read_beat<=0;end
   end
   if(response_valid && pending_read)begin
    if(read_beat==7)begin pending_read<=0;read_beat<=0;end
    else read_beat<=read_beat+1'b1;
   end
  end
 end
endmodule
`default_nettype wire
