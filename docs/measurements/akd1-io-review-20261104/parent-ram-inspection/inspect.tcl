set here [file dirname [file normalize [info script]]]
set dcp C:/Users/lavat/codex/moonbub/fpga/candidates/akd1-compute-lcd-prune-20261104/build/akd1-routed.dcp
open_checkpoint $dcp
set f [open [file join $here ram-cones.txt] w]
puts $f "READ_ONLY_ROUTED_CHECKPOINT=$dcp"
puts $f "VIVADO_VERSION=[version -short]"
set selected {}
foreach c [get_cells -hier -filter {REF_NAME == RAMB36E1}] {
 set name [get_property NAME $c]
 if {[string match diagnostic/byte_data_reg* $name] || $name eq "bridge/queue_reg" || $name eq "audio/samples_reg_0"} {
  lappend selected $c
 }
}
puts $f "SELECTED_RAM_COUNT=[llength $selected]"
foreach ram $selected {
 puts $f "\nRAM=[get_property NAME $ram]"
 set props [list_property $ram]
 foreach key {REF_NAME LOC DOA_REG DOB_REG INIT_A INIT_B SRVAL_A SRVAL_B READ_WIDTH_A READ_WIDTH_B WRITE_WIDTH_A WRITE_WIDTH_B WRITE_MODE_A WRITE_MODE_B RSTREG_PRIORITY_A RSTREG_PRIORITY_B EN_ECC_READ EN_ECC_WRITE} {
  if {[lsearch -exact $props $key]>=0} {puts $f "PROPERTY $key=[get_property $key $ram]"}
 }
 foreach pin_name {ENARDEN ENBWREN RSTRAMARSTRAM RSTRAMB RSTREGARSTREG RSTREGB WEA[0] WEBWE[0]} {
  set pin [get_pins -quiet "$ram/$pin_name"]
  if {[llength $pin]==0} {continue}
  puts $f "PIN=$pin"
  set net [get_nets -quiet -of_objects $pin]
  puts $f "NET=$net"
  puts $f "STARTPOINTS=[all_fanin -flat -startpoints_only -to $pin]"
  set cells [all_fanin -flat -only_cells -to $pin -levels 8]
  foreach c $cells {
   set ref [get_property REF_NAME $c]
   set cp [list_property $c]
   set init ""
   if {[lsearch -exact $cp INIT]>=0} {set init [get_property INIT $c]}
   puts $f "CELL $c REF=$ref INIT=$init"
   foreach ip [get_pins -quiet -of_objects $c -filter {DIRECTION == IN}] {
    set n [get_nets -quiet -of_objects $ip]
    set dp [get_pins -quiet -of_objects $n -filter {DIRECTION == OUT}]
    set port [get_ports -quiet -of_objects $n]
    puts $f "  INPUT $ip NET=$n DRIVER=$dp PORT=$port"
   }
  }
 }
}
close $f
set g [open [file join $here reset-clock-init.txt] w]
foreach c [get_cells -quiet -hier -regexp {rst(100|200|pixel)_reg\[[0-9]+\]|audio_reset_reg|audio/(crst|prst)_reg\[[0-9]+\]|diagnostic/(bytes_sent|state|byte_valid)_reg.*}] {
 puts $g "CELL=$c REF=[get_property REF_NAME $c]"
 set props [list_property $c]
 foreach p {INIT IS_CLR_INVERTED IS_PRE_INVERTED IS_R_INVERTED IS_S_INVERTED} {
  if {[lsearch -exact $props $p]>=0} {puts $g " $p=[get_property $p $c]"}
 }
 foreach ip [get_pins -quiet -of_objects $c -filter {DIRECTION == IN}] {
  puts $g " PIN=$ip NET=[get_nets -quiet -of_objects $ip]"
 }
}
close $g
puts "READ_ONLY_RAM_CONES_COMPLETE=1"
close_design
exit
