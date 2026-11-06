// Actual admitted modes + signed residuals -> provisional canonical tile bytes.
// One reference request retains its physical owner across cancel and warm reset.
module cu66_reconstruct_stream_v91k (
    input logic clk, reset, start, cancel, admitted_ready, key_frame, input_done,
    input logic [31:0] epoch, frame_fid,
    input logic accepted_ref_valid,
    input logic [31:0] accepted_ref_fid,
    input logic [63:0] accepted_ref_generation,
    output logic lookup_req,
    input logic lookup_ready,
    output logic [12:0] lookup_tile,
    output logic [10:0] lookup_cell,
    input logic lookup_rsp,
    input logic [1:0] lookup_mode, lookup_scale,
    input logic in_valid,
    output logic in_ready,
    input logic [31:0] in_epoch, in_child_epoch, in_token,
    input logic [1:0] in_plane,in_qscale,
    input logic [15:0] in_block,
    input logic [12:0] in_tile,
    input logic [10:0] in_qcell,
    input logic [5:0] in_index,
    input logic signed [23:0] in_value,
    output logic out_valid,
    input logic out_ready,
    output logic [31:0] out_epoch,out_fid,
    output logic [1:0] out_plane,out_mode,
    output logic [12:0] out_tile,
    output logic [5:0] out_index,
    output logic [7:0] out_value,
    output logic ref_req_valid,
    input logic ref_req_ready,
    output logic [31:0] ref_req_epoch,ref_req_fid,
    output logic [63:0] ref_req_generation,
    output logic [1:0] ref_req_plane,
    output logic [12:0] ref_req_tile,
    input logic ref_rsp_valid,
    output logic ref_rsp_ready,
    input logic [31:0] ref_rsp_epoch,ref_rsp_fid,
    input logic [63:0] ref_rsp_generation,
    input logic [1:0] ref_rsp_plane,
    input logic [12:0] ref_rsp_tile,
    input logic [511:0] ref_rsp_pixels,
    input logic ref_rsp_error,
    output logic busy,done,ref_pending,
    output logic [7:0] error,
    output logic [3:0] state,
    output logic [63:0] count_modes,count_residuals,count_outputs,count_ref_requests,count_ref_acks,
    output logic [63:0] count_copy_tiles,count_const_tiles,count_residual_tiles,count_ref_discarded,
    output logic [63:0] count_output_stalls,count_ref_wait
);
    localparam logic [3:0] IDLE=0,WAIT_ADMISSION=1,MODE_REQ=2,MODE_WAIT=3,
        RESIDUAL=4,REF_REQ=5,REF_WAIT=6,MATH_SEND=7,MATH_WAIT=8,EMIT=9,WAIT_DONE=10;
    logic running,snapshot_ref_valid,snapshot_key,discard_ref;
    logic [31:0] frame_epoch,frame_id,snapshot_ref_fid;
    logic [63:0] snapshot_ref_generation;
    logic [1:0] plane,mode,scale;
    logic [12:0] tile;
    logic [5:0] fill_index,emit_index;
    logic [15:0] residual_block [0:2];
    logic [31:0] residual_child,residual_token;
    logic [1535:0] residual;
    logic [511:0] reference_pixels;
    logic [31:0] pending_epoch=0,pending_fid=0;
    logic [63:0] pending_generation=0;
    logic [1:0] pending_plane=0;
    logic [12:0] pending_tile=0;
    logic owner_initialized=0;
    logic ref_match,kill,hidden;
    logic math_in_ready,math_out_valid,math_out_error,math_ref_ready;
    logic [31:0] math_out_id;
    logic [511:0] math_out_pixels;
    logic [31:0] tile_id;

    function automatic logic [10:0] quant_cell(input logic [1:0] p,input logic [12:0] t);
        return p==0?11'(((32'(t)/90)/2)*45+(32'(t)%90)/2):11'(t);
    endfunction
    function automatic logic safe_hidden(input logic [1:0] p,input logic [12:0] t);
        integer x,y;
        begin
            x=32'(t)%(p==0?90:45);y=32'(t)/(p==0?90:45);
            return p==0?((x>=3&&x<22&&((y>=7&&y<9)||(y>=11&&y<13)))||
                (x>=21&&x<61&&y>=45&&y<48)||(x>=21&&x<51&&y>=49&&y<51)):
                (x>=11&&x<30&&y==23);
        end
    endfunction
    task automatic fail(input logic [7:0] reason);
        error<=reason;running<=0;done<=0;state<=IDLE;discard_ref<=1;
    endtask
    assign kill=reset||start||cancel||error!=0;
    assign busy=running||ref_pending;
    assign hidden=safe_hidden(plane,tile);
    assign tile_id=32'(plane==0?0:plane==1?5400:6750)+32'(tile);
    assign lookup_tile=13'(tile_id);assign lookup_cell=quant_cell(plane,tile);
    assign lookup_req=running&&state==MODE_REQ&&!kill;
    assign in_ready=running&&state==RESIDUAL&&!kill;
    assign out_valid=running&&state==EMIT&&math_out_valid&&!math_out_error&&!kill;
    assign out_epoch=frame_epoch;assign out_fid=frame_id;
    assign out_plane=plane;assign out_tile=tile;assign out_mode=mode;
    assign out_index=emit_index;assign out_value=math_out_pixels[int'(emit_index)*8+:8];
    assign ref_req_valid=running&&state==REF_REQ&&!ref_pending&&!kill;
    assign ref_req_epoch=frame_epoch;assign ref_req_fid=snapshot_ref_fid;
    assign ref_req_generation=snapshot_ref_generation;assign ref_req_plane=plane;assign ref_req_tile=tile;
    assign ref_rsp_ready=ref_pending;
    assign ref_match=ref_rsp_epoch==pending_epoch&&ref_rsp_fid==pending_fid&&
        ref_rsp_generation==pending_generation&&ref_rsp_plane==pending_plane&&ref_rsp_tile==pending_tile;

    cu66_reconstruct_tile reconstruct (
        .clk(clk),.rst(reset),.abort_i(start||cancel||error!=0),
        .in_valid(running&&state==MATH_SEND&&!kill),.in_ready(math_in_ready),
        .in_id(tile_id),.in_key(snapshot_key),.in_hidden(mode==1),.in_residual(residual),
        .ref_valid(snapshot_key||mode==1||state==MATH_SEND),.ref_ready(math_ref_ready),
        .ref_tile_id(tile_id),.ref_pixels(reference_pixels),
        .out_valid(math_out_valid),.out_ready(running&&state==EMIT&&out_ready&&emit_index==63&&!kill),
        .out_id(math_out_id),.out_pixels(math_out_pixels),.out_error(math_out_error));

    // Physical response ownership survives local reset/cancellation. Declaration
    // initialization only establishes power-on empty, not a warm-reset flush.
    initial ref_pending=0;
    always_ff @(posedge clk)begin
        owner_initialized<=1;
        if(ref_req_valid&&ref_req_ready)begin
            ref_pending<=1;pending_epoch<=ref_req_epoch;pending_fid<=ref_req_fid;
            pending_generation<=ref_req_generation;pending_plane<=ref_req_plane;pending_tile<=ref_req_tile;
        end
        if(ref_rsp_valid&&ref_rsp_ready&&ref_match)ref_pending<=0;
    end

    always_ff @(posedge clk)begin
        if(reset||cancel||start)begin
            running<=start&&!reset&&!cancel;done<=0;error<=0;state<=start?WAIT_ADMISSION:IDLE;
            plane<=0;tile<=0;mode<=0;scale<=0;fill_index<=0;emit_index<=0;
            residual<=0;reference_pixels<=0;residual_child<=0;residual_token<=0;
            residual_block[0]<=0;residual_block[1]<=0;residual_block[2]<=0;
            discard_ref<=1;
            if(start)begin
                frame_epoch<=epoch;frame_id<=frame_fid;snapshot_ref_valid<=accepted_ref_valid;
                snapshot_ref_fid<=accepted_ref_fid;snapshot_ref_generation<=accepted_ref_generation;
            end
            if(reset||start)begin
                count_modes<=0;count_residuals<=0;count_outputs<=0;count_ref_requests<=0;count_ref_acks<=0;
                count_copy_tiles<=0;count_const_tiles<=0;count_residual_tiles<=0;count_ref_discarded<=0;
                count_output_stalls<=0;count_ref_wait<=0;
            end
        end else begin
            if(ref_rsp_valid&&ref_rsp_ready)begin
                if(ref_match)begin
                    count_ref_acks<=count_ref_acks+1;
                    if(discard_ref||!running)count_ref_discarded<=count_ref_discarded+1;
                    else if(ref_rsp_error)fail(3);
                    else begin reference_pixels<=ref_rsp_pixels;state<=MATH_SEND;end
                end else if(running&&!discard_ref)fail(3);
            end
            if(running&&error==0)begin
                if(out_valid&&!out_ready)count_output_stalls<=count_output_stalls+1;
                if(ref_pending)count_ref_wait<=count_ref_wait+1;
                case(state)
                    WAIT_ADMISSION:if(admitted_ready)begin
                        frame_id<=frame_fid;snapshot_key<=key_frame;state<=MODE_REQ;discard_ref<=0;
                    end
                    MODE_REQ:if(lookup_ready)state<=MODE_WAIT;
                    MODE_WAIT:if(lookup_rsp)begin
                        count_modes<=count_modes+1;mode<=lookup_mode;scale<=lookup_scale;
                        fill_index<=0;residual<=0;reference_pixels<=0;
                        if(lookup_mode>2||(hidden!=(lookup_mode==1))||(snapshot_key&&lookup_mode==0))fail(1);
                        else if(lookup_mode==2)begin state<=RESIDUAL;count_residual_tiles<=count_residual_tiles+1;end
                        else if(lookup_mode==1)begin state<=MATH_SEND;count_const_tiles<=count_const_tiles+1;end
                        else if(!snapshot_ref_valid)fail(2);
                        else begin state<=REF_REQ;count_copy_tiles<=count_copy_tiles+1;end
                    end
                    RESIDUAL:if(in_valid&&in_ready)begin
                        if(in_epoch!=frame_epoch||in_plane!=plane||in_tile!=tile||in_index!=fill_index||
                           in_qcell!=quant_cell(plane,tile)||in_qscale!=scale||in_block!=residual_block[plane]||
                           in_child_epoch==0||in_token==0||(fill_index!=0&&(in_child_epoch!=residual_child||in_token!=residual_token)))fail(4);
                        else begin
                            residual[int'(fill_index)*24+:24]<=in_value;count_residuals<=count_residuals+1;
                            if(fill_index==0)begin residual_child<=in_child_epoch;residual_token<=in_token;end
                            if(fill_index==63)begin
                                residual_block[plane]<=residual_block[plane]+1;
                                if(snapshot_key)state<=MATH_SEND;
                                else if(!snapshot_ref_valid)fail(2);
                                else state<=REF_REQ;
                            end else fill_index<=fill_index+1;
                        end
                    end
                    REF_REQ:if(ref_req_valid&&ref_req_ready)begin state<=REF_WAIT;count_ref_requests<=count_ref_requests+1;end
                    REF_WAIT:begin end
                    MATH_SEND:if(math_in_ready)state<=MATH_WAIT;
                    MATH_WAIT:if(math_out_valid)begin
                        if(math_out_error||math_out_id!=tile_id)fail(5);
                        else begin emit_index<=0;state<=EMIT;end
                    end
                    EMIT:if(out_valid&&out_ready)begin
                        count_outputs<=count_outputs+1;
                        if(emit_index==63)begin
                            emit_index<=0;
                            if(tile+1==(plane==0?13'd5400:13'd1350))begin
                                tile<=0;
                                if(plane==2)state<=WAIT_DONE;
                                else begin plane<=plane+1;state<=MODE_REQ;end
                            end else begin tile<=tile+1;state<=MODE_REQ;end
                        end else emit_index<=emit_index+1;
                    end
                    WAIT_DONE:if(input_done&&!ref_pending)begin running<=0;done<=1;state<=IDLE;end
                    default:begin end
                endcase
            end
        end
    end
`ifndef SYNTHESIS
    always_ff @(posedge clk)if(owner_initialized&&!reset&&!cancel&&!start)begin
        if(running&&state==MATH_SEND&&math_in_ready&&!snapshot_key&&mode!=1)
            assert(math_ref_ready)else $fatal(1,"reconstruction reference handshake missing");
        if(done)assert(!running&&!ref_pending&&count_outputs==64'd518400)else $fatal(1,"canonical completion before full output/drain");
        if(out_valid)assert(math_out_id==tile_id&&!math_out_error)else $fatal(1,"canonical output owner mismatch");
        if(ref_req_valid)assert(!ref_pending&&snapshot_ref_valid&&!snapshot_key&&!hidden)else $fatal(1,"reference request ownership");
    end
`endif
endmodule
