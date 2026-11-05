#!/usr/bin/env python3
"""Extract generic synchronous RAM ports, not device primitive/fit results."""
from pathlib import Path
import hashlib,json,sys,zlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 assert len(sys.argv)==3,'audit_memory.py one-bank.json two-bank.json'
 cases=[]
 for banks,path in enumerate(sys.argv[1:],1):
  raw=Path(path).read_bytes();data=json.loads(zlib.decompress(raw)if path.endswith('.zlib')else raw);cell=data['modules']['cu66_tile_rows']['cells']['strip'];assert cell['type']=='$mem_v2'
  p={k:int(cell['parameters'][k],2)for k in('WIDTH','SIZE','RD_PORTS','WR_PORTS','RD_CLK_ENABLE','WR_CLK_ENABLE')}
  assert p==dict(WIDTH=64,SIZE=720*banks,RD_PORTS=1,WR_PORTS=1,RD_CLK_ENABLE=1,WR_CLK_ENABLE=1),p
  cases.append(dict(strip_banks=banks,logical_payload_bytes=5760*banks,parameters=p,netlist_sha256=sha(path)))
 files=[HERE/'cu66_tile_rows.sv',HERE/'audit_memory.py',HERE/'yosys-rows1.log',HERE/'yosys-rows2.log',*(Path(p).resolve()for p in sys.argv[1:])]
 result=dict(schema='cu66-rows-generic-memory-v69',cases=cases,source_sha256={p.relative_to(ROOT).as_posix():sha(p)for p in files},physical_BRAM_mapping_or_fit_proven=False)
 (HERE/'memory-evidence.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(configurations=2,one_sync_read_and_one_write_port=True,physical_mapping_proven=False)))
if __name__=='__main__':main()
