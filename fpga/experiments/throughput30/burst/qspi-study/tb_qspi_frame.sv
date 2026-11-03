`timescale 1ns/1ps
module tb_qspi_frame;
    reg clk200=0,clk100=0;always #2.5 clk200=~clk200;always #5 clk100=~clk100;
    reg reset_n=0,cs=1,sck=0;reg[3:0]host_dq=0;wire[3:0]dq,oe;
    reg[11:0]buttons=0;wire[3:0]control;wire[11:0]force_buttons;
    wire[23:0]ox,oy;wire ovwr;wire[17:0]ovaddr;wire[15:0]ovdata;
    wire spiwrite,spiread;wire[11:0]spiaddr;wire[31:0]spiwdata,spirddata;
    wire corewrite;wire[11:0]coreaddr;wire[31:0]corewdata;reg[31:0]corerdata;
    wire overflow;reg[31:0]metadata=0,total=0,fifo_count=0,sum=0;integer writes=0;
    reg clock_run=1;
    moonshine_qspi_endpoint endpoint(.clk200(clk200),.rst_n(reset_n),.qspi_sck(sck),.qspi_cs_n(cs),
      .qspi_dq_i(host_dq),.dq_o(dq),.dq_oe(oe),.buttons_native(buttons),.vblank(1'b0),
      .irq_request(),.control(control),.force_buttons_native(force_buttons),.display_external(),.color_correct_enable(),
      .overlay_xctrl(ox),.overlay_yctrl(oy),.ov_wr(ovwr),.ov_addr(ovaddr),.ov_data(ovdata),
      .core_write(spiwrite),.core_read(spiread),.core_address(spiaddr),.core_wdata(spiwdata),.core_rdata(spirddata));
    moonshine_bus_cdc bridge(.spi_clk(clk200),.spi_reset(!reset_n),.spi_write(spiwrite),.spi_read(spiread),
      .spi_address(spiaddr),.spi_wdata(spiwdata),.spi_rdata(spirddata),.overflow(overflow),
      .core_clk(clk100),.core_reset(!reset_n),.core_write(corewrite),.core_address(coreaddr),.core_wdata(corewdata),.core_rdata(corerdata));
    always @*begin
        case(coreaddr)
          'h000:corerdata=32'h4d425631;'h014:corerdata=metadata;'h018:corerdata=total;
          'h00c:corerdata=32'd26159-fifo_count;'h028:corerdata=fifo_count;'h050:corerdata=sum;default:corerdata=0;
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
        begin header(8'h54,address,write_half_ps/1000.0);shift(value,32,4,write_half_ps/1000.0);end_transaction();end
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
    reg[31:0]readback,second_word;integer i,j,chunk,phase_ps=0,write_half_ps=12500;realtime transfer_start,transfer_end;
    initial begin
        if($value$plusargs("PHASE_PS=%d",phase_ps)) begin end
        if($value$plusargs("WRITE_HALF_PS=%d",write_half_ps)) begin end
        if(phase_ps<0 || phase_ps>=5000 || write_half_ps<5000 || write_half_ps>50000)$fatal(1,"invalid phase or write period");
        #(phase_ps/1000.0);
        #100;reset_n=1;#200;
        read32(32'he0000000,readback);if(readback!==32'h4d425631)$fatal(1,"core mailbox read%h",readback);
        write32(32'he0000014,32'h12345678);
        write32(32'he0000018,32'd1024);
        read32(32'he0000014,readback);if(readback!==32'h12345678)$fatal(1,"metadata order/mailbox%h",readback);
        read32(32'he0000018,readback);if(readback!==1024)$fatal(1,"back-to-back read stale%h",readback);
        read_two(32'he0000014,readback,second_word);
        if(readback!==32'h12345678 || second_word!==1024)$fatal(1,"auto-increment core snapshots stale%h %h",readback,second_word);
        // Simulate one frame-sized payload with actual firmware-like 1024-byte
        // chunks and a 16 MHz remaining-frame-length read before each chunk.
        transfer_start=$realtime;
        for(i=0;i<26159;i=i+chunk)begin
            read32(32'he000000c,readback);
            if(readback !== 26159-i)$fatal(1,"remaining length mismatch at %0d: %0d",i,readback);
            chunk=(26159-i>1024)?1024:26159-i;
            header(8'h40,32'he0000100,write_half_ps/1000.0);
            for(j=0;j<chunk;j=j+1)shift((i+j)&255,8,4,write_half_ps/1000.0);
            end_transaction();
        end
        read32(32'he0000028,readback);transfer_end=$realtime;
        if(readback!==26159 || fifo_count!==26159 || overflow)$fatal(1,"frame payload lost at CDC");
        if(writes!=26161)$fatal(1,"wrong accepted write count %0d",writes);
        $display("QSPI_FRAME_PASS bytes=26159 chunks=26 write_half_ps=%0d clock_read_mhz=16 elapsed_ns=%0.3f overflow=%0d phase_ps=%0d",write_half_ps,transfer_end-transfer_start,overflow,phase_ps);$finish;
    end
    initial begin #5000000;$fatal(1,"watchdog");end
endmodule
