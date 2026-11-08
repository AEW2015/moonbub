#!/usr/bin/env python3
"""Bounded same-stimulus accepted-output comparison of frozen/V113 inverse."""
import argparse,datetime,hashlib,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=ROOT/'experiments/python-gamebub-v113/inverse';SRC=ROOT/'fpga/experiments/cu66-v113-inverse';IMAGE='gamebub-cu66-v69-tools:20261105'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',action='store_true');a=ap.parse_args()
 if not a.run:print('BENCHMARK_PREPARED_NOT_RUN');return
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'benchmarks'/stamp;out.mkdir(parents=True)
 base=Path('/home/lori/gamebub-build/cu66-v69')/('v113-inverse-benchmark-'+stamp);base.mkdir();report=dict(schema='v113-inverse-throughput-comparison-v1',status='FAIL',backend='Verilator',commands=[],runs={},sources={})
 def run(cmd,name,cap):
  command=['docker','run','--rm','--init','--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={base},dst=/work','-w','/work',IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*cmd];report['commands'].append(command)
  with(out/name).open('w')as f:subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,timeout=cap+20,check=True)
 try:
  for label,inverse in [('frozen',ROOT/'fpga/experiments/cu66-v110-fault/cu66_inverse_stream_v91j.sv'),('candidate',SRC/'cu66_inverse_stream_v91j.sv')]:
   build=base/label;build.mkdir();paths=[inverse,SRC/'tb_throughput.cpp',ROOT/'fpga/experiments/cu66-v110-dequant/cu66_dequant.sv',ROOT/'fpga/experiments/cu66-v108-outtile/cu66_idct8x8.sv',ROOT/'fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh',ROOT/'experiments/python-gamebub-v91j/vectors/boundary.tsv',Path(__file__)]
   for p in paths:
    shutil.copyfile(p,build/p.name);report['sources'][str(p.relative_to(ROOT))]=sha(p);s=out/'sources'/p.relative_to(ROOT);s.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,s)
   m='/work/'+label;run(['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--public-flat-rw','--output-split','10000','--output-split-cfuncs','500','--language','1800-2017','-I'+m,'-CFLAGS','-std=c++17 -O1 -Wall -Wextra -Werror','--top-module','cu66_inverse_stream_v91j','--Mdir',m+'/obj',*[m+'/'+n for n in ('cu66_inverse_stream_v91j.sv','cu66_dequant.sv','cu66_idct8x8.sv','tb_throughput.cpp')]],label+'-compile.log',600)
   assert '%Warning-' not in(out/(label+'-compile.log')).read_text();run([m+'/obj/Vcu66_inverse_stream_v91j',m+'/boundary.tsv'],label+'-run.log',120);rows=[json.loads(l)for l in(out/(label+'-run.log')).read_text().splitlines()];assert rows[-1]['status']=='TEST_PASS';report['runs'][label]=rows[:-1]
  report['comparisons']=[dict(case=a['case'],profile=a['profile'],frozen_cycles=a['total_cycles'],candidate_cycles=b['total_cycles'],candidate_minus_frozen=b['total_cycles']-a['total_cycles']) for a,b in zip(report['runs']['frozen'],report['runs']['candidate'])];report['status']='PASS'
 finally:
  (out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');(AREA/'benchmark-selected.json').write_text(json.dumps(dict(path=str((out/'receipt.json').relative_to(ROOT)),sha256=sha(out/'receipt.json'),status=report['status']),indent=2)+'\n');print(report['status'],out,flush=True)
if __name__=='__main__':main()
