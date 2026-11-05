# Preserve only asynchronous first-stage captures, never recovery stages.
first_stage endpoint_raw {endpoint/(sck_sync_reg\[0\]|cs_sync_reg\[0\]|dq_meta_reg\[[0-3]\]|buttons_meta_reg\[[0-9]+\]|vblank_sync_reg\[0\])}
first_stage bridge_tokens {bridge/(read_sync|ack_sync)_reg\[0\]}
first_stage lcd_tokens {diagnostic/core/lcd/(request_sync0|request_sync1|frame_sync|done_sync0|done_sync1|valid_sync)_reg\[0\]}
first_stage reference_pll_status {platform_(service|panel)_lock_sync_reg\[0\]}
first_stage core_pll_status {status_(service|panel)_lock_sync_reg\[0\]}
# Existing QSPI propagation bounds are retained, NOT an external hold proof.
set_max_delay -datapath_only 10.0 -from [all_registers -clock_pins] -to [get_ports {mcu_spi_d[*] mcu_irq_n}]
set_max_delay -datapath_only 10.0 -from [get_ports mcu_spi_cs_n] -to [get_ports {mcu_spi_d[*]}]

