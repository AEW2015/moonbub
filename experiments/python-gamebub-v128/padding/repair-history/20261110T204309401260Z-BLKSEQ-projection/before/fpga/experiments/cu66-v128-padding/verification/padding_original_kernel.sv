module padding_original_kernel(
    input logic clk,reset,start,abort_packet,
    input logic [7:0] state,byte_value,
    input logic [31:0] header_index,receipt_epoch,size_bytes,snapshot_fid,
    input logic snapshot_valid,
    input logic [63:0] snapshot_generation,
    input logic [34:0] header_packet_total,
    output logic observed_padding,
    output logic [7:0] error
);
    localparam logic [7:0] HEADER_BYTE=4, HEADER_CHECK=5;
    logic [7:0] header [0:127];
    logic padding_ok;
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
    always_ff @(posedge clk)begin
        if(reset||start||abort_packet)error<=0;
        else begin
            if(state==HEADER_BYTE)begin
                    header[header_index[6:0]]<=byte_value;
            end
            if(state==HEADER_CHECK)begin
                    padding_ok=1;
                    for(integer k=116;k<128;k=k+1)if(header[k]!=0)padding_ok=0;
                    if(h32(0)!=32'h43533838||header[4]!=1||header[6]!=16||
                       h16(28)!=32||h32(32)!=65536||
                       (header[5]==1?header[7]!=0:header[7]!=3))error<=8'd4;
                    else if(header[5]>1||h16(24)!=720||h16(26)!=480||h16(30)!=0||!padding_ok||
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
    assign observed_padding=padding_ok;
endmodule

