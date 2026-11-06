from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time
r=Path(__file__).resolve().parents[4];d=r/'fpga/experiments/cu66-v71/direct-display';a=argparse.ArgumentParser();a.add_argument('--output',required=True);a.add_argument('--variant',choices=['frozen','syncsafe'],default='syncsafe');args=a.parse_args();o=(r/args.output).resolve();o.mkdir(parents=True,exist_ok=False)
rtl=d/'cu71_lcd_lines_direct.sv'if args.variant=='frozen'else d/'cdc/cu71_lcd_lines_syncsafe.sv';tb=d/'cdc/tb_lcd_cdc.sv';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before={str(p.relative_to(r)):sha(p)for p in [rtl,tb,Path(__file__)]};shutil.copyfile(rtl,o/rtl.name);shutil.copyfile(tb,o/tb.name)
if args.variant=='syncsafe':
 p=o/tb.name;s=p.read_text().replace('cu71_lcd_lines_direct dut','cu71_lcd_lines_syncsafe dut')
 s=s.replace('integer checks=0,','integer raw_busy_frames=0;reg raw_event,pre_idle;integer checks=0,')
 s=s.replace('memcycles=memcycles+1;pre_admit=', 'raw_event=dut.frame_sync[1]!=dut.frame_seen;pre_idle=!dut.receiving&&!dut.line_req_valid&&!dut.address_pending&&dut.request_sync0[1]==dut.seen0&&dut.request_sync1[1]==dut.seen1;memcycles=memcycles+1;pre_admit=')
 s=s.replace('if(pre_admit)begin', 'if(raw_event&&!pre_idle)raw_busy_frames=raw_busy_frames+1;\n   if(pre_admit)begin')
 s=s.replace('held_requests>0&&late_frames>0','held_requests>0&&raw_busy_frames>0')
 s=s.replace('forever #17.03 pixel_clk=~pixel_clk','forever #17.028824833703 pixel_clk=~pixel_clk')
 s=s.replace('reg old_frame=0;', 'reg[31:0]gray_before;reg[31:0]gray_changed;reg old_frame=0;')
 s=s.replace('old_x=dut.x;old_y=dut.y;', 'gray_before=dut.underrun_gray;old_x=dut.x;old_y=dut.y;')
 s=s.replace('for(integer b=0;b<2;b=b+1)begin\n    reg token', 'gray_changed=dut.underrun_gray^gray_before;check((gray_changed&(gray_changed-1))==0,"Gray source must change at most one bit");\n   for(integer b=0;b<2;b=b+1)begin\n    reg token')
 p.write_text(s,newline='\n')
(o/'source-freeze.json').write_text(json.dumps(dict(original=before,executed={n:sha(o/n)for n in [rtl.name,tb.name]}),indent=2)+'\n');shutil.copyfile(Path(__file__),o/'executed-runner.py');env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+env.get('PATH','');steps=[]
def run(label,cmd):
 t=time.monotonic()
 with(o/(label+'.log')).open('wb')as f:q=subprocess.run(cmd,cwd=o,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=600)
 steps.append(dict(label=label,command=cmd,returncode=q.returncode,seconds=time.monotonic()-t));(o/'execution.json').write_text(json.dumps(steps,indent=2)+'\n');print(label,q.returncode,flush=True);assert q.returncode==0,(label,o)
for phase,seed in [(0,1),(9999,49001)]:
 run('compile'+str(phase),['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-s','tb_lcd_cdc','-Ptb_lcd_cdc.PHASE_PS='+str(phase),'-Ptb_lcd_cdc.SEED='+str(seed),'-o',str(o/'test.vvp'),str(o/rtl.name),str(o/tb.name)])
 run('phase'+str(phase),['C:/msys64/ucrt64/bin/vvp.exe','-i',str(o/'test.vvp')]);assert 'LCD_CDC_PROTOCOL_PASS'in(o/('phase'+str(phase)+'.log')).read_text()
assert before=={str(p.relative_to(r)):sha(p)for p in [rtl,tb,Path(__file__)]};(o/'result.json').write_text(json.dumps(dict(status='PASS_PHASE_HELD_PAYLOAD_BOUNDED_CAPTURE_AND_COORDINATED_RESET',sources=before,variant=args.variant,hardware=False,metastability_model=False,MTBF_qualified=False,board_reference_period_ns=34.057649667406,simulator_quantized_period_ns=34.058,source_gray_onebit_assertion=True),indent=2)+'\n')
