#!/usr/bin/env python3
"""Run dequantization/reconstruction contracts on two independent simulators."""
from pathlib import Path
import argparse,hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/'fpga/experiments/cu66-v69/inverse'

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--container',default='gamebub-cu66-v69-build');args=parser.parse_args()
    result_dir=HERE/'math-results';result_dir.mkdir(exist_ok=True)
    sources=[HERE/n for n in ['cu66_dequant.sv','cu66_quant_rom.svh','cu66_reconstruct_tile.sv','tb_math.sv','export_math.py','math-fixtures.json','dequant.hex','reconstruct.hex']]
    before={p.relative_to(ROOT).as_posix():digest(p)for p in sources}
    prefix=['docker','exec','-w','/build',args.container]
    commands=[
        ('verilator-compile',prefix+['timeout','120s','verilator','--binary','--timing','--assert','--Wall','--top-module','tb_math','--Mdir','/build/math','-j','2','+incdir+'+str(HERE),str(HERE/'cu66_dequant.sv'),str(HERE/'cu66_reconstruct_tile.sv'),str(HERE/'tb_math.sv')],False),
        ('verilator-run',prefix+['timeout','90s','/build/math/Vtb_math','+FIXTURES='+str(HERE)],True),
        ('icarus-compile',prefix+['timeout','120s','iverilog','-g2012','-I',str(HERE),'-s','tb_math','-o','/build/math-icarus',str(HERE/'cu66_dequant.sv'),str(HERE/'cu66_reconstruct_tile.sv'),str(HERE/'tb_math.sv')],False),
        ('icarus-run',prefix+['timeout','90s','vvp','/build/math-icarus','+FIXTURES='+str(HERE)],True)]
    results=[]
    for name,cmd,require_pass in commands:
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=150)
        content=p.stdout+p.stderr;(result_dir/(name+'.log')).write_text(content)
        p.check_returncode()
        if require_pass:assert 'CU66_MATH_TEST_PASS dequant=1536 reconstruct=1536'in content,name
        results.append({'name':name,'command':cmd,'returncode':p.returncode,'terminal_PASS_required':require_pass,'log_sha256':digest(result_dir/(name+'.log'))})
        print(name,'PASS',flush=True)
    assert before=={p.relative_to(ROOT).as_posix():digest(p)for p in sources}
    output={'schema':'cu66-math-v69-regression','source_sha256':before,'runs':results,'dequant_cases_per_backend':1536,'reconstruct_cases_per_backend':1536,
            'scope':['Signed dequantization and clipped key/zero-motion/hidden reconstruction; input/output stalls and reference latency.','No integration with entropy/DDR/physical scanout in this component regression.','Icarus constant-select sensitivity notices retained. Verilator Wall clean. No FPGA timing/fit/FPS result.']}
    (result_dir/'results.json').write_text(json.dumps(output,indent=2)+'\n')
if __name__=='__main__':main()
