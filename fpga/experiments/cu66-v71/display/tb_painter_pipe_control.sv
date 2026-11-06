`timescale 1ns/1ps
module tb_painter_pipe_control;
    reg clk=0;always #5 clk=~clk;
    reg rst=1,abort_i=0,start_valid=0;
    wire start_ready;
    reg [63:0] generation=0;
    reg [31:0] frame_id=0;
    wire req_valid,req_write,rsp_ready,result_valid,busy,done,aborted,error;
    wire [23:0] req_addr;
    wire [15:0] req_data;
    reg req_ready=1,rsp_valid=0;
    reg [15:0] rsp_data=0;
    wire [63:0] result_generation;
    wire [31:0] result_frame_id,reads,writes,painted,cycles;
    wire [7:0] error_code;
    reg pending=0;reg clear_counts=0;integer source_bias=0;
    reg pending_write=0;
    reg [23:0] pending_addr=0;
    reg [15:0] pending_data=0;
    integer delay=0,write_checks=0,read_checks=0;
    integer px,yy,sample;
    reg [15:0] expected;
    cu71_painter_strip_pipe dut(.clk,.rst,.abort_i,.start_valid,.start_ready,.generation,.frame_id,
        .y_base(24'h080000),.u_base(24'h0aa300),.v_base(24'h0b4bc0),
        .hud_base(24'h100000),.rgb_base(24'hc00000),
        .aux_req_valid(req_valid),.aux_req_ready(req_ready),.aux_req_write(req_write),
        .aux_req_addr(req_addr),.aux_req_data(req_data),.aux_rsp_valid(rsp_valid),
        .aux_rsp_ready(rsp_ready),.aux_rsp_data(rsp_data),.aux_rsp_error(1'b0),
        .result_valid,.result_ready(1'b0),.result_generation,.result_frame_id,
        .busy,.done,.aborted,.error,.error_code,.memory_reads(reads),.memory_writes(writes),
        .painted_pixels(painted),.cycle_count(cycles));
    always @(posedge clk)begin
        if(rst||clear_counts)begin pending<=0;rsp_valid<=0;delay<=0;req_ready<=1;write_checks<=0;read_checks<=0;end
        else begin
            if(req_valid&&req_ready)begin
                if(pending)$fatal(1,"overlappingoperations");
                pending<=1;pending_write<=req_write;pending_addr<=req_addr;pending_data<=req_data;delay<=2;
                req_ready<=0;
            end
            if(pending&&delay>0)delay<=delay-1;
            if(pending&&delay==0&&!rsp_valid)begin
                rsp_valid<=1;
                if(pending_write)rsp_data<=0;
                else if(pending_addr<24'h0aa300)begin
                    sample=((int'(pending_addr)-32'h00080000)*2*17+source_bias)&255;
                    rsp_data<=16'(sample|(((sample+17)&255)<<8));
                end else rsp_data<=16'h8080;
            end
            if(rsp_valid&&rsp_ready)begin
                rsp_valid<=0;pending<=0;req_ready<=1;
                if(pending_write)begin
                    if(write_checks<19200)begin
                        if(pending_addr!=24'hc00000+24'(write_checks)||pending_data!=0)$fatal(1,"topbars");
                    end else begin
                        px=(int'(pending_addr)-32'h00c00000)/480-40;
                        yy=(int'(pending_addr)-32'h00c00000)%480;
                        if(px!=0||yy!=write_checks-19200)$fatal(1,"strip_portrait_mapping");
                        sample=(yy*720*17+source_bias)&255;
                        expected={5'(sample>>3),6'(sample>>2),5'(sample>>3)};
                        if(pending_data!=expected)$fatal(1,"grayroundtrip px%0d expected%h got%h",px,expected,pending_data);
                    end
                    write_checks<=write_checks+1;
                end else read_checks<=read_checks+1;
            end
        end
    end
    initial begin
        #20000000;$fatal(1,"watchdog");
    end
    initial begin
        repeat(3)@(negedge clk);rst=0;
        @(negedge clk);start_valid=1;
        @(negedge clk);start_valid=0;
        wait(!busy);if(!error||error_code!=1||writes!=0)$fatal(1,"invalidgeneration");
        @(negedge clk);generation=70;frame_id=100;start_valid=1;
        @(negedge clk);start_valid=0;
        wait(painted==123);
        @(negedge clk);abort_i=1;
        @(negedge clk);abort_i=0;
        wait(!busy);@(negedge clk);
        if(error||pending||!start_ready||result_valid||done||!aborted||result_generation!=70||result_frame_id!=100||writes!=19200)$fatal(1,"dirty_strip_abort");
        if(read_checks!=1080||write_checks!=19200)$fatal(1,"dirty_strip_no_canvas_writes");
        clear_counts=1;source_bias=91;
        @(negedge clk);clear_counts=0;generation=71;frame_id=101;start_valid=1;
        @(negedge clk);start_valid=0;
        wait(write_checks==19208);
        @(negedge clk);abort_i=1;
        @(negedge clk);abort_i=0;
        wait(!busy);@(negedge clk);
        if(error||pending||!start_ready||result_valid||done||!aborted||result_generation!=71||result_frame_id!=101||reads!=4680||writes!=19208||painted!=5760||cycles==0||read_checks!=4680)$fatal(1,"strip_drain_abort_lease");
        // Configuration-style reset flushes DUT and external model together.
        // The bulk data arrays are intentionally NOT reset. A new generation
        // and source bias must overwrite/validate every used cache/strip word.
        clear_counts=1;source_bias=37;
        @(negedge clk);clear_counts=0;generation=72;frame_id=102;start_valid=1;
        @(negedge clk);start_valid=0;wait(painted==123);
        @(negedge clk);rst=1;
        repeat(3)@(negedge clk);rst=0;source_bias=173;generation=73;frame_id=103;start_valid=1;
        @(negedge clk);start_valid=0;wait(write_checks==19208);
        @(negedge clk);abort_i=1;
        @(negedge clk);abort_i=0;wait(!busy);@(negedge clk);
        if(error||pending||!start_ready||result_valid||done||!aborted||result_generation!=73||result_frame_id!=103||reads!=4680||writes!=19208||painted!=5760)
            $fatal(1,"unreset_RAM_reset_recovery");
        $display("TEST_PASS_BRAM_STRIP_CONTROL dirty_pixels_discarded=123 no_premature_canvas_writes=1 reset_new_bias=173 first_contiguous_words=8 reads=4680 strip_pixels=5760 abort_drained=1 coordinated_reset=1");
        $finish;
    end
endmodule
