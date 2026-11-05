`timescale 1ns/1ps
module tb;
 parameter SMOKE=1,CASE=0,ABORT_PENDING=0,ABORT_MODE=0,RESET_LOAD=0,PRIVATE_ERROR=0;
 localparam N=518400,PACKET=17412,BASE=24'h100000,SECOND=24'h140000;
 reg clk=0;always #5 clk=~clk;wire read_clk;assign #2.75 read_clk=~clk;
 reg pixel_clk=0;realtime next_pixel_edge=0;
 localparam realtime HALF_PIXEL_NS=1.0e9/(2.0*(50.0e6*56.375/3.0/32.0));
 initial forever begin next_pixel_edge=next_pixel_edge+HALF_PIXEL_NS;#(next_pixel_edge-$realtime)pixel_clk=~pixel_clk;end
 reg reset=1,pixel_reset_n=0,start=0,second=0,feeding=0,iv=0,il=0,allow_sample=1,abort_job=0;
 reg[15:0]hud_golden[0:21119];integer hud_seen=0;
 reg[7:0]ib=0,fixture[0:PACKET-1],expected[0:N-1];reg[15:0]column_words[0:N/2-1],rgb[0:345599];
 wire sr,ir,bq,fv,qp,pp,rp,last_aborted,last_failed,job,frb,hs,vs,de;
 wire[31:0]promotions,underruns,start_cycle,qual_cycle;wire[63:0]last_owner;wire[127:0]first_tag;
 wire[7:0]red,green,blue;wire[9:0]px,py;
 wire[12:0]a;wire[1:0]ba,cke,cs;wire[15:0]dq;wire sclk,ras,cas,we,lm,um;
 cp23_key_composite_scanout dut(.clk(clk),.read_clk(read_clk),.pixel_clk(pixel_clk),.reset(reset),.pixel_reset_n(pixel_reset_n),
  .start_valid(start),.start_ready(sr),.payload_valid(iv),.payload_ready(ir),.payload_byte(ib),.payload_last(il),.sample_enable(allow_sample),.abort_job(abort_job),
  .base_qualified(bq),.front_valid(fv),.promotion_count(promotions),.qualified_pulse(qp),.promoted_pulse(pp),.released_pulse(rp),
  .job_active_out(job),.lcd_underruns(underruns),.frame_boundary(frb),
  .red(red),.green(green),.blue(blue),.hsync(hs),.vsync(vs),.data_enable(de),.physical_x(px),.physical_y(py),
  .sdram_a(a),.sdram_bs(ba),.sdram_dq(dq),.sdram_clk(sclk),.sdram_cke(cke),.sdram_cs_n(cs),.sdram_ras_n(ras),.sdram_cas_n(cas),.sdram_we_n(we),.sdram_ldqm(lm),.sdram_udqm(um));
 sdram_model_burst #(.MEM_WORDS(1572865)) model(.clk(sclk),.a(a),.ba(ba),.cke(cke),.cs(cs),.ras(ras),.cas(cas),.we(we),.ldqm(lm),.udqm(um),.dq(dq));
 integer failed_since=0;reg pending_abort_sent=0;reg phase_abort_sent=0;integer phase_abort_cycle=0;
 reg result_fault_edge_checked=0;
 integer cycle=0,input_count=0,samples=0,hash_samples=0,i,j;
 integer sink_stalls=0,sha_stalls=0,transpose_stalls=0,first_samples=0,first_hash_samples=0,first_input=0,first_writes=0;
 integer first_sink_stalls=0,first_sha_stalls=0,first_transpose_stalls=0,first_fifo_peak=0,first_bank_peak=0;
 integer write_seen=0,first_physical=0,second_physical=0,write_address=0,second_abort_cycle=0,second_release_cycle=0;
 integer background_pixels=0,background_blank=0,background_latches=0,canvas=0,margins=0,blank=0,mismatches=0,misses=0,latches=0;
 integer post_origins=0,accepted_lines=0,completed_lines=0,line_words=0,line_column=0,line_begin=0,max_line_cycles=0,min_line_cycles=999999;
 integer line_log,shadow_x=0,shadow_y=0,raster_edges=0;
 reg watching=0,second_released=0,abort_scheduled=0;realtime line_ns;
 wire[15:0]panel_rgb={red[7:3],green[7:2],blue[7:3]};
 task check_first_region;
  begin
   for(j=0;j<N/2;j=j+1)if(model.mem[BASE+j]!==column_words[j])$fatal(1,"physical first column mismatch index=%0d got=%h expected=%h",j,model.mem[BASE+j],column_words[j]);
   if(model.mem[BASE-1]!==16'h1357||model.mem[BASE+N/2]!==16'h2468||model.mem[SECOND-1]!==16'h5a5a||model.mem[SECOND+N/2]!==16'h369c||model.mem[24'h180000]!==16'h7bd1)$fatal(1,"nonalias guards");
  end
 endtask

 reg stage_was_held=0;reg[202:0]held_stage_tuple;integer stage_in=0,stage_out=0,stage_holds=0;
 always @(posedge clk)begin
  if(reset||dut.go||dut.stop_job||dut.join_failed||dut.failed||dut.aborted||dut.tfailed||dut.taborted||dut.boundary_fault||dut.word_discard_q)begin stage_was_held<=0;stage_in=0;stage_out=0;end
  else begin
   if(stage_was_held&&(!dut.sv||dut.yuv_stage_tuple!==held_stage_tuple))$fatal(1,"canonical ownership stage changed/withdrew under backpressure");
   if(stage_in-stage_out!=dut.yuv_stage_valid||stage_in-stage_out<0||stage_in-stage_out>1)$fatal(1,"canonical ownership stage reservation mismatch");
   if(dut.raw_sv&&dut.yuv_stage_ready)stage_in=stage_in+1;
   if(dut.sv&&dut.store_ready&&allow_sample)stage_out=stage_out+1;
   stage_was_held<=dut.sv&&!(dut.store_ready&&allow_sample);
   if(dut.sv&&!(dut.store_ready&&allow_sample))begin held_stage_tuple<=dut.yuv_stage_tuple;stage_holds=stage_holds+1;end
   if(dut.good_done&&(stage_in!=518400||stage_out!=518400||stage_holds==0))$fatal(1,"canonical stage complete/stall coverage missing");
  end
 end
 reg wh=0,hh=0;reg[167:0]wt;reg[225:0]ht;
 integer wi=0,wo=0,hi=0,ho=0,word_holds=0,hud_holds=0,extra_after_error=0,total_word_captures=0;
 reg injected=0;integer injected_cycle=0;
 always @(posedge clk)begin
  if(reset||dut.go||dut.stop_job||dut.join_failed||dut.failed||dut.aborted||dut.tfailed||dut.taborted||dut.boundary_fault||dut.word_discard_q||dut.old_discard)begin wh<=0;hh<=0;wi=0;wo=0;hi=0;ho=0;end
  else begin
   if(wh&&(!dut.word_stage_valid||dut.word_stage_tuple!==wt))$fatal(1,"word tuple changed under stall");
   if(hh&&(!dut.hud_stage_valid||dut.hud_stage_tuple!==ht))$fatal(1,"HUD tuple changed under stall");
   if(wi-wo!=dut.word_stage_valid||hi-ho!=dut.hud_stage_valid||wi-wo<0||wi-wo>1||hi-ho<0||hi-ho>1)$fatal(1,"boundary reservation mismatch");
   if(dut.hud_stage_valid&&dut.hud_ready)$fatal(1,"HUD bypass reintroduced");
   if(dut.word_capture)wi=wi+1;if(dut.word_forward)wo=wo+1;
   if(dut.hud_capture)hi=hi+1;if(dut.hud_consume)ho=ho+1;
   wh<=dut.word_stage_valid&&!dut.word_forward;
   hh<=dut.hud_stage_valid&&!dut.hud_consume;
   if(dut.word_stage_valid&&!dut.word_forward)begin wt<=dut.word_stage_tuple;word_holds=word_holds+1;end
   if(dut.hud_stage_valid&&!dut.hud_consume)begin ht<=dut.hud_stage_tuple;hud_holds=hud_holds+1;end
   if(dut.good_done)begin
    if(wi!=259200||wo!=259200||hi!=21120||ho!=21120)$fatal(1,"boundary counts wi=%0d wo=%0d hi=%0d ho=%0d word_holds=%0d",wi,wo,hi,ho,word_holds);
    $display("BOUNDARY_COUNTS captured=%0d forwarded=%0d hud_captured=%0d hud_consumed=%0d word_holds=%0d hud_holds=%0d",wi,wo,hi,ho,word_holds,hud_holds);
   end
  end
  if(!reset&&dut.word_capture)total_word_captures=total_word_captures+1;
  if(PRIVATE_ERROR==2&&injected&&dut.old_pixel_address==24'h100001&&(dut.old_pixel_ready||dut.word_capture))$fatal(1,"invalid offered word handshook");
  if(!reset&&job&&dut.old_discard&&!dut.stop_job&&!dut.join_failed&&dut.word_forward)extra_after_error=extra_after_error+1;
  if(extra_after_error>1)$fatal(1,"more than one valid staged word forwarded after private error");
  if((dut.good_done||rp)&&(dut.word_stage_valid||dut.hud_stage_valid||dut.word_discard_q))$fatal(1,"qualification/release with pending boundary state");
  if(PRIVATE_ERROR&&rp)begin
   if(!injected||bq||fv||promotions||dut.store_owner||dut.transpose_owner||!dut.sr||!dut.ts||!dut.js||dut.cv||!dut.jq||!dut.raw_idle||!dut.joined_idle||model.write_left||model.interrupts)$fatal(1,"private boundary error escaped or failed positive release");
   if(PRIVATE_ERROR==1&&(extra_after_error!=1||word_holds==0||model.writes<8||model.writes%8))$fatal(1,"delayed private error/retained burst coverage missing");
   if(PRIVATE_ERROR==2&&(total_word_captures||model.writes))$fatal(1,"invalid incoming word accepted");
   if(PRIVATE_ERROR==3&&dut.hud_stored)$fatal(1,"invalid captured HUD tuple wrote RAM");
   $display("CP23_BOUNDARY_PRIVATE_ERROR_PASS mode=%0d cycle=%0d injection=%0d extra_valid_words=%0d physical=%0d hud_stored=%0d word_holds=%0d join_stage=%0d join_code=%0d",PRIVATE_ERROR,cycle,injected_cycle,extra_after_error,model.writes,dut.hud_stored,word_holds,dut.key_stage,dut.join_code);$finish;
  end
  if(injected&&cycle-injected_cycle>50000)$fatal(1,"private boundary error did not reach bounded positive release");
 end
 // Bounded offline fault injection into existing private producer signals.
 initial if(PRIVATE_ERROR==1)begin
  wait(!reset);wait(job);wait(dut.word_stage_valid);@(negedge clk);
  force dut.word_forward_ready=0;force dut.word_forward_valid=0;
  repeat(7)@(negedge clk);
  release dut.word_forward_ready;release dut.word_forward_valid;
  while(!injected)begin @(negedge clk);#0.01;
   if(model.write_left>0&&dut.word_stage_valid&&dut.word_forward_ready&&dut.sv&&allow_sample&&dut.store_ready)begin
    force dut.sample_owner=64'h123456789abcdef1;injected=1;injected_cycle=cycle;
    @(negedge clk);release dut.sample_owner;
   end
  end
 end
 initial if(PRIVATE_ERROR==2)begin
  wait(!reset);wait(job);
  wait(dut.old_pixel_valid&&dut.word_captured==0);@(negedge clk);
  force dut.old_pixel_address=24'h100001;injected=1;injected_cycle=cycle;
  @(negedge clk);release dut.old_pixel_address;
 end
 initial if(PRIVATE_ERROR==3)begin
  wait(!reset);wait(job);wait(dut.hud_valid&&dut.hud_ready);@(negedge clk);
  force dut.raw_owner=64'h123456789abcdef1;injected=1;injected_cycle=cycle;
  @(negedge clk);release dut.raw_owner;
 end
 // Exercise a held complete HUD tuple before the partial-HUD cancellation.
 initial if(ABORT_MODE==2)begin
  wait(!reset);wait(dut.hud_stage_valid);@(negedge clk);
  force dut.hud_consume=0;repeat(7)@(negedge clk);release dut.hud_consume;
 end
 // Natural late-tag result raises store discard on the same cycle as CV.
 // On the next edge both registered result-seen and discard must settle without
 // feeding the result mask back into a new abort request or changing its reason.
 always @(posedge clk)if(!reset&&CASE==2&&dut.cv&&!dut.join_result_seen)begin
  if(dut.key_stage!=4||dut.join_code!=6||!dut.old_discard||dut.word_discard_q||dut.boundary_abort_request)$fatal(1,"result/fault observation arbitration invalid");
  #0.01;
  if(!dut.join_result_seen||!dut.word_discard_q||dut.boundary_abort_request||!dut.cv||dut.key_stage!=4||dut.join_code!=6)$fatal(1,"registered result/fault fence changed late-tag reason");
  result_fault_edge_checked=1;
  $display("RESULT_FAULT_EDGE_PASS seen=%b discard=%b abort=%b stage=%0d code=%0d",dut.join_result_seen,dut.word_discard_q,dut.boundary_abort_request,dut.key_stage,dut.join_code);
 end
 always @(posedge clk)begin
  cycle=cycle+1;
  if(!reset)begin
   if(cycle%1000000==0)begin $display("PROGRESS cycle=%0d join=%0d store=%0d trans=%0d samples=%0d hud=%0d front=%b",cycle,dut.key.state,dut.store_state,dut.transpose_state,samples,hud_seen,fv);$fflush();end
   if(iv&&ir&&job)input_count=input_count+1;
   if(dut.sv&&dut.store_ready&&allow_sample)begin
    if(samples>=N||dut.sample!==expected[samples]||dut.sample_owner!==64'h123456789abcdef0||dut.sample_epoch!=1||dut.sample_frame!=0||dut.sample_gen!=1)$fatal(1,"canonical sample/identity mismatch index=%0d",samples);
    samples=samples+1;
   end
   if(dut.hud_valid&&dut.hud_ready)begin
    if(hud_seen>=21120||dut.hud_word!==hud_golden[hud_seen])$fatal(1,"actual decoded HUD mismatch index=%0d",hud_seen);
    hud_seen=hud_seen+1;
   end
   if(dut.ack||dut.pub||dut.cap)$fatal(1,"private joint unexpectedly advertised protocol result");
   if(dut.request_valid&&(dut.request_owner!==64'h123456789abcdef0||dut.request_epoch!=1||dut.request_frame!=0))$fatal(1,"front read identity");
   if(dut.request_rejected||dut.gather_faults)$fatal(1,"owned gather rejected/faulted");
   if(!bq&&dut.request_valid)$fatal(1,"read before complete pair and physical drain");
   if(dut.good_done)begin
    if(CASE!=0||ABORT_MODE!=0||PRIVATE_ERROR!=0)$fatal(1,"bad/canceled candidate published success");
    if(!dut.raw_idle||!dut.joined_idle||model.write_left!=0||samples!=N||hud_seen!=21120||input_count!=PACKET||model.writes!=N/2||!dut.jq)$fatal(1,"joint/tag/physical certificate failure");
    check_first_region();
    for(j=0;j<21120;j=j+1)if(dut.hud_ram[j]!==hud_golden[j])$fatal(1,"fresh HUD RAM mismatch %0d",j);
    $display("CP23_PAIR_PHYSICAL_CERTIFICATE cycle=%0d encoded=%0d canonical=%0d hud=%0d physical_words=%0d base_tag=%032h hud_tag=%032h",cycle,input_count,samples,hud_seen,model.writes,dut.completion_tag,dut.hud_tag);
   end
   if(ABORT_MODE!=0&&rp)begin
    if(!phase_abort_sent||bq||fv||promotions||dut.store_owner!=0||dut.transpose_owner!=0||!dut.sr||!dut.ts||!dut.js||dut.cv||!dut.jq||!dut.raw_idle||!dut.joined_idle||model.write_left||model.interrupts)$fatal(1,"phase abort did not drain/release safely");
    if(ABORT_MODE==1&&(model.writes<8||model.writes%8!=0))$fatal(1,"physical burst cancellation coverage missing");
    if(ABORT_MODE==2&&(hud_seen<100||hud_seen>=21120||model.writes!=259200))$fatal(1,"partial HUD cancellation coverage missing");
    $display("CP23_PHASE_ABORT_PASS mode=%0d cycle=%0d abort_cycle=%0d samples=%0d hud=%0d physical=%0d",ABORT_MODE,cycle,phase_abort_cycle,samples,hud_seen,model.writes);$finish;
   end
   if(ABORT_PENDING&&rp)begin
    if(!pending_abort_sent||bq||fv||promotions||dut.store_owner!=0||dut.transpose_owner!=0||!dut.sr||!dut.ts||!dut.js||dut.cv||!dut.jq||!dut.raw_idle||!dut.joined_idle)$fatal(1,"pending abort did not cancel publication or release ownership");
    $display("CP23_PENDING_ABORT_PASS cycle=%0d samples=%0d hud=%0d physical=%0d",cycle,samples,hud_seen,model.writes);$finish;
   end
   if(CASE!=0&&rp)begin
    if(CASE==2&&!result_fault_edge_checked)$fatal(1,"result/fault edge coverage missing");
    case(CASE)
     1:if(dut.key_stage!=2||dut.join_code!=4)$fatal(1,"wrong outer CRC rejection reason");
     2:if(dut.key_stage!=4||dut.join_code!=6)$fatal(1,"wrong HUD tag rejection reason");
     3:if(dut.key_stage!=3||dut.join_code!=6)$fatal(1,"wrong base CRC rejection reason");
     4:if(dut.key_stage!=4||dut.join_code!=5)$fatal(1,"wrong HUD CRC rejection reason");
     5:if(dut.key_stage!=3||dut.join_code!=3)$fatal(1,"wrong base tag rejection reason");
    endcase

    if(bq||fv||promotions||!dut.raw_idle||!dut.joined_idle||model.write_left||dut.key.candidate_checked||dut.store_owner!=0||dut.transpose_owner!=0||!dut.sr||!dut.ts||!dut.js||dut.cv||!dut.jq)$fatal(1,"failed pair escaped/drain unsafe");
    $display("CP23_COMPOSITE_NEGATIVE_PASS case=%0d cycle=%0d stage=%0d code=%0d samples=%0d hud=%0d physical=%0d",CASE,cycle,dut.key_stage,dut.join_code,samples,hud_seen,model.writes);$finish;
   end
   if(pp)begin if(!bq||!dut.primed||promotions!=1)$fatal(1,"invalid publication");watching=1;post_origins=0;$display("COMPOSITE_PROMOTED cycle=%0d",cycle);end
   if(dut.line_req_valid&&dut.line_req_ready)begin accepted_lines=accepted_lines+1;line_column=dut.line_req_address/480;line_words=0;line_begin=cycle;line_ns=$realtime;end
   if(dut.line_data_valid)begin
    if(dut.line_data!==rgb[line_words*720+line_column])$fatal(1,"composite exact/native mismatch col=%0d row=%0d got=%h expected=%h",line_column,line_words,dut.line_data,rgb[line_words*720+line_column]);
    line_words=line_words+1;
    if(line_words==480)begin completed_lines=completed_lines+1;if(cycle-line_begin>max_line_cycles)max_line_cycles=cycle-line_begin;if(cycle-line_begin<min_line_cycles)min_line_cycles=cycle-line_begin;$fdisplay(line_log,"LINE column=%0d accept=%0d complete=%0d cycles=%0d accept_ns=%0.3f complete_ns=%0.3f",line_column,line_begin,cycle,cycle-line_begin,line_ns,$realtime);end
   end
   if(watching&&frb&&!pp)begin
    post_origins=post_origins+1;
    if(post_origins==2)begin
     check_first_region();
     if(canvas!=691200||margins!=76800||latches!=1440||promotions!=1||model.interrupts!=0||samples!=N||hud_seen!=21120||mismatches||misses||underruns)$fatal(1,"incomplete exact composite display coverage");
     $display("CP23_COMPOSITE_SCANOUT_PASS canvas=%0d margins=%0d latches=%0d misses=%0d underruns=%0d physical=%0d hud=%0d min_line=%0d max_line=%0d requests=%0d responses=%0d refreshes=%0d",canvas,margins,latches,misses,underruns,model.writes,hud_seen,min_line_cycles,max_line_cycles,dut.gather_requests,dut.gather_responses,model.refreshes);$fclose(line_log);$finish;
    end
   end
  end
  if(phase_abort_sent&&cycle-phase_abort_cycle>50000)$fatal(1,"phase abort did not reach bounded positive release");
  if(CASE!=0&&dut.cv&&!dut.checked)begin if(failed_since==0)failed_since=cycle; if(cycle-failed_since>10000)$fatal(1,"failed pair retained after terminal and bounded drain join=%0d store=%0d trans=%0d raw_idle=%b joined_idle=%b",dut.key.state,dut.store_state,dut.transpose_state,dut.raw_idle,dut.joined_idle);end
  if(cycle>(SMOKE?150000:12000000))$fatal(1,"bounded composite timeout join=%0d code=%0d store=%0d transpose=%0d front=%b",dut.key.state,dut.join_code,dut.store_state,dut.transpose_state,fv);
 end
 always @(negedge clk)begin
  allow_sample=cycle%41<34;
  if(ABORT_MODE!=0&&!phase_abort_sent&&((ABORT_MODE==1&&model.write_left>0)||(ABORT_MODE==2&&hud_seen>=100&&hud_seen<21120&&dut.tdone)))begin abort_job=1;phase_abort_sent=1;phase_abort_cycle=cycle;end
  else if(phase_abort_sent)abort_job=0;
  if(ABORT_PENDING&&dut.release_pending&&dut.release_success&&!pending_abort_sent)begin abort_job=1;pending_abort_sent=1;end else if(pending_abort_sent)abort_job=0;
  iv=feeding&&job&&input_count<PACKET&&cycle%23!=0;ib=input_count<PACKET?fixture[input_count]:0;il=input_count==PACKET-1;
 end
 always @(posedge model.device_clock)begin
  #0.001;
  if(model.writes!=write_seen)begin
   if(model.writes!=write_seen+1)$fatal(1,"missed physical beat");write_address=model.writeaddr-1;
   if(write_address<BASE||write_address>=BASE+N/2||bq)$fatal(1,"unowned/mutated immutable physical write");
   if(model.mem[write_address]!==column_words[write_address-BASE]||lm||um)$fatal(1,"physical data/mask mismatch");write_seen=model.writes;
  end
 end
 // Continuous independent raster progression; never reset for prime/promotion/abort.
 always @(posedge pixel_clk)begin
  if(!pixel_reset_n)begin shadow_x=0;shadow_y=0;end
  else begin
   if(dut.lcd.x!==shadow_x||dut.lcd.y!==shadow_y)$fatal(1,"LCD timing reset/jump x=%0d y=%0d expected=%0d/%0d",dut.lcd.x,dut.lcd.y,shadow_x,shadow_y);
   raster_edges=raster_edges+1;
   if(shadow_x==540)begin shadow_x=0;if(shadow_y==833)shadow_y=0;else shadow_y=shadow_y+1;end else shadow_x=shadow_x+1;
   if(dut.lcd.x==13&&dut.lcd.y>=37&&dut.lcd.y<757)begin
    #0.001;
    if(watching)begin
     latches=latches+1;if(!dut.lcd.line_good)misses=misses+1;
     $fdisplay(line_log,"NEED column=%0d latch_ns=%0.3f line_good=%b sampling_offset_ns=0.001",dut.lcd.y-37,$realtime,dut.lcd.line_good);
    end else background_latches=background_latches+1;
   end
  end
 end
 always @(negedge pixel_clk)if(pixel_reset_n)begin
  if(!watching)begin
   if({red,green,blue}!==0)$fatal(1,"nonblack declared background before promotion");
   if(de)background_pixels=background_pixels+1;else background_blank=background_blank+1;
  end else if(de)begin
   if(py>=13&&py<733)begin
    canvas=canvas+1;
    if(panel_rgb!==rgb[px*720+py-13])begin
     mismatches=mismatches+1;if(mismatches<=8)$display("NATIVE_PANEL_MISMATCH x=%0d y=%0d got=%h expected=%h scan_good=%b",py-13,px,panel_rgb,rgb[px*720+py-13],dut.lcd.scan_good);
    end
   end else begin margins=margins+1;if({red,green,blue}!==0)$fatal(1,"nonblack margin");end
  end else begin blank=blank+1;if({red,green,blue}!==0)$fatal(1,"nonblack blanking");end
 end

 initial begin
  line_log=$fopen("line-timing.log","w");
  $readmemh("fixture.hex",fixture);$readmemh("expected.hex",expected);$readmemh("column.hex",column_words);$readmemh("composite.hex",rgb);$readmemh("hud.hex",hud_golden);
  model.mem[BASE-1]=16'h1357;model.mem[BASE+N/2]=16'h2468;model.mem[SECOND-1]=16'h5a5a;model.mem[SECOND+N/2]=16'h369c;model.mem[24'h180000]=16'h7bd1;
  repeat(8)@(negedge clk);reset=0;@(negedge pixel_clk);pixel_reset_n=1;
  wait(sr);@(negedge clk);start=1;@(negedge clk);start=0;feeding=1;
  if(RESET_LOAD)begin
   wait(input_count>=1000);@(negedge clk);feeding=0;iv=0;reset=1;pixel_reset_n=0;
   if(model.writes||samples||hud_seen)$fatal(1,"LOAD reset occurred after private output");
   repeat(8)@(negedge clk);input_count=0;reset=0;@(negedge pixel_clk);pixel_reset_n=1;
   if(dut.key.complete_store||dut.key.read_enable||dut.hud_stored||bq||fv)$fatal(1,"LOAD reset leaked prior validity");
   wait(sr);@(negedge clk);start=1;@(negedge clk);start=0;feeding=1;
  end
  if(SMOKE)begin
   wait(cycle>=5000);@(negedge clk);feeding=0;iv=0;abort_job=1;@(negedge clk);abort_job=0;
   wait(rp);@(negedge clk);
   if(bq||fv||promotions||dut.accepted_bytes||dut.gather_requests||model.writes||raster_edges<2000)$fatal(1,"smoke did not preserve background/cancel safety");
   $display("CP23_COMPOSITE_SMOKE_PASS cycles=%0d encoded=%0d background=%0d",cycle,input_count,background_pixels);$finish;
  end
 end
endmodule
