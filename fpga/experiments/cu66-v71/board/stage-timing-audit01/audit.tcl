set_param general.maxThreads 2
open_checkpoint C:/mb70/fpga/experiments/cu66-v71/board/implementation02/routed.dcp
foreach {name expression} {
 inverse {system_core/receiver/base/inverse/.*}
 dequant {system_core/receiver/base/dequant/.*}
 tile_address {system_core/memory/tiles/.*}
 canonical {system_core/receiver/base/canonical/.*}
 parser {system_core/receiver/parser/.*}
 control {control_plane/.*}
} {
 set cells [get_cells -quiet -hier -regexp $expression]
 set pins [get_pins -quiet -of_objects $cells -filter {REF_PIN_NAME == D || REF_PIN_NAME == CE || REF_PIN_NAME == P || REF_PIN_NAME == CEA2 || REF_PIN_NAME == CEP}]
 if {[llength $pins]==0} {error "Missing $name endpoints"}
 report_timing -delay_type max -to $pins -max_paths 10 -file C:/mb70/fpga/experiments/cu66-v71/board/stage-timing-audit01/$name.rpt
}
puts CU71_STAGE_TIMING_AUDIT_DONE
