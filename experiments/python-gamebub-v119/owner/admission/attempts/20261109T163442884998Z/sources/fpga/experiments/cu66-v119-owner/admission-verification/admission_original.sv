// V91i2a provisional mode/scale retention and synchronous replay, forked from frozen V91i1.
// Structural admission is still not frame acceptance; no accepted-state commit.
module admission_original (
    input logic clk, reset, start, abort_packet,
    input logic cache_write,
    input logic [10:0] cache_index,
    input logic [1:0] cache_data,
    input logic replay_req,
    input logic [31:0] replay_addr,
    output logic replay_ready, replay_rsp_valid,
    output logic [7:0] replay_data,
    output logic [31:0] replay_rsp_addr, replay_rsp_epoch,
    input logic lookup_req,
    input logic [12:0] lookup_tile,
    input logic [10:0] lookup_cell,
    output logic lookup_rsp_valid,
    output logic [1:0] lookup_mode, lookup_scale,
    input logic [31:0] packet_bytes, epoch,
    input logic accepted_ref_valid, accepted_qcache_valid,
    input logic [31:0] accepted_ref_fid,
    input logic [63:0] accepted_ref_generation,
    input logic in_valid, in_last,
    input logic [7:0] in_data,
    output logic in_ready, busy,
    output logic receipt_valid,
    input logic receipt_ready,
    output logic [7:0] error,
    output logic [31:0] receipt_epoch, fid, refid,
    output logic [63:0] generation,
    output logic key_frame,
    output logic [31:0] mode_bytes, qmap_bytes /* verilator public_flat_rw */, hud_bytes, data_bytes,
    output logic [31:0] plane_blocks [0:2],
    output logic [31:0] plane_offset [0:2],
    output logic [31:0] plane_length [0:2],
    output logic [1:0] plane_entropy [0:2],
    output logic stage_read_req, stage_read_rsp, stage_write, stage_pending, stage_cancel,
    output logic [31:0] stage_read_addr, stage_rsp_addr, stage_req_epoch, stage_rsp_epoch,
    output logic [7:0] stage_read_data,
    output logic [7:0] debug_state,
    output logic [63:0] count_cycles, count_inputs, count_stage_reads,
    output logic [63:0] count_stage_responses, count_receipt_wait,
    output logic [31:0] required_cells,
    output logic verify_coord_valid,
    output logic [1:0] verify_plane,
    output logic [31:0] verify_tile,
    output logic [10:0] verify_cell,
    output logic [6:0] verify_column,
    output logic verify_odd,
    output logic [10:0] verify_pair_base,
    output logic verify_residual,
    output logic [10:0] verify_active_index,
    output logic verify_active_value,
    output logic [31:0] verify_q_index, verify_q_runs,
    output logic [6:0] verify_q_remaining,
    output logic [1:0] verify_q_value,
    output logic [7:0] verify_q_selected, verify_q_cached,
    output logic [31:0] verify_header_index,
    output logic [34:0] verify_header_mode_start, verify_header_residual_start,
    output logic [34:0] verify_header_hud_tail, verify_header_residual_end, verify_header_packet_total
);
    localparam logic [7:0] IDLE=0, RX=1, CRC_CHECK=2, HEADER_LOAD=3,
        HEADER_BYTE=4, HEADER_CHECK=5, KEY_TILE=6, GROUP_BEGIN=7,
        MODE_BIT=8, MODE_LOADED=9, GROUP_TILE=10, GROUP_NEXT=11,
        MODE_END=12, ACTIVE_SCAN=13, Q_LOAD=14, Q_BYTE=15, Q_CHECK=16,
        Q_RUN=17, PLANE_BEGIN=18, CHUNK_NUMBER=19, CHUNK_BLOCKS=20,
        CHUNK_LENGTH=21, CHUNK_MAGIC=22, PLANE_NEXT=23, COMPLETE=24,
        RECEIPT=25, FINISHED=26, FAILED=27, FETCH_REQ=28,
        FETCH_WAIT=29, WORD_BYTE=30, ACTIVE_CLEAR=31, Q_FILL=32;
    localparam integer MAX_BYTES=49152;
    logic [7:0] state /* verilator public_flat_rw */, fetch_return, word_return;
    logic [7:0] memory [0:MAX_BYTES-1];
    logic [7:0] header [0:127] /* verilator public_flat_rw */;
    logic [7:0] qbuffer [0:353] /* verilator public_flat_rw */;
    // V107: select a run byte on the existing edge before Q_RUN.
    logic [7:0] q_run_byte /* verilator public_flat_rw */;
    logic active_cell [0:1349];
    logic [6:0] q_remaining /* verilator public_flat_rw */;
    logic [1:0] q_value /* verilator public_flat_rw */;
    logic [7:0] ram_data, byte_value /* verilator public_flat_rw */;
    logic [31:0] ram_addr, ram_epoch, fetch_addr;
    logic [31:0] size_bytes /* verilator public_flat_rw */, received, outer_crc, outer_trailer;
    logic snapshot_valid /* verilator public_flat_rw */, snapshot_cache;
    logic [31:0] snapshot_fid /* verilator public_flat_rw */;
    logic [63:0] snapshot_generation /* verilator public_flat_rw */;
    logic [31:0] cursor, q_start /* verilator public_flat_rw */, residual_start /* verilator public_flat_rw */, residual_end /* verilator public_flat_rw */;
    // V107: exact full-width header sums captured on existing byte-load edges.
    logic [34:0] header_mode_start /* verilator public_flat_rw */, header_residual_start /* verilator public_flat_rw */, header_hud_tail /* verilator public_flat_rw */;
    logic [34:0] header_residual_end /* verilator public_flat_rw */, header_packet_total /* verilator public_flat_rw */;
    logic [31:0] header_index /* verilator public_flat_rw */, q_index /* verilator public_flat_rw */, q_crc, q_trailer, q_runs /* verilator public_flat_rw */;
    logic [31:0] tile, group_end, group_visible, mixed_ones;
    logic [1:0] plane, group_tag;
    // V105: reachable parser coordinates; tile/group_end remain 32-bit state.
    logic coord_valid /* verilator public_flat_rw */;
    logic [10:0] coord_cell, coord_pair_base;
    logic [6:0] coord_y_column;
    logic coord_y_odd;
    logic [7:0] bit_cache;
    logic [3:0] bits_left;
    logic tag_second, first_tag_bit, mixed_bit;
    logic [31:0] mode_cursor, active_index, word_cursor, word_index;
    logic [23:0] word_acc;
    logic [31:0] word_value, chunk_length;
    integer i;

    // V107: external writes on A, Q_FILL/registered lookup on B.
    wire scale_live=!reset&&!start&&!abort_packet;
    wire scale_fill=scale_live&&state==Q_FILL;
    wire scale_lookup=scale_live&&lookup_req&&state==FINISHED;
    cu66_scale_tdp_v107 scale_store(.clk(clk),.a_write(scale_live&&cache_write),
        .a_addr(cache_index),.a_data(cache_data),.b_write(scale_fill),.b_read(scale_lookup),
        .b_addr(scale_fill?q_runs[10:0]:lookup_cell),.b_data(q_value),.b_q(lookup_scale));

    function automatic logic [31:0] crc_byte(input logic [31:0] old_crc, input logic [7:0] b);
        logic [31:0] c;
        begin
            c=old_crc^{24'd0,b};
            for(integer k=0;k<8;k=k+1)c=c[0]?(c>>1)^32'hedb88320:(c>>1);
            return c;
        end
    endfunction
    function automatic logic [31:0] h32(input integer n);
        return {header[n],header[n+1],header[n+2],header[n+3]};
    endfunction
    function automatic logic [15:0] h16(input integer n);
        return {header[n],header[n+1]};
    endfunction
    function automatic logic hidden(input logic [1:0] p, input logic [31:0] t);
        if(p!=0)return t>=1046&&t<=1064;
        return (t>=633&&t<=651)||(t>=723&&t<=741)||
            (t>=993&&t<=1011)||(t>=1083&&t<=1101)||
            (t>=4071&&t<=4110)||(t>=4161&&t<=4200)||
            (t>=4251&&t<=4290)||(t>=4431&&t<=4460)||
            (t>=4521&&t<=4550);
    endfunction
    function automatic logic [31:0] tile_count(input logic [1:0] p);
        return p==0?32'd5400:32'd1350;
    endfunction
    function automatic logic [31:0] cell_index(input logic [1:0] p, input logic [31:0] t);
        return p==0?((t/90)/2)*45+(t%90)/2:t;
    endfunction
    function automatic logic [31:0] visible_group(input logic [1:0] p, input logic [31:0] t);
        logic [31:0] n;
        begin
            n=0;
            for(integer k=0;k<16;k=k+1)
                if(t+32'(k)<tile_count(p)&&!hidden(p,t+32'(k)))n=n+1;
            return n;
        end
    endfunction
    // V112_VISIBILITY_BEGIN: private preparation on the existing predecessor
    // edge, using the successor key when GROUP_NEXT changes plane/tile.
    // The mask retains the generic uint32 t+k wrap and all four plane values.
    logic [15:0] group_visibility_mask;
    function automatic logic [15:0] visibility_mask(input logic [1:0] p,input logic [31:0] t);
        logic [15:0] m;
        begin
            for(integer k=0;k<16;k=k+1)
                m[k]=t+32'(k)<tile_count(p)&&!hidden(p,t+32'(k));
            return m;
        end
    endfunction
    function automatic logic [4:0] visibility_count(input logic [15:0] m);
        logic [1:0] pair_count [0:7];
        logic [2:0] quad_count [0:3];
        logic [3:0] oct_count [0:1];
        begin
            for(integer k=0;k<8;k=k+1)
                pair_count[k]={1'b0,m[2*k]}+{1'b0,m[2*k+1]};
            for(integer k=0;k<4;k=k+1)
                quad_count[k]={1'b0,pair_count[2*k]}+{1'b0,pair_count[2*k+1]};
            for(integer k=0;k<2;k=k+1)
                oct_count[k]={1'b0,quad_count[2*k]}+{1'b0,quad_count[2*k+1]};
            return {1'b0,oct_count[0]}+{1'b0,oct_count[1]};
        end
    endfunction
    always_ff @(posedge clk)begin
        if(state==HEADER_CHECK)group_visibility_mask<=visibility_mask(2'd0,32'd0);
        else if(state==GROUP_NEXT)begin
            if(tile==tile_count(plane))group_visibility_mask<=visibility_mask(plane+2'd1,32'd0);
            else group_visibility_mask<=visibility_mask(plane,tile);
        end
    end
`ifndef SYNTHESIS
    // Independent original scalar sum at the actual unchanged consume edge.
    always_ff @(posedge clk)if(!reset&&!start&&!abort_packet&&state==GROUP_BEGIN)
        assert(32'(visibility_count(group_visibility_mask))==visible_group(plane,tile))
            else $fatal(1,"V112 prepared group visibility owner mismatch");
`endif
    // V112_VISIBILITY_END

    // V116_SELECTED_BEGIN: two existing edges separate plane selection from
    // the original uint32 wrapped length expression. No fetch is advanced.
    logic selected_valid, selected_limit_valid;
    logic [1:0] selected_plane;
    logic [31:0] selected_owner, selected_blocks, selected_limit;
    logic selected_zero;
    always_ff @(posedge clk)begin
        if(reset||start||abort_packet)begin
            selected_valid<=0;selected_limit_valid<=0;
        end else if(state==PLANE_BEGIN)begin
            selected_plane<=plane;selected_owner<=receipt_epoch;
            selected_blocks<=plane_blocks[plane];
            selected_zero<=plane_blocks[plane]==0;
            selected_valid<=1;selected_limit_valid<=0;
        end else if(state==PLANE_NEXT)begin
            selected_valid<=0;selected_limit_valid<=0;
        end else if(state==FETCH_REQ&&selected_valid&&!selected_limit_valid)begin
            selected_limit<=46+128*selected_blocks;
            selected_limit_valid<=1;
        end
    end
`ifndef SYNTHESIS
    // Check the complete owned tuple throughout all real fetch/word edges.
    // plane_blocks has no writer during this interval; equality to the held
    // selected count checks that stability rather than assuming it.
    always_ff @(posedge clk)if(!reset&&!start&&!abort_packet&&selected_valid&&
        (state==FETCH_REQ||state==FETCH_WAIT||state==WORD_BYTE||
         state==CHUNK_NUMBER||state==CHUNK_BLOCKS||state==CHUNK_LENGTH||
         state==CHUNK_MAGIC||state==PLANE_NEXT))begin
        assert(selected_plane==plane&&selected_owner==receipt_epoch)
            else $fatal(1,"V116 selected tuple owner/plane stability");
        assert(selected_blocks==plane_blocks[plane]&&selected_zero==(plane_blocks[plane]==0))
            else $fatal(1,"V116 selected count/zero stability");
    end
    // Literal old arithmetic and predicates, including expression width, are
    // retained at every actual consume. The residual-end bound stays separate.
    always_ff @(posedge clk)if(!reset&&!start&&!abort_packet&&
        (state==CHUNK_NUMBER||state==CHUNK_BLOCKS||state==CHUNK_LENGTH))begin
        assert(selected_valid&&selected_limit_valid&&selected_plane==plane&&selected_owner==receipt_epoch)
            else $fatal(1,"V116 selected consume without current preparation");
        assert(selected_blocks==plane_blocks[plane]&&selected_zero==(plane_blocks[plane]==0))
            else $fatal(1,"V116 selected consume count/zero");
        assert(selected_limit==46+128*plane_blocks[plane])
            else $fatal(1,"V116 selected consume literal old limit");
        if(state==CHUNK_NUMBER)
            assert((word_value!=(selected_zero?32'd0:32'd1))==
                (word_value!=(plane_blocks[plane]==0?32'd0:32'd1)))
                else $fatal(1,"V116 literal CHUNK_NUMBER predicate");
        if(state==CHUNK_BLOCKS)
            assert((word_value!=selected_blocks||word_value==0)==
                (word_value!=plane_blocks[plane]||word_value==0))
                else $fatal(1,"V116 literal CHUNK_BLOCKS predicate");
        if(state==CHUNK_LENGTH)
            assert((word_value<46||word_value>selected_limit||
                {32'd0,cursor}+4+{32'd0,word_value}>{32'd0,residual_end})==
                (word_value<46||word_value>46+128*plane_blocks[plane]||
                {32'd0,cursor}+4+{32'd0,word_value}>{32'd0,residual_end}))
                else $fatal(1,"V116 literal CHUNK_LENGTH predicate");
    end
`endif
    // V116_SELECTED_END

    task automatic reject(input logic [7:0] code);
        error<=code;state<=FAILED;
    endtask
    task automatic request_byte(input logic [31:0] address, input logic [7:0] continuation);
        fetch_addr<=address;fetch_return<=continuation;state<=FETCH_REQ;
    endtask
    task automatic request_word(input logic [31:0] address, input logic [7:0] continuation);
        word_cursor<=address;word_index<=0;word_acc<=0;word_return<=continuation;
        request_byte(address,WORD_BYTE);
    endtask
    task automatic clear_coordinate;
        coord_cell<=0;coord_pair_base<=0;coord_y_column<=0;coord_y_odd<=0;
    endtask
    task automatic advance_coordinate(input logic [4:0] delta);
        logic [6:0] next_column;
        logic [10:0] next_base;
        logic next_odd;
        begin
`ifndef SYNTHESIS
            assert(coord_valid && plane<=2 && tile<tile_count(plane));
            assert(delta>=1 && delta<=16 && tile+32'(delta)<=tile_count(plane));
`endif
            if(plane==0)begin
                next_column=coord_y_column+7'(delta);
                next_base=coord_pair_base;next_odd=coord_y_odd;
                if(next_column>=90)begin
                    next_column=next_column-7'd90;next_odd=!coord_y_odd;
                    if(coord_y_odd)next_base=coord_pair_base+11'd45;
                end
                coord_y_column<=next_column;coord_y_odd<=next_odd;
                coord_pair_base<=next_base;coord_cell<=next_base+{5'd0,next_column[6:1]};
            end else coord_cell<=coord_cell+11'(delta);
        end
    endtask
`ifndef SYNTHESIS
    // Reachable-state oracle only: no arbitrary 32-bit tile-state equivalence claim.
    always_ff @(posedge clk)begin
        if(!reset&&!start&&!abort_packet&&coord_valid)begin
            assert(plane<=2 && tile<=tile_count(plane));
            assert(32'(coord_cell)==cell_index(plane,tile));
            if(plane==0)begin
                assert(32'(coord_y_column)==tile%90);
                assert(32'(coord_y_odd)==(tile/90)%2);
                assert(32'(coord_pair_base)==(tile/180)*45);
            end else begin
                assert(coord_y_column==0 && !coord_y_odd && coord_pair_base==0);
            end
        end
    end
`endif
`ifndef SYNTHESIS
    // Only the nonterminal Q_RUN branch consumes this prefetched byte.
    // qbuffer has no writes between capture in Q_CHECK/Q_FILL and Q_RUN.
    always_ff @(posedge clk)if(!reset&&!start&&!abort_packet &&
        state==Q_RUN && q_index!=qmap_bytes-4)begin
        assert(q_run_byte==qbuffer[q_index[8:0]])
            else $fatal(1,"quant run-byte cache mismatch");
    end
`endif
`ifndef SYNTHESIS
    // Every real HEADER_CHECK follows a complete sequential header load. The
    // caches need no reset: cancelled parses cannot consume them, and a new
    // parse recaptures all fields. Prepared-state tests bind these invariants.
    always_ff @(posedge clk)if(!reset&&!start&&!abort_packet&&state==HEADER_CHECK)begin
        assert(header_mode_start==35'd128+{3'd0,h32(36)}) else $fatal(1,"header mode-start cache");
        assert(header_residual_start==35'd128+{3'd0,h32(36)}+{3'd0,h32(40)}) else $fatal(1,"header residual-start cache");
        assert(header_hud_tail==35'd4+{3'd0,h32(44)}) else $fatal(1,"header HUD-tail cache");
        assert(header_residual_end==35'd128+{3'd0,h32(36)}+{3'd0,h32(40)}+{3'd0,h32(48)}) else $fatal(1,"header residual-end cache");
        assert(header_packet_total==35'd132+{3'd0,h32(36)}+{3'd0,h32(40)}+{3'd0,h32(44)}+{3'd0,h32(48)}) else $fatal(1,"header packet-total cache");
    end
`endif
    task automatic residual_tile;
`ifndef SYNTHESIS
        assert(coord_valid && plane<=2 && tile<tile_count(plane));
        assert(coord_cell<1350 && 32'(coord_cell)==cell_index(plane,tile));
`endif
        active_cell[coord_cell]<=1'b1;
        plane_blocks[plane]<=plane_blocks[plane]+1;
    endtask

    // Canonical single mode-store write port. The full-width parser address
    // arithmetic and branch guards retain the original source semantics.
    logic mode_write_enable;
    logic [12:0] mode_write_address;
    logic [1:0] mode_write_data;
    always_comb begin
        mode_write_enable=1'b0;
        mode_write_address=13'd0;
        mode_write_data=2'd0;
        if(!reset&&!start&&!abort_packet)begin
            if(state==ACTIVE_CLEAR&&active_index!=8100)begin
                mode_write_enable=1'b1;
                mode_write_address=active_index[12:0];
                mode_write_data=2'd1;
            end else if(state==KEY_TILE&&tile!=tile_count(plane))begin
                mode_write_enable=1'b1;
                mode_write_address=13'((plane==0?0:plane==1?5400:6750)+tile);
                mode_write_data=hidden(plane,tile)?2'd1:2'd2;
            end else if(state==MODE_BIT&&bits_left!=0&&mixed_bit)begin
                mode_write_enable=1'b1;
                mode_write_address=13'((plane==0?0:plane==1?5400:6750)+tile);
                mode_write_data=bit_cache[7]?2'd2:2'd0;
            end else if(state==GROUP_TILE&&tile!=group_end)begin
                if(hidden(plane,tile)||group_tag==0)begin
                    mode_write_enable=1'b1;
                    mode_write_address=13'((plane==0?0:plane==1?5400:6750)+tile);
                    mode_write_data=hidden(plane,tile)?2'd1:2'd0;
                end else if(group_tag==1)begin
                    mode_write_enable=1'b1;
                    mode_write_address=13'((plane==0?0:plane==1?5400:6750)+tile);
                    mode_write_data=2'd2;
                end
            end
        end
    end
    cu66_mode_store_v107 mode_store(.clk(clk),.write_enable(mode_write_enable),
        .write_address(mode_write_address),.write_data(mode_write_data),
        .read_enable(lookup_req&&state==FINISHED&&!reset&&!start&&!abort_packet),
        .read_address(lookup_tile),.q(lookup_mode));

    assign replay_ready=state==FINISHED&&!reset&&!start&&!abort_packet&&replay_addr<size_bytes;
    assign replay_data=ram_data;
    assign replay_rsp_addr=ram_addr;
    assign replay_rsp_epoch=ram_epoch;
    assign in_ready=state==RX&&!reset&&!start&&!abort_packet;
    assign receipt_valid=state==RECEIPT&&!reset&&!start&&!abort_packet;
    assign busy=state!=IDLE&&state!=FINISHED&&state!=FAILED;
    assign stage_read_req=state==FETCH_REQ&&!reset&&!start&&!abort_packet;
    assign stage_read_rsp=state==FETCH_WAIT&&!reset&&!start&&!abort_packet;
    assign stage_write=in_valid&&in_ready;
    assign stage_pending=state==FETCH_WAIT;
    assign stage_cancel=reset||start||abort_packet;
    assign stage_read_addr=fetch_addr;
    assign stage_rsp_addr=ram_addr;
    assign stage_req_epoch=receipt_epoch;
    assign stage_rsp_epoch=ram_epoch;
    assign stage_read_data=ram_data;
    assign debug_state=state;

    // One registered, read-first packet RAM port. Selection retains stage priority.
    logic memory_read_enable;
    logic [15:0] memory_read_address;
    assign memory_read_enable=stage_read_req || (replay_req && replay_ready);
    assign memory_read_address=stage_read_req ? fetch_addr[15:0] : replay_addr[15:0];
    always_ff @(posedge clk) begin
        if(stage_write)memory[received[15:0]]<=in_data;
        if(memory_read_enable)ram_data<=memory[memory_read_address];
    end

    always_ff @(posedge clk) begin
        replay_rsp_valid<=replay_req&&replay_ready;
        lookup_rsp_valid<=lookup_req&&state==FINISHED&&!reset&&!start&&!abort_packet;
        if(stage_read_req)begin
            ram_addr<=fetch_addr;ram_epoch<=receipt_epoch;
        end else if(replay_req&&replay_ready)begin
            ram_addr<=replay_addr;ram_epoch<=receipt_epoch;
        end
        if(reset||start||abort_packet)begin
            coord_valid<=0;
            state<=IDLE;error<=0;receipt_epoch<=epoch;
            replay_rsp_valid<=0;lookup_rsp_valid<=0;
            size_bytes<=packet_bytes;received<=0;outer_crc<=32'hffffffff;outer_trailer<=0;
            snapshot_valid<=accepted_ref_valid;snapshot_cache<=accepted_qcache_valid;
            snapshot_fid<=accepted_ref_fid;snapshot_generation<=accepted_ref_generation;
            fid<=0;refid<=0;generation<=0;key_frame<=0;
            mode_bytes<=0;qmap_bytes<=0;hud_bytes<=0;data_bytes<=0;required_cells<=0;
            count_cycles<=0;count_inputs<=0;count_stage_reads<=0;count_stage_responses<=0;count_receipt_wait<=0;
            for(i=0;i<3;i=i+1)begin
                plane_blocks[i]<=0;plane_offset[i]<=0;plane_length[i]<=0;plane_entropy[i]<=0;
            end
            // Backing RAM, header and QM caches are never reset; each parser
            // reaches only bytes written by this transaction before reading.
            if(start&&!reset&&!abort_packet)begin
                if(packet_bytes<132||packet_bytes>MAX_BYTES)begin state<=FAILED;error<=1;end
                else begin active_index<=0;state<=ACTIVE_CLEAR;end
            end
        end else begin
            if(busy)count_cycles<=count_cycles+1;
            if(stage_read_req)count_stage_reads<=count_stage_reads+1;
            if(stage_read_rsp)count_stage_responses<=count_stage_responses+1;
            case(state)
                ACTIVE_CLEAR:begin
                    if(active_index==8100)state<=RX;
                    else begin
                        if(active_index<1350)active_cell[active_index[10:0]]<=0;
                        active_index<=active_index+1;
                    end
                end
                RX: if(in_valid&&in_ready)begin
                    count_inputs<=count_inputs+1;received<=received+1;
                    if(received<size_bytes-4)outer_crc<=crc_byte(outer_crc,in_data);
                    else outer_trailer<={outer_trailer[23:0],in_data};
                    if(in_last!=(received==size_bytes-1))reject(2);
                    else if(received==size_bytes-1)state<=CRC_CHECK;
                end
                CRC_CHECK:begin
                    if((~outer_crc)!=outer_trailer)reject(3);
                    else begin header_index<=0;state<=HEADER_LOAD;end
                end
                HEADER_LOAD:request_byte(header_index,HEADER_BYTE);
                HEADER_BYTE:begin
                    header[header_index[6:0]]<=byte_value;
                    // The current field's final byte has not reached header[]
                    // yet; forward it while the preceding bytes are stable.
                    if(header_index==39)
                        header_mode_start<=35'd128+{3'd0,header[36],header[37],header[38],byte_value};
                    if(header_index==43)
                        header_residual_start<=header_mode_start+{3'd0,header[40],header[41],header[42],byte_value};
                    if(header_index==47)
                        header_hud_tail<=35'd4+{3'd0,header[44],header[45],header[46],byte_value};
                    if(header_index==51)
                        header_residual_end<=header_residual_start+{3'd0,header[48],header[49],header[50],byte_value};
                    if(header_index==55)
                        header_packet_total<=header_residual_end+header_hud_tail;
                    if(header_index==127)state<=HEADER_CHECK;
                    else begin header_index<=header_index+1;state<=HEADER_LOAD;end
                end
                HEADER_CHECK:begin : header_validation
                    logic padding_ok;
                    padding_ok=1;
                    for(integer k=116;k<128;k=k+1)if(header[k]!=0)padding_ok=0;
                    if(h32(0)!=32'h43533838||header[4]!=1||header[6]!=16||
                       h16(28)!=32||h32(32)!=65536||
                       (header[5]==1?header[7]!=0:header[7]!=3))reject(4);
                    else if(header[5]>1||h16(24)!=720||h16(26)!=480||h16(30)!=0||!padding_ok||
                        h32(36)>976||h32(40)<16||h32(40)>354||h32(44)<110||h32(44)>49152||
                        header_packet_total!={3'd0,size_bytes})reject(5);
                    else if(h32(8)==32'hffffffff||{h32(16),h32(20)}==0||
                        (snapshot_valid&&(h32(8)<=snapshot_fid||{h32(16),h32(20)}<=snapshot_generation)))reject(6);
                    else if(header[5]==1?h32(12)!=32'hffffffff:(!snapshot_valid||h32(12)!=snapshot_fid))reject(7);
                    else if(header[5]==1&&h32(36)!=0)reject(8);
                    else begin
                        fid<=h32(8);refid<=h32(12);generation<={h32(16),h32(20)};key_frame<=header[5]==1;
                        mode_bytes<=h32(36);qmap_bytes<=h32(40);hud_bytes<=h32(44);data_bytes<=h32(48);
                        q_start<=header_mode_start[31:0];residual_start<=header_residual_start[31:0];
                        residual_end<=header_residual_end[31:0];
                        clear_coordinate();coord_valid<=1;
                        plane<=0;tile<=0;mode_cursor<=128;bits_left<=0;bit_cache<=0;
                        state<=header[5]==1?KEY_TILE:GROUP_BEGIN;
                    end
                end
                KEY_TILE:begin
                    if(tile==tile_count(plane))begin
                        clear_coordinate();
                        tile<=0;
                        if(plane==2)state<=MODE_END;else plane<=plane+1;
                    end else begin
                        
                        if(!hidden(plane,tile))residual_tile();
                        advance_coordinate(1);tile<=tile+1;
                    end
                end
                GROUP_BEGIN:begin
                    group_end<=tile+16<tile_count(plane)?tile+16:tile_count(plane);
                    group_visible<=32'(visibility_count(group_visibility_mask));mixed_ones<=0;
                    tag_second<=0;mixed_bit<=0;state<=MODE_BIT;
                end
                MODE_BIT:begin
                    if(bits_left==0)begin
                        if(mode_cursor>=128+mode_bytes)reject(8);
                        else begin mode_cursor<=mode_cursor+1;request_byte(mode_cursor,MODE_LOADED);end
                    end else begin
                        bit_cache<={bit_cache[6:0],1'b0};bits_left<=bits_left-1;
                        if(mixed_bit)begin
                            
                            if(bit_cache[7])begin residual_tile();mixed_ones<=mixed_ones+1;end
                            advance_coordinate(1);tile<=tile+1;state<=GROUP_TILE;
                        end else if(!tag_second)begin first_tag_bit<=bit_cache[7];tag_second<=1;end
                        else begin
                            group_tag<={first_tag_bit,bit_cache[7]};
                            if(group_visible==0)begin
                                if({first_tag_bit,bit_cache[7]}!=3)reject(8);
                                else begin advance_coordinate(5'(group_end-tile));tile<=group_end;state<=GROUP_NEXT;end
                            end else if({first_tag_bit,bit_cache[7]}==3)reject(8);
                            else state<=GROUP_TILE;
                        end
                    end
                end
                MODE_LOADED:begin bit_cache<=byte_value;bits_left<=8;state<=MODE_BIT;end
                GROUP_TILE:begin
                    if(tile==group_end)begin
                        if(group_tag==2&&(mixed_ones==0||mixed_ones==group_visible))reject(8);
                        else state<=GROUP_NEXT;
                    end else if(hidden(plane,tile)||group_tag==0)begin
                        
                        advance_coordinate(1);tile<=tile+1;
                    end else if(group_tag==1)begin
                        
                        residual_tile();advance_coordinate(1);tile<=tile+1;
                    end
                    else begin mixed_bit<=1;state<=MODE_BIT;end
                end
                GROUP_NEXT:begin
                    if(tile==tile_count(plane))begin
                        if(plane==2)state<=MODE_END;
                        else begin clear_coordinate();plane<=plane+1;tile<=0;state<=GROUP_BEGIN;end
                    end else state<=GROUP_BEGIN;
                end
                MODE_END:begin
                    coord_valid<=0;
                    if(!key_frame&&(mode_cursor!=128+mode_bytes||bit_cache!=0))reject(8);
                    else begin active_index<=0;required_cells<=0;state<=ACTIVE_SCAN;end
                end
                ACTIVE_SCAN:begin
                    if(active_index==1350)begin q_index<=0;q_crc<=32'hffffffff;q_trailer<=0;state<=Q_LOAD;end
                    else begin
                        if(active_cell[active_index[10:0]])required_cells<=required_cells+1;
                        active_index<=active_index+1;
                    end
                end
                Q_LOAD:request_byte(q_start+q_index,Q_BYTE);
                Q_BYTE:begin
                    qbuffer[q_index[8:0]]<=byte_value;
                    if(q_index<qmap_bytes-4)q_crc<=crc_byte(q_crc,byte_value);
                    else q_trailer<={q_trailer[23:0],byte_value};
                    if(q_index==qmap_bytes-1)state<=Q_CHECK;
                    else begin q_index<=q_index+1;state<=Q_LOAD;end
                end
                Q_CHECK:begin
                    if((~q_crc)!=q_trailer)reject(9);
                    else if({qbuffer[0],qbuffer[1],qbuffer[2],qbuffer[3]}!=32'h514d3837||
                        qbuffer[4]!=1||{qbuffer[6],qbuffer[7]}!=1350||
                        32'({qbuffer[8],qbuffer[9]})+16!=qmap_bytes)reject(10);
                    else if(qbuffer[5]!=2&&qbuffer[5]!=6)reject(4);
                    else if(32'({qbuffer[10],qbuffer[11]})!=required_cells)reject(11);
                    else if(qbuffer[5]==6)begin
                        if(key_frame||!snapshot_valid||!snapshot_cache)reject(7);
                        else if(qmap_bytes!=16)reject(10);
                        else begin plane<=0;cursor<=residual_start;state<=PLANE_BEGIN;end
                    end else begin q_index<=12;q_runs<=0;q_run_byte<=qbuffer[12];state<=Q_RUN;end
                end
                Q_RUN:begin
                    if(q_index==qmap_bytes-4)begin
                        if(q_runs!=1350)reject(10);
                        else begin plane<=0;cursor<=residual_start;state<=PLANE_BEGIN;end
                    end else if(q_run_byte[7:6]>2||q_runs+32'(q_run_byte[5:0])+1>1350)reject(10);
                    else begin
                        q_remaining<={1'b0,q_run_byte[5:0]}+1;
                        q_value<=q_run_byte[7:6];q_index<=q_index+1;state<=Q_FILL;
                    end
                end
                Q_FILL:begin
                    q_runs<=q_runs+1;
                    q_remaining<=q_remaining-1;
                    if(q_remaining==1)begin
                        q_run_byte<=qbuffer[q_index[8:0]];state<=Q_RUN;
                    end
                end
                PLANE_BEGIN:begin
                    if(cursor+4>residual_end)reject(13);
                    else request_word(cursor,CHUNK_NUMBER);
                end
                CHUNK_NUMBER:begin
                    cursor<=cursor+4;
                    if(word_value!=(selected_zero?32'd0:32'd1))reject(12);
                    else if(word_value==0)state<=PLANE_NEXT;
                    else if(cursor+12>residual_end)reject(13);
                    else request_word(cursor+4,CHUNK_BLOCKS);
                end
                CHUNK_BLOCKS:begin
                    cursor<=cursor+4;
                    if(word_value!=selected_blocks||word_value==0)reject(13);
                    else request_word(cursor+4,CHUNK_LENGTH);
                end
                CHUNK_LENGTH:begin
                    cursor<=cursor+4;chunk_length<=word_value;
                    if(word_value<46||word_value>selected_limit||
                        {32'd0,cursor}+4+{32'd0,word_value}>{32'd0,residual_end})reject(13);
                    else begin
                        plane_offset[plane]<=cursor+4;plane_length[plane]<=word_value;
                        request_word(cursor+4,CHUNK_MAGIC);
                    end
                end
                CHUNK_MAGIC:begin
                    if(word_value==32'h41423338)plane_entropy[plane]<=1;
                    else if(word_value==32'h42523838)plane_entropy[plane]<=2;
                    else reject(14);
                    if(word_value==32'h41423338||word_value==32'h42523838)begin
                        cursor<=cursor+chunk_length;state<=PLANE_NEXT;
                    end
                end
                PLANE_NEXT:begin
                    if(plane==2)state<=COMPLETE;
                    else begin plane<=plane+1;state<=PLANE_BEGIN;end
                end
                COMPLETE:begin if(cursor!=residual_end)reject(13);else state<=RECEIPT;end
                RECEIPT:begin
                    if(receipt_ready)state<=FINISHED;
                    else count_receipt_wait<=count_receipt_wait+1;
                end
                FETCH_REQ:state<=FETCH_WAIT;
                FETCH_WAIT:begin byte_value<=ram_data;state<=fetch_return;end
                WORD_BYTE:begin
                    if(word_index==3)begin word_value<={word_acc,byte_value};state<=word_return;end
                    else begin
                        word_acc<={word_acc[15:0],byte_value};word_index<=word_index+1;word_cursor<=word_cursor+1;
                        request_byte(word_cursor+1,WORD_BYTE);
                    end
                end
                default:begin end
            endcase
        end
    end
    assign verify_coord_valid=coord_valid;
    assign verify_plane=plane;assign verify_tile=tile;assign verify_cell=coord_cell;
    assign verify_column=coord_y_column;assign verify_odd=coord_y_odd;
    assign verify_pair_base=coord_pair_base;
    assign verify_residual=coord_valid && ((state==KEY_TILE && tile<tile_count(plane) && !hidden(plane,tile)) ||
        (state==MODE_BIT && bits_left!=0 && mixed_bit && bit_cache[7]) ||
        (state==GROUP_TILE && tile!=group_end && !hidden(plane,tile) && group_tag==1));
    assign verify_active_index=active_index[10:0];
    assign verify_active_value=active_index<1350 ? active_cell[active_index[10:0]] : 1'b0;

    assign verify_q_index=q_index;assign verify_q_runs=q_runs;
    assign verify_q_remaining=q_remaining;assign verify_q_value=q_value;
    assign verify_q_selected=qbuffer[q_index[8:0]];
    assign verify_q_cached=q_run_byte;
    assign verify_header_index=header_index;
    assign verify_header_mode_start=header_mode_start;
    assign verify_header_residual_start=header_residual_start;
    assign verify_header_hud_tail=header_hud_tail;
    assign verify_header_residual_end=header_residual_end;
    assign verify_header_packet_total=header_packet_total;

endmodule

// Isolated common-clock TDP scale storage; no reset/initialization promise.
module cu66_scale_tdp_v107 (
    input wire clk,input wire a_write,input wire [10:0] a_addr,input wire [1:0] a_data,
    input wire b_write,b_read,input wire [10:0] b_addr,input wire [1:0] b_data,
    output reg [1:0] b_q
);
    (* ram_style="block" *) reg [1:0] words [0:1349];
    // Suppress only same-address simultaneous A writes: original Q_FILL wins.
    wire a_commit=a_write && !(b_write && a_addr==b_addr);
    always @(posedge clk)if(a_commit) words[a_addr]<=a_data;
    // A B-write must hold the previous lookup output (NO_CHANGE semantics).
    always @(posedge clk)begin
        if(b_write) words[b_addr]<=b_data;
        else if(b_read) b_q<=words[b_addr];
    end
endmodule
module cu66_mode_store_v107 (
    input wire clk,write_enable,input wire [12:0] write_address,input wire [1:0] write_data,
    input wire read_enable,input wire [12:0] read_address,output reg [1:0] q
);
    (* ram_style="block" *) reg [1:0] words [0:8099];
    // Parser writes and FINISHED reads are mutually exclusive in the caller.
    // Preserve the last registered lookup value across every parser write.
    always @(posedge clk)begin
        if(write_enable)words[write_address]<=write_data;
        else if(read_enable)q<=words[read_address];
    end
endmodule
