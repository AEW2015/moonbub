source {C:/Users/lavat/codex/moonbub/evidence/hardware-combined-window-20261106T004742Z/combined_burst_lab-v4.tcl}
lab_open
set row {85 166015625 425 4 4 90000 22500 8}
set f [open {C:/Users/lavat/codex/moonbub/evidence/hardware-combined-window-20261106T004742Z/tap-slot-summary.tsv} w]
puts $f "actual_phase_mdeg	tap	delay	slot	clock_epoch	run_id	pass	compared	errors	first_addr	expected_actual"
for {set tap 0} {$tap<32} {incr tap} {
 set lab_capture_delay 3;set lab_capture_slot 1
 set config [lab_profile $row $tap]
 foreach slot {0 1 2 3} {
  set lab_capture_slot $slot
  set result [lab_run {C:/Users/lavat/codex/moonbub/evidence/hardware-combined-window-20261106T004742Z} tap-${tap}-slot-${slot} 0 65536 511 10000]
  set pass [lindex $result 0];set snap [lindex $result 1]
  foreach i {0 1 2 3} {if {[lindex $snap [expr {32+$i}]]!=[lindex $config $i]} {error "Run settings tag mismatch"}}
  puts $f "90000	$tap	3	$slot	[lindex $config 3]	[lindex $snap 6]	$pass	[lindex $snap 3]	[lindex $snap 5]	[format %08X [lindex $snap 10]]	[format %08X [lindex $snap 11]]"
  flush $f
 }
}
close $f
set lab_capture_delay 3;set lab_capture_slot 1
set config [lab_profile $row 0]
lab_owner 1
set bases {0x60000000 0x600003f0 0x60000400 0x607ffff0 0x60800000 0x61000000 0x61800000 0x61fffff0}
set f [open {C:/Users/lavat/codex/moonbub/evidence/hardware-combined-window-20261106T004742Z/masked-cpu-bl8.tsv} w]
puts $f "stage	address	expected	actual"
set j 0
foreach base $bases {
 for {set lane 0} {$lane<4} {incr lane} {lab_write [expr {$base+4*$lane}] [expr {0xb16b0000^($j<<8)^$lane}]}
 incr j
}
set comparisons 0
foreach stage {seeded masked} {
 if {$stage eq "masked"} {
  set j 0;foreach base $bases {lab_write [expr {$base+4}] [expr {0x5a5a8000^$j}];incr j}
 }
 set j 0
 foreach base $bases {
  for {set lane 0} {$lane<4} {incr lane} {
   set expected [expr {$stage eq "masked"&&$lane==1?(0x5a5a8000^$j):(0xb16b0000^($j<<8)^$lane)}]
   set address [expr {$base+4*$lane}];set actual [lab_read $address]
   puts $f "$stage	[format %08X $address]	[format %08X $expected]	[format %08X $actual]"
   flush $f
   if {$actual!=$expected} {error "Masked CPU burst preservation failure"}
   incr comparisons
  }
  incr j
 }
}
close $f
puts "COMBINED_MASKED_BL8_PHYSICAL_PASS comparisons=$comparisons blocks=8 writes32=40 bank_row_last_address=1"
lab_close
puts "COMBINED_TAP_SLOT_SWEEP_COMPLETE_FIXED_WRITE_TIMING"
