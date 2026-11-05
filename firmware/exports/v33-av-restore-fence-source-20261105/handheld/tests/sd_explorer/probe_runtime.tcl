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
  puts "SD_RUNTIME_ID USERID=[get_property REGISTER.USERCODE $dev] DONE=[get_property REGISTER.CONFIG_STATUS.BIT13_DONE_INTERNAL_SIGNAL_STATUS $dev] CRC=[get_property REGISTER.CONFIG_STATUS.BIT00_CRC_ERROR $dev]"
  set axes [get_hw_axis -of_objects $dev]
  check {[llength $axes] == 1} "Expected one JTAG AXI"
  set axis [lindex $axes 0]
  foreach address {40000000 42000000 42000034 42004000 44A00000} {
    set txn [create_hw_axi_txn -quiet probe_$address $axis -type read -address $address -len 1]
    set result [catch {run_hw_axi $txn} message options]
    set data [get_property DATA $txn]
    set status [get_property STATUS $txn]
    puts "SD_RUNTIME_READ address=$address catch=$result status=$status data=$data message={$message}"
    delete_hw_axi_txn $txn
  }
} finally {
  catch {close_hw_target}
  catch {disconnect_hw_server}
  close_hw_manager
  puts "SD_RUNTIME_JTAG_RELEASED=1"
}
