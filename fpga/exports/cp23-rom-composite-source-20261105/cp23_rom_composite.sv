`timescale 1ns/1ps
`default_nettype none
// Fixed frame0 ROM -> real CP23/YUV/HUD -> physical storage/native LCD.
// Local diagnostics only: no CSR, external payload, transport or capabilities.
module cp23_rom_composite (
 input wire clk,read_clk,pixel_clk,reset,pixel_reset_n,
 input wire local_start,local_cancel,
 output wire loader_busy,local_start_accepted,local_start_rejected,
 output wire [31:0]rejected_starts,bytes_sent,
 output wire load_complete,loader_cancelled,
 output wire consumer_started_once,reconfigure_required,
 output wire bootstrap_released_pulse,consumer_job_released_pulse,
 output wire idle_certificate,
 output wire base_qualified,front_valid,
 output wire [31:0]promotion_count,lcd_underruns,
 output wire qualified_pulse,promoted_pulse,frame_boundary,
 output wire [7:0]red,green,blue,
 output wire hsync,vsync,data_enable,
 output wire [9:0]physical_x,physical_y,
 output wire [12:0]sdram_a,output wire [1:0]sdram_bs,
 inout wire [15:0]sdram_dq,
 output wire sdram_clk,output wire [1:0]sdram_cke,sdram_cs_n,
 output wire sdram_ras_n,sdram_cas_n,sdram_we_n,sdram_ldqm,sdram_udqm
);
 wire start_valid,start_ready,payload_valid,payload_ready,payload_last,abort_job;
 wire [7:0]payload_byte;
 wire loader_waiting_release,loader_released_pulse,loader_rejected;
 wire [31:0]loader_reject_count;
 wire core_released_pulse,job_active;

 // These are configuration-initialized state, deliberately NOT logical-reset
 // state. An accepted consumer job cannot be erased into a fresh bootstrap.
 reg ever_consumer_started_since_configuration=1'b0;
 reg configuration_required=1'b0;
 always @(posedge clk)begin
  if(start_valid&&start_ready)ever_consumer_started_since_configuration<=1'b1;
  // Strong conservative policy: ANY logical reset after accepted work requires
  // configuration. Reset may interrupt the memory interface; no warm proof.
  if(reset&&ever_consumer_started_since_configuration)configuration_required<=1'b1;
 end
 assign consumer_started_once=ever_consumer_started_since_configuration;
 assign reconfigure_required=configuration_required;

 reg release_seen=1'b0;
 always @(posedge clk)begin
  if(reset)release_seen<=0;
  else begin
   if(core_released_pulse)release_seen<=1;
   if(loader_released_pulse&&ever_consumer_started_since_configuration)release_seen<=0;
  end
 end
 // WAIT qualification creates a fresh edge per parked loader request. Only a
 // never-started configuration may bootstrap; after work, retain the actual
 // consumer release pulse until its positive idle certificate can be joined.
 wire consumer_released=!reset&&!configuration_required&&idle_certificate&&loader_waiting_release&&
                         (!ever_consumer_started_since_configuration||release_seen);
 wire permitted_start=local_start&&!ever_consumer_started_since_configuration&&!configuration_required;

 reg raw_start_seen;
 reg repeat_rejected;
 reg [31:0]repeat_reject_count;
 always @(posedge clk)begin
  if(reset)begin raw_start_seen<=local_start;repeat_rejected<=0;repeat_reject_count<=0;end
  else begin
   raw_start_seen<=local_start;repeat_rejected<=0;
   if(local_start&&!raw_start_seen&&(ever_consumer_started_since_configuration||configuration_required))begin
    repeat_rejected<=1;
    if(repeat_reject_count!=32'hffffffff)repeat_reject_count<=repeat_reject_count+1'b1;
   end
  end
 end
 wire [32:0]reject_sum={1'b0,loader_reject_count}+{1'b0,repeat_reject_count};
 assign rejected_starts=reject_sum[32]?32'hffffffff:reject_sum[31:0];
 assign local_start_rejected=loader_rejected||repeat_rejected;
 assign bootstrap_released_pulse=loader_released_pulse&&!ever_consumer_started_since_configuration&&!reset;
 // This is CONSUMER JOB retirement only. The immutable front bank remains
 // reserved for scanout; this signal is not a front-bank lease release.
 assign consumer_job_released_pulse=loader_released_pulse&&ever_consumer_started_since_configuration&&
                                    !reset&&!configuration_required;

 // The actual consumer accepts a cancellation pulse; a held abort keeps its
 // cancel_live priority asserted and cannot retire. Pulse the held loader
 // request once, while the loader's own fence remains latched until proof.
 reg abort_seen;
 always @(posedge clk)begin
  if(reset)abort_seen<=1'b1;
  else abort_seen<=abort_job;
 end
 wire core_abort_job=!reset&&job_active&&ever_consumer_started_since_configuration&&abort_job&&!abort_seen;

 cp23_fixed_rom_loader loader(.clk(clk),.reset(reset),.local_start(permitted_start),.local_cancel(local_cancel),
  .consumer_released(consumer_released),.start_valid(start_valid),.start_ready(start_ready),
  .payload_valid(payload_valid),.payload_ready(payload_ready),.payload_byte(payload_byte),.payload_last(payload_last),
  .abort_job(abort_job),.busy(loader_busy),.waiting_release(loader_waiting_release),
  .start_accepted(local_start_accepted),.start_rejected(loader_rejected),.released_pulse(loader_released_pulse),
  .consumer_started(),.load_complete(load_complete),.cancelled(loader_cancelled),
  .bytes_sent(bytes_sent),.rejected_starts(loader_reject_count));

 cp23_key_composite_scanout_local core(.clk(clk),.read_clk(read_clk),.pixel_clk(pixel_clk),.reset(reset),.pixel_reset_n(pixel_reset_n),
  .start_valid(start_valid),.start_ready(start_ready),.payload_valid(payload_valid),.payload_ready(payload_ready),
  .payload_byte(payload_byte),.payload_last(payload_last),.sample_enable(1'b1),.abort_job(core_abort_job),
  .base_qualified(base_qualified),.front_valid(front_valid),.promotion_count(promotion_count),
  .qualified_pulse(qualified_pulse),.promoted_pulse(promoted_pulse),.released_pulse(core_released_pulse),
  .job_active_out(job_active),.idle_certificate(idle_certificate),.lcd_underruns(lcd_underruns),.frame_boundary(frame_boundary),
  .red(red),.green(green),.blue(blue),.hsync(hsync),.vsync(vsync),.data_enable(data_enable),.physical_x(physical_x),.physical_y(physical_y),
  .sdram_a(sdram_a),.sdram_bs(sdram_bs),.sdram_dq(sdram_dq),.sdram_clk(sdram_clk),.sdram_cke(sdram_cke),.sdram_cs_n(sdram_cs_n),
  .sdram_ras_n(sdram_ras_n),.sdram_cas_n(sdram_cas_n),.sdram_we_n(sdram_we_n),.sdram_ldqm(sdram_ldqm),.sdram_udqm(sdram_udqm));
endmodule
`default_nettype wire
