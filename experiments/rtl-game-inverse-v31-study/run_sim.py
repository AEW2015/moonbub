#!/usr/bin/env python3
"""Portable Docker-based bounded RTL regression; no board interaction."""
from pathlib import Path
import argparse,hashlib,json,os,re,subprocess,zlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--work',required=True);ap.add_argument('--image',default='gamebub-codec-sim:v31');args=ap.parse_args()
    work=Path(args.work).resolve();work.mkdir(parents=True,exist_ok=True);fixtures=work/'fixtures';fixtures.mkdir(exist_ok=True)
    m=json.loads((HERE/'vectors.json').read_text())
    for name,d in m['files'].items():
        packed=(HERE/d['path']).read_bytes();assert hashlib.sha256(packed).hexdigest()==d['stored_sha256']
        dc=zlib.decompressobj();raw=dc.decompress(packed,d['raw_bytes']+1)
        assert dc.eof and not dc.unused_data and not dc.unconsumed_tail and len(raw)==d['raw_bytes'] and hashlib.sha256(raw).hexdigest()==d['raw_sha256']
        (fixtures/(name+'.mem')).write_bytes(raw)
    (fixtures/'vector_config.vh').write_text(f'localparam integer VECTOR_BLOCKS={m["blocks"]};\nlocalparam integer DIRECTED_BLOCKS={m["directed_random_blocks"]};\n')
    prefix=['docker','run','--rm','--cpus=2','--memory=4g','--network=none','--user',f'{os.getuid()}:{os.getgid()}','-v',str(ROOT)+':/src:ro','-v',str(work)+':/build','-w','/build',args.image]
    rel=HERE.relative_to(ROOT).as_posix();dut='/src/'+rel+'/inverse_q14.sv';tb='/src/'+rel+'/tb_inverse_q14.sv'
    def run(name,command,timeout=240):
        with (work/name).open('w') as log:
            result=subprocess.run(prefix+command,stdout=log,stderr=subprocess.STDOUT,timeout=timeout)
        if result.returncode:raise RuntimeError(f'{name} failed: {(work/name).read_text()[-4000:]}')
    run('versions.log',['sh','-c','verilator --version; iverilog -V; yosys -V'])
    run('lint.log',['verilator','--lint-only','--timing','--assert','--top-module','tb_inverse_q14','-I/build/fixtures',dut,tb])
    reports=[]
    for bypass in (0,1):
        run(f'build-{bypass}.log',['verilator','--binary','-j','2','--timing','--assert','--top-module','tb_inverse_q14',f'-GBYPASS={bypass}','-I/build/fixtures','--Mdir',f'/build/obj-{bypass}',dut,tb])
        for stalls in ((0,) if bypass==0 else (0,1)):
            name=f'run-{bypass}-{stalls}.log'
            run(name,[f'/build/obj-{bypass}/Vtb_inverse_q14','+FIXTURES=/build/fixtures',f'+STALL={stalls}'],timeout=240)
            text=(work/name).read_text();assert 'RESET_ABORT_PASS' in text
            found=re.search(r'TEST_PASS blocks=(\d+) samples=(\d+) bypass=(\d+) stalls=(\d+) service_cycles=(\d+) elapsed_cycles=(\d+) output_stall_cycles=(\d+)',text);assert found,name
            assert not re.search(r'\b(Fatal|ERROR|Error|MISMATCH|TIMEOUT)\b',text),name
            blocks=[tuple(map(int,t)) for t in re.findall(r'^BLOCK id=(\d+) kind=(\d+) cycles=(\d+)$',text,re.M)]
            assert len(blocks)==m['blocks'] and [b[0] for b in blocks]==list(range(m['blocks']))
            frames=[]
            for group in m['groups']:
                if 'scene' not in group:continue
                chosen=blocks[group['start_block']:group['start_block']+group['blocks']]
                frames.append(dict(scene=group['scene'],frame_id=group['frame_id'],blocks=len(chosen),service_cycles=sum(b[2] for b in chosen),
                                   projection_ms_at_assumed_100MHz=sum(b[2] for b in chosen)/100000))
            reports.append(dict(bypass=bypass,stalls=stalls,blocks=int(found[1]),samples=int(found[2]),service_cycles=int(found[5]),elapsed_cycles=int(found[6]),
                                output_stall_cycles=int(found[7]),frames=frames,log=name,
                                cycles_by_kind={str(k):sorted({b[2] for b in blocks if b[1]==k}) for k in (0,1,2)}))
            print(json.dumps(dict(simulation=name,summary=reports[-1])),flush=True)
    run('iverilog-build.log',['iverilog','-g2012','-s','tb_inverse_q14','-Ptb_inverse_q14.SHORT=1','-I/build/fixtures','-o','/build/iverilog.vvp',dut,tb])
    run('iverilog-run.log',['vvp','/build/iverilog.vvp','+FIXTURES=/build/fixtures','+STALL=1'],timeout=240)
    text=(work/'iverilog-run.log').read_text();assert f'TEST_PASS blocks={m["directed_random_blocks"]}' in text and 'RESET_ABORT_PASS' in text
    run('yosys.log',['yosys','-p',f'read_verilog -sv {dut}; synth_xilinx -family xc7 -top inverse_q14; check; write_json /build/mapped.json; write_verilog -noattr /build/mapped.v; tee -o /build/yosys-stat.json stat -json'],timeout=240)
    mapped=json.loads((work/'mapped.json').read_text());cells=mapped['modules']['inverse_q14']['cells'];counts={}
    for cell in cells.values():counts[cell['type']]=counts.get(cell['type'],0)+1
    run('mapped-build.log',['iverilog','-g2012','-DMAPPED','-s','tb_inverse_q14','-Ptb_inverse_q14.SHORT=1','-I/build/fixtures','-o','/build/mapped.vvp','/build/mapped.v','/usr/share/yosys/xilinx/cells_sim.v',tb])
    run('mapped-run.log',['vvp','/build/mapped.vvp','+FIXTURES=/build/fixtures','+STALL=1'],timeout=600)
    text=(work/'mapped-run.log').read_text();assert f'TEST_PASS blocks={m["directed_random_blocks"]}' in text and 'RESET_ABORT_PASS' in text
    image_id=subprocess.check_output(['docker','image','inspect',args.image,'--format','{{.Id}}'],text=True).strip()
    output=dict(schema='gamebub-rtl-q14-v31',tool_image_id=image_id,vectors_sha256=hashlib.sha256((HERE/'vectors.json').read_bytes()).hexdigest(),
                source_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (HERE/'inverse_q14.sv',HERE/'tb_inverse_q14.sv',HERE/'run_sim.py',HERE/'Dockerfile')},
                simulations=reports,iverilog_directed_blocks=m['directed_random_blocks'],mapped_directed_blocks=m['directed_random_blocks'],
                mapped_cell_counts=counts,
                physical_30fps_proven=False,vivado_timing_closed=False,full_decoder_implemented=False)
    (work/'results.json').write_text(json.dumps(output,indent=2,sort_keys=True)+'\n')
    print('RTL_Q14_REGRESSION_PASS',flush=True)

if __name__=='__main__':main()
