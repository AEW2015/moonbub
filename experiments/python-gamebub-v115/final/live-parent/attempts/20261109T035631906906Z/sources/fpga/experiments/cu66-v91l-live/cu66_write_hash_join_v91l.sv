// One byte owner joins a real external write ACK to its hash-stream delivery.
// Warm reset/cancel drops local work but never forgets an accepted request.
module cu66_write_hash_join_v91l (
    input logic clk,power_on_reset,reset,cancel,start,
    input logic in_valid,output logic in_ready,
    input logic in_hud,input logic [7:0] in_data,
    input logic [31:0] in_epoch,in_fid,
    input logic [1:0] in_bank,in_plane,
    input logic [19:0] in_addr,
    input logic [12:0] in_tile,input logic [5:0] in_index,input logic in_last,
    output logic req_valid,input logic req_ready,
    output logic [31:0] req_epoch,req_token,
    output logic [1:0] req_bank,output logic [19:0] req_addr,output logic [7:0] req_data,
    input logic rsp_valid,output logic rsp_ready,
    input logic [31:0] rsp_epoch,rsp_token,
    input logic [1:0] rsp_bank,input logic [19:0] rsp_addr,input logic rsp_error,
    output logic out_valid,input logic out_ready,
    output logic out_hud,output logic [7:0] out_data,
    output logic [31:0] out_epoch,out_fid,
    output logic [1:0] out_bank,out_plane,output logic [19:0] out_addr,
    output logic [12:0] out_tile,output logic [5:0] out_index,output logic out_last,
    output logic busy,physical_pending,drained,
    output logic [1:0] state,output logic [7:0] error,
    output logic [31:0] count_inputs,count_requests,count_acks,count_outputs,count_wrong_acks,count_drops
);
    localparam logic [1:0] IDLE=0,OFFER=1,WAIT_ACK=2,DELIVER=3;
    logic [31:0] next_token;
    logic killed,kill,matching;
    assign kill=reset||cancel;
    assign busy=state!=IDLE;
    assign physical_pending=state==WAIT_ACK;
    assign drained=state==IDLE;
    assign in_ready=state==IDLE&&!kill&&!power_on_reset&&error==0&&!start;
    assign req_valid=state==OFFER&&!kill&&!power_on_reset&&error==0;
    assign rsp_ready=state==WAIT_ACK&&!power_on_reset;
    assign matching=rsp_epoch==req_epoch&&rsp_token==req_token&&rsp_bank==req_bank&&rsp_addr==req_addr;
    assign out_valid=state==DELIVER&&!kill&&!power_on_reset&&error==0;
    assign out_data=req_data;assign out_epoch=req_epoch;assign out_bank=req_bank;assign out_addr=req_addr;
    always_ff @(posedge clk)begin
        if(power_on_reset)begin
            state<=IDLE;error<=0;killed<=0;next_token<=1;
            req_epoch<=0;req_token<=0;req_bank<=0;req_addr<=0;req_data<=0;
            out_hud<=0;out_fid<=0;out_plane<=0;out_tile<=0;out_index<=0;out_last<=0;
            count_inputs<=0;count_requests<=0;count_acks<=0;count_outputs<=0;count_wrong_acks<=0;count_drops<=0;
        end else begin
            if(start&&state==IDLE&&!kill)begin
                error<=0;killed<=0;
                count_inputs<=0;count_requests<=0;count_acks<=0;count_outputs<=0;count_wrong_acks<=0;count_drops<=0;
            end
            if(kill)begin
                killed<=1;
                if(state==OFFER||state==DELIVER)begin state<=IDLE;count_drops<=count_drops+1;end
            end
            if(in_valid&&in_ready)begin
                req_epoch<=in_epoch;req_token<=next_token;next_token<=next_token+1;
                req_bank<=in_bank;req_addr<=in_addr;req_data<=in_data;
                out_hud<=in_hud;out_fid<=in_fid;out_plane<=in_plane;out_tile<=in_tile;out_index<=in_index;out_last<=in_last;
                state<=OFFER;killed<=0;count_inputs<=count_inputs+1;
            end
            if(req_valid&&req_ready)begin state<=WAIT_ACK;count_requests<=count_requests+1;end
            if(rsp_valid&&rsp_ready)begin
                if(!matching)begin error<=8'h81;killed<=1;count_wrong_acks<=count_wrong_acks+1;end
                else begin
                    count_acks<=count_acks+1;
                    if(rsp_error)error<=8'h82;
                    if(kill||killed||error!=0||rsp_error)begin state<=IDLE;count_drops<=count_drops+1;end
                    else state<=DELIVER;
                end
            end
            if(out_valid&&out_ready)begin state<=IDLE;count_outputs<=count_outputs+1;end
        end
    end
    always_ff @(posedge clk)if(!power_on_reset)begin
        assert(!(req_valid&&physical_pending));
        assert(count_requests>=count_acks);
        assert(count_requests-count_acks<=1);
        assert(count_outputs<=count_acks);
        if(start)assert(state==IDLE&&!kill);
    end
endmodule
