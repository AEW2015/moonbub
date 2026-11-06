// CU66 fixed-profile dequant, selection/product/store pipeline successor.
// Same one-outstanding ready/valid contract; nonzero valid tiles take 10
// work clocks instead of 8. Invalid and zero tiles retain the fast path.
module cu71_dequant_resetlight (
    input logic clk, rst, abort_i,
    input logic in_valid, output logic in_ready,
    input logic [31:0] in_id,
    input logic [1023:0] in_coefficients,
    input logic in_chroma,
    input logic [1:0] in_scale_code,
    output logic out_valid, input logic out_ready,
    output logic [31:0] out_id,
    output logic [1279:0] out_dequantized,
    output logic out_error
);
    `include "cu66_quant_rom.svh"
    typedef enum logic [1:0] {IDLE, RUN, HOLD_TILE} state_t;
    state_t state;
    logic [1023:0] coefficients;
    logic chroma;
    logic [1:0] scale_code;
    logic [2:0] issue_group;
    logic issued_all, select_valid, product_valid;
    logic [7:0] select_destination, product_destination;
    logic input_bad, fast_result;
    logic [8:0] scaled [0:7];
    logic [7:0] quantizer [0:7], selected_quantizer [0:7];
    logic signed [15:0] selected_coefficient [0:7];
    (* use_dsp = "yes" *) logic signed [24:0] product [0:7];

    always_comb begin
        input_bad=(in_scale_code==3);
        for(integer i=0;i<64;i=i+1)
            if($signed(in_coefficients[i*16 +:16]) < -16'sd2048 ||
               $signed(in_coefficients[i*16 +:16]) > 16'sd2048)input_bad=1;
        for(integer lane=0;lane<8;lane=lane+1)begin
            case(scale_code)
                0:scaled[lane]=({1'b0,base_quant(chroma,{issue_group,3'(lane)})}+9'd1)>>1;
                1:scaled[lane]={1'b0,base_quant(chroma,{issue_group,3'(lane)})};
                2:scaled[lane]={base_quant(chroma,{issue_group,3'(lane)}),1'b0};
                default:scaled[lane]=0;
            endcase
            quantizer[lane]=(scaled[lane]>255)?8'hff:scaled[lane][7:0];
        end
    end
    assign fast_result=input_bad || in_coefficients==0;
    assign in_ready=state==IDLE && !rst && !abort_i;
    assign out_valid=state==HOLD_TILE && !rst && !abort_i;

    // Payload registers deliberately have no reset; valid bits fence them.
    // ID/error/valid control retain reset; tile payload is overwritten before valid.
    always_ff @(posedge clk)begin
        if(rst||abort_i)begin
            state<=IDLE;
            issue_group<=0;issued_all<=0;select_valid<=0;product_valid<=0;
            select_destination<=0;product_destination<=0;out_id<=0;out_error<=0;
        end else case(state)
            IDLE:begin
                select_valid<=0;product_valid<=0;
                if(in_valid&&in_ready)begin
                    coefficients<=in_coefficients;chroma<=in_chroma;scale_code<=in_scale_code;
                    out_id<=in_id;out_error<=input_bad;issue_group<=0;issued_all<=0;
                    if(fast_result)state<=HOLD_TILE;else state<=RUN;
                end
            end
            RUN:begin
                select_valid<=!issued_all;
                if(!issued_all)begin
                    select_destination<=8'b1<<issue_group;
                    if(issue_group==7)issued_all<=1;else issue_group<=issue_group+1'b1;
                    for(integer lane=0;lane<8;lane=lane+1)begin
                        selected_coefficient[lane]<=coefficients[(int'(issue_group)*8+lane)*16 +:16];
                        selected_quantizer[lane]<=quantizer[lane];
                    end
                end
                product_valid<=select_valid;
                if(select_valid)begin
                    product_destination<=select_destination;
                    for(integer lane=0;lane<8;lane=lane+1)
                        product[lane]<=selected_coefficient[lane]*$signed({1'b0,selected_quantizer[lane]});
                end
                if(product_valid && product_destination[7])state<=HOLD_TILE;
            end
            HOLD_TILE:if(out_ready&&out_valid)state<=IDLE;
            default:state<=IDLE;
        endcase
    end
    // Constant slices avoid a variable-index 1280-bit output write mux.
    for(genvar group_number=0;group_number<8;group_number=group_number+1)begin:g_store
        for(genvar lane_number=0;lane_number<8;lane_number=lane_number+1)begin:g_lane
            always_ff @(posedge clk)begin
                if(!rst && !abort_i && state==IDLE && in_valid && in_ready && fast_result)
                    out_dequantized[(group_number*8+lane_number)*20 +:20]<=0;
                else if(!rst && !abort_i && state==RUN && product_valid && product_destination[group_number])
                    out_dequantized[(group_number*8+lane_number)*20 +:20]<=20'(product[lane_number]);
            end
        end
    end
endmodule
