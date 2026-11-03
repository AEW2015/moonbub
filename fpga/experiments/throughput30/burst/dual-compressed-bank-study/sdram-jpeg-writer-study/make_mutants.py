#!/usr/bin/env python3
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text();out=Path(sys.argv[2])
changes=[
 ('padding','buffer<=0;buffer_full<=0;await_drain<=0;aborting<=0;failing<=0;offer_locked<=0;active<=1;begin_accept<=1;',
  "buffer<=128'hffffffffffffffffffffffffffffffff;buffer_full<=0;await_drain<=0;aborting<=0;failing<=0;offer_locked<=0;active<=1;begin_accept<=1;"),
 ('drain','else if(await_drain && write_drain_done)','else if(await_drain)'),
 ('hold','(offer_locked||(!abort&&!sink_fault&&!aborting&&!failing))',"(1'b0||(!abort&&!sink_fault&&!aborting&&!failing))"),
 ('address','BASE_WORDS+issued_bursts*8','BASE_WORDS+issued_bursts*4'),
 ('capacity','declared_length>CAP_BYTES',"1'b0"),
]
for name,old,new in changes:
 if s.count(old)!=1:raise SystemExit('mutation anchor mismatch '+name)
 (out/(name+'.sv')).write_text(s.replace(old,new))
