// AB38 coefficient payload decoder, dispatch 5 (full) / 6 (compact) only.
// One shared arithmetic engine, four persistent interval/probability contexts.
// Compressed storage is external. Output is provisional until done && !error.
module cu71_ab38_decoder_intervalregs_v019 #(
    parameter integer MAX_PACKET_BYTES = 49152,
    parameter integer MAX_BLOCKS = 8100
) (
    input  logic clk,
    input  logic rst,
    input  logic abort_i,
    input  logic cfg_valid,
    output logic cfg_ready,
    input  logic [2:0] cfg_dispatch,
    input  logic [15:0] cfg_packet_bytes,
    input  logic [16:0] cfg_blocks,
    input  logic [8:0] cfg_blocks_w,
    output logic rd_req_valid,
    input  logic rd_req_ready,
    output logic [15:0] rd_req_addr,
    input  logic rd_rsp_valid,
    output logic rd_rsp_ready,
    input  logic [7:0] rd_rsp_data,
    output logic tile_valid,
    input  logic tile_ready,
    output logic [1023:0] tile_coefficients,
    output logic [16:0] tile_index,
    output logic tile_last,
    output logic busy,
    output logic done,
    output logic aborted,
    output logic error,
    output logic [7:0] error_code,
    output logic [7:0] debug_state,
    output logic [31:0] decoded_decisions,
    output logic [31:0] renormalizations,
    output logic [31:0] memory_reads,
    output logic [31:0] output_stall_cycles
);
    typedef enum logic [7:0] {
        IDLE, READ_REQUEST, READ_RESPONSE, DRAIN,
        CRC_READ, CRC_BYTE, HEADER_CHECK, STREAM_BEGIN, PARAM_READ, PARAM_BYTE,
        PARAM_CHECK, PAD_READ, PAD_CHECK, PROB_INIT, PRELOAD_BEGIN, PRELOAD_BIT,
        EVENT_INIT, EVENT_START, EVENT_RUN, EVENT_LEVEL,
        BLOCK_BEGIN, DC_VALUE, DC_COMMIT, BAND_CHECK, BAND_ADVANCE,
        RAW_COEF_LOW, RAW_COEF_HIGH, RAW_COEF_STORE, OUTPUT_TILE,
        RAW_BIT, RAW_CACHE, RAW_DELIVER,
        ARITH_DECIDE, ARITH_RENORM, ARITH_SHIFT,
        RICE_QUOTIENT, RICE_QUOTIENT_BIT, RICE_SUFFIX, RICE_SUFFIX_BIT,
        FINISH_BEGIN, FINISH_FIRST, FINISH_SECOND, CFG_MODULO,
        ARITH_PRODUCT, ARITH_CLAMP, ARITH_BOUNDARY, ARITH_APPLY,
        BAND_LIMIT, BAND_TEST, BAND_POSITION, BAND_STORE,
        PARAM_BOUNDS, PARAM_SIZE, PARAM_VALIDATE, HEADER_SUM, HEADER_INSTALL, DC_CHECK, READ_CHECK
    } state_t;
    state_t state, memory_return, raw_return, arithmetic_return, rice_return, finish_return;
    // Accepted metadata is immutable throughout17 restoring-remainder steps.
    logic [16:0] cfg_mod_dividend;
    logic [7:0] cfg_mod_remainder;
    logic [4:0] cfg_mod_bit;
    wire [8:0] cfg_mod_shift={cfg_mod_remainder,cfg_mod_dividend[16]};
    wire [8:0] cfg_mod_next=cfg_mod_shift>=blocks_w ? cfg_mod_shift-blocks_w : cfg_mod_shift;
    logic [15:0] packet_bytes;
    logic [16:0] nblocks, block_number;
    logic [8:0] blocks_w, dc_column;
    logic [7:0] header [0:41];
    logic [31:0] scan_address, crc, received_crc;
    logic [7:0] memory_byte;
    logic [31:0] lengths [0:3];
    // Private signed32-bit payload; DC_VALUE always writes before DC_CHECK.
    logic signed [31:0] dc_prediction;
    // Private payload registers: all assigned before HEADER_INSTALL, no reset.
    logic [31:0] header_pair01,header_pair23,header_total;
    logic [31:0] header_prefix1,header_prefix2,header_prefix3;
    logic [31:0] event_counts [0:2];
    // HEADER_CHECK establishes these private bounds before PARAM_CHECK.
    // Full17-bit block count times6-bit width fits23bits; no reset required.
    logic [22:0] event_limits [0:2];
    logic [31:0] stream_chunk [0:3], stream_base [0:3];
    logic [31:0] stream_bits [0:3], stream_position [0:3];
    logic [7:0] stream_k0 [0:3], stream_k1 [0:3];
    // Four-entry interval state stays in FFs, not async distributed RAM.
    logic [3:0][15:0] low, high, code;
    logic [7:0] probabilities [0:351];
    logic [7:0] byte_cache [0:3];
    // Relative byte index: stream_base is immutable while its cache is valid.
    logic [31:0] byte_cache_offset [0:3];
    // Private payload written before READ_CHECK, never needs bulk reset.
    logic [31:0] pending_read_address;
    logic [3:0] byte_cache_valid, stream_finished;
    logic [1:0] stream;
    logic [2:0] parameter_byte;
    logic [1:0] param_stream;
    logic [31:0] param_bits,param_length,param_chunk,param_count,param_capacity,param_rounded,param_encoded;
    logic [22:0] param_limit;
    logic [7:0] param_k0,param_k1;
    logic [5:0] preload_count;
    logic [8:0] probability_index;
    logic raw_bit_value, arithmetic_bit;
    logic [6:0] arithmetic_context;
    logic [15:0] renorm_offset;
    logic [4:0] rice_k, rice_escape, rice_quotient, suffix_left;
    logic rice_level, rice_is_escape;
    logic [31:0] suffix_value, rice_value;
    logic [31:0] pending_left [0:2];
    logic signed [31:0] pending_index [0:2];
    logic signed [15:0] pending_value [0:2];
    logic [1:0] band;
    logic [1:0] band_snapshot;
    logic [5:0] band_width_snapshot,band_coefficient;
    logic [22:0] band_base,band_limit;
    logic [5:0] raw_coefficient;
    logic [7:0] raw_low_byte;
    logic signed [15:0] tile [0:63];
    logic signed [31:0] previous_dc;
    logic raw_mode;
    integer i;

    function automatic [31:0] h32(input integer offset);
        h32 = {header[offset+3],header[offset+2],header[offset+1],header[offset]};
    endfunction
    function automatic [31:0] crc_byte(input [31:0] initial_crc, input [7:0] value);
        reg [31:0] value_crc;
        integer j;
        begin
            value_crc = initial_crc ^ {24'd0,value};
            for (j=0;j<8;j=j+1)
                value_crc = value_crc[0] ? ((value_crc >> 1)^32'hedb88320) : (value_crc >> 1);
            crc_byte = value_crc;
        end
    endfunction
    function automatic signed [31:0] unzigzag(input [31:0] value);
        unzigzag = value[0] ? -$signed(value >> 1)-32'sd1 : $signed(value >> 1);
    endfunction
    function automatic [5:0] band_width(input [1:0] which_band);
        case(which_band) 0:band_width=6'd5; 1:band_width=6'd15; default:band_width=6'd43; endcase
    endfunction
    function automatic [5:0] band_low(input [1:0] which_band);
        case(which_band) 0:band_low=6'd1; 1:band_low=6'd6; default:band_low=6'd21; endcase
    endfunction
    function automatic [5:0] zig_address(input [5:0] value);
        case(value)
            6'd0:zig_address=6'd0;
            6'd1:zig_address=6'd1;
            6'd2:zig_address=6'd8;
            6'd3:zig_address=6'd16;
            6'd4:zig_address=6'd9;
            6'd5:zig_address=6'd2;
            6'd6:zig_address=6'd3;
            6'd7:zig_address=6'd10;
            6'd8:zig_address=6'd17;
            6'd9:zig_address=6'd24;
            6'd10:zig_address=6'd32;
            6'd11:zig_address=6'd25;
            6'd12:zig_address=6'd18;
            6'd13:zig_address=6'd11;
            6'd14:zig_address=6'd4;
            6'd15:zig_address=6'd5;
            6'd16:zig_address=6'd12;
            6'd17:zig_address=6'd19;
            6'd18:zig_address=6'd26;
            6'd19:zig_address=6'd33;
            6'd20:zig_address=6'd40;
            6'd21:zig_address=6'd48;
            6'd22:zig_address=6'd41;
            6'd23:zig_address=6'd34;
            6'd24:zig_address=6'd27;
            6'd25:zig_address=6'd20;
            6'd26:zig_address=6'd13;
            6'd27:zig_address=6'd6;
            6'd28:zig_address=6'd7;
            6'd29:zig_address=6'd14;
            6'd30:zig_address=6'd21;
            6'd31:zig_address=6'd28;
            6'd32:zig_address=6'd35;
            6'd33:zig_address=6'd42;
            6'd34:zig_address=6'd49;
            6'd35:zig_address=6'd56;
            6'd36:zig_address=6'd57;
            6'd37:zig_address=6'd50;
            6'd38:zig_address=6'd43;
            6'd39:zig_address=6'd36;
            6'd40:zig_address=6'd29;
            6'd41:zig_address=6'd22;
            6'd42:zig_address=6'd15;
            6'd43:zig_address=6'd23;
            6'd44:zig_address=6'd30;
            6'd45:zig_address=6'd37;
            6'd46:zig_address=6'd44;
            6'd47:zig_address=6'd51;
            6'd48:zig_address=6'd58;
            6'd49:zig_address=6'd59;
            6'd50:zig_address=6'd52;
            6'd51:zig_address=6'd45;
            6'd52:zig_address=6'd38;
            6'd53:zig_address=6'd31;
            6'd54:zig_address=6'd39;
            6'd55:zig_address=6'd46;
            6'd56:zig_address=6'd53;
            6'd57:zig_address=6'd60;
            6'd58:zig_address=6'd61;
            6'd59:zig_address=6'd54;
            6'd60:zig_address=6'd47;
            6'd61:zig_address=6'd55;
            6'd62:zig_address=6'd62;
            6'd63:zig_address=6'd63;
            default:zig_address=0;
        endcase
    endfunction

    task automatic fail(input [7:0] why);
        begin
            state <= IDLE; busy <= 1'b0; error <= 1'b1; error_code <= why;
            rd_req_valid <= 1'b0;
        end
    endtask
    task automatic read_byte(input [31:0] address, input state_t return_state);
        begin
            pending_read_address <= address;
            memory_return <= return_state; state <= READ_CHECK;
        end
    endtask
    task automatic get_raw(input state_t return_state);
        begin raw_return <= return_state; state <= RAW_BIT; end
    endtask
    task automatic get_arithmetic(input [6:0] context_id, input state_t return_state);
        begin arithmetic_context <= context_id; arithmetic_return <= return_state; state <= ARITH_DECIDE; end
    endtask
    task automatic get_rice(input [4:0] k, input [4:0] escape_width, input logic level, input state_t return_state);
        begin
            rice_k<=k;rice_escape<=escape_width;rice_level<=level;
            rice_quotient<=0;suffix_value<=0;rice_return<=return_state;state<=RICE_QUOTIENT;
        end
    endtask
    task automatic finish_stream(input state_t return_state);
        begin finish_return<=return_state;state<=FINISH_BEGIN;end
    endtask

    // Snapshot one valid decision. No interval/context can mutate until APPLY.
    logic [1:0] arith_stream;
    logic [8:0] arith_address;
    logic [7:0] arith_probability;
    logic [16:0] arith_span,arith_product;
    logic [15:0] arith_low,arith_code,arith_partition,arith_boundary;
    logic [8:0] arith_delta,arith_probability_next;
    wire [8:0] probability_address=({7'd0,stream}*9'd88)+{2'd0,arithmetic_context};
    wire [16:0] interval_span={1'b0,high[stream]}-{1'b0,low[stream]}+17'd1;
    always_comb begin
        if(arith_code>arith_boundary)begin
            arith_delta={1'b0,arith_probability}>>5;
            if(arith_delta==0)arith_delta=1;
            arith_probability_next=({1'b0,arith_probability}>arith_delta)?({1'b0,arith_probability}-arith_delta):9'd1;
        end else begin
            arith_delta=(9'd256-{1'b0,arith_probability})>>5;
            if(arith_delta==0)arith_delta=1;
            arith_probability_next={1'b0,arith_probability}+arith_delta;
            if(arith_probability_next>255)arith_probability_next=255;
        end
    end
    always_comb begin
        debug_state=state;
        cfg_ready=(state==IDLE)&&!abort_i&&!rst;
        rd_rsp_ready=(state==READ_RESPONSE)||(state==DRAIN);
        tile_valid=(state==OUTPUT_TILE)&&busy&&!abort_i&&!rst;
        tile_index=block_number;
        tile_last=(block_number+17'd1==nblocks);
        for(integer t=0;t<64;t=t+1)tile_coefficients[t*16+:16]=tile[t];
    end

    always_ff @(posedge clk) begin
        if(rst) begin
            state<=IDLE;busy<=0;done<=0;aborted<=0;error<=0;error_code<=0;rd_req_valid<=0;decoded_decisions<=0;renormalizations<=0;memory_reads<=0;output_stall_cycles<=0;rd_req_addr<=0;
            decoded_decisions<=0;renormalizations<=0;memory_reads<=0;output_stall_cycles<=0;
            packet_bytes<=0;nblocks<=0;blocks_w<=0;block_number<=0;dc_column<=0;
            cfg_mod_dividend<=0;cfg_mod_remainder<=0;cfg_mod_bit<=0;
            arith_stream<=0;arith_address<=0;arith_probability<=0;arith_span<=0;arith_product<=0;
            arith_low<=0;arith_code<=0;arith_partition<=0;arith_boundary<=0;
            scan_address<=0;crc<=32'hffffffff;received_crc<=0;memory_byte<=0;
            stream<=0;parameter_byte<=0;preload_count<=0;probability_index<=0;
            raw_bit_value<=0;arithmetic_bit<=0;arithmetic_context<=0;renorm_offset<=0;
            rice_k<=0;rice_escape<=0;rice_quotient<=0;suffix_left<=0;rice_level<=0;rice_is_escape<=0;suffix_value<=0;rice_value<=0;
            band_snapshot<=0;band_width_snapshot<=0;band_coefficient<=0;band_base<=0;band_limit<=0;
            band<=0;raw_coefficient<=0;raw_low_byte<=0;previous_dc<=0;raw_mode<=0;
            byte_cache_valid<=0;stream_finished<=0;initial_events<=1;
            memory_return<=IDLE;raw_return<=IDLE;arithmetic_return<=IDLE;rice_return<=IDLE;finish_return<=IDLE;
            for(i=0;i<64;i=i+1)tile[i]<=0;
        end else begin
            done<=0;aborted<=0;
            if(rd_req_valid && rd_req_ready)memory_reads<=memory_reads+1;
            if(tile_valid && !tile_ready)output_stall_cycles<=output_stall_cycles+1;
            if(abort_i) begin
                aborted<=1;busy<=0;rd_req_valid<=0;
                if(state==READ_RESPONSE || state==DRAIN)begin
                    if(rd_rsp_valid)state<=IDLE;else state<=DRAIN;
                end else if(state==READ_REQUEST && rd_req_valid && rd_req_ready)state<=DRAIN;
                else state<=IDLE;
            end else case(state)
                IDLE: if(cfg_valid) begin
                    error<=0;error_code<=0;rd_req_valid<=0;decoded_decisions<=0;renormalizations<=0;memory_reads<=0;output_stall_cycles<=0;
                    if((cfg_dispatch!=3'd5 && cfg_dispatch!=3'd6)||cfg_packet_bytes<46||{16'd0,cfg_packet_bytes}>32'(MAX_PACKET_BYTES)||
                       cfg_blocks==0||{15'd0,cfg_blocks}>32'(MAX_BLOCKS)||cfg_blocks_w==0||cfg_blocks_w>256||
                       (cfg_dispatch==3'd6 && cfg_blocks_w!=1))fail(8'h01);
                    else begin
                        packet_bytes<=cfg_packet_bytes;nblocks<=cfg_blocks;blocks_w<=cfg_blocks_w;
                        busy<=1;scan_address<=0;crc<=32'hffffffff;received_crc<=0;
                        block_number<=0;dc_column<=0;previous_dc<=0;byte_cache_valid<=0;stream_finished<=0;initial_events<=1;
                        cfg_mod_dividend<=cfg_blocks;cfg_mod_remainder<=0;cfg_mod_bit<=16;state<=CFG_MODULO;
                    end
                end
                CFG_MODULO:begin
                    cfg_mod_remainder<=cfg_mod_next[7:0];cfg_mod_dividend<=cfg_mod_dividend<<1;
                    if(cfg_mod_bit==0)begin
                        if(cfg_mod_next!=0)fail(8'h01);else state<=CRC_READ;
                    end else cfg_mod_bit<=cfg_mod_bit-1'b1;
                end
                READ_CHECK:begin
                    if(pending_read_address >= {16'd0,packet_bytes})fail(8'h06);
                    else begin rd_req_addr<=pending_read_address[15:0];rd_req_valid<=1'b1;state<=READ_REQUEST;end
                end
                READ_REQUEST:if(rd_req_ready)begin rd_req_valid<=0;state<=READ_RESPONSE;end
                READ_RESPONSE:if(rd_rsp_valid)begin memory_byte<=rd_rsp_data;state<=memory_return;end
                DRAIN:if(rd_rsp_valid)state<=IDLE;
                CRC_READ:read_byte(scan_address,CRC_BYTE);
                CRC_BYTE:begin
                    if(scan_address<42)header[scan_address]<=memory_byte;
                    if(scan_address<{16'd0,packet_bytes}-4)crc<=crc_byte(crc,memory_byte);
                    else received_crc<=received_crc|({24'd0,memory_byte}<<((scan_address-({16'd0,packet_bytes}-4))*8));
                    if(scan_address+1=={16'd0,packet_bytes})state<=HEADER_CHECK;
                    else begin scan_address<=scan_address+1;state<=CRC_READ;end
                end
                HEADER_CHECK:begin
                    if((crc^32'hffffffff)!=received_crc)fail(8'h02);
                    else if(header[0]!=8'h41||header[1]!=8'h42||header[2]!=8'h33||header[3]!=8'h38||header[4]!=1||header[5]>1||
                            h32(6)!={15'd0,nblocks}||{header[11],header[10]}!={7'd0,blocks_w}||{header[13],header[12]}!=0)fail(8'h03);
                    else begin
                        header_pair01<=h32(14)+h32(18);
                        header_pair23<=h32(22)+h32(26);
                        event_limits[0]<=23'(23'(nblocks)*23'd5);
                        event_limits[1]<=23'(23'(nblocks)*23'd15);
                        event_limits[2]<=23'(23'(nblocks)*23'd43);
                        for(i=0;i<4;i=i+1)lengths[i]<=h32(14+4*i);
                        for(i=0;i<3;i=i+1)event_counts[i]<=h32(30+4*i);
                        state<=HEADER_SUM;
                    end
                end
                HEADER_SUM:begin
                    // All assignments retain the original unsigned32-bit wrap.
                    header_total<=32'd46+header_pair01+header_pair23;
                    header_prefix1<=32'd42+lengths[0];
                    header_prefix2<=32'd42+header_pair01;
                    header_prefix3<=32'd42+header_pair01+lengths[2];
                    state<=HEADER_INSTALL;
                end
                HEADER_INSTALL:begin
                    if(header_total!={16'd0,packet_bytes})fail(8'h04);
                    else begin
                        stream_chunk[0]<=42;stream_chunk[1]<=header_prefix1;
                        stream_chunk[2]<=header_prefix2;stream_chunk[3]<=header_prefix3;
                        raw_mode<=header[5][0];stream<=0;state<=STREAM_BEGIN;
                    end
                end
                STREAM_BEGIN:begin
                    if(raw_mode) begin
                        if(lengths[0]!=128*{15'd0,nblocks}||lengths[1]!=0||lengths[2]!=0||lengths[3]!=0||event_counts[0]!=0||event_counts[1]!=0||event_counts[2]!=0)fail(8'h05);
                        else begin raw_coefficient<=0;state<=BLOCK_BEGIN;end
                    end else if(lengths[stream]<9)fail(8'h07);
                    else begin parameter_byte<=0;state<=PARAM_READ;end
                end
                PARAM_READ:read_byte(stream_chunk[stream]+{29'd0,parameter_byte},PARAM_BYTE);
                PARAM_BYTE:begin
                    case(parameter_byte)
                        0:stream_k0[stream]<=memory_byte;
                        1:stream_k1[stream]<=memory_byte;
                        2:stream_bits[stream]<={24'd0,memory_byte};
                        3:stream_bits[stream]<=stream_bits[stream]|({24'd0,memory_byte}<<8);
                        4:stream_bits[stream]<=stream_bits[stream]|({24'd0,memory_byte}<<16);
                        5:stream_bits[stream]<=stream_bits[stream]|({24'd0,memory_byte}<<24);
                        default:begin end
                    endcase
                    if(parameter_byte==5)state<=PARAM_CHECK;
                    else begin parameter_byte<=parameter_byte+1;state<=PARAM_READ;end
                end
                PARAM_CHECK:begin
                    param_stream<=stream;param_bits<=stream_bits[stream];param_length<=lengths[stream];
                    param_chunk<=stream_chunk[stream];param_k0<=stream_k0[stream];param_k1<=stream_k1[stream];
                    param_count<=event_counts[2'(stream-2'd1)];param_limit<=event_limits[2'(stream-2'd1)];
                    state<=PARAM_BOUNDS;
                end
                PARAM_BOUNDS:begin
                    // Preserve original32-bit wrap before shifting/dividing.
                    param_capacity<=32'd8*(param_length-32'd6);
                    param_rounded<=param_bits+32'd7;state<=PARAM_SIZE;
                end
                PARAM_SIZE:begin
                    param_encoded<=32'd6+(param_rounded>>3);state<=PARAM_VALIDATE;
                end
                PARAM_VALIDATE:begin
                    if(param_bits<18 || param_bits>param_capacity || param_encoded!=param_length)fail(8'h08);
                    else if(param_stream==0 && (param_k0>13||param_k1!=255))fail(8'h09);
                    else if(param_stream!=0 && (param_k0>19||param_k1>11||param_count>{9'd0,param_limit}))fail(8'h0a);
                    else begin stream_base[param_stream]<=param_chunk+6;state<=PAD_READ;end
                end
                PAD_READ:read_byte(stream_chunk[stream]+lengths[stream]-1,PAD_CHECK);
                PAD_CHECK:begin
                    if(stream_bits[stream][2:0]!=0 && (memory_byte & (8'hff>>(stream_bits[stream][2:0])))!=0)fail(8'h0b);
                    else if(stream==3)begin probability_index<=0;state<=PROB_INIT;end
                    else begin stream<=stream+1;state<=STREAM_BEGIN;end
                end
                PROB_INIT:begin
                    probabilities[probability_index]<=128;
                    if(probability_index==351)begin stream<=0;state<=PRELOAD_BEGIN;end
                    else probability_index<=probability_index+1;
                end
                PRELOAD_BEGIN:begin
                    low[stream]<=0;high[stream]<=65535;code[stream]<=0;stream_position[stream]<=0;preload_count<=0;get_raw(PRELOAD_BIT);
                end
                PRELOAD_BIT:begin
                    code[stream]<={code[stream][14:0],raw_bit_value};
                    if(preload_count==15)begin
                        if(stream==3)begin band<=0;state<=EVENT_INIT;end
                        else begin stream<=stream+1;state<=PRELOAD_BEGIN;end
                    end else begin preload_count<=preload_count+1;get_raw(PRELOAD_BIT);end
                end
                EVENT_INIT:begin
                    pending_left[band]<=event_counts[band];pending_index[band]<=-1;pending_value[band]<=0;
                    stream<=band+1;state<=EVENT_START;
                end
                EVENT_START:begin
                    if(pending_left[band]==0) begin
                        pending_index[band]<=$signed({9'd0,event_limits[band]});pending_value[band]<=0;
                        finish_stream(BAND_ADVANCE);
                    end else get_rice(stream_k0[stream][4:0],24,0,EVENT_RUN);
                end
                EVENT_RUN:begin
                    if($signed(pending_index[band])+1+$signed(rice_value)>=$signed({9'd0,event_limits[band]}))fail(8'h10);
                    else begin pending_index[band]<=pending_index[band]+1+$signed(rice_value);get_rice(stream_k1[stream][4:0],12,1,EVENT_LEVEL);end
                end
                EVENT_LEVEL:begin
                    if(unzigzag(rice_value+1)==0||unzigzag(rice_value+1)<-2048||unzigzag(rice_value+1)>2048)fail(8'h11);
                    else begin
                        pending_value[band]<=16'(unzigzag(rice_value+1));pending_left[band]<=pending_left[band]-1;
                        state<=BAND_ADVANCE;
                    end
                end
                BAND_ADVANCE:begin
                    // During initial prefetch, block_number is zero and no DC has been decoded.
                    if(initial_events) begin
                        if(band==2)begin initial_events<=0;state<=BLOCK_BEGIN;end
                        else begin band<=band+1;state<=EVENT_INIT;end
                    end else state<=BAND_CHECK;
                end
                BLOCK_BEGIN:begin
                    for(i=0;i<64;i=i+1)tile[i]<=0;
                    band<=0;
                    if(raw_mode)begin raw_coefficient<=0;state<=RAW_COEF_LOW;end
                    else begin stream<=0;get_rice(stream_k0[0][4:0],14,0,DC_VALUE);end
                end
                DC_VALUE:begin
                    dc_prediction<=(dc_column==0?32'sd0:previous_dc)+unzigzag(rice_value);
                    state<=DC_CHECK;
                end
                DC_CHECK:begin
                    if(dc_prediction<-2048 || dc_prediction>2048)fail(8'h12);
                    else begin previous_dc<=dc_prediction;tile[0]<=16'(dc_prediction);state<=DC_COMMIT;end
                end
                DC_COMMIT:begin
                    if(block_number+1==nblocks)finish_stream(BAND_CHECK);
                    else state<=BAND_CHECK;
                end
                BAND_CHECK:begin
                    band_snapshot<=band;band_width_snapshot<=band_width(band);
                    // Full17x6product fits23bits; avoids(block+1)->DSP->compare.
                    band_base<=23'(23'(block_number)*23'(band_width(band)));
                    state<=BAND_LIMIT;
                end
                BAND_LIMIT:begin
                    band_limit<=band_base+{17'd0,band_width_snapshot};state<=BAND_TEST;
                end
                BAND_TEST:begin
                    if(pending_index[band_snapshot]<$signed({9'd0,band_limit}))begin
                        if(pending_index[band_snapshot]<$signed({9'd0,band_base}))fail(8'h13);
                        else state<=BAND_POSITION;
                    end else if(band_snapshot==2)begin
                        if(block_number+1==nblocks && (pending_left[0]!=0||pending_left[1]!=0||pending_left[2]!=0||stream_finished!=4'b1111))fail(8'h14);
                        else state<=OUTPUT_TILE;
                    end else begin band<=band_snapshot+1'b1;state<=BAND_CHECK;end
                end
                BAND_POSITION:begin
                    // Proven by BAND_TEST:0<=index-base<width<=43. Low6bit
                    // subtraction therefore preserves the exact coefficient.
                    band_coefficient<=band_low(band_snapshot)+(pending_index[band_snapshot][5:0]-band_base[5:0]);
                    state<=BAND_STORE;
                end
                BAND_STORE:begin
                    tile[zig_address(band_coefficient)]<=pending_value[band_snapshot];
                    stream<=band_snapshot+1;state<=EVENT_START;
                end
                RAW_COEF_LOW:read_byte(42+block_number*128+{26'd0,raw_coefficient}*2,RAW_COEF_HIGH);
                RAW_COEF_HIGH:begin raw_low_byte<=memory_byte;read_byte(43+block_number*128+{26'd0,raw_coefficient}*2,RAW_COEF_STORE);end
                RAW_COEF_STORE:begin
                    if($signed({memory_byte,raw_low_byte})<-2048||$signed({memory_byte,raw_low_byte})>2048)fail(8'h15);
                    else begin
                        tile[raw_coefficient]<=$signed({memory_byte,raw_low_byte});
                        if(raw_coefficient==63)state<=OUTPUT_TILE;
                        else begin raw_coefficient<=raw_coefficient+1;state<=RAW_COEF_LOW;end
                    end
                end
                OUTPUT_TILE:if(tile_ready)begin
                    if(block_number+1==nblocks)begin done<=1;busy<=0;state<=IDLE;end
                    else begin
                        block_number<=block_number+1;
                        if(dc_column+1==blocks_w)dc_column<=0;else dc_column<=dc_column+1;
                        state<=BLOCK_BEGIN;
                    end
                end
                RAW_BIT:begin
                    if(stream_position[stream]>=stream_bits[stream])fail(8'h20);
                    else if(byte_cache_valid[stream] && byte_cache_offset[stream]==(stream_position[stream]>>3))state<=RAW_DELIVER;
                    else read_byte(stream_base[stream]+(stream_position[stream]>>3),RAW_CACHE);
                end
                RAW_CACHE:begin
                    byte_cache[stream]<=memory_byte;byte_cache_offset[stream]<=(stream_position[stream]>>3);byte_cache_valid[stream]<=1;state<=RAW_DELIVER;
                end
                RAW_DELIVER:begin raw_bit_value<=byte_cache[stream][7-stream_position[stream][2:0]];stream_position[stream]<=stream_position[stream]+1;state<=raw_return;end
                ARITH_DECIDE:begin
                    if(arithmetic_context>=88||low[stream]>=high[stream]||code[stream]<low[stream]||code[stream]>high[stream])fail(8'h21);
                    else begin
                        arith_stream<=stream;arith_address<=probability_address;
                        arith_probability<=probabilities[probability_address];
                        arith_span<=interval_span;arith_low<=low[stream];arith_code<=code[stream];
                        state<=ARITH_PRODUCT;
                    end
                end
                ARITH_PRODUCT:begin
                    // Exact original25-bit product, floor divide by256.
                    arith_product<=17'((25'(arith_span)*25'(arith_probability))>>8);
                    state<=ARITH_CLAMP;
                end
                ARITH_CLAMP:begin
                    // Valid captured interval has2<=span<=65536. The clamped
                    // partition is therefore1..65535 and fits16bits exactly.
                    if(arith_product==0)arith_partition<=16'd1;
                    else if(arith_product>=arith_span)arith_partition<=arith_span[15:0]-16'd1;
                    else arith_partition<=arith_product[15:0];
                    state<=ARITH_BOUNDARY;
                end
                ARITH_BOUNDARY:begin
                    arith_boundary<=arith_low+arith_partition-16'd1;
                    state<=ARITH_APPLY;
                end
                ARITH_APPLY:begin
                    decoded_decisions<=decoded_decisions+1;
                    arithmetic_bit<=(arith_code>arith_boundary);
                    probabilities[arith_address]<=arith_probability_next[7:0];
                    if(arith_code>arith_boundary)low[arith_stream]<=arith_boundary+16'd1;
                    else high[arith_stream]<=arith_boundary;
                    state<=ARITH_RENORM;
                end
                ARITH_RENORM:begin
                    if(high[stream]<32768)begin renorm_offset<=0;get_raw(ARITH_SHIFT);end
                    else if(low[stream]>=32768)begin renorm_offset<=32768;get_raw(ARITH_SHIFT);end
                    else if(low[stream]>=16384 && high[stream]<49152)begin renorm_offset<=16384;get_raw(ARITH_SHIFT);end
                    else if(code[stream]<low[stream]||code[stream]>high[stream])fail(8'h22);
                    else state<=arithmetic_return;
                end
                ARITH_SHIFT:begin
                    renormalizations<=renormalizations+1;
                    low[stream]<=(low[stream]-renorm_offset)<<1;high[stream]<=((high[stream]-renorm_offset)<<1)|16'd1;
                    code[stream]<=((code[stream]-renorm_offset)<<1)|{15'd0,raw_bit_value};state<=ARITH_RENORM;
                end
                RICE_QUOTIENT:get_arithmetic((rice_level?7'd48:7'd0)+{2'd0,rice_quotient},RICE_QUOTIENT_BIT);
                RICE_QUOTIENT_BIT:begin
                    if(arithmetic_bit || rice_quotient==14)begin
                        rice_is_escape<=!arithmetic_bit; suffix_left<=arithmetic_bit?rice_k:rice_escape;suffix_value<=0;
                        if(arithmetic_bit && rice_k==0)begin rice_value<={27'd0,rice_quotient};state<=rice_return;end
                        else state<=RICE_SUFFIX;
                    end else begin rice_quotient<=rice_quotient+1;state<=RICE_QUOTIENT;end
                end
                RICE_SUFFIX:get_arithmetic((rice_level?7'd48:7'd0)+7'd16+{2'd0,(suffix_left-5'd1)},RICE_SUFFIX_BIT);
                RICE_SUFFIX_BIT:begin
                    suffix_value<=(suffix_value<<1)|{31'd0,arithmetic_bit};
                    if(suffix_left==1)begin
                        rice_value<=rice_is_escape?((suffix_value<<1)|{31'd0,arithmetic_bit}):(({27'd0,rice_quotient}<<rice_k)|((suffix_value<<1)|{31'd0,arithmetic_bit}));state<=rice_return;
                    end else begin suffix_left<=suffix_left-1;state<=RICE_SUFFIX;end
                end
                FINISH_BEGIN:begin
                    if(stream_bits[stream]-stream_position[stream]!=2)fail(8'h23);else get_raw(FINISH_FIRST);
                end
                FINISH_FIRST:if(raw_bit_value)fail(8'h24);else get_raw(FINISH_SECOND);
                FINISH_SECOND:if(raw_bit_value)fail(8'h24);else begin stream_finished[stream]<=1;state<=finish_return;end
                default:fail(8'hff);
            endcase
        end
    end
    logic initial_events;
endmodule
