// Two coefficient-tile owners around the frozen dequantizer and Q14 inverse.
// Output is a provisional signed residual, never a published pixel frame.
module cu66_inverse_stream_v91j (
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
    input logic in_metadata_bad, in_domain_bad,
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
);
    localparam logic [1:0] FREE=0, FILL=1, READY=2, ACTIVE=3;
    localparam logic [2:0] M_IDLE=0, M_DQ_SEND=1, M_DQ_WAIT=2,
        M_IDCT_WAIT=3, M_EMIT=4;
    logic running, finished_input, kill;
    logic [1023:0] coefficients [0:1];
    logic [31:0] epochs [0:1], child_epochs [0:1], tokens [0:1];
    logic [1:0] planes [0:1], scales [0:1];
    logic [15:0] blocks [0:1];
    logic [12:0] tiles [0:1];
    logic [10:0] cells [0:1];
    logic [5:0] fill_index, emit_index;
    logic [31:0] next_token;
    logic dq_ready, dq_valid, dq_out_ready, dq_error;
    logic [31:0] dq_id;
    logic [1279:0] dq_data;
    logic idct_ready, idct_valid, idct_out_ready, idct_error;
    logic [31:0] idct_id;
    logic [1535:0] idct_data;
    logic [31:0] unused_idct_cycles;
    logic input_metadata_bad;
    logic [7:0] input_fault;

    function automatic logic [10:0] quant_cell(input logic [1:0] p,input logic [12:0] t);
        // Exact combinational Y truth table: paired tiles share a cell (90 is even).
        // 64 banks of LUT6-sized bit tables; native mapping/area are measured separately.
        logic [63:0] lut0;
        logic [63:0] lut1;
        logic [63:0] lut2;
        logic [63:0] lut3;
        logic [63:0] lut4;
        logic [63:0] lut5;
        logic [63:0] lut6;
        logic [63:0] lut7;
        logic [63:0] lut8;
        logic [63:0] lut9;
        logic [63:0] lut10;
        begin
            case(t[12:7])
                6'd0:begin
                    lut0=64'h55554aaaaaaaaaaa;
                    lut1=64'h99998ccccccccccc;
                    lut2=64'h1e1e10f0f0f0f0f0;
                    lut3=64'h1fe01f00ff00ff00;
                    lut4=64'he0000000ffff0000;
                    lut5=64'h00001fff00000000;
                    lut6=64'h0000000000000000;
                    lut7=64'h0000000000000000;
                    lut8=64'h0000000000000000;
                    lut9=64'h0000000000000000;
                    lut10=64'h0000000000000000;
                end
                6'd1:begin
                    lut0=64'h5555555555555555;
                    lut1=64'h9999999999999999;
                    lut2=64'h1e1e1e1e1e1e1e1e;
                    lut3=64'h1fe01fe01fe01fe0;
                    lut4=64'he0001fffe0001fff;
                    lut5=64'h00001fffffffe000;
                    lut6=64'hffffe00000000000;
                    lut7=64'h0000000000000000;
                    lut8=64'h0000000000000000;
                    lut9=64'h0000000000000000;
                    lut10=64'h0000000000000000;
                end
                6'd2:begin
                    lut0=64'haaaaaaaaaaaaaad5;
                    lut1=64'h3333333333333319;
                    lut2=64'hc3c3c3c3c3c3c39e;
                    lut3=64'h03fc03fc03fc03e0;
                    lut4=64'h03fffc0003fffc7f;
                    lut5=64'hfc00000003ffff80;
                    lut6=64'hfffffffffc00007f;
                    lut7=64'h0000000000000000;
                    lut8=64'h0000000000000000;
                    lut9=64'h0000000000000000;
                    lut10=64'h0000000000000000;
                end
                6'd3:begin
                    lut0=64'h55555554aaaaaaaa;
                    lut1=64'h6666666733333333;
                    lut2=64'h78787879c3c3c3c3;
                    lut3=64'h807f807e03fc03fc;
                    lut4=64'hff80007e03fffc00;
                    lut5=64'hffffff8003ffffff;
                    lut6=64'hfffffffe03ffffff;
                    lut7=64'h00000001fc000000;
                    lut8=64'h0000000000000000;
                    lut9=64'h0000000000000000;
                    lut10=64'h0000000000000000;
                end
                6'd4:begin
                    lut0=64'had55555555555555;
                    lut1=64'hce66666666666666;
                    lut2=64'h0878787878787878;
                    lut3=64'hf07f807f807f807f;
                    lut4=64'h0780007fff80007f;
                    lut5=64'h07ffff800000007f;
                    lut6=64'h000000000000007f;
                    lut7=64'hffffffffffffff80;
                    lut8=64'h0000000000000000;
                    lut9=64'h0000000000000000;
                    lut10=64'h0000000000000000;
                end
                6'd5:begin
                    lut0=64'haaaaaaaaaaaaaaaa;
                    lut1=64'hcccccccccccccccc;
                    lut2=64'h0f0f0f0f0f0f0f0f;
                    lut3=64'hf00ff00ff00ff00f;
                    lut4=64'h000ffff0000ffff0;
                    lut5=64'h000ffffffff00000;
                    lut6=64'hfff0000000000000;
                    lut7=64'hffffffffffffffff;
                    lut8=64'h0000000000000000;
                    lut9=64'h0000000000000000;
                    lut10=64'h0000000000000000;
                end
                6'd6:begin
                    lut0=64'h55555555554aaaaa;
                    lut1=64'h99999999998ccccc;
                    lut2=64'he1e1e1e1e1ef0f0f;
                    lut3=64'hfe01fe01fe0ff00f;
                    lut4=64'hfffe0001ffeffff0;
                    lut5=64'h00000001fff00000;
                    lut6=64'hfffffffe001fffff;
                    lut7=64'hffffffffffffffff;
                    lut8=64'h0000000000000000;
                    lut9=64'h0000000000000000;
                    lut10=64'h0000000000000000;
                end
                6'd7:begin
                    lut0=64'haaaad55555555555;
                    lut1=64'h3333199999999999;
                    lut2=64'h3c3c61e1e1e1e1e1;
                    lut3=64'h3fc07e01fe01fe01;
                    lut4=64'hc0000001fffe0001;
                    lut5=64'hffff8001fffffffe;
                    lut6=64'hffff8001ffffffff;
                    lut7=64'hffff8001ffffffff;
                    lut8=64'h00007ffe00000000;
                    lut9=64'h0000000000000000;
                    lut10=64'h0000000000000000;
                end
                6'd8:begin
                    lut0=64'haaaaaaaaaaaaaaaa;
                    lut1=64'h3333333333333333;
                    lut2=64'h3c3c3c3c3c3c3c3c;
                    lut3=64'h3fc03fc03fc03fc0;
                    lut4=64'hc0003fffc0003fff;
                    lut5=64'hffffc00000003fff;
                    lut6=64'h0000000000003fff;
                    lut7=64'h0000000000003fff;
                    lut8=64'hffffffffffffc000;
                    lut9=64'h0000000000000000;
                    lut10=64'h0000000000000000;
                end
                6'd9:begin
                    lut0=64'h55555555555554aa;
                    lut1=64'h6666666666666733;
                    lut2=64'h878787878787863c;
                    lut3=64'h07f807f807f807c0;
                    lut4=64'h07fff80007fff9ff;
                    lut5=64'h07fffffff80001ff;
                    lut6=64'hf800000000000000;
                    lut7=64'h0000000000000000;
                    lut8=64'hffffffffffffffff;
                    lut9=64'h0000000000000000;
                    lut10=64'h0000000000000000;
                end
                6'd10:begin
                    lut0=64'haaaaaaad55555555;
                    lut1=64'hccccccce66666666;
                    lut2=64'hf0f0f0f787878787;
                    lut3=64'h00ff00f807f807f8;
                    lut4=64'hff0000f807fff800;
                    lut5=64'h000000fff8000000;
                    lut6=64'hffffff07ffffffff;
                    lut7=64'h0000000000000000;
                    lut8=64'hffffffffffffffff;
                    lut9=64'h0000000000000000;
                    lut10=64'h0000000000000000;
                end
                6'd11:begin
                    lut0=64'h4aaaaaaaaaaaaaaa;
                    lut1=64'h8ccccccccccccccc;
                    lut2=64'h10f0f0f0f0f0f0f0;
                    lut3=64'he0ff00ff00ff00ff;
                    lut4=64'h1f0000ffff0000ff;
                    lut5=64'he00000ffffffff00;
                    lut6=64'he00000ffffffffff;
                    lut7=64'h1fffff0000000000;
                    lut8=64'hffffffffffffffff;
                    lut9=64'h0000000000000000;
                    lut10=64'h0000000000000000;
                end
                6'd12:begin
                    lut0=64'h5555555555555555;
                    lut1=64'h9999999999999999;
                    lut2=64'h1e1e1e1e1e1e1e1e;
                    lut3=64'he01fe01fe01fe01f;
                    lut4=64'h001fffe0001fffe0;
                    lut5=64'hffe00000001fffff;
                    lut6=64'h00000000001fffff;
                    lut7=64'hffffffffffe00000;
                    lut8=64'hffffffffffffffff;
                    lut9=64'h0000000000000000;
                    lut10=64'h0000000000000000;
                end
                6'd13:begin
                    lut0=64'haaaaaaaaaad55555;
                    lut1=64'h3333333333199999;
                    lut2=64'hc3c3c3c3c39e1e1e;
                    lut3=64'hfc03fc03fc1fe01f;
                    lut4=64'hfffc0003ff9fffe0;
                    lut5=64'hfffffffc001fffff;
                    lut6=64'h0000000000600000;
                    lut7=64'hffffffffffffffff;
                    lut8=64'hffffffffffffffff;
                    lut9=64'h0000000000000000;
                    lut10=64'h0000000000000000;
                end
                6'd14:begin
                    lut0=64'h5554aaaaaaaaaaaa;
                    lut1=64'h6667333333333333;
                    lut2=64'h7879c3c3c3c3c3c3;
                    lut3=64'h7f81fc03fc03fc03;
                    lut4=64'h80000003fffc0003;
                    lut5=64'h0001fffc00000003;
                    lut6=64'hfffffffffffffffc;
                    lut7=64'hffffffffffffffff;
                    lut8=64'hffffffffffffffff;
                    lut9=64'h0000000000000000;
                    lut10=64'h0000000000000000;
                end
                6'd15:begin
                    lut0=64'h5555555555555555;
                    lut1=64'h6666666666666666;
                    lut2=64'h7878787878787878;
                    lut3=64'h7f807f807f807f80;
                    lut4=64'h80007fff80007fff;
                    lut5=64'h00007fffffff8000;
                    lut6=64'h00007fffffffffff;
                    lut7=64'h00007fffffffffff;
                    lut8=64'h00007fffffffffff;
                    lut9=64'hffff800000000000;
                    lut10=64'h0000000000000000;
                end
                6'd16:begin
                    lut0=64'haaaaaaaaaaaaad55;
                    lut1=64'hccccccccccccce66;
                    lut2=64'h0f0f0f0f0f0f0878;
                    lut3=64'h0ff00ff00ff00f80;
                    lut4=64'h0ffff0000ffff7ff;
                    lut5=64'hf00000000ffff800;
                    lut6=64'h000000000ffff800;
                    lut7=64'h000000000ffff800;
                    lut8=64'h000000000ffff800;
                    lut9=64'hfffffffff00007ff;
                    lut10=64'h0000000000000000;
                end
                6'd17:begin
                    lut0=64'h5555554aaaaaaaaa;
                    lut1=64'h9999998ccccccccc;
                    lut2=64'he1e1e1ef0f0f0f0f;
                    lut3=64'h01fe01f00ff00ff0;
                    lut4=64'hfe0001e00ffff000;
                    lut5=64'hfffffe000fffffff;
                    lut6=64'h0000001ff0000000;
                    lut7=64'h0000000000000000;
                    lut8=64'h0000000000000000;
                    lut9=64'hffffffffffffffff;
                    lut10=64'h0000000000000000;
                end
                6'd18:begin
                    lut0=64'hd555555555555555;
                    lut1=64'h1999999999999999;
                    lut2=64'h61e1e1e1e1e1e1e1;
                    lut3=64'h81fe01fe01fe01fe;
                    lut4=64'h7e0001fffe0001ff;
                    lut5=64'h7ffffe00000001ff;
                    lut6=64'hfffffffffffffe00;
                    lut7=64'h0000000000000000;
                    lut8=64'h0000000000000000;
                    lut9=64'hffffffffffffffff;
                    lut10=64'h0000000000000000;
                end
                6'd19:begin
                    lut0=64'haaaaaaaaaaaaaaaa;
                    lut1=64'h3333333333333333;
                    lut2=64'h3c3c3c3c3c3c3c3c;
                    lut3=64'hc03fc03fc03fc03f;
                    lut4=64'h003fffc0003fffc0;
                    lut5=64'h003fffffffc00000;
                    lut6=64'h003fffffffffffff;
                    lut7=64'hffc0000000000000;
                    lut8=64'h0000000000000000;
                    lut9=64'hffffffffffffffff;
                    lut10=64'h0000000000000000;
                end
                6'd20:begin
                    lut0=64'h5555555554aaaaaa;
                    lut1=64'h6666666667333333;
                    lut2=64'h87878787863c3c3c;
                    lut3=64'hf807f807f83fc03f;
                    lut4=64'hfff80007fe3fffc0;
                    lut5=64'h00000007ffc00000;
                    lut6=64'h00000007fe000000;
                    lut7=64'hfffffff801ffffff;
                    lut8=64'h0000000000000000;
                    lut9=64'hffffffffffffffff;
                    lut10=64'h0000000000000000;
                end
                6'd21:begin
                    lut0=64'haaad555555555555;
                    lut1=64'hccce666666666666;
                    lut2=64'hf0f7878787878787;
                    lut3=64'hff07f807f807f807;
                    lut4=64'h00000007fff80007;
                    lut5=64'hfff80007fffffff8;
                    lut6=64'h0007fff800000000;
                    lut7=64'hffffffffffffffff;
                    lut8=64'h0000000000000000;
                    lut9=64'hffffffffffffffff;
                    lut10=64'h0000000000000000;
                end
                6'd22:begin
                    lut0=64'haaaaaaaaaaaaaaaa;
                    lut1=64'hcccccccccccccccc;
                    lut2=64'hf0f0f0f0f0f0f0f0;
                    lut3=64'hff00ff00ff00ff00;
                    lut4=64'h0000ffff0000ffff;
                    lut5=64'hffff00000000ffff;
                    lut6=64'hffffffffffff0000;
                    lut7=64'hffffffffffffffff;
                    lut8=64'h0000000000000000;
                    lut9=64'hffffffffffffffff;
                    lut10=64'h0000000000000000;
                end
                6'd23:begin
                    lut0=64'h5555555555554aaa;
                    lut1=64'h9999999999998ccc;
                    lut2=64'h1e1e1e1e1e1e10f0;
                    lut3=64'h1fe01fe01fe01f00;
                    lut4=64'h1fffe0001fffffff;
                    lut5=64'h1fffffffe0001fff;
                    lut6=64'h1fffffffffffffff;
                    lut7=64'h1fffffffffffffff;
                    lut8=64'he000000000000000;
                    lut9=64'hffffffffffffffff;
                    lut10=64'h0000000000000000;
                end
                6'd24:begin
                    lut0=64'haaaaaad555555555;
                    lut1=64'h3333331999999999;
                    lut2=64'hc3c3c39e1e1e1e1e;
                    lut3=64'h03fc03e01fe01fe0;
                    lut4=64'hfc0003801fffe000;
                    lut5=64'h000003ffe0000000;
                    lut6=64'h0000038000000000;
                    lut7=64'h0000038000000000;
                    lut8=64'hfffffc7fffffffff;
                    lut9=64'hffffffffffffffff;
                    lut10=64'h0000000000000000;
                end
                6'd25:begin
                    lut0=64'haaaaaaaaaaaaaaaa;
                    lut1=64'h3333333333333333;
                    lut2=64'hc3c3c3c3c3c3c3c3;
                    lut3=64'h03fc03fc03fc03fc;
                    lut4=64'hfc0003fffc0003ff;
                    lut5=64'h000003fffffffc00;
                    lut6=64'hfffffc0000000000;
                    lut7=64'h0000000000000000;
                    lut8=64'hffffffffffffffff;
                    lut9=64'hffffffffffffffff;
                    lut10=64'h0000000000000000;
                end
                6'd26:begin
                    lut0=64'h5555555555555554;
                    lut1=64'h6666666666666667;
                    lut2=64'h7878787878787879;
                    lut3=64'h807f807f807f807e;
                    lut4=64'h007fff80007fff81;
                    lut5=64'hff800000007ffffe;
                    lut6=64'hffffffffff800001;
                    lut7=64'h0000000000000000;
                    lut8=64'hffffffffffffffff;
                    lut9=64'hffffffffffffffff;
                    lut10=64'h0000000000000000;
                end
                6'd27:begin
                    lut0=64'haaaaaaaaad555555;
                    lut1=64'hccccccccce666666;
                    lut2=64'h0f0f0f0f08787878;
                    lut3=64'hf00ff00ff07f807f;
                    lut4=64'hfff0000ff87fff80;
                    lut5=64'hfffffff0007fffff;
                    lut6=64'hfffffffff87fffff;
                    lut7=64'h0000000007800000;
                    lut8=64'hffffffffffffffff;
                    lut9=64'hffffffffffffffff;
                    lut10=64'h0000000000000000;
                end
                6'd28:begin
                    lut0=64'h554aaaaaaaaaaaaa;
                    lut1=64'h998ccccccccccccc;
                    lut2=64'he1ef0f0f0f0f0f0f;
                    lut3=64'hfe0ff00ff00ff00f;
                    lut4=64'h0010000ffff0000f;
                    lut5=64'h001ffff00000000f;
                    lut6=64'h000000000000000f;
                    lut7=64'hfffffffffffffff0;
                    lut8=64'hffffffffffffffff;
                    lut9=64'hffffffffffffffff;
                    lut10=64'h0000000000000000;
                end
                6'd29:begin
                    lut0=64'h5555555555555555;
                    lut1=64'h9999999999999999;
                    lut2=64'he1e1e1e1e1e1e1e1;
                    lut3=64'hfe01fe01fe01fe01;
                    lut4=64'h0001fffe0001fffe;
                    lut5=64'h0001fffffffe0000;
                    lut6=64'hfffe000000000000;
                    lut7=64'hffffffffffffffff;
                    lut8=64'hffffffffffffffff;
                    lut9=64'hffffffffffffffff;
                    lut10=64'h0000000000000000;
                end
                6'd30:begin
                    lut0=64'haaaaaaaaaaaad555;
                    lut1=64'h3333333333331999;
                    lut2=64'h3c3c3c3c3c3c61e1;
                    lut3=64'h3fc03fc03fc07e01;
                    lut4=64'h3fffc0003ffffffe;
                    lut5=64'hc00000003fff8000;
                    lut6=64'hffffffffc0007fff;
                    lut7=64'hffffffffffffffff;
                    lut8=64'hffffffffffffffff;
                    lut9=64'hffffffffffffffff;
                    lut10=64'h0000000000000000;
                end
                6'd31:begin
                    lut0=64'h555554aaaaaaaaaa;
                    lut1=64'h6666673333333333;
                    lut2=64'h8787863c3c3c3c3c;
                    lut3=64'h07f807c03fc03fc0;
                    lut4=64'hf80006003fffc000;
                    lut5=64'hfffff8003fffffff;
                    lut6=64'hfffffe003fffffff;
                    lut7=64'hfffffe003fffffff;
                    lut8=64'hfffffe003fffffff;
                    lut9=64'hfffffe003fffffff;
                    lut10=64'h000001ffc0000000;
                end
                6'd32:begin
                    lut0=64'h5555555555555555;
                    lut1=64'h6666666666666666;
                    lut2=64'h8787878787878787;
                    lut3=64'h07f807f807f807f8;
                    lut4=64'hf80007fff80007ff;
                    lut5=64'hfffff800000007ff;
                    lut6=64'h00000000000007ff;
                    lut7=64'h00000000000007ff;
                    lut8=64'h00000000000007ff;
                    lut9=64'h00000000000007ff;
                    lut10=64'hfffffffffffff800;
                end
                6'd33:begin
                    lut0=64'haaaaaaaaaaaaaaad;
                    lut1=64'hccccccccccccccce;
                    lut2=64'hf0f0f0f0f0f0f0f7;
                    lut3=64'h00ff00ff00ff00f8;
                    lut4=64'h00ffff0000ffff07;
                    lut5=64'h00ffffffff000007;
                    lut6=64'hff00000000000000;
                    lut7=64'h0000000000000000;
                    lut8=64'h0000000000000000;
                    lut9=64'h0000000000000000;
                    lut10=64'hffffffffffffffff;
                end
                6'd34:begin
                    lut0=64'h555555554aaaaaaa;
                    lut1=64'h999999998ccccccc;
                    lut2=64'h1e1e1e1e10f0f0f0;
                    lut3=64'he01fe01fe0ff00ff;
                    lut4=64'hffe0001fe0ffff00;
                    lut5=64'h0000001fff000000;
                    lut6=64'hffffffe01fffffff;
                    lut7=64'h0000000000000000;
                    lut8=64'h0000000000000000;
                    lut9=64'h0000000000000000;
                    lut10=64'hffffffffffffffff;
                end
                6'd35:begin
                    lut0=64'haad5555555555555;
                    lut1=64'h3319999999999999;
                    lut2=64'hc39e1e1e1e1e1e1e;
                    lut3=64'hfc1fe01fe01fe01f;
                    lut4=64'h0060001fffe0001f;
                    lut5=64'hff80001fffffffe0;
                    lut6=64'hff80001fffffffff;
                    lut7=64'h007fffe000000000;
                    lut8=64'h0000000000000000;
                    lut9=64'h0000000000000000;
                    lut10=64'hffffffffffffffff;
                end
                6'd36:begin
                    lut0=64'haaaaaaaaaaaaaaaa;
                    lut1=64'h3333333333333333;
                    lut2=64'hc3c3c3c3c3c3c3c3;
                    lut3=64'hfc03fc03fc03fc03;
                    lut4=64'h0003fffc0003fffc;
                    lut5=64'hfffc00000003ffff;
                    lut6=64'h000000000003ffff;
                    lut7=64'hfffffffffffc0000;
                    lut8=64'h0000000000000000;
                    lut9=64'h0000000000000000;
                    lut10=64'hffffffffffffffff;
                end
                6'd37:begin
                    lut0=64'h555555555554aaaa;
                    lut1=64'h6666666666673333;
                    lut2=64'h787878787879c3c3;
                    lut3=64'h7f807f807f81fc03;
                    lut4=64'h7fff80007ffffffc;
                    lut5=64'h7fffffff8001ffff;
                    lut6=64'h8000000000000000;
                    lut7=64'hffffffffffffffff;
                    lut8=64'h0000000000000000;
                    lut9=64'h0000000000000000;
                    lut10=64'hffffffffffffffff;
                end
                6'd38:begin
                    lut0=64'haaaaad5555555555;
                    lut1=64'hccccce6666666666;
                    lut2=64'h0f0f087878787878;
                    lut3=64'h0ff00f807f807f80;
                    lut4=64'hf00008007fff8000;
                    lut5=64'h00000fff80000000;
                    lut6=64'hfffff7ffffffffff;
                    lut7=64'hffffffffffffffff;
                    lut8=64'h0000000000000000;
                    lut9=64'h0000000000000000;
                    lut10=64'hffffffffffffffff;
                end
                6'd39:begin
                    lut0=64'haaaaaaaaaaaaaaaa;
                    lut1=64'hcccccccccccccccc;
                    lut2=64'h0f0f0f0f0f0f0f0f;
                    lut3=64'h0ff00ff00ff00ff0;
                    lut4=64'hf0000ffff0000fff;
                    lut5=64'h00000ffffffff000;
                    lut6=64'h00000fffffffffff;
                    lut7=64'h00000fffffffffff;
                    lut8=64'hfffff00000000000;
                    lut9=64'h0000000000000000;
                    lut10=64'hffffffffffffffff;
                end
                6'd40:begin
                    lut0=64'h555555555555554a;
                    lut1=64'h999999999999998c;
                    lut2=64'he1e1e1e1e1e1e1ef;
                    lut3=64'h01fe01fe01fe01f0;
                    lut4=64'h01fffe0001fffe1f;
                    lut5=64'hfe00000001ffffe0;
                    lut6=64'h0000000001ffffe0;
                    lut7=64'h0000000001ffffe0;
                    lut8=64'hfffffffffe00001f;
                    lut9=64'h0000000000000000;
                    lut10=64'hffffffffffffffff;
                end
                6'd41:begin
                    lut0=64'haaaaaaaad5555555;
                    lut1=64'h3333333319999999;
                    lut2=64'h3c3c3c3c61e1e1e1;
                    lut3=64'hc03fc03f81fe01fe;
                    lut4=64'hffc0003f81fffe00;
                    lut5=64'hffffffc001ffffff;
                    lut6=64'h000000007e000000;
                    lut7=64'h0000000000000000;
                    lut8=64'hffffffffffffffff;
                    lut9=64'h0000000000000000;
                    lut10=64'hffffffffffffffff;
                end
                6'd42:begin
                    lut0=64'h54aaaaaaaaaaaaaa;
                    lut1=64'h6733333333333333;
                    lut2=64'h863c3c3c3c3c3c3c;
                    lut3=64'hf83fc03fc03fc03f;
                    lut4=64'h01c0003fffc0003f;
                    lut5=64'h01ffffc00000003f;
                    lut6=64'hffffffffffffffc0;
                    lut7=64'h0000000000000000;
                    lut8=64'hffffffffffffffff;
                    lut9=64'h0000000000000000;
                    lut10=64'hffffffffffffffff;
                end
                6'd43:begin
                    lut0=64'h5555555555555555;
                    lut1=64'h6666666666666666;
                    lut2=64'h8787878787878787;
                    lut3=64'hf807f807f807f807;
                    lut4=64'h0007fff80007fff8;
                    lut5=64'h0007fffffff80000;
                    lut6=64'h0007ffffffffffff;
                    lut7=64'hfff8000000000000;
                    lut8=64'hffffffffffffffff;
                    lut9=64'h0000000000000000;
                    lut10=64'hffffffffffffffff;
                end
                6'd44:begin
                    lut0=64'haaaaaaaaaaad5555;
                    lut1=64'hccccccccccce6666;
                    lut2=64'hf0f0f0f0f0f78787;
                    lut3=64'hff00ff00ff07f807;
                    lut4=64'hffff0000fffffff8;
                    lut5=64'h00000000fff80000;
                    lut6=64'h00000000fff80000;
                    lut7=64'hffffffff0007ffff;
                    lut8=64'hffffffffffffffff;
                    lut9=64'h0000000000000000;
                    lut10=64'hffffffffffffffff;
                end
                6'd45:begin
                    lut0=64'h55554aaaaaaaaaaa;
                    lut1=64'h99998ccccccccccc;
                    lut2=64'h1e1e10f0f0f0f0f0;
                    lut3=64'h1fe01f00ff00ff00;
                    lut4=64'he0000000ffff0000;
                    lut5=64'hffffe000ffffffff;
                    lut6=64'h00001fff00000000;
                    lut7=64'hffffffffffffffff;
                    lut8=64'hffffffffffffffff;
                    lut9=64'h0000000000000000;
                    lut10=64'hffffffffffffffff;
                end
                6'd46:begin
                    lut0=64'h5555555555555555;
                    lut1=64'h9999999999999999;
                    lut2=64'h1e1e1e1e1e1e1e1e;
                    lut3=64'h1fe01fe01fe01fe0;
                    lut4=64'he0001fffe0001fff;
                    lut5=64'hffffe00000001fff;
                    lut6=64'hffffffffffffe000;
                    lut7=64'hffffffffffffffff;
                    lut8=64'hffffffffffffffff;
                    lut9=64'h0000000000000000;
                    lut10=64'hffffffffffffffff;
                end
                6'd47:begin
                    lut0=64'haaaaaaaaaaaaaad5;
                    lut1=64'h3333333333333319;
                    lut2=64'hc3c3c3c3c3c3c39e;
                    lut3=64'h03fc03fc03fc03e0;
                    lut4=64'h03fffc0003fffc7f;
                    lut5=64'h03fffffffc00007f;
                    lut6=64'h03ffffffffffffff;
                    lut7=64'h03ffffffffffffff;
                    lut8=64'h03ffffffffffffff;
                    lut9=64'hfc00000000000000;
                    lut10=64'hffffffffffffffff;
                end
                6'd48:begin
                    lut0=64'h55555554aaaaaaaa;
                    lut1=64'h6666666733333333;
                    lut2=64'h78787879c3c3c3c3;
                    lut3=64'h807f807e03fc03fc;
                    lut4=64'hff80007e03fffc00;
                    lut5=64'h0000007ffc000000;
                    lut6=64'h0000007e00000000;
                    lut7=64'h0000007e00000000;
                    lut8=64'h0000007e00000000;
                    lut9=64'hffffff81ffffffff;
                    lut10=64'hffffffffffffffff;
                end
                6'd49:begin
                    lut0=64'had55555555555555;
                    lut1=64'hce66666666666666;
                    lut2=64'h0878787878787878;
                    lut3=64'hf07f807f807f807f;
                    lut4=64'h0780007fff80007f;
                    lut5=64'hf800007fffffff80;
                    lut6=64'h07ffff8000000000;
                    lut7=64'h0000000000000000;
                    lut8=64'h0000000000000000;
                    lut9=64'hffffffffffffffff;
                    lut10=64'hffffffffffffffff;
                end
                6'd50:begin
                    lut0=64'haaaaaaaaaaaaaaaa;
                    lut1=64'hcccccccccccccccc;
                    lut2=64'h0f0f0f0f0f0f0f0f;
                    lut3=64'hf00ff00ff00ff00f;
                    lut4=64'h000ffff0000ffff0;
                    lut5=64'hfff00000000fffff;
                    lut6=64'hfffffffffff00000;
                    lut7=64'h0000000000000000;
                    lut8=64'h0000000000000000;
                    lut9=64'hffffffffffffffff;
                    lut10=64'hffffffffffffffff;
                end
                6'd51:begin
                    lut0=64'h55555555554aaaaa;
                    lut1=64'h99999999998ccccc;
                    lut2=64'he1e1e1e1e1ef0f0f;
                    lut3=64'hfe01fe01fe0ff00f;
                    lut4=64'hfffe0001ffeffff0;
                    lut5=64'hfffffffe000fffff;
                    lut6=64'hffffffffffefffff;
                    lut7=64'h0000000000100000;
                    lut8=64'h0000000000000000;
                    lut9=64'hffffffffffffffff;
                    lut10=64'hffffffffffffffff;
                end
                6'd52:begin
                    lut0=64'haaaad55555555555;
                    lut1=64'h3333199999999999;
                    lut2=64'h3c3c61e1e1e1e1e1;
                    lut3=64'h3fc07e01fe01fe01;
                    lut4=64'hc0000001fffe0001;
                    lut5=64'h00007ffe00000001;
                    lut6=64'h0000000000000001;
                    lut7=64'hfffffffffffffffe;
                    lut8=64'h0000000000000000;
                    lut9=64'hffffffffffffffff;
                    lut10=64'hffffffffffffffff;
                end
                6'd53:begin
                    lut0=64'haaaaaaaaaaaaaaaa;
                    lut1=64'h3333333333333333;
                    lut2=64'h3c3c3c3c3c3c3c3c;
                    lut3=64'h3fc03fc03fc03fc0;
                    lut4=64'hc0003fffc0003fff;
                    lut5=64'h00003fffffffc000;
                    lut6=64'hffffc00000000000;
                    lut7=64'hffffffffffffffff;
                    lut8=64'h0000000000000000;
                    lut9=64'hffffffffffffffff;
                    lut10=64'hffffffffffffffff;
                end
                6'd54:begin
                    lut0=64'h55555555555554aa;
                    lut1=64'h6666666666666733;
                    lut2=64'h878787878787863c;
                    lut3=64'h07f807f807f807c0;
                    lut4=64'h07fff80007fff9ff;
                    lut5=64'hf800000007fffe00;
                    lut6=64'hfffffffff80001ff;
                    lut7=64'hffffffffffffffff;
                    lut8=64'h0000000000000000;
                    lut9=64'hffffffffffffffff;
                    lut10=64'hffffffffffffffff;
                end
                6'd55:begin
                    lut0=64'haaaaaaad55555555;
                    lut1=64'hccccccce66666666;
                    lut2=64'hf0f0f0f787878787;
                    lut3=64'h00ff00f807f807f8;
                    lut4=64'hff0000f807fff800;
                    lut5=64'hffffff0007ffffff;
                    lut6=64'hfffffff807ffffff;
                    lut7=64'hfffffff807ffffff;
                    lut8=64'h00000007f8000000;
                    lut9=64'hffffffffffffffff;
                    lut10=64'hffffffffffffffff;
                end
                6'd56:begin
                    lut0=64'h4aaaaaaaaaaaaaaa;
                    lut1=64'h8ccccccccccccccc;
                    lut2=64'h10f0f0f0f0f0f0f0;
                    lut3=64'he0ff00ff00ff00ff;
                    lut4=64'h1f0000ffff0000ff;
                    lut5=64'h1fffff00000000ff;
                    lut6=64'h00000000000000ff;
                    lut7=64'h00000000000000ff;
                    lut8=64'hffffffffffffff00;
                    lut9=64'hffffffffffffffff;
                    lut10=64'hffffffffffffffff;
                end
                6'd57:begin
                    lut0=64'h5555555555555555;
                    lut1=64'h9999999999999999;
                    lut2=64'h1e1e1e1e1e1e1e1e;
                    lut3=64'he01fe01fe01fe01f;
                    lut4=64'h001fffe0001fffe0;
                    lut5=64'h001fffffffe00000;
                    lut6=64'hffe0000000000000;
                    lut7=64'h0000000000000000;
                    lut8=64'hffffffffffffffff;
                    lut9=64'hffffffffffffffff;
                    lut10=64'hffffffffffffffff;
                end
                6'd58:begin
                    lut0=64'haaaaaaaaaad55555;
                    lut1=64'h3333333333199999;
                    lut2=64'hc3c3c3c3c39e1e1e;
                    lut3=64'hfc03fc03fc1fe01f;
                    lut4=64'hfffc0003ff9fffe0;
                    lut5=64'h00000003ffe00000;
                    lut6=64'hfffffffc007fffff;
                    lut7=64'h0000000000000000;
                    lut8=64'hffffffffffffffff;
                    lut9=64'hffffffffffffffff;
                    lut10=64'hffffffffffffffff;
                end
                6'd59:begin
                    lut0=64'h5554aaaaaaaaaaaa;
                    lut1=64'h6667333333333333;
                    lut2=64'h7879c3c3c3c3c3c3;
                    lut3=64'h7f81fc03fc03fc03;
                    lut4=64'h80000003fffc0003;
                    lut5=64'hfffe0003fffffffc;
                    lut6=64'hfffe0003ffffffff;
                    lut7=64'h0001fffc00000000;
                    lut8=64'hffffffffffffffff;
                    lut9=64'hffffffffffffffff;
                    lut10=64'hffffffffffffffff;
                end
                6'd60:begin
                    lut0=64'h5555555555555555;
                    lut1=64'h6666666666666666;
                    lut2=64'h7878787878787878;
                    lut3=64'h7f807f807f807f80;
                    lut4=64'h80007fff80007fff;
                    lut5=64'hffff800000007fff;
                    lut6=64'h0000000000007fff;
                    lut7=64'hffffffffffff8000;
                    lut8=64'hffffffffffffffff;
                    lut9=64'hffffffffffffffff;
                    lut10=64'hffffffffffffffff;
                end
                6'd61:begin
                    lut0=64'haaaaaaaaaaaaad55;
                    lut1=64'hccccccccccccce66;
                    lut2=64'h0f0f0f0f0f0f0878;
                    lut3=64'h0ff00ff00ff00f80;
                    lut4=64'h0ffff0000ffff7ff;
                    lut5=64'h0ffffffff00007ff;
                    lut6=64'hf000000000000000;
                    lut7=64'hffffffffffffffff;
                    lut8=64'hffffffffffffffff;
                    lut9=64'hffffffffffffffff;
                    lut10=64'hffffffffffffffff;
                end
                6'd62:begin
                    lut0=64'h5555554aaaaaaaaa;
                    lut1=64'h9999998ccccccccc;
                    lut2=64'he1e1e1ef0f0f0f0f;
                    lut3=64'h01fe01f00ff00ff0;
                    lut4=64'hfe0001e00ffff000;
                    lut5=64'h000001fff0000000;
                    lut6=64'hfffffe1fffffffff;
                    lut7=64'hffffffffffffffff;
                    lut8=64'hffffffffffffffff;
                    lut9=64'hffffffffffffffff;
                    lut10=64'hffffffffffffffff;
                end
                6'd63:begin
                    lut0=64'hd555555555555555;
                    lut1=64'h1999999999999999;
                    lut2=64'h61e1e1e1e1e1e1e1;
                    lut3=64'h81fe01fe01fe01fe;
                    lut4=64'h7e0001fffe0001ff;
                    lut5=64'h800001fffffffe00;
                    lut6=64'h800001ffffffffff;
                    lut7=64'h800001ffffffffff;
                    lut8=64'h800001ffffffffff;
                    lut9=64'h800001ffffffffff;
                    lut10=64'h800001ffffffffff;
                end
            endcase
            return p==0?{lut10[t[6:1]], lut9[t[6:1]], lut8[t[6:1]], lut7[t[6:1]], lut6[t[6:1]], lut5[t[6:1]], lut4[t[6:1]], lut3[t[6:1]], lut2[t[6:1]], lut1[t[6:1]], lut0[t[6:1]]}:t[10:0];
        end
    endfunction
    task automatic fail(input logic [7:0] reason);
        error<=reason;running<=0;done<=0;bank_state[0]<=FREE;bank_state[1]<=FREE;
        fill_index<=0;math_state<=M_IDLE;
    endtask

    assign kill=reset||start||cancel||error!=0;
    assign busy=running||owned_banks!=0||math_state!=M_IDLE;
    assign owned_banks=2'(bank_state[0]!=FREE)+2'(bank_state[1]!=FREE);
    assign in_ready=running&&!finished_input&&!input_done&&!kill&&
        (bank_state[fill_bank]==FREE||bank_state[fill_bank]==FILL);
    assign input_metadata_bad=in_metadata_bad||
        (bank_state[fill_bank]==FILL&&(epochs[fill_bank]!=in_epoch||child_epochs[fill_bank]!=in_child_epoch||
         planes[fill_bank]!=in_plane||scales[fill_bank]!=in_qscale||blocks[fill_bank]!=in_block||
         tiles[fill_bank]!=in_tile||cells[fill_bank]!=in_qcell));
    always_comb begin
        input_fault=0;
        if(input_done&&fill_index!=0)input_fault=4;
        else if(in_valid&&in_ready)begin
            if(in_index!=fill_index)input_fault=1;
            else if(input_metadata_bad)input_fault=2;
            else if(in_domain_bad)input_fault=3;
            else if(fill_index==0&&next_token==32'hffffffff)input_fault=7;
        end
    end
    assign out_valid=running&&math_state==M_EMIT&&idct_valid&&!kill&&!idct_error&&idct_id==tokens[math_bank];
    assign out_value=$signed(idct_data[int'(emit_index)*24+:24]);
    assign out_index=emit_index;
    assign out_epoch=epochs[math_bank];assign out_child_epoch=child_epochs[math_bank];
    assign out_token=tokens[math_bank];assign out_plane=planes[math_bank];
    assign out_qscale=scales[math_bank];assign out_block=blocks[math_bank];
    assign out_tile=tiles[math_bank];assign out_qcell=cells[math_bank];
    assign dq_out_ready=math_state==M_DQ_WAIT&&idct_ready&&!kill&&!dq_error&&dq_id==tokens[math_bank];
    assign idct_out_ready=math_state==M_EMIT&&out_ready&&emit_index==63&&!kill&&!idct_error&&idct_id==tokens[math_bank];
    assign dbg_launch=math_state==M_DQ_SEND&&dq_ready&&!kill;
    assign dbg_dequant=dq_valid&&dq_out_ready;
    assign dbg_coefficients=coefficients[math_bank];assign dbg_dequantized=dq_data;
    assign dbg_token=tokens[math_bank];assign dbg_epoch=epochs[math_bank];
    assign dbg_child_epoch=child_epochs[math_bank];assign dbg_plane=planes[math_bank];
    assign dbg_qscale=scales[math_bank];assign dbg_block=blocks[math_bank];
    assign dbg_tile=tiles[math_bank];assign dbg_qcell=cells[math_bank];

    // Coefficient storage is physically expressed as fixed-bank, fixed-word
    // registers. No payload reset: ownership invalidation remains in the FSM.
    // The original packed bank views feed both debug and the dequantizer.
    for(genvar coef_bank=0;coef_bank<2;coef_bank=coef_bank+1)begin: coefficient_banks
        for(genvar coef_word=0;coef_word<64;coef_word=coef_word+1)begin: words
            logic [15:0] value;
            always_ff @(posedge clk)begin
                if(!reset&&!start&&!cancel&&error==0&&running&&input_fault==0&&
                    in_valid&&in_ready&&fill_bank==1'(coef_bank)&&fill_index==6'(coef_word))
                    value<=in_value;
            end
            assign coefficients[coef_bank][coef_word*16+:16]=value;
        end
    end

    cu66_dequant dequant (
        .clk(clk),.rst(reset),.abort_i(start||cancel||error!=0),
        .in_valid(math_state==M_DQ_SEND&&!kill),.in_ready(dq_ready),
        .in_id(tokens[math_bank]),.in_coefficients(coefficients[math_bank]),
        .in_chroma(planes[math_bank]!=0),.in_scale_code(scales[math_bank]),
        .out_valid(dq_valid),.out_ready(dq_out_ready),.out_id(dq_id),
        .out_dequantized(dq_data),.out_error(dq_error));
    cu66_idct8x8 inverse (
        .clk(clk),.rst(reset),.abort_frame(start||cancel||error!=0),
        .in_valid(dq_valid&&math_state==M_DQ_WAIT&&!kill&&!dq_error&&dq_id==tokens[math_bank]),
        .in_ready(idct_ready),.in_id(dq_id),.in_tile(dq_data),
        .out_valid(idct_valid),.out_ready(idct_out_ready),.out_id(idct_id),
        .out_tile(idct_data),.out_error(idct_error),.active_cycles(unused_idct_cycles));

    always_ff @(posedge clk) begin
        if(reset||start||cancel)begin
            running<=start&&!reset&&!cancel;finished_input<=0;done<=0;error<=0;
            bank_state[0]<=FREE;bank_state[1]<=FREE;fill_bank<=0;math_bank<=0;
            fill_index<=0;emit_index<=0;math_state<=M_IDLE;
            // Both arithmetic producers flush synchronously on this same edge.
            // Token identity is frame_epoch + token, not a lifetime nonce.
            next_token<=0;
            if(reset||start)begin
                count_inputs<=0;count_tiles<=0;count_launches<=0;count_dequant<=0;
                count_outputs<=0;count_completed_tiles<=0;count_input_stalls<=0;count_output_stalls<=0;
                count_cancelled_banks<=0;max_owned_banks<=0;
            end else count_cancelled_banks<=count_cancelled_banks+64'(owned_banks);
        end else if(error==0&&running)begin
            if(owned_banks>max_owned_banks)max_owned_banks<=owned_banks;
            if(in_valid&&!in_ready)count_input_stalls<=count_input_stalls+1;
            if(out_valid&&!out_ready)count_output_stalls<=count_output_stalls+1;
            if(in_valid&&in_ready)count_inputs<=count_inputs+1;
            if(dbg_launch)count_launches<=count_launches+1;
            if(dbg_dequant)count_dequant<=count_dequant+1;
            if(out_valid&&out_ready)begin
                count_outputs<=count_outputs+1;
                if(emit_index==63)count_completed_tiles<=count_completed_tiles+1;
            end
            if(input_fault!=0)fail(input_fault);
            else begin
            if(input_done)finished_input<=1;
            if(in_valid&&in_ready)begin
                    
                    if(fill_index==0)begin
                        epochs[fill_bank]<=in_epoch;child_epochs[fill_bank]<=in_child_epoch;
                        planes[fill_bank]<=in_plane;scales[fill_bank]<=in_qscale;
                        blocks[fill_bank]<=in_block;tiles[fill_bank]<=in_tile;cells[fill_bank]<=in_qcell;
                        tokens[fill_bank]<=next_token+1;next_token<=next_token+1;
                        bank_state[fill_bank]<=FILL;
                    end
                    if(fill_index==63)begin
                        bank_state[fill_bank]<=READY;fill_bank<=!fill_bank;fill_index<=0;
                        count_tiles<=count_tiles+1;
                    end else fill_index<=fill_index+1;
            end
            case(math_state)
                M_IDLE:if(bank_state[math_bank]==READY)begin
                    bank_state[math_bank]<=ACTIVE;math_state<=M_DQ_SEND;
                end
                M_DQ_SEND:if(dbg_launch)math_state<=M_DQ_WAIT;
                M_DQ_WAIT:if(dq_valid)begin
                    if(dq_error||dq_id!=tokens[math_bank])fail(5);
                    else if(dq_out_ready)math_state<=M_IDCT_WAIT;
                end
                M_IDCT_WAIT:if(idct_valid)begin
                    if(idct_error||idct_id!=tokens[math_bank])fail(6);
                    else begin emit_index<=0;math_state<=M_EMIT;end
                end
                M_EMIT:begin
                    if(idct_valid&&(idct_error||idct_id!=tokens[math_bank]))fail(6);
                    else if(out_valid&&out_ready)begin
                        if(emit_index==63)begin
                            bank_state[math_bank]<=FREE;math_bank<=!math_bank;math_state<=M_IDLE;
                            emit_index<=0;
                        end else emit_index<=emit_index+1;
                    end
                end
                default:begin end
            endcase
            if(finished_input&&owned_banks==0&&math_state==M_IDLE)begin running<=0;done<=1;end
            end
        end
    end
`ifndef SYNTHESIS
    // Sidebands are valid only for the same owned token as the input tuple.
    always_ff @(posedge clk)if(!kill&&running&&in_valid&&in_ready)begin
        assert(in_metadata_bad==(in_plane>2||in_tile>=(in_plane==0?13'd5400:13'd1350)||in_qcell!=quant_cell(in_plane,in_tile)))
            else $fatal(1,"inverse static metadata flag mismatch");
        assert(in_domain_bad==(in_qscale==3||!(in_value[15:11]==5'd0||in_value[15:11]==5'b11111||in_value==16'h0800)))
            else $fatal(1,"inverse static domain flag mismatch");
    end
    always_ff @(posedge clk) if(!kill)begin
        assert(owned_banks<=2)else $fatal(1,"inverse bank owner bound");
        if(dbg_launch)assert(bank_state[math_bank]==ACTIVE)else $fatal(1,"inverse launch without owner");
        if(out_valid)assert(bank_state[math_bank]==ACTIVE&&idct_id==tokens[math_bank])else $fatal(1,"inverse output without owner");
        if(done)assert(owned_banks==0&&math_state==M_IDLE)else $fatal(1,"inverse done before drain");
    end
`endif
endmodule
