// One outstanding byte lease and one physical aligned 128-bit read owner.
// Three plane-specific line slots preserve partial Cb/Cr rows across switches.
module canonical_line_reader (
    input logic clk,reset,start,cancel,finish,
    input logic [31:0] start_epoch,
    output logic start_ready,busy,draining,
    output logic [7:0] error,
    input logic probe_valid,
    input logic [18:0] probe_addr,
    input logic [31:0] probe_epoch,
    output logic probe_hit,
    output logic [7:0] probe_data,
    input logic byte_req_valid,
    output logic byte_req_ready,
    input logic [18:0] byte_req_addr,
    input logic [31:0] byte_req_epoch,
    output logic byte_rsp_valid,
    input logic byte_rsp_ready,
    output logic [7:0] byte_rsp_data,
    output logic [31:0] byte_rsp_epoch,
    output logic byte_rsp_error,
    output logic mem_req_valid,
    input logic mem_req_ready,
    output logic [18:0] mem_req_addr,
    output logic [31:0] mem_req_epoch,
    input logic mem_rsp_valid,
    output logic mem_rsp_ready,
    input logic [127:0] mem_rsp_data,
    input logic [31:0] mem_rsp_epoch,
    input logic mem_rsp_error,
    output logic [1:0] state,
    output logic physical_pending,byte_pending,
    output logic [2:0] line_valid,
    output logic [18:0] line_address [0:2],
    output logic [63:0] count_byte_requests,count_hits,count_misses,
    output logic [63:0] count_physical_requests,count_physical_responses
);
    localparam logic [1:0] IDLE=0, OFFER=1, WAIT_LINE=2;
    logic active;
    logic pending=1'b0;
    initial byte_pending=0;
    logic [31:0] epoch;
    logic [3:0] owned_offset;
    logic [18:0] owned_line;
    logic [1:0] owned_plane;
    logic [127:0] line_data [0:2];
    logic [1:0] request_plane;
    logic [18:0] request_line;
    logic request_hit;
    logic [1:0] probe_plane;
    assign probe_plane=probe_addr<345600?2'd0:probe_addr<432000?2'd1:2'd2;
    // A read-only view of the existing three 16B plane slots: zero new payload.
    assign probe_hit=probe_valid&&active&&state==IDLE&&!pending&&!byte_pending&&!byte_rsp_valid&&
        !reset&&!cancel&&!start&&!finish&&error==0&&probe_epoch==epoch&&probe_addr<518400&&
        line_valid[probe_plane]&&line_address[probe_plane]=={probe_addr[18:4],4'b0};
    assign probe_data=probe_hit?line_data[probe_plane][8*probe_addr[3:0]+:8]:8'd0;
    assign request_plane=byte_req_addr<345600?2'd0:byte_req_addr<432000?2'd1:2'd2;
    assign request_line={byte_req_addr[18:4],4'b0};
    assign request_hit=line_valid[request_plane]&&line_address[request_plane]==request_line;
    assign physical_pending=pending;
    assign busy=active||pending||byte_pending||byte_rsp_valid;
    assign draining=!active&&(pending||byte_pending||byte_rsp_valid);
    assign start_ready=!busy&&!reset&&!cancel;
    assign byte_req_ready=active&&!byte_pending&&!byte_rsp_valid&&!pending&&state==IDLE&&!reset&&!cancel&&error==0;
    assign mem_req_valid=active&&state==OFFER&&!pending&&!reset&&!cancel&&error==0;
    assign mem_req_addr=owned_line;
    assign mem_req_epoch=epoch;
    assign mem_rsp_ready=pending;

    always_ff @(posedge clk)begin
        if(reset||cancel)begin
            active<=0;state<=IDLE;error<=0;line_valid<=0;
            // The inner byte lease is retired locally, but physical bus work
            // stays owned until its matching ACK even after inner cancellation.
            if(byte_pending)begin
                if(byte_rsp_valid&&byte_rsp_ready)begin byte_rsp_valid<=0;byte_pending<=0;end
                else begin byte_rsp_valid<=1;byte_rsp_error<=1;byte_rsp_epoch<=epoch;byte_rsp_data<=0;end
            end else byte_rsp_valid<=0;
            if(pending&&mem_rsp_valid&&mem_rsp_epoch==epoch)pending<=0;
            if(reset)begin
                count_byte_requests<=0;count_hits<=0;count_misses<=0;
                count_physical_requests<=0;count_physical_responses<=0;
            end
        end else begin
            if(byte_rsp_valid&&byte_rsp_ready)begin byte_rsp_valid<=0;byte_pending<=0;end
            if(pending&&mem_rsp_valid)begin
                if(mem_rsp_epoch==epoch)begin pending<=0;count_physical_responses<=count_physical_responses+1;end
                if(active)begin
                    if(mem_rsp_error||mem_rsp_epoch!=epoch)begin
                        active<=0;state<=IDLE;line_valid<=0;error<=mem_rsp_error?8'd2:8'd1;
                        byte_rsp_valid<=byte_pending;byte_rsp_data<=0;byte_rsp_error<=1;byte_rsp_epoch<=epoch;
                    end else begin
                        line_data[owned_plane]<=mem_rsp_data;
                        line_address[owned_plane]<=owned_line;line_valid[owned_plane]<=1;
                        byte_rsp_data<=mem_rsp_data[int'(owned_offset)*8+:8];
                        byte_rsp_epoch<=epoch;byte_rsp_error<=0;byte_rsp_valid<=1;state<=IDLE;
                    end
                end
            end
            if(start&&start_ready)begin
                active<=start_epoch!=0;epoch<=start_epoch;state<=IDLE;
                error<=start_epoch!=0?8'd0:8'd3;line_valid<=0;
                byte_pending<=0;byte_rsp_valid<=0;byte_rsp_error<=0;byte_rsp_data<=0;byte_rsp_epoch<=start_epoch;
                count_byte_requests<=0;count_hits<=0;count_misses<=0;
                count_physical_requests<=0;count_physical_responses<=0;
            end else if(active)begin
                if(finish&&!pending&&!byte_pending&&!byte_rsp_valid)active<=0;
                if(byte_req_valid&&byte_req_ready)begin
                    count_byte_requests<=count_byte_requests+1;byte_pending<=1;
                    owned_offset<=byte_req_addr[3:0];owned_line<=request_line;owned_plane<=request_plane;
                    if(byte_req_addr>=518400||byte_req_epoch!=epoch)begin
                        active<=0;line_valid<=0;state<=IDLE;error<=4;
                        byte_rsp_data<=0;byte_rsp_epoch<=byte_req_epoch;byte_rsp_error<=1;byte_rsp_valid<=1;
                    end else if(request_hit)begin
                        count_hits<=count_hits+1;
                        byte_rsp_data<=line_data[request_plane][int'(byte_req_addr[3:0])*8+:8];
                        byte_rsp_epoch<=epoch;byte_rsp_error<=0;byte_rsp_valid<=1;
                    end else begin count_misses<=count_misses+1;state<=OFFER;end
                end
                if(mem_req_valid&&mem_req_ready)begin
                    pending<=1;state<=WAIT_LINE;count_physical_requests<=count_physical_requests+1;
                end
            end
        end
    end
`ifndef SYNTHESIS
    always_ff @(posedge clk)if(!reset&&!cancel)begin
        if(mem_req_valid)assert(!pending&&byte_pending&&mem_req_addr[3:0]==0&&mem_req_addr<=518384)else $fatal(1,"line read offer ownership/range");
        if(byte_rsp_valid)assert(byte_pending)else $fatal(1,"byte response without owner");
        if(byte_req_ready)assert(!pending&&!byte_pending&&!byte_rsp_valid)else $fatal(1,"byte lease overwritten");
    end
`endif
endmodule
