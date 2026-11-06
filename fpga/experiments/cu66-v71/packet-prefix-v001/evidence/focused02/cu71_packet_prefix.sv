// CU66/GU66 structural packet controller. This module does NOT decode pixels,
// verify canonical SHA or decode HUD symbols. Metadata is provisional until the
// external frame owner completes ALL downstream checks and asserts commit.
// Accepted reference/history are cfg snapshots owned exclusively by that owner.
module cu71_packet_prefix (
    input logic clk, rst, abort_i,
    input logic cfg_valid,
    output logic cfg_ready,
    input logic [15:0] cfg_packet_bytes,
    input logic cfg_last_valid,
    input logic [31:0] cfg_last_frame_id,
    input logic cfg_reference_valid,
    input logic [31:0] cfg_reference_id,
    input logic [127:0] cfg_reference_tag,
    output logic rd_req_valid,
    input logic rd_req_ready,
    output logic [15:0] rd_req_addr,
    input logic rd_rsp_valid,
    output logic rd_rsp_ready,
    input logic [7:0] rd_rsp_data,
    output logic metadata_valid,
    input logic metadata_ready,
    output logic metadata_key,
    output logic [31:0] metadata_frame_id, metadata_reference_id,
    output logic [127:0] metadata_reference_tag, metadata_output_tag,
    output logic [7:0] metadata_block_size,
    output logic [15:0] metadata_plane_addr [0:2],
    output logic [15:0] metadata_plane_bytes [0:2],
    output logic [2:0] metadata_plane_dispatch [0:2],
    output logic [16:0] metadata_plane_blocks [0:2],
    output logic [8:0] metadata_plane_blocks_w [0:2],
    output logic [15:0] metadata_hud_addr, metadata_hud_bytes,
    output logic [127:0] metadata_hud_reference_tag, metadata_hud_output_tag,
    input logic qmap_req_valid,
    output logic qmap_req_ready,
    input logic [10:0] qmap_req_index,
    output logic qmap_rsp_valid,
    output logic [10:0] qmap_rsp_index,
    output logic [1:0] qmap_rsp_code,
    input logic commit_valid,
    output logic commit_ready,
    output logic busy, done, aborted, error,
    output logic [7:0] error_code,
    output logic [7:0] debug_state,
    output logic [31:0] memory_reads
);
    `include "cu66_profile.svh"
    typedef enum logic [7:0] {
        IDLE, READ_REQUEST, READ_RESPONSE, CHECK_OUTER, CHECK_INNER,
        CHECK_HUD, CHECK_CRCS, OFFER_METADATA, WAIT_COMMIT, DRAIN, PREFIX_STARTS, PREFIX_ADDRESSES
    } state_t;
    state_t state;
    logic [15:0] packet_bytes, scan_addr;
    logic last_valid, reference_valid, outer_validated, inner_validated;
    logic [31:0] last_frame_id, reference_id;
    logic [127:0] reference_tag;
    logic [7:0] outer_header [0:75], inner_header [0:59], hud_header [0:105];
    logic [7:0] qmap_mem [0:337];
    logic [31:0] crc_outer, crc_inner, crc_hud;
    logic [31:0] received_outer, received_inner, received_hud;
    logic [15:0] inner_bytes, plane_start [0:2];
    logic [15:0] vector_start, vector_end;
    logic [15:0] prefix0, prefix_yu, prefix_y;
    logic byte_bad, hud_bad;
    logic [7:0] byte_error;
    integer i;

    function automatic [31:0] outer32(input integer offset);
        outer32={outer_header[offset+3],outer_header[offset+2],outer_header[offset+1],outer_header[offset]};
    endfunction
    function automatic [15:0] outer16(input integer offset);
        outer16={outer_header[offset+1],outer_header[offset]};
    endfunction
    function automatic [127:0] outer128(input integer offset);
        integer j;
        for(j=0;j<16;j=j+1) outer128[127-8*j -:8]=outer_header[offset+j];
    endfunction
    function automatic [31:0] inner32(input integer offset);
        inner32={inner_header[offset+3],inner_header[offset+2],inner_header[offset+1],inner_header[offset]};
    endfunction
    function automatic [15:0] inner16(input integer offset);
        inner16={inner_header[offset+1],inner_header[offset]};
    endfunction
    function automatic [127:0] inner128(input integer offset);
        integer j;
        for(j=0;j<16;j=j+1) inner128[127-8*j -:8]=inner_header[offset+j];
    endfunction
    function automatic [31:0] hud32(input integer offset);
        hud32={hud_header[offset+3],hud_header[offset+2],hud_header[offset+1],hud_header[offset]};
    endfunction
    function automatic [15:0] hud16(input integer offset);
        hud16={hud_header[offset+1],hud_header[offset]};
    endfunction
    function automatic [127:0] hud128(input integer offset);
        integer j;
        for(j=0;j<16;j=j+1) hud128[127-8*j -:8]=hud_header[offset+j];
    endfunction
    function automatic [31:0] crc_byte(input [31:0] value_crc, input [7:0] value);
        reg [31:0] c;
        integer j;
        begin
            c=value_crc^{24'd0,value};
            for(j=0;j<8;j=j+1) c=c[0]?((c>>1)^32'hedb88320):(c>>1);
            crc_byte=c;
        end
    endfunction
    task automatic reject_packet(input [7:0] code);
        begin state<=IDLE;error<=1'b1;error_code<=code;done<=1'b1;end
    endtask

    always_comb begin
        cfg_ready=(state==IDLE)&&!abort_i;
        rd_req_valid=(state==READ_REQUEST)&&!abort_i;
        rd_req_addr=scan_addr;
        rd_rsp_ready=(state==READ_RESPONSE)||(state==DRAIN);
        metadata_valid=(state==OFFER_METADATA)&&!abort_i;
        commit_ready=(state==WAIT_COMMIT)&&!abort_i;
        qmap_req_ready=(state==WAIT_COMMIT)&&
                       !abort_i&&!commit_valid&&(qmap_req_index<11'd1350);
        busy=(state!=IDLE);
        debug_state=state;
        hud_bad=1'b0;
        for(integer j=0;j<16;j=j+1) if(hud16(74+2*j)!=expected_rect(j)) hud_bad=1'b1;
        for(integer j=0;j<4;j=j+1) begin
            if((hud32(54+4*j)<1)||(hud32(54+4*j)>32'(packet_bytes))||
               (hud_header[70+j]<1)||(hud_header[70+j]>((hud_header[2]==8'h32)?8'd2:(hud_header[3]==8'h32)?8'd3:8'd4))) hud_bad=1'b1;
        end
        if(hud32(54)+hud32(58)+hud32(62)+hud32(66)+32'd110!=32'(metadata_hud_bytes)) hud_bad=1'b1;
        byte_bad=1'b0;byte_error=8'd0;
        if(inner_validated) begin
            if((scan_addr>=16'd136)&&(scan_addr<16'd474)) begin
                for(integer slot=0;slot<4;slot=slot+1) begin
                    if((32'(scan_addr)-32'd136)*4+32'(slot)<32'd1350) begin
                        if(((rd_rsp_data>>(6-2*slot))&8'd3)==8'd3) begin
                            byte_bad=1'b1;byte_error=8'd8;
                        end
                    end else if(((rd_rsp_data>>(6-2*slot))&8'd3)!=0) begin
                        byte_bad=1'b1;byte_error=8'd8;
                    end
                end
            end
            if((scan_addr>=vector_start)&&(scan_addr<vector_end)&&(rd_rsp_data!=0)) begin
                byte_bad=1'b1;byte_error=8'd9;
            end
            for(integer plane=0;plane<3;plane=plane+1)
                if((scan_addr==plane_start[plane])&&(rd_rsp_data!=8'd5)&&(rd_rsp_data!=8'd6)) begin
                    byte_bad=1'b1;byte_error=8'd10;
                end
        end
    end

    always_ff @(posedge clk) begin
        if(rst) begin
            state<=IDLE;done<=0;aborted<=0;error<=0;error_code<=0;memory_reads<=0;
            packet_bytes<=0;scan_addr<=0;last_valid<=0;reference_valid<=0;
            last_frame_id<=0;reference_id<=0;reference_tag<=0;
            outer_validated<=0;inner_validated<=0;
            crc_outer<=32'hffffffff;crc_inner<=32'hffffffff;crc_hud<=32'hffffffff;
            received_outer<=0;received_inner<=0;received_hud<=0;
            inner_bytes<=0;vector_start<=0;vector_end<=0;
            prefix0<=0;prefix_yu<=0;prefix_y<=0;
            metadata_key<=0;metadata_frame_id<=0;metadata_reference_id<=0;
            metadata_reference_tag<=0;metadata_output_tag<=0;metadata_block_size<=0;
            metadata_hud_addr<=0;metadata_hud_bytes<=0;
            metadata_hud_reference_tag<=0;metadata_hud_output_tag<=0;
            qmap_rsp_valid<=0;qmap_rsp_index<=0;qmap_rsp_code<=0;
            for(i=0;i<3;i=i+1) begin
                plane_start[i]<=0;
                metadata_plane_addr[i]<=0;metadata_plane_bytes[i]<=0;
                metadata_plane_dispatch[i]<=0;metadata_plane_blocks[i]<=0;
                metadata_plane_blocks_w[i]<=0;
            end
        end else begin
            done<=0;qmap_rsp_valid<=0;
            if(qmap_req_valid&&qmap_req_ready) begin
                qmap_rsp_valid<=1;qmap_rsp_index<=qmap_req_index;
                case(qmap_req_index[1:0])
                    2'd0:qmap_rsp_code<=qmap_mem[qmap_req_index[10:2]][7:6];
                    2'd1:qmap_rsp_code<=qmap_mem[qmap_req_index[10:2]][5:4];
                    2'd2:qmap_rsp_code<=qmap_mem[qmap_req_index[10:2]][3:2];
                    2'd3:qmap_rsp_code<=qmap_mem[qmap_req_index[10:2]][1:0];
                endcase
            end
            if(abort_i&&(state!=IDLE)) begin
                aborted<=1;
                if(((state==READ_RESPONSE)||(state==DRAIN))&&!rd_rsp_valid) state<=DRAIN;
                else begin state<=IDLE;done<=1;end
            end else case(state)
                IDLE: if(cfg_valid&&cfg_ready) begin
                    error<=0;error_code<=0;aborted<=0;memory_reads<=0;
                    outer_validated<=0;inner_validated<=0;scan_addr<=0;
                    crc_outer<=32'hffffffff;crc_inner<=32'hffffffff;crc_hud<=32'hffffffff;
                    received_outer<=0;received_inner<=0;received_hud<=0;
                    packet_bytes<=cfg_packet_bytes;last_valid<=cfg_last_valid;
                    last_frame_id<=cfg_last_frame_id;reference_valid<=cfg_reference_valid;
                    reference_id<=cfg_reference_id;reference_tag<=cfg_reference_tag;
                    if((cfg_packet_bytes<16'd733)||(cfg_packet_bytes>16'd49152)) reject_packet(8'd1);
                    else state<=READ_REQUEST;
                end
                READ_REQUEST: if(rd_req_ready) begin memory_reads<=memory_reads+1;state<=READ_RESPONSE;end
                READ_RESPONSE: if(rd_rsp_valid) begin
                    if(byte_bad) reject_packet(byte_error);
                    else begin
                        if(scan_addr<packet_bytes-16'd4) crc_outer<=crc_byte(crc_outer,rd_rsp_data);
                        else received_outer[8*(scan_addr-(packet_bytes-16'd4))+:8]<=rd_rsp_data;
                        if(scan_addr<16'd76) outer_header[scan_addr[6:0]]<=rd_rsp_data;
                        if(outer_validated) begin
                            if((scan_addr>=16'd76)&&(scan_addr<16'd76+inner_bytes-16'd4))
                                crc_inner<=crc_byte(crc_inner,rd_rsp_data);
                            if((scan_addr>=16'd76+inner_bytes-16'd4)&&(scan_addr<16'd76+inner_bytes))
                                received_inner[8*(scan_addr-(16'd76+inner_bytes-16'd4))+:8]<=rd_rsp_data;
                            if((scan_addr>=16'd76)&&(scan_addr<16'd136)) inner_header[6'(scan_addr-16'd76)]<=rd_rsp_data;
                            if((scan_addr>=metadata_hud_addr)&&(scan_addr<packet_bytes-16'd8))
                                crc_hud<=crc_byte(crc_hud,rd_rsp_data);
                            if((scan_addr>=packet_bytes-16'd8)&&(scan_addr<packet_bytes-16'd4))
                                received_hud[8*(scan_addr-(packet_bytes-16'd8))+:8]<=rd_rsp_data;
                            if((scan_addr>=metadata_hud_addr)&&(scan_addr<metadata_hud_addr+16'd106))
                                hud_header[7'(scan_addr-metadata_hud_addr)]<=rd_rsp_data;
                        end
                        if(inner_validated) begin
                            if((scan_addr>=16'd136)&&(scan_addr<16'd474)) qmap_mem[9'(scan_addr-16'd136)]<=rd_rsp_data;
                            for(i=0;i<3;i=i+1) if(scan_addr==plane_start[i]) begin
                                metadata_plane_dispatch[i]<=rd_rsp_data[2:0];
                                metadata_plane_blocks[i]<=(rd_rsp_data==8'd6)?((i==0)?17'd5144:17'd1331):((i==0)?17'd5400:17'd1350);
                                metadata_plane_blocks_w[i]<=(rd_rsp_data==8'd6)?9'd1:((i==0)?9'd90:9'd45);
                            end
                        end
                        scan_addr<=scan_addr+16'd1;
                        if(scan_addr==16'd75) state<=CHECK_OUTER;
                        else if(scan_addr==16'd135) state<=CHECK_INNER;
                        else if(outer_validated&&(scan_addr==metadata_hud_addr+16'd105)) state<=CHECK_HUD;
                        else if(scan_addr==packet_bytes-16'd1) state<=CHECK_CRCS;
                        else state<=READ_REQUEST;
                    end
                end
                CHECK_OUTER: begin
                    if(({outer_header[0],outer_header[1],outer_header[2],outer_header[3]}!=32'h43553636)||
                       (outer_header[4]!=8'd1)||((outer_header[5]!=8'd2)&&(outer_header[5]!=8'd3))||
                       (outer16(6)!=16'd25)||(outer16(16)!=16'd720)||(outer16(18)!=16'd480)||
                       (outer128(20)!=CU66_PROFILE)) reject_packet(8'd2);
                    else if((outer32(8)==32'hffffffff)||(outer128(52)==0)||
                            (last_valid&&(outer32(8)<=last_frame_id))) reject_packet(8'd3);
                    else if((outer32(68)<32'd543)||(outer32(68)>32'(packet_bytes))||
                            (outer32(72)<32'd110)||(outer32(72)>32'(packet_bytes))||
                            ({1'b0,outer32(68)}+{1'b0,outer32(72)}+33'd80!={17'd0,packet_bytes})) reject_packet(8'd4);
                    else if(outer_header[5][0]?((outer32(12)!=32'hffffffff)||(outer128(36)!=0)):
                            (!reference_valid||(outer32(12)!=reference_id)||(outer32(12)>=outer32(8))||
                             (outer128(36)==0)||(outer128(36)!=reference_tag))) reject_packet(8'd5);
                    else begin
                        metadata_key<=outer_header[5][0];metadata_frame_id<=outer32(8);metadata_reference_id<=outer32(12);
                        metadata_reference_tag<=outer128(36);metadata_output_tag<=outer128(52);
                        inner_bytes<=16'(outer32(68));metadata_hud_addr<=16'd76+16'(outer32(68));metadata_hud_bytes<=16'(outer32(72));
                        outer_validated<=1;state<=READ_REQUEST;
                    end
                end
                CHECK_INNER: begin
                    if(({inner_header[0],inner_header[1],inner_header[2],inner_header[3]}!=32'h47553636)||
                       (inner_header[4]!=8'd1)||(inner_header[5]!={7'd0,metadata_key})||
                       (inner32(6)!=32'd25)||(inner32(10)!=metadata_frame_id)||(inner32(14)!=metadata_reference_id)||
                       (inner16(18)!=16'd720)||(inner16(20)!=16'd480)||
                       ((inner_header[22]!=8'd16)&&(inner_header[22]!=8'd32))||(inner_header[23]!=8'd18)||
                       (inner128(24)!=metadata_reference_tag)) reject_packet(8'd6);
                    else if((inner32(40)!=32'd338)||(inner32(44)!=(metadata_key?32'd0:32'd3))||
                            (inner32(48)<32'd47)||(inner32(48)>32'(packet_bytes))||
                            (inner32(52)<32'd47)||(inner32(52)>32'(packet_bytes))||
                            (inner32(56)<32'd47)||(inner32(56)>32'(packet_bytes))||
                            (inner32(40)+inner32(44)+inner32(48)+inner32(52)+inner32(56)+32'd64!=32'(inner_bytes))) reject_packet(8'd7);
                    else begin
                        metadata_block_size<=inner_header[22];
                        // Preserve the original 16-bit modular prefix domain.
                        // Only checked, immutable header fields reach these stages.
                        prefix0<=16'd474+16'(inner32(44));
                        prefix_yu<=16'(inner32(48))+16'(inner32(52));
                        prefix_y<=16'(inner32(48));
                        for(i=0;i<3;i=i+1) begin
                            metadata_plane_bytes[i]<=16'(inner32(48+4*i))-16'd1;
                        end
                        state<=PREFIX_STARTS;
                    end
                end
                PREFIX_STARTS: begin
                    vector_start<=16'd474;vector_end<=prefix0;
                    plane_start[0]<=prefix0;
                    plane_start[1]<=prefix0+prefix_y;
                    plane_start[2]<=prefix0+prefix_yu;
                    state<=PREFIX_ADDRESSES;
                end
                PREFIX_ADDRESSES: begin
                    for(i=0;i<3;i=i+1) metadata_plane_addr[i]<=plane_start[i]+16'd1;
                    inner_validated<=1;state<=READ_REQUEST;
                end
                CHECK_HUD: begin
                    if((({hud_header[0],hud_header[1],hud_header[2],hud_header[3]}!=32'h48553235)&&
                        ({hud_header[0],hud_header[1],hud_header[2],hud_header[3]}!=32'h48583332)&&
                        ({hud_header[0],hud_header[1],hud_header[2],hud_header[3]}!=32'h48583333))||
                       (hud_header[4]!=8'd1)||(hud_header[5]!=8'd4)||(hud32(6)!=32'd25)||
                       (hud32(10)!=metadata_frame_id)||(hud32(14)!=metadata_reference_id)||
                       (hud16(18)!=16'd720)||(hud16(20)!=16'd480)||(hud128(38)==0)||
                       (metadata_key?(hud128(22)!=0):(hud128(22)==0))) reject_packet(8'd11);
                    else begin
                        if(hud_bad) reject_packet(8'd12);
                        else begin metadata_hud_reference_tag<=hud128(22);metadata_hud_output_tag<=hud128(38);state<=READ_REQUEST;end
                    end
                end
                CHECK_CRCS: begin
                    if((crc_outer^32'hffffffff)!=received_outer) reject_packet(8'd13);
                    else if((crc_inner^32'hffffffff)!=received_inner) reject_packet(8'd14);
                    else if((crc_hud^32'hffffffff)!=received_hud) reject_packet(8'd15);
                    else state<=OFFER_METADATA;
                end
                OFFER_METADATA: if(metadata_ready) state<=WAIT_COMMIT;
                WAIT_COMMIT: if(commit_valid) begin state<=IDLE;done<=1;end
                DRAIN: if(rd_rsp_valid) begin state<=IDLE;done<=1;end
                default: reject_packet(8'd255);
            endcase
        end
    end
endmodule
