`timescale 1ns/1ps
`default_nettype none
// Per-16B round robin. The owner survives accepted commands, drain, and held
// replies. accepted gates repeated client offers throughout the release cycle.
module reader_client_mux(
input logic clk,power_on_reset,
output logic [1:0] owner,
input logic display_reset,display_cancel,display_req_valid,display_rsp_ready,
output logic display_req_ready,display_rsp_valid,display_rsp_error,
input logic [31:0] display_req_epoch,display_req_generation,
input logic [1:0] display_req_bank,input logic [18:0] display_req_addr,
output logic [31:0] display_rsp_epoch,display_rsp_generation,
output logic [1:0] display_rsp_bank,output logic [18:0] display_rsp_addr,
output logic [127:0] display_rsp_data,
input logic reference_reset,reference_cancel,reference_req_valid,reference_rsp_ready,
output logic reference_req_ready,reference_rsp_valid,reference_rsp_error,
input logic [31:0] reference_req_epoch,reference_req_generation,
input logic [1:0] reference_req_bank,input logic [18:0] reference_req_addr,
output logic [31:0] reference_rsp_epoch,reference_rsp_generation,
output logic [1:0] reference_rsp_bank,output logic [18:0] reference_rsp_addr,
output logic [127:0] reference_rsp_data,
output logic mem_reset,mem_cancel,mem_req_valid,mem_rsp_ready,
input logic mem_req_ready,mem_rsp_valid,mem_rsp_error,
output logic [31:0] mem_req_epoch,mem_req_generation,
output logic [1:0] mem_req_bank,output logic [18:0] mem_req_addr,
input logic [31:0] mem_rsp_epoch,mem_rsp_generation,
input logic [1:0] mem_rsp_bank,input logic [18:0] mem_rsp_addr,
input logic [127:0] mem_rsp_data,
input logic mem_busy);
 logic accepted,last_reference,initialized=0;
 logic [31:0] epoch,generation;logic [1:0] bank;logic [18:0] address;
 wire display_owned=owner==1,reference_owned=owner==2;
 wire response_match=mem_rsp_epoch==epoch&&mem_rsp_generation==generation&&mem_rsp_bank==bank&&mem_rsp_addr==address;
 assign mem_reset=(display_owned&&display_reset)||(reference_owned&&reference_reset);
 assign mem_cancel=(display_owned&&display_cancel)||(reference_owned&&reference_cancel);
 assign mem_req_valid=!accepted&&((display_owned&&display_req_valid&&!display_reset&&!display_cancel)||(reference_owned&&reference_req_valid&&!reference_reset&&!reference_cancel));
 assign mem_req_epoch=display_owned?display_req_epoch:reference_req_epoch;
 assign mem_req_generation=display_owned?display_req_generation:reference_req_generation;
 assign mem_req_bank=display_owned?display_req_bank:reference_req_bank;
 assign mem_req_addr=display_owned?display_req_addr:reference_req_addr;
 assign display_req_ready=display_owned&&!accepted&&mem_req_ready&&!display_reset&&!display_cancel;
 assign reference_req_ready=reference_owned&&!accepted&&mem_req_ready&&!reference_reset&&!reference_cancel;
 assign display_rsp_valid=display_owned&&accepted&&mem_rsp_valid&&response_match;
 assign reference_rsp_valid=reference_owned&&accepted&&mem_rsp_valid&&response_match;
 assign mem_rsp_ready=accepted&&response_match&&((display_owned&&display_rsp_ready)||(reference_owned&&reference_rsp_ready));
 assign display_rsp_data=mem_rsp_data;
 assign display_rsp_epoch=mem_rsp_epoch;
 assign display_rsp_generation=mem_rsp_generation;
 assign display_rsp_bank=mem_rsp_bank;
 assign display_rsp_addr=mem_rsp_addr;
 assign display_rsp_error=mem_rsp_error;
 assign reference_rsp_data=mem_rsp_data;
 assign reference_rsp_epoch=mem_rsp_epoch;
 assign reference_rsp_generation=mem_rsp_generation;
 assign reference_rsp_bank=mem_rsp_bank;
 assign reference_rsp_addr=mem_rsp_addr;
 assign reference_rsp_error=mem_rsp_error;
 always_ff @(posedge clk)begin
  initialized<=1;
  if(power_on_reset)begin owner<=0;accepted<=0;last_reference<=1;epoch<=0;generation<=0;bank<=0;address<=0;end
  else if(owner==0)begin
   accepted<=0;
   if(display_req_valid&&!display_reset&&!display_cancel&&(!reference_req_valid||reference_reset||reference_cancel||last_reference))begin owner<=1;last_reference<=0;end
   else if(reference_req_valid&&!reference_reset&&!reference_cancel)begin owner<=2;last_reference<=1;end
  end else begin
   if(mem_req_valid&&mem_req_ready)begin accepted<=1;epoch<=mem_req_epoch;generation<=mem_req_generation;bank<=mem_req_bank;address<=mem_req_addr;end
   if((accepted&&!mem_busy&&!mem_rsp_valid)||(!accepted&&!mem_req_valid))begin owner<=0;accepted<=0;end
  end
 end
`ifndef SYNTHESIS
 logic [1:0] prior_owner=0;
 always_ff @(posedge clk)begin
  if(power_on_reset&&initialized)assert(!accepted)else $fatal(1,"cold reset while mux owns accepted line");
  if(!power_on_reset)begin
   if(owner==0&&(display_req_valid||reference_req_valid))$display("{\"type\":\"mux_arbitrate\",\"time_ps\":%0d,\"display_eligible\":%0d,\"reference_eligible\":%0d,\"last_reference\":%0d}",longint'($realtime*1000.0),display_req_valid&&!display_reset&&!display_cancel,reference_req_valid&&!reference_reset&&!reference_cancel,last_reference);
   if(owner!=prior_owner)$display("{\"type\":\"mux_owner\",\"time_ps\":%0d,\"old_owner\":%0d,\"owner\":%0d}",longint'($realtime*1000.0),prior_owner,owner);
   if(mem_req_valid&&mem_req_ready)$display("{\"type\":\"mux_req\",\"time_ps\":%0d,\"owner\":%0d,\"epoch\":%0d,\"generation\":%0d,\"bank\":%0d,\"address\":%0d}",longint'($realtime*1000.0),owner,mem_req_epoch,mem_req_generation,mem_req_bank,mem_req_addr);
   if(mem_rsp_valid&&mem_rsp_ready)$display("{\"type\":\"mux_rsp\",\"time_ps\":%0d,\"owner\":%0d,\"epoch\":%0d,\"generation\":%0d,\"bank\":%0d,\"address\":%0d,\"error\":%0d,\"data\":\"%032h\"}",longint'($realtime*1000.0),owner,mem_rsp_epoch,mem_rsp_generation,mem_rsp_bank,mem_rsp_addr,mem_rsp_error,mem_rsp_data);
  end
  prior_owner<=owner;
 end
`endif
endmodule
`default_nettype wire
