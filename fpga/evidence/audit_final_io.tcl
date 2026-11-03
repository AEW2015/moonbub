set root [file normalize [file join [file dirname [info script]] ..]]
set out [file join $root build-final]
set_param general.maxThreads 4
open_checkpoint [file join $out moonshine_routed.dcp]
report_clocks -file [file join $out clocks.rpt]
report_timing -from [get_ports {sdram_dq[*]}] -delay_type max -max_paths 16 -file [file join $out sdram_input_setup.rpt]
report_timing -from [get_ports {sdram_dq[*]}] -delay_type min -max_paths 16 -file [file join $out sdram_input_hold.rpt]
set outputs [get_ports {sdram_a[*] sdram_bs[*] sdram_dq[*] sdram_we_n sdram_ldqm sdram_udqm sdram_cas_n sdram_ras_n sdram_cke[*] sdram_cs_n[*]}]
report_timing -to $outputs -delay_type max -max_paths 64 -file [file join $out sdram_output_setup.rpt]
report_timing -to $outputs -delay_type min -max_paths 64 -file [file join $out sdram_output_hold.rpt]
set setup [get_property SLACK [get_timing_paths -from [get_ports {sdram_dq[*]}] -delay_type max -max_paths 1]]
set hold [get_property SLACK [get_timing_paths -from [get_ports {sdram_dq[*]}] -delay_type min -max_paths 1]]
puts "MOONSHINE_FINAL_SDRAM_INPUT_SETUP=$setup HOLD=$hold"
if {$setup<=0 || $hold<=0} {error "Final SDRAM input gate failed"}
