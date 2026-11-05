#!/usr/bin/env python3
"""Retain only an explicitly passing simulation ledger and small map archives."""
from pathlib import Path
import argparse,hashlib,json,shutil,zlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--work',required=True);args=ap.parse_args();work=Path(args.work)
    data=json.loads((work/'results.json').read_text());assert data['schema']=='gamebub-rtl-q14-v31'
    for rel,h in data['source_sha256'].items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==h,rel
    assert len(data['simulations'])==3 and data['mapped_directed_blocks']==654 and data['iverilog_directed_blocks']==654
    logs=['versions.log','lint.log','build-0.log','build-1.log','run-0-0.log','run-1-0.log','run-1-1.log',
          'iverilog-build.log','iverilog-run.log','yosys.log','yosys-stat.json','mapped-build.log','mapped-run.log','results.json']
    for name in ('run-0-0.log','run-1-0.log','run-1-1.log','iverilog-run.log','mapped-run.log'):
        text=(work/name).read_text();assert 'RESET_ABORT_PASS' in text and 'TEST_PASS' in text,name
        assert 'FATAL:' not in text and 'WATCHDOG_TIMEOUT' not in text,name
    dest=HERE/'results';dest.mkdir(exist_ok=True)
    for name in logs:shutil.copyfile(work/name,dest/name)
    artifacts={}
    for name in ('mapped.v','mapped.json'):
        raw=(work/name).read_bytes();packed=zlib.compress(raw,9);rel='results/'+name+'.zlib';(HERE/rel).write_bytes(packed)
        artifacts[name]=dict(path=rel,raw_bytes=len(raw),raw_sha256=hashlib.sha256(raw).hexdigest(),stored_sha256=hashlib.sha256(packed).hexdigest())
    (dest/'mapped-artifacts.json').write_text(json.dumps(artifacts,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(retained_logs=len(logs),mapped_archives=2,simulations=5,physical_30fps_proven=False)))
if __name__=='__main__':main()
