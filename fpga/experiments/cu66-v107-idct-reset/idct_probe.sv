module idct_probe (
    input  logic clk,
    input  logic rst,
    input  logic abort_frame,
    input  logic in_valid,
    output logic in_ready,
    input  logic [31:0] in_id,
    input  logic [1279:0] in_tile,
    output logic out_valid,
    input  logic out_ready,
    output logic [31:0] out_id,
    output logic [1535:0] out_tile,
    output logic out_error,
    output logic [31:0] active_cycles,
    output logic [1279:0] verify_source_tile,
    output logic probe_equal,
    output logic [3:0] verify_state,
    output logic [2:0] verify_k,
    output logic [1:0] verify_group,
    output logic [303:0] verify_products,
    output logic [191:0] verify_samples,
    output logic [111:0] verify_basis
);
    logic [1279:0] old_verify_source_tile;
    logic  old_in_ready;
    logic  old_out_valid;
    logic [31:0] old_out_id;
    logic [1535:0] old_out_tile;
    logic  old_out_error;
    logic [31:0] old_active_cycles;
    logic [3:0] old_verify_state;
    logic [2:0] old_verify_k;
    logic [1:0] old_verify_group;
    logic [303:0] old_verify_products;
    logic [191:0] old_verify_samples;
    logic [111:0] old_verify_basis;
    idct_original original (
        .clk(clk),
        .rst(rst),
        .abort_frame(abort_frame),
        .in_valid(in_valid),
        .in_ready(old_in_ready),
        .in_id(in_id),
        .in_tile(in_tile),
        .out_valid(old_out_valid),
        .out_ready(out_ready),
        .out_id(old_out_id),
        .out_tile(old_out_tile),
        .out_error(old_out_error),
        .active_cycles(old_active_cycles),
        .verify_state(old_verify_state),
        .verify_k(old_verify_k),
        .verify_group(old_verify_group),
        .verify_products(old_verify_products),
        .verify_samples(old_verify_samples),
        .verify_basis(old_verify_basis),.verify_source_tile(old_verify_source_tile));
    idct_candidate candidate (
        .clk(clk),
        .rst(rst),
        .abort_frame(abort_frame),
        .in_valid(in_valid),
        .in_ready(in_ready),
        .in_id(in_id),
        .in_tile(in_tile),
        .out_valid(out_valid),
        .out_ready(out_ready),
        .out_id(out_id),
        .out_tile(out_tile),
        .out_error(out_error),
        .active_cycles(active_cycles),
        .verify_state(verify_state),
        .verify_k(verify_k),
        .verify_group(verify_group),
        .verify_products(verify_products),
        .verify_samples(verify_samples),
        .verify_basis(verify_basis),.verify_source_tile(verify_source_tile));
    assign probe_equal=((verify_state==0)||(old_verify_source_tile==verify_source_tile)) && (old_in_ready==in_ready) && (old_out_valid==out_valid) && (old_out_id==out_id) && (old_out_tile==out_tile) && (old_out_error==out_error) && (old_active_cycles==active_cycles) && (old_verify_state==verify_state) && (old_verify_k==verify_k) && (old_verify_group==verify_group) && (old_verify_products==verify_products) && (old_verify_samples==verify_samples) && (old_verify_basis==verify_basis);
endmodule
