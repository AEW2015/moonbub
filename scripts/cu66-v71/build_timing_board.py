"""Exact-source successor board implementation. Reports only, no BIT or hardware."""
from pathlib import Path
import argparse, hashlib, json, os, shutil, subprocess, time

root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--output', required=True)
parser.add_argument('--board', required=True)
parser.add_argument('--system', required=True, help='Explicit hardware-only source manifest')
args = parser.parse_args()
out = (root / args.output).resolve()
out.mkdir(parents=True, exist_ok=False)
board = (root / args.board).resolve()
system_path = (root / args.system).resolve()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: str(p.relative_to(root)).replace('\\', '/')
selected = json.loads(system_path.read_text())
assert selected['SIMULATION'] is False
assert selected['top'] == json.loads((board/'provenance.json').read_text())['system_module']
for name, expected in selected['sources_sha256'].items():
    assert sha(root/name) == expected, f'Selected RTL changed: {name}'
files = list(selected['sources'])
files += ['fpga/experiments/cu66-v71/system/'+name for name in
          ['cu71_local_control.sv', 'cu71_packet_staging.sv', 'cu71_packet_arbiter.sv']]
files += [rel(board/name) for name in
          ['moonshine_top_cu71.sv', 'moonshine_qspi_endpoint.sv', 'moonshine_bus_cdc.sv']]
include_dirs = selected['include_dirs']
for directory in include_dirs:
    files += [rel(path) for path in (root/directory).glob('*.svh')]
files += [rel(path) for path in (board/'constraints').iterdir() if path.is_file()]
files = list(dict.fromkeys(files))
assert not any(name.endswith(('_model.sv', '_sim.sv')) for name in files)
pins = {name:sha(root/name) for name in files}
for name in files:
    path = out/'inputs'/name
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(root/name, path)
assert pins == {name:sha(out/'inputs'/name) for name in pins}, 'Copied input hash mismatch'
shutil.copyfile(Path(__file__), out/'executed-builder.py')
(out/'source-freeze.json').write_text(json.dumps(pins, indent=2)+'\n')
(out/'selection.json').write_text(json.dumps(dict(
    top='moonshine_top_cu71', part='xc7a100tcsg324-1', system=selected['top'],
    system_manifest=rel(system_path), system_manifest_sha256=sha(system_path),
    files=files, include_dirs=include_dirs, board=rel(board), SIMULATION=False,
    scope='Local original key/P correctness fixture; not streaming rate qualified',
), indent=2)+'\n')
tcl = '''set_param general.maxThreads 4
set out [file normalize [lindex $argv 0]]
set root [file join $out inputs]
create_project -in_memory -part xc7a100tcsg324-1 cu71_timing_board
'''
tcl += 'set_property include_dirs [list '+' '.join('[file join $root '+d+']' for d in include_dirs)+'] [current_fileset]\n'
tcl += '\n'.join('read_verilog -sv [file join $root '+name+']' for name in files if name.endswith('.sv'))+'\n'
bc = rel(board/'constraints')
for name in ['lcd_pins_rev4.xdc', 'sdram_pins_rev4.xdc', 'buttons.xdc', 'platform.xdc']:
    tcl += 'read_xdc [file join $root '+bc+'/'+name+']\n'
tcl += '''synth_design -top moonshine_top_cu71 -part xc7a100tcsg324-1
write_checkpoint -force [file join $out synthesized.dcp]
report_utilization -hierarchical -file [file join $out synthesized-utilization.rpt]
report_clocks -file [file join $out synthesized-clocks.rpt]
'''
tcl += 'source [file join $root '+bc+'/timing-cu71-reviewed.tcl]\n'
tcl += '''write_checkpoint -force [file join $out constrained.dcp]
check_timing -verbose -file [file join $out check-timing-postsynth.rpt]
opt_design
place_design
phys_opt_design
route_design
phys_opt_design -directive AggressiveExplore
route_design -directive Explore -tns_cleanup
write_checkpoint -force [file join $out routed.dcp]
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $out timing-summary.rpt]
report_timing -delay_type max -max_paths 40 -file [file join $out setup-paths.rpt]
report_timing -delay_type min -max_paths 40 -file [file join $out hold-paths.rpt]
report_utilization -hierarchical -file [file join $out utilization.rpt]
report_route_status -file [file join $out route-status.rpt]
report_drc -file [file join $out drc.rpt]
report_cdc -details -file [file join $out cdc.rpt]
report_exceptions -coverage -file [file join $out exceptions.rpt]
report_clock_interaction -file [file join $out clock-interaction.rpt]
report_bus_skew -file [file join $out bus-skew.rpt]
check_timing -verbose -file [file join $out check-timing.rpt]
puts CU71_TIMING_BOARD_REPORTS_COMPLETE_NO_BIT_OR_HARDWARE
'''
(out/'executed.tcl').write_text(tcl, newline='\n')
(out/'tmp').mkdir()
cmd = ['C:/Xilinx/2025.2/Vivado/bin/vivado.bat', '-mode', 'batch', '-source', str(out/'executed.tcl'), '-log', str(out/'vivado.log'), '-journal', str(out/'vivado.jou'), '-tclargs', str(out)]
start = time.monotonic()
proc = subprocess.run(cmd, cwd=out, env=dict(os.environ, TEMP=str(out/'tmp'), TMP=str(out/'tmp')))
assert pins == {name:sha(root/name) for name in pins}, 'Live sources changed during implementation'
assert pins == {name:sha(out/'inputs'/name) for name in pins}, 'Copied inputs changed during implementation'
(out/'execution.json').write_text(json.dumps(dict(command=cmd, returncode=proc.returncode,
    seconds=time.monotonic()-start, hardware=False, BIT=False), indent=2)+'\n')
raise SystemExit(proc.returncode)
