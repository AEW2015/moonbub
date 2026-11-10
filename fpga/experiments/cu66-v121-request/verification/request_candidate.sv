// Bounded one-edge read/refill queue. Queued bytes plus pending response <= 2.
module request_candidate (
    input logic clk, reset, cancel, start, clear_stats,
    input logic [31:0] start_offset, start_length, start_epoch,
    output logic req_valid,
    input logic req_ready,
    output logic [31:0] req_addr, req_epoch,
    input logic rsp_valid,
    input logic [31:0] rsp_addr, rsp_epoch,
    input logic [7:0] rsp_data,
    output logic out_valid,
    input logic out_ready,
    output logic [7:0] out_data,
    output logic out_last,
    output logic done,
    output logic [7:0] error,
    output logic active,
    output logic [1:0] fifo_count,
    output logic pending, push_event, pop_event,
    output logic [31:0] count_requests, count_responses, count_pops, count_stalls,
    output logic [31:0] count_cancel_queued, count_cancel_pending,
    output logic [1:0] max_count, max_owned
);
    logic [7:0] data [0:1];
    logic last [0:1];
    logic head, tail, pending_last;
    logic [31:0] offset, length, owner_epoch, issued, consumed, pending_addr;
    // V121: next full32 address owned by the existing start/issue edges.
    // Holds through stalls, responses, pops, completion and faults.
    logic [31:0] prepared_req_addr;
    logic blocked, response_fault, issue;
    logic [2:0] owned_after_pop, next_count, next_owned;

    assign blocked=reset||cancel||start||clear_stats;
    assign response_fault=active&&((pending&&(!rsp_valid||rsp_addr!=pending_addr||rsp_epoch!=owner_epoch))||(!pending&&rsp_valid));
    assign out_valid=active&&fifo_count!=0&&!blocked&&!response_fault;
    assign out_data=data[head];
    assign out_last=last[head];
    assign pop_event=out_valid&&out_ready;
    assign push_event=active&&pending&&rsp_valid&&!blocked&&!response_fault;
    assign owned_after_pop={1'b0,fifo_count}+{2'b0,pending}-{2'b0,pop_event};
    assign req_valid=active&&issued<length&&owned_after_pop<3'd2&&!blocked&&!response_fault;
    assign req_addr=prepared_req_addr;
    assign req_epoch=owner_epoch;
    assign issue=req_valid&&req_ready;
    assign next_count={1'b0,fifo_count}+{2'b0,push_event}-{2'b0,pop_event};
    assign next_owned=next_count+{2'b0,issue};

    always_ff @(posedge clk) begin
        if(reset||clear_stats)begin
            count_requests<=0;count_responses<=0;count_pops<=0;count_stalls<=0;
            count_cancel_queued<=0;count_cancel_pending<=0;max_count<=0;max_owned<=0;
        end else begin
            if(issue)count_requests<=count_requests+1;
            if(push_event)count_responses<=count_responses+1;
            if(pop_event)count_pops<=count_pops+1;
            if(out_valid&&!out_ready)count_stalls<=count_stalls+1;
            if(cancel||start||response_fault)begin
                count_cancel_queued<=count_cancel_queued+32'(fifo_count);
                count_cancel_pending<=count_cancel_pending+32'(pending);
            end
            if(!blocked&&!response_fault)begin
                if(next_count>3'(max_count))max_count<=next_count[1:0];
                if(next_owned>3'(max_owned))max_owned<=next_owned[1:0];
            end
        end
        if(reset||cancel||clear_stats)begin
            active<=0;done<=0;error<=0;fifo_count<=0;pending<=0;head<=0;tail<=0;
            prepared_req_addr<=0;
            offset<=0;length<=0;owner_epoch<=0;issued<=0;consumed<=0;pending_addr<=0;pending_last<=0;
        end else if(start)begin
            active<=start_length!=0;done<=start_length==0;error<=0;
            fifo_count<=0;pending<=0;head<=0;tail<=0;
            prepared_req_addr<=start_offset;
            offset<=start_offset;length<=start_length;owner_epoch<=start_epoch;
            issued<=0;consumed<=0;pending_addr<=0;pending_last<=0;
        end else if(response_fault)begin
            error<=1;active<=0;done<=0;fifo_count<=0;pending<=0;head<=0;tail<=0;
        end else if(active)begin
            pending<=issue;
            fifo_count<=next_count[1:0];
            if(issue)begin
                prepared_req_addr<=prepared_req_addr+32'd1;
                issued<=issued+1;pending_addr<=req_addr;pending_last<=issued+1==length;
            end
            if(push_event)begin data[tail]<=rsp_data;last[tail]<=pending_last;tail<=!tail;end
            if(pop_event)begin
                head<=!head;consumed<=consumed+1;
                if(out_last)begin active<=0;done<=1;end
            end
        end
    end

`ifndef SYNTHESIS
    always_ff @(posedge clk) if(!blocked)begin
        assert(prepared_req_addr==offset+issued)
            else $fatal(1,"V121 prepared full32 request owner mismatch");
    end
`endif

`ifndef SYNTHESIS
    always_ff @(posedge clk) if(!blocked)begin
        assert({1'b0,fifo_count}+{2'b0,pending}<=3'd2)else $fatal(1,"refill owner credit exceeded");
        if(!response_fault)assert(next_owned<=3'd2)else $fatal(1,"refill reservation exceeded");
        if(issue)assert(req_addr>=offset&&issued<length)else $fatal(1,"refill request span overflow");
        if(pop_event)begin
            assert(consumed<length)else $fatal(1,"extra refill byte");
            assert(out_last==(consumed+1==length))else $fatal(1,"refill last binding");
            if(out_last)assert(next_count==0&&!issue&&!pending)else $fatal(1,"tail pop with local owners remaining");
        end
    end
`endif
endmodule
