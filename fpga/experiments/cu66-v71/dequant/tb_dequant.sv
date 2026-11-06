module tb_dequant;
    logic clk=0; always #5 clk=~clk;
    logic rst=1,abort_i=0,in_valid=0,out_ready=0;
    logic in_ready,out_valid,out_error,ref_ready,ref_valid,ref_error;
    logic [31:0] in_id=0,out_id,ref_id;
    logic [1023:0] in_coefficients=0;
    logic in_chroma=0;logic[1:0]in_scale_code=0;
    logic[1279:0]out_dequantized,ref_tile,expected,held;
    cu71_dequant_pipe dut(.*);
    cu66_dequant reference(.clk,.rst,.abort_i,.in_valid,.in_ready(ref_ready),.in_id,
        .in_coefficients,.in_chroma,.in_scale_code,.out_valid(ref_valid),.out_ready,
        .out_id(ref_id),.out_dequantized(ref_tile),.out_error(ref_error));
    integer fd,status,ident,chroma,scale,err,checked=0,cancelled=0,max_work=0,work;
    logic[1023:0]data;string fixture;
    task automatic tick;begin @(posedge clk);#1;end endtask
    task automatic send(input logic[1023:0] a,input integer id,input integer c,input integer s);
        begin
            @(negedge clk);while(!(in_ready&&ref_ready))@(negedge clk);
            in_coefficients=a;in_id=32'(id);in_chroma=1'(c);in_scale_code=2'(s);in_valid=1;
            tick();@(negedge clk);in_valid=0;
        end
    endtask
    task automatic verify(input logic[1279:0] golden,input integer id,input integer error_bit,input integer stall);
        begin
            work=0;
            while(!(out_valid&&ref_valid))begin
                // Input poison may not overwrite an outstanding transaction.
                in_valid=1;in_id=32'hbadf00d;in_coefficients=~data;in_scale_code=3;
                tick();work=work+1;if(work>20)$fatal(1,"timeout id=%0d",id);
                if(in_ready||ref_ready)$fatal(1,"busy accepted input");
            end
            in_valid=0;
            if(work>max_work)max_work=work;
            if(out_id!==32'(id)||out_error!==1'(error_bit)||out_dequantized!==golden)
                $fatal(1,"golden mismatch id=%0d goterr=%0b",id,out_error);
            if(out_id!==ref_id||out_error!==ref_error||out_dequantized!==ref_tile)
                $fatal(1,"parent mismatch id=%0d",id);
            held=out_dequantized;
            repeat(stall)begin tick();if(!out_valid||out_dequantized!==held||out_id!==32'(id)||out_error!==1'(error_bit))$fatal(1,"stall changed result");end
            @(negedge clk);out_ready=1;tick();
            if(out_valid||ref_valid)$fatal(1,"consume did not clear valid");
            @(negedge clk);out_ready=0;checked=checked+1;
        end
    endtask
    initial begin
        if(!$value$plusargs("FIXTURE=%s",fixture))$fatal(1,"missing FIXTURE");
        fd=$fopen(fixture,"r");if(!fd)$fatal(1,"open fixture");
        repeat(3)tick();@(negedge clk);rst=0;
        while(!$feof(fd))begin
            status=$fscanf(fd,"%d %d %d %h %h %d\n",ident,chroma,scale,data,expected,err);
            if(status!=6)$fatal(1,"bad fixture line");
            send(data,ident,chroma,scale);verify(expected,ident,err,(ident%31==0)?257:ident%7);
        end
        $fclose(fd);
        // Cancel every nonzero pipeline microstep and held-output state with
        // both reset and abort, then replay a known full golden transaction.
        data=0;data[15:0]=16'sd2048;expected=0;expected[19:0]=20'sd69632;
        for(integer kind=0;kind<2;kind=kind+1)begin
            for(integer delay_count=0;delay_count<13;delay_count=delay_count+1)begin
                send(data,32'hffffffff,1,2);repeat(delay_count)tick();
                @(negedge clk);if(kind==0)rst=1;else abort_i=1;#1;
                if(in_ready||out_valid||ref_ready||ref_valid)$fatal(1,"cancel immediate gating");
                tick();if(out_id!==0||out_error!==0||out_dequantized!==0||ref_tile!==0)$fatal(1,"cancel clear");
                @(negedge clk);rst=0;abort_i=0;in_valid=0;#1;
                if(!in_ready||!ref_ready||out_valid||ref_valid)$fatal(1,"cancel ready");
                repeat(15)tick();if(out_valid||ref_valid)$fatal(1,"phantom cancelled output");
                send(data,32'hffffffff,1,2);verify(expected,32'hffffffff,0,13);cancelled=cancelled+1;
            end
        end
        $display("PASS checked=%0d reset_abort_points=%0d max_work=%0d",checked,cancelled,max_work);$finish;
    end
    initial begin #100000000;$fatal(1,"watchdog");end
endmodule
