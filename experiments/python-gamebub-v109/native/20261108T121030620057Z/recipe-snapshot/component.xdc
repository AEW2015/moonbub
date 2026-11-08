# V107 OOC comparison only; this file is loaded BEFORE synth_design.
# The selected component has one clk input and no generated clock primitive.
# No external I/O or board relationship is implied by this 100-MHz target.
create_clock -name component_clk -period 10.000 [get_ports clk]
# Deliberately leave external protocol/diagnostic arrival/required times open.
# No set_input_delay, set_output_delay, false/multicycle paths or clock groups.
