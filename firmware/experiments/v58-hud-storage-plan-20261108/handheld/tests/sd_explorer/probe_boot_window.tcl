if {[llength $argv] != 1} { error "Expected SD Explorer bitfile" }
set bitfile [file normalize [lindex $argv 0]]
proc check {condition message} {if {![uplevel 1 [list expr $condition]]} {error $message}}
open_hw_manager
try {
  connect_hw_server -url localhost:3121
  set targets [get_hw_targets -quiet *210249AE796F]
  check {[llength $targets] == 1} "Expected known GameBub cable"
  open_hw_target [lindex $targets 0]
  set devices [get_hw_devices -filter {PART == "xc7a100t"}]
  check {[llength $devices] == 1} "Expected one XC7A100T"
  set dev [lindex $devices 0]
  refresh_hw_device -update_hw_probes false $dev
  check {[string equal -nocase [get_property REGISTER.USERCODE $dev] 53444531]} "Unexpected preimage"
  set_property PROBES.FILE {} $dev
  set_property FULL_PROBES.FILE {} $dev
  set_property PROGRAM.FILE $bitfile $dev
  program_hw_devices $dev
  refresh_hw_device -update_hw_probes false $dev
  check {[string equal -nocase [get_property REGISTER.USERCODE $dev] 53444531]} "Programming identity failed"
  set axes [get_hw_axis -of_objects $dev]
  check {[llength $axes] == 1} "Expected one JTAG AXI"
  set axis [lindex $axes 0]
  for {set sample 0} {$sample < 8} {incr sample} {
    set txn [create_hw_axi_txn -quiet boot_$sample $axis -type read -address 42000000 -len 1]
    set failed [catch {run_hw_axi -quiet $txn} message]
    set data [get_property DATA $txn]
    puts "SD_BOOT_WINDOW sample=$sample catch=$failed data=$data message={$message}"
    delete_hw_axi_txn $txn
    after 250
  }
} finally {
  catch {close_hw_target}
  catch {disconnect_hw_server}
  close_hw_manager
  puts "SD_BOOT_WINDOW_JTAG_RELEASED=1"
}
