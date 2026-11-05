# OOC resource/timing investigation; no physical pin or I/O qualification.
create_clock -name clk -period 10.000 [get_ports clk]
create_generated_clock -name read_clk -source [get_ports clk] -edges {1 2 3} -edge_shift {7.75 7.75 7.75} [get_ports read_clk]
create_generated_clock -name pixel_clk -source [get_ports clk] -multiply_by 451 -divide_by 1536 [get_ports pixel_clk]
