if {[llength $argv] != 3} {error "Usage: run_hardware.tcl program|test bitfile expected_previous_userid"}
set mode [lindex $argv 0]
set bitfile [file normalize [lindex $argv 1]]
set expected_previous [lindex $argv 2]
proc check {condition message} {if {![uplevel 1 [list expr $condition]]} {error $message}}
proc ar {address} {global axis;set t [create_hw_axi_txn -quiet sd_rd $axis -type read -address [format %08X $address] -len 1];try {run_hw_axi -quiet $t;return [expr {[scan [get_property DATA $t] %x]&0xffffffff}]} finally {delete_hw_axi_txn $t}}
proc aw {address data} {global axis;set t [create_hw_axi_txn -quiet sd_wr $axis -type write -address [format %08X $address] -data [format %08X $data]];try {run_hw_axi -quiet $t} finally {delete_hw_axi_txn $t}}
proc command {code} {
 set sequence [expr {([ar 0x42000028]+1)&0xffffffff}]
 if {$sequence==0} {set sequence 1}
 aw 0x42000024 $code;aw 0x42000028 $sequence
 set deadline [expr {[clock milliseconds]+10000}]
 while {[clock milliseconds]<$deadline} {
  set accepted [ar 0x4200002c];set completed [ar 0x42000030]
  if {$accepted==$sequence&&$completed==$sequence} {
   set status [ar 0x42000038]
   if {$status!=0} {error "CPU command $code failed status=[format %08X $status]"}
   after 80;return
  }
  after 20
 }
 error "CPU command $code timed out"
}
proc entry_name {entry} {
 set text ""
 for {set word 0} {$word<3} {incr word} {
  set value [ar [expr {0x42000224+($entry*3+$word)*4}]]
  for {set byte 3} {$byte>=0} {incr byte -1} {set c [expr {($value>>($byte*8))&255}];if {$c!=0} {append text [format %c $c]}}
 }
 return $text
}
open_hw_manager
try {
 connect_hw_server -url localhost:3121
 set targets [get_hw_targets -quiet *210249AE796F]
 check {[llength $targets]==1} "Expected known GameBub cable 210249AE796F"
 open_hw_target [lindex $targets 0]
 set devices [get_hw_devices -filter {PART == "xc7a100t"}]
 check {[llength $devices]==1} "Expected one XC7A100T"
 set dev [lindex $devices 0]
 if {$mode eq "program"} {
  check {[file exists $bitfile]} "Bitfile not found"
  refresh_hw_device -update_hw_probes false $dev
  set previous [get_property REGISTER.USERCODE $dev]
  check {[string equal -nocase $previous $expected_previous]} "Current image changed: expected $expected_previous, found $previous"
  puts "SD_EXPLORER_PREIMAGE USERID=$previous recovery=power_cycle_ESP32_reload"
  set_property PROBES.FILE {} $dev;set_property FULL_PROBES.FILE {} $dev;set_property PROGRAM.FILE $bitfile $dev
  program_hw_devices $dev;refresh_hw_device -update_hw_probes false $dev
  check {[get_property REGISTER.CONFIG_STATUS.BIT13_DONE_INTERNAL_SIGNAL_STATUS $dev] eq "1"} "DONE is low"
  check {[get_property REGISTER.CONFIG_STATUS.BIT00_CRC_ERROR $dev] eq "0"} "FPGA CRC error"
  check {[string equal -nocase [get_property REGISTER.USERCODE $dev] 53444531]} "Wrong SD Explorer USERID"
  puts "SD_EXPLORER_PROGRAM_PASS USERID=53444531; now choose Attach to FPGA app on the ESP32"
 } elseif {$mode eq "test"} {
  refresh_hw_device -update_hw_probes false $dev
  check {[string equal -nocase [get_property REGISTER.USERCODE $dev] 53444531]} "Wrong SD Explorer image"
  set axes [get_hw_axis -of_objects $dev];check {[llength $axes]==1} "Expected one JTAG AXI"
  set axis [lindex $axes 0]
  check {[ar 0x42000000]==0x4c434401} "UI ABI mismatch"
  check {[ar 0x42000044]==0x53444432} "Always-on diagnostic ABI mismatch"
  set diagnostic_flags [ar 0x42000048]
  check {($diagnostic_flags&0x3d)==0x3d} "POR/host/UI/clock diagnostics are not healthy"
  set heartbeat50 [ar 0x4200004c];set heartbeat200 [ar 0x42000050];after 100
  check {[ar 0x4200004c]!=$heartbeat50} "50 MHz always-on heartbeat stopped"
  check {[ar 0x42000050]!=$heartbeat200} "200 MHz always-on heartbeat stopped"
  set heartbeat [ar 0x42000034];after 250;check {[ar 0x42000034]>$heartbeat} "MicroBlaze heartbeat stopped"
  command 6
  check {([ar 0x42000200]&(1<<27))!=0} "SD Explorer page is not active"
  set count [expr {[ar 0x4200027c]&255}];set root_count $count;set many -1
  for {set i 0} {$i<$count} {incr i} {set name [entry_name $i];puts "SD_ROOT_ENTRY index=$i name=$name";if {$name eq "MANY"} {set many $i}}
  check {$many>=0} "Fixture directory MANY was not returned by the ESP32"
  for {set i 0} {$i<$many} {incr i} {command 8}
  command 5
  set names [dict create]
  while {1} {
   set count [expr {[ar 0x4200027c]&255}]
   for {set i 0} {$i<$count} {incr i} {dict set names [entry_name $i] 1}
   if {([ar 0x42000200]&(1<<22))!=0} break
   command 2
  }
  check {[dict size $names]==257} "Expected 257 CPU-consumed MANY entries, got [dict size $names]"
  for {set i 0} {$i<257} {incr i} {set expected [string toupper [format "item-%03d.dat" $i]];check {[dict exists $names $expected]} "Missing $expected"}
  set read_name [entry_name 0];command 9;set read_hash [ar 0x4200003c];set read_bytes [ar 0x42000040]
  check {$read_bytes>0&&$read_hash!=2166136261} "CPU READ_CHUNK did not consume file data"
  puts "SD_EXPLORER_HARDWARE_PASS always_on_50=1 always_on_200=1 cpu_heartbeat=1 diagnostics=[format %08X $diagnostic_flags] mailbox root_entries=$root_count many_entries=[dict size $names] read_name=$read_name read_bytes=$read_bytes read_fnv=[format %08X $read_hash] physical_path=MicroBlaze-QSPI-ESP32-FAT32"
 } else {error "Mode must be program or test"}
} finally {
 catch {close_hw_target};catch {disconnect_hw_server};close_hw_manager
 puts "SD_EXPLORER_JTAG_RELEASED=1"
}
