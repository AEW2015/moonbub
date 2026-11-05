module tb_math;
    logic clk=0;always #5 clk<=~clk;
    logic rst=1,abort_i=0;
    logic dq_in_valid=0,dq_in_ready,dq_chroma=0,dq_out_valid,dq_out_ready=0,dq_error;
    logic [31:0] dq_in_id=0,dq_out_id;
    logic [1:0] dq_scale=0;
    logic [1023:0] dq_coeff=0;
    logic [1279:0] dq_output;
    cu66_dequant dq(.clk,.rst,.abort_i,.in_valid(dq_in_valid),.in_ready(dq_in_ready),
        .in_id(dq_in_id),.in_coefficients(dq_coeff),.in_chroma(dq_chroma),.in_scale_code(dq_scale),
        .out_valid(dq_out_valid),.out_ready(dq_out_ready),.out_id(dq_out_id),.out_dequantized(dq_output),.out_error(dq_error));
    logic rc_in_valid=0,rc_in_ready,rc_key=0,rc_hidden=0,rc_ref_valid=0,rc_ref_ready,rc_out_valid,rc_out_ready=0,rc_error;
    logic [31:0] rc_in_id=0,rc_ref_id=0,rc_out_id;
    logic [1535:0] rc_residual=0;
    logic [511:0] rc_reference=0,rc_output;
    cu66_reconstruct_tile rc(.clk,.rst,.abort_i,.in_valid(rc_in_valid),.in_ready(rc_in_ready),
        .in_id(rc_in_id),.in_key(rc_key),.in_hidden(rc_hidden),.in_residual(rc_residual),
        .ref_valid(rc_ref_valid),.ref_ready(rc_ref_ready),.ref_tile_id(rc_ref_id),.ref_pixels(rc_reference),
        .out_valid(rc_out_valid),.out_ready(rc_out_ready),.out_id(rc_out_id),.out_pixels(rc_output),.out_error(rc_error));
    integer f,status,id,kind,scale,err,key,hidden,rid,waits;
    integer dq_checked=0,rc_checked=0;
    logic [1023:0] coeff;
    logic [1279:0] expected_dq;
    logic [1535:0] residual;
    logic [511:0] reference_pixels,expected_rc;
    string directory;
    task automatic tick;begin @(posedge clk);#1;end endtask
    initial begin
        if(!$value$plusargs("FIXTURES=%s",directory))$fatal(1,"FIXTURES required");
        repeat(3)tick();@(negedge clk);rst=0;
        f=$fopen({directory,"/dequant.hex"},"r");if(f==0)$fatal(1,"dequant fixture missing");
        while(!$feof(f))begin
            status=$fscanf(f,"%d %d %d %h %h %d\n",id,kind,scale,coeff,expected_dq,err);
            if(status!=6||kind<0||kind>1||scale<0||scale>3||err<0||err>1)$fatal(1,"dequant parse/domain");
            @(negedge clk);while(!dq_in_ready)@(negedge clk);
            dq_in_id=32'(id);dq_chroma=1'(kind);dq_scale=2'(scale);dq_coeff=coeff;dq_in_valid=1;
            tick();@(negedge clk);dq_in_valid=0;
            while(!dq_out_valid)tick();
            if(dq_out_id!=32'(id)||dq_error!=1'(err)||dq_output!==expected_dq)$fatal(1,"dequant mismatch id=%0d",id);
            waits=id%7;
            repeat(waits)begin tick();if(!dq_out_valid||dq_out_id!=32'(id)||dq_error!=1'(err)||dq_output!==expected_dq)$fatal(1,"dequant stall");end
            @(negedge clk);dq_out_ready=1;tick();@(negedge clk);dq_out_ready=0;dq_checked=dq_checked+1;
        end
        $fclose(f);
        f=$fopen({directory,"/reconstruct.hex"},"r");if(f==0)$fatal(1,"reconstruct fixture missing");
        while(!$feof(f))begin
            status=$fscanf(f,"%d %d %d %d %h %h %h %d\n",id,key,hidden,rid,residual,reference_pixels,expected_rc,err);
            if(status!=8||key<0||key>1||hidden<0||hidden>1||err<0||err>1)$fatal(1,"reconstruct parse/domain");
            @(negedge clk);rc_in_id=32'(id);rc_key=1'(key);rc_hidden=1'(hidden);rc_ref_id=32'(rid);
            rc_residual=residual;rc_reference=reference_pixels;rc_in_valid=1;rc_ref_valid=0;
            if(key==0&&hidden==0)begin
                repeat(id%4+1)begin tick();if(rc_in_ready||rc_out_valid)$fatal(1,"reference latency violated");end
                @(negedge clk);rc_ref_valid=1;
            end
            #1;
            if((key!=0||hidden!=0)&&rc_ref_ready)$fatal(1,"unused reference consumed");
            if(key==0&&hidden==0&&!rc_ref_ready)$fatal(1,"required reference not ready");
            tick();
            if(!rc_out_valid||rc_out_id!=32'(id)||rc_error!=1'(err)||rc_output!==expected_rc)$fatal(1,"reconstruct mismatch id=%0d",id);
            @(negedge clk);rc_in_valid=0;rc_ref_valid=0;
            repeat(id%5)begin tick();if(!rc_out_valid||rc_output!==expected_rc||rc_error!=1'(err))$fatal(1,"reconstruct stall");end
            @(negedge clk);rc_out_ready=1;tick();@(negedge clk);rc_out_ready=0;rc_checked=rc_checked+1;
        end
        $fclose(f);
        if(dq_checked!=1536||rc_checked!=1536)$fatal(1,"incomplete fixture");
        $display("CU66_MATH_TEST_PASS dequant=%0d reconstruct=%0d",dq_checked,rc_checked);$finish;
    end
    initial begin #10000000;$fatal(1,"math watchdog");end
endmodule
