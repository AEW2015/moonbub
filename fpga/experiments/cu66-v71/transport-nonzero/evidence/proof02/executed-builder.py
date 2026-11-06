"""All-value two-state Gray zero/nonzero equivalence for a same-cycle flag."""
from pathlib import Path
import argparse,hashlib,json,shlex,shutil,subprocess
r=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--output',default='fpga/experiments/cu66-v71/transport-nonzero/evidence/proof02');a=p.parse_args()
out=r/a.output;out.mkdir(parents=True,exist_ok=False)
shutil.copyfile(__file__,out/'executed-builder.py')
sv='''module miter(input [31:0]gray,output mismatch);
wire[31:0]binary;
for(genvar i=0;i<32;i=i+1)assign binary[i]=^(gray>>i);
assign mismatch=(|binary)^(|gray);
endmodule
'''
(out/'miter.sv').write_text(sv,newline='\n')
lin=lambda p:'/mnt/'+p.resolve().drive[0].lower()+p.resolve().as_posix()[2:]
program='read_verilog -sv '+lin(out/'miter.sv')+'; prep -top miter; sat -prove mismatch 0 -show-inputs -show-outputs'
shell='source /opt/gamebub-openxc7-20261021/oss-cad-suite/environment && yosys -Q -T -p '+shlex.quote(program)
cmd=['wsl','-d','MRS-HDL-Research','--','bash','-lc',shell]
with(out/'yosys.log').open('wb')as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=120)
(out/'execution.json').write_text(json.dumps(dict(command=cmd,returncode=p.returncode),indent=2)+'\n')
assert p.returncode==0 and 'SUCCESS!'in(out/'yosys.log').read_text()
(out/'result.json').write_text(json.dumps(dict(status='PASS_ALL_32_BIT_TWO_STATE_GRAY_NONZERO_EQUIVALENCE',
 command=cmd,returncode=p.returncode,miter_sha256=hashlib.sha256((out/'miter.sv').read_bytes()).hexdigest(),
 log_sha256=hashlib.sha256((out/'yosys.log').read_bytes()).hexdigest(),
 intended_use='Register |transport_gray_sync on SAME core edge that previously registered ungray(transport_gray_sync), with same reset; no added cycle.',
 limits=['Combinational two-state proof, not metastability/CDC or unknown-state equivalence.',
         'No top selection or hardware change; prospective exact-reset/same-edge wrapper test required.'],hardware=False),indent=2)+'\n')
print('TRANSPORT_NONZERO_COMBINATIONAL_EQUIVALENCE_PASS')
