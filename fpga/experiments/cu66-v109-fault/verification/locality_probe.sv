// Two coefficient-tile owners around the frozen dequantizer and Q14 inverse.
// Output is a provisional signed residual, never a published pixel frame.
module locality_probe (
    input logic clk, reset, start, cancel, input_done,
    input logic in_valid,
    output logic in_ready,
    input logic [31:0] in_epoch, in_child_epoch,
    input logic [1:0] in_plane, in_qscale,
    input logic [15:0] in_block,
    input logic [12:0] in_tile,
    input logic [10:0] in_qcell,
    input logic [5:0] in_index,
    input logic signed [15:0] in_value,
    output logic out_valid,
    input logic out_ready,
    output logic [31:0] out_epoch, out_child_epoch, out_token,
    output logic [1:0] out_plane, out_qscale,
    output logic [15:0] out_block,
    output logic [12:0] out_tile,
    output logic [10:0] out_qcell,
    output logic [5:0] out_index,
    output logic signed [23:0] out_value,
    output logic busy, done,
    output logic [7:0] error,
    output logic [1:0] bank_state [0:1],
    output logic fill_bank, math_bank,
    output logic [2:0] math_state,
    output logic [1:0] owned_banks, max_owned_banks,
    output logic dbg_launch, dbg_dequant,
    output logic [31:0] dbg_token,
    output logic [1023:0] dbg_coefficients,
    output logic [1279:0] dbg_dequantized,
    output logic [31:0] dbg_epoch, dbg_child_epoch,
    output logic [1:0] dbg_plane, dbg_qscale,
    output logic [15:0] dbg_block,
    output logic [12:0] dbg_tile,
    output logic [10:0] dbg_qcell,
    output logic [63:0] count_inputs, count_tiles, count_launches,
    output logic [63:0] count_dequant, count_outputs, count_completed_tiles,
    output logic [63:0] count_input_stalls, count_output_stalls,
    output logic [63:0] count_cancelled_banks
, input logic verify_metadata_bad, verify_domain_bad, output logic probe_outputs_equal, probe_stores_equal, probe_state_equal, output logic [1023:0] probe_store0, probe_store1, output logic [5:0] probe_fill_index, output logic [31:0] probe_next_token, output logic [7:0] probe_fault, output logic probe_fault_equal);
logic  old_in_ready;
logic  old_out_valid;
logic [31:0]  old_out_epoch;
logic [31:0]  old_out_child_epoch;
logic [31:0]  old_out_token;
logic [1:0]  old_out_plane;
logic [1:0]  old_out_qscale;
logic [15:0]  old_out_block;
logic [12:0]  old_out_tile;
logic [10:0]  old_out_qcell;
logic [5:0]  old_out_index;
logic signed [23:0]  old_out_value;
logic  old_busy;
logic  old_done;
logic [7:0]  old_error;
logic [1:0]  old_bank_state[0:1];
logic  old_fill_bank;
logic  old_math_bank;
logic [2:0]  old_math_state;
logic [1:0]  old_owned_banks;
logic [1:0]  old_max_owned_banks;
logic  old_dbg_launch;
logic  old_dbg_dequant;
logic [31:0]  old_dbg_token;
logic [1023:0]  old_dbg_coefficients;
logic [1279:0]  old_dbg_dequantized;
logic [31:0]  old_dbg_epoch;
logic [31:0]  old_dbg_child_epoch;
logic [1:0]  old_dbg_plane;
logic [1:0]  old_dbg_qscale;
logic [15:0]  old_dbg_block;
logic [12:0]  old_dbg_tile;
logic [10:0]  old_dbg_qcell;
logic [63:0]  old_count_inputs;
logic [63:0]  old_count_tiles;
logic [63:0]  old_count_launches;
logic [63:0]  old_count_dequant;
logic [63:0]  old_count_outputs;
logic [63:0]  old_count_completed_tiles;
logic [63:0]  old_count_input_stalls;
logic [63:0]  old_count_output_stalls;
logic [63:0]  old_count_cancelled_banks;
logic old_fault,new_fault;
assign probe_fault_equal=(old_fault==new_fault);
locality_original old_dut(.in_metadata_bad(verify_metadata_bad),.in_domain_bad(verify_domain_bad),.fault_o(old_fault),.clk(clk),.reset(reset),.start(start),.cancel(cancel),.input_done(input_done),.in_valid(in_valid),.in_ready(old_in_ready),.in_epoch(in_epoch),.in_child_epoch(in_child_epoch),.in_plane(in_plane),.in_qscale(in_qscale),.in_block(in_block),.in_tile(in_tile),.in_qcell(in_qcell),.in_index(in_index),.in_value(in_value),.out_valid(old_out_valid),.out_ready(out_ready),.out_epoch(old_out_epoch),.out_child_epoch(old_out_child_epoch),.out_token(old_out_token),.out_plane(old_out_plane),.out_qscale(old_out_qscale),.out_block(old_out_block),.out_tile(old_out_tile),.out_qcell(old_out_qcell),.out_index(old_out_index),.out_value(old_out_value),.busy(old_busy),.done(old_done),.error(old_error),.bank_state(old_bank_state),.fill_bank(old_fill_bank),.math_bank(old_math_bank),.math_state(old_math_state),.owned_banks(old_owned_banks),.max_owned_banks(old_max_owned_banks),.dbg_launch(old_dbg_launch),.dbg_dequant(old_dbg_dequant),.dbg_token(old_dbg_token),.dbg_coefficients(old_dbg_coefficients),.dbg_dequantized(old_dbg_dequantized),.dbg_epoch(old_dbg_epoch),.dbg_child_epoch(old_dbg_child_epoch),.dbg_plane(old_dbg_plane),.dbg_qscale(old_dbg_qscale),.dbg_block(old_dbg_block),.dbg_tile(old_dbg_tile),.dbg_qcell(old_dbg_qcell),.count_inputs(old_count_inputs),.count_tiles(old_count_tiles),.count_launches(old_count_launches),.count_dequant(old_count_dequant),.count_outputs(old_count_outputs),.count_completed_tiles(old_count_completed_tiles),.count_input_stalls(old_count_input_stalls),.count_output_stalls(old_count_output_stalls),.count_cancelled_banks(old_count_cancelled_banks));
locality_candidate new_dut(.fault_o(new_fault),.clk(clk),.reset(reset),.start(start),.cancel(cancel),.input_done(input_done),.in_valid(in_valid),.in_ready(in_ready),.in_epoch(in_epoch),.in_child_epoch(in_child_epoch),.in_plane(in_plane),.in_qscale(in_qscale),.in_block(in_block),.in_tile(in_tile),.in_qcell(in_qcell),.in_index(in_index),.in_value(in_value),.out_valid(out_valid),.out_ready(out_ready),.out_epoch(out_epoch),.out_child_epoch(out_child_epoch),.out_token(out_token),.out_plane(out_plane),.out_qscale(out_qscale),.out_block(out_block),.out_tile(out_tile),.out_qcell(out_qcell),.out_index(out_index),.out_value(out_value),.busy(busy),.done(done),.error(error),.bank_state(bank_state),.fill_bank(fill_bank),.math_bank(math_bank),.math_state(math_state),.owned_banks(owned_banks),.max_owned_banks(max_owned_banks),.dbg_launch(dbg_launch),.dbg_dequant(dbg_dequant),.dbg_token(dbg_token),.dbg_coefficients(dbg_coefficients),.dbg_dequantized(dbg_dequantized),.dbg_epoch(dbg_epoch),.dbg_child_epoch(dbg_child_epoch),.dbg_plane(dbg_plane),.dbg_qscale(dbg_qscale),.dbg_block(dbg_block),.dbg_tile(dbg_tile),.dbg_qcell(dbg_qcell),.count_inputs(count_inputs),.count_tiles(count_tiles),.count_launches(count_launches),.count_dequant(count_dequant),.count_outputs(count_outputs),.count_completed_tiles(count_completed_tiles),.count_input_stalls(count_input_stalls),.count_output_stalls(count_output_stalls),.count_cancelled_banks(count_cancelled_banks),.in_metadata_bad(verify_metadata_bad),.in_domain_bad(verify_domain_bad));
assign probe_outputs_equal = (old_in_ready == in_ready) && (old_out_valid == out_valid) && (old_out_epoch == out_epoch) && (old_out_child_epoch == out_child_epoch) && (old_out_token == out_token) && (old_out_plane == out_plane) && (old_out_qscale == out_qscale) && (old_out_block == out_block) && (old_out_tile == out_tile) && (old_out_qcell == out_qcell) && (old_out_index == out_index) && (old_out_value == out_value) && (old_busy == busy) && (old_done == done) && (old_error == error) && (old_bank_state == bank_state) && (old_fill_bank == fill_bank) && (old_math_bank == math_bank) && (old_math_state == math_state) && (old_owned_banks == owned_banks) && (old_max_owned_banks == max_owned_banks) && (old_dbg_launch == dbg_launch) && (old_dbg_dequant == dbg_dequant) && (old_dbg_token == dbg_token) && (old_dbg_coefficients == dbg_coefficients) && (old_dbg_dequantized == dbg_dequantized) && (old_dbg_epoch == dbg_epoch) && (old_dbg_child_epoch == dbg_child_epoch) && (old_dbg_plane == dbg_plane) && (old_dbg_qscale == dbg_qscale) && (old_dbg_block == dbg_block) && (old_dbg_tile == dbg_tile) && (old_dbg_qcell == dbg_qcell) && (old_count_inputs == count_inputs) && (old_count_tiles == count_tiles) && (old_count_launches == count_launches) && (old_count_dequant == count_dequant) && (old_count_outputs == count_outputs) && (old_count_completed_tiles == count_completed_tiles) && (old_count_input_stalls == count_input_stalls) && (old_count_output_stalls == count_output_stalls) && (old_count_cancelled_banks == count_cancelled_banks);
assign probe_state_equal = (old_dut.running == new_dut.running) && (old_dut.finished_input == new_dut.finished_input) && (old_dut.fill_index == new_dut.fill_index) && (old_dut.emit_index == new_dut.emit_index) && (old_dut.next_token == new_dut.next_token) && (old_dut.epochs == new_dut.epochs) && (old_dut.child_epochs == new_dut.child_epochs) && (old_dut.tokens == new_dut.tokens) && (old_dut.planes == new_dut.planes) && (old_dut.scales == new_dut.scales) && (old_dut.blocks == new_dut.blocks) && (old_dut.tiles == new_dut.tiles) && (old_dut.cells == new_dut.cells) && (old_dut.input_metadata_bad == new_dut.input_metadata_bad) && (old_dut.input_fault == new_dut.input_fault) && (old_dut.dq_ready == new_dut.dq_ready) && (old_dut.dq_valid == new_dut.dq_valid) && (old_dut.dq_out_ready == new_dut.dq_out_ready) && (old_dut.dq_error == new_dut.dq_error) && (old_dut.dq_id == new_dut.dq_id) && (old_dut.dq_data == new_dut.dq_data) && (old_dut.idct_ready == new_dut.idct_ready) && (old_dut.idct_valid == new_dut.idct_valid) && (old_dut.idct_out_ready == new_dut.idct_out_ready) && (old_dut.idct_error == new_dut.idct_error) && (old_dut.idct_id == new_dut.idct_id) && (old_dut.idct_data == new_dut.idct_data) && (old_dut.unused_idct_cycles == new_dut.unused_idct_cycles);
assign probe_store0=new_dut.coefficients[0]; assign probe_store1=new_dut.coefficients[1];
assign probe_stores_equal=(old_dut.coefficients[0]==new_dut.coefficients[0])&&(old_dut.coefficients[1]==new_dut.coefficients[1]);
assign probe_fill_index=new_dut.fill_index; assign probe_next_token=new_dut.next_token; assign probe_fault=new_dut.input_fault;
endmodule
