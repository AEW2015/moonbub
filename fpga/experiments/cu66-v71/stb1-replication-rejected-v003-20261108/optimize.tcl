set_param general.maxThreads 4
set out [file normalize [lindex $argv 0]]
open_checkpoint C:/moon/builds/stb1-v001/placed.dcp
if {[get_property PART [current_design]] ne "xc7a100tcsg324-1"} {error "wrong part"}
if {[version -short] ne "2025.2"} {error "wrong Vivado"}
proc target_ce {} {
 set ce [get_pins -quiet -hier -filter {NAME == "control_plane/hud_ticket_reg[4]/CE"}]
 if {[llength $ce]!=1} {error "exact semantic CE endpoint missing"}
 set nets [get_nets -quiet -of_objects $ce]
 if {[llength $nets]!=1} {error "CE net ambiguous"}
 set pin [get_pins -quiet -leaf -of_objects $nets -filter {DIRECTION == OUT}]
 set cell [get_cells -quiet -of_objects $pin]
 if {[llength $pin]!=1 || [llength $cell]!=1 || [get_property REF_NAME $cell] ne "LUT4"} {error "target must have one actual LUT4 driver; no guessing"}
 set loads [get_pins -quiet -leaf -of_objects $nets -filter {DIRECTION == IN}]
 return [list $ce $nets $pin $cell [get_property REF_NAME $cell] [get_property INIT $cell] [llength $loads]]
}
if {[llength $argv]!=8} {error "root-reviewed exact CE target fields required"}
set actual [target_ce]
set expected [lrange $argv 1 7]
if {$actual ne $expected} {error "postplace target differs from reviewed query"}
set target [lindex $actual 1]
set before [dict create];foreach c [get_cells -hier] {dict set before $c 1}
puts POSTPLACE_TARGETED_REPLICATION_BEGIN
if {[catch {phys_opt_design -force_replication_on_nets $target -verbose} reason opts]} {
 set f [open [file join $out unsupported.txt] w];puts $f $reason;close $f
 return -options $opts $reason
}
set newcells {};set f [open [file join $out replication-new-cells.tsv] w]
foreach c [get_cells -hier] {if {![dict exists $before $c]} {lappend newcells $c;puts $f "$c\t[get_property REF_NAME $c]\t[get_property LOC $c]"}}
close $f
if {![llength $newcells]} {puts POSTPLACE_REPLICATION_NOOP;close_design;exit 2}
set f [open [file join $out replication-nets.tsv] w]
foreach c [concat [lindex $actual 3] $newcells] {
 foreach pin [get_pins -of_objects $c -filter {DIRECTION == OUT}] {
  foreach n [get_nets -of_objects $pin] {puts $f "$pin\t$n\t[llength [get_pins -leaf -of_objects $n -filter {DIRECTION == IN}]]"}
 }
}
close $f
write_checkpoint -force [file join $out replicated-placed.dcp]
route_design -directive NoTimingRelaxation
phys_opt_design -directive AggressiveExplore
route_design -directive Explore -tns_cleanup
write_checkpoint -force [file join $out routed.dcp]
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $out timing-summary.rpt]
report_timing -delay_type max -max_paths 50 -file [file join $out setup-paths.rpt]
report_timing -delay_type min -max_paths 50 -file [file join $out hold-paths.rpt]
report_utilization -hierarchical -file [file join $out utilization.rpt]
report_route_status -file [file join $out route-status.rpt]
foreach c [get_drc_checks] {if {[lsearch -exact [list_property $c] MAX_MESSAGES]>=0} {set_property MAX_MESSAGES 100000 $c}}
report_drc -no_waivers -file [file join $out drc.rpt]
report_cdc -details -file [file join $out cdc.rpt]
report_exceptions -coverage -file [file join $out exceptions.rpt]
report_clock_interaction -file [file join $out clock-interaction.rpt]
report_bus_skew -file [file join $out bus-skew.rpt]
check_timing -verbose -file [file join $out check-timing.rpt]
report_clocks -file [file join $out clocks-after.rpt]
report_timing -delay_type max -to [get_ports {lcd_hsync lcd_vsync lcd_data_en lcd_data_r[*] lcd_data_g[*] lcd_data_b[*]}] -max_paths 64 -file [file join $out lcd-output-setup.rpt]
report_timing -delay_type min -to [get_ports {lcd_hsync lcd_vsync lcd_data_en lcd_data_r[*] lcd_data_g[*] lcd_data_b[*]}] -max_paths 64 -file [file join $out lcd-output-hold.rpt]
report_property [get_cells dotclock] -file [file join $out lcd-clock-cell.rpt]
puts STB1_MARGIN_V003_POSTPLACE_REPORTS_COMPLETE_NO_BIT_OR_HARDWARE
close_design
