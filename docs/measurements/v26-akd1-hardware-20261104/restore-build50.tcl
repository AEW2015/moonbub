open_hw_manager
connect_hw_server -url 127.0.0.1:3122
set targets [get_hw_targets -quiet *210249AE796F*]
if {[llength $targets] != 1} {error "Expected intended serial-numbered cable"}
set target [lindex $targets 0]
current_hw_target $target
set_property PARAM.FREQUENCY 3000000 $target
open_hw_target $target
set devices [get_hw_devices -quiet]
if {[llength $devices] != 1 || ![string match xc7a100t* [lindex $devices 0]]} {
    error "Unexpected target device"
}
set device [lindex $devices 0]
set_property PROGRAM.FILE {C:/Users/lavat/codex/moonbub/fpga/candidates/v21-audio/build/moonshine-rev4.1.bit} $device
program_hw_devices $device
refresh_hw_device $device
set done [get_property REGISTER.IR.BIT5_DONE $device]
set usercode [string tolower [get_property REGISTER.USERCODE $device]]
set access [string tolower [get_property REGISTER.USR_ACCESS $device]]
puts "LAB_BUILD50_RECOVERY_DONE=$done USERCODE=$usercode USR_ACCESS=$access"
if {$done != 1 || $usercode ne "b0100004" || $access ne "4d424f50"} {
    error "Programmed family identity/DONE mismatch"
}
puts "LAB_BUILD50_RECOVERY_VOLATILE_PROGRAM_PASS=1"
close_hw_target $target
disconnect_hw_server
close_hw_manager
