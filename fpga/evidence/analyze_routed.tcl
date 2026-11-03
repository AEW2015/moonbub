set root [file normalize [file join [file dirname [info script]] ..]]
set_param general.maxThreads 4
open_checkpoint [file join $root attempts v2-routed moonshine_routed.dcp]
report_timing -from [get_ports {sdram_dq[*]}] -delay_type max -max_paths 16 -file [file join $root evidence v2_sdram_setup.rpt]
report_timing -from [get_ports {sdram_dq[*]}] -delay_type min -max_paths 16 -file [file join $root evidence v2_sdram_hold.rpt]
report_timing -to [get_ports {sdram_a[*] sdram_bs[*] sdram_dq[*] sdram_we_n sdram_ldqm sdram_udqm sdram_cas_n sdram_ras_n sdram_cke[*] sdram_cs_n[*]}] -delay_type max -max_paths 16 -file [file join $root evidence v2_sdram_output_setup.rpt]
