set_param general.maxThreads 2
set out [file normalize [lindex $argv 0]]
create_project -in_memory -part xc7a100tcsg324-1 bus_split
set_property include_dirs $out [current_fileset]
foreach f [glob -directory $out *.sv] {read_verilog -sv $f}
synth_design -top dy71_staging_ooc -mode out_of_context -part xc7a100tcsg324-1 -flatten_hierarchy none
create_clock -period 5.0 -name spi [get_ports spi_clk]
create_clock -period 10.0 -name core [get_ports core_clk]
set core_inputs [get_ports -filter {DIRECTION == IN && NAME !~ spi* && NAME != core_clk}]
set spi_inputs [get_ports {spi_reset spi_write spi_read spi_address[*] spi_wdata[*]}]
set core_outputs [get_ports -filter {DIRECTION == OUT && NAME !~ spi* && NAME !~ overflow*}]
set spi_outputs [get_ports {spi_rdata[*] overflow overflow_gray[*]}]
foreach pair [list [list core $core_inputs] [list spi $spi_inputs]] {set_input_delay -clock [lindex $pair 0] -max 1.0 [lindex $pair 1];set_input_delay -clock [lindex $pair 0] -min 0.0 [lindex $pair 1]}
foreach pair [list [list core $core_outputs] [list spi $spi_outputs]] {set_output_delay -clock [lindex $pair 0] -max 1.0 [lindex $pair 1];set_output_delay -clock [lindex $pair 0] -min 0.0 [lindex $pair 1]}
# Exact existing token first-stage/Gray/bundled constraints only, no queue/response false paths.
set tokens [get_cells -hier -regexp {bridge/(read_sync|ack_sync)_reg\[0\]}]
if {[llength $tokens]!=2} {error "token object count differs"}
set_false_path -to [get_pins -of_objects $tokens -filter {REF_PIN_NAME == D}]
set rg1 [get_cells -hier -regexp {bridge/rg1_reg\[[0-9]+\]}]
set wg1 [get_cells -hier -regexp {bridge/wg1_reg\[[0-9]+\]}]
set_max_delay -datapath_only 10.0 -from [get_clocks core] -to $rg1
set_bus_skew 10.0 -from [all_registers -clock core] -to $rg1
set_max_delay -datapath_only 5.0 -from [get_clocks spi] -to $wg1
set_bus_skew 5.0 -from [all_registers -clock spi] -to $wg1
set read_address [get_cells -hier -regexp {bridge/read_address_reg.*}]
set latched_address [get_cells -hier -regexp {bridge/latched_address_reg.*}]
set response [get_cells -hier -regexp {bridge/response_reg.*}]
set capture [get_cells -hier -regexp {bridge/spi_rdata_reg.*}]
foreach spec [list [list $read_address $latched_address] [list $response $capture]] {if {[llength [lindex $spec 0]]==0||[llength [lindex $spec 1]]==0} {error "missing bundle registers"};set_max_delay -datapath_only 10.0 -from [lindex $spec 0] -to [lindex $spec 1]}
set queue [get_cells -hier -filter {NAME =~ bridge/* && REF_NAME =~ RAMB*}]
if {[llength $queue]!=1} {error "expected exact one queue RAMB36E1"}
set d [get_pins -of_objects $response -filter {REF_PIN_NAME == D}]
set direct [get_timing_paths -quiet -from $queue -to $d -max_paths 32]
set f [open [file join $out structural-cone.txt] w]
puts $f "QUEUE_BRAMS=[llength $queue] RESPONSE_REGISTERS=[llength $response] DIRECT_QUEUE_TO_RESPONSE_PATHS=[llength $direct]"
foreach c $queue {puts $f "QUEUE $c"}
foreach p $direct {puts $f "PATH [get_property STARTPOINT_PIN $p] -> [get_property ENDPOINT_PIN $p] SLACK=[get_property SLACK $p]"}
close $f
report_timing -from $queue -to $d -max_paths 32 -file [file join $out queue-to-response.rpt]
report_timing -to $d -max_paths 50 -file [file join $out response-paths.rpt]
report_utilization -hierarchical -file [file join $out utilization.rpt]
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $out timing.rpt]
report_timing -delay_type max -max_paths 40 -file [file join $out setup-paths.rpt]
report_exceptions -file [file join $out exceptions.rpt]

set held [get_cells -hier -regexp {control_plane/staging/held_count_reg.*}]
if {[llength $held]!=3} {error "expected3heldcountFF"}
set held_ce [get_pins -of_objects $held -filter {REF_PIN_NAME == CE}]
report_timing -to $held -max_paths 30 -file [file join $out staging-held-all.rpt]
if {[llength $held_ce]>0} {report_timing -to $held_ce -max_paths 30 -file [file join $out staging-held-enable.rpt]}
set packet_regs [get_cells -hier -regexp {control_plane/staging/(packet_bytes|written_bytes)_reg.*}]
report_timing -from $packet_regs -to $held -max_paths 30 -file [file join $out packet-to-held.rpt]
report_timing -through [get_cells -hier -filter {NAME =~ control_plane/staging/*}] -max_paths 50 -file [file join $out staging-cone.rpt]
report_timing -to [get_cells -hier -regexp {control_plane/staging/(remaining_bytes|upload_capacity|within_packet)_reg.*}] -max_paths 30 -file [file join $out credit-update.rpt]

write_checkpoint -force [file join $out synthesized.dcp]
puts BUS_SPLIT_OOC_UNPLACED_ONLY_NOT_BOARD_SIGNOFF
