module tb_expand_tiles;
    logic clk=0;
    always #5 clk<=~clk;
    logic rst=0,abort_i=0,cfg_valid=0,cfg_ready;
    logic [1:0] cfg_plane=0;
    logic [2:0] cfg_dispatch=0;
    logic [16:0] cfg_blocks=0;
    logic in_valid=0,in_ready,out_valid,out_ready=0;
    logic [1023:0] in_coefficients=0,out_coefficients;
    logic [16:0] in_index=0,out_index;
    logic in_last=0,out_hidden,out_last;
    logic [6:0] out_x;
    logic [5:0] out_y;
    logic busy,done,error;
    logic [7:0] error_code;
    logic [7:0] mask_y[0:5399];
    logic [7:0] mask_cb[0:1349],mask_cr[0:1349];
    logic [31:0] rng=32'd69004701,seed=32'd69004701;
    integer plane,width,total,encoded_total;
    integer expected_blocks=0,input_blocks=0,stalls=0,stream_count=0;
    string mask_y_file,mask_cb_file,mask_cr_file;
    logic random_stalls=1;

    cu66_expand_tiles dut(.*);

    function automatic [31:0] random_next(input logic [31:0] a);
        logic [31:0] v;
        begin v=a^(a<<13);v=v^(v>>17);random_next=v^(v<<5);end
    endfunction

    function automatic [1023:0] make_tile(input integer p,input integer block_id,
                                          input logic nonzero);
        integer k,value;
        begin
            make_tile='0;
            if(nonzero)for(k=0;k<64;k=k+1)begin
                value=((block_id*13+p*71+k*7+1)&32'h00007fff);
                if(value==0)value=1;
                make_tile[k*16 +:16]=16'(value);
            end
        end
    endfunction

    function automatic logic hidden_at(input integer p,input logic [12:0] i);
        begin
            if(p==0)hidden_at=mask_y[i]!=0;
            else if(p==1)hidden_at=mask_cb[i[10:0]]!=0;
            else hidden_at=mask_cr[i[10:0]]!=0;
        end
    endfunction

    task automatic reset_dut;
        begin
            @(negedge clk);rst=1;abort_i=0;cfg_valid=0;in_valid=0;out_ready=0;
            @(posedge clk);#1;
            if(busy||out_valid||done||error)$fatal(1,"reset did not flush expander");
            @(negedge clk);rst=0;#1;
            if(!cfg_ready)$fatal(1,"reset did not restore cfg_ready");
        end
    endtask

    task automatic configure(input integer p,input integer dispatch,input logic [16:0] blocks);
        begin
            @(negedge clk);cfg_plane=2'(p);cfg_dispatch=3'(dispatch);
            cfg_blocks=17'(blocks);cfg_valid=1;
            #1;if(!cfg_ready)$fatal(1,"cfg not ready p=%0d d=%0d",p,dispatch);
            @(posedge clk);#1;@(negedge clk);cfg_valid=0;
        end
    endtask

    task automatic send_tile(input integer p,input integer block_id,
                             input logic [16:0] encoded_id,input logic last,
                             input logic nonzero);
        begin
            @(negedge clk);
            while(!in_ready)@(negedge clk);
            in_coefficients=make_tile(p,block_id,nonzero);
            in_index=17'(encoded_id);in_last=last;in_valid=1;
            @(posedge clk);#1;input_blocks=input_blocks+1;
            @(negedge clk);in_valid=0;
        end
    endtask

    task automatic check_output(input integer p,input integer block_id,
                               input integer row_width,input logic hidden,
                               input logic last,input logic [1023:0] coeff);
        logic [1023:0] held_coeff;
        logic [16:0] held_index;
        logic [6:0] held_x;
        logic [5:0] held_y;
        logic held_hidden,held_last;
        integer nstall,n;
        begin
            while(!out_valid)begin @(posedge clk);#1;end
            if(out_index!==17'(block_id)||out_x!==7'(block_id%row_width)||
               out_y!==6'(block_id/row_width)||out_hidden!==hidden||out_last!==last||
               out_coefficients!==coeff)
                $fatal(1,"expand mismatch p=%0d block=%0d got idx=%0d xy=%0d,%0d hidden=%b last=%b",
                    p,block_id,out_index,out_x,out_y,out_hidden,out_last);
            held_coeff=out_coefficients;held_index=out_index;held_x=out_x;held_y=out_y;
            held_hidden=out_hidden;held_last=out_last;
            rng=random_next(rng);nstall=random_stalls?int'(rng%5):0;
            for(n=0;n<nstall;n=n+1)begin
                @(negedge clk);out_ready=0;
                @(posedge clk);#1;stalls=stalls+1;
                if(!out_valid||out_coefficients!==held_coeff||out_index!==held_index||
                   out_x!==held_x||out_y!==held_y||out_hidden!==held_hidden||out_last!==held_last)
                    $fatal(1,"unstable stalled output p=%0d block=%0d",p,block_id);
            end
            @(negedge clk);out_ready=1;
            @(posedge clk);#1;
            if(last)begin
                if(!done||busy||out_valid)$fatal(1,"missing stream completion p=%0d",p);
            end else if(done)$fatal(1,"early done p=%0d block=%0d",p,block_id);
            @(negedge clk);out_ready=0;
            expected_blocks=expected_blocks+1;
        end
    endtask

    task automatic run_stream(input integer p,input integer dispatch,
                              input integer full_count,input integer compact_count,
                              input integer row_width);
        integer i,enc;
        logic hidden;
        logic [1023:0] coeff;
        begin
            configure(p,dispatch,17'(dispatch==5?full_count:compact_count));
            enc=0;
            for(i=0;i<full_count;i=i+1)begin
                hidden=hidden_at(p,13'(i));
                if(dispatch==5||!hidden)begin
                    coeff=make_tile(p,i,!hidden);
                    send_tile(p,i,17'(enc),enc==(dispatch==5?full_count:compact_count)-1,!hidden);
                    enc=enc+1;
                end else coeff='0;
                check_output(p,i,row_width,hidden,i==full_count-1,coeff);
            end
            if(enc!=(dispatch==5?full_count:compact_count))
                $fatal(1,"encoded count mismatch p=%0d d=%0d got=%0d",p,dispatch,enc);
            if(done!==1||error||busy)$fatal(1,"stream terminal status p=%0d d=%0d",p,dispatch);
            stream_count=stream_count+1;
        end
    endtask

    task automatic check_error(input integer expected_code);
        begin
            @(posedge clk);#1;
            if(!error||error_code!=8'(expected_code)||busy||out_valid)
                $fatal(1,"expected error %0d got valid=%b code=%0d busy=%b",expected_code,error,error_code,busy);
        end
    endtask

    integer i,first_hidden;
    initial begin
        if($value$plusargs("SEED=%d",seed))rng=seed;
        if(!$value$plusargs("MASK_Y=%s",mask_y_file))mask_y_file="fpga/experiments/cu66-v69/inverse/expand/mask_y.hex";
        if(!$value$plusargs("MASK_CB=%s",mask_cb_file))mask_cb_file="fpga/experiments/cu66-v69/inverse/expand/mask_cb.hex";
        if(!$value$plusargs("MASK_CR=%s",mask_cr_file))mask_cr_file="fpga/experiments/cu66-v69/inverse/expand/mask_cr.hex";
        $readmemh(mask_y_file,mask_y);$readmemh(mask_cb_file,mask_cb);$readmemh(mask_cr_file,mask_cr);
        reset_dut();
        for(plane=0;plane<3;plane=plane+1)begin
            width=plane==0?90:45;total=plane==0?5400:1350;encoded_total=plane==0?5144:1331;
            run_stream(plane,5,total,encoded_total,width);
            run_stream(plane,6,total,encoded_total,width);
        end

        // Bad plane geometry and full-block count are rejected at configure.
        reset_dut();configure(3,5,17'd5400);check_error(1);
        reset_dut();configure(0,5,17'd5399);check_error(1);
        // Wrong encoded index and incorrect last marker are transaction errors.
        reset_dut();configure(1,5,17'd1350);send_tile(1,0,17'd1,0,1);check_error(2);
        reset_dut();configure(1,5,17'd1350);send_tile(1,0,17'd0,1,1);check_error(2);
        // Find first hidden block from the archived mask, not a copied predicate.
        first_hidden=-1;
        for(i=0;i<5400;i=i+1)if(first_hidden<0&&mask_y[13'(i)]!=0)first_hidden=i;
        if(first_hidden<0)$fatal(1,"mask contains no hidden luma blocks");
        reset_dut();configure(0,5,17'd5400);
        random_stalls=0;
        for(i=0;i<first_hidden;i=i+1)begin
            send_tile(0,i,17'(i),i==5399,0);
            check_output(0,i,90,0,i==5399,1024'd0);
        end
        send_tile(0,first_hidden,17'(first_hidden),0,1);check_error(2);
        random_stalls=1;

        // Abort an accepted output held under backpressure.
        reset_dut();configure(2,5,17'd1350);send_tile(2,0,17'd0,0,1);
        while(!out_valid)begin @(posedge clk);#1;end
        repeat(3)begin
            @(negedge clk);out_ready=0;
            @(posedge clk);#1;
            if(!out_valid||out_index!=0||out_coefficients!==make_tile(2,0,1))
                $fatal(1,"abort setup output was not stable");
        end
        @(negedge clk);abort_i=1;@(posedge clk);#1;
        if(busy||out_valid||done||error)$fatal(1,"abort did not flush active output");
        @(negedge clk);abort_i=0;#1;if(!cfg_ready)$fatal(1,"abort did not restore cfg_ready");

        // Synchronous reset also discards a stalled visible tile.
        configure(2,5,17'd1350);send_tile(2,0,17'd0,0,1);
        while(!out_valid)begin @(posedge clk);#1;end
        @(negedge clk);out_ready=0;rst=1;@(posedge clk);#1;
        if(busy||out_valid||done||error)$fatal(1,"reset did not flush active output");
        @(negedge clk);rst=0;#1;if(!cfg_ready)$fatal(1,"reset did not restore cfg_ready");

        if(expected_blocks!=16200+first_hidden||stream_count!=6||stalls<100)
            $fatal(1,"coverage short outputs=%0d streams=%0d stalls=%0d",expected_blocks,stream_count,stalls);
        $display("CU66_EXPAND_TILES_PASS outputs=%0d streams=%0d inputs=%0d stalls=%0d seed=%0d first_hidden_y=%0d",
            expected_blocks,stream_count,input_blocks,stalls,seed,first_hidden);
        $finish;
    end
    initial begin #100000000;$fatal(1,"tile expand watchdog");end
endmodule
