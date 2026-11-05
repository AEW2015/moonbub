"""Prepare a fresh isolated capture-alignment candidate; never program hardware."""
from pathlib import Path
import argparse,hashlib,json,shutil
root=Path(__file__).resolve().parents[1]
package=root/'fpga/exports/cpl1-timing-fsmcopy-source-20261105-v002'
parser=argparse.ArgumentParser();parser.add_argument('--output');args=parser.parse_args()
dest=Path(args.output).resolve() if args.output else root/'fpga/candidates/cp23-sdram-capture135-20261105-v002'
dest.mkdir(exist_ok=False)
shutil.copytree(package/'inputs',dest/'inputs')
for name in ['key.cp23.hex','quantizers.hex']:
    shutil.copyfile(package/name,dest/name)
changes={}
def patch(name,old,new):
    path=dest/'inputs'/name
    text=path.read_text()
    assert text.count(old)==1,(name,old)
    before=hashlib.sha256(path.read_bytes()).hexdigest()
    path.write_text(text.replace(old,new),newline='\n')
    changes[name]=dict(parent_sha256=before,candidate_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
patch('rtl/moonshine_top_cpl1.sv','.CLKOUT2_PHASE(279.0)','.CLKOUT2_PHASE(135.0)')
patch('core/parents/moonshine_sdram_burst.sv',
      'always @(negedge clk)dq_retime<=dq_capture;',
      'always @(posedge clk)dq_retime<=dq_capture;')
p=dest/'inputs/core/parents/moonshine_sdram_burst.sv'
s=p.read_text();start=s.index(' // The routed round-trip window');end=s.index(' (* IOB="TRUE" *)reg[15:0]dq_capture;',start)
s=s[:start]+''' // Candidate only: sample at 135 degrees (3.75 ns), then retime on
 // the next command posedge. Response logic consumes the previous retime
 // register value; READ_WAIT=5 is preserved. Native-pad unit sweeps qualify
 // modeled beat alignment only, not implementation or external timing.
'''+s[end:];p.write_text(s,newline='\n')
changes['core/parents/moonshine_sdram_burst.sv']['candidate_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
p=dest/'inputs/constraints/timing-cpl1-reviewed.tcl'
s=p.read_text();start=s.index('# The receive architecture captures');end=s.index('# Preserve only asynchronous first-stage captures',start)
old=s[start:end]
assert 'set_multicycle_path 2 -setup' in old
new='''# Capture-alignment candidate: 100 MHz, 135 degrees. The intended
# previous forwarded rising edge is already the default setup launch edge:
# launch -5 ns -> capture 3.75 ns. Use ordinary single-cycle setup/hold;
# do not carry over the old 279-degree multicycle exception.
set receive_clock [get_clocks -of_objects [get_pins read_clock/O]]
if {[llength $receive_clock]!=1} {error "Missing phased SDRAM receive clock"}
set receive_period [get_property PERIOD $receive_clock]
set receive_wave [get_property WAVEFORM $receive_clock]
set receive_rise [lindex $receive_wave 0]
set receive_phase [expr {$receive_rise-floor($receive_rise/$receive_period)*$receive_period}]
if {abs($receive_period-10.0)>0.001 || abs($receive_phase-3.75)>0.001} {
    error "Capture candidate requires 100 MHz, 135-degree receive clock"
}
set receive_cells [required_cells sdram_capture {diagnostic/core/memory/controller/dq_capture_reg\\[[0-9]+\\]}]
if {[llength $receive_cells]!=16} {error "Expected exactly 16 SDRAM capture FFs"}
puts "MOONSHINE_SDR_CAPTURE_SINGLE_CYCLE=16 PHASE_NS=3.75"

'''
before=hashlib.sha256(p.read_bytes()).hexdigest();p.write_text(s[:start]+new+s[end:],newline='\n')
changes['constraints/timing-cpl1-reviewed.tcl']=dict(parent_sha256=before,candidate_sha256=hashlib.sha256(p.read_bytes()).hexdigest())
manifest=dict(status='SIMULATION_CANDIDATE_ONLY_NO_BIT_NO_HARDWARE',
              parent_package=str(package.relative_to(root)),changes=changes,
              clocks='Original frequencies; read phase intentionally changed from 279 to 135 degrees',
              external_budgets='Unchanged provisional max7/min2 input and max2/min-1.3 output',
              remaining=['Exact full-board CRC under strict hold model','Routed internal and external timing','Physical readback and unchanged golden CRC'])
(dest/'candidate.json').write_text(json.dumps(manifest,indent=2)+'\n',newline='\n')
print('CAPTURE_CANDIDATE_PREPARED',dest)
