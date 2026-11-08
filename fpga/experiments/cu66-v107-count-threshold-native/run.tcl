if {[llength $argv]!=1} {error "expected build directory"}
set build [file normalize [lindex $argv 0]]
file mkdir [file join $build results]
set_param general.maxThreads 2
create_project -in_memory -part xc7a100tcsg324-1
set_property verilog_define SYNTHESIS [current_fileset]
read_verilog -sv [file join $build threshold_math_probe.sv]
read_xdc [file join $build unit.xdc]
synth_design -top threshold_math_probe -part xc7a100tcsg324-1 -mode out_of_context -flatten_hierarchy rebuilt -directive Default
write_checkpoint -force [file join $build results synth.dcp]
write_verilog -force -mode funcsim [file join $build results mapped.v]
report_utilization -file [file join $build results utilization.rpt]
report_utilization -hierarchical -file [file join $build results hierarchy.rpt]
report_control_sets -verbose -file [file join $build results control-sets.rpt]
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $build results timing.rpt]
check_timing -verbose -file [file join $build results check-timing.rpt]
report_high_fanout_nets -max_nets 30 -load_types -timing -file [file join $build results fanout.rpt]
report_methodology -file [file join $build results methodology.rpt]
report_drc -file [file join $build results drc.rpt]
report_clocks -file [file join $build results clocks.rpt]
write_xdc -force -exclude_physical [file join $build results effective.xdc]
set f [open [file join $build results settings.tsv] w]
puts $f "key\tvalue"
foreach {key value} [list tool [version -short] part [get_property PART [current_design]] top [get_property NAME [current_design]] threads [get_param general.maxThreads] mode out_of_context directive Default flatten_hierarchy rebuilt defines SYNTHESIS clock_period_ns [get_property PERIOD [get_clocks threshold_unit_clk]]] {puts $f "$key\t$value"}
close $f
proc pin_drivers {pin} {
 set drivers [get_pins -quiet -of_objects [get_nets -quiet -of_objects $pin] -filter {DIRECTION == OUT}]
 set refs {}
 foreach q $drivers {lappend refs [get_property REF_NAME [get_cells -of_objects $q]]}
 return [list $drivers [lsort -unique $refs]]
}
proc starts {pin} {
 lassign [pin_drivers $pin] drivers refs
 if {$refs eq "GND" || $refs eq "VCC"} {return [list {} {}]}
 set ports {};set sequential {}
 foreach p [all_fanin -flat -startpoints_only -to $pin] {
  if {[get_property CLASS $p] eq "port"} {lappend ports $p} else {lappend sequential $p}
 }
 return [list [lsort -unique $ports] [lsort -unique $sequential]]
}
set props {AREG BREG MREG PREG ACASCREG BCASCREG CREG DREG ADREG USE_MULT USE_SIMD A_INPUT B_INPUT}
set f [open [file join $build results dsp-registers.tsv] w]
puts $f "cell\tprimitive\t[join $props \t]"
set dsps [get_cells -hierarchical -filter {REF_NAME == DSP48E1}]
if {[llength $dsps]<1} {error "extracted nontrivial multiplication probe mapped no DSP48E1"}
foreach c [lsort $dsps] {
 set row [list $c [get_property REF_NAME $c]]
 foreach p $props {lappend row [get_property $p $c]}
 puts $f [join $row \t]
}
close $f
set f [open [file join $build results dsp-control-pins.tsv] w]
puts $f "cell\tpin\tdrivers\tdriver_types\tinput_ports\tsequential_starts"
foreach c [lsort $dsps] {
 foreach p [lsort [get_pins -of_objects $c -filter {DIRECTION == IN}]] {
  set leaf [get_property REF_PIN_NAME $p]
  if {![string match CE* $leaf] && ![string match RST* $leaf]} {continue}
  lassign [pin_drivers $p] d refs
  lassign [starts $p] ports regs
  puts $f [join [list $c $leaf $d $refs $ports $regs] \t]
 }
}
close $f
set f [open [file join $build results ff-control-pins.tsv] w]
puts $f "cell\tprimitive\trole\tpin\tdrivers\tdriver_types\tinput_ports\tsequential_starts"
set ffs [get_cells -hierarchical -filter {REF_NAME =~ FD*}]
if {[llength $ffs]<1} {error "no mapped fabric flops"}
foreach c [lsort $ffs] {
 set role [expr {[regexp {valid_pipe|threshold_live|live_reg} $c] ? "control" : "data"}]
 foreach p [lsort [get_pins -of_objects $c -filter {DIRECTION == IN}]] {
  set leaf [get_property REF_PIN_NAME $p]
  if {$leaf ni {CE R S CLR PRE}} {continue}
  lassign [pin_drivers $p] d refs
  lassign [starts $p] ports regs
  puts $f [join [list $c [get_property REF_NAME $c] $role $leaf $d $refs $ports $regs] \t]
 }
}
close $f
set f [open [file join $build results srls.tsv] w]
puts $f "cell\tprimitive\tCE_drivers\tCE_driver_types\tCE_ports"
foreach c [lsort [get_cells -hierarchical -filter {REF_NAME =~ SRL*}]] {
 set p [get_pins -quiet $c/CE];lassign [pin_drivers $p] d refs;lassign [starts $p] ports regs
 puts $f [join [list $c [get_property REF_NAME $c] $d $refs $ports] \t]
}
close $f
puts V107_THRESHOLD_EXTRACTED_NATIVE_MAPPING_COMPLETE
