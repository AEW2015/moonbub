"""Four-state goldens plus latency-aligned parent and abort/stall behavior."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,time
r=Path(__file__).resolve().parents[2]
out=r/'fpga/experiments/cu66-v71/inverse-validpipe/evidence/functional01'
out.mkdir(parents=True,exist_ok=False)
candidate=r/'fpga/experiments/cu66-v71/inverse-validpipe/cu71_idct_validpipe.sv'
parent=r/'fpga/experiments/cu66-v71/inverse-index/cu71_idct_indexed.sv'
fixture=r/'fpga/experiments/cu66-v69/inverse/tiles.hex'
bench=r/'fpga/experiments/cu66-v69/inverse/tb_idct.sv'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pins={p.relative_to(r).as_posix():sha(p)for p in[candidate,parent,fixture,bench,Path(__file__)]}
for p in[candidate,parent]:shutil.copyfile(p,out/p.name)
t=bench.read_text().replace('cu66_idct8x8 dut','cu71_idct_validpipe dut')
anchor='    cu71_idct_validpipe dut(.*);'
assert t.count(anchor)==1
t=t.replace(anchor,anchor+'''
    logic parent_pending=0,parent_ready,parent_valid,parent_error;
    logic [1279:0] parent_tile;
    logic [31:0] parent_id,parent_out_id,parent_cycles;
    logic [1535:0] parent_out_tile;
    integer compared=0;
    always @(posedge clk)begin
        if(rst || abort_frame)parent_pending<=0;
        else parent_pending<=in_valid && in_ready;
        if(in_valid && in_ready)begin parent_tile<=in_tile;parent_id<=in_id;end
    end
    cu71_idct_indexed reference(.clk,.rst,.abort_frame,.in_valid(parent_pending),
        .in_ready(parent_ready),.in_tile(parent_tile),.in_id(parent_id),
        .out_valid(parent_valid),.out_ready,.out_id(parent_out_id),
        .out_tile(parent_out_tile),.out_error(parent_error),.active_cycles(parent_cycles));
    always @(posedge clk)begin
        #2;
        if(out_valid!==parent_valid)$fatal(1,"latency-aligned valid mismatch");
        if(out_valid)begin
            if(out_tile!==parent_out_tile || out_id!==parent_out_id || out_error!==parent_error ||
               active_cycles!==parent_cycles+1)$fatal(1,"latency-aligned result/cycle mismatch");
            compared=compared+1;
        end
    end
''')
t=t.replace('repeat(3)tick();@(negedge clk);rst=0;',
 'repeat(3)tick();if(!$isunknown(out_tile))$fatal(1,"payload unexpectedly initialized");@(negedge clk);rst=0;')
(out/'tb_idct.sv').write_text(t,newline='\n')
(out/'source-freeze.json').write_text(json.dumps(pins,indent=2)+'\n')
env=dict(os.environ,PATH='C:/msys64/ucrt64/bin;'+os.environ['PATH']);steps=[]
def run(label,cmd):
 start=time.monotonic()
 with(out/(label+'.log')).open('wb')as f:p=subprocess.run(list(map(str,cmd)),stdout=f,stderr=subprocess.STDOUT,env=env,timeout=1200)
 steps.append(dict(label=label,command=list(map(str,cmd)),returncode=p.returncode,seconds=time.monotonic()-start,log_sha256=sha(out/(label+'.log'))))
 (out/'execution.json').write_text(json.dumps(steps,indent=2)+'\n')
 assert p.returncode==0,(label,out)
 print(label,'PASS',flush=True)
 return(out/(label+'.log')).read_text()
run('compile',['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-s','tb_idct','-o',out/'idct.vvp',out/candidate.name,out/parent.name,out/'tb_idct.sv'])
for seed in[69004501,69004502]:
 log=run('seed'+str(seed),['C:/msys64/ucrt64/bin/vvp.exe',out/'idct.vvp','+FIXTURE='+str(fixture),'+SEED='+str(seed)])
 assert 'CU66_IDCT_TEST_PASS tiles=3471' in log
assert pins=={n:sha(r/n)for n in pins}
(out/'result.json').write_text(json.dumps(dict(status='PASS_3471_GOLDENS_TWO_SEEDS_AND_ONE_CYCLE_DELAY_ALIGNED_PARENT',
 source_sha256=pins,added_latency_cycles=1,initial_payload='FOUR_STATE_UNKNOWN',
 abort_reset_stall='Original golden bench cancel/replay cases retained',
 limits=['Not cycle-identical to parent; one extra work cycle and valid/error publication stage.',
         'No synthesis, full-system, routed timing or physical qualification.'],hardware=False),indent=2)+'\n')
