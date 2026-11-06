`timescale 1ns/1ps
// Lab-only BL8 SDR SDRAM model. Functional exercise; not timing signoff.
module sdram_model_burst #(parameter real T_OH_NS=0.5, T_AC_NS=2.0, CLOCK_FLIGHT_NS=4.0, parameter integer MEM_WORDS=1310721)(input wire clk,input wire[12:0]a,input wire[1:0]ba,input wire[1:0]cke,cs,
 input wire ras,cas,we,ldqm,udqm,inout wire[15:0]dq);
 reg[15:0]mem[0:MEM_WORDS-1];reg[12:0]rows[0:3];reg[3:0]opened=0;
 reg drive=0;reg[15:0]outdata;assign dq=drive ? outdata:16'bz;
 integer reads=0,acts=0,pres=0; integer latency=0,left=0,readaddr=0,refreshes=0,mrs=0,writes=0,write_left=0,writeaddr=0,interrupts=0,masked_bytes=0;
 integer lastact[0:3],lastpre[0:3],cycle=0,i;reg[15:0]old_word;
 initial for(i=0;i<4;i=i+1)begin lastact[i]=-100;lastpre[i]=-100;end
 wire device_clock;assign #(CLOCK_FLIGHT_NS)device_clock=clk;
 task apply_word(input integer addr);
  begin
   if(addr<0||addr>=MEM_WORDS)$fatal(1,"model write out of bounds %0d",addr);
   old_word=mem[addr];
   if(!ldqm)old_word[7:0]=dq[7:0];else masked_bytes=masked_bytes+1;
   if(!udqm)old_word[15:8]=dq[15:8];else masked_bytes=masked_bytes+1;
   mem[addr]=old_word;writes=writes+1;
  end
 endtask
 always @(posedge device_clock)if(cke[0])begin
  cycle=cycle+1;
  if(latency>0)begin latency=latency-1;if(latency==0)begin if(readaddr<0||readaddr>=MEM_WORDS)$fatal(1,"model read out of bounds %0d",readaddr);outdata<=#(T_AC_NS) mem[readaddr];drive<=#(T_AC_NS) 1;readaddr=readaddr+1;left=7;end end
  else if(left>0)begin outdata<=#(T_OH_NS) 16'hxxxx; if(readaddr<0||readaddr>=MEM_WORDS)$fatal(1,"model read out of bounds %0d",readaddr);outdata<=#(T_AC_NS) mem[readaddr];readaddr=readaddr+1;left=left-1;end
  else drive<=#(T_OH_NS) 0;
  // SDR burst terminate interrupts before consuming the current beat.
  if(write_left>0)begin
   if(!cs[0] && {ras,cas,we}==3'b110)begin write_left=0;interrupts=interrupts+1;end
   else begin
    if(!cs[0] && {ras,cas,we}!=3'b111)$fatal(1,"non-NOP during write burst");
    apply_word(writeaddr);writeaddr=writeaddr+1;write_left=write_left-1;
   end
  end
  if(!cs[0])case({ras,cas,we})
   3'b011:begin acts=acts+1;if(opened[ba])$fatal(1,"ACT on open bank");if(cycle-lastpre[ba]<2)$fatal(1,"tRP violated");opened[ba]=1;rows[ba]=a;lastact[ba]=cycle;end
   3'b010:begin pres=pres+1;if(!a[10]&&cycle-lastact[ba]<5)$fatal(1,"tRAS violated");if(a[10])begin opened=0;for(i=0;i<4;i=i+1)lastpre[i]=cycle;end else begin opened[ba]=0;lastpre[ba]=cycle;end end
   3'b100:begin
    if(!opened[ba]||cycle-lastact[ba]<2)$fatal(1,"write tRCD violated");
    if(a[2:0]!=0)$fatal(1,"burst write address must be aligned");
    writeaddr={ba,rows[ba],a[8:0]};apply_word(writeaddr);writeaddr=writeaddr+1;write_left=7;
   end
   3'b101:begin if(!opened[ba]||cycle-lastact[ba]<2)$fatal(1,"read tRCD violated");if(a[2:0]!=0)$fatal(1,"unaligned burst read");reads=reads+1;readaddr={ba,rows[ba],a[8:0]};// W9825G6KH A04 p23: READ edge3, D0 launch edge5, capture edge6.
    // Programmed CAS remains3; first DQ launch is CL-1 subsequent edges.
    latency=2;end
   3'b001:begin if(opened!=0)$fatal(1,"refresh open bank");refreshes=refreshes+1;end
   3'b000:begin if(a!==13'h033)$fatal(1,"bad mode %x",a);mrs=mrs+1;end
  endcase
 end

// Winbond W9825G6KH-6 A04 digital limits, ns at 100MHz.
real last_pin_change=-1.0e9,last_pin_edge=-1.0e9;
real last_dq_low=-1.0e9,last_dq_high=-1.0e9,last_write_low=-1.0e9,last_write_high=-1.0e9;
real last_any_act=-1.0e9,last_ref=-1.0e9,last_deadline_anchor=-1.0e9,last_mrs=-1.0e9;
real mon_act[0:3],mon_pre[0:3],mon_write[0:3];
reg[3:0]mon_open=0;integer mon_i,seen_writes=0;reg refresh_tracking=0;
initial for(mon_i=0;mon_i<4;mon_i=mon_i+1)begin
 mon_act[mon_i]=-1.0e9;mon_pre[mon_i]=-1.0e9;mon_write[mon_i]=-1.0e9;
end
always @(a or ba or cs or ras or cas or we or ldqm or udqm or cke)begin
 if(cke[0] && $realtime-last_pin_edge<0.8)$fatal(1,"SDR2_INPUT_HOLD_VIOLATION");
 last_pin_change=$realtime;
end
always @(dq[7:0])begin
 if($realtime-last_write_low<0.8)$fatal(1,"SDR2_DQ_HOLD_VIOLATION");
 last_dq_low=$realtime;
end
always @(dq[15:8])begin
 if($realtime-last_write_high<0.8)$fatal(1,"SDR2_DQ_HOLD_VIOLATION");
 last_dq_high=$realtime;
end
always @(posedge device_clock)if(cke[0])begin
 if($realtime-last_pin_change<1.5)$fatal(1,"SDR2_INPUT_SETUP_VIOLATION");
 last_pin_edge=$realtime;
 // Run after the functional model's blocking write counter; no sampled pin changes.
 #0;
 if(writes!=seen_writes)begin
  if((!ldqm&&$realtime-last_dq_low<1.5)||(!udqm&&$realtime-last_dq_high<1.5))$fatal(1,"SDR2_DQ_SETUP_VIOLATION");
  if((!ldqm&&(^dq[7:0]===1'bx))||(!udqm&&(^dq[15:8]===1'bx)))$fatal(1,"SDR2_DQ_UNKNOWN_WRITE");
  if(!ldqm)last_write_low=$realtime;if(!udqm)last_write_high=$realtime;
  mon_write[ba]=$realtime;seen_writes=writes;
 end
 if(refresh_tracking&&$realtime-last_deadline_anchor>7812.5)$fatal(1,"SDR2_REFRESH_POLICY_DEADLINE");
 for(mon_i=0;mon_i<4;mon_i=mon_i+1)
  if(mon_open[mon_i]&&$realtime-mon_act[mon_i]>100000.0)$fatal(1,"SDR2_TRAS_MAX_VIOLATION");
 if(!cs[0]&&{ras,cas,we}!=3'b111)begin
  if($realtime-last_ref<60.0)$fatal(1,"SDR2_TRFC_VIOLATION");
  if($realtime-last_mrs<20.0)$fatal(1,"SDR2_TMRD_VIOLATION");
  case({ras,cas,we})
   3'b011:begin
    if($realtime-mon_act[ba]<60.0)$fatal(1,"SDR2_TRC_VIOLATION");
    if($realtime-last_any_act<20.0)$fatal(1,"SDR2_TRRD_VIOLATION");
    if($realtime-mon_pre[ba]<15.0)$fatal(1,"SDR2_TRP_VIOLATION");
    mon_act[ba]=$realtime;last_any_act=$realtime;mon_open[ba]=1;
   end
   3'b010:begin
    for(mon_i=0;mon_i<4;mon_i=mon_i+1)if(a[10]||mon_i==ba)begin
     if(mon_open[mon_i]&&$realtime-mon_act[mon_i]<42.0)$fatal(1,"SDR2_TRAS_MIN_VIOLATION");
     if($realtime-mon_write[mon_i]<20.0)$fatal(1,"SDR2_TWR_VIOLATION");
     mon_pre[mon_i]=$realtime;mon_open[mon_i]=0;
    end
   end
   3'b100,3'b101:if($realtime-mon_act[ba]<15.0)$fatal(1,"SDR2_TRCD_VIOLATION");
   3'b001:begin
    for(mon_i=0;mon_i<4;mon_i=mon_i+1)
     if($realtime-mon_pre[mon_i]<15.0)$fatal(1,"SDR2_TRP_REFRESH_VIOLATION");
    last_ref=$realtime;last_deadline_anchor=$realtime;
   end
   3'b000:begin last_mrs=$realtime;last_deadline_anchor=$realtime;refresh_tracking=1;end
  endcase
 end
end

endmodule
