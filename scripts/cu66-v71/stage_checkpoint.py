"""Stage bounded development source/reports; omit images, tool databases and footage."""
from pathlib import Path
import argparse,datetime,hashlib,json,subprocess

root=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser()
parser.add_argument('--index',required=True)
parser.add_argument('--stage',action='store_true')
parser.add_argument('--exclude-prefix',action='append',default=[],help='Repository-relative active producer directory to omit')
args=parser.parse_args()
index=root/args.index
assert not index.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
allowed={'.sv','.svh','.v','.cpp','.hpp','.h','.rs','.py','.tcl','.xdc','.json','.md','.rpt','.log','.sh','.tsv'}
skip={'inputs','build','tmp','.Xil','__pycache__','target','python-deps','xsim.dir','.git'}
files=set()
for directory in [root/'docs/cu66-v71',root/'scripts/cu66-v71',root/'firmware/experiments/v35-cu71-local-fixture-20261105',root/'firmware/experiments/v36-dual-local-fixture-20261106']:
 for path in directory.rglob('*'):
  if path.is_file()and not any(part in skip for part in path.relative_to(directory).parts)and not any(path.relative_to(root).as_posix().startswith(prefix.rstrip('/')+'/')for prefix in args.exclude_prefix):files.add(path)
fpga=root/'fpga/experiments/cu66-v71'
omitted=[]
for path in fpga.rglob('*'):
 if not path.is_file():continue
 if any(path.relative_to(root).as_posix().startswith(prefix.rstrip('/')+'/') for prefix in args.exclude_prefix):continue
 parts=path.relative_to(fpga).parts
 if any(part in skip for part in parts):continue
 if parts[0]=='board'and len(parts)>1 and parts[1].startswith('implementation'):
  if path.name not in {'source-freeze.json','selection.json','execution.json','executed.tcl','synthesized-utilization.rpt','timing-summary.rpt','setup-paths.rpt','hold-paths.rpt','utilization.rpt','route-status.rpt','drc.rpt','cdc.rpt','exceptions.rpt','check-timing.rpt','bus-skew.rpt'}:continue
 if path.suffix.lower()in allowed and path.stat().st_size<=2_000_000:files.add(path)
 else:omitted.append(dict(path=path.relative_to(root).as_posix(),bytes=path.stat().st_size))
records={path.relative_to(root).as_posix():sha(path)for path in sorted(files)}
index.write_text(json.dumps(dict(status='DEVELOPMENT_SOURCE_AND_SELECTED_REPORTS_NOT_RELEASE',
 created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=records,
 omitted_scope='Images/checkpoints, generated objects, tool temporary files, vendor/dependency installations, large logs and footage remain local. This is not a complete Vivado image handoff.',
 omitted_selected_files=omitted,hardware_ready=False,CU66_network=False),indent=2)+'\n')
files.add(index)
list_path=root/'.git-cu71-stage-paths'
assert not list_path.exists()
list_path.write_bytes(b''.join(path.relative_to(root).as_posix().encode()+b'\0'for path in sorted(files)))
try:
 # Exact selected snapshots include intentionally ignored lock files and fonts.
 if args.stage:subprocess.run(['git','add','-f','--pathspec-from-file='+str(list_path),'--pathspec-file-nul'],cwd=root,check=True)
finally:list_path.unlink()
assert records=={name:sha(root/name)for name in records},'Selected file changed during snapshot; inspect index before commit'
print(json.dumps(dict(files=len(files),source_bytes=sum(path.stat().st_size for path in files),staged=args.stage,index=args.index)))
