# OOC component implementation only. No board pins, I/O delays or BIT.
set root [file dirname [file normalize [info script]]]
set_param general.maxThreads 4
open_checkpoint [file join $root bank2-constrained synthesized.dcp]
opt_design
place_design
phys_opt_design
route_design
report_route_status -file route-status.rpt
report_timing_summary -delay_type min_max -max_paths 10 -report_unconstrained -file timing-routed.rpt
report_timing -delay_type max -max_paths 10 -path_type full -file setup-paths-routed.rpt
report_timing -delay_type min -max_paths 10 -path_type full -file hold-paths-routed.rpt
report_utilization -file utilization-routed.rpt
report_drc -file drc-routed.rpt
write_checkpoint -force routed-component.dcp
puts "OOC_ROUTED_COMPONENT_ONLY_NO_BOARD_IMAGE=1"
