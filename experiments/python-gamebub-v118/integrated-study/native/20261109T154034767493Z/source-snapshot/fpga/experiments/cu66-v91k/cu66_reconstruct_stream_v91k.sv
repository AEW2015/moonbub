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
    // Same-edge next-status predicate, never a delayed sample of error.
    output logic fault_o,
    // Pulse equals fault_o && !top acknowledgement on the original fault edge.
    input logic fault_ack_i,
    output logic fault_pending_o,
    output logic [3:0] state,
    output logic [63:0] count_modes,count_residuals,count_outputs,count_ref_requests,count_ref_acks,
    output logic [63:0] count_copy_tiles,count_const_tiles,count_residual_tiles,count_ref_discarded,
    output logic [63:0] count_output_stalls,count_ref_wait
);
    localparam logic [3:0] IDLE=0,WAIT_ADMISSION=1,MODE_REQ=2,MODE_WAIT=3,
        RESIDUAL=4,REF_REQ=5,REF_WAIT=6,MATH_SEND=7,MATH_WAIT=8,EMIT=9,WAIT_DONE=10,COPY=11;
    logic running,snapshot_ref_valid,snapshot_key,discard_ref;
    logic [31:0] frame_epoch,frame_id,snapshot_ref_fid;
    logic [63:0] snapshot_ref_generation;
    logic [1:0] plane,mode,scale;
    logic [12:0] tile;
    logic [10:0] cached_cell;
    logic [6:0] y_column;
    logic y_odd_row;
    // fill_index reserves accepted words; count_residuals counts validated commits.
    logic [5:0] fill_index,emit_index;
    logic accepted_last;
    typedef struct packed {
        logic [31:0] epoch,child,token,expected_epoch,expected_child,expected_token;
        logic [1:0] plane,scale,expected_plane,expected_scale;
        logic [15:0] block_id,expected_block;
        logic [12:0] tile,expected_tile;
        logic [10:0] cell_id,expected_cell;
        logic [5:0] index,expected_index;
        logic signed [23:0] value;
    } residual_accept_t;
    residual_accept_t accepted_tuple;
    logic accepted_valid,checked_valid,checked_good;
    logic [5:0] checked_index;
    logic signed [23:0] checked_value;
    logic [1:0] copy_beat;
    logic [3:0] storage_copy_lane0,storage_copy_lane1;
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
    logic [31:0] tile_id,gather_tile_id;
    // Exactly two logical tile owners. The gather FSM owns owner_tail until
    // conversion is copied; owner_head independently holds ordered scanout.
    localparam logic [1:0] O_FREE=0,O_FILL=1,O_MATH=2,O_READY=3;
    logic [1:0] owner_state [0:1];
    logic owner_head,owner_tail,owner_copy,storage_copy;
    // Historical observation views; physical enables are four registered lanes.
    logic storage_copy_bank0,storage_copy_bank1;
    assign storage_copy_bank0=|storage_copy_lane0;
    assign storage_copy_bank1=|storage_copy_lane1;
    logic [1:0] owned_tiles,max_owned_tiles;
    logic [1:0] owner_plane [0:1],owner_mode [0:1];
    logic [12:0] owner_tile [0:1];
    logic [511:0] owner_pixels [0:1];
    logic [31:0] owner_math_id [0:1];
    logic owner_math_error [0:1];
    logic engine_out_valid,engine_out_error;
    logic [31:0] engine_out_id;
    logic [511:0] engine_out_pixels;
    logic response_failure;

    function automatic logic [10:0] quant_cell(input logic [1:0] p,input logic [12:0] t);
        return p==0?11'(((32'(t)/90)/2)*45+(32'(t)%90)/2):11'(t);
    endfunction
    function automatic logic safe_hidden(input logic [1:0] p,input logic [12:0] t);
        begin
            return p==0 ? ((t>=13'd633 && t<=13'd651) ||
                (t>=13'd723 && t<=13'd741) || (t>=13'd993 && t<=13'd1011) ||
                (t>=13'd1083 && t<=13'd1101) || (t>=13'd4071 && t<=13'd4110) ||
                (t>=13'd4161 && t<=13'd4200) || (t>=13'd4251 && t<=13'd4290) ||
                (t>=13'd4431 && t<=13'd4460) || (t>=13'd4521 && t<=13'd4550)) :
                (t>=13'd1046 && t<=13'd1064);
        end
    endfunction
    task automatic fail(input logic [7:0] reason);
        error<=reason;fault_o<=(reason)!=0;fault_pending_o<=(reason)!=0&&!fault_ack_i&&!fault_o;running<=0;done<=0;state<=IDLE;discard_ref<=1;
        owner_state[0]<=O_FREE;owner_state[1]<=O_FREE;
        accepted_valid<=0;checked_valid<=0;accepted_last<=0;
        storage_copy_lane0<=0;storage_copy_lane1<=0;
    endtask
    assign kill=reset||start||cancel||fault_o;
    assign busy=running||ref_pending;
    assign hidden=safe_hidden(plane,tile);
    assign gather_tile_id=32'(plane==0?0:plane==1?5400:6750)+32'(tile);
    assign tile_id=32'(out_plane==0?0:out_plane==1?5400:6750)+32'(out_tile);
    assign lookup_tile=13'(gather_tile_id);assign lookup_cell=cached_cell;
    assign lookup_req=running&&state==MODE_REQ&&owner_state[owner_tail]==O_FREE&&!kill;
    assign in_ready=running&&state==RESIDUAL&&!accepted_last&&owner_state[owner_tail]==O_FILL&&!kill;
    // These historical math_out_* views now name the completed head record,
    // independently copied from the actual engine response. The old output
    // owner assertion therefore still compares response ID against coordinates.
    assign math_out_valid=owner_state[owner_head]==O_READY;
    assign math_out_pixels=owner_pixels[owner_head];
    assign math_out_id=owner_math_id[owner_head];
    assign math_out_error=owner_math_error[owner_head];
    assign owned_tiles=2'(owner_state[0]!=O_FREE)+2'(owner_state[1]!=O_FREE);
    assign out_valid=running&&math_out_valid&&!math_out_error&&!kill;
    assign out_epoch=frame_epoch;assign out_fid=frame_id;
    assign out_plane=owner_plane[owner_head];assign out_tile=owner_tile[owner_head];assign out_mode=owner_mode[owner_head];
    assign out_index=emit_index;assign out_value=math_out_pixels[int'(emit_index)*8+:8];
    assign ref_req_valid=running&&state==REF_REQ&&!ref_pending&&!kill;
    assign ref_req_epoch=frame_epoch;assign ref_req_fid=snapshot_ref_fid;
    assign ref_req_generation=snapshot_ref_generation;assign ref_req_plane=plane;assign ref_req_tile=tile;
    assign ref_rsp_ready=ref_pending;
    assign ref_match=ref_rsp_epoch==pending_epoch&&ref_rsp_fid==pending_fid&&
        ref_rsp_generation==pending_generation&&ref_rsp_plane==pending_plane&&ref_rsp_tile==pending_tile;

    // The physical inactive-slot write has only registered local ownership.
    // On a kill edge the private copy may occur, but no logical owner is granted.
    assign storage_copy=state==COPY;
    assign owner_copy=running&&state==COPY&&copy_beat==3&&!kill;
    assign response_failure=ref_rsp_valid&&ref_rsp_ready&&!discard_ref&&running&&(!ref_match||ref_rsp_error);
    // Four real128-bit destination writes, no extra tile payload buffer. The
    // existing engine holds all512 bits until beat3 consumes its response.
    // Payloads are not reset and no partial copy acquires a logical READY owner.
    for(genvar b=0;b<2;b=b+1)begin: canonical_owners
        for(genvar w=0;w<64;w=w+1)begin: bytes
            logic [7:0] value;
            always_ff @(posedge clk)if(b==0?storage_copy_lane0[w/16]:storage_copy_lane1[w/16])value<=engine_out_pixels[w*8+:8];
            assign owner_pixels[b][w*8+:8]=value;
        end
        always_ff @(posedge clk)if(b==0?storage_copy_lane0[3]:storage_copy_lane1[3])begin
            owner_math_id[b]<=engine_out_id;owner_math_error[b]<=engine_out_error;
        end
    end
    cu66_reconstruct_tile reconstruct (
        .clk(clk),.rst(reset),.abort_i(start||cancel||fault_o),
        .in_valid(running&&state==MATH_SEND&&!kill),.in_ready(math_in_ready),
        .in_id(gather_tile_id),.in_key(snapshot_key),.in_hidden(mode==1),.in_residual(residual),
        .ref_valid(snapshot_key||mode==1||state==MATH_SEND),.ref_ready(math_ref_ready),
        .ref_tile_id(gather_tile_id),.ref_pixels(reference_pixels),
        .out_valid(engine_out_valid),.out_ready(owner_copy),
        .out_id(engine_out_id),.out_pixels(engine_out_pixels),.out_error(engine_out_error));

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
        storage_copy_lane0<=0;storage_copy_lane1<=0;
        accepted_valid<=0;checked_valid<=0;
        // Ack observes the old fault on this edge. A held fault is acknowledged.
        fault_pending_o<=0;
        if(reset||cancel||start)begin
            running<=start&&!reset&&!cancel;done<=0;error<=0;fault_o<=(0)!=0;state<=start?WAIT_ADMISSION:IDLE;
            plane<=0;tile<=0;mode<=0;scale<=0;fill_index<=0;emit_index<=0;
            accepted_last<=0;copy_beat<=0;
            cached_cell<=0;y_column<=0;y_odd_row<=0;
            owner_state[0]<=O_FREE;owner_state[1]<=O_FREE;owner_head<=0;owner_tail<=0;
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
                count_output_stalls<=0;count_ref_wait<=0;max_owned_tiles<=0;
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
            if(running&&!fault_o&&!response_failure)begin
                // Acceptance only captures whole immutable ownership; it does
                // not use validation results to write the wide residual bank.
                accepted_valid<=in_valid&&in_ready;
                if(in_valid&&in_ready)begin
                    accepted_tuple<='{epoch:in_epoch,child:in_child_epoch,token:in_token,
                        expected_epoch:frame_epoch,expected_child:residual_child,expected_token:residual_token,
                        plane:in_plane,scale:in_qscale,expected_plane:plane,expected_scale:scale,
                        block_id:in_block,expected_block:residual_block[plane],tile:in_tile,expected_tile:tile,
                        cell_id:in_qcell,expected_cell:cached_cell,index:in_index,expected_index:fill_index,value:in_value};
                    if(fill_index==0)begin residual_child<=in_child_epoch;residual_token<=in_token;end
                    if(fill_index==63)accepted_last<=1;else fill_index<=fill_index+1;
                end
                checked_valid<=accepted_valid;
                if(accepted_valid)begin
                    checked_good<=accepted_tuple.epoch==accepted_tuple.expected_epoch&&
                        accepted_tuple.plane==accepted_tuple.expected_plane&&accepted_tuple.tile==accepted_tuple.expected_tile&&
                        accepted_tuple.index==accepted_tuple.expected_index&&accepted_tuple.cell_id==accepted_tuple.expected_cell&&
                        accepted_tuple.scale==accepted_tuple.expected_scale&&accepted_tuple.block_id==accepted_tuple.expected_block&&
                        accepted_tuple.child!=0&&accepted_tuple.token!=0&&
                        (accepted_tuple.expected_index==0||(accepted_tuple.child==accepted_tuple.expected_child&&accepted_tuple.token==accepted_tuple.expected_token));
                    checked_index<=accepted_tuple.expected_index;checked_value<=accepted_tuple.value;
                end
                if(out_valid&&!out_ready)count_output_stalls<=count_output_stalls+1;
                if(ref_pending)count_ref_wait<=count_ref_wait+1;
                if(owned_tiles>max_owned_tiles)max_owned_tiles<=owned_tiles;
                if(out_valid&&out_ready)begin
                    count_outputs<=count_outputs+1;
                    if(emit_index==63)begin owner_state[owner_head]<=O_FREE;owner_head<=!owner_head;emit_index<=0;end
                    else emit_index<=emit_index+1;
                end
                case(state)
                    WAIT_ADMISSION:if(admitted_ready&&!ref_pending)begin
                        frame_id<=frame_fid;snapshot_key<=key_frame;state<=MODE_REQ;discard_ref<=0;
                    end
                    MODE_REQ:if(lookup_req&&lookup_ready)begin state<=MODE_WAIT;owner_state[owner_tail]<=O_FILL;end
                    MODE_WAIT:if(lookup_rsp)begin
                        count_modes<=count_modes+1;mode<=lookup_mode;scale<=lookup_scale;
                        owner_plane[owner_tail]<=plane;owner_tile[owner_tail]<=tile;owner_mode[owner_tail]<=lookup_mode;
                        fill_index<=0;accepted_last<=0;residual<=0;reference_pixels<=0;
                        if(lookup_mode>2||(hidden!=(lookup_mode==1))||(snapshot_key&&lookup_mode==0))fail(1);
                        else if(lookup_mode==2)begin state<=RESIDUAL;count_residual_tiles<=count_residual_tiles+1;end
                        else if(lookup_mode==1)begin state<=MATH_SEND;count_const_tiles<=count_const_tiles+1;end
                        else if(!snapshot_ref_valid)fail(2);
                        else begin state<=REF_REQ;count_copy_tiles<=count_copy_tiles+1;end
                    end
                    RESIDUAL:if(checked_valid)begin
                        if(!checked_good)fail(4);
                        else begin
                            for(integer word_index=0;word_index<64;word_index=word_index+1)begin
                                if(checked_index==6'(word_index))residual[word_index*24+:24]<=checked_value;
                            end
                            count_residuals<=count_residuals+1;
                            if(checked_index==63)begin
                                residual_block[plane]<=residual_block[plane]+1;
                                if(snapshot_key)state<=MATH_SEND;
                                else if(!snapshot_ref_valid)fail(2);
                                else state<=REF_REQ;
                            end
                        end
                    end
                    REF_REQ:if(ref_req_valid&&ref_req_ready)begin state<=REF_WAIT;count_ref_requests<=count_ref_requests+1;end
                    REF_WAIT:begin end
                    MATH_SEND:if(math_in_ready)begin state<=MATH_WAIT;owner_state[owner_tail]<=O_MATH;end
                    MATH_WAIT:if(engine_out_valid)begin
                        if(engine_out_error||engine_out_id!=gather_tile_id)fail(5);
                        else begin
                            state<=COPY;copy_beat<=0;
                            if(owner_tail)storage_copy_lane1<=4'b0001;else storage_copy_lane0<=4'b0001;
                        end
                    end
                    COPY:if(copy_beat!=3)begin
                        copy_beat<=copy_beat+1;
                        if(owner_tail)storage_copy_lane1<=4'b0001<<(copy_beat+1'b1);
                        else storage_copy_lane0<=4'b0001<<(copy_beat+1'b1);
                    end else if(owner_copy)begin
                            owner_state[owner_tail]<=O_READY;owner_tail<=!owner_tail;
                            if(tile+1==(plane==0?13'd5400:13'd1350))begin
                                tile<=0;cached_cell<=0;y_column<=0;y_odd_row<=0;
                                if(plane==2)state<=WAIT_DONE;
                                else begin plane<=plane+1;state<=MODE_REQ;end
                            end else begin
                                tile<=tile+1;state<=MODE_REQ;
                                if(plane==0)begin
                                    if(y_column==7'd89)begin
                                        y_column<=0;y_odd_row<=!y_odd_row;
                                        cached_cell<=y_odd_row?cached_cell+11'd1:cached_cell-11'd44;
                                    end else begin
                                        y_column<=y_column+7'd1;
                                        if(y_column[0])cached_cell<=cached_cell+11'd1;
                                    end
                                end else cached_cell<=cached_cell+11'd1;
                            end
                    end
                    WAIT_DONE:if(input_done&&!ref_pending&&owned_tiles==0&&!engine_out_valid)begin running<=0;done<=1;state<=IDLE;end
                    default:begin end
                endcase
                if(response_failure)begin owner_state[0]<=O_FREE;owner_state[1]<=O_FREE;end
            end
        end
    end
`ifndef SYNTHESIS
    always_ff @(posedge clk)if(owner_initialized&&!reset&&!cancel&&!start)begin
        assert(cached_cell==quant_cell(plane,tile))else $fatal(1,"cached reconstruction cell diverged");
        assert(plane<=2 && tile<(plane==0?13'd5400:13'd1350))else $fatal(1,"reconstruction coordinate range");
        if(plane==0)begin
            assert(y_column==7'(32'(tile)%90))else $fatal(1,"cached Y column diverged");
            assert(y_odd_row==1'((32'(tile)/90)%2))else $fatal(1,"cached Y row parity diverged");
        end
        if(running&&state==MATH_SEND&&math_in_ready&&!snapshot_key&&mode!=1)
            assert(math_ref_ready)else $fatal(1,"reconstruction reference handshake missing");
        if(done)assert(!running&&!ref_pending&&count_outputs==64'd518400)else $fatal(1,"canonical completion before full output/drain");
        if(out_valid)assert(math_out_id==tile_id&&!math_out_error)else $fatal(1,"canonical output owner mismatch");
        if(ref_req_valid)assert(!ref_pending&&snapshot_ref_valid&&!snapshot_key&&!hidden)else $fatal(1,"reference request ownership");
    end
`endif
`ifndef SYNTHESIS
    // Checked in all cycles, including sticky failure and retry/abort edges.
    always_ff @(posedge clk)begin
        assert(fault_o==(error!=0)) else $fatal(1,"same-edge fault/status mismatch");
    end
`endif
`ifndef SYNTHESIS
    logic copy_checked,copy_bank_checked,held_checked;
    logic [511:0] copied_pixels,held_pixels;
    logic [31:0] copied_id,held_id;
    logic copied_error,held_error;
    logic [1:0] copied_plane,held_plane,copied_mode,held_mode;
    logic [12:0] copied_tile,held_tile;
    logic [5:0] held_index;
    always_ff @(posedge clk)begin
        if(kill)begin copy_checked<=0;held_checked<=0;end
        else begin
            if(copy_checked)assert(owner_pixels[copy_bank_checked]==copied_pixels&&owner_math_id[copy_bank_checked]==copied_id&&
                owner_math_error[copy_bank_checked]==copied_error&&owner_plane[copy_bank_checked]==copied_plane&&
                owner_tile[copy_bank_checked]==copied_tile&&owner_mode[copy_bank_checked]==copied_mode)
                else $fatal(1,"reconstruction whole engine response copy mismatch");
            copy_checked<=owner_copy;
            if(owner_copy)begin
                assert(engine_out_valid&&!engine_out_error&&engine_out_id==gather_tile_id&&owner_state[owner_tail]==O_MATH)
                    else $fatal(1,"reconstruction copy without complete engine owner");
                assert(!(out_valid&&owner_head==owner_tail))else $fatal(1,"reconstruction overwrote offered head");
                copy_bank_checked<=owner_tail;copied_pixels<=engine_out_pixels;copied_id<=engine_out_id;copied_error<=engine_out_error;
                copied_plane<=owner_plane[owner_tail];copied_tile<=owner_tile[owner_tail];copied_mode<=owner_mode[owner_tail];
            end
            if(held_checked)assert(out_valid&&math_out_pixels==held_pixels&&math_out_id==held_id&&math_out_error==held_error&&
                out_plane==held_plane&&out_tile==held_tile&&out_mode==held_mode&&out_index==held_index)
                else $fatal(1,"reconstruction held head storage or owner changed");
            held_checked<=out_valid&&!out_ready;
            if(out_valid&&!out_ready)begin held_pixels<=math_out_pixels;held_id<=math_out_id;held_error<=math_out_error;
                held_plane<=out_plane;held_tile<=out_tile;held_mode<=out_mode;held_index<=out_index;end
            if(running)begin
                assert(owned_tiles<=2)else $fatal(1,"reconstruction exceeded two owners");
                assert(state!=EMIT)else $fatal(1,"reconstruction reentered legacy serialized emit state");
                if(lookup_req)assert(owner_state[owner_tail]==O_FREE)else $fatal(1,"reconstruction lookup reused owner");
                if(in_ready)assert(owner_state[owner_tail]==O_FILL)else $fatal(1,"reconstruction residual without fill owner");
                if(out_valid)assert(owner_state[owner_head]==O_READY)else $fatal(1,"reconstruction output without completed owner");
                if(state==COPY)assert(engine_out_valid)else $fatal(1,"reconstruction registered copy lost engine response");
            end
            if(done)assert(owned_tiles==0&&!engine_out_valid)else $fatal(1,"reconstruction done with private ownership");
        end
    end
`endif
`ifndef SYNTHESIS
    logic revoked_storage_copy_checked;
    always_ff @(posedge clk)begin
        if(!owner_initialized)revoked_storage_copy_checked<=0;
        else begin
            if(revoked_storage_copy_checked)assert(owner_state[0]==O_FREE&&owner_state[1]==O_FREE&&!out_valid)
                else $fatal(1,"killed private reconstruction copy acquired a logical owner");
            revoked_storage_copy_checked<=storage_copy&&kill;
            if(storage_copy)begin
                assert(owner_state[owner_tail]==O_MATH&&engine_out_valid)
                    else $fatal(1,"private reconstruction copy without reserved complete response");
                assert(owner_state[owner_head]!=O_READY||owner_tail!=owner_head)
                    else $fatal(1,"private reconstruction copy overwrote READY head");
                if(kill)assert(!owner_copy&&!out_valid)else $fatal(1,"killed reconstruction copy published");
                else assert(owner_copy==(copy_beat==3))else $fatal(1,"logical copy must wait for fourth physical beat");
            end
        end
    end
`endif
`ifndef SYNTHESIS
    // Check the prediction against the unchanged physical state/bank owner on
    // every real preedge, including COPY with external kill asserted.
    always_ff @(posedge clk)if(owner_initialized)begin
        assert(storage_copy_lane0==(storage_copy&&!owner_tail?(4'b0001<<copy_beat):4'b0000))
            else $fatal(1,"bank0 COPY lane changed physical edge");
        assert(storage_copy_lane1==(storage_copy&&owner_tail?(4'b0001<<copy_beat):4'b0000))
            else $fatal(1,"bank1 COPY lane changed physical edge");
        assert(!(storage_copy_bank0&&storage_copy_bank1))
            else $fatal(1,"COPY prediction granted both physical banks");
    end
`endif
`ifndef SYNTHESIS
    logic [6:0] accepted_words,committed_words;
    logic copy_engine_held;
    logic [511:0] copy_engine_pixels;
    logic [31:0] copy_engine_id;
    always_ff @(posedge clk)begin
        if(kill||!running||state==MODE_WAIT)begin accepted_words<=0;committed_words<=0;end
        else begin
            if(in_valid&&in_ready)begin
                assert(accepted_words<64&&fill_index==accepted_words[5:0])else $fatal(1,"residual acceptance reservation");
                accepted_words<=accepted_words+1;
            end
            if(state==RESIDUAL&&checked_valid&&checked_good)begin
                assert(committed_words<accepted_words&&checked_index==committed_words[5:0])else $fatal(1,"residual ordered validated commit");
                committed_words<=committed_words+1;
                if(checked_index==63)assert(accepted_last&&accepted_words==64&&!accepted_valid)
                    else $fatal(1,"math armed before final owned residual drained");
            end
        end
        if(kill)copy_engine_held<=0;
        else begin
            if(copy_engine_held)assert(engine_out_valid&&engine_out_pixels==copy_engine_pixels&&engine_out_id==copy_engine_id)
                else $fatal(1,"engine response changed during partial canonical copy");
            copy_engine_held<=state==COPY&&copy_beat!=3;
            if(state==COPY)begin copy_engine_pixels<=engine_out_pixels;copy_engine_id<=engine_out_id;end
        end
    end
`endif
endmodule
