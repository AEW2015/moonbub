"""Fresh candidate from sealed source; retain all original common constraints."""
from pathlib import Path
import hashlib,json,shutil
r=Path(__file__).resolve().parents[1]
p=r/'fpga/exports/cpl1-timing-fsmcopy-source-20261105-v002'
c=r/'fpga/candidates/cp23-sdram-capture274p5-20261105-v001'
c.mkdir(exist_ok=False);shutil.copytree(p/'inputs',c/'inputs')
for n in ['key.cp23.hex','quantizers.hex']:shutil.copyfile(p/n,c/n)
changes={}
def edit(n,old,new):
    f=c/'inputs'/n;s=f.read_text();assert s.count(old)==1,(n,old)
    parent=hashlib.sha256(f.read_bytes()).hexdigest();f.write_text(s.replace(old,new),newline='\n')
    changes[n]=dict(parent_sha256=parent,candidate_sha256=hashlib.sha256(f.read_bytes()).hexdigest())
edit('rtl/moonshine_top_cpl1.sv','.CLKOUT2_PHASE(279.0)','.CLKOUT2_PHASE(274.5)')
edit('core/parents/moonshine_sdram_burst.sv','always @(negedge clk)dq_retime<=dq_capture;',
     'always @(posedge clk)dq_retime<=dq_capture;')
n='core/parents/moonshine_sdram_burst.sv';f=c/'inputs'/n;s=f.read_text()
start=s.index(' // The routed round-trip window');end=s.index(' (* IOB="TRUE" *)reg[15:0]dq_capture;',start)
s=s[:start]+''' // Candidate: capture at 274.5 degrees (7.625 ns), then retime on
 // the next command posedge. READ_WAIT=5 and previous-beat indexing remain.
 // Physical input setup/strong hold and exact readback are separate gates.
'''+s[end:];f.write_text(s,newline='\n');changes[n]['candidate_sha256']=hashlib.sha256(f.read_bytes()).hexdigest()
n='constraints/timing-cpl1-reviewed.tcl';f=c/'inputs'/n;s=f.read_text();parent=hashlib.sha256(f.read_bytes()).hexdigest()
s=s.replace('279-degree','274.5-degree').replace('capture17.75','capture17.625').replace('capture7.75','capture7.625')
s=s.replace('$receive_phase-7.75','$receive_phase-7.625')
f.write_text(s,newline='\n');changes[n]=dict(parent_sha256=parent,candidate_sha256=hashlib.sha256(f.read_bytes()).hexdigest())
original=(p/'inputs'/n).read_text()
assert s[s.index('# Preserve only asynchronous first-stage captures'):]==original[original.index('# Preserve only asynchronous first-stage captures'):]
assert s.count('set_multicycle_path 2 -setup')==1 and 'set_multicycle_path 2 -hold' not in s
(c/'candidate.json').write_text(json.dumps(dict(status='UNIMPLEMENTED_NO_BIT_NO_HARDWARE',changes=changes,
    read_phase_degrees=274.5,read_phase_ns=7.625,retime='posedge',response_countdown=5,
    external_budgets='Unchanged max7/min2 input; max2/min-1.3 output',
    IO_settings='Unchanged FAST slew / DRIVE12; no input power mode modification',
    common_constraint_tail_exact=True,previous_beat_setup2_strong_hold_preserved=True),indent=2)+'\n')
print('CAPTURE274P5_CANDIDATE_PREPARED',c)
