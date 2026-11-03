#!/usr/bin/env python3
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text();out=Path(sys.argv[2])
for name,old,new in (
 ('stale_generation','p_generation!=active_generation',"1'b0"),
 ('no_replay','if(cache_valid && pending_seq==cache_seq)',"if(1'b0 && pending_seq==cache_seq)"),
):
 if s.count(old)!=1:raise SystemExit('mutation anchor mismatch '+name)
 (out/(name+'.sv')).write_text(s.replace(old,new))
