# Read-only edge audit of an immutable checkpoint. Not routed signoff.
set cp [file normalize [lindex $argv 0]]
set out [file normalize [lindex $argv 1]]
open_checkpoint $cp
report_clocks -file [file join $out clocks.rpt]
report_timing -delay_type max -max_paths 10 -file [file join $out setup.rpt]
report_timing -delay_type min -max_paths 10 -file [file join $out hold.rpt]
report_timing -delay_type max -from [get_ports {sdram_dq[*]}] -max_paths 16 -file [file join $out input-setup.rpt]
report_timing -delay_type min -from [get_ports {sdram_dq[*]}] -max_paths 16 -file [file join $out input-hold.rpt]
close_design
