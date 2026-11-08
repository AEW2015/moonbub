# Synthetic UNIT screen clocks only. These are NOT parent-board constraints.
create_clock -name unit_transport -period 5.000 [get_ports transport_clk]
create_clock -name unit_decoder -period 10.000 [get_ports decoder_clk]
create_clock -name unit_memory -period 10.000 [get_ports memory_clk]
create_clock -name unit_display -period 16.667 [get_ports display_clk]
# No input/output delays: complete parent interface timing is deliberately open.
# No clock groups, blanket false paths, clock-source guesses or timing relaxations.
