set_param general.maxThreads 2
open_checkpoint {C:/mb70/fpga/experiments/cu66-v71/direct-display/evidence/direct-pipe-ooc01/synthesized.dcp}
set f [open {C:/mb70/fpga/experiments/cu66-v71/direct-display/cdc/inventory01.txt} w]
foreach c [get_cells -hier -regexp {.*(request_sync[01]_reg|frame_sync_reg|done_sync[01]_reg|valid_sync_reg|pattern_sync_reg|underrun_sync[12]_reg|completed_bad[01]_reg|captured_line_reg|request_line[01]_reg|frame_toggle_reg|request[01]_reg|done[01]_reg|loaded[01]_reg|front_valid_reg).*}] {
 puts $f "$c REF=[get_property REF_NAME $c] ASYNC=[get_property ASYNC_REG $c] CLOCK=[get_clocks -of_objects [get_pins -of_objects $c -filter {REF_PIN_NAME == C}]]"
}
close $f
help set_max_delay
help set_bus_skew
report_cdc -details -file {C:/mb70/fpga/experiments/cu66-v71/direct-display/cdc/unconstrained-cdc01.rpt}
puts "DIRECT_CDC_INVENTORY_COMPLETE"
