`timescale 1ns/1ps
module tb_lcd_cdc #(parameter integer PHASE_PS=0,SEED=1);
 reg mem_clk=0,pixel_clk=0,mem_reset=1,reset_n=0;always #5 mem_clk=~mem_clk;
 initial begin #(PHASE_PS/1000.0);forever #17.028824833703 pixel_clk=~pixel_clk;end
 reg front_valid=0,front_buffer=0,pattern_enable=0;wire line_req_valid;reg line_req_ready=0;wire[23:0]line_req_address;wire[9:0]line_req_line;wire line_req_context;
 reg line_data_valid=0;reg[15:0]line_data=0;reg line_data_error=0;wire frame_boundary,requests_idle;wire[31:0]underruns;wire hsync,vsync,data_enable;wire[9:0]physical_x,physical_y;wire[7:0]red,green,blue;
 cu71_lcd_lines_syncsafe dut(.*);
 integer raw_busy_frames=0;reg raw_event,pre_idle;integer checks=0,launches=0,captures=0,acks=0,frames=0,qualified=0,reset_cases=0,late_frames=0,held_requests=0;integer random_state=SEED,worker_delay=0,worker_count=0,memcycles=0;reg worker=0,worker_bad=0;reg[9:0]worker_line=0;reg worker_context=0;
 real launched_at[0:1],done_at[0:1],last_launch=-1,min_capture=1.0e12,min_ack=1.0e12,min_quiet=1.0e12;
 reg[9:0]held_line[0:1];reg held_epoch[0:1],old_request[0:1],old_busy[0:1],old_done[0:1],old_bad[0:1];reg[31:0]gray_before;reg[31:0]gray_changed;reg old_frame=0;reg[9:0]old_x=0,old_y=0;
 reg pre_admit,pre_data;reg[9:0]pre_line;reg pre_context;integer prior_frames=0;reg injected_hold=0;integer hold_until=0;
 task check(input bit okay,input string why);begin checks=checks+1;if(!okay)$fatal(1,"CDC %s phase%0d seed%0d memcycle%0d",why,PHASE_PS,SEED,memcycles);end endtask
 initial begin
  for(integer i=0;i<2;i=i+1)begin launched_at[i]=-1;done_at[i]=-1;held_line[i]=0;held_epoch[i]=0;old_request[i]=0;old_busy[i]=0;old_done[i]=0;old_bad[i]=0;end
  repeat(10)@(negedge mem_clk);mem_reset=0;reset_n=1;front_valid=1;
 end
 // A bounded worker deliberately holds one late request across the next
 // vblank, inserts data bubbles, and reports line-level decode errors.
 always @(negedge mem_clk)begin
  if(mem_reset)begin worker=0;line_req_ready=0;line_data_valid=0;line_data_error=0;end
  else begin
   random_state=(random_state*1664525+1013904223);line_data_valid=0;line_req_ready=0;
   if(!worker)begin
    if(line_req_valid&&line_req_line==756&&!injected_hold)begin injected_hold=1;hold_until=memcycles+130000;end
    if(memcycles>=hold_until)line_req_ready=(random_state&3)!=0;else if(line_req_valid)held_requests=held_requests+1;
   end else if(worker_delay!=0)worker_delay=worker_delay-1;
   else if((random_state&7)!=0)begin line_data_valid=1;line_data=16'((worker_line*47+worker_count*133+worker_context*16'h53ab)|1);line_data_error=worker_bad&&(worker_count==120||worker_count==479);end
  end
 end
 always @(posedge mem_clk)begin
  raw_event=dut.frame_sync[1]!=dut.frame_seen;pre_idle=!dut.receiving&&!dut.line_req_valid&&!dut.address_pending&&dut.request_sync0[1]==dut.seen0&&dut.request_sync1[1]==dut.seen1;memcycles=memcycles+1;pre_admit=line_req_valid&&line_req_ready;pre_line=line_req_line;pre_context=line_req_context;pre_data=line_data_valid&&worker;
  #0.002;
  if(mem_reset)begin
   for(integer i=0;i<2;i=i+1)begin old_done[i]=0;old_bad[i]=0;done_at[i]=-1;end
  end else begin
   if(raw_event&&!pre_idle)raw_busy_frames=raw_busy_frames+1;
   if(pre_admit)begin check(!worker,"accepted while worker active");worker=1;worker_line=pre_line;worker_context=pre_context;worker_count=0;worker_delay=SEED%13;worker_bad=pre_line%17==0;captures=captures+1;end
   if(pre_data)begin
    check(!(dut.scan_content&&dut.scan_good&&dut.scan_odd==dut.selected),"writer touched good pixel bank");
    if(worker_count==479)worker=0;else worker_count=worker_count+1;
   end
   for(integer b=0;b<2;b=b+1)begin
    if((b==0?dut.done0:dut.done1)!=old_done[b])begin done_at[b]=$realtime;old_done[b]=(b==0?dut.done0:dut.done1);old_bad[b]=(b==0?dut.completed_bad0:dut.completed_bad1);end
    else check((b==0?dut.completed_bad0:dut.completed_bad1)===old_bad[b],"completion payload changed without token");
   end
   if(dut.address_pending)begin
    integer b;real age;b=dut.selected;age=$realtime-launched_at[b];
    check(launched_at[b]>=0&&age>=19.990,"request bundle captured too early");
    check(dut.captured_line===held_line[b],"request bundle/tag mismatch");if(age<min_capture)min_capture=age;
    check(dut.captured_buffer===front_buffer,"context must be memory local");
   end
   if(frame_boundary)begin
    if(last_launch>=0)check($realtime-last_launch>900000.0,"frame event lacks legal request quiet window");
    if($realtime-last_launch<min_quiet&&last_launch>=0)min_quiet=$realtime-last_launch;
    if(requests_idle&&!worker)begin front_buffer=~front_buffer;qualified=qualified+1;end else late_frames=late_frames+1;
   end
  end
 end
 always @(posedge pixel_clk)begin
  gray_before=dut.underrun_gray;old_x=dut.x;old_y=dut.y;
  for(integer b=0;b<2;b=b+1)begin old_busy[b]=(b==0?dut.busy0:dut.busy1);end
  #0.001;
  if(!reset_n)begin
   old_frame=0;last_launch=-1;for(integer b=0;b<2;b=b+1)begin old_request[b]=0;held_line[b]=0;held_epoch[b]=0;launched_at[b]=-1;end
  end else begin
   gray_changed=dut.underrun_gray^gray_before;check((gray_changed&(gray_changed-1))==0,"Gray source must change at most one bit");
   for(integer b=0;b<2;b=b+1)begin
    reg token,busy_now,epoch_now;reg[9:0]line_now;real age;
    token=b==0?dut.request0:dut.request1;busy_now=b==0?dut.busy0:dut.busy1;line_now=b==0?dut.request_line0:dut.request_line1;epoch_now=b==0?dut.request_epoch0:dut.request_epoch1;
    if(token!=old_request[b])begin
     check(!old_busy[b],"request reused busy bank");check(old_x==494&&old_y>=62&&old_y<782,"request outside legal source window");
     launched_at[b]=$realtime;last_launch=$realtime;held_line[b]=line_now;held_epoch[b]=epoch_now;launches=launches+1;old_request[b]=token;
    end else check(line_now===held_line[b]&&epoch_now===held_epoch[b],"request payload changed without token");
    if(old_busy[b]&&!busy_now)begin age=$realtime-done_at[b];check(done_at[b]>=0&&age>=68.110,"done bundle consumed too early");check((b==0?dut.completed_bad0:dut.completed_bad1)===old_bad[b],"done payload lost hold");if(age<min_ack)min_ack=age;acks=acks+1;end
   end
   if(dut.frame_toggle!=old_frame)begin frames=frames+1;old_frame=dut.frame_toggle;end
  end
 end
 // Abort/recovery scope is coordinated reset of the two-domain adapter.
 // There is no LCD-only/front abort port; provisional cache abort stays in
 // memory domain and FRONT/PENDING cancellation is forbidden by the owner.
 initial begin
  wait(captures>=4);wait(worker&&worker_count>=200);@(negedge mem_clk);mem_reset=1;reset_n=0;reset_cases=reset_cases+1;repeat(10)@(negedge mem_clk);mem_reset=0;reset_n=1;
  wait(injected_hold);wait(memcycles>=hold_until);wait(frames>=5);repeat(200)@(negedge mem_clk);
  check(launches>1500&&captures>1400&&acks>1400,"insufficient repeated CDC handshakes");check(held_requests>0&&raw_busy_frames>0,"held-vblank case not observed");
  $display("LCD_CDC_PROTOCOL_PASS phase_ps%0d seed%0d checks%0d launches%0d captures%0d acks%0d frames%0d qualified%0d lateframes%0d resetcases%0d min_capture_ns%0.3f min_ack_ns%0.3f min_quiet_ns%0.3f",PHASE_PS,SEED,checks,launches,captures,acks,frames,qualified,late_frames,reset_cases,min_capture,min_ack,min_quiet);$finish;
 end
 initial begin #90000000;$fatal(1,"CDC watchdog");end
endmodule
