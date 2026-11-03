`timescale 1ns/1ps
module tb_transport_overflow;
    reg spi_clk=0,core_clk=0;always #2.5 spi_clk=~spi_clk;always #5 core_clk=~core_clk;
    reg reset=1,wr=0,rd=0;reg[11:0]addr=12'h100;reg[31:0]data=0;
    wire[31:0]rdata,gray;wire overflow,cwrite;wire[11:0]caddr;wire[31:0]cdata;
    integer offered=0,delivered=0,last=-1,cycles=0;
    moonshine_bus_cdc dut(.spi_clk(spi_clk),.spi_reset(reset),.spi_write(wr),.spi_read(rd),
      .spi_address(addr),.spi_wdata(data),.spi_rdata(rdata),.overflow(overflow),.overflow_gray(gray),
      .core_clk(core_clk),.core_reset(reset),.core_write(cwrite),.core_address(caddr),.core_wdata(cdata),
      .core_rdata(delivered));
    function automatic[31:0]binary(input[31:0]g);
        integer i;begin binary[31]=g[31];for(i=30;i>=0;i=i-1)binary[i]=binary[i+1]^g[i];end
    endfunction
    reg[31:0]previous_gray=0,delta;
    always @(posedge spi_clk)if(!reset && wr)offered=offered+1;
    always @(negedge spi_clk)begin
        if(reset)previous_gray=0;
        else begin
            delta=gray^previous_gray;
            if(delta!=0 && (delta&(delta-1))!=0)$fatal(1,"non-Gray loss counter transition");
            previous_gray=gray;
        end
    end
    always @(posedge core_clk)begin
        cycles=cycles+1;
        if(reset)begin delivered=0;last=-1;end
        else if(cwrite)begin
            if(caddr!==12'h100 || cdata>=offered || $signed(cdata)<=last)$fatal(1,"corrupted/duplicate/out-of-order accepted word");
            last=cdata;delivered=delivered+1;
        end
    end
    integer i,expected;
    task clear;
        begin @(negedge spi_clk);reset=1;wr=0;rd=0;offered=0;
            repeat(8)@(negedge spi_clk);reset=0;repeat(8)@(negedge spi_clk);
        end
    endtask
    initial begin
        clear();
        // Maximum source-clock offer rate exceeds consumer rate and fills the
        // finite bridge; loss must be counted rather than silently aliased.
        for(i=0;i<512;i=i+1)begin @(negedge spi_clk);wr=1;data=i;end
        @(negedge spi_clk);wr=0;
        repeat(200)@(negedge core_clk);
        expected=offered-delivered;
        if(expected<=0 || !overflow || binary(gray)!==expected)$fatal(1,"loss conservation offered%0d delivered%0d gray%h",offered,delivered,gray);
        $display("TRANSPORT_OVERFLOW_CONSERVATION offers=%0d delivered=%0d lost=%0d",offered,delivered,expected);
        // Verify the existing response mailbox still works after saturation.
        @(negedge spi_clk);rd=1;addr=12'h028;
        @(negedge spi_clk);rd=0;repeat(32)@(negedge spi_clk);
        if(rdata!==delivered)$fatal(1,"read recovery after overflow");
        clear();addr=12'h100;
        // Normal pacing accepts every word and leaves the loss count zero.
        for(i=0;i<128;i=i+1)begin
            @(negedge spi_clk);wr=1;data=i;
            @(negedge spi_clk);wr=0;repeat(12)@(negedge spi_clk);
        end
        repeat(100)@(negedge core_clk);
        if(delivered!=128 || offered!=128 || overflow || gray!=0)$fatal(1,"normal traffic/reset recovery");
        $display("TRANSPORT_OVERFLOW_PASS conservation Gray_singlebit mailbox_recovery reset normal128");$finish;
    end
    initial begin #100000;$fatal(1,"watchdog");end
endmodule
