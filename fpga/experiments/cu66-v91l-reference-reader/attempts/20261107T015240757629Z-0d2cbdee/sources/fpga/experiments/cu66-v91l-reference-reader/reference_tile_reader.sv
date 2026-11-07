`timescale 1ns/1ps
`default_nettype none
// Exactly one 64B tile payload; full 64-bit publication generation is never
// projected into the physical bridge's separate nonzero 32-bit ticket space.
module reference_tile_reader(
 input logic clk,power_on_reset,reset,cancel,
 input logic accepted_valid,input logic [1:0] accepted_bank,
 input logic [31:0] accepted_fid,input logic [63:0] accepted_generation,
 input logic ref_req_valid,output logic ref_req_ready,
 input logic [31:0] ref_req_epoch,ref_req_fid,input logic [63:0] ref_req_generation,
 input logic [1:0] ref_req_plane,input logic [12:0] ref_req_tile,
 output logic ref_rsp_valid,input logic ref_rsp_ready,
 output logic [31:0] ref_rsp_epoch,ref_rsp_fid,output logic [63:0] ref_rsp_generation,
 output logic [1:0] ref_rsp_plane,output logic [12:0] ref_rsp_tile,
 output logic [511:0] ref_rsp_pixels,output logic ref_rsp_error,
 output logic mem_req_valid,input logic mem_req_ready,
 output logic [31:0] mem_req_epoch,mem_req_generation,
 output logic [1:0] mem_req_bank,output logic [18:0] mem_req_addr,
 input logic mem_rsp_valid,output logic mem_rsp_ready,
 input logic [31:0] mem_rsp_epoch,mem_rsp_generation,
 input logic [1:0] mem_rsp_bank,input logic [18:0] mem_rsp_addr,
 input logic [127:0] mem_rsp_data,input logic mem_rsp_error,
 output logic busy,physical_pending,output logic [2:0] state,
 output logic [1:0] line_index,source_bank
);
 localparam logic [2:0] IDLE=0,OFFER=1,WAIT_LINE=2,RESPONSE=3;
 logic canceled,initialized=0;
 logic [18:0] tile_base;
 logic [31:0] ticket;
 wire kill=reset||cancel;
 wire legal_request=accepted_valid&&accepted_bank<3&&accepted_generation!=0&&
  ref_req_epoch!=0&&ref_req_fid==accepted_fid&&ref_req_generation==accepted_generation&&
  ((ref_req_plane==0&&ref_req_tile<5400)||((ref_req_plane==1||ref_req_plane==2)&&ref_req_tile<1350));
 wire match_line=mem_rsp_epoch==ref_rsp_epoch&&mem_rsp_generation==ticket&&
  mem_rsp_bank==source_bank&&mem_rsp_addr==mem_req_addr;
 assign busy=state!=IDLE;
 assign ref_req_ready=state==IDLE&&!kill&&!power_on_reset;
 assign ref_rsp_valid=state==RESPONSE&&!power_on_reset;
 assign mem_req_valid=state==OFFER&&!kill&&!canceled&&!power_on_reset;
 assign mem_req_epoch=ref_rsp_epoch;
 assign mem_req_generation=ticket;
 assign mem_req_bank=source_bank;
 assign mem_req_addr=tile_base+{13'd0,line_index,4'd0};
 assign mem_rsp_ready=physical_pending&&match_line&&!power_on_reset;
 always_ff @(posedge clk)begin
  initialized<=1;
  if(power_on_reset)begin
   state<=IDLE;canceled<=0;physical_pending<=0;line_index<=0;source_bank<=0;tile_base<=0;ticket<=1;
   ref_rsp_epoch<=0;ref_rsp_fid<=0;ref_rsp_generation<=0;ref_rsp_plane<=0;ref_rsp_tile<=0;
   ref_rsp_pixels<=0;ref_rsp_error<=0;
  end else begin
   case(state)
    IDLE:if(ref_req_valid&&ref_req_ready)begin
     ref_rsp_epoch<=ref_req_epoch;ref_rsp_fid<=ref_req_fid;ref_rsp_generation<=ref_req_generation;
     ref_rsp_plane<=ref_req_plane;ref_rsp_tile<=ref_req_tile;source_bank<=accepted_bank;
     ref_rsp_pixels<=0;ref_rsp_error<=!legal_request;line_index<=0;canceled<=0;
     tile_base<=(ref_req_plane==0?19'd0:ref_req_plane==1?19'd345600:19'd432000)+{ref_req_tile,6'd0};
     state<=legal_request?OFFER:RESPONSE;
    end
    OFFER:if(kill||canceled)begin ref_rsp_error<=1;state<=RESPONSE;canceled<=1;end
     else if(mem_req_valid&&mem_req_ready)begin physical_pending<=1;state<=WAIT_LINE;end
    WAIT_LINE:begin
     if(kill)canceled<=1;
     if(mem_rsp_valid&&mem_rsp_ready)begin
      physical_pending<=0;ticket<=ticket==32'hffffffff?32'd1:ticket+1;
      if(kill||canceled||mem_rsp_error)begin ref_rsp_error<=1;state<=RESPONSE;end
      else begin
       ref_rsp_pixels[int'(line_index)*128+:128]<=mem_rsp_data;
       if(line_index==3)state<=RESPONSE;
       else begin line_index<=line_index+1;state<=OFFER;end
      end
     end
    end
    // An already offered response is immutable, including through reset/cancel.
    RESPONSE:if(ref_rsp_valid&&ref_rsp_ready)state<=IDLE;
    default:state<=IDLE;
   endcase
  end
 end
`ifndef SYNTHESIS
 logic offered=0;
 always_ff @(posedge clk)begin
  if(power_on_reset&&initialized)assert(!busy)else $fatal(1,"cold reset while reference owned");
  if(!power_on_reset)begin
   if(mem_req_valid)assert(!physical_pending&&mem_req_addr[3:0]==0&&mem_req_addr<=518384&&ticket!=0)else $fatal(1,"reference line bounds/ownership");
   if(ref_req_valid&&ref_req_ready)$display("{\"type\":\"ref_req\",\"time_ps\":%0d,\"epoch\":%0d,\"fid\":%0d,\"generation\":%0d,\"plane\":%0d,\"tile\":%0d,\"bank\":%0d,\"lease_valid\":%0d}",longint'($realtime*1000.0),ref_req_epoch,ref_req_fid,ref_req_generation,ref_req_plane,ref_req_tile,accepted_bank,accepted_valid);
   if(ref_rsp_valid&&(!offered||ref_rsp_ready))$display("{\"type\":\"%s\",\"time_ps\":%0d,\"epoch\":%0d,\"fid\":%0d,\"generation\":%0d,\"plane\":%0d,\"tile\":%0d,\"bank\":%0d,\"error\":%0d,\"data\":\"%0128h\"}",ref_rsp_ready?"ref_rsp":"ref_rsp_offer",longint'($realtime*1000.0),ref_rsp_epoch,ref_rsp_fid,ref_rsp_generation,ref_rsp_plane,ref_rsp_tile,source_bank,ref_rsp_error,ref_rsp_pixels);
   if(mem_req_valid&&mem_req_ready)$display("{\"type\":\"ref_line_req\",\"time_ps\":%0d,\"epoch\":%0d,\"fid\":%0d,\"generation\":%0d,\"plane\":%0d,\"tile\":%0d,\"bank\":%0d,\"address\":%0d,\"ticket\":%0d,\"line\":%0d}",longint'($realtime*1000.0),ref_rsp_epoch,ref_rsp_fid,ref_rsp_generation,ref_rsp_plane,ref_rsp_tile,source_bank,mem_req_addr,ticket,line_index);
   if(mem_rsp_valid&&mem_rsp_ready)$display("{\"type\":\"ref_line_rsp\",\"time_ps\":%0d,\"epoch\":%0d,\"fid\":%0d,\"generation\":%0d,\"plane\":%0d,\"tile\":%0d,\"bank\":%0d,\"address\":%0d,\"ticket\":%0d,\"line\":%0d,\"error\":%0d,\"data\":\"%032h\"}",longint'($realtime*1000.0),ref_rsp_epoch,ref_rsp_fid,ref_rsp_generation,ref_rsp_plane,ref_rsp_tile,mem_rsp_bank,mem_rsp_addr,mem_rsp_generation,line_index,mem_rsp_error,mem_rsp_data);
  end
  offered<=ref_rsp_valid&&!ref_rsp_ready;
 end
`endif
endmodule
`default_nettype wire
