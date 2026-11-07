# Exact held-address / response bundle bounds: same 10 ns and protocol.
# Register C pins are legal launch points and retain C_Q; D pins are endpoints.
# No clock/FIFO/mailbox/dummy timing, RTL, LCD, SDRAM or reset-policy change.
proc dy71_bundle_exact_regs {base width} {
 set cells {}
 for {set bit 0} {$bit<$width} {incr bit} {
  set name [format {%s[%d]} $base $bit]
  set c [get_cells -quiet -hier -filter [format {NAME == "%s"} $name]]
  if {[llength $c]!=1 || ![regexp {^FD} [get_property REF_NAME $c]]} {error "DY71 bundle expected exact primitive FD register $name; got $c"}
  lappend cells $c
 }
 return $cells
}
proc dy71_bundle_pins {cells role expected_period} {
 set pins [get_pins -quiet -of_objects $cells -filter [format {REF_PIN_NAME == %s} $role]]
 if {[llength $pins]!=[llength $cells]} {error "DY71 bundle missing exact $role pins"}
 foreach c $cells {
  set cp [get_pins -quiet -of_objects $c -filter {REF_PIN_NAME == C}]
  set clock [get_clocks -quiet -of_objects $cp]
  if {[llength $cp]!=1 || [llength $clock]!=1 || abs([get_property PERIOD $clock]-$expected_period)>0.001} {error "DY71 bundle clock identity/period mismatch $c"}
 }
 return $pins
}
set read_address [dy71_bundle_exact_regs bridge/read_address_reg 12]
set latched_address [dy71_bundle_exact_regs bridge/latched_address_reg 12]
set response [dy71_bundle_exact_regs bridge/response_reg 32]
set spi_rdata [dy71_bundle_exact_regs bridge/spi_rdata_reg 32]
set dy71_bundle_address_C [dy71_bundle_pins $read_address C 5.0]
set dy71_bundle_address_D [dy71_bundle_pins $latched_address D 10.0]
set dy71_bundle_response_C [dy71_bundle_pins $response C 10.0]
set dy71_bundle_response_D [dy71_bundle_pins $spi_rdata D 5.0]
set_max_delay -datapath_only 10.0 -from $dy71_bundle_address_C -to $dy71_bundle_address_D
set_max_delay -datapath_only 10.0 -from $dy71_bundle_response_C -to $dy71_bundle_response_D
puts "DY71_EXACT_PRIMITIVE_HELD_ADDRESS_BUNDLE_C_D=12:12@10ns"
puts "DY71_EXACT_PRIMITIVE_RESPONSE_BUNDLE_C_D=32:32@10ns"
