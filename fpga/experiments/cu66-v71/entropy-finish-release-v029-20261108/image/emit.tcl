set_param general.maxThreads 2
open_checkpoint {C:/moon/builds/entropy-finish-v001/routed.dcp}
set out {C:/moon/builds/entropy-finish-image-v029}
set_property BITSTREAM.CONFIG.USERID 0x44593741 [current_design]
set_property BITSTREAM.CONFIG.USR_ACCESS 0x44593741 [current_design]
if {[get_property PART [current_design]] ne "xc7a100tcsg324-1"} {error "Wrong DY71 part"}
set core [get_cells -quiet system_core]
if {[llength $core] != 1 || [get_property REF_NAME $core] ne "cu71_system_final_v023"} {error "Wrong DY71 core"}
proc identity32 {value} {
 if {![regexp {^(?:32'[hH]|0[xX])([0-9a-fA-F]{1,8})$} $value unused digits]} {error "Invalid32-bit identity: $value"}
 scan $digits %x parsed
 return [expr {$parsed & 4294967295}]
}
foreach key {BITSTREAM.CONFIG.USERID BITSTREAM.CONFIG.USR_ACCESS} {
 set value [get_property $key [current_design]]
 if {[identity32 $value] != 0x44593741} {error "Wrong DY71 image identity at $key: $value"}
}
set f [open [file join $out identity.tsv] w]
foreach key {NAME PART BITSTREAM.CONFIG.USERID BITSTREAM.CONFIG.USR_ACCESS} {puts $f "$key	[get_property $key [current_design]]"}
puts $f "CORE_REFNAME	[get_property REF_NAME $core]"
close $f
set f [open [file join $out bitstream-properties.tsv] w]
foreach key [lsort [list_property [current_design]]] {if {[string match BITSTREAM.* $key]} {puts $f "$key	[get_property $key [current_design]]"}}
close $f
foreach type {max min} {
 set paths [get_timing_paths -delay_type $type -max_paths 1]
 if {[llength $paths] != 1} {error "Missing routed timing path"}
 set slack [get_property SLACK $paths]
 if {$type eq "max" && $slack < 0} {error "Negative routed setup slack"}
 if {$type eq "min" && $slack <= 0} {error "Nonpositive routed hold slack"}
}
foreach check [get_drc_checks] {if {[lsearch -exact [list_property $check] MAX_MESSAGES]>=0} {set_property MAX_MESSAGES 100000 $check}}
report_drc -no_waivers -file [file join $out drc-uncapped.rpt]
set f [open [file join $out native-drc.tsv] w]
set errors 0
foreach violation [get_drc_violations] {
 set severity [get_property SEVERITY $violation]
 puts $f "$violation	$severity"
 if {[string equal -nocase $severity Error]} {incr errors}
}
puts $f "ERROR_COUNT	$errors"
close $f
if {$errors != 0} {error "Native unwaived DRC errors"}
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $out timing-summary.rpt]
report_route_status -file [file join $out route-status.rpt]
report_cdc -details -file [file join $out cdc.rpt]
report_exceptions -coverage -file [file join $out exceptions.rpt]
report_clock_interaction -file [file join $out clock-interaction.rpt]
report_bus_skew -file [file join $out bus-skew.rpt]
check_timing -verbose -file [file join $out check-timing.rpt]
# Read-only native audit: no image write

set cells [get_cells -quiet -hier -regexp {lcd_observer/(rgb_out_reg\[[0-9]+\]|hs_out_reg|vs_out_reg|de_out_reg)}]
if {[llength $cells]!=27} {error "Wrong LCD output register count"}
set f [open [file join $out lcd-iob-registers.tsv] w]
foreach c $cells {
 set loc [get_property LOC $c];set bel [get_property BEL $c]
 puts $f "$c	$loc	$bel"
 if {![string match OLOGIC_* $loc] || ![string match *.OUTFF $bel]} {error "LCD output FF outside IOB"}
}
close $f
set f [open [file join $out held-status-paths.tsv] w]
foreach bank {0 1} {
 set src [get_pins [format {system_core/scanout/lcd/completed_bad%d_reg/C} $bank]]
 set dst [get_pins [format {system_core/scanout/lcd/loaded%d_reg/D} $bank]]
 set path [get_timing_paths -from $src -to $dst -delay_type max -max_paths 1]
 if {[llength $path]!=1 || [get_property SLACK $path]<=0} {error "Held status max-delay check failed"}
 puts $f "$src	$dst	[get_property REQUIREMENT $path]	[get_property SLACK $path]"
}
close $f
report_timing -delay_type max -from [get_pins -hier -regexp {lcd_observer/snapshot_pixel_reg\[[0-9]+\]/C}] -to [get_pins -hier -regexp {lcd_observer/snapshot_mem_reg\[[0-9]+\]/D}] -max_paths 128 -file [file join $out observer-held-data.rpt]
report_timing -delay_type max -to [get_ports {lcd_hsync lcd_vsync lcd_data_en lcd_data_r[*] lcd_data_g[*] lcd_data_b[*]}] -max_paths 64 -file [file join $out lcd-output-setup.rpt]
report_timing -delay_type min -to [get_ports {lcd_hsync lcd_vsync lcd_data_en lcd_data_r[*] lcd_data_g[*] lcd_data_b[*]}] -max_paths 64 -file [file join $out lcd-output-hold.rpt]
set reset [filter [get_cells -quiet -hier -regexp {.*joint_core_reset_reg\[[0-3]\]}] {REF_NAME =~ FD*}]
if {[llength $reset]!=4} {error "Wrong original protected reset topology"}
set f [open [file join $out reset-topology.tsv] w]
foreach c $reset {
 if {[get_property ASYNC_REG $c] ne "1"} {error "Original reset stage protection missing"}
 set clocks [get_clocks -of_objects [get_pins $c/C]]
 if {[llength $clocks]!=1 || abs([get_property PERIOD $clocks]-10.0)>0.001} {error "Reset clock mismatch"}
 puts $f "protected\t$c\t[get_property REF_NAME $c]\t[get_property ASYNC_REG $c]"
}
close $f

set c [get_cells -quiet core_reset_distribution]
if {[llength $c]!=1 || [get_property REF_NAME $c] ni {BUFG BUFGCTRL}} {error "Missing reset global buffer"}
report_property $c -file [file join $out reset-buffer.rpt]

set rst_source [get_pins {joint_core_reset_reg[3]/C}]
set rst_targets [get_pins -quiet -hier -filter {NAME =~ system_core/* && REF_PIN_NAME == R}]
if {[llength $rst_source]!=1 || [llength $rst_targets]<100} {error "Reset coverage endpoints missing"}
set rst_paths [get_timing_paths -from $rst_source -to $rst_targets -delay_type max -max_paths 16]
if {[llength $rst_paths]<1} {error "Buffered reset paths are not timed"}
foreach path $rst_paths {if {[get_property SLACK $path]<=0} {error "Buffered reset path violates setup"}}
report_timing -from $rst_source -to $rst_targets -delay_type max -max_paths 16 -file [file join $out reset-distribution-timing.rpt]

set burst [get_cells -quiet control_plane/burst]
if {[llength $burst]!=1} {error "Missing selected burst cell"}
write_verilog -cell $burst -mode funcsim [file join $out burst-funcsim.v]
write_checkpoint [file join $out routed-image.dcp]
write_bitstream [file join $out moonbub-v029-entropyfinish-rev4.1.bit]
close_design
puts V029_ENTROPY_FINISH_BIT_EMITTED_NO_HARDWARE
