module tb_bank_control;
    logic clk=0;
    always #5 clk<=~clk;
    logic rst=0,abort_i=0,drain_done=0;
    logic begin_valid=0,begin_ready;
    logic [31:0] begin_id=32'hffffffff,begin_reference_id=32'hffffffff;
    logic begin_key=0,commit_valid=0,commit_ready,commit_ok=0;
    logic vblank=0,scanout_drained=0;
    logic active,aborting;
    logic [1:0] write_bank,read_bank,ref_bank,front_bank,pending_bank;
    logic read_bank_valid,ref_valid,front_valid,pending_valid;
    logic [31:0] ref_id,front_id,pending_id;
    logic begin_accepted,frame_committed,frame_presented,aborted,error;
    logic [7:0] error_code;
    logic [31:0] accepted_count,presented_count;

    logic [0:0] x_rst,x_abort_i,x_drain_done,x_begin_valid,x_begin_key;
    logic [31:0] x_begin_id,x_begin_reference_id;
    logic [0:0] x_commit_valid,x_commit_ok,x_vblank,x_scanout_drained;
    logic x_pre_begin_ready,x_pre_commit_ready;
    logic [0:0] x_active,x_aborting,x_read_bank_valid,x_ref_valid;
    logic [0:0] x_front_valid,x_pending_valid;
    logic [1:0] x_write_bank,x_read_bank,x_ref_bank,x_front_bank,x_pending_bank;
    logic [31:0] x_ref_id,x_front_id,x_pending_id;
    logic [0:0] x_begin_accepted,x_frame_committed,x_frame_presented,x_aborted,x_error;
    logic [7:0] x_error_code;
    logic [31:0] x_accepted_count,x_presented_count;

    integer fd,status,cycle_count=0,begin_count=0,commit_count=0;
    integer present_count=0,abort_count=0,error_count=0;
    string vectors;

    cu66_frame_bank_control dut(.*);

    task automatic read_vector;
        begin
            status=$fscanf(fd,
                "%d %d %d %d %h %d %h %d %d %d %d %d %d %d %d %d %d %h %d %d %h %d %d %h %d %d %h %d %d %d %d %d %d %d %d\n",
                x_rst,x_abort_i,x_drain_done,x_begin_valid,x_begin_id,x_begin_key,
                x_begin_reference_id,x_commit_valid,x_commit_ok,x_vblank,x_scanout_drained,
                x_pre_begin_ready,x_pre_commit_ready,x_active,x_aborting,x_write_bank,
                x_read_bank_valid,x_read_bank,x_ref_valid,x_ref_bank,x_ref_id,
                x_front_valid,x_front_bank,x_front_id,x_pending_valid,x_pending_bank,
                x_pending_id,x_begin_accepted,x_frame_committed,x_frame_presented,
                x_aborted,x_error,x_error_code,x_accepted_count,x_presented_count);
        end
    endtask

    initial begin
        if(!$value$plusargs("VECTORS=%s",vectors))
            vectors="fpga/experiments/cu66-v69/banks/vectors.txt";
        fd=$fopen(vectors,"r");
        if(fd==0)$fatal(1,"unable to open vectors: %s",vectors);
        repeat(2)@(posedge clk);
        read_vector();
        while(status==35)begin

            @(negedge clk);
            rst=x_rst;abort_i=x_abort_i;drain_done=x_drain_done;
            begin_valid=x_begin_valid;begin_id=x_begin_id;begin_key=x_begin_key;
            begin_reference_id=x_begin_reference_id;
            commit_valid=x_commit_valid;commit_ok=x_commit_ok;
            vblank=x_vblank;scanout_drained=x_scanout_drained;
            #1;
            if(begin_ready!==x_pre_begin_ready||commit_ready!==x_pre_commit_ready)
                $fatal(1,"ready mismatch cycle=%0d begin=%0b/%0b commit=%0b/%0b",
                    cycle_count,begin_ready,x_pre_begin_ready,commit_ready,x_pre_commit_ready);
            @(posedge clk);#1;
            if(active!==x_active||aborting!==x_aborting||write_bank!==x_write_bank||
               read_bank_valid!==x_read_bank_valid||read_bank!==x_read_bank||
               ref_valid!==x_ref_valid||ref_bank!==x_ref_bank||ref_id!==x_ref_id||
               front_valid!==x_front_valid||front_bank!==x_front_bank||front_id!==x_front_id||
               pending_valid!==x_pending_valid||pending_bank!==x_pending_bank||pending_id!==x_pending_id||
               begin_accepted!==x_begin_accepted||frame_committed!==x_frame_committed||
               frame_presented!==x_frame_presented||aborted!==x_aborted||error!==x_error||
               error_code!==x_error_code||accepted_count!==x_accepted_count||
               presented_count!==x_presented_count)
                $fatal(1,"state mismatch cycle=%0d active=%b/%b aborting=%b/%b wb=%0d/%0d rb=%b:%0d/%b:%0d ref=%b:%0d:%0d/%b:%0d:%0d front=%b:%0d:%0d/%b:%0d:%0d pending=%b:%0d:%0d/%b:%0d:%0d pulses=%b%b%b%b%b:%0d/%b%b%b%b%b:%0d counts=%0d:%0d/%0d:%0d",
                    cycle_count,active,x_active,aborting,x_aborting,write_bank,x_write_bank,
                    read_bank_valid,read_bank, x_read_bank_valid,x_read_bank,
                    ref_valid,ref_bank,ref_id,x_ref_valid,x_ref_bank,x_ref_id,
                    front_valid,front_bank,front_id,x_front_valid,x_front_bank,x_front_id,
                    pending_valid,pending_bank,pending_id,x_pending_valid,x_pending_bank,x_pending_id,
                    begin_accepted,frame_committed,frame_presented,aborted,error,error_code,
                    x_begin_accepted,x_frame_committed,x_frame_presented,x_aborted,x_error,x_error_code,
                    accepted_count,presented_count,x_accepted_count,x_presented_count);
            if(begin_accepted)begin_count=begin_count+1;
            if(frame_committed)commit_count=commit_count+1;
            if(frame_presented)present_count=present_count+1;
            if(aborted)abort_count=abort_count+1;
            if(error)error_count=error_count+1;
            cycle_count=cycle_count+1;
            read_vector();
        end
        if(status>0)$fatal(1,"vector parse mismatch cycle=%0d fields=%0d",cycle_count,status);
        $fclose(fd);
        if(cycle_count<400||begin_count<4||commit_count<3||present_count<2||
           abort_count<2||error_count<5)
            $fatal(1,"coverage short cycles=%0d begins=%0d commits=%0d presents=%0d aborts=%0d errors=%0d",
                cycle_count,begin_count,commit_count,present_count,abort_count,error_count);
        $display("CU66_BANK_CONTROL_PASS cycles=%0d begins=%0d commits=%0d presents=%0d aborts=%0d errors=%0d",
            cycle_count,begin_count,commit_count,present_count,abort_count,error_count);
        $finish;
    end

    initial begin
        #1000000;
        $fatal(1,"bank controller vector watchdog");
    end
endmodule
