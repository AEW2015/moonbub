source {C:/Users/lavat/codex/moonbub/evidence/hardware-combined-window-20261106T004742Z/combined_burst_lab-v4.tcl}
lab_open
set f [open {C:/Users/lavat/codex/moonbub/evidence/hardware-combined-window-20261106T004742Z/phase-slot-summary.tsv} w]
puts $f "requested_phase	actual_phase_mdeg	tap	delay	slot	clock_epoch	run_id	pass	compared	errors	first_addr	expected_actual"
set pf [open {C:/Users/lavat/codex/moonbub/evidence/hardware-combined-window-20261106T004742Z/clock-profiles.txt} r];set profiles [split [string trim [read $pf]] "\n"];close $pf
foreach row $profiles {
 set phase [lindex $row 0]
 set lab_capture_delay 3;set lab_capture_slot 1
 set config [lab_profile $row 0]
 foreach slot {0 1 2 3} {
  set lab_capture_slot $slot
  set result [lab_run {C:/Users/lavat/codex/moonbub/evidence/hardware-combined-window-20261106T004742Z} phase-${phase}-slot-${slot} 0 65536 511 10000]
  set pass [lindex $result 0];set snap [lindex $result 1]
  foreach i {0 1 2 3} {if {[lindex $snap [expr {32+$i}]]!=[lindex $config $i]} {error "Run settings tag mismatch"}}
  puts $f "$phase	[lindex $row 5]	0	3	$slot	[lindex $config 3]	[lindex $snap 6]	$pass	[lindex $snap 3]	[lindex $snap 5]	[format %08X [lindex $snap 10]]	[format %08X [lindex $snap 11]]"
  flush $f
 }
}
close $f
lab_owner 1
lab_close
puts "COMBINED_PHASE_SLOT_SWEEP_COMPLETE_FIXED_WRITE_TIMING"
