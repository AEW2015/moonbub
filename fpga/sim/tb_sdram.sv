`timescale 1ns/1ps
module tb_sdram #(parameter real T_AC_NS=2.0);
 initial if($test$plusargs("wave"))begin
  $dumpfile($sformatf("sdram-tac%0d.vcd",T_AC_NS));$dumpvars(0,tb_sdram);
 end
 reg clk=0;always #5 clk=!clk;
 wire read_clk;assign #2.75 read_clk=~clk;
 reg reset=1,valid=0,write=0;reg[23:0]address=0;reg[15:0]data=0;
 wire ready,rv,idle;wire[15:0]rd;wire[12:0]a;wire[1:0]ba,cke,cs;wire[15:0]dq;
 wire sclk,ras,cas,we,ldqm,udqm;
 moonshine_sdram #(.POWERUP_CYCLES(30),.REFRESH_CYCLES(90)) dut(.clk(clk),.read_clk(read_clk),.reset(reset),
 .request_valid(valid),.request_ready(ready),.request_write(write),.request_address(address),.request_data(data),
 .response_valid(rv),.response_data(rd),.idle(idle),.sdram_a(a),.sdram_bs(ba),.sdram_dq(dq),.sdram_clk(sclk),
 .sdram_cke(cke),.sdram_cs_n(cs),.sdram_ras_n(ras),.sdram_cas_n(cas),.sdram_we_n(we),.sdram_ldqm(ldqm),.sdram_udqm(udqm));
 reg[15:0]mem[0:1048575];reg[12:0]rows[0:3];reg[3:0]opened=0;
 reg drive=0;reg[15:0]outdata;assign dq=drive ? outdata:16'bz;
 integer latency=0,left=0,readaddr=0,refreshes=0,mrs=0;
 integer lastact[0:3],lastpre[0:3],cycle=0;
 wire device_clock;assign #4 device_clock=sclk;
 always @(posedge device_clock)if(cke[0])begin
  cycle=cycle+1;
  if(latency>0)begin
   latency=latency-1;
   if(latency==0)begin outdata<=#(T_AC_NS) mem[readaddr];drive<=#(T_AC_NS) 1;readaddr=readaddr+1;left=7;end
  end else if(left>0)begin outdata<=#(T_AC_NS) mem[readaddr];readaddr=readaddr+1;left=left-1;end
  else drive<=#(T_AC_NS) 0;
  if(!cs[0])case({ras,cas,we})
   3'b011:begin
    if(opened[ba])$fatal(1,"ACT on open bank");
    if(cycle-lastpre[ba]<2)$fatal(1,"tRP violated");
    opened[ba]=1;rows[ba]=a;lastact[ba]=cycle;
   end
   3'b010:begin
    if(a[10])opened=0;else opened[ba]=0;
    if(!a[10]&&cycle-lastact[ba]<5)$fatal(1,"tRAS violated");
    if(a[10])begin lastpre[0]=cycle;lastpre[1]=cycle;lastpre[2]=cycle;lastpre[3]=cycle;end
    else lastpre[ba]=cycle;
   end
   3'b100:begin
    if(!opened[ba]||cycle-lastact[ba]<2)$fatal(1,"write tRCD violated");
    if(ldqm||udqm)$fatal(1,"bad write mask");
    mem[{ba,rows[ba],a[8:0]}]=dq;
   end
   3'b101:begin
    if(!opened[ba]||cycle-lastact[ba]<2)$fatal(1,"read tRCD violated");
    if(a[2:0]!=0)$fatal(1,"unaligned burst test");
    readaddr={ba,rows[ba],a[8:0]};latency=3;
   end
   3'b001:begin if(opened!=0)$fatal(1,"refresh openbank");refreshes=refreshes+1;end
   3'b000:begin if(a!==13'h233)$fatal(1,"bad mode %x",a);mrs=mrs+1;end
  endcase
 end
 task request(input bit w,input[23:0]addr,input[15:0]d);
 begin @(negedge clk);valid=1;write=w;address=addr;data=d;
 while(!ready)@(negedge clk);
 @(negedge clk);valid=0;
 end endtask
 task read8(input[23:0]addr,input[15:0]base);
 integer beat;
 begin request(0,addr,0);beat=0;
 while(beat<8)begin @(negedge clk);if(rv)begin
 if(rd!==(base+beat))$fatal(1,"read mismatch addr=%x beat=%d actual=%x expected=%x",addr,beat,rd,base+beat);
 beat=beat+1;end end
 end endtask
 integer i;
 initial begin
  for(i=0;i<4;i=i+1)begin lastact[i]=-100;lastpre[i]=-100;end
  repeat(4)@(negedge clk);reset=0;
  for(i=0;i<16;i=i+1)request(1,24'h1230+i,16'ha000+i);
  for(i=0;i<8;i=i+1)request(1,24'h84500+i,16'hb000+i);
  read8(24'h1230,16'ha000);read8(24'h1238,16'ha008);read8(24'h84500,16'hb000);
  repeat(250)@(negedge clk);read8(24'h1230,16'ha000);
  if(refreshes<4||mrs!=1)$fatal(1,"init/refresh missing");
  $display("SDRAM_PASS writes24 readwords32 refreshes%0d modeBL8_CAS3_writeSingle=1",refreshes);$finish;
 end
 initial begin #100000;$fatal(1,"timeout");end
endmodule
