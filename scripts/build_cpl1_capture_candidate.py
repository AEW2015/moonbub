"""Source-bound implementation only; no bitstream emission or hardware access."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,time
root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--output');parser.add_argument('--candidate',default='fpga/candidates/cp23-sdram-capture135-20261105-v001');args=parser.parse_args()
c=(root/args.candidate).resolve()
out=Path(args.output).resolve() if args.output else c/'implementation01'
out.mkdir(parents=True,exist_ok=False)
for name,record in json.loads((c/'candidate.json').read_text())['changes'].items():
    assert hashlib.sha256((c/'inputs'/name).read_bytes()).hexdigest()==record['candidate_sha256']
shutil.copytree(c/'inputs',out/'inputs')
for n in ['key.cp23.hex','quantizers.hex']:shutil.copyfile(c/n,out/n)
(out/'source-freeze.json').write_text(json.dumps({str(f.relative_to(out)).replace('\\','/'):hashlib.sha256(f.read_bytes()).hexdigest()
    for f in out.rglob('*')if f.is_file()},indent=2)+'\n')
cmd=['C:/Xilinx/2025.2/Vivado/bin/vivado.bat','-mode','batch','-source',str(out/'inputs/build_board.tcl'),
     '-log',str(out/'vivado.log'),'-journal',str(out/'vivado.jou'),'-tclargs',str(out)]
started=time.monotonic();q=subprocess.run(cmd,cwd=out)
(out/'execution.json').write_text(json.dumps(dict(command=cmd,returncode=q.returncode,wall_seconds=time.monotonic()-started,
    scope='Implementation reports only; no BIT, no hardware'),indent=2)+'\n')
raise SystemExit(q.returncode)
