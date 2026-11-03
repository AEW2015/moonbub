#!/usr/bin/env python3
"""Generate an isolated missing-controller-accept fault and focused test."""
from pathlib import Path
import sys
control=Path(sys.argv[1]).read_text();tb=Path(sys.argv[2]).read_text()
old='accepted_frames<=accepted_frames+1;commit_accept<=1;'
assert control.count(old)==1
Path(sys.argv[3]).write_text(control.replace(old,'accepted_frames<=accepted_frames+1;commit_accept<=0;'))
old='  body(6,2,17,b0,g0,0,0,0,0,0);transaction(0,3,0);'
new='''  body(6,2,17,b0,g0,0,0,0,0,0);transaction(8,3,0);
  if(!dut.faulted || dut.active)$fatal(1,"missing acceptance failed to fault");
  body(7,0,17,0,0,1,3,32'h352441c2,0,0);transaction(8,0,0);
  $display("TEST_PASS_CONTROLLER_ACCEPT_FAULT no_false_success=1 fault_latched=1");$finish;'''
assert tb.count(old)==1
Path(sys.argv[4]).write_text(tb.replace(old,new))
