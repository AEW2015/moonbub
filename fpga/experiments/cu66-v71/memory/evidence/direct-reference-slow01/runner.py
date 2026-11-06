"""Tile-major four-full-BL8 canonical memory qualification, no board access."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time
p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--slow',action='store_true');p.add_argument('--seed',type=int,default=7001);p.add_argument('--map',type=Path);a=p.parse_args()
r=Path(__file__).resolve().parents[3];m=r/'fpga/experiments/cu66-v71/memory';base=m/'evidence/lookahead-fast01';o=Path(a.output).resolve();o.mkdir(parents=True,exist_ok=False);sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
files=['cu71_memory_system_direct.sv','cu71_word_bridge_direct.sv','cu71_tile_memory_direct.sv','moonshine_sdram_burst.sv']
for n in files:shutil.copy2(m/n,o/n)
for n in ['model.sv','primitives.sv','cu70_memory_map.svh']:shutil.copy2(base/n,o/n)
if a.map:shutil.copy2(a.map/'cu70_memory_map.svh',o/'cu70_memory_map.svh')
tb=(base/'tb.sv').read_text().replace('cu71_memory_system #','cu71_memory_system_direct #')
if a.slow:tb=tb.replace('.T_AC_NS(2.223),.CLOCK_FLIGHT_NS(0.757)', '.T_AC_NS(8.489),.CLOCK_FLIGHT_NS(3.768)')
tb=tb.replace(' logic[31:0]cache_hits,', ''' logic rgb_req_valid=0,rgb_req_ready,rgb_rsp_valid,rgb_rsp_ready=1,rgb_rsp_error,rgb_abort_i=0,rgb_busy,rgb_aborted;
 logic[23:0]rgb_req_addr=0;logic[127:0]rgb_req_data=0;logic[15:0]rgb_req_mask=16'hffff;
 logic[31:0]rgb_completed_writes,rgb_max_wait;
 logic[31:0]cache_hits,''')
tb=tb.replace(' integer checks=0,', ''' integer pin_read_beats=0;
 integer canonical_read_commands=0;
 always @(posedge clk)if(!rst&&dut.mem_req_valid&&dut.mem_req_ready&&!dut.mem_req_write&&dut.bridge.owner==0)canonical_read_commands=canonical_read_commands+1;
 always @(posedge clk)if(!rst&&dut.mem_rsp_valid)pin_read_beats=pin_read_beats+1;
 integer checks=0,''')
old='address0=base+(by*8+j/4)*pitch+bx*4+j%4;'
assert tb.count(old)==1;tb=tb.replace(old,'address0=base+idx*32+j;')
tb=tb.replace('for(k=1;k<=8;k=k+1)abort_read(k);','for(k=1;k<=4;k=k+1)abort_read(k);')
extra='''  begin: direct_command_proof
   integer old_r,old_w,old_mask;logic[511:0]data;
   data=make_pattern(1777);old_w=completed_writes;old_mask=model.masked_bytes;
   write_tile(2,2,1349,data,0);
   if(completed_writes-old_w!=4||model.masked_bytes!=old_mask)$fatal(1,"directtilewriteisnot4fullBL8");
   old_r=completed_reads;read_tile(2,2,1349,data,0);
   if(completed_reads-old_r!=4)$fatal(1,"directtilereadisnot4fullBL8");
   for(integer n=0;n<32;n=n+1)begin
    aux(0,CANONICAL2_BASE+24'd216000+24'(1349*32+n),0,0,got);
    if(got!==data[n*16+:16])$fatal(1,"directlasttilelinearphysicaloracle");
   end
   $display("CU71_DIRECT_TILE_COMMAND_PASS full_read_BL8=4 full_write_BL8=4 physical_words=32 logical_bytes=64 masked_write_bytes=0");
  end
  // Every one of32physical write-beat abort positions, acrossall4bursts.
  for(k=1;k<=32;k=k+1)begin: write_abort_all
   logic[511:0]data;integer expected_beats;
   data=make_pattern(k+1900);prior_writes=model.writes;expected_beats=((k+7)/8)*8;
   @(negedge clk);write_valid=1;write_generation=1900+k;write_bank=1;write_plane=1;write_index=99;write_pixels=data;
   do @(posedge clk);while(!write_ready);
   @(negedge clk);write_valid=0;
   while(model.writes-prior_writes<k)@(negedge clk);
   abort_i=1;@(posedge clk);@(negedge clk);abort_i=0;
   while(tile_busy)begin if(write_done_valid||read_rsp_valid)$fatal(1,"directwriteabortsuccessleak");@(negedge clk);end
   if(!tile_aborted||model.writes-prior_writes!=expected_beats)$fatal(1,"directwriteabortdraincount");
   for(integer n=0;n<expected_beats;n=n+1)begin
    aux(0,CANONICAL1_BASE+24'd172800+24'(99*32+n),0,0,got);
    if(got!==data[n*16+:16])$fatal(1,"directacceptedwriteburstnotfullystored");
   end
   checks=checks+1;aborts=aborts+1;
  end
  // Read-data abort at every one of32accepted responsebeats. A full tile
  // is never exposed from a canceled transaction; accepted BL8alwaysdrains.
  for(k=1;k<=32;k=k+1)begin: read_abort_all
   integer old_beats,old_reads;old_beats=pin_read_beats;old_reads=completed_reads;
   @(negedge clk);read_valid=1;read_generation=2000+k;read_bank=2;read_plane=2;read_index=1349;
   do @(posedge clk);while(!read_ready);
   @(negedge clk);read_valid=0;
   while(pin_read_beats-old_beats<k)@(negedge clk);
   abort_i=1;@(posedge clk);@(negedge clk);abort_i=0;
   while(tile_busy)begin if(read_rsp_valid||write_done_valid)$fatal(1,"directreadabortsuccessleak");@(negedge clk);end
   if(!tile_aborted||completed_reads-old_reads!=(k+7)/8)$fatal(1,"directreadabortdraincount");
   checks=checks+1;aborts=aborts+1;
  end
  $display("CU71_DIRECT_ABORT_ALL_PASS write_positions=32 read_positions=32");
  write_tile(0,2,333,make_pattern(13171),0);
  fork
   begin: direct_reference_concurrent
    integer n,start_cycle,max_cycles,prior_cmds;max_cycles=0;prior_cmds=canonical_read_commands;
    for(n=0;n<4;n=n+1)begin
     start_cycle=cycles;read_tile(0,2,333,make_pattern(13171),0);
     if(cycles-start_cycle>max_cycles)max_cycles=cycles-start_cycle;
    end
    if(canonical_read_commands-prior_cmds!=16)$fatal(1,"directconcurrentfourBL8perreference");
    $display("CU71_DIRECT_REFERENCE_CONTENDED tiles=4 actual_BL8_reads=%0d max_tile_cycles=%0d",canonical_read_commands-prior_cmds,max_cycles);
   end
   begin: direct_aux_concurrent
    integer n;logic[15:0]v;
    for(n=0;n<64;n=n+1)aux(1,HUD2_BASE+24'(n),16'(n+13),0,v);
   end
   begin: direct_LCD_concurrent
    integer n,m;
    for(n=0;n<32;n=n+1)begin
     @(negedge clk);lcd_req_valid=1;lcd_req_addr=RGB0_BASE;
     do @(posedge clk);while(!lcd_req_ready);
     @(negedge clk);lcd_req_valid=0;while(!lcd_rsp_valid)@(negedge clk);
     if(lcd_rsp_error)$fatal(1,"directconcurrentLCDerror");
     for(m=0;m<8;m=m+1)if(lcd_rsp_data[m*16+:16]!==16'(16'h6000+m))$fatal(1,"directconcurrentLCDwrongowner");
     lcd_rsp_ready=1;@(posedge clk);@(negedge clk);lcd_rsp_ready=0;
    end
   end
  join
'''
needle='  prior_refreshes=model.refreshes;';assert tb.count(needle)==1;tb=tb.replace(needle,extra+needle)
tb=tb.replace('CU71_MEMORY_PASS','CU71_DIRECT_MEMORY_PASS')
(o/'tb.sv').write_text(tb,newline='\n');(o/'runner.py').write_bytes(Path(__file__).read_bytes())
sources=files+['model.sv','primitives.sv','tb.sv'];(o/'source-freeze.json').write_text(json.dumps({n:sha(o/n)for n in sources+['cu70_memory_map.svh','runner.py']},indent=2)+'\n')
env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env.get('PATH','');steps=[]
for label,cmd in [('compile',['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-s','tb_memory','-I',str(o),'-o',str(o/'test.vvp'),*[str(o/n)for n in sources]]),('simulation',['C:/msys64/ucrt64/bin/vvp.exe','-i',str(o/'test.vvp'),'+SEED='+str(a.seed)])]:
 t=time.monotonic()
 with(o/(label+'.log')).open('wb')as f:q=subprocess.run(cmd,cwd=o,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=600)
 steps.append({'label':label,'command':cmd,'returncode':q.returncode,'seconds':time.monotonic()-t});(o/'execution.json').write_text(json.dumps(steps,indent=2)+'\n')
 print(label,q.returncode,flush=True);assert q.returncode==0,(label,o)
log=(o/'simulation.log').read_text();assert 'CU71_DIRECT_MEMORY_PASS'in log and 'CU71_DIRECT_TILE_COMMAND_PASS'in log and 'CU71_DIRECT_ABORT_ALL_PASS'in log
(o/'result.json').write_text(json.dumps({'status':'PASS_TILE_MAJOR_FOUR_FULL_BL8_CANONICAL_MEMORY_COMPONENT','slow':a.slow,'seed':a.seed,'hardware':False,'routed_timing':False,'layout':'tileIndex*32words +localRowMajorSample/2;planesizes/basesunchanged','scope':'Allplanes/banks/edges/guards/scalarphysicaloracle/actual4read+4writecommands,32read+32writeacceptedbeatabortpositions,aux/LCDisolation. NotcompleteCU66/directdisplay/30fps.'},indent=2)+'\n')
