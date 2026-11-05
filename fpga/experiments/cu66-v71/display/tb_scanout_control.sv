`timescale 1ps/1ps
module tb_scanout_control;
    logic mem_clk=0,pixel_clk=0,mem_rst=1,pixel_reset_n=0;
    always #5000 mem_clk=~mem_clk;
    always #17029 pixel_clk=~pixel_clk;
    logic descriptor_valid=0,descriptor_ready;
    logic [63:0] descriptor_generation=1;
    logic [31:0] descriptor_frame_id=10;
    logic descriptor_slot=0;
    wire presented,error,front_valid,front_slot,pending_valid;
    wire [63:0] front_generation;
    wire [31:0] front_frame_id,presented_count;
    wire frame_boundary,scanout_drained,lcd_req_valid;
    logic lcd_req_ready=0;
    wire [23:0] lcd_req_addr;
    logic lcd_rsp_valid=0,lcd_rsp_last=0,lcd_rsp_error=0;
    logic [15:0] lcd_rsp_data=16'haa55;
    wire lcd_rsp_ready;
    wire [31:0] underruns,memory_errors;
    wire hsync,vsync,data_enable;
    wire [9:0] physical_x,physical_y;
    wire [7:0] red,green,blue;
    integer checks=0;
    cu71_scanout dut(.*);
    task check(input bit condition,input string label_text);
        if(!condition)$fatal(1,"FAIL %s",label_text);
        checks=checks+1;
    endtask
    initial begin
        #250000;
        @(negedge mem_clk);mem_rst=0;pixel_reset_n=1;descriptor_valid=1;
        @(posedge mem_clk);check(descriptor_ready,"initial_descriptor_ready");
        @(negedge mem_clk);descriptor_valid=0;
        wait(presented);#1;
        check(front_valid&&front_generation==1&&front_frame_id==10,"front_identity");
        wait(lcd_req_valid);
        @(negedge mem_clk);lcd_req_ready=1;
        check(lcd_req_addr[2:0]==0,"burst_aligned");
        @(posedge mem_clk);
        @(negedge mem_clk);lcd_req_ready=0;lcd_rsp_valid=1;lcd_rsp_last=1;
        check(lcd_rsp_ready&&!scanout_drained,"accepted_burst_owned");
        @(posedge mem_clk);#1;
        check(memory_errors==1&&error,"early_last_reported");
        @(negedge mem_clk);lcd_rsp_valid=0;
        repeat(20)begin
            @(posedge mem_clk);#1;
            check(lcd_rsp_ready&&!lcd_req_valid&&!scanout_drained,"gapped_burst_remains_owned");
        end
        // Reset is a coordinated flush of both domains and the memory source.
        @(negedge mem_clk);mem_rst=1;pixel_reset_n=0;
        repeat(10)@(posedge mem_clk);
        #1;check(!front_valid&&!pending_valid&&presented_count==0,"reset_front_and_queue");
        check(!lcd_req_valid&&!lcd_rsp_ready&&memory_errors==0,"reset_reader_and_diagnostics");
        @(negedge mem_clk);mem_rst=0;pixel_reset_n=1;lcd_rsp_valid=1;
        #1;check(!lcd_rsp_ready,"orphan_reply_not_consumed");
        @(posedge mem_clk);#1;check(memory_errors==0,"orphan_reply_no_effect");
        @(negedge mem_clk);lcd_rsp_valid=0;descriptor_valid=1;
        // Generation one is valid again only because all adapters were flushed.
        @(posedge mem_clk);check(descriptor_ready,"fresh_generation_after_flush");
        @(negedge mem_clk);descriptor_valid=0;
        wait(presented);#1;
        check(front_valid&&front_generation==1&&presented_count==1,"fresh_descriptor_presented");
        $display("TEST_PASS_SCANOUT_CONTROL checks=%0d early_last=1 gap_cycles=20 reset_flush=1 orphan_ignored=1",checks);
        $finish;
    end
    initial begin #20000000000;$fatal(1,"FAIL watchdog_20ms");end
endmodule
