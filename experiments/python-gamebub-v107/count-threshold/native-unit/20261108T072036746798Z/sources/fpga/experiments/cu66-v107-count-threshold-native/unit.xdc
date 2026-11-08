# Synthetic arithmetic-unit clock only. No board clock or I/O timing inference.
create_clock -name threshold_unit_clk -period 10.000 [get_ports clk]
