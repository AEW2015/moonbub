# Hypothesis screening on a COPY opened in memory. No image, no programming.
# This is not implementation qualification for changed RTL/IO settings.
set cp [file normalize [lindex $argv 0]]
set out [file normalize [lindex $argv 1]]
set common [file normalize [lindex $argv 2]]
open_checkpoint $cp
proc first_stage {description expression} {
 set cells [get_cells -quiet -hier -regexp $expression]
 if {[llength $cells]==0} {error "Missing original first-stage objects $description"}
 set_false_path -to [get_pins -of_objects $cells -filter {REF_PIN_NAME == D}]
}
source $common
puts "IO_WINDOW_SCREEN_ORIGINAL SLEW=[get_property SLEW [get_ports sdram_clk]] DRIVE=[get_property DRIVE [get_ports sdram_clk]]"
set pll [get_cells service_pll]
if {[llength $pll]!=1} {error "Missing source-bound PLL"}
set_property CLKOUT2_PHASE 270.0 $pll
set_property DRIVE 16 [get_ports sdram_clk]
# Input-buffer power mode is a synthesis setting and cannot be changed by
# set_property on these checkpoint cells. Preserve it in this screen.
set captures [get_cells -hier -regexp {diagnostic/core/memory/controller/dq_capture_reg\[[0-9]+\]}]
if {[llength $captures]!=16} {error "Expected 16 capture registers"}
# At 7.50 ns, selecting the preceding 5 ns forwarded-clock beat needs the
# same setup-2/strong-hold relationship as the old 279-degree design.
set_multicycle_path 2 -setup -from [get_ports {sdram_dq[*]}] -to [get_pins -of_objects $captures -filter {REF_PIN_NAME == D}]
update_timing
puts "IO_WINDOW_SCREEN_READ_WAVE=[get_property WAVEFORM [get_clocks -of_objects [get_pins read_clock/O]]]"
report_clocks -file [file join $out clocks.rpt]
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $out timing-summary.rpt]
report_timing -delay_type max -from [get_ports {sdram_dq[*]}] -max_paths 16 -file [file join $out input-setup.rpt]
report_timing -delay_type min -from [get_ports {sdram_dq[*]}] -max_paths 16 -file [file join $out input-hold.rpt]
report_timing -delay_type max -max_paths 10 -file [file join $out setup.rpt]
report_timing -delay_type min -max_paths 10 -file [file join $out hold.rpt]
check_timing -verbose -file [file join $out check-timing.rpt]
puts "IO_WINDOW_HYPOTHESIS_SCREEN_ONLY_NO_IMAGE_NO_HARDWARE"
close_design
