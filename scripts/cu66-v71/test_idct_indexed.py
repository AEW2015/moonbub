"""Four-state native goldens and exact-cycle parent comparison, no hardware."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time
root=Path(__file__).resolve().parents[2]
a=argparse.ArgumentParser();a.add_argument('--output',required=True);args=a.parse_args()
out=(root/args.output).resolve();out.mkdir(parents=True,exist_ok=False)
candidate=root/'fpga/experiments/cu66-v71/inverse-index/cu71_idct_indexed.sv'
parent=root/'fpga/experiments/cu66-v71/inverse-reset/cu71_idct_resetlight.sv'
fixture=root/'fpga/experiments/cu66-v69/inverse/tiles.hex'
bench=root/'fpga/experiments/cu66-v69/inverse/tb_idct.sv'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pins={p.relative_to(root).as_posix():sha(p)for p in[candidate,parent,fixture,bench,Path(__file__)]}
for p in[candidate,parent]:shutil.copyfile(p,out/p.name)
text=bench.read_text().replace('cu66_idct8x8 dut','cu71_idct_indexed dut')
anchor='    cu71_idct_indexed dut(.*);'
assert text.count(anchor)==1
text=text.replace(anchor,anchor+'''
    logic reference_in_ready,reference_out_valid,reference_out_error;
    logic[31:0]reference_out_id,reference_active_cycles;
    logic[1535:0]reference_out_tile;
    cu71_idct_resetlight reference(.clk,.rst,.abort_frame,.in_valid,.in_ready(reference_in_ready),
      .in_id,.in_tile,.out_valid(reference_out_valid),.out_ready,.out_id(reference_out_id),
      .out_tile(reference_out_tile),.out_error(reference_out_error),.active_cycles(reference_active_cycles));
    integer cycle_comparisons=0;
    always @(posedge clk)begin
      #2;
      if(in_ready!==reference_in_ready || out_valid!==reference_out_valid ||
         active_cycles!==reference_active_cycles || dut.state!==reference.state ||
         dut.group_index!==reference.group_index || dut.k!==reference.k ||
         out_id!==reference_out_id || out_error!==reference_out_error)
        $fatal(1,"public/control cycle mismatch at %0d",cycle_comparisons);
      if(out_valid && out_tile!==reference_out_tile)$fatal(1,"valid payload differs from parent");
      cycle_comparisons=cycle_comparisons+1;
    end
''')
text=text.replace('repeat(3)tick();@(negedge clk);rst=0;',
 'repeat(3)tick();if(!$isunknown(out_tile))$fatal(1,"payload unexpectedly initialized");@(negedge clk);rst=0;')
(out/'tb_idct.sv').write_text(text,newline='\n')
(out/'source-freeze.json').write_text(json.dumps(pins,indent=2)+'\n')
env=dict(os.environ,PATH='C:/msys64/ucrt64/bin;'+os.environ['PATH']);steps=[]
def run(label,cmd):
 start=time.monotonic()
 with(out/(label+'.log')).open('wb')as stream:p=subprocess.run(list(map(str,cmd)),stdout=stream,stderr=subprocess.STDOUT,env=env,timeout=1200)
 steps.append(dict(label=label,command=list(map(str,cmd)),returncode=p.returncode,seconds=time.monotonic()-start,log_sha256=sha(out/(label+'.log'))))
 (out/'execution.json').write_text(json.dumps(steps,indent=2)+'\n');assert p.returncode==0,(label,out)
 print(label,'PASS',flush=True);return(out/(label+'.log')).read_text()
run('compile',['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-s','tb_idct','-o',out/'idct.vvp',out/candidate.name,out/parent.name,out/'tb_idct.sv'])
for seed in[69004501,69004502]:
 text=run('seed'+str(seed),['C:/msys64/ucrt64/bin/vvp.exe',out/'idct.vvp','+FIXTURE='+str(fixture),'+SEED='+str(seed)])
 assert 'CU66_IDCT_TEST_PASS tiles=3471'in text
assert pins=={name:sha(root/name)for name in pins}
(out/'result.json').write_text(json.dumps(dict(status='PASS_EXACT_CYCLE_PARENT_AND_3471_GOLDENS_TWO_SEEDS',source_sha256=pins,
 payload_comparison='Only valid payload; initial payload deliberately unknown in four-state simulation',
 cycle_comparison='Ready/valid/ID/error/active_cycles and original state/group/k every clock',
 added_latency_cycles=0,hardware=False,routed_timing=False),indent=2)+'\n')
print('INDEXED_IDCT_FUNCTIONAL_PASS_NOT_TIMING_OR_HARDWARE')
