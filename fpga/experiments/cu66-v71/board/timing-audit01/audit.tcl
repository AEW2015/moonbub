set_param general.maxThreads 2
open_checkpoint C:/mb70/fpga/experiments/cu66-v71/board/implementation02/constrained.dcp
report_timing -delay_type max -max_paths 20 -file C:/mb70/fpga/experiments/cu66-v71/board/timing-audit01/setup.rpt
report_timing_summary -delay_type min_max -report_unconstrained -file C:/mb70/fpga/experiments/cu66-v71/board/timing-audit01/summary.rpt
puts CU71_READONLY_POSTSYNTH_TIMING_AUDIT_DONE
