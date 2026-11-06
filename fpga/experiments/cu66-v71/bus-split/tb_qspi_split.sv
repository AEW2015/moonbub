`timescale 1ns/1ps
module tb_qspi_split #(parameter realtime START_PHASE_NS=0.0);
    reg clk200=0,clk100=0;always #2.5 clk200=~clk200;always #5 clk100=~clk100;
    reg reset_n=0,cs=1,sck=0;reg[3:0]host_dq=0;wire[3:0]dq,oe;
    reg[11:0]buttons=0;wire[3:0]control;wire[11:0]force_buttons;
    wire[23:0]ox,oy;wire ovwr;wire[17:0]ovaddr;wire[15:0]ovdata;
    wire spiwrite,spiread;wire[11:0]spiaddr;wire[31:0]spiwdata,spirddata;
    wire corewrite;wire[11:0]coreaddr,corereadaddr;wire[31:0]corewdata;reg[31:0]corerdata;
    wire overflow;reg[31:0]metadata=0,total=0,fifo_count=0,sum=0;integer writes=0;
    reg clock_run=1;
    moonshine_qspi_endpoint endpoint(.clk200(clk200),.rst_n(reset_n),.qspi_sck(sck),.qspi_cs_n(cs),
      .qspi_dq_i(host_dq),.dq_o(dq),.dq_oe(oe),.buttons_native(buttons),.vblank(1'b0),
      .irq_request(),.control(control),.force_buttons_native(force_buttons),.display_external(),.color_correct_enable(),
      .overlay_xctrl(ox),.overlay_yctrl(oy),.ov_wr(ovwr),.ov_addr(ovaddr),.ov_data(ovdata),
      .core_write(spiwrite),.core_read(spiread),.core_address(spiaddr),.core_wdata(spiwdata),.core_rdata(spirddata));
    cu71_bus_cdc_split bridge(.spi_clk(clk200),.spi_reset(!reset_n),.spi_write(spiwrite),.spi_read(spiread),
      .spi_address(spiaddr),.spi_wdata(spiwdata),.spi_rdata(spirddata),.overflow(overflow),
      .core_clk(clk100),.core_reset(!reset_n),.core_write(corewrite),.core_address(coreaddr),.core_read_address(corereadaddr),.core_wdata(corewdata),.core_rdata(corerdata));
    always @*begin
        case(corereadaddr)
          'h000:corerdata=32'h4d425631;'h014:corerdata=metadata;'h018:corerdata=total;
          'h028:corerdata=fifo_count;'h050:corerdata=sum;default:corerdata=0;
        endcase
    end
    always @(posedge clk100)begin
        if(!reset_n)begin metadata<=0;total<=0;fifo_count<=0;sum<=0;writes<=0;end
        else if(corewrite)begin
            writes<=writes+1;
            case(coreaddr)
              'h014:metadata<=corewdata;'h018:total<=corewdata;
              'h100:begin
                if(corewdata!=={24'b0,fifo_count[7:0]})$fatal(1,"FIFO order error %0d data%h",fifo_count,corewdata);
                fifo_count<=fifo_count+1;sum<=sum+corewdata;
              end
              default:begin end
            endcase
        end
    end
wire old_write,old_overflow;wire[11:0]old_address;wire[31:0]old_wdata,old_rdata,old_spi_rdata;reg[31:0]old_core_rdata;
 moonshine_bus_cdc old_bridge(.spi_clk(clk200),.spi_reset(!reset_n),.spi_write(spiwrite),.spi_read(spiread),.spi_address(spiaddr),.spi_wdata(spiwdata),.spi_rdata(old_spi_rdata),.overflow(old_overflow),.overflow_gray(),.core_clk(clk100),.core_reset(!reset_n),.core_write(old_write),.core_address(old_address),.core_wdata(old_wdata),.core_rdata(old_core_rdata));
 always @*begin case(old_address)
 'h000:old_core_rdata=32'h4d425631;'h014:old_core_rdata=metadata;'h018:old_core_rdata=total;'h028:old_core_rdata=fifo_count;'h050:old_core_rdata=sum;default:old_core_rdata=0;endcase end
 always @(negedge clk200)if(reset_n && {spirddata,overflow}!=={old_spi_rdata,old_overflow})$fatal(1,"original QSPI response differs from split");
 always @(negedge clk100)if(reset_n)begin
 if(corewrite!==old_write)$fatal(1,"original write pulse differs");
 if(corewrite && {coreaddr,corewdata}!=={old_address,old_wdata})$fatal(1,"original write data/address differs");end

    integer overlays=0;
    always @(posedge clk200)if(ovwr)begin
        if(ovaddr!==18'd10 || ovdata!==16'habcd)$fatal(1,"overlay byte swap framing error");
        overlays=overlays+1;
    end
    task begin_transaction;begin sck=0;host_dq=0;cs=0;#100;end endtask
    task end_transaction;begin sck=0;cs=1;#1;if(oe!==0)$fatal(1,"CS did not release bus");#99;end endtask
    task shift(input[31:0]value,input integer bits,input integer lanes,input realtime half_period);
        integer n;begin
            for(n=bits-lanes;n>=0;n=n-lanes)begin
                host_dq=(value>>n)&((1<<lanes)-1);#(half_period);sck=1;#(half_period);sck=0;
            end
        end
    endtask
    task header(input[7:0]command,input[31:0]address,input realtime half_period);
        begin begin_transaction();shift(command,8,1,half_period);shift(address,32,4,half_period);end
    endtask
    task write32(input[31:0]address,input[31:0]value);
        begin header(8'h54,address,12.5);shift(value,32,4,12.5);end_transaction();end
    endtask
    task read32(input[31:0]address,output[31:0]value);
        integer n;begin
            header(8'h55,address,31.25);shift(0,64,4,31.25);value=0;
            for(n=0;n<8;n=n+1)begin
                #31.25;sck=1;value=(value<<4)|dq;#31.25;sck=0;
            end
            end_transaction();
        end
    endtask
    task read_two(input[31:0]address,output[31:0]first,output[31:0]second);
        integer n;begin
            header(8'h55,address,31.25);shift(0,64,4,31.25);first=0;second=0;
            for(n=0;n<16;n=n+1)begin
                #31.25;sck=1;
                if(n<8)first=(first<<4)|dq;else second=(second<<4)|dq;
                #31.25;sck=0;
            end
            end_transaction();
        end
    endtask
    reg[31:0]readback,second_word;integer i;
    initial begin
        #(START_PHASE_NS);
        #100;reset_n=1;#200;
        read32(32'he0000000,readback);if(readback!==32'h4d425631)$fatal(1,"core mailbox read%h",readback);
        write32(32'he0000014,32'h12345678);
        write32(32'he0000018,32'd1024);
        read32(32'he0000014,readback);if(readback!==32'h12345678)$fatal(1,"metadata order/mailbox%h",readback);
        read32(32'he0000018,readback);if(readback!==1024)$fatal(1,"back-to-back read stale%h",readback);
        read_two(32'he0000014,readback,second_word);
        if(readback!==32'h12345678 || second_word!==1024)$fatal(1,"auto-increment core snapshots stale%h %h",readback,second_word);
        header(8'h40,32'he0000100,12.5);
        for(i=0;i<1024;i=i+1)shift(i&255,8,4,12.5);
        end_transaction();
        read32(32'he0000028,readback);if(readback!==1024)$fatal(1,"FIFO credit snapshot%h",readback);
        read32(32'he0000050,readback);if(readback!==130560)$fatal(1,"FIFO checksum%h",readback);
        if(overflow)$fatal(1,"CDC overflow at supported write speed");
        // The framework window is independently decoded and never core aliased.
        write32(32'h01000100,32'h0000ff00);
        read32(32'h01000100,readback);if(readback!==32'h0000ff00)$fatal(1,"framework register changed");
        read32(32'h10000000,readback);if(readback!==0)$fatal(1,"unknown read aliased to core");
        // Native GPIO order and the firmware-visible host mask are reversed
        // exactly once, preserving every physical/forced controller button.
        for(i=0;i<12;i=i+1)begin
            buttons=12'b1<<i;
            read32(32'h0100001c,readback);
            if(readback!==(32'b1<<(11-i)))$fatal(1,"physical button map bit%0d got%h",i,readback);
            write32(32'h01000004,32'b1<<(11-i));
            if(force_buttons!==(12'b1<<i))$fatal(1,"forced button map bit%0d",i);
            write32(32'h01000010,2);
            read32(32'h01000010,readback);
            if(readback&2)$fatal(1,"stable button W1C did not clear IRQ");
        end
        buttons=0;write32(32'h01000004,0);
        header(8'h5a,32'h0300000a,12.5);shift(32'hcdab,16,4,12.5);end_transaction();
        if(overlays!=1)$fatal(1,"missing overlay write");
        // Mid-command CS cancellation must not create an extra accepted write.
        header(8'h54,32'he0000014,12.5);shift(16'hffff,16,4,12.5);end_transaction();
        read32(32'he0000014,readback);if(readback!==32'h12345678)$fatal(1,"partial write committed");
        if(writes!=1026)$fatal(1,"wrong core accepted write count%0d",writes);
        // Reset during a transaction cancels it in both domains.
        header(8'h54,32'he0000014,12.5);shift(16'haaaa,16,4,12.5);reset_n=0;#100;cs=1;sck=0;#100;reset_n=1;#200;
        read32(32'he0000014,readback);if(readback!==0)$fatal(1,"reset did not cancel");
        read32(32'he0000000,readback);if(readback!==32'h4d425631)$fatal(1,"recovery read failed");
        $display("QSPI_CDC_PASS write40MHz read16MHz fifo1024 checksum130560 metadata autoinc2words framework button12_IRQ_W1C overlay CS/reset cancellation");$finish;
    end
    initial begin #1000000;$fatal(1,"watchdog");end
endmodule
