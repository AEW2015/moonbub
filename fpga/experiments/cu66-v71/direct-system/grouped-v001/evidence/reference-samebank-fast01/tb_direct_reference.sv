`timescale 1ns/1ps
module tb_direct_reference #(parameter integer LAST_LINE=799,BACKGROUND=0,FRONT_BANK=0,WRITE_BANK=1,WRITE_HUD_BANK=1,REF_BANK=-1);
 logic clk=0,read_clk=0,rst=1,abort_i=0,aux_abort_i=0;
 always #5 clk=~clk;
 always @(clk)read_clk<=#2.625 ~clk;
 logic read_valid=0,read_ready;logic [63:0] read_generation=0;logic [1:0] read_bank=0,read_plane=0;logic [16:0]read_index=0;
 logic read_rsp_valid,read_rsp_ready=0;logic [63:0]read_rsp_generation;logic[1:0]read_rsp_bank,read_rsp_plane;logic[16:0]read_rsp_index;logic[511:0]read_rsp_pixels;logic read_rsp_error;
 logic write_valid=0,write_ready;logic[63:0]write_generation=0;logic[1:0]write_bank=0,write_plane=0;logic[16:0]write_index=0;logic[511:0]write_pixels=0;
 logic write_done_valid,write_done_ready=0;logic[63:0]write_done_generation;logic[1:0]write_done_bank,write_done_plane;logic[16:0]write_done_index;logic write_done_error;
 logic tile_busy,tile_aborted;
 logic aux_req_valid=0,aux_req_ready,aux_req_write=0;logic[23:0]aux_req_addr=0;logic[15:0]aux_req_data=0;
 logic aux_rsp_valid,aux_rsp_ready=0;logic[15:0]aux_rsp_data;logic aux_rsp_error,aux_busy,aux_aborted;
 wire[12:0]sdram_a;wire[1:0]sdram_bs,sdram_cke,sdram_cs_n;wire[15:0]sdram_dq;wire sdram_clk,sdram_ras_n,sdram_cas_n,sdram_we_n,sdram_ldqm,sdram_udqm;logic idle;
 logic lcd_req_valid,lcd_req_ready,lcd_rsp_valid,lcd_rsp_ready,lcd_rsp_error,lcd_abort_i,lcd_busy,lcd_aborted;
 logic[23:0]lcd_req_addr;logic[127:0]lcd_rsp_data;logic[31:0]lcd_completed_reads,lcd_max_wait;
 logic rgb_req_valid=0,rgb_req_ready,rgb_rsp_valid,rgb_rsp_ready=1,rgb_rsp_error,rgb_abort_i=0,rgb_busy,rgb_aborted;logic[23:0]rgb_req_addr=0;logic[127:0]rgb_req_data=0;logic[15:0]rgb_req_mask=0;logic[31:0]rgb_completed_writes,rgb_max_wait;
 logic[31:0]cache_hits,cache_misses,completed_reads,completed_writes;
 cu71_memory_system_direct #(.POWERUP_CYCLES(20)) dut(.*);
 sdram_model_burst #(.MEM_WORDS(16777216),.T_AC_NS(2.223),.CLOCK_FLIGHT_NS(0.757),.T_OH_NS(2.223)) model(.clk(sdram_clk),.a(sdram_a),.ba(sdram_bs),.cke(sdram_cke),.cs(sdram_cs_n),.ras(sdram_ras_n),.cas(sdram_cas_n),.we(sdram_we_n),.ldqm(sdram_ldqm),.udqm(sdram_udqm),.dq(sdram_dq));
 `include "cu70_memory_map.svh"

 logic pixel_clk=0,pixel_reset_n=0;always #17.03 pixel_clk=~pixel_clk;
 logic prepare_valid=0,prepare_ready;logic[63:0]prepare_generation=1;logic[31:0]prepare_frame_id=100;
 logic[1:0]prepare_canonical_bank=FRONT_BANK,prepare_hud_bank=FRONT_BANK;logic prepare_cache_slot=0;
 logic prepared_valid,prepared_ready=0;logic[63:0]prepared_generation;logic[31:0]prepared_frame_id;logic prepared_cache_slot,prepared_error;logic[7:0]prepared_reason;
 logic prepare_abort_valid=0,prepare_abort_ready;logic[63:0]prepare_abort_generation=0;logic[31:0]prepare_abort_frame_id=0;logic prepare_abort_cache_slot=0,abort_done,abort_error;
 logic descriptor_valid=0,descriptor_ready;logic[63:0]descriptor_generation=1;logic[31:0]descriptor_frame_id=100;logic descriptor_cache_slot=0;
 logic presented,error,front_valid,front_cache_slot;logic[63:0]front_generation;logic[31:0]front_frame_id;logic pending_valid;logic[31:0]presented_count;
 logic frame_boundary,scanout_drained;logic[31:0]underruns,dma_reads,unowned_dma_responses,accepted_prepares,rejected_prepares,rejected_descriptors,memory_errors,line_cache_misses,generated_lines,prepare_cycles;
 logic[7:0]first_fault;logic[63:0]first_fault_generation;logic[31:0]first_fault_frame_id;
 logic hsync,vsync,data_enable;logic[9:0]physical_x,physical_y;logic[7:0]red,green,blue;
 cu71_direct_scanout scanout(.mem_clk(clk),.*);
 reg[15:0]canonical[0:259199],hud[0:21119],gold[0:345599];integer i,pixels=0,black_lines=0;reg[15:0]want;reg black_line=0,monitor_done=0;integer prep_start,prep_reads;
 always @(posedge pixel_clk)begin
  #0.001;
  if(pixel_reset_n&&front_valid&&data_enable&&!monitor_done)begin
   want=(physical_y>=40&&physical_y<760)?gold[physical_x*720+physical_y-40]:16'd0;
   if(physical_x==0)begin black_line=physical_y>=40&&physical_y<760&&!scanout.lcd.line_good;if(black_line)black_lines=black_lines+1;end
   if(black_line)want=0;
   if(red!=={want[15:11],want[15:13]}||green!=={want[10:5],want[10:9]}||blue!=={want[4:0],want[4:2]})$fatal(1,"direct pin native pixel mismatch x%0d y%0d expected%h got%h %h %h fault%h",physical_x,physical_y,want,red,green,blue,first_fault);
   pixels=pixels+1;if(physical_y==LAST_LINE&&physical_x==479)monitor_done=1;
  end
 end
 localparam integer COPY_REF_BANK=REF_BANK<0?FRONT_BANK:REF_BANK;
 localparam[23:0]COPY_REF_BASE=CANONICAL0_BASE+24'(COPY_REF_BANK*4194304);
 localparam[23:0]FRONT_CAN_BASE=CANONICAL0_BASE+24'(FRONT_BANK*4194304),FRONT_HUD_BASE=HUD0_BASE+24'(FRONT_BANK*4194304);
 integer bg_tiles=0,bg_hud=0,bg_cycles=0,bg_reads=0;reg[511:0]reference_expected;integer bg_plane=0,bg_index=0;reg bg_started=0;
 always @(posedge clk)if(bg_started&&!monitor_done)bg_cycles=bg_cycles+1;
 initial begin
  if(BACKGROUND!=0)begin
   wait(front_valid);bg_started=1;
   while(!monitor_done)begin
    @(negedge clk);read_valid=1;read_generation=64'd2000+64'(bg_tiles);read_bank=2'(COPY_REF_BANK);read_plane=2'(bg_plane);read_index=17'(bg_index);
    for(integer w=0;w<32;w=w+1)reference_expected[w*16+:16]=canonical[(bg_plane==0?0:bg_plane==1?172800:216000)+bg_index*32+w];
    do @(posedge clk);while(!read_ready);@(negedge clk);read_valid=0;
    while(!read_rsp_valid)@(negedge clk);
    if(read_rsp_error||read_rsp_generation!=read_generation||read_rsp_bank!=COPY_REF_BANK||read_rsp_plane!=bg_plane||read_rsp_index!=bg_index||read_rsp_pixels!==reference_expected)$fatal(1,"concurrent reference identity/payload failure");
    write_pixels=read_rsp_pixels;read_rsp_ready=1;@(posedge clk);@(negedge clk);read_rsp_ready=0;bg_reads=bg_reads+1;
    write_valid=1;write_generation=64'd1000+64'(bg_tiles);write_bank=2'(WRITE_BANK);write_plane=2'(bg_plane);write_index=17'(bg_index);
    do @(posedge clk);while(!write_ready);@(negedge clk);write_valid=0;
    while(!write_done_valid)@(negedge clk);
    if(write_done_error||write_done_generation!=write_generation||write_done_bank!=WRITE_BANK||write_done_plane!=bg_plane||write_done_index!=bg_index)$fatal(1,"concurrent canonical completion identity/error");
    write_done_ready=1;@(posedge clk);@(negedge clk);write_done_ready=0;bg_tiles=bg_tiles+1;
    if(bg_index==(bg_plane==0?5399:1349))begin bg_index=0;bg_plane=bg_plane==2?0:bg_plane+1;end else bg_index=bg_index+1;
    if(bg_tiles%16==0&&!monitor_done)begin
     aux_req_valid=1;aux_req_write=1;aux_req_addr=HUD0_BASE+24'(WRITE_HUD_BANK*4194304)+24'(bg_hud%21120);aux_req_data=16'(bg_hud^16'h7bed);
     do @(posedge clk);while(!aux_req_ready);@(negedge clk);aux_req_valid=0;while(!aux_rsp_valid)@(negedge clk);if(aux_rsp_error)$fatal(1,"concurrent HUD write error");aux_rsp_ready=1;@(posedge clk);@(negedge clk);aux_rsp_ready=0;bg_hud=bg_hud+1;
    end
   end
  end
 end
 reg[23:0]check_address;integer checks=0;reg[15:0]expected_word;
 always @(posedge clk)begin
  if(lcd_req_valid&&lcd_req_ready)check_address<=lcd_req_addr;
  if(lcd_rsp_valid&&lcd_rsp_ready)begin
   for(integer q=0;q<8;q=q+1)begin
    expected_word=(check_address>=FRONT_HUD_BASE&&check_address<FRONT_HUD_BASE+21120)?hud[check_address-FRONT_HUD_BASE+q]:canonical[check_address-FRONT_CAN_BASE+q];
    if(lcd_rsp_data[q*16+:16]!==expected_word)$fatal(1,"physical BL8 payload mismatch addr%h lane%0d got%h want%h",check_address,q,lcd_rsp_data[q*16+:16],expected_word);
   end
   checks=checks+1;
  end
  if(scanout.cache_rd_valid&&scanout.render_u==0&&scanout.issue_count==40)$display("RAW_V40 ymem%h canonicalY%h CB%h CR%h gold%h",scanout.cache.y_mem[40],canonical[14400],scanout.cache.cb_top_mem[20],scanout.cache.cr_top_mem[20],gold[28800]);
 end
 integer trace_fd,trace_events=0,trace_overflow=0,memcycles=0,job_start=0,job_max_y=0,job_max_c=0,jobs_y=0,jobs_c=0,first_miss=-1;
 integer request_cycle[0:799],admit_cycle[0:799],fill_cycle[0:799],deadline_cycle[0:799];
 reg previous_request=0,previous_job=0;reg[1:0]previous_kind=0;reg[6:0]previous_group=0;
 reg event_admit,event_fill;reg[9:0]event_line;reg[1:0]job_kind;
 task trace_event(input string name,input integer line_number);
  if(trace_events<12000)begin
   $fwrite(trace_fd,"%s,%0d,%0t,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d\n",name,memcycles,$time,line_number,front_cache_slot,scanout.requested_u,scanout.request_y_ready,scanout.request_c_ready,scanout.request_next_c_ready,scanout.cache_ready,scanout.f_active,scanout.f_kind,scanout.f_group,scanout.p_active,scanout.p_phase,lcd_busy,lcd_max_wait,scanout.render_active,scanout.issue_count,scanout.emit_count,scanout.lcd.fill);trace_events=trace_events+1;
  end else trace_overflow=trace_overflow+1;
 endtask
 initial begin
  trace_fd=$fopen("trace.csv","w");if(!trace_fd)$fatal(1,"trace open");
  $fwrite(trace_fd,"event,memcycle,time_ps,panel_line,context,requested_u,y_ready,c_ready,halo_ready,cache_ready,front_job,kind,group,prepare,prepare_phase,lcd_busy,max_backend_wait,render,issue,emit,lcd_fill\n");
  for(integer l=0;l<800;l=l+1)begin request_cycle[l]=-1;admit_cycle[l]=-1;fill_cycle[l]=-1;deadline_cycle[l]=-1;end
 end
 always @(posedge clk)begin
  memcycles=memcycles+1;event_admit=scanout.line_req_valid&&scanout.line_req_ready;event_line=scanout.line_req_line;
  event_fill=scanout.render_active&&scanout.line_data_valid&&scanout.emit_count==479;
  #0.001;
  if(scanout.line_req_valid&&!previous_request)begin
   request_cycle[scanout.line_req_line]=memcycles;trace_event("LINE_REQUEST",scanout.line_req_line);
  end
  if(event_admit)begin admit_cycle[event_line]=memcycles;trace_event("LINE_ADMIT",event_line);end
  if(event_fill)begin
   fill_cycle[scanout.render_u+40]=memcycles;trace_event("LINE_FILL",scanout.render_u+40);
   if(scanout.render_u[2:0]==7)trace_event("Y_BANK_LAST_READER",scanout.render_u+40);
  end
  if(scanout.f_active&&!previous_job)begin job_start=memcycles;job_kind=scanout.f_kind;trace_event("PAGE_START",scanout.lcd.py);end
  if(scanout.f_active&&previous_job&&scanout.f_kind!=previous_kind)trace_event("PAGE_PLANE",scanout.lcd.py);
  if(!scanout.f_active&&previous_job)begin
   if(job_kind==0)begin jobs_y=jobs_y+1;if(memcycles-job_start>job_max_y)job_max_y=memcycles-job_start;end
   else begin jobs_c=jobs_c+1;if(memcycles-job_start>job_max_c)job_max_c=memcycles-job_start;end
   trace_event("PAGE_DONE",scanout.lcd.py);
  end
  previous_request=scanout.line_req_valid;previous_job=scanout.f_active;previous_kind=scanout.f_kind;previous_group=scanout.f_group;
 end
 always @(posedge pixel_clk)begin
  #0.002;
  if(pixel_reset_n&&front_valid&&data_enable&&physical_x==0&&!monitor_done)begin
   deadline_cycle[physical_y]=memcycles;trace_event("LINE_DEADLINE",physical_y);
   if(physical_y>=40&&physical_y<760&&!scanout.lcd.line_good&&first_miss<0)begin first_miss=physical_y;trace_event("FIRST_UNDERRUN",physical_y);end
  end
 end
 initial begin
  $readmemh("canonical.hex",canonical);$readmemh("hud.hex",hud);$readmemh("gold.hex",gold);
  for(i=0;i<259200;i=i+1)begin model.mem[FRONT_CAN_BASE+i]=canonical[i];model.mem[COPY_REF_BASE+i]=canonical[i];end
  for(i=0;i<21120;i=i+1)model.mem[FRONT_HUD_BASE+i]=hud[i];
  repeat(8)@(negedge clk);rst=0;wait(idle);@(negedge clk);prep_start=scanout.prepare_cycles;prepare_valid=1;
  do @(posedge clk);while(!prepare_ready);@(negedge clk);prepare_valid=0;wait(prepared_valid);@(negedge clk);
  if(prepared_error||prepared_generation!=1||prepared_frame_id!=100||prepared_cache_slot!=0)$fatal(1,"prepare identity/error reason%h",prepared_reason);
  if(dma_reads!=3600)$fatal(1,"cold prepare reads%0d",dma_reads);
  $display("DIRECT_PREPARE_PASS cycles%0d actual_pin_reads%0d",prepare_cycles,dma_reads);
  prepared_ready=1;@(posedge clk);@(negedge clk);prepared_ready=0;descriptor_valid=1;
  do @(posedge clk);while(!descriptor_ready);@(negedge clk);descriptor_valid=0;pixel_reset_n=1;
  wait(monitor_done);repeat(8)@(negedge clk);
  if(first_fault||memory_errors||unowned_dma_responses)$fatal(1,"direct diagnostics fault%h errors%0d",first_fault,memory_errors);
  $display("DIRECT_PHYSICAL_COUNTERS reference_bank%0d readBL8%0d write_beats%0d ACT%0d PRE%0d refresh%0d maskedbytes%0d tile_busy%0d aux_busy%0d",COPY_REF_BANK,model.reads,model.writes,model.acts,model.pres,model.refreshes,model.masked_bytes,tile_busy,aux_busy);
  $display("DIRECT_REFERENCE_CONTROL ref_tiles%0d maxYpage%0d maxCpage%0d jobsY%0d jobsC%0d trace_events%0d trace_overflow%0d firstmiss%0d",bg_reads,job_max_y,job_max_c,jobs_y,jobs_c,trace_events,trace_overflow,first_miss);
  for(integer l=40;l<760;l=l+1)$fwrite(trace_fd,"LINE_TIMES,%0d,%0d,%0d,%0d,%0d\n",l,request_cycle[l],admit_cycle[l],fill_cycle[l],deadline_cycle[l]);
  $fclose(trace_fd);
  $display("DIRECT_BACKGROUND tiles%0d logical_words%0d HUDwords%0d active_cycles%0d frontbank%0d writebank%0d hudbank%0d",bg_tiles,bg_tiles*32,bg_hud,bg_cycles,FRONT_BANK,WRITE_BANK,WRITE_HUD_BANK);
  $display("CU71_DIRECT_PIN_FUNCTIONAL_PASS pixels%0d black_lines%0d underruns%0d reads%0d maxwait%0d refreshes%0d",pixels,black_lines,underruns,dma_reads,lcd_max_wait,model.refreshes);
  if(black_lines==0&&underruns==0)$display("CU71_DIRECT_PIN_CADENCE_PASS");else $display("CU71_DIRECT_PIN_CADENCE_FAIL");
  $finish;
 end
 initial begin #60000000;$fatal(1,"direct actual pin watchdog gen%0d prep%0d reads%0d fault%h",front_generation,prepared_valid,dma_reads,first_fault);end
endmodule

