set_param general.maxThreads 4
open_checkpoint {C:/Users/lavat/codex/moonbub/fpga/experiments/cp23-key-registered-child-cancel-20261105/ooc01/synthesized.dcp}
set held [get_cells -hier -filter {NAME =~ "gather/held_request_address_reg*"}]
puts "PARENT_HELD_ADDRESS_REGISTERS=[llength $held]"
if {[llength $held] == 0} {error "No held-address registers found"}
report_timing -to $held -max_paths 5 -file {C:/Users/lavat/codex/moonbub/fpga/experiments/cp23-key-address-strength-20261105/address-paths01/parent-gather-address.rpt}
set hudr [get_cells -hier -filter {NAME =~ "*hud_ram*" && REF_NAME =~ "RAMB*"}]
set hudaddr [get_pins -of_objects $hudr -filter {REF_PIN_NAME =~ "ADDR*"}]
puts "PARENT_HUD_RAM_CELLS=[llength $hudr] ADDRESS_PINS=[llength $hudaddr]"
if {[llength $hudaddr] == 0} {error "No HUD RAM address pins found"}
report_timing -to $hudaddr -max_paths 5 -file {C:/Users/lavat/codex/moonbub/fpga/experiments/cp23-key-address-strength-20261105/address-paths01/parent-hud-address.rpt}
set dsps [get_cells -hier -filter {REF_NAME =~ "DSP*"}]
puts "PARENT_DSP_COUNT=[llength $dsps]"
foreach d $dsps {puts "PARENT_DSP $d"}
close_design
open_checkpoint {C:/Users/lavat/codex/moonbub/fpga/experiments/cp23-key-address-strength-20261105/ooc01/synthesized.dcp}
set held [get_cells -hier -filter {NAME =~ "gather/held_request_address_reg*"}]
puts "SUCCESSOR_HELD_ADDRESS_REGISTERS=[llength $held]"
if {[llength $held] == 0} {error "No held-address registers found"}
report_timing -to $held -max_paths 5 -file {C:/Users/lavat/codex/moonbub/fpga/experiments/cp23-key-address-strength-20261105/address-paths01/successor-gather-address.rpt}
set hudr [get_cells -hier -filter {NAME =~ "*hud_ram*" && REF_NAME =~ "RAMB*"}]
set hudaddr [get_pins -of_objects $hudr -filter {REF_PIN_NAME =~ "ADDR*"}]
puts "SUCCESSOR_HUD_RAM_CELLS=[llength $hudr] ADDRESS_PINS=[llength $hudaddr]"
if {[llength $hudaddr] == 0} {error "No HUD RAM address pins found"}
report_timing -to $hudaddr -max_paths 5 -file {C:/Users/lavat/codex/moonbub/fpga/experiments/cp23-key-address-strength-20261105/address-paths01/successor-hud-address.rpt}
set dsps [get_cells -hier -filter {REF_NAME =~ "DSP*"}]
puts "SUCCESSOR_DSP_COUNT=[llength $dsps]"
foreach d $dsps {puts "SUCCESSOR_DSP $d"}
close_design
