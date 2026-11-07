`timescale 1ns/1ps
`default_nettype none
// Bounded reference-tile reservation. Lower transactions remain 16 bytes.
// One matching reply ACK plus physical bridge drain retires each line.
module tile_reader_mux #(parameter integer REF_LINES=4,GAP_CYCLES=8)(
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
input logic mem_busy,
output logic [2:0] grant_lines,
output logic [3:0] grant_gap,
output logic grant_reserved,
output logic [31:0] grant_groups,grant_continuations,grant_timeouts,grant_mismatches,
output logic [31:0] grant_yields,grant_cancel_yields,grant_error_yields);
 logic accepted,last_reference,initialized=0;
 logic group_valid,group_killed,response_seen,response_failed;
 logic [18:0] group_base;
 wire [31:0] next_ticket=generation==32'hffffffff?32'd1:generation+32'd1;
 wire continuation_match=reference_req_epoch==epoch&&reference_req_bank==bank&&
  reference_req_generation==next_ticket&&reference_req_addr==address+19'd16&&
  reference_req_addr[18:6]==group_base[18:6];
 wire first_group_legal=reference_req_epoch!=0&&reference_req_generation!=0&&
  reference_req_bank<3&&reference_req_addr[5:0]==0&&reference_req_addr<=19'd518336;
 wire reference_eligible=reference_req_valid&&!reference_reset&&!reference_cancel&&
  (!grant_reserved||continuation_match);
 wire owned_kill=reference_owned?(reference_reset||reference_cancel):(display_reset||display_cancel);
 wire line_closed=accepted&&!mem_busy&&!mem_rsp_valid;
 wire may_reserve=reference_owned&&group_valid&&grant_lines<3'(REF_LINES)&&
  !group_killed&&!owned_kill&&!response_failed&&response_seen;
 wire continuation_mismatch=grant_reserved&&reference_req_valid&&!continuation_match;
 wire gap_timeout=grant_reserved&&!reference_req_valid&&grant_gap==4'(GAP_CYCLES-1);
 wire [2:0] yield_reason=owned_kill||group_killed?3'd1:response_failed?3'd2:
  (continuation_mismatch||(line_closed&&may_reserve&&reference_req_valid&&!continuation_match))?3'd3:
  gap_timeout?3'd4:3'd0;
 wire release_now=owner!=0&&((line_closed&&(!may_reserve||yield_reason!=0))||
  (!accepted&&(!grant_reserved&&!mem_req_valid))||
  (!accepted&&grant_reserved&&(owned_kill||group_killed||continuation_mismatch||gap_timeout)));
 initial begin assert(REF_LINES==1||REF_LINES==4);assert(GAP_CYCLES>=1&&GAP_CYCLES<=15);end
 logic [31:0] epoch,generation;logic [1:0] bank;logic [18:0] address;
 wire display_owned=owner==1,reference_owned=owner==2;
 wire response_match=mem_rsp_epoch==epoch&&mem_rsp_generation==generation&&mem_rsp_bank==bank&&mem_rsp_addr==address;
 assign mem_reset=(display_owned&&display_reset)||(reference_owned&&reference_reset);
 assign mem_cancel=(display_owned&&display_cancel)||(reference_owned&&reference_cancel);
 assign mem_req_valid=!accepted&&((display_owned&&display_req_valid&&!display_reset&&!display_cancel)||(reference_owned&&reference_eligible&&!group_killed));
 assign mem_req_epoch=display_owned?display_req_epoch:reference_req_epoch;
 assign mem_req_generation=display_owned?display_req_generation:reference_req_generation;
 assign mem_req_bank=display_owned?display_req_bank:reference_req_bank;
 assign mem_req_addr=display_owned?display_req_addr:reference_req_addr;
 assign display_req_ready=display_owned&&!accepted&&mem_req_ready&&!display_reset&&!display_cancel;
 assign reference_req_ready=reference_owned&&!accepted&&mem_req_ready&&reference_eligible&&!group_killed;
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
  if(power_on_reset)begin
   owner<=0;accepted<=0;last_reference<=1;epoch<=0;generation<=0;bank<=0;address<=0;
   grant_lines<=0;grant_gap<=0;grant_reserved<=0;group_valid<=0;group_killed<=0;
   response_seen<=0;response_failed<=0;group_base<=0;
   grant_groups<=0;grant_continuations<=0;grant_timeouts<=0;grant_mismatches<=0;
   grant_yields<=0;grant_cancel_yields<=0;grant_error_yields<=0;
  end else if(owner==0)begin
   accepted<=0;grant_reserved<=0;grant_gap<=0;grant_lines<=0;
   group_valid<=0;group_killed<=0;response_seen<=0;response_failed<=0;
   if(display_req_valid&&!display_reset&&!display_cancel&&(!reference_req_valid||reference_reset||reference_cancel||last_reference))begin owner<=1;last_reference<=0;end
   else if(reference_req_valid&&!reference_reset&&!reference_cancel)begin owner<=2;last_reference<=1;end
  end else begin
   if(reference_owned&&owned_kill)group_killed<=1;
   if(mem_req_valid&&mem_req_ready)begin
    accepted<=1;epoch<=mem_req_epoch;generation<=mem_req_generation;bank<=mem_req_bank;address<=mem_req_addr;
    response_seen<=0;response_failed<=0;grant_reserved<=0;grant_gap<=0;
    if(reference_owned)begin
     if(grant_reserved)grant_continuations<=grant_continuations+1;
     else begin
      group_valid<=REF_LINES>1&&first_group_legal;group_base<=reference_req_addr;
      if(REF_LINES>1&&first_group_legal)grant_groups<=grant_groups+1;
     end
    end
   end
   if(mem_rsp_valid&&mem_rsp_ready)begin
    response_seen<=1;response_failed<=mem_rsp_error;
    if(reference_owned&&!mem_rsp_error)grant_lines<=grant_lines+1'b1;
   end
   if(line_closed&&may_reserve&&yield_reason==0)begin
    accepted<=0;grant_reserved<=1;grant_gap<=0;
   end else if(grant_reserved&&!accepted&&!reference_req_valid&&!owned_kill)grant_gap<=grant_gap+1'b1;
   if(release_now)begin
    owner<=0;accepted<=0;grant_reserved<=0;grant_gap<=0;
    if(reference_owned)begin
     grant_yields<=grant_yields+1;
     if(yield_reason==1)grant_cancel_yields<=grant_cancel_yields+1;
     if(yield_reason==2)grant_error_yields<=grant_error_yields+1;
     if(yield_reason==3)grant_mismatches<=grant_mismatches+1;
     if(yield_reason==4)grant_timeouts<=grant_timeouts+1;
    end
   end
  end
 end
`ifndef SYNTHESIS
 logic [1:0] prior_owner=0;
 always_ff @(posedge clk)begin
  if(power_on_reset&&initialized)assert(!accepted)else $fatal(1,"cold reset while mux owns accepted line");
  if(!power_on_reset)begin
   assert(grant_lines<=3'(REF_LINES));
   if(line_closed)assert(response_seen)else $fatal(1,"physical bridge drained before owned response ACK");
   if(grant_reserved)assert(reference_owned&&!accepted&&group_valid&&grant_lines>0&&grant_lines<3'(REF_LINES));
   if(grant_reserved&&reference_req_valid&&!continuation_match)assert(!mem_req_valid&&!reference_req_ready);
   if(mem_req_valid&&mem_req_ready&&grant_reserved)assert(continuation_match);
   if(reference_owned&&mem_req_valid&&mem_req_ready&&!grant_reserved)$display("{\"type\":\"batch_start\",\"time_ps\":%0d,\"groupable\":%0d,\"limit\":%0d,\"epoch\":%0d,\"generation\":%0d,\"bank\":%0d,\"address\":%0d}",longint'($realtime*1000.0),REF_LINES>1&&first_group_legal,REF_LINES,mem_req_epoch,mem_req_generation,mem_req_bank,mem_req_addr);
   if(reference_owned&&mem_req_valid&&mem_req_ready&&grant_reserved)$display("{\"type\":\"batch_continue\",\"time_ps\":%0d,\"lines\":%0d,\"gap\":%0d,\"epoch\":%0d,\"generation\":%0d,\"bank\":%0d,\"address\":%0d}",longint'($realtime*1000.0),grant_lines,grant_gap,mem_req_epoch,mem_req_generation,mem_req_bank,mem_req_addr);
   if(grant_reserved&&!accepted)$display("{\"type\":\"batch_wait\",\"time_ps\":%0d,\"lines\":%0d,\"gap\":%0d,\"offer\":%0d,\"match\":%0d,\"ready\":%0d}",longint'($realtime*1000.0),grant_lines,grant_gap,reference_req_valid,continuation_match,mem_req_ready);
   if(reference_owned&&release_now)$display("{\"type\":\"batch_yield\",\"time_ps\":%0d,\"reason\":%0d,\"lines\":%0d,\"gap\":%0d,\"seen\":%0d,\"failed\":%0d,\"display_waiting\":%0d}",longint'($realtime*1000.0),yield_reason,grant_lines,grant_gap,response_seen,response_failed,display_req_valid&&!display_reset&&!display_cancel);
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
