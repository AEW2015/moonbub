"""Four-state goldens/recovery tests for valid-fenced payload reset removal."""
from pathlib import Path
import argparse, hashlib, json, os, shutil, subprocess, time

root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--output', required=True)
args = parser.parse_args()
out = (root/args.output).resolve()
out.mkdir(parents=True, exist_ok=False)
candidate = root/'fpga/experiments/cu66-v71/inverse-reset'
inverse = root/'fpga/experiments/cu66-v69/inverse'
dequant = root/'fpga/experiments/cu66-v71/dequant'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
sources = [candidate/name for name in
    ['cu71_idct_resetlight.sv','cu71_dequant_resetlight.sv','cu71_reconstruct_resetlight.sv']]
sources += [inverse/'cu66_quant_rom.svh', inverse/'cu66_dequant.sv']
pins = {p.relative_to(root).as_posix():sha(p) for p in sources}
for path in sources:
    shutil.copyfile(path, out/path.name)

idct = (inverse/'tb_idct.sv').read_text().replace('cu66_idct8x8 dut', 'cu71_idct_resetlight dut')
idct = idct.replace('repeat(3)tick();@(negedge clk);rst=0;',
    'repeat(3)tick();if(!$isunknown(out_tile))$fatal(1,"payload unexpectedly initialized");@(negedge clk);rst=0;')
(out/'tb_idct.sv').write_text(idct, newline='\n')
math = (inverse/'tb_math.sv').read_text().replace('cu66_dequant dq', 'cu71_dequant_resetlight dq').replace('cu66_reconstruct_tile rc','cu71_reconstruct_resetlight rc')
math = math.replace('repeat(3)tick();@(negedge clk);rst=0;',
    'repeat(3)tick();if(!$isunknown(dq_output)||!$isunknown(rc_output))$fatal(1,"payload unexpectedly initialized");@(negedge clk);rst=0;')
(out/'tb_math.sv').write_text(math, newline='\n')
dq = (dequant/'tb_dequant.sv').read_text().replace('cu71_dequant_pipe dut','cu71_dequant_resetlight dut')
assert dq.count('out_dequantized!==0||ref_tile!==0') == 1
dq = dq.replace('out_dequantized!==0||ref_tile!==0','out_valid||ref_tile!==0')
dq = dq.replace('repeat(3)tick();@(negedge clk);rst=0;',
    'repeat(3)tick();if(!$isunknown(out_dequantized))$fatal(1,"payload unexpectedly initialized");@(negedge clk);rst=0;')
(out/'tb_dequant.sv').write_text(dq, newline='\n')
fixtures = [inverse/'tiles.hex',inverse/'dequant.hex',inverse/'reconstruct.hex']
fixtures += [dequant/'evidence/proof-synth01'/name for name in ['gameplay.hex','directed.hex']]
for path in fixtures:
    pins[path.relative_to(root).as_posix()] = sha(path)
env = dict(os.environ, PATH='C:/msys64/ucrt64/bin;'+os.environ['PATH'])
steps = []
def run(label, command):
    start = time.monotonic()
    with (out/(label+'.log')).open('wb') as stream:
        proc = subprocess.run(list(map(str,command)), env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=900)
    steps.append(dict(label=label,command=list(map(str,command)),returncode=proc.returncode,seconds=time.monotonic()-start,log_sha256=sha(out/(label+'.log'))))
    (out/'execution.json').write_text(json.dumps(steps,indent=2)+'\n')
    assert proc.returncode == 0, (label,out/(label+'.log'))
    print(label,'PASS',flush=True)
    return (out/(label+'.log')).read_text()

iv = 'C:/msys64/ucrt64/bin/iverilog.exe'
vv = 'C:/msys64/ucrt64/bin/vvp.exe'
run('idct-compile',[iv,'-g2012','-s','tb_idct','-o',out/'idct.vvp',out/'cu71_idct_resetlight.sv',out/'tb_idct.sv'])
for seed in [69004501,69004502]:
    text=run('idct-seed'+str(seed),[vv,out/'idct.vvp','+FIXTURE='+str(inverse/'tiles.hex'),'+SEED='+str(seed)])
    assert 'CU66_IDCT_TEST_PASS tiles=3471' in text
run('math-compile',[iv,'-g2012','-I',out,'-s','tb_math','-o',out/'math.vvp',out/'cu71_dequant_resetlight.sv',out/'cu71_reconstruct_resetlight.sv',out/'tb_math.sv'])
assert 'CU66_MATH_TEST_PASS dequant=1536 reconstruct=1536' in run('math',[vv,out/'math.vvp','+FIXTURES='+str(inverse)])
run('dequant-compile',[iv,'-g2012','-I',out,'-s','tb_dequant','-o',out/'dequant.vvp',out/'cu71_dequant_resetlight.sv',out/'cu66_dequant.sv',out/'tb_dequant.sv'])
for name,path in [('normative',inverse/'dequant.hex'),('gameplay',fixtures[-2]),('directed',fixtures[-1])]:
    assert 'reset_abort_points=26' in run('dequant-'+name,[vv,out/'dequant.vvp','+FIXTURE='+str(path)])
assert pins == {name:sha(root/name) for name in pins}
(out/'result.json').write_text(json.dumps(dict(
    status='PASS_FOUR_STATE_VALID_PAYLOAD_GOLDENS_AND_RESET_ABORT_REPLAY',source_sha256=pins,
    idct_tiles_per_seed=3471,idct_seeds=2,dequant_tiles=7081,reconstruction_tiles=1536,
    dequant_reset_abort_replays=78, invalid_payload='Explicitly unspecified; initial payload checked unknown in four-state simulation',
    pipeline_latency_changed=False,hardware=False,routed_timing=False,
),indent=2)+'\n')
print('RESETLIGHT_VALID_PAYLOAD_PASS_NOT_TIMING_OR_HARDWARE')
