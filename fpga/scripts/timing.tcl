# Constraints applied after synthesis so generated PLL/MMCM clocks exist.
create_generated_clock -name sdram_forwarded -source [get_pins memory/controller/forward_clock/C] -divide_by 1 -invert [get_ports sdram_clk]
set outputs [get_ports {sdram_a[*] sdram_bs[*] sdram_dq[*] sdram_we_n sdram_ldqm sdram_udqm sdram_cas_n sdram_ras_n sdram_cke[*] sdram_cs_n[*]}]
# Inherited conservative part+provisional PCB budgets from existing SDRAM app.
# These are explicit assumptions, not measured board flight times.
set_output_delay -clock sdram_forwarded -max 2.0 $outputs
set_output_delay -clock sdram_forwarded -min -1.3 $outputs
set_input_delay -clock sdram_forwarded -max 7.0 [get_ports {sdram_dq[*]}]
set_input_delay -clock sdram_forwarded -min 2.0 [get_ports {sdram_dq[*]}]
create_generated_clock -name lcd_forwarded -source [get_pins dotclock/C] -divide_by 1 -invert [get_ports lcd_dotclk]
# Same RGB/sync output budget as native baseline, allow2ns panel setup/hold.
set_output_delay -clock lcd_forwarded -max 2.0 [get_ports {lcd_hsync lcd_vsync lcd_data_en lcd_data_r[*] lcd_data_g[*] lcd_data_b[*]}]
set_output_delay -clock lcd_forwarded -min -1.0 [get_ports {lcd_hsync lcd_vsync lcd_data_en lcd_data_r[*] lcd_data_g[*] lcd_data_b[*]}]
# Raw SPI/buttons enter only first-stage samplers; following parser remains timed.
set endpoint_meta [get_cells -hier -regexp {endpoint/(sck_sync_reg\[0\]|cs_sync_reg\[0\]|dq_meta_reg\[[0-3]\]|buttons_meta_reg\[[0-9]+\]|vblank_sync_reg\[0\])}]
set_false_path -to [get_pins -of_objects $endpoint_meta -filter {REF_PIN_NAME == D}]
set_max_delay -datapath_only 10.0 -from [all_registers -clock_pins] -to [get_ports {mcu_spi_d[*] mcu_irq_n}]
set_max_delay -datapath_only 10.0 -from [get_ports mcu_spi_cs_n] -to [get_ports {mcu_spi_d[*]}]
# First-stage token/Gray synchronizers only; multi-bit payloads use separately
# bounded stable-data mailboxes, not global clock-group exceptions.
set sync0 [get_cells -hier -regexp {.*(rg1|wg1|read_sync|ack_sync|request_sync0|request_sync1|frame_sync|done_sync0|done_sync1|valid_sync|pattern_sync|underrun_sync1)_reg(\[0\]|\[[0-9]+\])?}]
set_false_path -to [get_pins -of_objects $sync0 -filter {REF_PIN_NAME == D}]
set rst [get_cells -hier -regexp {rst(100|200|pixel)_reg.*}]
set_false_path -to [get_pins -of_objects $rst -filter {REF_PIN_NAME == PRE || REF_PIN_NAME == CLR}]
# Bundled data is held from request through completion acknowledgment.
set_max_delay -datapath_only 10.0 -from [get_cells -hier -regexp {bridge/read_address_reg.*}] -to [get_cells -hier -regexp {bridge/latched_address_reg.*}]
set_max_delay -datapath_only 10.0 -from [get_cells -hier -regexp {bridge/response_reg.*}] -to [get_cells -hier -regexp {bridge/spi_rdata_reg.*}]
set_max_delay -datapath_only 10.0 -from [get_cells -hier -regexp {lcd/request_line[01]_reg.*}] -to [get_cells -hier -regexp {lcd/line_req_address_reg.*}]
