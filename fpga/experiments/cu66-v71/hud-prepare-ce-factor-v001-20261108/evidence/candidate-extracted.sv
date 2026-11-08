`timescale 1ns/1ps
module ce_candidate #(parameter integer WATCHDOG_CYCLES=32'd3000000000)(input wire [3:0] state,input wire  rst,input wire  abort_i,input wire  abort_allowed,input wire  hud_pending,input wire  hud_requested,input wire  p_error,input wire  bank_error,input wire  b_error,input wire [7:0] p_code,input wire [7:0] bank_code,input wire [7:0] b_code,input wire  hud_result_valid,input wire [63:0] hud_result_generation,input wire [31:0] hud_result_frame_id,input wire [31:0] hud_result_reference_id,input wire [127:0] hud_result_tag,input wire [15:0] hud_result_words,input wire  hud_result_success,input wire  hud_drain_valid,input wire [63:0] hud_drain_generation,input wire [31:0] hud_drain_frame_id,input wire [1:0] hud_drain_bank,input wire [127:0] hud_drain_tag,input wire [15:0] hud_drain_words,input wire  hud_drain_success,input wire [63:0] active_generation,input wire [31:0] fid,input wire [31:0] rid,input wire [127:0] hud_expected,input wire [1:0] bank_write,input wire  cache_prepare_result_valid,input wire  cache_prepare_match,input wire  cache_prepare_result_success,input wire  ref_rsp_valid,input wire  ref_match,input wire  ref_rsp_error,input wire  q_rsp_valid,input wire [10:0] q_rsp_index,input wire [10:0] q_expected_index,input wire  packet_pending,input wire  p_req_valid,input wire  b_req_valid,input wire [16:0] calculated_packet_address,input wire [15:0] packet_length,input wire [31:0] age,output wire hud_prepare_valid,output logic fatal,output logic [7:0]fatal_code,output logic fatal_non_hud,output wire capture_effective);
localparam [3:0] IDLE=4'd0,PARSER_START=4'd1,METADATA=4'd2,WAIT_BANK=4'd3,BASE_START=4'd4,BASE_RUN=4'd5,WAIT_CACHE=4'd6,CACHE_PREPARE_START=4'd7,CACHE_PREPARE_RUN=4'd8,COMMIT_READY=4'd9,COMMIT_ACK=4'd10,DRAIN=4'd11;
wire kill,hud_match,hud_write_match;
assign kill=(abort_i&&abort_allowed)||state==DRAIN;
assign hud_match=hud_requested&&hud_result_generation==active_generation&&
        hud_result_frame_id==fid;
assign hud_write_match=hud_requested&&hud_drain_generation==active_generation&&
        hud_drain_frame_id==fid;
assign hud_prepare_valid=(state==BASE_START||state==BASE_RUN)&&!hud_requested&&!kill&&!fatal_non_hud;
always_comb begin
fatal=0;fatal_code=0;
        if(state!=IDLE&&state!=DRAIN&&state!=COMMIT_ACK)begin
            if(state==METADATA&&p_error)begin fatal=1;fatal_code=8'h10|(p_code&8'h0f);end
            else if(state==WAIT_BANK&&bank_error)begin fatal=1;fatal_code=8'h20|(bank_code&8'h0f);end
            else if((state==BASE_RUN)&&b_error)begin fatal=1;fatal_code=b_code;end
            else if(hud_result_valid&&hud_match&&(!hud_result_success||
                hud_result_reference_id!=rid||hud_result_words!=21120||hud_result_tag!=hud_expected))
                begin fatal=1;fatal_code=8'h70;end
            else if(hud_drain_valid&&hud_write_match&&(!hud_drain_success||
                hud_drain_bank!=bank_write||hud_drain_words!=21120||hud_drain_tag!=hud_expected))
                begin fatal=1;fatal_code=8'h71;end
            else if(state==CACHE_PREPARE_RUN&&cache_prepare_result_valid&&cache_prepare_match&&!cache_prepare_result_success)
                begin fatal=1;fatal_code=8'h72;end
            else if(ref_rsp_valid&&ref_match&&ref_rsp_error)begin fatal=1;fatal_code=8'h73;end
            else if(q_rsp_valid&&q_rsp_index!=q_expected_index)begin fatal=1;fatal_code=8'h74;end
            else if(!packet_pending&&(p_req_valid||b_req_valid)&&
                calculated_packet_address>={1'b0,packet_length[15:0]})begin fatal=1;fatal_code=8'h75;end
            else if(WATCHDOG_CYCLES!=0&&age>=32'(WATCHDOG_CYCLES))begin fatal=1;fatal_code=8'h7f;end
        end
    end

    always_comb begin
        fatal_non_hud=0;
        if(state!=IDLE&&state!=DRAIN&&state!=COMMIT_ACK)begin
            if(state==METADATA&&p_error)begin fatal_non_hud=1;end
            else if(state==WAIT_BANK&&bank_error)begin fatal_non_hud=1;end
            else if((state==BASE_RUN)&&b_error)begin fatal_non_hud=1;end
            else if(state==CACHE_PREPARE_RUN&&cache_prepare_result_valid&&cache_prepare_match&&!cache_prepare_result_success)
                begin fatal_non_hud=1;end
            else if(ref_rsp_valid&&ref_match&&ref_rsp_error)begin fatal_non_hud=1;end
            else if(q_rsp_valid&&q_rsp_index!=q_expected_index)begin fatal_non_hud=1;end
            else if(!packet_pending&&(p_req_valid||b_req_valid)&&
                calculated_packet_address>={1'b0,packet_length[15:0]})begin fatal_non_hud=1;end
            else if(WATCHDOG_CYCLES!=0&&age>=32'(WATCHDOG_CYCLES))begin fatal_non_hud=1;end
        end
    end

assign capture_effective=!rst&&hud_prepare_valid&&!hud_pending;
endmodule
