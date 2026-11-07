open_hw_manager
connect_hw_server -url localhost:3121
set target [lindex [get_hw_targets -quiet *210249AE796F] 0]
open_hw_target $target
set dev [lindex [get_hw_devices -filter {PART == "xc7a100t"}] 0]
refresh_hw_device -update_hw_probes false $dev
puts "SD_DIAG_USERID=[get_property REGISTER.USERCODE $dev] axes=[get_hw_axis -of_objects $dev]"
set axis [lindex [get_hw_axis -of_objects $dev] 0]
foreach address {
  42000000 42000034 42000038 42000044 42000048 4200004C 42000050 42000200
  42004000 42004004 4200400C 42004010 42004014 42004018 4200401C
  42004020 42004024 42004028 4200402C 42004030
  47000000 47000008 44A00000
} {
 set txn [create_hw_axi_txn sd_diag_$address $axis -type read -address $address -len 1]
 set rc [catch {run_hw_axi $txn} message options]
 set status "unsupported"
 if {[lsearch -exact [list_property $txn] STATUS] >= 0} {set status [get_property STATUS $txn]}
 puts "SD_DIAG_AXI address=$address rc=$rc message={$message} DATA={[get_property DATA $txn]} STATUS={$status}"
 if {$rc} {puts "SD_DIAG_ERROR_OPTIONS=$options"}
 delete_hw_axi_txn $txn
}
close_hw_target
disconnect_hw_server
close_hw_manager
