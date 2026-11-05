`timescale 1ns/1ps
// Eight shared signed MAC lanes. Dequantization/entropy/reference fetch are upstream.
// Contract: 64 raster input samples per block, signed dequantized coefficient
// magnitude <=522240, unsigned predictor 0..255. Exact (x+8192) >>> 14 at both passes.
// Reset discards all partial work. No bank publication or clock crossing here.
module inverse_q14 #(parameter integer BYPASS = 1) (
    input wire clk, input wire rst,
    input wire in_valid, output wire in_ready,
    input wire signed [19:0] in_coeff, input wire [7:0] in_prediction,
    output wire out_valid, input wire out_ready,
    output wire [5:0] out_index, output wire out_last,
    output wire signed [23:0] out_residual, output wire [7:0] out_pixel
);
    localparam [3:0] LOAD=0, P1=1, WAIT1=2, P2=3, WAIT2=4,
        DC1=5, DCWAIT1=6, DC2=7, DCWAIT2=8, SEND=9;
    reg [3:0] state;
    reg [5:0] load_index, term, send_index;
    reg [1:0] shortcut;
    reg have_nonzero, have_ac;
    reg signed [19:0] dc;
    reg signed [23:0] dc_mid, dc_result;
    reg signed [19:0] coeff_mem [0:63];
    reg [7:0] pred_mem [0:63];
    reg signed [23:0] mid_mem [0:63];
    reg signed [23:0] result_mem [0:63];
    (* use_dsp = "yes" *) reg signed [37:0] product [0:7];
    reg signed [47:0] accum [0:7];
    reg product_valid;
    reg [1:0] product_kind;
    reg [2:0] product_group, product_k;
    reg signed [23:0] operand;
    reg [2:0] matrix_row;
    integer lane;

    function automatic signed [13:0] matrix(input [5:0] address);
        begin
            case(address)
                0,1,2,3,4,5,6,7: matrix=14'sd5793;
                8:matrix=14'sd8035;9:matrix=14'sd6811;10:matrix=14'sd4551;11:matrix=14'sd1598;
                12:matrix=-14'sd1598;13:matrix=-14'sd4551;14:matrix=-14'sd6811;15:matrix=-14'sd8035;
                16:matrix=14'sd7568;17:matrix=14'sd3135;18:matrix=-14'sd3135;19:matrix=-14'sd7568;
                20:matrix=-14'sd7568;21:matrix=-14'sd3135;22:matrix=14'sd3135;23:matrix=14'sd7568;
                24:matrix=14'sd6811;25:matrix=-14'sd1598;26:matrix=-14'sd8035;27:matrix=-14'sd4551;
                28:matrix=14'sd4551;29:matrix=14'sd8035;30:matrix=14'sd1598;31:matrix=-14'sd6811;
                32:matrix=14'sd5793;33:matrix=-14'sd5793;34:matrix=-14'sd5793;35:matrix=14'sd5793;
                36:matrix=14'sd5793;37:matrix=-14'sd5793;38:matrix=-14'sd5793;39:matrix=14'sd5793;
                40:matrix=14'sd4551;41:matrix=-14'sd8035;42:matrix=14'sd1598;43:matrix=14'sd6811;
                44:matrix=-14'sd6811;45:matrix=-14'sd1598;46:matrix=14'sd8035;47:matrix=-14'sd4551;
                48:matrix=14'sd3135;49:matrix=-14'sd7568;50:matrix=14'sd7568;51:matrix=-14'sd3135;
                52:matrix=-14'sd3135;53:matrix=14'sd7568;54:matrix=-14'sd7568;55:matrix=14'sd3135;
                56:matrix=14'sd1598;57:matrix=-14'sd4551;58:matrix=14'sd6811;59:matrix=-14'sd8035;
                60:matrix=14'sd8035;61:matrix=-14'sd6811;62:matrix=14'sd4551;63:matrix=-14'sd1598;
                default:matrix=14'sd0;
            endcase
        end
    endfunction

    function automatic signed [23:0] rounded(input signed [47:0] value);
        reg signed [47:0] shifted;
        begin shifted=(value+48'sd8192) >>> 14; rounded=shifted[23:0]; end
    endfunction

    always @* begin
        operand=24'sd0; matrix_row=term[2:0];
        case(state)
            P1:operand={{4{coeff_mem[term][19]}},coeff_mem[term]};
            P2:operand=mid_mem[{term[2:0],term[5:3]}];
            DC1:begin operand={{4{dc[19]}},dc};matrix_row=0;end
            DC2:begin operand=dc_mid;matrix_row=0;end
            default:begin end
        endcase
    end
    assign in_ready=state==LOAD;
    assign out_valid=state==SEND;
    assign out_index=send_index;
    assign out_last=send_index==6'd63;
    assign out_residual=shortcut==1 ? 24'sd0 : shortcut==2 ? dc_result : result_mem[send_index];
    wire signed [24:0] predicted=$signed({out_residual[23],out_residual})+$signed({17'd0,pred_mem[send_index]});
    assign out_pixel=predicted<25'sd0 ? 8'd0 : predicted>25'sd255 ? 8'd255 : predicted[7:0];

    always @(posedge clk) begin
        if(rst) begin
            state<=LOAD;load_index<=0;term<=0;send_index<=0;shortcut<=0;
            have_nonzero<=0;have_ac<=0;product_valid<=0;
            product_kind<=0;product_group<=0;product_k<=0;dc<=0;dc_mid<=0;dc_result<=0;
            for(lane=0;lane<8;lane=lane+1) begin product[lane]<=0;accum[lane]<=0;end
        end else begin
            product_valid<=0;
            if(product_valid) begin
                if(product_kind==2) dc_mid<=rounded({{10{product[0][37]}},product[0]});
                else if(product_kind==3) dc_result<=rounded({{10{product[0][37]}},product[0]});
                else for(lane=0;lane<8;lane=lane+1) begin
                    if(product_k==0) accum[lane]<={{10{product[lane][37]}},product[lane]};
                    else accum[lane]<=accum[lane]+{{10{product[lane][37]}},product[lane]};
                    if(product_k==7) begin
                        if(product_kind==0) mid_mem[{product_group,lane[2:0]}]<=rounded(accum[lane]+{{10{product[lane][37]}},product[lane]});
                        else result_mem[{lane[2:0],product_group}]<=rounded(accum[lane]+{{10{product[lane][37]}},product[lane]});
                    end
                end
            end
            if(state==P1 || state==P2 || state==DC1 || state==DC2) begin
                for(lane=0;lane<8;lane=lane+1) product[lane]<=operand*matrix({matrix_row,lane[2:0]});
                product_valid<=1;product_group<=term[5:3];product_k<=term[2:0];
                product_kind<=state==P1 ? 2'd0 : state==P2 ? 2'd1 : state==DC1 ? 2'd2 : 2'd3;
            end
            case(state)
                LOAD:if(in_valid) begin
                    coeff_mem[load_index]<=in_coeff;pred_mem[load_index]<=in_prediction;
                    if(load_index==0) dc<=in_coeff;
                    have_nonzero<=have_nonzero || in_coeff!=0;
                    have_ac<=have_ac || (load_index!=0 && in_coeff!=0);
                    if(load_index==63) begin
                        term<=0;send_index<=0;
                        if(BYPASS!=0 && !have_nonzero && in_coeff==0) begin shortcut<=1;state<=SEND;end
                        else if(BYPASS!=0 && !have_ac && in_coeff==0) begin shortcut<=2;state<=DC1;end
                        else begin shortcut<=0;state<=P1;end
                    end else load_index<=load_index+1'b1;
                end
                P1:if(term==63)state<=WAIT1;else term<=term+1'b1;
                WAIT1:if(!product_valid)begin term<=0;state<=P2;end
                P2:if(term==63)state<=WAIT2;else term<=term+1'b1;
                WAIT2:if(!product_valid)state<=SEND;
                DC1:state<=DCWAIT1;
                DCWAIT1:if(product_valid)state<=DC2;
                DC2:state<=DCWAIT2;
                DCWAIT2:if(product_valid)state<=SEND;
                SEND:if(out_ready) begin
                    if(send_index==63) begin
                        state<=LOAD;load_index<=0;have_nonzero<=0;have_ac<=0;shortcut<=0;
                    end else send_index<=send_index+1'b1;
                end
                default:begin state<=LOAD;load_index<=0;product_valid<=0;have_nonzero<=0;have_ac<=0;end
            endcase
        end
    end
endmodule
