module tb_idct;
    logic clk=0;
    always #5 clk<=~clk;
    logic rst=1,abort_frame=0,in_valid=0,in_ready,out_valid,out_ready=0;
    logic [31:0] in_id=0,out_id,active_cycles;
    logic [1279:0] in_tile=0;
    logic [1535:0] out_tile;
    logic out_error;
    cu66_idct8x8 dut(.*);
    integer fd,status,expected_id,expected_error;
    logic [1279:0] data;
    logic [1535:0] expected,held;
    logic [31:0] held_id,held_cycles;
    logic held_error;
    integer checked=0,cycle_count=0,aborted=0,reset_cancelled=0,stall_cancelled=0,max_work=0;
    integer stalls,delay_count;
    logic [31:0] rng=32'd69004501,seed=32'd69004501;
    string fixture;
    function automatic logic [31:0] random_next(input logic [31:0] a);
        logic [31:0] v;
        begin v=a^(a<<13);v=v^(v>>17);random_next=v^(v<<5);end
    endfunction
    task automatic tick;
        begin @(posedge clk);#1;cycle_count=cycle_count+1;end
    endtask
    task automatic send(input logic [1279:0] tile,input integer ident);
        begin
            @(negedge clk);
            while(!in_ready)@(negedge clk);
            in_tile=tile;in_id=32'(ident);in_valid=1;
            tick();
            @(negedge clk);in_valid=0;
        end
    endtask
    initial begin
        if(!$value$plusargs("FIXTURE=%s",fixture)) $fatal(1,"missing FIXTURE");
        if($value$plusargs("SEED=%d",seed)) rng=seed;
        fd=$fopen(fixture,"r");if(fd==0)$fatal(1,"fixture open failed");
        repeat(3)tick();@(negedge clk);rst=0;
        while(!$feof(fd))begin
            status=$fscanf(fd,"%d %h %h %d\n",expected_id,data,expected,expected_error);
            if(status!=4)$fatal(1,"fixture parse count=%0d",status);
            rng=random_next(rng);delay_count=int'(rng%4);
            repeat(delay_count)tick();
            // Abort complex work at different pipeline microsteps, then replay.
            if(expected_id%17==0 && expected_error==0)begin
                send(data,expected_id);repeat(expected_id%19+1)tick();
                @(negedge clk);abort_frame=1;tick();
                if(out_valid)$fatal(1,"aborted tile leaked");
                @(negedge clk);abort_frame=0;aborted=aborted+1;
            end
            // Exercise synchronous reset while registered work is in flight,
            // then replay this exact vector and compare the same golden.
            if(expected_id==138 && expected_error==0)begin
                send(data,expected_id);repeat(9)tick();
                if(out_valid)$fatal(1,"reset cancel setup reached output too early");
                @(negedge clk);rst=1;tick();
                if(out_valid)$fatal(1,"reset-cancelled output leaked");
                @(negedge clk);rst=0;#1;reset_cancelled=reset_cancelled+1;
                if(!in_ready)$fatal(1,"reset did not return DUT to input-ready");
            end
            send(data,expected_id);
            while(!out_valid)tick();
            if(out_id!=32'(expected_id)||out_error!=1'(expected_error)||out_tile!==expected)
                $fatal(1,"IDCT mismatch id=%0d outid=%0d error=%0b expectederr=%0d actual=%h expected=%h",expected_id,out_id,out_error,expected_error,out_tile,expected);
            if(int'(active_cycles)>max_work)max_work=int'(active_cycles);
            held=out_tile;held_id=out_id;held_error=out_error;held_cycles=active_cycles;
            rng=random_next(rng);stalls=int'(rng%6);
            repeat(stalls)begin
                tick();
                if(!out_valid||out_tile!==held||out_id!=held_id||out_error!=held_error||active_cycles!=held_cycles)
                    $fatal(1,"unstable stalled tile id=%0d",expected_id);
            end
            // Cancel a fully computed output while it is deliberately stalled;
            // replay immediately to prove the cancelled result was not retained.
            if(expected_id==139 && expected_error==0)begin
                @(negedge clk);abort_frame=1;tick();
                if(out_valid)$fatal(1,"stalled-output abort remained valid");
                @(negedge clk);abort_frame=0;#1;stall_cancelled=stall_cancelled+1;
                if(!in_ready)$fatal(1,"stalled-output abort did not return to idle");
                send(data,expected_id);
                while(!out_valid)tick();
                if(out_id!=32'(expected_id)||out_error!=1'(expected_error)||out_tile!==expected)
                    $fatal(1,"stalled-output replay mismatch id=%0d",expected_id);
                held=out_tile;held_id=out_id;held_error=out_error;held_cycles=active_cycles;
                repeat(2)begin
                    tick();
                    if(!out_valid||out_tile!==held||out_id!=held_id||out_error!=held_error||active_cycles!=held_cycles)
                        $fatal(1,"unstable replayed stalled output id=%0d",expected_id);
                end
            end
            @(negedge clk);out_ready=1;tick();@(negedge clk);out_ready=0;
            checked=checked+1;
        end
        $fclose(fd);
        if(checked!=3471||aborted==0||reset_cancelled!=1||stall_cancelled!=1)
            $fatal(1,"incomplete test checked=%0d aborts=%0d reset_cancelled=%0d stall_cancelled=%0d",checked,aborted,reset_cancelled,stall_cancelled);
        $display("CU66_IDCT_TEST_PASS tiles=%0d aborts=%0d reset_cancelled=%0d stall_cancelled=%0d cycles=%0d maximum_work_cycles=%0d seed=%0d",checked,aborted,reset_cancelled,stall_cancelled,cycle_count,max_work,seed);
        $finish;
    end
    initial begin #100000000;$fatal(1,"IDCT watchdog");end
endmodule
