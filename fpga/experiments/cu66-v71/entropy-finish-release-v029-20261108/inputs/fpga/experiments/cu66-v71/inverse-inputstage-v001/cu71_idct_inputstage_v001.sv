// Exact two-pass Q14 inverse, mirrored outputs, eight shared multiply lanes.
// Two microcycles per input: registered multiply, then signed accumulation.
// Inputs are dequantized raster coefficients; output is an unclipped residual.
module cu71_idct_inputstage_v001 (
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
    output logic [31:0] active_cycles
);
    typedef enum logic [3:0] {IDLE, FIRST_MUL, FIRST_ACC, SECOND_MUL,
        SECOND_ACC, DC_FIRST_MUL, DC_FIRST_ACC, DC_SECOND_MUL,
        DC_SECOND_ACC, OUTPUT_TILE, VALIDATE_INPUT, FIRST_EXEC, SECOND_EXEC,
        DC_FIRST_EXEC, DC_SECOND_EXEC} state_t;
    state_t state;
    // Every source/output word is written before its valid use; no bulk reset.
    logic signed [19:0] source_coeff [0:63];
    logic signed [23:0] result_word [0:63];
    for(genvar output_word=0;output_word<64;output_word=output_word+1)begin:g_output
        assign out_tile[output_word*24 +:24]=result_word[output_word];
    end
    (* MAX_FANOUT = 32 *) logic [1:0] group_index;
    (* MAX_FANOUT = 32 *) logic [2:0] k;
    logic signed [23:0] intermediate [0:63];
    logic signed [23:0] dc_middle;
    logic signed [23:0] samples [0:7];
    logic signed [37:0] products [0:7];
    logic signed [39:0] even_sum [0:7], odd_sum [0:7];
    logic signed [39:0] next_even [0:7], next_odd [0:7];
    // Classification payload is overwritten on every accepted input before
    // VALIDATE_INPUT uses it. No bulk or startup payload reset is required.
    logic [7:0] bad_group, zero_group, ac_zero_group;
    function automatic logic bad_eight(input logic [159:0] tile);
        begin
            bad_eight=1'b0;
            for(integer c=0;c<8;c=c+1)
                if($signed(tile[c*20 +:20])>20'sd522240 ||
                   $signed(tile[c*20 +:20])< -20'sd522240)bad_eight=1'b1;
        end
    endfunction
    for(genvar g=0;g<8;g=g+1)begin:g_classify
        always_ff @(posedge clk)if(in_valid && in_ready)begin
            bad_group[g]<=bad_eight(in_tile[g*160 +:160]);
            zero_group[g]<=in_tile[g*160 +:160]==0;
            if(g==0)ac_zero_group[g]<=in_tile[159:20]==0;
            else ac_zero_group[g]<=in_tile[g*160 +:160]==0;
        end
    end
    integer lane;
    integer index;

    function automatic logic signed [13:0] basis(input logic [2:0] fk,
                                                input logic [1:0] fp);
        case ({fk, fp})
            5'd0,5'd1,5'd2,5'd3: basis=14'sd5793;
            5'd4: basis=14'sd8035; 5'd5: basis=14'sd6811;
            5'd6: basis=14'sd4551; 5'd7: basis=14'sd1598;
            5'd8: basis=14'sd7568; 5'd9: basis=14'sd3135;
            5'd10: basis=-14'sd3135; 5'd11: basis=-14'sd7568;
            5'd12: basis=14'sd6811; 5'd13: basis=-14'sd1598;
            5'd14: basis=-14'sd8035; 5'd15: basis=-14'sd4551;
            5'd16: basis=14'sd5793; 5'd17: basis=-14'sd5793;
            5'd18: basis=-14'sd5793; 5'd19: basis=14'sd5793;
            5'd20: basis=14'sd4551; 5'd21: basis=-14'sd8035;
            5'd22: basis=14'sd1598; 5'd23: basis=14'sd6811;
            5'd24: basis=14'sd3135; 5'd25: basis=-14'sd7568;
            5'd26: basis=14'sd7568; 5'd27: basis=-14'sd3135;
            5'd28: basis=14'sd1598; 5'd29: basis=-14'sd4551;
            5'd30: basis=14'sd6811; 5'd31: basis=-14'sd8035;
            default: basis='0;
        endcase
    endfunction

    function automatic logic signed [23:0] rounded(input logic signed [39:0] a);
        begin
            rounded=24'((a+40'sd8192) >>> 14);
        end
    endfunction

    // Two carry-save reductions and one final modular-40 carry propagation.
    function automatic logic [39:0] csa4_mod40(
        input logic [39:0] a,b,c,d);
        logic [39:0] s0,c0,s1,c1;
        begin
            s0=a^b^c;
            c0=((a&b)|(a&c)|(b&c))<<1;
            s1=s0^c0^d;
            c1=((s0&c0)|(s0&d)|(c0&d))<<1;
            csa4_mod40=s1+c1;
        end
    endfunction
    function automatic logic signed [23:0] final_plus(
        input logic [39:0] e,o,p);
        logic [39:0] value;
        begin value=csa4_mod40(e,o,p,40'd8192);final_plus=value[37:14];end
    endfunction
    function automatic logic signed [23:0] final_minus(
        input logic [39:0] e,o,p);
        logic [39:0] value;
        begin value=csa4_mod40(e,~o,~p,40'd8194);final_minus=value[37:14];end
    endfunction

    always_comb begin
        for (integer l=0; l<8; l=l+1) begin
            samples[l]='0;
            if (state==FIRST_MUL)
                samples[l]=$signed(source_coeff[{group_index,1'(l/4),k}]);
            else if (state==SECOND_MUL)
                samples[l]=intermediate[{k,group_index,1'(l/4)}];
            else if (state==DC_FIRST_MUL && l==0)
                samples[l]=$signed(source_coeff[0]);
            else if (state==DC_SECOND_MUL && l==0)
                samples[l]=dc_middle;
            next_even[l]=even_sum[l];
            next_odd[l]=odd_sum[l];
            if (k[0]) next_odd[l]=odd_sum[l]+{{2{products[l][37]}},products[l]};
            else next_even[l]=even_sum[l]+{{2{products[l][37]}},products[l]};
        end
    end

    // Private payload is overwritten at every edge. EXEC states are the
    // only consumers, each entered from a matching original MUL sample edge.
    logic signed [23:0] sample_stage [0:7];
    logic signed [13:0] basis_stage [0:7];
    always_ff @(posedge clk)begin
        for(integer sample_lane=0;sample_lane<8;sample_lane=sample_lane+1)begin
            sample_stage[sample_lane]<=samples[sample_lane];
            basis_stage[sample_lane]<=basis(k,2'(sample_lane%4));
        end
    end

    assign in_ready=(state==IDLE) && !abort_frame && !rst;
    assign out_valid=(state==OUTPUT_TILE) && !abort_frame && !rst;

    always_ff @(posedge clk) begin
        if (rst || abort_frame) begin
            state<=IDLE;
            out_error<=1'b0;
            out_id<='0;
            group_index<='0;
            k<='0;
            active_cycles<='0;
        end else begin
            if (state!=IDLE && state!=OUTPUT_TILE) active_cycles<=active_cycles+1;
            case (state)
                IDLE: if (in_valid && in_ready) begin
                    for(index=0;index<64;index=index+1)source_coeff[index]<=in_tile[index*20 +:20];
                    out_id<=in_id;
                    out_error<=1'b0;
                    active_cycles<=0;
                    group_index<=0;
                    k<=0;
                    for (lane=0; lane<8; lane=lane+1) begin
                        even_sum[lane]<=0;
                        odd_sum[lane]<=0;
                    end
                    state<=VALIDATE_INPUT;
                end
                VALIDATE_INPUT: begin
                    out_error<=|bad_group;
                    if ((|bad_group) || (&zero_group)) begin
                        for(index=0;index<64;index=index+1)result_word[index]<=0;
                        state<=OUTPUT_TILE;
                    end else if (&ac_zero_group) state<=DC_FIRST_MUL;
                    else state<=FIRST_MUL;
                end
                FIRST_MUL, SECOND_MUL, DC_FIRST_MUL, DC_SECOND_MUL: begin
                    // The unconditional private sample/basis registers capture
                    // exactly this original MUL edge; arithmetic executes next.
                    case (state)
                        FIRST_MUL: state<=FIRST_EXEC;
                        SECOND_MUL: state<=SECOND_EXEC;
                        DC_FIRST_MUL: state<=DC_FIRST_EXEC;
                        default: state<=DC_SECOND_EXEC;
                    endcase
                end
                FIRST_EXEC, SECOND_EXEC, DC_FIRST_EXEC, DC_SECOND_EXEC: begin
                    for (lane=0; lane<8; lane=lane+1)
                        products[lane]<=$signed(sample_stage[lane]) * $signed(basis_stage[lane]);
                    case (state)
                        FIRST_EXEC: state<=FIRST_ACC;
                        SECOND_EXEC: state<=SECOND_ACC;
                        DC_FIRST_EXEC: state<=DC_FIRST_ACC;
                        default: state<=DC_SECOND_ACC;
                    endcase
                end
                DC_FIRST_ACC: begin
                    dc_middle<=rounded({{2{products[0][37]}},products[0]});
                    state<=DC_SECOND_MUL;
                end
                DC_SECOND_ACC: begin
                    for (index=0; index<64; index=index+1)
                        result_word[index]<=rounded({{2{products[0][37]}},products[0]});
                    state<=OUTPUT_TILE;
                end
                FIRST_ACC, SECOND_ACC: begin
                    if (k==7) begin
                        for (lane=0; lane<8; lane=lane+1) begin
                            if (state==FIRST_ACC) begin
                                intermediate[{group_index,1'(lane/4),3'(lane%4)}]
                                    <=final_plus(even_sum[lane],odd_sum[lane],{{2{products[lane][37]}},products[lane]});
                                intermediate[{group_index,1'(lane/4),3'(7-lane%4)}]
                                    <=final_minus(even_sum[lane],odd_sum[lane],{{2{products[lane][37]}},products[lane]});
                            end else begin
                                result_word[{3'(lane%4),group_index,1'(lane/4)}]
                                    <=final_plus(even_sum[lane],odd_sum[lane],{{2{products[lane][37]}},products[lane]});
                                result_word[{3'(7-lane%4),group_index,1'(lane/4)}]
                                    <=final_minus(even_sum[lane],odd_sum[lane],{{2{products[lane][37]}},products[lane]});
                            end
                            even_sum[lane]<=0;
                            odd_sum[lane]<=0;
                        end
                        k<=0;
                        if (group_index==3) begin
                            group_index<=0;
                            state<=(state==FIRST_ACC) ? SECOND_MUL : OUTPUT_TILE;
                        end else begin
                            group_index<=group_index+1;
                            state<=(state==FIRST_ACC) ? FIRST_MUL : SECOND_MUL;
                        end
                    end else begin
                        for (lane=0; lane<8; lane=lane+1) begin
                            even_sum[lane]<=next_even[lane];
                            odd_sum[lane]<=next_odd[lane];
                        end
                        k<=k+1;
                        state<=(state==FIRST_ACC) ? FIRST_MUL : SECOND_MUL;
                    end
                end
                OUTPUT_TILE: if (out_ready && out_valid) state<=IDLE;
                default: state<=IDLE;
            endcase
        end
    end
endmodule
