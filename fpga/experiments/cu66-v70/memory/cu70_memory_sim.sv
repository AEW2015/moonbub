// Simulation-only combination of actualRTLmemorysystem andchecked32MiBcommandmodel.
`timescale 1ns/1ps
// Canonical tile + scalar auxiliary memory clients over real controller commands.
module cu70_memory_sim #(
 parameter integer POWERUP_CYCLES=20,REFRESH_CYCLES=750
)(
 input logic clk,read_clk,rst,abort_i,aux_abort_i,
 input logic read_valid,output logic read_ready,input logic [63:0] read_generation,
 input logic [1:0] read_bank,read_plane,input logic [16:0] read_index,
 output logic read_rsp_valid,input logic read_rsp_ready,output logic [63:0] read_rsp_generation,
 output logic [1:0] read_rsp_bank,read_rsp_plane,output logic [16:0] read_rsp_index,
 output logic [511:0] read_rsp_pixels,output logic read_rsp_error,
 input logic write_valid,output logic write_ready,input logic [63:0] write_generation,
 input logic [1:0] write_bank,write_plane,input logic [16:0] write_index,input logic [511:0] write_pixels,
 output logic write_done_valid,input logic write_done_ready,output logic [63:0] write_done_generation,
 output logic [1:0] write_done_bank,write_done_plane,output logic [16:0] write_done_index,output logic write_done_error,
 output logic tile_busy,tile_aborted,
 input logic aux_req_valid,output logic aux_req_ready,input logic aux_req_write,input logic [23:0] aux_req_addr,input logic [15:0] aux_req_data,
 output logic aux_rsp_valid,input logic aux_rsp_ready,output logic [15:0] aux_rsp_data,output logic aux_rsp_error,
 output logic aux_busy,aux_aborted,
 output logic [31:0] cache_hits,cache_misses,completed_reads,completed_writes,
 output logic[31:0] model_writes,model_reads,model_refreshes,model_acts,model_pres,
 output logic idle
);
 wire[12:0] sdram_a;wire[1:0] sdram_bs,sdram_cke,sdram_cs_n;wire[15:0] sdram_dq;
 wire sdram_clk,sdram_ras_n,sdram_cas_n,sdram_we_n,sdram_ldqm,sdram_udqm;
 cu70_memory_system #(.POWERUP_CYCLES(POWERUP_CYCLES),.REFRESH_CYCLES(REFRESH_CYCLES)) hardware(.*);
 cu70_sdram_model #(.REFRESH_CYCLES(REFRESH_CYCLES)) model(.reset(rst),.clk(sdram_clk),.a(sdram_a),.ba(sdram_bs),.cke(sdram_cke),.cs(sdram_cs_n),.ras(sdram_ras_n),.cas(sdram_cas_n),.we(sdram_we_n),.ldqm(sdram_ldqm),.udqm(sdram_udqm),.dq(sdram_dq));
 assign model_writes=32'(model.writes);assign model_reads=32'(model.reads);assign model_refreshes=32'(model.refreshes);
 assign model_acts=32'(model.acts);assign model_pres=32'(model.pres);
endmodule
