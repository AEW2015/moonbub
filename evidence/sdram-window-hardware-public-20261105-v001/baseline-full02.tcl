source {C:/Users/lavat/codex/moonbub/evidence/hardware-combined-window-20261106T004742Z/combined_burst_lab-v2.tcl}
lab_open
set result [lab_run {C:/Users/lavat/codex/moonbub/evidence/hardware-combined-window-20261106T004742Z} baseline-full 0 16777216 511 180000]
lab_owner 1
lab_close
if {![lindex $result 0]} {error "Full reference baseline failed; retain snapshot"}
puts "COMBINED_FULL_32MIB_NINE_PATTERN_PASS"
