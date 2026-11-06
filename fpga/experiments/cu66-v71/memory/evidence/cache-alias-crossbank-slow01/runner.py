"""Explicit RGB BL8 port regression with unchanged selected SDR2 pin model."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time
p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--slow',action='store_true');p.add_argument('--seed',type=int,default=7001);p.add_argument('--map',type=Path);p.add_argument('--cache',action='store_true');a=p.parse_args()
r=Path(__file__).resolve().parents[3];m=r/'fpga/experiments/cu66-v71/memory';base=m/'evidence/lookahead-fast01';o=Path(a.output).resolve();o.mkdir(parents=True,exist_ok=False)
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
files=['cu71_memory_system_burst.sv','cu71_word_bridge_burst.sv','cu71_tile_memory.sv','moonshine_sdram_burst.sv']
if a.cache:files=[n.replace('_burst.sv','_burst_cache.sv')if n.startswith('cu71_memory_system')or n.startswith('cu71_word_bridge')else n for n in files]
for n in files:shutil.copy2(m/n,o/n)
for n in ['model.sv','primitives.sv','cu70_memory_map.svh']:shutil.copy2(base/n,o/n)
if a.map:shutil.copy2(a.map/'cu70_memory_map.svh',o/'cu70_memory_map.svh')
tb=(base/'tb.sv').read_text().replace('cu71_memory_system #','cu71_memory_system_burst #')
if a.cache:tb=tb.replace('cu71_memory_system_burst #','cu71_memory_system_burst_cache #')
if a.slow:tb=tb.replace('.T_AC_NS(2.223),.CLOCK_FLIGHT_NS(0.757)', '.T_AC_NS(8.489),.CLOCK_FLIGHT_NS(3.768)')
tb=tb.replace(' logic[31:0]cache_hits,', ''' logic rgb_parallel=0;
 logic rgb_req_valid=0,rgb_req_ready,rgb_rsp_valid,rgb_rsp_ready=0,rgb_rsp_error,rgb_abort_i=0,rgb_busy,rgb_aborted;
 logic[23:0]rgb_req_addr=0;logic[127:0]rgb_req_data=0;logic[15:0]rgb_req_mask=16'hffff;
 logic[31:0]rgb_completed_writes,rgb_max_wait;
 logic[31:0]cache_hits,''')
tb=tb.replace(' integer checks=0,', ''' integer canonical_read_commands=0;
 always @(posedge clk)if(!rst&&dut.mem_req_valid&&dut.mem_req_ready&&!dut.mem_req_write&&dut.bridge.owner==0)canonical_read_commands=canonical_read_commands+1;
 integer checks=0,''')
task=''' task automatic rgb_write(input logic[23:0]addr,input logic[127:0]data,input logic[15:0]mask,input bit bad);
  integer wait_count,prior,prior_rgb;bit saved;
  begin
   prior=model.writes;prior_rgb=rgb_completed_writes;
   @(negedge clk);rgb_req_valid=1;rgb_req_addr=addr;rgb_req_data=data;rgb_req_mask=mask;
   do @(posedge clk);while(!rgb_req_ready);
   @(negedge clk);rgb_req_valid=0;wait_count=0;
   while(!rgb_rsp_valid)begin @(negedge clk);if(wait_count++>500)$fatal(1,"RGB completion timeout");end
   if(rgb_rsp_error!==bad)$fatal(1,"RGB completion error");
   if(rgb_completed_writes-prior_rgb!=(bad?0:1))$fatal(1,"RGB completion count disagrees with actual recovery");
   if(!rgb_parallel&&model.writes-prior!=(bad?0:8))$fatal(1,"RGB physical8beat drain prior=%0d now=%0d addr=%h",prior,model.writes,addr);
   saved=rgb_rsp_error;
   repeat(3)begin @(negedge clk);if(!rgb_rsp_valid||rgb_rsp_error!==saved)$fatal(1,"RGB held completion changed");end
   rgb_rsp_ready=1;@(posedge clk);@(negedge clk);rgb_rsp_ready=0;checks=checks+1;
  end
 endtask
'''
tb=tb.replace(' initial begin\n',task+' initial begin\n',1)
extra='''  // Independent RGB128producer: all bytes, low/high byte masks, halves,
  // allmaskedNOP and seeded masks. Every operation retains actual drain.
  begin: rgb_mask_campaign
   logic[127:0]data;logic[15:0]mask,expected_word;integer n,v;
   model.mem[RGB1_BASE-1]=16'hcafe;model.mem[RGB1_BASE+RGB1_WORDS]=16'hbabe;
   for(v=0;v<10;v=v+1)begin
    for(n=0;n<8;n=n+1)aux(1,RGB1_BASE+24'(n),16'(16'h1200+n),0,got);
    aux(0,RGB1_BASE,0,0,got); // Populate oldauxcachebeforetheRGBwrite.
    for(n=0;n<8;n=n+1)data[16*n+:16]=16'(16'h7000+v*16+n);
    case(v)0:mask=0;1:mask=16'haaaa;2:mask=16'h5555;3:mask=16'hff00;4:mask=16'h00ff;5:mask=16'hffff;default:mask=16'($random(seed));endcase
    rgb_write(RGB1_BASE,data,mask,0);
    for(n=0;n<8;n=n+1)begin
     expected_word=16'(16'h1200+n);
     if(!mask[n*2])expected_word[7:0]=data[n*16+:8];if(!mask[n*2+1])expected_word[15:8]=data[n*16+8+:8];
     aux(0,RGB1_BASE+24'(n),0,0,got);if(got!==expected_word)$fatal(1,"RGB byte mask/cache coherence");
    end
   end
   rgb_write(RGB1_BASE+24'(RGB1_WORDS)-8,data,0,0);
   for(n=0;n<8;n=n+1)begin aux(0,RGB1_BASE+24'(RGB1_WORDS)-8+24'(n),0,0,got);if(got!==data[16*n+:16])$fatal(1,"RGBlastblock");end
   rgb_write(RGB1_BASE+1,data,0,1);rgb_write(RGB1_BASE+24'(RGB1_WORDS),data,0,1);rgb_write(CANONICAL0_BASE,data,0,1);
   if(model.mem[RGB1_BASE-1]!==16'hcafe||model.mem[RGB1_BASE+RGB1_WORDS]!==16'hbabe)$fatal(1,"RGBguardcorrupted");
  end
  // Accepted RGBoperation is indivisible: abort at each physicalbeat drains
  // all8beats, exposes no success, and releasesonlyafteractualcompletion.
  for(k=1;k<=8;k=k+1)begin
   prior_writes=model.writes;
   @(negedge clk);rgb_req_valid=1;rgb_req_addr=RGB1_BASE;rgb_req_data={8{16'(16'h8000+k)}};rgb_req_mask=0;
   do @(posedge clk);while(!rgb_req_ready);
   @(negedge clk);rgb_req_valid=0;
   while(model.writes-prior_writes<k)@(negedge clk);
   rgb_abort_i=1;@(posedge clk);@(negedge clk);rgb_abort_i=0;
   while(rgb_busy)begin if(rgb_rsp_valid)$fatal(1,"aborted RGB exposed success");@(negedge clk);end
   if(!rgb_aborted||model.writes-prior_writes!=8)$fatal(1,"RGBabortdidnotdrain");
   for(j=0;j<8;j=j+1)begin aux(0,RGB1_BASE+24'(j),0,0,got);if(got!==16'(16'h8000+k))$fatal(1,"RGBabortacceptedoperationpartial");end
   checks=checks+1;aborts=aborts+1;
  end
  // Stalled RGBcompletion leaves LCD andaux clients operational.
  @(negedge clk);rgb_req_valid=1;rgb_req_addr=RGB1_BASE;rgb_req_data={8{16'h4abc}};rgb_req_mask=0;
  do @(posedge clk);while(!rgb_req_ready);
  @(negedge clk);rgb_req_valid=0;while(!rgb_rsp_valid)@(negedge clk);
  lcd_req_valid=1;lcd_req_addr=RGB1_BASE;
  do @(posedge clk);while(!lcd_req_ready);
  @(negedge clk);lcd_req_valid=0;while(!lcd_rsp_valid)@(negedge clk);
  if(lcd_rsp_error||lcd_rsp_data!=={8{16'h4abc}}||!rgb_rsp_valid)$fatal(1,"heldRGBblockedLCD");
  lcd_rsp_ready=1;@(posedge clk);@(negedge clk);lcd_rsp_ready=0;
  aux(1,DIAGNOSTIC_BASE+200,16'h7db0,0,got);
  if(!rgb_rsp_valid||rgb_rsp_error)$fatal(1,"heldRGBcompletionunstable");
  rgb_rsp_ready=1;@(posedge clk);@(negedge clk);rgb_rsp_ready=0;checks=checks+1;
  // Allfourclients have independent ownership, and backgroundRRincludesRGB.
  write_tile(0,2,333,make_pattern(13171),0);
  rgb_parallel=1;
  fork
   begin: rgb_parallel_tile write_tile(2,1,51,make_pattern(900),0);end
   begin: rgb_parallel_aux integer n;logic[15:0]value;for(n=0;n<32;n=n+1)aux(1,HUD2_BASE+24'(n),16'(n+5),0,value);end
   begin: rgb_parallel_writer integer n;for(n=0;n<32;n=n+1)rgb_write(RGB1_BASE+24'(n*8),{8{16'(n+100)}},0,0);end
   begin: contended_reference_reads
    integer n,start_cycle,max_cycles,prior_cmds,prior_hits;max_cycles=0;prior_cmds=canonical_read_commands;prior_hits=cache_hits;
    for(n=0;n<4;n=n+1)begin
     start_cycle=cycles;read_tile(0,2,333,make_pattern(13171),0);
     if(cycles-start_cycle>max_cycles)max_cycles=cycles-start_cycle;
    end
    if(canonical_read_commands-prior_cmds!=32)$fatal(1,"contendedreferenceBL8commandcount");
    if(cache_hits-prior_hits!=96)$fatal(1,"contendedreferenceprivatecachehits");
    $display("CU71_CONTENDED_REFERENCE_READ tiles=4 actual_BL8_reads=%0d private_cache_hits=%0d max_tile_cycles=%0d",canonical_read_commands-prior_cmds,cache_hits-prior_hits,max_cycles);
   end
   begin: rgb_parallel_lcd integer n;for(n=0;n<32;n=n+1)begin
    @(negedge clk);lcd_req_valid=1;lcd_req_addr=RGB0_BASE;
    do @(posedge clk);while(!lcd_req_ready);
    @(negedge clk);lcd_req_valid=0;while(!lcd_rsp_valid)@(negedge clk);
    if(lcd_rsp_error)$fatal(1,"parallelLCDerror");
    for(integer q=0;q<8;q=q+1)if(lcd_rsp_data[q*16+:16]!==16'(16'h6000+q))$fatal(1,"parallelLCDpayload");
    lcd_rsp_ready=1;@(posedge clk);@(negedge clk);lcd_rsp_ready=0;
   end end
  join
  read_tile(2,1,51,make_pattern(900),0);
  for(j=0;j<256;j=j+1)begin aux(0,RGB1_BASE+24'(j),0,0,got);if(got!==16'(j/8+100))$fatal(1,"concurrentRGBfunctionalreadback");end
  for(j=0;j<32;j=j+1)begin aux(0,HUD2_BASE+24'(j),0,0,got);if(got!==16'(j+5))$fatal(1,"concurrentHUDfunctionalreadback");end
  $display("CU71_RGB_BURST_COVERAGE rgb_operations=%0d rgb_max_wait=%0d lcd_max_wait=%0d",rgb_completed_writes,rgb_max_wait,lcd_max_wait);
'''
needle='  prior_refreshes=model.refreshes;';assert tb.count(needle)==1;tb=tb.replace(needle,extra+needle)
if a.cache:
 alias='''  // Prime an oldRGBauxcacheline, then read while an aliasingRGB
  // write is physically active. Grant-time invalidation must defeat fast hits.
  aux(0,RGB1_BASE,0,0,got);if(got!==16'd100)$fatal(1,"RGBaliasprime");
  prior_writes=model.writes;
  @(negedge clk);rgb_req_valid=1;rgb_req_addr=RGB1_BASE;rgb_req_data={8{16'h9a80}};rgb_req_mask=0;
  do @(posedge clk);while(!rgb_req_ready);
  @(negedge clk);rgb_req_valid=0;while(model.writes-prior_writes<1)@(negedge clk);
  if(dut.bridge.cache_valid[1])$fatal(1,"activeRGBwriteleftaliascachevalid");
  aux(0,RGB1_BASE,0,0,got);if(got!==16'h9a80)$fatal(1,"activeRGBaliasreturnedstalehit");
  if(!rgb_rsp_valid||rgb_rsp_error)$fatal(1,"RGBaliasdrainresponse");
  rgb_rsp_ready=1;@(posedge clk);@(negedge clk);rgb_rsp_ready=0;checks=checks+1;
  // Prime canonicalcachefirstrow by aborting a read after that acceptedBL8
  // fills. An activeauxwrite must invalidate it before a newtile read bypasses.
  begin: canonical_alias_campaign
   integer target_addr;logic[511:0]expected;
   expected=make_pattern(13171);read_tile(0,2,333,expected,0);
   target_addr=int'(CANONICAL0_BASE)+216000+(333/45)*8*180+(333%45)*4;
   read_valid=1;read_generation=990;read_bank=0;read_plane=2;read_index=333;
   do @(posedge clk);while(!read_ready);
   @(negedge clk);read_valid=0;
   while(!(dut.bridge.cache_valid[0]&&dut.bridge.cache_tag[0]==(target_addr>>3)))@(negedge clk);
   abort_i=1;@(posedge clk);@(negedge clk);abort_i=0;
   while(tile_busy)@(negedge clk);if(!tile_aborted)$fatal(1,"canonicalcacheprimeabort");
   checks=checks+1;aborts=aborts+1;
   prior_writes=model.writes;aux_req_valid=1;aux_req_write=1;aux_req_addr=24'(target_addr);aux_req_data=16'habcd;
   do @(posedge clk);while(!aux_req_ready);
   @(negedge clk);aux_req_valid=0;while(model.writes-prior_writes<1)@(negedge clk);
   if(dut.bridge.cache_valid[0])$fatal(1,"activeauxwriteleftcanonicalaliasvalid");
   expected[15:0]=16'habcd;read_tile(0,2,333,expected,0);
   if(!aux_rsp_valid||aux_rsp_error)$fatal(1,"canonicalaliasauxdrain");
   aux_rsp_ready=1;@(posedge clk);@(negedge clk);aux_rsp_ready=0;checks=checks+1;
  end
  $display("CU71_CACHE_ACTIVE_ALIAS_PASS RGBaux=1 AUXcanonical=1 accepted_prime_abort=1");
'''
 assert tb.count(needle)==1;tb=tb.replace(needle,alias+needle)
tb=tb.replace('CU71_MEMORY_PASS','CU71_MEMORY_RGB_BURST_PASS')
(o/'tb.sv').write_text(tb,newline='\n')
sources=files+['model.sv','primitives.sv','tb.sv']
(o/'runner.py').write_bytes(Path(__file__).read_bytes())
(o/'source-freeze.json').write_text(json.dumps({n:sha(o/n)for n in sources+['cu70_memory_map.svh','runner.py']},indent=2)+'\n')
env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env.get('PATH','');steps=[]
for label,cmd in [('compile',['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-s','tb_memory','-I',str(o),'-o',str(o/'test.vvp'),*[str(o/n)for n in sources]]),('simulation',['C:/msys64/ucrt64/bin/vvp.exe','-i',str(o/'test.vvp'),'+SEED='+str(a.seed)])]:
 t=time.monotonic()
 with(o/(label+'.log')).open('wb')as f:q=subprocess.run(cmd,cwd=o,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=600)
 steps.append({'label':label,'command':cmd,'returncode':q.returncode,'seconds':time.monotonic()-t});(o/'execution.json').write_text(json.dumps(steps,indent=2)+'\n')
 print(label,q.returncode,flush=True);assert q.returncode==0,(label,o)
log=(o/'simulation.log').read_text();assert 'CU71_MEMORY_RGB_BURST_PASS'in log and 'CU71_RGB_BURST_COVERAGE'in log
(o/'result.json').write_text(json.dumps({'status':'PASS_EXPLICIT_RGB_BL8_ACTUAL_DRAIN_MASKS_ABORT_ISOLATION','slow':a.slow,'seed':a.seed,'hardware':False,'routed_timing':False,'scope':'ActualnonSIMULATIONcontroller+strictCAS3model; baselinecomponentchecks+RGBmasks/guards/all8abortpositions/4clientconcurrency. Cadenceseparate.'},indent=2)+'\n')
