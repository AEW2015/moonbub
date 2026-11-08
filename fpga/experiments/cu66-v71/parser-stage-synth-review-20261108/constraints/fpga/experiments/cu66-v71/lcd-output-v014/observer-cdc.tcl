# Only new observer crossings. Existing board/QSPI/SDRAM budgets are preserved.
proc obs_reg {name} {
 set cells [get_cells -quiet -hier -filter [format {NAME == "lcd_observer/%s"} $name]]
 if {[llength $cells]!=1} {error "Expected exact observer register $name"}
 return $cells
}
proc obs_pins {cells role} {
 set pins [get_pins -quiet -of_objects $cells -filter [format {REF_PIN_NAME == %s} $role]]
 if {[llength $pins]!=[llength $cells]} {error "Observer clock/data pin mismatch"}
 return $pins
}
foreach item {{requested_pattern_reg {pattern_sync_reg[0]} 34.057649667} {request_token_reg {request_sync_reg[0]} 34.057649667} {ack_token_reg {ack_sync_reg[0]} 10.0} {applied_pattern_reg {applied_sync_reg[0]} 10.0}} {
 lassign $item source dest delay
 set_max_delay -datapath_only $delay -from [obs_pins [obs_reg $source] C] -to [obs_pins [obs_reg $dest] D]
}
foreach name {pattern_sync request_sync ack_sync applied_sync} {
 foreach bit {0 1} {
  set c [obs_reg [format {%s_reg[%d]} $name $bit]]
  if {[get_property ASYNC_REG $c] ne "1"} {error "Observer synchronizer attribute missing"}
 }
}
set source [get_cells -quiet -hier -regexp {lcd_observer/snapshot_pixel_reg\[[0-9]+\]}]
set dest [get_cells -quiet -hier -regexp {lcd_observer/snapshot_mem_reg\[[0-9]+\]}]
# RGB565 expansion can merge duplicate RGB888 bits. Bind the actual synthesized
# endpoints, requiring at least all 4*16 independent color payload bits.
foreach group [list $source $dest] {if {[llength $group]<64||[llength $group]>96} {error "Unexpected held observer payload width"}}
set_max_delay -datapath_only 10.0 -from [obs_pins $source C] -to [obs_pins $dest D]
set_bus_skew 5.0 -from [obs_pins $source C] -to [obs_pins $dest D]
puts "LCD_OBSERVER_CDC_HELD_PAYLOAD source_FF=[llength $source] destination_FF=[llength $dest] max_ns=10 skew_ns=5"
