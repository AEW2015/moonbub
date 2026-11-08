# Volatile configuration only; invoked only after Python's bound preconditions.
set bit {C:/moon/builds/entropy-finish-image-v029/moonbub-v029-entropyfinish-rev4.1.bit}
open_hw_manager
connect_hw_server -url 127.0.0.1:3122
set targets [get_hw_targets -quiet -filter {NAME =~ "*/Digilent/210249AE796F"}]
if {[llength $targets]!=1} {error "Expected exact HS2 adapter"}
set target [lindex $targets 0]
current_hw_target $target
set_property PARAM.FREQUENCY 3000000 $target
open_hw_target $target
set devices [get_hw_devices -quiet]
if {[llength $devices]!=1 || ![string match xc7a100t* [lindex $devices 0]]} {error "Unexpected FPGA chain"}
set device [lindex $devices 0]
set_property PROBES.FILE {} $device
set_property FULL_PROBES.FILE {} $device
set_property PROGRAM.FILE $bit $device
program_hw_devices $device
refresh_hw_device $device
set done [get_property REGISTER.IR.BIT5_DONE $device]
set uid [get_property REGISTER.USERCODE $device]
if {$done!=1 || [string tolower $uid] ne "44593741"} {error "V029 DONE/USERID mismatch"}
set f [open {C:/moon/dev/evidence/v56-v029-hardware-20261108-run01/program-receipt.tsv} w]
puts $f "utc\t[clock format [clock seconds] -gmt true -format {%Y-%m-%dT%H:%M:%SZ}]"
puts $f "target\t$target\ndevice\t$device\nDONE\t$done\nUSERCODE\t$uid\nvolatile_only\ttrue"
close $f
puts "V029_PROGRAMMED done=$done usercode=$uid target=$target"
close_hw_target $target
disconnect_hw_server
close_hw_manager
puts V029_PROGRAM_COMPLETE_NO_FLASH_OR_SD_WRITES
