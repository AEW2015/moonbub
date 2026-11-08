# V014 LCD requirement: ILI9806E section14.4.2 setup/hold5ns; additional1ns engineering skew reserve, not measured PCB flight.
# CU71 hierarchy-specific derivative; identical pin budgets and selected100MHz read profile.
# Independent review of timing.tcl. Source after opening the unconstrained
# synthesized checkpoint; never combine with the exploratory broad exceptions.
create_generated_clock -name sdram_forwarded -source [get_pins system_core/memory/controller/forward_clock/C] -divide_by 1 -invert [get_ports sdram_clk]
set outputs [get_ports {sdram_a[*] sdram_bs[*] sdram_dq[*] sdram_we_n sdram_ldqm sdram_udqm sdram_cas_n sdram_ras_n sdram_cke[*] sdram_cs_n[*]}]
# Same provisional device/PCB budgets as the first implementation. No clock
# frequency or external delay was relaxed to repair internal timing.
set_output_delay -clock sdram_forwarded -max 2.0 $outputs
set_output_delay -clock sdram_forwarded -min -1.3 $outputs
set_input_delay -clock sdram_forwarded -max 7.0 [get_ports {sdram_dq[*]}]
set_input_delay -clock sdram_forwarded -min 2.0 [get_ports {sdram_dq[*]}]
# The data/T ODDRs are SAME_EDGE with identical D1/D2: their falling-edge
# output value is the value already launched on the preceding rising edge.
# Guard that structural fact before excluding only the impossible falling
# transition through these 32 cells. Rising launches and all D1/D2 setup/hold
# checks remain timed with the original external budgets.
set sdr_oddrs [get_cells -quiet -hier -regexp {system_core/memory/controller/dq_io\[[0-9]+\][./](data_out|tri_out)}]
if {[llength $sdr_oddrs]!=32} {error "Expected 16 SDR data and 16 SDR T ODDRs"}
set sdr_q {}
foreach cell $sdr_oddrs {
    if {[get_property DDR_CLK_EDGE $cell] ne "SAME_EDGE"} {error "SDR exception requires SAME_EDGE: $cell"}
    set d1 [get_nets -of_objects [get_pins $cell/D1]]
    set d2 [get_nets -of_objects [get_pins $cell/D2]]
    if {[llength $d1]!=1 || $d1 ne $d2} {error "SDR exception requires identical D1/D2 nets: $cell"}
    lappend sdr_q [get_pins $cell/Q]
}
set sdr_command_clock [get_clocks -of_objects [get_pins memory_clock/O]]
if {[llength $sdr_command_clock]!=1} {error "Missing SDR command clock"}
set_false_path -fall_from $sdr_command_clock -through $sdr_q -to [get_ports {sdram_dq[*]}]
puts "MOONSHINE_SDR_IDENTICAL_ODDR_FALL_ONLY=32"
# Corrected ODDR D1=1/D2=0 forwards pclk without inversion.
# Panel firmware documents FALLING sampling; retain identical numeric budgets.
create_generated_clock -name lcd_forwarded -source [get_pins dotclock/C] -divide_by 1 [get_ports lcd_dotclk]
set_output_delay -clock lcd_forwarded -clock_fall -max 6.0 [get_ports {lcd_hsync lcd_vsync lcd_data_en lcd_data_r[*] lcd_data_g[*] lcd_data_b[*]}]
set_output_delay -clock lcd_forwarded -clock_fall -min -6.0 [get_ports {lcd_hsync lcd_vsync lcd_data_en lcd_data_r[*] lcd_data_g[*] lcd_data_b[*]}]

proc required_cells {description expression} {
    set cells [get_cells -quiet -hier -regexp $expression]
    if {[llength $cells]==0} {error "Missing CDC objects: $description ($expression)"}
    puts "MOONSHINE_CDC_OBJECTS $description [llength $cells]"
    return $cells
}
proc first_stage {description expression} {
    set cells [required_cells $description $expression]
    set_false_path -to [get_pins -of_objects $cells -filter {REF_PIN_NAME == D}]
}

# The receive architecture captures the PREVIOUS returned SDRAM beat: the
# 274.5-degree clock and controller read latency select launch5 -> capture17.625,
# rather than launch5 -> capture7.625. Model that latency on the 16 pin-to-input
# FF paths only. Deliberately do NOT add a hold multiplier: the associated
# strong hold check protects capture7.625 from the next/new returned beat.
set receive_clock [get_clocks -of_objects [get_pins read_clock/O]]
if {[llength $receive_clock]!=1} {error "Missing phased SDRAM receive clock"}
set receive_period [get_property PERIOD $receive_clock]
set receive_wave [get_property WAVEFORM $receive_clock]
set receive_rise [lindex $receive_wave 0]
set receive_phase [expr {$receive_rise-floor($receive_rise/$receive_period)*$receive_period}]
if {abs($receive_period-10.0)>0.001 || abs($receive_phase-7.625)>0.001} {
    error "Previous-beat constraint requires 100 MHz, 274.5-degree receive clock"
}
set receive_cells [required_cells sdram_previous_beat_capture {system_core/memory/controller/dq_capture_reg\[[0-9]+\]}]
if {[llength $receive_cells]!=16} {error "Expected exactly 16 SDRAM input capture FFs"}
set_multicycle_path 2 -setup -from [get_ports {sdram_dq[*]}] -to [get_pins -of_objects $receive_cells -filter {REF_PIN_NAME == D}]
puts "MOONSHINE_SDR_PREVIOUS_BEAT_SETUP2_STRONG_HOLD=16"


# Preserve only asynchronous first-stage captures, never recovery stages.
first_stage endpoint_raw {endpoint/(sck_sync_reg\[0\]|cs_sync_reg\[0\]|dq_meta_reg\[[0-3]\]|buttons_meta_reg\[[0-9]+\]|vblank_sync_reg\[0\])}
first_stage bridge_tokens {bridge/(read_sync|ack_sync)_reg\[0\]}
first_stage reference_pll_status {platform_(service|panel)_lock_sync_reg\[0\]}
first_stage configuration_quarantine {quarantine_sync_reg\[0\]}
# Existing QSPI propagation bounds are retained, NOT an external hold proof.
set_max_delay -datapath_only 10.0 -from [all_registers -clock_pins] -to [get_ports {mcu_spi_d[*] mcu_irq_n}]
set_max_delay -datapath_only 10.0 -from [get_ports mcu_spi_cs_n] -to [get_ports {mcu_spi_d[*]}]
# Gray buses use physical delay/skew bounds, not false paths. Otherwise a bit
# from a later count can overtake an earlier bit before the first-stage sample.
set rgray [required_cells fifo_read_gray {bridge/rgray_reg\[[0-9]+\]}]
set rg1 [required_cells fifo_read_gray_first {bridge/rg1_reg\[[0-9]+\]}]
set read_source_clock [get_clocks -of_objects [get_pins memory_clock/O]]
if {[llength $read_source_clock]!=1} {error "Missing/ambiguous FIFO read source clock"}
# Clock-scoped source with an exact first-stage destination also covers a
# Gray MSB merged into its binary pointer register by synthesis. It does not
# cut any other destination or the following synchronizer stage.
set_max_delay -datapath_only 10.0 -from $read_source_clock -to $rg1
set_bus_skew 10.0 -from [all_registers -clock $read_source_clock] -to $rg1
set wgray [required_cells fifo_write_gray {bridge/wgray_reg\[[0-9]+\]}]
set wg1 [required_cells fifo_write_gray_first {bridge/wg1_reg\[[0-9]+\]}]
set write_source_clock [get_clocks -of_objects [get_pins spi_clock/O]]
if {[llength $write_source_clock]!=1} {error "Missing/ambiguous FIFO write source clock"}
set_max_delay -datapath_only 5.0 -from $write_source_clock -to $wg1
set_bus_skew 5.0 -from [all_registers -clock $write_source_clock] -to $wg1
set transport_meta [required_cells transport_loss_gray_first {transport_gray_meta_reg\[[0-9]+\]}]
set_max_delay -datapath_only 5.0 -from $write_source_clock -to $transport_meta
set_bus_skew 5.0 -from [all_registers -clock $write_source_clock] -to $transport_meta
# Exact primitive C->D bundled payload bounds; original 10 ns protocol unchanged.
source [file join [file dirname [info script]] bundle-registers-exact.tcl]
set reset_cells [required_cells reset_chains {joint_(core|spi|pixel)_reset_reg.*}]
set_false_path -to [get_pins -of_objects $reset_cells -filter {REF_PIN_NAME == PRE || REF_PIN_NAME == CLR}]
puts "MOONSHINE_REVIEWED_CDC_CONSTRAINTS=1"


set joint_reset_cells [required_cells joint_reset_chains {joint_(core|spi|pixel)_reset_reg\[[0-3]\]}]
if {[llength $joint_reset_cells]!=12} {error "Expected three four-stage joint reset chains"}
foreach spec {{spi_clock 5.0} {memory_clock 10.0} {read_clock 10.0} {panel_clock 34.05764966740576}} {
 set obj [get_clocks -of_objects [get_pins [lindex $spec 0]/O]]
 if {[llength $obj]!=1 || abs([get_property PERIOD $obj]-[lindex $spec 1])>0.001} {error "DY71 clock mismatch: $spec"}
}
required_cells actual_compute {system_core/receiver/base/.*}
required_cells actual_packet_store {control_plane/staging/bytes_reg.*}
required_cells actual_sdram {system_core/memory/controller/.*}
required_cells actual_lcd {system_core/scanout/lcd/x_reg.*}
foreach pattern {{overlay/.*} {audio/.*} {margin/.*} {timing/.*}} {
 if {[llength [get_cells -quiet -hier -regexp $pattern]]!=0} {error "Unexpected unsupported DY71 block: $pattern"}
}
puts "DY71_CONSTRAINTS_REQUIRED_OBJECTS_ONLY_NOT_BOARD_SIGNOFF=1"
puts "DY71_QSPI_EXTERNAL_HOLD_NOT_PROVEN=1"

# Exact selected direct-display C-start constraints and topology audit.
set DIRECT_DISPLAY_ROOT "system_core/scanout"
source [file join [file dirname [info script]] direct_cdc_candidate.tcl]
source [file join [file dirname [info script]] lcd-first-stage-guards.tcl]
puts "DY71_INTERNAL_CDC_BOUNDS_REQUIRE_ROOT_OBJECT_REPORT_REVIEW=1"
