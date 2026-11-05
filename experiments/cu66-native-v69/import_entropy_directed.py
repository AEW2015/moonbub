#!/usr/bin/env python3
"""Copy independently qualified entropy fixtures; no modification to RTL work."""
from pathlib import Path
import hashlib,json,zlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];SOURCE=ROOT/'fpga/experiments/cu66-v69/entropy/directed.tsv'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 rows=[];lines=[];pins={SOURCE.relative_to(ROOT).as_posix():sha(SOURCE.read_bytes())}
 for line in SOURCE.read_text().splitlines():
  name,path,expected,blocks,bw,dispatch,invalid=line.split('\t');path=Path(path)if Path(path).is_absolute()else SOURCE.parent/path;raw=path.read_bytes();rel='fixtures/'+sha(raw)+'.ab38';(HERE/rel).write_bytes(raw);pins[path.relative_to(ROOT).as_posix()]=sha(raw)
  tag='-'
  if expected!='-':
   expected=Path(expected)if Path(expected).is_absolute()else SOURCE.parent/expected;data=expected.read_bytes();pins[expected.relative_to(ROOT).as_posix()]=sha(data);tag=sha(zlib.decompress(data))
  rows.append(dict(name=name,packet=dict(path=rel,bytes=len(raw),sha256=sha(raw)),blocks=int(blocks),blocks_w=int(bw),dispatch=int(dispatch),reject=bool(int(invalid)),expected_coefficients_raw_sha256=tag));lines.append('\t'.join((name,rel,blocks,bw,dispatch,invalid,tag)))
 (HERE/'entropy-directed.tsv').write_text('\n'.join(lines)+'\n');(HERE/'entropy-directed.json').write_text(json.dumps(dict(schema='cu66-native-v69-entropy-directed',source_sha256=pins,cases=rows),indent=2)+'\n');print('directed entropy',len(rows))
if __name__=='__main__':main()
