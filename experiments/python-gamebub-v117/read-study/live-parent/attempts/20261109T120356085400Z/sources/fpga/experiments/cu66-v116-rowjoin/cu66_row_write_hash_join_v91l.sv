// Three bounded eight-byte slots; one physical ACK lease; ordered hash drain.
// Cold power reset requires external quiescence. Warm kill retains physical debt.
module cu66_row_write_hash_join_v91l (
    input logic clk,power_on_reset,reset,cancel,start,
    input logic in_valid,output logic in_ready,
    input logic in_hud,input logic [7:0] in_data,
    input logic [31:0] in_epoch,in_fid,
    input logic [1:0] in_bank,in_plane,
    input logic [19:0] in_addr,
    input logic [12:0] in_tile,input logic [5:0] in_index,input logic in_last,
    output logic req_valid,input logic req_ready,
    output logic [31:0] req_epoch,req_token,
    output logic [1:0] req_bank,output logic [19:0] req_addr,
    output logic [63:0] req_data,output logic [3:0] req_bytes,
    input logic rsp_valid,output logic rsp_ready,
    input logic [31:0] rsp_epoch,rsp_token,
    input logic [1:0] rsp_bank,input logic [19:0] rsp_addr,input logic rsp_error,
    output logic out_valid,input logic out_ready,
    output logic out_hud,output logic [7:0] out_data,
    output logic [31:0] out_epoch,out_fid,
    output logic [1:0] out_bank,out_plane,output logic [19:0] out_addr,
    output logic [12:0] out_tile,output logic [5:0] out_index,output logic out_last,
    output logic busy,physical_pending,drained,
    output logic [2:0] state,output logic [7:0] error,
    output logic [3:0] fill_count,output logic [2:0] deliver_index,
    output logic [31:0] count_inputs,count_requests,count_acks,count_outputs,count_wrong_acks,count_drops
);
    localparam logic [2:0] IDLE=0,FILL=1,OFFER=2,WAIT_ACK=3,DELIVER=4;
    localparam logic [2:0] FREE_SLOT=0,FILL_SLOT=1,READY_SLOT=2,WAIT_SLOT=3,HASH_SLOT=4;
    logic [2:0] owner [0:2];
    logic [63:0] payload [0:2];
    logic [31:0] epochs [0:2],tokens [0:2],fids [0:2];
    logic [1:0] banks [0:2],planes [0:2];
    logic [19:0] addresses [0:2];
    logic [12:0] tiles [0:2];
    logic [5:0] indices [0:2];
    logic hud [0:2],lasts [0:2];
    logic [3:0] fills [0:2];
    logic [1:0] fill_slot,issue_slot,hash_slot,pending_slot,request_slot;
    logic [31:0] next_token;
    logic killed,kill,matching,first_ok,continuation_ok;
    logic input_fire,request_fire,response_fire,output_fire,bad_input,bad_ack,bus_error,flush;
    function automatic logic [1:0] advance(input logic [1:0] slot);
        advance=slot==2 ? 2'd0 : slot+2'd1;
    endfunction
    assign kill=reset||cancel;
    assign busy=physical_pending || owner[0]!=FREE_SLOT || owner[1]!=FREE_SLOT || owner[2]!=FREE_SLOT;
    assign drained=!busy;
    assign in_ready=(owner[fill_slot]==FREE_SLOT||owner[fill_slot]==FILL_SLOT)&&
        (!killed||!physical_pending)&&!kill&&!power_on_reset&&error==0&&!start;
    assign req_valid=!physical_pending&&owner[issue_slot]==READY_SLOT&&
        !kill&&!power_on_reset&&error==0&&!killed;
    assign request_slot=physical_pending?pending_slot:issue_slot;
    assign req_epoch=epochs[request_slot];assign req_token=tokens[request_slot];
    assign req_bank=banks[request_slot];assign req_addr=addresses[request_slot];
    assign req_data=payload[request_slot];assign req_bytes=8;
    assign rsp_ready=physical_pending&&!power_on_reset;
    assign matching=rsp_epoch==epochs[pending_slot]&&rsp_token==tokens[pending_slot]&&
        rsp_bank==banks[pending_slot]&&rsp_addr==addresses[pending_slot];
    assign out_valid=owner[hash_slot]==HASH_SLOT&&!kill&&!power_on_reset&&error==0&&!killed;
    assign out_data=payload[hash_slot][32'(deliver_index)*8+:8];
    assign out_epoch=epochs[hash_slot];assign out_fid=fids[hash_slot];
    assign out_bank=banks[hash_slot];assign out_plane=planes[hash_slot];
    assign out_hud=hud[hash_slot];assign out_tile=tiles[hash_slot];
    assign out_addr=addresses[hash_slot]+20'(deliver_index);
    assign out_index=hud[hash_slot]?indices[hash_slot]:indices[hash_slot]+6'(deliver_index);
    assign out_last=lasts[hash_slot]&&deliver_index==7;
    assign fill_count=owner[fill_slot]==FILL_SLOT?fills[fill_slot]:
        (owner[issue_slot]==READY_SLOT||physical_pending||owner[hash_slot]==HASH_SLOT?4'd8:4'd0);
    assign state=physical_pending?WAIT_ACK:owner[hash_slot]==HASH_SLOT?DELIVER:
        owner[issue_slot]==READY_SLOT?OFFER:owner[fill_slot]==FILL_SLOT?FILL:IDLE;
    assign first_ok=in_epoch!=0&&in_addr[2:0]==0&&!in_last&&
        (in_hud||(in_plane<3&&in_index[2:0]==0));
    assign continuation_ok=in_epoch==epochs[fill_slot]&&in_fid==fids[fill_slot]&&
        in_bank==banks[fill_slot]&&in_hud==hud[fill_slot]&&
        in_addr==addresses[fill_slot]+20'(fills[fill_slot])&&(!in_last||fills[fill_slot]==7)&&
        (in_hud||(in_plane==planes[fill_slot]&&in_tile==tiles[fill_slot]&&
            in_index==indices[fill_slot]+6'(fills[fill_slot])));
    assign input_fire=in_valid&&in_ready;assign request_fire=req_valid&&req_ready;
    assign response_fire=rsp_valid&&rsp_ready;assign output_fire=out_valid&&out_ready;
    assign bad_input=input_fire&&(owner[fill_slot]==FREE_SLOT?!first_ok:!continuation_ok);
    assign bad_ack=response_fire&&!matching;
    assign bus_error=response_fire&&matching&&rsp_error;
    assign flush=kill||bad_input||bad_ack||bus_error;
    always_ff @(posedge clk)begin
        if(power_on_reset)begin
            error<=0;killed<=0;next_token<=1;physical_pending<=0;
            fill_slot<=0;issue_slot<=0;hash_slot<=0;pending_slot<=0;deliver_index<=0;
            for(integer n=0;n<3;n=n+1)begin
                owner[n]<=FREE_SLOT;payload[n]<=0;epochs[n]<=0;tokens[n]<=0;
                fids[n]<=0;banks[n]<=0;planes[n]<=0;addresses[n]<=0;
                tiles[n]<=0;indices[n]<=0;hud[n]<=0;lasts[n]<=0;fills[n]<=0;
            end
            count_inputs<=0;count_requests<=0;count_acks<=0;count_outputs<=0;
            count_wrong_acks<=0;count_drops<=0;
        end else begin
            if(start&&drained&&!kill)begin
                error<=0;killed<=0;fill_slot<=0;issue_slot<=0;hash_slot<=0;deliver_index<=0;
                count_inputs<=0;count_requests<=0;count_acks<=0;count_outputs<=0;
                count_wrong_acks<=0;count_drops<=0;
            end
            if(input_fire)begin
                count_inputs<=count_inputs+1;
                if(!bad_input)begin
                    if(owner[fill_slot]==FREE_SLOT)begin
                        epochs[fill_slot]<=in_epoch;tokens[fill_slot]<=next_token;next_token<=next_token+1;
                        banks[fill_slot]<=in_bank;addresses[fill_slot]<=in_addr;payload[fill_slot]<=64'(in_data);
                        hud[fill_slot]<=in_hud;fids[fill_slot]<=in_fid;planes[fill_slot]<=in_plane;
                        tiles[fill_slot]<=in_tile;indices[fill_slot]<=in_index;lasts[fill_slot]<=0;
                        owner[fill_slot]<=FILL_SLOT;fills[fill_slot]<=1;killed<=0;
                    end else begin
                        payload[fill_slot][32'(fills[fill_slot])*8+:8]<=in_data;
                        fills[fill_slot]<=fills[fill_slot]+1;
                        if(fills[fill_slot]==7)begin
                            owner[fill_slot]<=READY_SLOT;lasts[fill_slot]<=in_last;fill_slot<=advance(fill_slot);
                        end
                    end
                end
            end
            if(request_fire)begin
                owner[issue_slot]<=WAIT_SLOT;pending_slot<=issue_slot;physical_pending<=1;
                issue_slot<=advance(issue_slot);count_requests<=count_requests+1;
            end
            if(response_fire)begin
                if(!matching)count_wrong_acks<=count_wrong_acks+1;
                else begin
                    count_acks<=count_acks+1;physical_pending<=0;
                    if(killed||error!=0||flush)begin
                        owner[pending_slot]<=FREE_SLOT;
                        fill_slot<=0;issue_slot<=0;hash_slot<=0;deliver_index<=0;
                    end else owner[pending_slot]<=HASH_SLOT;
                end
            end
            if(output_fire)begin
                count_outputs<=count_outputs+1;
                if(deliver_index==7)begin
                    owner[hash_slot]<=FREE_SLOT;hash_slot<=advance(hash_slot);deliver_index<=0;
                end else deliver_index<=deliver_index+1;
            end
            // Flush dominates all same-edge slot transitions. Only a live
            // physical lease survives, and only its matching ACK can retire it.
            if(flush)begin
                killed<=1;
                if(bad_ack)error<=8'h81;
                else if(bus_error)error<=8'h82;
                else if(bad_input)error<=owner[fill_slot]==FREE_SLOT?8'h83:8'h84;
                count_drops<=count_inputs+32'(input_fire)-count_outputs-32'(output_fire);
                for(integer n=0;n<3;n=n+1)
                    if(!((physical_pending&&pending_slot==2'(n)&&!(response_fire&&matching))||
                        (request_fire&&issue_slot==2'(n))))owner[n]<=FREE_SLOT;
                if(!physical_pending||(response_fire&&matching))begin
                    fill_slot<=0;issue_slot<=0;hash_slot<=0;deliver_index<=0;
                end
            end
        end
    end
`ifndef SYNTHESIS
    // Original local conservation obligations, strengthened for all three slots.
    always_ff @(posedge clk)if(!power_on_reset)begin
        assert(!(req_valid&&physical_pending));
        assert(count_requests>=count_acks);
        assert(count_requests-count_acks<=1);
        assert(count_outputs<=count_acks*8);
        assert(fill_count<=8);
        if(start)assert(state==IDLE&&!kill&&drained);
        if(req_valid)assert(fills[issue_slot]==8&&req_addr[2:0]==0);
        assert(fill_slot<3&&issue_slot<3&&hash_slot<3&&pending_slot<3);
        assert(count_outputs+count_drops<=count_inputs);
        if(physical_pending)assert(owner[pending_slot]==WAIT_SLOT);
        if(out_valid)assert(fills[hash_slot]==8&&owner[hash_slot]==HASH_SLOT);
        for(integer n=0;n<3;n=n+1)begin
            assert(owner[n]<=HASH_SLOT&&fills[n]<=8);
            if(owner[n]==WAIT_SLOT)assert(physical_pending&&pending_slot==2'(n));
        end
    end
    assert property(@(posedge clk)disable iff(power_on_reset)
        req_valid&&!req_ready&&!kill |=> kill||error!=0||
        (req_valid&&$stable({req_epoch,req_token,req_bank,req_addr,req_data,req_bytes})));
    assert property(@(posedge clk)disable iff(power_on_reset)
        out_valid&&!out_ready&&!kill |=> kill||error!=0||
        (out_valid&&$stable({out_hud,out_data,out_epoch,out_fid,out_bank,out_plane,out_addr,out_tile,out_index,out_last})));
    assert property(@(posedge clk)disable iff(power_on_reset)
        physical_pending&&!(response_fire&&matching) |=> physical_pending&&
        $stable({req_epoch,req_token,req_bank,req_addr,req_data}));
`endif
endmodule
