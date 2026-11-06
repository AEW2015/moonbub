# Independent review of timing.tcl. Source after opening the unconstrained
# synthesized checkpoint; never combine with the exploratory broad exceptions.
create_generated_clock -name sdram_forwarded -source [get_pins controller/forward_clock/C] -divide_by 1 -invert [get_ports sdram_clk]
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
set sdr_oddrs [get_cells -quiet -hier -regexp {controller/dq_io\[[0-9]+\][./](data_out|tri_out)}]
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
set_output_delay -clock lcd_forwarded -clock_fall -max 2.0 [get_ports {lcd_hsync lcd_vsync lcd_data_en lcd_data_r[*] lcd_data_g[*] lcd_data_b[*]}]
set_output_delay -clock lcd_forwarded -clock_fall -min -1.0 [get_ports {lcd_hsync lcd_vsync lcd_data_en lcd_data_r[*] lcd_data_g[*] lcd_data_b[*]}]


set captures [get_cells -hier -regexp {^controller/dq_capture_reg\[[0-9]+\]$}]
if {[llength $captures]!=16} {error "Expected 16 input capture FFs"}
set rc [get_clocks -of_objects [get_pins read_clock/O]]
if {[get_property PERIOD $rc]!=10.0 || abs([lindex [get_property WAVEFORM $rc] 0]-7.625)>0.001} {error "Wrong receive clock"}
set_multicycle_path 2 -setup -from [get_ports {sdram_dq[*]}] -to [get_pins -of_objects $captures -filter {REF_PIN_NAME == D}]
set ep [get_cells -hier -regexp {^endpoint/(sck_sync_reg\[0\]|cs_sync_reg\[0\]|dq_meta_reg\[[0-3]\]|buttons_meta_reg\[[0-9]+\]|vblank_sync_reg\[0\])$}]
if {[llength $ep]!=19} {error "Unexpected endpoint synchronizer prefix count"}
set_false_path -to [get_pins -of_objects $ep -filter {REF_PIN_NAME == D}]
set panel [get_cells -hier -regexp {^panel_(done|bad)_reg\[0\]$}]
if {[llength $panel]!=2} {error "Missing panel status synchronizers"}
set_false_path -to [get_pins -of_objects $panel -filter {REF_PIN_NAME == D}]
set resets [get_cells -hier -regexp {^rst(100|200|pixel)_reg.*}]
set_false_path -to [get_pins -of_objects $resets -filter {REF_PIN_NAME == PRE || REF_PIN_NAME == CLR}]
set_max_delay -datapath_only 10.0 -from [all_registers -clock_pins] -to [get_ports {mcu_spi_d[*] mcu_irq_n}]
set_max_delay -datapath_only 10.0 -from [get_ports mcu_spi_cs_n] -to [get_ports {mcu_spi_d[*]}]
