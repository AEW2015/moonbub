// Fixed profile: scale_code 0/1/2 denotes 8/16/32; 3 is invalid.
// Eight coefficient multiplies per active clock; packed raster order, index0 LSB.
module cu66_dequant (
    input logic clk, rst, abort_i,
    input logic in_valid,
    output logic in_ready,
    input logic [31:0] in_id,
    input logic [1023:0] in_coefficients,
    input logic in_chroma,
    input logic [1:0] in_scale_code,
    output logic out_valid,
    input logic out_ready,
    output logic [31:0] out_id,
    output logic [1279:0] out_dequantized,
    output logic out_error
);
    `include "cu66_quant_rom.svh"
    typedef enum logic [1:0] {IDLE, MULTIPLY, HOLD_TILE} state_t;
    state_t state;
    logic [1023:0] coefficients;
    logic chroma;
    logic [1:0] scale_code;
    logic [2:0] group_index;
    logic input_bad;
    logic [7:0] q [0:7];
    logic [8:0] scaled [0:7];
    logic signed [24:0] products [0:7];
    always_comb begin
        input_bad=(in_scale_code==3);
        for(integer i=0;i<64;i=i+1)
            if($signed(in_coefficients[i*16 +:16]) < -16'sd2048 ||
               $signed(in_coefficients[i*16 +:16]) > 16'sd2048)input_bad=1;
        for(integer lane=0;lane<8;lane=lane+1)begin
            case(scale_code)
                0:scaled[lane]=({1'b0,base_quant(chroma,{group_index,3'(lane)})}+9'd1)>>1;
                1:scaled[lane]={1'b0,base_quant(chroma,{group_index,3'(lane)})};
                2:scaled[lane]={base_quant(chroma,{group_index,3'(lane)}),1'b0};
                default:scaled[lane]=0;
            endcase
            q[lane]=(scaled[lane]>255)?8'hff:scaled[lane][7:0];
            products[lane]=$signed(coefficients[(int'(group_index)*8+lane)*16 +:16]) *
                           $signed({1'b0,q[lane]});
        end
    end
    assign in_ready=state==IDLE && !rst && !abort_i;
    assign out_valid=state==HOLD_TILE && !rst && !abort_i;
    always_ff @(posedge clk)begin
        if(rst||abort_i)begin
            state<=IDLE;coefficients<=0;chroma<=0;scale_code<=0;
            group_index<=0;out_id<=0;out_error<=0;out_dequantized<=0;
        end else case(state)
            IDLE:if(in_valid&&in_ready)begin
                coefficients<=in_coefficients;chroma<=in_chroma;scale_code<=in_scale_code;
                out_id<=in_id;out_error<=input_bad;group_index<=0;
                if(input_bad||in_coefficients==0)begin out_dequantized<=0;state<=HOLD_TILE;end
                else state<=MULTIPLY;
            end
            MULTIPLY:begin
                for(integer lane=0;lane<8;lane=lane+1)
                    out_dequantized[(int'(group_index)*8+lane)*20 +:20]<=20'(products[lane]);
                if(group_index==7)state<=HOLD_TILE;
                else group_index<=group_index+1;
            end
            HOLD_TILE:if(out_ready&&out_valid)state<=IDLE;
            default:state<=IDLE;
        endcase
    end
endmodule
