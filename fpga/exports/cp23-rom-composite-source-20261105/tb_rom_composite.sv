`timescale 1ns/1ps
module tb;
 parameter MODE=0;
 localparam SMOKE=(MODE==1),CASE=0,ABORT_PENDING=(MODE==5),ABORT_MODE=(MODE==2?1:0),RESET_LOAD=(MODE==3||MODE==4);
 localparam N=518400,PACKET=17412,BASE=24'h100000,SECOND=24'h140000;
 reg clk=0;always #5 clk=~clk;wire read_clk;assign #2.75 read_clk=~clk;
 reg pixel_clk=0;realtime next_pixel_edge=0;
 localparam realtime HALF_PIXEL_NS=1.0e9/(2.0*(50.0e6*56.375/3.0/32.0));
 initial forever begin next_pixel_edge=next_pixel_edge+HALF_PIXEL_NS;#(next_pixel_edge-$realtime)pixel_clk=~pixel_clk;end
 reg reset=1,pixel_reset_n=0,local_start=0,local_cancel=0;
 wire allow_sample=1'b1;
 reg[15:0]hud_golden[0:21119];integer hud_seen=0;
 wire[7:0]ib=dut.payload_byte;reg[7:0]fixture[0:PACKET-1],expected[0:N-1];reg[15:0]column_words[0:N/2-1],rgb[0:345599];
 wire bq,fv,qp,pp,rp,last_aborted,last_failed,frb,hs,vs,de;
 wire sr=dut.start_ready,ir=dut.payload_ready,iv=dut.payload_valid,il=dut.payload_last,job=dut.job_active;
 wire loader_busy,local_accepted,local_rejected,loader_done,loader_cancelled,started_once,reconfiguration,boot_rp,idle_cert;
 wire[31:0]loader_bytes,rejected;
 wire[31:0]promotions,underruns,start_cycle,qual_cycle;wire[63:0]last_owner;wire[127:0]first_tag;
 wire[7:0]red,green,blue;wire[9:0]px,py;
 wire[12:0]a;wire[1:0]ba,cke,cs;wire[15:0]dq;wire sclk,ras,cas,we,lm,um;
 cp23_rom_composite dut(.clk(clk),.read_clk(read_clk),.pixel_clk(pixel_clk),.reset(reset),.pixel_reset_n(pixel_reset_n),
  .local_start(local_start),.local_cancel(local_cancel),.loader_busy(loader_busy),.local_start_accepted(local_accepted),.local_start_rejected(local_rejected),
  .rejected_starts(rejected),.bytes_sent(loader_bytes),.load_complete(loader_done),.loader_cancelled(loader_cancelled),
  .consumer_started_once(started_once),.reconfigure_required(reconfiguration),.bootstrap_released_pulse(boot_rp),.consumer_job_released_pulse(rp),.idle_certificate(idle_cert),
  .base_qualified(bq),.front_valid(fv),.promotion_count(promotions),.qualified_pulse(qp),.promoted_pulse(pp),
  .lcd_underruns(underruns),.frame_boundary(frb),
  .red(red),.green(green),.blue(blue),.hsync(hs),.vsync(vs),.data_enable(de),.physical_x(px),.physical_y(py),
  .sdram_a(a),.sdram_bs(ba),.sdram_dq(dq),.sdram_clk(sclk),.sdram_cke(cke),.sdram_cs_n(cs),.sdram_ras_n(ras),.sdram_cas_n(cas),.sdram_we_n(we),.sdram_ldqm(lm),.sdram_udqm(um));
 sdram_model_burst #(.MEM_WORDS(1572865)) model(.clk(sclk),.a(a),.ba(ba),.cke(cke),.cs(cs),.ras(ras),.cas(cas),.we(we),.ldqm(lm),.udqm(um),.dq(dq));
 integer boot_releases=0,job_releases=0,consumer_starts=0,core_aborts=0;
 reg ever_observed=0,reset_issued=0;
 always @(posedge clk)begin
  if(boot_rp)boot_releases=boot_releases+1;
  if(rp)job_releases=job_releases+1;
  if(dut.start_valid&&dut.start_ready)consumer_starts=consumer_starts+1;
  if(dut.core_abort_job)core_aborts=core_aborts+1;
  if(started_once)ever_observed=1;
  if(ever_observed&&!started_once)$fatal(1,"configuration ownership flag erased by logical reset");
  if(dut.consumer_released&&(!idle_cert||reset||reconfiguration))$fatal(1,"unqualified loader release");
  if(dut.consumer_released&&started_once&&!dut.release_seen)$fatal(1,"job release pulse not retained");
  if(started_once&&dut.permitted_start)$fatal(1,"repeat local START admitted");
  if(consumer_starts>1)$fatal(1,"consumer started more than once");
  if(core_aborts>1)$fatal(1,"held cancel repeated consumer abort");
 end
 integer failed_since=0;reg pending_abort_sent=0;reg phase_abort_sent=0;integer phase_abort_cycle=0;
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

 always @(posedge clk)begin
  cycle=cycle+1;
  if(!reset)begin
   if(cycle%1000000==0)begin $display("PROGRESS cycle=%0d join=%0d store=%0d trans=%0d samples=%0d hud=%0d front=%b",cycle,dut.core.key.state,dut.core.store_state,dut.core.transpose_state,samples,hud_seen,fv);$fflush();end
   if(iv&&ir&&job)begin
    if(input_count>=PACKET||ib!==fixture[input_count]||il!==(input_count==PACKET-1))$fatal(1,"real ROM payload mismatch %0d",input_count);
    input_count=input_count+1;
   end
   if(dut.core.sv&&dut.core.store_ready&&allow_sample)begin
    if(samples>=N||dut.core.sample!==expected[samples]||dut.core.sample_owner!==64'h123456789abcdef0||dut.core.sample_epoch!=1||dut.core.sample_frame!=0||dut.core.sample_gen!=1)$fatal(1,"canonical sample/identity mismatch index=%0d",samples);
    samples=samples+1;
   end
   if(dut.core.hud_valid&&dut.core.hud_ready)begin
    if(hud_seen>=21120||dut.core.hud_word!==hud_golden[hud_seen])$fatal(1,"actual decoded HUD mismatch index=%0d",hud_seen);
    hud_seen=hud_seen+1;
   end
   if(dut.core.ack||dut.core.pub||dut.core.cap)$fatal(1,"private joint unexpectedly advertised protocol result");
   if(dut.core.request_valid&&(dut.core.request_owner!==64'h123456789abcdef0||dut.core.request_epoch!=1||dut.core.request_frame!=0))$fatal(1,"front read identity");
   if(dut.core.request_rejected||dut.core.gather_faults)$fatal(1,"owned gather rejected/faulted");
   if(!bq&&dut.core.request_valid)$fatal(1,"read before complete pair and physical drain");
   if(dut.core.good_done)begin
    if(CASE!=0||ABORT_MODE!=0)$fatal(1,"bad/canceled candidate published success");
    if(!dut.core.raw_idle||!dut.core.joined_idle||model.write_left!=0||samples!=N||hud_seen!=21120||input_count!=PACKET||model.writes!=N/2||!dut.core.jq)$fatal(1,"joint/tag/physical certificate failure");
    check_first_region();
    for(j=0;j<21120;j=j+1)if(dut.core.hud_ram[j]!==hud_golden[j])$fatal(1,"fresh HUD RAM mismatch %0d",j);
    $display("CP23_PAIR_PHYSICAL_CERTIFICATE cycle=%0d encoded=%0d canonical=%0d hud=%0d physical_words=%0d base_tag=%032h hud_tag=%032h",cycle,input_count,samples,hud_seen,model.writes,dut.core.completion_tag,dut.core.hud_tag);
   end
   if(ABORT_MODE!=0&&rp)begin
    if(loader_busy||!idle_cert||boot_releases!=1||core_aborts!=1||!local_cancel||!started_once||reconfiguration)$fatal(1,"held physical cancel wrapper fence");
    if(!phase_abort_sent||bq||fv||promotions||dut.core.store_owner!=0||dut.core.transpose_owner!=0||!dut.core.sr||!dut.core.ts||!dut.core.js||dut.core.cv||!dut.core.jq||!dut.core.raw_idle||!dut.core.joined_idle||model.write_left||model.interrupts)$fatal(1,"phase abort did not drain/release safely");
    if(ABORT_MODE==1&&(model.writes<8||model.writes%8!=0))$fatal(1,"physical burst cancellation coverage missing");
    if(ABORT_MODE==2&&(hud_seen<100||hud_seen>=21120||model.writes!=259200))$fatal(1,"partial HUD cancellation coverage missing");
    $display("CP23_ROM_PHYSICAL_ABORT_PASS mode=%0d cycle=%0d abort_cycle=%0d samples=%0d hud=%0d physical=%0d",ABORT_MODE,cycle,phase_abort_cycle,samples,hud_seen,model.writes);$finish;
   end
   if(ABORT_PENDING&&rp)begin
    if(loader_busy||!idle_cert||boot_releases!=1||core_aborts!=1||!local_cancel||!started_once||reconfiguration)$fatal(1,"pending cancel wrapper fence");
    if(!pending_abort_sent||bq||fv||promotions||dut.core.store_owner!=0||dut.core.transpose_owner!=0||!dut.core.sr||!dut.core.ts||!dut.core.js||dut.core.cv||!dut.core.jq||!dut.core.raw_idle||!dut.core.joined_idle)$fatal(1,"pending abort did not cancel publication or release ownership");
    $display("CP23_ROM_PENDING_ABORT_PASS cycle=%0d samples=%0d hud=%0d physical=%0d",cycle,samples,hud_seen,model.writes);$finish;
   end
   if(CASE!=0&&rp)begin
    if(bq||fv||promotions||!dut.core.raw_idle||!dut.core.joined_idle||model.write_left||dut.core.key.candidate_checked||dut.core.store_owner!=0||dut.core.transpose_owner!=0||!dut.core.sr||!dut.core.ts||!dut.core.js||dut.core.cv||!dut.core.jq)$fatal(1,"failed pair escaped/drain unsafe");
    $display("CP23_COMPOSITE_NEGATIVE_PASS case=%0d cycle=%0d stage=%0d code=%0d samples=%0d hud=%0d physical=%0d",CASE,cycle,dut.core.key_stage,dut.core.join_code,samples,hud_seen,model.writes);$finish;
   end
   if(pp)begin if(!bq||!dut.core.primed||promotions!=1)$fatal(1,"invalid publication");watching=1;post_origins=0;$display("COMPOSITE_PROMOTED cycle=%0d",cycle);end
   if(dut.core.line_req_valid&&dut.core.line_req_ready)begin accepted_lines=accepted_lines+1;line_column=dut.core.line_req_address/480;line_words=0;line_begin=cycle;line_ns=$realtime;end
   if(dut.core.line_data_valid)begin
    if(dut.core.line_data!==rgb[line_words*720+line_column])$fatal(1,"composite exact/native mismatch col=%0d row=%0d got=%h expected=%h",line_column,line_words,dut.core.line_data,rgb[line_words*720+line_column]);
    line_words=line_words+1;
    if(line_words==480)begin completed_lines=completed_lines+1;if(cycle-line_begin>max_line_cycles)max_line_cycles=cycle-line_begin;if(cycle-line_begin<min_line_cycles)min_line_cycles=cycle-line_begin;$fdisplay(line_log,"LINE column=%0d accept=%0d complete=%0d cycles=%0d accept_ns=%0.3f complete_ns=%0.3f",line_column,line_begin,cycle,cycle-line_begin,line_ns,$realtime);end
   end
   if(watching&&frb&&!pp)begin
    post_origins=post_origins+1;
    if(post_origins==2)begin
     check_first_region();
     if(loader_busy||loader_bytes!=PACKET||!loader_done||job_releases!=1||boot_releases!=1||consumer_starts!=1||!rejected||core_aborts||reconfiguration)$fatal(1,"full ROM ownership/status fence");
     if(canvas!=691200||margins!=76800||latches!=1440||promotions!=1||model.interrupts!=0||samples!=N||hud_seen!=21120||mismatches||misses||underruns)$fatal(1,"incomplete exact composite display coverage");
     $display("CP23_ROM_COMPOSITE_SCANOUT_PASS canvas=%0d margins=%0d latches=%0d misses=%0d underruns=%0d physical=%0d hud=%0d min_line=%0d max_line=%0d requests=%0d responses=%0d refreshes=%0d",canvas,margins,latches,misses,underruns,model.writes,hud_seen,min_line_cycles,max_line_cycles,dut.core.gather_requests,dut.core.gather_responses,model.refreshes);$fclose(line_log);$finish;
    end
   end
  end
  if(phase_abort_sent&&cycle-phase_abort_cycle>50000)$fatal(1,"phase abort did not reach bounded positive release");
  if(CASE!=0&&dut.core.cv&&!dut.core.checked)begin if(failed_since==0)failed_since=cycle; if(cycle-failed_since>10000)$fatal(1,"failed pair retained after terminal and bounded drain join=%0d store=%0d trans=%0d raw_idle=%b joined_idle=%b",dut.core.key.state,dut.core.store_state,dut.core.transpose_state,dut.core.raw_idle,dut.core.joined_idle);end
  if(cycle>((MODE==1||MODE==3||MODE==6||MODE==7)?250000:12000000))$fatal(1,"bounded composite timeout join=%0d code=%0d store=%0d transpose=%0d front=%b",dut.core.key.state,dut.core.join_code,dut.core.store_state,dut.core.transpose_state,fv);
 end
 always @(negedge clk)begin
  if(MODE==2&&!phase_abort_sent&&model.write_left>0)begin
   local_cancel=1;phase_abort_sent=1;phase_abort_cycle=cycle;
  end
  if(MODE==5&&dut.core.release_pending&&dut.core.release_success&&!pending_abort_sent)begin
   local_cancel=1;pending_abort_sent=1;
  end
 end
 always @(posedge model.device_clock)begin
  #0.001;
  if(model.writes!=write_seen&&!(MODE==4&&reset_issued))begin
   if(model.writes!=write_seen+1)$fatal(1,"missed physical beat");write_address=model.writeaddr-1;
   if(write_address<BASE||write_address>=BASE+N/2||bq)$fatal(1,"unowned/mutated immutable physical write");
   if(model.mem[write_address]!==column_words[write_address-BASE]||lm||um)$fatal(1,"physical data/mask mismatch");write_seen=model.writes;
  end
 end
 // Continuous independent raster progression; never reset for prime/promotion/abort.
 always @(posedge pixel_clk)begin
  if(!pixel_reset_n)begin shadow_x=0;shadow_y=0;end
  else begin
   if(dut.core.lcd.x!==shadow_x||dut.core.lcd.y!==shadow_y)$fatal(1,"LCD timing reset/jump x=%0d y=%0d expected=%0d/%0d",dut.core.lcd.x,dut.core.lcd.y,shadow_x,shadow_y);
   raster_edges=raster_edges+1;
   if(shadow_x==540)begin shadow_x=0;if(shadow_y==833)shadow_y=0;else shadow_y=shadow_y+1;end else shadow_x=shadow_x+1;
   if(dut.core.lcd.x==13&&dut.core.lcd.y>=37&&dut.core.lcd.y<757)begin
    #0.001;
    if(watching)begin
     latches=latches+1;if(!dut.core.lcd.line_good)misses=misses+1;
     $fdisplay(line_log,"NEED column=%0d latch_ns=%0.3f line_good=%b sampling_offset_ns=0.001",dut.core.lcd.y-37,$realtime,dut.core.lcd.line_good);
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
     mismatches=mismatches+1;if(mismatches<=8)$display("NATIVE_PANEL_MISMATCH x=%0d y=%0d got=%h expected=%h scan_good=%b",py-13,px,panel_rgb,rgb[px*720+py-13],dut.core.lcd.scan_good);
    end
   end else begin margins=margins+1;if({red,green,blue}!==0)$fatal(1,"nonblack margin");end
  end else begin blank=blank+1;if({red,green,blue}!==0)$fatal(1,"nonblack blanking");end
 end

 initial begin
  line_log=$fopen("line-timing.log","w");
  $readmemh("fixture.hex",fixture);$readmemh("expected.hex",expected);$readmemh("column.hex",column_words);$readmemh("composite.hex",rgb);$readmemh("hud.hex",hud_golden);
  model.mem[BASE-1]=16'h1357;model.mem[BASE+N/2]=16'h2468;model.mem[SECOND-1]=16'h5a5a;model.mem[SECOND+N/2]=16'h369c;model.mem[24'h180000]=16'h7bd1;
  repeat(8)@(negedge clk);reset=0;@(negedge pixel_clk);pixel_reset_n=1;
  wait(!loader_busy);repeat(2)@(negedge clk);
  if(boot_releases!=1||!idle_cert||core_aborts||started_once||reconfiguration)$fatal(1,"bootstrap was not fresh positive idle");
  local_start=1; // held through load, release and eventual display
  if(MODE==6)begin
   wait(local_accepted);@(negedge clk);local_cancel=1;
   wait(boot_releases==2);@(negedge clk);
   if(consumer_starts||started_once||core_aborts||loader_busy||!loader_cancelled)$fatal(1,"pre-consumer cancel fabricated ownership/abort");
   local_cancel=0;local_start=0;@(negedge clk);local_start=1;
   wait(consumer_starts==1);@(negedge clk);local_cancel=1;
   if(dut.loader.state!=2)$fatal(1,"FETCH cancel phase not covered");
   wait(rp);repeat(2)@(negedge clk);
   if(loader_busy||input_count||loader_bytes||core_aborts!=1||job_releases!=1||boot_releases!=2||bq||fv||promotions)$fatal(1,"FETCH cancel did not drain actual consumer busy=%b input=%0d bytes=%0d aborts=%0d releases=%0d boot=%0d",loader_busy,input_count,loader_bytes,core_aborts,job_releases,boot_releases);
   $display("CP23_ROM_PRESTART_FETCH_CANCEL_PASS cycle=%0d starts=%0d core_aborts=%0d",cycle,consumer_starts,core_aborts);$finish;
  end
  wait(consumer_starts==1);
  if(MODE==1||MODE==7)begin
   wait(input_count>=1000);@(negedge clk);local_cancel=1;
   if(MODE==7)begin @(negedge clk);local_cancel=0;end
   wait(rp);repeat(2)@(negedge clk);
   if(loader_busy||bq||fv||promotions||dut.core.accepted_bytes||dut.core.gather_requests||model.writes||core_aborts!=1||!loader_cancelled||!started_once||boot_releases!=1)$fatal(1,"ROM LOAD cancel safety");
   repeat(20)@(negedge clk);
   if(consumer_starts!=1||loader_busy)$fatal(1,"held local START restarted after cancel");
   local_cancel=0;local_start=0;@(negedge clk);local_start=1;@(negedge clk);local_start=0;repeat(3)@(negedge clk);
   if(!rejected||consumer_starts!=1||dut.start_valid)$fatal(1,"repeat START after canceled job not rejected");
   $display("CP23_ROM_LOAD_CANCEL_PASS cycle=%0d encoded=%0d starts=%0d rejects=%0d",cycle,input_count,consumer_starts,rejected);$finish;
  end
  if(MODE==3||MODE==4)begin
   if(MODE==3)wait(input_count>=1000);else wait(model.write_left>0);
   @(negedge clk);reset_issued=1;reset=1;
   repeat(8)@(negedge clk);reset=0;
   wait(idle_cert);repeat(100)@(negedge clk);
   if(!started_once||!reconfiguration||!loader_busy||rp||job_releases||boot_releases!=1||iv||dut.start_valid||bq||fv||promotions)$fatal(1,"logical reset silently released consumer ownership");
   local_start=0;@(negedge clk);local_start=1;repeat(8)@(negedge clk);
   if(!loader_busy||consumer_starts!=1||!reconfiguration||!rejected)$fatal(1,"reset allowed unsafe warm restart");
   $display("CP23_ROM_RESET_FENCE_PASS mode=%0d cycle=%0d consumer_starts=%0d physical_words=%0d model_interrupts=%0d requires_configuration=1",MODE,cycle,consumer_starts,model.writes,model.interrupts);$finish;
  end
  if(MODE==0)begin
   wait(rp);repeat(10)@(negedge clk);
   if(loader_busy||!loader_done||consumer_starts!=1||!started_once)$fatal(1,"whole ROM job not positively released");
   local_start=0;@(negedge clk);local_start=1;@(negedge clk);local_start=0;
  end
 end
endmodule
