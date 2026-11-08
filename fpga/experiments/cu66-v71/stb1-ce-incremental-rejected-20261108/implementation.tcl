set_param general.maxThreads 4
set out [file normalize [lindex $argv 0]]
open_checkpoint C:/moon/builds/stb1-ce-v001/constrained.dcp
if {[get_property PART [current_design]] ne "xc7a100tcsg324-1"} {error "Wrong part"}
if {[get_property REF_NAME [get_cells system_core]] ne "cu71_system_final_v023"} {error "Wrong core"}
set lc [get_clocks lcd_forwarded]
set period [get_property PERIOD $lc];set wave [get_property WAVEFORM $lc]
set high [expr {[lindex $wave 1]-[lindex $wave 0]}];set low [expr {$period-$high}]
# Nominal waveform check, separate from native library pulse checks and
# physical panel-pin duty-cycle measurement. Controller min13ns +1ns reserve.
if {$period<28.0 || $high<14.0 || $low<14.0} {error "LCD nominal clock contract violated"}
set f [open [file join $out lcd-nominal-clock.tsv] w];puts $f "period_ns\t$period\nhigh_ns\t$high\nlow_ns\t$low\ncontroller_min_high_low_ns\t13\nengineering_reserve_ns\t1\nphysical_pin_pulse_measurement\tNOT_RUN";close $f

opt_design
report_clocks -file [file join $out clocks-before-reuse.rpt]
report_exceptions -coverage -file [file join $out exceptions-before-reuse.rpt]
# Standard incremental mode: never force reuse; tool may choose full flow.
read_checkpoint -incremental -directive RuntimeOptimized C:/moon/builds/stb1-v001/routed.dcp
report_incremental_reuse -file [file join $out reuse-after-read.rpt]
report_clocks -file [file join $out clocks-after-read.rpt]
report_exceptions -coverage -file [file join $out exceptions-after-read.rpt]
puts INCREMENTAL_REQUESTED_ACTUAL_MODE_MUST_BE_READ_FROM_TOOL_LOG
place_design -directive Explore
report_incremental_reuse -file [file join $out reuse-postplace.rpt]
phys_opt_design
write_checkpoint -force [file join $out placed.dcp]
report_timing_summary -delay_type min_max -file [file join $out placed-timing-summary.rpt]
report_timing -delay_type max -max_paths 40 -file [file join $out placed-setup-paths.rpt]
route_design -directive NoTimingRelaxation
phys_opt_design -directive AggressiveExplore
route_design -directive Explore -tns_cleanup
report_incremental_reuse -file [file join $out reuse-final.rpt]
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
report_clocks -file [file join $out clocks-final.rpt]
report_clock_interaction -file [file join $out clock-interaction.rpt]
report_bus_skew -file [file join $out bus-skew.rpt]
check_timing -verbose -file [file join $out check-timing.rpt]
report_timing -delay_type max -to [get_ports {lcd_hsync lcd_vsync lcd_data_en lcd_data_r[*] lcd_data_g[*] lcd_data_b[*]}] -max_paths 64 -file [file join $out lcd-output-setup.rpt]
report_timing -delay_type min -to [get_ports {lcd_hsync lcd_vsync lcd_data_en lcd_data_r[*] lcd_data_g[*] lcd_data_b[*]}] -max_paths 64 -file [file join $out lcd-output-hold.rpt]
set f [open [file join $out lcd-iob-registers.tsv] w]
foreach c [get_cells -quiet -hier -regexp {lcd_observer/(rgb_out_reg\[[0-9]+\]|hs_out_reg|vs_out_reg|de_out_reg)}] {
 puts $f "$c\t[get_property REF_NAME $c]\t[get_property LOC $c]\t[get_property BEL $c]"
}
close $f
report_property [get_cells dotclock] -file [file join $out lcd-clock-cell.rpt]
puts CE_INCREMENTAL_REPORTS_COMPLETE_NO_BIT_OR_HARDWARE
