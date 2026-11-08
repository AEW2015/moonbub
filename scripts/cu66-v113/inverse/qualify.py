#!/usr/bin/env python3
"""Reproducible V113 inverse-only independent golden/accepted-event proof (Verilator)."""
import argparse,datetime,hashlib,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'fpga/experiments/cu66-v113-inverse';AREA=ROOT/'experiments/python-gamebub-v113/inverse'
IMAGE='gamebub-cu66-v69-tools:20261105'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',action='store_true');a=ap.parse_args()
 paths=[SRC/'cu66_inverse_stream_v91j.sv',SRC/'tb_inverse.cpp',ROOT/'fpga/experiments/cu66-v110-dequant/cu66_dequant.sv',ROOT/'fpga/experiments/cu66-v108-outtile/cu66_idct8x8.sv',ROOT/'fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh',ROOT/'experiments/python-gamebub-v91j/vectors/boundary.tsv',Path(__file__)]
 if not a.run:print('V113_INVERSE_PREPARED_NOT_RUN');return
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True)
 build=Path('/home/lori/gamebub-build/cu66-v69')/('v113-inverse-'+stamp);build.mkdir();mapped='/build/'+build.name
 receipt=dict(schema='v113-inverse-owned-accept-results-v1',status='FAIL',backend='Verilator',assertions_disabled_or_downgraded=False,source_sha256={str(p.relative_to(ROOT)):sha(p) for p in paths},commands=[],runs=[])
 for p in paths:
  shutil.copyfile(p,build/p.name);snap=out/'sources'/p.relative_to(ROOT);snap.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,snap)
 def run(argv,name,cap):
  cmd=['docker','run','--rm','--init','--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv]
  receipt['commands'].append(cmd);t=time.monotonic()
  with (out/name).open('w')as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=cap+20,check=True)
  receipt.setdefault('wall_seconds',{})[name]=time.monotonic()-t
 try:
  run(['verilator','--version'],'version.log',30)
  run(['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--public-flat-rw','--output-split','10000','--output-split-cfuncs','500','--language','1800-2017','-I'+mapped,'-CFLAGS','-std=c++17 -O1 -Wall -Wextra -Werror','--top-module','cu66_inverse_stream_v91j','--Mdir',mapped+'/obj',*[mapped+'/'+n for n in ('cu66_inverse_stream_v91j.sv','cu66_dequant.sv','cu66_idct8x8.sv','tb_inverse.cpp')]],'compile.log',600)
  assert '%Warning-' not in (out/'compile.log').read_text()
  for seed in (113101,113102):
   run([mapped+'/obj/Vcu66_inverse_stream_v91j',mapped+'/boundary.tsv',str(seed)],f'run-{seed}.log',120)
   result=json.loads((out/f'run-{seed}.log').read_text().splitlines()[-1]);assert result['status']=='TEST_PASS';receipt['runs'].append(result)
  assert receipt['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in paths};receipt['status']='PASS'
 except BaseException as e:receipt['error']=repr(e);raise
 finally:
  receipt['artifact_sha256']={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()}
  (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');(AREA/'selected.json').write_text(json.dumps(dict(path=str((out/'receipt.json').relative_to(ROOT)),sha256=sha(out/'receipt.json'),status=receipt['status']),indent=2)+'\n');print(receipt['status'],out,flush=True)
if __name__=='__main__':main()
