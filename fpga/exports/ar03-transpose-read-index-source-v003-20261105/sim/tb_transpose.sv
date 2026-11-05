`timescale 1ns/1ps
module tb_transpose;
 parameter FULL_TEST=0;
 localparam BASE=24'h100000,N=259200;
 reg clk=0;always #5 clk=~clk;wire read_clk;assign #2.75 read_clk=~clk;
 reg reset=1,start=0,iv=0,uflush=0,udiscard=1,ab=0,ft=0,rel=0,manual_allow=1,stall_enable=0;
 reg[63:0]so=64'h1020304050607080,io=64'h1020304050607080,ro=64'h1020304050607080;
 reg[31:0]se=1,sf=7,ie=1,ifr=7,re=1,rf=7;
 reg[15:0]sw=720,sh=480,idata=0;reg[23:0]sb=BASE,ia=BASE;
 wire sr,srej,ir,pv,pr,mpr,flush,discard,idle,storeidle,done,failed,aborted,rrej;
 wire[23:0]pa;wire[15:0]pd;wire[63:0]owner;wire[31:0]ins,processed,outs,highwater;wire[3:0]ec,state;
 wire[12:0]a;wire[1:0]ba,cke,cs;wire[15:0]dq;wire sc,ras,cas,we,lm,um;
 integer cycle=0,sent=0,produced=0,jobs=0,i,j,checks=0,held=0,jobserial=0,writes_before;
 reg[31:0]fresh[0:23039];reg[39:0]goldseq[0:N-1];reg[15:0]goldmem[0:N-1];
 reg old_hold=0;reg[39:0]held_output;reg previous_idle=0,previous_terminal=0;
 reg old_input_hold=0;reg[167:0]held_input;
 reg[1:0]previous_owned=0,previous_retired=0;
 reg[181:0]held_meta[0:1];integer bc,both_owned_cycles=0,both_full_cycles=0,overlap_cycles=0;
 wire allow_write=manual_allow&&(!stall_enable||cycle%97>=13);
 function[7:0]datum(input integer index);datum=index*37+91;endfunction
 ar03_yuv_transpose dut(.clk(clk),.reset(reset),.start_valid(start),.start_ready(sr),.start_rejected(srej),
  .start_owner(so),.start_epoch(se),.start_frame(sf),.start_width(sw),.start_height(sh),.start_base(sb),
  .in_valid(iv),.in_ready(ir),.in_address(ia),.in_data(idata),.in_owner(io),.in_epoch(ie),.in_frame(ifr),
  .upstream_flush(uflush),.upstream_discard(udiscard),.abort(ab),.fault(ft),
  .pixel_valid(pv),.pixel_ready(pr),.pixel_address(pa),.pixel_data(pd),.force_flush(flush),.discard(discard),.memory_idle(idle),
  .store_idle(storeidle),.done(done),.failed(failed),.aborted(aborted),.release_valid(rel),.release_owner(ro),.release_epoch(re),.release_frame(rf),.release_rejected(rrej),
  .owner(owner),.input_words(ins),.processed_bytes(processed),.output_words(outs),.stripe_high_water(highwater),.error_code(ec),.state(state));
 wire b_sr,b_srej,b_ir,b_pv,b_flush,b_discard,b_storeidle,b_done,b_failed,b_aborted,b_rrej;
 wire[23:0]b_pa;wire[15:0]b_pd;wire[63:0]b_owner;
 wire[31:0]b_ins,b_processed,b_outs,b_highwater;wire[3:0]b_ec,b_state;
 reg[31:0]expected_delayed_peak=0;integer equivalence_cycles=0;
 ar03_yuv_transpose_baseline baseline(.clk(clk),.reset(reset),.start_valid(start),.start_ready(b_sr),.start_rejected(b_srej),
  .start_owner(so),.start_epoch(se),.start_frame(sf),.start_width(sw),.start_height(sh),.start_base(sb),
  .in_valid(iv),.in_ready(b_ir),.in_address(ia),.in_data(idata),.in_owner(io),.in_epoch(ie),.in_frame(ifr),
  .upstream_flush(uflush),.upstream_discard(udiscard),.abort(ab),.fault(ft),
  .pixel_valid(b_pv),.pixel_ready(pr),.pixel_address(b_pa),.pixel_data(b_pd),.force_flush(b_flush),.discard(b_discard),.memory_idle(idle),
  .store_idle(b_storeidle),.done(b_done),.failed(b_failed),.aborted(b_aborted),.release_valid(rel),.release_owner(ro),.release_epoch(re),.release_frame(rf),.release_rejected(b_rrej),
  .owner(b_owner),.input_words(b_ins),.processed_bytes(b_processed),.output_words(b_outs),.stripe_high_water(b_highwater),.error_code(b_ec),.state(b_state));
 always @(posedge clk)begin
  if(reset||(state==0&&start&&sr&&dut.g_double.core.admission))expected_delayed_peak=0;
  else expected_delayed_peak=b_highwater;
 end
 always @(negedge clk)if(!reset)begin
  equivalence_cycles=equivalence_cycles+1;
  if({sr,srej,ir,pv,pa,pd,flush,discard,storeidle,done,failed,aborted,rrej,owner,ins,processed,outs,ec,state} !==
     {b_sr,b_srej,b_ir,b_pv,b_pa,b_pd,b_flush,b_discard,b_storeidle,b_done,b_failed,b_aborted,b_rrej,b_owner,b_ins,b_processed,b_outs,b_ec,b_state})$fatal(1,"DATAPATH_EQUIVALENCE_MISMATCH cycle=%0d",cycle);
  if(highwater!==expected_delayed_peak)$fatal(1,"PEAK_DELAY_MISMATCH cycle=%0d new=%0d expected=%0d baseline=%0d",cycle,highwater,expected_delayed_peak,b_highwater);
 end

 assign pr=mpr&&allow_write;
 moonshine_memory_burst memory(.clk(clk),.read_clk(read_clk),.reset(reset),.pixel_valid(pv&&allow_write),.pixel_ready(mpr),
  .pixel_address(pa),.pixel_rgb565(pd),.force_flush(flush),.discard(discard),.idle(idle),
  .line_req_valid(1'b0),.line_req_address(24'd0),
  .sdram_a(a),.sdram_bs(ba),.sdram_dq(dq),.sdram_clk(sc),.sdram_cke(cke),.sdram_cs_n(cs),.sdram_ras_n(ras),.sdram_cas_n(cas),.sdram_we_n(we),.sdram_ldqm(lm),.sdram_udqm(um));
 sdram_model_burst model(.clk(sc),.a(a),.ba(ba),.cke(cke),.cs(cs),.ras(ras),.cas(cas),.we(we),.ldqm(lm),.udqm(um),.dq(dq));
 always @(posedge clk)begin
  cycle=cycle+1;
  if(!reset)begin
   if(dut.owned_banks==3)both_owned_cycles=both_owned_cycles+1;
   if(dut.full_banks==3)both_full_cycles=both_full_cycles+1;
   if(dut.g_double.core.fill_take&&dut.g_double.core.read_take)overlap_cycles=overlap_cycles+1;
   for(bc=0;bc<2;bc=bc+1)begin
    if(previous_owned[bc]&&dut.owned_banks[bc]&&!dut.g_double.core.cancel_active&&
     held_meta[bc]!=={dut.g_double.core.bank_owner[bc],dut.g_double.core.bank_epoch[bc],dut.g_double.core.bank_frame[bc],dut.g_double.core.bank_base[bc],dut.g_double.core.bank_plane[bc],dut.g_double.core.bank_y[bc],dut.g_double.core.bank_pw[bc],dut.g_double.core.bank_ph[bc]})$fatal(1,"owned bank metadata changed");
    if(previous_owned[bc]&&!dut.owned_banks[bc]&&state==1&&!previous_retired[bc])$fatal(1,"bank freed before final output acceptance");
    held_meta[bc]={dut.g_double.core.bank_owner[bc],dut.g_double.core.bank_epoch[bc],dut.g_double.core.bank_frame[bc],dut.g_double.core.bank_base[bc],dut.g_double.core.bank_plane[bc],dut.g_double.core.bank_y[bc],dut.g_double.core.bank_pw[bc],dut.g_double.core.bank_ph[bc]};
   end
   previous_owned=dut.owned_banks;previous_retired=0;
   if(dut.g_double.core.retire_bank)previous_retired[dut.g_double.core.rb]=1;
   if(old_input_hold&&!ab&&!ft&&!udiscard&&!dut.g_double.core.cancel_active&&(!iv||{ia,idata,io,ie,ifr}!==held_input))$fatal(1,"input producer withdrew/changed a held word");
   old_input_hold=iv&&!ir&&!ab&&!ft&&!udiscard&&!dut.g_double.core.cancel_active&&state<5;
   if(old_input_hold)held_input={ia,idata,io,ie,ifr};
   if(iv&&ir)sent=sent+1;
   if(dut.g_double.core.fill_take)begin
    if(dut.g_double.core.fill_address>=23040)$fatal(1,"stripe write bounds");fresh[dut.g_double.core.fill_address]=jobserial*1000+dut.g_double.core.plane*100+dut.g_double.core.stripe_y/16;
   end
   if(dut.g_double.core.read_take)begin
    if(dut.g_double.core.low_address!==baseline.g_double.core.low_address||dut.g_double.core.high_address!==baseline.g_double.core.high_address)$fatal(1,"registered read address mismatch");
    if(dut.g_double.core.low_address>=23040||dut.g_double.core.high_address>=23040)$fatal(1,"stripe read bounds");
    if(fresh[dut.g_double.core.read_high?dut.g_double.core.high_address:dut.g_double.core.low_address]!==jobserial*1000+dut.g_double.core.bank_plane[dut.g_double.core.rb]*100+dut.g_double.core.bank_y[dut.g_double.core.rb]/16)$fatal(1,"read before current-owner/stripe fresh write");
   end
   if(pv&&pr)begin
    if({pa-BASE,pd}!==goldseq[produced])$fatal(1,"independent sequence mismatch output=%0d address=%h data=%h expected=%h",produced,pa,pd,goldseq[produced]);
    produced=produced+1;
   end
   if(old_hold&&!ab&&!ft&&!udiscard&&!dut.g_double.core.cancel_active&&(!pv||{pa,pd}!==held_output))$fatal(1,"held output changed");
   old_hold=pv&&!pr;if(old_hold)begin held_output={pa,pd};held=held+1;end
   if(flush&&(dut.g_double.core.skid_valid||dut.g_double.core.bank_owned!=0||dut.g_double.core.reserved_bytes!=0||dut.g_double.core.out_valid))$fatal(1,"early downstream flush");
   if((done||failed||aborted)&&!previous_terminal&&(!previous_idle||model.write_left!=0))$fatal(1,"terminal before actual physical drain");
   if(owner!=0&&(done||failed||aborted)&&!rel&&owner!==so)$fatal(1,"terminal owner lost");
   if(highwater>23040)$fatal(1,"storage capacity");
  end
  previous_idle=idle;previous_terminal=done||failed||aborted;
  if(cycle>2500000)$fatal(1,"unit timeout state=%0d ins=%0d outs=%0d",state,ins,outs);
 end
 task launch;
  begin
   while(!sr)@(negedge clk);@(negedge clk);udiscard=1;start=1;jobserial=jobserial+1;sent=0;produced=0;old_hold=0;
   @(negedge clk);start=0;udiscard=0;
   if(owner!==so||state!=1)$fatal(1,"IDLE discard defeated valid START");jobs=jobs+1;
  end
 endtask
 task feed(input integer target);
  begin
   while(sent<target)begin
    @(negedge clk);
    if(sent<target)begin iv=1;ia=BASE+sent;idata={datum(sent*2+1),datum(sent*2)};end
    else iv=0;
   end
   iv=0;
  end
 endtask
 task release_job;
  begin
   wait(done||failed||aborted);@(negedge clk);
   if(owner!==so)$fatal(1,"owner lost before release");
   ro=so^64'h8000000000000000;rel=1;#1;if(!rrej)$fatal(1,"stale release admitted");
   @(negedge clk);rel=0;ro=so;repeat(2)@(negedge clk);while(!storeidle)@(negedge clk);
   rel=1;@(negedge clk);rel=0;udiscard=1;
   if(owner!=0||state!=0)$fatal(1,"release failed");checks=checks+1;
  end
 endtask
 initial begin
  $readmemh("unit-sequence.hex",goldseq);$readmemh("unit-column.hex",goldmem);
  model.mem[BASE-1]=16'h1357;model.mem[BASE+N]=16'h2468;
  repeat(8)@(negedge clk);reset=0;
  if(FULL_TEST)begin
   stall_enable=1;launch;feed(N);uflush=1;
   if(FULL_TEST==2)begin
    wait(state==4&&model.write_left>0);@(negedge clk);ab=1;@(negedge clk);ab=0;
    wait(aborted);if(done)$fatal(1,"final-flush abort became success");
   end else wait(done);
   @(negedge clk);
   if(sent!=N||ins!=N||processed!=518400||produced!=N||outs!=N||(highwater<11520||highwater>23040))$fatal(1,"full counts");
   for(i=0;i<N;i=i+1)if(model.mem[BASE+i]!==goldmem[i])$fatal(1,"independent column memory mismatch %0d",i);
   uflush=0;release_job;
   if(model.mem[BASE-1]!==16'h1357||model.mem[BASE+N]!==16'h2468)$fatal(1,"guard alias");
   if(overlap_cycles==0||both_owned_cycles==0)$fatal(1,"fill/drain overlap not exercised");
   $display("EQUIVALENCE cycles=%0d",equivalence_cycles);
   $display("TRANSPOSE_FULL_PASS inputs=%0d outputs=%0d column_words=%0d high_water=%0d held=%0d cycles=%0d physical_writes=%0d aborted_at_final_flush=%0d overlap_cycles=%0d both_owned_cycles=%0d both_full_cycles=%0d",sent,produced,N,highwater,held,cycle,model.writes,FULL_TEST==2,overlap_cycles,both_owned_cycles,both_full_cycles);
  end else begin
   // START cancellation guards; deliberately held START can admit after drop.
   @(negedge clk);start=1;ab=1;#1;if(sr)$fatal(1,"START+abort");@(negedge clk);if(owner!=0)$fatal(1,"abort allocated owner");
   ab=0;ft=1;#1;if(sr)$fatal(1,"START+fault");@(negedge clk);if(owner!=0)$fatal(1,"fault allocated owner");ft=0;jobserial=jobserial+1;
   @(negedge clk);start=0;udiscard=0;if(owner!==so||state!=1)$fatal(1,"held START did not admit after cancellation dropped");jobs=jobs+1;
   ab=1;@(negedge clk);ab=0;release_job;
   // Invalid geometry, alignment, range and identity never allocate.
   for(j=0;j<6;j=j+1)begin
    @(negedge clk);sw=720;sb=BASE;so=64'h1020304050607080;se=1;sf=7;
    case(j)0:sw=718;1:sb=BASE+1;2:sb=BASE+2952;3:so=0;4:se=32'hffffffff;5:sf=32'hffffffff;endcase
    start=1;#1;if(!srej)$fatal(1,"invalid START not rejected case%0d",j);@(negedge clk);start=0;if(owner!=0)$fatal(1,"invalid owner allocation");checks=checks+1;
   end
   sw=720;so=64'h1020304050607080;se=1;sf=7;
   // Exact top boundary is legal; one aligned group beyond it was rejected.
   sb=BASE+2944;launch;@(negedge clk);ab=1;@(negedge clk);ab=0;release_job;sb=BASE;
   launch;feed(1);wait(dut.g_double.core.skid_valid&&dut.g_double.core.skid_high);@(negedge clk);
   if(!dut.g_double.core.skid_valid||!dut.g_double.core.skid_high||processed!=1)$fatal(1,"partial-input abort phase missed");
   ab=1;@(negedge clk);ab=0;release_job;
   launch;feed(100);uflush=1;@(negedge clk);uflush=0;wait(failed);if(ec!=6)$fatal(1,"premature end");release_job;
   launch;feed(40);ft=1;@(negedge clk);ft=0;wait(failed);if(ec!=4)$fatal(1,"active fault classification");release_job;
   launch;feed(40);udiscard=1;@(negedge clk);wait(failed);if(ec!=4)$fatal(1,"active discard classification");release_job;
   launch;@(negedge clk);io=so^64'h8000000000000000;iv=1;ia=BASE;@(negedge clk);iv=0;io=so;wait(failed);if(ec!=2||ins!=0)$fatal(1,"bad identity accepted");release_job;
   launch;@(negedge clk);iv=1;ia=BASE+1;@(negedge clk);iv=0;wait(failed);if(ec!=3||ins!=0)$fatal(1,"bad word address accepted");release_job;
   // Abort after full stripe with next-word skid and held physical output.
   manual_allow=0;launch;feed(5761);wait(pv);repeat(7)@(negedge clk);ab=1;@(negedge clk);ab=0;manual_allow=1;release_job;
   // Cancel an accepted physical burst; local discard cannot stop its eight beats.
   launch;fork feed(5761);begin wait(model.write_left>0);@(negedge clk);ab=1;@(negedge clk);ab=0;end join
   iv=0;wait(aborted);if(model.write_left!=0)$fatal(1,"physical burst not drained");release_job;
   // Both entire banks plus the2-byte next-stripe skid remain owned while a
   // stalled output holds the oldest bank. Exercise every cancellation class.
   for(j=0;j<4;j=j+1)begin
    manual_allow=0;launch;feed(11521);wait(dut.full_banks==3&&dut.g_double.core.skid_valid);repeat(9)@(negedge clk);
    if(dut.reserved_bytes!=23040||highwater!=23040||outs!=0)$fatal(1,"two-bank ownership bound");
    case(j)
     0:ab=1;1:ft=1;2:udiscard=1;
     3:begin dut.g_double.core.bank_owner[dut.g_double.core.rb]=so^64'h8000000000000000; baseline.g_double.core.bank_owner[baseline.g_double.core.rb]=so^64'h8000000000000000; end
    endcase
    @(negedge clk);ab=0;ft=0;manual_allow=1;
    if(j==0)wait(aborted);else wait(failed);
    if(j==3&&ec!=7)$fatal(1,"stale bank owner was not rejected");release_job;
   end
   if(both_owned_cycles==0||both_full_cycles==0)$fatal(1,"missing both-owned/full coverage");
   $display("EQUIVALENCE cycles=%0d",equivalence_cycles);
   $display("TRANSPOSE_DIRECTED_PASS jobs=%0d checks=%0d held=%0d cycles=%0d overlap_cycles=%0d both_owned_cycles=%0d both_full_cycles=%0d",jobs,checks,held,cycle,overlap_cycles,both_owned_cycles,both_full_cycles);
  end
  $finish;
 end
endmodule
