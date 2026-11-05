`timescale 1ns/1ps
module tb_painter_control;
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
    reg pending=0;
    reg pending_write=0;
    reg [23:0] pending_addr=0;
    reg [15:0] pending_data=0;
    integer delay=0,write_checks=0,read_checks=0;
    integer px,yy,sample;
    reg [15:0] expected;
    cu70_painter dut(.clk,.rst,.abort_i,.start_valid,.start_ready,.generation,.frame_id,
        .y_base(24'h080000),.u_base(24'h0aa300),.v_base(24'h0b4bc0),
        .hud_base(24'h100000),.rgb_base(24'hc00000),
        .aux_req_valid(req_valid),.aux_req_ready(req_ready),.aux_req_write(req_write),
        .aux_req_addr(req_addr),.aux_req_data(req_data),.aux_rsp_valid(rsp_valid),
        .aux_rsp_ready(rsp_ready),.aux_rsp_data(rsp_data),.aux_rsp_error(1'b0),
        .result_valid,.result_ready(1'b0),.result_generation,.result_frame_id,
        .busy,.done,.aborted,.error,.error_code,.memory_reads(reads),.memory_writes(writes),
        .painted_pixels(painted),.cycle_count(cycles));
    always @(posedge clk)begin
        if(rst)begin pending<=0;rsp_valid<=0;delay<=0;end
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
                    sample=((int'(pending_addr)-32'h00080000)*2*17)&255;
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
                        if(px!=write_checks-19200||yy!=0)$fatal(1,"portraitmapping");
                        sample=(px*17)&255;
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
        wait(write_checks==19920);
        @(negedge clk);abort_i=1;
        @(negedge clk);abort_i=0;
        wait(!busy);@(negedge clk);
        if(error||pending||!start_ready||result_valid||done||!aborted||result_generation!=70||result_frame_id!=100||reads!=1080||writes!=19920||cycles==0)$fatal(1,"abortlease");
        if(read_checks!=1080||painted!=720)$fatal(1,"rowcounts %0d %0d",read_checks,painted);
        $display("TEST_PASS_PAINTER_CONTROL topbars=19200 coded_pixels=720 reads=1080 invalid_generation_rejected=1 abort_drained=1");
        $finish;
    end
endmodule
