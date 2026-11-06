# Controlled laboratory driver for the already-qualified combined SERDES4 image.
# No programming or clock changes are performed when this library is sourced.
set lab_capture_delay 3
set lab_capture_slot 1
proc lab_open {} {
 global axis lab_device lab_target
 open_hw_manager
 connect_hw_server -url 127.0.0.1:3122
 set targets [get_hw_targets -quiet -filter {NAME =~ "*/Digilent/210249AE796F"}]
 if {[llength $targets]!=1} {error "Wrong intended cable"}
 set lab_target [lindex $targets 0]
 current_hw_target $lab_target
 set_property PARAM.FREQUENCY 3000000 $lab_target
 open_hw_target $lab_target
 set devices [get_hw_devices -quiet]
 if {[llength $devices]!=1||![string match xc7a100t* [lindex $devices 0]]} {error "Wrong device"}
 set lab_device [lindex $devices 0]
 set_property PROBES.FILE {C:/xup/bub/gamebub_combined_v2/release/gamebub-combined.ltx} $lab_device
 refresh_hw_device $lab_device
 if {[get_property REGISTER.IR.BIT5_DONE $lab_device]!=1||[string tolower [get_property REGISTER.USERCODE $lab_device]] ne "47544301"} {error "Wrong combined image"}
 set axes [get_hw_axis -of_objects $lab_device]
 if {[llength $axes]!=1} {error "Expected one AXI debug interface"}
 set axis [lindex $axes 0]
 if {[lab_read 0x62000000]!=0x53345331||[lab_read 0x41000000]!=0x53344331} {error "Wrong memory/clock ABI"}
}
proc lab_read {addr} {
 global axis
 set txn [create_hw_axi_txn -quiet lab_read $axis -type read -address [format %08X $addr] -len 1]
 try {run_hw_axi -quiet $txn;return [expr {[scan [get_property DATA $txn] %x]&0xffffffff}]} finally {delete_hw_axi_txn $txn}
}
proc lab_write {addr data} {
 global axis
 set txn [create_hw_axi_txn -quiet lab_write $axis -type write -address [format %08X $addr] -data [format %08X $data] -len 1]
 try {run_hw_axi -quiet $txn} finally {delete_hw_axi_txn $txn}
}
proc lab_wait {addr mask expected timeout_ms} {
 set deadline [expr {[clock milliseconds]+$timeout_ms}]
 while {[clock milliseconds]<$deadline} {
  set actual [lab_read $addr]
  if {($actual&$mask)==$expected} {return $actual}
  after 5
 }
 error "Timeout waiting for [format %08X $addr]"
}
proc lab_command {op} {
 lab_wait 0x62000008 3 0 2000
 set before [lab_read 0x6200000c]
 lab_write 0x62000004 $op
 lab_wait 0x62000008 3 0 2000
 if {[lab_read 0x62000004]!=0||[lab_read 0x6200000c]!=(($before+1)&0xffffffff)} {error "Memory command rejected or sequence changed: $op"}
}
proc lab_snapshot {} {
 lab_command 6
 set data {}
 for {set i 0} {$i<40} {incr i} {lappend data [lab_read [expr {0x62000100+4*$i}]]}
 if {[lindex $data 15]!=0x53543431} {error "Wrong snapshot schema"}
 return $data
}
proc lab_owner {owner} {
 global lab_capture_delay lab_capture_slot
 lab_write 0x6200004c [expr {($owner<<30)|($lab_capture_delay<<2)|$lab_capture_slot}]
 lab_command 3
 if {(([lab_read 0x62000008]>>2)&3)!=$owner} {error "Ownership change not acknowledged"}
}
proc lab_save {path data} {
 set f [open $path w]
 puts $f "# UTC=[clock format [clock seconds] -gmt true -format {%Y-%m-%dT%H:%M:%SZ}]"
 for {set i 0} {$i<[llength $data]} {incr i} {puts $f "$i\t[format %08X [lindex $data $i]]"}
 close $f
}
proc lab_run {out label base words patterns timeout_ms} {
 global lab_capture_delay lab_capture_slot
 lab_owner 2
 set before [lab_snapshot]
 set prior_id [lindex $before 6]
 lab_write 0x62000040 $base
 lab_write 0x62000044 $words
 lab_write 0x62000048 [expr {0x1d0f0000|$patterns}]
 lab_command 4
 set deadline [expr {[clock milliseconds]+$timeout_ms}]
 set fresh 0
 while {1} {
  set data [lab_snapshot]
  set id [lindex $data 6]
  if {$id!=(($prior_id+1)&0xffffffff)} {error "Test did not retain the expected fresh run ID"}
  set fresh 1
  set status [lindex $data 0]
  puts "BL8_PROGRESS label=$label run=$id status=[format %08X $status] work=[lindex $data 1]/[lindex $data 2] compared=[lindex $data 3] errors=[lindex $data 5]"
  if {$status&2} {break}
  if {$status&0x350} {lab_save [file join $out ${label}-fault.tsv] $data;error "Controller/align/config fault"}
  if {[clock milliseconds]>$deadline} {lab_save [file join $out ${label}-timeout.tsv] $data;error "Bounded test deadline expired"}
  after 200
 }
 lab_save [file join $out ${label}.tsv] $data
 if {[lindex $data 7]!=$base||[lindex $data 8]!=$words||[lindex $data 9]!=(0x1d0f0000|$patterns)} {error "Run region/pattern metadata changed"}
 if {([lindex $data 14]&63)!=(($lab_capture_delay<<2)|$lab_capture_slot)} {error "Run capture configuration changed"}
 set count 0
 for {set i 0} {$i<9} {incr i} {if {$patterns&(1<<$i)} {incr count}}
 set expected [expr {$words*$count}]
 set pass [expr {($status&0x37e)==6&&[lindex $data 1]==2*$expected&&[lindex $data 2]==2*$expected&&[lindex $data 3]==$expected&&[lindex $data 4]==$expected&&[lindex $data 5]==0&&(($status>>24)&15)==$count}]
 puts "BL8_RESULT label=$label run=$id PASS=$pass words=$words patterns=$count compared=[lindex $data 3] errors=[lindex $data 5] first=[format %08X [lindex $data 10]] expected_actual=[format %08X [lindex $data 11]]"
 return [list $pass $data]
}
proc lab_close {} {
 global lab_target
 close_hw_target $lab_target
 disconnect_hw_server
 close_hw_manager
}
proc lab_profile {row tap} {
 global lab_capture_delay lab_capture_slot
 # Same PARK/hold/apply/release/tap-load ordering as the archived firmware.
 lassign $row requested_phase actual_hz m8 divider output_div read_phase read_div_phase ticks
 lab_owner 0
 lab_wait 0x40000008 1 1 2000
 lab_write 0x40000000 1
 lab_wait 0x40000008 2 2 2000
 set settings [list $m8 $divider $output_div $read_phase $read_div_phase 166000]
 for {set i 0} {$i<6} {incr i} {lab_write [expr {0x41000020+4*$i}] [lindex $settings $i]}
 set before [lab_read 0x41000008]
 lab_write 0x41000004 1
 set deadline [expr {[clock milliseconds]+3000}]
 while {[lab_read 0x41000008]==$before} {
  if {[clock milliseconds]>$deadline} {error "Clock APPLY did not finish"}
  after 5
 }
 if {([lab_read 0x41000004]&0xff0f)!=6||[lab_read 0x41000040]!=$actual_hz} {error "Clock not healthy or actual rate changed"}
 for {set i 0} {$i<6} {incr i} {
  if {[lab_read [expr {0x41000060+4*$i}]]!=[lindex $settings $i]} {error "Clock latch readback mismatch"}
 }
 set epoch [lab_read 0x4100000c]
 lab_write 0x40000000 0
 lab_wait 0x40000008 2 0 2000
 set deadline [expr {[clock milliseconds]+2000}]
 while {1} {
  set snap [lab_snapshot]
  if {[lindex $snap 0]&128} {break}
  if {[clock milliseconds]>$deadline} {error "Memory did not initialize after APPLY"}
 }
 set taps 0
 for {set i 0} {$i<16} {incr i} {set taps [expr {$taps|($tap<<(5*$i))}]}
 lab_write 0x6200004c [expr {($lab_capture_delay<<2)|$lab_capture_slot}]
 for {set i 0} {$i<3} {incr i} {lab_write [expr {0x62000050+4*$i}] [expr {($taps>>(32*$i))&0xffffffff}]}
 lab_command 7
 set snap [lab_snapshot]
 for {set i 0} {$i<3} {incr i} {
  set actual [lindex $snap [expr {36+$i}]]
  if {$i==2} {set actual [expr {$actual&65535}]}
  if {$actual!=(($taps>>(32*$i))&0xffffffff)} {error "Tap readback mismatch"}
 }
 foreach offset {0x5c 0x60 0x64 0x68} value [list $actual_hz $requested_phase $tap $epoch] {lab_write [expr {0x62000000+$offset}] $value}
 set command_khz [lab_read 0x41000044]
 set read_khz [lab_read 0x41000048]
 if {abs($command_khz-$actual_hz/1000)>100||abs($read_khz-$actual_hz/1000)>100} {error "Independent rate meters disagree"}
 puts "BL8_PROFILE hz=$actual_hz requested_phase=$requested_phase actual_read_phase_mdeg=$read_phase tap=$tap epoch=$epoch cmd_khz=$command_khz read_khz=$read_khz"
 return [list $actual_hz $requested_phase $tap $epoch $command_khz $read_khz $read_phase $read_div_phase]
}
