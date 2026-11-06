"""Implement a hash-frozen explicit board selection. Never emit a BIT or program."""
from pathlib import Path
import argparse, hashlib, json, os, re, shutil, subprocess, time

root = Path(__file__).resolve().parents[2]
p = argparse.ArgumentParser()
p.add_argument('--selection', required=True)
p.add_argument('--output', required=True)
args = p.parse_args()
selection = (root / args.selection).resolve()
selected = json.loads(selection.read_text())
assert selected['BUILD_ALLOWED'] is True and selected['BIT_ALLOWED'] is False
assert selected['PROGRAM_ALLOWED'] is False and selected['SIMULATION'] is False
assert selected['part'] == 'xc7a100tcsg324-1'
assert selected['top'] == 'moonshine_top_dy71'
assert selected['UID_USR_ACCESS'] == selected['CSR_magic'] == '0x44593731'
assert selected['ABI'] == '0x00010000' and selected['capabilities'] == '0x0f'
assert selected['clock_IO_SDRAM_budget_changes'] is False
sha = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
pins = {}
for category in ['sources_sha256', 'headers_sha256', 'constraints_sha256']:
    for name, expected in selected[category].items():
        path = (root / name).resolve()
        assert path.is_relative_to(root) and sha(path) == expected, (category, name)
        if name in pins:
            assert pins[name] == expected
        pins[name] = expected
for name, expected in selected['native_guard_references'].items():
    assert sha(root / name) == expected, ('guard', name)
assert set(selected['sources']) == set(selected['sources_sha256'])
assert selected['constraint_entry'] in selected['constraints_sha256']
constraint_dir = Path(selected['constraint_entry']).parent.as_posix()
for name in selected['XDC_order']:
    assert constraint_dir + '/' + name in selected['constraints_sha256']
assert not any(name.endswith(('_model.sv', '_sim.sv')) for name in pins)
out = (root / args.output).resolve()
assert out.is_relative_to(root)
out.mkdir(parents=True, exist_ok=False)
for name in pins:
    dest = out / 'inputs' / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(root / name, dest)
assert pins == {name: sha(out / 'inputs' / name) for name in pins}
shutil.copyfile(selection, out / 'selection.json')
shutil.copyfile(__file__, out / 'executed-builder.py')
(out / 'source-freeze.json').write_text(json.dumps(pins, indent=2) + '\n')
tcl = '''set_param general.maxThreads 4
set out [file normalize [lindex $argv 0]]
set root [file join $out inputs]
create_project -in_memory -part xc7a100tcsg324-1 dy71_board
'''
tcl += 'set_property include_dirs [list ' + ' '.join('[file join $root ' + d + ']' for d in selected['include_dirs']) + '] [current_fileset]\n'
for name in selected['sources']:
    tcl += 'read_verilog -sv [file join $root ' + name + ']\n'
for name in selected['XDC_order']:
    tcl += 'read_xdc [file join $root ' + constraint_dir + '/' + name + ']\n'
tcl += '''synth_design -top moonshine_top_dy71 -part xc7a100tcsg324-1
write_checkpoint -force [file join $out synthesized.dcp]
report_utilization -hierarchical -file [file join $out synthesized-utilization.rpt]
report_clocks -file [file join $out synthesized-clocks.rpt]
'''
tcl += 'source [file join $root ' + selected['constraint_entry'] + ']\n'
tcl += '''write_checkpoint -force [file join $out constrained.dcp]
report_exceptions -coverage -file [file join $out exceptions-postsynth.rpt]
report_cdc -details -file [file join $out cdc-postsynth.rpt]
check_timing -verbose -file [file join $out check-timing-postsynth.rpt]
opt_design
place_design
phys_opt_design
write_checkpoint -force [file join $out placed.dcp]
report_timing_summary -delay_type min_max -file [file join $out placed-timing-summary.rpt]
report_timing -delay_type max -max_paths 40 -file [file join $out placed-setup-paths.rpt]
route_design
phys_opt_design -directive AggressiveExplore
route_design -directive Explore -tns_cleanup
write_checkpoint -force [file join $out routed.dcp]
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $out timing-summary.rpt]
report_timing -delay_type max -max_paths 50 -file [file join $out setup-paths.rpt]
report_timing -delay_type min -max_paths 50 -file [file join $out hold-paths.rpt]
report_utilization -hierarchical -file [file join $out utilization.rpt]
report_route_status -file [file join $out route-status.rpt]
report_drc -file [file join $out drc.rpt]
report_cdc -details -file [file join $out cdc.rpt]
report_exceptions -coverage -file [file join $out exceptions.rpt]
report_clock_interaction -file [file join $out clock-interaction.rpt]
report_bus_skew -file [file join $out bus-skew.rpt]
check_timing -verbose -file [file join $out check-timing.rpt]
puts DY71_BOARD_REPORTS_COMPLETE_NO_BIT_OR_HARDWARE
'''
(out / 'executed.tcl').write_text(tcl, newline='\n')
(out / 'tmp').mkdir()
cmd = ['C:/Xilinx/2025.2/Vivado/bin/vivado.bat', '-mode', 'batch', '-source', str(out / 'executed.tcl'),
       '-log', str(out / 'vivado.log'), '-journal', str(out / 'vivado.jou'), '-tclargs', str(out)]
start = time.monotonic()
with (out / 'console.log').open('w') as log:
    proc = subprocess.run(cmd, cwd=out, stdout=log, stderr=subprocess.STDOUT,
                          env=dict(os.environ, TEMP=str(out / 'tmp'), TMP=str(out / 'tmp')))
assert pins == {name: sha(root / name) for name in pins}, 'Live selected inputs changed'
assert pins == {name: sha(out / 'inputs' / name) for name in pins}, 'Frozen copied inputs changed'
result = dict(command=cmd, returncode=proc.returncode, seconds=time.monotonic()-start,
              selection_sha256=sha(selection), hardware=False, BIT=False,
              completion_marker='DY71_BOARD_REPORTS_COMPLETE_NO_BIT_OR_HARDWARE' in (out / 'console.log').read_text())
required = ['synthesized.dcp', 'constrained.dcp', 'routed.dcp', 'timing-summary.rpt',
            'setup-paths.rpt', 'hold-paths.rpt', 'utilization.rpt', 'route-status.rpt',
            'drc.rpt', 'cdc.rpt', 'exceptions.rpt', 'clock-interaction.rpt',
            'bus-skew.rpt', 'check-timing.rpt']
result['required_reports_present'] = all((out / name).is_file() and (out / name).stat().st_size for name in required)
result['native_error_lines'] = re.findall(r'^ERROR:.*$', (out / 'console.log').read_text(), re.M)
result['status'] = ('REPORTS_COMPLETE_NOT_TIMING_QUALIFIED' if proc.returncode == 0
                    and result['completion_marker'] and result['required_reports_present']
                    and not result['native_error_lines']
                    else 'INCOMPLETE_NATIVE_IMPLEMENTATION')
(out / 'execution.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
raise SystemExit(0 if result['status'] == 'REPORTS_COMPLETE_NOT_TIMING_QUALIFIED' else (proc.returncode or 1))
