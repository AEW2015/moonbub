`timescale 1ns/1ps
module tb_inverse_q14;
    parameter integer BYPASS=1;
    parameter integer SHORT=0;
    `include "vector_config.vh"
    localparam integer RUN_BLOCKS=SHORT!=0 ? DIRECTED_BLOCKS : VECTOR_BLOCKS;
    localparam integer RUN_SAMPLES=RUN_BLOCKS*64;
    reg clk=0;
    always #5 clk=~clk;
    reg rst=1,in_valid=0,out_ready=0;
    wire in_ready,out_valid,out_last;
    reg signed [19:0] in_coeff=0;
    reg [7:0] in_prediction=0;
    wire [5:0] out_index;
    wire signed [23:0] out_residual;
    wire [7:0] out_pixel;
    // Icarus12 misreports $isunknown on an inline concatenation of known bits.
    // Named vectors preserve the complete X/Z checks; see unknown_repro.sv.
    wire [1:0] handshake_check={out_valid,in_ready};
    wire [38:0] output_check={out_residual,out_pixel,out_index,out_last};
    `ifdef MAPPED
    inverse_q14 dut(.*); // Synthesized default BYPASS=1 has no remaining parameter.
    `else
    inverse_q14 #(.BYPASS(BYPASS)) dut(.*);
    `endif
    reg signed [19:0] coeff_data[0:VECTOR_BLOCKS*64-1];
    reg [7:0] prediction_data[0:VECTOR_BLOCKS*64-1];
    reg signed [23:0] residual_data[0:VECTOR_BLOCKS*64-1];
    reg [7:0] pixel_data[0:VECTOR_BLOCKS*64-1];
    reg [3:0] kind_data[0:VECTOR_BLOCKS-1];
    string prefix;
    reg enabled=0,pending=0,previous_stall=0;
    reg [38:0] held_output=0;
    reg [31:0] lfsr=32'h31cafe17;
    integer stall_mode=0,sent=0,received=0,cycle=0,start_cycle=0;
    integer total_service_cycles=0,stall_cycles=0;

    task automatic reset_kernel;
        begin
            @(negedge clk);rst=1;in_valid=0;out_ready=0;
            repeat(3) @(negedge clk);
            rst=0;
            @(negedge clk);
            if(out_valid!==0 || in_ready!==1)$fatal(1,"RESET_NOT_FLUSHED");
        end
    endtask
    task automatic word(input signed [19:0] c,input [7:0] p);
        begin
            @(negedge clk);in_valid=1;in_coeff=c;in_prediction=p;
            @(posedge clk);while(!in_ready)@(posedge clk);
            @(negedge clk);in_valid=0;
        end
    endtask
    integer i;
    initial begin
        if(!$value$plusargs("FIXTURES=%s",prefix))$fatal(1,"FIXTURES_REQUIRED");
        if(!$value$plusargs("STALL=%d",stall_mode))stall_mode=0;
        $readmemh({prefix,"/coeff.mem"},coeff_data);
        $readmemh({prefix,"/prediction.mem"},prediction_data);
        $readmemh({prefix,"/residual.mem"},residual_data);
        $readmemh({prefix,"/pixel.mem"},pixel_data);
        $readmemh({prefix,"/kind.mem"},kind_data);
        reset_kernel();
        word(20'sd3,8'd128);word(-20'sd1,8'd128);word(20'sd7,8'd128);
        reset_kernel();
        for(i=0;i<64;i=i+1)word(20'sd21,8'd128);
        repeat(7)@(negedge clk);
        if(out_valid)$fatal(1,"DENSE_PREMATURE_OUTPUT");
        reset_kernel();
        for(i=0;i<64;i=i+1)word(20'sd0,8'd127);
        while(!out_valid)@(negedge clk);
        repeat(4)begin
            @(negedge clk);
            if(!out_valid || out_index!=0 || out_residual!=0 || out_pixel!=127)$fatal(1,"STALLED_OUTPUT_UNSTABLE");
        end
        reset_kernel();
        $display("RESET_ABORT_PASS partial_load=1 partial_compute=1 stalled_output=1");
        @(negedge clk);#1;enabled=1;
    end
    always @(negedge clk) if(enabled)begin
        lfsr={lfsr[30:0],lfsr[31]^lfsr[21]^lfsr[1]^lfsr[0]};
        in_valid=sent<RUN_SAMPLES && (stall_mode==0 || pending || lfsr[1:0]!=0);
        if(sent<RUN_SAMPLES)begin in_coeff=coeff_data[sent];in_prediction=prediction_data[sent];end
        else begin in_coeff=0;in_prediction=0;end
        out_ready=stall_mode==0 || lfsr[3:2]!=0;
    end
    always @(posedge clk) if(enabled)begin
        cycle=cycle+1;
        if($isunknown(handshake_check))$fatal(1,"UNKNOWN_HANDSHAKE valid=%b ready=%b rst=%b",out_valid,in_ready,rst);
        if(previous_stall && (!out_valid || {out_residual,out_pixel,out_index,out_last}!==held_output))$fatal(1,"BACKPRESSURE_CHANGED_OUTPUT");
        previous_stall=out_valid && !out_ready;
        held_output={out_residual,out_pixel,out_index,out_last};
        if(out_valid && $isunknown(output_check))$fatal(1,"UNKNOWN_VALID_OUTPUT");
        pending=in_valid && !in_ready;
        if(in_valid && in_ready)begin
            if(sent%64==0)start_cycle=cycle;
            sent=sent+1;
        end
        if(out_valid && !out_ready)stall_cycles=stall_cycles+1;
        if(out_valid && out_ready)begin
            if(received>=RUN_SAMPLES)$fatal(1,"EXTRA_OUTPUT");
            if(out_index!==6'(received%64) || out_last!==(received%64==63))$fatal(1,"OUTPUT_ORDER sample=%0d index=%0d",received,out_index);
            if(out_residual!==residual_data[received] || out_pixel!==pixel_data[received])
                $fatal(1,"PIXEL_MISMATCH sample=%0d residual=%0d expected=%0d pixel=%0d expectedpixel=%0d",received,out_residual,residual_data[received],out_pixel,pixel_data[received]);
            if(received%64==63)begin
                total_service_cycles=total_service_cycles+cycle-start_cycle+1;
                $display("BLOCK id=%0d kind=%0d cycles=%0d",received/64,kind_data[received/64],cycle-start_cycle+1);
            end
            received=received+1;
            if(received==RUN_SAMPLES)begin
                if(sent!=RUN_SAMPLES)$fatal(1,"MISSING_INPUT_COUNTS");
                $display("TEST_PASS blocks=%0d samples=%0d bypass=%0d stalls=%0d service_cycles=%0d elapsed_cycles=%0d output_stall_cycles=%0d",RUN_BLOCKS,RUN_SAMPLES,BYPASS,stall_mode,total_service_cycles,cycle,stall_cycles);
                $finish;
            end
        end
    end
    initial begin #1000000000;$fatal(1,"WATCHDOG_TIMEOUT sent=%0d received=%0d",sent,received);end
endmodule
