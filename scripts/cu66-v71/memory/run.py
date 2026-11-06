"""Source-bound qualified-backend component regression, no Vivado/hardware."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,sys,time
p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--seed',type=int,default=7001)
p.add_argument('--flight',type=float,default=.757);p.add_argument('--access',type=float,default=2.223);p.add_argument('--hold',type=float,default=2.223);a=p.parse_args()
root=Path(__file__).resolve().parents[3];source=root/'fpga/experiments/cu66-v71/memory';old=root/'fpga/experiments/cu66-v70/memory'
out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=False)
helpers=Path(__file__).resolve().parent;sys.path.insert(0,str(helpers))
from cpl1_sdram_models import strict_hold_text
from sdr2_model_checked import add_checks
from sdr2_model_spec_v2 import correct_cas3_launch,correct_monitor_refresh_anchor
frozen=source/'verification'
model=correct_monitor_refresh_anchor(add_checks(strict_hold_text(correct_cas3_launch((frozen/'model_base.sv').read_text()))))
# Verification observability only: count READ commands, preserve device behavior.
model=model.replace('integer latency=0,', 'integer reads=0,acts=0,pres=0; integer latency=0,').replace("readaddr={ba,rows[ba],a[8:0]};", "reads=reads+1;readaddr={ba,rows[ba],a[8:0]};")
model=model.replace("3'b011:begin if(opened", "3'b011:begin acts=acts+1;if(opened").replace("3'b010:begin if(!a", "3'b010:begin pres=pres+1;if(!a")
(out/'model.sv').write_text(model,newline='\n')
shutil.copy2(frozen/'primitives.sv',out/'primitives.sv')
for n in ['cu71_memory_system.sv','cu71_word_bridge.sv','cu71_tile_memory.sv','moonshine_sdram_burst.sv']:shutil.copy2(source/n,out/n)
for n in ['cu70_memory_map.svh']:shutil.copy2(old/n,out/n)
tb=(old/'tb_memory.sv').read_text().replace('module tb_memory #(parameter real TAC_NS=2.0,FLIGHT_NS=4.0);','module tb_memory;')
tb=tb.replace('read_clk<=#2.75 ~clk','read_clk<=#2.625 ~clk')
tb=tb.replace('cu70_memory_system #','cu71_memory_system #')
tb=tb.replace(' cu70_sdram_model #(.T_AC_NS(TAC_NS),.CLOCK_FLIGHT_NS(FLIGHT_NS)) model(.reset(rst),', f' sdram_model_burst #(.MEM_WORDS(16777216),.T_AC_NS({a.access:.3f}),.CLOCK_FLIGHT_NS({a.flight:.3f}),.T_OH_NS({a.hold:.3f})) model(')
tb=tb.replace(' logic[31:0]cache_hits,', ''' logic lcd_req_valid=0,lcd_req_ready,lcd_rsp_valid,lcd_rsp_ready=0,lcd_rsp_error,lcd_abort_i=0,lcd_busy,lcd_aborted;
 logic[23:0]lcd_req_addr=0;logic[127:0]lcd_rsp_data;logic[31:0]lcd_completed_reads,lcd_max_wait;
 logic[31:0]cache_hits,''')
# Original abort thresholds count scalar write commands, while this model counts
# all8physical BL8 beats including masked. Preserve original abort tasks for audit
# but execute dedicated accepted-operation/held-response cases below.
tb=tb.replace('for(k=0;k<=32;k=k+1)abort_write(k);','// Legacy single-write abort task not applicable to masked BL8; new cases below.')
tb=tb.replace('for(k=1;k<=8;k=k+1)abort_read(k);','for(k=1;k<=8;k=k+1)abort_read(k);')
tb=tb.replace("completed_writes!=32'(model.writes)","completed_writes*8!=32'(model.writes)")
needle='  prior_refreshes=model.refreshes;'
extra='''  // Held auxiliary response must not prevent dedicated LCD or tile service.
  for(j=0;j<8;j=j+1)aux(1,RGB0_BASE+24'(j),16'(16'h6000+j),0,got);
  @(negedge clk);aux_req_valid=1;aux_req_write=0;aux_req_addr=DIAGNOSTIC_BASE;
  do @(posedge clk);while(!aux_req_ready);
  @(negedge clk);aux_req_valid=0;while(!aux_rsp_valid)@(negedge clk);
  @(negedge clk);lcd_req_valid=1;lcd_req_addr=RGB0_BASE;
  do @(posedge clk);while(!lcd_req_ready);
  @(negedge clk);lcd_req_valid=0;
  begin: held_aux integer wait_lcd;wait_lcd=0;
   while(!lcd_rsp_valid)begin @(negedge clk);wait_lcd=wait_lcd+1;if(wait_lcd>200)$fatal(1,"stalled aux blocked LCD");end
   for(integer n=0;n<8;n=n+1)if(lcd_rsp_data[n*16+:16]!==16'(16'h6000+n))$fatal(1,"LCD BL8 ordering");
   if(lcd_rsp_error||!aux_rsp_valid)$fatal(1,"independent responses");
   repeat(5)@(negedge clk);
   lcd_rsp_ready=1;aux_rsp_ready=1;@(posedge clk);@(negedge clk);lcd_rsp_ready=0;aux_rsp_ready=0;checks=checks+1;
  end
  // A held LCD response must not prevent another auxiliary write from draining.
  @(negedge clk);lcd_req_valid=1;lcd_req_addr=RGB0_BASE;
  do @(posedge clk);while(!lcd_req_ready);
  @(negedge clk);lcd_req_valid=0;while(!lcd_rsp_valid)@(negedge clk);
  aux(1,DIAGNOSTIC_BASE+24'd128,16'h7bad,0,got);
  if(!lcd_rsp_valid||lcd_rsp_data[15:0]!==16'h6000)$fatal(1,"held LCD response changed");
  lcd_abort_i=1;@(posedge clk);@(negedge clk);lcd_abort_i=0;
  while(lcd_busy)@(negedge clk);
  if(!lcd_aborted||lcd_rsp_valid)$fatal(1,"LCD abort did not drain held response");checks=checks+1;
  // Reject unaligned LCD request without issuing any controller READ.
  prior_writes=model.reads;
  lcd_req_valid=1;lcd_req_addr=RGB0_BASE+1;
  do @(posedge clk);while(!lcd_req_ready);
  @(negedge clk);lcd_req_valid=0;while(!lcd_rsp_valid)@(negedge clk);
  if(!lcd_rsp_error||model.reads!=prior_writes)$fatal(1,"LCD alignment guard");
  lcd_rsp_ready=1;@(posedge clk);@(negedge clk);lcd_rsp_ready=0;checks=checks+1;
  // Abort during each of the8accepted physical write beats. The accepted row
  // drains normally, candidate is not published, no new row starts afterwards.
  for(k=1;k<=8;k=k+1)begin
   prior_writes=model.writes;
   write_valid=1;write_generation=900+k;write_bank=0;write_plane=0;write_index=100;write_pixels=make_pattern(k);
   do @(posedge clk);while(!write_ready);
   @(negedge clk);write_valid=0;
   while(model.writes-prior_writes<k)@(negedge clk);
   abort_i=1;@(posedge clk);@(negedge clk);abort_i=0;
   while(tile_busy)begin if(write_done_valid)$fatal(1,"accepted row abort exposed success");@(negedge clk);end
   if(!tile_aborted||model.writes-prior_writes!=8)$fatal(1,"accepted row abort failed drain");
   checks=checks+1;aborts=aborts+1;
  end
  // LCD abort after each accepted read-data beat: no success is exposed,
  // but all8controllerbeats finish before the client allocation is released.
  for(k=0;k<8;k=k+1)begin
   @(negedge clk);lcd_req_valid=1;lcd_req_addr=RGB0_BASE;
   do @(posedge clk);while(!lcd_req_ready);
   @(negedge clk);lcd_req_valid=0;
   while(!(dut.bridge.state==2&&dut.bridge.beat==k&&dut.mem_rsp_valid))@(negedge clk);
   lcd_abort_i=1;@(posedge clk);@(negedge clk);lcd_abort_i=0;
   while(lcd_busy)begin if(lcd_rsp_valid)$fatal(1,"aborted LCD exposed successful response");@(negedge clk);end
   if(!lcd_aborted)$fatal(1,"missing accepted LCD abort drain");checks=checks+1;aborts=aborts+1;
  end
  // Auxiliary masked write abort at everyphysicalbeat; completion is drained,
  // never canceled at request-queue acceptance or acknowledged as success.
  for(k=1;k<=8;k=k+1)begin
   prior_writes=model.writes;
   aux_req_valid=1;aux_req_write=1;aux_req_addr=DIAGNOSTIC_BASE+24'd80;aux_req_data=16'h7dab;
   do @(posedge clk);while(!aux_req_ready);
   @(negedge clk);aux_req_valid=0;
   while(model.writes-prior_writes<k)@(negedge clk);
   aux_abort_i=1;@(posedge clk);@(negedge clk);aux_abort_i=0;
   while(aux_busy)begin if(aux_rsp_valid)$fatal(1,"aborted aux exposed successful response");@(negedge clk);end
   if(!aux_aborted||model.writes-prior_writes!=8)$fatal(1,"accepted aux write failed drain");checks=checks+1;aborts=aborts+1;
  end
  // A full480word line under concurrentcanonical+HUD work. This measures,
  // rather than assumes, the line deadline;8cycle gaps mimic current serializer.
  for(j=0;j<480;j=j+1)aux(1,RGB0_BASE+24'(j),16'(16'h6000+j),0,got);
  fork
   begin: lcd_line_measure
    integer start_cycle,n,m;logic[127:0]held;start_cycle=cycles;
    for(n=0;n<60;n=n+1)begin
     @(negedge clk);lcd_req_valid=1;lcd_req_addr=RGB0_BASE+24'(n*8);
     do @(posedge clk);while(!lcd_req_ready);
     @(negedge clk);lcd_req_valid=0;
     while(!lcd_rsp_valid)@(negedge clk);
     if(lcd_rsp_error)$fatal(1,"concurrent LCD response error");
     for(m=0;m<8;m=m+1)if(lcd_rsp_data[m*16+:16]!==16'(16'h6000+n*8+m))$fatal(1,"concurrent LCD data mismatch");
     held=lcd_rsp_data;
     repeat(2)begin @(negedge clk);if(!lcd_rsp_valid||lcd_rsp_data!==held)$fatal(1,"LCD held payload unstable");end
     lcd_rsp_ready=1;@(posedge clk);@(negedge clk);lcd_rsp_ready=0;
     repeat(8)@(negedge clk);
    end
    $display("CU71_LCD_LINE_MEASURE clocks=%0d words=480 max_backend_wait=%0d concurrent_tile_HUD=1 deadline_gate=NOT_QUALIFIED",cycles-start_cycle,lcd_max_wait);
   end
   begin: line_background_tile
    write_tile(1,0,230,make_pattern(600),0);
   end
   begin: line_background_hud
    integer n;logic[15:0]value;
    for(n=0;n<96;n=n+1)aux(1,HUD2_BASE+24'(n),16'(n*13+3),0,value);
   end
  join
'''
assert needle in tb;tb=tb.replace(needle,extra+needle)
tb=tb.replace('MEMORY_PASS seed=', 'CU71_MEMORY_PASS seed=')
(out/'tb.sv').write_text(tb,newline='\n')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=['cu71_memory_system.sv','cu71_word_bridge.sv','moonshine_sdram_burst.sv','cu71_tile_memory.sv','model.sv','primitives.sv','tb.sv']
(out/'source-freeze.json').write_text(json.dumps({n:sha(out/n)for n in files+['cu70_memory_map.svh']},indent=2)+'\n')
env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env.get('PATH','');steps=[]
for label,cmd in [('compile',['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-s','tb_memory','-I',str(out),'-o',str(out/'test.vvp'),*[str(out/n)for n in files]]),('simulation',['C:/msys64/ucrt64/bin/vvp.exe','-i',str(out/'test.vvp'),'+SEED='+str(a.seed)])]:
 t=time.monotonic()
 with(out/(label+'.log')).open('wb')as f:q=subprocess.run(cmd,cwd=out,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=600)
 steps.append(dict(label=label,command=cmd,returncode=q.returncode,seconds=time.monotonic()-t));(out/'execution.json').write_text(json.dumps(steps,indent=2)+'\n')
 print(label,q.returncode,flush=True)
 assert q.returncode==0,(label,out)
assert 'CU71_MEMORY_PASS' in(out/'simulation.log').read_text()
(out/'result.json').write_text(json.dumps({'status':'PASS_COMPONENT_CANONICAL_AUX_LCD_QUALIFIED_CONTROLLER','seed':a.seed,'hardware':False,'routed_timing':False,'SIMULATION_define':False,'lumped_clock_ns':a.flight,'lumped_access_ns':a.access,'strict_hold_ns':a.hold,'limits':'Canonical4-wordrows use maskedBL8; auxiliary scalar writes one maskedBL8 each. Conditional digital model only; no reset/PVT/fit signoff.'},indent=2)+'\n')
