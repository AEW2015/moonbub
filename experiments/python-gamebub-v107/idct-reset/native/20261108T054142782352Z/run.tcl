set build [file normalize [lindex $argv 0]]
proc input_starts {pin} {
 set names {}
 foreach obj [all_fanin -flat -startpoints_only -to $pin] {
  if {[get_property CLASS $obj] eq "port"} {lappend names $obj}
 }
 return [lsort -unique $names]
}
set_param general.maxThreads 2
foreach variant {original candidate} {
 set dst [file join $build results $variant]
 file mkdir $dst
 create_project -in_memory -part xc7a100tcsg324-1
 set_property include_dirs $build [current_fileset]
 read_verilog -sv [file join $build ${variant}.sv]
 synth_design -top cu66_idct8x8 -part xc7a100tcsg324-1 -mode out_of_context -flatten_hierarchy rebuilt -directive Default
 create_clock -name unit_clk -period 10 [get_ports clk]
 write_checkpoint -force [file join $dst synth.dcp]
 write_verilog -force -mode funcsim [file join $dst mapped.v]
 report_utilization -hierarchical -file [file join $dst utilization.rpt]
 report_timing_summary -delay_type min_max -report_unconstrained -file [file join $dst timing.rpt]
 report_control_sets -verbose -file [file join $dst control-sets.rpt]
 report_high_fanout_nets -max_nets 30 -timing -load_types -file [file join $dst fanout.rpt]
 set f [open [file join $dst payload.tsv] w]
 puts $f "cell\tref\treset_pin\treset_driver\treset_is_ground\tce_driver\tce_port_fanin\treset_port_fanin\tce_register_starts"
 set payload [get_cells -hierarchical -regexp {(^|.*/)(source_tile_reg\[[0-9]+\])}]
 if {[llength $payload] != 1280} {error "payload count expected 1280 got [llength $payload]"}
 foreach c [lsort $payload] {
  set ref [get_property REF_NAME $c]
  set reset [get_pins -quiet $c/R]
  if {[llength $reset]!=1} {error "expected R pin $c"}
  set net [get_nets -of_objects $reset]
  set drivers [get_pins -of_objects $net -filter {DIRECTION == OUT}]
  set resetground 0
  foreach d $drivers {if {[get_property REF_NAME [get_cells -of_objects $d]] eq "GND"} {set resetground 1}}
  set ce [get_pins $c/CE]
  set cedrivers [get_pins -of_objects [get_nets -of_objects $ce] -filter {DIRECTION == OUT}]
  set ceports [input_starts $ce]
  set resetports [input_starts $reset]
  set regstarts {}
  foreach p [all_fanin -flat -startpoints_only -to $ce] {if {[get_property CLASS $p] eq "pin"} {lappend regstarts $p}}
  puts $f [join [list $c $ref $reset $drivers $resetground $cedrivers $ceports $resetports [lsort -unique $regstarts]] \t]
 }
 close $f
 set f [open [file join $dst reset-loads.tsv] w]
 puts $f "port\tregister_reset_endpoints\tall_flat_endpoints"
 foreach port {rst abort_frame in_valid} {
  set ends [all_fanout -flat -endpoints_only -from [get_ports $port]]
  set resets [filter $ends {REF_PIN_NAME == R || REF_PIN_NAME == S || REF_PIN_NAME == CLR || REF_PIN_NAME == PRE}]
  puts $f "$port\t[llength $resets]\t[llength $ends]"
 }
 close $f
 puts "IDCT_COMPONENT_COMPLETE $variant"
 close_project
}
