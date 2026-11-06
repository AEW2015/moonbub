"""Additional digital AC/protocol checks for the isolated SDR2 pin model.

Commands and DQ are observed at the modeled device clock. CAS scheduling and
functional memory behavior remain the original model's. The refresh maximum
interval check is a conservative evenly-spaced-refresh policy, not a claim
that the datasheet forbids legal burst-refresh schedules.
"""
def add_checks(text):
    assert text.count('endmodule')==1
    monitor=r'''
// Winbond W9825G6KH-6 A04 digital limits, ns at 100MHz.
real last_pin_change=-1.0e9,last_pin_edge=-1.0e9;
real last_dq_low=-1.0e9,last_dq_high=-1.0e9,last_write_low=-1.0e9,last_write_high=-1.0e9;
real last_any_act=-1.0e9,last_ref=-1.0e9,last_mrs=-1.0e9;
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
 if(refresh_tracking&&$realtime-last_ref>7812.5)$fatal(1,"SDR2_REFRESH_POLICY_DEADLINE");
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
    last_ref=$realtime;
   end
   3'b000:begin last_mrs=$realtime;last_ref=$realtime;refresh_tracking=1;end
  endcase
 end
end
'''
    return text.replace('endmodule',monitor+'\nendmodule')
