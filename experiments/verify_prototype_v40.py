#!/usr/bin/env python3
"""Portable v40 inventory, causal custom packets and native AU replay."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
def path(raw):
 p=Path(raw);assert not p.is_absolute() and '..' not in p.parts;p=(ROOT/p).resolve();assert p.is_relative_to(ROOT);return p
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(path(p).read_text())
def run(name,*args):
 p=subprocess.run([sys.executable,str(path(name)),*args],capture_output=True,text=True)
 if p.returncode:sys.stderr.write(p.stdout+p.stderr);p.check_returncode()
 return p.stdout.strip()
def main():
 d=load('docs/prototype-v40-provenance.json');assert d['schema']=='gamebub-v40-provenance'
 assert 'experiments/verify_source_archive_v40.py' in d['stored_helpers']
 for key in ('file_sha256','frozen_v39_sha256'):
  for p,h in d[key].items():assert sha(path(p))==h,(key,p)
 tests=pins=0
 for p,n in d['passing_test_logs'].items():
  t=path(p).read_text();m=re.search(r'^Ran (\d+) tests? in ',t,re.M);assert m and int(m[1])==n and t.rstrip().endswith('OK');tests+=n
 for p,key in d['run_artifacts'].items():
  for f,h in load(p)[key].items():assert sha(path(f))==h,('producer',p,f);pins+=1
 results={}
 for p in d['stored_helpers']:print('Replay '+p,flush=True);results[p]=run(p)
 comparison=run('experiments/compare_prototype_v40.py','--check')
 for p,h in d['file_sha256'].items():assert sha(path(p))==h,('postreplay',p)
 print(json.dumps(dict(snapshot_files=len(d['file_sha256']),frozen_v39_files=len(d['frozen_v39_sha256']),new_passing_tests=tests,source_bindings=pins,retained_verifiers=results,comparison=comparison,six_hour_run_complete=False,physical_30fps_or_FPGA_fit_proven=False,HEVC_AV1_superiority_proven=False),indent=2))
if __name__=='__main__':main()
