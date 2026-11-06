"""Real dequant goldens/recovery, parent oracle and poisoned live input."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,time
r=Path(__file__).resolve().parents[2]
out=r/'fpga/experiments/cu66-v71/dequant-validpipe/evidence/functional01';out.mkdir(parents=True,exist_ok=False)
candidate=r/'fpga/experiments/cu66-v71/dequant-validpipe/cu71_dequant_validpipe.sv'
inv=r/'fpga/experiments/cu66-v69/inverse';dq=r/'fpga/experiments/cu66-v71/dequant'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sources=[candidate,inv/'cu66_dequant.sv',inv/'cu66_quant_rom.svh',dq/'tb_dequant.sv',Path(__file__)]
fixtures=[inv/'dequant.hex',dq/'evidence/proof-synth01/gameplay.hex',dq/'evidence/proof-synth01/directed.hex']
pins={p.relative_to(r).as_posix():sha(p)for p in sources+fixtures}
for p in sources[:3]:shutil.copyfile(p,out/p.name)
t=(dq/'tb_dequant.sv').read_text().replace('cu71_dequant_pipe dut','cu71_dequant_validpipe dut')
t=t.replace('out_dequantized!==0||ref_tile!==0','out_valid||ref_tile!==0')
t=t.replace('delay_count<13','delay_count<14')
t=t.replace('repeat(3)tick();@(negedge clk);rst=0;',
 'repeat(3)tick();if(!$isunknown(out_dequantized))$fatal(1,"payload unexpectedly initialized");@(negedge clk);rst=0;')
(out/'tb.sv').write_text(t,newline='\n');(out/'source-freeze.json').write_text(json.dumps(pins,indent=2)+'\n')
env=dict(os.environ,PATH='C:/msys64/ucrt64/bin;'+os.environ['PATH']);steps=[]
def run(label,cmd):
 start=time.monotonic()
 with(out/(label+'.log')).open('wb')as f:p=subprocess.run(list(map(str,cmd)),stdout=f,stderr=subprocess.STDOUT,env=env,timeout=900)
 steps.append(dict(label=label,command=list(map(str,cmd)),returncode=p.returncode,seconds=time.monotonic()-start,log_sha256=sha(out/(label+'.log'))))
 (out/'execution.json').write_text(json.dumps(steps,indent=2)+'\n');assert p.returncode==0,(label,out)
 print(label,'PASS',flush=True);return(out/(label+'.log')).read_text()
run('compile',['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-I',out,'-s','tb_dequant','-o',out/'sim.vvp',out/candidate.name,out/'cu66_dequant.sv',out/'tb.sv'])
counts=[]
for f in fixtures:
 text=run(f.stem,['C:/msys64/ucrt64/bin/vvp.exe',out/'sim.vvp','+FIXTURE='+str(f)])
 assert 'PASS checked='in text and 'reset_abort_points=28' in text
 counts.append(text.splitlines()[-2:])
assert pins=={n:sha(r/n)for n in pins}
(out/'result.json').write_text(json.dumps(dict(status='PASS_REAL_DEQUANT_GOLDENS_PARENT_AND_RESET_ABORT_REPLAY',
 source_sha256=pins,logs=counts,added_work_cycles=1,initial_payload='FOUR_STATE_UNKNOWN',
 limit='New-state direct cancellation/metadata poison and synthesis/full-system gates separate',hardware=False),indent=2)+'\n')
