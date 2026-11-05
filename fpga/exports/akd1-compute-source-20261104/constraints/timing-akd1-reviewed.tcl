# AKD1 source-specific reviewed constraints. Not executed/qualified by source
# preparation. SDRAM is explicitly inactive: no clock/capture/command timing
# claim, no previous-beat multicycle and no inactive-pin false paths.
proc absent_cells {description expression} {
 set cells [get_cells -quiet -hier -regexp $expression]
 if {[llength $cells]!=0} {error "Unexpected inactive AKD1 objects: $description ($cells)"}
 puts "AKD1_ABSENT $description 0"
}
absent_cells external_memory {memory/.*}
absent_cells unused_receive_clock {read_clock}
absent_cells framebuffer_lcd {lcd/(bank[01].*|request_line[01].*|captured_line.*|request_sync[01].*|done_sync[01].*|frame_sync.*|underrun_(gray|sync[12]).*|mode_sync.*|valid_sync.*)}
puts "AKD1_SDRAM_INACTIVE_NOT_QUALIFIED=1"
# Corrected ODDR D1=1/D2=0 forwards pclk without inversion.
# Panel firmware documents FALLING sampling; retain identical numeric budgets.
create_generated_clock -name lcd_forwarded -source [get_pins dotclock/C] -divide_by 1 [get_ports lcd_dotclk]
set_output_delay -clock lcd_forwarded -clock_fall -max 2.0 [get_ports {lcd_hsync lcd_vsync lcd_data_en lcd_data_r[*] lcd_data_g[*] lcd_data_b[*]}]
set_output_delay -clock lcd_forwarded -clock_fall -min -1.0 [get_ports {lcd_hsync lcd_vsync lcd_data_en lcd_data_r[*] lcd_data_g[*] lcd_data_b[*]}]

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

# Positive live-design checks, not stale client-count preservation. This script
# must fail if a test stub or a missing platform consumer reaches board review.
required_cells real_compute {diagnostic/compute/.*}
required_cells live_lcd_counter {lcd/x_reg.*}
required_cells live_overlay_ram {overlay/overlay_bank.*mem.*}
required_cells live_audio_ram {audio/samples.*}
foreach spec {{spi_clock 5.0} {memory_clock 10.0} {panel_clock 34.05764966740576}} {
 set clock_name [lindex $spec 0]
 set clock [get_clocks -of_objects [get_pins $clock_name/O]]
 if {[llength $clock]!=1} {error "Missing/ambiguous AKD1 live clock: $clock_name"}
 if {abs([get_property PERIOD $clock]-[lindex $spec 1])>0.001} {error "AKD1 live clock changed: $clock_name"}
}

# Only bit zero of the serial synchronizer vectors is an asynchronous capture.
# Cutting bit one/two would suppress the timed metastability recovery stages.
first_stage endpoint_raw {endpoint/(sck_sync_reg\[0\]|cs_sync_reg\[0\]|dq_meta_reg\[[0-3]\]|buttons_meta_reg\[[0-9]+\]|vblank_sync_reg\[0\])}
first_stage bridge_tokens {bridge/(read_sync|ack_sync)_reg\[0\]}
# Native-only LCD flags are constants, not asynchronous framebuffer tokens.
# Their former first-stage exceptions are intentionally absent.
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

# Bundled payloads remain stable through a synchronized request/acknowledgment.
set read_address [required_cells read_address {bridge/read_address_reg.*}]
set latched_address [required_cells latched_address {bridge/latched_address_reg.*}]
set_max_delay -datapath_only 10.0 -from $read_address -to $latched_address
set response [required_cells response {bridge/response_reg.*}]
set spi_rdata [required_cells response_capture {bridge/spi_rdata_reg.*}]
set_max_delay -datapath_only 10.0 -from $response -to $spi_rdata

set reset_cells [required_cells reset_chains {rst(100|200|pixel)_reg.*}]
set_false_path -to [get_pins -of_objects $reset_cells -filter {REF_PIN_NAME == PRE || REF_PIN_NAME == CLR}]
puts "MOONSHINE_REVIEWED_CDC_CONSTRAINTS=1"

# Margin mailbox tokens: cut only first-stage D pins; preserve recovery stages.
first_stage margin_core_tokens {margin/(ack_sync|online_sync|armed_sync)_reg\[0\]}
first_stage margin_pixel_tokens {margin/(core_online_sync|request_sync)_reg\[0\]}
# Seven-bit value is held from request assertion until acknowledgement clears.
# Two request synchronizer stages precede pending capture; bound physical payload
# propagation instead of falsely synchronizing its bits or cutting the bus.
set margin_source [required_cells margin_requested_value {margin/transport_payload_reg\[[0-6]\]}]
set margin_capture [required_cells margin_pending_value {margin/pending_margin_reg\[[0-6]\]}]
if {[llength $margin_source]!=7 || [llength $margin_capture]!=7} {error "Expected seven held margin bits"}
set_max_delay -datapath_only 10.0 -from $margin_source -to $margin_capture
puts "MOONSHINE_MARGIN_HELD_VALUE_BOUNDED=7"

# Timing-profile mailbox uses the same four-phase token/reset handshake.
first_stage timing_core_tokens {timing/(ack_sync|online_sync|armed_sync)_reg\[0\]}
first_stage timing_pixel_tokens {timing/(core_online_sync|request_sync)_reg\[0\]}
set timing_source [required_cells timing_requested_value {timing/transport_payload_reg\[[0-9]+\]}]
set timing_capture [required_cells timing_pending_value {timing/pending_timing_reg\[[0-9]+\]}]
if {[llength $timing_source]!=62 || [llength $timing_capture]!=62} {error "Expected sixty-two held timing bits"}
set_max_delay -datapath_only 10.0 -from $timing_source -to $timing_capture
puts "MOONSHINE_TIMING_HELD_VALUE_BOUNDED=62"

# Audio has independent block-slot ownership. Each Gray token advances one
# slot; per-frame counters advance one sample, never a whole packet at once.
first_stage audio_core_tokens {audio/(ack_sync|playing_sync|rebuffer_sync)_reg\[0\]}
first_stage audio_pixel_tokens {audio/(online_sync|enable_sync)_reg\[0\]}
first_stage audio_reference_lock_tokens {audio_(service|panel)_lock_sync_reg\[0\]}
set audio_core_clock [get_clocks -of_objects [get_pins memory_clock/O]]
set audio_pixel_clock [get_clocks -of_objects [get_pins panel_clock/O]]
set audio_wg1 [required_cells audio_slot_write_first {audio/wg1_reg\[[0-9]+\]}]
set_max_delay -datapath_only 10.0 -from $audio_core_clock -to $audio_wg1
set_bus_skew 10.0 -from [all_registers -clock $audio_core_clock] -to $audio_wg1
foreach pair {{audio_slot_read_first {audio/rg1_reg\[[0-9]+\]}} {audio_played_first {audio/played_meta_reg\[[0-9]+\]}} {audio_underrun_first {audio/underrun_meta_reg\[[0-9]+\]}} {audio_consumed_first {audio/consumed_meta_reg\[[0-9]+\]}}} {
 set dest [required_cells [lindex $pair 0] [lindex $pair 1]]
 set_max_delay -datapath_only 34.0 -from $audio_pixel_clock -to $dest
 set_bus_skew 34.0 -from [all_registers -clock $audio_pixel_clock] -to $dest
}
set audio_reset [required_cells audio_private_reset {audio/(crst|prst)_reg\[[0-9]+\]}]
set_false_path -to [get_pins -of_objects $audio_reset -filter {REF_PIN_NAME == PRE || REF_PIN_NAME == CLR}]
# DAC DSP mode: data/WCLK change only at rising BCLK, sampled falling BCLK.
# Use the proven speaker tester's arrival envelope: every BCLK/WCLK/DIN path
# must arrive within one pclk period, not an unproved CE-phase multicycle.
# Functional DSP assertions establish data launches at BCLK rising, then four
# MCLKs to sampling. Bounding all three pad latencies to [0,1] MCLK guarantees
# at least3 MCLKs (~102ns) setup/hold before PCB skew, exceeding provisional8ns
# DAC requirements. Clock-enable logic is not a timing exception. Physical
# PCB/pin qualification and acoustics remain separate.
create_generated_clock -name audio_mclk -source [get_pins audio_mclock/C] -divide_by 1 [get_ports dac_mclk]
create_generated_clock -name audio_bclk -source [get_pins panel_clock/O] -divide_by 8 [get_ports dac_bclk]
set_output_delay -clock $audio_pixel_clock -max 0.0 [get_ports {dac_bclk dac_wclk dac_din}]
set_output_delay -clock $audio_pixel_clock -min 0.0 [get_ports {dac_bclk dac_wclk dac_din}]
puts "MOONSHINE_AUDIO_SLOT_GRAY_DSP608=1"
