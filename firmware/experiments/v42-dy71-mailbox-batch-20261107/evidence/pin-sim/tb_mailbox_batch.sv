`timescale 1ns/1ps
module tb_mailbox_batch #(parameter realtime START_PHASE_NS=0.0, parameter realtime HALF=31.25);
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
    reg[31:0]fields[0:11];reg[31:0]submitted=0,ack=0,status=0,data=0;reg[31:0]expect_data=0;integer delay_count=0,commands=0,j;
    always @*begin
      case(corereadaddr)
       'h028:corerdata=ack;'h02c:corerdata=status;'h030:corerdata=data;default:corerdata=0;
      endcase
    end
    always @(posedge clk100)begin
     if(!reset_n)begin submitted<=0;ack<=0;status<=0;data<=0;delay_count<=0;commands<=0;writes<=0;for(j=0;j<12;j=j+1)fields[j]<=0;end
     else begin
      if(corewrite)begin
       writes<=writes+1;
       if(coreaddr>='h040&&coreaddr<='h06c)fields[(coreaddr-'h040)>>2]<=corewdata;
       if(coreaddr=='h020)submitted<=corewdata;
       if(coreaddr=='h024)begin
        if(delay_count!=0||submitted!=ack+1)$fatal(1,"doorbell order/sequence");
        for(j=0;j<12;j=j+1)if(fields[j]!==('h12300000|(submitted<<8)|j))$fatal(1,"field burst mismatch%0d",j);
        if(corewdata!==17)$fatal(1,"wrong operation");
        status<=1;delay_count<=512;expect_data<=fields[0]^fields[11]^corewdata;commands<=commands+1;
       end
      end
      if(delay_count>0)begin delay_count<=delay_count-1;if(delay_count==1)begin ack<=submitted;status<=0;data<=expect_data;end end
     end
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
            header(8'h55,address,HALF);shift(0,64,4,HALF);value=0;
            for(n=0;n<8;n=n+1)begin
                #HALF;sck=1;value=(value<<4)|dq;#HALF;sck=0;
            end
            end_transaction();
        end
    endtask
    task read_two(input[31:0]address,output[31:0]first,output[31:0]second);
        integer n;begin
            header(8'h55,address,HALF);shift(0,64,4,HALF);first=0;second=0;
            for(n=0;n<16;n=n+1)begin
                #HALF;sck=1;
                if(n<8)first=(first<<4)|dq;else second=(second<<4)|dq;
                #HALF;sck=0;
            end
            end_transaction();
        end
    endtask

    task read_three(output[31:0]a,output[31:0]b,output[31:0]c);
     integer n;begin header(8'h55,32'he0000028,HALF);shift(0,64,4,HALF);a=0;b=0;c=0;
      for(n=0;n<24;n=n+1)begin #(HALF);sck=1;if(n<8)a=(a<<4)|dq;else if(n<16)b=(b<<4)|dq;else c=(c<<4)|dq;#(HALF);sck=0;end
      end_transaction();end
    endtask
    reg[31:0]a,b,c;integer seq,i,polls;
    initial begin
     #(START_PHASE_NS);#100;reset_n=1;#200;
     for(seq=1;seq<=32;seq=seq+1)begin
      header(8'h54,32'he0000040,HALF);for(i=0;i<12;i=i+1)shift('h12300000|(seq<<8)|i,32,4,HALF);end_transaction();
      header(8'h54,32'he0000020,HALF);shift(seq,32,4,HALF);shift(17,32,4,HALF);end_transaction();
      polls=0;read_three(a,b,c);
      while(a!==seq)begin if(polls>10)$fatal(1,"mailbox timeout");polls=polls+1;read_three(a,b,c);end
      if(b!==0||c!==(32'd11^32'd17))$fatal(1,"burst reply stale/mixed ack%h status%h data%h",a,b,c);
      if(overflow)$fatal(1,"CDC overflow");
     end
     if(commands!=32||writes!=448)$fatal(1,"accepted counts commands%0d writes%0d",commands,writes);
     $display("PIN_BATCH_PASS actual_selected_endpoint_CDC fields12 submit2 reply3 commands32 writes448 overflow0 phase%0f half%0f",START_PHASE_NS,HALF);$finish;
    end
    initial begin #2000000;$fatal(1,"watchdog");end
endmodule
