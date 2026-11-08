#!/usr/bin/env python3
"""Prepare three matched unit-only IDCT synthesis screens, separate from native campaign."""
import argparse,datetime,hashlib,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];BUILD_ROOT=Path('/home/lori/gamebub-build/cu66-v69');AREA=ROOT/'experiments/python-gamebub-v106/idct-area'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',action='store_true');args=ap.parse_args()
    if args.run:
        focus=json.loads((AREA/'results.json').read_text());assert focus['status']=='PASS' and focus['candidate']['sha256']==sha(ROOT/'fpga/experiments/cu66-v106-idct-area/cu66_idct8x8.sv')
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');build=BUILD_ROOT/('v106-idct-unit-'+stamp);build.mkdir();mapped=Path('/build')/build.name
    variants={'original':'fpga/experiments/cu66-v69/inverse/cu66_idct8x8.sv','prefetch':'fpga/experiments/cu66-v106-idct/cu66_idct8x8.sv','shared':'fpga/experiments/cu66-v106-idct-area/cu66_idct8x8.sv'}
    hashes={};origins={}
    for name,source in variants.items():
        p=ROOT/source;dest=build/'snapshot'/name/p.name;dest.parent.mkdir(parents=True);shutil.copyfile(p,dest);key=str(dest.relative_to(build/'snapshot'));hashes[key]=sha(p);origins[key]={'path':source,'sha256':sha(p)}
    shutil.copyfile(ROOT/'fpga/experiments/cu66-v106-flow/component.xdc',build/'component.xdc')
    (build/'inputs.tcl').write_text('set part xc7a100tcsg324-1\nset variants {original prefetch shared}\n')
    (build/'report.tcl').write_text('''proc unit_reports {variant} {
    global build
    set out [file join $build results]
    report_clocks -file [file join $out ${variant}-clocks.rpt]
    check_timing -verbose -file [file join $out ${variant}-check-timing.rpt]
    report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose -max_paths 20 -file [file join $out ${variant}-timing-summary.rpt]
    report_timing -delay_type max -max_paths 50 -path_type full_clock_expanded -file [file join $out ${variant}-setup-paths.rpt]
    report_utilization -file [file join $out ${variant}-utilization.rpt]
    report_utilization -hierarchical -file [file join $out ${variant}-hierarchy.rpt]
    report_high_fanout_nets -timing -load_types -max_nets 50 -file [file join $out ${variant}-high-fanout.rpt]
    report_control_sets -verbose -file [file join $out ${variant}-control-sets.rpt]
    report_exceptions -file [file join $out ${variant}-exceptions.rpt]
    set f [open [file join $out ${variant}-dsp-registers.tsv] w]
    puts $f "instance\\tprimitive\\tAREG\\tBREG\\tMREG\\tPREG"
    foreach cell [lsort [get_cells -hierarchical -filter {REF_NAME == DSP48E1}]] {
        puts $f "$cell\\t[get_property REF_NAME $cell]\\t[get_property AREG $cell]\\t[get_property BREG $cell]\\t[get_property MREG $cell]\\t[get_property PREG $cell]"
    }
    close $f
}
''')
    (build/'run.tcl').write_text('''if {[llength $argv]!=1} {error "expected build directory"}
set build [file normalize [lindex $argv 0]]
source [file join $build inputs.tcl]
file mkdir [file join $build results]
set_param general.maxThreads 2
set f [open [file join $build results tool-part.txt] w]
puts $f "version=[version -short]"
set parts [get_parts -quiet $part]
puts $f "part=$part matches=[llength $parts]"
close $f
if {[llength $parts]!=1} {error "exact part unavailable"}
source [file join $build report.tcl]
foreach variant $variants {
    create_project -in_memory -part $part
    set_property target_language Verilog [current_project]
    set_property verilog_define SYNTHESIS [current_fileset]
    read_verilog -sv [file join $build snapshot $variant cu66_idct8x8.sv]
    read_xdc [file join $build component.xdc]
    synth_design -top cu66_idct8x8 -part $part -mode out_of_context -flatten_hierarchy rebuilt -directive Default
    write_checkpoint -force [file join $build results ${variant}-synth.dcp]
    unit_reports $variant
    close_project
    puts "V106_IDCT_UNIT_VARIANT_FINISHED=$variant"
}
puts "V106_SYNTH_ONLY_FINISHED; isolated IDCT units only; no placement/routing/board signoff"
''')
    inputs={'schema':'v106-idct-area-unit-inputs-v1','variants':variants,'source_sha256':hashes,'source_origins':origins,'top':'cu66_idct8x8','part':'xc7a100tcsg324-1','clock_period_ns':10.0,'max_threads':2,'synth_only':True,'area_attribution_only':True,'matched_settings':'All three variants synthesized sequentially in one owned Vivado2026.1 container; clock loaded before synthesis, OOC/rebuilt/Default identical. No placement/routing or complete-top signoff.','recipe_sha256':{n:sha(build/n) for n in ('run.tcl','report.tcl','component.xdc','inputs.tcl')},'runner_sha256':sha(ROOT/'scripts/cu66-v106/idct_area_native.py')}
    (build/'inputs.json').write_text(json.dumps(inputs,indent=2,sort_keys=True)+'\n');print('V106_IDCT_UNIT_PREPARED',build,flush=True)
    if args.run:subprocess.run([sys.executable,str(ROOT/'scripts/cu66-v106/idct_area_native.py'),'--build',str(build),'--license-file','/home/lori/acorn-nexys4-ddr/cache/vivado.lic','--timeout','900'],check=True)
if __name__=='__main__':main()
