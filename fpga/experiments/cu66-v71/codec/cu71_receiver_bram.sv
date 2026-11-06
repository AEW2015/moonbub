// CU66 frame transaction owner. Actual packet and base RTL; processor HUD and
// painter/memory completion are explicit external contracts, never goldens.
// One frame at a time; accepted canonical/HUD state is preserved on failure.
// Reset requires ALL external adapters flushed and a fresh host generation.
module cu71_receiver_bram #(
    parameter integer WATCHDOG_CYCLES=64000000,
    parameter integer COMMIT_RETRY_CYCLES=64
)(
    input logic clk,rst,abort_i,clear_fault,
    input logic start_valid,output logic start_ready,
    input logic [63:0] start_generation,
    input logic [31:0] start_packet_bytes,
    output logic packet_req_valid,input logic packet_req_ready,
    output logic [15:0] packet_req_address,
    output logic [63:0] packet_req_generation,
    output logic [31:0] packet_req_sequence,
    input logic packet_rsp_valid,output logic packet_rsp_ready,
    input logic [63:0] packet_rsp_generation,
    input logic [31:0] packet_rsp_sequence,input logic [15:0] packet_rsp_address,
    input logic [7:0] packet_rsp_data,
    output logic ref_req_valid,input logic ref_req_ready,
    output logic [63:0] ref_req_generation,
    output logic [1:0] ref_req_bank,ref_req_plane,
    output logic [16:0] ref_req_index,
    input logic ref_rsp_valid,output logic ref_rsp_ready,
    input logic [63:0] ref_rsp_generation,
    input logic [1:0] ref_rsp_bank,ref_rsp_plane,
    input logic [16:0] ref_rsp_index,
    input logic [511:0] ref_rsp_pixels,input logic ref_rsp_error,
    output logic write_valid,input logic write_ready,
    output logic [63:0] write_generation,
    output logic [1:0] write_bank,write_plane,
    output logic [16:0] write_index,
    output logic [511:0] write_pixels,
    input logic write_done_valid,output logic write_done_ready,
    input logic [63:0] write_done_generation,
    input logic [1:0] write_done_bank,write_done_plane,
    input logic [16:0] write_done_index,
    input logic write_done_error,
    input logic memory_drained,
    output logic hud_prepare_valid,input logic hud_prepare_ready,
    output logic [63:0] active_generation,
    output logic [31:0] active_frame_id,active_reference_id,
    output logic active_key,
    output logic [15:0] hud_address,hud_bytes,
    output logic [127:0] expected_hud_tag,
    output logic [1:0] candidate_bank,
    input logic hud_result_valid,output logic hud_result_ready,
    input logic [63:0] hud_result_generation,
    input logic [31:0] hud_result_frame_id,hud_result_reference_id,
    input logic [127:0] hud_result_tag,
    input logic [15:0] hud_result_words,input logic hud_result_success,
    input logic hud_drain_valid,output logic hud_drain_ready,
    input logic [63:0] hud_drain_generation,
    input logic [31:0] hud_drain_frame_id,
    input logic [1:0] hud_drain_bank,
    input logic [127:0] hud_drain_tag,
    input logic [15:0] hud_drain_words,input logic hud_drain_success,
    output logic software_command_valid,input logic software_command_ready,
    output logic [2:0] software_command_opcode,
    input logic software_ack_valid,output logic software_ack_ready,
    input logic [2:0] software_ack_opcode,
    input logic [63:0] software_ack_generation,
    input logic [31:0] software_ack_frame_id,input logic software_ack_success,
    output logic paint_start_valid,input logic paint_start_ready,
    output logic paint_rgb_slot,
    input logic paint_result_valid,output logic paint_result_ready,
    input logic [63:0] paint_result_generation,
    input logic [31:0] paint_result_frame_id,
    input logic paint_result_success,input logic painter_drained,
    output logic paint_abort,
    output logic presentation_valid,input logic presentation_ready,
    output logic [63:0] presentation_generation,
    output logic [31:0] presentation_frame_id,output logic presentation_rgb_slot,
    input logic vblank,scanout_drained,
    input logic [63:0] presented_generation,
    input logic [31:0] presented_frame_id,input logic presented_rgb_slot,
    output logic front_valid,front_rgb_slot,
    output logic [1:0] front_bank,
    output logic [63:0] front_generation,
    output logic [31:0] front_frame_id,
    output logic reference_valid,
    output logic [1:0] reference_bank,
    output logic [31:0] reference_frame_id,
    output logic [127:0] reference_tag,
    output logic busy,done,aborted,error,
    output logic [7:0] error_code,stage,
    output logic [31:0] accepted_count,presented_count,rejected_count,stale_completions,
    input logic [9:0] diag_address,output logic [31:0] diag_data
);
    typedef enum logic [3:0] {IDLE,PARSER_START,METADATA,WAIT_BANK,
        BASE_START,BASE_RUN,WAIT_RGB,PAINT_START,PAINT_RUN,
        COMMIT_READY,COMMIT_ACK,DRAIN} state_t;
    state_t state;
    logic [63:0] latest_generation,clock_count;
    logic [15:0] packet_length;
    logic [31:0] age,retry_age;
    logic hud_requested,hud_good,hud_written,base_good,paint_good,command_sent,command_issued,abort_acknowledged;
    logic [1:0] next_plane;
    logic [31:0] fid,rid;
    logic key;
    logic [127:0] canonical_expected,hud_expected;
    logic [15:0] hud_offset,hud_length;
    logic rgb_slot,rgb_free,rgb_choice;
    logic [2:0] bank_rgb;
    logic [63:0] bank_generation [0:2];
    logic [127:0] accepted_tag;
    logic p_cfg_ready,p_req_valid,p_req_ready,p_rsp_ready,p_meta_valid,p_meta_ready;
    logic [15:0] p_req_address;
    logic p_key,p_commit_ready,p_busy,p_done,p_error;
    logic [31:0] p_fid,p_rid;
    logic [127:0] p_reference_tag,p_output_tag,p_hud_reference_tag,p_hud_tag;
    logic [15:0] p_plane_address[0:2],p_plane_bytes[0:2];
    logic [2:0] p_plane_dispatch[0:2];
    logic [16:0] p_plane_blocks[0:2];
    logic [8:0] p_plane_bw[0:2];
    logic [7:0] p_block_size,p_code;
    logic [15:0] p_hud_address,p_hud_bytes;
    logic [31:0] p_reads;
    logic b_start_ready,b_plane_ready,b_req_valid,b_req_ready,b_rsp_ready,b_busy,b_error,b_tag_valid;
    logic [1:0] b_req_plane;
    logic [15:0] b_req_address;
    logic [7:0] b_code;
    logic [255:0] b_digest;
    logic [31:0] b_tiles,b_cycles,b_write_fid;
    logic b_write_last;
    logic b_ref_valid,b_ref_ready,b_ref_rsp_ready;
    logic [31:0] b_ref_tile;
    logic q_valid,q_ready,q_rsp_valid;
    logic [10:0] q_index,q_rsp_index,q_expected_index;
    logic [1:0] q_code;
    logic bank_begin_ready,bank_begin_accepted,bank_active,bank_aborting,bank_read_valid;
    logic [1:0] bank_write,bank_read,pending_bank;
    logic bank_commit_ready,bank_committed,bank_presented,bank_aborted,bank_error,pending_valid;
    logic [31:0] pending_id;
    logic [7:0] bank_code;
    logic packet_pending,packet_owner,ref_pending,write_pending;
    logic [31:0] packet_sequence,packet_expected_sequence;
    logic [15:0] packet_expected_address;
    logic [3:0] stale_this_cycle;
    logic [31:0] ref_identity,write_identity;
    logic [1:0] read_identity_bank,write_identity_bank;
    logic packet_match,ref_match,write_match,hud_match,hud_write_match,paint_match,ack_match;
    logic [16:0] calculated_packet_address;
    logic start_fire,meta_fire,base_start_fire,base_tag_fire,commit_fire,present_match;
    logic fatal,kill,abort_allowed;
    logic [7:0] fatal_code;
    logic [23:0] last_address;
    logic first_fault;
    logic [63:0] fault_generation;
    logic [31:0] fault_frame;
    logic [7:0] fault_stage,fault_reason,fault_detail;
    logic [23:0] fault_address;
    logic [63:0] arrived_at,parsed_at,base_at,hud_at,painted_at,committed_at,presented_at;
    logic [255:0] events[0:7];
    logic [31:0] event_sequence,event_overwrites;
    logic [7:0] event_code;
    logic [63:0] event_generation;
    logic [31:0] event_fid;

    assign stage={4'd0,state};
    assign busy=state!=IDLE;
    assign start_ready=state==IDLE&&p_cfg_ready&&!bank_active&&!packet_pending&&
                       !ref_pending&&!write_pending&&memory_drained&&painter_drained&&!rst&&!abort_i;
    assign start_fire=start_valid&&start_ready;
    assign active_frame_id=fid;
    assign active_reference_id=rid;
    assign active_key=key;
    assign candidate_bank=bank_write;
    assign hud_address=hud_offset;
    assign hud_bytes=hud_length;
    assign expected_hud_tag=hud_expected;
    assign reference_tag=accepted_tag;
    assign front_generation=front_valid?bank_generation[front_bank]:64'd0;
    assign front_rgb_slot=front_valid?bank_rgb[front_bank]:1'b0;
    assign meta_fire=p_meta_valid&&p_meta_ready;
    assign p_meta_ready=state==METADATA&&bank_begin_ready&&!kill;
    assign base_start_fire=state==BASE_START&&b_start_ready&&!kill;
    assign base_tag_fire=state==BASE_RUN&&b_tag_valid&&!base_good&&!kill;
    assign abort_allowed=state!=IDLE&&state!=COMMIT_ACK&&state!=DRAIN;
    assign kill=(abort_i&&abort_allowed)||state==DRAIN;
    assign paint_abort=kill;
    assign packet_req_generation=active_generation;
    assign packet_req_sequence=packet_sequence;
    assign calculated_packet_address=p_req_valid?{1'b0,p_req_address}:
                            ({1'b0,p_plane_address[b_req_plane]}+{1'b0,b_req_address});
    assign packet_req_valid=!packet_pending&&!kill&&(p_req_valid||b_req_valid)&&
                            calculated_packet_address<{1'b0,packet_length[15:0]};
    assign packet_req_address=calculated_packet_address[15:0];
    assign p_req_ready=packet_req_ready&&!packet_pending&&!kill&&packet_req_valid&&p_req_valid;
    assign b_req_ready=packet_req_ready&&!packet_pending&&!kill&&packet_req_valid&&!p_req_valid;
    assign packet_match=packet_pending&&packet_rsp_generation==active_generation&&
        packet_rsp_sequence==packet_expected_sequence&&packet_rsp_address==packet_expected_address;
    assign packet_rsp_ready=packet_match?(packet_owner?b_rsp_ready:p_rsp_ready):1'b1;
    assign ref_req_valid=b_ref_valid&&!kill;
    assign b_ref_ready=ref_req_ready&&!kill;
    assign ref_req_generation=active_generation;
    assign ref_req_bank=bank_read;
    assign ref_req_plane=b_ref_tile[18:17];
    assign ref_req_index=b_ref_tile[16:0];
    assign ref_match=ref_pending&&ref_rsp_generation==active_generation&&
        ref_rsp_bank==read_identity_bank&&{13'd0,ref_rsp_plane,ref_rsp_index}==ref_identity;
    assign ref_rsp_ready=ref_match?b_ref_rsp_ready:1'b1;
    assign write_generation=active_generation;
    assign write_bank=bank_write;
    assign write_match=write_pending&&write_done_generation==active_generation&&
        write_done_bank==write_identity_bank&&{13'd0,write_done_plane,write_done_index}==write_identity;
    assign write_done_ready=!rst;
    assign hud_prepare_valid=(state==BASE_START||state==BASE_RUN)&&!hud_requested&&!kill&&!fatal;
    assign hud_result_ready=busy&&!rst;
    assign hud_drain_ready=busy&&!rst;
    assign hud_match=hud_requested&&hud_result_generation==active_generation&&
        hud_result_frame_id==fid;
    assign hud_write_match=hud_requested&&hud_drain_generation==active_generation&&
        hud_drain_frame_id==fid;
    assign paint_start_valid=state==PAINT_START&&!kill;
    assign paint_rgb_slot=rgb_slot;
    assign paint_result_ready=busy&&!rst;
    assign paint_match=paint_result_generation==active_generation&&paint_result_frame_id==fid;
    assign commit_fire=state==COMMIT_READY&&bank_commit_ready&&p_commit_ready&&
        base_good&&hud_good&&hud_written&&paint_good&&memory_drained&&painter_drained&&
        (!presentation_valid||presentation_ready)&&!kill&&!fatal;
    assign present_match=pending_valid&&presented_generation==bank_generation[pending_bank]&&
        presented_frame_id==pending_id&&presented_rgb_slot==bank_rgb[pending_bank];
    assign software_command_opcode=state==COMMIT_ACK?3'd5:3'd6;
    assign software_command_valid=((state==COMMIT_ACK)||
        (state==DRAIN&&hud_requested&&!abort_acknowledged))&&!command_sent&&!rst;
    assign software_ack_ready=busy&&!rst;
    assign ack_match=command_issued&&software_ack_generation==active_generation&&software_ack_frame_id==fid&&
        ((state==COMMIT_ACK&&software_ack_opcode==5)||(state==DRAIN&&software_ack_opcode==6));

    always_comb begin
        rgb_free=0;rgb_choice=0;
        for(integer i=0;i<2;i=i+1)if(!rgb_free&&
            !(front_valid&&bank_rgb[front_bank]==1'(i))&&
            !(pending_valid&&bank_rgb[pending_bank]==1'(i)))begin
            rgb_free=1;rgb_choice=1'(i);
        end
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
            else if(state==PAINT_RUN&&paint_result_valid&&paint_match&&!paint_result_success)
                begin fatal=1;fatal_code=8'h72;end
            else if(ref_rsp_valid&&ref_match&&ref_rsp_error)begin fatal=1;fatal_code=8'h73;end
            else if(q_rsp_valid&&q_rsp_index!=q_expected_index)begin fatal=1;fatal_code=8'h74;end
            else if(!packet_pending&&(p_req_valid||b_req_valid)&&
                calculated_packet_address>={1'b0,packet_length[15:0]})begin fatal=1;fatal_code=8'h75;end
            else if(WATCHDOG_CYCLES!=0&&age>=32'(WATCHDOG_CYCLES))begin fatal=1;fatal_code=8'h7f;end
        end
    end

    always_comb begin
        stale_this_cycle=0;
        if(packet_rsp_valid&&packet_rsp_ready&&!packet_match)stale_this_cycle=stale_this_cycle+1;
        if(ref_rsp_valid&&ref_rsp_ready&&!ref_match)stale_this_cycle=stale_this_cycle+1;
        if(write_done_valid&&write_done_ready&&!write_match)stale_this_cycle=stale_this_cycle+1;
        if(hud_result_valid&&hud_result_ready&&!hud_match)stale_this_cycle=stale_this_cycle+1;
        if(hud_drain_valid&&hud_drain_ready&&!hud_write_match)stale_this_cycle=stale_this_cycle+1;
        if(software_ack_valid&&software_ack_ready&&!ack_match)stale_this_cycle=stale_this_cycle+1;
        if(paint_result_valid&&paint_result_ready&&(!paint_match||state!=PAINT_RUN))stale_this_cycle=stale_this_cycle+1;
        if(vblank&&!present_match)stale_this_cycle=stale_this_cycle+1;
    end

    always_ff @(posedge clk)begin
        if(rst)begin
            state<=IDLE;active_generation<=0;latest_generation<=0;clock_count<=0;
            packet_length<=0;age<=0;retry_age<=0;fid<=32'hffffffff;rid<=32'hffffffff;key<=0;
            canonical_expected<=0;hud_expected<=0;hud_offset<=0;hud_length<=0;
            hud_requested<=0;hud_good<=0;hud_written<=0;base_good<=0;paint_good<=0;
            command_sent<=0;command_issued<=0;abort_acknowledged<=0;next_plane<=0;rgb_slot<=0;bank_rgb<=0;
            packet_sequence<=0;packet_expected_sequence<=0;packet_expected_address<=0;
            accepted_tag<=0;presentation_valid<=0;presentation_generation<=0;presentation_frame_id<=0;presentation_rgb_slot<=0;packet_pending<=0;packet_owner<=0;ref_pending<=0;write_pending<=0;
            ref_identity<=0;write_identity<=0;read_identity_bank<=0;write_identity_bank<=0;
            q_expected_index<=0;last_address<=0;done<=0;aborted<=0;error<=0;error_code<=0;
            rejected_count<=0;stale_completions<=0;first_fault<=0;fault_generation<=0;
            fault_frame<=0;fault_stage<=0;fault_reason<=0;fault_detail<=0;fault_address<=0;
            arrived_at<=0;parsed_at<=0;base_at<=0;hud_at<=0;painted_at<=0;committed_at<=0;presented_at<=0;
            for(integer i=0;i<3;i=i+1)bank_generation[i]<=0;
        end else begin
            clock_count<=clock_count+1;done<=0;aborted<=0;
            if(clear_fault)first_fault<=0;
            if(presentation_valid&&presentation_ready)presentation_valid<=0;
            if(busy&&state!=DRAIN&&state!=COMMIT_ACK)age<=age+1;
            if(packet_req_valid&&packet_req_ready)begin
                packet_pending<=1;packet_owner<=!p_req_valid;last_address<={8'd0,packet_req_address};
                packet_expected_sequence<=packet_sequence;packet_sequence<=packet_sequence+1;
                packet_expected_address<=packet_req_address;
            end
            if(packet_rsp_valid&&packet_rsp_ready)begin
                if(packet_match)packet_pending<=0;
            end
            if(ref_req_valid&&ref_req_ready)begin
                ref_pending<=1;ref_identity<=b_ref_tile;read_identity_bank<=bank_read;
                last_address<=b_ref_tile[23:0];
            end
            if(ref_rsp_valid&&ref_rsp_ready)begin
                if(ref_match)ref_pending<=0;
            end
            if(write_valid&&write_ready)begin
                write_pending<=1;write_identity<={13'd0,write_plane,write_index};
                write_identity_bank<=bank_write;last_address<={5'd0,write_plane,write_index};
            end
            if(write_done_valid&&write_done_ready)begin
                if(write_match)write_pending<=0;
            end
            if(q_valid&&q_ready)q_expected_index<=q_index;
            if(hud_prepare_valid&&hud_prepare_ready)hud_requested<=1;
            if(hud_result_valid&&hud_result_ready)begin
                if(hud_match)begin if(hud_result_success)hud_good<=1;end
                
            end
            if(hud_drain_valid&&hud_drain_ready)begin
                if(hud_write_match)begin if(hud_drain_success)hud_written<=1;end
                
            end
            if(hud_good&&hud_written&&hud_at==0)hud_at<=clock_count;
            if(software_command_valid&&software_command_ready)begin command_sent<=1;command_issued<=1;retry_age<=0;end
            if(command_sent)begin
                if(retry_age>=32'(COMMIT_RETRY_CYCLES))begin command_sent<=0;retry_age<=0;end
                else retry_age<=retry_age+1;
            end
            if(stale_this_cycle!=0)stale_completions<=stale_completions+{28'd0,stale_this_cycle};
            if(bank_presented)presented_at<=clock_count;
            if(fatal||(abort_i&&abort_allowed))begin
                state<=DRAIN;error<=fatal;error_code<=fatal?fatal_code:8'h80;
                command_sent<=0;command_issued<=0;abort_acknowledged<=!hud_requested;
                rejected_count<=rejected_count+1;
                if(fatal&&(!first_fault||clear_fault))begin first_fault<=1;fault_generation<=active_generation;
                    fault_frame<=fid;fault_stage<=stage;fault_reason<=fatal_code;fault_address<=last_address;
                    fault_detail<=state==METADATA?p_code:(state==WAIT_BANK?bank_code:b_code);end
            end else case(state)
                IDLE:if(start_fire)begin
                    error<=0;error_code<=0;
                    if(start_generation==0||start_generation<=latest_generation||
                       start_packet_bytes==0||start_packet_bytes>49152)begin
                        error<=1;error_code<=8'h01;rejected_count<=rejected_count+1;
                        if(!first_fault||clear_fault)begin first_fault<=1;fault_generation<=start_generation;
                            fault_frame<=32'hffffffff;fault_stage<=0;fault_reason<=1;fault_detail<=0;fault_address<=0;end
                    end else begin
                        active_generation<=start_generation;latest_generation<=start_generation;
                        packet_length<=16'(start_packet_bytes);state<=PARSER_START;age<=0;
                        fid<=32'hffffffff;rid<=32'hffffffff;key<=0;
                        hud_requested<=0;hud_good<=0;hud_written<=0;base_good<=0;paint_good<=0;
                        abort_acknowledged<=0;command_sent<=0;command_issued<=0;next_plane<=0;
                        arrived_at<=clock_count;parsed_at<=0;base_at<=0;hud_at<=0;painted_at<=0;committed_at<=0;
                    end
                end
                PARSER_START:if(p_cfg_ready)state<=METADATA;
                METADATA:if(meta_fire)begin
                    fid<=p_fid;rid<=p_rid;key<=p_key;canonical_expected<=p_output_tag;
                    hud_expected<=p_hud_tag;hud_offset<=p_hud_address;hud_length<=p_hud_bytes;
                    parsed_at<=clock_count;state<=WAIT_BANK;
                end
                WAIT_BANK:if(bank_begin_accepted)state<=BASE_START;
                BASE_START:if(base_start_fire)state<=BASE_RUN;
                BASE_RUN:begin
                    if(next_plane<3&&b_plane_ready)next_plane<=next_plane+1;
                    if(base_tag_fire)begin base_good<=1;base_at<=clock_count;end
                    if(base_good&&hud_good&&hud_written&&memory_drained)state<=WAIT_RGB;
                end
                WAIT_RGB:if(rgb_free)begin rgb_slot<=rgb_choice;state<=PAINT_START;end
                PAINT_START:if(paint_start_valid&&paint_start_ready)state<=PAINT_RUN;
                PAINT_RUN:if(paint_result_valid&&paint_result_ready)begin
                    if(paint_match)begin
                        if(paint_result_success)begin paint_good<=1;painted_at<=clock_count;state<=COMMIT_READY;end
                    end 
                end
                COMMIT_READY:if(commit_fire)begin
                    accepted_tag<=canonical_expected;bank_generation[bank_write]<=active_generation;
                    bank_rgb[bank_write]<=rgb_slot;committed_at<=clock_count;
                    presentation_valid<=1;presentation_generation<=active_generation;
                    presentation_frame_id<=fid;presentation_rgb_slot<=rgb_slot;
                    state<=COMMIT_ACK;command_sent<=0;command_issued<=0;
                end
                COMMIT_ACK:if(software_ack_valid&&software_ack_ready&&ack_match&&software_ack_success)begin
                    state<=IDLE;command_sent<=0;command_issued<=0;done<=1;
                end
                DRAIN:begin
                    if(software_ack_valid&&software_ack_ready&&ack_match&&software_ack_success)
                        begin abort_acknowledged<=1;command_sent<=0;end
                    if(!p_busy&&!b_busy&&!packet_pending&&!ref_pending&&!write_pending&&
                        memory_drained&&painter_drained&&(!hud_requested||abort_acknowledged)&&!bank_active)
                        begin state<=IDLE;aborted<=1;command_sent<=0;command_issued<=0;end
                end
                default:state<=DRAIN;
            endcase
        end
    end

    cu66_packet_control parser(
        .clk,.rst,.abort_i(kill),.cfg_valid(state==PARSER_START&&!kill),.cfg_ready(p_cfg_ready),
        .cfg_packet_bytes(packet_length[15:0]),.cfg_last_valid(reference_valid),.cfg_last_frame_id(reference_frame_id),
        .cfg_reference_valid(reference_valid),.cfg_reference_id(reference_frame_id),.cfg_reference_tag(accepted_tag),
        .rd_req_valid(p_req_valid),.rd_req_ready(p_req_ready),.rd_req_addr(p_req_address),
        .rd_rsp_valid(packet_rsp_valid&&packet_match&&!packet_owner),.rd_rsp_ready(p_rsp_ready),.rd_rsp_data(packet_rsp_data),
        .metadata_valid(p_meta_valid),.metadata_ready(p_meta_ready),.metadata_key(p_key),
        .metadata_frame_id(p_fid),.metadata_reference_id(p_rid),.metadata_reference_tag(p_reference_tag),
        .metadata_output_tag(p_output_tag),.metadata_block_size(p_block_size),
        .metadata_plane_addr(p_plane_address),.metadata_plane_bytes(p_plane_bytes),
        .metadata_plane_dispatch(p_plane_dispatch),.metadata_plane_blocks(p_plane_blocks),.metadata_plane_blocks_w(p_plane_bw),
        .metadata_hud_addr(p_hud_address),.metadata_hud_bytes(p_hud_bytes),
        .metadata_hud_reference_tag(p_hud_reference_tag),.metadata_hud_output_tag(p_hud_tag),
        .qmap_req_valid(q_valid),.qmap_req_ready(q_ready),.qmap_req_index(q_index),
        .qmap_rsp_valid(q_rsp_valid),.qmap_rsp_index(q_rsp_index),.qmap_rsp_code(q_code),
        .commit_valid(commit_fire),.commit_ready(p_commit_ready),.busy(p_busy),.done(p_done),
        .aborted(),.error(p_error),.error_code(p_code),.debug_state(),.memory_reads(p_reads));
    cu71_base_pipeline_bram base(
        .clk,.rst,.abort_i(kill),.start_valid(state==BASE_START&&!kill),.start_ready(b_start_ready),
        .frame_id(fid),.key,.expected_tag(canonical_expected),
        .plane_cfg_valid(state==BASE_RUN&&next_plane<3&&!kill),.plane_cfg_ready(b_plane_ready),
        .plane_cfg_plane(next_plane),.plane_cfg_dispatch(p_plane_dispatch[next_plane<3?next_plane:2'd0]),
        .plane_cfg_bytes(p_plane_bytes[next_plane<3?next_plane:2'd0]),
        .plane_cfg_blocks(p_plane_blocks[next_plane<3?next_plane:2'd0]),
        .rd_req_valid(b_req_valid),.rd_req_ready(b_req_ready),.rd_req_plane(b_req_plane),.rd_req_addr(b_req_address),
        .rd_rsp_valid(packet_rsp_valid&&packet_match&&packet_owner),.rd_rsp_ready(b_rsp_ready),.rd_rsp_data(packet_rsp_data),
        .q_req_valid(q_valid),.q_req_ready(q_ready),.q_req_index(q_index),.q_rsp_valid(q_rsp_valid),.q_rsp_code(q_code),
        .ref_req_valid(b_ref_valid),.ref_req_ready(b_ref_ready),.ref_req_tile(b_ref_tile),
        .ref_rsp_valid(ref_rsp_valid&&ref_match),.ref_rsp_ready(b_ref_rsp_ready),
        .ref_rsp_tile({13'd0,ref_rsp_plane,ref_rsp_index}),.ref_rsp_pixels,
        .tile_valid(write_valid),.tile_ready(write_ready),.write_done(write_done_valid&&write_match),
        .write_error(write_done_error),.tile_frame_id(b_write_fid),.tile_plane(write_plane),
        .tile_index(write_index),.tile_pixels(write_pixels),.tile_last(b_write_last),
        .tag_valid(b_tag_valid),.tag_ready(base_tag_fire),.digest(b_digest),.busy(b_busy),
        .error(b_error),.error_code(b_code),.aborted(),.accepted_tiles(b_tiles),.cycle_count(b_cycles));
    cu66_frame_bank_control banks(
        .clk,.rst,.abort_i(kill),.drain_done(!b_busy&&!ref_pending&&!write_pending&&memory_drained&&painter_drained),
        .begin_valid(meta_fire),.begin_ready(bank_begin_ready),.begin_id(p_fid),.begin_key(p_key),.begin_reference_id(p_rid),
        .commit_valid(commit_fire),.commit_ready(bank_commit_ready),.commit_ok(1'b1),.vblank(vblank&&present_match),.scanout_drained,
        .active(bank_active),.aborting(bank_aborting),.write_bank(bank_write),
        .read_bank_valid(bank_read_valid),.read_bank(bank_read),.ref_valid(reference_valid),
        .ref_bank(reference_bank),.ref_id(reference_frame_id),.front_valid,.front_bank,.front_id(front_frame_id),
        .pending_valid,.pending_bank,.pending_id,.begin_accepted(bank_begin_accepted),
        .frame_committed(bank_committed),.frame_presented(bank_presented),.aborted(bank_aborted),
        .error(bank_error),.error_code(bank_code),.accepted_count,.presented_count);

    always_comb begin
        event_code=0;event_generation=active_generation;event_fid=fid;
        if(start_fire)begin event_code=1;event_generation=start_generation;event_fid=32'hffffffff;end
        if(meta_fire)begin event_code=2;event_fid=p_fid;end
        if(base_tag_fire)event_code=3;
        if(hud_drain_valid&&hud_drain_ready&&hud_write_match)event_code=4;
        if(state==PAINT_RUN&&paint_result_valid&&paint_result_ready&&paint_match)event_code=5;
        if(commit_fire)event_code=6;
        if(bank_presented)begin event_code=7;event_generation=front_generation;event_fid=front_frame_id;end
        if(aborted)event_code=8;
        if(fatal)event_code=9;
        if(state==COMMIT_ACK&&software_ack_valid&&ack_match&&software_ack_success)event_code=10;
    end
    always_ff @(posedge clk)begin
        if(rst)begin
            event_sequence<=0;event_overwrites<=0;
            for(integer i=0;i<8;i=i+1)events[i]<=0;
        end else if(event_code!=0)begin
            events[event_sequence[2:0]]<={8'd0,last_address,stage,event_code,fatal_code,8'd0,
                event_fid,event_generation[63:32],event_generation[31:0],clock_count[63:32],clock_count[31:0],event_sequence};
            event_sequence<=event_sequence+1;
            if(event_sequence>=8)event_overwrites<=event_overwrites+1;
        end
    end
    always_comb begin
        diag_data=0;
        case(diag_address)
            10'h000:diag_data=32'h43553730;
            10'h004:diag_data=32'h00010000;
            10'h008:diag_data=32'h0000003f;
            10'h00c:diag_data={16'd0,error_code,2'd0,first_fault,error,bank_aborting,busy,state[1:0]};
            10'h010:diag_data=active_generation[31:0];
            10'h014:diag_data=active_generation[63:32];
            10'h018:diag_data=fid;
            10'h01c:diag_data=reference_frame_id;
            10'h020:diag_data=front_frame_id;
            10'h024:diag_data=accepted_count;
            10'h028:diag_data=presented_count;
            10'h02c:diag_data=rejected_count;
            10'h030:diag_data=stale_completions;
            10'h034:diag_data=age;
            10'h038:diag_data=p_reads;
            10'h03c:diag_data=b_cycles;
            10'h040:diag_data=b_tiles;
            10'h044:diag_data={8'd0,fault_address};
            10'h048:diag_data={15'd0,first_fault,fault_stage,fault_reason};
            10'h04c:diag_data=fault_frame;
            10'h050:diag_data=fault_generation[31:0];
            10'h054:diag_data=fault_generation[63:32];
            10'h058:diag_data=event_sequence;
            10'h05c:diag_data=event_overwrites;
            10'h060:diag_data=arrived_at[31:0];
            10'h064:diag_data=arrived_at[63:32];
            10'h068:diag_data=parsed_at[31:0];
            10'h06c:diag_data=parsed_at[63:32];
            10'h070:diag_data=base_at[31:0];
            10'h074:diag_data=base_at[63:32];
            10'h078:diag_data=hud_at[31:0];
            10'h07c:diag_data=hud_at[63:32];
            10'h080:diag_data=painted_at[31:0];
            10'h084:diag_data=painted_at[63:32];
            10'h088:diag_data=committed_at[31:0];
            10'h08c:diag_data=committed_at[63:32];
            10'h090:diag_data=presented_at[31:0];
            10'h094:diag_data=presented_at[63:32];
            10'h098:diag_data=reference_tag[31:0];
            10'h09c:diag_data=reference_tag[63:32];
            10'h0a0:diag_data=reference_tag[95:64];
            10'h0a4:diag_data=reference_tag[127:96];
            10'h0a8:diag_data={24'd0,p_block_size};
            10'h0ac:diag_data={p_plane_bw[0],p_plane_bw[1],p_plane_bw[2],p_block_size[4:0]};
            10'h0b0:diag_data=b_write_fid;
            10'h0b4:diag_data={26'd0,bank_read_valid,bank_committed,bank_aborted,p_done,b_write_last,pending_valid};
            10'h0b8:diag_data=pending_id;
            10'h0bc:diag_data={fault_detail,p_code,b_code,bank_code};
            default:begin
                if(diag_address>=10'h100&&diag_address<10'h200&&diag_address[1:0]==0)
                    diag_data=events[diag_address[7:5]][int'(diag_address[4:2])*32+:32];
                if(diag_address>=10'h200&&diag_address<10'h220&&diag_address[1:0]==0)
                    diag_data=b_digest[int'(diag_address[4:2])*32+:32];
                if(diag_address>=10'h220&&diag_address<10'h230&&diag_address[1:0]==0)
                    diag_data=p_reference_tag[int'(diag_address[3:2])*32+:32];
                if(diag_address>=10'h230&&diag_address<10'h240&&diag_address[1:0]==0)
                    diag_data=p_hud_reference_tag[int'(diag_address[3:2])*32+:32];
            end
        endcase
    end
endmodule
