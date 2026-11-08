// Exact two-pass Q14 inverse, mirrored outputs, eight shared multiply lanes.
// Two microcycles per input: registered multiply, then signed accumulation.
// Inputs are dequantized raster coefficients; output is an unclipped residual.
module cu66_idct8x8 (
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
        DC_SECOND_ACC, OUTPUT_TILE} state_t;
    state_t state;
    logic [1279:0] source_tile;
    logic [1:0] group_index;
    logic [2:0] k;
    logic signed [23:0] intermediate [0:63];
    logic signed [23:0] dc_middle;
    logic signed [23:0] samples [0:7];
    logic signed [37:0] products [0:7];
    logic signed [23:0] operand_samples[0:7], next_samples[0:1];
    logic [19:0] source_words[0:63];
    logic signed [13:0] operand_basis[0:3];
    logic prefetch_enable, prefetch_dc, prefetch_first;
    logic [1:0] prefetch_group;
    logic [2:0] prefetch_k;
`ifndef SYNTHESIS
    logic operand_live;
`endif
    logic signed [39:0] even_sum [0:7], odd_sum [0:7];
    logic signed [39:0] next_even [0:7], next_odd [0:7];
    logic input_bad;
    integer lane;

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

    for(genvar word=0;word<64;word=word+1)begin: fixed_source_words
        assign source_words[word]=source_tile[word*20+:20];
    end
    // One next-address decoder and one variable read network per source.
    always_comb begin
        prefetch_enable=0;prefetch_dc=0;prefetch_first=state==FIRST_ACC;
        prefetch_group=group_index;prefetch_k=k+3'd1;
        if(state==IDLE)begin
            prefetch_enable=in_valid && in_ready && !input_bad && in_tile!=0;
            prefetch_group=0;prefetch_k=0;prefetch_dc=in_tile[1279:20]==0;
        end else if(state==DC_FIRST_ACC)begin
            prefetch_enable=1;prefetch_dc=1;prefetch_group=0;prefetch_k=0;
        end else if(state==FIRST_ACC || state==SECOND_ACC)begin
            prefetch_enable=!(state==SECOND_ACC && group_index==3 && k==7);
            if(k==7)begin
                prefetch_k=0;prefetch_group=group_index+2'd1;
                if(group_index==3)prefetch_first=0;
            end
        end
        for(integer row=0;row<2;row=row+1)begin
            if(state==IDLE)
                next_samples[row]={{4{in_tile[(row*8)*20+19]}},in_tile[(row*8)*20+:20]};
            else if(prefetch_dc)
                next_samples[row]=row==0 ? rounded({{2{products[0][37]}},products[0]}) : 24'sd0;
            else if(prefetch_first)
                next_samples[row]={{4{source_words[{prefetch_group,1'(row),prefetch_k}][19]}},
                    source_words[{prefetch_group,1'(row),prefetch_k}]};
            else next_samples[row]=intermediate[{prefetch_k,prefetch_group,1'(row)}];
        end
    end
`ifndef SYNTHESIS
    always_ff @(posedge clk)if(!rst&&!abort_frame &&
        (state==FIRST_MUL||state==SECOND_MUL||state==DC_FIRST_MUL||state==DC_SECOND_MUL))begin
        assert(operand_live);
        for(integer p=0;p<8;p=p+1)begin
            assert(operand_samples[p]==samples[p]);
            assert(operand_basis[p%4]==basis(k,2'(p%4)));
        end
    end
`endif

    always_comb begin
        input_bad=1'b0;
        for (integer n=0; n<64; n=n+1)
            if ($signed(in_tile[n*20 +:20]) > 20'sd522240 ||
                $signed(in_tile[n*20 +:20]) < -20'sd522240)
                input_bad=1'b1;
        for (integer l=0; l<8; l=l+1) begin
            samples[l]='0;
            if (state==FIRST_MUL)
                samples[l]={{4{source_tile[((int'(group_index)*2+l/4)*8+int'(k))*20+19]}},
                    source_tile[((int'(group_index)*2+l/4)*8+int'(k))*20 +:20]};
            else if (state==SECOND_MUL)
                samples[l]=intermediate[int'(k)*8+int'(group_index)*2+l/4];
            else if (state==DC_FIRST_MUL && l==0)
                samples[l]={{4{source_tile[19]}}, source_tile[19:0]};
            else if (state==DC_SECOND_MUL && l==0)
                samples[l]=dc_middle;
            next_even[l]=even_sum[l];
            next_odd[l]=odd_sum[l];
            if (k[0]) next_odd[l]=odd_sum[l]+{{2{products[l][37]}},products[l]};
            else next_even[l]=even_sum[l]+{{2{products[l][37]}},products[l]};
        end
    end

    assign in_ready=(state==IDLE) && !abort_frame && !rst;
    assign out_valid=(state==OUTPUT_TILE) && !abort_frame && !rst;

    // V107: this private payload is unowned in IDLE. Capture freely there;
    // the accepted edge captures the same tile, then every math/output state
    // holds it. Only the small owner/control state needs reset/cancellation.
    always_ff @(posedge clk)if(state==IDLE)source_tile<=in_tile;

    // OUTTILE_PRIVATE_WORDS_BEGIN: public zero/partial-word visibility is exact.
    logic [63:0] out_written;
    for(genvar out_word=0;out_word<64;out_word=out_word+1)begin: output_words
        localparam integer ROW=out_word/8, COL=out_word%8;
        localparam integer RESULT_LANE=(ROW<4?ROW:7-ROW)+4*(COL%2);
        logic [23:0] payload;
        // This storage has local math-state enables only. A simultaneous kill
        // clears visibility below; a future visible word is replaced completely.
        always_ff @(posedge clk)begin
            if(state==DC_SECOND_ACC)
                payload<=rounded({{2{products[0][37]}},products[0]});
            else if(state==SECOND_ACC && k==7 && group_index==2'(COL/2))begin
                if(ROW<4)payload<=rounded(next_even[RESULT_LANE]+next_odd[RESULT_LANE]);
                else payload<=rounded(next_even[RESULT_LANE]-next_odd[RESULT_LANE]);
            end
        end
        assign out_tile[out_word*24+:24]=out_written[out_word]?payload:24'd0;
    end
    // OUTTILE_PRIVATE_WORDS_END

    always_ff @(posedge clk) begin
        if (rst || abort_frame) begin
`ifndef SYNTHESIS
            operand_live<=0;
`endif
            for(integer p=0;p<4;p=p+1)operand_basis[p]<=0;
            state<=IDLE;
            out_written<='0;
            out_error<=1'b0;
            out_id<='0;
            group_index<='0;
            k<='0;
            dc_middle<='0;
            active_cycles<='0;
            for (lane=0; lane<8; lane=lane+1) begin
                operand_samples[lane]<='0;
                products[lane]<='0;
                even_sum[lane]<='0;
                odd_sum[lane]<='0;
            end
        end else begin
            if(prefetch_enable)begin
                for(integer p=0;p<8;p=p+1)
                    operand_samples[p]<=prefetch_dc && p!=0 ? 24'sd0 : next_samples[p/4];
                for(integer p=0;p<4;p=p+1)operand_basis[p]<=basis(prefetch_k,2'(p));
            end
`ifndef SYNTHESIS
            if(prefetch_enable)operand_live<=1;
            else if((state==IDLE && in_valid && in_ready) || state==DC_SECOND_ACC ||
                (state==SECOND_ACC && group_index==3 && k==7))operand_live<=0;
`endif
            if (state!=IDLE && state!=OUTPUT_TILE) active_cycles<=active_cycles+1;
            case (state)
                IDLE: if (in_valid && in_ready) begin
                    out_id<=in_id;
                    out_error<=input_bad;
                    active_cycles<=0;
                    group_index<=0;
                    k<=0;
                    for (lane=0; lane<8; lane=lane+1) begin
                        even_sum[lane]<=0;
                        odd_sum[lane]<=0;
                    end
                    if (input_bad || in_tile==0) begin
                        out_written<=0;
                        state<=OUTPUT_TILE;
                    end else if (in_tile[1279:20]==0) state<=DC_FIRST_MUL;
                    else state<=FIRST_MUL;
                end
                FIRST_MUL, SECOND_MUL, DC_FIRST_MUL, DC_SECOND_MUL: begin
                    for (lane=0; lane<8; lane=lane+1)
                        products[lane]<=$signed(operand_samples[lane]) * $signed(operand_basis[lane%4]);
                    case (state)
                        FIRST_MUL: state<=FIRST_ACC;
                        SECOND_MUL: state<=SECOND_ACC;
                        DC_FIRST_MUL: state<=DC_FIRST_ACC;
                        default: state<=DC_SECOND_ACC;
                    endcase
                end
                DC_FIRST_ACC: begin
                    dc_middle<=rounded({{2{products[0][37]}},products[0]});
                    state<=DC_SECOND_MUL;
                end
                DC_SECOND_ACC: begin
                    out_written<='1;
                    state<=OUTPUT_TILE;
                end
                FIRST_ACC, SECOND_ACC: begin
                    if (k==7) begin
                        for (lane=0; lane<8; lane=lane+1) begin
                            if (state==FIRST_ACC) begin
                                intermediate[(int'(group_index)*2+lane/4)*8+lane%4]
                                    <=rounded(next_even[lane]+next_odd[lane]);
                                intermediate[(int'(group_index)*2+lane/4)*8+7-lane%4]
                                    <=rounded(next_even[lane]-next_odd[lane]);
                            end else begin
                                out_written[(lane%4)*8+int'(group_index)*2+lane/4]<=1;
                                out_written[(7-lane%4)*8+int'(group_index)*2+lane/4]<=1;
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
