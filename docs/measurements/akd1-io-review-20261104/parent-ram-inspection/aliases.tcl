set here [file dirname [file normalize [info script]]]
open_checkpoint C:/Users/lavat/codex/moonbub/fpga/candidates/akd1-compute-lcd-prune-20261104/build/akd1-routed.dcp
set f [open [file join $here aliases.txt] w]
foreach name {{rst100_reg[3]/Q} diagnostic/byte_data_reg_0_0_i_1/I4 diagnostic/byte_data_reg_0_0_i_2/I0 bridge/fault_code[4]_i_1/I0 bridge/fault_code[4]_i_1/I1} {
 set pin [get_pins -quiet $name]
 puts $f "PIN=$name"
 puts $f "SEGMENTS=[get_nets -segments -quiet -of_objects $pin]"
}
foreach name {diagnostic/byte_data_reg_0_0/ENARDEN diagnostic/byte_data_reg_1_0/ENARDEN diagnostic/byte_data_reg_0_0/RSTRAMARSTRAM bridge/queue_reg/WEBWE[0]} {
 set pin [get_pins -quiet $name]
 set nets [get_nets -segments -quiet -of_objects $pin]
 puts $f "TARGET=$name"
 puts $f "DRIVER=[get_pins -leaf -quiet -of_objects $nets -filter {DIRECTION == OUT}]"
}
close $f
puts "READ_ONLY_ALIAS_QUERY_COMPLETE=1"
close_design
exit
