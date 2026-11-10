module padding_candidate_kernel(
    input logic clk,reset,start,abort_packet,
    input logic [7:0] state,byte_value,
    input logic [31:0] header_index,receipt_epoch,size_bytes,snapshot_fid,
    input logic snapshot_valid,
    input logic [63:0] snapshot_generation,
    input logic [34:0] header_packet_total,
    output logic observed_padding,
    output logic [7:0] error,
    output logic observed_cache,owner_complete
);
    localparam logic [7:0] HEADER_BYTE=4, HEADER_CHECK=5;
    logic [7:0] header [0:127];
    logic evaluated_padding;
    // V128_PADDING_CACHE_BEGIN: one unreset Boolean payload, owned only
    // after the current header's ordered116..127 byte-load edges. The final
    // byte is forwarded here while header[127] still has its old NBA value.
    logic prepared_header_padding_ok;
    always_ff @(posedge clk)if(state==HEADER_BYTE && header_index>=116 && header_index<=127)
        prepared_header_padding_ok<=header_index==116 ? byte_value==0 :
            prepared_header_padding_ok && byte_value==0;
    // V128_PADDING_CACHE_END
`ifndef SYNTHESIS
    // V128_PADDING_OWNER_BEGIN: verification-only freshness, not payload reset.
    logic padding_owner_valid=0;
    logic [31:0] padding_owner_epoch,padding_owner_size,padding_owner_next;
    logic padding_reference_ok;
    always_comb begin
        padding_reference_ok=1;
        for(integer padding_index=116;padding_index<128;padding_index=padding_index+1)
            if(header[padding_index]!=0)padding_reference_ok=0;
    end
    always_ff @(posedge clk)begin
        if(reset||start||abort_packet)padding_owner_valid<=0;
        else if(state==HEADER_BYTE && header_index>=116 && header_index<=127)begin
            if(header_index==116)begin
                padding_owner_valid<=1;
                padding_owner_epoch<=receipt_epoch;padding_owner_size<=size_bytes;
            end else begin
                assert(padding_owner_valid && padding_owner_epoch==receipt_epoch &&
                    padding_owner_size==size_bytes && padding_owner_next==header_index)
                    else $fatal(1,"V128 padding byte sequence lost its complete owner");
            end
            padding_owner_next<=header_index+32'd1;
        end else if(state==HEADER_CHECK)padding_owner_valid<=0;
    end
    always_ff @(posedge clk)if(!reset&&!start&&!abort_packet&&state==HEADER_CHECK)begin
        assert(padding_owner_valid && padding_owner_epoch==receipt_epoch &&
            padding_owner_size==size_bytes && padding_owner_next==128 && header_index==127)
            else $fatal(1,"V128 padding consume without full owned116..127 writer sequence");
        assert(prepared_header_padding_ok==padding_reference_ok)
            else $fatal(1,"V128 padding cache differs from current complete header");
    end
    // V128_PADDING_OWNER_END
`endif
    logic prepared_header_total_matches;
    always_ff @(posedge clk)if(state==HEADER_BYTE)
        prepared_header_total_matches<=header_packet_total=={3'd0,size_bytes};
`ifndef SYNTHESIS
    logic header_match_owner_valid;
    logic [31:0] header_match_owner_epoch, header_match_owner_size;
    logic [34:0] header_match_owner_total;
    always_ff @(posedge clk)begin
        if(reset||start||abort_packet)header_match_owner_valid<=0;
        else if(state==HEADER_BYTE&&header_index==127)begin
            header_match_owner_valid<=1;
            header_match_owner_epoch<=receipt_epoch;
            header_match_owner_size<=size_bytes;
            header_match_owner_total<=header_packet_total;
        end else if(state==HEADER_CHECK)header_match_owner_valid<=0;
    end
    always_ff @(posedge clk)if(!reset&&!start&&!abort_packet&&state==HEADER_CHECK)begin
        assert(header_match_owner_valid&&header_index==127&&
            header_match_owner_epoch==receipt_epoch&&header_match_owner_size==size_bytes&&
            header_match_owner_total==header_packet_total)
            else $fatal(1,"V120 header equality complete owner mismatch");
        assert(prepared_header_total_matches==(header_packet_total=={3'd0,size_bytes}))
            else $fatal(1,"V120 full35 header equality payload mismatch");
    end
`endif
    function automatic logic [31:0] h32(input integer n);
        return {header[n],header[n+1],header[n+2],header[n+3]};
    endfunction
    function automatic logic [15:0] h16(input integer n);
        return {header[n],header[n+1]};
    endfunction
    always_comb begin
                    evaluated_padding=prepared_header_padding_ok;
    end
    always_ff @(posedge clk)begin
        if(reset||start||abort_packet)error<=0;
        else begin
            if(state==HEADER_BYTE)begin
                    header[header_index[6:0]]<=byte_value;
            end
            if(state==HEADER_CHECK)begin
                    observed_padding<=evaluated_padding;
                    if(h32(0)!=32'h43533838||header[4]!=1||header[6]!=16||
                       h16(28)!=32||h32(32)!=65536||
                       (header[5]==1?header[7]!=0:header[7]!=3))error<=8'd4;
                    else if(header[5]>1||h16(24)!=720||h16(26)!=480||h16(30)!=0||!evaluated_padding||
                        h32(36)>976||h32(40)<16||h32(40)>354||h32(44)<110||h32(44)>49152||
                        !prepared_header_total_matches)error<=8'd5;
                    else if(h32(8)==32'hffffffff||{h32(16),h32(20)}==0||
                        (snapshot_valid&&(h32(8)<=snapshot_fid||{h32(16),h32(20)}<=snapshot_generation)))error<=8'd6;
                    else if(header[5]==1?h32(12)!=32'hffffffff:(!snapshot_valid||h32(12)!=snapshot_fid))error<=8'd7;
                    else if(header[5]==1&&h32(36)!=0)error<=8'd8;
                    else error<=0;
            end
        end
    end
    assign observed_cache=prepared_header_padding_ok;
    assign owner_complete=padding_owner_valid && padding_owner_next==128;
endmodule
