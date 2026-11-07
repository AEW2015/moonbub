`timescale 1ns/1ps
`default_nettype none
// Immutable accepted display-bank lease. No pixel memory is added.
// Warm cancellation is a drain request; it never discards an accepted lease.
module display_overlap_lease(
 input logic clk,power_on_reset,reset,cancel,
 input logic start_valid,input logic [31:0] start_epoch,start_generation,
 input logic [1:0] start_bank,
 input logic accepted_valid,input logic [1:0] accepted_bank,
 input logic [31:0] accepted_fid,input logic [63:0] accepted_generation,
 input logic engine_start_ready,engine_busy,engine_draining,engine_done,
 input logic [7:0] engine_error,
 input logic reader_busy,reader_pending,input logic [1:0] mux_owner,
 input logic external_drained,candidate_valid,input logic [1:0] candidate_bank,
 output logic start_ready,engine_start,start_rejected,
 output logic active=0,draining,
 output logic [1:0] lease_bank=0,
 output logic [31:0] lease_epoch=0,lease_fid=0,
 output logic [63:0] lease_generation=0,
 output logic [7:0] terminal_error=0,
 output logic effective_drained,candidate_allowed,alias_fault,
 output logic [1:0] idle_samples=0,
 output logic terminal_seen=0
);
 logic initialized=0;
 wire kill=reset||cancel;
 wire descriptor_good=accepted_valid&&accepted_bank<3&&start_bank==accepted_bank&&
  start_epoch!=0&&accepted_generation!=0&&accepted_generation[63:32]==0&&
  start_generation==accepted_generation[31:0];
 wire engines_drained=!engine_busy&&!engine_draining&&!reader_busy&&!reader_pending&&mux_owner!=1;
 wire accept=start_valid&&start_ready;
 assign start_ready=!active&&engine_start_ready&&!kill&&!power_on_reset;
 assign engine_start=accept&&descriptor_good;
 assign start_rejected=accept&&!descriptor_good;
 assign draining=active&&terminal_seen;
 // Start on this edge already reserves the bank, before active is registered.
 assign candidate_allowed=!(active&&candidate_bank==lease_bank)&&
  !(engine_start&&candidate_bank==start_bank);
 assign alias_fault=candidate_valid&&!candidate_allowed;
 assign effective_drained=external_drained&&!active&&engines_drained&&!start_valid&&!power_on_reset;
 always_ff @(posedge clk)begin
  initialized<=1;
  if(power_on_reset)begin
   active<=0;lease_bank<=0;lease_epoch<=0;lease_fid<=0;lease_generation<=0;
   terminal_error<=0;terminal_seen<=0;idle_samples<=0;
  end else if(engine_start)begin
   active<=1;lease_bank<=accepted_bank;lease_epoch<=start_epoch;lease_fid<=accepted_fid;
   lease_generation<=accepted_generation;terminal_error<=0;terminal_seen<=0;idle_samples<=0;
  end else if(active)begin
   if(kill||engine_error!=0||engine_done)begin
    terminal_seen<=1;
    if(terminal_error==0)begin
     if(kill)terminal_error<=8'd2;
     else if(engine_error!=0)terminal_error<=engine_error;
    end
   end
   if((terminal_seen||kill||engine_error!=0||engine_done)&&engines_drained)begin
    if(idle_samples==1)begin active<=0;idle_samples<=0;end
    else idle_samples<=idle_samples+1'b1;
   end else idle_samples<=0;
  end else begin terminal_seen<=0;idle_samples<=0;end
 end
 always_ff @(posedge clk)begin
  if(power_on_reset&&initialized)assert(!active&&!reader_pending)else $fatal(1,"cold reset discards display lease");
  if(!power_on_reset)begin
   assert(idle_samples<=1);
   if(active)assert(lease_bank<3&&lease_epoch!=0&&lease_generation!=0&&lease_generation[63:32]==0);
   if(engine_start)assert(!active&&descriptor_good&&engine_start_ready);
   if(effective_drained)assert(!active&&!reader_busy&&!reader_pending&&!engine_busy&&!engine_draining&&mux_owner!=1&&!start_valid);
   if(alias_fault)assert(!candidate_allowed);
  end
 end
 assert property(@(posedge clk) !power_on_reset&&active |=> power_on_reset||$stable({lease_bank,lease_epoch,lease_fid,lease_generation}));
`ifdef SIMULATION
 integer receipt_cycle=0;
 logic previous_active=0,previous_terminal=0;
 always @(posedge clk)begin
  receipt_cycle<=receipt_cycle+1;
  if(!power_on_reset)begin
   if(accept)$display("{\"type\":\"lease_request\",\"cycle\":%0d,\"time_ps\":%0d,\"accepted\":%0d,\"rejected\":%0d,\"bank\":%0d,\"epoch\":%0d,\"generation32\":%0d,\"accepted_valid\":%0d,\"accepted_bank\":%0d,\"accepted_fid\":%0d,\"accepted_generation\":%0d}",receipt_cycle+1,longint'($realtime*1000.0),engine_start,start_rejected,start_bank,start_epoch,start_generation,accepted_valid,accepted_bank,accepted_fid,accepted_generation);
   if(active!=previous_active)$display("{\"type\":\"lease_owner\",\"cycle\":%0d,\"time_ps\":%0d,\"old_active\":%0d,\"active\":%0d,\"bank\":%0d,\"epoch\":%0d,\"fid\":%0d,\"generation\":%0d}",receipt_cycle+1,longint'($realtime*1000.0),previous_active,active,lease_bank,lease_epoch,lease_fid,lease_generation);
   if(active&&(terminal_seen!=previous_terminal||terminal_seen||kill||engine_done||engine_error!=0))$display("{\"type\":\"lease_fence\",\"cycle\":%0d,\"time_ps\":%0d,\"active\":%0d,\"terminal\":%0d,\"terminal_error\":%0d,\"reset\":%0d,\"cancel\":%0d,\"engine_done\":%0d,\"engine_error\":%0d,\"engine_busy\":%0d,\"engine_draining\":%0d,\"reader_busy\":%0d,\"reader_pending\":%0d,\"mux_owner\":%0d,\"idle_samples\":%0d}",receipt_cycle+1,longint'($realtime*1000.0),active,terminal_seen,terminal_error,reset,cancel,engine_done,engine_error,engine_busy,engine_draining,reader_busy,reader_pending,mux_owner,idle_samples);
   if(alias_fault)$display("{\"type\":\"lease_alias_block\",\"cycle\":%0d,\"time_ps\":%0d,\"candidate_bank\":%0d,\"lease_bank\":%0d,\"lease_active\":%0d,\"engine_start\":%0d}",receipt_cycle+1,longint'($realtime*1000.0),candidate_bank,lease_bank,active,engine_start);
  end
  previous_active<=active;previous_terminal<=terminal_seen;
 end
`endif
endmodule
`default_nettype wire
