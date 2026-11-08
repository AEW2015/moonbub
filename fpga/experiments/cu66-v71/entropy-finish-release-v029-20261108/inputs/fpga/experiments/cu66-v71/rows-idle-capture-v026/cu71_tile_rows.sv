// Ordered full-grid canonical uint8 tiles -> geometry + planar row-major bytes.
// Canonical SHA serialization only; this is NOT physical LCD scanout/rotation.
module cu71_tile_rows #(
    parameter integer STRIP_BANKS=1
)(
    input logic clk,rst,abort_i,
    input logic start_valid,
    output logic start_ready,
    input logic [31:0] frame_id,
    input logic key,
    input logic tile_valid,
    output logic tile_ready,
    input logic [511:0] tile_pixels,
    input logic [31:0] tile_frame_id,
    input logic tile_key,
    input logic [1:0] tile_plane,
    input logic [16:0] tile_index,
    input logic tile_last,
    output logic data_valid,
    input logic data_ready,
    output logic [7:0] data,
    output logic data_last,
    output logic busy,done,error,aborted,
    output logic [7:0] error_code,
    output logic [31:0] accepted_tiles,emitted_bytes,
    output logic [31:0] strip_word_writes,strip_word_reads,
    output logic [31:0] input_stall_cycles,output_stall_cycles,
    output logic write_busy,
    output logic [1:0] expected_plane,
    output logic [16:0] expected_index
);
    logic active,input_done;
    logic [31:0] current_frame;
    logic current_key;
    wire [63:0] bank_output [0:STRIP_BANKS-1];
    logic selected_read_bank;
    logic [STRIP_BANKS-1:0] bank_full,bank_last;
    logic [9:0] bank_words [0:STRIP_BANKS-1];
    logic fill_bank,read_bank;
    logic [6:0] tile_column,fill_words;
    logic [511:0] captured_tile;
    logic [2:0] write_row;
    logic [9:0] write_address;
    logic [63:0] output_word;
    logic cache_valid,prefix_pending;
    logic [1:0] prefix_index;
    logic [9:0] read_word;
    logic [2:0] read_byte;
    logic expected_last,bad_tile;
    logic ram_read_enable,ram_read_bank;
    logic [9:0] ram_read_address;
    always_comb begin
        busy=active;
        start_ready=!active&&!abort_i&&!rst;
        tile_ready=active&&!input_done&&!write_busy&&!bank_full[fill_bank]&&!abort_i&&!rst;
        fill_words=expected_plane==0?7'd90:7'd45;
        expected_last=(expected_plane==2&&expected_index==1349);
        bad_tile=tile_valid&&tile_ready&&(tile_frame_id!=current_frame||tile_key!=current_key||tile_plane!=expected_plane||tile_index!=expected_index||tile_last!=expected_last);
        data_valid=active&&(prefix_pending||cache_valid)&&!abort_i&&!rst;
        data_last=active&&!prefix_pending&&cache_valid&&bank_last[read_bank]&&
                  read_word+10'd1==bank_words[read_bank]&&read_byte==7;
        if(prefix_pending)case(prefix_index)
            0:data=8'hd0;1:data=8'h02;2:data=8'he0;default:data=8'h01;
        endcase
        else data=output_word[{read_byte,3'd0}+:8];
        ram_read_enable=0;ram_read_bank=read_bank;ram_read_address=0;
        if(active&&!rst&&!abort_i&&!bad_tile)begin
            if(prefix_pending)begin
                if(data_ready&&prefix_index==3&&bank_full[read_bank])ram_read_enable=1;
            end else if(cache_valid)begin
                if(data_ready&&read_byte==7)begin
                    if(read_word+10'd1<bank_words[read_bank])begin ram_read_enable=1;ram_read_address=read_word+10'd1;end
                    else if(!bank_last[read_bank]&&STRIP_BANKS==2&&bank_full[!read_bank])begin ram_read_enable=1;ram_read_bank=!read_bank;end
                end
            end else if(bank_full[read_bank])ram_read_enable=1;
        end
    end
    // Deliberately unreset RAM output register: cache_valid protects ownership.
    // Each bank has one explicit synchronous read/write RAM. No data reset.
    wire ram_write_enable=active&&!rst&&!abort_i&&!bad_tile&&write_busy;
    genvar bank_number;
    generate for(bank_number=0;bank_number<STRIP_BANKS;bank_number=bank_number+1)begin:strip_bank
        (* ram_style="block" *) logic [63:0] memory [0:719];
        logic [63:0] read_data;
        always_ff @(posedge clk)begin
            if(ram_write_enable&&fill_bank==bank_number)
                memory[write_address]<=captured_tile[{write_row,6'd0}+:64];
            if(ram_read_enable)read_data<=memory[ram_read_address];
        end
        assign bank_output[bank_number]=read_data;
    end endgenerate
    always_ff @(posedge clk)if(ram_read_enable)selected_read_bank<=ram_read_bank;
    generate if(STRIP_BANKS==1)begin:single_bank
        always_comb output_word=bank_output[0];
    end else begin:two_banks
        always_comb output_word=bank_output[selected_read_bank];
    end endgenerate
    // Speculatively capture while idle; payload is authoritative only while
    // write_busy is asserted. A true tile handshake sets write_busy on the same
    // edge that captures the accepted pixels. Abort/reset invalidate tokens,
    // never require resetting the 512-bit payload. No added handshake latency.
    always_ff @(posedge clk) if(!write_busy) captured_tile<=tile_pixels;
    always_ff @(posedge clk)begin
        if(rst)begin
            active<=0;input_done<=0;current_frame<=0;current_key<=0;bank_full<=0;bank_last<=0;fill_bank<=0;read_bank<=0;
            tile_column<=0;write_row<=0;write_address<=0;write_busy<=0;
            cache_valid<=0;prefix_pending<=0;prefix_index<=0;read_word<=0;read_byte<=0;
            expected_plane<=0;expected_index<=0;done<=0;error<=0;aborted<=0;error_code<=0;
            accepted_tiles<=0;emitted_bytes<=0;strip_word_writes<=0;strip_word_reads<=0;input_stall_cycles<=0;output_stall_cycles<=0;
        end else begin
            done<=0;aborted<=0;
            if(abort_i)begin active<=0;input_done<=0;bank_full<=0;bank_last<=0;write_busy<=0;cache_valid<=0;prefix_pending<=0;aborted<=1;end
            else if(start_valid&&start_ready)begin
                error<=0;error_code<=0;
                if(frame_id==32'hffffffff)begin error<=1;error_code<=1;end
                else begin
                    active<=1;input_done<=0;current_frame<=frame_id;current_key<=key;bank_full<=0;bank_last<=0;fill_bank<=0;read_bank<=0;
                    tile_column<=0;write_busy<=0;cache_valid<=0;prefix_pending<=1;prefix_index<=0;read_word<=0;read_byte<=0;
                    expected_plane<=0;expected_index<=0;accepted_tiles<=0;emitted_bytes<=0;strip_word_writes<=0;strip_word_reads<=0;input_stall_cycles<=0;output_stall_cycles<=0;
                end
            end else if(bad_tile)begin
                active<=0;bank_full<=0;write_busy<=0;cache_valid<=0;prefix_pending<=0;error<=1;
                error_code<=tile_last!=expected_last?8'h03:8'h02;
            end else if(active)begin
                if(ram_read_enable)strip_word_reads<=strip_word_reads+1;
                if(tile_valid&&!tile_ready&&!input_done)input_stall_cycles<=input_stall_cycles+1;
                if(data_valid&&!data_ready)output_stall_cycles<=output_stall_cycles+1;
                if(tile_valid&&tile_ready)begin
                    write_row<=0;write_address<={3'd0,tile_column};write_busy<=1;accepted_tiles<=accepted_tiles+1;
                end
                if(write_busy)begin
                    strip_word_writes<=strip_word_writes+1;
                    if(write_row==7)begin
                        write_busy<=0;
                        if(tile_column+7'd1==fill_words)begin
                            bank_full[fill_bank]<=1;bank_last[fill_bank]<=expected_last;bank_words[fill_bank]<={fill_words,3'd0};tile_column<=0;
                            if(STRIP_BANKS==2)fill_bank<=!fill_bank;
                        end else tile_column<=tile_column+1;
                        if(expected_index==(expected_plane==0?17'd5399:17'd1349))begin
                            expected_index<=0;
                            if(expected_plane==2)input_done<=1;else expected_plane<=expected_plane+1;
                        end else expected_index<=expected_index+1;
                    end else begin write_row<=write_row+1;write_address<=write_address+{3'd0,fill_words};end
                end
                if(prefix_pending)begin
                    if(data_valid&&data_ready)begin
                        emitted_bytes<=emitted_bytes+1;
                        if(prefix_index==3)begin
                            prefix_pending<=0;
                            if(bank_full[read_bank])begin cache_valid<=1;read_word<=0;read_byte<=0;end
                        end else prefix_index<=prefix_index+1;
                    end
                end else if(cache_valid)begin
                    if(data_valid&&data_ready)begin
                        emitted_bytes<=emitted_bytes+1;
                        if(read_byte==7)begin
                            read_byte<=0;
                            if(read_word+10'd1==bank_words[read_bank])begin
                                bank_full[read_bank]<=0;cache_valid<=0;read_word<=0;
                                if(bank_last[read_bank])begin
                                    if(emitted_bytes!=518403)begin error<=1;error_code<=4;end
                                    else done<=1;
                                    active<=0;
                                end else if(STRIP_BANKS==2)begin
                                    read_bank<=!read_bank;
                                    if(bank_full[!read_bank])begin cache_valid<=1;end
                                end
                            end else begin
                                read_word<=read_word+1;
                            end
                        end else read_byte<=read_byte+1;
                    end
                end else if(bank_full[read_bank])begin
                    cache_valid<=1;read_word<=0;read_byte<=0;
                end
            end
        end
    end
endmodule
