// Actual C2 Merkle root / semantic-HUD hash / frame seal and atomic ownership.
// HUD decoding is an explicit software endpoint; bytes below are hashed by RTL.
module cs88_validate_publish_v91l (
    input logic clk,power_on_reset,reset,abort_i,
    input logic start_valid,
    output logic start_ready,
    input logic [31:0] start_epoch,start_fid,start_refid,
    input logic [63:0] start_generation,
    input logic start_key,
    input logic [255:0] start_expected_root,start_expected_seal,
    input logic pixel_valid,
    output logic pixel_ready,
    input logic [7:0] pixel_data,
    input logic [31:0] pixel_epoch,
    input logic [1:0] pixel_plane,
    input logic [12:0] pixel_tile,
    input logic [5:0] pixel_index,
    input logic pixel_last,
    input logic hud_receipt_valid,
    output logic hud_receipt_ready,
    input logic hud_decoded_verified,
    input logic [31:0] hud_receipt_epoch,hud_receipt_fid,hud_receipt_refid,
    input logic [63:0] hud_receipt_generation,
    input logic [255:0] hud_receipt_sha256,
    input logic hud_valid,
    output logic hud_ready,
    input logic [7:0] hud_data,
    input logic hud_last,
    input logic [31:0] hud_epoch,hud_fid,hud_refid,
    input logic [63:0] hud_generation,
    input logic producer_done,producer_error,
    input logic [31:0] producer_epoch,
    input logic writes_drained,vblank,scanout_drained,
    output logic busy,done,
    output logic [7:0] error,
    output logic [3:0] state,
    output logic [31:0] frame_epoch,frame_fid,
    output logic [63:0] frame_generation,
    output logic [255:0] computed_root,computed_hud,computed_seal,
    output logic accepted_valid,
    output logic [31:0] accepted_fid,
    output logic [63:0] accepted_generation,
    output logic [255:0] accepted_root,accepted_hud,accepted_seal,
    output logic [1:0] write_bank,reference_bank,front_bank,pending_bank,
    output logic reference_bank_valid,front_valid,pending_valid,
    output logic [31:0] front_fid,pending_fid,
    output logic frame_committed,frame_presented,
    output logic bank_active,bank_aborting,
    output logic [31:0] pixel_bytes,hud_bytes,hash_jobs,hash_message_bytes,hash_blocks,
    output logic hash_result,
    output logic [2:0] hash_job_kind,
    output logic [9:0] hash_job_node,
    output logic [255:0] hash_digest
);
    localparam logic [3:0] IDLE=0,BEGIN_JOB=1,SEND_HEADER=2,SEND_PIXELS=3,
        SEND_HUD=4,SEND_FIXED=5,WAIT_HASH=6,COMMIT=7,DRAIN=8;
    localparam logic [2:0] LEAF=0,EMPTY_LEAF=1,NODE=2,HUD=3,SEAL=4;
    localparam logic [255:0] CONTEXT=256'h286386153d5fd535a7aabf60493040f99831315d6e107d7242bc39872b18d6b0;
    logic frame_key,have_hud_receipt;
    logic [31:0] frame_refid;
    logic [255:0] expected_root,expected_seal,previous_root,receipt_hud;
    logic [255:0] nodes [0:1023];
    logic [255:0] node_left,node_right;
    logic [2:0] job;
    logic [9:0] leaf_number,node_width,node_index,empty_index;
    logic [3:0] node_level;
    logic [1:0] plane,leaf_plane;
    logic [12:0] tile,leaf_start;
    logic [5:0] byte_index;
    logic [4:0] leaf_count;
    logic [15:0] message_pos,message_length;
    logic sha_start,sha_start_ready,sha_data_valid,sha_data_ready,sha_data_last,sha_valid;
    logic [7:0] sha_data;
    logic [255:0] sha_digest;
    logic sha_error,sha_busy;
    logic [31:0] sha_accepted_bytes,sha_blocks;
    logic [31:0] unused_sha_rounds,unused_sha_padding,unused_sha_input_stalls,unused_sha_output_stalls;
    logic unused_sha_aborted;
    logic [7:0] unused_sha_error_code;
    logic [2:0] unused_sha_fill;
    logic [1:0] unused_sha_core;
    logic kill,invalid_start,pixel_tuple_ok,hud_tuple_ok,receipt_tuple_ok;
    logic bank_begin_ready,bank_commit_ready,bank_commit_valid,bank_begin_valid;
    logic bank_ref_valid;
    logic [31:0] bank_ref_fid;
    logic unused_read_bank_valid,unused_begin_accepted,unused_aborted,unused_bank_error;
    logic [1:0] unused_read_bank;
    logic [7:0] unused_bank_error_code;
    logic [31:0] unused_bank_accepted,unused_bank_presented;

    function automatic logic [7:0] digest_byte(input logic [255:0] value,input integer index);
        return value[(31-index)*8+:8];
    endfunction
    function automatic logic [7:0] domain_byte(input integer index,input logic [7:0] kind);
        case(index)
            0:return "C";1:return "U";2:return "6";3:return "6";4:return "V";
            5:return "8";6:return "2";7:return "C";8:return "2";10:return kind;
            default:return 0;
        endcase
    endfunction
    function automatic logic [4:0] group_count(input logic [1:0] p,input logic [12:0] t);
        integer remaining;
        remaining=(p==0?5400:1350)-32'(t);
        return remaining>=16?5'd16:5'(remaining);
    endfunction
    function automatic logic [7:0] fixed_byte(input logic [2:0] kind,input integer index);
        logic [7:0] letter;
        letter=kind==LEAF?"L":kind==EMPTY_LEAF?"E":kind==NODE?"N":"S";
        if(index<12)return domain_byte(index,letter);
        if(kind!=NODE&&index<44)return digest_byte(CONTEXT,index-12);
        if(kind==LEAF)begin
            if(index==44)return {6'd0,leaf_plane};
            if(index>=45&&index<49)return 8'(32'(leaf_start)>>((48-index)*8));
            if(index==49)return 0;
            return {3'd0,leaf_count};
        end
        if(kind==EMPTY_LEAF)begin
            if(index<48)return 8'(32'(empty_index)>>((47-index)*8));
            return 8'(32'd512>>((51-index)*8));
        end
        if(kind==NODE)begin
            if(index<14)return 8'(16'(node_level)>>((13-index)*8));
            if(index<18)return 8'(32'(node_index)>>((17-index)*8));
            if(index<50)return digest_byte(node_left,index-18);
            return digest_byte(node_right,index-50);
        end
        if(index<48)return 8'(frame_fid>>((47-index)*8));
        if(index<52)return 8'(frame_refid>>((51-index)*8));
        if(index==52)return {7'd0,frame_key};
        if(index<61)return 8'(frame_generation>>((60-index)*8));
        if(index<93)return digest_byte(previous_root,index-61);
        if(index<125)return digest_byte(computed_hud,index-93);
        return digest_byte(computed_root,index-125);
    endfunction
    task automatic fail(input logic [7:0] reason);
        error<=reason;state<=DRAIN;done<=0;
    endtask

    assign kill=power_on_reset||reset||abort_i||state==DRAIN||error!=0;
    assign busy=state!=IDLE||bank_active;
    assign start_ready=state==IDLE&&bank_begin_ready&&!power_on_reset&&!reset&&!abort_i;
    assign invalid_start=start_epoch==0||start_generation==0||start_fid==32'hffffffff||
        (accepted_valid&&(start_generation<=accepted_generation||start_fid<=accepted_fid))||
        (start_key?start_refid!=32'hffffffff:(!accepted_valid||start_refid!=accepted_fid));
    assign bank_begin_valid=start_valid&&start_ready&&!invalid_start;
    assign bank_commit_valid=state==COMMIT&&writes_drained&&producer_done&&producer_epoch==frame_epoch&&!kill;
    assign accepted_valid=bank_ref_valid;
    assign accepted_fid=bank_ref_fid;
    assign pixel_tuple_ok=pixel_epoch==frame_epoch&&pixel_plane==plane&&pixel_tile==tile&&pixel_index==byte_index&&
        pixel_last==(pixel_bytes==518399);
    assign hud_tuple_ok=hud_epoch==frame_epoch&&hud_fid==frame_fid&&hud_refid==frame_refid&&hud_generation==frame_generation&&
        hud_last==(hud_bytes==42239);
    assign receipt_tuple_ok=hud_decoded_verified&&hud_receipt_epoch==frame_epoch&&hud_receipt_fid==frame_fid&&
        hud_receipt_refid==frame_refid&&hud_receipt_generation==frame_generation;
    assign hud_receipt_ready=state!=IDLE&&state!=DRAIN&&!have_hud_receipt&&!kill;
    assign message_length=job==LEAF?16'd51+16'(leaf_count)*16'd64:job==EMPTY_LEAF?16'd52:
        job==NODE?16'd82:job==HUD?16'd42240:16'd157;
    assign sha_start=state==BEGIN_JOB&&(job!=HUD||have_hud_receipt)&&!kill;
    assign sha_data_valid=!kill&&((state==SEND_HEADER||state==SEND_FIXED)||
        (state==SEND_PIXELS&&pixel_valid&&pixel_tuple_ok)||(state==SEND_HUD&&hud_valid&&hud_tuple_ok));
    assign sha_data=state==SEND_PIXELS?pixel_data:state==SEND_HUD?hud_data:fixed_byte(job,32'(message_pos));
    assign sha_data_last=message_pos+1==message_length;
    assign pixel_ready=state==SEND_PIXELS&&sha_data_ready&&!kill;
    assign hud_ready=state==SEND_HUD&&sha_data_ready&&!kill;
    assign hash_result=state==WAIT_HASH&&sha_valid&&!kill;
    assign hash_job_kind=job;
    assign hash_job_node=job==LEAF?10'd512+leaf_number:job==EMPTY_LEAF?empty_index+10'd512:
        job==NODE?node_width+node_index:10'd0;
    assign hash_digest=sha_digest;

    cu66_sha256_bytes #(.BUFFER_BLOCKS(2)) sha(
        .clk(clk),.rst(power_on_reset||reset),.abort_i(abort_i||state==DRAIN||error!=0),
        .start_valid(sha_start),.start_ready(sha_start_ready),.total_bytes(32'(message_length)),
        .data_valid(sha_data_valid),.data_ready(sha_data_ready),.data(sha_data),.data_last(sha_data_last),
        .result_valid(sha_valid),.result_ready(state==WAIT_HASH&&!kill),.digest(sha_digest),
        .busy(sha_busy),.error(sha_error),.aborted(unused_sha_aborted),.error_code(unused_sha_error_code),
        .accepted_bytes(sha_accepted_bytes),.compressed_blocks(sha_blocks),.round_cycles(unused_sha_rounds),
        .padding_bytes(unused_sha_padding),.input_stall_cycles(unused_sha_input_stalls),.output_stall_cycles(unused_sha_output_stalls),
        .debug_fill_state(unused_sha_fill),.debug_core_state(unused_sha_core));
    cu66_frame_bank_control banks(
        .clk(clk),.rst(power_on_reset),.abort_i(abort_i||reset||state==DRAIN),.drain_done(writes_drained),
        .begin_valid(bank_begin_valid),.begin_ready(bank_begin_ready),.begin_id(start_fid),.begin_key(start_key),.begin_reference_id(start_refid),
        .commit_valid(bank_commit_valid),.commit_ready(bank_commit_ready),.commit_ok(1'b1),.vblank(vblank),.scanout_drained(scanout_drained),
        .active(bank_active),.aborting(bank_aborting),.write_bank(write_bank),.read_bank_valid(unused_read_bank_valid),.read_bank(unused_read_bank),
        .ref_valid(bank_ref_valid),.ref_bank(reference_bank),.ref_id(bank_ref_fid),.front_valid(front_valid),.front_bank(front_bank),.front_id(front_fid),
        .pending_valid(pending_valid),.pending_bank(pending_bank),.pending_id(pending_fid),.begin_accepted(unused_begin_accepted),
        .frame_committed(frame_committed),.frame_presented(frame_presented),.aborted(unused_aborted),.error(unused_bank_error),
        .error_code(unused_bank_error_code),.accepted_count(unused_bank_accepted),.presented_count(unused_bank_presented));
    assign reference_bank_valid=bank_ref_valid;

    always_ff @(posedge clk)begin
        if(power_on_reset)begin
            state<=IDLE;done<=0;error<=0;frame_epoch<=0;frame_fid<=0;frame_refid<=0;frame_generation<=0;frame_key<=0;
            expected_root<=0;expected_seal<=0;previous_root<=0;receipt_hud<=0;have_hud_receipt<=0;
            computed_root<=0;computed_hud<=0;computed_seal<=0;
            accepted_generation<=0;accepted_root<=0;accepted_hud<=0;accepted_seal<=0;
            job<=LEAF;leaf_number<=0;empty_index<=508;node_width<=256;node_index<=0;node_level<=1;
            plane<=0;tile<=0;byte_index<=0;leaf_plane<=0;leaf_start<=0;leaf_count<=16;message_pos<=0;
            node_left<=0;node_right<=0;pixel_bytes<=0;hud_bytes<=0;hash_jobs<=0;hash_message_bytes<=0;hash_blocks<=0;
        end else begin
            done<=0;
            if(reset||abort_i)begin state<=DRAIN;error<=0;have_hud_receipt<=0;end
            else if(state==DRAIN)begin if(!bank_active&&!sha_busy)state<=IDLE;end
            else if(start_valid&&start_ready)begin
                error<=0;
                if(invalid_start)error<=1;
                else begin
                    state<=BEGIN_JOB;job<=LEAF;frame_epoch<=start_epoch;frame_fid<=start_fid;frame_refid<=start_refid;
                    frame_generation<=start_generation;frame_key<=start_key;expected_root<=start_expected_root;expected_seal<=start_expected_seal;
                    previous_root<=start_key?256'd0:accepted_root;have_hud_receipt<=0;receipt_hud<=0;
                    computed_root<=0;computed_hud<=0;computed_seal<=0;
                    leaf_number<=0;empty_index<=508;node_width<=256;node_index<=0;node_level<=1;
                    plane<=0;tile<=0;byte_index<=0;leaf_plane<=0;leaf_start<=0;leaf_count<=16;message_pos<=0;
                    pixel_bytes<=0;hud_bytes<=0;hash_jobs<=0;hash_message_bytes<=0;hash_blocks<=0;
                end
            end else if(state!=IDLE)begin
                if(producer_error)fail(10);
                else if(sha_error)fail(9);
                else if(hud_receipt_valid&&hud_receipt_ready&&!receipt_tuple_ok)fail(5);
                else if(state==SEND_PIXELS&&pixel_valid&&pixel_ready&&!pixel_tuple_ok)fail(2);
                else if(state==SEND_HUD&&hud_valid&&hud_ready&&!hud_tuple_ok)fail(3);
                else begin
                    if(hud_receipt_valid&&hud_receipt_ready)begin receipt_hud<=hud_receipt_sha256;have_hud_receipt<=1;end
                    if(sha_data_valid&&sha_data_ready)begin message_pos<=message_pos+1;hash_message_bytes<=hash_message_bytes+1;end
                    case(state)
                        BEGIN_JOB:if(sha_start&&sha_start_ready)begin
                            message_pos<=0;
                            if(job==NODE)begin node_left<=nodes[10'((node_width+node_index)*2)];node_right<=nodes[10'((node_width+node_index)*2+1)];end
                            state<=job==LEAF?SEND_HEADER:job==HUD?SEND_HUD:SEND_FIXED;
                        end
                        SEND_HEADER:if(sha_data_valid&&sha_data_ready&&message_pos==50)state<=SEND_PIXELS;
                        SEND_PIXELS:if(pixel_valid&&pixel_ready)begin
                            pixel_bytes<=pixel_bytes+1;
                            if(byte_index==63)begin
                                byte_index<=0;
                                if(tile==(plane==0?5399:1349))begin tile<=0;plane<=plane+1;end else tile<=tile+1;
                            end else byte_index<=byte_index+1;
                            if(sha_data_last)state<=WAIT_HASH;
                        end
                        SEND_HUD:if(hud_valid&&hud_ready)begin hud_bytes<=hud_bytes+1;if(sha_data_last)state<=WAIT_HASH;end
                        SEND_FIXED:if(sha_data_valid&&sha_data_ready&&sha_data_last)state<=WAIT_HASH;
                        WAIT_HASH:if(sha_valid)begin
                            hash_jobs<=hash_jobs+1;hash_blocks<=hash_blocks+sha_blocks;
                            if(sha_accepted_bytes!=32'(message_length))fail(9);
                            else if(job==LEAF)begin
                                nodes[512+leaf_number]<=sha_digest;
                                if(leaf_number==507)begin job<=EMPTY_LEAF;empty_index<=508;end
                                else begin leaf_number<=leaf_number+1;leaf_plane<=plane;leaf_start<=tile;leaf_count<=group_count(plane,tile);end
                                state<=BEGIN_JOB;
                            end else if(job==EMPTY_LEAF)begin
                                nodes[512+empty_index]<=sha_digest;
                                if(empty_index==511)begin job<=NODE;node_width<=256;node_index<=0;node_level<=1;end
                                else empty_index<=empty_index+1;
                                state<=BEGIN_JOB;
                            end else if(job==NODE)begin
                                nodes[node_width+node_index]<=sha_digest;
                                if(node_width==1)begin
                                    computed_root<=sha_digest;
                                    if(sha_digest!=expected_root)fail(6);
                                    else begin job<=HUD;state<=BEGIN_JOB;end
                                end else begin
                                    if(node_index+1==node_width)begin node_width<=node_width>>1;node_index<=0;node_level<=node_level+1;end
                                    else node_index<=node_index+1;
                                    state<=BEGIN_JOB;
                                end
                            end else if(job==HUD)begin
                                computed_hud<=sha_digest;
                                if(sha_digest!=receipt_hud)fail(7);else begin job<=SEAL;state<=BEGIN_JOB;end
                            end else begin
                                computed_seal<=sha_digest;
                                if(sha_digest!=expected_seal)fail(8);else state<=COMMIT;
                            end
                        end
                        COMMIT:if(bank_commit_valid&&bank_commit_ready)begin
                            accepted_generation<=frame_generation;accepted_root<=computed_root;accepted_hud<=computed_hud;accepted_seal<=computed_seal;
                            state<=IDLE;done<=1;
                        end
                        default:begin end
                    endcase
                end
            end
        end
    end
`ifndef SYNTHESIS
    always_ff @(posedge clk)if(!power_on_reset&&!reset&&!abort_i)begin
        if(bank_commit_valid)assert(pixel_bytes==518400&&hud_bytes==42240&&hash_jobs==1025&&have_hud_receipt&&
            computed_root==expected_root&&computed_seal==expected_seal&&writes_drained)else $fatal(1,"V91l commit before complete validation/drain");
        if(hash_result&&job==NODE)assert(node_width+node_index<512)else $fatal(1,"V91l internal node index");
        if(pixel_ready)assert(pixel_bytes<518400&&plane<3)else $fatal(1,"V91l canonical stream overrun");
        if(hud_ready)assert(have_hud_receipt&&hud_bytes<42240)else $fatal(1,"V91l HUD stream without receipt");
    end
`endif
endmodule
