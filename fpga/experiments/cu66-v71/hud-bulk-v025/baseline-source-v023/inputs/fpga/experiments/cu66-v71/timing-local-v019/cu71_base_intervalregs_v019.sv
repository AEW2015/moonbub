// Fixed-profile base-layer integration. Configuration must come from a qualified
// CU66 packet parser; writes are provisional until tag_valid and external HUD /
// packet checks also pass. This module does not publish a display/reference bank.
// All memory ports permit one outstanding transaction. Reset requires adapters
// flushed; abort drains accepted reads before another frame can start.
module cu71_base_intervalregs_v019 (
    input logic clk,rst,abort_i,
    input logic start_valid,
    output logic start_ready,
    input logic [31:0] frame_id,
    input logic key,
    input logic [127:0] expected_tag,
    input logic plane_cfg_valid,
    output logic plane_cfg_ready,
    input logic [1:0] plane_cfg_plane,
    input logic [2:0] plane_cfg_dispatch,
    input logic [15:0] plane_cfg_bytes,
    input logic [16:0] plane_cfg_blocks,
    output logic rd_req_valid,
    input logic rd_req_ready,
    output logic [1:0] rd_req_plane,
    output logic [15:0] rd_req_addr,
    input logic rd_rsp_valid,
    output logic rd_rsp_ready,
    input logic [7:0] rd_rsp_data,
    output logic q_req_valid,
    input logic q_req_ready,
    output logic [10:0] q_req_index,
    input logic q_rsp_valid,
    input logic [1:0] q_rsp_code,
    output logic ref_req_valid,
    input logic ref_req_ready,
    output logic [31:0] ref_req_tile,
    input logic ref_rsp_valid,
    output logic ref_rsp_ready,
    input logic [31:0] ref_rsp_tile,
    input logic [511:0] ref_rsp_pixels,
    output logic tile_valid,
    input logic tile_ready,
    input logic write_done,write_error,
    output logic [31:0] tile_frame_id,
    output logic [1:0] tile_plane,
    output logic [16:0] tile_index,
    output logic [511:0] tile_pixels,
    output logic tile_last,
    output logic tag_valid,
    input logic tag_ready,
    output logic [255:0] digest,
    output logic busy,error,aborted,
    output logic [7:0] error_code,
    output logic [31:0] accepted_tiles,cycle_count
);
    typedef enum logic [3:0] {IDLE,PLANE_WAIT,CONFIGURE,RUN_PLANE,
                             HASH_WAIT,RESULT_HOLD,DRAIN} frame_state_t;
    typedef enum logic [3:0] {TAKE_TILE,REQUEST_Q,WAIT_Q,SEND_DQ,
                             WAIT_DQ,WAIT_IDCT,WAIT_RECON,WRITE_TILE} tile_state_t;
    frame_state_t fs;
    tile_state_t ts;
    logic [31:0] fid,tid;
    logic is_key,hidden,last_tile,entropy_complete,last_written;
    logic [127:0] wanted_tag;
    logic [1:0] plane,scale_code;
    logic [2:0] dispatch;
    logic [15:0] packet_bytes;
    logic [16:0] blocks;
    logic [1023:0] held_coefficients;
    logic [10:0] q_index;
    logic byte_pending,q_pending,ref_pending,ref_received;
    logic [31:0] held_ref_tag;
    logic [511:0] held_ref_pixels;
    logic e_cfg_ready,e_valid,e_ready,e_last,e_busy,e_done,e_error;
    logic [1023:0] e_coefficients;
    logic [16:0] e_index;
    logic [7:0] e_code;
    logic s_cfg_ready,s_valid,s_ready,s_hidden,s_last,s_error;
    logic [1023:0] s_coefficients;
    logic [16:0] s_index;
    logic [6:0] s_x;
    logic [5:0] s_y;
    logic [7:0] s_code;
    logic dq_ready,dq_valid,dq_out_ready,dq_error;
    logic [31:0] dq_id;
    logic [1279:0] dq_tile;
    logic idct_ready,idct_valid,idct_out_ready,idct_error;
    logic [31:0] idct_id;
    logic [1535:0] residual;
    logic recon_ready,recon_valid,recon_error;
    logic [31:0] recon_id;
    logic [511:0] recon_pixels;
    logic rows_ready,rows_tile_ready,rows_result_valid,rows_error;
    logic [7:0] rows_code;
    logic fail_now,fail_for_tag_valid,kill,configure_fire,start_fire,write_fire,rows_fire,tile_complete;
    logic memory_acked,rows_acked,write_pending;
    logic [7:0] fail_code;
    logic [255:0] hash_value;

    assign busy=fs!=IDLE;
    assign start_ready=fs==IDLE&&e_cfg_ready&&rows_ready&&!q_pending&&
                       !ref_pending&&!byte_pending&&!write_pending&&!rst&&!abort_i;
    assign start_fire=start_valid&&start_ready;
    assign plane_cfg_ready=fs==PLANE_WAIT&&!abort_i&&!rst;
    assign configure_fire=fs==CONFIGURE&&e_cfg_ready&&s_cfg_ready&&!kill;
    assign rd_req_plane=plane;
    assign q_req_valid=fs==RUN_PLANE&&ts==REQUEST_Q&&!kill;
    assign q_req_index=q_index;
    assign ref_req_valid=fs==RUN_PLANE&&ts!=TAKE_TILE&&!is_key&&!hidden&&
                         !ref_pending&&!ref_received&&!kill;
    assign ref_req_tile=tid;
    assign ref_rsp_ready=ref_pending&&!rst;
    assign s_ready=fs==RUN_PLANE&&ts==TAKE_TILE&&!kill;
    assign dq_out_ready=ts==WAIT_DQ&&idct_ready&&!kill;
    assign idct_out_ready=ts==WAIT_IDCT&&recon_ready&&!kill;
    // Each fork branch holds valid independently until acknowledged.
    assign tile_valid=fs==RUN_PLANE&&ts==WRITE_TILE&&recon_valid&&
                      !memory_acked&&!write_pending&&!kill;
    assign write_fire=tile_valid&&tile_ready;
    assign rows_fire=fs==RUN_PLANE&&ts==WRITE_TILE&&recon_valid&&
                     !rows_acked&&rows_tile_ready&&!kill;
    assign tile_complete=fs==RUN_PLANE&&ts==WRITE_TILE&&
                        (memory_acked||write_fire)&&(rows_acked||rows_fire)&&!kill;
    assign tile_frame_id=fid;
    assign tile_plane=plane;
    assign tile_index=recon_id[16:0];
    assign tile_pixels=recon_pixels;
    assign tile_last=plane==2&&last_tile;
    assign digest=hash_value;
    assign tag_valid=fs==RESULT_HOLD&&!kill&&!fail_for_tag_valid;
    // Reachable RESULT_HOLD always has no accepted write outstanding.
    // Independently compute only errors that can qualify tag_valid there.
    // Keep the actual fail_now/fail_code priority chain below unchanged.
    always_comb begin
        fail_for_tag_valid=0;
        if(fs!=IDLE&&fs!=DRAIN)begin
            if(fs==RUN_PLANE&&e_error)fail_for_tag_valid=1;
            else if(s_error)fail_for_tag_valid=1;
            else if(dq_valid&&dq_error)fail_for_tag_valid=1;
            else if(idct_valid&&idct_error)fail_for_tag_valid=1;
            else if(recon_valid&&(recon_error||recon_id!=tid))fail_for_tag_valid=1;
            else if(rows_error)fail_for_tag_valid=1;
        end
    end
    always_comb begin
        fail_now=0;fail_code=0;
        if(fs!=IDLE&&fs!=DRAIN)begin
            if(write_done&&write_pending&&write_error)begin fail_now=1;fail_code=8'h61;end
            else if(fs==RUN_PLANE&&e_error)begin fail_now=1;fail_code=8'h10|(e_code&8'h0f);end
            else if(s_error)begin fail_now=1;fail_code=8'h20|(s_code&8'h0f);end
            else if(dq_valid&&dq_error)begin fail_now=1;fail_code=8'h31;end
            else if(idct_valid&&idct_error)begin fail_now=1;fail_code=8'h32;end
            else if(recon_valid&&(recon_error||recon_id!=tid))begin fail_now=1;fail_code=8'h33;end
            else if(rows_error)begin fail_now=1;fail_code=8'h40|(rows_code&8'h0f);end
            else if(fs==HASH_WAIT&&rows_result_valid&&hash_value[255:128]!=wanted_tag)
                begin fail_now=1;fail_code=8'h50;end
        end
        kill=abort_i||fs==DRAIN;
    end

    always_ff @(posedge clk)begin
        if(rst)begin
            fs<=IDLE;ts<=TAKE_TILE;fid<=0;tid<=0;is_key<=0;wanted_tag<=0;
            plane<=0;dispatch<=0;packet_bytes<=0;blocks<=0;held_coefficients<=0;
            hidden<=0;last_tile<=0;entropy_complete<=0;last_written<=0;
            q_index<=0;scale_code<=0;byte_pending<=0;q_pending<=0;ref_pending<=0;ref_received<=0;
            held_ref_tag<=0;held_ref_pixels<=0;error<=0;error_code<=0;aborted<=0;
            accepted_tiles<=0;cycle_count<=0;memory_acked<=0;rows_acked<=0;write_pending<=0;
        end else begin
            aborted<=0;
            if(busy&&fs!=DRAIN)cycle_count<=cycle_count+1;
            if(write_fire)begin memory_acked<=1;write_pending<=1;end
            if(write_done&&write_pending)write_pending<=0;
            if(rows_fire)rows_acked<=1;
            if(rd_req_valid&&rd_req_ready)byte_pending<=1;
            if(rd_rsp_valid&&rd_rsp_ready)byte_pending<=0;
            if(q_req_valid&&q_req_ready)q_pending<=1;
            if(q_rsp_valid&&q_pending)q_pending<=0;
            if(ref_req_valid&&ref_req_ready)ref_pending<=1;
            if(ref_rsp_valid&&ref_rsp_ready)begin
                ref_pending<=0;
                if(!kill)begin ref_received<=1;held_ref_tag<=ref_rsp_tile;
                    held_ref_pixels<=ref_rsp_pixels;end
            end
            if((abort_i&&fs!=IDLE&&fs!=DRAIN)||fail_now)begin
                fs<=DRAIN;ts<=TAKE_TILE;
                if(fail_now)begin error<=1;error_code<=fail_code;end
            end else case(fs)
                IDLE:if(start_fire)begin
                    fs<=PLANE_WAIT;ts<=TAKE_TILE;fid<=frame_id;is_key<=key;
                    wanted_tag<=expected_tag;plane<=0;error<=0;error_code<=0;
                    accepted_tiles<=0;cycle_count<=0;ref_received<=0;
                end
                PLANE_WAIT:if(plane_cfg_valid&&plane_cfg_ready)begin
                    if(plane_cfg_plane!=plane)begin error<=1;error_code<=1;fs<=DRAIN;end
                    else begin dispatch<=plane_cfg_dispatch;packet_bytes<=plane_cfg_bytes;
                        blocks<=plane_cfg_blocks;fs<=CONFIGURE;
                        entropy_complete<=0;last_written<=0;end
                end
                CONFIGURE:if(configure_fire)begin fs<=RUN_PLANE;ts<=TAKE_TILE;end
                RUN_PLANE:begin
                    if(e_done)entropy_complete<=1;
                    if(entropy_complete&&last_written&&ts==TAKE_TILE)begin
                        if(plane==2)fs<=HASH_WAIT;
                        else begin plane<=plane+1;fs<=PLANE_WAIT;end
                    end
                    case(ts)
                        TAKE_TILE:if(s_valid&&s_ready)begin
                            memory_acked<=0;rows_acked<=0;
                            held_coefficients<=s_coefficients;
                            tid<={13'd0,plane,s_index};hidden<=s_hidden;last_tile<=s_last;
                            q_index<=plane==0?11'((int'(s_y)/2)*45+int'(s_x)/2):
                                                       11'(int'(s_y)*45+int'(s_x));
                            ref_received<=0;ts<=REQUEST_Q;
                        end
                        REQUEST_Q:if(q_req_valid&&q_req_ready)ts<=WAIT_Q;
                        WAIT_Q:if(q_rsp_valid&&q_pending)begin scale_code<=q_rsp_code;ts<=SEND_DQ;end
                        SEND_DQ:if(dq_ready)ts<=WAIT_DQ;
                        WAIT_DQ:if(dq_valid&&dq_out_ready)ts<=WAIT_IDCT;
                        WAIT_IDCT:if(idct_valid&&idct_out_ready)ts<=WAIT_RECON;
                        WAIT_RECON:if(recon_valid)ts<=WRITE_TILE;
                        WRITE_TILE:if(tile_complete)begin
                            ts<=TAKE_TILE;ref_received<=0;accepted_tiles<=accepted_tiles+1;
                            if(last_tile)last_written<=1;
                        end
                        default:ts<=TAKE_TILE;
                    endcase
                end
                HASH_WAIT:if(rows_result_valid&&!fail_now&&!write_pending)fs<=RESULT_HOLD;
                RESULT_HOLD:if(tag_valid&&tag_ready)fs<=IDLE;
                DRAIN:if(!e_busy&&!byte_pending&&!q_pending&&!ref_pending&&!write_pending)begin
                    fs<=IDLE;aborted<=1;ref_received<=0;
                end
                default:fs<=DRAIN;
            endcase
        end
    end

    cu71_ab38_decoder_intervalregs_v019 entropy(
        .clk,.rst,.abort_i(kill),.cfg_valid(configure_fire),.cfg_ready(e_cfg_ready),
        .cfg_dispatch(dispatch),.cfg_packet_bytes(packet_bytes),.cfg_blocks(blocks),
        .cfg_blocks_w(dispatch==6?9'd1:(plane==0?9'd90:9'd45)),
        .rd_req_valid,.rd_req_ready,.rd_req_addr,.rd_rsp_valid,.rd_rsp_ready,.rd_rsp_data,
        .tile_valid(e_valid),.tile_ready(e_ready),.tile_coefficients(e_coefficients),
        .tile_index(e_index),.tile_last(e_last),.busy(e_busy),.done(e_done),
        .aborted(),.error(e_error),.error_code(e_code),.debug_state(),
        .decoded_decisions(),.renormalizations(),.memory_reads(),.output_stall_cycles());
    cu71_expand_validpipe_v001 scatter(
        .clk,.rst,.abort_i(kill),.cfg_valid(configure_fire),.cfg_ready(s_cfg_ready),
        .cfg_plane(plane),.cfg_dispatch(dispatch),.cfg_blocks(blocks),
        .in_valid(e_valid),.in_ready(e_ready),.in_coefficients(e_coefficients),.in_index(e_index),.in_last(e_last),
        .out_valid(s_valid),.out_ready(s_ready),.out_coefficients(s_coefficients),
        .out_index(s_index),.out_x(s_x),.out_y(s_y),.out_hidden(s_hidden),.out_last(s_last),
        .busy(),.done(),.error(s_error),.error_code(s_code));
    cu71_dequant_validpipe dequant(
        .clk,.rst,.abort_i(kill),.in_valid(fs==RUN_PLANE&&ts==SEND_DQ&&!kill),.in_ready(dq_ready),
        .in_id(tid),.in_coefficients(held_coefficients),.in_chroma(plane!=0),.in_scale_code(scale_code),
        .out_valid(dq_valid),.out_ready(dq_out_ready),.out_id(dq_id),.out_dequantized(dq_tile),.out_error(dq_error));
    cu71_idct_inputstage_v001 inverse(
        .clk,.rst,.abort_frame(kill),.in_valid(dq_valid&&ts==WAIT_DQ&&!kill),.in_ready(idct_ready),
        .in_id(dq_id),.in_tile(dq_tile),.out_valid(idct_valid),.out_ready(idct_out_ready),
        .out_id(idct_id),.out_tile(residual),.out_error(idct_error),.active_cycles());
    cu71_reconstruct_resetlight reconstruct(
        .clk,.rst,.abort_i(kill),.in_valid(idct_valid&&ts==WAIT_IDCT&&!kill),.in_ready(recon_ready),
        .in_id(idct_id),.in_key(is_key),.in_hidden(hidden),.in_residual(residual),
        .ref_valid(ref_received),.ref_ready(),.ref_tile_id(held_ref_tag),.ref_pixels(held_ref_pixels),
        .out_valid(recon_valid),.out_ready(tile_complete),.out_id(recon_id),.out_pixels(recon_pixels),.out_error(recon_error));
    cu71_rows_sha256_schedule_v015 #(.STRIP_BANKS(2),.HASH_BLOCKS(2)) canonical(
        .clk,.rst,.abort_i(kill),.start_valid(start_fire),.start_ready(rows_ready),.frame_id,.key,
        .tile_valid(recon_valid&&fs==RUN_PLANE&&ts==WRITE_TILE&&!rows_acked&&!kill),
        .tile_ready(rows_tile_ready),.tile_pixels(recon_pixels),.tile_frame_id(fid),.tile_key(is_key),
        .tile_plane(plane),.tile_index(recon_id[16:0]),.tile_last(plane==2&&last_tile),
        .data_valid(),.data_ready(),.data(),.data_last(),
        .result_valid(rows_result_valid),.result_ready(fs==RESULT_HOLD&&tag_ready&&!kill),.digest(hash_value),
        .busy(),.done(),.error(rows_error),.error_code(rows_code),
        .accepted_tiles(),.emitted_bytes(),.strip_word_writes(),.strip_word_reads(),.input_stall_cycles(),.output_stall_cycles(),
        .write_busy(),.expected_plane(),.expected_index(),.hash_blocks(),.hash_rounds(),.hash_bytes(),.hash_padding(),
        .hash_input_stalls(),.hash_output_stalls(),.rows_busy(),.rows_aborted(),.hash_busy(),.hash_aborted(),
        .hash_fill_state(),.hash_core_state());
endmodule
