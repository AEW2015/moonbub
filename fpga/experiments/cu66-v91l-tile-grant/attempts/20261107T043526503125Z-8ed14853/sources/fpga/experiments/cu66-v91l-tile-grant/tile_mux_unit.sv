`timescale 1ns/1ps
`default_nettype none
module tile_mux_unit #(parameter integer REF_LINES=4,GAP_CYCLES=8)(
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
 tile_reader_mux #(.REF_LINES(REF_LINES),.GAP_CYCLES(GAP_CYCLES)) dut(
.clk(clk),
.power_on_reset(power_on_reset),
.owner(owner),
.display_reset(display_reset),
.display_cancel(display_cancel),
.display_req_valid(display_req_valid),
.display_rsp_ready(display_rsp_ready),
.display_req_ready(display_req_ready),
.display_rsp_valid(display_rsp_valid),
.display_rsp_error(display_rsp_error),
.display_req_epoch(display_req_epoch),
.display_req_generation(display_req_generation),
.display_req_bank(display_req_bank),
.display_req_addr(display_req_addr),
.display_rsp_epoch(display_rsp_epoch),
.display_rsp_generation(display_rsp_generation),
.display_rsp_bank(display_rsp_bank),
.display_rsp_addr(display_rsp_addr),
.display_rsp_data(display_rsp_data),
.reference_reset(reference_reset),
.reference_cancel(reference_cancel),
.reference_req_valid(reference_req_valid),
.reference_rsp_ready(reference_rsp_ready),
.reference_req_ready(reference_req_ready),
.reference_rsp_valid(reference_rsp_valid),
.reference_rsp_error(reference_rsp_error),
.reference_req_epoch(reference_req_epoch),
.reference_req_generation(reference_req_generation),
.reference_req_bank(reference_req_bank),
.reference_req_addr(reference_req_addr),
.reference_rsp_epoch(reference_rsp_epoch),
.reference_rsp_generation(reference_rsp_generation),
.reference_rsp_bank(reference_rsp_bank),
.reference_rsp_addr(reference_rsp_addr),
.reference_rsp_data(reference_rsp_data),
.mem_reset(mem_reset),
.mem_cancel(mem_cancel),
.mem_req_valid(mem_req_valid),
.mem_rsp_ready(mem_rsp_ready),
.mem_req_ready(mem_req_ready),
.mem_rsp_valid(mem_rsp_valid),
.mem_rsp_error(mem_rsp_error),
.mem_req_epoch(mem_req_epoch),
.mem_req_generation(mem_req_generation),
.mem_req_bank(mem_req_bank),
.mem_req_addr(mem_req_addr),
.mem_rsp_epoch(mem_rsp_epoch),
.mem_rsp_generation(mem_rsp_generation),
.mem_rsp_bank(mem_rsp_bank),
.mem_rsp_addr(mem_rsp_addr),
.mem_rsp_data(mem_rsp_data),
.mem_busy(mem_busy),
.grant_lines(grant_lines),
.grant_gap(grant_gap),
.grant_reserved(grant_reserved),
.grant_groups(grant_groups),
.grant_continuations(grant_continuations),
.grant_timeouts(grant_timeouts),
.grant_mismatches(grant_mismatches),
.grant_yields(grant_yields),
.grant_cancel_yields(grant_cancel_yields),
.grant_error_yields(grant_error_yields)
);
 generate if(REF_LINES==1)begin: exact_control
wire [1:0] old_owner;
wire  old_display_req_ready;
wire  old_display_rsp_valid;
wire  old_display_rsp_error;
wire [31:0] old_display_rsp_epoch;
wire [31:0] old_display_rsp_generation;
wire [1:0] old_display_rsp_bank;
wire [18:0] old_display_rsp_addr;
wire [127:0] old_display_rsp_data;
wire  old_reference_req_ready;
wire  old_reference_rsp_valid;
wire  old_reference_rsp_error;
wire [31:0] old_reference_rsp_epoch;
wire [31:0] old_reference_rsp_generation;
wire [1:0] old_reference_rsp_bank;
wire [18:0] old_reference_rsp_addr;
wire [127:0] old_reference_rsp_data;
wire  old_mem_reset;
wire  old_mem_cancel;
wire  old_mem_req_valid;
wire  old_mem_rsp_ready;
wire [31:0] old_mem_req_epoch;
wire [31:0] old_mem_req_generation;
wire [1:0] old_mem_req_bank;
wire [18:0] old_mem_req_addr;
reader_client_mux frozen(
.clk(clk),
.power_on_reset(power_on_reset),
.owner(old_owner),
.display_reset(display_reset),
.display_cancel(display_cancel),
.display_req_valid(display_req_valid),
.display_rsp_ready(display_rsp_ready),
.display_req_ready(old_display_req_ready),
.display_rsp_valid(old_display_rsp_valid),
.display_rsp_error(old_display_rsp_error),
.display_req_epoch(display_req_epoch),
.display_req_generation(display_req_generation),
.display_req_bank(display_req_bank),
.display_req_addr(display_req_addr),
.display_rsp_epoch(old_display_rsp_epoch),
.display_rsp_generation(old_display_rsp_generation),
.display_rsp_bank(old_display_rsp_bank),
.display_rsp_addr(old_display_rsp_addr),
.display_rsp_data(old_display_rsp_data),
.reference_reset(reference_reset),
.reference_cancel(reference_cancel),
.reference_req_valid(reference_req_valid),
.reference_rsp_ready(reference_rsp_ready),
.reference_req_ready(old_reference_req_ready),
.reference_rsp_valid(old_reference_rsp_valid),
.reference_rsp_error(old_reference_rsp_error),
.reference_req_epoch(reference_req_epoch),
.reference_req_generation(reference_req_generation),
.reference_req_bank(reference_req_bank),
.reference_req_addr(reference_req_addr),
.reference_rsp_epoch(old_reference_rsp_epoch),
.reference_rsp_generation(old_reference_rsp_generation),
.reference_rsp_bank(old_reference_rsp_bank),
.reference_rsp_addr(old_reference_rsp_addr),
.reference_rsp_data(old_reference_rsp_data),
.mem_reset(old_mem_reset),
.mem_cancel(old_mem_cancel),
.mem_req_valid(old_mem_req_valid),
.mem_rsp_ready(old_mem_rsp_ready),
.mem_req_ready(mem_req_ready),
.mem_rsp_valid(mem_rsp_valid),
.mem_rsp_error(mem_rsp_error),
.mem_req_epoch(old_mem_req_epoch),
.mem_req_generation(old_mem_req_generation),
.mem_req_bank(old_mem_req_bank),
.mem_req_addr(old_mem_req_addr),
.mem_rsp_epoch(mem_rsp_epoch),
.mem_rsp_generation(mem_rsp_generation),
.mem_rsp_bank(mem_rsp_bank),
.mem_rsp_addr(mem_rsp_addr),
.mem_rsp_data(mem_rsp_data),
.mem_busy(mem_busy)
);
always_ff @(posedge clk)if(!power_on_reset)begin
assert(owner==old_owner)else $fatal(1,"REF_LINES1 differs: owner");
assert(display_req_ready==old_display_req_ready)else $fatal(1,"REF_LINES1 differs: display_req_ready");
assert(display_rsp_valid==old_display_rsp_valid)else $fatal(1,"REF_LINES1 differs: display_rsp_valid");
assert(display_rsp_error==old_display_rsp_error)else $fatal(1,"REF_LINES1 differs: display_rsp_error");
assert(display_rsp_epoch==old_display_rsp_epoch)else $fatal(1,"REF_LINES1 differs: display_rsp_epoch");
assert(display_rsp_generation==old_display_rsp_generation)else $fatal(1,"REF_LINES1 differs: display_rsp_generation");
assert(display_rsp_bank==old_display_rsp_bank)else $fatal(1,"REF_LINES1 differs: display_rsp_bank");
assert(display_rsp_addr==old_display_rsp_addr)else $fatal(1,"REF_LINES1 differs: display_rsp_addr");
assert(display_rsp_data==old_display_rsp_data)else $fatal(1,"REF_LINES1 differs: display_rsp_data");
assert(reference_req_ready==old_reference_req_ready)else $fatal(1,"REF_LINES1 differs: reference_req_ready");
assert(reference_rsp_valid==old_reference_rsp_valid)else $fatal(1,"REF_LINES1 differs: reference_rsp_valid");
assert(reference_rsp_error==old_reference_rsp_error)else $fatal(1,"REF_LINES1 differs: reference_rsp_error");
assert(reference_rsp_epoch==old_reference_rsp_epoch)else $fatal(1,"REF_LINES1 differs: reference_rsp_epoch");
assert(reference_rsp_generation==old_reference_rsp_generation)else $fatal(1,"REF_LINES1 differs: reference_rsp_generation");
assert(reference_rsp_bank==old_reference_rsp_bank)else $fatal(1,"REF_LINES1 differs: reference_rsp_bank");
assert(reference_rsp_addr==old_reference_rsp_addr)else $fatal(1,"REF_LINES1 differs: reference_rsp_addr");
assert(reference_rsp_data==old_reference_rsp_data)else $fatal(1,"REF_LINES1 differs: reference_rsp_data");
assert(mem_reset==old_mem_reset)else $fatal(1,"REF_LINES1 differs: mem_reset");
assert(mem_cancel==old_mem_cancel)else $fatal(1,"REF_LINES1 differs: mem_cancel");
assert(mem_req_valid==old_mem_req_valid)else $fatal(1,"REF_LINES1 differs: mem_req_valid");
assert(mem_rsp_ready==old_mem_rsp_ready)else $fatal(1,"REF_LINES1 differs: mem_rsp_ready");
assert(mem_req_epoch==old_mem_req_epoch)else $fatal(1,"REF_LINES1 differs: mem_req_epoch");
assert(mem_req_generation==old_mem_req_generation)else $fatal(1,"REF_LINES1 differs: mem_req_generation");
assert(mem_req_bank==old_mem_req_bank)else $fatal(1,"REF_LINES1 differs: mem_req_bank");
assert(mem_req_addr==old_mem_req_addr)else $fatal(1,"REF_LINES1 differs: mem_req_addr");
end
end endgenerate
endmodule
`default_nettype wire
