// V72 checked 32MiB SDR SDRAM functional/timing model: BL8, CAS3, byte masks.
// This is a bounded command model, not vendor/electrical timing signoff.
`timescale 1ns/1ps
module cu72_sdram_model #(
 parameter integer REFRESH_CYCLES=750,
 parameter real T_AC_NS=2.0,CLOCK_FLIGHT_NS=4.0
)(input wire clk,reset,input wire[12:0]a,input wire[1:0]ba,input wire[1:0]cke,cs,
 input wire ras,cas,we,ldqm,udqm,inout wire[15:0]dq);
 reg[15:0]mem[0:16777215];reg[12:0]rows[0:3];reg[3:0]opened=0;
 reg drive=0;reg[15:0]outdata;assign dq=drive?outdata:16'bz;
 integer latency=0,left=0,readaddr=0,refreshes=0,mrs=0,writes=0;
 integer lastact[0:3],lastpre[0:3],lastwrite[0:3],cycle=0,i;
 integer lastrefresh=0,lastmrs=-100,acts=0,pres=0,reads=0;
 integer write_commands=0,write_bus_beats=0,write_left=0,writeaddr=0;
 reg[1:0]writebank=0;
 reg[23:0]last_write_address=0;
 reg[15:0]last_write_data=0;
 reg configured=0;
 integer command_addr;
 wire[2:0]command={ras,cas,we};
 initial for(i=0;i<4;i=i+1)begin lastact[i]=-100;lastpre[i]=-100;lastwrite[i]=-100;end
 reg device_clock;always @(clk)device_clock<=#(CLOCK_FLIGHT_NS)clk;
 task automatic accept_write_word(input integer address,input logic[1:0]bank);
 begin
  if(address<0||address>=16777216)$fatal(1,"write address outside 32MiB");
  if((ldqm!==1'b0&&ldqm!==1'b1)||(udqm!==1'b0&&udqm!==1'b1))$fatal(1,"unknown DQM");
  write_bus_beats=write_bus_beats+1;
  // tWR starts at the last bus beat even when the data is masked.
  lastwrite[bank]=cycle;
  if(!ldqm)begin
   if($isunknown(dq[7:0]))$fatal(1,"undriven low write byte");
   mem[address][7:0]=dq[7:0];
  end
  if(!udqm)begin
   if($isunknown(dq[15:8]))$fatal(1,"undriven high write byte");
   mem[address][15:8]=dq[15:8];
  end
  if(!ldqm||!udqm)begin
   writes=writes+1;last_write_address=24'(address);last_write_data=mem[address];
  end
 end endtask
 always @(posedge device_clock)begin
  if(reset)begin
   drive<=0;opened=0;latency=0;left=0;readaddr=0;cycle=0;
   refreshes=0;mrs=0;writes=0;reads=0;acts=0;pres=0;configured=0;lastrefresh=0;lastmrs=-100;
   write_commands=0;write_bus_beats=0;write_left=0;writeaddr=0;writebank=0;last_write_address=0;last_write_data=0;
   for(i=0;i<4;i=i+1)begin lastact[i]=-100;lastpre[i]=-100;lastwrite[i]=-100;rows[i]=0;end
  end else if(cke[0])begin
   cycle=cycle+1;
   if(cke[1]||!cs[1])$fatal(1,"unimplemented second chip selected");
   if(configured&&cycle-lastrefresh>REFRESH_CYCLES+64)$fatal(1,"refresh deadline exceeded cycle=%0d previous=%0d",cycle,lastrefresh);
   if(latency>0)begin
    latency=latency-1;
    if(latency==0)begin outdata<=#(T_AC_NS)mem[readaddr];drive<=#(T_AC_NS)1;readaddr=readaddr+1;left=7;end
   end else if(left>0)begin outdata<=#(T_AC_NS)mem[readaddr];readaddr=readaddr+1;left=left-1;end
   else drive<=#(T_AC_NS)0;
   if(write_left>0)begin
    if(!cs[0]&&command!=3'b111)$fatal(1,"command during write burst");
    accept_write_word(writeaddr,writebank);writeaddr=writeaddr+1;write_left=write_left-1;
   end
   if(!cs[0])begin
    if(command!=3'b111&&configured&&cycle-lastrefresh<8)$fatal(1,"tRFC violated");
    if(command!=3'b111&&cycle-lastmrs<2)$fatal(1,"tMRD violated");
    case(command)
     3'b011:begin
      if(!configured)$fatal(1,"ACT before MRS");
      if(opened[ba])$fatal(1,"ACT on open bank");
      if(cycle-lastpre[ba]<2)$fatal(1,"tRP violated");
      opened[ba]=1;rows[ba]=a;lastact[ba]=cycle;acts=acts+1;
     end
     3'b010:begin
      if(!a[10]&&cycle-lastact[ba]<5)$fatal(1,"tRAS violated");
      if(a[10])begin for(i=0;i<4;i=i+1)if(opened[i]&&(cycle-lastact[i]<5||cycle-lastwrite[i]<2))$fatal(1,"all-pre timing");end
      else if(cycle-lastwrite[ba]<2)$fatal(1,"write recovery violated");
      pres=pres+1;
      if(a[10])begin opened=0;for(i=0;i<4;i=i+1)lastpre[i]=cycle;end
      else begin opened[ba]=0;lastpre[ba]=cycle;end
     end
     3'b100:begin
      if(!configured||!opened[ba]||cycle-lastact[ba]<2)$fatal(1,"write tRCD/config violated");
      if(a[2:0]!=0)$fatal(1,"unaligned BL8 write");
      if(latency!=0||left!=0)$fatal(1,"write overlaps outstanding read burst");
      command_addr={8'd0,ba,rows[ba],a[8:0]};
      if(command_addr<0||command_addr+7>=16777216)$fatal(1,"write burst outside 32MiB");
      write_commands=write_commands+1;writebank=ba;
      accept_write_word(command_addr,ba);writeaddr=command_addr+1;write_left=7;
     end
     3'b101:begin
      if(!configured||!opened[ba]||cycle-lastact[ba]<2)$fatal(1,"read tRCD/config violated");
      if(a[2:0]!=0)$fatal(1,"unaligned BL8 read");
      if(ldqm||udqm)$fatal(1,"masked read command");
      if(latency!=0||left!=0)$fatal(1,"read overlaps outstanding read burst");
      readaddr={8'd0,ba,rows[ba],a[8:0]};latency=3;reads=reads+1;
      if(readaddr<0||readaddr+7>=16777216)$fatal(1,"read burst outside 32MiB");
     end
     3'b001:begin if(opened!=0)$fatal(1,"refresh open bank");refreshes=refreshes+1;lastrefresh=cycle;end
     3'b000:begin if(a!==13'h033)$fatal(1,"bad BL8 mode %x",a);mrs=mrs+1;configured=1;lastrefresh=cycle-8;lastmrs=cycle;end
     3'b111:begin end
     default:$fatal(1,"unsupported SDRAM command");
    endcase
   end
  end
 end
endmodule
