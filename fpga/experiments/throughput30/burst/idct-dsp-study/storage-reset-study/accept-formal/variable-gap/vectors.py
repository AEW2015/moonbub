from itertools import product
from pathlib import Path
import sys
from reach import advance
out=Path(sys.argv[1])
with out.open('w') as f:
 for flags,wr,rd,ri,st,v,end in product(range(4),range(2),range(2),range(64),range(4),range(2),range(2)):
  idx=63 if end else 0
  ns=advance((idx,0,flags,wr,rd,ri,st),v,0,0)
  f.write(' '.join(format(x,'x') for x in (flags,wr,rd,ri,st,v,idx,*ns[2:]))+'\n')
