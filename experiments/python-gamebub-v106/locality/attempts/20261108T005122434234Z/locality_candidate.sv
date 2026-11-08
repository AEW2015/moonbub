// Two coefficient-tile owners around the frozen dequantizer and Q14 inverse.
// Output is a provisional signed residual, never a published pixel frame.
module locality_candidate (
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
        return p==0?11'(((32'(t)/90)/2)*45+(32'(t)%90)/2):11'(t);
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
    assign input_metadata_bad=in_plane>2||in_tile>=(in_plane==0?13'd5400:13'd1350)||
        in_qcell!=quant_cell(in_plane,in_tile)||
        (bank_state[fill_bank]==FILL&&(epochs[fill_bank]!=in_epoch||child_epochs[fill_bank]!=in_child_epoch||
         planes[fill_bank]!=in_plane||scales[fill_bank]!=in_qscale||blocks[fill_bank]!=in_block||
         tiles[fill_bank]!=in_tile||cells[fill_bank]!=in_qcell));
    always_comb begin
        input_fault=0;
        if(input_done&&fill_index!=0)input_fault=4;
        else if(in_valid&&in_ready)begin
            if(in_index!=fill_index)input_fault=1;
            else if(input_metadata_bad)input_fault=2;
            else if(in_qscale==3||in_value < -16'sd2048||in_value > 16'sd2048)input_fault=3;
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
    always_ff @(posedge clk) if(!kill)begin
        assert(owned_banks<=2)else $fatal(1,"inverse bank owner bound");
        if(dbg_launch)assert(bank_state[math_bank]==ACTIVE)else $fatal(1,"inverse launch without owner");
        if(out_valid)assert(bank_state[math_bank]==ACTIVE&&idct_id==tokens[math_bank])else $fatal(1,"inverse output without owner");
        if(done)assert(owned_banks==0&&math_state==M_IDLE)else $fatal(1,"inverse done before drain");
    end
`endif
endmodule
