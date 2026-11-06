source {C:/Users/lavat/codex/moonbub/evidence/hardware-combined-window-20261106T004742Z/combined_burst_lab-v4.tcl}
lab_open
set lab_capture_delay 3;set lab_capture_slot 1
lab_profile {220 166015625 425 4 4 225000 56250 20} 0
set edge [lab_run {C:/Users/lavat/codex/moonbub/evidence/hardware-combined-window-20261106T004742Z} edge-225-full 0 16777216 511 180000]
lab_profile {85 166015625 425 4 4 90000 22500 8} 0
set control [lab_run {C:/Users/lavat/codex/moonbub/evidence/hardware-combined-window-20261106T004742Z} control-90-full-repeat 0 16777216 511 180000]
lab_owner 1
lab_close
if {![lindex $control 0]} {error "Interior control failed"}
puts "COMBINED_EDGE_AND_INTERIOR_FULL_TESTS_RECORDED EDGE_PASS=[lindex $edge 0] CONTROL_PASS=[lindex $control 0]"
