source {C:/Users/lavat/codex/moonbub/evidence/hardware-combined-window-20261106T004742Z/combined_burst_lab-v3.tcl}
lab_open
set f [open {C:/Users/lavat/codex/moonbub/evidence/hardware-combined-window-20261106T004742Z/phase-sweep-summary.tsv} w]
puts $f "requested_phase	actual_phase_mdeg	tap	clock_epoch	pass	compared	errors	first_addr	expected_actual	command_khz	read_khz"
set pf [open {C:/Users/lavat/codex/moonbub/evidence/hardware-combined-window-20261106T004742Z/clock-profiles.txt} r]
set profiles [split [string trim [read $pf]] "\n"]
close $pf
foreach row $profiles {
 set phase [lindex $row 0]
 set config [lab_profile $row 0]
 set result [lab_run {C:/Users/lavat/codex/moonbub/evidence/hardware-combined-window-20261106T004742Z} phase-$phase 0 65536 511 10000]
 set pass [lindex $result 0];set snap [lindex $result 1]
 foreach i {0 1 2 3} {if {[lindex $snap [expr {32+$i}]]!=[lindex $config $i]} {error "Run settings tag mismatch"}}
 puts $f "$phase	[lindex $row 5]	0	[lindex $config 3]	$pass	[lindex $snap 3]	[lindex $snap 5]	[format %08X [lindex $snap 10]]	[format %08X [lindex $snap 11]]	[lindex $config 4]	[lindex $config 5]"
 flush $f
}
close $f
lab_owner 1
lab_close
puts "COMBINED_READ_PHASE_SWEEP_COMPLETE_FIXED_WRITE_TIMING"
